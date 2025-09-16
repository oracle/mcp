from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

# Domain modules (business logic stays here)
from .jira import api as jira_api
from .jira import search as jira_search
from .utils.query import substitute_current_user, inject_default_project, inject_default_space
from .confluence import api as conf_api
from .auth import authed_fetch, conf_state_from_env
from .config import set_defaults as set_defaults_fn, defaults_as_dict

# ------------------------------------------------------------------------------
# Logging setup (LOG_LEVEL, LOG_FILE/MCP_LOG_FILE)
# ------------------------------------------------------------------------------

logger = logging.getLogger("atlassian.oauth")
_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
_level = getattr(logging, _level_name, logging.INFO)
logging.basicConfig(level=_level)
logger.setLevel(_level)

_log_file = os.environ.get("LOG_FILE") or os.environ.get("MCP_LOG_FILE")
if _log_file:
    try:
        _fh = RotatingFileHandler(_log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
        _fh.setLevel(_level)
        _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
            logger.addHandler(_fh)
    except Exception as _e:
        logger.warning("Failed to attach file logger: %s", _e)


def _debug_payload(prefix: str, payload: Any) -> None:
    if not logger.isEnabledFor(logging.DEBUG):
        return
    try:
        if isinstance(payload, (dict, list)):
            txt = json.dumps(payload)[:4000]
        else:
            s = str(payload)
            txt = s[:4000]
        if len(txt) == 4000:
            txt += "…(truncated)"
        logger.debug("%s %s", prefix, txt)
    except Exception:
        pass


# ------------------------------------------------------------------------------
# FastMCP app
# ------------------------------------------------------------------------------

mcp = FastMCP("atlassian.oauth")


# ------------------------------------------------------------------------------
# Jira tools
# ------------------------------------------------------------------------------

@mcp.tool()
async def jira_get_myself() -> str:
    """
    GET /rest/api/latest/myself
    Returns raw JSON string from Jira.
    """
    st, _, body = jira_api.get_myself()
    if st != 200:
        raise RuntimeError(f"Jira {st}: {body.decode('utf-8', 'ignore')}")
    out = body.decode("utf-8")
    _debug_payload("[jira_get_myself] ->", out)
    return out


@mcp.tool()
async def jira_search_issues(
    jql: str,
    fields: Optional[List[str]] = None,
    maxResults: int = 50,
    startAt: int = 0,
) -> str:
    """
    Search issues by JQL.
    Applies current-user substitution and default project injection.
    Returns raw JSON string.
    """
    j = substitute_current_user(str(jql))
    j = inject_default_project(j)
    st, _, body = jira_api.search_issues(j, fields=fields, max_results=int(maxResults), start_at=int(startAt))
    if st != 200:
        raise RuntimeError(f"Jira {st}: {body.decode('utf-8', 'ignore')}")
    out = body.decode("utf-8")
    _debug_payload("[jira_search_issues] ->", out)
    return out


@mcp.tool()
async def jira_get_issue(issueKey: str) -> str:
    """
    Get issue by key. Returns raw JSON string.
    """
    st, _, body = jira_api.get_issue(str(issueKey))
    if st != 200:
        raise RuntimeError(f"Jira {st}: {body.decode('utf-8', 'ignore')}")
    out = body.decode("utf-8")
    _debug_payload("[jira_get_issue] ->", out)
    return out


@mcp.tool()
async def jira_add_comment(issueKey: str, body: str) -> str:
    """
    Add a comment to an issue. Returns raw JSON string (created comment).
    """
    st, _, resp = jira_api.add_comment(str(issueKey), str(body))
    if st not in (200, 201):
        raise RuntimeError(f"Jira {st}: {resp.decode('utf-8', 'ignore')}")
    out = resp.decode("utf-8")
    _debug_payload("[jira_add_comment] ->", out)
    return out


@mcp.tool()
async def jira_find_similar(
    issueKey: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    project: Optional[str] = None,
    maxResults: int = 20,
    includeClosed: bool = True,
    excludeSelf: bool = True,
    mode: str = "heuristic",
    modelName: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> dict:
    """
    Find related issues by key or text. Returns structured JSON dict.
    """
    if not (issueKey or title or description):
        raise RuntimeError("Provide at least one of: issueKey, title, description")

    results = jira_search.find_similar(
        issue_key=str(issueKey) if issueKey else None,
        title=str(title) if title else None,
        description=str(description) if description else None,
        project=str(project) if project else None,
        max_results=int(maxResults),
        include_closed=bool(includeClosed),
        exclude_self=bool(excludeSelf),
        mode=str(mode),
        model_name=str(modelName),
    )
    _debug_payload("[jira_find_similar] ->", results)
    return results


# ------------------------------------------------------------------------------
# Confluence tools
# ------------------------------------------------------------------------------

@mcp.tool()
async def conf_get_server_info() -> str:
    """
    GET /rest/api/latest/settings/systemInfo (fallback to / if unavailable).
    """
    st, _, body = conf_api.get_server_info()
    if st != 200:
        s2, _, _ = authed_fetch(conf_state_from_env(), "/", "GET")
        return f"systemInfo: {st}; root: {s2}"
    out = body.decode("utf-8")
    _debug_payload("[conf_get_server_info] ->", out)
    return out


@mcp.tool()
async def conf_get_page(pageId: str) -> str:
    """
    Get Confluence page by ID. Returns raw JSON string.
    """
    st, _, body = conf_api.get_page(str(pageId))
    if st != 200:
        raise RuntimeError(f"Confluence {st}: {body.decode('utf-8', 'ignore')}")
    out = body.decode("utf-8")
    _debug_payload("[conf_get_page] ->", out)
    return out


@mcp.tool()
async def conf_search_cql(cql: str, limit: int = 25) -> str:
    """
    Search Confluence using CQL.
    Applies current-user substitution and default space injection.
    Returns raw JSON string.
    """
    cq = inject_default_space(substitute_current_user(str(cql)))
    st, _, body = conf_api.cql_search(cql=cq, limit=int(limit), start=0)
    if st != 200:
        raise RuntimeError(f"Confluence {st}: {body.decode('utf-8', 'ignore')}")
    out = body.decode("utf-8")
    _debug_payload("[conf_search_cql] ->", out)
    return out


# ------------------------------------------------------------------------------
# Utility tool: set_defaults
# ------------------------------------------------------------------------------

@mcp.tool()
async def set_defaults(
    preferredUser: Optional[str] = None,
    jiraProject: Optional[str] = None,
    confSpace: Optional[str] = None,
    outputFormat: Optional[str] = None,
    show: bool = False,
) -> dict:
    """
    Set or view runtime defaults for preferred user, Jira project, Confluence space, and output format.
    Returns the current defaults as a dict.
    """
    if not bool(show):
        set_defaults_fn(
            preferred_user=str(preferredUser) if preferredUser is not None else None,
            jira_project=str(jiraProject) if jiraProject is not None else None,
            conf_space=str(confSpace) if confSpace is not None else None,
            output_format=str(outputFormat) if outputFormat is not None else None,
        )
    out = defaults_as_dict()
    _debug_payload("[set_defaults] ->", out)
    return out


def get_app() -> FastMCP:
    return mcp


def main() -> None:
    """
    Default entry: run fastmcp in stdio mode.
    HTTP mode is launched by __main__.py using our FastAPI bridge.
    """
    mcp.run()


if __name__ == "__main__":
    main()
