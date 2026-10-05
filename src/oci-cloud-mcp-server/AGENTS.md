# Cloud engineering context

## Scope and ownership

This Python server discovers and invokes OCI SDK operations dynamically; it owns discovery/schema shaping, coercion, invocation, serialization and transport/client setup. Apply [root instructions](../../AGENTS.md) and [shared engineering context](../../docs/agent-development.md#start-here). Common owns shared Python credential resolution, not this dynamic operation surface.

## Entry points

- [server.py](oracle/oci_cloud_mcp_server/server.py): SDK class/method validation, signatures, coercion helpers, operation execution and auth/transport wiring.
- [Package metadata](oracle/oci_cloud_mcp_server/__init__.py): project/version used for user-agent derivation.
- [Tests](oracle/oci_cloud_mcp_server/tests): concern-specific discovery, coercion, invocation, shaping, serialization and bootstrap definitions.
- [Manifest](pyproject.toml) and [Moon dependency](moon.yml): Common workspace dependency, package entry point and coverage configuration; [README](README.md): native usage.

## Setup / build / run

From the repository root, use `make sync project=oci-cloud-mcp-server` and `make build project=oci-cloud-mcp-server`. Locked `uv sync --directory src/oci-cloud-mcp-server --locked --all-extras --dev` and `moon run oci-cloud-mcp-server:build` are defined alternatives. Preserve the Common workspace relationship. Use README for transport/auth setup; no live SDK invocation is needed for documentation validation. See the [validation map](../../docs/agent-development.md#validation-map).

## Tests and validation

Root policy uses `make test project=oci-cloud-mcp-server` and `make lint` after Python changes; `moon run oci-cloud-mcp-server:test` provides package-scoped feedback with different aggregate behavior. The manifest configures 90% coverage; no checks have run by virtue of this guide.

Start with [model coercion](oracle/oci_cloud_mcp_server/tests/test_model_coercion.py), [helper branches](oracle/oci_cloud_mcp_server/tests/test_helper_branches.py), [discovery/shaping](oracle/oci_cloud_mcp_server/tests/test_discovery_and_shaping.py), [models/serialization](oracle/oci_cloud_mcp_server/tests/test_models_and_serialization.py), [bootstrap/introspection](oracle/oci_cloud_mcp_server/tests/test_bootstrap_and_introspection.py) or [invocation/traversal](oracle/oci_cloud_mcp_server/tests/test_pagination_and_invocation.py) for the affected concern. Tests use SDK/token mocks; real OCI execution is a separate runtime action.

## Architecture and dependencies

Trace signature normalization, `_coerce_params_to_oci_models()`, invocation and serialization together when changing input/output behavior. Class/method validation constrains the dynamic surface; service-specific assumptions must be checked against actual SDK signatures and tests.

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
| **Know:** Changing auth or client boundaries | [Server auth/client helpers](oracle/oci_cloud_mcp_server/server.py), [Common contract](../common/README.md) | [Common guide](../common/AGENTS.md), caller-specific HTTP context | [Bootstrap tests](oracle/oci_cloud_mcp_server/tests/test_bootstrap_and_introspection.py), owning auth tests |
| **Know:** Changing operation results or traversal | Invocation/serialization helpers in [server.py](oracle/oci_cloud_mcp_server/server.py) | Dynamic operation signatures and shared quality/compatibility guidance | [Invocation tests](oracle/oci_cloud_mcp_server/tests/test_pagination_and_invocation.py), [serialization tests](oracle/oci_cloud_mcp_server/tests/test_models_and_serialization.py) |
| **Do:** Preparing or validating a change | [Validation map](../../docs/agent-development.md#validation-map), [manifest](pyproject.toml) | Package environment, Common workspace and actual change scope | Current run reports; [evidence routes](../../docs/agent-development.md#evidence-and-context-routes) |

Keep shared source reuse and local differences visible. The adoption's Now/Proof record is the [summary](../../docs/plans/adopt-monorepo-agent-context/adoption-summary.md); it does not certify runtime behavior or every dynamic SDK operation.
