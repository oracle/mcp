"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import base64
from typing import Any


def required_string(arguments: dict[str, Any], name: str) -> str:
    """Reads a required string argument."""
    value = arguments.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def optional_string(arguments: dict[str, Any], name: str) -> str | None:
    """Reads an optional string argument."""
    value = arguments.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    return value


def required_base64_string(arguments: dict[str, Any], name: str) -> str:
    """Reads and validates a required base64 string without changing its value."""
    value = required_string(arguments, name)
    try:
        base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValueError(f"{name} must be valid base64-encoded content") from exc
    return value


def required_string_list(arguments: dict[str, Any], name: str) -> list[str]:
    """Reads a required non-empty list of strings."""
    value = arguments.get(name)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a non-empty array")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{name} must contain only non-empty strings")
    return value


def optional_object(arguments: dict[str, Any], name: str) -> dict[str, Any]:
    """Reads an optional object argument."""
    value = arguments.get(name)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def optional_boolean(arguments: dict[str, Any], name: str, default: bool) -> bool:
    """Reads an optional boolean argument."""
    value = arguments.get(name)
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def optional_number_between(arguments: dict[str, Any], name: str, minimum: float, maximum: float) -> float | None:
    """Reads an optional numeric argument constrained to an inclusive range."""
    value = arguments.get(name)
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a number")
    number = float(value)
    if number < minimum or number > maximum:
        raise ValueError(f"{name} must be between {minimum:g} and {maximum:g}")
    return number

