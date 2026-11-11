"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any

from oracle.oci_document_understanding_mcp_server.handlers.validation import optional_object, required_base64_string, required_string
from oracle.oci_document_understanding_mcp_server.models import DocumentSource


def parse_document_source(arguments: dict[str, Any]) -> DocumentSource:
    """Parses either the new document_source object or the legacy top-level inline fields."""
    if "document_source" not in arguments:
        return DocumentSource(
            source_type="INLINE_BASE64",
            document=required_base64_string(arguments, "document"),
            mime_type=required_string(arguments, "mime_type"),
        )

    source = optional_object(arguments, "document_source")
    source_type = required_string(source, "source_type").upper()
    page_range = _optional_string_list(source, "page_range")

    if source_type == "INLINE_BASE64":
        return DocumentSource(
            source_type=source_type,
            document=required_base64_string(source, "document"),
            mime_type=required_string(source, "mime_type"),
            page_range=page_range,
        )

    if source_type == "OBJECT_STORAGE":
        return DocumentSource(
            source_type=source_type,
            namespace_name=required_string(source, "namespace_name"),
            bucket_name=required_string(source, "bucket_name"),
            object_name=required_string(source, "object_name"),
            page_range=page_range,
        )

    raise ValueError("document_source.source_type must be INLINE_BASE64 or OBJECT_STORAGE")


def _optional_string_list(arguments: dict[str, Any], name: str) -> list[str] | None:
    """Reads an optional list of strings."""
    value = arguments.get(name)
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{name} must be an array of non-empty strings")
    return value
