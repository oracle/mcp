# Monorepo engineering-context implementation plan

> **For execution:** Use `superpowers:executing-plans` task by task, preserving the user's sequential execution preference. This development workflow is not an adopter requirement or guide content.

**Status:** Approved sequential implementation completed on October 5, 2026; subsequently rebased onto user-updated main and rechecked for source drift. Fresh review of the rebased guidance found no documentation issues. The adoption summary distinguishes historical review from current corrections, validation and the new independent verdict.

**Goal:** Establish broad, source-backed engineering context in six selected guide scopes on a clean main branch.

**Architecture:** Root owns shared orientation and context routes; a shared engineering document routes existing native procedures and evidence. Five library/component guides add local information and references without copying shared policy. Adapt verified older content individually onto a fresh main baseline.

**Tech stack:** Markdown; existing Moon/uv Python tasks, TypeScript/Moon tasks and Java/Maven definitions as source material only.

**Spec:** [Adoption design](design.md). Read the [reuse assessment](reuse-assessment.md) before execution.

## Global constraints

- Fork: `dustin-sale/mcp`; updated local main baseline `52ea0163591d4c8bf3adc8e7cf74e7532ecd1df4` (original `d0e442b` baseline superseded); older guide source `03faa20e23753a4a148839243382c7d3b11dac5e`. Recheck source identities and diffs before edits if the baseline changes.
- Selected scopes: root, Common, Compute, Cloud, JavaScript and Java toolkit. No whole-repository coverage claim or placeholder group guide.
- Each guide makes all nine informational areas available inline, through specific shared/native references or explicit gaps. Exact headings/table format are flexible.
- Existing project instructions and native sources retain policy, command, precedence and execution authority. No code, tooling, dependency, lockfile, threshold, skill or runtime changes.
- Carry only this monorepo-agent bundle and the subsequent guide/documentation changes. Do not import pagination policy/docs/inventory, application fixes, tooling or commits from the earlier branches. Keep shared answers centralized; task maps expose relevance, context, shared prerequisites and evidence.
- Documentation validation only. No fabricated source facts, ownership identities, commands or executed results; no new server tests mirroring prose and no implicit live/paid trial.

## File map

| File | Responsibility |
| --- | --- |
| `AGENTS.md` — modify | Root orientation, shared constraints, selected guide/topic routes and coverage boundary; retain existing policy |
| `docs/agent-development.md` — create | Source-backed start route, setup/validation map, command provenance, contribution/security sources and selected gaps |
| `src/common/AGENTS.md` — create | Shared auth/library orientation, exports, consumers, native actions and gaps |
| `src/oci-compute-mcp-server/AGENTS.md` — create | Broad Compute orientation, legacy-auth distinction and defined validation routes |
| `src/oci-cloud-mcp-server/AGENTS.md` — create | Broad dynamic-SDK orientation, Common boundaries and concern-specific evidence |
| `src/oci-javascript-mcp-server/AGENTS.md` — create | Broad host/runner context, defined Moon actions, isolation limits and policy conflict |
| `src/oracle-db-mcp-java-toolkit/AGENTS.md` — create | Broad Java/config/OAuth context, native build and evidence limitations |
| `docs/plans/adopt-monorepo-agent-context/adoption-summary.md` — update | Source identities, actual coverage, review results, gaps and implementation status |

Native READMEs, BEST_PRACTICES, CONTRIBUTING, SECURITY, manifests and task files remain authoritative sources, not copied bodies. No server changelog entry is planned for this instruction-only change; preserve root changelog rules.

## Review focus

1. Component-start navigation reaches root/shared prerequisites as well as local topic material.
2. Main defines inherited/root Python Moon tasks and explicit JavaScript Moon tasks; npm scripts expose startup only. Retain actual command scope, prerequisites and working directory. Source verification is not execution.
3. Shared-library consumers and Compute's legacy auth stay distinct from full Common adoption or compliance.
4. JavaScript's existing Podman implementation/root-policy conflict and Java test/coverage gaps remain explicit.
5. Shared authentication, validation and architecture context compose with local differences; no inherited pagination-policy dependency or whole-repository coverage claim.

## Task 1: Shared engineering source map and root guide

**Files:** Create `docs/agent-development.md`; modify `AGENTS.md`; update this bundle's adoption summary.

**Consumes:** Existing root guide, README, BEST_PRACTICES, CONTRIBUTING, SECURITY, toolchains, root/package task definitions and the reuse assessment. Inspect older `docs/agent-development.md` using pinned `git show`; no branch merge.

**Produces:** Stable `docs/agent-development.md#start-here`, `#validation-map`, `#known-gaps` and `#evidence-and-context-routes` anchors for local guides. Root discovery lists the selected scopes and clearly labels current/uncompleted coverage.

- [x] Read current root policy and source definitions. Confirm no new applicable guide or source drift; record baseline.
- [x] Write the shared document with the four stable anchors, the assessment's current command map, native-source references, actual evidence labels and selected gaps. Exclude old skill and harness/approval mechanics.
- [x] Expand root orientation across the nine areas using shared references. Preserve existing validation/auth/subprocess/changelog requirements. Qualify Compute's reference role and expose existing conflicts without authorizing exceptions.
- [x] Add Know/Do/Now/Proof routes or their clear equivalents for shared auth, architecture, engineering actions, selected local context and this bundle. Label pending guide coverage; add each local guide link only once the target exists.
- [x] Review cases 1–5 below for root/shared sources and run link/path checks plus `git diff --check`. Report source-verified commands and unresolved conflicts.
- [x] Update the adoption summary and commit the explicit files with signoff under CONTRIBUTING: `docs: establish shared engineering context routes`.

