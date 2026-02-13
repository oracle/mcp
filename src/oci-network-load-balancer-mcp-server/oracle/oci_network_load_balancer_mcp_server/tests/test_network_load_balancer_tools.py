"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from oracle.oci_network_load_balancer_mcp_server import server
from oracle.oci_network_load_balancer_mcp_server.server import mcp


@pytest.fixture
def mock_nlb_client():
    with patch("oracle.mcp_common.helpers._create_oci_client") as mock_create_client:
        client = MagicMock()
        mock_create_client.return_value = client
        yield client


class TestNlbTools:
    @pytest.mark.asyncio
    async def test_list_nlbs(self, mock_nlb_client):

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
        mock_nlb_client.list_network_load_balancers.return_value = mock_list_response

        async with Client(mcp) as client:
            response = await client.call_tool(
                "list_network_load_balancers",
                {"compartment_id": "test_compartment"},
            )
            assert response.structured_content is not None
            result = response.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "nlb1"

    @pytest.mark.asyncio
    async def test_list_nlbs_pagination(self, mock_nlb_client):

        first = create_autospec(oci.response.Response)
        first.data = oci.network_load_balancer.models.NetworkLoadBalancerCollection(
            items=[
                oci.network_load_balancer.models.NetworkLoadBalancerSummary(id="n1"),
                oci.network_load_balancer.models.NetworkLoadBalancerSummary(id="n2"),
            ]
        )
        first.has_next_page = True
        first.next_page = "np1"

        second = create_autospec(oci.response.Response)
        second.data = oci.network_load_balancer.models.NetworkLoadBalancerCollection(
            items=[oci.network_load_balancer.models.NetworkLoadBalancerSummary(id="n3")]
        )
        second.has_next_page = False
        second.next_page = None

        mock_nlb_client.list_network_load_balancers.side_effect = [first, second]

        async with Client(mcp) as client:
            response = await client.call_tool(
                "list_network_load_balancers", {"compartment_id": "c1"}
            )
            assert response.structured_content is not None
            result = response.structured_content["result"]

        assert [n["id"] for n in result] == ["n1", "n2", "n3"]

    @pytest.mark.asyncio
    async def test_list_nlbs_error(self, mock_nlb_client):
        mock_nlb_client.list_network_load_balancers.side_effect = Exception("boom")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "list_network_load_balancers", {"compartment_id": "c1"}
                )

    @pytest.mark.asyncio
    async def test_list_listeners(self, mock_nlb_client):

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
        mock_nlb_client.list_listeners.return_value = mock_list_response

        async with Client(mcp) as client:
            response = await client.call_tool(
                "list_network_load_balancer_listeners",
                {"network_load_balancer_id": "test_nlb"},
            )
            assert response.structured_content is not None
            result = response.structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "Listener 1"

    @pytest.mark.asyncio
    async def test_list_listeners_pagination(self, mock_nlb_client):

        first = create_autospec(oci.response.Response)
        first.data = oci.network_load_balancer.models.ListenerCollection(
            items=[
                oci.network_load_balancer.models.ListenerSummary(name="listener1"),
                oci.network_load_balancer.models.ListenerSummary(name="listener2"),
            ]
        )
        first.has_next_page = True
        first.next_page = "np1"

        second = create_autospec(oci.response.Response)
        second.data = oci.network_load_balancer.models.ListenerCollection(
            items=[oci.network_load_balancer.models.ListenerSummary(name="listener3")]
        )
        second.has_next_page = False
        second.next_page = None

        mock_nlb_client.list_listeners.side_effect = [first, second]

        async with Client(mcp) as client:
            response = await client.call_tool(
                "list_network_load_balancer_listeners",
                {"network_load_balancer_id": "nlb1"},
            )
            assert response.structured_content is not None
            result = response.structured_content["result"]

        assert [listener["name"] for listener in result] == [
            "listener1",
            "listener2",
            "listener3",
        ]

    @pytest.mark.asyncio
    async def test_list_listeners_error(self, mock_nlb_client):
        mock_nlb_client.list_listeners.side_effect = Exception("fail list")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "list_network_load_balancer_listeners",
                    {"network_load_balancer_id": "n1"},
                )

    @pytest.mark.asyncio
    async def test_list_backend_sets(self, mock_nlb_client):

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
        mock_nlb_client.list_backend_sets.return_value = mock_list_response

        async with Client(mcp) as client:
            response = await client.call_tool(
                "list_network_load_balancer_backend_sets",
                {"network_load_balancer_id": "test_nlb"},
            )
            assert response.structured_content is not None
            result = response.structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "Backend Set 1"

    @pytest.mark.asyncio
    async def test_list_backend_sets_pagination(self, mock_nlb_client):

        first = create_autospec(oci.response.Response)
        first.data = oci.network_load_balancer.models.BackendSetCollection(
            items=[
                oci.network_load_balancer.models.BackendSetSummary(name="bs1"),
                oci.network_load_balancer.models.BackendSetSummary(name="bs2"),
            ]
        )
        first.has_next_page = True
        first.next_page = "np1"

        second = create_autospec(oci.response.Response)
        second.data = oci.network_load_balancer.models.BackendSetCollection(
            items=[oci.network_load_balancer.models.BackendSetSummary(name="bs3")]
        )
        second.has_next_page = False
        second.next_page = None

        mock_nlb_client.list_backend_sets.side_effect = [first, second]

        async with Client(mcp) as client:
            response = await client.call_tool(
                "list_network_load_balancer_backend_sets",
                {"network_load_balancer_id": "nlb1"},
            )
            assert response.structured_content is not None
            result = response.structured_content["result"]

        assert [b["name"] for b in result] == ["bs1", "bs2", "bs3"]

    @pytest.mark.asyncio
    async def test_list_backend_sets_error(self, mock_nlb_client):
        mock_nlb_client.list_backend_sets.side_effect = Exception("fail bs")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "list_network_load_balancer_backend_sets",
                    {"network_load_balancer_id": "nlb1"},
                )

    @pytest.mark.asyncio
    async def test_list_backends(self, mock_nlb_client):

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
        mock_nlb_client.list_backends.return_value = mock_list_response

        async with Client(mcp) as client:
            response = await client.call_tool(
                "list_network_load_balancer_backends",
                {
                    "network_load_balancer_id": "test_nlb",
                    "backend_set_name": "test_backend_set",
                },
            )
            assert response.structured_content is not None
            result = response.structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "Backend 1"

    @pytest.mark.asyncio
    async def test_list_backends_pagination(self, mock_nlb_client):

        first = create_autospec(oci.response.Response)
        first.data = oci.network_load_balancer.models.BackendCollection(
            items=[
                oci.network_load_balancer.models.BackendSummary(name="b1"),
                oci.network_load_balancer.models.BackendSummary(name="b2"),
            ]
        )
        first.has_next_page = True
        first.next_page = "np1"

        second = create_autospec(oci.response.Response)
        second.data = oci.network_load_balancer.models.BackendCollection(
            items=[oci.network_load_balancer.models.BackendSummary(name="b3")]
        )
        second.has_next_page = False
        second.next_page = None

        mock_nlb_client.list_backends.side_effect = [first, second]

        async with Client(mcp) as client:
            response = await client.call_tool(
                "list_network_load_balancer_backends",
                {
                    "network_load_balancer_id": "nlb1",
                    "backend_set_name": "bs1",
                },
            )
            assert response.structured_content is not None
            result = response.structured_content["result"]

        assert [b["name"] for b in result] == ["b1", "b2", "b3"]

    @pytest.mark.asyncio
    async def test_list_backends_error(self, mock_nlb_client):
        mock_nlb_client.list_backends.side_effect = Exception("fail backends")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "list_network_load_balancer_backends",
                    {
                        "network_load_balancer_id": "nlb1",
                        "backend_set_name": "bs1",
                    },
                )

    @pytest.mark.asyncio
    async def test_get_network_load_balancer(self, mock_nlb_client):

        mock_resp = create_autospec(oci.response.Response)
        mock_resp.data = oci.network_load_balancer.models.NetworkLoadBalancer(
            id="nlb1", display_name="nlb"
        )
        mock_nlb_client.get_network_load_balancer.return_value = mock_resp

        async with Client(mcp) as client:
            response = await client.call_tool(
                "get_network_load_balancer", {"network_load_balancer_id": "nlb1"}
            )
            assert response.structured_content is not None
            res = response.structured_content
        assert res["id"] == "nlb1"

    @pytest.mark.asyncio
    async def test_get_network_load_balancer_error(self, mock_nlb_client):
        mock_nlb_client.get_network_load_balancer.side_effect = Exception("bad nlb")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "get_network_load_balancer", {"network_load_balancer_id": "x"}
                )

    @pytest.mark.asyncio
    async def test_get_listener(self, mock_nlb_client):

        mock_resp = create_autospec(oci.response.Response)
        mock_resp.data = oci.network_load_balancer.models.Listener(name="l1")
        mock_nlb_client.get_listener.return_value = mock_resp

        async with Client(mcp) as client:
            response = await client.call_tool(
                "get_network_load_balancer_listener",
                {"network_load_balancer_id": "nlb1", "listener_name": "l1"},
            )
            assert response.structured_content is not None
            res = response.structured_content
        assert res["name"] == "l1"

    @pytest.mark.asyncio
    async def test_get_listener_error(self, mock_nlb_client):
        mock_nlb_client.get_listener.side_effect = Exception("bad listener")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "get_network_load_balancer_listener",
                    {"network_load_balancer_id": "nlb1", "listener_name": "l1"},
                )

    @pytest.mark.asyncio
    async def test_get_backend_set(self, mock_nlb_client):

        mock_resp = create_autospec(oci.response.Response)
        mock_resp.data = oci.network_load_balancer.models.BackendSet(name="bs1")
        mock_nlb_client.get_backend_set.return_value = mock_resp

        async with Client(mcp) as client:
            response = await client.call_tool(
                "get_network_load_balancer_backend_set",
                {
                    "network_load_balancer_id": "nlb1",
                    "backend_set_name": "bs1",
                },
            )
            assert response.structured_content is not None
            res = response.structured_content
        assert res["name"] == "bs1"

    @pytest.mark.asyncio
    async def test_get_backend_set_error(self, mock_nlb_client):
        mock_nlb_client.get_backend_set.side_effect = Exception("bad bs")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "get_network_load_balancer_backend_set",
                    {"network_load_balancer_id": "nlb1", "backend_set_name": "bs1"},
                )

    @pytest.mark.asyncio
    async def test_get_backend(self, mock_nlb_client):

        mock_resp = create_autospec(oci.response.Response)
        mock_resp.data = oci.network_load_balancer.models.Backend(name="b1")
        mock_nlb_client.get_backend.return_value = mock_resp

        async with Client(mcp) as client:
            response = await client.call_tool(
                "get_network_load_balancer_backend",
                {
                    "network_load_balancer_id": "nlb1",
                    "backend_set_name": "bs1",
                    "backend_name": "b1",
                },
            )
            assert response.structured_content is not None
            res = response.structured_content
        assert res["name"] == "b1"

    @pytest.mark.asyncio
    async def test_get_backend_error(self, mock_nlb_client):
        mock_nlb_client.get_backend.side_effect = Exception("bad backend")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "get_network_load_balancer_backend",
                    {
                        "network_load_balancer_id": "nlb1",
                        "backend_set_name": "bs1",
                        "backend_name": "b1",
                    },
                )


class TestServer:
    @patch("oracle.oci_network_load_balancer_mcp_server.server.mcp.run")
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

    @patch("oracle.oci_network_load_balancer_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_network_load_balancer_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_network_load_balancer_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()
