"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import inspect
import json
import os
import pkgutil
import re
from importlib import import_module
from logging import Logger
from typing import Annotated, Any, Callable, Dict, List, Optional, Tuple

import oci
from fastmcp import FastMCP

from . import __project__, __version__
from .utils import initAuditLogger

logger = Logger(__name__, level="INFO")

initAuditLogger(logger)

mcp = FastMCP(
    name=__project__,
    instructions="""
        This server provides tools to interact directly with the OCI Python SDK,
        invoking API clients and operations in-process (no CLI).
        - invoke_oci_api: Call any OCI SDK client operation by FQN and method.
        - list_client_operations: Discover available operations on a client.
        - get_client_operation_details: Inspect one operation including expected kwargs.
    """,
)

_user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
_ADDITIONAL_UA = f"{_user_agent_name}/{__version__}"

# Backwards-compat pagination allowlist placeholder.
# Heuristic detection handles most cases; keep an empty set to avoid NameError
# in any residual fallback checks.
known_paginated: set = set()


def _get_config_and_signer() -> Tuple[Dict[str, Any], Any]:
    """
    Load OCI config and build an appropriate signer.

    Preference order:
    - If a security_token_file exists, use SecurityTokenSigner (session auth).
    - Otherwise, fall back to API key Signer from config.
    """
    config = oci.config.from_file(profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE))
    config["additional_user_agent"] = _ADDITIONAL_UA

    # try security token
    token_file = os.path.expanduser(config.get("security_token_file", "") or "")
    try:
        private_key = oci.signer.load_private_key_from_file(config["key_file"])
    except Exception as e:
        logger.error(f"Failed loading private key: {e}")
        raise

    signer = None
    if token_file and os.path.exists(token_file):
        try:
            with open(token_file, "r") as f:
                token = f.read()
            signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
            logger.info("Using SecurityTokenSigner from security_token_file.")
        except Exception as e:
            logger.warning(
                f"Failed to build SecurityTokenSigner from token file, will try API key signer: {e}"
            )

    if signer is None:
        # fall back to API key signer
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


def _import_client(client_fqn: str) -> Any:
    """
    Import and instantiate an OCI SDK Client given a fully-qualified class name.
    Example: 'oci.core.ComputeClient'
    """
    if "." not in client_fqn:
        raise ValueError("client_fqn must be a fully-qualified class name like 'oci.core.ComputeClient'")
    module_name, class_name = client_fqn.rsplit(".", 1)
    module = import_module(module_name)
    cls = getattr(module, class_name)
    if not inspect.isclass(cls):
        raise ValueError(f"{client_fqn} is not a class")
    config, signer = _get_config_and_signer()
    instance = cls(config, signer=signer)
    return instance


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return "".join(p.capitalize() for p in parts if p)


def _resolve_model_class_from_swagger_type(
    swagger_type: str, models_module: Any
) -> Optional[type]:
    """
    Resolve an OCI SDK model class from a swagger type string.

    Examples:
      - "InstanceOptions" -> models.InstanceOptions
      - "list[IngressSecurityRule]" -> models.IngressSecurityRule
      - "dict(str, TcpOptions)" -> models.TcpOptions
    """
    if not models_module or not isinstance(swagger_type, str):
        return None

    t = swagger_type.strip()

    m_list = re.match(r"^list\[(.+)\]$", t)
    if m_list:
        return _resolve_model_class_from_swagger_type(
            m_list.group(1).strip(), models_module
        )

    m_dict = re.match(r"^dict\(\s*[^,]+,\s*(.+)\)$", t)
    if m_dict:
        return _resolve_model_class_from_swagger_type(
            m_dict.group(1).strip(), models_module
        )

    primitives = {
        "str",
        "int",
        "float",
        "bool",
        "object",
        "datetime",
        "date",
    }
    if t in primitives:
        return None

    class_name = t.rsplit(".", 1)[-1]
    cls = _resolve_model_class(models_module, class_name)
    return cls if inspect.isclass(cls) else None


def _resolve_discriminated_model_class(
    swagger_type: str, payload: Dict[str, Any], models_module: Any
) -> Optional[type]:
    """
    Resolve a more specific model class when payload contains a discriminator-like field.

    Example:
      swagger_type = "InstanceSourceDetails", payload.source_type = "image"
      -> InstanceSourceViaImageDetails
    """
    if not models_module or not isinstance(payload, dict) or not isinstance(swagger_type, str):
        return None

    discriminator = payload.get("source_type")
    if not isinstance(discriminator, str):
        discriminator = payload.get("sourceType")
    if not isinstance(discriminator, str):
        return None

    norm = re.sub(r"[^a-zA-Z0-9]+", "_", discriminator).strip("_")
    if not norm:
        return None
    discr_token = _snake_to_camel(norm.lower())

    candidates: List[str] = []
    if swagger_type.endswith("Details"):
        prefix = swagger_type[: -len("Details")]
        candidates.append(f"{prefix}Via{discr_token}Details")
        candidates.append(f"{prefix}{discr_token}Details")

    for cand in candidates:
        cls = _resolve_model_class(models_module, cand)
        if inspect.isclass(cls):
            return cls
    return None


