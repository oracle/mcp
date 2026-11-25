# Changelog

All notable changes to OCI Database MCP Server are documented in this file.

## Unreleased

### Breaking Changes

- Require FastMCP 4.2.2 and `oracle-mcp-common>=0.3.0,<0.4.0`; FastMCP 3 and Common 0.2.x are no longer supported.

### Changed

- Update locked dnspython to 2.9.2.

- Resolve Common from published packages by default in development and CI; local Common integration now requires an explicit override.

## 1.4.0

### Added

- Support `resource_principal_v212` authentication through the shared Common library.

### Fixed

- Allow explicit null for optional region arguments so calls use the configured default region, matching omission.

### Security

- Updated locked AnyIO to 4.15.1; updated locked multidict to 6.9.1; updated PyJWT to 2.15.1 and urllib3 to 2.8.0; updated `cryptography` to 50.0.2 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247).

### Changed

- Require `oracle-mcp-common>=0.2.0,<0.3.0` for the coordinated Common authentication release.

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
