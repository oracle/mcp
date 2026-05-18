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
    parser = argparse.ArgumentParser(description="Project-local helper for Nx targets.")
    parser.add_argument("target", choices=("containerize", "stamp"))
    parser.add_argument("project_root", nargs="?", type=Path)
    args = parser.parse_args()

    if args.project_root is None:
        parser.error(f"{args.target} requires project_root")

    project_root = args.project_root.resolve()
    if not (project_root / "pyproject.toml").exists():
        parser.error(f"{project_root} does not contain pyproject.toml")

    if args.target == "containerize":
        return containerize(project_root)

    update_project_init(project_root)
    return 0


def containerize(project_root: Path) -> int:
    metadata = project_metadata(project_root)
    versioned_tag = f'{metadata["name"]}:{metadata["version"]}'
    latest_tag = f'{metadata["name"]}:latest'
    subprocess.run(("podman", "build", "-t", versioned_tag, "."), cwd=project_root, check=True)
    subprocess.run(("podman", "tag", versioned_tag, latest_tag), check=True)
    return 0


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


if __name__ == "__main__":
    sys.exit(main())
