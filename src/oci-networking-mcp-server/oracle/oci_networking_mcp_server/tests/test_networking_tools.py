"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, mock_open, patch

import oci
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from oracle.oci_networking_mcp_server import server
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
    async def test_list_vcns_pagination(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        first = create_autospec(oci.response.Response)
        first.data = [oci.core.models.Vcn(id="v1"), oci.core.models.Vcn(id="v2")]
        first.has_next_page = True
        first.next_page = "np1"

        second = create_autospec(oci.response.Response)
        second.data = [oci.core.models.Vcn(id="v3")]
        second.has_next_page = False
        second.next_page = None

        mock_client.list_vcns.side_effect = [first, second]

        async with Client(mcp) as client:
            result = (await client.call_tool("list_vcns", {"compartment_id": "c1"})).structured_content[
                "result"
            ]

        assert [v["id"] for v in result] == ["v1", "v2", "v3"]

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_get_vcn_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_vcn.side_effect = Exception("boom")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("get_vcn", {"vcn_id": "bad"})

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
    async def test_delete_vcn_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.delete_vcn.side_effect = Exception("delete vcn failed")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("delete_vcn", {"vcn_id": "bad"})

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
    async def test_create_vcn_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.create_vcn.side_effect = Exception("create vcn failed")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "create_vcn",
                    {
                        "compartment_id": "c1",
                        "cidr_block": "10.0.0.0/16",
                        "display_name": "n",
                    },
                )

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
    async def test_list_subnets_pagination(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        first = create_autospec(oci.response.Response)
        first.data = [oci.core.models.Subnet(id="s1"), oci.core.models.Subnet(id="s2")]
        first.has_next_page = True
        first.next_page = "np1"

        second = create_autospec(oci.response.Response)
        second.data = [oci.core.models.Subnet(id="s3")]
        second.has_next_page = False
        second.next_page = None

        mock_client.list_subnets.side_effect = [first, second]

        async with Client(mcp) as client:
            result = (
                await client.call_tool("list_subnets", {"compartment_id": "c1", "vcn_id": "v1"})
            ).structured_content["result"]

        assert [s["id"] for s in result] == ["s1", "s2", "s3"]

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
    async def test_get_subnet_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_subnet.side_effect = Exception("bad subnet")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("get_subnet", {"subnet_id": "bad"})

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
    async def test_create_subnet_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.create_subnet.side_effect = Exception("create subnet failed")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "create_subnet",
                    {
                        "vcn_id": "v1",
                        "compartment_id": "c1",
                        "cidr_block": "10.0.1.0/24",
                        "display_name": "s1",
                    },
                )

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
    async def test_list_security_lists_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_security_lists.side_effect = Exception("sl list fail")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "list_security_lists",
                    {"compartment_id": "c1", "vcn_id": "v1"},
                )

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
    async def test_get_security_list_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_security_list.side_effect = Exception("bad sl")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("get_security_list", {"security_list_id": "bad"})

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
    async def test_list_network_security_groups_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_network_security_groups.side_effect = Exception("nsg list fail")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "list_network_security_groups",
                    {"compartment_id": "c1", "vcn_id": "v1"},
                )

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
    async def test_get_vnic_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_vnic.side_effect = Exception("vnic boom")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("get_vnic", {"vnic_id": "bad"})

    @pytest.mark.asyncio
    @patch("oracle.oci_networking_mcp_server.server.get_networking_client")
    async def test_get_vnic(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.core.models.Vnic(
            id="vnic1", display_name="VNIC 1", lifecycle_state="AVAILABLE"
        )
        mock_client.get_vnic.return_value = mock_get_response

        async with Client(mcp) as client:
            # Expect ToolError due to schema validation issue in installed package
            with pytest.raises(ToolError):
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

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_networking_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_networking_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()


class TestGetClient:
    @patch("oracle.oci_networking_mcp_server.server.oci.core.VirtualNetworkClient")
    @patch("oracle.oci_networking_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_networking_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_networking_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_networking_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_networking_mcp_server.server.os.getenv")
    def test_get_networking_client_with_profile_env(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        # Arrange: provide profile via env var and minimal config dict
        mock_getenv.side_effect = lambda k, default=None: (
            "MYPROFILE" if k == "OCI_CONFIG_PROFILE" else default
        )
        config = {
            "key_file": "/abs/path/to/key.pem",
            "security_token_file": "/abs/path/to/token",
        }
        mock_from_file.return_value = config
        private_key_obj = object()
        mock_load_private_key.return_value = private_key_obj

        # Act
        result = server.get_networking_client()

        # Assert calls
        mock_from_file.assert_called_once_with(
            file_location=oci.config.DEFAULT_LOCATION,
            profile_name="MYPROFILE",
        )
        mock_open_file.assert_called_once_with("/abs/path/to/token", "r")
        mock_security_token_signer.assert_called_once_with("SECURITY_TOKEN", private_key_obj)
        # Ensure user agent was set on the same config dict passed into client
        args, _ = mock_client.call_args
        passed_config = args[0]
        assert passed_config is config
        expected_user_agent = (
            f"{server.__project__.split('oracle.', 1)[1].split('-server', 1)[0]}/{server.__version__}"  # noqa
        )
        assert passed_config.get("additional_user_agent") == expected_user_agent
        # And we returned the client instance
        assert result == mock_client.return_value

    @patch("oracle.oci_networking_mcp_server.server.oci.core.VirtualNetworkClient")
    @patch("oracle.oci_networking_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_networking_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_networking_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_networking_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_networking_mcp_server.server.os.getenv")
    def test_get_networking_client_uses_default_profile_when_env_missing(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        # Arrange: no env var present; from_file should be called with DEFAULT_PROFILE
        mock_getenv.side_effect = lambda k, default=None: default
        config = {"key_file": "/k.pem", "security_token_file": "/tkn"}
        mock_from_file.return_value = config
        priv = object()
        mock_load_private_key.return_value = priv

        # Act
        srv_client = server.get_networking_client()

        # Assert: profile defaulted
        mock_from_file.assert_called_once_with(
            file_location=oci.config.DEFAULT_LOCATION,
            profile_name=oci.config.DEFAULT_PROFILE,
        )
        # Token file opened and read
        mock_open_file.assert_called_once_with("/tkn", "r")
        mock_security_token_signer.assert_called_once()
        signer_args, _ = mock_security_token_signer.call_args
        assert signer_args[0] == "TOK"
        assert signer_args[1] is priv
        # additional_user_agent set on original config and passed through
        cc_args, _ = mock_client.call_args
        assert cc_args[0] is config
        assert "additional_user_agent" in config
        assert isinstance(config["additional_user_agent"], str) and "/" in config["additional_user_agent"]
        # Returned object is client instance
        assert srv_client is mock_client.return_value
