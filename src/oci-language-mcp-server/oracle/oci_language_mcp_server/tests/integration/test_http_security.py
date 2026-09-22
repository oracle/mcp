# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import pytest
from pydantic import ValidationError
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from oracle.oci_language_mcp_server.config import LanguageMcpSettings
from oracle.oci_language_mcp_server.http_security import HttpSecurityMiddleware, http_middleware
from oracle.oci_language_mcp_server.server import create_server


def test_local_mode_allows_localhost_and_rejects_other_hosts_and_origins() -> None:
    settings = LanguageMcpSettings()
    server = create_server(settings)
    app = server.http_app(transport="streamable-http", middleware=http_middleware(settings))
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            assert client.get("/health").status_code == 200
            rejected_origin = client.get(
                "/health", headers={"Origin": "https://evil.example"}
            )
            assert rejected_origin.status_code == 403
            assert client.get("/health", headers={"Host": "evil.example"}).status_code == 400
    finally:
        server.language_service.shutdown()


def test_remote_mode_requires_complete_security_configuration() -> None:
    with pytest.raises(ValidationError, match="Remote mode requires"):
        LanguageMcpSettings(deployment_mode="remote")


def test_local_http_rejects_non_loopback_listener() -> None:
    with pytest.raises(ValidationError, match="loopback"):
        LanguageMcpSettings(host="0.0.0.0")


def test_invalid_oauth_bearers_do_not_consume_the_post_auth_quota() -> None:
    settings = LanguageMcpSettings(
        deployment_mode="remote",
        http_auth_mode="oauth",
        allowed_hosts="mcp.example.test",
        allowed_origins="https://agent.example.test",
        public_base_url="https://mcp.example.test",
        oauth_issuer="https://identity.example.test",
        oauth_jwks_uri="https://identity.example.test/jwks",
        oauth_audience="https://mcp.example.test/mcp",
        remote_requests_per_minute=1,
    )

    async def authenticated_app(scope, receive, send) -> None:
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                event = "startup" if message["type"] == "lifespan.startup" else "shutdown"
                await send({"type": f"lifespan.{event}.complete"})
                if event == "shutdown":
                    break
            return
        await JSONResponse({"status": "authenticated"})(scope, receive, send)

    middleware = HttpSecurityMiddleware(authenticated_app, settings=settings, remote_token=None)

    async def pre_auth_quota_must_not_run() -> bool:
        raise AssertionError("OAuth quota was charged before authentication")

    middleware._within_rate_limit = pre_auth_quota_must_not_run  # type: ignore[method-assign]
    headers = {
        "Host": "mcp.example.test",
        "Origin": "https://agent.example.test",
        "Authorization": "Bearer invalid-token",
    }
    with TestClient(middleware, base_url="https://mcp.example.test") as client:
        assert client.post("/mcp", headers=headers, json={}).status_code == 200
        assert client.post("/mcp", headers=headers, json={}).status_code == 200


def test_remote_mode_requires_bearer_token_and_enforces_rate_limit(tmp_path) -> None:
    token_file = tmp_path / "mcp-token"
    token_file.write_text("test-secret-token", encoding="utf-8")
    settings = LanguageMcpSettings(
        deployment_mode="remote",
        allowed_hosts="mcp.example.test",
        allowed_origins="https://agent.example.test",
        auth_token_file=str(token_file),
        remote_requests_per_minute=1,
    )
    server = create_server(settings)
    app = server.http_app(transport="streamable-http", middleware=http_middleware(settings))
    headers = {
        "Host": "mcp.example.test",
        "Origin": "https://agent.example.test",
    }
    try:
        with TestClient(app, base_url="https://mcp.example.test") as client:
            assert client.post("/mcp", headers=headers, json={}).status_code == 401
            authorized = {**headers, "Authorization": "Bearer test-secret-token"}
            assert client.post("/mcp", headers=authorized, json={}).status_code != 401
            assert client.post("/mcp", headers=authorized, json={}).status_code == 429
    finally:
        server.language_service.shutdown()


def test_request_body_limit_is_enforced_before_mcp_parsing() -> None:
    settings = LanguageMcpSettings(request_body_limit_bytes=16_384)
    server = create_server(settings)
    app = server.http_app(transport="streamable-http", middleware=http_middleware(settings))
    try:
        with TestClient(app, base_url="http://127.0.0.1") as client:
            response = client.post("/mcp", content=b"x" * 16_385)
    finally:
        server.language_service.shutdown()

    assert response.status_code == 413


def test_remote_oauth_publishes_metadata_and_challenges_unauthorized_calls() -> None:
    settings = LanguageMcpSettings(
        deployment_mode="remote",
        http_auth_mode="oauth",
        allowed_hosts="mcp.example.test",
        allowed_origins="https://agent.example.test",
        public_base_url="https://mcp.example.test",
        oauth_issuer="https://identity.example.test",
        oauth_jwks_uri="https://identity.example.test/.well-known/jwks.json",
        oauth_audience="https://mcp.example.test/mcp",
    )
    server = create_server(settings)
    app = server.http_app(transport="streamable-http", middleware=http_middleware(settings))
    headers = {
        "Host": "mcp.example.test",
        "Origin": "https://agent.example.test",
        "Accept": "application/json, text/event-stream",
    }
    try:
        with TestClient(app, base_url="https://mcp.example.test") as client:
            metadata = client.get(
                "/.well-known/oauth-protected-resource/mcp",
                headers=headers,
            )
            unauthorized = client.post("/mcp", headers=headers, json={})
    finally:
        server.language_service.shutdown()

    assert metadata.status_code == 200
    assert metadata.json()["authorization_servers"] == ["https://identity.example.test/"]
    assert metadata.json()["scopes_supported"] == ["oci-language.invoke"]
    assert unauthorized.status_code == 401
    challenge = unauthorized.headers["www-authenticate"]
    assert "resource_metadata=" in challenge
    assert "identity.example.test" not in unauthorized.text
