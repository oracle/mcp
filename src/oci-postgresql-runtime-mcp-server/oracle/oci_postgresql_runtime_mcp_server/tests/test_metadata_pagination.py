"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import contextlib
from unittest.mock import Mock

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from pydantic_core import to_json

from oracle.oci_postgresql_runtime_mcp_server import inspection, pagination, server
from oracle.oci_postgresql_runtime_mcp_server.tests.test_postgresql_tools import (
    FakeConnection, FakeCursor, FakeInspector, TEST_CONFIG, fake_metadata_inspector_cm,
)


@pytest.fixture
def catalog(monkeypatch):
    inspector = FakeInspector()
    monkeypatch.setattr(server, "config", TEST_CONFIG)
    monkeypatch.setattr(server, "config_error_msg", None)
    monkeypatch.setattr(server, "_metadata_inspector_cm", lambda kwargs: fake_metadata_inspector_cm(inspector))
    return inspector


def table_keys(result):
    return [(table["table_schema"], table["table_name"]) for table in result["tables"]]


def test_default_page_does_not_reflect_off_page_catalog_objects(catalog):
    catalog.tables = {"app": [f"table_{index:05}" for index in range(10_000)]}
    result = server.list_tables("app-db")
    assert result["count"] == 100
    assert result["has_more"] is True
    assert result["detail"] == "summary"
    assert result["next_cursor"] == ["app", "table_00099"]
    assert result["truncation_reason"] == "limit"
    assert [call["limit"] for call in catalog.discovery_calls] == [101]
    expected = {f"table_{index:05}" for index in range(100)}
    assert all(set(names) == expected for _, _, names in catalog.reflection_calls)
    assert catalog.table_name_calls == []


def test_pages_cross_schema_and_view_boundaries_without_skips(catalog):
    catalog.tables = {"z": ["last"], "app": ["b", "a"], " app ": [" quoted "]}
    catalog.views = {"app": ["ab_view"]}
    expected = [(" app ", " quoted "), ("app", "a"), ("app", "ab_view"), ("app", "b"), ("z", "last")]
    cursor = None
    seen = []
    while True:
        result = server.list_tables("app-db", limit=2, cursor=cursor, detail="summary")
        seen.extend(table_keys(result))
        assert result["schemas"] == list(dict.fromkeys(schema for schema, _ in table_keys(result)))
        if not result["has_more"]:
            assert result["next_cursor"] is None
            break
        assert result["next_cursor"] == list(seen[-1])
        cursor = result["next_cursor"]
    assert seen == expected


@pytest.mark.parametrize("detail,expected", [("auto", "summary"), ("summary", "summary"), ("full", "full")])
def test_auto_uses_entire_filtered_scope_even_on_final_short_page(catalog, detail, expected):
    catalog.tables = {"app": ["a", "b", "c"]}
    first = server.list_tables("app-db", schemas=["app"], limit=2, auto_full_limit=2, detail=detail)
    final = server.list_tables("app-db", schemas=["app"], limit=2, auto_full_limit=2, detail=detail, cursor=first["next_cursor"])
    assert final["count"] == 1
    assert final["detail"] == expected
    assert ("columns" in final["tables"][0]) == (expected == "full")
    if detail == "auto":
        assert catalog.discovery_calls[-1]["after"] is None
        assert catalog.discovery_calls[-1]["limit"] == 3


def test_exact_table_filters_are_preserved(catalog):
    catalog.tables = {" app ": ["%_a", "%_b", "other"], "other": ["%_a"]}
    refs = [{"schema": " app ", "name": name} for name in ("%_a", "%_b")]
    first = server.list_tables("app-db", table_refs=refs, limit=1)
    assert first["next_cursor"] == [" app ", "%_a"]
    final = server.list_tables("app-db", table_refs=list(reversed(refs)), limit=2, cursor=first["next_cursor"])
    assert table_keys(first) + table_keys(final) == [(" app ", "%_a"), (" app ", "%_b")]
    assert final["has_more"] is False


