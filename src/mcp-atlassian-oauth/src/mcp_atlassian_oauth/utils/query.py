from __future__ import annotations

import re

from ..config import get_defaults


def substitute_current_user(expr: str) -> str:
    """
    Substitute occurrences of currentUser() in a JQL/CQL expression with the configured
    preferred user (MCP_PREFERRED_USER or set via set_defaults), if present.

    Behavior:
    - If a preferred user is set, replaces case-insensitive occurrences of:
        currentUser()
      (whitespace inside parentheses allowed) with:
        "preferred_user"
    - If no preferred user is set or on any error, returns the expression unchanged.

    Note: This is a simple textual substitution and does not skip quoted regions.
    Typical usage of currentUser() is not quoted. If needed, enhance to skip string
    literals in the future.
    """
    if not isinstance(expr, str) or not expr:
        return expr

    try:
        defaults = get_defaults()
        preferred = getattr(defaults, "preferred_user", None)
        if preferred:
            pattern = re.compile(r"\bcurrentUser\b\s*(?:\(\s*\))?", flags=re.IGNORECASE)
            return pattern.sub(f'"{preferred}"', expr)
    except Exception:
        # Do not fail the call if defaults cannot be read; proceed with original expression
        return expr

    return expr


def _has_project_clause(jql: str) -> bool:
    return re.search(r"(?i)\bproject\s*(=|in)\b", jql or "") is not None


def inject_default_project(jql: str) -> str:
    """
    If Defaults.jira_project is set and the JQL does not already constrain the project,
    inject project = "<KEY>" before any ORDER BY clause.

    - If JQL is empty/whitespace and a default project exists, return just project = "<KEY>".
    - If a project clause already exists, return unchanged.
    - On any error, return unchanged.
    """
    if not isinstance(jql, str):
        return jql
    try:
        proj = (get_defaults().jira_project or "").strip()
    except Exception:
        proj = ""
    if not proj:
        return jql

    base = jql or ""
    if not base.strip():
        return f'project = "{proj}"'

    if _has_project_clause(base):
        return base

    m = re.search(r"(?i)\border\s+by\b", base)
    if m:
        where = base[:m.start()].rstrip()
        order_by = base[m.start():]
    else:
        where = base
        order_by = ""

    where = (where + f' AND project = "{proj}"') if where.strip() else f'project = "{proj}"'
    return where + ((" " + order_by) if order_by else "")


def _has_space_clause(cql: str) -> bool:
    return re.search(r"(?i)\bspace\s*(=|in)\b", cql or "") is not None


def inject_default_space(cql: str) -> str:
    """
    If Defaults.conf_space is set and the CQL does not already constrain the space,
    inject space = "<KEY>" before any ORDER BY clause.

    - If CQL is empty/whitespace and a default space exists, return just space = "<KEY>".
    - If a space clause already exists, return unchanged.
    - On any error, return unchanged.
    """
    if not isinstance(cql, str):
        return cql
    try:
        space = (get_defaults().conf_space or "").strip()
    except Exception:
        space = ""
    if not space:
        return cql

    base = cql or ""
    if not base.strip():
        return f'space = "{space}"'

    if _has_space_clause(base):
        return base

    m = re.search(r"(?i)\border\s+by\b", base)
    if m:
        where = base[:m.start()].rstrip()
        order_by = base[m.start():]
    else:
        where = base
        order_by = ""

    where = (where + f' AND space = "{space}"') if where.strip() else f'space = "{space}"'
    return where + ((" " + order_by) if order_by else "")


__all__ = ["substitute_current_user", "inject_default_project", "inject_default_space"]
