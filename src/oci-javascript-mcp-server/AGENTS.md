# JavaScript engineering context

## Scope and ownership

This TypeScript server runs JavaScript in an isolated runner and mediates OCI calls on the host. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The existing Podman implementation conflicts with root's named subprocess exception; that gap is recorded below, not treated as authorization for a new backend.

## Entry points

- [server.ts](src/server.ts): MCP tool handling and entry point; [oci-host.ts](src/oci-host.ts): host-side OCI calls, credentials and exposed SDK behavior.
- [protocol.ts](src/protocol.ts): framed host/runner messages; [sandbox.ts](src/sandbox.ts), [worker](src/sandbox-worker.ts) and [isolate](src/sandbox-isolate.ts): execution orchestration.
- [Podman provider](src/isolation/podman.ts) and [pipe lifecycle](src/isolation/pipe-execution.ts): process arguments, execution limits and cleanup.
- [Test directory](test), [package.json](package.json) and [README](README.md): behavior definitions, native commands and runtime setup.

## Setup / build / run

Run `npm ci` from this package directory (`src/oci-javascript-mcp-server`) for locked setup. The manifest requires Node 26+ and declares npm 11.12.1; [repository pins](../../.prototools) and native dependencies also matter. Runtime Podman image/configuration and stdio startup are in README. `npm run podman:build` and `npm start` are runtime actions, separate from the fake-control-plane checks and this documentation pass.

## Tests and validation

From this package directory, `npm run ci` runs coverage, TypeScript checking and package verification. Focused `npm test`, `npm run coverage` and `npm run check` have different scope; tests alone do not enforce coverage. Root `make javascript-ci` runs npm setup and CI. Use the [shared validation map](../../docs/agent-development.md#validation-map) for sources and cross-runtime limits.

Protocol work starts with [protocol tests](test/protocol.test.ts) and [sandbox tests](test/sandbox.test.ts); host changes with [OCI host tests](test/oci-host.test.ts); MCP changes with [server tests](test/server.test.ts). Tests use [fake Podman](test/fake-podman.ts) for command/framing behavior. c8 config enforces 90% **line** coverage with explicit exclusions; neither those tests nor this unexecuted check list prove deployment isolation.

## Architecture and dependencies

Preserve the host/runner split described in [README architecture](README.md#architecture): credentials, SDK clients and HTTPS calls remain on the host; runner communication uses the narrow framed bridge. Trace message validation, size/time/call limits, cancellation and teardown together. Native npm scripts define TypeScript execution flags and package verification. Python/Common credential implementations are not the authentication interface of this Node SDK path.

## Security and secrets handling

The [provider](src/isolation/podman.ts) defines no network, a read-only root, dropped capabilities, non-root execution and bounded resources. Preserve those constraints and cleanup; keep credentials and raw SDK/process errors out of runner-visible responses. The [README security model](README.md#security-model) distinguishes nested isolate/container controls from a VM security boundary. Mocked command/protocol checks do not certify real Podman isolation.

## Change impact

Protocol, host OCI, sandbox, provider or package-script changes affect runtime execution and client-visible results/errors. Select focused tests and the package CI route, and review native README for configuration/isolation changes. Follow [CONTRIBUTING](../../CONTRIBUTING.md) and root changelog rules; no package changelog exists at this baseline, and instruction-only adoption does not create one.

## Known gaps

- Root's subprocess rule names API alone as the exception, while this package already launches Podman. Record the conflict and resolve policy through the owning project; this guide grants no exception or new backend authority.
- Native dependency/toolchain setup can block checks. A setup failure is separate from a test result; c8 coverage is line coverage with exclusions.
- Fake-control-plane tests establish command/framing behavior only. No real runtime, OCI service or isolation checks ran in this adoption.
- There is no explicit package `moon.yml`; [toolchains](../../.moon/toolchains.yml) infer tasks from npm scripts. Use native package commands rather than a task file from a different branch.

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Changing exposed OCI calls or credentials | [Host implementation](src/oci-host.ts), [README](README.md) | Root quality/security guidance and host/runner boundary | [Host tests](test/oci-host.test.ts); no Python/Common-auth assumption |
| **Know:** Changing execution/protocol/isolation | [Protocol](src/protocol.ts), [provider](src/isolation/podman.ts), [pipe lifecycle](src/isolation/pipe-execution.ts) | [Security model](README.md#security-model), recorded root-policy conflict | [Protocol](test/protocol.test.ts), [sandbox](test/sandbox.test.ts) and [server tests](test/server.test.ts); fake provider limits explicit |
| **Do:** Preparing or validating this runtime | [Package scripts](package.json), [validation map](../../docs/agent-development.md#validation-map) | Node/native dependency setup, package working directory | Actual CI/coverage/type/package reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

Use native sources for local details and inherited shared guidance for repository requirements. This adoption's Now/Proof record is the [summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md); startup/deployment checks remain separate from documentation review.
