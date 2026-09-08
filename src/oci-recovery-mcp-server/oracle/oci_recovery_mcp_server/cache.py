"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

The in-process TTL/LRU cache behind the compartment lookup.

Two things live here: the key that decides who may see a cached entry -- namespace
plus tenant plus caller, composed in exactly one place so no cache can be added
that quietly omits the caller -- and the bounded TTL store itself: a TTL sweep plus an LRU bound, so
a hosted deployment does not grow an entry per signed-in caller forever. FastMCP
runs synchronous tools in worker threads, so every mutation is done under
``_CACHE_LOCK``.
"""

import hashlib
import os
import threading
import uuid
from typing import Any, Optional

from . import auth


def _tenant_cache_key() -> str:
    """
    Stable per-tenant key for the in-process caches.

    Every in-process cache is partitioned by tenant so a cached result can never
    outlive the tenancy it was computed for -- including across a configuration
    change that repoints the server at a different tenancy. get_tenancy() returns
    the configured tenancy OCID over HTTP, or the local config's over stdio.
    """
    try:
        return auth.get_tenancy() or "_default"
    except Exception:
        return "_default"


def _caller_cache_key() -> str:
    """
    Stable per-caller key for caches whose contents depend on the caller's own
    OCI permissions, appended to the tenant key.

    Tenant partitioning alone is not enough for those: over HTTP every caller has
    their own IAM permissions, so a result computed with one caller's
    authorizations (anything fetched with access_level="ACCESSIBLE") must never be
    served to another. Over stdio there is exactly one set of credentials for the
    whole process, so there is nothing to separate and this contributes nothing to
    the key.

    The subject claim identifies the human, not the session, so the cache still
    survives a token refresh. When the provider omits it we fall back to
    per-session values (jti, then the raw token), which costs a refetch after a
    refresh but never merges two callers. The key is hashed because it is cheap
    to end up in a log line or a debug dump.
    """
    if not auth._serving_http():
        return ""
    try:
        access = auth._current_access_token()
        claims = (getattr(access, "claims", None) or {}) if access is not None else {}
        # Only ever caller-specific values here. client_id identifies the
        # registered OAuth application, which many humans share, so it must
        # never appear in this chain. Some providers omit sub; jti and the raw
        # token are both per-session, so the entry is scoped to this session.
        subject = claims.get("sub") or claims.get("jti") or getattr(access, "token", None)
    except Exception:
        subject = None
    if not subject:
        # No request context at all (e.g. startup): don't touch a shared entry.
        return f"anon:{uuid.uuid4().hex}"
    return "sub:" + hashlib.sha256(str(subject).encode()).hexdigest()[:16]


def _cache_key(namespace: str) -> str:
    """
    Build the key for a cached value. The only supported way to make one.

    Every cached value is scoped to the tenancy and to the caller whose
    permissions produced it. Composing that by hand at the call site is exactly
    how the old region cache came to key on tenancy alone and hand one caller's
    result to another, so the accessors below take a namespace and come here --
    there is no way to reach the store with a key that skipped this.
    """
    return f"{namespace}|{_tenant_cache_key()}|{_caller_cache_key()}"


_CACHE_MAX_ENTRIES = int(os.getenv("ORACLE_MCP_CACHE_MAX_ENTRIES", "256"))

# FastMCP runs synchronous tools in worker threads, so two tool calls can be inside
# these helpers at once. Both of them reorder and evict entries, not just read them:
# unsynchronized, the reinsert in _cache_get raises KeyError when another thread
# sweeps the same key first, and the sweep and eviction in _cache_put raise
# "dictionary changed size during iteration" or StopIteration. The critical sections
# are dict operations only -- the upstream fetch happens between a _cache_get miss
# and the _cache_put, outside the lock -- so no OCI call is ever made holding it.
_CACHE_LOCK = threading.Lock()


def _cache_get(
    entries: dict[str, Any], namespace: str, *, ttl: float, now: float
) -> Optional[Any]:
    """Return a live cache entry, refreshing its recency, or None.

    Reinserting on a hit makes the dict's insertion order a true LRU order, which
    is what _cache_put evicts from. The key is resolved before the lock is taken:
    it reads the tenancy and the caller's token, and neither belongs in a critical
    section that every other tool call is waiting on.
    """
    key = _cache_key(namespace)
    with _CACHE_LOCK:
        cached = entries.get(key)
        if not cached:
            return None
        if now - float(cached.get("fetched_at") or 0.0) >= ttl:
            entries.pop(key, None)
            return None
        entries[key] = entries.pop(key)
        return cached


def _cache_put(
    entries: dict[str, Any], namespace: str, value: Any, *, ttl: float, now: float
) -> None:
    """Store a cache entry, sweeping expired ones and bounding the total.

    This cache is partitioned per tenant and per caller, so on the hosted HTTP
    transport it gains an entry for every person who signs in and each one holds
    that caller's whole compartment listing. Without a bound the process grows
    with the user count for the life of the deployment.
    """
    key = _cache_key(namespace)
    with _CACHE_LOCK:
        for expired in [
            k for k, v in entries.items() if now - float(v.get("fetched_at") or 0.0) >= ttl
        ]:
            entries.pop(expired, None)
        entries.pop(key, None)
        entries[key] = value
        # Holding the lock, len() > max guarantees there is something to pop.
        while len(entries) > _CACHE_MAX_ENTRIES:
            entries.pop(next(iter(entries)))
