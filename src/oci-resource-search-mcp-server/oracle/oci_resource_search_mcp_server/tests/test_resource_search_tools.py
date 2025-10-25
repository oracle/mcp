"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_resource_search_mcp_server.server import mcp


class TestResourceSearchTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_resource_search_mcp_server.server.get_search_client")
    async def test_list_all_resources(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_search_response = create_autospec(oci.response.Response)
        mock_search_response.data = (
            oci.resource_search.models.ResourceSummaryCollection(
                items=[
                    oci.resource_search.models.ResourceSummary(
                        identifier="resource1",
                        display_name="Resource 1",
                        resource_type="instance",
                        lifecycle_state="RUNNING",
                    )
                ]
            )
        )
        mock_client.search_resources.return_value = mock_search_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_all_resources",
                    {
                        "compartment_id": "compartment1",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["resource_id"] == "resource1"

    @pytest.mark.asyncio
    @patch("oracle.oci_resource_search_mcp_server.server.get_search_client")
    async def test_search_resources(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_search_response = create_autospec(oci.response.Response)
        mock_search_response.data = (
            oci.resource_search.models.ResourceSummaryCollection(
                items=[
                    oci.resource_search.models.ResourceSummary(
                        identifier="resource1",
                        display_name="Resource 1",
                        resource_type="instance",
                        lifecycle_state="RUNNING",
                    )
                ]
            )
        )
        mock_client.search_resources.return_value = mock_search_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "search_resources",
                    {
                        "compartment_id": "compartment1",
                        "display_name": "Resource",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["resource_id"] == "resource1"

    @pytest.mark.asyncio
    @patch("oracle.oci_resource_search_mcp_server.server.get_search_client")
    async def test_search_resources_free_form(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_search_response = create_autospec(oci.response.Response)
        mock_search_response.data = (
            oci.resource_search.models.ResourceSummaryCollection(
                items=[
                    oci.resource_search.models.ResourceSummary(
                        identifier="resource1",
                        display_name="Resource 1",
                        resource_type="instance",
                        lifecycle_state="RUNNING",
                    )
                ]
            )
        )
        mock_client.search_resources.return_value = mock_search_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "search_resources_free_form",
                    {
                        "compartment_id": "compartment1",
                        "text": "Resource",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["resource_id"] == "resource1"

    @pytest.mark.asyncio
    @patch("oracle.oci_resource_search_mcp_server.server.get_search_client")
    async def test_list_resource_types(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.resource_search.models.ResourceType(name="instance"),
            oci.resource_search.models.ResourceType(name="volume"),
        ]
        mock_client.list_resource_types.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (await client.call_tool("list_resource_types", {})).data

            assert result == ["instance", "volume"]
