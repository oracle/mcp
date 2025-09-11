from __future__ import annotations

import json
import os
import urllib.parse
from dataclasses import dataclass
from typing import Optional, Tuple

from . import http


@dataclass
class TokenState:
    """
    OAuth token + base URL configuration for an Atlassian product (Jira/Confluence).
    """
    base_url: str
    access_token: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    refresh_token: Optional[str]

    def __post_init__(self) -> None:
        self.base_url = (self.base_url or "").rstrip("/")

    def can_refresh(self) -> bool:
        return bool(self.client_id and self.client_secret and self.refresh_token)

    def token_url(self) -> str:
        return f"{self.base_url}/rest/oauth2/latest/token"

    def refresh(self) -> bool:
        """
        Refresh the access token using the refresh token if possible.
        Returns True if access_token was updated.
        """
        if not self.can_refresh():
            return False

        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        url = self.token_url() + "?" + urllib.parse.urlencode(params)

        status, _, body = http.http_request(
            url,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=b"",
        )
        if status != 200:
            return False

        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            return False

        new_access = payload.get("access_token")
        new_refresh = payload.get("refresh_token")
        if new_access:
            self.access_token = new_access
        if new_refresh:
            self.refresh_token = new_refresh
        return bool(new_access)


def jira_state_from_env() -> TokenState:
    """
    Construct a TokenState for Jira from environment variables.
    Required:
      - JIRA_BASE_URL
    Optional:
      - JIRA_ACCESS_TOKEN
      - JIRA_CLIENT_ID
      - JIRA_CLIENT_SECRET
      - JIRA_REFRESH_TOKEN
    """
    base = os.environ.get("JIRA_BASE_URL")
    if not base:
        raise RuntimeError("JIRA_BASE_URL is required")
    return TokenState(
        base_url=base,
        access_token=os.environ.get("JIRA_ACCESS_TOKEN"),
        client_id=os.environ.get("JIRA_CLIENT_ID"),
        client_secret=os.environ.get("JIRA_CLIENT_SECRET"),
        refresh_token=os.environ.get("JIRA_REFRESH_TOKEN"),
    )


def conf_state_from_env() -> TokenState:
    """
    Construct a TokenState for Confluence from environment variables.
    Required:
      - CONF_BASE_URL
    Optional:
      - CONF_ACCESS_TOKEN
      - CONF_CLIENT_ID
      - CONF_CLIENT_SECRET
      - CONF_REFRESH_TOKEN
    """
    base = os.environ.get("CONF_BASE_URL")
    if not base:
        raise RuntimeError("CONF_BASE_URL is required")
    return TokenState(
        base_url=base,
        access_token=os.environ.get("CONF_ACCESS_TOKEN"),
        client_id=os.environ.get("CONF_CLIENT_ID"),
        client_secret=os.environ.get("CONF_CLIENT_SECRET"),
        refresh_token=os.environ.get("CONF_REFRESH_TOKEN"),
    )


def authed_fetch(
    state: TokenState,
    path: str,
    method: str = "GET",
    json_body: Optional[dict] = None,
) -> Tuple[int, str, bytes]:
    """
    Perform an authenticated HTTP call using the current TokenState.
    On 401 with refresh capability, refresh and retry once.
    """
    url = state.base_url + path
    headers = {"Accept": "application/json"}
    data = None

    if json_body is not None:
        import json as _json
        data = _json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    if state.access_token:
        headers["Authorization"] = f"Bearer {state.access_token}"

    status, ctype, body = http.http_request(url, method=method, headers=headers, data=data)

    if status == 401 and state.can_refresh():
        if state.refresh():
            headers["Authorization"] = f"Bearer {state.access_token}"
            status, ctype, body = http.http_request(url, method=method, headers=headers, data=data)

    return status, ctype, body
