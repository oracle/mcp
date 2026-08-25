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

Requires Node.js 26 or newer, Podman, and an OCI SDK configuration. A native
build toolchain is also needed when installing `isolated-vm` on the host.

From this directory:

```bash
npm install
npm run podman:build
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

After publication, install and configure the `oci-javascript-mcp-server`
command instead of invoking `node` directly.

## Tools

### `run_javascript`

Runs `code` with an optional timeout of 1–120 seconds (default 30). The final
expression becomes `result`; logs, errors, exit status, and timeout state are
returned separately. Every OCI call must be awaited; the host aborts outstanding
calls and rejects a run that finishes while OCI work is still pending.

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

Structured results are limited to 1 MiB by default. Set
`OCI_JAVASCRIPT_MAX_RESULT_BYTES` to a positive byte count to change the limit;
the bounded bridge clamps it below the 2 MiB frame ceiling.

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
            -> Podman container (compatibility default), or fresh Kubernetes pod
                 -> standard runtime (local/in-cluster), or reviewed Kata RuntimeClass
            -> locked-down, credential-free runner
                 -> fresh Node worker
                      -> isolated-vm V8 isolate
                           -> user JavaScript + injected oci proxy
                 <-> bounded framed pipe <-> OCI broker
```

The host owns credentials, OCI clients, request validation, deadlines, budgets,
bounded result encoding, and teardown. The container and isolate
receive reflection metadata and a narrow RPC bridge, but no credential or
signer. The `IsolationProvider` seam keeps these host controls independent of
the runtime backend.

## Security model

- Every call receives a fresh locked-down provider boundary, worker, and isolate.
- Podman runs with no network, a read-only root filesystem, no capabilities,
  `no-new-privileges`, a non-root user, and CPU, memory, process, file, and
  temporary-filesystem limits.
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

Every Kubernetes profile uses the same fixed non-root security context and
resources, no token or service links, no host namespace or owner reference, and
one bounded memory-backed `/tmp`. In-cluster profiles require digest-pinned
images, separate namespaces, fail-closed RBAC/admission preflight, and an
independent cleanup-only reconciler. Only `kata-in-cluster` adds a preflighted
RuntimeClass/handler. Kubernetes and raw exec errors remain trusted diagnostics
and are never copied into MCP result fields.

## Development

```bash
npm test         # unit and MCP stdio integration tests
npm run coverage # subprocess-aware coverage; 90% line minimum
npm run check    # TypeScript validation
npm run check:kubernetes-manifests # standard/Kata manifest, admission, and RBAC checks
npm run kubectl:dry-run:kubernetes # client-side dry run when kubectl is installed
npm run ci       # coverage, type checking, and package verification
```

Tests use a fake Podman control plane to validate the exact hardened CLI
arguments and exercise the framed worker protocol without requiring Podman in
CI. They test this server's command construction, not Podman itself.

Kubernetes tests use injectable fake APIs and exec channels across all three
profiles. They validate configuration, credential-factory selection, pod shape,
hostile framing, startup admission probes, lifecycle races, cancellation,
cleanup, reconciliation, and provider-compatible MCP results. The opt-in local
cluster harness adds real standard-runtime lifecycle evidence; it never claims
Kata, CRI, CNI, or guest-kernel evidence.

The generated sandbox prelude and type-only declarations are excluded from
source-line instrumentation; their behavior is exercised through integration
tests.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown in
[LICENSE.txt](LICENSE.txt).
