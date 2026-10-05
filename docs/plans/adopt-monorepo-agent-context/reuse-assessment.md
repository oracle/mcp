# Guide reuse assessment against main

Status: **Reassessed on October 5, 2026 for a fresh main-based monorepo-agent branch.** This replaces the pagination-based assessment for this branch. No guides, server code or tooling have been adapted; no server tests or agent trial have run.

## Source identities and method

| Source | Identity | Use |
| --- | --- | --- |
| Fork local main | `d0e442b3ddcffe05c6f366c14dac42548641b60f` | Clean application, instruction and command baseline |
| Earlier broad-guide work | `enhanced-agent-harness`, `03faa20e23753a4a148839243382c7d3b11dac5e` | Individual guide/source leads to recheck |
| Framework reviewed draft | AI Pit Crew `codex/agent-guide-contract`, `c9b1724` | Nine-area informational guide profile |
| Previous planning bundle | `c4a36c7d025758cc9969428e649337a1066c5b2c` | Four documents copied and revised; no commit or application history imported |

Inspected tracked trees, pinned older guides, scoped diffs and main's native docs, manifests, Makefile, Moon definitions, entry points and test definitions. `main` denotes the fork's existing local branch; no remote fetch or latest-remote claim is made. Its snapshot is materially different from the previous pagination-based plan.

Common and Cloud implementation/tests/manifests are unchanged relative to the inspected broad-guide source. JavaScript source/tests are unchanged, but package scripts and task configuration differ. Compute source/model/tests and Java implementation/tests/POM differ. No unchanged-source assumption can be transferred across all five packages. Reuse each verified fact, not the old branch as a unit.

## Core-area dispositions

R = source-backed content can be reused; V = adapt/recheck against main. Explicit gaps below remain even in otherwise reusable areas. The same nine questions apply at root and local scopes; inherited answers do not need repeated bodies.

| Core area | Root | Common | Compute | Cloud | JavaScript | Java toolkit |
| --- | --- | --- | --- | --- | --- | --- |
| Scope/ownership | V: selected guide map | R: auth library | R: compute operations | R: dynamic SDK | V: root exception claim | R: configurable toolkit |
| Entry points | V: native/shared routes | R: auth/exports/tests | V: main tools/models/tests | R: discovery/invocation/tests | R: host/runner/protocol | V: main config/tools/OAuth/tests |
| Setup/build/run | V: Makefile and Moon | R: manifest/lock/tasks | V: current native procedures | R: workspace/tasks | V: main npm scripts | R: README Maven/JDK |
| Tests/validation | V: actual command scopes | V: shared map | V: no focused Moon task | V: shared map | V: npm ci is valid here | V: two tests; discovery/coverage gap |
| Architecture/dependencies | V: shared/runtime boundaries | R: auth ownership | V: main behavior; legacy auth | R: Common/dynamic calls | R: host/runner split | V: exclude newer implementation claims |
| Security/secrets | R: native policy routes | R: auth boundaries | R: legacy credential gap | R: caller-specific clients | V: policy conflict explicit | V: main OAuth/auth sources |
| Change impact | V: selected scope/consumers | V: three declared consumers | V: current tools/models | R: dynamic operation surface | V: npm validation | V: current handlers/config |
| Known gaps | V: scoped source limits | V: doc/manifest mismatch | V: no new test-result claim | R: unrun validation | V: isolation/policy limits | V: discovery/90% limits |
| Workflow/routing | V: existing sources/intents | V: new shared links | V: current local topics | V: shared/local composition | V: native runtime routes | V: native runtime routes |

## Root and shared guidance

Main has a [root guide](../../../AGENTS.md), [README](../../../README.md), [BEST_PRACTICES](../../../BEST_PRACTICES.md), [CONTRIBUTING](../../../CONTRIBUTING.md) and [SECURITY](../../../SECURITY.md). It has no selected nested guides or `docs/agent-development.md`. Create those as the scoped monorepo-agent deliverable. CONTRIBUTING governs contribution/signoff; SECURITY is vulnerability-reporting guidance, not a complete runtime security contract.

The older shared engineering document supplies orientation, validation mapping and evidence distinctions. Adapt those responsibilities, excluding skill routing/catalog/provenance, fixed development workflows, environment/approval mechanics and missing evaluation-document dependencies. Keep native sources authoritative and show Do/Know/Now/Proof routes; no archive or placeholder intent folders are required.

Unlike the pagination baseline, main retains the [Makefile](../../../Makefile) and root Makefile validation instructions alongside [Moon Python tasks](../../../.moon/tasks/python.yml) and [root tasks](../../../moon.yml). Document both sources and their scope. Do not copy newer Moon-only root instructions or replace command definitions. Compute remains a structure/model/test reference; its legacy auth is not the Common contract to copy.

## Common and Cloud

Common's [README](../../../src/common/README.md), [auth implementation](../../../src/common/oracle_mcp_common/auth.py), [exports](../../../src/common/oracle_mcp_common/__init__.py), [tests](../../../src/common/oracle_mcp_common/tests/test_auth.py) and [manifest](../../../src/common/pyproject.toml) support the old library orientation and credential/per-caller HTTP boundaries. The library owns auth ingredients, not server listeners or service clients.

Main declares `oracle-mcp-common` consumers in API, Cloud and Database manifests; all three also declare Moon `common` dependency edges. The DB Observability consumer from the previous assessment is not present here. Compute has no Common dependency. Recheck actual consumers for later shared changes.

The Common README lists OCI SDK 2.179.0+ and optional FastMCP 3.4.2; the manifest declares OCI 2.185.0+ and FastMCP `>=3.2.4,<4.0.0`. Link the manifest for install requirements and record the mismatch; do not reconcile version policy in this pass.

