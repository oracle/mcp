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
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_container_repositories(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = oci.artifacts.models.ContainerRepositoryCollection(
            items=[
                oci.artifacts.models.ContainerRepositorySummary(
                    display_name="repo1",
                    id="repo1_id",
                    is_public=False,
                    compartment_id="compartment1",
                )
            ]
        )
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_container_repositories.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_container_repositories",
                {"compartment_id": "compartment1"},
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["display_name"] == "repo1"

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_get_container_repository(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.artifacts.models.ContainerRepository(
            display_name="repo1",
            id="repo1_id",
            is_public=False,
            compartment_id="compartment1",
        )
        mock_client.get_container_repository.return_value = mock_get_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_container_repository",
                    {
                        "repository_id": "repo1_id",
                    },
                )
            ).structured_content

            assert result["display_name"] == "repo1"

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_create_container_repository(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

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

            assert result["display_name"] == "repo1"

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_delete_container_repository(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_delete_response = create_autospec(oci.response.Response)
        mock_delete_response.status = 204
        mock_client.delete_container_repository.return_value = mock_delete_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "delete_container_repository",
                    {
                        "repository_id": "repo1_id",
                    },
                )
            ).structured_content

            assert result["status"] == 204

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_container_repositories_raises(self, mock_create_client):
        # Cause the tool to raise and ensure the MCP wrapper returns an error payload
        mock_create_client.side_effect = ValueError("boom")

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_container_repositories",
                {"compartment_id": "ocid1.compartment"},
                raise_on_error=False,
            )
            assert call_tool_result.is_error is True
            # The error text is present in the first content block
            assert any(
                getattr(block, "text", "").find("boom") != -1
                for block in call_tool_result.content
            )

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_get_container_repository_raises(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.get_container_repository.side_effect = RuntimeError("oops")
        mock_create_client.return_value = mock_client

        async with Client(mcp) as client:
            res = await client.call_tool(
                "get_container_repository",
                {"repository_id": "ocid1.repo"},
                raise_on_error=False,
            )
            assert res.is_error is True
            assert any(getattr(b, "text", "").find("oops") != -1 for b in res.content)

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_create_container_repository_raises(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.create_container_repository.side_effect = RuntimeError("fail")
        mock_create_client.return_value = mock_client

        async with Client(mcp) as client:
            res = await client.call_tool(
                "create_container_repository",
                {
                    "compartment_id": "ocid1.compartment",
                    "repository_name": "my/repo",
                    "is_public": True,
                },
                raise_on_error=False,
            )
            assert res.is_error is True
            assert any(getattr(b, "text", "").find("fail") != -1 for b in res.content)

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_delete_container_repository_raises(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.delete_container_repository.side_effect = RuntimeError("nope")
        mock_create_client.return_value = mock_client

        async with Client(mcp) as client:
            res = await client.call_tool(
                "delete_container_repository",
                {"repository_id": "ocid1.repo"},
                raise_on_error=False,
            )
            assert res.is_error is True
            assert any(getattr(b, "text", "").find("nope") != -1 for b in res.content)


class TestServer:
    @patch("oracle.oci_registry_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_registry_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=int(mock_env["ORACLE_MCP_PORT"]),
        )

    @patch("oracle.oci_registry_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        import oracle.oci_registry_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_registry_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_registry_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_registry_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_registry_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
