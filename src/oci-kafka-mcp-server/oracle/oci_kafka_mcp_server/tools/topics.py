"""Topic operations tools for OCI Kafka MCP Server."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from oracle.oci_kafka_mcp_server.audit.logger import audit
from oracle.oci_kafka_mcp_server.kafka.admin_client import KafkaAdminClient
from oracle.oci_kafka_mcp_server.kafka.connection import CircuitBreaker
from oracle.oci_kafka_mcp_server.security.policy_guard import PolicyGuard


def register_topic_tools(
    mcp: FastMCP,
    admin_client: KafkaAdminClient,
    policy_guard: PolicyGuard,
    circuit_breaker: CircuitBreaker,
) -> None:
    """Register topic operation tools with the MCP server."""

    @mcp.tool()
    def oci_kafka_list_topics() -> str:
        """List all topics in the Kafka cluster.

        Returns the total topic count and a list of topics with their partition counts.
        Use this to get an overview of all topics in the cluster.
        """
        if not circuit_breaker.allow_request():
            return json.dumps({"error": "Circuit breaker is open. Kafka may be unavailable."})

        with audit.audit_tool("oci_kafka_list_topics", {}) as entry:
            try:
                result = admin_client.list_topics()
                entry.result_status = "success"
                circuit_breaker.record_success()
                return json.dumps(result, indent=2)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to list topics: {e}"})

    @mcp.tool()
    def oci_kafka_describe_topic(topic_name: str) -> str:
        """Get detailed information about a specific Kafka topic.

        Args:
            topic_name: Name of the topic to describe.

        Returns partition details (leader, replicas, ISR), and non-default
        configuration settings. Use this to inspect a topic's health and config.
        """
        if not circuit_breaker.allow_request():
            return json.dumps({"error": "Circuit breaker is open. Kafka may be unavailable."})

        params = {"topic_name": topic_name}
        with audit.audit_tool("oci_kafka_describe_topic", params) as entry:
            try:
                result = admin_client.describe_topic(topic_name)
                entry.result_status = "success"
                circuit_breaker.record_success()
                return json.dumps(result, indent=2)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to describe topic '{topic_name}': {e}"})

    @mcp.tool()
    def oci_kafka_create_topic(
        topic_name: str, num_partitions: int = 6, replication_factor: int = 3
    ) -> str:
        """Create a new Kafka topic.

        Requires --allow-writes to be enabled.

        Args:
            topic_name: Name for the new topic.
            num_partitions: Number of partitions (default: 6).
            replication_factor: Replication factor (default: 3).

        Returns the creation status and topic details.
        """
        params = {
            "topic_name": topic_name,
            "num_partitions": num_partitions,
            "replication_factor": replication_factor,
        }

        check = policy_guard.check("oci_kafka_create_topic", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})

        if not circuit_breaker.allow_request():
            return json.dumps({"error": "Circuit breaker is open. Kafka may be unavailable."})

        with audit.audit_tool("oci_kafka_create_topic", params) as entry:
            try:
                result = admin_client.create_topic(topic_name, num_partitions, replication_factor)
                entry.result_status = result.get("status", "unknown")
                circuit_breaker.record_success()
                return json.dumps(result, indent=2)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to create topic '{topic_name}': {e}"})

    @mcp.tool()
    def oci_kafka_update_topic_config(topic_name: str, configs: dict[str, str]) -> str:
        """Update configuration settings for a Kafka topic.

        Requires --allow-writes to be enabled.

        Args:
            topic_name: Name of the topic to update.
            configs: Dictionary of config key-value pairs to set
                     (e.g., {"retention.ms": "604800000", "cleanup.policy": "compact"}).

        Returns the update status and the configs that were changed.
        """
        params = {"topic_name": topic_name, "configs": configs}

        check = policy_guard.check("oci_kafka_update_topic_config", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})

        if not circuit_breaker.allow_request():
            return json.dumps({"error": "Circuit breaker is open. Kafka may be unavailable."})

        with audit.audit_tool("oci_kafka_update_topic_config", params) as entry:
            try:
                result = admin_client.update_topic_config(topic_name, configs)
                entry.result_status = result.get("status", "unknown")
                circuit_breaker.record_success()
                return json.dumps(result, indent=2)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps(
                    {"error": f"Failed to update config for topic '{topic_name}': {e}"}
                )

    @mcp.tool()
    def oci_kafka_delete_topic(topic_name: str) -> str:
        """Delete a Kafka topic. THIS IS A DESTRUCTIVE OPERATION.

        Requires --allow-writes to be enabled.
        This is a HIGH RISK operation that requires confirmation.

        Args:
            topic_name: Name of the topic to delete.

        Returns the deletion status.
        """
        params = {"topic_name": topic_name}

        check = policy_guard.check("oci_kafka_delete_topic", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})

        if check.needs_confirmation:
            return json.dumps(
                {
                    "status": "confirmation_required",
                    "message": f"Deleting topic '{topic_name}' is a HIGH RISK operation. "
                    "This will permanently delete the topic and all its data. "
                    "Please confirm by calling this tool again with confirmation.",
                    "risk_level": "HIGH",
                }
            )

        if not circuit_breaker.allow_request():
            return json.dumps({"error": "Circuit breaker is open. Kafka may be unavailable."})

        with audit.audit_tool("oci_kafka_delete_topic", params) as entry:
            try:
                result = admin_client.delete_topic(topic_name)
                entry.result_status = result.get("status", "unknown")
                circuit_breaker.record_success()
                return json.dumps(result, indent=2)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to delete topic '{topic_name}': {e}"})
