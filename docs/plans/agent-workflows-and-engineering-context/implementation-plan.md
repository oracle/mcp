# Repository Skills and Engineering Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` for inline execution or `superpowers:subagent-driven-development` if delegated execution is selected. Implement task by task, using the checkboxes to record actual progress. These development skills are not dependencies of the repository skills being authored.

**Goal:** Add five source-backed engineering guides and two repository skills for local review and PR authoring, with issue authoring deferred.

**Architecture:** Existing root policies retain shared requirements; focused documents explain their application. Local review consumes those documents and native validation definitions. PR authoring consumes the canonical PR template, contribution rules and review evidence for the actual proposed change.

**Tech Stack:** Markdown, skill YAML frontmatter, existing Git/Moon/uv and package-native definitions; an authorized GitHub connector or `gh` for the eventual PR workflow.

**Spec:** [Scoped proposal](proposal.md). Read it together with this plan.

**Status:** Implemented and evaluated on 2026-10-07; see the [outcome](outcome.md) for evidence and limits. Changes remain uncommitted. Source baseline: `6e6c3e5121a7ac5000e57648ca51370f75da9e34`, branch `codex/agent-context-followup`.

## Global constraints

- Skills live in `.agents/skills/`; names are `local-review` and `pr-authoring`. No issue-authoring skill, issue templates or issue-creation dependency.
- Keep shared requirements in `AGENTS.md` and `BEST_PRACTICES.md`, procedures in skills, and commands in their native definitions. Follow [context conventions](../../agent-context.md#authoring-procedure).
- Preserve existing Common authentication, caller isolation, derived user-agent, subprocess, changelog and validation requirements. Minimum unit-test coverage remains at least 90%; retain stricter package gates, including Recovery's 100%.
- Both server safeguards and agent confirmation are covered, proportional to reversibility, cost, blast radius and authority changes. Existing authorization persists for the covered target and scope.
- PR authoring returns draft content by default. An explicit draft-creation request authorizes that scoped publication; resolve material target/branch uncertainty before writing. Do not add unrelated external actions.
- Keep contributor skills independent of personal installed Oracle MCP skills. Do not hard-code a fork/upstream target, local machine paths or claims about unavailable capabilities.
- This increment changes context and skills only. Runtime fixes, dependency upgrades, universal pagination helpers, new workflow scripts and repository-wide compliance audits are separate work.
- Record structural checks separately from behavioral evaluation and application tests. Controlled skill trials must not push branches, create public PRs or invoke live OCI operations.
- Preserve user changes. Commit only each task's explicit files, with sign-off when execution includes committing; never stage the whole worktree indiscriminately.

## Review focus

1. Identically named FastMCP implementations: examples must follow actual imports and resolved versions, including Data Studio's SDK import.
2. A total result limit cutting through a backend page: continuation must not silently skip the unreturned part of that page.
3. A confirmation token or timed-out mutation: distinguish target validation from human authorization and reconcile uncertain outcomes before retrying.
4. Documentation-only or dirty-worktree review: choose proportional checks and report the exact included local state, without inventing passing suites.
5. Fork PR with stale review evidence or a missing tracking issue: use the selected base's template and actual published head, preserving contribution requirements without a deferred skill dependency.

Each condition has an owning task and a check below. New policy text must state expectations separately from source descriptions and existing gaps.

## File map and dependencies

| Task | Create | Modify | Responsibility |
| --- | --- | --- | --- |
| 1 | `docs/code-quality.md`, `docs/test-quality.md` | `BEST_PRACTICES.md`, `AGENTS.md` | Concrete code/test criteria and concise owning rules |
| 2 | `docs/fastmcp.md` | `BEST_PRACTICES.md` | Version-aware framework guidance |
| 3 | `docs/pagination.md` | `BEST_PRACTICES.md` | Collection limits, completeness and continuation |
| 4 | `docs/tool-safety.md` | `BEST_PRACTICES.md` | Server safeguards and authorized agent execution |
| 5 | `.agents/skills/local-review/SKILL.md`, `references/report-template.md`, `references/dependency-review.md` within that skill | None | Review workflow and report consumed by PR authoring |
| 6 | `.agents/skills/pr-authoring/SKILL.md` | None | Canonical-template drafting and scoped draft creation |
| 7 | `docs/plans/agent-workflows-and-engineering-context/outcome.md` | `AGENTS.md`, `docs/agent-development.md` | Discovery routes and actual validation record |

Tasks 1–4 supply criteria to Task 5; Task 6 consumes Task 5's report contract. Task 7 verifies the composed routes. Do not add optional UI metadata or supporting scripts unless a demonstrated need changes this scope. Use section anchors as interfaces; do not depend on plan-time line numbers remaining stable.

## Task 1: Code and test quality

**Consumes:** Root editing/quality rules, BEST_PRACTICES code organization and test sections, native coverage definitions, Common contracts and representative tests.

**Produces:** `docs/code-quality.md#review-criteria` and `docs/test-quality.md#review-criteria`; brief owning requirements and links in BEST_PRACTICES. Root editing rules remain concise.

- [x] Read those sources and applicable instructions; check for baseline drift and distinguish existing requirements from additions.
- [x] Write code criteria for unnecessary wrappers/speculative abstractions, duplicated Common logic, success-like exception fallbacks, unjustified suppressions, redundant comments and unrelated cleanup. Include a useful short adapter as a valid counterexample to a blanket wrapper ban.
- [x] Write test criteria for observable results, realistic boundary data, regression/failure cases, isolation, exact user-agent assertions, fixture cleanup and appropriate boundary mocks. Explain direct-function versus in-memory MCP tests and the separate prerequisites for live tests.
- [x] Update BEST_PRACTICES's existing code/test sections and root editing rules with only the enforceable core. Preserve the coverage floor and stricter native gates; avoid copying all rationale into policy.
- [x] Walk examples: a meaningful adapter passes; a silent exception-to-empty-success fails; a mock that bypasses conversion is insufficient evidence for conversion; a 100% coverage package with weak assertions still has a test-quality gap. Check links/anchors and whitespace.
- [x] Review and, when committing, use `docs: define code and test quality guidance` with sign-off and only Task 1 files.

## Task 2: FastMCP guidance

**Consumes:** Task 1 criteria, Common's authentication/HTTP contracts, package imports/manifests/locks, Cloud in-memory tests and native lifecycle implementations.

**Produces:** `docs/fastmcp.md#library-and-version`, `#tool-contracts`, `#lifecycle-and-isolation`, and `#testing`.

- [x] Compare standalone `fastmcp` use in Cloud/Recovery with Data Studio's `mcp.server.fastmcp` import. Record version provenance from manifests and resolved locks; dependency declarations alone do not prove API compatibility.
- [x] Verify needed APIs against version-matched official documentation/source. Recover or explicitly report previously inaccessible testing/lifespan references rather than supplying guessed imports.
- [x] Author the four sections covering input/output schemas, registration, descriptions, cleanup, blocking work, sanitized errors, transport behavior, caller-specific clients and in-process contract tests. Link authentication and Task 1 guidance instead of reimplementing it.
- [x] Add a concise FastMCP route in BEST_PRACTICES. Cross-link pagination and tool safety once their targets exist.
- [x] Review Focus 1: a Data Studio reader receives SDK-compatible guidance, and a standalone reader receives APIs verified for that package's version. Check that cancellation is not represented as rollback and source-defined tests are not described as executed.
- [x] Review and commit Task 2 files with sign-off as `docs: add version-aware FastMCP guidance` when committing is in scope.

## Task 3: Pagination guidance

**Consumes:** MCP discovery pagination specification for the selected protocol version; Compute, Cloud, Recovery and Pricing implementation/tests; Task 1 test criteria.

**Produces:** `docs/pagination.md#protocol-and-tool-results`, `#limits-and-continuation`, `#current-patterns`, and `#review-checklist`.

- [x] Trace each representative implementation's page size, total limit, aggregation, completion indicator, continuation and failure behavior. Label unsupported capabilities and gaps; do not turn a sample into repository-wide compliance evidence.
- [x] Explain discovery cursors separately from OCI business results. Document new-tool expectations for bounded retrieval, explicit aggregation, scope/filter consistency, budgets and truthful incomplete results; flag compatibility work before changing existing defaults.
- [x] Specify the partial-page continuation problem without mandating a universal envelope/helper. Cover next-link origin validation, repeated continuation values, fan-out, empty pages and changing collections.
- [x] Add the short owning pagination expectation and topic link to BEST_PRACTICES.
- [x] Review Focus 2 with a five-item backend page and a three-item total limit: the explanation must account for the two unreturned items before advertising lossless continuation. Also walk empty/non-final pages, failure after a successful page, and a rejected foreign-origin next link.
- [x] Review and commit Task 3 files with sign-off as `docs: define pagination contracts and limits` when committing is in scope.

## Task 4: Tool safety guidance

**Consumes:** Existing root/security/authentication policy, MCP annotation contract, Recovery annotations, Data Studio profiles/confirmation checks and API's exceptional CLI path.

**Produces:** `docs/tool-safety.md#operation-risk`, `#server-safeguards`, `#agent-authorization`, and `#uncertain-outcomes`.

- [x] Trace representative enforcement paths and annotations, separating source behavior from proposed requirements. Preserve package guidance and the existing subprocess exception boundary.
- [x] Author the impact matrix for reads, additive/reversible changes and destructive/irreversible/bulk/access-changing actions. Explain how cost and sensitivity can raise the risk of an otherwise additive action.
- [x] Cover validated exact targets, caller authorization, least privilege, supported preconditions, bounded execution, previews where available, sanitized audit evidence and partial success. Distinguish annotations, visibility and confirmation tokens from authorization.
- [x] Define agent behavior using task authorization that persists for covered targets. Make missing approval the final step after preparing a concrete action; ask again only when authorization or material scope is missing or changed.
- [x] Add the enforceable core and link to BEST_PRACTICES. Avoid promising dry runs, rollback or idempotency without backend support.
- [x] Review Focus 3 with a correct resource-name token but no human authorization, a timed-out delete, an expensive create, a previously authorized reversible update, and a bulk target change. Expect proportionate safeguards and no automatic replay of an unknown outcome.
- [x] Review and commit Task 4 files with sign-off as `docs: define proportional MCP tool safeguards` when committing is in scope.

## Skill evaluation protocol for Tasks 5–6

Use the available skill-authoring validation workflow during execution. Prepare raw fixtures and run baseline requests before adding the new skill; record actual failures, not an assumed failing outcome. Use clean evaluation contexts that do not inherit the desired answer. Personal Oracle MCP skills should not supply the control's guidance.

Keep fixtures and raw outputs in a temporary workspace; the outcome record captures source identity, prompt/case, observed behavior and result. GitHub writes must be intercepted by a controlled interface. Run the same meaningful cases with the new skill and correct demonstrated failures. For wording that shapes decisions, use a no-guidance control and at least five fresh-context repetitions per tested wording variant, reading flagged outputs manually. Pure reference checks do not need wording micro-tests. If a control already passes, do not manufacture a failure or add unnecessary prohibitions.

Structural validation uses the installed skill-creator's `scripts/quick_validate.py` against each skill folder, resolving that tool from the execution environment rather than committing a personal absolute path. It must report success for required names/descriptions, frontmatter and unfinished placeholders. Also check reference resolution. This does not replace behavioral evaluation.

## Task 5: Local review skill

**Files:** `.agents/skills/local-review/SKILL.md`; its `references/report-template.md` and `references/dependency-review.md`.

**Consumes:** Tasks 1–4, `docs/agent-development.md#validation-map`, native commands and the personal local-review skill as an authoring reference only.

**Produces:** `name: local-review`; a discriminating description for local/pre-PR review in this repository. Its report contract includes review scope; base/head/merge-base where applicable; staged/unstaged/untracked inclusion and fingerprint; summary; findings with severity/path/line/evidence/impact/remedy; check command, directory, scope and status; dependency/test/docs assessment; and residual uncertainty. This is the interface consumed by Task 6.

- [x] Prepare and run baseline cases: docs-only diff; one Moon-managed Python package; Common behavior change; excluded Python plus JavaScript/Java routing; dirty worktree with blocked tests; state changing during review. Record observed gaps.
- [x] Write the report reference and skill entrypoint using the report contract above. Return review content in the requested channel/file; do not require automatic report-file creation. A blocked check limits the result while allowing source review.
- [x] Write the conditional dependency reference: direct/resolved version and lock coherence; Common consumer impact; SDK/auth/user-agent compatibility; CLI command/option/denylist implications when relevant. Remove old Make and generated-metadata assumptions.
- [x] Define scoped validation from current native sources. From the repository root, affected Python source uses `moon run <server-name>:test` and `moon run root:lint`; shared Python behavior uses `moon run :test` and `moon run root:combine-coverage`. Dependency changes use the affected project's defined `:lock-check` and relevant build/install tasks. Route excluded packages and other runtimes through their native procedures, including JavaScript's explicit Moon tasks. Recheck commands at execution; do not run every package for a docs-only review.
- [x] Define snapshot preservation: distinguish branch versus local-only changes, include relevant untracked files, use isolation when needed, and recheck final state. No reset/clean/restore of user work.
- [x] Validate frontmatter/references and run controlled with-skill cases. Review Focus 4 passes when the report identifies the included local state, selects docs checks for docs-only work and labels blocked checks accurately. Common and other-runtime cases must select their actual validation routes.
- [x] Review and commit only Task 5 files with sign-off as `feat: add repository local review skill` when committing is in scope.

## Task 6: PR authoring skill

**File:** `.agents/skills/pr-authoring/SKILL.md`.

**Consumes:** Task 5's report contract, `.github/pull_request_template.md`, CONTRIBUTING, SECURITY, Git state and the available authorized GitHub interface.

**Produces:** `name: pr-authoring`; a discriminating description for PR drafting or draft creation from a local branch in this repository. Output is title/body, repository/base/head/draft status, publication scope and actual validation/review limitations; creation additionally returns the resulting draft URL.

- [x] Prepare and run baseline cases: docs-only drafting; matched versus stale review; selected fork-head/upstream-base; dirty changes absent from the remote head; missing tracking issue/unverified attestations; existing draft or unavailable authentication. Record observed gaps.
- [x] Write canonical-template selection and drafting instructions. Use the selected base's template, preserve its sections/checklist and replace placeholders. Describe behavior/compatibility, actual tests and relevant configuration. Preserve unknown author attestations and contribution requirements without inventing issue numbers or requiring an issue skill. A missing required tracking issue leaves the body draftable but blocks submission until that prerequisite is met.
- [x] Consume Task 5's report only when reviewed base/head and included state match. Distinguish reviewed dirty content from the committed PR diff; do not use elapsed age alone as a validity gate or impose a blanket review requirement for unrelated authoring requests.
- [x] Define publication conditions: a requested draft may be created once the exact target/head/body is reviewable and authorization covers necessary actions. Recheck state and existing PRs; resolve a necessary push within the user's scope. Drafting alone performs no publication. Use `--body-file` for CLI multiline content; stop on authentication or ambiguous creation outcomes without blindly creating duplicates.
- [x] Validate frontmatter/references and run with-skill cases through controlled GitHub writes. Review Focus 5 passes when the selected target/template/head are accurate, stale review is qualified, the missing required issue blocks submission while permitting drafting, and draft creation occurs only in the explicitly authorized case with prerequisites satisfied.
- [x] Review and commit only Task 6 files with sign-off as `feat: add repository PR authoring skill` when committing is in scope.

## Task 7: Routes and completion evidence

**Consumes:** All seven deliverables and their real check/evaluation results.

**Produces:** Root/shared routes for the five topics and two workflows; `outcome.md` recording the implemented scope, source identities, actual checks and remaining limits.

- [x] Add root/shared routes using the existing Read when / Context / Depends on / Evidence convention. Link applicable prerequisites and owning tests/commands. Avoid reproducing skill bodies, confusing proposals with policy, or copying topic rules into all 35 component guides.
- [x] Walk root-start cases for code/test quality, correct FastMCP library, pagination and mutation safety; then walk local-review-to-PR evidence handoff. Follow package guides when entering component source. Repair unreachable prerequisites or contradictory routes.
- [x] Check every changed Markdown link/anchor, skill reference and named source path; compare displayed native commands with definitions. Run skill validation for both folders and `git diff --check`; check untracked new files explicitly before staging.
- [x] Inspect the complete intended diff to confirm no issue skill/templates, application changes, generated output, dependencies or copied PR template entered it. Recheck all five Review Focus conditions against their owning task's results.
- [x] Write `outcome.md` with actual structural/behavioral results and limitations. Record blocked/unrun checks explicitly; do not claim application suites or live PR creation passed through fixture tests. Update this plan's task state only for completed work.
- [x] Review and commit Task 7's exact files with sign-off as `docs: route and verify repository workflow context` when committing is in scope. Present the final changes and evidence without implicitly publishing a PR.

## Execution boundary

The user subsequently authorized implementation. All seven tasks were completed inline in the existing feature workspace; independent agents supplied controlled skill evaluations and the final read-only review. Checked review/conditional-commit steps mean review is complete; committing was deferred, and their messages remain suggestions. No commit, push, public PR or live OCI operation was performed. The outcome records actual checks, scope decisions and limitations.
