"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
import os
import subprocess
import time


def set_default(obj, attribute, value):
    if attribute not in obj or not obj[attribute]:
        obj[attribute] = value


try:
    config_path = os.path.join(os.path.dirname(__file__), ".env")
    mcp_host_file = os.path.join(os.path.dirname(__file__), "mcphost.json")
    config = {}
    with open(config_path, "r") as config_file:
        for line in config_file:
            line = line.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()

    # set defaults
    set_default(config, "MCP_HOST_FILE", mcp_host_file)
    set_default(config, "URL", "http://localhost:8000/api/chat")
    set_default(config, "MODEL", "gpt-oss:20b")
    set_default(config, "COMPARTMENT_OCID", config["TENANCY_OCID"])
    set_default(config, "USER_NAME", "")
    set_default(config, "REGION", "us-ashburn-1")

except FileNotFoundError:
    raise EnvironmentError(
        print(
            "\nPlease provide the environment configuration through the .env file.\n"
            "You can copy .env.template and fill with data\n\n"
        )
    )

_system_prompt = f"""You are an Oracle Cloud Infrastructure expert generative chat assistant. Limit your answers to OCI. OCID is synonymous with ID. The logged in user's OCID is '{config["USER_OCID"]}', and the display name is {config["USER_NAME"]}. The tenancy OCID is '{config["TENANCY_OCID"]}', which is also called the root compartment. The active (current) tenancy name is {config["TENANCY_NAME"]}. The active (current) region is {config["REGION"]}. The active (current) compartment is '{config["COMPARTMENT_OCID"]}'. If the user makes a request that relies on a tool that requires a compartment id, and the user doesn't specify one, don't ask the user for the compartment id and use the root compartment instead. If I ask you for a list of things, prefer either a tabular or text-based approach over dumping them in a code block. When formatting your response, don't use bullets or lists within tables. When a user makes a request, you must first attempt to fulfill it by using the available MCP tools. These tools are connected to our live data sources and provide the most accurate and real-time information. Only after exhausting the capabilities of the MCP tools should you resort to other methods, such as using a general web search, if the MCP tools cannot provide the necessary information. If there is an error in calling the run_oci_command tool, then try to use the get_oci_command_help tool to get more information on the command and retry with the updated information. Don't send back emojis in the responses."""  # noqa ES501


def set_mcp_servers(context):
    try:
        context.mcp_servers = []
        with open(mcp_host_file, "r") as f:
            mcp_hosts = json.load(f)
            for key in mcp_hosts["mcpServers"]:
                context.mcp_servers.append(key.replace("-", "_"))

        print("Configured servers: ", ", ".join(sorted(context.mcp_servers)))
    except FileNotFoundError:
        raise EnvironmentError(
            f"{mcp_host_file} could not be found. Provide one to configure the MCP servers"
        )


def before_all(context):
    """Start the MCP bridge before running any prompts"""
    try:
        # set the current configured mcp servers
        set_mcp_servers(context)

        # load the MCP servers
        context.bridge_proc = subprocess.Popen(
            ["uvx", "ollama-mcp-bridge", "--config", config["MCP_HOST_FILE"]]
        )
        print("Waiting for servers to start...", flush=True)
        time.sleep(
            2 * len(context.mcp_servers or 10)
        )  # Give the server and bridge time to start 2s per server seems to be good.

        if context.bridge_proc.poll() is not None:
            raise RuntimeError("Process failed to start")

        # add global defaults to the context
        context.system_message = {"role": "system", "content": _system_prompt}
        context.url = config["URL"]
        context.model = config["MODEL"]

        print("\n\n Starting tests...\n\n")
    except FileNotFoundError as e:
        raise EnvironmentError(
            f"Command not found: {e.filename}. Ensure it's installed and in your PATH."
        )


def after_all(context):
    """Terminate the MCP bridge"""
    print("Checking and terminating process...")
    # Poll the process to get its return code
    return_code = context.bridge_proc.poll()

    if return_code is None:
        # Process is still running, terminate it
        print("Process is still running. Terminating...")
        context.bridge_proc.terminate()
        # Optionally, check again to see if it terminated cleanly
        context.bridge_proc.wait(timeout=5)
        print("Process terminated.")
    elif return_code != 0:
        # Process exited with an error code, meaning it failed
        stdout, stderr = context.bridge_proc.communicate()
        error_message = f"Process closed prematurely with exit code {return_code}\n"
        error_message += f"Stdout: {stdout}\nStderr: {stderr}"
        raise RuntimeError(error_message)
    else:
        # Process exited cleanly (with code 0) but was not expected to
        raise RuntimeError("Process closed unexpectedly but cleanly.")
