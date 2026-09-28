# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""Standards-based inbound authentication for remote MCP deployments."""

from __future__ import annotations

from fastmcp.server.auth import RemoteAuthProvider
from pydantic import AnyHttpUrl

from .config import LanguageMcpSettings


def build_mcp_auth(settings: LanguageMcpSettings) -> RemoteAuthProvider | None:
    """Build an OAuth protected-resource verifier for remote HTTP mode."""

    if settings.deployment_mode != "remote" or settings.http_auth_mode != "oauth":
        return None

    public_base_url = settings.public_base_url or ""
    issuer = settings.oauth_issuer or ""
    # Keep the cryptography/Authlib dependency path lazy for local and stdio users.
    from fastmcp.server.auth import JWTVerifier

    verifier = JWTVerifier(
        jwks_uri=settings.oauth_jwks_uri,
        issuer=issuer,
        audience=settings.oauth_audience,
        algorithm=settings.oauth_algorithm,
        required_scopes=list(settings.parsed_oauth_required_scopes()),
        base_url=public_base_url,
        ssrf_safe=True,
    )
    return RemoteAuthProvider(
        token_verifier=verifier,
        authorization_servers=[AnyHttpUrl(issuer)],
        base_url=public_base_url,
        resource_base_url=public_base_url,
        scopes_supported=list(settings.parsed_oauth_required_scopes()),
        resource_name="OCI Language MCP Server",
    )
