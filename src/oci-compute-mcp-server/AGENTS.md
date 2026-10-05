# Compute engineering context

## Scope and ownership

This Python package owns Compute instance, image and attachment tools and their typed response mappings. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). It is a structure/model/test reference; its legacy authentication is not the shared credential implementation to copy.

## Entry points

- [server.py](oracle/oci_compute_mcp_server/server.py): FastMCP tools, `get_compute_client()`, HTTP auth helper and runtime entry point.
- [models.py](oracle/oci_compute_mcp_server/models.py): response types and OCI model conversions; [consts.py](oracle/oci_compute_mcp_server/consts.py): local Compute defaults.
- [Tool tests](oracle/oci_compute_mcp_server/tests/test_compute_tools.py) and [model tests](oracle/oci_compute_mcp_server/tests/test_compute_models.py): existing behavioral/mapping test definitions.
- [Package metadata](oracle/oci_compute_mcp_server/__init__.py) and [manifest](pyproject.toml): project/version, dependency, entry point and coverage definitions.

## Setup / build / run

From the repository root, install pinned tools with `proto install`, then use `moon run oci-compute-mcp-server:build` when checking packaging. Moon manages the locked project environment; direct `uv sync --directory src/oci-compute-mcp-server --locked --all-extras --dev` is also a native setup route. [README](README.md) owns runtime transport/configuration; startup is separate from documentation validation. See the [shared validation map](../../docs/agent-development.md#validation-map).

## Tests and validation

Use `moon run oci-compute-mcp-server:test` for package tests and `moon run root:lint` after Python source changes. Aggregate coverage is a separate root task; see the shared validation map for scope. No `test-focused` task exists here. Tool changes start with tool tests; response conversions also need model-test review. The manifest configures 90% coverage; this adoption ran no server checks.

## Architecture and dependencies

Keep tool parameters, Pydantic descriptions/constraints and typed mappings consistent with [quality guidance](../../BEST_PRACTICES.md). Trace the actual source/test path for the operation being changed. Current launch handling supports boot-volume sources with precedence over image sources, with corresponding tool/model tests. Derive OCI user agents from package metadata under root requirements.

`get_compute_client()` reads local config/security-token credentials, and `_get_http_config_and_signer()` constructs token exchange locally. The manifest has no Common dependency. New auth work follows [Common's contract](../common/README.md) and [guide](../common/AGENTS.md); this existing gap does not authorize extending duplicated credential resolution or transport-based selection.

## Security and secrets handling

Use existing client/credential mocks for unit validation. Do not create/terminate real instances for a unit check; native runtime operations can mutate OCI resources. Keep profile/key/token values out of examples/logs, and caller-derived HTTP signers/clients separate across requests. Shared requirements remain in root/Common guidance.

## Change impact

Tool parameter/default/error/response changes affect MCP callers and corresponding tool/model tests. Auth changes can require Common/consumer review; expanding into shared code changes the validation scope. Check [CONTRIBUTING](../../CONTRIBUTING.md), [README](README.md) and the existing [CHANGELOG](CHANGELOG.md) under root rules for compatibility/operator-visible changes.

## Known gaps

- Local and HTTP auth are legacy paths outside Common; this pass documents them without migration.
- Source and test identities can change independently of these guides; inspect current definitions before applying an older branch's behavior or validation claims.
- Configured 90% coverage and available test definitions are not executed evidence; shared [gap/evidence limits](../../docs/agent-development.md#known-gaps) apply.

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating a response or tool change | [Tools](oracle/oci_compute_mcp_server/server.py), [models](oracle/oci_compute_mcp_server/models.py) | Root quality/compatibility guidance and operation's native inputs | [Tool tests](oracle/oci_compute_mcp_server/tests/test_compute_tools.py), [model tests](oracle/oci_compute_mcp_server/tests/test_compute_models.py) |
| **Know:** Investigating authentication/client creation | [Client helpers](oracle/oci_compute_mcp_server/server.py), [Common contract](../common/README.md) | [Common guide](../common/AGENTS.md), root auth requirements and recorded legacy gap | Existing client tests and current manifest; source inference is not auth-path coverage proof |
| **Do:** Preparing or validating a package change | [Validation map](../../docs/agent-development.md#validation-map), [README](README.md), [manifest](pyproject.toml) | Package environment and change scope | Actual package/shared reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

Keep investigations scoped to the requested behavior and affected interfaces. The selected guide adoption's Now/Proof record is the [summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md); an unrelated Compute change does not imply a Common migration.
