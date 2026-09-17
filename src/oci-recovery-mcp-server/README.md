# OCI Recovery Service MCP Server

An Oracle Cloud Infrastructure (OCI) Model Context Protocol (MCP) server for read-oriented Autonomous Recovery Service and Database Service operations. It maps OCI SDK responses to Pydantic models suitable for MCP clients.

## What it provides

- Browse protected databases, protection policies, Recovery Service subnets, restore work requests, DB homes, DB systems, databases, and backups.
- Summarize protected-database health, redo-shipping status, backup-space consumption, and backup destinations.
- Query Recovery Service metrics, service limits, and tenancy region subscriptions.
- Aggregate supported list and summary operations across a compartment subtree.
- Provide non-destructive dashboard, Cloud Protect onboarding, and backup/recoverability diagnostic guidance.
- Run locally with OCI API-key or session-token authentication, or as a hosted HTTP service with OCI IAM (IDCS) OAuth sign-in.

The server exposes 25 MCP tools. It does not create, update, or delete OCI resources.

## Requirements

- Python 3.13 or later
- [`uv`](https://docs.astral.sh/uv/)
- OCI credentials appropriate to the selected authentication mode

## Install and run locally

From this project directory (`src/oci-recovery-mcp-server`), `uv` resolves and installs
the dependencies into a project virtual environment on first run:

```sh
uv sync
```

Authentication is resolved by [`oracle-mcp-common`](../common) and **needs no
configuration in the common case**. The default, `auto`, selects session-token
authentication when the chosen OCI profile directly declares a `security_token_file`,
and API-key authentication otherwise.

For a session-token profile, authenticate once and run the server:

```sh
oci session authenticate --profile-name DEFAULT
uv run oracle.oci-recovery-mcp-server
```

For API-key authentication, no extra setting is needed either — the selected profile
just has to contain the normal API-key fields.

Set `OCI_CONFIG_PROFILE` to select a profile other than `DEFAULT`, and
`OCI_MCP_AUTH_TYPE` to pin a mode explicitly instead of auto-detecting. Local profile
credentials are only used over stdio.

The 2.x variables `ORACLE_MCP_AUTH_METHOD` (`session`/`apikey`) and
`ORACLE_MCP_AUTH_PROFILE` remain supported, so existing configurations keep working,
but they are optional and no longer needed.

Configuration comes from environment variables. Set them in the MCP client's `env`
block, as in the examples below, or export them in the shell or service that starts the
server.

### Local MCP client configuration (from source)

Configure an MCP client to start the server with `uv`. `--directory` points at this
project so `uv` uses its lockfile, and works regardless of the client's own working
directory:

```json
{
  "mcpServers": {
    "oci-recovery-local": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/ABS/PATH/mcp/src/oci-recovery-mcp-server",
        "run",
        "oracle.oci-recovery-mcp-server"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT"
      }
    }
  }
}
```

If `uv` is not on the MCP client's `PATH` (common for GUI clients that do not load your
shell profile), use its absolute path — `which uv` — as `command`.

### Local MCP client configuration (published PyPI package)

