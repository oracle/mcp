"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from typing import Any
from fastmcp import FastMCP
from pydantic import Field
from .registry import compartment_requirements, load_registry, to_jsonable
from .runtime import invoke_registered_tool

registry = load_registry()

mcp = FastMCP(
    name="oracle.oci-db-observability-mcp-server",
    instructions="For a compartment-scoped operation, first use `oci-identity-mcp-server` to resolve or list the compartment and obtain a real compartment OCID. "
                 "Pass that OCID as the compartment_id argument to Database Observability operations; do not invent one. "
                 "Use `list_dbo_skills` and `list_dbo_tools` when the relevant capability or operation is not already known. "
                 "Use `describe_dbo_tool` to inspect or confirm a tool's exact contract when its schema is unavailable, "
                 "outdated, or uncertain. Reuse information from earlier discovery calls when it remains applicable, then "
                 "call `invoke_dbo_tool` with arguments that match the known input schema exactly."
)

@mcp.tool(
    description="Entry point for Oracle Database Observability capability discovery. Returns a compact list of available "
        "skills with short summaries only; does not return operation schemas. Use it when the relevant capability "
                "is not already known, and reuse prior results when they remain applicable."
)
def list_dbo_skills() -> dict[str, Any]:
    return {"skills": [{"name": s["name"], "description": s["description"], "toolCount": len(s["tools"])} for s in registry.skills]}

@mcp.tool(
    description="Discovery endpoint for Oracle Database Observability operations within selected skills. Use it to list "
                "candidate operations when the required operation is not already known. Reuse prior results when they "
                "remain applicable, and use `describe_dbo_tool` to inspect or confirm a schema when needed before "
                "calling `invoke_dbo_tool`."
)
def list_dbo_tools(
    skill_names: list[str] = Field(
        ...,
        min_length=1,
        description="Required skill names returned by list_dbo_skills. Only tools belonging to these skills are listed.",
    ),
    limit: int = Field(50, ge=1, le=100, description="Maximum compact tool entries to return."),
) -> dict[str, Any]:
    selected = set(skill_names)
    tools = registry.list_tools(selected)
    return {
        "count": len(tools),
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "skills": list(tool["skills"]),
                "mutable": tool["mutable"],
                "compartmentRequirements": compartment_requirements(tool),
            }
            for tool in tools[:limit]
        ],
        "truncated": len(tools) > limit,
    }

@mcp.tool(
    description="Retrieve the complete invocation contract for one Oracle Database Observability tool selected from "
                "`list_dbo_tools`. Returns the exact JSON input schema, required fields, and mutability metadata. "
                "Call it when the schema is unavailable, outdated, or uncertain; a previously retrieved applicable "
                "schema may be reused."
)
def describe_dbo_tool(
    tool_name: str = Field(..., description="Required logical tool name returned by list_dbo_tools, for example list_database_insights."),
) -> dict[str, Any]:
    tool = registry.get_tool(tool_name)
    return {
        "name": tool["name"],
        "description": tool["description"],
        "inputSchema": to_jsonable(tool["inputSchema"]),
        "mutable": tool["mutable"],
        "compartmentRequirements": compartment_requirements(tool),
        "guidance": "Pass an arguments object that exactly matches inputSchema.",
    }

@mcp.tool(
    description="Invoke one registered Oracle Database Observability operation. The supplied arguments object must "
                "conform exactly to the selected tool's known `inputSchema`. For an operation with compartment "
                "requirements, provide a real compartment OCID. Use `oci-identity-mcp-server` to resolve a "
                "user-provided compartment name; do not invent an OCID. Use `describe_dbo_tool` first when that schema is "
                "unavailable, outdated, or uncertain. This is the sole endpoint that executes catalog "
                "operations."
)
def invoke_dbo_tool(
    tool_name: str = Field(..., description="Required logical tool name returned by list_dbo_tools or otherwise known."),
    arguments: dict[str, Any] = Field(default_factory=dict, description="Required JSON object of SDK arguments matching the exact known inputSchema."),
) -> Any:
    return invoke_registered_tool(registry.get_tool(tool_name), arguments)
