"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Opt-in foreign-key tests against a disposable PostgreSQL database."""

import os
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
import pytest

from oracle.oci_postgresql_runtime_mcp_server import server


@pytest.fixture(scope="module")
def foreign_key_database():
    dsn = os.environ.get("POSTGRESQL_MCP_TEST_DSN")
    if not dsn:
        pytest.skip("Set POSTGRESQL_MCP_TEST_DSN to a disposable PostgreSQL database")

    connect_kwargs = conninfo_to_dict(dsn)
    prefix = "mcp_fk_" + uuid4().hex
    source = prefix + "_app"
    shared = prefix + "_shared"
    public_parent = prefix + "_parent"
    parents = {
        "same": (source, "parents"),
        "shared": (shared, "parents"),
        "public": ("public", public_parent),
    }
    child = sql.Identifier(source, "children")

    with psycopg.connect(**connect_kwargs, autocommit=True) as setup:
        with setup.transaction():
            for schema in (source, shared):
                setup.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            for schema, name in parents.values():
                parent = sql.Identifier(schema, name)
                setup.execute(sql.SQL("CREATE TABLE {} (a integer, b integer, PRIMARY KEY (a, b))").format(parent))
                setup.execute(sql.SQL("INSERT INTO {} VALUES (1, 2)").format(parent))
            constraints = [
                sql.SQL("CONSTRAINT {} FOREIGN KEY ({}, {}) REFERENCES {} (a, b) ON UPDATE CASCADE ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED").format(
                    sql.Identifier("fk_" + target),
                    sql.Identifier(target + "_a"),
                    sql.Identifier(target + "_b"),
                    sql.Identifier(*parent),
                )
                for target, parent in parents.items()
            ]
            setup.execute(sql.SQL("CREATE TABLE {} (id integer PRIMARY KEY, same_a integer, same_b integer, shared_a integer, shared_b integer, public_a integer, public_b integer, {})").format(
                child, sql.SQL(", ").join(constraints),
            ))
            setup.execute(sql.SQL("INSERT INTO {} VALUES (1, 1, 2, 1, 2, 1, 2)").format(child))

        try:
            yield {"connect_kwargs": connect_kwargs, "source": source, "shared": shared, "parents": parents}
        finally:
            for schema in (source, shared):
                setup.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            setup.execute(sql.SQL("DROP TABLE {}").format(sql.Identifier("public", public_parent)))


def _foreign_keys(database, monkeypatch, search_path, detail):
    schemas = {"public": "public", "shared": database["shared"]}
    options = "-csearch_path=" + ",".join(schemas[name] for name in search_path)
    monkeypatch.setattr(server, "config_error_msg", None)
    monkeypatch.setattr(server, "config", {
        "connections": {"integration": {"connect_kwargs": {**database["connect_kwargs"], "options": options}}},
        "config_path": None,
    })
    result = server.list_tables(
        "integration", detail=detail,
        table_refs=[{"schema": database["source"], "name": "children"}],
    )
    assert result["count"] == 1
    return {fk["name"]: fk for fk in result["tables"][0]["foreign_keys"]}


@pytest.mark.parametrize("search_path", [(), ("public",), ("public", "shared"), ("shared", "public")])
@pytest.mark.parametrize("detail", ["summary", "full", "auto"])
def test_cross_schema_foreign_key_columns_and_options(foreign_key_database, monkeypatch, search_path, detail):
    foreign_keys = _foreign_keys(foreign_key_database, monkeypatch, search_path, detail)
    assert set(foreign_keys) == {"fk_same", "fk_shared", "fk_public"}
    for target, (_, parent_name) in foreign_key_database["parents"].items():
        foreign_key = foreign_keys["fk_" + target]
        assert foreign_key["constrained_columns"] == [target + "_a", target + "_b"]
        assert foreign_key["referred_table"] == parent_name
        assert foreign_key["referred_columns"] == ["a", "b"]
        assert foreign_key["options"] == {
            "onupdate": "CASCADE", "ondelete": "RESTRICT", "deferrable": True, "initially": "DEFERRED",
        }


@pytest.mark.parametrize("search_path,target", [
    ((), "public"),
    ((), "shared"),
    (("public",), "public"),
    (("public",), "shared"),
    (("public", "shared"), "public"),
    (("public", "shared"), "shared"),
    (("shared", "public"), "public"),
    (("shared", "public"), "shared"),
])
@pytest.mark.parametrize("detail", ["summary", "full", "auto"])
def test_cross_schema_foreign_key_target_namespace(foreign_key_database, monkeypatch, search_path, target, detail):
    foreign_keys = _foreign_keys(foreign_key_database, monkeypatch, search_path, detail)
    expected_schema, _ = foreign_key_database["parents"][target]
    assert foreign_keys["fk_" + target]["referred_schema"] == expected_schema


def test_existing_sqlalchemy_option_with_empty_metadata_search_path(foreign_key_database):
    connect_kwargs = {**foreign_key_database["connect_kwargs"], "options": "-csearch_path="}
    with server._metadata_inspector_cm(connect_kwargs) as inspector:
        assert inspector.default_schema_name is None
        reflected = inspector.get_multi_foreign_keys(
            schema=foreign_key_database["source"], filter_names=["children"],
            postgresql_ignore_search_path=True,
        )
    foreign_keys = {fk["name"]: fk for fk in reflected[(foreign_key_database["source"], "children")]}
    for target, (expected_schema, _) in foreign_key_database["parents"].items():
        assert foreign_keys["fk_" + target]["referred_schema"] == expected_schema


@pytest.mark.parametrize("target", ["public", "shared"])
def test_database_enforces_cross_schema_foreign_keys(foreign_key_database, target):
    child = sql.Identifier(foreign_key_database["source"], "children")
    with psycopg.connect(**foreign_key_database["connect_kwargs"]) as connection:
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            with connection.transaction():
                connection.execute(sql.SQL("INSERT INTO {} (id, {}, {}) VALUES (2, 99, 99)").format(
                    child, sql.Identifier(target + "_a"), sql.Identifier(target + "_b"),
                ))
