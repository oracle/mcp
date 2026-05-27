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
        list_resp.has_next_page = False
        list_resp.next_page = None
        mock_client.list_databases.return_value = list_resp

        # Enrichment path: get_database() to fill db_backup_config if missing
        get_resp = create_autospec(oci.response.Response)
        get_resp.data = {
            "id": "db1",
            "db_backup_config": {"is_auto_backup_enabled": True},
        }
        mock_client.get_database.return_value = get_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_databases",
                {
                    "compartment_id": "ocid1.compartment.oc1..test",
                    "db_home_id": "home1",
                },
            )
            result = call_tool_result.structured_content["result"]

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
            call_tool_result = await client.call_tool(
                "get_database",
                {"database_id": "db1"},
            )
            result = call_tool_result.structured_content

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
        list_resp.has_next_page = False
        list_resp.next_page = None
        mock_client.list_backups.return_value = list_resp

        get_db_resp = create_autospec(oci.response.Response)
        get_db_resp.data = {"id": "db1", "db_unique_name": "DB1_UNQ"}
        mock_client.get_database.return_value = get_db_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_backups",
                {"database_id": "db1"},
            )
            result = call_tool_result.structured_content["result"]

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "b1"
        assert result[0]["db_unique_name"] == "DB1_UNQ"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_get_backup(self, mock_get_db_client):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        get_resp = create_autospec(oci.response.Response)
        get_resp.data = {"id": "b1", "database_id": "db1"}
        mock_client.get_backup.return_value = get_resp

        get_db_resp = create_autospec(oci.response.Response)
        get_db_resp.data = {
            "id": "db1",
            "db_unique_name": "DB1_UNQ",
            "db_backup_config": {
                "backup_destination_details": [{"type": "OBJECT_STORE"}]
            },
        }
        mock_client.get_database.return_value = get_db_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_backup",
                {"backup_id": "b1"},
            )
            result = call_tool_result.structured_content

        assert result["id"] == "b1"
        assert result["db_unique_name"] == "DB1_UNQ"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_work_request_client")
    async def test_list_restore(self, mock_get_wr_client):
        mock_client = MagicMock()
        mock_get_wr_client.return_value = mock_client

        list_resp = create_autospec(oci.response.Response)
        list_resp.data = SimpleNamespace(
            items=[
                {"id": "wr1", "operation_type": "Restore Database", "status": "SUCCEEDED"},
                {"id": "wr2", "operation_type": "Create Backup", "status": "SUCCEEDED"},
            ]
        )
        list_resp.has_next_page = False
        list_resp.next_page = None
        mock_client.list_work_requests.return_value = list_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_restore",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "wr1"
        assert result[0]["operation_type"] == "Restore Database"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_create_backup(self, mock_get_db_client):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        create_resp = create_autospec(oci.response.Response)
        create_resp.data = {
            "id": "b-created",
            "database_id": "db1",
            "display_name": "Manual Backup",
            "type": "FULL",
        }
        mock_client.create_backup.return_value = create_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "create_backup",
                {
                    "database_id": "db1",
                    "display_name": "Manual Backup",
                    "retention_period_in_days": 14,
                },
            )
            result = call_tool_result.structured_content

        assert result["id"] == "b-created"
        kwargs = mock_client.create_backup.call_args.kwargs
        assert kwargs["create_backup_details"].database_id == "db1"
        assert kwargs["create_backup_details"].retention_period_in_days == 14

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_update_backup(self, mock_get_db_client):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        update_resp = create_autospec(oci.response.Response)
        update_resp.data = {
            "id": "b1",
            "database_id": "db1",
            "retention_period_in_days": 30,
        }
        mock_client.update_backup.return_value = update_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "update_backup",
                {
                    "backup_id": "b1",
                    "retention_period_in_days": 30,
                },
            )
            result = call_tool_result.structured_content

        assert result["id"] == "b1"
        kwargs = mock_client.update_backup.call_args.kwargs
        assert kwargs["backup_id"] == "b1"
        assert kwargs["update_backup_details"].retention_period_in_days == 30

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_summarize_protected_database_backup_destination(self, mock_get_db_client):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        list_db_resp = create_autospec(oci.response.Response)
        list_db_resp.data = [
            {
                "id": "db1",
                "db_name": "DB1",
                "db_backup_config": {
                    "is_auto_backup_enabled": True,
                    "backup_destination_details": [
                        {"type": "RECOVERY_SERVICE", "id": "dest1"}
                    ],
                },
            },
            {
                "id": "db2",
                "db_name": "DB2",
                "db_backup_config": {"is_auto_backup_enabled": False},
            },
        ]
        list_db_resp.has_next_page = False
        list_db_resp.next_page = None
        mock_client.list_databases.return_value = list_db_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "summarize_protected_database_backup_destination",
                {
                    "compartment_id": "ocid1.compartment.oc1..test",
                    "db_home_id": "home1",
                },
            )
            result = call_tool_result.structured_content

        assert result["total_databases"] == 2
        assert result["unconfigured_count"] == 1
        assert result["counts_by_destination_type"]["DBRS"] == 1
        assert len(result["items"]) == 2

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_list_db_homes(self, mock_get_db_client):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        list_resp = create_autospec(oci.response.Response)
        list_resp.data = [
            {"id": "home1", "display_name": "Home 1", "lifecycle_state": "AVAILABLE"}
        ]
        list_resp.has_next_page = False
        list_resp.next_page = None
        mock_client.list_db_homes.return_value = list_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_db_homes",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "home1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_get_db_home(self, mock_get_db_client):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        get_resp = create_autospec(oci.response.Response)
        get_resp.data = {"id": "home1", "display_name": "Home 1"}
        mock_client.get_db_home.return_value = get_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_db_home",
                {"db_home_id": "home1"},
            )
            result = call_tool_result.structured_content

        assert result["id"] == "home1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_list_db_systems(self, mock_get_db_client):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        list_resp = create_autospec(oci.response.Response)
        list_resp.data = [
            {"id": "dbs1", "display_name": "DB System 1", "lifecycle_state": "AVAILABLE"}
        ]
        list_resp.has_next_page = False
        list_resp.next_page = None
        mock_client.list_db_systems.return_value = list_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_db_systems",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "dbs1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_get_db_system(self, mock_get_db_client):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        get_resp = create_autospec(oci.response.Response)
        get_resp.data = {"id": "dbs1", "display_name": "DB System 1"}
        mock_client.get_db_system.return_value = get_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_db_system",
                {"db_system_id": "dbs1"},
            )
            result = call_tool_result.structured_content

        assert result["id"] == "dbs1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    @patch("oracle.oci_recovery_mcp_server.server._fetch_db_home_ids_for_compartment")
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_list_databases_compartment_only_discovers_homes(
        self, mock_get_db_client, mock_fetch_homes, mock_get_rec_client
    ):
        db_client = MagicMock()
        rec_client = MagicMock()
        mock_get_db_client.return_value = db_client
        mock_get_rec_client.return_value = rec_client
        mock_fetch_homes.return_value = ["home1"]

        # Recovery PD list returns empty (no policy enrichment needed)
        pd_list_resp = create_autospec(oci.response.Response)
        pd_list_resp.data = SimpleNamespace(items=[])
        pd_list_resp.has_next_page = False
        pd_list_resp.next_page = None
        rec_client.list_protected_databases.return_value = pd_list_resp

        list_resp = create_autospec(oci.response.Response)
        list_resp.data = SimpleNamespace(items=[{"id": "db1", "db_name": "DB1"}])
        list_resp.has_next_page = False
        list_resp.next_page = None
        db_client.list_databases.return_value = list_resp

        get_db_resp = create_autospec(oci.response.Response)
        get_db_resp.data = {"id": "db1", "db_backup_config": {"is_auto_backup_enabled": True}}
        db_client.get_database.return_value = get_db_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_databases",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "db1"
        mock_fetch_homes.assert_called_once_with("ocid1.compartment.oc1..test", region=None)
        # list_databases must be called with the discovered home id
        call_kwargs = db_client.list_databases.call_args.kwargs
        assert call_kwargs.get("db_home_id") == "home1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server._fetch_db_home_ids_for_compartment")
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_list_backups_compartment_path(
        self, mock_get_db_client, mock_fetch_homes
    ):
        db_client = MagicMock()
        mock_get_db_client.return_value = db_client
        mock_fetch_homes.return_value = ["home1"]

        # list_databases returns one AVAILABLE DB with auto-backup enabled
        list_db_resp = create_autospec(oci.response.Response)
        list_db_resp.data = SimpleNamespace(
            items=[
                {
                    "id": "db1",
                    "db_unique_name": "DB1_UNQ",
                    "db_backup_config": {"is_auto_backup_enabled": True},
                }
            ]
        )
        list_db_resp.has_next_page = False
        list_db_resp.next_page = None

        list_bk_resp = create_autospec(oci.response.Response)
        list_bk_resp.data = SimpleNamespace(items=[{"id": "b1", "database_id": "db1"}])
        list_bk_resp.has_next_page = False
        list_bk_resp.next_page = None

        get_db_resp = create_autospec(oci.response.Response)
        get_db_resp.data = {"id": "db1", "db_unique_name": "DB1_UNQ"}

        db_client.list_databases.return_value = list_db_resp
        db_client.list_backups.return_value = list_bk_resp
        db_client.get_database.return_value = get_db_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_backups",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "b1"
        assert result[0]["db_unique_name"] == "DB1_UNQ"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server._fetch_db_home_ids_for_compartment")
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_list_backups_compartment_skips_db_without_autobackup(
        self, mock_get_db_client, mock_fetch_homes
    ):
        db_client = MagicMock()
        mock_get_db_client.return_value = db_client
        mock_fetch_homes.return_value = ["home1"]

        # DB has auto-backup disabled -> no backups should be listed
        list_db_resp = create_autospec(oci.response.Response)
        list_db_resp.data = SimpleNamespace(
            items=[
                {
                    "id": "db1",
                    "db_unique_name": "DB1_UNQ",
                    "db_backup_config": {"is_auto_backup_enabled": False},
                }
            ]
        )
        list_db_resp.has_next_page = False
        list_db_resp.next_page = None

        get_db_resp = create_autospec(oci.response.Response)
        get_db_resp.data = {
            "id": "db1",
            "db_unique_name": "DB1_UNQ",
            "db_backup_config": {"is_auto_backup_enabled": False},
        }

        db_client.list_databases.return_value = list_db_resp
        db_client.get_database.return_value = get_db_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_backups",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

        assert result == []
        db_client.list_backups.assert_not_called()

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_work_request_client")
    async def test_list_restore_empty_when_no_restore_ops(self, mock_get_wr_client):
        mock_client = MagicMock()
        mock_get_wr_client.return_value = mock_client

        list_resp = create_autospec(oci.response.Response)
        list_resp.data = SimpleNamespace(
            items=[
                {"id": "wr1", "operation_type": "Create Backup", "status": "SUCCEEDED"},
                {"id": "wr2", "operation_type": "DELETE_PROTECTED_DATABASE", "status": "SUCCEEDED"},
            ]
        )
        list_resp.has_next_page = False
        list_resp.next_page = None
        mock_client.list_work_requests.return_value = list_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_restore",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

        assert result == []

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_update_backup_no_fields_raises(self, mock_get_db_client):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        with pytest.raises(Exception, match="No update fields provided"):
            async with Client(mcp) as client:
                await client.call_tool(
                    "update_backup",
                    {"backup_id": "b1"},
                )

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_summarize_backup_destination_with_last_backup_time(
        self, mock_get_db_client
    ):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        list_db_resp = create_autospec(oci.response.Response)
        list_db_resp.data = [
            {
                "id": "db1",
                "db_name": "DB1",
                "db_backup_config": {
                    "is_auto_backup_enabled": True,
                    "backup_destination_details": [
                        {"type": "OBJECT_STORE", "id": "dest1"}
                    ],
                },
            }
        ]
        list_db_resp.has_next_page = False
        list_db_resp.next_page = None
        mock_client.list_databases.return_value = list_db_resp

        bk_resp = create_autospec(oci.response.Response)
        bk_resp.data = SimpleNamespace(
            items=[SimpleNamespace(time_ended="2024-06-01T10:00:00Z")]
        )
        bk_resp.has_next_page = False
        mock_client.list_backups.return_value = bk_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "summarize_protected_database_backup_destination",
                {
                    "compartment_id": "ocid1.compartment.oc1..test",
                    "db_home_id": "home1",
                    "include_last_backup_time": True,
                },
            )
            result = call_tool_result.structured_content

        assert result["total_databases"] == 1
        assert result["counts_by_destination_type"]["OBJECT_STORE"] == 1
        items = result["items"]
        assert len(items) == 1
        assert items[0]["last_backup_time"] == "2024-06-01T10:00:00Z"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_database_client")
    async def test_list_db_homes_fetch_child_compartments_dedup(
        self, mock_get_db_client
    ):
        mock_client = MagicMock()
        mock_get_db_client.return_value = mock_client

        # Same home returned from two list calls (simulating two compartments)
        list_resp = create_autospec(oci.response.Response)
        list_resp.data = [
            {"id": "home1", "display_name": "Home 1", "lifecycle_state": "AVAILABLE"}
        ]
        list_resp.has_next_page = False
        list_resp.next_page = None
        mock_client.list_db_homes.return_value = list_resp

        with patch(
            "oracle.oci_recovery_mcp_server.server._compartment_ids_for_tool",
            return_value=["comp1", "comp2"],
        ):
            async with Client(mcp) as client:
                call_tool_result = await client.call_tool(
                    "list_db_homes",
                    {
                        "compartment_id": "ocid1.compartment.oc1..test",
                        "fetch_for_child_compartment": True,
                    },
                )
                result = call_tool_result.structured_content["result"]

        # Dedup should collapse the duplicate home1 from two compartments to one
        assert len(result) == 1
        assert result[0]["id"] == "home1"

