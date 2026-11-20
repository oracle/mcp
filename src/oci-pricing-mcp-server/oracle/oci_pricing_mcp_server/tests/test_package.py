"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import asyncio
from importlib import metadata

import pytest
from fastmcp import Client


def test_installed_distribution_exposes_both_commands():
    try:
        distribution = metadata.distribution("oracle.oci-pricing-mcp-server")
    except metadata.PackageNotFoundError:
        pytest.fail("Pricing must be installed as oracle.oci-pricing-mcp-server")

    from oracle.oci_pricing_mcp_server import __project__, __version__, server

    assert __project__ == "oracle.oci-pricing-mcp-server"
    assert __version__ == distribution.version
    commands = {
        entry.name: entry for entry in distribution.entry_points if entry.group == "console_scripts"
    }
    assert commands["oracle.oci-pricing-mcp-server"].load() is server.main
    assert commands["oci-pricing-mcp"].load() is server.main


def test_protocol_exposes_existing_tools_and_ping():
    from oracle.oci_pricing_mcp_server import server

    async def check():
        async with Client(server.mcp) as client:
            tools = {tool.name: tool for tool in await client.list_tools()}
            assert set(tools) == {"pricing_get_sku", "pricing_search_name", "ping"}
            assert tools["pricing_get_sku"].inputSchema["required"] == ["part_number"]
            assert tools["pricing_search_name"].inputSchema["required"] == ["query"]
            assert tools["pricing_search_name"].inputSchema["properties"]["limit"]["default"] == 12
            result = await client.call_tool("ping", {})
            assert result.is_error is False
            assert result.data == "ok"

    asyncio.run(check())
