# OCI Object Storage MCP Server

## Overview

This server provides tools to interact with the OCI Object Storage resources.
It includes tools to help with managing object storage configurations.

## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-object-storage-mcp-server
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<hostname/IP address> ORACLE_MCP_PORT=<port number> uvx oracle.oci-object-storage-mcp-server
```

## Tools

| Tool Name | Description |
| --- | --- |
| get_namespace | Get the object storage namespace for the tenancy |
| list_buckets | List object storage buckets in a given compartment |
| get_bucket_details | Get details for a specific object storage bucket |
| list_objects | List objects in a given object storage bucket |
| list_object_versions | List object versions in a given object storage bucket |
| get_object | Get a specific object from an object storage bucket |
| upload_object | Upload an object to an object storage bucket |

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.

