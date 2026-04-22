"""Tests for OCI control plane metadata tools."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from oracle.oci_kafka_mcp_server.config import OciConfig
from oracle.oci_kafka_mcp_server.oci.kafka_client import OciKafkaClient
from oracle.oci_kafka_mcp_server.tools.oci_metadata import register_oci_metadata_tools


def _make_tool_functions(
    kafka_client: OciKafkaClient | MagicMock,
    oci_config: OciConfig | None = None,
) -> dict[str, object]:
    """Register tools and return a dict of tool name -> callable."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("test")
    config = oci_config or OciConfig()
    register_oci_metadata_tools(mcp, kafka_client, config)  # type: ignore[arg-type]

    # Extract registered tool functions by name
    tools = {}
    for name, tool in mcp._tool_manager._tools.items():
        tools[name] = tool.fn
    return tools


class TestGetOciClusterInfo:
    """Test the oci_kafka_get_oci_cluster_info tool."""

    def test_returns_cluster_metadata(self) -> None:
        """Should return Kafka cluster details when cluster_id is provided."""
        client = MagicMock(spec=OciKafkaClient)
        client.get_kafka_cluster.return_value = {
            "id": "ocid1.kafkacluster.oc1.us-chicago-1.aaaaaa",
            "display_name": "my-kafka-cluster",
            "compartment_id": "ocid1.compartment.oc1..aaaaaa",
            "lifecycle_state": "ACTIVE",
            "kafka_version": "3.7.0",
            "cluster_type": "PRODUCTION",
            "coordination_type": "ZOOKEEPER",
            "time_created": "2026-01-15T10:00:00Z",
            "time_updated": "2026-01-15T12:00:00Z",
            "broker_shape": {
                "node_count": 3,
                "ocpu_count": 2,
                "storage_size_in_gbs": 50,
            },
            "bootstrap_urls": [
                {
                    "name": "bootstrap",
                    "url": "bootstrap-clstr-xxx.kafka.us-chicago-1.oci.oraclecloud.com:9092",
                }
            ],
        }

        tools = _make_tool_functions(client)
        result = json.loads(
            tools["oci_kafka_get_oci_cluster_info"](
                cluster_id="ocid1.kafkacluster.oc1.us-chicago-1.aaaaaa"
            )
        )

        assert result["id"] == "ocid1.kafkacluster.oc1.us-chicago-1.aaaaaa"
        assert result["display_name"] == "my-kafka-cluster"
        assert result["lifecycle_state"] == "ACTIVE"
        assert result["kafka_version"] == "3.7.0"
        assert result["broker_shape"]["node_count"] == 3
        assert result["bootstrap_urls"][0]["url"].endswith(":9092")
        client.get_kafka_cluster.assert_called_once_with(
            "ocid1.kafkacluster.oc1.us-chicago-1.aaaaaa"
        )

    def test_uses_config_default_cluster_id(self) -> None:
        """Should fall back to OCI_CLUSTER_ID config when no parameter given."""
        client = MagicMock(spec=OciKafkaClient)
        client.get_kafka_cluster.return_value = {
            "id": "ocid1.kafkacluster.oc1.us-chicago-1.default",
            "display_name": "default-cluster",
            "lifecycle_state": "ACTIVE",
        }

        config = OciConfig(cluster_id="ocid1.kafkacluster.oc1.us-chicago-1.default")
        tools = _make_tool_functions(client, config)
        result = json.loads(tools["oci_kafka_get_oci_cluster_info"](cluster_id=None))

        assert result["display_name"] == "default-cluster"
        client.get_kafka_cluster.assert_called_once_with(
            "ocid1.kafkacluster.oc1.us-chicago-1.default"
        )

    def test_error_when_no_cluster_id(self) -> None:
        """Should return error guiding LLM to discover or ask user."""
        client = MagicMock(spec=OciKafkaClient)
        config = OciConfig(cluster_id=None)
        tools = _make_tool_functions(client, config)

        result = json.loads(tools["oci_kafka_get_oci_cluster_info"](cluster_id=None))

        assert "error" in result
        assert "oci_kafka_list_oci_clusters" in result["error"]
        assert "ask the user" in result["error"]
        client.get_kafka_cluster.assert_not_called()

    def test_handles_oci_sdk_not_configured(self) -> None:
        """Should propagate error when OCI SDK is not available."""
        client = MagicMock(spec=OciKafkaClient)
        client.get_kafka_cluster.return_value = {
            "error": "OCI SDK not configured",
        }

        tools = _make_tool_functions(client)
        result = json.loads(
            tools["oci_kafka_get_oci_cluster_info"](
                cluster_id="ocid1.kafkacluster.oc1.us-chicago-1.aaaaaa"
            )
        )

        assert result["error"] == "OCI SDK not configured"

    def test_handles_api_exception(self) -> None:
        """Should return error when OCI API call raises an exception."""
        client = MagicMock(spec=OciKafkaClient)
        client.get_kafka_cluster.side_effect = Exception("Service unavailable")

        tools = _make_tool_functions(client)
        result = json.loads(
            tools["oci_kafka_get_oci_cluster_info"](
                cluster_id="ocid1.kafkacluster.oc1.us-chicago-1.aaaaaa"
            )
        )

        assert "error" in result
        assert "Service unavailable" in result["error"]


