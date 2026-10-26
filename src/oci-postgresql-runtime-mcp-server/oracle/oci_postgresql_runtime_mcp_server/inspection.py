"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import contextlib
from typing import Any, Optional

import psycopg
from sqlalchemy import create_engine, inspect as inspect_database, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import ObjectKind
from sqlalchemy.exc import CompileError
from sqlalchemy.types import TypeEngine

from .pagination import _MAX_IDENTIFIER_BYTES, _MAX_METADATA_LIMIT, _LOCK_TIMEOUT_MS, _STATEMENT_TIMEOUT_MS


_POSTGRESQL_DIALECT = postgresql.dialect()


def _normalize_identifier_list(
    field_name: str,
    values: Optional[list[str]],
) -> Optional[list[str]]:
    if values is None:
        return None
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list of strings")

    if len(values) > _MAX_METADATA_LIMIT:
        raise ValueError(f"{field_name} may contain at most {_MAX_METADATA_LIMIT} entries")
    normalized_values: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} entries must be non-empty strings")
        if len(value.encode("utf-8")) > _MAX_IDENTIFIER_BYTES or "\x00" in value:
            raise ValueError(f"{field_name} entries must be valid database identifiers")
        if value not in seen_values:
            normalized_values.append(value)
            seen_values.add(value)
    if not normalized_values:
        raise ValueError(f"{field_name} must include at least one entry")
    return normalized_values


def _normalize_table_refs(
    table_refs: Optional[list[dict[str, str]]],
) -> Optional[list[dict[str, str]]]:
    if table_refs is None:
        return None
    if not isinstance(table_refs, list):
        raise ValueError("table_refs must be a list of objects")

    if len(table_refs) > _MAX_METADATA_LIMIT:
        raise ValueError(f"table_refs may contain at most {_MAX_METADATA_LIMIT} entries")
    normalized_refs: list[dict[str, str]] = []
    seen_refs: set[tuple[str, str]] = set()
    for ref in table_refs:
        if not isinstance(ref, dict):
            raise ValueError("table_refs entries must be objects")
        schema = ref.get("schema")
        name = ref.get("name") or ref.get("table_name")
        if not isinstance(schema, str) or not schema:
            raise ValueError("table_refs entries must include a non-empty schema")
        if not isinstance(name, str) or not name:
            raise ValueError("table_refs entries must include a non-empty name")
        if any(len(value.encode("utf-8")) > _MAX_IDENTIFIER_BYTES or "\x00" in value for value in (schema, name)):
            raise ValueError("table_refs entries must be valid database identifiers")
        normalized_ref = {"schema": schema, "name": name}
        ref_key = (normalized_ref["schema"], normalized_ref["name"])
        if ref_key not in seen_refs:
            normalized_refs.append(normalized_ref)
            seen_refs.add(ref_key)
    if not normalized_refs:
        raise ValueError("table_refs must include at least one entry")
    return normalized_refs


@contextlib.contextmanager
def _metadata_inspector_cm(connect_kwargs: dict[str, Any]):
    def connect():
        options = connect_kwargs.get("options") or ""
        conn = psycopg.connect(**{
            **connect_kwargs,
            "options": f"{options} -cstatement_timeout={_STATEMENT_TIMEOUT_MS} "
            f"-clock_timeout={_LOCK_TIMEOUT_MS}",
        })
        conn.read_only = True
        return conn

    engine = create_engine("postgresql+psycopg://", creator=connect)
    try:
        yield inspect_database(engine)
    finally:
        engine.dispose()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, TypeEngine):
        return value.compile(dialect=_POSTGRESQL_DIALECT)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    return str(value)


def _reflected(reflected: dict[Any, Any], schema: str, name: str, default: Any) -> Any:
    return reflected.get((schema, name), reflected.get((None, name), default))


def _resolve_column_types(
    inspector: Any,
    schema: str,
    columns: dict[Any, Any],
) -> dict[Any, Any]:
    unresolved: set[tuple[str, str]] = set()
    for (_, table_name), table_columns in columns.items():
        for column in table_columns:
            column_type = column.get("type")
            if isinstance(column_type, TypeEngine):
                try:
                    column_type.compile(dialect=_POSTGRESQL_DIALECT)
                except CompileError:
                    unresolved.add((table_name, column["name"]))
    if not unresolved:
        return columns

    with inspector.bind.connect() as connection:
        rows = connection.execute(
            text(
                """
                select relation.relname, attribute.attname,
                    pg_catalog.format_type(attribute.atttypid, attribute.atttypmod)
                from pg_catalog.pg_attribute as attribute
                join pg_catalog.pg_class as relation
                    on relation.oid = attribute.attrelid
                join pg_catalog.pg_namespace as namespace
                    on namespace.oid = relation.relnamespace
                where namespace.nspname = :schema
                    and relation.relname = any(cast(:table_names as pg_catalog.text[]))
                    and attribute.attnum > 0
                    and not attribute.attisdropped
                """
            ),
            {
                "schema": schema,
                "table_names": sorted({name for name, _ in unresolved}),
            },
        )
        native_types = {
            (table_name, column_name): native_type
            for table_name, column_name, native_type in rows
        }

    return {
        key: [
            {**column, "type": native_types[(key[1], column["name"])]}
            if (key[1], column["name"]) in unresolved
            else column
            for column in table_columns
        ]
        for key, table_columns in columns.items()
    }


