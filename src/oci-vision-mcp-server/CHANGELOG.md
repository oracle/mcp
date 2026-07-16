# Changelog

## [Unreleased]

### Added

- Added public Oracle MCP package layout under `oracle/oci_vision_mcp_server`.
- Added the `oracle.oci-vision-mcp-server` stdio entry point.
- Added OCI SDK additional user-agent telemetry for Vision and Object Storage clients.

### Changed

- Updated runtime dependencies to FastMCP 3.4.2, OCI SDK 2.179.0, and Pydantic 2.12.3.
- Disabled browser-based session authentication by default; it remains available by setting `OCI_MCP_AUTO_AUTH=true`.

## 0.1.0

### Added

- Initial OCI Vision MCP server with Vision analysis, Object Storage upload/list, result lookup, and configuration status tools.
