"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import importlib.metadata
import json
import subprocess
from unittest.mock import ANY, MagicMock, patch
from urllib.error import HTTPError

import pytest
from fastmcp import Client

import oracle.oci_api_mcp_server.auth as auth
import oracle.oci_api_mcp_server.server as server
from oracle.oci_api_mcp_server import __project__
from oracle.oci_api_mcp_server.denylist import Denylist
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
    async def test_get_oci_command_help_preserves_quoted_arguments(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "Help output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_oci_command_help",
                    {
                        "command": 'compute instance list --display-name "Shared Services"'
                    },
                )
            ).structured_content["result"]

            assert result == "Help output"
            mock_run.assert_called_once_with(
                [
                    "oci",
                    "compute",
                    "instance",
                    "list",
                    "--display-name",
                    "Shared Services",
                    "--help",
                ],
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
    async def test_run_oci_command_preserves_quoted_arguments(self, mock_run):
        command = 'compute instance list --display-name "Shared Services"'

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
            mock_run.assert_called_once_with(
                [
                    "oci",
                    "--profile",
                    "DEFAULT",
                    "--auth",
                    "security_token",
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
    @patch("oracle.oci_api_mcp_server.server.get_upst_cli_configuration")
    @patch(
        "oracle.oci_api_mcp_server.server.is_upst_auth_configured", return_value=True
    )
    @patch("oracle.oci_api_mcp_server.server.subprocess.run")
    async def test_run_oci_command_uses_upst_profile(
        self, mock_run, mock_is_upst_auth_configured, mock_get_upst_cli_configuration
    ):
        mock_get_upst_cli_configuration.return_value = ("/private/upst/config", "UPST")
        mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "run_oci_command", {"command": "iam region list"}
                )
            ).data

        assert result["output"] == {}
        mock_is_upst_auth_configured.assert_called_once_with()
        mock_get_upst_cli_configuration.assert_called_once_with()
        assert mock_run.call_args.args[0][:7] == [
            "oci",
            "--config-file",
            "/private/upst/config",
            "--profile",
            "UPST",
            "--auth",
            "security_token",
        ]

    @pytest.mark.asyncio
    @patch("oracle.oci_api_mcp_server.server.get_upst_cli_configuration")
    @patch(
        "oracle.oci_api_mcp_server.server.is_upst_auth_configured", return_value=True
    )
    async def test_run_oci_command_returns_upst_error(
        self, mock_is_upst_auth_configured, mock_get_upst_cli_configuration
    ):
        mock_get_upst_cli_configuration.side_effect = auth.UpstAuthenticationError(
            "token exchange failed"
        )

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "run_oci_command", {"command": "iam region list"}
                )
            ).data

        assert result["error"] == "token exchange failed"
        assert result["returncode"] == 1

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

    @pytest.mark.parametrize(
        ("command", "normalized"),
        [
            (
                "compute instance terminate --instance-id ocid1.instance.oc1..example",
                "compute instance terminate",
            ),
            (
                "--debug compute instance terminate --instance-id ocid1.instance.oc1..example",
                "compute instance terminate",
            ),
            (
                "--raw-output compute instance terminate --instance-id ocid1.instance.oc1..example",
                "compute instance terminate",
            ),
            (
                "--no-retry compute instance terminate --instance-id ocid1.instance.oc1..example",
                "compute instance terminate",
            ),
            (
                "--config-file /tmp/config compute instance terminate --instance-id ocid1.instance.oc1..example",
                "compute instance terminate",
            ),
        ],
    )
    def test_denylist_preserves_command_words_after_global_options(
        self, command, normalized
    ):
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
    def test_denylist_blocks_destructive_commands_after_valueless_global_options(
        self, command
    ):
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
        mock_getenv.side_effect = lambda x: {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }.get(x)

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


