# OCI Cloud MCP Server

## Overview

This server provides tools to interact with Oracle Cloud Infrastructure (OCI) services using the official OCI Python SDK directly (no OCI CLI subprocess calls). It exposes generic tools that let you:
- Invoke any OCI SDK client operation by fully-qualified client class and method name
- Discover available operations for a given OCI client

## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-cloud-mcp-server
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<hostname/IP address> ORACLE_MCP_PORT=<port number> uvx oracle.oci-cloud-mcp-server
```

## Quick start

### Easiest working setup: local OCI config

If you already have a working OCI CLI config in `~/.oci/config`, this is the fastest path.

1. Make sure your OCI profile works.
2. Start the server:

```sh
uvx oracle.oci-cloud-mcp-server
```

3. Call a simple tool such as:

```json
{
  "client_fqn": "oci.identity.IdentityClient",
  "operation": "list_regions",
  "params": {}
}
```

If your profile is not `DEFAULT`, set it first:

```sh
export OCI_CONFIG_PROFILE=MY_PROFILE
uvx oracle.oci-cloud-mcp-server
```

If your config file is not in the default location:

```sh
export OCI_CONFIG_FILE=/full/path/to/config
uvx oracle.oci-cloud-mcp-server
```

### Easy HTTP + OIDC example

Use this when your MCP client connects over HTTP. HTTP mode requires IDCS-backed OIDC authentication for every OCI tool call.

```sh
export IDCS_DOMAIN="example.identity.oraclecloud.com"
export IDCS_CLIENT_ID="<client-id>"
export IDCS_CLIENT_SECRET="<client-secret>"
export ORACLE_MCP_HOST="127.0.0.1"
export ORACLE_MCP_PORT="5000"
export OCI_REGION="us-phoenix-1"  # only needed when you are not using ~/.oci/config

uvx oracle.oci-cloud-mcp-server
```

Then connect your MCP client to `http://127.0.0.1:5000` and authenticate through IDCS before invoking OCI tools.

## Tools

| Tool Name | Description |
| --- | --- |
| invoke_oci_api | Invoke an OCI Python SDK API via client and operation name. Example: client_fqn="oci.core.ComputeClient", operation="list_instances", params={"compartment_id": "ocid1.compartment.oc1..."} |
| list_client_operations | List public callable operations for a given OCI client class (by fully-qualified name). |

### invoke_oci_api

- client_fqn: Fully-qualified client class name, e.g. `oci.core.ComputeClient`
- operation: Client method/operation, e.g. `list_instances`, `get_instance`, `launch_instance`, etc.
- params: JSON object of keyword arguments as expected by the SDK method (snake_case). For list operations, the server automatically paginates to return all results.

Example usage:
```json
{
  "client_fqn": "oci.core.ComputeClient",
  "operation": "list_instances",
  "params": {
    "compartment_id": "ocid1.compartment.oc1..exampleuniqueID"
  }
}
```

Response (shape):
```json
{
  "client": "oci.core.ComputeClient",
  "operation": "list_instances",
  "params": { "...": "..." },
  "opc_request_id": "abcd-efgh-....",
  "data": [ /* JSON-serialized OCI SDK response data */ ]
}
```

### list_client_operations

- client_fqn: Fully-qualified client class name, e.g. `oci.identity.IdentityClient`

Returns a list of operations with a short summary extracted from docstrings when available.

## Passing complex model parameters

Many OCI SDK operations expect complex model instances (e.g., CreateVcnDetails) rather than raw dictionaries.
This server now automatically constructs SDK model objects from JSON parameters using heuristics:

- If a parameter name ends with "_details", "_config", "_configuration", or "_source_details", the value will be
  coerced into the appropriate model class from the client's models module.
  - Example: For VirtualNetworkClient.create_vcn, either of these will work:
    {
      "client_fqn": "oci.core.VirtualNetworkClient",
      "operation": "create_vcn",
      "params": {
        "create_vcn_details": {
          "cidr_block": "10.0.0.0/16",
          "compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
          "display_name": "my-vcn"
        }
      }
    }
    {
      "client_fqn": "oci.core.VirtualNetworkClient",
      "operation": "create_vcn",
      "params": {
        "vcn_details": {
          "cidr_block": "10.0.0.0/16",
          "compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
          "display_name": "my-vcn"
        }
      }
    }
  In both cases, the server will construct an instance of oci.core.models.CreateVcnDetails.

- For "create_*" and "update_*" operations, if the parameter is named like "vcn_details" (missing the verb),
  the server will also try CreateVcnDetails/UpdateVcnDetails automatically.

- Nested dictionaries and lists inside such parameters are recursively coerced. For lists that do not obviously
  map to a model type, you can provide explicit hints.

Explicit model hints (optional):
- __model: Simple class name in the client's models module (e.g., "CreateVcnDetails")
- __model_fqn: Fully-qualified class name (e.g., "oci.core.models.CreateVcnDetails")

Example with explicit hint:
{
  "client_fqn": "oci.core.VirtualNetworkClient",
  "operation": "create_vcn",
  "params": {
    "create_vcn_details": {
      "__model": "CreateVcnDetails",
      "cidr_block": "10.0.0.0/16",
      "compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
      "display_name": "my-vcn"
    }
  }
}

Note:
- Parameter names must match the SDK's expected kwargs. For example, the SDK expects "create_vcn_details" for create_vcn.
  The heuristic also accepts "vcn_details" and will resolve it to the correct model class, but the keyword name still needs to be correct for other methods without such ambiguity.

## Authentication and configuration

This server supports two outbound OCI auth flows:

### 1. Local OCI config flow

This is the default behavior for stdio usage.

- Loads OCI configuration from `OCI_CONFIG_FILE` when set, otherwise from `~/.oci/config`
- Uses `OCI_CONFIG_PROFILE` when set, otherwise `DEFAULT`
- Adds an additional user-agent suffix for MCP telemetry
- Prefers a Security Token Signer when `security_token_file` is available; otherwise falls back to API key signer

### 2. OIDC token exchange flow

For authenticated HTTP requests, the server uses the OCI Python SDK's `TokenExchangeSigner` to exchange the caller's OIDC JWT for an OCI UPST and sign OCI SDK calls. This matches the Oracle sample flow in `oracle-samples/mcp-examples/server`.

HTTP transport is only available when the IDCS variables below are configured. Unauthenticated HTTP requests are rejected and do not fall back to the local OCI config flow.

Required variables:

- `IDCS_DOMAIN`
- `IDCS_CLIENT_ID`
- `IDCS_CLIENT_SECRET`
- `ORACLE_MCP_HOST`
- `ORACLE_MCP_PORT`

Optional helpers:

- `OCI_REGION` when you want to use OIDC auth without relying on an OCI config file for region settings

Example OIDC setup:

```sh
export IDCS_DOMAIN="example.identity.oraclecloud.com"
export IDCS_CLIENT_ID="<client-id>"
export IDCS_CLIENT_SECRET="<client-secret>"
export ORACLE_MCP_HOST="127.0.0.1"
export ORACLE_MCP_PORT="5000"
export OCI_REGION="us-phoenix-1"  # only needed when not using ~/.oci/config
uv run oracle.oci-cloud-mcp-server
```

In this mode, authenticated OIDC HTTP requests use token exchange automatically. Local OCI config remains available for stdio only.

Ensure the effective principal for either path has the necessary permissions (least privilege recommended).

## Security and privacy

All actions are performed with the permissions of the configured OCI profile. Follow best practices:
- Use least-privilege IAM policies
- Manage credentials securely
- Avoid logging sensitive data
- Be mindful of network egress and data residency

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
