"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# noinspection PyPackageRequirements
from unittest.mock import MagicMock, create_autospec, mock_open, patch

import oci
import oracle.oci_cloud_guard_mcp_server.server as server
import pytest
from fastmcp import Client


class TestResourceSearchTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_cloud_guard_mcp_server.server.get_cloud_guard_client")
    async def test_list_all_problems(self, mock_get_client):
        resource_id = "ocid.resource1"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_problems_response = create_autospec(oci.response.Response)
        mock_problems_response.data = oci.cloud_guard.models.ProblemCollection(
            items=[
                oci.cloud_guard.models.ProblemSummary(
                    id=resource_id,
                    resource_type="instance",
                    resource_id="resource1",
                    lifecycle_state="ACTIVE",
                    lifecycle_detail="OPEN",
                )
            ]
        )
        mock_client.list_problems.return_value = mock_problems_response

        async with Client(server.mcp) as client:
            result = (
                await client.call_tool("list_problems", {"compartment_id": "test_compartment"})
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == resource_id

    @pytest.mark.asyncio
    @patch("oracle.oci_cloud_guard_mcp_server.server.get_cloud_guard_client")
    async def test_get_problem_details(self, mock_get_client):
        problem_id = "ocid.resource1"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_problem_response = create_autospec(oci.response.Response)
        mock_get_problem_response.data = oci.cloud_guard.models.Problem(
            id=problem_id,
            resource_type="instance",
            resource_id="resource1",
            lifecycle_state="ACTIVE",
            lifecycle_detail="OPEN",
            compartment_id="test_compartment",
            region="test_region",
            impacted_resource_type="123",
            impacted_resource_name="123",
            risk_level="HIGH",
        )
        mock_client.get_problem.return_value = mock_get_problem_response

        async with Client(server.mcp) as client:
            result = (
                await client.call_tool(
                    "get_problem_details",
                    {
                        "problem_id": problem_id,
                    },
                )
            ).structured_content

            assert result["id"] == problem_id

    @pytest.mark.asyncio
    @patch("oracle.oci_cloud_guard_mcp_server.server.get_cloud_guard_client")
    async def test_update_problem_status(self, mock_get_client):
        problem_id = "ocid.resource1"
        status = "OPEN"
        comment = "this is updated with ai"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_update_problem_status_response = create_autospec(oci.response.Response)
        mock_update_problem_status_response.data = oci.cloud_guard.models.Problem(
            id=problem_id,
            resource_type="instance",
            resource_id="resource1",
            lifecycle_state="ACTIVE",
            lifecycle_detail=status,
            comment=comment,
        )
        mock_client.update_problem_status.return_value = mock_update_problem_status_response

        async with Client(server.mcp) as client:
            result = (
                await client.call_tool(
                    "update_problem_status",
                    {"problem_id": problem_id, "status": status, "comment": comment},
                )
            ).structured_content

            print(result)
            assert result["id"] == problem_id
            assert result["lifecycle_detail"] == status
            assert result["comment"] == comment


class TestServer:
    @patch("oracle.oci_cloud_guard_mcp_server.server.mcp.run")
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

    @patch("oracle.oci_cloud_guard_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_cloud_guard_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_cloud_guard_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()


class TestGetClient:
    @patch("oracle.oci_cloud_guard_mcp_server.server.CloudGuardClient")
    @patch("oracle.oci_cloud_guard_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_cloud_guard_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_cloud_guard_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_cloud_guard_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_cloud_guard_mcp_server.server.os.getenv")
    def test_get_cloud_guard_client_with_profile_env(
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
        result = server.get_cloud_guard_client()

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

    @patch("oracle.oci_cloud_guard_mcp_server.server.CloudGuardClient")
    @patch("oracle.oci_cloud_guard_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_cloud_guard_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_cloud_guard_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_cloud_guard_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_cloud_guard_mcp_server.server.os.getenv")
    def test_get_cloud_guard_client_uses_default_profile_when_env_missing(
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
        srv_client = server.get_cloud_guard_client()

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