def _normalize_value_for_swagger_type(
    value: Any, swagger_type: str, models_module: Any, use_wire_keys: bool = False
) -> Any:
    """
    Normalize nested dict/list payloads to SDK attribute_map keys based on swagger type.
    """
    if not isinstance(swagger_type, str):
        return value

    t = swagger_type.strip()

    if isinstance(value, list):
        m_list = re.match(r"^list\[(.+)\]$", t)
        if not m_list:
            return value
        item_type = m_list.group(1).strip()
        return [
            _normalize_value_for_swagger_type(
                item, item_type, models_module, use_wire_keys=use_wire_keys
            )
            for item in value
        ]

    if isinstance(value, dict):
        m_dict = re.match(r"^dict\(\s*[^,]+,\s*(.+)\)$", t)
        if m_dict:
            val_type = m_dict.group(1).strip()
            return {
                k: _normalize_value_for_swagger_type(
                    v, val_type, models_module, use_wire_keys=use_wire_keys
                )
                for k, v in value.items()
            }

        nested_cls = _resolve_discriminated_model_class(t, value, models_module)
        if not nested_cls:
            nested_cls = _resolve_model_class_from_swagger_type(t, models_module)
        if nested_cls:
            normalized = _normalize_mapping_for_model(
                value, nested_cls, models_module, use_wire_keys=use_wire_keys
            )
            # Prefer passing real nested model instances to parent constructors.
            try:
                return _construct_model_with_class(normalized, nested_cls, models_module)
            except Exception:
                return normalized

    return value


def _normalize_mapping_for_model(
    payload: Dict[str, Any],
    model_cls: type,
    models_module: Any,
    use_wire_keys: bool,
) -> Dict[str, Any]:
    """
    Convert a model payload from snake_case attribute names to the SDK wire keys
    defined in model_cls.attribute_map, recursively for nested model fields.
    """
    if not isinstance(payload, dict):
        return payload

    swagger_types, attribute_map = _get_model_schema(model_cls)
    if not isinstance(swagger_types, dict):
        return payload
    if not isinstance(attribute_map, dict):
        attribute_map = {}

    reverse_attribute_map = {
        wire: attr for attr, wire in attribute_map.items() if isinstance(wire, str)
    }

    normalized: Dict[str, Any] = {}
    for in_key, raw_value in payload.items():
        attr_key = in_key if in_key in swagger_types else reverse_attribute_map.get(in_key)
        if attr_key in swagger_types:
            out_key = attribute_map.get(attr_key, in_key) if use_wire_keys else attr_key
            normalized[out_key] = _normalize_value_for_swagger_type(
                raw_value,
                swagger_types[attr_key],
                models_module,
                use_wire_keys=use_wire_keys,
            )
        else:
            normalized[in_key] = raw_value

    return normalized


def _get_model_schema(model_cls: type) -> Tuple[Optional[Dict[str, str]], Optional[Dict[str, str]]]:
    """
    Return (swagger_types, attribute_map) for an OCI model class.

    OCI SDK 2.160.0 exposes these on instances (not classes), while older
    versions may expose them on the class. Support both.
    """
    swagger_types = getattr(model_cls, "swagger_types", None)
    attribute_map = getattr(model_cls, "attribute_map", None)
    if isinstance(swagger_types, dict):
        if not isinstance(attribute_map, dict):
            attribute_map = {}
        return swagger_types, attribute_map

    try:
        inst = model_cls()
        swagger_types = getattr(inst, "swagger_types", None)
        attribute_map = getattr(inst, "attribute_map", None)
        if isinstance(swagger_types, dict):
            if not isinstance(attribute_map, dict):
                attribute_map = {}
            return swagger_types, attribute_map
    except Exception:
        pass

    return None, None


def _from_dict_if_available(model_cls: type, payload: Dict[str, Any]):
    """
    Best-effort wrapper for SDKs that expose oci.util.from_dict.
    OCI SDK 2.160.0 does not expose this symbol.
    """
    from_dict = getattr(oci.util, "from_dict", None)
    if callable(from_dict):
        return from_dict(model_cls, payload)
    raise AttributeError("oci.util.from_dict is not available")


def _to_model_attribute_map_keys(
    payload: Dict[str, Any], model_cls: type, models_module: Any
) -> Dict[str, Any]:
    """
    Convert to SDK wire keys (camelCase) using attribute_map.
    Kept for compatibility with existing tests/helpers.
    """
    return _normalize_mapping_for_model(
        payload, model_cls, models_module, use_wire_keys=True
    )


