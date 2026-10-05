# Java toolkit engineering context

## Scope and ownership

This Java toolkit exposes configurable database and related tools over stdio or HTTP. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here), using the package's native Java procedures rather than Python/Common implementations.

## Entry points

- [OracleDatabaseMCPToolkit.java](src/main/java/com/oracle/database/mcptoolkit/OracleDatabaseMCPToolkit.java): runtime entry point and server/tool registration.
- [ServerConfig.java](src/main/java/com/oracle/database/mcptoolkit/ServerConfig.java), [config classes](src/main/java/com/oracle/database/mcptoolkit/config) and [LoadedConstants.java](src/main/java/com/oracle/database/mcptoolkit/LoadedConstants.java): tool/data-source/server settings.
- [Tools](src/main/java/com/oracle/database/mcptoolkit/tools): custom-policy, database, RAG, administration and log-analysis handlers; inspect the owning schema and handler together.
- [OAuth classes](src/main/java/com/oracle/database/mcptoolkit/oauth), [AuthorizationFilter.java](src/main/java/com/oracle/database/mcptoolkit/web/AuthorizationFilter.java) and [RequestTargetValidator.java](src/main/java/com/oracle/database/mcptoolkit/web/RequestTargetValidator.java): token/scope handling, request identity and HTTP origin validation.
- [OwnedTransactionRegistry.java](src/main/java/com/oracle/database/mcptoolkit/tools/OwnedTransactionRegistry.java): JDBC transactions spanning requests, bound to authenticated owners; [EndUserSecurityContextHolder.java](src/main/java/com/oracle/database/mcptoolkit/oauth/EndUserSecurityContextHolder.java): request-scoped principal/OJDBC context.
- [pom.xml](pom.xml) and [README](README.md): Java/dependencies/build and operator-facing configuration contracts.

## Setup / build / run

README documents JDK 17+ and Maven 3.9+. Run `mvn clean package` from this package directory (`src/oracle-db-mcp-java-toolkit`). POM declares Java 17 and packages the runtime jar; these are source definitions, not a verified build result. Native README owns transport/configuration and startup. Building and starting a database-backed server are separate activities; no live server is needed for guide review.

## Tests and validation

Current unit-test leads are [OAuth2TokenValidatorTest](src/test/java/com/oracle/database/mcptoolkit/oauth/OAuth2TokenValidatorTest.java) for scope extraction, [AuthenticatedPrincipalTest](src/test/java/com/oracle/database/mcptoolkit/oauth/AuthenticatedPrincipalTest.java) for identity derivation, [RequestTargetValidatorTest](src/test/java/com/oracle/database/mcptoolkit/web/RequestTargetValidatorTest.java) for origins, [OwnedTransactionRegistryTest](src/test/java/com/oracle/database/mcptoolkit/tools/OwnedTransactionRegistryTest.java) for ownership/lifecycle and [OracleJDBCLogAnalyzerTest](src/test/java/com/oracle/database/mcptoolkit/OracleJDBCLogAnalyzerTest.java) for analyzer registration/schema. Their definitions do not establish coverage for all tools or transport behavior.

