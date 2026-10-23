"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

MCP tool server exposing Oracle GoldenGate operational APIs.

Each @mcp.tool function is a callable tool endpoint used by MCP clients.
"""

import json
import os
import sys
import traceback
from datetime import datetime
from functools import wraps
from threading import Lock
from typing import Any

from anyio import to_thread
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field
from pydantic.fields import FieldInfo

from . import api
from .config import read_config
from .consts import DEFAULT_DOMAIN, PROCESS_NAME_PATTERN, SERVER_NAME, TRAIL_NAME_PATTERN
from .extract_config import build_advanced_extract_parameters
from .http_client import HttpClient
from .map_statement import build_map_statement, normalize_map_statement
from .models import (
    CreateExtractBegin,
    CreateExtractOptions,
    CreateExtractSource,
    CreateReplicatBegin,
    CreateReplicatOptions,
    CreateReplicatSource,
    ExtractAdvancedParameters,
    PrepareCsnMode,
    ReplicatAdvancedParameters,
)
from .process_safety import ensure_generic_start_allowed, validate_initial_load_start
from .replicat_config import build_advanced_replicat_parameters
from .security import redact_text, sanitize_data
from .table_statement import add_as_of_scn_to_table_statements, build_table_statement, normalize_table_statement

cfg = read_config()
client = HttpClient(cfg)
_debug_enabled = os.getenv("OGG_MCP_DEBUG", "false").strip().lower() == "true"
INITIAL_LOAD_CDC_INSTRUCTIONS = """
For an Oracle Initial Load followed by ongoing CDC, do not guess the process order:
1. Create, register, and start the primary CDC Extract first so source changes are captured during the load.
2. Determine an appropriate instantiation SCN after registration.
3. Create the Initial Load Extract with asOfScn set to that instantiation SCN.
4. Start the Initial Load Extract and wait until it has stopped; review its report and resolve any failure.
5. Only after the Initial Load Extract completes and its EXTFILE is available, start the Initial Load Replicat.
   Use start_initial_load_replicat, not the generic start tool, so prerequisites are checked.
