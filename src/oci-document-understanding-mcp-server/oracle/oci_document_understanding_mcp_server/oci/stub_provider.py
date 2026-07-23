"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from oracle.oci_document_understanding_mcp_server.models import ClassificationRequest, ExtractionRequest, RawOciDocumentResult
from oracle.oci_document_understanding_mcp_server.oci.config import OciDocumentUnderstandingConfig
from oracle.oci_document_understanding_mcp_server.oci.request_mapper import classification_config, extraction_configs


class StubOciDocumentUnderstandingProvider:
    """Deterministic provider for smoke tests and local MCP flow debugging."""

    def __init__(self, config: OciDocumentUnderstandingConfig) -> None:
        self.config = config

    def extract(self, request: ExtractionRequest) -> RawOciDocumentResult:
        """Returns fake extraction output shaped like the real provider payload."""
        payload: dict[str, Any] = {
            "provider": "stub",
            "region": self.config.region,
            "requestConfigs": extraction_configs(request, self.config),
            "includeConfidence": request.options.include_confidence,
        }
        if "TEXT" in request.features:
            payload["text"] = "Sample extracted text from OCI Document Understanding."
        if "KEY_VALUE" in request.features:
            payload["keyValues"] = [
                {"key": "InvoiceNumber", "value": "INV-001", "confidence": 0.98},
                {"key": "TotalAmount", "value": "1250.00", "confidence": 0.95},
            ]
        if "TABLE" in request.features:
            payload["tables"] = [
                {
                    "headers": ["Item", "Quantity", "Amount"],
                    "rows": [["Consulting", "10", "1000.00"], ["Support", "5", "250.00"]],
                    "confidence": 0.93,
                }
            ]
        if "ELEMENT" in request.features:
            payload["elements"] = [
                {"type": "TITLE", "text": "Invoice", "page": 1, "confidence": 0.99},
                {"type": "PARAGRAPH", "text": "Sample extracted text from OCI Document Understanding.", "page": 1, "confidence": 0.94},
            ]
        return RawOciDocumentResult(
            request_id=str(uuid4()),
            operation="extract",
            received_at=datetime.now(timezone.utc),
            payload=payload,
        )

    def classify(self, request: ClassificationRequest) -> RawOciDocumentResult:
        """Returns fake classification output shaped like the real provider payload."""
        payload: dict[str, Any] = {
            "provider": "stub",
            "region": self.config.region,
            "requestConfig": classification_config(request, self.config),
            "documentTypeHint": request.document_type_hint,
            "documentType": "INVOICE",
            "confidence": 0.97,
            "classifications": [
                {"label": "INVOICE", "confidence": 0.97},
                {"label": "RECEIPT", "confidence": 0.02},
                {"label": "CONTRACT", "confidence": 0.01},
            ],
        }
        if request.options.confidence_threshold is not None:
            payload["confidenceThreshold"] = request.options.confidence_threshold
        return RawOciDocumentResult(
            request_id=str(uuid4()),
            operation="classify",
            received_at=datetime.now(timezone.utc),
            payload=payload,
        )
