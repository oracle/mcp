# Changelog

## Unreleased

### Fixed

- Bound Kubernetes reconciliation listing and propagate standalone reconciler
  shutdown cancellation into list and deletion requests.
- Resume Kubernetes deletion watches from the observed resource version and
  recover expired versions within the original confirmation deadline.
- Require port-forward WebSocket closure before tunnel cleanup succeeds,
  including forwarding handles acquired after shutdown begins.

- Require an observed Running Kubernetes pod before runner startup; respect
  cancellation and execution deadlines during the initial readiness request.
- Select OCI session authentication for named profiles that inherit token
  configuration from DEFAULT, while respecting explicit profile overrides.
- Preserve the final JavaScript expression result when trailing comments are
  present, including expressions containing strings or regular expressions.
- Generate arrays for required array fields in `discover_oci` request examples,
  including arrays of models, while retaining bounded model expansion.
- Preserve OCI status codes, service codes, operation details, and request IDs in
  uncaught `run_javascript` errors so callers can assess failures and retry decisions.

### Security

- Updated @grpc/grpc-js to 1.14.6, proxy-addr to 2.0.8, brace-expansion to 5.0.12, and fast-uri to 3.1.8.

## 0.1.1 - 2026-09-30

### Breaking Changes

- Replace the internal raw-JSON gRPC v1 session with the protobuf-defined v4
  session. Update the host and rebuild its runner image together; older runners
  are not supported. Public MCP tools and response fields are unchanged.

### Added

- Add an opt-in Kubernetes isolation provider with `local-development`,
  `in-cluster`, and `kata-in-cluster` profiles. Podman remains the default;
  provider and profile selection is explicit and fails closed at startup.
- Run each Kubernetes execution in a fresh, credential-free pod with bounded
  deletion and expiry reconciliation. Add versioned standard and Kata deployment
  examples, including separate host, runner, and cleanup identities.
- Add a Kata proof-of-concept profile with an exact RuntimeClass and handler
  check, digest-pinned runner image, admission checks, and a deployment guide.
- Add a Moon `k8s-build` task to build the Kubernetes runner and host Docker images.
- Build-generated TypeScript codecs and gRPC bindings, tested before release and
  included in the npm package and runner image rather than source control. No
  runtime schema loading or generation is required. Wire-format compatibility
  tests preserve the contract; OCI data retains bounded JSON validation.

### Changed

- Update architecture and operator guides for protobuf gRPC v4, current Moon
  commands, installation policy, and cleanup outcomes; ship the README-linked
  architecture document and label historical security-review evidence.
- Make container source filtering explicit and exclude stale generated/local
  artifacts; add opt-in builder-context and host/reconciler/runner smoke checks.
- Harden the in-cluster and Kata profiles with scoped RBAC, fail-closed pod
  admission checks, reviewed resource ranges, and a cleanup-only reconciler.
  Add a helper to sync host OCI credentials into a host-only Kubernetes Secret.
- Clarify local in-cluster image digest lookup, all four manifest replacements,
  and rollout verification, and update setup commands to use the existing tools.
- Migrate the Kubernetes isolation provider from the removed framed pipe to the
  shared protobuf gRPC v4 transport, bootstrapped over `pods/exec` and carried
  through one execution-scoped loopback `pods/portforward` connection with mTLS.
  Trusted host roles now require `create` and `get` on `pods/portforward`;
  runner and cleanup identities receive no added authority.
- Return stdout/stderr with the final result and use native gRPC readiness,
  deadlines, cancellation, and failure status; remove the obsolete custom framing
  layer and duplicate transport timer/timeout field. The overall execution
  watchdog and isolate execution limit remain in place.
- Bootstrap each runner's execution-scoped TLS identity only over stdin; remove
  the unused file-based certificate path.

### Fixed

- Build container native dependencies with the bundled Node headers offline,
  avoiding header-download timeouts; cache npm installation separately from native setup.
- Find the local `ts-proto` plugin when generating bindings in the runner and host image builds.
- Delete Kubernetes execution pods alongside transport teardown under one
  cleanup deadline, so stalled startup or channel closure cannot skip deletion;
  unconfirmed cleanup still fails the execution.
- Observe Kubernetes runner failures throughout startup so readiness and tunnel
  faults return sanitized execution failures without terminating the MCP host;
  stop runner and tunnel handles delivered after cancellation.
- Keep host-only certificate generation out of the runner image so Podman and Kubernetes executions can start.
- Generate protobuf bindings when building the host image so fresh checkouts do not need a prior compile.
- Disable SDK circuit breakers and retries on per-call OCI clients while retaining
  cancellation, so successful responses and service errors are returned promptly
  instead of failing with an OCI cleanup timeout.
- Truncate oversized stdout/stderr at UTF-8 character boundaries so output-limit
  errors remain structured results rather than gRPC protocol failures.
- Preserve the remaining gRPC deadline inside the isolate, including subsecond
  execution budgets.
- Generate bindings and compile through Moon dependencies before tests, type
  checks, and packaging, without relying on npm lifecycle hooks.
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

- Disable automatic dependency lifecycle scripts in controlled repository and
  container installs; validate the pinned `isolated-vm` version and install
  command before explicitly building its native addon. Document manual setup
  for npm package consumers.
- Reject guest request-level `retryConfiguration` so OCI SDK calls retain the
  host-controlled single-attempt policy.
- Suppress OCI session-refresh and Kubernetes Secret/restart subprocess output
  so failed credential synchronization cannot expose private keys or tokens;
  report fixed stage summaries, including restart failures after a Secret update.
- Bound all runner RPC frames, including rejected requests, and attempt Podman
  resource removal even if its run command does not close.
