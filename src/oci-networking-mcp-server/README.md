# OCI Networking MCP Server

## Overview

This server provides tools to interact with the OCI Networking resources.
It includes tools to help with managing network configurations.

## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-networking-mcp-server
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<bind_host> \
ORACLE_MCP_PORT=<port> \
ORACLE_MCP_BASE_URL=<public_base_url> \
OCI_REGION=<region> \
IDCS_DOMAIN=<idcs_domain> \
IDCS_CLIENT_ID=<client_id> \
IDCS_CLIENT_SECRET=<client_secret> \
IDCS_AUDIENCE=<audience> \
uvx oracle.oci-networking-mcp-server
```

Register `${ORACLE_MCP_BASE_URL}/auth/callback` in the OCI IAM confidential application. If `IDCS_REQUIRED_SCOPES` is unset, the default is `openid profile email oci_mcp.networking.invoke`.

## Tools

| Tool Name | Description |
| --- | --- |
| list_vcns | List Virtual Cloud Networks (VCNs) in a given compartment |
| get_vcn | Get a VCN with a given VCN OCID |
| delete_vcn | Delete a VCN with a given VCN OCID |
| create_vcn | Create a new VCN |
| list_subnets | List subnets in a given compartment and VCN |
| get_subnet | Get a subnet with a given subnet OCID |
| create_subnet | Create a new subnet |
| list_security_lists | List security lists in a given VCN and compartment |
| get_security_list | Get a security list with a given security list OCID |
| list_network_security_groups | List network security groups in a given compartment and VCN |
| get_network_security_group | Get a network security group with a given NSG OCID |

⚠️ **NOTE**: `stdio` uses the configured OCI CLI profile. HTTP uses the authenticated OCI IAM user and does not use the local OCI CLI profile for request authentication.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
