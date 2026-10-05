# Monorepo engineering-context adoption

Status: **The original six-scope increment is implemented and reviewed, with ten supported read-only evaluation cases. The user subsequently approved expanding the same profile to all MCP servers.** Current documentation coverage is root, Common and all 34 server components. Original evaluation evidence remains tied to its original guide revision; current expansion review is recorded below.

## Scope and identities

- Branch: `codex/monorepo-agent-context-clean` in `dustin-sale/mcp`.
- Current application/instruction baseline: user-updated main `52ea0163591d4c8bf3adc8e7cf74e7532ecd1df4`; this branch adds no application, dependency, tooling or test-definition changes relative to that main.
- Historical pre-rebase identities (superseded by the rebase): planning commit: `98d8da92652c65c5b9f7d1e28f64e5426630e2fe`; implementation commits: `f84bc95` (shared/root), `7d4596b` (Common/Python), `0858500` (JavaScript/Java). Final review-record identity is available in Git history and the delivery message.
- Broader-guide source reviewed for reuse: `03faa20e23753a4a148839243382c7d3b11dac5e`; framework working profile: AI Pit Crew `c9b1724`.
- Original scopes at `838d82b`: root, Common, Compute, Cloud, JavaScript and Java toolkit.
- Expanded scopes: root, Common and all 34 MCP server components under `src/`; 30 new guides extend the original four server guides. See the [complete map](../../agent-development.md#selected-component-context).

## Delivered context

Expanded [root guidance](../../../AGENTS.md) and [shared engineering context](../../agent-development.md) route all 34 server guides plus Common. The original increment created five local guides; the approved expansion adds 30 server guides. Native READMEs, commands, manifests, source/tests and project policies remain authoritative. Shared/local task maps answer relevance, context, prerequisites and evidence without copying native bodies. Now/Proof routes use this scoped root bundle; no optional-role placeholder or archive store was created.

Existing root validation/auth/subprocess/changelog requirements were preserved. No standalone pagination policy, inventory or local paging documents, skills or runtime harness were added, and no prior branch commits were merged. Broad guides use the rebased main sources; upstream application/test/tooling changes are part of main, not this documentation diff.

## Original increment: nine-area coverage review

Executed author review on October 5, 2026, repeated against updated main after rebase. Each local guide contains all nine areas; the root uses existing sections and specific shared routes. The table identifies the source of each answer; explicit gaps are coverage disclosures, not proof of compliance.

| Area | Root answer/reference | Local answer/reference |
| --- | --- | --- |
| Scope and ownership | [Scope](../../../AGENTS.md#scope), technical package/library boundary; named-owner gap | Each guide's scope; Common library/non-listener role and component responsibilities |
| Entry points | [Repository layout](../../../AGENTS.md#repository-layout), [selected guide/native map](../../agent-development.md#selected-component-context) | Source/interface/config/test/manifest leads in each guide |
| Setup/build/run | [Setup/build routes](../../../AGENTS.md#setup-build-and-change-impact), [validation map](../../agent-development.md#validation-map) | Package working directories, native procedures and runtime separation |
| Tests and validation | [Root requirements](../../../AGENTS.md#validation), shared command-scope/coverage distinctions | Existing local test leads, native checks and configured-versus-executed limits |
| Architecture/dependencies | [Shared boundaries](../../../AGENTS.md#architecture-and-dependencies), Common contract | Library/server/host/runner/Java boundaries; actual consumers and local differences |
| Security/secrets | [Editing rules](../../../AGENTS.md#editing-rules), [quality rules](../../../AGENTS.md#mcp-server-quality-validation), native disclosure/auth sources | Credential/caller/isolation/OAuth constraints with owning source/test references |
| Change impact | [Setup/change impact](../../../AGENTS.md#setup-build-and-change-impact), [changelog rules](../../../AGENTS.md#changelog-guidance), contribution process | Consumers, tool/model/protocol/config interfaces, local docs and validation scope |
| Known gaps | [Gap route](../../../AGENTS.md#known-gaps), [shared gap register](../../agent-development.md#known-gaps) | Local auth, policy, source-version and evidence limitations |
| Workflow/context routing | [Context routes](../../../AGENTS.md#context-routes), [evidence routes](../../agent-development.md#evidence-and-context-routes) | Several native task routes plus explicit root/shared prerequisites and this scoped record |

Selected guide targets: [Common](../../../src/common/AGENTS.md), [Compute](../../../src/oci-compute-mcp-server/AGENTS.md), [Cloud](../../../src/oci-cloud-mcp-server/AGENTS.md), [JavaScript](../../../src/oci-javascript-mcp-server/AGENTS.md) and [Java toolkit](../../../src/oracle-db-mcp-java-toolkit/AGENTS.md).

## Original increment: executed manual route cases

These are author-operated document/source walks from root and relevant local guides, not agent behavior trials or server execution. The [plan](implementation-plan.md#manual-review-cases-and-expected-sources) supplies the questions. Shared targets and prerequisites were followed and checked against current definitions.

| Case | Starts and sources reached | Result and limits |
| --- | --- | --- |
| Compute response change | Root -> shared selected map -> Compute guide -> server/models/tool/model tests; Compute start -> root quality and shared validation/changelog sources | Entry points, compatibility/change impact and legacy auth distinction discoverable; current boot-volume source and precedence handling/tests acknowledged; no application fix added |
| Runtime setup/validation | Root and all five local starts -> shared validation map plus inherited/root/JavaScript Moon tasks, native manifests and Java README/POM | Working directory, setup/build/check scope and evidence limits exposed; no undefined focused task; commands source-verified only |
| Authentication ownership/impact | Root/Common/Cloud/Compute -> Common contracts/exports/tests, five consumer manifests, three explicit package Moon edges and local client helpers | Shared credential ownership and caller-owned client lifecycle visible; Compute legacy/non-consumer gap preserved |
| Isolation/auth evidence | Root/JavaScript/Java -> provider/protocol/host tests, README security model, Java OAuth/principal/origin/transaction sources and tests, gated DeepSec definition and POM | Podman policy conflict, fake-runtime/VM-boundary limits and Java discovery/coverage gap explicit; no security/compliance certification |
| Shared/local composition | Root and all selected local starts -> parent/shared guides and runtime-specific native topic/action/evidence sources | Broad orientation works across auth, architecture, setup, validation, impact and gaps without a pagination-policy dependency; unselected packages not counted as covered |

## Historical pre-rebase checks and unexecuted work

These checks apply only to the initial `d0e442b` baseline. Current validation is recorded below; these totals and source facts do not validate the rebased guidance.

- Local-link/anchor and source-path review across the branch's changed Markdown. Task 1: 6 files, 121 links/16 fragments; Task 2: 9 files, 219/38; Task 3: 11 files, 290/51. Task 4/final author pass: 11 files, 311 links/67 fragments; later review corrections are checked again.
- Checked displayed commands against Makefile, inherited/root Moon definitions, npm scripts, manifests/locks/toolchains and Java README/POM. Checked three Common dependency declarations/edges and two current Java test definitions.
- Confirmed all existing root instruction lines remain, source/tooling diffs are empty, and the branch diff is limited to the planned 11 Markdown files. `git diff --check` passed.
- No server suites, builds, dependency installations, live OCI/database/Podman operations, paid evaluation or agent trial ran. Documentation checks do not establish runtime coverage or effective agent use.

## Remaining gaps and next review

Common README/manifest requirement differences, Compute legacy auth, JavaScript's root subprocess-policy conflict/isolation limits and Java discovery/coverage enforcement remain unresolved by design. Named maintainer ownership is not verified. The original review covered six guide scopes; the subsequent approved extension is recorded below. These observations are not exemptions or new policy.

The user reviewed the original baseline and approved its explanation evaluation, then the all-server extension. Policy/code remediation remains separate. Preserve source identities and recorded limits when interpreting either increment.

## Historical pre-rebase independent review

This review applies to the initial baseline, not the rebased sources or guidance.

A fresh-context reviewer inspected main `d0e442b3ddcffe05c6f366c14dac42548641b60f` through `a11565b15ea4204f2a9381e4be3dfff666d99431` on October 5, 2026. Verdict: no substantive guide/routing defects; ready after correcting the review-record status. The reviewer found the plan prematurely said the review was recorded while this summary still said pending. This final record/status update resolves that inconsistency.

The reviewer independently confirmed all 311 local link targets, the planned 11-file documentation scope, ordered preservation of existing root instructions, clean whitespace/tree, command/dependency/source facts and selected nine-area coverage. The author's 67-anchor result was not independently reproduced; the final author check repeats those anchor checks after this record update.

Runtime correctness, test pass status, actual coverage, deployment isolation and agent effectiveness were explicitly outside the review. They remain unverified; this adoption neither certifies them nor resolves application/policy gaps. No deferred guide findings remain.

## Rebase and current source reassessment

The user pulled main and requested rebasing plus correction of guidance on October 5, 2026. The six documentation commits rebased without conflicts onto `52ea0163591d4c8bf3adc8e7cf74e7532ecd1df4`, matching local `origin/main`. The pre-rebase delivery `c06877005d595367b01e24b71591da6d48302836` is preserved in local `codex/monorepo-agent-context-before-rebase`. No additional fetch, push or merge was performed.

Current corrections:

- Removed Make commands and broken Makefile links. Preserved updated main's root Moon policy, documented package versus aggregate coverage and cross-runtime scope, and retained native Maven validation.
- Replaced JavaScript's removed npm validation/Podman-build scripts and pipe lifecycle with explicit Moon tasks, generated compile prerequisites, bounded mTLS gRPC sources and the internal no-egress network. Recorded matching v4 host/runner requirements and the existing changelog.
- Updated Common to five declared consumers, separating them from three explicit package Moon edges; declarations alone do not prove complete runtime migration.
- Updated Compute's source-version guidance for boot-volume launch sources and corresponding model/tool tests; retained legacy auth as a gap.
- Added Java principal/context, origin-validation, transaction-ownership and current unit-test routes. The gated browser/database DeepSec test remains separate from normal documentation/unit checks; Surefire discovery and 90% enforcement remain unverified/gapped.

Repeated the five manual document/source walks above against the updated baseline. Results remain document navigation/source review evidence, not executed agent behavior. Current author checks resolved 334 local links and 71 fragments across eleven Markdown files, preserved updated-main root instruction lines in order, checked native Moon task definitions, five Common declarations, five Java unit-test classes plus the gated integration source, and confirmed no active Make/npm-validation/pipe routes remain. `git diff --check` passed. Command/source and scoped-diff checks are recorded with the corrective commit in Git history and the delivery message. Only the planned eleven Markdown files differ from updated main; original updated-main root policy remains intact. No server suite, build, dependency installation, runtime or live trial ran.

The earlier independent review is historical. Current source reassessment and author checks apply to the rebased correction; the following record identifies its fresh review.

## Fresh review of the rebased guidance

A fresh-context reviewer inspected the full eleven-file diff from updated main `52ea0163591d4c8bf3adc8e7cf74e7532ecd1df4` through corrective commit `77d463b537721a4afc3b8242e3d1173fc2c4fd37` on October 5, 2026. Verdict: no substantive or minor documentation findings; ready for user review. No findings were deferred.

The reviewer confirmed ordered preservation of updated-main root instructions, selected nine-area coverage and shared/local routing, current Moon command scopes, JavaScript compile/gRPC/mTLS/network boundaries, five Common declarations versus three explicit package graph edges, Compute boot-volume guidance, and Java's current source/test routes and gated integration distinction. It reran the documentation/source checker successfully: eleven Markdown files, 334 local links and 71 fragments. The exact branch diff passed `git diff --check` and the reviewed worktree was clean.

This review did not evaluate builds, server suites, dependency installation, live services, runtime coverage, deployment isolation or agent effectiveness. Those outcomes remain unverified; recording this verdict does not expand the adoption scope.


## Completed original read-only evaluation

On October 5, 2026, five read-only questions were run from both root and a relevant component directory: ten fresh consumer sessions against MCP commit `838d82b1f6c879b306368960a79b9bb71335c4b5`. All ten were supported under the selected pilot’s retrieval/interpretation rubric and passed the access-boundary gate. The cases covered Compute change impact, Common ownership/consumers, runtime validation differences, JavaScript communication/isolation and Java HTTP auth/transactions.

The authoritative report is AI Pit Crew commit `910ba97501f22e2970ba615ae7a8d6ddd41374e5`, `evaluations/reviews/2026-10-05-oracle-mcp-agent-context.md`; sanitized evidence is in `evaluations/evidence/2026-10-05-oracle-mcp-context-03/` at that revision. The source/runtime/access manifest, separately not-assessable setup attempts, rubric scores and final review are recorded there. The consumer used codex-cli 0.157.0, gpt-6-sol and medium reasoning. No application builds/tests, dependency installation or live OCI/database/Podman checks ran. The result supports those questions at the pinned original revision; it does not establish repeatability, causal improvement or behavior coverage for the 30 new guides.

## Approved all-server extension

The user approved the [expansion design](design.md#approved-all-server-expansion--october-5-2026) after the original evaluation. Sequential source inspection at `838d82b` found 34 server components, four with existing guides, and added the 30 missing guides. Common remains a covered library; no placeholder group guide is needed. The complete [server/library map](../../agent-development.md#selected-component-context) reaches each native README, implementation entry and guide.

Every new guide covers the nine informational areas using local source-backed orientation, inherited requirements and explicit gaps. The extension preserves existing root instructions and documents actual differences: CLI versus SDK execution; stdio versus caller-specific HTTP auth; database and document data boundaries; IoT control/data planes; credential-free public pricing; local index lifecycle; profile-filtered Data Studio; GoldenGate REST integration; and Moon-excluded native validation.

Newly visible source gaps include removed Make procedures in DB Observability, its OCI/Common dependency conflict, Data Studio’s 75% threshold, local credential-resolution departures, IoT/OpenSearch token-failure fallback, mismatched native tool tables, Pricing’s absent console package, DB Doc’s absent requirements.txt/tests and DBTools’ live test prerequisites. These are documentation disclosures. Source behavior, dependencies, tasks and coverage settings are unchanged.

### Expansion checks and fresh review

Executed documentation/source checks on October 5, 2026 across the full 41-file Markdown diff from application baseline `52ea016`, explicitly including all 30 new guides. All 34 server directories and Common have local guides, all local guides expose the nine informational areas and parent/shared routes, and the shared map reaches every guide. Author checks resolved 1,292 local links and 330 fragments, checked 78 displayed Moon commands and 48 named function leads against native definitions, preserved main’s root instructions in order and confirmed a documentation-only diff. `git diff --check` passed; new files were also checked for trailing whitespace and final newlines.

A fresh-context read-only reviewer inspected the six changed root/shared/adoption documents and all 30 new guides against `838d82b`, plus the retained guides within the full branch diff. Verdict: ready for user review, with no Critical or Important findings. Two Minor findings were corrected and verified during the same review: DB Doc processes HTML/HTM into Markdown chunks; the reuse assessment’s unexecuted-trial statement is dated to its original rebase assessment. No findings were deferred. The reviewer independently resolved the same 1,292 links/330 fragments, checked ordered root-policy preservation and confirmed no application/configuration changes. Its reviewed 41-file content fingerprint was `e6b36a2a7cb32ae321d314842016d9d44a0240f260e71d27de9bff3e28d46cb1`; the review’s HEAD was `838d82b` with the expansion uncommitted.

After that review, the author added a source-checked DB Doc stdio/HTTP listener disclosure, a Data Studio case to the proposed evaluation and this review record. Final author verification repeated the path/anchor, scope, command-source and whitespace checks. The extension’s final guidance identity is the commit containing this record, available in Git history; it is separate from the original evaluation’s pinned identity.

The reviewer set aside application correctness/remediation, dependency/build success, test discovery/results/achieved coverage, live OCI/database/public API/Podman behavior, deployed security assurance, expanded-guide agent effectiveness/repeatability and named-maintainer ownership. Those remain outside this documentation task. No server imports, builds/tests, dependency installation, live operations or additional consumer runs were performed by the author or reviewer.

### Proposed follow-up evaluation

Prepare a separately identified read-only batch after guide review, with each question asked from root and the owning component directory:

| Case | Investigation | New patterns exercised |
| --- | --- | --- |
| API command change | Explain command parsing/filtering, managed OCI CLI auth/options, subprocess boundaries and appropriate test evidence | CLI-backed execution, Common helpers and explicit root exception |
| Database credential/PDB change | Trace shared versus caller-specific auth, client lifecycle, PDB inputs/response impact and relevant checks | Common SDK consumer, HTTP boundary and database mutations |
| Data Studio access change | Trace default/opt-in capability profiles, config/keyring credential precedence, HTTP bind/bearer controls, query policy and relevant checks | Service SDK integration, profile-filtered tools, non-IDCS HTTP auth and coverage discrepancy |
| IoT twin data access | Trace friendly selectors/domain endpoints, OCI control-plane auth versus ORDS data tokens, caching and relevant tests | Multi-module resolution, independent credential planes and local/Common differences |
| Moon-excluded validation | Explain how to prepare/check DBTools, MySQL, Pricing and DB Doc, distinguishing documented commands, live tests, coverage and packaging gaps | Native script/package routes, network prerequisites and missing evidence |

This is a proposal with no executed expansion trial or prefilled pass result. Freeze a new guide/source identity and approve the concrete prompts/runtime/access plan before executing consumer runs. The original ten-case batch does not need to be rerun solely because this documentation scope grew.
