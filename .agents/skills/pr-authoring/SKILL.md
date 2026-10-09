---
name: pr-authoring
description: Use when asked to draft a PR title or description from a local branch in this MCP repository, fill its PR template, or create a draft PR.
---

# PR authoring

Produce an accurate description using the [canonical template](../../../.github/pull_request_template.md). Read [root instructions](../../../AGENTS.md), [CONTRIBUTING](../../../CONTRIBUTING.md), [SECURITY](../../../SECURITY.md) and relevant component guidance. Personal installed skills are not dependencies.

## Select scope and template

Draft content by default; create when requested. Identify target repository/base ref and SHA, head repository/branch/SHA, merge base, full branch diff and dirty state. Derive candidates from remotes/session context rather than hard-coding upstream or assuming `origin` is the destination. Resolve material ambiguity before publication. Detached/unpushed state can support a content draft; publication needs a concrete branch/head.

Explain local changes absent from committed/published content. A draft may describe intended dirty content, explicitly labeled, but a PR cannot include uncommitted files. Do not commit/discard them implicitly.

Use the selected base's `.github/pull_request_template.md`. Read the local copy if it represents that base, `git show <base-sha>:.github/pull_request_template.md` if available, or an authorized remote read at the selected SHA. Report inaccessible/missing templates without claiming retrieval. Resolve multiple applicable templates when selection is unclear.

## Fill the body

Return a title, complete Markdown body and unresolved facts. Preserve template sections/checklist and option-removal instructions. Explain the concrete problem, resulting behavior, motivation, dependencies and compatibility. Replace sample tests with actual results and reproducible command/directory details; report failed, blocked and not-run checks. Mark irrelevant configuration fields not applicable.

Use `Fixes #N` only when evidence establishes resolution; otherwise use a related reference. A missing required tracking issue leaves content draftable but blocks submission until addressed. Issue authoring is outside this skill. Sensitive vulnerabilities follow SECURITY.

Check only supported change-type and objective validation/documentation items. Personal attestations such as author self-review need author confirmation; independent review cannot supply it. Follow code-contribution OCA/signoff requirements without claiming automated verification or silently signing for the author. Surface missing submission prerequisites before publication.

## Review evidence

When supplied/requested, use the [local-review report contract](../local-review/references/report-template.md). Compare repository/base/head and included index/worktree/untracked identities to the actual PR content. Changed identity makes affected evidence stale; missing identity is unavailable. Date alone does not determine validity.

Report matching, stale, absent or incomplete review accurately. A draft PR may truthfully record tests not run or an old review; fresh review/passing tests are not blanket creation conditions unless policy or the user requires them. Route a requested local review to [local-review](../local-review/SKILL.md).

## Create the requested draft

Use an available authorized connector or `gh`. Local drafting needs no authentication. For publication, preflight access without requesting/displaying tokens; verify exact remote base/head and existing PRs. A failed lookup does not mean none exists. Return a matching existing PR rather than duplicating it; edits need an update request.

Make target, branches/SHAs, title/body, draft status, evidence limits and necessary push reviewable. Existing authorization covers the requested action; do not ask again solely because creation is a write. Resolve a necessary push within publication scope, surfacing branch/target ambiguity and respecting any no-push constraint. Prepare the concrete action before asking for missing authorization.

Immediately before writing, recheck state, prerequisites and existing PRs. Reevaluate material changes against authorization without silently substituting content/targets. Default to draft. With `gh`, use explicit `--repo`, `--base`, `--head`, `--draft`, `--title` and a temporary `--body-file`; avoid `gh pr create --dry-run`, which can push. Another publication state needs an explicit request and available capability.

For timeout/ambiguous creation, reconcile through lookup before retrying. Return the actual URL/actions only after success; simulated calls do not establish creation. Labels, reviewers, issue writes and merge are separate scope.
