"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass

import oci

from .. import __project__, __version__
from ..config.consts import DEFAULT_SESSION_AUTH_COMMAND, SESSION_AUTH_COMMAND_ENV
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
    resolved_config = None if profile and region else get_resolved_config()
    selected_profile = profile or resolved_config.profile
    config = oci.config.from_file(profile_name=selected_profile)
    selected_region = region or resolved_config.region
    if selected_region:
        config["region"] = selected_region
    config["additional_user_agent"] = _ADDITIONAL_UA
    context = SessionAuthContext(profile=selected_profile, region=config.get("region"))

    security_token_file = config.get("security_token_file")
    key_file = config.get("key_file")
    if not security_token_file or not key_file:
        raise _session_auth_error(
            context,
            "OCI config profile is not a session-token profile",
        )

    try:
        with open(security_token_file, encoding="utf-8") as token_file:
            token = token_file.read()
        private_key = oci.signer.load_private_key_from_file(key_file)
    except OSError as exc:
        raise _session_auth_error(
            context,
            f"OCI session material could not be read: {exc}",
        ) from exc

    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return config, signer, context


def session_auth_command(context: SessionAuthContext) -> str:
    executable = os.getenv(SESSION_AUTH_COMMAND_ENV, DEFAULT_SESSION_AUTH_COMMAND)
    region = context.region or "<region>"
    parts = [
        executable,
        "session",
        "authenticate",
        "--profile-name",
        context.profile,
        "--region",
        region,
    ]
    return " ".join(shlex.quote(part) for part in parts)


def session_auth_error_from_service_error(
    exc: Exception,
    *,
    profile: str | None = None,
    region: str | None = None,
) -> SessionAuthenticationError | None:
    if not _is_auth_failure(exc):
        return None

    resolved_config = None if profile and region else get_resolved_config()
    selected_profile = profile or resolved_config.profile
    selected_region = region or resolved_config.region
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
