"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime, timezone

from oracle.oci_document_understanding_mcp_server.models import (
    ClassificationOptions,
    ClassificationRequest,
    DocumentSource,
    ExtractionOptions,
    ExtractionRequest,
    RawOciDocumentResult,
)
from oracle.oci_document_understanding_mcp_server.oci.config import OciDocumentUnderstandingConfig
from oracle.oci_document_understanding_mcp_server.oci.request_mapper import classification_config, extraction_configs
from oracle.oci_document_understanding_mcp_server.parsers.classification import ClassificationOutputParser
from oracle.oci_document_understanding_mcp_server.parsers.extraction import ExtractionOutputParser


def _raw(payload: dict) -> RawOciDocumentResult:
    return RawOciDocumentResult(
        request_id="req",
        operation="op",
        received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        payload=payload,
    )


def test_extraction_parser_reads_text_from_pages() -> None:
    result = ExtractionOutputParser().parse(_raw({"pages": [{"lines": [{"text": "line 1"}, {"text": "line 2"}]}]}))

    assert result["text"] == "line 1\nline 2"
    assert result["keyValues"] == []
    assert result["metadata"]["requestId"] == "req"


def test_classification_parser_falls_back_to_top_classification() -> None:
    result = ClassificationOutputParser().parse(_raw({"documentClassification": [{"documentType": "RECEIPT", "confidence": 0.8}]}))

    assert result["documentType"] == "RECEIPT"
    assert result["confidence"] == 0.8


def test_classification_parser_handles_missing_or_unstructured_classifications() -> None:
    parser = ClassificationOutputParser()

    assert parser.parse(_raw({"classifications": []}))["documentType"] is None
    assert parser.parse(_raw({"classifications": ["INVOICE"]}))["confidence"] is None


def test_request_mapper_redacts_inline_content_and_preserves_object_storage() -> None:
    config = OciDocumentUnderstandingConfig(
        runtime_mode="stub",
        region="us-phoenix-1",
        endpoint=None,
        auth_mode="none",
        default_compartment_id="ocid1.compartment.oc1..example",
        config_file_path=None,
        profile="DEFAULT",
    )
    inline_source = DocumentSource(source_type="INLINE_BASE64", document="SGVsbG8=", mime_type="application/pdf")
    object_source = DocumentSource(source_type="OBJECT_STORAGE", namespace_name="ns", bucket_name="bucket", object_name="doc.pdf")
    extraction = ExtractionRequest(document_source=inline_source, features=["TEXT"], options=ExtractionOptions(language="en", include_confidence=True))
    classification = ClassificationRequest(document_source=object_source, options=ClassificationOptions(language="en", confidence_threshold=0.2), document_type_hint="INVOICE")

    extraction_config = extraction_configs(extraction, config)[0]
    classification_request_config = classification_config(classification, config)

    assert extraction_config["parameters"]["document"]["content"] == "<redacted>"
    assert extraction_config["parameters"]["document"]["contentLength"] == 8
    assert classification_request_config["parameters"]["document"]["objectName"] == "doc.pdf"


def test_extraction_parser_ignores_unstructured_pages_and_lines() -> None:
    result = ExtractionOutputParser().parse(_raw({"pages": ["bad", {"lines": ["bad", {"text": "line"}]}]}))

    assert result["text"] == "line"
