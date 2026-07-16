"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import base64
import json
import time
from types import SimpleNamespace

import oci

from oracle.oci_vision_mcp_server.authentication import auth


def _jwt_with_expiry(exp: int) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode("utf-8"))
    return f"header.{payload.decode('ascii').rstrip('=')}.signature"


def test_ensure_session_auth_accepts_current_session(monkeypatch, tmp_path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text(_jwt_with_expiry(int(time.time()) + 3600), encoding="utf-8")

    monkeypatch.setenv("OCI_CONFIG_PROFILE", "DEFAULT")
    monkeypatch.setenv("OCI_REGION", "us-ashburn-1")
    monkeypatch.setattr(
        oci.config,
        "from_file",
        lambda profile_name: {
            "region": "us-ashburn-1",
            "security_token_file": str(token_file),
        },
    )
    monkeypatch.setattr(auth.subprocess, "run", lambda *args, **kwargs: None)

    auth.ensure_session_auth()


def test_ensure_session_auth_refreshes_expired_session(monkeypatch, tmp_path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text(_jwt_with_expiry(int(time.time()) - 60), encoding="utf-8")
    commands = []

    monkeypatch.setenv("OCI_CONFIG_PROFILE", "DEFAULT")
    monkeypatch.setenv("OCI_REGION", "us-ashburn-1")
    monkeypatch.setattr(
        oci.config,
        "from_file",
        lambda profile_name: {
            "region": "us-ashburn-1",
            "security_token_file": str(token_file),
        },
    )

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[:3] == ["oci", "session", "refresh"]:
            token_file.write_text(_jwt_with_expiry(int(time.time()) + 3600), encoding="utf-8")

    monkeypatch.setattr(auth.subprocess, "run", fake_run)

    auth.ensure_session_auth()

    assert commands == [["oci", "session", "refresh", "--profile", "DEFAULT"]]


def test_ensure_session_auth_runs_authenticate_when_enabled(monkeypatch, tmp_path) -> None:
    token_file = tmp_path / "token"
    commands = []

    monkeypatch.setenv("OCI_CONFIG_PROFILE", "DEFAULT")
    monkeypatch.setenv("OCI_REGION", "us-ashburn-1")
    monkeypatch.setenv("OCI_MCP_AUTO_AUTH", "1")
    monkeypatch.setattr(
        oci.config,
        "from_file",
        lambda profile_name: {
            "region": "us-ashburn-1",
            "security_token_file": str(token_file),
        },
    )

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[:3] == ["oci", "session", "authenticate"]:
            token_file.write_text(_jwt_with_expiry(int(time.time()) + 3600), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(auth.subprocess, "run", fake_run)

    auth.ensure_session_auth()

    assert commands == [
        ["oci", "session", "refresh", "--profile", "DEFAULT"],
        [
            "oci",
            "session",
            "authenticate",
            "--profile-name",
            "DEFAULT",
            "--region",
            "us-ashburn-1",
        ],
    ]


def test_ensure_session_auth_raises_when_authenticate_fails(monkeypatch, tmp_path) -> None:
    token_file = tmp_path / "token"

    monkeypatch.setenv("OCI_CONFIG_PROFILE", "DEFAULT")
    monkeypatch.setenv("OCI_REGION", "us-ashburn-1")
    monkeypatch.setenv("OCI_MCP_AUTO_AUTH", "1")
    monkeypatch.setattr(
        oci.config,
        "from_file",
        lambda profile_name: {
            "region": "us-ashburn-1",
            "security_token_file": str(token_file),
        },
    )
    monkeypatch.setattr(
        auth.subprocess,
        "run",
        lambda command, **kwargs: SimpleNamespace(returncode=1),
    )

    try:
        auth.ensure_session_auth()
    except RuntimeError as exc:
        assert "OCI session authentication failed" in str(exc)
        assert "oci session authenticate" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