def _to_model_attribute_keys(
    payload: Dict[str, Any], model_cls: type, models_module: Any
) -> Dict[str, Any]:
    """
    Convert payload keys to model attribute names (snake_case) recursively.
    This is the most robust input shape for oci.util.from_dict/constructors.
    """
    return _normalize_mapping_for_model(
        payload, model_cls, models_module, use_wire_keys=False
    )


def _import_models_module_from_client_fqn(client_fqn: str):
    try:
        # Typical OCI client FQNs look like:
        #   oci.core.compute_client.ComputeClient
        # and models live at:
        #   oci.core.models
        parts = client_fqn.split(".")
        candidates: List[str] = []

        if len(parts) >= 3:
            # preferred: drop "<module>.<ClassName>"
            candidates.append(".".join(parts[:-2]) + ".models")
        if len(parts) >= 2:
            # fallback for simpler FQNs used in tests/mocks: "x.y.Client" -> "x.y.models"
            candidates.append(".".join(parts[:-1]) + ".models")

        seen = set()
        for mod_name in candidates:
            if mod_name in seen:
                continue
            seen.add(mod_name)
            try:
                return import_module(mod_name)
            except Exception:
                continue
    except Exception:
        pass
    return None


def _resolve_model_class(models_module: Any, class_name: str):
    try:
        return getattr(models_module, class_name)
    except Exception:
        return None


def _candidate_model_names_for_param(
    param_name: str, operation_name: str
) -> List[str]:
    names: List[str] = []
    if not isinstance(param_name, str) or not param_name:
        return names

    suffixes = ("_details", "_config", "_configuration", "_source_details")
    for suffix in suffixes:
        if not param_name.endswith(suffix):
            continue
        names.append(_snake_to_camel(param_name))
        if suffix == "_details":
            # add verb-specific class names only for canonical payload keys,
            # e.g. vcn_details/create_vcn_details -> CreateVcnDetails.
            op_verb, _, op_rest = operation_name.partition("_")
            if op_verb in ("create", "update"):
                if param_name in (f"{op_rest}_details", f"{operation_name}_details"):
                    base = _snake_to_camel(op_rest)
                    names.append(f"{op_verb.capitalize()}{base}Details")
        break

    # de-duplicate while preserving order
    seen = set()
    out: List[str] = []
    for n in names:
        if n not in seen:
            out.append(n)
            seen.add(n)
    return out


def _operation_param_model_candidates(
    method: Optional[Callable[..., Any]], operation_name: str
) -> Dict[str, List[str]]:
    hints: Dict[str, List[str]] = {}
    if method is None:
        return hints
    try:
        sig = inspect.signature(method)
    except Exception:
        return hints

    for name, param in sig.parameters.items():
        if name in ("self", "kwargs"):
            continue
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        cands = _candidate_model_names_for_param(name, operation_name)
        if cands:
            hints[name] = cands
    return hints


