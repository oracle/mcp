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
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field
from pydantic.fields import FieldInfo

from . import api
from .config import read_config
from .consts import DEFAULT_DOMAIN, SERVER_NAME
from .extract_config import build_advanced_extract_parameters
from .http_client import HttpClient
from .map_statement import build_map_statement, normalize_map_statement
from .models import (
    CreateExtractOptions,
    CreateExtractSource,
    CreateReplicatOptions,
    CreateReplicatSource,
    ExtractAdvancedParameters,
    ReplicatAdvancedParameters,
)
from .replicat_config import build_advanced_replicat_parameters
from .table_statement import build_table_statement, normalize_table_statement

cfg = read_config()
client = HttpClient(cfg)
mcp = FastMCP(SERVER_NAME)

DEFAULT_MANAGED_PROCESS_SETTINGS = "ogg:managedProcessSettings:Default"


def _ok(data: Any) -> str:
    """Normalize tool output to string (JSON-encoded for dict/list payloads)."""
    return data if isinstance(data, str) else json.dumps(data)


def _log_startup(level: str, message: str) -> None:
    """Emit startup logs to stderr and optionally append to launcher log file."""
    stderr_line = f"[{level}] {message}"
    print(stderr_line, file=sys.stderr, flush=True)
    log_file = os.getenv("GG_MCP_LOG_FILE")
    if log_file:
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] [{level}] {message}\n")
        except OSError:
            # Avoid breaking MCP startup if file logging fails.
            pass


def _verify_deployment_connectivity() -> None:
    """Validate GoldenGate deployment connectivity before serving MCP tools."""
    deployment_url = cfg.get("baseUrl", "<unknown>")
    _log_startup("INFO", f"Verifying connectivity to GoldenGate deployment: {deployment_url}")
    try:
        client.get(api.list_domains())
    except Exception as exc:
        _log_startup("ERROR", f"Failed to connect to GoldenGate deployment: {deployment_url} ({exc})")
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


@mcp.tool(description="Return the list of GoldenGate domains available in OCI GoldenGate deployment. Domains group connections in GoldenGate.")
def list_domains() -> str:
    """Return the list of GoldenGate domains available in OCI GoldenGate deployment. Domains group connections in GoldenGate."""
    return _ok(client.get(api.list_domains()))


@mcp.tool(description="Return the list of Connections available in specific GoldenGate domains in OCI GoldenGate deployment. A connection stores the metadata defining connectivity to a source or target.")
def list_connections(domain: str = Field(..., description="GoldenGate domain name")) -> str:
    """Return the list of Connections available in specific GoldenGate domains in OCI GoldenGate deployment. A connection stores the metadata defining connectivity to a source or target."""
    return _ok(client.get(api.list_connections(domain)))


@mcp.tool(description="Returns the list of checkpoint tables for a given connection or domains/alias pair. Checkpoints are required when creating Replicat processes.")
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


@mcp.tool(description="Return the list of Extracts (processes that capture data from a source) available in OCI GoldenGate deployment")
def list_extracts() -> str:
    """Return the list of Extracts (processes that capture data from a source) available in OCI GoldenGate deployment."""
    return _ok(client.get(api.list_extracts()))


@mcp.tool(description="Return the list of Replicats (processes that replicate data into a target) available in OCI GoldenGate deployment")
def list_replicats() -> str:
    """Return the list of Replicats (processes that replicate data into a target) available in OCI GoldenGate deployment."""
    return _ok(client.get(api.list_replicats()))


@mcp.tool(description="Return the list of Distribution Paths available in OCI GoldenGate deployment. A Distribution Path is used to send data to another GoldenGate deployment.")
def list_distribution_paths() -> str:
    """Return the list of Distribution Paths available in OCI GoldenGate deployment. A Distribution Path is used to send data to another GoldenGate deployment."""
    return _ok(client.get(api.list_distribution_paths()))


