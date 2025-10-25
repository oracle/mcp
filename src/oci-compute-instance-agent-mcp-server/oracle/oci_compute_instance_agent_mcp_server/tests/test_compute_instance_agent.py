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
    InstanceAgentCommandSummary,
)
from oracle.oci_compute_instance_agent_mcp_server.server import mcp


class TestComputeInstanceAgent:
    # @pytest.mark.asyncio
    # @patch(
    #    "oracle.oci_compute_instance_agent_mcp_server.server.get_compute_instance_agent_client"
    # )
    # @patch("oracle.oci_compute_instance_agent_mcp_server.server.oci.wait_until")
    # async def test_run_command(self, mock_get_client, mock_wait_until):
    #    compartment_id = "test_compartment"
    #    instance_id = "test_instance"
    #    display_name ="test_command"
    #    script ="echo Hello"
    #    execution_time_out_in_seconds = 30

    #    mock_client = MagicMock()
    #    mock_get_client.return_value = mock_client

    #    mock_create_response = create_autospec(oci.response.Response)
    #    mock_create_response.data = InstanceAgentCommand(
    #        compartment_id=compartment_id,
    #        display_name=display_name,
    #        execution_time_out_in_seconds=execution_time_out_in_seconds,
    #        content=InstanceAgentCommandContent(
    #            source=InstanceAgentCommandSourceViaTextDetails(
    #                source_type=InstanceAgentCommandSourceViaTextDetails.SOURCE_TYPE_TEXT,
    #                text=script,
    #            ),
    #            output=InstanceAgentCommandOutputViaTextDetails(
    #                output_type=InstanceAgentCommandOutputViaTextDetails.OUTPUT_TYPE_TEXT,
    #            ),
    #        ),
    #    )
    #    mock_client.create_instance_agent_command.return_value = mock_create_response

    #    mock_execution_response = create_autospec(oci.response.Response)
    #    mock_execution_response.data = InstanceAgentCommandExecution(
    #        lifecycle_state="SUCCEEDED",
    #        content=InstanceAgentCommandExecutionOutputContent(
    #            output_type="TEXT",
    #            message="Hello",
    #            exit_code=0,
    #        )
    #    )
    #    mock_client.get_instance_agent_command_execution.return_value = (
    #        mock_execution_response
    #    )

    #    async with Client(mcp) as client:
    #        result = (
    #            await client.call_tool(
    #                "run_command",
    #                {
    #                    "compartment_id": "test_compartment",
    #                    "instance_id": "test_instance",
    #                    "display_name": "test_command",
    #                    "script": "echo Hello",
    #                    "execution_time_out_in_seconds": 30,
    #                },
    #            )
    #        ).structured_content

    #        assert result["command_id"] == "command_id"
    #        assert result["instance_id"] == "test_instance"
    #        assert result["text"] == "Command output"

    # @pytest.mark.asyncio
    # @patch(
    #    "oracle.oci_compute_instance_agent_mcp_server.server.get_compute_instance_agent_client"
    # )
    # @patch("oracle.oci_compute_instance_agent_mcp_server.server.oci.wait_until")
    # async def test_run_command_failure(self, mock_get_client, mock_wait_until):
    #    mock_client = MagicMock()
    #    mock_get_client.return_value = mock_client

    #    mock_create_response = create_autospec(oci.resource.Response)
    #    mock_create_response.data = MagicMock()
    #    mock_create_response.data.id = "command_id"
    #    mock_client.create_instance_agent_command.return_value = mock_create_response

    #    mock_execution_response = create_autospec(oci.response.Response)
    #    mock_execution_response.data = MagicMock()
    #    mock_execution_response.data.lifecycle_state = "FAILED"
    #    mock_client.get_instance_agent_command_execution.return_value = (
    #        mock_execution_response
    #    )

    #    async with Client(mcp) as client:
    #        result = (
    #            await client.call_tool(
    #                "run_command",
    #                {
    #                    "compartment_id": "test_compartment",
    #                    "instance_id": "test_instance",
    #                    "display_name": "test_command",
    #                    "script": "echo Hello",
    #                    "execution_time_out_in_seconds": 30,
    #                },
    #            )
    #        ).data

    #        assert "error_code" in result

    @pytest.mark.asyncio
    @patch(
        "oracle.oci_compute_instance_agent_mcp_server.server.get_compute_instance_agent_client"  # noqa: E501
    )
    async def test_list_instance_agent_commands(self, mock_get_client):
        compartment_id = "test_compartment"
        instance_id = "test_instance"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_command_1 = InstanceAgentCommandSummary(
            instance_agent_command_id="command1",
            compartment_id=compartment_id,
            display_name="Command 1",
            time_created="2023-01-01T00:00:00Z",
            time_updated="2023-01-01T00:00:00Z",
        )

        mock_list_response.data = [
            mock_command_1,
        ]
        mock_client.list_instance_agent_commands.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_instance_agent_commands",
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
