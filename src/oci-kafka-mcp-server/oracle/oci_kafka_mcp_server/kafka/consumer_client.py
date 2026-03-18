"""Kafka Consumer client wrapper for consumer group operations."""

from __future__ import annotations

import logging
from typing import Any

from confluent_kafka import Consumer, KafkaException, TopicPartition
from confluent_kafka.admin import AdminClient

from oracle.oci_kafka_mcp_server.config import KafkaConfig

logger = logging.getLogger(__name__)


class KafkaConsumerClient:
    """Wrapper for Kafka consumer group operations."""

    _NOT_CONFIGURED_MSG = (
        "Kafka connection not configured. "
        "Ask the user for: "
        "(1) bootstrap_servers — broker address ending in :9092, "
        "(2) security_protocol — usually SASL_SSL, "
        "(3) sasl_mechanism — usually SCRAM-SHA-512, "
        "(4) sasl_username and (5) sasl_password from their OCI Console cluster details. "
        "Then call oci_kafka_configure_connection with those values."
    )

    def __init__(self, config: KafkaConfig) -> None:
        self._config = config
        self._admin: AdminClient | None = None

    def reconfigure(self, config: KafkaConfig) -> None:
        """Replace the active configuration and reset the client connection."""
        self._config = config
        self._admin = None

    def _get_admin(self) -> AdminClient:
        """Get or create AdminClient for consumer group operations."""
        if not self._config.is_configured:
            raise RuntimeError(self._NOT_CONFIGURED_MSG)
        if self._admin is None:
            confluent_config = self._config.to_confluent_config()
            confluent_config["client.id"] = "oci-kafka-mcp-consumer-admin"
            self._admin = AdminClient(confluent_config)  # type: ignore[arg-type]
        return self._admin

    def list_consumer_groups(self) -> dict[str, Any]:
        """List all consumer groups."""
        admin = self._get_admin()
        future = admin.list_consumer_groups()

        try:
            result = future.result()
            groups = []
            for group in result.valid:
                groups.append(
                    {
                        "group_id": group.group_id,
                        "is_simple": group.is_simple_consumer_group,
                        "state": str(group.state),
                    }
                )
            return {
                "group_count": len(groups),
                "groups": groups,
            }
        except KafkaException as e:
            return {"error": f"Failed to list consumer groups: {e}"}

    def describe_consumer_group(self, group_id: str) -> dict[str, Any]:
        """Get detailed information about a consumer group."""
        admin = self._get_admin()
        futures = admin.describe_consumer_groups([group_id])

        try:
            result = futures[0].result()  # type: ignore[index]
            members = []
            for member in result.members:
                assignment = []
                if member.assignment:
                    assignment = [
                        {"topic": tp.topic, "partition": tp.partition}
                        for tp in member.assignment.topic_partitions
                    ]
                members.append(
                    {
                        "member_id": member.member_id,
                        "client_id": member.client_id,
                        "host": member.host,
                        "assignment": assignment,
                    }
                )

            return {
                "group_id": result.group_id,
                "state": str(result.state),
                "coordinator": {
                    "id": result.coordinator.id,
                    "host": result.coordinator.host,
                    "port": result.coordinator.port,
                },
                "partition_assignor": result.partition_assignor,
                "member_count": len(members),
                "members": members,
            }
        except KafkaException as e:
            return {"error": f"Failed to describe consumer group '{group_id}': {e}"}

    def get_consumer_lag(self, group_id: str) -> dict[str, Any]:
        """Get consumer lag for all partitions assigned to a consumer group."""
        admin = self._get_admin()

        # Get committed offsets for the group
        futures = admin.list_consumer_group_offsets(
            [{"group_id": group_id}]  # type: ignore[list-item]
        )

        try:
            result = futures[0].result()  # type: ignore[index]
        except (KafkaException, Exception) as e:
            return {"error": f"Failed to get offsets for group '{group_id}': {e}"}

        # Create a temporary consumer to get end offsets (high watermarks)
        consumer_config = self._config.to_confluent_config()
        consumer_config["group.id"] = f"oci-mcp-lag-check-{group_id}"
        consumer_config["enable.auto.commit"] = "false"
        consumer = Consumer(consumer_config)

        lag_details = []
        total_lag = 0

        try:
            for tp in result.topic_partitions:
                if tp.error is not None:
                    continue

                committed_offset = tp.offset
                # Get high watermark (end offset)
                low, high = consumer.get_watermark_offsets(
                    TopicPartition(tp.topic, tp.partition), timeout=5
                )

                lag = max(0, high - committed_offset) if committed_offset >= 0 else high - low
                total_lag += lag

                lag_details.append(
                    {
                        "topic": tp.topic,
                        "partition": tp.partition,
                        "committed_offset": committed_offset,
                        "end_offset": high,
                        "lag": lag,
                    }
                )
        finally:
            consumer.close()

        return {
            "group_id": group_id,
            "total_lag": total_lag,
            "partition_count": len(lag_details),
            "partitions": lag_details,
        }

    def _resolve_offsets(
        self,
        topic_name: str,
        partitions: list[int],
        strategy: str,
    ) -> list[TopicPartition] | dict[str, Any]:
        """Resolve target offsets for a reset operation.

        Returns a list of TopicPartition with offsets, or an error dict.
        """
        if strategy in ("earliest", "latest"):
            consumer_config = self._config.to_confluent_config()
            consumer_config["group.id"] = "oci-mcp-offset-resolver"
            consumer_config["enable.auto.commit"] = "false"
            consumer = Consumer(consumer_config)
            try:
                result = []
                for p in partitions:
                    low, high = consumer.get_watermark_offsets(
                        TopicPartition(topic_name, p), timeout=5
                    )
                    offset = low if strategy == "earliest" else high
                    result.append(TopicPartition(topic_name, p, offset))
                return result
            finally:
                consumer.close()

        try:
            target_offset = int(strategy)
        except ValueError:
            return {
                "error": f"Invalid strategy '{strategy}'. "
                "Use 'earliest', 'latest', or an integer offset."
            }
        return [TopicPartition(topic_name, p, target_offset) for p in partitions]

    def reset_consumer_offset(
        self,
        group_id: str,
        topic_name: str,
        strategy: str = "latest",
        partition: int | None = None,
    ) -> dict[str, Any]:
        """Reset consumer group offsets for a topic.

        The consumer group must be in EMPTY state (no active members).

        Args:
            group_id: Consumer group to reset.
            topic_name: Topic to reset offsets for.
            strategy: One of 'earliest', 'latest', or an integer offset.
            partition: Specific partition to reset, or None for all partitions.
        """
        admin = self._get_admin()

        metadata = admin.list_topics(topic=topic_name, timeout=10)
        if topic_name not in metadata.topics:
            return {"error": f"Topic '{topic_name}' not found"}

        topic_meta = metadata.topics[topic_name]
        partitions = [partition] if partition is not None else list(topic_meta.partitions.keys())

        resolved = self._resolve_offsets(topic_name, partitions, strategy)
        if isinstance(resolved, dict):
            return resolved  # error dict

        try:
            futures = admin.alter_consumer_group_offsets(
                [{"group_id": group_id, "topic_partitions": resolved}]  # type: ignore[list-item]
            )
            result = futures[0].result()  # type: ignore[index]

            reset_details = [
                {"topic": tp.topic, "partition": tp.partition, "error": str(tp.error)}
                if tp.error is not None
                else {"topic": tp.topic, "partition": tp.partition, "new_offset": tp.offset}
                for tp in result.topic_partitions
            ]

            return {
                "status": "reset",
                "group_id": group_id,
                "topic": topic_name,
                "strategy": strategy,
                "partitions_reset": len(reset_details),
                "details": reset_details,
            }
        except KafkaException as e:
            return {"error": f"Failed to reset offsets: {e}"}

    def delete_consumer_group(self, group_id: str) -> dict[str, Any]:
        """Delete a consumer group.

        The consumer group must be in EMPTY state (no active members).
        """
        admin = self._get_admin()

        try:
            futures = admin.delete_consumer_groups([group_id])
            futures[0].result()  # type: ignore[index]
            return {"status": "deleted", "group_id": group_id}
        except KafkaException as e:
            return {"error": f"Failed to delete consumer group '{group_id}': {e}"}

    def close(self) -> None:
        """Clean up resources."""
        self._admin = None