@mcp.tool(description="Retrieve a collection of all known trails available in OCI GoldenGate deployment. A trail is a file that stores the captured data. A trail can only have two alphanumeric characters.")
def list_trails() -> str:
    """Retrieve a collection of all known trails available in OCI GoldenGate deployment. A trail is a file that stores the captured data. A trail can only have two alphanumeric characters."""
    return _ok(client.get(api.list_trails()))


@mcp.tool(description="Return the status of a given Extract in OCI GoldenGate deployment")
def get_extract_status(
    extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8)
) -> str:
    """Return the status of a given Extract in OCI GoldenGate deployment."""
    return _ok(client.post(api.get_extract_status(extractName), {"command": "STATUS"}))


@mcp.tool(description="Return the status of a given Replicat in OCI GoldenGate deployment")
def get_replicat_status(
    replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8)
) -> str:
    """Return the status of a given Replicat in OCI GoldenGate deployment."""
    return _ok(client.post(api.get_replicat_status(replicatName), {"command": "STATUS"}))


@mcp.tool(description="Create a new alias or connection in the GoldenGate credential store. If no domain is provided, defaults to OracleGoldenGate.")
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


@mcp.tool(description="Add TRANDATA at schema level for a given connection. Manage Supplemental Logging for Database Schemas.")
def add_trandata_schema(
    domain: str = Field(..., description="GoldenGate domain name"),
    connection: str = Field(..., description="GoldenGate connection (alias) name"),
    schemaName: str = Field(..., description="Database schema name"),
) -> str:
    """Add TRANDATA at schema level for a given connection. Manage Supplemental Logging for Database Schemas."""
    payload = {
        "schemaName": schemaName,
        "nonvalidatedKeysAllowed": False,
        "schedulingColumns": True,
        "allColumns": False,
        "prepareCsnMode": "nowait",
        "operation": "add",
    }
    return _ok(client.post(api.add_trandata_schema(domain, connection), payload))


@mcp.tool(description="Add TRANDATA at table level for a given connection. Manage Supplemental Logging for Database tables.")
def add_trandata_table(
    domain: str = Field(..., description="GoldenGate domain name"),
    connection: str = Field(..., description="GoldenGate connection (alias) name"),
    schemaName: str = Field(..., description="Database schema name"),
    tableName: str = Field(..., description="Database table name"),
) -> str:
    """Add TRANDATA at table level for a given connection. Manage Supplemental Logging for Database tables."""
    payload = {
        "tableName": f"{schemaName}.{tableName}",
        "primaryKey": True,
        "schedulingColumns": True,
        "allColumns": False,
        "prepareCsnMode": "nowait",
        "operation": "add",
    }
    return _ok(client.post(api.add_trandata_table(domain, connection), payload))


@mcp.tool(description="Creates a new Extract in OCI GoldenGate deployment to capture data from schemas and tables. The Extract name can have, at most, 8 alphanumeric characters.")
def create_extract(
    extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8),
    trailName: str = Field(..., description="Two-character trail name", min_length=2, max_length=2),
    domainName: str = Field(..., description="GoldenGate domain name"),
    connectionName: str = Field(..., description="GoldenGate connection (alias) name"),
    tableStatement: str | None = Field(None, description="Raw TABLE statement(s) for Extract"),
    source: CreateExtractSource | None = Field(None, description="Structured source mapping used to build TABLE statements"),
    options: CreateExtractOptions | None = Field(None, description="Optional structured TABLE statement options"),
    advanced: ExtractAdvancedParameters | None = Field(None, description="Advanced GoldenGate Extract parameters"),
) -> str:
    """Creates a new Extract in OCI GoldenGate deployment to capture data from schemas and tables. The Extract name can have, at most, 8 alphanumeric characters."""
    tableStatement = _none_if_fieldinfo(tableStatement)
    source = _none_if_fieldinfo(source)
    options = _none_if_fieldinfo(options)
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
    config_lines.extend(advanced_params)
    config_lines.append(final_table_statement)

    payload = {
        "config": config_lines,
        "source": {"tranlogs": "integrated"},
        "credentials": {"domain": domainName, "alias": connectionName},
        "managedProcessSettings": DEFAULT_MANAGED_PROCESS_SETTINGS,
        "registration": {"optimized": False},
        "begin": "now",
        "targets": [{"name": trailName}],
    }
    return _ok(client.post(api.create_extract(extractName), payload))


