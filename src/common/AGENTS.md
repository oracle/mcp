# Common engineering context

## Scope and ownership

Common owns reusable Python OCI authentication ingredients. It does not own MCP tools, server listeners or service clients. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here); the package's public contract is in its [README](README.md).

## Entry points

- [auth.py](oracle_mcp_common/auth.py): configured credential resolution, profile classification, signer construction and HTTP IDCS provider/context helpers.
- [Public exports](oracle_mcp_common/__init__.py): auth option/context types, builders and resolution helpers; inspect compatibility before changing them.
- [Auth tests](oracle_mcp_common/tests/test_auth.py): credential modes, config/profile precedence, validation and HTTP exchange definitions.
- [pyproject.toml](pyproject.toml): package/dependency/coverage definitions; [CHANGELOG](CHANGELOG.md) records public changes.

## Setup / build / run

From the repository root, install the pinned tools with `proto install`, then use `moon run common:build` when checking packaging. Moon manages the locked project environment; direct `uv sync --directory src/common --locked --all-extras --dev` is also defined by the native environment configuration. Read the [validation map](../../docs/agent-development.md#validation-map) for source definitions and scope. Running a server listener is not applicable to this library.

## Tests and validation

Use `moon run common:test` for package tests and `moon run root:lint` after Python changes. Shared auth changes require the broader root checks and affected consumer review, including `moon run :test` and `moon run root:combine-coverage`; Common-only tests do not validate every caller. The manifest configures 90% coverage; no tests/coverage have been executed by this guide adoption.

## Architecture and dependencies

`build_auth_context()` returns config/signer ingredients; servers retain client type, lifecycle, user-agent derivation and retry/circuit-breaker choices. `build_idcs_http_auth()` creates provider policy and `context_for()` derives explicit caller-token auth; listener startup, request-context retrieval and OCI client construction stay with the server. The README defines input precedence, explicit principal modes and profile-backed `auto`; do not infer automatic principal probing.

Declared consumers at this baseline are [API](../oci-api-mcp-server/pyproject.toml), [Cloud](../oci-cloud-mcp-server/pyproject.toml), [Database](../oci-database-mcp-server/pyproject.toml), [DB Observability](../oci-db-observability-mcp-server/pyproject.toml) and [Document Understanding](../oci-document-understanding-mcp-server/pyproject.toml). API, Cloud and Database also declare Common edges in their package Moon files; the two newer consumers have no explicit package Moon file. Manifests and graph edges are different sources to recheck, and declarations alone do not establish runtime use; other servers, including Compute, are not assumed migrated.

## Security and secrets handling

The [profile contract](README.md#profile-backed-authentication) requires a security token directly in the selected profile; inherited DEFAULT tokens and silent fallback after configured-token failure are rejected. The [HTTP contract](README.md#http-idcs-authentication) keeps request signers/clients caller-specific and passes the token explicitly. Use the existing mocked auth tests and synthetic files; keep secret values out of diagnostics. Common does not retrieve global FastMCP request context.

## Change impact

Public exports, configuration precedence, supported modes and aliases affect declared consumers. Inspect their call sites/manifests and relevant tests before changing the library; apply root shared-change validation and [contribution/changelog guidance](../../AGENTS.md#changelog-guidance). Review README and changelog for public API/config changes.

## Known gaps

- Not every Python server has migrated; consumer declarations must be inspected for each shared change.
- [README requirements](README.md#package-requirements) and [manifest dependencies](pyproject.toml) differ on OCI/FastMCP versions. Use the manifest for install definitions and report the discrepancy without inventing a new version policy.
- Configured test thresholds and source-reviewed contracts are not executed validation results. See [shared gaps](../../docs/agent-development.md#known-gaps).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Integrating Common into a server or addressing a missing shared capability | [Shared authentication guide and ledger](../../docs/authentication.md) | Root auth requirements and Common public API contract; applicable consumer guide | Linked consumer manifests/call sites and [documentation outcome](../../docs/plans/shared-authentication-context/outcome.md); actual integration checks recorded separately |
| **Know:** Changing a mode, profile input or auth precedence | [README auth contract](README.md#authentication-module), [auth.py](oracle_mcp_common/auth.py) | Root quality requirements; public exports/compatibility | [Auth tests](oracle_mcp_common/tests/test_auth.py), relevant consumer call sites |
| **Know:** Changing HTTP provider or token handling | [HTTP contract](README.md#http-idcs-authentication), [auth.py](oracle_mcp_common/auth.py) | Caller-specific context; server owns transport/client lifecycle | [HTTP test definitions](oracle_mcp_common/tests/test_auth.py); actual runs recorded separately |
| **Know:** Comparing Common contracts with Compute's current authentication | [Compute authentication explanation](../oci-compute-mcp-server/docs/authentication.md), [applicable Compute guide](../oci-compute-mcp-server/AGENTS.md) | Root auth requirements, [README auth contract](README.md#authentication-module) and [HTTP contract](README.md#http-idcs-authentication); needed only for this comparison | [Local source/check definitions and limits](../oci-compute-mcp-server/docs/authentication.md#supporting-definitions-and-evidence-limits) |
| **Do:** Authoring or maintaining Common context | [Repository context conventions](../../docs/agent-context.md) | Root and this guide; relevant native contract/source definitions | [Separate application outcome](../../docs/plans/apply-agent-context-guide/outcome.md); older adoption results retain their recorded scope |
| **Do:** Building or validating a shared change | [Validation map](../../docs/agent-development.md#validation-map), [manifest](pyproject.toml) | Root/shared scope and current consumer declarations | Native run reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

Follow [CONTRIBUTING](../../CONTRIBUTING.md). This pass's Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md); other changes keep their own scoped records. A Common fix does not imply an unrelated whole-repository authentication migration.
