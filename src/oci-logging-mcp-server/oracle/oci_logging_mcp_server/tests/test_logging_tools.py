"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_logging_mcp_server.server import mcp


class TestLoggingTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_logging_client")
    async def test_list_log_groups(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_summarize_response = create_autospec(oci.response.Response)
        mock_summarize_response.data = [
            oci.logging.models.LogGroup(
                id="logGroup1",
                compartment_id="compartment1",
                display_name="groupUp",
            )
        ]
        mock_summarize_response.has_next_page = False
        mock_summarize_response.next_page = None
        mock_client.list_log_groups.return_value = mock_summarize_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_log_groups", {"compartment_id": "compartment1"}
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["display_name"] == "groupUp"
            assert result[0]["id"] == "logGroup1"

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_logging_client")
    async def test_get_log_group(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.logging.models.LogGroup(
            id="logGroup1",
            compartment_id="compartment1",
            lifecycle_state="ACTIVE",
            display_name="groupUp",
        )
        mock_client.get_log_group.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_log_group", {"log_group_id": "logGroup1"}
            )
            result = call_tool_result.structured_content

            assert result["id"] == "logGroup1"
            assert result["compartment_id"] == "compartment1"
            assert result["lifecycle_state"] == "ACTIVE"
            assert result["display_name"] == "groupUp"

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_logging_client")
    async def test_list_logs(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_summarize_response = create_autospec(oci.response.Response)
        mock_summarize_response.data = [
            oci.logging.models.Log(
                id="logid1",
                lifecycle_state="ACTIVE",
                display_name="logjam",
            )
        ]
        mock_summarize_response.has_next_page = False
        mock_summarize_response.next_page = None
        mock_client.list_logs.return_value = mock_summarize_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_logs", {"log_group_id": "logGroup1"}
            )
            result = call_tool_result.structured_content["result"]

            assert result[0]["id"] == "logid1"
            assert result[0]["lifecycle_state"] == "ACTIVE"
            assert result[0]["display_name"] == "logjam"

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_logging_client")
    async def test_get_log(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.logging.models.Log(
            id="ocid1.log.oc1.iad.1",
            display_name="jh-pbf-app_invoke",
            lifecycle_state="ACTIVE",
            log_type="SERVICE",
            retention_duration=30,
        )
        mock_client.get_log.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_log",
                {
                    "log_id": "ocid1.log.oc1.1",
                    "log_group_id": "logGroup1",
                },
            )
            result = call_tool_result.structured_content

            assert result["id"] == "ocid1.log.oc1.iad.1"
            assert result["display_name"] == "jh-pbf-app_invoke"
            assert result["lifecycle_state"] == "ACTIVE"
            assert result["log_type"] == "SERVICE"
            assert result["retention_duration"] == 30

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_logging_search_client")
    async def test_search_logs(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.loggingsearch.models.SearchResponse(
            results=[
                oci.loggingsearch.models.SearchResult(data={"event": "testEvent"})
            ],
            fields=[],
            summary=[],
        )
        mock_client.search_logs.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "search_logs",
                {
                    "time_start": "2025-11-18T15:19:25Z",
                    "time_end": "2025-11-18T20:19:25Z",
                    "search_query": 'search "ocid1.tenancy.oc1..foobar" | sort by datetime desc',
                },
            )
            result = call_tool_result.structured_content

            assert result["results"][0]["data"]["event"] == "testEvent"


class TestServer:
    @patch("oracle.oci_logging_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_logging_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=int(mock_env["ORACLE_MCP_PORT"]),
        )

    @patch("oracle.oci_logging_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        import oracle.oci_logging_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_logging_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_logging_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_logging_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_logging_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
