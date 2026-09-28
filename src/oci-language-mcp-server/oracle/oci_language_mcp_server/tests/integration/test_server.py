# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastmcp import Client
from pydantic import ValidationError
from starlette.testclient import TestClient

from oracle.oci_language_mcp_server.config import LanguageMcpSettings
from oracle.oci_language_mcp_server.constants import TOOL_NAMES
from oracle.oci_language_mcp_server.server import create_server
from oracle.oci_language_mcp_server.tools import TOOL_TITLES


async def test_server_discovers_seven_strict_typed_tools() -> None:
    server = create_server(LanguageMcpSettings(log_format="console"))
    try:
        async with Client(server) as client:
            tools = await client.list_tools()
            initialized = client.initialize_result
    finally:
        server.language_service.shutdown()
    assert tuple(tool.name for tool in tools) == TOOL_NAMES
    for tool in tools:
        assert tool.title == TOOL_TITLES[tool.name]
        assert tool.inputSchema["additionalProperties"] is False
        assert tool.inputSchema["properties"]["documents"]["minItems"] == 1
        assert tool.inputSchema["properties"]["documents"]["maxItems"] == 100
        assert tool.outputSchema is not None
    assert initialized is not None
    assert initialized.serverInfo.name == "oci-language-mcp"
    assert initialized.serverInfo.version == "0.1.0"


async def test_enabled_tools_restricts_discovery() -> None:
    server = create_server(
        LanguageMcpSettings(
            enabled_tools="translate_language_text,detect_language_entities"
        )
    )
    try:
        async with Client(server) as client:
            tools = await client.list_tools()
    finally:
        server.language_service.shutdown()
    assert [tool.name for tool in tools] == [
        "detect_language_entities",
        "translate_language_text",
    ]


@pytest.mark.parametrize(
    "legacy_tool",
    [
        "classify_text",
        "detect_entities",
        "extract_key_phrases",
        "analyze_sentiment",
        "detect_pii_entities",
        "translate_text",
    ],
)
def test_enabled_tools_rejects_legacy_catalog_names(legacy_tool: str) -> None:
    with pytest.raises(ValidationError, match="Unknown enabled tool"):
        LanguageMcpSettings(enabled_tools=legacy_tool)


def test_enabled_tools_rejects_unknown_or_empty_catalog() -> None:
    with pytest.raises(ValidationError, match="Unknown enabled tool"):
        LanguageMcpSettings(
            enabled_tools="detect_language_entities,run_any_sdk_method"
        )
    with pytest.raises(ValidationError, match="At least one"):
        LanguageMcpSettings(enabled_tools="")


def test_health_and_readiness_are_minimal() -> None:
    server = create_server(LanguageMcpSettings())
    app = server.http_app(transport="streamable-http")
    try:
        with TestClient(app) as client:
            assert client.get("/health").json() == {"status": "ok"}
            assert client.get("/ready").json() == {"status": "ready"}
    finally:
        server.language_service.shutdown()


def test_stdio_writes_only_json_rpc_to_stdout() -> None:
    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "stdio-test", "version": "1.0"},
            },
        }
    )
    completed = subprocess.run(
        [sys.executable, "-m", "oracle.oci_language_mcp_server.server", "--transport", "stdio"],
        input=request + "\n",
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    )
    responses = [
        json.loads(line) for line in completed.stdout.splitlines() if line.strip()
    ]
    assert responses[0]["result"]["serverInfo"]["version"] == "0.1.0"
    assert responses[0]["result"]["serverInfo"]["name"] == "oci-language-mcp"
    assert "Starting MCP server" not in completed.stdout
