"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from jsonschema import Draft202012Validator

from oracle.oci_networking_mcp_server import server


@pytest.mark.asyncio
async def test_null_defaults_are_accepted_by_advertised_schemas():
    async with Client(server.mcp) as client:
        for tool in await client.list_tools():
            validator = Draft202012Validator(tool.inputSchema)
            for name, schema in tool.inputSchema["properties"].items():
                if "default" in schema and schema["default"] is None:
                    assert validator.evolve(schema=schema).is_valid(None), f"{tool.name}.{name}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "filters"),
    [("list_subnets", ("vcn_id",)), ("list_security_lists", ("vcn_id",)),
     ("list_network_security_groups", ("vcn_id", "vlan_id"))],
)
@pytest.mark.parametrize("value", [None, "sample", 7])
async def test_optional_network_filters(monkeypatch, tool_name, filters, value):
    sdk = MagicMock()
    response = getattr(sdk, tool_name).return_value
    response.data = []
    response.has_next_page = False
    response.next_page = None
    monkeypatch.setattr(server, "get_networking_client", lambda: sdk)

    async with Client(server.mcp) as client:
        omitted = await client.call_tool(tool_name, {"compartment_id": "sample"})
        assert omitted.structured_content["result"] == []
        arguments = {"compartment_id": "sample", **dict.fromkeys(filters, value)}
        if isinstance(value, int):
            with pytest.raises(ToolError, match="valid string"):
                await client.call_tool(tool_name, arguments)
        else:
            result = await client.call_tool(tool_name, arguments)
            assert result.structured_content["result"] == []
            for name in filters:
                assert getattr(sdk, tool_name).call_args.kwargs[name] == value
