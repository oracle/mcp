"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
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
from oracle.database_mcp_server.models import (
    ApplicationVipSummary,
    AutonomousContainerDatabaseDataguardAssociation,
    AutonomousContainerDatabaseSummary,
    AutonomousContainerDatabaseVersionSummary,
    AutonomousDatabaseBackupSummary,
    AutonomousDatabaseCharacterSets,
    AutonomousDatabaseDataguardAssociation,
    AutonomousDatabasePeerCollection,
    AutonomousDatabaseSoftwareImageCollection,
    AutonomousDatabaseSummary,
    AutonomousDbPreviewVersionSummary,
    AutonomousDbVersionSummary,
    AutonomousPatchSummary,
    AutonomousVirtualMachineSummary,
    AutonomousVmClusterSummary,
    BackupDestinationSummary,
    BackupSummary,
    CloudAutonomousVmClusterSummary,
    CloudExadataInfrastructureSummary,
    CloudVmClusterSummary,
    ConsoleConnectionSummary,
    ConsoleHistoryCollection,
    CreatePluggableDatabaseDetails,
    DatabaseSoftwareImageSummary,
    DatabaseSummary,
    DataGuardAssociationSummary,
    DbHomeSummary,
    DbNodeSummary,
    DbServerSummary,
    DbSystemComputePerformanceSummary,
    DbSystemShapeSummary,
    DbSystemStoragePerformanceSummary,
    DbSystemSummary,
    DbVersionSummary,
    ExadataInfrastructureSummary,
    ExadbVmClusterSummary,
    ExadbVmClusterUpdateSummary,
    ExascaleDbStorageVaultSummary,
    ExecutionActionSummary,
    ExecutionWindowSummary,
    ExternalContainerDatabaseSummary,
    ExternalDatabaseConnectorSummary,
    ExternalNonContainerDatabaseSummary,
    ExternalPluggableDatabaseSummary,
    FlexComponentCollection,
    GiMinorVersionSummary,
    GiVersionSummary,
    KeyStoreSummary,
    MaintenanceRunHistorySummary,
    MaintenanceRunSummary,
    OneoffPatchSummary,
    PatchHistoryEntrySummary,
    PatchSummary,
    PluggableDatabase,
    PluggableDatabaseSummary,
    RefreshableCloneCollection,
    ResourcePoolShapeCollection,
    ScheduledActionCollection,
    SchedulingPlanCollection,
    SchedulingPolicySummary,
    SchedulingWindowSummary,
    SystemVersionCollection,
    UpdatePluggableDatabaseDetails,
    UpdateSummary,
    VmClusterNetworkSummary,
    VmClusterSummary,
    VmClusterUpdateSummary,
    map_applicationvipsummary,
    map_autonomouscontainerdatabasedataguardassociation,
    map_autonomouscontainerdatabasesummary,
    map_autonomouscontainerdatabaseversionsummary,
    map_autonomousdatabasebackupsummary,
    map_autonomousdatabasecharactersets,
    map_autonomousdatabasedataguardassociation,
    map_autonomousdatabasepeercollection,
    map_autonomousdatabasesoftwareimagecollection,
    map_autonomousdatabasesummary,
    map_autonomousdbpreviewversionsummary,
    map_autonomousdbversionsummary,
    map_autonomouspatchsummary,
    map_autonomousvirtualmachinesummary,
    map_autonomousvmclustersummary,
    map_backupdestinationsummary,
    map_backupsummary,
    map_cloudautonomousvmclustersummary,
    map_cloudexadatainfrastructuresummary,
    map_cloudvmclustersummary,
    map_consoleconnectionsummary,
    map_consolehistorycollection,
    map_databasesoftwareimagesummary,
    map_databasesummary,
    map_dataguardassociationsummary,
    map_dbhomesummary,
    map_dbnodesummary,
    map_dbserversummary,
    map_dbsystemcomputeperformancesummary,
    map_dbsystemshapesummary,
    map_dbsystemstorageperformancesummary,
    map_dbsystemsummary,
    map_dbversionsummary,
    map_exadatainfrastructuresummary,
    map_exadbvmclustersummary,
    map_exadbvmclusterupdatesummary,
    map_exascaledbstoragevaultsummary,
    map_executionactionsummary,
    map_executionwindowsummary,
    map_externalcontainerdatabasesummary,
    map_externaldatabaseconnectorsummary,
    map_externalnoncontainerdatabasesummary,
    map_externalpluggabledatabasesummary,
    map_flexcomponentcollection,
    map_giminorversionsummary,
    map_giversionsummary,
    map_keystoresummary,
    map_maintenancerunhistorysummary,
    map_maintenancerunsummary,
    map_oneoffpatchsummary,
    map_patchhistoryentrysummary,
    map_patchsummary,
    map_pluggabledatabase,
    map_pluggabledatabasesummary,
    map_refreshableclonecollection,
    map_resourcepoolshapecollection,
    map_scheduledactioncollection,
    map_schedulingplancollection,
    map_schedulingpolicysummary,
    map_schedulingwindowsummary,
    map_systemversioncollection,
    map_updatesummary,
    map_vmclusternetworksummary,
    map_vmclustersummary,
    map_vmclusterupdatesummary,
)

from . import __project__, __version__

logger = Logger(__name__, level="INFO")
mcp = FastMCP(name=__project__)


def get_database_client(region: str = None):
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
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
    regional_config = config.copy()  # make a shallow copy
    regional_config["region"] = region
    return oci.database.DatabaseClient(regional_config, signer=signer)


def get_identity_client():
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.identity.IdentityClient(config, signer=signer)


def call_create_pdb(client, details, opc_retry_token=None, opc_request_id=None):
    kwargs = {"create_pluggable_database_details": details}
    if opc_retry_token:
        kwargs["opc_retry_token"] = opc_retry_token
    if opc_request_id:
        kwargs["opc_request_id"] = opc_request_id
    response = client.create_pluggable_database(**kwargs)
    return map_pluggabledatabase(response.data)


def get_tenancy():
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    return os.getenv("TENANCY_ID_OVERRIDE", config["tenancy"])


def list_all_compartments_internal(only_one_page: bool, limit=100):
    """Internal function to get List all compartments in a tenancy"""
    identity_client = get_identity_client()
    response = identity_client.list_compartments(
        compartment_id=get_tenancy(),
        compartment_id_in_subtree=True,
        access_level="ACCESSIBLE",
        lifecycle_state="ACTIVE",
        limit=limit,
    )
    compartments = response.data
    compartments.append(
        identity_client.get_compartment(compartment_id=get_tenancy()).data
    )
    if only_one_page:  # limiting the number of items returned
        return compartments
    while response.has_next_page:
        response = identity_client.list_compartments(
            compartment_id=get_tenancy(),
            compartment_id_in_subtree=True,
            access_level="ACCESSIBLE",
            lifecycle_state="ACTIVE",
            page=response.next_page,
            limit=limit,
        )
        compartments.extend(response.data)

    return compartments


