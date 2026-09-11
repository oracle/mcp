"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Derive strict JSON Schema contracts from the locked OCI Python SDK.
"""
from __future__ import annotations

import inspect
import re
from collections.abc import Mapping
from importlib import import_module
from typing import Any


TRANSPORT_KWARGS = frozenset({"retry_strategy", "allow_control_chars", "enable_strict_url_encoding"})
_SCALAR_SCHEMAS = {
    "str": {"type": "string"},
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "bool": {"type": "boolean"},
    "datetime": {"type": "string", "format": "date-time"},
}
_CONSTRAINT_KEYS = frozenset({"enum", "minimum", "maximum", "minLength", "maxLength", "pattern"})


def expected_kwargs(method: Any) -> set[str]:
    """Return all generated OCI SDK call arguments, excluding transport controls."""
    source = inspect.getsource(method)
    match = re.search(r"expected_kwargs\s*=\s*\[\s*(.*?)\s*\]", source, re.DOTALL)
    if not match:
        raise ValueError(f"Unable to find expected_kwargs in {method.__qualname__}")
    optional = set(re.findall(r"['\"]([a-zA-Z0-9_]+)['\"]", match.group(1)))
    required = {
        parameter.name
        for parameter in inspect.signature(method).parameters.values()
        if parameter.name not in {"self", "kwargs"}
        and parameter.kind in {parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD, parameter.KEYWORD_ONLY}
    }
    return (required | optional) - TRANSPORT_KWARGS


def parameter_docs(method: Any) -> dict[str, tuple[str, bool, str]]:
    """Return SDK parameter type, requiredness, and documentation by argument name."""
    text = inspect.getdoc(method) or ""
    matches = list(re.finditer(r"^:param\s+([^\s]+)\s+([a-zA-Z0-9_]+):\s*(.*)$", text, re.MULTILINE))
    result: dict[str, tuple[str, bool, str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        detail = f"{match.group(3)}\n{text[match.end():end]}".strip()
        result[match.group(2)] = (match.group(1), "(required)" in match.group(3), detail)
    return result


def _split_generic(value: str) -> tuple[str, str] | None:
    match = re.fullmatch(r"(list|dict)\[(.*)\]", value)
    if match:
        return match.group(1), match.group(2)
    match = re.fullmatch(r"dict\((.*)\)", value)
    return ("dict", match.group(1)) if match else None


def _split_pair(value: str) -> tuple[str, str]:
    depth = 0
    for index, character in enumerate(value):
        if character in "[(":
            depth += 1
        elif character in "])":
            depth -= 1
        elif character == "," and depth == 0:
            return value[:index].strip(), value[index + 1 :].strip()
    raise ValueError(f"Expected two generic arguments in {value!r}")


def _enum_from_description(description: str) -> list[str] | None:
    match = re.search(r"Allowed values are:\s*(.*?)(?:\n\n|:param|:return:|$)", description, re.DOTALL)
    if not match:
        return None
    values = re.findall(r'"([^"\n]+)"', match.group(1))
    return values or None


def _model_maps(model_class: type[Any]) -> tuple[dict[str, str], dict[str, str]]:
    instance = model_class()
    swagger_types = getattr(instance, "swagger_types", None)
    attribute_map = getattr(instance, "attribute_map", None)
    if not isinstance(swagger_types, dict) or not isinstance(attribute_map, dict):
        raise ValueError(f"OCI model {model_class.__name__} does not expose schema maps")
    return swagger_types, attribute_map


def _model_required_and_description(model_class: type[Any], field: str) -> tuple[bool, str]:
    property_value = getattr(model_class, field, None)
    getter = getattr(property_value, "fget", None)
    description = inspect.getdoc(getter) or ""
    return "**[Required]**" in description, description


def _resolve_model(type_name: str, models_module: Any) -> type[Any] | None:
    normalized = type_name.removeprefix("oci.")
    if ".models." in type_name:
        module_name, class_name = type_name.rsplit(".", 1)
        return getattr(import_module(module_name), class_name, None)
    return getattr(models_module, normalized.rsplit(".", 1)[-1], None)


def _model_schema(model_class: type[Any], models_module: Any, seen: frozenset[str]) -> dict[str, Any]:
    model_name = f"{model_class.__module__}.{model_class.__name__}"
    if model_name in seen:
        raise ValueError(f"Recursive OCI model type {model_name}")
    swagger_types, _ = _model_maps(model_class)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for field, field_type in swagger_types.items():
        field_required, field_description = _model_required_and_description(model_class, field)
        properties[field] = schema_for_type(field_type, models_module, field_description, seen | {model_name})
        if field_required:
            required.append(field)
    schema = {"type": "object", "properties": properties, "additionalProperties": False}
    if required:
        schema["required"] = required
    return schema


def _polymorphic_schema(model_class: type[Any], models_module: Any, seen: frozenset[str]) -> dict[str, Any]:
    source = inspect.getsource(model_class.get_subtype)
    variants = re.findall(r"if type == ['\"]([^'\"]+)['\"]:\s*return ['\"]([^'\"]+)['\"]", source)
    if not variants:
        raise ValueError(f"Unable to resolve polymorphic OCI model type {model_class.__name__}")
    discriminator = re.search(r"object_dictionary\[['\"]([^'\"]+)['\"]\]", source)
    if not discriminator:
        raise ValueError(f"Unable to resolve discriminator for OCI model type {model_class.__name__}")
    _, attribute_map = _model_maps(model_class)
    fields = [field for field, wire_name in attribute_map.items() if wire_name == discriminator.group(1)]
    if len(fields) != 1:
        raise ValueError(f"Unable to resolve discriminator field for OCI model type {model_class.__name__}")
    discriminator_field = fields[0]
    schemas = []
    for discriminator, subtype_name in variants:
        subtype = getattr(models_module, subtype_name, None)
        if not inspect.isclass(subtype):
            raise ValueError(f"Unable to resolve OCI subtype {subtype_name}")
        schema = _model_schema(subtype, models_module, seen)
        discriminator_schema = schema["properties"].get(discriminator_field)
        if not isinstance(discriminator_schema, dict):
            raise ValueError(f"OCI subtype {subtype_name} lacks the {discriminator_field} discriminator")
        discriminator_schema["enum"] = [discriminator]
        if discriminator_field not in schema.get("required", []):
            schema["required"] = [*schema.get("required", []), discriminator_field]
        schemas.append(schema)
    return {"oneOf": schemas}


def schema_for_type(type_name: str, models_module: Any, description: str = "", seen: frozenset[str] = frozenset()) -> dict[str, Any]:
    """Build a strict JSON Schema fragment for one OCI SDK type spelling."""
    normalized = type_name.removeprefix("oci.opsi.models.").removeprefix("oci.database_management.models.")
    if normalized in _SCALAR_SCHEMAS:
        schema = dict(_SCALAR_SCHEMAS[normalized])
        enum = _enum_from_description(description)
        if enum:
            schema["enum"] = enum
        return schema
    generic = _split_generic(normalized)
    if generic:
        kind, contents = generic
        if kind == "list":
            return {"type": "array", "items": schema_for_type(contents.strip(), models_module, description, seen)}
        _, value_type = _split_pair(contents)
        return {
            "type": "object",
            "additionalProperties": schema_for_type(value_type, models_module, "", seen),
        }
    if normalized in {"object", "Any"}:
        return {}
    model_class = _resolve_model(type_name, models_module)
    if not inspect.isclass(model_class):
        raise ValueError(f"Unable to resolve OCI SDK type {type_name!r}")
    if callable(getattr(model_class, "get_subtype", None)):
        return _polymorphic_schema(model_class, models_module, seen)
    return _model_schema(model_class, models_module, seen)


def schema_for_operation(method: Any, models_module: Any, existing: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build the strict input schema for an SDK operation and preserve known constraints."""
    docs = parameter_docs(method)
    expected = expected_kwargs(method)
    if set(docs) - TRANSPORT_KWARGS != expected:
        raise ValueError(f"SDK documentation and expected_kwargs differ for {method.__qualname__}")
    existing_properties = existing.get("properties", {}) if isinstance(existing, Mapping) else {}
    properties: dict[str, Any] = {}
    required: list[str] = []
    for name in sorted(expected):
        type_name, is_required, description = docs[name]
        schema = schema_for_type(type_name, models_module, description)
        _preserve_constraints(schema, existing_properties.get(name))
        if isinstance(existing_properties.get(name), Mapping) and "description" in existing_properties[name]:
            schema["description"] = existing_properties[name]["description"]
        properties[name] = schema
        if is_required:
            required.append(name)
    result: dict[str, Any] = {"type": "object", "properties": properties, "additionalProperties": False}
    if required:
        existing_required = existing.get("required", []) if isinstance(existing, Mapping) else []
        result["required"] = [name for name in existing_required if name in required] + [name for name in required if name not in existing_required]
    if isinstance(existing, Mapping) and "oneOf" in existing:
        result["oneOf"] = existing["oneOf"]
    return result


def _preserve_constraints(schema: dict[str, Any], existing: Any) -> None:
    if not isinstance(existing, Mapping):
        return
    for key in _CONSTRAINT_KEYS:
        if key in existing:
            schema[key] = existing[key]
    if schema.get("type") == "array":
        _preserve_constraints(schema["items"], existing.get("items"))
    if schema.get("type") == "object" and schema.get("additionalProperties") is False:
        existing_properties = existing.get("properties", {})
        for name, nested in schema.get("properties", {}).items():
            _preserve_constraints(nested, existing_properties.get(name))
