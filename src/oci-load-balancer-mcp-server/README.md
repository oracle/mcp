# OCI Load Balancer MCP Server

This server provides tools for interacting with Oracle Cloud Infrastructure (OCI) Load Balancer service.

## MCP client configuration (recommended)

Most users should configure their MCP client to launch the server, rather than starting it manually.

Add a stanza like this to your MCP client config (often called `mcp.json`; example shown is **stdio**):

```json
{
  "mcpServers": {
    "oci-load-balancer": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "oracle.oci-load-balancer-mcp-server"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT"
      }
    }
  }
}
```
