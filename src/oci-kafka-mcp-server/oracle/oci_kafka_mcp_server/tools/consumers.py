"""Consumer operations tools for OCI Kafka MCP Server."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from oracle.oci_kafka_mcp_server.audit.logger import audit
from oracle.oci_kafka_mcp_server.kafka.connection import CircuitBreaker
from oracle.oci_kafka_mcp_server.kafka.consumer_client import KafkaConsumerClient
from oracle.oci_kafka_mcp_server.security.policy_guard import PolicyGuard
from oracle.oci_kafka_mcp_server.tools import wrap_untrusted

CIRCUIT_OPEN_MSG = "Circuit breaker is open. Kafka may be unavailable."


def _check_write_preconditions(
    tool_name: str,
    params: dict[str, Any],
    policy_guard: PolicyGuard,
    circuit_breaker: CircuitBreaker,
    confirmation_message: str,
    confirmed: bool = False,
) -> str | None:
    """Check policy guard and circuit breaker before a write operation.

    Returns a JSON error string if blocked, or None if execution should proceed.
    """
    check = policy_guard.check(tool_name, params)
    if not check.allowed:
        return json.dumps({"error": check.reason})

    if check.needs_confirmation and not confirmed:
        return json.dumps(
            {
                "status": "confirmation_required",
                "message": confirmation_message + " Call again with confirmed=True to proceed.",
                "risk_level": "HIGH",
            }
        )

    if not circuit_breaker.allow_request():
        return json.dumps({"error": CIRCUIT_OPEN_MSG})

    return None


def register_consumer_tools(
    mcp: FastMCP,
    consumer_client: KafkaConsumerClient,
    policy_guard: PolicyGuard,
    circuit_breaker: CircuitBreaker,
) -> None:
    """Register consumer operation tools with the MCP server."""
    _register_consumer_read_tools(mcp, consumer_client, circuit_breaker)
    _register_consumer_write_tools(mcp, consumer_client, policy_guard, circuit_breaker)


def _register_consumer_read_tools(
    mcp: FastMCP,
    consumer_client: KafkaConsumerClient,
    circuit_breaker: CircuitBreaker,
) -> None:
    """Register read-only consumer tools."""

    @mcp.tool()
    def oci_kafka_list_consumer_groups() -> str:
        """List all consumer groups in the Kafka cluster.

        Returns the total group count and a list of consumer groups
        with their state and type information.
        """
        if not circuit_breaker.allow_request():
            return json.dumps({"error": CIRCUIT_OPEN_MSG})

        with audit.audit_tool("oci_kafka_list_consumer_groups", {}) as entry:
            try:
                result = consumer_client.list_consumer_groups()
                entry.result_status = "success"
                circuit_breaker.record_success()
                return wrap_untrusted(result)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to list consumer groups: {e}"})

    @mcp.tool()
    def oci_kafka_describe_consumer_group(group_id: str) -> str:
        """Get detailed information about a consumer group.

        Args:
            group_id: The consumer group ID to describe.

        Returns the group state, coordinator, partition assignor, and
        member details including their topic-partition assignments.
        """
        if not circuit_breaker.allow_request():
            return json.dumps({"error": CIRCUIT_OPEN_MSG})

        params = {"group_id": group_id}
        with audit.audit_tool("oci_kafka_describe_consumer_group", params) as entry:
            try:
                result = consumer_client.describe_consumer_group(group_id)
                entry.result_status = "success"
                circuit_breaker.record_success()
                return wrap_untrusted(result)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to describe consumer group '{group_id}': {e}"})

    @mcp.tool()
    def oci_kafka_get_consumer_lag(group_id: str) -> str:
        """Get consumer lag for a consumer group across all assigned partitions.

        Args:
            group_id: The consumer group ID to check lag for.

        Returns total lag, and per-partition details including committed offset,
        end offset, and lag. Use this to diagnose slow consumers or processing bottlenecks.
        """
        if not circuit_breaker.allow_request():
            return json.dumps({"error": CIRCUIT_OPEN_MSG})

        params = {"group_id": group_id}
        with audit.audit_tool("oci_kafka_get_consumer_lag", params) as entry:
            try:
                result = consumer_client.get_consumer_lag(group_id)
                entry.result_status = "success"
                circuit_breaker.record_success()
                return wrap_untrusted(result)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps(
                    {"error": f"Failed to get consumer lag for group '{group_id}': {e}"}
                )


def _register_consumer_write_tools(
    mcp: FastMCP,
    consumer_client: KafkaConsumerClient,
    policy_guard: PolicyGuard,
    circuit_breaker: CircuitBreaker,
) -> None:
    """Register consumer write tools (require --allow-writes)."""

    @mcp.tool()
    def oci_kafka_reset_consumer_offset(
        group_id: str,
        topic_name: str,
        strategy: str = "latest",
        partition: int | None = None,
        confirmed: bool = False,
    ) -> str:
        """Reset consumer group offsets for a topic. THIS IS A DESTRUCTIVE OPERATION.

        The consumer group must have no active members (EMPTY state).
        Requires --allow-writes to be enabled.
        This is a HIGH RISK operation that requires confirmation.

        Args:
            group_id: The consumer group ID to reset offsets for.
            topic_name: The topic to reset offsets for.
            strategy: Reset strategy — 'earliest' (beginning), 'latest' (end),
                      or a specific integer offset.
            partition: Optional specific partition number. If omitted, resets all partitions.
            confirmed: Must be True to execute. First call without this
                returns a confirmation prompt.

        Returns the reset status and new offset positions for each partition.
        """
        params = {
            "group_id": group_id,
            "topic_name": topic_name,
            "strategy": strategy,
            "partition": partition,
        }

        blocked = _check_write_preconditions(
            "oci_kafka_reset_consumer_offset",
            params,
            policy_guard,
            circuit_breaker,
            f"Resetting offsets for group '{group_id}' on topic '{topic_name}' "
            f"to '{strategy}' is a HIGH RISK operation. This will change the "
            "consumer's position and may cause messages to be reprocessed or skipped.",
            confirmed=confirmed,
        )
        if blocked:
            return blocked

        with audit.audit_tool("oci_kafka_reset_consumer_offset", params) as entry:
            try:
                result = consumer_client.reset_consumer_offset(
                    group_id, topic_name, strategy, partition
                )
                entry.result_status = result.get("status", "unknown")
                circuit_breaker.record_success()
                return wrap_untrusted(result)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to reset offsets for group '{group_id}': {e}"})

    @mcp.tool()
    def oci_kafka_delete_consumer_group(
        group_id: str,
        confirmed: bool = False,
    ) -> str:
        """Delete a consumer group. THIS IS A DESTRUCTIVE OPERATION.

        The consumer group must have no active members (EMPTY state).
        Requires --allow-writes to be enabled.
        This is a HIGH RISK operation that requires confirmation.

        Args:
            group_id: The consumer group ID to delete.
            confirmed: Must be True to execute. First call without this
                returns a confirmation prompt.

        Returns the deletion status.
        """
        params = {"group_id": group_id}

        blocked = _check_write_preconditions(
            "oci_kafka_delete_consumer_group",
            params,
            policy_guard,
            circuit_breaker,
            f"Deleting consumer group '{group_id}' is a HIGH RISK operation. "
            "This will permanently remove the group and all committed offsets.",
            confirmed=confirmed,
        )
        if blocked:
            return blocked

        with audit.audit_tool("oci_kafka_delete_consumer_group", params) as entry:
            try:
                result = consumer_client.delete_consumer_group(group_id)
                entry.result_status = result.get("status", "unknown")
                circuit_breaker.record_success()
                return wrap_untrusted(result)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to delete consumer group '{group_id}': {e}"})
