"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_identity_mcp_server.server import mcp


class TestIdentityTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    async def test_list_compartments(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.identity.models.Compartment(
                id="compartment1",
                compartment_id="compartment1",
                name="Compartment 1",
                description="Test compartment",
                lifecycle_state="ACTIVE",
                time_created="1970-01-01T00:00:00",
            )
        ]
        mock_client.list_compartments.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_compartments",
                    {
                        "tenancy_id": "test_tenancy",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "compartment1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    async def test_list_availability_domains(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.identity.models.AvailabilityDomain(
                id="ad1",
                name="AD-1",
                compartment_id="compartment1",
            )
        ]
        mock_client.list_availability_domains.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_availability_domains",
                    {
                        "tenancy_id": "test_tenancy",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "ad1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    async def test_get_tenancy_info(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.identity.models.Tenancy(
            id="tenancy1",
            name="Tenancy 1",
            description="Test tenancy",
            home_region_key="PHX",
        )
        mock_client.get_tenancy.return_value = mock_get_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_tenancy_info",
                    {
                        "tenancy_id": "test_tenancy",
                    },
                )
            ).data

            assert result["id"] == "tenancy1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    async def test_get_current_tenancy(self, mock_config_from_file, mock_get_client):
        mock_config_from_file.return_value = {"tenancy": "test_tenancy"}
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = MagicMock(
            id="tenancy1",
            name="Tenancy 1",
            description="Test tenancy",
            home_region_key="PHX",
        )
        mock_client.get_tenancy.return_value = mock_get_response

        async with Client(mcp) as client:
            result = (await client.call_tool("get_current_tenancy", {})).data

            assert result["id"] == "tenancy1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    async def test_create_auth_token(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_create_response = create_autospec(oci.response.Response)
        mock_create_response.data = oci.identity.models.AuthToken(
            token="token1", description="Test token", lifecycle_state="ACTIVE"
        )
        mock_client.create_auth_token.return_value = mock_create_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "create_auth_token",
                    {
                        "user_id": "test_user",
                    },
                )
            ).data

            assert result["token"] == "token1"

    @pytest.mark.asyncio
    @patch("oracle.oci_identity_mcp_server.server.get_identity_client")
    @patch("oracle.oci_identity_mcp_server.server.oci.config.from_file")
    async def test_get_current_user(self, mock_config_from_file, mock_get_client):
        mock_config_from_file.return_value = {"user": "test_user"}
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = MagicMock(
            id="user1", name="User 1", description="Test user"
        )
        mock_client.get_user.return_value = mock_get_response

        async with Client(mcp) as client:
            result = (await client.call_tool("get_current_user", {})).data

            assert result["id"] == "user1"
