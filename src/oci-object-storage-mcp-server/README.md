# OCI Object Storage MCP Server

## Overview
This server provides tools to interact with the OCI Object Storage resources.
It includes resources and tools to help with managing object storage configurations.

## Running the server
```sh
uv run oracle.oci-object-storage-mcp-server
```

## Tools and Resources
| Tool/Resource Name | Description |
| --- | --- |
| get_namespace | Get the object storage namespace for the tenancy |
| list_buckets | List object storage buckets in a given compartment |
| get_bucket_details | Get details for a specific object storage bucket |
| list_objects | List objects in a given object storage bucket |
| list_object_versions | List object versions in a given object storage bucket |
| get_object | Get a specific object from an object storage bucket |
| upload_object | Upload an object to an object storage bucket |

<span style="font-size: small;">Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.</span>
