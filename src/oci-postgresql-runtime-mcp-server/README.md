# OCI PostgreSQL Runtime MCP Server

## Overview

This server connects MCP clients to PostgreSQL to test connectivity, inspect schemas, tables, and views, and execute read-only SQL. It does not provision or manage OCI resources.

The MCP process must be able to reach the database. OCI PostgreSQL private endpoints require private network connectivity. For local use without an existing private route, an OCI Bastion port-forwarding session is required. Alternatively, run the MCP process on a compute host that can reach the database and carry MCP traffic over SSH. See [Setup](#setup) for both approaches.

[Tools](#tools) · [Usage](#usage) · [Query Policy](#query-policy) · [Setup](#setup) · [Integration Tests](#integration-tests)

## Tools

The database tools `test_connection`, `list_schemas`, `list_tables`, and `execute_query` require `connection_name` on every call. This selects a named profile; there is no active or current connection shared between calls.

| Tool Name | Description |
| --- | --- |
| `get_runtime_info` | Returns non-secret runtime version, Python version, and source fingerprint metadata. |
| `list_connections` | Lists configured PostgreSQL connection profiles loaded at startup. |
| `test_connection` | Tests the specified connection profile and returns basic server/session metadata. |
| `list_schemas` | Lists a bounded page of schemas visible to the database role in the specified connection profile. |
| `list_tables` | Lists a bounded page of tables and views with auto, summary, or full metadata. |
| `execute_query` | Executes read-only SQL through the specified connection profile, with optional parameter values bound in order. |

## Usage

These examples assume a configured connection profile. For first-time configuration, see [Setup](#setup).

### Connection Selection and Lifecycle

Use `list_connections` to discover configured profile names, then pass the selected name as `connection_name` to each database tool. `test_connection` checks that profile; it does not make it active for later calls. Each database tool call opens its own connections, and the server does not pool connections across calls. SQL calls are stateless: do not rely on session variables, temporary tables, prepared statements, or transaction state surviving a tool call.

List configured profiles:

```json
{
  "tool": "list_connections"
}
```

Test a named connection profile:

```json
{
  "tool": "test_connection",
  "arguments": {
    "connection_name": "app-db"
  }
}
```

List schemas through a named profile:

```json
{
  "tool": "list_schemas",
  "arguments": {
    "connection_name": "app-db"
  }
}
```

### Metadata Pagination

`list_schemas` and `list_tables` return one page per call. `page_size` defaults to 100 and accepts values from 1 through 1,000. This limits each response, not the number of schemas or tables supported by the database. `count` is the number of objects returned in this page, not the total matching inventory.

When `has_more` is true, pass `next_cursor` as `cursor` in another call with the same connection, filters and metadata settings. The cursor carries the last returned name and request scope; it requires no open database session or server-side pagination state. Table ordering uses the schema and table name together, so continuation can cross schemas when no schema filter is supplied. Ordering is deterministic, but objects created, dropped or renamed between calls can change the inventory.

For example, continue an unfiltered table listing as follows:

```json
{
  "tool": "list_tables",
  "arguments": {
    "connection_name": "app-db",
    "detail": "summary",
    "page_size": 100,
    "cursor": "<next_cursor from the previous response>"
  }
}
```

Do not collect every page unless the task requires a complete inventory. Narrow discovery by schema or table name, then use exact `table_refs` to fetch full metadata for the relevant objects. For unfiltered table discovery, the response’s `schemas` field lists the schemas represented by that page. The server limits catalog discovery before reflecting metadata. Table metadata applies a 60-second database-work budget across its queries; schema discovery uses a 60-second statement timeout. Both apply a five-second lock timeout. These controls do not guarantee a complete tool-call deadline. Metadata responses also have an approximately 1 MB size budget; a page can contain fewer than `page_size` objects when this budget is reached. Continuation starts after the last object actually returned. An object that cannot fit on its own produces an error instead of silently losing metadata.

### Table and View Metadata

Use `list_schemas` to discover schemas through a specified profile. By default, it excludes `information_schema` and schema names beginning with `pg_`; set `include_system=true` to include them.

Use `list_tables` with the following filters and metadata depth:

- Omit `schemas` and `table_refs` to discover tables across visible non-system schemas, one page at a time. Default discovery excludes `information_schema` and schema names beginning with `pg_`.
- Use `schemas` for exact schema names or `table_refs` for exact `{schema, name}` references. The filters are mutually exclusive. Explicit filters may target system schemas.
- Use `name_prefix` for a literal, case-sensitive table/view-name prefix. `list_schemas` also accepts `name_prefix` for schema names. Prefixes are not SQL patterns: `%` and `_` match themselves.
- Each explicit `schemas` or `table_refs` list accepts at most 1,000 entries. Identifiers and prefixes accept at most 1,024 UTF-8 bytes.
- Views are included by default. Set `include_views=false` to inspect base tables only.
- `detail=auto` returns full metadata when the complete filtered scope contains at most 100 matched tables/views, and summary metadata above that. `auto_full_limit` changes this threshold independently of page size, with a maximum of 1,000. A bounded catalog probe determines the detail level; selecting a small page does not turn a large catalog into full metadata.
- `detail=summary` returns names, comments, indexes, and foreign keys without column lists.
- `detail=full` also returns columns, primary keys, unique constraints, and check constraints.

List tables and views across all visible non-system schemas with automatic metadata depth:

```json
{
  "tool": "list_tables",
  "arguments": {
    "connection_name": "app-db"
  }
}
```

List only summary metadata for multiple schemas:

```json
{
  "tool": "list_tables",
  "arguments": {
    "connection_name": "app-db",
    "schemas": ["app", "public"],
    "detail": "summary"
  }
}
```

Fetch full metadata for exact tables or views:

```json
{
  "tool": "list_tables",
  "arguments": {
    "connection_name": "app-db",
    "table_refs": [
      {"schema": "app", "name": "orders"},
      {"schema": "public", "name": "customers"}
    ],
    "detail": "full"
  }
}
```

### Query Parameters

`params` supplies values in the same order as the SQL placeholders. For example, with `where active = %s and id > %s`, `params=[true, 100]` binds `true` to the first placeholder and `100` to the second. Values are sent separately from the SQL; do not insert or quote them yourself.

- Use Psycopg `%s`, `%b`, or `%t` placeholders. When `params` is supplied, write `%%` for a literal percent sign in SQL.
- For one statement, use a flat `params` list.
- For multiple statements, use one nested bind list per non-empty statement. Every statement is validated before any statement executes.

Execute a parameterized query through a named profile:

```json
{
  "tool": "execute_query",
  "arguments": {
    "sql": "select id, email from app.users where active = %s order by id",
    "connection_name": "app-db",
    "params": [true],
    "max_rows": 50
  }
}
```

Execute multiple read statements with separate bind parameters:

```json
{
  "tool": "execute_query",
  "arguments": {
    "sql": "select id from app.users where name = %s; select event_name from app.audit where user_id = %s",
    "connection_name": "app-db",
    "params": [
      ["Ada"],
      [42]
    ],
    "max_rows": 50
  }
}
```

### Query Results, Limits, and Concurrency

- `max_rows` defaults to 100 and accepts values from 1 through 10,000 per result set. The server fetches at most one extra row to detect truncation.
- Serialized row data is capped at approximately 1 MB across all statements in one call. This is a response limit, not a guarantee that fetching uses at most 1 MB of memory.
- The row limit applies to each result set in one call. Pagination and repeated calls can retrieve more rows in total; other database clients are outside this limit.
- Before each submitted statement, the runtime applies a five-minute statement timeout and a five-second lock timeout within the current transaction.
- Result rows are JSON-serializable dictionaries keyed by column name. Duplicate direct-column labels use their PostgreSQL origin, such as `users.id` and `orders.id`; remaining collisions receive `_2`, `_3`, and subsequent suffixes.
- Responses include `executed_sql`, `param_count`, and `params_redacted` when bind parameters are supplied.

The server uses FastMCP 3.4.5, which runs synchronous tools in worker threads. Clients can submit overlapping requests. Cancelling a client request does not guarantee immediate cancellation of its PostgreSQL query; the worker retains its connection until execution and cleanup finish.

## Query Policy

The runtime accepts read-only SQL only. Every query runs in a read-only transaction and rolls back after returning results. There is no write-enabling option.

The parser accepts read statements, including `SELECT`, `VALUES`, `SHOW`, and plain `EXPLAIN` of permitted reads. It rejects SQL writes, modifying CTEs, `SELECT INTO`, locking reads, `EXPLAIN ANALYZE`, explicit transaction control, role/session changes, and other administrative statements.

Permitted `SELECT` statements can call functions with effects that rollback cannot undo, such as cancelling other sessions or committing writes through the `dblink` extension. Database privileges control whether those calls can succeed.

These safeguards apply only to SQL submitted through this MCP server. They do not restrict other tools, database clients, or agents that can access the same credentials and network path. Give agent-accessible credentials only the privileges you are willing for the agent to exercise directly. The MCP does not implement relation-specific access control: after a statement passes the syntax filter, PostgreSQL decides whether the role may access each table or view.

## Setup

This server requires `uv`, Python 3.13 or later, database credentials, and a network path from the MCP process to PostgreSQL. Configure the profile, choose the local or remote network approach, and verify the configured tools.

### Connection Profiles

The runtime server uses named PostgreSQL connection profiles loaded when the server starts:

1. If `POSTGRESQL_MCP_CONFIG` has a non-empty value, load that file.
2. Otherwise, load `local_config.json` in this server directory if it exists.

Profile edits also require a restart because profiles are loaded only at startup.

Example profile file:

```json
{
  "connections": {
    "app-db": {
      "host": "db.example.oraclecloud.com",
      "port": 5432,
      "database": "app_db",
      "user": "app_user",
      "password_keyring": {
        "service": "oracle-postgresql/app-db",
        "username": "app_user"
      },
      "sslmode": "verify-full",
      "sslrootcert": "/absolute/path/to/server-ca.pem"
    }
  }
}
```

Each profile must select exactly one password source:

- `password_keyring`: an object containing explicit `service` and `username` strings. The server reads that entry from a supported OS credential store. Select a supported backend before storing the secret, and use the same `PYTHON_KEYRING_BACKEND` for provisioning and server startup. Provision on the MCP host under its runtime user, using the server Python environment. For example, on macOS run `PYTHON_KEYRING_BACKEND=keyring.backends.macOS.Keyring python -m keyring set oracle-postgresql/app-db app_user` and enter the password at the prompt. For Linux Secret Service, select `keyring.backends.SecretService.Keyring` after setting up its daemon and session. Do not provision secrets through an automatically selected plaintext backend.
- `password_env`: the name of an environment variable that contains the password, such as `APP_DB_PASSWORD`. Supply the value through the deployment's secret injection mechanism. The profile contains only the variable name. Storing the value in an MCP client's configuration file would still leave a plaintext secret on disk; an environment reference does not provide encryption at rest by itself.
- `password`: a literal password, retained for compatibility. This source stores the secret in the profile file. Prefer a credential reference and protect any legacy password-bearing profile as a secret.

Password sources resolve once when profiles load at startup. Restart the server after changing a referenced environment value or keyring entry. Conflicting sources, missing secrets and unavailable or unsupported keyring backends produce a configuration error; the server does not silently fall back to another source. Secrets are excluded from connection summaries and credential-resolution errors.

Keyring support uses native macOS Keychain, Windows Credential Manager, Linux Secret Service, KWallet or libsecret backends. Configure a supported backend explicitly when necessary with `PYTHON_KEYRING_BACKEND`; plaintext third-party stores and automatic backend chains are not accepted. See [keyring's headless Linux requirements](https://keyring.readthedocs.io/en/latest/#using-keyring-on-headless-linux-systems) for the required daemon, D-Bus session and unlocked store. For SSH deployment, configure credentials and the keyring session on compute. The local desktop's keyring is not forwarded through SSH.

Profiles default to `sslmode=verify-full`. The runtime accepts `require`, `verify-ca`, and `verify-full`. Set `sslmode=require` explicitly to require TLS without hostname verification. libpq can still verify the CA when `sslrootcert` or the default root CA file exists.

### Private Endpoints

The machine running the MCP process must have a network path to the PostgreSQL private endpoint. A local process cannot reach that endpoint over the public internet. If an approved private route, such as site-to-site VPN, already connects the local machine to the database VCN, use the database FQDN and port `5432` without a tunnel `hostaddr`. Otherwise, use one of the following approaches. See [Oracle's PostgreSQL connection guide](https://docs.oracle.com/en-us/iaas/Content/postgresql/connect-to-db.htm).

Choose the approach based on where the database endpoint is reachable:

| | Approach A: local MCP | Approach B: MCP on compute |
| --- | --- | --- |
| Use when | OCI Bastion can forward directly to PostgreSQL | PostgreSQL is reachable only from a compute host |
| MCP process | Codex machine | Compute host, launched over SSH STDIO |
| Profile and CA file | Codex machine | Compute host |
| `host` | Database FQDN | Database FQDN |
| `hostaddr` | Local tunnel address, such as `127.0.0.1` | Omit |
| `port` | Local forwarded port, such as `15432` | PostgreSQL port, usually `5432` |

Configure only the approach you intend to use.

#### Approach A: Local MCP Through OCI Bastion

Codex and the MCP server run locally. OCI Bastion forwards a local port to the database:

```text
Codex -> local MCP -> 127.0.0.1:15432 -> OCI Bastion -> PostgreSQL:5432
```

Use an existing approved OCI Bastion to create a port-forwarding session targeting PostgreSQL port `5432` and keep the session running. Use the database private IP unless Bastion DNS proxy is enabled for an FQDN target.

Inside the existing connection entry, set the following fields. Keep `host` set to the database FQDN for `verify-full` hostname verification; `hostaddr` and `port` select the local tunnel:

```json
{
  "host": "primary.example.postgresql.region.oci.oraclecloud.com",
  "hostaddr": "127.0.0.1",
  "port": 15432
}
```

When a Bastion session expires, recreate it on the same local port. The MCP server does not need to restart unless the profile or local port changes.

#### Approach B: MCP on Compute Through SSH

Use this approach when only a compute host can reach PostgreSQL:

```text
Codex -> SSH STDIO -> runtime MCP on compute -> PostgreSQL:5432
```

SSH carries MCP over standard input and output, so compute does not expose a separate MCP port.

The runtime server source, `uv`, Python 3.13 or later, the connection profile, and the CA file, if configured, must be available on compute. Clone the repository or copy only this server directory. Do not copy `.venv`, caches, profiles, credentials, or private keys. Let `uv run` create or update the Python environment on compute, and run `command -v uv` there to obtain the absolute path used below.

Inside the existing remote connection entry, set the following fields. Use the database FQDN and PostgreSQL port; do not set `hostaddr` to the compute loopback address:

```json
{
  "host": "primary.example.postgresql.region.oci.oraclecloud.com",
  "port": 5432
}
```

On the machine running Codex, locate the SSH executable with `command -v ssh` and create a reusable target in `~/.ssh/config`:

```sshconfig
Host postgresql-compute
  HostName compute.example.com
  User <remote-user>
  IdentityFile /absolute/path/to/compute-private-key
  IdentitiesOnly yes
  BatchMode yes
```

Replace the host, user, and key path for your compute instance. `IdentityFile` selects a key, and `IdentitiesOnly yes` limits SSH to configured identities.

If your SSH key is supplied by `ssh-agent` or a compatible agent, SSH asks that agent to authenticate through the local `SSH_AUTH_SOCK` socket. Load or unlock the key in the agent before starting Codex. To let SSH offer the agent's available keys, omit the `IdentityFile` and `IdentitiesOnly` lines from this example, subject to your existing SSH configuration. You can also keep those settings to select a specific key supplied by the agent. See the [OpenSSH identity settings](https://man.openbsd.org/ssh_config#IdentitiesOnly).

If compute is reached through OCI Bastion, forward a local port to compute port `22`, then set `HostName 127.0.0.1` and `Port <local-forwarded-port>` in the same SSH target. This changes only the SSH route: the remote database profile still uses the database FQDN on port `5432` and omits `hostaddr`.

If your environment supplies `ProxyCommand` or `ProxyJump` instead of a local port forward, add it to the same SSH target. The MCP definition and remote database profile remain otherwise unchanged.

After configuring the final `HostName`, `Port`, and proxy settings, run `ssh -o BatchMode=no postgresql-compute true` once to verify and store the host key. Then confirm `ssh -T postgresql-compute true` succeeds without prompting or writing to standard output.

Configure Codex with the absolute SSH path reported by `command -v ssh` and the same target name:

```toml
[mcp_servers.oci-postgresql-runtime-mcp-server]
command = "/absolute/path/to/ssh"
env_vars = ["SSH_AUTH_SOCK"]
args = [
  "-T",
  "postgresql-compute",
  "exec env POSTGRESQL_MCP_CONFIG='/absolute/remote/path/to/postgresql-profiles.json' FASTMCP_LOG_LEVEL=ERROR '/absolute/remote/path/to/uv' run --project '/absolute/remote/path/to/oci-postgresql-runtime-mcp-server' oracle.oci-postgresql-runtime-mcp-server",
]
startup_timeout_sec = 60
tool_timeout_sec = 330
```

`env_vars` forwards the local agent socket to the local SSH process; keep it when the SSH target or its proxy uses `ssh-agent`. `POSTGRESQL_MCP_CONFIG` must be set in the remote command because a local Codex `env` table configures only the SSH process. The remote shell must not write startup text to standard output because MCP uses that stream. If the SSH connection ends, the remote MCP process ends with it. Restore the SSH route and restart the server; profile changes also require a restart.

### Add the Server to Codex

The following entry runs the MCP process on the same machine as Codex, using either a Bastion tunnel or an existing approved private network route. For a remote MCP process, use the SSH definition in Approach B instead.

Add this definition to `~/.codex/config.toml`, replacing the project and profile paths with absolute paths:

```toml
[mcp_servers.oci-postgresql-runtime-mcp-server]
command = "uv"
args = [
  "run",
  "--project",
  "/absolute/path/to/oci-postgresql-runtime-mcp-server",
  "oracle.oci-postgresql-runtime-mcp-server",
]
cwd = "/absolute/path/to/oci-postgresql-runtime-mcp-server"
startup_timeout_sec = 60
tool_timeout_sec = 330

[mcp_servers.oci-postgresql-runtime-mcp-server.env]
FASTMCP_LOG_LEVEL = "ERROR"
POSTGRESQL_MCP_CONFIG = "/absolute/path/to/postgresql-profiles.json"
```

### Running the Server Manually

From this server directory, start the STDIO server manually with:

```sh
uv run --project . oracle.oci-postgresql-runtime-mcp-server
```

`uv run` creates or updates the project environment before starting the server. Use the Codex launch configuration in the applicable network approach for normal Codex use.

### Verify and Troubleshoot

After adding or changing the Codex MCP definition, start a new Codex process or session before verifying it. Profile changes require restarting the MCP server because profiles are loaded only at startup. Then use the runtime tools in this order:

1. `get_runtime_info` to confirm the project and version. If `POSTGRESQL_MCP_EXPECTED_SOURCE_FINGERPRINT` is configured, also require `source_fingerprint_status` to be `match`; `not_configured` does not indicate a mismatch.
2. `list_connections` to confirm the loaded profile.
3. `test_connection` to validate connectivity.
4. `execute_query` with a minimal query such as `select current_database(), current_user`.

Common DP-specific failures:

- No profiles: check the `POSTGRESQL_MCP_CONFIG` path and JSON syntax, then restart the MCP server.
- Connection refused: confirm the profile uses the tunnel address and port for local Bastion access, or the database endpoint and port for a direct private route or remote MCP.
- TLS verification failure: keep `host` set to the database FQDN and verify the `sslrootcert` path on the machine running the MCP process.
- SSH MCP initialization closes unexpectedly: confirm the SSH target works non-interactively and, when it uses `ssh-agent`, that the MCP definition forwards `SSH_AUTH_SOCK` through `env_vars`.
- uv cache permission failure: keep uv's default cache unless startup reports `Operation not permitted` for that cache. In that case only, set `UV_CACHE_DIR` to a writable path in the MCP environment. For Approach B, set it in the remote `exec env` command.

## Scope

This server intentionally stays small. It does not manage migrations, pool connections across calls, or provision OCI resources. It is a runtime SQL companion to the OCI PostgreSQL control-plane server.

## Security

⚠️ **NOTE**: Runtime SQL actions use the configured PostgreSQL connection profile and run with the permissions of that database user or role. OCI IAM controls the companion control-plane server, but it is not the authorization boundary for SQL execution. The SQL policy filters top-level syntax only and cannot prove that allowed expressions are free of side effects. Use least-privilege database grants, restrict function execution, keep verified TLS enabled, protect profile files, credential stores, passwords, CA certificates, and network settings, and avoid logging or exposing secrets.

Providing shell access or another SQL client creates an execution path outside this MCP query policy. Restrict those paths and credentials if MCP filtering is required.

## Integration Tests

Set `POSTGRESQL_MCP_TEST_DSN` to a libpq connection string for a disposable PostgreSQL database, then run `uv run pytest oracle/oci_postgresql_runtime_mcp_server/tests/`. The integration tests skip when the variable is unset. The database role must be able to create schemas and create tables in `public`.

The integration tests create uniquely named fixtures and remove them afterward. They verify bounded metadata pages, continuation across schemas, native scalar and array type names for tables and views, cross-schema composite foreign keys, constraint options, database enforcement, and schema visibility under different search paths. Foreign-key metadata must include explicit target schemas regardless of the connection search path.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at <https://oss.oracle.com/licenses/upl/>.
