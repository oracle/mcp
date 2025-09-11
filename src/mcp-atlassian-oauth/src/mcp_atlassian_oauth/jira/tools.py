from __future__ import annotations

import json
from typing import Any, Dict, List, Set

from mcp.types import Tool, TextContent

from . import api as jira_api
from . import search as jira_search
from ..utils.query import substitute_current_user, inject_default_project


_JIRA_TOOLS: List[Tool] = [
    Tool(
        name="jira_get_myself",
        description="GET /rest/api/latest/myself",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="jira_search_issues",
        description="Search Jira by JQL",
        inputSchema={
            "type": "object",
            "properties": {
                "jql": {"type": "string"},
                "fields": {"type": "array", "items": {"type": "string"}},
                "maxResults": {"type": "number"},
                "startAt": {"type": "number"},
            },
            "required": ["jql"],
        },
    ),
    Tool(
        name="jira_get_issue",
        description="Get issue by key",
        inputSchema={
            "type": "object",
            "properties": {"issueKey": {"type": "string"}},
            "required": ["issueKey"],
        },
    ),
    Tool(
        name="jira_add_comment",
        description="Add comment to issue",
        inputSchema={
            "type": "object",
            "properties": {
                "issueKey": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["issueKey", "body"],
        },
    ),
    Tool(
        name="jira_find_similar",
        description="Find related Jira issues by key or free text (title/description) using phrase+token search; supports semantic re-ranking behind optional extra",
        inputSchema={
            "type": "object",
            "properties": {
                "issueKey": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "project": {"type": "string"},
                "maxResults": {"type": "number"},
                "includeClosed": {"type": "boolean"},
                "excludeSelf": {"type": "boolean"},
                "mode": {"type": "string", "enum": ["heuristic", "semantic", "hybrid"]},
                "modelName": {"type": "string"}
            }
        },
    ),
]


def list_tools() -> List[Tool]:
    return list(_JIRA_TOOLS)


def names() -> Set[str]:
    return {t.name for t in _JIRA_TOOLS}


async def handle_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "jira_get_myself":
        st, _, body = jira_api.get_myself()
        if st != 200:
            raise RuntimeError(f"Jira {st}: {body.decode('utf-8', 'ignore')}")
        return [TextContent(type="text", text=body.decode("utf-8"))]

    if name == "jira_search_issues":
        jql = substitute_current_user(str(arguments.get("jql")))
        jql = inject_default_project(jql)
        fields = arguments.get("fields")
        max_results = int(arguments.get("maxResults", 50))
        start_at = int(arguments.get("startAt", 0))
        st, _, body = jira_api.search_issues(jql, fields=fields, max_results=max_results, start_at=start_at)
        if st != 200:
            raise RuntimeError(f"Jira {st}: {body.decode('utf-8', 'ignore')}")
        return [TextContent(type="text", text=body.decode("utf-8"))]

    if name == "jira_get_issue":
        issue_key = str(arguments.get("issueKey"))
        st, _, body = jira_api.get_issue(issue_key)
        if st != 200:
            raise RuntimeError(f"Jira {st}: {body.decode('utf-8', 'ignore')}")
        return [TextContent(type="text", text=body.decode("utf-8"))]

    if name == "jira_add_comment":
        issue_key = str(arguments.get("issueKey"))
        body_str = str(arguments.get("body"))
        st, _, body = jira_api.add_comment(issue_key, body_str)
        if st not in (200, 201):
            raise RuntimeError(f"Jira {st}: {body.decode('utf-8', 'ignore')}")
        return [TextContent(type="text", text=body.decode("utf-8"))]

    if name == "jira_find_similar":
        issue_key = arguments.get("issueKey")
        title = arguments.get("title")
        description = arguments.get("description")
        project = arguments.get("project")
        max_results = int(arguments.get("maxResults", 20))
        include_closed = bool(arguments.get("includeClosed", True))
        exclude_self = bool(arguments.get("excludeSelf", True))
        mode = str(arguments.get("mode", "heuristic"))
        model_name = str(arguments.get("modelName", "sentence-transformers/all-MiniLM-L6-v2"))

        if not (issue_key or title or description):
            raise RuntimeError("Provide at least one of: issueKey, title, description")

        results = jira_search.find_similar(
            issue_key=str(issue_key) if issue_key else None,
            title=str(title) if title else None,
            description=str(description) if description else None,
            project=str(project) if project else None,
            max_results=max_results,
            include_closed=include_closed,
            exclude_self=exclude_self,
            mode=mode,
            model_name=model_name,
        )
        return [TextContent(type="text", text=json.dumps(results, indent=2))]

    raise RuntimeError(f"Unknown Jira tool: {name}")
