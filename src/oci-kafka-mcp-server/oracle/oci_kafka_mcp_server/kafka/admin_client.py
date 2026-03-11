"""Kafka AdminClient wrapper with connection management and circuit breaker."""

from __future__ import annotations

import logging
from typing import Any

from confluent_kafka import KafkaException
from confluent_kafka.admin import (  # type: ignore[attr-defined]
    AdminClient,
    ConfigResource,
    NewTopic,
    ResourceType,
)

from oracle.oci_kafka_mcp_server.config import KafkaConfig

logger = logging.getLogger(__name__)


class KafkaAdminClient:
    """Wrapper around confluent_kafka AdminClient.

    Provides structured access to Kafka admin operations with
    connection management and error handling.
    """

    _NO_RESULT_MSG = "No result returned"
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
        self._client: AdminClient | None = None

    def reconfigure(self, config: KafkaConfig) -> None:
        """Replace the active configuration and reset the client connection."""
        self._config = config
        self._client = None

    def _get_client(self) -> AdminClient:
        """Get or create the AdminClient instance."""
        if not self._config.is_configured:
            raise RuntimeError(self._NOT_CONFIGURED_MSG)
        if self._client is None:
            confluent_config = self._config.to_confluent_config()
            confluent_config["client.id"] = "oci-kafka-mcp-admin"
            self._client = AdminClient(confluent_config)  # type: ignore[arg-type]
        return self._client

    def get_cluster_health(self) -> dict[str, Any]:
        """Get cluster health: broker list, controller, and cluster ID."""
        client = self._get_client()
        metadata = client.list_topics(timeout=10)

        brokers = []
        for broker_id, broker in metadata.brokers.items():
            brokers.append(
                {
                    "id": broker_id,
                    "host": broker.host,
                    "port": broker.port,
                }
            )

        return {
            "cluster_id": metadata.cluster_id,
            "controller_id": metadata.controller_id,
            "broker_count": len(brokers),
            "brokers": brokers,
            "topic_count": len(metadata.topics),
        }

    def get_cluster_config(self) -> dict[str, Any]:
        """Get configuration for all brokers in the cluster."""
        client = self._get_client()
        metadata = client.list_topics(timeout=10)

        # Get config for the first broker (cluster-level config)
        if not metadata.brokers:
            return {"error": "No brokers available"}

        broker_id = next(iter(metadata.brokers))
        resource = ConfigResource(ResourceType.BROKER, str(broker_id))
        futures = client.describe_configs([resource])

        configs: dict[str, Any] = {}
        for _resource, future in futures.items():
            try:
                config_entries = future.result()
                for name, entry in config_entries.items():
                    configs[name] = {
                        "value": entry.value,
                        "source": str(entry.source),
                        "is_read_only": entry.is_read_only,
                        "is_default": entry.is_default,
                    }
            except KafkaException as e:
                return {"error": f"Failed to describe config: {e}"}

        return {
            "broker_id": broker_id,
            "config_count": len(configs),
            "configs": configs,
        }

    def list_topics(self) -> dict[str, Any]:
        """List all topics in the cluster."""
        client = self._get_client()
        metadata = client.list_topics(timeout=10)

        topics = []
        for topic_name, topic_metadata in metadata.topics.items():
            if topic_metadata.error is not None:
                continue
            topics.append(
                {
                    "name": topic_name,
                    "partition_count": len(topic_metadata.partitions),
                }
            )

        return {
            "topic_count": len(topics),
            "topics": topics,
        }

    def describe_topic(self, topic_name: str) -> dict[str, Any]:
        """Get detailed information about a specific topic."""
        client = self._get_client()
        metadata = client.list_topics(topic=topic_name, timeout=10)

        if topic_name not in metadata.topics:
            return {"error": f"Topic '{topic_name}' not found"}

        topic_meta = metadata.topics[topic_name]
        if topic_meta.error is not None:
            return {"error": f"Topic error: {topic_meta.error}"}

        partitions = []
        for part_id, part_meta in topic_meta.partitions.items():
            partitions.append(
                {
                    "id": part_id,
                    "leader": part_meta.leader,
                    "replicas": list(part_meta.replicas),
                    "in_sync_replicas": list(part_meta.isrs),
                }
            )

        # Get topic config
        resource = ConfigResource(ResourceType.TOPIC, topic_name)
        futures = client.describe_configs([resource])
        config: dict[str, str] = {}
        for _res, future in futures.items():
            try:
                config_entries = future.result()
                for name, entry in config_entries.items():
                    if not entry.is_default:
                        config[name] = entry.value
            except KafkaException:
                pass

        return {
            "name": topic_name,
            "partition_count": len(partitions),
            "partitions": partitions,
            "config": config,
        }

    def create_topic(
        self, topic_name: str, num_partitions: int, replication_factor: int
    ) -> dict[str, Any]:
        """Create a new topic."""
        client = self._get_client()
        new_topic = NewTopic(
            topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor,
        )
        futures = client.create_topics([new_topic])

        for topic, future in futures.items():
            try:
                future.result()
                return {
                    "status": "created",
                    "topic": topic,
                    "partitions": num_partitions,
                    "replication_factor": replication_factor,
                }
            except KafkaException as e:
                return {"status": "error", "topic": topic, "error": str(e)}

        return {"status": "error", "error": self._NO_RESULT_MSG}

    def delete_topic(self, topic_name: str) -> dict[str, Any]:
        """Delete a topic."""
        client = self._get_client()
        futures = client.delete_topics([topic_name])

        for topic, future in futures.items():
            try:
                future.result()
                return {"status": "deleted", "topic": topic}
            except KafkaException as e:
                return {"status": "error", "topic": topic, "error": str(e)}

        return {"status": "error", "error": self._NO_RESULT_MSG}

    def update_topic_config(self, topic_name: str, configs: dict[str, str]) -> dict[str, Any]:
        """Update topic configuration."""
        client = self._get_client()
        resource = ConfigResource(ResourceType.TOPIC, topic_name)
        for key, value in configs.items():
            resource.set_config(key, value)

        futures = client.alter_configs([resource])

        for _res, future in futures.items():
            try:
                future.result()
                return {
                    "status": "updated",
                    "topic": topic_name,
                    "updated_configs": configs,
                }
            except KafkaException as e:
                return {"status": "error", "topic": topic_name, "error": str(e)}

        return {"status": "error", "error": self._NO_RESULT_MSG}

    def get_partition_skew(self, topic_name: str | None = None) -> dict[str, Any]:
        """Detect partition imbalance across brokers.

        If topic_name is provided, checks that specific topic.
        Otherwise, checks all topics.
        """
        client = self._get_client()
        if topic_name:
            metadata = client.list_topics(topic=topic_name, timeout=10)
        else:
            metadata = client.list_topics(timeout=10)

        # Count partitions per broker (as leader)
        broker_leader_count: dict[int, int] = {}
        for _topic_name, topic_meta in metadata.topics.items():
            if topic_meta.error is not None:
                continue
            for _part_id, part_meta in topic_meta.partitions.items():
                leader = part_meta.leader
                broker_leader_count[leader] = broker_leader_count.get(leader, 0) + 1

        if not broker_leader_count:
            return {"skew_detected": False, "message": "No partition data available"}

        counts = list(broker_leader_count.values())
        min_count = min(counts)
        max_count = max(counts)
        skew_ratio = max_count / min_count if min_count > 0 else float("inf")

        return {
            "skew_detected": skew_ratio > 1.5,
            "skew_ratio": round(skew_ratio, 2),
            "broker_partition_counts": broker_leader_count,
            "min_partitions": min_count,
            "max_partitions": max_count,
            "recommendation": (
                "Partition distribution is uneven. Consider rebalancing."
                if skew_ratio > 1.5
                else "Partition distribution is balanced."
            ),
        }

    def detect_under_replicated_partitions(self) -> dict[str, Any]:
        """Detect partitions where ISR count < replica count."""
        client = self._get_client()
        metadata = client.list_topics(timeout=10)

        under_replicated = []
        total_partitions = 0

        for topic_name, topic_meta in metadata.topics.items():
            if topic_meta.error is not None:
                continue
            for part_id, part_meta in topic_meta.partitions.items():
                total_partitions += 1
                if len(part_meta.isrs) < len(part_meta.replicas):
                    under_replicated.append(
                        {
                            "topic": topic_name,
                            "partition": part_id,
                            "replicas": list(part_meta.replicas),
                            "in_sync_replicas": list(part_meta.isrs),
                            "missing_replicas": len(part_meta.replicas) - len(part_meta.isrs),
                        }
                    )

        return {
            "total_partitions": total_partitions,
            "under_replicated_count": len(under_replicated),
            "healthy": len(under_replicated) == 0,
            "under_replicated_partitions": under_replicated,
        }

    def close(self) -> None:
        """Close the admin client connection."""
        self._client = None