def _resolve_foreign_key_schemas(
    inspector: Any,
    schema: str,
    foreign_keys: dict[Any, Any],
) -> dict[Any, Any]:
    names = sorted({name for (_, name), keys in foreign_keys.items() if keys})
    if not names:
        return foreign_keys

    # SQLAlchemy's search-path-relative schemas are ambiguous in standalone JSON.
    with inspector.bind.connect() as connection:
        rows = connection.execute(
            text(
                """
                select source.relname, constraint_info.conname, target_namespace.nspname
                from pg_catalog.pg_constraint as constraint_info
                join pg_catalog.pg_class as source
                    on source.oid = constraint_info.conrelid
                join pg_catalog.pg_namespace as source_namespace
                    on source_namespace.oid = source.relnamespace
                join pg_catalog.pg_class as target
                    on target.oid = constraint_info.confrelid
                join pg_catalog.pg_namespace as target_namespace
                    on target_namespace.oid = target.relnamespace
                where constraint_info.contype = 'f'
                    and source_namespace.nspname = :schema
                    and source.relname = any(cast(:table_names as pg_catalog.text[]))
                """
            ),
            {"schema": schema, "table_names": names},
        )
        target_schemas = {
            (table_name, constraint_name): target_schema
            for table_name, constraint_name, target_schema in rows
        }

    return {
        key: [
            {**foreign_key, "referred_schema": target_schemas[(key[1], foreign_key["name"])]}
            for foreign_key in keys
        ]
        for key, keys in foreign_keys.items()
    }


def _multi(
    inspector: Any,
    method: str,
    schema: str,
    names: list[str],
    kind: ObjectKind,
) -> dict[Any, Any]:
    if not names:
        return {}
    try:
        return (
            getattr(inspector, method)(schema=schema, filter_names=names, kind=kind)
            or {}
        )
    except NotImplementedError:
        return {}


def _discover_table_refs(
    inspector: Any,
    *,
    schemas: Optional[list[str]],
    table_refs: Optional[list[dict[str, str]]],
    include_views: bool,
    after: Optional[tuple[str, ...]],
    limit: int,
) -> list[dict[str, str]]:
    conditions = [
        "relation.relkind in ('r', 'p', 'v')" if include_views else "relation.relkind in ('r', 'p')",
        "relation.relpersistence <> 't'",
    ]
    params: dict[str, Any] = {"limit": limit}
    if after is not None:
        params["after_schema"], params["after_name"] = after
    if table_refs is not None:
        conditions.append("""exists (
            select 1 from unnest(cast(:ref_schemas as pg_catalog.text[]),
                cast(:ref_names as pg_catalog.text[])) as requested(schema, name)
            where requested.schema = namespace.nspname and requested.name = relation.relname
        )""")
        params["ref_schemas"] = [ref["schema"] for ref in table_refs]
        params["ref_names"] = [ref["name"] for ref in table_refs]
        if after is not None:
            conditions.append("""(namespace.nspname, relation.relname) >
                (cast(:after_schema as pg_catalog.name) collate "C",
                 cast(:after_name as pg_catalog.name) collate "C")""")
        from_clause = """pg_catalog.pg_class as relation
            join pg_catalog.pg_namespace as namespace on namespace.oid = relation.relnamespace"""
    else:
        namespace_conditions = []
        visible_join = ""
        if schemas is not None:
            namespace_conditions.append("namespace.nspname = any(cast(:schemas as pg_catalog.text[]))")
            params["schemas"] = schemas
        else:
            visible_join = "join information_schema.schemata as visible on visible.schema_name = namespace.nspname"
            namespace_conditions.extend([
                "namespace.nspname <> 'information_schema'",
                "left(namespace.nspname, 3) <> 'pg_'",
            ])
        conditions.append("relation.relnamespace = namespace.oid")
        if after is not None:
            namespace_conditions.append('namespace.nspname >= cast(:after_schema as pg_catalog.name) collate "C"')
            conditions.append("""relation.relname > (case
                when namespace.nspname = cast(:after_schema as pg_catalog.name)
                then cast(:after_name as pg_catalog.name) else ''::pg_catalog.name end) collate "C"
            """)
        # Limit each schema in native name order so the catalog index can serve the page.
        from_clause = """pg_catalog.pg_namespace as namespace """ + visible_join + """
            cross join lateral (
                select relation.relname, relation.relkind
                from pg_catalog.pg_class as relation
                where """ + " and ".join(conditions) + """
                order by relation.relname collate "C" limit :limit
            ) as relation"""
        conditions = namespace_conditions
    query = text("""
        select namespace.nspname as schema, relation.relname as name,
            case when relation.relkind = 'v' then 'VIEW' else 'BASE TABLE' end as table_type
        from """ + from_clause + " where " + " and ".join(conditions) +
        ' order by namespace.nspname collate "C", relation.relname collate "C" limit :limit')
    with inspector.bind.connect() as connection:
        rows = connection.execute(query, params).mappings().fetchmany(limit)
    return [dict(row) for row in rows]


