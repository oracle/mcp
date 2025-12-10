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
ORACLE_MCP_HOST=<hostname/IP address> ORACLE_MCP_PORT=<port number> uvx oracle.oci-networking-mcp-server
```

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

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
