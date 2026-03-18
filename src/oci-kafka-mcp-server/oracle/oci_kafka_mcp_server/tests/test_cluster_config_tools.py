"""Tests for OCI cluster configuration management tools."""

from __future__ import annotations

from oracle.oci_kafka_mcp_server.security.policy_guard import PolicyGuard, RiskLevel


class TestCreateClusterConfigPolicy:
    def test_denied_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_create_cluster_config", {})
        assert not result.allowed
        assert "allow-writes" in result.reason

    def test_allowed_in_readwrite_mode(self, policy_guard_readwrite: PolicyGuard) -> None:
        result = policy_guard_readwrite.check("oci_kafka_create_cluster_config", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.MEDIUM


class TestGetOciClusterConfigPolicy:
    def test_allowed_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_get_cluster_config", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.LOW

    def test_allowed_in_readwrite_mode(self, policy_guard_readwrite: PolicyGuard) -> None:
        result = policy_guard_readwrite.check("oci_kafka_get_cluster_config", {})
        assert result.allowed


class TestListClusterConfigsPolicy:
    def test_allowed_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_list_cluster_configs", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.LOW


class TestUpdateClusterConfigPolicy:
    def test_denied_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_update_cluster_config", {})
        assert not result.allowed

    def test_allowed_in_readwrite_mode(self, policy_guard_readwrite: PolicyGuard) -> None:
        result = policy_guard_readwrite.check("oci_kafka_update_cluster_config", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.MEDIUM


class TestDeleteClusterConfigPolicy:
    def test_denied_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_delete_cluster_config", {})
        assert not result.allowed

    def test_requires_confirmation_in_readwrite_mode(
        self, policy_guard_readwrite: PolicyGuard
    ) -> None:
        result = policy_guard_readwrite.check("oci_kafka_delete_cluster_config", {})
        assert result.allowed
        assert result.needs_confirmation
        assert result.risk_level == RiskLevel.HIGH


class TestChangeClusterConfigCompartmentPolicy:
    def test_denied_in_readonly_mode(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_change_cluster_config_compartment", {})
        assert not result.allowed

    def test_allowed_in_readwrite_mode(self, policy_guard_readwrite: PolicyGuard) -> None:
        result = policy_guard_readwrite.check("oci_kafka_change_cluster_config_compartment", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.MEDIUM


class TestClusterConfigVersionPolicy:
    def test_get_version_allowed_readonly(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_get_cluster_config_version", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.LOW

    def test_list_versions_allowed_readonly(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_list_cluster_config_versions", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.LOW

    def test_delete_version_denied_readonly(self, policy_guard_readonly: PolicyGuard) -> None:
        result = policy_guard_readonly.check("oci_kafka_delete_cluster_config_version", {})
        assert not result.allowed

    def test_delete_version_allowed_readwrite(self, policy_guard_readwrite: PolicyGuard) -> None:
        result = policy_guard_readwrite.check("oci_kafka_delete_cluster_config_version", {})
        assert result.allowed
        assert result.risk_level == RiskLevel.MEDIUM


class TestClusterConfigOciSdk:
    def test_get_cluster_config_returns_error_without_sdk(self) -> None:
        from oracle.oci_kafka_mcp_server.oci.kafka_client import OciKafkaClient

        client = OciKafkaClient(config_file="/nonexistent/path", profile="DEFAULT")
        result = client.get_kafka_cluster_config(
            kafka_cluster_config_id="ocid1.kafkaclusterconfig.oc1..xxx"
        )
        assert "error" in result

    def test_list_cluster_configs_returns_error_without_sdk(self) -> None:
        from oracle.oci_kafka_mcp_server.oci.kafka_client import OciKafkaClient

        client = OciKafkaClient(config_file="/nonexistent/path", profile="DEFAULT")
        result = client.list_kafka_cluster_configs(compartment_id="ocid1.compartment.oc1..xxx")
        assert "error" in result
