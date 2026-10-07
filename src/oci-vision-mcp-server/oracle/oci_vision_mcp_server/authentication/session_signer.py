"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass

import oci
from oracle_mcp_common import AuthOptions, AuthType, build_auth_context, resolve_config_file

from .. import __project__, __version__
from ..config.settings import get_resolved_config

_user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
_ADDITIONAL_UA = f"{_user_agent_name}/{__version__}"


@dataclass(frozen=True)
class SessionAuthContext:
    profile: str
    region: str | None


class SessionAuthenticationError(RuntimeError):
    code = "OCI_SESSION_AUTH_REQUIRED"
    retryable = True

    def __init__(self, message: str, *, context: SessionAuthContext) -> None:
        super().__init__(message)
        self.context = context


def session_config(*, profile: str | None = None, region: str | None = None):
    """Resolve the configured session-token context through oracle-mcp-common."""
    resolved_config = None if profile else get_resolved_config()
    selected_profile = profile or resolved_config.profile
    selected_region = region or (resolved_config.region if resolved_config else None)
    try:
        auth_context = build_auth_context(
            AuthOptions(
                auth_type=AuthType.SECURITY_TOKEN,
                profile_name=selected_profile,
                region=selected_region,
            )
        )
    except ValueError as exc:
        context = SessionAuthContext(profile=selected_profile, region=selected_region)
        raise _session_auth_error(
            context,
            str(exc),
        ) from exc
    config = {**auth_context.config, "additional_user_agent": _ADDITIONAL_UA}
    context = SessionAuthContext(profile=selected_profile, region=auth_context.region)
    return config, auth_context.signer, context


def session_auth_command(context: SessionAuthContext) -> str:
    """Return manual OCI CLI recovery guidance; this command is never executed."""
    region = context.region or "<region>"
    config_file = resolve_config_file()
    parts = [
        "oci",
        "session",
        "authenticate",
        "--profile-name",
        context.profile,
        "--region",
        region,
    ]
    if config_file != oci.config.DEFAULT_LOCATION:
        parts.extend(["--config-location", config_file])
    return " ".join(shlex.quote(part) for part in parts)


def session_auth_error_from_service_error(
    exc: Exception,
    *,
    profile: str | None = None,
    region: str | None = None,
) -> SessionAuthenticationError | None:
    if not _is_auth_failure(exc):
        return None

    resolved_config = None if profile else get_resolved_config()
    selected_profile = profile or resolved_config.profile
    selected_region = region or (
        resolved_config.region if resolved_config else _profile_region(selected_profile)
    )
    context = SessionAuthContext(profile=selected_profile, region=selected_region)
    return _session_auth_error(
        context,
        "OCI session token is expired, invalid, or not accepted by OCI Vision",
    )


def _session_auth_error(context: SessionAuthContext, reason: str) -> SessionAuthenticationError:
    command = session_auth_command(context)
    return SessionAuthenticationError(
        (
            f"{reason}. This MCP server uses OCI session-token authentication only. "
            f"Run `{command}` and retry the MCP tool."
        ),
        context=context,
    )


def _is_auth_failure(exc: Exception) -> bool:
    return (
        getattr(exc, "status", None) == 401
        or getattr(exc, "code", None) == "NotAuthenticated"
    )


def _profile_region(profile: str) -> str | None:
    """Read a selected profile's region only for session-repair guidance."""
    try:
        config = oci.config.from_file(
            file_location=resolve_config_file(),
            profile_name=profile,
        )
    except Exception:
        return None
    region = config.get("region")
    return str(region) if region else None
