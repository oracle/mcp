# MySQL engineering context

## Scope and ownership

This package owns MySQL connections, SQL execution, HeatWave AI/vector operations and optional OCI inventory access. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/mysql_mcp_server/server.py): MCP registration, tool handlers and runtime entry point.
- [Connection helpers](oracle/mysql_mcp_server/utils.py): config validation, OCI clients, provider mode and SSH command construction
- [Defaults](oracle/mysql_mcp_server/consts.py): local constants
- [Package metadata](oracle/mysql_mcp_server/__init__.py) and [manifest](pyproject.toml): version, dependencies and executable definitions.
- [Tests](oracle/mysql_mcp_server/tests): local behavior definitions; start with [test_mysql_mcp_server.py](oracle/mysql_mcp_server/tests/test_mysql_mcp_server.py).

## Setup / build / run

This package is excluded from Moon. Read [README](README.md) for MCP client/configuration setup and [pyproject.toml](pyproject.toml) for Python >=3.12, dependencies, packaging and the `oracle.mysql_mcp_server` executable. Connection credentials/config and optional OCI access are runtime prerequisites; startup is separate from documentation validation.

## Tests and validation

[test_mysql_mcp_server.py](oracle/mysql_mcp_server/tests/test_mysql_mcp_server.py) contains mocked database/config behavior. The README does not define a test/coverage procedure, and the manifest has no test dependency group or coverage enforcement. Report these gaps before treating a native test command as an established validation route. Root Python lint and shared quality requirements remain applicable.

## Architecture and dependencies

mysql-connector-python owns database connections. server.py manages connection lifetime, SQL/result serialization and HeatWave operations. utils.py validates MYSQL_MCP_CONFIG/local_config.json and bastion inputs; OciInfo separately constructs OCI Identity/Object Storage clients from PROFILE_NAME. `_get_mode()` discovers the HeatWave provider, not a read-only access mode.

## Security and secrets handling

SQL execution commits statements and can mutate data; vector loading can read files and update databases. Connection passwords, SQL/parameters and generated SSH tunnel hints are sensitive. The SSH helper returns a command string rather than launching a process. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Connection IDs/config schema, SQL results, provider detection and vector/AI parameters affect clients and database behavior. Inspect test mocks before any check that could connect to real MySQL or OCI. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- Moon exclusion leaves native test setup and 90% coverage enforcement undocumented.
- Optional OCI clients resolve profiles locally without Common or the root-required metadata-derived user agent. This is an implementation gap, not an auth-policy exception.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle/mysql_mcp_server/server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Local tests](oracle/mysql_mcp_server/tests); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
