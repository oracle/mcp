"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_networking_mcp_server.server import mcp


class TestNetworkingTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_list_vcns(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.core.models.Vcn(
                id="vcn1",
                display_name="VCN 1",
                lifecycle_state="AVAILABLE",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_vcns.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_vcns",
                {
                    "compartment_id": "compartment1",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "vcn1"

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_get_vcn(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.core.models.Vcn(
            id="vcn1", display_name="VCN 1", lifecycle_state="AVAILABLE"
        )
        mock_client.get_vcn.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_vcn",
                {
                    "vcn_id": "vcn1",
                },
            )
            result = call_tool_result.structured_content

            assert result["id"] == "vcn1"

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_delete_vcn(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_delete_response = create_autospec(oci.response.Response)
        mock_delete_response.status = 204
        mock_client.delete_vcn.return_value = mock_delete_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "delete_vcn",
                {
                    "vcn_id": "vcn1",
                },
            )
            result = call_tool_result.structured_content

            assert result["status"] == 204

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_create_vcn(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_create_response = create_autospec(oci.response.Response)
        mock_create_response.data = oci.core.models.Vcn(
            id="vcn1", display_name="VCN 1", lifecycle_state="PROVISIONING"
        )
        mock_client.create_vcn.return_value = mock_create_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "create_vcn",
                {
                    "compartment_id": "compartment1",
                    "cidr_block": "10.0.0.0/16",
                    "display_name": "VCN 1",
                },
            )
            result = call_tool_result.structured_content

            assert result["id"] == "vcn1"

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_list_subnets(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.core.models.Subnet(
                id="subnet1",
                vcn_id="vcn1",
                display_name="Subnet 1",
                lifecycle_state="AVAILABLE",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_subnets.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_subnets",
                {
                    "compartment_id": "compartment1",
                    "vcn_id": "vcn1",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "subnet1"

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_get_subnet(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.core.models.Subnet(
            id="subnet1",
            vcn_id="vcn1",
            display_name="Subnet 1",
            lifecycle_state="AVAILABLE",
        )
        mock_client.get_subnet.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_subnet",
                {
                    "subnet_id": "subnet1",
                },
            )
            result = call_tool_result.structured_content

            assert result["id"] == "subnet1"

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_create_subnet(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_create_response = create_autospec(oci.response.Response)
        mock_create_response.data = oci.core.models.Subnet(
            id="subnet1", display_name="Subnet 1", lifecycle_state="PROVISIONING"
        )
        mock_client.create_subnet.return_value = mock_create_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "create_subnet",
                {
                    "vcn_id": "vcn1",
                    "compartment_id": "compartment1",
                    "cidr_block": "10.0.1.0/24",
                    "display_name": "Subnet 1",
                },
            )
            result = call_tool_result.structured_content

            assert result["id"] == "subnet1"

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_list_security_lists(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.core.models.SecurityList(
                id="securitylist1",
                display_name="Security List 1",
                lifecycle_state="AVAILABLE",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_security_lists.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_security_lists",
                {
                    "compartment_id": "compartment1",
                    "vcn_id": "vcn1",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "securitylist1"

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_get_security_list(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.core.models.SecurityList(
            id="securitylist1",
            display_name="Security List 1",
            lifecycle_state="AVAILABLE",
        )
        mock_client.get_security_list.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_security_list",
                {
                    "security_list_id": "securitylist1",
                },
            )
            result = call_tool_result.structured_content

            assert result["id"] == "securitylist1"

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_list_network_security_groups(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.core.models.NetworkSecurityGroup(
                id="nsg1",
                display_name="Nsg 1",
                lifecycle_state="AVAILABLE",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_network_security_groups.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_network_security_groups",
                {
                    "compartment_id": "compartment1",
                    "vcn_id": "vcn1",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "nsg1"

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_get_network_security_group(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.core.models.NetworkSecurityGroup(
            id="nsg1",
            display_name="Nsg 1",
            lifecycle_state="AVAILABLE",
        )
        mock_client.get_network_security_group.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_network_security_group",
                {
                    "network_security_group_id": "nsg1",
                },
            )
            result = call_tool_result.structured_content

            assert result["id"] == "nsg1"

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def get_get_vnic(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.core.models.Vnic(
            id="vnic1", display_name="VNIC 1", lifecycle_state="AVAILABLE"
        )
        mock_client.get_vnic.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool("get_vnic", {"vnic_id": "vnic1"})
            result = call_tool_result.structured_content

            assert result["id"] == "vnic1"


class TestServer:
    @patch("oracle.oci_networking_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_networking_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=int(mock_env["ORACLE_MCP_PORT"]),
        )

    @patch("oracle.oci_networking_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        import oracle.oci_networking_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_networking_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_networking_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_networking_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_networking_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
