# Changelog

## 3.0.0

### Breaking Changes

- HTTP transport now requires OCI IAM/IDCS authentication and no longer uses local OCI CLI profile credentials for request authentication.
- HTTP deployments must set `ORACLE_MCP_BASE_URL`, `OCI_REGION`, `IDCS_DOMAIN`, `IDCS_CLIENT_ID`, `IDCS_CLIENT_SECRET`, and `IDCS_AUDIENCE`, and register `${ORACLE_MCP_BASE_URL}/auth/callback`.
- The default required scopes are `openid profile email oci_mcp.identity.invoke`; set `IDCS_REQUIRED_SCOPES` to override.
- `create_auth_token`: the returned model **no longer includes the token secret value**; retrieve it from the OCI Console.
