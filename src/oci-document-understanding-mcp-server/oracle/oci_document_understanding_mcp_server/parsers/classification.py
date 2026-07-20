"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any

from oracle.oci_document_understanding_mcp_server.models import RawOciDocumentResult


class ClassificationOutputParser:
    """Converts raw OCI classification output into structured MCP data."""

    def parse(self, raw_result: RawOciDocumentResult) -> dict[str, Any]:
        """Parses classification payload fields into the unified data shape."""
        payload = raw_result.payload
        classifications = payload.get("classifications") or payload.get("documentClassification") or []
        return {
            "documentType": payload.get("documentType") or self._top_label(classifications),
            "confidence": payload.get("confidence") or self._top_confidence(classifications),
            "classifications": classifications,
            "metadata": {
                "requestId": raw_result.request_id,
                "operation": raw_result.operation,
                "receivedAt": raw_result.received_at.isoformat().replace("+00:00", "Z"),
                "provider": payload.get("provider", "oci-sdk"),
                "requestConfig": payload.get("requestConfig", {}),
            },
        }

    def _top_label(self, classifications: Any) -> str | None:
        """Returns the highest-ranked classification label if present."""
        if isinstance(classifications, list) and classifications:
            first = classifications[0]
            if isinstance(first, dict):
                return first.get("label") or first.get("documentType")
        return None

    def _top_confidence(self, classifications: Any) -> float | None:
        """Returns the highest-ranked classification confidence if present."""
        if isinstance(classifications, list) and classifications:
            first = classifications[0]
            if isinstance(first, dict):
                return first.get("confidence")
        return None

