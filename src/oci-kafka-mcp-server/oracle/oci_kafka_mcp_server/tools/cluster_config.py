"""OCI Kafka cluster configuration management tools.

Manages OCI KafkaClusterConfig resources — named, versioned sets of Kafka broker
settings that can be applied to one or more clusters. Changes create new config
versions; clusters reference a config by ID + version number.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from oracle.oci_kafka_mcp_server.audit.logger import audit
from oracle.oci_kafka_mcp_server.config import OciConfig
from oracle.oci_kafka_mcp_server.oci.kafka_client import OciKafkaClient
from oracle.oci_kafka_mcp_server.security.policy_guard import PolicyGuard
from oracle.oci_kafka_mcp_server.tools import wrap_untrusted


def register_cluster_config_tools(
    mcp: FastMCP,
    kafka_client: OciKafkaClient,
    oci_config: OciConfig,
    policy_guard: PolicyGuard,
) -> None:
    """Register OCI cluster configuration tools with the MCP server."""

    @mcp.tool()
    def oci_kafka_create_cluster_config(
        display_name: str,
        compartment_id: str,
        freeform_tags: dict[str, str] | None = None,
    ) -> str:
        """Create a new OCI Kafka cluster configuration.

        Requires --allow-writes. A cluster configuration is a named, versioned
        container for Kafka broker settings. After creation, use
        oci_kafka_update_cluster to apply it to a cluster.

        Args:
            display_name: Human-readable name for the configuration.
            compartment_id: OCI compartment OCID where the config will live.
            freeform_tags: Optional free-form string key-value tags.
        """
        params = {"display_name": display_name, "compartment_id": compartment_id}
        check = policy_guard.check("oci_kafka_create_cluster_config", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_create_cluster_config", params) as entry:
            try:
                result = kafka_client.create_kafka_cluster_config(
                    display_name=display_name,
                    compartment_id=compartment_id,
                    freeform_tags=freeform_tags,
                )
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to create cluster config: {e}"})

    @mcp.tool()
    def oci_kafka_get_oci_cluster_config(cluster_config_id: str) -> str:
        """Get detailed information about an OCI Kafka cluster configuration.

        Returns the config metadata and its latest version. Use
        oci_kafka_list_cluster_config_versions to see all versions.

        Args:
            cluster_config_id: OCI cluster config OCID (ocid1.kafkaclusterconfig.*).
        """
        params = {"cluster_config_id": cluster_config_id}
        check = policy_guard.check("oci_kafka_get_oci_cluster_config", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_get_oci_cluster_config", params) as entry:
            try:
                result = kafka_client.get_kafka_cluster_config(
                    kafka_cluster_config_id=cluster_config_id
                )
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to get cluster config: {e}"})

    @mcp.tool()
    def oci_kafka_list_cluster_configs(
        compartment_id: str | None = None,
    ) -> str:
        """List OCI Kafka cluster configurations in a compartment.

        If compartment_id is not provided, falls back to the OCI_COMPARTMENT_ID
        environment variable or the tenancy OCID from ~/.oci/config.

        Args:
            compartment_id: OCI compartment OCID to search. If omitted, uses the
                tenancy OCID from the OCI config file as the default scope.
        """
        effective_compartment = (
            compartment_id or oci_config.compartment_id or kafka_client.get_tenancy_id()
        )
        if not effective_compartment:
            return json.dumps(
                {
                    "error": "Could not determine OCI compartment. "
                    "Please provide a compartment_id parameter."
                }
            )
        params = {"compartment_id": effective_compartment}
        check = policy_guard.check("oci_kafka_list_cluster_configs", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_list_cluster_configs", params) as entry:
            try:
                result = kafka_client.list_kafka_cluster_configs(
                    compartment_id=effective_compartment
                )
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to list cluster configs: {e}"})

    @mcp.tool()
    def oci_kafka_update_cluster_config(
        cluster_config_id: str,
        display_name: str | None = None,
        freeform_tags: dict[str, str] | None = None,
    ) -> str:
        """Update an OCI Kafka cluster configuration's name or tags.

        Requires --allow-writes. Updating metadata does not create a new version.
        The operation is asynchronous — use oci_kafka_get_work_request to track it.

        Args:
            cluster_config_id: OCI cluster config OCID (ocid1.kafkaclusterconfig.*).
            display_name: New display name for the configuration.
            freeform_tags: Updated free-form string key-value tags.
        """
        params = {"cluster_config_id": cluster_config_id}
        check = policy_guard.check("oci_kafka_update_cluster_config", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_update_cluster_config", params) as entry:
            try:
                result = kafka_client.update_kafka_cluster_config(
                    kafka_cluster_config_id=cluster_config_id,
                    display_name=display_name,
                    freeform_tags=freeform_tags,
                )
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to update cluster config: {e}"})

    @mcp.tool()
    def oci_kafka_delete_cluster_config(
        cluster_config_id: str,
        confirmed: bool = False,
    ) -> str:
        """Delete an OCI Kafka cluster configuration permanently.

        Requires --allow-writes. This is a HIGH RISK operation that requires
        confirmation. All versions of the configuration will be deleted.
        Clusters referencing this config should be updated before deletion.

        Args:
            cluster_config_id: OCI cluster config OCID to delete (ocid1.kafkaclusterconfig.*).
            confirmed: Must be True to execute. First call without this
                returns a confirmation prompt.
        """
        params = {"cluster_config_id": cluster_config_id}
        check = policy_guard.check("oci_kafka_delete_cluster_config", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        if check.needs_confirmation and not confirmed:
            return json.dumps(
                {
                    "status": "confirmation_required",
                    "message": f"Deleting cluster config '{cluster_config_id}' is IRREVERSIBLE. "
                    "All config versions will be permanently deleted. "
                    "Call again with confirmed=True to proceed.",
                    "risk_level": "HIGH",
                }
            )
        with audit.audit_tool("oci_kafka_delete_cluster_config", params) as entry:
            try:
                result = kafka_client.delete_kafka_cluster_config(
                    kafka_cluster_config_id=cluster_config_id
                )
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to delete cluster config: {e}"})

    @mcp.tool()
    def oci_kafka_change_cluster_config_compartment(
        cluster_config_id: str,
        target_compartment_id: str,
    ) -> str:
        """Move an OCI Kafka cluster configuration to a different compartment.

        Requires --allow-writes. Moving a config changes which IAM policies and
        users can access it.

        Args:
            cluster_config_id: OCI cluster config OCID to move.
            target_compartment_id: Target OCI compartment OCID.
        """
        params = {
            "cluster_config_id": cluster_config_id,
            "target_compartment_id": target_compartment_id,
        }
        check = policy_guard.check("oci_kafka_change_cluster_config_compartment", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_change_cluster_config_compartment", params) as entry:
            try:
                result = kafka_client.change_kafka_cluster_config_compartment(
                    kafka_cluster_config_id=cluster_config_id,
                    compartment_id=target_compartment_id,
                )
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to change config compartment: {e}"})

    @mcp.tool()
    def oci_kafka_get_cluster_config_version(
        cluster_config_id: str,
        version_number: int,
    ) -> str:
        """Get a specific version of an OCI Kafka cluster configuration.

        Args:
            cluster_config_id: OCI cluster config OCID (ocid1.kafkaclusterconfig.*).
            version_number: The integer version number to retrieve.
        """
        params = {"cluster_config_id": cluster_config_id, "version_number": version_number}
        check = policy_guard.check("oci_kafka_get_cluster_config_version", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_get_cluster_config_version", params) as entry:
            try:
                result = kafka_client.get_kafka_cluster_config_version(
                    kafka_cluster_config_id=cluster_config_id,
                    version_number=version_number,
                )
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to get config version: {e}"})

    @mcp.tool()
    def oci_kafka_list_cluster_config_versions(cluster_config_id: str) -> str:
        """List all versions of an OCI Kafka cluster configuration.

        Configurations are versioned — each update creates a new version.
        Use this to see the version history and identify which version to apply
        or roll back to.

        Args:
            cluster_config_id: OCI cluster config OCID (ocid1.kafkaclusterconfig.*).
        """
        params = {"cluster_config_id": cluster_config_id}
        check = policy_guard.check("oci_kafka_list_cluster_config_versions", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_list_cluster_config_versions", params) as entry:
            try:
                result = kafka_client.list_kafka_cluster_config_versions(
                    kafka_cluster_config_id=cluster_config_id
                )
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to list config versions: {e}"})

    @mcp.tool()
    def oci_kafka_delete_cluster_config_version(
        cluster_config_id: str,
        version_number: int,
    ) -> str:
        """Delete a specific version of an OCI Kafka cluster configuration.

        Requires --allow-writes. Deleting a version is irreversible. Do not delete
        a version that is currently applied to a cluster.

        Args:
            cluster_config_id: OCI cluster config OCID (ocid1.kafkaclusterconfig.*).
            version_number: The integer version number to delete.
        """
        params = {"cluster_config_id": cluster_config_id, "version_number": version_number}
        check = policy_guard.check("oci_kafka_delete_cluster_config_version", params)
        if not check.allowed:
            return json.dumps({"error": check.reason})
        with audit.audit_tool("oci_kafka_delete_cluster_config_version", params) as entry:
            try:
                result = kafka_client.delete_kafka_cluster_config_version(
                    kafka_cluster_config_id=cluster_config_id,
                    version_number=version_number,
                )
                entry.result_status = "success" if "error" not in result else "error"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to delete config version: {e}"})
