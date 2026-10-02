## 1. Trusted lifecycle coordinator

- [x] 1.1 Refactor `src/sandbox.ts` finalization so it freezes bridge acceptance and aborts the run before starting provider termination and pending-RPC draining concurrently; verify a unit test proves they share one cleanup-tail deadline rather than run serially.
- [x] 1.2 Add a bounded, rejection-observing pending-RPC drain that cannot delay result delivery past the execution deadline plus the provider termination allowance; verify a fake RPC that never settles returns the structured timeout result inside the bound.
- [x] 1.3 Preserve cleanup-failure precedence and the unawaited-OCI-call failure within the new bounded finalization path; verify focused tests cover successful completion with abandoned work, timeout with abandoned work, and failed provider cleanup.

## 2. Trusted OCI broker cancellation policy

- [x] 2.1 Configure OCI SDK clients created by `src/oci-host.ts` with the trusted no-retry policy, an explicitly disabled client circuit breaker, and the existing abort-aware HTTP options; verify client-construction tests assert all three configurations and guest-provided retry or circuit-breaker options remain rejected.
- [x] 2.2 Add broker tests proving an aborted OCI operation neither retries nor uses the default circuit breaker, and cannot publish late data after the tool result is final; verify public errors remain sanitized and client close behavior is retained.

## 3. Provider and protocol lifecycle coverage

- [x] 3.1 Exercise Podman and Kubernetes-compatible fake providers through the shared coordinator to verify cancellation, idempotent termination, channel close, and confirmed resource cleanup remain authoritative under a permanently pending RPC.
- [x] 3.2 Add adversarial framed-channel tests for malformed, unknown-version, unknown-field, oversized, invalid-UTF-8, dangerous-key, and truncated messages during cancellation; verify no malformed frame reaches the OCI broker and the public failure remains sanitized.
- [x] 3.3 Add MCP stdio integration coverage for a timed-out `run_javascript` request with unresolved host OCI work; verify the response fields remain compatible and elapsed time is bounded by execution deadline plus one cleanup tail.

## 4. Documentation and release readiness

- [x] 4.1 Update `README.md` and `docs/architecture-and-isolation-design.md` to describe the execution-deadline-plus-one-tail lifecycle contract, cancellation behavior, and no-retry policy; verify documentation preserves Podman/Kubernetes isolation and no-fallback statements.
- [x] 4.2 Review deployment implications and rollback in the change artifacts: no provider, credential, manifest, or VM-isolation migration is required; verify the documented rollback is a code rollback and real-provider evidence remains unchanged.
- [x] 4.3 Run `npm test`, `npm run coverage`, `npm run check`, `npm run packcheck`, and `npm run ci`; verify all pass with c8 coverage at or above the configured 90% line threshold.
