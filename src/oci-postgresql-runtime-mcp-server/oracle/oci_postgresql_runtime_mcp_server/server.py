"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import contextlib
import hashlib
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Annotated, Any, Literal, Optional

import psycopg
from fastmcp import FastMCP
from psycopg.rows import dict_row, tuple_row
from pydantic import Field
from pydantic_core import from_json, to_json

from . import __project__, __version__
from .inspection import (
    _inspect_postgresql_tables,
    _metadata_inspector_cm,
    _normalize_identifier_list,
    _normalize_table_refs,
)
from .pagination import (
    _DEFAULT_METADATA_LIMIT, _MAX_METADATA_LIMIT, _STATEMENT_TIMEOUT_MS, _LOCK_TIMEOUT_MS,
    _bounded_integer, _bounded_page, _validate_cursor,
)
from .profiles import (
    _CONFIG_ENV_VAR,
    _ConnectionProfile,
    _as_connection_profile,
    _get_package_dir,
    _summarize_connection,
    load_postgresql_config,
)
from .sql_policy import _param_count, _prepare_sql_execution

_DEFAULT_MAX_ROWS = 100
_MAX_RESULT_ROWS = 10_000
_MAX_RESULT_BYTES = 1_048_576
_DEFAULT_AUTO_FULL_TABLE_LIMIT = 100
_MAX_ECHOED_SQL_CHARS = 4000
_TABLE_DETAIL_MODES = {"auto", "summary", "full"}
_EXPECTED_SOURCE_FINGERPRINT_ENV_VAR = "POSTGRESQL_MCP_EXPECTED_SOURCE_FINGERPRINT"
_COLUMN_ORIGIN_SQL = """
with requested(table_oid, column_number) as (
    select * from unnest(%s::oid[], %s::int2[])
)
select
    requested.table_oid,
    requested.column_number,
    relation.relname,
    attribute.attname
from requested
join pg_catalog.pg_class as relation
    on relation.oid = requested.table_oid
join pg_catalog.pg_attribute as attribute
    on attribute.attrelid = requested.table_oid
    and attribute.attnum = requested.column_number
where not attribute.attisdropped
""".strip()
_SOURCE_FINGERPRINT_FILES = (
    "oracle/oci_postgresql_runtime_mcp_server/__init__.py",
    "oracle/oci_postgresql_runtime_mcp_server/inspection.py",
    "oracle/oci_postgresql_runtime_mcp_server/profiles.py",
    "oracle/oci_postgresql_runtime_mcp_server/pagination.py",
    "oracle/oci_postgresql_runtime_mcp_server/server.py",
    "oracle/oci_postgresql_runtime_mcp_server/sql_policy.py",
)

mcp = FastMCP(
    name="oci-postgresql-runtime-mcp-server",
    instructions=(
        "Use this server for runtime PostgreSQL operations only. "
        "It opens PostgreSQL connections, validates connectivity, lists schemas/tables, "
        "and executes SQL queries. It does not provision OCI resources."
    ),
)


def _compute_source_fingerprint() -> str:
    package_dir = Path(_get_package_dir())
    digest = hashlib.sha256()
    for relative_path in _SOURCE_FINGERPRINT_FILES:
        path = package_dir / relative_path
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


SOURCE_FINGERPRINT = _compute_source_fingerprint()
EXPECTED_SOURCE_FINGERPRINT = os.environ.get(_EXPECTED_SOURCE_FINGERPRINT_ENV_VAR)


def _source_fingerprint_status() -> str:
    if not EXPECTED_SOURCE_FINGERPRINT:
        return "not_configured"
    if EXPECTED_SOURCE_FINGERPRINT == SOURCE_FINGERPRINT:
        return "match"
    return "mismatch"


def _runtime_info() -> dict[str, Any]:
    status = _source_fingerprint_status()
    info: dict[str, Any] = {
        "project": __project__,
        "version": __version__,
        "python_version": sys.version.split()[0],
        "source_fingerprint": SOURCE_FINGERPRINT,
        "expected_source_fingerprint": EXPECTED_SOURCE_FINGERPRINT,
        "source_fingerprint_status": status,
        "source_fingerprint_match": status == "match",
    }
    if status == "mismatch":
        info["source_fingerprint_warning"] = (
            "Runtime MCP source fingerprint differs from the expected local "
            "fingerprint; sync/restart the remote runtime before relying on "
            "current SQL policy behavior."
        )
    return info


config: dict[str, Any] = {"connections": {}, "config_path": None}
config_error_msg: Optional[str] = None
try:
    config = load_postgresql_config()
