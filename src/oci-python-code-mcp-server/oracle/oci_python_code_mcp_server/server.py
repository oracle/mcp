"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import pkgutil
import re
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from logging import Logger
from typing import Annotated, Any, Callable, Optional

import oci
from fastmcp import FastMCP

from . import __project__, __version__
from .compiler import (
    OciSdkCompileError,
    ResultReference,
    compile_oci_sdk_program,
    resolve_oci_sdk_reference,
)
from .utils import initAuditLogger

logger = Logger(__name__, level="INFO")
initAuditLogger(logger)

mcp = FastMCP(
    name=__project__,
    instructions="""
        This server lets you work with OCI by writing ordinary OCI Python SDK code.
        Public tools:
        - run_oci_sdk_code: the primary action tool for almost every request
        - help_write_oci_sdk_code: a fallback helper when you are stuck or repairing code

        Preferred workflow:
        1. Start by writing OCI Python SDK code that directly satisfies the user's request.
        2. Call run_oci_sdk_code first for ordinary tasks.
        3. Use help_write_oci_sdk_code only if you cannot write plausible OCI Python yet,
           or if a previous run failed and you need repair hints.

        Write OCI Python code naturally. The server translates it into internal OCI SDK execution.
        You do not need to learn any raw JSON invoke contract or server-specific calling convention.
    """,
)

_user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
_ADDITIONAL_UA = f"{_user_agent_name}/{__version__}"
AUTO_PAGINATION_MAX_RESULTS = 100
AUTO_PAGINATION_PAGE_SIZE = 25
ALLOWED_DERIVED_BUILTINS = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "len": len,
}
SEARCH_STOPWORDS = {
    "a",
    "an",
    "the",
    "for",
    "of",
    "to",
    "my",
    "all",
    "with",
    "using",
    "about",
    "show",
    "find",
    "lookup",
    "look",
    "up",
    "sdk",
    "tool",
    "tools",
    "call",
    "calls",
    "operation",
    "operations",
    "python",
    "oci",
    "code",
}


def _get_config_and_signer() -> tuple[dict[str, Any], Any]:
    config = oci.config.from_file(profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE))
    config["additional_user_agent"] = _ADDITIONAL_UA

    token_file = os.path.expanduser(config.get("security_token_file", "") or "")
    try:
        private_key = oci.signer.load_private_key_from_file(config["key_file"])
    except Exception as exc:
        logger.error("Failed loading private key: %s", exc)
        raise

    signer = None
    if token_file and os.path.exists(token_file):
        try:
            with open(token_file, "r", encoding="utf-8") as handle:
                token = handle.read()
            signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
            logger.info("Using SecurityTokenSigner from security_token_file.")
        except Exception as exc:
            logger.warning("Failed to build SecurityTokenSigner from token file: %s", exc)

    if signer is None:
        signer = oci.signer.Signer(
            tenancy=config["tenancy"],
            user=config["user"],
            fingerprint=config["fingerprint"],
            private_key_file_location=config["key_file"],
            pass_phrase=config.get("pass_phrase"),
        )
        logger.info("Using API key Signer.")

    return config, signer


def _canonical_client_alias(cls: Any, module_name: str, class_name: str) -> str:
    module_parts = module_name.split(".")
    for index in range(2, len(module_parts)):
        candidate_module = ".".join(module_parts[:index])
        try:
            candidate = import_module(candidate_module)
        except Exception:
            continue
        if getattr(candidate, class_name, None) is cls:
            return f"{candidate_module}.{class_name}"
    return f"{module_name}.{class_name}"


@lru_cache(maxsize=1)
def _discover_oci_clients() -> tuple[dict[str, str], ...]:
    discovered: list[dict[str, str]] = []
    seen_runtime: set[str] = set()
    seen_public: set[str] = set()

    for module_info in pkgutil.walk_packages(oci.__path__, prefix="oci."):
        module_name = module_info.name
        if ".models" in module_name:
            continue
        try:
            module = import_module(module_name)
        except Exception:
            continue

        for class_name, member in inspect.getmembers(module, inspect.isclass):
            if not class_name.endswith("Client"):
                continue
            if member.__module__ != module.__name__:
                continue

            runtime_client_fqn = f"{module.__name__}.{class_name}"
            public_client = _canonical_client_alias(member, module.__name__, class_name)
            if runtime_client_fqn in seen_runtime or public_client in seen_public:
                continue

            seen_runtime.add(runtime_client_fqn)
            seen_public.add(public_client)
            discovered.append(
                {
                    "client": public_client,
                    "service_module": public_client.rsplit(".", 1)[0],
                    "runtime_client_fqn": runtime_client_fqn,
                    "runtime_module": module.__name__,
                    "class": class_name,
                }
            )

    discovered.sort(key=lambda item: item["client"])
    return tuple(discovered)


