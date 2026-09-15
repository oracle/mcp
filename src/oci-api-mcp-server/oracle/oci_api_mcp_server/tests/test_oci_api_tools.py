"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import importlib.metadata
import json
import os
from pathlib import Path
import runpy
import subprocess
from unittest.mock import ANY, MagicMock, patch

import click
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from oci.config import DEFAULT_LOCATION
from oci_cli import dynamic_loader
from oci_cli.cli_root import cli as oci_cli
import oracle.oci_api_mcp_server.server as server
from oracle.oci_api_mcp_server import __project__
from oracle.oci_api_mcp_server.denylist import Denylist
from oracle.oci_api_mcp_server.server import mcp

__version__ = importlib.metadata.version(__project__)
user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
USER_AGENT = f"{user_agent_name}/{__version__}"
OCI_CLI = server._OCI_CLI_BASE_COMMAND[0]
DENYLIST_GENERATOR = runpy.run_path(
    str(Path(__file__).parents[5] / "scripts" / "oci-api-denylist-generator.py")
)


class TestOCITools:
    @pytest.fixture(autouse=True)
    def clear_oci_cli_auth(self, monkeypatch):
        for name in (
            "OCI_CLI_AUTH",
            "OCI_CLI_CONFIG_FILE",
            "OCI_CONFIG_FILE",
            "OCI_CONFIG_PROFILE",
            "OCI_MCP_AUTH_TYPE",
            "OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN_PATH",
            "OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN",
        ):
            monkeypatch.delenv(name, raising=False)
        # These tests mock OCI CLI execution, so use an explicit auth type instead
        # of relying on a developer machine's default OCI profile for auto resolution.
        monkeypatch.setenv("OCI_MCP_AUTH_TYPE", "api_key")

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
                [
                    OCI_CLI,
                    "--cli-rc-file",
                    os.devnull,
                    "compute",
                    "instance",
                    "list",
                    "--help",
                ],
                env=ANY,
                stdin=subprocess.DEVNULL,
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
                    OCI_CLI,
                    "--cli-rc-file",
                    os.devnull,
                    "recovery",
                    "protected-database-collection",
                    "list-protected-databases",
                    "--help",
                ],
                env=ANY,
                stdin=subprocess.DEVNULL,
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
            cmd=[
                OCI_CLI,
                "--cli-rc-file",
                os.devnull,
                "compute",
                "instance",
                "list",
                "--help",
            ],
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
                    OCI_CLI,
                    "--cli-rc-file",
                    os.devnull,
                    "--config-file",
                    str(config_file),
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
                stdin=subprocess.DEVNULL,
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
        monkeypatch.delenv("OCI_MCP_AUTH_TYPE")
        config_file = tmp_path / "oci_config"
        config_file.write_text("[SESSION]\nsecurity_token_file=/tmp/session-token\n")
        monkeypatch.setenv("OCI_CONFIG_FILE", str(config_file))
        monkeypatch.setenv("OCI_CONFIG_PROFILE", "SESSION")
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            await client.call_tool("run_oci_command", {"command": "compute instance list"})

        mock_run.assert_called_once_with(
            [
                OCI_CLI,
                "--cli-rc-file",
                os.devnull,
                "--config-file",
                str(config_file),
                "--profile",
                "SESSION",
                "--auth",
                "security_token",
                "compute",
                "instance",
                "list",
            ],
            env=ANY,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
        assert mock_run.call_args.kwargs["env"]["OCI_SDK_APPEND_USER_AGENT"] == USER_AGENT

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_uses_resolved_config_file_over_cli_config_env(
        self, mock_run, monkeypatch, tmp_path
    ):
        monkeypatch.delenv("OCI_MCP_AUTH_TYPE")
        inspected_config = tmp_path / "inspected_config"
        inspected_config.write_text("[SESSION]\nsecurity_token_file=/tmp/session-token\n")
        cli_config = tmp_path / "cli_config"
        cli_config.write_text("[SESSION]\ntenancy=ocid1.tenancy\n")
        monkeypatch.setenv("OCI_CONFIG_FILE", str(inspected_config))
        monkeypatch.setenv("OCI_CLI_CONFIG_FILE", str(cli_config))
        monkeypatch.setenv("OCI_CONFIG_PROFILE", "SESSION")
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            await client.call_tool("run_oci_command", {"command": "compute instance list"})

        assert mock_run.call_args.args[0] == [
            OCI_CLI,
            "--cli-rc-file",
            os.devnull,
            "--config-file",
            str(inspected_config),
            "--profile",
            "SESSION",
            "--auth",
            "security_token",
            "compute",
            "instance",
            "list",
        ]

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_uses_api_key_for_profile_with_inherited_session_token(
        self, mock_run, monkeypatch, tmp_path
    ):
        monkeypatch.delenv("OCI_MCP_AUTH_TYPE")
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
            OCI_CLI,
            "--cli-rc-file",
            os.devnull,
            "--config-file",
            str(config_file),
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
        monkeypatch.setenv("OCI_MCP_AUTH_TYPE", "resource_principal")
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            await client.call_tool("run_oci_command", {"command": "compute instance list"})

        assert mock_run.call_args.args[0] == [
            OCI_CLI,
            "--cli-rc-file",
            os.devnull,
            "--config-file",
            str(config_file),
            "--profile",
            "SESSION",
            "compute",
            "instance",
            "list",
        ]

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_rejects_unclassifiable_auto_profile(
        self, mock_run, monkeypatch, tmp_path
    ):
        monkeypatch.delenv("OCI_MCP_AUTH_TYPE")
        monkeypatch.setenv("OCI_CONFIG_FILE", str(tmp_path / "missing_config"))
        monkeypatch.setenv("OCI_CONFIG_PROFILE", "MISSING")
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            result = (await client.call_tool("run_oci_command", {"command": "compute instance list"})).data

        assert "Unable to resolve OCI_MCP_AUTH_TYPE=auto" in result["error"]
        mock_run.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("auth_type", "cli_auth"),
        [
            ("api_key", "api_key"),
            ("security_token", "security_token"),
            ("instance_principal", "instance_principal"),
            ("resource_principal", "resource_principal"),
            ("oke_workload_identity", "oke_workload_identity"),
        ],
    )
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_maps_supported_mcp_auth_types(
        self, mock_run, monkeypatch, auth_type, cli_auth
    ):
        monkeypatch.setenv("OCI_MCP_AUTH_TYPE", auth_type)
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            await client.call_tool("run_oci_command", {"command": "compute instance list"})

        assert mock_run.call_args.args[0] == [
            OCI_CLI,
            "--cli-rc-file",
            os.devnull,
            "--config-file",
            DEFAULT_LOCATION,
            "--profile",
            "DEFAULT",
            "--auth",
            cli_auth,
            "compute",
            "instance",
            "list",
        ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth_type",
        [
            "identity_domain_upst",
            "instance_principal_delegation",
            "resource_principal_delegation",
        ],
    )
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_rejects_mcp_auth_types_without_cli_equivalents(
        self, mock_run, monkeypatch, auth_type
    ):
        monkeypatch.setenv("OCI_MCP_AUTH_TYPE", auth_type)

        async with Client(mcp) as client:
            result = (await client.call_tool("run_oci_command", {"command": "compute instance list"})).data

        assert f"OCI_MCP_AUTH_TYPE={auth_type!r}" in result["error"]
        mock_run.assert_not_called()

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_translates_oke_token_path_for_cli(self, mock_run, monkeypatch):
        monkeypatch.setenv("OCI_MCP_AUTH_TYPE", "oke_workload_identity")
        monkeypatch.setenv("OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN_PATH", "/var/run/secrets/token")
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            await client.call_tool("run_oci_command", {"command": "compute instance list"})

        assert (
            mock_run.call_args.kwargs["env"]["OCI_KUBERNETES_SERVICE_ACCOUNT_TOKEN_PATH"]
            == "/var/run/secrets/token"
        )

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_rejects_inline_oke_token(self, mock_run, monkeypatch):
        secret = "not-a-token"
        monkeypatch.setenv("OCI_MCP_AUTH_TYPE", "oke_workload_identity")
        monkeypatch.setenv("OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN", secret)

        async with Client(mcp) as client:
            result = (await client.call_tool("run_oci_command", {"command": "compute instance list"})).data

        assert "OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN is not supported" in result["error"]
        assert secret not in result["error"]
        mock_run.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "command",
        [
            "compute instance list --auth=api_key",
            "compute instance list --auth-purpose service-principal",
            "compute instance list --profile OTHER",
            "compute instance list --config-file=/tmp/config",
            "--cli-rc-file /tmp/other-rc compute instance list",
            "--defaults-file=/tmp/other-rc compute instance list",
            "compute instance list --endpoint https://example.invalid",
            "compute instance list --federation-endpoint https://example.invalid",
            "--proxy http://127.0.0.1:8080 compute instance list",
        ],
    )
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_rejects_server_managed_global_options(self, mock_run, command):
        async with Client(mcp) as client:
            result = (await client.call_tool("run_oci_command", {"command": command})).data

        assert result == {"error": "OCI command contains a server-managed global option"}
        mock_run.assert_not_called()

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
            cmd=[OCI_CLI, "--cli-rc-file", os.devnull] + command.split(),
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
    @pytest.mark.parametrize(
        "command",
        [
            "raw-request --http-method GET --target-uri https://169.254.169.254",
            "--debug raw-request --http-method=GET --target-uri=https://example.com",
            "--connection-timeout 5 raw-request --http-method GET --target-uri https://example.com",
            "--realm-specific-endpoint raw-request --http-method GET --target-uri https://example.com",
            "--opc-request-id request123 raw-request --http-method GET --target-uri https://example.com",
            "--enable-propagation True raw-request --http-method GET --target-uri https://example.com",
            "-d raw-request --http-method GET --target-uri https://example.com",
        ],
    )
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_denies_raw_request(self, mock_run, command):
        async with Client(mcp) as client:
            result = (await client.call_tool("run_oci_command", {"command": command})).data

        assert "error" in result
        assert "denied by denylist" in result["error"]
        mock_run.assert_not_called()

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_allows_denylisted_words_in_option_values(self, mock_run):
        command = "os object get --bucket-name raw-request --name safe --file /tmp/safe"
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            result = (await client.call_tool("run_oci_command", {"command": command})).data

        assert result["returncode"] == 0
        mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_disables_cli_aliases(self, mock_run):
        command = "rr --http-method GET --target-uri https://example.com"
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            result = (await client.call_tool("run_oci_command", {"command": command})).data

        assert result["returncode"] == 0
        assert mock_run.call_args.args[0] == [
            OCI_CLI,
            "--cli-rc-file",
            os.devnull,
            "--config-file",
            DEFAULT_LOCATION,
            "--profile",
            "DEFAULT",
            "--auth",
            "api_key",
            "rr",
            "--http-method",
            "GET",
            "--target-uri",
            "https://example.com",
        ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "command",
        [
            "-dd compute instance terminate --instance-id ocid1.instance.oc1..example",
            "compute -dd instance terminate --instance-id ocid1.instance.oc1..example",
            "compute instance -dd terminate --instance-id ocid1.instance.oc1..example",
        ],
    )
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_denies_clustered_short_flags(self, mock_run, command):
        async with Client(mcp) as client:
            result = (await client.call_tool("run_oci_command", {"command": command})).data

        assert "denied by denylist" in result["error"]
        mock_run.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "command",
        [
            "os object bulk-delete --namespace n --bucket-name b --force",
            "ocvs cluster delete --cluster-id ocid1.cluster.oc1..example --force",
            "generative-ai api-key delete --api-key-id ocid1.generativeaiapikey.oc1..example",
            "budgets budget budget update --budget-id ocid1.budget.oc1..example",
            (
                "mysql db-system controlled-update "
                "--db-system-id ocid1.mysqldbsystem.oc1..example"
            ),
            "session terminate",
        ],
    )
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_denies_canonical_destructive_actions(
        self, mock_run, command
    ):
        async with Client(mcp) as client:
            result = (await client.call_tool("run_oci_command", {"command": command})).data

        assert "denied by denylist" in result["error"]
        mock_run.assert_not_called()

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
                [OCI_CLI, "--cli-rc-file", os.devnull, "--help"],
                env=ANY,
                stdin=subprocess.DEVNULL,
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
            cmd=[OCI_CLI, "--cli-rc-file", os.devnull, "--help"],
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
            ("--connection-timeout 5 compute instance terminate --instance-id ocid1.instance.oc1..example", "compute instance terminate"),
            ("--realm-specific-endpoint compute instance terminate --instance-id ocid1.instance.oc1..example", "compute instance terminate"),
            ("--proxy http://127.0.0.1:8080 compute instance terminate", "compute instance terminate"),
            ("--opc-request-id request123 compute instance terminate", "compute instance terminate"),
            ("--enable-propagation=True compute instance terminate", "compute instance terminate"),
            ("-dd compute instance terminate --instance-id ocid1.instance.oc1..example", "compute instance terminate"),
            ("compute -dd instance terminate --instance-id ocid1.instance.oc1..example", "compute instance terminate"),
            ("compute instance -dd terminate --instance-id ocid1.instance.oc1..example", "compute instance terminate"),
            ("compute --proxy http://127.0.0.1:8080 instance terminate", "compute instance terminate"),
            ("compute instance --proxy http://127.0.0.1:8080 terminate", "compute instance terminate"),
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

    @pytest.mark.parametrize(
        "command",
        [
            "compute --proxy http://127.0.0.1:8080 instance terminate",
            "compute instance --proxy http://127.0.0.1:8080 terminate",
            "-dd compute instance terminate --instance-id ocid1.instance.oc1..example",
            "compute -dd instance terminate --instance-id ocid1.instance.oc1..example",
            "compute instance -dd terminate --instance-id ocid1.instance.oc1..example",
        ],
    )
    def test_denylist_blocks_commands_with_interspersed_global_options(self, command):
        denylist = Denylist(MagicMock())
        denylist.denylist = ["compute instance terminate"]

        assert denylist.isCommandInDenyList(command) is True

    def test_denylist_blocks_raw_request(self):
        denylist = Denylist(MagicMock())

        for command in (
            "raw-request --http-method GET --target-uri https://example.com",
            "--connection-timeout 5 raw-request --http-method GET --target-uri https://example.com",
            "--realm-specific-endpoint raw-request --http-method GET --target-uri https://example.com",
            "--federation-endpoint https://example.com raw-request --http-method GET --target-uri https://example.com",
            "--proxy http://127.0.0.1:8080 raw-request --http-method GET --target-uri https://example.com",
            "--opc-request-id request123 raw-request --http-method GET --target-uri https://example.com",
            "--auth-purpose service-principal raw-request --http-method GET --target-uri https://example.com",
            "--enable-propagation True raw-request --http-method GET --target-uri https://example.com",
            "-d raw-request --http-method GET --target-uri https://example.com",
        ):
            assert denylist.isCommandInDenyList(command) is True

    @pytest.mark.parametrize(
        "command",
        [
            "--future-global-option value raw-request --http-method GET",
            "--future-global-option=value raw-request --http-method GET",
            "-x raw-request --http-method GET",
            "--proxy",
        ],
    )
    def test_denylist_fails_closed_for_ambiguous_leading_options(self, command):
        denylist = Denylist(MagicMock())

        assert denylist.isCommandInDenyList(command) is True

    def test_denylist_global_options_match_oci_cli_metadata(self):
        cli_flags = {option for param in oci_cli.params if param.is_flag for option in param.opts}
        cli_options_with_values = {
            option for param in oci_cli.params if not param.is_flag for option in param.opts
        }

        assert Denylist._global_flags_without_values == cli_flags
        assert Denylist._global_options_with_values == cli_options_with_values

    def test_denylist_does_not_scan_option_values_as_command_words(self):
        denylist = Denylist(MagicMock())

        command = "os object get --bucket-name raw-request --name safe --file /tmp/safe"

        assert denylist.remove_params_from_command(command) == "os object get"
        assert denylist.isCommandInDenyList(command) is False


