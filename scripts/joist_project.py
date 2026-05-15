"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Project-local helpers for Joist targets.")
    parser.add_argument("target", choices=("build", "containerize", "test"))
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    if not (project_root / "pyproject.toml").exists():
        parser.error(f"{project_root} does not contain pyproject.toml")

    if args.target == "build":
        update_project_init(project_root)
        return run(["uv", "build"], cwd=project_root)
    if args.target == "containerize":
        return containerize(project_root)
    if args.target == "test":
        return test(project_root)
    return 2


def test(project_root: Path) -> int:
    env = os.environ.copy()
    env["COVERAGE_FILE"] = str(REPO_ROOT / f".coverage.{project_root.name}")
    return run(
        [
            "uv",
            "run",
            "pytest",
            "--cov=.",
            "--cov-branch",
            "--cov-append",
            "--cov-report=html",
            "--cov-report=term-missing",
        ],
        cwd=project_root,
        env=env,
    )


def containerize(project_root: Path) -> int:
    containerfile = project_root / "Containerfile"
    if not containerfile.exists():
        print(f"Skipping {project_root.relative_to(REPO_ROOT)}: no Containerfile")
        return 0

    metadata = project_metadata(project_root)
    image = f"{metadata['name']}:{metadata['version']}"
    code = run(["podman", "build", "-t", image, "."], cwd=project_root)
    if code != 0:
        return code
    return run(["podman", "tag", image, f"{metadata['name']}:latest"], cwd=project_root)


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


def run(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> int:
    print(f"+ {' '.join(args)}", flush=True)
    completed = subprocess.run(args, cwd=cwd, env=env)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