def _coerce_mapping_values(
    mapping: Dict[str, Any], models_module: Any, parent_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Recursively coerce nested dict/list values inside a mapping into OCI SDK model instances.
    Additionally, when a parent model prefix is known (e.g., 'LaunchInstance' for
    LaunchInstanceDetails), attempt prefixed candidate class names for nested fields,
    such as 'LaunchInstance' + CamelCase(key) + 'Details'. This helps resolve cases like
    shape_config -> LaunchInstanceShapeConfigDetails.
    """
    suffixes = ("_details", "_config", "_configuration", "_source_details")
    out: Dict[str, Any] = {}
    for key, val in mapping.items():
        if isinstance(val, dict):
            if key == "source_details" or key.endswith("_source_details"):
                # Keep source details as a plain mapping so parent swagger_types +
                # discriminator normalization can resolve concrete models correctly.
                out[key] = _coerce_mapping_values(val, models_module, parent_prefix=None)
                continue
            candidates: List[str] = []
            for s in suffixes:
                if key.endswith(s):
                    base_camel = _snake_to_camel(key)
                    # also try parent-prefixed variants like 'LaunchInstanceShapeConfigDetails'
                    if parent_prefix:
                        candidates.append(f"{parent_prefix}{base_camel}Details")
                        candidates.append(f"{parent_prefix}{base_camel}")
                    candidates.append(base_camel)
                    break
            out[key] = _construct_model_from_mapping(val, models_module, candidates)
        elif isinstance(val, list):
            new_list: List[Any] = []
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
    # explicit override via magic keys
    fqn = mapping.get("__model_fqn") or mapping.get("__class_fqn")
    class_name = mapping.get("__model") or mapping.get("__class")
    clean = {k: v for k, v in mapping.items() if not k.startswith("__")}
    # derive a parent model prefix hint from candidate classnames
    # (e.g., 'LaunchInstance' from 'LaunchInstanceDetails')
    parent_prefix_hint: Optional[str] = None
    for cand in candidate_classnames:
        if isinstance(cand, str) and cand:
            if cand.endswith("Details"):
                parent_prefix_hint = cand[: -len("Details")]
                break
            # fallback to whole cand if no 'Details' suffix
            if parent_prefix_hint is None:
                parent_prefix_hint = cand
    # recursively coerce nested mappings/lists before attempting construction
    clean = _coerce_mapping_values(clean, models_module, parent_prefix=parent_prefix_hint)
    # try explicit FQN first
    if isinstance(fqn, str):
        try:
            mod_name, cls_name = fqn.rsplit(".", 1)
            mod = import_module(mod_name)
            cls = getattr(mod, cls_name)
            if inspect.isclass(cls):
                try:
                    normalized_clean = _to_model_attribute_keys(
                        clean, cls, models_module
                    )
                    return _from_dict_if_available(cls, normalized_clean)
                except Exception:
                    try:
                        return cls(**normalized_clean)
                    except Exception:
                        pass
        except Exception:
            pass
    # try explicit simple class name within models module
    if models_module and isinstance(class_name, str):
        cls = _resolve_model_class(models_module, class_name)
        if inspect.isclass(cls):
            try:
                normalized_clean = _to_model_attribute_keys(clean, cls, models_module)
                filtered_clean = normalized_clean
                swagger_types, _ = _get_model_schema(cls)
                if isinstance(swagger_types, dict):
                    filtered_clean = {
                        k: v for k, v in normalized_clean.items() if k in swagger_types
                    }
                return _from_dict_if_available(cls, filtered_clean)
            except Exception:
                try:
                    return cls(**filtered_clean)
                except Exception:
                    pass
    # try candidates derived from param name
    if models_module:
        for cand in candidate_classnames:
            cls = _resolve_model_class(models_module, cand)
            if inspect.isclass(cls):
                try:
                    normalized_clean = _to_model_attribute_keys(clean, cls, models_module)
                    filtered_clean = normalized_clean
                    swagger_types, _ = _get_model_schema(cls)
                    if isinstance(swagger_types, dict):
                        filtered_clean = {
                            k: v for k, v in normalized_clean.items() if k in swagger_types
                        }
                    return _from_dict_if_available(cls, filtered_clean)
                except Exception:
                    try:
                        return cls(**filtered_clean)
                    except Exception:
                        continue
    # fall back to original mapping
    return mapping


def _construct_model_with_class(mapping: Dict[str, Any], cls: type, models_module: Any):
    clean = {k: v for k, v in mapping.items() if not k.startswith("__")}
    parent_prefix_hint: Optional[str] = None
    cls_name = getattr(cls, "__name__", "")
    if isinstance(cls_name, str) and cls_name:
        if cls_name.endswith("Details"):
            parent_prefix_hint = cls_name[: -len("Details")]
        else:
            parent_prefix_hint = cls_name

    clean = _coerce_mapping_values(
        clean, models_module, parent_prefix=parent_prefix_hint
    )

    normalized_clean = _to_model_attribute_keys(clean, cls, models_module)
    filtered_clean = normalized_clean
    try:
        swagger_types, _ = _get_model_schema(cls)
        if isinstance(swagger_types, dict):
            filtered_clean = {
                k: v for k, v in normalized_clean.items() if k in swagger_types
            }
    except Exception:
        filtered_clean = normalized_clean
    try:
        return _from_dict_if_available(cls, filtered_clean)
    except Exception:
        return cls(**filtered_clean)


def _coerce_params_to_oci_models(
    client_fqn: str,
    operation: str,
    params: Dict[str, Any],
    method: Optional[Callable[..., Any]] = None,
) -> Dict[str, Any]:
    """
    Convert plain dict/list params to OCI model instances when appropriate.
    Heuristics:
      - If a dict contains '__model_fqn' or '__model'/'__class', build that model.
      - If a param name ends with typical model suffixes (e.g., *_details), attempt to
        construct the corresponding CamelCase model class from the client's models module.
    """
    if not params:
        return {}
    models_module = _import_models_module_from_client_fqn(client_fqn)
    op_hints = _operation_param_model_candidates(method, operation)
    suffixes = ("_details", "_config", "_configuration", "_source_details")
    out: Dict[str, Any] = {}
    for key, val in params.items():
        if isinstance(val, dict):
            candidates: List[str] = list(op_hints.get(key, []))
            dest_key = key
            for s in suffixes:
                if key.endswith(s):
                    candidates.extend(_candidate_model_names_for_param(key, operation))
                    if s == "_details":
                        # rename "<resource>_details" to the SDK's expected
                        # "create_<resource>_details"/"update_<resource>_details"
                        if operation.startswith("create_") or operation.startswith("update_"):
                            _, _, op_rest = operation.partition("_")
                            if key == f"{op_rest}_details":
                                # only rename to SDK-expected key when destination not already
                                # provided by caller
                                alt_key = f"{operation}_details"
                                if alt_key not in params:
                                    dest_key = alt_key
                    break
            if dest_key != key:
                candidates.extend(op_hints.get(dest_key, []))
                candidates.extend(_candidate_model_names_for_param(dest_key, operation))
            # de-duplicate while preserving order
            seen = set()
            deduped: List[str] = []
            for c in candidates:
                if c not in seen:
                    deduped.append(c)
                    seen.add(c)
            constructed = None
            if models_module:
                for cand in deduped:
                    cls = _resolve_model_class(models_module, cand)
                    if inspect.isclass(cls):
                        swagger_types, _ = _get_model_schema(cls)
                        if not isinstance(swagger_types, dict):
                            # keep legacy heuristic path for classes without model schema
                            continue
                        try:
                            constructed = _construct_model_with_class(
                                val, cls, models_module
                            )
                            break
                        except Exception:
                            continue
            if constructed is None:
                constructed = _construct_model_from_mapping(
                    val, models_module, deduped
                )
            out[dest_key] = constructed
        elif isinstance(val, list):
            new_list: List[Any] = []
            for item in val:
                if isinstance(item, dict):
                    # only construct list items if explicit model hint is present
                    if any(hint in item for hint in ("__model_fqn", "__model", "__class_fqn", "__class")):
                        new_list.append(_construct_model_from_mapping(item, models_module, []))
                    else:
                        new_list.append(item)
                else:
                    new_list.append(item)
            out[key] = new_list
        else:
            out[key] = val
    # final aliasing: if caller used "<resource>_details" and op is create_/update_,
    # rename to the SDK-expected "create_<resource>_details"/"update_<resource>_details".
    if operation.startswith("create_") or operation.startswith("update_"):
        _, _, op_rest = operation.partition("_")
        src = f"{op_rest}_details"
        dst = f"{operation}_details"
        if src in out and dst not in out:
            out[dst] = out.pop(src)
    return out


def _align_params_to_signature(
    method: Callable[..., Any], operation_name: str, params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Align incoming params to the method's expected signature names.
    Specifically, for create_/update_ operations remap '<resource>_details' to
    'create_<resource>_details'/'update_<resource>_details' when the latter exists
    in the target method signature.
    """
    try:
        sig = inspect.signature(method)
    except Exception:
        return params
    aligned = dict(params)
    sig_params = dict(sig.parameters)
    param_names = set(sig_params.keys())
    if operation_name.startswith("create_") or operation_name.startswith("update_"):
        _, _, op_rest = operation_name.partition("_")
        src = f"{op_rest}_details"
        dst = f"{operation_name}_details"
        if src in aligned and dst not in aligned and dst in param_names:
            aligned[dst] = aligned.pop(src)

    # General fallback for SDK operations that use abbreviated id parameters
    # (e.g., ig_id, rt_id). If exactly one caller *_id key does not match and
    # exactly one signature *_id parameter is missing, remap it.
    explicit_param_names = {
        name
        for name, p in sig_params.items()
        if name != "self"
        and p.kind
        not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    }
    unknown_id_keys = [
        k for k in aligned.keys() if k.endswith("_id") and k not in explicit_param_names
    ]
    missing_id_params = [
        p
        for p in explicit_param_names
        if p.endswith("_id") and p not in aligned
    ]
    if len(unknown_id_keys) == 1 and len(missing_id_params) == 1:
        src_id = unknown_id_keys[0]
        dst_id = missing_id_params[0]
        aligned[dst_id] = aligned.pop(src_id)

    return aligned


def _serialize_oci_data(data: Any) -> Any:
    """
    Convert OCI SDK model objects or collections into JSON-serializable structures.
    Ensures the final result is JSON-serializable even if oci.util.to_dict returns the original object.
    """

    def ensure_jsonable(obj: Any) -> Any:
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, (list, tuple)):
            return [ensure_jsonable(x) for x in obj]
        if isinstance(obj, dict):
            return {k: ensure_jsonable(v) for k, v in obj.items()}
        # OCI models in newer SDK versions expose swagger_types on instances.
        swagger_types = getattr(obj, "swagger_types", None)
        if isinstance(swagger_types, dict):
            out: Dict[str, Any] = {}
            for key in swagger_types.keys():
                try:
                    out[key] = ensure_jsonable(getattr(obj, key))
                except Exception:
                    continue
            return out
        try:
            json.dumps(obj)
            return obj
        except Exception:
            return str(obj)

    try:
        converted = oci.util.to_dict(data)
    except Exception:
        converted = ensure_jsonable(data)
    return ensure_jsonable(converted)


