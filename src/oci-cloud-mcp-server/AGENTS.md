# Cloud engineering context

## Scope and ownership

This Python server discovers and invokes OCI SDK operations dynamically; it owns discovery/schema shaping, coercion, invocation, serialization and transport/client setup. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). Common owns shared Python credential resolution, not this dynamic operation surface.

## Entry points

- [server.py](oracle/oci_cloud_mcp_server/server.py): SDK class/method validation, signatures, coercion helpers, operation execution and auth/transport wiring.
- [Package metadata](oracle/oci_cloud_mcp_server/__init__.py): project/version used for user-agent derivation.
- [SDK catalog resolver](oracle/oci_cloud_mcp_server/sdk_catalog.py) and [maintainer generator](scripts/generate_sdk_catalog.py): exact membership, version checks and committed resource generation.
- [Tests](oracle/oci_cloud_mcp_server/tests): concern-specific discovery, coercion, invocation, shaping, serialization and bootstrap definitions.
- [Manifest](pyproject.toml): Common workspace dependency, package entry point and coverage configuration; [README](README.md): native usage.

## Setup / build / run

From the repository root, install pinned tools with `proto install`, then use `moon run oci-cloud-mcp-server:build` when checking packaging. Moon manages the locked environment; direct `uv sync --directory src/oci-cloud-mcp-server --locked --all-extras --dev` is also a native setup route. Preserve the Common workspace relationship. Use README for transport/auth setup; no live SDK invocation is needed for documentation validation. See the [validation map](../../docs/agent-development.md#validation-map).

## Tests and validation

Use `moon run oci-cloud-mcp-server:test` for package tests and `moon run root:lint` after Python changes. Shared behavior changes require root's broader test and aggregate-coverage checks; the package task alone does not establish consumer coverage. The manifest configures 90% coverage; no checks have run by virtue of this guide.

Start with [model coercion](oracle/oci_cloud_mcp_server/tests/test_model_coercion.py), [helper branches](oracle/oci_cloud_mcp_server/tests/test_helper_branches.py), [discovery/shaping](oracle/oci_cloud_mcp_server/tests/test_discovery_and_shaping.py), [models/serialization](oracle/oci_cloud_mcp_server/tests/test_models_and_serialization.py), [bootstrap/introspection](oracle/oci_cloud_mcp_server/tests/test_bootstrap_and_introspection.py) or [invocation/traversal](oracle/oci_cloud_mcp_server/tests/test_pagination_and_invocation.py) for the affected concern. Tests use SDK/token mocks; real OCI execution is a separate runtime action.

## Architecture and dependencies

Trace signature normalization, `prepare_params()`, `materialize_params()`, invocation and serialization together when changing input/output behavior. Catalog client/operation lookup and recursive model-resolution preflight precede constructors and authentication; service-specific assumptions must be checked against actual SDK signatures and tests.

When changing the OCI SDK pin, follow [Updating the pinned SDK and catalog](README.md#updating-the-pinned-sdk-and-catalog). `pyproject.toml` owns the exact SDK version; regenerate `oracle/oci_cloud_mcp_server/sdk_catalog.json` with the locked SDK and review `scripts/sdk_schema_exceptions.json` against that version. Do not hand-edit the resource, copy old exception approvals without checking the SDK, add import fallbacks or regenerate during startup/build/install. Run generation `--check`, the package tests and installed-distribution smoke checks; test definitions alone are not evidence those checks passed.

Configured auth delegates to Common's `build_auth_context()`; HTTP requests use initialized provider policy and `context_for()` with an explicit request token. `_import_client()` combines config, signer, derived user agent and client-specific kwargs. Common's [contract](../common/README.md) and [guide](../common/AGENTS.md) retain credential ownership; the server retains clients and transport. Do not turn current host/port transport selection into a new credential-resolution pattern.

## Security and secrets handling

Preserve validated discovery/invocation boundaries and secret-safe failures. Caller-derived HTTP clients/signers must remain request-specific; mock token exchange and SDK calls for unit checks. Changing dynamic discovery or invocation can expose behavior across many OCI services; inspect that surface before expanding it.

## Change impact

Discovery, accepted parameters, coercion, response shaping, authentication and transport changes can affect dynamically exposed operations across services. Common changes also affect other consumers and require root shared-change review. Follow [CONTRIBUTING](../../CONTRIBUTING.md) and root changelog rules for the existing [CHANGELOG](CHANGELOG.md); native usage/config changes also affect README.

## Known gaps

- Dynamic operation facts require source/signature/test inspection; another server's tool contract does not define this surface.
- Transport selection still uses host/port inputs; keep the source-observed arrangement distinct from shared credential requirements.
- Configured coverage and mock definitions are not executed results or evidence of live service behavior. See [shared gaps](../../docs/agent-development.md#known-gaps).

## Workflow and context routing

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Changing discovery or accepted arguments | [server.py](oracle/oci_cloud_mcp_server/server.py), native SDK signatures | Root quality guidance and existing class/method validation | [Discovery tests](oracle/oci_cloud_mcp_server/tests/test_discovery_and_shaping.py), [coercion tests](oracle/oci_cloud_mcp_server/tests/test_model_coercion.py) |
| **Do:** Changing the OCI SDK pin or regenerating its catalog | [SDK upgrade procedure](README.md#updating-the-pinned-sdk-and-catalog), [generator](scripts/generate_sdk_catalog.py) | This guide, exact manifest pin, synchronized lock/SDK and reviewed schema exceptions | [Catalog tests](oracle/oci_cloud_mcp_server/tests/test_sdk_catalog.py), generation `--check`, [installed smoke script](scripts/check_installed_catalog.py) and actual run results |
| **Know:** Changing auth or client boundaries | [Server auth/client helpers](oracle/oci_cloud_mcp_server/server.py), [Common contract](../common/README.md) | [Common guide](../common/AGENTS.md), caller-specific HTTP context | [Bootstrap tests](oracle/oci_cloud_mcp_server/tests/test_bootstrap_and_introspection.py), owning auth tests |
| **Know:** Changing operation results or traversal | Invocation/serialization helpers in [server.py](oracle/oci_cloud_mcp_server/server.py) | Dynamic operation signatures and shared quality/compatibility guidance | [Invocation tests](oracle/oci_cloud_mcp_server/tests/test_pagination_and_invocation.py), [serialization tests](oracle/oci_cloud_mcp_server/tests/test_models_and_serialization.py) |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map), [manifest](pyproject.toml) | Package environment, Common workspace and actual change scope | Current run reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

Keep shared source reuse and local differences visible. The adoption's Now/Proof record is the [summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md); it does not certify runtime behavior or every dynamic SDK operation.
