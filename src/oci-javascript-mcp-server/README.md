# OCI JavaScript MCP Server

`oci-javascript-mcp-server` runs agent-authored JavaScript that calls OCI
through a trusted host bridge. The sandbox receives an SDK-like `oci` binding,
but never receives OCI credentials, the real SDK, Node built-ins, filesystem
access, environment variables, or a network API.

> **Security:** Podman remains the compatibility default and shares the host
> kernel. The optional `kubernetes` provider has explicit `local-development`,
> `in-cluster`, and `kata-in-cluster` profiles. The first two provide container
> isolation only. The Kata profile is a proof of concept, not proof of a VM
> boundary; real-provider evidence and a current security review remain required.

## Quick start

Requires Node.js 26 or newer, rootless Podman, and an OCI SDK configuration. A
native build toolchain is also needed if `isolated-vm` cannot use its packaged
prebuilt binary. The repository pins Node 26.8.1, npm 11.12.1, and Moon 2.5.2.

From this directory:

```bash
proto install
moon run oci-javascript-mcp-server:compile
moon run oci-javascript-mcp-server:runner-build
npm start
```

The server uses MCP over stdio. For an MCP client, invoke Node directly so npm
lifecycle output cannot interfere with JSON-RPC:

```json
{
  "mcpServers": {
    "oci-javascript-mcp-server": {
      "type": "stdio",
      "command": "node",
      "args": [
        "--no-node-snapshot",
        "--experimental-strip-types",
        "<repo>/src/oci-javascript-mcp-server/src/server.ts"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "<profile_name>"
      }
    }
  }
}
```

Set `OCI_CONFIG_FILE` or `OCI_CONFIG_PROFILE` when the default OCI configuration
is not appropriate. The default runner image is
`localhost/oci-javascript-mcp-runner:dev`; override it with
`OCI_JAVASCRIPT_PODMAN_IMAGE`. `OCI_JAVASCRIPT_PODMAN_CLI` may specify a
nonstandard Podman executable path. The provider invokes the CLI directly with
fixed arguments and never through a shell. There is no process fallback.

`OCI_JAVASCRIPT_ISOLATION_PROVIDER` accepts exactly `podman` or `kubernetes`;
omission retains Podman. Kubernetes additionally requires
`OCI_JAVASCRIPT_KUBERNETES_PROFILE` set to exactly `local-development`,
`in-cluster`, or `kata-in-cluster`. Selection is trusted startup configuration,
never MCP input, and failure never falls back to another provider, profile, or
credential source. See the [Kubernetes profile guide](docs/kubernetes-isolation-profiles.md)
for the complete provider matrix, configuration, preflight behavior, local
cluster workflow, and versioned assets. Kata-specific deployment evidence is in
the [Kata POC guide](docs/kata-kubernetes-poc.md).
For the verified Rancher Desktop `in-cluster` workflow, including image pinning,
host-only OCI Secret synchronization, and Inspector connection, see the
[local Kubernetes in-cluster setup guide](docs/kubernetes-local-in-cluster-setup.md).

After publication, install into a project with automatic lifecycle scripts
disabled, then explicitly prepare the reviewed native addon:

```bash
npm install --ignore-scripts oci-javascript-mcp-server
node --no-node-snapshot node_modules/oci-javascript-mcp-server/scripts/setup-native.mjs
```

Configure the installed `oci-javascript-mcp-server` command for your MCP client.
The setup script checks the installed addon's identity, exact 7.0.0 version, and
reviewed install command before running only that command with pre/post hooks
disabled, then verifies that the addon loads. This package pins `isolated-vm`
to 7.0.0 so consumers receive the reviewed version. Dependency overrides or
changes to its install script require another review. A published package's
metadata and repository `.npmrc` do not control arbitrary consumer installs;
consumers must supply `--ignore-scripts` themselves. Native setup uses npm from
the caller's PATH and requires Node 26 or newer.

## Tools

### `run_javascript`