def _extract_expected_kwargs_from_source(method: Callable[..., Any]) -> Optional[set]:
    """
    Best-effort extraction of the SDK generator's 'expected_kwargs' list from the method source.
    Returns a set of kwarg names if found, None if source cannot be retrieved, or empty set if
    the pattern isn't present.
    """
    try:
        src = inspect.getsource(method)
    except Exception:
        return None
    try:
        m = re.search(r"expected_kwargs\s*=\s*\[\s*(.*?)\s*\]", src, re.DOTALL)
        if not m:
            return set()
        body = m.group(1)
        kws = set(re.findall(r"['\"]([a-zA-Z0-9_]+)['\"]", body))
        return kws
    except Exception:
        return None


def _docstring_mentions_pagination(method: Callable[..., Any]) -> bool:
    """
    Inspect a method's docstring to detect pagination-related parameters
    that may be documented even if only accepted via **kwargs, such as
    ':param int limit:' or ':param str page:'.
    """
    try:
        doc = inspect.getdoc(method) or ""
    except Exception:
        return False
    # look for common Sphinx/ReST patterns or plain mentions of parameter names
    return bool(re.search(r"\b(page|limit)\b", doc))


def _supports_pagination(method: Callable[..., Any], operation_name: str) -> bool:
    """
    Determine if an operation is paginated and should use the OCI paginator.
    Heuristics:
      - Operation name starts with 'list_' (standard OCI pattern).
      - Operation name starts with 'summarize_' (many summarize ops are paginated).
      - Method signature includes 'page' or 'limit' kwargs (explicit params).
      - Method accepts **kwargs and operation name indicates record/rrset style (DNS-like).
    """
    non_paginated_prefixes = (
        "create_",
        "update_",
        "delete_",
        "launch_",
        "terminate_",
        "attach_",
        "detach_",
        "change_",
        "start_",
        "stop_",
        "reboot_",
        "reset_",
    )
    if operation_name.startswith(non_paginated_prefixes):
        return False

    try:
        if operation_name.startswith("list_"):
            return True
        if operation_name.startswith("summarize_"):
            return True

        # detect SDK-generated kwargs list that includes pagination tokens even when only exposed via **kwargs
        ek = _extract_expected_kwargs_from_source(method)
        if ek and (("page" in ek) or ("limit" in ek)):
            return True

        # docstring-only detection is intentionally restricted to list/summarize
        # style methods to avoid false positives on create/get operations.
        if operation_name.startswith("list_") or operation_name.startswith("summarize_"):
            try:
                if _docstring_mentions_pagination(method):
                    return True
            except Exception:
                pass

        sig = inspect.signature(method)
        param_names = set(sig.parameters.keys())
        if "page" in param_names or "limit" in param_names:
            return True
    except Exception:
        # if we cannot introspect, fall through to explicit allowlist
        pass

    return operation_name in known_paginated


