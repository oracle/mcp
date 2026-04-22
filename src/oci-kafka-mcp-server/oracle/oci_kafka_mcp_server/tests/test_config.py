"""Tests for configuration management."""

from oracle.oci_kafka_mcp_server.config import KafkaConfig, ServerConfig
from oracle.oci_kafka_mcp_server.security.auth import validate_kafka_auth


class TestKafkaConfig:
    """Test Kafka configuration."""

    def test_default_config(self) -> None:
        """Default config should use localhost plaintext."""
        config = KafkaConfig()
        assert config.bootstrap_servers == "localhost:9092"
        assert config.security_protocol == "PLAINTEXT"
        assert config.sasl_mechanism is None

    def test_to_confluent_config_plaintext(self) -> None:
        """Plaintext config should produce minimal confluent config."""
        config = KafkaConfig()
        confluent = config.to_confluent_config()
        assert confluent["bootstrap.servers"] == "localhost:9092"
        assert confluent["security.protocol"] == "PLAINTEXT"
        assert "sasl.mechanism" not in confluent

    def test_to_confluent_config_sasl_ssl(self) -> None:
        """SASL_SSL config should include all SASL and SSL settings."""
        config = KafkaConfig(
            bootstrap_servers="kafka.example.com:9093",
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_username="admin",
            sasl_password="secret",
            ssl_ca_location="/certs/ca.pem",
        )
        confluent = config.to_confluent_config()
        assert confluent["security.protocol"] == "SASL_SSL"
        assert confluent["sasl.mechanism"] == "SCRAM-SHA-512"
        assert confluent["sasl.username"] == "admin"
        assert confluent["sasl.password"] == "secret"
        assert confluent["ssl.ca.location"] == "/certs/ca.pem"


class TestAuthValidation:
    """Test authentication configuration validation."""

    def test_plaintext_valid(self) -> None:
        """Plaintext config should have no validation errors."""
        config = KafkaConfig(security_protocol="PLAINTEXT")
        errors = validate_kafka_auth(config)
        assert errors == []

    def test_sasl_ssl_missing_credentials(self) -> None:
        """SASL_SSL without credentials should produce errors."""
        config = KafkaConfig(security_protocol="SASL_SSL")
        errors = validate_kafka_auth(config)
        assert len(errors) >= 3  # mechanism, username, password, ca_location

    def test_sasl_ssl_complete(self) -> None:
        """Complete SASL_SSL config should validate."""
        config = KafkaConfig(
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_username="admin",
            sasl_password="secret",
            ssl_ca_location="/certs/ca.pem",
        )
        errors = validate_kafka_auth(config)
        assert errors == []

    def test_mtls_incomplete(self) -> None:
        """mTLS with only cert (no key) should produce error."""
        config = KafkaConfig(
            security_protocol="SSL",
            ssl_ca_location="/certs/ca.pem",
            ssl_cert_location="/certs/client.pem",
        )
        errors = validate_kafka_auth(config)
        assert any("ssl_key_location" in e for e in errors)


class TestServerConfig:
    """Test top-level server configuration."""

    def test_default_readonly(self) -> None:
        """Server should default to read-only mode."""
        config = ServerConfig()
        assert config.allow_writes is False

    def test_default_log_level(self) -> None:
        """Default log level should be INFO."""
        config = ServerConfig()
        assert config.log_level == "INFO"
