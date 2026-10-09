# Oracle Data Studio engineering context

## Scope and ownership

This package owns task-oriented Essbase, Autonomous Database Data Platform and Data Transforms tools. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/data_studio_mcp_server/server.py): MCP registration, tool handlers and runtime entry point.
- [Configuration](oracle/data_studio_mcp_server/config.py): CLI/environment/service/transport configuration
- [Credential store](oracle/data_studio_mcp_server/credential_store.py): keyring and secret-key handling
- [Profiles](oracle/data_studio_mcp_server/profiles.py): tool filtering and capability defaults
- [HTTP runtime](oracle/data_studio_mcp_server/http_runtime.py): bind gate and bearer middleware
- [Tools](oracle/data_studio_mcp_server/tools): Essbase/ADP/Data Transforms handlers
- [Package metadata](oracle/data_studio_mcp_server/__init__.py) and [manifest](pyproject.toml): version, dependencies and executable definitions.
- [Tests](oracle/data_studio_mcp_server/tests): local behavior definitions; start with [test_unit.py](oracle/data_studio_mcp_server/tests/test_unit.py).

## Setup / build / run

From the repository root, use `proto install` for pinned tools and `moon run oracle-data-studio-mcp-server:build` for packaging. The [manifest](pyproject.toml) requires Python `>=3.13`. Read the local [README](README.md) and server `main()` for runtime transport/configuration; startup can access real services. See the [shared validation map](../../docs/agent-development.md#validation-map) for command definitions and check scope.

## Tests and validation

Use `moon run oracle-data-studio-mcp-server:test` from the repository root for the inherited Python test task, and `moon run root:lint` after Python source changes. The [manifest](pyproject.toml) configures `90%` coverage; the [native development route](README.md#local-development) and inherited task collect branch coverage with the offline unit suite. Inspect the relevant tool/model or helper tests for the requested change; shared changes also require [shared validation](../../docs/agent-development.md#validation-map). These definitions are source evidence; this context maintenance ran no server tests or coverage.

## Architecture and dependencies

The oracle-data-studio SDK owns underlying service REST clients. Local tools compose those clients; profiles.py filters tool registration into viewer (default), analyst and admin capabilities. Config loading combines CLI, environment, keyring and INI sources; annotation-aware query guidance is part of the ADP tool surface.

## Security and secrets handling

Passwords/tokens route through credential_store.py to the OS keyring. Inspect profile filtering and AI-chat table policy with query/admin changes. http_runtime.py gates exposed HTTP binds and enforces a configured bearer token; this uses configured service credentials, not OCI IDCS caller-token exchange. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Tool/profile registration, credential precedence, annotation-guided queries and HTTP bind policy affect all three service families. Review the unit module and native CLI/config examples. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- The README emphasizes stdio; the source also implements streamable HTTP. Use config.py, server.py and http_runtime.py for the actual transport/bind behavior.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle/data_studio_mcp_server/server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Local tests](oracle/data_studio_mcp_server/tests); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
