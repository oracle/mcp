# Changelog

## Unreleased

### Tool surface

- Clarified `list_jobs` sorting guidance so ordinary inventory requests omit
  optional sorting, while retaining the OCI SDK's documented sort values.
- Added the `database-and-infra-observability-metric-catalog` skill with local
  metric catalog search/get/list handlers, a catalog-validated live OCI
  Monitoring metric reader, and read-only OCI Monitoring alarm definition and
  status operations.
- Added capability-first classification, AWR fallback, and single-target
  validation checkpoints to health and AWR skill prompts.

## 0.1.0 - 2026-08-05

### Server

- Unified, read-only Oracle Database Observability MCP server for OCI
  Operations Insights (OPSI) and Database Management (DBM).

### Transports

- STDIO and HTTP streaming transports.

### Authentication

- Configured OCI authentication through `oracle-mcp-common`, including
  API-key, security-token, instance-principal, and resource-principal flows.

### Tool surface

- Explicit-compartment scope discovery through `get_oci_compartment` and
  `list_oci_compartments`.
- Catalog discovery and dispatch through `list_dbo_skills`, `list_dbo_tools`,
  `describe_dbo_tool`, and `invoke_dbo_tool`.
- 34 workflow skills and 229 read-only OPSI/DBM SDK-backed catalog operations.

### Package and entry point

- Distribution: `oracle.oci-db-observability-mcp-server`.
- Console entry point: `oracle.oci-db-observability-mcp-server`.
- Python package: `oracle.oci_db_observability_mcp_server`.
- Discovery guidance permits reuse of applicable skill, tool, and schema
  information from earlier calls instead of requiring the full workflow for
  every invocation.
