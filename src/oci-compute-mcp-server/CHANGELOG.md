# Changelog

## Unreleased

### Added

- `launch_instance` can now use an existing boot volume as its source by accepting `boot_volume_id`.

### Fixed

- `launch_instance` rejects empty `boot_volume_id` values instead of launching from the default image.
- Enforce the total result limit across paginated Compute MCP tool responses.

### Security

- Updated `cryptography` to 50.0.1 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247).

## 2.0.2

### Changed

- Excluded development artifacts, local configuration, and container build files from source-distribution packages.

## 2.0.1

### Changed

- Updated dependency locks for FastMCP 3.4.5, OCI SDK 2.182.1, and refreshed authentication-related transitive packages.

## 2.0.0

### Breaking Changes

- HTTP transport now requires OCI IAM/IDCS authentication and no longer uses local OCI CLI profile credentials for request authentication.
- HTTP deployments must set `ORACLE_MCP_BASE_URL`, `OCI_REGION`, `IDCS_DOMAIN`, `IDCS_CLIENT_ID`, `IDCS_CLIENT_SECRET`, and `IDCS_AUDIENCE`, and register `${ORACLE_MCP_BASE_URL}/auth/callback`.
- The default required scopes are `openid profile email oci_mcp.compute.invoke`; set `IDCS_REQUIRED_SCOPES` to override.
