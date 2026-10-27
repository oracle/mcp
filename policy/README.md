# Repository policy gate

Added or changed `src/<package>/pyproject.toml` files, except Common's, must
declare numeric `tool.coverage.report.fail_under` between 90 and 100. Missing or
malformed settings, deleted/renamed manifests, and symlinks fail. This checks the
declared threshold; measured coverage, overrides, and unchanged manifests are
outside its scope.

The [workflow](../.github/workflows/policy.yml) uses the protected base commit's
policy, verifier, and locked dependencies to inspect the PR's committed Git blobs.
It verifies merge parents, never executes candidate code, and denies parsing,
validation, or evaluation errors. It supports PRs to `main`, without a merge queue.

[cedarpy](https://github.com/k9securityio/cedar-py) runs native Cedar in-process
using published wheels; no Rust compiler is needed. The binding discards policy
and schema warnings, so warning-only diagnostics are not enforced.

## Local validation

From the repository root:

```sh
uv sync --project policy --locked --no-build --python 3.13.15
policy/.venv/bin/python -I -m unittest discover -s policy/tests -v
moon run root:lint
policy/.venv/bin/python -I policy/check.py \
  "$(git rev-parse main)" "$(git rev-parse HEAD)"
```

The CLI requires full commit IDs and ignores uncommitted changes. Maintainers
must validate proposed policy/verifier changes locally; CI uses the approved base.

## Activate enforcement

Humans listed in [CODEOWNERS](../CODEOWNERS) approve policy changes. After
bootstrapping this change, a maintainer must:

1. Require PRs, code-owner approval, dismissal of stale approvals, and up-to-date
   branches on `main`. Restrict review dismissal and bypasses; agent credentials
   must not control approving accounts, bypass identities, or repository settings.
2. Use an organization/enterprise ruleset to [require this exact workflow](https://docs.github.com/en/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#require-workflows-to-pass-before-merging)
   from this repository's protected `main`. Requiring a status name alone is
   insufficient. Without required-workflow support, enforcement needs a separately
   trusted check publisher.
3. [Allow `pull_request_target`](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)
   in the Actions event policy. Keep the job read-only, free of secrets, and never
   execute candidate code.
4. Verify with disposable PRs that lowered thresholds block merging, policy and
   ownership edits require current owners, duplicate check names cannot bypass
   enforcement, and new pushes invalidate approvals. Do not merge these test PRs.

Enforcement is active only after these settings and GitHub checks are verified.
