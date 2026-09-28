# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from pathlib import Path


def test_container_defaults_to_safe_stdio_configuration() -> None:
    containerfile = Path(__file__).parents[4] / "Containerfile"
    content = containerfile.read_text(encoding="utf-8")
    assert "LANGUAGE_MCP_TRANSPORT=stdio" in content
    assert "LANGUAGE_MCP_HOST=127.0.0.1" in content
    assert "LANGUAGE_MCP_HEALTHCHECK_HOST" in content
    assert "uv --no-cache sync --no-sources --no-dev --no-editable" in content


def test_documented_container_workflow_uses_podman() -> None:
    readme = Path(__file__).parents[4] / "README.md"
    content = readme.read_text(encoding="utf-8")
    assert "Python 3.13 or Podman" in content
    assert "SUBDIRS=src/oci-language-mcp-server make containerize" in content
    assert "podman run" in content
