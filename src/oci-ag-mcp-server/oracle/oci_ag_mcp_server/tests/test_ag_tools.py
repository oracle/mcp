import pytest
from unittest.mock import AsyncMock, patch
from fastmcp import Client
import oracle.oci_ag_mcp_server.server as server

class TestAGTools:

    @pytest.mark.asyncio
    @patch("oracle.oci_ag_mcp_server.server.client")
    async def test_health_check(self, mock_client):
        async with Client(server.mcp) as client:
            result = (await client.call_tool("health_check", {})).structured_content
            assert result["status"] == "Healthy"

    @pytest.mark.asyncio
    @patch("oracle.oci_ag_mcp_server.server.client")
    async def test_list_identities(self, mock_client):
        mock_client.list_identities = AsyncMock(
            return_value={"items": [{"id": "id1", "name": "User1"}]}
        )

        async with Client(server.mcp) as client:
            result = (await client.call_tool("list_identities", {})).structured_content
            items = result["result"]

            assert len(items) == 1
            assert items[0]["id"] == "id1"

    @pytest.mark.asyncio
    @patch("oracle.oci_ag_mcp_server.server.client")
    async def test_list_identity_collections(self, mock_client):
        mock_client.list_identity_collections = AsyncMock(
            return_value={"items": [{"id": "col1", "name": "Collection1"}]}
        )

        async with Client(server.mcp) as client:
            result = (await client.call_tool("list_identity_collections", {})).structured_content
            items = result["result"]

            assert len(items) == 1
            assert items[0]["id"] == "col1"

    @pytest.mark.asyncio
    @patch("oracle.oci_ag_mcp_server.server._resolve_identity")
    @patch("oracle.oci_ag_mcp_server.server.client")
    async def test_create_identity_collection(
        self,
        mock_client,
        mock_resolve_identity
    ):
        mock_resolve_identity.return_value = {"id": "id1", "name": "User1"}

        mock_client.create_identity_collection = AsyncMock(
            return_value={"id": "col1", "name": "test"}
        )

        async with Client(server.mcp) as client:
            result = (
                await client.call_tool(
                    "create_identity_collection",
                    {
                        "display_name": "Test Collection",
                        "owner": "User1",
                        "included_identities": ["User1"]
                    }
                )
            ).structured_content

            assert result["id"] == "col1"

    # ---------------- NEW TOOLS ----------------

    @pytest.mark.asyncio
    @patch("oracle.oci_ag_mcp_server.server.client")
    async def test_list_access_bundles(self, mock_client):
        mock_client.list_access_bundles = AsyncMock(
            return_value={"items": [{"id": "b1", "displayName": "Bundle1"}]}
        )

        async with Client(server.mcp) as client:
            result = (await client.call_tool("list_access_bundles", {})).structured_content
            items = result["result"]

            assert len(items) == 1
            assert items[0]["id"] == "b1"

    @pytest.mark.asyncio
    @patch("oracle.oci_ag_mcp_server.server.client")
    async def test_list_orchestrated_systems(self, mock_client):
        mock_client.list_orchestrated_systems = AsyncMock(
            return_value={"items": [{"id": "sys1", "displayName": "System1"}]}
        )

        async with Client(server.mcp) as client:
            result = (await client.call_tool("list_orchestrated_systems", {})).structured_content
            items = result["result"]

            assert len(items) == 1
            assert items[0]["id"] == "sys1"

    @pytest.mark.asyncio
    @patch("oracle.oci_ag_mcp_server.server.client")
    async def test_list_access_requests(self, mock_client):
        mock_client.list_access_requests = AsyncMock(
            return_value={"items": [{"id": "req1", "status": "PENDING"}]}
        )

        async with Client(server.mcp) as client:
            result = (await client.call_tool("list_access_requests", {})).structured_content
            items = result["result"]

            assert len(items) == 1
            assert items[0]["id"] == "req1"

    @pytest.mark.asyncio
    @patch("oracle.oci_ag_mcp_server.server._resolve_access_bundle")
    @patch("oracle.oci_ag_mcp_server.server._resolve_identity")
    @patch("oracle.oci_ag_mcp_server.server.client")
    async def test_create_access_request(
        self,
        mock_client,
        mock_resolve_identity,
        mock_resolve_bundle,
    ):
        mock_resolve_identity.return_value = {"id": "user1", "name": "User1"}
        mock_resolve_bundle.return_value = {"id": "bundle1", "name": "Bundle1"}

        mock_client.create_access_request = AsyncMock(
            return_value={"id": "req1"}
        )

        async with Client(server.mcp) as client:
            result = (
                await client.call_tool(
                    "create_access_request",
                    {
                        "justification": "test",
                        "created_by_user": "User1",
                        "beneficiaries": ["User1"],
                        "access_bundles": ["Bundle1"]
                    }
                )
            ).structured_content

            assert result["id"] == "req1"