#!/usr/bin/env python3
# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.
"""Opt in to testing a consumer wheel against a local Common wheel.

Published dependency constraints still apply. An incompatible local Common is
expected to fail resolution; use --common-source with a compatible checkout to
test that release line. Builds, environment and coverage live in a temporary
directory. No manifests, locks or normal project environments are changed.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib


CONSUMERS = (
    "oci-api-mcp-server",
    "oci-cloud-mcp-server",
    "oci-database-mcp-server",
    "oci-db-observability-mcp-server",
    "oci-document-understanding-mcp-server",
    "oci-recovery-mcp-server",
)
REPO_ROOT = Path(__file__).resolve().parents[1]

# Executed with the isolated environment's Python, from a neutral directory.
# Preloading only the metadata-only package initializer pins its __path__ to
# site-packages before pytest adds the original test directories to sys.path.
RUN_TESTS = r"""
import importlib
from importlib.machinery import ModuleSpec
from importlib.metadata import version
import json
from pathlib import Path
import sys
import types

settings = json.loads(sys.argv[1])
prefix = Path(sys.prefix).resolve()
for module_name, distribution, expected in (
    ("oracle_mcp_common", "oracle-mcp-common", settings["common_version"]),
    (settings["module"], settings["distribution"], settings["consumer_version"]),
):
    module = importlib.import_module(module_name)
    location = Path(module.__file__).resolve()
    if not location.is_relative_to(prefix):
        raise RuntimeError(f"{module_name} imported outside isolated environment: {location}")
    if version(distribution) != expected or module.__version__ != expected:
        raise RuntimeError(f"{distribution} version differs from selected source {expected}")
    print(f"{distribution}=={expected}: {location}", flush=True)

# Some suites import helpers as oracle.<consumer>.tests.<helper>. Expose only
# that test subtree; adding its parent to the installed package's search path
# would let source implementation files replace the artifact under test.
test_name = settings["module"] + ".tests"
test_package = types.ModuleType(test_name)
test_package.__path__ = [settings["tests"]]
test_package.__package__ = test_name
test_package.__spec__ = ModuleSpec(test_name, loader=None, is_package=True)
sys.modules[test_name] = test_package

import pytest

raise SystemExit(pytest.main([
    settings["tests"],
    "-c", settings["manifest"],
    "-p", "no:cacheprovider",
    "--cov=" + settings["module"],
    "--cov-config=" + settings["manifest"],
    "--cov-branch",
    "--cov-report=term-missing",
]))
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("consumer", choices=CONSUMERS)
    parser.add_argument(
        "--common-source",
        type=Path,
        default=REPO_ROOT / "src/common",
        help="Common project directory, including pyproject.toml (default: src/common)",
    )
    args = parser.parse_args(argv)
    consumer = REPO_ROOT / "src" / args.consumer
    common = args.common_source.resolve()
    try:
        with (common / "pyproject.toml").open("rb") as source:
            common_project = tomllib.load(source)["project"]
        if common_project["name"] != "oracle-mcp-common":
            parser.error("--common-source must identify the oracle-mcp-common project")
        with (consumer / "pyproject.toml").open("rb") as source:
            consumer_project = tomllib.load(source)["project"]
        settings = {
            "common_version": common_project["version"],
            "consumer_version": consumer_project["version"],
            "distribution": consumer_project["name"],
            "module": "oracle." + args.consumer.replace("-", "_"),
            "manifest": str(consumer / "pyproject.toml"),
            "tests": str(consumer / "oracle" / args.consumer.replace("-", "_") / "tests"),
        }
    except (OSError, KeyError, tomllib.TOMLDecodeError) as error:
        parser.error(f"cannot read Common/consumer project metadata: {error}")

    env = dict(os.environ)
    # Inherited interpreter/test options must not substitute workspace imports
    # or silently disable coverage in the isolated artifact check.
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "COVERAGE_PROCESS_START",
        "UV_NO_DEPS",
        "UV_OVERRIDE",
        "UV_EXCLUDE",
        "ORACLE_MCP_LOG_FILE",
        "ORACLE_MCP_INSTALLATION_ID_FILE",
    ):
        env.pop(name, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        with tempfile.TemporaryDirectory(prefix="common-consumer-") as temporary:
            work = Path(temporary)
            env["COVERAGE_FILE"] = str(work / ".coverage")
            env["ORACLE_MCP_LOG_DIR"] = str(work / "logs")
            env["ORACLE_MCP_STATE_DIR"] = str(work / "state")

            def run(command):
                label = (
                    "isolated wheel verification and consumer pytest"
                    if "-c" in command
                    else " ".join(map(str, command))
                )
                print("+ " + label, flush=True)
                subprocess.run(list(map(str, command)), cwd=work, env=env, check=True)

            wheels = []
            for label, project in (("common", common), ("consumer", consumer)):
                output = work / label
                run(["uv", "build", "--no-sources", "--wheel", "--project", project, "--out-dir", output])
                built = list(output.glob("*.whl"))
                if len(built) != 1:
                    raise RuntimeError(f"expected one {label} wheel, found {len(built)}")
                wheels.append(built[0])
            environment = work / "venv"
            run(["uv", "venv", "--python", "3.13", environment])
            python = environment / "bin/python"
            run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--python",
                    python,
                    *wheels,
                    "--group",
                    str(consumer / "pyproject.toml") + ":dev",
                ]
            )
            run(["uv", "pip", "check", "--python", python])
            run([python, "-I", "-c", RUN_TESTS, json.dumps(settings)])
    except subprocess.CalledProcessError as error:
        print(f"Common consumer check failed (exit {error.returncode}).", file=sys.stderr)
        return error.returncode if error.returncode > 0 else 1
    except (OSError, RuntimeError) as error:
        print(f"Common consumer check failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
