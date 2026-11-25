"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Opt-in native column-type tests against a disposable PostgreSQL database."""

import os
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
import pytest
from sqlalchemy.exc import SAWarning

from oracle.oci_postgresql_runtime_mcp_server import server


@pytest.fixture(scope="module")
def column_type_database():
    dsn = os.environ.get("POSTGRESQL_MCP_TEST_DSN")
    if not dsn:
        pytest.skip("Set POSTGRESQL_MCP_TEST_DSN to a disposable PostgreSQL database")

    connect_kwargs = {**conninfo_to_dict(dsn), "options": "-csearch_path=public"}
    schema = " mcp_types_" + uuid4().hex + " "
    table = " typed rows "
    view = " typed view "
    with psycopg.connect(**connect_kwargs, autocommit=True) as setup:
        with setup.transaction():
            setup.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            setup.execute(sql.SQL("CREATE TYPE {} AS (value integer)").format(sql.Identifier(schema, "payload")))
            setup.execute(sql.SQL("CREATE TABLE {} (id integer, location point, locations point[], payload {}, payloads {}[], amount numeric(12, 3), occurred_at timestamp(3) with time zone)").format(
                sql.Identifier(schema, table),
                sql.Identifier(schema, "payload"),
                sql.Identifier(schema, "payload"),
            ))
            setup.execute(sql.SQL("CREATE VIEW {} AS SELECT * FROM {}").format(
                sql.Identifier(schema, view), sql.Identifier(schema, table),
            ))
        try:
            yield {"connect_kwargs": connect_kwargs, "schema": schema, "objects": [table, view]}
        finally:
            setup.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def _configure(monkeypatch, database):
    monkeypatch.setattr(server, "config_error_msg", None)
    monkeypatch.setattr(server, "config", {
        "connections": {"integration": {"connect_kwargs": database["connect_kwargs"]}},
        "config_path": None,
    })


@pytest.mark.parametrize("detail", ["auto", "full"])
@pytest.mark.parametrize("filter_name", ["schemas", "table_refs"])
def test_list_tables_preserves_native_unknown_column_types(column_type_database, monkeypatch, detail, filter_name):
    database = column_type_database
    _configure(monkeypatch, database)
    filters = (
        {"schemas": [database["schema"]]}
        if filter_name == "schemas"
        else {"table_refs": [{"schema": database["schema"], "name": name} for name in database["objects"]]}
    )
    with pytest.warns(SAWarning, match="Did not recognize type"):
        result = server.list_tables("integration", detail=detail, **filters)

    assert result["detail"] == "full"
    assert result["count"] == 2
    with psycopg.connect(**database["connect_kwargs"]) as connection:
        for table in result["tables"]:
            assert table["table_schema"] == database["schema"]
            relation = sql.Identifier(database["schema"], table["table_name"]).as_string(connection)
            native_types = dict(connection.execute(
                "SELECT attname, pg_catalog.format_type(atttypid, atttypmod) "
                "FROM pg_catalog.pg_attribute WHERE attrelid = %s::regclass "
                "AND attnum > 0 AND NOT attisdropped",
                [relation],
            ).fetchall())
            columns = {column["name"]: column for column in table["columns"]}
            for name in ("location", "locations", "payload", "payloads"):
                assert columns[name]["type"] == native_types[name]
            assert columns["location"]["type"] == "point"
            assert columns["locations"]["type"] == "point[]"
            assert columns["id"]["type"] == "INTEGER"
            assert columns["amount"]["type"] == "NUMERIC(12, 3)"
            assert columns["occurred_at"]["type"] == "TIMESTAMP(3) WITH TIME ZONE"


def test_list_tables_summary_omits_unknown_column_types(column_type_database, monkeypatch):
    _configure(monkeypatch, column_type_database)
    result = server.list_tables("integration", detail="summary", schemas=[column_type_database["schema"]])
    assert result["count"] == 2
    assert all(table["columns_omitted"] and "columns" not in table for table in result["tables"])
