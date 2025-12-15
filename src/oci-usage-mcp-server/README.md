# OCI Usage MCP Server

## Overview

This server provides tools for interacting with Oracle Cloud Infrastructure (OCI) Usage service.


## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-usage-mcp-server
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<hostname/IP address> ORACLE_MCP_PORT=<port number> uvx oracle.oci-usage-mcp-server
```

## Tools

| Tool Name | Description |
| --- | --- |
| list_usage_reports | List usage reports in the tenancy |
| get_usage_report | Get usage report by ID |

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
