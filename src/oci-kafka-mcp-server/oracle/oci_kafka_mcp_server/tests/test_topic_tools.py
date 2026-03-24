"""Tests for topic operation tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from oracle.oci_kafka_mcp_server.config import KafkaConfig
from oracle.oci_kafka_mcp_server.kafka.admin_client import KafkaAdminClient


class TestListTopics:
    """Test the list_topics admin method."""

    @patch("oracle.oci_kafka_mcp_server.kafka.admin_client.AdminClient")
    def test_returns_topics(self, mock_admin_cls: MagicMock) -> None:
        """Should return a list of topics with partition counts."""
        mock_topic1 = MagicMock()
        mock_topic1.error = None
        mock_topic1.partitions = {0: MagicMock(), 1: MagicMock(), 2: MagicMock()}

        mock_topic2 = MagicMock()
        mock_topic2.error = None
        mock_topic2.partitions = {0: MagicMock()}

        mock_metadata = MagicMock()
        mock_metadata.topics = {"orders": mock_topic1, "events": mock_topic2}

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_admin_cls.return_value = mock_client

        admin = KafkaAdminClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = admin.list_topics()

        assert result["topic_count"] == 2
        topics_by_name = {t["name"]: t for t in result["topics"]}
        assert topics_by_name["orders"]["partition_count"] == 3
        assert topics_by_name["events"]["partition_count"] == 1


class TestDescribeTopic:
    """Test the describe_topic admin method."""

    @patch("oracle.oci_kafka_mcp_server.kafka.admin_client.AdminClient")
    def test_returns_topic_details(self, mock_admin_cls: MagicMock) -> None:
        """Should return partition details and non-default config."""
        mock_partition = MagicMock()
        mock_partition.leader = 1
        mock_partition.replicas = [1, 2, 3]
        mock_partition.isrs = [1, 2, 3]

        mock_topic = MagicMock()
        mock_topic.error = None
        mock_topic.partitions = {0: mock_partition}

        mock_metadata = MagicMock()
        mock_metadata.topics = {"orders": mock_topic}

        mock_entry = MagicMock()
        mock_entry.value = "compact"
        mock_entry.is_default = False

        mock_default_entry = MagicMock()
        mock_default_entry.value = "604800000"
        mock_default_entry.is_default = True

        mock_future = MagicMock()
        mock_future.result.return_value = {
            "cleanup.policy": mock_entry,
            "retention.ms": mock_default_entry,
        }

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_client.describe_configs.return_value = {MagicMock(): mock_future}
        mock_admin_cls.return_value = mock_client

        admin = KafkaAdminClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = admin.describe_topic("orders")

        assert result["name"] == "orders"
        assert result["partition_count"] == 1
        assert result["partitions"][0]["leader"] == 1
        assert result["partitions"][0]["replicas"] == [1, 2, 3]
        # Only non-default config should be included
        assert "cleanup.policy" in result["config"]
        assert "retention.ms" not in result["config"]

    @patch("oracle.oci_kafka_mcp_server.kafka.admin_client.AdminClient")
    def test_topic_not_found(self, mock_admin_cls: MagicMock) -> None:
        """Should return error for non-existent topic."""
        mock_metadata = MagicMock()
        mock_metadata.topics = {}

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_admin_cls.return_value = mock_client

        admin = KafkaAdminClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = admin.describe_topic("nonexistent")

        assert "error" in result


class TestCreateTopic:
    """Test the create_topic admin method."""

    @patch("oracle.oci_kafka_mcp_server.kafka.admin_client.AdminClient")
    def test_creates_topic(self, mock_admin_cls: MagicMock) -> None:
        """Should create a topic and return success status."""
        mock_future = MagicMock()
        mock_future.result.return_value = None

        mock_client = MagicMock()
        mock_client.create_topics.return_value = {"test-topic": mock_future}
        mock_admin_cls.return_value = mock_client

        admin = KafkaAdminClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = admin.create_topic("test-topic", num_partitions=6, replication_factor=3)

        assert result["status"] == "created"
        assert result["topic"] == "test-topic"
        assert result["partitions"] == 6
        assert result["replication_factor"] == 3


class TestDeleteTopic:
    """Test the delete_topic admin method."""

    @patch("oracle.oci_kafka_mcp_server.kafka.admin_client.AdminClient")
    def test_deletes_topic(self, mock_admin_cls: MagicMock) -> None:
        """Should delete a topic and return success status."""
        mock_future = MagicMock()
        mock_future.result.return_value = None

        mock_client = MagicMock()
        mock_client.delete_topics.return_value = {"test-topic": mock_future}
        mock_admin_cls.return_value = mock_client

        admin = KafkaAdminClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = admin.delete_topic("test-topic")

        assert result["status"] == "deleted"
        assert result["topic"] == "test-topic"
