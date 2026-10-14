# Repository context assessment — 2026-10-07

Assessment of `dustin-sale/mcp` at `3a7cfd9623ec97ad7c365b9b77f28e459aefca8c` on `main`. The working tree was clean before this review. This record is the only repository change; assessed guides, contracts, application code and historical outcomes are unchanged.

The reviewed context has complete component discovery and usable shared/native routes. No broken local link or fragment was found in the selected corpus. Its main weakness is source drift: Recovery 3.0, Common consumer relationships and two coverage settings have changed without corresponding updates to current guidance. Four context findings remain below. This is a scoped assessment, not whole-repository certification or a passing application/effectiveness evaluation.

## Scope and method

Selected engineering baseline:

- Root [instructions](../../../AGENTS.md), [shared engineering context](../../agent-development.md), [context conventions](../../agent-context.md) and [authentication integration/ledger](../../authentication.md).
- Structural inventory of every current server component: 34 servers plus Common, with all 35 local guides checked against the shared index and nine-area profile.
- Substantive route walks for Common, Compute, Cloud, API, Database, Recovery, Document Understanding, Data Studio, IoT, JavaScript, Java toolkit, DBTools, MySQL, Pricing and DB Doc. Other guides received structural checks and review of architecture, security and known-gap descriptions; their complete source semantics were not independently audited.
- Historical adoption, context-application and shared-authentication records, read for their scope, source identities and evidence distinctions.

Starting points were root `AGENTS.md` and the relevant component `AGENTS.md`. The representative questions were: where does a tool/response change belong; who owns credential resolution and which consumers need review; how do HTTP and configured credentials differ; what commands and working directories apply; what does isolation evidence establish; and how are context changes maintained?

Excluded: application-code review/remediation, exhaustive validation of every native README/source claim, named-maintainer verification, other repository directories as independent component scopes, installation/build/lint/server-test/coverage execution, live OCI/database/public-API/Podman calls, new consumer evaluations, paid tracing and publication. Optional action, evidence or archive directories are not required and their absence is not a finding.

The user-supplied aipack-managed OCI Console policies were treated as session guidance and left unchanged. Their access rules apply to Console systems; this assessment needed no Console backend access. Tracked repository context has no managed/generated notice requiring a separate editable source for this record. Root instructions and applicable local guides remain engineering requirements; the AgentStanza framework supplies the assessment method, not new application policy.

## Sources and identities

