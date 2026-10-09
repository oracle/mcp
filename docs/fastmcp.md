# FastMCP engineering guidance

Use this guide for Python MCP registration, schemas, lifecycle, transport and contract tests. [BEST_PRACTICES](../BEST_PRACTICES.md#fastmcp), [shared authentication](authentication.md) and the applicable [component guide](agent-development.md#selected-component-context) supply requirements and local constraints. This is repository guidance, not a claim that every server implements it.

## Library and version

Identify the actual import, direct manifest and resolved lock before choosing an API. The two similarly named implementations are not interchangeable.

| Selected scope at source baseline `6e6c3e5` | Import and resolved version | Owning sources |
| --- | --- | --- |
| Cloud | `from fastmcp import FastMCP`; standalone 3.4.5, underlying `mcp` 1.29.0 | [Server](../src/oci-cloud-mcp-server/oracle/oci_cloud_mcp_server/server.py), [manifest](../src/oci-cloud-mcp-server/pyproject.toml), [lock](../src/oci-cloud-mcp-server/uv.lock) |
| Common | Standalone FastMCP auth integrations; manifest `>=3.4.5,<4.0.0`, lock 3.4.8 | [Auth](../src/common/oracle_mcp_common/auth.py), [manifest](../src/common/pyproject.toml), [lock](../src/common/uv.lock) |
| Data Studio | `from mcp.server.fastmcp import FastMCP`; SDK `mcp` 1.28.1. Its manifest also declares standalone 3.4.5 | [Server](../src/oracle-data-studio-mcp-server/oracle/data_studio_mcp_server/server.py), [manifest](../src/oracle-data-studio-mcp-server/pyproject.toml), [lock](../src/oracle-data-studio-mcp-server/uv.lock) |

Recheck these sources for later changes; neither dependency presence nor a common class name establishes runtime use. Do not change pins to make an example work.

## Tool contracts

Typed signatures expose tool inputs; return types and result shaping expose outputs. Make parameter descriptions, constraints, defaults and errors understandable to a caller. Verify the advertised schema and serialized result with the selected library's APIs. The [version-tagged standalone tool documentation](https://github.com/PrefectHQ/fastmcp/blob/v3.4.5/docs/servers/tools.mdx) describes registration, schemas, thread dispatch and error masking for that release.

Keep [repository Pydantic Field conventions](../BEST_PRACTICES.md#function-parameters-with-pydantic-field), stable tool names and package-owned response contracts. Explain limits and incomplete results through [pagination guidance](pagination.md); avoid double-encoding structured output as JSON text without a compatibility reason. Descriptions should explain the task, important inputs and effects rather than repeat the function name.

Choose truthful annotations using [tool safety](tool-safety.md#server-safeguards). Generic operation dispatchers need effect analysis for the selected operation; a single tool name cannot make every invocation read-only.

## Lifecycle and isolation

Keep startup/cleanup in the owning runtime lifecycle. Release acquired clients and other resources on shutdown and partial initialization failure. When embedding an HTTP app, follow that version's ASGI/session-manager lifecycle instead of assuming the standalone and SDK mounting APIs match. The [SDK 1.28.1 server source](https://github.com/modelcontextprotocol/python-sdk/blob/v1.28.1/src/mcp/server/fastmcp/server.py) supplies its lifecycle interface; Data Studio's `app_lifespan` is a local example, not a shared OCI-auth implementation.

Common supplies credential ingredients; the server retains listener setup, request-token retrieval and service-client lifecycle. For IDCS HTTP exchange, derive clients from the actual caller token and preserve caller-specific state. Do not store one caller's signer/client globally or select credentials from a listener's host/port. Read [Common's HTTP contract](../src/common/README.md#http-idcs-authentication) and [root requirements](../AGENTS.md#mcp-server-quality-validation).

Avoid synchronous network calls directly inside async handlers without an intentional execution strategy. Standalone 3.4.5 dispatches synchronous tools to threads; async handlers still need async I/O or a suitable offload for blocking SDK calls. Consider client thread safety, context propagation and cancellation. A tool timeout can end the response while external work has already happened; it does not prove rollback.

Sanitize client-facing errors and logs separately. In standalone 3.4.5, explicit `ToolError` messages remain caller-visible even with error masking; use safe messages. An SDK error class or settings interface must be verified separately. Protect stdio's protocol channel from diagnostic prints, and keep credentials and caller data out of examples and logs.

## Testing

Standalone [in-memory transport](https://gofastmcp.com/v3/clients/transports#in-memory-transport) supports `Client(mcp)` without starting a subprocess or binding a port. Cloud already exercises it in [model coercion tests](../src/oci-cloud-mcp-server/oracle/oci_cloud_mcp_server/tests/test_model_coercion.py). In-memory tests share process state, so fixtures must restore caches/environment and cannot certify process or HTTP isolation.

Test discovered tool names, important schema constraints, representative calls, returned structured content and error behavior when those contracts change. Use the selected implementation's client/exception conventions; do not transplant standalone client assertions into an SDK-only server without verifying compatibility. Prefer an existing package test as the runnable example. Use [test quality](test-quality.md) and [native validation](agent-development.md#validation-map); mocked/in-memory tests do not establish live OCI authentication or deployed transport security.

Official sources were inspected on 2026-10-07 at the linked versions. Unversioned documentation can evolve; verify new API examples against the target lock and source before adopting them.
