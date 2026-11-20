"""Smoke tests for metadata-only OCI Identity Policy MCP wrapper."""

from importlib.metadata import version


def test_upstream_entrypoint_importable() -> None:
    """Ensure upstream MCP server entrypoint is importable from dependency package."""
    from oci_policy_analysis import mcp_server

    assert hasattr(mcp_server, "main")


def test_released_upstream_package_version() -> None:
    """Require the released upstream version used by this wrapper."""
    assert tuple(map(int, version("oci-policy-analysis").split(".")[:3])) >= (6, 5, 1)
