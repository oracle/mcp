"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import base64
import json
import os
from unittest.mock import MagicMock, create_autospec, mock_open, patch

import oci
import oracle.oci_identity_mcp_server.server as server
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from oracle.oci_identity_mcp_server.server import mcp


@pytest.fixture
def mock_identity_client():
    client = MagicMock()
    with patch(
        "oracle.mcp_common.helpers._create_oci_client",
        return_value=client,
    ):
        yield client


class TestIdentityTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    async def test_list_compartments(self, mock_config_from_file, mock_identity_client):
        mock_config_from_file.return_value = {"tenancy": "test_tenancy"}

        mock_list_response = create_autospec(oci.response.Response)
        mock_get_response = create_autospec(oci.response.Response)
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

        mock_get_response.data = oci.identity.models.Compartment(
            id="tenancy1",
            compartment_id=None,
            name="Root Compartment",
            description="Test compartment (root)",
            lifecycle_state="ACTIVE",
            time_created="1970-01-01T00:00:00",
        )
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_identity_client.list_compartments.return_value = mock_list_response
        mock_identity_client.get_compartment.return_value = mock_get_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_compartments",
                    {
                        "compartment_id": "test_tenancy",
                        "compartment_id_in_subtree": True,
                    },
                )
            ).structured_content["result"]

            assert len(result) == 2
            assert result[0]["id"] == "compartment1"
            assert result[1]["id"] == "tenancy1"

    @pytest.mark.asyncio
    async def test_list_compartments_without_root(self, mock_identity_client):
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
        mock_identity_client.list_compartments.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_compartments",
                    {
                        "compartment_id": "test_tenancy",
                        "compartment_id_in_subtree": True,
                        "include_root": False,
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "compartment1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    async def test_list_compartments_pagination_without_limit(
        self, mock_config_from_file, mock_identity_client
    ):
        mock_config_from_file.return_value = {"tenancy": "test_tenancy"}

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.identity.models.Compartment(
            id="tenancy1",
            compartment_id=None,
            name="Root Compartment",
            description="Test compartment (root)",
            lifecycle_state="ACTIVE",
            time_created="1970-01-01T00:00:00",
        )

        # Page 1
        resp1 = create_autospec(oci.response.Response)
        resp1.data = [
            oci.identity.models.Compartment(
                id="c1",
                name="C1",
                description="Test compartment",
                lifecycle_state="ACTIVE",
                time_created="1970-01-01T00:00:00",
            ),
            oci.identity.models.Compartment(
                id="c2",
                name="C2",
                description="Test compartment",
                lifecycle_state="ACTIVE",
                time_created="1970-01-01T00:00:00",
            ),
        ]
        resp1.has_next_page = True
        resp1.next_page = "p2"

        # Page 2
        resp2 = create_autospec(oci.response.Response)
        resp2.data = [
            oci.identity.models.Compartment(
                id="c3",
                name="C3",
                description="Test compartment",
                lifecycle_state="ACTIVE",
                time_created="1970-01-01T00:00:00",
            ),
        ]
        resp2.has_next_page = False
        resp2.next_page = None

        mock_identity_client.list_compartments.side_effect = [resp1, resp2]
        mock_identity_client.get_compartment.return_value = mock_get_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_compartments",
                    {
                        "compartment_id": "tenancy",
                    },
                )
            ).structured_content["result"]

        assert len(result) == 4
        assert [r["id"] for r in result] == ["c1", "c2", "c3", "tenancy1"]

        # Verify pagination call args across pages
        first_kwargs = mock_identity_client.list_compartments.call_args_list[0].kwargs
        second_kwargs = mock_identity_client.list_compartments.call_args_list[1].kwargs
        assert first_kwargs["page"] is None
        assert first_kwargs["limit"] is None
        assert second_kwargs["page"] == "p2"
        assert second_kwargs["limit"] is None

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    async def test_list_compartments_limit_stops_pagination(
        self, mock_config_from_file, mock_identity_client
    ):
        mock_config_from_file.return_value = {"tenancy": "test_tenancy"}

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.identity.models.Compartment(
            id="tenancy1",
            compartment_id=None,
            name="Root Compartment",
            description="Test compartment (root)",
            lifecycle_state="ACTIVE",
            time_created="1970-01-01T00:00:00",
        )

        # Page 1
        resp1 = create_autospec(oci.response.Response)
        resp1.data = [
            oci.identity.models.Compartment(
                id="c1",
                name="C1",
                description="Test compartment",
                lifecycle_state="ACTIVE",
                time_created="1970-01-01T00:00:00",
            ),
            oci.identity.models.Compartment(
                id="c2",
                name="C2",
                description="Test compartment",
                lifecycle_state="ACTIVE",
                time_created="1970-01-01T00:00:00",
            ),
        ]
        resp1.has_next_page = True
        resp1.next_page = "p2"

        # Page 2 (would exist, but should not be called due to limit)
        resp2 = create_autospec(oci.response.Response)
        resp2.data = [
            oci.identity.models.Compartment(
                id="c3",
                name="C3",
                description="Test compartment",
                lifecycle_state="ACTIVE",
                time_created="1970-01-01T00:00:00",
            ),
        ]
        resp2.has_next_page = False
        resp2.next_page = None

        mock_identity_client.list_compartments.side_effect = [resp1, resp2]
        mock_identity_client.get_compartment.return_value = mock_get_response

        limit = 2
        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_compartments",
                    {
                        "compartment_id": "tenancy",
                        "limit": limit,
                    },
                )
            ).structured_content["result"]

        assert len(result) == 3
        assert [r["id"] for r in result] == ["c1", "c2", "tenancy1"]
        # With limit, only first page should be fetched
        assert mock_identity_client.list_compartments.call_count == 1
        first_kwargs = mock_identity_client.list_compartments.call_args_list[0].kwargs
        assert first_kwargs["limit"] == limit
        assert first_kwargs["page"] is None

    @pytest.mark.asyncio
    async def test_list_availability_domains(self, mock_identity_client):
        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.identity.models.AvailabilityDomain(
                id="ad1",
                name="AD-1",
                compartment_id="compartment1",
            )
        ]
        mock_identity_client.list_availability_domains.return_value = mock_list_response

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
    async def test_list_compartments_exception_propagates(self, mock_identity_client):
        mock_identity_client.list_compartments.side_effect = RuntimeError("boom")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "list_compartments",
                    {
                        "compartment_id": "tenancy",
                    },
                )

    @pytest.mark.asyncio
    async def test_get_tenancy(self, mock_identity_client):
        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.identity.models.Tenancy(
            id="tenancy1",
            name="Tenancy 1",
            description="Test tenancy",
            home_region_key="PHX",
        )
        mock_identity_client.get_tenancy.return_value = mock_get_response

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
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    async def test_get_current_tenancy(
        self, mock_config_from_file, mock_identity_client
    ):
        mock_config_from_file.return_value = {"tenancy": "test_tenancy"}

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.identity.models.Tenancy(
            id="tenancy1",
            name="Tenancy 1",
            description="Test tenancy",
            home_region_key="PHX",
        )
        mock_identity_client.get_tenancy.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_current_tenancy",
                {},
            )
            result = call_tool_result.structured_content

            assert result["id"] == "tenancy1"

    @pytest.mark.asyncio
    async def test_create_auth_token(self, mock_identity_client):
        mock_create_response = create_autospec(oci.response.Response)
        mock_create_response.data = oci.identity.models.AuthToken(
            token="token1", description="Test token", lifecycle_state="ACTIVE"
        )
        mock_identity_client.create_auth_token.return_value = mock_create_response

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
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    async def test_get_current_user_from_config_user(
        self, mock_config_from_file, mock_identity_client
    ):
        mock_config_from_file.return_value = {"user": "test_user"}

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.identity.models.User(
            id="user1", name="User 1", description="Test user"
        )
        mock_identity_client.get_user.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_current_user",
                {},
            )
            result = call_tool_result.structured_content

            assert result["id"] == "user1"

    def _make_jwt(self, payload_dict: dict) -> str:
        header_b64 = (
            base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode())
            .decode()
            .rstrip("=")
        )
        payload_b64 = (
            base64.urlsafe_b64encode(json.dumps(payload_dict).encode())
            .decode()
            .rstrip("=")
        )
        return f"{header_b64}.{payload_b64}.signature"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.os.path.exists")
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    async def test_get_current_user_fallback_from_token_sub(
        self, mock_config_from_file, mock_path_exists, mock_identity_client
    ):
        # No user in config, but provide a token file with JWT 'sub'
        token = self._make_jwt({"sub": "ocid1.user.oc1..sub"})
        mock_config_from_file.return_value = {
            "security_token_file": "/tmp/token.txt",
        }
        mock_path_exists.return_value = True

        m = mock_open(read_data=token)
        mock_resp = create_autospec(oci.response.Response)
        mock_resp.data = oci.identity.models.User(id="user-sub", name="User From Sub")
        mock_identity_client.get_user.return_value = mock_resp

        with patch("builtins.open", m):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool("get_current_user", {})
                ).structured_content
                assert result["id"] == "user-sub"
                # Ensure client.get_user called with derived OCID
                mock_identity_client.get_user.assert_called_once_with(
                    "ocid1.user.oc1..sub"
                )

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.os.path.exists")
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    async def test_get_current_user_fallback_from_token_opc_user_id(
        self, mock_config_from_file, mock_path_exists, mock_identity_client
    ):
        token = self._make_jwt({"opc-user-id": "ocid1.user.oc1..opc"})
        mock_config_from_file.return_value = {
            "security_token_file": "/tmp/token.txt",
        }
        mock_path_exists.return_value = True

        m = mock_open(read_data=token)
        mock_resp = create_autospec(oci.response.Response)
        mock_resp.data = oci.identity.models.User(id="user-opc", name="User From OPC")
        mock_identity_client.get_user.return_value = mock_resp

        with patch("builtins.open", m):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool("get_current_user", {})
                ).structured_content
                assert result["id"] == "user-opc"
                mock_identity_client.get_user.assert_called_once_with(
                    "ocid1.user.oc1..opc"
                )

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.os.path.exists")
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    async def test_get_current_user_raises_when_no_user(
        self, mock_config_from_file, mock_path_exists, mock_identity_client
    ):
        # No user in config, token file missing -> KeyError should propagate as ToolError
        mock_config_from_file.return_value = {"security_token_file": "/tmp/token.txt"}
        mock_path_exists.return_value = False

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("get_current_user", {})

    @pytest.mark.asyncio
    async def test_get_compartment_by_name(self, mock_identity_client):
        """
        Tests finding a compartment by name, including simulating pagination
        where the target is on the second page.
        """
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

        mock_identity_client.list_compartments.side_effect = [
            mock_response_p1,
            mock_response_p2,
        ]

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

            assert mock_identity_client.list_compartments.call_count == 2

    @pytest.mark.asyncio
    async def test_get_compartment_by_name_not_found(self, mock_identity_client):
        resp = create_autospec(oci.response.Response)
        resp.data = []
        resp.has_next_page = False
        resp.next_page = None
        mock_identity_client.list_compartments.return_value = resp

        async with Client(mcp) as client:
            raw_content = (
                await client.call_tool(
                    "get_compartment_by_name",
                    {
                        "name": "Missing",
                        "parent_compartment_id": "ocid1.tenancy",
                    },
                )
            ).structured_content

            # Depending on FastMCP version, result may be nested
            result = raw_content.get("result", raw_content)
            assert result is None

    @pytest.mark.asyncio
    async def test_list_subscribed_regions(self, mock_identity_client):
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
        mock_identity_client.list_region_subscriptions.return_value = mock_list_response

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

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_identity_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_identity_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()


