"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Annotated, Any, Optional

import oci
from fastmcp import FastMCP
from oci.database.models import (
    CreatePluggableDatabaseFromLocalCloneDetails,
    CreatePluggableDatabaseFromRelocateDetails,
    CreatePluggableDatabaseFromRemoteCloneDetails,
)
from oci.util import to_dict
from oracle.oci_database_mcp_server.models import (
    ApplicationVip,
    ApplicationVipSummary,
    AutonomousContainerDatabase,
    AutonomousContainerDatabaseDataguardAssociation,
    AutonomousContainerDatabaseResourceUsage,
    AutonomousContainerDatabaseSummary,
    AutonomousContainerDatabaseVersionSummary,
    AutonomousDatabase,
    AutonomousDatabaseBackup,
    AutonomousDatabaseBackupSummary,
    AutonomousDatabaseCharacterSets,
    AutonomousDatabaseDataguardAssociation,
    AutonomousDatabasePeerCollection,
    AutonomousDatabaseSoftwareImage,
    AutonomousDatabaseSoftwareImageCollection,
    AutonomousDatabaseSummary,
    AutonomousDatabaseWallet,
    AutonomousDbPreviewVersionSummary,
    AutonomousDbVersionSummary,
    AutonomousExadataInfrastructure,
    AutonomousPatch,
    AutonomousPatchSummary,
    AutonomousVirtualMachine,
    AutonomousVirtualMachineSummary,
    AutonomousVmCluster,
    AutonomousVmClusterResourceUsage,
    AutonomousVmClusterSummary,
    Backup,
    BackupDestination,
    BackupDestinationSummary,
    BackupSummary,
    CloudAutonomousVmCluster,
    CloudAutonomousVmClusterResourceUsage,
    CloudAutonomousVmClusterSummary,
    CloudExadataInfrastructure,
    CloudExadataInfrastructureSummary,
    CloudExadataInfrastructureUnallocatedResources,
    CloudVmCluster,
    CloudVmClusterSummary,
    ConsoleConnection,
    ConsoleConnectionSummary,
    ConsoleHistory,
    ConsoleHistoryCollection,
    CreatePluggableDatabaseDetails,
    Database,
    DatabaseSoftwareImage,
    DatabaseSoftwareImageSummary,
    DatabaseSummary,
    DatabaseUpgradeHistoryEntry,
    DataGuardAssociation,
    DataGuardAssociationSummary,
    DbHome,
    DbHomeSummary,
    DbNode,
    DbNodeSummary,
    DbServer,
    DbServerSummary,
    DbSystem,
    DbSystemComputePerformanceSummary,
    DbSystemShapeSummary,
    DbSystemStoragePerformanceSummary,
    DbSystemSummary,
    DbSystemUpgradeHistoryEntry,
    DbVersionSummary,
    ExadataInfrastructure,
    ExadataInfrastructureSummary,
    ExadataInfrastructureUnAllocatedResources,
    ExadataIormConfig,
    ExadbVmCluster,
    ExadbVmClusterSummary,
    ExadbVmClusterUpdate,
    ExadbVmClusterUpdateHistoryEntry,
    ExadbVmClusterUpdateSummary,
    ExascaleDbStorageVault,
    ExascaleDbStorageVaultSummary,
    ExecutionAction,
    ExecutionActionSummary,
    ExecutionWindow,
    ExecutionWindowSummary,
    ExternalBackupJob,
    ExternalContainerDatabase,
    ExternalContainerDatabaseSummary,
    ExternalDatabaseConnector,
    ExternalDatabaseConnectorSummary,
    ExternalNonContainerDatabase,
    ExternalNonContainerDatabaseSummary,
    ExternalPluggableDatabase,
    ExternalPluggableDatabaseSummary,
    FlexComponentCollection,
    GiMinorVersionSummary,
    GiVersionSummary,
    InfrastructureTargetVersion,
    KeyStore,
    KeyStoreSummary,
    MaintenanceRun,
    MaintenanceRunHistory,
    MaintenanceRunHistorySummary,
    MaintenanceRunSummary,
    OCPUs,
    OneoffPatch,
    OneoffPatchSummary,
    Patch,
    PatchHistoryEntry,
    PatchHistoryEntrySummary,
    PatchSummary,
    PdbConversionHistoryEntry,
    PluggableDatabase,
    PluggableDatabaseSummary,
    RefreshableCloneCollection,
    ResourcePoolShapeCollection,
    ScheduledAction,
    ScheduledActionCollection,
    SchedulingPlan,
    SchedulingPlanCollection,
    SchedulingPolicy,
    SchedulingPolicySummary,
    SchedulingWindow,
    SchedulingWindowSummary,
    SystemVersionCollection,
    Update,
    UpdateHistoryEntry,
    UpdatePluggableDatabaseDetails,
    UpdateSummary,
    VmCluster,
    VmClusterNetwork,
    VmClusterNetworkSummary,
    VmClusterSummary,
    VmClusterUpdate,
    VmClusterUpdateHistoryEntry,
    VmClusterUpdateSummary,
    map_applicationvip,
    map_applicationvipsummary,
    map_autonomouscontainerdatabase,
    map_autonomouscontainerdatabasedataguardassociation,
    map_autonomouscontainerdatabaseresourceusage,
    map_autonomouscontainerdatabasesummary,
    map_autonomouscontainerdatabaseversionsummary,
    map_autonomousdatabase,
    map_autonomousdatabasebackup,
    map_autonomousdatabasebackupsummary,
    map_autonomousdatabasecharactersets,
    map_autonomousdatabasedataguardassociation,
    map_autonomousdatabasepeercollection,
    map_autonomousdatabasesoftwareimage,
    map_autonomousdatabasesoftwareimagecollection,
    map_autonomousdatabasesummary,
    map_autonomousdatabasewallet,
    map_autonomousdbpreviewversionsummary,
    map_autonomousdbversionsummary,
    map_autonomousexadatainfrastructure,
    map_autonomouspatch,
    map_autonomouspatchsummary,
    map_autonomousvirtualmachine,
    map_autonomousvirtualmachinesummary,
    map_autonomousvmcluster,
    map_autonomousvmclusterresourceusage,
    map_autonomousvmclustersummary,
    map_backup,
    map_backupdestination,
    map_backupdestinationsummary,
    map_backupsummary,
    map_cloudautonomousvmcluster,
    map_cloudautonomousvmclusterresourceusage,
    map_cloudautonomousvmclustersummary,
    map_cloudexadatainfrastructure,
    map_cloudexadatainfrastructuresummary,
    map_cloudexadatainfrastructureunallocatedresources,
    map_cloudvmcluster,
    map_cloudvmclustersummary,
    map_consoleconnection,
    map_consoleconnectionsummary,
    map_consolehistory,
    map_consolehistorycollection,
    map_database,
    map_databasesoftwareimage,
    map_databasesoftwareimagesummary,
    map_databasesummary,
    map_databaseupgradehistoryentry,
    map_dataguardassociation,
    map_dataguardassociationsummary,
    map_dbhome,
    map_dbhomesummary,
    map_dbnode,
    map_dbnodesummary,
    map_dbserver,
    map_dbserversummary,
    map_dbsystem,
    map_dbsystemcomputeperformancesummary,
    map_dbsystemshapesummary,
    map_dbsystemstorageperformancesummary,
    map_dbsystemsummary,
    map_dbsystemupgradehistoryentry,
    map_dbversionsummary,
    map_exadatainfrastructure,
    map_exadatainfrastructuresummary,
    map_exadatainfrastructureunallocatedresources,
    map_exadataiormconfig,
    map_exadbvmcluster,
    map_exadbvmclustersummary,
    map_exadbvmclusterupdate,
    map_exadbvmclusterupdatehistoryentry,
    map_exadbvmclusterupdatesummary,
    map_exascaledbstoragevault,
    map_exascaledbstoragevaultsummary,
    map_executionaction,
    map_executionactionsummary,
    map_executionwindow,
    map_executionwindowsummary,
    map_externalbackupjob,
    map_externalcontainerdatabase,
    map_externalcontainerdatabasesummary,
    map_externaldatabaseconnector,
    map_externaldatabaseconnectorsummary,
    map_externalnoncontainerdatabase,
    map_externalnoncontainerdatabasesummary,
    map_externalpluggabledatabase,
    map_externalpluggabledatabasesummary,
    map_flexcomponentcollection,
    map_giminorversionsummary,
    map_giversionsummary,
    map_infrastructuretargetversion,
    map_keystore,
    map_keystoresummary,
    map_maintenancerun,
    map_maintenancerunhistory,
    map_maintenancerunhistorysummary,
    map_maintenancerunsummary,
    map_ocpus,
    map_oneoffpatch,
    map_oneoffpatchsummary,
    map_patch,
    map_patchhistoryentry,
    map_patchhistoryentrysummary,
    map_patchsummary,
    map_pdbconversionhistoryentry,
    map_pluggabledatabase,
    map_pluggabledatabasesummary,
    map_refreshableclonecollection,
    map_resourcepoolshapecollection,
    map_scheduledaction,
    map_scheduledactioncollection,
    map_schedulingplan,
    map_schedulingplancollection,
    map_schedulingpolicy,
    map_schedulingpolicysummary,
    map_schedulingwindow,
    map_schedulingwindowsummary,
    map_systemversioncollection,
    map_update,
    map_updatehistoryentry,
    map_updatesummary,
    map_vmcluster,
    map_vmclusternetwork,
    map_vmclusternetworksummary,
    map_vmclustersummary,
    map_vmclusterupdate,
    map_vmclusterupdatehistoryentry,
    map_vmclusterupdatesummary,
)

from . import __project__, __version__

logger = Logger(__name__, level="INFO")
mcp = FastMCP(name=__project__)


def get_database_client(region: str = None):
    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    if region is None:
        return oci.database.DatabaseClient(config, signer=signer)
    regional_config = config.copy()
    regional_config["region"] = region
    return oci.database.DatabaseClient(regional_config, signer=signer)


def call_create_pdb(client, details, opc_retry_token=None, opc_request_id=None):
    kwargs = {"create_pluggable_database_details": details.__dict__}
    if opc_retry_token:
        kwargs["opc_retry_token"] = opc_retry_token
    if opc_request_id:
        kwargs["opc_request_id"] = opc_request_id
    response = client.create_pluggable_database(**kwargs)
    return map_pluggabledatabase(response.data)


