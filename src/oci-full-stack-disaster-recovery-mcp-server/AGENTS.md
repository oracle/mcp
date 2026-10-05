# OCI Full Stack Disaster Recovery engineering context

## Scope and ownership

This package owns FSDR protection-group, plan, execution and packaged recovery-workflow tools/prompts. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/oci_fsdr_mcp_server/server.py): MCP registration, tool handlers and runtime entry point.
- [models.py](oracle/oci_fsdr_mcp_server/models.py), [test_models.py](tests/test_models.py): local request/response models and conversions.
- [Auth/client factory](oracle/oci_fsdr_mcp_server/auth.py): profile-keyed clients and API-key/session-token handling
- [Defaults](oracle/oci_fsdr_mcp_server/consts.py): region-profile/auth configuration
- [Workflow prompts](oracle/oci_fsdr_mcp_server/data/prompts): packaged operational prompt content
- [Package metadata](oracle/oci_fsdr_mcp_server/__init__.py) and [manifest](pyproject.toml): version, dependencies and executable definitions.
- [Tests](tests): local behavior definitions; start with [test_auth.py](tests/test_auth.py), [test_models.py](tests/test_models.py).

## Setup / build / run

From the repository root, use `proto install` for pinned tools and `moon run oci-full-stack-disaster-recovery-mcp-server:build` for packaging. The [manifest](pyproject.toml) requires Python `>=3.13`. Read the local [README](README.md) and server `main()` for runtime transport/configuration; startup can access real services. See the [shared validation map](../../docs/agent-development.md#validation-map) for command definitions and check scope.

## Tests and validation

Use `moon run oci-full-stack-disaster-recovery-mcp-server:test` from the repository root for the inherited Python test task, and `moon run root:lint` after Python source changes. The manifest configures `90%` coverage. Inspect the relevant tool/model or helper tests for the requested change; shared changes also require [shared validation](../../docs/agent-development.md#validation-map). These definitions are source evidence; this documentation expansion ran no server tests or coverage.

## Architecture and dependencies

auth.py caches DisasterRecoveryClient instances by named OCI profile for primary/standby regions. consts.py owns profile/auth defaults; server.py exposes tool operations and workflow prompts loaded from package data. The console executable is `oracle.oci-fsdr-mcp-server`, while the Moon project target uses the directory name `oci-full-stack-disaster-recovery-mcp-server`.

Authentication is implemented locally and the manifest has no Common dependency. Existing OCI SDK authentication requirements remain in [root instructions](../../AGENTS.md#mcp-server-quality-validation) and [Common’s contract](../common/README.md). Recheck credential/client paths before authentication work; this implementation departure grants no exception.

## Security and secrets handling

Switchover, failover, drill and member/plan changes affect recovery resources across regions. Preserve explicit target-profile selection; unit tests and source review do not authorize disaster-recovery execution. Cached clients are configured-profile clients, not HTTP caller clients. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Profile selection, raw SDK-call inputs, response models and packaged prompts affect cross-region workflows. Review auth/models/server tests together with prompts. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- Local OCI credential resolution is outside Common. This pass records the departure without migrating authentication.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle/oci_fsdr_mcp_server/server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Local tests](tests); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
