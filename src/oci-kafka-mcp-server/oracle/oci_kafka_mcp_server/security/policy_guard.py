"""Policy guard engine for safe AI execution.

Enforces risk classification and confirmation requirements
before executing tools that can modify Kafka state.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class RiskLevel(StrEnum):
    """Risk classification for MCP tools."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# Tool risk classification registry
TOOL_RISK_REGISTRY: dict[str, RiskLevel] = {
    # Cluster operations — read
    "oci_kafka_get_cluster_health": RiskLevel.LOW,
    "oci_kafka_get_cluster_config": RiskLevel.LOW,
    # Cluster operations — write
    "oci_kafka_create_cluster": RiskLevel.HIGH,
    "oci_kafka_scale_cluster": RiskLevel.HIGH,
    # Topic operations — read
    "oci_kafka_list_topics": RiskLevel.LOW,
    "oci_kafka_describe_topic": RiskLevel.LOW,
    # Topic operations — write
    "oci_kafka_create_topic": RiskLevel.MEDIUM,
    "oci_kafka_update_topic_config": RiskLevel.MEDIUM,
    "oci_kafka_delete_topic": RiskLevel.HIGH,
    # Consumer operations — read
    "oci_kafka_get_consumer_lag": RiskLevel.LOW,
    "oci_kafka_list_consumer_groups": RiskLevel.LOW,
    "oci_kafka_describe_consumer_group": RiskLevel.LOW,
    # Consumer operations — write
    "oci_kafka_reset_consumer_offset": RiskLevel.HIGH,
    "oci_kafka_delete_consumer_group": RiskLevel.HIGH,
    # Observability — read
    "oci_kafka_get_partition_skew": RiskLevel.LOW,
    "oci_kafka_detect_under_replicated_partitions": RiskLevel.LOW,
    "oci_kafka_recommend_scaling": RiskLevel.LOW,
    "oci_kafka_analyze_lag_root_cause": RiskLevel.LOW,
    # OCI control plane — read
    "oci_kafka_get_oci_cluster_info": RiskLevel.LOW,
    "oci_kafka_list_oci_clusters": RiskLevel.LOW,
    # OCI cluster lifecycle — write
    "oci_kafka_update_cluster": RiskLevel.MEDIUM,
    "oci_kafka_delete_cluster": RiskLevel.HIGH,
    "oci_kafka_change_cluster_compartment": RiskLevel.HIGH,
    "oci_kafka_enable_superuser": RiskLevel.HIGH,
    "oci_kafka_disable_superuser": RiskLevel.MEDIUM,
    # OCI cluster configuration — read
    "oci_kafka_get_oci_cluster_config": RiskLevel.LOW,
    "oci_kafka_list_cluster_configs": RiskLevel.LOW,
    "oci_kafka_get_cluster_config_version": RiskLevel.LOW,
    "oci_kafka_list_cluster_config_versions": RiskLevel.LOW,
    # OCI cluster configuration — write
    "oci_kafka_create_cluster_config": RiskLevel.MEDIUM,
    "oci_kafka_update_cluster_config": RiskLevel.MEDIUM,
    "oci_kafka_delete_cluster_config": RiskLevel.HIGH,
    "oci_kafka_change_cluster_config_compartment": RiskLevel.MEDIUM,
    "oci_kafka_delete_cluster_config_version": RiskLevel.MEDIUM,
    # OCI work requests — read
    "oci_kafka_get_work_request": RiskLevel.LOW,
    "oci_kafka_list_work_requests": RiskLevel.LOW,
    "oci_kafka_get_work_request_errors": RiskLevel.LOW,
    "oci_kafka_get_work_request_logs": RiskLevel.LOW,
    "oci_kafka_list_node_shapes": RiskLevel.LOW,
    # OCI work requests — write
    "oci_kafka_cancel_work_request": RiskLevel.MEDIUM,
}

# Tools that require explicit confirmation before execution
CONFIRMATION_REQUIRED: set[str] = {
    "oci_kafka_create_cluster",
    "oci_kafka_scale_cluster",
    "oci_kafka_delete_cluster",
    "oci_kafka_change_cluster_compartment",
    "oci_kafka_delete_topic",
    "oci_kafka_reset_consumer_offset",
    "oci_kafka_delete_consumer_group",
    "oci_kafka_delete_cluster_config",
    "oci_kafka_enable_superuser",
}

# Tools that modify state (require --allow-writes)
WRITE_TOOLS: set[str] = {
    "oci_kafka_create_cluster",
    "oci_kafka_scale_cluster",
    "oci_kafka_update_cluster",
    "oci_kafka_delete_cluster",
    "oci_kafka_change_cluster_compartment",
    "oci_kafka_enable_superuser",
    "oci_kafka_disable_superuser",
    "oci_kafka_create_topic",
    "oci_kafka_update_topic_config",
    "oci_kafka_delete_topic",
    "oci_kafka_reset_consumer_offset",
    "oci_kafka_delete_consumer_group",
    "oci_kafka_create_cluster_config",
    "oci_kafka_update_cluster_config",
    "oci_kafka_delete_cluster_config",
    "oci_kafka_change_cluster_config_compartment",
    "oci_kafka_delete_cluster_config_version",
    "oci_kafka_cancel_work_request",
}


class PolicyGuard:
    """Validates tool execution against policy rules."""

    def __init__(self, allow_writes: bool = False) -> None:
        self._allow_writes = allow_writes

    def check(self, tool_name: str, params: dict[str, Any]) -> PolicyResult:
        """Check if a tool execution is allowed.

        Returns a PolicyResult indicating whether execution should proceed,
        needs confirmation, or is denied.
        """
        # Check if writes are allowed
        if tool_name in WRITE_TOOLS and not self._allow_writes:
            return PolicyResult(
                allowed=False,
                reason=f"Write tool '{tool_name}' is disabled. "
                "Start the server with --allow-writes to enable write operations.",
            )

        # Check risk level
        risk = TOOL_RISK_REGISTRY.get(tool_name, RiskLevel.LOW)

        # Check if confirmation is required
        needs_confirmation = tool_name in CONFIRMATION_REQUIRED

        return PolicyResult(
            allowed=True,
            risk_level=risk,
            needs_confirmation=needs_confirmation,
            reason=None,
        )


class PolicyResult:
    """Result of a policy guard check."""

    def __init__(
        self,
        allowed: bool,
        risk_level: RiskLevel = RiskLevel.LOW,
        needs_confirmation: bool = False,
        reason: str | None = None,
    ) -> None:
        self.allowed = allowed
        self.risk_level = risk_level
        self.needs_confirmation = needs_confirmation
        self.reason = reason
