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
from oracle.oci_usage_mcp_server import server
from oracle.oci_usage_mcp_server.server import mcp


class TestUsageTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_usage_mcp_server.server.get_usage_client")
    async def test_get_summarized_usage(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_request_summarized_response = create_autospec(oci.response.Response)
        mock_request_summarized_response.data = oci.usage_api.models.QueryCollection(
            items=[
                oci.usage_api.models.UsageSummary(
                    compartment_id="test_compartment_id",
                    compartment_name="test_compartment_name",
                    computed_amount=6.731118997232,
                    computed_quantity=69.842410393953,
                    service="Database",
                )
            ]
        )

        mock_client.request_summarized_usages.return_value = mock_request_summarized_response
        print("mock response", mock_request_summarized_response)
        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_summarized_usage",
                    {
                        "tenant_id": "test_tenant_id",
                        "start_time": "2023-01-01T00:00:00Z",
                        "end_time": "2023-01-02T00:00:00Z",
                        "group_by": ["compartment"],
                        "compartment_depth": 1.0,
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["compartment_id"] == "test_compartment_id"
            assert result[0]["service"] == "Database"
            assert result[0]["computed_amount"] == 6.731118997232


class TestServer:
    @patch("oracle.oci_usage_mcp_server.server.oci.auth.signers.TokenExchangeSigner", return_value="signer")
    @patch("oracle.oci_usage_mcp_server.server.get_access_token")
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

    @patch("oracle.oci_usage_mcp_server.server.get_access_token", return_value=None)
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

    @patch("oracle.oci_usage_mcp_server.server.OCIProvider")
    @patch("oracle.oci_usage_mcp_server.server.mcp.run")
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

    @patch("oracle.oci_usage_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_usage_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x, d=None: mock_env.get(x, d)
        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_usage_mcp_server.server.mcp.run")
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


class TestGetClient:
    @patch("oracle.oci_usage_mcp_server.server.oci.usage_api.UsageapiClient")
    @patch("oracle.oci_usage_mcp_server.server._get_http_config_and_signer")
    def test_get_usage_client_http(self, mock_http_config_and_signer, mock_client):
        mock_http_config_and_signer.return_value = ({"region": "us-phoenix-1"}, "signer")

        result = server.get_usage_client()

        mock_client.assert_called_once()
        assert mock_client.call_args.kwargs["signer"] == "signer"
        assert result == mock_client.return_value

    @patch("oracle.oci_usage_mcp_server.server.oci.usage_api.UsageapiClient")
    @patch("oracle.oci_usage_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_usage_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_usage_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_usage_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_usage_mcp_server.server.os.getenv")
    def test_get_search_client_with_profile_env(
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
        result = server.get_usage_client()

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

    @patch("oracle.oci_usage_mcp_server.server.oci.usage_api.UsageapiClient")
    @patch("oracle.oci_usage_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_usage_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_usage_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_usage_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_usage_mcp_server.server.os.getenv")
    def test_get_search_client_uses_default_profile_when_env_missing(
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
        srv_client = server.get_usage_client()

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
