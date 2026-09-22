"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import zipfile
from collections import Counter
from pathlib import Path

import pytest

PACKAGE_PATH = Path("oracle") / "oci_vision_mcp_server"


class WheelVerificationError(RuntimeError):
    """Raised when a wheel does not represent the current source tree."""


def verify_wheel_sources(wheel_path: Path, package_source: Path) -> None:
    """Require the wheel's Python modules to exactly match source modules."""
    expected = {
        f"{PACKAGE_PATH.as_posix()}/{path.relative_to(package_source).as_posix()}": path
        for path in package_source.rglob("*.py")
        if "tests" not in path.relative_to(package_source).parts
    }

    with zipfile.ZipFile(wheel_path) as archive:
        module_entries = [
            name
            for name in archive.namelist()
            if name.startswith(f"{PACKAGE_PATH.as_posix()}/") and name.endswith(".py")
        ]
        duplicates = sorted(
            name for name, count in Counter(module_entries).items() if count > 1
        )
        actual = set(module_entries)
        missing = sorted(set(expected) - actual)
        unexpected = sorted(actual - set(expected))
        changed = sorted(
            name
            for name in actual & set(expected)
            if archive.read(name) != expected[name].read_bytes()
        )

    problems: list[str] = []
    if missing:
        problems.append(f"missing modules: {missing}")
    if unexpected:
        problems.append(f"unexpected modules: {unexpected}")
    if duplicates:
        problems.append(f"duplicate modules: {duplicates}")
    if changed:
        problems.append(f"content differs from src: {changed}")
    if problems:
        raise WheelVerificationError("; ".join(problems))


def _write_wheel(path: Path, modules: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in modules.items():
            archive.writestr(name, content)


def test_wheel_source_verification_accepts_exact_module_set(tmp_path: Path) -> None:
    source = tmp_path / "oracle" / "oci_vision_mcp_server"
    (source / "tools").mkdir(parents=True)
    (source / "tests").mkdir(parents=True)
    (source / "__init__.py").write_bytes(b"# package\n")
    (source / "tools" / "demo.py").write_bytes(b"VALUE = 1\n")
    (source / "tests" / "test_demo.py").write_bytes(b"def test_demo(): pass\n")
    wheel = tmp_path / "package.whl"
    _write_wheel(
        wheel,
        {
            "oracle/oci_vision_mcp_server/__init__.py": b"# package\n",
            "oracle/oci_vision_mcp_server/tools/demo.py": b"VALUE = 1\n",
            "oci_vision_mcp_server-0.1.dist-info/METADATA": b"metadata",
        },
    )

    verify_wheel_sources(wheel, source)


@pytest.mark.parametrize(
    ("wheel_modules", "message"),
    [
            (
                {
                    "oracle/oci_vision_mcp_server/__init__.py": b"# package\n",
                    "oracle/oci_vision_mcp_server/stale.py": b"STALE = True\n",
                },
                "unexpected modules",
            ),
            ({"oracle/oci_vision_mcp_server/__init__.py": b"# changed\n"}, "content differs from src"),
        ],
)
def test_wheel_source_verification_rejects_stale_or_changed_modules(
    tmp_path: Path,
    wheel_modules: dict[str, bytes],
    message: str,
) -> None:
    source = tmp_path / "oracle" / "oci_vision_mcp_server"
    source.mkdir(parents=True)
    (source / "__init__.py").write_bytes(b"# package\n")
    wheel = tmp_path / "package.whl"
    _write_wheel(wheel, wheel_modules)

    with pytest.raises(WheelVerificationError, match=message):
        verify_wheel_sources(wheel, source)
