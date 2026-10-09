# OCI Recovery Service engineering context

## Scope and ownership

This package owns Recovery Service protected-database discovery, database/backup inventory and dashboard summaries. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/oci_recovery_mcp_server/server.py): transport/startup and imports that register each tool family; [app.py](oracle/oci_recovery_mcp_server/app.py): shared FastMCP instance, tool hints and cooperative deadlines.
- [Recovery tools](oracle/oci_recovery_mcp_server/recovery_tools.py), [database tools](oracle/oci_recovery_mcp_server/database_tools.py), [summaries](oracle/oci_recovery_mcp_server/summarise_tools.py) and [guidance tools](oracle/oci_recovery_mcp_server/prompt_tools.py): the four registered tool families.
- [Authentication](oracle/oci_recovery_mcp_server/auth.py) and [client factories](oracle/oci_recovery_mcp_server/clients.py): Common integration, request-context selection, region and user-agent handling.
- [Compartment discovery](oracle/oci_recovery_mcp_server/compartments.py), [cache keys](oracle/oci_recovery_mcp_server/cache.py) and [regions](oracle/oci_recovery_mcp_server/regions.py): scope expansion, tenant/caller partitioning and IAM region discovery.
- [Telemetry](oracle/oci_recovery_mcp_server/telemetry.py) and [logging setup](oracle/oci_recovery_mcp_server/logging_setup.py): tool/SDK correlation, request identifiers and log output.
- [models.py](oracle/oci_recovery_mcp_server/models.py): typed responses and SDK conversions; [prompt content](oracle/oci_recovery_mcp_server/data/prompts): packaged Recovery guidance.
- [Package metadata](oracle/oci_recovery_mcp_server/__init__.py) and [manifest](pyproject.toml): version, dependencies and executable definitions.
- [Tests](oracle/oci_recovery_mcp_server/tests): concern-specific behavior definitions; use the routes below to select the owning module.

## Setup / build / run

