# Kubernetes Isolation Profiles

Source-reviewed with branch `b0ad446` on 2026-10-09. Commands and deployment
controls below were inspected, not executed in this documentation pass. Earlier
POC evidence claims retain their original scope; this review does not establish
current cluster enforcement or production admission.

The `kubernetes` isolation provider runs each `run_javascript` call in one fresh,
credential-free pod while using the shared execution-scoped protobuf gRPC transport,
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

The server defaults to four active tool calls across both tools, controlled by
`OCI_JAVASCRIPT_MAX_CONCURRENT_TOOL_CALLS`. Excess calls are rejected; no
application-level queue or 64-call queue setting is implemented. Test definitions
cover fixed-concurrency behavior, not a measured load or throughput target.

## Local development

`local-development` additionally requires an absolute
`OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG` path and an exact
`OCI_JAVASCRIPT_KUBERNETES_CONTEXT`. The client loads only that file and context;
it does not search default paths or try in-cluster credentials. Downward-API host
identity and Kata runtime variables are rejected.

A digest-pinned image is accepted. A locally loaded tag requires
`OCI_JAVASCRIPT_KUBERNETES_ALLOW_LOCAL_IMAGE=true`; the pod then fixes
`imagePullPolicy: Never`. This is a development-only configuration; image
provenance and effective admission/network enforcement require external evidence.

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
`_IMAGE`; optionally set `_RUNNER_SERVICE_ACCOUNT`. `moon run oci-javascript-mcp-server:test` otherwise reports
a clear skip. This harness exercises namespace access, create, watch, exec
bootstrap, port-forwarded gRPC execution, cancellation, deletion confirmation,
and reconciliation. It
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
python3 scripts/sync-oci-session-secret.py --profile DEFAULT --restart-host
```

The helper reads `OCI_CONFIG_FILE` or `~/.oci/config`, selects
`OCI_CONFIG_PROFILE` or the specified profile, writes only the selected profile
as `[DEFAULT]` in the Secret, rewrites credential paths to `/var/run/oci`, and
never prints credential content. It creates `config`, `private-key.pem`, and
when applicable `token` in `oci-js-host-oci-config` under
`oci-js-standard-host`. For an expired OCI session, use:

```bash
python3 scripts/sync-oci-session-secret.py --profile DEFAULT --refresh-session --restart-host
```

`--dry-run` validates the selected local profile and source files without
contacting Kubernetes. The helper intentionally never creates or mounts this
Secret in the execution namespace.

`kata-in-cluster` additionally requires:

| Variable | Meaning |
| --- | --- |
| `OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_CLASS` | Exact reviewed RuntimeClass name. |
| `OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_HANDLER` | Exact expected RuntimeClass handler for deployment validation. |

Its assets remain under `examples/kata-kubernetes/v1/`. They add RuntimeClass
read authority for validation under the host identity, exact RuntimeClass
admission, and the Kata deployment-evidence
boundary described in the [Kata POC guide](kata-kubernetes-poc.md).

## Startup, execution, and cleanup

All profiles read the execution namespace and verify namespace/pod lifecycle
permissions. In-cluster profiles also require Secrets create/get/list/delete;
workstation local-development instead requires exec and `pods/portforward`.
Reconciliation covers pods and, in-cluster, TLS Secrets for the exact namespace/profile. The Namespace `get` access review names
exactly the configured execution Namespace; generated pod operations remain
execution-namespace scoped because pod names are dynamic. Periodic reconciliation
starts after the startup sweep succeeds.

The server completes operational preflight before MCP stdio is connected.
Configuration, authentication, RBAC, namespace access or startup reconciliation
failure stops startup. Execution is gated on a private readiness flag: pending
or failed preflight blocks new runs, including failure after an earlier success.
Stopping the reconciliation timer alone does not revoke readiness. Guest code is
never retried through another provider, profile, runtime or credential source.

Server startup performs no admission dry-runs or live RuntimeClass/handler
checks and emits no assurance descriptor. Run [deployment validation](#deployment-validation)
before rollout. An operationally ready server can still encounter policy rejection
or an unavailable RuntimeClass during actual pod creation/scheduling; those
fail through the normal bounded execution contract.

The absolute 1–120 second execution deadline includes pod creation, scheduling,
image availability, TLS Secret provisioning (or local exec/port-forward), gRPC readiness,
worker execution, OCI RPC, and result
delivery. Abort or timeout remains authoritative in every phase. At
finalization, the host stops accepting bridge work and aborts the run, then
starts provider termination and a rejection-observing snapshot drain of pending
OCI calls concurrently. Both consume one configured cleanup tail, capped by the
trusted host at 60 seconds; the drain does not receive a second tail. Kubernetes
channel stop and pod/Secret delete/NotFound confirmation start concurrently against that same cleanup
deadline. Pending runner/tunnel acquisition is independently bounded and cannot
prevent pod deletion from being attempted. Late transport handles receive the
original cleanup deadline; late pod or Secret creation triggers compensating deletion.
Failure to confirm the gRPC session, local tunnel/runner closure, or resource NotFound
returns `isolation provider cleanup failed` even after a valid or timed-out
worker result. If provider cleanup succeeds but pending OCI work does not settle
before that deadline, `OCI cleanup did not complete` overrides the earlier outcome. Only an
otherwise successful run whose drain completes returns
`JavaScript completed with unawaited OCI calls` when OCI work was pending at
finalization. Late promises retain rejection observers.

Trusted-host OCI clients use the SDK no-retry policy, an explicitly disabled
client circuit breaker, and the run abort signal in HTTP options. Guest code
cannot override either policy. Cancellation therefore prevents new bridge work
and automatic retries; a late OCI promise remains rejection-observed but cannot
change the finalized MCP result.

Every host reconciles expired pods and, in-cluster, TLS Secrets matching the
generic manager label and exact profile. Independent Secret listing also finds
orphans from partial creation. Both in-cluster profiles deploy a separate
cleanup-only reconciler with pod get/list/watch/delete and Secret get/list/delete,
with no create, `pods/exec`, or `pods/portforward`. Local development relies on
host reconciliation. Unrelated, malformed, other-profile, wrong-namespace, and
non-expired resources are preserved. Each candidate consumes at most five seconds;
delete or confirmation failure increments one aggregate failure count and does
not block later candidates. Startup consumes the full pass before failing,
periodic host and cleanup-only passes emit one sanitized aggregate count, and a
failed pass does not stop future intervals.

## Direct in-cluster transport and rollout evidence

Both in-cluster profiles require host-to-pod IP reachability on TCP 50051.
Each runner starts normally with `--tls-files`, reads its immutable
`<pod-name>-tls` Secret at `/run/oci-javascript/tls`, and authenticates the host
using application mTLS. The Secret contains only the runner key/certificate and
the host public certificate. OCI credentials and the host private key remain on
the host. Mode 0440 and fsGroup 65532 provide non-root read access. Istio is not
required; the example execution namespaces disable sidecar injection and ambient
enrollment. See the [architecture decision](architecture-and-isolation-design.md#architecture-decision-direct-in-cluster-transport).

Before rollout, restrict access to execution Secrets and enable encryption at
rest for Secrets in the cluster. Update the matching host/runner images, RBAC,
admission and NetworkPolicies as one deployment increment. Old policies reject
the TLS mount and new policies reject the old wait command. The local-in-cluster
example also uses direct transport; workstation `local-development` retains its
explicit tunnel. Rollback drains executions, confirms pod and TLS Secret absence,
and restores the previous matching images and policy/RBAC bundle.

The following opt-in tests run inside the trusted host using its configured
in-cluster identity. They do not use OCI APIs. Deploy the matching images and
policy assets first, and run the standalone deployment validator below. Set the
three variables to the actual target; the standard example values are shown:

```bash
export HOST_NAMESPACE=oci-js-standard-host
export HOST_POD_LABEL=oci-js-standard-host
export HOST_CONTAINER=host
HOST_POD=$(kubectl -n "$HOST_NAMESPACE" get pods \
  -l "app.kubernetes.io/name=$HOST_POD_LABEL" \
  -o jsonpath='{.items[0].metadata.name}')
