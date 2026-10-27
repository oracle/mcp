"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from jsonschema import Draft202012Validator

from oracle.oci_database_mcp_server import server


@pytest.mark.asyncio
async def test_null_defaults_are_accepted_by_advertised_schemas():
    async with Client(server.mcp) as client:
        for tool in await client.list_tools():
            validator = Draft202012Validator(tool.inputSchema)
            for name, schema in tool.inputSchema["properties"].items():
                if "default" in schema and schema["default"] is None:
                    assert validator.evolve(schema=schema).is_valid(None), f"{tool.name}.{name}"


@pytest.mark.asyncio
@pytest.mark.parametrize("region_args", [{}, {"region": None}, {"region": "us-ashburn-1"}])
async def test_public_ip_accepts_default_and_explicit_regions(monkeypatch, region_args):
    database = MagicMock()
    database.get_database.return_value.data = SimpleNamespace(
        db_system_id="sample", vm_cluster_id=None, compartment_id="sample"
    )
    database.list_db_nodes.return_value.data = []
    monkeypatch.setattr(
        server, "build_auth_context",
        lambda: SimpleNamespace(config={"region": "us-phoenix-1"}, signer=None),
    )
    factory = MagicMock(return_value=database)
    monkeypatch.setattr(server.oci.database, "DatabaseClient", factory)

    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "get_public_ip_for_database", {"database_id": "sample", **region_args}
        )
        assert not result.is_error
        assert factory.call_args.args[0]["region"] == (region_args.get("region") or "us-phoenix-1")


@pytest.mark.asyncio
async def test_public_ip_rejects_invalid_region():
    async with Client(server.mcp) as client:
        with pytest.raises(ToolError, match="valid string"):
            await client.call_tool("get_public_ip_for_database", {"database_id": "sample", "region": 7})
