"""Configuration management for OCI Kafka MCP Server."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class KafkaConfig(BaseSettings):
    """Kafka connection configuration, loaded from environment variables."""

    model_config = {"env_prefix": "KAFKA_"}

    bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Comma-separated list of Kafka broker addresses",
    )
    security_protocol: str = Field(
        default="PLAINTEXT",
        description="Security protocol: PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL",
    )
    sasl_mechanism: str | None = Field(
        default=None,
        description="SASL mechanism: SCRAM-SHA-512, SCRAM-SHA-256, PLAIN",
    )
    sasl_username: str | None = Field(default=None, description="SASL username")
    sasl_password: str | None = Field(default=None, description="SASL password")
    ssl_ca_location: str | None = Field(default=None, description="CA certificate path for TLS")
    ssl_cert_location: str | None = Field(
        default=None, description="Client certificate path for mTLS"
    )
    ssl_key_location: str | None = Field(default=None, description="Client key path for mTLS")

    @property
    def is_configured(self) -> bool:
        """Return True if a Kafka cluster has been explicitly configured.

        Returns False when only the default localhost:9092 placeholder is set,
        indicating the user needs to call oci_kafka_configure_connection first.
        """
        return self.bootstrap_servers != "localhost:9092"

    def to_confluent_config(self) -> dict[str, str]:
        """Convert to confluent-kafka configuration dictionary."""
        config: dict[str, str] = {
            "bootstrap.servers": self.bootstrap_servers,
            "security.protocol": self.security_protocol,
        }
        if self.sasl_mechanism:
            config["sasl.mechanism"] = self.sasl_mechanism
        if self.sasl_username:
            config["sasl.username"] = self.sasl_username
        if self.sasl_password:
            config["sasl.password"] = self.sasl_password
        if self.ssl_ca_location:
            config["ssl.ca.location"] = self.ssl_ca_location
        if self.ssl_cert_location:
            config["ssl.certificate.location"] = self.ssl_cert_location
        if self.ssl_key_location:
            config["ssl.key.location"] = self.ssl_key_location
        return config


class OciConfig(BaseSettings):
    """OCI SDK configuration, loaded from environment variables."""

    model_config = {"env_prefix": "OCI_"}

    config_file: str = Field(default="~/.oci/config", description="OCI config file path")
    profile: str = Field(default="DEFAULT", description="OCI config profile name")
    compartment_id: str | None = Field(default=None, description="OCI compartment OCID")
    cluster_id: str | None = Field(default=None, description="OCI Kafka cluster (stream pool) OCID")


class ServerConfig(BaseSettings):
    """Top-level server configuration."""

    allow_writes: bool = Field(
        default=False,
        description="Enable write tools (createTopic, deleteTopic, etc.)",
    )
    log_level: str = Field(default="INFO", description="Logging level")

    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    oci: OciConfig = Field(default_factory=OciConfig)


def load_config() -> ServerConfig:
    """Load configuration from environment variables."""
    return ServerConfig()
