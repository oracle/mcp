"""OCI control plane metadata tools for OCI Kafka MCP Server.

These tools read cluster metadata from the OCI Managed Kafka API
(via KafkaClusterClient) rather than from Kafka protocol operations.
They provide information like cluster OCID, display name, lifecycle
state, Kafka version, broker shape, bootstrap URLs, and tags.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from oracle.oci_kafka_mcp_server.audit.logger import audit
from oracle.oci_kafka_mcp_server.config import OciConfig
from oracle.oci_kafka_mcp_server.oci.kafka_client import OciKafkaClient
from oracle.oci_kafka_mcp_server.tools import wrap_untrusted


def register_oci_metadata_tools(
    mcp: FastMCP,
    kafka_client: OciKafkaClient,
    oci_config: OciConfig,
) -> None:
    """Register OCI control plane metadata tools with the MCP server."""

    @mcp.tool()
    def oci_kafka_get_oci_cluster_info(cluster_id: str | None = None) -> str:
        """Get OCI control plane metadata for a Kafka cluster.

        Returns the cluster OCID, display name, lifecycle state, Kafka
        version, broker shape (node count, OCPUs, storage), bootstrap
        URLs, compartment, and tags.

        Args:
            cluster_id: OCI Kafka cluster OCID (ocid1.kafkacluster.*).
                        Defaults to OCI_CLUSTER_ID environment variable
                        if not provided.

        Use this to answer questions like "What is the cluster OCID?",
        "What is the cluster name?", or "What state is the cluster in?".

        If you don't have a cluster_id, first call oci_kafka_list_oci_clusters
        to discover available clusters and their OCIDs, or ask the user to
        provide the cluster OCID.
        """
        effective_cluster_id = cluster_id or oci_config.cluster_id
        if not effective_cluster_id:
            return json.dumps(
                {
                    "error": "No cluster_id provided. Either ask the user for the "
                    "OCI Kafka cluster OCID, or call oci_kafka_list_oci_clusters "
                    "first to discover available clusters and their OCIDs."
                }
            )

        params = {"cluster_id": effective_cluster_id}
        with audit.audit_tool("oci_kafka_get_oci_cluster_info", params) as entry:
            try:
                result = kafka_client.get_kafka_cluster(effective_cluster_id)
                if "error" in result:
                    entry.result_status = "error"
                    entry.error_message = result["error"]
                else:
                    entry.result_status = "success"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to get OCI cluster info: {e}"})

    @mcp.tool()
    def oci_kafka_list_oci_clusters(compartment_id: str | None = None) -> str:
        """List all Kafka clusters in an OCI compartment.

        Returns the count of clusters and a list with each cluster's OCID,
        display name, lifecycle state, Kafka version, broker shape, and
        creation time.

        Args:
            compartment_id: OCI compartment OCID. Defaults to
                            OCI_COMPARTMENT_ID env var, then to the tenancy
                            OCID from the OCI config file (~/.oci/config).

        Use this to discover available clusters, check their lifecycle
        states, or find a cluster OCID before calling
        oci_kafka_get_oci_cluster_info.

        If no compartment_id is provided, the tool automatically uses the
        tenancy OCID from the OCI config file as the default compartment.
        """
        effective_compartment_id = (
            compartment_id or oci_config.compartment_id or kafka_client.get_tenancy_id()
        )
        if not effective_compartment_id:
            return json.dumps(
                {
                    "error": "Could not determine the OCI compartment to search. "
                    "Please ask the user for their OCI compartment OCID and pass it "
                    "as the compartment_id parameter."
                }
            )

        params = {"compartment_id": effective_compartment_id}
        with audit.audit_tool("oci_kafka_list_oci_clusters", params) as entry:
            try:
                result = kafka_client.list_kafka_clusters(effective_compartment_id)
                if "error" in result:
                    entry.result_status = "error"
                    entry.error_message = result["error"]
                else:
                    entry.result_status = "success"
                return wrap_untrusted(result)
            except Exception as e:
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to list OCI clusters: {e}"})