def get_compartment_by_name(compartment_name: str):
    """Internal function to get compartment by name with caching"""
    compartments = list_all_compartments_internal(False)
    # Search for the compartment by name
    for compartment in compartments:
        if compartment.name.lower() == compartment_name.lower():
            return compartment

    return None


@mcp.tool()
def get_compartment_by_name_tool(name: str) -> str:
    """Return a compartment matching the provided name"""
    compartment = get_compartment_by_name(name)
    if compartment:
        return str(compartment)
    else:
        return json.dumps({"error": f"Compartment '{name}' not found."})


@mcp.tool()
def list_subscribed_regions_tool() -> str:
    """Return a list of all regions the customer (tenancy) is subscribed to"""
    try:
        identity_client = get_identity_client()
        response = identity_client.list_region_subscriptions(tenancy_id=get_tenancy())
        regions = [region.region_name for region in response.data]
        return json.dumps({"regions": regions})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool(
    description="Gets a list of application virtual IP (VIP) addresses on a cloud VM cluster."
)
def list_application_vips(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    cloud_vm_cluster_id: Annotated[
        Optional[str],
        "The `OCID`__ of the cloud VM cluster associated with the application virtual IP (VIP) address. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "DISPLAYNAME", "TIMECREATED"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "TERMINATING", "TERMINATED", "FAILED"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ApplicationVipSummary:
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
        return map_applicationvipsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_application_vips tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the Autonomous Container Databases with Autonomous Data Guard-enabled associated with the specified Autonomous Container Database."
)
def list_autonomous_container_database_dataguard_associations(
    autonomous_container_database_id: Annotated[
        Optional[str],
        "The Autonomous Container Database `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousContainerDatabaseDataguardAssociation:
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
        return map_autonomouscontainerdatabasedataguardassociation(response.data)
    except Exception as e:
        logger.error(
            f"Error in list_autonomous_container_database_dataguard_associations tool: {e}"
        )
        raise


@mcp.tool(
    description="Gets a list of supported Autonomous Container Database versions."
)
def list_autonomous_container_database_versions(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    service_component: Annotated[
        Optional[str],
        'The service component to use, either ADBD or EXACC. Allowed values are: "ADBD", "EXACC"',
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousContainerDatabaseVersionSummary:
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
        return map_autonomouscontainerdatabaseversionsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_container_database_versions tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the Autonomous Container Databases in the specified compartment."
)
def list_autonomous_container_databases(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    autonomous_exadata_infrastructure_id: Annotated[
        Optional[str],
        "The Autonomous Exadata Infrastructure `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    autonomous_vm_cluster_id: Annotated[
        Optional[str],
        "The Autonomous VM Cluster `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    infrastructure_type: Annotated[
        Optional[str],
        'A filter to return only resources that match the given Infrastructure Type. Allowed values are: "CLOUD", "CLOUD_AT_CUSTOMER"',
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. **Note:** If you do not include the availability domain filter, the resources are grouped by availability domain, then sorted. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "BACKUP_IN_PROGRESS", "RESTORING", "RESTORE_FAILED", "RESTARTING", "MAINTENANCE_IN_PROGRESS", "ROLE_CHANGE_IN_PROGRESS", "ENABLING_AUTONOMOUS_DATA_GUARD", "UNAVAILABLE"',
    ] = None,
    availability_domain: Annotated[
        Optional[str],
        "A filter to return only resources that match the given availability domain exactly.",
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    service_level_agreement_type: Annotated[
        Optional[str],
        "A filter to return only resources that match the given service-level agreement type exactly.",
    ] = None,
    cloud_autonomous_vm_cluster_id: Annotated[
        Optional[str],
        "The cloud Autonomous VM Cluster `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousContainerDatabaseSummary:
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
        return map_autonomouscontainerdatabasesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_container_databases tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of Autonomous Database backups based on either the `autonomousDatabaseId` or `compartmentId` specified as a query parameter."
)
def list_autonomous_database_backups(
    autonomous_database_id: Annotated[
        Optional[str],
        "The database `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. **Note:** If you do not include the availability domain filter, the resources are grouped by availability domain, then sorted. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "CREATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "UPDATING"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    type: Annotated[
        Optional[str],
        "A filter to return only backups that matches with the given type of Backup.",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousDatabaseBackupSummary:
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
        return map_autonomousdatabasebackupsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_database_backups tool: {e}")
        raise


@mcp.tool(description="Gets a list of supported character sets.")
def list_autonomous_database_character_sets(
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    is_shared: Annotated[
        Optional[bool],
        "Specifies whether this request is for an Autonomous Database Serverless instance. By default, this request will be for Autonomous Database on Dedicated Exadata Infrastructure.",
    ] = None,
    is_dedicated: Annotated[
        Optional[bool],
        "Specifies if the request is for an Autonomous Database Dedicated instance. The default request is for an Autonomous Database Dedicated instance.",
    ] = None,
    character_set_type: Annotated[
        Optional[str],
        'Specifies whether this request pertains to database character sets or national character sets. Allowed values are: "DATABASE", "NATIONAL"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousDatabaseCharacterSets:
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
        return map_autonomousdatabasecharactersets(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_database_character_sets tool: {e}")
        raise


@mcp.tool(
    description="Lists the Autonomous Database clones for the specified Autonomous Database."
)
def list_autonomous_database_clones(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    autonomous_database_id: Annotated[
        Optional[str],
        "The database `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "STOPPING", "STOPPED", "STARTING", "TERMINATING", "TERMINATED", "UNAVAILABLE", "RESTORE_IN_PROGRESS", "RESTORE_FAILED", "BACKUP_IN_PROGRESS", "SCALE_IN_PROGRESS", "AVAILABLE_NEEDS_ATTENTION", "UPDATING", "MAINTENANCE_IN_PROGRESS", "RESTARTING", "RECREATING", "ROLE_CHANGE_IN_PROGRESS", "UPGRADING", "INACCESSIBLE", "STANDBY"',
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. **Note:** If you do not include the availability domain filter, the resources are grouped by availability domain, then sorted. Allowed values are: "NONE", "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    clone_type: Annotated[
        Optional[str],
        'A filter to return only resources that match the given clone type exactly. Allowed values are: "REFRESHABLE_CLONE"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousDatabaseSummary:
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
        return map_autonomousdatabasesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_database_clones tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the Autonomous Data Guard-enabled databases associated with the specified Autonomous Database."
)
def list_autonomous_database_dataguard_associations(
    autonomous_database_id: Annotated[
        Optional[str],
        "The database `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousDatabaseDataguardAssociation:
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
        return map_autonomousdatabasedataguardassociation(response.data)
    except Exception as e:
        logger.error(
            f"Error in list_autonomous_database_dataguard_associations tool: {e}"
        )
        raise


@mcp.tool(
    description="Lists the Autonomous Database peers for the specified Autonomous Database."
)
def list_autonomous_database_peers(
    autonomous_database_id: Annotated[
        Optional[str],
        "The database `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousDatabasePeerCollection:
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
        return map_autonomousdatabasepeercollection(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_database_peers tool: {e}")
        raise


@mcp.tool(
    description="Lists the OCIDs of the Autonomous Database local and connected remote refreshable clones with the region where they exist for the specified source database."
)
def list_autonomous_database_refreshable_clones(
    autonomous_database_id: Annotated[
        Optional[str],
        "The database `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> RefreshableCloneCollection:
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
        return map_refreshableclonecollection(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_database_refreshable_clones tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the Autonomous Database Software Images in the specified compartment."
)
def list_autonomous_database_software_images(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    image_shape_family: Annotated[
        Optional[str],
        'A filter to return only resources that match the given image shape family exactly. Allowed values are: "EXACC_SHAPE", "EXADATA_SHAPE"',
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'parameter according to which Autonomous Database Software Images will be sorted. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "AVAILABLE", "FAILED", "PROVISIONING", "EXPIRED", "TERMINATED", "TERMINATING", "UPDATING"',
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousDatabaseSoftwareImageCollection:
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
        return map_autonomousdatabasesoftwareimagecollection(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_database_software_images tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of Autonomous Databases based on the query parameters specified."
)
def list_autonomous_databases(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    autonomous_container_database_id: Annotated[
        Optional[str],
        "The Autonomous Container Database `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. **Note:** If you do not include the availability domain filter, the resources are grouped by availability domain, then sorted. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    infrastructure_type: Annotated[
        Optional[str],
        'A filter to return only resources that match the given Infrastructure Type. Allowed values are: "CLOUD", "CLOUD_AT_CUSTOMER"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "STOPPING", "STOPPED", "STARTING", "TERMINATING", "TERMINATED", "UNAVAILABLE", "RESTORE_IN_PROGRESS", "RESTORE_FAILED", "BACKUP_IN_PROGRESS", "SCALE_IN_PROGRESS", "AVAILABLE_NEEDS_ATTENTION", "UPDATING", "MAINTENANCE_IN_PROGRESS", "RESTARTING", "RECREATING", "ROLE_CHANGE_IN_PROGRESS", "UPGRADING", "INACCESSIBLE", "STANDBY"',
    ] = None,
    lifecycle_state_not_equal_to: Annotated[
        Optional[str],
        'A filter to return only resources that not match the given lifecycle state. Allowed values are: "PROVISIONING", "AVAILABLE", "STOPPING", "STOPPED", "STARTING", "TERMINATING", "TERMINATED", "UNAVAILABLE", "RESTORE_IN_PROGRESS", "RESTORE_FAILED", "BACKUP_IN_PROGRESS", "SCALE_IN_PROGRESS", "AVAILABLE_NEEDS_ATTENTION", "UPDATING", "MAINTENANCE_IN_PROGRESS", "RESTARTING", "RECREATING", "ROLE_CHANGE_IN_PROGRESS", "UPGRADING", "INACCESSIBLE", "STANDBY"',
    ] = None,
    db_workload: Annotated[
        Optional[str],
        'A filter to return only autonomous database resources that match the specified workload type. Allowed values are: "OLTP", "DW", "AJD", "APEX"',
    ] = None,
    db_version: Annotated[
        Optional[str],
        "A filter to return only autonomous database resources that match the specified dbVersion.",
    ] = None,
    is_free_tier: Annotated[
        Optional[bool],
        "Filter on the value of the resource's 'isFreeTier' property. A value of `true` returns only Always Free resources. A value of `false` excludes Always Free resources from the returned results. Omitting this parameter returns both Always Free and paid resources.",
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    is_refreshable_clone: Annotated[
        Optional[bool],
        "Filter on the value of the resource's 'isRefreshableClone' property. A value of `true` returns only refreshable clones. A value of `false` excludes refreshable clones from the returned results. Omitting this parameter returns both refreshable clones and databases that are not refreshable clones.",
    ] = None,
    is_data_guard_enabled: Annotated[
        Optional[bool],
        "A filter to return only resources that have Data Guard enabled.",
    ] = None,
    is_resource_pool_leader: Annotated[
        Optional[bool],
        "Filter if the resource is the resource pool leader. A value of `true` returns only resource pool leader.",
    ] = None,
    resource_pool_leader_id: Annotated[
        Optional[str],
        "The database `OCID`__ of the resourcepool Leader Autonomous Database. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousDatabaseSummary:
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
        return map_autonomousdatabasesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_databases tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of supported Autonomous Database versions. Note that preview version software is only available for"
)
def list_autonomous_db_preview_versions(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for DBWORKLOAD is ascending. **Note:** If you do not include the availability domain filter, the resources are grouped by availability domain, then sorted. Allowed values are: "DBWORKLOAD"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousDbPreviewVersionSummary:
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
        return map_autonomousdbpreviewversionsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_db_preview_versions tool: {e}")
        raise


@mcp.tool(description="Gets a list of supported Autonomous Database versions.")
def list_autonomous_db_versions(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    db_workload: Annotated[
        Optional[str],
        'A filter to return only autonomous database resources that match the specified workload type. Allowed values are: "OLTP", "DW", "AJD", "APEX"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousDbVersionSummary:
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
        return map_autonomousdbversionsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_db_versions tool: {e}")
        raise


@mcp.tool(
    description="Lists the Autonomous Virtual Machines in the specified Autonomous VM Cluster and Compartment."
)
def list_autonomous_virtual_machines(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    autonomous_vm_cluster_id: Annotated[
        Optional[str],
        "The Autonomous Virtual machine `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousVirtualMachineSummary:
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
        return map_autonomousvirtualmachinesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_virtual_machines tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of Exadata Cloud@Customer Autonomous VM clusters in the specified compartment. To list Autonomous VM Clusters in the Oracle Cloud, see :func:`list_cloud_autonomous_vm_clusters`."
)
def list_autonomous_vm_clusters(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    exadata_infrastructure_id: Annotated[
        Optional[str],
        "If provided, filters the results for the given Exadata Infrastructure.",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousVmClusterSummary:
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
        return map_autonomousvmclustersummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_autonomous_vm_clusters tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of backup destinations in the specified compartment."
)
def list_backup_destination(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    type: Annotated[
        Optional[str],
        "A filter to return only resources that match the given type of the Backup Destination.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> BackupDestinationSummary:
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
        return map_backupdestinationsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_backup_destination tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of backups based on the `databaseId` or `compartmentId` specified. Either one of these query parameters must be provided."
)
def list_backups(
    database_id: Annotated[
        Optional[str],
        "The `OCID`__ of the database. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    shape_family: Annotated[
        Optional[str],
        'If provided, filters the results to the set of database versions which are supported for the given shape family. Allowed values are: "SINGLENODE", "YODA", "VIRTUALMACHINE", "EXADATA", "EXACC", "EXADB_XS"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> BackupSummary:
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
        return map_backupsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_backups tool: {e}")
        raise


@mcp.tool(
    description="Lists Autonomous Exadata VM clusters in the Oracle cloud. For Exadata Cloud@Customer systems, see :func:`list_autonomous_vm_clusters`."
)
def list_cloud_autonomous_vm_clusters(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    cloud_exadata_infrastructure_id: Annotated[
        Optional[str],
        "If provided, filters the results for the specified cloud Exadata infrastructure.",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS"',
    ] = None,
    availability_domain: Annotated[
        Optional[str],
        "A filter to return only resources that match the given availability domain exactly.",
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> CloudAutonomousVmClusterSummary:
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
        return map_cloudautonomousvmclustersummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_cloud_autonomous_vm_clusters tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the cloud Exadata infrastructure resources in the specified compartment. Applies to Exadata Cloud Service instances and Autonomous Database on dedicated Exadata infrastructure only."
)
def list_cloud_exadata_infrastructures(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    cluster_placement_group_id: Annotated[
        Optional[str],
        "A filter to return only resources that match the given cluster placement group ID exactly.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> CloudExadataInfrastructureSummary:
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
        return map_cloudexadatainfrastructuresummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_cloud_exadata_infrastructures tool: {e}")
        raise


@mcp.tool(
    description="Lists the maintenance updates that can be applied to the specified cloud VM cluster. Applies to Exadata Cloud Service instances only."
)
def list_cloud_vm_cluster_updates(
    cloud_vm_cluster_id: Annotated[
        Optional[str],
        "The cloud VM cluster `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    update_type: Annotated[
        Optional[str],
        'A filter to return only resources that match the given update type exactly. Allowed values are: "GI_UPGRADE", "GI_PATCH", "OS_UPDATE"',
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> UpdateSummary:
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
        return map_updatesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_cloud_vm_cluster_updates tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the cloud VM clusters in the specified compartment. Applies to Exadata Cloud Service instances and Autonomous Database on dedicated Exadata infrastructure only."
)
def list_cloud_vm_clusters(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    cloud_exadata_infrastructure_id: Annotated[
        Optional[str],
        "If provided, filters the results for the specified cloud Exadata infrastructure.",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only cloud VM clusters that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> CloudVmClusterSummary:
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
        return map_cloudvmclustersummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_cloud_vm_clusters tool: {e}")
        raise


@mcp.tool(description="Lists the console connections for the specified database node.")
def list_console_connections(
    db_node_id: Annotated[
        Optional[str],
        "The database node `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ConsoleConnectionSummary:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_node_id"] = db_node_id
        response: oci.response.Response = client.list_console_connections(**kwargs)
        return map_consoleconnectionsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_console_connections tool: {e}")
        raise


@mcp.tool(description="Lists the console histories for the specified database node.")
def list_console_histories(
    db_node_id: Annotated[
        Optional[str],
        "The database node `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "REQUESTED", "GETTING_HISTORY", "SUCCEEDED", "FAILED", "DELETED", "DELETING"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ConsoleHistoryCollection:
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
        return map_consolehistorycollection(response.data)
    except Exception as e:
        logger.error(f"Error in list_console_histories tool: {e}")
        raise


@mcp.tool(
    description="Lists the patches applicable to the requested container database."
)
def list_container_database_patches(
    autonomous_container_database_id: Annotated[
        Optional[str],
        "The Autonomous Container Database `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    autonomous_patch_type: Annotated[
        Optional[str],
        'Autonomous patch type, either "QUARTERLY" or "TIMEZONE". Allowed values are: "QUARTERLY", "TIMEZONE"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> AutonomousPatchSummary:
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
        return map_autonomouspatchsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_container_database_patches tool: {e}")
        raise


@mcp.tool(description="Lists all Data Guard associations for the specified database.")
def list_data_guard_associations(
    database_id: Annotated[
        Optional[str],
        "The database `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> DataGuardAssociationSummary:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["database_id"] = database_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_data_guard_associations(**kwargs)
        return map_dataguardassociationsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_data_guard_associations tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the database software images in the specified compartment."
)
def list_database_software_images(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Default order for PATCHSET is descending. Allowed values are: "TIMECREATED", "DISPLAYNAME", "PATCHSET"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "DELETING", "DELETED", "FAILED", "TERMINATING", "TERMINATED", "UPDATING"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    image_type: Annotated[
        Optional[str],
        'A filter to return only resources that match the given image type exactly. Allowed values are: "GRID_IMAGE", "DATABASE_IMAGE"',
    ] = None,
    image_shape_family: Annotated[
        Optional[str],
        'A filter to return only resources that match the given image shape family exactly. Allowed values are: "VM_BM_SHAPE", "EXADATA_SHAPE", "EXACC_SHAPE", "EXADBXS_SHAPE"',
    ] = None,
    patch_set_greater_than_or_equal_to: Annotated[
        Optional[str],
        "A filter to return only resources with `patchSet` greater than or equal to given value.",
    ] = None,
    is_upgrade_supported: Annotated[
        Optional[bool],
        "If provided, filters the results to the set of database versions which are supported for Upgrade.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> DatabaseSoftwareImageSummary:
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
        return map_databasesoftwareimagesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_database_software_images tool: {e}")
        raise


@mcp.tool(description="Gets a list of the databases in the specified Database Home.")
def list_databases(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    db_home_id: Annotated[
        Optional[str],
        "A Database Home `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    system_id: Annotated[
        Optional[str],
        "The `OCID`__ of the Exadata DB system that you want to filter the database results by. Applies only to Exadata DB systems. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DBNAME is ascending. The DBNAME sort order is case sensitive. Allowed values are: "DBNAME", "TIMECREATED"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "BACKUP_IN_PROGRESS", "UPGRADING", "CONVERTING", "TERMINATING", "TERMINATED", "RESTORE_FAILED", "FAILED"',
    ] = None,
    db_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire database name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> DatabaseSummary:
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
        return map_databasesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_databases tool: {e}")
        raise


@mcp.tool(
    description="Lists the history of patch operations on the specified Database Home."
)
def list_db_home_patch_history_entries(
    db_home_id: Annotated[
        Optional[str],
        "The Database Home `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> PatchHistoryEntrySummary:
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
        return map_patchhistoryentrysummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_db_home_patch_history_entries tool: {e}")
        raise


@mcp.tool(description="Lists patches applicable to the requested Database Home.")
def list_db_home_patches(
    db_home_id: Annotated[
        Optional[str],
        "The Database Home `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> PatchSummary:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_home_id"] = db_home_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_db_home_patches(**kwargs)
        return map_patchsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_db_home_patches tool: {e}")
        raise


@mcp.tool(
    description="Lists the Database Homes in the specified DB system and compartment. A Database Home is a directory where Oracle Database software is installed."
)
def list_db_homes(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    db_system_id: Annotated[
        Optional[str],
        "The DB system `OCID`__. If provided, filters the results to the set of database versions which are supported for the DB system. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    vm_cluster_id: Annotated[
        Optional[str],
        "The `OCID`__ of the VM cluster. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    backup_id: Annotated[
        Optional[str],
        "The `OCID`__ of the backup. Specify a backupId to list only the DB systems or DB homes that support creating a database using this backup in this compartment. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    db_version: Annotated[
        Optional[str],
        "A filter to return only DB Homes that match the specified dbVersion.",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> DbHomeSummary:
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
        return map_dbhomesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_db_homes tool: {e}")
        raise


@mcp.tool(
    description="Lists the database nodes in the specified DB system and compartment. A database node is a server running database software."
)
def list_db_nodes(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    db_system_id: Annotated[
        Optional[str],
        "The DB system `OCID`__. If provided, filters the results to the set of database versions which are supported for the DB system. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    vm_cluster_id: Annotated[
        Optional[str],
        "The `OCID`__ of the VM cluster. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'Sort by TIMECREATED. Default order for TIMECREATED is descending. Allowed values are: "TIMECREATED"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "STOPPING", "STOPPED", "STARTING", "TERMINATING", "TERMINATED", "FAILED"',
    ] = None,
    db_server_id: Annotated[
        Optional[str],
        "The `OCID`__ of the Exacc Db server. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> DbNodeSummary:
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
        return map_dbnodesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_db_nodes tool: {e}")
        raise


@mcp.tool(
    description="Lists the Exadata DB servers in the ExadataInfrastructureId and specified compartment."
)
def list_db_servers(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    exadata_infrastructure_id: Annotated[
        Optional[str],
        "The `OCID`__ of the ExadataInfrastructure. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'Sort by TIMECREATED. Default order for TIMECREATED is descending. Allowed values are: "TIMECREATED"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "CREATING", "AVAILABLE", "UNAVAILABLE", "DELETING", "DELETED", "MAINTENANCE_IN_PROGRESS"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> DbServerSummary:
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
        return map_dbserversummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_db_servers tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of expected compute performance parameters for a virtual machine DB system based on system configuration."
)
def list_db_system_compute_performances(
    db_system_shape: Annotated[
        Optional[str],
        "If provided, filters the results to the set of database versions which are supported for the given shape.",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> DbSystemComputePerformanceSummary:
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
        return map_dbsystemcomputeperformancesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_db_system_compute_performances tool: {e}")
        raise


@mcp.tool(description="Lists the patches applicable to the specified DB system.")
def list_db_system_patches(
    db_system_id: Annotated[
        Optional[str],
        "The DB system `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> PatchSummary:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["db_system_id"] = db_system_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_db_system_patches(**kwargs)
        return map_patchsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_db_system_patches tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the shapes that can be used to launch a new DB system. The shape determines resources to allocate to the DB system - CPU cores and memory for VM shapes; CPU cores, memory and storage for non-VM (or bare metal) shapes."
)
def list_db_system_shapes(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    availability_domain: Annotated[
        Optional[str], "The name of the Availability Domain."
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> DbSystemShapeSummary:
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
        return map_dbsystemshapesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_db_system_shapes tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of possible expected storage performance parameters of a VMDB System based on Configuration."
)
def list_db_system_storage_performances(
    storage_management: Annotated[
        Optional[str],
        'The DB system storage management option. Used to list database versions available for that storage manager. Valid values are `ASM` and `LVM`. * ASM specifies Oracle Automatic Storage Management * LVM specifies logical volume manager, sometimes called logical disk manager. Allowed values are: "ASM", "LVM"',
    ],
    shape_type: Annotated[
        Optional[str], "Optional. Filters the performance results by shape type."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> DbSystemStoragePerformanceSummary:
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
        return map_dbsystemstorageperformancesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_db_system_storage_performances tool: {e}")
        raise


@mcp.tool(
    description="Lists the DB systems in the specified compartment. You can specify a `backupId` to list only the DB systems that support creating a database using this backup in this compartment."
)
def list_db_systems(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    backup_id: Annotated[
        Optional[str],
        "The `OCID`__ of the backup. Specify a backupId to list only the DB systems or DB homes that support creating a database using this backup in this compartment. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. **Note:** If you do not include the availability domain filter, the resources are grouped by availability domain, then sorted. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MIGRATED", "MAINTENANCE_IN_PROGRESS", "NEEDS_ATTENTION", "UPGRADING"',
    ] = None,
    availability_domain: Annotated[
        Optional[str],
        "A filter to return only resources that match the given availability domain exactly.",
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> DbSystemSummary:
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
        return map_dbsystemsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_db_systems tool: {e}")
        raise


@mcp.tool(description="Gets a list of supported Oracle Database versions.")
def list_db_versions(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    db_system_shape: Annotated[
        Optional[str],
        "If provided, filters the results to the set of database versions which are supported for the given shape.",
    ] = None,
    db_system_id: Annotated[
        Optional[str],
        "The DB system `OCID`__. If provided, filters the results to the set of database versions which are supported for the DB system. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    storage_management: Annotated[
        Optional[str],
        'The DB system storage management option. Used to list database versions available for that storage manager. Valid values are `ASM` and `LVM`. * ASM specifies Oracle Automatic Storage Management * LVM specifies logical volume manager, sometimes called logical disk manager. Allowed values are: "ASM", "LVM"',
    ] = None,
    is_upgrade_supported: Annotated[
        Optional[bool],
        "If provided, filters the results to the set of database versions which are supported for Upgrade.",
    ] = None,
    is_database_software_image_supported: Annotated[
        Optional[bool],
        "If true, filters the results to the set of Oracle Database versions that are supported for OCI database software images.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> DbVersionSummary:
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
        return map_dbversionsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_db_versions tool: {e}")
        raise


@mcp.tool(
    description="Lists the Exadata infrastructure resources in the specified compartment. Applies to Exadata Cloud@Customer instances only."
)
def list_exadata_infrastructures(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "CREATING", "REQUIRES_ACTIVATION", "ACTIVATING", "ACTIVE", "ACTIVATION_FAILED", "FAILED", "UPDATING", "DELETING", "DELETED", "DISCONNECTED", "MAINTENANCE_IN_PROGRESS", "WAITING_FOR_CONNECTIVITY"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    excluded_fields: Annotated[
        Optional[str],
        'If provided, the specified fields will be excluded in the response. Allowed values are: "multiRackConfigurationFile"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ExadataInfrastructureSummary:
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
        return map_exadatainfrastructuresummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_exadata_infrastructures tool: {e}")
        raise


@mcp.tool(
    description="Lists the maintenance updates that can be applied to the specified Exadata VM cluster on Exascale Infrastructure."
)
def list_exadb_vm_cluster_updates(
    exadb_vm_cluster_id: Annotated[
        Optional[str],
        "The Exadata VM cluster `OCID`__ on Exascale Infrastructure. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    update_type: Annotated[
        Optional[str],
        'A filter to return only resources that match the given update type exactly. Allowed values are: "GI_UPGRADE", "GI_PATCH", "OS_UPDATE"',
    ] = None,
    version: Annotated[
        Optional[str],
        "A filter to return only resources that match the given update version exactly.",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ExadbVmClusterUpdateSummary:
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
        return map_exadbvmclusterupdatesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_exadb_vm_cluster_updates tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the Exadata VM clusters on Exascale Infrastructure in the specified compartment. Applies to Exadata Database Service on Exascale Infrastructure only."
)
def list_exadb_vm_clusters(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only Exadata VM clusters on Exascale Infrastructure that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS"',
    ] = None,
    exascale_db_storage_vault_id: Annotated[
        Optional[str],
        "A filter to return only Exadata VM clusters on Exascale Infrastructure that match the given Exascale Database Storage Vault ID.",
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ExadbVmClusterSummary:
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
        return map_exadbvmclustersummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_exadb_vm_clusters tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the Exadata Database Storage Vaults in the specified compartment."
)
def list_exascale_db_storage_vaults(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only Exadata Database Storage Vaults that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    exadata_infrastructure_id: Annotated[
        Optional[str],
        "A filter to return only list of Vaults that are linked to the exadata infrastructure Id.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ExascaleDbStorageVaultSummary:
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
        return map_exascaledbstoragevaultsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_exascale_db_storage_vaults tool: {e}")
        raise


@mcp.tool(
    description="Lists the execution action resources in the specified compartment."
)
def list_execution_actions(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "SCHEDULED", "IN_PROGRESS", "FAILED", "CANCELED", "UPDATING", "DELETED", "SUCCEEDED", "PARTIAL_SUCCESS"',
    ] = None,
    execution_window_id: Annotated[
        Optional[str],
        "A filter to return only resources that match the given execution wondow id.",
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ExecutionActionSummary:
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
        return map_executionactionsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_execution_actions tool: {e}")
        raise


@mcp.tool(
    description="Lists the execution window resources in the specified compartment."
)
def list_execution_windows(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    execution_resource_id: Annotated[
        Optional[str],
        "A filter to return only resources that match the given resource id exactly.",
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "CREATED", "SCHEDULED", "IN_PROGRESS", "FAILED", "CANCELED", "UPDATING", "DELETED", "SUCCEEDED", "PARTIAL_SUCCESS", "CREATING", "DELETING"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ExecutionWindowSummary:
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
        return map_executionwindowsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_execution_windows tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the external container databases in the specified compartment."
)
def list_external_container_databases(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "DISPLAYNAME", "TIMECREATED"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the specified lifecycle state. Allowed values are: "PROVISIONING", "NOT_CONNECTED", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ExternalContainerDatabaseSummary:
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
        return map_externalcontainerdatabasesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_external_container_databases tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the external database connectors in the specified compartment."
)
def list_external_database_connectors(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    external_database_id: Annotated[
        Optional[str],
        "The `OCID`__ of the external database whose connectors will be listed. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "DISPLAYNAME", "TIMECREATED"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the specified lifecycle state. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ExternalDatabaseConnectorSummary:
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
        return map_externaldatabaseconnectorsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_external_database_connectors tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the ExternalNonContainerDatabases in the specified compartment."
)
def list_external_non_container_databases(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "DISPLAYNAME", "TIMECREATED"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the specified lifecycle state. Allowed values are: "PROVISIONING", "NOT_CONNECTED", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ExternalNonContainerDatabaseSummary:
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
        return map_externalnoncontainerdatabasesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_external_non_container_databases tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the :func:`create_external_pluggable_database_details`"
)
def list_external_pluggable_databases(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    external_container_database_id: Annotated[
        Optional[str],
        "The ExternalContainerDatabase `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "DISPLAYNAME", "TIMECREATED"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the specified lifecycle state. Allowed values are: "PROVISIONING", "NOT_CONNECTED", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ExternalPluggableDatabaseSummary:
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
        return map_externalpluggabledatabasesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_external_pluggable_databases tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the flex components that can be used to launch a new DB system. The flex component determines resources to allocate to the DB system - Database Servers and Storage Servers."
)
def list_flex_components(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire name given. The match is not case sensitive.",
    ] = None,
    shape: Annotated[
        Optional[str],
        "A filter to return only resources that belong to the entire shape name given. The match is not case sensitive.",
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for NAME is ascending. The NAME sort order is case sensitive. Allowed values are: "NAME"',
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> FlexComponentCollection:
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
        return map_flexcomponentcollection(response.data)
    except Exception as e:
        logger.error(f"Error in list_flex_components tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of supported Oracle Grid Infrastructure minor versions for the given major version and shape family."
)
def list_gi_version_minor_versions(
    version: Annotated[Optional[str], "The Oracle Grid Infrastructure major version."],
    availability_domain: Annotated[
        Optional[str],
        "The target availability domain. Only passed if the limit is AD-specific.",
    ] = None,
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    shape_family: Annotated[
        Optional[str],
        'If provided, filters the results to the set of database versions which are supported for the given shape family. Allowed values are: "SINGLENODE", "YODA", "VIRTUALMACHINE", "EXADATA", "EXACC", "EXADB_XS"',
    ] = None,
    is_gi_version_for_provisioning: Annotated[
        Optional[bool],
        "If true, returns the Grid Infrastructure versions that can be used for provisioning a cluster",
    ] = None,
    shape: Annotated[
        Optional[str], "If provided, filters the results for the given shape."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'Sort by VERSION. Default order for VERSION is descending. Allowed values are: "VERSION"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> GiMinorVersionSummary:
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
        return map_giminorversionsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_gi_version_minor_versions tool: {e}")
        raise


@mcp.tool(description="Gets a list of supported GI versions.")
def list_gi_versions(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    shape: Annotated[
        Optional[str], "If provided, filters the results for the given shape."
    ] = None,
    availability_domain: Annotated[
        Optional[str],
        "The target availability domain. Only passed if the limit is AD-specific.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> GiVersionSummary:
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
        return map_giversionsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_gi_versions tool: {e}")
        raise


@mcp.tool(description="Gets a list of key stores in the specified compartment.")
def list_key_stores(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> KeyStoreSummary:
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
        return map_keystoresummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_key_stores tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the maintenance run histories in the specified compartment."
)
def list_maintenance_run_history(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    target_resource_id: Annotated[Optional[str], "The target resource ID."] = None,
    target_resource_type: Annotated[
        Optional[str],
        'The type of the target resource. Allowed values are: "AUTONOMOUS_EXADATA_INFRASTRUCTURE", "AUTONOMOUS_CONTAINER_DATABASE", "EXADATA_DB_SYSTEM", "CLOUD_EXADATA_INFRASTRUCTURE", "EXACC_INFRASTRUCTURE", "AUTONOMOUS_VM_CLUSTER", "AUTONOMOUS_DATABASE", "CLOUD_AUTONOMOUS_VM_CLUSTER"',
    ] = None,
    maintenance_type: Annotated[
        Optional[str],
        'The maintenance type. Allowed values are: "PLANNED", "UNPLANNED"',
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIME_SCHEDULED and TIME_ENDED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. **Note:** If you do not include the availability domain filter, the resources are grouped by availability domain, then sorted. Allowed values are: "TIME_SCHEDULED", "TIME_ENDED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'The state of the maintenance run history. Allowed values are: "SCHEDULED", "IN_PROGRESS", "SUCCEEDED", "SKIPPED", "FAILED", "UPDATING", "DELETING", "DELETED", "CANCELED"',
    ] = None,
    availability_domain: Annotated[
        Optional[str],
        "A filter to return only resources that match the given availability domain exactly.",
    ] = None,
    maintenance_subtype: Annotated[
        Optional[str],
        'The sub-type of the maintenance run. Allowed values are: "QUARTERLY", "HARDWARE", "CRITICAL", "INFRASTRUCTURE", "DATABASE", "ONEOFF", "SECURITY_MONTHLY", "TIMEZONE", "CUSTOM_DATABASE_SOFTWARE_IMAGE"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> MaintenanceRunHistorySummary:
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
        return map_maintenancerunhistorysummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_maintenance_run_history tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the maintenance runs in the specified compartment."
)
def list_maintenance_runs(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    target_resource_id: Annotated[Optional[str], "The target resource ID."] = None,
    target_resource_type: Annotated[
        Optional[str],
        'The type of the target resource. Allowed values are: "AUTONOMOUS_EXADATA_INFRASTRUCTURE", "AUTONOMOUS_CONTAINER_DATABASE", "EXADATA_DB_SYSTEM", "CLOUD_EXADATA_INFRASTRUCTURE", "EXACC_INFRASTRUCTURE", "AUTONOMOUS_VM_CLUSTER", "AUTONOMOUS_DATABASE", "CLOUD_AUTONOMOUS_VM_CLUSTER"',
    ] = None,
    maintenance_type: Annotated[
        Optional[str],
        'The maintenance type. Allowed values are: "PLANNED", "UNPLANNED"',
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIME_SCHEDULED and TIME_ENDED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. **Note:** If you do not include the availability domain filter, the resources are grouped by availability domain, then sorted. Allowed values are: "TIME_SCHEDULED", "TIME_ENDED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "SCHEDULED", "IN_PROGRESS", "SUCCEEDED", "SKIPPED", "FAILED", "UPDATING", "DELETING", "DELETED", "CANCELED"',
    ] = None,
    availability_domain: Annotated[
        Optional[str],
        "A filter to return only resources that match the given availability domain exactly.",
    ] = None,
    maintenance_subtype: Annotated[
        Optional[str],
        'The sub-type of the maintenance run. Allowed values are: "QUARTERLY", "HARDWARE", "CRITICAL", "INFRASTRUCTURE", "DATABASE", "ONEOFF", "SECURITY_MONTHLY", "TIMEZONE", "CUSTOM_DATABASE_SOFTWARE_IMAGE"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> MaintenanceRunSummary:
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
        return map_maintenancerunsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_maintenance_runs tool: {e}")
        raise


@mcp.tool(description="Lists one-off patches in the specified compartment.")
def list_oneoff_patches(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly Allowed values are: "CREATING", "AVAILABLE", "UPDATING", "INACTIVE", "FAILED", "EXPIRED", "DELETING", "DELETED", "TERMINATING", "TERMINATED"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> OneoffPatchSummary:
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
        return map_oneoffpatchsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_oneoff_patches tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the pluggable databases in a database or compartment. You must provide either a `databaseId` or `compartmentId` value."
)
def list_pluggable_databases(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    database_id: Annotated[
        Optional[str],
        "The `OCID`__ of the database. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for PDBNAME is ascending. The PDBNAME sort order is case sensitive. Allowed values are: "PDBNAME", "TIMECREATED"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "TERMINATING", "TERMINATED", "UPDATING", "FAILED", "RELOCATING", "RELOCATED", "REFRESHING", "RESTORE_IN_PROGRESS", "RESTORE_FAILED", "BACKUP_IN_PROGRESS", "DISABLED"',
    ] = None,
    pdb_name: Annotated[
        Optional[str],
        "A filter to return only pluggable databases that match the entire name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> PluggableDatabaseSummary:
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
        return map_pluggabledatabasesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_pluggable_databases tool: {e}")
        raise


@mcp.tool(
    description="Lists the Scheduled Action resources in the specified compartment."
)
def list_scheduled_actions(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    service_type: Annotated[
        Optional[str],
        "A filter to return only resources that match the given service type exactly.",
    ] = None,
    scheduling_plan_id: Annotated[
        Optional[str],
        "A filter to return only resources that match the given scheduling policy id exactly.",
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    id: Annotated[
        Optional[str],
        "A filter to return only resources that match the given Scheduled Action id exactly.",
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "CREATING", "NEEDS_ATTENTION", "AVAILABLE", "UPDATING", "FAILED", "DELETING", "DELETED"',
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ScheduledActionCollection:
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
        return map_scheduledactioncollection(response.data)
    except Exception as e:
        logger.error(f"Error in list_scheduled_actions tool: {e}")
        raise


@mcp.tool(
    description="Lists the Scheduling Plan resources in the specified compartment."
)
def list_scheduling_plans(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "CREATING", "NEEDS_ATTENTION", "AVAILABLE", "UPDATING", "FAILED", "DELETING", "DELETED"',
    ] = None,
    scheduling_policy_id: Annotated[
        Optional[str],
        "A filter to return only resources that match the given scheduling policy id exactly.",
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    resource_id: Annotated[
        Optional[str],
        "A filter to return only resources that match the given resource id exactly.",
    ] = None,
    id: Annotated[
        Optional[str],
        "A filter to return only resources that match the given Schedule Plan id exactly.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> SchedulingPlanCollection:
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
        return map_schedulingplancollection(response.data)
    except Exception as e:
        logger.error(f"Error in list_scheduling_plans tool: {e}")
        raise


@mcp.tool(
    description="Lists the Scheduling Policy resources in the specified compartment."
)
def list_scheduling_policies(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "CREATING", "NEEDS_ATTENTION", "AVAILABLE", "UPDATING", "FAILED", "DELETING", "DELETED"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> SchedulingPolicySummary:
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
        return map_schedulingpolicysummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_scheduling_policies tool: {e}")
        raise


@mcp.tool(
    description="Lists the Scheduling Window resources in the specified compartment."
)
def list_scheduling_windows(
    scheduling_policy_id: Annotated[
        Optional[str],
        "The Scheduling Policy `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "CREATING", "AVAILABLE", "UPDATING", "FAILED", "DELETING", "DELETED"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> SchedulingWindowSummary:
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
        return map_schedulingwindowsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_scheduling_windows tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of supported Exadata system versions for a given shape and GI version."
)
def list_system_versions(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    shape: Annotated[Optional[str], "Specifies shape query parameter."],
    gi_version: Annotated[Optional[str], "Specifies gi version query parameter."],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> SystemVersionCollection:
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
        return map_systemversioncollection(response.data)
    except Exception as e:
        logger.error(f"Error in list_system_versions tool: {e}")
        raise


@mcp.tool(
    description="Gets a list of the VM cluster networks in the specified compartment. Applies to Exadata Cloud@Customer instances only."
)
def list_vm_cluster_networks(
    exadata_infrastructure_id: Annotated[
        Optional[str],
        "The Exadata infrastructure `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "CREATING", "REQUIRES_VALIDATION", "VALIDATING", "VALIDATED", "VALIDATION_FAILED", "UPDATING", "ALLOCATED", "TERMINATING", "TERMINATED", "FAILED", "NEEDS_ATTENTION"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> VmClusterNetworkSummary:
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
        return map_vmclusternetworksummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_vm_cluster_networks tool: {e}")
        raise


@mcp.tool(
    description="Lists the patches applicable to the specified VM cluster in an Exadata Cloud@Customer system."
)
def list_vm_cluster_patches(
    vm_cluster_id: Annotated[
        Optional[str],
        "The VM cluster `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> PatchSummary:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["vm_cluster_id"] = vm_cluster_id
        if limit is not None:
            kwargs["limit"] = limit
        if page is not None:
            kwargs["page"] = page
        response: oci.response.Response = client.list_vm_cluster_patches(**kwargs)
        return map_patchsummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_vm_cluster_patches tool: {e}")
        raise


@mcp.tool(
    description="Lists the maintenance updates that can be applied to the specified VM cluster. Applies to Exadata Cloud@Customer instances only."
)
def list_vm_cluster_updates(
    vm_cluster_id: Annotated[
        Optional[str],
        "The VM cluster `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    update_type: Annotated[
        Optional[str],
        'A filter to return only resources that match the given update type exactly. Allowed values are: "GI_UPGRADE", "GI_PATCH", "OS_UPDATE"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "AVAILABLE", "SUCCESS", "IN_PROGRESS", "FAILED"',
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> VmClusterUpdateSummary:
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
        return map_vmclusterupdatesummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_vm_cluster_updates tool: {e}")
        raise


@mcp.tool(
    description="Lists the VM clusters in the specified compartment. Applies to Exadata Cloud@Customer instances only."
)
def list_vm_clusters(
    compartment_id: Annotated[
        Optional[str],
        "The compartment `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    exadata_infrastructure_id: Annotated[
        Optional[str],
        "If provided, filters the results for the given Exadata Infrastructure.",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[
        Optional[str],
        'The field to sort by. You can provide one sort order (`sortOrder`). Default order for TIMECREATED is descending. Default order for DISPLAYNAME is ascending. The DISPLAYNAME sort order is case sensitive. Allowed values are: "TIMECREATED", "DISPLAYNAME"',
    ] = None,
    sort_order: Annotated[
        Optional[str],
        'The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"',
    ] = None,
    lifecycle_state: Annotated[
        Optional[str],
        'A filter to return only resources that match the given lifecycle state exactly. Allowed values are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS"',
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A filter to return only resources that match the entire display name given. The match is not case sensitive.",
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> VmClusterSummary:
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
        return map_vmclustersummary(response.data)
    except Exception as e:
        logger.error(f"Error in list_vm_clusters tool: {e}")
        raise


@mcp.tool(description="Lists available resource pools shapes.")
def resource_pool_shapes(
    if_match: Annotated[
        Optional[str],
        "For optimistic concurrency control. In the PUT or DELETE call for a resource, set the `if-match` parameter to the value of the etag from a previous GET or POST response for that resource. The resource will be updated or deleted only if the etag you provide matches the resource's current etag value.",
    ] = None,
    opc_retry_token: Annotated[
        Optional[str],
        "A token that uniquely identifies a request so it can be retried in case of a timeout or server error without risk of executing that same action again. Retry tokens expire after 24 hours, but can be invalidated before then due to conflicting operations (for example, if a resource has been deleted and purged from the system, then a retry of the original creation request may be rejected).",
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request."
    ] = None,
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> ResourcePoolShapeCollection:
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
        return map_resourcepoolshapecollection(response.data)
    except Exception as e:
        logger.error(f"Error in resource_pool_shapes tool: {e}")
        raise


@mcp.tool(description="Deletes the specified pluggable database.")
def delete_pluggable_database(
    pluggable_database_id: Annotated[
        Optional[str],
        "The database `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
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
        "Region to execute the request, if no region is specified then default will be picked",
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
        return oci.util.to_dict(response.data)
    except Exception as e:
        logger.error(f"Error in delete_pluggable_database tool: {e}")
        raise


@mcp.tool(description="Gets information about the specified pluggable database.")
def get_pluggable_database(
    pluggable_database_id: Annotated[
        Optional[str],
        "The database `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    ],
    region: Annotated[
        str,
        "Region to execute the request, if no region is specified then default will be picked",
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
        "The database `OCID`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
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
        "Region to execute the request, if no region is specified then default will be picked",
    ] = None,
) -> PluggableDatabase:
    try:
        client = get_database_client(region)
        kwargs = {}
        kwargs["pluggable_database_id"] = pluggable_database_id
        if isinstance(
            update_pluggable_database_details, UpdatePluggableDatabaseDetails
        ):
            kwargs["update_pluggable_database_details"] = oci.util.to_dict(
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

        kwargs = {
            "create_pluggable_database_details": details,
            "opc_retry_token": opc_retry_token,
            "opc_request_id": opc_request_id,
        }

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

        clone_details = CreatePluggableDatabaseFromLocalCloneDetails(
            creation_type="LOCAL_CLONE_PDB",
            source_pluggable_database_id=source_pluggable_database_id,
            is_thin_clone=is_thin_clone,
            source_pluggable_database_snapshot_id=source_pluggable_database_snapshot_id,
            dblink_username=dblink_username,
            dblink_user_password=dblink_user_password,
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
            pdb_creation_type_details=clone_details,
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
    is_thin_clone: Optional[bool] = None,
    source_pluggable_database_snapshot_id: Optional[str] = None,
    dblink_username: Optional[str] = None,
    dblink_user_password: Optional[str] = None,
    source_tde_wallet_password: Optional[str] = None,
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
            source_pluggable_database_id=source_pluggable_database_id,
            source_container_database_admin_password=source_container_database_admin_password,
            is_thin_clone=is_thin_clone,
            source_pluggable_database_snapshot_id=source_pluggable_database_snapshot_id,
            dblink_username=dblink_username,
            dblink_user_password=dblink_user_password,
            source_tde_wallet_password=source_tde_wallet_password,
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
            pdb_creation_type_details=remote_details,
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
    source_tde_wallet_password: Optional[str] = None,
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
            source_pluggable_database_id=source_pluggable_database_id,
            source_container_database_admin_password=source_container_database_admin_password,
            dblink_username=dblink_username,
            dblink_user_password=dblink_user_password,
            source_tde_wallet_password=source_tde_wallet_password,
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
            pdb_creation_type_details=relocate_details,
        )

        return call_create_pdb(client, details, opc_retry_token, opc_request_id)

    except Exception as e:
        logger.error(f"Error in create_pdb_from_relocate: {e}")
        raise


def main():
    mcp.run()


if __name__ == "__main__":
    main()
