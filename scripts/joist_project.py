"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Project-local build helper for Joist targets.")
    parser.add_argument("target", choices=("build",))
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    if not (project_root / "pyproject.toml").exists():
        parser.error(f"{project_root} does not contain pyproject.toml")

    update_project_init(project_root)
    return run(["uv", "build"], cwd=project_root)


def update_project_init(project_root: Path) -> None:
    oracle_dir = project_root / "oracle"
    if not oracle_dir.exists():
        return

    metadata = project_metadata(project_root)
    init_content = (
        '"""\n'
        "Copyright (c) 2025, Oracle and/or its affiliates.\n"
        "Licensed under the Universal Permissive License v1.0 as shown at\n"
        "https://oss.oracle.com/licenses/upl.\n"
        '"""\n\n'
        f'__project__ = "{metadata["name"]}"\n'
        f'__version__ = "{metadata["version"]}"\n'
    )
    for package_dir in sorted(path for path in oracle_dir.glob("*_mcp_server") if path.is_dir()):
        (package_dir / "__init__.py").write_text(init_content, encoding="utf-8")


def project_metadata(project_root: Path) -> dict[str, str]:
    with (project_root / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]
    return {"name": project["name"], "version": project["version"]}


def run(args: list[str], cwd: Path) -> int:
    print(f"+ {' '.join(args)}", flush=True)
    completed = subprocess.run(args, cwd=cwd)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
