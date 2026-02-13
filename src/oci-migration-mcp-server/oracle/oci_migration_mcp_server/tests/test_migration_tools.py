"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from oracle.oci_migration_mcp_server.server import mcp


class TestMigrationTools:
    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_get_migration(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.cloud_migrations.models.Migration(
            id="migration1", display_name="Migration 1", lifecycle_state="ACTIVE"
        )
        mock_client.get_migration.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_migration", {"migration_id": "migration1"}
            )
            result = call_tool_result.structured_content

            assert result["id"] == "migration1"

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_migrations(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = oci.cloud_migrations.models.MigrationCollection(
            items=[
                oci.cloud_migrations.models.Migration(
                    id="migration1",
                    display_name="Migration 1",
                    compartment_id="compartment1",
                    lifecycle_state="RUNNING",
                )
            ]
        )
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_migrations.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_migrations",
                    {
                        "compartment_id": "compartment1",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "migration1"


@pytest.mark.asyncio
@patch("oracle.mcp_common.helpers._create_oci_client")
async def test_list_migrations_pagination_without_limit(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client

    resp1 = create_autospec(oci.response.Response)
    resp1.data = SimpleNamespace(
        items=[
            oci.cloud_migrations.models.Migration(id="m1", display_name="M1"),
            oci.cloud_migrations.models.Migration(id="m2", display_name="M2"),
        ]
    )
    resp1.has_next_page = True
    resp1.next_page = "np1"

    resp2 = create_autospec(oci.response.Response)
    resp2.data = SimpleNamespace(
        items=[
            oci.cloud_migrations.models.Migration(id="m3", display_name="M3"),
        ]
    )
    resp2.has_next_page = False
    resp2.next_page = None

    mock_client.list_migrations.side_effect = [resp1, resp2]

    async with Client(mcp) as client:
        result = (
            await client.call_tool(
                "list_migrations",
                {"compartment_id": "tenancy"},
            )
        ).structured_content["result"]

    assert [r["id"] for r in result] == ["m1", "m2", "m3"]
    first_kwargs = mock_client.list_migrations.call_args_list[0].kwargs
    second_kwargs = mock_client.list_migrations.call_args_list[1].kwargs
    assert first_kwargs["page"] is None
    assert "limit" not in first_kwargs
    assert second_kwargs["page"] == "np1"
    assert "limit" not in second_kwargs


@pytest.mark.asyncio
@patch("oracle.mcp_common.helpers._create_oci_client")
async def test_list_migrations_limit_stops_pagination(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client

    resp1 = create_autospec(oci.response.Response)
    resp1.data = SimpleNamespace(
        items=[
            oci.cloud_migrations.models.Migration(id="m1"),
            oci.cloud_migrations.models.Migration(id="m2"),
        ]
    )
    resp1.has_next_page = True
    resp1.next_page = "np1"

    resp2 = create_autospec(oci.response.Response)
    resp2.data = SimpleNamespace(items=[oci.cloud_migrations.models.Migration(id="m3")])
    resp2.has_next_page = False
    resp2.next_page = None

    mock_client.list_migrations.side_effect = [resp1, resp2]

    limit = 2
    async with Client(mcp) as client:
        result = (
            await client.call_tool(
                "list_migrations",
                {"compartment_id": "tenancy", "limit": limit},
            )
        ).structured_content["result"]

    assert [r["id"] for r in result] == ["m1", "m2"]
    assert mock_client.list_migrations.call_count == 1
    kwargs = mock_client.list_migrations.call_args.kwargs
    assert kwargs["limit"] == limit
    assert kwargs["page"] is None


@pytest.mark.asyncio
@patch("oracle.mcp_common.helpers._create_oci_client")
async def test_list_migrations_includes_lifecycle_state_filter(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client

    resp = create_autospec(oci.response.Response)
    resp.data = SimpleNamespace(items=[oci.cloud_migrations.models.Migration(id="x")])
    resp.has_next_page = False
    resp.next_page = None
    mock_client.list_migrations.return_value = resp

    async with Client(mcp) as client:
        await client.call_tool(
            "list_migrations",
            {"compartment_id": "tenancy", "lifecycle_state": "ACTIVE"},
        )

    kwargs = mock_client.list_migrations.call_args.kwargs
    assert kwargs["lifecycle_state"] == "ACTIVE"


@pytest.mark.asyncio
@patch("oracle.mcp_common.helpers._create_oci_client")
async def test_get_migration_exception_propagates(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    mock_client.get_migration.side_effect = RuntimeError("boom")

    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool("get_migration", {"migration_id": "ocid1.mig"})


@pytest.mark.asyncio
@patch("oracle.mcp_common.helpers._create_oci_client")
async def test_list_migrations_exception_propagates(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    mock_client.list_migrations.side_effect = ValueError("err")

    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "list_migrations", {"compartment_id": "ocid1.tenancy"}
            )