def _table_metadata(
    inspector: Any,
    refs: list[dict[str, str]],
    *,
    detail: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    metadata: dict[tuple[str, str], dict[str, Any]] = {}
    refs_by_schema: dict[tuple[str, ObjectKind], list[str]] = {}
    for ref in refs:
        kind = ObjectKind.VIEW if ref["table_type"] == "VIEW" else ObjectKind.TABLE
        refs_by_schema.setdefault((ref["schema"], kind), []).append(ref["name"])

    for (schema, kind), names in refs_by_schema.items():
        comments = _multi(inspector, "get_multi_table_comment", schema, names, kind)
        indexes = _multi(inspector, "get_multi_indexes", schema, names, kind)
        fks = _resolve_foreign_key_schemas(
            inspector, schema,
            _multi(inspector, "get_multi_foreign_keys", schema, names, kind),
        )
        columns = (
            _multi(inspector, "get_multi_columns", schema, names, kind)
            if detail == "full"
            else {}
        )
        if detail == "full":
            columns = _resolve_column_types(inspector, schema, columns)
        pks = (
            _multi(inspector, "get_multi_pk_constraint", schema, names, kind)
            if detail == "full"
            else {}
        )
        uniques = (
            _multi(inspector, "get_multi_unique_constraints", schema, names, kind)
            if detail == "full"
            else {}
        )
        checks = (
            _multi(inspector, "get_multi_check_constraints", schema, names, kind)
            if detail == "full"
            else {}
        )

        for name in names:
            table = {
                "comment": (_reflected(comments, schema, name, {}) or {}).get("text"),
                "indexes": _jsonable(_reflected(indexes, schema, name, [])),
                "foreign_keys": _jsonable(_reflected(fks, schema, name, [])),
            }
            if detail == "full":
                reflected_columns = _jsonable(_reflected(columns, schema, name, []))
                table.update(
                    {
                        "column_count": len(reflected_columns),
                        "columns": reflected_columns,
                        "primary_key": _jsonable(_reflected(pks, schema, name, {})),
                        "unique_constraints": _jsonable(
                            _reflected(uniques, schema, name, [])
                        ),
                        "check_constraints": _jsonable(
                            _reflected(checks, schema, name, [])
                        ),
                    }
                )
            metadata[(schema, name)] = table
    return metadata


def _inspect_postgresql_tables(
    inspector: Any,
    *,
    schemas: Optional[list[str]],
    table_refs: Optional[list[dict[str, str]]],
    include_views: bool,
    detail: str,
    auto_full_limit: int,
    limit: int,
    after: Optional[tuple[str, ...]],
) -> tuple[str, list[dict[str, Any]], bool]:
    filters = {"schemas": schemas, "table_refs": table_refs,
               "include_views": include_views}
    candidates = _discover_table_refs(inspector, **filters, after=after, limit=limit + 1)
    has_more = len(candidates) > limit
    refs = candidates[:limit]
    resolved_detail = detail
    if detail == "auto":
        # Probe the entire filtered scope, not only this page. Otherwise every
        # short page of a large catalog would incorrectly request full metadata.
        if after is None and (len(candidates) > auto_full_limit or not has_more):
            probe = candidates
        else:
            probe = _discover_table_refs(inspector, **filters, after=None, limit=auto_full_limit + 1)
        resolved_detail = "full" if len(probe) <= auto_full_limit else "summary"

    metadata = _table_metadata(inspector, refs, detail=resolved_detail)
    tables = []
    for ref in refs:
        schema, name = ref["schema"], ref["name"]
        table = {
            "table_schema": schema, "table_name": name,
            "table_type": ref["table_type"], **metadata[(schema, name)],
        }
        if resolved_detail != "full":
            table["columns_omitted"] = True
        tables.append(table)
    return resolved_detail, tables, has_more
