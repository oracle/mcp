---
name: local-review
description: Use when asked to review local, committed, staged or uncommitted changes in this MCP repository, or perform a pre-PR review.
---

# Local review

Review the requested change and return evidence-backed findings plus validation limits. Read [root instructions](../../../AGENTS.md), [shared context](../../../docs/agent-development.md#start-here), [BEST_PRACTICES](../../../BEST_PRACTICES.md) and applicable component guides. Use [references/report-template.md](references/report-template.md) for the report contract, also consumed by PR authoring.

## Establish the snapshot

Honor an explicit branch, commit, staged-only or worktree scope. For a general local review, include the branch diff and relevant staged, unstaged and untracked changes; state that choice. Identify repository, base ref/SHA, HEAD, merge base and included paths. Resolve a base ambiguity only when it materially changes the review.

Inspect full relevant files. `git diff <base>...HEAD`, `git diff --cached`, `git diff` and untracked contents represent different scopes. Record identities for included dirty content, with fingerprint method and path list; mark unavailable inputs rather than inventing a hash. Exclude unrelated secrets and ignored output.

Preserve user changes. Use an isolated snapshot when checks would alter reviewed files, including selected dirty content where applicable. Do not reset/clean/restore user work to manufacture a clean review.

## Review and validate

Trace correctness, security, compatibility, operational effects and meaningful test gaps. Use [code quality](../../../docs/code-quality.md#review-criteria), [test quality](../../../docs/test-quality.md#review-criteria) and relevant [FastMCP](../../../docs/fastmcp.md), [pagination](../../../docs/pagination.md) or [tool safety](../../../docs/tool-safety.md) guidance. Optional style preferences are not defects.

Choose checks from the [current validation map](../../../docs/agent-development.md#validation-map) and native definitions:

- Docs/context: source alignment, links/anchors, routes and diff hygiene.
- Moon-managed Python source: affected server tests/root lint; shared behavior also needs root-required broad tests/combined coverage and consumer review.
- Dependencies/packaging: appropriate lock/build/install checks; read [references/dependency-review.md](references/dependency-review.md).
- Excluded Python, JavaScript and Java: native procedures and explicit enforcement/discovery gaps. Missing commands do not justify inventing Moon tasks.

Run relevant authorized checks when feasible. Record actual command, directory, snapshot/scope, status and coverage/discovery evidence. Blocked checks permit source review but not a passing validation claim. Preserve at-least-90% and stricter native gates. Do not silently upgrade dependencies or invoke live mutation/service tests to bypass a blocker.

## Return the review

Fill the report contract even when evidence is missing. Findings need severity, path/line, evidence, consequence and bounded remedy. Separate optional suggestions and uncertainty. “No findings in the inspected scope” does not establish unavailable checks passed.

Recheck base/head and included identities at the end; identify stale evidence if state changed. Return the report in the requested channel/file without an unsolicited artifact. PR authoring must distinguish reviewed dirty content from the committed/published head.
