# OCI Monitoring engineering context

## Scope and ownership

This package owns OCI alarm, metric-definition and metric-data discovery. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). The local [README](README.md) owns user-facing setup and service guidance; this guide routes engineering sources and local limitations.

## Entry points

- [Server](oracle/oci_monitoring_mcp_server/server.py): MCP registration, tool handlers and runtime entry point.
- [alarm_models.py](oracle/oci_monitoring_mcp_server/alarm_models.py), [metric_models.py](oracle/oci_monitoring_mcp_server/metric_models.py): local request/response models and conversions.
- [MQL resource](oracle/oci_monitoring_mcp_server/scripts.py): packaged query-syntax guidance
- [Package metadata](oracle/oci_monitoring_mcp_server/__init__.py) and [manifest](pyproject.toml): version, dependencies and executable definitions.
- [Tests](oracle/oci_monitoring_mcp_server/tests): local behavior definitions; start with [test_monitoring_models.py](oracle/oci_monitoring_mcp_server/tests/test_monitoring_models.py), [test_monitoring_tools.py](oracle/oci_monitoring_mcp_server/tests/test_monitoring_tools.py).

## Setup / build / run

From the repository root, use `proto install` for pinned tools and `moon run oci-monitoring-mcp-server:build` for packaging. The [manifest](pyproject.toml) requires Python `>=3.13`. Read the local [README](README.md) and server `main()` for runtime transport/configuration; startup can access real services. See the [shared validation map](../../docs/agent-development.md#validation-map) for command definitions and check scope.

## Tests and validation

Use `moon run oci-monitoring-mcp-server:test` from the repository root for the inherited Python test task, and `moon run root:lint` after Python source changes. The manifest configures `90%` coverage. Inspect the relevant tool/model or helper tests for the requested change; shared changes also require [shared validation](../../docs/agent-development.md#validation-map). These definitions are source evidence; this documentation expansion ran no server tests or coverage.

## Architecture and dependencies

`_prepare_time_parameters()` participates in metric-query time handling. Alarm and metric models are separate modules; scripts.py loads the packaged MQL guide. Trace MQL/time inputs, SDK calls and result mapping together.

Authentication is implemented locally and the manifest has no Common dependency. Existing OCI SDK authentication requirements remain in [root instructions](../../AGENTS.md#mcp-server-quality-validation) and [Common’s contract](../common/README.md). Recheck credential/client paths before authentication work; this implementation departure grants no exception.

## Security and secrets handling

Metric dimensions and alarm metadata can reveal infrastructure details. Source review and mocked tests do not require live telemetry reads. Follow [shared quality/credential constraints](../../AGENTS.md#mcp-server-quality-validation) and [security reporting](../../SECURITY.md); keep credentials and real customer data out of committed examples and diagnostics.

## Change impact

Time-window/default changes, MQL guidance and alarm/metric response shapes affect callers and the monitoring tests. Review [CONTRIBUTING](../../CONTRIBUTING.md), the local README and the existing [CHANGELOG](CHANGELOG.md) under [root changelog rules](../../AGENTS.md#changelog-guidance).

## Known gaps

- Local OCI credential resolution is outside Common. This pass records the departure without migrating authentication.
- Source definitions and available tests do not establish passing validation or live security/transport behavior. Record actual checks separately through the [shared evidence routes](../../docs/agent-development.md#evidence-and-context-routes).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a tool or response change | [Server](oracle/oci_monitoring_mcp_server/server.py), local model/helper entry points above | Root quality requirements and the relevant service inputs/contract | [Local tests](oracle/oci_monitoring_mcp_server/tests); actual run results recorded separately |
| **Know:** Investigating configuration, credentials or service boundaries | Local README and architecture/security entry points above | [Root instructions](../../AGENTS.md), applicable shared contracts and explicit local gaps | Current client/configuration sources and relevant tests |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map) and local command sources above | Native toolchain, working directory, change scope and live prerequisites | Actual scoped reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

This context adoption’s Now/Proof record is the [adoption summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md). Keep unrelated engineering work in its own scoped change record.
