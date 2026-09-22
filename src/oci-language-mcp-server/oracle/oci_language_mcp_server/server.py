# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""Configurable stdio and hardened HTTP OCI Language MCP server."""

from __future__ import annotations

import argparse
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP
from fastmcp.server.middleware.rate_limiting import SlidingWindowRateLimitingMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from . import __version__
from .config import LanguageMcpSettings, get_settings
from .http_security import http_middleware
from .logging import configure_logging
from .mcp_auth import build_mcp_auth
from .middleware import ArgumentSanitizationMiddleware, SafeTelemetryMiddleware
from .prompts import load_instructions
from .provider import OciLanguageProvider
from .service import LanguageProvider, LanguageService
from .tools import register_tools


def create_server(
    settings: LanguageMcpSettings | None = None,
    *,
    provider: LanguageProvider | None = None,
) -> FastMCP:
    """Assemble the generic shared-pretrained OCI Language server."""

    settings = settings or get_settings()
    configure_logging(level=settings.log_level, output_format=settings.log_format)
    provider = provider or OciLanguageProvider(settings)
    service = LanguageService(provider=provider, settings=settings)

    @asynccontextmanager
    async def lifespan(_server: FastMCP) -> AsyncIterator[dict[str, Any]]:
        try:
            yield {}
        finally:
            service.shutdown()

    mcp_middleware = [ArgumentSanitizationMiddleware(), SafeTelemetryMiddleware()]
    # FastMCP applies this middleware only after its configured auth provider has
    # accepted the request. This keeps invalid OAuth tokens out of the authenticated
    # request quota while preserving a limit for successful remote MCP requests.
    if settings.deployment_mode == "remote" and settings.http_auth_mode == "oauth":
        mcp_middleware.append(
            SlidingWindowRateLimitingMiddleware(
                max_requests=settings.remote_requests_per_minute,
                window_minutes=1,
            )
        )

    mcp_server = FastMCP(
        name=settings.server_name,
        version=__version__,
        instructions=load_instructions(),
        auth=build_mcp_auth(settings),
        middleware=mcp_middleware,
        lifespan=lifespan,
        mask_error_details=True,
        strict_input_validation=False,
        tasks=False,
    )

    @mcp_server.custom_route("/health", methods=["GET"])
    async def health_check(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    @mcp_server.custom_route("/ready", methods=["GET"])
    async def readiness_check(_request: Request) -> JSONResponse:
        if service.is_ready:
            return JSONResponse({"status": "ready"})
        return JSONResponse({"status": "busy"}, status_code=503)

    register_tools(mcp_server, service, settings.parsed_enabled_tools())
    mcp_server.language_service = service
    return mcp_server


mcp = create_server()


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="OCI Language MCP server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        help="MCP transport; overrides LANGUAGE_MCP_TRANSPORT.",
    )
    args = parser.parse_args(argv)
    settings = get_settings()
    transport = args.transport or settings.transport
    if transport == "stdio":
        mcp.run(transport="stdio", show_banner=False, log_level=settings.log_level)
    else:
        mcp.run(
            transport="streamable-http",
            host=settings.host,
            port=settings.port,
            show_banner=False,
            middleware=http_middleware(settings),
            uvicorn_config={"server_header": False, "access_log": False},
        )


if __name__ == "__main__":
    main()
