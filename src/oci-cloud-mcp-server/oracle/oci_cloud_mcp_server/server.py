"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import difflib
import inspect
import json
import os
import re
from copy import copy
from dataclasses import dataclass
from functools import lru_cache
from itertools import islice
from logging import Logger
from typing import Annotated, Any, Callable, Dict, List, Literal, Optional, Tuple, get_args, get_origin

import oci
from oracle_mcp_common import IDCSHttpAuth, build_auth_context, build_idcs_http_auth
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from fastmcp.utilities.auth import parse_scopes

from . import __project__, __version__
from .sdk_catalog import ClientEntry, ModelEntry, SdkResolutionError, load_catalog
from .utils import initAuditLogger

logger = Logger(__name__, level="INFO")
initAuditLogger(logger)

_SERVER_INSTRUCTIONS = inspect.cleandoc(
    """
    Thin MCP wrapper over the OCI Python SDK.
    Think in SDK terms: client_fqn -> operation -> params.
    Prefer direct describe_oci_operation / invoke_oci_api when you already know the call shape.
    If the client family is obvious but the method is fuzzy, use list_client_operations first.
    Use find_oci_api only as a fallback with short resource/action phrases like
    'list regions', 'launch instance', or 'vcn create', not full sentences.
    `oci.core.ComputeClient.list_instances(compartment_id='...')` maps to
    `client_fqn='oci.core.ComputeClient', operation='list_instances', params={'compartment_id': '...'}`.
    invoke_oci_api defaults to compact results for list, summarize, and paginated operations.
    Use result_mode="full" only when needed, and prefer fields=[...] for a few exact top-level fields.
    """
)

_catalog = load_catalog()

mcp = FastMCP(
    name=__project__,
    instructions=_SERVER_INSTRUCTIONS,
)

_user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
_ADDITIONAL_UA = f"{_user_agent_name}/{__version__}"
_http_auth: IDCSHttpAuth | None = None
known_paginated: set = {"get_rr_set"}
_MODEL_SUFFIXES = ("_details", "_config", "_configuration", "_source_details")
_DEFAULT_SUMMARY_ITEMS = 5
_DEFAULT_MODEL_FIELDS = 20
_SEARCH_QUERY_STOPWORDS = {
    "a",
    "an",
    "all",
    "cloud",
    "for",
    "in",
    "infrastructure",
    "oci",
    "of",
    "on",
    "oracle",
    "please",
    "the",
    "to",
    "with",
}
_FALLBACK_CLIENT_PREFERENCES = {
    "compartment": ("oci.identity.IdentityClient",),
    "compartments": ("oci.identity.IdentityClient",),
    "instance": ("oci.core.ComputeClient",),
    "instances": ("oci.core.ComputeClient",),
    "region": ("oci.identity.IdentityClient",),
    "regions": ("oci.identity.IdentityClient",),
    "shape": ("oci.core.ComputeClient",),
    "shapes": ("oci.core.ComputeClient",),
    "subnet": ("oci.core.VirtualNetworkClient",),
    "subnets": ("oci.core.VirtualNetworkClient",),
    "vcn": ("oci.core.VirtualNetworkClient",),
    "vcns": ("oci.core.VirtualNetworkClient",),
}


def _validate_client_fqn(client_fqn: str, *, require_client_class: bool = False) -> None:
    _catalog.client(client_fqn)