@pytest.mark.asyncio
@patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
async def test_get_current_tenancy_with_env_override(
    mock_from_file, mock_identity_client
):
    mock_from_file.return_value = {"tenancy": "base-tenancy"}

    mock_get_response = create_autospec(oci.response.Response)
    mock_get_response.data = oci.identity.models.Tenancy(
        id="tenancy1",
        name="Tenancy 1",
        description="Test tenancy",
        home_region_key="PHX",
    )
    mock_identity_client.get_tenancy.return_value = mock_get_response

    with patch.dict(
        os.environ, {"TENANCY_ID_OVERRIDE": "ocid1.tenancy.oc1..override"}, clear=False
    ):
        async with Client(mcp) as client:
            result = (
                await client.call_tool("get_current_tenancy", {})
            ).structured_content
            assert result["id"] == "tenancy1"

    mock_identity_client.get_tenancy.assert_called_once_with(
        "ocid1.tenancy.oc1..override"
    )


@pytest.mark.asyncio
async def test_get_tenancy_exception_propagates(mock_identity_client):
    mock_identity_client.get_tenancy.side_effect = RuntimeError("boom")

    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool("get_tenancy", {"tenancy_id": "ocid1.tenancy"})


@pytest.mark.asyncio
async def test_list_availability_domains_exception_propagates(mock_identity_client):
    mock_identity_client.list_availability_domains.side_effect = ValueError("err")

    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "list_availability_domains", {"compartment_id": "ocid1.tenancy"}
            )


@pytest.mark.asyncio
@patch("oracle.oci_identity_mcp_server.server.os.path.exists")
@patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
async def test_get_current_user_invalid_token_decode_raises(
    mock_from_file, mock_exists, mock_identity_client
):
    mock_from_file.return_value = {"security_token_file": "/tmp/token.txt"}
    mock_exists.return_value = True
    invalid_token = "a.b.c"  # invalid base64 payload to trigger decode error

    m = mock_open(read_data=invalid_token)
    with patch("builtins.open", m):
        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("get_current_user", {})
