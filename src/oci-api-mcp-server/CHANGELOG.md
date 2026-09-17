# Changelog

## 2.1.5

### Security

- Updated the denylist to match OCI CLI 3.89.3's complete canonical command tree,
  supporting compound actions like `bulk-delete`.
- Prevented the denylist generator from following destination symlinks when writing files.
- Restricted execution to OCI CLI 3.89.3 installed in the MCP server environment.
- Excluded development artifacts, local configuration, and container build files from source-distribution packages.

## 2.1.4

### Changed

- Updated the FastMCP dependency and lockfile to 3.4.5.

## 2.1.3 - 2026-07-30

### Security

- Denied arbitrary `raw-request` execution, including when OCI global options precede
  the command path.
- Disabled OCI CLI command aliases so configured aliases cannot bypass destructive-command
  or `raw-request` denylist entries.
- Recognized clustered short global flags when normalizing command paths, preventing
  interspersed flag clusters from truncating denylist checks.
- Failed server startup when the denylist file is missing instead of starting without
  command restrictions.
- Detached OCI subprocesses from MCP protocol input so CLI prompts and interactive
  modes cannot consume the server's standard input.

### Fixed

- Denylist checks now match only normalized OCI command paths, recognize global
  options wherever the CLI accepts them, and fail closed on ambiguous leading options.

## 2.1.2

### Changed

- `run_oci_command` now honors `OCI_MCP_AUTH_TYPE` when `OCI_CLI_AUTH` is unset, supports direct OCI CLI auth modes, and fails safely for unsupported modes or unclassifiable automatic profile selection.
- Updated runtime dependencies: FastMCP to 3.4.4, OCI CLI to 3.89.3, and `oracle-mcp-common` to require 0.1.2 or later (within the 0.1.x compatibility range). The shared library now requires OCI Python SDK 2.182.1 or later.

### Security

- Prevented command-provided OCI CLI authentication, profile, endpoint, proxy, and configuration overrides from bypassing server-managed settings.
- `run_oci_command` now passes its resolved OCI config file explicitly to the OCI CLI, preventing a conflicting `OCI_CLI_CONFIG_FILE` from selecting different credentials than the server inspected.

## 2.1.1 - 2026-07-22

### Security

- Blocked caller overrides of the OCI CLI endpoint, authentication mode, profile,
  configuration file, and defaults file; denied arbitrary `raw-request` execution even
  when global options precede the command.

### Fixed

- Aligned the OCI CLI telemetry version with the package version.

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
