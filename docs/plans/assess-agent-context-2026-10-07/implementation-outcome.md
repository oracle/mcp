# Context follow-up outcome — 2026-10-07

Implements the four findings in the [assessment](adoption-summary.md) on the user-requested branch `codex/agent-context-followup`, based on MCP `3a7cfd9623ec97ad7c365b9b77f28e459aefca8c`. The assessment remains unchanged as the pre-fix record.

## Scope and source roles

This maintenance pass updates current root/shared context and the Common, Recovery and Data Studio guides. Application code, manifests, commands, tests, native READMEs/changelogs, other component guides and historical adoption/application/evaluation records remain unchanged. No auth migration, new application requirement, live operation or consumer evaluation is included.

Used `agentstanza-adopt` with installed framework package `2217b49f6669db88d6fb1fef3a722969b751daa5`: adoption runbook, application guide, core guide profile, mapping questions and optionality conventions. The repository's [authoring procedure](../../agent-context.md#authoring-procedure) and [validation map](../../agent-development.md#validation-map) supply local procedures. Required framework resources were accessible; no external service retrieval was needed.

Revalidated the findings against the pinned baseline before editing. Native source and manifests establish current behavior/configuration; root/BEST_PRACTICES/Common contracts retain requirements; test definitions establish available checks. Historical results remain tied to their original sources and are not current passing evidence.

## Delivered fixes and reuse choices

| Finding | Context change | Owning sources reused |
| --- | --- | --- |
| F1: Recovery pre-3.0 description | Refreshed the [Recovery guide](../../../src/oci-recovery-mcp-server/AGENTS.md) with tool-family registration, auth/client factories, discovery/cache/caller boundaries, telemetry/deadlines and concern-specific test routes; removed obsolete local-auth/README conflict claims | Native [server](../../../src/oci-recovery-mcp-server/oracle/oci_recovery_mcp_server/server.py), [auth](../../../src/oci-recovery-mcp-server/oracle/oci_recovery_mcp_server/auth.py), [clients](../../../src/oci-recovery-mcp-server/oracle/oci_recovery_mcp_server/clients.py), [cache](../../../src/oci-recovery-mcp-server/oracle/oci_recovery_mcp_server/cache.py), tool/helper modules and [README](../../../src/oci-recovery-mcp-server/README.md); no copied auth topic or native startup procedure |
| F2: Common consumer/graph inventory | Updated [root](../../../AGENTS.md#architecture-and-dependencies), [Common](../../../src/common/AGENTS.md#architecture-and-dependencies), [shared register](../../agent-development.md#known-gaps) and [ledger](../../authentication.md#adoption-ledger). Six consumers and five explicit package Moon edges are distinguished from source use; Recovery is an SDK/HTTP user | All server manifests/production imports; package Moon files; Recovery's Common API call sites. New ledger snapshot is baseline `3a7cfd9`; the earlier outcome/counts remain historical |
| F3: Coverage description drift | Data Studio now records the native 90% gate and offline branch-coverage route; Recovery records 100%; removed the obsolete Data Studio gap from current root/shared guidance | Native [Data Studio manifest](../../../src/oracle-data-studio-mcp-server/pyproject.toml)/[development route](../../../src/oracle-data-studio-mcp-server/README.md#local-development) and [Recovery manifest](../../../src/oci-recovery-mcp-server/pyproject.toml); no threshold or tests changed |
| F4: Common version-gap drift | Narrowed current Common/shared gap text to README OCI 2.179.0+ versus manifest 2.185.0+; recorded matching FastMCP 3.4.5+ in 3.x | [Common requirements](../../../src/common/README.md#package-requirements), [manifest](../../../src/common/pyproject.toml) and existing [HTTP contract](../../../src/common/README.md#http-idcs-authentication); no dependency remediation or duplicate API explanation |

The ledger retains all 34 server rows: six Common users (five SDK integrations plus API CLI helpers), 23 local OCI authentication/signing cases and five other-runtime/non-OCI cases. Common dependency declarations, production imports, package graph edges and runtime success remain separate claims. DB Observability remains the declared consumer without a package Moon file.

## Verification

Executed author documentation/source checks against the six-file guidance diff and the assessment/follow-up records:

| Check | Result and scope |
| --- | --- |
| Local links and anchors | 49 context Markdown files, including all component guides and historical records: all 1,651 local link occurrences and 418 fragments resolve |
| Guide coverage and preservation | All 35 local guides retain nine engineering areas and root/shared/index routes; the other 32 component guides are byte-for-byte unchanged |
| Common inventory and ledger | Native declarations and tracked production imports identify the same six consuming server scopes as the ledger; five explicit package Moon edges match the Common guide. All 34 rows remain, classified as 6 Common, 23 local OCI and 5 other cases |
| Coverage and version descriptions | Guide coverage-gate statements match native TOML definitions, including Data Studio 90 and Recovery 100. Common FastMCP requirement alignment and remaining OCI discrepancy match native README/manifest |
| Source and route review | Recovery registration, Common calls, request-context/local-credential guard, cache partitioning, region queries, client/telemetry wrappers and test leads reviewed; selected root/component walks recorded below |
| Policy, history and diff scope | Root validation/editing/changelog/quality requirements and historical plan/outcome files are byte-for-byte unchanged. Changes are six existing Markdown files plus the assessment and this follow-up record; no application/native configuration changes |
| Whitespace | `git diff --check` passes; both new records pass a separate new-file whitespace/final-newline check |

The structural/inventory/manifest checks used a one-off Python checker outside the repository and read-only Git/search/source inspection. These are executed documentation checks, not application tests, achieved coverage, a fresh independent review or an agent-effectiveness trial.

### Selected route review

These are author-operated document/source walks, not fresh-consumer trials:

- Root → shared component map → Recovery guide reaches owning tool families, auth/client code and matching tests. Direct Recovery starts reach root requirements, shared integration and Common auth/HTTP prerequisites. The source's request-context dispatch and HTTP local-credential refusal remain distinct from listener selection and live auth evidence.
- Root/Common → shared ledger → six manifests and importing server scopes reaches Recovery; Common's explicit graph links reach API, Cloud, Database, Document Understanding and Recovery Moon files. DB Observability's absent package edge is explicit.
- Root/Data Studio → validation map/native development/manifest exposes the configured 90% gate, and direct Recovery validation exposes 100%. Neither is presented as achieved coverage.
- Common setup/gap routes reach the current README/manifest and preserve only the observed OCI mismatch. Existing HTTP contract remains the owning explanation for scope qualification and CIMD options.

Selected prerequisites were reviewed as prerequisites, not recursively expanded ordinary links. No new prerequisite cycle was introduced; Common/Recovery guide references are navigation and the selected auth dependencies are root/shared requirements and native Common contracts.

## Remaining limits

No application imports, installations, builds, lint, server tests, coverage, live authentication/OCI/database/Podman operations, paid tracing or new agent evaluations ran. Context consistency is the outcome; deployed security, full auth compliance, achieved coverage and agent effectiveness remain unverified.

Previously disclosed application/policy/validation gaps remain outside this maintenance pass, including Compute/local OCI auth departures, Cloud credential dispatch, DB Observability dependency constraints, Common's OCI version discrepancy, JavaScript subprocess/isolation limits, Java test/coverage limits and excluded-package validation gaps. Context-only corrections require no runtime changelog entry.

Future maintenance should recheck affected guides/ledger when their owning source or manifests change. Any application remediation or consumer evaluation needs its own scope and evidence. No additional context expansion is proposed by this follow-up.
