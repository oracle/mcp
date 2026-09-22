"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any

from oracle.oci_document_understanding_mcp_server.handlers.ids import document_id_from_source
from oracle.oci_document_understanding_mcp_server.handlers.sources import parse_document_source
from oracle.oci_document_understanding_mcp_server.handlers.validation import (
    optional_number_between,
    optional_object,
    optional_string,
)
from oracle.oci_document_understanding_mcp_server.models import ClassificationOptions, ClassificationRequest
from oracle.oci_document_understanding_mcp_server.oci.provider import OciDocumentUnderstandingProvider
from oracle.oci_document_understanding_mcp_server.parsers.classification import ClassificationOutputParser
from oracle.oci_document_understanding_mcp_server.response import successful_envelope

ALLOWED_DOCUMENT_TYPE_HINTS = {
    "INVOICE",
    "RECEIPT",
    "RESUME",
    "TAX_FORM",
    "DRIVER_LICENSE",
    "PASSPORT",
    "BANK_STATEMENT",
    "CHECK",
    "PAYSLIP",
    "OTHERS",
    "HEALTH_INSURANCE_ID",
}


class DocumentClassificationHandler:
    """Validates document_classify input, calls OCI, parses output, and wraps the response."""

    def __init__(self, provider: OciDocumentUnderstandingProvider, parser: ClassificationOutputParser) -> None:
        self.provider = provider
        self.parser = parser

    def handle(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Runs the complete classification flow for a single MCP tools/call request."""
        request = self._to_request(arguments)
        raw_result = self.provider.classify(request)
        result = self.parser.parse(raw_result)
        return successful_envelope(raw_result.request_id, document_id_from_source(request.document_source), result)

    def _to_request(self, arguments: dict[str, Any]) -> ClassificationRequest:
        """Converts untyped MCP arguments into an internal classification request."""
        options = optional_object(arguments, "options")
        return ClassificationRequest(
            document_source=parse_document_source(arguments),
            options=ClassificationOptions(
                language=optional_string(options, "language"),
                confidence_threshold=optional_number_between(options, "confidence_threshold", 0, 1),
            ),
            document_type_hint=_normalize_document_type_hint(optional_string(arguments, "document_type_hint")),
        )


def _normalize_document_type_hint(value: str | None) -> str | None:
    """Normalizes user-provided document type hints into OCI enum values."""
    if value is None or not value.strip():
        return None
    normalized = value.strip().replace("-", "_").replace(" ", "_").upper()
    if normalized not in ALLOWED_DOCUMENT_TYPE_HINTS:
        allowed = ", ".join(sorted(ALLOWED_DOCUMENT_TYPE_HINTS))
        raise ValueError(f"document_type_hint must be one of: {allowed}")
    return normalized
