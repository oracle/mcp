"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from mcp.types import CallToolResult, TextContent

from ...config.consts import TOOL_GET_CONFIG_STATUS
from ...config.settings import env_var_catalog, get_config_diagnostics
from ...runtime.mcp_app import mcp


@mcp.tool(name=TOOL_GET_CONFIG_STATUS)
def get_config_status() -> CallToolResult:
    """Show non-secret MCP runtime configuration and env-var requirements.

    Call this when a Vision/Object Storage tool is missing profile, region,
    compartment, bucket, namespace, base directory, result path, or auth-related
    configuration. This reports resolved values, whether each value came from
    process environment or a default, missing required variables, validation
    errors, and the full env-var catalog. It succeeds even when configuration is
    incomplete, must not be used to retrieve secrets, and does not call OCI.
    """
    status = get_config_diagnostics()
    status["env_variables"] = env_var_catalog()
    values = status["values"]
    profile = values["profile"]["value"] or "not configured"
    region = values["region"]["value"] or "not configured"
    compartment = "configured" if values["default_compartment_id"]["value"] else "not configured"
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=(
                    "OCI Vision MCP config: "
                    f"profile={profile}, region={region}, default_compartment_id={compartment}."
                ),
            )
        ],
        structuredContent=status,
        isError=False,
    )
