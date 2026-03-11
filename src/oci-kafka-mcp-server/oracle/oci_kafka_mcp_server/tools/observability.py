"""Observability and diagnostics tools for OCI Kafka MCP Server."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from oracle.oci_kafka_mcp_server.audit.logger import audit
from oracle.oci_kafka_mcp_server.kafka.admin_client import KafkaAdminClient
from oracle.oci_kafka_mcp_server.kafka.connection import CircuitBreaker


def register_observability_tools(
    mcp: FastMCP,
    admin_client: KafkaAdminClient,
    circuit_breaker: CircuitBreaker,
) -> None:
    """Register observability and diagnostics tools with the MCP server."""

    @mcp.tool()
    def oci_kafka_get_partition_skew(topic_name: str | None = None) -> str:
        """Detect partition imbalance across brokers.

        Checks if partitions are evenly distributed across brokers (as leaders).
        A skew ratio > 1.5 indicates significant imbalance that may cause
        performance degradation.

        Args:
            topic_name: Optional topic to check. If not provided, checks all topics.

        Returns skew ratio, per-broker partition counts, and a recommendation.
        """
        if not circuit_breaker.allow_request():
            return json.dumps({"error": "Circuit breaker is open. Kafka may be unavailable."})

        params = {"topic_name": topic_name}
        with audit.audit_tool("oci_kafka_get_partition_skew", params) as entry:
            try:
                result = admin_client.get_partition_skew(topic_name)
                entry.result_status = "success"
                circuit_breaker.record_success()
                return json.dumps(result, indent=2)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to check partition skew: {e}"})

    @mcp.tool()
    def oci_kafka_detect_under_replicated_partitions() -> str:
        """Detect partitions where the in-sync replica (ISR) count is less than the replica count.

        Under-replicated partitions indicate potential data durability risks.
        This can be caused by broker failures, network issues, or disk problems.

        Returns the total partition count, under-replicated count, and details
        of each affected partition including which replicas are missing from ISR.
        """
        if not circuit_breaker.allow_request():
            return json.dumps({"error": "Circuit breaker is open. Kafka may be unavailable."})

        with audit.audit_tool("oci_kafka_detect_under_replicated_partitions", {}) as entry:
            try:
                result = admin_client.detect_under_replicated_partitions()
                entry.result_status = "success"
                circuit_breaker.record_success()
                return json.dumps(result, indent=2)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to detect under-replicated partitions: {e}"})