def _call_with_pagination_if_applicable(
    method: Callable[..., Any], params: Dict[str, Any], operation_name: str
) -> Tuple[Any, Optional[str]]:
    """
    If the operation appears to be paginated, use the OCI paginator to get all results.
    Returns (data, opc_request_id).
    """
    if _supports_pagination(method, operation_name):
        logger.info(f"Using paginator for operation {operation_name}")
        try:
            response = oci.pagination.list_call_get_all_results(method, **params)
            opc_request_id = None
            try:
                opc_request_id = response.headers.get("opc-request-id")
            except Exception:
                opc_request_id = None
            return response.data, opc_request_id
        except Exception as e:
            logger.warning(
                f"Paginator path failed for {operation_name}; falling back to direct call: {e}"
            )

    # non-list operation; pre-alias known kwarg patterns and invoke, with fallback aliasing
    call_params = dict(params)
    if operation_name.startswith("create_") or operation_name.startswith("update_"):
        _, _, op_rest = operation_name.partition("_")
        src = f"{op_rest}_details"
        dst = f"{operation_name}_details"
        if src in call_params and dst not in call_params:
            call_params[dst] = call_params.pop(src)

    try:
        logger.debug(f"_call_with_pagination_if_applicable call_params keys: {list(call_params.keys())}")
        logger.debug(f"op: {operation_name}")
        response = method(**call_params)
    except TypeError as e:
        # fallback: if user passed "<resource>_details" for a create_/update_ op,
        # retry with "create_<resource>_details"/"update_<resource>_details"
        msg = str(e)
        if "unexpected keyword argument" in msg and (
            operation_name.startswith("create_") or operation_name.startswith("update_")
        ):
            try:
                bad_kw = msg.split("'")[1]
                _, _, op_rest = operation_name.partition("_")
                expected_src = f"{op_rest}_details"
                if bad_kw == expected_src and expected_src in call_params:
                    alt_key = f"{operation_name}_details"
                    new_params = dict(call_params)
                    new_params[alt_key] = new_params.pop(expected_src)
                    response = method(**new_params)
                else:
                    raise
            except Exception:
                raise
        else:
            raise

    # most OCI SDK methods return oci.response.Response with .data and .headers
    if hasattr(response, "data"):
        data = response.data
    else:
        data = response
    opc_request_id = None
    try:
        opc_request_id = response.headers.get("opc-request-id")
    except Exception:
        opc_request_id = None
    return data, opc_request_id