| Source | Role and identity |
| --- | --- |
| Target repository | Clean `main` at `3a7cfd9623ec97ad7c365b9b77f28e459aefca8c`; this commit identifies the reviewed tracked documents, manifests, command definitions and source |
| AgentStanza assessment skill | Installed `agentstanza-assess`; resource package identity `2217b49f6669db88d6fb1fef3a722969b751daa5` |
| Framework method | `agentstanza/workflows/readiness-playbook.md`, core profile in `guide/agent-guides.md`, four mapping questions in `guide/discovery-and-mapping.md`, optionality in `guide/intents-and-layout.md`; all required resources available and read |
| Local context method | [Authoring procedure](../../agent-context.md#authoring-procedure), [mapping convention](../../agent-context.md#mapping-convention), [evidence and maintenance](../../agent-context.md#evidence-and-maintenance) |
| Engineering requirements | [Root quality rules](../../../AGENTS.md#mcp-server-quality-validation), [BEST_PRACTICES](../../../BEST_PRACTICES.md), [contribution process](../../../CONTRIBUTING.md), [security reporting](../../../SECURITY.md), native package contracts |
| Command sources | [Inherited Python tasks](../../../.moon/tasks/python.yml), [root tasks](../../../moon.yml), [workspace discovery](../../../.moon/workspace.yml), [toolchains](../../../.moon/toolchains.yml), [tool pins](../../../.prototools), [JavaScript tasks](../../../src/oci-javascript-mcp-server/moon.yml), native manifests/READMEs |
| Historical adoption | [Adoption summary](../adopt-monorepo-agent-context/adoption-summary.md), including the original evaluation at MCP `838d82b1f6c879b306368960a79b9bb71335c4b5` and separate expanded documentation review |
| Later documentation evidence | [Context application outcome](../apply-agent-context-guide/outcome.md), [shared-authentication outcome](../shared-authentication-context/outcome.md); these retain their earlier source/check scopes |

Framework file SHA-256 identities: readiness playbook `5cbb554846ebc245b2fc2c099fb0d5b3009c6495410da97dc71034ae4c3f50a2`; core guide profile `41578e1976e69229dbae99dc7a85069a8b2d8f81f9237e22a8699ea44ebabe64`. These identify the installed text used here; they are not claims about a moving external repository.

The historical evaluation report and manifest were accessible in the installed resource package at `agentstanza/evaluations/reviews/2026-10-05-oracle-mcp-agent-context.md` and `evaluations/evidence/2026-10-05-oracle-mcp-context-03/manifest.json`. The packaged report records ten supported retrieval/interpretation cases, setup limitations and no application checks. Its SHA-256 is `85eadb3b26fe8e3413f9abfe1774c49cf82e808fd2a3ffde596e50627afdc1c3`. This review read the packaged report/manifest; it did not independently retrieve the original AI Pit Crew commit `910ba97501f22e2970ba615ae7a8d6ddd41374e5`, re-score raw cases or rerun consumers. No login response or unavailable required framework resource blocked the selected review. Ordinary outbound links from native docs were outside the selected retrieval scope.

## Coverage and route observations

| Core area | Reviewed answer and limit |
| --- | --- |
| Scope and ownership | Root and component boundaries are discoverable, including Common's library role and different runtimes. Named ownership is explicitly unverified |
| Entry points | Shared map reaches all 35 guides, READMEs and implementation entries. Recovery's entry remains valid but no longer describes where most behavior lives (F1) |
| Setup/build/run | Root versus package working directories and runtime prerequisites are available through the validation map and native sources; no startup was performed |
| Tests and validation | Native tasks and package/shared coverage scope are discoverable. Recovery/Data Studio threshold descriptions have drifted (F3); configured gates are not passing results |
| Architecture/dependencies | Common ingredients versus server clients/listeners and CLI/SDK/non-Python distinctions are available. Recovery architecture and shared consumer/graph inventories need refreshing (F1/F2) |
| Security/secrets | Local guides expose credential, caller, document, database and isolation boundaries with shared policy routes. This establishes reachable guidance, not deployed security assurance |
| Change impact | Contribution/changelog routes and affected interfaces are exposed. The Common consumer omission can under-scope a shared change (F2) |
| Known gaps | Guides distinguish observed departures from exceptions and results. Some previously accurate gap descriptions are stale (F1/F3/F4) |
| Workflow/context routing | Four mapping answers are present through tables and referenced local sections. Context conventions reuse native stores; historical records retain source/evidence limits |

These observations combine structural checks with the selected substantive walks; section presence alone does not prove informational accuracy in every component.

| Representative question, from root and owning component | Walked route and result |
| --- | --- |
| Common change: ownership, credentials and consumers | Root/Common → shared authentication → native API/profile/HTTP contract → manifests, imports and Moon files. Ownership is clear; current inventory differs from the guides/ledger (F2) |
| Compute versus Common authentication | Root/Compute → shared guide and Common auth/HTTP prerequisites → local [Compute explanation](../../../src/oci-compute-mcp-server/docs/authentication.md) → helpers/test definitions. Local credentials and host/port dispatch remain distinguishable from requirements; no migration or runtime result inferred |
| API command/filter change | Root/API → guide → server/denylist and Common helper contract → tool tests/inherited task. CLI exception, managed options, `shell=False` and user-agent environment path are discoverable |
| Cloud/Database HTTP client boundaries | Root/local guides → Common contract → client/request helpers and tests. Source distinguishes Cloud's host/port credential dispatch from Database's request-context selection; caller-specific source paths are not caller-isolation test results |
| Recovery auth/tool change | Root/Recovery → current guide → server/manifest/README → actual auth, clients and tool-family modules. All targets resolve, but current guide describes older behavior and omits the new owning modules (F1/F2) |
| Data Studio access or validation | Root/Data Studio → config/profiles/credential store/HTTP runtime and test/manifest routes. Viewer/analyst/admin and service-credential boundaries remain discoverable; the coverage description conflicts with current manifest/README (F3) |
| IoT data access | Root/IoT → local auth/client plus domain/resolver/data-plane entries → module tests. Control-plane OCI auth and ORDS data-token ownership are separate; same-named local `build_auth_context` is not Common adoption |
| JavaScript isolation and Java auth/transactions | Root/local guides → native security/contracts, protocol/provider or OAuth/registry/POM/tests. Fake Podman evidence, shared-kernel limits, subprocess-policy conflict, native Maven and gated database integration limits remain explicit |
| Excluded Python validation | Root/excluded guides → native manifests/READMEs/test definitions. DBTools live prerequisites, MySQL missing native coverage procedure, Pricing network/coverage/packaging limits and DB Doc missing tests/requirements route remain disclosed |
| Context maintenance | Root/Common/Compute → local authoring conventions → owning sources and scoped outcome records. No copied shared auth topic or placeholder guide is needed |

Declared prerequisites were followed for these selected routes, including root/local instructions, Common public contracts and runtime/command sources. No selected prerequisite cycle or missing prerequisite target was found. Common ↔ Compute comparison links are navigation; their selected dependency columns point to shared contracts, not recursive dependency on every mapping in the other guide. This is a manual selected-chain observation, not an exhaustive semantic dependency-graph proof.

## Findings

Priorities describe practical context impact. Recommendations authorize no guide or application edits.

### F1 — Important: Recovery guidance describes the pre-3.0 implementation

**Route/scope:** Root component map → [Recovery guide](../../../src/oci-recovery-mcp-server/AGENTS.md), or a direct Recovery start; entry points, architecture, auth and known gaps.

**Evidence:** The guide says `server.py` coordinates clients/tools, the manifest has no Common dependency, and the native README's Common claim conflicts with local auth. Current [server.py](../../../src/oci-recovery-mcp-server/oracle/oci_recovery_mcp_server/server.py) mainly wires tool-family imports and startup. [auth.py](../../../src/oci-recovery-mcp-server/oracle/oci_recovery_mcp_server/auth.py) calls `build_auth_context`, `build_idcs_http_auth` and `context_for`; [clients.py](../../../src/oci-recovery-mcp-server/oracle/oci_recovery_mcp_server/clients.py) owns factories. The [manifest](../../../src/oci-recovery-mcp-server/pyproject.toml) declares `oracle-mcp-common>=0.1.4,<0.2.0`. The [native README](../../../src/oci-recovery-mcp-server/README.md#http-streamable-http-deployment) and [3.0.0 changelog](../../../src/oci-recovery-mcp-server/CHANGELOG.md#300) describe the newer Common-backed design.

**Effect:** A reader can investigate the wrong file, repeat an obsolete non-adoption claim, or miss request-auth, cache, telemetry and tool-registration boundaries even though all guide links resolve.

**Proposed context improvement:** Refresh the Recovery guide against 3.0. Map tool families, auth/client factories, cache/caller boundaries, telemetry and their relevant test modules. Replace the obsolete Common/README conflict disclosure with current, source-supported limitations; retain separation of source observations from runtime qualification. Preserve old adoption records as history.

**Follow-up check:** From root and Recovery starts, an auth/tool investigation reaches `auth.py`, `clients.py`, the owning tool module and [auth/client test definitions](../../../src/oci-recovery-mcp-server/oracle/oci_recovery_mcp_server/tests/test_auth_and_client_factories.py), with correct Common adoption and caller-context descriptions. Search current guides for the obsolete absent-dependency claim; it should not remain as current guidance.

### F2 — Important: shared-change consumer and graph maps are behind source

**Route/scope:** [Root architecture](../../../AGENTS.md#architecture-and-dependencies), [Common architecture](../../../src/common/AGENTS.md#architecture-and-dependencies), [shared gap register](../../agent-development.md#known-gaps) and [authentication ledger](../../authentication.md#adoption-ledger).

**Evidence:** Current guidance lists five declared Common consumers and only API/Cloud/Database Moon edges. Native manifests and production imports now identify six consumers: API, Cloud, Database, DB Observability, Document Understanding and Recovery. [Recovery](../../../src/oci-recovery-mcp-server/moon.yml) and [Document Understanding](../../../src/oci-document-understanding-mcp-server/moon.yml) both declare `dependsOn: common`; five consumers therefore have explicit package edges. DB Observability remains without a package Moon file. The ledger's Recovery row says absent dependency/local auth, consistent with its explicitly pinned `019fec4` snapshot but superseded for a current shared-change investigation.

**Effect:** Shared API/auth changes can omit Recovery from impact analysis, and graph review can incorrectly flag Document Understanding as lacking an existing edge. The ledger's historical snapshot is qualified correctly, but current routes need newer adoption visibility under their own maintenance rules.

**Proposed context improvement:** Refresh the current root/Common/shared inventory together and publish a new source-identified ledger snapshot: six Common users (five SDK integrations plus API's CLI helper integration), 23 local OCI auth/signing cases and five other-runtime/non-OCI cases. Record five explicit package graph edges separately from declarations/imports. Preserve earlier outcome counts at their historical revisions.

**Follow-up check:** Enumerate all server manifests, tracked production Common imports and package Moon edges, then compare sets with current guides/ledger. Expect six declarations/importing server scopes and five explicit edges; inspect Recovery call sites before assigning SDK/HTTP labels. Source use still must not imply full migration compliance or passing validation.

### F3 — Moderate: validation context reports obsolete coverage gates

**Route/scope:** Root known-gap route → [shared gap register](../../agent-development.md#known-gaps) → [Data Studio guide](../../../src/oracle-data-studio-mcp-server/AGENTS.md#tests-and-validation); direct Data Studio and Recovery validation starts.

**Evidence:** Data Studio's guide reports 75% and a below-90% gap; its current [manifest](../../../src/oracle-data-studio-mcp-server/pyproject.toml) sets `fail_under = 90`, and [README development instructions](../../../src/oracle-data-studio-mcp-server/README.md#local-development)/[changelog](../../../src/oracle-data-studio-mcp-server/CHANGELOG.md) describe the newer offline coverage gate. The [root guide](../../../AGENTS.md#known-gaps) and shared gap register still repeat the threshold concern. Recovery's guide reports 90%, while its [manifest](../../../src/oci-recovery-mcp-server/pyproject.toml) sets `fail_under = 100`. These were the two mismatches found when comparing guide threshold statements with native TOML definitions.

**Effect:** Data Studio appears to have a configuration gap already corrected in source; Recovery's stronger package gate is hidden. This can misdirect validation/remediation planning.

**Proposed context improvement:** Update current guide/summary threshold statements and remove the obsolete Data Studio configuration-gap claim. Prefer a specific native-definition route when copying a numeric threshold adds no necessary explanation. Keep historical records and the distinction between a configured gate and achieved coverage.

**Follow-up check:** Recompare every guide's declared threshold with its manifest; expect Data Studio 90 and Recovery 100 with no obsolete current 75% gap. Actual achieved coverage requires a separately scoped test run and remains unverified here.

### F4 — Minor: Common's dependency-gap description is partially outdated

**Route/scope:** Shared gap register → [Common requirements](../../../src/common/README.md#package-requirements) and [manifest](../../../src/common/pyproject.toml); direct Common setup/gap investigation.

**Evidence:** The shared register says README FastMCP 3.4.2 versus manifest `>=3.2.4,<4.0.0`. Current README requires FastMCP 3.4.5+ in 3.x, matching manifest `>=3.4.5,<4.0.0`. The OCI discrepancy remains: README 2.179.0+ versus manifest 2.185.0+. Common's guide still says the sources differ on OCI/FastMCP versions.

**Effect:** A resolved FastMCP mismatch is presented as a current setup concern, making the remaining OCI discrepancy harder to assess accurately.

**Proposed context improvement:** Narrow the current gap to the observed OCI mismatch and refresh/remove obsolete FastMCP version details. Reuse the updated native HTTP contract for Common 0.1.4 resource-scope qualification and CIMD options rather than adding a copied topic document.

**Follow-up check:** Compare README requirement statements with TOML dependencies; current context should identify only the remaining OCI version difference. Installation and compatibility remain separate checks.

## Executed checks and limits

| Check executed in this assessment | Outcome and scope |
| --- | --- |
| Repository identity/status and baseline comparison | Recorded HEAD/branch and initial clean tree; compared changed source/manifests against the ledger's `019fec4` baseline to identify newer Recovery, Common and Data Studio definitions |
| Component inventory and guide profile | All 34 server directories plus Common have guides and shared index entries; all 35 local guides contain the nine profile areas and root/shared references. Presence is structural evidence |
| Local path/fragment resolution | 47 existing context Markdown files: root, 35 guides, four shared/topic docs and seven historical change records. Checked 1,529 inline local link occurrences and 383 fragments; zero unresolved paths/fragments. Headings were checked with GitHub-style slug generation and duplicate-heading suffixes. This is a bounded Markdown check, not a full renderer or all-native-doc crawl |
| Moon command-source comparison | Checked 117 displayed concrete command occurrences, 66 distinct targets, against root/inherited Python/JavaScript task definitions and workspace discovery/exclusions; no undefined concrete target found. Generic template commands were not treated as concrete targets; no task executed |
| Native manifest claims | Parsed package TOML and compared stated coverage thresholds/Python requirements; threshold drift identified in F3. Separately enumerated Common declarations, production imports and package graph edges for F2 |
| Selected route/prerequisite/source review | Manual walks recorded above, with no selected missing target or dependency cycle; source observations remain distinct from mocked test definitions and executed results |
| Historical evaluation retrieval | Read installed packaged report/manifest and retained pinned identities/limits; no new trial, re-scoring or original remote-commit verification |
| Assessment artifact | All 44 local links and 15 fragments in this record resolve; final newline/whitespace and repository diff scope checked. Only this new Markdown record was written |

The source/link/inventory checks used one-off Python and read-only Git/search commands, with temporary outputs outside the repository. No new test suite or checker is installed. No application import, dependency installation, build, lint, test, coverage, authentication exchange or live operation was executed.

Still-disclosed limits include Compute/local OCI auth departures, Cloud host/port credential dispatch, DB Observability's OCI dependency constraint conflict, the remaining Common OCI requirement mismatch, JavaScript's subprocess-policy conflict/fake-provider isolation limits, Java test-discovery/coverage limits and excluded-package validation gaps. They are not approved exceptions and were not remediated by this assessment.

## Proposed next increment

A bounded context-maintenance pass should refresh Recovery's local guide and the affected current root/Common/shared/authentication entries, reconcile Data Studio/Recovery coverage descriptions and narrow Common's requirement-gap text. Use the existing context-authoring conventions and `agentstanza-adopt` if that work is requested. Reuse native source/README/test entries, preserve historical records and review both root and component starts. Application remediation, new consumer evaluations and expansion beyond this scope remain separate work.
