# OCI OpenSearch MCP Runtime Guide

This server exposes a focused, SDK-backed MVP for OCI OpenSearch control-plane workflows.

## Tool families

- cluster discovery: `list_opensearch_clusters`, `get_opensearch_cluster`
- shape discovery: `list_opensearch_cluster_shapes`
- cluster mutations: `create`, `update`, `delete`, `resize`, `backup`
- async tracking: `list_work_requests`, `get_work_request`

## Async behavior

- most mutating actions are **asynchronous**
- capture the returned `opc_work_request_id`
- create, resize, and backup requests send an `opc_retry_token`; if you omit one, MCP generates a deterministic token for the same logical request and returns it in the tool response
- optionally call `get_work_request` once for an immediate status snapshot
- do not poll continuously by default; ask the user before repeated status checks
- use the work-request tools later before assuming the cluster state has converged
- `list_work_requests` returns `items` and `count`; an empty match is returned as `{"items": [], "count": 0}`

## Retry token behavior

For side-effecting async operations that support OCI retry tokens (`create_opensearch_cluster`, both resize tools, and `backup_opensearch_cluster`):

- callers may provide `opc_retry_token` explicitly
- if omitted, MCP generates a deterministic token from the operation and request payload
- successful async responses include `opc_retry_token` and `opc_retry_token_source` (`caller` or `generated`)
- reuse the same `opc_retry_token` when manually retrying the same logical request after an ambiguous timeout
- do not reuse a retry token for a different logical request

## Error behavior

When OCI returns a service error, tools return normalized fields when available:

- `status`
- `code`
- `message`
- `opc_request_id`

## Request body conventions

Mutation tools expect request bodies shaped like OCI Python SDK models and using **snake_case** field names.

Examples:

- `create_opensearch_cluster` → `CreateOpensearchClusterDetails`
- `update_opensearch_cluster` → `UpdateOpensearchClusterDetails`
- `resize_opensearch_cluster_vertical` → `ResizeOpensearchClusterVerticalDetails`
- `resize_opensearch_cluster_horizontal` → `ResizeOpensearchClusterHorizontalDetails`
- `backup_opensearch_cluster` → `BackupOpensearchClusterDetails`

The `update_opensearch_cluster`, `resize_opensearch_cluster_vertical`, `resize_opensearch_cluster_horizontal`, and `backup_opensearch_cluster` tools follow the same request pattern as create:

- MCP-facing request bodies use snake_case fields
- the server validates those bodies with explicit typed schemas
- the server converts them into OCI SDK model objects before calling the client

For `update_opensearch_cluster`, provide `update_details` with at least one field. `display_name` is optional and only needed when renaming a cluster; software-version, tag, backup-policy, maintenance, certificate, load-balancer, and security updates do not require a rename field.

Security updates require `security_mode`. To update the local security master-user password hash, provide all of:

- `security_mode` (usually the current value, for example `ENFORCING`)
- `security_master_user_name` (the current master username from `get_opensearch_cluster`)
- `security_master_user_password_hash`

Do not send `security_master_user_password_hash` by itself; include `security_mode` so OCI treats the request as a security configuration update. OCI does not allow software-version and security-config updates in the same request. For easier rollback and work-request triage, submit one update family per request.

For `resize_opensearch_cluster_vertical` and `resize_opensearch_cluster_horizontal`, provide at least one field inside `resize_details`.

For `backup_opensearch_cluster`, pass `backup_details` with:

- `compartment_id`
- `display_name`

For `create_opensearch_cluster`, pass a JSON object under the top-level key:

- `create_opensearch_cluster_details`

The create tool performs light validation for the required body shape before calling OCI and returns async metadata such as `opc_work_request_id`. When the service returns cluster data, the tool also surfaces `cluster_id` and `lifecycle_state` in the top-level response.

Required create fields are limited to:

- `display_name`
- `software_version`
- `compartment_id`
- `vcn_id`
- `vcn_compartment_id`
- `subnet_id`
- `subnet_compartment_id`
- `security_master_user_name`
- `security_master_user_password_hash`

Other create fields are optional. The tool fills only non-shape node sizing defaults needed by the minimal MCP create flow before calling OCI. If you omit `*_host_shape` fields, MCP does not inject a shape string; OCI service-side validation and selection remain authoritative.

Create requires three explicit compartment values: `compartment_id` for the OpenSearch cluster resource, `vcn_compartment_id` for the VCN, and `subnet_compartment_id` for the subnet. These may differ for cross-compartment networking, but they must belong to the same intended tenancy and region and must match the actual VCN/subnet ownership.

The create and update schemas include the current SDK-backed `load_balancer_config` and `certificate_config` nested objects. Use OCI SDK snake_case keys for those nested objects, such as `load_balancer_service_type`, `cluster_certificate_mode`, and `open_search_api_certificate_id`.

