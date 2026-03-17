"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, mock_open, patch

import oci
import oracle.oci_logging_mcp_server.server as server
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
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
            call_tool_result = await client.call_tool("list_log_groups", {"compartment_id": "compartment1"})
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["display_name"] == "groupUp"
            assert result[0]["id"] == "logGroup1"

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_logging_client")
    async def test_list_log_groups_pagination_without_limit(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Page 1
        resp1 = create_autospec(oci.response.Response)
        resp1.data = [
            oci.logging.models.LogGroup(id="lg1", display_name="G1"),
            oci.logging.models.LogGroup(id="lg2", display_name="G2"),
        ]
        resp1.has_next_page = True
        resp1.next_page = "p2"

        # Page 2
        resp2 = create_autospec(oci.response.Response)
        resp2.data = [
            oci.logging.models.LogGroup(id="lg3", display_name="G3"),
        ]
        resp2.has_next_page = False
        resp2.next_page = None

        mock_client.list_log_groups.side_effect = [resp1, resp2]

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_log_groups",
                    {"compartment_id": "tenancy"},
                )
            ).structured_content["result"]

        assert [r["id"] for r in result] == ["lg1", "lg2", "lg3"]
        first_kwargs = mock_client.list_log_groups.call_args_list[0].kwargs
        second_kwargs = mock_client.list_log_groups.call_args_list[1].kwargs
        assert first_kwargs["page"] is None
        assert first_kwargs["limit"] is None
        assert second_kwargs["page"] == "p2"
        assert second_kwargs["limit"] is None

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_logging_client")
    async def test_list_log_groups_limit_stops_pagination(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp1 = create_autospec(oci.response.Response)
        resp1.data = [
            oci.logging.models.LogGroup(id="lg1", display_name="G1"),
            oci.logging.models.LogGroup(id="lg2", display_name="G2"),
        ]
        resp1.has_next_page = True
        resp1.next_page = "p2"

        resp2 = create_autospec(oci.response.Response)
        resp2.data = [oci.logging.models.LogGroup(id="lg3", display_name="G3")]
        resp2.has_next_page = False
        resp2.next_page = None

        mock_client.list_log_groups.side_effect = [resp1, resp2]

        limit = 2
        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_log_groups",
                    {"compartment_id": "tenancy", "limit": limit},
                )
            ).structured_content["result"]

        assert [r["id"] for r in result] == ["lg1", "lg2"]
        assert mock_client.list_log_groups.call_count == 1
        kwargs = mock_client.list_log_groups.call_args.kwargs
        assert kwargs["limit"] == limit
        assert kwargs["page"] is None

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
            call_tool_result = await client.call_tool("get_log_group", {"log_group_id": "logGroup1"})
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
            call_tool_result = await client.call_tool("list_logs", {"log_group_id": "logGroup1"})
            result = call_tool_result.structured_content["result"]

            assert result[0]["id"] == "logid1"
            assert result[0]["lifecycle_state"] == "ACTIVE"
            assert result[0]["display_name"] == "logjam"

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_logging_client")
    async def test_list_logs_pagination_without_limit(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Page 1
        resp1 = create_autospec(oci.response.Response)
        resp1.data = [
            oci.logging.models.Log(id="l1", display_name="L1"),
            oci.logging.models.Log(id="l2", display_name="L2"),
        ]
        resp1.has_next_page = True
        resp1.next_page = "np"

        # Page 2
        resp2 = create_autospec(oci.response.Response)
        resp2.data = [oci.logging.models.Log(id="l3", display_name="L3")]
        resp2.has_next_page = False
        resp2.next_page = None

        mock_client.list_logs.side_effect = [resp1, resp2]

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_logs",
                    {"log_group_id": "lg"},
                )
            ).structured_content["result"]

        assert [r["id"] for r in result] == ["l1", "l2", "l3"]
        first_kwargs = mock_client.list_logs.call_args_list[0].kwargs
        second_kwargs = mock_client.list_logs.call_args_list[1].kwargs
        assert first_kwargs["page"] is None
        assert first_kwargs["limit"] is None
        assert second_kwargs["page"] == "np"

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_logging_client")
    async def test_list_logs_limit_stops_pagination(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp1 = create_autospec(oci.response.Response)
        resp1.data = [
            oci.logging.models.Log(id="l1"),
            oci.logging.models.Log(id="l2"),
        ]
        resp1.has_next_page = True
        resp1.next_page = "np"

        resp2 = create_autospec(oci.response.Response)
        resp2.data = [oci.logging.models.Log(id="l3")]
        resp2.has_next_page = False
        resp2.next_page = None

        mock_client.list_logs.side_effect = [resp1, resp2]

        limit = 2
        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_logs",
                    {"log_group_id": "lg", "limit": limit},
                )
            ).structured_content["result"]

        assert [r["id"] for r in result] == ["l1", "l2"]
        assert mock_client.list_logs.call_count == 1
        kwargs = mock_client.list_logs.call_args.kwargs
        assert kwargs["limit"] == limit
        assert kwargs["page"] is None

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
    @patch("oracle.oci_logging_mcp_server.server.get_logging_client")
    async def test_list_log_groups_exception_propagates(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_log_groups.side_effect = RuntimeError("boom")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "list_log_groups",
                    {"compartment_id": "ocid1.tenancy"},
                )

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_logging_client")
    async def test_list_logs_exception_propagates(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_logs.side_effect = ValueError("err")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("list_logs", {"log_group_id": "ocid1.loggroup"})

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_logging_client")
    async def test_get_log_exception_propagates(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_log.side_effect = RuntimeError("boom")

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "get_log",
                    {"log_id": "ocid1.log", "log_group_id": "ocid1.lg"},
                )

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_logging_search_client")
    async def test_search_logs(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.loggingsearch.models.SearchResponse(
            results=[oci.loggingsearch.models.SearchResult(data={"event": "testEvent"})],
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

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.map_search_response")
    @patch("oracle.oci_logging_mcp_server.server.get_logging_search_client")
    async def test_search_logs_oversize_raises_toolerror(self, mock_get_client, mock_map):
        class DummySearchResponse:
            def model_dump_json(self):
                # Force the ValueError path by exceeding size threshold
                return "x" * 60000

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp = create_autospec(oci.response.Response)
        resp.data = object()  # not used by our patched map
        mock_client.search_logs.return_value = resp

        mock_map.return_value = DummySearchResponse()

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "search_logs",
                    {
                        "time_start": "2025-01-01T00:00:00Z",
                        "time_end": "2025-01-01T01:00:00Z",
                        "search_query": "search *",
                        "limit": 50,
                    },
                )

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_script_content")
    async def test_search_log_query_syntax_guide_resource(self, mock_get_script):
        mock_get_script.return_value = "GUIDE CONTENT"

        async with Client(mcp) as client:
            content = (await client.read_resource("resource://search-log-query-syntax-guide"))[0].text
        assert content == "GUIDE CONTENT"
        mock_get_script.assert_called_once()

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_script_content")
    async def test_get_paginated_event_types_basic_pagination(self, mock_get_script):
        content = "\n".join(
            [
                "# Title",
                "",
                "| Event Description | Event ID |",
                "|-------------------|----------|",
                "| Desc A | A |",
                "| Desc B | B |",
                "| Desc C | C |",
            ]
        )
        mock_get_script.return_value = content

        async with Client(mcp) as client:
            raw = (
                await client.call_tool("get_paginated_event_types", {"page": 1, "page_size": 2})
            ).structured_content

        text = raw["result"] if isinstance(raw, dict) and "result" in raw else raw

        # Includes header and only first 2 rows
        assert "| Event Description | Event ID |" in text
        assert "| Desc A | A |" in text
        assert "| Desc B | B |" in text
        assert "| Desc C | C |" not in text
        assert "Page 1 of 2" in text

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_script_content")
    async def test_get_paginated_event_types_no_more_data(self, mock_get_script):
        rows = [
            "| Event Description | Event ID |",
            "|-------------------|----------|",
        ] + [f"| D{i} | {i} |" for i in range(3)]
        content = "\n".join(["Intro", ""] + rows)
        mock_get_script.return_value = content

        async with Client(mcp) as client:
            raw = (
                await client.call_tool("get_paginated_event_types", {"page": 3, "page_size": 2})
            ).structured_content

        text = raw["result"] if isinstance(raw, dict) and "result" in raw else raw
        assert "No more data on page 3" in text

    @pytest.mark.asyncio
    @patch("oracle.oci_logging_mcp_server.server.get_script_content")
    async def test_get_paginated_event_types_table_not_found(self, mock_get_script):
        mock_get_script.return_value = "This is a guide without a table."
        async with Client(mcp) as client:
            raw = (await client.call_tool("get_paginated_event_types", {})).structured_content
        text = raw["result"] if isinstance(raw, dict) and "result" in raw else raw
        assert "Table not found in the guide." in text


class TestServer:
    @patch("oracle.oci_logging_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)

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

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_logging_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_logging_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()


class TestGetClient:
    @patch("oracle.oci_logging_mcp_server.server.oci.logging.LoggingManagementClient")
    @patch("oracle.oci_logging_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_logging_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_logging_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_logging_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_logging_mcp_server.server.os.getenv")
    def test_get_logging_client_with_profile_env(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        # Arrange: provide profile via env var and minimal config dict
        mock_getenv.side_effect = lambda k, default=None: (
            "MYPROFILE" if k == "OCI_CONFIG_PROFILE" else default
        )
        config = {
            "key_file": "/abs/path/to/key.pem",
            "security_token_file": "/abs/path/to/token",
        }
        mock_from_file.return_value = config
        private_key_obj = object()
        mock_load_private_key.return_value = private_key_obj

        # Act
        result = server.get_logging_client()

        # Assert calls
        mock_from_file.assert_called_once_with(
            file_location=oci.config.DEFAULT_LOCATION,
            profile_name="MYPROFILE",
        )
        mock_open_file.assert_called_once_with("/abs/path/to/token", "r")
        mock_security_token_signer.assert_called_once_with("SECURITY_TOKEN", private_key_obj)
        # Ensure user agent was set on the same config dict passed into client
        args, _ = mock_client.call_args
        passed_config = args[0]
        assert passed_config is config
        # And we returned the client instance
        assert result == mock_client.return_value

    @patch("oracle.oci_logging_mcp_server.server.oci.logging.LoggingManagementClient")
    @patch("oracle.oci_logging_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_logging_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_logging_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_logging_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_logging_mcp_server.server.os.getenv")
    def test_get_logging_client_uses_default_profile_when_env_missing(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        # Arrange: no env var present; from_file should be called with DEFAULT_PROFILE
        mock_getenv.side_effect = lambda k, default=None: default
        config = {"key_file": "/k.pem", "security_token_file": "/tkn"}
        mock_from_file.return_value = config
        priv = object()
        mock_load_private_key.return_value = priv

        # Act
        srv_client = server.get_logging_client()

        # Assert: profile defaulted
        mock_from_file.assert_called_once_with(
            file_location=oci.config.DEFAULT_LOCATION,
            profile_name=oci.config.DEFAULT_PROFILE,
        )
        # Token file opened and read
        mock_open_file.assert_called_once_with("/tkn", "r")
        mock_security_token_signer.assert_called_once()
        signer_args, _ = mock_security_token_signer.call_args
        assert signer_args[0] == "TOK"
        assert signer_args[1] is priv
        # additional_user_agent set on original config and passed through
        cc_args, _ = mock_client.call_args
        assert cc_args[0] is config
        # Returned object is client instance
        assert srv_client is mock_client.return_value

    @patch("oracle.oci_logging_mcp_server.server.oci.loggingsearch.LogSearchClient")
    @patch("oracle.oci_logging_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_logging_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_logging_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_logging_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_logging_mcp_server.server.os.getenv")
    def test_get_logging_search_client_with_profile_env(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        # Arrange: provide profile via env var and minimal config dict
        mock_getenv.side_effect = lambda k, default=None: (
            "MYPROFILE" if k == "OCI_CONFIG_PROFILE" else default
        )
        config = {
            "key_file": "/abs/path/to/key.pem",
            "security_token_file": "/abs/path/to/token",
        }
        mock_from_file.return_value = config
        private_key_obj = object()
        mock_load_private_key.return_value = private_key_obj

        # Act
        result = server.get_logging_search_client()

        # Assert calls
        mock_from_file.assert_called_once_with(
            file_location=oci.config.DEFAULT_LOCATION,
            profile_name="MYPROFILE",
        )
        mock_open_file.assert_called_once_with("/abs/path/to/token", "r")
        mock_security_token_signer.assert_called_once_with("SECURITY_TOKEN", private_key_obj)
        # Ensure user agent was set on the same config dict passed into client
        args, _ = mock_client.call_args
        passed_config = args[0]
        assert passed_config is config
        # And we returned the client instance
        assert result == mock_client.return_value

    @patch("oracle.oci_logging_mcp_server.server.oci.loggingsearch.LogSearchClient")
    @patch("oracle.oci_logging_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_logging_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_logging_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_logging_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_logging_mcp_server.server.os.getenv")
    def test_get_logging_search_client_uses_default_profile_when_env_missing(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        # Arrange: no env var present; from_file should be called with DEFAULT_PROFILE
        mock_getenv.side_effect = lambda k, default=None: default
        config = {"key_file": "/k.pem", "security_token_file": "/tkn"}
        mock_from_file.return_value = config
        priv = object()
        mock_load_private_key.return_value = priv

        # Act
        srv_client = server.get_logging_search_client()

        # Assert: profile defaulted
        mock_from_file.assert_called_once_with(
            file_location=oci.config.DEFAULT_LOCATION,
            profile_name=oci.config.DEFAULT_PROFILE,
        )
        # Token file opened and read
        mock_open_file.assert_called_once_with("/tkn", "r")
        mock_security_token_signer.assert_called_once()
        signer_args, _ = mock_security_token_signer.call_args
        assert signer_args[0] == "TOK"
        assert signer_args[1] is priv
        # additional_user_agent set on original config and passed through
        cc_args, _ = mock_client.call_args
        assert cc_args[0] is config
        # Returned object is client instance
        assert srv_client is mock_client.return_value
