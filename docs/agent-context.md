# Authoring and maintaining repository context

These are the context conventions for this MCP monorepo. Use them when adding or updating engineering guides, topic explanations or context routes. Ordinary engineering work starts with [shared engineering context](agent-development.md#start-here) and the applicable component guide. Application policies, permissions and engineering completion remain owned by the repository and its tools.

## Locations and owning sources

| Material | Existing location and role |
| --- | --- |
| Repository instructions and discovery | [Root AGENTS.md](../AGENTS.md); shared policies and task routes |
| Shared engineering orientation | [agent-development.md](agent-development.md); component index, validation definitions and known gaps |
| Component orientation | `src/<component>/AGENTS.md`, including [Common](../src/common/AGENTS.md) and [Compute](../src/oci-compute-mcp-server/AGENTS.md); broad engineering context and local routes |
| Shared policies and contracts | [BEST_PRACTICES.md](../BEST_PRACTICES.md), root instructions, the [shared authentication guide and ledger](authentication.md), and owning library documentation such as [Common's authentication contract](../src/common/README.md#authentication-module) |
| Local topic explanations | Existing native README sections first; `src/<component>/docs/<topic>.md` when a material explanation gap warrants a document, as with [Compute authentication](../src/oci-compute-mcp-server/docs/authentication.md) |
| Commands, interfaces and validation | Native manifests, source, tests, scripts and [Moon definitions](agent-development.md#validation-map); map these in place |
| Scoped change records | Existing `docs/plans/<change>/` convention; [this application bundle](plans/apply-agent-context-guide/scope-and-reuse.md) is separate from the [original adoption bundle](plans/adopt-monorepo-agent-context/adoption-summary.md) |

### Context intents: Know, Do, Now, Proof and Done

These labels explain **why a source is useful for the selected task**. They help people and agents interpret a route; they do not change the source's authority, grant execution permission or require a loading order.

| Intent | Question it answers | Example in this repository / interpretation |
| --- | --- | --- |
| **Know** | What do I need to understand, and what requirements apply? | [Shared authentication](authentication.md), architecture, native contracts and local behavior explanations. Distinguish requirements from descriptions and proposals |
| **Do** | How is the relevant work performed? | [Validation map](agent-development.md#validation-map), native task definitions and documented procedures. Read prerequisites and effects; a route is not permission to execute |
| **Now** | What is the scope and current direction of this active change? | A selected `docs/plans/<change>/` bundle. Read its status and decisions; a proposal does not become approved through this label |
| **Proof** | What supports this claim, and what was actually checked? | Source/interfaces for implementation claims; test definitions for available checks; actual run reports for execution results. The label does not turn a test definition into a passing result |
| **Done** | What historical change and outcome should I consult? | A completed change's scoped record/history. Read its recorded source state and limitations; an archived or completed record alone does not certify correctness |

A source may serve several intents; choose the relevant section and scope. These definitions make the existing routing vocabulary explicit and do not require new directory names, placeholders or copies. This repository uses its native docs and task stores, and root change bundles state their actual scope. Native outputs remain with their owning tools; there is no required Done/archive tree or new action wrapper.

Broad root/component guides retain scope and ownership, entry points, setup/build/run, validation, architecture/dependencies, security, change impact, gaps and workflow/routes. A focused topic document adds depth to a concern; it does not replace that engineering orientation. Named ownership and unverified capabilities remain explicit gaps where the sources do not establish them.

## Authoring procedure

1. State the reader's task and affected scopes. Read root and applicable nested instructions, then inspect the owning documents, interfaces, source, tests and command definitions. Check for a managed/generated notice before editing guidance; use its declared editable source and regeneration procedure if present.
2. Decide reuse, update or creation before writing. Map an adequate explanation directly. Update an existing owning document if it lacks a material detail. Add an explanation when several sources need interpretation together or no adequate explanation exists. If no source establishes a policy or intended behavior, identify the question and observations instead of inventing a contract.
3. Keep genuinely shared requirements with their existing owners and local behavior with its component. Link shared prerequisites rather than copying them into every guide. Show current behavior, intended requirements and unresolved differences explicitly; an observed departure is not an approved exception.
4. Make each explanation's purpose, applicability and standing understandable in ordinary prose. Use existing terminology such as current implementation, shared requirement, proposal or historical evidence; no new frontmatter schema or mandatory headings are required.
5. Add or update applicable root/component mappings. Walk both entry points and check links, prerequisites and evidence roles. A direct root link into a component preserves that component's applicable instructions.
6. Record the scope and outcome of the selected review using the team's change process. Review concrete changes before broader adoption. Source review and reachable routes do not establish effective agent use or passing application checks.

### Mapping convention

Use the existing `Read when / Context / Depends on / Evidence` table, or equivalent readable prose, to expose four answers: the relevant task/scope, the specific target, concrete prerequisites and where claims can be checked. Resolve relative links from the declaring document, independently of a command's working directory. Read relevant declared prerequisites before dependent context; ordinary navigation links are not recursive dependencies. Identify missing targets, inaccessible references or cycles without claiming the affected route was satisfied.

Map specific sections or useful indexes. A file in `docs/` may be guidance, a proposal, evidence or history; storage alone does not determine authority or relevance. Topic links and evidence pointers do not import all destination instructions. Root guidance delegates the context-authoring method described here; repository policies and native procedures govern engineering work.

## First focused topic: Common and Compute authentication

For server integration requirements and current adoption, use the [shared authentication guide and ledger](authentication.md). For detailed shared credential resolution, reuse [Common's authentication module](../src/common/README.md#authentication-module), [profile rules](../src/common/README.md#profile-backed-authentication) and [HTTP IDCS contract](../src/common/README.md#http-idcs-authentication). [Root quality requirements](../AGENTS.md#mcp-server-quality-validation) and [BEST_PRACTICES](../BEST_PRACTICES.md#oci-sdk-authentication) govern server adoption; Common's implementation and tests support its descriptive claims.

For Compute's current client/transport behavior and differences, read its [local authentication explanation](../src/oci-compute-mcp-server/docs/authentication.md) with the [Compute guide](../src/oci-compute-mcp-server/AGENTS.md). Compute is not assumed migrated to Common. The [reuse assessment](plans/apply-agent-context-guide/scope-and-reuse.md#source-assessment) explains why Common needed no duplicate topic document and Compute warranted one. That initial application assessed Common/Compute only. The subsequent [shared-authentication ledger review](plans/shared-authentication-context/outcome.md) records source-based adoption across all servers, with separate evidence limits.

## Evidence and maintenance

Requirements and decisions establish expectations; source/interfaces describe implementation; manifests and task/test definitions establish available checks. Only recorded executions establish what ran, against which sources, and with what result. Label source inference, structural review, executed checks and unverified behavior separately. Source-defined test cases are not passing results, and a declaration of Common dependency does not prove runtime use.

When authentication behavior, public exports, dependencies, transports, commands or references change, review the owning explanation and affected root/component routes. Recheck claims against their current sources; a date alone establishes neither freshness nor error. If a source moves or is superseded, repair the relevant route and identify its replacement through the repository's existing process. Use [contribution guidance](../CONTRIBUTING.md), root editing/changelog rules and [engineering evidence routes](agent-development.md#evidence-and-context-routes).

The [application outcome](plans/apply-agent-context-guide/outcome.md) records this increment's documentation review. The earlier adoption summary's ten-case read-only evaluation applies to its recorded guide revision; it is not a new evaluation of these conventions or the focused authentication explanation.
