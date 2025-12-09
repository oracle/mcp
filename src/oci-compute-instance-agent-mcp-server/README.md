# OCI Compute Instance Agent MCP Server

## Overview

This server provides tools for interacting with Oracle Cloud Infrastructure (OCI) Compute Instance Agent service.

## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-compute-instance-agent-mcp-server
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<hostname/IP address> ORACLE_MCP_PORT=<port number> uvx oracle.oci-compute-instance-agent-mcp-server
```

## Tools

| Tool Name | Description |
| --- | --- |
| list_instance_agent_commands | List instance agent commands |
| get_instance_agent_command | Get instance agent command by ID |
| create_instance_agent_command | Create a new instance agent command |
| list_instance_agent_command_executions | List command executions for an instance agent command |

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
