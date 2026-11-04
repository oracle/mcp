# OCI Pricing MCP Server

A Python-based MCP (Model Context Protocol) server that fetches **Oracle Cloud Infrastructure (OCI)** service pricing from Oracle’s public **Price List API (cetools)**.
This project is a **proof of concept** for MCP integrations. While not production-hardened, it is **stateless, credential-free, and suitable for day-to-day internal use** in MCP clients.

### ⚠️ Important pricing disclaimer

* **Informational only** — responses are **not quotes or invoices**. Pricing can change and may vary by **region**, **commitment/discounts**, and **tenancy-specific terms**. Taxes and surcharges are not included.
* The Oracle **Price List API** is a **public subset**. Some items may return **`0.00`** (e.g., free-tier-only or missing localization). The server attempts to flag such cases with `note: "zero-price-or-free-tier-only"` when detected, but **always verify** in the OCI Console or official materials before making decisions.
* This server **does not** know your account’s negotiated pricing and **does not** perform currency conversion; it requests the currency you specify (or the configured default) and surfaces what the API returns.

**Oracle Price List API reference:**
[https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/signingup\_topic-Estimating\_Costs.htm#accessing\_list\_pricing](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/signingup_topic-Estimating_Costs.htm#accessing_list_pricing)

## Overview

`oracle.oci-pricing-mcp-server` (FastMCP-based) exposes tools to:

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

### Install from this checkout

From `src/oci-pricing-mcp-server`:

```bash
# Installs the project and all declared runtime dependencies
python3 -m pip install .

# Or use the committed dependency lock, including development dependencies
uv sync --locked --all-extras --dev
```

The distribution is now named `oracle.oci-pricing-mcp-server` (previously
`oci-pricing-mcp-server`). When migrating an environment that has the old
distribution installed, uninstall that distribution before installing this one.
Python **3.11+** remains supported. OCI credentials are not required.

## Usage

Run the installed stdio command:

```bash
oracle.oci-pricing-mcp-server

# From the development checkout
uv run --locked oracle.oci-pricing-mcp-server
```

For one release, `oci-pricing-mcp` remains an alias for the canonical command,
and `python3 oci-pricing-mcp-server.py` remains a compatibility launcher after
installing the project. Both launch the same package implementation; the script
is no longer a self-contained server. Migrate clients to the canonical command.

## MCP Server Configuration

After installing the project into an environment available on your client's
`PATH`, use this portable stdio configuration:

```json
{
  "mcpServers": {
    "oci-pricing": {
      "command": "oracle.oci-pricing-mcp-server",
      "args": []
    }
  }
}
```

## Environment Variables

These variables control **runtime defaults and behavior** (they are **optional**):

* `OCI_PRICING_DEFAULT_CCY` – default currency code (e.g., `JPY`; default: `USD`)
* `OCI_PRICING_MAX_PAGES` – page-follow upper bound for listing (default: `6`, clamped to `1–10`)
* `OCI_PRICING_HTTP_TIMEOUT` – HTTP timeout in seconds (default: `25`)
* `OCI_PRICING_RETRIES` – transient retry count (default: `2`; total tries = `1 + retries`)
* `OCI_PRICING_BACKOFF` – exponential backoff base in seconds (default: `0.5`)
* `OCI_PRICING_ALT_CCY` – optional alternate currency for a reference price when the requested price is zero or missing; no conversion is performed

Test-only helpers (used by functional tests; **not needed** for normal use):

* `PROBE_SKU_OK` – known-good SKU (default: `B93113`)
* `PROBE_SKU_MISSING` – likely missing SKU (default: `B88298`)
* `PROBE_CCY` – currency used by live probes (default: `JPY`); does not change the server default
* `PROBE_QUERY` – search term used by live probes (default: `Compute`)

**Example client configuration to default to JPY:**

```json
{
  "mcpServers": {
    "oci-pricing": {
      "command": "oracle.oci-pricing-mcp-server",
      "args": [],
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

## Development and testing

Implementation lives in `oracle/oci_pricing_mcp_server/server.py`; package
metadata reads the installed distribution version. Install the project before
importing it. Default unit tests live alongside the package, mock public HTTP
and retry delays, and fail if they attempt a real HTTP send. They collect branch
coverage and enforce the configured **90%** minimum.

From the repository root, use the pinned toolchain and inherited Moon targets:

```bash
proto install moon --immutable-lockfile
moon setup
moon run oci-pricing-mcp-server:test
moon run oci-pricing-mcp-server:lock-check oci-pricing-mcp-server:build oci-pricing-mcp-server:install-check
moon run root:lint
moon run root:combine-coverage
```

The test target writes `.coverage.oci-pricing-mcp-server` at the repository root.
Aggregation combines the reports present from that run; a Pricing-only report
does not establish coverage for other servers. See the repository validation
map for full-workspace checks.

From this package directory, the native equivalent for unit tests is:

```bash
uv run --locked pytest
uv build --clear
```

### Optional public API probes

Live probes are outside default discovery in `tests/integration/`. They require
internet access to Oracle's public Price List API and current public pricing
data. The dataset can legitimately produce empty or zero-priced results, and
some probes skip those cases. Enable them explicitly from this package:

```bash
OCI_PRICING_LIVE_TESTS=1 uv run --locked pytest tests/integration -m integration --no-cov -v
```

Without `OCI_PRICING_LIVE_TESTS=1`, explicit integration-suite invocation skips
these probes. They are separate from deterministic unit coverage.

### Container

Build using the committed `Containerfile` (Docker and Podman accept `-f`):

```bash
docker build -f Containerfile -t oci-pricing-mcp:dev .
docker run --rm -i --network=none oci-pricing-mcp:dev
```

The image installs the package non-editably with locked production dependencies
and runs the canonical command as UID 10001. Initialization, tool discovery and
`ping` need neither OCI credentials nor pricing API access. Pricing lookups
require outbound HTTPS, so omit `--network=none` for normal pricing use. Use
`-i` without allocating a TTY for MCP stdio clients.

The protocol smoke helper runs initialization, discovers all three tools, and
calls `ping` against a command, without making a pricing lookup:

```bash
uv run --locked python3 tests/stdio_smoke.py oracle.oci-pricing-mcp-server
uv run --locked python3 tests/stdio_smoke.py docker run --rm -i --network=none oci-pricing-mcp:dev
```
