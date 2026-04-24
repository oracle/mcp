# OCI Monitoring MCP Server

## Overview

This server provides tools for interacting with Oracle Cloud Infrastructure (OCI) Monitoring service.

## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-monitoring-mcp-server
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
uvx oracle.oci-monitoring-mcp-server
```

Register `${ORACLE_MCP_BASE_URL}/auth/callback` in the OCI IAM confidential application. If `IDCS_REQUIRED_SCOPES` is unset, the default is `openid profile email oci_mcp.monitoring.invoke`.

## Tools

| Tool Name             | Description                                                      |
|-----------------------|------------------------------------------------------------------|
| list_alarms           | List Alarms in the tenancy                                       |
| get_metrics_data      | Gets aggregated metric data                                      |
| get_available_metrics | Lists the available metrics a user can query on in their tenancy |

⚠️ **NOTE**: `stdio` uses the configured OCI CLI profile. HTTP uses the authenticated OCI IAM user and does not use the local OCI CLI profile for request authentication.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing
all required licenses and copyright notices for the third-party code used in order to ensure compliance with their
respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield
different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