[DeepSecIntegrationTest](src/test/java/com/oracle/database/mcptoolkit/DeepSecIntegrationTest.java) is database-backed and gated by `DEEPSEC_IT_ENABLED=true`. It uses browser OAuth login, JDBC context propagation and real transactions; [native instructions](README.md#deepsec-integration-test) own its prerequisites. It is disabled during normal builds and is not a default documentation or unit check.

`mvn clean package` is the documented build route. Inspect actual test discovery/reports when executing it: JUnit dependency presence, build success or zero discovered tests is not a passing unit suite. The POM has no explicit Surefire pin or JaCoCo coverage enforcement; report the root 90% requirement as a gap. The [validation map](../../docs/agent-development.md#validation-map) records runtime scope; Java has no discovered Moon project here and requires native Maven validation.

## Architecture and dependencies

Trace settings through config/data-source resolution and tool registration before changing defaults, schema or exposure. Read the [custom tool framework](README.md#2-custom-tool-framework--extending-the-mcp-server), owning handlers and [CustomToolPolicy.java](src/main/java/com/oracle/database/mcptoolkit/tools/CustomToolPolicy.java) together. OAuth changes require the current [validator](src/main/java/com/oracle/database/mcptoolkit/oauth/OAuth2TokenValidator.java), principal/context helpers and HTTP authorization inspection. DeepSec propagates end-user context through the OJDBC SPI; the configured database credentials still open connections. Transaction changes must trace authenticated ownership and context across requests through the registry and database operator tools.

## Security and secrets handling

Keep database passwords, OAuth secrets and tokens out of source/logs and use synthetic inputs for unit checks. Inspect configured tool exposure, origin validation, authorization and request-context clearing in the native README/filter/handlers; development-token examples are not production authentication guidance. Preserve transaction-owner checks and distinguish MCP login scopes from DeepSec database scopes. A live database operation can mutate data and is not a default validation check.

## Change impact

Tool, data-source, policy, OAuth, transport or configuration changes affect exposed behavior and operator setup. Select corresponding source/tests and native Maven checks, and review README for configuration/startup differences. Follow [CONTRIBUTING](../../CONTRIBUTING.md) and root changelog rules; no package changelog exists at this baseline, and instruction-only adoption does not create one.

## Known gaps

- Actual test discovery, execution and coverage have not been observed here. No explicit Surefire pin/JaCoCo enforcement establishes the root 90% requirement.
- The five unit-test definitions and gated integration test are evidence leads; no discovery, execution or coverage result is claimed by this adoption.
- Python/JavaScript Moon success does not validate this Java package. Native runtime/database/auth checks remain separate from documentation review.

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Changing tools, defaults or data-source configuration | [Config](src/main/java/com/oracle/database/mcptoolkit/config), [tools](src/main/java/com/oracle/database/mcptoolkit/tools), [native contract](README.md) | Root quality/compatibility guidance; owning policy/schema/handler | Available [test definitions](src/test/java/com/oracle/database/mcptoolkit), explicit missing coverage |
| **Know:** Changing HTTP auth, origins or scopes | [OAuth validator](src/main/java/com/oracle/database/mcptoolkit/oauth/OAuth2TokenValidator.java), [authorization filter](src/main/java/com/oracle/database/mcptoolkit/web/AuthorizationFilter.java), [origin validator](src/main/java/com/oracle/database/mcptoolkit/web/RequestTargetValidator.java) | README transport/OAuth configuration; request identity/context helpers; root secrets guidance | [Scope](src/test/java/com/oracle/database/mcptoolkit/oauth/OAuth2TokenValidatorTest.java), [principal](src/test/java/com/oracle/database/mcptoolkit/oauth/AuthenticatedPrincipalTest.java) and [origin tests](src/test/java/com/oracle/database/mcptoolkit/web/RequestTargetValidatorTest.java); runtime evidence separately required |
| **Know:** Changing transaction ownership or end-user database context | [Registry](src/main/java/com/oracle/database/mcptoolkit/tools/OwnedTransactionRegistry.java), [context holder](src/main/java/com/oracle/database/mcptoolkit/oauth/EndUserSecurityContextHolder.java), [DeepSec contract](README.md#45-oracle-deep-data-security-support) | Authenticated principal, database credentials/configuration and request lifecycle | [Registry unit tests](src/test/java/com/oracle/database/mcptoolkit/tools/OwnedTransactionRegistryTest.java); [gated integration test](src/test/java/com/oracle/database/mcptoolkit/DeepSecIntegrationTest.java) has separate live prerequisites |
| **Do:** Preparing or validating Java changes | [README build](README.md#42-build-the-mcp-server-jar), [POM](pom.xml), [validation map](../../docs/agent-development.md#validation-map) | Java/Maven prerequisites and package working directory | Actual build/test-discovery reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

Keep the owning native sources and shared requirements reachable. The adoption's Now/Proof record is the [summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md); an instruction pass does not remediate build/coverage or authorize database operations.
