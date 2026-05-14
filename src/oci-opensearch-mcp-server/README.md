# OCI OpenSearch MCP Server

## Overview

This server provides MCP tools for interacting with the Oracle Cloud Infrastructure (OCI)
OpenSearch control plane.

It exposes a focused, SDK-backed set of OpenSearch cluster lifecycle operations and
work-request tracking tools for use by MCP clients.

## Authentication

The server uses standard OCI configuration and signer behavior. Configure OCI credentials
with an OCI config file and profile before starting the server. The active OCI identity's
IAM permissions determine which OpenSearch operations are allowed.

## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-opensearch-mcp-server
```

### Local development from source

From this project directory, use one of these commands:

```sh
uv run oracle.oci-opensearch-mcp-server
```

```sh
uvx --from . oracle.oci-opensearch-mcp-server
```

## Tools

| Tool Name | Description |
|---|---|
| `list_opensearch_clusters` | List OpenSearch clusters in a compartment |
| `get_opensearch_cluster` | Get a cluster by OCID |
| `list_opensearch_cluster_shapes` | List available OpenSearch cluster node shapes |
| `create_opensearch_cluster` | Create a cluster |
| `update_opensearch_cluster` | Update a cluster |
| `delete_opensearch_cluster` | Delete a cluster |
| `resize_opensearch_cluster_vertical` | Resize a cluster vertically |
| `resize_opensearch_cluster_horizontal` | Resize a cluster horizontally |
| `backup_opensearch_cluster` | Trigger a cluster backup |
| `list_work_requests` | List work requests; returns `items` and `count` |
| `get_work_request` | Get work request status |

## Resources

| Resource | Description |
|---|---|
| `resource://oci-opensearch-api-guide` | MVP guidance for async OpenSearch cluster workflows |
| `resource://oci-opensearch-work-request-guide` | Guidance for work-request status tracking and failure triage |
| `resource://oci-opensearch-tool-surface-summary` | Summary of implemented MVP tools and deferred families |

## Request body guidance

Mutation tools use OCI Python SDK-style request bodies with **snake_case** field names.
For detailed payload conventions and examples, read the bundled
`resource://oci-opensearch-api-guide` resource from your MCP client.

`update_opensearch_cluster` accepts a non-empty partial `update_details` body.
`display_name` is optional and only needed when renaming a cluster.

To discover existing clusters, use `list_opensearch_clusters` rather than `create_opensearch_cluster`.

Most mutating operations are asynchronous and return an `opc_work_request_id`. Use
`get_work_request` and `list_work_requests` to inspect status. MCP agents should not
poll continuously by default: after an async response, they may call `get_work_request`
once for an immediate status snapshot, then ask the user before repeated checks.
For create, resize, and backup operations, MCP sends an `opc_retry_token`; callers may
provide one explicitly, otherwise MCP generates and returns a deterministic token for the
same logical request.
An empty `list_work_requests` match is explicit: `{"items": [], "count": 0}`.

## Notes

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI profile. Use
least-privilege IAM policies, secure credential handling, and safe operational practices.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining
and providing all required licenses and copyright notices for third-party code.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model
selections may yield different results and performance.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