def _resolve_client_entry(client_ref: str) -> dict[str, str]:
    if "." not in client_ref:
        raise ValueError("client must be a fully-qualified OCI SDK client like 'oci.identity.IdentityClient'")

    for entry in _discover_oci_clients():
        if client_ref in {entry["client"], entry["runtime_client_fqn"]}:
            return entry
    raise ValueError(f"{client_ref} is not a discoverable OCI SDK client")


def _load_oci_client_class(client_ref: str) -> Any:
    entry = _resolve_client_entry(client_ref)
    module_name, class_name = entry["runtime_client_fqn"].rsplit(".", 1)
    module = import_module(module_name)
    cls = getattr(module, class_name)
    if not inspect.isclass(cls) or cls.__module__ != module.__name__ or not class_name.endswith("Client"):
        raise ValueError(f"{entry['client']} is not a concrete OCI SDK client class")
    return cls


def _import_client(client_ref: str) -> Any:
    entry = _resolve_client_entry(client_ref)
    cls = _load_oci_client_class(client_ref)
    config, signer = _get_config_and_signer()
    logger.info("Instantiating OCI client %s via runtime %s", entry["client"], entry["runtime_client_fqn"])
    return cls(config, signer=signer)


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return "".join(part.capitalize() for part in parts if part)


def _details_param_alias(operation_name: str) -> tuple[Optional[str], Optional[str]]:
    if not (operation_name.startswith("create_") or operation_name.startswith("update_")):
        return None, None
    _, _, suffix = operation_name.partition("_")
    return f"{suffix}_details", f"{operation_name}_details"


def _normalize_operation_params(
    operation_name: str, params: dict[str, Any], expected_param_names: Optional[set[str]] = None
) -> dict[str, Any]:
    normalized = dict(params)
    source_key, dest_key = _details_param_alias(operation_name)
    if not source_key or not dest_key:
        return normalized
    if source_key not in normalized or dest_key in normalized:
        return normalized
    if expected_param_names is None or dest_key in expected_param_names:
        normalized[dest_key] = normalized.pop(source_key)
    return normalized


def _import_models_module_from_client_fqn(client_fqn: str):
    try:
        entry = _resolve_client_entry(client_fqn)
        return import_module(f"{entry['service_module']}.models")
    except Exception:
        return None


def _load_oci_model_class(model_fqn: str):
    if not model_fqn.startswith("oci.") or ".models." not in model_fqn:
        raise ValueError("Only OCI SDK model classes are supported")
    module_name, class_name = model_fqn.rsplit(".", 1)
    module = import_module(module_name)
    cls = getattr(module, class_name)
    if not inspect.isclass(cls) or cls.__module__ != module.__name__:
        raise ValueError(f"{model_fqn} is not a concrete OCI SDK model class")
    return cls


def _resolve_model_class(models_module: Any, class_name: str):
    try:
        return getattr(models_module, class_name)
    except Exception:
        return None


def _extract_internal_model_metadata(
    mapping: dict[str, Any],
) -> tuple[Optional[str], Optional[str], dict[str, Any]]:
    model_fqn: Optional[str] = None
    model_name: Optional[str] = None
    clean: dict[str, Any] = {}

    for key, value in mapping.items():
        if not key.startswith("__"):
            clean[key] = value
            continue
        if key == "__model_fqn":
            if not isinstance(value, str):
                raise ValueError("Internal model FQN metadata must be a string")
            model_fqn = value
            continue
        if key == "__model":
            if not isinstance(value, str):
                raise ValueError("Internal model name metadata must be a string")
            model_name = value
            continue
        raise ValueError(f"Unsupported internal model metadata key: {key}")

    return model_fqn, model_name, clean


def _coerce_mapping_values(
    mapping: dict[str, Any], models_module: Any, parent_prefix: Optional[str] = None
) -> dict[str, Any]:
    suffixes = ("_details", "_config", "_configuration", "_source_details")
    coerced: dict[str, Any] = {}

    for key, value in mapping.items():
        if isinstance(value, dict):
            candidates: list[str] = []
            for suffix in suffixes:
                if key.endswith(suffix):
                    base_camel = _snake_to_camel(key)
                    candidates.append(base_camel)
                    if parent_prefix:
                        candidates.append(f"{parent_prefix}{base_camel}Details")
                        candidates.append(f"{parent_prefix}{base_camel}")
                    break
            coerced[key] = _construct_model_from_mapping(value, models_module, candidates)
            continue
        if isinstance(value, list):
            items: list[Any] = []
            for item in value:
                if isinstance(item, dict):
                    items.append(_construct_model_from_mapping(item, models_module, []))
                else:
                    items.append(item)
            coerced[key] = items
            continue
        coerced[key] = value

    return coerced