class TestDenylist:
    def test_missing_denylist_fails_closed(self, tmp_path):
        missing_denylist = tmp_path / "missing-denylist"

        with pytest.raises(RuntimeError, match="Denylist file not found"):
            Denylist(MagicMock(), str(missing_denylist))

    @pytest.mark.parametrize(
        "command",
        [
            "db cloud-vm-cluster get-update --update-id update-id",
            "db cloud-vm-cluster list-update-histories --cloud-vm-cluster-id cluster-id",
            "devops repository create-or-update-git-branch-details",
            "devops project cancel-cascading-delete --project-id project-id",
            (
                "db autonomous-database "
                "create-autonomous-database-undelete-autonomous-database-details"
            ),
        ],
    )
    def test_reviewed_denylist_excludes_read_cancel_and_create_commands(self, command):
        denylist = Denylist(MagicMock())

        assert denylist.isCommandInDenyList(command) is False

    @pytest.mark.parametrize(
        "command_path",
        [
            ("os", "object", "bulk-delete"),
            ("ocvs", "cluster", "delete"),
            ("generative-ai", "api-key", "delete"),
            ("budgets", "budget", "budget", "update"),
            ("mysql", "db-system", "controlled-update"),
            ("session", "terminate"),
        ],
    )
    def test_destructive_action_regressions_are_canonical_cli_paths(self, command_path):
        dynamic_loader.load_service(command_path[0])
        command = oci_cli

        for command_word in command_path:
            assert isinstance(command, click.Group)
            command = click.Group.get_command(command, None, command_word)
            assert command is not None

    @pytest.mark.parametrize(
        ("command", "expected"),
        [
            ("os object bulk-delete", True),
            ("data-safe alert alerts-update", True),
            ("identity-domains mapped-attribute patch", True),
            ("os object resume-put", True),
            ("service-catalog service-catalog-association bulk-replace", True),
            ("devops repository create-or-update-git-branch-details", False),
            ("db cloud-vm-cluster get-update", False),
            ("devops project cancel-cascading-delete", False),
            (
                "db autonomous-database "
                "create-autonomous-database-undelete-autonomous-database-details",
                False,
            ),
        ],
    )
    def test_denylist_generator_classifies_compound_actions(self, command, expected):
        assert DENYLIST_GENERATOR["is_denied_command"](command) is expected

    def test_denylist_generator_preserves_mandatory_commands(self):
        assert DENYLIST_GENERATOR["get_denied_commands"]([]) == ["raw-request"]

    def test_denylist_generator_does_not_follow_output_symlinks(self, tmp_path):
        target = tmp_path / "target"
        output = tmp_path / "denylist"
        target.write_text("keep me")
        try:
            output.symlink_to(target)
        except OSError:
            pytest.skip("Symbolic links are not available")

        DENYLIST_GENERATOR["write_file"](output, "replacement")

        assert target.read_text() == "keep me"
        assert output.read_text() == "replacement"
        assert not output.is_symlink()

    def test_packaged_denylist_matches_classified_cli_commands(self):
        expected = set(
            DENYLIST_GENERATOR["get_denied_commands"](
                DENYLIST_GENERATOR["get_canonical_commands"]()
            )
        )
        actual = set(Denylist(MagicMock()).denylist)
        missing = sorted(expected - actual)
        stale = sorted(actual - expected)

        assert not missing and not stale, (
            f"Missing denylist paths: {missing}; stale paths: {stale}"
        )


