# Changelog

## 3.0.1

### Fixed

- `search_resources_by_type` now validates resource types across all `ListResourceTypes` pages.
- Returned OCI fields are no longer wrapped in untrusted-data sentinel envelopes, restoring the stable response shapes from before 3.0.0.

## 3.0.0

### Breaking Changes

- HTTP transport now requires OCI IAM/IDCS authentication and no longer uses local OCI CLI profile credentials for request authentication.
- HTTP deployments must set `ORACLE_MCP_BASE_URL`, `OCI_REGION`, `IDCS_DOMAIN`, `IDCS_CLIENT_ID`, `IDCS_CLIENT_SECRET`, and `IDCS_AUDIENCE`, and register `${ORACLE_MCP_BASE_URL}/auth/callback`.
- The default required scopes are `openid profile email oci_mcp.resource_search.invoke`; set `IDCS_REQUIRED_SCOPES` to override.
- `list_all_resources`, `search_resources`, and `list_resources_by_type` now validate `compartment_id` (OCID format), reject `'` in `display_name`, and validate `resource_type` against `ListResourceTypes`.

### Changed

- Returned `display_name`, freeform/defined tags, and additional details are wrapped in an `--- BEGIN/END UNTRUSTED OCI DATA ---` envelope.
