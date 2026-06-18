"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from fastmcp import FastMCP

from . import __project__


mcp = FastMCP(
    name=__project__,
    instructions=(
        "Use this server for OCI Database Management workflows. "
        "Mutating non-delete and non-drop tools are marked with MCP tool annotations and "
        "should only be used when the user explicitly intends the change."
    ),
)
