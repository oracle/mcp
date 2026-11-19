# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.
"""Safety boundaries for the opt-in, wheel-based Common integration check."""

import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/check-common-consumer.py"


class CommonConsumerCheckTests(unittest.TestCase):
    def load_checker(self):
        self.assertTrue(SCRIPT.is_file(), "the opt-in checker must exist")
        spec = importlib.util.spec_from_file_location("check_common_consumer", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_invalid_consumer_is_rejected_before_running_commands(self):
        checker = self.load_checker()
        with patch.object(checker.subprocess, "run") as run:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                checker.main(["../common"])
        run.assert_not_called()

    def test_invalid_common_source_is_rejected_before_build(self):
        checker = self.load_checker()
        with tempfile.TemporaryDirectory() as source:
            Path(source, "pyproject.toml").write_text('[project]\nname="unrelated"\nversion="1"\n')
            with patch.object(checker.subprocess, "run") as run:
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    checker.main(["oci-cloud-mcp-server", "--common-source", source])
            run.assert_not_called()

    def exercise_run(self, fail_install=False):
        checker = self.load_checker()
        calls = []

        def run(command, *, cwd, env, check):
            self.assertTrue(check)
            calls.append((command, Path(cwd), dict(env)))
            if command[1] == "build":
                output = Path(command[command.index("--out-dir") + 1])
                output.mkdir(parents=True, exist_ok=True)
                Path(output, "artifact-1-py3-none-any.whl").touch()
            if command[1:3] == ["pip", "install"] and fail_install:
                raise subprocess.CalledProcessError(1, command)
            return subprocess.CompletedProcess(command, 0)

        with patch.object(checker.subprocess, "run", side_effect=run):
            with (
                patch.dict(
                    "os.environ",
                    {
                        "PYTHONPATH": "/untrusted",
                        "PYTEST_ADDOPTS": "--no-cov",
                        "UV_OVERRIDE": "/untrusted/overrides.txt",
                        "UV_EXCLUDE": "oracle-mcp-common",
                        "ORACLE_MCP_LOG_FILE": "/outside/consumer.log",
                        "ORACLE_MCP_STATE_DIR": "/outside/state",
                        "ORACLE_MCP_INSTALLATION_ID_FILE": "/outside/installation-id",
                    },
                    clear=True,
                ),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                result = checker.main(["oci-cloud-mcp-server"])
        self.assertTrue(calls)
        for _, cwd, env in calls:
            self.assertFalse(cwd.exists(), "temporary outputs must be removed after the check")
            for name in (
                "PYTHONPATH",
                "PYTEST_ADDOPTS",
                "UV_OVERRIDE",
                "UV_EXCLUDE",
                "ORACLE_MCP_LOG_FILE",
                "ORACLE_MCP_INSTALLATION_ID_FILE",
            ):
                self.assertTrue(name not in env, f"{name} must be removed")
        return result, calls

    def test_resolution_failure_is_nonzero_and_cleans_temporary_outputs(self):
        result, calls = self.exercise_run(fail_install=True)
        self.assertNotEqual(result, 0)
        self.assertFalse(any(cmd[0].endswith("/bin/python") for cmd, _, _ in calls))

    def test_success_installs_both_wheels_with_dependencies_and_runs_isolated_tests(self):
        result, calls = self.exercise_run()
        self.assertEqual(result, 0)
        install = next(cmd for cmd, _, _ in calls if cmd[1:3] == ["pip", "install"])
        self.assertEqual(sum(arg.endswith(".whl") for arg in install), 2)
        self.assertIn("--group", install)
        self.assertFalse({"--no-deps", "--override", "--overrides"}.intersection(install))
        self.assertTrue(any(cmd[1:3] == ["pip", "check"] for cmd, _, _ in calls))
        runner, _, env = calls[-1]
        self.assertIn("-I", runner)
        self.assertIn("-c", runner)
        self.assertTrue(env["COVERAGE_FILE"].startswith(str(calls[-1][1])))
        self.assertTrue(env["ORACLE_MCP_LOG_DIR"].startswith(str(calls[-1][1])))
        self.assertTrue(env["ORACLE_MCP_STATE_DIR"].startswith(str(calls[-1][1])))

    def test_runner_exposes_source_test_helpers_without_exposing_source_runtime(self):
        checker = self.load_checker()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            installed = root / "venv"
            installed.mkdir()
            tests = root / "source/tests"
            tests.mkdir(parents=True)
            (tests / "helper.py").write_text("value = 42\n")
            package = types.ModuleType("oracle.oci_cloud_mcp_server")
            package.__file__ = str(installed / "consumer/__init__.py")
            package.__path__ = [str(installed / "consumer")]
            package.__version__ = "2.3.1"
            common = types.ModuleType("oracle_mcp_common")
            common.__file__ = str(installed / "common/__init__.py")
            common.__version__ = "0.2.0"
            settings = {
                "module": "oracle.oci_cloud_mcp_server",
                "distribution": "consumer",
                "common_version": "0.2.0",
                "consumer_version": "2.3.1",
                "manifest": str(root / "pyproject.toml"),
                "tests": str(tests),
            }
            import json

            modules = {package.__name__: package, common.__name__: common}
            pytest = types.ModuleType("pytest")

            def run_pytest(arguments):
                import importlib

                helper = importlib.import_module("oracle.oci_cloud_mcp_server.tests.helper")
                self.assertEqual(helper.value, 42)
                self.assertEqual(package.__path__, [str(installed / "consumer")])
                self.assertIn("--cov-config=" + settings["manifest"], arguments)
                self.assertIn("--cov-branch", arguments)
                return 0

            pytest.main = run_pytest
            modules["pytest"] = pytest
            with patch.dict(sys.modules, modules), patch.object(sys, "prefix", str(installed)):
                with patch.object(sys, "argv", ["runner", json.dumps(settings)]):
                    with patch(
                        "importlib.metadata.version",
                        side_effect=lambda name: "0.2.0" if name == "oracle-mcp-common" else "2.3.1",
                    ):
                        with (
                            contextlib.redirect_stdout(io.StringIO()),
                            self.assertRaises(SystemExit) as result,
                        ):
                            exec(checker.RUN_TESTS, {})
            self.assertEqual(result.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
