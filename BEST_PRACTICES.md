# MCP Server Best Practices

This document lays out the best practices for an individual MCP server. You may use `oci-compute-mcp-server` as an example.

## Typical MCP Server Structure

```
mcp-server-name/
├── LICENSE.txt             # License information
├── pyproject.toml          # Project configuration
├── README.md               # Project description, setup instructions
├── uv.lock                 # Dependency lockfile
└── oracle/                 # Source code directory
    ├── __init__.py         # Package initialization
    └── mcp_server_name/    # Server package, notice the underscores
        ├── __init__.py     # Package version and metadata
        ├── models.py       # Pydantic models
        ├── server.py       # Server implementation
        ├── consts.py       # Constants definition
        ├── ...             # Additional modules
        └── tests/          # Test directory
```

## Code Organization

1. **Separation of Concerns**:
   - `models.py`: Define data models and validation logic
   - `server.py`: Implement MCP server, tools, and resources
   - `consts.py`: Define constants used across the server
   - Additional modules for specific functionality (e.g., API clients)

2. **Keep modules focused and limited to a single responsibility**

3. **Use clear and consistent naming conventions**

### Code quality

- Add abstractions and helpers for demonstrated behavior, meaningful boundaries or reuse; avoid speculative frameworks and pass-through wrappers that add no responsibility.
- Reuse owning common packages instead of duplicating their logic. Preserve package-owned client and lifecycle decisions.
- Handle expected errors explicitly; do not turn an unexpected failure into a successful empty/default result.
- Keep type/lint suppressions narrow and justified, comments explanatory, and changes focused on the requested behavior.

