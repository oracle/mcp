"""Keep oracle-mcp-common runtime version metadata aligned with pyproject.toml.

Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path


VERSION_PATTERN = re.compile(r'^__version__ = "[^"]*"$', re.MULTILINE)


def project_version(package_dir: Path) -> str:
    with (package_dir / "pyproject.toml").open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)
    try:
        version = pyproject["project"]["version"]
    except KeyError as error:
        raise ValueError("pyproject.toml must define project.version") from error
    if not isinstance(version, str) or not version:
        raise ValueError("pyproject.toml must define a non-empty project.version")
    return version


def synchronize(package_dir: Path, *, check: bool = False) -> None:
    init_file = package_dir / "oracle_mcp_common" / "__init__.py"
    content = init_file.read_text(encoding="utf-8")
    version = project_version(package_dir)
    updated, replacements = VERSION_PATTERN.subn(f'__version__ = "{version}"', content)
    if replacements != 1:
        raise ValueError(
            f"{init_file} must contain exactly one __version__ declaration; found {replacements}"
        )
    if check and updated != content:
        raise ValueError(f"{init_file} does not match pyproject.toml project.version {version}")
    if not check:
        with init_file.open("w", encoding="utf-8", newline="") as init_file_handle:
            init_file_handle.write(updated)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        synchronize(args.package_dir, check=args.check)
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
