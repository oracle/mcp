"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os

from pydantic import BaseModel, ConfigDict, Field


class OciDocumentUnderstandingConfig(BaseModel):
    """Runtime configuration for OCI provider setup."""

    model_config = ConfigDict(frozen=True)

    runtime_mode: str = Field(..., description="Runtime mode: stub, local, or prod.")
    region: str = Field(..., description="OCI region used for Document Understanding requests.")
    endpoint: str | None = Field(None, description="Optional OCI Document Understanding endpoint override.")
    auth_mode: str = Field(..., description="OCI auth mode.")
    default_compartment_id: str | None = Field(None, description="Default compartment OCID for OCI Document Understanding calls.")
    config_file_path: str | None = Field(None, description="Optional OCI config file path.")
    profile: str = Field(..., description="OCI config profile name.")

    @staticmethod
    def from_environment() -> "OciDocumentUnderstandingConfig":
        """Builds provider configuration from environment variables."""
        runtime_mode = _normalize_mode(_env("DOCUMENT_MCP_MODE", "local"))
        auth_mode = _normalize_auth(_env("OCI_AUTH_MODE", _default_auth_mode(runtime_mode)))
        return OciDocumentUnderstandingConfig(
            runtime_mode=runtime_mode,
            region=_env("OCI_REGION", "us-ashburn-1"),
            endpoint=_env("OCI_DOCUMENT_ENDPOINT", None),
            auth_mode=auth_mode,
            default_compartment_id=_env("OCI_COMPARTMENT_ID", None),
            config_file_path=_env("OCI_CONFIG_FILE", None),
            profile=_env("OCI_CONFIG_PROFILE", "DEFAULT"),
        )


def _env(name: str, default: str | None) -> str | None:
    """Reads an environment variable and falls back when absent or blank."""
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else default


def _normalize_mode(value: str | None) -> str:
    """Parses environment runtime mode aliases."""
    normalized = (value or "local").strip().replace("_", "-").lower()
    if normalized in {"stub", "test", "mock"}:
        return "stub"
    if normalized in {"local", "dev", "development"}:
        return "local"
    if normalized in {"prod", "production", "compute"}:
        return "prod"
    raise ValueError(f"Unsupported DOCUMENT_MCP_MODE: {value}")


def _normalize_auth(value: str | None) -> str:
    """Parses environment auth mode aliases."""
    normalized = (value or "").strip().replace("_", "-").lower()
    if normalized in {"session-token", "sessiontoken", "local"}:
        return "session-token"
    if normalized in {"instance-principal", "instanceprincipal", "prod", "production"}:
        return "instance-principal"
    if normalized in {"api-key", "apikey", "config-file", "config"}:
        return "api-key"
    if normalized in {"none", "stub"}:
        return "none"
    raise ValueError(f"Unsupported OCI_AUTH_MODE: {value}")


def _default_auth_mode(runtime_mode: str) -> str:
    """Returns the default auth mode for a runtime mode."""
    if runtime_mode == "stub":
        return "none"
    if runtime_mode == "prod":
        return "instance-principal"
    return "session-token"
