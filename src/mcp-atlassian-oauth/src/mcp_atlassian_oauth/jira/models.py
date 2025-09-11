from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class Project:
    key: str
    name: Optional[str] = None
    url: Optional[str] = None


@dataclass
class Issue:
    key: str
    summary: Optional[str] = None
    status: Optional[str] = None
    updated: Optional[str] = None
    projectKey: Optional[str] = None
    url: Optional[str] = None

    @staticmethod
    def from_rest(issue: Dict[str, Any]) -> "Issue":
        fields = issue.get("fields", {}) or {}
        status = fields.get("status") or {}
        project = fields.get("project") or {}
        return Issue(
            key=issue.get("key"),
            summary=fields.get("summary"),
            status=(status.get("name") or ""),
            updated=fields.get("updated"),
            projectKey=project.get("key"),
        )
