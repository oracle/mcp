"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Who may see a cached entry.

The store itself is cachetools' -- TTL, LRU and the size bound are a solved problem
and not this server's to re-implement. What is this server's problem is the key:
namespace plus tenant plus caller, composed in exactly one place so that no cache
can be added that quietly omits the caller and serves one person's result to
another. That is what the old region cache did.
"""

import hashlib
import os
import uuid

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
    permissions produced it. Composing that by hand at the call site is exactly how
    the old region cache came to key on tenancy alone and hand one caller's result
    to another, so a call site supplies only a namespace and the partition is
    appended here.
    """
    return f"{namespace}|{_tenant_cache_key()}|{_caller_cache_key()}"


# The bound each cache passes to its store as maxsize. It matters on the hosted
# transport, where the key includes the caller: without it the process would grow an
# entry per person signed in, each holding that caller's whole compartment listing.
_CACHE_MAX_ENTRIES = int(os.getenv("ORACLE_MCP_CACHE_MAX_ENTRIES", "256"))
