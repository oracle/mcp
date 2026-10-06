# Oracle GoldenGate engineering context

## Scope and ownership

This package owns GoldenGate Administration REST operations, process lifecycle, configuration and monitoring. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/oracle_goldengate_mcp_server/server.py): MCP registration, tool handlers and runtime entry point.
- [models.py](oracle/oracle_goldengate_mcp_server/models.py): local request/response models and conversions.
- [Configuration](oracle/oracle_goldengate_mcp_server/config.py): deployment and Vault/file/environment credential resolution
- [HTTP client](oracle/oracle_goldengate_mcp_server/http_client.py): REST transport and OCI request signing
- [REST API](oracle/oracle_goldengate_mcp_server/api.py): GoldenGate endpoint adapter
- [Extract config](oracle/oracle_goldengate_mcp_server/extract_config.py): Extract payload construction
- [Replicat config](oracle/oracle_goldengate_mcp_server/replicat_config.py): Replicat payload construction
- [Extract guidance](docs/createExtract.md): native Extract inputs/examples
- [Replicat guidance](docs/createReplicat.md): native Replicat inputs/examples
- [Package metadata](oracle/oracle_goldengate_mcp_server/__init__.py) and [manifest](pyproject.toml): version, dependencies and executable definitions.
- [Tests](oracle/oracle_goldengate_mcp_server/tests): local behavior definitions; start with [test_goldengate_tools.py](oracle/oracle_goldengate_mcp_server/tests/test_goldengate_tools.py), [test_support_modules.py](oracle/oracle_goldengate_mcp_server/tests/test_support_modules.py).

## Setup / build / run

From the repository root, use `proto install` for pinned tools and `moon run oracle-goldengate-mcp-server:build` for packaging. The [manifest](pyproject.toml) requires Python `>=3.10`. Read the local [README](README.md) and server `main()` for runtime transport/configuration; startup can access real services. See the [shared validation map](../../docs/agent-development.md#validation-map) for command definitions and check scope.

## Tests and validation

Use `moon run oracle-goldengate-mcp-server:test` from the repository root for the inherited Python test task, and `moon run root:lint` after Python source changes. The manifest configures `90%` coverage. Inspect the relevant tool/model or helper tests for the requested change; shared changes also require [shared validation](../../docs/agent-development.md#validation-map). These definitions are source evidence; this documentation expansion ran no server tests or coverage.

## Architecture and dependencies

api.py combines HttpClient with GoldenGate REST endpoints; extract/replicat/map/table helpers build configuration payloads. config.py resolves deployment Basic auth credentials with Vault secret, password file and environment precedence; http_client.py separately signs OCI Secrets retrieval requests. This is REST integration, not a Common-backed OCI SDK factory.

## Security and secrets handling

Extract/replicat/distribution lifecycle and configuration operations mutate deployments. Review deployment URL, Basic auth, password-file/Vault retrieval and startup connectivity checks using HTTP mocks. Keep credentials, private-key PEMs and generated configuration secrets out of logs. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

REST payloads, extract/replicat configuration, connection credential handling and process state changes affect operators and tool clients. Review tool/support-module tests and the native createExtract/createReplicat docs. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle/oracle_goldengate_mcp_server/server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Local tests](oracle/oracle_goldengate_mcp_server/tests); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
