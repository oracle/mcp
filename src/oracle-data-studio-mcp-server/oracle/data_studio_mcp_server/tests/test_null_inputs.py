"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import pytest
from jsonschema import Draft202012Validator
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from oracle.data_studio_mcp_server.tools import adp_tools, dt_tools, essbase_tools


def test_null_defaults_are_accepted_by_advertised_schemas():
    mcp = FastMCP("test")
    for module in (adp_tools, dt_tools, essbase_tools):
        module.register_tools(mcp)
    for tool in mcp._tool_manager.list_tools():
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
    omitted = await mcp.call_tool(tool_name, required)
    for value in (None, valid):
        assert await mcp.call_tool(tool_name, {**required, parameter: value}) == omitted
    with pytest.raises(ToolError, match="validation error"):
        await mcp.call_tool(tool_name, {**required, parameter: invalid})
