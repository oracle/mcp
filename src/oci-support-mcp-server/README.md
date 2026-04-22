# OCI Support MCP Server

## Overview

This MCP server provides tools to interact with Oracle Cloud Infrastructure (OCI) Support resources via the CIMS API. The server enables listing and managing support tickets, validating users making it easy to automate and monitor support operations.

## MCP client configuration (recommended)

Most users should configure their MCP client to launch the server, rather than starting it manually.

Add a stanza like this to your MCP client config (often called `mcp.json`; example shown is **stdio**):

```json
{
  "mcpServers": {
    "oci-support": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "oracle.oci-support-mcp-server"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT"
      }
    }
  }
}
```

For HTTP transport, start the server with:

```sh
ORACLE_MCP_HOST=<bind_host> \
ORACLE_MCP_PORT=<port> \
ORACLE_MCP_BASE_URL=<public_base_url> \
OCI_REGION=<region> \
IDCS_DOMAIN=<idcs_domain> \
IDCS_CLIENT_ID=<client_id> \
IDCS_CLIENT_SECRET=<client_secret> \
IDCS_AUDIENCE=<audience> \
uvx oracle.oci-support-mcp-server
```

Register `${ORACLE_MCP_BASE_URL}/auth/callback` in the OCI IAM confidential application. If `IDCS_REQUIRED_SCOPES` is unset, the default is `openid profile email oci_mcp.support.invoke`.

## Tools

| Tool Name | Description |
| --- | --- |
| list_incidents | List support incidents for the tenancy using Oracle CIMS. |
| get_incident | Get details of a specific support incident. |
| create_incident | Create a new support incident with all required details. |
| list_incident_resource_types | List available incident resource types (products, services, service categories) for OCI support requests. |
| validate_user | Validate if a user (by OCID/CSI and credentials) is permitted for OCI support operations. |

⚠️ **NOTE**: `stdio` uses OCI config-file credentials. HTTP uses the authenticated OCI IAM user and does not use the local OCI CLI profile for request authentication.

## Authentication

For `stdio`, provide credentials in the standard OCI config file (see [OCI docs](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm)). Use API key credentials with a private key and fingerprint.

**Example environment configuration for Cline or compatible clients:**

```json
{
  "mcpServers": {
    "oci-support": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "oracle.oci-support-mcp-server"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT",
        "OCI_CONFIG_FILE": "~/.oci/config"
      }
    }
  }
}
```
- `OCI_CONFIG_PROFILE` — This is the name of your OCI config CLI profile that includes the correct private key and fingerprint.
- `OCI_CONFIG_FILE` — Path to the OCI CLI config file (default: `~/.oci/config`).

`oci session authenticate` is not supported for `stdio`. For HTTP, use the OCI IAM confidential application settings shown above; HTTP does not use the local OCI config for request authentication.

## Third-Party APIs

Developers distributing a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for third-party code to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Use of this software may impact OCI support configuration if misused. Different LLM/model selections and prompt configurations can yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
