"""Connection configuration tools for OCI Kafka MCP Server."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from oracle.oci_kafka_mcp_server.audit.logger import audit
from oracle.oci_kafka_mcp_server.config import KafkaConfig
from oracle.oci_kafka_mcp_server.kafka.admin_client import KafkaAdminClient
from oracle.oci_kafka_mcp_server.kafka.connection import CircuitBreaker
from oracle.oci_kafka_mcp_server.kafka.consumer_client import KafkaConsumerClient

_DEFAULT_PERSIST_PATH = Path.home() / ".oci" / "kafka-mcp-connection.env"


def _sanitize_env_value(value: str) -> str:
    """Sanitize a value for safe inclusion in a .env file.

    Rejects values containing characters that could be dangerous
    if the file is accidentally sourced as a shell script.
    """
    # Reject values with shell-dangerous characters
    dangerous_chars = set("`$\\\"'\n\r")
    found = dangerous_chars.intersection(value)
    if found:
        escaped_chars = ", ".join(repr(c) for c in sorted(found))
        raise ValueError(
            f"Value contains unsafe characters ({escaped_chars}) "
            "that are not allowed in .env files."
        )
    return value


def _write_env_file(path: Path, config: KafkaConfig) -> None:
    """Write connection details to a .env file (non-executable format).

    Uses plain KEY=VALUE format without shell 'export' directives.
    This file should be loaded by application code (e.g. python-dotenv),
    NOT sourced as a shell script.
    """
    lines = [
        "# OCI Kafka MCP — connection configuration",
        "# Load with python-dotenv or pass to Docker/Podman — do NOT source in shell.",
        f"KAFKA_BOOTSTRAP_SERVERS={_sanitize_env_value(config.bootstrap_servers)}",
        f"KAFKA_SECURITY_PROTOCOL={_sanitize_env_value(config.security_protocol)}",
    ]
    if config.sasl_mechanism:
        lines.append(f"KAFKA_SASL_MECHANISM={_sanitize_env_value(config.sasl_mechanism)}")
    if config.sasl_username:
        lines.append(f"KAFKA_SASL_USERNAME={_sanitize_env_value(config.sasl_username)}")
    if config.sasl_password:
        lines.append(f"KAFKA_SASL_PASSWORD={_sanitize_env_value(config.sasl_password)}")
    if config.ssl_ca_location:
        lines.append(f"KAFKA_SSL_CA_LOCATION={_sanitize_env_value(config.ssl_ca_location)}")
    if config.ssl_cert_location:
        lines.append(f"KAFKA_SSL_CERT_LOCATION={_sanitize_env_value(config.ssl_cert_location)}")
    if config.ssl_key_location:
        lines.append(f"KAFKA_SSL_KEY_LOCATION={_sanitize_env_value(config.ssl_key_location)}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    # Restrict file permissions — contains credentials
    os.chmod(path, 0o600)


def register_connection_tools(
    mcp: FastMCP,
    admin_client: KafkaAdminClient,
    consumer_client: KafkaConsumerClient,
    circuit_breaker: CircuitBreaker,
) -> None:
    """Register connection configuration tools with the MCP server."""

    @mcp.tool()
    def oci_kafka_configure_connection(
        bootstrap_servers: str,
        security_protocol: str = "SASL_SSL",
        sasl_mechanism: str | None = None,
        sasl_username: str | None = None,
        sasl_password: str | None = None,
        ssl_ca_location: str | None = None,
        persist: bool = False,
    ) -> str:
        """Configure or update the Kafka cluster connection details at runtime.

        Use this tool when:
        - No Kafka cluster is configured yet and other tools return a 'not configured' error.
        - The user wants to switch to a different Kafka cluster.
        - The user provides new credentials or bootstrap servers.

        The new connection takes effect immediately — no server restart required.
        All existing clients are reset and will reconnect on the next tool call.

        Args:
            bootstrap_servers: Kafka broker address(es), e.g.
                'bootstrap-clstr-XXXXX.kafka.us-chicago-1.oci.oraclecloud.com:9092'
            security_protocol: PLAINTEXT, SSL, SASL_PLAINTEXT, or SASL_SSL (default: SASL_SSL)
            sasl_mechanism: SCRAM-SHA-512, SCRAM-SHA-256, or PLAIN (required for SASL_*)
            sasl_username: SASL username (required for SASL_*)
            sasl_password: SASL password (required for SASL_*)
            ssl_ca_location: Path to CA certificate bundle for TLS verification.
                If not set and security_protocol is SASL_SSL or SSL, the system
                default CA bundle is used.
            persist: If True, save the connection details to
                ~/.oci/kafka-mcp-connection.env so they survive server restarts.
                Load them with python-dotenv or pass to Docker/Podman.
        """
        new_config = KafkaConfig(
            bootstrap_servers=bootstrap_servers,
            security_protocol=security_protocol,
            sasl_mechanism=sasl_mechanism,
            sasl_username=sasl_username,
            sasl_password=sasl_password,
            ssl_ca_location=ssl_ca_location,
        )

        admin_client.reconfigure(new_config)
        consumer_client.reconfigure(new_config)
        circuit_breaker.reset()

        result: dict[str, Any] = {
            "status": "configured",
            "bootstrap_servers": bootstrap_servers,
            "security_protocol": security_protocol,
            "sasl_mechanism": sasl_mechanism,
            "authenticated": sasl_username is not None,
            "tls_ca_set": ssl_ca_location is not None,
        }

        if persist:
            try:
                _write_env_file(_DEFAULT_PERSIST_PATH, new_config)
                result["persisted_to"] = str(_DEFAULT_PERSIST_PATH)
                result["persist_note"] = (
                    f"Connection saved to {_DEFAULT_PERSIST_PATH}. "
                    "Load with python-dotenv or --env-file in Docker/Podman."
                )
            except OSError as e:
                result["persist_error"] = f"Could not write env file: {e}"

        audit_params = {"bootstrap_servers": bootstrap_servers}
        with audit.audit_tool("oci_kafka_configure_connection", audit_params) as entry:
            entry.result_status = "success"

        return json.dumps(result, indent=2)

    @mcp.tool()
    def oci_kafka_get_connection_info() -> str:
        """Show the current Kafka connection configuration.

        Returns connection details with the password masked. Use this to:
        - Check whether a cluster is already configured before calling other tools.
        - Verify which cluster the server is connected to.
        - Confirm security settings before troubleshooting connectivity issues.

        If 'configured' is false, call oci_kafka_configure_connection first.
        """
        config = admin_client._config

        with audit.audit_tool("oci_kafka_get_connection_info", {}) as entry:
            entry.result_status = "success"
            return json.dumps(
                {
                    "configured": config.is_configured,
                    "bootstrap_servers": config.bootstrap_servers,
                    "security_protocol": config.security_protocol,
                    "sasl_mechanism": config.sasl_mechanism,
                    "sasl_username": config.sasl_username,
                    "password_set": config.sasl_password is not None,
                    "ssl_ca_location": config.ssl_ca_location,
                    "action_if_not_configured": (
                        None
                        if config.is_configured
                        else (
                            "Ask the user for the following details, then call "
                            "oci_kafka_configure_connection: "
                            "(1) bootstrap_servers — broker address ending in :9092, "
                            "(2) security_protocol — usually SASL_SSL, "
                            "(3) sasl_mechanism — usually SCRAM-SHA-512, "
                            "(4) sasl_username, "
                            "(5) sasl_password. "
                            "All five values are shown on the OCI Console > "
                            "Streaming with Apache Kafka > Cluster Details page."
                        )
                    ),
                },
                indent=2,
            )
