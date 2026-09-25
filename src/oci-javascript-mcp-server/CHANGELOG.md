# Changelog

## Unreleased

### Breaking Changes

- Replace the internal raw-JSON gRPC v1 session with the protobuf-defined v4
  session. Update the host and rebuild its runner image together; older runners
  are not supported. Public MCP tools and response fields are unchanged.

### Added

- Build-generated TypeScript codecs and gRPC bindings, tested before release and
  included in the npm package and runner image rather than source control. No
  runtime schema loading or generation is required. Wire-format compatibility
  tests preserve the contract; OCI data retains bounded JSON validation.

### Changed

- Return stdout/stderr with the final result and use native gRPC readiness,
  deadlines, cancellation, and failure status; remove the obsolete custom framing
  layer and duplicate transport timer/timeout field. The overall execution
  watchdog and isolate execution limit remain in place.
- Bootstrap each runner's execution-scoped TLS identity only over stdin; remove
  the unused file-based certificate path.

### Fixed

- Require a final successful gRPC status before accepting runner results, propagate
  MCP request cancellation to execution and OCI work, and consistently enforce
  the configured result-size limit across the host and runner.
- Ship a compiled JavaScript npm entry point and bindings so installed packages
  run without Node's unsupported TypeScript stripping under `node_modules`.
- Preserve JavaScript source and log strings across gRPC, including unpaired
  UTF-16 surrogates, using bounded UTF-16LE payloads.
- Start execution after gRPC readiness, ignore messages after completion,
  and terminate executions when runner replies encounter backpressure.
- Bound cleanup when an OCI call ignores cancellation, and return a structured
  output-limit error when a script catches the console exception.
- Let final gRPC status determine the outcome once the runner responds, even if
  the Podman CLI exits first.

### Security

- Bound all runner RPC frames, including rejected requests, and attempt Podman
  resource removal even if its run command does not close.
