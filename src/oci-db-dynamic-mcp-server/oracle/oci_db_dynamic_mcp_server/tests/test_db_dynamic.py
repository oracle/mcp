from unittest.mock import patch

import pytest
from fastmcp import Client
from oracle.oci_db_dynamic_mcp_server.server import mcp


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListApplicationVips(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListApplicationVips",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateApplicationVip(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateApplicationVip",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid",
                "hostnameLabel": "mockhost",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteApplicationVip(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteApplicationVip",
            arguments={
                "applicationVipId": "ocid1.applicationvip.oc1..mockapplicationvipid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetApplicationVip(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetApplicationVip",
            arguments={
                "applicationVipId": "ocid1.applicationvip.oc1..mockapplicationvipid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousContainerDatabaseBackups(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousContainerDatabaseBackups", arguments={}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousContainerDatabaseVersions(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousContainerDatabaseVersions",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "serviceComponent": "DATABASE",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousContainerDatabases(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousContainerDatabases",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateAutonomousContainerDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateAutonomousContainerDatabase",
            arguments={
                "displayName": "Mock_Display_Name",
                "patchModel": "RELEASE_UPDATE",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_TerminateAutonomousContainerDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "TerminateAutonomousContainerDatabase",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetAutonomousContainerDatabase(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetAutonomousContainerDatabase",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateAutonomousContainerDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateAutonomousContainerDatabase",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_AddStandbyAutonomousContainerDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "AddStandbyAutonomousContainerDatabase",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeAutonomousContainerDatabaseCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeAutonomousContainerDatabaseCompartment",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_EditAutonomousContainerDatabaseDataguard(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "EditAutonomousContainerDatabaseDataguard",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_FailoverAutonomousContainerDatabaseDataguard(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "FailoverAutonomousContainerDatabaseDataguard",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ReinstateAutonomousContainerDatabaseDataguard(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ReinstateAutonomousContainerDatabaseDataguard",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RestartAutonomousContainerDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RestartAutonomousContainerDatabase",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RotateAutonomousContainerDatabaseEncryptionKey(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RotateAutonomousContainerDatabaseEncryptionKey",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ConvertStandbyAutonomousContainerDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ConvertStandbyAutonomousContainerDatabase",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid",
                "role": "PRIMARY",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_SwitchoverAutonomousContainerDatabaseDataguard(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "SwitchoverAutonomousContainerDatabaseDataguard",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_MigrateAutonomousContainerDatabaseDataguardAssociation(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "MigrateAutonomousContainerDatabaseDataguardAssociation",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid",
                "autonomousContainerDatabaseDataguardAssociationId": "ocid1.autonomouscontainerdatabasedataguardassociation.oc1..mockacddgassocid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListContainerDatabasePatches(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListContainerDatabasePatches",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetAutonomousContainerDatabaseResourceUsage(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetAutonomousContainerDatabaseResourceUsage",
            arguments={
                "autonomousContainerDatabaseId": "ocid1.autonomouscontainerdatabase.oc1..mockacdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousDatabaseBackups(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool("ListAutonomousDatabaseBackups", arguments={})
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateAutonomousDatabaseBackup(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateAutonomousDatabaseBackup",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid",
                "backupDestinationDetails_type": "NFS",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteAutonomousDatabaseBackup(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteAutonomousDatabaseBackup",
            arguments={
                "autonomousDatabaseBackupId": "ocid1.autonomousdatabasebackup.oc1..mockadbbackupid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetAutonomousDatabaseBackup(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetAutonomousDatabaseBackup",
            arguments={
                "autonomousDatabaseBackupId": "ocid1.autonomousdatabasebackup.oc1..mockadbbackupid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateAutonomousDatabaseBackup(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateAutonomousDatabaseBackup",
            arguments={
                "autonomousDatabaseBackupId": "ocid1.autonomousdatabasebackup.oc1..mockadbbackupid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousDatabaseCharacterSets(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousDatabaseCharacterSets", arguments={}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousDatabaseSoftwareImages(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousDatabaseSoftwareImages",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "imageShapeFamily": "VM.Standard",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateAutonomousDatabaseSoftwareImage(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateAutonomousDatabaseSoftwareImage",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
                "imageShapeFamily": "VM.Standard",
                "sourceCdbId": "ocid1.database.oc1..mocksourcecdbid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteAutonomousDatabaseSoftwareImage(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteAutonomousDatabaseSoftwareImage",
            arguments={
                "autonomousDatabaseSoftwareImageId": "ocid1.autonomousdatabasesoftwareimage.oc1..mockadbimageid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetAutonomousDatabaseSoftwareImage(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetAutonomousDatabaseSoftwareImage",
            arguments={
                "autonomousDatabaseSoftwareImageId": "ocid1.autonomousdatabasesoftwareimage.oc1..mockadbimageid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateAutonomousDatabaseSoftwareImage(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateAutonomousDatabaseSoftwareImage",
            arguments={
                "autonomousDatabaseSoftwareImageId": "ocid1.autonomousdatabasesoftwareimage.oc1..mockadbimageid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeAutonomousDatabaseSoftwareImageCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeAutonomousDatabaseSoftwareImageCompartment",
            arguments={
                "autonomousDatabaseSoftwareImageId": "ocid1.autonomousdatabasesoftwareimage.oc1..mockadbimageid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousDatabases(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousDatabases",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateAutonomousDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateAutonomousDatabase",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ResourcePoolShapes(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool("ResourcePoolShapes", arguments={})
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetAutonomousDatabaseRegionalWallet(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetAutonomousDatabaseRegionalWallet", arguments={}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateAutonomousDatabaseRegionalWallet(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateAutonomousDatabaseRegionalWallet", arguments={}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteAutonomousDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteAutonomousDatabase",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetAutonomousDatabase(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetAutonomousDatabase",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateAutonomousDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateAutonomousDatabase",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeAutonomousDatabaseCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeAutonomousDatabaseCompartment",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeDisasterRecoveryConfiguration(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeDisasterRecoveryConfiguration",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeAutonomousDatabaseSubscription(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeAutonomousDatabaseSubscription",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ConfigureAutonomousDatabaseVaultKey(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ConfigureAutonomousDatabaseVaultKey",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ConfigureSaasAdminUser(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ConfigureSaasAdminUser",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeregisterAutonomousDatabaseDataSafe(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeregisterAutonomousDatabaseDataSafe",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid",
                "pdbAdminPassword": "MockPdbPassword123!",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DisableAutonomousDatabaseManagement(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DisableAutonomousDatabaseManagement",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DisableAutonomousDatabaseOperationsInsights(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DisableAutonomousDatabaseOperationsInsights",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_EnableAutonomousDatabaseManagement(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "EnableAutonomousDatabaseManagement",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_EnableAutonomousDatabaseOperationsInsights(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "EnableAutonomousDatabaseOperationsInsights",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_FailOverAutonomousDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "FailOverAutonomousDatabase",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GenerateAutonomousDatabaseWallet(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GenerateAutonomousDatabaseWallet",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid",
                "password": "MockPassword!",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_SaasAdminUserStatus(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "SaasAdminUserStatus",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_AutonomousDatabaseManualRefresh(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "AutonomousDatabaseManualRefresh",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RegisterAutonomousDatabaseDataSafe(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RegisterAutonomousDatabaseDataSafe",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid",
                "pdbAdminPassword": "MockPdbPassword123!",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RestartAutonomousDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RestartAutonomousDatabase",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RestoreAutonomousDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RestoreAutonomousDatabase",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RotateAutonomousDatabaseEncryptionKey(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RotateAutonomousDatabaseEncryptionKey",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ShrinkAutonomousDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ShrinkAutonomousDatabase",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_StartAutonomousDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "StartAutonomousDatabase",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_StopAutonomousDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "StopAutonomousDatabase",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_SwitchoverAutonomousDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "SwitchoverAutonomousDatabase",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousDatabaseDataguardAssociations(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousDatabaseDataguardAssociations",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetAutonomousDatabaseDataguardAssociation(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetAutonomousDatabaseDataguardAssociation",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid",
                "autonomousDatabaseDataguardAssociationId": "ocid1.autonomousdatabasedataguardassociation.oc1..mockadbdgassocid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousDatabaseClones(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousDatabaseClones",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousDatabasePeers(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousDatabasePeers",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousDatabaseRefreshableClones(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousDatabaseRefreshableClones",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListResourcePoolMembers(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListResourcePoolMembers",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetAutonomousDatabaseWallet(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetAutonomousDatabaseWallet",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateAutonomousDatabaseWallet(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateAutonomousDatabaseWallet",
            arguments={
                "autonomousDatabaseId": "ocid1.autonomousdatabase.oc1..mockadbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousDbPreviewVersions(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousDbPreviewVersions",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousDbVersions(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousDbVersions",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExadataInfrastructureOcpus(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExadataInfrastructureOcpus",
            arguments={
                "autonomousExadataInfrastructureId": "ocid1.autonomousexadatainfrastructure.oc1..mockaxid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetAutonomousPatch(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetAutonomousPatch",
            arguments={
                "autonomousPatchId": "ocid1.autonomouspatch.oc1..mockautonomouspatchid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousVirtualMachines(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousVirtualMachines",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "autonomousVmClusterId": "ocid1.autonomousvmcluster.oc1..mockavmclusterid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetAutonomousVirtualMachine(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetAutonomousVirtualMachine",
            arguments={
                "autonomousVirtualMachineId": "ocid1.autonomousvirtualmachine.oc1..mockavmid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousVmClusters(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousVmClusters",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateAutonomousVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateAutonomousVmCluster",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "vmClusterNetworkId": "ocid1.vmclusternetwork.oc1..mockvmclusternetworkid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteAutonomousVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteAutonomousVmCluster",
            arguments={
                "autonomousVmClusterId": "ocid1.autonomousvmcluster.oc1..mockavmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetAutonomousVmCluster(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetAutonomousVmCluster",
            arguments={
                "autonomousVmClusterId": "ocid1.autonomousvmcluster.oc1..mockavmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateAutonomousVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateAutonomousVmCluster",
            arguments={
                "autonomousVmClusterId": "ocid1.autonomousvmcluster.oc1..mockavmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListAutonomousVmClusterAcdResourceUsage(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListAutonomousVmClusterAcdResourceUsage",
            arguments={
                "autonomousVmClusterId": "ocid1.autonomousvmcluster.oc1..mockavmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeAutonomousVmClusterCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeAutonomousVmClusterCompartment",
            arguments={
                "autonomousVmClusterId": "ocid1.autonomousvmcluster.oc1..mockavmclusterid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RotateAutonomousVmClusterOrdsCerts(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RotateAutonomousVmClusterOrdsCerts",
            arguments={
                "autonomousVmClusterId": "ocid1.autonomousvmcluster.oc1..mockavmclusterid",
                "certificateGenerationType": "BYOC",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RotateAutonomousVmClusterSslCerts(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RotateAutonomousVmClusterSslCerts",
            arguments={
                "autonomousVmClusterId": "ocid1.autonomousvmcluster.oc1..mockavmclusterid",
                "certificateGenerationType": "BYOC",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetAutonomousVmClusterResourceUsage(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetAutonomousVmClusterResourceUsage",
            arguments={
                "autonomousVmClusterId": "ocid1.autonomousvmcluster.oc1..mockavmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListBackupDestination(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListBackupDestination",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateBackupDestination(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateBackupDestination",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
                "type": "FULL",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteBackupDestination(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteBackupDestination",
            arguments={
                "backupDestinationId": "ocid1.backupdestination.oc1..mockbackupdestinationid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetBackupDestination(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetBackupDestination",
            arguments={
                "backupDestinationId": "ocid1.backupdestination.oc1..mockbackupdestinationid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateBackupDestination(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateBackupDestination",
            arguments={
                "backupDestinationId": "ocid1.backupdestination.oc1..mockbackupdestinationid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeBackupDestinationCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeBackupDestinationCompartment",
            arguments={
                "backupDestinationId": "ocid1.backupdestination.oc1..mockbackupdestinationid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListBackups(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool("ListBackups", arguments={})
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateBackup(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateBackup",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "displayName": "Mock_Display_Name",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteBackup(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteBackup", arguments={"backupId": "ocid1.backup.oc1..mockbackupid"}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetBackup(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetBackup", arguments={"backupId": "ocid1.backup.oc1..mockbackupid"}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListCloudAutonomousVmClusters(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListCloudAutonomousVmClusters",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateCloudAutonomousVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateCloudAutonomousVmCluster",
            arguments={
                "cloudExadataInfrastructureId": "ocid1.cloudexadatainfrastructure.oc1..mockcloudexadataid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
                "subnetId": "ocid1.subnet.oc1..mocksubnetid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteCloudAutonomousVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteCloudAutonomousVmCluster",
            arguments={
                "cloudAutonomousVmClusterId": "ocid1.cloudautonomousvmcluster.oc1..mockcloudavmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetCloudAutonomousVmCluster(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetCloudAutonomousVmCluster",
            arguments={
                "cloudAutonomousVmClusterId": "ocid1.cloudautonomousvmcluster.oc1..mockcloudavmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateCloudAutonomousVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateCloudAutonomousVmCluster",
            arguments={
                "cloudAutonomousVmClusterId": "ocid1.cloudautonomousvmcluster.oc1..mockcloudavmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListCloudAutonomousVmClusterAcdResourceUsage(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListCloudAutonomousVmClusterAcdResourceUsage",
            arguments={
                "cloudAutonomousVmClusterId": "ocid1.cloudautonomousvmcluster.oc1..mockcloudavmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeCloudAutonomousVmClusterCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeCloudAutonomousVmClusterCompartment",
            arguments={
                "cloudAutonomousVmClusterId": "ocid1.cloudautonomousvmcluster.oc1..mockcloudavmclusterid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RotateCloudAutonomousVmClusterOrdsCerts(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RotateCloudAutonomousVmClusterOrdsCerts",
            arguments={
                "cloudAutonomousVmClusterId": "ocid1.cloudautonomousvmcluster.oc1..mockcloudavmclusterid",
                "certificateGenerationType": "BYOC",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RotateCloudAutonomousVmClusterSslCerts(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RotateCloudAutonomousVmClusterSslCerts",
            arguments={
                "cloudAutonomousVmClusterId": "ocid1.cloudautonomousvmcluster.oc1..mockcloudavmclusterid",
                "certificateGenerationType": "BYOC",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetCloudAutonomousVmClusterResourceUsage(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetCloudAutonomousVmClusterResourceUsage",
            arguments={
                "cloudAutonomousVmClusterId": "ocid1.cloudautonomousvmcluster.oc1..mockcloudavmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListCloudExadataInfrastructures(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListCloudExadataInfrastructures",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateCloudExadataInfrastructure(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateCloudExadataInfrastructure",
            arguments={
                "availabilityDomain": "Uocm:US-ASHBURN-AD-1",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
                "shape": "Exadata.X8M",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteCloudExadataInfrastructure(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteCloudExadataInfrastructure",
            arguments={
                "cloudExadataInfrastructureId": "ocid1.cloudexadatainfrastructure.oc1..mockcloudexadataid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetCloudExadataInfrastructure(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetCloudExadataInfrastructure",
            arguments={
                "cloudExadataInfrastructureId": "ocid1.cloudexadatainfrastructure.oc1..mockcloudexadataid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateCloudExadataInfrastructure(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateCloudExadataInfrastructure",
            arguments={
                "cloudExadataInfrastructureId": "ocid1.cloudexadatainfrastructure.oc1..mockcloudexadataid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_AddStorageCapacityCloudExadataInfrastructure(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "AddStorageCapacityCloudExadataInfrastructure",
            arguments={
                "cloudExadataInfrastructureId": "ocid1.cloudexadatainfrastructure.oc1..mockcloudexadataid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeCloudExadataInfrastructureCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeCloudExadataInfrastructureCompartment",
            arguments={
                "cloudExadataInfrastructureId": "ocid1.cloudexadatainfrastructure.oc1..mockcloudexadataid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeCloudExadataInfrastructureSubscription(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeCloudExadataInfrastructureSubscription",
            arguments={
                "cloudExadataInfrastructureId": "ocid1.cloudexadatainfrastructure.oc1..mockcloudexadataid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ConfigureExascaleCloudExadataInfrastructure(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ConfigureExascaleCloudExadataInfrastructure",
            arguments={
                "cloudExadataInfrastructureId": "ocid1.cloudexadatainfrastructure.oc1..mockcloudexadataid",
                "totalStorageInGBs": 5000,
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetCloudExadataInfrastructureUnallocatedResources(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetCloudExadataInfrastructureUnallocatedResources",
            arguments={
                "cloudExadataInfrastructureId": "ocid1.cloudexadatainfrastructure.oc1..mockcloudexadataid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListCloudVmClusters(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListCloudVmClusters",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateCloudVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateCloudVmCluster",
            arguments={
                "backupSubnetId": "ocid1.subnet.oc1..mockbackupsubnetid",
                "cloudExadataInfrastructureId": "ocid1.cloudexadatainfrastructure.oc1..mockcloudexadataid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "cpuCoreCount": 16,
                "displayName": "Mock_Display_Name",
                "giVersion": "19.0.0.0",
                "hostname": "mock-host-1",
                "sshPublicKeys": ["ssh-rsa AAAAB3Nza... mockKey1"],
                "subnetId": "ocid1.subnet.oc1..mocksubnetid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteCloudVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteCloudVmCluster",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetCloudVmCluster(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetCloudVmCluster",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateCloudVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateCloudVmCluster",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetCloudVmClusterIormConfig(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetCloudVmClusterIormConfig",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateCloudVmClusterIormConfig(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateCloudVmClusterIormConfig",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_AddVirtualMachineToCloudVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "AddVirtualMachineToCloudVmCluster",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid",
                "dbServers": [
                    "ocid1.dbserver.oc1..server1",
                    "ocid1.dbserver.oc1..server2",
                ],
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeCloudVmClusterCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeCloudVmClusterCompartment",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeCloudVmClusterSubscription(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeCloudVmClusterSubscription",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RemoveVirtualMachineFromCloudVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RemoveVirtualMachineFromCloudVmCluster",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid",
                "dbServers": [
                    "ocid1.dbserver.oc1..server1",
                    "ocid1.dbserver.oc1..server2",
                ],
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListCloudVmClusterUpdateHistoryEntries(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListCloudVmClusterUpdateHistoryEntries",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetCloudVmClusterUpdateHistoryEntry(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetCloudVmClusterUpdateHistoryEntry",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid",
                "updateHistoryEntryId": "ocid1.updatehistory.oc1..mockupdatehistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListCloudVmClusterUpdates(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListCloudVmClusterUpdates",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetCloudVmClusterUpdate(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetCloudVmClusterUpdate",
            arguments={
                "cloudVmClusterId": "ocid1.cloudvmcluster.oc1..mockcloudvmclusterid",
                "updateId": "ocid1.update.oc1..mockupdateid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDatabaseSoftwareImages(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDatabaseSoftwareImages",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateDatabaseSoftwareImage(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateDatabaseSoftwareImage",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteDatabaseSoftwareImage(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteDatabaseSoftwareImage",
            arguments={
                "databaseSoftwareImageId": "ocid1.databasesoftwareimage.oc1..mockdbsoftwareimageid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDatabaseSoftwareImage(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDatabaseSoftwareImage",
            arguments={
                "databaseSoftwareImageId": "ocid1.databasesoftwareimage.oc1..mockdbsoftwareimageid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateDatabaseSoftwareImage(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateDatabaseSoftwareImage",
            arguments={
                "databaseSoftwareImageId": "ocid1.databasesoftwareimage.oc1..mockdbsoftwareimageid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeDatabaseSoftwareImageCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeDatabaseSoftwareImageCompartment",
            arguments={
                "databaseSoftwareImageId": "ocid1.databasesoftwareimage.oc1..mockdbsoftwareimageid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDatabases(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDatabases",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateDatabase",
            arguments={
                "dbHomeId": "ocid1.dbhome.oc1..mockdbhomeid",
                "source": "DB_SYSTEM",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteDatabase",
            arguments={"databaseId": "ocid1.database.oc1..mockdatabaseid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDatabase(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDatabase",
            arguments={"databaseId": "ocid1.database.oc1..mockdatabaseid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateDatabase",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "storageSizeDetails_dataStorageSizeInGBs": 1024,
                "storageSizeDetails_recoStorageSizeInGBs": 256,
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeEncryptionKeyLocation(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeEncryptionKeyLocation",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "providerType": "OCI",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ConvertToPdb(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ConvertToPdb",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "action": "STOP",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DisableDatabaseManagement(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DisableDatabaseManagement",
            arguments={"databaseId": "ocid1.database.oc1..mockdatabaseid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_EnableDatabaseManagement(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "EnableDatabaseManagement",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "credentialDetails_passwordSecretId": "ocid1.vaultsecret.oc1..mockpasswordsecretid",
                "credentialDetails_userName": "db_admin",
                "privateEndPointId": "ocid1.privateendpoint.oc1..mockprivateendpointid",
                "serviceName": "mockservice.example.com",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_MigrateVaultKey(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "MigrateVaultKey",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "kmsKeyId": "ocid1.key.oc1..mockkmskeyid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ModifyDatabaseManagement(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ModifyDatabaseManagement",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "credentialDetails_passwordSecretId": "ocid1.vaultsecret.oc1..mockpasswordsecretid",
                "credentialDetails_userName": "db_admin",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RestoreDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RestoreDatabase",
            arguments={"databaseId": "ocid1.database.oc1..mockdatabaseid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RotateVaultKey(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RotateVaultKey",
            arguments={"databaseId": "ocid1.database.oc1..mockdatabaseid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpgradeDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpgradeDatabase",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "action": "STOP",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ConvertToStandalone(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ConvertToStandalone",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "databaseAdminPassword": "MockDbPassword123!",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_FailoverDataGuard(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "FailoverDataGuard",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "databaseAdminPassword": "MockDbPassword123!",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ReinstateDataGuard(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ReinstateDataGuard",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "databaseAdminPassword": "MockDbPassword123!",
                "sourceDatabaseId": "ocid1.database.oc1..mocksourcedbid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_SwitchOverDataGuard(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "SwitchOverDataGuard",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "databaseAdminPassword": "MockDbPassword123!",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateDataGuard(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateDataGuard",
            arguments={"databaseId": "ocid1.database.oc1..mockdatabaseid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDataGuardAssociations(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDataGuardAssociations",
            arguments={"databaseId": "ocid1.database.oc1..mockdatabaseid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateDataGuardAssociation(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateDataGuardAssociation",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "creationType": "CLONE",
                "databaseAdminPassword": "MockDbPassword123!",
                "protectionMode": "MAXIMUM_PERFORMANCE",
                "sourceEncryptionKeyLocationDetails_providerType": "OCI_VAULT",
                "transportType": "TCP",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDataGuardAssociation(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDataGuardAssociation",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "dataGuardAssociationId": "ocid1.dataguardassociation.oc1..mockdgassocid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateDataGuardAssociation(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateDataGuardAssociation",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "dataGuardAssociationId": "ocid1.dataguardassociation.oc1..mockdgassocid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_FailoverDataGuardAssociation(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "FailoverDataGuardAssociation",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "dataGuardAssociationId": "ocid1.dataguardassociation.oc1..mockdgassocid",
                "databaseAdminPassword": "MockDbPassword123!",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_MigrateDataGuardAssociationToMultiDataGuards(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "MigrateDataGuardAssociationToMultiDataGuards",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "dataGuardAssociationId": "ocid1.dataguardassociation.oc1..mockdgassocid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ReinstateDataGuardAssociation(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ReinstateDataGuardAssociation",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "dataGuardAssociationId": "ocid1.dataguardassociation.oc1..mockdgassocid",
                "databaseAdminPassword": "MockDbPassword123!",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_SwitchoverDataGuardAssociation(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "SwitchoverDataGuardAssociation",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "dataGuardAssociationId": "ocid1.dataguardassociation.oc1..mockdgassocid",
                "databaseAdminPassword": "MockDbPassword123!",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListPdbConversionHistoryEntries(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListPdbConversionHistoryEntries",
            arguments={"databaseId": "ocid1.database.oc1..mockdatabaseid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetPdbConversionHistoryEntry(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetPdbConversionHistoryEntry",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "pdbConversionHistoryEntryId": "ocid1.pdbconversionhistory.oc1..mockpdbhistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDatabaseUpgradeHistoryEntries(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDatabaseUpgradeHistoryEntries",
            arguments={"databaseId": "ocid1.database.oc1..mockdatabaseid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDatabaseUpgradeHistoryEntry(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDatabaseUpgradeHistoryEntry",
            arguments={
                "databaseId": "ocid1.database.oc1..mockdatabaseid",
                "upgradeHistoryEntryId": "ocid1.upgradehistory.oc1..mockupgradehistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbHomes(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbHomes",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateDbHome(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool("CreateDbHome", arguments={})
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteDbHome(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteDbHome", arguments={"dbHomeId": "ocid1.dbhome.oc1..mockdbhomeid"}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDbHome(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDbHome", arguments={"dbHomeId": "ocid1.dbhome.oc1..mockdbhomeid"}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateDbHome(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateDbHome", arguments={"dbHomeId": "ocid1.dbhome.oc1..mockdbhomeid"}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbHomePatchHistoryEntries(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbHomePatchHistoryEntries",
            arguments={"dbHomeId": "ocid1.dbhome.oc1..mockdbhomeid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDbHomePatchHistoryEntry(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDbHomePatchHistoryEntry",
            arguments={
                "dbHomeId": "ocid1.dbhome.oc1..mockdbhomeid",
                "patchHistoryEntryId": "ocid1.patchhistory.oc1..mockpatchhistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbHomePatches(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbHomePatches",
            arguments={"dbHomeId": "ocid1.dbhome.oc1..mockdbhomeid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDbHomePatch(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDbHomePatch",
            arguments={
                "dbHomeId": "ocid1.dbhome.oc1..mockdbhomeid",
                "patchId": "ocid1.patch.oc1..mockpatchid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbNodes(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbNodes",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDbNode(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDbNode", arguments={"dbNodeId": "ocid1.dbnode.oc1..mockdbnodeid"}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DbNodeAction(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DbNodeAction",
            arguments={"dbNodeId": "ocid1.dbnode.oc1..mockdbnodeid", "action": "STOP"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListConsoleConnections(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListConsoleConnections",
            arguments={"dbNodeId": "ocid1.dbnode.oc1..mockdbnodeid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateConsoleConnection(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateConsoleConnection",
            arguments={
                "dbNodeId": "ocid1.dbnode.oc1..mockdbnodeid",
                "publicKey": "ssh-rsa AAAAB3Nza... mockPublicKey",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteConsoleConnection(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteConsoleConnection",
            arguments={
                "dbNodeId": "ocid1.dbnode.oc1..mockdbnodeid",
                "consoleConnectionId": "ocid1.consoleconnection.oc1..mockconsoleconnid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetConsoleConnection(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetConsoleConnection",
            arguments={
                "dbNodeId": "ocid1.dbnode.oc1..mockdbnodeid",
                "consoleConnectionId": "ocid1.consoleconnection.oc1..mockconsoleconnid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListConsoleHistories(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListConsoleHistories",
            arguments={"dbNodeId": "ocid1.dbnode.oc1..mockdbnodeid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateConsoleHistory(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateConsoleHistory",
            arguments={
                "dbNodeId": "ocid1.dbnode.oc1..mockdbnodeid",
                "displayName": "Mock_Display_Name",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteConsoleHistory(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteConsoleHistory",
            arguments={
                "dbNodeId": "ocid1.dbnode.oc1..mockdbnodeid",
                "consoleHistoryId": "ocid1.consolehistory.oc1..mockconsolehistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetConsoleHistory(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetConsoleHistory",
            arguments={
                "dbNodeId": "ocid1.dbnode.oc1..mockdbnodeid",
                "consoleHistoryId": "ocid1.consolehistory.oc1..mockconsolehistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateConsoleHistory(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateConsoleHistory",
            arguments={
                "dbNodeId": "ocid1.dbnode.oc1..mockdbnodeid",
                "consoleHistoryId": "ocid1.consolehistory.oc1..mockconsolehistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetConsoleHistoryContent(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetConsoleHistoryContent",
            arguments={
                "dbNodeId": "ocid1.dbnode.oc1..mockdbnodeid",
                "consoleHistoryId": "ocid1.consolehistory.oc1..mockconsolehistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbServers(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbServers",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDbServer(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDbServer",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "dbServerId": "ocid1.dbserver.oc1..mockdbserverid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbSystemComputePerformances(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbSystemComputePerformances", arguments={}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbSystemShapes(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbSystemShapes",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListFlexComponents(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListFlexComponents",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbSystemStoragePerformances(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbSystemStoragePerformances", arguments={"storageManagement": "ASM"}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbSystems(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbSystems",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_LaunchDbSystem(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "LaunchDbSystem",
            arguments={
                "availabilityDomain": "Uocm:US-ASHBURN-AD-1",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "hostname": "mock-host-1",
                "shape": "Exadata.X8M",
                "sshPublicKeys": ["ssh-rsa AAAAB3Nza... mockKey1"],
                "subnetId": "ocid1.subnet.oc1..mocksubnetid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_TerminateDbSystem(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "TerminateDbSystem",
            arguments={"dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDbSystem(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDbSystem",
            arguments={"dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateDbSystem(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateDbSystem",
            arguments={"dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExadataIormConfig(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExadataIormConfig",
            arguments={"dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateExadataIormConfig(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateExadataIormConfig",
            arguments={"dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeDbSystemCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeDbSystemCompartment",
            arguments={
                "dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_MigrateExadataDbSystemResourceModel(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "MigrateExadataDbSystemResourceModel",
            arguments={"dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpgradeDbSystem(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpgradeDbSystem",
            arguments={
                "dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid",
                "action": "STOP",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbSystemPatchHistoryEntries(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbSystemPatchHistoryEntries",
            arguments={"dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDbSystemPatchHistoryEntry(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDbSystemPatchHistoryEntry",
            arguments={
                "dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid",
                "patchHistoryEntryId": "ocid1.patchhistory.oc1..mockpatchhistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbSystemPatches(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbSystemPatches",
            arguments={"dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDbSystemPatch(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDbSystemPatch",
            arguments={
                "dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid",
                "patchId": "ocid1.patch.oc1..mockpatchid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbSystemUpgradeHistoryEntries(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbSystemUpgradeHistoryEntries",
            arguments={"dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetDbSystemUpgradeHistoryEntry(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetDbSystemUpgradeHistoryEntry",
            arguments={
                "dbSystemId": "ocid1.dbsystem.oc1..mockdbsystemid",
                "upgradeHistoryEntryId": "ocid1.upgradehistory.oc1..mockupgradehistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListDbVersions(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListDbVersions",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListExadataInfrastructures(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListExadataInfrastructures",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateExadataInfrastructure(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateExadataInfrastructure",
            arguments={
                "adminNetworkCIDR": "192.168.1.0/24",
                "cloudControlPlaneServer1": "10.0.0.5",
                "cloudControlPlaneServer2": "10.0.0.6",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "corporateProxy": "http://corp-proxy:8080",
                "displayName": "Mock_Display_Name",
                "dnsServer": ["169.254.169.254"],
                "gateway": "10.0.0.1",
                "infiniBandNetworkCIDR": "192.168.0.0/24",
                "netmask": "255.255.255.0",
                "ntpServer": ["169.254.169.254"],
                "shape": "Exadata.X8M",
                "timeZone": "UTC",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteExadataInfrastructure(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteExadataInfrastructure",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExadataInfrastructure(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExadataInfrastructure",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateExadataInfrastructure(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateExadataInfrastructure",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ActivateExadataInfrastructure(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ActivateExadataInfrastructure",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "activationFile": "mock_activation_file_path_or_content",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_AddStorageCapacityExadataInfrastructure(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "AddStorageCapacityExadataInfrastructure",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeExadataInfrastructureCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeExadataInfrastructureCompartment",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DownloadExadataInfrastructureConfigFile(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DownloadExadataInfrastructureConfigFile",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExadataInfrastructureUnAllocatedResources(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExadataInfrastructureUnAllocatedResources",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListVmClusterNetworks(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListVmClusterNetworks",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateVmClusterNetwork(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateVmClusterNetwork",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
                "scans": [{"hostname": "scan1", "port": 1521}],
                "vmNetworks": [
                    {
                        "networkType": "CLIENT",
                        "netmask": "255.255.255.0",
                        "gateway": "10.0.0.1",
                    }
                ],
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GenerateRecommendedVmClusterNetwork(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GenerateRecommendedVmClusterNetwork",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
                "networks": [{"id": "ocid1.network.oc1..mocknetworkid"}],
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteVmClusterNetwork(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteVmClusterNetwork",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "vmClusterNetworkId": "ocid1.vmclusternetwork.oc1..mockvmclusternetworkid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetVmClusterNetwork(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetVmClusterNetwork",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "vmClusterNetworkId": "ocid1.vmclusternetwork.oc1..mockvmclusternetworkid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateVmClusterNetwork(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateVmClusterNetwork",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "vmClusterNetworkId": "ocid1.vmclusternetwork.oc1..mockvmclusternetworkid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DownloadVmClusterNetworkConfigFile(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DownloadVmClusterNetworkConfigFile",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "vmClusterNetworkId": "ocid1.vmclusternetwork.oc1..mockvmclusternetworkid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ResizeVmClusterNetwork(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ResizeVmClusterNetwork",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "vmClusterNetworkId": "ocid1.vmclusternetwork.oc1..mockvmclusternetworkid",
                "action": "STOP",
                "vmNetworks": [
                    {
                        "networkType": "CLIENT",
                        "netmask": "255.255.255.0",
                        "gateway": "10.0.0.1",
                    }
                ],
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ValidateVmClusterNetwork(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ValidateVmClusterNetwork",
            arguments={
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "vmClusterNetworkId": "ocid1.vmclusternetwork.oc1..mockvmclusternetworkid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListExadbVmClusters(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListExadbVmClusters",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateExadbVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateExadbVmCluster",
            arguments={
                "availabilityDomain": "Uocm:US-ASHBURN-AD-1",
                "backupSubnetId": "ocid1.subnet.oc1..mockbackupsubnetid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
                "enabledECpuCount": 8,
                "exascaleDbStorageVaultId": "ocid1.exascaledbstoragevault.oc1..mockexascalevaultid",
                "gridImageId": "ocid1.gridimage.oc1..mockgridimageid",
                "hostname": "mock-host-1",
                "nodeCount": 3,
                "shape": "Exadata.X8M",
                "sshPublicKeys": ["ssh-rsa AAAAB3Nza... mockKey1"],
                "subnetId": "ocid1.subnet.oc1..mocksubnetid",
                "totalECpuCount": 32,
                "vmFileSystemStorage_totalSizeInGbs": 500,
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteExadbVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteExadbVmCluster",
            arguments={
                "exadbVmClusterId": "ocid1.exadbvmcluster.oc1..mockexadbvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExadbVmCluster(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExadbVmCluster",
            arguments={
                "exadbVmClusterId": "ocid1.exadbvmcluster.oc1..mockexadbvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateExadbVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateExadbVmCluster",
            arguments={
                "exadbVmClusterId": "ocid1.exadbvmcluster.oc1..mockexadbvmclusterid",
                "vmFileSystemStorage_totalSizeInGbs": 500,
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeExadbVmClusterCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeExadbVmClusterCompartment",
            arguments={
                "exadbVmClusterId": "ocid1.exadbvmcluster.oc1..mockexadbvmclusterid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeExadbVmClusterSubscription(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeExadbVmClusterSubscription",
            arguments={
                "exadbVmClusterId": "ocid1.exadbvmcluster.oc1..mockexadbvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RemoveVirtualMachineFromExadbVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RemoveVirtualMachineFromExadbVmCluster",
            arguments={
                "exadbVmClusterId": "ocid1.exadbvmcluster.oc1..mockexadbvmclusterid",
                "dbNodes": [
                    {"id": "ocid1.dbnode.oc1..node1"},
                    {"id": "ocid1.dbnode.oc1..node2"},
                ],
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListExadbVmClusterUpdateHistoryEntries(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListExadbVmClusterUpdateHistoryEntries",
            arguments={
                "exadbVmClusterId": "ocid1.exadbvmcluster.oc1..mockexadbvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExadbVmClusterUpdateHistoryEntry(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExadbVmClusterUpdateHistoryEntry",
            arguments={
                "exadbVmClusterId": "ocid1.exadbvmcluster.oc1..mockexadbvmclusterid",
                "updateHistoryEntryId": "ocid1.updatehistory.oc1..mockupdatehistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListExadbVmClusterUpdates(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListExadbVmClusterUpdates",
            arguments={
                "exadbVmClusterId": "ocid1.exadbvmcluster.oc1..mockexadbvmclusterid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExadbVmClusterUpdate(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExadbVmClusterUpdate",
            arguments={
                "exadbVmClusterId": "ocid1.exadbvmcluster.oc1..mockexadbvmclusterid",
                "updateId": "ocid1.update.oc1..mockupdateid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListExascaleDbStorageVaults(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListExascaleDbStorageVaults",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateExascaleDbStorageVault(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateExascaleDbStorageVault",
            arguments={
                "availabilityDomain": "Uocm:US-ASHBURN-AD-1",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
                "highCapacityDatabaseStorage_totalSizeInGbs": 4096,
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteExascaleDbStorageVault(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteExascaleDbStorageVault",
            arguments={
                "exascaleDbStorageVaultId": "ocid1.exascaledbstoragevault.oc1..mockexascalevaultid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExascaleDbStorageVault(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExascaleDbStorageVault",
            arguments={
                "exascaleDbStorageVaultId": "ocid1.exascaledbstoragevault.oc1..mockexascalevaultid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateExascaleDbStorageVault(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateExascaleDbStorageVault",
            arguments={
                "exascaleDbStorageVaultId": "ocid1.exascaledbstoragevault.oc1..mockexascalevaultid",
                "highCapacityDatabaseStorage_totalSizeInGbs": 4096,
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeExascaleDbStorageVaultCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeExascaleDbStorageVaultCompartment",
            arguments={
                "exascaleDbStorageVaultId": "ocid1.exascaledbstoragevault.oc1..mockexascalevaultid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeExascaleDbStorageVaultSubscription(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeExascaleDbStorageVaultSubscription",
            arguments={
                "exascaleDbStorageVaultId": "ocid1.exascaledbstoragevault.oc1..mockexascalevaultid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListExecutionActions(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListExecutionActions",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateExecutionAction(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateExecutionAction",
            arguments={
                "actionType": "DB_Server_Patching",
                "executionWindowId": "ocid1.executionwindow.oc1..mockexecutionwindowid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteExecutionAction(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteExecutionAction",
            arguments={
                "executionActionId": "ocid1.executionaction.oc1..mockexecutionactionid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExecutionAction(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExecutionAction",
            arguments={
                "executionActionId": "ocid1.executionaction.oc1..mockexecutionactionid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateExecutionAction(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateExecutionAction",
            arguments={
                "executionActionId": "ocid1.executionaction.oc1..mockexecutionactionid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_MoveExecutionActionMember(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "MoveExecutionActionMember",
            arguments={
                "executionActionId": "ocid1.executionaction.oc1..mockexecutionactionid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListExecutionWindows(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListExecutionWindows",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateExecutionWindow(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateExecutionWindow",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "executionResourceId": "ocid1.executionresource.oc1..mockexecutionresourceid",
                "timeScheduled": "2025-01-01T00:00:00.000Z",
                "windowDurationInMins": 240,
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteExecutionWindow(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteExecutionWindow",
            arguments={
                "executionWindowId": "ocid1.executionwindow.oc1..mockexecutionwindowid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExecutionWindow(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExecutionWindow",
            arguments={
                "executionWindowId": "ocid1.executionwindow.oc1..mockexecutionwindowid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateExecutionWindow(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateExecutionWindow",
            arguments={
                "executionWindowId": "ocid1.executionwindow.oc1..mockexecutionwindowid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ReorderExecutionActions(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ReorderExecutionActions",
            arguments={
                "executionWindowId": "ocid1.executionwindow.oc1..mockexecutionwindowid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateExternalBackupJob(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateExternalBackupJob",
            arguments={
                "availabilityDomain": "Uocm:US-ASHBURN-AD-1",
                "characterSet": "AL32UTF8",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "databaseEdition": "ENTERPRISE_EDITION_EXTREME_PERFORMANCE",
                "databaseMode": "READ_WRITE",
                "dbName": "MOCKDB",
                "dbVersion": "19.0.0.0",
                "displayName": "Mock_Display_Name",
                "externalDatabaseIdentifier": 1,
                "ncharacterSet": "AL16UTF16",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExternalBackupJob(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExternalBackupJob",
            arguments={"backupId": "ocid1.backup.oc1..mockbackupid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CompleteExternalBackupJob(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CompleteExternalBackupJob",
            arguments={"backupId": "ocid1.backup.oc1..mockbackupid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListExternalContainerDatabases(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListExternalContainerDatabases",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateExternalContainerDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateExternalContainerDatabase",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteExternalContainerDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteExternalContainerDatabase",
            arguments={
                "externalContainerDatabaseId": "ocid1.externalcontainerdatabase.oc1..mockextcdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExternalContainerDatabase(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExternalContainerDatabase",
            arguments={
                "externalContainerDatabaseId": "ocid1.externalcontainerdatabase.oc1..mockextcdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateExternalContainerDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateExternalContainerDatabase",
            arguments={
                "externalContainerDatabaseId": "ocid1.externalcontainerdatabase.oc1..mockextcdbid",
                "displayName": "Mock_Display_Name",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeExternalContainerDatabaseCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeExternalContainerDatabaseCompartment",
            arguments={
                "externalContainerDatabaseId": "ocid1.externalcontainerdatabase.oc1..mockextcdbid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DisableExternalContainerDatabaseDatabaseManagement(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DisableExternalContainerDatabaseDatabaseManagement",
            arguments={
                "externalContainerDatabaseId": "ocid1.externalcontainerdatabase.oc1..mockextcdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DisableExternalContainerDatabaseStackMonitoring(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DisableExternalContainerDatabaseStackMonitoring",
            arguments={
                "externalContainerDatabaseId": "ocid1.externalcontainerdatabase.oc1..mockextcdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_EnableExternalContainerDatabaseDatabaseManagement(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "EnableExternalContainerDatabaseDatabaseManagement",
            arguments={
                "externalContainerDatabaseId": "ocid1.externalcontainerdatabase.oc1..mockextcdbid",
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid",
                "licenseModel": "BRING_YOUR_OWN_LICENSE",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_EnableExternalContainerDatabaseStackMonitoring(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "EnableExternalContainerDatabaseStackMonitoring",
            arguments={
                "externalContainerDatabaseId": "ocid1.externalcontainerdatabase.oc1..mockextcdbid",
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ScanExternalContainerDatabasePluggableDatabases(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ScanExternalContainerDatabasePluggableDatabases",
            arguments={
                "externalContainerDatabaseId": "ocid1.externalcontainerdatabase.oc1..mockextcdbid",
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListExternalDatabaseConnectors(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListExternalDatabaseConnectors",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "externalDatabaseId": "ocid1.externaldatabase.oc1..mockexternaldatabaseid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateExternalDatabaseConnector(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateExternalDatabaseConnector",
            arguments={
                "displayName": "Mock_Display_Name",
                "externalDatabaseId": "ocid1.externaldatabase.oc1..mockexternaldatabaseid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteExternalDatabaseConnector(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteExternalDatabaseConnector",
            arguments={
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExternalDatabaseConnector(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExternalDatabaseConnector",
            arguments={
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateExternalDatabaseConnector(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateExternalDatabaseConnector",
            arguments={
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CheckExternalDatabaseConnectorConnectionStatus(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CheckExternalDatabaseConnectorConnectionStatus",
            arguments={
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListExternalNonContainerDatabases(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListExternalNonContainerDatabases",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateExternalNonContainerDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateExternalNonContainerDatabase",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteExternalNonContainerDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteExternalNonContainerDatabase",
            arguments={
                "externalNonContainerDatabaseId": "ocid1.externalnoncontainerdatabase.oc1..mockextnoncdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExternalNonContainerDatabase(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExternalNonContainerDatabase",
            arguments={
                "externalNonContainerDatabaseId": "ocid1.externalnoncontainerdatabase.oc1..mockextnoncdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateExternalNonContainerDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateExternalNonContainerDatabase",
            arguments={
                "externalNonContainerDatabaseId": "ocid1.externalnoncontainerdatabase.oc1..mockextnoncdbid",
                "displayName": "Mock_Display_Name",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeExternalNonContainerDatabaseCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeExternalNonContainerDatabaseCompartment",
            arguments={
                "externalNonContainerDatabaseId": "ocid1.externalnoncontainerdatabase.oc1..mockextnoncdbid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DisableExternalNonContainerDatabaseDatabaseManagement(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DisableExternalNonContainerDatabaseDatabaseManagement",
            arguments={
                "externalNonContainerDatabaseId": "ocid1.externalnoncontainerdatabase.oc1..mockextnoncdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DisableExternalNonContainerDatabaseOperationsInsights(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DisableExternalNonContainerDatabaseOperationsInsights",
            arguments={
                "externalNonContainerDatabaseId": "ocid1.externalnoncontainerdatabase.oc1..mockextnoncdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DisableExternalNonContainerDatabaseStackMonitoring(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DisableExternalNonContainerDatabaseStackMonitoring",
            arguments={
                "externalNonContainerDatabaseId": "ocid1.externalnoncontainerdatabase.oc1..mockextnoncdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_EnableExternalNonContainerDatabaseDatabaseManagement(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "EnableExternalNonContainerDatabaseDatabaseManagement",
            arguments={
                "externalNonContainerDatabaseId": "ocid1.externalnoncontainerdatabase.oc1..mockextnoncdbid",
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid",
                "licenseModel": "BRING_YOUR_OWN_LICENSE",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_EnableExternalNonContainerDatabaseOperationsInsights(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "EnableExternalNonContainerDatabaseOperationsInsights",
            arguments={
                "externalNonContainerDatabaseId": "ocid1.externalnoncontainerdatabase.oc1..mockextnoncdbid",
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_EnableExternalNonContainerDatabaseStackMonitoring(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "EnableExternalNonContainerDatabaseStackMonitoring",
            arguments={
                "externalNonContainerDatabaseId": "ocid1.externalnoncontainerdatabase.oc1..mockextnoncdbid",
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListExternalPluggableDatabases(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListExternalPluggableDatabases",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateExternalPluggableDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateExternalPluggableDatabase",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
                "externalContainerDatabaseId": "ocid1.externalcontainerdatabase.oc1..mockextcdbid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteExternalPluggableDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteExternalPluggableDatabase",
            arguments={
                "externalPluggableDatabaseId": "ocid1.externalpluggabledatabase.oc1..mockextpdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetExternalPluggableDatabase(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetExternalPluggableDatabase",
            arguments={
                "externalPluggableDatabaseId": "ocid1.externalpluggabledatabase.oc1..mockextpdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateExternalPluggableDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateExternalPluggableDatabase",
            arguments={
                "externalPluggableDatabaseId": "ocid1.externalpluggabledatabase.oc1..mockextpdbid",
                "displayName": "Mock_Display_Name",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeExternalPluggableDatabaseCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeExternalPluggableDatabaseCompartment",
            arguments={
                "externalPluggableDatabaseId": "ocid1.externalpluggabledatabase.oc1..mockextpdbid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DisableExternalPluggableDatabaseDatabaseManagement(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DisableExternalPluggableDatabaseDatabaseManagement",
            arguments={
                "externalPluggableDatabaseId": "ocid1.externalpluggabledatabase.oc1..mockextpdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DisableExternalPluggableDatabaseOperationsInsights(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DisableExternalPluggableDatabaseOperationsInsights",
            arguments={
                "externalPluggableDatabaseId": "ocid1.externalpluggabledatabase.oc1..mockextpdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DisableExternalPluggableDatabaseStackMonitoring(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DisableExternalPluggableDatabaseStackMonitoring",
            arguments={
                "externalPluggableDatabaseId": "ocid1.externalpluggabledatabase.oc1..mockextpdbid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_EnableExternalPluggableDatabaseDatabaseManagement(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "EnableExternalPluggableDatabaseDatabaseManagement",
            arguments={
                "externalPluggableDatabaseId": "ocid1.externalpluggabledatabase.oc1..mockextpdbid",
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_EnableExternalPluggableDatabaseOperationsInsights(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "EnableExternalPluggableDatabaseOperationsInsights",
            arguments={
                "externalPluggableDatabaseId": "ocid1.externalpluggabledatabase.oc1..mockextpdbid",
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_EnableExternalPluggableDatabaseStackMonitoring(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "EnableExternalPluggableDatabaseStackMonitoring",
            arguments={
                "externalPluggableDatabaseId": "ocid1.externalpluggabledatabase.oc1..mockextpdbid",
                "externalDatabaseConnectorId": "ocid1.externaldatabaseconnector.oc1..mockextdbconnectorid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListGiVersions(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListGiVersions",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListGiVersionMinorVersions(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListGiVersionMinorVersions", arguments={"version": "1.0"}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListKeyStores(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListKeyStores",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateKeyStore(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateKeyStore",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
                "typeDetails_type": "VM_CLUSTER",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteKeyStore(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteKeyStore",
            arguments={"keyStoreId": "ocid1.keystore.oc1..mockkeystoreid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetKeyStore(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetKeyStore",
            arguments={"keyStoreId": "ocid1.keystore.oc1..mockkeystoreid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateKeyStore(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateKeyStore",
            arguments={
                "keyStoreId": "ocid1.keystore.oc1..mockkeystoreid",
                "typeDetails_type": "VM_CLUSTER",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeKeyStoreCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeKeyStoreCompartment",
            arguments={
                "keyStoreId": "ocid1.keystore.oc1..mockkeystoreid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListMaintenanceRunHistory(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListMaintenanceRunHistory",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetMaintenanceRunHistory(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetMaintenanceRunHistory",
            arguments={
                "maintenanceRunHistoryId": "ocid1.maintenancerunhistory.oc1..mockmrhistoryid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListMaintenanceRuns(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListMaintenanceRuns",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateMaintenanceRun(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateMaintenanceRun",
            arguments={
                "patchType": "GI",
                "targetResourceId": "ocid1.resource.oc1..mocktargetresourceid",
                "timeScheduled": "2025-01-01T00:00:00.000Z",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetMaintenanceRun(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetMaintenanceRun",
            arguments={"maintenanceRunId": "ocid1.maintenancerun.oc1..mockmrid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateMaintenanceRun(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateMaintenanceRun",
            arguments={"maintenanceRunId": "ocid1.maintenancerun.oc1..mockmrid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListOneoffPatches(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListOneoffPatches",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateOneoffPatch(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateOneoffPatch",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "dbVersion": "19.0.0.0",
                "displayName": "Mock_Display_Name",
                "releaseUpdate": "19.15",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteOneoffPatch(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteOneoffPatch",
            arguments={"oneoffPatchId": "ocid1.oneoffpatch.oc1..mockoneoffpatchid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetOneoffPatch(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetOneoffPatch",
            arguments={"oneoffPatchId": "ocid1.oneoffpatch.oc1..mockoneoffpatchid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateOneoffPatch(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateOneoffPatch",
            arguments={"oneoffPatchId": "ocid1.oneoffpatch.oc1..mockoneoffpatchid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeOneoffPatchCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeOneoffPatchCompartment",
            arguments={
                "oneoffPatchId": "ocid1.oneoffpatch.oc1..mockoneoffpatchid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DownloadOneoffPatch(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DownloadOneoffPatch",
            arguments={"oneoffPatchId": "ocid1.oneoffpatch.oc1..mockoneoffpatchid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListPluggableDatabases(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool("ListPluggableDatabases", arguments={})
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreatePluggableDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreatePluggableDatabase",
            arguments={
                "containerDatabaseId": "ocid1.database.oc1..mockcontainerdatabaseid",
                "pdbCreationTypeDetails_creationType": "LOCAL_CLONE",
                "pdbName": "PDB1",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeletePluggableDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeletePluggableDatabase",
            arguments={"pluggableDatabaseId": "ocid1.pluggabledatabase.oc1..mockpdbid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetPluggableDatabase(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetPluggableDatabase",
            arguments={"pluggableDatabaseId": "ocid1.pluggabledatabase.oc1..mockpdbid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdatePluggableDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdatePluggableDatabase",
            arguments={"pluggableDatabaseId": "ocid1.pluggabledatabase.oc1..mockpdbid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ConvertToRegularPluggableDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ConvertToRegularPluggableDatabase",
            arguments={"pluggableDatabaseId": "ocid1.pluggabledatabase.oc1..mockpdbid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RefreshPluggableDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RefreshPluggableDatabase",
            arguments={"pluggableDatabaseId": "ocid1.pluggabledatabase.oc1..mockpdbid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_StartPluggableDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "StartPluggableDatabase",
            arguments={"pluggableDatabaseId": "ocid1.pluggabledatabase.oc1..mockpdbid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_StopPluggableDatabase(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "StopPluggableDatabase",
            arguments={"pluggableDatabaseId": "ocid1.pluggabledatabase.oc1..mockpdbid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetResourcePrincipalToken(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetResourcePrincipalToken",
            arguments={"instanceId": "ocid1.instance.oc1..mockinstanceid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListParamsForActionType(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListParamsForActionType", arguments={"type": "FULL"}
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListScheduledActions(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListScheduledActions",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateScheduledAction(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateScheduledAction",
            arguments={
                "actionOrder": [1],
                "actionType": "DB_Server_Patching",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "schedulingPlanId": "ocid1.schedulingplan.oc1..mockschedulingplanid",
                "schedulingWindowId": "ocid1.schedulingwindow.oc1..mockschedulingwindowid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteScheduledAction(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteScheduledAction",
            arguments={
                "scheduledActionId": "ocid1.scheduledaction.oc1..mockscheduledactionid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetScheduledAction(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetScheduledAction",
            arguments={
                "scheduledActionId": "ocid1.scheduledaction.oc1..mockscheduledactionid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateScheduledAction(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateScheduledAction",
            arguments={
                "scheduledActionId": "ocid1.scheduledaction.oc1..mockscheduledactionid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListSchedulingPlans(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListSchedulingPlans",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateSchedulingPlan(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateSchedulingPlan",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "resourceId": "ocid1.resource.oc1..mockresourceid",
                "schedulingPolicyId": "ocid1.schedulingpolicy.oc1..mockschedulingpolicyid",
                "serviceType": "EXADATA",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteSchedulingPlan(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteSchedulingPlan",
            arguments={
                "schedulingPlanId": "ocid1.schedulingplan.oc1..mockschedulingplanid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetSchedulingPlan(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetSchedulingPlan",
            arguments={
                "schedulingPlanId": "ocid1.schedulingplan.oc1..mockschedulingplanid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeSchedulingPlanCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeSchedulingPlanCompartment",
            arguments={
                "schedulingPlanId": "ocid1.schedulingplan.oc1..mockschedulingplanid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ReorderScheduledActions(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ReorderScheduledActions",
            arguments={
                "schedulingPlanId": "ocid1.schedulingplan.oc1..mockschedulingplanid",
                "scheduledActionIdOrders": [
                    {"actionId": "ocid1.scheduledaction.oc1..id1", "order": 1}
                ],
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListSchedulingPolicies(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListSchedulingPolicies",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateSchedulingPolicy(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateSchedulingPolicy",
            arguments={
                "cadence": "MONTHLY",
                "cadenceStartMonth_name": "JANUARY",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "displayName": "Mock_Display_Name",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteSchedulingPolicy(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteSchedulingPolicy",
            arguments={
                "schedulingPolicyId": "ocid1.schedulingpolicy.oc1..mockschedulingpolicyid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetSchedulingPolicy(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetSchedulingPolicy",
            arguments={
                "schedulingPolicyId": "ocid1.schedulingpolicy.oc1..mockschedulingpolicyid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateSchedulingPolicy(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateSchedulingPolicy",
            arguments={
                "schedulingPolicyId": "ocid1.schedulingpolicy.oc1..mockschedulingpolicyid",
                "cadenceStartMonth_name": "JANUARY",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeSchedulingPolicyCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeSchedulingPolicyCompartment",
            arguments={
                "schedulingPolicyId": "ocid1.schedulingpolicy.oc1..mockschedulingpolicyid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListRecommendedScheduledActions(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListRecommendedScheduledActions",
            arguments={
                "schedulingPolicyId": "ocid1.schedulingpolicy.oc1..mockschedulingpolicyid",
                "schedulingPolicyTargetResourceId": "ocid1.resource.oc1..mockpolicytargetid",
                "planIntent": "EXADATA",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListSchedulingWindows(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListSchedulingWindows",
            arguments={
                "schedulingPolicyId": "ocid1.schedulingpolicy.oc1..mockschedulingpolicyid"
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateSchedulingWindow(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateSchedulingWindow",
            arguments={
                "schedulingPolicyId": "ocid1.schedulingpolicy.oc1..mockschedulingpolicyid",
                "windowPreference_daysOfWeek": [{"name": "SUNDAY"}],
                "windowPreference_duration": 4,
                "windowPreference_isEnforcedDuration": True,
                "windowPreference_startTime": "02:00",
                "windowPreference_weeksOfMonth": [1, 3],
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteSchedulingWindow(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteSchedulingWindow",
            arguments={
                "schedulingPolicyId": "ocid1.schedulingpolicy.oc1..mockschedulingpolicyid",
                "schedulingWindowId": "ocid1.schedulingwindow.oc1..mockschedulingwindowid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetSchedulingWindow(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetSchedulingWindow",
            arguments={
                "schedulingPolicyId": "ocid1.schedulingpolicy.oc1..mockschedulingpolicyid",
                "schedulingWindowId": "ocid1.schedulingwindow.oc1..mockschedulingwindowid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateSchedulingWindow(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateSchedulingWindow",
            arguments={
                "schedulingPolicyId": "ocid1.schedulingpolicy.oc1..mockschedulingpolicyid",
                "schedulingWindowId": "ocid1.schedulingwindow.oc1..mockschedulingwindowid",
                "windowPreference_daysOfWeek": [{"name": "SUNDAY"}],
                "windowPreference_duration": 4,
                "windowPreference_isEnforcedDuration": True,
                "windowPreference_startTime": "02:00",
                "windowPreference_weeksOfMonth": [1, 3],
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListSystemVersions(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListSystemVersions",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "shape": "Exadata.X8M",
                "giVersion": "19.0.0.0",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListVmClusters(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListVmClusters",
            arguments={"compartmentId": "ocid1.compartment.oc1..mockcompartmentid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_CreateVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "CreateVmCluster",
            arguments={
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
                "cpuCoreCount": 16,
                "displayName": "Mock_Display_Name",
                "exadataInfrastructureId": "ocid1.exadatainfrastructure.oc1..mockexadatainfraid",
                "giVersion": "19.0.0.0",
                "sshPublicKeys": ["ssh-rsa AAAAB3Nza... mockKey1"],
                "vmClusterNetworkId": "ocid1.vmclusternetwork.oc1..mockvmclusternetworkid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_DeleteVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "DeleteVmCluster",
            arguments={"vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetVmCluster(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetVmCluster",
            arguments={"vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_UpdateVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "UpdateVmCluster",
            arguments={"vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_AddVirtualMachineToVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "AddVirtualMachineToVmCluster",
            arguments={
                "vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid",
                "dbServers": [
                    "ocid1.dbserver.oc1..server1",
                    "ocid1.dbserver.oc1..server2",
                ],
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ChangeVmClusterCompartment(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ChangeVmClusterCompartment",
            arguments={
                "vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid",
                "compartmentId": "ocid1.compartment.oc1..mockcompartmentid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_RemoveVirtualMachineFromVmCluster(mock_invoke):
    mock_data = {}
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "RemoveVirtualMachineFromVmCluster",
            arguments={
                "vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid",
                "dbServers": [
                    "ocid1.dbserver.oc1..server1",
                    "ocid1.dbserver.oc1..server2",
                ],
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListVmClusterPatchHistoryEntries(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListVmClusterPatchHistoryEntries",
            arguments={"vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetVmClusterPatchHistoryEntry(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetVmClusterPatchHistoryEntry",
            arguments={
                "vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid",
                "patchHistoryEntryId": "ocid1.patchhistory.oc1..mockpatchhistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListVmClusterPatches(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListVmClusterPatches",
            arguments={"vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetVmClusterPatch(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetVmClusterPatch",
            arguments={
                "vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid",
                "patchId": "ocid1.patch.oc1..mockpatchid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListVmClusterUpdateHistoryEntries(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListVmClusterUpdateHistoryEntries",
            arguments={"vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetVmClusterUpdateHistoryEntry(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetVmClusterUpdateHistoryEntry",
            arguments={
                "vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid",
                "updateHistoryEntryId": "ocid1.updatehistory.oc1..mockupdatehistoryid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_ListVmClusterUpdates(mock_invoke):
    mock_data = [
        {
            "id": "ocid1.resource.oc1..fallbackmockid",
            "displayName": "Fallback_Mock_Resource",
            "lifecycleState": "AVAILABLE",
            "timeCreated": "2025-01-01T00:00:00.000Z",
        }
    ]
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "ListVmClusterUpdates",
            arguments={"vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid"},
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
@patch("oracle.oci_db_dynamic_mcp_server.server.invoke_oci_api")
async def test_GetVmClusterUpdate(mock_invoke):
    mock_data = {
        "id": "ocid1.resource.oc1..fallbackmockid",
        "displayName": "Fallback_Mock_Resource",
        "lifecycleState": "AVAILABLE",
        "timeCreated": "2025-01-01T00:00:00.000Z",
    }
    mock_invoke.return_value = {"status": 200, "data": mock_data}

    async with Client(mcp) as client:
        response = await client.call_tool(
            "GetVmClusterUpdate",
            arguments={
                "vmClusterId": "ocid1.vmcluster.oc1..mockvmclusterid",
                "updateId": "ocid1.update.oc1..mockupdateid",
            },
        )
        assert response is not None
        assert not response.is_error
        mock_invoke.assert_called_once()
