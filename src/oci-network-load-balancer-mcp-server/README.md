# OCI Network Load Balancer MCP Server

## Overview

This server provides tools to interact with the OCI Network Load Balancer resources.
It includes tools to help with managing network load balancers.

## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-network-load-balancer-mcp-server
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<hostname/IP address> ORACLE_MCP_PORT=<port number> uvx oracle.oci-network-load-balancer-mcp-server
```

## Tools

| Tool Name | Description |
| --- | --- |
| list_network_load_balancers | List network load balancers in a given compartment |
| get_network_load_balancer | Get network load balancer details |
| list_network_load_balancer_listeners | List listeners in a given network load balancer |
| get_network_load_balancer_listener | Get a listener with a given listener name from a network load balancer |
| list_network_load_balancer_backend_sets | List backend sets in a given network load balancer |
| get_network_load_balancer_backend_set | Get a backend set with a given backend set name from a network load balancer |
| list_network_load_balancer_backends | List backends in a given backend set and network load balancer |
| get_network_load_balancer_backend | Get a backend with a given backend name from a backend set and network load balancer |

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
