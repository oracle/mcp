# OCI Pricing engineering context

## Scope and ownership

This package owns credential-free public OCI Price List API lookup, fuzzy name search and currency-aware result shaping. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/oci_pricing_mcp_server/server.py): MCP registration, tool handlers and runtime entry point.
- [Manifest](pyproject.toml): dependencies, Python requirement and available packaging/check configuration.
- [Unit tests](oracle/oci_pricing_mcp_server/tests/): deterministic package-local checks. [Live probes](tests/integration/test_public_api.py) are explicitly enabled separately.

## Setup / build / run

This package uses inherited Moon Python tasks. [README](README.md#development-and-testing) owns setup and validation commands; [pyproject.toml](pyproject.toml) requires Python >=3.11 and configures Hatchling. Install with `uv sync --locked --all-extras --dev` from this directory, then run `uv run --locked oracle.oci-pricing-mcp-server`. Package metadata requires installation before import. The old command and standalone script remain thin launchers for one release; see the README migration notes.

## Tests and validation

From the repository root, run `moon run oci-pricing-mcp-server:test`, `oci-pricing-mcp-server:lock-check`, `oci-pricing-mcp-server:build` and `oci-pricing-mcp-server:install-check`, plus root lint and aggregate coverage as required by the shared validation map. From this directory, `uv run --locked pytest` selects package-local offline tests and enforces the manifest's 90% threshold with branch coverage. Unit fixtures block real HTTP sends and retry delays. Live probes are outside default discovery and require the explicit README command with `OCI_PRICING_LIVE_TESTS=1`; their data-dependent skips do not establish deterministic unit coverage.

## Architecture and dependencies

The canonical server module uses httpx against Oracle’s public cetools API. `_safe_next_url()` bounds API continuation URLs; fetch/retry/page limits, SKU/name lookup and optional currency validation are local. Returned list prices are not negotiated account prices or currency conversions.

## Security and secrets handling

No OCI credential/signing path is needed for this public API. Preserve allowed-host/HTTPS continuation checks and request/page bounds. Opt-in integration probes use the public network and may skip on empty results or network errors. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Price-block normalization, currency choices, fuzzy matching, retry bounds and result fields affect caller interpretation. Review both mocked cases and live functional prerequisites. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle/oci_pricing_mcp_server/server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Unit test definitions](oracle/oci_pricing_mcp_server/tests/); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
