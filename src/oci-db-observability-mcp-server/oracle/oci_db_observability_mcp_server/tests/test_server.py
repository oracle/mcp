"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from oracle.oci_db_observability_mcp_server import server


def test_main_runs_stdio(monkeypatch) -> None:
    calls: list[tuple[tuple, dict]] = []
    monkeypatch.setattr(server.mcp, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    server.main()

    assert calls == [((), {})]
