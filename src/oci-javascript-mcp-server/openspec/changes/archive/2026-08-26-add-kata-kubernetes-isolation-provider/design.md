## Context

See `proposal.md` for motivation. The current change already introduced a provider-neutral worker channel and a complete Kubernetes pod lifecycle, but its API, configuration, diagnostics, pod builder, reconciliation, and provider class are all named and configured as Kata-specific. Most of that behavior is independent of the selected container runtime.

The runner image and framed worker protocol remain credential-free and hostile by design. The trusted host owns Kubernetes credentials, OCI credentials, deadlines, RPC budgets, SDK request validation, public-error sanitization, and deterministic cleanup. A Kubernetes profile changes how the trusted host reaches the Kubernetes API and which runtime constraints are added to the pod; it does not change guest authority or the MCP result contract.

The subsequent `bound-sandbox-deadline-lifecycle` change refines the shared host contract without changing the provider or profile architecture: provider termination and pending OCI RPC draining share one bounded post-execution tail, and trusted OCI clients use no retries, no client circuit breaker, and the run abort signal. This design treats that lifecycle contract as authoritative for every provider and profile.

## Goals / Non-Goals

**Goals:**

- Extract one Kubernetes execution engine shared by workstation-local, standard in-cluster, and Kata in-cluster profiles.
- Make credential source, deployment topology, runtime policy, image policy, and assurance posture explicit and fail closed.
- Enable a macOS-hosted MCP server to exercise the real create/watch/exec/delete path against a local Kubernetes cluster without Kata.
- Support an in-cluster standard-runtime deployment that validates production-like RBAC, namespace, admission, reconciliation, network, and lifecycle behavior without claiming a VM boundary.
- Retain all existing Kata-specific RuntimeClass, deployment-evidence, and cleanup requirements as an additive runtime policy.
- Preserve Podman behavior, the `isolated-vm` boundary, wire protocol, OCI facade, result contract, limits, and no-fallback posture.
- Preserve the bounded execution-deadline-plus-one-cleanup-tail contract and host-owned no-retry/circuit-breaker policy across every profile.

**Non-Goals:**

- Running Kata inside a macOS local Kubernetes VM or claiming that a shared local-cluster VM is a per-execution Kata boundary.
- Automatically selecting kubeconfig versus service-account credentials, probing available runtimes to choose a profile, or falling back between profiles.
- Treating the standard runtime profile as production-equivalent isolation for hostile multi-tenant code.
- Allowing arbitrary pod fragments, commands, environments, volumes, security contexts, runtime classes, credentials, or image-pull behavior.
- Supporting a workstation-hosted Kata production topology in this change; a remote Kata integration profile can be considered separately.
- Changing the protocol, guest OCI surface, authorization model, or concurrency/load goals.

## Decisions

### 1. Select one provider and one exact Kubernetes profile

`OCI_JAVASCRIPT_ISOLATION_PROVIDER` accepts `podman` or `kubernetes`; omission preserves Podman. Kubernetes additionally requires `OCI_JAVASCRIPT_KUBERNETES_PROFILE` with exactly `local-development`, `in-cluster`, or `kata-in-cluster`.

Named profiles are parsed as closed configuration bundles rather than freely combinable flags:

| Profile | Trusted host | Kubernetes credentials | Runtime | Assurance |
| --- | --- | --- | --- | --- |
| `local-development` | workstation | explicit kubeconfig path and context | cluster default | development-only container isolation |
| `in-cluster` | Kubernetes pod | service account only | cluster default | in-cluster container isolation |
| `kata-in-cluster` | Kubernetes pod | service account only | exact RuntimeClass/handler | Kata POC pending real evidence |

This prevents invalid combinations such as an in-cluster profile silently loading a user kubeconfig or a local profile claiming the in-cluster service-account topology. Provider or profile failure is authoritative; there is no fallback.

**Alternatives considered:** Keeping `kata-kubernetes` as a separate provider would continue duplicating generic Kubernetes behavior. Independent connection/runtime flags would create a larger invalid configuration matrix. Automatic discovery would let environment availability choose security posture.

### 2. Compose the Kubernetes engine from constrained connection and runtime policies

The implementation separates:

- a Kubernetes API adapter and connection factory;
- shared configuration for namespace, image, resources, deadline, cleanup, and reconciliation;
- the hardened base pod builder;
- the shared execution provider and lifecycle state machine;
- shared host and independent reconciliation;
- runtime policies for standard and Kata execution;
- profile-aware diagnostics and assurance descriptors.

The runtime-policy contract is monotonic. It can supply an optional reviewed RuntimeClass constraint, additional preflight requirements, additional unsafe admission variants, and additional descriptor evidence. It cannot mutate or remove base security controls, supply arbitrary pod fragments, change the worker command, inject environment, add volumes, or select credentials. The base builder constructs the complete pod and applies only typed additive runtime fields.

