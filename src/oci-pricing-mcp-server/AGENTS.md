# OCI Pricing engineering context

## Scope and ownership

This package owns credential-free public OCI Price List API lookup, fuzzy name search and currency-aware result shaping. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oci-pricing-mcp-server.py): MCP registration, tool handlers and runtime entry point.
- [Manifest](pyproject.toml): dependencies, Python requirement and available packaging/check configuration.
- [test_oci_pricing_mcp_server.py](test_oci_pricing_mcp_server.py): available test definitions; inspect live prerequisites before execution.

## Setup / build / run

This package is excluded from Moon. From its directory, [README](README.md) defines dependency setup and `python oci-pricing-mcp-server.py` for stdio startup; [pyproject.toml](pyproject.toml) requires Python >=3.11. Inspect the packaging gap below before relying on the declared console script.

## Tests and validation

The README defines `python -m unittest -v` and `uv run -m unittest -v` from this package directory. [test_oci_pricing_mcp_server.py](test_oci_pricing_mcp_server.py) mixes mocked boundary checks with functional API calls; running the full suite can access the public network. The manifest configures 90% coverage, but the documented unittest commands do not collect/enforce it. This expansion executes none of these checks.

## Architecture and dependencies

The standalone script uses httpx against Oracle’s public cetools API. `_safe_next_url()` bounds API continuation URLs; fetch/retry/page limits, SKU/name lookup and optional currency validation are local. Returned list prices are not negotiated account prices or currency conversions.

## Security and secrets handling

No OCI credential/signing path is needed for this public API. Preserve allowed-host/HTTPS continuation checks and request/page bounds. Some functional tests use the public network and may skip on empty results or network errors. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Price-block normalization, currency choices, fuzzy matching, retry bounds and result fields affect caller interpretation. Review both mocked cases and live functional prerequisites. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- The manifest declares oci_pricing_mcp.entry:main and a src/ package layout, but no corresponding tracked src/oci_pricing_mcp package exists. Direct-script startup and package installation are separate unresolved routes.
- Documented unittest commands do not establish enforcement of the configured 90% threshold.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oci-pricing-mcp-server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Test definitions](test_oci_pricing_mcp_server.py); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
