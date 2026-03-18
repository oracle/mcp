"""Tests for the audit logger."""

import json
import logging

from oracle.oci_kafka_mcp_server.audit.logger import AuditEntry, AuditLogger


class TestAuditEntry:
    """Test AuditEntry dataclass."""

    def test_creates_input_hash(self) -> None:
        """AuditEntry should create a hash of input params."""
        entry = AuditEntry(tool_name="test_tool", input_params={"key": "value"})
        assert entry.input_hash != ""
        assert len(entry.input_hash) == 16

    def test_same_inputs_same_hash(self) -> None:
        """Same inputs should produce the same hash."""
        entry1 = AuditEntry(tool_name="test", input_params={"a": 1, "b": 2})
        entry2 = AuditEntry(tool_name="test", input_params={"b": 2, "a": 1})
        assert entry1.input_hash == entry2.input_hash

    def test_different_inputs_different_hash(self) -> None:
        """Different inputs should produce different hashes."""
        entry1 = AuditEntry(tool_name="test", input_params={"a": 1})
        entry2 = AuditEntry(tool_name="test", input_params={"a": 2})
        assert entry1.input_hash != entry2.input_hash

    def test_default_status_is_pending(self) -> None:
        """Default result_status should be 'pending'."""
        entry = AuditEntry(tool_name="test", input_params={})
        assert entry.result_status == "pending"

    def test_timestamp_is_set(self) -> None:
        """Timestamp should be automatically set."""
        entry = AuditEntry(tool_name="test", input_params={})
        assert entry.timestamp is not None
        assert "T" in entry.timestamp  # ISO format


class TestAuditLogger:
    """Test AuditLogger context manager."""

    def test_successful_audit(self, caplog: logging.LogRecord) -> None:
        """Successful tool execution should log with status 'success'."""
        audit = AuditLogger()

        with caplog.at_level(logging.INFO, logger="oci_kafka_mcp.audit"):
            with audit.audit_tool("test_tool", {"param": "value"}) as entry:
                entry.result_status = "success"

        assert len(caplog.records) == 1
        log_data = json.loads(caplog.records[0].message)
        assert log_data["audit"] is True
        assert log_data["toolName"] == "test_tool"
        assert log_data["resultStatus"] == "success"
        assert log_data["executionTimeMs"] >= 0

    def test_error_audit(self, caplog: logging.LogRecord) -> None:
        """Failed tool execution should log with error details."""
        audit = AuditLogger()

        with caplog.at_level(logging.INFO, logger="oci_kafka_mcp.audit"):
            try:
                with audit.audit_tool("fail_tool", {}) as _entry:
                    raise ValueError("Something went wrong")
            except ValueError:
                pass

        assert len(caplog.records) == 1
        log_data = json.loads(caplog.records[0].message)
        assert log_data["resultStatus"] == "error"
        assert log_data["errorMessage"] == "Something went wrong"

    def test_execution_time_measured(self, caplog: logging.LogRecord) -> None:
        """Execution time should be measured in milliseconds."""
        import time

        audit = AuditLogger()

        with caplog.at_level(logging.INFO, logger="oci_kafka_mcp.audit"):
            with audit.audit_tool("slow_tool", {}) as entry:
                time.sleep(0.01)  # 10ms
                entry.result_status = "success"

        log_data = json.loads(caplog.records[0].message)
        assert log_data["executionTimeMs"] >= 10
