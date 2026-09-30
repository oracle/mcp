# Changelog

All notable changes to `oracle-mcp-common` are documented in this file.

## 0.1.4

### Added

- `IDCSHttpAuthOptions.enable_cimd` (default `True`). Set it to `False` to turn off
  CIMD client registration on hosts without direct internet egress; clients then
  register with DCR against `/register`, which never leaves the host.

### Fixed

- `build_idcs_http_auth()` now sends resource scopes to IDCS qualified with
  `IDCS_AUDIENCE`, as `/authorize` requires, on the advertised defaults, the
  authorize request, and the refresh request. Before, bare scopes such as
  `oci_mcp.<server>.invoke` were rejected with `invalid_scope` and sign-in could not
  complete. `required_scopes` stays bare, because it is checked against the issued
  token's bare `scope` claim. A scope that already starts with the audience is not
  qualified again, so non-URL primary audiences work too.

## 0.1.3

### Changed

- Excluded development artifacts and local configuration from the shared library’s source distribution.

## 0.1.2

### Fixed

- Session-token authentication now requires only `key_file` and
  `security_token_file`, allowing profiles created by `oci session authenticate`
  to work without API-key-only fields such as `user`, `fingerprint`, or
  `tenancy`. ([#400](https://github.com/oracle/mcp/issues/400))

## 0.1.1

### Added

- Exported authentication type, config file, and profile resolution helpers for
  consumers that need the same credential-selection behavior without
  constructing an OCI SDK signer.

## 0.1.0

### Added

- Introduced shared OCI SDK authentication contexts for API keys, session
  tokens, Identity Domains UPST exchange, instance and resource principals,
  delegation tokens, and OKE workload identity.
- Added HTTP OCI IAM/IDCS provider setup and caller-specific request-token
  exchange for authenticated MCP servers.
- Added inheritance-safe OCI profile classification for session-token
  authentication.