def test_explicit_cursor_starts_after_a_known_table_without_prior_request(catalog):
    catalog.tables = {"app": ["a", "b"], "audit": ["a", "b"], "other": ["c"]}
    cursor = ["app", "b"]
    result = server.list_tables("app-db", schemas=["app", "audit"], cursor=cursor, limit=2, detail="summary")
    assert table_keys(result) == [("audit", "a"), ("audit", "b")]
    assert result["has_more"] is False
    assert result["next_cursor"] is None
    assert catalog.discovery_calls[0]["after"] == ("app", "b")
    assert cursor == ["app", "b"]


@pytest.mark.parametrize("tool,width", [(server.list_schemas, 1), (server.list_tables, 2)])
@pytest.mark.parametrize("cursor", ["", "eyJ2IjoxLCJzY29wZSI6InVudXNlZCIsImFmdGVyIjpbImFwcCIsImEiXX0", {}, 0, True])
def test_non_array_cursors_are_rejected_before_database_access(monkeypatch, tool, width, cursor):
    connect = Mock()
    monkeypatch.setattr(server.psycopg, "connect", connect)
    monkeypatch.setattr(server, "_metadata_inspector_cm", connect)
    with pytest.raises(ValueError, match="cursor"):
        tool("app-db", cursor=cursor)
    connect.assert_not_called()


@pytest.mark.parametrize("tool,width", [(server.list_schemas, 1), (server.list_tables, 2)])
@pytest.mark.parametrize("shape", ["empty", "too_many", "tuple"])
def test_cursor_array_shape_is_validated_before_database_access(monkeypatch, tool, width, shape):
    cursor = [] if shape == "empty" else ["app"] * (width + 1) if shape == "too_many" else ("app",) * width
    connect = Mock()
    monkeypatch.setattr(server.psycopg, "connect", connect)
    monkeypatch.setattr(server, "_metadata_inspector_cm", connect)
    with pytest.raises(ValueError, match="cursor"):
        tool("app-db", cursor=cursor)
    connect.assert_not_called()


@pytest.mark.parametrize("tool,width", [(server.list_schemas, 1), (server.list_tables, 2)])
@pytest.mark.parametrize("value", [None, 1, "", "a\x00", "a" * 1025, "é" * 513])
def test_cursor_values_are_validated_before_database_access(monkeypatch, tool, width, value):
    connect = Mock()
    monkeypatch.setattr(server.psycopg, "connect", connect)
    monkeypatch.setattr(server, "_metadata_inspector_cm", connect)
    with pytest.raises(ValueError, match="cursor"):
        tool("app-db", cursor=[value] * width)
    connect.assert_not_called()


def test_cursor_validation_preserves_exact_names_and_accepts_the_byte_boundary():
    assert pagination._validate_cursor(None, 2) is None
    assert pagination._validate_cursor([" app ", " quote's "], 2) == (" app ", " quote's ")
    assert pagination._validate_cursor(["é" * 512], 1) == ("é" * 512,)


@pytest.mark.parametrize("value", [0, 1001, -1, True, 1.5])
@pytest.mark.parametrize("tool", [server.list_schemas, server.list_tables])
def test_invalid_limits_fail_before_connect(monkeypatch, value, tool):
    connect = Mock()
    monkeypatch.setattr(server.psycopg, "connect", connect)
    with pytest.raises(ValueError, match="limit"):
        tool("app-db", limit=value)
    connect.assert_not_called()


@pytest.mark.parametrize("value", [0, 1001, True])
def test_auto_threshold_is_independently_bounded(value):
    with pytest.raises(ValueError, match="auto_full_limit"):
        server.list_tables("app-db", auto_full_limit=value)


@pytest.mark.parametrize("filters", [
    {"schemas": ["app"] * 1001},
    {"table_refs": [{"schema": "app", "name": "a"}] * 1001},
    {"schemas": ["a" * 1025]},
    {"table_refs": [{"schema": "app", "name": "a" * 1025}]},
    {"schemas": ["a\x00"]},
])
def test_explicit_filters_are_bounded_before_connect(monkeypatch, filters):
    connect = Mock()
    monkeypatch.setattr(server.psycopg, "connect", connect)
    with pytest.raises(ValueError, match="at most|identifiers"):
        server.list_tables("app-db", **filters)
    connect.assert_not_called()





def test_empty_catalog_is_complete(catalog):
    result = server.list_tables("app-db")
    assert result["count"] == 0
    assert result["has_more"] is False
    assert result["next_cursor"] is None


