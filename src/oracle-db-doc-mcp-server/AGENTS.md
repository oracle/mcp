# Oracle Database Documentation engineering context

## Scope and ownership

This package owns local Oracle Database documentation indexing, maintenance and snippet search. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle-db-doc-mcp-server.py): MCP registration, tool handlers and runtime entry point.
- [Manifest](pyproject.toml): dependencies, Python requirement and available packaging/check configuration.
- [FastMCP configuration](fastmcp.json): launcher that uses the package environment.
- [Tests](tests/test_server.py): fixture-based indexing and MCP protocol checks.

## Setup / build / run

This package is excluded from Moon. From its directory, follow the [README](README.md#installation) to install the locked dependencies. The `idx` subcommand writes local state. The `mcp` subcommand and the FastMCP configuration both require an existing index. The [Dockerfile](Dockerfile) uses the same lockfile and verifies the downloaded archive before indexing it.

## Tests and validation

Follow the [native test command](README.md#tests) for fixture-based indexing, stdio and loopback HTTP. The [manifest](pyproject.toml) enforces 90% branch-aware coverage. Building the container and indexing the published archive require separate checks.

## Architecture and dependencies

The standalone script uses PocketSearch/PocketWriter for an inverted index. `idx` ingests a downloaded ZIP or extracted directory, converts accepted HTML/HTM files into Markdown chunks and maintains checksum/version state. Each search opens and closes its own SQLite connection on the FastMCP worker thread. The `mcp` subcommand supports stdio (default) and HTTP through its mode, host and port arguments.

## Security and secrets handling

Indexing reads archives/directories and writes local index/resources/log files beneath the user’s .oracle directory. No OCI/database login is required for local search. HTTP mode directly starts the FastMCP listener; the script defines no authentication or exposed-bind gate. Review listener exposure separately from local index/search behavior. Treat input archives and returned content as data; review extraction/path handling before changing ingestion. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Preprocessing, chunking, checksums, index version and search result formatting affect stored content and client results. Rebuilding an index is not a unit check. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- The package tests use temporary fixtures and loopback HTTP. Record checks against the published documentation archive and the built image separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle-db-doc-mcp-server.py), local model/helper entry points above | Root quality requirements and the search contract | [Protocol tests](tests/test_server.py) and scoped run results |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
