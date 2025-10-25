"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Annotated

import oci
from fastmcp import FastMCP
from oci.compute_instance_agent.models import (
    CreateInstanceAgentCommandDetails,
    InstanceAgentCommandContent,
    InstanceAgentCommandExecution,
    InstanceAgentCommandOutputViaTextDetails,
    InstanceAgentCommandSourceViaTextDetails,
    InstanceAgentCommandTarget,
)

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


@mcp.tool
def run_command(
    compartment_id: str,
    instance_id: str,
    display_name: Annotated[
        str, "Display name of the command, this parameter is required"
    ],
    script: str,
    execution_time_out_in_seconds: int,
):
    """Run a command on a compute instance"""
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
        execution_time_out_in_seconds=30,
    )

    response = client.create_instance_agent_command(
        create_instance_agent_command_details=command_details
    ).data

    command_id = response.id

    try:
        execution_response = client.get_instance_agent_command_execution(
            instance_agent_command_id=command_id, instance_id=instance_id
        )

        final_response = oci.wait_until(
            client=client,
            response=execution_response,
            property="lifecycle_state",
            state=InstanceAgentCommandExecution.LIFECYCLE_STATE_SUCCEEDED,
            max_interval_seconds=5,
            max_wait_seconds=240,
        )

        if final_response.data.content and (
            final_response.data.content.output_type
            == InstanceAgentCommandOutputViaTextDetails.OUTPUT_TYPE_TEXT
        ):
            return {
                "command_id": command_id,
                "instance_id": instance_id,
                "exit_code": final_response.data.content.exit_code,
                "text": final_response.data.content.text,
            }
    except oci.exceptions.ServiceError as e:
        return {
            "error_code": e.code,
            "message": e.message,
        }


@mcp.tool
def list_instance_agent_commands(compartment_id: str, instance_id: str) -> list[dict]:
    """Get instance agent commands"""
    client = get_compute_instance_agent_client()
    commands = client.list_instance_agent_commands(
        compartment_id=compartment_id,
        instance_id=instance_id,
    ).data

    return [
        {
            "compartment_id": command.compartment_id,
            "display_name": command.display_name,
            "instance_agent_command_id": command.instance_agent_command_id,
            "is_canceled": command.is_canceled,
            "time_created": command.time_created,
            "time_updated": command.time_updated,
        }
        for command in commands
    ]


def main():
    mcp.run()


if __name__ == "__main__":
    main()
