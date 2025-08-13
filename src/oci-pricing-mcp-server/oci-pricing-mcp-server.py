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
from functools import lru_cache
from typing import Any, TypedDict

import httpx
from fastmcp import FastMCP

# Optional deps for ISO 4217 validation
try:
    from babel.numbers import get_currency_name  # type: ignore
    _HAS_BABEL = True
except Exception:
    _HAS_BABEL = False

try:
    import pycountry  # type: ignore
    _HAS_PYCOUNTRY = True
except Exception:
    _HAS_PYCOUNTRY = False

API = "https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/"
mcp = FastMCP("oci-pricing-mcp")

# -------------------- environment-driven defaults --------------------
# These allow MCP client config to override defaults via "env".
# Example (Claude Desktop):
#   "env": {
#       "OCI_PRICING_DEFAULT_CCY": "JPY",
#       "OCI_PRICING_HTTP_TIMEOUT": "30",
#       "OCI_PRICING_MAX_PAGES": "6",
#       "OCI_PRICING_ALT_CCY": "USD"
#   }
DEFAULT_CCY = os.getenv("OCI_PRICING_DEFAULT_CCY", "USD").strip().upper()
DEFAULT_MAX_PAGES = int(os.getenv("OCI_PRICING_MAX_PAGES", "6"))
DEFAULT_TIMEOUT = float(os.getenv("OCI_PRICING_HTTP_TIMEOUT", "25"))
_RETRIES = int(os.getenv("OCI_PRICING_RETRIES", "2"))  # total tries = 1 (initial) + _RETRIES
_BACKOFF_BASE = float(os.getenv("OCI_PRICING_BACKOFF", "0.5"))  # seconds
# Optional alternate currency for reference when requested currency is zero/missing
ALT_CCY = (os.getenv("OCI_PRICING_ALT_CCY", "").strip().upper() or None)

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
    # Optional reference price in alternate currency
    altCurrencyCode: str | None
    altModel: str | None
    altValue: float | None


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
      - Add notes for missing or zero unit prices.
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

    # annotate missing or zero price
    if model is None or value is None:
        out["note"] = "no-unit-price-in-public-subset-or-currency"
    else:
        try:
            if float(value) == 0.0:
                out["note"] = "zero-price-or-free-tier-only"
        except Exception:
            out.setdefault("note", "no-unit-price-in-public-subset-or-currency")

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
    # legacy helper (unused by strict path); kept for completeness
    return (cur or default).strip().upper()


# --- currency validation (ISO 4217 AAA) ---
_CCY_RE = re.compile(r"^[A-Z]{3}$")


@lru_cache(maxsize=1024)
def _is_valid_iso4217(code: str) -> bool:
    """
    True if code is an uppercase AAA and exists per Babel or pycountry.
    Fallback: if neither dependency is available, accept AAA-form codes.
    """
    if not _CCY_RE.match(code):
        return False

    # Prefer Babel (aligns better with current tender currencies)
    if _HAS_BABEL:
        try:
            # Unknown codes often raise UnknownCurrencyError
            get_currency_name(code)
            return True
        except Exception:
            # Fall through to pycountry check
            pass

    if _HAS_PYCOUNTRY:
        try:
            return (pycountry.currencies.get(alpha_3=code) is not None)  # type: ignore
        except Exception:
            pass

    # Offline / no deps: allow AAA-form as best-effort fallback
    return True


def _norm_currency_strict(cur: str | None, default: str = DEFAULT_CCY) -> tuple[str, str | None]:
    """
    Validate currency as ISO 4217 (three letters), auto-uppercasing inputs.

    Behavior:
      - If the caller omits the parameter (None), fall back to default (upper) and validate.
      - If the caller provides a value (including mixed/lower case), it is **uppercased** then validated.
        -> 'jpy' -> 'JPY', 'Usd' -> 'USD'
      - Invalid forms (not 3 letters) or unknown codes return ('<UPPER>', 'invalid-currency-format').

    Returns (currency_uppercased, error_note). error_note is None if valid.
    """
    if cur is None:
        c = (default or "").strip().upper()
        return (c, None) if _is_valid_iso4217(c) else (c, "invalid-default-currency")

    s = cur.strip().upper()
    if not _is_valid_iso4217(s):
        return s, "invalid-currency-format"
    return s, None


# -------------------- alt-currency enrichment --------------------


async def _enrich_with_alt_currency_if_zero(
    client: httpx.AsyncClient,
    item: dict[str, Any],
    part_number: str,
    requested_currency: str,
) -> dict[str, Any]:
    """
    If the requested-currency price is zero or missing, optionally fetch
    an alternate-currency price (ALT_CCY) and attach it as alt* fields.
    Does not change the main currency/value; only adds reference info.
    """
    try:
        v = item.get("value", None)
        is_zero_or_missing = (v is None)
        if not is_zero_or_missing:
            try:
                is_zero_or_missing = (float(v) == 0.0)
            except Exception:
                is_zero_or_missing = True

        if is_zero_or_missing and ALT_CCY and ALT_CCY != requested_currency:
            detail_alt = await fetch(
                client, API, {"partNumber": part_number, "currencyCode": ALT_CCY}
            )
            det_alt_items = detail_alt.get("items") or []
            if det_alt_items:
                alt = simplify(det_alt_items[0], ALT_CCY)
                if alt.get("value") is not None:
                    item["altCurrencyCode"] = alt.get("currencyCode")
                    item["altModel"] = alt.get("model")
                    item["altValue"] = alt.get("value")
                    item.setdefault("note", "zero-in-requested-currency-see-alt")
        return item
    except Exception:
        # If alternate fetch fails, keep original item untouched
        return item


# -------------------- PURE IMPLEMENTATIONS (test here primarily) --------------------