Cloud's [server](../../../src/oci-cloud-mcp-server/oracle/oci_cloud_mcp_server/server.py), [test directory](../../../src/oci-cloud-mcp-server/oracle/oci_cloud_mcp_server/tests), [manifest](../../../src/oci-cloud-mcp-server/pyproject.toml) and [Moon dependency](../../../src/oci-cloud-mcp-server/moon.yml) support reuse of dynamic discovery/coercion/invocation/serialization, Common auth and caller-specific client descriptions. Add native source/test routes without importing a shared pagination policy.

## Compute

Recheck the older guide against main's [server](../../../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/server.py), [models](../../../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/models.py), [tool tests](../../../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/tests/test_compute_tools.py), [model tests](../../../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/tests/test_compute_models.py) and [manifest](../../../src/oci-compute-mcp-server/pyproject.toml). Main lacks the subsequent response/model/limit fixes and associated tests; those changes must not enter this branch through guide reuse.

Scope, major entry points and the legacy local security-token/HTTP exchange gap remain useful. Describe only main's behavior and available evidence. The inherited Moon file has no `test-focused`; use existing Makefile/Moon commands with their actual scope. A pagination question can point to current source/tests as an optional example, without new pagination documentation or policy.

## JavaScript

The [README](../../../src/oci-javascript-mcp-server/README.md), [host](../../../src/oci-javascript-mcp-server/src/oci-host.ts), [protocol](../../../src/oci-javascript-mcp-server/src/protocol.ts), [Podman provider](../../../src/oci-javascript-mcp-server/src/isolation/podman.ts) and [tests](../../../src/oci-javascript-mcp-server/test) support host-owned credentials, bounded runner communication and fake-control-plane evidence limits.

Here [package.json](../../../src/oci-javascript-mcp-server/package.json) defines `test`, `coverage`, `check`, `packcheck` and `ci`: the older `npm run ci` route is valid on main. It runs coverage, type checking and package verification. c8 enforces 90% line coverage with exclusions; `npm test` alone does not enforce that threshold. Main has no explicit package `moon.yml`; [toolchains](../../../.moon/toolchains.yml) enable task inference from npm scripts. Prefer native README/npm commands, not the later explicit Moon configuration.

Root's subprocess rule names API alone as an exception, while JavaScript already invokes Podman. Record that instruction/implementation conflict; do not import the old guide's authorization claim or add an exception. Fake tests do not establish real Podman isolation, and shared-kernel containers are not VM boundaries. Python Common auth does not define this Node SDK implementation.

## Java toolkit

Main's [README](../../../src/oracle-db-mcp-java-toolkit/README.md) documents JDK 17+, Maven 3.9+, `mvn clean package`, tool/configuration and transport/OAuth procedures. The [POM](../../../src/oracle-db-mcp-java-toolkit/pom.xml) declares Java 17/JUnit with no explicit Surefire pin or JaCoCo enforcement. Actual discovery and the root 90% requirement remain unverified/gapped.

Main's [test tree](../../../src/oracle-db-mcp-java-toolkit/src/test/java/com/oracle/database/mcptoolkit) contains `OracleJDBCLogAnalyzerTest` and `oauth/OAuth2TokenValidatorTest`. Newer request-target, authenticated-principal, owned-transaction and DeepSec test/source additions from the previous plan are absent. Route current [config](../../../src/oracle-db-mcp-java-toolkit/src/main/java/com/oracle/database/mcptoolkit/config), [tools](../../../src/oracle-db-mcp-java-toolkit/src/main/java/com/oracle/database/mcptoolkit/tools), [OAuth](../../../src/oracle-db-mcp-java-toolkit/src/main/java/com/oracle/database/mcptoolkit/oauth) and [web](../../../src/oracle-db-mcp-java-toolkit/src/main/java/com/oracle/database/mcptoolkit/web) sources; no live database or browser login is a default check. Java is outside current Makefile Python targets and has no discovered Moon project.

## Source-verified command map

These are existing command definitions, **not executed results**. Read [Makefile](../../../Makefile), [Moon workspace](../../../.moon/workspace.yml), inherited/root task definitions and runtime manifests before choosing a later check.

| Scope | Working directory | Current route and limits |
| --- | --- | --- |
| Python setup | Repository root | `make sync project=<package>` or `uv sync --directory src/<package> --locked --all-extras --dev`; manifests/locks/toolchain configuration |
| Python package validation | Repository root | Root policy: `make test project=<package>`. Makefile runs package tests then aggregate coverage; compare run provenance. Moon alternative: `moon run <package>:test` checks package scope without that aggregate step. |
| Python build/source/shared | Repository root | `make build project=<package>`, `make lint`, shared `make test`; Moon `:build`, `root:lint`, `:test` and `root:combine-coverage` are defined alternatives with their own scope. Root combine task delegates to Makefile. |
| JavaScript setup/validation | Package directory | `npm ci`, `npm run ci`; README/package scripts. Root `make javascript-ci` also exists. No runtime Podman build/start is needed for documentation validation. |
| Java build | Java toolkit directory | `mvn clean package`; README/POM. Check actual test reports when executed; no implied 90% enforcement. |
| Documentation | Repository root | Local links/anchors/paths, command definitions, scope/instruction consistency and `git diff --check`; no server-test claim. |

## Exclusions and next action

Only monorepo-agent planning and later root/shared/local guide changes belong in this branch. No pagination adoption history, policy/docs/inventory, application fixes, task changes, dependencies, lockfiles, thresholds, skills, agent harness or live trial. Baseline source and substantive policies remain project-owned. Review the [implementation plan](implementation-plan.md) before adapting the six guides sequentially.
