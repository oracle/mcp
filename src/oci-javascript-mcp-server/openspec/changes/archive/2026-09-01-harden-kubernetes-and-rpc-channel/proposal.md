## Why

The shared worker channel and Kubernetes provider accept hostile-but-valid behavior that can consume trusted-host resources, cross terminal protocol boundaries, or delay pod cleanup. The 2026-08-28 security review also found that reconciliation, admission diagnostics, cluster-scoped authorization checks, and the Kata validation guide overstate or weaken the intended Kubernetes posture.

## What Changes

- Bound hostile worker-channel ingress, message handling, log processing, result payloads, and egress; enforce the configured result limit over the combined encoded terminal `result` and `error` values at trusted-host acceptance, honor stream backpressure within the execution deadline, and preserve the existing host-owned OCI call and concurrency limits.
- Replace repeated partial-frame concatenation with bounded linear-time frame assembly.
- Enforce an ordered `WAIT_HEALTH -> RUNNING -> TERMINAL` trusted-host protocol state machine, safe unique RPC identifiers, and synchronous authority revocation at terminal settlement.
- Pass cancellation and the absolute execution deadline into Kubernetes pod creation and exec establishment, close late channels, bound channel shutdown independently, make zero-grace pod deletion proceed even when creation or channel closure stalls or fails, and repeat bounded deletion after any post-termination creation settlement because a client-side rejection does not prove the API server rejected the pod.
- Isolate reconciliation failures per pod, cancel the underlying Kubernetes API work at each candidate deadline, continue processing the batch, and expose only aggregate sanitized failure evidence.
- Expand admission negative probes to the complete reviewed pod invariant set, make the example policies use supported inclusive CEL `quantity().compareTo()` checks that accept the documented reviewed resource ranges while rejecting unequal or out-of-range resources, and replace the broad `enforced` descriptor claim with the narrower fact that reviewed variants were rejected.
- Scope cluster-level Namespace and Kata RuntimeClass authorization checks and example RBAC to their configured object names where Kubernetes supports `resourceNames`.
- Correct the Kata guide to use the implemented Kubernetes dry-run command and add a documentation-command regression check.
- Make both standard and Kata in-cluster example bundles deploy the complete trusted-host topology: a hardened host Deployment with profile-specific configuration and downward-API identity, a host-only OCI credential mount, and image-digest alignment between the host configuration and runner admission policy.
- Preserve the MCP result contract, SDK-shaped `oci` facade, supported OCI operations and client options, host credential isolation, provider selection, OCI call/concurrency budgets, 2 MiB per-frame limit, and Podman/Kubernetes profile isolation posture. No process fallback or new provider is introduced.

## Capabilities

### New Capabilities

- `hostile-worker-channel`: Defines bounded frame assembly, channel traffic and backpressure behavior, strict protocol phases, RPC identifier handling, and terminal authority revocation for every isolation provider.

### Modified Capabilities

- `bounded-execution-lifecycle`: Makes Kubernetes pod creation, exec setup, and channel shutdown deadline-aware and requires deletion to remain independent and authoritative during teardown, including after an ambiguous late creation outcome.
- `kata-kubernetes-isolation`: Requires per-pod reconciliation isolation, complete reviewed admission variants with precise assurance reporting, and exact-object cluster authorization checks.
- `isolation-provider-selection`: Narrows the Kubernetes admission descriptor claim while preserving explicit profile selection and unchanged guest authority.

## Impact

- Trusted host and protocol: `src/protocol.ts`, `src/isolation/pipe-execution.ts`, `src/isolation/worker-channel.ts`, and capped log handling in `src/sandbox-common.ts`.
- Kubernetes provider: API/exec adapter, lifecycle cleanup, reconciliation, pod admission variants, diagnostics, and provider preflight under `src/isolation/`, plus the cleanup-only reconciler entry point.
- Deployment and operations: complete standard and Kata trusted-host, cleanup-reconciler, RBAC, admission, and host-only credential-mount assets; Kubernetes/Kata documentation; and package script documentation checks.
- Validation: focused protocol/channel adversarial tests including simultaneously populated `result` and `error` values whose combined encoding exceeds a deliberately small host limit; Kubernetes API/lifecycle/reconciler/profile tests including never-settling, late-success, and server-created/client-rejected creation outcomes plus cancellation of never-settling candidate requests; manifest and admission tests covering supported `compareTo()` expressions and non-default, boundary, unequal, and out-of-range resource settings; MCP stdio compatibility tests; and the opt-in real local-cluster lifecycle and admission harnesses.
- Dependencies and public API: no new runtime dependency, no change to MCP tool schemas or successful result fields, and no expansion of OCI SDK operation exposure or credential authority.
