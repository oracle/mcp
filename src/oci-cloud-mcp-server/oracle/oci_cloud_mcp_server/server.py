"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import difflib
import inspect
import json
import os
import pkgutil
import re
from functools import lru_cache
from importlib import import_module
from itertools import islice
from logging import Logger
from typing import Annotated, Any, Callable, Dict, List, Literal, Optional, Tuple, get_args, get_origin

import oci
from fastmcp import FastMCP
from fastmcp.server.auth.providers.oci import OCIProvider
from fastmcp.server.dependencies import get_access_token
from fastmcp.utilities.auth import parse_scopes

from . import __project__, __version__
from .utils import initAuditLogger

logger = Logger(__name__, level="INFO")
initAuditLogger(logger)

_SERVER_INSTRUCTIONS = inspect.cleandoc(
    """
    This server is a thin MCP wrapper over the OCI Python SDK without arbitrary Python execution.
    Think in SDK terms: client_fqn -> operation -> params.
    Do not search first.
    Default workflow:
    1. Infer the SDK client class and method you would write in Python.
    2. Use describe_oci_operation if the contract is unclear.
    3. Use invoke_oci_api once the call shape is clear.
    Prefer direct describe/invoke when you already know the method.
    If the client family is obvious but the method is fuzzy, use list_client_operations first.
    Use find_oci_api only as a fallback with short resource/action phrases like
    'list regions', 'launch instance', or 'vcn create'; not full user sentences.
    invoke_oci_api maps directly from the Python SDK call shape:
    `oci.core.ComputeClient.list_instances(compartment_id='...')` becomes
    `client_fqn='oci.core.ComputeClient', operation='list_instances',
    params={'compartment_id': '...'}`.
    It defaults to compact results for list, summarize, and paginated operations.
    Use result_mode="full" only when needed, and prefer fields=[...] when you only need
    a few exact top-level fields.
    list_oci_clients is for capability discovery/debugging.
    The server automatically normalizes common scalar and model-field type mistakes
    (for example "3" -> 3 or "true" -> True when the SDK metadata is clear),
    so prefer one clean call over trial-and-error retries.
    """
)

mcp = FastMCP(
    name=__project__,
    instructions=_SERVER_INSTRUCTIONS,
)

_user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
_ADDITIONAL_UA = f"{_user_agent_name}/{__version__}"
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
    if not isinstance(client_fqn, str) or not client_fqn:
        raise ValueError("client_fqn must be a non-empty string")
    if "." not in client_fqn:
        raise ValueError("client_fqn must be a fully-qualified class name like 'oci.core.ComputeClient'")
    if not client_fqn.startswith("oci."):
        raise ValueError("client_fqn must reference an OCI SDK client under the 'oci.' namespace")
    if require_client_class and not client_fqn.rsplit(".", 1)[-1].endswith("Client"):
        raise ValueError("client_fqn must reference an OCI SDK client class ending in 'Client'")


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
    _validate_client_fqn(client_fqn)
    module_name, class_name = client_fqn.rsplit(".", 1)
    module = import_module(module_name)
    cls = getattr(module, class_name)
    if not inspect.isclass(cls):
        raise ValueError(f"{client_fqn} is not a class")
    return cls


def _get_public_client_methods(cls: Any) -> List[Tuple[str, Callable[..., Any]]]:
    return [
        (name, member)
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]


def _signature_to_display(operation_name: str, signature) -> str:
    if signature is None:
        return f"{operation_name}(...)"
    params = [param.replace(annotation=inspect.Signature.empty) for param in signature.parameters.values()]
    if params and params[0].name == "self":
        params = params[1:]
    display_signature = inspect.Signature(parameters=params)
    return f"{operation_name}{display_signature}"


