# Shared authentication context: scope, reuse and outcome

Recorded 2026-10-06 for user feedback requesting a repository-level authentication guide, a ledger of all MCP servers, a direction to extend Common for missing use cases, preservation of Compute's local topic and explicit context-intent definitions.

## Scope and source roles

This documentation follow-up extends the staged [initial Common/Compute application](../apply-agent-context-guide/scope-and-reuse.md). Application sources/manifests remain at MCP commit `019fec4392667e99e97fac7baa69a08440835675`; pre-existing staged documentation and the user's edits are preserved. The earlier application review/evaluation records retain their recorded scope and are not reused as current passing results.

Reuse assessment: Common's README already owns API details and input contracts; root/BEST_PRACTICES own existing quality/auth requirements; Compute's topic explains its local paths. The material gap identified by the user is **repository-level integration and adoption visibility across servers**, so [docs/authentication.md](../../authentication.md) relates those sources, adds an all-server ledger and records the newly requested missing-capability direction. It does not duplicate the full Common API reference or invent migration completion. [Context conventions](../../agent-context.md#context-intents-know-do-now-proof-and-done) now define each existing intent with repository examples.

The ledger was built by enumerating all 34 component guides, checking tracked production-source imports and auth call sites, checking each native manifest and inspecting distinct CLI/SDK/HTTP, local OCI signing, non-Python and non-OCI paths. A local IoT function called `build_auth_context` is not counted as Common. API's CLI helper use is distinct from SDK-context use. Cloud's host/port credential selection remains explicit despite Common API use; Database's caller path is selected through request-token/request context. This is adoption-source review, not exhaustive authentication or security qualification.

## Delivered routes

Root/shared engineering and BEST_PRACTICES reach the shared guide/ledger. Common's integration route reaches the shared requirements and consumer evidence. Compute's local route/topic names the shared guide as a prerequisite and retains its native details. Each ledger row reaches the applicable broad guide, native manifest/guide and implementation evidence. Existing broad guide coverage and native procedures remain intact.

## Validation outcome

Executed on 2026-10-06:

- Checked all 34 ledger rows against tracked production sources and manifest declarations. Five implementations call Common APIs; four use the SDK context builder and API uses CLI-resolution helpers. Remaining rows distinguish 24 local OCI paths from five non-Python/non-OCI cases.
- Checked all 491 relative link occurrences and 89 Markdown fragments across the 12 pending documentation files (including the previous staged application). Root, Common and Compute routes reach the shared guide, appropriate local detail and source evidence. All targets/anchors resolve; no selected prerequisite cycle was found.
- Confirmed the nine files affected by this feedback are Markdown only, all 35 broad local guides retain their nine areas, root quality requirements are unchanged, other pre-existing Markdown files retain their content, and the pre-existing index/staged-diff fingerprint is unchanged.
- `git diff --check` and `git diff --cached --check` pass. No application source, manifest, task or test definition changed.
- A fresh read-only reviewer checked requirements, ledger classifications, integrations, intent definitions and routes. Review and author source inspection identified a draft claim that Database selected credentials by host/port; it was corrected to its actual request-token/request-context selection. Cloud's host/port dispatch gap remains recorded. The reviewer reported no outstanding Critical, Important or Minor documentation findings after correction. The final root legend link was subsequently checked by the author with the full link/diff check.

These are source/structural documentation checks, not authentication test executions or fresh-consumer trials. The one-off author checker lives outside the repository and is not an added application test suite. The feedback changes are left unstaged on top of the preserved prior staging.

The reviewer declined to judge runtime authentication success, caller isolation/security qualification, package installation, full migration compliance, application test/coverage results, live service behavior and agent-effectiveness evaluations. Those claims remain outside this documentation scope; no result was inferred from ledger status or reachable files.

## Evidence limits

Five servers use Common in the stated paths (four SDK integrations, one CLI helper integration); 24 use local OCI authentication/signing; five use another runtime or have no OCI credential path for this Python integration. These statuses derive from source and manifests, not package-install success, complete migration, test/coverage results, live authentication or agent-effectiveness trials. No application builds/lint/tests, service calls, new framework retrieval by an agent, or fresh-consumer evaluations are executed. Missing-capability support is an engineering requirement for future work, not an implemented library extension in this documentation increment.
