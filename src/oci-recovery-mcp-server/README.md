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

- get_compartment_by_name_tool(name) -> str
- list_protected_databases(compartment_id, lifecycle_state=None, display_name=None, id=None, protection_policy_id=None, recovery_service_subnet_id=None, limit=None, page=None, sort_order=None, sort_by=None, opc_request_id=None, region=None) -> list[ProtectedDatabaseSummary]
- get_protected_database(protected_database_id, opc_request_id=None, region=None) -> ProtectedDatabase
- summarize_protected_database_health(compartment_id=None, region=None) -> ProtectedDatabaseHealthCounts
- summarize_protected_database_redo_status(compartment_id=None, region=None) -> ProtectedDatabaseRedoCounts
- summarize_backup_space_used(compartment_id=None, region=None) -> ProtectedDatabaseBackupSpaceSum
- list_protection_policies(compartment_id, lifecycle_state=None, display_name=None, id=None, limit=None, page=None, sort_order=None, sort_by=None, opc_request_id=None, region=None) -> list[ProtectionPolicySummary]
- get_protection_policy(protection_policy_id, opc_request_id=None, region=None) -> ProtectionPolicy
- list_recovery_service_subnets(compartment_id, lifecycle_state=None, display_name=None, id=None, vcn_id=None, limit=None, page=None, sort_order=None, sort_by=None, opc_request_id=None, region=None) -> list[RecoveryServiceSubnetSummary]
- get_recovery_service_subnet(recovery_service_subnet_id, opc_request_id=None, region=None) -> RecoveryServiceSubnet
- get_recovery_service_metrics(compartment_id, start_time, end_time, metricName="SpaceUsedForRecoveryWindow", resolution="1h", aggregation="max", protected_database_id=None) -> list[dict]
- list_databases(compartment_id=None, db_home_id=None, system_id=None, limit=None, page=None, sort_by=None, sort_order=None, lifecycle_state=None, db_name=None, region=None) -> list[DatabaseSummary]
- get_database(database_id, region=None) -> Database
- list_backups(compartment_id=None, database_id=None, lifecycle_state=None, type=None, limit=None, page=None, region=None) -> list[BackupSummary]
- get_backup(backup_id, region=None) -> Backup
- summarize_protected_database_backup_destination(compartment_id=None, region=None, db_home_id=None, include_last_backup_time=False) -> ProtectedDatabaseBackupDestinationSummary
- get_db_home(db_home_id, region=None) -> DatabaseHome
- list_db_systems(compartment_id=None, lifecycle_state=None, limit=None, page=None, region=None) -> list[DbSystemSummary]
- get_db_system(db_system_id, region=None) -> DbSystem

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
