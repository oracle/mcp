from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Page:
    id: str
    space: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    body_storage: Optional[str] = None
    body_view: Optional[str] = None

    @staticmethod
    def from_rest(doc: Dict[str, Any]) -> "Page":
        body = (doc.get("body") or {})
        storage = (body.get("storage") or {}).get("value")
        view = (body.get("view") or {}).get("value")
        space = (doc.get("space") or {}).get("key")
        # Confluence Cloud `_links` may contain "tinyui" or "webui"
        links = doc.get("_links") or {}
        webui = links.get("webui") or ""
        base = links.get("base") or ""
        url = (base.rstrip("/") + "/" + webui.lstrip("/")) if base and webui else None
        return Page(
            id=str(doc.get("id")),
            space=space,
            title=doc.get("title"),
            url=url,
            body_storage=storage,
            body_view=view,
        )
