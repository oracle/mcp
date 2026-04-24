# OCI Cloud Guard MCP Server

## Overview

This package implements certain functions of the [OCI Cloud Guard Service](https://docs.oracle.com/en-us/iaas/Content/cloud-guard/home.htm).
It includes tools to help with managing cloud guard problems.

## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-cloud-guard-mcp-server
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
uvx oracle.oci-cloud-guard-mcp-server
```

Register `${ORACLE_MCP_BASE_URL}/auth/callback` in the OCI IAM confidential application. If `IDCS_REQUIRED_SCOPES` is unset, the default is `openid profile email oci_mcp.cloud_guard.invoke`.

## Tools

| Tool Name             | Description                               |
|-----------------------|-------------------------------------------|
| list_problems         | List the problems in a given compartment  |
| get_problem_details   | Get the problem details with a given OCID |
| update_problem_status | Updates the status of a problem           |

⚠️ **NOTE**: `stdio` uses the configured OCI CLI profile. HTTP uses the authenticated OCI IAM user and does not use the local OCI CLI profile for request authentication.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
