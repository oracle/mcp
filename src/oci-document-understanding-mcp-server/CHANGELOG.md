# Changelog

## [Unreleased]

### Breaking Changes

- The locked cryptography security update removes upstream support for Intel macOS and 32-bit Windows.

### Changed

- Require FastMCP 3.4.5 or later and OCI Python SDK 2.185.0 so the server resolves alongside `oracle-mcp-common`.

### Security

- Update locked PyJWT to 2.15.1, urllib3 to 2.8.0, cryptography to 50.0.2, and PyOpenSSL to 26.4.0 to address dependency security advisories.

## 0.1.0

### Added

- Added public Oracle MCP package layout under `oracle/oci_document_understanding_mcp_server`.
- Added the FastMCP-based `oracle.oci-document-understanding-mcp-server` stdio entry point.
- Added OCI SDK additional user-agent telemetry for Document Understanding clients.
- Removed the custom stdio JSON-RPC transport and prototype shell helper scripts from the public package layout.

### Changed

- Use `oracle-mcp-common` for OCI SDK authentication and standard region resolution.

### Fixed

- Honor `include_confidence=false` by omitting confidence values from extraction results.
- Serialize and map OCI SDK response models into extraction and classification results.
- Apply `confidence_threshold` to classification results.
