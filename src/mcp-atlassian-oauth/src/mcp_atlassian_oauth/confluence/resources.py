from __future__ import annotations

import html
import json
import re
import urllib.parse
from typing import Any, Dict, List, Optional

from mcp.types import Resource, TextResourceContents

from ..resources.registry import parse_uri
from . import api as conf_api
from ..config import get_defaults


def _q_int(q: Dict[str, str], key: str, default: int) -> int:
    try:
        return int(q.get(key, default))  # type: ignore[arg-type]
    except Exception:
        return default


def _strip_html_to_text(s: str) -> str:
    """
    Minimal HTML → text fallback without adding dependencies.
    """
    # Remove script/style
    s = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", s)
    # Replace <br> and <p> with line breaks
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p\s*>", "\n\n", s)
    # Remove tags
    s = re.sub(r"(?s)<.*?>", "", s)
    # Unescape entities
    s = html.unescape(s)
    # Normalize whitespace
    s = re.sub(r"[ \t]+\n", "\n", s)
    return s.strip()


async def list_resources(uri: str) -> List[Resource]:
    """
    List Confluence resources under a given prefix.
    Supported:
      - confluence://{space_key}
      - confluence://{space_key}/pages
    """
    scheme, path, space_key, q = parse_uri(uri)
    if scheme != "confluence" or not space_key:
        return []

    # Normalize path
    path = (path or "").strip("/")
    limit = _q_int(q, "limit", 10)

    resources: List[Resource] = []
    if path == "" or path == "/":
        # Space root + advertise child listing
        resources.append(Resource(uri=f"confluence://{space_key}", name=f"Confluence Space {space_key}"))
        resources.append(Resource(uri=f"confluence://{space_key}/pages", name="Pages (recent)"))

        # Add a few recent pages for convenience via CQL
        cql = f'space="{space_key}" AND type=page ORDER BY lastmodified DESC'
        st, _, body = conf_api.cql_search(cql=cql, limit=limit, start=0)
        if st == 200:
            try:
                data = json.loads(body.decode("utf-8"))
                results = data.get("results") or data.get("results", [])  # different deployments may vary
                for it in results[:limit]:
                    # Cloud search payload usually at it.get("content")
                    content = it.get("content") or it
                    cid = content.get("id")
                    title = content.get("title") or it.get("title") or ""
                    if cid and title:
                        resources.append(
                            Resource(
                                uri=f"confluence://{space_key}/pages/{urllib.parse.quote(title)}",
                                name=str(title)[:200],
                            )
                        )
            except Exception:
                pass
        return resources

    if path == "pages":
        resources.append(Resource(uri=f"confluence://{space_key}/pages", name=f"{space_key} Pages"))
        cql = f'space="{space_key}" AND type=page ORDER BY lastmodified DESC'
        st, _, body = conf_api.cql_search(cql=cql, limit=limit, start=0)
        if st == 200:
            try:
                data = json.loads(body.decode("utf-8"))
                results = data.get("results") or data.get("results", [])
                for it in results[:limit]:
                    content = it.get("content") or it
                    title = content.get("title") or it.get("title") or ""
                    if title:
                        resources.append(
                            Resource(
                                uri=f"confluence://{space_key}/pages/{urllib.parse.quote(title)}",
                                name=str(title)[:200],
                            )
                        )
            except Exception:
                pass
        return resources

    # Unknown subpath → no children
    return []


async def read_resource(uri: str) -> List[TextResourceContents]:
    """
    Read Confluence resources:
      - confluence://{space_key}
      - confluence://{space_key}/pages/{title}
    Query params:
      - format=markdown|json|storage (default markdown)
      - limit for space page list in the root summary
    """
    scheme, path, space_key, q = parse_uri(uri)
    if scheme != "confluence" or not space_key:
        return []

    # Honor default output format from Defaults when query param is absent
    try:
        default_fmt = (get_defaults().output_format or "markdown").lower()
    except Exception:
        default_fmt = "markdown"
    fmt = (q.get("format") or default_fmt).lower()
    limit = _q_int(q, "limit", 10)
    path = (path or "").strip("/")

    if path == "" or path == "/":
        # Space summary (recent pages)
        cql = f'space="{space_key}" AND type=page ORDER BY lastmodified DESC'
        st, _, body = conf_api.cql_search(cql=cql, limit=limit, start=0)
        pages = []
        if st == 200:
            try:
                data = json.loads(body.decode("utf-8"))
                results = data.get("results") or data.get("results", [])
                for it in results[:limit]:
                    content = it.get("content") or it
                    title = content.get("title") or it.get("title") or ""
                    if title:
                        pages.append({"title": title})
            except Exception:
                pages = []
        if fmt == "json":
            payload = {"space": space_key, "pages": pages}
            return [TextResourceContents(uri=uri, mimeType="application/json", text=json.dumps(payload, indent=2))]
        # markdown
        lines = [f"# Confluence Space {space_key}", "", f"Recent {len(pages)} pages:"]
        for p in pages:
            title = p.get("title") or ""
            enc = urllib.parse.quote(title)
            lines.append(f"- {title} (confluence://{space_key}/pages/{enc})")
        text = "\n".join(lines) + "\n"
        return [TextResourceContents(uri=uri, mimeType="text/markdown", text=text)]

    if path.startswith("pages/"):
        title_enc = path.split("/", 1)[1]
        title = urllib.parse.unquote(title_enc)
        # Find the page by CQL
        cql = f'space="{space_key}" AND type=page AND title="{title}" ORDER BY version DESC'
        st, _, body = conf_api.cql_search(cql=cql, limit=1, start=0)
        if st != 200:
            return [TextResourceContents(uri=uri, mimeType="text/plain", text=f"Error: Confluence {st}")]
        try:
            data = json.loads(body.decode("utf-8"))
            results = data.get("results") or []
            content = (results[0].get("content") if results else None) or {}
            page_id = content.get("id")
        except Exception:
            page_id = None

        if not page_id:
            return [TextResourceContents(uri=uri, mimeType="text/plain", text=f"Not found: {space_key}/{title}")]

        st2, _, page_body = conf_api.get_page(page_id)
        if st2 != 200:
            return [TextResourceContents(uri=uri, mimeType="text/plain", text=f"Error: Confluence {st2}")]
        try:
            page = json.loads(page_body.decode("utf-8"))
        except Exception:
            page = {}

        if fmt == "json":
            return [TextResourceContents(uri=uri, mimeType="application/json", text=json.dumps(page, indent=2))]

        # raw storage (XHTML) if requested
        if fmt == "storage":
            storage = (((page.get("body") or {}).get("storage") or {}).get("value") or "")
            return [TextResourceContents(uri=uri, mimeType="text/xml", text=str(storage))]

        # default: markdown (best-effort)
        storage = (((page.get("body") or {}).get("storage") or {}).get("value") or "")
        view_html = (((page.get("body") or {}).get("view") or {}).get("value") or "")
        content_html = view_html or storage
        text = _strip_html_to_text(str(content_html))
        # Title as header
        title_hdr = page.get("title") or title
        md = f"# {title_hdr}\n\n{text}\n"
        return [TextResourceContents(uri=uri, mimeType="text/markdown", text=md)]

    # Unknown
    return []
