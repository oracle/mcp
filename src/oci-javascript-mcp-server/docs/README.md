# OCI JavaScript documentation baseline

This source-checkout index selects the documentation baseline for branch commit
`b0ad446`, reviewed on 2026-10-09 with the local worktree. It describes current
implementation and supported procedures; design requirements, prior execution
reports and deployment evidence retain their own standing. No runtime, OCI,
container or cluster checks were executed during this documentation pass.

## Read by task

| Task | Maintained explanation | Implementation and check definitions |
| --- | --- | --- |
| Invoke tools or understand results/errors | [README tools](../README.md#tools), [public behavior and limits](architecture-and-isolation-design.md#72-public-mcp-behavior) | [Server](../src/server.ts), [server tests](../test/server.test.ts) |
| Trace credentials, SDK exposure and pagination | [Host identity and SDK exposure](architecture-and-isolation-design.md#73-host-identity-and-sdk-exposure) | [OCI host](../src/oci-host.ts), [JSON decoder](../src/json.ts), [host tests](../test/oci-host.test.ts) |
| Change protocol, deadlines, cancellation or cleanup | [Architecture](architecture-and-isolation-design.md#8-provider-neutral-worker-protocol), [failure contract](architecture-and-isolation-design.md#13-failure-handling-and-public-contract) | [Schema](../proto/runner.proto), [gRPC execution](../src/isolation/grpc-execution.ts), [coordinator](../src/sandbox.ts), [gRPC tests](../test/grpc.test.ts), [sandbox tests](../test/sandbox.test.ts) |
| Select/configure a provider or Kubernetes profile | [Profile guide](kubernetes-isolation-profiles.md) | [Provider factory](../src/isolation/provider-factory.ts), [strict config](../src/isolation/kubernetes-config.ts), [configuration tests](../test/kubernetes-config.test.ts), [profile tests](../test/kubernetes-profiles.test.ts) |
| Assess pod policy, startup, reconciliation or Kata | [Kubernetes design](architecture-and-isolation-design.md#10-kubernetes-execution-engine), [Kata POC](kata-kubernetes-poc.md) | [Pod builder](../src/isolation/kubernetes-pod.ts), [provider](../src/isolation/kubernetes.ts), [reconciler](../src/isolation/kubernetes-reconciler.ts), [provider tests](../test/kata-provider.test.ts), [reconciler tests](../test/kata-reconciler.test.ts) |
| Follow the local in-cluster procedure | [Local setup](kubernetes-local-in-cluster-setup.md) | [Local manifest](../examples/kubernetes/v1/local-in-cluster.yaml), [Secret helper](../scripts/sync-oci-session-secret.py), [helper tests](../test/sync-oci-session-secret.test.ts) |
| Build, test, install or package | [README development](../README.md#development), [component guide](../AGENTS.md#tests-and-validation) | [Moon tasks](../moon.yml), [manifest](../package.json), [native setup](../scripts/setup-native.mjs), [installation tests](../test/install-policy.test.ts), [packaging test](../test/packaging.test.ts) |

Apply [root requirements](../../../AGENTS.md) and the [component guide](../AGENTS.md)
when changing this server. The [shared validation map](../../../docs/agent-development.md#validation-map)
owns repository procedures. Python Common authentication is not this Node SDK
path's implementation; shared requirements remain with their owning sources.

## Known differences and evidence limits

- There is no application tool-call queue. Both tools share the active-call
  limit (default four) and reject overload.
- The gRPC host requires nonzero RPC IDs and bounds frames/calls, but does not
  enforce unique IDs. A general cumulative traffic budget and combined
  result/error byte budget from older designs are not current controls.
- `json.ts` decodes known tags with coercion/defaults; it does not implement the
  exact tag schemas or reserved-key escaped-object representation described by
  some historical contracts. Broker request validation rejects a top-level
  `retryConfiguration`; it is not complete SDK request-schema validation or
  comprehensive recursive transport-control filtering.
- The lock resolves `isolated-vm` 7.0.0; the manifest allows `^7.0.0` while native
  setup accepts exactly 7.0.0 and its reviewed command. Fresh consumer resolution
  can conflict with that gate. Dependency policy remains a maintainer decision.
- OCI access uses the configured host principal. Per-caller authorization,
  semantic response policy and HTTP/multi-user identity are unresolved.
- Kubernetes NotFound confirms API-object deletion, not process termination on
  an unreachable node. Admission probes cover reviewed variants, not the exact
  policy revision or every admission path. CNI, CRI, Kata guest boundary, image
  provenance and real resource enforcement require target-environment evidence.
- Root's subprocess policy and the existing Podman backend remain a documented
  conflict; this baseline grants no exception.
- The prior local Rancher Desktop and POC claims were not reproduced. The
  previously referenced security-review rubric is absent from this worktree;
  this baseline does not establish a current security approval record.

Verification for this documentation pass resolved all maintained local links
and heading anchors, checked Moon command references against task definitions,
and confirmed implementation/build inputs were unchanged. Runtime tests and
deployment checks were not run. This index is source-checkout documentation;
the package's product-doc allowlist ships the architecture and three deployment
guides.
