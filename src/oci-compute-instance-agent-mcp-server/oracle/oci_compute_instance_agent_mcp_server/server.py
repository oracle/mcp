"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Optional

import oci
from fastmcp import FastMCP
from oci.compute_instance_agent.models import (
    CreateInstanceAgentCommandDetails,
    InstanceAgentCommand,
    InstanceAgentCommandContent,
    InstanceAgentCommandOutputViaTextDetails,
    InstanceAgentCommandSourceViaTextDetails,
    InstanceAgentCommandTarget,
)
from oracle.oci_compute_instance_agent_mcp_server.models import (
    InstanceAgentCommandExecution,
    InstanceAgentCommandExecutionSummary,
    map_instance_agent_command_execution,
    map_instance_agent_command_execution_summary,
)
from pydantic import Field

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_compute_instance_agent_client():
    logger.info("entering get_compute_instance_agent_client")
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )

    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    token = None
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.compute_instance_agent.ComputeInstanceAgentClient(config, signer=signer)


@mcp.tool(
    description="Runs a script on a compute instance",
)
def run_instance_agent_command(
    compartment_id: str = Field(
        ..., description="The OCID of the compartment to create the command in"
    ),
    instance_id: str = Field(
        ..., description="The OCID of the instance to run the command on"
    ),
    display_name: str = Field(
        ...,
        description="The display name of the command"
        "If no value is provded, then you can pass in "
        '"agent-command-<year><month><day>-<hour><minute>" '
        "where those time values come from the current date time",
    ),
    script: str = Field(..., description="The plain text command to run"),
    execution_time_out_in_seconds: Optional[int] = Field(
        30, description="The command's timeout in seconds"
    ),
) -> InstanceAgentCommandExecution:
    try:
        client = get_compute_instance_agent_client()
        command_details = CreateInstanceAgentCommandDetails(
            display_name=display_name,
            compartment_id=compartment_id,
            target=InstanceAgentCommandTarget(
                instance_id=instance_id,
            ),
            content=InstanceAgentCommandContent(
                source=InstanceAgentCommandSourceViaTextDetails(
                    source_type=InstanceAgentCommandSourceViaTextDetails.SOURCE_TYPE_TEXT,
                    text=script,
                ),
                output=InstanceAgentCommandOutputViaTextDetails(
                    output_type=InstanceAgentCommandOutputViaTextDetails.OUTPUT_TYPE_TEXT,
                ),
            ),
            execution_time_out_in_seconds=execution_time_out_in_seconds,
        )

        # Trigger the command
        response: oci.response.Response = client.create_instance_agent_command(
            create_instance_agent_command_details=command_details
        )
        data: InstanceAgentCommand = response.data

        # Poll until the command finishes
        command_id = data.id
        execution_response: oci.response.Response = (
            client.get_instance_agent_command_execution(
                instance_agent_command_id=command_id, instance_id=instance_id
            )
        )

        final_response: oci.response.Response = oci.wait_until(
            client=client,
            response=execution_response,
            property="lifecycle_state",
            state=oci.compute_instance_agent.models.InstanceAgentCommandExecution.LIFECYCLE_STATE_SUCCEEDED,
            max_interval_seconds=5,
            max_wait_seconds=240,
        )
        final_data: InstanceAgentCommandExecution = final_response.data

        logger.info("Executed instance agent command")
        return map_instance_agent_command_execution(final_data)
    except Exception as e:
        logger.error(f"Error in run_instance_agent_command tool: {str(e)}")
        raise e


@mcp.tool(description="Lists an instance's agent command executions")
def list_instance_agent_command_executions(
    compartment_id: str = Field(
        ..., description="The OCID of the compartment to list commands from"
    ),
    instance_id: str = Field(
        ..., description="The OCID of the instance to list commands from"
    ),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of commands to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[InstanceAgentCommandExecutionSummary]:
    commands: list[InstanceAgentCommandExecutionSummary] = []

    try:
        client = get_compute_instance_agent_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(commands) < limit):
            kwargs = {
                "compartment_id": compartment_id,
                "instance_id": instance_id,
                "page": next_page,
                "limit": limit,
            }

            response = client.list_instance_agent_command_executions(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[
                oci.compute_instance_agent.models.InstanceAgentCommandExecutionSummary
            ] = response.data
            for d in data:
                commands.append(map_instance_agent_command_execution_summary(d))

        logger.info(f"Found {len(commands)} Instance Agent Commands")
        return commands

    except Exception as e:
        logger.error(f"Error in list_instance_agent_command_executions tool: {str(e)}")
        raise e


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
