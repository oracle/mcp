"""Tests for consumer write tools (reset offset, delete group)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from oracle.oci_kafka_mcp_server.config import KafkaConfig
from oracle.oci_kafka_mcp_server.kafka.consumer_client import KafkaConsumerClient


class TestResetConsumerOffset:
    """Test the reset_consumer_offset method."""

    @patch("oracle.oci_kafka_mcp_server.kafka.consumer_client.Consumer")
    @patch("oracle.oci_kafka_mcp_server.kafka.consumer_client.AdminClient")
    def test_reset_to_latest(self, mock_admin_cls: MagicMock, mock_consumer_cls: MagicMock) -> None:
        """Should reset offsets to latest (end) for all partitions."""
        # Mock topic metadata
        mock_metadata = MagicMock()
        mock_metadata.topics = {"orders": MagicMock(partitions={0: MagicMock(), 1: MagicMock()})}

        # Mock watermark offsets
        mock_consumer = MagicMock()
        mock_consumer.get_watermark_offsets.side_effect = [(0, 100), (0, 200)]
        mock_consumer_cls.return_value = mock_consumer

        # Mock alter offsets result
        mock_tp0 = MagicMock(topic="orders", partition=0, offset=100, error=None)
        mock_tp1 = MagicMock(topic="orders", partition=1, offset=200, error=None)
        mock_result = MagicMock()
        mock_result.topic_partitions = [mock_tp0, mock_tp1]
        mock_future = MagicMock()
        mock_future.result.return_value = mock_result

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_client.alter_consumer_group_offsets.return_value = [mock_future]
        mock_admin_cls.return_value = mock_client

        consumer = KafkaConsumerClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = consumer.reset_consumer_offset("my-group", "orders", "latest")

        assert result["status"] == "reset"
        assert result["group_id"] == "my-group"
        assert result["strategy"] == "latest"
        assert result["partitions_reset"] == 2
        assert result["details"][0]["new_offset"] == 100
        assert result["details"][1]["new_offset"] == 200

    @patch("oracle.oci_kafka_mcp_server.kafka.consumer_client.Consumer")
    @patch("oracle.oci_kafka_mcp_server.kafka.consumer_client.AdminClient")
    def test_reset_to_earliest(
        self, mock_admin_cls: MagicMock, mock_consumer_cls: MagicMock
    ) -> None:
        """Should reset offsets to earliest (beginning) for all partitions."""
        mock_metadata = MagicMock()
        mock_metadata.topics = {"orders": MagicMock(partitions={0: MagicMock()})}

        mock_consumer = MagicMock()
        mock_consumer.get_watermark_offsets.return_value = (0, 500)
        mock_consumer_cls.return_value = mock_consumer

        mock_tp = MagicMock(topic="orders", partition=0, offset=0, error=None)
        mock_result = MagicMock()
        mock_result.topic_partitions = [mock_tp]
        mock_future = MagicMock()
        mock_future.result.return_value = mock_result

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_client.alter_consumer_group_offsets.return_value = [mock_future]
        mock_admin_cls.return_value = mock_client

        consumer = KafkaConsumerClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = consumer.reset_consumer_offset("my-group", "orders", "earliest")

        assert result["status"] == "reset"
        assert result["strategy"] == "earliest"
        assert result["details"][0]["new_offset"] == 0

    @patch("oracle.oci_kafka_mcp_server.kafka.consumer_client.AdminClient")
    def test_reset_to_specific_offset(self, mock_admin_cls: MagicMock) -> None:
        """Should reset offsets to a specific integer offset."""
        mock_metadata = MagicMock()
        mock_metadata.topics = {"orders": MagicMock(partitions={0: MagicMock(), 1: MagicMock()})}

        mock_tp0 = MagicMock(topic="orders", partition=0, offset=42, error=None)
        mock_tp1 = MagicMock(topic="orders", partition=1, offset=42, error=None)
        mock_result = MagicMock()
        mock_result.topic_partitions = [mock_tp0, mock_tp1]
        mock_future = MagicMock()
        mock_future.result.return_value = mock_result

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_client.alter_consumer_group_offsets.return_value = [mock_future]
        mock_admin_cls.return_value = mock_client

        consumer = KafkaConsumerClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = consumer.reset_consumer_offset("my-group", "orders", "42")

        assert result["status"] == "reset"
        assert result["strategy"] == "42"
        assert result["details"][0]["new_offset"] == 42

    @patch("oracle.oci_kafka_mcp_server.kafka.consumer_client.AdminClient")
    def test_reset_invalid_strategy(self, mock_admin_cls: MagicMock) -> None:
        """Should return error for invalid strategy string."""
        mock_metadata = MagicMock()
        mock_metadata.topics = {"orders": MagicMock(partitions={0: MagicMock()})}

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_admin_cls.return_value = mock_client

        consumer = KafkaConsumerClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = consumer.reset_consumer_offset("my-group", "orders", "invalid")

        assert "error" in result
        assert "Invalid strategy" in result["error"]

    @patch("oracle.oci_kafka_mcp_server.kafka.consumer_client.AdminClient")
    def test_reset_topic_not_found(self, mock_admin_cls: MagicMock) -> None:
        """Should return error when topic doesn't exist."""
        mock_metadata = MagicMock()
        mock_metadata.topics = {}

        mock_client = MagicMock()
        mock_client.list_topics.return_value = mock_metadata
        mock_admin_cls.return_value = mock_client

        consumer = KafkaConsumerClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = consumer.reset_consumer_offset("my-group", "nonexistent", "latest")

        assert "error" in result
        assert "not found" in result["error"]


class TestDeleteConsumerGroup:
    """Test the delete_consumer_group method."""

    @patch("oracle.oci_kafka_mcp_server.kafka.consumer_client.AdminClient")
    def test_deletes_group(self, mock_admin_cls: MagicMock) -> None:
        """Should delete a consumer group and return success."""
        mock_future = MagicMock()
        mock_future.result.return_value = None

        mock_client = MagicMock()
        mock_client.delete_consumer_groups.return_value = [mock_future]
        mock_admin_cls.return_value = mock_client

        consumer = KafkaConsumerClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = consumer.delete_consumer_group("old-group")

        assert result["status"] == "deleted"
        assert result["group_id"] == "old-group"

    @patch("oracle.oci_kafka_mcp_server.kafka.consumer_client.AdminClient")
    def test_delete_group_error(self, mock_admin_cls: MagicMock) -> None:
        """Should return error when deletion fails."""
        from confluent_kafka import KafkaException

        mock_future = MagicMock()
        mock_future.result.side_effect = KafkaException(
            MagicMock(str=lambda _: "Group has active members")
        )

        mock_client = MagicMock()
        mock_client.delete_consumer_groups.return_value = [mock_future]
        mock_admin_cls.return_value = mock_client

        consumer = KafkaConsumerClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = consumer.delete_consumer_group("active-group")

        assert "error" in result
