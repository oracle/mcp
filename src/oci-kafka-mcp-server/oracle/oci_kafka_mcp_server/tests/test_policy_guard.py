"""Tests for the policy guard engine."""

from oracle.oci_kafka_mcp_server.security.policy_guard import PolicyGuard, RiskLevel


class TestPolicyGuardReadOnly:
    """Test policy guard in read-only mode (default)."""

    def test_read_tools_allowed(self, policy_guard_readonly: PolicyGuard) -> None:
        """Read-only tools should be allowed even in read-only mode."""
        read_tools = [
            "oci_kafka_get_cluster_health",
            "oci_kafka_list_topics",
            "oci_kafka_describe_topic",
            "oci_kafka_get_consumer_lag",
            "oci_kafka_get_partition_skew",
            "oci_kafka_detect_under_replicated_partitions",
        ]
        for tool in read_tools:
            result = policy_guard_readonly.check(tool, {})
            assert result.allowed, f"Read tool '{tool}' should be allowed"

    def test_write_tools_denied(self, policy_guard_readonly: PolicyGuard) -> None:
        """Write tools should be denied in read-only mode."""
        write_tools = [
            "oci_kafka_create_topic",
            "oci_kafka_delete_topic",
            "oci_kafka_update_topic_config",
            "oci_kafka_create_cluster",
            "oci_kafka_scale_cluster",
            "oci_kafka_reset_consumer_offset",
            "oci_kafka_delete_consumer_group",
        ]
        for tool in write_tools:
            result = policy_guard_readonly.check(tool, {})
            assert not result.allowed, f"Write tool '{tool}' should be denied"
            assert "allow-writes" in result.reason


class TestPolicyGuardReadWrite:
    """Test policy guard with writes enabled."""

    def test_write_tools_allowed(self, policy_guard_readwrite: PolicyGuard) -> None:
        """Write tools should be allowed when writes are enabled."""
        result = policy_guard_readwrite.check("oci_kafka_create_topic", {})
        assert result.allowed

    def test_high_risk_needs_confirmation(self, policy_guard_readwrite: PolicyGuard) -> None:
        """HIGH risk tools should require confirmation."""
        high_risk_tools = [
            "oci_kafka_delete_topic",
            "oci_kafka_create_cluster",
            "oci_kafka_scale_cluster",
            "oci_kafka_reset_consumer_offset",
            "oci_kafka_delete_consumer_group",
        ]
        for tool in high_risk_tools:
            result = policy_guard_readwrite.check(tool, {})
            assert result.allowed, f"Tool '{tool}' should be allowed"
            assert result.needs_confirmation, f"Tool '{tool}' should require confirmation"
            assert result.risk_level == RiskLevel.HIGH

    def test_medium_risk_no_confirmation(self, policy_guard_readwrite: PolicyGuard) -> None:
        """MEDIUM risk tools should NOT require confirmation."""
        result = policy_guard_readwrite.check("oci_kafka_create_topic", {})
        assert result.allowed
        assert not result.needs_confirmation
        assert result.risk_level == RiskLevel.MEDIUM

    def test_low_risk_no_confirmation(self, policy_guard_readwrite: PolicyGuard) -> None:
        """LOW risk tools should not require confirmation."""
        result = policy_guard_readwrite.check("oci_kafka_list_topics", {})
        assert result.allowed
        assert not result.needs_confirmation
        assert result.risk_level == RiskLevel.LOW
