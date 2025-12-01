"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import oci
import pytest
from oracle.oci_monitoring_mcp_server.metrics.models import Metric
from oracle.oci_monitoring_mcp_server.metrics.tools import MonitoringMetricsTools


@pytest.fixture
def mock_context():
    """Create mock MCP context."""
    context = Mock()
    context.info = AsyncMock()
    context.warning = AsyncMock()
    context.error = AsyncMock()
    return context


class TestMetricTools:
    @pytest.mark.asyncio
    async def test_get_compute_metrics(self, mock_context):
        with patch.object(
            MonitoringMetricsTools, "get_monitoring_client"
        ) as mock_oci_monitoring_client:
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

            mock_oci_monitoring_client.return_value = Mock()
            mock_list_response = Mock()
            mock_list_response.data = [metric]
            mock_oci_monitoring_client.return_value.summarize_metrics_data.return_value = (
                mock_list_response
            )

            metrics_tools = MonitoringMetricsTools()

            result = metrics_tools.get_compute_metrics(
                compartment_id="compartment1",
                start_time="2023-01-01T00:00:00Z",
                end_time="2023-01-01T00:00:00Z",
                metric_name="MemoryUtilization",
            )

            assert result is not None
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["dimensions"] == {"resourceId": "instance1"}
            assert "datapoints" in result[0]
            assert len(result[0]["datapoints"]) == 2
            assert result[0]["datapoints"][0]["timestamp"] == "2023-01-01T00:00:00Z"
            assert result[0]["datapoints"][0]["value"] == pytest.approx(42.0)

    @pytest.mark.asyncio
    async def test_get_metrics_data(self, mock_context):
        with patch.object(
            MonitoringMetricsTools, "get_monitoring_client"
        ) as mock_oci_monitoring_client:
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

            mock_oci_monitoring_client.return_value = Mock()
            mock_list_response = Mock()
            mock_list_response.data = [metric]
            mock_oci_monitoring_client.return_value.summarize_metrics_data.return_value = (
                mock_list_response
            )

            metrics_tools = MonitoringMetricsTools()

            result = await metrics_tools.get_metrics_data(
                mock_context,
                compartment_id="compartment1",
                start_time="2023-01-01T00:00:00Z",
                end_time="2023-01-01T00:00:00Z",
            )

            assert result is not None
        for metric in result:
            assert isinstance(metric, Metric)
