"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime, timezone

import oci

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
        default_compartment_id="ocid1.compartment.oc1..example",
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


def test_parsers_map_real_oci_sdk_result_models_for_advertised_outputs() -> None:
    models = oci.ai_document.models
    result = models.AnalyzeDocumentResult(
        pages=[
            models.Page(
                page_number=1,
                lines=[models.Line(text="Invoice 123", confidence=0.99)],
                document_fields=[
                    models.DocumentField(
                        field_type="KEY_VALUE",
                        field_label=models.FieldLabel(name="Invoice Number", confidence=0.98),
                        field_value=models.FieldValue(value_type="STRING", text="123", confidence=0.97),
                    )
                ],
                tables=[models.Table(row_count=1, column_count=2, confidence=0.96)],
                bar_codes=[models.BarCode(value="code-123", confidence=0.95)],
                signatures=[models.Signature(confidence=0.94)],
                selection_marks=[models.SelectionMark(state="SELECTED", confidence=0.93)],
            )
        ],
        detected_document_types=[models.DetectedDocumentType(document_type="INVOICE", confidence=0.98)],
    )
    payload = oci.util.to_dict(result)

    extraction = ExtractionOutputParser().parse(_raw(payload))
    classification = ClassificationOutputParser().parse(_raw(payload))

    assert extraction["text"] == "Invoice 123"
    assert extraction["keyValues"][0]["field_value"]["text"] == "123"
    assert extraction["tables"][0]["confidence"] == 0.96
    assert {element["type"] for element in extraction["elements"]} == {"BAR_CODE", "SIGNATURE", "SELECTION_MARK"}
    assert classification["documentType"] == "INVOICE"
    assert classification["confidence"] == 0.98


def test_classification_parser_applies_threshold_and_recalculates_top_result() -> None:
    parser = ClassificationOutputParser()

    filtered = parser.parse(
        _raw(
            {
                "classifications": [
                    {"label": "INVOICE", "confidence": 0.97},
                    {"label": "RECEIPT", "confidence": 0.02},
                ],
                "confidenceThreshold": 0.5,
            }
        )
    )
    empty = parser.parse(
        _raw(
            {
                "classifications": [{"label": "RECEIPT", "confidence": 0.02}],
                "confidenceThreshold": 0.5,
            }
        )
    )

    assert filtered["classifications"] == [{"label": "INVOICE", "confidence": 0.97}]
    assert filtered["documentType"] == "INVOICE"
    assert filtered["confidence"] == 0.97
    assert empty["classifications"] == []
    assert empty["documentType"] is None
    assert empty["confidence"] is None
