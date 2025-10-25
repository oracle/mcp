"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_migration_mcp_server.server import mcp


class TestMigrationTools:
    # @pytest.mark.asyncio
    # @patch("oracle.oci_migration_mcp_server.server.get_migration_client")
    # async def test_get_migration(self, mock_get_client):
    #    mock_client = MagicMock()
    #    mock_get_client.return_value = mock_client

    #    mock_get_response = create_autospec(oci.response.Response)
    #    mock_get_response.data = oci.cloud_migrations.models.Migration(
    #        id="migration1",
    #        display_name="Migration 1",
    #    )
    #    mock_client.get_migration.return_value = mock_get_response

    #    async with Client(mcp) as client:
    #        result = (
    #            await client.call_tool(
    #                "get_migration",
    #                {
    #                    "migration_id": "migration1",
    #                },
    #            )
    #        ).data

    #        assert result.id == "migration1"

    @pytest.mark.asyncio
    @patch("oracle.oci_migration_mcp_server.server.get_migration_client")
    async def test_list_migrations(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

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