TEST_DIRECTORY=$(kubectl -n "$HOST_NAMESPACE" exec "$HOST_POD" -c "$HOST_CONTAINER" -- \
  node -e 'const fs=require("node:fs"); const d=fs.mkdtempSync("/tmp/oci-js-tests-"); fs.mkdirSync(d+"/test"); fs.symlinkSync("/app/src",d+"/src"); fs.symlinkSync("/app/node_modules",d+"/node_modules"); console.log(d)')
kubectl -n "$HOST_NAMESPACE" cp \
  test/kubernetes-direct-integration.test.ts \
  "$HOST_POD:$TEST_DIRECTORY/test/kubernetes-direct-integration.test.ts" \
  -c "$HOST_CONTAINER"
kubectl -n "$HOST_NAMESPACE" exec "$HOST_POD" -c "$HOST_CONTAINER" -- \
  env OCI_JAVASCRIPT_RUN_DIRECT_KUBERNETES_TESTS=true \
  node --no-node-snapshot --experimental-strip-types --test \
  "$TEST_DIRECTORY/test/kubernetes-direct-integration.test.ts"
```

Run from the package directory. The host mounts writable `/tmp`; copying the
test does not modify its read-only application files. Operator exec/copy authority
is separate from the host service account's execution Role, which has no exec
or port-forward grants. For Kata use host namespace `oci-js-host`, pod label
`oci-js-kata-host`, and container `host`, on actual reviewed Kata nodes.

Require exit 0 for execution, cancellation, and orphan-Secret reconciliation.
These tests confirm their own resource absence; they do not certify the CNI,
Secret-store encryption, or VM boundary. Record additional target evidence:

- While a runner exists, confirm its TLS projection is read-only and readable by
  UID/GID 65532, and its pod has no service-account token or OCI credential mount.
- Confirm trusted-host TCP 50051 access and rejection from an unauthorized
  namespace/workload. Inspect CNI enforcement, not only the policy objects.
- Confirm wrong execution certificates cannot open a session and runner-initiated
  egress is blocked while replies on the established stream work.
- Confirm conforming admission succeeds, every negative variant fails, and live
  CEL type checking reports no expression warnings.
- Confirm the independent reconciler removes expired pods and orphan TLS Secrets
  when the MCP host is unavailable, while preserving unexpired resources.

No live direct-transport, CNI, encryption-at-rest, or Kata evidence is established
by the normal unit suite or offline kubectl dry-run.

## Deployment validation

Run the standalone validator after applying the target deployment's namespace,
RBAC, admission and runtime assets. It checks API identity, execution
permissions, the Kata RuntimeClass/handler when selected, and acceptance or
rejection of server-side pod dry-runs. It reuses the same pod builder and reviewed
negative variants used to review the execution pod contract, without starting MCP or loading OCI
credentials or the native isolate.

The command can run on a workstation, in a pipeline, or in another environment
with Node 26+, the package dependencies, cluster access and an explicit kubeconfig
using supported credentials. Automatic in-cluster service-account authentication
is deferred; a Kubernetes Job would currently need an explicit kubeconfig too.

Set the existing environment variables for the **target** profile, runner image,
runner service account and resource settings. The explicit
`--kubeconfig` and `--context` arguments select the **connection**, even when
validating an in-cluster target. This does not change the server's credential
selection rules. No default kubeconfig or in-cluster credential discovery occurs.

For the standard example, set `RUNNER_IMAGE_DIGEST` to the reviewed runner image
reference, including its 64-character SHA-256 digest, then run from the package
directory:

```bash
export OCI_JAVASCRIPT_ISOLATION_PROVIDER=kubernetes
export OCI_JAVASCRIPT_KUBERNETES_PROFILE=in-cluster
export OCI_JAVASCRIPT_KUBERNETES_NAMESPACE=oci-js-standard-execution
export OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_NAMESPACE=oci-js-standard-host
export OCI_JAVASCRIPT_KUBERNETES_RUNNER_SERVICE_ACCOUNT=oci-js-runner
export OCI_JAVASCRIPT_KUBERNETES_IMAGE="$RUNNER_IMAGE_DIGEST"

