# Guide reuse assessment against updated main

Status: **Reassessed on October 5, 2026 after the user pulled main and requested a rebase plus guidance corrections.** This is the current source assessment. The earlier main baseline and its review are retained as historical evidence in the adoption summary. Only documentation changes belong to this branch; no server tests or agent trial have run.

## Source identities and method

| Source | Identity | Use |
| --- | --- | --- |
| Updated fork main | `52ea0163591d4c8bf3adc8e7cf74e7532ecd1df4` | Current application, instruction and task baseline; equals local `origin/main` at reassessment |
| Initial fork main | `d0e442b3ddcffe05c6f366c14dac42548641b60f` | Historical pre-rebase baseline, superseded for current guidance |
| Pre-rebase delivery | `c06877005d595367b01e24b71591da6d48302836` | Preserved in local `codex/monorepo-agent-context-before-rebase`; prior review does not validate newer sources |
| Earlier broad-guide work | `03faa20e23753a4a148839243382c7d3b11dac5e` | Individual source/guide leads, rechecked rather than merged |
| Framework reviewed draft | AI Pit Crew `c9b1724` | Nine-area informational guide profile |

Rebased the six context commits onto the user's updated main without conflicts, then inspected the upstream diff, current native docs, task definitions, manifests, selected implementation and test definitions. This task did not fetch again. Source identities changed materially: no unchanged-source or prior-review assumption is transferred to this revision.

## Core-area dispositions

All nine areas remain required for the selected guides, with concise local answers, specific shared/native references or explicit gaps. This pass rechecks scope/ownership, entry points, setup/build/run, tests/validation, architecture/dependencies, security/secrets, change impact, known gaps and workflow/routing. Exact heading representation remains flexible. Shared answers remain centralized.

## Root and shared guidance

Preserve updated [root instructions](../../../AGENTS.md), including Moon validation and exclusions. [README](../../../README.md), [BEST_PRACTICES](../../../BEST_PRACTICES.md), [CONTRIBUTING](../../../CONTRIBUTING.md) and [SECURITY](../../../SECURITY.md) retain their native responsibilities. The selected nested guides and [shared engineering map](../../agent-development.md) are this branch's additions.

Main removed the Makefile. [Inherited Python tasks](../../../.moon/tasks/python.yml), [root tasks](../../../moon.yml), [workspace discovery](../../../.moon/workspace.yml), [toolchains](../../../.moon/toolchains.yml) and [JavaScript tasks](../../../src/oci-javascript-mcp-server/moon.yml) now own validation definitions. Remove obsolete Make commands and links. Root aggregate Python coverage is a direct coverage-tool task, separate from package tests. No `test-focused` task exists. Compute remains a structure/model/test reference with legacy auth, not the shared credential contract to copy.

## Common and Cloud

[Common README](../../../src/common/README.md), [auth](../../../src/common/oracle_mcp_common/auth.py), [exports](../../../src/common/oracle_mcp_common/__init__.py), [tests](../../../src/common/oracle_mcp_common/tests/test_auth.py) and [manifest](../../../src/common/pyproject.toml) remain the owning auth sources. Common owns credential ingredients; servers own listeners, request retrieval and service clients.

Five manifests declare Common: API, Cloud, Database, DB Observability and Document Understanding. API, Cloud and Database explicitly declare Common Moon dependency edges; the two newer consumers have no package Moon file. Dependency declarations, build graph edges and actual call sites are separate facts; no whole-repository migration is inferred. Compute declares no Common dependency.

Common's README still lists OCI SDK 2.179.0+ and optional FastMCP 3.4.2, while the manifest declares OCI 2.185.0+ and FastMCP `>=3.2.4,<4.0.0`. Preserve the mismatch as a gap and use the manifest for installation requirements; no version-policy change is authorized.

Cloud's [server](../../../src/oci-cloud-mcp-server/oracle/oci_cloud_mcp_server/server.py), [tests](../../../src/oci-cloud-mcp-server/oracle/oci_cloud_mcp_server/tests), [manifest](../../../src/oci-cloud-mcp-server/pyproject.toml) and [Moon dependency](../../../src/oci-cloud-mcp-server/moon.yml) still support dynamic discovery/coercion/invocation/serialization and Common auth with caller-specific clients. Update setup and validation routes; retain the transport-selection distinction and no imported pagination policy.

## Compute

Current [server](../../../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/server.py), [models](../../../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/models.py), [tool tests](../../../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/tests/test_compute_tools.py) and [model tests](../../../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/tests/test_compute_models.py) now include boot-volume instance sources with precedence over image sources. Replace stale blanket claims that newer source/test additions are absent. Use current definitions for response work without changing application behavior.