**Alternatives considered:** Class inheritance between standard and Kata providers would couple lifecycle overrides to security policy and make it easier for a subclass to bypass cleanup. An arbitrary `mutatePod` hook would reintroduce unsafe operator-controlled pod shape.

### 3. Keep credential loading explicit and profile-bound

The local connection uses a required kubeconfig path and required context supplied by trusted configuration. It does not call a default-loading API, search conventional files, read in-cluster credentials, or fall back when the selected context fails. The host remains outside Kubernetes and uses a generated instance identity for correlation; it does not fabricate downward-API pod metadata.

Both in-cluster profiles use only `loadFromCluster()`, require downward-API host namespace/name/UID, and reject equal host/execution namespaces. Their execution permissions come from a cross-namespace RoleBinding naming only the trusted host service account.

In every profile the Kubernetes client and credential material remain solely in the trusted host. The execution pod receives neither kubeconfig nor service-account token.

**Alternatives considered:** One auto-loading client factory is convenient but can silently switch credential sources. Deploying the trusted host into a local cluster preserves in-cluster identity but makes an MCP stdio development workflow awkward and does not validate workstation kubeconfig behavior.

### 4. Preserve one hardened pod shape and distinguish image policy

Every profile uses the existing fixed non-root UID/GID, read-only root filesystem, dropped capabilities, disabled privilege escalation, runtime-default seccomp, no host namespaces, no token, no service links, zero-authority runner service account, equal CPU/memory requests and limits, bounded ephemeral storage, and one memory-backed `/tmp`. The worker starts only through the fixed non-TTY exec command after the silent wait pod is Running.

Both in-cluster profiles require a digest-pinned runner image. Local development accepts a digest or, with an explicit local-image opt-in, a safe tag combined with `imagePullPolicy: Never`. That exception is unavailable in-cluster and is recorded as unverified provenance.

The standard runtime policy omits `runtimeClassName`. The Kata policy adds the exact configured RuntimeClass after handler preflight. Neither policy can alter the base pod.

### 5. Make startup preflight proportional without blurring assurance

All profiles validate configuration, namespace access, required pod lifecycle operations, and the conforming pod shape they will create.

`local-development` verifies that its explicit identity can create, observe, exec, and delete the pod. Because local clusters may not install the versioned production ValidatingAdmissionPolicy or enforce NetworkPolicy, absence of those controls is recorded rather than blocking development. The profile can never become production-admitted.

`in-cluster` requires namespace separation, downward identity, exact SelfSubjectAccessReview permissions, acceptance of the conforming base pod, and rejection of shared unsafe variants for image, service account, token, command, environment, host access, volumes, and security context.

`kata-in-cluster` performs every standard in-cluster check plus RuntimeClass lookup, exact handler comparison, and the wrong-RuntimeClass unsafe variant. Its descriptor continues to mark CRI mapping, guest kernel, node runtime, CNI, PID limits, RuntimeClass overhead, and image provenance as external evidence.

### 6. Retain the provider-neutral channel and lifecycle unchanged

The flow remains:

```text
MCP run_javascript
  -> trusted sandbox budgets and OCI broker
  -> selected Kubernetes connection and runtime policy
  -> fresh hardened pod
  -> Running watch
  -> fixed non-TTY exec of sandbox-worker
  -> hostile framed WorkerChannel
  -> isolated-vm OCI facade and host RPC
  -> channel close, zero-grace delete, NotFound confirmation
```

The four-byte framed protocol, version and field validation, strict UTF-8, recursive decoder limits, dangerous-key rejection, message sequencing, RPC validation, deadlines, call/concurrency limits, response limits, and sanitized public errors do not vary by profile.

Abort and timeout remain authoritative during create, scheduling, connection, execution, and RPC. Finalization first rejects new bridge work and aborts the run, then starts provider termination and a rejection-observing snapshot drain of pending OCI calls concurrently against one host-clamped cleanup tail. The drain never receives a second tail after provider cleanup. A valid or timed-out result is replaced with `isolation provider cleanup failed` when pod deletion cannot be confirmed; an otherwise successful result with unawaited OCI work becomes the bounded unawaited-call failure. Trusted OCI clients use the SDK no-retry configuration, a disabled client circuit breaker, and abort-aware HTTP options, none of which can be supplied by guest code.

### 7. Reconcile according to deployment lifetime

Every trusted host reconciles expired managed pods for its selected profile at startup and periodically. Labels include the generic manager identity plus exact profile so one profile cannot accidentally adopt unrelated pods.

Both in-cluster profiles ship an independent cleanup-only reconciler outside the execution namespace with get/list/watch/delete but no create or `pods/exec`. Local development relies on host reconciliation because there is no durable in-cluster trusted deployment to outlive the workstation process; the expiry metadata still permits manual cleanup and a later opt-in cluster reconciler.