@mcp.tool(description="Invoke an OCI Python SDK API via client and operation name.")
def invoke_oci_api(
    client_fqn: Annotated[str, "Fully-qualified client class, e.g. 'oci.core.ComputeClient'"],
    operation: Annotated[str, "Client method/operation name, e.g. 'list_instances' or 'get_instance'"],
    params: Annotated[
        Dict[str, Any],
        "Keyword arguments for the operation (JSON object). Use snake_case keys as in SDK.",
    ] = {},
) -> dict:
    """
    Example:
      client_fqn='oci.core.ComputeClient'
      operation='list_instances'
      params={'compartment_id': '<ocid>', 'availability_domain': '...'}
    """
    try:
        client = _import_client(client_fqn)
        if not hasattr(client, operation):
            raise AttributeError(f"Operation '{operation}' not found on client '{client_fqn}'")

        method = getattr(client, operation)
        if not callable(method):
            raise AttributeError(f"Attribute '{operation}' on client '{client_fqn}' is not callable")

        params = params or {}
        # pre-normalize parameter key to the SDK-expected kw for create_/update_ ops,
        # so downstream coercion and invocation consistently use the correct key.
        normalized_params = dict(params)
        if operation.startswith("create_") or operation.startswith("update_"):
            _, _, op_rest = operation.partition("_")
            src = f"{op_rest}_details"
            dst = f"{operation}_details"
            if src in normalized_params and dst not in normalized_params:
                normalized_params[dst] = normalized_params.pop(src)

        coerced_params = _coerce_params_to_oci_models(
            client_fqn, operation, normalized_params, method=method
        )
        # final kwarg aliasing at the top-level prior to invocation to ensure correct SDK kw
        final_params = dict(coerced_params)

        final_params = _align_params_to_signature(method, operation, final_params)
        logger.debug(f"invoke_oci_api final_params keys: {list(final_params.keys())}")
        logger.debug(f"op: {operation}")
        try:
            data, opc_request_id = _call_with_pagination_if_applicable(method, final_params, operation)
        except TypeError as e:
            msg = str(e)
            if "unexpected keyword argument" in msg and (
                operation.startswith("create_") or operation.startswith("update_")
            ):
                # last-chance aliasing retry at top level
                _, _, op_rest = operation.partition("_")
                src = f"{op_rest}_details"
                dst = f"{operation}_details"
                if src in final_params and dst not in final_params:
                    alt_params = dict(final_params)
                    alt_params[dst] = alt_params.pop(src)
                    data, opc_request_id = _call_with_pagination_if_applicable(method, alt_params, operation)
                else:
                    raise
            else:
                raise

        result = {
            "client": client_fqn,
            "operation": operation,
            "params": params,
            "opc_request_id": opc_request_id,
            "data": _serialize_oci_data(data),
        }
        logger.info(
            f"invoke_oci_api success: client={client_fqn} op={operation} opc_request_id={opc_request_id}"
        )
        return result

    except Exception as e:
        logger.error(f"Error invoking OCI API {client_fqn}.{operation}: {e}")
        return {
            "client": client_fqn,
            "operation": operation,
            "params": params or {},
            "error": str(e),
        }


@mcp.tool(description="List public callable operations for a given OCI client class.")
def list_client_operations(
    client_fqn: Annotated[
        str, "Fully-qualified client class, e.g. 'oci.core.ComputeClient'"
    ],
    name_regex: Annotated[
        Optional[str],
        "Optional regex to filter operations by name (Python re syntax). Uses re.search.",
    ] = None,
) -> dict:
    try:
        module_name, class_name = client_fqn.rsplit(".", 1)
        module = import_module(module_name)
        cls = getattr(module, class_name)
        if not inspect.isclass(cls):
            raise ValueError(f"{client_fqn} is not a class")

        compiled: Optional[re.Pattern] = None
        if name_regex:
            try:
                compiled = re.compile(name_regex)
            except re.error as e:
                raise ValueError(f"Invalid name_regex: {e}")

        ops: List[dict] = []
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name.startswith("_"):
                continue
            if compiled and not compiled.search(name):
                continue
            try:
                doc = (inspect.getdoc(member) or "").strip()
                first_line = doc.splitlines()[0] if doc else ""
                params = inspect.signature(member)
            except Exception:
                first_line = ""
                params = ""
            ops.append({"name": name, "summary": first_line, "params": str(params)})

        logger.info(
            f"Found {len(ops)} operations on {client_fqn} (name_regex={name_regex!r})"
        )
        # return a mapping to avoid Pydantic RootModel list-wrapping
        return {"operations": ops, "name_regex": name_regex}
    except Exception as e:
        logger.error(f"Error listing operations for {client_fqn}: {e}")
        raise