The server is published as
[`oracle.oci-recovery-mcp-server`](https://pypi.org/project/oracle.oci-recovery-mcp-server/).
No clone or checkout is needed: `uvx` downloads the package into a cached, isolated
environment and runs its entry point.

```sh
uvx oracle.oci-recovery-mcp-server
```

To pin a version, use `uvx oracle.oci-recovery-mcp-server@3.0.0`.

```json
{
  "mcpServers": {
    "oci-recovery": {
      "type": "stdio",
      "command": "uvx",
      "args": ["oracle.oci-recovery-mcp-server"],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT"
      }
    }
  }
}
```

Installing the package into a persistent tool environment instead of the `uvx` cache also
works:

```sh
uv tool install oracle.oci-recovery-mcp-server
```

That puts `oracle.oci-recovery-mcp-server` on `PATH`, which can then be used directly as
the client's `command`.

Local profile credentials are only used over stdio. To expose this server on a network
listener, where each caller authenticates against an OCI IAM (IDCS) domain instead, see
[HTTP (Streamable HTTP) deployment](#http-streamable-http-deployment) below.

## HTTP (Streamable HTTP) deployment

Setting `ORACLE_MCP_HOST` and `ORACLE_MCP_PORT` runs the server over Streamable HTTP
instead of stdio. The transport decides how requests are authenticated, the same way it
does in the other OCI MCP servers:

- **stdio** uses the operator's own OCI credentials from the selected config profile.
- **HTTP** authenticates every caller against an OCI IAM (IDCS) domain and exchanges
  that caller's access token for caller-specific OCI credentials. Local profile
  credentials are never used to serve a network listener.

Both paths go through the shared [`oracle-mcp-common`](../common) library:
`build_auth_context()` for the profile credentials, and `build_idcs_http_auth()` plus
`IDCSHttpAuth.context_for()` for HTTP. A fresh signer is built for every tool call from
the caller's own token, so one caller's credentials are never reused for another.

### Prerequisites

In the OCI IAM domain, create:

1. A **resource application** with a **primary audience** and a scope named
   `oci_mcp.recovery.invoke`.
2. A **confidential application** (client ID + secret) authorized for that resource
   application, with `${ORACLE_MCP_BASE_URL}/auth/callback` registered as the redirect
   URI, and both the Authorization Code and Client Credentials grants enabled.
3. An **Identity Propagation Trust** that lists that confidential application's client
   ID. Without it, sign-in succeeds and the first tool call fails: the IAM domain refuses
   to exchange the caller's token for an OCI UPST.

The primary audience is both the `aud` claim that issued access tokens are verified
against and the audience requested at `/authorize` and `/token`, so a value that does not
match the domain's configuration makes every sign-in fail.

Run the HTTP listener behind a TLS-terminating reverse proxy. `ORACLE_MCP_BASE_URL` must
be the public URL clients reach, since the authorize, callback, and well-known URLs are
built from it.

By default the server requires `openid profile email oci_mcp.recovery.invoke`; the
resource scope gates access to the Recovery tools beyond a bare authenticated identity.
Set `IDCS_REQUIRED_SCOPES` to a space-delimited list or JSON array to override it, and
keep `oci_mcp.recovery.invoke` in that list.

Write those scopes **bare**, not qualified with the audience. IDCS recognizes a resource
scope at `/authorize` only in its fully-qualified form — the audience and the scope name
concatenated without a separator — but returns it bare in the access token it issues, and
that token is re-validated against this setting on every request. The server handles both
forms for you: it keeps the configured value for verification and qualifies the resource
scopes with the audience on every path that reaches IDCS. Qualifying them yourself makes
every tool call fail with `401 invalid_token`.

### Running it

```sh
ORACLE_MCP_HOST=127.0.0.1 \
ORACLE_MCP_PORT=8000 \
ORACLE_MCP_BASE_URL=https://MCP_HOST \
OCI_REGION=us-ashburn-1 \
OCI_MCP_TENANCY_ID_OVERRIDE=ocid1.tenancy.oc1..aaaa \
IDCS_DOMAIN=idcs-aaaa.identity.oraclecloud.com \
IDCS_CLIENT_ID=REPLACE_ME \
IDCS_CLIENT_SECRET=REPLACE_ME \
IDCS_AUDIENCE=REPLACE_ME \
uv run oracle.oci-recovery-mcp-server
```

`oracle-mcp-common` validates `IDCS_DOMAIN`, `IDCS_CLIENT_ID`, `IDCS_CLIENT_SECRET`,
`IDCS_AUDIENCE`, and `ORACLE_MCP_BASE_URL` before the listener starts. `OCI_REGION`
supplies the default region for the request-token exchange; a tool's `region` argument
overrides it for that request. `OCI_MCP_TENANCY_ID_OVERRIDE` is required over HTTP because
compartment and region discovery need a tenancy OCID and there is no local OCI config
file to read one from.

Supply them as environment variables of the server process, for example through a
systemd `EnvironmentFile=` or a container's `--env-file`. Keep client secrets out of
source control and supply `IDCS_CLIENT_SECRET` from a secret manager or the deployment
environment.

Client configuration needs only the URL:

```json
{
  "mcpServers": {
    "oci-recovery": {
      "type": "streamableHttp",
      "url": "https://MCP_HOST/mcp"
    }
  }
}
```

### Operational notes

OAuth state (client registrations and authorization state) is persisted and encrypted at
rest by FastMCP under its home directory, `~/.fastmcp/oauth-proxy/` by default and
relocatable with `FASTMCP_HOME`. The storage directory and the token-signing key are both
derived from the client secret, so keys survive restarts and multiple workers without
being configured anywhere. Treat that directory as secret material, exclude it from
images, and give it persistent storage in a container deployment — a fresh directory on
every restart forces all clients to re-register. `FASTMCP_HOME` is resolved when FastMCP
is imported, so it must be set in the environment before the server starts. Rotating the client secret invalidates already-issued tokens, and clients sign
in again.

Clients register through Dynamic Client Registration at `/register`, an exchange that
never leaves the host, so authentication needs no outbound internet access. CIMD (Client
ID Metadata Document) registration is deliberately disabled: it would let a client present
an HTTPS URL as its `client_id` and require this server to fetch that URL, which fails on
a network-restricted host and surfaces as `The client ID ... was not found in the server's
client registry`.

Compartment listings are cached in-process for five minutes, separately for each caller.
The listing is fetched with `access_level="ACCESSIBLE"`, so it reflects that caller's own
permissions and is never served to another — two people signed in to the same deployment
do not share an entry. Subscribed regions are not cached at all: whether a caller may read
them is their own IAM policy's decision, so every lookup goes to IAM.

For a VPN-only deployment whose proxy uses an internal CA, clients must trust that CA's
public root certificate. Distribute only the public root certificate, never the private key.

## Environment variables

Only what you need to configure. Behaviour not listed here has working defaults.

**stdio (running it from your own MCP client)**

| Variable | Description |
| --- | --- |
| `OCI_CONFIG_FILE`, `OCI_CONFIG_PROFILE` | Which OCI config file and profile to authenticate with. Default `~/.oci/config` and `DEFAULT`. |
| `OCI_MCP_AUTH_TYPE` | Authentication mode. Defaults to `auto`, which picks session-token when the profile declares a `security_token_file` and API-key otherwise. |
| `OCI_MCP_TENANCY_ID_OVERRIDE` | Use a different tenancy than the one in the profile. |

**HTTP deployment**

| Variable | Description |
| --- | --- |
| `ORACLE_MCP_HOST`, `ORACLE_MCP_PORT` | Setting **both** switches from stdio to the Streamable HTTP listener. Startup fails if only one is set, or if the port is outside `1..65535`. |
| `ORACLE_MCP_BASE_URL` | Required. The public URL clients reach, used to build the authorize, callback and well-known URLs. |
| `IDCS_DOMAIN`, `IDCS_CLIENT_ID`, `IDCS_CLIENT_SECRET`, `IDCS_AUDIENCE` | Required. The IAM domain and its confidential OAuth application. |
| `OCI_MCP_TENANCY_ID_OVERRIDE` | Required. Tenancy OCID used for compartment and region discovery; there is no local OCI config file to read one from. |
| `OCI_REGION` | Default region for the request-token exchange. A tool's `region` argument overrides it per request. |
| `IDCS_REQUIRED_SCOPES` | Required scopes, written bare, as a space-delimited list or JSON array. Defaults to `openid profile email oci_mcp.recovery.invoke`. |
| `FASTMCP_HOME` | Where OAuth state is persisted. Contains secret material. |

**Tuning the large-tenancy scans**

Set these only if the summary tools return `truncated: true`, or scan more compartments
than you want them to.

| Variable | Description |
| --- | --- |
| `ORACLE_MCP_TOOL_DEADLINE_SECONDS` | Time budget for compartment-subtree summary scans, checked between OCI requests. Default 120; `0` removes the limit. A scan that stops early returns `truncated: true` with partial counts rather than an error. |
| `ORACLE_MCP_MAX_COMPARTMENTS_IN_SCOPE` | Cap on compartments scanned when `fetch_for_child_compartment=true`. Default 200. |

**Logging**

| Variable | Description |
| --- | --- |
| `ORACLE_MCP_LOG_LEVEL` | Default `INFO`. |
| `ORACLE_MCP_LOG_DIR`, `ORACLE_MCP_LOG_FILE` | Where logs are written. Files are created `0600` and rotate at 10 MB, keeping five. If the file cannot be opened the server warns and logs to stderr rather than failing to start. |
| `ORACLE_MCP_LOG_TO_STDOUT` | Log to stdout as well as the file. |
| `ORACLE_MCP_STATE_DIR` | Directory for this server's own state, including the default log directory. Defaults to `~/.oci-recovery-mcp`; set it when the home directory is not writable. |

Legacy names from 2.x still work: `ORACLE_MCP_AUTH_METHOD` and `ORACLE_MCP_AUTH_PROFILE`
for `OCI_MCP_AUTH_TYPE` and `OCI_CONFIG_PROFILE`, and `ORACLE_MCP_TENANCY_ID` /
`TENANCY_ID_OVERRIDE` for `OCI_MCP_TENANCY_ID_OVERRIDE`. Where both are set, the
`OCI_*` name wins. A few further variables tune internals (telemetry identifiers, log
redaction, cache sizing); they have working defaults and are documented at their
definitions in the source.

## Tools

Most resource tools accept `region` where the OCI API supports it. The supported list and summary tools accept `fetch_for_child_compartment=true` to include the requested compartment and its descendants.

| Area | Tools |
| --- | --- |
| Protected databases | `list_protected_databases`, `get_protected_database`, `summarize_protected_database_health`, `summarize_protected_database_redo_status`, `summarize_backup_space_used` |
| Recovery Service | `check_recovery_service_limits`, `fetch_regions_subscribed`, `list_protection_policies`, `get_protection_policy`, `list_recovery_service_subnets`, `get_recovery_service_subnet`, `get_recovery_service_metrics`, `list_restore` |
| Database Service and backups | `list_databases`, `get_database`, `list_backups`, `get_backup`, `summarize_protected_database_backup_destination`, `list_db_homes`, `get_db_home`, `list_db_systems`, `get_db_system` |
| Guidance | `oci_recovery_service_dashboard_prompt`, `onboard_database_to_recovery_service`, `diagnose_recovery_service_issue` |

Use the MCP tool descriptions as the authoritative parameter reference. Some list tools can resolve a compartment display name; OCI resource retrieval tools require the corresponding OCID.

## Development and validation

Install the development dependencies before running tests:

```sh
uv sync --group dev
uv run pytest --cov=. --cov-branch --cov-report=term-missing
```

The test suite is offline: OCI clients are mocked, so no credentials or live resources
are required.

## License

Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at <https://oss.oracle.com/licenses/upl>.
