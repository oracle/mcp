# Compute authentication: current implementation and shared requirements

This document explains Compute's OCI client authentication and how it relates to Common. It is a descriptive topic slice based on the [source identities recorded for this increment](../../../docs/plans/apply-agent-context-guide/scope-and-reuse.md#source-identities), not a migration design, approved exception or executed security assessment. Apply [root instructions](../../../AGENTS.md) and the broad [Compute guide](../AGENTS.md). Recheck current source when changing authentication.

## Shared prerequisites and ownership

Read the [repository-level authentication integration guide and adoption ledger](../../../docs/authentication.md), [root server-quality requirements](../../../AGENTS.md#mcp-server-quality-validation), [shared OCI SDK authentication guidance](../../../BEST_PRACTICES.md#oci-sdk-authentication) and [Common's authentication contract](../../common/README.md#authentication-module) first. For HTTP, also read [Common's HTTP IDCS contract](../../common/README.md#http-idcs-authentication). Those sources own the shared requirements and public API; this document explains Compute's local differences.

Common resolves config/signer ingredients through `build_auth_context()`. Its HTTP API builds provider policy through `build_idcs_http_auth()` and derives request auth through `context_for()` with an explicitly supplied token. Servers retain their service client type, listener, request-token retrieval, client lifecycle, retry/circuit-breaker choices and metadata-derived user agent. See [Common's guide](../../common/AGENTS.md) for public exports, consumers and validation scope. These Common capabilities must not be inferred to exist in Compute merely because both live in this monorepo.

## Current Compute paths

[server.py](../oracle/oci_compute_mcp_server/server.py) owns `main()`, `_get_http_config_and_signer()`, `get_compute_client()` and `_get_oci_client_kwargs()`. The [native README](../README.md#running-the-server) owns runtime invocation and callback setup; it need not be duplicated here.

| Selected local path | Source behavior | Boundary or limitation |
| --- | --- | --- |
| Startup without both `ORACLE_MCP_HOST` and `ORACLE_MCP_PORT` | `main()` calls `mcp.run()`; the HTTP signer helper returns `(None, None)` | Host alone or port alone does not select HTTP in this implementation |
| Profile-backed client | `get_compute_client()` loads `OCI_CONFIG_FILE` / `OCI_CONFIG_PROFILE` with OCI SDK defaults, loads `key_file`, reads `security_token_file` and constructs `SecurityTokenSigner` | This path expects a security-token profile; it does not call Common or select Common's API-key/principal modes |
| HTTP startup with both host and port | `main()` requires IDCS domain/client ID/client secret/audience/public base URL and assigns a locally constructed `OCIProvider`; it uses `IDCS_REQUIRED_SCOPES` or the derived default `openid profile email oci_mcp.compute.invoke` | Listener/provider configuration remains server-owned; startup is distinct from request-time signer construction |
| HTTP request client | `_get_http_config_and_signer()` retrieves `get_access_token()`, rejects a missing token, requires IDCS domain/client ID/client secret and `OCI_REGION`, then constructs `TokenExchangeSigner`; `get_compute_client()` creates a `ComputeClient` from that config/signer | This helper chooses the credential path using host/port environment variables; it does not call Common's explicit-token API |

Both client paths derive `additional_user_agent` from package metadata. `_get_oci_client_kwargs()` supplies the local circuit-breaker configuration and the signer. The factory constructs a client on each call; no HTTP signer/client cache is present in these helpers. That source observation does not establish tested caller isolation, successful token exchange or a live deployment's security properties.

## Differences that remain unresolved

- Compute's [manifest](../pyproject.toml) has no `oracle-mcp-common` dependency, and the client/provider helpers implement credentials locally. Root/shared guidance requires Common use for SDK-backed servers; documenting this legacy implementation does not waive that requirement.
- Root/shared HTTP guidance prohibits selecting credentials by host/port. Compute currently uses those variables in the signer helper as well as startup. Keep listener selection distinct from credential policy in future auth work; this increment changes neither.
- Common's [profile contract](../../common/README.md#profile-backed-authentication) classifies security tokens from the selected profile's direct declaration, excludes inherited DEFAULT tokens for named profiles and fails without API-key fallback after a configured-token failure. Compute reads the SDK-loaded config and requires its token/key entries without Common's raw-profile classifier. Do not claim Common's inheritance safeguard or full mode/precedence contract for this local path.
- Common's HTTP API validates provider inputs, accepts explicit caller tokens and sanitizes signer-construction errors. Compute's local helpers must be assessed on their own source/tests; Common's tests do not validate them. No new local policy exception or migration schedule is established here.

For a later implementation change, inspect interfaces and tests against the shared contracts, then update this explanation, the native README where behavior changes, and applicable routes. Broader consumer changes and validation belong to that engineering task's scope.

## Supporting definitions and evidence limits

| Claim or question | Owning source / available check definition | What this increment establishes |
| --- | --- | --- |
| Shared input precedence, direct-profile token classification and failure behavior | [Common README](../../common/README.md#configuration-precedence), [auth.py](../../common/oracle_mcp_common/auth.py), [auth tests](../../common/oracle_mcp_common/tests/test_auth.py), including `test_profile_classifier_excludes_default_inheritance` and `test_auto_direct_unreadable_token_fails_without_api_key_fallback` | Source relationship reviewed; tests not executed |
| Shared HTTP provider/request ownership | [HTTP contract](../../common/README.md#http-idcs-authentication), `build_idcs_http_auth()` / `IDCSHttpAuth.context_for()` in [auth.py](../../common/oracle_mcp_common/auth.py), `test_idcs_http_auth_builds_provider_and_creates_request_context` in [auth tests](../../common/oracle_mcp_common/tests/test_auth.py) | API and test definition reviewed; no live exchange |
| Compute profile selection and client configuration | `TestGetClient.test_get_compute_client_with_profile_env` and `test_get_compute_client_uses_default_profile_when_env_missing` in [tool tests](../oracle/oci_compute_mcp_server/tests/test_compute_tools.py) | Mocked check definitions exist; the explicit-profile test asserts the exact derived user agent, while the default-profile test only checks its string shape |
| Compute HTTP helper and startup branches | `TestServer.test_http_signer_uses_region_without_loading_config`, token/region error cases, and `test_main_with_host_and_port`, `test_main_without_host_and_port`, `test_main_with_only_host`, `test_main_with_only_port` in [tool tests](../oracle/oci_compute_mcp_server/tests/test_compute_tools.py) | Available mocked assertions identified; they do not establish all root-required auth-path/user-agent/isolation coverage or passing results |
| Install and test/coverage definitions | [Compute manifest](../pyproject.toml), [Common manifest](../../common/pyproject.toml), [validation map](../../../docs/agent-development.md#validation-map) | Definitions only; Common README/manifest dependency-version discrepancy remains in the [existing gap register](../../../docs/agent-development.md#known-gaps) |

The [separate application outcome](../../../docs/plans/apply-agent-context-guide/outcome.md) records documentation checks. Application builds, lint, tests, coverage, deployments and fresh-consumer evaluations were not run for this increment. The historical adoption evaluation is scoped to its earlier guidance identity.
