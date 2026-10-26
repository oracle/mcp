"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Opt-in bounded catalog discovery tests against a disposable PostgreSQL database.
"""

import os
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
import pytest

from oracle.oci_postgresql_runtime_mcp_server import server


@pytest.fixture(scope="module")
def catalog_database():
    dsn = os.environ.get("POSTGRESQL_MCP_TEST_DSN")
    if not dsn:
        pytest.skip("Set POSTGRESQL_MCP_TEST_DSN to a disposable PostgreSQL database")
    kwargs = conninfo_to_dict(dsn)
    unique = uuid4().hex
    schemas = ["mcp_pages_" + unique + suffix for suffix in ("_a", "_m space", "_z")]
    prefix = "mcp_item_" + unique + "_"
    expected = []
    with psycopg.connect(**kwargs, autocommit=True) as setup:
        try:
            with setup.transaction():
                for schema in schemas:
                    setup.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
                    for index in range(367):
                        name = prefix + f"{index:04d}"
                        setup.execute(sql.SQL("CREATE TABLE {} (id integer PRIMARY KEY, note text)").format(sql.Identifier(schema, name)))
                        expected.append((schema, name, "BASE TABLE"))
                    name = prefix + "view"
                    setup.execute(sql.SQL("CREATE VIEW {} AS SELECT 1 AS id").format(sql.Identifier(schema, name)))
                    expected.append((schema, name, "VIEW"))
                    name = prefix + "percent%_quote'"
                    setup.execute(sql.SQL("CREATE TABLE {} (id integer)").format(sql.Identifier(schema, name)))
                    expected.append((schema, name, "BASE TABLE"))
            yield {"kwargs": kwargs, "schemas": schemas, "prefix": prefix, "expected": sorted(expected)}
        finally:
            for schema in schemas:
                setup.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def catalog(catalog_database, monkeypatch):
    monkeypatch.setattr(server, "config_error_msg", None)
    monkeypatch.setattr(server, "config", {
        "connections": {"integration": {"connect_kwargs": catalog_database["kwargs"]}},
        "config_path": None,
    })
    return catalog_database


def _walk(**kwargs):
    seen = []
    cursors = set()
    cursor = None
    for _ in range(100):
        page = server.list_tables("integration", cursor=cursor, **kwargs)
        assert page["count"] == len(page["tables"])
        assert page["count"] <= kwargs.get("limit", 100)
        seen.extend((t["table_schema"], t["table_name"], t["table_type"]) for t in page["tables"])
        if not page["has_more"]:
            assert page["next_cursor"] is None
            return seen
        cursor = page["next_cursor"]
        assert cursor and cursor not in cursors
        cursors.add(cursor)
    pytest.fail("Catalog continuation did not finish")


def test_unfiltered_paging_crosses_schema_boundaries(catalog):
    seen = _walk(limit=113, detail="summary")
    assert [r for r in seen if r[0] in catalog["schemas"]] == catalog["expected"]
    assert len(seen) == len(set(seen))


def test_page_maximum_does_not_limit_total_catalog(catalog):
    first = server.list_tables("integration", limit=1000, detail="summary")
    assert first["count"] == 1000 and first["has_more"]
    second = server.list_tables("integration", limit=1000, detail="summary", cursor=first["next_cursor"])
    assert first["count"] + second["count"] == len(catalog["expected"])
    assert not second["has_more"]


def test_small_page_does_not_change_auto_metadata_depth(catalog):
    page = server.list_tables("integration", limit=2)
    assert page["count"] == 2 and page["has_more"]
    assert page["detail"] == "summary"
    assert all("columns" not in t for t in page["tables"])


def test_explicit_tables_and_full_metadata(catalog):
    refs = [{"schema": schema, "name": catalog["prefix"] + "0000"} for schema in catalog["schemas"]]
    seen = _walk(table_refs=refs, limit=1, detail="full")
    assert [(schema, name) for schema, name, _ in seen] == sorted((r["schema"], r["name"]) for r in refs)
    page = server.list_tables("integration", table_refs=refs, limit=1, detail="full")
    assert [c["name"] for c in page["tables"][0]["columns"]] == ["id", "note"]
    assert page["tables"][0]["primary_key"]["constrained_columns"] == ["id"]


def test_schema_filter_and_view_selection_preserved(catalog):
    seen = _walk(schemas=[catalog["schemas"][1]], limit=70, include_views=False, detail="summary")
    assert seen == [r for r in catalog["expected"] if r[0] == catalog["schemas"][1] and r[2] == "BASE TABLE"]


def test_exact_quoted_table_refs_are_preserved(catalog):
    refs = [{"schema": schema, "name": catalog["prefix"] + "percent%_quote'"} for schema in catalog["schemas"]]
    seen = _walk(table_refs=refs, limit=2, detail="summary")
    assert seen == sorted((r["schema"], r["name"], "BASE TABLE") for r in refs)


def test_schema_pages_have_complete_continuation(catalog):
    names = []
    cursor = None
    for _ in range(10):
        page = server.list_schemas("integration", limit=1, cursor=cursor)
        names.extend(page["schemas"])
        assert page["count"] == len(page["schemas"]) <= 1
        if not page["has_more"]:
            assert page["next_cursor"] is None
            break
        cursor = page["next_cursor"]
    assert [name for name in names if name in catalog["schemas"]] == sorted(catalog["schemas"])


def test_cursor_rejects_changed_filters(catalog):
    page = server.list_tables("integration", limit=2, detail="summary")
    with pytest.raises(ValueError):
        server.list_tables("integration", schemas=[catalog["schemas"][0]], limit=2, detail="summary", cursor=page["next_cursor"])