def _get_oci_client_kwargs(signer=None):
    kwargs = {
        "circuit_breaker_strategy": oci.circuit_breaker.CircuitBreakerStrategy(
            failure_threshold=int(os.getenv("OCI_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "10")),
            recovery_timeout=int(os.getenv("OCI_CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30")),
        ),
        "circuit_breaker_callback": lambda exc: logger.warning(
            "Circuit breaker triggered: %s", exc
        ),
    }
    if signer is not None:
        kwargs["signer"] = signer
    return kwargs


def _details_param_alias_for_operation(operation_name: str) -> Tuple[Optional[str], Optional[str]]:
    if not (operation_name.startswith("create_") or operation_name.startswith("update_")):
        return None, None
    _, _, op_rest = operation_name.partition("_")
    return f"{op_rest}_details", f"{operation_name}_details"


def _normalize_details_param_alias(
    params: Dict[str, Any],
    operation_name: str,
    *,
    accepted_param_names: Optional[set[str]] = None,
) -> Dict[str, Any]:
    src_key, dst_key = _details_param_alias_for_operation(operation_name)
    if not src_key or not dst_key or src_key not in params or dst_key in params:
        return dict(params)
    if accepted_param_names is not None and (dst_key not in accepted_param_names or src_key in accepted_param_names):
        return dict(params)
    normalized = dict(params)
    normalized[dst_key] = normalized.pop(src_key)
    return normalized


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for value in values:
        if value and value not in seen:
            out.append(value)
            seen.add(value)
    return out


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return "".join(part.capitalize() for part in parts if part)


def _candidate_model_class_names(operation_name: str, param_name: str) -> List[str]:
    candidates: List[str] = []
    for suffix in _MODEL_SUFFIXES:
        if not param_name.endswith(suffix):
            continue
        candidates.append(_snake_to_camel(param_name))
        if suffix == "_details":
            src_key, _ = _details_param_alias_for_operation(operation_name)
            if operation_name.startswith("create_") and src_key and param_name == src_key:
                _, _, op_rest = operation_name.partition("_")
                candidates.insert(0, f"Create{_snake_to_camel(op_rest)}Details")
            elif operation_name.startswith("update_") and src_key and param_name == src_key:
                _, _, op_rest = operation_name.partition("_")
                candidates.insert(0, f"Update{_snake_to_camel(op_rest)}Details")
            else:
                base = _snake_to_camel(param_name[: -len(suffix)])
                if operation_name.startswith("create_"):
                    candidates.append(f"Create{base}Details")
                elif operation_name.startswith("update_"):
                    candidates.append(f"Update{base}Details")
        break
    return _dedupe_preserve_order(candidates)


def _get_client_class(client_fqn: str) -> Any:
    return _catalog.load_client(_catalog.client(client_fqn))


def _get_public_client_methods(cls: Any) -> List[Tuple[str, Callable[..., Any]]]:
    entry = _catalog.client(f"{cls.__module__}.{cls.__name__}")
    return [(name, getattr(cls, name)) for name in entry.operations]


def _public_client_operation_names(cls: Any) -> List[str]:
    return [name for name, _ in _get_public_client_methods(cls)]


def _resolve_public_client_method(target: Any, client_fqn: str, operation_name: str) -> Callable[..., Any]:
    entry = _catalog.client(client_fqn)
    _catalog.operation(entry, operation_name)
    method = getattr(target, operation_name)
    if not callable(method):
        raise SdkResolutionError(f"Cataloged operation {operation_name!r} is not callable")
    return method


def _signature_to_display(operation_name: str, signature) -> str:
    if signature is None:
        return f"{operation_name}(...)"
    params = [param.replace(annotation=inspect.Signature.empty) for param in signature.parameters.values()]
    if params and params[0].name == "self":
        params = params[1:]
    display_signature = inspect.Signature(parameters=params)
    return f"{operation_name}{display_signature}"


def _import_models_module_from_client_fqn(client_fqn: str):
    # This is a catalog service context, not a module path selected by the request.
    return _catalog.client(client_fqn).service


def _resolve_model_class(models_module: str, class_name: str):
    try:
        entry = _catalog.model(class_name, models_module)
    except SdkResolutionError:
        return None  # Optional heuristic lookup; explicit hints never use this path.
    return _catalog.load_model(entry)


def _get_model_schema_maps(model_class: Any) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    entry = _catalog.model_for_class(model_class)
    return dict(entry.swagger_types), dict(entry.attribute_map)


def _is_oci_sdk_model_class(model_class: Any) -> bool:
    if not inspect.isclass(model_class):
        return False
    try:
        _catalog.model_for_class(model_class)
    except SdkResolutionError:
        return False
    return True


def _resolve_model_class_from_fqn(fqn: str) -> Any:
    if not isinstance(fqn, str) or "." not in fqn:
        raise SdkResolutionError("Model FQN must reference a cataloged OCI SDK model class")
    return _catalog.load_model(_catalog.model(fqn))


def _polymorphic_entry(entry: ModelEntry, mapping: Dict[str, Any]) -> ModelEntry:
    model_class = _catalog.load_model(entry)
    subtype_resolver = getattr(model_class, "get_subtype", None)
    if not callable(subtype_resolver):
        return entry
    payload = dict(mapping)
    for snake_name, api_name in entry.attribute_map.items():
        if snake_name in mapping and api_name not in payload:
            payload[api_name] = mapping[snake_name]
    try:
        name = subtype_resolver(payload)
    except (KeyError, TypeError, ValueError):
        return entry  # Preserve the SDK base for an absent/unusable discriminator.
    subtype = _catalog.model(name, entry.service)
    if not _catalog.is_subtype(entry, subtype):
        raise SdkResolutionError("Polymorphic subtype is outside the cataloged base hierarchy")
    return subtype


def _resolve_polymorphic_model_class(model_class: Any, mapping: Dict[str, Any], models_module: Any) -> Any:
    return _catalog.load_model(_polymorphic_entry(_catalog.model_for_class(model_class), mapping))


def _extract_expected_kwargs_from_source(method: Callable[..., Any]) -> Optional[set]:
    try:
        src = inspect.getsource(method)
    except Exception:
        return None
    try:
        match = re.search(r"expected_kwargs\s*=\s*\[\s*(.*?)\s*\]", src, re.DOTALL)
        if not match:
            return set()
        body = match.group(1)
        return set(re.findall(r"['\"]([a-zA-Z0-9_]+)['\"]", body))
    except Exception:
        return None


def _supports_pagination(method: Callable[..., Any], operation_name: str) -> bool:
    try:
        param_names = _extract_expected_kwargs_from_source(method) or set()
        try:
            param_names |= set(inspect.signature(method).parameters)
        except (TypeError, ValueError):
            pass
        if "page" in param_names or {"start_index", "count"} <= param_names:
            return True
        if operation_name == "list_objects" and {"start", "limit"} <= param_names:
            return True
    except Exception:
        pass

    return operation_name in known_paginated


def _score_query_match(
    query: str,
    *texts: str,
    query_tokens: Optional[List[str]] = None,
    normalized_query: Optional[str] = None,
) -> int:
    q = query.lower().strip()
    if not q:
        return 1
    tokens = query_tokens or _normalized_query_tokens(q)
    normalized_query = normalized_query or " ".join(tokens) or q
    haystack = " ".join(texts).lower()
    matched_tokens = [token for token in tokens if token in haystack]
    if q not in haystack and len(matched_tokens) < min(2, len(tokens)):
        return 0
    return (
        (100 if q in haystack else 0)
        + (20 * len(matched_tokens))
        + (20 if tokens and len(matched_tokens) == len(tokens) else 0)
        + int(difflib.SequenceMatcher(None, normalized_query, haystack).ratio() * 10)
    )


def _inspect_method(method: Callable[..., Any]) -> Tuple[Optional[inspect.Signature], str]:
    try:
        signature = inspect.signature(method)
    except Exception:
        signature = None
    try:
        doc = inspect.getdoc(method) or ""
    except Exception:
        doc = ""
    return signature, doc


def _normalized_query_tokens(text: str) -> List[str]:
    raw_tokens = [token for token in re.split(r"[\s._/-]+", text.lower().strip()) if token]
    return [token for token in raw_tokens if token not in _SEARCH_QUERY_STOPWORDS] or raw_tokens


def _score_discovery_match(
    query: str,
    client_fqn: str,
    operation_name: str,
    summary: str,
    *,
    query_tokens: Optional[List[str]] = None,
    normalized_query: Optional[str] = None,
) -> int:
    # Reserved for future search tuning if the thin fallback search needs extra help.
    # TODO(rg): Tradeoff note: because fallback search is intentionally thin now, some ambiguous
    # queries may resolve less helpfully than the heavier heuristic version did.
    # Revisit only if translator-first discovery adoption is insufficient or search
    # quality becomes a real user-facing issue.
    # The main discovery flow is translator-first and does not currently rely on this.
    query_tokens = query_tokens if query_tokens is not None else _normalized_query_tokens(query)
    normalized_query = normalized_query if normalized_query is not None else " ".join(query_tokens)
    score = _score_query_match(
        query,
        client_fqn,
        operation_name,
        summary,
        query_tokens=query_tokens,
        normalized_query=normalized_query,
    )
    if score <= 0:
        return 0

    if normalized_query and normalized_query == " ".join(_normalized_query_tokens(operation_name)):
        score += 40

    if any(client_fqn in _FALLBACK_CLIENT_PREFERENCES.get(token, ()) for token in query_tokens):
        score += 12
    return score


@lru_cache(maxsize=1)
def _discover_client_classes() -> List[Tuple[str, Any]]:
    return [(entry.identity, _catalog.load_client(entry)) for entry in _catalog.clients.values()]


def _get_http_config_and_signer() -> Tuple[Dict[str, Any], Any]:
    """Build caller-specific OCI SDK authentication for an HTTP request."""
    if _http_auth is None:
        raise RuntimeError("HTTP authentication policy has not been initialized.")
    access_token = get_access_token()
    request_auth = _http_auth.context_for(access_token.token if access_token else None)
    config = {**request_auth.config, "additional_user_agent": _ADDITIONAL_UA}
    return config, request_auth.signer


def _get_config_and_signer() -> Tuple[Dict[str, Any], Any]:
    """Resolve outbound OCI SDK authentication for the active transport."""
    if os.getenv("ORACLE_MCP_HOST") and os.getenv("ORACLE_MCP_PORT"):
        return _get_http_config_and_signer()

    auth_context = build_auth_context()
    config = {**auth_context.config, "additional_user_agent": _ADDITIONAL_UA}
    return config, auth_context.signer


def _import_client(cls: type):
    config, signer = _get_config_and_signer()
    client_kwargs = _get_oci_client_kwargs(signer)
    try:
        init_signature = inspect.signature(cls.__init__)
        if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in init_signature.parameters.values()):
            return cls(config, **client_kwargs)
    except (TypeError, ValueError):
        return cls(config, **client_kwargs)

    filtered_kwargs = {key: value for key, value in client_kwargs.items() if key in init_signature.parameters}
    return cls(config, **filtered_kwargs)


def _annotation_to_type_name(annotation: Any) -> Optional[str]:
    if annotation is inspect.Signature.empty:
        return None
    if isinstance(annotation, str):
        return annotation
    origin = get_origin(annotation)
    if origin is list:
        inner = _annotation_to_type_name(get_args(annotation)[0]) or "Any"
        return f"list[{inner}]"
    if origin is dict:
        args = get_args(annotation)
        if len(args) == 2:
            key_type = _annotation_to_type_name(args[0]) or "Any"
            value_type = _annotation_to_type_name(args[1]) or "Any"
            return f"dict({key_type}, {value_type})"
    if origin is not None:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]  # noqa: E721
        if len(args) == 1:
            return _annotation_to_type_name(args[0])
    if isinstance(annotation, type):
        return annotation.__name__
    rendered = str(annotation).replace("typing.", "")
    return rendered if rendered else None