@mcp.tool(description="Updates an existing Extract in OCI GoldenGate deployment. Accepts the same structured payload as create_extract but performs a PATCH instead.")
def update_extract(
    extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8),
    trailName: str | None = Field(None, description="Two-character trail name", min_length=2, max_length=2),
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


@mcp.tool(description="Creates a new Replicat in OCI GoldenGate deployment to replicate data into a target. Supports raw mapStatement or structured source/options. Optionally accepts a checkpointTable, otherwise use list_checkpoint_tables to find a checkpoint table.")
def create_replicat(
    replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8),
    trailName: str = Field(..., description="Two-character trail name", min_length=2, max_length=2),
    domainName: str = Field(..., description="GoldenGate domain name"),
    connectionName: str = Field(..., description="GoldenGate connection (alias) name"),
    mapStatement: str | None = Field(None, description="Raw MAP statement(s) for Replicat"),
    source: CreateReplicatSource | None = Field(None, description="Structured source mapping used to build MAP statements"),
    options: CreateReplicatOptions | None = Field(None, description="Optional structured MAP statement options"),
    advanced: ReplicatAdvancedParameters | None = Field(None, description="Advanced GoldenGate Replicat parameters"),
) -> str:
    """Creates a new Replicat in OCI GoldenGate deployment to replicate data into a target. Supports raw mapStatement or structured source/options. Optionally accepts a checkpointTable, otherwise use list_checkpoint_tables to find a checkpoint table."""
    mapStatement = _none_if_fieldinfo(mapStatement)
    source = _none_if_fieldinfo(source)
    options = _none_if_fieldinfo(options)
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
    config_lines = [f"REPLICAT {replicatName}"]
    if adv.get("credentialLines"):
        config_lines.extend(adv["credentialLines"])
    else:
        config_lines.append(f"USERIDALIAS {connectionName} DOMAIN {domainName}")

    lines = adv.get("lines") or []
    checkpoint = adv.get("checkpointTable")
    if checkpoint:
        lines = [ln for ln in lines if not ln.startswith("CHECKPOINTTABLE")]
    config_lines.extend(lines)
    config_lines.append(final_map_statement)

    payload: dict[str, Any] = {
        "config": config_lines,
        "credentials": {"domain": domainName, "alias": connectionName},
        "managedProcessSettings": DEFAULT_MANAGED_PROCESS_SETTINGS,
        "mode": adv.get("mode") or {"type": "nonintegrated", "parallel": True},
        "registration": "none",
        "status": "stopped",
    }
    mode_type = (payload["mode"] or {}).get("type", "nonintegrated")
    if mode_type != "parallel":
        payload["source"] = {"name": trailName}
    if checkpoint:
        payload["checkpoint"] = {"table": checkpoint}
    return _ok(client.post(api.create_replicat(replicatName), payload))


