# OCI JMS MCP Server Implementation Guide

Implement `src/oci-jms-mcp-server` as a standard, service-specific OCI Python MCP server.

Do not invent a new architecture for JMS. Match the structure and coding style already used by the mature Python OCI MCP servers in this repository.

## Goal

Build `oci-jms-mcp-server` as a read-only v1 focused on fleet inventory and discovery in OCI Java Management Service (JMS).

The implementation must follow the same patterns used by:

- `src/oci-compute-mcp-server`
- `src/oci-networking-mcp-server`
- `src/oci-monitoring-mcp-server`
- `src/oci-usage-mcp-server`

Use those servers as the source of truth for packaging, client bootstrap, tool layout, model mapping, tests, and README style.

## Required Files

Create and maintain this exact package-local file set:

- `src/oci-jms-mcp-server/pyproject.toml`
- `src/oci-jms-mcp-server/README.md`
- `src/oci-jms-mcp-server/oracle/oci_jms_mcp_server/__init__.py`
- `src/oci-jms-mcp-server/oracle/oci_jms_mcp_server/server.py`
- `src/oci-jms-mcp-server/oracle/oci_jms_mcp_server/models.py`
- `src/oci-jms-mcp-server/oracle/oci_jms_mcp_server/tests/test_jms_tools.py`
- `src/oci-jms-mcp-server/oracle/oci_jms_mcp_server/tests/test_jms_models.py`

Do not add repo-wide shared abstractions just to support JMS.

## Package Structure Pattern

Follow the same package envelope used by the other Python OCI servers:

1. `pyproject.toml`
   - Python package name: `oracle.oci-jms-mcp-server`
   - entrypoint: `oracle.oci-jms-mcp-server = "oracle.oci_jms_mcp_server.server:main"`
   - use `hatchling`
   - depend on `fastmcp`, `oci`, and `pydantic`
   - include the usual dev dependencies for `pytest`, `pytest-asyncio`, and `pytest-cov`

2. `README.md`
   - short overview
   - stdio run command
   - HTTP transport run command using `ORACLE_MCP_HOST` and `ORACLE_MCP_PORT`
   - a tool table listing the JMS tools implemented
   - the same OCI credential/safety note used in peer servers

3. `__init__.py`
   - preserve the standard Oracle copyright header
   - define `__project__` and `__version__`

## Server Implementation Pattern

`server.py` must look and behave like the service-specific servers, not like `oci-cloud-mcp-server`.

### Required bootstrap

- Add the standard Oracle license header.
- Import `__project__` and `__version__` from the package.
- Create `logger = Logger(__name__, level="INFO")`.
- Create `mcp = FastMCP(name=__project__)`.

### Required client helper

Implement `get_jms_client()` using the same pattern as compute, networking, monitoring, usage, registry, and resource-search:

1. load OCI config with:
   - `file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION)`
   - `profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)`
2. derive the user agent name from `__project__`
3. set `config["additional_user_agent"] = f"{user_agent_name}/{__version__}"`
4. load the private key from `config["key_file"]`
5. read the security token from `config["security_token_file"]`
6. create `oci.auth.signers.SecurityTokenSigner`
7. return `oci.jms.JavaManagementServiceClient(config, signer=signer)`

Do not replace this with a generic helper module or a dynamic client loader.

### Required `main()`

Implement:

- stdio mode by default
- HTTP mode only when both `ORACLE_MCP_HOST` and `ORACLE_MCP_PORT` are set
- `mcp.run(transport="http", host=host, port=int(port))` when HTTP is enabled
- `mcp.run()` otherwise

Keep the entrypoint in `server.py`. Do not create `main.py`.

## Tool Design Pattern

Use hand-written `@mcp.tool` functions exactly like the other service servers.

### Tool rules

- Each tool must have a clear description.
- Use `pydantic.Field` metadata for required and optional parameters where it adds clarity.
- Use `Literal` for constrained enum-like values when practical.
- Return typed Pydantic models, not raw OCI SDK objects.
- Catch exceptions only for lightweight logging and then re-raise.
- Paginate list-style APIs manually using `has_next_page` and `next_page`.
- Stop pagination when the server-provided page stream ends or the requested `limit` has been satisfied.

### V1 JMS tool set

Implement this exact read-only tool set first:

- `list_fleets`
- `get_fleet`
- `list_jms_plugins`
- `get_jms_plugin`
- `list_installation_sites`
- `get_fleet_agent_configuration`
- `get_fleet_advanced_feature_configuration`
- `summarize_resource_inventory`
- `summarize_managed_instance_usage`

