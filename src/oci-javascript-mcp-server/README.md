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

## Tools

### `run_javascript`

Runs a complete JavaScript program body with top-level `await`, an injected `oci`
namespace, and an explicit `return` for the result. Final-expression inference
also remains supported. Source is limited to 1 MiB of UTF-8. The optional
`timeout` is 1–120 seconds (default 30), covering startup, JavaScript, and OCI
calls; the existing bounded cleanup phases can extend response time after the
deadline. Every OCI call must be awaited; the host aborts outstanding calls and
rejects a run that finishes while OCI work is still pending.

Execute directly when the SDK shape is known. When it is unclear, discover only
the necessary service/client/operation depth, then execute. Requests use
camelCase fields. Host IAM permissions govern operations, which may read,
create, update, or delete OCI resources. Tool annotations describe possible
effects and do not enforce authorization.

Per-call OCI clients retain the execution's abort signal and disable SDK retries
and circuit breakers. Each operation makes one attempt so SDK retry delays cannot
outlive the execution budget and service errors return promptly.

Use the injected binding like the OCI JavaScript SDK. This example requires a
configured identity with tenancy context and permission for the operation:

```js
const config = await oci.config();
const client = new oci.identity.IdentityClient();
const response = await client.listRegionSubscriptions({ tenancyId: config.tenancyId });
return response.items.map(item => item.regionName);
```

Static operations, constructed clients, per-client `region`, SDK pagination
fields, and shallow `Object.keys` reflection are supported. Only API operations
backed by SDK request types are exposed; arbitrary endpoints, credentials,
signers, retry configuration, pagination helpers, and local utilities are not.
For a specific region, use
`new oci.identity.IdentityClient({ region: "us-ashburn-1" })`.
`region` is the only supported client option. The sandbox has no imports, Node
built-ins, credentials, direct filesystem/network access, process state, or host
environment access.

Every completed execution returns the same JSON object as `structuredContent`
and serialized text, conforming to its advertised object-root output schema:

| Field | Meaning |
| --- | --- |
| `result` | Any JSON-compatible result, including null, arrays, primitives, and existing tagged wire objects |
| `error` | Null, or a sanitized error object with a nonempty `message` and optional OCI details |
| `stdout`, `stderr` | Captured log strings |
| `exit_code` | Integer; zero on success |
| `timed_out` | Boolean deadline indicator |

All six fields are required. A non-null `error`, nonzero `exit_code`, or true
`timed_out` sets outer MCP `isError: true` without discarding the envelope.
Sanitized OCI status, service code, request ID, and operation details remain
available in `error`. Invalid inputs, oversized source, concurrency admission
failures, and discovery errors are tool errors with actionable text and
`isError: true`; they do not invent an execution envelope.

Scripts are not transactions. A mutation can complete before a later script,
timeout, output-limit, or cleanup failure. Inspect resource state before retrying
mutations and never automatically replay an entire failed script. A one-attempt
policy does not prove absence of side effects. If an operation supports
`opcRetryToken`, preserve it for a retry of the same logical request under that
operation's semantics; token support is not universal and no rollback is provided.

Structured results are limited to 1 MiB by default. Set
`OCI_JAVASCRIPT_MAX_RESULT_BYTES` to a positive byte count to change the limit;
the bounded bridge clamps it below the 2 MiB frame ceiling.

The host bounds each full OCI response before guest code sees it. Reduce page
size or narrow the request if that response exceeds its limit: projecting fields
in JavaScript cannot repair a rejected host response. Projection and aggregation
control the separate final-result size. Finite operator-configured call and
concurrency budgets also apply, and `oci.config()` consumes a bridge call.

Use one bounded page per execution when continuing a larger listing:

```js
const config = await oci.config();
const region = "us-ashburn-1";
const page = undefined; // Replace with the previous nextPage for a continuation.
const client = new oci.identity.IdentityClient({ region });
const response = await client.listCompartments({
  compartmentId: config.tenancyId,
  limit: 25,
  sortBy: "NAME",
  sortOrder: "ASC",
  ...(page === undefined ? {} : { page })
});
return {
  items: response.items.map(item => ({ id: item.id, name: item.name })),
  nextPage: response.opcNextPage ?? null
};
```

Choose the intended region before the first run. Each execution has fresh
variables and clients; supply the previous `nextPage` explicitly and preserve
region, compartment, filters, and sorting. An empty page is not complete when a
token remains; return null only when no next token exists. Prefer sequential
bounded pages. Pagination across calls is not a snapshot of resources changing
concurrently.

### `discover_oci`

Inspects available OCI services, clients, operations, and request/model fields.
Use it when the SDK shape is unclear, including after an SDK shape error.

| Arguments | Result `type` | Required result fields |
| --- | --- | --- |
| None | `index` | `type`, `services` |
| `service` | `service` | `type`, `service`, `clients` |
| `service`, `client` | `client` | `type`, `service`, `client`, `operations` |
| `service`, `client`, `operation` | `operation` | `type`, `service`, `client`, `operation`, `requestShape` |

Identifiers are case-sensitive strings matching `^[A-Za-z][A-Za-z0-9_]*$`, for
example `identity`, `IdentityClient`, and `listCompartments`. Empty identifiers,
whitespace, malformed syntax, wrong types, or children without parents are
rejected before host discovery. Identifiers are not trimmed, normalized, or
fuzzily matched. Unknown names or incorrect case produce host discovery errors.

The output schema advertises an object with `type` and optional depth fields;
the host result is validated for its required variant fields before success is
returned. Listing fields are string arrays; identities and `requestShape` are
strings. Optional extracted details include `requestType`, `requestFields`
(`name`, `required`, `type`, optional `modelRefs`), `models` with field lists,
`exampleRequest`, and `responseShape` with body, request ID, and pagination hints.
Additional existing data is preserved.

Discovery inspects installed declarations on the host without starting an
isolation provider or making OCI network calls. It does not grant IAM permission
or guarantee regional availability. Parsing is best-effort: model expansion is
bounded, inline types may be incomplete, references can remain unresolved, and
enum or conditional constraints can be missing. `exampleRequest` is a placeholder
skeleton, not a complete validated API request. Missing detail does not prove
the absence of an API requirement.

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

[src/server.ts](src/server.ts) owns MCP registration, stdio startup, and tool-call
orchestration, including provider selection, concurrency admission, and forwarding
cancellation to the runtime. [src/tool-contracts.ts](src/tool-contracts.ts) owns
server instructions, tool metadata, input/output schemas, discovery validation,
and MCP result serialization. The contract module does not start the server when
imported, so focused tests can exercise these contracts without connecting a
stdio transport or starting an execution provider.

For contract changes, use [test/tool-contracts.test.ts](test/tool-contracts.test.ts)
for direct schema, validation, and result tests, together with
[test/server.test.ts](test/server.test.ts) to verify the actual MCP initialization,
advertised catalog, and tool-call responses. The direct tests isolate contract
edge cases; the stdio integration tests check their registration and behavior at
the client boundary.

```bash
moon run oci-javascript-mcp-server:compile # generate bindings and compile the npm entry point
moon run oci-javascript-mcp-server:test   # unit and MCP stdio integration tests; 90% line minimum
moon run oci-javascript-mcp-server:check  # TypeScript validation
moon run oci-javascript-mcp-server:build  # create the npm package tarball
```

Moon installs the locked npm dependencies before running package tasks.
Publish through the manually dispatched `Publish package` GitHub Actions
workflow, selecting the `npm` registry and `oci-javascript-mcp-server` project.
It builds and tests before running Moon's publish task with npm credentials.

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
