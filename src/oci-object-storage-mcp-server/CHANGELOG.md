# Changelog

## [Unreleased]

### Changed

- Updated Object Storage response models and tests to use Pydantic v2 serialization and configuration APIs, removing deprecation warnings during unit tests. ([#304](https://github.com/oracle/mcp/issues/304))

## 2.0.0

### Breaking Changes

- HTTP transport now requires OCI IAM/IDCS authentication and no longer uses local OCI CLI profile credentials for request authentication.
- HTTP deployments must set `ORACLE_MCP_BASE_URL`, `OCI_REGION`, `IDCS_DOMAIN`, `IDCS_CLIENT_ID`, `IDCS_CLIENT_SECRET`, and `IDCS_AUDIENCE`, and register `${ORACLE_MCP_BASE_URL}/auth/callback`.
- The default required scopes are `openid profile email oci_mcp.object_storage.invoke`; set `IDCS_REQUIRED_SCOPES` to override.
- `upload_object` now restricts `file_path` to a configured upload root. Set `OCI_MCP_UPLOAD_ROOT` to choose the directory (default: `<tmpdir>/oci-mcp-uploads`). Paths outside this root, and paths under `~/.oci`, `~/.ssh`, `/etc`, `/run/secrets`, or `/var/run/secrets`, are rejected.
