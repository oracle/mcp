"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from pathlib import Path


def test_server_module_does_not_include_remote_http_or_oauth_terms() -> None:
    server_source = (
        Path(__file__).resolve().parents[1] / "server.py"
    ).read_text(encoding="utf-8")

    forbidden_terms = [
        "Streamable",
        "ORACLE_MCP_HOST",
        "ORACLE_MCP_PORT",
        "ORACLE_MCP_BASE_URL",
        "IDCS_",
        "oauth",
        "/.well-known",
        "Authorization: Bearer",
    ]
    for term in forbidden_terms:
        assert term not in server_source
