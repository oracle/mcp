# PostgreSQL runtime engineering context

## Scope and ownership

This Python package exposes six PostgreSQL runtime tools: `get_runtime_info`, `list_connections`, `test_connection`, `list_schemas`, `list_tables` and `execute_query`. It does not provision OCI resources or use OCI SDK authentication. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). Confirm maintenance ownership through the [contribution process](../../CONTRIBUTING.md).

## Entry points

- [server.py](oracle/oci_postgresql_runtime_mcp_server/server.py): FastMCP registration, runtime fingerprint, connections, result limits and entry point.
- [profiles.py](oracle/oci_postgresql_runtime_mcp_server/profiles.py): startup profile loading, validation and summaries.
- [sql_policy.py](oracle/oci_postgresql_runtime_mcp_server/sql_policy.py): parsing, statement policy and bind-parameter handling.
- [inspection.py](oracle/oci_postgresql_runtime_mcp_server/inspection.py): SQLAlchemy reflection, native column types and explicit foreign-key target schemas.
- [Tests](oracle/oci_postgresql_runtime_mcp_server/tests/): tool/protocol, concurrency and optional database tests; [manifest](pyproject.toml), [lockfile](uv.lock) and [package metadata](oracle/oci_postgresql_runtime_mcp_server/__init__.py) define packaging and dependencies.

## Setup / build / run

Use Python 3.13+ and `uv`. From the repository root, `proto install` installs pinned tools; `uv sync --directory src/oci-postgresql-runtime-mcp-server --locked --all-extras --dev` sets up the locked package environment. Follow the [shared validation map](../../docs/agent-development.md#validation-map).

[Connection profiles](README.md#connection-profiles) load once at startup from `POSTGRESQL_MCP_CONFIG`, otherwise this server directory's `local_config.json`; changes require a restart. TLS defaults to `verify-full`; preserve certificate and hostname verification for normal deployment. Keep profiles outside tracked files.

[Setup](README.md#setup) owns local launch and network prerequisites. For remote execution, follow [MCP on compute through SSH](README.md#approach-b-mcp-on-compute-through-ssh): SSH carries STDIO, and the remote process needs its own environment, profile and database route. Console command: `oracle.oci-postgresql-runtime-mcp-server`.

## Tests and validation

From the repository root, use the inherited [Python tasks](../../.moon/tasks/python.yml):

```sh
moon run oci-postgresql-runtime-mcp-server:lock-check
moon run oci-postgresql-runtime-mcp-server:test
moon run oci-postgresql-runtime-mcp-server:build
moon run oci-postgresql-runtime-mcp-server:install-check
```

After Python source changes, also run `moon run root:lint`. The manifest enforces at least 90% coverage; the Moon test task measures branches. Report actual results separately.

Optional integration tests skip without `POSTGRESQL_MCP_TEST_DSN`. Set it only for a disposable database with the [documented privileges](README.md#integration-tests). Fixtures create, write and drop objects; the read-only regression test deliberately bypasses the parser and commits a fixture write. Do not point these tests at a shared or production database.

## Architecture and dependencies

FastMCP exposes synchronous tools; Psycopg connects, pglast validates SQL, and SQLAlchemy reflects metadata. Each database call requires `connection_name` and owns its connections, without shared active connections or cross-call pooling. Preserve [stateless lifecycle](README.md#connection-selection-and-lifecycle) and exact schema/table identifiers.

## Security and secrets handling

Preserve [query policy](README.md#query-policy) and [security boundaries](README.md#security): validate every statement before execution, use read-only transactions and roll back query calls. Top-level syntax filtering cannot prove permitted functions lack side effects. Restrict database grants and function execution. The MCP SQL policy applies only to calls through this server.

[Result limits](README.md#query-results-limits-and-concurrency) cap rows per result set and serialized row data per call, with statement/lock timeouts. Preserve connection cleanup, parameter redaction and duplicate-column handling.

Keep credentials, profiles, certificates, private endpoints and machine-specific paths out of tracked files and logs. Use synthetic fixtures and mocked boundaries for normal unit checks.

## Change impact

Tool schemas, defaults, errors and response changes affect MCP callers. Profile, policy and metadata changes require corresponding tests and README review. The fingerprint covers five runtime modules; update its file list and tests when that scope changes. Follow root changelog rules; this package currently has no changelog.

## Known gaps

- The serialized result-size cap does not bound memory used while fetching rows.
- Cancelling an MCP request does not guarantee immediate cancellation of its PostgreSQL query; the worker retains its connection until execution and cleanup finish.

See [result limits and concurrency](README.md#query-results-limits-and-concurrency).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Changing tools, profiles or SQL policy | Entry points above; [README](README.md) | Root quality/security rules and actual dependency versions | Corresponding tool/protocol, concurrency and integration tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map), manifest and native tasks | Selected scope and disposable-database prerequisites when applicable | Actual command, snapshot, coverage and skip results |
| **Do:** Maintaining this guide | [Context conventions](../../docs/agent-context.md) | Root instructions, this guide and owning sources | Changed links/anchors, command-source checks and scoped diff review |
