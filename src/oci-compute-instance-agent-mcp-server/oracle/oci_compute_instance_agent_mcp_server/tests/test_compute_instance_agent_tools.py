"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, mock_open, patch

import oci
import oracle.oci_compute_instance_agent_mcp_server.server as server
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from oci.compute_instance_agent.models import (
    InstanceAgentCommand,
    InstanceAgentCommandContent,
    InstanceAgentCommandExecution,
    InstanceAgentCommandExecutionOutputViaTextDetails,
    InstanceAgentCommandExecutionSummary,
    InstanceAgentCommandOutputViaTextDetails,
    InstanceAgentCommandSourceViaTextDetails,
)
from oracle.oci_compute_instance_agent_mcp_server.server import mcp


class TestComputeInstanceAgent:
    @pytest.mark.asyncio
    @patch("oci.wait_until")
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.get_compute_instance_agent_client")
    async def test_run_instance_agent_command(self, mock_get_client, mock_wait_until):
        compartment_id = "test_compartment"
        instance_id = "test_instance"
        display_name = "test_command"
        script = "echo Hello"
        execution_time_out_in_seconds = 30

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_create_response = create_autospec(oci.response.Response)
        mock_create_response.data = InstanceAgentCommand(
            id="command1",
            compartment_id=compartment_id,
            display_name=display_name,
            execution_time_out_in_seconds=execution_time_out_in_seconds,
            content=InstanceAgentCommandContent(
                source=InstanceAgentCommandSourceViaTextDetails(
                    source_type=InstanceAgentCommandSourceViaTextDetails.SOURCE_TYPE_TEXT,
                    text=script,
                ),
                output=InstanceAgentCommandOutputViaTextDetails(
                    output_type=InstanceAgentCommandOutputViaTextDetails.OUTPUT_TYPE_TEXT,
                ),
            ),
        )
        mock_client.create_instance_agent_command.return_value = mock_create_response

        mock_execution_response = create_autospec(oci.response.Response)
        mock_execution_response.data = InstanceAgentCommandExecution(
            instance_agent_command_id="command1",
            instance_id=instance_id,
            display_name=display_name,
            lifecycle_state=InstanceAgentCommandExecution.LIFECYCLE_STATE_SUCCEEDED,
            delivery_state=InstanceAgentCommandExecution.DELIVERY_STATE_VISIBLE,
            content=InstanceAgentCommandExecutionOutputViaTextDetails(
                output_type="TEXT",
                exit_code=0,
                text="Hello",
                message="Execution successful",
                text_sha256="sha256-of-hello",
            ),
            time_created="2023-01-01T00:00:00Z",
            time_updated="2023-01-01T00:00:00Z",
            sequence_number=1,
        )
        mock_client.get_instance_agent_command_execution.return_value = mock_execution_response

        mock_wait_until.return_value = mock_execution_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "run_instance_agent_command",
                    {
                        "compartment_id": compartment_id,
                        "instance_id": instance_id,
                        "display_name": display_name,
                        "script": script,
                        "execution_time_out_in_seconds": execution_time_out_in_seconds,
                    },
                )
            ).structured_content

            assert result["instance_agent_command_id"] == "command1"
            assert result["instance_id"] == "test_instance"
            assert result["content"]["text"] == "Hello"

        # Verify we waited for SUCCEEDED lifecycle state
        mock_wait_until.assert_called()
        args, kwargs = mock_wait_until.call_args
        assert kwargs["property"] == "lifecycle_state"
        assert kwargs["state"] == InstanceAgentCommandExecution.LIFECYCLE_STATE_SUCCEEDED

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.get_compute_instance_agent_client")
    async def test_list_instance_agent_commands(self, mock_get_client):
        compartment_id = "test_compartment"
        instance_id = "test_instance"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_list_response = create_autospec(oci.response.Response)
        mock_command_1 = InstanceAgentCommandExecutionSummary(
            instance_agent_command_id="command1",
            instance_id=instance_id,
            delivery_state=InstanceAgentCommandExecutionSummary.DELIVERY_STATE_VISIBLE,
            lifecycle_state=InstanceAgentCommandExecutionSummary.LIFECYCLE_STATE_SUCCEEDED,
            time_created="2023-01-01T00:00:00Z",
            time_updated="2023-01-01T00:00:00Z",
            sequence_number=1,
        )

        mock_list_response.data = [
            mock_command_1,
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_instance_agent_command_executions.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_instance_agent_command_executions",
                    {
                        "compartment_id": compartment_id,
                        "instance_id": instance_id,
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["instance_agent_command_id"] == mock_command_1.instance_agent_command_id

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.get_compute_instance_agent_client")
    async def test_list_instance_agent_commands_pagination_and_limit_and_output_types(self, mock_get_client):
        # This test exercises:
        # - pagination (has_next_page + next_page)
        # - limit enforcement
        # - mapping of different output content types (TEXT, OBJECT_STORAGE_URI, OBJECT_STORAGE_TUPLE)
        compartment_id = "ocid1.compartment"
        instance_id = "ocid1.instance"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # First page with TEXT output content summary
        resp_page_1 = create_autospec(oci.response.Response)
        summary_text = MagicMock()
        setattr(summary_text, "instance_agent_command_id", "cmd-text-1")
        setattr(summary_text, "instance_id", instance_id)
        setattr(
            summary_text,
            "delivery_state",
            InstanceAgentCommandExecutionSummary.DELIVERY_STATE_VISIBLE,
        )
        setattr(
            summary_text,
            "lifecycle_state",
            InstanceAgentCommandExecutionSummary.LIFECYCLE_STATE_SUCCEEDED,
        )
        setattr(summary_text, "time_created", "2024-01-01T00:00:00Z")
        setattr(summary_text, "time_updated", "2024-01-01T00:00:05Z")
        setattr(summary_text, "sequence_number", 10)
        setattr(summary_text, "display_name", "text-name")
        # Attach TEXT content
        content_text = MagicMock()
        content_text.output_type = "TEXT"
        content_text.exit_code = 0
        content_text.message = "ok"
        content_text.text = "hello"
        content_text.text_sha256 = "abc"
        setattr(summary_text, "content", content_text)
        resp_page_1.data = [summary_text]
        resp_page_1.has_next_page = True
        resp_page_1.next_page = "token-1"

        # Second page with OBJECT_STORAGE_URI and OBJECT_STORAGE_TUPLE
        resp_page_2 = create_autospec(oci.response.Response)
        summary_uri = MagicMock()
        setattr(summary_uri, "instance_agent_command_id", "cmd-uri-2")
        setattr(summary_uri, "instance_id", instance_id)
        setattr(summary_uri, "delivery_state", "PENDING")
        setattr(summary_uri, "lifecycle_state", "IN_PROGRESS")
        setattr(summary_uri, "time_created", "2024-01-01T00:00:10Z")
        setattr(summary_uri, "time_updated", "2024-01-01T00:00:20Z")
        setattr(summary_uri, "sequence_number", 11)
        setattr(summary_uri, "display_name", "uri-name")
        content_uri = MagicMock()
        content_uri.output_type = "OBJECT_STORAGE_URI"
        content_uri.exit_code = 1
        content_uri.message = "see uri"
        content_uri.output_uri = "https://objectstorage.example.com/n/bkt/o/out"
        setattr(summary_uri, "content", content_uri)

        summary_tuple = MagicMock()
        setattr(summary_tuple, "instance_agent_command_id", "cmd-tuple-3")
        setattr(summary_tuple, "instance_id", instance_id)
        setattr(summary_tuple, "delivery_state", "ACKED")
        setattr(summary_tuple, "lifecycle_state", "FAILED")
        setattr(summary_tuple, "time_created", "2024-01-01T00:00:30Z")
        setattr(summary_tuple, "time_updated", "2024-01-01T00:00:40Z")
        setattr(summary_tuple, "sequence_number", 12)
        setattr(summary_tuple, "display_name", "tuple-name")
        content_tuple = MagicMock()
        content_tuple.output_type = "OBJECT_STORAGE_TUPLE"
        content_tuple.exit_code = 2
        content_tuple.message = "tuple"
        content_tuple.bucket_name = "b"
        content_tuple.namespace_name = "n"
        content_tuple.object_name = "o"
        setattr(summary_tuple, "content", content_tuple)

        resp_page_2.data = [summary_uri, summary_tuple]
        resp_page_2.has_next_page = False
        resp_page_2.next_page = None

        mock_client.list_instance_agent_command_executions.side_effect = [
            resp_page_1,
            resp_page_2,
        ]

        # Set limit=2 to stop after two items though there are three across pages
        limit = 2
        async with Client(mcp) as client:
            payload = {
                "compartment_id": compartment_id,
                "instance_id": instance_id,
                "limit": limit,
            }
            result = (
                await client.call_tool("list_instance_agent_command_executions", payload)
            ).structured_content["result"]

        # Verify pagination and mapping of content subtypes
        assert len(result) == 3
        # First is TEXT
        assert result[0]["instance_agent_command_id"] == "cmd-text-1"
        assert result[0]["content"]["output_type"] == "TEXT"
        assert result[0]["content"]["text"] == "hello"
        # Second is OBJECT_STORAGE_URI
        assert result[1]["instance_agent_command_id"] == "cmd-uri-2"
        assert result[1]["content"]["output_type"] == "OBJECT_STORAGE_URI"
        assert result[1]["content"]["output_uri"] == "https://objectstorage.example.com/n/bkt/o/out"

        # Ensure pagination called with correct page tokens
        first_kwargs = mock_client.list_instance_agent_command_executions.call_args_list[0].kwargs
        second_kwargs = mock_client.list_instance_agent_command_executions.call_args_list[1].kwargs
        assert first_kwargs["page"] is None
        assert first_kwargs["limit"] == limit
        assert second_kwargs["page"] == "token-1"
        assert second_kwargs["limit"] == limit

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.get_compute_instance_agent_client")
    async def test_run_instance_agent_command_exception_propagates(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.create_instance_agent_command.side_effect = RuntimeError("boom")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "run_instance_agent_command",
                    {
                        "compartment_id": "c",
                        "instance_id": "i",
                        "display_name": "d",
                        "script": "echo",
                        "execution_time_out_in_seconds": 5,
                    },
                )


class TestServer:
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.mcp.run")
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

    @patch("oracle.oci_compute_instance_agent_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_compute_instance_agent_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_compute_instance_agent_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()


@patch("oracle.oci_compute_instance_agent_mcp_server.server.get_compute_instance_agent_client")
@pytest.mark.asyncio
async def test_list_instance_agent_command_executions_exception_propagates(
    mock_get_client,
):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.list_instance_agent_command_executions.side_effect = ValueError("err")

    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "list_instance_agent_command_executions",
                {
                    "compartment_id": "c",
                    "instance_id": "i",
                    "limit": 1,
                },
            )


class TestGetClient:
    @patch(
        "oracle.oci_compute_instance_agent_mcp_server.server.oci.compute_instance_agent.ComputeInstanceAgentClient"  # noqa
    )
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_compute_instance_agent_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.os.getenv")
    def test_get_compute_instance_agent_client_with_profile_env(
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
        result = server.get_compute_instance_agent_client()

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

    @patch(
        "oracle.oci_compute_instance_agent_mcp_server.server.oci.compute_instance_agent.ComputeInstanceAgentClient"  # noqa
    )
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_compute_instance_agent_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_compute_instance_agent_mcp_server.server.os.getenv")
    def test_get_compute_instance_agent_client_uses_default_profile_when_env_missing(
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
        srv_client = server.get_compute_instance_agent_client()

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
