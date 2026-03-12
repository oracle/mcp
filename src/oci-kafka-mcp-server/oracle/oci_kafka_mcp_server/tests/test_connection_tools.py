"""Tests for connection configuration tools."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from oracle.oci_kafka_mcp_server.config import KafkaConfig
from oracle.oci_kafka_mcp_server.kafka.admin_client import KafkaAdminClient
from oracle.oci_kafka_mcp_server.kafka.connection import CircuitBreaker, CircuitState
from oracle.oci_kafka_mcp_server.kafka.consumer_client import KafkaConsumerClient


class TestKafkaConfigIsConfigured:
    """Test the is_configured property."""

    def test_default_is_not_configured(self) -> None:
        config = KafkaConfig()
        assert config.is_configured is False

    def test_custom_bootstrap_is_configured(self) -> None:
        config = KafkaConfig(bootstrap_servers="broker.example.com:9092")
        assert config.is_configured is True

    def test_localhost_non_default_port_is_configured(self) -> None:
        config = KafkaConfig(bootstrap_servers="localhost:9093")
        assert config.is_configured is True


class TestCircuitBreakerReset:
    """Test the CircuitBreaker.reset() method."""

    def test_reset_clears_failure_count(self) -> None:
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True


class TestAdminClientReconfigure:
    """Test KafkaAdminClient.reconfigure()."""

    @patch("oracle.oci_kafka_mcp_server.kafka.admin_client.AdminClient")
    def test_reconfigure_resets_client(self, mock_admin_cls: MagicMock) -> None:
        original_config = KafkaConfig(bootstrap_servers="old.broker:9092")
        client = KafkaAdminClient(original_config)

        # Force client creation
        mock_admin_cls.return_value = MagicMock()
        client._get_client()
        assert client._client is not None

        new_config = KafkaConfig(bootstrap_servers="new.broker:9092")
        client.reconfigure(new_config)

        assert client._config is new_config
        assert client._client is None

    def test_not_configured_raises_runtime_error(self) -> None:
        client = KafkaAdminClient(KafkaConfig())  # default = localhost:9092
        with pytest.raises(RuntimeError, match="oci_kafka_configure_connection"):
            client._get_client()


class TestConsumerClientReconfigure:
    """Test KafkaConsumerClient.reconfigure()."""

    @patch("oracle.oci_kafka_mcp_server.kafka.consumer_client.AdminClient")
    def test_reconfigure_resets_admin(self, mock_admin_cls: MagicMock) -> None:
        original_config = KafkaConfig(bootstrap_servers="old.broker:9092")
        client = KafkaConsumerClient(original_config)

        mock_admin_cls.return_value = MagicMock()
        client._get_admin()
        assert client._admin is not None

        new_config = KafkaConfig(bootstrap_servers="new.broker:9092")
        client.reconfigure(new_config)

        assert client._config is new_config
        assert client._admin is None

    def test_not_configured_raises_runtime_error(self) -> None:
        client = KafkaConsumerClient(KafkaConfig())
        with pytest.raises(RuntimeError, match="oci_kafka_configure_connection"):
            client._get_admin()


class TestConnectionTools:
    """Test the connection MCP tools via the register function."""

    def _make_tools(
        self,
    ) -> tuple[MagicMock, KafkaAdminClient, KafkaConsumerClient, CircuitBreaker]:
        """Return (mcp_mock, admin_client, consumer_client, circuit_breaker)."""
        from mcp.server.fastmcp import FastMCP

        from oracle.oci_kafka_mcp_server.tools.connection import register_connection_tools

        mcp = FastMCP("test")
        admin = KafkaAdminClient(KafkaConfig())
        consumer = KafkaConsumerClient(KafkaConfig())
        cb = CircuitBreaker()
        register_connection_tools(mcp, admin, consumer, cb)
        return mcp, admin, consumer, cb

    def test_configure_connection_updates_clients(self) -> None:
        _mcp, admin, consumer, cb = self._make_tools()

        from mcp.server.fastmcp import FastMCP

        from oracle.oci_kafka_mcp_server.tools.connection import register_connection_tools

        # Access tools via direct function call pattern
        mcp = FastMCP("test2")
        admin2 = KafkaAdminClient(KafkaConfig())
        consumer2 = KafkaConsumerClient(KafkaConfig())
        cb2 = CircuitBreaker()

        captured: dict = {}

        # Monkeypatch reconfigure to capture calls
        def fake_admin_reconfig(cfg: KafkaConfig) -> None:
            captured["admin_config"] = cfg

        def fake_consumer_reconfig(cfg: KafkaConfig) -> None:
            captured["consumer_config"] = cfg

        admin2.reconfigure = fake_admin_reconfig  # type: ignore[method-assign]
        consumer2.reconfigure = fake_consumer_reconfig  # type: ignore[method-assign]

        register_connection_tools(mcp, admin2, consumer2, cb2)

        # Get the tool function from the FastMCP registry
        tool_fn = None
        for tool in mcp._tool_manager.list_tools():
            if tool.name == "oci_kafka_configure_connection":
                tool_fn = mcp._tool_manager._tools[tool.name].fn
                break

        assert tool_fn is not None
        result = json.loads(
            tool_fn(
                bootstrap_servers="new.broker:9092",
                security_protocol="SASL_SSL",
                sasl_mechanism="SCRAM-SHA-512",
                sasl_username="user1",
                sasl_password="pass1",
            )
        )

        assert result["status"] == "configured"
        assert result["bootstrap_servers"] == "new.broker:9092"
        assert result["authenticated"] is True
        assert captured["admin_config"].bootstrap_servers == "new.broker:9092"
        assert captured["consumer_config"].bootstrap_servers == "new.broker:9092"

    def test_configure_resets_circuit_breaker(self) -> None:
        from mcp.server.fastmcp import FastMCP

        from oracle.oci_kafka_mcp_server.tools.connection import register_connection_tools

        mcp = FastMCP("test3")
        admin = KafkaAdminClient(KafkaConfig())
        consumer = KafkaConsumerClient(KafkaConfig())
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        register_connection_tools(mcp, admin, consumer, cb)
        tool_fn = mcp._tool_manager._tools["oci_kafka_configure_connection"].fn
        tool_fn(bootstrap_servers="broker:9092")

        assert cb.state == CircuitState.CLOSED

    def test_get_connection_info_not_configured(self) -> None:
        from mcp.server.fastmcp import FastMCP

        from oracle.oci_kafka_mcp_server.tools.connection import register_connection_tools

        mcp = FastMCP("test4")
        admin = KafkaAdminClient(KafkaConfig())
        consumer = KafkaConsumerClient(KafkaConfig())
        cb = CircuitBreaker()
        register_connection_tools(mcp, admin, consumer, cb)

        tool_fn = mcp._tool_manager._tools["oci_kafka_get_connection_info"].fn
        result = json.loads(tool_fn())

        assert result["configured"] is False
        assert result["action_if_not_configured"] is not None

    def test_get_connection_info_configured(self) -> None:
        from mcp.server.fastmcp import FastMCP

        from oracle.oci_kafka_mcp_server.tools.connection import register_connection_tools

        mcp = FastMCP("test5")
        admin = KafkaAdminClient(
            KafkaConfig(
                bootstrap_servers="real.broker:9092",
                sasl_username="admin",
                sasl_password="secret",
            )
        )
        consumer = KafkaConsumerClient(KafkaConfig())
        cb = CircuitBreaker()
        register_connection_tools(mcp, admin, consumer, cb)

        tool_fn = mcp._tool_manager._tools["oci_kafka_get_connection_info"].fn
        result = json.loads(tool_fn())

        assert result["configured"] is True
        assert result["bootstrap_servers"] == "real.broker:9092"
        assert result["sasl_username"] == "admin"
        assert result["password_set"] is True
        assert result["action_if_not_configured"] is None

    def test_configure_persist_writes_file(self, tmp_path: pytest.FixtureRequest) -> None:
        from mcp.server.fastmcp import FastMCP

        from oracle.oci_kafka_mcp_server.tools import connection as conn_module
        from oracle.oci_kafka_mcp_server.tools.connection import register_connection_tools

        persist_path = tmp_path / "test-connection.env"  # type: ignore[operator]
        original_path = conn_module._DEFAULT_PERSIST_PATH
        conn_module._DEFAULT_PERSIST_PATH = persist_path  # type: ignore[assignment]

        try:
            mcp = FastMCP("test6")
            admin = KafkaAdminClient(KafkaConfig())
            consumer = KafkaConsumerClient(KafkaConfig())
            cb = CircuitBreaker()
            register_connection_tools(mcp, admin, consumer, cb)

            tool_fn = mcp._tool_manager._tools["oci_kafka_configure_connection"].fn
            result = json.loads(
                tool_fn(
                    bootstrap_servers="broker:9092",
                    sasl_username="user",
                    sasl_password="pass",
                    persist=True,
                )
            )

            assert "persisted_to" in result
            assert persist_path.exists()
            content = persist_path.read_text()
            assert "broker:9092" in content
            assert "pass" in content
        finally:
            conn_module._DEFAULT_PERSIST_PATH = original_path