def _import_models_module_from_client_fqn(client_fqn: str):
    module_name = client_fqn.rsplit(".", 1)[0]
    candidates: List[str] = [f"{module_name}.models"]
    if module_name.count(".") >= 2:
        parent_module = module_name.rsplit(".", 1)[0]
        candidates.append(f"{parent_module}.models")

    for candidate in _dedupe_preserve_order(candidates):
        try:
            return import_module(candidate)
        except Exception:
            continue
    return None


def _resolve_model_class(models_module: Any, class_name: str):
    try:
        return getattr(models_module, class_name)
    except Exception:
        return None


def _get_model_schema_maps(model_class: Any) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    swagger_types = getattr(model_class, "swagger_types", None)
    attribute_map = getattr(model_class, "attribute_map", None)
    if isinstance(swagger_types, dict) and isinstance(attribute_map, dict):
        return swagger_types, attribute_map

    try:
        model_instance = model_class()
    except Exception:
        model_instance = None

    if model_instance is not None:
        if not isinstance(swagger_types, dict):
            swagger_types = getattr(model_instance, "swagger_types", None)
        if not isinstance(attribute_map, dict):
            attribute_map = getattr(model_instance, "attribute_map", None)

    return (
        swagger_types if isinstance(swagger_types, dict) else None,
        attribute_map if isinstance(attribute_map, dict) else None,
    )


def _resolve_polymorphic_model_class(model_class: Any, mapping: Dict[str, Any], models_module: Any) -> Any:
    subtype_resolver = getattr(model_class, "get_subtype", None)
    if not callable(subtype_resolver):
        return model_class

    _, attribute_map = _get_model_schema_maps(model_class)
    discriminator_payload = dict(mapping)
    if isinstance(attribute_map, dict):
        for snake_name, api_name in attribute_map.items():
            if snake_name in mapping and api_name not in discriminator_payload:
                discriminator_payload[api_name] = mapping[snake_name]

    try:
        subtype_name = subtype_resolver(discriminator_payload)
    except Exception:
        return model_class

    subtype_class = _resolve_model_class(models_module, subtype_name) if models_module else None
    return subtype_class if inspect.isclass(subtype_class) else model_class


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
        if operation_name.startswith("list_"):
            return True
        if operation_name.startswith("summarize_"):
            return True

        expected_kwargs = _extract_expected_kwargs_from_source(method)
        if expected_kwargs and (("page" in expected_kwargs) or ("limit" in expected_kwargs)):
            return True

        sig = inspect.signature(method)
        param_names = set(sig.parameters.keys())
        if "page" in param_names or "limit" in param_names:
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
    if not query:
        return 1
    haystack = " ".join(texts).lower()
    q = query.lower().strip()
    if not q:
        return 1
    if query_tokens is None:
        raw_tokens = [token for token in re.split(r"[\s._/-]+", q) if token]
        tokens = [token for token in raw_tokens if token not in _SEARCH_QUERY_STOPWORDS] or raw_tokens
    else:
        tokens = query_tokens
    matched_tokens = [token for token in tokens if token in haystack]
    if q not in haystack and len(matched_tokens) < min(2, len(tokens)):
        return 0
    score = 0
    if q in haystack:
        score += 100
    score += 20 * len(matched_tokens)
    if tokens and len(matched_tokens) == len(tokens):
        score += 20
    score += int(difflib.SequenceMatcher(None, normalized_query or " ".join(tokens) or q, haystack).ratio() * 10)
    return score


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


def _normalized_operation_phrase(operation_name: str) -> str:
    return " ".join(_normalized_query_tokens(operation_name))


def _fallback_client_preference_bonus(query_tokens: List[str], client_fqn: str) -> int:
    for token in query_tokens:
        preferred_clients = _FALLBACK_CLIENT_PREFERENCES.get(token)
        if preferred_clients and client_fqn in preferred_clients:
            return 12
    return 0


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

    if normalized_query and normalized_query == _normalized_operation_phrase(operation_name):
        score += 40

    score += _fallback_client_preference_bonus(query_tokens, client_fqn)
    return score


