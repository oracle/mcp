# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import pytest
from oracle_mcp_common import AuthContext, AuthType

from oracle.oci_language_mcp_server import auth
from oracle.oci_language_mcp_server.auth import build_auth_context
from oracle.oci_language_mcp_server.config import LanguageMcpSettings


@pytest.mark.parametrize(
    ("mode", "expected_type", "configured_region", "resolved_region"),
    [
        ("session", AuthType.SECURITY_TOKEN, None, "us-chicago-1"),
        ("instance_principal", AuthType.INSTANCE_PRINCIPAL, None, "us-ashburn-1"),
        ("resource_principal", AuthType.RESOURCE_PRINCIPAL, "us-phoenix-1", "us-phoenix-1"),
    ],
)
def test_auth_uses_shared_context_for_each_supported_mode(
    monkeypatch, mode, expected_type, configured_region, resolved_region
) -> None:
    signer = object()
    options_seen = []

    def fake_shared_auth(options):
        options_seen.append(options)
        return AuthContext(
            expected_type,
            {"region": resolved_region},
            signer,
            None,
            resolved_region,
            "LANG",
        )

    monkeypatch.setattr(auth, "build_shared_auth_context", fake_shared_auth)

    context = build_auth_context(
        LanguageMcpSettings(
            oci_auth_mode=mode,
            region=configured_region,
            oci_config_file="/tmp/language-oci-config",
            oci_config_profile="LANG",
        )
    )

    assert context.signer is signer
    assert context.config["region"] == resolved_region
    assert options_seen[-1].auth_type is expected_type
    assert options_seen[-1].config_file == "/tmp/language-oci-config"
    assert options_seen[-1].profile_name == "LANG"
    assert options_seen[-1].region == configured_region


def test_auth_allows_service_endpoint_without_resolved_region(monkeypatch) -> None:
    signer = object()
    monkeypatch.setattr(
        auth,
        "build_shared_auth_context",
        lambda _options: AuthContext(AuthType.RESOURCE_PRINCIPAL, {}, signer, None, None, None),
    )

    context = build_auth_context(
        LanguageMcpSettings(
            oci_auth_mode="resource_principal",
            oci_service_endpoint="https://language.example.test",
        )
    )

    assert context.config == {}


def test_auth_request_region_overrides_configured_region(monkeypatch) -> None:
    options_seen = []
    signer = object()

    def fake_shared_auth(options):
        options_seen.append(options)
        return AuthContext(
            AuthType.RESOURCE_PRINCIPAL,
            {"region": "us-ashburn-1"},
            signer,
            None,
            "us-ashburn-1",
            None,
        )

    monkeypatch.setattr(auth, "build_shared_auth_context", fake_shared_auth)

    context = build_auth_context(
        LanguageMcpSettings(oci_auth_mode="resource_principal", region="us-phoenix-1"),
        region="us-ashburn-1",
    )

    assert context.config["region"] == "us-ashburn-1"
    assert options_seen[-1].region == "us-ashburn-1"


def test_auth_hides_shared_authentication_error(monkeypatch) -> None:
    monkeypatch.setattr(
        auth,
        "build_shared_auth_context",
        lambda _options: (_ for _ in ()).throw(ValueError("token file /private/secret is invalid")),
    )

    with pytest.raises(auth.OciAuthenticationError) as exc_info:
        build_auth_context(LanguageMcpSettings(oci_auth_mode="session"))

    assert "session authentication could not be initialized" in str(exc_info.value)
    assert "/private/secret" not in str(exc_info.value)
