"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import os
from logging import Logger
from typing import Any, Callable

import oci
from fastmcp.server.dependencies import get_access_token


def _get_http_config_and_signer(project: str, version: str) -> tuple[dict[str, str] | None, oci.signer.Signer | None]:
    if not (os.getenv("ORACLE_MCP_HOST") and os.getenv("ORACLE_MCP_PORT")):
        return None, None

    token = get_access_token()
    if token is None:
        raise RuntimeError("HTTP requests require an authenticated IDCS access token.")

    domain = os.getenv("IDCS_DOMAIN")
    client_id = os.getenv("IDCS_CLIENT_ID")
    client_secret = os.getenv("IDCS_CLIENT_SECRET")
    if not all((domain, client_id, client_secret)):
        raise RuntimeError(
            "HTTP requests require IDCS authentication. Set IDCS_DOMAIN, IDCS_CLIENT_ID, and IDCS_CLIENT_SECRET."
        )

    region = os.getenv("OCI_REGION")
    if not region:
        raise RuntimeError("HTTP requests require OCI_REGION.")

    user_agent_name = project.split("oracle.", 1)[1].split("-mcp-server", 1)[0]
    config = {"region": region, "additional_user_agent": f"{user_agent_name}/{version}"}
    return config, oci.auth.signers.TokenExchangeSigner(
        token.token,
        f"https://{domain}",
        client_id,
        client_secret,
        region=config.get("region"),
    )


def get_oci_config(project: str, version: str) -> dict[str, str]:
    """Resolve the OCI config used by this server without constructing a signer."""

    user_agent_name = project.split("oracle.", 1)[1].split("-mcp-server", 1)[0]
    if os.getenv("ORACLE_MCP_HOST") and os.getenv("ORACLE_MCP_PORT"):
        region = os.getenv("OCI_REGION")
        if not region:
            raise RuntimeError("HTTP requests require OCI_REGION.")
        return {"region": region, "additional_user_agent": f"{user_agent_name}/{version}"}

    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )
    config["additional_user_agent"] = f"{user_agent_name}/{version}"
    return config


def build_client(
    client_type: Callable[..., Any],
    *,
    project: str,
    version: str,
    logger: Logger,
) -> Any:
    """Create an OCI SDK client with the resolved config and signer."""

    config, signer = _get_http_config_and_signer(project, version)
    if config is None:
        config = get_oci_config(project, version)
        token_file = config.get("security_token_file")
        if token_file:
            key_file = config.get("key_file")
            if not key_file:
                raise RuntimeError(
                    "Stdio transport OCI session-token profiles require both key_file and security_token_file."
                )
            private_key = oci.signer.load_private_key_from_file(key_file)
            with open(os.path.expanduser(token_file), "r", encoding="utf-8") as token:
                signer = oci.auth.signers.SecurityTokenSigner(token.read(), private_key)
        else:
            try:
                oci.config.validate_config(config)
            except ValueError as exc:
                raise RuntimeError(
                    "Stdio transport requires a valid OCI CLI profile using either API-key auth "
                    "or session-token auth. API-key profiles must include key_file, fingerprint, "
                    "user, tenancy, and region; session-token profiles must include security_token_file."
                ) from exc

    kwargs: dict[str, object] = {
        "circuit_breaker_strategy": oci.circuit_breaker.CircuitBreakerStrategy(
            failure_threshold=int(os.getenv("OCI_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "10")),
            recovery_timeout=int(os.getenv("OCI_CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30")),
        ),
        "circuit_breaker_callback": lambda exc: logger.warning("Circuit breaker triggered: %s", exc),
    }
    if signer is not None:
        kwargs["signer"] = signer
    return client_type(config, **kwargs)
