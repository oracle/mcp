# OCI Compute Instance Agent MCP Server

## Overview

This server provides tools for interacting with Oracle Cloud Infrastructure (OCI) Compute Instance Agent service.

## MCP client configuration (recommended)

Most users should configure their MCP client to launch the server, rather than starting it manually.

Add a stanza like this to your MCP client config (often called `mcp.json`; example shown is **stdio**):

```json
{
  "mcpServers": {
    "oci-compute-instance-agent": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "oracle.oci-compute-instance-agent-mcp-server"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT"
      }
    }
  }
}
```

## Run the server locally (HTTP transport)

Most MCP clients run this server for you over **stdio** (see above). If you want to run the server as a standalone
service and connect to it over HTTP (**streamable HTTP**), you can.

1) Start the server in HTTP mode (choose host/port):

```bash
ORACLE_MCP_HOST=127.0.0.1 ORACLE_MCP_PORT=8000 uvx oracle.oci-compute-instance-agent-mcp-server
```

This will expose the MCP endpoint at:

`http://127.0.0.1:8000/mcp`

2) Configure your MCP client to connect via `streamableHttp`:

> Note: MCP client configuration varies by client/tooling. Some clients refer to streamable HTTP as just `http`.

```json
{
  "mcpServers": {
    "oci-compute-instance-agent": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
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
