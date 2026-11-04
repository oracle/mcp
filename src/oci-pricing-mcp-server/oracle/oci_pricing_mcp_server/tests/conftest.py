"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import httpx
import pytest

from oracle.oci_pricing_mcp_server import server


@pytest.fixture(autouse=True)
def offline_boundaries(monkeypatch):
    """Default tests must never reach the public API or wait for retry backoff."""

    def forbidden_send(*args, **kwargs):
        # A pytest failure cannot be swallowed by optional API error handling.
        pytest.fail("Live HTTP is forbidden in unit tests; use the explicit integration suite")

    async def no_sleep(seconds):
        pass

    monkeypatch.setattr(httpx.Client, "send", forbidden_send)
    monkeypatch.setattr(httpx.AsyncClient, "send", forbidden_send)
    monkeypatch.setattr(server.asyncio, "sleep", no_sleep)
    server._is_valid_iso4217.cache_clear()
    yield
    server._is_valid_iso4217.cache_clear()
