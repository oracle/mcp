# Local Kubernetes in-cluster setup

This guide records the local Rancher Desktop workflow for running the OCI
JavaScript MCP server with the `kubernetes` / `in-cluster` profile. It uses
[`examples/kubernetes/v1/local-in-cluster.yaml`](../examples/kubernetes/v1/local-in-cluster.yaml),
which is an alternative to `standard-in-cluster.yaml`; do not apply both. The
profile uses ordinary Kubernetes container isolation, not a Kata or VM boundary,
and is for local development only.

The trusted host holds both OCI credentials and Kubernetes service-account
credentials. Every execution runner is a fresh, credential-free pod in a
separate namespace. That separation is a security requirement, not merely a
deployment convention.

## What the working local setup requires

- Node.js 26 or newer. For local package tasks, use the [repository installation
  policy](../README.md#development): `npm ci --ignore-scripts` followed by the
  reviewed native setup. Image builds prepare dependencies inside their own
  build stages and do not require a host native-addon build.
- A running Kubernetes cluster and a `kubectl` context that can create
  namespaces, RBAC, quota/limit, NetworkPolicy, Deployment, and
  `ValidatingAdmissionPolicy` resources. The verified local target is the
  `rancher-desktop` context on Kubernetes `v1.35.4+k3s1`.
- A cluster that supports `admissionregistration.k8s.io/v1`
  `ValidatingAdmissionPolicy`; the manifest fails closed if its policy cannot be
  created.
- Two Node 26 images available to every node under immutable, lowercase
  SHA-256 repository digests: the runner built from `Containerfile` and the
  trusted host/reconciler built from `Containerfile.host`.
- A usable OCI CLI profile. API-key profiles need `user`, `fingerprint`,
  `tenancy`, `region`, and `key_file`; session profiles additionally need a
  current `security_token_file`.

The checked-in `localhost/...@sha256:...` image references are appropriate only
when the Rancher Desktop node can resolve those exact local images. For a
multi-node cluster, publish both images to a registry available to every node.
An image ID or a mutable tag is not a substitute for a repository digest.

## 1. Build, make available, and pin the images

For Rancher Desktop using the Moby container engine, confirm Docker targets the
local cluster's image store:

```sh
docker context show
```

The expected context is `rancher-desktop`. If another context is selected, use
`docker context use rancher-desktop` before building.

From the repository root, build both images, including after local code changes:

```sh
moon run oci-javascript-mcp-server:k8s-build
```

Read the full repository-digest references from the newly built images:

```sh
docker image inspect localhost/oci-javascript-mcp-host:dev \
  --format '{{index .RepoDigests 0}}'
docker image inspect localhost/oci-javascript-mcp-runner:dev \
  --format '{{index .RepoDigests 0}}'
```

Each output must be a full `localhost/...@sha256:<64 lowercase hex characters>`
reference. Copy the `RepoDigests` reference, not the image `Id` or the `:dev` tag.
If no repository digest is available, import or publish the images through the
image store used by the target cluster and obtain their repository digests there
before continuing. For a registry-backed deployment, use the registry repository
references instead of `localhost/...`.

In `src/oci-javascript-mcp-server/examples/kubernetes/v1/local-in-cluster.yaml`,
replace all four image references:

| Location | Replacement |
| --- | --- |
| Deployment `oci-js-standard-host`, container `host`, `image` | Full host repository-digest reference |
| Deployment `oci-js-standard-reconciler`, container `reconciler`, `image` | The same host reference |
| Host environment variable `OCI_JAVASCRIPT_KUBERNETES_IMAGE`, `value` | Full runner repository-digest reference |
| Admission-policy expression `object.spec.containers[0].image == '...'` | The same runner reference inside the quotes |

Find-and-replace the old full host reference throughout this file, then do the
same for the old full runner reference. Each occurs twice. **The runner reference
in the host environment and admission policy must be identical**; a mismatch
causes admission to reject runner pods. Reapply this manifest after every digest
update, using the next step.

The runner image uses `IfNotPresent`. This is intentional: in-cluster profiles
reject tags and do not permit the `local-development` profile's local-image
escape hatch.

## 2. Apply the versioned local manifest

From `src/oci-javascript-mcp-server`:

```sh
kubectl --context rancher-desktop apply \
  -f examples/kubernetes/v1/local-in-cluster.yaml
```

This creates the following required controls:

| Area | Resources and purpose |
| --- | --- |
| Trust separation | `oci-js-standard-host` and `oci-js-standard-execution` namespaces. Only the host namespace may receive OCI credentials. |
| Identities | A host service account with create/exec lifecycle authority, a zero-authority runner account with token automount disabled, and a cleanup-only reconciler account. |
| Admission | A fail-closed policy and binding that only admits the host-created, fixed runner-pod shape. |
| Resource and network bounds | Execution-namespace quota, limit range, and default-deny ingress and egress NetworkPolicies. |
| Availability and cleanup | One trusted host Deployment and a separate reconciler Deployment that can delete expired managed runner pods but cannot create or exec them. |

Changing the Deployment image references automatically starts a rollout; no
separate rollout restart is needed for an image update. If the OCI Secret is
already configured and current, proceed directly to the verification in step 4.

The host deployment may remain unavailable until the OCI Secret is created. That
is expected; do not bypass the Secret mount or put the Secret in the execution
namespace.

## 3. Synchronize OCI credentials into the host-only Secret

The helper turns one local OCI profile into the pod-compatible Secret
`oci-js-host-oci-config` in namespace `oci-js-standard-host`. It writes a
sanitized `[DEFAULT]` config that refers only to `/var/run/oci` paths and never
prints credential content.

First, validate the selected local profile without changing the cluster:

```sh
python3 scripts/sync-oci-session-secret.py \
  --context rancher-desktop --profile DEFAULT --dry-run
```

Then create or update the Secret and restart the trusted host so it reloads the
mount:

```sh
python3 scripts/sync-oci-session-secret.py \
  --context rancher-desktop --profile DEFAULT --restart-host
```

For an expired OCI session profile, refresh before updating the Secret:

```sh
python3 scripts/sync-oci-session-secret.py \
  --context rancher-desktop --profile DEFAULT --refresh-session --restart-host
```

The Secret contains `config` and `private-key.pem`, plus `token` for a session
profile. Inspect only its metadata or key names; do not print or commit its
data. The example `oci-js-host-oci-config.secret.local.yaml` is intentionally a
local-only template, not a place to store credentials in Git.

## 4. Verify deployment and startup controls

After applying the manifest and ensuring the OCI Secret is available, wait for
both Deployments to complete their rollouts:

```sh
kubectl --context rancher-desktop -n oci-js-standard-host \
  rollout status deployment/oci-js-standard-host --timeout=120s
kubectl --context rancher-desktop -n oci-js-standard-host \
  rollout status deployment/oci-js-standard-reconciler --timeout=120s
```

Then inspect the deployment and required controls:

```sh
kubectl --context rancher-desktop get namespace \
  oci-js-standard-host oci-js-standard-execution
kubectl --context rancher-desktop -n oci-js-standard-host get deployment,pod
kubectl --context rancher-desktop -n oci-js-standard-execution get \
  serviceaccount,resourcequota,limitrange,networkpolicy
kubectl --context rancher-desktop get validatingadmissionpolicy \
  oci-js-standard-execution-pods-v1
```

Both rollout commands must succeed before connecting the Inspector. A successful
host startup also performs service-account/RBAC checks and server
dry-runs of the approved runner-pod contract before accepting MCP stdio.

For local manifest checks, run from the repository root:

```sh
moon run oci-javascript-mcp-server:check-kubernetes-manifests
moon run oci-javascript-mcp-server:kubectl-dry-run-kubernetes
```

These are static/client-side checks; they do not prove effective cluster RBAC,
admission, CNI enforcement, or runtime containment.

### Troubleshoot `ErrImagePull` or `ImagePullBackOff`

Compare the live Deployment image references with the host repository digest
obtained in step 1:

```sh
kubectl --context rancher-desktop -n oci-js-standard-host get deployment \
  oci-js-standard-host oci-js-standard-reconciler \
  -o 'custom-columns=NAME:.metadata.name,IMAGE:.spec.template.spec.containers[0].image'
kubectl --context rancher-desktop -n oci-js-standard-host get events \
  --field-selector type=Warning --sort-by=.lastTimestamp
```

Editing the YAML does not update existing Deployments until `kubectl apply`
succeeds. If the live references still contain an old digest, reapply the updated
`local-in-cluster.yaml` using step 2, then repeat the rollout checks above. Apply
the whole manifest so the runner environment and admission policy update together.

If events report a connection refused at `https://localhost/v2/...`, Kubernetes
has attempted to pull the requested image from a registry on the node's localhost.
For this local workflow, verify that the exact live digest resolves in the
Rancher Desktop Docker image store; having only a different digest under `:dev`
does not satisfy it. If the live digest is correct but unavailable locally, make
that exact image available using step 1 before retrying the rollout.

## 5. Connect the Inspector through the trusted host

The deployment is a stdio MCP server, so it has no HTTP service to browse to.
Start the Inspector locally and have it open an interactive `kubectl exec`
session into the already configured trusted host:

```sh
npx --yes @modelcontextprotocol/inspector \
  kubectl --context rancher-desktop -n oci-js-standard-host exec -i \
  deployment/oci-js-standard-host -- \
  node --no-node-snapshot --experimental-strip-types /app/src/server.ts
```

This starts a second stdio server process inside the trusted host container for
the Inspector session. It inherits the mounted OCI Secret and the host service
account, while the JavaScript execution itself still occurs in a newly created
runner pod. Do not use `-t`: a TTY corrupts the JSON-RPC stdio stream.

## Operational constraints

- Never mount OCI or Kubernetes credentials, host paths, devices, or runtime
  sockets into the execution namespace or runner pod.
- Do not weaken the manifest's admission policy to change a runner image,
  command, environment, security context, volumes, resources, or service
  account. Update the reviewed manifest and the matching image digest together.
- Keep the host and execution namespaces distinct. The runner account must stay
  token-free and have no RBAC binding.
- This local profile uses a shared-kernel standard runtime. It is not a
  production deployment or evidence of a Kata VM boundary. See the
  [Kubernetes isolation profile guide](kubernetes-isolation-profiles.md) and
  [Kata POC guide](kata-kubernetes-poc.md) for the broader profile and evidence
  requirements.
