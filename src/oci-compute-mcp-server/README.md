# OCI Compute MCP Server

## Overview

This server provides tools to interact with the OCI Compute resources.
It includes tools to help with managing compute instances.

## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-compute-mcp-server
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<hostname/IP address> ORACLE_MCP_PORT=<port number> uvx oracle.oci-compute-mcp-server
```

## Tools

| Tool Name | Description |
| --- | --- |
| list_instances | List Instances in a given compartment |
| get_instance | Get Instance with a given instance OCID |
| launch_instance | Create a new instance |
| terminate_instance | Terminate an instance |
| update_instance | Update instance configuration |
| list_images | List images in a given compartment |
| get_image | Get Image with a given image OCID |
| instance_action | Perform actions on a given instance |

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