Use the OCI SDK call shapes that are already available in `oci.jms.JavaManagementServiceClient`.

### Scope boundaries for v1

Do not add these in v1:

- create/update/delete fleet operations
- create/update/delete JMS plugin operations
- analysis request submission APIs
- DRS file mutation APIs
- task schedule mutation APIs
- generic OCI SDK invocation

The first cut must be read-only and inventory-focused.

## Model Design Pattern

`models.py` must mirror the approach used by compute, networking, registry, and other typed servers.

### Required model rules

- Use Pydantic `BaseModel`.
- Add field descriptions.
- Keep field names aligned with OCI SDK attribute names.
- Add nested Pydantic models only when needed for stable serialization.
- Implement explicit `map_*` functions for every top-level returned OCI SDK model.
- Return `None` from mappers when the input is `None`.
- Preserve datetimes as datetimes.
- Preserve optional fields as optional.

### V1 model set

Implement only the models required for the v1 tools:

- `FleetSummary`
- `Fleet`
- `JmsPluginSummary`
- `JmsPlugin`
- `InstallationSiteSummary`
- `FleetAgentConfiguration`
- `FleetAdvancedFeatureConfiguration`
- `ManagedInstanceUsageSummary`
- `ResourceInventory`

Add nested models only when they are actually present in those responses and would otherwise serialize poorly.

Do not attempt to mirror the entire JMS SDK in v1.

## Testing Pattern

Follow the package-local test layout used by the other Python OCI servers.

### `test_jms_tools.py`

Use `fastmcp.Client` and patch `get_jms_client()`.

Required coverage:

- happy-path test for each tool
- at least one paginated list test
- at least one paginated summarize/list-style usage test
- exception propagation test for a list tool
- exception propagation test for a get tool
- `main()` transport selection tests
- `get_jms_client()` test verifying:
  - config loading
  - token file read
  - signer creation
  - `additional_user_agent` assignment
  - `JavaManagementServiceClient` instantiation

### `test_jms_models.py`

Required coverage:

- mapper test for each top-level model returned by the tools
- nested object mapping where applicable
- datetime preservation
- optional and missing field handling

## Reference Patterns To Copy

Use these files as implementation references:

- `src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/server.py`
  - classic service-specific tool layout
- `src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/models.py`
  - typed Pydantic models plus explicit `map_*` helpers
- `src/oci-networking-mcp-server/oracle/oci_networking_mcp_server/server.py`
  - straightforward client bootstrap and paginated list tools
- `src/oci-monitoring-mcp-server/oracle/oci_monitoring_mcp_server/server.py`
  - richer read-only tool descriptions and optional filtering
- `src/oci-usage-mcp-server/oracle/oci_usage_mcp_server/server.py`
  - minimal `main()` and client bootstrap pattern
- `src/oci-usage-mcp-server/oracle/oci_usage_mcp_server/tests/test_usage_tools.py`
  - server bootstrap and client helper tests

## Anti-Patterns To Avoid

Do not do any of the following:

- do not build JMS as a generic OCI API wrapper
- do not use the `oci-cloud-mcp-server` dynamic invocation design
- do not return raw OCI SDK model objects from tools
- do not skip Pydantic mapping because `oci.util.to_dict` is easier
- do not add mutating JMS tools in v1
- do not create repo-wide helpers just to reduce duplication
- do not omit `main()`
- do not omit tests
- do not leave the README or `pyproject.toml` out of sync with the tool surface

## Verification Checklist

Before considering the JMS server complete, verify all of the following:

- `src/oci-jms-mcp-server/pyproject.toml` exists and defines the correct package script
- the package imports successfully
- `server.py` exposes `mcp`, `get_jms_client()`, and `main()`
- stdio and HTTP transport behavior are both tested
- all v1 tools are registered and callable through `fastmcp.Client`
- list-style tools paginate correctly
- outputs are typed and serialized through Pydantic models
- `get_jms_client()` sets `additional_user_agent`
- README documents the final v1 tool list
- package-local tests pass

## Implementation Defaults

If a decision is not explicitly documented elsewhere, use these defaults:

- prefer read-only behavior
- prefer service-specific typed tools
- prefer explicit mappers over clever abstractions
- prefer matching peer server patterns over reducing line count
- prefer the smallest model set that fully supports the v1 JMS tools