def test_byte_cutoff_resumes_after_last_emitted_not_last_reflected_table(catalog, monkeypatch):
    catalog.tables = {"app": ["a", "b", "c", "d"]}
    catalog.metadata = {"comments": {("app", name): "x" * 1000 for name in "abcd"}}
    monkeypatch.setattr(pagination, "_MAX_METADATA_BYTES", 3000)
    seen = []
    cursor = None
    while True:
        result = server.list_tables("app-db", detail="summary", limit=4, cursor=cursor)
        assert len(to_json(result)) <= 3000
        seen.extend(table_keys(result))
        if not result["has_more"]:
            break
        assert result["truncation_reason"] == "max_result_bytes"
        assert result["next_cursor"] == list(seen[-1])
        cursor = result["next_cursor"]
    assert seen == [("app", name) for name in "abcd"]


def test_oversized_object_is_an_explicit_error_after_connection_cleanup(catalog, monkeypatch):
    catalog.tables = {"app": ["a"]}
    catalog.metadata = {"comments": {("app", "a"): "private-comment" * 1000}}
    monkeypatch.setattr(pagination, "_MAX_METADATA_BYTES", 1000)
    closed = []

    @contextlib.contextmanager
    def manager(kwargs):
        try:
            with fake_metadata_inspector_cm(catalog) as inspector:
                yield inspector
        finally:
            closed.append(True)

    monkeypatch.setattr(server, "_metadata_inspector_cm", manager)
    with pytest.raises(ValueError, match="one object") as error:
        server.list_tables("app-db")
    assert "private-comment" not in str(error.value)
    assert closed == [True]


def test_schema_pages_use_bounded_query_and_timeout_before_return(monkeypatch):
    cursor = FakeCursor(fetchmany_result=[{"schema_name": name} for name in ("a", "b", "c")])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(server, "config", TEST_CONFIG)
    monkeypatch.setattr(server, "config_error_msg", None)
    monkeypatch.setattr(server.psycopg, "connect", Mock(return_value=connection))
    result = server.list_schemas("app-db", limit=2)
    assert result["schemas"] == ["a", "b"]
    assert result["has_more"] is True
    assert result["next_cursor"] == ["b"]
    query, params = cursor.executed[-1]
    assert "limit %(limit)s" in query
    assert "left(schema_name, 3) <> 'pg_'" in query
    assert params == {"limit": 3}
    assert cursor.executed[:2] == [("set local statement_timeout = 300000", None), ("set local lock_timeout = 5000", None)]
    assert cursor.fetchmany_sizes == [3]
    assert connection.read_only is True
    assert cursor.exit_count == 1


def test_schema_continuation_uses_arrays_and_resumes_after_the_last_emitted_name(monkeypatch):
    monkeypatch.setattr(server, "config", TEST_CONFIG)
    monkeypatch.setattr(server, "config_error_msg", None)
    monkeypatch.setattr(pagination, "_MAX_METADATA_BYTES", 500)
    names = [f"schema_{index:03}_" + "x" * 40 for index in range(20)]
    cursors = []

    def connect(**kwargs):
        class SchemaCursor(FakeCursor):
            def execute(self, query, params=None):
                super().execute(query, params)
                if query.startswith("select"):
                    self.fetchmany_result = [{"schema_name": name} for name in names if name > (params.get("after") or "")][:params["limit"]]
        cursor = SchemaCursor()
        cursors.append(cursor)
        return FakeConnection(cursor)

    monkeypatch.setattr(server.psycopg, "connect", connect)
    seen = []
    cursor = None
    while True:
        result = server.list_schemas("app-db", limit=10, include_system=True, cursor=cursor)
        seen.extend(result["schemas"])
        assert len(to_json(result)) <= 500
        if not result["has_more"]:
            assert result["next_cursor"] is None
            break
        assert result["next_cursor"] == [seen[-1]]
        cursor = result["next_cursor"]
    assert seen == names
    assert "after" in cursors[1].executed[-1][1]


