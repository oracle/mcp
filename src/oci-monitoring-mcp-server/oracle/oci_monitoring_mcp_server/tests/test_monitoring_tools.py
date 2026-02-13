"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_monitoring_mcp_server import server
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
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_get_metrics_data(self, mock_create_client):
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

        monitoring_client = Mock()
        mock_create_client.return_value = monitoring_client
        mock_list_response = Mock()
        mock_list_response.data = [metric]
        monitoring_client.summarize_metrics_data.return_value = mock_list_response

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
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_metric_definitions(self, mock_create_client):
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

        monitoring_client = Mock()
        mock_create_client.return_value = monitoring_client
        mock_list_response = Mock()
        mock_list_response.data = [metric1, metric2]
        monitoring_client.list_metrics.return_value = mock_list_response

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
            assert isinstance(metric, dict)
            assert metric["compartment_id"] == "compartment1"
            assert "namespace" in metric

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_metric_definitions_empty(self, mock_create_client):
        monitoring_client = Mock()
        mock_create_client.return_value = monitoring_client
        mock_list_response = None
        monitoring_client.list_metrics.return_value = mock_list_response

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
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_alarms(self, mock_create_client):
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

        monitoring_client = Mock()
        mock_create_client.return_value = monitoring_client
        mock_list_response = Mock()
        mock_list_response.data = [mock_alarm1, mock_alarm2]
        monitoring_client.list_alarms.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_alarms", {"compartment_id": "compartment1"}
            )
        result = call_tool_result.structured_content["result"]

        for alarm in result:
            assert isinstance(alarm, dict)
            assert "id" in alarm
            assert "display_name" in alarm

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_alarms_with_overrides(self, mock_create_client):
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

        monitoring_client = Mock()
        mock_create_client.return_value = monitoring_client
        mock_list_response = Mock()
        mock_list_response.data = [mock_alarm1, mock_alarm2]
        monitoring_client.list_alarms.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_alarms", {"compartment_id": "compartment1"}
            )
        result = call_tool_result.structured_content["result"]

        for alarm in result:
            assert isinstance(alarm, dict)
            assert "id" in alarm
            assert "display_name" in alarm

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_alarms_no_response(self, mock_create_client):
        monitoring_client = Mock()
        mock_create_client.return_value = monitoring_client
        mock_list_response = None
        monitoring_client.list_alarms.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_alarms", {"compartment_id": "compartment1"}
            )
        result = call_tool_result.structured_content["result"]
        assert result == "There was no response returned from the Monitoring API"

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_get_metrics_data_empty_response(self, mock_create_client):
        monitoring_client = Mock()
        mock_create_client.return_value = monitoring_client
        monitoring_client.summarize_metrics_data.return_value = None

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_metrics_data",
                {
                    "query": "CpuUtilization[1m].sum()",
                    "compartment_id": "compartment1",
                    "start_time": "2023-01-01T00:00:00Z",
                    "end_time": "2023-01-01T00:00:00Z",
                    "namespace": "oci_compute",
                },
            )
        result = call_tool_result.structured_content["result"]
        assert result == "There was no response returned from the Monitoring API"


class TestInternals:
    def test_prepare_time_parameters(self):
        start, end = server._prepare_time_parameters("2023-01-01T00:00:00Z", None)
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert start.tzinfo is not None
        assert end.tzinfo is not None


class TestReadFile:
    def test_read_file(self):
        document = get_script_content(MQL_QUERY_DOC)
        assert document is not None
