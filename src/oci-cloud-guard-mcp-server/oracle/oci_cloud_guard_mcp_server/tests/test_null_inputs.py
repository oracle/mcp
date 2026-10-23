"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock

import oci
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from jsonschema import Draft202012Validator

from oracle.oci_cloud_guard_mcp_server import server


@pytest.mark.asyncio
async def test_null_defaults_are_accepted_by_advertised_schemas():
    async with Client(server.mcp) as client:
        for tool in await client.list_tools():
            validator = Draft202012Validator(tool.inputSchema)
            for name, schema in tool.inputSchema["properties"].items():
                if "default" in schema and schema["default"] is None:
                    assert validator.evolve(schema=schema).is_valid(None), f"{tool.name}.{name}"


@pytest.mark.asyncio
@pytest.mark.parametrize("comment_args", [{}, {"comment": None}, {"comment": "Investigated"}])
async def test_update_problem_accepts_optional_comment(monkeypatch, comment_args):
    sdk = MagicMock()
    sdk.update_problem_status.return_value.data = oci.cloud_guard.models.Problem(
        id="sample", lifecycle_detail="OPEN", comment=comment_args.get("comment")
    )
    monkeypatch.setattr(server, "get_cloud_guard_client", lambda: sdk)

    async with Client(server.mcp) as client:
        result = await client.call_tool("update_problem_status", {"problem_id": "sample", **comment_args})
        assert result.structured_content["id"] == "sample"
        assert result.structured_content["comment"] == comment_args.get("comment")
        details = sdk.update_problem_status.call_args.kwargs["update_problem_status_details"]
        assert details.comment == comment_args.get("comment")


@pytest.mark.asyncio
async def test_update_problem_rejects_invalid_comment():
    async with Client(server.mcp) as client:
        with pytest.raises(ToolError, match="valid string"):
            await client.call_tool("update_problem_status", {"problem_id": "sample", "comment": 7})
