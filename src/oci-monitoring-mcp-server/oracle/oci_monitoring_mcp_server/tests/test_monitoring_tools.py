"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, mock_open, patch

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
        mock_get_client.return_value.summarize_metrics_data.return_value = mock_list_response

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
            assert isinstance(metric, dict)
            assert metric["compartment_id"] == "compartment1"
            assert "namespace" in metric

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
            call_tool_result = await client.call_tool("list_alarms", {"compartment_id": "compartment1"})
        result = call_tool_result.structured_content["result"]

        for alarm in result:
            assert isinstance(alarm, dict)
            assert "id" in alarm
            assert "display_name" in alarm

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
            call_tool_result = await client.call_tool("list_alarms", {"compartment_id": "compartment1"})
        result = call_tool_result.structured_content["result"]

        for alarm in result:
            assert isinstance(alarm, dict)
            assert "id" in alarm
            assert "display_name" in alarm

    @pytest.mark.asyncio
    @patch("oracle.oci_monitoring_mcp_server.server.get_monitoring_client")
    async def test_list_alarms_no_response(self, mock_get_client):
        mock_get_client.return_value = Mock()
        mock_list_response = None
        mock_get_client.return_value.list_alarms.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool("list_alarms", {"compartment_id": "compartment1"})
        result = call_tool_result.structured_content["result"]
        assert result == "There was no response returned from the Monitoring API"

    @pytest.mark.asyncio
    @patch("oracle.oci_monitoring_mcp_server.server.get_monitoring_client")
    async def test_get_metrics_data_empty_response(self, mock_get_client):
        mock_get_client.return_value = Mock()
        mock_get_client.return_value.summarize_metrics_data.return_value = None

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


class TestServer:
    @patch("oracle.oci_monitoring_mcp_server.server.mcp.run")
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

    @patch("oracle.oci_monitoring_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_monitoring_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_monitoring_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()


class TestReadFile:
    def test_read_file(self):
        document = get_script_content(MQL_QUERY_DOC)
        assert document is not None


class TestGetClient:
    @patch("oracle.oci_monitoring_mcp_server.server.oci.monitoring.MonitoringClient")
    @patch("oracle.oci_monitoring_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_monitoring_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_monitoring_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_monitoring_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_monitoring_mcp_server.server.os.getenv")
    def test_get_monitoring_client_with_profile_env(
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
        result = server.get_monitoring_client()

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
        expected_user_agent = (
            f"{server.__project__.split('oracle.', 1)[1].split('-server', 1)[0]}/{server.__version__}"  # noqa
        )
        assert passed_config.get("additional_user_agent") == expected_user_agent
        # And we returned the client instance
        assert result == mock_client.return_value

    @patch("oracle.oci_monitoring_mcp_server.server.oci.monitoring.MonitoringClient")
    @patch("oracle.oci_monitoring_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_monitoring_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_monitoring_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_monitoring_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_monitoring_mcp_server.server.os.getenv")
    def test_get_monitoring_client_uses_default_profile_when_env_missing(
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
        srv_client = server.get_monitoring_client()

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
        assert "additional_user_agent" in config
        assert isinstance(config["additional_user_agent"], str) and "/" in config["additional_user_agent"]
        # Returned object is client instance
        assert srv_client is mock_client.return_value
