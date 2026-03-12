"""Tests for cluster lifecycle management tools (create, scale)."""

from __future__ import annotations

from oracle.oci_kafka_mcp_server.security.policy_guard import PolicyGuard, RiskLevel


class TestCreateClusterPolicy:
    """Test policy guard checks for create_cluster."""

    def test_denied_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        """create_cluster should be denied in read-only mode."""
        result = policy_guard_readonly.check("oci_kafka_create_cluster", {})
        assert not result.allowed
        assert "allow-writes" in result.reason

    def test_requires_confirmation(self, policy_guard_readwrite: PolicyGuard) -> None:
        """create_cluster should require confirmation in read-write mode."""
        result = policy_guard_readwrite.check("oci_kafka_create_cluster", {})
        assert result.allowed
        assert result.needs_confirmation
        assert result.risk_level == RiskLevel.HIGH


class TestScaleClusterPolicy:
    """Test policy guard checks for scale_cluster."""

    def test_denied_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        """scale_cluster should be denied in read-only mode."""
        result = policy_guard_readonly.check("oci_kafka_scale_cluster", {})
        assert not result.allowed

    def test_requires_confirmation(self, policy_guard_readwrite: PolicyGuard) -> None:
        """scale_cluster should require confirmation in read-write mode."""
        result = policy_guard_readwrite.check("oci_kafka_scale_cluster", {})
        assert result.allowed
        assert result.needs_confirmation
        assert result.risk_level == RiskLevel.HIGH


class TestCreateClusterOciSdk:
    """Test the OCI SDK integration for cluster creation."""

    def test_returns_error_without_sdk(self) -> None:
        """OciKafkaClient should return an error dict when OCI SDK is unavailable."""
        from oracle.oci_kafka_mcp_server.oci.kafka_client import OciKafkaClient

        client = OciKafkaClient(config_file="/nonexistent/path", profile="DEFAULT")
        result = client.create_kafka_cluster(
            display_name="test",
            compartment_id="ocid1.compartment.oc1..xxx",
            subnet_id="ocid1.subnet.oc1..xxx",
        )
        assert "error" in result


class TestDeleteConsumerGroupPolicy:
    """Test policy guard checks for delete_consumer_group."""

    def test_denied_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        """delete_consumer_group should be denied in read-only mode."""
        result = policy_guard_readonly.check("oci_kafka_delete_consumer_group", {})
        assert not result.allowed

    def test_requires_confirmation(self, policy_guard_readwrite: PolicyGuard) -> None:
        """delete_consumer_group should require confirmation in read-write mode."""
        result = policy_guard_readwrite.check("oci_kafka_delete_consumer_group", {})
        assert result.allowed
        assert result.needs_confirmation
        assert result.risk_level == RiskLevel.HIGH


class TestResetConsumerOffsetPolicy:
    """Test policy guard checks for reset_consumer_offset."""

    def test_denied_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        """reset_consumer_offset should be denied in read-only mode."""
        result = policy_guard_readonly.check("oci_kafka_reset_consumer_offset", {})
        assert not result.allowed

    def test_requires_confirmation(self, policy_guard_readwrite: PolicyGuard) -> None:
        """reset_consumer_offset should require confirmation in read-write mode."""
        result = policy_guard_readwrite.check("oci_kafka_reset_consumer_offset", {})
        assert result.allowed
        assert result.needs_confirmation
        assert result.risk_level == RiskLevel.HIGH
