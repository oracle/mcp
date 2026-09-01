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

- Node.js 26 or newer and the package dependencies (`npm ci`) in this directory.
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

Build the two images from this package:

```sh
npm ci
npm run docker:build
npm run docker:build-host
```

Import or publish the images through the image store used by the target cluster,
then obtain their repository digests. Before applying the manifest, set:

- the host/reconciler image at the two Deployment container `image` fields;
- the runner image in `OCI_JAVASCRIPT_KUBERNETES_IMAGE`; and
- **the identical runner digest** in the admission-policy expression that
  requires `object.spec.containers[0].image`.

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
npm run oci:sync-kubernetes-secret -- --profile DEFAULT --dry-run
```

Then create or update the Secret and restart the trusted host so it reloads the
mount:

```sh
npm run oci:sync-kubernetes-secret -- --profile DEFAULT --restart-host
```

For an expired OCI session profile, refresh before updating the Secret:

```sh
npm run oci:sync-kubernetes-secret -- \
  --profile DEFAULT --refresh-session --restart-host
```

The Secret contains `config` and `private-key.pem`, plus `token` for a session
profile. Inspect only its metadata or key names; do not print or commit its
data. The example `oci-js-host-oci-config.secret.local.yaml` is intentionally a
local-only template, not a place to store credentials in Git.

## 4. Verify deployment and startup controls

```sh
kubectl --context rancher-desktop get namespace \
  oci-js-standard-host oci-js-standard-execution
kubectl --context rancher-desktop -n oci-js-standard-host get deployment,pod
kubectl --context rancher-desktop -n oci-js-standard-execution get \
  serviceaccount,resourcequota,limitrange,networkpolicy
kubectl --context rancher-desktop get validatingadmissionpolicy \
  oci-js-standard-execution-pods-v1
```

Wait for both the trusted host and reconciler Deployments to be available. A
successful host startup also performs service-account/RBAC checks and server
dry-runs of the approved runner-pod contract before accepting MCP stdio.

For local code and manifest checks, run:

```sh
npm run check:kubernetes-manifests
npm run kubectl:dry-run:kubernetes
```

These are static/client-side checks; they do not prove effective cluster RBAC,
admission, CNI enforcement, or runtime containment.

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
