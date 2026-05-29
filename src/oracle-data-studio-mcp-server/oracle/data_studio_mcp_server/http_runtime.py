# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''Streamable-HTTP transport hardening.

The FastMCP `streamable-http` transport is a bare HTTP endpoint with
no built-in auth: anyone who reaches the port gets the configured
profile under the configured Oracle credentials. This module:

  - Decides whether a bind is allowed at startup (fail-closed gate).
  - When a bearer token is configured, wraps the Starlette HTTP app
    with a middleware that enforces `Authorization: Bearer <token>`
    on every request before any tool dispatch happens.

The rules (enforced by `decide_bind`):

  1. Loopback bind (127.0.0.1 / ::1 / localhost) is always allowed —
     attacker must already be on the host.
  2. Non-loopback bind requires either:
       a. `auth_token` set  → bearer middleware enforces auth, or
       b. `allow_insecure_bind=True` → operator has acknowledged that
          they have an external auth proxy in front. Big WARNING is
          logged.
  3. Otherwise: refuse to start. `decide_bind` raises
     `InsecureBindRefused` and `main()` exits non-zero.

This is the first-party fallback. The reviewer-recommended path is
still "put an authenticated reverse proxy in front", and that path
is what `allow_insecure_bind` acknowledges.
'''

from __future__ import annotations

import logging
import secrets
from typing import Optional

logger = logging.getLogger('oracle-data-studio-mcp')


class InsecureBindRefused(Exception):
    '''Raised when a non-loopback bind is requested without auth.'''


# Hosts treated as loopback. Anything else is considered exposed and
# subject to the auth gate.
_LOOPBACK_HOSTS = frozenset({
    '127.0.0.1',
    '::1',
    'localhost',
    # Empty string sometimes means "default = loopback" in dev setups.
    '',
})


def is_loopback(host: Optional[str]) -> bool:
    '''True if `host` is a loopback address.

    Accepts the common forms: 127.0.0.1, ::1, localhost. Anything
    else — including 0.0.0.0, a LAN IP, or a hostname — is treated as
    a non-loopback bind that requires auth or explicit opt-in.
    '''
    if host is None:
        return True
    return host.strip().lower() in _LOOPBACK_HOSTS


def decide_bind(host: Optional[str], *,
                auth_token: Optional[str] = None,
                allow_insecure_bind: bool = False) -> None:
    '''Gate the streamable-http bind. Raises if the bind is unsafe.

    Loopback binds are always allowed silently. Non-loopback binds
    require `auth_token` OR `allow_insecure_bind`. The chosen path is
    logged at INFO so operators see what's in effect; insecure binds
    log a prominent WARNING.

    @raises InsecureBindRefused: when host is non-loopback and neither
        `auth_token` nor `allow_insecure_bind` is set.
    '''
    if is_loopback(host):
        logger.info('streamable-http bind: loopback (%s) — no auth gate needed',
                    host or '127.0.0.1')
        return
    if auth_token:
        logger.info(
            'streamable-http bind: non-loopback (%s) with MCP_AUTH_TOKEN '
            'set — bearer middleware will reject unauthenticated requests',
            host)
        return
    if allow_insecure_bind:
        logger.warning(
            'streamable-http bind: non-loopback (%s) WITHOUT MCP_AUTH_TOKEN — '
            '--allow-insecure-bind acknowledged by operator. Server has NO '
            'first-party auth; ensure an authenticated reverse proxy is in '
            'front of port %s. Anyone reaching the port gets the configured '
            'profile under the configured Oracle credentials.',
            host, host)
        return
    raise InsecureBindRefused(
        'streamable-http refusing to bind to non-loopback host {!r}: '
        'no MCP_AUTH_TOKEN and --allow-insecure-bind not set. '
        'Either (a) set MCP_AUTH_TOKEN to a strong secret so the '
        'server can enforce bearer auth, (b) pass --allow-insecure-bind '
        '(or MCP_ALLOW_INSECURE_BIND=1) if an authenticated reverse '
        'proxy / API gateway sits in front, or (c) leave the bind on '
        '127.0.0.1.'.format(host))


def make_bearer_middleware(token: str):
    '''Return a Starlette middleware class that enforces Bearer auth.

    The token comparison uses `secrets.compare_digest` for constant-
    time matching. Tool dispatch never sees the request unless the
    Authorization header is present and matches.

    Health check (`GET /`) returns 200 unauthenticated so load
    balancers / readiness probes work; everything else (POST, the
    MCP message endpoints, etc.) requires auth.
    '''
    # Import lazily so the module imports without Starlette installed
    # (relevant for the stdio-only case in tests).
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    expected = token

    class BearerAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            # Allow unauthenticated readiness probes
            if request.method == 'GET' and request.url.path in ('/', '/health'):
                return await call_next(request)
            header = request.headers.get('Authorization') or ''
            scheme, _, value = header.partition(' ')
            if scheme.lower() != 'bearer' or not value:
                return JSONResponse(
                    {'error': 'authentication required'},
                    status_code=401,
                    headers={'WWW-Authenticate': 'Bearer'})
            if not secrets.compare_digest(value, expected):
                return JSONResponse(
                    {'error': 'invalid bearer token'},
                    status_code=401,
                    headers={'WWW-Authenticate': 'Bearer'})
            return await call_next(request)

    return BearerAuthMiddleware


def wrap_app_with_bearer_auth(app, token: str):
    '''Wrap `app` (a Starlette ASGI app) with bearer-token enforcement.

    Returns the wrapped app, which still talks ASGI and can be served
    by uvicorn exactly like the original.
    '''
    from starlette.middleware import Middleware
    from starlette.applications import Starlette

    mw_cls = make_bearer_middleware(token)
    # Mount the original app under "/" of a thin wrapper Starlette
    # that carries the middleware. We can't .add_middleware() after
    # the Starlette app's startup; building a fresh wrapper is the
    # documented pattern.
    wrapper = Starlette(
        debug=False,
        routes=[],
        middleware=[Middleware(mw_cls)],
    )
    # Forward all routes/lifespan to the inner app via mount.
    wrapper.mount('/', app)
    return wrapper
