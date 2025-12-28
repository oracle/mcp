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
from oracle.oci_recovery_mcp_server.server import mcp


class TestRecoveryDatabaseTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_list_databases(self, mock_get_db_client):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        # list_databases() returns a Response with .data.items
        list_resp = create_autospec(oci.response.Response)
        list_resp.data = SimpleNamespace(items=[{"id": "db1", "db_name": "DB1"}])
        mock_client.list_databases.return_value = list_resp

        # Enrichment path: get_database() to fill db_backup_config if missing
        get_resp = create_autospec(oci.response.Response)
        get_resp.data = {
            "id": "db1",
            "db_backup_config": {"is_auto_backup_enabled": True},
        }
        mock_client.get_database.return_value = get_resp

        async with Client(mcp) as client:
            call = await client.call_tool("list_databases", {"db_home_id": "home1"})
            result = call.structured_content["result"]

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "db1"
            # db_backup_config should be present after enrichment
            assert "db_backup_config" in result[0]

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_get_database_sets_protection_policy(
        self, mock_get_db_client, mock_get_rec_client
    ):
        db_client = MagicMock()
        rec_client = MagicMock()
        mock_get_db_client.return_value = db_client
        mock_get_rec_client.return_value = rec_client

        # DB fetch with compartment_id
        db_resp = create_autospec(oci.response.Response)
        db_resp.data = {"id": "db1", "compartment_id": "ocid1.compartment.oc1..comp"}
        db_client.get_database.return_value = db_resp

        # Recovery PD listing returns item with databaseId and protectionPolicyId
        pd_list_resp = create_autospec(oci.response.Response)
        pd_list_resp.has_next_page = False
        pd_list_resp.next_page = None
        pd_list_resp.data = SimpleNamespace(
            items=[{"databaseId": "db1", "protectionPolicyId": "pp1"}]
        )
        rec_client.list_protected_databases.return_value = pd_list_resp

        async with Client(mcp) as client:
            call = await client.call_tool("get_database", {"database_id": "db1"})
            result = call.structured_content
            assert result["id"] == "db1"
            # Enriched field from correlation loop
            assert result.get("protection_policy_id") == "pp1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_list_backups(self, mock_get_db_client):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        list_resp = create_autospec(oci.response.Response)
        list_resp.data = SimpleNamespace(items=[{"id": "b1", "database_id": "db1"}])
        mock_client.list_backups.return_value = list_resp

        async with Client(mcp) as client:
            call = await client.call_tool("list_backups", {})
            result = call.structured_content["result"]
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "b1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_get_backup(self, mock_get_db_client):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        get_resp = create_autospec(oci.response.Response)
        get_resp.data = {"id": "b1", "database_id": "db1"}
        mock_client.get_backup.return_value = get_resp

        async with Client(mcp) as client:
            call = await client.call_tool("get_backup", {"backup_id": "b1"})
            result = call.structured_content
            assert result["id"] == "b1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server._fetch_db_home_ids_for_compartment")
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_summarise_protected_database_backup_destination_dbrs_configured(
        self, mock_get_db_client, mock_get_rec_client, mock_fetch_homes
    ):
        mock_fetch_homes.return_value = ["home1"]

        db_client = MagicMock()
        rec_client = MagicMock()
        mock_get_db_client.return_value = db_client
        mock_get_rec_client.return_value = rec_client

        # One database summary in the discovered DB Home
        list_db_resp = create_autospec(oci.response.Response)
        list_db_resp.data = SimpleNamespace(items=[{"id": "dbA", "db_name": "DBA"}])
        db_client.list_databases.return_value = list_db_resp

        # Full DB details (no backup config required to still detect DBRS)
        get_db_resp = create_autospec(oci.response.Response)
        get_db_resp.data = {"id": "dbA"}
        db_client.get_database.return_value = get_db_resp

        # Minimal non-empty backup list for the quick "has backups" probe path
        list_bk_resp = create_autospec(oci.response.Response)
        list_bk_resp.data = SimpleNamespace(items=[{"id": "bk1"}])
        db_client.list_backups.return_value = list_bk_resp

        # Protected databases listing correlates dbA -> implies DBRS destination
        pd_list_resp = create_autospec(oci.response.Response)
        pd_list_resp.has_next_page = False
        pd_list_resp.next_page = None
        pd_list_resp.data = SimpleNamespace(items=[{"id": "pd1", "databaseId": "dbA"}])
        rec_client.list_protected_databases.return_value = pd_list_resp

        async with Client(mcp) as client:
            call = await client.call_tool(
                "summarise_protected_database_backup_destination",
                {"compartment_id": "ocid1.compartment.oc1..comp"},
            )
            result = call.structured_content

            # Expect 1 total DB, configured under DBRS
            assert result["total_databases"] == 1
            counts = result["counts_by_destination_type"]
            assert isinstance(counts, dict)
            # DBRS should be detected due to Protected Database correlation
            assert counts.get("DBRS", 0) >= 1
