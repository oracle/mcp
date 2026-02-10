"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec, mock_open, patch

import oci
import oracle.oci_migration_mcp_server.server as server
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from oracle.oci_migration_mcp_server.server import mcp


class TestMigrationTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_migration_mcp_server.server.get_migration_client")
    async def test_get_migration(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.cloud_migrations.models.Migration(
            id="migration1", display_name="Migration 1", lifecycle_state="ACTIVE"
        )
        mock_client.get_migration.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool("get_migration", {"migration_id": "migration1"})
            result = call_tool_result.structured_content

            assert result["id"] == "migration1"

    @pytest.mark.asyncio
    @patch("oracle.oci_migration_mcp_server.server.get_migration_client")
    async def test_list_migrations(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = oci.cloud_migrations.models.MigrationCollection(
            items=[
                oci.cloud_migrations.models.Migration(
                    id="migration1",
                    display_name="Migration 1",
                    compartment_id="compartment1",
                    lifecycle_state="RUNNING",
                )
            ]
        )
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_migrations.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_migrations",
                    {
                        "compartment_id": "compartment1",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "migration1"


class TestServer:
    @patch("oracle.oci_migration_mcp_server.server.mcp.run")
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

    @patch("oracle.oci_migration_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_migration_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_migration_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()


@pytest.mark.asyncio
@patch("oracle.oci_migration_mcp_server.server.get_migration_client")
async def test_list_migrations_pagination_without_limit(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    resp1 = create_autospec(oci.response.Response)
    resp1.data = SimpleNamespace(
        items=[
            oci.cloud_migrations.models.Migration(id="m1", display_name="M1"),
            oci.cloud_migrations.models.Migration(id="m2", display_name="M2"),
        ]
    )
    resp1.has_next_page = True
    resp1.next_page = "np1"

    resp2 = create_autospec(oci.response.Response)
    resp2.data = SimpleNamespace(
        items=[
            oci.cloud_migrations.models.Migration(id="m3", display_name="M3"),
        ]
    )
    resp2.has_next_page = False
    resp2.next_page = None

    mock_client.list_migrations.side_effect = [resp1, resp2]

    async with Client(mcp) as client:
        result = (
            await client.call_tool(
                "list_migrations",
                {"compartment_id": "tenancy"},
            )
        ).structured_content["result"]

    assert [r["id"] for r in result] == ["m1", "m2", "m3"]
    first_kwargs = mock_client.list_migrations.call_args_list[0].kwargs
    second_kwargs = mock_client.list_migrations.call_args_list[1].kwargs
    assert first_kwargs["page"] is None
    assert first_kwargs["limit"] is None
    assert second_kwargs["page"] == "np1"
    assert second_kwargs["limit"] is None


@pytest.mark.asyncio
@patch("oracle.oci_migration_mcp_server.server.get_migration_client")
async def test_list_migrations_limit_stops_pagination(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    resp1 = create_autospec(oci.response.Response)
    resp1.data = SimpleNamespace(
        items=[
            oci.cloud_migrations.models.Migration(id="m1"),
            oci.cloud_migrations.models.Migration(id="m2"),
        ]
    )
    resp1.has_next_page = True
    resp1.next_page = "np1"

    resp2 = create_autospec(oci.response.Response)
    resp2.data = SimpleNamespace(items=[oci.cloud_migrations.models.Migration(id="m3")])
    resp2.has_next_page = False
    resp2.next_page = None

    mock_client.list_migrations.side_effect = [resp1, resp2]

    limit = 2
    async with Client(mcp) as client:
        result = (
            await client.call_tool(
                "list_migrations",
                {"compartment_id": "tenancy", "limit": limit},
            )
        ).structured_content["result"]

    assert [r["id"] for r in result] == ["m1", "m2"]
    assert mock_client.list_migrations.call_count == 1
    kwargs = mock_client.list_migrations.call_args.kwargs
    assert kwargs["limit"] == limit
    assert kwargs["page"] is None


@pytest.mark.asyncio
@patch("oracle.oci_migration_mcp_server.server.get_migration_client")
async def test_list_migrations_includes_lifecycle_state_filter(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    resp = create_autospec(oci.response.Response)
    resp.data = SimpleNamespace(items=[oci.cloud_migrations.models.Migration(id="x")])
    resp.has_next_page = False
    resp.next_page = None
    mock_client.list_migrations.return_value = resp

    async with Client(mcp) as client:
        await client.call_tool(
            "list_migrations",
            {"compartment_id": "tenancy", "lifecycle_state": "ACTIVE"},
        )

    kwargs = mock_client.list_migrations.call_args.kwargs
    assert kwargs["lifecycle_state"] == "ACTIVE"


@pytest.mark.asyncio
@patch("oracle.oci_migration_mcp_server.server.get_migration_client")
async def test_get_migration_exception_propagates(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.get_migration.side_effect = RuntimeError("boom")

    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool("get_migration", {"migration_id": "ocid1.mig"})


@pytest.mark.asyncio
@patch("oracle.oci_migration_mcp_server.server.get_migration_client")
async def test_list_migrations_exception_propagates(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.list_migrations.side_effect = ValueError("err")

    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool("list_migrations", {"compartment_id": "ocid1.tenancy"})


class TestGetClient:
    @patch("oracle.oci_migration_mcp_server.server.oci.cloud_migrations.MigrationClient")
    @patch("oracle.oci_migration_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_migration_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_migration_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_migration_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_migration_mcp_server.server.os.getenv")
    def test_get_migration_client_with_profile_env(
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
        result = server.get_migration_client()

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

    @patch("oracle.oci_migration_mcp_server.server.oci.cloud_migrations.MigrationClient")
    @patch("oracle.oci_migration_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_migration_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_migration_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_migration_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_migration_mcp_server.server.os.getenv")
    def test_get_migration_client_uses_default_profile_when_env_missing(
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
        srv_client = server.get_migration_client()

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
