"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
import oracle.oci_recovery_mcp_server.server as server
from oracle.oci_recovery_mcp_server.server import mcp


class TestGetClientFactories:
    @patch("oracle.oci_recovery_mcp_server.server._wrap_oci_client", side_effect=lambda client, **_: client)
    @patch("oracle.oci_recovery_mcp_server.server.oci.recovery.DatabaseRecoveryClient")
    @patch("oracle.oci_recovery_mcp_server.server._effective_auth_method", return_value="apikey")
    @patch("oracle.oci_recovery_mcp_server.server._load_oci_config_for_server")
    def test_get_recovery_client_apikey_passes_circuit_breaker(
        self,
        mock_load_config,
        _mock_auth_method,
        mock_client,
        _mock_wrap,
    ):
        mock_load_config.return_value = {"region": "us-ashburn-1"}

        result = server.get_recovery_client(region="us-phoenix-1", request_id="rid")

        args, kwargs = mock_client.call_args
        assert args[0]["region"] == "us-phoenix-1"
        assert "signer" not in kwargs
        assert isinstance(kwargs["circuit_breaker_strategy"], oci.circuit_breaker.CircuitBreakerStrategy)
        assert callable(kwargs["circuit_breaker_callback"])
        assert result is mock_client.return_value

    @patch("oracle.oci_recovery_mcp_server.server._wrap_oci_client", side_effect=lambda client, **_: client)
    @patch("oracle.oci_recovery_mcp_server.server._build_signer_for_session")
    @patch("oracle.oci_recovery_mcp_server.server.oci.monitoring.MonitoringClient")
    @patch("oracle.oci_recovery_mcp_server.server._effective_auth_method", return_value="session")
    @patch("oracle.oci_recovery_mcp_server.server._load_oci_config_for_server")
    def test_get_monitoring_client_session_passes_circuit_breaker(
        self,
        mock_load_config,
        _mock_auth_method,
        mock_client,
        mock_build_signer,
        _mock_wrap,
    ):
        mock_load_config.return_value = {"region": "us-ashburn-1"}
        signer = object()
        mock_build_signer.return_value = signer

        result = server.get_monitoring_client(region="us-phoenix-1", request_id="rid")

        args, kwargs = mock_client.call_args
        assert args[0]["region"] == "us-phoenix-1"
        assert kwargs["signer"] is signer
        assert isinstance(kwargs["circuit_breaker_strategy"], oci.circuit_breaker.CircuitBreakerStrategy)
        assert callable(kwargs["circuit_breaker_callback"])
        assert result is mock_client.return_value


class TestRecoveryTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_list_protected_databases(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock list response with a single ProtectedDatabaseSummary
        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.recovery.models.ProtectedDatabaseSummary(
                id="pd1",
                display_name="Protected DB 1",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_protected_databases.return_value = mock_list_response
        # attach metrics at summary level to ensure fallback path covers
        mock_list_response.data[0].metrics = {"backup_space_used_in_gbs": 10.5}

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_protected_databases",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "pd1"
            assert result[0]["display_name"] == "Protected DB 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_get_protected_database(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock get response with a ProtectedDatabase
        mock_get_response = create_autospec(oci.response.Response)
        pd = oci.recovery.models.ProtectedDatabase(
            id="pd1",
            display_name="Protected DB 1",
            lifecycle_state="ACTIVE",
            health="PROTECTED",
        )
        # attach minimal metrics for mapping tolerance
        pd.metrics = {"backup_space_used_in_gbs": 12.5}
        mock_get_response.data = pd
        mock_client.get_protected_database.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_protected_database", {"protected_database_id": "pd1"}
            )
            result = call_tool_result.structured_content

            assert result["id"] == "pd1"
            assert result["health"] == "PROTECTED"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_list_protection_policies(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.recovery.models.ProtectionPolicySummary(
                id="pp1",
                display_name="Policy 1",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_protection_policies.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_protection_policies",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "pp1"
            assert result[0]["display_name"] == "Policy 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_get_protection_policy(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.recovery.models.ProtectionPolicy(
            id="pp1",
            display_name="Policy 1",
            lifecycle_state="ACTIVE",
        )
        mock_client.get_protection_policy.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_protection_policy", {"protection_policy_id": "pp1"}
            )
            result = call_tool_result.structured_content

            assert result["id"] == "pp1"
            assert result["display_name"] == "Policy 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_list_recovery_service_subnets(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.recovery.models.RecoveryServiceSubnetSummary(
                id="rss1",
                display_name="RSS 1",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_recovery_service_subnets.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_recovery_service_subnets",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "rss1"
            assert result[0]["display_name"] == "RSS 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_get_recovery_service_subnet(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.recovery.models.RecoveryServiceSubnet(
            id="rss1",
            display_name="RSS 1",
            lifecycle_state="ACTIVE",
        )
        mock_client.get_recovery_service_subnet.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_recovery_service_subnet", {"recovery_service_subnet_id": "rss1"}
            )
            result = call_tool_result.structured_content

            assert result["id"] == "rss1"
            assert result["display_name"] == "RSS 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_summarize_protected_database_health(
        self, mock_get_client, mock_get_tenancy
    ):
        mock_get_tenancy.return_value = "ocid1.compartment.oc1..test"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # list two PDs
        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.recovery.models.ProtectedDatabaseSummary(id="pd1"),
            oci.recovery.models.ProtectedDatabaseSummary(id="pd2"),
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_protected_databases.return_value = mock_list_response

        # get each with different health
        mock_get_pd_resp1 = create_autospec(oci.response.Response)
        mock_get_pd_resp1.data = oci.recovery.models.ProtectedDatabase(
            id="pd1", health="PROTECTED"
        )
        mock_get_pd_resp2 = create_autospec(oci.response.Response)
        mock_get_pd_resp2.data = oci.recovery.models.ProtectedDatabase(
            id="pd2", health="WARNING"
        )
        mock_client.get_protected_database.side_effect = [
            mock_get_pd_resp1,
            mock_get_pd_resp2,
        ]

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "summarize_protected_database_health",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content

            assert result["protected"] == 1
            assert result["warning"] == 1
            assert result["alert"] == 0
            assert result["total"] == 2

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_summarize_protected_database_redo_status(
        self, mock_get_client, mock_get_tenancy
    ):
        mock_get_tenancy.return_value = "ocid1.compartment.oc1..test"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.recovery.models.ProtectedDatabaseSummary(id="pd1"),
            oci.recovery.models.ProtectedDatabaseSummary(id="pd2"),
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_protected_databases.return_value = mock_list_response

        # get PDs with redo shipped enabled/disabled
        pd1 = oci.recovery.models.ProtectedDatabase(id="pd1")
        pd1.is_redo_logs_shipped = True
        pd2 = oci.recovery.models.ProtectedDatabase(id="pd2")
        pd2.is_redo_logs_shipped = False
        mock_get_pd_resp1 = create_autospec(oci.response.Response)
        mock_get_pd_resp1.data = pd1
        mock_get_pd_resp2 = create_autospec(oci.response.Response)
        mock_get_pd_resp2.data = pd2
        mock_client.get_protected_database.side_effect = [
            mock_get_pd_resp1,
            mock_get_pd_resp2,
        ]

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "summarize_protected_database_redo_status",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content

            assert result["enabled"] == 1
            assert result["disabled"] == 1
            assert result["total"] == 2

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_summarize_backup_space_used(self, mock_get_client, mock_get_tenancy):
        mock_get_tenancy.return_value = "ocid1.compartment.oc1..test"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        pd1_summary = oci.recovery.models.ProtectedDatabaseSummary(
            id="pd1", lifecycle_state="ACTIVE"
        )
        pd2_summary = oci.recovery.models.ProtectedDatabaseSummary(
            id="pd2", lifecycle_state="ACTIVE"
        )
        mock_list_response.data = [pd1_summary, pd2_summary]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_protected_databases.return_value = mock_list_response
        # Fallback path for metrics at summary level
        pd1_summary.metrics = {"backup_space_used_in_gbs": 10.5}
        pd2_summary.metrics = {"backup_space_used_in_gbs": 4.5}

        # PD1 metrics 10.5 GB, PD2 metrics 4.5 GB
        pd1 = oci.recovery.models.ProtectedDatabase(id="pd1")
        pd1.metrics = {"backup_space_used_in_gbs": 10.5}
        pd2 = oci.recovery.models.ProtectedDatabase(id="pd2")
        pd2.metrics = {"backup_space_used_in_gbs": 4.5}

        mock_get_pd_resp1 = create_autospec(oci.response.Response)
        mock_get_pd_resp1.data = pd1
        mock_get_pd_resp2 = create_autospec(oci.response.Response)
        mock_get_pd_resp2.data = pd2
        mock_client.get_protected_database.side_effect = [
            mock_get_pd_resp1,
            mock_get_pd_resp2,
        ]

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "summarize_backup_space_used",
                {
                    "compartment_id": "ocid1.compartment.oc1..test",
                    "region": "us-ashburn-1",
                },
            )
            result = call_tool_result.structured_content

        total_scanned = result.get("total_databases_scanned") or result.get(
            "totalDatabasesScanned"
        )
        sum_gb = result.get("sum_backup_space_used_in_gbs") or result.get(
            "sumBackupSpaceUsedInGBs"
        )
        assert abs(sum_gb - 15.0) < 1e-9
        assert total_scanned == 2

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_monitoring_client")
    async def test_get_recovery_service_metrics(self, mock_get_monitoring_client):
        mock_client = MagicMock()
        mock_get_monitoring_client.return_value = mock_client

        # Prepare a fake series with aggregated datapoints
        dp1 = SimpleNamespace(timestamp="2024-01-01T00:00:00Z", value=1.0)
        dp2 = SimpleNamespace(timestamp="2024-01-01T00:01:00Z", value=2.0)
        series = SimpleNamespace(
            dimensions={"resourceId": "pd1"}, aggregated_datapoints=[dp1, dp2]
        )

        mock_metrics_response = create_autospec(oci.response.Response)
        mock_metrics_response.data = [series]
        mock_client.summarize_metrics_data.return_value = mock_metrics_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_recovery_service_metrics",
                {
                    "compartment_id": "ocid1.compartment.oc1..test",
                    "start_time": "2024-01-01T00:00:00Z",
                    "end_time": "2024-01-01T00:05:00Z",
                    "metricName": "SpaceUsedForRecoveryWindow",
                    "resolution": "1m",
                    "aggregation": "mean",
                    "protected_database_id": "pd1",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["dimensions"]["resourceId"] == "pd1"
            assert len(result[0]["datapoints"]) == 2
            assert result[0]["datapoints"][0]["value"] == 1.0

class TestServer:
    def test_http_signer_requires_region(self, monkeypatch):
        monkeypatch.setattr(server, "get_access_token", lambda: SimpleNamespace(token="token"))
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8080")
        monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")

        with pytest.raises(RuntimeError, match="OCI_REGION"):
            server._get_http_config_and_signer()

    @patch("oracle.oci_recovery_mcp_server.server.OCIProvider")
    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run, mock_provider):
        mock_env = {
            "ORACLE_MCP_HOST": "127.0.0.1",
            "ORACLE_MCP_PORT": "8080",
            "IDCS_DOMAIN": "idcs.example.com",
            "IDCS_CLIENT_ID": "client-id",
            "IDCS_CLIENT_SECRET": "client-secret",
            "IDCS_AUDIENCE": "mcp-audience",
            "ORACLE_MCP_BASE_URL": "http://127.0.0.1:8080",
        }
        # Return configured values for known keys, and default for others
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)
        mock_provider.return_value = MagicMock()

        import oracle.oci_recovery_mcp_server.server as server

        server.main()
        mock_provider.assert_called_once_with(
            config_url="https://idcs.example.com/.well-known/openid-configuration",
            client_id="client-id",
            client_secret="client-secret",
            audience="mcp-audience",
            required_scopes=f"openid profile email oci_mcp.{server.__project__.removeprefix('oracle.oci-').removesuffix('-mcp-server').replace('-', '_')}.invoke".split(),
            base_url="http://127.0.0.1:8080",
        )
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=int(mock_env["ORACLE_MCP_PORT"]),
        )

    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        # Return None for host/port keys, otherwise pass through default (for log dir/file)
        mock_getenv.side_effect = lambda k, d=None: (
            None if k in ("ORACLE_MCP_HOST", "ORACLE_MCP_PORT") else d
        )

        import oracle.oci_recovery_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {"ORACLE_MCP_HOST": "127.0.0.1"}
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)

        import oracle.oci_recovery_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {"ORACLE_MCP_PORT": "8080"}
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)

        import oracle.oci_recovery_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
