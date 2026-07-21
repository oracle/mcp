"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import base64
import binascii
import json
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import oci

from ..config.settings import ResolvedMcpConfig, get_resolved_config


@dataclass(frozen=True)
class SessionConfig:
    profile: str
    region: str | None
    security_token_file: str | None


def ensure_session_auth() -> None:
    resolved_config = get_resolved_config(persist_generated_profile=True)
    config = _load_session_config(resolved_config)

    if _session_is_current(config, skew_seconds=resolved_config.token_expiry_skew_seconds):
        return

    if resolved_config.refresh_session and config.security_token_file:
        _run_session_refresh(config.profile, executable=resolved_config.session_auth_command)
        config = _load_session_config(resolved_config)
        if _session_is_current(config, skew_seconds=resolved_config.token_expiry_skew_seconds):
            return

    if resolved_config.auto_auth:
        region = config.region or resolved_config.region
        if not region:
            raise RuntimeError(
                "OCI region is required before automatic session authentication can run. "
                "Set OCI_REGION in your MCP client environment and restart the MCP server."
            )
        _run_session_authenticate(
            config.profile,
            region,
            executable=resolved_config.session_auth_command,
        )
        config = _load_session_config(resolved_config)
        if _session_is_current(config, skew_seconds=resolved_config.token_expiry_skew_seconds):
            return

    command = _session_authenticate_command(
        config.profile,
        config.region or resolved_config.region,
        executable=resolved_config.session_auth_command,
    )
    raise RuntimeError(f"run `{command}` and restart the MCP server")


def _load_session_config(resolved_config: ResolvedMcpConfig) -> SessionConfig:
    try:
        raw_config = oci.config.from_file(profile_name=resolved_config.profile)
    except Exception:
        return SessionConfig(
            profile=resolved_config.profile,
            region=resolved_config.region,
            security_token_file=None,
        )

    selected_region = resolved_config.region or raw_config.get("region")
    return SessionConfig(
        profile=resolved_config.profile,
        region=selected_region,
        security_token_file=raw_config.get("security_token_file"),
    )


def _session_is_current(config: SessionConfig, *, skew_seconds: int) -> bool:
    if not config.security_token_file:
        return False
    token_path = Path(config.security_token_file).expanduser()
    if not token_path.is_file():
        return False

    try:
        token = token_path.read_text(encoding="utf-8").strip()
    except OSError:
        return False

    expires_at = _jwt_expiry(token)
    if expires_at is None:
        return False
    return expires_at > time.time() + skew_seconds


def _jwt_expiry(token: str) -> int | None:
    parts = token.split(".")
    if len(parts) < 2:
        return None
    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    try:
        decoded = base64.urlsafe_b64decode(f"{payload}{padding}")
        data = json.loads(decoded)
    except (binascii.Error, ValueError, json.JSONDecodeError):
        return None
    exp = data.get("exp")
    return exp if isinstance(exp, int) else None


def _run_session_refresh(profile: str, *, executable: str) -> None:
    command = [executable, "session", "refresh", "--profile", profile]
    # Refresh can fail for expired sessions; authenticate may still repair it.
    subprocess.run(command, check=False, stdin=sys.stdin, stdout=sys.stderr, stderr=sys.stderr)


def _run_session_authenticate(profile: str, region: str, *, executable: str) -> None:
    command = [
        executable,
        "session",
        "authenticate",
        "--profile-name",
        profile,
    ]
    command.extend(["--region", region])
    completed = subprocess.run(
        command,
        check=False,
        stdin=sys.stdin,
        stdout=sys.stderr,
        stderr=sys.stderr,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"OCI session authentication failed. Run `{shlex.join(command)}` and retry.")


def _session_authenticate_command(profile: str, region: str | None, *, executable: str) -> str:
    return shlex.join(
        [
            executable,
            "session",
            "authenticate",
            "--profile-name",
            profile,
            "--region",
            region or "<region>",
        ]
    )