@lru_cache(maxsize=1)
def _discover_client_classes() -> List[Tuple[str, Any]]:
    discovered: List[Tuple[str, Any]] = []
    seen: set[str] = set()
    for module_info in pkgutil.walk_packages(oci.__path__, prefix="oci."):
        module_name = module_info.name
        if module_name.startswith("oci._"):
            continue
        if not module_name.endswith("_client") or module_name.endswith(".composite_operations"):
            continue
        try:
            module = import_module(module_name)
        except Exception:
            continue
        parent_module_name = module_name.rsplit(".", 1)[0]
        if parent_module_name == "oci" or parent_module_name.startswith("oci._"):
            continue
        try:
            parent_module = import_module(parent_module_name)
        except Exception:
            parent_module = None
        for class_name, cls in inspect.getmembers(module, predicate=inspect.isclass):
            if not class_name.endswith("Client"):
                continue
            if getattr(cls, "__module__", "") != module.__name__:
                continue
            client_fqn = f"{module_name}.{class_name}"
            if parent_module is not None and getattr(parent_module, class_name, None) is cls:
                client_fqn = f"{parent_module_name}.{class_name}"
            if client_fqn in seen:
                continue
            seen.add(client_fqn)
            discovered.append((client_fqn, cls))
    return sorted(discovered, key=lambda item: item[0])


def _get_config_and_signer() -> Tuple[Dict[str, Any], Any]:
    """
    Load OCI config and build an appropriate signer.

    Preference order:
    - If a security_token_file exists, use SecurityTokenSigner (session auth).
    - Otherwise, fall back to API key Signer from config.
    """
    domain = os.getenv("IDCS_DOMAIN")
    client_id = os.getenv("IDCS_CLIENT_ID")
    client_secret = os.getenv("IDCS_CLIENT_SECRET")
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")
    token = None
    if host and port:
        token = get_access_token()
        if token is None:
            raise RuntimeError("HTTP requests require an authenticated IDCS access token.")
    if token is not None:
        if not all((domain, client_id, client_secret)):
            raise RuntimeError(
                "HTTP requests require IDCS authentication. Set IDCS_DOMAIN, IDCS_CLIENT_ID, and IDCS_CLIENT_SECRET."
            )
        region = os.getenv("OCI_REGION")
        if not region:
            raise RuntimeError("HTTP requests require OCI_REGION.")
        config = {"region": region}
        config["additional_user_agent"] = _ADDITIONAL_UA
        return config, oci.auth.signers.TokenExchangeSigner(
            token.token,
            f"https://{domain}",
            client_id,
            client_secret,
            region=config.get("region"),
        )

    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )
    config["additional_user_agent"] = _ADDITIONAL_UA

    token_file = os.path.expanduser(config.get("security_token_file", "") or "")
    try:
        private_key = oci.signer.load_private_key_from_file(config["key_file"])
    except Exception as e:
        logger.error(f"Failed loading private key: {e}")
        raise

    signer = None
    if token_file and os.path.exists(token_file):
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                token = f.read()
            signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
            logger.info("Using SecurityTokenSigner from security_token_file.")
        except Exception as e:
            logger.warning(
                f"Failed to build SecurityTokenSigner from token file, will try API key signer: {e}"
            )

    if signer is None:
        try:
            signer = oci.signer.Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config["key_file"],
                pass_phrase=config.get("pass_phrase"),
            )
            logger.info("Using API key Signer.")
        except Exception as e:
            logger.error(f"Failed to build API key Signer: {e}")
            raise

    return config, signer


def _import_client(client_fqn: str):
    cls = _get_client_class(client_fqn)
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


def _resolve_model_class_from_type_name(type_name: str, models_module: Any) -> Any:
    if not type_name:
        return None
    model_class = _resolve_model_class(models_module, type_name) if models_module else None
    if inspect.isclass(model_class):
        return model_class
    if "." in type_name:
        try:
            module_name, class_name = type_name.rsplit(".", 1)
            module = import_module(module_name)
            model_class = getattr(module, class_name)
            if inspect.isclass(model_class):
                return model_class
        except Exception:
            return None
    return None