def _construct_model_from_mapping(
    mapping: dict[str, Any], models_module: Any, candidate_classnames: list[str]
):
    model_fqn, class_name, clean = _extract_internal_model_metadata(mapping)

    parent_prefix_hint: Optional[str] = None
    for candidate in candidate_classnames:
        if not candidate:
            continue
        if candidate.endswith("Details"):
            parent_prefix_hint = candidate[: -len("Details")]
            break
        if parent_prefix_hint is None:
            parent_prefix_hint = candidate

    clean = _coerce_mapping_values(clean, models_module, parent_prefix=parent_prefix_hint)

    if model_fqn:
        try:
            cls = _load_oci_model_class(model_fqn)
            try:
                return oci.util.from_dict(cls, clean)
            except Exception:
                return cls(**clean)
        except Exception:
            pass

    if models_module and isinstance(class_name, str):
        cls = _resolve_model_class(models_module, class_name)
        if inspect.isclass(cls):
            filtered_clean = clean
            swagger_types = getattr(cls, "swagger_types", None)
            if isinstance(swagger_types, dict):
                filtered_clean = {key: value for key, value in clean.items() if key in swagger_types}
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
            if not inspect.isclass(cls):
                continue
            filtered_clean = clean
            swagger_types = getattr(cls, "swagger_types", None)
            if isinstance(swagger_types, dict):
                filtered_clean = {key: value for key, value in clean.items() if key in swagger_types}
            try:
                return oci.util.from_dict(cls, filtered_clean)
            except Exception:
                try:
                    return cls(**filtered_clean)
                except Exception:
                    continue

    return mapping


def _coerce_params_to_oci_models(client_fqn: str, operation: str, params: dict[str, Any]) -> dict[str, Any]:
    if not params:
        return {}

    models_module = _import_models_module_from_client_fqn(client_fqn)
    suffixes = ("_details", "_config", "_configuration", "_source_details")
    coerced: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, dict):
            candidates: list[str] = []
            for suffix in suffixes:
                if key.endswith(suffix):
                    candidates.append(_snake_to_camel(key))
                    if suffix == "_details":
                        base = _snake_to_camel(key[: -len(suffix)])
                        if operation.startswith("create_"):
                            candidates.append(f"Create{base}Details")
                        elif operation.startswith("update_"):
                            candidates.append(f"Update{base}Details")
                    break
            coerced[key] = _construct_model_from_mapping(value, models_module, candidates)
            continue
        if isinstance(value, list):
            items: list[Any] = []
            for item in value:
                if isinstance(item, dict) and any(hint in item for hint in ("__model_fqn", "__model")):
                    items.append(_construct_model_from_mapping(item, models_module, []))
                else:
                    items.append(item)
            coerced[key] = items
            continue
        coerced[key] = value
    return coerced


def _align_params_to_signature(
    method: Callable[..., Any], operation_name: str, params: dict[str, Any]
) -> dict[str, Any]:
    try:
        signature = inspect.signature(method)
    except Exception:
        return params
    return _normalize_operation_params(operation_name, params, set(signature.parameters.keys()))


def _serialize_oci_data(data: Any) -> Any:
    def ensure_jsonable(obj: Any) -> Any:
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, (list, tuple)):
            return [ensure_jsonable(item) for item in obj]
        if isinstance(obj, dict):
            return {key: ensure_jsonable(value) for key, value in obj.items()}
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


def _extract_expected_kwargs_from_source(method: Callable[..., Any]) -> Optional[set[str]]:
    try:
        source = inspect.getsource(method)
    except Exception:
        return None
    match = re.search(r"expected_kwargs\s*=\s*\[\s*(.*?)\s*\]", source, re.DOTALL)
    if not match:
        return set()
    return set(re.findall(r"['\"]([a-zA-Z0-9_]+)['\"]", match.group(1)))


def _docstring_mentions_pagination(method: Callable[..., Any]) -> bool:
    try:
        doc = inspect.getdoc(method) or ""
    except Exception:
        return False
    return bool(re.search(r":param\s+\w+\s+(page|limit)\b", doc))


def _supports_pagination(method: Callable[..., Any], operation_name: str) -> bool:
    try:
        expected_kwargs = _extract_expected_kwargs_from_source(method)
        if expected_kwargs is not None and (("page" in expected_kwargs) or ("limit" in expected_kwargs)):
            return True

        if _docstring_mentions_pagination(method):
            return True

        signature = inspect.signature(method)
        param_names = set(signature.parameters.keys())
        return "page" in param_names or "limit" in param_names
    except Exception:
        return False


def _should_auto_paginate(
    method: Callable[..., Any], params: dict[str, Any], operation_name: str
) -> bool:
    if "page" in params or "limit" in params:
        return False
    return _supports_pagination(method, operation_name)


