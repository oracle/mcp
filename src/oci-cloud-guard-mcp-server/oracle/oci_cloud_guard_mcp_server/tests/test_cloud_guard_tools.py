"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# noinspection PyPackageRequirements
from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_cloud_guard_mcp_server.server import mcp


class TestResourceSearchTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_cloud_guard_mcp_server.server.get_cloud_guard_client")
    async def test_list_all_problems(self, mock_get_client):
        resource_id = "ocid.resource1"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_problems_response = create_autospec(oci.response.Response)
        mock_problems_response.data = oci.cloud_guard.models.ProblemCollection(
            items=[
                oci.cloud_guard.models.ProblemSummary(
                    id=resource_id,
                    resource_type="instance",
                    resource_id="resource1",
                    lifecycle_state="ACTIVE",
                    lifecycle_detail="OPEN",
                )
            ]
        )
        mock_client.list_problems.return_value = mock_problems_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_problems", {"compartment_id": "test_compartment"}
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == resource_id

    @pytest.mark.asyncio
    @patch("oracle.oci_cloud_guard_mcp_server.server.get_cloud_guard_client")
    async def test_get_problem_details(self, mock_get_client):
        problem_id = "ocid.resource1"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_problem_response = create_autospec(oci.response.Response)
        mock_get_problem_response.data = oci.cloud_guard.models.Problem(
            id=problem_id,
            resource_type="instance",
            resource_id="resource1",
            lifecycle_state="ACTIVE",
            lifecycle_detail="OPEN",
            compartment_id="test_compartment",
            region="test_region",
            impacted_resource_type="123",
            impacted_resource_name="123",
            risk_level="HIGH",
        )
        mock_client.get_problem.return_value = mock_get_problem_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_problem_details",
                    {
                        "problem_id": problem_id,
                    },
                )
            ).structured_content

            assert result["id"] == problem_id

    @pytest.mark.asyncio
    @patch("oracle.oci_cloud_guard_mcp_server.server.get_cloud_guard_client")
    async def test_update_problem_status(self, mock_get_client):
        problem_id = "ocid.resource1"
        status = "OPEN"
        comment = "this is updated with ai"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_update_problem_status_response = create_autospec(oci.response.Response)
        mock_update_problem_status_response.data = oci.cloud_guard.models.Problem(
            id=problem_id,
            resource_type="instance",
            resource_id="resource1",
            lifecycle_state="ACTIVE",
            lifecycle_detail=status,
            comment=comment,
        )
        mock_client.update_problem_status.return_value = (
            mock_update_problem_status_response
        )

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "update_problem_status",
                    {"problem_id": problem_id, "status": status, "comment": comment},
                )
            ).structured_content

            print(result)
            assert result["id"] == problem_id
            assert result["lifecycle_detail"] == status
            assert result["comment"] == comment


class TestServer:
    @patch("oracle.oci_cloud_guard_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_cloud_guard_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=int(mock_env["ORACLE_MCP_PORT"]),
        )

    @patch("oracle.oci_cloud_guard_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        import oracle.oci_cloud_guard_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_cloud_guard_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_cloud_guard_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_cloud_guard_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_cloud_guard_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
