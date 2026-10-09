## Context

See `proposal.md` for motivation and `specs/bounded-execution-lifecycle/spec.md` for the behavioral contract. The trusted host owns a run-wide `AbortController`, starts one provider execution, and wraps its result in the absolute user-selected deadline. In the finalizer it aborts the run, terminates the provider inside that provider's host-clamped allowance, then awaits every pending OCI RPC without a deadline. This makes result delivery unbounded even though execution and provider cleanup are bounded.

The flow remains:

```text
MCP stdio tool
  -> trusted sandbox lifecycle coordinator
       -> selected provider -> credential-free runner -> framed worker -> isolated-vm guest
       -> trusted OCI broker -> OCI SDK client with host credentials -> OCI API
```

The change is entirely in the trusted host. It does not alter the worker protocol, guest `oci` facade, Podman hardening, Kubernetes pod shape, guest credentials, mounts, network posture, resource limits, or deployment-provided VM-grade isolation.

## Goals / Non-Goals

**Goals:**

- Return a timeout result after the execution deadline plus at most one bounded cleanup tail.
- Preserve deterministic, idempotent provider termination and make cleanup failure authoritative.
- Ensure cancelled OCI requests do not use SDK retry/backoff to extend the lifecycle.
- Retain per-run call and concurrency limits, hostile-input validation, and sanitized public failures.

**Non-Goals:**

- Guarantee that a third-party OCI SDK or underlying network stack immediately releases every resource after an abort.
- Change guest-visible OCI operation, pagination, client-option, retry-configuration, or authentication capabilities.
- Add a provider, process fallback, global request queue, or a network-facing MCP transport.

## Decisions

### 1. Treat the cleanup tail as one shared post-deadline budget

On finalization, the coordinator marks the run non-accepting and aborts its signal. It starts provider termination and a snapshot drain of outstanding host RPC promises concurrently. Both operations share the provider's already host-clamped termination allowance. The coordinator returns after both settle or the shared tail expires; it never begins a new drain timer after awaiting termination.

The timeout result remains the outcome when cleanup succeeds but a cancelled RPC has not settled. A late promise remains observed internally so it cannot become an unhandled rejection, but it cannot affect the completed tool result.

**Alternatives considered:** Waiting for every RPC preserves maximal local tidiness but violates the caller-facing deadline. Returning immediately at the execution deadline would make provider destruction asynchronous and weaken the existing cleanup-confirmation guarantee. Serial termination then drain is the current bug.

### 2. Preserve cleanup failure precedence

Provider termination still closes the execution channel and confirms resource destruction. If it fails or exceeds the shared tail, the result becomes the existing sanitized `isolation provider cleanup failed` non-timeout result, even if the initial outcome was timeout. A drain timeout alone does not replace a timeout result because cancellation has already withdrawn the execution's authority.

**Alternatives considered:** Reporting timeout regardless of unconfirmed cleanup hides a security-relevant resource-lifecycle failure. Treating a late RPC as a cleanup failure would conflate external SDK liveness with provider resource ownership.

### 3. Make trusted OCI clients non-retrying and circuit-breaker-free for an execution

The host will construct OCI SDK clients with the SDK's no-retry configuration, an explicit disabled client circuit breaker, and the existing abort-aware HTTP options. The SDK creates its default `opossum` circuit breaker unless client configuration carries a disabled breaker; the environment variable is an operational workaround, but explicit configuration makes the behavior independent of the launcher and Inspector environment. The SDK propagates `httpOptions` to `fetch`, but its normal retry path treats client-side errors as retryable and uses non-abortable backoff; no-retry prevents an abort from becoming several post-deadline attempts. The host continues to own retry and circuit-breaker policy; guest code still cannot provide either.

**Alternatives considered:** Setting `OCI_SDK_DEFAULT_CIRCUITBREAKER_ENABLED=false` in every launcher works as an immediate mitigation, but is environment-dependent and can be omitted by a client such as MCP Inspector. An abort-aware retry predicate cannot interrupt a retry delay that began before abort. A custom SDK transport is a larger security-sensitive integration with no demonstrated need. Keeping the default circuit breaker or retries fails the bounded-lifecycle goal.

### 4. Keep pending-call accounting and protocol defenses unchanged in authority

The coordinator retains the pending-promise set until each promise settles, attaches handlers before returning, and stops accepting bridge requests before aborting. The existing frame decoder, strict message sequencing, recursive limits, dangerous-key rejection, request validation, response limits, and public error formatter remain the enforcement boundary. Provider cleanup stays provider-neutral: Podman and Kubernetes receive the same abort signal and expose their existing idempotent `terminate()` contract.

**Alternatives considered:** Dropping references without observing rejected promises risks unhandled rejections. Moving OCI lifecycle authority into the runner would expose credentials and bypass trusted request validation.

## Risks / Trade-offs

- **[An OCI operation may remain alive after the response]** → Abort it, disable SDK retries, retain observed settlement handlers, and bound the response independently; no late result can regain guest authority.
- **[A timed-out client may wait through the cleanup tail]** → Document the explicit execution-deadline-plus-one-tail contract; retain the smallest provider tail consistent with confirmed teardown.
- **[No-retry and no-circuit-breaker configuration changes transient-failure behavior]** → Scope it to trusted sandbox OCI invocations, document it, and test that cancellation neither retries nor enters the default breaker; callers can issue a new complete execution when appropriate.
- **[Concurrent finalization can race]** → Keep provider termination idempotent, freeze RPC acceptance before abort, and test completion, timeout, late settlement, and cleanup failure races.

## Migration Plan

1. Add the shared-tail coordinator behavior and no-retry OCI client configuration behind the existing public interfaces.
2. Add deterministic fake-provider and fake-host-RPC tests for permanently pending, aborting, and late-settling requests, plus OCI-client configuration tests.
3. Update lifecycle documentation with the bounded end-to-end contract and retry behavior.
4. Run the focused tests and the required package validation suite before release.

This change requires no data, provider, credential, Kubernetes manifest, or VM-isolation migration. Existing Podman, Kubernetes, Kata, and real-provider evidence remains unchanged because the runner and deployment boundaries do not change. Rollback is a code rollback with no provider fallback or configuration change; reverting restores the prior unbounded-drain behavior and is therefore only appropriate if a compatibility issue requires it.
