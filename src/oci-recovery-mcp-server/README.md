# OCI Recovery Service MCP Server

OCI Model Context Protocol (MCP) server exposing Oracle Cloud Recovery Service operations as MCP tools.

## Features

- List Protected Databases with rich filtering (compartment, lifecycle_state, display_name, id, protection_policy_id, recovery_service_subnet_id, limit, page, sort_order, sort_by, opc_request_id, region).
- Mapping of OCI SDK models to Pydantic for safe, serializable responses.

## Install

From this repository root:

```
make build
uv pip install ./src/oci-recovery-mcp-server
```

Or directly inside the package directory:

```
cd src/oci-recovery-mcp-server
uv build
uv pip install .
```

## Usage

Run the MCP server (HTTP transport is optional):

```
# environment variables (optional)
export ORACLE_MCP_HOST=127.0.0.1
export ORACLE_MCP_PORT=7337

# run
uv run oracle.oci-recovery-mcp-server
```

The server reads OCI auth from your OCI CLI config/profile:
- Uses the profile in $OCI_CONFIG_PROFILE (defaults to DEFAULT)
- Uses security token file signer with the private key specified in config

## Tools

- list_protected_databases(compartment_id, lifecycle_state=None, display_name=None, id=None, protection_policy_id=None, recovery_service_subnet_id=None, limit=None, page=None, sort_order=None, sort_by=None, opc_request_id=None, region=None) -> list[ProtectedDatabaseSummary]

## Development

- Code style/format/lint/test tasks are managed via Makefile:
  - `make build` — builds all sub-packages
  - `make install` — installs all sub-packages into current environment
  - `make test` — runs unit tests
  - `make lint` — runs linters
  - `make format` — formats code

## License

Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
