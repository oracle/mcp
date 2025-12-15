"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
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
    @patch(
        "oracle.oci_compute_instance_agent_mcp_server.server.get_compute_instance_agent_client"
    )
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
        mock_client.get_instance_agent_command_execution.return_value = (
            mock_execution_response
        )

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

    @pytest.mark.asyncio
    @patch(
        "oracle.oci_compute_instance_agent_mcp_server.server.get_compute_instance_agent_client"
    )
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
        mock_client.list_instance_agent_command_executions.return_value = (
            mock_list_response
        )

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
            assert (
                result[0]["instance_agent_command_id"]
                == mock_command_1.instance_agent_command_id
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
        import oracle.oci_compute_instance_agent_mcp_server.server as server

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
        import oracle.oci_compute_instance_agent_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_compute_instance_agent_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_compute_instance_agent_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_compute_instance_agent_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_compute_instance_agent_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
