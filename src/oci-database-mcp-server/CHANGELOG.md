# Changelog

All notable changes to OCI Database MCP Server are documented in this file.

## 1.3.3

### Changed

- Excluded development artifacts, local configuration, and container build files from source-distribution packages.

## 1.3.2

### Changed

- Updated the FastMCP dependency and lockfile to 3.4.5.

## 1.3.1

### Changed

- Updated `oracle-mcp-common` dependency minimum version to >=0.1.2,<0.2.0.

## 1.3.0

### Added

- Added OCI IAM/IDCS-authenticated HTTP transport. Each HTTP request exchanges
  the authenticated caller's access token through `oracle-mcp-common` and uses
  a caller-specific OCI SDK signer.

### Changed

- Updated FastMCP from 3.4.2 to 3.4.4 and the OCI Python SDK from 2.179.0 to
  2.182.1. The MCP SDK is now supplied transitively by FastMCP rather than
  declared as a direct dependency.

## 1.2.0

### Changed

- Moved OCI Database and Virtual Network client credential resolution and
  signer construction to `oracle-mcp-common`, including API-key,
  security-token, identity-domain UPST, principal, delegation, and OKE
  workload-identity authentication modes.
