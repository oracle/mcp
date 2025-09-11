from __future__ import annotations

import json
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

from ..auth import authed_fetch, jira_state_from_env


def get_myself() -> Tuple[int, str, bytes]:
    s = jira_state_from_env()
    return authed_fetch(s, "/rest/api/latest/myself", "GET")


def search_issues(
    jql: str,
    fields: Optional[List[str]] = None,
    max_results: int = 50,
    start_at: int = 0,
) -> Tuple[int, str, bytes]:
    s = jira_state_from_env()
    payload: Dict[str, Any] = {
        "jql": str(jql),
        "fields": fields,
        "maxResults": int(max_results),
        "startAt": int(start_at),
    }
    return authed_fetch(s, "/rest/api/latest/search", "POST", payload)


def get_issue(issue_key: str, expand: Optional[str] = None, fields: Optional[List[str]] = None) -> Tuple[int, str, bytes]:
    s = jira_state_from_env()
    q: Dict[str, str] = {}
    if expand:
        q["expand"] = expand
    if fields:
        q["fields"] = ",".join(fields)
    qs = "?" + urllib.parse.urlencode(q) if q else ""
    path = f"/rest/api/latest/issue/{urllib.parse.quote(issue_key)}{qs}"
    return authed_fetch(s, path, "GET")


def add_comment(issue_key: str, body: str) -> Tuple[int, str, bytes]:
    s = jira_state_from_env()
    path = f"/rest/api/latest/issue/{urllib.parse.quote(issue_key)}/comment"
    payload = {"body": str(body)}
    return authed_fetch(s, path, "POST", payload)


def jql_search_raw(jql: str, max_results: int = 50, fields: Optional[List[str]] = None) -> List[dict]:
    """
    Helper for internal search flows that returns parsed JSON issues list or [].
    """
    st, _, body = search_issues(jql=jql, fields=fields or ["summary", "status", "updated", "project", "description"], max_results=max_results, start_at=0)
    if st != 200:
        return []
    try:
        data = json.loads(body.decode("utf-8"))
    except Exception:
        return []
    return (data.get("issues") or []) if isinstance(data, dict) else []
