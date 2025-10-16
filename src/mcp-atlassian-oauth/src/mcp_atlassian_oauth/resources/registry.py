from __future__ import annotations

import urllib.parse
from typing import Dict, Tuple


def parse_uri(uri: str) -> Tuple[str, str, str, Dict[str, str]]:
    """
    Parse a resource URI into (scheme, path, netloc, query_dict).

    Examples:
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
