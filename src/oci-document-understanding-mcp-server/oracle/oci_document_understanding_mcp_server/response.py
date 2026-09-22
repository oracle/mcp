"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
from typing import Any


def successful_envelope(job_id: str, document_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Returns the structured response envelope used by Document MCP tools."""
    return {
        "status": "Successful",
        "job_id": job_id,
        "document_id": document_id,
        "data": data,
        "metadata": data.get("metadata", {}),
    }


def failed_envelope(message: str) -> dict[str, Any]:
    """Returns the structured response envelope used for handled failures."""
    return {
        "status": "Failed",
        "job_id": "",
        "document_id": "",
        "data": {"message": message},
        "metadata": {},
    }


def to_text(data: dict[str, Any]) -> str:
    """Serializes a response envelope to compact JSON for text-only clients."""
    return json.dumps(data, separators=(",", ":"))