class TestListOciClusters:
    """Test the oci_kafka_list_oci_clusters tool."""

    def test_returns_cluster_list(self) -> None:
        """Should return list of Kafka clusters in compartment."""
        client = MagicMock(spec=OciKafkaClient)
        client.list_kafka_clusters.return_value = {
            "cluster_count": 2,
            "clusters": [
                {
                    "id": "ocid1.kafkacluster.oc1.us-chicago-1.aaaa1",
                    "display_name": "prod-kafka",
                    "lifecycle_state": "ACTIVE",
                    "compartment_id": "ocid1.compartment.oc1..aaaaaa",
                    "kafka_version": "3.7.0",
                    "cluster_type": "PRODUCTION",
                    "time_created": "2026-01-15T10:00:00Z",
                    "broker_shape": {
                        "node_count": 3,
                        "ocpu_count": 2,
                        "storage_size_in_gbs": 50,
                    },
                },
                {
                    "id": "ocid1.kafkacluster.oc1.us-chicago-1.aaaa2",
                    "display_name": "dev-kafka",
                    "lifecycle_state": "ACTIVE",
                    "compartment_id": "ocid1.compartment.oc1..aaaaaa",
                    "kafka_version": "3.7.0",
                    "cluster_type": "PRODUCTION",
                    "time_created": "2026-02-01T10:00:00Z",
                    "broker_shape": {
                        "node_count": 3,
                        "ocpu_count": 2,
                        "storage_size_in_gbs": 50,
                    },
                },
            ],
        }

        tools = _make_tool_functions(client)
        result = json.loads(
            tools["oci_kafka_list_oci_clusters"](compartment_id="ocid1.compartment.oc1..aaaaaa")
        )

        assert result["cluster_count"] == 2
        assert len(result["clusters"]) == 2
        assert result["clusters"][0]["display_name"] == "prod-kafka"
        assert result["clusters"][1]["display_name"] == "dev-kafka"
        client.list_kafka_clusters.assert_called_once_with("ocid1.compartment.oc1..aaaaaa")

    def test_uses_config_default_compartment_id(self) -> None:
        """Should fall back to OCI_COMPARTMENT_ID config when no parameter."""
        client = MagicMock(spec=OciKafkaClient)
        client.list_kafka_clusters.return_value = {
            "cluster_count": 0,
            "clusters": [],
        }

        config = OciConfig(compartment_id="ocid1.compartment.oc1..default")
        tools = _make_tool_functions(client, config)
        result = json.loads(tools["oci_kafka_list_oci_clusters"](compartment_id=None))

        assert result["cluster_count"] == 0
        client.list_kafka_clusters.assert_called_once_with("ocid1.compartment.oc1..default")

    def test_falls_back_to_tenancy_id(self) -> None:
        """Should use tenancy OCID when no compartment_id param or env var."""
        client = MagicMock(spec=OciKafkaClient)
        client.get_tenancy_id.return_value = "ocid1.tenancy.oc1..tenancy123"
        client.list_kafka_clusters.return_value = {
            "cluster_count": 1,
            "clusters": [],
        }

        config = OciConfig(compartment_id=None)
        tools = _make_tool_functions(client, config)
        result = json.loads(tools["oci_kafka_list_oci_clusters"](compartment_id=None))

        assert result["cluster_count"] == 1
        client.list_kafka_clusters.assert_called_once_with("ocid1.tenancy.oc1..tenancy123")

    def test_error_when_no_compartment_and_no_tenancy(self) -> None:
        """Should return error guiding LLM to ask user."""
        client = MagicMock(spec=OciKafkaClient)
        client.get_tenancy_id.return_value = None
        config = OciConfig(compartment_id=None)
        tools = _make_tool_functions(client, config)

        result = json.loads(tools["oci_kafka_list_oci_clusters"](compartment_id=None))

        assert "error" in result
        assert "ask the user" in result["error"]
        client.list_kafka_clusters.assert_not_called()

    def test_handles_oci_sdk_not_configured(self) -> None:
        """Should propagate error when OCI SDK is not available."""
        client = MagicMock(spec=OciKafkaClient)
        client.list_kafka_clusters.return_value = {
            "error": "OCI SDK not configured",
        }

        config = OciConfig(compartment_id="ocid1.compartment.oc1..aaaaaa")
        tools = _make_tool_functions(client, config)
        result = json.loads(tools["oci_kafka_list_oci_clusters"](compartment_id=None))

        assert result["error"] == "OCI SDK not configured"

    def test_handles_api_exception(self) -> None:
        """Should return error when OCI API call raises an exception."""
        client = MagicMock(spec=OciKafkaClient)
        client.list_kafka_clusters.side_effect = Exception("Timeout")

        config = OciConfig(compartment_id="ocid1.compartment.oc1..aaaaaa")
        tools = _make_tool_functions(client, config)
        result = json.loads(tools["oci_kafka_list_oci_clusters"](compartment_id=None))

        assert "error" in result
        assert "Timeout" in result["error"]
