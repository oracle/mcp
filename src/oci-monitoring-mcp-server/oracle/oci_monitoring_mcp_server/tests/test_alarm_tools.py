"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import AsyncMock, Mock, patch

import oci
import pytest
from oracle.oci_monitoring_mcp_server.alarms.models import AlarmSummary
from oracle.oci_monitoring_mcp_server.alarms.tools import MonitoringAlarmTools


@pytest.fixture
def mock_context():
    """Create mock MCP context."""
    context = Mock()
    context.info = AsyncMock()
    context.warning = AsyncMock()
    context.error = AsyncMock()
    return context


class TestAlarmTools:
    @pytest.mark.asyncio
    @patch.object(MonitoringAlarmTools, "get_monitoring_client")
    async def test_list_alarms(self, mock_context):
        with patch("oci.monitoring.MonitoringClient") as mock_oci_monitoring_client:
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

            mock_oci_monitoring_client.return_value = Mock()
            mock_list_response = Mock()
            mock_list_response.data = [mock_alarm1, mock_alarm2]
            mock_oci_monitoring_client.return_value.list_alarms.return_value = (
                mock_list_response
            )

            alarm_tools = MonitoringAlarmTools()

            result = alarm_tools.list_alarms(compartment_id="compartment1")
            for alarm in result:
                assert isinstance(alarm, AlarmSummary)
