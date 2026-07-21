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
from fastmcp.exceptions import ToolError
import oracle.oci_api_mcp_server.server as server
from oracle.oci_api_mcp_server import __project__
from oracle.oci_api_mcp_server.denylist import Denylist
from oracle.oci_api_mcp_server.server import mcp

__version__ = importlib.metadata.version(__project__)
user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
USER_AGENT = f"{user_agent_name}/{__version__}"


class TestOCITools:
    @pytest.fixture(autouse=True)
    def clear_oci_cli_auth(self, monkeypatch):
        monkeypatch.delenv("OCI_CLI_AUTH", raising=False)

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_get_oci_command_help_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "Help output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        async with Client(mcp) as client:
            result = (
                await client.call_tool("get_oci_command_help", {"command": "compute instance list"})
            ).structured_content["result"]

            assert result == "Help output"
            assert mock_run.call_args.kwargs["env"]["OCI_SDK_APPEND_USER_AGENT"] == USER_AGENT
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
    async def test_get_oci_command_help_accepts_hyphenated_command_path(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "Help output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_oci_command_help",
                    {
                        "command": (
                            "recovery protected-database-collection "
                            "list-protected-databases"
                        )
                    },
                )
            ).structured_content["result"]

            assert result == "Help output"
            mock_run.assert_called_once_with(
                [
                    "oci",
                    "recovery",
                    "protected-database-collection",
                    "list-protected-databases",
                    "--help",
                ],
                env=ANY,
                capture_output=True,
                text=True,
                check=True,
                shell=False,
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "command",
        [
            "compute instance terminate --opc-client-request-id",
            'compute instance list --display-name "Shared Services"',
        ],
    )
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_get_oci_command_help_rejects_options(self, mock_run, command):
        mock_run.return_value.stdout = "Help output"

        async with Client(mcp) as client:
            with pytest.raises(ToolError, match="command paths only"):
                await client.call_tool("get_oci_command_help", {"command": command})

        mock_run.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("command", "error"),
        [
            ("", "command paths only"),
            ("oci compute instance list", "Do not include the 'oci' executable"),
            ("compute 'unterminated", "command paths only"),
            ("compute instance/list", "command paths only"),
        ],
    )
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_get_oci_command_help_rejects_invalid_command_paths(
        self, mock_run, command, error
    ):
        mock_run.return_value.stdout = "Help output"

        async with Client(mcp) as client:
            with pytest.raises(ToolError, match=error):
                await client.call_tool("get_oci_command_help", {"command": command})

        mock_run.assert_not_called()

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_get_oci_command_help_rejects_denylisted_command(self, mock_run):
        mock_run.return_value.stdout = "Help output"

        async with Client(mcp) as client:
            with pytest.raises(ToolError, match="denied by denylist"):
                await client.call_tool(
                    "get_oci_command_help", {"command": "compute instance terminate"}
                )

        mock_run.assert_not_called()

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
                await client.call_tool("get_oci_command_help", {"command": "compute instance list"})
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
            result = (await client.call_tool("run_oci_command", {"command": command})).data

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
            result = (await client.call_tool("run_oci_command", {"command": command})).data

            assert result == {
                "command": command,
                "output": mock_result.stdout,
                "error": mock_result.stderr,
                "returncode": mock_result.returncode,
            }

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_preserves_quoted_arguments(self, mock_run, monkeypatch, tmp_path):
        command = 'compute instance list --display-name "Shared Services"'
        config_file = tmp_path / "oci_config"
        config_file.write_text("[DEFAULT]\ntenancy=ocid1.tenancy\n")
        monkeypatch.setenv("OCI_CONFIG_FILE", str(config_file))

        mock_result = MagicMock()
        mock_result.stdout = "This is not JSON"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        async with Client(mcp) as client:
            result = (await client.call_tool("run_oci_command", {"command": command})).data

            assert result == {
                "command": command,
                "output": mock_result.stdout,
                "error": mock_result.stderr,
                "returncode": mock_result.returncode,
            }
            mock_run.assert_called_once_with(
                [
                    "oci",
                    "--profile",
                    "DEFAULT",
                    "--auth",
                    "api_key",
                    "compute",
                    "instance",
                    "list",
                    "--display-name",
                    "Shared Services",
                ],
                env=ANY,
                capture_output=True,
                text=True,
                check=True,
                shell=False,
            )

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_uses_security_token_for_direct_session_profile(
        self, mock_run, monkeypatch, tmp_path
    ):
        config_file = tmp_path / "oci_config"
        config_file.write_text("[SESSION]\nsecurity_token_file=/tmp/session-token\n")
        monkeypatch.setenv("OCI_CONFIG_FILE", str(config_file))
        monkeypatch.setenv("OCI_CONFIG_PROFILE", "SESSION")
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            await client.call_tool("run_oci_command", {"command": "compute instance list"})

        mock_run.assert_called_once_with(
            [
                "oci",
                "--profile",
                "SESSION",
                "--auth",
                "security_token",
                "compute",
                "instance",
                "list",
            ],
            env=ANY,
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
        assert mock_run.call_args.kwargs["env"]["OCI_SDK_APPEND_USER_AGENT"] == USER_AGENT

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_uses_api_key_for_profile_with_inherited_session_token(
        self, mock_run, monkeypatch, tmp_path
    ):
        config_file = tmp_path / "oci_config"
        config_file.write_text(
            "[DEFAULT]\nsecurity_token_file=/tmp/session-token\n\n[API_KEY]\ntenancy=ocid1.tenancy\n"
        )
        monkeypatch.setenv("OCI_CONFIG_FILE", str(config_file))
        monkeypatch.setenv("OCI_CONFIG_PROFILE", "API_KEY")
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            await client.call_tool("run_oci_command", {"command": "compute instance list"})

        assert mock_run.call_args.args[0] == [
            "oci",
            "--profile",
            "API_KEY",
            "--auth",
            "api_key",
            "compute",
            "instance",
            "list",
        ]

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_defers_to_oci_cli_auth_override(
        self, mock_run, monkeypatch, tmp_path
    ):
        config_file = tmp_path / "oci_config"
        config_file.write_text("[SESSION]\nsecurity_token_file=/tmp/session-token\n")
        monkeypatch.setenv("OCI_CONFIG_FILE", str(config_file))
        monkeypatch.setenv("OCI_CONFIG_PROFILE", "SESSION")
        monkeypatch.setenv("OCI_CLI_AUTH", "api_key")
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            await client.call_tool("run_oci_command", {"command": "compute instance list"})

        assert mock_run.call_args.args[0] == [
            "oci",
            "--profile",
            "SESSION",
            "compute",
            "instance",
            "list",
        ]

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_defers_to_cli_when_profile_cannot_be_classified(
        self, mock_run, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("OCI_CONFIG_FILE", str(tmp_path / "missing_config"))
        monkeypatch.setenv("OCI_CONFIG_PROFILE", "MISSING")
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            await client.call_tool("run_oci_command", {"command": "compute instance list"})

        assert mock_run.call_args.args[0] == [
            "oci",
            "--profile",
            "MISSING",
            "compute",
            "instance",
            "list",
        ]

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
            result = (await client.call_tool("run_oci_command", {"command": command})).data

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
            assert mock_run.call_args.kwargs["env"]["OCI_SDK_APPEND_USER_AGENT"] == USER_AGENT
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
                await client.call_tool("run_oci_command", {"command": "compute instance terminate"})
            ).data

            assert "error" in result
            assert any("denied by denylist" in value for value in result.values())

    @pytest.mark.parametrize(
        ("command", "normalized"),
        [
            ("compute instance terminate --instance-id ocid1.instance.oc1..example", "compute instance terminate"),
            ("--debug compute instance terminate --instance-id ocid1.instance.oc1..example", "compute instance terminate"),
            ("--raw-output compute instance terminate --instance-id ocid1.instance.oc1..example", "compute instance terminate"),
            ("--no-retry compute instance terminate --instance-id ocid1.instance.oc1..example", "compute instance terminate"),
            ("--config-file /tmp/config compute instance terminate --instance-id ocid1.instance.oc1..example", "compute instance terminate"),
        ],
    )
    def test_denylist_preserves_command_words_after_global_options(self, command, normalized):
        denylist = Denylist(MagicMock())

        assert denylist.remove_params_from_command(command) == normalized

    @pytest.mark.parametrize(
        "command",
        [
            "--debug compute instance terminate --instance-id ocid1.instance.oc1..example",
            "--raw-output compute instance terminate --instance-id ocid1.instance.oc1..example",
            "--no-retry compute instance terminate --instance-id ocid1.instance.oc1..example",
        ],
    )
    def test_denylist_blocks_destructive_commands_after_valueless_global_options(self, command):
        denylist = Denylist(MagicMock())
        denylist.denylist = ["compute instance terminate"]

        assert denylist.isCommandInDenyList(command) is True


class TestServer:
    @patch("oracle.oci_api_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv):
        mock_getenv.side_effect = lambda x: {"ORACLE_MCP_HOST": "1.2.3.4", "ORACLE_MCP_PORT": "8888"}.get(x)

        with pytest.raises(RuntimeError, match="stdio transport only"):
            server.main()

    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv):
        mock_getenv.side_effect = lambda x: {"ORACLE_MCP_HOST": "1.2.3.4"}.get(x)

        with pytest.raises(RuntimeError, match="stdio transport only"):
            server.main()

    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv):
        mock_getenv.side_effect = lambda x: {"ORACLE_MCP_PORT": "8888"}.get(x)

        with pytest.raises(RuntimeError, match="stdio transport only"):
            server.main()
