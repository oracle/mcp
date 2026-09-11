# Changelog

All notable changes to OCI Database MCP Server are documented in this file.

## Unreleased

### Security

- Updated `cryptography` to 50.0.1 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247).

## 1.3.4

### Changed

- Published a new release carrying the `oracle-mcp-common` 0.2 compatibility requirement.

## 1.3.3

### Changed

- Excluded development artifacts, local configuration, and container build files from source-distribution packages.
- Updated the `oracle-mcp-common` compatibility requirement to 0.2 and synchronized package metadata.

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
