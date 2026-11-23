"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import pytest
from jsonschema import Draft202012Validator
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from oracle.data_studio_mcp_server.tools import adp_tools, dt_tools, essbase_tools


@pytest.mark.asyncio
async def test_null_defaults_are_accepted_by_advertised_schemas():
    mcp = FastMCP("test")
    for module in (adp_tools, dt_tools, essbase_tools):
        module.register_tools(mcp)
    for tool in await mcp.list_tools():
        validator = Draft202012Validator(tool.parameters)
        assert "ctx" not in tool.parameters["properties"]
        for name, schema in tool.parameters["properties"].items():
            if "default" in schema and schema["default"] is None:
                assert validator.evolve(schema=schema).is_valid(None), f"{tool.name}.{name}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("module", "connection", "tool_name", "required", "parameter", "valid", "invalid"),
    [(adp_tools, "get_adp", "adp_build_analytic_view", {"fact_table": "FACT"}, "av_name", "AV", 7),
     (essbase_tools, "get_essbase", "essbase_outline_metadata",
      {"app_name": "Sample", "db_name": "Basic"}, "dimension_name", "Measures", 7),
     (dt_tools, "get_dt", "dt_manage_connection", {"action": "list"}, "port", 1521, "invalid")],
)
async def test_optional_tool_inputs(monkeypatch, module, connection, tool_name, required, parameter, valid, invalid):
    mcp = FastMCP("test")
    module.register_tools(mcp)
    monkeypatch.setattr(module, connection, lambda ctx: None)
    async with Client(mcp) as client:
        omitted = await client.call_tool(tool_name, required)
        for value in (None, valid):
            result = await client.call_tool(tool_name, {**required, parameter: value})
            assert result.content == omitted.content
        with pytest.raises(ToolError, match="validation error"):
            await client.call_tool(tool_name, {**required, parameter: invalid})