Runs `code` with an optional timeout of 1–120 seconds (default 30). The final
expression becomes `result`; logs, errors, exit status, and timeout state are
returned separately. Every OCI call must be awaited; the host aborts outstanding
calls and rejects a run that finishes while OCI work is still pending.

The timeout is the absolute execution deadline. When execution finishes or that
deadline expires, the host stops accepting OCI bridge work and aborts the run,
then terminates the provider and drains a snapshot of pending OCI RPC promises
concurrently. Both use one provider-specific, host-clamped cleanup tail; their
allowances never accumulate serially. A never-settling OCI request therefore
cannot delay the MCP result beyond the execution deadline plus that one tail.
Provider cleanup failure returns `isolation provider cleanup failed` and takes
precedence over every earlier outcome. If provider cleanup succeeds but pending
OCI work does not settle within the tail, the result is `OCI cleanup did not
complete`. Only an otherwise successful run whose pending work settles reports
`JavaScript completed with unawaited OCI calls`. Late OCI completion remains
observed internally and cannot change or republish the finalized result.

The runner accepts one protobuf gRPC session and one execution. The host stops
accepting runner messages after a valid result and waits for final gRPC `OK`
status before accepting success. It requires nonzero protobuf `uint32` RPC IDs,
but does not enforce their uniqueness against a compromised runner. Message
size, source/log/result size, request size, OCI call count and concurrency, and
the absolute deadline are bounded; a stalled reply writer fails on backpressure.
Cumulative traffic accounting and semantic output policy remain review gaps.

Use the injected binding like the OCI JavaScript SDK:

```js
const config = await oci.config();
const response = await oci.identity.IdentityClient.listRegionSubscriptions({
  tenancyId: config.tenancyId
});
response.items.map(item => item.regionName);
```

Static operations, constructed clients, per-client `region`, SDK pagination
fields, and shallow `Object.keys` reflection are supported. Only API operations
backed by SDK request types are exposed; arbitrary endpoints, credentials,
signers, retry configuration, pagination helpers, and local utilities are not.
Trusted-host OCI clients use the SDK no-retry policy, an explicitly disabled
client circuit breaker, and the run's abort signal. Guest code cannot override
retry or circuit-breaker policy; after a transient failure, issue a new complete
execution when appropriate.

Structured results are limited to 1 MiB by default. Set
`OCI_JAVASCRIPT_MAX_RESULT_BYTES` to a positive byte count to change the limit;
the bounded bridge clamps it below the 2 MiB JSON payload ceiling.

### `discover_oci`

Inspects available OCI services, clients, operations, and request/model fields.
Use it when a normal JavaScript attempt fails because the SDK shape is unclear,
not as the default way to call OCI.

## Architecture

The [formal architecture and isolation design](docs/architecture-and-isolation-design.md)
consolidates the MCP server, OCI broker, provider contract, Kubernetes engine,
Kata profile layer, trust model, evidence gates, and open design decisions.

```text
MCP client
  -> trusted stdio server
       -> OCI broker -> OCI SDK + host credentials -> OCI APIs
       -> selected isolation provider
            -> Podman: private network + loopback port, or
            -> Kubernetes: fresh pod + exec bootstrap + loopback port-forward
                 -> standard runtime (local/in-cluster), or reviewed Kata RuntimeClass
            -> locked-down, credential-free runner
                 -> fresh Node worker
                      -> isolated-vm V8 isolate
                           -> user JavaScript + injected oci proxy
                 <-> bounded gRPC session <-> OCI broker
```

The host owns credentials, OCI clients, request validation, deadlines, budgets,
bounded result encoding, and teardown. The container and isolate
receive reflection metadata and a narrow RPC bridge, but no credential or
signer. The `IsolationProvider` seam keeps these host controls independent of
the runtime backend.

The host's gRPC boundary decodes and validates runner data once; the coordinator
consumes typed results without re-serializing them. gRPC owns the session and
channel, while the isolation provider owns process/container lifecycle and cleanup.

