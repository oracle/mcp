"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import importlib.metadata
import json
import subprocess
from unittest.mock import ANY, MagicMock, patch

import pytest
from fastmcp import Client
from oracle.oci_api_mcp_server import __project__
from oracle.oci_api_mcp_server.server import mcp

__version__ = importlib.metadata.version(__project__)
user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
USER_AGENT = f"{user_agent_name}/{__version__}"


class TestOCITools:
    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_get_oci_command_help_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "Help output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_oci_command_help", {"command": "compute instance list"}
                )
            ).structured_content["result"]

            assert result == "Help output"
            assert (
                mock_run.call_args.kwargs["env"]["OCI_SDK_APPEND_USER_AGENT"]
                == USER_AGENT
            )
            mock_run.assert_called_once_with(
                ["oci", "compute", "instance", "list", "--help"],
                env=ANY,
                capture_output=True,
                text=True,
                check=True,
                shell=False,
            )

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_get_oci_command_help_failure(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "Some output"
        mock_result.stderr = "Some error"
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["oci", "compute", "instance", "list", "--help"],
            output=mock_result.stdout,
            stderr=mock_result.stderr,
        )

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_oci_command_help", {"command": "compute instance list"}
                )
            ).structured_content["result"]

            assert "Error: Some error" in result

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_success(self, mock_run):
        command = "compute instance list"

        mock_result = MagicMock()
        mock_result.stdout = '{"key": "value"}'
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        async with Client(mcp) as client:
            result = (
                await client.call_tool("run_oci_command", {"command": command})
            ).data

            assert result == {
                "command": command,
                "output": json.loads(mock_result.stdout),
                "error": mock_result.stderr,
                "returncode": mock_result.returncode,
            }

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_string_success(self, mock_run):
        command = "compute instance list"

        mock_result = MagicMock()
        mock_result.stdout = "This is not JSON"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        async with Client(mcp) as client:
            result = (
                await client.call_tool("run_oci_command", {"command": command})
            ).data

            assert result == {
                "command": command,
                "output": mock_result.stdout,
                "error": mock_result.stderr,
                "returncode": mock_result.returncode,
            }

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_failure(self, mock_run):
        command = "compute instance list"

        mock_result = MagicMock()
        mock_result.stdout = "Some output"
        mock_result.stderr = "Some error"
        mock_result.returncode = 1

        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=mock_result.returncode,
            cmd=["oci"] + command.split(),
            output=mock_result.stdout,
            stderr=mock_result.stderr,
        )

        async with Client(mcp) as client:
            result = (
                await client.call_tool("run_oci_command", {"command": command})
            ).data

            assert result == {
                "command": command,
                "output": mock_result.stdout,
                "error": mock_result.stderr,
                "returncode": mock_result.returncode,
            }

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_get_oci_commands_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "OCI commands output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        async with Client(mcp) as client:
            result = (await client.read_resource("resource://oci-api-commands"))[0].text

            assert result == "OCI commands output"
            assert (
                mock_run.call_args.kwargs["env"]["OCI_SDK_APPEND_USER_AGENT"]
                == USER_AGENT
            )
            mock_run.assert_called_once_with(
                ["oci", "--help"],
                env=ANY,
                capture_output=True,
                text=True,
                check=True,
                shell=False,
            )

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_get_oci_commands_failure(self, mock_run):
        mock_result = MagicMock()
        mock_result.stderr = "Some error"
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["oci", "--help"],
            output=None,
            stderr=mock_result.stderr,
        )

        async with Client(mcp) as client:
            result = (await client.read_resource("resource://oci-api-commands"))[0].text

            assert "error" in result

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    @patch("oracle.oci_api_mcp_server.server.json.loads")
    async def test_run_oci_command_denied(self, mock_json_loads, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = '{"key": "value"}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        mock_json_loads.return_value = {"key": "value"}

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "run_oci_command", {"command": "compute instance terminate"}
                )
            ).data

            assert "error" in result
            assert any("denied by denylist" in value for value in result.values())


class TestServer:
    @patch("oracle.oci_api_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": 8888,
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_api_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=mock_env["ORACLE_MCP_PORT"],
        )

    @patch("oracle.oci_api_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        import oracle.oci_api_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_api_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_api_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_api_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_api_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
