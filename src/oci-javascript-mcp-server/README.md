# OCI JavaScript MCP Server

`oci-javascript-mcp-server` runs agent-authored JavaScript that calls OCI
through a trusted host bridge. The sandbox receives an SDK-like `oci` binding,
but never receives OCI credentials, the real SDK, Node built-ins, filesystem
access, environment variables, or a network API.

> **Security:** Podman is the only implemented isolation provider. On Linux, a
> normal Podman container shares the host kernel and is not a VM boundary. The
> deployment is responsible for selecting a Podman backend and surrounding
> controls appropriate to its threat model; the MCP server does not perform
> provider admission.

## Quick start

Requires Node.js 26 or newer, rootless Podman, and an OCI SDK configuration. A
native build toolchain is also needed when installing `isolated-vm` on the host.

From this directory:

```bash
npm install
npm run proto:generate
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

```text
MCP client
  -> trusted stdio server
       -> OCI broker -> OCI SDK + host credentials -> OCI APIs
       -> Podman isolation provider
            -> private no-egress network + localhost mTLS gRPC
            -> locked-down, credential-free container
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

- Every call receives a fresh locked-down container, worker, and isolate.
- Podman uses a fresh internal network with no external route and publishes only
  the runner's gRPC port to host loopback. The container also has a read-only
  root filesystem, no capabilities, `no-new-privileges`, a non-root user, and
  CPU, memory, process, file, and temporary-filesystem limits.
- Each execution gets fresh mutual-TLS identities. The runner receives its
  server key and the host's public certificate, never the host's private key.
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

## Development

```bash
npm run build    # generate bindings and compile the npm entry point
npm test         # unit and MCP stdio integration tests
npm run coverage # subprocess-aware coverage; 90% line minimum
npm run check    # TypeScript validation
npm run ci       # generated bindings, coverage, types, and package verification
```

Commit `proto/runner.proto`, `buf.gen.yaml`, and the dependency lockfile, not
`src/generated/` or `dist/`. Tests, type checks, and npm packaging regenerate the
codecs and gRPC bindings using the pinned Buf CLI and `ts-proto` development
dependencies. Run `npm run proto:generate` after schema changes before launching
the server directly; no separate `protoc` installation is needed.

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
