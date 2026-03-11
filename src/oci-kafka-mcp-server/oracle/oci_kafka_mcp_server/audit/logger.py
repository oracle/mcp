"""Structured audit logging for all MCP tool executions."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("oci_kafka_mcp.audit")


@dataclass
class AuditEntry:
    """A single audit log entry for a tool execution."""

    tool_name: str
    input_params: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    result_status: str = "pending"
    error_message: str | None = None
    execution_time_ms: float = 0.0
    input_hash: str = ""

    def __post_init__(self) -> None:
        self.input_hash = hashlib.sha256(
            json.dumps(self.input_params, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]


class AuditLogger:
    """Logs structured audit entries for every tool execution."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("oci_kafka_mcp.audit")

    @contextmanager
    def audit_tool(
        self, tool_name: str, input_params: dict[str, Any]
    ) -> Generator[AuditEntry, None, None]:
        """Context manager that creates, times, and logs an audit entry.

        Usage:
            with audit.audit_tool("oci_kafka_list_topics", {"cluster_id": "xxx"}) as entry:
                result = do_work()
                entry.result_status = "success"
        """
        entry = AuditEntry(tool_name=tool_name, input_params=input_params)
        start = time.monotonic()
        try:
            yield entry
        except Exception as exc:
            entry.result_status = "error"
            entry.error_message = str(exc)
            raise
        finally:
            entry.execution_time_ms = round((time.monotonic() - start) * 1000, 2)
            self._emit(entry)

    def _emit(self, entry: AuditEntry) -> None:
        """Emit the audit entry as structured JSON log."""
        record = {
            "audit": True,
            "timestamp": entry.timestamp,
            "toolName": entry.tool_name,
            "inputHash": entry.input_hash,
            "resultStatus": entry.result_status,
            "executionTimeMs": entry.execution_time_ms,
        }
        if entry.error_message:
            record["errorMessage"] = entry.error_message

        self._logger.info(json.dumps(record))


# Module-level singleton
audit = AuditLogger()
