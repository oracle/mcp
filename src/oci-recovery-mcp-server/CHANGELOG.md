# Changelog

## 2.1.0

### Added

- Added `list_restore` for retrieving database restore work requests, with filters, paging, and optional child-compartment aggregation.
- Added `check_recovery_service_limits` to report available protected-database backup storage and protected-database-count limits.
- Added `fetch_regions_subscribed` to list the tenancy's subscribed regions and their statuses.

### Changed

- Updated dependency locks for FastMCP 3.4.2, OCI SDK 2.179.0, and refreshed authentication-related transitive packages.
- Added optional child-compartment aggregation to existing compartment-scoped list and summary tools.
- Improved response models with explicit optional-field defaults and descriptions, including the new `WorkRequest` restore-job model.

## 2.0.0

### Breaking Changes

- HTTP transport now requires OCI IAM/IDCS authentication and no longer uses local OCI CLI profile credentials for request authentication.
- HTTP deployments must set `ORACLE_MCP_BASE_URL`, `OCI_REGION`, `IDCS_DOMAIN`, `IDCS_CLIENT_ID`, `IDCS_CLIENT_SECRET`, and `IDCS_AUDIENCE`, and register `${ORACLE_MCP_BASE_URL}/auth/callback`.
- The default required scopes are `openid profile email oci_mcp.recovery.invoke`; set `IDCS_REQUIRED_SCOPES` to override.
