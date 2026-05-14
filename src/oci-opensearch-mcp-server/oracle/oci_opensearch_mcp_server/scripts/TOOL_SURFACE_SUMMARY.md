# OCI OpenSearch MCP Tool Surface Summary

### Cluster discovery and inspection

- `list_opensearch_clusters`
- `get_opensearch_cluster`
- `list_opensearch_cluster_shapes`

### Cluster mutations

- `create_opensearch_cluster`
- `update_opensearch_cluster`
- `delete_opensearch_cluster`
- `resize_opensearch_cluster_vertical`
- `resize_opensearch_cluster_horizontal`
- `backup_opensearch_cluster`

### Async tracking

- `list_work_requests`
- `get_work_request`

## Deferred families

- restore operations
- work-request logs and errors
- backup-resource CRUD families
- standalone remote/outbound configuration workflows, upgrade, customer logging, and broader control-plane actions

The public surface is intentionally small and SDK-backed.