@mcp.tool(
    description="Fetches the public IP address for a specified Database. For a Pluggable Database, use it's container database id as input"
)
def get_public_ip_for_database(
    database_id: Annotated[
        str,
        "The database `OCID` ",
    ],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> Optional[str]:
    try:
        logger.info(f"Fetching public IP for Database: {database_id}")
        client = get_database_client(region)

        get_database_response = client.get_database(database_id=database_id)
        database = get_database_response.data

        db_system_id = database.db_system_id
        vm_cluster_id = getattr(database, "vm_cluster_id", None)
        compartment_id = database.compartment_id

        # Prepare arguments for list_db_nodes
        kwargs = {"compartment_id": compartment_id}

        if db_system_id:
            kwargs["db_system_id"] = db_system_id
        elif vm_cluster_id:
            kwargs["vm_cluster_id"] = vm_cluster_id
        else:
            logger.error(
                f"Database {database_id} is not associated with a DB System or VM Cluster."
            )
            return None

        # Get all DB nodes
        try:
            list_db_nodes_response = client.list_db_nodes(**kwargs)
            db_nodes = list_db_nodes_response.data
        except oci.exceptions.ServiceError as e:
            logger.error(f"Service error while listing DB nodes: {e}")
            return None

        if not db_nodes:
            return None

        # Initialize Virtual Network Client
        config = oci.config.from_file(
            profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
        )
        private_key = oci.signer.load_private_key_from_file(config["key_file"])
        token_file = config["security_token_file"]
        with open(token_file, "r") as f:
            token = f.read()
        signer = oci.auth.signers.SecurityTokenSigner(token, private_key)

        virtual_network_client = oci.core.VirtualNetworkClient(config, signer=signer)
        if region:
            virtual_network_client.base_client.set_region(region)

        # Iterate through nodes to find one with a valid VNIC and Public IP
        found_public_ip = None

        for node in db_nodes:
            # Safety Check: Skip nodes with no VNIC ID
            if not node.vnic_id:
                continue

            try:
                # Fetch VNIC details
                get_vnic_response = virtual_network_client.get_vnic(node.vnic_id)
                vnic = get_vnic_response.data

                # Check for Public IP
                if vnic.public_ip:
                    found_public_ip = vnic.public_ip
                    break  # Stop once we find a valid IP

            except Exception:
                continue

        if found_public_ip:
            return found_public_ip

        logger.warning(
            f"No public IP found for any active VNIC in the Database cluster."
        )
        return None

    except Exception as e:
        logger.error(f"Error in get_public_ip_for_db tool: {e}")
        raise


@mcp.tool(description="Deletes the specified pluggable database.")
def delete_pluggable_database(
    pluggable_database_id: Annotated[
        Optional[str],
        "The database `OCID` ",
    ],
    if_match: Annotated[
        Optional[str],
        "For optimistic concurrency control. In the PUT or DELETE call for a resource, set the `if-match` parameter to the value of the etag from a previous GET or POST response for that resource. The resource will be updated or deleted only if the etag you provide matches the resource's current etag value.",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> Any:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["pluggable_database_id"] = pluggable_database_id
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.delete_pluggable_database(**kwargs)
        return to_dict(response.data)
    except Exception as e:
        logger.error(f"Error in delete_pluggable_database tool: {e}")
        raise


@mcp.tool(description="Gets information about the specified pluggable database.")
def get_pluggable_database(
    pluggable_database_id: Annotated[
        Optional[str],
        "The database `OCID` ",
    ],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> PluggableDatabase:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["pluggable_database_id"] = pluggable_database_id
        response: oci.response.Response = client.get_pluggable_database(**kwargs)
        return map_pluggabledatabase(response.data)

    except Exception as e:
        logger.error(f"Error in get_pluggable_database tool: {e}")
        raise


@mcp.tool(description="Updates the specified pluggable database.")
def update_pluggable_database(
    pluggable_database_id: Annotated[
        Optional[str],
        "The database `OCID` ",
    ],
    update_pluggable_database_details: Annotated[
        dict | UpdatePluggableDatabaseDetails,
        "Request to perform pluggable database update.",
    ],
    if_match: Annotated[
        Optional[str],
        "For optimistic concurrency control. In the PUT or DELETE call for a resource, set the `if-match` parameter to the value of the etag from a previous GET or POST response for that resource. The resource will be updated or deleted only if the etag you provide matches the resource's current etag value.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> PluggableDatabase:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["pluggable_database_id"] = pluggable_database_id
        if isinstance(
            update_pluggable_database_details, UpdatePluggableDatabaseDetails
        ):
            kwargs["update_pluggable_database_details"] = to_dict(
                update_pluggable_database_details
            )
        else:
            kwargs["update_pluggable_database_details"] = (
                update_pluggable_database_details
            )
        if if_match is not None:
            kwargs["if_match"] = if_match
        response: oci.response.Response = client.update_pluggable_database(**kwargs)
        return map_pluggabledatabase(response.data)
    except Exception as e:
        logger.error(f"Error in update_pluggable_database tool: {e}")
        raise


@mcp.tool(description="Create a new pluggable database.")
def create_pluggable_database(
    pdb_name: str,
    container_database_id: str,
    pdb_admin_password: str,
    tde_wallet_password: Optional[str] = None,
    should_pdb_admin_account_be_locked: Optional[bool] = None,
    container_database_admin_password: Optional[str] = None,
    should_create_pdb_backup: Optional[bool] = None,
    freeform_tags: Optional[dict] = None,
    defined_tags: Optional[dict] = None,
    opc_retry_token: Optional[str] = None,
    opc_request_id: Optional[str] = None,
    region: Optional[str] = None,
):
    try:
        client = get_database_client(region)

        details = oci.database.models.CreatePluggableDatabaseDetails(
            pdb_name=pdb_name,
            container_database_id=container_database_id,
            pdb_admin_password=pdb_admin_password,
            tde_wallet_password=tde_wallet_password,
            container_database_admin_password=container_database_admin_password,
            should_pdb_admin_account_be_locked=should_pdb_admin_account_be_locked,
            should_create_pdb_backup=should_create_pdb_backup,
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )

        kwargs = {"create_pluggable_database_details": details}
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token

        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        resp = client.create_pluggable_database(**kwargs)
        return map_pluggabledatabase(resp.data)

    except Exception as e:
        logger.error(f"Error in create_pdb_new: {e}")
        raise


@mcp.tool(
    description="Create a pluggable database from a local clone (LOCAL_CLONE_PDB)."
)
def create_pluggable_database_from_local_clone(
    pdb_name: str,
    container_database_id: str,
    pdb_admin_password: str,
    source_pluggable_database_id: str,
    is_thin_clone: Optional[bool] = None,
    source_pluggable_database_snapshot_id: Optional[str] = None,
    tde_wallet_password: Optional[str] = None,
    container_database_admin_password: Optional[str] = None,
    should_pdb_admin_account_be_locked: Optional[bool] = None,
    should_create_pdb_backup: Optional[bool] = None,
    freeform_tags: Optional[dict] = None,
    defined_tags: Optional[dict] = None,
    opc_retry_token: Optional[str] = None,
    opc_request_id: Optional[str] = None,
    region: Optional[str] = None,
):
    try:
        client = get_database_client(region)

        clone_details = CreatePluggableDatabaseFromLocalCloneDetails(
            creation_type="LOCAL_CLONE_PDB",
            source_pluggable_database_snapshot_id=source_pluggable_database_snapshot_id,
            is_thin_clone=is_thin_clone,
            source_pluggable_database_id=source_pluggable_database_id,
        )

        details = CreatePluggableDatabaseDetails(
            pdb_name=pdb_name,
            container_database_id=container_database_id,
            pdb_admin_password=pdb_admin_password,
            tde_wallet_password=tde_wallet_password,
            container_database_admin_password=container_database_admin_password,
            should_pdb_admin_account_be_locked=should_pdb_admin_account_be_locked,
            should_create_pdb_backup=should_create_pdb_backup,
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
            pdb_creation_type_details=to_dict(clone_details),
        )

        return call_create_pdb(client, details, opc_retry_token, opc_request_id)

    except Exception as e:
        logger.error(f"Error in create_pdb_from_local_clone: {e}")
        raise


# 2) Remote Clone
@mcp.tool(
    description="Create a pluggable database by cloning from a remote source CDB (REMOTE_CLONE_PDB)."
)
def create_pluggable_database_from_remote_clone(
    pdb_name: str,
    container_database_id: str,
    pdb_admin_password: str,
    source_pluggable_database_id: str,
    source_container_database_admin_password: str,
    dblink_username: Optional[str] = None,
    dblink_user_password: Optional[str] = None,
    tde_wallet_password: Optional[str] = None,
    container_database_admin_password: Optional[str] = None,
    should_pdb_admin_account_be_locked: Optional[bool] = None,
    should_create_pdb_backup: Optional[bool] = None,
    freeform_tags: Optional[dict] = None,
    defined_tags: Optional[dict] = None,
    opc_retry_token: Optional[str] = None,
    opc_request_id: Optional[str] = None,
    region: Optional[str] = None,
):
    try:
        client = get_database_client(region)

        remote_details = CreatePluggableDatabaseFromRemoteCloneDetails(
            creation_type="REMOTE_CLONE_PDB",
            dblink_username=dblink_username,
            dblink_user_password=dblink_user_password,
            source_pluggable_database_id=source_pluggable_database_id,
            source_container_database_admin_password=source_container_database_admin_password,
        )

        details = CreatePluggableDatabaseDetails(
            pdb_name=pdb_name,
            container_database_id=container_database_id,
            pdb_admin_password=pdb_admin_password,
            tde_wallet_password=tde_wallet_password,
            container_database_admin_password=container_database_admin_password,
            should_pdb_admin_account_be_locked=should_pdb_admin_account_be_locked,
            should_create_pdb_backup=should_create_pdb_backup,
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
            pdb_creation_type_details=to_dict(remote_details),
        )

        return call_create_pdb(client, details, opc_retry_token, opc_request_id)

    except Exception as e:
        logger.error(f"Error in create_pdb_from_remote_clone: {e}")
        raise


@mcp.tool(
    description="Relocate (move) a pluggable database from a source CDB into the target CDB (RELOCATE_PDB)."
)
def create_pluggable_database_from_relocate(
    pdb_name: str,
    container_database_id: str,
    pdb_admin_password: str,
    source_pluggable_database_id: str,
    source_container_database_admin_password: str,
    dblink_username: Optional[str] = None,
    dblink_user_password: Optional[str] = None,
    tde_wallet_password: Optional[str] = None,
    container_database_admin_password: Optional[str] = None,
    should_pdb_admin_account_be_locked: Optional[bool] = None,
    should_create_pdb_backup: Optional[bool] = None,
    freeform_tags: Optional[dict] = None,
    defined_tags: Optional[dict] = None,
    opc_retry_token: Optional[str] = None,
    opc_request_id: Optional[str] = None,
    region: Optional[str] = None,
):
    try:
        client = get_database_client(region)

        relocate_details = CreatePluggableDatabaseFromRelocateDetails(
            creation_type="RELOCATE_PDB",
            dblink_username=dblink_username,
            dblink_user_password=dblink_user_password,
            source_pluggable_database_id=source_pluggable_database_id,
            source_container_database_admin_password=source_container_database_admin_password,
        )

        details = CreatePluggableDatabaseDetails(
            pdb_name=pdb_name,
            container_database_id=container_database_id,
            pdb_admin_password=pdb_admin_password,
            tde_wallet_password=tde_wallet_password,
            container_database_admin_password=container_database_admin_password,
            should_pdb_admin_account_be_locked=should_pdb_admin_account_be_locked,
            should_create_pdb_backup=should_create_pdb_backup,
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
            pdb_creation_type_details=to_dict(relocate_details),
        )

        return call_create_pdb(client, details, opc_retry_token, opc_request_id)

    except Exception as e:
        logger.error(f"Error in create_pdb_from_relocate: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of application virtual IP (VIP) addresses on a cloud VM cluster."
    )
)
def list_application_vips(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    cloud_vm_cluster_id: Annotated[
        Optional[Any],
        (
            "The `OCID` of the cloud VM cluster associated with the"
            "application virtual IP (VIP) address."
        ),
    ],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"DISPLAYNAME", "TIMECREATED"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "TERMINATING",'
            '"TERMINATED", "FAILED"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ApplicationVipSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        kwargs["cloud_vm_cluster_id"] = cloud_vm_cluster_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        response: oci.response.Response = client.list_application_vips(**kwargs)
        return [map_applicationvipsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_application_vips tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the Autonomous Container Databases with Autonomous Data Guard-"
        "enabled associated with the specified Autonomous Container Database."
    )
)
def list_autonomous_container_database_dataguard_associations(
    autonomous_container_database_id: Annotated[
        Optional[Any], ("The Autonomous Container Database `OCID`.")
    ],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousContainerDatabaseDataguardAssociation]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_container_database_id"] = autonomous_container_database_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = (
            client.list_autonomous_container_database_dataguard_associations(**kwargs)
        )
        return [
            map_autonomouscontainerdatabasedataguardassociation(item)
            for item in response.data
        ]
    except Exception as e:
        logger.error(
            f"Error in list_autonomous_container_database_dataguard_associations tool: {e}"
        )
        raise


@mcp.tool(
    description=("Gets a list of supported Autonomous Container Database versions.")
)
def list_autonomous_container_database_versions(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    service_component: Annotated[
        Optional[Any],
        (
            "The service component to use, either ADBD or EXACC. Allowed"
            'values are: "ADBD", "EXACC"'
        ),
    ],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousContainerDatabaseVersionSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        kwargs["service_component"] = service_component
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        response: oci.response.Response = (
            client.list_autonomous_container_database_versions(**kwargs)
        )
        return [
            map_autonomouscontainerdatabaseversionsummary(item)
            for item in response.data
        ]
    except Exception as e:
        logger.error(f"Error in list_autonomous_container_database_versions tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the Autonomous Container Databases in the specified compartment."
    )
)
def list_autonomous_container_databases(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    autonomous_exadata_infrastructure_id: Annotated[
        Optional[Any], ("The Autonomous Exadata Infrastructure `OCID`.")
    ] = None,
    autonomous_vm_cluster_id: Annotated[
        Optional[Any], ("The Autonomous VM Cluster `OCID`.")
    ] = None,
    infrastructure_type: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'Infrastructure Type. Allowed values are: "CLOUD",'
            '"CLOUD_AT_CUSTOMER"'
        ),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. **Note:** If you do not"
            "include the availability domain filter, the resources are"
            "grouped by availability domain, then sorted. Allowed values"
            'are: "TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED",'
            '"BACKUP_IN_PROGRESS", "RESTORING", "RESTORE_FAILED",'
            '"RESTARTING", "MAINTENANCE_IN_PROGRESS",'
            '"ROLE_CHANGE_IN_PROGRESS",'
            '"ENABLING_AUTONOMOUS_DATA_GUARD", "UNAVAILABLE"'
        ),
    ] = None,
    availability_domain: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "availability domain exactly."
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    service_level_agreement_type: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "service-level agreement type exactly."
        ),
    ] = None,
    cloud_autonomous_vm_cluster_id: Annotated[
        Optional[Any], ("The cloud Autonomous VM Cluster `OCID`.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousContainerDatabaseSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if autonomous_exadata_infrastructure_id is not None:
            kwargs["autonomous_exadata_infrastructure_id"] = (
                autonomous_exadata_infrastructure_id
            )
        if autonomous_vm_cluster_id is not None:
            kwargs["autonomous_vm_cluster_id"] = autonomous_vm_cluster_id
        if infrastructure_type is not None:
            kwargs["infrastructure_type"] = infrastructure_type
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if availability_domain is not None:
            kwargs["availability_domain"] = availability_domain
        if display_name is not None:
            kwargs["display_name"] = display_name
        if service_level_agreement_type is not None:
            kwargs["service_level_agreement_type"] = service_level_agreement_type
        if cloud_autonomous_vm_cluster_id is not None:
            kwargs["cloud_autonomous_vm_cluster_id"] = cloud_autonomous_vm_cluster_id
        response: oci.response.Response = client.list_autonomous_container_databases(
            **kwargs
        )
        return [map_autonomouscontainerdatabasesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_autonomous_container_databases tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of Autonomous Database backups based on either the"
        "`autonomousDatabaseId` or `compartmentId` specified as a query parameter."
    )
)
def list_autonomous_database_backups(
    autonomous_database_id: Annotated[Optional[Any], ("The database `OCID`.")] = None,
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. **Note:** If you do not"
            "include the availability domain filter, the resources are"
            "grouped by availability domain, then sorted. Allowed values"
            'are: "TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "CREATING",'
            '"ACTIVE", "DELETING", "DELETED", "FAILED",'
            '"UPDATING"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    type: Annotated[
        Optional[Any],
        (
            "A filter to return only backups that matches with the given"
            "type of Backup."
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousDatabaseBackupSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        if autonomous_database_id is not None:
            kwargs["autonomous_database_id"] = autonomous_database_id
        if compartment_id is not None:
            kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        if type is not None:
            kwargs["type"] = type
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_autonomous_database_backups(
            **kwargs
        )
        return [map_autonomousdatabasebackupsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_autonomous_database_backups tool: {e}")
        raise


@mcp.tool(description=("Gets a list of supported character sets."))
def list_autonomous_database_character_sets(
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    is_shared: Annotated[
        Optional[Any],
        (
            "Specifies whether this request is for an Autonomous Database"
            "Serverless instance. By default, this request will be for"
            "Autonomous Database on Dedicated Exadata Infrastructure."
        ),
    ] = None,
    is_dedicated: Annotated[
        Optional[Any],
        (
            "Specifies if the request is for an Autonomous Database"
            "Dedicated instance. The default request is for an Autonomous"
            "Database Dedicated instance."
        ),
    ] = None,
    character_set_type: Annotated[
        Optional[Any],
        (
            "Specifies whether this request pertains to database"
            "character sets or national character sets. Allowed values"
            'are: "DATABASE", "NATIONAL"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousDatabaseCharacterSets]:
    try:
        client = get_database_client(region)
        kwargs = {}
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if is_shared is not None:
            kwargs["is_shared"] = is_shared
        if is_dedicated is not None:
            kwargs["is_dedicated"] = is_dedicated
        if character_set_type is not None:
            kwargs["character_set_type"] = character_set_type
        response: oci.response.Response = (
            client.list_autonomous_database_character_sets(**kwargs)
        )
        return [map_autonomousdatabasecharactersets(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_autonomous_database_character_sets tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the Autonomous Database clones for the specified Autonomous Database."
    )
)
def list_autonomous_database_clones(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    autonomous_database_id: Annotated[Optional[Any], ("The database `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "STOPPING", "STOPPED",'
            '"STARTING", "TERMINATING", "TERMINATED",'
            '"UNAVAILABLE", "RESTORE_IN_PROGRESS",'
            '"RESTORE_FAILED", "BACKUP_IN_PROGRESS",'
            '"SCALE_IN_PROGRESS", "AVAILABLE_NEEDS_ATTENTION",'
            '"UPDATING", "MAINTENANCE_IN_PROGRESS", "RESTARTING",'
            '"RECREATING", "ROLE_CHANGE_IN_PROGRESS", "UPGRADING",'
            '"INACCESSIBLE", "STANDBY"'
        ),
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. **Note:** If you do not"
            "include the availability domain filter, the resources are"
            "grouped by availability domain, then sorted. Allowed values"
            'are: "NONE", "TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    clone_type: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given clone"
            'type exactly. Allowed values are: "REFRESHABLE_CLONE"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousDatabaseSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        kwargs["autonomous_database_id"] = autonomous_database_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if display_name is not None:
            kwargs["display_name"] = display_name
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if clone_type is not None:
            kwargs["clone_type"] = clone_type
        response: oci.response.Response = client.list_autonomous_database_clones(
            **kwargs
        )
        return [map_autonomousdatabasesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_autonomous_database_clones tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the Autonomous Data Guard-enabled databases associated with the"
        "specified Autonomous Database."
    )
)
def list_autonomous_database_dataguard_associations(
    autonomous_database_id: Annotated[Optional[Any], ("The database `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousDatabaseDataguardAssociation]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_database_id"] = autonomous_database_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = (
            client.list_autonomous_database_dataguard_associations(**kwargs)
        )
        return [
            map_autonomousdatabasedataguardassociation(item) for item in response.data
        ]
    except Exception as e:
        logger.error(
            f"Error in list_autonomous_database_dataguard_associations tool: {e}"
        )
        raise


@mcp.tool(
    description=(
        "Lists the Autonomous Database peers for the specified Autonomous Database."
    )
)
def list_autonomous_database_peers(
    autonomous_database_id: Annotated[Optional[Any], ("The database `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousDatabasePeerCollection]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_database_id"] = autonomous_database_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_autonomous_database_peers(
            **kwargs
        )
        return [map_autonomousdatabasepeercollection(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_autonomous_database_peers tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the OCIDs of the Autonomous Database local and connected remote"
        "refreshable clones with the region where they exist for the specified source"
        "database."
    )
)
def list_autonomous_database_refreshable_clones(
    autonomous_database_id: Annotated[Optional[Any], ("The database `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[RefreshableCloneCollection]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_database_id"] = autonomous_database_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = (
            client.list_autonomous_database_refreshable_clones(**kwargs)
        )
        return [map_refreshableclonecollection(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_autonomous_database_refreshable_clones tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the Autonomous Database Software Images in the specified"
        "compartment."
    )
)
def list_autonomous_database_software_images(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    image_shape_family: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given image"
            'shape family exactly. Allowed values are: "EXACC_SHAPE",'
            '"EXADATA_SHAPE"'
        ),
    ],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "parameter according to which Autonomous Database Software"
            'Images will be sorted. Allowed values are: "TIMECREATED",'
            '"DISPLAYNAME"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "AVAILABLE",'
            '"FAILED", "PROVISIONING", "EXPIRED", "TERMINATED",'
            '"TERMINATING", "UPDATING"'
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousDatabaseSoftwareImageCollection]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        kwargs["image_shape_family"] = image_shape_family
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = (
            client.list_autonomous_database_software_images(**kwargs)
        )
        return [
            map_autonomousdatabasesoftwareimagecollection(item)
            for item in response.data
        ]
    except Exception as e:
        logger.error(f"Error in list_autonomous_database_software_images tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of Autonomous Databases based on the query parameters specified."
    )
)
def list_autonomous_databases(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    autonomous_container_database_id: Annotated[
        Optional[Any], ("The Autonomous Container Database `OCID`.")
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. **Note:** If you do not"
            "include the availability domain filter, the resources are"
            "grouped by availability domain, then sorted. Allowed values"
            'are: "TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    infrastructure_type: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'Infrastructure Type. Allowed values are: "CLOUD",'
            '"CLOUD_AT_CUSTOMER"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "STOPPING", "STOPPED",'
            '"STARTING", "TERMINATING", "TERMINATED",'
            '"UNAVAILABLE", "RESTORE_IN_PROGRESS",'
            '"RESTORE_FAILED", "BACKUP_IN_PROGRESS",'
            '"SCALE_IN_PROGRESS", "AVAILABLE_NEEDS_ATTENTION",'
            '"UPDATING", "MAINTENANCE_IN_PROGRESS", "RESTARTING",'
            '"RECREATING", "ROLE_CHANGE_IN_PROGRESS", "UPGRADING",'
            '"INACCESSIBLE", "STANDBY"'
        ),
    ] = None,
    lifecycle_state_not_equal_to: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that not match the given"
            'lifecycle state. Allowed values are: "PROVISIONING",'
            '"AVAILABLE", "STOPPING", "STOPPED", "STARTING",'
            '"TERMINATING", "TERMINATED", "UNAVAILABLE",'
            '"RESTORE_IN_PROGRESS", "RESTORE_FAILED",'
            '"BACKUP_IN_PROGRESS", "SCALE_IN_PROGRESS",'
            '"AVAILABLE_NEEDS_ATTENTION", "UPDATING",'
            '"MAINTENANCE_IN_PROGRESS", "RESTARTING", "RECREATING",'
            '"ROLE_CHANGE_IN_PROGRESS", "UPGRADING",'
            '"INACCESSIBLE", "STANDBY"'
        ),
    ] = None,
    db_workload: Annotated[
        Optional[Any],
        (
            "A filter to return only autonomous database resources that"
            "match the specified workload type. Allowed values are:"
            '"OLTP", "DW", "AJD", "APEX"'
        ),
    ] = None,
    db_version: Annotated[
        Optional[Any],
        (
            "A filter to return only autonomous database resources that"
            "match the specified dbVersion."
        ),
    ] = None,
    is_free_tier: Annotated[
        Optional[Any],
        (
            "Filter on the value of the resource's 'isFreeTier' property."
            "A value of `true` returns only Always Free resources. A"
            "value of `false` excludes Always Free resources from the"
            "returned results. Omitting this parameter returns both"
            "Always Free and paid resources."
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    is_refreshable_clone: Annotated[
        Optional[Any],
        (
            "Filter on the value of the resource's 'isRefreshableClone'"
            "property. A value of `true` returns only refreshable clones."
            "A value of `false` excludes refreshable clones from the"
            "returned results. Omitting this parameter returns both"
            "refreshable clones and databases that are not refreshable"
            "clones."
        ),
    ] = None,
    is_data_guard_enabled: Annotated[
        Optional[Any],
        ("A filter to return only resources that have Data Guard" "enabled."),
    ] = None,
    is_resource_pool_leader: Annotated[
        Optional[Any],
        (
            "Filter if the resource is the resource pool leader. A value"
            "of `true` returns only resource pool leader."
        ),
    ] = None,
    resource_pool_leader_id: Annotated[
        Optional[Any],
        ("The database `OCID` of the resourcepool Leader Autonomous" "Database."),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousDatabaseSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if autonomous_container_database_id is not None:
            kwargs["autonomous_container_database_id"] = (
                autonomous_container_database_id
            )
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if infrastructure_type is not None:
            kwargs["infrastructure_type"] = infrastructure_type
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if lifecycle_state_not_equal_to is not None:
            kwargs["lifecycle_state_not_equal_to"] = lifecycle_state_not_equal_to
        if db_workload is not None:
            kwargs["db_workload"] = db_workload
        if db_version is not None:
            kwargs["db_version"] = db_version
        if is_free_tier is not None:
            kwargs["is_free_tier"] = is_free_tier
        if display_name is not None:
            kwargs["display_name"] = display_name
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if is_refreshable_clone is not None:
            kwargs["is_refreshable_clone"] = is_refreshable_clone
        if is_data_guard_enabled is not None:
            kwargs["is_data_guard_enabled"] = is_data_guard_enabled
        if is_resource_pool_leader is not None:
            kwargs["is_resource_pool_leader"] = is_resource_pool_leader
        if resource_pool_leader_id is not None:
            kwargs["resource_pool_leader_id"] = resource_pool_leader_id
        response: oci.response.Response = client.list_autonomous_databases(**kwargs)
        return [map_autonomousdatabasesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_autonomous_databases tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of supported Autonomous Database versions. Note that preview version"
        "software is only available for"
    )
)
def list_autonomous_db_preview_versions(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for DBWORKLOAD is ascending."
            "**Note:** If you do not include the availability domain"
            "filter, the resources are grouped by availability domain,"
            'then sorted. Allowed values are: "DBWORKLOAD"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousDbPreviewVersionSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        response: oci.response.Response = client.list_autonomous_db_preview_versions(
            **kwargs
        )
        return [map_autonomousdbpreviewversionsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_autonomous_db_preview_versions tool: {e}")
        raise


@mcp.tool(description=("Gets a list of supported Autonomous Database versions."))
def list_autonomous_db_versions(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    db_workload: Annotated[
        Optional[Any],
        (
            "A filter to return only autonomous database resources that"
            "match the specified workload type. Allowed values are:"
            '"OLTP", "DW", "AJD", "APEX"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousDbVersionSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if db_workload is not None:
            kwargs["db_workload"] = db_workload
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        response: oci.response.Response = client.list_autonomous_db_versions(**kwargs)
        return [map_autonomousdbversionsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_autonomous_db_versions tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the Autonomous Virtual Machines in the specified Autonomous VM Cluster and"
        "Compartment."
    )
)
def list_autonomous_virtual_machines(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    autonomous_vm_cluster_id: Annotated[
        Optional[Any], ("The Autonomous Virtual machine `OCID`.")
    ],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED",'
            '"MAINTENANCE_IN_PROGRESS"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousVirtualMachineSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        kwargs["autonomous_vm_cluster_id"] = autonomous_vm_cluster_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        response: oci.response.Response = client.list_autonomous_virtual_machines(
            **kwargs
        )
        return [map_autonomousvirtualmachinesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_autonomous_virtual_machines tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of Exadata Cloud@Customer Autonomous VM clusters in the specified"
        "compartment. To list Autonomous VM Clusters in the Oracle Cloud, see"
        ":func:`list_cloud_autonomous_vm_clusters`."
    )
)
def list_autonomous_vm_clusters(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    exadata_infrastructure_id: Annotated[
        Optional[Any],
        ("If provided, filters the results for the given Exadata" "Infrastructure."),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED",'
            '"MAINTENANCE_IN_PROGRESS"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousVmClusterSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if exadata_infrastructure_id is not None:
            kwargs["exadata_infrastructure_id"] = exadata_infrastructure_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_autonomous_vm_clusters(**kwargs)
        return [map_autonomousvmclustersummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_autonomous_vm_clusters tool: {e}")
        raise


@mcp.tool(
    description=("Gets a list of backup destinations in the specified compartment.")
)
def list_backup_destination(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    type: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given type"
            "of the Backup Destination."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[BackupDestinationSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if type is not None:
            kwargs["type"] = type
        response: oci.response.Response = client.list_backup_destination(**kwargs)
        return [map_backupdestinationsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_backup_destination tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of backups based on the `databaseId` or `compartmentId` specified."
        "Either one of these query parameters must be provided."
    )
)
def list_backups(
    database_id: Annotated[Optional[Any], ("The `OCID` of the database.")] = None,
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    shape_family: Annotated[
        Optional[Any],
        (
            "If provided, filters the results to the set of database"
            "versions which are supported for the given shape family."
            'Allowed values are: "SINGLENODE", "YODA",'
            '"VIRTUALMACHINE", "EXADATA", "EXACC", "EXADB_XS"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[BackupSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        if database_id is not None:
            kwargs["database_id"] = database_id
        if compartment_id is not None:
            kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if shape_family is not None:
            kwargs["shape_family"] = shape_family
        response: oci.response.Response = client.list_backups(**kwargs)
        return [map_backupsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_backups tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists Autonomous Exadata VM clusters in the Oracle cloud. For Exadata"
        "Cloud@Customer systems, see :func:`list_autonomous_vm_clusters`."
    )
)
def list_cloud_autonomous_vm_clusters(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    cloud_exadata_infrastructure_id: Annotated[
        Optional[Any],
        (
            "If provided, filters the results for the specified cloud"
            "Exadata infrastructure."
        ),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED",'
            '"MAINTENANCE_IN_PROGRESS"'
        ),
    ] = None,
    availability_domain: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "availability domain exactly."
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[CloudAutonomousVmClusterSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if cloud_exadata_infrastructure_id is not None:
            kwargs["cloud_exadata_infrastructure_id"] = cloud_exadata_infrastructure_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if availability_domain is not None:
            kwargs["availability_domain"] = availability_domain
        if display_name is not None:
            kwargs["display_name"] = display_name
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_cloud_autonomous_vm_clusters(
            **kwargs
        )
        return [map_cloudautonomousvmclustersummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_cloud_autonomous_vm_clusters tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the cloud Exadata infrastructure resources in the specified"
        "compartment. Applies to Exadata Cloud Service instances and Autonomous Database"
        "on dedicated Exadata infrastructure only."
    )
)
def list_cloud_exadata_infrastructures(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED",'
            '"MAINTENANCE_IN_PROGRESS"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    cluster_placement_group_id: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "cluster placement group ID exactly."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[CloudExadataInfrastructureSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        if cluster_placement_group_id is not None:
            kwargs["cluster_placement_group_id"] = cluster_placement_group_id
        response: oci.response.Response = client.list_cloud_exadata_infrastructures(
            **kwargs
        )
        return [map_cloudexadatainfrastructuresummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_cloud_exadata_infrastructures tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the maintenance updates that can be applied to the specified cloud VM"
        "cluster. Applies to Exadata Cloud Service instances only."
    )
)
def list_cloud_vm_cluster_updates(
    cloud_vm_cluster_id: Annotated[Optional[Any], ("The cloud VM cluster `OCID`.")],
    update_type: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'update type exactly. Allowed values are: "GI_UPGRADE",'
            '"GI_PATCH", "OS_UPDATE"'
        ),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[UpdateSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["cloud_vm_cluster_id"] = cloud_vm_cluster_id
        if update_type is not None:
            kwargs["update_type"] = update_type
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_cloud_vm_cluster_updates(**kwargs)
        return [map_updatesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_cloud_vm_cluster_updates tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the cloud VM clusters in the specified compartment. Applies to"
        "Exadata Cloud Service instances and Autonomous Database on dedicated Exadata"
        "infrastructure only."
    )
)
def list_cloud_vm_clusters(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    cloud_exadata_infrastructure_id: Annotated[
        Optional[Any],
        (
            "If provided, filters the results for the specified cloud"
            "Exadata infrastructure."
        ),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only cloud VM clusters that match the"
            "given lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED",'
            '"MAINTENANCE_IN_PROGRESS"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[CloudVmClusterSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if cloud_exadata_infrastructure_id is not None:
            kwargs["cloud_exadata_infrastructure_id"] = cloud_exadata_infrastructure_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_cloud_vm_clusters(**kwargs)
        return [map_cloudvmclustersummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_cloud_vm_clusters tool: {e}")
        raise


@mcp.tool(
    description=("Lists the console connections for the specified database node.")
)
def list_console_connections(
    db_node_id: Annotated[Optional[Any], ("The database node `OCID`.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ConsoleConnectionSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_node_id"] = db_node_id
        response: oci.response.Response = client.list_console_connections(**kwargs)
        return [map_consoleconnectionsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_console_connections tool: {e}")
        raise


@mcp.tool(description=("Lists the console histories for the specified database node."))
def list_console_histories(
    db_node_id: Annotated[Optional[Any], ("The database node `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "REQUESTED",'
            '"GETTING_HISTORY", "SUCCEEDED", "FAILED", "DELETED",'
            '"DELETING"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ConsoleHistoryCollection]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_node_id"] = db_node_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = client.list_console_histories(**kwargs)
        return [map_consolehistorycollection(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_console_histories tool: {e}")
        raise


@mcp.tool(
    description=("Lists the patches applicable to the requested container database.")
)
def list_container_database_patches(
    autonomous_container_database_id: Annotated[
        Optional[Any], ("The Autonomous Container Database `OCID`.")
    ],
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    autonomous_patch_type: Annotated[
        Optional[Any],
        (
            'Autonomous patch type, either "QUARTERLY" or "TIMEZONE".'
            'Allowed values are: "QUARTERLY", "TIMEZONE"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[AutonomousPatchSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_container_database_id"] = autonomous_container_database_id
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if autonomous_patch_type is not None:
            kwargs["autonomous_patch_type"] = autonomous_patch_type
        response: oci.response.Response = client.list_container_database_patches(
            **kwargs
        )
        return [map_autonomouspatchsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_container_database_patches tool: {e}")
        raise


@mcp.tool(description=("Lists all Data Guard associations for the specified database."))
def list_data_guard_associations(
    database_id: Annotated[Optional[Any], ("The database `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[DataGuardAssociationSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["database_id"] = database_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_data_guard_associations(**kwargs)
        return [map_dataguardassociationsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_data_guard_associations tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the database software images in the specified compartment."
    )
)
def list_database_software_images(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Default order for PATCHSET is"
            'descending. Allowed values are: "TIMECREATED",'
            '"DISPLAYNAME", "PATCHSET"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "DELETING", "DELETED",'
            '"FAILED", "TERMINATING", "TERMINATED", "UPDATING"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    image_type: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given image"
            'type exactly. Allowed values are: "GRID_IMAGE",'
            '"DATABASE_IMAGE"'
        ),
    ] = None,
    image_shape_family: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given image"
            'shape family exactly. Allowed values are: "VM_BM_SHAPE",'
            '"EXADATA_SHAPE", "EXACC_SHAPE", "EXADBXS_SHAPE"'
        ),
    ] = None,
    patch_set_greater_than_or_equal_to: Annotated[
        Optional[Any],
        (
            "A filter to return only resources with `patchSet` greater"
            "than or equal to given value."
        ),
    ] = None,
    is_upgrade_supported: Annotated[
        Optional[Any],
        (
            "If provided, filters the results to the set of database"
            "versions which are supported for Upgrade."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[DatabaseSoftwareImageSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        if image_type is not None:
            kwargs["image_type"] = image_type
        if image_shape_family is not None:
            kwargs["image_shape_family"] = image_shape_family
        if patch_set_greater_than_or_equal_to is not None:
            kwargs["patch_set_greater_than_or_equal_to"] = (
                patch_set_greater_than_or_equal_to
            )
        if is_upgrade_supported is not None:
            kwargs["is_upgrade_supported"] = is_upgrade_supported
        response: oci.response.Response = client.list_database_software_images(**kwargs)
        return [map_databasesoftwareimagesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_database_software_images tool: {e}")
        raise


@mcp.tool(description=("Gets a list of the databases in the specified Database Home."))
def list_databases(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    db_home_id: Annotated[Optional[Any], ("A Database Home `OCID`.")] = None,
    system_id: Annotated[
        Optional[Any],
        (
            "The `OCID` of the Exadata DB system that you want to"
            "filter the database results by. Applies only to Exadata DB"
            "systems."
        ),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DBNAME is ascending. The DBNAME sort order"
            'is case sensitive. Allowed values are: "DBNAME",'
            '"TIMECREATED"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "UPDATING",'
            '"BACKUP_IN_PROGRESS", "UPGRADING", "CONVERTING",'
            '"TERMINATING", "TERMINATED", "RESTORE_FAILED",'
            '"FAILED"'
        ),
    ] = None,
    db_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "database name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[DatabaseSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if db_home_id is not None:
            kwargs["db_home_id"] = db_home_id
        if system_id is not None:
            kwargs["system_id"] = system_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if db_name is not None:
            kwargs["db_name"] = db_name
        response: oci.response.Response = client.list_databases(**kwargs)
        return [map_databasesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_databases tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the history of patch operations on the specified Database Home."
    )
)
def list_db_home_patch_history_entries(
    db_home_id: Annotated[Optional[Any], ("The Database Home `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[PatchHistoryEntrySummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_home_id"] = db_home_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_db_home_patch_history_entries(
            **kwargs
        )
        return [map_patchhistoryentrysummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_db_home_patch_history_entries tool: {e}")
        raise


@mcp.tool(description=("Lists patches applicable to the requested Database Home."))
def list_db_home_patches(
    db_home_id: Annotated[Optional[Any], ("The Database Home `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[PatchSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_home_id"] = db_home_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_db_home_patches(**kwargs)
        return [map_patchsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_db_home_patches tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the Database Homes in the specified DB system and compartment. A Database"
        "Home is a directory where Oracle Database software is installed."
    )
)
def list_db_homes(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    db_system_id: Annotated[
        Optional[Any],
        (
            "The DB system `OCID`. If provided, filters the results to"
            "the set of database versions which are supported for the DB"
            "system."
        ),
    ] = None,
    vm_cluster_id: Annotated[Optional[Any], ("The `OCID` of the VM cluster.")] = None,
    backup_id: Annotated[
        Optional[Any],
        (
            "The `OCID` of the backup. Specify a backupId to list only"
            "the DB systems or DB homes that support creating a database"
            "using this backup in this compartment."
        ),
    ] = None,
    db_version: Annotated[
        Optional[Any],
        ("A filter to return only DB Homes that match the specified" "dbVersion."),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[DbHomeSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if db_system_id is not None:
            kwargs["db_system_id"] = db_system_id
        if vm_cluster_id is not None:
            kwargs["vm_cluster_id"] = vm_cluster_id
        if backup_id is not None:
            kwargs["backup_id"] = backup_id
        if db_version is not None:
            kwargs["db_version"] = db_version
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = client.list_db_homes(**kwargs)
        return [map_dbhomesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_db_homes tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the database nodes in the specified DB system and compartment. A database"
        "node is a server running database software."
    )
)
def list_db_nodes(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    db_system_id: Annotated[
        Optional[Any],
        (
            "The DB system `OCID`. If provided, filters the results to"
            "the set of database versions which are supported for the DB"
            "system."
        ),
    ] = None,
    vm_cluster_id: Annotated[Optional[Any], ("The `OCID` of the VM cluster.")] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "Sort by TIMECREATED. Default order for TIMECREATED is"
            'descending. Allowed values are: "TIMECREATED"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "UPDATING", "STOPPING",'
            '"STOPPED", "STARTING", "TERMINATING", "TERMINATED",'
            '"FAILED"'
        ),
    ] = None,
    db_server_id: Annotated[
        Optional[Any], ("The `OCID` of the Exacc Db server.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[DbNodeSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if db_system_id is not None:
            kwargs["db_system_id"] = db_system_id
        if vm_cluster_id is not None:
            kwargs["vm_cluster_id"] = vm_cluster_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if db_server_id is not None:
            kwargs["db_server_id"] = db_server_id
        response: oci.response.Response = client.list_db_nodes(**kwargs)
        return [map_dbnodesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_db_nodes tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the Exadata DB servers in the ExadataInfrastructureId and specified"
        "compartment."
    )
)
def list_db_servers(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    exadata_infrastructure_id: Annotated[
        Optional[Any], ("The `OCID` of the ExadataInfrastructure.")
    ],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "Sort by TIMECREATED. Default order for TIMECREATED is"
            'descending. Allowed values are: "TIMECREATED"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "CREATING",'
            '"AVAILABLE", "UNAVAILABLE", "DELETING", "DELETED",'
            '"MAINTENANCE_IN_PROGRESS"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[DbServerSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        kwargs["exadata_infrastructure_id"] = exadata_infrastructure_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = client.list_db_servers(**kwargs)
        return [map_dbserversummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_db_servers tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of expected compute performance parameters for a virtual machine DB"
        "system based on system configuration."
    )
)
def list_db_system_compute_performances(
    db_system_shape: Annotated[
        Optional[Any],
        (
            "If provided, filters the results to the set of database"
            "versions which are supported for the given shape."
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[DbSystemComputePerformanceSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        if db_system_shape is not None:
            kwargs["db_system_shape"] = db_system_shape
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_db_system_compute_performances(
            **kwargs
        )
        return [map_dbsystemcomputeperformancesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_db_system_compute_performances tool: {e}")
        raise


@mcp.tool(description=("Lists the patches applicable to the specified DB system."))
def list_db_system_patches(
    db_system_id: Annotated[Optional[Any], ("The DB system `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[PatchSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_system_id"] = db_system_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_db_system_patches(**kwargs)
        return [map_patchsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_db_system_patches tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the shapes that can be used to launch a new DB system. The shape"
        "determines resources to allocate to the DB system - CPU cores and memory for VM"
        "shapes; CPU cores, memory and storage for non-VM (or bare metal) shapes."
    )
)
def list_db_system_shapes(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    availability_domain: Annotated[
        Optional[Any], ("The name of the Availability Domain.")
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[DbSystemShapeSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if availability_domain is not None:
            kwargs["availability_domain"] = availability_domain
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_db_system_shapes(**kwargs)
        return [map_dbsystemshapesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_db_system_shapes tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of possible expected storage performance parameters of a VMDB System"
        "based on Configuration."
    )
)
def list_db_system_storage_performances(
    storage_management: Annotated[
        Optional[Any],
        (
            "The DB system storage management option. Used to list"
            "database versions available for that storage manager. Valid"
            "values are `ASM` and `LVM`. * ASM specifies Oracle Automatic"
            "Storage Management * LVM specifies logical volume manager,"
            "sometimes called logical disk manager. Allowed values are:"
            '"ASM", "LVM"'
        ),
    ],
    shape_type: Annotated[
        Optional[Any], ("Optional. Filters the performance results by shape type.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[DbSystemStoragePerformanceSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["storage_management"] = storage_management
        if shape_type is not None:
            kwargs["shape_type"] = shape_type
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_db_system_storage_performances(
            **kwargs
        )
        return [map_dbsystemstorageperformancesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_db_system_storage_performances tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the DB systems in the specified compartment. You can specify a `backupId`"
        "to list only the DB systems that support creating a database using this backup"
        "in this compartment."
    )
)
def list_db_systems(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    backup_id: Annotated[
        Optional[Any],
        (
            "The `OCID` of the backup. Specify a backupId to list only"
            "the DB systems or DB homes that support creating a database"
            "using this backup in this compartment."
        ),
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. **Note:** If you do not"
            "include the availability domain filter, the resources are"
            "grouped by availability domain, then sorted. Allowed values"
            'are: "TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED", "MIGRATED",'
            '"MAINTENANCE_IN_PROGRESS", "NEEDS_ATTENTION",'
            '"UPGRADING"'
        ),
    ] = None,
    availability_domain: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "availability domain exactly."
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[DbSystemSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if backup_id is not None:
            kwargs["backup_id"] = backup_id
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if availability_domain is not None:
            kwargs["availability_domain"] = availability_domain
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = client.list_db_systems(**kwargs)
        return [map_dbsystemsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_db_systems tool: {e}")
        raise


@mcp.tool(description=("Gets a list of supported Oracle Database versions."))
def list_db_versions(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    db_system_shape: Annotated[
        Optional[Any],
        (
            "If provided, filters the results to the set of database"
            "versions which are supported for the given shape."
        ),
    ] = None,
    db_system_id: Annotated[
        Optional[Any],
        (
            "The DB system `OCID`. If provided, filters the results to"
            "the set of database versions which are supported for the DB"
            "system."
        ),
    ] = None,
    storage_management: Annotated[
        Optional[Any],
        (
            "The DB system storage management option. Used to list"
            "database versions available for that storage manager. Valid"
            "values are `ASM` and `LVM`. * ASM specifies Oracle Automatic"
            "Storage Management * LVM specifies logical volume manager,"
            "sometimes called logical disk manager. Allowed values are:"
            '"ASM", "LVM"'
        ),
    ] = None,
    is_upgrade_supported: Annotated[
        Optional[Any],
        (
            "If provided, filters the results to the set of database"
            "versions which are supported for Upgrade."
        ),
    ] = None,
    is_database_software_image_supported: Annotated[
        Optional[Any],
        (
            "If true, filters the results to the set of Oracle Database"
            "versions that are supported for OCI database software"
            "images."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[DbVersionSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if db_system_shape is not None:
            kwargs["db_system_shape"] = db_system_shape
        if db_system_id is not None:
            kwargs["db_system_id"] = db_system_id
        if storage_management is not None:
            kwargs["storage_management"] = storage_management
        if is_upgrade_supported is not None:
            kwargs["is_upgrade_supported"] = is_upgrade_supported
        if is_database_software_image_supported is not None:
            kwargs["is_database_software_image_supported"] = (
                is_database_software_image_supported
            )
        response: oci.response.Response = client.list_db_versions(**kwargs)
        return [map_dbversionsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_db_versions tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the Exadata infrastructure resources in the specified compartment. Applies"
        "to Exadata Cloud@Customer instances only."
    )
)
def list_exadata_infrastructures(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "CREATING",'
            '"REQUIRES_ACTIVATION", "ACTIVATING", "ACTIVE",'
            '"ACTIVATION_FAILED", "FAILED", "UPDATING",'
            '"DELETING", "DELETED", "DISCONNECTED",'
            '"MAINTENANCE_IN_PROGRESS", "WAITING_FOR_CONNECTIVITY"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    excluded_fields: Annotated[
        Optional[Any],
        (
            "If provided, the specified fields will be excluded in the"
            'response. Allowed values are: "multiRackConfigurationFile"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ExadataInfrastructureSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        if excluded_fields is not None:
            kwargs["excluded_fields"] = excluded_fields
        response: oci.response.Response = client.list_exadata_infrastructures(**kwargs)
        return [map_exadatainfrastructuresummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_exadata_infrastructures tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the maintenance updates that can be applied to the specified Exadata VM"
        "cluster on Exascale Infrastructure."
    )
)
def list_exadb_vm_cluster_updates(
    exadb_vm_cluster_id: Annotated[
        Optional[Any], ("The Exadata VM cluster `OCID` on Exascale Infrastructure.")
    ],
    update_type: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'update type exactly. Allowed values are: "GI_UPGRADE",'
            '"GI_PATCH", "OS_UPDATE"'
        ),
    ] = None,
    version: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "update version exactly."
        ),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ExadbVmClusterUpdateSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["exadb_vm_cluster_id"] = exadb_vm_cluster_id
        if update_type is not None:
            kwargs["update_type"] = update_type
        if version is not None:
            kwargs["version"] = version
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_exadb_vm_cluster_updates(**kwargs)
        return [map_exadbvmclusterupdatesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_exadb_vm_cluster_updates tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the Exadata VM clusters on Exascale Infrastructure in the"
        "specified compartment. Applies to Exadata Database Service on Exascale"
        "Infrastructure only."
    )
)
def list_exadb_vm_clusters(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only Exadata VM clusters on Exascale"
            "Infrastructure that match the given lifecycle state exactly."
            'Allowed values are: "PROVISIONING", "AVAILABLE",'
            '"UPDATING", "TERMINATING", "TERMINATED", "FAILED",'
            '"MAINTENANCE_IN_PROGRESS"'
        ),
    ] = None,
    exascale_db_storage_vault_id: Annotated[
        Optional[Any],
        (
            "A filter to return only Exadata VM clusters on Exascale"
            "Infrastructure that match the given Exascale Database"
            "Storage Vault ID."
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ExadbVmClusterSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if exascale_db_storage_vault_id is not None:
            kwargs["exascale_db_storage_vault_id"] = exascale_db_storage_vault_id
        if display_name is not None:
            kwargs["display_name"] = display_name
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_exadb_vm_clusters(**kwargs)
        return [map_exadbvmclustersummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_exadb_vm_clusters tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the Exadata Database Storage Vaults in the specified compartment."
    )
)
def list_exascale_db_storage_vaults(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only Exadata Database Storage Vaults that"
            "match the given lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    exadata_infrastructure_id: Annotated[
        Optional[Any],
        (
            "A filter to return only list of Vaults that are linked to"
            "the exadata infrastructure Id."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ExascaleDbStorageVaultSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if exadata_infrastructure_id is not None:
            kwargs["exadata_infrastructure_id"] = exadata_infrastructure_id
        response: oci.response.Response = client.list_exascale_db_storage_vaults(
            **kwargs
        )
        return [map_exascaledbstoragevaultsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_exascale_db_storage_vaults tool: {e}")
        raise


@mcp.tool(
    description=("Lists the execution action resources in the specified compartment.")
)
def list_execution_actions(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "SCHEDULED",'
            '"IN_PROGRESS", "FAILED", "CANCELED", "UPDATING",'
            '"DELETED", "SUCCEEDED", "PARTIAL_SUCCESS"'
        ),
    ] = None,
    execution_window_id: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "execution wondow id."
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ExecutionActionSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if execution_window_id is not None:
            kwargs["execution_window_id"] = execution_window_id
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = client.list_execution_actions(**kwargs)
        return [map_executionactionsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_execution_actions tool: {e}")
        raise


@mcp.tool(
    description=("Lists the execution window resources in the specified compartment.")
)
def list_execution_windows(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    execution_resource_id: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "resource id exactly."
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "CREATED",'
            '"SCHEDULED", "IN_PROGRESS", "FAILED", "CANCELED",'
            '"UPDATING", "DELETED", "SUCCEEDED",'
            '"PARTIAL_SUCCESS", "CREATING", "DELETING"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ExecutionWindowSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if execution_resource_id is not None:
            kwargs["execution_resource_id"] = execution_resource_id
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = client.list_execution_windows(**kwargs)
        return [map_executionwindowsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_execution_windows tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the external container databases in the specified compartment."
    )
)
def list_external_container_databases(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"DISPLAYNAME", "TIMECREATED"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the specified"
            'lifecycle state. Allowed values are: "PROVISIONING",'
            '"NOT_CONNECTED", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ExternalContainerDatabaseSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = client.list_external_container_databases(
            **kwargs
        )
        return [map_externalcontainerdatabasesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_external_container_databases tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the external database connectors in the specified compartment."
    )
)
def list_external_database_connectors(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    external_database_id: Annotated[
        Optional[Any],
        ("The `OCID` of the external database whose connectors will" "be listed."),
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"DISPLAYNAME", "TIMECREATED"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the specified"
            'lifecycle state. Allowed values are: "PROVISIONING",'
            '"AVAILABLE", "UPDATING", "TERMINATING",'
            '"TERMINATED", "FAILED"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ExternalDatabaseConnectorSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        kwargs["external_database_id"] = external_database_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = client.list_external_database_connectors(
            **kwargs
        )
        return [map_externaldatabaseconnectorsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_external_database_connectors tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the ExternalNonContainerDatabases in the specified compartment."
    )
)
def list_external_non_container_databases(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"DISPLAYNAME", "TIMECREATED"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the specified"
            'lifecycle state. Allowed values are: "PROVISIONING",'
            '"NOT_CONNECTED", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ExternalNonContainerDatabaseSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = client.list_external_non_container_databases(
            **kwargs
        )
        return [map_externalnoncontainerdatabasesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_external_non_container_databases tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the :func:`create_external_pluggable_database_details`"
    )
)
def list_external_pluggable_databases(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    external_container_database_id: Annotated[
        Optional[Any], ("The ExternalContainerDatabase `OCID`.")
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"DISPLAYNAME", "TIMECREATED"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the specified"
            'lifecycle state. Allowed values are: "PROVISIONING",'
            '"NOT_CONNECTED", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ExternalPluggableDatabaseSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if external_container_database_id is not None:
            kwargs["external_container_database_id"] = external_container_database_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = client.list_external_pluggable_databases(
            **kwargs
        )
        return [map_externalpluggabledatabasesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_external_pluggable_databases tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the flex components that can be used to launch a new DB system."
        "The flex component determines resources to allocate to the DB system - Database"
        "Servers and Storage Servers."
    )
)
def list_flex_components(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire name"
            "given. The match is not case sensitive."
        ),
    ] = None,
    shape: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that belong to the entire"
            "shape name given. The match is not case sensitive."
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for NAME is ascending. The NAME"
            'sort order is case sensitive. Allowed values are: "NAME"'
        ),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[FlexComponentCollection]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if name is not None:
            kwargs["name"] = name
        if shape is not None:
            kwargs["shape"] = shape
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_flex_components(**kwargs)
        return [map_flexcomponentcollection(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_flex_components tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of supported Oracle Grid Infrastructure minor versions for the given"
        "major version and shape family."
    )
)
def list_gi_version_minor_versions(
    version: Annotated[
        Optional[Any], ("The Oracle Grid Infrastructure major version.")
    ],
    availability_domain: Annotated[
        Optional[Any],
        ("The target availability domain. Only passed if the limit is" "AD-specific."),
    ] = None,
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    shape_family: Annotated[
        Optional[Any],
        (
            "If provided, filters the results to the set of database"
            "versions which are supported for the given shape family."
            'Allowed values are: "SINGLENODE", "YODA",'
            '"VIRTUALMACHINE", "EXADATA", "EXACC", "EXADB_XS"'
        ),
    ] = None,
    is_gi_version_for_provisioning: Annotated[
        Optional[Any],
        (
            "If true, returns the Grid Infrastructure versions that can"
            "be used for provisioning a cluster"
        ),
    ] = None,
    shape: Annotated[
        Optional[Any], ("If provided, filters the results for the given shape.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "Sort by VERSION. Default order for VERSION is descending."
            'Allowed values are: "VERSION"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[GiMinorVersionSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["version"] = version
        if availability_domain is not None:
            kwargs["availability_domain"] = availability_domain
        if compartment_id is not None:
            kwargs["compartment_id"] = compartment_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if shape_family is not None:
            kwargs["shape_family"] = shape_family
        if is_gi_version_for_provisioning is not None:
            kwargs["is_gi_version_for_provisioning"] = is_gi_version_for_provisioning
        if shape is not None:
            kwargs["shape"] = shape
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_gi_version_minor_versions(
            **kwargs
        )
        return [map_giminorversionsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_gi_version_minor_versions tool: {e}")
        raise


@mcp.tool(description=("Gets a list of supported GI versions."))
def list_gi_versions(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    shape: Annotated[
        Optional[Any], ("If provided, filters the results for the given shape.")
    ] = None,
    availability_domain: Annotated[
        Optional[Any],
        ("The target availability domain. Only passed if the limit is" "AD-specific."),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[GiVersionSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if shape is not None:
            kwargs["shape"] = shape
        if availability_domain is not None:
            kwargs["availability_domain"] = availability_domain
        response: oci.response.Response = client.list_gi_versions(**kwargs)
        return [map_giversionsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_gi_versions tool: {e}")
        raise


@mcp.tool(description=("Gets a list of key stores in the specified compartment."))
def list_key_stores(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[KeyStoreSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_key_stores(**kwargs)
        return [map_keystoresummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_key_stores tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the maintenance run histories in the specified compartment."
    )
)
def list_maintenance_run_history(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    target_resource_id: Annotated[Optional[Any], ("The target resource ID.")] = None,
    target_resource_type: Annotated[
        Optional[Any],
        (
            "The type of the target resource. Allowed values are:"
            '"AUTONOMOUS_EXADATA_INFRASTRUCTURE",'
            '"AUTONOMOUS_CONTAINER_DATABASE", "EXADATA_DB_SYSTEM",'
            '"CLOUD_EXADATA_INFRASTRUCTURE", "EXACC_INFRASTRUCTURE",'
            '"AUTONOMOUS_VM_CLUSTER", "AUTONOMOUS_DATABASE",'
            '"CLOUD_AUTONOMOUS_VM_CLUSTER"'
        ),
    ] = None,
    maintenance_type: Annotated[
        Optional[Any],
        ('The maintenance type. Allowed values are: "PLANNED",' '"UNPLANNED"'),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIME_SCHEDULED and"
            "TIME_ENDED is descending. Default order for DISPLAYNAME is"
            "ascending. The DISPLAYNAME sort order is case sensitive."
            "**Note:** If you do not include the availability domain"
            "filter, the resources are grouped by availability domain,"
            'then sorted. Allowed values are: "TIME_SCHEDULED",'
            '"TIME_ENDED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "The state of the maintenance run history. Allowed values"
            'are: "SCHEDULED", "IN_PROGRESS", "SUCCEEDED",'
            '"SKIPPED", "FAILED", "UPDATING", "DELETING",'
            '"DELETED", "CANCELED"'
        ),
    ] = None,
    availability_domain: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "availability domain exactly."
        ),
    ] = None,
    maintenance_subtype: Annotated[
        Optional[Any],
        (
            "The sub-type of the maintenance run. Allowed values are:"
            '"QUARTERLY", "HARDWARE", "CRITICAL",'
            '"INFRASTRUCTURE", "DATABASE", "ONEOFF",'
            '"SECURITY_MONTHLY", "TIMEZONE",'
            '"CUSTOM_DATABASE_SOFTWARE_IMAGE"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[MaintenanceRunHistorySummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if target_resource_id is not None:
            kwargs["target_resource_id"] = target_resource_id
        if target_resource_type is not None:
            kwargs["target_resource_type"] = target_resource_type
        if maintenance_type is not None:
            kwargs["maintenance_type"] = maintenance_type
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if availability_domain is not None:
            kwargs["availability_domain"] = availability_domain
        if maintenance_subtype is not None:
            kwargs["maintenance_subtype"] = maintenance_subtype
        response: oci.response.Response = client.list_maintenance_run_history(**kwargs)
        return [map_maintenancerunhistorysummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_maintenance_run_history tool: {e}")
        raise


@mcp.tool(
    description=("Gets a list of the maintenance runs in the specified compartment.")
)
def list_maintenance_runs(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    target_resource_id: Annotated[Optional[Any], ("The target resource ID.")] = None,
    target_resource_type: Annotated[
        Optional[Any],
        (
            "The type of the target resource. Allowed values are:"
            '"AUTONOMOUS_EXADATA_INFRASTRUCTURE",'
            '"AUTONOMOUS_CONTAINER_DATABASE", "EXADATA_DB_SYSTEM",'
            '"CLOUD_EXADATA_INFRASTRUCTURE", "EXACC_INFRASTRUCTURE",'
            '"AUTONOMOUS_VM_CLUSTER", "AUTONOMOUS_DATABASE",'
            '"CLOUD_AUTONOMOUS_VM_CLUSTER"'
        ),
    ] = None,
    maintenance_type: Annotated[
        Optional[Any],
        ('The maintenance type. Allowed values are: "PLANNED",' '"UNPLANNED"'),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIME_SCHEDULED and"
            "TIME_ENDED is descending. Default order for DISPLAYNAME is"
            "ascending. The DISPLAYNAME sort order is case sensitive."
            "**Note:** If you do not include the availability domain"
            "filter, the resources are grouped by availability domain,"
            'then sorted. Allowed values are: "TIME_SCHEDULED",'
            '"TIME_ENDED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "SCHEDULED",'
            '"IN_PROGRESS", "SUCCEEDED", "SKIPPED", "FAILED",'
            '"UPDATING", "DELETING", "DELETED", "CANCELED"'
        ),
    ] = None,
    availability_domain: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "availability domain exactly."
        ),
    ] = None,
    maintenance_subtype: Annotated[
        Optional[Any],
        (
            "The sub-type of the maintenance run. Allowed values are:"
            '"QUARTERLY", "HARDWARE", "CRITICAL",'
            '"INFRASTRUCTURE", "DATABASE", "ONEOFF",'
            '"SECURITY_MONTHLY", "TIMEZONE",'
            '"CUSTOM_DATABASE_SOFTWARE_IMAGE"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[MaintenanceRunSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if target_resource_id is not None:
            kwargs["target_resource_id"] = target_resource_id
        if target_resource_type is not None:
            kwargs["target_resource_type"] = target_resource_type
        if maintenance_type is not None:
            kwargs["maintenance_type"] = maintenance_type
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if availability_domain is not None:
            kwargs["availability_domain"] = availability_domain
        if maintenance_subtype is not None:
            kwargs["maintenance_subtype"] = maintenance_subtype
        response: oci.response.Response = client.list_maintenance_runs(**kwargs)
        return [map_maintenancerunsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_maintenance_runs tool: {e}")
        raise


@mcp.tool(description=("Lists one-off patches in the specified compartment."))
def list_oneoff_patches(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly Allowed values are: "CREATING",'
            '"AVAILABLE", "UPDATING", "INACTIVE", "FAILED",'
            '"EXPIRED", "DELETING", "DELETED", "TERMINATING",'
            '"TERMINATED"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[OneoffPatchSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_oneoff_patches(**kwargs)
        return [map_oneoffpatchsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_oneoff_patches tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the pluggable databases in a database or compartment. You must"
        "provide either a `databaseId` or `compartmentId` value."
    )
)
def list_pluggable_databases(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")] = None,
    database_id: Annotated[Optional[Any], ("The `OCID` of the database.")] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for PDBNAME is ascending. The PDBNAME sort"
            'order is case sensitive. Allowed values are: "PDBNAME",'
            '"TIMECREATED"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "TERMINATING",'
            '"TERMINATED", "UPDATING", "FAILED", "RELOCATING",'
            '"RELOCATED", "REFRESHING", "RESTORE_IN_PROGRESS",'
            '"RESTORE_FAILED", "BACKUP_IN_PROGRESS", "DISABLED"'
        ),
    ] = None,
    pdb_name: Annotated[
        Optional[Any],
        (
            "A filter to return only pluggable databases that match the"
            "entire name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[PluggableDatabaseSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        if compartment_id is not None:
            kwargs["compartment_id"] = compartment_id
        if database_id is not None:
            kwargs["database_id"] = database_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if pdb_name is not None:
            kwargs["pdb_name"] = pdb_name
        response: oci.response.Response = client.list_pluggable_databases(**kwargs)
        return [map_pluggabledatabasesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_pluggable_databases tool: {e}")
        raise


@mcp.tool(
    description=("Lists the Scheduled Action resources in the specified compartment.")
)
def list_scheduled_actions(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    service_type: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "service type exactly."
        ),
    ] = None,
    scheduling_plan_id: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "scheduling policy id exactly."
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            'Allowed values are: "TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    id: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "Scheduled Action id exactly."
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "CREATING",'
            '"NEEDS_ATTENTION", "AVAILABLE", "UPDATING",'
            '"FAILED", "DELETING", "DELETED"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ScheduledActionCollection]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if service_type is not None:
            kwargs["service_type"] = service_type
        if scheduling_plan_id is not None:
            kwargs["scheduling_plan_id"] = scheduling_plan_id
        if display_name is not None:
            kwargs["display_name"] = display_name
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if id is not None:
            kwargs["id"] = id
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        response: oci.response.Response = client.list_scheduled_actions(**kwargs)
        return [map_scheduledactioncollection(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_scheduled_actions tool: {e}")
        raise


@mcp.tool(
    description=("Lists the Scheduling Plan resources in the specified compartment.")
)
def list_scheduling_plans(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            'Allowed values are: "TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "CREATING",'
            '"NEEDS_ATTENTION", "AVAILABLE", "UPDATING",'
            '"FAILED", "DELETING", "DELETED"'
        ),
    ] = None,
    scheduling_policy_id: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "scheduling policy id exactly."
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    resource_id: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "resource id exactly."
        ),
    ] = None,
    id: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "Schedule Plan id exactly."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[SchedulingPlanCollection]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if scheduling_policy_id is not None:
            kwargs["scheduling_policy_id"] = scheduling_policy_id
        if display_name is not None:
            kwargs["display_name"] = display_name
        if resource_id is not None:
            kwargs["resource_id"] = resource_id
        if id is not None:
            kwargs["id"] = id
        response: oci.response.Response = client.list_scheduling_plans(**kwargs)
        return [map_schedulingplancollection(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_scheduling_plans tool: {e}")
        raise


@mcp.tool(
    description=("Lists the Scheduling Policy resources in the specified compartment.")
)
def list_scheduling_policies(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "CREATING",'
            '"NEEDS_ATTENTION", "AVAILABLE", "UPDATING",'
            '"FAILED", "DELETING", "DELETED"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[SchedulingPolicySummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = client.list_scheduling_policies(**kwargs)
        return [map_schedulingpolicysummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_scheduling_policies tool: {e}")
        raise


@mcp.tool(
    description=("Lists the Scheduling Window resources in the specified compartment.")
)
def list_scheduling_windows(
    scheduling_policy_id: Annotated[Optional[Any], ("The Scheduling Policy `OCID`.")],
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "CREATING",'
            '"AVAILABLE", "UPDATING", "FAILED", "DELETING",'
            '"DELETED"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[SchedulingWindowSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["scheduling_policy_id"] = scheduling_policy_id
        if compartment_id is not None:
            kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        response: oci.response.Response = client.list_scheduling_windows(**kwargs)
        return [map_schedulingwindowsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_scheduling_windows tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of supported Exadata system versions for a given shape and GI"
        "version."
    )
)
def list_system_versions(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    shape: Annotated[Optional[Any], ("Specifies shape query parameter.")],
    gi_version: Annotated[Optional[Any], ("Specifies gi version query parameter.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[SystemVersionCollection]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        kwargs["shape"] = shape
        kwargs["gi_version"] = gi_version
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_system_versions(**kwargs)
        return [map_systemversioncollection(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_system_versions tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets a list of the VM cluster networks in the specified compartment. Applies to"
        "Exadata Cloud@Customer instances only."
    )
)
def list_vm_cluster_networks(
    exadata_infrastructure_id: Annotated[
        Optional[Any], ("The Exadata infrastructure `OCID`.")
    ],
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "CREATING",'
            '"REQUIRES_VALIDATION", "VALIDATING", "VALIDATED",'
            '"VALIDATION_FAILED", "UPDATING", "ALLOCATED",'
            '"TERMINATING", "TERMINATED", "FAILED",'
            '"NEEDS_ATTENTION"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[VmClusterNetworkSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["exadata_infrastructure_id"] = exadata_infrastructure_id
        kwargs["compartment_id"] = compartment_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_vm_cluster_networks(**kwargs)
        return [map_vmclusternetworksummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_vm_cluster_networks tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the patches applicable to the specified VM cluster in an Exadata"
        "Cloud@Customer system."
    )
)
def list_vm_cluster_patches(
    vm_cluster_id: Annotated[Optional[Any], ("The VM cluster `OCID`.")],
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[PatchSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["vm_cluster_id"] = vm_cluster_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_vm_cluster_patches(**kwargs)
        return [map_patchsummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_vm_cluster_patches tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the maintenance updates that can be applied to the specified VM cluster."
        "Applies to Exadata Cloud@Customer instances only."
    )
)
def list_vm_cluster_updates(
    vm_cluster_id: Annotated[Optional[Any], ("The VM cluster `OCID`.")],
    update_type: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'update type exactly. Allowed values are: "GI_UPGRADE",'
            '"GI_PATCH", "OS_UPDATE"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            'lifecycle state exactly. Allowed values are: "AVAILABLE",'
            '"SUCCESS", "IN_PROGRESS", "FAILED"'
        ),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[VmClusterUpdateSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["vm_cluster_id"] = vm_cluster_id
        if update_type is not None:
            kwargs["update_type"] = update_type
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_vm_cluster_updates(**kwargs)
        return [map_vmclusterupdatesummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_vm_cluster_updates tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists the VM clusters in the specified compartment. Applies to Exadata"
        "Cloud@Customer instances only."
    )
)
def list_vm_clusters(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    exadata_infrastructure_id: Annotated[
        Optional[Any],
        ("If provided, filters the results for the given Exadata" "Infrastructure."),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    sort_by: Annotated[
        Optional[Any],
        (
            "The field to sort by. You can provide one sort order"
            "(`sortOrder`). Default order for TIMECREATED is descending."
            "Default order for DISPLAYNAME is ascending. The DISPLAYNAME"
            "sort order is case sensitive. Allowed values are:"
            '"TIMECREATED", "DISPLAYNAME"'
        ),
    ] = None,
    sort_order: Annotated[
        Optional[Any],
        (
            "The sort order to use, either ascending (`ASC`) or"
            'descending (`DESC`). Allowed values are: "ASC", "DESC"'
        ),
    ] = None,
    lifecycle_state: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the given"
            "lifecycle state exactly. Allowed values are:"
            '"PROVISIONING", "AVAILABLE", "UPDATING",'
            '"TERMINATING", "TERMINATED", "FAILED",'
            '"MAINTENANCE_IN_PROGRESS"'
        ),
    ] = None,
    display_name: Annotated[
        Optional[Any],
        (
            "A filter to return only resources that match the entire"
            "display name given. The match is not case sensitive."
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[VmClusterSummary]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if exadata_infrastructure_id is not None:
            kwargs["exadata_infrastructure_id"] = exadata_infrastructure_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if sort_order is not None:
            kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name is not None:
            kwargs["display_name"] = display_name
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.list_vm_clusters(**kwargs)
        return [map_vmclustersummary(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in list_vm_clusters tool: {e}")
        raise


@mcp.tool(description=("Lists available resource pools shapes."))
def resource_pool_shapes(
    if_match: Annotated[
        Optional[Any],
        (
            "For optimistic concurrency control. In the PUT or DELETE"
            "call for a resource, set the `if-match` parameter to the"
            "value of the etag from a previous GET or POST response for"
            "that resource. The resource will be updated or deleted only"
            "if the etag you provide matches the resource's current etag"
            "value."
        ),
    ] = None,
    opc_retry_token: Annotated[
        Optional[Any],
        (
            "A token that uniquely identifies a request so it can be"
            "retried in case of a timeout or server error without risk of"
            "executing that same action again. Retry tokens expire after"
            "24 hours, but can be invalidated before then due to"
            "conflicting operations (for example, if a resource has been"
            "deleted and purged from the system, then a retry of the"
            "original creation request may be rejected)."
        ),
    ] = None,
    limit: Annotated[
        Optional[Any], ("The maximum number of items to return per page.")
    ] = None,
    page: Annotated[
        Optional[Any], ("The pagination token to continue listing from.")
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[ResourcePoolShapeCollection]:
    try:
        client = get_database_client(region)
        kwargs = {}
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.resource_pool_shapes(**kwargs)
        return [map_resourcepoolshapecollection(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in resource_pool_shapes tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about a specified application virtual IP (VIP) address."
    )
)
def get_application_vip(
    application_vip_id: Annotated[
        Optional[Any], ("The `OCID` of the application virtual IP (VIP) address.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ApplicationVip:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["application_vip_id"] = application_vip_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_application_vip(**kwargs)
        return map_applicationvip(response.data)
    except Exception as e:
        logger.error(f"Error in get_application_vip tool: {e}")
        raise


@mcp.tool(
    description=("Gets information about the specified Autonomous Container Database.")
)
def get_autonomous_container_database(
    autonomous_container_database_id: Annotated[
        Optional[Any], ("The Autonomous Container Database `OCID`.")
    ],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousContainerDatabase:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_container_database_id"] = autonomous_container_database_id
        response: oci.response.Response = client.get_autonomous_container_database(
            **kwargs
        )
        return map_autonomouscontainerdatabase(response.data)
    except Exception as e:
        logger.error(f"Error in get_autonomous_container_database tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets an Autonomous Container Database enabled with Autonomous Data Guard"
        "associated with the specified Autonomous Container Database."
    )
)
def get_autonomous_container_database_dataguard_association(
    autonomous_container_database_id: Annotated[
        Optional[Any], ("The Autonomous Container Database `OCID`.")
    ],
    autonomous_container_database_dataguard_association_id: Annotated[
        Optional[Any],
        (
            "The Autonomous Container Database-Autonomous Data Guard"
            "association `OCID`."
        ),
    ],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousContainerDatabaseDataguardAssociation:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_container_database_id"] = autonomous_container_database_id
        kwargs["autonomous_container_database_dataguard_association_id"] = (
            autonomous_container_database_dataguard_association_id
        )
        response: oci.response.Response = (
            client.get_autonomous_container_database_dataguard_association(**kwargs)
        )
        return map_autonomouscontainerdatabasedataguardassociation(response.data)
    except Exception as e:
        logger.error(
            f"Error in get_autonomous_container_database_dataguard_association tool: {e}"
        )
        raise


@mcp.tool(
    description=(
        "Get resource usage details for the specified Autonomous Container Database."
    )
)
def get_autonomous_container_database_resource_usage(
    autonomous_container_database_id: Annotated[
        Optional[Any], ("The Autonomous Container Database `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousContainerDatabaseResourceUsage:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_container_database_id"] = autonomous_container_database_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = (
            client.get_autonomous_container_database_resource_usage(**kwargs)
        )
        return map_autonomouscontainerdatabaseresourceusage(response.data)
    except Exception as e:
        logger.error(
            f"Error in get_autonomous_container_database_resource_usage tool: {e}"
        )
        raise


@mcp.tool(description=("Gets the details of the specified Autonomous Database."))
def get_autonomous_database(
    autonomous_database_id: Annotated[Optional[Any], ("The database `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousDatabase:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_database_id"] = autonomous_database_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_autonomous_database(**kwargs)
        return map_autonomousdatabase(response.data)
    except Exception as e:
        logger.error(f"Error in get_autonomous_database tool: {e}")
        raise


@mcp.tool(
    description=("Gets information about the specified Autonomous Database backup.")
)
def get_autonomous_database_backup(
    autonomous_database_backup_id: Annotated[
        Optional[Any], ("The `OCID` of the Autonomous Database backup.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousDatabaseBackup:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_database_backup_id"] = autonomous_database_backup_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_autonomous_database_backup(
            **kwargs
        )
        return map_autonomousdatabasebackup(response.data)
    except Exception as e:
        logger.error(f"Error in get_autonomous_database_backup tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets an Autonomous Data Guard-enabled database associated with the specified"
        "Autonomous Database."
    )
)
def get_autonomous_database_dataguard_association(
    autonomous_database_id: Annotated[Optional[Any], ("The database `OCID`.")],
    autonomous_database_dataguard_association_id: Annotated[
        Optional[Any],
        (
            "The Autonomous Container Database-Autonomous Data Guard"
            "association `OCID`."
        ),
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousDatabaseDataguardAssociation:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_database_id"] = autonomous_database_id
        kwargs["autonomous_database_dataguard_association_id"] = (
            autonomous_database_dataguard_association_id
        )
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = (
            client.get_autonomous_database_dataguard_association(**kwargs)
        )
        return map_autonomousdatabasedataguardassociation(response.data)
    except Exception as e:
        logger.error(
            f"Error in get_autonomous_database_dataguard_association tool: {e}"
        )
        raise


@mcp.tool(description=("Gets the Autonomous Database regional wallet details."))
def get_autonomous_database_regional_wallet(
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousDatabaseWallet:
    try:
        client = get_database_client(region)
        kwargs = {}
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = (
            client.get_autonomous_database_regional_wallet(**kwargs)
        )
        return map_autonomousdatabasewallet(response.data)
    except Exception as e:
        logger.error(f"Error in get_autonomous_database_regional_wallet tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about the specified Autonomous Database Software Image."
    )
)
def get_autonomous_database_software_image(
    autonomous_database_software_image_id: Annotated[
        Optional[Any], ("The Autonomous Database Software Image `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousDatabaseSoftwareImage:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_database_software_image_id"] = (
            autonomous_database_software_image_id
        )
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_autonomous_database_software_image(
            **kwargs
        )
        return map_autonomousdatabasesoftwareimage(response.data)
    except Exception as e:
        logger.error(f"Error in get_autonomous_database_software_image tool: {e}")
        raise


@mcp.tool(
    description=("Gets the wallet details for the specified Autonomous Database.")
)
def get_autonomous_database_wallet(
    autonomous_database_id: Annotated[Optional[Any], ("The database `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousDatabaseWallet:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_database_id"] = autonomous_database_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_autonomous_database_wallet(
            **kwargs
        )
        return map_autonomousdatabasewallet(response.data)
    except Exception as e:
        logger.error(f"Error in get_autonomous_database_wallet tool: {e}")
        raise


@mcp.tool(
    description=(
        "**Deprecated.** Use the :func:`get_cloud_exadata_infrastructure` operation to"
        "get details of an Exadata Infrastructure resource and the"
        ":func:`get_cloud_autonomous_vm_cluster` operation to get details of an"
        "Autonomous Exadata VM cluster."
    )
)
def get_autonomous_exadata_infrastructure(
    autonomous_exadata_infrastructure_id: Annotated[
        Optional[Any], ("The Autonomous Exadata Infrastructure `OCID`.")
    ],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousExadataInfrastructure:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_exadata_infrastructure_id"] = (
            autonomous_exadata_infrastructure_id
        )
        response: oci.response.Response = client.get_autonomous_exadata_infrastructure(
            **kwargs
        )
        return map_autonomousexadatainfrastructure(response.data)
    except Exception as e:
        logger.error(f"Error in get_autonomous_exadata_infrastructure tool: {e}")
        raise


@mcp.tool(description=("Gets information about a specific autonomous patch."))
def get_autonomous_patch(
    autonomous_patch_id: Annotated[Optional[Any], ("The autonomous patch `OCID`.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousPatch:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_patch_id"] = autonomous_patch_id
        response: oci.response.Response = client.get_autonomous_patch(**kwargs)
        return map_autonomouspatch(response.data)
    except Exception as e:
        logger.error(f"Error in get_autonomous_patch tool: {e}")
        raise


@mcp.tool(description=("Gets the details of specific Autonomous Virtual Machine."))
def get_autonomous_virtual_machine(
    autonomous_virtual_machine_id: Annotated[
        Optional[Any], ("The Autonomous Virtual machine `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousVirtualMachine:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_virtual_machine_id"] = autonomous_virtual_machine_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_autonomous_virtual_machine(
            **kwargs
        )
        return map_autonomousvirtualmachine(response.data)
    except Exception as e:
        logger.error(f"Error in get_autonomous_virtual_machine tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about the specified Autonomous VM cluster for an Exadata"
        "Cloud@Customer system. To get information about an Autonomous VM Cluster in the"
        "Oracle cloud, see :func:`get_cloud_autonomous_vm_cluster`."
    )
)
def get_autonomous_vm_cluster(
    autonomous_vm_cluster_id: Annotated[
        Optional[Any], ("The autonomous VM cluster `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousVmCluster:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_vm_cluster_id"] = autonomous_vm_cluster_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_autonomous_vm_cluster(**kwargs)
        return map_autonomousvmcluster(response.data)
    except Exception as e:
        logger.error(f"Error in get_autonomous_vm_cluster tool: {e}")
        raise


@mcp.tool(
    description=(
        "Get the resource usage details for the specified Autonomous Exadata VM cluster."
    )
)
def get_autonomous_vm_cluster_resource_usage(
    autonomous_vm_cluster_id: Annotated[
        Optional[Any], ("The autonomous VM cluster `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> AutonomousVmClusterResourceUsage:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_vm_cluster_id"] = autonomous_vm_cluster_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = (
            client.get_autonomous_vm_cluster_resource_usage(**kwargs)
        )
        return map_autonomousvmclusterresourceusage(response.data)
    except Exception as e:
        logger.error(f"Error in get_autonomous_vm_cluster_resource_usage tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified backup."))
def get_backup(
    backup_id: Annotated[Optional[Any], ("The backup `OCID`.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> Backup:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["backup_id"] = backup_id
        response: oci.response.Response = client.get_backup(**kwargs)
        return map_backup(response.data)
    except Exception as e:
        logger.error(f"Error in get_backup tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about the specified backup destination in an Exadata"
        "Cloud@Customer system."
    )
)
def get_backup_destination(
    backup_destination_id: Annotated[
        Optional[Any], ("The `OCID` of the backup destination.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> BackupDestination:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["backup_destination_id"] = backup_destination_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_backup_destination(**kwargs)
        return map_backupdestination(response.data)
    except Exception as e:
        logger.error(f"Error in get_backup_destination tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about the specified Autonomous Exadata VM cluster in the Oracle"
        "cloud. For Exadata Cloud@Custustomer systems, see"
        ":func:`get_autonomous_vm_cluster`."
    )
)
def get_cloud_autonomous_vm_cluster(
    cloud_autonomous_vm_cluster_id: Annotated[
        Optional[Any], ("The Cloud VM cluster `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> CloudAutonomousVmCluster:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["cloud_autonomous_vm_cluster_id"] = cloud_autonomous_vm_cluster_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_cloud_autonomous_vm_cluster(
            **kwargs
        )
        return map_cloudautonomousvmcluster(response.data)
    except Exception as e:
        logger.error(f"Error in get_cloud_autonomous_vm_cluster tool: {e}")
        raise


@mcp.tool(
    description=(
        "Get the resource usage details for the specified Cloud Autonomous Exadata VM"
        "cluster."
    )
)
def get_cloud_autonomous_vm_cluster_resource_usage(
    cloud_autonomous_vm_cluster_id: Annotated[
        Optional[Any], ("The Cloud VM cluster `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> CloudAutonomousVmClusterResourceUsage:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["cloud_autonomous_vm_cluster_id"] = cloud_autonomous_vm_cluster_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = (
            client.get_cloud_autonomous_vm_cluster_resource_usage(**kwargs)
        )
        return map_cloudautonomousvmclusterresourceusage(response.data)
    except Exception as e:
        logger.error(
            f"Error in get_cloud_autonomous_vm_cluster_resource_usage tool: {e}"
        )
        raise


@mcp.tool(
    description=(
        "Gets information about the specified cloud Exadata infrastructure resource."
        "Applies to Exadata Cloud Service instances and Autonomous Database on dedicated"
        "Exadata infrastructure only."
    )
)
def get_cloud_exadata_infrastructure(
    cloud_exadata_infrastructure_id: Annotated[
        Optional[Any], ("The cloud Exadata infrastructure `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> CloudExadataInfrastructure:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["cloud_exadata_infrastructure_id"] = cloud_exadata_infrastructure_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_cloud_exadata_infrastructure(
            **kwargs
        )
        return map_cloudexadatainfrastructure(response.data)
    except Exception as e:
        logger.error(f"Error in get_cloud_exadata_infrastructure tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets unallocated resources information for the specified Cloud Exadata"
        "infrastructure."
    )
)
def get_cloud_exadata_infrastructure_unallocated_resources(
    cloud_exadata_infrastructure_id: Annotated[
        Optional[Any], ("The cloud Exadata infrastructure `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    db_servers: Annotated[
        Optional[Any], ("The list of `OCIDs` of the Db servers.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> CloudExadataInfrastructureUnallocatedResources:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["cloud_exadata_infrastructure_id"] = cloud_exadata_infrastructure_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if db_servers is not None:
            kwargs["db_servers"] = db_servers
        response: oci.response.Response = (
            client.get_cloud_exadata_infrastructure_unallocated_resources(**kwargs)
        )
        return map_cloudexadatainfrastructureunallocatedresources(response.data)
    except Exception as e:
        logger.error(
            f"Error in get_cloud_exadata_infrastructure_unallocated_resources tool: {e}"
        )
        raise


@mcp.tool(
    description=(
        "Gets information about the specified cloud VM cluster. Applies to Exadata Cloud"
        "Service instances and Autonomous Database on dedicated Exadata infrastructure"
        "only."
    )
)
def get_cloud_vm_cluster(
    cloud_vm_cluster_id: Annotated[Optional[Any], ("The cloud VM cluster `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> CloudVmCluster:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["cloud_vm_cluster_id"] = cloud_vm_cluster_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_cloud_vm_cluster(**kwargs)
        return map_cloudvmcluster(response.data)
    except Exception as e:
        logger.error(f"Error in get_cloud_vm_cluster tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets the IORM configuration for the specified cloud VM cluster in an Exadata"
        "Cloud Service instance."
    )
)
def get_cloud_vm_cluster_iorm_config(
    cloud_vm_cluster_id: Annotated[Optional[Any], ("The cloud VM cluster `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExadataIormConfig:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["cloud_vm_cluster_id"] = cloud_vm_cluster_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_cloud_vm_cluster_iorm_config(
            **kwargs
        )
        return map_exadataiormconfig(response.data)
    except Exception as e:
        logger.error(f"Error in get_cloud_vm_cluster_iorm_config tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about a specified maintenance update package for a cloud VM"
        "cluster. Applies to Exadata Cloud Service instances only."
    )
)
def get_cloud_vm_cluster_update(
    cloud_vm_cluster_id: Annotated[Optional[Any], ("The cloud VM cluster `OCID`.")],
    update_id: Annotated[Optional[Any], ("The `OCID` of the maintenance update.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> Update:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["cloud_vm_cluster_id"] = cloud_vm_cluster_id
        kwargs["update_id"] = update_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_cloud_vm_cluster_update(**kwargs)
        return map_update(response.data)
    except Exception as e:
        logger.error(f"Error in get_cloud_vm_cluster_update tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets the maintenance update history details for the specified update history"
        "entry. Applies to Exadata Cloud Service instances only."
    )
)
def get_cloud_vm_cluster_update_history_entry(
    cloud_vm_cluster_id: Annotated[Optional[Any], ("The cloud VM cluster `OCID`.")],
    update_history_entry_id: Annotated[
        Optional[Any], ("The `OCID` of the maintenance update history entry.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> UpdateHistoryEntry:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["cloud_vm_cluster_id"] = cloud_vm_cluster_id
        kwargs["update_history_entry_id"] = update_history_entry_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = (
            client.get_cloud_vm_cluster_update_history_entry(**kwargs)
        )
        return map_updatehistoryentry(response.data)
    except Exception as e:
        logger.error(f"Error in get_cloud_vm_cluster_update_history_entry tool: {e}")
        raise


@mcp.tool(
    description=("Gets the specified database node console connection's information.")
)
def get_console_connection(
    db_node_id: Annotated[Optional[Any], ("The database node `OCID`.")],
    console_connection_id: Annotated[
        Optional[Any], ("The OCID of the console connection.")
    ],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ConsoleConnection:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_node_id"] = db_node_id
        kwargs["console_connection_id"] = console_connection_id
        response: oci.response.Response = client.get_console_connection(**kwargs)
        return map_consoleconnection(response.data)
    except Exception as e:
        logger.error(f"Error in get_console_connection tool: {e}")
        raise


@mcp.tool(
    description=("Gets information about the specified database node console history.")
)
def get_console_history(
    db_node_id: Annotated[Optional[Any], ("The database node `OCID`.")],
    console_history_id: Annotated[Optional[Any], ("The OCID of the console history.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ConsoleHistory:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_node_id"] = db_node_id
        kwargs["console_history_id"] = console_history_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_console_history(**kwargs)
        return map_consolehistory(response.data)
    except Exception as e:
        logger.error(f"Error in get_console_history tool: {e}")
        raise


@mcp.tool(
    description=(
        "Retrieves the specified database node console history contents upto a megabyte."
    )
)
def get_console_history_content(
    db_node_id: Annotated[Optional[Any], ("The database node `OCID`.")],
    console_history_id: Annotated[Optional[Any], ("The OCID of the console history.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> list[Any]:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_node_id"] = db_node_id
        kwargs["console_history_id"] = console_history_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_console_history_content(**kwargs)
        return [oci.util.to_dict(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error in get_console_history_content tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets the specified Data Guard association's configuration information."
    )
)
def get_data_guard_association(
    database_id: Annotated[Optional[Any], ("The database `OCID`.")],
    data_guard_association_id: Annotated[
        Optional[Any], ("The Data Guard association's `OCID`.")
    ],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> DataGuardAssociation:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["database_id"] = database_id
        kwargs["data_guard_association_id"] = data_guard_association_id
        response: oci.response.Response = client.get_data_guard_association(**kwargs)
        return map_dataguardassociation(response.data)
    except Exception as e:
        logger.error(f"Error in get_data_guard_association tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified database."))
def get_database(
    database_id: Annotated[Optional[Any], ("The database `OCID`.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> Database:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["database_id"] = database_id
        response: oci.response.Response = client.get_database(**kwargs)
        return map_database(response.data)
    except Exception as e:
        logger.error(f"Error in get_database tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified database software image."))
def get_database_software_image(
    database_software_image_id: Annotated[Optional[Any], ("The DB system `OCID`.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> DatabaseSoftwareImage:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["database_software_image_id"] = database_software_image_id
        response: oci.response.Response = client.get_database_software_image(**kwargs)
        return map_databasesoftwareimage(response.data)
    except Exception as e:
        logger.error(f"Error in get_database_software_image tool: {e}")
        raise


@mcp.tool(description=("gets the upgrade history for a specified database."))
def get_database_upgrade_history_entry(
    database_id: Annotated[Optional[Any], ("The database `OCID`.")],
    upgrade_history_entry_id: Annotated[
        Optional[Any], ("The database/db system upgrade History `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> DatabaseUpgradeHistoryEntry:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["database_id"] = database_id
        kwargs["upgrade_history_entry_id"] = upgrade_history_entry_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_database_upgrade_history_entry(
            **kwargs
        )
        return map_databaseupgradehistoryentry(response.data)
    except Exception as e:
        logger.error(f"Error in get_database_upgrade_history_entry tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified Database Home."))
def get_db_home(
    db_home_id: Annotated[Optional[Any], ("The Database Home `OCID`.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> DbHome:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_home_id"] = db_home_id
        response: oci.response.Response = client.get_db_home(**kwargs)
        return map_dbhome(response.data)
    except Exception as e:
        logger.error(f"Error in get_db_home tool: {e}")
        raise


@mcp.tool(description=("Gets information about a specified patch package."))
def get_db_home_patch(
    db_home_id: Annotated[Optional[Any], ("The Database Home `OCID`.")],
    patch_id: Annotated[Optional[Any], ("The `OCID` of the patch.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> Patch:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_home_id"] = db_home_id
        kwargs["patch_id"] = patch_id
        response: oci.response.Response = client.get_db_home_patch(**kwargs)
        return map_patch(response.data)
    except Exception as e:
        logger.error(f"Error in get_db_home_patch tool: {e}")
        raise


@mcp.tool(
    description=("Gets the patch history details for the specified patchHistoryEntryId")
)
def get_db_home_patch_history_entry(
    db_home_id: Annotated[Optional[Any], ("The Database Home `OCID`.")],
    patch_history_entry_id: Annotated[
        Optional[Any], ("The `OCID` of the patch history entry.")
    ],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> PatchHistoryEntry:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_home_id"] = db_home_id
        kwargs["patch_history_entry_id"] = patch_history_entry_id
        response: oci.response.Response = client.get_db_home_patch_history_entry(
            **kwargs
        )
        return map_patchhistoryentry(response.data)
    except Exception as e:
        logger.error(f"Error in get_db_home_patch_history_entry tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified database node."))
def get_db_node(
    db_node_id: Annotated[Optional[Any], ("The database node `OCID`.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> DbNode:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_node_id"] = db_node_id
        response: oci.response.Response = client.get_db_node(**kwargs)
        return map_dbnode(response.data)
    except Exception as e:
        logger.error(f"Error in get_db_node tool: {e}")
        raise


@mcp.tool(description=("Gets information about the Exadata Db server."))
def get_db_server(
    exadata_infrastructure_id: Annotated[
        Optional[Any], ("The `OCID` of the ExadataInfrastructure.")
    ],
    db_server_id: Annotated[Optional[Any], ("The DB server `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> DbServer:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["exadata_infrastructure_id"] = exadata_infrastructure_id
        kwargs["db_server_id"] = db_server_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_db_server(**kwargs)
        return map_dbserver(response.data)
    except Exception as e:
        logger.error(f"Error in get_db_server tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified DB system."))
def get_db_system(
    db_system_id: Annotated[Optional[Any], ("The DB system `OCID`.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> DbSystem:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_system_id"] = db_system_id
        response: oci.response.Response = client.get_db_system(**kwargs)
        return map_dbsystem(response.data)
    except Exception as e:
        logger.error(f"Error in get_db_system tool: {e}")
        raise


@mcp.tool(description=("Gets information the specified patch."))
def get_db_system_patch(
    db_system_id: Annotated[Optional[Any], ("The DB system `OCID`.")],
    patch_id: Annotated[Optional[Any], ("The `OCID` of the patch.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> Patch:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_system_id"] = db_system_id
        kwargs["patch_id"] = patch_id
        response: oci.response.Response = client.get_db_system_patch(**kwargs)
        return map_patch(response.data)
    except Exception as e:
        logger.error(f"Error in get_db_system_patch tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets the details of the specified patch operation on the specified DB system."
    )
)
def get_db_system_patch_history_entry(
    db_system_id: Annotated[Optional[Any], ("The DB system `OCID`.")],
    patch_history_entry_id: Annotated[
        Optional[Any], ("The `OCID` of the patch history entry.")
    ],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> PatchHistoryEntry:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_system_id"] = db_system_id
        kwargs["patch_history_entry_id"] = patch_history_entry_id
        response: oci.response.Response = client.get_db_system_patch_history_entry(
            **kwargs
        )
        return map_patchhistoryentry(response.data)
    except Exception as e:
        logger.error(f"Error in get_db_system_patch_history_entry tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets the details of the specified operating system upgrade operation for the"
        "specified DB system."
    )
)
def get_db_system_upgrade_history_entry(
    db_system_id: Annotated[Optional[Any], ("The DB system `OCID`.")],
    upgrade_history_entry_id: Annotated[
        Optional[Any], ("The database/db system upgrade History `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> DbSystemUpgradeHistoryEntry:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_system_id"] = db_system_id
        kwargs["upgrade_history_entry_id"] = upgrade_history_entry_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_db_system_upgrade_history_entry(
            **kwargs
        )
        return map_dbsystemupgradehistoryentry(response.data)
    except Exception as e:
        logger.error(f"Error in get_db_system_upgrade_history_entry tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about the specified Exadata infrastructure. Applies to Exadata"
        "Cloud@Customer instances only."
    )
)
def get_exadata_infrastructure(
    exadata_infrastructure_id: Annotated[
        Optional[Any], ("The Exadata infrastructure `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    excluded_fields: Annotated[
        Optional[Any],
        (
            "If provided, the specified fields will be excluded in the"
            'response. Allowed values are: "multiRackConfigurationFile"'
        ),
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExadataInfrastructure:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["exadata_infrastructure_id"] = exadata_infrastructure_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if excluded_fields is not None:
            kwargs["excluded_fields"] = excluded_fields
        response: oci.response.Response = client.get_exadata_infrastructure(**kwargs)
        return map_exadatainfrastructure(response.data)
    except Exception as e:
        logger.error(f"Error in get_exadata_infrastructure tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets details of the available and consumed OCPUs for the specified Autonomous"
        "Exadata Infrastructure resource."
    )
)
def get_exadata_infrastructure_ocpus(
    autonomous_exadata_infrastructure_id: Annotated[
        Optional[Any], ("The Autonomous Exadata Infrastructure `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> OCPUs:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["autonomous_exadata_infrastructure_id"] = (
            autonomous_exadata_infrastructure_id
        )
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_exadata_infrastructure_ocpus(
            **kwargs
        )
        return map_ocpus(response.data)
    except Exception as e:
        logger.error(f"Error in get_exadata_infrastructure_ocpus tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets un allocated resources information for the specified Exadata"
        "infrastructure. Applies to Exadata Cloud@Customer instances only."
    )
)
def get_exadata_infrastructure_un_allocated_resources(
    exadata_infrastructure_id: Annotated[
        Optional[Any], ("The Exadata infrastructure `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    db_servers: Annotated[
        Optional[Any], ("The list of `OCIDs` of the Db servers.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExadataInfrastructureUnAllocatedResources:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["exadata_infrastructure_id"] = exadata_infrastructure_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if db_servers is not None:
            kwargs["db_servers"] = db_servers
        response: oci.response.Response = (
            client.get_exadata_infrastructure_un_allocated_resources(**kwargs)
        )
        return map_exadatainfrastructureunallocatedresources(response.data)
    except Exception as e:
        logger.error(
            f"Error in get_exadata_infrastructure_un_allocated_resources tool: {e}"
        )
        raise


@mcp.tool(
    description=(
        "Gets the IORM configuration settings for the specified cloud Exadata DB system."
    )
)
def get_exadata_iorm_config(
    db_system_id: Annotated[Optional[Any], ("The DB system `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExadataIormConfig:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_system_id"] = db_system_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_exadata_iorm_config(**kwargs)
        return map_exadataiormconfig(response.data)
    except Exception as e:
        logger.error(f"Error in get_exadata_iorm_config tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about the specified Exadata VM cluster on Exascale"
        "Infrastructure. Applies to Exadata Database Service on Exascale Infrastructure"
        "only."
    )
)
def get_exadb_vm_cluster(
    exadb_vm_cluster_id: Annotated[
        Optional[Any], ("The Exadata VM cluster `OCID` on Exascale Infrastructure.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExadbVmCluster:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["exadb_vm_cluster_id"] = exadb_vm_cluster_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_exadb_vm_cluster(**kwargs)
        return map_exadbvmcluster(response.data)
    except Exception as e:
        logger.error(f"Error in get_exadb_vm_cluster tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about a specified maintenance update package for a Exadata VM"
        "cluster on Exascale Infrastructure."
    )
)
def get_exadb_vm_cluster_update(
    exadb_vm_cluster_id: Annotated[
        Optional[Any], ("The Exadata VM cluster `OCID` on Exascale Infrastructure.")
    ],
    update_id: Annotated[Optional[Any], ("The `OCID` of the maintenance update.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExadbVmClusterUpdate:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["exadb_vm_cluster_id"] = exadb_vm_cluster_id
        kwargs["update_id"] = update_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_exadb_vm_cluster_update(**kwargs)
        return map_exadbvmclusterupdate(response.data)
    except Exception as e:
        logger.error(f"Error in get_exadb_vm_cluster_update tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets the maintenance update history details for the specified update history"
        "entry."
    )
)
def get_exadb_vm_cluster_update_history_entry(
    exadb_vm_cluster_id: Annotated[
        Optional[Any], ("The Exadata VM cluster `OCID` on Exascale Infrastructure.")
    ],
    update_history_entry_id: Annotated[
        Optional[Any], ("The `OCID` of the maintenance update history entry.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExadbVmClusterUpdateHistoryEntry:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["exadb_vm_cluster_id"] = exadb_vm_cluster_id
        kwargs["update_history_entry_id"] = update_history_entry_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = (
            client.get_exadb_vm_cluster_update_history_entry(**kwargs)
        )
        return map_exadbvmclusterupdatehistoryentry(response.data)
    except Exception as e:
        logger.error(f"Error in get_exadb_vm_cluster_update_history_entry tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about the specified Exadata Database Storage Vaults in the"
        "specified compartment."
    )
)
def get_exascale_db_storage_vault(
    exascale_db_storage_vault_id: Annotated[
        Optional[Any], ("The Exadata Database Storage Vault `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExascaleDbStorageVault:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["exascale_db_storage_vault_id"] = exascale_db_storage_vault_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_exascale_db_storage_vault(**kwargs)
        return map_exascaledbstoragevault(response.data)
    except Exception as e:
        logger.error(f"Error in get_exascale_db_storage_vault tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified execution action."))
def get_execution_action(
    execution_action_id: Annotated[Optional[Any], ("The execution action `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExecutionAction:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["execution_action_id"] = execution_action_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_execution_action(**kwargs)
        return map_executionaction(response.data)
    except Exception as e:
        logger.error(f"Error in get_execution_action tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified execution window."))
def get_execution_window(
    execution_window_id: Annotated[Optional[Any], ("The execution window `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExecutionWindow:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["execution_window_id"] = execution_window_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_execution_window(**kwargs)
        return map_executionwindow(response.data)
    except Exception as e:
        logger.error(f"Error in get_execution_window tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified external backup job."))
def get_external_backup_job(
    backup_id: Annotated[Optional[Any], ("The backup `OCID`.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExternalBackupJob:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["backup_id"] = backup_id
        response: oci.response.Response = client.get_external_backup_job(**kwargs)
        return map_externalbackupjob(response.data)
    except Exception as e:
        logger.error(f"Error in get_external_backup_job tool: {e}")
        raise


@mcp.tool(
    description=("Gets information about the specified external container database.")
)
def get_external_container_database(
    external_container_database_id: Annotated[
        Optional[Any], ("The ExternalContainerDatabase `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExternalContainerDatabase:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["external_container_database_id"] = external_container_database_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_external_container_database(
            **kwargs
        )
        return map_externalcontainerdatabase(response.data)
    except Exception as e:
        logger.error(f"Error in get_external_container_database tool: {e}")
        raise


@mcp.tool(
    description=("Gets information about the specified external database connector.")
)
def get_external_database_connector(
    external_database_connector_id: Annotated[
        Optional[Any],
        (
            "The `OCID` of the external database connector resource"
            "(`ExternalDatabaseConnectorId`)."
        ),
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExternalDatabaseConnector:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["external_database_connector_id"] = external_database_connector_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_external_database_connector(
            **kwargs
        )
        return map_externaldatabaseconnector(response.data)
    except Exception as e:
        logger.error(f"Error in get_external_database_connector tool: {e}")
        raise


@mcp.tool(
    description=("Gets information about a specific external non-container database.")
)
def get_external_non_container_database(
    external_non_container_database_id: Annotated[
        Optional[Any], ("The external non-container database `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExternalNonContainerDatabase:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["external_non_container_database_id"] = (
            external_non_container_database_id
        )
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_external_non_container_database(
            **kwargs
        )
        return map_externalnoncontainerdatabase(response.data)
    except Exception as e:
        logger.error(f"Error in get_external_non_container_database tool: {e}")
        raise


@mcp.tool(description=("Gets information about a specific"))
def get_external_pluggable_database(
    external_pluggable_database_id: Annotated[
        Optional[Any], ("The ExternalPluggableDatabaseId `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ExternalPluggableDatabase:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["external_pluggable_database_id"] = external_pluggable_database_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_external_pluggable_database(
            **kwargs
        )
        return map_externalpluggabledatabase(response.data)
    except Exception as e:
        logger.error(f"Error in get_external_pluggable_database tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets details of the Exadata Infrastructure target system software versions that"
        "can be applied to the specified infrastructure resource for maintenance updates."
    )
)
def get_infrastructure_target_versions(
    compartment_id: Annotated[Optional[Any], ("The compartment `OCID`.")],
    target_resource_id: Annotated[Optional[Any], ("The target resource ID.")] = None,
    target_resource_type: Annotated[
        Optional[Any],
        (
            "The type of the target resource. Allowed values are:"
            '"AUTONOMOUS_EXADATA_INFRASTRUCTURE",'
            '"AUTONOMOUS_CONTAINER_DATABASE", "EXADATA_DB_SYSTEM",'
            '"CLOUD_EXADATA_INFRASTRUCTURE", "EXACC_INFRASTRUCTURE",'
            '"AUTONOMOUS_VM_CLUSTER", "AUTONOMOUS_DATABASE",'
            '"CLOUD_AUTONOMOUS_VM_CLUSTER"'
        ),
    ] = None,
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> InfrastructureTargetVersion:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["compartment_id"] = compartment_id
        if target_resource_id is not None:
            kwargs["target_resource_id"] = target_resource_id
        if target_resource_type is not None:
            kwargs["target_resource_type"] = target_resource_type
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_infrastructure_target_versions(
            **kwargs
        )
        return map_infrastructuretargetversion(response.data)
    except Exception as e:
        logger.error(f"Error in get_infrastructure_target_versions tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified key store."))
def get_key_store(
    key_store_id: Annotated[Optional[Any], ("The `OCID` of the key store.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> KeyStore:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["key_store_id"] = key_store_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_key_store(**kwargs)
        return map_keystore(response.data)
    except Exception as e:
        logger.error(f"Error in get_key_store tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified maintenance run."))
def get_maintenance_run(
    maintenance_run_id: Annotated[Optional[Any], ("The maintenance run OCID.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> MaintenanceRun:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["maintenance_run_id"] = maintenance_run_id
        response: oci.response.Response = client.get_maintenance_run(**kwargs)
        return map_maintenancerun(response.data)
    except Exception as e:
        logger.error(f"Error in get_maintenance_run tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified maintenance run history."))
def get_maintenance_run_history(
    maintenance_run_history_id: Annotated[
        Optional[Any], ("The maintenance run history OCID.")
    ],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> MaintenanceRunHistory:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["maintenance_run_history_id"] = maintenance_run_history_id
        response: oci.response.Response = client.get_maintenance_run_history(**kwargs)
        return map_maintenancerunhistory(response.data)
    except Exception as e:
        logger.error(f"Error in get_maintenance_run_history tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified one-off patch."))
def get_oneoff_patch(
    oneoff_patch_id: Annotated[Optional[Any], ("The one-off patch `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> OneoffPatch:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["oneoff_patch_id"] = oneoff_patch_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_oneoff_patch(**kwargs)
        return map_oneoffpatch(response.data)
    except Exception as e:
        logger.error(f"Error in get_oneoff_patch tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets the details of operations performed to convert the specified database from"
        "non-container (non-CDB) to pluggable (PDB)."
    )
)
def get_pdb_conversion_history_entry(
    database_id: Annotated[Optional[Any], ("The database `OCID`.")],
    pdb_conversion_history_entry_id: Annotated[
        Optional[Any], ("The database conversion history `OCID`.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> PdbConversionHistoryEntry:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["database_id"] = database_id
        kwargs["pdb_conversion_history_entry_id"] = pdb_conversion_history_entry_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_pdb_conversion_history_entry(
            **kwargs
        )
        return map_pdbconversionhistoryentry(response.data)
    except Exception as e:
        logger.error(f"Error in get_pdb_conversion_history_entry tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified Scheduled Action."))
def get_scheduled_action(
    scheduled_action_id: Annotated[Optional[Any], ("The Scheduled Action `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> ScheduledAction:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["scheduled_action_id"] = scheduled_action_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_scheduled_action(**kwargs)
        return map_scheduledaction(response.data)
    except Exception as e:
        logger.error(f"Error in get_scheduled_action tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified Scheduling Plan."))
def get_scheduling_plan(
    scheduling_plan_id: Annotated[Optional[Any], ("The Schedule Plan `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> SchedulingPlan:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["scheduling_plan_id"] = scheduling_plan_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_scheduling_plan(**kwargs)
        return map_schedulingplan(response.data)
    except Exception as e:
        logger.error(f"Error in get_scheduling_plan tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified Scheduling Policy."))
def get_scheduling_policy(
    scheduling_policy_id: Annotated[Optional[Any], ("The Scheduling Policy `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> SchedulingPolicy:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["scheduling_policy_id"] = scheduling_policy_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_scheduling_policy(**kwargs)
        return map_schedulingpolicy(response.data)
    except Exception as e:
        logger.error(f"Error in get_scheduling_policy tool: {e}")
        raise


@mcp.tool(description=("Gets information about the specified Scheduling Window."))
def get_scheduling_window(
    scheduling_policy_id: Annotated[Optional[Any], ("The Scheduling Policy `OCID`.")],
    scheduling_window_id: Annotated[Optional[Any], ("The Scheduling Window `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> SchedulingWindow:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["scheduling_policy_id"] = scheduling_policy_id
        kwargs["scheduling_window_id"] = scheduling_window_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_scheduling_window(**kwargs)
        return map_schedulingwindow(response.data)
    except Exception as e:
        logger.error(f"Error in get_scheduling_window tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about the VM cluster. Applies to Exadata Cloud@Customer"
        "instances only."
    )
)
def get_vm_cluster(
    vm_cluster_id: Annotated[Optional[Any], ("The VM cluster `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> VmCluster:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["vm_cluster_id"] = vm_cluster_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_vm_cluster(**kwargs)
        return map_vmcluster(response.data)
    except Exception as e:
        logger.error(f"Error in get_vm_cluster tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about the specified VM cluster network. Applies to Exadata"
        "Cloud@Customer instances only."
    )
)
def get_vm_cluster_network(
    exadata_infrastructure_id: Annotated[
        Optional[Any], ("The Exadata infrastructure `OCID`.")
    ],
    vm_cluster_network_id: Annotated[Optional[Any], ("The VM cluster network `OCID`.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> VmClusterNetwork:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["exadata_infrastructure_id"] = exadata_infrastructure_id
        kwargs["vm_cluster_network_id"] = vm_cluster_network_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_vm_cluster_network(**kwargs)
        return map_vmclusternetwork(response.data)
    except Exception as e:
        logger.error(f"Error in get_vm_cluster_network tool: {e}")
        raise


@mcp.tool(description=("Gets information about a specified patch package."))
def get_vm_cluster_patch(
    vm_cluster_id: Annotated[Optional[Any], ("The VM cluster `OCID`.")],
    patch_id: Annotated[Optional[Any], ("The `OCID` of the patch.")],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> Patch:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["vm_cluster_id"] = vm_cluster_id
        kwargs["patch_id"] = patch_id
        response: oci.response.Response = client.get_vm_cluster_patch(**kwargs)
        return map_patch(response.data)
    except Exception as e:
        logger.error(f"Error in get_vm_cluster_patch tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets the patch history details for the specified patch history entry."
    )
)
def get_vm_cluster_patch_history_entry(
    vm_cluster_id: Annotated[Optional[Any], ("The VM cluster `OCID`.")],
    patch_history_entry_id: Annotated[
        Optional[Any], ("The `OCID` of the patch history entry.")
    ],
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> PatchHistoryEntry:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["vm_cluster_id"] = vm_cluster_id
        kwargs["patch_history_entry_id"] = patch_history_entry_id
        response: oci.response.Response = client.get_vm_cluster_patch_history_entry(
            **kwargs
        )
        return map_patchhistoryentry(response.data)
    except Exception as e:
        logger.error(f"Error in get_vm_cluster_patch_history_entry tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets information about a specified maintenance update package for a VM cluster."
        "Applies to Exadata Cloud@Customer instances only."
    )
)
def get_vm_cluster_update(
    vm_cluster_id: Annotated[Optional[Any], ("The VM cluster `OCID`.")],
    update_id: Annotated[Optional[Any], ("The `OCID` of the maintenance update.")],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> VmClusterUpdate:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["vm_cluster_id"] = vm_cluster_id
        kwargs["update_id"] = update_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_vm_cluster_update(**kwargs)
        return map_vmclusterupdate(response.data)
    except Exception as e:
        logger.error(f"Error in get_vm_cluster_update tool: {e}")
        raise


@mcp.tool(
    description=(
        "Gets the maintenance update history details for the specified update history"
        "entry. Applies to Exadata Cloud@Customer instances only."
    )
)
def get_vm_cluster_update_history_entry(
    vm_cluster_id: Annotated[Optional[Any], ("The VM cluster `OCID`.")],
    update_history_entry_id: Annotated[
        Optional[Any], ("The `OCID` of the maintenance update history entry.")
    ],
    opc_request_id: Annotated[
        Optional[Any], ("Unique identifier for the request.")
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request (Use proper region identifiers like us-ashburn-1, eu-zurich-1), if unspecified then default region will be picked",
    ] = None,
) -> VmClusterUpdateHistoryEntry:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["vm_cluster_id"] = vm_cluster_id
        kwargs["update_history_entry_id"] = update_history_entry_id
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response: oci.response.Response = client.get_vm_cluster_update_history_entry(
            **kwargs
        )
        return map_vmclusterupdatehistoryentry(response.data)
    except Exception as e:
        logger.error(f"Error in get_vm_cluster_update_history_entry tool: {e}")
        raise


def main():
    mcp.run()


if __name__ == "__main__":
    main()
