# Changelog

## Unreleased

## 0.2.0

### Breaking Changes

- The locked cryptography update removes support for Intel macOS and 32-bit Windows. Use Apple Silicon macOS, 64-bit Windows, or a supported Linux environment.

### Added

- Support `resource_principal_v212` authentication through the shared Common library.

### Fixed

- Use the local Common workspace package during development so shared changes trigger validation; update the OCI SDK to 2.185.1 to satisfy Common's requirements.

### Security

- Updated locked dependencies: AnyIO 4.15.1, cryptography 50.0.0, joserfc 1.7.5, MCP Python SDK 1.30.0, pydantic-settings 2.15.0, PyJWT 2.15.1, and urllib3 2.8.0.

### Changed

- Require `oracle-mcp-common>=0.2.0,<0.3.0` for the coordinated Common authentication release.

## 0.1.0 - 2026-08-05

- Initial release of the read-only Oracle Database Observability MCP server,
  covering OCI Database Management, Operations Insights, Monitoring, and
  limited Identity region metadata with 229 catalog tools. Compartment
  discovery is provided by the separate `oci-identity-mcp-server`.
