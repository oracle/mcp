# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''
Auto-reconnect helper for ADP connections.

The ORDS session (or OAuth token) can expire during a long MCP session.
This helper:
1. Proactively checks token expiry before returning the client.
2. Reactively catches "expired" / 401 errors and re-logins once.

Usage in tool modules:
    from ._adp_connect import run_adp

    @mcp.tool()
    def adp_list_tables(ctx: Context) -> str:
        """List all tables."""
        return run_adp(ctx, lambda adp: adp.Misc.list_tables())
'''

import json
import logging
import threading
import time
from datetime import datetime

from mcp.server.fastmcp import Context

logger = logging.getLogger('oracle-data-studio-mcp')

_NO_CONN_MSG = 'ADP not connected. Set ADP_URL, ADP_USER, ADP_PASSWORD.'

# ── Reconnect throttling (S6) ──────────────────────────────────────
# A malformed-401 storm or compromised credential could otherwise
# cause unlimited re-login attempts.
_MAX_RECONNECTS_PER_WINDOW = 3
_WINDOW_SECONDS = 60
# Cool-down once we've hit the limit.
_COOLDOWN_SECONDS = 30

# ── Reconnect serialisation (S7) ───────────────────────────────────
# In streamable-http transport, multiple tool calls run concurrently.
# A reconnect that swaps lc['adp'] must hold a per-context lock so
# we don't return a client while another thread is replacing it.
_locks: dict[int, threading.Lock] = {}
_locks_lock = threading.Lock()


def _ctx_lock(lc) -> threading.Lock:
    '''Per-lifespan-context reconnect lock.'''
    key = id(lc)
    with _locks_lock:
        lk = _locks.get(key)
        if lk is None:
            lk = threading.Lock()
            _locks[key] = lk
        return lk


# ------------------------------------------------------------------ #
#  Formatting helpers                                                  #
# ------------------------------------------------------------------ #

def _default_format(result):
    '''Standard JSON formatting for SDK results.'''
    if result is None:
        return json.dumps({'status': 'success'})
    if isinstance(result, (dict, list)):
        return json.dumps(result, indent=2)
    return str(result)


def _err(msg):
    # Funnel through the shared sanitiser so connect-time errors
    # (which often carry DSNs / passwords) are scrubbed.
    from ._helpers import safe_err
    return json.dumps({'error': safe_err(msg)})


# ------------------------------------------------------------------ #
#  Connection management                                               #
# ------------------------------------------------------------------ #

def _is_expired(exc):
    '''Return True if the exception indicates an expired session/token.'''
    msg = str(exc).lower()
    return 'expired' in msg or '401' in msg


def _allow_reconnect(lc) -> tuple[bool, str | None]:
    '''Rate-limit check. Returns (allowed, deny_reason_if_not).'''
    now = time.monotonic()
    history = lc.setdefault('_adp_reconnect_times', [])
    cooldown_until = lc.get('_adp_reconnect_cooldown_until', 0)
    if now < cooldown_until:
        return (False, f'reconnect cooled down for '
                       f'{int(cooldown_until - now)}s '
                       f'(too many recent failures)')
    # Drop entries outside the rolling window
    cutoff = now - _WINDOW_SECONDS
    history[:] = [t for t in history if t >= cutoff]
    if len(history) >= _MAX_RECONNECTS_PER_WINDOW:
        lc['_adp_reconnect_cooldown_until'] = now + _COOLDOWN_SECONDS
        return (False,
                f'reconnect rate limit hit '
                f'({_MAX_RECONNECTS_PER_WINDOW} attempts in '
                f'{_WINDOW_SECONDS}s) — cooling down for '
                f'{_COOLDOWN_SECONDS}s')
    history.append(now)
    return (True, None)


def _reconnect(lc):
    '''Re-login to ADP using stored credentials. Returns new client or None.

    Serialised per lifespan-context (S7) and rate-limited (S6).
    '''
    cfg = lc.get('_adp_config')
    if not cfg:
        return None

    lock = _ctx_lock(lc)
    with lock:
        # Another thread may have already reconnected while we were
        # waiting for the lock — avoid duplicate logins.
        existing = lc.get('adp')
        if existing is not None:
            rest = getattr(existing, 'rest', None)
            still_valid = (rest is None
                           or rest.expired is None
                           or datetime.now() < rest.expired)
            if still_valid:
                return existing

        ok, reason = _allow_reconnect(lc)
        if not ok:
            logger.warning('ADP reconnect denied: %s', reason)
            return None

        try:
            import adp
            adp_client = adp.login(cfg.url, cfg.user, cfg.password)
            lc['adp'] = adp_client
            logger.info('ADP reconnected to %s as %s', cfg.url, cfg.user)
            return adp_client
        except Exception as e:
            logger.error('ADP reconnect failed: %s', e)
            return None


def get_adp(ctx: Context):
    '''Return the ADP client, reconnecting proactively if the token has expired.

    Reads of `lc['adp']` are best-effort racy (a concurrent reconnect
    might be in-flight) — but the swap inside `_reconnect` happens
    under a per-context lock, so worst case is that a caller uses a
    just-replaced-but-still-valid client.
    '''
    lc = ctx.request_context.lifespan_context
    client = lc.get('adp')

    if client:
        # Proactive check for OAuth-token connections
        rest = client.rest
        if rest.expired is not None and datetime.now() >= rest.expired:
            logger.info('ADP token expired, reconnecting proactively')
            return _reconnect(lc) or client
        return client

    # No client at all — attempt initial connection
    return _reconnect(lc)


# ------------------------------------------------------------------ #
#  Public API: run_adp                                                 #
# ------------------------------------------------------------------ #

def run_adp(ctx: Context, fn, format_fn=None):
    '''Execute *fn(adp_client)* with auto-reconnect on session expiry.

    Parameters
    ----------
    ctx : Context
        FastMCP request context.
    fn : callable(adp_client) -> result
        A callable that receives the ADP client and makes the SDK call.
        May also do pre-processing (e.g. json.loads) inside the callable.
    format_fn : callable(result) -> str, optional
        Custom formatter.  Defaults to the standard JSON formatter.

    Returns
    -------
    str
        JSON-encoded result or error.
    '''
    fmt = format_fn or _default_format
    lc = ctx.request_context.lifespan_context
    client = get_adp(ctx)

    if not client:
        return json.dumps({'error': _NO_CONN_MSG})

    try:
        result = fn(client)
        return fmt(result)
    except Exception as e:
        if _is_expired(e):
            logger.info('ADP session expired during call, reconnecting...')
            client = _reconnect(lc)
            if client:
                try:
                    result = fn(client)
                    return fmt(result)
                except Exception as e2:
                    return _err(str(e2))
        return _err(str(e))