except Exception as exc:  # pragma: no cover - exercised via helper tests
    config_error_msg = str(exc)


def _get_configured_connections() -> dict[str, dict[str, Any]]:
    if config_error_msg is not None:
        raise ValueError(
            "Configured PostgreSQL connection profiles are unavailable. "
            f"Fix {_CONFIG_ENV_VAR} or local_config.json and restart the MCP server. "
            f"Underlying error: {config_error_msg}"
        )
    return config["connections"]


def _resolve_connection_profile(connection_name: str) -> _ConnectionProfile:
    if not isinstance(connection_name, str) or not connection_name.strip():
        raise ValueError("connection_name must be a non-empty string")

    configured_connections = _get_configured_connections()
    if connection_name not in configured_connections:
        raise ValueError(
            f"Connection '{connection_name}' is not a valid connection profile. "
            "Use list_connections() to see available profiles."
        )

    return _as_connection_profile(configured_connections[connection_name])


def _resolve_connect_kwargs(connection_name: str) -> dict[str, Any]:
    return _resolve_connection_profile(connection_name).connect_kwargs


def _statement_metadata(
    sql: str,
    params: Optional[list[Any]],
    *,
    param_count: Optional[int] = None,
) -> dict[str, Any]:
    sql_truncated = len(sql) > _MAX_ECHOED_SQL_CHARS
    metadata: dict[str, Any] = {
        "executed_sql": sql[:_MAX_ECHOED_SQL_CHARS],
        "sql_truncated": sql_truncated,
        "param_count": len(params or []) if param_count is None else param_count,
    }
    if sql_truncated:
        metadata["executed_sql"] += "..."
    if params:
        metadata["params_redacted"] = True
    return metadata


@contextlib.contextmanager
def get_postgresql_connection_cm(connect_kwargs: dict[str, Any]):
    with psycopg.connect(**connect_kwargs) as conn:
        # This configures BEGIN READ ONLY for new transactions, not an immutable SQL policy.
        # Validation must reject transaction overrides and COMMIT; rollback cannot undo a commit.
        conn.read_only = True
        yield conn


def _apply_statement_timeouts(cursor: Any) -> None:
    cursor.execute(f"set local statement_timeout = {_STATEMENT_TIMEOUT_MS}")
    cursor.execute(f"set local lock_timeout = {_LOCK_TIMEOUT_MS}")


def _schema_page(
    connect_kwargs: dict[str, Any],
    *,
    include_system: bool,
    after: Optional[tuple[str, ...]],
    limit: int,
) -> list[str]:
    conditions: list[str] = []
    params: dict[str, Any] = {"limit": limit + 1}
    if not include_system:
        conditions.extend(["schema_name <> 'information_schema'", "left(schema_name, 3) <> 'pg_'"])
    if after is not None:
        conditions.append('schema_name::text collate "C" > %(after)s::text collate "C"')
        params["after"] = after[0]
    query = "select schema_name from information_schema.schemata"
    if conditions:
        query += " where " + " and ".join(conditions)
    query += ' order by schema_name::text collate "C" limit %(limit)s'
    with get_postgresql_connection_cm(connect_kwargs) as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(f"set local statement_timeout = {_STATEMENT_TIMEOUT_MS}")
            cursor.execute(f"set local lock_timeout = {_LOCK_TIMEOUT_MS}")
            cursor.execute(query, params)
            return [row["schema_name"] for row in cursor.fetchmany(limit + 1)]


def _resolve_column_origins(
    conn: Any,
    origins: list[tuple[int, int]],
) -> dict[tuple[int, int], tuple[str, str]]:
    unique_origins = list(dict.fromkeys(origins))
    if not unique_origins:
        return {}

    table_oids = [origin[0] for origin in unique_origins]
    column_numbers = [origin[1] for origin in unique_origins]
    try:
        with conn.transaction():
            with conn.cursor(row_factory=tuple_row) as cursor:
                cursor.execute(_COLUMN_ORIGIN_SQL, [table_oids, column_numbers])
                rows = cursor.fetchall()
    except psycopg.DatabaseError as exc:
        if conn.closed or isinstance(exc, psycopg.OperationalError):
            raise
        return {}

    return {
        (table_oid, column_number): (table_name, column_name)
        for table_oid, column_number, table_name, column_name in rows
    }


