"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, mock_open, patch

import oci
import pytest
from fastmcp import Client
from fastmcp.server.dependencies import AccessToken
from oracle.oci_registry_mcp_server import server
from oracle.oci_registry_mcp_server.server import mcp


class TestRegistryTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_registry_mcp_server.server.get_ocir_client")
    async def test_list_container_repositories(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

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
    @patch("oracle.oci_registry_mcp_server.server.get_ocir_client")
    async def test_get_container_repository(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

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
    @patch("oracle.oci_registry_mcp_server.server.get_ocir_client")
    async def test_create_container_repository(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

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
    @patch("oracle.oci_registry_mcp_server.server.get_ocir_client")
    async def test_delete_container_repository(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

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
    @patch("oracle.oci_registry_mcp_server.server.get_ocir_client")
    async def test_list_container_repositories_raises(self, mock_get_client):
        # Cause the tool to raise and ensure the MCP wrapper returns an error payload
        mock_get_client.side_effect = ValueError("boom")

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_container_repositories",
                {"compartment_id": "ocid1.compartment"},
                raise_on_error=False,
            )
            assert call_tool_result.is_error is True
            # The error text is present in the first content block
            assert any(getattr(block, "text", "").find("boom") != -1 for block in call_tool_result.content)

    @pytest.mark.asyncio
    @patch("oracle.oci_registry_mcp_server.server.get_ocir_client")
    async def test_get_container_repository_raises(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.get_container_repository.side_effect = RuntimeError("oops")
        mock_get_client.return_value = mock_client

        async with Client(mcp) as client:
            res = await client.call_tool(
                "get_container_repository",
                {"repository_id": "ocid1.repo"},
                raise_on_error=False,
            )
            assert res.is_error is True
            assert any(getattr(b, "text", "").find("oops") != -1 for b in res.content)

    @pytest.mark.asyncio
    @patch("oracle.oci_registry_mcp_server.server.get_ocir_client")
    async def test_create_container_repository_raises(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.create_container_repository.side_effect = RuntimeError("fail")
        mock_get_client.return_value = mock_client

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
    @patch("oracle.oci_registry_mcp_server.server.get_ocir_client")
    async def test_delete_container_repository_raises(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.delete_container_repository.side_effect = RuntimeError("nope")
        mock_get_client.return_value = mock_client

        async with Client(mcp) as client:
            res = await client.call_tool(
                "delete_container_repository",
                {"repository_id": "ocid1.repo"},
                raise_on_error=False,
            )
            assert res.is_error is True
            assert any(getattr(b, "text", "").find("nope") != -1 for b in res.content)


class TestServer:
    @patch("oracle.oci_registry_mcp_server.server.oci.auth.signers.TokenExchangeSigner", return_value="signer")
    @patch("oracle.oci_registry_mcp_server.server.get_access_token")
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

    @patch("oracle.oci_registry_mcp_server.server.get_access_token", return_value=None)
    def test_http_signer_requires_authenticated_token(self, _mock_get_access_token, monkeypatch):
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8888")

        with pytest.raises(RuntimeError, match="authenticated IDCS access token"):
            server._get_http_config_and_signer()

    def test_http_signer_requires_region(self, monkeypatch):
        monkeypatch.setattr(server, "get_access_token", lambda: AccessToken(token="token", client_id="client", scopes=[], claims={}))
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8888")
        monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")

        with pytest.raises(RuntimeError, match="OCI_REGION"):
            server._get_http_config_and_signer()

    @patch("oracle.oci_registry_mcp_server.server.OCIProvider")
    @patch("oracle.oci_registry_mcp_server.server.mcp.run")
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
        import oracle.oci_registry_mcp_server.server as server

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
        mock_getenv.side_effect = lambda x, d=None: mock_env.get(x, d)
        import oracle.oci_registry_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_registry_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x, d=None: mock_env.get(x, d)
        import oracle.oci_registry_mcp_server.server as server

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


class TestGetClient:
    @patch("oracle.oci_registry_mcp_server.server.oci.artifacts.ArtifactsClient")
    @patch("oracle.oci_registry_mcp_server.server._get_http_config_and_signer")
    def test_get_ocir_client_http(self, mock_http_config_and_signer, mock_client):
        mock_http_config_and_signer.return_value = ({"region": "us-phoenix-1"}, "signer")

        result = server.get_ocir_client()

        mock_client.assert_called_once()
        assert mock_client.call_args.kwargs["signer"] == "signer"
        assert result == mock_client.return_value

    @patch("oracle.oci_registry_mcp_server.server.oci.artifacts.ArtifactsClient")
    @patch("oracle.oci_registry_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_registry_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_registry_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_registry_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_registry_mcp_server.server.os.getenv")
    def test_get_ocir_client_with_profile_env(
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
        result = server.get_ocir_client()

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

    @patch("oracle.oci_registry_mcp_server.server.oci.artifacts.ArtifactsClient")
    @patch("oracle.oci_registry_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_registry_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_registry_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_registry_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_registry_mcp_server.server.os.getenv")
    def test_get_ocir_client_uses_default_profile_when_env_missing(
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
        srv_client = server.get_ocir_client()

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
