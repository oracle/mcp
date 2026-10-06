# JavaScript engineering context

## Scope and ownership

This TypeScript server runs JavaScript in an isolated runner and mediates OCI calls on the host. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The existing Podman implementation conflicts with root's named subprocess exception; that gap is recorded below, not treated as authorization for a new backend.

## Entry points

- [server.ts](src/server.ts): MCP tool handling and entry point; [oci-host.ts](src/oci-host.ts): host-side OCI calls, credentials and exposed SDK behavior.
- [Protocol](src/protocol.ts), [gRPC boundary](src/grpc.ts) and [protobuf contract](proto/runner.proto): typed host/runner messages, bounded encoding and session contract; [sandbox.ts](src/sandbox.ts), [worker](src/sandbox-worker.ts) and [isolate](src/sandbox-isolate.ts): execution orchestration.
- [Podman provider](src/isolation/podman.ts) and [gRPC lifecycle](src/isolation/grpc-execution.ts): process/network arguments, fresh mTLS identities, execution limits and cleanup.
- [Test directory](test), [Moon tasks](moon.yml), [package.json](package.json) and [README](README.md): behavior definitions, native commands and runtime setup.

## Setup / build / run

From the repository root, run `proto install`, then `moon run oci-javascript-mcp-server:compile` to generate bindings and compile the npm entry point. Moon installs locked npm dependencies before package tasks. The manifest requires Node 26+ and declares npm 11.12.1; [repository pins](../../.prototools) and native dependencies also matter. README owns runtime setup: `moon run oci-javascript-mcp-server:runner-build` builds the image, and `npm start` runs from this package directory. Runtime actions are separate from this documentation pass.

## Tests and validation

From the repository root, use `moon run oci-javascript-mcp-server:test` for tests with coverage, `moon run oci-javascript-mcp-server:check` for TypeScript checks and `moon run oci-javascript-mcp-server:build` for the npm tarball. All three depend on compile. The package exposes only the `start` npm script; former npm test/coverage/check/CI scripts are unavailable. Use the [shared validation map](../../docs/agent-development.md#validation-map) for sources and cross-runtime limits.

Protocol work starts with [protocol tests](test/protocol.test.ts), [gRPC tests](test/grpc.test.ts) and [sandbox tests](test/sandbox.test.ts); host changes with [OCI host tests](test/oci-host.test.ts); MCP changes with [server tests](test/server.test.ts); packaging changes with [packaging tests](test/packaging.test.ts). Tests use [fake Podman](test/fake-podman.ts) for command construction and the mTLS gRPC session. c8 config enforces 90% **line** coverage with explicit exclusions; neither those definitions nor this unexecuted check list prove deployment isolation.

## Architecture and dependencies

Preserve the host/runner split described in [README architecture](README.md#architecture): credentials, SDK clients and HTTPS calls remain on the host; runner communication uses the bounded mTLS gRPC session defined by `proto/runner.proto`. Trace message validation, size/time/call limits, cancellation and teardown together. The v4 endpoint requires matching host/runner versions; rebuild the runner image after a host update, with no fallback or execution replay. Moon compile generates codecs/bindings from the schema; generated `src/generated/` and `dist/` are not committed. Python/Common credential implementations are not the authentication interface of this Node SDK path.

## Security and secrets handling

The [provider](src/isolation/podman.ts) defines a fresh internal network with no external route, a gRPC port published to host loopback, a read-only root, dropped capabilities, non-root execution and bounded resources. Each execution receives fresh mTLS identities; the runner receives its server key and the host's public certificate, never the host's private key. Preserve those constraints and cleanup; keep OCI credentials and raw SDK/process errors out of runner-visible responses. The [README security model](README.md#security-model) distinguishes nested isolate/container controls from a VM security boundary. Mocked command/protocol checks do not certify real Podman isolation.

## Change impact

Protocol, host OCI, sandbox, provider or task/schema changes affect runtime execution and client-visible results/errors. Select relevant tests plus Moon test/check/build routes, and review native README for configuration/isolation changes. Follow [CONTRIBUTING](../../CONTRIBUTING.md) and root rules for the existing [CHANGELOG](CHANGELOG.md); instruction-only adoption requires no runtime changelog entry.

## Known gaps

- Root's subprocess rule names API alone as the exception, while this package already launches Podman. Record the conflict and resolve policy through the owning project; this guide grants no exception or new backend authority.
- Native dependency/toolchain setup can block checks. A setup failure is separate from a test result; c8 coverage is line coverage with exclusions.
- Fake-control-plane test definitions cover command construction and gRPC behavior, not Podman itself. No real runtime, OCI service or isolation checks ran in this adoption.
- Explicit [Moon tasks](moon.yml) own compilation, tests, type checking and packaging; inspecting those definitions is not evidence that they passed.

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Changing exposed OCI calls or credentials | [Host implementation](src/oci-host.ts), [README](README.md) | Root quality/security guidance and host/runner boundary | [Host tests](test/oci-host.test.ts); no Python/Common-auth assumption |
| **Know:** Changing execution/protocol/isolation | [Protocol](src/protocol.ts), [schema](proto/runner.proto), [provider](src/isolation/podman.ts), [gRPC lifecycle](src/isolation/grpc-execution.ts) | [Security model](README.md#security-model), matching host/runner contract, recorded root-policy conflict | [Protocol](test/protocol.test.ts), [gRPC](test/grpc.test.ts), [sandbox](test/sandbox.test.ts) and [server tests](test/server.test.ts); fake provider limits explicit |
| **Do:** Preparing or validating this runtime | [Moon tasks](moon.yml), [manifest](package.json), [validation map](../../docs/agent-development.md#validation-map) | Node/native dependencies, repository task directory, generated compile prerequisites | Actual test/coverage/type/package reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

Use native sources for local details and inherited shared guidance for repository requirements. This adoption's Now/Proof record is the [summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md); startup/deployment checks remain separate from documentation review.
