"""Shared test fixtures for OCI Kafka MCP Server tests."""

from __future__ import annotations

import pytest

from oracle.oci_kafka_mcp_server.config import KafkaConfig, ServerConfig
from oracle.oci_kafka_mcp_server.kafka.admin_client import KafkaAdminClient
from oracle.oci_kafka_mcp_server.kafka.connection import CircuitBreaker
from oracle.oci_kafka_mcp_server.kafka.consumer_client import KafkaConsumerClient
from oracle.oci_kafka_mcp_server.security.policy_guard import PolicyGuard


@pytest.fixture
def kafka_config() -> KafkaConfig:
    """Create a test Kafka configuration."""
    return KafkaConfig(
        bootstrap_servers="localhost:9092",
        security_protocol="PLAINTEXT",
    )


@pytest.fixture
def server_config() -> ServerConfig:
    """Create a test server configuration."""
    return ServerConfig(allow_writes=True)


@pytest.fixture
def policy_guard_readonly() -> PolicyGuard:
    """Policy guard in read-only mode."""
    return PolicyGuard(allow_writes=False)


@pytest.fixture
def policy_guard_readwrite() -> PolicyGuard:
    """Policy guard with writes enabled."""
    return PolicyGuard(allow_writes=True)


@pytest.fixture
def circuit_breaker() -> CircuitBreaker:
    """Fresh circuit breaker for testing."""
    return CircuitBreaker(failure_threshold=3, cooldown_seconds=1.0)


@pytest.fixture
def mock_admin_client(kafka_config: KafkaConfig) -> KafkaAdminClient:
    """KafkaAdminClient with a mocked underlying confluent-kafka client."""
    client = KafkaAdminClient(kafka_config)
    # We'll mock the internal _client in individual tests
    return client


@pytest.fixture
def mock_consumer_client(kafka_config: KafkaConfig) -> KafkaConsumerClient:
    """KafkaConsumerClient with mocked internals."""
    return KafkaConsumerClient(kafka_config)
