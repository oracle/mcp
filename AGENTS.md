# Repository Agent Instructions

## Scope

These instructions apply to the entire repository. More specific instructions in a nested `AGENTS.md` file override this file for that subtree.

Before editing, read this file and applicable nested guides for the target paths. Start with [shared engineering context](docs/agent-development.md#start-here) for repository procedures and validation sources. Package guides add local orientation and constraints; a documented implementation gap does not waive a shared requirement.

This is a polyglot reference-implementation monorepo. Packages under `src/` own their tools, service clients and runtime behavior; [Common](src/common/README.md) owns reusable Python authentication. Named maintainer ownership is not established by these guides; consult the project's contribution process when ownership is unclear.

## Repository Layout

- `src/<server-name>/` contains individual MCP server implementations.
- `tests/` contains repository-level tests and end-to-end test assets.
- `BEST_PRACTICES.md` defines expected quality standards for MCP servers in this repository.
- `README.md` contains repository setup, authentication, and client configuration guidance.

## Architecture and Dependencies

- Follow the [repository scope and setup](README.md) and each package's native README/manifest. Python, TypeScript and Java packages have different runtime and validation interfaces.
- Use Compute as a structure/model/tool-test reference. Its current credential handling is legacy; use [Common's authentication contracts](src/common/README.md#authentication-module) and the quality requirements below for new authentication work.
- Before changing Common, inspect declared `oracle-mcp-common` consumers and their manifests. API, Cloud, Database, DB Observability, Document Understanding and Recovery declare the dependency at this baseline; dependency declarations alone do not establish complete migration or runtime use. Use the [authentication ledger](docs/authentication.md#adoption-ledger) for source paths and the [Common guide](src/common/AGENTS.md#architecture-and-dependencies) for package dependency edges.
- Preserve package-owned client type, lifecycle, transport and compatibility decisions. See [shared and local gaps](docs/agent-development.md#known-gaps) when implementation and policy differ.

## Setup, Build and Change Impact

Use the [validation map](docs/agent-development.md#validation-map) for working directories, setup/build definitions and check scope. [Moon Python tasks](.moon/tasks/python.yml), [root tasks](moon.yml), [JavaScript tasks](src/oci-javascript-mcp-server/moon.yml) and native manifests define commands; setup/build instructions are not proof checks have run.

Changes to tools, models, authentication, configuration or shared exports can affect clients and consumers. Inspect local interfaces/tests, the [contribution process](CONTRIBUTING.md) and changelog rules below. Security reports follow [SECURITY.md](SECURITY.md); credential and runtime boundaries also require the relevant native package guidance.

## Context Authoring and Maintenance

When creating or maintaining repository context, follow [local context conventions](docs/agent-context.md#authoring-procedure). These conventions cover context authoring only; existing repository policies, native contracts and runtime instruction rules govern engineering behavior. Preserve broad guides, assess reuse before creating topic documents, and report inaccessible sources. See the separate [application bundle](docs/plans/apply-agent-context-guide/scope-and-reuse.md) for this increment's scope and evidence.

## Context Routes

The Know / Do / Now / Proof / Done labels describe a source's purpose; see the [context-intent definitions](docs/agent-context.md#context-intents-know-do-now-proof-and-done) for their meaning and evidence limits.

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating shared architecture/authentication or a package boundary | [README](README.md), [quality standards](BEST_PRACTICES.md), [shared authentication guide and ledger](docs/authentication.md), [Common contract](src/common/README.md) | Applicable package README, manifest and guide | Relevant implementation/tests; [consumer and gap notes](docs/agent-development.md#known-gaps) |
| **Know:** Starting a server/library change | [Server and library guide map](docs/agent-development.md#selected-component-context) | This root guide and the applicable local guide; native README/manifest | Local source/test entry points and [actual adoption coverage](docs/plans/adopt-monorepo-agent-context/adoption-summary.md) |
| **Do:** Preparing, building or validating an engineering change | [Shared validation map](docs/agent-development.md#validation-map) | Native command definitions and target runtime prerequisites | Actual command/run reports; [evidence distinctions](docs/agent-development.md#evidence-and-context-routes) |
| **Know:** Implementing or reviewing code and tests | [Code quality](docs/code-quality.md#review-criteria), [test quality](docs/test-quality.md#review-criteria) | Root editing/quality rules, [BEST_PRACTICES](BEST_PRACTICES.md), applicable component contracts | Changed implementation/assertions, native coverage gates and actual scoped check results |
| **Know:** Changing Python MCP schemas, lifecycle or transport | [FastMCP guidance](docs/fastmcp.md) | Applicable component guide, actual imports/manifest/lock, shared authentication requirements | [Library/version sources](docs/fastmcp.md#library-and-version), protocol-facing tests and actual runs |
| **Know:** Designing or reviewing collection results | [Pagination](docs/pagination.md) | Owning tool contract and component guide; shared quality rules | [Current patterns](docs/pagination.md#current-patterns), boundary/continuation tests and actual runs |
| **Know:** Implementing or invoking mutating/destructive tools | [Tool safety](docs/tool-safety.md) | Caller authorization, user-authorized scope, root security/credential rules and local runtime constraints | [Selected source/check examples](docs/tool-safety.md#current-examples-and-checks); annotations are hints, not enforcement |
| **Do:** Reviewing local changes or authoring a PR | [Local-review skill](.agents/skills/local-review/SKILL.md), [PR-authoring skill](.agents/skills/pr-authoring/SKILL.md) | Applicable guides, [validation map](docs/agent-development.md#validation-map), [contribution rules](CONTRIBUTING.md) and selected-base PR template | Snapshot-specific review report, real check results and actual publication response when requested |
| **Know:** Assessing credentials, isolation or disclosure handling | [Shared security sources and gaps](docs/agent-development.md#known-gaps), [security reporting](SECURITY.md) | Editing/quality rules here and local runtime constraints | Relevant auth/isolation tests; unrun definitions remain source leads |
| **Do:** Adding, updating or reviewing context and mappings | [Authoring and maintenance conventions](docs/agent-context.md) | Applicable root/component instructions and the topic's owning native sources | [Reuse assessment](docs/plans/apply-agent-context-guide/scope-and-reuse.md#source-assessment), [application outcome](docs/plans/apply-agent-context-guide/outcome.md); source review and structural checks have distinct roles |
| **Know:** Integrating shared auth, assessing adoption or a missing shared capability | [Shared authentication requirements and integration](docs/authentication.md), [server ledger](docs/authentication.md#adoption-ledger) | Root quality rules and applicable server/library guides; Common public API contracts | Linked manifests and implementation paths; [documentation outcome](docs/plans/shared-authentication-context/outcome.md); source use is not runtime validation |
| **Know:** Comparing Compute authentication with the shared contract | [Compute authentication](src/oci-compute-mcp-server/docs/authentication.md), [Compute guide](src/oci-compute-mcp-server/AGENTS.md), [Common guide](src/common/AGENTS.md) | Root quality rules, [shared authentication guide](docs/authentication.md), [Common contract](src/common/README.md#authentication-module) and [HTTP contract](src/common/README.md#http-idcs-authentication) | [Source/check definitions and limits](src/oci-compute-mcp-server/docs/authentication.md#supporting-definitions-and-evidence-limits); current behavior does not waive shared requirements |
| **Now:** Reviewing this context adoption | [Design and scope](docs/plans/adopt-monorepo-agent-context/design.md), [plan](docs/plans/adopt-monorepo-agent-context/implementation-plan.md) | [Main-based reuse assessment](docs/plans/adopt-monorepo-agent-context/reuse-assessment.md) | [Adoption summary](docs/plans/adopt-monorepo-agent-context/adoption-summary.md) |
| **Proof:** Checking coverage or a completion claim | [Evidence routes](docs/agent-development.md#evidence-and-context-routes) | Source/guidance identity and actual check scope | [Recorded adoption checks and limits](docs/plans/adopt-monorepo-agent-context/adoption-summary.md) or the owning change's native reports |

Broad engineering guides now cover all 34 MCP server components under `src/`, including the Java toolkit, plus Common. Find each local guide and native entry point in the [shared context map](docs/agent-development.md#selected-component-context). Documentation coverage and recorded behavior-evaluation coverage are separate; see the [adoption summary](docs/plans/adopt-monorepo-agent-context/adoption-summary.md).

## Known Gaps

The [gap register](docs/agent-development.md#known-gaps) and local guides record Common adoption/source differences, stale native procedures, excluded-package validation limits, JavaScript's existing subprocess-policy conflict/isolation limits and Java's test/coverage limitations. These are observations to recheck, not policy exceptions or executed validation results.

## Validation

- For Moon-managed Python MCP servers, run `moon run <server-name>:test` to test one server, for example `moon run oci-compute-mcp-server:test`.
- The Python servers excluded from Moon are `dbtools-mcp-server`, `mysql-mcp-server`, `oci-pricing-mcp-server`, `oracle-db-doc-mcp-server`, and `oracle-db-mcp-java-toolkit`. Follow each excluded server's `README.md` for validation and report a gap if it does not document validation commands.
- Run `moon run root:lint` after Python source changes.
- Run `moon run :test` and `moon run root:combine-coverage` when a change affects shared behavior across multiple Moon-managed Python servers.
- For non-Python servers, read the server's `README.md` and run its documented test command.
- Do not mark validation complete until the relevant commands pass.

## Editing Rules

- Keep each MCP server self-contained under `src/<server-name>/` unless shared repository tooling must change.
- Do not add secrets, tenancy-specific values, credentials, or local absolute paths to examples, configs, docs, or tests.
- Do not edit generated or local output artifacts such as `htmlcov/`, `.coverage*`, `.ruff_cache/`, `.pytest_cache/`, `__pycache__/`, `dist/`, `src/logs`, or `.venv/`.
- Keep diffs focused on the requested change; avoid unrelated formatting, import reordering, or refactors.
- Write the smallest implementation that satisfies the requested behavior. Add abstractions or helpers for meaningful boundaries, demonstrated variation or reuse; avoid speculative frameworks and pass-through wrappers with no responsibility. See [code-quality criteria](docs/code-quality.md#review-criteria).
- Handle expected errors explicitly; do not silently turn unexpected failures into successful empty/default results. Keep type/lint suppressions narrow and justified, and comments focused on non-obvious constraints.

## Changelog Guidance

- When changing any server under `src/<server-name>/`, check whether that server has a `CHANGELOG.md`; if it does, update it for user-visible or operator-visible changes.
- Follow Keep a Changelog 1.1.0 principles: write changelog entries for humans, keep the newest release first, group related change types, and use ISO 8601 dates (`YYYY-MM-DD`) when adding dated release sections.
- Prefer the standard sections `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, and `Security`.
- Preserve this repository's existing `Breaking Changes` heading for compatibility breaks, and list those entries first within a release section.
- Use an `## Unreleased` section for work that has not been assigned a release version yet; move entries into `## <version>` or `## <version> - YYYY-MM-DD` when a release is cut.
- Keep entries concise and outcome-focused instead of copying commit messages. Mention changed tools, transports, authentication requirements, configuration or environment variables, response shapes, validation behavior, and security posture when relevant.
- Do not add changelog entries for purely internal refactors, formatting-only edits, or test-only changes unless they affect users, operators, packaging, or documented behavior.
- If multiple `src/` servers are changed, update each changed server's changelog independently when that server has one.
- Only create a new changelog if a server doesn't have one when explicitly requested, or when the update introduces breaking changes; maintain existing src/*/CHANGELOG.md files.

## MCP Server Quality Validation

When validating the quality of any MCP server under `src/`:

- Read `BEST_PRACTICES.md` first and use it as the validation checklist.
- Use `src/oci-compute-mcp-server/` as the reference example for expected structure, packaging, models, server entry point, tool parameter style, and tests.
- If changes are scoped to a specific server, validate only that server for best-practice patterns and 90% coverage. Do not audit or require unrelated servers to meet those standards unless the change touches shared tooling or the user explicitly asks for a broader review.
- Confirm the server includes unit tests for the MCP server code.
- For Python MCP servers, require unit tests to enforce at least 90% coverage through `[tool.coverage.report] fail_under = 90` in `pyproject.toml`. Do not mark validation complete if the coverage threshold is lower than 90% or if coverage fails.
- For OCI Python SDK-backed servers, require every OCI client-configuration path to derive the canonical `<user_agent_name>/<version>` `additional_user_agent` from package `__project__` and `__version__`; do not duplicate literal names or versions. Client factories may live outside `server.py`, but every path that constructs an OCI client must receive the value. Strip `-server` off the end of `__project__` when applicable; ex `oci-cloud-mcp`.
- For OCI Python SDK-backed servers, declare `oracle-mcp-common>=0.1.0,<0.2.0` and use `oracle_mcp_common.build_auth_context()` for stdio and other configured OCI credential modes instead of duplicating credential resolution, OCI profile parsing, environment-variable precedence, or signer construction. Merge the returned `AuthContext.config` with the derived `additional_user_agent`, pass `AuthContext.signer` to each OCI client, and keep the server responsible for its client type, retry and circuit-breaker policy, and lifecycle. Use `AuthOptions` only when a server must explicitly override configured authentication inputs.
- For an HTTP server that uses OCI IAM/IDCS request-token exchange, use `build_idcs_http_auth(required_scopes)` once for provider configuration; the server retains listener startup, `mcp.auth` assignment, request-token retrieval, and user-agent assignment. During each authenticated request, call `IDCSHttpAuth.context_for(access_token.token)` and create only caller-specific OCI SDK clients from that context. Do not inspect host/port to select credentials, call FastMCP request-context APIs from the common library, or cache an HTTP-derived signer/client globally across callers.
- For OCI Python SDK-backed servers, require unit tests to assert the exact derived `additional_user_agent` for each supported client-construction authentication path: API-key, security-token, each supported principal-based path (for example, instance- and resource-principal), and HTTP/token-exchange.
- For servers that invoke the OCI CLI instead of constructing OCI Python SDK clients, require the same derived value through `OCI_SDK_APPEND_USER_AGENT` in the launched process environment.
- For non-Python or Moon-excluded servers, follow the server's `README.md` to identify the test and coverage commands. Report a gap if the README does not document how to enforce 90% unit-test coverage.
- Treat end-to-end tests under `tests/e2e/` as optional unless they can run without making the normal test suite slower or less reliable.
- Don't duplicate or reinvent anything that's in the common packages (src/common) (like authentication).
- Do not implement a server that invokes subprocesses because it's difficult to secure and it limits how and where the MCP servers can run. `oci-api-mcp-server` is the exception: it launches the OCI CLI rather than constructing OCI Python SDK clients directly.
