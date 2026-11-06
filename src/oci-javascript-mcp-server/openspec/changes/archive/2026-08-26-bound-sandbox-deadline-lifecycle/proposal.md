## Why

`run_javascript` enforces its execution deadline but can still delay its MCP response indefinitely while waiting for aborted host OCI RPC promises to settle. An expired OCI session exposed the gap: a 30-second execution timeout produced a response near 90 seconds later because provider cleanup and SDK retry/drain work continued serially after the deadline.

The trusted host must retain deterministic provider cleanup while giving callers a predictable, bounded response time and preventing cancelled OCI work from extending the lifecycle through retry backoff.

## What Changes

- Bound post-deadline host-OCI-RPC draining to the same host-clamped cleanup tail used for provider termination, instead of waiting without a deadline.
- Start provider termination and host RPC draining concurrently after cancellation so their independent tails do not accumulate serially.
- Configure trusted-host OCI SDK clients to avoid retries and disable the SDK's default circuit breaker when the server supplies cancellation; this does not expose retry or circuit-breaker configuration to guest code.
- Preserve structured timeout and cleanup-failure results, including the existing failure for a successful script that leaves OCI calls unawaited.
- Document the end-to-end lifecycle bound as the execution deadline followed by one separately bounded cleanup tail.

## Capabilities

### New Capabilities

- `bounded-execution-lifecycle`: Bounded cancellation, cleanup, and MCP-result delivery for sandbox executions and host OCI RPCs.

### Modified Capabilities

- None.

## Impact

- Trusted host lifecycle and OCI client construction in `src/sandbox.ts` and `src/oci-host.ts`.
- Existing Podman and Kubernetes provider executions use the same provider-neutral termination contract; no provider fallback, guest authority, protocol format, or runner isolation posture changes.
- Focused sandbox, OCI-host, and MCP stdio lifecycle tests, plus lifecycle documentation in `README.md` and the architecture design.
