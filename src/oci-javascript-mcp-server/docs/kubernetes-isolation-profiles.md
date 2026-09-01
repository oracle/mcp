# Kubernetes Isolation Profiles

The `kubernetes` isolation provider runs each `run_javascript` call in one fresh,
credential-free pod while preserving the existing hostile framed channel,
host-owned OCI broker, nested `isolated-vm`, deadlines, call budgets, result
shape, forced deletion, and expiry reconciliation. It never auto-detects a
credential source or runtime and never falls back to Podman or another profile.

## Provider and profile matrix

| Provider/profile | Host and credentials | Runtime | Image policy | Assurance |
| --- | --- | --- | --- | --- |
| Podman (unset default) | local host, Podman CLI | host container runtime | configured local image | compatibility container isolation; shared host kernel |
| `kubernetes` / `local-development` | workstation, explicit kubeconfig file and context | cluster default | digest, or explicit safe local tag with `Never` | development-only container isolation |
| `kubernetes` / `in-cluster` | trusted host pod, service account only | cluster default | lowercase SHA-256 digest required | in-cluster container isolation |
| `kubernetes` / `kata-in-cluster` | trusted host pod, service account only | exact RuntimeClass and handler | lowercase SHA-256 digest required | Kata POC pending real-node evidence and review |

Standard runtime profiles do not provide or claim a per-execution guest kernel.
Selecting a Kata RuntimeClass is CRI-neutral and still does not prove that a pod
received the reviewed VM boundary. OKE virtual nodes are outside this POC.

## Shared configuration

Set `OCI_JAVASCRIPT_ISOLATION_PROVIDER=kubernetes` and one exact
`OCI_JAVASCRIPT_KUBERNETES_PROFILE`. Every profile requires:

| Variable | Meaning |
| --- | --- |
| `OCI_JAVASCRIPT_KUBERNETES_NAMESPACE` | Execution namespace. |
| `OCI_JAVASCRIPT_KUBERNETES_IMAGE` | Reviewed runner image under the profile image policy. |
| `OCI_JAVASCRIPT_KUBERNETES_RUNNER_SERVICE_ACCOUNT` | Zero-authority execution-pod service account. |

Optional strict base-10 settings are:

| Variable | Default | Range |
| --- | ---: | ---: |
| `OCI_JAVASCRIPT_KUBERNETES_CPU_MILLICORES` | 100 | 100–4000 |
| `OCI_JAVASCRIPT_KUBERNETES_MEMORY_MB` | 512 | 128–2048 |
| `OCI_JAVASCRIPT_KUBERNETES_EPHEMERAL_STORAGE_MB` | 64 | 16–1024 |
| `OCI_JAVASCRIPT_KUBERNETES_TMP_MB` | 16 | 1–64 |
| `OCI_JAVASCRIPT_ISOLATE_MEMORY_MB` | 128 | 16–1024 |
| `OCI_JAVASCRIPT_MAX_RESULT_BYTES` | 1048576 | 1–2031616 |
| `OCI_JAVASCRIPT_KUBERNETES_CLEANUP_TIMEOUT_SECONDS` | 30 | 1–60 |
| `OCI_JAVASCRIPT_KUBERNETES_RECONCILE_INTERVAL_SECONDS` | 30 | 5–300 |

The standard and Kata example admission policies use CEL `quantity()` bounds
for the four pod-resource settings above. Every documented CPU, memory,
ephemeral-storage, and `/tmp` value is therefore accepted without a synchronized
policy edit. CPU, memory, and ephemeral-storage requests must equal their
corresponding limits and stay within 100–4000 millicores, 128–2048 MiB, and
16–1024 MiB respectively; the memory-backed `/tmp` size must stay within
1–64 MiB. Missing, malformed, unequal, or out-of-range values fail closed.

The provider uses conservative host concurrency defaults: four active tool calls
and 64 queued calls unless the trusted operator sets the existing bounded host
settings. This POC establishes correctness, not a load or throughput target.

## Local development

`local-development` additionally requires an absolute
`OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG` path and an exact
`OCI_JAVASCRIPT_KUBERNETES_CONTEXT`. The client loads only that file and context;
it does not search default paths or try in-cluster credentials. Downward-API host
identity and Kata runtime variables are rejected.

A digest-pinned image is accepted. A locally loaded tag requires
`OCI_JAVASCRIPT_KUBERNETES_ALLOW_LOCAL_IMAGE=true`; the pod then fixes
`imagePullPolicy: Never`, and the descriptor records development-only assurance,
unverified admission/network enforcement, and unverified image provenance.

Example using a local cluster and a preloaded image:

```bash
export OCI_JAVASCRIPT_ISOLATION_PROVIDER=kubernetes
export OCI_JAVASCRIPT_KUBERNETES_PROFILE=local-development
export OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG=<absolute-kubeconfig-path>
export OCI_JAVASCRIPT_KUBERNETES_CONTEXT=oci-js-local
export OCI_JAVASCRIPT_KUBERNETES_NAMESPACE=oci-js-local
export OCI_JAVASCRIPT_KUBERNETES_RUNNER_SERVICE_ACCOUNT=oci-js-runner
export OCI_JAVASCRIPT_KUBERNETES_IMAGE=oci-javascript-mcp-runner:dev
export OCI_JAVASCRIPT_KUBERNETES_ALLOW_LOCAL_IMAGE=true
npm start
```

Use a dedicated, least-privileged context and namespace. The kubeconfig remains
on the workstation and is never mounted or copied into an execution pod.

The real-cluster lifecycle harness is opt-in. Set
`OCI_JAVASCRIPT_RUN_LOCAL_KUBERNETES_TESTS=true` plus
`OCI_JAVASCRIPT_TEST_KUBERNETES_KUBECONFIG`, `_CONTEXT`, `_NAMESPACE`, and
`_IMAGE`; optionally set `_RUNNER_SERVICE_ACCOUNT`. `npm test` otherwise reports
a clear skip. This harness exercises namespace access, create, watch, exec,
framed execution, cancellation, deletion confirmation, and reconciliation. It
is standard-runtime lifecycle evidence only and never Kata evidence.

## In-cluster profiles

Both in-cluster profiles load only service-account credentials with
`loadFromCluster()` and require these downward-API values:

| Variable | Meaning |
| --- | --- |
| `OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_NAMESPACE` | Trusted host namespace; must differ from the execution namespace. |
| `OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME` | Trusted host pod name. |
| `OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID` | Trusted host pod UID. |

Kubeconfig settings and the local-image opt-in are rejected. The runner image
must use a lowercase SHA-256 digest. The standard assets at
`examples/kubernetes/v1/standard-in-cluster.yaml` provide distinct namespaces,
the trusted host and zero-authority runner identities, cross-namespace lifecycle
RBAC, cleanup-only RBAC, restricted Pod Security labels, ResourceQuota,
LimitRange, default-deny NetworkPolicies, base-pod admission, and the independent
reconciler. They contain no RuntimeClass requirement.

### Synchronizing a local OCI session Secret

For a local in-cluster test, the trusted host needs a Kubernetes Secret with a
pod-compatible OCI config, its private key, and, for session authentication, its
current security token. Run the helper after the host namespace exists:

```bash
npm run oci:sync-kubernetes-secret -- --profile DEFAULT --restart-host
```

The helper reads `OCI_CONFIG_FILE` or `~/.oci/config`, selects
`OCI_CONFIG_PROFILE` or the specified profile, writes only the selected profile
as `[DEFAULT]` in the Secret, rewrites credential paths to `/var/run/oci`, and
never prints credential content. It creates `config`, `private-key.pem`, and
when applicable `token` in `oci-js-host-oci-config` under
`oci-js-standard-host`. For an expired OCI session, use:

```bash
npm run oci:sync-kubernetes-secret -- --profile DEFAULT --refresh-session --restart-host
```

`--dry-run` validates the selected local profile and source files without
contacting Kubernetes. The helper intentionally never creates or mounts this
Secret in the execution namespace.

`kata-in-cluster` additionally requires:

| Variable | Meaning |
| --- | --- |
| `OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_CLASS` | Exact reviewed RuntimeClass name. |
| `OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_HANDLER` | Exact expected RuntimeClass handler. |

Its assets remain under `examples/kata-kubernetes/v1/`. They add RuntimeClass
read authority, exact RuntimeClass admission, and the Kata deployment-evidence
boundary described in the [Kata POC guide](kata-kubernetes-poc.md).

## Startup, execution, and cleanup

All profiles read the execution namespace, verify exact pod lifecycle and exec
authority, and dry-run the conforming pod. The Namespace `get` access review
names exactly the configured execution Namespace, and Kata similarly names the
configured RuntimeClass; example ClusterRoles use matching `resourceNames`.
Generated pod lifecycle and exec permissions remain scoped to the execution
namespace because pod names are dynamic. In-cluster profiles fail startup if
any identified weakening of the reviewed metadata, image, service account,
token/service-link, command/environment, host namespace, container cardinality,
security context, capabilities, seccomp, filesystem, resource, deadline,
probe/hook, volume, or `/tmp` contract is accepted. Kata additionally verifies
the exact RuntimeClass/handler and rejects a wrong-RuntimeClass variant.
Successful dry-run evidence is reported as `reviewed-variants-rejected`, not as
general admission enforcement; the exact deployed policy revision remains
unverified. Local development may continue when production admission is absent,
but records that gap and can never acquire in-cluster or Kata assurance.

