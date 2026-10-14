"""Regression tests for the local Recovery installer helpers."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

INSTALLER_PATH = (
    Path(__file__).resolve().parents[3] / "scripts" / "install_oci_recovery_mcp.py"
)
INSTALLER_SPEC = importlib.util.spec_from_file_location(
    "oci_recovery_installer_under_test", INSTALLER_PATH
)
assert INSTALLER_SPEC is not None and INSTALLER_SPEC.loader is not None
installer = importlib.util.module_from_spec(INSTALLER_SPEC)
sys.modules[INSTALLER_SPEC.name] = installer
INSTALLER_SPEC.loader.exec_module(installer)


class InstallerHelperTests(unittest.TestCase):
    def test_custom_config_path_is_used_for_auth_and_client_configs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            custom_config = Path(temporary_directory) / "OCI config" / "config"
            expected_path = custom_config.resolve()

            for variable in ("OCI_CONFIG_FILE", "OCI_CLI_CONFIG_FILE"):
                with self.subTest(variable=variable):
                    with patch.dict(
                        installer.os.environ, {variable: str(custom_config)}, clear=True
                    ):
                        selected_path = installer._oci_config_path()
                        self.assertEqual(selected_path, expected_path)
                        with patch.object(
                            installer,
                            "_run",
                            return_value=SimpleNamespace(returncode=0),
                        ) as run_command:
                            with contextlib.redirect_stdout(io.StringIO()):
                                installer._authenticate(
                                    "/opt/oracle/oci", "OCI_RECOVERY", selected_path
                                )

                        self.assertEqual(
                            run_command.call_args.args[0],
                            [
                                "/opt/oracle/oci",
                                "session",
                                "authenticate",
                                "--profile-name",
                                "OCI_RECOVERY",
                                "--config-location",
                                str(expected_path),
                            ],
                        )
                        self.assertEqual(
                            run_command.call_args.kwargs["env"]["OCI_CLI_CONFIG_FILE"],
                            str(expected_path),
                        )
                        self.assertEqual(
                            installer._authentication_command(
                                "/opt/oracle/oci", "OCI_RECOVERY", selected_path
                            ),
                            run_command.call_args.args[0],
                        )

                        json_config, toml_config = installer._config_outputs(
                            Path("/opt/recovery-server"), "OCI_RECOVERY", selected_path
                        )
                        json_environment = json.loads(json_config)["mcpServers"][
                            "oci-recovery"
                        ]["env"]
                        toml_environment = tomllib.loads(toml_config)["mcp_servers"][
                            "oci_recovery"
                        ]["env"]
                        self.assertEqual(
                            json_environment["OCI_CONFIG_FILE"], str(expected_path)
                        )
                        self.assertEqual(
                            toml_environment["OCI_CONFIG_FILE"], str(expected_path)
                        )

    def test_powershell_refresh_command_quotes_executable_path_with_spaces(
        self,
    ) -> None:
        command = installer._authentication_command(
            r"C:\Users\Jane Doe\.local-rcv-mcp\.venv\Scripts\oci.exe",
            "Jane's profile",
            Path(r"C:\Users\Jane Doe\OCI Config\config"),
        )

        with patch.object(installer.os, "name", "nt"):
            rendered = installer._shell_command(command)

        self.assertEqual(
            rendered,
            "& 'C:\\Users\\Jane Doe\\.local-rcv-mcp\\.venv\\Scripts\\oci.exe' "
            "'session' 'authenticate' '--profile-name' 'Jane''s profile' "
            "'--config-location' 'C:\\Users\\Jane Doe\\OCI Config\\config'",
        )


if __name__ == "__main__":
    unittest.main()
