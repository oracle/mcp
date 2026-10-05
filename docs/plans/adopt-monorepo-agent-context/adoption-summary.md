# Selected monorepo engineering-context adoption

Status: **Approved sequential guide implementation completed; subsequently rebased onto user-updated main with source-guidance corrections.** This is a documentation baseline for six selected scopes, not a server-quality or agent-effectiveness result.

## Scope and identities

- Branch: `codex/monorepo-agent-context-clean` in `dustin-sale/mcp`.
- Current application/instruction baseline: user-updated main `52ea0163591d4c8bf3adc8e7cf74e7532ecd1df4`; this branch adds no application, dependency, tooling or test-definition changes relative to that main.
- Historical pre-rebase identities (superseded by the rebase): planning commit: `98d8da92652c65c5b9f7d1e28f64e5426630e2fe`; implementation commits: `f84bc95` (shared/root), `7d4596b` (Common/Python), `0858500` (JavaScript/Java). Final review-record identity is available in Git history and the delivery message.
- Broader-guide source reviewed for reuse: `03faa20e23753a4a148839243382c7d3b11dac5e`; framework working profile: AI Pit Crew `c9b1724`.
- Selected scopes: root, Common, Compute, Cloud, JavaScript and Java toolkit. Other packages inherit existing root/native guidance and have not received this broad-guide pass.

## Delivered context

Expanded [root guidance](../../../AGENTS.md) and created [shared engineering context](../../agent-development.md) plus five local guides. Native READMEs, commands, manifests, source/tests and project policies remain authoritative. Shared/local task maps answer relevance, context, prerequisites and evidence without copying native bodies. Now/Proof routes use this scoped root bundle; no optional-role placeholder or archive store was created.

Existing root validation/auth/subprocess/changelog requirements were preserved. No standalone pagination policy, inventory or local paging documents, skills or runtime harness were added, and no prior branch commits were merged. Broad guides use the rebased main sources; upstream application/test/tooling changes are part of main, not this documentation diff.

## Nine-area coverage review

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

## Executed manual route cases

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

Common README/manifest requirement differences, Compute legacy auth, JavaScript's root subprocess-policy conflict/isolation limits and Java discovery/coverage enforcement remain unresolved by design. Named maintainer ownership is not verified, and other packages have not received this pass. These observations are not exemptions or new policy.

Review this concrete six-guide baseline. Broader adoption, policy/code remediation and agent explanation trials are subsequent choices. Preserve existing sources and recorded limits when expanding.

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
