"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any

from oracle.oci_document_understanding_mcp_server.handlers.ids import document_id_from_source
from oracle.oci_document_understanding_mcp_server.handlers.sources import parse_document_source
from oracle.oci_document_understanding_mcp_server.handlers.validation import (
    optional_boolean,
    optional_object,
    optional_string,
    required_string_list,
)
from oracle.oci_document_understanding_mcp_server.models import ExtractionOptions, ExtractionRequest
from oracle.oci_document_understanding_mcp_server.oci.provider import OciDocumentUnderstandingProvider
from oracle.oci_document_understanding_mcp_server.parsers.extraction import ExtractionOutputParser
from oracle.oci_document_understanding_mcp_server.response import successful_envelope

ALLOWED_FEATURES = {"TEXT", "KEY_VALUE", "TABLE", "ELEMENT"}


class DocumentExtractionHandler:
    """Validates document_extract input, calls OCI, parses output, and wraps the response."""

    def __init__(self, provider: OciDocumentUnderstandingProvider, parser: ExtractionOutputParser) -> None:
        self.provider = provider
        self.parser = parser

    def handle(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Runs the complete extraction flow for a single MCP tools/call request."""
        request = self._to_request(arguments)
        raw_result = self.provider.extract(request)
        result = self.parser.parse(raw_result)
        return successful_envelope(raw_result.request_id, document_id_from_source(request.document_source), result)

    def _to_request(self, arguments: dict[str, Any]) -> ExtractionRequest:
        """Converts untyped MCP arguments into an internal extraction request."""
        features = [feature.upper() for feature in required_string_list(arguments, "features")]
        unsupported = [feature for feature in features if feature not in ALLOWED_FEATURES]
        if unsupported:
            raise ValueError(f"Unsupported extraction feature(s): {', '.join(unsupported)}")

        options = optional_object(arguments, "options")
        return ExtractionRequest(
            document_source=parse_document_source(arguments),
            features=features,
            options=ExtractionOptions(
                language=optional_string(options, "language"),
                include_confidence=optional_boolean(options, "include_confidence", True),
            ),
        )
