"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from datetime import UTC, datetime
from unittest.mock import MagicMock, create_autospec, mock_open, patch

import fastmcp.exceptions
import oci
import pytest
from fastmcp import Client
from oracle.oci_jms_mcp_server import server
from oracle.oci_jms_mcp_server.server import mcp


class TestJmsTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_fleets_paginates(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response_page_1 = create_autospec(oci.response.Response)
        response_page_1.data = oci.jms.models.FleetCollection(
            items=[
                oci.jms.models.FleetSummary(id="fleet1", display_name="Fleet 1"),
            ]
        )
        response_page_1.has_next_page = True
        response_page_1.next_page = "token"

        response_page_2 = create_autospec(oci.response.Response)
        response_page_2.data = oci.jms.models.FleetCollection(
            items=[
                oci.jms.models.FleetSummary(id="fleet2", display_name="Fleet 2"),
            ]
        )
        response_page_2.has_next_page = False
        response_page_2.next_page = None

        mock_client.list_fleets.side_effect = [response_page_1, response_page_2]

        async with Client(mcp) as client:
            result = (
                await client.call_tool("list_fleets", {"compartment_id": "ocid1.compartment.oc1..test"})
            ).structured_content["result"]

            assert [item["id"] for item in result] == ["fleet1", "fleet2"]
            assert "lifecycle_state" not in mock_client.list_fleets.call_args.kwargs

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_fleets_normalizes_lifecycle_state(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.FleetCollection(
            items=[oci.jms.models.FleetSummary(id="fleet1", display_name="Fleet 1")]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.list_fleets.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_fleets",
                    {
                        "compartment_id": "ocid1.compartment.oc1..test",
                        "lifecycle_state": "needs-attention",
                    },
                )
            ).structured_content["result"]

            assert result[0]["id"] == "fleet1"
            assert (
                mock_client.list_fleets.call_args.kwargs["lifecycle_state"] == "NEEDS_ATTENTION"
            )

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_fleets_normalizes_sort_order(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.FleetCollection(
            items=[oci.jms.models.FleetSummary(id="fleet1", display_name="Fleet 1")]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.list_fleets.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_fleets",
                    {
                        "compartment_id": "ocid1.compartment.oc1..test",
                        "sort_order": "desc",
                    },
                )
            ).structured_content["result"]

            assert result[0]["id"] == "fleet1"
            assert mock_client.list_fleets.call_args.kwargs["sort_order"] == "DESC"

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_fleets_ignores_blank_lifecycle_state(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.FleetCollection(
            items=[oci.jms.models.FleetSummary(id="fleet1", display_name="Fleet 1")]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.list_fleets.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_fleets",
                    {
                        "compartment_id": "ocid1.compartment.oc1..test",
                        "lifecycle_state": "   ",
                    },
                )
            ).structured_content["result"]

            assert result[0]["id"] == "fleet1"
            assert "lifecycle_state" not in mock_client.list_fleets.call_args.kwargs

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_fleets_normalizes_sort_by(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.FleetCollection(
            items=[oci.jms.models.FleetSummary(id="fleet1", display_name="Fleet 1")]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.list_fleets.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_fleets",
                    {
                        "compartment_id": "ocid1.compartment.oc1..test",
                        "sort_by": "time_created",
                    },
                )
            ).structured_content["result"]

            assert result[0]["id"] == "fleet1"
            assert mock_client.list_fleets.call_args.kwargs["sort_by"] == "timeCreated"

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_fleets_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_fleets.side_effect = oci.exceptions.ServiceError(
            status=500,
            code="InternalServerError",
            message="Internal server error",
            opc_request_id="req",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError):
                await client.call_tool("list_fleets", {"compartment_id": "ocid1.compartment.oc1..test"})

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_get_fleet(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.Fleet(id="fleet1", display_name="Fleet 1")
        mock_client.get_fleet.return_value = response

        async with Client(mcp) as client:
            result = (await client.call_tool("get_fleet", {"fleet_id": "fleet1"})).structured_content
            assert result["id"] == "fleet1"

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_get_fleet_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_fleet.side_effect = oci.exceptions.ServiceError(
            status=404,
            code="NotAuthorizedOrNotFound",
            message="Not found",
            opc_request_id="req",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError):
                await client.call_tool("get_fleet", {"fleet_id": "fleet1"})

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_jms_plugins(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.JmsPluginCollection(
            items=[oci.jms.models.JmsPluginSummary(id="plugin1", hostname="host1")]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.list_jms_plugins.return_value = response

        async with Client(mcp) as client:
            result = (await client.call_tool("list_jms_plugins", {"fleet_id": "fleet1"})).structured_content[
                "result"
            ]
            assert result[0]["id"] == "plugin1"

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_get_jms_plugin(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.JmsPlugin(id="plugin1", hostname="host1")
        mock_client.get_jms_plugin.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool("get_jms_plugin", {"jms_plugin_id": "plugin1"})
            ).structured_content
            assert result["id"] == "plugin1"

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_installation_sites(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.InstallationSiteCollection(
            items=[
                oci.jms.models.InstallationSiteSummary(
                    installation_key="install1",
                    managed_instance_id="mi1",
                    path="/usr/java",
                )
            ]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.list_installation_sites.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool("list_installation_sites", {"fleet_id": "fleet1"})
            ).structured_content["result"]
            assert result[0]["installation_key"] == "install1"

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_installation_sites_normalizes_os_family(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.InstallationSiteCollection(
            items=[
                oci.jms.models.InstallationSiteSummary(
                    installation_key="install1",
                    managed_instance_id="mi1",
                    path="/usr/java",
                )
            ]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.list_installation_sites.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_installation_sites",
                    {"fleet_id": "fleet1", "os_family": ["linux"]},
                )
            ).structured_content["result"]

            assert result[0]["installation_key"] == "install1"
            assert mock_client.list_installation_sites.call_args.kwargs["os_family"] == ["LINUX"]

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_installation_sites_omits_blank_os_family_entries(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.InstallationSiteCollection(
            items=[
                oci.jms.models.InstallationSiteSummary(
                    installation_key="install1",
                    managed_instance_id="mi1",
                    path="/usr/java",
                )
            ]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.list_installation_sites.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_installation_sites",
                    {"fleet_id": "fleet1", "os_family": ["linux", "   "]},
                )
            ).structured_content["result"]

            assert result[0]["installation_key"] == "install1"
            assert mock_client.list_installation_sites.call_args.kwargs["os_family"] == ["LINUX"]

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_installation_sites_omits_os_family_when_only_blank_values(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.InstallationSiteCollection(
            items=[
                oci.jms.models.InstallationSiteSummary(
                    installation_key="install1",
                    managed_instance_id="mi1",
                    path="/usr/java",
                )
            ]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.list_installation_sites.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_installation_sites",
                    {"fleet_id": "fleet1", "os_family": ["   "]},
                )
            ).structured_content["result"]

            assert result[0]["installation_key"] == "install1"
            assert "os_family" not in mock_client.list_installation_sites.call_args.kwargs

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_installation_sites_normalizes_sort_by(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.InstallationSiteCollection(
            items=[
                oci.jms.models.InstallationSiteSummary(
                    installation_key="install1",
                    managed_instance_id="mi1",
                    path="/usr/java",
                )
            ]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.list_installation_sites.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_installation_sites",
                    {"fleet_id": "fleet1", "sort_by": "managed_instance_id"},
                )
            ).structured_content["result"]

            assert result[0]["installation_key"] == "install1"
            assert (
                mock_client.list_installation_sites.call_args.kwargs["sort_by"]
                == "managedInstanceId"
            )

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_get_fleet_agent_configuration(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.FleetAgentConfiguration(
            jre_scan_frequency_in_minutes=60,
            java_usage_tracker_processing_frequency_in_minutes=10,
        )
        mock_client.get_fleet_agent_configuration.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool("get_fleet_agent_configuration", {"fleet_id": "fleet1"})
            ).structured_content
            assert result["jre_scan_frequency_in_minutes"] == 60

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_get_fleet_advanced_feature_configuration(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.FleetAdvancedFeatureConfiguration(
            analytic_namespace="analytics_ns",
            analytic_bucket_name="bucket",
        )
        mock_client.get_fleet_advanced_feature_configuration.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_fleet_advanced_feature_configuration", {"fleet_id": "fleet1"}
                )
            ).structured_content
            assert result["analytic_namespace"] == "analytics_ns"

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_summarize_resource_inventory(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.ResourceInventory(
            active_fleet_count=1,
            managed_instance_count=2,
            jre_count=3,
            installation_count=4,
            application_count=5,
        )
        mock_client.summarize_resource_inventory.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "summarize_resource_inventory",
                    {"compartment_id": "ocid1.compartment.oc1..test"},
                )
            ).structured_content
            assert result["active_fleet_count"] == 1

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_summarize_resource_inventory_omits_blank_time_start(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.ResourceInventory(
            active_fleet_count=1,
            managed_instance_count=2,
            jre_count=3,
            installation_count=4,
            application_count=5,
        )
        mock_client.summarize_resource_inventory.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "summarize_resource_inventory",
                    {
                        "compartment_id": "ocid1.compartment.oc1..test",
                        "time_start": "",
                    },
                )
            ).structured_content

            assert result["active_fleet_count"] == 1
            assert "time_start" not in mock_client.summarize_resource_inventory.call_args.kwargs

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_summarize_managed_instance_usage(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.ManagedInstanceUsageCollection(
            items=[
                oci.jms.models.ManagedInstanceUsage(
                    managed_instance_id="mi1",
                    managed_instance_type="ORACLE_MANAGEMENT_AGENT",
                    hostname="host1",
                )
            ]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.summarize_managed_instance_usage.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool("summarize_managed_instance_usage", {"fleet_id": "fleet1"})
            ).structured_content["result"]
            assert result[0]["managed_instance_id"] == "mi1"

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_summarize_managed_instance_usage_normalizes_fields_and_sort_by(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.ManagedInstanceUsageCollection(
            items=[
                oci.jms.models.ManagedInstanceUsage(
                    managed_instance_id="mi1",
                    managed_instance_type="ORACLE_MANAGEMENT_AGENT",
                    hostname="host1",
                )
            ]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.summarize_managed_instance_usage.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "summarize_managed_instance_usage",
                    {
                        "fleet_id": "fleet1",
                        "fields": ["approximate_jre_count"],
                        "sort_by": "time_first_seen",
                    },
                )
            ).structured_content["result"]

            assert result[0]["managed_instance_id"] == "mi1"
            assert mock_client.summarize_managed_instance_usage.call_args.kwargs["fields"] == [
                "approximateJreCount"
            ]
            assert (
                mock_client.summarize_managed_instance_usage.call_args.kwargs["sort_by"]
                == "timeFirstSeen"
            )

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_summarize_managed_instance_usage_omits_blank_os_family_entries_and_time_end(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.ManagedInstanceUsageCollection(
            items=[
                oci.jms.models.ManagedInstanceUsage(
                    managed_instance_id="mi1",
                    managed_instance_type="ORACLE_MANAGEMENT_AGENT",
                    hostname="host1",
                )
            ]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.summarize_managed_instance_usage.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "summarize_managed_instance_usage",
                    {
                        "fleet_id": "fleet1",
                        "os_family": ["linux", "   "],
                        "time_end": "   ",
                    },
                )
            ).structured_content["result"]

            assert result[0]["managed_instance_id"] == "mi1"
            assert mock_client.summarize_managed_instance_usage.call_args.kwargs["os_family"] == [
                "LINUX"
            ]
            assert "time_end" not in mock_client.summarize_managed_instance_usage.call_args.kwargs

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_summarize_fleet_health_with_issues(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        diagnoses_page = create_autospec(oci.response.Response)
        diagnoses_page.data = oci.jms.models.FleetDiagnosisCollection(
            items=[
                oci.jms.models.FleetDiagnosisSummary(
                    resource_id="resource1",
                    resource_diagnosis="Inventory scan issue",
                )
            ]
        )
        diagnoses_page.has_next_page = False
        diagnoses_page.next_page = None

        error_detail = oci.jms.models.FleetErrorDetails(
            details="Critical agent reporting failure",
            reason="Agent connectivity failure",
            time_last_seen=datetime.now(UTC),
        )
        fleet_errors_page = create_autospec(oci.response.Response)
        fleet_errors_page.data = oci.jms.models.FleetErrorCollection(
            items=[
                oci.jms.models.FleetErrorSummary(
                    fleet_id="fleet1",
                    fleet_name="Fleet 1",
                    errors=[error_detail],
                )
            ]
        )
        fleet_errors_page.has_next_page = False
        fleet_errors_page.next_page = None

        mock_client.list_fleet_diagnoses.return_value = diagnoses_page
        mock_client.list_fleet_errors.return_value = fleet_errors_page

        async with Client(mcp) as client:
            result = (
                await client.call_tool("summarize_fleet_health", {"fleet_id": "fleet1"})
            ).structured_content

            assert result["fleet_id"] == "fleet1"
            assert result["diagnosis_count"] == 1
            assert result["overall_health_status"] == "CRITICAL"
            assert "Inventory scan issue" in result["top_issue_categories"]
            assert "Critical agent reporting failure" in result["top_issue_categories"]
            assert "Check JMS notices for any known service-side issues or advisories." in result[
                "recommended_next_checks"
            ]

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_summarize_fleet_health_healthy(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        diagnoses_page = create_autospec(oci.response.Response)
        diagnoses_page.data = oci.jms.models.FleetDiagnosisCollection(items=[])
        diagnoses_page.has_next_page = False
        diagnoses_page.next_page = None

        fleet_errors_page = create_autospec(oci.response.Response)
        fleet_errors_page.data = oci.jms.models.FleetErrorCollection(items=[])
        fleet_errors_page.has_next_page = False
        fleet_errors_page.next_page = None

        mock_client.list_fleet_diagnoses.return_value = diagnoses_page
        mock_client.list_fleet_errors.return_value = fleet_errors_page

        async with Client(mcp) as client:
            result = (
                await client.call_tool("summarize_fleet_health", {"fleet_id": "fleet1"})
            ).structured_content

            assert result["overall_health_status"] == "HEALTHY"
            assert result["recommended_next_checks"] == []
            assert result["fleet_errors"] == []

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_get_fleet_health_diagnostics_paginates(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        diagnoses_page_1 = create_autospec(oci.response.Response)
        diagnoses_page_1.data = oci.jms.models.FleetDiagnosisCollection(
            items=[oci.jms.models.FleetDiagnosisSummary(resource_id="resource1")]
        )
        diagnoses_page_1.has_next_page = True
        diagnoses_page_1.next_page = "token"

        diagnoses_page_2 = create_autospec(oci.response.Response)
        diagnoses_page_2.data = oci.jms.models.FleetDiagnosisCollection(
            items=[oci.jms.models.FleetDiagnosisSummary(resource_id="resource2")]
        )
        diagnoses_page_2.has_next_page = False
        diagnoses_page_2.next_page = None

        fleet_errors_page = create_autospec(oci.response.Response)
        fleet_errors_page.data = oci.jms.models.FleetErrorCollection(
            items=[oci.jms.models.FleetErrorSummary(fleet_id="fleet1")]
        )
        fleet_errors_page.has_next_page = False
        fleet_errors_page.next_page = None

        mock_client.list_fleet_diagnoses.side_effect = [diagnoses_page_1, diagnoses_page_2]
        mock_client.list_fleet_errors.return_value = fleet_errors_page

        async with Client(mcp) as client:
            result = (
                await client.call_tool("get_fleet_health_diagnostics", {"fleet_id": "fleet1"})
            ).structured_content

            assert result["diagnosis_count"] == 2
            assert result["fleet_error_count"] == 1
            assert [item["resource_id"] for item in result["diagnoses"]] == [
                "resource1",
                "resource2",
            ]

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_summarize_fleet_health_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_fleet_diagnoses.side_effect = oci.exceptions.ServiceError(
            status=500,
            code="InternalServerError",
            message="Internal server error",
            opc_request_id="req",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError):
                await client.call_tool("summarize_fleet_health", {"fleet_id": "fleet1"})

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_jms_notices_normalizes_sort_by_and_time_filters(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = create_autospec(oci.response.Response)
        response.data = oci.jms.models.AnnouncementCollection(
            items=[
                oci.jms.models.AnnouncementSummary(
                    key="announcement1",
                    summary="Planned maintenance",
                    time_released=datetime.now(UTC),
                    url="https://example.com",
                )
            ]
        )
        response.has_next_page = False
        response.next_page = None
        mock_client.list_announcements.return_value = response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_jms_notices",
                    {
                        "summary_contains": "maintenance",
                        "time_start": "2026-03-01T00:00:00Z",
                        "time_end": "2026-03-02T00:00:00Z",
                        "sort_order": "desc",
                        "sort_by": "time_released",
                    },
                )
            ).structured_content["result"]

            assert result[0]["key"] == "announcement1"
            assert mock_client.list_announcements.call_args.kwargs["sort_order"] == "DESC"
            assert mock_client.list_announcements.call_args.kwargs["sort_by"] == "timeReleased"
            assert (
                mock_client.list_announcements.call_args.kwargs["time_start"].isoformat()
                == "2026-03-01T00:00:00+00:00"
            )

    @pytest.mark.asyncio
    @patch("oracle.oci_jms_mcp_server.server.get_jms_client")
    async def test_list_jms_notices_paginates_with_limit(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        page_1 = create_autospec(oci.response.Response)
        page_1.data = oci.jms.models.AnnouncementCollection(
            items=[
                oci.jms.models.AnnouncementSummary(key="announcement1"),
                oci.jms.models.AnnouncementSummary(key="announcement2"),
            ]
        )
        page_1.has_next_page = True
        page_1.next_page = "token"

        page_2 = create_autospec(oci.response.Response)
        page_2.data = oci.jms.models.AnnouncementCollection(
            items=[oci.jms.models.AnnouncementSummary(key="announcement3")]
        )
        page_2.has_next_page = False
        page_2.next_page = None

        mock_client.list_announcements.side_effect = [page_1, page_2]

        async with Client(mcp) as client:
            result = (
                await client.call_tool("list_jms_notices", {"limit": 2})
            ).structured_content["result"]

            assert [item["key"] for item in result] == ["announcement1", "announcement2"]
            assert mock_client.list_announcements.call_count == 1


class TestServerMain:
    @patch("oracle.oci_jms_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {"ORACLE_MCP_HOST": "1.2.3.4", "ORACLE_MCP_PORT": "8888"}
        mock_getenv.side_effect = lambda key: mock_env.get(key)
        server.main()
        mock_mcp_run.assert_called_once_with(transport="http", host="1.2.3.4", port=8888)

    @patch("oracle.oci_jms_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_jms_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {"ORACLE_MCP_HOST": "1.2.3.4"}
        mock_getenv.side_effect = lambda key: mock_env.get(key)
        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_jms_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {"ORACLE_MCP_PORT": "8888"}
        mock_getenv.side_effect = lambda key: mock_env.get(key)
        server.main()
        mock_mcp_run.assert_called_once_with()


class TestGetJmsClient:
    @patch("oracle.oci_jms_mcp_server.server.oci.jms.JavaManagementServiceClient")
    @patch("oracle.oci_jms_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_jms_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_jms_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_jms_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_jms_mcp_server.server.os.getenv")
    def test_get_jms_client(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        mock_getenv.side_effect = lambda key, default=None: (
            "MYPROFILE" if key == "OCI_CONFIG_PROFILE" else default
        )
        config = {"key_file": "/abs/key.pem", "security_token_file": "/abs/token"}
        mock_from_file.return_value = config
        private_key = object()
        mock_load_private_key.return_value = private_key

        result = server.get_jms_client()

        mock_from_file.assert_called_once_with(
            file_location=oci.config.DEFAULT_LOCATION,
            profile_name="MYPROFILE",
        )
        mock_open_file.assert_called_once_with("/abs/token", "r")
        mock_security_token_signer.assert_called_once_with("SECURITY_TOKEN", private_key)
        passed_config = mock_client.call_args[0][0]
        assert passed_config is config
        assert "additional_user_agent" in config
        assert mock_client.call_args.kwargs == {"signer": mock_security_token_signer.return_value}
        assert result == mock_client.return_value

    @patch("oracle.oci_jms_mcp_server.server.oci.jms.JavaManagementServiceClient")
    @patch("oracle.oci_jms_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_jms_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_jms_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_jms_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_jms_mcp_server.server.os.getenv")
    def test_get_jms_client_with_jms_test_environment_override(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        values = {
            "OCI_CONFIG_PROFILE": "MYPROFILE",
            "JMS_TEST_ENVIRONMENT": "DEV-canary",
        }
        mock_getenv.side_effect = lambda key, default=None: values.get(key, default)
        config = {
            "key_file": "/abs/key.pem",
            "security_token_file": "/abs/token",
            "region": "us-ashburn-1",
        }
        mock_from_file.return_value = config
        mock_load_private_key.return_value = object()

        server.get_jms_client()

        assert mock_client.call_args.kwargs == {
            "signer": mock_security_token_signer.return_value,
            "service_endpoint": "https://javamanagement-dev.us-ashburn-1.oci.oc-test.com",
        }

    @patch("oracle.oci_jms_mcp_server.server.oci.jms.JavaManagementServiceClient")
    @patch("oracle.oci_jms_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_jms_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_jms_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_jms_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_jms_mcp_server.server.os.getenv")
    def test_get_jms_client_with_test_endpoint_override(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        values = {
            "JMS_TEST_ENVIRONMENT": "TEST",
        }
        mock_getenv.side_effect = lambda key, default=None: values.get(key, default)
        config = {
            "key_file": "/abs/key.pem",
            "security_token_file": "/abs/token",
            "region": "us-ashburn-1",
        }
        mock_from_file.return_value = config
        mock_load_private_key.return_value = object()

        server.get_jms_client()

        assert mock_client.call_args.kwargs == {
            "signer": mock_security_token_signer.return_value,
            "service_endpoint": "https://javamanagement-test.us-ashburn-1.oci.oc-test.com",
        }

    @patch("oracle.oci_jms_mcp_server.server.oci.jms.JavaManagementServiceClient")
    @patch("oracle.oci_jms_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_jms_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_jms_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_jms_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_jms_mcp_server.server.os.getenv")
    def test_get_jms_client_with_herds_endpoint_override(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        values = {
            "JMS_TEST_ENVIRONMENT": "HERDS",
        }
        mock_getenv.side_effect = lambda key, default=None: values.get(key, default)
        config = {
            "key_file": "/abs/key.pem",
            "security_token_file": "/abs/token",
            "region": "eu-frankfurt-1",
        }
        mock_from_file.return_value = config
        mock_load_private_key.return_value = object()

        server.get_jms_client()

        assert mock_client.call_args.kwargs == {
            "signer": mock_security_token_signer.return_value,
            "service_endpoint": "https://javamanagement-herds.eu-frankfurt-1.oci.rbcloud.oc-test.com",
        }

    @patch("oracle.oci_jms_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_jms_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_jms_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_jms_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_jms_mcp_server.server.os.getenv")
    def test_get_jms_client_rejects_unknown_jms_test_environment(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
    ):
        values = {
            "JMS_TEST_ENVIRONMENT": "BOGUS",
        }
        mock_getenv.side_effect = lambda key, default=None: values.get(key, default)
        mock_from_file.return_value = {
            "key_file": "/abs/key.pem",
            "security_token_file": "/abs/token",
            "region": "us-ashburn-1",
        }
        mock_load_private_key.return_value = object()

        with pytest.raises(ValueError, match="Unsupported JMS_TEST_ENVIRONMENT"):
            server.get_jms_client()

    @patch("oracle.oci_jms_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_jms_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_jms_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_jms_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_jms_mcp_server.server.os.getenv")
    def test_get_jms_client_requires_region_for_jms_test_environment(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
    ):
        values = {
            "JMS_TEST_ENVIRONMENT": "DEV2",
        }
        mock_getenv.side_effect = lambda key, default=None: values.get(key, default)
        mock_from_file.return_value = {
            "key_file": "/abs/key.pem",
            "security_token_file": "/abs/token",
        }
        mock_load_private_key.return_value = object()

        with pytest.raises(ValueError, match="OCI config does not contain a region"):
            server.get_jms_client()

    @patch("oracle.oci_jms_mcp_server.server.logger")
    @patch("oracle.oci_jms_mcp_server.server.os.getenv")
    def test_load_oci_config_warns_on_oci_api_mcp_env_aliases(self, mock_getenv, mock_logger):
        values = {
            "OCI_CONFIG": "/Users/test/.oci/config",
            "OCI_PROFILE": "DEFAULT",
        }
        mock_getenv.side_effect = lambda key, default=None: values.get(key, default)

        with patch("oracle.oci_jms_mcp_server.server.oci.config.from_file") as mock_from_file:
            server._load_oci_config()

        mock_from_file.assert_called_once_with(
            file_location=oci.config.DEFAULT_LOCATION,
            profile_name=oci.config.DEFAULT_PROFILE,
        )
        assert mock_logger.warning.call_count == 2

    @patch("oracle.oci_jms_mcp_server.server.open", new_callable=mock_open, read_data="SECURITY_TOKEN\n")
    @patch("oracle.oci_jms_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_jms_mcp_server.server.oci.signer.load_private_key_from_file")
    def test_build_security_token_signer_strips_token(
        self,
        mock_load_private_key,
        mock_security_token_signer,
        mock_open_file,
    ):
        config = {
            "key_file": "/abs/key.pem",
            "security_token_file": "~/.oci/sessions/DEFAULT/token",
        }
        private_key = object()
        mock_load_private_key.return_value = private_key

        server._build_security_token_signer(config)

        mock_open_file.assert_called_once_with(os.path.expanduser(config["security_token_file"]), "r")
        mock_security_token_signer.assert_called_once_with("SECURITY_TOKEN", private_key)