@mcp.tool(description="Updates an existing Replicat in OCI GoldenGate deployment. Accepts the same structured payload as create_replicat but performs a PATCH instead.")
def update_replicat(
    replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8),
    trailName: str | None = Field(None, description="Two-character trail name", min_length=2, max_length=2),
    domainName: str | None = Field(None, description="GoldenGate domain name"),
    connectionName: str | None = Field(None, description="GoldenGate connection (alias) name"),
    mapStatement: str | None = Field(None, description="Raw MAP statement(s) for Replicat"),
    source: CreateReplicatSource | None = Field(None, description="Structured source mapping used to build MAP statements"),
    options: CreateReplicatOptions | None = Field(None, description="Optional structured MAP statement options"),
    advanced: ReplicatAdvancedParameters | None = Field(None, description="Advanced GoldenGate Replicat parameters"),
) -> str:
    """Updates an existing Replicat in OCI GoldenGate deployment. Accepts the same structured payload as create_replicat but performs a PATCH instead."""
    trailName = _none_if_fieldinfo(trailName)
    domainName = _none_if_fieldinfo(domainName)
    connectionName = _none_if_fieldinfo(connectionName)
    mapStatement = _none_if_fieldinfo(mapStatement)
    source = _none_if_fieldinfo(source)
    options = _none_if_fieldinfo(options)
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
    config_lines = [f"REPLICAT {replicatName}"]
    if adv.get("credentialLines"):
        config_lines.extend(adv["credentialLines"])
    elif domainName and connectionName:
        config_lines.append(f"USERIDALIAS {connectionName} DOMAIN {domainName}")
    config_lines.extend(adv.get("lines") or [])
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
    if not adv.get("credentialLines") and domainName and connectionName:
        payload["credentials"] = {"domain": domainName, "alias": connectionName}
    return _ok(client.patch(api.update_replicat(replicatName), payload))


@mcp.tool(description="Creates a new GoldenGate Distribution Path to distribute or send data from one GoldenGate deployment to another. The sourceURI and targetURI parameters must only contain the source and target deployment hostnames without any protocol, service, or trail name. The support target authentication methods are OAuth and Alias.")
def create_distribution_path(
    distributionPathName: str = Field(..., description="Distribution path name"),
    sourceURI: str = Field(..., description="Source deployment hostname (no protocol)"),
    sourceTrailName: str = Field(..., description="Source two-character trail name", min_length=2, max_length=2),
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


@mcp.tool(description="Creates a new Data Stream using the trail provided in OCI GoldenGate deployment to distribute or expose data as AsyncAPI channels")
def create_data_stream(
    dataStreamName: str = Field(..., description="Data stream name"),
    trailName: str = Field(..., description="Two-character trail name", min_length=2, max_length=2),
    qualityOfService: str | None = Field(
        None,
        description="Delivery quality of service for the data stream",
        pattern="^(exactlyOnce|atLeastOnce|atMostOnce)$",
    ),
    cloudEventsFormat: bool | None = Field(None, description="Whether to emit records in CloudEvents format"),
    bufferSize: int | None = Field(None, description="Data stream buffer size in bytes", ge=1024),
) -> str:
    """Creates a new Data Stream using the trail provided in OCI GoldenGate deployment to distribute or expose data as AsyncAPI channels."""
    payload = {
        "source": {"trail": trailName},
        "cloudEventsFormat": cloudEventsFormat if cloudEventsFormat is not None else False,
        "encoding": "json",
        "bufferSize": bufferSize if bufferSize is not None else 1048576,
        "qualityOfService": qualityOfService or "exactlyOnce",
    }
    return _ok(client.post(api.create_data_stream(dataStreamName, trailName, qualityOfService, cloudEventsFormat, bufferSize), payload))


@mcp.tool(description="Start a process in GoldenGate")
def start(processName: str = Field(..., description="GoldenGate process name")) -> str:
    """Start a process in GoldenGate."""
    return _ok(client.post(api.start(processName), {"name": "start", "processName": processName}))


@mcp.tool(description="Stop a process in GoldenGate")
def stop(processName: str = Field(..., description="GoldenGate process name")) -> str:
    """Stop a process in GoldenGate."""
    return _ok(client.post(api.stop(processName), {"name": "stop", "processName": processName, "force": False}))


@mcp.tool(description="Start a distribution path")
def start_distribution_path(processName: str = Field(..., description="Distribution path name")) -> str:
    """Start a distribution path."""
    return _ok(client.patch(api.start_distribution_path(processName), {"status": "running"}))


@mcp.tool(description="Stop a distribution path")
def stop_distribution_path(processName: str = Field(..., description="Distribution path name")) -> str:
    """Stop a distribution path."""
    return _ok(client.patch(api.stop_distribution_path(processName), {"status": "stopped"}))


@mcp.tool(description="Get lag metrics for an Extract")
def get_extract_lag(extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8)) -> str:
    """Get lag metrics for an Extract."""
    return _ok(client.post(api.get_extract_lag(extractName), {"command": "GETLAG", "isReported": True}))


