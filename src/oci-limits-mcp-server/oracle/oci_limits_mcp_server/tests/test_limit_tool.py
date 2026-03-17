"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_limits_mcp_server.server import mcp


class TestLimitsTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    async def test_list_services(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = [
            oci.limits.models.ServiceSummary(name="service1", description="Service 1")
        ]
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_services.return_value = mock_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_services",
                    {
                        "compartment_id": "ocid1.compartment.oc1..xxxx",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "service1"

    @pytest.mark.asyncio
    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    async def test_list_limit_definitions(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = [
            oci.limits.models.LimitDefinitionSummary(
                name="limit1", service_name="service1", description="Limit 1"
            )
        ]
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_limit_definitions.return_value = mock_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_limit_definitions",
                    {
                        "compartment_id": "ocid1.compartment.oc1..xxxx",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "limit1"

    @pytest.mark.asyncio
    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    async def test_list_limit_value(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = [
            oci.limits.models.LimitValueSummary(
                name="limit_value1", scope_type="GLOBAL", value=10
            )
        ]
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_limit_values.return_value = mock_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_limit_value",
                    {
                        "compartment_id": "ocid1.compartment.oc1..xxxx",
                        "service_name": "service1",
                        "name": "limit_value1",
                        "scope_type": "GLOBAL",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "limit_value1"

    @pytest.mark.asyncio
    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    async def test_get_resource_availability_ad_scope(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_limit_definition = create_autospec(
            oci.limits.models.LimitDefinitionSummary
        )
        mock_limit_definition.is_resource_availability_supported = True
        mock_limit_definition.scope_type = "AD"

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = [mock_limit_definition]
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_limit_definitions.return_value = mock_response

        # Simulate that the tool returns a redirect/hint to identity server for AD lists
        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_resource_availability",
                {
                    "service_name": "service1",
                    "limit_name": "limit1",
                    "compartment_id": "ocid1.compartment.oc1..xxxx",
                },
            )

            result_obj = result.structured_content["result"]
            assert isinstance(result_obj, list)
            assert "redirect" in result_obj[0] or "message" in result_obj[0]
            assert "identity" in result_obj[0].get(
                "message", ""
            ) or "list_availability_domains" in str(result_obj[0])

            # Optionally check that the redirect/hint is well-formed
            if "redirect" in result_obj[0]:
                redirect = result_obj[0]["redirect"]
                assert redirect["server"].endswith("identity-mcp-server")
                assert redirect["tool"] == "list_availability_domains"

    @pytest.mark.asyncio
    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    async def test_get_resource_availability_non_ad_scope(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_limit_definition = create_autospec(
            oci.limits.models.LimitDefinitionSummary
        )
        mock_limit_definition.is_resource_availability_supported = True
        mock_limit_definition.scope_type = "REGION"

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = [mock_limit_definition]
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_limit_definitions.return_value = mock_response

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = oci.limits.models.ResourceAvailability(
            used=10, available=100
        )
        mock_client.get_resource_availability.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_resource_availability",
                {
                    "service_name": "service1",
                    "limit_name": "limit1",
                    "compartment_id": "ocid1.compartment.oc1..xxxx",
                },
            )

            assert len(result.structured_content["result"]) == 1
            assert result.structured_content["result"][0]["used"] == 10
            assert result.structured_content["result"][0]["available"] == 100
