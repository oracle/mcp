# Changelog

## 2.1.1

### Changed


- `run_oci_command` now honors `OCI_MCP_AUTH_TYPE` when `OCI_CLI_AUTH` is unset, supports direct OCI CLI auth modes, and fails safely for unsupported modes or unclassifiable automatic profile selection.
- Updated runtime dependencies: FastMCP to 3.4.4, OCI CLI to 3.89.3, and `oracle-mcp-common` to require 0.1.1 or later (within the 0.1.x compatibility range). The shared library now requires OCI Python SDK 2.182.1 or later.

### Security

- Prevented command-provided OCI CLI authentication, profile, endpoint, proxy, and configuration overrides from bypassing server-managed settings.
- `run_oci_command` now passes its resolved OCI config file explicitly to the OCI CLI, preventing a conflicting `OCI_CLI_CONFIG_FILE` from selecting different credentials than the server inspected.

## 2.1.0

### Changed

- Updated dependency locks for FastMCP 3.4.2, OCI CLI 3.87.0, and refreshed transitive packages.
- `run_oci_command` now chooses OCI CLI API-key or session-token authentication from the selected profile and defers to `OCI_CLI_AUTH` or the OCI CLI when the profile cannot be classified.

### Fixed

- Restricted `get_oci_command_help` to option-free OCI command paths and applied the destructive-command denylist before invoking the OCI CLI.
- OCI command parsing now preserves quoted arguments when retrieving command help or running OCI CLI commands. ([#100](https://github.com/oracle/mcp/issues/100))

## 2.0.0

### Breaking Changes

- HTTP transport support was removed; this server is now `stdio`-only.
- `stdio` request authentication continues to use the configured OCI CLI profile.

### Fixed

- Destructive-command denylist matching is now prefix-based and recognizes valueless global flags (e.g. `--debug`), closing a normalization bypass.
