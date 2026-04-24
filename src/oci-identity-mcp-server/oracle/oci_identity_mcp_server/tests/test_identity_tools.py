"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from unittest.mock import MagicMock, create_autospec, mock_open, patch

import oci
import oracle.oci_identity_mcp_server.server as server
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from fastmcp.server.auth import AccessToken
from oracle.oci_identity_mcp_server.server import mcp


class TestIdentityTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    @patch("oracle.oci_identity_mcp_server.server._get_profile_value", return_value="test_tenancy")
    async def test_list_compartments(self, _mock_get_profile_value, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

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
        mock_client.list_compartments.return_value = mock_list_response
        mock_client.get_compartment.return_value = mock_get_response

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
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    async def test_list_compartments_without_root(self, mock_get_client):
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
                        "compartment_id_in_subtree": True,
                        "include_root": False,
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "compartment1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    @patch("oracle.oci_identity_mcp_server.server._get_profile_value", return_value="test_tenancy")
    async def test_list_compartments_pagination_without_limit(self, _mock_get_profile_value, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

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

        mock_client.list_compartments.side_effect = [resp1, resp2]
        mock_client.get_compartment.return_value = mock_get_response

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
        first_kwargs = mock_client.list_compartments.call_args_list[0].kwargs
        second_kwargs = mock_client.list_compartments.call_args_list[1].kwargs
        assert first_kwargs["page"] is None
        assert first_kwargs["limit"] is None
        assert second_kwargs["page"] == "p2"
        assert second_kwargs["limit"] is None

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    @patch("oracle.oci_identity_mcp_server.server._get_profile_value", return_value="test_tenancy")
    async def test_list_compartments_limit_stops_pagination(self, _mock_get_profile_value, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

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

        mock_client.list_compartments.side_effect = [resp1, resp2]
        mock_client.get_compartment.return_value = mock_get_response

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
        assert mock_client.list_compartments.call_count == 1
        first_kwargs = mock_client.list_compartments.call_args_list[0].kwargs
        assert first_kwargs["limit"] == limit
        assert first_kwargs["page"] is None

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
    async def test_list_compartments_exception_propagates(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_compartments.side_effect = RuntimeError("boom")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "list_compartments",
                    {
                        "compartment_id": "tenancy",
                    },
                )

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
    @patch("oracle.oci_identity_mcp_server.server._get_profile_value", return_value="test_tenancy")
    async def test_get_current_tenancy(self, _mock_get_profile_value, mock_get_client):
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
    @patch("oracle.oci_identity_mcp_server.server._get_profile_value", return_value="test_user")
    async def test_get_current_user_from_config_user(self, _mock_get_profile_value, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.identity.models.User(id="user1", name="User 1", description="Test user")
        mock_client.get_user.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_current_user",
                {},
            )
            result = call_tool_result.structured_content

            assert result["id"] == "user1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_access_token")
    async def test_get_current_user_from_http_sub(self, mock_get_access_token):
        mock_get_access_token.return_value = AccessToken(
            token="token", client_id="client", scopes=[], claims={"sub": "ocid1.user.oc1..sub"}
        )

        async with Client(mcp) as client:
            result = (await client.call_tool("get_current_user", {})).structured_content
            assert result["id"] == "ocid1.user.oc1..sub"
            assert result["name"] == "ocid1.user.oc1..sub"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_access_token")
    async def test_get_current_user_from_http_opc_user_id(self, mock_get_access_token):
        mock_get_access_token.return_value = AccessToken(
            token="token", client_id="client", scopes=[], claims={"opc-user-id": "ocid1.user.oc1..opc"}
        )

        async with Client(mcp) as client:
            result = (await client.call_tool("get_current_user", {})).structured_content
            assert result["id"] == "ocid1.user.oc1..opc"
            assert result["name"] == "ocid1.user.oc1..opc"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    @patch("oracle.oci_identity_mcp_server.server._get_profile_value", return_value=None)
    async def test_get_current_user_raises_when_no_user(self, _mock_get_profile_value, mock_get_client):

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("get_current_user", {})

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
        mock_response_p1.data = [oci.identity.models.Compartment(name="WrongName", id="wrong_id")]
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
    async def test_get_compartment_by_name_not_found(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp = create_autospec(oci.response.Response)
        resp.data = []
        resp.has_next_page = False
        resp.next_page = None
        mock_client.list_compartments.return_value = resp

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
    @patch("oracle.oci_identity_mcp_server.server.oci.auth.signers.TokenExchangeSigner", return_value="signer")
    @patch("oracle.oci_identity_mcp_server.server.get_access_token")
    def test_http_signer_uses_region_without_loading_config(self, mock_get_access_token, mock_signer, monkeypatch):
        mock_get_access_token.return_value = AccessToken(token="token", client_id="client", scopes=[], claims={})
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8888")
        monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")
        monkeypatch.setenv("OCI_REGION", "us-phoenix-1")

        config, signer = server._get_http_config_and_signer()

        assert config["region"] == "us-phoenix-1"
        assert signer == "signer"
        mock_signer.assert_called_once()

    @patch("oracle.oci_identity_mcp_server.server.get_access_token", return_value=None)
    def test_http_signer_requires_authenticated_token(self, _mock_get_access_token, monkeypatch):
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8888")

        with pytest.raises(RuntimeError, match="authenticated IDCS access token"):
            server._get_http_config_and_signer()

    def test_http_signer_requires_region(self, monkeypatch):
        monkeypatch.setattr(
            server,
            "get_access_token",
            lambda: AccessToken(token="token", client_id="client", scopes=[], claims={}),
        )
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8888")
        monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")

        with pytest.raises(RuntimeError, match="OCI_REGION"):
            server._get_http_config_and_signer()

    def test_get_profile_value_reads_profile_and_defaults(self, monkeypatch, tmp_path):
        config_path = tmp_path / "config"
        config_path.write_text("[DEFAULT]\ntenancy=ocid1.tenancy.oc1..default\n[ALT]\ntenancy=ocid1.tenancy.oc1..alt\n")
        monkeypatch.setenv("OCI_CONFIG_FILE", str(config_path))
        monkeypatch.setenv("OCI_CONFIG_PROFILE", "ALT")
        assert server._get_profile_value("tenancy") == "ocid1.tenancy.oc1..alt"
        monkeypatch.setenv("OCI_CONFIG_PROFILE", "MISSING")
        assert server._get_profile_value("tenancy") == "ocid1.tenancy.oc1..default"

    @patch("oracle.oci_identity_mcp_server.server.OCIProvider")
    @patch("oracle.oci_identity_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run, mock_provider):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
            "IDCS_DOMAIN": "idcs.example.com",
            "IDCS_CLIENT_ID": "client-id",
            "IDCS_CLIENT_SECRET": "client-secret",
            "IDCS_AUDIENCE": "mcp-audience",
            "ORACLE_MCP_BASE_URL": "https://mcp.example.com",
        }

        mock_getenv.side_effect = lambda x, d=None: mock_env.get(x, d)
        mock_provider.return_value = MagicMock()

        server.main()
        mock_provider.assert_called_once_with(
            config_url="https://idcs.example.com/.well-known/openid-configuration",
            client_id="client-id",
            client_secret="client-secret",
            audience="mcp-audience",
            required_scopes=f"openid profile email oci_mcp.{server.__project__.removeprefix('oracle.oci-').removesuffix('-mcp-server').replace('-', '_')}.invoke".split(),
            base_url="https://mcp.example.com",
        )
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
        mock_getenv.side_effect = lambda x, d=None: mock_env.get(x, d)

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_identity_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x, d=None: mock_env.get(x, d)

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("os.getenv")
    def test_main_with_http_missing_idcs_env(self, mock_getenv):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x, d=None: mock_env.get(x, d)

        with pytest.raises(RuntimeError, match="HTTP transport requires IDCS authentication"):
            server.main()


@pytest.mark.asyncio
@patch("oracle.oci_identity_mcp_server.server.get_identity_client")
async def test_get_current_tenancy_with_env_override(mock_get_client):
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

    with patch.dict(os.environ, {"TENANCY_ID_OVERRIDE": "ocid1.tenancy.oc1..override"}, clear=False):
        async with Client(mcp) as client:
            result = (await client.call_tool("get_current_tenancy", {})).structured_content
            assert result["id"] == "tenancy1"

    mock_client.get_tenancy.assert_called_once_with("ocid1.tenancy.oc1..override")


@pytest.mark.asyncio
@patch("oracle.oci_identity_mcp_server.server._get_profile_value", return_value=None)
async def test_list_compartments_include_root_requires_tenancy(_mock_get_profile_value):
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool("list_compartments", {"compartment_id": "ocid1.tenancy", "include_root": True})


@pytest.mark.asyncio
@patch("oracle.oci_identity_mcp_server.server._get_profile_value", return_value=None)
async def test_get_current_tenancy_raises_without_tenancy(_mock_get_profile_value):
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool("get_current_tenancy", {})


@pytest.mark.asyncio
@patch("oracle.oci_identity_mcp_server.server.get_identity_client")
async def test_get_tenancy_exception_propagates(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.get_tenancy.side_effect = RuntimeError("boom")

    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool("get_tenancy", {"tenancy_id": "ocid1.tenancy"})


@pytest.mark.asyncio
@patch("oracle.oci_identity_mcp_server.server.get_identity_client")
async def test_list_availability_domains_exception_propagates(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.list_availability_domains.side_effect = ValueError("err")

    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool("list_availability_domains", {"compartment_id": "ocid1.tenancy"})


@pytest.mark.asyncio
@patch("oracle.oci_identity_mcp_server.server.get_access_token")
async def test_get_current_user_raises_when_http_claims_missing(mock_get_access_token):
    mock_get_access_token.return_value = AccessToken(token="token", client_id="client", scopes=[], claims={})

    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool("get_current_user", {})


class TestGetClient:
    @patch("oracle.oci_identity_mcp_server.server.oci.identity.IdentityClient")
    @patch("oracle.oci_identity_mcp_server.server._get_http_config_and_signer")
    def test_get_identity_client_http(self, mock_http_config_and_signer, mock_client):
        mock_http_config_and_signer.return_value = ({"region": "us-phoenix-1"}, "signer")

        result = server.get_identity_client()

        mock_client.assert_called_once()
        assert mock_client.call_args.kwargs["signer"] == "signer"
        assert result == mock_client.return_value

    @patch("oracle.oci_identity_mcp_server.server.oci.identity.IdentityClient")
    @patch("oracle.oci_identity_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_identity_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_identity_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_identity_mcp_server.server.os.getenv")
    def test_get_identity_client_with_profile_env(
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
        result = server.get_identity_client()

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

    @patch("oracle.oci_identity_mcp_server.server.oci.identity.IdentityClient")
    @patch("oracle.oci_identity_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_identity_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_identity_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_identity_mcp_server.server.os.getenv")
    def test_get_identity_client_uses_default_profile_when_env_missing(
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
        srv_client = server.get_identity_client()

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
