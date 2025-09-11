import asyncio
import json
from typing import Any, Dict, List, Set

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import set_defaults as set_defaults_fn, defaults_as_dict
from .jira import tools as jira_tools
from .confluence import tools as conf_tools
from .resources.registry import register_schemes


server = Server("atlassian")


def _set_defaults_tool() -> Tool:
    return Tool(
        name="set_defaults",
        description="Set or view runtime defaults for preferred user, Jira project, and Confluence space. Returns current defaults.",
        inputSchema={
            "type": "object",
            "properties": {
                "preferredUser": {"type": "string"},
                "jiraProject": {"type": "string"},
                "confSpace": {"type": "string"},
                "outputFormat": {"type": "string", "enum": ["markdown", "json", "storage"]},
                "show": {"type": "boolean"}
            },
        },
    )


@server.list_tools()
async def list_tools() -> List[Tool]:
    tools: List[Tool] = []
    tools.extend(jira_tools.list_tools())
    tools.extend(conf_tools.list_tools())
    tools.append(_set_defaults_tool())
    return tools


_JIRA_TOOL_NAMES: Set[str] = jira_tools.names()
_CONF_TOOL_NAMES: Set[str] = conf_tools.names()


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if name in _JIRA_TOOL_NAMES:
            return await jira_tools.handle_tool(name, arguments)

        if name in _CONF_TOOL_NAMES:
            return await conf_tools.handle_tool(name, arguments)

        if name == "set_defaults":
            # If show=true, don't change; simply return current defaults.
            show = bool(arguments.get("show", False))
            if not show:
                preferred_user = arguments.get("preferredUser")
                jira_project = arguments.get("jiraProject")
                conf_space = arguments.get("confSpace")
                output_format = arguments.get("outputFormat")
                set_defaults_fn(
                    preferred_user=str(preferred_user) if preferred_user is not None else None,
                    jira_project=str(jira_project) if jira_project is not None else None,
                    conf_space=str(conf_space) if conf_space is not None else None,
                    output_format=str(output_format) if output_format is not None else None,
                )
            return [TextContent(type="text", text=json.dumps(defaults_as_dict(), indent=2))]

        raise RuntimeError(f"Unknown tool: {name}")
    except Exception as e:
        raise RuntimeError(str(e))


async def amain():
    # Enable resource URI providers (jira://, confluence://)
    try:
        register_schemes(server)
    except Exception:
        # Do not fail server if resources cannot be registered
        pass
    async with stdio_server() as (read, write):
        await server.run(read, write, initialization_options=server.create_initialization_options())


def main():
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
