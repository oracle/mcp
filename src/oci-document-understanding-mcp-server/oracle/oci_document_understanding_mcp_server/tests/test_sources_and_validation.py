"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import pytest

from oracle.oci_document_understanding_mcp_server.handlers.sources import parse_document_source
from oracle.oci_document_understanding_mcp_server.handlers.validation import (
    optional_boolean,
    optional_number_between,
    required_base64_string,
    required_string_list,
)
from oracle.oci_document_understanding_mcp_server.handlers.ids import document_id_from_source


def test_parse_legacy_inline_source_and_document_id() -> None:
    source = parse_document_source({"document": "SGVsbG8=", "mime_type": "application/pdf"})

    assert source.source_type == "INLINE_BASE64"
    assert source.document == "SGVsbG8="
    assert document_id_from_source(source).startswith("doc_")


def test_parse_object_storage_source() -> None:
    source = parse_document_source(
        {
            "document_source": {
                "source_type": "OBJECT_STORAGE",
                "namespace_name": "namespace",
                "bucket_name": "bucket",
                "object_name": "doc.pdf",
                "page_range": ["1-3"],
            }
        }
    )

    assert source.source_type == "OBJECT_STORAGE"
    assert source.namespace_name == "namespace"
    assert source.page_range == ["1-3"]
    assert document_id_from_source(source).startswith("doc_")


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"document": "not base64", "mime_type": "application/pdf"}, "valid base64"),
        ({"document_source": {"source_type": "BAD"}}, "source_type"),
        ({"document_source": {"source_type": "OBJECT_STORAGE", "namespace_name": "n"}}, "bucket_name"),
        ({"document_source": []}, "document_source must be an object"),
    ],
)
def test_parse_document_source_rejects_invalid_inputs(arguments: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_document_source(arguments)


def test_validation_helpers_cover_error_paths() -> None:
    assert required_base64_string({"document": "SGVsbG8="}, "document") == "SGVsbG8="
    assert required_string_list({"features": ["TEXT"]}, "features") == ["TEXT"]
    assert optional_boolean({}, "include_confidence", True) is True
    assert optional_number_between({"threshold": 1}, "threshold", 0, 1) == 1.0

    with pytest.raises(ValueError, match="non-empty array"):
        required_string_list({"features": []}, "features")
    with pytest.raises(ValueError, match="boolean"):
        optional_boolean({"include_confidence": "true"}, "include_confidence", True)
    with pytest.raises(ValueError, match="between"):
        optional_number_between({"threshold": 2}, "threshold", 0, 1)
