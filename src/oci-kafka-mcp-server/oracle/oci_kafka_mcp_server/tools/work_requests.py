"""OCI work request and node shape tools for OCI Kafka MCP Server.

Work requests track asynchronous OCI control plane operations (create cluster,
delete cluster, enable superuser, etc.). Most OCI Kafka operations return a
work request OCID — use oci_kafka_get_work_request to poll for completion.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from oracle.oci_kafka_mcp_server.audit.logger import audit
from oracle.oci_kafka_mcp_server.config import OciConfig
from oracle.oci_kafka_mcp_server.oci.kafka_client import OciKafkaClient
from oracle.oci_kafka_mcp_server.security.policy_guard import PolicyGuard
from oracle.oci_kafka_mcp_server.tools import wrap_untrusted


def register_work_request_tools(
    mcp: FastMCP,
    kafka_client: OciKafkaClient,
    oci_config: OciConfig,
    policy_guard: PolicyGuard,
) -> None:
    """Register OCI work request and node shape tools with the MCP server."""

    @mcp.tool()
    def oci_kafka_get_work_request(work_request_id: str) -> str:
        """Get the status and details of an asynchronous OCI work request.

        Use this after any async operation (create/update/delete cluster,
        enable superuser, etc.) to track progress. Poll until status is
        SUCCEEDED or FAILED.

        Args:
            work_request_id: Work request OCID returned by the triggering operation.
        """
        params = {"work_request_id": work_request_id}
        check = policy_guard.check("oci_kafka_get_work_request", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_get_work_request", params) as entry:
            try:
                result = kafka_client.get_work_request(work_request_id=work_request_id)
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to get work request: {e}"})

    @mcp.tool()
    def oci_kafka_list_work_requests(
        compartment_id: str | None = None,
        resource_id: str | None = None,
    ) -> str:
        """List OCI work requests, optionally filtered by compartment or resource.

        Use resource_id to find all operations on a specific cluster or config.
        If neither filter is provided, uses the tenancy OCID from ~/.oci/config.

        Args:
            compartment_id: OCI compartment OCID to filter work requests.
            resource_id: OCI resource OCID to find operations affecting that resource
                (e.g., a cluster OCID to see all work requests for that cluster).
        """
        effective_compartment = (
            compartment_id or oci_config.compartment_id or kafka_client.get_tenancy_id()
        )
        params = {
            "compartment_id": effective_compartment,
            "resource_id": resource_id,
        }
        check = policy_guard.check("oci_kafka_list_work_requests", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_list_work_requests", params) as entry:
            try:
                result = kafka_client.list_work_requests(
                    compartment_id=effective_compartment,
                    resource_id=resource_id,
                )
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to list work requests: {e}"})

    @mcp.tool()
    def oci_kafka_cancel_work_request(work_request_id: str) -> str:
        """Cancel an in-progress OCI work request.

        Requires --allow-writes. Only in-progress requests can be cancelled.
        Already-completed or failed requests cannot be cancelled.

        Args:
            work_request_id: Work request OCID to cancel.
        """
        params = {"work_request_id": work_request_id}
        check = policy_guard.check("oci_kafka_cancel_work_request", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_cancel_work_request", params) as entry:
            try:
                result = kafka_client.cancel_work_request(work_request_id=work_request_id)
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to cancel work request: {e}"})

    @mcp.tool()
    def oci_kafka_get_work_request_errors(work_request_id: str) -> str:
        """Get error details from a failed OCI work request.

        Call this when oci_kafka_get_work_request shows status FAILED to
        get the specific error codes and messages explaining the failure.

        Args:
            work_request_id: Work request OCID that failed.
        """
        params = {"work_request_id": work_request_id}
        check = policy_guard.check("oci_kafka_get_work_request_errors", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_get_work_request_errors", params) as entry:
            try:
                result = kafka_client.get_work_request_errors(work_request_id=work_request_id)
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to get work request errors: {e}"})

    @mcp.tool()
    def oci_kafka_get_work_request_logs(work_request_id: str) -> str:
        """Get log entries from an OCI work request.

        Returns timestamped log messages from the work request execution.
        Useful for understanding the sequence of steps in a long-running operation.

        Args:
            work_request_id: Work request OCID to retrieve logs for.
        """
        params = {"work_request_id": work_request_id}
        check = policy_guard.check("oci_kafka_get_work_request_logs", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_get_work_request_logs", params) as entry:
            try:
                result = kafka_client.get_work_request_logs(work_request_id=work_request_id)
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to get work request logs: {e}"})

    @mcp.tool()
    def oci_kafka_list_node_shapes(
        compartment_id: str | None = None,
    ) -> str:
        """List available broker node shapes for OCI Kafka cluster provisioning.

        Returns available shapes with their OCPU and memory specs. Use this
        before oci_kafka_create_cluster to choose an appropriate broker shape.

        Args:
            compartment_id: Optional OCI compartment OCID to scope the shape list.
        """
        effective_compartment = (
            compartment_id or oci_config.compartment_id or kafka_client.get_tenancy_id()
        )
        params = {"compartment_id": effective_compartment}
        check = policy_guard.check("oci_kafka_list_node_shapes", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_list_node_shapes", params) as entry:
            try:
                result = kafka_client.list_node_shapes(compartment_id=effective_compartment)
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to list node shapes: {e}"})
