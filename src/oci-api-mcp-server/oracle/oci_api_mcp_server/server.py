"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
import os
import subprocess
from logging import Logger
from typing import Annotated

import oci
from fastmcp import FastMCP
from oracle.oci_api_mcp_server import __project__, __version__
from oracle.oci_api_mcp_server.denylist import Denylist
from oracle.oci_api_mcp_server.utils import initAuditLogger

logger = Logger(__project__, level="INFO")

mcp = FastMCP(name=__project__)

# setup user agent
user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
USER_AGENT = f"{user_agent_name}/{__version__}"

# Initialize the rotating audit logger. It will store logs at /tmp/audit.log
initAuditLogger(logger)

# Read and setup deny list
denylist_manager = Denylist(logger)

# Initialize the MCP server
mcp = FastMCP(
    name="oracle.oci-api-mcp-server",
    instructions="""
        This server provides tools to run the OCI CLI commands to interact with OCI services.
        Use the resource resource://oci-api-commands to get information on OCI services and
        related commands available for each service. You can use this information to identify
        which commands to run for a specific service.
        Call get_oci_command_help to provide information about a specific OCI command.
        Call run_oci_command to run a specific OCI command
    """,
)


@mcp.resource("resource://oci-api-commands")
def get_oci_commands() -> str:
    """Returns helpful information on various OCI services and related commands."""
    logger.info("get_oci_commands resource has been called into action")
    env_copy = os.environ.copy()
    env_copy["OCI_SDK_APPEND_USER_AGENT"] = USER_AGENT

    try:
        # Run OCI CLI command using subprocess
        result = subprocess.run(
            ["oci", "--help"],
            env=env_copy,
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"


@mcp.tool
def get_oci_command_help(command: str) -> str:
    """Returns helpful instructions for running an OCI CLI command.
    Only provide the command after 'oci', do not include the string 'oci'
    in your command.

    Never use the information returned by this tool to tell a user what
    to do, only use it to help you determine which command to run yourself
    using the run_oci_command tool.

    CLI commands are structured as <service> <resource> <action>; you can get
    help at the service level, resource level or action level, respectively:
        1. compute
        2. compute instance
        3. compute instance list

    If your request for help for a specific command
    returns an error, make your requests successively less specific;
    example:
        1. compute instance list
        2. compute instance
        3. compute
    """
    logger.info(f"get_oci_command_help called with command: {command}")
    env_copy = os.environ.copy()
    env_copy["OCI_SDK_APPEND_USER_AGENT"] = USER_AGENT

    try:
        # Run OCI CLI command using subprocess
        result = subprocess.run(
            ["oci"] + command.split() + ["--help"],
            env=env_copy,
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error in get_oci_command_help: {e.stderr}")
        return f"Error: {e.stderr}"


@mcp.tool
def run_oci_command(
    command: Annotated[
        str,
        "The OCI CLI command to run. Do not include 'oci' in your command",
    ],
) -> dict:
    """Runs an OCI CLI command.
    This tool allows you to run OCI CLI commands on the user's behalf.

    Only provide the command after 'oci', do not include the string 'oci'
    in your command.

    Never tell the user which command to run, only run it for them using
    this tool.
    """

    env_copy = os.environ.copy()
    env_copy["OCI_SDK_APPEND_USER_AGENT"] = USER_AGENT

    profile = os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    logger.info(f"run_oci_command called with command: {command} --profile {profile}")

    # Check if command is in denylist
    if denylist_manager.isCommandInDenyList(command):
        error_message = (
            f"Command '{command}' is denied by denylist. This command is found in the "
            "deny list and is not executed as it can delete resources or alter the "
            "configuration of your cloud services. Please terminate any tasks "
            "currently related to the execution of this command and stop finding any "
            "alternative solutions to executing this command."
        )
        logger.error(error_message)
        return {"error": error_message}

    # Run OCI CLI command using subprocess
    try:
        result = subprocess.run(
            ["oci", "--profile"]
            + [profile]
            + ["--auth", "security_token"]
            + command.split(),
            env=env_copy,
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
        return (
            json.loads(result.stdout)
            if result.stdout
            else {
                "error": result.stderr,
            }
        )
    except subprocess.CalledProcessError as e:
        return {
            "error": e.stderr,
            "output": e.stdout,
        }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
