"""Tests for OCI work request and node shape tools."""

from __future__ import annotations

from oracle.oci_kafka_mcp_server.security.policy_guard import PolicyGuard, RiskLevel


class TestGetWorkRequestPolicy:
    def test_allowed_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_get_work_request", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.LOW

    def test_allowed_in_readwrite_mode(self, policy_guard_readwrite: PolicyGuard) -> None:
        result = policy_guard_readwrite.check("oci_kafka_get_work_request", {})
        assert result.allowed


class TestListWorkRequestsPolicy:
    def test_allowed_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_list_work_requests", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.LOW


class TestCancelWorkRequestPolicy:
    def test_denied_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_cancel_work_request", {})
        assert not result.allowed
        assert "allow-writes" in result.reason

    def test_allowed_in_readwrite_mode(self, policy_guard_readwrite: PolicyGuard) -> None:
        result = policy_guard_readwrite.check("oci_kafka_cancel_work_request", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.MEDIUM


class TestWorkRequestErrorsAndLogsPolicy:
    def test_errors_allowed_readonly(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_get_work_request_errors", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.LOW

    def test_logs_allowed_readonly(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_get_work_request_logs", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.LOW


class TestListNodeShapesPolicy:
    def test_allowed_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_list_node_shapes", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.LOW

    def test_allowed_in_readwrite_mode(self, policy_guard_readwrite: PolicyGuard) -> None:
        result = policy_guard_readwrite.check("oci_kafka_list_node_shapes", {})
        assert result.allowed


class TestWorkRequestOciSdk:
    def test_get_work_request_returns_error_without_sdk(self) -> None:
        from oracle.oci_kafka_mcp_server.oci.kafka_client import OciKafkaClient

        client = OciKafkaClient(config_file="/nonexistent/path", profile="DEFAULT")
        result = client.get_work_request(work_request_id="ocid1.workrequest.oc1..xxx")
        assert "error" in result

    def test_list_work_requests_returns_error_without_sdk(self) -> None:
        from oracle.oci_kafka_mcp_server.oci.kafka_client import OciKafkaClient

        client = OciKafkaClient(config_file="/nonexistent/path", profile="DEFAULT")
        result = client.list_work_requests(compartment_id="ocid1.compartment.oc1..xxx")
        assert "error" in result

    def test_list_node_shapes_returns_error_without_sdk(self) -> None:
        from oracle.oci_kafka_mcp_server.oci.kafka_client import OciKafkaClient

        client = OciKafkaClient(config_file="/nonexistent/path", profile="DEFAULT")
        result = client.list_node_shapes(compartment_id="ocid1.compartment.oc1..xxx")
        assert "error" in result
