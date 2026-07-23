"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any

from oracle.oci_document_understanding_mcp_server.models import RawOciDocumentResult


class ExtractionOutputParser:
    """Converts raw OCI extraction output into structured MCP data."""

    def parse(self, raw_result: RawOciDocumentResult) -> dict[str, Any]:
        """Parses extraction payload fields into the unified data shape."""
        payload = raw_result.payload
        return {
            "text": payload.get("text") or payload.get("extractedText") or self._text_from_pages(payload),
            "keyValues": payload.get("keyValues") or payload.get("key_value_fields") or [],
            "tables": payload.get("tables") or [],
            "elements": payload.get("elements") or [],
            "metadata": {
                "requestId": raw_result.request_id,
                "operation": raw_result.operation,
                "receivedAt": raw_result.received_at.isoformat().replace("+00:00", "Z"),
                "provider": payload.get("provider", "oci-sdk"),
                "requestConfigs": payload.get("requestConfigs", []),
            },
        }

    def _text_from_pages(self, payload: dict[str, Any]) -> str:
        """Best-effort text extraction from page-oriented SDK dictionaries."""
        pages = payload.get("pages")
        if not isinstance(pages, list):
            return ""
        lines: list[str] = []
        for page in pages:
            if isinstance(page, dict):
                for line in page.get("lines", []) or []:
                    if isinstance(line, dict) and isinstance(line.get("text"), str):
                        lines.append(line["text"])
        return "\n".join(lines)

