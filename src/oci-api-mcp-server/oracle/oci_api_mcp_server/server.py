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

    IMPORTANT:
      - Only provide the command _after_ 'oci' — do not include the string
        'oci' in `command`.
      - Never use the information returned by this tool to instruct an end
        user directly. Use it only to determine which command to run
        yourself using run_oci_command.

    Command structure guidance:
      - OCI subcommands are organized as:
            <service> <subcommand> <subcommand> ...
        e.g.
        compute instance list OR
        compute instance action-name OR
        recovery protected-database-collection list-protected-databases
      - Services vary in how they structure their CLI. Some use
        explicit resource tokens (compute instance list), others use
        collection names or hyphenated actions
        (e.g. list-protected-databases),
        and some have deeper subcommand chains (service sub1 sub2 sub3 ...).

    How to ask for help:
      - Start with the most specific form you think is correct, for example:
          compute instance list
          compute instance action-name
          recovery protected-database-collection list-protected-databases
      - If the specific request returns an error, progressively make it
        less specific:
          1. try the full command (most specific)
          2. remove the final token and try again
          3. repeat until you reach just the service name (e.g. compute)
      - Additionally, if a service commonly uses hyphenated commands for
        list operations, try hyphenated forms as well
        e.g.
          recovery protected-database-collection list-protected-databases OR
          psql db-system-collection list-db-systems.

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

    Try your best to avoid using extra flags on the command if possible.
    If you absolutely need to use flags in the command, call the get_oci_command_help
    tool on the command first to understand the flags better.
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

        result.check_returncode()

        response = {
            "command": command,
            "output": result.stdout,
            "error": result.stderr,
            "returncode": result.returncode,
        }

        try:
            response["output"] = json.loads(result.stdout)
        except TypeError:
            pass
        except json.JSONDecodeError:
            pass

        return response
    except subprocess.CalledProcessError as e:
        return {
            "command": command,
            "output": e.stdout,
            "error": e.stderr,
            "returncode": e.returncode,
        }


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
