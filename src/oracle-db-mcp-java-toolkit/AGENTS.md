# Java toolkit engineering context

## Scope and ownership

This Java toolkit exposes configurable database and related tools over stdio or HTTP. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here), using the package's native Java procedures rather than Python/Common implementations.

## Entry points

- [OracleDatabaseMCPToolkit.java](src/main/java/com/oracle/database/mcptoolkit/OracleDatabaseMCPToolkit.java): runtime entry point and server/tool registration.
- [ServerConfig.java](src/main/java/com/oracle/database/mcptoolkit/ServerConfig.java), [config classes](src/main/java/com/oracle/database/mcptoolkit/config) and [LoadedConstants.java](src/main/java/com/oracle/database/mcptoolkit/LoadedConstants.java): tool/data-source/server settings.
- [Tools](src/main/java/com/oracle/database/mcptoolkit/tools): custom-policy, database, RAG, administration and log-analysis handlers; inspect the owning schema and handler together.
- [OAuth classes](src/main/java/com/oracle/database/mcptoolkit/oauth) and [AuthorizationFilter.java](src/main/java/com/oracle/database/mcptoolkit/web/AuthorizationFilter.java): token/scope handling and HTTP boundary.
- [pom.xml](pom.xml) and [README](README.md): Java/dependencies/build and operator-facing configuration contracts.

## Setup / build / run

README documents JDK 17+ and Maven 3.9+. Run `mvn clean package` from this package directory (`src/oracle-db-mcp-java-toolkit`). POM declares Java 17 and packages the runtime jar; these are source definitions, not a verified build result. Native README owns transport/configuration and startup. Building and starting a database-backed server are separate activities; no live server is needed for guide review.

## Tests and validation

Current test definitions are [OAuth2TokenValidatorTest](src/test/java/com/oracle/database/mcptoolkit/oauth/OAuth2TokenValidatorTest.java), covering default/custom scope extraction, and [OracleJDBCLogAnalyzerTest](src/test/java/com/oracle/database/mcptoolkit/OracleJDBCLogAnalyzerTest.java), covering analyzer tool presence and file-path schema. They do not establish coverage for all tools or OAuth transport behavior.

`mvn clean package` is the documented build route. Inspect actual test discovery/reports when executing it: JUnit dependency presence, build success or zero discovered tests is not a passing unit suite. The POM has no explicit Surefire pin or JaCoCo coverage enforcement; report the root 90% requirement as a gap. The [validation map](../../docs/agent-development.md#validation-map) records Makefile/Moon scope; Java is excluded from Python Makefile targets and has no discovered Moon project here.

## Architecture and dependencies

Trace settings through config/data-source resolution and tool registration before changing defaults, schema or exposure. Read the [custom tool framework](README.md#2-custom-tool-framework--extending-the-mcp-server), owning handlers and [CustomToolPolicy.java](src/main/java/com/oracle/database/mcptoolkit/tools/CustomToolPolicy.java) together. OAuth changes require current [validator](src/main/java/com/oracle/database/mcptoolkit/oauth/OAuth2TokenValidator.java), scope tests and HTTP authorization inspection. Source/test additions from newer experimental branches are not part of this baseline.

## Security and secrets handling

Keep database passwords, OAuth secrets and tokens out of source/logs and use synthetic inputs for unit checks. Inspect configured tool exposure and authorization in the native README/filter/handlers; development-token examples are not production authentication guidance. A live database operation can mutate data and is not a default validation check.

## Change impact

Tool, data-source, policy, OAuth, transport or configuration changes affect exposed behavior and operator setup. Select corresponding source/tests and native Maven checks, and review README for configuration/startup differences. Follow [CONTRIBUTING](../../CONTRIBUTING.md) and root changelog rules; no package changelog exists at this baseline, and instruction-only adoption does not create one.

## Known gaps

- Actual test discovery, execution and coverage have not been observed here. No explicit Surefire pin/JaCoCo enforcement establishes the root 90% requirement.
- The two current tests are limited evidence leads; newer request-target, owned-transaction and DeepSec implementation/test additions are absent and must not be inferred.
- Python Makefile/Moon success does not validate this Java package. Native runtime/database/auth checks remain separate from documentation review.

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Changing tools, defaults or data-source configuration | [Config](src/main/java/com/oracle/database/mcptoolkit/config), [tools](src/main/java/com/oracle/database/mcptoolkit/tools), [native contract](README.md) | Root quality/compatibility guidance; owning policy/schema/handler | Available [test definitions](src/test/java/com/oracle/database/mcptoolkit), explicit missing coverage |
| **Know:** Changing HTTP auth or scopes | [OAuth validator](src/main/java/com/oracle/database/mcptoolkit/oauth/OAuth2TokenValidator.java), [authorization filter](src/main/java/com/oracle/database/mcptoolkit/web/AuthorizationFilter.java) | README transport/OAuth configuration; root secrets guidance | [Scope extraction tests](src/test/java/com/oracle/database/mcptoolkit/oauth/OAuth2TokenValidatorTest.java); transport/runtime evidence separately required |
| **Do:** Preparing or validating Java changes | [README build](README.md#42-build-the-mcp-server-jar), [POM](pom.xml), [validation map](../../docs/agent-development.md#validation-map) | Java/Maven prerequisites and package working directory | Actual build/test-discovery reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

Keep the owning native sources and shared requirements reachable. The adoption's Now/Proof record is the [summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md); an instruction pass does not remediate build/coverage or authorize database operations.
