# OCI Compute MCP Server

## Overview
This server provides tools to interact with the OCI Compute resources.
It includes resources and tools to help with managing compute instances.

## Running the server
```sh
uv run oracle.oci-compute-mcp-server
```

## Tools and Resources
| Tool/Resource Name | Description |
| --- | --- |
| list_instances | List Instances in a given compartment |
| get_instance | Get Instance with a given instance OCID |
| launch_instance | Create a new instance |
| terminate_instance | Terminate an instance |
| update_instance | Update instance configuration |
| list_images | List images in a given compartment |
| get_image | Get Image with a given image OCID |
| instance_action | Perform actions on a given instance |

<span style="font-size: small;">Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.</span>
