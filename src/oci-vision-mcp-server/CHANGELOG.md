# Changelog

## 0.1.0

### Added

- Added public Oracle MCP package layout under `oracle/oci_vision_mcp_server`.
- Added the `oracle.oci-vision-mcp-server` stdio entry point.
- Added OCI SDK additional user-agent telemetry for Vision and Object Storage clients.

### Changed

- Updated runtime dependencies to FastMCP 3.4.5, MCP 1.29+, OCI SDK 2.182.1, and Pydantic 2.13.4+.
- Use the shared `oracle-mcp-common` authentication context for OCI Vision and Object Storage clients.
- Default the OCI profile to `DEFAULT` and defer Vision compartment validation until a Vision operation requires it.
- Restrict Vision image inputs to OCI-supported JPEG/PNG images no larger than 5 MiB.
- Limit Object Storage uploads to local `file_path` image inputs, matching the supported upload implementation.

### Fixed

- Corrected the configuration-status environment-variable catalog.
- Removed the unused stderr-log configuration and implementation.
- Include image-validation and Object Storage download code in the coverage gate.
- Preserve the selected profile's configured region when handling an OCI session-authentication failure.
- Keep OCI session authentication outside the server process; the server no longer invokes the OCI CLI or starts browser-based authentication.
- Include the configured OCI config-file path in the manual session-authentication recovery guidance.
