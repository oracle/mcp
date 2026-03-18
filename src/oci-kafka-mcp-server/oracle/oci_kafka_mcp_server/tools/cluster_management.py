"""Cluster lifecycle management tools for OCI Kafka MCP Server.

These tools use the OCI control plane API (oci.managed_kafka) to manage
Kafka cluster lifecycle: create, update, delete, scale, move compartment,
and manage superusers. They require OCI SDK configuration (~/.oci/config).
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from oracle.oci_kafka_mcp_server.audit.logger import audit
from oracle.oci_kafka_mcp_server.config import OciConfig
from oracle.oci_kafka_mcp_server.oci.kafka_client import OciKafkaClient
from oracle.oci_kafka_mcp_server.security.policy_guard import PolicyGuard


def register_cluster_management_tools(
    mcp: FastMCP,
    kafka_client: OciKafkaClient,
    oci_config: OciConfig,
    policy_guard: PolicyGuard,
) -> None:
    """Register OCI cluster lifecycle tools with the MCP server."""

    @mcp.tool()
    def oci_kafka_create_cluster(
        display_name: str,
        compartment_id: str,
        subnet_id: str,
        broker_count: int = 3,
        kafka_version: str = "3.6.0",
        cluster_type: str = "PRODUCTION",
        ocpu_count: int = 2,
        storage_size_in_gbs: int = 50,
        cluster_config_id: str | None = None,
    ) -> str:
        """Create a new OCI Streaming with Apache Kafka cluster.

        Requires --allow-writes. This is a HIGH RISK operation that requires confirmation.
        The operation is asynchronous — use oci_kafka_get_work_request to track progress.

        Args:
            display_name: Human-readable name for the cluster.
            compartment_id: OCI compartment OCID where the cluster will be created.
            subnet_id: OCI subnet OCID for the cluster's private network.
            broker_count: Number of broker nodes (default: 3).
            kafka_version: Kafka version to deploy (default: 3.6.0).
            cluster_type: PRODUCTION or DEVELOPMENT (default: PRODUCTION).
            ocpu_count: OCPUs per broker node (default: 2).
            storage_size_in_gbs: Storage per broker in GB (default: 50).
            cluster_config_id: Optional OCID of a cluster configuration to apply.
        """
        params = {
            "display_name": display_name,
            "compartment_id": compartment_id,
            "subnet_id": subnet_id,
            "broker_count": broker_count,
        }
        check = policy_guard.check("oci_kafka_create_cluster", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        if check.needs_confirmation:
            return json.dumps(
                {
                    "status": "confirmation_required",
                    "message": f"Creating cluster '{display_name}' with {broker_count} brokers "
                    "will provision new OCI infrastructure and incur costs. Confirm to proceed.",
                    "risk_level": "HIGH",
                }
            )
        with audit.audit_tool("oci_kafka_create_cluster", params) as entry:
            try:
                result = kafka_client.create_kafka_cluster(
                    display_name=display_name,
                    compartment_id=compartment_id,
                    subnet_id=subnet_id,
                    broker_count=broker_count,
                    kafka_version=kafka_version,
                    cluster_type=cluster_type,
                    ocpu_count=ocpu_count,
                    storage_size_in_gbs=storage_size_in_gbs,
                    cluster_config_id=cluster_config_id,
                )
                entry.result_status = "success" if "error" not in result else "error"
                return json.dumps(result, indent=2)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to create cluster: {e}"})

    @mcp.tool()
    def oci_kafka_update_cluster(
        cluster_id: str,
        display_name: str | None = None,
        cluster_config_id: str | None = None,
        cluster_config_version: int | None = None,
        freeform_tags: dict[str, str] | None = None,
    ) -> str:
        """Update an OCI Kafka cluster's display name, tags, or applied configuration.

        Requires --allow-writes. The operation is asynchronous — use
        oci_kafka_get_work_request to track progress.

        Args:
            cluster_id: OCI Kafka cluster OCID (ocid1.kafkacluster.*).
            display_name: New display name for the cluster.
            cluster_config_id: OCID of the cluster configuration to apply.
            cluster_config_version: Specific version number of the config to apply.
            freeform_tags: Free-form tags as a dict of string key-value pairs.
        """
        params = {"cluster_id": cluster_id}
        check = policy_guard.check("oci_kafka_update_cluster", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_update_cluster", params) as entry:
            try:
                result = kafka_client.update_kafka_cluster(
                    kafka_cluster_id=cluster_id,
                    display_name=display_name,
                    cluster_config_id=cluster_config_id,
                    cluster_config_version=cluster_config_version,
                    freeform_tags=freeform_tags,
                )
                entry.result_status = "success" if "error" not in result else "error"
                return json.dumps(result, indent=2)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to update cluster: {e}"})

    @mcp.tool()
    def oci_kafka_scale_cluster(
        cluster_id: str,
        broker_count: int,
    ) -> str:
        """Scale an OCI Kafka cluster to a different broker count.

        Requires --allow-writes. This is a HIGH RISK operation that requires confirmation.
        The operation is asynchronous — use oci_kafka_get_work_request to track progress.

        Args:
            cluster_id: OCI Kafka cluster OCID to scale.
            broker_count: Target number of broker nodes.
        """
        params = {"cluster_id": cluster_id, "broker_count": broker_count}
        check = policy_guard.check("oci_kafka_scale_cluster", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        if check.needs_confirmation:
            return json.dumps(
                {
                    "status": "confirmation_required",
                    "message": f"Scaling cluster to {broker_count} brokers will modify live "
                    "infrastructure and may cause temporary partition rebalancing. "
                    "Confirm to proceed.",
                    "risk_level": "HIGH",
                }
            )
        with audit.audit_tool("oci_kafka_scale_cluster", params) as entry:
            try:
                # Scaling is done via update with a new BrokerShape node_count.
                # We fetch the current shape first to preserve ocpu/storage settings.
                current = kafka_client.get_kafka_cluster(kafka_cluster_id=cluster_id)
                if "error" in current:
                    entry.result_status = "error"
                    return json.dumps(current, indent=2)
                from oci.managed_kafka.models import BrokerShape, UpdateKafkaClusterDetails

                shape = current.get("broker_shape", {})
                new_shape = BrokerShape(
                    node_count=broker_count,
                    ocpu_count=shape.get("ocpu_count", 2),
                    storage_size_in_gbs=shape.get("storage_size_in_gbs", 50),
                )
                oci_client = kafka_client._get_client()
                if oci_client is None:
                    entry.result_status = "error"
                    return json.dumps({"error": "OCI SDK not configured"})
                response = oci_client.update_kafka_cluster(
                    kafka_cluster_id=cluster_id,
                    update_kafka_cluster_details=UpdateKafkaClusterDetails(broker_shape=new_shape),
                )
                from oracle.oci_kafka_mcp_server.oci.kafka_client import _serialize_work_request

                result = _serialize_work_request(response.data)
                entry.result_status = "success"
                return json.dumps(result, indent=2)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to scale cluster: {e}"})

    @mcp.tool()
    def oci_kafka_delete_cluster(cluster_id: str) -> str:
        """Delete an OCI Kafka cluster permanently.

        Requires --allow-writes. This is a HIGH RISK operation that requires confirmation.
        The operation is asynchronous — use oci_kafka_get_work_request to track progress.
        ALL DATA ON THE CLUSTER WILL BE PERMANENTLY LOST.

        Args:
            cluster_id: OCI Kafka cluster OCID to delete (ocid1.kafkacluster.*).
        """
        params = {"cluster_id": cluster_id}
        check = policy_guard.check("oci_kafka_delete_cluster", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        if check.needs_confirmation:
            return json.dumps(
                {
                    "status": "confirmation_required",
                    "message": f"Deleting cluster '{cluster_id}' is IRREVERSIBLE. "
                    "All topics and data will be permanently lost. Confirm to proceed.",
                    "risk_level": "HIGH",
                }
            )
        with audit.audit_tool("oci_kafka_delete_cluster", params) as entry:
            try:
                result = kafka_client.delete_kafka_cluster(kafka_cluster_id=cluster_id)
                entry.result_status = "success" if "error" not in result else "error"
                return json.dumps(result, indent=2)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to delete cluster: {e}"})

    @mcp.tool()
    def oci_kafka_change_cluster_compartment(
        cluster_id: str,
        target_compartment_id: str,
    ) -> str:
        """Move an OCI Kafka cluster to a different OCI compartment.

        Requires --allow-writes. This is a HIGH RISK operation that requires confirmation.
        Moving a cluster changes which IAM policies and users can access it.

        Args:
            cluster_id: OCI Kafka cluster OCID to move.
            target_compartment_id: Target OCI compartment OCID.
        """
        params = {"cluster_id": cluster_id, "target_compartment_id": target_compartment_id}
        check = policy_guard.check("oci_kafka_change_cluster_compartment", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        if check.needs_confirmation:
            return json.dumps(
                {
                    "status": "confirmation_required",
                    "message": f"Moving cluster to compartment '{target_compartment_id}' "
                    "will change which IAM policies control access. Confirm to proceed.",
                    "risk_level": "HIGH",
                }
            )
        with audit.audit_tool("oci_kafka_change_cluster_compartment", params) as entry:
            try:
                result = kafka_client.change_kafka_cluster_compartment(
                    kafka_cluster_id=cluster_id,
                    compartment_id=target_compartment_id,
                )
                entry.result_status = "success" if "error" not in result else "error"
                return json.dumps(result, indent=2)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to change compartment: {e}"})

    @mcp.tool()
    def oci_kafka_enable_superuser(
        cluster_id: str,
        duration_in_hours: int | None = None,
    ) -> str:
        """Enable the superuser for an OCI Kafka cluster.

        Requires --allow-writes. The superuser has full administrative access
        to all Kafka resources. Use sparingly and with a time limit.

        Args:
            cluster_id: OCI Kafka cluster OCID.
            duration_in_hours: Optional duration (hours) to keep superuser enabled.
                If not set, superuser stays enabled until explicitly disabled.
        """
        params = {"cluster_id": cluster_id, "duration_in_hours": duration_in_hours}
        check = policy_guard.check("oci_kafka_enable_superuser", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_enable_superuser", params) as entry:
            try:
                result = kafka_client.enable_superuser(
                    kafka_cluster_id=cluster_id,
                    duration_in_hours=duration_in_hours,
                )
                entry.result_status = "success" if "error" not in result else "error"
                return json.dumps(result, indent=2)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to enable superuser: {e}"})

    @mcp.tool()
    def oci_kafka_disable_superuser(cluster_id: str) -> str:
        """Disable the superuser for an OCI Kafka cluster.

        Requires --allow-writes. Use this after completing administrative
        tasks to restore least-privilege access.

        Args:
            cluster_id: OCI Kafka cluster OCID.
        """
        params = {"cluster_id": cluster_id}
        check = policy_guard.check("oci_kafka_disable_superuser", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_disable_superuser", params) as entry:
            try:
                result = kafka_client.disable_superuser(kafka_cluster_id=cluster_id)
                entry.result_status = "success" if "error" not in result else "error"
                return json.dumps(result, indent=2)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to disable superuser: {e}"})
