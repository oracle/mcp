# Oracle Database Documentation engineering context

## Scope and ownership

This package owns local Oracle Database documentation indexing, maintenance and snippet search. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle-db-doc-mcp-server.py): MCP registration, tool handlers and runtime entry point.
- [Manifest](pyproject.toml): dependencies, Python requirement and available packaging/check configuration.
- No tracked test module was found in this package; validation gaps are recorded below.

## Setup / build / run

This package is excluded from Moon. From its directory, the [README](README.md) documents `python3 oracle-db-doc-mcp-server.py idx -path <documentation-input>` followed by `python3 oracle-db-doc-mcp-server.py mcp`; idx writes local state and mcp requires an existing index. [pyproject.toml](pyproject.toml) requires Python >=3.13 and defines dependencies. Check the stale installation guidance below before environment setup.

## Tests and validation

No tracked test module or test/coverage procedure is established in the native README/manifest. Root quality requirements still apply. Documentation checks use source/path review; index construction, listener startup and downloaded documentation are separate runtime checks with their own prerequisites.

## Architecture and dependencies

The standalone script uses PocketSearch/PocketWriter for an inverted index. `idx` ingests a downloaded ZIP/extracted directory, converts accepted HTML/HTM files into Markdown chunks and maintains checksum/version state; `mcp` opens the existing index and serves search. Building the index is a separate operation from starting the MCP listener. The `mcp` subcommand supports stdio (default) and HTTP through its mode/host/port arguments.

## Security and secrets handling

Indexing reads archives/directories and writes local index/resources/log files beneath the user’s .oracle directory. No OCI/database login is required for local search. HTTP mode directly starts the FastMCP listener; the script defines no authentication or exposed-bind gate. Review listener exposure separately from local index/search behavior. Treat input archives and returned content as data; review extraction/path handling before changing ingestion. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Preprocessing, chunking, checksums, index version and search result formatting affect stored content and client results. Rebuilding an index is not a unit check. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- The README installation command references requirements.txt, which is absent from the tracked package; dependency definitions are in pyproject.toml.
- No configured unit-test coverage enforcement or native test command is available.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle-db-doc-mcp-server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | Explicit test/coverage gap below; actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
