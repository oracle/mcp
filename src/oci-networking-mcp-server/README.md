# OCI Networking MCP Server

## Overview
This server provides tools to interact with the OCI Networking resources.
It includes resources and tools to help with managing network configurations.

## Running the server
```sh
uv run oracle.oci-networking-mcp-server
```

## Tools and Resources
| Tool/Resource Name | Description |
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

<span style="font-size: small;">Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.</span>
