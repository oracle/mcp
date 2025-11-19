from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.database_mcp_server.server import mcp


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_application_vips(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_application_vips.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_application_vips",
            {
                "compartment_id": "ocid1.compartment.sampleCompartmentId",
                "cloud_vm_cluster_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_application_vips.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_container_database_dataguard_associations(
    mock_get_client,
):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_container_database_dataguard_associations.return_value = (
        mock_response
    )

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_container_database_dataguard_associations",
            {
                "autonomous_container_database_id": "ocid1.autonomouscontainer.sampleDatabaseId"
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_container_database_dataguard_associations.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_container_database_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_container_database_versions.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_container_database_versions",
            {
                "compartment_id": "ocid1.compartment.sampleCompartmentId",
                "service_component": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_container_database_versions.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_container_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_container_databases.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_container_databases",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_container_databases.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_backups(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_database_backups.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_database_backups",
            {},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_database_backups.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_character_sets(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_database_character_sets.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_database_character_sets",
            {},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_database_character_sets.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_clones(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_database_clones.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_database_clones",
            {
                "compartment_id": "ocid1.compartment.sampleCompartmentId",
                "autonomous_database_id": "ocid1.autonomous.sampleDatabaseId",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_database_clones.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_dataguard_associations(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_database_dataguard_associations.return_value = (
        mock_response
    )

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_database_dataguard_associations",
            {"autonomous_database_id": "ocid1.autonomous.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_database_dataguard_associations.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_peers(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_database_peers.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_database_peers",
            {"autonomous_database_id": "ocid1.autonomous.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_database_peers.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_refreshable_clones(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_database_refreshable_clones.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_database_refreshable_clones",
            {"autonomous_database_id": "ocid1.autonomous.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_database_refreshable_clones.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_software_images(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_database_software_images.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_database_software_images",
            {
                "compartment_id": "ocid1.compartment.sampleCompartmentId",
                "image_shape_family": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_database_software_images.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_databases.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_databases",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_databases.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_db_preview_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_db_preview_versions.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_db_preview_versions",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_db_preview_versions.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_db_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_db_versions.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_db_versions",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_db_versions.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_virtual_machines(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_virtual_machines.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_virtual_machines",
            {
                "compartment_id": "ocid1.compartment.sampleCompartmentId",
                "autonomous_vm_cluster_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_virtual_machines.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_autonomous_vm_clusters(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_autonomous_vm_clusters.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_autonomous_vm_clusters",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_autonomous_vm_clusters.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_backup_destination(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_backup_destination.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_backup_destination",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_backup_destination.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_backups(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_backups.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_backups",
            {},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_backups.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_cloud_autonomous_vm_clusters(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_cloud_autonomous_vm_clusters.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_cloud_autonomous_vm_clusters",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_cloud_autonomous_vm_clusters.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_cloud_exadata_infrastructures(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_cloud_exadata_infrastructures.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_cloud_exadata_infrastructures",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_cloud_exadata_infrastructures.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_cloud_vm_cluster_updates(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_cloud_vm_cluster_updates.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_cloud_vm_cluster_updates",
            {"cloud_vm_cluster_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_cloud_vm_cluster_updates.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_cloud_vm_clusters(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_cloud_vm_clusters.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_cloud_vm_clusters",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_cloud_vm_clusters.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_console_connections(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_console_connections.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_console_connections",
            {"db_node_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_console_connections.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_console_histories(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_console_histories.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_console_histories",
            {"db_node_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_console_histories.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_container_database_patches(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_container_database_patches.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_container_database_patches",
            {
                "autonomous_container_database_id": "ocid1.autonomouscontainer.sampleDatabaseId",
                "compartment_id": "ocid1.compartment.sampleCompartmentId",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_container_database_patches.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_data_guard_associations(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_data_guard_associations.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_data_guard_associations",
            {"database_id": "ocid1.database.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_data_guard_associations.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_database_software_images(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_database_software_images.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_database_software_images",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_database_software_images.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_databases.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_databases",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_databases.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_db_home_patch_history_entries(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_db_home_patch_history_entries.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_db_home_patch_history_entries",
            {"db_home_id": "ocid1.dbhome.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_db_home_patch_history_entries.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_db_home_patches(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_db_home_patches.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_db_home_patches",
            {"db_home_id": "ocid1.dbhome.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_db_home_patches.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_db_homes(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_db_homes.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_db_homes",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_db_homes.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_db_nodes(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_db_nodes.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_db_nodes",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_db_nodes.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_db_servers(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_db_servers.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_db_servers",
            {
                "compartment_id": "ocid1.compartment.sampleCompartmentId",
                "exadata_infrastructure_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_db_servers.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_db_system_compute_performances(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_db_system_compute_performances.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_db_system_compute_performances",
            {},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_db_system_compute_performances.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_db_system_patches(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_db_system_patches.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_db_system_patches",
            {"db_system_id": "ocid1.dbsystem.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_db_system_patches.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_db_system_shapes(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_db_system_shapes.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_db_system_shapes",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_db_system_shapes.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_db_system_storage_performances(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_db_system_storage_performances.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_db_system_storage_performances",
            {"storage_management": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_db_system_storage_performances.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_db_systems(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_db_systems.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_db_systems",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_db_systems.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_db_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_db_versions.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_db_versions",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_db_versions.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_exadata_infrastructures(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_exadata_infrastructures.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_exadata_infrastructures",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_exadata_infrastructures.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_exadb_vm_cluster_updates(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_exadb_vm_cluster_updates.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_exadb_vm_cluster_updates",
            {"exadb_vm_cluster_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_exadb_vm_cluster_updates.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_exadb_vm_clusters(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_exadb_vm_clusters.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_exadb_vm_clusters",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_exadb_vm_clusters.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_exascale_db_storage_vaults(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_exascale_db_storage_vaults.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_exascale_db_storage_vaults",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_exascale_db_storage_vaults.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_execution_actions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_execution_actions.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_execution_actions",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_execution_actions.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_execution_windows(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_execution_windows.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_execution_windows",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_execution_windows.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_external_container_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_external_container_databases.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_external_container_databases",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_external_container_databases.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_external_database_connectors(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_external_database_connectors.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_external_database_connectors",
            {
                "compartment_id": "ocid1.compartment.sampleCompartmentId",
                "external_database_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_external_database_connectors.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_external_non_container_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_external_non_container_databases.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_external_non_container_databases",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_external_non_container_databases.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_external_pluggable_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_external_pluggable_databases.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_external_pluggable_databases",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_external_pluggable_databases.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_flex_components(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_flex_components.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_flex_components",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_flex_components.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_gi_version_minor_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_gi_version_minor_versions.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_gi_version_minor_versions",
            {"version": "19c"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_gi_version_minor_versions.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_gi_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_gi_versions.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_gi_versions",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_gi_versions.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_key_stores(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_key_stores.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_key_stores",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_key_stores.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_maintenance_run_history(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_maintenance_run_history.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_maintenance_run_history",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_maintenance_run_history.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_maintenance_runs(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_maintenance_runs.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_maintenance_runs",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_maintenance_runs.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_oneoff_patches(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_oneoff_patches.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_oneoff_patches",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_oneoff_patches.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_pluggable_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_pluggable_databases.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_pluggable_databases",
            {},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_pluggable_databases.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_scheduled_actions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_scheduled_actions.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_scheduled_actions",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_scheduled_actions.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_scheduling_plans(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_scheduling_plans.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_scheduling_plans",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_scheduling_plans.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_scheduling_policies(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_scheduling_policies.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_scheduling_policies",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_scheduling_policies.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_scheduling_windows(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_scheduling_windows.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_scheduling_windows",
            {"scheduling_policy_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_scheduling_windows.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_system_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_system_versions.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_system_versions",
            {
                "compartment_id": "ocid1.compartment.sampleCompartmentId",
                "shape": "VM.Standard2.1",
                "gi_version": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_system_versions.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_vm_cluster_networks(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_vm_cluster_networks.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_vm_cluster_networks",
            {
                "exadata_infrastructure_id": "sampleValue",
                "compartment_id": "ocid1.compartment.sampleCompartmentId",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_vm_cluster_networks.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_vm_cluster_patches(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_vm_cluster_patches.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_vm_cluster_patches",
            {"vm_cluster_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_vm_cluster_patches.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_vm_cluster_updates(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_vm_cluster_updates.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_vm_cluster_updates",
            {"vm_cluster_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_vm_cluster_updates.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_list_vm_clusters(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.list_vm_clusters.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "list_vm_clusters",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.list_vm_clusters.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_resource_pool_shapes(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.resource_pool_shapes.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "resource_pool_shapes",
            {},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.resource_pool_shapes.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_delete_pluggable_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.delete_pluggable_database.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "delete_pluggable_database",
            {"pluggable_database_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.delete_pluggable_database.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_get_pluggable_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_pluggable_database.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_pluggable_database",
            {"pluggable_database_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_pluggable_database.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.database_mcp_server.server.get_database_client")
async def test_update_pluggable_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.update_pluggable_database.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "update_pluggable_database",
            {
                "pluggable_database_id": "sampleValue",
                "update_pluggable_database_details": {},
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.update_pluggable_database.assert_called_once()
