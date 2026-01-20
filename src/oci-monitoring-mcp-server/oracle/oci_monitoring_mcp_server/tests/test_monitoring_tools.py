"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_monitoring_mcp_server.alarm_models import (
    AlarmSummary,
    map_alarm_summary,
)
from oracle.oci_monitoring_mcp_server.metric_models import (
    Metric,
    map_metric,
)
from oracle.oci_monitoring_mcp_server.scripts import MQL_QUERY_DOC, get_script_content
from oracle.oci_monitoring_mcp_server.server import mcp


@pytest.fixture
def mock_context():
    """Create mock MCP context."""
    context = Mock()
    context.info = AsyncMock()
    context.warning = AsyncMock()
    context.error = AsyncMock()
    return context


class TestMonitoringTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_monitoring_mcp_server.server.get_monitoring_client")
    async def test_get_metrics_data(self, mock_get_client):
        metric = oci.monitoring.models.MetricData(
            namespace="123",
            resource_group=None,
            dimensions={"resourceId": "instance1"},
            compartment_id="compartment1",
            aggregated_datapoints=[
                MagicMock(timestamp="2023-01-01T00:00:00Z", value=42.0),
                MagicMock(timestamp="2023-01-01T00:01:00Z", value=43.5),
            ],
        )

        mock_get_client.return_value = Mock()
        mock_list_response = Mock()
        mock_list_response.data = [metric]
        mock_get_client.return_value.summarize_metrics_data.return_value = (
            mock_list_response
        )

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_metrics_data",
                {
                    "query": "CpuUtilization[1m].sum()",
                    "compartment_id": "compartment1",
                    "start_time": "2023-01-01T00:00:00Z",
                    "end_time": "2023-01-01T00:00:00Z",
                },
            )
        result = call_tool_result.structured_content["result"]

        assert result is not None
        for metric in result:
            assert metric["namespace"] == "123"
            assert metric["compartment_id"] == "compartment1"
            assert isinstance(metric["aggregated_datapoints"], list)

    @pytest.mark.asyncio
    @patch("oracle.oci_monitoring_mcp_server.server.get_monitoring_client")
    async def test_list_metric_definitions(self, mock_get_client):
        metric1 = oci.monitoring.models.Metric(
            namespace="123",
            resource_group=None,
            dimensions={"resourceId": "instance1"},
            compartment_id="compartment1",
        )

        metric2 = oci.monitoring.models.Metric(
            namespace="123",
            resource_group=None,
            dimensions={"resourceId": "instance1"},
            compartment_id="compartment1",
        )

        mock_get_client.return_value = Mock()
        mock_list_response = Mock()
        mock_list_response.data = [metric1, metric2]
        mock_get_client.return_value.list_metrics.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_metric_definitions",
                {
                    "compartment_id": "compartment1",
                },
            )
        result = call_tool_result.structured_content["result"]

        assert result is not None
        for metric in result:
            assert isinstance(map_metric(metric), Metric)
            assert metric["compartment_id"] == "compartment1"

    @pytest.mark.asyncio
    @patch("oracle.oci_monitoring_mcp_server.server.get_monitoring_client")
    async def test_list_metric_definitions_empty(self, mock_get_client):
        mock_get_client.return_value = Mock()
        mock_list_response = None
        mock_get_client.return_value.list_metrics.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_metric_definitions",
                {
                    "compartment_id": "compartment1",
                },
            )
        result = call_tool_result.structured_content["result"]

        assert result == "There was no response returned from the Monitoring API"

    @pytest.mark.asyncio
    @patch("oracle.oci_monitoring_mcp_server.server.get_monitoring_client")
    async def test_list_alarms(self, mock_get_client):
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

        mock_get_client.return_value = Mock()
        mock_list_response = Mock()
        mock_list_response.data = [mock_alarm1, mock_alarm2]
        mock_get_client.return_value.list_alarms.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_alarms", {"compartment_id": "compartment1"}
            )
        result = call_tool_result.structured_content["result"]

        for alarm in result:
            assert alarm is not None
            assert isinstance(map_alarm_summary(alarm), AlarmSummary)

    @pytest.mark.asyncio
    @patch("oracle.oci_monitoring_mcp_server.server.get_monitoring_client")
    async def test_list_alarms_with_overrides(self, mock_get_client):
        alarm_override = oci.monitoring.models.AlarmOverride(
            body="95% CPU utilization",
            query="CPUUtilization[1m].mean()>95",
            severity="CRITICAL",
        )
        alarm_overrides = [alarm_override]

        mock_alarm1 = oci.monitoring.models.Alarm(
            id="alarm1",
            display_name="Test Alarm 1",
            severity="CRITICAL",
            lifecycle_state="ACTIVE",
            namespace="oci_monitoring",
            query="CpuUtilization[1m].mean() > 80",
            overrides=alarm_overrides,
        )
        mock_alarm2 = oci.monitoring.models.Alarm(
            id="alarm2",
            display_name="Test Alarm 2",
            severity="WARNING",
            lifecycle_state="ACTIVE",
            namespace="oci_monitoring",
            query="MemoryUtilization[1m].mean() > 90",
        )

        mock_get_client.return_value = Mock()
        mock_list_response = Mock()
        mock_list_response.data = [mock_alarm1, mock_alarm2]
        mock_get_client.return_value.list_alarms.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_alarms", {"compartment_id": "compartment1"}
            )
        result = call_tool_result.structured_content["result"]

        for alarm in result:
            assert alarm is not None
            assert isinstance(map_alarm_summary(alarm), AlarmSummary)

    @pytest.mark.asyncio
    @patch("oracle.oci_monitoring_mcp_server.server.get_monitoring_client")
    async def test_list_alarms_no_response(self, mock_get_client):
        mock_get_client.return_value = Mock()
        mock_list_response = None
        mock_get_client.return_value.list_alarms.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_alarms", {"compartment_id": "compartment1"}
            )
        result = call_tool_result.structured_content["result"]
        assert result == "There was no response returned from the Monitoring API"


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


class TestReadFile:
    def test_read_file(self):
        document = get_script_content(MQL_QUERY_DOC)
        assert document is not None