class TestServer:
    def test_oci_cli_uses_server_environment(self):
        assert Path(OCI_CLI).parent == Path(server.sys.executable).parent
        assert importlib.metadata.version("oci-cli") == server._OCI_CLI_VERSION
        assert f"oci-cli=={server._OCI_CLI_VERSION}" in importlib.metadata.requires(__project__)

    @patch("oracle.oci_api_mcp_server.server.importlib.metadata.version")
    @patch("oracle.oci_api_mcp_server.server.shutil.which")
    def test_resolve_oci_cli_success(self, mock_which, mock_version):
        mock_which.return_value = "/server-environment/bin/oci"
        mock_version.return_value = server._OCI_CLI_VERSION

        assert server._resolve_oci_cli() == "/server-environment/bin/oci"

    @patch("oracle.oci_api_mcp_server.server.importlib.metadata.version")
    @patch("oracle.oci_api_mcp_server.server.shutil.which", return_value=None)
    def test_resolve_oci_cli_fails_when_executable_is_missing(self, _, mock_version):
        with pytest.raises(RuntimeError, match="OCI CLI 3.89.3 is required"):
            server._resolve_oci_cli()

        mock_version.assert_not_called()

    @patch("oracle.oci_api_mcp_server.server.importlib.metadata.version", return_value="3.89.2")
    @patch("oracle.oci_api_mcp_server.server.shutil.which", return_value="/server/bin/oci")
    def test_resolve_oci_cli_fails_when_version_mismatches(self, *_):
        with pytest.raises(RuntimeError, match="OCI CLI 3.89.3 is required"):
            server._resolve_oci_cli()

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