The internal gRPC contract is defined in `proto/runner.proto`. The v4 `Session`
uses direction-specific protobuf messages for execution, OCI RPCs, and a final
result containing stdout/stderr. gRPC supplies readiness, deadlines, cancellation,
and protocol-failure status. The runner derives its execution budget from the
session deadline; the host retains its overall execution watchdog.
Source code and log text use bounded UTF-16LE bytes,
preserving JavaScript code units including unpaired surrogates; dynamic OCI data retains
bounded UTF-8 JSON and structural validation. Protobuf does not replace
execution budgets, protocol-state checks, or OCI authorization.

The v4 endpoint is incompatible with earlier endpoints.
Rebuild the runner image when updating the host; no fallback or execution replay
is provided. The public MCP tools and response fields are unchanged.

## Security model

- Every call receives a fresh locked-down provider boundary, worker, and isolate.
- Podman uses a fresh internal network with no external route and publishes only
  the runner's gRPC port to host loopback. The container also has a read-only
  root filesystem, no capabilities, `no-new-privileges`, a non-root user, and
  CPU, memory, process, file, and temporary-filesystem limits.
- Each execution gets fresh mutual-TLS identities. The runner receives its
  server key and the host's public certificate, never the host's private key.
- Kubernetes uses exec only for the TLS bootstrap and runner lifecycle, then
  carries the same mTLS gRPC session over one host-loopback `pods/portforward`
  connection. It creates no Service and declares no container port.
- Sandbox code cannot import Node modules or directly access files or networks.
- Credentials, signers, SDK clients, and HTTPS remain in the trusted host.
- The host validates each request and enforces deadlines, message and result
  sizes, call counts, concurrency, cancellation, and teardown.
- OCI failures expose only status, service code, operation, and request identifiers;
  raw SDK details and runner-process stderr are not returned.

The nested `isolated-vm` boundary reduces exposure inside the runner, but an
`isolated-vm`, V8, native-addon, container-runtime, or shared-kernel compromise
can cross a shared-kernel container boundary. Deployments requiring a VM-grade
boundary must supply that boundary outside the MCP server and retain
conservative mounts and network policy.

Every Kubernetes profile uses the same fixed non-root security context, no token
or service links, no host namespace or owner reference, and one bounded
memory-backed `/tmp`. CPU, memory, and ephemeral-storage requests must equal
their limits and stay within the documented reviewed ranges; `/tmp` must also
stay within its documented range. The example admission policies use CEL
quantity bounds so every documented value is accepted without a synchronized
policy edit. In-cluster profiles require digest-pinned
images, separate namespaces, fail-closed exact RBAC checks including trusted-host
`pods/exec` and `pods/portforward`, rejection of the
reviewed admission variants, and an independent cleanup-only reconciler. Only
`kata-in-cluster` adds a preflighted RuntimeClass/handler. Kubernetes exec and
port-forward errors remain trusted diagnostics and are never copied into MCP result
fields.

Cluster-scoped preflight reads name exactly the configured execution Namespace
and, for Kata, RuntimeClass; the example ClusterRoles apply matching
`resourceNames`, while generated pod operations remain namespace-scoped.
Admission evidence is reported only as `reviewed-variants-rejected` or
`unverified`, and the exact deployed policy revision remains explicitly
unverified. During cleanup, the gRPC session, loopback tunnel, exec runner, and
zero-grace pod deletion plus NotFound confirmation share one absolute cleanup
deadline; an unconfirmed transport close or deletion returns `isolation provider cleanup
failed`. Reconciliation bounds each expired candidate to five seconds,
continues after candidate failures, and emits only aggregate success/failure
counts so later intervals continue without exposing pod names.

## Development

```bash
moon run oci-javascript-mcp-server:compile # generate bindings and compile the npm entry point
moon run oci-javascript-mcp-server:test   # unit and MCP stdio integration tests; all four coverage metrics >=90%
moon run oci-javascript-mcp-server:check  # TypeScript validation
moon run oci-javascript-mcp-server:build  # create the npm package tarball
moon run oci-javascript-mcp-server:k8s-build # build the Kubernetes runner and host Docker images
moon run oci-javascript-mcp-server:container-smoke # opt-in builder context and offline image startup checks
moon run oci-javascript-mcp-server:check-kubernetes-manifests # RBAC/admission manifests
moon run oci-javascript-mcp-server:kubectl-dry-run-kubernetes # optional local kubectl check
```

