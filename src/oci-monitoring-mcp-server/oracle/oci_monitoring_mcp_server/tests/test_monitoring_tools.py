"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_monitoring_mcp_server.server import mcp


class TestMonitoringTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_monitoring_mcp_server.server.get_monitoring_client")
    async def test_get_compute_metrics(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock OCI summarize_metrics_data response with one series containing two points
        mock_summarize_response = create_autospec(oci.response.Response)
        series = MagicMock()
        series.dimensions = {"resourceId": "instance1"}
        series.aggregated_datapoints = [
            MagicMock(timestamp="2023-01-01T00:00:00Z", value=42.0),
            MagicMock(timestamp="2023-01-01T00:01:00Z", value=43.5),
        ]
        mock_summarize_response.data = [series]
        mock_client.summarize_metrics_data.return_value = mock_summarize_response

        # Call the MCP tool
        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_compute_metrics",
                    {
                        "compartment_id": "compartment1",
                        "start_time": "2023-01-01T00:00:00Z",
                        "end_time": "2023-01-01T01:00:00Z",
                        "metricName": "CpuUtilization",
                        "resolution": "1m",
                        "aggregation": "mean",
                        "instance_id": "instance1",
                        "compartment_id_in_subtree": False,
                    },
                )
            ).structured_content["result"]

            # Validate result structure and values
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["dimensions"] == {"resourceId": "instance1"}
            assert "datapoints" in result[0]
            assert len(result[0]["datapoints"]) == 2
            assert result[0]["datapoints"][0]["timestamp"] == "2023-01-01T00:00:00Z"
            assert result[0]["datapoints"][0]["value"] == pytest.approx(42.0)

    @pytest.mark.asyncio
    @patch("oracle.oci_monitoring_mcp_server.server.get_monitoring_client")
    async def test_list_alarms(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_alarm1 = oci.monitoring.models.Alarm(
            id="alarm1",
            display_name="Test Alarm 1",
            severity="CRITICAL",
            lifecycle_state="ACTIVE",
            namespace="oci_monitoring",
            query="CpuUtilization[1m].mean() > 80",
        )
        mock_alarm2 = oci.monitoring.models.Alarm(
            id="alarm2",
            display_name="Test Alarm 2",
            severity="WARNING",
            lifecycle_state="ACTIVE",
            namespace="oci_monitoring",
            query="MemoryUtilization[1m].mean() > 90",
        )

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [mock_alarm1, mock_alarm2]
        mock_client.list_alarms.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_alarms",
                    {
                        "compartment_id": "compartment1",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 2
            assert result[0]["id"] == "alarm1"
            assert result[0]["display_name"] == "Test Alarm 1"
            assert result[1]["id"] == "alarm2"
            assert result[1]["display_name"] == "Test Alarm 2"


class TestServer:
    @patch("oracle.oci_monitoring_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_monitoring_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=int(mock_env["ORACLE_MCP_PORT"]),
        )

    @patch("oracle.oci_monitoring_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        import oracle.oci_monitoring_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_monitoring_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_monitoring_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_monitoring_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_monitoring_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
