"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_registry_mcp_server.server import mcp


class TestRegistryTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_registry_mcp_server.server.get_ocir_client")
    async def test_create_container_repository(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_create_response = create_autospec(oci.response.Response)
        mock_create_response.data = oci.artifacts.models.ContainerRepository(
            display_name="repo1", id="repo1_id", is_public=False
        )
        mock_client.create_container_repository.return_value = mock_create_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "create_container_repository",
                    {
                        "compartment_id": "compartment1",
                        "repository_name": "repo1",
                    },
                )
            ).structured_content

            assert result["repository_name"] == "repo1"

    # @pytest.mark.asyncio
    # @patch("oracle.oci_registry_mcp_server.server.get_ocir_client")
    # async def test_list_container_repositories(self, mock_get_client):
    #    mock_client = MagicMock()
    #    mock_get_client.return_value = mock_client

    #    mock_list_response = create_autospec(oci.response.Response)
    #    mock_list_response.data = oci.artifacts.models.ContainerRepositoryCollection(
    #        items=[MagicMock(display_name="repo1", id="repo1_id", is_public=False)]
    #    )
    #    mock_client.list_container_repositories.return_value = mock_list_response

    #    async with Client(mcp) as client:
    #        result = (
    #            await client.call_tool(
    #                "list_container_repositories",
    #                {
    #                    "compartment_id": "compartment1",
    #                },
    #            )
    #        ).structured_content

    #        assert len(result) == 1
    #        assert result[0]["repository_name"] == "repo1"

    @pytest.mark.asyncio
    @patch("oracle.oci_registry_mcp_server.server.get_ocir_client")
    async def test_get_container_repo_details(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = MagicMock(
            display_name="repo1",
            id="repo1_id",
            is_public=False,
            compartment_id="compartment1",
        )
        mock_client.get_container_repository.return_value = mock_get_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_container_repo_details",
                    {
                        "repository_id": "repo1_id",
                    },
                )
            ).data

            assert result["repository_name"] == "repo1"

    @pytest.mark.asyncio
    @patch("oracle.oci_registry_mcp_server.server.get_ocir_client")
    async def test_delete_container_repository(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_delete_response = create_autospec(oci.response.Response)
        mock_client.delete_container_repository.return_value = mock_delete_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "delete_container_repository",
                    {
                        "repository_id": "repo1_id",
                    },
                )
            ).data

            assert result["success"]
