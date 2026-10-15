# OCI Identity Policy MCP Server: Full Guide

This module is a thin, pip-only wrapper around the released
[`oci-policy-analysis`](https://github.com/agregory999/oci-policy-analysis)
package. It exposes that package's MCP entry point without duplicating its
implementation.

The wrapper requires Python 3.13 or later and `oci-policy-analysis` 6.5.1 or
later. It does not provide a container image or OCI Container Instance
deployment path.

## What it provides

The implementation comes from `oci-policy-analysis[mcp]`. Its MCP tools
search OCI IAM policies, users, groups, dynamic groups, identity domains,
compartments, cached snapshots, and cross-tenancy policy statements.

| Tool | Use it for |
| --- | --- |
| `policy_search` | Search OCI IAM policies for one policy question, such as who can manage a resource. |
| `policy_search_set` | Run related policy searches and summarize coverage for an access review or installation validation. |
| `policy_history_search` | Compare policy-search results across cached snapshots. |
| `identity_search` | Search users, groups, dynamic groups, compartments, identity domains, and memberships. |
| `data_operations` | Check readiness, list or load caches, and reload OCI data. |
| `cross_tenancy_search` | List cross-tenancy aliases or search cross-tenancy policy statements. |
| `oke_workload_identity_search` | Search policies that grant access to OKE workload identities. |
| `tag_based_policy_search` | Search parsed tag-based policy conditions and associated warnings. |

## Prerequisites and IAM access

Install Python 3.13 or later and the OCI CLI. The examples use the OCI CLI
`DEFAULT` profile, normally configured in `~/.oci/config`.

The principal that loads live tenancy data needs read-only identity and policy
permissions. Create or use a narrowly scoped group, then grant:

```text
allow group PolicyAnalysisUsers to {POLICY_READ, COMPARTMENT_INSPECT, DOMAIN_INSPECT, DYNAMIC_GROUP_INSPECT, GROUP_INSPECT, USER_INSPECT, LIMITS_VIEW_INSPECT} in tenancy
```

Verify the profile before starting the server:

```sh
oci iam region list --profile DEFAULT
```

## Install with pip

Create an isolated virtual environment, upgrade pip, and install the released
package. The `mcp` extra installs the MCP server dependencies; the released
base package also provides the cache-management command.

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --upgrade "oci-policy-analysis[mcp]>=6.5.1"
```

When developing this wrapper from a clone, install the wrapper itself into the
same environment:

```sh
.venv/bin/python -m pip install -e src/oci-identity-policy-mcp-server
```

Verify both upstream entry points and the wrapper console script:

```sh
python -m oci_policy_analysis.cli --help
python -m oci_policy_analysis.mcp_server --help
oracle.oci-identity-policy-mcp-server --help
```

## Run the server

For a desktop MCP client, use standard input/output and your `DEFAULT` OCI
profile:

```sh
python -m oci_policy_analysis.mcp_server --profile DEFAULT --transport stdio
```

For a local MCP client that supports Streamable HTTP:

```sh
python -m oci_policy_analysis.mcp_server \
  --profile DEFAULT \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8765 \
  --log-level INFO
```

The MCP endpoint is `http://127.0.0.1:8765/mcp`; the health endpoint is
`http://127.0.0.1:8765/health`. Keep an HTTP server bound to localhost unless
you have an authenticated, trusted network boundary.

## Additional MCP server parameters

Choose exactly one authentication or data source: `--profile`,
`--instance-principal`, `--resource-principal`, `--session-token`, or
`--use-cache`. The following options are useful when adapting the server to
your tenancy and runtime environment.

| Parameter | When to use it |
| --- | --- |
| `--compartment-domain-search-depth 1-6` | Control how far identity-domain discovery traverses from the root compartment. Use `1` for root-only domains, `2` to include direct children, and a larger value only when domains are nested more deeply. |
| `--instance-principal` | Run on an OCI Compute instance using its instance principal instead of an OCI CLI profile. |
| `--resource-principal` | Run in an OCI resource that supplies a resource principal, such as a supported OCI managed runtime. |
| `--use-cache <CACHE_NAME>` | Start from an existing combined cache rather than loading live tenancy data. This will be on your local machine after a previous run loading from a live tenancy.|
| `--dont-save-cache-after-load` | Avoid writing a combined cache after a live load. |
| `--log-level INFO` | Increase standalone-server diagnostics while troubleshooting. |

### Run on an OCI Compute instance

To use an instance principal, create a dynamic group that includes the Compute
instance and grant it the same read-only IAM permissions listed above. Then
start the server without `--profile`:

```sh
python -m oci_policy_analysis.mcp_server \
  --instance-principal \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8765
```

The OCI SDK obtains the instance principal automatically. The instance still
needs network access to the OCI Identity service endpoints for its region.

## MCP client configuration

Use the absolute path to the virtual environment's Python executable, not a
shell-dependent `python` alias.

### Find `PYTHON_EXECUTABLE`

Activate the virtual environment, then run `which python` and use the returned
absolute path wherever these examples show `<PYTHON_EXECUTABLE>`:

```sh
source .venv/bin/activate
which python
```

### Claude Desktop

Add an entry to Claude Desktop's MCP configuration, replacing
`<PYTHON_EXECUTABLE>` with the absolute path to `.venv/bin/python`:

```json
{
  "mcpServers": {
    "oci-policy": {
      "command": "<PYTHON_EXECUTABLE>",
      "args": ["-m", "oci_policy_analysis.mcp_server", "--profile", "DEFAULT", "--transport", "stdio"]
    }
  }
}
```

### Codex

Add this to Codex `config.toml`, replacing `<PYTHON_EXECUTABLE>` with an
absolute path:

```toml
[mcp_servers.oci_policy]
command = "<PYTHON_EXECUTABLE>"
args = ["-m", "oci_policy_analysis.mcp_server", "--profile", "DEFAULT", "--transport", "stdio"]
```

For a server already running locally over HTTP:

```toml
[mcp_servers.oci_policy]
url = "http://127.0.0.1:8765/mcp"
```

## Caches and authentication

Live profile loading is the simplest first validation. If the data is large or
you want predictable startup, use the upstream CLI to create and list caches,
then start the MCP server with `--use-cache <CACHE_NAME>`.

```sh
python -m oci_policy_analysis.cli --help
python -m oci_policy_analysis.mcp_server --use-cache <CACHE_NAME> --transport stdio
```

The released package also supports the authentication modes documented by its
command help, including instance principal, resource principal, and
session-token based workflows. Pass those arguments directly to
`oci_policy_analysis.mcp_server`; this wrapper does not translate environment
variables or manage credentials.

## Troubleshooting

- If the module cannot be imported, activate the virtual environment and rerun
  the pip install command.
- If the OCI profile is unavailable, run `oci iam region list --profile DEFAULT`
  and inspect `~/.oci/config` and the selected profile name.
- If live loading returns authorization errors, verify the policy permissions
  above and that they are attached to the same principal used by the profile.
- If a desktop client cannot start the server, use the absolute venv Python path
  in its configuration and run the same command in a terminal first.
- For option details and supported authentication modes, run
  `python -m oci_policy_analysis.mcp_server --help` from the installed
  environment.

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