def _call_with_pagination_if_applicable(
    method: Callable[..., Any], params: dict[str, Any], operation_name: str
) -> tuple[Any, Optional[str]]:
    if _should_auto_paginate(method, params, operation_name):
        logger.info(
            "Using bounded paginator for operation %s (max %s results, page size %s)",
            operation_name,
            AUTO_PAGINATION_MAX_RESULTS,
            AUTO_PAGINATION_PAGE_SIZE,
        )
        response = oci.pagination.list_call_get_up_to_limit(
            method,
            AUTO_PAGINATION_MAX_RESULTS,
            AUTO_PAGINATION_PAGE_SIZE,
            **params,
        )
        opc_request_id = None
        try:
            opc_request_id = response.headers.get("opc-request-id")
        except Exception:
            pass
        return response.data, opc_request_id

    response = method(**params)
    data = response.data if hasattr(response, "data") else response
    opc_request_id = None
    try:
        opc_request_id = response.headers.get("opc-request-id")
    except Exception:
        pass
    return data, opc_request_id


def _invoke_oci_api(client_fqn: str, operation: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    params = params or {}
    try:
        entry = _resolve_client_entry(client_fqn)
        public_client = entry["client"]
        client = _import_client(client_fqn)
        if not hasattr(client, operation):
            raise AttributeError(f"Operation '{operation}' not found on client '{public_client}'")

        method = getattr(client, operation)
        if not callable(method):
            raise AttributeError(f"Attribute '{operation}' on client '{public_client}' is not callable")

        normalized_params = _align_params_to_signature(method, operation, dict(params))
        final_params = _coerce_params_to_oci_models(client_fqn, operation, normalized_params)
        data, opc_request_id = _call_with_pagination_if_applicable(method, final_params, operation)

        return {
            "client": public_client,
            "operation": operation,
            "opc_request_id": opc_request_id,
            "data": _serialize_oci_data(data),
        }
    except Exception as exc:
        try:
            public_client = _resolve_client_entry(client_fqn)["client"]
        except Exception:
            public_client = client_fqn
        logger.error("Error invoking OCI API %s.%s: %s", public_client, operation, exc)
        return {
            "client": public_client,
            "operation": operation,
            "error": str(exc),
        }


def _signature_without_self(signature: inspect.Signature) -> str:
    parts = [str(param) for param in signature.parameters.values() if param.name != "self"]
    return f"({', '.join(parts)})"


def _format_method_ref(client: str, operation: str) -> str:
    return f"{client}.{operation}"


def _format_call_stub(client: str, operation: str, signature: inspect.Signature) -> str:
    params = [param for param in signature.parameters.values() if param.name != "self"]
    if not params:
        return f"{client}.{operation}()"

    lines = [f"{client}.{operation}("]
    for param in params:
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            lines.append("    # optional SDK kwargs")
            continue
        default = "<value>"
        if param.default is not inspect.Parameter.empty and isinstance(param.default, (str, int, float, bool)):
            default = repr(param.default)
        elif param.default is None:
            default = "None"
        lines.append(f"    {param.name}={default},")
    lines.append(")")
    return "\n".join(lines)


def _request_model_hints(operation: str, signature: inspect.Signature) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    suffixes = ("_details", "_config", "_configuration", "_source_details")
    for param in signature.parameters.values():
        if param.name == "self":
            continue
        for suffix in suffixes:
            if not param.name.endswith(suffix):
                continue
            candidates = [_snake_to_camel(param.name)]
            if suffix == "_details":
                base = _snake_to_camel(param.name[: -len(suffix)])
                if operation.startswith("create_"):
                    candidates.append(f"Create{base}Details")
                elif operation.startswith("update_"):
                    candidates.append(f"Update{base}Details")
            hints.append({"param": param.name, "candidates": list(dict.fromkeys(candidates))})
            break
    return hints


def _describe_operation_metadata(client: str, operation: str, method: Callable[..., Any]) -> dict[str, Any]:
    try:
        signature = inspect.signature(method)
    except Exception:
        signature = inspect.Signature()

    summary = ""
    try:
        doc = (inspect.getdoc(method) or "").strip()
        summary = doc.splitlines()[0] if doc else ""
    except Exception:
        pass

    required_params: list[str] = []
    optional_params: list[str] = []
    for param in signature.parameters.values():
        if param.name == "self" or param.kind == inspect.Parameter.VAR_KEYWORD:
            continue
        target_list = required_params if param.default is inspect.Parameter.empty else optional_params
        target_list.append(param.name)

    return {
        "client": client,
        "operation": operation,
        "method_ref": _format_method_ref(client, operation),
        "summary": summary,
        "signature": f"{client}.{operation}{_signature_without_self(signature)}",
        "call_stub": _format_call_stub(client, operation, signature),
        "required_params": required_params,
        "optional_params": optional_params,
        "accepted_kwargs": sorted(_extract_expected_kwargs_from_source(method) or []),
        "request_model_hints": _request_model_hints(operation, signature),
        "supports_pagination": _supports_pagination(method, operation),
    }


@lru_cache(maxsize=1)
def _discover_operation_catalog() -> tuple[dict[str, Any], ...]:
    operations: list[dict[str, Any]] = []
    for entry in _discover_oci_clients():
        cls = _load_oci_client_class(entry["client"])
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name.startswith("_"):
                continue
            operations.append(_describe_operation_metadata(entry["client"], name, member))
    operations.sort(key=lambda item: (item["client"], item["operation"]))
    return tuple(operations)


def _normalize_search_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for raw in re.findall(r"[a-zA-Z0-9]+", text.lower()):
        if raw in SEARCH_STOPWORDS:
            continue
        candidates = [raw]
        if len(raw) > 3 and raw.endswith("s"):
            candidates.append(raw[:-1])
        for candidate in candidates:
            if candidate and candidate not in SEARCH_STOPWORDS and candidate not in seen:
                seen.add(candidate)
                tokens.append(candidate)
    return tokens


def _score_operation_match(query: str, metadata: dict[str, Any]) -> int:
    query_text = query.strip().lower()
    sanitized_query = re.sub(r"\(.*\)", "", query_text).strip()
    method_ref = metadata["method_ref"].lower()
    client_text = metadata["client"].lower()
    operation_text = metadata["operation"].lower()
    summary_text = (metadata.get("summary") or "").lower()
    signature_text = metadata.get("signature", "").lower()

    score = 0
    if sanitized_query and sanitized_query == method_ref:
        score += 150
    elif sanitized_query and sanitized_query in method_ref:
        score += 90

    tokens = _normalize_search_tokens(query_text)
    if not tokens:
        return score

    operation_tokens = set(re.findall(r"[a-z0-9]+", operation_text.replace("_", " ")))
    client_tokens = set(re.findall(r"[a-z0-9]+", client_text))
    matched_tokens = 0
    for token in tokens:
        token_score = 0
        if token == operation_text:
            token_score = max(token_score, 40)
        if token in operation_tokens:
            token_score = max(token_score, 28)
        elif token in operation_text:
            token_score = max(token_score, 20)
        if token in client_tokens or token in client_text:
            token_score = max(token_score, 12)
        if token in summary_text:
            token_score = max(token_score, 8)
        if token in signature_text:
            token_score = max(token_score, 5)
        if token_score:
            matched_tokens += 1
            score += token_score

    if matched_tokens == len(tokens):
        score += 20
    if operation_text.startswith("list_") and "list" in tokens:
        score += 6
    if operation_text.startswith("get_") and "get" in tokens:
        score += 6
    if operation_text.startswith("create_") and any(token in {"create", "launch"} for token in tokens):
        score += 6
    if operation_text.startswith("delete_") and any(token in {"delete", "remove"} for token in tokens):
        score += 6

    return score


def _compile_oci_sdk_code(source: str) -> dict[str, Any]:
    plan = compile_oci_sdk_program(source, best_effort=True)
    return {
        "mode": "call" if len(plan["steps"]) == 1 else "procedure",
        "steps": plan["steps"],
        "program": plan["program"],
        "static_bindings": plan["static_bindings"],
        "setup_bindings": plan["setup_bindings"],
        "translation_warnings": plan.get("translation_warnings", []),
    }


def _collect_result_labels(value: Any) -> set[str]:
    if isinstance(value, ResultReference):
        return {value.label}
    if isinstance(value, list):
        labels: set[str] = set()
        for item in value:
            labels.update(_collect_result_labels(item))
        return labels
    if isinstance(value, dict):
        labels = set()
        for item in value.values():
            labels.update(_collect_result_labels(item))
        return labels
    return set()


def _preview_compiled_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    preview: list[dict[str, Any]] = []
    for index, step in enumerate(steps, start=1):
        try:
            public_client = _resolve_client_entry(step["client_fqn"])["client"]
        except Exception:
            public_client = step["client_fqn"]

        item = {
            "step": index,
            "method_ref": _format_method_ref(public_client, step["operation"]),
            "argument_names": list(step.get("params", {}).keys()),
        }
        if "label" in step:
            item["label"] = step["label"]

        references = sorted(_collect_result_labels(step.get("params", {})))
        if references:
            item["references"] = references
        preview.append(item)
    return preview


def _public_step_result(step_result: dict[str, Any]) -> dict[str, Any]:
    public = {
        "method_ref": _format_method_ref(step_result["client"], step_result["operation"]),
    }
    if "opc_request_id" in step_result:
        public["opc_request_id"] = step_result["opc_request_id"]
    if "data" in step_result:
        public["data"] = step_result["data"]
    if "error" in step_result:
        public["error"] = step_result["error"]
    return public


@dataclass
class _RuntimeResult:
    data: Any


def _runtime_attr(current: Any, attr: str) -> Any:
    if isinstance(current, _RuntimeResult):
        if attr == "data":
            return current.data
        current = current.data
    if isinstance(current, dict):
        if attr in current:
            return current[attr]
        raise AttributeError(attr)
    return getattr(current, attr)


def _runtime_item(current: Any, piece: Any) -> Any:
    if isinstance(current, _RuntimeResult):
        current = current.data
    return current[piece]


def _resolve_runtime_path(current: Any, path: tuple[tuple[str, Any], ...]) -> Any:
    for kind, piece in path:
        if kind == "index":
            current = _runtime_item(current, piece)
            continue
        if kind == "key":
            current = _runtime_item(current, piece)
            continue
        current = _runtime_attr(current, piece)
    return current


def _resolve_runtime_value(value: Any, runtime_bindings: dict[str, Any]) -> Any:
    if isinstance(value, ResultReference):
        if value.label not in runtime_bindings:
            raise ValueError(f"Bound value '{value.label}' is not available yet")
        return _resolve_runtime_path(runtime_bindings[value.label], value.path)
    if isinstance(value, list):
        return [_resolve_runtime_value(item, runtime_bindings) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_runtime_value(item, runtime_bindings) for key, item in value.items()}
    return value


def _resolve_step_params(params: dict[str, Any], runtime_bindings: dict[str, Any]) -> dict[str, Any]:
    return {key: _resolve_runtime_value(value, runtime_bindings) for key, value in params.items()}


def _iter_runtime_values(value: Any) -> list[Any]:
    if isinstance(value, _RuntimeResult):
        value = value.data
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    raise ValueError("Only list-like values can be iterated in derived output")


def _setup_dotted_path(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _setup_dotted_path(node.value)
        if base:
            return f"{base}.{node.attr}"
    return None


def _setup_binding_value(source: str, *, active_config: dict[str, Any]) -> Optional[Any]:
    try:
        expr = ast.parse(source, mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(expr, ast.Call):
        return None
    if expr.args or expr.keywords:
        return None
    if _setup_dotted_path(expr.func) != "oci.config.from_file":
        return None
    return deepcopy(active_config)


def _materialize_setup_bindings(setup_sources: dict[str, str], *, active_config: dict[str, Any]) -> dict[str, Any]:
    setup_bindings: dict[str, Any] = {}
    for name, source in setup_sources.items():
        value = _setup_binding_value(source, active_config=active_config)
        if value is not None:
            setup_bindings[name] = value
    return setup_bindings


def _eval_runtime_expr(
    node: ast.AST, runtime_bindings: dict[str, Any], local_bindings: Optional[dict[str, Any]] = None
) -> Any:
    local_bindings = local_bindings or {}

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in local_bindings:
            return local_bindings[node.id]
        if node.id in runtime_bindings:
            value = runtime_bindings[node.id]
            if isinstance(value, ResultReference):
                return _resolve_runtime_value(value, runtime_bindings)
            return value
        raise ValueError(f"Unknown value '{node.id}'")
    if isinstance(node, ast.List):
        return [_eval_runtime_expr(item, runtime_bindings, local_bindings) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return [_eval_runtime_expr(item, runtime_bindings, local_bindings) for item in node.elts]
    if isinstance(node, ast.Dict):
        compiled: dict[str, Any] = {}
        for key_node, value_node in zip(node.keys, node.values, strict=True):
            if key_node is None:
                raise ValueError("Dict unpacking is not supported")
            key = _eval_runtime_expr(key_node, runtime_bindings, local_bindings)
            compiled[key] = _eval_runtime_expr(value_node, runtime_bindings, local_bindings)
        return compiled
    if isinstance(node, ast.Attribute):
        base = _eval_runtime_expr(node.value, runtime_bindings, local_bindings)
        return _runtime_attr(base, node.attr)
    if isinstance(node, ast.Subscript):
        base = _eval_runtime_expr(node.value, runtime_bindings, local_bindings)
        piece = _eval_runtime_expr(node.slice, runtime_bindings, local_bindings)
        return _runtime_item(base, piece)
    if isinstance(node, ast.ListComp):
        generator = node.generators[0]
        iterable = _iter_runtime_values(_eval_runtime_expr(generator.iter, runtime_bindings, local_bindings))
        results = []
        for item in iterable:
            nested_locals = dict(local_bindings)
            nested_locals[generator.target.id] = item
            keep = True
            for condition in generator.ifs:
                if not _eval_runtime_expr(condition, runtime_bindings, nested_locals):
                    keep = False
                    break
            if keep:
                results.append(_eval_runtime_expr(node.elt, runtime_bindings, nested_locals))
        return results
    if isinstance(node, ast.Compare):
        left = _eval_runtime_expr(node.left, runtime_bindings, local_bindings)
        for operator, comparator_node in zip(node.ops, node.comparators, strict=True):
            right = _eval_runtime_expr(comparator_node, runtime_bindings, local_bindings)
            if isinstance(operator, ast.Eq):
                passed = left == right
            elif isinstance(operator, ast.NotEq):
                passed = left != right
            elif isinstance(operator, ast.In):
                passed = left in right
            elif isinstance(operator, ast.NotIn):
                passed = left not in right
            elif isinstance(operator, ast.Lt):
                passed = left < right
            elif isinstance(operator, ast.LtE):
                passed = left <= right
            elif isinstance(operator, ast.Gt):
                passed = left > right
            elif isinstance(operator, ast.GtE):
                passed = left >= right
            else:
                raise ValueError("That comparison is not supported in derived output")
            if not passed:
                return False
            left = right
        return True
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            for value in node.values:
                result = _eval_runtime_expr(value, runtime_bindings, local_bindings)
                if not result:
                    return result
            return result
        if isinstance(node.op, ast.Or):
            for value in node.values:
                result = _eval_runtime_expr(value, runtime_bindings, local_bindings)
                if result:
                    return result
            return result
        raise ValueError("That boolean expression is not supported in derived output")
    if isinstance(node, ast.UnaryOp):
        operand = _eval_runtime_expr(node.operand, runtime_bindings, local_bindings)
        if isinstance(node.op, ast.Not):
            return not operand
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise ValueError("That unary expression is not supported in derived output")
    if isinstance(node, ast.Call):
        if any(keyword.arg is None for keyword in node.keywords):
            raise ValueError("Only simple keyword-free builtins are supported in derived output")
        if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_DERIVED_BUILTINS:
            raise ValueError("Only simple builtins like str(...), int(...), float(...), bool(...), and len(...) are supported in derived output")
        func = ALLOWED_DERIVED_BUILTINS[node.func.id]
        args = [_eval_runtime_expr(arg, runtime_bindings, local_bindings) for arg in node.args]
        kwargs = {keyword.arg: _eval_runtime_expr(keyword.value, runtime_bindings, local_bindings) for keyword in node.keywords}
        return func(*args, **kwargs)
    raise ValueError("This derived Python expression is not supported yet")


def _unwrap_runtime_value(value: Any) -> Any:
    if isinstance(value, _RuntimeResult):
        return _unwrap_runtime_value(value.data)
    if isinstance(value, list):
        return [_unwrap_runtime_value(item) for item in value]
    if isinstance(value, tuple):
        return [_unwrap_runtime_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _unwrap_runtime_value(item) for key, item in value.items()}
    return value


def _public_operation_help(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "method_ref": metadata["method_ref"],
        "signature": metadata["signature"],
        "call_stub": metadata["call_stub"],
        "summary": metadata["summary"],
        "required_params": metadata["required_params"],
        "optional_params": metadata["optional_params"],
        "accepted_kwargs": metadata["accepted_kwargs"],
        "request_model_hints": metadata["request_model_hints"],
        "supports_pagination": metadata["supports_pagination"],
    }


@mcp.tool(
    description=(
        "Primary action tool: use this first for ordinary OCI tasks. "
        "Write ordinary OCI Python SDK code and the server will translate it internally."
    )
)
def run_oci_sdk_code(
    source: Annotated[
        str,
        "Write the OCI Python SDK snippet that should satisfy the user's request. Start here before asking for help.",
    ],
    execute: Annotated[
        bool,
        "When false, only compile and preview the planned OCI SDK calls.",
    ] = True,
) -> dict[str, Any]:
    try:
        compiled = _compile_oci_sdk_code(source)
    except OciSdkCompileError as exc:
        return {
            "source": source,
            "error": (
                "The server could not translate this OCI Python snippet yet. "
                "Supported patterns include OCI imports, client construction, SDK calls, "
                "simple bindings, references to earlier results, and simple list-style output shaping."
            ),
            "details": str(exc),
            "error_type": "compile_error",
        }

    steps = compiled["steps"]
    if not execute:
        preview = {
            "source": source,
            "mode": compiled["mode"],
            "executed": False,
            "step_count": len(steps),
            "preview_steps": _preview_compiled_steps(steps),
        }
        if compiled.get("translation_warnings"):
            preview["translation_warnings"] = compiled["translation_warnings"]
        final_program_item = compiled["program"][-1] if compiled["program"] else None
        if final_program_item and final_program_item["type"] in {"bind", "output"}:
            preview["output_expression"] = final_program_item["source"]
        return preview

    results: list[dict[str, Any]] = []
    try:
        config, _ = _get_config_and_signer()
        runtime_bindings: dict[str, Any] = _materialize_setup_bindings(
            compiled.get("setup_bindings", {}),
            active_config=config,
        )
    except Exception as exc:
        return {
            "source": source,
            "error": "The server could not prepare the OCI SDK setup values in this snippet yet.",
            "details": str(exc),
            "error_type": "setup_error",
        }
    runtime_bindings.update({name: deepcopy(value) for name, value in compiled.get("static_bindings", {}).items()})
    step_index = 0
    explicit_output = None

    for program_item in compiled["program"]:
        if program_item["type"] == "call":
            step_index += 1
            try:
                resolved_params = _resolve_step_params(program_item.get("params", {}), runtime_bindings)
            except Exception as exc:
                step_result = {
                    "method_ref": _format_method_ref(
                        _resolve_client_entry(program_item["client_fqn"])["client"],
                        program_item["operation"],
                    ),
                    "error": str(exc),
                }
                if "label" in program_item:
                    step_result["label"] = program_item["label"]
                results.append(step_result)
                if compiled["mode"] == "call":
                    response = {
                        "source": source,
                        "executed": True,
                        **step_result,
                    }
                    if compiled.get("translation_warnings"):
                        response["translation_warnings"] = compiled["translation_warnings"]
                    return response
                return {
                    "source": source,
                    "mode": compiled["mode"],
                    "executed": True,
                    "step_count": len(steps),
                    "completed_steps": len(results),
                    "failed_step": step_index,
                    "results": results,
                    "error": step_result["error"],
                }

            internal_result = _invoke_oci_api(
                program_item["client_fqn"],
                program_item["operation"],
                resolved_params,
            )
            step_result = _public_step_result(internal_result)
            if "label" in program_item:
                step_result = {"label": program_item["label"], **step_result}
                if "data" in internal_result:
                    runtime_bindings[program_item["label"]] = _RuntimeResult(internal_result["data"])
            results.append(step_result)

            if "error" in step_result:
                if compiled["mode"] == "call":
                    response = {
                        "source": source,
                        "executed": True,
                        **step_result,
                    }
                    if compiled.get("translation_warnings"):
                        response["translation_warnings"] = compiled["translation_warnings"]
                    return response
                return {
                    "source": source,
                    "mode": "procedure",
                    "executed": True,
                    "step_count": len(steps),
                    "completed_steps": len(results),
                    "failed_step": step_index,
                    "results": results,
                    "error": step_result["error"],
                }
            continue

        if program_item["type"] == "bind":
            try:
                runtime_bindings[program_item["label"]] = _eval_runtime_expr(
                    program_item["expr"], runtime_bindings
                )
            except Exception as exc:
                return {
                    "source": source,
                    "mode": compiled["mode"],
                    "executed": True,
                    "step_count": len(steps),
                    "completed_steps": len(results),
                    "results": results,
                    "error": str(exc),
                }
            if program_item.get("final"):
                explicit_output = runtime_bindings[program_item["label"]]
            continue

        if program_item["type"] == "output":
            try:
                explicit_output = _eval_runtime_expr(program_item["expr"], runtime_bindings)
            except Exception as exc:
                return {
                    "source": source,
                    "mode": compiled["mode"],
                    "executed": True,
                    "step_count": len(steps),
                    "completed_steps": len(results),
                    "results": results,
                    "error": str(exc),
                }
            continue

    if compiled["mode"] == "call":
        result = dict(results[0])
        result["source"] = source
        result["executed"] = True
        if compiled.get("translation_warnings"):
            result["translation_warnings"] = compiled["translation_warnings"]
        if explicit_output is not None:
            result["output"] = _serialize_oci_data(_unwrap_runtime_value(explicit_output))
        return result

    response = {
        "source": source,
        "mode": "procedure",
        "executed": True,
        "step_count": len(steps),
        "completed_steps": len(results),
        "results": results,
    }
    if explicit_output is not None:
        response["output"] = _serialize_oci_data(_unwrap_runtime_value(explicit_output))
    if compiled.get("translation_warnings"):
        response["translation_warnings"] = compiled["translation_warnings"]
    return response


@mcp.tool(
    description=(
        "Fallback helper: only use this when you are stuck or repairing code. "
        "It returns likely OCI SDK calls, call stubs, and parameter hints from a task, "
        "partial OCI Python snippet, or method reference."
    )
)
def help_write_oci_sdk_code(
    query: Annotated[
        str,
        "A user task, failed OCI Python attempt, partial snippet, or method reference to help you write OCI Python code.",
    ],
    limit: Annotated[int, "Maximum number of likely OCI SDK operations to return"] = 5,
) -> dict[str, Any]:
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    try:
        reference = resolve_oci_sdk_reference(query)
        entry = _resolve_client_entry(reference["client_fqn"])
        public_client = entry["client"]
        cls = _load_oci_client_class(reference["client_fqn"])
        operation = reference["operation"]
        if not hasattr(cls, operation):
            raise AttributeError(f"Operation '{operation}' not found on client '{public_client}'")
        method = getattr(cls, operation)
        if not callable(method):
            raise AttributeError(f"Attribute '{operation}' on client '{public_client}' is not callable")
        metadata = _describe_operation_metadata(public_client, operation, method)
        return {
            "query": query,
            "count": 1,
            "matches": [_public_operation_help(metadata)],
        }
    except Exception:
        pass

    scored_matches: list[tuple[int, dict[str, Any]]] = []
    for metadata in _discover_operation_catalog():
        score = _score_operation_match(query, metadata)
        if score > 0:
            scored_matches.append((score, metadata))

    scored_matches.sort(
        key=lambda item: (
            -item[0],
            len(item[1]["signature"]),
            item[1]["client"],
            item[1]["operation"],
        )
    )

    matches = [_public_operation_help(metadata) for _, metadata in scored_matches[:limit]]
    return {"query": query, "count": len(matches), "matches": matches}


def main() -> None:
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")
    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