Normal cleanup and reconciliation remain idempotent and confirm NotFound. Malformed, unrelated, and non-expired pods are preserved.

### 8. Report assurance rather than infer it

The descriptor records provider, exact profile, credential mode, runtime policy, image policy, namespace topology, admission outcome, and bounded external-evidence flags. Diagnostics retain only allowlisted profile, phase, outcome, reason, duration, and correlation data.

`local-development` is always development-only. `in-cluster` reports standard container isolation and the nested V8 isolate. `kata-in-cluster` reports requested RuntimeClass/handler but remains a POC until real-node evidence and a current security review pass. RuntimeClass existence, a NetworkPolicy object, or successful execution never upgrades assurance automatically.

### 9. Layer validation so macOS testing adds evidence without replacing Kata evidence

Deterministic unit and fake API/exec tests remain the CI foundation for protocol, races, sanitized failures, and cleanup. A local-cluster integration harness uses the explicit kubeconfig profile to exercise real namespace access, pod creation, watch, exec, framed execution, timeout, deletion, and reconciliation without requiring Kata. It is opt-in when a local cluster is unavailable.

Standard in-cluster manifest and fake integration coverage verifies service-account RBAC, separate namespaces, admission shape, independent reconciliation, and the absence of RuntimeClass requirements. Kata coverage retains all exact handler, RuntimeClass, OKE/CRI-O documentation, and deferred real-provider evidence.

## Risks / Trade-offs

- **[A standard Kubernetes profile may be mistaken for VM-grade isolation]** → Use exact profile names and descriptors, never use “Kata” for standard profiles, and document their shared-kernel limitation prominently.
- **[Local kubeconfig can carry broad cluster authority]** → Require an explicit file and context, recommend a dedicated local context/namespace, never mount credentials into the runner, and label the profile development-only.
- **[Allowing local image tags weakens provenance]** → Require explicit opt-in plus `Never`, prohibit tags in-cluster, and expose the relaxed posture in the descriptor.
- **[Optional local admission checks exercise less than production topology]** → Treat local tests as lifecycle evidence only; retain required in-cluster admission/RBAC tests and Kata real-cluster evidence.
- **[Composition could still permit runtime policy to weaken the pod]** → Expose only typed additive runtime constraints and construct the full base pod after configuration validation; do not accept arbitrary mutation callbacks.
- **[Renaming Kata modules can create regressions in already-complete behavior]** → Refactor behind existing fake tests first, then add standard/local profile tests and run the full coverage, type, package, manifest, and OpenSpec validation suite.
- **[Profiles increase documentation and deployment assets]** → Share base manifests and provide small profile overlays or focused examples rather than duplicating the entire topology.
- **[Kubernetes exec/watch races and deletion failures remain security-sensitive]** → Retain the existing idempotent lifecycle, absolute deadline, forced deletion, NotFound confirmation, and adversarial race coverage unchanged.
- **[Pending OCI work could outlive the execution or add serial cleanup delay]** → Freeze bridge acceptance, abort the run, and share one cleanup deadline between provider termination and rejection-observing RPC draining; late completion cannot change the result.
- **[Disabling SDK retries changes transient-failure behavior]** → Keep retry and circuit-breaker policy host-owned, return the first sanitized failure, and require callers to issue a new complete execution when retry is appropriate.
- **[Fake and local-standard tests cannot prove Kata]** → Keep the Kata evidence plan and production-security decision separate and explicitly deferred.

## Migration Plan

1. Add profile parsing and typed shared/Kata configuration while retaining Podman as the unset default.
2. Rename and extract generic Kubernetes API, pod, lifecycle, diagnostics, and reconciliation modules without changing behavior; keep all current Kata fake tests passing through compatibility-neutral fixtures.
3. Add explicit kubeconfig and in-cluster connection factories with no auto-detection, then implement the local-development and standard in-cluster policies.
4. Move RuntimeClass/handler and Kata assurance checks into the additive Kata runtime policy.
5. Add local-cluster validation support, standard in-cluster deployment assets, profile descriptors, and documentation.
6. Run focused tests followed by coverage, type checking, package validation, manifest checks, `npm run ci`, `git diff --check`, and strict OpenSpec validation.

Because the current change has not been archived or released, no compatibility alias for the interim `kata-kubernetes` provider value is required. Rollback during development returns to the preceding commit. Future live deployment rollback selects the previously approved explicit configuration only after managed pods are drained and confirmed deleted; it never relies on automatic provider or profile fallback.

## Open Questions

The following remain deferred real-Kata questions and do not change this task breakdown:

- Which OKE region, Kubernetes/node image, bare-metal shape, CRI-O version, and pinned Kata release will instantiate the first validation profile?
- Which CNI profile and registry digest will be used for the first real Kata canary?
- Which team will own Kata patching, node cycling, quota, support posture, and the independent reconciler deployment?
