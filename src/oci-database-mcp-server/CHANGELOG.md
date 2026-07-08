# Changelog

All notable changes to OCI Database MCP Server are documented in this file.

## [Unreleased]

### Added

- Resource principal and instance principal authentication options for OCI Database service requests.

### Changed

- Added `cryptography` for RPST request signing and `requests` for RPST token exchange.

### Fixed

- Bound resource-principal token and session-token HTTP calls with explicit connect and read timeouts.
