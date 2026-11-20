# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""Offline protocol checks for the published Data Studio entry points."""

import json
import sys
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from jsonschema import Draft202012Validator
from starlette.testclient import TestClient

from oracle.data_studio_mcp_server import server
from oracle.data_studio_mcp_server.config import (
    AdpConfig,
    DataTransformsConfig,
    EssbaseConfig,
    ServerConfig,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("profile", "count", "can_query", "can_manage"),
    [("viewer", 15, False, False), ("analyst", 20, True, False), ("admin", 60, True, True)],
)
async def test_profiles_enforce_discovery_and_direct_calls(profile, count, can_query, can_manage):
    async with Client(server.create_server(ServerConfig(profile=profile))) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        assert len(tools) == count
        assert {"essbase_explore", "adp_get_annotations", "dt_explore"} <= tools.keys()
        assert {prompt.name for prompt in await client.list_prompts()} == {"adp_sql_with_annotations"}
        for name, allowed, arguments in [
            ("essbase_query", can_query, {"app_name": "Sample", "db_name": "Basic", "mdx": "SELECT"}),
            ("adp_ai_chat", can_manage, {"question": "example report"}),
            ("dt_run_pipeline", can_manage, {"project_name": "Demo", "resource_name": "Sample"}),
        ]:
            assert (name in tools) is allowed
            if not allowed:
                with pytest.raises(ToolError, match=f"Unknown tool: {name!r}"):
                    await client.call_tool(name, arguments)


@pytest.mark.asyncio
async def test_tool_calls_still_ignore_unknown_top_level_arguments():
    async with Client(server.create_server(ServerConfig())) as client:
        arguments = {"unused": "ignored"}
        result = await client.call_tool("dt_explore", arguments)
        assert json.loads(result.content[0].text) == {
            "error": "Data Transforms not connected. Set DT_URL, DT_USER, DT_PASSWORD."
        }
        tool = next(tool for tool in await client.list_tools() if tool.name == "dt_explore")
        assert Draft202012Validator(tool.input_schema).is_valid(arguments)


@pytest.mark.asyncio
async def test_nullable_arguments_still_accept_encoded_null_without_decoding_plain_strings(monkeypatch):
    adp = SimpleNamespace(
        rest=SimpleNamespace(expired=None, session=Mock()),
        Misc=SimpleNamespace(run_query=lambda _: []),
    )
    monkeypatch.setitem(sys.modules, "adp", SimpleNamespace(login=lambda *_: adp))
    config = ServerConfig(adp=AdpConfig("https://adp.example.invalid", "user", "dummy-password"))

    async with Client(server.create_server(config)) as client:
        result = await client.call_tool(
            "adp_get_annotations", {"object_name": "null", "annotation_owner": "null"}
        )
        body = json.loads(result.content[0].text)
        assert body["object"] == "NULL"
        assert body["annotation_owner_filter"] is None
        for encoded in ("[]", "{}"):
            with pytest.raises(ToolError, match="validation error"):
                await client.call_tool(
                    "adp_get_annotations", {"object_name": "SALES", "annotation_owner": encoded}
                )


@pytest.mark.asyncio
async def test_all_service_tools_use_lifespan_and_preserve_json_results(monkeypatch, caplog):
    ess_session, adp_session = Mock(), Mock()
    ess_grid = Mock()
    ess_grid.execute_mdx.return_value = {"cells": [], "axes": []}
    ess = SimpleNamespace(get_client=lambda: SimpleNamespace(session=ess_session), grid=ess_grid)
    dt = SimpleNamespace(
        get_about=lambda: {"version": "test"},
        list_connections=lambda: [{"name": "REPORTING", "password": "dummy-password"}],
        list_projects=lambda: [],
        list_schedules=lambda: [],
    )
    adp = SimpleNamespace(
        rest=SimpleNamespace(expired=None, session=adp_session),
        Misc=SimpleNamespace(run_query=lambda _: [{"annotation_name": "UNIT", "annotation_value": "USD"}]),
        dt=SimpleNamespace(get_client=lambda: dt),
        wait_for_datatransforms=lambda **_: None,
    )
    monkeypatch.setitem(sys.modules, "essbase", SimpleNamespace(login=lambda *_: ess))
    monkeypatch.setitem(sys.modules, "adp", SimpleNamespace(login=lambda *_: adp))
    config = ServerConfig(
        profile="analyst",
        essbase=EssbaseConfig("https://essbase.example.invalid", "user", "dummy-password"),
        adp=AdpConfig("https://adp.example.invalid", "user", "dummy-password"),
        datatransforms=DataTransformsConfig("https://dt.example.invalid", "user", "dummy-password"),
    )
    caplog.set_level("INFO", logger="oracle-data-studio-mcp.audit")
    async with Client(server.create_server(config)) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        query_schema = tools["essbase_query"].input_schema
        assert set(query_schema["properties"]) == {"app_name", "db_name", "mdx", "max_rows"}
        assert query_schema["required"] == ["app_name", "db_name", "mdx"]
        assert query_schema["properties"]["max_rows"]["default"] == 1000
        assert tools["essbase_query"].output_schema["properties"]["result"]["type"] == "string"

        for name, args, expected in [
            ("essbase_query", {"app_name": "Sample", "db_name": "Basic", "mdx": "example"},
             {"cells": [], "axes": []}),
            ("adp_get_annotations", {"object_name": "sales", "column_name": None},
             {"object": "SALES", "object_type": "TABLE", "annotation_owner_filter": None,
              "annotations": {"table": {"UNIT": "USD"}, "columns": {}}, "annotation_count": 1}),
            ("dt_explore", {}, {"about": {"version": "test"},
                                     "connections": [{"name": "REPORTING", "_redacted": True}]}),
        ]:
            result = await client.call_tool(name, args)
            assert len(result.content) == 1
            assert json.loads(result.content[0].text) == expected
            assert result.structured_content == {"result": result.content[0].text}

        ess_grid.execute_mdx.side_effect = RuntimeError("password=dummy-password")
        result = await client.call_tool("essbase_query", {"app_name": "user/dummy-password@Sample",
                                                        "db_name": "Basic", "mdx": "Bearer example-token"})
        assert json.loads(result.content[0].text) == {"error": "password=***"}
    logs = [r.getMessage() for r in caplog.records if r.name == "oracle-data-studio-mcp.audit"]
    assert logs == [
        "audit tool=essbase_query target=Sample profile=analyst outcome=ok",
        "audit tool=essbase_query target=user/***@Sample profile=analyst outcome=error",
    ]
    ess_session.close.assert_called_once_with()
    adp_session.close.assert_called_once_with()


