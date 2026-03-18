"""Authentication helpers for Kafka and OCI connections."""

from __future__ import annotations

from oracle.oci_kafka_mcp_server.config import KafkaConfig


def validate_kafka_auth(config: KafkaConfig) -> list[str]:
    """Validate that Kafka auth configuration is consistent.

    Returns a list of validation errors (empty if valid).
    """
    errors: list[str] = []

    if config.security_protocol in ("SASL_SSL", "SASL_PLAINTEXT"):
        if not config.sasl_mechanism:
            errors.append(
                f"sasl_mechanism is required when security_protocol={config.security_protocol}"
            )
        if not config.sasl_username:
            errors.append("sasl_username is required for SASL authentication")
        if not config.sasl_password:
            errors.append("sasl_password is required for SASL authentication")

    if config.security_protocol in ("SSL", "SASL_SSL"):
        if not config.ssl_ca_location:
            errors.append(
                f"ssl_ca_location is required when security_protocol={config.security_protocol}"
            )

    if config.ssl_cert_location and not config.ssl_key_location:
        errors.append("ssl_key_location is required when ssl_cert_location is provided (mTLS)")

    if config.ssl_key_location and not config.ssl_cert_location:
        errors.append("ssl_cert_location is required when ssl_key_location is provided (mTLS)")

    return errors