6. Wait until the Initial Load Replicat finishes processing the initial-load data.
7. Start the CDC Replicat at the matching instantiation CSN using the required AT CSN or AFTER CSN semantics.
The asOfScn value controls the Initial Load Extract's Oracle flashback query; it is not a process start position.
Call get_initial_load_cdc_workflow for the complete workflow and safety checks.
""".strip()
mcp = FastMCP(
    SERVER_NAME,
    instructions=INITIAL_LOAD_CDC_INSTRUCTIONS,
    debug=_debug_enabled,
    log_level="DEBUG" if _debug_enabled else "WARNING",
)

DEFAULT_MANAGED_PROCESS_SETTINGS = "ogg:managedProcessSettings:Default"
DEFAULT_REPORTCOUNT_PARAMETER = "REPORTCOUNT EVERY 1 MINUTES, RATE"
DEFAULT_WARNLONGTRANS_PARAMETER = "WARNLONGTRANS 1H, CHECKINTERVAL 10M"

READ_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True
)
WRITE_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True
)
LOCAL_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)
_tool_execution_lock = Lock()


def _tool(*, description: str, annotations: ToolAnnotations):
    """Register blocking tools on workers while preserving their public schemas."""
    def register(func):
        @wraps(func)
        async def invoke(*args, **kwargs):
            def execute():
                # Preserve serialized operations and requests.Session ownership,
                # including the check-and-start sequence of guarded mutations.
                with _tool_execution_lock:
                    return func(*args, **kwargs)

            # Do not abandon a mutating worker when the caller cancels: a
            # cancelled MCP response does not mean the backend rolled back.
            return await to_thread.run_sync(execute, abandon_on_cancel=False)

        mcp.tool(description=description, annotations=annotations)(invoke)
        return func

    return register


def _ok(data: Any) -> str:
    """Normalize tool output to string (JSON-encoded for dict/list payloads)."""
    sanitized = sanitize_data(data)
    return sanitized if isinstance(sanitized, str) else json.dumps(sanitized)


def _log_startup(level: str, message: str) -> None:
    """Write startup logs to the launcher file, falling back to stderr."""
    safe_message = redact_text(message)
    log_file = os.getenv("GG_MCP_LOG_FILE")
    if log_file:
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] [{level}] {safe_message}\n")
            return
        except OSError:
            # Preserve diagnostics if launcher file logging is unavailable.
            pass
    print(f"[{level}] {safe_message}", file=sys.stderr, flush=True)


def _verify_deployment_connectivity() -> None:
    """Validate GoldenGate deployment connectivity before serving MCP tools."""
    deployment_url = redact_text(str(cfg.get("baseUrl", "<unknown>")))
    _log_startup("INFO", f"Verifying connectivity to GoldenGate deployment: {deployment_url}")
    try:
        client.get(api.list_domains())
    except Exception as exc:
        _log_startup("ERROR", f"Failed to connect to GoldenGate deployment: {deployment_url} ({redact_text(str(exc))})")
        exc_message = str(exc)
        if " 401 " in exc_message or "401 {" in exc_message or "401" in exc_message:
            _log_startup(
                "ERROR",
                "Authentication to the GoldenGate deployment failed. Verify OGG_USERNAME and the configured password source. If using OGG_PASSWORD_SECRET_OCID, ensure the OCI Secret contains the current GoldenGate password.",
            )
        raise
    _log_startup("INFO", f"Successfully connected to GoldenGate deployment: {deployment_url}")


def _serialize_model(model: Any | None) -> dict[str, Any] | None:
    """Serialize optional Pydantic model to dict with aliases and no null fields."""
    if model is None:
        return None
    return model.model_dump(by_alias=True, exclude_none=True)


def _none_if_fieldinfo(value: Any) -> Any:
    """Convert undecorated FastMCP default FieldInfo values to None for direct Python calls."""
    return None if isinstance(value, FieldInfo) else value


def _default_if_fieldinfo(value: Any) -> Any:
    """Resolve undecorated FastMCP default FieldInfo values for direct Python calls."""
    return value.default if isinstance(value, FieldInfo) else value


def _resolve_begin_value(begin: Any, default: Any = "now") -> Any:
    """Normalize begin parameter values for GoldenGate payloads."""
    begin = _none_if_fieldinfo(begin)
    if begin is None:
        return default
    if isinstance(begin, str):
        return begin.strip() or default
    if hasattr(begin, "model_dump"):
        return begin.model_dump(by_alias=True, exclude_none=True)
    return begin


def _resolve_replicat_checkpoint(
    checkpoint_table: Any,
    advanced_checkpoint_table: Any,
) -> str | None:
    """Resolve a Replicat checkpoint table from top-level or advanced input.

    The GoldenGate REST endpoint requires the checkpoint table in the Replicat
    creation payload, not in MAP options.  Exposing it as a top-level tool
    argument makes the MCP schema easier for LLM clients to discover, while the
    advanced.checkpointTable location is kept for backward compatibility.
    """
    checkpoint_table = _none_if_fieldinfo(checkpoint_table)
    advanced_checkpoint_table = _none_if_fieldinfo(advanced_checkpoint_table)

    top_level = str(checkpoint_table).strip() if checkpoint_table and str(checkpoint_table).strip() else None
    advanced = (
        str(advanced_checkpoint_table).strip()
        if advanced_checkpoint_table and str(advanced_checkpoint_table).strip()
        else None
    )
    if top_level and advanced and top_level != advanced:
        raise ValueError("Conflicting checkpoint table values supplied in 'checkpointTable' and 'advanced.checkpointTable'.")
    return top_level or advanced


def _has_parameter_line(lines: list[str], parameter_name: str) -> bool:
    """Return whether a GoldenGate parameter line is already present."""
    prefix = parameter_name.upper()
    return any(line.strip().upper().startswith(prefix) for line in lines)


def _normalize_distribution_host(value: Any, field_name: str) -> str:
    """Validate and normalize a Distribution Path host field."""
    value = _none_if_fieldinfo(value)
    host = str(value).strip() if value is not None else ""
    if not host:
        raise ValueError(f"{field_name} is required.")
    if "://" in host or any(ch in host for ch in "/?#:"):
        raise ValueError(f"{field_name} must be a hostname only, without protocol, port, path, query, or fragment.")
    return host


@_tool(annotations=READ_ANNOTATIONS, description="Return the list of GoldenGate domains available in OCI GoldenGate deployment. Domains group connections in GoldenGate.")
def list_domains() -> str:
    """Return the list of GoldenGate domains available in OCI GoldenGate deployment. Domains group connections in GoldenGate."""
    return _ok(client.get(api.list_domains()))


@_tool(annotations=READ_ANNOTATIONS, description="Return the list of Connections available in specific GoldenGate domains in OCI GoldenGate deployment. A connection stores the metadata defining connectivity to a source or target.")
def list_connections(domain: str = Field(..., description="GoldenGate domain name")) -> str:
    """Return the list of Connections available in specific GoldenGate domains in OCI GoldenGate deployment. A connection stores the metadata defining connectivity to a source or target."""
    return _ok(client.get(api.list_connections(domain)))


@_tool(annotations=READ_ANNOTATIONS, description="Returns the list of checkpoint tables for a given connection or domains/alias pair. Checkpoints are required when creating Replicat processes.")
def list_checkpoint_tables(
    domainName: str = Field(..., description="GoldenGate domain name"),
    connectionName: str = Field(..., description="GoldenGate connection (alias) name"),
) -> str:
    """Returns the list of checkpoint tables for a given connection or domains/alias pair. Checkpoints are required when creating Replicat processes."""
    data = client.post(
        api.list_checkpoint_tables(domainName, connectionName),
        {
            "name": "report",
            "reportType": "checkpointTables",
            "specification": "*.*",
            "credentials": {"domain": domainName, "alias": connectionName},
        },
    )
    return _ok(data)


@_tool(annotations=READ_ANNOTATIONS, description="Return the list of Extracts (processes that capture data from a source) available in OCI GoldenGate deployment")
def list_extracts() -> str:
    """Return the list of Extracts (processes that capture data from a source) available in OCI GoldenGate deployment."""
    return _ok(client.get(api.list_extracts()))


@_tool(annotations=READ_ANNOTATIONS, description="Return the list of Replicats (processes that replicate data into a target) available in OCI GoldenGate deployment")
def list_replicats() -> str:
    """Return the list of Replicats (processes that replicate data into a target) available in OCI GoldenGate deployment."""
    return _ok(client.get(api.list_replicats()))


@_tool(annotations=READ_ANNOTATIONS, description="Return the list of Distribution Paths available in OCI GoldenGate deployment. A Distribution Path is used to send data to another GoldenGate deployment.")
def list_distribution_paths() -> str:
    """Return the list of Distribution Paths available in OCI GoldenGate deployment. A Distribution Path is used to send data to another GoldenGate deployment."""
    return _ok(client.get(api.list_distribution_paths()))


@_tool(annotations=READ_ANNOTATIONS, description="Return the list of Data Streams available in OCI GoldenGate deployment. A Data Stream exposes GoldenGate data for downstream consumers over AsyncAPI channels.")
def list_data_streams() -> str:
    """Return the list of Data Streams available in OCI GoldenGate deployment. A Data Stream exposes GoldenGate data for downstream consumers over AsyncAPI channels."""
    return _ok(client.get(api.list_data_streams()))


@_tool(annotations=READ_ANNOTATIONS, description="Retrieve a collection of all known trails available in OCI GoldenGate deployment. A trail is a file that stores the captured data. A trail can only have two alphanumeric characters.")
def list_trails() -> str:
    """Retrieve a collection of all known trails available in OCI GoldenGate deployment. A trail is a file that stores the captured data. A trail can only have two alphanumeric characters."""
    return _ok(client.get(api.list_trails()))


@_tool(
    annotations=READ_ANNOTATIONS,
    description=(
        "Return an Extract status. In an Initial Load workflow, wait for STOPPED and then inspect the Extract report "
        "before starting the Initial Load Replicat."
    )
)
def get_extract_status(
    extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN)
) -> str:
    """Return the status of a given Extract in OCI GoldenGate deployment."""
    return _ok(client.get(api.get_extract_status(extractName)))


@_tool(annotations=READ_ANNOTATIONS, description="Return the status of a given Replicat in OCI GoldenGate deployment")
def get_replicat_status(
    replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN)
) -> str:
    """Return the status of a given Replicat in OCI GoldenGate deployment."""
    return _ok(client.get(api.get_replicat_status(replicatName)))


@_tool(annotations=WRITE_ANNOTATIONS, description="Create a new alias or connection in the GoldenGate credential store. If no domain is provided, defaults to OracleGoldenGate.")
def create_connection(
    connection: str = Field(..., description="Connection/alias name in GoldenGate credential store"),
    userid: str = Field(..., description="Database user identifier"),
    connectionPassword: str = Field(..., description="Password for the provided database userid"),
    domain: str | None = Field(None, description="GoldenGate domain; defaults to OracleGoldenGate when omitted"),
) -> str:
    """Create a new alias or connection in the GoldenGate credential store. If no domain is provided, defaults to OracleGoldenGate."""
    resolved_domain = domain.strip() if domain and domain.strip() else DEFAULT_DOMAIN
    data = client.post(
        api.create_connection(resolved_domain, connection, userid, connectionPassword),
        {"userid": userid, "password": connectionPassword},
    )
    return _ok(data)


@_tool(annotations=WRITE_ANNOTATIONS, description="Add TRANDATA at schema level for a given connection. Manage Supplemental Logging for Database Schemas.")
def add_trandata_schema(
    domain: str = Field(..., description="GoldenGate domain name"),
    connection: str = Field(..., description="GoldenGate connection (alias) name"),
    schemaName: str = Field(..., description="Database schema name"),
    nonvalidatedKeysAllowed: bool = Field(False, description="Allow nonvalidated keys for supplemental logging"),
    schedulingColumns: bool = Field(True, description="Enable scheduling columns for supplemental logging"),
    allColumns: bool = Field(False, description="Log all table columns instead of only required key columns"),
    prepareCsnMode: PrepareCsnMode = Field("nowait", description="Prepare CSN mode: nowait, wait, lock, or none"),
) -> str:
    """Add TRANDATA at schema level for a given connection. Manage Supplemental Logging for Database Schemas."""
    nonvalidatedKeysAllowed = _default_if_fieldinfo(nonvalidatedKeysAllowed)
    schedulingColumns = _default_if_fieldinfo(schedulingColumns)
    allColumns = _default_if_fieldinfo(allColumns)
    prepareCsnMode = _default_if_fieldinfo(prepareCsnMode)
    payload = {
        "schemaName": schemaName,
        "nonvalidatedKeysAllowed": nonvalidatedKeysAllowed,
        "schedulingColumns": schedulingColumns,
        "allColumns": allColumns,
        "prepareCsnMode": prepareCsnMode,
        "operation": "add",
    }
    return _ok(client.post(api.add_trandata_schema(domain, connection), payload))


@_tool(annotations=WRITE_ANNOTATIONS, description="Add TRANDATA at table level for a given connection. Manage Supplemental Logging for Database tables.")
def add_trandata_table(
    domain: str = Field(..., description="GoldenGate domain name"),
    connection: str = Field(..., description="GoldenGate connection (alias) name"),
    schemaName: str = Field(..., description="Database schema name"),
    tableName: str = Field(..., description="Database table name"),
    primaryKey: bool = Field(True, description="Log primary-key columns for supplemental logging"),
    schedulingColumns: bool = Field(True, description="Enable scheduling columns for supplemental logging"),
    allColumns: bool = Field(False, description="Log all table columns instead of only required key columns"),
    prepareCsnMode: PrepareCsnMode = Field("nowait", description="Prepare CSN mode: nowait, wait, lock, or none"),
) -> str:
    """Add TRANDATA at table level for a given connection. Manage Supplemental Logging for Database tables."""
    primaryKey = _default_if_fieldinfo(primaryKey)
    schedulingColumns = _default_if_fieldinfo(schedulingColumns)
    allColumns = _default_if_fieldinfo(allColumns)
    prepareCsnMode = _default_if_fieldinfo(prepareCsnMode)
    payload = {
        "tableName": f"{schemaName}.{tableName}",
        "primaryKey": primaryKey,
        "schedulingColumns": schedulingColumns,
        "allColumns": allColumns,
        "prepareCsnMode": prepareCsnMode,
        "operation": "add",
    }
    return _ok(client.post(api.add_trandata_table(domain, connection), payload))


@_tool(annotations=WRITE_ANNOTATIONS, description="Creates a new Extract in OCI GoldenGate deployment to capture data from schemas and tables. The Extract name can have, at most, 8 alphanumeric characters.")
def create_extract(
    extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN),
    trailName: str = Field(..., description="Two-character trail name", min_length=2, max_length=2, pattern=TRAIL_NAME_PATTERN),
    domainName: str = Field(..., description="GoldenGate domain name"),
    connectionName: str = Field(..., description="GoldenGate connection (alias) name"),
    tableStatement: str | None = Field(None, description="Raw TABLE statement(s) for Extract"),
    source: CreateExtractSource | None = Field(None, description="Structured source mapping used to build TABLE statements"),
    options: CreateExtractOptions | None = Field(None, description="Optional structured TABLE statement options"),
    begin: str | CreateExtractBegin | None = Field(
        None,
        description="Optional start position for Extract. Defaults to 'now'. Accepts an ISO-8601 timestamp string or structured CSN payload like {at: {csn: 11}}.",
    ),
    advanced: ExtractAdvancedParameters | None = Field(None, description="Advanced GoldenGate Extract parameters"),
) -> str:
    """Creates a new Extract in OCI GoldenGate deployment to capture data from schemas and tables. The Extract name can have, at most, 8 alphanumeric characters."""
    tableStatement = _none_if_fieldinfo(tableStatement)
    source = _none_if_fieldinfo(source)
    options = _none_if_fieldinfo(options)
    begin = _none_if_fieldinfo(begin)
    advanced = _none_if_fieldinfo(advanced)

    if tableStatement and tableStatement.strip():
        final_table_statement = normalize_table_statement(tableStatement)
    else:
        if not source:
            raise ValueError("Either 'tableStatement' or 'source' must be provided.")
        final_table_statement = build_table_statement(
            {"source": _serialize_model(source), "options": _serialize_model(options)}
        )

    advanced_payload = _serialize_model(advanced) or {}
    advanced_params = build_advanced_extract_parameters(advanced_payload)
    config_lines = [f"EXTRACT {extractName}"]
    ext_trail = advanced_payload.get("extTrail")
    config_lines.append(f"EXTTRAIL {ext_trail.strip() if ext_trail and ext_trail.strip() else trailName}")
    config_lines.append(f"USERIDALIAS {connectionName} DOMAIN {domainName}")
    if not _has_parameter_line(advanced_params, "REPORTCOUNT"):
        config_lines.append(DEFAULT_REPORTCOUNT_PARAMETER)
    if not _has_parameter_line(advanced_params, "WARNLONGTRANS"):
        config_lines.append(DEFAULT_WARNLONGTRANS_PARAMETER)
    config_lines.extend(advanced_params)
    config_lines.append(final_table_statement)

    payload = {
        "config": config_lines,
        "source": {"tranlogs": "integrated"},
        "credentials": {"domain": domainName, "alias": connectionName},
        "managedProcessSettings": DEFAULT_MANAGED_PROCESS_SETTINGS,
        "registration": {"optimized": False},
        "begin": _resolve_begin_value(begin),
        "targets": [{"name": trailName}],
    }
    return _ok(client.post(api.create_extract(extractName), payload))


@_tool(
    annotations=WRITE_ANNOTATIONS,
    description=(
        "Creates an Initial Load Extract that reads source tables directly and writes to an EXTFILE. "
        "For a consistent Oracle flashback snapshot, set asOfScn to emit SQLPREDICATE 'AS OF SCN <scn>' "
        "in the TABLE statement; this is a table-query snapshot, not an Extract process start position."
    )
)
def create_initial_load_extract(
    extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN),
    trailName: str = Field(..., description="Two-character EXTFILE name", min_length=2, max_length=2, pattern=TRAIL_NAME_PATTERN),
    domainName: str = Field(..., description="GoldenGate domain name"),
    connectionName: str = Field(..., description="GoldenGate connection (alias) name"),
    tableStatement: str | None = Field(None, description="Raw TABLE statement(s) for Initial Load Extract"),
    source: CreateExtractSource | None = Field(None, description="Structured source mapping used to build TABLE statements"),
    options: CreateExtractOptions | None = Field(None, description="Optional structured TABLE statement options"),
    encryptionProfile: str | None = Field("LocalWallet", description="GoldenGate encryption profile for the Initial Load Extract"),
    asOfScn: int | None = Field(
        None,
        ge=0,
        description=(
            "Oracle flashback snapshot SCN for the Initial Load Extract. Emits SQLPREDICATE 'AS OF SCN <scn>' "
            "in the TABLE statement; it does not set the Extract process start position."
        ),
    ),
) -> str:
    """Create an Initial Load Extract, optionally reading an Oracle snapshot as of an SCN."""
    tableStatement = _none_if_fieldinfo(tableStatement)
    source = _none_if_fieldinfo(source)
    options = _none_if_fieldinfo(options)
    asOfScn = _none_if_fieldinfo(asOfScn)
    encryptionProfile = _none_if_fieldinfo(encryptionProfile)

    options_payload = _serialize_model(options) or {}
    if asOfScn is not None:
        if options_payload.get("sqlPredicate"):
            raise ValueError("'asOfScn' and 'options.sqlPredicate' are mutually exclusive.")
        options_payload["sqlPredicate"] = f"AS OF SCN {asOfScn}"

    if tableStatement and tableStatement.strip():
        final_table_statement = (
            add_as_of_scn_to_table_statements(tableStatement, asOfScn)
            if asOfScn is not None
            else normalize_table_statement(tableStatement)
        )
    else:
        if not source:
            raise ValueError("Either 'tableStatement' or 'source' must be provided.")
        final_table_statement = build_table_statement(
            {"source": _serialize_model(source), "options": options_payload}
        )

    config_lines = [
        "--- Auto generated Parameter File, do not edit ---",
        f"EXTRACT {extractName}",
        "--- End of auto generated Parameter File ---",
        f"USERIDALIAS {connectionName} DOMAIN {domainName}",
        f"EXTFILE {trailName}, PURGE",
        final_table_statement,
    ]

    payload = {
        "status": "stopped",
        "managedProcessSettings": DEFAULT_MANAGED_PROCESS_SETTINGS,
        "encryptionProfile": encryptionProfile or "LocalWallet",
        "source": "tables",
        "config": config_lines,
    }
    return _ok(client.post(api.create_extract(extractName), payload))


@_tool(annotations=WRITE_ANNOTATIONS, description="Updates an existing Extract in OCI GoldenGate deployment. Accepts the same structured payload as create_extract but performs a PATCH instead.")
def update_extract(
    extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN),
    trailName: str | None = Field(None, description="Two-character trail name", min_length=2, max_length=2, pattern=TRAIL_NAME_PATTERN),
    domainName: str | None = Field(None, description="GoldenGate domain name"),
    connectionName: str | None = Field(None, description="GoldenGate connection (alias) name"),
    tableStatement: str | None = Field(None, description="Raw TABLE statement(s) for Extract"),
    source: CreateExtractSource | None = Field(None, description="Structured source mapping used to build TABLE statements"),
    options: CreateExtractOptions | None = Field(None, description="Optional structured TABLE statement options"),
    advanced: ExtractAdvancedParameters | None = Field(None, description="Advanced GoldenGate Extract parameters"),
) -> str:
    """Updates an existing Extract in OCI GoldenGate deployment. Accepts the same structured payload as create_extract but performs a PATCH instead."""
    trailName = _none_if_fieldinfo(trailName)
    domainName = _none_if_fieldinfo(domainName)
    connectionName = _none_if_fieldinfo(connectionName)
    tableStatement = _none_if_fieldinfo(tableStatement)
    source = _none_if_fieldinfo(source)
    options = _none_if_fieldinfo(options)
    advanced = _none_if_fieldinfo(advanced)

    final_table_statement: str | None = None
    if tableStatement and tableStatement.strip():
        final_table_statement = normalize_table_statement(tableStatement)
    elif source:
        final_table_statement = build_table_statement(
            {"source": _serialize_model(source), "options": _serialize_model(options)}
        )

    advanced_payload = _serialize_model(advanced) or {}

    config_lines = [f"EXTRACT {extractName}"]
    if trailName:
        config_lines.append(f"EXTTRAIL {trailName}")
    if domainName and connectionName:
        config_lines.append(f"USERIDALIAS {connectionName} DOMAIN {domainName}")
    config_lines.extend(build_advanced_extract_parameters(advanced_payload))
    if final_table_statement:
        config_lines.append(final_table_statement)

    payload: dict[str, Any] = {
        "config": config_lines,
        "managedProcessSettings": DEFAULT_MANAGED_PROCESS_SETTINGS,
    }
    ext_trail = advanced_payload.get("extTrail")
    if ext_trail and (not trailName or ext_trail.strip() != trailName.strip()):
        payload["targets"] = [{"name": ext_trail.strip()}]
        payload["begin"] = "now"
    elif trailName:
        payload["targets"] = [{"name": trailName}]
        payload["begin"] = "now"
    if domainName and connectionName:
        payload["credentials"] = {"domain": domainName, "alias": connectionName}
    return _ok(client.patch(api.update_extract(extractName), payload))


@_tool(
    annotations=WRITE_ANNOTATIONS,
    description=(
        "Creates a new Replicat in OCI GoldenGate deployment to replicate data into a target. Supports raw "
        "mapStatement or structured source/options. Requires checkpointTable for deployments that use database "
        "checkpoints; use list_checkpoint_tables to find a valid table. Creating an Initial Load Replicat does not "
        "authorize starting it: wait for its Initial Load Extract to finish, then use start_initial_load_replicat."
    )
)
def create_replicat(
    replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN),
    trailName: str = Field(..., description="Two-character trail name", min_length=2, max_length=2, pattern=TRAIL_NAME_PATTERN),
    domainName: str = Field(..., description="GoldenGate domain name"),
    connectionName: str = Field(..., description="GoldenGate connection (alias) name"),
    mapStatement: str | None = Field(None, description="Raw MAP statement(s) for Replicat"),
    source: CreateReplicatSource | None = Field(None, description="Structured source mapping used to build MAP statements"),
    options: CreateReplicatOptions | None = Field(None, description="Optional structured MAP statement options"),
    begin: str | CreateReplicatBegin | None = Field(
        None,
        description="Optional start position for Replicat. Defaults to 'now'. Accepts an ISO-8601 timestamp string or structured trail position like {sequence: 145, offset: 5}.",
    ),
    checkpointTable: str | None = Field(
        None,
        description='Checkpoint table name for ADD REPLICAT, for example SRCMIRROR_OCIGGLL.CHECKTABLE or "SRCMIRROR_OCIGGLL"."CHECKTABLE". Prefer this top-level field over options or advanced parameters.',
    ),
    advanced: ReplicatAdvancedParameters | None = Field(None, description="Advanced GoldenGate Replicat parameters"),
) -> str:
    """Creates a new Replicat in OCI GoldenGate deployment to replicate data into a target. Supports raw mapStatement or structured source/options. Requires checkpointTable for deployments that use database checkpoints; use list_checkpoint_tables to find a valid table."""
    mapStatement = _none_if_fieldinfo(mapStatement)
    source = _none_if_fieldinfo(source)
    options = _none_if_fieldinfo(options)
    begin = _none_if_fieldinfo(begin)
    checkpointTable = _none_if_fieldinfo(checkpointTable)
    advanced = _none_if_fieldinfo(advanced)

    if mapStatement and mapStatement.strip():
        final_map_statement = normalize_map_statement(mapStatement)
    else:
        if not source:
            raise ValueError("Either 'mapStatement' or 'source' (with targetTable) must be provided.")
        final_map_statement = build_map_statement(
            {"source": _serialize_model(source), "options": _serialize_model(options)}
        )

    advanced_payload = _serialize_model(advanced) or {}
    adv = build_advanced_replicat_parameters(advanced_payload)
    checkpoint = _resolve_replicat_checkpoint(checkpointTable, adv.get("checkpointTable"))
    config_lines = [f"REPLICAT {replicatName}"]
    if adv.get("credentialLines"):
        config_lines.extend(adv["credentialLines"])
    else:
        config_lines.append(f"USERIDALIAS {connectionName} DOMAIN {domainName}")

    lines = adv.get("lines") or []
    if checkpoint:
        lines = [ln for ln in lines if not ln.startswith("CHECKPOINTTABLE")]
    if not _has_parameter_line(lines, "REPORTCOUNT"):
        config_lines.append(DEFAULT_REPORTCOUNT_PARAMETER)
    config_lines.extend(lines)
    config_lines.append(final_map_statement)

    payload: dict[str, Any] = {
        "config": config_lines,
        "managedProcessSettings": DEFAULT_MANAGED_PROCESS_SETTINGS,
        "mode": adv.get("mode") or {"type": "nonintegrated", "parallel": True},
        "registration": "none",
        "status": "stopped",
        "begin": _resolve_begin_value(begin),
    }
    if not adv.get("credentialLines"):
        payload["credentials"] = {"domain": domainName, "alias": connectionName}
    mode_type = (payload["mode"] or {}).get("type", "nonintegrated")
    if mode_type != "parallel":
        payload["source"] = {"name": trailName}
    if checkpoint:
        payload["checkpoint"] = {"table": checkpoint}
    return _ok(client.post(api.create_replicat(replicatName), payload))


@_tool(annotations=WRITE_ANNOTATIONS, description="Updates an existing Replicat in OCI GoldenGate deployment. Accepts the same structured payload as create_replicat but performs a PATCH instead.")
def update_replicat(
    replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN),
    trailName: str | None = Field(None, description="Two-character trail name", min_length=2, max_length=2, pattern=TRAIL_NAME_PATTERN),
    domainName: str | None = Field(None, description="GoldenGate domain name"),
    connectionName: str | None = Field(None, description="GoldenGate connection (alias) name"),
    mapStatement: str | None = Field(None, description="Raw MAP statement(s) for Replicat"),
    source: CreateReplicatSource | None = Field(None, description="Structured source mapping used to build MAP statements"),
    options: CreateReplicatOptions | None = Field(None, description="Optional structured MAP statement options"),
    checkpointTable: str | None = Field(
        None,
        description='Checkpoint table name for the Replicat checkpoint payload, for example SRCMIRROR_OCIGGLL.CHECKTABLE or "SRCMIRROR_OCIGGLL"."CHECKTABLE".',
    ),
    advanced: ReplicatAdvancedParameters | None = Field(None, description="Advanced GoldenGate Replicat parameters"),
) -> str:
    """Updates an existing Replicat in OCI GoldenGate deployment. Accepts the same structured payload as create_replicat but performs a PATCH instead."""
    trailName = _none_if_fieldinfo(trailName)
    domainName = _none_if_fieldinfo(domainName)
    connectionName = _none_if_fieldinfo(connectionName)
    mapStatement = _none_if_fieldinfo(mapStatement)
    source = _none_if_fieldinfo(source)
    options = _none_if_fieldinfo(options)
    checkpointTable = _none_if_fieldinfo(checkpointTable)
    advanced = _none_if_fieldinfo(advanced)

    if mapStatement and mapStatement.strip():
        final_map_statement = normalize_map_statement(mapStatement)
    elif source:
        source_payload = _serialize_model(source) or {}
        if not source_payload.get("targetTable"):
            raise ValueError("'source.targetTable' must be provided when using structured source.")
        final_map_statement = build_map_statement(
            {"source": source_payload, "options": _serialize_model(options)}
        )
    else:
        raise ValueError("Either 'mapStatement' or 'source' must be provided (with 'targetTable').")

    advanced_payload = _serialize_model(advanced) or {}
    adv = build_advanced_replicat_parameters(advanced_payload)
    checkpoint = _resolve_replicat_checkpoint(checkpointTable, adv.get("checkpointTable"))
    config_lines = [f"REPLICAT {replicatName}"]
    if adv.get("credentialLines"):
        config_lines.extend(adv["credentialLines"])
    elif domainName and connectionName:
        config_lines.append(f"USERIDALIAS {connectionName} DOMAIN {domainName}")
    lines = adv.get("lines") or []
    if checkpoint:
        lines = [ln for ln in lines if not ln.startswith("CHECKPOINTTABLE")]
    config_lines.extend(lines)
    config_lines.append(final_map_statement)

    payload: dict[str, Any] = {
        "config": config_lines,
        "managedProcessSettings": DEFAULT_MANAGED_PROCESS_SETTINGS,
    }
    resolved_mode = adv.get("mode") or (
        {
            "type": advanced_payload.get("modeType"),
            **(
                {"parallel": advanced_payload.get("modeParallel")}
                if advanced_payload and advanced_payload.get("modeParallel") is not None
                else {}
            ),
        }
        if advanced_payload.get("modeType")
        else {"type": "nonintegrated", "parallel": True}
    )
    payload["mode"] = resolved_mode
    if resolved_mode.get("type") != "parallel" and trailName:
        payload["source"] = {"name": trailName}
    if checkpoint:
        payload["checkpoint"] = {"table": checkpoint}
    if not adv.get("credentialLines") and domainName and connectionName:
        payload["credentials"] = {"domain": domainName, "alias": connectionName}
    return _ok(client.patch(api.update_replicat(replicatName), payload))


@_tool(annotations=WRITE_ANNOTATIONS, description="Creates a new GoldenGate Distribution Path to distribute or send data from one GoldenGate deployment to another. The sourceURI and targetURI parameters must only contain the source and target deployment hostnames without any protocol, service, or trail name. The support target authentication methods are OAuth and Alias.")
def create_distribution_path(
    distributionPathName: str = Field(..., description="Distribution path name"),
    sourceURI: str = Field(..., description="Source deployment hostname (no protocol)"),
    sourceTrailName: str = Field(..., description="Source two-character trail name", min_length=2, max_length=2, pattern=TRAIL_NAME_PATTERN),
    targetURI: str = Field(..., description="Target deployment hostname (no protocol)"),
    targetPort: int | None = Field(None, description="Target port for distribution path", ge=1, le=65535),
    targetAuthenticationMethod: str | None = Field(
        None,
        description="Authentication method for target deployment",
        pattern="^(OAuth|Alias)$",
    ),
    targetDomain: str | None = Field(None, description="Target credential domain when authentication method is Alias"),
    targetAlias: str | None = Field(None, description="Target credential alias when authentication method is Alias"),
) -> str:
    """Creates a new GoldenGate Distribution Path to distribute or send data from one GoldenGate deployment to another. The sourceURI and targetURI parameters must only contain the source and target deployment hostnames without any protocol, service, or trail name. The support target authentication methods are OAuth and Alias."""
    targetPort = _none_if_fieldinfo(targetPort)
    targetAuthenticationMethod = _none_if_fieldinfo(targetAuthenticationMethod)
    targetDomain = _none_if_fieldinfo(targetDomain)
    targetAlias = _none_if_fieldinfo(targetAlias)
    sourceURI = _normalize_distribution_host(sourceURI, "sourceURI")
    targetURI = _normalize_distribution_host(targetURI, "targetURI")

    auth = targetAuthenticationMethod or "OAuth"
    port = targetPort or 443
    target_auth: Any
    if auth.upper() == "ALIAS":
        if not targetDomain or not targetAlias:
            raise ValueError("targetDomain and targetAlias are required when targetAuthenticationMethod is 'Alias'.")
        target_auth = {"domain": targetDomain, "alias": targetAlias}
    else:
        target_auth = "oauth2ClientCredentials"

    payload = {
        "name": distributionPathName,
        "status": "stopped",
        "source": {"uri": f"trail://{sourceURI}/services/distsrvr/v2/sources?trail={sourceTrailName}"},
        "target": {
            "uri": f"wss://{targetURI}:{port}/services/v2/targets?trail={sourceTrailName}",
            "authenticationMethod": target_auth,
        },
        "begin": {"sequence": 0, "offset": 0},
    }
    return _ok(client.post(api.create_distribution_path(distributionPathName, sourceURI, sourceTrailName, targetURI, port, auth, targetDomain, targetAlias), payload))


@_tool(
    annotations=WRITE_ANNOTATIONS,
    description=(
        "Creates a new Data Stream using a trail in OCI GoldenGate to expose data as AsyncAPI channels. "
        "Optionally set includeTables and excludeTables to emit ordered object-name filter rules."
    )
)
def create_data_stream(
    dataStreamName: str = Field(..., description="Data stream name"),
    trailName: str = Field(..., description="Two-character trail name", min_length=2, max_length=2, pattern=TRAIL_NAME_PATTERN),
    qualityOfService: str | None = Field(
        None,
        description="Delivery quality of service for the data stream",
        pattern="^(exactlyOnce|atLeastOnce|atMostOnce)$",
    ),
    cloudEventsFormat: bool | None = Field(None, description="Whether to emit records in CloudEvents format"),
    bufferSize: int | None = Field(None, description="Data stream buffer size in bytes", ge=1024),
    includeTables: list[str] | None = Field(
        None,
        description=(
            "Source object names to include in the Data Stream, such as ['YAN_POS.CUSTOMER']. "
            "Emits a rules entry with action 'include' and filter.objectNames."
        ),
        min_length=1,
    ),
    excludeTables: list[str] | None = Field(
        None,
        description=(
            "Source object names to exclude from the Data Stream, such as ['YAN_POS.REGIONS']. "
            "Emits a rules entry with action 'exclude' and filter.objectNames."
        ),
        min_length=1,
    ),
) -> str:
    """Create a Data Stream, optionally limited to selected source tables."""
    qualityOfService = _none_if_fieldinfo(qualityOfService)
    cloudEventsFormat = _none_if_fieldinfo(cloudEventsFormat)
    bufferSize = _none_if_fieldinfo(bufferSize)
    includeTables = _none_if_fieldinfo(includeTables)
    excludeTables = _none_if_fieldinfo(excludeTables)

    normalized_tables: list[str] | None = None
    if includeTables is not None:
        normalized_tables = [str(table).strip() for table in includeTables]
        if not normalized_tables or any(not table for table in normalized_tables):
            raise ValueError("'includeTables' must contain at least one non-empty source object name.")
    normalized_excluded_tables: list[str] | None = None
    if excludeTables is not None:
        normalized_excluded_tables = [str(table).strip() for table in excludeTables]
        if not normalized_excluded_tables or any(not table for table in normalized_excluded_tables):
            raise ValueError("'excludeTables' must contain at least one non-empty source object name.")

    payload: dict[str, Any] = {
        "source": {"trail": trailName},
        "cloudEventsFormat": cloudEventsFormat if cloudEventsFormat is not None else False,
        "encoding": "json",
        "bufferSize": bufferSize if bufferSize is not None else 1048576,
        "qualityOfService": qualityOfService or "exactlyOnce",
    }
    rules: list[dict[str, Any]] = []
    if normalized_tables is not None:
        rules.append({"action": "include", "filter": {"objectNames": normalized_tables}})
    if normalized_excluded_tables is not None:
        rules.append({"action": "exclude", "filter": {"objectNames": normalized_excluded_tables}})
    if rules:
        payload["rules"] = rules
    return _ok(
        client.post(
            api.create_data_stream(
                dataStreamName,
                trailName,
                qualityOfService,
                cloudEventsFormat,
                bufferSize,
                includeTables,
                excludeTables,
            ),
            payload,
        )
    )


@_tool(
    annotations=WRITE_ANNOTATIONS,
    description=(
        "Start a GoldenGate Extract or a Replicat with a verified local CDC Extract producer, optionally at or after "
        "a CSN. Refuses Initial Load and ambiguous or remote-only Replicat sources. Use start_initial_load_replicat "
        "for an Initial Load Replicat."
    )
)
def start(
    processName: str = Field(..., description="GoldenGate process name", pattern=PROCESS_NAME_PATTERN),
    at: int | None = Field(None, description="Start at this commit sequence number (CSN)", ge=0),
    after: int | None = Field(None, description="Start after this commit sequence number (CSN)", ge=0),
) -> str:
    """Start a process in GoldenGate, optionally at or after a CSN."""
    at = _none_if_fieldinfo(at)
    after = _none_if_fieldinfo(after)
    if at is not None and after is not None:
        raise ValueError("'at' and 'after' are mutually exclusive.")

    ensure_generic_start_allowed(client, processName)

    payload: dict[str, Any] = {"name": "start", "processName": processName}
    if at is not None:
        payload["at"] = at
    if after is not None:
        payload["after"] = after
    return _ok(client.post(api.start(processName), payload))


@_tool(
    annotations=LOCAL_ANNOTATIONS,
    description=(
        "Return the ordered Oracle Initial Load-to-CDC workflow, including required wait points, status/report checks, "
        "and instantiation SCN reuse. Call this before creating or starting Initial Load and CDC processes."
    )
)
def get_initial_load_cdc_workflow() -> str:
    """Return the safe, ordered Oracle Initial Load-to-CDC workflow."""
    return _ok(
        {
            "workflow": "Oracle Initial Load followed by ongoing CDC",
            "steps": [
                {
                    "order": 1,
                    "action": "Create, register, and start the primary CDC Extract",
                    "reason": "Capture source changes while the initial load is running.",
                },
                {
                    "order": 2,
                    "action": "Determine the instantiation SCN after CDC Extract registration",
                    "reason": "Use a consistent point that is later than the registration SCN.",
                },
                {
                    "order": 3,
                    "action": "Create the Initial Load Extract with asOfScn set to the instantiation SCN",
                    "reason": "Emit SQLPREDICATE 'AS OF SCN <scn>' for the Oracle flashback snapshot.",
                },
                {
                    "order": 4,
                    "action": "Start the Initial Load Extract and wait for it to stop",
                    "requiredChecks": ["get_extract_status returns STOPPED", "get_extract_report shows no failure"],
                },
                {
                    "order": 5,
                    "action": "Start the Initial Load Replicat with start_initial_load_replicat",
                    "precondition": "The Initial Load Extract has completed and its EXTFILE is available.",
                },
                {
                    "order": 6,
                    "action": "Wait for the Initial Load Replicat to finish processing the initial-load data",
                    "requiredChecks": ["Check Replicat status, report, statistics, and lag as applicable"],
                },
                {
                    "order": 7,
                    "action": "Start the CDC Replicat at the matching instantiation SCN",
                    "reason": "Use the selected AT CSN or AFTER CSN semantics consistently with the load design.",
                },
            ],
            "safetyRules": [
                "Never start an Initial Load Replicat while its Initial Load Extract is RUNNING.",
                "Do not proceed when Extract status is ambiguous or its report contains an abend or fatal failure.",
                "asOfScn is a flashback-query snapshot and not an Extract process start position.",
                "Use the generic start tool only for processes whose workflow prerequisites have already been met.",
            ],
        }
    )


@_tool(
    annotations=WRITE_ANNOTATIONS,
    description=(
        "Start an Initial Load Replicat only after backend checks confirm matching EXTFILE/source paths, STOPPED "
        "Extract status, successful execution history, and a report identifying that execution. Refuses missing, "
        "stale, failed, manually stopped, or ambiguous evidence."
    )
)
def start_initial_load_replicat(
    replicatName: str = Field(..., description="Initial Load Replicat process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN),
    initialLoadExtractName: str = Field(
        ...,
        description="Completed Initial Load Extract that produced the EXTFILE consumed by this Replicat",
        min_length=1,
        max_length=8,
        pattern=PROCESS_NAME_PATTERN,
    ),
) -> str:
    """Start an Initial Load Replicat after backend-derived prerequisite checks."""
    prerequisites = validate_initial_load_start(client, replicatName, initialLoadExtractName)

    start_response = client.post(
        api.start(replicatName),
        {"name": "start", "processName": replicatName},
    )
    return _ok(
        {
            "prerequisites": prerequisites,
            "startResult": start_response,
        }
    )


@_tool(annotations=WRITE_ANNOTATIONS, description="Stop a process in GoldenGate")
def stop(processName: str = Field(..., description="GoldenGate process name", pattern=PROCESS_NAME_PATTERN)) -> str:
    """Stop a process in GoldenGate."""
    return _ok(client.post(api.stop(processName), {"name": "stop", "processName": processName, "force": False}))


@_tool(annotations=WRITE_ANNOTATIONS, description="Start a distribution path")
def start_distribution_path(processName: str = Field(..., description="Distribution path name")) -> str:
    """Start a distribution path."""
    return _ok(client.patch(api.start_distribution_path(processName), {"status": "running"}))


@_tool(annotations=WRITE_ANNOTATIONS, description="Stop a distribution path")
def stop_distribution_path(processName: str = Field(..., description="Distribution path name")) -> str:
    """Stop a distribution path."""
    return _ok(client.patch(api.stop_distribution_path(processName), {"status": "stopped"}))


@_tool(annotations=READ_ANNOTATIONS, description="Get lag metrics for an Extract")
def get_extract_lag(extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN)) -> str:
    """Get lag metrics for an Extract."""
    return _ok(client.post(api.get_extract_lag(extractName), {"command": "GETLAG", "isReported": True}))


@_tool(annotations=READ_ANNOTATIONS, description="Get lag metrics for a Replicat")
def get_replicat_lag(replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN)) -> str:
    """Get lag metrics for a Replicat."""
    return _ok(client.post(api.get_replicat_lag(replicatName), {"command": "GETLAG", "isReported": True}))


@_tool(
    annotations=READ_ANNOTATIONS,
    description=(
        "Retrieve an Extract report. For an Initial Load Extract, review this after status becomes STOPPED and before "
        "starting the Initial Load Replicat; resolve any abend, fatal, or failed operation first."
    )
)
def get_extract_report(extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN)) -> str:
    """Retrieve a report from the Extract process to monitor or troubleshoot it. A report contains all the information about a GoldenGate process."""
    return _ok(client.get(api.get_extract_report(extractName)))


@_tool(annotations=READ_ANNOTATIONS, description="Retrieve a report from the Replicat process to monitor or troubleshoot it. A report contains all the information about a GoldenGate process")
def get_replicat_report(replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN)) -> str:
    """Retrieve a report from the Replicat process to monitor or troubleshoot it. A report contains all the information about a GoldenGate process."""
    return _ok(client.get(api.get_replicat_report(replicatName)))


@_tool(annotations=READ_ANNOTATIONS, description="Retrieve information about an existing GoldenGate Data Stream")
def get_data_stream_info(dataStreamName: str = Field(..., description="Data stream name")) -> str:
    """Retrieve information about an existing GoldenGate Data Stream."""
    return _ok(client.get(api.get_data_stream_info(dataStreamName)))


@_tool(annotations=READ_ANNOTATIONS, description="Retrieve the AsyncAPI yaml specification / definition of an existing GoldenGate Data Stream")
def get_data_stream_yaml(dataStreamName: str = Field(..., description="Data stream name")) -> str:
    """Retrieve the AsyncAPI yaml specification / definition of an existing GoldenGate Data Stream."""
    return _ok(client.get(api.get_data_stream_yaml(dataStreamName), headers={"Content-Type": "application/json", "Accept": "application/yaml"}, response_text=True))


@_tool(annotations=READ_ANNOTATIONS, description="Retrieve statistics for an existing GoldenGate Data Stream")
def get_data_stream_stats(dataStreamName: str = Field(..., description="Data stream name")) -> str:
    """Retrieve overall, network, and table statistics for an existing GoldenGate Data Stream."""
    return _ok(
        {
            "overall": client.get(api.get_data_stream_overall_stats(dataStreamName)),
            "network": client.get(api.get_data_stream_network_stats(dataStreamName)),
            "tables": client.get(api.get_data_stream_table_stats(dataStreamName)),
        }
    )


@_tool(annotations=READ_ANNOTATIONS, description="Retrieve an Extract statistics: number of inserts, updates, deletes, etc. that were captured by the process")
def get_extract_stats(extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN)) -> str:
    """Retrieve an Extract statistics: number of inserts, updates, deletes, etc. that were captured by the process."""
    return _ok(client.post(api.get_extract_stats(extractName), {"command": "STATS", "isReported": True}))


@_tool(annotations=READ_ANNOTATIONS, description="Retrieve a Replicat statistics: number of inserts, updates, deletes, etc. that were replicated by the process")
def get_replicat_stats(replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN)) -> str:
    """Retrieve a Replicat statistics: number of inserts, updates, deletes, etc. that were replicated by the process."""
    return _ok(client.post(api.get_replicat_stats(replicatName), {"command": "STATS", "isReported": True}))


@_tool(annotations=READ_ANNOTATIONS, description="Retrieve the details of an extract process: parameters, configuration, targets, type, etc.")
def get_extract_details(extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN)) -> str:
    """Retrieve the details of an extract process: parameters, configuration, targets, type, etc."""
    return _ok(client.get(api.get_extract_details(extractName)))


@_tool(annotations=READ_ANNOTATIONS, description="Retrieve the details of a replicat process: parameters, configuration, targets, type, etc.")
def get_replicat_details(replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8, pattern=PROCESS_NAME_PATTERN)) -> str:
    """Retrieve the details of a replicat process: parameters, configuration, targets, type, etc."""
    return _ok(client.get(api.get_replicat_details(replicatName)))


def main() -> None:
    """Start the FastMCP server using stdio transport."""
    try:
        try:
            _verify_deployment_connectivity()
        except Exception:
            _log_startup(
                "ERROR",
                "Startup aborted. Verify the deployment is started, the configured baseUrl is reachable, and if you received HTTP 401, check OGG_USERNAME and the password or OGG_PASSWORD_SECRET_OCID secret value.",
            )
            if os.getenv("OGG_MCP_DEBUG", "false").strip().lower() == "true":
                traceback.print_exc(file=sys.stderr)
            raise SystemExit(1) from None
        mcp.run(transport="stdio")
    finally:
        client.close()


if __name__ == "__main__":
    main()
