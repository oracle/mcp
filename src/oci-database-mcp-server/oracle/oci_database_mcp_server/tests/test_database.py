from unittest.mock import MagicMock, create_autospec, mock_open, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_database_mcp_server.server import mcp


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_application_vips(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_container_database_dataguard_associations(
    mock_get_client,
):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_container_database_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_container_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_backups(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_character_sets(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_clones(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_dataguard_associations(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_peers(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_refreshable_clones(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_database_software_images(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_db_preview_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_db_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_virtual_machines(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_autonomous_vm_clusters(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_backup_destination(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_backups(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_cloud_autonomous_vm_clusters(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_cloud_exadata_infrastructures(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_cloud_vm_cluster_updates(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_cloud_vm_clusters(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_console_connections(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_console_histories(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_container_database_patches(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_data_guard_associations(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_database_software_images(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_db_home_patch_history_entries(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_db_home_patches(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_db_homes(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_db_nodes(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_db_servers(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_db_system_compute_performances(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_db_system_patches(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_db_system_shapes(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_db_system_storage_performances(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_db_systems(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_db_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_exadata_infrastructures(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_exadb_vm_cluster_updates(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_exadb_vm_clusters(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_exascale_db_storage_vaults(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_execution_actions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_execution_windows(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_external_container_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_external_database_connectors(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_external_non_container_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_external_pluggable_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_flex_components(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_gi_version_minor_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_gi_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_key_stores(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_maintenance_run_history(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_maintenance_runs(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_oneoff_patches(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_pluggable_databases(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_scheduled_actions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_scheduling_plans(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_scheduling_policies(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_scheduling_windows(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_system_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_vm_cluster_networks(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_vm_cluster_patches(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_vm_cluster_updates(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_list_vm_clusters(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_resource_pool_shapes(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_delete_pluggable_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"status": "200"}
    mock_client.delete_pluggable_database.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "delete_pluggable_database",
            {"pluggable_database_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        assert result.get("status") == "200"

        mock_client.delete_pluggable_database.assert_called_once_with(
            pluggable_database_id="sampleValue"
        )


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_pluggable_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_update_pluggable_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = [{"id": "sampleId"}]
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


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_create_pluggable_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_resp = create_autospec(oci.response.Response)
    mock_resp.data = {"id": "sample"}
    mock_client.create_pluggable_database.return_value = mock_resp

    async with Client(mcp) as client:
        response = await client.call_tool(
            "create_pluggable_database",
            {
                "pdb_name": "PDB1",
                "container_database_id": "CDB1",
                "pdb_admin_password": "pwd",
            },
        )

        assert isinstance(response.structured_content, dict)
        mock_client.create_pluggable_database.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
@patch("oracle.oci_database_mcp_server.server.call_create_pdb")
async def test_create_pluggable_database_from_local_clone(mock_call, mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_call.return_value = {"ok": True}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "create_pluggable_database_from_local_clone",
            {
                "pdb_name": "PDB1",
                "container_database_id": "CDB1",
                "pdb_admin_password": "pwd",
                "source_pluggable_database_id": "SRC",
            },
        )

        assert isinstance(response.structured_content, dict)
        mock_call.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
@patch("oracle.oci_database_mcp_server.server.call_create_pdb")
async def test_create_pluggable_database_from_remote_clone(mock_call, mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_call.return_value = {"ok": True}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "create_pluggable_database_from_remote_clone",
            {
                "pdb_name": "PDB_REMOTE",
                "container_database_id": "CDB1",
                "pdb_admin_password": "pwd",
                "source_pluggable_database_id": "SRC",
                "source_container_database_admin_password": "CDBpwd",
            },
        )

        assert isinstance(response.structured_content, dict)
        mock_call.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
@patch("oracle.oci_database_mcp_server.server.call_create_pdb")
async def test_create_pluggable_database_from_relocate(mock_call, mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_call.return_value = {"ok": True}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "create_pluggable_database_from_relocate",
            {
                "pdb_name": "PDB_MOVE",
                "container_database_id": "CDB1",
                "pdb_admin_password": "pwd",
                "source_pluggable_database_id": "SRC",
                "source_container_database_admin_password": "CDBpwd",
            },
        )

        assert isinstance(response.structured_content, dict)
        mock_call.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_application_vip(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_application_vip.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_application_vip",
            {"application_vip_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_application_vip.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_container_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_container_database.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_container_database",
            {
                "autonomous_container_database_id": "ocid1.autonomouscontainer.sampleDatabaseId"
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_container_database.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_container_database_dataguard_association(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_container_database_dataguard_association.return_value = (
        mock_response
    )

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_container_database_dataguard_association",
            {
                "autonomous_container_database_id": "ocid1.autonomouscontainer.sampleDatabaseId",
                "autonomous_container_database_dataguard_association_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_container_database_dataguard_association.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_container_database_resource_usage(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_container_database_resource_usage.return_value = (
        mock_response
    )

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_container_database_resource_usage",
            {
                "autonomous_container_database_id": "ocid1.autonomouscontainer.sampleDatabaseId"
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_container_database_resource_usage.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_database.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_database",
            {"autonomous_database_id": "ocid1.autonomous.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_database.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_database_backup(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_database_backup.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_database_backup",
            {"autonomous_database_backup_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_database_backup.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_database_dataguard_association(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_database_dataguard_association.return_value = (
        mock_response
    )

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_database_dataguard_association",
            {
                "autonomous_database_id": "ocid1.autonomous.sampleDatabaseId",
                "autonomous_database_dataguard_association_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_database_dataguard_association.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_database_regional_wallet(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_database_regional_wallet.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_database_regional_wallet",
            {},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_database_regional_wallet.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_database_software_image(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_database_software_image.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_database_software_image",
            {"autonomous_database_software_image_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_database_software_image.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_database_wallet(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_database_wallet.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_database_wallet",
            {"autonomous_database_id": "ocid1.autonomous.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_database_wallet.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_exadata_infrastructure(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_exadata_infrastructure.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_exadata_infrastructure",
            {"autonomous_exadata_infrastructure_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_exadata_infrastructure.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_patch(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_patch.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_patch",
            {"autonomous_patch_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_patch.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_virtual_machine(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_virtual_machine.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_virtual_machine",
            {"autonomous_virtual_machine_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_virtual_machine.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_vm_cluster(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_vm_cluster.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_vm_cluster",
            {"autonomous_vm_cluster_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_vm_cluster.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_autonomous_vm_cluster_resource_usage(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_autonomous_vm_cluster_resource_usage.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_autonomous_vm_cluster_resource_usage",
            {"autonomous_vm_cluster_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_autonomous_vm_cluster_resource_usage.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_backup(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_backup.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_backup",
            {"backup_id": "ocid1.backup.sampleBackupId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_backup.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_backup_destination(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_backup_destination.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_backup_destination",
            {"backup_destination_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_backup_destination.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_cloud_autonomous_vm_cluster(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_cloud_autonomous_vm_cluster.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_cloud_autonomous_vm_cluster",
            {"cloud_autonomous_vm_cluster_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_cloud_autonomous_vm_cluster.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_cloud_autonomous_vm_cluster_resource_usage(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_cloud_autonomous_vm_cluster_resource_usage.return_value = (
        mock_response
    )

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_cloud_autonomous_vm_cluster_resource_usage",
            {"cloud_autonomous_vm_cluster_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_cloud_autonomous_vm_cluster_resource_usage.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_cloud_exadata_infrastructure(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_cloud_exadata_infrastructure.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_cloud_exadata_infrastructure",
            {"cloud_exadata_infrastructure_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_cloud_exadata_infrastructure.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_cloud_exadata_infrastructure_unallocated_resources(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_cloud_exadata_infrastructure_unallocated_resources.return_value = (
        mock_response
    )

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_cloud_exadata_infrastructure_unallocated_resources",
            {"cloud_exadata_infrastructure_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_cloud_exadata_infrastructure_unallocated_resources.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_cloud_vm_cluster(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_cloud_vm_cluster.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_cloud_vm_cluster",
            {"cloud_vm_cluster_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_cloud_vm_cluster.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_cloud_vm_cluster_iorm_config(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_cloud_vm_cluster_iorm_config.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_cloud_vm_cluster_iorm_config",
            {"cloud_vm_cluster_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_cloud_vm_cluster_iorm_config.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_cloud_vm_cluster_update(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_cloud_vm_cluster_update.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_cloud_vm_cluster_update",
            {"cloud_vm_cluster_id": "sampleValue", "update_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_cloud_vm_cluster_update.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_cloud_vm_cluster_update_history_entry(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_cloud_vm_cluster_update_history_entry.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_cloud_vm_cluster_update_history_entry",
            {
                "cloud_vm_cluster_id": "sampleValue",
                "update_history_entry_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_cloud_vm_cluster_update_history_entry.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_console_connection(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_console_connection.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_console_connection",
            {"db_node_id": "sampleValue", "console_connection_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_console_connection.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_console_history(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_console_history.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_console_history",
            {"db_node_id": "sampleValue", "console_history_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_console_history.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_console_history_content(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_console_history_content.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_console_history_content",
            {"db_node_id": "sampleValue", "console_history_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_console_history_content.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_data_guard_association(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_data_guard_association.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_data_guard_association",
            {
                "database_id": "ocid1.database.sampleDatabaseId",
                "data_guard_association_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_data_guard_association.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_database.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_database",
            {"database_id": "ocid1.database.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_database.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_database_software_image(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_database_software_image.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_database_software_image",
            {"database_software_image_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_database_software_image.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_database_upgrade_history_entry(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_database_upgrade_history_entry.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_database_upgrade_history_entry",
            {
                "database_id": "ocid1.database.sampleDatabaseId",
                "upgrade_history_entry_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_database_upgrade_history_entry.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_db_home(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_db_home.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_db_home",
            {"db_home_id": "ocid1.dbhome.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_db_home.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_db_home_patch(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_db_home_patch.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_db_home_patch",
            {"db_home_id": "ocid1.dbhome.sampleDatabaseId", "patch_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_db_home_patch.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_db_home_patch_history_entry(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_db_home_patch_history_entry.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_db_home_patch_history_entry",
            {
                "db_home_id": "ocid1.dbhome.sampleDatabaseId",
                "patch_history_entry_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_db_home_patch_history_entry.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_db_node(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_db_node.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_db_node",
            {"db_node_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_db_node.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_db_server(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_db_server.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_db_server",
            {"exadata_infrastructure_id": "sampleValue", "db_server_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_db_server.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_db_system(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_db_system.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_db_system",
            {"db_system_id": "ocid1.dbsystem.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_db_system.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_db_system_patch(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_db_system_patch.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_db_system_patch",
            {
                "db_system_id": "ocid1.dbsystem.sampleDatabaseId",
                "patch_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_db_system_patch.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_db_system_patch_history_entry(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_db_system_patch_history_entry.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_db_system_patch_history_entry",
            {
                "db_system_id": "ocid1.dbsystem.sampleDatabaseId",
                "patch_history_entry_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_db_system_patch_history_entry.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_db_system_upgrade_history_entry(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_db_system_upgrade_history_entry.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_db_system_upgrade_history_entry",
            {
                "db_system_id": "ocid1.dbsystem.sampleDatabaseId",
                "upgrade_history_entry_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_db_system_upgrade_history_entry.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_exadata_infrastructure(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_exadata_infrastructure.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_exadata_infrastructure",
            {"exadata_infrastructure_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_exadata_infrastructure.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_exadata_infrastructure_ocpus(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_exadata_infrastructure_ocpus.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_exadata_infrastructure_ocpus",
            {"autonomous_exadata_infrastructure_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_exadata_infrastructure_ocpus.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_exadata_infrastructure_un_allocated_resources(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_exadata_infrastructure_un_allocated_resources.return_value = (
        mock_response
    )

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_exadata_infrastructure_un_allocated_resources",
            {"exadata_infrastructure_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_exadata_infrastructure_un_allocated_resources.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_exadata_iorm_config(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_exadata_iorm_config.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_exadata_iorm_config",
            {"db_system_id": "ocid1.dbsystem.sampleDatabaseId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_exadata_iorm_config.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_exadb_vm_cluster(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_exadb_vm_cluster.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_exadb_vm_cluster",
            {"exadb_vm_cluster_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_exadb_vm_cluster.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_exadb_vm_cluster_update(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_exadb_vm_cluster_update.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_exadb_vm_cluster_update",
            {"exadb_vm_cluster_id": "sampleValue", "update_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_exadb_vm_cluster_update.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_exadb_vm_cluster_update_history_entry(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_exadb_vm_cluster_update_history_entry.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_exadb_vm_cluster_update_history_entry",
            {
                "exadb_vm_cluster_id": "sampleValue",
                "update_history_entry_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_exadb_vm_cluster_update_history_entry.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_exascale_db_storage_vault(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_exascale_db_storage_vault.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_exascale_db_storage_vault",
            {"exascale_db_storage_vault_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_exascale_db_storage_vault.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_execution_action(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_execution_action.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_execution_action",
            {"execution_action_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_execution_action.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_execution_window(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_execution_window.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_execution_window",
            {"execution_window_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_execution_window.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_external_backup_job(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_external_backup_job.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_external_backup_job",
            {"backup_id": "ocid1.backup.sampleBackupId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_external_backup_job.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_external_container_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_external_container_database.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_external_container_database",
            {"external_container_database_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_external_container_database.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_external_database_connector(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_external_database_connector.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_external_database_connector",
            {"external_database_connector_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_external_database_connector.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_external_non_container_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_external_non_container_database.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_external_non_container_database",
            {"external_non_container_database_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_external_non_container_database.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_external_pluggable_database(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_external_pluggable_database.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_external_pluggable_database",
            {"external_pluggable_database_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_external_pluggable_database.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_infrastructure_target_versions(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_infrastructure_target_versions.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_infrastructure_target_versions",
            {"compartment_id": "ocid1.compartment.sampleCompartmentId"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_infrastructure_target_versions.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_key_store(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_key_store.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_key_store",
            {"key_store_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_key_store.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_maintenance_run(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_maintenance_run.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_maintenance_run",
            {"maintenance_run_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_maintenance_run.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_maintenance_run_history(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_maintenance_run_history.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_maintenance_run_history",
            {"maintenance_run_history_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_maintenance_run_history.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_oneoff_patch(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_oneoff_patch.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_oneoff_patch",
            {"oneoff_patch_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_oneoff_patch.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_pdb_conversion_history_entry(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_pdb_conversion_history_entry.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_pdb_conversion_history_entry",
            {
                "database_id": "ocid1.database.sampleDatabaseId",
                "pdb_conversion_history_entry_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_pdb_conversion_history_entry.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
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
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_scheduled_action(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_scheduled_action.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_scheduled_action",
            {"scheduled_action_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_scheduled_action.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_scheduling_plan(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_scheduling_plan.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_scheduling_plan",
            {"scheduling_plan_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_scheduling_plan.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_scheduling_policy(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_scheduling_policy.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_scheduling_policy",
            {"scheduling_policy_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_scheduling_policy.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_scheduling_window(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_scheduling_window.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_scheduling_window",
            {
                "scheduling_policy_id": "sampleValue",
                "scheduling_window_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_scheduling_window.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_vm_cluster(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_vm_cluster.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_vm_cluster",
            {"vm_cluster_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_vm_cluster.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_vm_cluster_network(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_vm_cluster_network.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_vm_cluster_network",
            {
                "exadata_infrastructure_id": "sampleValue",
                "vm_cluster_network_id": "sampleValue",
            },
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_vm_cluster_network.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_vm_cluster_patch(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_vm_cluster_patch.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_vm_cluster_patch",
            {"vm_cluster_id": "sampleValue", "patch_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_vm_cluster_patch.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_vm_cluster_patch_history_entry(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_vm_cluster_patch_history_entry.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_vm_cluster_patch_history_entry",
            {"vm_cluster_id": "sampleValue", "patch_history_entry_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_vm_cluster_patch_history_entry.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_vm_cluster_update(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_vm_cluster_update.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_vm_cluster_update",
            {"vm_cluster_id": "sampleValue", "update_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_vm_cluster_update.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
async def test_get_vm_cluster_update_history_entry(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = create_autospec(oci.response.Response)
    mock_response.data = {"id": "sampleId"}
    mock_client.get_vm_cluster_update_history_entry.return_value = mock_response

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_vm_cluster_update_history_entry",
            {"vm_cluster_id": "sampleValue", "update_history_entry_id": "sampleValue"},
        )

        result = response.structured_content
        assert isinstance(result, dict)
        mock_client.get_vm_cluster_update_history_entry.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_database_mcp_server.server.get_database_client")
@patch("oci.core.VirtualNetworkClient")
@patch("oci.config.from_file")
@patch("oci.signer.load_private_key_from_file")
@patch("builtins.open", new_callable=mock_open, read_data="dummy_token")
async def test_get_public_ip_for_database(
    mock_file, mock_load_key, mock_config, mock_vcn_client_cls, mock_get_db_client
):
    mock_db_client = MagicMock()
    mock_get_db_client.return_value = mock_db_client

    mock_db_response = create_autospec(oci.response.Response)
    mock_database = MagicMock()
    mock_database.db_system_id = "ocid1.dbsystem.oc1..sample"
    mock_database.vm_cluster_id = None
    mock_database.compartment_id = "ocid1.compartment.oc1..sample"
    mock_db_response.data = mock_database
    mock_db_client.get_database.return_value = mock_db_response

    mock_nodes_response = create_autospec(oci.response.Response)
    mock_node = MagicMock()
    mock_node.vnic_id = "ocid1.vnic.oc1..sample"
    mock_nodes_response.data = [mock_node]
    mock_db_client.list_db_nodes.return_value = mock_nodes_response

    mock_vcn_client = MagicMock()
    mock_vcn_client_cls.return_value = mock_vcn_client

    mock_vnic_response = create_autospec(oci.response.Response)
    mock_vnic = MagicMock()
    mock_vnic.public_ip = "203.0.113.10"
    mock_vnic_response.data = mock_vnic
    mock_vcn_client.get_vnic.return_value = mock_vnic_response

    mock_config.return_value = {
        "key_file": "/dummy/path/key.pem",
        "security_token_file": "/dummy/path/token",
    }

    async with Client(mcp) as client:
        response = await client.call_tool(
            "get_public_ip_for_database",
            {"database_id": "ocid1.database.oc1..sampleId"},
        )

        mock_db_client.get_database.assert_called_with(
            database_id="ocid1.database.oc1..sampleId"
        )
        mock_db_client.list_db_nodes.assert_called_once()

        mock_vcn_client.get_vnic.assert_called_with("ocid1.vnic.oc1..sample")

        result_text = response.content[0].text
        assert result_text == "203.0.113.10"