async def pricing_get_sku_impl(
    part_number: str, currency: str | None = None, max_pages: int | None = None
) -> dict[str, Any]:
    """
    Fetch a SKU's price. If the SKU misses, fall back to fuzzy name search.

    Environment overrides (when args are omitted):
      - currency: OCI_PRICING_DEFAULT_CCY (default: 'USD')
      - max_pages: OCI_PRICING_MAX_PAGES (default: 6)

    Returns (dict):
      - On SKU hit:
          {"kind":"sku", partNumber, displayName, metricName, serviceCategory, currencyCode, model, value}
      - On name fallback:
          {"kind":"search","note":"matched-by-name","query","currency","returned","items":[...]}
      - On not found:
          {"kind":"search","note":"not-found","query","currency","returned":0,"items":[]}
      - On HTTP failure:
          {"kind":"error","note":"http-error","error","input","currency"}
    """
    pn = (part_number or "").strip()
    # ISO 4217 validation with auto-uppercasing
    cur, cur_err = _norm_currency_strict(currency, default=DEFAULT_CCY)
    if cur_err:
        return {"kind": "error", "note": cur_err, "input": currency}
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
                # Add alternate-currency reference when zero/missing
                out = await _enrich_with_alt_currency_if_zero(client, out, pn, cur)
                return out

            # 2) Fuzzy name search (bounded pages)
            all_items = [it async for it in iter_all(client, cur, pages)]
            hits = search_items(all_items, pn, limit=12, prefer_currency=cur)
            # (Optional) we could enrich each hit too, but keep this lightweight for fallback path
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
    """
    q = (query or "").strip()
    if not q:
        return {"kind": "error", "note": "empty-query", "items": []}

    # ISO 4217 validation with auto-uppercasing
    cur, cur_err = _norm_currency_strict(currency, default=DEFAULT_CCY)
    if cur_err:
        return {"kind": "error", "note": cur_err, "input": currency}

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

                    # Add alternate-currency reference when zero/missing
                    got = await _enrich_with_alt_currency_if_zero(client, got, pn, cur)

                if require_priced:
                    # Keep only items with positive value in the requested currency
                    try:
                        if got.get("model") is not None and got.get("value") is not None:
                            if float(got["value"]) > 0.0:
                                enriched.append(got)
                    except Exception:
                        # Non-numeric value -> drop when require_priced
                        pass
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
    Look up list price for a specific OCI SKU (partNumber).

    When to use:
      - Use this tool when you already know the exact SKU (e.g., "B88298").

    Parameters:
      - part_number (str, required): Oracle SKU. Case-insensitive; avoid internal spaces. Example: "B88298".
      - currency (str, optional): ISO 4217 code (three letters). **Case-insensitive**; inputs are
        auto-uppercased (e.g., "jpy" → "JPY") and validated against Babel/pycountry.
        If omitted (None), defaults to OCI_PRICING_DEFAULT_CCY ("USD" if unset).
        Invalid formats/codes (e.g., "USDT", "", "12$") return {"kind":"error","note":"invalid-currency-format"}.
      - max_pages (int, optional): Bounds pagination used only when falling back to name search. Integer 1–10. Defaults to OCI_PRICING_MAX_PAGES (6).

    Returns:
      - On success with SKU: {"kind":"sku", partNumber, displayName, metricName, serviceCategory, currencyCode, model, value, note?, altCurrencyCode?, altModel?, altValue?}
      - On fallback to name search (SKU not found): {"kind":"search", "note":"matched-by-name"|"not-found", "query", "currency", "returned", "items":[...]}
      - On HTTP or input error: {"kind":"error", "note":"http-error"|"...", "error"?, "input"?, "currency"?}

    Notes:
      - If the requested currency has no unit price or returns 0.0, the response may include alt* fields with a reference price in ALT_CCY (if configured).
      - The upstream source (cetools) is a public subset; empty items can be expected.
      - Examples — OK: "USD", "JPY", "usd", "jpy" / NG: "USDT", "12$", ""
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
    Search the OCI price list by product/name keywords when the exact SKU is unknown.

    When to use:
      - Use this to discover SKUs and prices by keywords/aliases (e.g., "Autonomous Database", "ADB", "Object Storage").

    Parameters:
      - query (str, required): Product keywords or abbreviations. Short queries (3–4 chars) match by word boundary; longer
        queries support space-insensitive and fuzzy matches. For "ADB"-like intent, both "autonomous" and "database" must match.
      - currency (str, optional): ISO 4217 code (three letters). **Case-insensitive**; inputs are
        auto-uppercased (e.g., "usd" → "USD") and validated. If omitted (None), defaults to OCI_PRICING_DEFAULT_CCY.
        Invalid formats/codes (e.g., "USDT", "", "12$") return {"kind":"error","note":"invalid-currency-format"}.
      - limit (int, optional): Max results to return. Integer 1–20. Default 12.
      - max_pages (int, optional): Pagination bound for the upstream listing. Integer 1–10. Defaults to OCI_PRICING_MAX_PAGES (6).
      - require_priced (bool, optional): If true, only return items with a positive unit price in the requested currency.

    Returns:
      - {"kind":"search", "query", "currency", "returned", "items":[...], "note":"fuzzy search; per-item price enriched via SKU endpoint"}
      - On error: {"kind":"error", ...}

    Notes:
      - Each item is simplified to include a single (model, value, currencyCode). If that value is missing or 0.0, alt* fields may include a reference price in ALT_CCY (if configured).
      - Examples — OK: "USD", "JPY", "usd", "jpy" / NG: "USDT", "12$", ""
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
    """Health check. Returns 'ok' if the server is responsive."""
    return "ok"


def main() -> None:
    """Start the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
