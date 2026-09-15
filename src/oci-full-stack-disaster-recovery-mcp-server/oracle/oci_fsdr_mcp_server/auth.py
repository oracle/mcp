"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

OCI client factory supporting API key and session token authentication.

Authentication is controlled by the OCI_AUTH_TYPE environment variable:
  - "api_key"        (default): standard OCI config file credentials
  - "security_token": OCI CLI session token (for interactive/cloud-shell sessions)
"""

from __future__ import annotations

import os
from typing import Dict

import oci

from . import __project__, __version__
from .consts import DEFAULT_OCI_AUTH_TYPE, DEFAULT_OCI_CONFIG_FILE

_user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
_ADDITIONAL_UA = f"{_user_agent_name}/{__version__}"

_client_cache: Dict[str, oci.disaster_recovery.DisasterRecoveryClient] = {}


def get_dr_client(profile: str) -> oci.disaster_recovery.DisasterRecoveryClient:
    """Return a cached DisasterRecoveryClient for the given OCI config profile.

    Created lazily on first use to avoid any stdout writes before the MCP
    stdio transport is active.
    """
    if profile not in _client_cache:
        _client_cache[profile] = _make_client(profile)
    return _client_cache[profile]


def _make_client(profile: str) -> oci.disaster_recovery.DisasterRecoveryClient:
    if DEFAULT_OCI_AUTH_TYPE == "security_token":
        return _make_security_token_client(profile)
    return _make_api_key_client(profile)


def _make_api_key_client(profile: str) -> oci.disaster_recovery.DisasterRecoveryClient:
    """Standard OCI config file / API key authentication."""
    config = oci.config.from_file(
        file_location=DEFAULT_OCI_CONFIG_FILE, profile_name=profile
    )
    oci.config.validate_config(config)
    config["additional_user_agent"] = _ADDITIONAL_UA
    return oci.disaster_recovery.DisasterRecoveryClient(config)


def _make_security_token_client(profile: str) -> oci.disaster_recovery.DisasterRecoveryClient:
    """OCI CLI session token authentication (security_token auth type).

    Reads the token file path and private key from the OCI config profile.
    Falls back to environment variables OCI_SECURITY_TOKEN_FILE and OCI_KEY_FILE.
    """
    config = oci.config.from_file(
        file_location=DEFAULT_OCI_CONFIG_FILE, profile_name=profile
    )

    token_file = os.path.expanduser(
        config.get("security_token_file")
        or os.getenv("OCI_SECURITY_TOKEN_FILE", "~/.oci/token")
    )
    key_file = os.path.expanduser(
        config.get("key_file")
        or os.getenv("OCI_KEY_FILE", "~/.oci/oci_api_key.pem")
    )

    with open(token_file, encoding="utf-8") as f:
        token = f.read().strip()

    signer = oci.auth.signers.SecurityTokenSigner(
        token=token,
        private_key_file_location=key_file,
    )
    return oci.disaster_recovery.DisasterRecoveryClient(
        config={"additional_user_agent": _ADDITIONAL_UA}, signer=signer
    )
