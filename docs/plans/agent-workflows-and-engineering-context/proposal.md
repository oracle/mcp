# Repository skills and engineering context proposal

Status: implemented on 2026-10-07 following the [implementation plan](implementation-plan.md); see the [outcome](outcome.md) for the final scope, evidence and limitations. Issue authoring remains deferred. This proposal records design intent; the linked owning guides and skills contain the implemented instructions.

Explored on 2026-10-07 against `6e6c3e5121a7ac5000e57648ca51370f75da9e34` on `codex/agent-context-followup`. Current scope: two repository skills and five engineering topics. The user selected guidance for both server safeguards and agent confirmation, proportional to the operation's impact. Issue authoring and issue templates are deferred.

## Placement and reuse

Follow the existing [context authoring conventions](../../agent-context.md#authoring-procedure). Preserve the broad root and component guides; give them routes to focused explanations. Keep shared requirements in [AGENTS.md](../../../AGENTS.md) and [BEST_PRACTICES.md](../../../BEST_PRACTICES.md), procedures in skills, and commands in their native definitions. A proposal or example does not establish current server behavior.

Three approaches were considered:

| Approach | Benefit | Cost and conclusion |
| --- | --- | --- |
| Expand only BEST_PRACTICES and embed everything in each skill | Few new files | Makes the broad guide long and duplicates explanations across skills |
| Focused topic guides, small policy additions, two lean skills | Clear ownership, selective loading, reusable review criteria | Requires maintaining links; recommended |
| Add a rules framework, shared runtime helpers and workflow automation together | More automation | Mixes documentation with application changes before contracts and gaps have been established; defer |

Proposed layout:

```text
.agents/skills/
  pr-authoring/SKILL.md
  local-review/SKILL.md
  local-review/references/report-template.md
  local-review/references/dependency-review.md
docs/
  fastmcp.md
  code-quality.md
  test-quality.md
  pagination.md
  tool-safety.md
```

The five documents warrant separate explanations: framework compatibility, implementation choices, test design, collection semantics, and mutation safety each combine several owning sources. Keep them focused and cross-link overlapping concerns. Supporting skill files are justified only where they keep the entry-point instructions concise; no scripts are proposed initially.

## 1. PR authoring skill

Use the existing [PR template](../../../.github/pull_request_template.md) rather than storing another copy. Preserve its sections and author checklist. Replace sample test entries with actual checks, explain inapplicable configuration fields, and leave unsupported author attestations unchecked. Use a closing issue reference only when the change actually resolves that issue.

Reuse the personal Oracle MCP PR Authoring skill's snapshot, template selection, evidence handling and draft-creation mechanics. Adapt its publication rules to the user's actual authorization; do not introduce a requirement to ask again after the user has already requested creation of the specific draft PR.

Workflow:

1. Identify the target repository, base branch, head branch, commits, merge base and local changes. Inspect the whole intended PR diff, not only the latest commit. Explain which local changes are absent from the pushed head.
2. Select the target base's template. Read the local copy when it represents that base; retrieve the target base's version when needed. Ask about materially ambiguous targets or multiple applicable templates.
3. Read [CONTRIBUTING.md](../../../CONTRIBUTING.md): issue tracking, contribution agreement and sign-off requirements. Report missing evidence without claiming the author signed the agreement. If the required tracking issue is missing, report the gap and keep the PR draft useful; submission waits for that prerequisite. Do not invent an issue or depend on a deferred issue-authoring skill. Drafting a PR alone does not authorize posting an issue. Sensitive vulnerability details follow [SECURITY.md](../../../SECURITY.md).
4. Produce a concise title and completed body explaining behavior, compatibility, validation and remaining limitations. Incorporate a local review only if its base/head and local state match the proposed change. Source identity matters more than an arbitrary age limit.
5. Return the draft by default. When creation is requested, make the exact target, branches, title, body and draft status reviewable; recheck branch state and existing PRs, then create the draft within the authorized scope. Resolve a necessary push from the user's publication request and branch state; surface uncertainty before writing. Do not bundle unrelated repository mutations.

GitHub access should be capability-based: use an available authorized connector or `gh`, with read-only preflight and `--body-file` for multiline CLI bodies. This checkout currently has only `origin`, pointing to a fork. The skill must establish the intended PR target rather than infer that every PR belongs in the fork or hard-code the public upstream.

Acceptance examples: documentation-only PR; server change with matching review evidence; dirty worktree that differs from the pushed head; fork head/upstream base; existing draft PR; stale review snapshot; unavailable authentication. Check that none produces invented validation or an unauthorized publication.

## 2. Local code review skill

Reuse the personal Oracle MCP Local Review skill's evidence-backed findings, snapshot tracking, dependency checks and residual-risk reporting. Replace its removed Makefile commands and generated-package-metadata assumptions with the current [validation map](../../agent-development.md#validation-map), manifests and native task definitions.

Support branch, committed, staged and unstaged review scopes. Record base/head and the included local state, including relevant untracked files. Findings need a concrete path/line, evidence, impact and bounded remedy. Prioritize correctness, security, compatibility and test gaps that could hide defects; keep optional style preferences separate from defects.

Choose checks according to impact:

- Documentation/context: source alignment, links/anchors, applicable routes and diff hygiene.
- Moon-managed Python source: affected server tests and root lint; additional native lock/build/install checks when packaging or dependencies change.
- Shared behavior across Python servers: the root-required multi-server tests and combined coverage, with Common consumers identified from current declarations and source use.
- Excluded Python, TypeScript and Java: package-native procedures and their documented limitations.

CI includes lint, lock, install, test, check and build tasks; distinguish local review evidence from a claim that all CI checks passed. An isolated snapshot may be needed for build/install commands that would alter the active worktree. Never reset, clean or overwrite the user's changes to manufacture a clean review.

Report each check as passed, failed, blocked or not run. A blocked test does not prevent source review; it limits the completion claim. The report reference should capture the reviewed snapshot, findings, dependency/test/documentation assessment, validation and remaining uncertainty. Recheck the snapshot before passing review evidence to PR authoring.

Acceptance examples: docs-only diff; one Python server; Common change; Moon-excluded package; JavaScript or Java change; dependency update; dirty worktree; blocked checks; state changing during review.

## 3. FastMCP best practices

Create `docs/fastmcp.md` for repository-specific framework guidance, linked from BEST_PRACTICES and the shared engineering map. Existing structure, Pydantic parameter and Common authentication requirements remain with their owners.

Start by identifying the import and manifest version. This repository includes both standalone `fastmcp` imports and the Python MCP SDK's `mcp.server.fastmcp` class, notably in Data Studio. Examples and API recommendations must fit the selected implementation; avoid treating similarly named libraries as interchangeable or upgrading dependencies as part of context authoring.

Cover typed inputs and output contracts, registration/discovery, useful tool descriptions, lifespan/client cleanup, caller isolation, synchronous SDK work in async handlers, sanitized failures, transport behavior and deterministic in-process testing. Link pagination, test quality and tool safety for their detailed contracts. Review examples against the package's resolved dependency version; do not copy evolving upstream documentation blindly.

Useful sources include [FastMCP 3.4.5 tool documentation](https://github.com/PrefectHQ/fastmcp/blob/v3.4.5/docs/servers/tools.mdx) and [FastMCP v3 client transports](https://gofastmcp.com/v3/clients/transports). The latter documents in-memory client/server testing; local Cloud tests already use that pattern. Framework cancellation or timeouts must not be described as proof that an external mutation was rolled back.

Acceptance: readers can select the correct library/version and follow examples without conflicting with Common's HTTP isolation or package-owned lifecycle.

## 4. Code quality: rules and explanations

Use both. Add a small set of observable requirements to the existing root editing rules and BEST_PRACTICES; put rationale and good/bad examples in `docs/code-quality.md`. Avoid a separate agent-specific rules mechanism or a second policy owner.

Proposed rules address unnecessary pass-through wrappers, speculative abstractions, duplicated shared logic, broad exception handling that silently returns success-like defaults, unjustified type/lint suppressions, comments that merely repeat code, and unrelated cleanup. Prefer the smallest implementation that satisfies the actual behavior and preserves native contracts.

Explain valid exceptions: a short function can enforce a boundary, adapt an interface or provide a meaningful test seam. Length and perceived AI authorship are not quality criteria. Review a concrete maintenance or correctness cost rather than guessing how code was generated.

Acceptance: examples make each proposed rule reviewable without imposing blanket bans on helpers, abstractions or defensive checks.

## 5. Test quality guidelines

Expand the sparse test section in BEST_PRACTICES with the minimum expectations, linking `docs/test-quality.md` for design guidance. Preserve the existing at-least-90% coverage requirement and stricter package gates, such as Recovery's 100%. Coverage is a floor, not a demonstration of meaningful assertions.

Cover behavior-oriented assertions; realistic boundary data; regression cases that fail for the intended defect; expected failure/error contracts; authentication and caller isolation; exact derived user-agent assertions; pagination boundaries; mutation refusal; and fixtures that restore environment, caches and monkeypatches. Mock external services at their boundary while exercising real conversion, validation and result handling where relevant. Use parameterization when cases express the same behavior; avoid test counts and line coverage as goals in themselves.

Prefer deterministic offline tests. Add in-memory MCP contract tests when registration, schema, serialization or error behavior could fail independently of a direct function test. Live service/end-to-end validation stays separate with explicit prerequisites and evidence limits; the normal suite should not need credentials or accidental cloud mutations.

Acceptance: guidelines distinguish meaningful tests from tautological mocks, excessive implementation coupling and coverage-only tests, while preserving each runtime's native tooling.

## 6. Pagination

Create `docs/pagination.md` to distinguish protocol discovery pagination from business-data pagination. The [MCP 2025-11-25 pagination specification](https://modelcontextprotocol.io/specification/2025-11-25/server/utilities/pagination) applies to tools, resources, resource templates and prompts discovery lists. It does not prescribe the result envelope of an OCI tool call.

For business results, explain single-page retrieval versus bounded aggregation, backend page size versus total item limits, opaque continuation values, scope/filter consistency, empty pages, changing collections, deadlines and partial failure. Make incompleteness and the ability to resume explicit. If a total limit cuts through a backend page, a backend next-page token alone can skip unreturned items; document the supported continuation strategy rather than promising lossless resumption automatically.

Use a source-based comparison of Compute's explicit page loops with optional total limits, Cloud's aggregation/projection and more-results reporting, Recovery's page/aggregation controls, and Pricing's bounded traversal with next-link origin validation. The Compute description was corrected during implementation source review. These are examples of different current contracts, not a finding that all servers implement the proposed guidance.

Propose bounded defaults for new collection tools and explicit opt-in to broad aggregation; flag compatibility implications before changing existing defaults. Review next-link validation, repeated cursor handling, fan-out budgets and tests for first/middle/final/empty/error/truncated pages. Do not add a universal pagination helper or response envelope in this increment.

Acceptance: callers can tell whether results are complete, what a limit means and whether/how to continue, without assuming every tool has the same shape.

## 7. Destructive and mutating tool calls

Create `docs/tool-safety.md` with two responsibilities: server enforcement and agent execution behavior. Keep the core proposed requirements in BEST_PRACTICES, with a short root route. Use an impact matrix:

| Operation | Server safeguards to consider | Agent behavior |
| --- | --- | --- |
| Read | Caller authorization, sensitive-data controls, bounded work | Proceed within the task's authorized scope |
| Additive or reversible change | Validated targets, least privilege, truthful results; safe retry/idempotency where supported | Use existing task authorization; clarify material ambiguity rather than asking on every write |
| Destructive, irreversible, bulk or access-changing action | Exact scope, appropriate preconditions, bounded execution, stronger authorization and confirmation mechanisms where warranted | Establish specific authorization for targets and consequences; prepare a reviewable action before requesting any missing approval |

Risk depends on data sensitivity, reversibility, cost, blast radius and authority changes, not just the tool's verb. Creating an expensive resource can warrant stronger safeguards than deleting a disposable local artifact. Existing authorization persists while the actual target and scope remain covered.

Explain accurate `readOnlyHint`, `destructiveHint`, `idempotentHint` and `openWorldHint` annotations, while retaining actual server-side authentication and authorization. The [MCP annotation contract](https://modelcontextprotocol.io/specification/2025-11-25/schema#toolannotations) explicitly treats them as hints. Generic API/SQL/CLI tools require analysis of the selected operation; their names alone do not establish safety.

Source examples: Recovery declares read-only annotations; Data Studio has access profiles and resource-name confirmation checks; API exposes the repository's exceptional CLI path. A caller-supplied confirmation string is an accidental-target check, not proof of human consent. Profiles and visibility controls also do not replace caller authorization.

Cover previews/dry runs where the backend supports them, target IDs and bulk scope, backend preconditions such as ETags when available, sanitized audit evidence, partial success and ambiguous outcomes. A timeout does not justify replaying a mutation: reconcile status or rely on a backend-supported idempotency mechanism. Do not invent rollback or dry-run capabilities.

Acceptance: representative read, reversible update, costly create, destructive delete, bulk change and generic-operation scenarios select proportionate safeguards and avoid both unauthorized execution and repetitive confirmation.

## Implementation sequence and validation

1. **Create the implementation plan.** Capture the two-skill scope, file responsibilities, task dependencies and acceptance checks. Default to draft content for PR authoring requests; create a draft PR when explicitly requested.
2. **Author shared guidance.** Create the five topic documents; update their owning BEST_PRACTICES sections and root/shared routes. Walk representative reader tasks and verify current implementations versus proposed requirements. Add component-specific links only where they help the local task.
3. **Build local review.** Use the current command map and shared quality guidance. Validate the report format and scope selection before making PR authoring consume its evidence.
4. **Build PR authoring.** Consume the canonical template, contribution rules and matching local review evidence. Validate fork/base/head selection and authorized draft creation separately from content drafting.
5. **Check and record the result.** Validate skill frontmatter and references, links/anchors, source/version alignment and `git diff --check`. Exercise task scenarios before and after adding the skills, using controlled GitHub interfaces without public mutations. Record what was actually evaluated; structural checks alone do not establish effective skill use. Use relevant native checks if implementation introduces scripts or application changes.

These can be reviewable increments on the current branch or separate follow-up changes. The shared guidance establishes criteria; local review consumes them; PR authoring consumes review evidence and any supplied tracking issue. Issue authoring is a separate future increment.

## Evidence and limits of this exploration

Reviewed root/shared context, BEST_PRACTICES, the PR template, contribution/security instructions, Moon/CI definitions, personal PR/local-review skill sources, and representative source/tests in Common, Cloud, Compute, Recovery, Pricing and Data Studio. The personal skills are design references available during authoring, not dependencies that contributors must install. No repository issue templates or `.agents/skills` directory existed at the reviewed baseline.

External sources were reviewed on 2026-10-07. Some requested upstream testing, lifespan and version-tagged transport URLs could not be retrieved. The v3 transport page and existing Cloud test source support the proposed testing direction; precise lifespan APIs and all runnable examples still need package/version verification during implementation. The 2025-11-25 MCP references describe the selected version, not a claim that it is the latest specification.

This is a focused source review and proposed plan. It is not a repository-wide code-quality, pagination or mutation-safety audit, and no application tests, live OCI operations, skill behavior trials or GitHub publications were performed during this exploration.
