# OCI Pricing MCP Server (oci-pricing-mcp-server.py)

A Python-based MCP (Model Context Protocol) server that fetches **Oracle Cloud Infrastructure (OCI)** service pricing from Oracle’s public **Price List API (cetools)**.
This project is a **proof of concept** for MCP integrations. While not production-hardened, it is **stateless, credential-free, and suitable for day-to-day internal use** in MCP clients.

### ⚠️ Important pricing disclaimer

* **Informational only** — responses are **not quotes or invoices**. Pricing can change and may vary by **region**, **commitment/discounts**, and **tenancy-specific terms**. Taxes and surcharges are not included.
* The Oracle **Price List API** is a **public subset**. Some items may return **`0.00`** (e.g., free-tier-only or missing localization). The server attempts to flag such cases with `note: "zero-price-or-free-tier-only"` when detected, but **always verify** in the OCI Console or official materials before making decisions.
* This server **does not** know your account’s negotiated pricing and **does not** perform currency conversion; it requests the currency you specify (or the configured default) and surfaces what the API returns.

**Oracle Price List API reference:**
[https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/signingup\_topic-Estimating\_Costs.htm#accessing\_list\_pricing](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/signingup_topic-Estimating_Costs.htm#accessing_list_pricing)

## Overview

`oci-pricing-mcp-server.py` (FastMCP-based) exposes tools to:

* Look up pricing by **SKU (part number)**
* **Fuzzy-search** pricing by **product name or alias**
* Return **consistent JSON** suitable for MCP clients

If you omit the currency when asking (e.g., “List Object Storage prices”), the server uses a **default currency**, configurable via environment variables (see **Environment Variables**).

## Features

* **SKU Pricing**
  Fetch pricing for a specific part number (e.g., `B93113`).

  **Example prompts**

  * “Price for **SKU B93113** in **JPY**.”
  * “Look up **part number B93113** (USD).”

* **Fuzzy Product Search**
  Search by product name or common alias (e.g., `ADB → Autonomous Database`, `OSS → Object Storage`, `OKE → Kubernetes`). Each hit is re-fetched by SKU to enrich pricing in the requested currency.

  **Example prompts**

  * “**Object Storage** pricing in **JPY**.”
  * “**Compute** pricing in **USD**, **priced items only**.”

* **Structured Responses**
  Responses include `currencyCode` (falls back to the requested/default currency) and a `kind` field: `"sku"`, `"search"`, or `"error"`.
  Items that appear **free-tier-only / zero-priced** may include `note: "zero-price-or-free-tier-only"`.

  **Example prompts**

  * “List **Object Storage** prices in **JPY**; ensure each item has **currencyCode**.”
  * “Show **Compute** pricing in **USD** and include the **kind** field.”

* **Health Check**
  `ping` returns `"ok"`.

  **Example prompts**

  * “Ping the pricing server.”
  * “Check if the server is alive.”

**Operational notes**

* **No credentials required** (uses a public API over HTTPS).
* **Stateless** and side-effect-free.
* **Network robustness**: light retry with exponential backoff and request timeout.
* **Currency handling**: normalizes ISO codes and ensures `currencyCode` is present (falls back to the requested or default currency).

## Prerequisites

* Python **3.11+**
* Internet access (calls Oracle public API)
* Dependencies via `pyproject.toml` / `uv.lock` or `pip`

## Installation

### Option A: pip

```bash
pip install fastmcp httpx
```

### Option B: uv (recommended, reproducible)

```bash
# Install uv once (e.g., via Homebrew or the official installer)
uv sync --frozen     # uses pyproject.toml / uv.lock
```

## Usage

Run with stdio transport:

```bash
# pip env
python oci-pricing-mcp-server.py

# or uv env
uv run python oci-pricing-mcp-server.py
```

## MCP Server Configuration

Exact steps depend on your MCP client. Typical stdio setup (example: **Claude Desktop on Windows**):

```json
{
  "mcpServers": {
    "oci-pricing": {
      "command": "C:\\Python\\python.exe",
      "args": [
        "C:\\Users\\user1\\oci-pricing-mcp-server\\oci-pricing-mcp-server.py"
      ]
    }
  }
}
```

Step-by-step guide (Claude Desktop: add local MCP servers):
[https://support.anthropic.com/en/articles/9793354-connect-local-mcp-servers-to-claude-desktop](https://support.anthropic.com/en/articles/9793354-connect-local-mcp-servers-to-claude-desktop)

## Environment Variables

These variables control **runtime defaults and behavior** (they are **optional**):

* `OCI_PRICING_DEFAULT_CCY` – default currency code (e.g., `JPY`; default: `USD`)
* `OCI_PRICING_MAX_PAGES` – page-follow upper bound for listing (default: `6`, clamped to `1–10`)
* `OCI_PRICING_HTTP_TIMEOUT` – HTTP timeout in seconds (default: `25`)
* `OCI_PRICING_RETRIES` – transient retry count (default: `2`; total tries = `1 + retries`)
* `OCI_PRICING_BACKOFF` – exponential backoff base in seconds (default: `0.5`)
* `PROBE_CCY` – **convenience fallback** for default currency (originally for tests; the server checks this as a fallback to `OCI_PRICING_DEFAULT_CCY`)

Test-only helpers (used by functional tests; **not needed** for normal use):

* `PROBE_SKU_OK` – known-good SKU (default: `B93113`)
* `PROBE_SKU_MISSING` – likely missing SKU (default: `B88298`)

**Example (Claude config) to default to JPY:**

```json
{
  "mcpServers": {
    "oci-pricing": {
      "command": "C:\\Python\\python.exe",
      "args": [
        "C:\\Users\\user1\\oci-pricing-mcp-server\\oci-pricing-mcp-server.py"
      ],
      "env": {
        "OCI_PRICING_DEFAULT_CCY": "JPY"
      }
    }
  }
}
```

## API Tools

1. **`pricing_get_sku(part_number, currency=None, max_pages=None)`**
   Look up pricing for a specific part number.
   If `currency`/`max_pages` are omitted, the server applies env defaults (`OCI_PRICING_DEFAULT_CCY`, `OCI_PRICING_MAX_PAGES`).

   * **Hit:** `{"kind":"sku", ...}` with `model`, `value`, `currencyCode`
   * **Fallback / not found:** `{"kind":"search","note":"matched-by-name"|"not-found", ...}`
   * **Error:** `{"kind":"error", ...}`

2. **`pricing_search_name(query, currency=None, limit=12, max_pages=None, require_priced=False)`**
   Fuzzy-search by product name/alias, then re-fetch each result by SKU to enrich pricing in the requested currency.
   If `currency`/`max_pages` are omitted, env defaults apply.

   * 3–4 chars → **word-boundary** match
   * ≥5 chars → **space-insensitive substring** + **similarity**
   * Aliases (e.g., `adb→autonomous database`, `oss→object storage`, `oke→kubernetes engine`)
   * `limit` **clamped to ≤20**; `max_pages` **clamped to 1–10**
   * `require_priced=True` → keep only items with `model` + `value`
   * Items with `value == 0` may include `note: "zero-price-or-free-tier-only"` if detected.

3. **`ping()`**
   Health check; returns `"ok"`.

## Natural Language Examples

> Many MCP clients map user text to tool calls. Examples:

**SKU lookup**

* “Show the price for **SKU B93113** in **JPY**.”
* “Look up **part number B93113** (USD).”

**Product search (fuzzy)**

* “**Object Storage** pricing in **JPY**.”
* “**OKE** (Kubernetes) pricing.”

**Filters & options**

* “**Compute** pricing in **JPY**, **priced items only**.”
* “**ADB**-related SKUs in **USD**.”

## Testing

```bash
# pip
python -m unittest -v

# uv
uv run -m unittest -v
```

### Docker (optional)

```bash
# Build
docker build -t oci-pricing-mcp:dev .

# Run the server (stdio)
docker run --rm -it --name oci-pricing-mcp oci-pricing-mcp:dev

# Run tests inside the container (with probe envs)
docker run --rm -it \
  -e PROBE_SKU_OK=B93113 \
  -e PROBE_CCY=JPY \
  oci-pricing-mcp:dev \
  python -m unittest discover -s . -p 'test_*.py' -v
```