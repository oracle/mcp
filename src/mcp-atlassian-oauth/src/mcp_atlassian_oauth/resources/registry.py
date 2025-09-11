from __future__ import annotations

import urllib.parse
from typing import Any, Dict, Optional, Tuple


def parse_uri(uri: str) -> Tuple[str, str, str, Dict[str, str]]:
    """
    Parse a resource URI into (scheme, path, netloc, query_dict).
    For URIs like:
      - jira://{project_key}
      - jira://{project_key}/issues/{issue_key}
      - confluence://{space_key}
      - confluence://{space_key}/pages/{title}
    """
    parsed = urllib.parse.urlparse(uri)
    scheme = (parsed.scheme or "").lower()
    netloc = parsed.netloc or ""
    path = parsed.path or ""
    q = dict(urllib.parse.parse_qsl(parsed.query or ""))
    return scheme, path, netloc, q


def _is_supported_scheme(uri: Optional[str]) -> bool:
    if not uri:
        return True  # allow listing top-level across schemes
    scheme, _, _, _ = parse_uri(uri)
    return scheme in ("jira", "confluence")


def register_schemes(server: Any) -> None:
    """
    Register list_resources/read_resource handlers on the given server if the MCP SDK
    exposes these decorators. If not present, this function becomes a no-op to avoid
    import-time failures.
    """
    # Defensive: Only register if the SDK exposes resource handlers
    if not hasattr(server, "list_resources") or not hasattr(server, "read_resource"):
        return

    # Imports placed inside to avoid hard dependency if not used
    from ..jira import resources as jira_res  # type: ignore
    from ..confluence import resources as conf_res  # type: ignore

    @server.list_resources()
    async def list_resources(uri: Optional[str] = None):
        """
        List resources under a given URI prefix.
        Return shape is SDK-defined; we delegate to domain modules which should
        return the expected model instances. This handler simply dispatches.
        """
        if not _is_supported_scheme(uri):
            return []

        if not uri:
            # Top-level: advertise root prefixes
            # Return lightweight faux resources as dictionaries; SDK may coerce or validate.
            # This path is mainly for discovery UIs.
            return [
                {"uri": "jira://", "name": "Jira"},
                {"uri": "confluence://", "name": "Confluence"},
            ]

        scheme, path, netloc, q = parse_uri(uri)
        if scheme == "jira":
            return await jira_res.list_resources(uri)
        if scheme == "confluence":
            return await conf_res.list_resources(uri)
        return []

    @server.read_resource()
    async def read_resource(uri: str):
        """
        Read a resource identified by a jira:// or confluence:// URI.
        Should return a list of ResourceContents (e.g., TextResourceContents).
        """
        scheme, path, netloc, q = parse_uri(uri)
        if scheme == "jira":
            return await jira_res.read_resource(uri)
        if scheme == "confluence":
            return await conf_res.read_resource(uri)
        # Unknown scheme → empty
        return []
