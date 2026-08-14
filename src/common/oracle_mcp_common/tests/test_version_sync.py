"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[4] / "scripts" / "sync_common_version.py"
SPEC = importlib.util.spec_from_file_location("sync_common_version", SCRIPT_PATH)
assert SPEC and SPEC.loader
sync_common_version = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_common_version)


def write_common_package(tmp_path: Path, init_content: str) -> Path:
    package_dir = tmp_path / "common"
    package_dir.mkdir()
    (package_dir / "pyproject.toml").write_text(
        '[project]\nname = "oracle-mcp-common"\nversion = "0.1.2"\n',
        encoding="utf-8",
    )
    init_file = package_dir / "oracle_mcp_common" / "__init__.py"
    init_file.parent.mkdir()
    init_file.write_text(init_content, encoding="utf-8")
    return package_dir


def test_synchronize_updates_only_the_version_declaration(tmp_path: Path) -> None:
    package_dir = write_common_package(
        tmp_path,
        'from .auth import AuthContext\n\n__all__ = ["AuthContext"]\n'
        '__project__ = "oracle_mcp_common"\n__version__ = "0.1.1"\n',
    )

    sync_common_version.synchronize(package_dir)

    assert (package_dir / "oracle_mcp_common" / "__init__.py").read_text(encoding="utf-8") == (
        'from .auth import AuthContext\n\n__all__ = ["AuthContext"]\n'
        '__project__ = "oracle_mcp_common"\n__version__ = "0.1.2"\n'
    )


@pytest.mark.parametrize(
    "init_content, expected_error",
    [
        ('__project__ = "oracle_mcp_common"\n', "found 0"),
        ('__version__ = "0.1.1"\n__version__ = "0.1.0"\n', "found 2"),
    ],
)
def test_synchronize_rejects_missing_or_ambiguous_versions(
    tmp_path: Path, init_content: str, expected_error: str
) -> None:
    package_dir = write_common_package(tmp_path, init_content)

    with pytest.raises(ValueError, match=expected_error):
        sync_common_version.synchronize(package_dir)


def test_check_rejects_a_drifted_version(tmp_path: Path) -> None:
    package_dir = write_common_package(tmp_path, '__version__ = "0.1.1"\n')

    with pytest.raises(ValueError, match="does not match"):
        sync_common_version.synchronize(package_dir, check=True)


def test_synchronize_rejects_a_missing_project_version(tmp_path: Path) -> None:
    package_dir = write_common_package(tmp_path, '__version__ = "0.1.1"\n')
    (package_dir / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must define project.version"):
        sync_common_version.synchronize(package_dir)
