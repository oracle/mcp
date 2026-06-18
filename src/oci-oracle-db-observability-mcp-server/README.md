# Oracle DB Observability MCP Servers

## Overview

This package provides MCP servers to interact with Oracle database observability services.
It currently includes separate v1 servers for OCI Operations Insights (OPSI) and OCI
Database Management (DBM).

## Running the OPSI server

### STDIO transport mode

```sh
uvx oracle.oci-opsi-mcp-server
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<bind_host> \
ORACLE_MCP_PORT=<port> \
ORACLE_MCP_BASE_URL=<public_base_url> \
OCI_REGION=<region> \
IDCS_DOMAIN=<idcs_domain> \
IDCS_CLIENT_ID=<client_id> \
IDCS_CLIENT_SECRET=<client_secret> \
IDCS_AUDIENCE=<audience> \
uvx oracle.oci-opsi-mcp-server
```

Register `${ORACLE_MCP_BASE_URL}/auth/callback` in the OCI IAM confidential application.
If `IDCS_REQUIRED_SCOPES` is unset, the default is `openid profile email oci_mcp.opsi.invoke`.

## Running the DBM server

### STDIO transport mode

```sh
uvx oracle.oci-dbm-mcp-server
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<bind_host> \
ORACLE_MCP_PORT=<port> \
ORACLE_MCP_BASE_URL=<public_base_url> \
OCI_REGION=<region> \
IDCS_DOMAIN=<idcs_domain> \
IDCS_CLIENT_ID=<client_id> \
IDCS_CLIENT_SECRET=<client_secret> \
IDCS_AUDIENCE=<audience> \
uvx oracle.oci-dbm-mcp-server
```

Register `${ORACLE_MCP_BASE_URL}/auth/callback` in the OCI IAM confidential application.
If `IDCS_REQUIRED_SCOPES` is unset, the default is `openid profile email oci_mcp.dbm.invoke`.

## Tools

| Tool Group | Description |
| --- | --- |
| OPSI tools | 158 non-deprecated OCI Operations Insights SDK methods, excluding `delete_*` methods and excluded operation classes from `docs/tool-list.csv`. Tool names match SDK method names. |
| DBM tools | 266 OCI Database Management SDK methods, excluding `delete_*`, `drop_*`, deprecated MySQL/HeatWave operations, and excluded operation classes from `docs/tool-list.csv`. Tool names match SDK method names. |
| get_compartment | Get an OCI compartment with a given compartment OCID. |
| list_compartments | List OCI compartments from a root compartment. |

## Generating OPSI MCP files

The OPSI tool, model, and manifest files can be generated from the Oracle OpenAPI spec.
Use a local spec for deterministic offline generation:

```sh
uv run oci-oracle-db-observability-mcp-server-generate-opsi --spec-file <openapi-yaml>
```

To verify checked-in generated files without rewriting them:

```sh
uv run oci-oracle-db-observability-mcp-server-generate-opsi --spec-file <openapi-yaml> --check
```

If `--spec-file` is omitted, the generator resolves `operations-insights` from the Oracle
API spec index URL and fetches the referenced spec.

⚠️ **NOTE**: `stdio` uses the configured OCI CLI profile. HTTP uses the authenticated OCI IAM
user and does not use the local OCI CLI profile for request authentication.

⚠️ **NOTE**: Non-delete mutating OPSI tools and non-delete, non-drop mutating DBM tools are
marked with MCP tool annotations because they can change OCI or database state.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
