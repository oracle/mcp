"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.

OCI Pricing MCP Server
- Fetch SKU pricing from Oracle's public Price List API (cetools)
- Falls back to fuzzy name search when direct SKU lookup misses
- Returns structured JSON for clients to render/phrase
- Note: cetools is a public subset; empty `items` is normal behavior
"""

from __future__ import annotations

import asyncio
import difflib
import os
import re
import unicodedata
from typing import Any
from typing import TypedDict

import httpx
from fastmcp import FastMCP

API = "https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/"
mcp = FastMCP("oci-pricing-mcp")

# -------------------- environment-driven defaults --------------------
# These allow MCP client config to override defaults via "env".
# Example (Claude Desktop):
#   "env": { "OCI_PRICING_DEFAULT_CCY": "JPY", "OCI_PRICING_HTTP_TIMEOUT": "30" }
DEFAULT_CCY = os.getenv("OCI_PRICING_DEFAULT_CCY", "USD").strip().upper()
DEFAULT_MAX_PAGES = int(os.getenv("OCI_PRICING_MAX_PAGES", "6"))
DEFAULT_TIMEOUT = float(os.getenv("OCI_PRICING_HTTP_TIMEOUT", "25"))
_RETRIES = int(os.getenv("OCI_PRICING_RETRIES", "2"))  # total tries = 1 + _RETRIES
_BACKOFF_BASE = float(os.getenv("OCI_PRICING_BACKOFF", "0.5"))  # seconds

# Minimal alias seed; we avoid maintaining a huge dictionary.
SEED: dict[str, str] = {
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
    partNumber: str | None
    displayName: str | None
    metricName: str | None
    serviceCategory: str | None
    currencyCode: str | None
    model: str | None
    value: float | None
    note: str | None


class SearchResult(TypedDict):
    query: str
    currency: str
    returned: int
    items: list[SimplifiedItem]
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


def _iter_price_blocks(x: dict[str, Any]) -> list[dict[str, Any]]:
    """
    cetools exposes price blocks in two shapes:
      1) prices: [{currencyCode, prices:[{model,value}]}]
      2) currencyCodeLocalizations: [{currencyCode, prices:[{model,value}]}]
    Merge both into a single list to simplify downstream picking.
    """
    blocks: list[dict[str, Any]] = []
    if isinstance(x.get("prices"), list):
        blocks += x["prices"]
    if isinstance(x.get("currencyCodeLocalizations"), list):
        blocks += x["currencyCodeLocalizations"]
    return blocks


def _pick_price(
    x: dict[str, Any], prefer_currency: str | None = None
) -> tuple[str | None, float | None, str | None]:
    """
    Return (model, value, currencyCode) selecting from both `prices` and
    `currencyCodeLocalizations`. If `prefer_currency` is given, pick from that
    currency first; otherwise return the first available.
    """
    blocks = _iter_price_blocks(x)

    # Prefer a specific currency if requested
    if prefer_currency:
        for b in blocks:
            if (b or {}).get("currencyCode") == prefer_currency:
                for pv in b.get("prices") or []:
                    model, value = pv.get("model"), pv.get("value")
                    if model is not None and value is not None:
                        return model, value, b.get("currencyCode")

    # Otherwise return the first model/value found
    for b in blocks:
        for pv in b.get("prices") or []:
            model, value = pv.get("model"), pv.get("value")
            if model is not None and value is not None:
                return model, value, b.get("currencyCode")

    return None, None, None


def simplify(x: dict[str, Any], prefer_currency: str | None = None) -> dict[str, Any]:
    """
    Shape an API item for clients:
      - Choose price/model based on prefer_currency when possible.
      - Ensure currencyCode is always set (fallback to prefer_currency).
    """
    model, value, ccy = _pick_price(x, prefer_currency)
    if ccy is None and prefer_currency:
        ccy = prefer_currency

    out: dict[str, Any] = {
        "partNumber": x.get("partNumber"),
        "displayName": x.get("displayName"),
        "metricName": x.get("metricName"),
        "serviceCategory": x.get("serviceCategory"),
        "currencyCode": ccy,
        "model": model,
        "value": value,
    }
    if model is None or value is None:
        out["note"] = "no-unit-price-in-public-subset-or-currency"
    return out


# ---- fetch with light retry & exponential backoff ----
# Retry only on transient cases: 5xx or network errors.


async def fetch(
    client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
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
        except (
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.RemoteProtocolError,
            httpx.HTTPStatusError,
        ):
            if attempt >= _RETRIES:
                raise
            await asyncio.sleep(_BACKOFF_BASE * (2**attempt))
            attempt += 1


async def iter_all(
    client: httpx.AsyncClient, currency: str = DEFAULT_CCY, max_pages: int = DEFAULT_MAX_PAGES
):
    """Follow APEX `links.rel == "next"` up to `max_pages` to avoid over-fetching/latency."""
    url, params = API, {"currencyCode": currency}
    for _ in range(max_pages):
        data = await fetch(client, url, params)
        for it in data.get("items") or []:
            yield it
        nxt = next(
            (
                lk.get("href")
                for lk in data.get("links", [])
                if lk.get("rel") == "next" and lk.get("href")
            ),
            None,
        )
        if not nxt:
            break
        url, params = (nxt if nxt.startswith("http") else f"https://apexapps.oracle.com{nxt}"), None


# -------------------- fuzzy search --------------------


def search_items(
    items: list[dict[str, Any]],
    query: str,
    limit: int = 12,
    prefer_currency: str | None = None,
) -> list[SimplifiedItem]:
    """
    Fuzzy name search:
    - Short queries (3–4 chars): word-boundary matches only (reduce false hits; e.g., 'ADB').
    - Long queries (>=5): space-insensitive substring OR similarity (≥0.90).
    - Expand aliases only when query == alias or query == full name or query contains full name.
    - If query intends 'Autonomous Database', require both 'autonomous' and 'database'.
    - On return, pass each hit through simplify(..., prefer_currency) so items[*].currencyCode is always populated.
    """
    qn = norm(query)

    # Intent: Autonomous Database?
    q_is_adb_intent = qn in {"adb", "autonomous db", "autonomousdb"}

    # Base variants
    variants = {qn, nospace(qn), acronym(qn)}

    # Strict alias expansion
    for short, full in SEED.items():
        sn, fn = norm(short), norm(full)
        if qn == sn or qn == fn or fn in qn:
            variants.update({sn, nospace(sn), fn, nospace(fn)})

    # Drop too-short tokens
    variants = {v for v in variants if len(v) >= 3}

    res: list[SimplifiedItem] = []
    for it in items:
        fields = [
            str(it.get(k, ""))
            for k in ("displayName", "serviceCategory", "metricName", "partNumber")
        ]
        text = " ".join(fields)
        tn = norm(text)
        tns = nospace(tn)

        # ADB intent: require both keywords
        if q_is_adb_intent:
            if not (re.search(r"\bautonomous\b", tn) and re.search(r"\bdatabase\b", tn)):
                continue

        short = [v for v in variants if 3 <= len(v) <= 4]
        long = [v for v in variants if len(v) >= 5]

        hit = (
            any(re.search(rf"\b{re.escape(v)}\b", tn) for v in short)
            or any(v in tns for v in long)
            or any(difflib.SequenceMatcher(a=v, b=tns).ratio() >= 0.90 for v in long)
        )
        if hit:
            sm = simplify(it, prefer_currency)
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


def _norm_currency(cur: str | None, default: str = DEFAULT_CCY) -> str:
    return (cur or default).strip().upper()


# -------------------- PURE IMPLEMENTATIONS (test here primarily) --------------------


async def pricing_get_sku_impl(
    part_number: str, currency: str | None = None, max_pages: int | None = None
) -> dict[str, Any]:
    """
    Fetch a SKU's price. If the SKU misses, fall back to fuzzy name search.

    Environment overrides (when args are omitted):
      - currency: OCI_PRICING_DEFAULT_CCY (default: 'USD')
      - max_pages: OCI_PRICING_MAX_PAGES (default: 6)

    Inputs:
      - part_number (str): e.g., "B88298"
      - currency (str|None): ISO code, e.g., "USD"/"JPY"; if None, uses env default
      - max_pages (int|None): pagination upper bound (1–10); if None, uses env default

    Returns (dict):
      - On SKU hit:
          {"kind":"sku", partNumber, displayName, metricName, serviceCategory, currencyCode, model, value}
      - On name fallback:
          {"kind":"search","note":"matched-by-name","query","currency","returned","items":[...]}
      - On not found:
          {"kind":"search","note":"not-found","query","currency","returned":0,"items":[]}
      - On HTTP failure:
          {"kind":"error","note":"http-error","error","input","currency"}

    Note: cetools is a public subset; empty items can be expected periodically.
    """
    pn = (part_number or "").strip()
    cur = _norm_currency(currency, default=DEFAULT_CCY)
    pages = _clamp(
        max_pages if max_pages is not None else DEFAULT_MAX_PAGES,
        lo=1,
        hi=10,
        default=DEFAULT_MAX_PAGES,
    )

    if not pn:
        return {"kind": "error", "note": "empty-part-number", "items": []}

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            # 1) Direct SKU
            data = await fetch(client, API, {"partNumber": pn, "currencyCode": cur})
            items = data.get("items") or []
            if items:
                out = simplify(items[0], cur)
                if not out.get("currencyCode"):
                    out["currencyCode"] = cur
                out["kind"] = "sku"
                return out

            # 2) Fuzzy name search (bounded pages)
            all_items = [it async for it in iter_all(client, cur, pages)]
            hits = search_items(all_items, pn, limit=12, prefer_currency=cur)
            return {
                "kind": "search",
                "note": "matched-by-name" if hits else "not-found",
                "query": pn,
                "currency": cur,
                "returned": len(hits),
                "items": hits,
                "info": "cetools is a public subset; empty items can be expected.",
            }
    except httpx.HTTPError as e:
        return {
            "kind": "error",
            "note": "http-error",
            "error": str(e),
            "input": pn,
            "currency": cur,
        }


async def pricing_search_name_impl(
    query: str,
    currency: str | None = None,
    limit: int = 12,
    max_pages: int | None = None,
    require_priced: bool = False,
) -> dict[str, Any]:
    """
    Fuzzy product-name search (aliases/variants/space-insensitive, bounded paging).

    Environment overrides (when args are omitted):
      - currency: OCI_PRICING_DEFAULT_CCY (default: 'USD')
      - max_pages: OCI_PRICING_MAX_PAGES (default: 6)

    Inputs:
      - query (str): e.g., "Autonomous DB", "Object Storage"
      - currency (str|None): ISO code, e.g., "USD"/"JPY"; if None, uses env default
      - limit (int): number of results to return (1–20)
      - max_pages (int|None): pagination upper bound (1–10); if None, uses env default
      - require_priced (bool): if True, keep only items with model/value present

    Returns (dict):
      - {"kind":"search","query","currency","returned","items":[...], "note":"fuzzy search over the public price list subset"}
      - On empty query: {"kind":"error","note":"empty-query","items":[]}
      - On HTTP failure: {"kind":"error","note":"http-error","error","items":[]}

    Behavior:
      - search→simplify(..., prefer_currency) ensures items[*].currencyCode is always populated
      - enrich via per-SKU fetch to fill pricing when possible; then filter if require_priced=True
    """
    q = (query or "").strip()
    if not q:
        return {"kind": "error", "note": "empty-query", "items": []}

    cur = _norm_currency(currency, default=DEFAULT_CCY)
    lim = _clamp(limit, lo=1, hi=20, default=12)
    pages = _clamp(
        max_pages if max_pages is not None else DEFAULT_MAX_PAGES,
        lo=1,
        hi=10,
        default=DEFAULT_MAX_PAGES,
    )

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            items = [it async for it in iter_all(client, cur, pages)]
            hits = search_items(items, q, lim, prefer_currency=cur)

            # Enrich each hit via SKU endpoint to pick the most precise price in requested currency
            enriched: list[dict[str, Any]] = []
            for sm in hits:
                pn = sm.get("partNumber")
                got = sm
                if pn:
                    detail = await fetch(client, API, {"partNumber": pn, "currencyCode": cur})
                    det_items = detail.get("items") or []
                    if det_items:
                        got = simplify(det_items[0], cur)
                        if not got.get("currencyCode"):
                            got["currencyCode"] = cur
                if require_priced:
                    if got.get("model") is not None and got.get("value") is not None:
                        enriched.append(got)
                else:
                    enriched.append(got)

            return {
                "kind": "search",
                "query": q,
                "currency": cur,
                "returned": len(enriched),
                "items": enriched,
                "note": "fuzzy search; per-item price enriched via SKU endpoint",
            }
    except httpx.HTTPError as e:
        return {"kind": "error", "note": "http-error", "error": str(e), "items": []}


# -------------------- MCP tool wrappers (thin) --------------------


@mcp.tool()
async def pricing_get_sku(
    part_number: str, currency: str | None = None, max_pages: int | None = None
) -> dict[str, Any]:
    """
    Thin wrapper that delegates to pricing_get_sku_impl.
    Returns a dict; FastMCP will serialize for the client.
    If currency/max_pages are omitted, environment defaults apply.
    """
    return await pricing_get_sku_impl(
        part_number=part_number, currency=currency, max_pages=max_pages
    )


@mcp.tool()
async def pricing_search_name(
    query: str,
    currency: str | None = None,
    limit: int = 12,
    max_pages: int | None = None,
    require_priced: bool = False,
) -> dict[str, Any]:
    """
    Thin wrapper that delegates to pricing_search_name_impl.
    Returns a dict; FastMCP will serialize for the client.
    If currency/max_pages are omitted, environment defaults apply.
    """
    return await pricing_search_name_impl(
        query=query,
        currency=currency,
        limit=limit,
        max_pages=max_pages,
        require_priced=require_priced,
    )


@mcp.tool()
def ping() -> str:
    """Health check (for CI/Inspector)."""
    return "ok"


def main() -> None:
    """MCP server entrypoint."""
    mcp.run()


if __name__ == "__main__":
    main()
