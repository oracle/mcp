"""Cluster operations tools for OCI Kafka MCP Server."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from oracle.oci_kafka_mcp_server.audit.logger import audit
from oracle.oci_kafka_mcp_server.kafka.admin_client import KafkaAdminClient
from oracle.oci_kafka_mcp_server.kafka.connection import CircuitBreaker
from oracle.oci_kafka_mcp_server.security.policy_guard import PolicyGuard
from oracle.oci_kafka_mcp_server.tools import wrap_untrusted


def register_cluster_tools(
    mcp: FastMCP,
    admin_client: KafkaAdminClient,
    policy_guard: PolicyGuard,
    circuit_breaker: CircuitBreaker,
) -> None:
    """Register cluster operation tools with the MCP server."""

    @mcp.tool()
    def oci_kafka_get_cluster_health() -> str:
        """Get Kafka cluster health status including broker list, controller info, and topic count.

        Returns cluster ID, controller ID, broker count and details, and total topic count.
        Use this to verify cluster connectivity and check overall cluster health.
        """
        if not circuit_breaker.allow_request():
            return json.dumps({"error": "Circuit breaker is open. Kafka may be unavailable."})

        with audit.audit_tool("oci_kafka_get_cluster_health", {}) as entry:
            try:
                result = admin_client.get_cluster_health()
                entry.result_status = "success"
                circuit_breaker.record_success()
                return wrap_untrusted(result)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to get cluster health: {e}"})

    @mcp.tool()
    def oci_kafka_get_cluster_config() -> str:
        """Get Kafka cluster configuration settings.

        Returns broker-level configuration including log settings, replication defaults,
        and other cluster parameters. Use this to inspect current cluster settings.
        """
        if not circuit_breaker.allow_request():
            return json.dumps({"error": "Circuit breaker is open. Kafka may be unavailable."})

        with audit.audit_tool("oci_kafka_get_cluster_config", {}) as entry:
            try:
                result = admin_client.get_cluster_config()
                entry.result_status = "success"
                circuit_breaker.record_success()
                return wrap_untrusted(result)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to get cluster config: {e}"})
