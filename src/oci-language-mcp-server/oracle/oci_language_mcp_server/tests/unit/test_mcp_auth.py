# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import pytest
from fastmcp.server.auth import JWTVerifier
from fastmcp.server.auth.providers.jwt import RSAKeyPair
from pydantic import ValidationError

from oracle.oci_language_mcp_server.config import LanguageMcpSettings
from oracle.oci_language_mcp_server.mcp_auth import build_mcp_auth


def test_local_and_token_file_modes_do_not_build_oauth_provider() -> None:
    assert build_mcp_auth(LanguageMcpSettings()) is None


def test_remote_oauth_configuration_is_https_and_scope_bound() -> None:
    with pytest.raises(ValidationError, match="must use HTTPS"):
        LanguageMcpSettings(
            deployment_mode="remote",
            http_auth_mode="oauth",
            allowed_hosts="mcp.example.test",
            allowed_origins="https://agent.example.test",
            public_base_url="http://mcp.example.test",
            oauth_issuer="https://identity.example.test",
            oauth_jwks_uri="https://identity.example.test/jwks",
            oauth_audience="https://mcp.example.test/mcp",
        )

    settings = LanguageMcpSettings(
        deployment_mode="remote",
        http_auth_mode="oauth",
        allowed_hosts="mcp.example.test",
        allowed_origins="https://agent.example.test",
        public_base_url="https://mcp.example.test",
        oauth_issuer="https://identity.example.test",
        oauth_jwks_uri="https://identity.example.test/jwks",
        oauth_audience="https://mcp.example.test/mcp",
        oauth_required_scopes="oci-language.invoke, audit.read",
    )
    provider = build_mcp_auth(settings)

    assert provider is not None
    assert provider.token_verifier.audience == "https://mcp.example.test/mcp"
    assert provider.token_verifier.required_scopes == [
        "oci-language.invoke",
        "audit.read",
    ]


@pytest.mark.asyncio
async def test_oauth_verifier_rejects_invalid_security_claims() -> None:
    key_pair = RSAKeyPair.generate()
    verifier = JWTVerifier(
        public_key=key_pair.public_key,
        issuer="https://identity.example.test",
        audience="https://mcp.example.test/mcp",
        required_scopes=["oci-language.invoke"],
    )

    valid = key_pair.create_token(
        issuer="https://identity.example.test",
        audience="https://mcp.example.test/mcp",
        scopes=["oci-language.invoke"],
    )
    assert await verifier.verify_token(valid) is not None

    invalid_tokens = [
        key_pair.create_token(
            issuer="https://wrong-issuer.example.test",
            audience="https://mcp.example.test/mcp",
            scopes=["oci-language.invoke"],
        ),
        key_pair.create_token(
            issuer="https://identity.example.test",
            audience="https://wrong-audience.example.test",
            scopes=["oci-language.invoke"],
        ),
        key_pair.create_token(
            issuer="https://identity.example.test",
            audience="https://mcp.example.test/mcp",
            scopes=["unrelated.scope"],
        ),
        key_pair.create_token(
            issuer="https://identity.example.test",
            audience="https://mcp.example.test/mcp",
            scopes=["oci-language.invoke"],
            expires_in_seconds=-1,
        ),
    ]

    for token in invalid_tokens:
        assert await verifier.verify_token(token) is None
