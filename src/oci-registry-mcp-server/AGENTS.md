# OCI Registry engineering context

## Scope and ownership

This package owns OCI container-repository discovery, creation and deletion. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/oci_registry_mcp_server/server.py): MCP registration, tool handlers and runtime entry point.
- [models.py](oracle/oci_registry_mcp_server/models.py): local request/response models and conversions.
- [Package metadata](oracle/oci_registry_mcp_server/__init__.py) and [manifest](pyproject.toml): version, dependencies and executable definitions.
- [Tests](oracle/oci_registry_mcp_server/tests): local behavior definitions; start with [test_registry_models.py](oracle/oci_registry_mcp_server/tests/test_registry_models.py), [test_registry_tools.py](oracle/oci_registry_mcp_server/tests/test_registry_tools.py).

## Setup / build / run

From the repository root, use `proto install` for pinned tools and `moon run oci-registry-mcp-server:build` for packaging. The [manifest](pyproject.toml) requires Python `>=3.13`. Read the local [README](README.md) and server `main()` for runtime transport/configuration; startup can access real services. See the [shared validation map](../../docs/agent-development.md#validation-map) for command definitions and check scope.

## Tests and validation

Use `moon run oci-registry-mcp-server:test` from the repository root for the inherited Python test task, and `moon run root:lint` after Python source changes. The manifest configures `90%` coverage. Inspect the relevant tool/model or helper tests for the requested change; shared changes also require [shared validation](../../docs/agent-development.md#validation-map). These definitions are source evidence; this documentation expansion ran no server tests or coverage.

## Architecture and dependencies

The package uses ArtifactsClient for container-repository operations. Trace `get_ocir_client()` with list/get/create/delete tools and container-repository mappings; this package does not execute image builds or container runtimes.

Authentication is implemented locally and the manifest has no Common dependency. Existing OCI SDK authentication requirements remain in [root instructions](../../AGENTS.md#mcp-server-quality-validation) and [Common’s contract](../common/README.md). Recheck credential/client paths before authentication work; this implementation departure grants no exception.

## Security and secrets handling

Repository create/delete operations mutate OCI resources. Visibility/access-related inputs and returned repository metadata need review alongside caller-specific HTTP credentials. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Repository inputs, visibility and response mappings affect tool clients and both model/tool test modules. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- Local OCI credential resolution is outside Common. This pass records the departure without migrating authentication.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle/oci_registry_mcp_server/server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Local tests](oracle/oci_registry_mcp_server/tests); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
