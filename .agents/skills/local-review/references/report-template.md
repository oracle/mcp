# Local review report contract

Use this structure, keeping sections concise. Unknown values remain unknown. Record repository identity and relative paths, not a machine-specific checkout path. PR authoring accepts chat or file reports; no mandatory report store or age-based expiry exists.

```markdown
# Local review: <change>

## Snapshot

- Repository and requested scope:
- Base ref/SHA; HEAD SHA; merge base (or not applicable):
- Included committed, staged, unstaged and relevant untracked paths:
- Dirty-content identities/fingerprint and method (or unavailable):
- Final state check: unchanged / changed / unavailable; evidence affected:

## Summary

<Behavior reviewed, recommendation and material evidence limits.>

## Findings

<Findings, or "No findings in the inspected scope" with its limits.>

- [P0/P1/P2/P3] path:line — title
  - Evidence:
  - Impact:
  - Bounded remedy:

## Validation

| Check/command | Directory | Snapshot and scope | Status | Evidence/limits |
| --- | --- | --- | --- | --- |
| ... | repo-relative directory | ... | passed / failed / blocked / not run | ... |

## Dependency, test and documentation assessment

<Dependencies/consumers; assertions/coverage; compatibility, README/examples
and changelog. "Not applicable" needs a scope-based reason.>

## Residual uncertainty and optional suggestions

<Unverified behavior, missing checks, snapshot limits and optional polish.>
```

For dirty content, identify each included path and its relevant index/worktree contents together with base/HEAD and statuses. Describe fingerprint method, ordering and included paths; a hash alone cannot be reproduced. Use available hashing/snapshot tools without exposing contents or secrets. Staged-only review identifies index content; a worktree-only hash cannot prove staged identity. Missing inputs make matching evidence unavailable.

P0: immediate severe security/data-loss failure. P1: likely correctness, compatibility, reliability or security defect to address before merge. P2: material but less urgent defect/test gap. P3: small evidence-backed improvement. Grade actual impact; keep preference-only advice outside findings. Missing live validation is uncertainty unless it exposes a concrete defect or unsupported claim.
