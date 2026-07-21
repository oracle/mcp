"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
import importlib
import re
from typing import Any

import oci
from pydantic import BaseModel

FORBIDDEN_REQUEST_FIELDS = frozenset(
    {
        "defined_tags",
        "freeform_tags",
        "system_tags",
        "tag_filters",
        "match_rule",
    }
)

_LIST_TYPE_RE = re.compile(r"list\[(.+)\]")


def to_plain_data(value: Any) -> Any:
    """Convert SDK/Pydantic values into JSON-serializable Python data."""

    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, BaseModel):
        return value.model_dump(by_alias=True, exclude_none=True)
    if isinstance(value, Mapping):
        return {key: to_plain_data(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [to_plain_data(item) for item in value]
    try:
        return oci.util.to_dict(value)
    except Exception:
        pass
    if hasattr(value, "__dict__"):
        return {
            key.removeprefix("_"): to_plain_data(item)
            for key, item in value.__dict__.items()
            if not key.startswith("__") and item is not None
        }
    return value


def pydantic_to_sdk_model(value: Any, sdk_model_type: type[Any]) -> Any:
    """Convert a Pydantic request model or plain mapping into an OCI SDK model."""

    if value is None:
        return None
    if isinstance(value, sdk_model_type):
        return value
    if isinstance(value, BaseModel):
        payload = value.model_dump(by_alias=False, exclude_none=True)
    elif isinstance(value, Mapping):
        payload = {key: to_plain_data(item) for key, item in value.items() if item is not None}
    else:
        return value
    return sdk_model_type(**payload)


def _sdk_model_metadata(sdk_model_type: type[Any]) -> tuple[dict[str, str], dict[str, str]]:
    try:
        instance = sdk_model_type()
    except Exception as exc:
        raise ValueError(f"Unable to inspect OCI SDK model {sdk_model_type.__name__}.") from exc
    return dict(getattr(instance, "swagger_types", {}) or {}), dict(getattr(instance, "attribute_map", {}) or {})


def _payload_from_request_value(value: Any) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(by_alias=False, exclude_none=True)
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items() if item is not None}
    raise ValueError(f"Request payload must be a mapping or Pydantic model, got {type(value).__name__}.")


def _wire_payload(payload: Mapping[str, Any], attribute_map: Mapping[str, str]) -> dict[str, Any]:
    return {
        attribute_map.get(key, key): item
        for key, item in payload.items()
    }


def _normalize_key(key: str, attribute_map: Mapping[str, str]) -> str:
    if key in attribute_map:
        return key
    inverse_attribute_map = {wire_key: model_key for model_key, wire_key in attribute_map.items()}
    return inverse_attribute_map.get(key, key)


def _sdk_models_module(sdk_model_type: type[Any]) -> Any:
    module_name = sdk_model_type.__module__
    package_name = module_name.rsplit(".", 1)[0]
    return importlib.import_module(package_name)


def _select_sdk_model_type(
    payload: Mapping[str, Any],
    sdk_model_type: type[Any],
    attribute_map: Mapping[str, str],
    path: str,
) -> type[Any]:
    get_subtype = getattr(sdk_model_type, "get_subtype", None)
    if get_subtype is None:
        return sdk_model_type

    try:
        subtype_name = get_subtype(_wire_payload(payload, attribute_map))
    except KeyError as exc:
        raise ValueError(f"{path} is missing discriminator field {exc.args[0]!r}.") from exc
    except Exception as exc:
        raise ValueError(f"Unable to resolve OCI SDK subtype for {path}: {exc}") from exc

    module = _sdk_models_module(sdk_model_type)
    subtype = getattr(module, subtype_name, None)
    if not isinstance(subtype, type):
        raise ValueError(f"{path} resolved unknown OCI SDK subtype {subtype_name!r}.")
    return subtype


def _resolve_sdk_model_type(type_spec: str, sdk_models_module: Any) -> type[Any] | None:
    type_name = type_spec.strip()
    list_match = _LIST_TYPE_RE.fullmatch(type_name)
    if list_match is not None:
        type_name = list_match.group(1).strip()
    if "[" in type_name or "(" in type_name:
        return None
    sdk_type = getattr(sdk_models_module, type_name, None)
    return sdk_type if isinstance(sdk_type, type) else None


def _is_sdk_model_type(sdk_type: type[Any] | None) -> bool:
    if sdk_type is None:
        return False
    try:
        swagger_types, _ = _sdk_model_metadata(sdk_type)
    except ValueError:
        return False
    return bool(swagger_types)


def _convert_sdk_field_value(value: Any, type_spec: str, sdk_models_module: Any, path: str) -> Any:
    if value is None:
        return None

    list_match = _LIST_TYPE_RE.fullmatch(type_spec.strip())
    if list_match is not None and isinstance(value, list | tuple):
        inner_type_spec = list_match.group(1).strip()
        return [
            _convert_sdk_field_value(item, inner_type_spec, sdk_models_module, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]

    sdk_field_type = _resolve_sdk_model_type(type_spec, sdk_models_module)
    if _is_sdk_model_type(sdk_field_type):
        if isinstance(value, sdk_field_type):
            return value
        if isinstance(value, BaseModel | Mapping):
            return _build_sdk_model(
                _payload_from_request_value(value),
                sdk_field_type,
                path,
            )

    return to_plain_data(value)


def _build_sdk_model(payload: Mapping[str, Any], sdk_model_type: type[Any], path: str) -> Any:
    _, base_attribute_map = _sdk_model_metadata(sdk_model_type)
    selected_sdk_model_type = _select_sdk_model_type(payload, sdk_model_type, base_attribute_map, path)
    swagger_types, attribute_map = _sdk_model_metadata(selected_sdk_model_type)
    sdk_models_module = _sdk_models_module(selected_sdk_model_type)

    normalized_payload: dict[str, Any] = {}
    unknown_fields: list[str] = []
    forbidden_fields: list[str] = []

    for raw_key, item in payload.items():
        key = _normalize_key(raw_key, attribute_map)
        if key in FORBIDDEN_REQUEST_FIELDS:
            forbidden_fields.append(raw_key)
            continue
        if key not in swagger_types:
            unknown_fields.append(raw_key)
            continue
        normalized_payload[key] = _convert_sdk_field_value(
            item,
            swagger_types[key],
            sdk_models_module,
            f"{path}.{key}",
        )

    if forbidden_fields:
        fields = ", ".join(sorted(forbidden_fields))
        raise ValueError(f"{path} contains forbidden request tag mutation fields: {fields}.")
    if unknown_fields:
        fields = ", ".join(sorted(unknown_fields))
        raise ValueError(f"{path} contains unsupported fields for {selected_sdk_model_type.__name__}: {fields}.")

    return selected_sdk_model_type(**normalized_payload)


def polymorphic_request_to_sdk_model(value: Any, sdk_model_type: type[Any]) -> Any:
    """Convert a request payload into the correct OCI SDK model or subtype."""

    if value is None:
        return None
    if isinstance(value, sdk_model_type):
        return value
    payload = _payload_from_request_value(value)
    return _build_sdk_model(payload, sdk_model_type, sdk_model_type.__name__)
