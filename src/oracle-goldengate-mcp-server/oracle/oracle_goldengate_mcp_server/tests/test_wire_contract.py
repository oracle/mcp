"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import asyncio
import json
import threading
import time
from types import SimpleNamespace

import pytest
import pytest_asyncio
from fastmcp import Client
from mcp.types import TextContent


@pytest.fixture
def server(monkeypatch):
    monkeypatch.setenv("OGG_BASE_URL", "https://example.com")
    monkeypatch.setenv("OGG_USERNAME", "user")
    monkeypatch.setenv("OGG_PASSWORD", "pass")
    monkeypatch.delenv("OGG_PASSWORD_SECRET_OCID", raising=False)
    monkeypatch.delenv("OGG_PASSWORD_FILE", raising=False)
    monkeypatch.delenv("OCI_PRIVATE_KEY_FILE", raising=False)
    from oracle.oracle_goldengate_mcp_server import server

    return server


@pytest_asyncio.fixture
async def mcp_client(server):
    async with Client(server.mcp) as client:
        yield client


@pytest.mark.asyncio
async def test_tool_catalog_preserves_names_and_contracts(mcp_client):
    tools = {tool.name: tool for tool in await mcp_client.list_tools()}
    assert tools.keys() == {
        "add_trandata_schema",
        "add_trandata_table",
        "create_connection",
        "create_data_stream",
        "create_distribution_path",
        "create_extract",
        "create_initial_load_extract",
        "create_replicat",
        "get_data_stream_info",
        "get_data_stream_stats",
        "get_data_stream_yaml",
        "get_extract_details",
        "get_extract_lag",
        "get_extract_report",
        "get_extract_stats",
        "get_extract_status",
        "get_initial_load_cdc_workflow",
        "get_replicat_details",
        "get_replicat_lag",
        "get_replicat_report",
        "get_replicat_stats",
        "get_replicat_status",
        "list_checkpoint_tables",
        "list_connections",
        "list_data_streams",
        "list_distribution_paths",
        "list_domains",
        "list_extracts",
        "list_replicats",
        "list_trails",
        "start",
        "start_distribution_path",
        "start_initial_load_replicat",
        "stop",
        "stop_distribution_path",
        "update_extract",
        "update_replicat",
    }
    for tool in tools.values():
        assert tool.description
        assert tool.input_schema["type"] == "object"
        assert tool.input_schema.get("additionalProperties", True) is True
        assert tool.output_schema["type"] == "object"
        assert tool.output_schema["required"] == ["result"]
        assert tool.output_schema["properties"]["result"]["type"] == "string"

    create_extract = tools["create_extract"].input_schema
    assert set(create_extract["required"]) == {"extractName", "trailName", "domainName", "connectionName"}
    extract_name = create_extract["properties"]["extractName"]
    assert extract_name["description"] == "Extract process name"
    assert extract_name["minLength"] == 1
    assert extract_name["maxLength"] == 8
    begin = create_extract["properties"]["begin"]
    assert begin["default"] is None
    assert {"type": "null"} in begin["anyOf"]


@pytest.mark.asyncio
async def test_list_domains_preserves_json_in_text_and_structured_results(mcp_client, server, monkeypatch):
    def get(path):
        assert path == "/services/v2/credentials"
        return {"items": [{"name": "OracleGoldenGate"}]}

    monkeypatch.setattr(server.client, "get", get)
    result = await mcp_client.call_tool_mcp("list_domains", {"unused": True})

    assert not result.is_error
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    text = result.content[0].text
    assert json.loads(text) == {"items": [{"name": "OracleGoldenGate"}]}
    assert result.structured_content == {"result": text}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("source", "begin"),
    [
        ({"schema": "HR", "table": "EMP"}, {}),
        ({"schema": "HR", "table": "EMP"}, {"begin": None}),
        ('{"schema":"HR","table":"EMP"}', {"begin": "null"}),
    ],
)
async def test_create_extract_preserves_structured_source_and_default_begin(mcp_client, server, monkeypatch, source, begin):
    def post(path, payload):
        assert path == "/services/v2/extracts/E1"
        assert payload["begin"] == "now"
        assert payload["config"][-1] == "TABLE HR.EMP;"
        return {"status": "created"}

    monkeypatch.setattr(server.client, "post", post)
    result = await mcp_client.call_tool_mcp(
        "create_extract",
        {
            "extractName": "E1",
            "trailName": "AA",
            "domainName": "OracleGoldenGate",
            "connectionName": "source",
            "source": source,
            **begin,
        },
    )
    assert not result.is_error
    assert json.loads(result.structured_content["result"]) == {"status": "created"}


@pytest.mark.asyncio
async def test_http_failure_reports_error_to_client_without_logging_response_body(mcp_client, server, monkeypatch, capsys):
    response = SimpleNamespace(status_code=422, text="synthetic HTTP error body")
    monkeypatch.setattr(server.client.session, "request", lambda **kwargs: response)

    result = await mcp_client.call_tool_mcp("list_domains", {})

    stderr = capsys.readouterr().err
    assert "Error calling tool 'list_domains'" in stderr
    assert response.text not in stderr
    assert result.is_error
    assert result.content[0].text == (
        "Error executing tool list_domains: GET /services/v2/credentials failed: 422 synthetic HTTP error body"
    )


@pytest.mark.asyncio
async def test_invalid_extract_name_rejected_before_http_request(mcp_client, server, monkeypatch):
    def post(*args):
        pytest.fail("An invalid extract name must not reach the deployment")

    monkeypatch.setattr(server.client, "post", post)
    result = await mcp_client.call_tool_mcp("get_extract_status", {"extractName": "TOO_LONG_NAME"})
    assert result.is_error
    assert "extractName" in result.content[0].text


@pytest.mark.asyncio
async def test_concurrent_calls_serialize_shared_http_session_access(mcp_client, server, monkeypatch):
    in_flight = threading.Lock()

    def get(path):
        if not in_flight.acquire(blocking=False):
            raise AssertionError("GoldenGate tools must serialize access to the shared HTTP session")
        try:
            time.sleep(0.05)
            return {"items": []}
        finally:
            in_flight.release()

    monkeypatch.setattr(server.client, "get", get)
    results = await asyncio.gather(
        mcp_client.call_tool_mcp("list_domains", {}),
        mcp_client.call_tool_mcp("list_extracts", {}),
    )
    assert all(result.structured_content == {"result": '{"items": []}'} for result in results)
