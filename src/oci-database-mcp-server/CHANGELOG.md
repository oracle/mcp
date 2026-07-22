# Changelog

All notable changes to OCI Database MCP Server are documented in this file.

## 1.2.0

### Changed

- Moved OCI Database and Virtual Network client credential resolution and
  signer construction to `oracle-mcp-common`, including API-key,
  security-token, identity-domain UPST, principal, delegation, and OKE
  workload-identity authentication modes.