Moon installs and deduplicates dependencies before running package tasks. The
server-local `.npmrc` disables automatic lifecycle scripts before those actions
run. Compile depends on `native-setup`, which explicitly activates only the
reviewed `isolated-vm` 7.0.0 install command and verifies it loads. Image builds
perform that setup inside their compiler-equipped dependency stages; building
an image does not require preparing the native addon on the host. For a direct
locked install, use `npm ci --ignore-scripts`, followed by
`moon run oci-javascript-mcp-server:native-setup` before loading the addon.
Container installs, pruning, packaging, and publishing also pass
`--ignore-scripts` explicitly. Buf's postinstall and protobufjs's version-warning
postinstall stay disabled: code generation uses Buf 1.73.0's installed optional
platform binary. Keep optional dependencies enabled; a missing binary makes
the CLI fail instead of running Buf's secondary npm-install fallback.
Run `k8s-build` before `container-smoke`, which requires Docker and the built
images. Set `OCI_JAVASCRIPT_CONTAINER_BUILDER=podman` to check images built with
Podman; `OCI_JAVASCRIPT_TEST_HOST_IMAGE` and `OCI_JAVASCRIPT_TEST_RUNNER_IMAGE`
override the default `:dev` tags. The smoke checks start the host's default CMD
and reconciler and bootstrap the runner with networking disabled, synthetic TLS,
and no mounted credentials or cluster access. They are skipped by the normal
test task.
Publish through the manually dispatched `Publish package` GitHub Actions
workflow, selecting the `npm` registry and `oci-javascript-mcp-server` project.
It builds and tests before running Moon's publish task with npm credentials.

Kubernetes tests use injectable fake APIs and gRPC transports across all three
profiles. They validate configuration, credential-factory selection, pod shape,
protobuf/mTLS exchange, startup admission probes, lifecycle races, cancellation,
cleanup, reconciliation, and provider-compatible MCP results. The opt-in local
cluster harness adds real standard-runtime lifecycle evidence; it never claims
Kata, CRI, CNI, or guest-kernel evidence. Offline resource-range fixtures and
client-side dry runs do not establish server-side CEL or admission enforcement.
When both example admission policies are already applied to a configured test
cluster, `OCI_JAVASCRIPT_RUN_REAL_KUBERNETES_ADMISSION_TESTS=true` makes the
test suite require their observed generations to have no CEL type-checking
warnings; otherwise that real-cluster-only evidence is deliberately skipped.

Commit `proto/runner.proto`, `buf.gen.yaml`, and the dependency lockfile, not
`src/generated/` or `dist/`. Tests, type checks, and npm packaging depend on
Moon's compile task, which generates the codecs and gRPC bindings using the
pinned Buf CLI and `ts-proto` dependencies. Run the compile task after schema
changes before launching the server directly; no separate `protoc` installation
is needed.

The published entry point runs compiled JavaScript from `dist/`, including the
generated bindings; Node does not strip TypeScript under `node_modules`.
The container generates its bindings in its build stage and copies them into
the final image without the generators or schema files. Neither runtime performs
schema loading or code generation.
Wire-format fixtures and gRPC integration tests exercise the generated bindings;
a packaging test starts the tarball under `node_modules` and executes an MCP call.
Never reuse field numbers; reserve removed fields and use a new service version
for incompatible semantics.

Tests use a fake Podman control plane to validate the exact hardened CLI
arguments and exercise the same mTLS gRPC session used by the real runner
without requiring Podman in CI. They test this server's command construction,
not Podman itself.

Generated protobuf codecs, the sandbox prelude, and type-only declarations are
excluded from source-line instrumentation; wire-format and integration tests
exercise their behavior.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown in
[LICENSE.txt](LICENSE.txt).
