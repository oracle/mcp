#!/usr/bin/env bash
# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
matrix_dir=$(mktemp -d "${TMPDIR:-/tmp}/common-fastmcp.XXXXXX")
trap 'rm -rf "$matrix_dir"' EXIT

# Build once, then install the artifact without local workspace sources or overrides.
uv build --project "$repo_root/src/common" --out-dir "$matrix_dir/dist"
cp "$repo_root/src/common/pyproject.toml" "$matrix_dir/pyproject.toml"
cp -R "$repo_root/src/common/oracle_mcp_common/tests" "$matrix_dir/tests"
unset PYTHONPATH
for endpoint in 4.0.0 4.1.6; do
    for oci_endpoint in minimum current; do
        env_dir="$matrix_dir/fastmcp-$endpoint-oci-$oci_endpoint"
        oci_requirement='oci>=2.185.0'
        if [ "$oci_endpoint" = minimum ]; then
            oci_requirement='oci==2.185.0'
        fi
        uv venv --python 3.13 "$env_dir"
        uv pip install --python "$env_dir/bin/python" \
            "$matrix_dir"/dist/*.whl "fastmcp==$endpoint" "$oci_requirement" \
            --group "$repo_root/src/common/pyproject.toml:dev"
        uv pip check --python "$env_dir/bin/python"
        (
            cd "$matrix_dir"
            "$env_dir/bin/python" - "$endpoint" "$oci_endpoint" <<'PYCODE'
import sys
import tomllib
from importlib.metadata import requires, version
from pathlib import Path

import oracle_mcp_common
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

manifest = tomllib.loads(Path("pyproject.toml").read_text())
assert version("oracle-mcp-common") == manifest["project"]["version"]
assert oracle_mcp_common.__version__ == manifest["project"]["version"]
assert version("fastmcp") == sys.argv[1]
if sys.argv[2] == "minimum":
    assert version("oci") == "2.185.0"
assert Path(oracle_mcp_common.__file__).is_relative_to(Path(sys.prefix))
requirements = {Requirement(r).name: Requirement(r).specifier for r in requires("oracle-mcp-common")}
assert requirements["fastmcp"] == SpecifierSet(">=4.0.0,<5.0.0")
assert requirements["oci"] == SpecifierSet(">=2.185.0")
for name in ("oracle-mcp-common", "fastmcp", "mcp", "oci"):
    print(f"{name}=={version(name)}", flush=True)
PYCODE
            COVERAGE_FILE="$env_dir/.coverage" "$env_dir/bin/python" -m pytest tests \
                --cov=oracle_mcp_common --cov-branch --cov-report=term-missing
        )
    done
done
