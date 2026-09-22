"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from oracle_mcp_common import AuthOptions, AuthType
from oracle_mcp_common import build_auth_context as build_shared_auth_context

from .config import LanguageMcpSettings


class OciAuthenticationError(RuntimeError):
    """Actionable, payload-safe OCI authentication failure."""

    code = "OCI_AUTHENTICATION_REQUIRED"
    retryable = False


@dataclass(frozen=True)
class OciAuthContext:
    config: dict[str, Any]
    signer: Any


def build_auth_context(
    settings: LanguageMcpSettings,
    *,
    region: str | None = None,
) -> OciAuthContext:
    """Build a signer and minimal OCI client config for the selected mode."""

    selected_region = region or settings.region
    try:
        auth_context = build_shared_auth_context(
            AuthOptions(
                auth_type=_auth_type_for(settings.oci_auth_mode),
                config_file=os.path.expanduser(settings.oci_config_file),
                profile_name=settings.oci_config_profile,
                region=selected_region,
            )
        )
    except Exception as exc:
        raise OciAuthenticationError(
            f"OCI {settings.oci_auth_mode} authentication could not be initialized."
        ) from exc

    selected_region = auth_context.region
    config = dict(auth_context.config)
    if not selected_region and not settings.oci_service_endpoint:
        raise OciAuthenticationError(
            "OCI region is required. Set LANGUAGE_MCP_REGION or provide options.region."
        )
    if selected_region:
        config["region"] = selected_region
    return OciAuthContext(
        config=config,
        signer=auth_context.signer,
    )


def _auth_type_for(mode: str) -> AuthType:
    """Map Language's stable auth-mode settings to shared auth types."""
    return {
        "session": AuthType.SECURITY_TOKEN,
        "instance_principal": AuthType.INSTANCE_PRINCIPAL,
        "resource_principal": AuthType.RESOURCE_PRINCIPAL,
    }[mode]
