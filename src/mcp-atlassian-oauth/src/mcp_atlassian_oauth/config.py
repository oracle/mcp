from __future__ import annotations

import os
import threading
from dataclasses import dataclass, replace, asdict
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class Defaults:
    """
    Runtime defaults for the MCP Atlassian server.

    Fields:
      - preferred_user: Optional default username to act as (display or account identifier)
      - jira_project: Optional default Jira project key (e.g., "ENG")
      - conf_space:   Optional default Confluence space key (e.g., "DOCS")
      - output_format: Preferred default output format for resource reads where applicable.
                       For Confluence pages this is 'markdown' by default.
    """
    preferred_user: Optional[str] = None
    jira_project: Optional[str] = None
    conf_space: Optional[str] = None
    output_format: str = "markdown"  # default read format for content-like resources


# Thread-safe, process-local defaults storage
_lock = threading.RLock()
_defaults = Defaults()


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name)
    if val is None or val == "":
        return default
    return val


def load_from_env() -> None:
    """
    Initialize defaults from environment variables if present.

    Recognized env vars:
      - MCP_PREFERRED_USER
      - JIRA_DEFAULT_PROJECT
      - CONF_DEFAULT_SPACE
      - MCP_DEFAULT_OUTPUT_FORMAT (markdown|json|storage); 'markdown' is typical default

    This function is idempotent; it merges only provided values over current defaults.
    """
    preferred_user = _get_env("MCP_PREFERRED_USER", None)
    jira_project = _get_env("JIRA_DEFAULT_PROJECT", None)
    conf_space = _get_env("CONF_DEFAULT_SPACE", None)
    output_format = _get_env("MCP_DEFAULT_OUTPUT_FORMAT", None)

    updates: Dict[str, Any] = {}
    if preferred_user is not None:
        updates["preferred_user"] = preferred_user
    if jira_project is not None:
        updates["jira_project"] = jira_project
    if conf_space is not None:
        updates["conf_space"] = conf_space
    if output_format is not None:
        updates["output_format"] = output_format

    if updates:
        set_defaults(**updates)


def get_defaults() -> Defaults:
    """
    Get a snapshot of the current defaults in a thread-safe manner.
    """
    with _lock:
        return _defaults  # Defaults is frozen (immutable), safe to return


def set_defaults(
    preferred_user: Optional[str] = None,
    jira_project: Optional[str] = None,
    conf_space: Optional[str] = None,
    output_format: Optional[str] = None,
) -> Defaults:
    """
    Update runtime defaults. Only non-None arguments will be updated.

    Returns the new Defaults snapshot.
    """
    global _defaults
    with _lock:
        new_defaults = _defaults
        if preferred_user is not None:
            new_defaults = replace(new_defaults, preferred_user=preferred_user)
        if jira_project is not None:
            new_defaults = replace(new_defaults, jira_project=jira_project)
        if conf_space is not None:
            new_defaults = replace(new_defaults, conf_space=conf_space)
        if output_format is not None:
            new_defaults = replace(new_defaults, output_format=output_format)

        _defaults = new_defaults
        return _defaults


def defaults_as_dict() -> Dict[str, Any]:
    """
    Convenience helper to expose defaults for diagnostics or a tool response.
    """
    return asdict(get_defaults())


# Initialize from environment once on import (non-fatal, idempotent).
try:
    load_from_env()
except Exception:
    # Do not fail import if environment-based initialization has issues.
    # Server will continue with safe defaults until set_defaults tool is invoked.
    pass
