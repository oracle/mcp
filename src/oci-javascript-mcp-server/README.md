# OCI JavaScript MCP Server

`oci-javascript-mcp-server` is a stdio MCP server that runs complete JavaScript
programs with an SDK-shaped OCI facade. OCI credentials, SDK clients, signing,
network access, request authorization, deadlines, and byte budgets remain in a
trusted host broker.

This repository version is a locally testable vertical slice of a VM-oriented
architecture. For Apple-silicon development machines, the preferred
`apple-container` provider runs every execution in a fresh lightweight Linux VM.
An **insecure local process provider** remains available for development and CI.
Neither provider is admitted in production.

## Architecture and trust boundary

```text
MCP client
  -> trusted stdio MCP host
       -> host-owned execution policy
       -> bounded, versioned JSON broker channel
       -> OCI SDK + host credentials + OCI network
       -> isolation provider
            -> fresh Apple container VM, or ordinary Node.js process
                 -> Node.js runner
                      -> vm.Context
                      -> user JavaScript + narrow oci facade
```

The provider creates the runner and gives it one pre-opened, execution-bound
channel. No bearer token is placed in the runner. Both included providers map
that channel to stdin/stdout pipes. OCI credentials, configuration files, SDK
clients, and the MCP transport remain outside the runner.

Node's `vm.Context` only shapes the JavaScript API. It is **not** a secure
sandbox for hostile code. A context escape is treated as compromise of the
whole runner, including its memory and open descriptors. The host therefore
validates and authorizes every raw channel message as hostile input.

## Requirements and installation

Node.js 26 or newer is required.

```sh
cd src/oci-javascript-mcp-server
npm install
```

No `isolated-vm` or other native V8 isolation dependency is used.

## Run locally with an Apple container VM