From the repository root, use `proto install` for pinned tools and `moon run oci-recovery-mcp-server:build` for packaging. The [manifest](pyproject.toml) requires Python `>=3.13`. Read the local [README](README.md) and server `main()` for runtime transport/configuration; startup can access real services. See the [shared validation map](../../docs/agent-development.md#validation-map) for command definitions and check scope.

## Tests and validation

Use `moon run oci-recovery-mcp-server:test` from the repository root for the inherited Python test task, and `moon run root:lint` after Python source changes. The [manifest](pyproject.toml) configures `100%` coverage; the native [development route](README.md#development-and-validation) describes the offline suite with mocked OCI clients. Shared changes also require [shared validation](../../docs/agent-development.md#validation-map). These definitions are source evidence; this context maintenance ran no server tests or coverage.

Start auth/client changes with [auth and factory tests](oracle/oci_recovery_mcp_server/tests/test_auth_and_client_factories.py), discovery/cache changes with [compartment tests](oracle/oci_recovery_mcp_server/tests/test_compartment_scope.py), and startup/telemetry changes with [server-helper tests](oracle/oci_recovery_mcp_server/tests/test_server_helpers.py). Tool/response changes use the matching family and [model tests](oracle/oci_recovery_mcp_server/tests/test_model_mappers.py), not only server startup tests.

## Architecture and dependencies

server.py imports the four tool families to register them on the shared app, then starts stdio or HTTP. Keep registration imports intact; handlers belong in their owning family. clients.py centralizes SDK construction through auth.py and wraps calls with telemetry. compartments.py owns discovery/expansion; cache.py composes namespace/tenant/caller keys; regions.py queries IAM subscriptions rather than reusing an authorization result across callers. Summary fan-out uses the cooperative deadline in app.py; an in-flight OCI request is allowed to finish.

The package declares `oracle-mcp-common>=0.1.4,<0.2.0` and a [Moon dependency edge](moon.yml). auth.py delegates configured credentials to `build_auth_context()`, builds HTTP provider policy through `build_idcs_http_auth()` and exchanges explicit caller tokens through `context_for()`. Listener selection remains in server.py; credential dispatch checks request-token/request context and refuses local profile credentials on an initialized HTTP deployment without caller context. The server retains client type/lifecycle, derived user agents, region overrides and compatibility handling for the deprecated `apikey` spelling. Read the [shared authentication guide](../../docs/authentication.md), [Common contract](../common/README.md) and [Common guide](../common/AGENTS.md) before changing these paths. Source use does not establish complete migration compliance or passing auth checks.

## Security and secrets handling

Recovery/database/backup results and logs may reveal sensitive infrastructure data. Review explicit caller-token exchange, local-credential refusal, cache partitioning and telemetry/log payload handling together. HTTP-derived clients/signers stay request-specific; cached discovery results use tenant/caller keys, and region subscriptions are read from IAM on each call. Use synthetic records and existing mocks to inspect these boundaries; source and mocked tests do not establish deployed isolation. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Compartment expansion, cache keys, auth/client construction, telemetry, deadlines and cross-service summaries affect multiple workflows. Review the matching family/helper tests and tool registration together. Common changes require consumer review and shared validation. Review [CONTRIBUTING](../../CONTRIBUTING.md), the native README and existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance); context-only corrections do not change runtime release notes.

## Known gaps

- Common integration, caller/cache boundaries and the configured 100% gate are source definitions, not successful token exchange, achieved coverage or deployed security assurance.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Changing Recovery/database tools or summaries | Owning tool family above, [models](oracle/oci_recovery_mcp_server/models.py), [registration](oracle/oci_recovery_mcp_server/server.py) | Root quality/compatibility guidance, service inputs and shared app/deadlines | [Recovery resource tests](oracle/oci_recovery_mcp_server/tests/test_recovery_resource_tools.py), [database tests](oracle/oci_recovery_mcp_server/tests/test_database_service_tools.py), [summary tests](oracle/oci_recovery_mcp_server/tests/test_summary_and_backup_tools.py), [model tests](oracle/oci_recovery_mcp_server/tests/test_model_mappers.py) |
| **Know:** Changing credentials, HTTP setup or client creation | [Auth](oracle/oci_recovery_mcp_server/auth.py), [clients](oracle/oci_recovery_mcp_server/clients.py), [native HTTP setup](README.md#http-streamable-http-deployment) | Root auth rules, [shared integration guide](../../docs/authentication.md), [Common auth](../common/README.md#authentication-module) and [HTTP contract](../common/README.md#http-idcs-authentication) | [Auth/factory tests](oracle/oci_recovery_mcp_server/tests/test_auth_and_client_factories.py), [startup tests](oracle/oci_recovery_mcp_server/tests/test_server_helpers.py); live auth evidence separate |
| **Know:** Changing discovery, caching or region selection | [Compartments](oracle/oci_recovery_mcp_server/compartments.py), [cache](oracle/oci_recovery_mcp_server/cache.py), [regions](oracle/oci_recovery_mcp_server/regions.py) | Authenticated caller/tenancy, credential boundaries above and cooperative deadlines | [Compartment tests](oracle/oci_recovery_mcp_server/tests/test_compartment_scope.py), [region/limit tests](oracle/oci_recovery_mcp_server/tests/test_region_and_limit_tools.py); caller isolation not inferred from definitions |
| **Know:** Changing telemetry or static guidance | [Telemetry](oracle/oci_recovery_mcp_server/telemetry.py), [logging](oracle/oci_recovery_mcp_server/logging_setup.py), [guidance tools](oracle/oci_recovery_mcp_server/prompt_tools.py) | Root secrets guidance; caller/request lifecycle for telemetry; owning prompt content for guidance | [Server-helper tests](oracle/oci_recovery_mcp_server/tests/test_server_helpers.py), [guidance tests](oracle/oci_recovery_mcp_server/tests/test_guidance_tools.py) |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map), [native development route](README.md#development-and-validation), [manifest](pyproject.toml) | Native toolchain, repository working directory and package/shared change scope | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

The [context follow-up outcome](../../docs/plans/assess-agent-context-2026-10-07/implementation-outcome.md) records this guide refresh; the [original adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md) retains its historical evidence. Keep unrelated engineering work in its own scoped change record.
