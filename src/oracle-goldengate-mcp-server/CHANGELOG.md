# Changelog

## Unreleased

### Breaking Changes

- Process names now follow the GoldenGate REST naming pattern (one to eight uppercase letters, digits, `_` or `$`, with no leading digit). Two-character trail names accept alphanumeric characters only.
- Generic `start` checks the backend before issuing a command. Replicat starts require a matching local CDC Extract and a complete Extract collection of at most 128 entries. Initial-load, remote-only, and ambiguous sources are refused.
- `start_initial_load_replicat` requires a matching EXTFILE/source path, a stopped Extract with identifiable execution history and a successful exit, and a report identifying that execution. Missing evidence, operator stops, failed runs and restarts during inspection are refused.
- Structured `advanced.reportCount.every` requires a positive `value` and a `unit` of `SECONDS`, `MINUTES` or `HOURS`. String frequency expressions remain supported.
- TRANDATA `prepareCsnMode` is constrained to `nowait`, `wait`, `lock`, or `none`.

### Fixed

- Filter Data Stream overall, network, and table statistics to the requested stream, retaining all matching table rows and returning empty collections when no statistics match.
- Decode environment-file credential quotes once so literal leading and trailing quotes are preserved; process environment credentials retain their existing precedence and quote handling.
- Redact complete quoted and escaped passwords, authorization headers and multiline private keys from reports, tool output and HTTP errors.
- Dispatch blocking tools to worker threads while serializing access to the shared HTTP session and guarded operations. Cancellation does not abandon a running worker or imply rollback.
- Close the HTTP session on server shutdown and remove the obsolete duplicate server-version constant.

### Added

- Explicit read-only, mutation, idempotency and external-system annotations for every tool.
- In-memory MCP regression tests for discovery, validation, serialization, guarded starts and protocol responsiveness during blocked HTTP calls.
