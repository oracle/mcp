"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_identity_mcp_server.server import mcp


class TestIdentityTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    async def test_list_compartments(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.identity.models.Compartment(
                id="compartment1",
                compartment_id="compartment1",
                name="Compartment 1",
                description="Test compartment",
                lifecycle_state="ACTIVE",
                time_created="1970-01-01T00:00:00",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_compartments.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_compartments",
                    {
                        "compartment_id": "test_tenancy",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "compartment1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    async def test_list_availability_domains(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.identity.models.AvailabilityDomain(
                id="ad1",
                name="AD-1",
                compartment_id="compartment1",
            )
        ]
        mock_client.list_availability_domains.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_availability_domains",
                    {
                        "compartment_id": "test_tenancy",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "ad1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    async def test_get_tenancy(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.identity.models.Tenancy(
            id="tenancy1",
            name="Tenancy 1",
            description="Test tenancy",
            home_region_key="PHX",
        )
        mock_client.get_tenancy.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_tenancy",
                {
                    "tenancy_id": "test_tenancy",
                },
            )
            result = call_tool_result.structured_content

            assert result["id"] == "tenancy1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    async def test_get_current_tenancy(self, mock_config_from_file, mock_get_client):
        mock_config_from_file.return_value = {"tenancy": "test_tenancy"}
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.identity.models.Tenancy(
            id="tenancy1",
            name="Tenancy 1",
            description="Test tenancy",
            home_region_key="PHX",
        )
        mock_client.get_tenancy.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_current_tenancy",
                {},
            )
            result = call_tool_result.structured_content

            assert result["id"] == "tenancy1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    async def test_create_auth_token(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_create_response = create_autospec(oci.response.Response)
        mock_create_response.data = oci.identity.models.AuthToken(
            token="token1", description="Test token", lifecycle_state="ACTIVE"
        )
        mock_client.create_auth_token.return_value = mock_create_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "create_auth_token",
                {
                    "user_id": "test_user",
                },
            )
            result = call_tool_result.structured_content

            assert result["token"] == "token1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    async def test_get_current_user(self, mock_config_from_file, mock_get_client):
        mock_config_from_file.return_value = {"user": "test_user"}
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.identity.models.User(
            id="user1", name="User 1", description="Test user"
        )
        mock_client.get_user.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_current_user",
                {},
            )
            result = call_tool_result.structured_content

            assert result["id"] == "user1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    async def test_get_compartment_by_name(self, mock_get_client):
        """
        Tests finding a compartment by name, including simulating pagination
        where the target is on the second page.
        """
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response_p1 = create_autospec(oci.response.Response)
        mock_response_p1.data = [
            oci.identity.models.Compartment(name="WrongName", id="wrong_id")
        ]
        mock_response_p1.has_next_page = True
        mock_response_p1.next_page = "page_2_token"

        mock_response_p2 = create_autospec(oci.response.Response)
        mock_response_p2.data = [
            oci.identity.models.Compartment(
                name="TargetComp",
                id="target_id",
                lifecycle_state="ACTIVE",
                time_created="2023-01-01T00:00:00.000Z",
            )
        ]
        mock_response_p2.has_next_page = False
        mock_response_p2.next_page = None

        mock_client.list_compartments.side_effect = [mock_response_p1, mock_response_p2]

        async with Client(mcp) as client:
            raw_content = (
                await client.call_tool(
                    "get_compartment_by_name",
                    {
                        "name": "TargetComp",
                        "parent_compartment_id": "test_parent_id",
                    },
                )
            ).structured_content

            if "result" in raw_content:
                result = raw_content["result"]
            else:
                result = raw_content

            assert result["id"] == "target_id"
            assert result["name"] == "TargetComp"

            assert mock_client.list_compartments.call_count == 2

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    async def test_list_subscribed_regions(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.identity.models.RegionSubscription(
                region_name="us-phoenix-1",
                region_key="PHX",
                status="READY",
                is_home_region=True,
            ),
            oci.identity.models.RegionSubscription(
                region_name="us-ashburn-1",
                region_key="IAD",
                status="READY",
                is_home_region=False,
            ),
        ]
        mock_client.list_region_subscriptions.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_subscribed_regions",
                    {
                        "tenancy_id": "test_tenancy",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 2
            assert result[0]["region_name"] == "us-phoenix-1"
            assert result[0]["is_home_region"] is True
            assert result[1]["region_key"] == "IAD"


class TestServer:
    @patch("oracle.oci_identity_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_identity_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=int(mock_env["ORACLE_MCP_PORT"]),
        )

    @patch("oracle.oci_identity_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        import oracle.oci_identity_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_identity_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_identity_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_identity_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_identity_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