def _coerce_primitive_value(value: Any, type_name: str) -> Any:
    normalized = type_name.strip().lower()
    if normalized in {"int", "integer", "long"}:
        if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
            return int(value.strip())
        if isinstance(value, float) and value.is_integer():
            return int(value)
    if normalized in {"float", "double", "number", "decimal"}:
        if isinstance(value, str):
            try:
                return float(value.strip())
            except ValueError:
                return value
    if normalized in {"bool", "boolean"} and isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    if normalized in {"str", "string"} and isinstance(value, (int, float, bool)):
        return str(value)
    return value


@dataclass(frozen=True)
class _PreparedModel:
    entry: ModelEntry
    values: Dict[str, Any]


@dataclass(frozen=True)
class PreparedParams:
    values: Dict[str, Any]


def _explicit_model(mapping: Dict[str, Any], service: str | None) -> ModelEntry | None:
    entries = []
    for key in ("__model_fqn", "__class_fqn"):
        if key in mapping:
            value = mapping[key]
            if not isinstance(value, str) or "." not in value:
                raise SdkResolutionError("Explicit model FQN must reference a cataloged SDK model")
            entries.append(_catalog.model(value))
    context = entries[0].service if entries else service
    for key in ("__model", "__class"):
        if key in mapping:
            value = mapping[key]
            if not isinstance(value, str) or not value or "." in value:
                raise SdkResolutionError("Short model hint must reference a cataloged service model")
            entries.append(_catalog.model(value, context))
    if entries and any(entry.identity != entries[0].identity for entry in entries):
        raise SdkResolutionError("Conflicting cataloged model hints")
    return entries[0] if entries else None


def _validate_model_hints(value: Any, service: str | None) -> None:
    if isinstance(value, dict):
        selected = _explicit_model(value, service)
        context = selected.service if selected else service
        for key, child in value.items():
            if not key.startswith("__"):
                _validate_model_hints(child, context)
    elif isinstance(value, list):
        for child in value:
            _validate_model_hints(child, service)


def _resolve_model_class_from_type_name(type_name: str, models_module: Any) -> Any:
    if not type_name:
        return None
    try:
        entry = _catalog.model(type_name, models_module)
    except SdkResolutionError:
        return None
    return _catalog.load_model(entry)


def _prepare_value(value: Any, type_name: Optional[str], service: str | None, candidates=()) -> Any:
    if value is None or isinstance(value, _PreparedModel):
        return value
    if type_name:
        primitive = _coerce_primitive_value(value, type_name)
        if primitive is not value:
            return primitive
        compact = type_name.replace(" ", "")
        list_match = re.fullmatch(r"list\[(.+)\]", compact)
        if list_match and isinstance(value, list):
            return [_prepare_value(item, list_match.group(1), service) for item in value]
        dict_match = re.fullmatch(r"dict\(([^,]+),(.+)\)", compact)
        if dict_match and isinstance(value, dict):
            return {key: _prepare_value(item, dict_match.group(2), service) for key, item in value.items()}
    if isinstance(value, list):
        return [_prepare_value(item, None, service) for item in value]
    if not isinstance(value, dict):
        return value
    selected = _explicit_model(value, service)
    if selected is None:
        for candidate in ([type_name] if type_name else []) + list(candidates):
            try:
                selected = _catalog.model(candidate, service)
                break
            except SdkResolutionError:
                continue
    if selected is None:
        return {key: _prepare_value(child, None, service) for key, child in value.items()}
    selected = _polymorphic_entry(selected, value)
    explicit_fqn = any(key in value for key in ("__model_fqn", "__class_fqn"))
    clean = {key: child for key, child in value.items() if not key.startswith("__")}
    if not explicit_fqn:
        clean = {key: child for key, child in clean.items() if key in selected.swagger_types}
    values = {}
    for key, child in clean.items():
        field_type = selected.swagger_types.get(key)
        nested_candidates = []
        if field_type is None:
            nested_candidates = _candidate_model_class_names("", key)
        # Schema gaps never infer a class; explicit approved hints still work.
        values[key] = _prepare_value(
            child, None if key in selected.opaque_fields else field_type,
            selected.service, nested_candidates,
        )
    return _PreparedModel(selected, values)


