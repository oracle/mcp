from __future__ import annotations

from typing import Any, Dict, List, Set

from mcp.types import Tool, TextContent

from . import api as conf_api
from ..auth import authed_fetch, conf_state_from_env
from ..utils.query import substitute_current_user, inject_default_space


_CONF_TOOLS: List[Tool] = [
    Tool(
        name="conf_get_server_info",
        description="GET /rest/api/latest/settings/systemInfo (fallback to /)",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="conf_get_page",
        description="Get Confluence page by ID",
        inputSchema={
            "type": "object",
            "properties": {"pageId": {"type": "string"}},
            "required": ["pageId"],
        },
    ),
    Tool(
        name="conf_search_cql",
        description="Search Confluence using CQL",
        inputSchema={
            "type": "object",
            "properties": {"cql": {"type": "string"}, "limit": {"type": "number"}},
            "required": ["cql"],
        },
    ),
]


def list_tools() -> List[Tool]:
    return list(_CONF_TOOLS)


def names() -> Set[str]:
    return {t.name for t in _CONF_TOOLS}


async def handle_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "conf_get_server_info":
        st, _, body = conf_api.get_server_info()
        if st != 200:
            # fallback to root probe
            s2, _, _ = authed_fetch(conf_state_from_env(), "/", "GET")
            return [TextContent(type="text", text=f"systemInfo: {st}; root: {s2}")]
        return [TextContent(type="text", text=body.decode("utf-8"))]

    if name == "conf_get_page":
        page_id = str(arguments.get("pageId"))
        st, _, body = conf_api.get_page(page_id)
        if st != 200:
            raise RuntimeError(f"Confluence {st}: {body.decode('utf-8', 'ignore')}")
        return [TextContent(type="text", text=body.decode("utf-8"))]

    if name == "conf_search_cql":
        cql = substitute_current_user(str(arguments.get("cql")))
        cql = inject_default_space(cql)
        limit = int(arguments.get("limit", 25))
        st, _, body = conf_api.cql_search(cql=cql, limit=limit, start=0)
        if st != 200:
            raise RuntimeError(f"Confluence {st}: {body.decode('utf-8', 'ignore')}")
        return [TextContent(type="text", text=body.decode("utf-8"))]

    raise RuntimeError(f"Unknown Confluence tool: {name}")
