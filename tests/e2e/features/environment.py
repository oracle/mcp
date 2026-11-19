"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import socket

from codex_runner import (
    isolated_session,
    prepare_environments,
    run_process,
    stop_process_group,
    termination_cleanup,
    translate_hosts,
)

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

config = {
    "MCP_HOST_FILE": os.environ.get("MCP_HOST_FILE") or str(Path(__file__).with_name("mcphost.json")),
    "MODEL": os.environ.get("CODEX_E2E_MODEL") or "gpt-6.1-sol",
    "TIMEOUT": float(os.environ.get("CODEX_E2E_TIMEOUT") or 180),
}

_system_prompt = f"""You are an Oracle Cloud Infrastructure expert generative chat assistant. You are working out of this tenancy (also know as the root compartment): ocid1.tenancy.oc1..mock. For any compartment IDs, just pass in the tenancy ID. Limit your answers to OCI. OCID is synonymous with ID. If the user makes a request that relies on a tool that requires a compartment id, and the user doesn't specify one, don't ask the user for the compartment id and use the active (current) compartment instead. If I ask you for a list of things, prefer either a tabular or text-based approach over dumping them in a code block. When formatting your response, don't use bullets or lists within tables. When a user makes a request, you must first attempt to fulfill it by using the available MCP tools. These tools are connected to our live data sources and provide the most accurate and real-time information. Only after exhausting the capabilities of the MCP tools should you resort to other methods, such as using a general web search, if the MCP tools cannot provide the necessary information. If there is an error in calling the run_oci_command tool, then try to use the get_oci_command_help tool to get more information on the command and retry with the updated information. Don't send back emojis in the responses."""  # noqa ES501


def wait_for_health_check(proc, url, service_name):
    # Local mock health must never use a personal inference/corporate proxy.
    with requests.Session() as client:
        client.trust_env = False
        for _ in range(30):
            if proc.poll() is not None:
                raise RuntimeError(f"{service_name} exited during startup")
            try:
                if client.get(f"{url}/health", timeout=1).status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.1)
    raise RuntimeError(f"{service_name} did not become healthy")


def before_all(context):
    """Start the mock OCI services; each scenario owns its fresh Codex session."""
    # Initialize attributes to None so cleanup doesn't fail if setup crashes early
    context.mock_proc = None
    context.shim_proc = None
    context.temp_dir = None
    termination = termination_cleanup()
    termination.__enter__()
    context.add_cleanup(termination.__exit__, None, None, None)

    try:
        base_dir = os.path.dirname(__file__)
        mock_server_path = os.path.join(base_dir, "mocks", "mock_oci_server.py")
        proxy_shim_path = os.path.join(base_dir, "mocks", "proxy_shim.py")

        # Set up directory for mock OCI config
        context.temp_dir = tempfile.TemporaryDirectory()

        # Select local ports without taking over existing services (e.g. macOS AirPlay).
        ports = []
        for _ in range(2):
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                ports.append(probe.getsockname()[1])
        mock_port, proxy_port = ports
        context.proxy_url = f"http://127.0.0.1:{proxy_port}"
        mock_env = {key: os.environ[key] for key in ("PATH", "LANG") if key in os.environ}
        mock_env.update(HOME=context.temp_dir.name, TMPDIR=context.temp_dir.name)
        mock_env.update(MOCK_OCI_PORT=str(mock_port), MOCK_PROXY_PORT=str(proxy_port))

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

        translate_hosts(config["MCP_HOST_FILE"], config_path, context.temp_dir.name, context.proxy_url)
        prepare_environments(config["MCP_HOST_FILE"])

        # Start Mock Server (Port 5001)
        print(f"Starting Mock OCI Server on http://127.0.0.1:{mock_port}...")
        context.mock_proc = subprocess.Popen(
            [sys.executable, mock_server_path],
            env=mock_env,
            start_new_session=True,
        )

        wait_for_health_check(context.mock_proc, f"http://127.0.0.1:{mock_port}", "Mock OCI Server")

        # Prepare Proxy Shim's env
        shim_env = mock_env.copy()
        shim_env["MOCK_REGION"] = mock_region
        shim_env["OCI_CONFIG_FILE"] = config_path

        # Start Proxy Shim (Port 5000)
        print(f"Starting Proxy Shim on {context.proxy_url}...")
        context.shim_proc = subprocess.Popen(
            [sys.executable, proxy_shim_path], env=shim_env, start_new_session=True
        )

        wait_for_health_check(context.shim_proc, context.proxy_url, "Proxy Shim")
        context.mock_config = Path(config_path)

    except BaseException as e:
        print(f"CRITICAL SETUP ERROR: {e}")
        cleanup_all_processes(context)
        raise


def before_scenario(context, scenario):
    manager = isolated_session(
        config["MCP_HOST_FILE"],
        context.mock_config,
        config["MODEL"],
        context.proxy_url,
    )
    session = manager.__enter__()
    context.add_cleanup(manager.__exit__, None, None, None)
    context.codex = session
    context.mcp_servers = list(session.servers)
    context.inventory_only = "tools available" in scenario.name.lower()
    version = run_process([session.command[0], "--version"], "", session.env, session.cwd, timeout=10)
    print(f"Runtime: {version.strip()}; model: {config['MODEL']}")
    context.codex_timeout = config["TIMEOUT"]
    context.system_prompt = _system_prompt + (
        " Use only the configured MCP tools and mock OCI data. Do not use shell, web, or fixture files."
        " For tool inventories, include exact server and tool names."
    )


def cleanup_all_processes(context):
    for attribute in ("shim_proc", "mock_proc"):
        proc = getattr(context, attribute, None)
        if proc is not None:
            stop_process_group(proc)
    directory = getattr(context, "temp_dir", None)
    if directory is not None:
        directory.cleanup()


def after_all(context):
    cleanup_all_processes(context)