@mcp.tool(
    description="Get details for one OCI client operation, including expected_kwargs when available."
)
def get_client_operation_details(
    client_fqn: Annotated[
        str, "Fully-qualified client class, e.g. 'oci.core.ComputeClient'"
    ],
    operation: Annotated[str, "Client method/operation name, e.g. 'list_instances'"],
) -> dict:
    try:
        module_name, class_name = client_fqn.rsplit(".", 1)
        module = import_module(module_name)
        cls = getattr(module, class_name)
        if not inspect.isclass(cls):
            raise ValueError(f"{client_fqn} is not a class")

        if not hasattr(cls, operation):
            raise AttributeError(
                f"Operation '{operation}' not found on client '{client_fqn}'"
            )

        member = getattr(cls, operation)
        if not callable(member):
            raise AttributeError(
                f"Attribute '{operation}' on client '{client_fqn}' is not callable"
            )

        try:
            doc = (inspect.getdoc(member) or "").strip()
            first_line = doc.splitlines()[0] if doc else ""
        except Exception:
            first_line = ""

        try:
            params = str(inspect.signature(member))
        except Exception:
            params = ""

        expected_kwargs = _extract_expected_kwargs_from_source(member)
        if expected_kwargs is None:
            expected_kwargs_list = []
        else:
            expected_kwargs_list = sorted(expected_kwargs)

        return {
            "client_fqn": client_fqn,
            "operation": operation,
            "summary": first_line,
            "params": params,
            "expected_kwargs": expected_kwargs_list,
        }
    except Exception as e:
        logger.error(
            f"Error getting operation details for {client_fqn}.{operation}: {e}"
        )
        raise


def _discover_oci_clients() -> List[dict]:
    """Discover available OCI Python SDK client classes.

    Returns a list of entries of the shape:
      {
        "client_fqn": "oci.core.ComputeClient",
        "module": "oci.core",
        "class": "ComputeClient"
      }

    Detection:
    - Walk submodules under `oci`.
    - Import only modules whose name ends with `_client` (OCI SDK convention)
      to avoid importing every single models module.
    - Collect any public class ending with `Client`.

      Note: OCI Python SDK v2.160.0+ no longer has service clients inherit
      from `oci.base_client.BaseClient`. Instead, service clients *compose*
      a `BaseClient` (e.g., `self.base_client = BaseClient(...)`).
      Therefore, inheritance checks will incorrectly filter out all clients.
      We detect clients by either:
        - inheriting from BaseClient (legacy SDK versions), OR
        - exposing an `__init__(config, **kwargs)` and a `base_client` attribute
          (current SDK versions).
    """
    clients: List[dict] = []

    try:
        BaseClient = getattr(oci.base_client, "BaseClient", None)

        def iter_oci_submodules():
            # walk packages recursively under `oci` but only import *_client modules
            for modinfo in pkgutil.walk_packages(oci.__path__, prefix="oci."):
                name = getattr(modinfo, "name", None) or modinfo[1]
                if not isinstance(name, str):
                    continue
                if not name.endswith("_client"):
                    continue
                yield name

        seen: set[str] = set()
        for module_name in iter_oci_submodules():
            try:
                module = import_module(module_name)
            except Exception:
                continue

            for cls_name, member in inspect.getmembers(module, predicate=inspect.isclass):
                if cls_name.startswith("_"):
                    continue
                if cls_name == "BaseClient":
                    continue
                if not cls_name.endswith("Client"):
                    continue
                # OCI SDK client classes historically inherited from BaseClient.
                # Newer SDK versions (e.g., 2.160.0) use composition instead, so
                # an issubclass check will fail for every client.
                if BaseClient and inspect.isclass(member):
                    if issubclass(member, BaseClient):
                        pass
                    else:
                        # Heuristic: client exposes 'base_client' after init.
                        # We can't instantiate here (would require config), so
                        # use a cheap source/attribute inspection fallback.
                        try:
                            # Some generated clients include 'self.base_client =' in __init__
                            src = inspect.getsource(member.__init__)
                            if "self.base_client" not in src:
                                continue
                        except Exception:
                            # If we can't inspect source, be permissive and keep it.
                            # Worst case: user sees extra non-usable 'Client' classes.
                            pass

                client_fqn = f"{module_name}.{cls_name}"
                if client_fqn in seen:
                    continue
                seen.add(client_fqn)
                clients.append(
                    {
                        "client_fqn": client_fqn,
                        "module": module_name,
                        "class": cls_name,
                    }
                )
    except Exception as e:
        logger.error(f"Error discovering OCI SDK clients: {e}")
        raise

    # Stable output for tests and user experience
    clients.sort(key=lambda c: c["client_fqn"])
    return clients


@mcp.tool(description="List all available clients in the installed OCI Python SDK.")
def list_oci_clients() -> dict:
    """Return a list of discoverable OCI SDK client classes."""
    clients = _discover_oci_clients()
    return {"count": len(clients), "clients": clients}


def main():
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
