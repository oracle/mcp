"""Tests for observability and diagnostics tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from oracle.oci_kafka_mcp_server.config import KafkaConfig
from oracle.oci_kafka_mcp_server.kafka.admin_client import KafkaAdminClient


class TestPartitionSkew:
    """Test the partition skew detection."""

    @patch("oracle.oci_kafka_mcp_server.kafka.admin_client.AdminClient")
    def test_balanced_partitions(self, mock_admin_cls: MagicMock) -> None:
        """Evenly distributed partitions should not detect skew."""
        # 3 brokers, each leading 2 partitions
        partitions = {}
        for i in range(6):
            p = MagicMock()
            p.leader = i % 3  # Round-robin across 3 brokers
            partitions[i] = p

        mock_topic = MagicMock()
        mock_topic.error = None
        mock_topic.partitions = partitions

        mock_metadata = MagicMock()
        mock_metadata.topics = {"test-topic": mock_topic}

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_admin_cls.return_value = mock_client

        admin = KafkaAdminClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = admin.get_partition_skew()

        assert result["skew_detected"] is False
        assert result["skew_ratio"] == 1.0

    @patch("oracle.oci_kafka_mcp_server.kafka.admin_client.AdminClient")
    def test_skewed_partitions(self, mock_admin_cls: MagicMock) -> None:
        """Unevenly distributed partitions should detect skew."""
        # Broker 0 leads 5 partitions, broker 1 leads 1
        partitions = {}
        for i in range(6):
            p = MagicMock()
            p.leader = 0 if i < 5 else 1
            partitions[i] = p

        mock_topic = MagicMock()
        mock_topic.error = None
        mock_topic.partitions = partitions

        mock_metadata = MagicMock()
        mock_metadata.topics = {"test-topic": mock_topic}

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_admin_cls.return_value = mock_client

        admin = KafkaAdminClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = admin.get_partition_skew()

        assert result["skew_detected"] is True
        assert result["skew_ratio"] == 5.0


class TestUnderReplicatedPartitions:
    """Test under-replicated partition detection."""

    @patch("oracle.oci_kafka_mcp_server.kafka.admin_client.AdminClient")
    def test_all_healthy(self, mock_admin_cls: MagicMock) -> None:
        """All partitions in-sync should return healthy."""
        mock_partition = MagicMock()
        mock_partition.replicas = [1, 2, 3]
        mock_partition.isrs = [1, 2, 3]

        mock_topic = MagicMock()
        mock_topic.error = None
        mock_topic.partitions = {0: mock_partition}

        mock_metadata = MagicMock()
        mock_metadata.topics = {"test-topic": mock_topic}

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_admin_cls.return_value = mock_client

        admin = KafkaAdminClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = admin.detect_under_replicated_partitions()

        assert result["healthy"] is True
        assert result["under_replicated_count"] == 0

    @patch("oracle.oci_kafka_mcp_server.kafka.admin_client.AdminClient")
    def test_under_replicated(self, mock_admin_cls: MagicMock) -> None:
        """Partitions with ISR < replicas should be flagged."""
        mock_partition = MagicMock()
        mock_partition.replicas = [1, 2, 3]
        mock_partition.isrs = [1, 3]  # Broker 2 fell out of ISR

        mock_topic = MagicMock()
        mock_topic.error = None
        mock_topic.partitions = {0: mock_partition}

        mock_metadata = MagicMock()
        mock_metadata.topics = {"test-topic": mock_topic}

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_admin_cls.return_value = mock_client

        admin = KafkaAdminClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = admin.detect_under_replicated_partitions()

        assert result["healthy"] is False
        assert result["under_replicated_count"] == 1
        assert result["under_replicated_partitions"][0]["missing_replicas"] == 1
        assert result["under_replicated_partitions"][0]["topic"] == "test-topic"
