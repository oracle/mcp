# Kata Kubernetes Isolation Provider POC

This guide describes the code-complete `kubernetes` / `kata-in-cluster` proof of concept. It
is functionally tested with deterministic fake Kubernetes APIs, fake exec
streams, static manifests, and the normal CI suite. It is not production-ready
or production-admitted. A current security review and the real-cluster evidence
listed below remain mandatory.

## Provider selection and topology

The server selects one provider before connecting MCP stdio:

- omit `OCI_JAVASCRIPT_ISOLATION_PROVIDER`, or set it to `podman`, for the
  compatible local-development provider;
- set it to `kubernetes` with
  `OCI_JAVASCRIPT_KUBERNETES_PROFILE=kata-in-cluster` only in a Kubernetes pod
  with in-cluster credentials and the required configuration below.

The value is exact and case-sensitive. Invalid configuration or any Kata
preflight failure stops startup. There is no kubeconfig fallback, provider
discovery, guest selection, or automatic Podman fallback. Podman is not a
production-equivalent VM boundary and must not be used as a production rollback
for an approved Kata deployment.

The credential-bearing trusted host runs in `oci-js-host`. Credential-free
execution pods run in the separate `oci-js-execution` namespace. The example
RoleBinding names only the trusted host service account across namespaces. The
runner service account has no authority and is never token-mounted. The
cleanup-only reconciler runs outside the execution namespace under a third
identity with get/list/watch/delete only—never create or `pods/exec`.

## Configuration

Kata requires all of these trusted environment values:

| Variable | Meaning |
| --- | --- |
| `OCI_JAVASCRIPT_KUBERNETES_NAMESPACE` | Dedicated execution namespace. Must differ from the trusted host namespace. |
| `OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_CLASS` | Reviewed Kubernetes RuntimeClass name. |
| `OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_HANDLER` | Exact expected handler returned by the RuntimeClass read. |
| `OCI_JAVASCRIPT_KUBERNETES_IMAGE` | Runner image with a lowercase `@sha256:<64 hex>` digest; tags alone are rejected. |
| `OCI_JAVASCRIPT_KUBERNETES_RUNNER_SERVICE_ACCOUNT` | Zero-authority service account in the execution namespace. |
| `OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_NAMESPACE` | Trusted host namespace supplied by the downward API. |
| `OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME` | Trusted host pod name supplied by the downward API. |
| `OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID` | Trusted host pod UID supplied by the downward API. |

Optional reviewed numeric settings use strict base-10 integer grammar:

| Variable | Default | Accepted range |
| --- | ---: | ---: |
| `OCI_JAVASCRIPT_KUBERNETES_CPU_MILLICORES` | 1000 | 100–4000 |
| `OCI_JAVASCRIPT_KUBERNETES_MEMORY_MB` | 512 | 128–2048 |
| `OCI_JAVASCRIPT_KUBERNETES_EPHEMERAL_STORAGE_MB` | 64 | 16–1024 |
| `OCI_JAVASCRIPT_KUBERNETES_TMP_MB` | 16 | 1–64 |
| `OCI_JAVASCRIPT_ISOLATE_MEMORY_MB` | 128 | 16–1024 |
| `OCI_JAVASCRIPT_MAX_RESULT_BYTES` | 1048576 | 1–2031616 |
| `OCI_JAVASCRIPT_KUBERNETES_CLEANUP_TIMEOUT_SECONDS` | 30 | 1–60 |
| `OCI_JAVASCRIPT_KUBERNETES_RECONCILE_INTERVAL_SECONDS` | 30 | 5–300 |

The host deployment should populate the identity fields directly:

```yaml
env:
  - name: OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_NAMESPACE
    valueFrom: { fieldRef: { fieldPath: metadata.namespace } }
  - name: OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME
    valueFrom: { fieldRef: { fieldPath: metadata.name } }
  - name: OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID
    valueFrom: { fieldRef: { fieldPath: metadata.uid } }
```

