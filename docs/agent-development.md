# Shared engineering context

This document routes existing monorepo engineering sources. It introduces no required skill bundle, agent harness or new application policy. Root instructions remain in [AGENTS.md](../AGENTS.md); native READMEs, manifests, command definitions and local guides provide their owning details.

## Start here

1. Identify the requested change and owning package/shared library. Read [root instructions](../AGENTS.md) and any applicable nested guide before editing, including when following a direct source link.
2. Find the package README, implementation/interfaces, manifest and tests. Use [BEST_PRACTICES](../BEST_PRACTICES.md) for shared server requirements and [Common's README](../src/common/README.md) for Python authentication contracts. Compute is a structure/model/test reference, with a legacy-auth gap.
3. Read the relevant command sources in the validation map. Separate setup, build, package tests, aggregate coverage and runtime checks; they provide different evidence.
4. Assess interfaces/consumers, contribution requirements and local gaps before expanding a change. [CONTRIBUTING](../CONTRIBUTING.md) owns issue, signoff and PR guidance; root owns changelog rules. [SECURITY](../SECURITY.md) owns vulnerability reporting, not every runtime security constraint.
5. Report source inference and actual checks separately using the evidence routes below. A local gap does not authorize removing shared requirements or performing an unrelated migration.

## Selected component context

This adoption selects root plus five local scopes. Common, Compute and Cloud now have broad guides; JavaScript and Java remain pending at this increment. Use native README/source/manifest/test paths alongside each guide. Other packages retain their existing root/native guidance and are not claimed as covered by this pass.

| Scope | Native entry | Local guide status |
| --- | --- | --- |
| Common shared library | [README](../src/common/README.md), [exports](../src/common/oracle_mcp_common/__init__.py) | [Common guide](../src/common/AGENTS.md) |
| Compute | [README](../src/oci-compute-mcp-server/README.md), [server](../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/server.py) | [Compute guide](../src/oci-compute-mcp-server/AGENTS.md) |
| Cloud | [README](../src/oci-cloud-mcp-server/README.md), [server](../src/oci-cloud-mcp-server/oracle/oci_cloud_mcp_server/server.py) | [Cloud guide](../src/oci-cloud-mcp-server/AGENTS.md) |
| JavaScript | [README](../src/oci-javascript-mcp-server/README.md), [server](../src/oci-javascript-mcp-server/src/server.ts) | Pending |
| Java toolkit | [README](../src/oracle-db-mcp-java-toolkit/README.md), [entry point](../src/oracle-db-mcp-java-toolkit/src/main/java/com/oracle/database/mcptoolkit/OracleDatabaseMCPToolkit.java) | Pending |

## Validation map

These commands are **source-verified**, not executed results. Choose the setup/checks appropriate to the change. Documentation-only changes need path/link, command-source, scope/instruction and diff review; running a server or installing dependencies is unnecessary for those checks.

| Scope | Working directory | Existing setup/build/check routes |
| --- | --- | --- |
| Common | Repository root | `make sync project=common`; `make build project=common`; `make test project=common` under root policy; Moon `common:build` and `common:test` are defined alternatives with different test scope |
| Compute | Repository root | `make sync project=oci-compute-mcp-server`; `make build project=oci-compute-mcp-server`; `make test project=oci-compute-mcp-server`; Moon `oci-compute-mcp-server:build` and `oci-compute-mcp-server:test` |
| Cloud | Repository root | `make sync project=oci-cloud-mcp-server`; `make build project=oci-cloud-mcp-server`; `make test project=oci-cloud-mcp-server`; Moon `oci-cloud-mcp-server:build` and `oci-cloud-mcp-server:test` |
| Python source/shared behavior | Repository root | Root requires `make lint` after Python source changes, and `make test` for shared changes across non-excluded packages. `moon run root:lint`, `moon run :test`, `moon run root:combine-coverage` exist; package-only checks do not establish shared coverage. |
| JavaScript | `src/oci-javascript-mcp-server` | `npm ci` for locked setup; `npm run ci` runs coverage, type checking and package verification. `npm test`, `npm run coverage`, `npm run check` are focused steps, not equivalent evidence. Root `make javascript-ci` performs setup and CI. |
| Java toolkit | `src/oracle-db-mcp-java-toolkit` | JDK 17+, Maven 3.9+ per README; `mvn clean package`. Check actual test discovery/reports when executed; no configured 90% enforcement is established. |
| Documentation only | Repository root | Resolve changed links/anchors and source paths, compare command definitions, review scope/instructions and run `git diff --check`. Report these separately from server quality. |

Command sources: [Makefile](../Makefile), [Moon Python tasks](../.moon/tasks/python.yml), [root tasks](../moon.yml), [workspace discovery](../.moon/workspace.yml), [toolchains](../.moon/toolchains.yml), [tool pins](../.prototools), native manifests and [JavaScript scripts](../src/oci-javascript-mcp-server/package.json). Python locks/manifests define each environment; direct `uv sync --directory src/<package> --locked --all-extras --dev` is also a source-backed setup route. Do not silently upgrade dependencies while synchronizing an existing environment.

### Check scope and coverage

- `make test project=<package>` runs the selected Python package tests, writes/appends its workspace coverage file, then invokes aggregate `combine-coverage`. Inspect which reports came from the current run; a focused invocation or existing report does not establish all consumers were tested.
- `moon run <package>:test` runs the package's inherited test task and writes `.coverage.<package>` plus its HTML report. It does not invoke Makefile's aggregate step. No `test-focused` task exists at this baseline.
- `make test` covers non-excluded Python packages. Makefile excludes dbtools, MySQL, JavaScript, Pricing, DB Doc and the Java toolkit. Follow each excluded package's native validation route; exclusion does not waive quality requirements.
- Moon discovery includes Python manifests and JavaScript's package manifest, with its own exclusions. JavaScript tasks are inferred from npm scripts; there is no explicit JavaScript `moon.yml` here. Java has no discovered Moon project. Do not infer coverage from another runtime's successful task.
- Python package manifests configure their own thresholds; root requires at least 90% for server quality checks. JavaScript c8 enforces 90% **line** coverage with explicit exclusions. Java's POM provides no JaCoCo enforcement; build success or zero discovered tests is insufficient evidence.
- Server startup, OCI operations, database access and real Podman deployment are distinct from mocked unit checks. Use each native README for runtime setup; this adoption performs none of those operations.

## Known gaps

These observations describe the pinned adoption source at `d0e442b`; recheck implementation and instruction identities for a later engineering task. They do not approve exceptions or prove compliance.

| Area | Observed source difference or evidence limit | Relevant sources |
| --- | --- | --- |
| Common consumers | API, Cloud and Database declare Common and Moon edges; other servers must not be assumed migrated | [API manifest](../src/oci-api-mcp-server/pyproject.toml), [Cloud manifest](../src/oci-cloud-mcp-server/pyproject.toml), [Database manifest](../src/oci-database-mcp-server/pyproject.toml) |
| Common package requirements | README lists OCI SDK 2.179.0+ and optional FastMCP 3.4.2; manifest declares OCI 2.185.0+ and FastMCP `>=3.2.4,<4.0.0` | [README](../src/common/README.md#package-requirements), [manifest](../src/common/pyproject.toml); use manifest for install definitions and flag the discrepancy |
| Compute auth | Client/HTTP helpers resolve credentials locally; manifest has no Common dependency | [server](../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/server.py), [manifest](../src/oci-compute-mcp-server/pyproject.toml); root Common requirement remains applicable |
| JavaScript subprocess policy | Existing Podman provider invokes a process, while root names API alone as a subprocess exception | [provider](../src/oci-javascript-mcp-server/src/isolation/podman.ts), [root quality rules](../AGENTS.md#mcp-server-quality-validation); record conflict without authorizing another backend/exception |
| JavaScript isolation evidence | Fake-control-plane tests cover protocol and command construction; shared-kernel containers are not VM boundaries | [README security/development](../src/oci-javascript-mcp-server/README.md), [tests](../src/oci-javascript-mcp-server/test); real deployment isolation not established |
| Java validation | JUnit dependency exists; no explicit Surefire pin or JaCoCo coverage enforcement; discovery/results unexecuted here | [POM](../src/oracle-db-mcp-java-toolkit/pom.xml), [tests](../src/oracle-db-mcp-java-toolkit/src/test/java/com/oracle/database/mcptoolkit) |
| Ownership and selected coverage | Guides describe technical scope, not a verified named-maintainer roster; unselected packages have not received this pass | [contribution process](../CONTRIBUTING.md), [adoption summary](plans/adopt-monorepo-agent-context/adoption-summary.md) |

## Evidence and context routes

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating implementation, constraints or shared/local differences | [Selected native entries](#selected-component-context), [Common contract](../src/common/README.md), [quality guidance](../BEST_PRACTICES.md) | Root and applicable local instructions, target manifest | Owning implementation/test definitions; [known gaps](#known-gaps) |
| **Do:** Selecting setup/build/validation | [Validation map](#validation-map) | Runtime/toolchain and native command definitions | Actual exit status, test discovery, current-run coverage and blocked-check reports in the owning change |
| **Now:** Reviewing this adoption | [Design](plans/adopt-monorepo-agent-context/design.md), [implementation plan](plans/adopt-monorepo-agent-context/implementation-plan.md) | [Pinned reuse assessment](plans/adopt-monorepo-agent-context/reuse-assessment.md) | [Adoption summary](plans/adopt-monorepo-agent-context/adoption-summary.md) |
| **Proof:** Interpreting an engineering completion claim | Owning tests and native run reports; this pass's [summary](plans/adopt-monorepo-agent-context/adoption-summary.md) | Source/guidance identity, exact command/directory and scope | Label source-verified, executed/pass, executed/fail, or unverified; distinguish retrieval/structural review from runtime behavior |

Keep long contracts/procedures in their owning docs and executable definitions. Guides provide orientation and task mappings. This root bundle states its selected scope; it does not imply every package is covered. No Done/archive directory or evidence placeholder is required. This pass does not launch an agent explanation trial; file/link checks do not establish effective agent use.
