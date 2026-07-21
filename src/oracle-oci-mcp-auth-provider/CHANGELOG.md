# Changelog

All notable changes to Oracle OCI MCP Auth Provider are documented in this file.

## Unreleased

### Added

- Added reusable security-token profile, instance-principal, resource-principal
  session-token, and user-principal session-token authentication providers.
- Added a Database-compatible RPST environment constructor that preserves IMDS
  endpoint resolution, signed token bootstrap, query-string retry, and timeout behavior.