Use [code-quality criteria and examples](docs/code-quality.md#review-criteria) when implementing or reviewing these requirements.

### Entry Points

MCP servers should follow these guidelines for application entry points:

1. **Single Entry Point**: Define the main entry point only in `server.py`
   - Do not create a separate `main.py` file
   - This maintains clarity about how the application starts

2. **Main Function**: Implement a `main()` function in `server.py` that:
   - Handles command-line arguments
   - Sets up environment and logging
   - Initializes the MCP server

Example:

```python
def main():
    """Run the MCP server with CLI argument support."""
    mcp.run()


if __name__ == '__main__':
    main()
```

3. **Package Entry Point**: Configure the entry point in `pyproject.toml`:

```toml
[project.scripts]
"oracle.mcp-server-name" = "oracle.mcp_server_name.server:main"
```

## License and Copyright Headers

Include license headers at the top of each source file:

```python
"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""
```

## OCI SDK user-agent telemetry

Every server that constructs OCI Python SDK clients must attach a consistent additional user agent to every client configuration path. Derive it from package metadata rather than duplicating a server name or version literal:

```python
# oracle/mcp_server_name/__init__.py
from importlib.metadata import version as distribution_version

__project__ = "oracle.mcp-server-name"
__version__ = distribution_version(__project__)
```

Keep the distribution version only in `pyproject.toml`. Do not add a
`PackageNotFoundError` fallback: importing a package that is not installed in
the active environment should fail instead of exposing stale metadata.

```python
# oracle/mcp_server_name/server.py
from . import __project__, __version__

_user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
_ADDITIONAL_UA = f"{_user_agent_name}/{__version__}"
```

Set the derived value before constructing every OCI SDK client, including API-key, security-token, each supported principal-based path (for example, instance- and resource-principal), and HTTP/token-exchange paths when the server supports them:

```python
config["additional_user_agent"] = _ADDITIONAL_UA
client = oci.some_service.SomeClient(config)
```

Client factories and authentication helpers may live outside `server.py`; the requirement is that every OCI client-construction path receives `_ADDITIONAL_UA`. Unit tests must assert the exact derived value passed through each supported path.

`oci-api-mcp-server` is the exception: it launches the OCI CLI rather than constructing OCI Python SDK clients directly. Set the same derived value on the subprocess environment instead:

```python
env_copy["OCI_SDK_APPEND_USER_AGENT"] = _ADDITIONAL_UA
```

Note: always remove `-server` from the end of the `__project__` name; ex `oci-cloud-mcp`.

## OCI SDK authentication

See the [shared authentication integration guide](docs/authentication.md) for server responsibilities, missing-capability handling and the source-based [adoption ledger](docs/authentication.md#adoption-ledger). Common's README remains the detailed public API contract.

Python MCP servers that construct OCI SDK clients should use the shared
`oracle-mcp-common` package instead of duplicating credential resolution,
profile parsing, environment-variable precedence, or signer construction.
Declare a bounded dependency compatible with the shared library's public API:

```toml
dependencies = [
    "oracle-mcp-common>=0.1.0,<0.2.0",
]
```

Use `build_auth_context()` from `oracle_mcp_common` to obtain the selected
authentication type, SDK config, and signer. The server remains responsible
for its OCI client type, retry and circuit-breaker policy, derived additional
user agent, and client lifecycle:

```python
import oci

from oracle_mcp_common import build_auth_context

auth_context = build_auth_context()
config = {
    **auth_context.config,
    "additional_user_agent": _ADDITIONAL_UA,
}
client = oci.object_storage.ObjectStorageClient(
    config,
    signer=auth_context.signer,
)
```

The module supports API-key, security-token, identity-domain UPST,
instance/resource principal, delegation, and OKE workload-identity flows.
Use `AuthOptions` only when the server needs to explicitly override its
configured authentication inputs. Unit tests must cover every supported
client-construction authentication path and assert the exact additional user
agent passed to the OCI SDK.

### HTTP IDCS request-token authentication

For an HTTP server that authenticates callers through OCI IAM/IDCS and signs
OCI SDK requests as the authenticated caller, use the shared HTTP policy
instead of duplicating `OCIProvider` and `TokenExchangeSigner` setup:

```python
from fastmcp.server.dependencies import get_access_token

from oracle_mcp_common import build_idcs_http_auth

# Startup: the server retains the mcp.auth assignment and HTTP listener setup.
http_auth = build_idcs_http_auth(required_scopes)
mcp.auth = http_auth.provider

# Request handling: retrieve the validated token in the server, then exchange it.
access_token = get_access_token()
request_auth = http_auth.context_for(access_token.token)
config = {**request_auth.config, "additional_user_agent": _ADDITIONAL_UA}
client = oci.object_storage.ObjectStorageClient(config, signer=request_auth.signer)
```

`build_idcs_http_auth()` validates `IDCS_DOMAIN`, `IDCS_CLIENT_ID`,
`IDCS_CLIENT_SECRET`, `IDCS_AUDIENCE`, and `ORACLE_MCP_BASE_URL`; `context_for()`
requires an authenticated access token and a region from an explicit argument
or `OCI_REGION`. The common package must not inspect host/port, start a
listener, assign `mcp.auth`, retrieve request context, create a service client,
or set `additional_user_agent`.

Each HTTP signer and OCI client is caller-specific. Do not cache either
globally or reuse it across requests from different callers. Tests must cover
successful provider setup and token exchange, failures before provider/signer
construction for missing or malformed configuration, secret-safe errors, the
exact derived user agent, and caller-specific client behavior.

## Type Definitions

### General Rules

1. Make all models Pydantic; this ensures serializability. You may refer to the OCI python SDK for reference to most OCI models.
2. Define Literals for constrained values.
3. Add comprehensive descriptions to each field.

Pydantic model example for [NetworkSecurityGroup](src/oci-networking-mcp-server/oracle/oci_networking_mcp_server/models.py)

```python
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

class NetworkSecurityGroup(BaseModel):
    """
    Pydantic model mirroring the fields of oci.core.models.NetworkSecurityGroup.
    """

    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment containing the network security group.",
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name. Does not have to be unique."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource as simple key/value pairs."
    )
    id: Optional[str] = Field(
        None, description="The OCID of the network security group."
    )
    lifecycle_state: Optional[
        Literal[
            "PROVISIONING",
            "AVAILABLE",
            "TERMINATING",
            "TERMINATED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The network security group's current state.")
    time_created: Optional[datetime] = Field(
        None,
        description="The date and time the network security group was created (RFC3339).",
    )
    vcn_id: Optional[str] = Field(
        None, description="The OCID of the VCN the network security group belongs to."
    )
```

The pydantic model above was generated using Cline by providing it a prompt similar to this:
```
Can you create a pydantic model of oci.core.models.NetworkSecurityGroup and put it inside of the oracle/oci_networking_mcp_server/models.py file, and name it NetworkSecurityGroup? Can you also make a function that maps an oci.core.models.NetworkSecurityGroup instance to an oracle.oci_networking_mcp_server.model.NetworkSecurityGroup instance? Do the same for all of the nested types within the model as well

Use file oracle/oci_compute_mcp_server/models.py as an example of how to do this
```

## Function Parameters with Pydantic Field

MCP tool functions should use spread parameters with Pydantic's `Field` for detailed descriptions:

This signature-only illustration uses the parameters of [list_instances](src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/server.py). Its body is deliberately omitted; Compute's current whole-page loop is not a safe hard-total-cap implementation template.

```python
@mcp.tool(description="List Instances in a given compartment")
def list_instances(
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of instances to return. If None, there is no limit.",
        ge=1,
    ),
    lifecycle_state: Optional[
        Literal[
            "MOVING",
            "PROVISIONING",
            "RUNNING",
            "STARTING",
            "STOPPING",
            "STOPPED",
            "CREATING_IMAGE",
            "TERMINATING",
            "TERMINATED",
        ]
    ] = Field(None, description="The lifecycle state of the instance to filter on"),
) -> list[Instance]:
    ...
```

For a hard total cap, apply both safeguards: request only the remaining allowance when the backend supports a page-size argument, and append no more than the remaining allowance even if the backend over-returns. Stop requesting when the cap is met. Trimming a page also needs truthful truncation and continuation handling; see the [partial-page example](docs/pagination.md#limits-and-continuation) and [regression matrix](docs/pagination.md#review-checklist). Whole-page overshoot does not satisfy a promised hard cap.

### Field Guidelines

1. **Required parameters**: Use `...` as the default value to indicate a parameter is required
2. **Optional parameters**: Provide sensible defaults and mark as `Optional` in the type hint
3. **Descriptions**: Write clear, informative descriptions for each parameter
4. **Validation**: Use Field constraints like `ge`, `le`, `min_length`, `max_length`
5. **Literals**: Use `Literal` for parameters with a fixed set of valid values

## Test cases

Enforce at least 90% unit-test coverage for Python MCP servers through the native package configuration; preserve stricter gates. Follow [root quality requirements](AGENTS.md#mcp-server-quality-validation) for other runtimes and documented enforcement gaps.

Tests must assert meaningful behavior and relevant failure paths. Mock external boundaries while exercising the changed validation, conversion and result handling; preserve deterministic fixtures and caller/state isolation. Coverage alone does not establish test quality. See [test design and evidence](docs/test-quality.md).

End-to-end tests under `e2e/` are not required, but good to add if they can be created without impacting other tests.

## FastMCP

Match tool registration, schema/result handling, lifecycle, concurrency and error APIs to the package's actual import and resolved version. Verify protocol-facing changes with suitable contract tests. Keep authentication and caller isolation under their existing owning requirements. See [FastMCP guidance](docs/fastmcp.md).

## Pagination

For new or changed collection contracts, document page size versus total limits, aggregation defaults, completeness and supported continuation. Prefer bounded defaults for new tools; review compatibility before changing existing defaults. Report truncation and partial failure truthfully, and do not advertise continuation that skips unreturned items. See [pagination contracts and examples](docs/pagination.md).

## Tool safety

Apply server safeguards proportional to an operation's effects, reversibility, sensitivity, cost, blast radius and authority changes. Validate caller authorization and targets before service calls. Higher-impact operations require stronger scope/precondition/confirmation safeguards as appropriate; annotations and caller-supplied confirmation strings do not replace authorization.

Report partial and uncertain mutation outcomes distinctly; use backend-supported reconciliation/idempotency rather than blind retry. Preserve credential isolation and sanitize client errors and audit logs. See [server safeguards and agent authorization](docs/tool-safety.md).
