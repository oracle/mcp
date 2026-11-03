# OCI IoT Platform engineering context

## Scope and ownership

This package owns IoT control-plane resources, domain/twin resolution, data-plane access and agent workflows. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/oci_iot_mcp_server/server.py): MCP registration, tool handlers and runtime entry point.
- [models.py](oracle/oci_iot_mcp_server/models.py), [tool_models.py](oracle/oci_iot_mcp_server/tool_models.py): local request/response models and conversions.
- [Control plane](oracle/oci_iot_mcp_server/control_plane.py): OCI IoT resource operations
- [Data plane](oracle/oci_iot_mcp_server/data_plane.py): ORDS credentials, token minting/cache and data requests
- [Resolvers](oracle/oci_iot_mcp_server/resolvers.py): friendly identifier and twin selection
- [Domain context](oracle/oci_iot_mcp_server/domain_context.py): domain endpoint/region derivation
- [Client/auth](oracle/oci_iot_mcp_server/client.py): configured client cache; local credential logic lives in auth.py
- [Agent workflows](oracle/oci_iot_mcp_server/agent_workflows.py): readiness/lifecycle orchestration
- [Polling](oracle/oci_iot_mcp_server/polling.py): wait behavior
- [Package metadata](oracle/oci_iot_mcp_server/__init__.py) and [manifest](pyproject.toml): version, dependencies and executable definitions.
- [Tests](oracle/oci_iot_mcp_server/tests): local behavior definitions; start with [test_agent_workflows.py](oracle/oci_iot_mcp_server/tests/test_agent_workflows.py), [test_client.py](oracle/oci_iot_mcp_server/tests/test_client.py).

## Setup / build / run

From the repository root, use `proto install` for pinned tools and `moon run oci-iot-mcp-server:build` for packaging. The [manifest](pyproject.toml) requires Python `>=3.13`. Read the local [README](README.md) and server `main()` for runtime transport/configuration; startup can access real services. See the [shared validation map](../../docs/agent-development.md#validation-map) for command definitions and check scope.

## Tests and validation

Use `moon run oci-iot-mcp-server:test` from the repository root for the inherited Python test task, and `moon run root:lint` after Python source changes. The manifest configures `90%` coverage. Inspect the relevant tool/model or helper tests for the requested change; shared changes also require [shared validation](../../docs/agent-development.md#validation-map). These definitions are source evidence; this documentation expansion ran no server tests or coverage.

## Architecture and dependencies

control_plane.py wraps OCI IoT SDK operations; data_plane.py handles IoT data APIs and ORDS token access. resolvers.py and domain_context.py connect friendly selectors/twins to concrete domain endpoints; polling.py and agent_workflows.py compose readiness/lifecycle operations. Local auth.py implements `OCI_IOT_AUTH_TYPE`; client.py caches configured-profile/auth-type clients.

Authentication is implemented locally and the manifest has no Common dependency. Existing OCI SDK authentication requirements remain in [root instructions](../../AGENTS.md#mcp-server-quality-validation) and [Common’s contract](../common/README.md). Recheck credential/client paths before authentication work; this implementation departure grants no exception.

## Security and secrets handling

Data-plane tokens, ORDS credentials, device commands and twin payloads require their own boundaries beyond OCI control-plane auth. Review token minting/cache scope and derived domain endpoints in data_plane.py/domain_context.py. Use the module-specific mocks; provisioning and device-command calls can mutate resources. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Friendly identifier rules, domain endpoint derivation, token/cache behavior, polling and workflow result envelopes affect multiple tool families. Inspect the matching resolver/control/data/workflow tests, not only server registration. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- Local OCI credential resolution is outside Common. This pass records the departure without migrating authentication.
- Local auto auth catches a configured security-token failure and falls back to API-key auth, differing from Common’s fail-closed profile contract. Recheck auth.py and Common before any auth change.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle/oci_iot_mcp_server/server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Local tests](oracle/oci_iot_mcp_server/tests); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
