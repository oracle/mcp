# Changelog

## 2.2.0

### Changed

- Updated dependency locks for FastMCP 3.4.2, OCI SDK 2.179.0, and refreshed authentication-related transitive packages.
- Moved stdio OCI SDK credential and signer resolution, plus HTTP OCI IAM/IDCS provider and request-token exchange setup, to `oracle-mcp-common`. Stdio supports explicit API-key, security-token, Identity Domains UPST, instance/resource principal, delegation, and OKE workload-identity modes.

### Fixed

- Prevented a named API-key profile from inheriting `security_token_file` from `[DEFAULT]` and signing as a different principal.
- Failed safely when a directly selected session token is unreadable or invalid instead of silently falling back to API-key authentication.

## 2.1.0

### Security

- Restricted `invoke_oci_api` and `describe_oci_operation` to public OCI SDK client methods, preventing private and dunder method invocation.
- Restricted `__model_fqn` and `__class_fqn` request-model hints to OCI SDK model classes under `oci.*.models` with OCI model schema metadata.

### Fixes

- Fixed field projection for empty list responses so successful empty OCI list calls return `[]` instead of an error.
- Added `available_fields` metadata for unmatched field projections to make field-selection errors easier to repair.

### Documentation

- Updated invocation guidance to describe the current parameter repair hints and field-projection metadata.

## 2.0.0

### Breaking Changes

- HTTP transport now requires OCI IAM/IDCS authentication and no longer uses local OCI CLI profile credentials for request authentication.
- HTTP deployments must set `ORACLE_MCP_BASE_URL`, `OCI_REGION`, `IDCS_DOMAIN`, `IDCS_CLIENT_ID`, `IDCS_CLIENT_SECRET`, and `IDCS_AUDIENCE`, and register `${ORACLE_MCP_BASE_URL}/auth/callback`.
- The default required scopes are `openid profile email oci_mcp.cloud.invoke`; set `IDCS_REQUIRED_SCOPES` to override.
