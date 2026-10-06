# OCI Recovery Service engineering context

## Scope and ownership

This package owns Recovery Service protected-database discovery, database/backup inventory and dashboard summaries. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/oci_recovery_mcp_server/server.py): MCP registration, tool handlers and runtime entry point.
- [models.py](oracle/oci_recovery_mcp_server/models.py): local request/response models and conversions.
- [Dashboard prompt](oracle/oci_recovery_mcp_server/data/prompts/oci_recovery_service_dashboard.txt): packaged Recovery dashboard guidance
- [Package metadata](oracle/oci_recovery_mcp_server/__init__.py) and [manifest](pyproject.toml): version, dependencies and executable definitions.
- [Tests](oracle/oci_recovery_mcp_server/tests): local behavior definitions; start with [test_recovery_database_tools.py](oracle/oci_recovery_mcp_server/tests/test_recovery_database_tools.py), [test_recovery_tools.py](oracle/oci_recovery_mcp_server/tests/test_recovery_tools.py).

## Setup / build / run

From the repository root, use `proto install` for pinned tools and `moon run oci-recovery-mcp-server:build` for packaging. The [manifest](pyproject.toml) requires Python `>=3.13`. Read the local [README](README.md) and server `main()` for runtime transport/configuration; startup can access real services. See the [shared validation map](../../docs/agent-development.md#validation-map) for command definitions and check scope.

## Tests and validation

Use `moon run oci-recovery-mcp-server:test` from the repository root for the inherited Python test task, and `moon run root:lint` after Python source changes. The manifest configures `90%` coverage. Inspect the relevant tool/model or helper tests for the requested change; shared changes also require [shared validation](../../docs/agent-development.md#validation-map). These definitions are source evidence; this documentation expansion ran no server tests or coverage.

## Architecture and dependencies

server.py coordinates Recovery, Database, Identity, Work Requests, Monitoring, Limits and OneSubscription clients, compartment expansion and summaries. Local auth/session helpers select profiles and signers; inspect every client factory when changing credentials. The packaged dashboard prompt complements these tools.

Authentication is implemented locally and the manifest has no Common dependency. Existing OCI SDK authentication requirements remain in [root instructions](../../AGENTS.md#mcp-server-quality-validation) and [Common’s contract](../common/README.md). Recheck credential/client paths before authentication work; this implementation departure grants no exception.

## Security and secrets handling

Recovery/backup/usage results and logs may reveal sensitive infrastructure data. Inspect logging wrappers and caller-specific HTTP signer paths along with profile handling. Unit/client mocks are separate from live backup/recovery verification. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Compartment expansion, cross-service summaries, client construction and dashboard content affect multiple workflows. Review the recovery and database tool tests together. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- Local OCI credential resolution is outside Common. This pass records the departure without migrating authentication.
- The README says local development uses Common, but the manifest has no Common dependency and server.py resolves credentials locally. Preserve the root requirement and report this source mismatch.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle/oci_recovery_mcp_server/server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Local tests](oracle/oci_recovery_mcp_server/tests); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