def _coerce_value_to_type(value: Any, type_name: Optional[str], models_module: Any) -> Any:
    if value is None or not type_name:
        return value

    coerced_primitive = _coerce_primitive_value(value, type_name)
    if coerced_primitive is not value:
        return coerced_primitive

    compact_type = type_name.replace(" ", "")
    list_match = re.fullmatch(r"list\[(.+)\]", compact_type)
    if list_match and isinstance(value, list):
        inner_type = list_match.group(1)
        return [_coerce_value_to_type(item, inner_type, models_module) for item in value]

    dict_match = re.fullmatch(r"dict\(([^,]+),(.+)\)", compact_type)
    if dict_match and isinstance(value, dict):
        value_type = dict_match.group(2)
        return {key: _coerce_value_to_type(item, value_type, models_module) for key, item in value.items()}

    if isinstance(value, dict):
        model_class = _resolve_model_class_from_type_name(type_name, models_module)
        if inspect.isclass(model_class):
            return _construct_model_from_mapping(
                value,
                models_module,
                [getattr(model_class, "__name__", type_name)],
            )

    return value


def _coerce_mapping_for_model_class(mapping: Dict[str, Any], models_module: Any, model_class: Any) -> Dict[str, Any]:
    swagger_types, _ = _get_model_schema_maps(model_class)
    if not isinstance(swagger_types, dict):
        return mapping
    return {
        key: _coerce_value_to_type(value, swagger_types.get(key), models_module)
        for key, value in mapping.items()
    }


def _coerce_params_to_method_types(client_fqn: str, method: Callable[..., Any], params: Dict[str, Any]) -> Dict[str, Any]:
    if not params:
        return {}
    models_module = _import_models_module_from_client_fqn(client_fqn)
    signature, doc = _inspect_method(method)
    doc_param_types = {
        name: type_name
        for type_name, name in re.findall(r":param\s+([^\s:]+)\s+([A-Za-z0-9_]+)\s*:", doc)
    }
    coerced: Dict[str, Any] = {}
    for key, value in params.items():
        type_name = doc_param_types.get(key)
        if signature and key in signature.parameters:
            annotation_type = _annotation_to_type_name(signature.parameters[key].annotation)
            if annotation_type and annotation_type != "Any":
                type_name = annotation_type
        coerced[key] = _coerce_value_to_type(value, type_name, models_module)
    return coerced


def _coerce_mapping_values(
    mapping: Dict[str, Any], models_module: Any, parent_prefix: Optional[str] = None
) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, val in mapping.items():
        if isinstance(val, dict):
            candidates: List[str] = []
            for suffix in _MODEL_SUFFIXES:
                if key.endswith(suffix):
                    base_camel = _snake_to_camel(key)
                    candidates.append(base_camel)
                    if parent_prefix:
                        candidates.append(f"{parent_prefix}{base_camel}Details")
                        candidates.append(f"{parent_prefix}{base_camel}")
                    break
            out[key] = _construct_model_from_mapping(val, models_module, candidates)
        elif isinstance(val, list):
            new_list = []
            for item in val:
                if isinstance(item, dict):
                    new_list.append(_construct_model_from_mapping(item, models_module, []))
                else:
                    new_list.append(item)
            out[key] = new_list
        else:
            out[key] = val
    return out


