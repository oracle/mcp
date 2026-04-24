# OCI Identity MCP Server

## Overview

This server provides tools to interact with the OCI Identity service.

## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-identity-mcp-server
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
uvx oracle.oci-identity-mcp-server
```

Register `${ORACLE_MCP_BASE_URL}/auth/callback` in the OCI IAM confidential application. If `IDCS_REQUIRED_SCOPES` is unset, the default is `openid profile email oci_mcp.identity.invoke`.

## Environment Variables

The server supports the following environment variables:

- `OCI_CONFIG_PROFILE`: OCI configuration profile name (default: "DEFAULT")
- `TENANCY_ID_OVERRIDE`: Overrides the tenancy ID from the config file

## Tools

| Tool Name | Description |
| --- | --- |
| list_compartments | List compartments in a given tenancy. |
| get_tenancy_info | Get tenancy information. |
| list_availability_domains | List availability domains in a given tenancy. |
| get_current_tenancy | Get current tenancy information. |
| create_auth_token | Create an authentication token for a user. |
| get_current_user | Get current user information. |
| get_compartment_by_name | Return a compartment matching the provided name                              |
| list_subscribed_regions | Return a list of all regions the customer (tenancy) is subscribed to         |


⚠️ **NOTE**: `stdio` uses the configured OCI CLI profile. HTTP uses the authenticated OCI IAM user and does not use the local OCI CLI profile for request authentication.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
