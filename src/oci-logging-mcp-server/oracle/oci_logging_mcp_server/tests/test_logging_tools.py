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
        mock_client.list_log_groups.return_value = mock_summarize_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_log_groups",
                    {
                        "compartment_id": "compartment1",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["display_name"] == "groupUp"
            assert result[0]["id"] == "logGroup1"

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
        mock_client.list_logs.return_value = mock_summarize_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_logs",
                    {
                        "log_group_id": "logGroup1",
                    },
                )
            ).structured_content["result"]
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
            is_enabled="true",
        )
        mock_client.get_log.return_value = mock_get_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_log",
                    {
                        "log_id": "ocid1.log.oc1.1",
                        "log_group_id": "logGroup1",
                    },
                )
            ).structured_content

            assert result["id"] == "ocid1.log.oc1.iad.1"
            assert result["display_name"] == "jh-pbf-app_invoke"
            assert result["lifecycle_state"] == "ACTIVE"
            assert result["log_type"] == "SERVICE"
            assert result["retention_duration"] == 30
            assert result["is_enabled"] == "true"
