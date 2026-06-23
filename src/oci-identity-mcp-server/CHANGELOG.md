# Changelog

## [Unreleased]

### Changed

- Updated dependency locks for FastMCP 3.4.2, OCI SDK 2.179.0, and refreshed authentication-related transitive packages.

## 3.0.1

### Removed

- `create_auth_token` tool. OCI returns the auth-token secret only in the create response, and an MCP tool result passes through the LLM context, so there is no safe way for this server to deliver the secret. Create auth tokens via the OCI Console or `oci iam auth-token create` instead. (3.0.0 had redacted the secret, which left an unusable token; this removes the tool to make the limitation explicit.)

## 3.0.0

### Breaking Changes

- HTTP transport now requires OCI IAM/IDCS authentication and no longer uses local OCI CLI profile credentials for request authentication.
- HTTP deployments must set `ORACLE_MCP_BASE_URL`, `OCI_REGION`, `IDCS_DOMAIN`, `IDCS_CLIENT_ID`, `IDCS_CLIENT_SECRET`, and `IDCS_AUDIENCE`, and register `${ORACLE_MCP_BASE_URL}/auth/callback`.
- The default required scopes are `openid profile email oci_mcp.identity.invoke`; set `IDCS_REQUIRED_SCOPES` to override.
