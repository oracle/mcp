# OCI Database Observability engineering context

## Scope and ownership

This package owns catalog discovery and allowlisted OPSI, Database Management and Monitoring observability invocation. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/oci_db_observability_mcp_server/server.py): MCP registration, tool handlers and runtime entry point.
- [MCP surface](oracle/oci_db_observability_mcp_server/mcp.py): discovery and invoke tool registration
- [Registry](oracle/oci_db_observability_mcp_server/registry.py): metadata/catalog allowlists and service clients
- [Dispatcher](oracle/oci_db_observability_mcp_server/runtime.py): Common auth, validation, coercion and SDK response handling
- [Metric catalog](oracle/oci_db_observability_mcp_server/metric_catalog.py): local metric catalog loading
- [Schema derivation](oracle/oci_db_observability_mcp_server/sdk_schema.py): SDK operation schema extraction
- [Package metadata](oracle/oci_db_observability_mcp_server/__init__.py) and [manifest](pyproject.toml): version, dependencies and executable definitions.
- [Tests](oracle/oci_db_observability_mcp_server/tests): local behavior definitions; start with [test_mcp_surface.py](oracle/oci_db_observability_mcp_server/tests/test_mcp_surface.py), [test_metric_catalog.py](oracle/oci_db_observability_mcp_server/tests/test_metric_catalog.py).

## Setup / build / run

From the repository root, use `proto install` for pinned tools and `moon run oci-db-observability-mcp-server:build` for packaging. The [manifest](pyproject.toml) requires Python `>=3.13`. Read the local [README](README.md) and server `main()` for runtime transport/configuration; startup can access real services. See the [shared validation map](../../docs/agent-development.md#validation-map) for command definitions and check scope.

## Tests and validation

Use `moon run oci-db-observability-mcp-server:test` from the repository root for the inherited Python test task, and `moon run root:lint` after Python source changes. The manifest configures `90%` coverage. Inspect the relevant tool/model or helper tests for the requested change; shared changes also require [shared validation](../../docs/agent-development.md#validation-map). These definitions are source evidence; this documentation expansion ran no server tests or coverage.

## Architecture and dependencies

server.py starts the stdio process; mcp.py owns the MCP discovery/invocation surface. registry.py reads packaged metadata, sdk_schema.py derives operation schemas, and runtime.py validates/coerces inputs and dispatches allowlisted SDK operations. Metric catalog lookup is local; metric/alarm reads use OCI Monitoring. Use Identity for compartment discovery; catalog skills are discovery metadata, not installed agent workflow skills.

The package declares Common; read [its contract](../common/README.md) and [guide](../common/AGENTS.md) for auth ownership and shared-change impact. A declared dependency alone does not establish every supported path’s coverage.

## Security and secrets handling

Preserve catalog allowlisting, argument validation and the read-only operation surface. runtime.py obtains Common auth ingredients and adds the package user agent. Real metric/diagnostic reads can expose database and infrastructure information. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Catalog JSON, generated schemas, coercion and serialized responses are caller contracts. Check catalog/registry/runtime/MCP tests and packaged metadata when changing dispatch. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- The README development section refers to removed Make tooling. Use the current inherited Moon test task and root lint definition instead.
- The manifest pins OCI 2.182.1 while Common requires OCI >=2.185.0. Dependency resolution is a separate engineering issue; setup/test execution has not been established.
- There is no package Moon file declaring a Common graph edge; the manifest declaration and actual runtime imports are separate evidence.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle/oci_db_observability_mcp_server/server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Local tests](oracle/oci_db_observability_mcp_server/tests); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
