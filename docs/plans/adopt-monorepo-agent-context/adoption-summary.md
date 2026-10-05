# Clean monorepo-agent planning summary

Status: **Approved sequential implementation in progress. Shared/root guidance is drafted; local guides and final review are pending.**

## Scope and identities

- Branch: `codex/monorepo-agent-context-clean` in the `dustin-sale/mcp` fork.
- Baseline: fork local `main` at `d0e442b3ddcffe05c6f366c14dac42548641b60f`; no remote fetch or latest-remote claim.
- Selected guide scopes: root, Common, Compute, Cloud, JavaScript and Java toolkit.
- Broad-guide reuse source: `03faa20e23753a4a148839243382c7d3b11dac5e`; framework reviewed draft: AI Pit Crew `c9b1724`.
- Only the four planning documents were copied from prior planning commit `c4a36c7` and revised. No prior commit history, pagination adoption files or application/tooling changes were imported.

## Executed work and findings

Created a branch directly at local main, reassessed current sources/commands, and updated the [design](design.md), [reuse assessment](reuse-assessment.md) and [implementation plan](implementation-plan.md) for that baseline.

The main baseline differs materially from the pagination-based plan: Makefile remains alongside Moon, JavaScript npm validation scripts exist, Common has three declared consumers, and Compute/Java lack later fixes and test additions. These facts replace the previous assessment; unchanged-source assumptions are limited to the inspected matching packages/files.

Guidance adaptation will preserve shared/native source ownership, nine-area informational coverage and explicit gaps. Common README/manifest differences, Compute legacy auth, JavaScript's root-policy conflict/isolation limits and Java discovery/coverage limits remain visible without remediation outside scope.

## Validation and next increment

Before delivery, check the planning documents' local links/anchors/source paths, command definitions, diff scope and branch ancestry against main. Record exact results and commit identity in the delivery message. No server suites, builds, dependency installation, live service or behavior evaluation ran.

Review the revised implementation plan, then create the selected root/shared/component engineering guides sequentially. Broader adoption, policy/code remediation and agent trials remain separately selected work.

## Implementation progress

Task 1 adds root orientation/context routes and `docs/agent-development.md` with stable shared anchors, native validation sources and scoped gaps. Existing validation, auth, subprocess and changelog policy is preserved. Local guide targets are labeled pending until created. Documentation-only checks are recorded per task; no server test result is claimed.

Task 1 review walked shared orientation, native entry points, auth/dependency sources, runtime-specific validation definitions and gap/evidence routes. The scoped checker resolved 121 local links and 16 fragments across the first six documents; exact totals are confirmed by its executed output. No policy exception or runtime validation is claimed.