@pytest.mark.parametrize("filters", [
    {"schemas": None, "table_refs": None, "include_views": True, "after": None},
    {"schemas": [" app "], "table_refs": None, "include_views": False, "after": (" app ", "x")},
    {"schemas": None, "table_refs": [{"schema": "app", "name": "a"}], "include_views": True, "after": None},
])
def test_catalog_discovery_pushes_page_and_filters_to_database(filters):
    inspector = Mock()
    connection = Mock()
    inspector.bind.connect.return_value = contextlib.nullcontext(connection)
    connection.execute.return_value.mappings.return_value.fetchmany.return_value = []
    assert inspection._discover_table_refs(inspector, **filters, limit=8) == []
    query, params = connection.execute.call_args.args
    assert params["limit"] == 8
    assert "limit :limit" in str(query)
    assert 'collate "C"' in str(query)
    assert "relpersistence <> 't'" in str(query)
    if filters["after"] is not None:
        assert params["after_schema"] == " app "
        assert params["after_name"] == "x"
        assert " app " not in str(query)
    if filters["schemas"] is None and filters["table_refs"] is None:
        assert "information_schema.schemata" in str(query)
    connection.execute.return_value.mappings.return_value.fetchmany.assert_called_once_with(8)


def test_metadata_connection_applies_statement_timeouts_and_disposes_engine(monkeypatch):
    connection = Mock()
    engine = Mock()
    connect = Mock(return_value=connection)
    monkeypatch.setattr(inspection.psycopg, "connect", connect)

    def create_engine(url, *, creator):
        assert creator() is connection
        assert connection.read_only is True
        return engine

    monkeypatch.setattr(inspection, "create_engine", create_engine)
    monkeypatch.setattr(inspection, "inspect_database", lambda engine: "inspector")
    with inspection._metadata_inspector_cm({"options": "-csearch_path=public"}) as inspector:
        assert inspector == "inspector"
    engine.dispose.assert_called_once_with()
    assert connect.call_args.kwargs["options"] == "-csearch_path=public -cstatement_timeout=300000 -clock_timeout=5000"


@pytest.mark.asyncio
async def test_protocol_advertises_bounded_metadata_page_and_auto_threshold():
    async with Client(server.mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
    for name, width in (("list_schemas", 1), ("list_tables", 2)):
        properties = tools[name].inputSchema["properties"]
        assert properties["limit"]["minimum"] == 1
        assert properties["limit"]["maximum"] == 1000
        assert "cursor" in properties
        assert "name_prefix" not in properties and "page_size" not in properties
        cursor_variants = properties["cursor"]["anyOf"]
        array_schema = next(variant for variant in cursor_variants if variant["type"] == "array")
        assert array_schema["minItems"] == width
        assert array_schema["maxItems"] == width
        assert array_schema["items"]["type"] == "string"
        assert {variant["type"] for variant in cursor_variants} == {"array", "null"}
    threshold = tools["list_tables"].inputSchema["properties"]["auto_full_limit"]
    assert threshold["minimum"] == 1 and threshold["maximum"] == 1000


@pytest.mark.asyncio
async def test_protocol_table_cursor_round_trip_uses_json_arrays(catalog):
    catalog.tables = {"app": ["a", "b"], "audit": ["a"]}
    async with Client(server.mcp) as client:
        first = (await client.call_tool("list_tables", {"connection_name": "app-db", "limit": 1, "detail": "summary"})).data
        assert first["next_cursor"] == ["app", "a"]
        final = (await client.call_tool("list_tables", {"connection_name": "app-db", "limit": 2, "detail": "summary", "cursor": first["next_cursor"]})).data
    assert table_keys(final) == [("app", "b"), ("audit", "a")]
    assert final["has_more"] is False
    assert final["next_cursor"] is None
    assert catalog.discovery_calls[-1]["after"] == ("app", "a")


@pytest.mark.asyncio
async def test_protocol_rejects_legacy_string_cursor_before_catalog_access(catalog):
    async with Client(server.mcp) as client:
        with pytest.raises(ToolError, match="cursor"):
            await client.call_tool("list_tables", {"connection_name": "app-db", "cursor": "eyJ2IjoxLCJhZnRlciI6WyJhcHAiLCJhIl19"})
    assert catalog.discovery_calls == []


def test_default_auto_small_catalog_has_full_metadata_without_another_probe(catalog):
    catalog.tables = {"public": ["a", "b"]}
    result = server.list_tables("app-db")
    assert result["count"] == 2 and result["has_more"] is False
    assert result["detail"] == "full"
    assert all("columns" in table for table in result["tables"])
    assert len(catalog.discovery_calls) == 1