def _result_column_keys(conn: Any, cursor: Any) -> list[str]:
    labels = [getattr(column, "name", column[0]) for column in cursor.description]
    label_counts = Counter(labels)
    if all(count == 1 for count in label_counts.values()):
        return labels

    origins: list[Optional[tuple[int, int]]] = [None] * len(labels)
    pgresult = getattr(cursor, "pgresult", None)
    if pgresult is not None:
        for index, label in enumerate(labels):
            if label_counts[label] == 1:
                continue
            table_oid = pgresult.ftable(index)
            column_number = pgresult.ftablecol(index)
            if table_oid != 0 and column_number != 0:
                origins[index] = (table_oid, column_number)

    resolved_origins = _resolve_column_origins(
        conn,
        [origin for origin in origins if origin is not None],
    )
    preferred_keys = list(labels)
    for index, origin in enumerate(origins):
        if origin is None or origin not in resolved_origins:
            continue
        table_name, column_name = resolved_origins[origin]
        preferred_keys[index] = f"{table_name}.{column_name}"

    reserved_labels = set(labels)
    used_keys: set[str] = set()
    result_keys: list[str] = []
    for label, preferred_key in zip(labels, preferred_keys):
        if label_counts[label] == 1:
            result_key = label
        elif preferred_key not in used_keys and (
            preferred_key not in reserved_labels or preferred_key == label
        ):
            result_key = preferred_key
        else:
            suffix = 2
            while True:
                candidate = f"{preferred_key}_{suffix}"
                if candidate not in used_keys and candidate not in reserved_labels:
                    result_key = candidate
                    break
                suffix += 1
        used_keys.add(result_key)
        result_keys.append(result_key)

    return result_keys


def _cursor_result(
    conn: Any,
    cursor: Any,
    *,
    metadata: dict[str, Any],
    max_rows: int,
    remaining_result_bytes: int,
) -> tuple[dict[str, Any], int]:
    if cursor.description:
        columns = _result_column_keys(conn, cursor)

        rows: list[Any] = []
        result_bytes = 0
        truncation_reason = None
        batch = cursor.fetchmany(max_rows + 1)

        for raw_row in batch:
            if len(rows) == max_rows:
                break
            row_json = to_json(
                dict(zip(columns, raw_row, strict=True)),
                bytes_mode="base64",
                fallback=str,
                inf_nan_mode="strings",
            )
            row = from_json(row_json)
            row_bytes = len(row_json) + (1 if rows else 0)
            if row_bytes > remaining_result_bytes - result_bytes:
                truncation_reason = "max_result_bytes"
                break
            rows.append(row)
            result_bytes += row_bytes

        if truncation_reason is None and len(batch) > max_rows:
            truncation_reason = "max_rows"

        result = {
            "has_result_set": True,
            **metadata,
            "command": cursor.statusmessage,
            "columns": columns,
            "row_count": len(rows),
            "rows": rows,
            "truncated": truncation_reason is not None,
        }
        if truncation_reason is not None:
            result["truncation_reason"] = truncation_reason
        return result, result_bytes

    result: dict[str, Any] = {
        "has_result_set": False,
        **metadata,
        "command": cursor.statusmessage,
    }
    if cursor.rowcount >= 0:
        result["row_count"] = cursor.rowcount
    return result, 0


@mcp.tool(description="Returns non-secret PostgreSQL runtime MCP source and environment metadata.")
def get_runtime_info() -> dict[str, Any]:
    return _runtime_info()


@mcp.tool(
    description=(
        "Lists configured PostgreSQL connection profiles loaded at server startup from "
        f"{_CONFIG_ENV_VAR} or local_config.json."
    )
)
def list_connections() -> dict[str, Any]:
    configured_connections = _get_configured_connections()
    connections = [
        _summarize_connection(connection_name, _as_connection_profile(connection))
        for connection_name, connection in sorted(configured_connections.items())
    ]
    return {
        **_runtime_info(),
        "config_path_loaded": config.get("config_path") is not None,
        "count": len(connections),
        "connections": connections,
    }