For BYOC certificates stored in OCI Certificates service, set `certificate_config.cluster_certificate_mode` and/or `certificate_config.dashboard_certificate_mode` to `OCI_CERTIFICATES_SERVICE` and provide the matching certificate OCID (`open_search_api_certificate_id` and/or `open_search_dashboard_certificate_id`). Use `OPENSEARCH_SERVICE` for service-managed certificates and omit certificate OCIDs for that mode.

## Shape selection workflow

Use `list_opensearch_cluster_shapes` before setting `*_host_shape` values in `create_opensearch_cluster` or `resize_opensearch_cluster_vertical` payloads.

Recommended shape workflow:

1. Call `list_opensearch_cluster_shapes`.
2. Use one of the returned strings for fields such as:
   - `master_node_host_shape`
   - `data_node_host_shape`
   - `opendashboard_node_host_shape`
   - `search_node_host_shape`
   - `ml_node_host_shape`
3. Use one of the returned shape strings exactly as returned; do not invent, normalize, or hard-code shape values.
4. If multiple shapes are returned, show the returned shape list to the user and ask which shape to use; suggest the first returned shape if the user has no preference.
5. For create, omit shape fields if you want OCI service-side validation and selection to decide the shape.
6. Use `resize_opensearch_cluster_vertical` for shape, OCPU, memory, or storage changes.
7. Use `resize_opensearch_cluster_horizontal` only for node-count changes.
8. Capture the returned `opc_work_request_id`; optionally call `get_work_request` once for a status snapshot, then ask before checking repeatedly.

Shape catalog membership is not a capacity guarantee. OCI still validates the final shape, OCPU, memory, node count, service-limit, and availability-domain capacity during the mutation.

## Optional node families from count 0

Search, ML, and OpenDashboard nodes do not all use the same zero-to-count workflow:

- Search nodes: if current `search_node_count` is 0, use `resize_opensearch_cluster_vertical` first with the full search node host config (`search_node_host_shape`, `search_node_host_ocpu_count`, `search_node_host_memory_gb`, and `search_node_storage_gb`). The service creates 1 search node. After that work request succeeds, use `resize_opensearch_cluster_horizontal` with `search_node_count` to scale to the final count.
- ML nodes: if current `ml_node_count` is 0, use `resize_opensearch_cluster_vertical` first with the full ML node host config (`ml_node_host_shape`, `ml_node_host_ocpu_count`, `ml_node_host_memory_gb`, and `ml_node_storage_gb`). The service creates 1 ML node. After that work request succeeds, use `resize_opensearch_cluster_horizontal` with `ml_node_count` to scale to the final count.
- OpenDashboard nodes: if current `opendashboard_node_count` is 0, use `resize_opensearch_cluster_horizontal` first with `opendashboard_node_count`. The service creates OpenDashboard nodes with defaults. After that work request succeeds, use `resize_opensearch_cluster_vertical` if you need to change OpenDashboard OCPU, memory, or shape.

Do not try to create search or ML nodes from count 0 using horizontal resize; OCI rejects that path and requires vertical resize first.

For security-admin credentials:

- only `security_mode = ENFORCING` is supported for create
- `security_master_user_name` is required
- provide only `security_master_user_password_hash`
- `security_master_user_password_hash` is required
- generate the hash externally using OCI's documented `pbkdf2_stretch_1000` process
- reference: https://docs.oracle.com/en-us/iaas/Content/search-opensearch/Tasks/manageociopensearch.htm#password_hash

The server always sends `security_mode = ENFORCING` for create requests and rejects other security mode values.

Minimal create request:

```json
{
  "create_opensearch_cluster_details": {
    "display_name": "my-opensearch-cluster",
    "compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
    "software_version": "3.2.0",
    "vcn_id": "ocid1.vcn.oc1..exampleuniqueID",
    "vcn_compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
    "subnet_id": "ocid1.subnet.oc1..exampleuniqueID",
    "subnet_compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
    "security_master_user_name": "admin1",
    "security_master_user_password_hash": "pbkdf2_stretch_1000$..."
  }
}
```

## SDK-backed vs fallback boundaries

This server exposes SDK-backed tools only. Raw REST fallback tools are not part of the public surface.

## Recommended workflow

1. Discover clusters with `list_opensearch_clusters`.
2. Inspect a cluster with `get_opensearch_cluster`.
3. Discover available shapes with `list_opensearch_cluster_shapes` before setting shape fields.
4. Submit one mutation at a time (`create_opensearch_cluster` creates resources; it is not a discovery tool).
5. Report the returned work request ID, optionally check it once with `get_work_request`, and ask the user before repeated polling.
