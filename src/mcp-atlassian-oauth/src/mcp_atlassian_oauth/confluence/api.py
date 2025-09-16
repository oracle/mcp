from __future__ import annotations

import urllib.parse
from typing import Optional, Tuple

from ..auth import authed_fetch, conf_state_from_env


def get_server_info() -> Tuple[int, str, bytes]:
    s = conf_state_from_env()
    return authed_fetch(s, "/rest/api/latest/settings/systemInfo", "GET")


def get_space(space_key: str, expand: Optional[str] = None) -> Tuple[int, str, bytes]:
    """
    Fetch Confluence space metadata by key.
    Useful to differentiate not-found (404) vs permission denied (401/403).
    """
    s = conf_state_from_env()
    qs = urllib.parse.urlencode({"expand": expand}) if expand else ""
    path = f"/rest/api/latest/space/{urllib.parse.quote(space_key)}"
    if qs:
        path = f"{path}?{qs}"
    return authed_fetch(s, path, "GET")


def get_page(page_id: str, expand: Optional[str] = None) -> Tuple[int, str, bytes]:
    """
    Fetch a Confluence page by ID.
    Default expand includes body.storage, version, ancestors, space if not provided.
    """
    s = conf_state_from_env()
    if not expand:
        expand = "body.storage,version,ancestors,space"
    qs = urllib.parse.urlencode({"expand": expand})
    path = f"/rest/api/latest/content/{urllib.parse.quote(page_id)}?{qs}"
    return authed_fetch(s, path, "GET")


def cql_search(cql: str, limit: int = 25, start: int = 0) -> Tuple[int, str, bytes]:
    """
    Execute a CQL search.
    """
    s = conf_state_from_env()
    qs = urllib.parse.urlencode({"cql": str(cql), "limit": str(int(limit)), "start": str(int(start))})
    path = f"/rest/api/latest/search?{qs}"
    return authed_fetch(s, path, "GET")


def find_page_by_space_and_title(space_key: str, title: str, expand: Optional[str] = None) -> Tuple[int, str, bytes]:
    """
    Fallback resolver: query content API by spaceKey and title.
    Defaults to expanding core fields unless expand is provided.
    """
    s = conf_state_from_env()
    if not expand:
        expand = "body.storage,version,ancestors,space"
    qs = urllib.parse.urlencode({"spaceKey": space_key, "title": title, "expand": expand})
    path = f"/rest/api/latest/content?{qs}"
    return authed_fetch(s, path, "GET")
