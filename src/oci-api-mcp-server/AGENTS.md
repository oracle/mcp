# OCI API engineering context

## Scope and ownership

This package owns OCI CLI command discovery, help and execution. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/oci_api_mcp_server/server.py): MCP registration, tool handlers and runtime entry point.
- [Denylist](oracle/oci_api_mcp_server/denylist.py): command-path filtering and ambiguous-input handling
- [Audit logger](oracle/oci_api_mcp_server/utils.py): rotating audit-log configuration
- [Package Moon task](moon.yml): Common dependency edge and denylist-generator test input
- [Package metadata](oracle/oci_api_mcp_server/__init__.py) and [manifest](pyproject.toml): version, dependencies and executable definitions.
- [Tests](oracle/oci_api_mcp_server/tests): local behavior definitions; start with [test_oci_api_tools.py](oracle/oci_api_mcp_server/tests/test_oci_api_tools.py).

## Setup / build / run

From the repository root, use `proto install` for pinned tools and `moon run oci-api-mcp-server:build` for packaging. The [manifest](pyproject.toml) requires Python `>=3.13`. Read the local [README](README.md) and server `main()` for runtime transport/configuration; startup can access real services. See the [shared validation map](../../docs/agent-development.md#validation-map) for command definitions and check scope.

## Tests and validation

Use `moon run oci-api-mcp-server:test` from the repository root for the inherited Python test task, and `moon run root:lint` after Python source changes. The manifest configures `90%` coverage. Inspect the relevant tool/model or helper tests for the requested change; shared changes also require [shared validation](../../docs/agent-development.md#validation-map). These definitions are source evidence; this documentation expansion ran no server tests or coverage.

## Architecture and dependencies

The server is stdio-only and launches a pinned OCI CLI from its own Python environment with argv and `shell=False`. Common supplies profile/config/auth classification helpers; this package translates modes to CLI arguments and sets `OCI_SDK_APPEND_USER_AGENT`. `OCI_CLI_AUTH` remains authoritative. Inspect command parsing, server-managed global options and denylist matching together.

The package declares Common; read [its contract](../common/README.md) and [guide](../common/AGENTS.md) for auth ownership and shared-change impact. A declared dependency alone does not establish every supported path’s coverage.

## Security and secrets handling

This package is the root policy’s explicit OCI CLI subprocess exception. Preserve executable pinning, disabled CLI rc files, noninteractive stdin, managed auth/config/endpoint options and denylist controls. Command execution can mutate OCI resources; audit logs can contain command data. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Auth-mode translation, denylist inputs and CLI help/execution behavior affect every exposed command. Review the denylist generator and command tests with changes to filtering. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle/oci_api_mcp_server/server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Local tests](oracle/oci_api_mcp_server/tests); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
