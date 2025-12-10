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
        mock_search_response.has_next_page = False
        mock_search_response.next_page = None
        mock_client.search_resources.return_value = mock_search_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_all_resources",
                    {
                        "tenant_id": "tenant1",
                        "compartment_id": "compartment1",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["identifier"] == "resource1"

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
        mock_search_response.has_next_page = False
        mock_search_response.next_page = None
        mock_client.search_resources.return_value = mock_search_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "search_resources",
                    {
                        "tenant_id": "tenant1",
                        "compartment_id": "compartment1",
                        "display_name": "Resource",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["identifier"] == "resource1"

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
        mock_search_response.has_next_page = False
        mock_search_response.next_page = None
        mock_client.search_resources.return_value = mock_search_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "search_resources_free_form",
                    {
                        "tenant_id": "tenant1",
                        "text": "Resource",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["identifier"] == "resource1"

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
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_resource_types.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (await client.call_tool("list_resource_types", {})).data

            assert result == ["instance", "volume"]


class TestServer:
    @patch("oracle.oci_resource_search_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_resource_search_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=int(mock_env["ORACLE_MCP_PORT"]),
        )

    @patch("oracle.oci_resource_search_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        import oracle.oci_resource_search_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_resource_search_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_resource_search_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_resource_search_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_resource_search_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
