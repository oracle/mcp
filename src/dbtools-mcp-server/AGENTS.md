# DBTools engineering context

## Scope and ownership

This package owns proof-of-concept OCI Database Tools connections, SQL/report execution, HeatWave operations and inventory tools. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](dbtools-mcp-server.py): MCP registration, tool handlers and runtime entry point.
- [requirements.txt](requirements.txt): script dependency definitions; this directory has no pyproject.toml.
- [test_dbtools_mcp_server.py](test_dbtools_mcp_server.py): available test definitions; inspect live prerequisites before execution.

## Setup / build / run

This proof-of-concept script is excluded from Moon and has no pyproject.toml. From this package directory, the [README](README.md) defines `pip install -r requirements.txt` and direct Python-script/client configuration with PROFILE_NAME. Those are runtime setup routes with host credentials; this documentation pass performs no installation or import.

## Tests and validation

[test_dbtools_mcp_server.py](test_dbtools_mcp_server.py) uses unittest and explicitly calls real OCI services with the host configuration. It is not an offline unit-validation route. The README does not define 90% coverage enforcement or an isolated unit-test setup; record these gaps before selecting execution.

## Architecture and dependencies

A single script initializes OCI config, service clients and a request signer at import time using PROFILE_NAME. SQL/report helpers, connection resolution and identifier/filter validation live in that script. requirements.txt defines its dependency environment; there is no packaged console entry point or Common integration.

## Security and secrets handling

SQL/report/bootstrap/vector operations can modify databases; OCI connection and secret access requires real credentials. Importing the script initializes host credential/client state. The existing test module explicitly requires OCI access; keep documentation review to file reads. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Connection resolution, SQL validation, retry rules, report schemas and model names affect multiple tools. Review the live test definitions separately from any future mock/unit validation. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- No isolated unit suite or configured 90% coverage enforcement is established.
- Import-time OCI credential/client construction is local, outside Common, and lacks the root-required metadata-derived user agent. The README labels this a proof of concept; that status does not waive shared requirements.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](dbtools-mcp-server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Test definitions](test_dbtools_mcp_server.py); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