def _construct_model_from_mapping(
    mapping: Dict[str, Any], models_module: Any, candidate_classnames: List[str]
):
    fqn = mapping.get("__model_fqn") or mapping.get("__class_fqn")
    class_name = mapping.get("__model") or mapping.get("__class")
    clean = {k: v for k, v in mapping.items() if not k.startswith("__")}
    parent_prefix_hint: Optional[str] = None
    for cand in candidate_classnames:
        if isinstance(cand, str) and cand:
            if cand.endswith("Details"):
                parent_prefix_hint = cand[: -len("Details")]
                break
            if parent_prefix_hint is None:
                parent_prefix_hint = cand
    clean = _coerce_mapping_values(clean, models_module, parent_prefix_hint)
    if isinstance(fqn, str):
        try:
            mod_name, cls_name = fqn.rsplit(".", 1)
            mod = import_module(mod_name)
            cls = getattr(mod, cls_name)
            if inspect.isclass(cls):
                cls = _resolve_polymorphic_model_class(cls, clean, models_module)
                coerced_clean = _coerce_mapping_for_model_class(clean, models_module, cls)
                try:
                    return oci.util.from_dict(cls, coerced_clean)
                except Exception:
                    return cls(**coerced_clean)
        except Exception:
            pass
    if models_module and isinstance(class_name, str):
        cls = _resolve_model_class(models_module, class_name)
        if inspect.isclass(cls):
            cls = _resolve_polymorphic_model_class(cls, clean, models_module)
            filtered_clean = clean
            swagger_types, _ = _get_model_schema_maps(cls)
            if isinstance(swagger_types, dict):
                filtered_clean = {k: v for k, v in clean.items() if k in swagger_types}
            filtered_clean = _coerce_mapping_for_model_class(filtered_clean, models_module, cls)
            try:
                return oci.util.from_dict(cls, filtered_clean)
            except Exception:
                try:
                    return cls(**filtered_clean)
                except Exception:
                    pass
    if models_module:
        for candidate in candidate_classnames:
            cls = _resolve_model_class(models_module, candidate)
            if inspect.isclass(cls):
                cls = _resolve_polymorphic_model_class(cls, clean, models_module)
                filtered_clean = clean
                swagger_types, _ = _get_model_schema_maps(cls)
                if isinstance(swagger_types, dict):
                    filtered_clean = {k: v for k, v in clean.items() if k in swagger_types}
                filtered_clean = _coerce_mapping_for_model_class(filtered_clean, models_module, cls)
                try:
                    return oci.util.from_dict(cls, filtered_clean)
                except Exception:
                    try:
                        return cls(**filtered_clean)
                    except Exception:
                        continue
    return mapping


