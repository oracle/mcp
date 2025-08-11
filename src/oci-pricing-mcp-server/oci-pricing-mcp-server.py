"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.

OCI Pricing MCP (MVP)
- Fetch SKU pricing from Oracle's public Price List API (cetools)
- Falls back to fuzzy name search when direct SKU lookup misses
- Returns structured JSON for clients to render/phrase
- Note: cetools is a public subset; empty `items` is normal behavior
"""

from __future__ import annotations

import asyncio
import difflib
import re
import unicodedata
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

import httpx
from fastmcp import FastMCP

API = "https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/"
mcp = FastMCP("oci-pricing-mcp")

# Minimal alias seed; we avoid maintaining a huge dictionary.
SEED: Dict[str, str] = {
    "adb": "autonomous database",
    "oss": "object storage",
    "lb": "load balancer",
    "oke": "kubernetes engine",
    "oac": "analytics cloud",
    "genai": "generative ai",
    "oci": "oracle cloud infrastructure",
    "db": "database",
    "vm": "virtual machine",
    "vmware": "vmware cloud",
    "bms": "bare metal server",
    "bmc": "bare metal cloud",
    "block": "block storage",
    "file": "file storage",
    "archive": "archive storage",
    "object": "object storage",
    "network": "virtual cloud network",
    "loadbalancer": "load balancer",
    "dns": "domain name system",
    "dns zone": "dns zone management",
}

# -------------------- types (thick only where useful) --------------------


class SimplifiedItem(TypedDict, total=False):
    partNumber: Optional[str]
    displayName: Optional[str]
    metricName: Optional[str]
    serviceCategory: Optional[str]
    currencyCode: Optional[str]
    model: Optional[str]
    value: Optional[float]


class SearchResult(TypedDict):
    query: str
    currency: str
    returned: int
    items: List[SimplifiedItem]
    note: str


# -------------------- text normalization helpers --------------------


def norm(s: str) -> str:
    """Normalize text for matching: NFKC, casefold, punctuation→space, collapse whitespace."""
    s = unicodedata.normalize("NFKC", s).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip()


def nospace(s: str) -> str:
    """Remove spaces for space-insensitive comparisons."""
    return re.sub(r"\s+", "", s)


def acronym(s: str) -> str:
    """Build an acronym: 'autonomous database' → 'ad' (used as a weak hint only)."""
    return "".join(w[0] for w in norm(s).split() if w)


# -------------------- API shaping --------------------


def simplify(x: Dict[str, Any]) -> SimplifiedItem:
    """Return only the first currency block / first price model (MVP simplification)."""
    p = (x.get("prices") or [{}])[0]
    pv = (p.get("prices") or [{}])[0]
    return {
        "partNumber": x.get("partNumber"),
        "displayName": x.get("displayName"),
        "metricName": x.get("metricName"),
        "serviceCategory": x.get("serviceCategory"),
        "currencyCode": p.get("currencyCode"),
        "model": pv.get("model"),
        "value": pv.get("value"),
    }


# ---- fetch with light retry & exponential backoff ----
# Retry only on transient cases: 5xx or network errors.

_RETRIES = 2  # total tries = 1 (initial) + _RETRIES
_BACKOFF_BASE = 0.5  # seconds (exponential: 0.5, 1.0, 2.0, ...)


async def fetch(
    client: httpx.AsyncClient, url: str, params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """GET JSON; non-200 raises; on JSON parse failure return {} safely. Retries transient errors."""
    attempt = 0
    while True:
        try:
            r = await client.get(url, params=params, headers={"Accept": "application/json"})
            # retry on 5xx
            if 500 <= r.status_code < 600 and attempt < _RETRIES:
                raise httpx.HTTPStatusError("server error", request=r.request, response=r)
            r.raise_for_status()
            try:
                return r.json() or {}
            except Exception:
                return {}
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError, httpx.HTTPStatusError) as e:
            if attempt >= _RETRIES:
                raise
            await asyncio.sleep(_BACKOFF_BASE * (2**attempt))
            attempt += 1


async def iter_all(client: httpx.AsyncClient, currency: str = "USD", max_pages: int = 6):
    """Follow APEX `links.rel == "next"` up to `max_pages` to avoid over-fetching/latency."""
    url, params = API, {"currencyCode": currency}
    for _ in range(max_pages):
        data = await fetch(client, url, params)
        for it in data.get("items") or []:
            yield it
        nxt = next((lk.get("href") for lk in data.get("links", []) if lk.get("rel") == "next" and lk.get("href")), None)
        if not nxt:
            break
        url, params = (nxt if nxt.startswith("http") else f"https://apexapps.oracle.com{nxt}"), None


# -------------------- fuzzy search --------------------


def search_items(items: List[Dict[str, Any]], query: str, limit: int = 12) -> List[SimplifiedItem]:
    """
    Fuzzy name search:
    - Short queries (3–4 chars): word-boundary matches only (reduce false hits; e.g., 'ADB').
    - Long queries (>=5): space-insensitive substring OR similarity (≥0.90).
    - Expand aliases only when query == alias or query == full name or query contains full name.
    - If query intends 'Autonomous Database', require both 'autonomous' and 'database'.
    """
    qn = norm(query)

    # ---- intent: Autonomous Database? ----
    q_is_adb_intent = qn in {"adb", "autonomous db", "autonomousdb"}

    # base variants
    variants = {qn, nospace(qn), acronym(qn)}

    # alias expansion (strict): do NOT expand when the only reason is "short alias in query"
    for short, full in SEED.items():
        sn, fn = norm(short), norm(full)
        if qn == sn or qn == fn or fn in qn:
            variants.update({sn, nospace(sn), fn, nospace(fn)})

    # drop too-short
    variants = {v for v in variants if len(v) >= 3}

    res: List[SimplifiedItem] = []
    for it in items:
        # text fields we search against
        fields = [str(it.get(k, "")) for k in ("displayName", "serviceCategory", "metricName", "partNumber")]
        text = " ".join(fields)
        tn = norm(text)
        tns = nospace(tn)

        # ----- ADB 意図なら、"autonomous" と "database" を必須にする -----
        if q_is_adb_intent:
            if not (re.search(r"\bautonomous\b", tn) and re.search(r"\bdatabase\b", tn)):
                continue  # ここで早期除外

        short = [v for v in variants if 3 <= len(v) <= 4]
        long  = [v for v in variants if len(v) >= 5]

        hit = (
            any(re.search(rf"\b{re.escape(v)}\b", tn) for v in short)
            or any(v in tns for v in long)
            or any(difflib.SequenceMatcher(a=v, b=tns).ratio() >= 0.90 for v in long)
        )
        if hit:
            sm = simplify(it)
            if sm not in res:
                res.append(sm)
                if len(res) >= limit:
                    break
    return res


# -------------------- tiny utils --------------------


def _clamp(val: int, lo: int, hi: int, default: int) -> int:
    try:
        v = int(val)
    except Exception:
        return default
    return max(lo, min(hi, v))


def _norm_currency(cur: Optional[str], default: str = "USD") -> str:
    return (cur or default).strip().upper()


# -------------------- MCP tools --------------------


@mcp.tool()
async def pricing_get_sku(part_number: str, currency: str = "USD", max_pages: int = 6) -> Dict[str, Any]:
    """
    Fetch a SKU's price. If the SKU misses, fall back to fuzzy name search.

    Inputs:
      - part_number (str): e.g., "B88298"
      - currency (str): ISO currency code, e.g., "USD"/"JPY" (case-insensitive)
      - max_pages (int): pagination upper bound (1–10)

    Returns (JSON):
      - On SKU hit:       {partNumber, displayName, metricName, serviceCategory, currencyCode, model, value}
      - On name fallback: {"note":"matched-by-name","query","currency","returned","items":[...]}
      - On not found:     {"note":"not-found","query","currency","returned":0,"items":[]}
      - On HTTP failure:  {"note":"http-error","error","input","currency"}
      - Info: cetools is a public subset; empty items can be expected.
    """
    pn = (part_number or "").strip()
    cur = _norm_currency(currency)
    pages = _clamp(max_pages, lo=1, hi=10, default=6)

    if not pn:
        return {"note": "empty-part-number", "items": []}

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            # 1) Direct SKU
            data = await fetch(client, API, {"partNumber": pn, "currencyCode": cur})
            items = data.get("items") or []
            if items:
                out = simplify(items[0])
                # Normalize currencyCode in output if API omitted it
                if not out.get("currencyCode"):
                    out["currencyCode"] = cur
                return out

            # 2) Fuzzy name search (bounded pages)
            all_items = [it async for it in iter_all(client, cur, pages)]
            hits = search_items(all_items, pn)
            return {
                "note": "matched-by-name" if hits else "not-found",
                "query": pn,
                "currency": cur,
                "returned": len(hits),
                "items": hits,
                "info": "cetools is a public subset; empty items can be expected.",
            }
    except httpx.HTTPError as e:
        return {"note": "http-error", "error": str(e), "input": pn, "currency": cur}


@mcp.tool()
async def pricing_search_name(
    query: str, currency: str = "USD", limit: int = 12, max_pages: int = 6
) -> Dict[str, Any]:
    """
    Fuzzy product-name search (aliases/variants/space-insensitive, bounded paging).

    Inputs:
      - query (str): e.g., "Autonomous DB", "Object Storage"
      - currency (str): ISO currency code, e.g., "USD"/"JPY" (case-insensitive)
      - limit (int): number of results to return (1–20)
      - max_pages (int): pagination upper bound (1–10)

    Returns (JSON):
      - {"query","currency","returned", "items":[...], "note":"fuzzy search over the public price list subset"}
      - On empty query: {"note":"empty-query","items":[]}
      - On HTTP failure: {"note":"http-error","error","items":[]}
    """
    q = (query or "").strip()
    if not q:
        return {"note": "empty-query", "items": []}

    cur = _norm_currency(currency)
    lim = _clamp(limit, lo=1, hi=20, default=12)
    pages = _clamp(max_pages, lo=1, hi=10, default=6)

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            items = [it async for it in iter_all(client, cur, pages)]
            hits = search_items(items, q, lim)
            return {
                "query": q,
                "currency": cur,
                "returned": len(hits),
                "items": hits,
                "note": "fuzzy search over the public price list subset",
            }
    except httpx.HTTPError as e:
        return {"note": "http-error", "error": str(e), "items": []}


@mcp.tool()
def ping() -> str:
    """Health check (for CI/Inspector)."""
    return "ok"


def main() -> None:
    """MCP server entrypoint."""
    mcp.run()


if __name__ == "__main__":
    main()