node --no-node-snapshot --experimental-strip-types \
  src/kubernetes-deployment-validation.ts \
  --kubeconfig "$HOME/.kube/config" --context your-context \
  --host-service-account oci-js-standard-host --impersonate
```

For the Kata example, use `kata-in-cluster`, execution namespace
`oci-js-execution`, trusted-host namespace `oci-js-host` and host service account
`oci-js-host`. Additionally set `OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_CLASS`
and `OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_HANDLER` to the deployed values;
the versioned example uses `kata-qemu-runtime-rs` for both. Supply the reviewed
Kata runner image digest.

For `local-development`, use its existing local configuration and omit
`--host-service-account` and `--impersonate`:

```bash
node --no-node-snapshot --experimental-strip-types \
  src/kubernetes-deployment-validation.ts \
  --kubeconfig "$HOME/.kube/config" --context your-local-context
```

All in-cluster targets require `--host-service-account`. The validator derives
its expected username from that name and the trusted-host namespace, then checks
the effective username and normal service-account groups through
`authentication.k8s.io/v1` SelfSubjectReview. A kubeconfig authenticated directly
as that account needs no `--impersonate` flag. For an operator kubeconfig,
`--impersonate` requires existing permission to impersonate that specific
service account; the command does not grant permissions or retry as the operator.
See [Kubernetes impersonation](https://kubernetes.io/docs/reference/access-authn-authz/user-impersonation/).
The identity must also be allowed to create self-access reviews, read the
execution namespace, perform pod lifecycle and in-cluster Secret lifecycle
operations (exec/port-forward for workstation local-development) and, for Kata,
read the configured RuntimeClass. Missing review
support or permission fails validation rather than assuming the workload identity.

If downward-API host pod name or UID variables are absent, dry-run probes use
synthetic host metadata and the report says `synthetic-host-identity`. These
values describe probe metadata; they do not verify an existing host pod or its
ownership. Supplied values retain the existing configuration validation.
The kubeconfig file is never modified.

Use a kubeconfig with valid token or client-certificate credentials. This first
version rejects `exec` and legacy `auth-provider` credential helpers before
running them: the SDK performs that authentication before request cancellation
is attached, so a stalled helper could outlive the validation deadline. Prepare
credentials through your approved authentication procedure before invoking the
validator; the command neither launches helpers nor falls back to other
credentials.

From the repository root, the opt-in Moon task invokes the same source command:

```bash
moon run oci-javascript-mcp-server:validate-deployment -- \
  --kubeconfig "$HOME/.kube/config" --context your-context \
  --host-service-account oci-js-standard-host --impersonate --json
