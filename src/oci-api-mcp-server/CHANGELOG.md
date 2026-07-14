# Changelog

## [Unreleased]

### Changed

- Updated dependency locks for FastMCP 3.4.2, OCI CLI 3.87.0, and refreshed transitive packages.

### Fixed

- Restricted `get_oci_command_help` to option-free OCI command paths and applied the destructive-command denylist before invoking the OCI CLI.
- OCI command parsing now preserves quoted arguments when retrieving command help or running OCI CLI commands. ([#100](https://github.com/oracle/mcp/issues/100))

## 2.0.0

### Breaking Changes

- HTTP transport support was removed; this server is now `stdio`-only.
- `stdio` request authentication continues to use the configured OCI CLI profile.

### Fixed

- Destructive-command denylist matching is now prefix-based and recognizes valueless global flags (e.g. `--debug`), closing a normalization bypass.