def _coerce_params_to_oci_models(client_fqn: str, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if not params:
        return {}
    models_module = _import_models_module_from_client_fqn(client_fqn)
    normalized_params = _normalize_details_param_alias(params, operation)
    out: Dict[str, Any] = {}
    for key, val in normalized_params.items():
        if isinstance(val, dict):
            candidates = _candidate_model_class_names(operation, key)
            out[key] = _construct_model_from_mapping(val, models_module, candidates)
        elif isinstance(val, list):
            new_list = []
            for item in val:
                if isinstance(item, dict):
                    if any(hint in item for hint in ("__model_fqn", "__model", "__class_fqn", "__class")):
                        new_list.append(_construct_model_from_mapping(item, models_module, []))
                    else:
                        new_list.append(item)
                else:
                    new_list.append(item)
            out[key] = new_list
        else:
            out[key] = val
    return out


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
    cls = _get_client_class(client_fqn)
    if not hasattr(cls, operation_name):
        suggestions = difflib.get_close_matches(
            operation_name,
            [name for name, _ in _get_public_client_methods(cls)],
            n=5,
            cutoff=0.4,
        )
        raise AttributeError(
            f"Operation '{operation_name}' not found on client '{client_fqn}'."
            + (f" Similar operations: {', '.join(suggestions)}" if suggestions else "")
        )

    method = getattr(cls, operation_name)
    if not callable(method):
        raise AttributeError(f"Attribute '{operation_name}' on client '{client_fqn}' is not callable")

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
        return response_data.items, "dns", response_data.__class__
    if isinstance(response_data, oci.object_storage.models.ListObjects):
        return response_data.objects, "object_storage", None
    if isinstance(response_data, list):
        return response_data, None, None
    items = getattr(response_data, "items", response_data)
    return (response_data if callable(items) else items), None, None


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


def _project_top_level_fields(
    serialized_data: Any, fields: Optional[List[str]]
) -> Tuple[Any, List[str], List[str]]:
    if fields is None:
        return serialized_data, [], []

    if isinstance(serialized_data, dict):
        available_fields = sorted(serialized_data.keys())
        matched_fields = [field for field in fields if field in serialized_data]
        if not matched_fields:
            raise ValueError(
                "None of the requested fields matched top-level response fields. "
                f"Requested: {fields}. Available: {available_fields[:20]}"
            )
        projected_data = {field: serialized_data[field] for field in matched_fields}
        unmatched_fields = [field for field in fields if field not in serialized_data]
        return projected_data, matched_fields, unmatched_fields

    if isinstance(serialized_data, list):
        available_fields = sorted(
            {
                key
                for item in serialized_data
                if isinstance(item, dict)
                for key in item.keys()
            }
        )
        matched_fields = [field for field in fields if field in available_fields]
        if not matched_fields:
            raise ValueError(
                "None of the requested fields matched top-level response fields. "
                f"Requested: {fields}. Available: {available_fields[:20]}"
            )
        projected_data = [
            {field: item[field] for field in matched_fields if field in item} if isinstance(item, dict) else item
            for item in serialized_data
        ]
        unmatched_fields = [field for field in fields if field not in available_fields]
        return projected_data, matched_fields, unmatched_fields

    raise ValueError("fields can only be used with object responses or lists of objects")


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
) -> Tuple[Any, Optional[str], bool]:
    if uses_pagination is None:
        uses_pagination = _supports_pagination(method, operation_name)
    if uses_pagination:
        logger.info(f"Using paginator for operation {operation_name}")
        if max_results is not None:
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

            while remaining_items > 0:
                if isinstance(requested_limit, int) and requested_limit > 0:
                    call_params["limit"] = min(requested_limit, remaining_items)
                else:
                    call_params.pop("limit", None)

                call_result = oci.retry.DEFAULT_RETRY_STRATEGY.make_retrying_call(method, **call_params)
                response_data = call_result.data if hasattr(call_result, "data") else call_result
                available_slots = remaining_items

                current_items, collection_kind, collection_class = _extract_paginated_items(response_data)
                if collection_kind == "dns":
                    is_dns_record_collection = True
                    dns_record_collection_class = collection_class
                elif collection_kind == "object_storage":
                    is_list_objects_response = True
                    if response_data.prefixes:
                        list_objects_prefixes.update(response_data.prefixes)

                if not hasattr(current_items, "__len__") or not hasattr(current_items, "__getitem__"):
                    current_items = list(current_items)
                current_count = len(current_items)
                aggregated_results.extend(islice(current_items, available_slots))
                if current_count > available_slots:
                    more_results_available = True
                remaining_items -= current_count

                if remaining_items <= 0:
                    if is_list_objects_response and getattr(response_data, "next_start_with", None) is not None:
                        more_results_available = True
                    elif getattr(call_result, "has_next_page", False):
                        more_results_available = True
                    break

                if is_list_objects_response:
                    next_start_with = getattr(response_data, "next_start_with", None)
                    if next_start_with is None:
                        break
                    call_params["start"] = next_start_with
                    continue

                if not getattr(call_result, "has_next_page", False):
                    break
                call_params["page"] = call_result.next_page

            response = call_result
            if is_dns_record_collection:
                data = dns_record_collection_class(items=aggregated_results)
            elif is_list_objects_response:
                data = oci.object_storage.models.ListObjects(
                    objects=aggregated_results,
                    prefixes=list(list_objects_prefixes),
                )
            else:
                data = aggregated_results
            has_more = more_results_available
        else:
            response = oci.pagination.list_call_get_all_results(method, **params)
            data = response.data
            has_more = getattr(response, "has_next_page", False)
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
    expected_param_names = []
    if signature is not None:
        expected_param_names = [
            param.name
            for param in signature.parameters.values()
            if param.name != "self" and param.kind != inspect.Parameter.VAR_KEYWORD
        ]

    accepted_kwargs = sorted(_extract_expected_kwargs_from_source(method) or [])
    hints: Dict[str, Any] = {}
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
    try:
        if max_results is not None and max_results < 1:
            raise ValueError("max_results must be >= 1")
        if fields is None:
            normalized_fields = None
        else:
            if not isinstance(fields, list):
                raise ValueError("fields must be a list of non-empty strings")
            raw_fields = fields
            normalized_fields = []
            seen = set()
            for field in raw_fields:
                if not isinstance(field, str) or not field.strip():
                    raise ValueError("fields must contain only non-empty strings")
                cleaned = field.strip()
                if cleaned not in seen:
                    normalized_fields.append(cleaned)
                    seen.add(cleaned)

            if not normalized_fields:
                raise ValueError("fields must contain at least one non-empty string")
        _validate_client_fqn(client_fqn, require_client_class=True)
        client = _import_client(client_fqn)
        if not hasattr(client, operation):
            suggestions = difflib.get_close_matches(
                operation,
                [name for name, _ in _get_public_client_methods(client.__class__)],
                n=5,
                cutoff=0.4,
            )
            raise AttributeError(
                f"Operation '{operation}' not found on client '{client_fqn}'"
                + (f". Similar operations: {', '.join(suggestions)}" if suggestions else "")
            )

        method = getattr(client, operation)
        if not callable(method):
            raise AttributeError(f"Attribute '{operation}' on client '{client_fqn}' is not callable")

        input_params = params or {}
        uses_pagination = _supports_pagination(method, operation)
        typed_params = _coerce_params_to_method_types(client_fqn, method, input_params)
        final_params = _align_params_to_signature(
            method,
            operation,
            _coerce_params_to_oci_models(client_fqn, operation, typed_params),
        )
        logger.debug(f"invoke_oci_api final_params keys: {list(final_params.keys())}")
        logger.debug(f"op: {operation}")
        data, opc_request_id, has_more_results = _call_with_pagination_if_applicable(
            method,
            final_params,
            operation,
            max_results,
            uses_pagination=uses_pagination,
        )

        serialized_data = _serialize_oci_data(data)
        projected_data, matched_fields, unmatched_fields = _project_top_level_fields(serialized_data, normalized_fields)

        effective_result_mode = result_mode
        if result_mode == "auto":
            effective_result_mode = (
                "summary"
                if uses_pagination or operation.startswith("list_") or operation.startswith("summarize_")
                else "full"
            )

        result_meta: Dict[str, Any] = {"result_mode": effective_result_mode, "pagination_used": uses_pagination}
        if max_results is not None:
            result_meta["max_results"] = max_results
        if normalized_fields is not None:
            result_meta["fields"] = matched_fields
            if unmatched_fields:
                result_meta["unmatched_fields"] = unmatched_fields

        if effective_result_mode == "summary":
            rendered_data = _summarize_serialized_data(projected_data, max_results or _DEFAULT_SUMMARY_ITEMS)
        else:
            trim_limit = None if uses_pagination else max_results
            if trim_limit is not None and isinstance(projected_data, list):
                rendered_data = projected_data[:trim_limit]
                truncated = len(projected_data) > trim_limit
            else:
                rendered_data = projected_data
                truncated = False
            if isinstance(projected_data, list):
                result_meta["returned_items"] = len(rendered_data)
                if uses_pagination and has_more_results:
                    result_meta["truncated"] = True
                else:
                    result_meta["total_items"] = len(projected_data)
                    result_meta["truncated"] = truncated

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
        needs_param_hints = any(
            clue in str(exc)
            for clue in (
                "unexpected keyword argument",
                "missing 1 required positional argument",
                "missing required positional argument",
                "required positional arguments",
            )
        )
        try:
            cls = _get_client_class(client_fqn)
            if not hasattr(cls, operation):
                suggestions = difflib.get_close_matches(
                    operation,
                    [name for name, _ in _get_public_client_methods(cls)],
                    n=5,
                    cutoff=0.4,
                )
                if suggestions:
                    error_result["suggested_operations"] = suggestions
            elif needs_param_hints:
                method = getattr(cls, operation)
                if callable(method):
                    operation_help = _describe_operation(client_fqn, operation)
                    error_result["operation_help"] = {
                        "signature": operation_help["signature"],
                        "required_params": [param["name"] for param in operation_help["required_params"]],
                        "accepted_kwargs": operation_help["accepted_kwargs"],
                        "parameter_aliases": operation_help["parameter_aliases"],
                        "request_models": operation_help["request_models"],
                    }
                    error_result.update(_build_param_error_hints(method, operation, params or {}, str(exc)))
        except Exception:
            pass
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
    matched_ops: List[Tuple[int, Dict[str, Any]]] = []
    total_operations = 0
    for name, member in _get_public_client_methods(cls):
        total_operations += 1
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

        entry: Dict[str, Any] = {
            "name": name,
            "summary": summary,
        }
        if include_params:
            entry["params"] = _signature_to_display(name, signature)
        matched_ops.append((score, entry))

    if query:
        matched_ops.sort(key=lambda item: (-item[0], item[1]["name"]))
    else:
        matched_ops.sort(key=lambda item: item[1]["name"])

    selected_ops = matched_ops[:limit] if limit is not None else matched_ops
    operations = [entry for _, entry in selected_ops]

    logger.info(f"Found {len(operations)} operations on {client_fqn}")
    return {
        "client": client_fqn,
        "query": query,
        "total_operations": total_operations,
        "returned_operations": len(operations),
        "operations": operations,
    }


