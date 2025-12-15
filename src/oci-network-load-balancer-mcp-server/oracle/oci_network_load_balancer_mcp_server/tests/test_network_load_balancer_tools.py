"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_network_load_balancer_mcp_server.server import mcp


class TestNlbTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_network_load_balancer_mcp_server.server.get_nlb_client")
    async def test_list_nlbs(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = (
            oci.network_load_balancer.models.NetworkLoadBalancerCollection(
                items=[
                    oci.network_load_balancer.models.NetworkLoadBalancerSummary(
                        id="nlb1",
                        display_name="NLB 1",
                        lifecycle_state="ACTIVE",
                        ip_addresses=[
                            oci.network_load_balancer.models.IpAddress(
                                ip_address="192.168.1.1", is_public=True
                            ),
                            oci.network_load_balancer.models.IpAddress(
                                ip_address="10.0.0.0", is_public=False
                            ),
                        ],
                    )
                ]
            )
        )
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_network_load_balancers.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_network_load_balancers",
                    {"compartment_id": "test_compartment"},
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "nlb1"

    @pytest.mark.asyncio
    @patch("oracle.oci_network_load_balancer_mcp_server.server.get_nlb_client")
    async def test_list_listeners(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = oci.network_load_balancer.models.ListenerCollection(
            items=[
                oci.network_load_balancer.models.ListenerSummary(
                    name="Listener 1",
                    ip_version="IPV4",
                    protocol="ANY",
                    port=8008,
                    is_ppv2_enabled=False,
                )
            ]
        )
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_listeners.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_network_load_balancer_listeners",
                    {"network_load_balancer_id": "test_nlb"},
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "Listener 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_network_load_balancer_mcp_server.server.get_nlb_client")
    async def test_list_backend_sets(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = oci.network_load_balancer.models.BackendSetCollection(
            items=[
                oci.network_load_balancer.models.BackendSetSummary(
                    name="Backend Set 1",
                    ip_version="IPV4",
                    are_operationally_active_backends_preferred=False,
                    policy="THREE_TUPLE",
                    backends=[],
                )
            ]
        )
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_backend_sets.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_network_load_balancer_backend_sets",
                    {"network_load_balancer_id": "test_nlb"},
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "Backend Set 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_network_load_balancer_mcp_server.server.get_nlb_client")
    async def test_list_backends(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = oci.network_load_balancer.models.BackendCollection(
            items=[
                oci.network_load_balancer.models.BackendSummary(
                    name="Backend 1",
                    ip_address="192.168.1.1",
                    target_id="target1",
                    port=8008,
                    weight=0,
                    is_drain=False,
                    is_backup=False,
                    is_offline=False,
                )
            ]
        )
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_backends.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_network_load_balancer_backends",
                    {
                        "network_load_balancer_id": "test_nlb",
                        "backend_set_name": "test_backend_set",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "Backend 1"


class TestServer:
    @patch("oracle.oci_network_load_balancer_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_network_load_balancer_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=int(mock_env["ORACLE_MCP_PORT"]),
        )

    @patch("oracle.oci_network_load_balancer_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        import oracle.oci_network_load_balancer_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_network_load_balancer_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_network_load_balancer_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_network_load_balancer_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_network_load_balancer_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
