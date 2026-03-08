"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import sys
import types
from unittest.mock import MagicMock, create_autospec, mock_open, patch

import oracle.oci_faaas_mcp_server.server as server
import pytest
from fastmcp import Client
from oracle.oci_faaas_mcp_server.server import main, mcp

# Provide a lightweight stub for 'oci' if not installed, so tests can import the server module
try:
    import oci  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    oci = types.SimpleNamespace()
    sys.modules["oci"] = oci
    oci.response = types.SimpleNamespace(Response=type("Response", (), {}))
    oci.util = types.SimpleNamespace(to_dict=lambda x: x)
    oci.config = types.SimpleNamespace(
        DEFAULT_PROFILE="DEFAULT",
        from_file=lambda profile_name=None: {"key_file": "", "security_token_file": ""},
    )
    oci.signer = types.SimpleNamespace(load_private_key_from_file=lambda path: "KEY")
    oci.auth = types.SimpleNamespace(
        signers=types.SimpleNamespace(SecurityTokenSigner=lambda token, key: object())
    )
    oci.fusion_apps = types.SimpleNamespace(FusionApplicationsClient=lambda config, signer=None: object())


class TestFaaasTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_fusion_environment_families(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            {
                "id": "family1",
                "display_name": "Family 1",
                "lifecycle_state": "ACTIVE",
            }
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_fusion_environment_families.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_fusion_environment_families",
                {"compartment_id": "test_compartment"},
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "family1"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_fusion_environments(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            {
                "id": "env1",
                "display_name": "Env 1",
                "lifecycle_state": "ACTIVE",
                "family_id": "family1",
            }
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_fusion_environments.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_fusion_environments",
                {
                    "compartment_id": "test_compartment",
                    "fusion_environment_family_id": "family1",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "env1"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_get_fusion_environment(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = {
            "id": "env1",
            "display_name": "Env 1",
            "lifecycle_state": "ACTIVE",
        }
        mock_client.get_fusion_environment.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_fusion_environment",
                {"fusion_environment_id": "env1"},
            )
            result = call_tool_result.structured_content

            assert result["id"] == "env1"
            assert result["display_name"] == "Env 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_get_fusion_environment_status(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = {
            "fusion_environment_id": "env1",
            "status": "ACTIVE",
            "time_updated": "2025-01-01T00:00:00Z",
        }
        mock_client.get_fusion_environment_status.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_fusion_environment_status",
                {"fusion_environment_id": "env1"},
            )
            result = call_tool_result.structured_content

            assert result["fusion_environment_id"] == "env1"
            assert result["status"] == "ACTIVE"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_fusion_environment_families_pagination_header_fallback(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp1 = create_autospec(oci.response.Response)
        resp1.data = [{"id": "family1", "display_name": "F1"}]
        resp1.next_page = None
        resp1.headers = {"opc-next-page": "token1"}

        resp2 = create_autospec(oci.response.Response)
        resp2.data = [{"id": "family2", "display_name": "F2"}]
        resp2.next_page = None
        resp2.headers = {}

        mock_client.list_fusion_environment_families.side_effect = [resp1, resp2]

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_fusion_environment_families",
                {
                    "compartment_id": "comp",
                    "display_name": "F",
                    "lifecycle_state": "ACTIVE",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert [item["id"] for item in result] == ["family1", "family2"]
            assert mock_client.list_fusion_environment_families.call_count == 2

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_fusion_environments_pagination_and_filters(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        r1 = create_autospec(oci.response.Response)
        r1.data = [{"id": "env1", "display_name": "E1"}]
        r1.next_page = "np1"
        r1.headers = {}

        r2 = create_autospec(oci.response.Response)
        r2.data = [{"id": "env2", "display_name": "E2"}]
        r2.next_page = None
        r2.headers = {}

        mock_client.list_fusion_environments.side_effect = [r1, r2]

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_fusion_environments",
                {
                    "compartment_id": "comp",
                    "fusion_environment_family_id": "fam",
                    "display_name": "E",
                    "lifecycle_state": "ACTIVE",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert [item["id"] for item in result] == ["env1", "env2"]
            assert mock_client.list_fusion_environments.call_count == 2

            # First call includes filters (no 'page'), second call includes page
            first_kwargs = mock_client.list_fusion_environments.call_args_list[0].kwargs
            second_kwargs = mock_client.list_fusion_environments.call_args_list[1].kwargs
            assert first_kwargs["compartment_id"] == "comp"
            assert first_kwargs["fusion_environment_family_id"] == "fam"
            assert first_kwargs["display_name"] == "E"
            assert first_kwargs["lifecycle_state"] == "ACTIVE"
            assert "page" not in first_kwargs

            assert second_kwargs.get("page") == "np1"

    @pytest.mark.asyncio
    async def test_main_runs_mcp_run(self):
        with patch("oracle.oci_faaas_mcp_server.server.mcp.run") as mock_run:
            main()
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_fusion_environment_families_handles_items_attr_and_filters(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Response has a 'data' object with an 'items' attribute
        resp = create_autospec(oci.response.Response)
        resp.data = types.SimpleNamespace(items=[{"id": "famX", "display_name": "Family X"}])
        resp.next_page = None
        resp.headers = {}

        mock_client.list_fusion_environment_families.return_value = resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_fusion_environment_families",
                {
                    "compartment_id": "comp",
                    "display_name": "Family",
                    "lifecycle_state": "ACTIVE",
                },
            )
            result = call_tool_result.structured_content["result"]
            assert [item["id"] for item in result] == ["famX"]
            mock_client.list_fusion_environment_families.assert_called_once()
            # Filters were passed through
            kwargs = mock_client.list_fusion_environment_families.call_args.kwargs
            assert kwargs["compartment_id"] == "comp"
            assert kwargs["display_name"] == "Family"
            assert kwargs["lifecycle_state"] == "ACTIVE"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_fusion_environment_families_headers_exception_fallback(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Headers object causes dict(headers) to raise; code should handle and stop pagination
        resp = create_autospec(oci.response.Response)
        resp.data = [{"id": "fam1"}]
        resp.next_page = None
        resp.headers = object()  # dict(object()) raises TypeError

        mock_client.list_fusion_environment_families.return_value = resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_fusion_environment_families",
                {"compartment_id": "comp"},
            )
            result = call_tool_result.structured_content["result"]
            assert [item["id"] for item in result] == ["fam1"]
            mock_client.list_fusion_environment_families.assert_called_once()

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_fusion_environments_data_single_object(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Response data is a single dict, not list, and no 'items' attr
        r = create_autospec(oci.response.Response)
        r.data = types.SimpleNamespace(id="envX", display_name="Env X")
        r.next_page = None
        r.headers = {}

        mock_client.list_fusion_environments.return_value = r

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_fusion_environments",
                {"compartment_id": "comp"},
            )
            result = call_tool_result.structured_content["result"]
            assert [item["id"] for item in result] == ["envX"]
            # Only required arg was passed
            kwargs = mock_client.list_fusion_environments.call_args.kwargs
            assert list(kwargs.keys()) == ["compartment_id"]


class TestGetClient:
    @patch("oracle.oci_faaas_mcp_server.server.oci.fusion_apps.FusionApplicationsClient")
    @patch("oracle.oci_faaas_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_faaas_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_faaas_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_faaas_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_faaas_mcp_server.server.os.getenv")
    def test_get_faaas_client_with_profile_env(
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
        result = server.get_faaas_client()

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

    @patch("oracle.oci_faaas_mcp_server.server.oci.fusion_apps.FusionApplicationsClient")
    @patch("oracle.oci_faaas_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_faaas_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_faaas_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_faaas_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_faaas_mcp_server.server.os.getenv")
    def test_get_faaas_client_uses_default_profile_when_env_missing(
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
        srv_client = server.get_faaas_client()

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
