"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import tomllib
from pathlib import Path


def test_package_exposes_public_oracle_entrypoint() -> None:
    pyproject = Path(__file__).resolve().parents[3] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))

    scripts = data["project"]["scripts"]
    wheel_config = data["tool"]["hatch"]["build"]["targets"]["wheel"]

    assert data["project"]["name"] == "oracle.oci-vision-mcp-server"
    assert data["project"]["requires-python"] == ">=3.13"
    assert data["project"]["license"] == "UPL-1.0"
    assert data["project"]["license-files"] == ["LICENSE.txt"]
    assert "fastmcp==3.4.2" in data["project"]["dependencies"]
    assert "oci==2.179.0" in data["project"]["dependencies"]
    assert "pydantic==2.12.3" in data["project"]["dependencies"]
    assert "mcp>=1.27.0" in data["project"]["dependencies"]
    assert scripts["oracle.oci-vision-mcp-server"] == "oracle.oci_vision_mcp_server.server:main"
    assert "oci-vision-mcp-server" not in scripts
    assert "oci-vision-mcp-server-launcher" not in scripts
    assert "oci-vision-mcp-server-codex" not in scripts
    assert wheel_config["packages"] == ["oracle"]
    assert data["tool"]["coverage"]["report"]["fail_under"] == 90