@mcp.tool(description="Get lag metrics for a Replicat")
def get_replicat_lag(replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8)) -> str:
    """Get lag metrics for a Replicat."""
    return _ok(client.post(api.get_replicat_lag(replicatName), {"command": "GETLAG", "isReported": True}))


@mcp.tool(description="Retrieve a report from the Extract process to monitor or troubleshoot it. A report contains all the information about a GoldenGate process")
def get_extract_report(extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8)) -> str:
    """Retrieve a report from the Extract process to monitor or troubleshoot it. A report contains all the information about a GoldenGate process."""
    return _ok(client.get(api.get_extract_report(extractName)))


@mcp.tool(description="Retrieve a report from the Replicat process to monitor or troubleshoot it. A report contains all the information about a GoldenGate process")
def get_replicat_report(replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8)) -> str:
    """Retrieve a report from the Replicat process to monitor or troubleshoot it. A report contains all the information about a GoldenGate process."""
    return _ok(client.get(api.get_replicat_report(replicatName)))


@mcp.tool(description="Retrieve information about an existing GoldenGate Data Stream")
def get_data_stream_info(dataStreamName: str = Field(..., description="Data stream name")) -> str:
    """Retrieve information about an existing GoldenGate Data Stream."""
    return _ok(client.get(api.get_data_stream_info(dataStreamName)))


@mcp.tool(description="Retrieve the AsyncAPI yaml specification / definition of an existing GoldenGate Data Stream")
def get_data_stream_yaml(dataStreamName: str = Field(..., description="Data stream name")) -> str:
    """Retrieve the AsyncAPI yaml specification / definition of an existing GoldenGate Data Stream."""
    return _ok(client.get(api.get_data_stream_yaml(dataStreamName), headers={"Content-Type": "application/json", "Accept": "application/yaml"}, response_text=True))


@mcp.tool(description="Retrieve an Extract statistics: number of inserts, updates, deletes, etc. that were captured by the process")
def get_extract_stats(extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8)) -> str:
    """Retrieve an Extract statistics: number of inserts, updates, deletes, etc. that were captured by the process."""
    return _ok(client.post(api.get_extract_stats(extractName), {"command": "STATS", "isReported": True}))


@mcp.tool(description="Retrieve a Replicat statistics: number of inserts, updates, deletes, etc. that were replicated by the process")
def get_replicat_stats(replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8)) -> str:
    """Retrieve a Replicat statistics: number of inserts, updates, deletes, etc. that were replicated by the process."""
    return _ok(client.post(api.get_replicat_stats(replicatName), {"command": "STATS", "isReported": True}))


@mcp.tool(description="Retrieve the details of an extract process: parameters, configuration, targets, type, etc.")
def get_extract_details(extractName: str = Field(..., description="Extract process name", min_length=1, max_length=8)) -> str:
    """Retrieve the details of an extract process: parameters, configuration, targets, type, etc."""
    return _ok(client.get(api.get_extract_details(extractName)))


@mcp.tool(description="Retrieve the details of a replicat process: parameters, configuration, targets, type, etc.")
def get_replicat_details(replicatName: str = Field(..., description="Replicat process name", min_length=1, max_length=8)) -> str:
    """Retrieve the details of a replicat process: parameters, configuration, targets, type, etc."""
    return _ok(client.get(api.get_replicat_details(replicatName)))


def main() -> None:
    """Start the FastMCP server using stdio transport."""
    try:
        _verify_deployment_connectivity()
    except Exception:
        _log_startup(
            "ERROR",
            "Startup aborted. Verify the deployment is started and the configured baseUrl is reachable.",
        )
        if os.getenv("OGG_MCP_DEBUG", "false").strip().lower() == "true":
            traceback.print_exc(file=sys.stderr)
        raise SystemExit(1) from None
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
