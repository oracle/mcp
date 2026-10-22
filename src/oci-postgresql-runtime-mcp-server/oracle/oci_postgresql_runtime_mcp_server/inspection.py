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


_POSTGRESQL_DIALECT = postgresql.dialect()


def _normalize_identifier_list(
    field_name: str,
    values: Optional[list[str]],
) -> Optional[list[str]]:
    if values is None:
        return None
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list of strings")

    normalized_values: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} entries must be non-empty strings")
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
        conn = psycopg.connect(**connect_kwargs)
        conn.read_only = True
        return conn

    engine = create_engine(
        "postgresql+psycopg://",
        creator=connect,
    )
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


def _requested_names_by_schema(table_refs: list[dict[str, str]]) -> dict[str, list[str]]:
    names_by_schema: dict[str, list[str]] = {}
    for ref in table_refs:
        names_by_schema.setdefault(ref["schema"], []).append(ref["name"])
    return names_by_schema


def _ref_names(
    inspector: Any,
    schema: str,
    names: Optional[list[str]],
    kind: ObjectKind,
) -> list[str]:
    if names is None:
        getter = (
            inspector.get_view_names
            if kind == ObjectKind.VIEW
            else inspector.get_table_names
        )
        return sorted(getter(schema=schema) or [])
    comments = _multi(inspector, "get_multi_table_comment", schema, names, kind)
    return [
        name
        for name in names
        if _reflected(comments, schema, name, None) is not None
    ]


def _table_refs_for_request(
    inspector: Any,
    *,
    schemas: list[str],
    table_refs: Optional[list[dict[str, str]]],
    include_views: bool,
) -> list[dict[str, str]]:
    names_by_schema = _requested_names_by_schema(table_refs) if table_refs else {}
    refs = []
    for schema in names_by_schema or {schema: None for schema in schemas}:
        requested_names = names_by_schema.get(schema)
        for name in _ref_names(inspector, schema, requested_names, ObjectKind.TABLE):
            refs.append({"schema": schema, "name": name, "table_type": "BASE TABLE"})
        if include_views:
            for name in _ref_names(inspector, schema, requested_names, ObjectKind.VIEW):
                refs.append({"schema": schema, "name": name, "table_type": "VIEW"})
    return refs


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
    schemas: list[str],
    table_refs: Optional[list[dict[str, str]]],
    include_views: bool,
    detail: str,
    auto_full_limit: int,
) -> tuple[str, list[dict[str, Any]]]:
    refs = _table_refs_for_request(
        inspector,
        schemas=schemas,
        table_refs=table_refs,
        include_views=include_views,
    )
    resolved_detail = detail
    if detail == "auto":
        resolved_detail = "full" if len(refs) <= auto_full_limit else "summary"

    metadata = _table_metadata(
        inspector,
        refs,
        detail=resolved_detail,
    )
    tables = []
    for ref in refs:
        schema = ref["schema"]
        name = ref["name"]
        table = {
            **{
                "table_schema": schema,
                "table_name": name,
                "table_type": ref["table_type"],
            },
            **metadata[(schema, name)],
        }
        if resolved_detail != "full":
            table["columns_omitted"] = True
        tables.append(table)
    return resolved_detail, tables