Legacy local config/security-token resolution and HTTP exchange remain outside Common; preserve that gap. Replace setup/test/lint commands with current Moon/native environment routes. Existing test definitions and configured 90% coverage are not executed results.

## JavaScript

The [README](../../../src/oci-javascript-mcp-server/README.md), [host](../../../src/oci-javascript-mcp-server/src/oci-host.ts), [protocol](../../../src/oci-javascript-mcp-server/src/protocol.ts), [schema](../../../src/oci-javascript-mcp-server/proto/runner.proto), [gRPC lifecycle](../../../src/oci-javascript-mcp-server/src/isolation/grpc-execution.ts), [provider](../../../src/oci-javascript-mcp-server/src/isolation/podman.ts) and [tests](../../../src/oci-javascript-mcp-server/test) describe a bounded mTLS gRPC bridge. The old pipe lifecycle is removed. The provider creates an internal no-egress network and publishes the gRPC port to host loopback; it does not disable networking entirely. Host OCI credentials remain outside the runner. Matching v4 host/runner versions and image rebuilds matter for compatibility.

Explicit [Moon tasks](../../../src/oci-javascript-mcp-server/moon.yml) own compile, test, check, build and runner-build. Test/check/build depend on generated compile output. [package.json](../../../src/oci-javascript-mcp-server/package.json) exposes only `start`; former npm validation and Podman-build scripts are unavailable. Node 26+ and npm 11.12.1 remain declared; c8 enforces 90% line coverage with exclusions. A package changelog now exists.

Preserve root's existing subprocess-policy conflict: it names only API as an exception while JavaScript invokes Podman. This guide grants no new exception. Fake-control-plane tests exercise hardened command construction and mTLS gRPC behavior, not Podman deployment isolation. Shared-kernel containers are not VM boundaries.

## Java toolkit

[README](../../../src/oracle-db-mcp-java-toolkit/README.md) still defines JDK 17+, Maven 3.9+ and package-directory `mvn clean package`. [POM](../../../src/oracle-db-mcp-java-toolkit/pom.xml) has Java 17/JUnit with no explicit Surefire pin or JaCoCo enforcement. Actual discovery/results and the root 90% requirement remain unverified/gapped. Java has no discovered Moon project.

The [test tree](../../../src/oracle-db-mcp-java-toolkit/src/test/java/com/oracle/database/mcptoolkit) now has five unit-test classes (scope extraction, authenticated principal, origin validator, transaction registry, JDBC log analyzer), one gated database-backed DeepSec integration test and two support classes. Update source/test routes for principal/context, request-target validation, owned transactions and DeepSec; remove claims that those additions are absent. The integration test requires `DEEPSEC_IT_ENABLED=true`, browser OAuth and a database and remains outside this documentation pass. No coverage or security certification follows from source definitions.

## Source-verified command map

These are current definitions, **not executed results**. The [shared validation map](../../agent-development.md#validation-map) gives task scope, prerequisites and evidence limits.

| Scope | Working directory | Current route and limits |
| --- | --- | --- |
| Tool/environment setup | Repository root | `proto install`; Moon installs locked package dependencies. Direct Python `uv sync --directory src/<package> --locked --all-extras --dev` remains defined by native environment configuration. |
| Python package | Repository root | `moon run <package>:test`; `moon run <package>:build` checks packaging. No aggregate coverage step is included in package tests. |
| Python source/shared | Repository root | `moon run root:lint`; shared `moon run :test`, then `moon run root:combine-coverage`. The test selector includes JavaScript; the combine task aggregates Python reports only. Inspect current report provenance. |
| JavaScript | Repository root | `moon run oci-javascript-mcp-server:compile`, `:test`, `:check`, `:build` using the full project-qualified target for each command. Runtime runner-build/start remain separate. |
| Java | Java toolkit directory | `mvn clean package`; verify actual test discovery/reports when executed. No implied 90% enforcement. |
| Documentation | Repository root | Local links/anchors/paths, command/source facts, scope/instruction consistency and `git diff --check`; no server-test claim. |

## Exclusions and next action

Only monorepo-agent bundle/root/shared/local guide changes belong in the diff against updated main. Upstream application, tests and tooling arrive through main, not this branch's scope. No pagination adoption history, policy/docs/inventory, application fixes, task changes, dependencies, lockfiles, thresholds, skills, harness or live trial is added. Review the corrected six-guide baseline with the [adoption summary](adoption-summary.md); any broader adoption or policy/code remediation remains separate.
