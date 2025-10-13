# OCI Identity MCP Server

## Overview

This server provides tools to interact with the OCI Identity service.

## Running the server

```sh
uv run oracle.oci-identity-mcp-server
```

## Tools

| Tool Name | Description |
| --- | --- |
| list_compartments | List compartments in a given tenancy. |
| get_tenancy_info | Get tenancy information. |
| list_availability_domains | List availability domains in a given tenancy. |
| get_current_tenancy | Get current tenancy information. |
| create_auth_token | Create an authentication token for a user. |
| get_current_user | Get current user information. |

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.