@pytest.mark.asyncio
@pytest.mark.parametrize("reuse_session", [False, True])
async def test_adp_reconnect_closes_each_acquired_session_at_shutdown(monkeypatch, reuse_session):
    original_session = Mock()
    new_session = original_session if reuse_session else Mock()

    def adp_connection(session, unit):
        return SimpleNamespace(
            rest=SimpleNamespace(expired=None, session=session),
            Misc=SimpleNamespace(run_query=lambda _: [{"annotation_name": "UNIT", "annotation_value": unit}]),
        )

    original = adp_connection(original_session, "USD")
    replacement = adp_connection(new_session, "EUR")
    login = Mock(side_effect=[original, replacement])
    monkeypatch.setitem(sys.modules, "adp", SimpleNamespace(login=login))
    config = ServerConfig(adp=AdpConfig("https://adp.example.invalid", "user", "dummy-password"))

    async with Client(server.create_server(config)) as client:
        first = await client.call_tool("adp_get_annotations", {"object_name": "SALES"})
        assert json.loads(first.content[0].text)["annotations"]["table"] == {"UNIT": "USD"}
        original.rest.expired = datetime.now() - timedelta(seconds=1)
        second = await client.call_tool("adp_get_annotations", {"object_name": "SALES"})
        assert json.loads(second.content[0].text)["annotations"]["table"] == {"UNIT": "EUR"}
        original_session.close.assert_not_called()
        new_session.close.assert_not_called()

    original_session.close.assert_called_once_with()
    new_session.close.assert_called_once_with()


def test_http_entry_point_enforces_bearer_and_runs_lifespan(monkeypatch):
    import uvicorn

    rest = SimpleNamespace(session=Mock())
    ess = SimpleNamespace(get_client=lambda: rest)
    login = Mock(return_value=ess)
    monkeypatch.setitem(sys.modules, "essbase", SimpleNamespace(login=login))

    config = ServerConfig(
        transport="streamable-http",
        host="127.0.0.1",
        port=9222,
        auth_token="test-http-token",
        essbase=EssbaseConfig("https://essbase.example.invalid", "user", "dummy-password"),
    )
    monkeypatch.setattr(server, "load_config", lambda: config)
    message = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-11-25", "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"},
    }}
    accept = {"Accept": "application/json, text/event-stream"}

    async def serve(uvicorn_server):
        settings = uvicorn_server.config
        assert (settings.host, settings.port) == ("127.0.0.1", 9222)
        with TestClient(settings.app, base_url="http://127.0.0.1:9222") as client:
            missing = client.post("/mcp", json=message, headers=accept)
            wrong = client.post("/mcp", json=message, headers={**accept, "Authorization": "Bearer wrong"})
            assert missing.status_code == wrong.status_code == 401
            assert missing.headers["WWW-Authenticate"] == "Bearer"
            assert missing.json() == {"error": "authentication required"}
            assert wrong.json() == {"error": "invalid bearer token"}
            response = client.post(
                "/mcp", json=message, headers={**accept, "Authorization": "Bearer test-http-token"}
            )
            assert response.status_code == 200
            assert "serverInfo" in response.text
            login.assert_called_once_with("https://essbase.example.invalid", "user", "dummy-password")
            rest.session.close.assert_not_called()

    monkeypatch.setattr(uvicorn.Server, "serve", serve)
    server.main()
    rest.session.close.assert_called_once_with()
