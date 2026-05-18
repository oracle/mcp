"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[1]
    if not list(workspace_root.glob(".coverage.*")):
        print("No coverage files found; skipping coverage combine.")
        return 0

    env = os.environ.copy()
    env.setdefault("UV_CACHE_DIR", str(workspace_root / ".uv-cache"))
    env.setdefault("UV_ISOLATED", "1")

    coverage = coverage_command(workspace_root)
    for args in (
        ("combine",),
        ("html",),
        ("report", "--fail-under=69"),
    ):
        subprocess.run((*coverage, *args), cwd=workspace_root, env=env, check=True)

    return 0


def coverage_command(workspace_root: Path) -> tuple[str, ...]:
    # The repo has no root pyproject.toml, so reuse a package lock that already
    # carries coverage through pytest-cov.
    project_root = coverage_project(workspace_root)
    if project_root is not None:
        return ("uv", "run", "--project", str(project_root.relative_to(workspace_root)), "coverage")

    return ("uv", "run", "--with", "coverage", "coverage")


def coverage_project(workspace_root: Path) -> Path | None:
    for lock_path in sorted((workspace_root / "src").glob("*/uv.lock")):
        with lock_path.open("rb") as handle:
            lock = tomllib.load(handle)
        for package in lock.get("package", []):
            if package.get("name") == "coverage":
                return lock_path.parent

    return None


if __name__ == "__main__":
    sys.exit(main())
