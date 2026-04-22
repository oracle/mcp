"""Tests for consumer operation tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from oracle.oci_kafka_mcp_server.config import KafkaConfig
from oracle.oci_kafka_mcp_server.kafka.consumer_client import KafkaConsumerClient


class TestListConsumerGroups:
    """Test listing consumer groups."""

    @patch("oracle.oci_kafka_mcp_server.kafka.consumer_client.AdminClient")
    def test_returns_groups(self, mock_admin_cls: MagicMock) -> None:
        """Should return list of consumer groups."""
        mock_group1 = MagicMock()
        mock_group1.group_id = "payment-processor"
        mock_group1.is_simple_consumer_group = False
        mock_group1.state = "Stable"

        mock_group2 = MagicMock()
        mock_group2.group_id = "analytics-etl"
        mock_group2.is_simple_consumer_group = False
        mock_group2.state = "Empty"

        mock_result = MagicMock()
        mock_result.valid = [mock_group1, mock_group2]

        mock_future = MagicMock()
        mock_future.result.return_value = mock_result

        mock_client = MagicMock()
        mock_client.list_consumer_groups.return_value = mock_future
        mock_admin_cls.return_value = mock_client

        consumer = KafkaConsumerClient(KafkaConfig(bootstrap_servers="test.broker:9092"))
        result = consumer.list_consumer_groups()

        assert result["group_count"] == 2
        assert result["groups"][0]["group_id"] == "payment-processor"
        assert result["groups"][1]["group_id"] == "analytics-etl"
