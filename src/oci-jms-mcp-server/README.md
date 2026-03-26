# OCI JMS MCP Server

## Overview

This server provides tools to interact with Oracle Cloud Infrastructure Java Management Service (JMS).
It focuses on fleet inventory, discovery, and health troubleshooting workflows.

## Authentication

This server expects OCI session-token auth through a normal OCI CLI config file.

- Use `OCI_CONFIG_FILE` to point at the OCI config file
- Use `OCI_CONFIG_PROFILE` to select the profile
- The configured profile must include a valid `security_token_file`
- Refresh expired sessions with `oci session authenticate ...`

This server does **not** use the env names from the separate `oci_api_mcp` project.


- Use `OCI_CONFIG_FILE`, not `OCI_CONFIG`
- Use `OCI_CONFIG_PROFILE`, not `OCI_PROFILE`

## JMS Environment Endpoint Selection

By default, this server lets the OCI Python SDK derive the production JMS endpoint from the OCI config region.

For dev and other non-prod JMS environments, set `JMS_TEST_ENVIRONMENT` to derive the service endpoint using the same environment naming pattern used by JMS Java tooling.

Supported base values:

- `PROD`
- `HERDS`
- `DEV`
- `DEV2`
- `DEV3`
- `TEST`
- `TEST2`
- `TEST3`
- `STAGE`
- `VANILLA`

Optional suffixes are allowed and ignored for endpoint derivation, for example `DEV-canary` or `DEV_canary`.

Examples:

- `JMS_TEST_ENVIRONMENT=DEV` -> `https://javamanagement-dev.<region>.oci.oc-test.com`
- `JMS_TEST_ENVIRONMENT=TEST` -> `https://javamanagement-test.<region>.oci.oc-test.com`
- `JMS_TEST_ENVIRONMENT=TEST2` -> `https://javamanagement-test2.<region>.oci.oc-test.com`
- `JMS_TEST_ENVIRONMENT=STAGE` -> `https://javamanagement-stage.<region>.oci.oc-test.com`
- `JMS_TEST_ENVIRONMENT=HERDS` -> `https://javamanagement-herds.<region>.oci.rbcloud.oc-test.com`

When `JMS_TEST_ENVIRONMENT=PROD` or the variable is unset, the server keeps the default SDK-derived production endpoint.

## Running the server

From the JMS package directory:

```sh
cd src/oci-jms-mcp-server
mkdir -p /tmp/uv-cache
UV_CACHE_DIR=/tmp/uv-cache uv sync
```

### STDIO transport mode

```sh
OCI_CONFIG_FILE=~/.oci/config OCI_CONFIG_PROFILE=DEFAULT UV_CACHE_DIR=/tmp/uv-cache uv run oracle.oci-jms-mcp-server
```

Non-prod example:

```sh
OCI_CONFIG_FILE=~/.oci/config OCI_CONFIG_PROFILE=DEFAULT JMS_TEST_ENVIRONMENT=DEV UV_CACHE_DIR=/tmp/uv-cache uv run oracle.oci-jms-mcp-server
```

### HTTP streaming transport mode

```sh
OCI_CONFIG_FILE=~/.oci/config OCI_CONFIG_PROFILE=DEFAULT UV_CACHE_DIR=/tmp/uv-cache ORACLE_MCP_HOST=127.0.0.1 ORACLE_MCP_PORT=8888 uv run oracle.oci-jms-mcp-server
```

Non-prod example:

```sh
OCI_CONFIG_FILE=~/.oci/config OCI_CONFIG_PROFILE=DEFAULT JMS_TEST_ENVIRONMENT=TEST UV_CACHE_DIR=/tmp/uv-cache ORACLE_MCP_HOST=127.0.0.1 ORACLE_MCP_PORT=8888 uv run oracle.oci-jms-mcp-server
```

The HTTP endpoint is:

```text
http://127.0.0.1:8888/mcp
```

## MCP Client Configuration

### Cline / stdio

```json
{
  "mcpServers": {
    "oracle-oci-jms-mcp-server": {
      "type": "stdio",
      "command": "/bin/zsh",
      "args": [
        "-lc",
        "cd src/oci-jms-mcp-server && OCI_CONFIG_FILE=~/.oci/config OCI_CONFIG_PROFILE=DEFAULT UV_CACHE_DIR=/tmp/uv-cache uv run oracle.oci-jms-mcp-server"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

### Cline / HTTP

Run the server manually, then configure:

```json
{
  "mcpServers": {
    "oracle-oci-jms-mcp-server": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8888/mcp"
    }
  }
}
```

## Verification

Verify the server through an MCP agent in this order:

1. List the tools from `oracle-oci-jms-mcp-server`
2. Call `list_fleets` for a known compartment
3. Use one returned fleet OCID in `get_fleet`

Prefer verifying `get_fleet` only with an OCID returned by `list_fleets`. If `get_fleet` fails with `NotAuthorizedOrNotFound`, first confirm the fleet is visible to the active profile.

## Troubleshooting

- If startup falls back to stdio, make sure both `ORACLE_MCP_HOST` and `ORACLE_MCP_PORT` are set.
- If `uv` fails with `Failed to initialize cache`, create a writable cache directory and run with `UV_CACHE_DIR=/tmp/uv-cache`.
- If `get_fleet` returns `NotAuthorizedOrNotFound`, verify:
  - the active `OCI_CONFIG_PROFILE`
  - the region/tenancy for the fleet OCID
  - IAM permission to read JMS fleets
  - the fleet exists by first calling `list_fleets`
- If your client config was copied from `oci_api_mcp`, replace `OCI_CONFIG`/`OCI_PROFILE` with `OCI_CONFIG_FILE`/`OCI_CONFIG_PROFILE`.
- If you set `JMS_TEST_ENVIRONMENT`, make sure the OCI config contains a `region`.
- If you need a dev endpoint, set `JMS_TEST_ENVIRONMENT`; tool inputs do not accept a per-call endpoint override.
- Blank optional filter values are ignored. For example, empty `time_start`, `time_end`, or blank entries in `os_family` are treated as unset inputs instead of being sent to the OCI SDK.

## Tools

| Tool Name | Description |
| --- | --- |
| list_fleets | List JMS fleets in a compartment |
| get_fleet | Get a JMS fleet by OCID |
| list_jms_plugins | List JMS plugins in a compartment or fleet |
| get_jms_plugin | Get a JMS plugin by OCID |
| list_installation_sites | List Java installation sites in a JMS fleet |
| get_fleet_agent_configuration | Get fleet agent configuration |
| get_fleet_advanced_feature_configuration | Get fleet advanced feature configuration |
| summarize_resource_inventory | Summarize JMS resource inventory |
| summarize_managed_instance_usage | Summarize managed instance usage in a fleet |
| summarize_fleet_health | Summarize fleet health using diagnoses and fleet errors |
| get_fleet_health_diagnostics | Get detailed fleet health diagnoses and fleet errors |
| list_jms_notices | List JMS announcements and notices |
| java_runtime_compliance | Summarize Java runtime compliance for a fleet |

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
