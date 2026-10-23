"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import contextlib
import json
from unittest.mock import Mock, patch

import psycopg
import pytest
from fastmcp import Client
from psycopg._queries import PostgresQuery
from psycopg.adapt import Transformer
from psycopg.rows import tuple_row
from psycopg.types.range import Range
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    BIT,
    DOMAIN,
    ENUM,
    INTEGER,
    INTERVAL,
    TIMESTAMP,
)
from sqlalchemy.types import NullType, TypeEngine

import oracle.oci_postgresql_runtime_mcp_server.server as server_module
from oracle.oci_postgresql_runtime_mcp_server.inspection import _jsonable
from oracle.oci_postgresql_runtime_mcp_server.server import mcp
from oracle.oci_postgresql_runtime_mcp_server.sql_policy import (
    _prepare_sql_execution,
    _replace_psycopg_placeholders,
)

TEST_CONFIG = {
    "connections": {
        "app-db": {
            "host": "db.example.oraclecloud.com",
            "dbname": "app_db",
            "user": "app_user",
            "password": "super-secret",
            "port": 5432,
            "connect_timeout": 10,
            "application_name": "oracle.oci-postgresql-runtime-mcp-server",
        }
    },
    "config_path": "/tmp/profiles.json",
}

DEFAULT_TIMEOUT_CALLS = [
    ("set local statement_timeout = 300000", None),
    ("set local lock_timeout = 5000", None),
]