Arbitrary pod fragments, commands, environment entries, annotations, volumes,
tolerations, selectors, or security-context overrides are not accepted.

## Startup and execution behavior

Startup loads only in-cluster credentials, reads the execution Namespace and
RuntimeClass, compares the exact handler, validates namespace separation and
the downward-API identity, and performs SelfSubjectAccessReview checks for the
exact pod lifecycle, watch/list/delete, `pods/exec`, Namespace, and RuntimeClass
operations. It then performs non-persistent server dry-runs: the conforming pod
must be accepted and unsafe variants for image mutability, RuntimeClass,
service account, token mounting, command/environment, host access, extra
volumes, and weakened security context must all be rejected.

Each call creates one uniquely named pod with a fixed silent Node wait command.
Only after the pod is Running does the host open a non-TTY Kubernetes exec
stream and start `/app/src/sandbox-worker.ts`. The existing four-byte framed
protocol, hostile decoder, OCI request validation, call/concurrency budgets,
result limits, and public-error sanitization remain above the provider.

The tool timeout is end-to-end: creation, scheduling, image pull, exec setup,
worker execution, and result delivery all consume the same 1–120 second
deadline. Abort and timeout remain authoritative in every phase. At
finalization, the host rejects new bridge work and aborts the run, then closes
exec, requests zero-grace deletion, confirms NotFound, and drains a snapshot of
pending OCI calls. Provider termination and RPC draining run concurrently
against one bounded cleanup tail (30 seconds by default, 60 maximum), not
serial tails. Unconfirmed deletion replaces any otherwise valid or timeout
result with `isolation provider cleanup failed`. A successful script that left
OCI calls unawaited returns `JavaScript completed with unawaited OCI calls`
within the same bound.

Each trusted OCI client uses the SDK no-retry policy, a disabled client circuit
breaker, and the run abort signal. These controls are host-owned and cannot be
changed by guest client options. Late OCI completion cannot restore bridge
authority or modify an already finalized result.

Host reconciliation runs at startup and periodically. It deletes only labeled
managed pods whose well-formed trusted expiry has passed and preserves every
non-expired, malformed, or unrelated pod, including pods from another host
replica. The independent reconciler uses the same rule so cleanup continues
when every host replica is unavailable.

Trusted stderr diagnostics contain only provider ID, random correlation ID,
allowlisted phase/outcome/reason, and bounded duration. They exclude code,
guest output, protocol payloads, OCI requests/responses, Kubernetes errors,
credentials, endpoints, events, and resource details. The provider descriptor
explicitly marks CRI mapping, node runtime, CNI isolation, PID limits,
RuntimeClass overhead, and image provenance as unverified external evidence.

Existing host concurrency defaults remain conservative: four active and 64
queued tool calls unless separately configured. The POC establishes correctness
for a small fixed number of concurrent executions, not load, throughput,
capacity, or high-concurrency readiness.

## Build and immutable image configuration

Build the runner reproducibly from the pinned Node base in `Containerfile`:

```bash
npm ci
podman build --pull --file Containerfile --tag registry.example/oci-javascript-runner:poc .
podman push registry.example/oci-javascript-runner:poc
podman inspect --format '{{index .RepoDigests 0}}' registry.example/oci-javascript-runner:poc
```

Record build provenance and configure the returned repository digest, never the
tag, as `OCI_JAVASCRIPT_KUBERNETES_IMAGE`; set the same reviewed runner digest in the
versioned admission policy. Build the full trusted host/reconciler image with
`Containerfile.host`, publish it by digest, and replace the placeholder in
`07-cleanup-reconciler.yaml`. The guest image contains only the worker and its
`isolated-vm` runtime; it contains neither the Kubernetes client nor OCI SDK or
credentials.

## Versioned deployment assets

