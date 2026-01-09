"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastmcp import Client
from oracle.oci_support_mcp_server.server import mcp

from oracle.oci_support_mcp_server.models import (
    Incident,
    IncidentSummary,
    IncidentResourceType,
    ValidationResponse,
    CreateIncident,
)


class TestSupportTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_support_mcp_server.server.get_cims_client")
    async def test_list_incidents(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        # Simulate OCI response with sample IncidentSummary data
        mock_summary = IncidentSummary(key="INC1", compartment_id="test_compartment")
        mock_response.data = [mock_summary]
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_incidents.return_value = mock_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_incidents", {"compartment_id": "test_compartment"}
            )
            result = call_tool_result.structured_content["result"]
            assert isinstance(result, list)
            assert result[0]["key"] == "INC1"

    @pytest.mark.asyncio
    @patch("oracle.oci_support_mcp_server.server.get_cims_client")
    async def test_get_incident(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_incident = Incident(key="INC1", ticket={"severity": "SEV1"})
        mock_response.data = mock_incident
        mock_client.get_incident.return_value = mock_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_incident",
                {"incident_key": "INC1", "compartment_id": "test_compartment"},
            )
            result = call_tool_result.structured_content
            assert result["key"] == "INC1"
            assert result["ticket"]["severity"] == "SEV1"

    @pytest.mark.asyncio
    @patch("oracle.oci_support_mcp_server.server.get_cims_client")
    async def test_create_incident(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_incident = Incident(key="INC1", ticket={"severity": "SEV2"})
        mock_response.data = mock_incident
        mock_client.create_incident.return_value = mock_response

        create_incident_details = CreateIncident(compartment_id="test_compartment")
        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "create_incident", {"create_incident_details": create_incident_details}
            )
            result = call_tool_result.structured_content
            assert result["key"] == "INC1"
            assert result["ticket"]["severity"] == "SEV2"

    @pytest.mark.asyncio
    @patch("oracle.oci_support_mcp_server.server.get_cims_client")
    async def test_list_incident_resource_types(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_res_type = IncidentResourceType(resource_type_key="RT1", name="ResType1")
        # Use model_dump to ensure dict serialization, matching FastMCP output
        mock_response.data = [mock_res_type.model_dump(exclude_none=True)]
        mock_client.list_incident_resource_types.return_value = mock_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_incident_resource_types",
                {"problem_type": "TECH", "compartment_id": "test_compartment"},
            )
            result = call_tool_result.structured_content
            assert isinstance(
                result, dict
            ), f"Expected a dict, got {type(result)}: {result}"
            entries = result.get("result")
            assert isinstance(entries, list), f"'result' is not a list: {entries}"
            assert (
                entries
            ), f"list_incident_resource_types returned empty list: {entries}"
            assert entries[0]["resource_type_key"] == "RT1"
            assert entries[0]["name"] == "ResType1"

    @pytest.mark.asyncio
    @patch("oracle.oci_support_mcp_server.server.get_cims_client")
    async def test_validate_user(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_validation = ValidationResponse(is_valid_user=True)
        mock_response.data = mock_validation
        mock_client.validate_user.return_value = mock_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool("validate_user", {})
            result = call_tool_result.structured_content
            assert "is_valid_user" in result
            assert result["is_valid_user"]
