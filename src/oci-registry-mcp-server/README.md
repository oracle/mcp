# OCI Registry MCP Server

## Overview

This server provides tools to interact with the OCI Registry resources.
It includes tools to help with managing container repositories.


## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-registry-mcp-server
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<hostname/IP address> ORACLE_MCP_PORT=<port number> uvx oracle.oci-registry-mcp-server
```

## Tools

| Tool Name | Description |
| --- | --- |
| create_container_repository | Create a new container repository |
| list_container_repositories | List container repositories in a given compartment |
| get_container_repo_details | Get details for a specific container repository |
| delete_container_repository | Delete a container repository |

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
