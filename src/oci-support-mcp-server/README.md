# OCI Support MCP Server

## Overview

This MCP server provides tools to interact with Oracle Cloud Infrastructure (OCI) Support resources via the CIMS API. The server enables listing and managing support tickets, validating users making it easy to automate and monitor support operations.

## Running the server

### STDIO transport mode (for local testing)

```sh
uv oracle.oci-support-mcp-server
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<hostname/IP address> ORACLE_MCP_PORT=<port number> uv oracle.oci-support-mcp-server
```

## Tools

| Tool Name | Description |
| --- | --- |
| list_incidents | List support incidents for the tenancy using Oracle CIMS. |
| get_incident | Get details of a specific support incident. |
| create_incident | Create a new support incident with all required details. |
| list_incident_resource_types | List available incident resource types (products, services, service categories) for OCI support requests. |
| validate_user | Validate if a user (by OCID/CSI and credentials) is permitted for OCI support operations. |

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Authentication

> **Important:**  
> The OCI Support MCP Server does NOT support `oci session authenticate` or token-based authentication.  
> Instead, it authenticates exclusively using the OCI config file with a private key and fingerprint.

You must provide credentials in the standard OCI CLI config file (see [OCI docs](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm)).

**Example environment configuration for Cline or compatible clients:**

```json
{
  "mcpServers": {
    "oracle-oci-support-mcp-server": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "oracle.oci-support-mcp-server"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "<profile>",        // OCI CLI profile with private key & fingerprint
        "OCI_CONFIG_FILE": "/.oci/config"        // Path to the OCI CLI config file (typically ~/.oci/config)
      }
    }
  }
}
```
- `OCI_CONFIG_PROFILE` — This is the name of your OCI config CLI profile that includes the correct private key and fingerprint.
- `OCI_CONFIG_FILE` — Path to the OCI CLI config file (default: `~/.oci/config`).

⚠️ **NOTE:** Session-based or ephemeral authentication (e.g., using `oci session authenticate`) is **not supported** for the Support MCP Server. Only config-file-based authentication is supported.

## Third-Party APIs

Developers distributing a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for third-party code to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Use of this software may impact OCI support configuration if misused. Different LLM/model selections and prompt configurations can yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
