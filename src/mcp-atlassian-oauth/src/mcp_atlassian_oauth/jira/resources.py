from __future__ import annotations

import json
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple


from ..resources.registry import parse_uri
from . import api as jira_api
from ..config import get_defaults


def _q_int(q: Dict[str, str], key: str, default: int) -> int:
    try:
        return int(q.get(key, default))  # type: ignore[arg-type]
    except Exception:
        return default


async def list_resources(uri: str) -> List[Dict[str, Any]]:
    """
    List Jira resources under a given prefix.
    Supported:
      - jira://{project_key}
      - jira://{project_key}/issues
    """
    scheme, path, project_key, q = parse_uri(uri)
    if scheme != "jira" or not project_key:
        return []

    # Normalize path
    path = (path or "").strip("/")
    limit = _q_int(q, "limit", 10)

    resources: List[Dict[str, Any]] = []
    if path == "" or path == "/":
        # Project root resource + advertise child issues listing
        resources.append({"uri": f"jira://{project_key}", "name": f"Jira Project {project_key}"})
        resources.append({"uri": f"jira://{project_key}/issues", "name": "Issues (recent)"})
        # Additionally, list a few recent issues as children for convenience
        jql = f'project = "{project_key}" ORDER BY updated DESC'
        st, _, body = jira_api.search_issues(jql=jql, fields=["summary", "status", "updated"], max_results=limit, start_at=0)
        if st == 200:
            try:
                data = json.loads(body.decode("utf-8"))
                for it in (data.get("issues") or [])[:limit]:
                    key = it.get("key")
                    summary = ((it.get("fields") or {}).get("summary") or "")[:120]
                    if key:
                        resources.append({"uri": f"jira://{project_key}/issues/{urllib.parse.quote(key)}", "name": f"{key}: {summary}"})
            except Exception:
                pass
        return resources

    if path == "issues":
        # List recent issues under this project
        resources.append({"uri": f"jira://{project_key}/issues", "name": f"{project_key} Issues"})
        jql = f'project = "{project_key}" ORDER BY updated DESC'
        st, _, body = jira_api.search_issues(jql=jql, fields=["summary", "status", "updated"], max_results=limit, start_at=0)
        if st == 200:
            try:
                data = json.loads(body.decode("utf-8"))
                for it in (data.get("issues") or [])[:limit]:
                    key = it.get("key")
                    summary = ((it.get("fields") or {}).get("summary") or "")[:120]
                    if key:
                        resources.append({"uri": f"jira://{project_key}/issues/{urllib.parse.quote(key)}", "name": f"{key}: {summary}"})
            except Exception:
                pass
        return resources

    # Unknown subpath → no children (leaf)
    return []


def _format_issue_markdown(issue: Dict[str, Any]) -> str:
    f = issue.get("fields") or {}
    key = issue.get("key") or ""
    summary = f.get("summary") or ""
    status = ((f.get("status") or {}) or {}).get("name") or ""
    assignee_obj = f.get("assignee") or {}
    assignee = assignee_obj.get("displayName") or assignee_obj.get("name") or ""
    desc = f.get("description") or ""
    md = []
    md.append(f"# {key} {summary}".strip())
    if status or assignee:
        md.append(f"Status: {status}  ")
        if assignee:
            md.append(f"Assignee: {assignee}")
    if desc:
        md.append("\n## Description\n")
        # Description may be plain text or Atlassian document format; include raw
        md.append(str(desc))
    return "\n".join(md).strip() + "\n"


async def read_resource(uri: str) -> List[Dict[str, Any]]:
    """
    Read Jira resources:
      - jira://{project_key}
      - jira://{project_key}/issues/{issue_key}
    Query params:
      - format=markdown|json (default markdown)
      - limit for project summary issue list
    """
    scheme, path, project_key, q = parse_uri(uri)
    if scheme != "jira" or not project_key:
        return []

    # Honor default output format from Defaults when query param is absent
    try:
        default_fmt = (get_defaults().output_format or "markdown").lower()
    except Exception:
        default_fmt = "markdown"
    fmt = (q.get("format") or default_fmt).lower()
    limit = _q_int(q, "limit", 10)

    path = (path or "").strip("/")

    if path == "" or path == "/":
        # Project summary
        jql = f'project = "{project_key}" ORDER BY updated DESC'
        st, _, body = jira_api.search_issues(jql=jql, fields=["summary", "status", "updated"], max_results=limit, start_at=0)
        issues = []
        if st == 200:
            try:
                data = json.loads(body.decode("utf-8"))
                issues = (data.get("issues") or [])[:limit]
            except Exception:
                issues = []
        if fmt == "json":
            payload = {"project": project_key, "issues": issues}
            return [{"type": "text", "uri": uri, "mimeType": "application/json", "text": json.dumps(payload, indent=2)}]
        # markdown
        lines = [f"# Jira Project {project_key}", "", f"Recent {len(issues)} issues:"]
        for it in issues:
            key = it.get("key")
            summary = ((it.get("fields") or {}).get("summary") or "")[:200]
            if key:
                lines.append(f"- {key}: {summary}")
        text = "\n".join(lines) + "\n"
        return [{"type": "text", "uri": uri, "mimeType": "text/markdown", "text": text}]

    # Support explicit listing node path
    if path == "issues":
        # treat as project summary list
        return await read_resource(f"jira://{project_key}?format={urllib.parse.quote(fmt)}&limit={limit}")

    # Issue leaf
    if path.startswith("issues/"):
        issue_key = path.split("/", 1)[1]
        st, _, body = jira_api.get_issue(issue_key, fields=["summary", "status", "assignee", "description"])
        if st != 200:
            return [{"type": "text", "uri": uri, "mimeType": "text/plain", "text": f"Error: Jira {st}"}]
        try:
            doc = json.loads(body.decode("utf-8"))
        except Exception:
            doc = {}
        if fmt == "json":
            return [{"type": "text", "uri": uri, "mimeType": "application/json", "text": json.dumps(doc, indent=2)}]
        text = _format_issue_markdown(doc)
        return [{"type": "text", "uri": uri, "mimeType": "text/markdown", "text": text}]

    # Unknown
    return []
