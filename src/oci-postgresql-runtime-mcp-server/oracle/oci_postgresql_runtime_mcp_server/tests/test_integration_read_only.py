"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Opt-in tests documenting why SQL validation must protect read-only transactions."""

import os
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
import pytest

from oracle.oci_postgresql_runtime_mcp_server import server


@pytest.fixture
def read_only_database():
    dsn = os.environ.get("POSTGRESQL_MCP_TEST_DSN")
    if not dsn:
        pytest.skip("Set POSTGRESQL_MCP_TEST_DSN to a disposable PostgreSQL database")

    connect_kwargs = conninfo_to_dict(dsn)
    schema = sql.Identifier("mcp_read_only_" + uuid4().hex)
    table = sql.SQL("{}.probe").format(schema)
    with psycopg.connect(**connect_kwargs, autocommit=True) as setup:
        with setup.transaction():
            setup.execute(sql.SQL("CREATE SCHEMA {}").format(schema))
            setup.execute(sql.SQL("CREATE TABLE {} (id integer)").format(table))
        try:
            yield connect_kwargs, table
        finally:
            setup.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(schema))


def test_sql_can_override_driver_read_only_and_commit_before_rollback(read_only_database):
    connect_kwargs, table = read_only_database
    insert = sql.SQL("INSERT INTO {} VALUES (%s)").format(table)

    # Bypass the parser deliberately to document the protection it must provide.
    with server.get_postgresql_connection_cm(connect_kwargs) as connection:
        with connection.cursor() as cursor:
            server._apply_statement_timeouts(cursor)
            with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
                cursor.execute(insert, [1])
            connection.rollback()

            server._apply_statement_timeouts(cursor)
            cursor.execute("SET TRANSACTION READ WRITE")
            cursor.execute("SHOW transaction_read_only")
            assert cursor.fetchone() == ("off",)
            assert connection.read_only is True

            cursor.execute(insert, [2])
            cursor.execute("COMMIT")
            connection.rollback()
            assert connection.read_only is True

    with psycopg.connect(**connect_kwargs) as observer:
        assert observer.execute(sql.SQL("SELECT id FROM {}").format(table)).fetchall() == [(2,)]
