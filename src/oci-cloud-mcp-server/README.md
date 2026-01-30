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

This server uses the same configuration as the OCI CLI:
- Loads configuration from the default `~/.oci/config` (or the profile specified by `OCI_CONFIG_PROFILE`)
- Adds an additional user-agent suffix for MCP telemetry
- Prefers a Security Token Signer when `security_token_file` is available; otherwise falls back to API key signer

Ensure your configured principal has the necessary permissions (least privilege recommended).

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