Assets live in `examples/kata-kubernetes/v1/` and include separate namespaces,
restricted Pod Security labels, all three service accounts, cross-namespace
least-privilege RBAC, quota and limits, default-deny ingress/egress policies, a
RuntimeClass example, fail-closed ValidatingAdmissionPolicy/binding, and the
cleanup-only Deployment.

Validate offline and perform a client-side dry run:

```bash
npm run check:kata-manifests
npm run kubectl:dry-run:kata
```

The kubectl command uses a temporary loopback discovery fixture so the client
can map built-in resource kinds without credentials or a live cluster.
Client-side parsing and offline CEL/static assertions are POC evidence.
Server-side dry-run enforcement against the selected Kubernetes release and
real admission chain is deliberately deferred real-cluster evidence.

## CRI-neutral boundary and future OKE profile

Provider code submits `runtimeClassName`, reads the RuntimeClass, and compares
its handler. It never reads or modifies containerd, CRI-O, node files, runtime
sockets, shim installation, or hypervisor configuration. Those are deployment
responsibilities bound by external evidence.

The first future OKE validation profile keeps the OKE-managed node's CRI-O and
uses a dedicated supported x86_64 bare-metal node pool. The Kata binary name
`containerd-shim-kata-v2` does not require containerd to be the node CRI: CRI-O
can invoke that shim through its reviewed handler mapping. Capture the rendered
CRI-O drop-in, shim/config paths and digests, versions, RuntimeClass/handler and
overhead, guest and host kernels, scheduling labels/taints, and bootstrap state
from every admitted node.

OKE virtual nodes are excluded because they cannot provide the DaemonSet,
runtime mapping, overhead, CNI, guest-kernel, or exec evidence this boundary
requires. Start with an isolated Flannel-plus-Calico validation cluster. Treat
OCI VCN-native `ipvlan`/`ptp` networking as a separate non-admitted profile
until metadata, control-plane, private, link-local, resident-node, DNS, and
public egress denial is proven after guest compromise. Kata is third-party
software on OKE; deployment ownership, patching, support boundaries, quota,
and node replacement must be recorded.

## Future canary, recovery, rollback, and revalidation

These steps are non-blocking operational guidance for work after this POC:

1. Apply the versioned controls, publish both images by digest, and run
   server-side admission dry-runs before creating execution pods.
2. Admit one tainted Kata node only after bootstrap proves the CRI-O handler,
   Kata configuration, hypervisor, CNI, PID limit, and RuntimeClass overhead.
3. Canary a small fixed call count. Inspect managed pods with
   `kubectl get pods -n oci-js-execution -l app.kubernetes.io/managed-by=oci-javascript-mcp,oci.oracle.com/isolation-provider=kubernetes,oci.oracle.com/kubernetes-profile=kata-in-cluster`.
4. Stop all host replicas and verify the independent reconciler preserves
   non-expired pods, removes expired pods after recovery, and emits only bounded
   diagnostics. Repeat across reconciler restart and temporary API outage.
5. For rollback, stop new admission, confirm all managed execution pods are
   deleted, verify reconciliation observes an empty namespace, and restore the
   previous approved Kata deployment. Do not silently select Podman.
6. Before node maintenance, drain executions, confirm cleanup, cordon/drain the
   dedicated pool, cycle nodes, and re-run the complete evidence suite before
   restoring the scheduling label/taint.

Revalidate after any Kubernetes/node image, CRI-O mapping, RuntimeClass,
Kata/runtime configuration, node pool, CNI, runner digest, namespace topology,
admission policy, reconciler identity/deployment, NetworkPolicy, quota, PID, or
overhead change.

Production admission still requires real-provider proof of the VM guest kernel,
credential/mount absence, effective network denial, resource/PID/storage limits,
hostile raw-channel handling, timeout/cancellation, forced deletion, host and
independent orphan cleanup, reconciler outage recovery, node replacement, and
concurrent isolation—plus a current security review. Until then, describe this
implementation only as a functionally tested POC.