The server completes preflight before MCP stdio is connected. Configuration,
authentication, RBAC, namespace, RuntimeClass, admission, or reconciliation
failure is authoritative. Guest code is never retried through another provider,
profile, runtime, or credential source.

The absolute 1–120 second execution deadline includes pod creation, scheduling,
image availability, exec connection, worker execution, OCI RPC, and result
delivery. Abort or timeout remains authoritative in every phase. At
finalization, the host stops accepting bridge work and aborts the run, then
starts provider termination and a rejection-observing snapshot drain of pending
OCI calls concurrently. Both consume one configured cleanup tail, capped by the
trusted host at 60 seconds; the drain does not receive a second tail after exec
close and zero-grace pod deletion. Kubernetes channel stop and pod
delete/NotFound confirmation start concurrently against that same cleanup
deadline after pod creation settles, even when exec establishment is pending or
produces a late channel. Failure to confirm either channel closure or NotFound
returns `isolation provider cleanup failed` even after a valid or timed-out
worker result. An otherwise successful script with pending OCI work instead returns
`JavaScript completed with unawaited OCI calls` within the same bound.

Trusted-host OCI clients use the SDK no-retry policy, an explicitly disabled
client circuit breaker, and the run abort signal in HTTP options. Guest code
cannot override either policy. Cancellation therefore prevents new bridge work
and automatic retries; a late OCI promise remains rejection-observed but cannot
change the finalized MCP result.

Every host reconciles expired pods matching the generic manager label and exact
profile. Both in-cluster profiles deploy a separate cleanup-only reconciler with
get/list/watch/delete and no create or `pods/exec`. Local development relies on
host reconciliation. Unrelated, malformed, other-profile, wrong-namespace, and
non-expired pods are preserved. Each candidate consumes at most five seconds;
delete or confirmation failure increments one aggregate failure count and does
not block later candidates. Startup consumes the full pass before failing,
periodic host and cleanup-only passes emit one sanitized aggregate count, and a
failed pass does not stop future intervals.

## Diagnostics and assurance

Diagnostics are JSON lines on trusted stderr. Events contain only provider,
profile, correlation ID, allowlisted phase/outcome/reason, and bounded duration.
Descriptors identify credential mode, runtime policy, image policy, namespace
topology, admission outcome, nested `isolated-vm`, and explicit unverified
external controls, including the exact deployed admission-policy revision.
Reconciliation events may add only bounded aggregate success and failure
counts. They exclude kubeconfig paths, endpoints, credentials, raw
Kubernetes errors, guest code/output, protocol frames, pod names, and resource
details. Provider-specific data never enters MCP structured results.

NetworkPolicy objects, RuntimeClass lookup, a successful pod, and provider
self-description are not effective-boundary proof. The standard profile remains
shared-kernel container isolation. The Kata profile remains a functionally
tested POC until the real-node and security-review evidence is complete.

## Validation and operations

Run:

```bash
npm test
npm run coverage
npm run check
npm run packcheck
npm run check:kubernetes-manifests
npm run kubectl:dry-run:kubernetes
npm run ci
```

Offline fixtures cover default, non-default, minimum, maximum, missing,
malformed, unequal, and out-of-range resource settings. Client-side dry-run and
those fixtures do not establish server-side CEL evaluation or admission, RBAC
effectiveness, CNI enforcement, or a Kata guest kernel. Those remain deferred
real-cluster evidence.

After applying both versioned example ValidatingAdmissionPolicies to a test
cluster, set `OCI_JAVASCRIPT_RUN_REAL_KUBERNETES_ADMISSION_TESTS=true` together
with `OCI_JAVASCRIPT_TEST_KUBERNETES_KUBECONFIG` and
`OCI_JAVASCRIPT_TEST_KUBERNETES_CONTEXT`. `npm test` then reads both applied
policies and requires the current observed generation to contain no
`status.typeChecking.expressionWarnings`. Without that explicit opt-in, the
test reports a deliberate skip and no server-side CEL evidence is claimed.

Lifecycle tests additionally cover permanently pending OCI work, provider
termination and RPC draining sharing one cleanup tail, cleanup-failure
precedence, unawaited OCI calls, and late completion after finalization.

Before a future canary, bind exact image digests, identities, namespaces,
admission policy, network controls, node/runtime profile, and descriptor output.
Inspect managed orphans by the generic provider label plus exact profile. For
rollback, stop admission of new work, drain calls, confirm every managed pod is
deleted, verify the reconciler sees an empty namespace, and select only the
previously approved explicit configuration. Never use automatic fallback.

After node, Kubernetes, CRI, runtime, CNI, policy, image, namespace, quota,
reconciler, or service-account changes, repeat the relevant profile evidence.
Node maintenance requires draining executions, confirming cleanup, cycling the
reviewed pool, and revalidating before restoring scheduling.
