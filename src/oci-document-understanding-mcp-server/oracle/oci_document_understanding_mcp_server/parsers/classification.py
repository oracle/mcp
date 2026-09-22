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
        classifications = self._classifications(payload)
        threshold = payload.get("confidenceThreshold")
        if isinstance(threshold, (int, float)):
            classifications = [
                classification
                for classification in classifications
                if isinstance(classification.get("confidence"), (int, float))
                and classification["confidence"] >= threshold
            ]
        return {
            "documentType": self._top_label(classifications),
            "confidence": self._top_confidence(classifications),
            "classifications": classifications,
            "metadata": {
                "requestId": raw_result.request_id,
                "operation": raw_result.operation,
                "receivedAt": raw_result.received_at.isoformat().replace("+00:00", "Z"),
                "provider": payload.get("provider", "oci-sdk"),
                "requestConfig": payload.get("requestConfig", {}),
            },
        }

    def _classifications(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Normalizes stub and OCI SDK classification result shapes."""
        values = payload.get("classifications") or payload.get("documentClassification")
        if values is None:
            values = payload.get("detected_document_types") or self._page_document_types(payload)
        if not isinstance(values, list):
            return []
        return [
            {
                **value,
                "label": value.get("label") or value.get("documentType") or value.get("document_type"),
                "confidence": value.get("confidence"),
            }
            for value in values
            if isinstance(value, dict)
        ]

    def _page_document_types(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Collects document types returned per page when no document-level list exists."""
        values: list[dict[str, Any]] = []
        for page in payload.get("pages") or []:
            if isinstance(page, dict):
                values.extend(value for value in page.get("detected_document_types") or [] if isinstance(value, dict))
        return values

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
