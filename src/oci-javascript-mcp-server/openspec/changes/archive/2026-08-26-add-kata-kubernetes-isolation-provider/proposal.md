## Why

The Kata proof of concept already implements a mostly generic Kubernetes pod lifecycle, but tying that lifecycle directly to Kata prevents real local-cluster testing on macOS and duplicates concerns that are not Kata-specific. Split Kubernetes execution from runtime assurance so the same hardened engine can run locally for development, in-cluster with the standard runtime, or in-cluster with an approved Kata RuntimeClass.

## What Changes

- Add explicit, operator-controlled isolation-provider selection with `podman` as the compatibility default and `kubernetes` as the only Kubernetes provider; Kubernetes selection additionally requires one exact profile: `local-development`, `in-cluster`, or `kata-in-cluster`.
- Refactor the Kubernetes implementation into a shared execution engine composed from an explicit connection mode and a monotonic runtime policy that can add constraints but cannot weaken the base pod shape.
- Add a `local-development` profile that runs the trusted MCP host on the developer workstation, connects only through explicitly configured kubeconfig credentials, uses the cluster's standard runtime, and is permanently identified as development-only container isolation.
- Add an `in-cluster` profile that uses only the trusted host service account, runs hardened execution pods with the cluster's standard runtime, requires separate trusted-host and execution namespaces, and reports container-grade rather than VM-grade isolation.
- Retain Kata as the `kata-in-cluster` profile, adding exact RuntimeClass/handler validation and the existing external evidence requirements for the guest kernel, CRI mapping, CNI, PID, overhead, and image provenance.
- Keep provider and profile selection fail closed. Do not auto-detect credentials, discover runtimes, fall back between profiles, or retry guest code through another provider.
- Preserve the provider-neutral framed worker channel, hostile protocol validation, host-owned OCI controls, execution deadline plus one shared cleanup tail, no-retry/circuit-breaker policy, call/concurrency budgets, result shapes, deterministic pod deletion, and reconciliation behavior.
- Require digest-pinned runner images for both in-cluster profiles. Permit a locally loaded tag only in `local-development` with `imagePullPolicy: Never`, an explicit configuration opt-in, and a descriptor that records the relaxed image provenance.
- Add local-cluster lifecycle validation and standard-runtime in-cluster deployment coverage without representing either as Kata or production-equivalent VM evidence.
- Preserve Podman as the unset default and preserve the nested `isolated-vm` boundary in every provider and profile.
- Keep high-concurrency tuning, OKE provisioning, live Kata evidence, production security review, full OCI authorization policy, caller authorization, mutation approval, and scope-policy redesign outside this POC.

## Capabilities

### New Capabilities

- `isolation-provider-selection`: Explicit provider and Kubernetes-profile selection, profile-specific configuration validation, assurance reporting, and fail-closed startup without provider or profile fallback.
- `kata-kubernetes-isolation`: Shared per-execution Kubernetes pod isolation for local-development, standard in-cluster, and Kata in-cluster profiles, including hardened execution, framed communication, lifecycle cleanup, reconciliation, and profile-specific deployment evidence.

### Modified Capabilities

None. This repository has no existing OpenSpec capability specifications for the current provider behavior.

## Impact

- Trusted host: provider/profile parsing, explicit kubeconfig versus in-cluster client construction, startup preflight, lifecycle telemetry, and profile assurance descriptors.
- Isolation layer: extraction of the current Kata-named API, configuration, pod builder, provider, diagnostics, and reconciler into generic Kubernetes components plus standard and Kata runtime policies.
- Untrusted runner: unchanged credential-free runner, `isolated-vm` boundary, OCI facade, and worker protocol.
- Protocol and MCP surface: no schema or result-shape change; the same limits, sequencing, cancellation, hostile-input handling, bounded finalization, unawaited-call failure, and public-error sanitization remain authoritative.
- Dependencies: retain the official Kubernetes JavaScript client and its locked transitive dependencies.
- Operations: developers can validate the real Kubernetes create/watch/exec/delete path from macOS against a local cluster; operators can deploy the same engine in-cluster with either standard container isolation or an approved Kata runtime. Only the Kata profile can pursue VM-grade admission, and it still requires the documented real-cluster evidence and security review.
