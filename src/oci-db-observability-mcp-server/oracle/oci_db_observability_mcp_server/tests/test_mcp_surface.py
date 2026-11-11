"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import re

import pytest

from oracle.oci_db_observability_mcp_server import mcp as mcp_module
from oracle.oci_db_observability_mcp_server.mcp import mcp


@pytest.mark.asyncio
async def test_unified_mcp_exposes_only_discovery_and_dispatch_tools() -> None:
    tools = await mcp.list_tools()

    assert {tool.name for tool in tools} == {
        "describe_dbo_tool",
        "invoke_dbo_tool",
        "list_dbo_skills",
        "list_dbo_tools",
    }


@pytest.mark.asyncio
async def test_advertised_workflow_references_registered_tools_only() -> None:
    registered_names = {tool.name for tool in await mcp.list_tools()}
    advertised_names = set(re.findall(r"`([^`]+)`", mcp.instructions))

    assert advertised_names - {"oci-identity-mcp-server"} <= registered_names
    assert "oci-identity-mcp-server" not in registered_names
    assert "oci-identity-mcp-server" in mcp.instructions


def test_discovery_and_invocation_tools_delegate_to_registry(monkeypatch) -> None:
    skills = mcp_module.list_dbo_skills()["skills"]
    assert len(skills) == 35
    assert {"name", "description", "toolCount"}.issubset(skills[0])

    listed = mcp_module.list_dbo_tools(["database-inventory"], limit=1)
    assert listed["count"] >= 1
    assert len(listed["tools"]) == 1
    assert listed["truncated"] is (listed["count"] > 1)
    assert "database-inventory" in listed["tools"][0]["skills"]
    assert "compartmentRequirements" in listed["tools"][0]

    described = mcp_module.describe_dbo_tool("list_database_insights")
    assert described["name"] == "list_database_insights"
    assert described["inputSchema"]["type"] == "object"
    assert described["compartmentRequirements"] == [{"argument": "compartment_id", "required": False}]

    expected = {"result": "ok"}
    monkeypatch.setattr(mcp_module, "invoke_registered_tool", lambda tool, arguments: (tool["name"], arguments, expected))
    assert mcp_module.invoke_dbo_tool("list_database_insights", {"compartment_id": "ocid"}) == (
        "list_database_insights",
        {"compartment_id": "ocid"},
        expected,
    )
