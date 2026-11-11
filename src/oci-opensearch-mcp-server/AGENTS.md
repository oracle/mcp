# OCI OpenSearch engineering context

## Scope and ownership

This package owns OCI OpenSearch control-plane cluster lifecycle and work-request discovery. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/oci_opensearch_mcp_server/server.py): MCP registration, tool handlers and runtime entry point.
- [models.py](oracle/oci_opensearch_mcp_server/models.py): local request/response models and conversions.
- [Client factory](oracle/oci_opensearch_mcp_server/client_factory.py): local profile/signers and OpenSearch client
- [SDK adapters](oracle/oci_opensearch_mcp_server/sdk_adapters.py): SDK operation compatibility
- [Resource loader](oracle/oci_opensearch_mcp_server/scripts.py): packaged API/work-request/tool-surface guides
- [Package metadata](oracle/oci_opensearch_mcp_server/__init__.py) and [manifest](pyproject.toml): version, dependencies and executable definitions.
- [Tests](oracle/oci_opensearch_mcp_server/tests): local behavior definitions; start with [test_client_factory.py](oracle/oci_opensearch_mcp_server/tests/test_client_factory.py), [test_opensearch_tools.py](oracle/oci_opensearch_mcp_server/tests/test_opensearch_tools.py).

## Setup / build / run

From the repository root, use `proto install` for pinned tools and `moon run oci-opensearch-mcp-server:build` for packaging. The [manifest](pyproject.toml) requires Python `>=3.13`. Read the local [README](README.md) and server `main()` for runtime transport/configuration; startup can access real services. See the [shared validation map](../../docs/agent-development.md#validation-map) for command definitions and check scope.

## Tests and validation

Use `moon run oci-opensearch-mcp-server:test` from the repository root for the inherited Python test task, and `moon run root:lint` after Python source changes. The manifest configures `90%` coverage. Inspect the relevant tool/model or helper tests for the requested change; shared changes also require [shared validation](../../docs/agent-development.md#validation-map). These definitions are source evidence; this documentation expansion ran no server tests or coverage.

## Architecture and dependencies

client_factory.py owns configuration/signers; sdk_adapters.py isolates OCI SDK method differences. server.py validates snake_case request bodies, retry tokens and asynchronous operation responses. Packaged guides describe the control-plane tool surface and work requests; this package is not a cluster data-plane search client.

Authentication is implemented locally and the manifest has no Common dependency. Existing OCI SDK authentication requirements remain in [root instructions](../../AGENTS.md#mcp-server-quality-validation) and [Common’s contract](../common/README.md). Recheck credential/client paths before authentication work; this implementation departure grants no exception.

## Security and secrets handling

Cluster create/update/delete/resize/backup tools mutate resources. Preserve payload validation and retry/idempotency behavior; local tests mock SDK/client boundaries and do not validate a deployed cluster. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

SDK adapters, cluster request bodies, retry-token derivation and work-request envelopes affect lifecycle callers. Review client-factory/adapter/tool tests and packaged guides together. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- Local OCI credential resolution is outside Common. This pass records the departure without migrating authentication.
- The client factory falls back to API-key signing after a security-token construction failure. This differs from Common’s configured-token failure behavior and is not an approved exception.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle/oci_opensearch_mcp_server/server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Local tests](oracle/oci_opensearch_mcp_server/tests); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