class TestUpstAuthentication:
    @pytest.fixture(autouse=True)
    def reset_upst_session(self):
        auth._temporary_directory = None
        auth._upst_session = None
        yield
        auth._temporary_directory = None
        auth._upst_session = None

    @staticmethod
    def environment(tmp_path):
        return {
            "OCI_UPST_DOMAIN_URL": "https://identity.example.com",
            "OCI_UPST_CLIENT_ID": "client",
            "OCI_UPST_CLIENT_SECRET": "secret",
            "OCI_UPST_REGION": "ap-mumbai-1",
            "OCI_UPST_CREDENTIALS_DIR": str(tmp_path / "credentials"),
        }

    def test_configuration_requires_all_required_environment_variables(self):
        with pytest.raises(auth.UpstAuthenticationError, match="OCI_UPST_CLIENT_ID"):
            auth.get_upst_cli_configuration(
                {"OCI_UPST_DOMAIN_URL": "https://identity.example.com"}
            )

    @pytest.mark.parametrize(
        "domain_url",
        ["http://identity.example.com", "https://identity.example.com?x=1"],
    )
    def test_configuration_requires_clean_https_domain_url(self, domain_url, tmp_path):
        environment = self.environment(tmp_path)
        environment["OCI_UPST_DOMAIN_URL"] = domain_url
        with pytest.raises(auth.UpstAuthenticationError, match="HTTPS identity domain"):
            auth.get_upst_cli_configuration(environment)

    @patch("oracle.oci_api_mcp_server.auth._post_token_request")
    def test_creates_private_files_and_reuses_upst_during_session(
        self, mock_post, tmp_path
    ):
        environment = self.environment(tmp_path)
        mock_post.side_effect = [
            {"access_token": "header.payload.signature"},
            {"token": "upst-token"},
        ]

        first_configuration = auth.get_upst_cli_configuration(environment)
        second_configuration = auth.get_upst_cli_configuration(environment)

        credentials_directory = tmp_path / "credentials"
        assert first_configuration == second_configuration
        assert mock_post.call_count == 2
        assert (credentials_directory / "token").read_text() == "upst-token"
        assert (credentials_directory / "private_key.pem").stat().st_mode & 0o077 == 0
        assert (credentials_directory / "config").stat().st_mode & 0o077 == 0

    @patch("oracle.oci_api_mcp_server.auth._post_token_request")
    @patch("oracle.oci_api_mcp_server.auth.time.time", return_value=1000)
    def test_renews_expiring_upst(self, mock_time, mock_post, tmp_path):
        environment = self.environment(tmp_path)
        mock_post.side_effect = [
            {"access_token": "header.payload.signature"},
            {"token": self._jwt(1050)},
            {"access_token": "header.payload.signature"},
            {"token": self._jwt(2000)},
        ]

        auth.get_upst_cli_configuration(environment)
        auth.get_upst_cli_configuration(environment)

        assert mock_post.call_count == 4

    @staticmethod
    def _jwt(expiration):
        payload = json.dumps({"exp": expiration}).encode()
        return (
            "header."
            + __import__("base64").urlsafe_b64encode(payload).decode().rstrip("=")
            + ".signature"
        )

    def test_private_key_rejects_unsafe_permissions_and_invalid_content(self, tmp_path):
        private_key_file = tmp_path / "key.pem"
        private_key_file.write_text("not a key")
        private_key_file.chmod(0o600)
        with pytest.raises(auth.UpstAuthenticationError, match="Failed to load"):
            auth._load_or_create_private_key(private_key_file)

        private_key_file.chmod(0o644)
        with pytest.raises(
            auth.UpstAuthenticationError, match="must not be group or world"
        ):
            auth._load_or_create_private_key(private_key_file)

    def test_expiration_parser_handles_jwt_and_opaque_tokens(self):
        assert auth._get_jwt_expiration(self._jwt(1234)) == 1234
        assert auth._get_jwt_expiration("opaque-token") is None
        assert auth._get_jwt_expiration("a.bad.c") is None

    @patch("oracle.oci_api_mcp_server.auth.urlopen")
    def test_post_token_request_uses_basic_auth_and_form_encoding(
        self, mock_urlopen, tmp_path
    ):
        response = MagicMock()
        response.read.return_value = b'{"token": "upst"}'
        mock_urlopen.return_value.__enter__.return_value = response

        result = auth._post_token_request(
            self.environment(tmp_path), {"grant_type": "client_credentials"}
        )

        assert result == {"token": "upst"}
        request = mock_urlopen.call_args.args[0]
        assert request.full_url == "https://identity.example.com/oauth2/v1/token"
        assert request.data == b"grant_type=client_credentials"
        assert request.headers["Authorization"].startswith("Basic ")

    @patch("oracle.oci_api_mcp_server.auth.urlopen")
    def test_post_token_request_hides_http_error_body(self, mock_urlopen, tmp_path):
        mock_urlopen.side_effect = HTTPError(
            "https://identity.example.com", 401, "Unauthorized", {}, None
        )
        with pytest.raises(auth.UpstAuthenticationError, match="HTTP 401"):
            auth._post_token_request(
                self.environment(tmp_path), {"grant_type": "client_credentials"}
            )
