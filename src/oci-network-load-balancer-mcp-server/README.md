# OCI Network Load Balancer MCP Server

## Overview
This server provides tools to interact with the OCI Network Load Balancer resources.
It includes resources and tools to help with managing network load balancers.

## Running the server
```sh
uv run oracle.oci-network-load-balancer-mcp-server
```

## Tools and Resources
| Tool/Resource Name | Description |
| --- | --- |
| list_network_load_balancers | List network load balancers in a given compartment |
| get_network_load_balancer | Get network load balancer details |
| list_network_load_balancer_listeners | List listeners in a given network load balancer |
| get_network_load_balancer_listener | Get a listener with a given listener name from a network load balancer |
| list_network_load_balancer_backend_sets | List backend sets in a given network load balancer |
| get_network_load_balancer_backend_set | Get a backend set with a given backend set name from a network load balancer |
| list_network_load_balancer_backends | List backends in a given backend set and network load balancer |
| get_network_load_balancer_backend | Get a backend with a given backend name from a backend set and network load balancer |

<span style="font-size: small;">Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.</span>