@mcp.tool(
    description=(
        "Tests a PostgreSQL runtime connection using a configured connection_name."
    )
)
def test_connection(
    connection_name: Annotated[
        str,
        Field(
            description=(
                "Configured PostgreSQL connection profile name loaded from "
                f"{_CONFIG_ENV_VAR} or local_config.json."
            )
        ),
    ],
) -> dict[str, Any]:
    connect_kwargs = _resolve_connect_kwargs(connection_name)

    with get_postgresql_connection_cm(connect_kwargs) as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                select
                    version() as server_version,
                    current_user as current_user,
                    current_database() as current_database
                """
            )
            row = cursor.fetchone() or {}

    return {
        "status": "ok",
        "server_version": row.get("server_version"),
        "current_user": row.get("current_user"),
        "current_database": row.get("current_database"),
    }


@mcp.tool(description="Lists a bounded page of visible PostgreSQL schemas. Follow next_cursor to continue.")
def list_schemas(
    connection_name: Annotated[
        str,
        Field(description="Configured PostgreSQL connection profile name."),
    ],
    include_system: Annotated[
        bool,
        Field(description="Include PostgreSQL system schemas when true."),
    ] = False,
    limit: Annotated[
        int,
        Field(
            ge=1,
            le=_MAX_METADATA_LIMIT,
            description="Maximum number of schemas to return (1-1000).",
        ),
    ] = _DEFAULT_METADATA_LIMIT,
    cursor: Annotated[
        Optional[list[str]],
        Field(
            min_length=1,
            max_length=1,
            description="Last returned [schema] from next_cursor; repeat the same connection and filters.",
        ),
    ] = None,
) -> dict[str, Any]:
    _bounded_integer("limit", limit)
    after = _validate_cursor(cursor, 1)
    schemas = _schema_page(_resolve_connect_kwargs(connection_name), include_system=include_system,
                           after=after, limit=limit)
    return _bounded_page(schemas[:limit], field="schemas", metadata={},
                         key=lambda name: (name,), has_more=len(schemas) > limit)


@mcp.tool(
    description=(
        "Lists a bounded page of PostgreSQL tables and views with auto, summary, or full metadata. "
        "Without schemas or table_refs, inspects all visible schemas in the connected "
        "database except information_schema and schemas whose names start with pg_. "
        "System schemas can be selected explicitly through schemas or table_refs. "
        "Auto mode returns full column metadata for up to 100 matched objects, "
        "then falls back to summary metadata. Follow next_cursor to continue."
    )
)
def list_tables(
    connection_name: Annotated[
        str,
        Field(
            description=(
                "Configured PostgreSQL connection profile name loaded from "
                f"{_CONFIG_ENV_VAR} or local_config.json."
            )
        ),
    ],
    include_views: Annotated[
        bool,
        Field(description="Include views alongside base tables when true."),
    ] = True,
    detail: Annotated[
        Literal["auto", "summary", "full"],
        Field(description="Metadata depth to return: auto, summary, or full."),
    ] = "auto",
    auto_full_limit: Annotated[
        int,
        Field(
            ge=1, le=_MAX_METADATA_LIMIT,
            description=(
                "When detail is auto, return full metadata only when the matched "
                "table/view count is at or below this limit."
            )
        ),
    ] = _DEFAULT_AUTO_FULL_TABLE_LIMIT,
    schemas: Annotated[
        Optional[list[str]],
        Field(
            description=(
                "Exact schema names to inspect. Mutually exclusive with table_refs. "
                "If neither filter is supplied, inspects all visible schemas in the "
                "connected database except information_schema and schemas whose names "
                "start with pg_. Explicit names may include system schemas."
            )
        ),
    ] = None,
    table_refs: Annotated[
        Optional[list[dict[str, str]]],
        Field(
            description=(
                "Exact table or view references to inspect, each with schema and name. "
                "Mutually exclusive with schemas. Explicit references may include "
                "system schemas."
            )
        ),
    ] = None,
    limit: Annotated[
        int,
        Field(
            ge=1,
            le=_MAX_METADATA_LIMIT,
            description="Maximum number of tables or views to return (1-1000).",
        ),
    ] = _DEFAULT_METADATA_LIMIT,
    cursor: Annotated[
        Optional[list[str]],
        Field(
            min_length=2,
            max_length=2,
            description="Last returned [schema, table] from next_cursor; repeat the same connection and filters.",
        ),
    ] = None,
) -> dict[str, Any]:
    if detail not in _TABLE_DETAIL_MODES:
        raise ValueError("detail must be one of: auto, summary, full")
    _bounded_integer("limit", limit)
    _bounded_integer("auto_full_limit", auto_full_limit)
    normalized_schemas = _normalize_identifier_list("schemas", schemas)
    normalized_table_refs = _normalize_table_refs(table_refs)
    if normalized_schemas is not None and normalized_table_refs is not None:
        raise ValueError("schemas and table_refs are mutually exclusive")
    after = _validate_cursor(cursor, 2)
    connect_kwargs = _resolve_connect_kwargs(connection_name)
    with _metadata_inspector_cm(connect_kwargs) as inspector:
        resolved_detail, tables, has_more = _inspect_postgresql_tables(
            inspector, schemas=normalized_schemas, table_refs=normalized_table_refs,
            include_views=include_views, detail=detail, auto_full_limit=auto_full_limit,
            limit=limit, after=after,
        )
    selected_schemas = normalized_schemas
    if selected_schemas is None:
        selected_schemas = list(dict.fromkeys(
            ref["schema"] for ref in normalized_table_refs
        )) if normalized_table_refs is not None else list(dict.fromkeys(table["table_schema"] for table in tables))
    metadata: dict[str, Any] = {
        "detail_requested": detail, "detail": resolved_detail,
        "auto_full_limit": auto_full_limit, "include_views": include_views,
        "schemas": selected_schemas, "table_refs": normalized_table_refs,
    }
    if normalized_table_refs is None and normalized_schemas is not None and len(normalized_schemas) == 1:
        metadata["schema"] = normalized_schemas[0]
    result = _bounded_page(tables, field="tables", metadata=metadata,
                           key=lambda table: (table["table_schema"], table["table_name"]), has_more=has_more)
    if normalized_schemas is None and normalized_table_refs is None:
        result["schemas"] = list(dict.fromkeys(table["table_schema"] for table in result["tables"]))
    return result


@mcp.tool(
    description=(
        "Executes read-only PostgreSQL SQL using the supplied connection profile. "
        "Use params for parameterized queries."
    )
)
def execute_query(
    sql: Annotated[
        str,
        Field(description="SQL statement or semicolon-separated statements to execute."),
    ],
    connection_name: Annotated[
        str,
        Field(
            description=(
                "Configured PostgreSQL connection profile name loaded from "
                f"{_CONFIG_ENV_VAR} or local_config.json."
            )
        ),
    ],
    params: Annotated[
        Optional[list[Any]],
        Field(
            description=(
                "Optional bind parameters. Use a flat list for one statement and "
                "one nested bind list per statement for multi-statement SQL."
            )
        ),
    ] = None,
    max_rows: Annotated[
        int,
        Field(
            ge=1,
            le=_MAX_RESULT_ROWS,
            description=(
                "Maximum number of result rows to return for result sets "
                f"(1-{_MAX_RESULT_ROWS})."
            ),
        ),
    ] = _DEFAULT_MAX_ROWS,
) -> dict[str, Any]:
    if not 1 <= max_rows <= _MAX_RESULT_ROWS:
        raise ValueError(f"max_rows must be between 1 and {_MAX_RESULT_ROWS}")

    profile = _resolve_connection_profile(connection_name)
    prepared_statements = _prepare_sql_execution(sql, params)
    statement_metadata = _statement_metadata(
        sql,
        params,
        param_count=_param_count(prepared_statements),
    )

    with get_postgresql_connection_cm(profile.connect_kwargs) as conn:
        with conn.cursor(row_factory=tuple_row) as cursor:
            try:
                results: list[dict[str, Any]] = []
                remaining_result_bytes = _MAX_RESULT_BYTES
                for index, statement in enumerate(prepared_statements, start=1):
                    _apply_statement_timeouts(cursor)
                    cursor_cm = (
                        conn.cursor(
                            name=f"_odsp_mcp_result_{index}",
                            row_factory=tuple_row,
                            scrollable=False,
                        )
                        if statement.server_cursor_compatible
                        else contextlib.nullcontext(cursor)
                    )
                    with cursor_cm as result_cursor:
                        result_cursor.execute(statement.sql, statement.params)
                        command = result_cursor.statusmessage
                        result, result_bytes = _cursor_result(
                            conn,
                            result_cursor,
                            metadata={
                                **_statement_metadata(
                                    statement.sql,
                                    statement.params,
                                ),
                                "statement_index": index,
                                "statement_kind": statement.kind,
                            },
                            max_rows=max_rows,
                            remaining_result_bytes=remaining_result_bytes,
                        )
                        if statement.server_cursor_compatible:
                            result["command"] = command or "SELECT"
                    results.append(result)
                    remaining_result_bytes -= result_bytes

                # Read-only mode rejects prohibited writes; rollback discards permitted
                # transactional effects, such as queued notifications, instead of committing.
                conn.rollback()

            except Exception:
                conn.rollback()
                raise

            if len(results) == 1:
                return {
                    **results[0],
                    **statement_metadata,
                }

            return {
                "has_result_set": any(result["has_result_set"] for result in results),
                "has_multiple_statements": True,
                **statement_metadata,
                "statement_count": len(results),
                "statements": results,
            }


def main() -> None:
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