def load_config_with_overrides(monkeypatch, tmp_path, **overrides):
    connection = {
        "host": "db.example.oraclecloud.com",
        "database": "app_db",
        "user": "app_user",
        "password": "super-secret",
        **overrides,
    }
    config_path = tmp_path / "profiles.json"
    config_path.write_text(
        json.dumps({"connections": {"app-db": connection}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("POSTGRESQL_MCP_CONFIG", str(config_path))
    return server_module.load_postgresql_config()


class FakePGResult:
    def __init__(self, origins):
        self.origins = origins

    def ftable(self, index):
        return self.origins[index][0]

    def ftablecol(self, index):
        return self.origins[index][1]


class FakeCursor:
    def __init__(
        self,
        *,
        fetchone_result=None,
        fetchall_result=None,
        fetchmany_result=None,
        description=None,
        execute_error=None,
        pgresult=None,
        rowcount=0,
        statusmessage="OK",
    ):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.fetchmany_result = list(fetchmany_result or [])
        self.fetchmany_sizes = []
        self.description = description
        self.execute_error = execute_error
        self.pgresult = pgresult
        self.rowcount = rowcount
        self.statusmessage = statusmessage
        self.executed = []
        self.row_factory = None
        self.enter_count = 0
        self.exit_count = 0

    def __enter__(self):
        self.enter_count += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exit_count += 1
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result

    def fetchmany(self, size):
        self.fetchmany_sizes.append(size)
        rows = self.fetchmany_result[:size]
        del self.fetchmany_result[:size]
        if self.row_factory is tuple_row:
            rows = [tuple(row.values()) if isinstance(row, dict) else row for row in rows]
        return rows


class FakeConnection:
    def __init__(self, cursor, *, additional_cursors=None, named_cursors=None):
        self._cursor = cursor
        self._cursors = iter([cursor, *(additional_cursors or [])])
        self._named_cursors = iter(named_cursors or [])
        self.row_factory = None
        self.row_factories = []
        self.cursor_calls = []
        self.read_only = False
        self.closed = False
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(
        self,
        name="",
        *,
        row_factory=None,
        scrollable=None,
    ):
        self.row_factory = row_factory
        self.row_factories.append(row_factory)
        self.cursor_calls.append(
            {
                "name": name,
                "row_factory": row_factory,
                "scrollable": scrollable,
            }
        )
        if name:
            cursor = next(self._named_cursors, self._cursor)
        else:
            cursor = next(self._cursors)
        cursor.row_factory = row_factory
        return cursor

    def transaction(self):
        return contextlib.nullcontext()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def execute_with_connection(connection, sql, *, config_value=TEST_CONFIG):
    with patch.object(
        server_module,
        "config",
        config_value,
    ), patch.object(server_module, "config_error_msg", None), patch(
        "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
        return_value=connection,
    ):
        return server_module.execute_query(
            sql=sql,
            connection_name="app-db",
        )


class FakeInspector:
    def __init__(self, *, tables=None, views=None, **metadata):
        self.tables = tables or {}
        self.views = views or {}
        self.metadata = metadata
        self.table_name_calls = []
        self.discovery_calls = []
        self.reflection_calls = []

    @staticmethod
    def _key(table_name, schema=None):
        return (schema, table_name)

    def _object_names(self, schema, kind):
        return (self.views if getattr(kind, "name", "TABLE") == "VIEW" else self.tables).get(schema, [])

    def _multi(self, key, schema=None, filter_names=None, kind=None, default=None):
        self.reflection_calls.append((key, schema, list(filter_names or [])))
        names = filter_names or self._object_names(schema, kind)
        object_names = set(self._object_names(schema, kind))
        data = self.metadata.get(key, {})
        return {
            item_key: data.get(item_key, default)
            for name in names
            if (item_key := self._key(name, schema)) in data or name in object_names
        }

    def discover(self, *, schemas, table_refs, include_views, name_prefix, after, limit):
        self.discovery_calls.append({"schemas": schemas, "table_refs": table_refs,
                                     "after": after, "limit": limit})
        refs = [
            {"schema": schema, "name": name, "table_type": kind}
            for objects, kind in [(self.tables, "BASE TABLE"), (self.views if include_views else {}, "VIEW")]
            for schema, names in objects.items() for name in names
        ]
        if table_refs is not None:
            requested = {(ref["schema"], ref["name"]) for ref in table_refs}
            refs = [ref for ref in refs if (ref["schema"], ref["name"]) in requested]
        elif schemas is not None:
            refs = [ref for ref in refs if ref["schema"] in schemas]
        else:
            refs = [ref for ref in refs if ref["schema"] != "information_schema" and not ref["schema"].startswith("pg_")]
        if name_prefix is not None:
            refs = [ref for ref in refs if ref["name"].startswith(name_prefix)]
        refs.sort(key=lambda ref: (ref["schema"].encode(), ref["name"].encode()))
        if after is not None:
            refs = [ref for ref in refs if (ref["schema"].encode(), ref["name"].encode()) > tuple(value.encode() for value in after)]
        return refs[:limit]

    def get_table_names(self, schema=None):
        self.table_name_calls.append(schema)
        return self.tables.get(schema, [])

    def get_view_names(self, schema=None):
        return self.views.get(schema, [])

    def get_multi_table_comment(self, schema=None, filter_names=None, kind=None):
        comments = {key: {"text": value} for key, value in self.metadata.get("comments", {}).items()}
        return self._multi("comments", schema, filter_names, kind, {"text": None}) | comments

    def get_multi_columns(self, schema=None, filter_names=None, kind=None):
        return self._multi("columns", schema, filter_names, kind, [])

    def get_multi_pk_constraint(self, schema=None, filter_names=None, kind=None):
        return self._multi("primary_keys", schema, filter_names, kind, {})

    def get_multi_indexes(self, schema=None, filter_names=None, kind=None):
        return self._multi("indexes", schema, filter_names, kind, [])

    def get_multi_foreign_keys(self, schema=None, filter_names=None, kind=None):
        return self._multi("foreign_keys", schema, filter_names, kind, [])

    def get_multi_unique_constraints(self, schema=None, filter_names=None, kind=None):
        return self._multi("unique_constraints", schema, filter_names, kind, [])

    def get_multi_check_constraints(self, schema=None, filter_names=None, kind=None):
        return self._multi("check_constraints", schema, filter_names, kind, [])


@contextlib.contextmanager
def fake_metadata_inspector_cm(inspector):
    with patch("oracle.oci_postgresql_runtime_mcp_server.inspection._discover_table_refs", side_effect=lambda _inspector, **kwargs: inspector.discover(**kwargs)):
        yield inspector


class TestTools:
    def test_runtime_server_uses_plugin_identity(self):
        assert mcp.name == "oci-postgresql-runtime-mcp-server"

    def test_statement_timeouts_use_fixed_defaults(self):
        cursor = FakeCursor()

        server_module._apply_statement_timeouts(cursor)

        assert cursor.executed == DEFAULT_TIMEOUT_CALLS

    @pytest.mark.parametrize(
        ("reflected_type", "expected"),
        [
            (ARRAY(INTEGER(), dimensions=2), "INTEGER[][]"),
            (ENUM("queued", "done", name="job_state"), "job_state"),
            (DOMAIN("positive_int", INTEGER()), "positive_int"),
            (TIMESTAMP(timezone=True, precision=3), "TIMESTAMP(3) WITH TIME ZONE"),
            (BIT(8), "BIT(8)"),
            (
                INTERVAL(fields="DAY TO SECOND", precision=3),
                "INTERVAL DAY TO SECOND (3)",
            ),
        ],
    )
    def test_jsonable_preserves_postgresql_type_details(
        self,
        reflected_type,
        expected,
    ):
        assert _jsonable({"type": reflected_type}) == {"type": expected}

    def test_load_postgresql_config_from_env(self, monkeypatch, tmp_path):
        config_path = tmp_path / "profiles.json"
        config_path.write_text(
            json.dumps(
                {
                    "connections": {
                        "app-db": {
                            "host": "db.example.oraclecloud.com",
                            "database": "app_db",
                            "user": "app_user",
                            "password": "super-secret",
                            "port": "5432",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setenv("POSTGRESQL_MCP_CONFIG", str(config_path))

        loaded_config = server_module.load_postgresql_config()
        profile = loaded_config["connections"]["app-db"]
        connect_kwargs = profile["connect_kwargs"]

        assert loaded_config["config_path"] == str(config_path)
        assert set(profile) == {"connect_kwargs"}
        assert connect_kwargs["dbname"] == "app_db"
        assert connect_kwargs["user"] == "app_user"
        assert connect_kwargs["port"] == 5432
        assert connect_kwargs["sslmode"] == "verify-full"

    @pytest.mark.asyncio
    async def test_list_connections_returns_configured_profiles(self):
        with patch.object(
            server_module,
            "config",
            {
                "connections": {
                    "app-db": {
                        **TEST_CONFIG["connections"]["app-db"],
                        "hostaddr": "127.0.0.1",
                        "sslmode": "require",
                    }
                },
                "config_path": TEST_CONFIG["config_path"],
            },
        ), patch.object(server_module, "config_error_msg", None):
            async with Client(mcp) as client:
                result = (await client.call_tool("list_connections", {})).data

        assert result["count"] == 1
        assert result["connections"][0]["connection_name"] == "app-db"
        assert result["connections"][0]["database"] == "app_db"
        assert result["connections"][0]["hostaddr"] == "127.0.0.1"
        assert result["connections"][0]["sslmode"] == "require"
        assert result["project"] == "oracle.oci-postgresql-runtime-mcp-server"
        assert result["source_fingerprint"]
        assert result["source_fingerprint_status"] == "not_configured"
        assert result["config_path_loaded"] is True

    def test_runtime_info_reports_source_fingerprint_mismatch(self):
        with patch.object(
            server_module,
            "EXPECTED_SOURCE_FINGERPRINT",
            "expected-fingerprint",
        ):
            result = server_module.get_runtime_info()

        assert result["source_fingerprint"] != "expected-fingerprint"
        assert result["expected_source_fingerprint"] == "expected-fingerprint"
        assert result["source_fingerprint_status"] == "mismatch"
        assert result["source_fingerprint_match"] is False
        assert "source_fingerprint_warning" in result

    def test_load_postgresql_config_preserves_tls_options(self, monkeypatch, tmp_path):
        sslrootcert = tmp_path / "server-ca.pem"
        sslrootcert.write_text("certificate", encoding="utf-8")
        config_path = tmp_path / "profiles.json"
        config_path.write_text(
            json.dumps(
                {
                    "connections": {
                        "app-db": {
                            "host": "db.example.oraclecloud.com",
                            "database": "app_db",
                            "user": "app_user",
                            "password": "super-secret",
                            "port": "5432",
                            "connect_timeout": "7",
                            "sslmode": "verify-full",
                            "sslrootcert": str(sslrootcert),
                            "hostaddr": "127.0.0.1",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setenv("POSTGRESQL_MCP_CONFIG", str(config_path))

        loaded_config = server_module.load_postgresql_config()
        connect_kwargs = loaded_config["connections"]["app-db"]["connect_kwargs"]

        assert connect_kwargs["connect_timeout"] == 7
        assert connect_kwargs["sslmode"] == "verify-full"
        assert connect_kwargs["sslrootcert"] == str(sslrootcert)
        assert connect_kwargs["hostaddr"] == "127.0.0.1"

    @pytest.mark.parametrize(
        "sslmode",
        ["require", "verify-ca", "verify-full"],
    )
    def test_load_postgresql_config_accepts_supported_tls_modes(
        self,
        monkeypatch,
        tmp_path,
        sslmode,
    ):
        profile = load_config_with_overrides(
            monkeypatch,
            tmp_path,
            sslmode=sslmode,
        )["connections"]["app-db"]

        assert profile["connect_kwargs"]["sslmode"] == sslmode

    @pytest.mark.parametrize("sslmode", ["disable", "allow", "prefer", "strict"])
    def test_load_postgresql_config_rejects_unsupported_tls_modes(
        self,
        monkeypatch,
        tmp_path,
        sslmode,
    ):
        with pytest.raises(ValueError, match="sslmode must be one of"):
            load_config_with_overrides(
                monkeypatch,
                tmp_path,
                sslmode=sslmode,
            )

    @pytest.mark.asyncio
    async def test_list_connections_hides_secret_fields(self):
        with patch.object(
            server_module,
            "config",
            {
                "connections": {
                    "app-db": {
                        **TEST_CONFIG["connections"]["app-db"],
                        "sslrootcert": "/tmp/server-ca.pem",
                    }
                },
                "config_path": TEST_CONFIG["config_path"],
            },
        ), patch.object(server_module, "config_error_msg", None):
            async with Client(mcp) as client:
                result = (await client.call_tool("list_connections", {})).data

        connection_summary = result["connections"][0]
        assert "password" not in connection_summary
        assert "sslrootcert" not in connection_summary
        assert connection_summary["sslmode"] == "verify-full"

    @pytest.mark.asyncio
    async def test_test_connection_accepts_connection_name(self):
        cursor = FakeCursor(
            fetchone_result={
                "server_version": "PostgreSQL 16.1",
                "current_user": "app_user",
                "current_database": "app_db",
            }
        )
        fake_connection = FakeConnection(cursor)

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=fake_connection,
        ) as mock_connect:
            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "test_connection",
                        {"connection_name": "app-db"},
                    )
                ).data

        assert result["status"] == "ok"
        assert result["current_database"] == "app_db"
        assert mock_connect.call_args.kwargs["host"] == "db.example.oraclecloud.com"
        assert mock_connect.call_args.kwargs["dbname"] == "app_db"
        assert mock_connect.call_args.kwargs["user"] == "app_user"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("include_system", [False, True])
    async def test_list_schemas_system_schema_filter(self, include_system):
        schema_names = [
            "app",
            "information_schema",
            "pg_catalog",
            "pg_temp_1",
            "pg_toast",
            "pg_toast_temp_1",
            "pgdata",
            "public",
        ]
        expected = schema_names if include_system else ["app", "pgdata", "public"]
        cursor = FakeCursor(fetchmany_result=[{"schema_name": name} for name in expected])

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=FakeConnection(cursor),
        ):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "list_schemas",
                        {
                            "connection_name": "app-db",
                            **({"include_system": True} if include_system else {}),
                        },
                    )
                ).data

        expected = schema_names if include_system else ["app", "pgdata", "public"]
        assert result["count"] == len(expected)
        assert result["schemas"] == expected
        assert "information_schema.schemata" in cursor.executed[2][0]
        assert cursor.executed[2][1]["limit"] == 101

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("visible_schemas", "expected_schemas"),
        [
            ([], []),
            (["information_schema", "pg_catalog", "pg_temp_1", "pg_toast"], []),
            (
                ["app", "audit", "information_schema", "pg_catalog", "pgdata"],
                ["app", "audit", "pgdata"],
            ),
        ],
    )
    async def test_list_tables_discovers_non_system_schemas(
        self, visible_schemas, expected_schemas
    ):
        cursor = FakeCursor(
            fetchall_result=[{"schema_name": name} for name in visible_schemas]
        )
        inspector = FakeInspector(
            tables={name: ["records"] for name in visible_schemas},
            views={name: ["report"] for name in visible_schemas},
        )

        with patch.object(
            server_module, "config", TEST_CONFIG
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=FakeConnection(cursor),
        ), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server._metadata_inspector_cm",
            lambda connect_kwargs: fake_metadata_inspector_cm(inspector),
        ):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool("list_tables", {"connection_name": "app-db"})
                ).data

        assert result["schemas"] == expected_schemas
        assert result["detail"] == "full"
        assert result["count"] == 2 * len(expected_schemas)
        assert [
            (table["table_schema"], table["table_name"]) for table in result["tables"]
        ] == [(schema, name) for schema in expected_schemas for name in ["records", "report"]]
        assert inspector.table_name_calls == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("filter_name", ["schemas", "table_refs"])
    async def test_list_tables_accepts_explicit_system_schemas(self, filter_name):
        table_refs = [
            {"schema": "pg_catalog", "name": "pg_class"},
            {"schema": "information_schema", "name": "tables"},
        ]
        schemas = [ref["schema"] for ref in table_refs]
        inspector = FakeInspector(
            tables={"pg_catalog": ["pg_class"]},
            views={"information_schema": ["tables"]},
        )

        with patch.object(
            server_module, "config", TEST_CONFIG
        ), patch.object(server_module, "config_error_msg", None), patch.object(
            server_module, "_schema_page"
        ) as discovery, patch(
            "oracle.oci_postgresql_runtime_mcp_server.server._metadata_inspector_cm",
            lambda connect_kwargs: fake_metadata_inspector_cm(inspector),
        ):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "list_tables",
                        {
                            "connection_name": "app-db",
                            filter_name: schemas if filter_name == "schemas" else table_refs,
                        },
                    )
                ).data

        discovery.assert_not_called()
        assert result["schemas"] == schemas
        assert result["count"] == 2
        assert [table["table_name"] for table in result["tables"]] == ["tables", "pg_class"]

    def test_list_tables_propagates_schema_discovery_failure(self):
        inspector = FakeInspector()
        inspector.discover = Mock(side_effect=psycopg.OperationalError("schema lookup failed"))
        with patch.object(server_module, "config", TEST_CONFIG), patch.object(
            server_module, "config_error_msg", None
        ), patch.object(server_module, "_metadata_inspector_cm", lambda kwargs: fake_metadata_inspector_cm(inspector)):
            with pytest.raises(psycopg.OperationalError, match="schema lookup failed"):
                server_module.list_tables(connection_name="app-db")
        assert inspector.reflection_calls == []

    @pytest.mark.asyncio
    async def test_list_tables_returns_full_metadata_by_default(self):
        inspector = FakeInspector(
            tables={"public": ["customers"]},
            views={"public": ["orders_view"]},
            comments={
                ("public", "customers"): "Customer accounts",
                ("public", "orders_view"): "Order rollup",
            },
            columns={
                ("public", "customers"): [
                    {
                        "name": "id",
                        "type": "bigint",
                        "nullable": False,
                        "default": None,
                        "comment": "Customer identifier",
                    },
                    {
                        "name": "email",
                        "type": "text",
                        "nullable": False,
                        "default": None,
                        "comment": "Login email",
                    },
                ],
                ("public", "orders_view"): [
                    {
                        "name": "customer_id",
                        "type": "bigint",
                        "nullable": True,
                        "default": None,
                        "comment": None,
                    }
                ],
            },
            primary_keys={
                ("public", "customers"): {
                    "name": "customers_pkey",
                    "constrained_columns": ["id"],
                }
            },
        )

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server._metadata_inspector_cm",
            lambda connect_kwargs: fake_metadata_inspector_cm(inspector),
        ):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "list_tables",
                        {
                            "connection_name": "app-db",
                            "schemas": ["public"],
                            "include_views": True,
                        },
                    )
                ).data

        assert result["schema"] == "public"
        assert result["detail_requested"] == "auto"
        assert result["detail"] == "full"
        assert result["include_views"] is True
        assert result["count"] == 2
        assert result["tables"][0]["table_name"] == "customers"
        assert result["tables"][0]["comment"] == "Customer accounts"
        assert result["tables"][0]["column_count"] == 2
        assert result["tables"][0]["columns"][1]["name"] == "email"
        assert result["tables"][0]["columns"][1]["type"] == "text"
        assert result["tables"][0]["columns"][1]["comment"] == "Login email"
        assert result["tables"][0]["primary_key"]["name"] == "customers_pkey"
        assert inspector.table_name_calls == []

    @pytest.mark.parametrize("detail", ["auto", "full"])
    @pytest.mark.parametrize("objects", ["tables", "views"])
    def test_list_tables_resolves_native_types_in_batches(self, detail, objects):
        class UnsupportedType(TypeEngine):
            __visit_name__ = "unsupported_native_type"

        schema = " app "
        columns = {
            (schema, " documents "): [
                {"name": "id", "type": INTEGER(), "nullable": False},
                {"name": " embedding ", "type": NullType(), "comment": "Embedding"},
            ],
            (schema, "vectors"): [
                {"name": "features", "type": ARRAY(NullType())},
                {"name": "opaque", "type": UnsupportedType()},
            ],
            (schema, "known"): [{"name": "body", "type": "text"}],
        }
        inspector = FakeInspector(
            **{objects: {schema: [" documents ", "vectors", "known"]}},
            columns=columns,
        )
        inspector.bind = Mock()
        connection = Mock()
        inspector.bind.connect.return_value = contextlib.nullcontext(connection)
        connection.execute.return_value = [
            (" documents ", "id", "integer"),
            (" documents ", " embedding ", "vector(3)"),
            ("vectors", "features", "vector(3)[]"),
            ("vectors", "opaque", "app.custom_type"),
        ]

        with patch.object(
            server_module, "config", TEST_CONFIG
        ), patch.object(server_module, "config_error_msg", None), patch.object(
            server_module,
            "_metadata_inspector_cm",
            lambda connect_kwargs: fake_metadata_inspector_cm(inspector),
        ):
            result = server_module.list_tables(
                connection_name="app-db", schemas=[schema], detail=detail
            )

        assert result["detail"] == "full"
        result_columns = {
            table["table_name"]: table["columns"] for table in result["tables"]
        }
        assert result_columns[" documents "] == [
            {"name": "id", "type": "INTEGER", "nullable": False},
            {"name": " embedding ", "type": "vector(3)", "comment": "Embedding"},
        ]
        assert result_columns["vectors"] == [
            {"name": "features", "type": "vector(3)[]"},
            {"name": "opaque", "type": "app.custom_type"},
        ]
        assert result_columns["known"] == [{"name": "body", "type": "text"}]
        connection.execute.assert_called_once()
        statement, params = connection.execute.call_args.args
        assert "pg_catalog.format_type" in str(statement)
        assert "not attribute.attisdropped" in str(statement)
        assert schema not in str(statement)
        assert params == {"schema": schema, "table_names": [" documents ", "vectors"]}
        assert isinstance(columns[(schema, " documents ")][1]["type"], NullType)
        assert isinstance(columns[(schema, "vectors")][0]["type"], ARRAY)

    @pytest.mark.parametrize(
        ("detail", "auto_full_limit"), [("summary", 100), ("auto", 1)]
    )
    def test_list_tables_summary_skips_native_type_lookup(self, detail, auto_full_limit):
        inspector = FakeInspector(
            tables={"public": ["documents", "vectors"]},
            columns={("public", "documents"): [{"name": "value", "type": NullType()}]},
        )
        inspector.bind = Mock()

        with patch.object(
            server_module, "config", TEST_CONFIG
        ), patch.object(server_module, "config_error_msg", None), patch.object(
            server_module,
            "_metadata_inspector_cm",
            lambda connect_kwargs: fake_metadata_inspector_cm(inspector),
        ):
            result = server_module.list_tables(
                connection_name="app-db",
                schemas=["public"],
                detail=detail,
                auto_full_limit=auto_full_limit,
            )

        assert result["detail"] == "summary"
        assert all(table["columns_omitted"] for table in result["tables"])
        inspector.bind.connect.assert_not_called()

    def test_list_tables_known_types_skip_native_type_lookup(self):
        inspector = FakeInspector(
            tables={"public": ["documents"]},
            columns={
                ("public", "documents"): [
                    {"name": "id", "type": INTEGER()},
                    {"name": "values", "type": ARRAY(INTEGER())},
                ]
            },
        )
        inspector.bind = Mock()

        with patch.object(
            server_module, "config", TEST_CONFIG
        ), patch.object(server_module, "config_error_msg", None), patch.object(
            server_module,
            "_metadata_inspector_cm",
            lambda connect_kwargs: fake_metadata_inspector_cm(inspector),
        ):
            result = server_module.list_tables(
                connection_name="app-db", schemas=["public"], detail="full"
            )

        assert result["tables"][0]["columns"] == [
            {"name": "id", "type": "INTEGER"},
            {"name": "values", "type": "INTEGER[]"},
        ]
        inspector.bind.connect.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_tables_auto_summary_when_over_limit(self):
        cursor = FakeCursor(
            fetchall_result=[{"schema_name": "app"}, {"schema_name": "audit"}]
        )
        inspector = FakeInspector(
            tables={"app": ["customers"], "audit": ["orders"]},
            indexes={
                ("audit", "orders"): [
                    {
                        "name": "orders_customer_id_idx",
                        "unique": False,
                        "column_names": ["customer_id"],
                    }
                ]
            },
            foreign_keys={
                ("audit", "orders"): [
                    {
                        "name": "orders_customer_id_fkey",
                        "constrained_columns": ["customer_id"],
                        "referred_schema": "app",
                        "referred_table": "customers",
                        "referred_columns": ["id"],
                    }
                ]
            },
        )

        inspector.bind = Mock()
        connection = Mock()
        inspector.bind.connect.return_value = contextlib.nullcontext(connection)
        connection.execute.return_value = [("orders", "orders_customer_id_fkey", "app")]

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=FakeConnection(cursor),
        ), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server._metadata_inspector_cm",
            lambda connect_kwargs: fake_metadata_inspector_cm(inspector),
        ):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "list_tables",
                        {
                            "connection_name": "app-db",
                            "auto_full_limit": 1,
                        },
                    )
                ).data

        assert result["detail_requested"] == "auto"
        assert result["detail"] == "summary"
        assert result["schemas"] == ["app", "audit"]
        assert result["count"] == 2
        assert result["tables"][0]["columns_omitted"] is True
        assert "columns" not in result["tables"][0]
        assert result["tables"][1]["indexes"][0]["name"] == "orders_customer_id_idx"
        assert result["tables"][1]["foreign_keys"][0]["referred_table"] == "customers"

    @pytest.mark.asyncio
    async def test_list_tables_uses_schema_bind_parameter(self):
        inspector = FakeInspector()
        schema = "app; select now()--"

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server._metadata_inspector_cm",
            lambda connect_kwargs: fake_metadata_inspector_cm(inspector),
        ):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "list_tables",
                        {
                            "connection_name": "app-db",
                            "schemas": [schema],
                        },
                    )
                ).data

        assert result["schema"] == schema
        assert result["count"] == 0
        assert result["detail"] == "full"
        assert inspector.table_name_calls == []

    def test_list_tables_accepts_schema_filters(self):
        inspector = FakeInspector()

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server._metadata_inspector_cm",
            lambda connect_kwargs: fake_metadata_inspector_cm(inspector),
        ):
            result = server_module.list_tables(
                connection_name="app-db",
                schemas=["app", "public", "app"],
                detail="summary",
            )

        assert result["schemas"] == ["app", "public"]
        assert "schema" not in result
        assert result["count"] == 0
        assert inspector.table_name_calls == []

    def test_list_tables_accepts_table_refs(self):
        inspector = FakeInspector(
            tables={
                "app": ["orders", "ignored"],
                "public": ["customers"],
            }
        )
        table_refs = [
            {"schema": "app", "name": "orders"},
            {"schema": "public", "name": "customers"},
        ]

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server._metadata_inspector_cm",
            lambda connect_kwargs: fake_metadata_inspector_cm(inspector),
        ):
            result = server_module.list_tables(
                connection_name="app-db",
                table_refs=table_refs,
                detail="summary",
            )

        assert result["schemas"] == ["app", "public"]
        assert result["table_refs"] == table_refs
        assert "schema" not in result
        assert [table["table_name"] for table in result["tables"]] == [
            "orders",
            "customers",
        ]

    def test_list_tables_preserves_exact_schema_filters(self):
        schemas = [" app ", "app", " "]
        inspector = FakeInspector(tables={schema: ["orders"] for schema in schemas})

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server._metadata_inspector_cm",
            lambda connect_kwargs: fake_metadata_inspector_cm(inspector),
        ):
            result = server_module.list_tables(
                connection_name="app-db",
                schemas=[*schemas, " app ", " "],
                detail="summary",
            )

        assert result["schemas"] == schemas
        assert inspector.table_name_calls == []
        assert [table["table_schema"] for table in result["tables"]] == sorted(schemas)

    @pytest.mark.parametrize("name_key", ["name", "table_name"])
    def test_list_tables_preserves_exact_table_refs(self, name_key):
        table_refs = [
            {"schema": " app ", "name": " orders "},
            {"schema": " app ", "name": "orders"},
            {"schema": "app", "name": "orders"},
            {"schema": " ", "name": " "},
        ]
        inspector = FakeInspector(
            tables={" app ": [" orders ", "orders"], "app": ["orders"], " ": [" "]}
        )
        requested_refs = [
            {"schema": ref["schema"], name_key: ref["name"]}
            for ref in [*table_refs, table_refs[0], table_refs[-1]]
        ]

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server._metadata_inspector_cm",
            lambda connect_kwargs: fake_metadata_inspector_cm(inspector),
        ):
            result = server_module.list_tables(
                connection_name="app-db",
                table_refs=requested_refs,
                detail="summary",
            )

        assert result["schemas"] == [" app ", "app", " "]
        assert result["table_refs"] == table_refs
        assert [
            {"schema": table["table_schema"], "name": table["table_name"]}
            for table in result["tables"]
        ] == sorted(table_refs, key=lambda ref: (ref["schema"], ref["name"]))

    @pytest.mark.parametrize("invalid_identifier", ["", None, 1])
    @pytest.mark.parametrize("field_name", ["schemas", "schema", "name"])
    def test_list_tables_rejects_invalid_identifier_entries(
        self, field_name, invalid_identifier
    ):
        if field_name == "schemas":
            filters = {"schemas": [invalid_identifier]}
        else:
            filters = {
                "table_refs": [
                    {"schema": "app", "name": "orders", field_name: invalid_identifier}
                ]
            }

        with patch.object(
            server_module, "_metadata_inspector_cm"
        ) as inspect_metadata, pytest.raises(ValueError, match="non-empty"):
            server_module.list_tables(connection_name="app-db", **filters)

        inspect_metadata.assert_not_called()

    def test_list_tables_rejects_schemas_and_table_refs_together(self):
        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError, match="mutually exclusive"):
            server_module.list_tables(
                connection_name="app-db",
                schemas=["public"],
                table_refs=[{"schema": "public", "name": "customers"}],
            )

        mock_connect.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_query_truncates_result_sets(self):
        control_cursor = FakeCursor(description=None)
        result_cursor = FakeCursor(
            fetchmany_result=[
                {"id": 1, "name": "Ada"},
                {"id": 2, "name": "Linus"},
                {"id": 3, "name": "Grace"},
            ],
            description=[("id",), ("name",)],
            statusmessage=None,
        )
        fake_connection = FakeConnection(
            control_cursor,
            named_cursors=[result_cursor],
        )

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=fake_connection,
        ):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "execute_query",
                        {
                            "sql": "select id, name from app.users order by id",
                            "connection_name": "app-db",
                            "max_rows": 2,
                        },
                    )
                ).data

        assert result["has_result_set"] is True
        assert result["executed_sql"] == "select id, name from app.users order by id"
        assert result["param_count"] == 0
        assert result["command"] == "SELECT"
        assert result["columns"] == ["id", "name"]
        assert len(result["rows"]) == 2
        assert result["truncated"] is True
        assert result["truncation_reason"] == "max_rows"
        assert result_cursor.fetchmany_sizes == [3]
        assert result_cursor.exit_count == 1

    def test_execute_query_does_not_truncate_exact_max_rows(self):
        cursor = FakeCursor(
            fetchmany_result=[(1,), (2,)],
            description=[("id",)],
        )

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=FakeConnection(cursor),
        ):
            result = server_module.execute_query(
                sql="select id from app.users",
                connection_name="app-db",
                max_rows=2,
            )

        assert result["row_count"] == 2
        assert result["truncated"] is False
        assert cursor.fetchmany_sizes == [3]

    @pytest.mark.parametrize("max_rows", [0, server_module._MAX_RESULT_ROWS + 1])
    def test_execute_query_rejects_out_of_range_max_rows(self, max_rows):
        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError, match="max_rows must be between"):
            server_module.execute_query(
                sql="select 1",
                connection_name="app-db",
                max_rows=max_rows,
            )

        mock_connect.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_query_schema_advertises_max_rows_bounds(self):
        async with Client(mcp) as client:
            tools = {tool.name: tool for tool in await client.list_tools()}
        max_rows_schema = tools["execute_query"].inputSchema["properties"]["max_rows"]

        assert max_rows_schema["minimum"] == 1
        assert server_module._MAX_RESULT_ROWS == 10_000
        assert max_rows_schema["maximum"] == server_module._MAX_RESULT_ROWS

    def test_execute_query_bounds_returned_row_bytes(self):
        first_row = {"value": "fits"}
        cursor = FakeCursor(
            fetchmany_result=[first_row, {"value": "does not fit"}],
            description=[("value",)],
        )

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch.object(
            server_module,
            "_MAX_RESULT_BYTES",
            len(server_module.to_json(first_row)),
        ), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=FakeConnection(cursor),
        ):
            result = server_module.execute_query(
                sql="select value from app.values",
                connection_name="app-db",
            )

        assert result["rows"] == [first_row]
        assert result["truncated"] is True
        assert result["truncation_reason"] == "max_result_bytes"
        assert cursor.fetchmany_sizes == [server_module._DEFAULT_MAX_ROWS + 1]

    def test_execute_query_serializes_psycopg_range(self):
        cursor = FakeCursor(
            fetchmany_result=[(7, Range(1, 3))],
            description=[("id",), ("window",)],
        )

        result = execute_with_connection(
            FakeConnection(cursor),
            "select id, availability_window as window from app.resources",
        )

        assert result["rows"] == [{"id": 7, "window": "[1, 3)"}]

    def test_execute_query_base64_encodes_non_utf8_bytea(self):
        cursor = FakeCursor(
            fetchmany_result=[(7, b"\xff\x00")],
            description=[("id",), ("payload",)],
        )

        result = execute_with_connection(
            FakeConnection(cursor),
            "select id, payload from app.binary_values",
        )

        assert result["rows"] == [{"id": 7, "payload": "_wA="}]

    @pytest.mark.asyncio
    async def test_execute_query_serializes_non_finite_floats_consistently(
        self,
    ):
        cursor = FakeCursor(
            fetchmany_result=[(float("nan"), float("inf"), float("-inf"), None)],
            description=[
                ("nan_value",),
                ("positive_infinity",),
                ("negative_infinity",),
                ("null_value",),
            ],
        )

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=FakeConnection(cursor),
        ):
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "execute_query",
                    {
                        "sql": "select 'NaN'::float8, 'Infinity'::float8, "
                        "'-Infinity'::float8, null",
                        "connection_name": "app-db",
                    },
                )

        expected_rows = [
            {
                "nan_value": "NaN",
                "positive_infinity": "Infinity",
                "negative_infinity": "-Infinity",
                "null_value": None,
            }
        ]
        assert result.data["rows"] == expected_rows
        assert result.structured_content == result.data
        text_result = json.loads(
            result.content[0].text,
            parse_constant=lambda value: pytest.fail(
                f"non-standard JSON constant in tool response: {value}"
            ),
        )
        assert text_result == result.data

    def test_multi_statement_results_share_returned_row_byte_budget(self):
        class MultiResultCursor(FakeCursor):
            def __init__(self, result_sets):
                super().__init__(description=[("value",)])
                self.result_sets = list(result_sets)

            def execute(self, sql, params=None):
                super().execute(sql, params)
                if not sql.startswith("set "):
                    self.fetchmany_result = list(self.result_sets.pop(0))

        first_row = {"value": "first"}
        cursor = MultiResultCursor([[first_row], [{"value": "second"}]])
        fake_connection = FakeConnection(cursor)

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch.object(
            server_module,
            "_MAX_RESULT_BYTES",
            len(server_module.to_json(first_row)),
        ), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=fake_connection,
        ):
            result = server_module.execute_query(
                sql="select 'first' as value; select 'second' as value",
                connection_name="app-db",
            )

        assert result["statements"][0]["rows"] == [first_row]
        assert result["statements"][1]["rows"] == []
        assert result["statements"][1]["truncation_reason"] == "max_result_bytes"
        assert [call["name"] for call in fake_connection.cursor_calls] == [
            "",
            "_odsp_mcp_result_1",
            "_odsp_mcp_result_2",
        ]

    def test_multi_statement_uses_server_cursor_only_for_select(self):
        control_cursor = FakeCursor(
            description=None,
            rowcount=1,
            statusmessage="UPDATE 1",
        )
        result_cursor = FakeCursor(
            fetchmany_result=[(7,)],
            description=[("id",)],
            statusmessage=None,
        )
        fake_connection = FakeConnection(
            control_cursor,
            named_cursors=[result_cursor],
        )

        result = execute_with_connection(
            fake_connection,
            "select id from app.users; show search_path",
            config_value=TEST_CONFIG,
        )

        assert result["statements"][0]["rows"] == [{"id": 7}]
        assert result["statements"][0]["command"] == "SELECT"
        assert result["statements"][1]["has_result_set"] is False
        assert result_cursor.executed == [("select id from app.users", None)]
        assert control_cursor.executed == [
            *DEFAULT_TIMEOUT_CALLS,
            *DEFAULT_TIMEOUT_CALLS,
            ("show search_path", None),
        ]
        assert [call["name"] for call in fake_connection.cursor_calls] == [
            "",
            "_odsp_mcp_result_1",
        ]
        assert fake_connection.committed is False

    @pytest.mark.parametrize(
        (
            "sql",
            "labels",
            "origins",
            "catalog_rows",
            "values",
            "expected_columns",
        ),
        [
            pytest.param(
                "select users.id, orders.id from app.users join app.orders using (id)",
                ["id", "id"],
                [(100, 1), (200, 1)],
                [(100, 1, "users", "id"), (200, 1, "orders", "id")],
                (1, 2),
                ["users.id", "orders.id"],
                id="distinct origins",
            ),
            pytest.param(
                "select manager.id, employee.id from app.users manager "
                "join app.users employee on manager.id = employee.id",
                ["id", "id"],
                [(100, 1), (100, 1)],
                [(100, 1, "users", "id")],
                (1, 2),
                ["users.id", "users.id_2"],
                id="repeated origin",
            ),
            pytest.param(
                "select count(*), count(id) from app.users",
                ["count", "count"],
                [(0, 0), (0, 0)],
                None,
                (2, 3),
                ["count", "count_2"],
                id="unresolved origins",
            ),
        ],
    )
    def test_execute_query_makes_duplicate_columns_unique(
        self,
        sql,
        labels,
        origins,
        catalog_rows,
        values,
        expected_columns,
    ):
        cursor = FakeCursor(
            fetchmany_result=[values],
            description=[(label,) for label in labels],
            pgresult=FakePGResult(origins),
        )
        catalog_cursors = (
            [FakeCursor(fetchall_result=catalog_rows)] if catalog_rows else []
        )
        fake_connection = FakeConnection(
            FakeCursor(description=None),
            additional_cursors=catalog_cursors,
            named_cursors=[cursor],
        )

        result = execute_with_connection(fake_connection, sql)

        assert result["columns"] == expected_columns
        assert result["rows"] == [dict(zip(expected_columns, values, strict=True))]
        assert fake_connection.cursor_calls[1]["name"] == "_odsp_mcp_result_1"
        assert fake_connection.rolled_back is True
        assert fake_connection.committed is False

    def test_column_origin_lookup_propagates_operational_errors(self):
        fake_connection = FakeConnection(
            FakeCursor(execute_error=psycopg.OperationalError("connection lost"))
        )

        with pytest.raises(psycopg.OperationalError, match="connection lost"):
            server_module._resolve_column_origins(fake_connection, [(100, 1)])

    def test_origin_lookup_failure_does_not_stop_later_statements(self):
        class MultiResultCursor(FakeCursor):
            def execute(self, sql, params=None):
                super().execute(sql, params)
                if sql.startswith("set "):
                    return
                if sql.startswith("show search_path"):
                    self.description = [("id",), ("id",)]
                    self.pgresult = FakePGResult([(100, 1), (100, 1)])
                    self.fetchmany_result = [(1, 1)]
                else:
                    self.description = None
                    self.pgresult = None
                    self.rowcount = 1

        cursor = MultiResultCursor()
        fake_connection = FakeConnection(
            cursor,
            additional_cursors=[
                FakeCursor(
                    execute_error=psycopg.ProgrammingError("catalog lookup failed")
                )
            ],
        )
        sql = "show search_path; show server_version"

        result = execute_with_connection(
            fake_connection,
            sql,
            config_value=TEST_CONFIG,
        )

        assert result["statements"][0]["columns"] == ["id", "id_2"]
        assert result["statements"][0]["rows"] == [{"id": 1, "id_2": 1}]
        assert result["statements"][1]["has_result_set"] is False
        assert cursor.executed == [
            *DEFAULT_TIMEOUT_CALLS,
            ("show search_path", None),
            *DEFAULT_TIMEOUT_CALLS,
            ("show server_version", None),
        ]
        assert fake_connection.committed is False
        assert fake_connection.rolled_back is True

    def test_execute_query_suffixes_without_reusing_existing_labels(self):
        cursor = FakeCursor(
            fetchmany_result=[(1, 2, 3)],
            description=[("id",), ("id",), ("id_2",)],
            pgresult=FakePGResult([(0, 0), (0, 0), (0, 0)]),
        )

        result = execute_with_connection(
            FakeConnection(cursor),
            "select id, id, id as id_2 from app.users",
        )

        assert result["columns"] == ["id", "id_3", "id_2"]
        assert result["rows"] == [{"id": 1, "id_3": 2, "id_2": 3}]

    def test_execute_query_preserves_uniquely_aliased_columns(self):
        row = {"user_id": 1, "order_id": 2}
        cursor = FakeCursor(
            fetchmany_result=[row],
            description=[("user_id",), ("order_id",)],
        )

        result = execute_with_connection(
            FakeConnection(cursor),
            "select users.id as user_id, orders.id as order_id "
            "from app.users join app.orders using (id)",
        )

        assert result["columns"] == ["user_id", "order_id"]
        assert result["rows"] == [row]

    @pytest.mark.asyncio
    async def test_runtime_smoke_sequence_uses_named_profile(self):
        connection_cursor = FakeCursor(
            fetchone_result={
                "server_version": "PostgreSQL 17.6 OCI Optimized, 64-bit",
                "current_user": "app_user",
                "current_database": "app_db",
            }
        )
        schemas_cursor = FakeCursor(fetchmany_result=[{"schema_name": "public"}])
        query_cursor = FakeCursor(
            fetchmany_result=[
                {
                    "database_name": "app_db",
                    "user_name": "app_user",
                    "server_ip": "<private-ip>",
                }
            ],
            description=[("database_name",), ("user_name",), ("server_ip",)],
        )

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            side_effect=[
                FakeConnection(connection_cursor),
                FakeConnection(schemas_cursor),
                FakeConnection(query_cursor),
            ],
        ) as mock_connect:
            async with Client(mcp) as client:
                connection_result = (
                    await client.call_tool(
                        "test_connection",
                        {"connection_name": "app-db"},
                    )
                ).data
                schemas_result = (
                    await client.call_tool(
                        "list_schemas",
                        {"connection_name": "app-db"},
                    )
                ).data
                query_result = (
                    await client.call_tool(
                        "execute_query",
                        {
                            "connection_name": "app-db",
                            "sql": "select current_database() as database_name",
                            "max_rows": 5,
                        },
                    )
                ).data

        assert connection_result["status"] == "ok"
        assert schemas_result["schemas"] == ["public"]
        assert query_result["rows"][0]["server_ip"] == "<private-ip>"
        assert mock_connect.call_count == 3
        assert all(
            call.kwargs["application_name"] == "oracle.oci-postgresql-runtime-mcp-server"
            for call in mock_connect.call_args_list
        )

    @pytest.mark.asyncio
    async def test_execute_query_reports_param_count_without_values(self):
        cursor = FakeCursor(
            fetchmany_result=[
                {"id": 1, "name": "Ada"},
            ],
            description=[("id",), ("name",)],
        )

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=FakeConnection(cursor),
        ):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "execute_query",
                        {
                            "sql": "select id, name from app.users where token = %s",
                            "connection_name": "app-db",
                            "params": ["secret-token"],
                        },
                    )
                ).data

        assert result["executed_sql"] == "select id, name from app.users where token = %s"
        assert result["param_count"] == 1
        assert result["params_redacted"] is True
        assert "secret-token" not in json.dumps(result)

    @pytest.mark.parametrize(
        ("sql", "expected"),
        [
            ("select 1", True),
            ("values (1)", True),
            ("with item as (select 1) select * from item", True),
            ("show search_path", False),
            ("explain select 1", False),
        ],
    )
    def test_prepared_statement_marks_server_cursor_compatibility(
        self,
        sql,
        expected,
    ):
        statement = _prepare_sql_execution(sql, None)[0]

        assert statement.server_cursor_compatible is expected

    def test_read_only_uses_read_only_transaction_and_rolls_back(self):
        control_cursor = FakeCursor(description=None)
        result_cursor = FakeCursor(
            fetchmany_result=[{"id": 1}],
            description=[("id",)],
            statusmessage=None,
        )
        fake_connection = FakeConnection(
            control_cursor,
            named_cursors=[result_cursor],
        )

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=fake_connection,
        ):
            result = server_module.execute_query(
                sql="select id from app.users where c1 = %s and c2 = %s;",
                connection_name="app-db",
                params=[1, 2],
            )

        assert fake_connection.read_only is True
        assert result["has_result_set"] is True
        assert "query_policy" not in result
        assert result["param_count"] == 2
        assert result["command"] == "SELECT"
        assert control_cursor.executed == [
            *DEFAULT_TIMEOUT_CALLS,
        ]
        assert result_cursor.executed == [
            ("select id from app.users where c1 = %s and c2 = %s", [1, 2]),
        ]
        assert [call["name"] for call in fake_connection.cursor_calls] == [
            "",
            "_odsp_mcp_result_1",
        ]
        assert fake_connection.cursor_calls[1]["scrollable"] is False
        assert fake_connection.rolled_back is True
        assert fake_connection.committed is False

    @pytest.mark.parametrize(
        "sql",
        [
            "set transaction read write",
            "set transaction_read_only = off",
            "begin read write",
            "commit",
            "end",
            "rollback",
            "set transaction read write; insert into app.users(id) values (1); commit",
            "select 1; set transaction read write; insert into app.users(id) values (1); commit",
        ],
    )
    def test_rejects_read_only_overrides_and_transaction_control_before_connect(self, sql):
        # Driver read_only can be overridden by SQL; rollback cannot undo SQL COMMIT.
        with patch.object(server_module, "config", TEST_CONFIG), patch.object(
            server_module, "config_error_msg", None
        ), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError):
            server_module.execute_query(sql=sql, connection_name="app-db")

        mock_connect.assert_not_called()

    @pytest.mark.parametrize(
        ("sql", "statement_kind", "value"),
        [
            ("show search_path", "read", '"$user", public'),
            ("explain select 1", "read", "Result"),
        ],
    )
    def test_non_select_result_statements_use_normal_cursor(
        self,
        sql,
        statement_kind,
        value,
    ):
        cursor = FakeCursor(
            fetchmany_result=[(value,)],
            description=[("value",)],
        )
        fake_connection = FakeConnection(cursor)

        result = execute_with_connection(
            fake_connection,
            sql,
            config_value=TEST_CONFIG,
        )

        assert result["rows"] == [{"value": value}]
        assert result["statement_kind"] == statement_kind
        assert [call["name"] for call in fake_connection.cursor_calls] == [""]

    def test_read_only_allows_leading_comments(self):
        cursor = FakeCursor(
            fetchmany_result=[{"id": 1}],
            description=[("id",)],
        )
        fake_connection = FakeConnection(cursor)
        sql = (
            "-- leading ; comment\n"
            "/* block ; comment */\n"
            "select id from app.users where id = %s;"
        )

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=fake_connection,
        ):
            result = server_module.execute_query(
                sql=sql,
                connection_name="app-db",
                params=[1],
            )

        assert result["has_result_set"] is True
        assert "has_multiple_statements" not in result
        assert result["executed_sql"] == sql
        assert cursor.executed == [
            *DEFAULT_TIMEOUT_CALLS,
            (
                "-- leading ; comment\n/* block ; comment */\nselect id from app.users where id = %s",
                [1],
            ),
        ]
        assert fake_connection.rolled_back is True

    @pytest.mark.parametrize(
        "sql",
        [
            "insert into app.users(id) values (1)",
            "update app.users set active = false",
            "create table app.orders (id bigint)",
            "alter table app.users add column flag boolean",
            "delete from app.users",
            "drop table app.users",
            "grant select on app.users to reporting",
            "revoke select on app.users from reporting",
            "explain analyze select id from app.users",
            "select id from app.users for update",
            "select 1 into app.mcp_bypass",
        ],
    )
    def test_read_only_rejects_mutating_and_privilege_sql_before_connect(self, sql):
        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError):
            server_module.execute_query(sql=sql, connection_name="app-db")

        mock_connect.assert_not_called()

    def test_nested_locking_selects_are_blocked_before_connect(self):
        config = TEST_CONFIG

        with patch.object(
            server_module,
            "config",
            config,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError):
            server_module.execute_query(
                sql="select * from (select * from app.users for update) locked_users",
                connection_name="app-db",
            )

        mock_connect.assert_not_called()

    def test_parse_errors_happen_before_connect(self):
        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError, match="SQL could not be parsed"):
            server_module.execute_query(
                sql="select from",
                connection_name="app-db",
            )

        mock_connect.assert_not_called()

    @pytest.mark.parametrize(
        ("sql", "params"),
        [
            ("select 'C:\\'::text, %s::int", [42]),
            ("select '%s', E'%b', $tag$%t$tag$, %s -- %s", [1, 2, 3, 4, 5]),
            ("select '100%%'::text, %s::int", [42]),
            ("select %s, %b, %t", [1, 2, 3]),
            ("select 10 %\n 3, %s::int", [42]),
            ("select %", []),
        ],
    )
    def test_placeholder_replacement_matches_psycopg(self, sql, params):
        psycopg_query = PostgresQuery(Transformer())
        psycopg_query.convert(sql, params)

        assert _replace_psycopg_placeholders(sql).encode() == psycopg_query.query

    @pytest.mark.parametrize(
        "sql",
        [
            "select %d",
            "select %(value)s",
        ],
    )
    def test_placeholder_replacement_rejects_unsupported_sequences(self, sql):
        with pytest.raises(ValueError, match="placeholder"):
            _replace_psycopg_placeholders(sql)

    def test_standard_string_backslash_does_not_hide_following_bind(self):
        cursor = FakeCursor(
            fetchmany_result=[{"path": "C:\\", "value": 42}],
            description=[("path",), ("value",)],
        )
        fake_connection = FakeConnection(cursor)
        sql = "select 'C:\\'::text as path, %s::int as value"

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=fake_connection,
        ):
            result = server_module.execute_query(
                sql=sql,
                connection_name="app-db",
                params=[42],
            )

        assert result["rows"] == [{"path": "C:\\", "value": 42}]
        assert cursor.executed == [
            *DEFAULT_TIMEOUT_CALLS,
            (sql, [42]),
        ]
        assert fake_connection.rolled_back is True

    def test_select_permits_operator_adjacent_params(self):
        cursor = FakeCursor(description=None, rowcount=1, statusmessage="OK")
        fake_connection = FakeConnection(cursor)
        sql = "select id from app.users where active=%s and id=%s"

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=fake_connection,
        ):
            result = server_module.execute_query(
                sql=sql,
                connection_name="app-db",
                params=[False, 42],
            )

        assert result["param_count"] == 2
        assert cursor.executed == [
            *DEFAULT_TIMEOUT_CALLS,
            (sql, [False, 42]),
        ]
        assert fake_connection.committed is False

    @pytest.mark.parametrize(
        "sql",
        [
            "insert into app.users(id) values (1)",
            "insert into app.audit_events(actor_id, event_name) select id, 'created' from app.users where active = true",
            "insert into app.inventory(code, label) values ('part-7', 'Valve') on conflict (code) do update set label = excluded.label",
            "update app.users set active = false",
            "update app.jobs set state = 'done' where id in (select job_id from app.ready_jobs) returning id",
        ],
    )
    def test_rejects_insert_and_update(self, sql):
        with patch.object(server_module, "config", TEST_CONFIG), patch.object(
            server_module, "config_error_msg", None
        ), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError):
            server_module.execute_query(sql=sql, connection_name="app-db")

        mock_connect.assert_not_called()

    @pytest.mark.parametrize(
        "sql",
        [
            "delete from app.users",
            "drop table app.users",
            "create table app.orders (id bigint)",
            "grant select on app.users to reporting",
            "revoke select on app.users from reporting",
            "select 1 into app.mcp_bypass",
            "with updated as (update app.users set active = false returning id) select id from updated",
        ],
    )
    def test_blocks_delete_ddl_and_privilege_sql_before_connect(self, sql):
        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError):
            server_module.execute_query(sql=sql, connection_name="app-db")

        mock_connect.assert_not_called()

    @pytest.mark.parametrize(
        "sql",
        [
            "create table app.orders (id bigint primary key)",
            "create index idx_orders_created_at on app.orders(created_at)",
            "create sequence app.ticket_seq start 200 increment 10",
            "create type app.job_state as enum ('queued', 'running')",
            "create domain app.email as text check (value like '%@%')",
            "create view app.enabled_accounts as select id from app.accounts where enabled = true",
            "create materialized view app.daily_totals as select id from app.metrics",
            "create schema reporting create table snapshots (id bigint)",
            "alter table app.orders add column note text",
            "alter table app.orders alter column state set default 'pending'",
            "alter table app.orders alter column account_id set not null",
            "alter table app.orders add constraint positive_total check (total >= 0) not valid",
            "alter table app.orders validate constraint positive_total",
            "alter table app.orders alter column id add generated always as identity",
            "alter table app.accounts rename column displayname to display_name",
        ],
    )
    def test_rejects_selected_create_and_alter(self, sql):
        with patch.object(server_module, "config", TEST_CONFIG), patch.object(
            server_module, "config_error_msg", None
        ), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError):
            server_module.execute_query(sql=sql, connection_name="app-db")

        mock_connect.assert_not_called()

    @pytest.mark.parametrize(
        "sql",
        [
            "delete from app.users",
            "drop table app.users",
            "grant select on app.users to reporting",
            "revoke select on app.users from reporting",
            "truncate table app.users",
            "merge into app.users u using app.staging_users s on u.id = s.id when matched then update set name = s.name",
            "call app.refresh_stats()",
            "do $$ begin null; end $$",
            "copy app.users to stdout",
            "create function app.f() returns integer language sql as $$ select 1 $$",
            "create procedure app.cleanup_old_data() language plpgsql as $$ begin null; end; $$",
            "create function app.delete_everything() returns void language sql as $$ delete from app.users $$",
            "create or replace procedure app.delete_everything() language plpgsql as $$ begin delete from app.users; end $$",
            "create schema hack create trigger audit_user_update after update on app.users execute function app.audit_user_update()",
            "create role app_admin login",
            "create user report_loader",
            "create extension if not exists hstore",
            "alter extension hstore update",
            "comment on table app.users is 'users'",
            "security label for selinux on table app.users is 'system_u:object_r:sepgsql_data_t:s0'",
            "vacuum app.users",
            "analyze app.users",
            "reindex table app.users",
            "create aggregate app.int_accumulate (sfunc = int4pl, basetype = int, stype = int)",
            "alter system set shared_buffers = '512MB'",
            "alter table app.users drop column name",
            "alter table app.users alter column name drop default",
            "alter table app.users set schema reporting",
            "alter type app.user_type add attribute legacy_name text",
            "alter table app.users disable row level security",
            "alter table app.users disable trigger all",
            "alter table app.users set unlogged",
            "alter domain app.email drop constraint valid_email",
            "prepare p as delete from app.users",
            "prepare p(int) as update app.users set active = false where id = $1",
            "execute p(1)",
        ],
    )
    def test_blocks_destructive_privilege_and_admin_sql(self, sql):
        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError):
            server_module.execute_query(sql=sql, connection_name="app-db")

        mock_connect.assert_not_called()

    @pytest.mark.parametrize(
        "sql",
        [
            "create function app.delete_everything() returns void language sql as $$ delete from app.users $$",
            "create procedure app.delete_everything() language sql as $$ delete from app.users $$",
            "call app.delete_everything()",
            "prepare p as delete from app.users",
            "prepare p(int) as update app.users set active = false where id = $1",
            "execute p(1)",
        ],
    )
    def test_blocks_stored_code_and_sql_prepared_statements_before_connect(
        self,
        sql,
    ):
        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError):
            server_module.execute_query(sql=sql, connection_name="app-db")

        mock_connect.assert_not_called()

    @pytest.mark.parametrize(
        "sql",
        [
            "select pg_sleep(1)",
            "select pg_catalog.pg_sleep(1)",
            "select pg_sleep_for(interval '1 second')",
            "select pg_sleep_until(now())",
            "select sleep(1)",
        ],
    )
    def test_blocks_sleep_functions_before_connect(self, sql):
        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError, match="blocked sleep functions"):
            server_module.execute_query(sql=sql, connection_name="app-db")

        mock_connect.assert_not_called()

    def test_select_function_calls_are_classified_as_reads(
        self,
    ):
        statement = _prepare_sql_execution(
            "select app.delete_everything()",
            None,
        )[0]

        assert statement.kind == "read"

    def test_multi_statement_sql_executes_sequentially_with_nested_params(self):
        cursor = FakeCursor(description=None, rowcount=1, statusmessage="OK")
        fake_connection = FakeConnection(cursor)
        sql = """
            select 'keeps ; inside string';
            -- this comment has a ; too
            select %s as name, %s as id;
        """

        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect",
            return_value=fake_connection,
        ):
            result = server_module.execute_query(
                sql=sql,
                connection_name="app-db",
                params=[[], ["Ada", 42]],
            )

        assert result["has_multiple_statements"] is True
        assert result["statement_count"] == 2
        assert result["param_count"] == 2
        assert cursor.executed == [
            *DEFAULT_TIMEOUT_CALLS,
            ("select 'keeps ; inside string'", []),
            *DEFAULT_TIMEOUT_CALLS,
            (
                "-- this comment has a ; too\n            select %s as name, %s as id",
                ["Ada", 42],
            ),
        ]
        assert fake_connection.committed is False

    def test_multi_statement_validation_happens_before_execution(self):
        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError, match="DropStmt"):
            server_module.execute_query(
                sql="select 1; drop table app.users",
                connection_name="app-db",
                params=[[], []],
            )

        mock_connect.assert_not_called()

    def test_multi_statement_requires_nested_params(self):
        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError, match="each params item must be a list"):
            server_module.execute_query(
                sql="select %s; select %s",
                connection_name="app-db",
                params=[1, 1],
            )

        mock_connect.assert_not_called()

    def test_parameterized_ddl_is_rejected(self):
        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError, match="not allowed|could not be parsed"):
            server_module.execute_query(
                sql="create table app.%s (id bigint)",
                connection_name="app-db",
                params=["orders"],
            )

        mock_connect.assert_not_called()

    def test_parameterized_select_into_is_rejected(self):
        with patch.object(
            server_module,
            "config",
            TEST_CONFIG,
        ), patch.object(server_module, "config_error_msg", None), patch(
            "oracle.oci_postgresql_runtime_mcp_server.server.psycopg.connect"
        ) as mock_connect, pytest.raises(ValueError, match="not allowed|could not be parsed"):
            server_module.execute_query(
                sql="select %s into app.created_from_param",
                connection_name="app-db",
                params=["payload"],
            )

        mock_connect.assert_not_called()


