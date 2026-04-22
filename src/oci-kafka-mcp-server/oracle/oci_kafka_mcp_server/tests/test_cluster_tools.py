"""Tests for cluster operation tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from oracle.oci_kafka_mcp_server.kafka.admin_client import KafkaAdminClient


class TestClusterHealthTool:
    """Test the oci_kafka_get_cluster_health tool."""

    @patch("oracle.oci_kafka_mcp_server.kafka.admin_client.AdminClient")
    def test_returns_cluster_info(self, mock_admin_cls: MagicMock) -> None:
        """Should return broker list, controller, and topic count."""
        # Set up mock metadata
        mock_broker = MagicMock()
        mock_broker.host = "kafka-1.example.com"
        mock_broker.port = 9092

        mock_metadata = MagicMock()
        mock_metadata.cluster_id = "test-cluster-123"
        mock_metadata.controller_id = 1
        mock_metadata.brokers = {1: mock_broker}
        mock_metadata.topics = {"topic1": MagicMock(), "topic2": MagicMock()}

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_admin_cls.return_value = mock_client

        from oracle.oci_kafka_mcp_server.config import KafkaConfig

        admin = KafkaAdminClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = admin.get_cluster_health()

        assert result["cluster_id"] == "test-cluster-123"
        assert result["controller_id"] == 1
        assert result["broker_count"] == 1
        assert result["topic_count"] == 2
        assert result["brokers"][0]["host"] == "kafka-1.example.com"


class TestClusterConfigTool:
    """Test the oci_kafka_get_cluster_config tool."""

    @patch("oracle.oci_kafka_mcp_server.kafka.admin_client.AdminClient")
    def test_returns_config(self, mock_admin_cls: MagicMock) -> None:
        """Should return broker configuration entries."""
        mock_broker = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.brokers = {1: mock_broker}

        mock_entry = MagicMock()
        mock_entry.value = "604800000"
        mock_entry.source = "DYNAMIC_BROKER_CONFIG"
        mock_entry.is_read_only = False
        mock_entry.is_default = False

        mock_future = MagicMock()
        mock_future.result.return_value = {"log.retention.ms": mock_entry}

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_client.describe_configs.return_value = {MagicMock(): mock_future}
        mock_admin_cls.return_value = mock_client

        from oracle.oci_kafka_mcp_server.config import KafkaConfig

        admin = KafkaAdminClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = admin.get_cluster_config()

        assert result["broker_id"] == 1
        assert "log.retention.ms" in result["configs"]
        assert result["configs"]["log.retention.ms"]["value"] == "604800000"
