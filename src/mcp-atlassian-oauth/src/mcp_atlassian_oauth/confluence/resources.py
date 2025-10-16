from __future__ import annotations

import html
import json
import re
import urllib.parse
from typing import Any, Dict, List, Optional


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


async def list_resources(uri: str) -> List[Dict[str, Any]]:
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

    resources: List[Dict[str, Any]] = []
    if path == "" or path == "/":
        # Space root + advertise child listing
        resources.append({"uri": f"confluence://{space_key}", "name": f"Confluence Space {space_key}"})
        resources.append({"uri": f"confluence://{space_key}/pages", "name": "Pages (recent)"})

        # Add a few recent pages for convenience via CQL
        cql = f'space="{space_key}" AND type=page ORDER BY lastmodified DESC'
        st, _, body = conf_api.cql_search(cql=cql, limit=limit, start=0)
        if st == 200:
            try:
                data = json.loads(body.decode("utf-8"))
                results = data.get("results") or []
                for it in results[:limit]:
                    # Cloud search payload usually at it.get("content")
                    content = it.get("content") or it
                    cid = content.get("id")
                    title = content.get("title") or it.get("title") or ""
                    if cid and title:
                        resources.append(
                            {"uri": f"confluence://{space_key}/pages/{urllib.parse.quote(title)}", "name": str(title)[:200]}
                        )
            except Exception:
                pass
        return resources

    if path == "pages":
        resources.append({"uri": f"confluence://{space_key}/pages", "name": f"{space_key} Pages"})
        cql = f'space="{space_key}" AND type=page ORDER BY lastmodified DESC'
        st, _, body = conf_api.cql_search(cql=cql, limit=limit, start=0)
        if st == 200:
            try:
                data = json.loads(body.decode("utf-8"))
                results = data.get("results") or []
                for it in results[:limit]:
                    content = it.get("content") or it
                    title = content.get("title") or it.get("title") or ""
                    if title:
                        resources.append(
                            {"uri": f"confluence://{space_key}/pages/{urllib.parse.quote(title)}", "name": str(title)[:200]}
                        )
            except Exception:
                pass
        return resources

    # Unknown subpath → no children
    return []


async def read_resource(uri: str) -> List[Dict[str, Any]]:
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

    # Probe space existence/permissions up front to distinguish 404 vs 401/403
    try:
        st_space, _, _ = conf_api.get_space(space_key)
        if st_space in (401, 403):
            return [
                {
                    "type": "text",
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": f"Permission denied: you do not have access to space {space_key}",
                }
            ]
        if st_space == 404:
            return [
                {
                    "type": "text",
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": f"Space not found: {space_key}",
                }
            ]
    except Exception:
        # If probing fails unexpectedly, continue with best-effort behavior below.
        pass

    if path == "" or path == "/":
        # Space summary (recent pages)
        cql = f'space="{space_key}" AND type=page ORDER BY lastmodified DESC'
        st, _, body = conf_api.cql_search(cql=cql, limit=limit, start=0)
        pages = []
        if st == 200:
            try:
                data = json.loads(body.decode("utf-8"))
                results = data.get("results") or []
                for it in results[:limit]:
                    content = it.get("content") or it
                    title = content.get("title") or it.get("title") or ""
                    if title:
                        pages.append({"title": title})
            except Exception:
                pages = []
        if fmt == "json":
            payload = {"space": space_key, "pages": pages}
            return [{"type": "text", "uri": uri, "mimeType": "application/json", "text": json.dumps(payload, indent=2)}]
        # markdown
        lines = [f"# Confluence Space {space_key}", "", f"Recent {len(pages)} pages:"]
        for p in pages:
            title = p.get("title") or ""
            enc = urllib.parse.quote(title)
            lines.append(f"- {title} (confluence://{space_key}/pages/{enc})")
        text = "\n".join(lines) + "\n"
        return [{"type": "text", "uri": uri, "mimeType": "text/markdown", "text": text}]

    if path.startswith("pages/"):
        title_enc = path.split("/", 1)[1]
        title = urllib.parse.unquote(title_enc)
        # Find the page by CQL (use lastmodified sort; escape quotes in title)
        title_esc = title.replace('"', '\\"')
        cql = f'space="{space_key}" AND type=page AND title="{title_esc}" ORDER BY lastmodified DESC'
        st, _, body = conf_api.cql_search(cql=cql, limit=1, start=0)
        page_id: Optional[str] = None
        if st == 200:
            try:
                data = json.loads(body.decode("utf-8"))
                results = data.get("results") or []
                first = results[0] if results else {}
                content = (first.get("content") if isinstance(first, dict) else None) or first or {}
                page_id = content.get("id") if isinstance(content, dict) else None
            except Exception:
                page_id = None

        # Fallback: if CQL failed or returned no id, use content API by spaceKey + title
        if not page_id:
            try:
                st_fb, _, body_fb = conf_api.find_page_by_space_and_title(space_key, title)
                if st_fb == 200:
                    data_fb = json.loads(body_fb.decode("utf-8"))
                    results_fb = (data_fb.get("results") or [])
                    # Prefer exact title match (case-insensitive), else first result
                    for it in results_fb:
                        if not isinstance(it, dict):
                            continue
                        t = it.get("title") or ""
                        if (t == title) or (str(t).strip().lower() == str(title).strip().lower()):
                            page_id = it.get("id")
                            break
                    if not page_id and results_fb:
                        first_fb = results_fb[0]
                        if isinstance(first_fb, dict):
                            page_id = first_fb.get("id")
            except Exception:
                page_id = page_id or None

        if not page_id:
            # If CQL errored earlier, avoid surfacing that code; show not found for cleaner UX
            return [{"type": "text", "uri": uri, "mimeType": "text/plain", "text": f"Not found: {space_key}/{title}"}]

        st2, _, page_body = conf_api.get_page(page_id)
        if st2 != 200:
            return [{"type": "text", "uri": uri, "mimeType": "text/plain", "text": f"Error: Confluence {st2}"}]
        try:
            page = json.loads(page_body.decode("utf-8"))
        except Exception:
            page = {}

        if fmt == "json":
            return [{"type": "text", "uri": uri, "mimeType": "application/json", "text": json.dumps(page, indent=2)}]

        # raw storage (XHTML) if requested
        if fmt == "storage":
            storage = (((page.get("body") or {}).get("storage") or {}).get("value") or "")
            return [{"type": "text", "uri": uri, "mimeType": "text/xml", "text": str(storage)}]

        # default: markdown (best-effort)
        storage = (((page.get("body") or {}).get("storage") or {}).get("value") or "")
        view_html = (((page.get("body") or {}).get("view") or {}).get("value") or "")
        content_html = view_html or storage
        text = _strip_html_to_text(str(content_html))
        # Title as header
        title_hdr = page.get("title") or title
        md = f"# {title_hdr}\n\n{text}\n"
        return [{"type": "text", "uri": uri, "mimeType": "text/markdown", "text": md}]

    # Unknown
    return []