This is the recommended development configuration on Apple silicon. Apple's
[`container`](https://github.com/apple/container) requires macOS 26 or newer.
Install its latest signed package from the
[`container` releases page](https://github.com/apple/container/releases/latest).
The package installs the CLI at `/usr/local/bin/container`. From the repository
root, prepare and verify the local runtime:

```sh
cd src/oci-javascript-mcp-server
/usr/local/bin/container --version
/usr/local/bin/container system start
/usr/local/bin/container system status
npm run apple-container:build
/usr/local/bin/container network create --internal oci-javascript-mcp-internal
```

The image build is required after runner-image changes. The network creation
command is a one-time setup step; do not repeat it if the network already
exists. Then start the MCP server directly:

```sh
OCI_JAVASCRIPT_MODE=development \
OCI_JAVASCRIPT_ISOLATION_PROVIDER=apple-container \
OCI_JAVASCRIPT_APPLE_CONTAINER_CLI=/usr/local/bin/container \
npm start
```

When using this server through Codex, add the equivalent STDIO entry to
`~/.codex/config.toml`, restart Codex, and use `/mcp` to confirm that the server
connected.

### Shut down

If the MCP server was started directly with `npm start`, press `Ctrl-C` in that
terminal. Active execution containers are removed automatically when execution
completes or is cancelled.

After the MCP server has exited and no other workloads need Apple's container
runtime, stop the subsystem:

```sh
/usr/local/bin/container system stop
```

Every execution launches a fresh, named VM using the locally built
`localhost/oci-javascript-mcp-runner:dev` image. The loopback-qualified name
also prevents a missing development image from resolving to a similarly named
public registry repository. The provider mounts no host paths, passes no host
credentials or OCI environment variables, runs as UID/GID 65532, uses a
read-only root filesystem, drops all Linux capabilities, disables DNS, and
limits the guest to one CPU, 512 MiB of memory, and 64 open files. Completion,
cancellation, protocol failure, and timeout all trigger forced cleanup by
execution name.

The default image and internal network can be overridden when necessary:

```sh
OCI_JAVASCRIPT_APPLE_CONTAINER_IMAGE=registry.example/runner@sha256:... \
OCI_JAVASCRIPT_APPLE_CONTAINER_NETWORK=my-internal-network
```

The image reference should be pinned by digest outside local iteration. The
included `Containerfile` pins its Node base image by multi-platform digest.

Apple's [command reference](https://github.com/apple/container/blob/main/docs/command-reference.md)
defines an `--internal` network as host-only, not as the absence of a network
device. A compromised guest can therefore still create sockets and probe
reachable host or peer services. This limitation is represented by
`networkCreationBlocked: false`; the provider is stronger than a host process
but remains development-only and is rejected in production.

## Insecure process fallback

The insecure process provider requires both development mode and explicit
opt-in:

```sh
OCI_JAVASCRIPT_MODE=development \
OCI_JAVASCRIPT_ALLOW_INSECURE_PROCESS=1 \
npm start
```

The host reads OCI credentials using the standard JavaScript SDK configuration.
Select a non-default local profile when needed:

```sh
OCI_CONFIG_PROFILE=MY_PROFILE \
OCI_JAVASCRIPT_MODE=development \
OCI_JAVASCRIPT_ALLOW_INSECURE_PROCESS=1 \
npm start
```

The development policy is read-only by default. Mutating OCI operations require
a deliberate additional local opt-in:

```sh
OCI_JAVASCRIPT_ALLOW_MUTATIONS=1
```

That setting does not make either included provider production-eligible.

## MCP client configuration

Use `node` directly so npm lifecycle output cannot interfere with stdio MCP
messages:

```json
{
  "mcpServers": {
    "oci-javascript-mcp-server": {
      "type": "stdio",
      "command": "node",
      "args": [
        "--experimental-strip-types",
        "/absolute/path/to/mcp/src/oci-javascript-mcp-server/src/server.ts"
      ],
      "env": {
        "OCI_JAVASCRIPT_MODE": "development",
        "OCI_JAVASCRIPT_ISOLATION_PROVIDER": "apple-container",
        "OCI_CONFIG_PROFILE": "DEFAULT"
      }
    }
  }
}
```

## MCP tools

### `run_javascript`

Inputs:

- `code`: required JavaScript source string.
- `timeout`: optional seconds, default `30`, range `1` through `120`.

The tool returns:

```json
{
  "result": null,
  "error": null,
  "stdout": "",
  "stderr": "",
  "exit_code": 0,
  "timed_out": false
}
```

The last JavaScript expression becomes `result`:

```js
const config = await oci.config();
const response = await oci.identity.IdentityClient.listRegionSubscriptions({
  tenancyId: config.tenancyId
});
response.items.map(item => item.regionName);
```

Constructed clients and per-client region selection are supported:

```js
const compute = new oci.core.ComputeClient({ region: "us-ashburn-1" });
const response = await compute.listInstances({
  compartmentId,
  limit: 50
});
response.items.map(instance => instance.displayName);
```

Only `region` is accepted as a client option. Arbitrary endpoints, credential
providers, signers, and retry configuration are rejected. SDK pagination
helpers and local utility methods are not exposed; use request `page` and
response `opcNextPage` fields directly.

Shallow reflection works with `Object.keys(oci)`, `Object.keys(oci.core)`, and
`Object.keys(new oci.core.ComputeClient())`.

### `discover_oci`

`discover_oci` accepts optional `service`, `client`, and `operation` filters. It
reads installed SDK declarations without running untrusted code and reports:

- supported services and client classes;
- actual API operations that have SDK request types;
- operation request fields and required-field metadata;
- basic response and pagination information.

## Validation

Run these commands from `src/oci-javascript-mcp-server`:

```sh
npm test
npm run coverage
npm run check
npm run ci
```

`npm run coverage` enforces at least 90% line coverage. `npm run ci` runs
coverage, TypeScript checking, and a package dry-run.

## Production admission

Production is the default mode. Both included providers fail closed in
production:

- Without `OCI_JAVASCRIPT_ALLOW_INSECURE_PROCESS=1`, startup rejects the
  insecure provider opt-in.
- With that opt-in but `OCI_JAVASCRIPT_MODE=production`, trusted admission still
  rejects the provider because it lacks a separate guest kernel, hardware
  virtualization, and enforced blocking of new network sockets.
- The Apple container provider has a separate hardware-virtualized guest kernel,
  but production still rejects it because its host-only network does not prevent
  socket creation and the provider remains explicitly development-only.
- Selecting an unimplemented provider also fails startup.

A production provider must report and independently demonstrate an approved
virtual-machine boundary, a separate guest kernel, hardware virtualization,
network-creation blocking, deterministic teardown, and a host-bound channel.
Capability metadata is descriptive; the trusted host admission decision is
authoritative.

## Security controls in this slice

- Four-byte length-prefixed, versioned JSON frames with a 2 MiB hard ceiling.
- Oversized frame rejection from the length header before parsing the body.
- Fatal UTF-8 decoding and inert JSON parsing.
- Recursive rejection of `__proto__`, `prototype`, `constructor`, and type-tag
  keys.
- Depth, string, array, object-key, node, request, response, result, and output
  limits.
- Exact message schemas and rejection of unknown versions, message types, and
  fields.
- Fresh null-prototype canonical OCI request objects built from SDK request
  field allowlists.
- Host-owned operation, mutation, region, tenancy, compartment, resource,
  deadline, call, concurrency, request-byte, and response-byte policy seams.
- OCI response sanitization removes credential-like and HTTP transport fields.
- A scrubbed runner environment and no `process`, `require`, filesystem,
  child-process, or general network globals in the `vm.Context`.
- Cancellation and deadlines forcibly terminate the runner process group.
- Apple container executions add a fresh VM boundary, no host mounts, read-only
  rootfs, non-root execution, dropped capabilities, resource limits, and named
  forced cleanup.

## Deliberately deferred work and limitations

This spike does not yet implement Firecracker, Kata Containers, or another
production-approved VM provider with independently enforced network-creation
blocking. Consequently it is suitable only for local development and CI, not
hostile production execution.

The Apple container provider requires Apple silicon and macOS 26 or newer. Its
internal network prevents external routing but remains host-only rather than
socketless, so a compromised guest may reach services on that network. The
runner image must be built before starting the MCP server; the provider does not
build or update images during execution.

The process provider cannot stop a fully compromised runner process from using
the host kernel or creating sockets. That limitation is explicit in its
capability metadata and is why production admission rejects it. The broker is
still designed and tested to remain authorization-safe when a compromised
runner bypasses the facade and drives the pre-opened channel directly.

The final production source for per-execution tenancy, compartment, resource,
and operation policy is not yet selected. Production defaults therefore expose
no OCI operations. Development policy is generated explicitly from installed
SDK request declarations and defaults to read-only.

## License

Copyright (c) 2026, Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0; see `LICENSE.txt`.
