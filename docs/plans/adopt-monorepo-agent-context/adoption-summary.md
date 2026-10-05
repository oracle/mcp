# Selected monorepo engineering-context adoption

Status: **Approved sequential guide implementation and structural coverage review completed; fresh whole-branch review pending.** This is a documentation baseline for six selected scopes, not a server-quality or agent-effectiveness result.

## Scope and identities

- Branch: `codex/monorepo-agent-context-clean` in `dustin-sale/mcp`.
- Application/instruction baseline: local main `d0e442b3ddcffe05c6f366c14dac42548641b60f`; no application, dependency, tooling or test-definition changes.
- Planning commit: `98d8da92652c65c5b9f7d1e28f64e5426630e2fe`; implementation commits: `f84bc95` (shared/root), `7d4596b` (Common/Python), `0858500` (JavaScript/Java). Final review-record identity is available in Git history and the delivery message.
- Broader-guide source reviewed for reuse: `03faa20e23753a4a148839243382c7d3b11dac5e`; framework working profile: AI Pit Crew `c9b1724`.
- Selected scopes: root, Common, Compute, Cloud, JavaScript and Java toolkit. Other packages inherit existing root/native guidance and have not received this broad-guide pass.

## Delivered context

Expanded [root guidance](../../../AGENTS.md) and created [shared engineering context](../../agent-development.md) plus five local guides. Native READMEs, commands, manifests, source/tests and project policies remain authoritative. Shared/local task maps answer relevance, context, prerequisites and evidence without copying native bodies. Now/Proof routes use this scoped root bundle; no optional-role placeholder or archive store was created.

Existing root validation/auth/subprocess/changelog requirements were preserved. No standalone pagination policy, inventory or local paging documents, skills or runtime harness were added, and no prior branch commits were merged. Broad guides use current main sources, not later experimental fixes/tests.

## Nine-area coverage review

Executed author review on October 5, 2026. Each local guide contains all nine areas; the root uses existing sections and specific shared routes. The table identifies the source of each answer; explicit gaps are coverage disclosures, not proof of compliance.

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
| Compute response change | Root -> shared selected map -> Compute guide -> server/models/tool/model tests; Compute start -> root quality and shared validation/changelog sources | Entry points, compatibility/change impact and legacy auth distinction discoverable; no later response fix/test was imported |
| Runtime setup/validation | Root and all five local starts -> shared validation map plus Makefile/Moon/native manifests, JavaScript scripts and Java README/POM | Working directory, setup/build/check scope and evidence limits exposed; no undefined focused task; commands source-verified only |
| Authentication ownership/impact | Root/Common/Cloud/Compute -> Common contracts/exports/tests, three consumer manifests/edges and local client helpers | Shared credential ownership and caller-owned client lifecycle visible; Compute legacy/non-consumer gap preserved |
| Isolation/auth evidence | Root/JavaScript/Java -> provider/protocol/host tests, README security model, Java OAuth/filter/scope tests and POM | Podman policy conflict, fake-runtime/VM-boundary limits and Java discovery/coverage gap explicit; no security/compliance certification |
| Shared/local composition | Root and all selected local starts -> parent/shared guides and runtime-specific native topic/action/evidence sources | Broad orientation works across auth, architecture, setup, validation, impact and gaps without a pagination-policy dependency; unselected packages not counted as covered |

## Executed checks and unexecuted work

- Local-link/anchor and source-path review across the branch's changed Markdown. Task 1: 6 files, 121 links/16 fragments; Task 2: 9 files, 219/38; Task 3: 11 files, 290/51. Task 4/final author pass: 11 files, 311 links/67 fragments; later review corrections are checked again.
- Checked displayed commands against Makefile, inherited/root Moon definitions, npm scripts, manifests/locks/toolchains and Java README/POM. Checked three Common dependency declarations/edges and two current Java test definitions.
- Confirmed all existing root instruction lines remain, source/tooling diffs are empty, and the branch diff is limited to the planned 11 Markdown files. `git diff --check` passed.
- No server suites, builds, dependency installations, live OCI/database/Podman operations, paid evaluation or agent trial ran. Documentation checks do not establish runtime coverage or effective agent use.

## Remaining gaps and next review

Common README/manifest requirement differences, Compute legacy auth, JavaScript's root subprocess-policy conflict/isolation limits and Java discovery/coverage enforcement remain unresolved by design. Named maintainer ownership is not verified, and other packages have not received this pass. These observations are not exemptions or new policy.

Review this concrete six-guide baseline. Broader adoption, policy/code remediation and agent explanation trials are subsequent choices. Preserve existing sources and recorded limits when expanding.
