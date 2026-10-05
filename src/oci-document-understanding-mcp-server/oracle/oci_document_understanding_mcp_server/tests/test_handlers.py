"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime, timezone

import pytest

from oracle.oci_document_understanding_mcp_server.handlers.classification import DocumentClassificationHandler
from oracle.oci_document_understanding_mcp_server.handlers.extraction import DocumentExtractionHandler
from oracle.oci_document_understanding_mcp_server.models import ClassificationRequest, ExtractionRequest, RawOciDocumentResult
from oracle.oci_document_understanding_mcp_server.parsers.classification import ClassificationOutputParser
from oracle.oci_document_understanding_mcp_server.parsers.extraction import ExtractionOutputParser


class FakeProvider:
    def __init__(self) -> None:
        self.extraction_request: ExtractionRequest | None = None
        self.classification_request: ClassificationRequest | None = None

    def extract(self, request: ExtractionRequest) -> RawOciDocumentResult:
        self.extraction_request = request
        return RawOciDocumentResult(
            request_id="req-extract",
            operation="extract",
            received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            payload={"text": "hello", "keyValues": [{"key": "A", "value": "B"}]},
        )

    def classify(self, request: ClassificationRequest) -> RawOciDocumentResult:
        self.classification_request = request
        return RawOciDocumentResult(
            request_id="req-classify",
            operation="classify",
            received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            payload={"classifications": [{"label": "INVOICE", "confidence": 0.9}]},
        )


def test_extraction_handler_preserves_request_and_response_shape() -> None:
    provider = FakeProvider()
    handler = DocumentExtractionHandler(provider, ExtractionOutputParser())

    result = handler.handle(
        {
            "document": "SGVsbG8=",
            "mime_type": "application/pdf",
            "features": ["text", "KEY_VALUE"],
            "options": {"language": "en", "include_confidence": False},
        }
    )

    assert provider.extraction_request is not None
    assert provider.extraction_request.features == ["TEXT", "KEY_VALUE"]
    assert provider.extraction_request.options.language == "en"
    assert provider.extraction_request.options.include_confidence is False
    assert result["status"] == "Successful"
    assert result["job_id"] == "req-extract"
    assert result["data"]["text"] == "hello"


def test_extraction_handler_rejects_invalid_feature() -> None:
    handler = DocumentExtractionHandler(FakeProvider(), ExtractionOutputParser())

    with pytest.raises(ValueError, match="Unsupported extraction feature"):
        handler.handle({"document": "SGVsbG8=", "mime_type": "application/pdf", "features": ["BAD"]})


def test_classification_handler_normalizes_hint_and_options() -> None:
    provider = FakeProvider()
    handler = DocumentClassificationHandler(provider, ClassificationOutputParser())

    result = handler.handle(
        {
            "document": "SGVsbG8=",
            "mime_type": "application/pdf",
            "document_type_hint": "bank statement",
            "options": {"language": "en", "confidence_threshold": 0.2},
        }
    )

    assert provider.classification_request is not None
    assert provider.classification_request.document_type_hint == "BANK_STATEMENT"
    assert provider.classification_request.options.confidence_threshold == 0.2
    assert result["data"]["documentType"] == "INVOICE"
    assert result["data"]["confidence"] == 0.9


def test_classification_handler_rejects_bad_hint() -> None:
    handler = DocumentClassificationHandler(FakeProvider(), ClassificationOutputParser())

    with pytest.raises(ValueError, match="document_type_hint must be one of"):
        handler.handle({"document": "SGVsbG8=", "mime_type": "application/pdf", "document_type_hint": "contract"})
