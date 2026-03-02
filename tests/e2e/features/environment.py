"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
import os
import subprocess
import sys
import tempfile
import time

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

try:
    config = {}

    config["MCP_HOST_FILE"] = os.environ.get(
        "MCP_HOST_FILE", os.path.join(os.path.dirname(__file__), "mcphost.json")
    )
    config["URL"] = os.environ.get("URL", "http://localhost:8000/api/chat")
    config["MODEL"] = os.environ.get("MODEL", "gpt-oss:20b")

except FileNotFoundError:
    raise EnvironmentError(
        print(f"{config['MCP_HOST_FILE']} could not be found. Provide one to configure the MCP servers")
    )

_system_prompt = f"""You are an Oracle Cloud Infrastructure expert generative chat assistant. You are working out of this tenancy (also know as the root compartment): ocid1.tenancy.oc1..mock. For any compartment IDs, just pass in the tenancy ID. Limit your answers to OCI. OCID is synonymous with ID. If the user makes a request that relies on a tool that requires a compartment id, and the user doesn't specify one, don't ask the user for the compartment id and use the active (current) compartment instead. If I ask you for a list of things, prefer either a tabular or text-based approach over dumping them in a code block. When formatting your response, don't use bullets or lists within tables. When a user makes a request, you must first attempt to fulfill it by using the available MCP tools. These tools are connected to our live data sources and provide the most accurate and real-time information. Only after exhausting the capabilities of the MCP tools should you resort to other methods, such as using a general web search, if the MCP tools cannot provide the necessary information. If there is an error in calling the run_oci_command tool, then try to use the get_oci_command_help tool to get more information on the command and retry with the updated information. Don't send back emojis in the responses."""  # noqa ES501


def set_mcp_servers(context):
    try:
        context.mcp_servers = []
        with open(config["MCP_HOST_FILE"], "r") as f:
            mcp_hosts = json.load(f)
            for key in mcp_hosts["mcpServers"]:
                context.mcp_servers.append(key.replace("-", "_"))

        print("Configured servers: ", ", ".join(sorted(context.mcp_servers)))
    except FileNotFoundError:
        raise EnvironmentError(
            f"{config['MCP_HOST_FILE']} could not be found. Provide one to configure the MCP servers"
        )


def wait_for_health_check(context, url, service_name, max_retries=30):
    print(f"Waiting for {service_name} to become healthy...")
    ready = False
    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/health", timeout=1)
            if response.status_code == 200:
                print(f"{service_name} is ready after {i} seconds.")
                ready = True
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)

    if not ready:
        cleanup_all_processes(context)
        raise RuntimeError(f"{service_name} failed to become healthy within {max_retries} seconds.")


def before_all(context):
    """Start Mock OCI Server, Proxy Shim, and MCP bridge with explicit variables"""
    # Initialize attributes to None so cleanup doesn't fail if setup crashes early
    context.mock_proc = None
    context.shim_proc = None
    context.bridge_proc = None

    try:
        base_dir = os.path.dirname(__file__)
        mock_server_path = os.path.join(base_dir, "mocks", "mock_oci_server.py")
        proxy_shim_path = os.path.join(base_dir, "mocks", "proxy_shim.py")

        # Set up directory for mock OCI config
        context.temp_dir = tempfile.TemporaryDirectory()

        # Create a dummy private key
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        key_data = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        key_path = os.path.join(context.temp_dir.name, "dummy_key.pem")
        with open(key_path, "wb") as f:
            f.write(key_data)

        # Create a dummy security token
        token_path = os.path.join(context.temp_dir.name, "token.txt")
        with open(token_path, "w") as f:
            f.write("mock-security-token")

        # Create the Mock OCI Config
        mock_region = "us-mock-1"  # This is important for the mock SSL creation
        config_path = os.path.join(context.temp_dir.name, "config")
        with open(config_path, "w") as f:
            f.write(
                f"""
[DEFAULT]
user=ocid1.user.oc1..mock
fingerprint=00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00
key_file={key_path}
tenancy=ocid1.tenancy.oc1..mock
region={mock_region}
security_token_file={token_path}
"""
            )

        # Start Mock Server (Port 5001)
        print("Starting Mock OCI Server on http://127.0.0.1:5001...")
        context.mock_proc = subprocess.Popen(
            [sys.executable, mock_server_path],
        )

        wait_for_health_check(context, "http://127.0.0.1:5001", "Mock OCI Server")

        # Prepare Proxy Shim's env
        shim_env = os.environ.copy()
        shim_env["MOCK_REGION"] = mock_region
        shim_env["OCI_CONFIG_FILE"] = config_path

        # Start Proxy Shim (Port 5000)
        print("Starting Proxy Shim on http://127.0.0.1:5000...")
        context.shim_proc = subprocess.Popen([sys.executable, proxy_shim_path], env=shim_env)

        wait_for_health_check(context, "http://127.0.0.1:5000", "Proxy Shim")

        # Configure MCP servers
        set_mcp_servers(context)

        # Prepare MCP Bridge's env
        bridge_env = os.environ.copy()
        bridge_env["OCI_CONFIG_FILE"] = config_path

        # Start MCP Bridge
        print(f"Starting MCP Bridge with {len(context.mcp_servers)} servers...")
        context.bridge_proc = subprocess.Popen(
            ["uv", "run", "ollama-mcp-bridge", "--config", config["MCP_HOST_FILE"]],
            env=bridge_env,
            preexec_fn=os.setpgrp,
        )

        wait_for_health_check(context, "http://localhost:8000", "MCP Bridge")

        # Immediate health check
        if context.bridge_proc.poll() is not None:
            raise RuntimeError("MCP Bridge failed to start.")

        # Final Context setup
        context.system_message = {"role": "system", "content": _system_prompt}
        context.url = config["URL"]
        context.model = config["MODEL"]

    except Exception as e:
        print(f"CRITICAL SETUP ERROR: {e}")
        cleanup_all_processes(context)
        raise e


def cleanup_all_processes(context):
    """Clean up the specific named processes"""
    procs_to_kill = [
        ("Bridge", getattr(context, "bridge_proc", None)),
        ("Shim", getattr(context, "shim_proc", None)),
        ("Mock", getattr(context, "mock_proc", None)),
    ]

    for name, proc in procs_to_kill:
        if proc and proc.poll() is None:
            print(f"Shutting down {name} (PID: {proc.pid})...")
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()


def after_all(context):
    cleanup_all_processes(context)
