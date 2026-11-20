"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import asyncio
import json
import os
import threading
from unittest.mock import patch

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from oracle.oracle_goldengate_mcp_server.http_client import GoldenGateHTTPError

with patch.dict(os.environ, {"OGG_BASE_URL": "https://example.invalid", "OGG_USERNAME": "user", "OGG_PASSWORD": "example-password"}, clear=True):
    from oracle.oracle_goldengate_mcp_server import server


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def session():
    async with create_connected_server_and_client_session(server.mcp) as connected:
        yield connected


@pytest.mark.anyio
async def test_discovery_exposes_effects_and_schema_constraints(session):
    discovered = await session.list_tools()
    tools = {tool.name: tool for tool in discovered.tools}
    assert len(tools) == 37
    for name, tool in tools.items():
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint == name.startswith(("list_", "get_"))
        assert tool.annotations.openWorldHint == (name != "get_initial_load_cdc_workflow")
        if not tool.annotations.readOnlyHint:
            assert tool.annotations.destructiveHint is True
            assert tool.annotations.idempotentHint is False
    schema = tools["create_extract"].inputSchema
    assert "extractName" in schema["required"]
    assert schema["properties"]["extractName"]["pattern"] == server.PROCESS_NAME_PATTERN
    assert schema["properties"]["trailName"]["pattern"] == server.TRAIL_NAME_PATTERN
    assert tools["add_trandata_table"].inputSchema["properties"]["prepareCsnMode"]["enum"] == ["nowait", "wait", "lock", "none"]


@pytest.mark.anyio
@pytest.mark.parametrize("argument,value", [
    ("extractName", "A!"), ("extractName", "E\nX"), ("extractName", "TOO_LONG_NAME"),
    ("trailName", "a!"), ("trailName", "ABC"),
    ("advanced", {"reportCount": {"every": {"value": 1}}}),
    ("advanced", {"reportCount": {"every": {"value": 0, "unit": "MINUTES"}}}),
    ("advanced", {"reportCount": {"every": {"value": 1, "unit": "BOGUS"}}}),
])
async def test_invalid_inputs_are_protocol_errors_before_service_calls(session, argument, value):
    arguments = {"extractName": "E1", "trailName": "AA", "domainName": "D", "connectionName": "C", "tableStatement": "S.T"}
    arguments[argument] = value
    with patch.object(server.client, "post") as post:
        result = await session.call_tool("create_extract", arguments)
    assert result.isError
    post.assert_not_called()


@pytest.mark.anyio
async def test_json_arguments_coercion_serialization_and_redaction(session):
    arguments = {
        "extractName": "E_$1", "trailName": "AA", "domainName": "D", "connectionName": "C",
        "source": {"schema": "HR", "table": "EMP"},
        "advanced": {"reportCount": {"every": {"value": 2, "unit": "MINUTES"}}},
    }
    with patch.object(server.client, "post", return_value={"password": "example-password", "ok": True}) as post:
        result = await session.call_tool("create_extract", arguments)
    assert not result.isError
    payload = post.call_args.args[1]
    assert "REPORTCOUNT EVERY 2 MINUTES" in payload["config"]
    assert "TABLE HR.EMP;" in payload["config"]
    assert json.loads(result.content[0].text) == {"password": "[REDACTED]", "ok": True}
    assert json.loads(result.structuredContent["result"])["ok"] is True


@pytest.mark.anyio
async def test_tool_workers_leave_event_loop_responsive(session):
    entered, release = threading.Event(), threading.Event()
    event_loop_thread = threading.get_ident()
    worker_threads = []

    def get(_path):
        worker_threads.append(threading.get_ident())
        entered.set()
        if not release.wait(5):
            raise AssertionError("Worker was not released")
        return {"items": []}

    with patch.object(server.client, "get", side_effect=get):
        task = asyncio.create_task(session.call_tool("list_domains", {}))
        try:
            assert await asyncio.to_thread(entered.wait, 5)
            assert worker_threads != [event_loop_thread]
            await asyncio.wait_for(session.send_ping(), timeout=2)
        finally:
            release.set()
        result = await task
    assert not result.isError


@pytest.mark.anyio
async def test_guard_refusal_is_an_mcp_error_and_never_starts(session):
    with patch.object(server.client, "get", return_value={"response": {"status": "running"}}), patch.object(server.client, "post") as post:
        result = await session.call_tool("start_initial_load_replicat", {"replicatName": "R_INIT", "initialLoadExtractName": "E_INIT"})
    assert result.isError
    assert "not confirmed STOPPED" in result.content[0].text
    post.assert_not_called()


@pytest.mark.anyio
async def test_generic_start_cannot_bypass_guard_over_mcp(session):
    def get(path):
        if path == server.api.get_extract_details("R1"):
            raise GoldenGateHTTPError(404, "not found")
        return {
            server.api.get_replicat_details("R1"): {"source": {"name": "I1"}, "config": ["REPLICAT R1"]},
            server.api.list_extracts(): {"items": [{"name": "E_INIT"}]},
            server.api.get_extract_details("E_INIT"): {"source": "tables", "config": ["EXTFILE I1, PURGE"]},
        }[path]

    with patch.object(server.client, "get", side_effect=get), patch.object(server.client, "post") as post:
        result = await session.call_tool("start", {"processName": "R1"})
    assert result.isError
    assert "start_initial_load_replicat" in result.content[0].text
    post.assert_not_called()


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["nowait", "wait", "lock", "none", "invalid"])
async def test_trandata_modes_are_validated_before_side_effects(session, mode):
    arguments = {"domain": "D", "connection": "C", "schemaName": "HR", "tableName": "EMP", "prepareCsnMode": mode}
    with patch.object(server.client, "post", return_value={"ok": True}) as post:
        result = await session.call_tool("add_trandata_table", arguments)
    if mode == "invalid":
        assert result.isError
        post.assert_not_called()
    else:
        assert not result.isError
        assert post.call_args.args[1]["prepareCsnMode"] == mode