```

The task is uncached and does not run in ordinary CI. After compilation, the
packed command is also available as `node dist/kubernetes-deployment-validation.js`
from the installed package directory. `--help` requires no deployment configuration
or cluster access. `--json` emits the same check outcomes as human output.
`--timeout-seconds` sets the whole API-validation deadline from 1 to 300 seconds
(default 60); SIGINT/SIGTERM cancel validation.

Exit code **0** means every required check passed. Exit code **1** means a check
failed or was inconclusive, including configuration, identity, authentication,
transport, malformed-response, timeout or cancellation failures. Every pod
submission has `dryRun=All`; the validator does not persist or execute runner
pods, establish channels, reconcile resources or delete pods. The conforming pod
must be accepted before negative probes run. An accepted negative variant fails
validation even for local development. Server startup does not test admission
for any profile.

A rejected probe records a matching Kubernetes Status response and HTTP status
and reason. It does not identify which admission policy, RBAC rule, schema
validation or other API control rejected the request, or certify the deployed
policy revision. A passing report does not establish CNI/CRI enforcement, a Kata
guest kernel, image provenance, effective resource limits or production
readiness. Real execution and external isolation evidence remain separate checks.

Deployment validation is an external pre-rollout gate. Operators or pipelines
run this command with the intended configuration and identity and require exit
0 before proceeding. The server neither invokes the command nor consumes its
report or a validation token; startup success is not deployment-policy evidence.

## Operational diagnostics and deployment evidence

Diagnostics are JSON lines on trusted stderr. Events contain only provider,
profile, correlation ID, allowlisted phase/outcome/reason, and bounded duration.
Reconciliation events may add only bounded aggregate success and failure
counts. They exclude kubeconfig paths, endpoints, credentials, raw Kubernetes
errors, guest code/output, protocol frames, pod names, and resource details.
Provider-specific data never enters MCP structured results. The server exposes
no assurance descriptor; operators retain validation reports and external
isolation evidence alongside the exact deployment configuration.

NetworkPolicy objects, RuntimeClass lookup and a successful pod are not
effective-boundary proof. The standard profile remains shared-kernel container
isolation. The Kata profile remains a functionally tested POC until the real-node
and security-review evidence is complete.

## Validation and operations

Run from the server directory or repository root:

```bash
moon run oci-javascript-mcp-server:compile
moon run oci-javascript-mcp-server:test
moon run oci-javascript-mcp-server:check
moon run oci-javascript-mcp-server:build
moon run oci-javascript-mcp-server:check-kubernetes-manifests
moon run oci-javascript-mcp-server:kubectl-dry-run-kubernetes
```

The test task enforces at least 90% statements, branches, functions, and lines
and checks the packed MCP entry point. The build task creates the tarball.
Compile runs the reviewed native setup; see [repository and consumer installation
guidance](../README.md#development) for the lifecycle policy.

Offline fixtures cover default, non-default, minimum, maximum, missing,
malformed, unequal, and out-of-range resource settings. Client-side dry-run and
those fixtures do not establish server-side CEL evaluation or admission, RBAC
effectiveness, CNI enforcement, or a Kata guest kernel. Those remain deferred
real-cluster evidence.

After applying both versioned example ValidatingAdmissionPolicies to a test
cluster, set `OCI_JAVASCRIPT_RUN_REAL_KUBERNETES_ADMISSION_TESTS=true` together
with `OCI_JAVASCRIPT_TEST_KUBERNETES_KUBECONFIG` and
`OCI_JAVASCRIPT_TEST_KUBERNETES_CONTEXT`. The Moon test task then reads both
applied policies and requires the current observed generation to contain no
`status.typeChecking.expressionWarnings`. Without that explicit opt-in, the
test reports a deliberate skip and no server-side CEL evidence is claimed.

Lifecycle tests additionally cover permanently pending OCI work, provider
termination and RPC draining sharing one cleanup tail, cleanup-failure
precedence, unawaited OCI calls, and late completion after finalization.

Before a future canary, bind exact image digests, identities, namespaces,
admission policy, network controls, node/runtime profile, and deployment-validation
report plus external isolation evidence.
Inspect managed orphans by the generic provider label plus exact profile. For
rollback, stop admission of new work, drain calls, confirm every managed pod is
deleted, verify the reconciler sees an empty namespace, and select only the
previously approved explicit configuration. Never use automatic fallback.

After node, Kubernetes, CRI, runtime, CNI, policy, image, namespace, quota,
reconciler, or service-account changes, repeat the relevant profile evidence.
Node maintenance requires draining executions, confirming cleanup, cycling the
reviewed pool, and revalidating before restoring scheduling.