@mcp.tool(
    description=(
        "List OCI Python SDK client classes discoverable in the current environment. "
        "Prefer direct SDK-shaped calls or find_oci_api for task-oriented requests; use this for capability "
        "discovery or debugging."
    )
)
def list_oci_clients() -> dict:
    clients = []
    for client_fqn, cls in _discover_client_classes():
        clients.append(
            {
                "client_fqn": client_fqn,
                "module": client_fqn.rsplit(".", 1)[0],
                "class": getattr(cls, "__name__", client_fqn.rsplit(".", 1)[-1]),
            }
        )
    return {"count": len(clients), "clients": clients}


def main():
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if not (host and port):
        mcp.run()
        return
    domain = os.getenv("IDCS_DOMAIN")
    client_id = os.getenv("IDCS_CLIENT_ID")
    client_secret = os.getenv("IDCS_CLIENT_SECRET")
    base_url = os.getenv("ORACLE_MCP_BASE_URL", "")
    audience = os.getenv("IDCS_AUDIENCE")
    if not all((domain, client_id, client_secret, audience, base_url)):
        raise RuntimeError(
            "HTTP transport requires IDCS authentication. "
            "Set IDCS_DOMAIN, IDCS_CLIENT_ID, IDCS_CLIENT_SECRET, IDCS_AUDIENCE, "
            "ORACLE_MCP_BASE_URL, ORACLE_MCP_HOST, and ORACLE_MCP_PORT."
        )
    mcp.auth = OCIProvider(
        config_url=f"https://{domain}/.well-known/openid-configuration",
        client_id=client_id,
        client_secret=client_secret,
        audience=audience,
        required_scopes=parse_scopes(os.getenv("IDCS_REQUIRED_SCOPES")) or f"openid profile email oci_mcp.{__project__.removeprefix('oracle.oci-').removesuffix('-mcp-server').replace('-', '_')}.invoke".split(),
        base_url=base_url,
    )
    mcp.run(transport="http", host=host, port=int(port))


if __name__ == "__main__":
    main()
