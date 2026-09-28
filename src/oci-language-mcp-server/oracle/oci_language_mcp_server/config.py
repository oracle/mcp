# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""Environment-driven server and OCI Language configuration."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

import oci
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import TOOL_NAMES

_DEFAULT_ENV_FILE = os.path.expanduser("~/.oci-language-mcp.env")


class LanguageMcpSettings(BaseSettings):
    """Validated runtime configuration.

    All values can be overridden with ``LANGUAGE_MCP_*`` environment variables.
    Sensitive OCI credentials are never represented by this model; the selected
    OCI signer obtains them from the standard OCI authentication mechanism.
    """

    model_config = SettingsConfigDict(
        env_prefix="LANGUAGE_MCP_",
        env_file=_DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    server_name: str = "oci-language-mcp"
    host: str = "127.0.0.1"
    port: int = Field(default=8080, ge=1, le=65535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "console"] = "json"
    transport: Literal["stdio", "streamable-http"] = "streamable-http"
    deployment_mode: Literal["local", "remote"] = "local"
    allowed_hosts: str | None = None
    allowed_origins: str | None = None
    http_auth_mode: Literal["oauth", "token-file"] = "token-file"
    auth_token_file: str | None = None
    public_base_url: str | None = None
    oauth_issuer: str | None = None
    oauth_jwks_uri: str | None = None
    oauth_audience: str | None = None
    oauth_required_scopes: str = "oci-language.invoke"
    oauth_algorithm: Literal["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"] = (
        "RS256"
    )
    request_body_limit_bytes: int = Field(default=262_144, ge=16_384, le=1_048_576)
    remote_requests_per_minute: int = Field(default=60, ge=1, le=10_000)

    max_inflight_requests: int = Field(default=8, ge=1, le=64)
    capacity_acquire_timeout_seconds: float = Field(default=0.25, gt=0, le=10)
    oci_connect_timeout_seconds: float = Field(default=5.0, gt=0, le=60)
    oci_read_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    tool_timeout_seconds: float = Field(default=40.0, gt=0, le=360)

    oci_auth_mode: Literal["resource_principal", "instance_principal", "session"] = (
        "resource_principal"
    )
    region: str | None = None
    compartment_id: str | None = None
    oci_config_file: str = "~/.oci/config"
    oci_config_profile: str = "DEFAULT"
    oci_service_endpoint: str | None = None
    enabled_tools: str = ",".join(TOOL_NAMES)

    @model_validator(mode="after")
    def validate_remote_security(self) -> LanguageMcpSettings:
        configured_tools = _split_csv(self.enabled_tools)
        unknown_tools = sorted(set(configured_tools).difference(TOOL_NAMES))
        if unknown_tools:
            raise ValueError("Unknown enabled tool(s): " + ", ".join(unknown_tools))
        if not configured_tools:
            raise ValueError("At least one OCI Language tool must be enabled.")
        if self.region and not oci.regions.is_region(self.region):
            raise ValueError("LANGUAGE_MCP_REGION must be a recognized OCI region identifier.")
        if (
            self.transport == "streamable-http"
            and self.deployment_mode == "local"
            and self.host not in {"127.0.0.1", "::1", "localhost"}
        ):
            raise ValueError("Local Streamable HTTP must bind to a loopback host.")
        if self.deployment_mode == "remote":
            required = [
                ("allowed_hosts", self.allowed_hosts),
                ("allowed_origins", self.allowed_origins),
            ]
            if self.http_auth_mode == "oauth":
                required.extend(
                    [
                        ("public_base_url", self.public_base_url),
                        ("oauth_issuer", self.oauth_issuer),
                        ("oauth_jwks_uri", self.oauth_jwks_uri),
                        ("oauth_audience", self.oauth_audience),
                    ]
                )
            else:
                required.append(("auth_token_file", self.auth_token_file))
            missing = [name for name, value in required if not value]
            if missing:
                raise ValueError(
                    "Remote mode requires: " + ", ".join(sorted(missing))
                )
            if self.http_auth_mode == "oauth":
                for name, value in (
                    ("public_base_url", self.public_base_url),
                    ("oauth_issuer", self.oauth_issuer),
                    ("oauth_jwks_uri", self.oauth_jwks_uri),
                ):
                    if urlsplit(value or "").scheme != "https":
                        raise ValueError(f"Remote OAuth {name} must use HTTPS.")
                if not self.parsed_oauth_required_scopes():
                    raise ValueError("Remote OAuth requires at least one scope.")
        return self

    def parsed_allowed_hosts(self) -> tuple[str, ...]:
        if self.deployment_mode == "local":
            return ("127.0.0.1", "localhost", "[::1]", "::1")
        return _split_csv(self.allowed_hosts)

    def parsed_allowed_origins(self) -> tuple[str, ...]:
        if self.deployment_mode == "local":
            return (
                "http://127.0.0.1",
                "http://localhost",
                "http://[::1]",
            )
        return _split_csv(self.allowed_origins)

    def parsed_oauth_required_scopes(self) -> tuple[str, ...]:
        return _split_space_or_csv(self.oauth_required_scopes)

    def parsed_enabled_tools(self) -> tuple[str, ...]:
        selected = set(_split_csv(self.enabled_tools))
        return tuple(tool for tool in TOOL_NAMES if tool in selected)


@lru_cache(maxsize=1)
def get_settings() -> LanguageMcpSettings:
    """Return the process-wide immutable settings instance."""

    return LanguageMcpSettings()


def clear_settings_cache() -> None:
    """Clear cached settings for tests and controlled process reconfiguration."""

    get_settings.cache_clear()


def _split_csv(value: str | None) -> tuple[str, ...]:
    return tuple(item.strip().rstrip("/") for item in (value or "").split(",") if item.strip())


def _split_space_or_csv(value: str | None) -> tuple[str, ...]:
    return tuple(
        item
        for item in (value or "").replace(",", " ").split()
        if item
    )
