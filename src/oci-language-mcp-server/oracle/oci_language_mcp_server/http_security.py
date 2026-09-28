# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""ASGI boundary controls for local and explicitly secured remote MCP use."""

from __future__ import annotations

import asyncio
import hmac
import time
from collections import deque
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from starlette.middleware import Middleware
from starlette.responses import JSONResponse

from .config import LanguageMcpSettings


class HttpSecurityMiddleware:
    """Validate Host/Origin, bound bodies, and authenticate remote MCP calls."""

    def __init__(
        self,
        app: Any,
        *,
        settings: LanguageMcpSettings,
        remote_token: str | None,
    ) -> None:
        self.app = app
        self.settings = settings
        self.remote_token = remote_token
        self._requests: deque[float] = deque()
        self._rate_lock = asyncio.Lock()

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        if not self._host_allowed(headers.get("host", "")):
            await self._reject(scope, receive, send, 400, "Request host is not allowed.")
            return
        origin = headers.get("origin")
        if origin and not self._origin_allowed(origin):
            await self._reject(scope, receive, send, 403, "Request origin is not allowed.")
            return

        path = str(scope.get("path", ""))
        if path.startswith("/mcp") and self.settings.deployment_mode == "remote":
            authorization = headers.get("authorization", "")
            if self.settings.http_auth_mode == "token-file":
                expected = f"Bearer {self.remote_token}"
                if not hmac.compare_digest(authorization, expected):
                    await self._reject(scope, receive, send, 401, "Authentication required.")
                    return
            # OAuth credentials are verified by FastMCP after this boundary.  Charging
            # here would let arbitrary invalid bearer values exhaust the valid-client
            # quota. Token-file credentials are verified above, so they are safe to
            # charge at this point.
            if (
                self.settings.http_auth_mode == "token-file"
                and authorization
                and not await self._within_rate_limit()
            ):
                await self._reject(scope, receive, send, 429, "Request rate limit exceeded.")
                return

        content_length = headers.get("content-length")
        if content_length and content_length.isdecimal():
            if int(content_length) > self.settings.request_body_limit_bytes:
                await self._reject(scope, receive, send, 413, "Request body is too large.")
                return

        buffered: list[dict[str, Any]] = []
        total = 0
        while True:
            message = await receive()
            buffered.append(message)
            if message.get("type") == "http.request":
                total += len(message.get("body", b""))
                if total > self.settings.request_body_limit_bytes:
                    await self._reject(scope, receive, send, 413, "Request body is too large.")
                    return
                if not message.get("more_body", False):
                    break
            else:
                break

        index = 0

        async def replay_receive() -> dict[str, Any]:
            nonlocal index
            if index < len(buffered):
                message = buffered[index]
                index += 1
                return message
            return await receive()

        await self.app(scope, replay_receive, send)

    def _host_allowed(self, host: str) -> bool:
        normalized = host.strip().lower()
        hostname = _hostname(normalized)
        return normalized in self.settings.parsed_allowed_hosts() or hostname in {
            item.lower() for item in self.settings.parsed_allowed_hosts()
        }

    def _origin_allowed(self, origin: str) -> bool:
        normalized = origin.strip().rstrip("/")
        if self.settings.deployment_mode == "remote":
            return normalized in self.settings.parsed_allowed_origins()
        parsed = urlsplit(normalized)
        return parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}

    async def _within_rate_limit(self) -> bool:
        now = time.monotonic()
        cutoff = now - 60
        async with self._rate_lock:
            while self._requests and self._requests[0] < cutoff:
                self._requests.popleft()
            if len(self._requests) >= self.settings.remote_requests_per_minute:
                return False
            self._requests.append(now)
            return True

    @staticmethod
    async def _reject(
        scope: dict[str, Any],
        receive: Any,
        send: Any,
        status: int,
        message: str,
    ) -> None:
        await JSONResponse({"error": message}, status_code=status)(scope, receive, send)


def http_middleware(settings: LanguageMcpSettings) -> list[Middleware]:
    token = _load_remote_token(settings)
    return [Middleware(HttpSecurityMiddleware, settings=settings, remote_token=token)]


def _load_remote_token(settings: LanguageMcpSettings) -> str | None:
    if settings.deployment_mode != "remote" or settings.http_auth_mode != "token-file":
        return None
    path = Path(settings.auth_token_file or "")
    token = path.read_text(encoding="utf-8").strip()
    if not token or len(token) > 4096 or "\n" in token or "\r" in token:
        raise ValueError("Remote authentication token file is empty or invalid.")
    return token


def _hostname(host: str) -> str:
    if host.startswith("[") and "]" in host:
        return host[1 : host.index("]")]
    return host.split(":", 1)[0]