@pytest.mark.asyncio
async def test_runtime_tool_contract():
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    assert set(tools) == {
        "get_runtime_info",
        "list_connections",
        "test_connection",
        "list_schemas",
        "list_tables",
        "execute_query",
    }
    properties = tools["list_tables"].inputSchema["properties"]
    assert "schema" not in properties
    assert "schemas" in properties
    assert "table_refs" in properties


def test_metadata_connection_sets_driver_read_only_before_inspection():
    from unittest.mock import Mock
    import oracle.oci_postgresql_runtime_mcp_server.inspection as inspection

    conn = Mock(read_only=False)
    engine = Mock()

    def create_engine(url, *, creator):
        assert creator() is conn
        assert conn.read_only is True
        return engine

    with patch.object(inspection.psycopg, "connect", return_value=conn), patch.object(
        inspection, "create_engine", side_effect=create_engine
    ), patch.object(inspection.event, "listen"), patch.object(inspection, "inspect_database", return_value="inspector"):
        with inspection._metadata_inspector_cm({"host": "synthetic"}) as inspector:
            assert inspector == "inspector"
    engine.dispose.assert_called_once()


def test_foreign_key_schemas_are_batched_and_preserve_other_metadata():
    from oracle.oci_postgresql_runtime_mcp_server import inspection

    inspector = Mock()
    connection = Mock()
    inspector.bind.connect.return_value = contextlib.nullcontext(connection)
    connection.execute.return_value = [
        (" orders ", "same_name", "public"),
        ("other", "same_name", " shared "),
    ]
    foreign_key = {"name": "same_name", "referred_schema": None,
                   "referred_table": "parents", "constrained_columns": ["a", "b"],
                   "referred_columns": ["x", "y"], "options": {"ondelete": "CASCADE"}}
    reflected = {(" app ", " orders "): [foreign_key],
                 (" app ", "other"): [{**foreign_key, "referred_schema": "wrong"}],
                 (" app ", "no_fk"): []}
    result = inspection._resolve_foreign_key_schemas(inspector, " app ", reflected)
    assert result == {
        (" app ", " orders "): [{**foreign_key, "referred_schema": "public"}],
        (" app ", "other"): [{**foreign_key, "referred_schema": " shared "}],
        (" app ", "no_fk"): [],
    }
    assert reflected[(" app ", " orders ")][0]["referred_schema"] is None
    connection.execute.assert_called_once()
    statement, params = connection.execute.call_args.args
    assert params == {"schema": " app ", "table_names": [" orders ", "other"]}
    assert " app " not in str(statement)


@pytest.mark.parametrize("foreign_keys", [{}, {("app", "orders"): []}])
def test_foreign_key_schema_lookup_skipped_without_foreign_keys(foreign_keys):
    from oracle.oci_postgresql_runtime_mcp_server import inspection

    inspector = Mock()
    assert inspection._resolve_foreign_key_schemas(inspector, "app", foreign_keys) == foreign_keys
    inspector.bind.connect.assert_not_called()