def _materialize(value: Any) -> Any:
    if isinstance(value, _PreparedModel):
        model_class = _catalog.load_model(value.entry)
        return model_class(**{key: _materialize(child) for key, child in value.values.items()})
    if isinstance(value, dict):
        return {key: _materialize(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_materialize(child) for child in value]
    return value


def _coerce_value_to_type(value: Any, type_name: Optional[str], models_module: Any) -> Any:
    _validate_model_hints(value, models_module)
    return _materialize(_prepare_value(value, type_name, models_module))


def _coerce_mapping_for_model_class(mapping: Dict[str, Any], models_module: Any, model_class: Any) -> Dict[str, Any]:
    entry = _catalog.model_for_class(model_class)
    _validate_model_hints(mapping, entry.service)
    return _materialize({
        key: _prepare_value(value, entry.swagger_types.get(key), entry.service)
        for key, value in mapping.items()
    })


def _method_param_types(method: Callable[..., Any]) -> Dict[str, str]:
    signature, doc = _inspect_method(method)
    types = {name: type_name for type_name, name in re.findall(
        r":param\s+([^\s:]+)\s+([A-Za-z0-9_]+)\s*:", doc,
    )}
    if signature:
        for name, param in signature.parameters.items():
            annotation = _annotation_to_type_name(param.annotation)
            if annotation and annotation != "Any":
                types[name] = annotation
    return types


def _coerce_params_to_method_types(client_fqn: str, method: Callable[..., Any], params: Dict[str, Any]) -> Dict[str, Any]:
    service = _catalog.client(client_fqn).service
    _validate_model_hints(params, service)
    types = _method_param_types(method)
    return _materialize({key: _prepare_value(value, types.get(key), service) for key, value in params.items()})


def _coerce_mapping_values(mapping: Dict[str, Any], models_module: Any, parent_prefix: Optional[str] = None) -> Dict[str, Any]:
    _validate_model_hints(mapping, models_module)
    return _materialize({
        key: _prepare_value(value, None, models_module, _candidate_model_class_names("", key))
        for key, value in mapping.items()
    })


def _construct_model_from_mapping(mapping: Dict[str, Any], models_module: Any, candidate_classnames: List[str]):
    _validate_model_hints(mapping, models_module)
    return _materialize(_prepare_value(mapping, None, models_module, candidate_classnames))


def _coerce_params_to_oci_models(client_fqn: str, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
    service = _catalog.client(client_fqn).service
    _validate_model_hints(params, service)
    normalized = _normalize_details_param_alias(params, operation)
    return _materialize({
        key: _prepare_value(value, None, service, _candidate_model_class_names(operation, key))
        for key, value in normalized.items()
    })


def prepare_params(client: ClientEntry, method: Callable[..., Any], operation: str, params: Dict[str, Any]) -> PreparedParams:
    _validate_model_hints(params, client.service)
    normalized = _normalize_details_param_alias(params, operation)
    types = _method_param_types(method)
    values = {
        key: _prepare_value(value, types.get(key), client.service, _candidate_model_class_names(operation, key))
        for key, value in normalized.items()
    }
    return PreparedParams(_align_params_to_signature(method, operation, values))


def materialize_params(prepared: PreparedParams) -> Dict[str, Any]:
    return _materialize(prepared.values)


def _describe_model_class(model_class: Any, max_fields: int = _DEFAULT_MODEL_FIELDS) -> Dict[str, Any]:
    swagger_types, _ = _get_model_schema_maps(model_class)
    fields = list(swagger_types.keys()) if isinstance(swagger_types, dict) else []

    return {
        "name": getattr(model_class, "__name__", str(model_class)),
        "field_count": len(fields),
        "fields": fields[:max_fields],
        "fields_truncated": len(fields) > max_fields,
    }


def _describe_operation(
    client_fqn: str, operation_name: str, *, max_model_fields: int = _DEFAULT_MODEL_FIELDS
) -> Dict[str, Any]:
    _catalog.operation(_catalog.client(client_fqn), operation_name)
    cls = _get_client_class(client_fqn)
    method = _resolve_public_client_method(cls, client_fqn, operation_name)

    signature, doc = _inspect_method(method)
    summary = doc.strip().partition("\n")[0] if doc else ""
    signature_display = _signature_to_display(operation_name, signature)
    expected_kwargs = sorted(_extract_expected_kwargs_from_source(method) or [])
    required_params: List[Dict[str, Any]] = []
    optional_params: List[Dict[str, Any]] = []
    request_models: List[Dict[str, Any]] = []
    param_aliases: List[Dict[str, str]] = []
    models_module = _import_models_module_from_client_fqn(client_fqn)

    src_key, dst_key = _details_param_alias_for_operation(operation_name)
    if src_key and dst_key:
        param_aliases.append({"from": src_key, "to": dst_key})

    if signature is not None:
        for param in signature.parameters.values():
            if param.name == "self":
                continue
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                continue

            info: Dict[str, Any] = {
                "name": param.name,
                "kind": param.kind.name.lower(),
                "type": _annotation_to_type_name(param.annotation) or "Any",
            }
            if param.default is inspect.Signature.empty:
                required_params.append(info)
            else:
                info["default"] = "None" if param.default is None else repr(param.default)
                optional_params.append(info)

            if not models_module:
                continue
            candidate_names = _candidate_model_class_names(operation_name, param.name)
            if not candidate_names:
                continue
            model_class = None
            for candidate_name in candidate_names:
                model_class = _resolve_model_class(models_module, candidate_name)
                if inspect.isclass(model_class):
                    break
            if inspect.isclass(model_class):
                request_models.append(
                    {
                        "param": param.name,
                        "candidates": candidate_names,
                        "model": _describe_model_class(model_class, max_model_fields),
                    }
                )

    return {
        "client": client_fqn,
        "operation": operation_name,
        "summary": summary,
        "signature": signature_display,
        "supports_pagination": _supports_pagination(method, operation_name),
        "required_params": required_params,
        "optional_params": optional_params,
        "accepted_kwargs": expected_kwargs,
        "request_models": request_models,
        "parameter_aliases": param_aliases,
    }


def _extract_paginated_items(response_data: Any) -> Tuple[Any, Optional[str], Any]:
    if isinstance(response_data, oci.dns.models.RecordCollection) or isinstance(response_data, oci.dns.models.RRSet):
        return response_data.items or [], "dns", response_data.__class__
    if isinstance(response_data, oci.object_storage.models.ListObjects):
        return response_data.objects or [], "object_storage", None
    if isinstance(response_data, list):
        return response_data, None, None
    schema = getattr(response_data, "swagger_types", {})
    # SDK arrays may be unset on an empty page. Keep their collection identity
    # so a valid continuation is followed and the legacy output shape is stable.
    results = getattr(response_data, "results", None)
    if results is not None or schema.get("results", "").startswith("list["):
        return results if results is not None else [], None, None
    items = getattr(response_data, "items", None)
    if (items is not None and not callable(items)) or schema.get("items", "").startswith("list["):
        return items if items is not None else [], None, None

    # Native envelopes declare their record arrays in the SDK model schema.
    # Do not guess among multiple arrays (e.g. schemas is SCIM metadata).
    fields = [name for name, kind in schema.items() if kind.startswith("list[") and name != "schemas"]
    if "resources" in fields:
        fields = ["resources"]
    if len(fields) == 1:
        field = fields[0]
        return getattr(response_data, field) or [], field, response_data
    return None, None, None


def _summarize_serialized_data(data: Any, sample_size: int) -> Dict[str, Any]:
    if isinstance(data, list):
        sample = data[:sample_size]
        keys = []
        for item in sample:
            if isinstance(item, dict):
                keys.extend(item.keys())
        return {
            "kind": "list",
            "item_count": len(data),
            "sample": sample,
            "sample_count": len(sample),
            "sample_truncated": len(data) > len(sample),
            "sample_item_keys": sorted(set(keys)),
        }
    if isinstance(data, dict):
        keys = list(data.keys())
        sample: Dict[str, Any] = {}
        for key in keys[:sample_size]:
            value = data[key]
            if isinstance(value, list):
                sample[key] = {"kind": "list", "item_count": len(value)}
            elif isinstance(value, dict):
                sample[key] = {"kind": "object", "keys": list(value.keys())[:sample_size]}
            else:
                sample[key] = value
        return {
            "kind": "object",
            "keys": keys,
            "sample": sample,
            "sample_truncated": len(keys) > len(sample),
        }
    return {"kind": type(data).__name__, "value": data}


def _serialize_oci_data(data: Any) -> Any:
    def ensure_jsonable(obj: Any) -> Any:
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, (list, tuple)):
            return [ensure_jsonable(x) for x in obj]
        if isinstance(obj, dict):
            return {k: ensure_jsonable(v) for k, v in obj.items()}
        try:
            json.dumps(obj)
            return obj
        except Exception:
            return str(obj)

    try:
        converted = oci.util.to_dict(data)
    except Exception:
        converted = data
    return ensure_jsonable(converted)


class FieldProjectionError(ValueError):
    def __init__(self, message: str, requested_fields: List[str], available_fields: List[str]):
        super().__init__(message)
        self.requested_fields = requested_fields
        self.available_fields = available_fields


def _project_top_level_fields(
    serialized_data: Any, fields: Optional[List[str]]
) -> Tuple[Any, List[str], List[str], List[str]]:
    if fields is None:
        return serialized_data, [], [], []

    if isinstance(serialized_data, dict):
        available_fields = sorted(serialized_data)
        is_list = False
    elif isinstance(serialized_data, list):
        if not serialized_data:
            return [], fields, [], []
        available_fields = sorted({key for item in serialized_data if isinstance(item, dict) for key in item})
        is_list = True
    else:
        raise ValueError("fields can only be used with object responses or lists of objects")

    matched_fields = [field for field in fields if field in available_fields]
    if not matched_fields:
        raise FieldProjectionError(
            "None of the requested fields matched top-level response fields. "
            f"Requested: {fields}. Available: {available_fields[:20]}",
            requested_fields=fields,
            available_fields=available_fields,
        )
    unmatched_fields = [field for field in fields if field not in available_fields]
    if is_list:
        projected_data = [
            {field: item[field] for field in matched_fields if field in item} if isinstance(item, dict) else item
            for item in serialized_data
        ]
    else:
        projected_data = {field: serialized_data[field] for field in matched_fields}
    return projected_data, matched_fields, unmatched_fields, available_fields


def _align_params_to_signature(
    method: Callable[..., Any], operation_name: str, params: Dict[str, Any]
) -> Dict[str, Any]:
    try:
        sig = inspect.signature(method)
        param_names = set(sig.parameters.keys())
    except Exception:
        return params

    return _normalize_details_param_alias(params, operation_name, accepted_param_names=param_names)


def _call_with_pagination_if_applicable(
    method: Callable[..., Any],
    params: Dict[str, Any],
    operation_name: str,
    max_results: Optional[int] = None,
    uses_pagination: Optional[bool] = None,
    pagination_metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[Any, Optional[str], bool]:
    if uses_pagination is None:
        uses_pagination = _supports_pagination(method, operation_name)
    if uses_pagination:
        logger.info(f"Using paginator for operation {operation_name}")
        call_params = dict(params)
        requested_limit = call_params.get("limit")
        remaining_items = max_results
        aggregated_results: List[Any] = []
        is_dns_record_collection = False
        dns_record_collection_class = None
        is_list_objects_response = False
        list_objects_prefixes = set()
        call_result = None
        more_results_available = False
        native_field = None
        native_envelope = None
        visited = {(name, params[name]) for name in ("page", "start", "start_index") if name in params}
        page_metadata = []
        collection_seen = False

        while remaining_items is None or remaining_items > 0:
            if remaining_items is not None:
                if isinstance(requested_limit, int) and requested_limit > 0:
                    call_params["limit"] = min(requested_limit, remaining_items)
                else:
                    call_params.pop("limit", None)
                if isinstance(params.get("count"), int) and params["count"] > 0:
                    call_params["count"] = min(params["count"], remaining_items)

            call_result = oci.retry.DEFAULT_RETRY_STRATEGY.make_retrying_call(method, **call_params)
            response_data = call_result.data if hasattr(call_result, "data") else call_result
            available_slots = remaining_items

            current_items, collection_kind, collection_class = _extract_paginated_items(response_data)
            if current_items is None:
                if collection_seen:
                    raise ValueError("Pagination response changed from a collection to a non-collection")
                # A page/limit argument does not imply a collection response.
                # Keep aggregate/scalar payloads intact and expose any continuation.
                if pagination_metadata is not None:
                    pagination_metadata["collection_paginated"] = False
                    if getattr(call_result, "next_page", None):
                        pagination_metadata["next_page"] = call_result.next_page
                return (
                    response_data,
                    getattr(call_result, "headers", {}).get("opc-request-id"),
                    bool(getattr(call_result, "has_next_page", False)),
                )
            collection_seen = True
            if getattr(response_data, "swagger_types", None):
                record_field = (
                    "objects" if collection_kind == "object_storage" else
                    "items" if collection_kind == "dns" else
                    collection_kind or ("results" if hasattr(response_data, "results") else "items")
                )
                page_metadata.append({
                    key: value for key, value in _serialize_oci_data(response_data).items() if key != record_field
                })
            if collection_kind == "dns":
                is_dns_record_collection = True
                dns_record_collection_class = collection_class
            elif collection_kind == "object_storage":
                is_list_objects_response = True
                if response_data.prefixes:
                    list_objects_prefixes.update(response_data.prefixes)
            elif collection_kind:
                native_field = collection_kind
                if native_envelope is None:
                    native_envelope = copy(collection_class)

            if not hasattr(current_items, "__len__") or not hasattr(current_items, "__getitem__"):
                current_items = list(current_items)
            current_count = len(current_items)
            aggregated_results.extend(islice(current_items, available_slots))
            if available_slots is not None and current_count > available_slots:
                more_results_available = True
            if remaining_items is not None:
                remaining_items -= current_count

            if native_field == "resources" and params.get("count") == 0:
                # SCIM count=0 requests only the total, not traversal of resources.
                more_results_available = bool(getattr(response_data, "total_results", 0))
                break

            next_param = "page"
            next_value = getattr(call_result, "next_page", None)
            if is_list_objects_response:
                next_param = "start"
                next_value = getattr(response_data, "next_start_with", None)
            elif native_field == "resources" and (
                "start_index" in params or "count" in params or next_value is None
            ):
                start_index = getattr(response_data, "start_index", None)
                total_results = getattr(response_data, "total_results", None)
                if isinstance(start_index, int) and isinstance(total_results, int):
                    accepted_params = _extract_expected_kwargs_from_source(method) or set()
                    accepted_params |= set(inspect.signature(method).parameters)
                    if "start_index" not in accepted_params:
                        # Search offsets belong in request models, not SDK kwargs.
                        # Preserve this page for manual continuation in that contract.
                        more_results_available = more_results_available or start_index + current_count <= total_results
                        break
                    next_param = "start_index"
                    next_value = start_index + current_count
                    if next_value > total_results:
                        next_value = None
                    elif current_count == 0:
                        raise ValueError("SCIM pagination made no progress before total_results was reached")
            elif getattr(call_result, "has_next_page", False) and next_value is None:
                raise ValueError("Paginated response has no usable next-page token")

            if remaining_items is not None and remaining_items <= 0:
                more_results_available = more_results_available or next_value is not None
                # A backend token cannot resume records discarded within a page.
                if pagination_metadata is not None and next_value is not None and current_count <= available_slots:
                    pagination_metadata[next_param] = next_value
                break
            if next_value is None:
                break
            continuation = (next_param, next_value)
            if continuation in visited or call_params.get(next_param) == next_value:
                raise ValueError("Pagination returned a repeated continuation")
            visited.add(continuation)
            call_params[next_param] = next_value
            if next_param == "start_index":
                call_params.pop("page", None)

        response = call_result
        if is_dns_record_collection:
            data = dns_record_collection_class(items=aggregated_results)
        elif is_list_objects_response:
            data = oci.object_storage.models.ListObjects(
                objects=aggregated_results,
                prefixes=list(list_objects_prefixes),
            )
        elif native_envelope is not None:
            setattr(native_envelope, native_field, aggregated_results)
            if native_field == "resources":
                native_envelope.items_per_page = len(aggregated_results)
            data = native_envelope
        else:
            data = aggregated_results
        if pagination_metadata is not None and page_metadata:
            pagination_metadata["page_metadata"] = page_metadata
        has_more = more_results_available
        try:
            opc_request_id = response.headers.get("opc-request-id")
        except Exception:
            opc_request_id = None
        return data, opc_request_id, has_more

    call_params = _normalize_details_param_alias(params, operation_name)

    try:
        logger.debug(f"_call_with_pagination_if_applicable call_params keys: {list(call_params.keys())}")
        logger.debug(f"op: {operation_name}")
        response = method(**call_params)
    except TypeError as exc:
        msg = str(exc)
        if "unexpected keyword argument" in msg and (
            operation_name.startswith("create_") or operation_name.startswith("update_")
        ):
            try:
                bad_kw = msg.split("'")[1]
                expected_src, alt_key = _details_param_alias_for_operation(operation_name)
                if expected_src and alt_key and bad_kw == expected_src and expected_src in call_params:
                    new_params = dict(call_params)
                    new_params.pop(expected_src, None)
                    response = method(**new_params)
                else:
                    raise
            except Exception:
                raise
        else:
            raise

    data = response.data if hasattr(response, "data") else response
    try:
        opc_request_id = response.headers.get("opc-request-id")
    except Exception:
        opc_request_id = None
    return data, opc_request_id, False


def _build_param_error_hints(
    method: Callable[..., Any], operation_name: str, params: Dict[str, Any], error_text: str
) -> Dict[str, Any]:
    signature, _ = _inspect_method(method)
    expected_param_names = (
        [
            param.name
            for param in signature.parameters.values()
            if param.name != "self" and param.kind != inspect.Parameter.VAR_KEYWORD
        ]
        if signature is not None
        else []
    )

    accepted_kwargs = sorted(_extract_expected_kwargs_from_source(method) or [])
    hints: Dict[str, Any] = {"signature": _signature_to_display(operation_name, signature)}
    bad_kw_match = re.search(r"unexpected keyword argument '([^']+)'", error_text)
    if bad_kw_match:
        bad_kw = bad_kw_match.group(1)
        suggestions = difflib.get_close_matches(
            bad_kw,
            expected_param_names + accepted_kwargs,
            n=5,
            cutoff=0.4,
        )
        hints["invalid_param"] = bad_kw
        if suggestions:
            hints["parameter_suggestions"] = suggestions

    if expected_param_names:
        hints["expected_params"] = expected_param_names
    if accepted_kwargs:
        hints["accepted_kwargs"] = accepted_kwargs

    src_key, dst_key = _details_param_alias_for_operation(operation_name)
    if src_key and dst_key and (src_key in params or dst_key in expected_param_names):
        hints["parameter_aliases"] = [{"from": src_key, "to": dst_key}]

    return hints


@mcp.tool(
    description=(
        "Thin keyword/resource-action fallback search across OCI Python SDK client methods. "
        "Use this only when you cannot infer a plausible client class or method well enough to call "
        "list_client_operations or describe_oci_operation first."
    )
)
def find_oci_api(
    query: Annotated[
        str,
        "Short SDK-oriented resource/action query such as 'list regions', 'launch instance', or 'vcn create'. "
        "Reduce requests to concise search terms; do not pass full sentences. This is an escape hatch, not the "
        "normal first step.",
    ],
    client_fqn: Annotated[
        Optional[str],
        "Optional fully-qualified client class to narrow the search, e.g. 'oci.core.ComputeClient'.",
    ] = None,
    limit: Annotated[int, "Maximum matches to return. Keep this small (3-5) for initial discovery."] = 5,
    include_params: Annotated[bool, "Include compact signatures for each match."] = False,
) -> dict:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    if not query or not query.strip():
        raise ValueError("query must be non-empty")
    query_tokens = _normalized_query_tokens(query)
    normalized_query = " ".join(query_tokens)

    if client_fqn:
        _validate_client_fqn(client_fqn, require_client_class=True)
        client_entries = [(client_fqn, _get_client_class(client_fqn))]
    else:
        client_entries = _discover_client_classes()

    matches: List[Tuple[int, Dict[str, Any]]] = []
    for current_client_fqn, cls in client_entries:
        for name, member in _get_public_client_methods(cls):
            signature, doc = _inspect_method(member)
            summary = doc.strip().partition("\n")[0] if doc else ""
            score = _score_discovery_match(
                query,
                current_client_fqn,
                name,
                summary,
                query_tokens=query_tokens,
                normalized_query=normalized_query,
            )
            if score <= 0:
                continue

            entry: Dict[str, Any] = {
                "client_fqn": current_client_fqn,
                "operation": name,
                "summary": summary,
            }
            if include_params:
                entry["params"] = _signature_to_display(name, signature)
            matches.append((score, entry))

    matches.sort(key=lambda item: (-item[0], item[1]["client_fqn"], item[1]["operation"]))
    limited_matches = [entry for _, entry in matches[:limit]]
    logger.info(f"find_oci_api query='{query}' returned {len(limited_matches)} matches")
    return {
        "query": query,
        "client_filter": client_fqn,
        "total_matches": len(matches),
        "matches": limited_matches,
    }


@mcp.tool(
    description=(
        "Describe a specific OCI Python SDK client method, including required params, "
        "optional params, pagination behavior, aliases, and request model hints."
    )
)
def describe_oci_operation(
    client_fqn: Annotated[str, "Fully-qualified client class, e.g. 'oci.core.VirtualNetworkClient'"],
    operation: Annotated[str, "Operation name, e.g. 'create_vcn' or 'list_instances'"],
    max_model_fields: Annotated[int, "Maximum number of model fields to include per request model hint."] = (
        _DEFAULT_MODEL_FIELDS
    ),
) -> dict:
    if max_model_fields < 1:
        raise ValueError("max_model_fields must be >= 1")
    _validate_client_fqn(client_fqn, require_client_class=True)
    return _describe_operation(client_fqn, operation, max_model_fields=max_model_fields)


@mcp.tool(
    description=(
        "Invoke an OCI Python SDK client method by fully-qualified client class and operation name. "
        "This is a thin wrapper over the OCI Python SDK call. Equivalent Python "
        "`oci.core.ComputeClient.list_instances(compartment_id='...')` maps to "
        "`client_fqn='oci.core.ComputeClient', operation='list_instances', "
        "params={'compartment_id': '...'}`. The default result_mode='auto' keeps list, summarize, and paginated results compact."
    )
)
def invoke_oci_api(
    client_fqn: Annotated[str, "Fully-qualified client class, e.g. 'oci.core.ComputeClient'"],
    operation: Annotated[str, "Client method/operation name, e.g. 'list_instances' or 'get_instance'"],
    params: Annotated[
        Optional[Dict[str, Any]],
        "Keyword arguments for the SDK method (JSON object). These are the snake_case kwargs you would pass in Python.",
    ] = None,
    fields: Annotated[
        Optional[List[str]],
        "Optional top-level response fields to project after serialization, e.g. "
        "['id', 'display_name', 'lifecycle_state']. This shapes the returned payload only; "
        "it does not change the SDK call contract.",
    ] = None,
    max_results: Annotated[
        Optional[int],
        "Optionally limit returned records for paginated operations, or trim top-level lists after serialization.",
    ] = None,
    result_mode: Annotated[
        Literal["auto", "full", "summary"],
        "Use 'auto' for compact defaults, 'summary' for a compact structural summary, or 'full' for the full payload.",
    ] = "auto",
) -> dict:
    validated_client = None
    validated_method = None
    try:
        if max_results is not None and max_results < 1:
            raise ValueError("max_results must be >= 1")
        if fields is not None:
            if not isinstance(fields, list) or not all(isinstance(field, str) and field.strip() for field in fields):
                raise ValueError("fields must contain only non-empty strings")
            normalized_fields = list(dict.fromkeys(field.strip() for field in fields))
            if not normalized_fields:
                raise ValueError("fields must contain at least one non-empty string")
        else:
            normalized_fields = None
        validated_client = _catalog.client(client_fqn)
        _catalog.operation(validated_client, operation)
        cls = _get_client_class(client_fqn)
        validated_method = _resolve_public_client_method(cls, client_fqn, operation)
        input_params = params or {}
        prepared = prepare_params(validated_client, validated_method, operation, input_params)
        final_params = materialize_params(prepared)
        client = _import_client(cls)
        method = _resolve_public_client_method(client, client_fqn, operation)
        uses_pagination = _supports_pagination(method, operation)
        logger.debug(f"invoke_oci_api final_params keys: {list(final_params.keys())}")
        logger.debug(f"op: {operation}")
        pagination_metadata: Dict[str, Any] = {}
        data, opc_request_id, has_more_results = _call_with_pagination_if_applicable(
            method,
            final_params,
            operation,
            max_results,
            uses_pagination=uses_pagination,
            pagination_metadata=pagination_metadata,
        )
        if pagination_metadata.pop("collection_paginated", True) is False:
            uses_pagination = False

        serialized_data = _serialize_oci_data(data)
        projected_data, matched_fields, unmatched_fields, available_fields = _project_top_level_fields(
            serialized_data, normalized_fields
        )

        effective_result_mode = result_mode
        if result_mode == "auto":
            effective_result_mode = (
                "summary"
                if uses_pagination or operation.startswith("list_") or operation.startswith("summarize_")
                else "full"
            )

        if max_results is not None and isinstance(projected_data, list):
            has_more_results = has_more_results or len(projected_data) > max_results

        result_meta: Dict[str, Any] = {
            "result_mode": effective_result_mode,
            "pagination_used": uses_pagination,
            "has_more_results": has_more_results,
            "truncated": has_more_results,
            **pagination_metadata,
        }
        if max_results is not None:
            result_meta["max_results"] = max_results
        if normalized_fields is not None:
            result_meta["fields"] = matched_fields
            if unmatched_fields:
                result_meta["unmatched_fields"] = unmatched_fields
                result_meta["available_fields"] = available_fields

        if effective_result_mode == "summary":
            rendered_data = _summarize_serialized_data(projected_data, max_results or _DEFAULT_SUMMARY_ITEMS)
        else:
            trim_limit = None if uses_pagination else max_results
            if trim_limit is not None and isinstance(projected_data, list):
                rendered_data = projected_data[:trim_limit]
            else:
                rendered_data = projected_data
            if isinstance(projected_data, list):
                result_meta["returned_items"] = len(rendered_data)
                if not (uses_pagination and has_more_results):
                    result_meta["total_items"] = len(projected_data)

        result = {
            "client": client_fqn,
            "operation": operation,
            "params": input_params,
            "opc_request_id": opc_request_id,
            "data": rendered_data,
            "result_meta": result_meta,
        }
        logger.info(f"invoke_oci_api success: client={client_fqn} op={operation} opc_request_id={opc_request_id}")
        return result
    except Exception as exc:
        logger.error(f"Error invoking OCI API {client_fqn}.{operation}: {exc}")
        error_result = {
            "client": client_fqn,
            "operation": operation,
            "params": params or {},
            "error": str(exc),
        }
        if isinstance(exc, FieldProjectionError):
            error_result["requested_fields"] = exc.requested_fields
            error_result["available_fields"] = exc.available_fields
        error_text = str(exc)
        needs_param_hints = any(clue in error_text for clue in ("unexpected keyword argument", "required positional argument"))
        if validated_client is not None:
            suggestions = difflib.get_close_matches(
                operation, list(validated_client.operations), n=5, cutoff=0.4,
            )
            if validated_method is None and suggestions:
                error_result["suggested_operations"] = suggestions
            elif needs_param_hints and validated_method is not None:
                error_result.update(_build_param_error_hints(validated_method, operation, params or {}, error_text))
        return error_result


@mcp.tool(
    description=(
        "List public callable OCI Python SDK methods for a given client class. Prefer this over find_oci_api when "
        "you already know the likely client family."
    )
)
def list_client_operations(
    client_fqn: Annotated[str, "Fully-qualified client class, e.g. 'oci.core.ComputeClient'"],
    query: Annotated[
        Optional[str],
        "Optional keyword/resource filter to keep the result compact, e.g. 'instance' or 'launch'.",
    ] = None,
    limit: Annotated[Optional[int], "Optional maximum number of operations to return."] = None,
    include_params: Annotated[bool, "Include compact method signatures in the response."] = True,
) -> dict:
    if limit is not None and limit < 1:
        raise ValueError("limit must be >= 1")

    _validate_client_fqn(client_fqn, require_client_class=True)
    cls = _get_client_class(client_fqn)
    query_tokens = _normalized_query_tokens(query or "")
    normalized_query = " ".join(query_tokens)
    matched_ops: List[Tuple[int, str, str, Optional[inspect.Signature]]] = []
    for name, member in _get_public_client_methods(cls):
        signature, doc = _inspect_method(member)
        summary = doc.strip().partition("\n")[0] if doc else ""
        score = _score_discovery_match(
            query or "",
            client_fqn,
            name,
            summary,
            query_tokens=query_tokens,
            normalized_query=normalized_query,
        )
        if query and score <= 0:
            continue
        matched_ops.append((score, name, summary, signature))

    matched_ops.sort(key=(lambda item: (-item[0], item[1])) if query else (lambda item: item[1]))
    selected_ops = matched_ops[:limit] if limit is not None else matched_ops
    operations = [
        {
            "name": name,
            "summary": summary,
            **({"params": _signature_to_display(name, signature)} if include_params else {}),
        }
        for _, name, summary, signature in selected_ops
    ]

    logger.info(f"Found {len(operations)} operations on {client_fqn}")
    return {"client": client_fqn, "operations": operations}


@mcp.tool(
    description=(
        "List OCI Python SDK service clients supported by the packaged SDK catalog. "
        "Prefer direct SDK-shaped calls or find_oci_api for task-oriented requests; use this for capability "
        "discovery or debugging."
    )
)
def list_oci_clients() -> dict:
    clients = [
        {"client_fqn": entry.identity, "module": entry.service, "class": entry.name}
        for entry in _catalog.clients.values()
    ]
    return {"count": len(clients), "clients": clients}


def main():
    global _http_auth

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if not (host and port):
        mcp.run()
        return
    required_scopes = parse_scopes(os.getenv("IDCS_REQUIRED_SCOPES")) or (
        f"openid profile email oci_mcp.{__project__.removeprefix('oracle.oci-').removesuffix('-mcp-server').replace('-', '_')}.invoke".split()
    )
    _http_auth = build_idcs_http_auth(required_scopes)
    mcp.auth = _http_auth.provider
    mcp.run(transport="http", host=host, port=int(port))


if __name__ == "__main__":
    main()