## Task 2: Common and Python component guides

**Files:** Create `src/common/AGENTS.md`; create Compute and Cloud `AGENTS.md`; finish their root routes; update adoption summary.

**Consumes:** Task 1's stable shared anchors, existing policy and native docs; older guides from the pinned source; current Python implementation, tests and manifests.

**Produces:** Three broad guides covering nine areas, with local source/action/evidence routes and explicit shared prerequisites. Common lists declared consumers and distinguishes Moon edges; Compute and Cloud provide several native task/topic routes.

- [x] Verify old entry points and architectural statements against current Common/Compute/Cloud source. Check all five declared Common consumers and the three explicit package Moon edges; record Compute's absent dependency.
- [x] Adapt Common's nine-area guide. Link native auth contracts and tests, state library non-applicability for a listener, route shared-change validation, and record the README/manifest requirements mismatch.
- [x] Adapt Compute's broad guide. Preserve tools/models/tests, client/user-agent boundaries and legacy auth gap. Preserve updated main root Moon policy and separate package tests from aggregate coverage.
- [x] Adapt Cloud's broad guide. Route discovery/coercion/invocation/serialization tests, Common dependency/auth and caller-specific client boundaries, plus operation-specific implementation/test evidence from main.
- [x] Complete root links to these guides. Review cases 1–3 and 5 below from both root and package starts; check all changed links/anchors and `git diff --check`.
- [x] Record coverage/gaps in the summary and commit the explicit files with signoff: `docs: add broad Common and Python server context`.

## Task 3: JavaScript and Java native context

**Files:** Create JavaScript and Java toolkit `AGENTS.md`; finish their root routes; update adoption summary.

**Consumes:** Task 1's shared anchors, current Node/Moon/Java sources and the pinned older guides. Python-specific auth/validation does not supply these runtime answers.

**Produces:** Two broad runtime-specific guides with native procedures, architecture/security boundaries, change impact, gaps and task-relevant native context.

- [x] Adapt JavaScript's nine areas from current host/runner/protocol/provider and test sources. Use explicit package Moon compile/test/check/build tasks from the repository root, with Node manifest/toolchain and generated-bindings prerequisites. Trace current mTLS gRPC sources and the no-egress internal network; former npm validation scripts and pipe lifecycle are removed.
- [x] Record JavaScript's existing root subprocess-policy conflict, credential-free runner boundary, shared-kernel limitation and fake-control-plane evidence limits. A documented gap grants no exception.
- [x] Adapt Java's nine areas from current config/registration/OAuth sources. Link native Maven/JDK guidance and current tests; route the five unit-test classes, current principal/context, origin and transaction sources, and separately gated DeepSec integration test now present in main. No live integration check is part of this pass.
- [x] Retain Java's native configuration/tool routes, no-discovered-Moon-project fact, and unverified test discovery/90% enforcement gap. Do not add Maven plugins or a new changelog.
- [x] Complete root links. Review cases 1, 2, 4 and 5 below from root and local starts; check changed links/anchors and `git diff --check`.
- [x] Update summary and commit the explicit files with signoff: `docs: add broad JavaScript and Java context`.

## Task 4: Complete selected coverage review and handoff

**Files:** Update the adoption summary; correct scoped documentation defects in Task 1–3 files if found.

**Consumes:** Six implemented guides, shared document and authoritative main-branch sources. **Produces:** Concrete review record for the selected engineering baseline, with unresolved gaps and source/check identities.

- [x] Review all six guides against the nine-area profile. For each area identify the answer/reference/gap; reject vague repo-wide references and unsupported completion claims.
- [x] Walk all five cases below from root and relevant local starts. Record expected sources reached, actual defects and unresolved conflicts; these manual checks are not agent trials.
- [x] Validate changed Markdown targets/anchors and referenced paths, compare every displayed command with its current definition, and run `git diff --check`. Inspect `git diff --name-only main` to confirm only planned documentation files changed.
- [x] Record final guidance/source revision, actual checks, unexecuted suites and limitations. State that unselected packages have not received this broader guide pass. Confirm no pagination-adoption files or source/tooling changes entered the diff.
- [x] Commit the review summary with signoff and present the concrete selected baseline for user review. Stop before expansion, policy remediation or a separately selected behavior trial.

## Manual review cases and expected sources

| Case | Starting points | Expected source-backed result |
| --- | --- | --- |
| 1. Investigate a Compute response change | Root; Compute | Root/shared constraints, Compute tool/model/test entry points, typed responses, compatibility/changelog routes; legacy auth not copied as the shared pattern |
| 2. Prepare and validate different runtimes | Root; Common/Compute/Cloud/JavaScript/Java | Correct working directory, existing manifests/tasks or README procedures, valid main-defined Moon/Maven actions, no undefined focused task, unrun commands labeled source-verified |
| 3. Identify auth ownership and change impact | Root; Common; Cloud; Compute | Common contracts and actual declared consumers; Cloud consumes them; Compute gap explicit; consumer declarations distinct from Moon edges |
| 4. Assess isolation/auth boundaries and evidence | Root; JavaScript; Java | Host credentials and bounded runner protocol; Podman policy conflict/isolation limits; Java OAuth/config and current test sources; no implied coverage/security certification |
| 5. Compose shared and local engineering context | Root; Common/Compute/Cloud/JavaScript/Java | Shared auth/quality/validation sources plus relevant local differences; setup/architecture/impact/gaps reachable without a pagination policy; unselected packages not counted as covered |

A separately selected agent explanation exercise can later observe retrieval/interpretation using these cases and pinned guidance identities. This plan executes no such trial.
