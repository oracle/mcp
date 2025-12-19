# OCI Database Dynamic MCP Server

## Overview

This server provides tools to interact with the OCI Database service.
You can load the required tools using the `--resources` filter, and the server is designed to dynamically generate the, during runtime.

## Running the server

```sh
uv run oracle.oci-db-dynamic-mcp-server
```

## Environment Variables

The server supports the following environment variables:

- `OCI_CONFIG_PROFILE`: OCI configuration profile name (default: "DEFAULT")

## Parameters

The server accepts the following parameters to control which OCI resources are loaded. This helps reduce startup time and token usage by only loading the tools you need.

| Parameter | Type | CLI Flag            | Description |
| :--- | :--- |:--------------------|:---------------------- |
| **Resources** | String | `--resources or -r` | A comma-separated list of OCI resources to load (e.g., `database`, `db_system`). If omitted, all available tools are loaded. |

## Configuration Example
This loads only the dbSystems and the databases resources (case-insensitive)
```json
    "database-dynamic": {
      "autoApprove": [],
      "disabled": false,
      "timeout": 30,
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "oracle.oci-db-dynamic-mcp-server",
        "--resources",
        "dbSystems, databases"
      ],
      "env": {
        "VIRTUAL_ENV": "Documents/oci-mcp/.venv",
        "OCI_CONFIG_PROFILE": "DEFAULT"
      }
```

## Tools

| Tool Name | Resource Name  | Description                                                                                                                                                                                                                                                                                                                                                         
| --- |----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ListApplicationVips | applicationVip | Gets a list of application virtual IP (VIP) addresses on a cloud VM cluster |
| CreateApplicationVip | applicationVip | Creates a new application virtual IP (VIP) address in the specified cloud VM cluster based on the request parameters you provide |
| DeleteApplicationVip | applicationVip | Deletes and deregisters the specified application virtual IP (VIP) address |
| GetApplicationVip | applicationVip | Gets information about a specified application virtual IP (VIP) address |
| ListAutonomousContainerDatabaseBackups | autonomousContainerDatabaseBackups | Gets a list of Autonomous Container Database backups by using either the 'autonomousDatabaseId' or 'compartmentId' as your query parameter |
| ListAutonomousContainerDatabaseVersions | autonomousContainerDatabaseVersions | Gets a list of supported Autonomous Container Database versions |
| ListAutonomousContainerDatabases | autonomousContainerDatabases | Gets a list of the Autonomous Container Databases in the specified compartment |
| CreateAutonomousContainerDatabase | autonomousContainerDatabases | Creates an Autonomous Container Database in the specified Autonomous Exadata Infrastructure |
| TerminateAutonomousContainerDatabase | autonomousContainerDatabases | Terminates an Autonomous Container Database, which permanently deletes the container database and any databases within the container database |
| GetAutonomousContainerDatabase | autonomousContainerDatabases | Gets information about the specified Autonomous Container Database |
| UpdateAutonomousContainerDatabase | autonomousContainerDatabases | Updates the properties of an Autonomous Container Database, such as display name, maintenance preference, backup retention, and tags |
| AddStandbyAutonomousContainerDatabase | autonomousContainerDatabases | Add a standby Autonomous Container Database |
| ChangeAutonomousContainerDatabaseCompartment | autonomousContainerDatabases | Move the Autonomous Container Database and its dependent resources to the specified compartment |
| EditAutonomousContainerDatabaseDataguard | autonomousContainerDatabases | Modify Autonomous Container Database Data Guard settings such as protection mode, automatic failover, and fast start failover lag limit |
| FailoverAutonomousContainerDatabaseDataguard | autonomousContainerDatabases | Performs failover to a standby Autonomous Container Database (ACD) identified by the autonomousContainerDatabaseId parameter |
| ReinstateAutonomousContainerDatabaseDataguard | autonomousContainerDatabases | Reinstates a disabled standby Autonomous Container Database (ACD), identified by the autonomousContainerDatabaseId parameter to an active standby ACD |
| RestartAutonomousContainerDatabase | autonomousContainerDatabases | Rolling restarts the specified Autonomous Container Database |
| RotateAutonomousContainerDatabaseEncryptionKey | autonomousContainerDatabases | Creates a new version of an existing [Vault service](/iaas/Content/KeyManagement/Concepts/keyoverview |
| ConvertStandbyAutonomousContainerDatabase | autonomousContainerDatabases | Convert the standby Autonomous Container Database (ACD) between physical standby and snapshot standby ACD |
| SwitchoverAutonomousContainerDatabaseDataguard | autonomousContainerDatabases | Switchover an Autonomous Container Database (ACD), identified by the autonomousContainerDatabaseId parameter, to an active standby ACD |
| MigrateAutonomousContainerDatabaseDataguardAssociation | autonomousContainerDatabases | Migrate Autonomous Container Database, identified by the autonomousContainerDatabaseId parameter |
| ListContainerDatabasePatches | autonomousContainerDatabases | Lists the patches applicable to the requested container database |
| GetAutonomousContainerDatabaseResourceUsage | autonomousContainerDatabases | Get resource usage details for the specified Autonomous Container Database |
| ListAutonomousDatabaseBackups | autonomousDatabaseBackups | Gets a list of Autonomous AI Database backups based on either the `autonomousDatabaseId` or `compartmentId` specified as a query parameter |
| CreateAutonomousDatabaseBackup | autonomousDatabaseBackups | Creates a new Autonomous AI Database backup for the specified database based on the provided request parameters |
| DeleteAutonomousDatabaseBackup | autonomousDatabaseBackups | Deletes a long-term backup |
| GetAutonomousDatabaseBackup | autonomousDatabaseBackups | Gets information about the specified Autonomous AI Database backup |
| UpdateAutonomousDatabaseBackup | autonomousDatabaseBackups | Updates the Autonomous AI Database backup of the specified database based on the request parameters |
| ListAutonomousDatabaseCharacterSets | autonomousDatabaseCharacterSets | Gets a list of supported character sets |
| ListAutonomousDatabaseSoftwareImages | autonomousDatabaseSoftwareImages | Gets a list of the Autonomous AI Database Software Images in the specified compartment |
| CreateAutonomousDatabaseSoftwareImage | autonomousDatabaseSoftwareImages | create Autonomous AI Database Software Image in the specified compartment |
| DeleteAutonomousDatabaseSoftwareImage | autonomousDatabaseSoftwareImages | Delete an Autonomous AI Database Software Image |
| GetAutonomousDatabaseSoftwareImage | autonomousDatabaseSoftwareImages | Gets information about the specified Autonomous AI Database Software Image |
| UpdateAutonomousDatabaseSoftwareImage | autonomousDatabaseSoftwareImages | Updates the properties of an Autonomous AI Database Software Image, like add tags |
| ChangeAutonomousDatabaseSoftwareImageCompartment | autonomousDatabaseSoftwareImages | Move the Autonomous AI Database Software Image and its dependent resources to the specified compartment |
| ListAutonomousDatabases | autonomousDatabases | Gets a list of Autonomous AI Databases based on the query parameters specified |
| CreateAutonomousDatabase | autonomousDatabases | Creates a new Autonomous AI Database |
| ResourcePoolShapes | autonomousDatabases | Lists available resource pools shapes |
| GetAutonomousDatabaseRegionalWallet | autonomousDatabases | Gets the Autonomous AI Database regional wallet details |
| UpdateAutonomousDatabaseRegionalWallet | autonomousDatabases | Updates the Autonomous AI Database regional wallet |
| DeleteAutonomousDatabase | autonomousDatabases | Deletes the specified Autonomous AI Database |
| GetAutonomousDatabase | autonomousDatabases | Gets the details of the specified Autonomous AI Database |
| UpdateAutonomousDatabase | autonomousDatabases | Updates one or more attributes of the specified Autonomous AI Database |
| ChangeAutonomousDatabaseCompartment | autonomousDatabases | Move the Autonomous AI Database and its dependent resources to the specified compartment |
| ChangeDisasterRecoveryConfiguration | autonomousDatabases | This operation updates the cross-region disaster recovery (DR) details of the standby Autonomous AI Database Serverless database, and must be run on the standby side |
| ChangeAutonomousDatabaseSubscription | autonomousDatabases | Associate an Autonomous AI Database with a different subscription |
| ConfigureAutonomousDatabaseVaultKey | autonomousDatabases | Configures the Autonomous AI Database Vault service [key](/Content/KeyManagement/Concepts/keyoverview |
| ConfigureSaasAdminUser | autonomousDatabases | This operation updates SaaS administrative user configuration of the Autonomous AI Database |
| DeregisterAutonomousDatabaseDataSafe | autonomousDatabases | Asynchronously deregisters this Autonomous AI Database with Data Safe |
| DisableAutonomousDatabaseManagement | autonomousDatabases | Disables Database Management for the Autonomous AI Database resource |
| DisableAutonomousDatabaseOperationsInsights | autonomousDatabases | Disables Operations Insights for the Autonomous AI Database resource |
| EnableAutonomousDatabaseManagement | autonomousDatabases | Enables Database Management for Autonomous AI Database |
| EnableAutonomousDatabaseOperationsInsights | autonomousDatabases | Enables the specified Autonomous AI Database with Operations Insights |
| FailOverAutonomousDatabase | autonomousDatabases | Initiates a failover of the specified Autonomous AI Database to the associated peer database |
| GenerateAutonomousDatabaseWallet | autonomousDatabases | Creates and downloads a wallet for the specified Autonomous AI Database |
| SaasAdminUserStatus | autonomousDatabases | This operation gets SaaS administrative user status of the Autonomous AI Database |
| AutonomousDatabaseManualRefresh | autonomousDatabases | Initiates a data refresh for an Autonomous AI Database refreshable clone |
| RegisterAutonomousDatabaseDataSafe | autonomousDatabases | Asynchronously registers this Autonomous AI Database with Data Safe |
| RestartAutonomousDatabase | autonomousDatabases | Restarts the specified Autonomous AI Database |
| RestoreAutonomousDatabase | autonomousDatabases | Restores an Autonomous AI Database based on the provided request parameters |
| RotateAutonomousDatabaseEncryptionKey | autonomousDatabases | Rotate existing AutonomousDatabase [Vault service](/iaas/Content/KeyManagement/Concepts/keyoverview |
| ShrinkAutonomousDatabase | autonomousDatabases | This operation shrinks the current allocated storage down to the current actual used data storage (actualUsedDataStorageSizeInTBs) |
| StartAutonomousDatabase | autonomousDatabases | Starts the specified Autonomous AI Database |
| StopAutonomousDatabase | autonomousDatabases | Stops the specified Autonomous AI Database |
| SwitchoverAutonomousDatabase | autonomousDatabases | Initiates a switchover of the specified Autonomous AI Database to the associated peer database |
| ListAutonomousDatabaseDataguardAssociations | autonomousDatabases | *Deprecated |
| GetAutonomousDatabaseDataguardAssociation | autonomousDatabases | *Deprecated |
| ListAutonomousDatabaseClones | autonomousDatabases | Lists the Autonomous AI Database clones for the specified Autonomous AI Database |
| ListAutonomousDatabasePeers | autonomousDatabases | Lists the Autonomous AI Database peers for the specified Autonomous AI Database |
| ListAutonomousDatabaseRefreshableClones | autonomousDatabases | Lists the OCIDs of the Autonomous AI Database local and connected remote refreshable clones with the region where they exist for the specified source database |
| ListResourcePoolMembers | autonomousDatabases | Lists the OCIDs of the Autonomous AI Database resource pool members for the specified Autonomous AI Database leader |
| GetAutonomousDatabaseWallet | autonomousDatabases | Gets the wallet details for the specified Autonomous AI Database |
| UpdateAutonomousDatabaseWallet | autonomousDatabases | Updates the wallet for the specified Autonomous AI Database |
| ListAutonomousDbPreviewVersions | autonomousDbPreviewVersions | Gets a list of supported Autonomous AI Database versions |
| ListAutonomousDbVersions | autonomousDbVersions | Gets a list of supported Autonomous AI Database versions |
| GetExadataInfrastructureOcpus | autonomousExadataInfrastructures | Gets details of the available and consumed OCPUs for the specified Autonomous Exadata Infrastructure resource |
| GetAutonomousPatch | autonomousPatches | Gets information about a specific autonomous patch |
| ListAutonomousVirtualMachines | autonomousVirtualMachines | Lists the Autonomous Virtual Machines in the specified Autonomous VM Cluster and Compartment |
| GetAutonomousVirtualMachine | autonomousVirtualMachines | Gets the details of specific Autonomous Virtual Machine |
| ListAutonomousVmClusters | autonomousVmClusters | Gets a list of Exadata Cloud@Customer Autonomous VM clusters in the specified compartment |
| CreateAutonomousVmCluster | autonomousVmClusters | Creates an Autonomous VM cluster for Exadata Cloud@Customer |
| DeleteAutonomousVmCluster | autonomousVmClusters | Deletes the specified Autonomous VM cluster in an Exadata Cloud@Customer system |
| GetAutonomousVmCluster | autonomousVmClusters | Gets information about the specified Autonomous VM cluster for an Exadata Cloud@Customer system |
| UpdateAutonomousVmCluster | autonomousVmClusters | Updates the specified Autonomous VM cluster for the Exadata Cloud@Customer system |
| ListAutonomousVmClusterAcdResourceUsage | autonomousVmClusters | Gets the list of resource usage details for all the Autonomous Container Database in the specified Autonomous Exadata VM cluster |
| ChangeAutonomousVmClusterCompartment | autonomousVmClusters | Moves an Autonomous VM cluster and its dependent resources to another compartment |
| RotateAutonomousVmClusterOrdsCerts | autonomousVmClusters | Rotates the Oracle REST Data Services (ORDS) certificates for Autonomous Exadata VM cluster |
| RotateAutonomousVmClusterSslCerts | autonomousVmClusters | Rotates the SSL certificates for Autonomous Exadata VM cluster |
| GetAutonomousVmClusterResourceUsage | autonomousVmClusters | Get the resource usage details for the specified Autonomous Exadata VM cluster |
| ListBackupDestination | backupDestinations | Gets a list of backup destinations in the specified compartment |
| CreateBackupDestination | backupDestinations | Creates a backup destination in an Exadata Cloud@Customer system |
| DeleteBackupDestination | backupDestinations | Deletes a backup destination in an Exadata Cloud@Customer system |
| GetBackupDestination | backupDestinations | Gets information about the specified backup destination in an Exadata Cloud@Customer system |
| UpdateBackupDestination | backupDestinations | If no database is associated with the backup destination: - For a RECOVERY_APPLIANCE backup destination, updates the connection string and/or the list of VPC users |
| ChangeBackupDestinationCompartment | backupDestinations | Move the backup destination and its dependent resources to the specified compartment |
| ListBackups | backups | Gets a list of backups based on the `databaseId` or `compartmentId` specified |
| CreateBackup | backups | Creates a new backup in the specified database based on the request parameters you provide |
| DeleteBackup | backups | Deletes a full backup |
| GetBackup | backups | Gets information about the specified backup |
| ListCloudAutonomousVmClusters | cloudAutonomousVmClusters | Lists Autonomous Exadata VM clusters in the Oracle cloud |
| CreateCloudAutonomousVmCluster | cloudAutonomousVmClusters | Creates an Autonomous Exadata VM cluster in the Oracle cloud |
| DeleteCloudAutonomousVmCluster | cloudAutonomousVmClusters | Deletes the specified Autonomous Exadata VM cluster in the Oracle cloud |
| GetCloudAutonomousVmCluster | cloudAutonomousVmClusters | Gets information about the specified Autonomous Exadata VM cluster in the Oracle cloud |
| UpdateCloudAutonomousVmCluster | cloudAutonomousVmClusters | Updates the specified Autonomous Exadata VM cluster in the Oracle cloud |
| ListCloudAutonomousVmClusterAcdResourceUsage | cloudAutonomousVmClusters | Gets the list of resource usage details for all the Cloud Autonomous Container Database in the specified Cloud Autonomous Exadata VM cluster |
| ChangeCloudAutonomousVmClusterCompartment | cloudAutonomousVmClusters | Moves an Autonomous Exadata VM cluster in the Oracle cloud and its dependent resources to another compartment |
| RotateCloudAutonomousVmClusterOrdsCerts | cloudAutonomousVmClusters | Rotates the Oracle REST Data Services (ORDS) certificates for a cloud Autonomous Exadata VM cluster |
| RotateCloudAutonomousVmClusterSslCerts | cloudAutonomousVmClusters | Rotates the SSL certficates for a cloud Autonomous Exadata VM cluster |
| GetCloudAutonomousVmClusterResourceUsage | cloudAutonomousVmClusters | Get the resource usage details for the specified Cloud Autonomous Exadata VM cluster |
| ListCloudExadataInfrastructures | cloudExadataInfrastructures | Gets a list of the cloud Exadata infrastructure resources in the specified compartment |
| CreateCloudExadataInfrastructure | cloudExadataInfrastructures | Creates a cloud Exadata infrastructure resource |
| DeleteCloudExadataInfrastructure | cloudExadataInfrastructures | Deletes the cloud Exadata infrastructure resource |
| GetCloudExadataInfrastructure | cloudExadataInfrastructures | Gets information about the specified cloud Exadata infrastructure resource |
| UpdateCloudExadataInfrastructure | cloudExadataInfrastructures | Updates the Cloud Exadata infrastructure resource |
| AddStorageCapacityCloudExadataInfrastructure | cloudExadataInfrastructures | Makes the storage capacity from additional storage servers available for Cloud VM Cluster consumption |
| ChangeCloudExadataInfrastructureCompartment | cloudExadataInfrastructures | Moves a cloud Exadata infrastructure resource and its dependent resources to another compartment |
| ChangeCloudExadataInfrastructureSubscription | cloudExadataInfrastructures | Associate a cloud Exadata infrastructure with a different subscription |
| ConfigureExascaleCloudExadataInfrastructure | cloudExadataInfrastructures | Configures Exascale on Cloud exadata infrastructure resource |
| GetCloudExadataInfrastructureUnallocatedResources | cloudExadataInfrastructures | Gets unallocated resources information for the specified Cloud Exadata infrastructure |
| ListCloudVmClusters | cloudVmClusters | Gets a list of the cloud VM clusters in the specified compartment |
| CreateCloudVmCluster | cloudVmClusters | Creates a cloud VM cluster |
| DeleteCloudVmCluster | cloudVmClusters | Deletes the specified cloud VM cluster |
| GetCloudVmCluster | cloudVmClusters | Gets information about the specified cloud VM cluster |
| UpdateCloudVmCluster | cloudVmClusters | Updates the specified cloud VM cluster |
| GetCloudVmClusterIormConfig | cloudVmClusters | Gets the IORM configuration for the specified cloud VM cluster in an Exadata Cloud Service instance |
| UpdateCloudVmClusterIormConfig | cloudVmClusters | Updates the IORM settings for the specified cloud VM cluster in an Exadata Cloud Service instance |
| AddVirtualMachineToCloudVmCluster | cloudVmClusters | Add Virtual Machines to the Cloud VM cluster |
| ChangeCloudVmClusterCompartment | cloudVmClusters | Moves a cloud VM cluster and its dependent resources to another compartment |
| ChangeCloudVmClusterSubscription | cloudVmClusters | Associate a cloud VM cluster with a different subscription |
| RemoveVirtualMachineFromCloudVmCluster | cloudVmClusters | Remove Virtual Machines from the Cloud VM cluster |
| ListCloudVmClusterUpdateHistoryEntries | cloudVmClusters | Gets the history of the maintenance update actions performed on the specified cloud VM cluster |
| GetCloudVmClusterUpdateHistoryEntry | cloudVmClusters | Gets the maintenance update history details for the specified update history entry |
| ListCloudVmClusterUpdates | cloudVmClusters | Lists the maintenance updates that can be applied to the specified cloud VM cluster |
| GetCloudVmClusterUpdate | cloudVmClusters | Gets information about a specified maintenance update package for a cloud VM cluster |
| ListDatabaseSoftwareImages | databaseSoftwareImages | Gets a list of the database software images in the specified compartment |
| CreateDatabaseSoftwareImage | databaseSoftwareImages | create database software image in the specified compartment |
| DeleteDatabaseSoftwareImage | databaseSoftwareImages | Delete a database software image |
| GetDatabaseSoftwareImage | databaseSoftwareImages | Gets information about the specified database software image |
| UpdateDatabaseSoftwareImage | databaseSoftwareImages | Updates the properties of a Database Software Image, like Display Nmae |
| ChangeDatabaseSoftwareImageCompartment | databaseSoftwareImages | Move the Database Software Image and its dependent resources to the specified compartment |
| ListDatabases | databases | Gets a list of the databases in the specified Database Home |
| CreateDatabase | databases | Creates a new database in the specified Database Home |
| DeleteDatabase | databases | Deletes the specified database |
| GetDatabase | databases | Gets information about the specified database |
| UpdateDatabase | databases | Update the specified database based on the request parameters provided |
| ChangeEncryptionKeyLocation | databases | Update the encryption key management location for the database |
| ConvertToPdb | databases | Converts a non-container database to a pluggable database |
| DisableDatabaseManagement | databases | Disables the Database Management service for the database |
| EnableDatabaseManagement | databases | Enables the Database Management service for an Oracle Database located in Oracle Cloud Infrastructure |
| MigrateVaultKey | databases | Changes encryption key management from customer-managed, using the [Vault service](/iaas/Content/KeyManagement/Concepts/keyoverview |
| ModifyDatabaseManagement | databases | Updates one or more attributes of the Database Management service for the database |
| RestoreDatabase | databases | Restore a Database based on the request parameters you provide |
| RotateVaultKey | databases | Creates a new version of an existing [Vault service](/iaas/Content/KeyManagement/Concepts/keyoverview |
| UpgradeDatabase | databases | Upgrades the specified Oracle Database instance |
| ConvertToStandalone | databases | Disassociate the standby database identified by the `databaseId` parameter from existing Data Guard group |
| FailoverDataGuard | databases | Performs a failover to transition the standby database identified by the `databaseId` path parameter into the primary role after the existing primary database fails or becomes unreachable |
| ReinstateDataGuard | databases | Reinstates the database identified by the `databaseId` parameter into the standby role in a Data Guard association |
| SwitchOverDataGuard | databases | Performs a switchover to transition primary database of this Data Guard association into a standby role |
| UpdateDataGuard | databases | Update an existing Data Guard member |
| ListDataGuardAssociations | databases | Lists all Data Guard associations for the specified database |
| CreateDataGuardAssociation | databases | Creates a new Data Guard association |
| GetDataGuardAssociation | databases | Gets the specified Data Guard association's configuration information |
| UpdateDataGuardAssociation | databases | Updates the Data Guard association the specified database |
| FailoverDataGuardAssociation | databases | Performs a failover to transition the standby database identified by the `databaseId` parameter into the specified Data Guard association's primary role after the existing primary database fails or becomes unreachable |
| MigrateDataGuardAssociationToMultiDataGuards | databases | Migrates the existing Data Guard association to new Data Guard model to support multiple standby databases functionality |
| ReinstateDataGuardAssociation | databases | Reinstates the database identified by the `databaseId` parameter into the standby role in a Data Guard association |
| SwitchoverDataGuardAssociation | databases | Performs a switchover to transition the primary database of a Data Guard association into a standby role |
| ListPdbConversionHistoryEntries | databases | Gets the pluggable database conversion history for a specified database in a bare metal or virtual machine DB system |
| GetPdbConversionHistoryEntry | databases | Gets the details of operations performed to convert the specified database from non-container (non-CDB) to pluggable (PDB) |
| ListDatabaseUpgradeHistoryEntries | databases | Gets the upgrade history for a specified database in a bare metal or virtual machine DB system |
| GetDatabaseUpgradeHistoryEntry | databases | gets the upgrade history for a specified database |
| ListDbHomes | dbHomes | Lists the Database Homes in the specified DB system and compartment |
| CreateDbHome | dbHomes | Creates a new Database Home in the specified database system based on the request parameters you provide |
| DeleteDbHome | dbHomes | Deletes a Database Home |
| GetDbHome | dbHomes | Gets information about the specified Database Home |
| UpdateDbHome | dbHomes | Patches the specified Database Home |
| ListDbHomePatchHistoryEntries | dbHomes | Lists the history of patch operations on the specified Database Home |
| GetDbHomePatchHistoryEntry | dbHomes | Gets the patch history details for the specified patchHistoryEntryId  |
| ListDbHomePatches | dbHomes | Lists patches applicable to the requested Database Home |
| GetDbHomePatch | dbHomes | Gets information about a specified patch package |
| ListDbNodes | dbNodes | Lists the database nodes in the specified DB system and compartment |
| GetDbNode | dbNodes | Gets information about the specified database node |
| DbNodeAction | dbNodes | Performs one of the following power actions on the specified DB node: - start - power on - stop - power off gracefully - softreset - ACPI shutdown and power on - reset - power off and power on  **Note:** Stopping a node affects billing differently, depending on the type of DB system: *Bare metal and Exadata systems* - The _stop_ state has no effect on the resources you consume |
| ListConsoleConnections | dbNodes | Lists the console connections for the specified database node |
| CreateConsoleConnection | dbNodes | Creates a new console connection to the specified database node |
| DeleteConsoleConnection | dbNodes | Deletes the specified database node console connection |
| GetConsoleConnection | dbNodes | Gets the specified database node console connection's information |
| ListConsoleHistories | dbNodes | Lists the console histories for the specified database node |
| CreateConsoleHistory | dbNodes | Captures the most recent serial console data (up to a megabyte) for the specified database node |
| DeleteConsoleHistory | dbNodes | Deletes the specified database node console history |
| GetConsoleHistory | dbNodes | Gets information about the specified database node console history |
| UpdateConsoleHistory | dbNodes | Updates the specified database node console history |
| GetConsoleHistoryContent | dbNodes | Retrieves the specified database node console history contents upto a megabyte |
| ListDbServers | dbServers | Lists the Exadata DB servers in the ExadataInfrastructureId and specified compartment |
| GetDbServer | dbServers | Gets information about the Exadata Db server |
| ListDbSystemComputePerformances | dbSystemComputePerformance | Gets a list of expected compute performance parameters for a virtual machine DB system based on system configuration |
| ListDbSystemShapes | dbSystemShapes | Gets a list of the shapes that can be used to launch a new DB system |
| ListFlexComponents | dbSystemShapes | Gets a list of the flex components that can be used to launch a new DB system |
| ListDbSystemStoragePerformances | dbSystemStoragePerformance | Gets a list of possible expected storage performance parameters of a VMDB System based on Configuration |
| ListDbSystems | dbSystems | Lists the DB systems in the specified compartment |
| LaunchDbSystem | dbSystems | Creates a new DB system in the specified compartment and availability domain |
| TerminateDbSystem | dbSystems | Terminates a DB system and permanently deletes it and any databases running on it, and any storage volumes attached to it |
| GetDbSystem | dbSystems | Gets information about the specified DB system |
| UpdateDbSystem | dbSystems | Updates the properties of the specified DB system |
| GetExadataIormConfig | dbSystems | Gets the IORM configuration settings for the specified cloud Exadata DB system |
| UpdateExadataIormConfig | dbSystems | Updates IORM settings for the specified Exadata DB system |
| ChangeDbSystemCompartment | dbSystems | Moves the DB system and its dependent resources to the specified compartment |
| MigrateExadataDbSystemResourceModel | dbSystems | Migrates the Exadata DB system to the new [Exadata resource model](/iaas/Content/Database/Concepts/exaflexsystem |
| UpgradeDbSystem | dbSystems | Upgrades the operating system and grid infrastructure of the DB system |
| ListDbSystemPatchHistoryEntries | dbSystems | Gets the history of the patch actions performed on the specified DB system |
| GetDbSystemPatchHistoryEntry | dbSystems | Gets the details of the specified patch operation on the specified DB system |
| ListDbSystemPatches | dbSystems | Lists the patches applicable to the specified DB system |
| GetDbSystemPatch | dbSystems | Gets information the specified patch |
| ListDbSystemUpgradeHistoryEntries | dbSystems | Gets the history of the upgrade actions performed on the specified DB system |
| GetDbSystemUpgradeHistoryEntry | dbSystems | Gets the details of the specified operating system upgrade operation for the specified DB system |
| ListDbVersions | dbVersions | Gets a list of supported Oracle Database versions |
| ListExadataInfrastructures | exadataInfrastructures | Lists the Exadata infrastructure resources in the specified compartment |
| CreateExadataInfrastructure | exadataInfrastructures | Creates an Exadata infrastructure resource |
| DeleteExadataInfrastructure | exadataInfrastructures | Deletes the Exadata Cloud@Customer infrastructure |
| GetExadataInfrastructure | exadataInfrastructures | Gets information about the specified Exadata infrastructure |
| UpdateExadataInfrastructure | exadataInfrastructures | Updates the Exadata infrastructure resource |
| ActivateExadataInfrastructure | exadataInfrastructures | Activates the specified Exadata infrastructure resource |
| AddStorageCapacityExadataInfrastructure | exadataInfrastructures | Makes the storage capacity from additional storage servers available for VM Cluster consumption |
| ChangeExadataInfrastructureCompartment | exadataInfrastructures | Moves an Exadata infrastructure resource and its dependent resources to another compartment |
| DownloadExadataInfrastructureConfigFile | exadataInfrastructures | Downloads the configuration file for the specified Exadata Cloud@Customer infrastructure |
| GetExadataInfrastructureUnAllocatedResources | exadataInfrastructures | Gets un allocated resources information for the specified Exadata infrastructure |
| ListVmClusterNetworks | exadataInfrastructures | Gets a list of the VM cluster networks in the specified compartment |
| CreateVmClusterNetwork | exadataInfrastructures | Creates the VM cluster network |
| GenerateRecommendedVmClusterNetwork | exadataInfrastructures | Generates a recommended Cloud@Customer VM cluster network configuration |
| DeleteVmClusterNetwork | exadataInfrastructures | Deletes the specified VM cluster network |
| GetVmClusterNetwork | exadataInfrastructures | Gets information about the specified VM cluster network |
| UpdateVmClusterNetwork | exadataInfrastructures | Updates the specified VM cluster network |
| DownloadVmClusterNetworkConfigFile | exadataInfrastructures | Downloads the configuration file for the specified VM cluster network |
| ResizeVmClusterNetwork | exadataInfrastructures | Adds or removes Db server network nodes to extend or shrink the existing VM cluster network |
| ValidateVmClusterNetwork | exadataInfrastructures | Validates the specified VM cluster network |
| ListExadbVmClusters | exadbVmClusters | Gets a list of the Exadata VM clusters on Exascale Infrastructure in the specified compartment |
| CreateExadbVmCluster | exadbVmClusters | Creates an Exadata VM cluster on Exascale Infrastructure  |
| DeleteExadbVmCluster | exadbVmClusters | Deletes the specified Exadata VM cluster on Exascale Infrastructure |
| GetExadbVmCluster | exadbVmClusters | Gets information about the specified Exadata VM cluster on Exascale Infrastructure |
| UpdateExadbVmCluster | exadbVmClusters | Updates the specified Exadata VM cluster on Exascale Infrastructure |
| ChangeExadbVmClusterCompartment | exadbVmClusters | Moves a Exadata VM cluster on Exascale Infrastructure and its dependent resources to another compartment |
| ChangeExadbVmClusterSubscription | exadbVmClusters | Associate a Exadata VM cluster on Exascale Infrastructure with a different subscription |
| RemoveVirtualMachineFromExadbVmCluster | exadbVmClusters | Remove Virtual Machines from the Exadata VM cluster on Exascale Infrastructure |
| ListExadbVmClusterUpdateHistoryEntries | exadbVmClusters | Gets the history of the maintenance update actions performed on the specified Exadata VM cluster on Exascale Infrastructure |
| GetExadbVmClusterUpdateHistoryEntry | exadbVmClusters | Gets the maintenance update history details for the specified update history entry |
| ListExadbVmClusterUpdates | exadbVmClusters | Lists the maintenance updates that can be applied to the specified Exadata VM cluster on Exascale Infrastructure |
| GetExadbVmClusterUpdate | exadbVmClusters | Gets information about a specified maintenance update package for a Exadata VM cluster on Exascale Infrastructure |
| ListExascaleDbStorageVaults | exascaleDbStorageVaults | Gets a list of the Exadata Database Storage Vaults in the specified compartment |
| CreateExascaleDbStorageVault | exascaleDbStorageVaults | Creates an Exadata Database Storage Vault  |
| DeleteExascaleDbStorageVault | exascaleDbStorageVaults | Deletes the specified Exadata Database Storage Vault |
| GetExascaleDbStorageVault | exascaleDbStorageVaults | Gets information about the specified Exadata Database Storage Vaults in the specified compartment |
| UpdateExascaleDbStorageVault | exascaleDbStorageVaults | Updates the specified Exadata Database Storage Vault |
| ChangeExascaleDbStorageVaultCompartment | exascaleDbStorageVaults | Moves a Exadata Database Storage Vault to another compartment |
| ChangeExascaleDbStorageVaultSubscription | exascaleDbStorageVaults | Associate a Exadata Database Storage Vault with a different subscription |
| ListExecutionActions | executionActions | Lists the execution action resources in the specified compartment |
| CreateExecutionAction | executionActions | Creates an execution action resource |
| DeleteExecutionAction | executionActions | Deletes the execution action |
| GetExecutionAction | executionActions | Gets information about the specified execution action |
| UpdateExecutionAction | executionActions | Updates the execution action resource |
| MoveExecutionActionMember | executionActions | Moves an execution action member to this execution action resource from another |
| ListExecutionWindows | executionWindows | Lists the execution window resources in the specified compartment |
| CreateExecutionWindow | executionWindows | Creates an execution window resource |
| DeleteExecutionWindow | executionWindows | Deletes the execution window |
| GetExecutionWindow | executionWindows | Gets information about the specified execution window |
| UpdateExecutionWindow | executionWindows | Updates the execution window resource |
| ReorderExecutionActions | executionWindows | Reorders the execution actions under this execution window resource |
| CreateExternalBackupJob | externalBackupJobs | Creates a new backup resource and returns the information the caller needs to back up an on-premises Oracle Database to Oracle Cloud Infrastructure |
| GetExternalBackupJob | externalBackupJobs | Gets information about the specified external backup job |
| CompleteExternalBackupJob | externalBackupJobs | Changes the status of the standalone backup resource to `ACTIVE` after the backup is created from the on-premises database and placed in Oracle Cloud Infrastructure Object Storage |
| ListExternalContainerDatabases | externalcontainerdatabases | Gets a list of the external container databases in the specified compartment |
| CreateExternalContainerDatabase | externalcontainerdatabases | Creates a new external container database resource |
| DeleteExternalContainerDatabase | externalcontainerdatabases | Deletes the [external container database](#/en/database/latest/datatypes/CreateExternalContainerDatabaseDetails) resource |
| GetExternalContainerDatabase | externalcontainerdatabases | Gets information about the specified external container database |
| UpdateExternalContainerDatabase | externalcontainerdatabases | Updates the properties of an [ExternalContainerDatabase](#/en/database/latest/datatypes/CreateExternalContainerDatabaseDetails) resource, such as the display name |
| ChangeExternalContainerDatabaseCompartment | externalcontainerdatabases | Move the [external container database](#/en/database/latest/datatypes/CreateExternalContainerDatabaseDetails) and its dependent resources to the specified compartment |
| DisableExternalContainerDatabaseDatabaseManagement | externalcontainerdatabases | Disable Database Management service for the external container database |
| DisableExternalContainerDatabaseStackMonitoring | externalcontainerdatabases | Disable Stack Monitoring for the external container database |
| EnableExternalContainerDatabaseDatabaseManagement | externalcontainerdatabases | Enables Database Management Service for the external container database |
| EnableExternalContainerDatabaseStackMonitoring | externalcontainerdatabases | Enable Stack Monitoring for the external container database |
| ScanExternalContainerDatabasePluggableDatabases | externalcontainerdatabases | Scans for pluggable databases in the specified external container database |
| ListExternalDatabaseConnectors | externaldatabaseconnectors | Gets a list of the external database connectors in the specified compartment |
| CreateExternalDatabaseConnector | externaldatabaseconnectors | Creates a new external database connector |
| DeleteExternalDatabaseConnector | externaldatabaseconnectors | Deletes an external database connector |
| GetExternalDatabaseConnector | externaldatabaseconnectors | Gets information about the specified external database connector |
| UpdateExternalDatabaseConnector | externaldatabaseconnectors | Updates the properties of an external database connector, such as the display name |
| CheckExternalDatabaseConnectorConnectionStatus | externaldatabaseconnectors | Check the status of the external database connection specified in this connector |
| ListExternalNonContainerDatabases | externalnoncontainerdatabases | Gets a list of the ExternalNonContainerDatabases in the specified compartment |
| CreateExternalNonContainerDatabase | externalnoncontainerdatabases | Creates a new ExternalNonContainerDatabase resource  |
| DeleteExternalNonContainerDatabase | externalnoncontainerdatabases | Deletes the Oracle Cloud Infrastructure resource representing an external non-container database |
| GetExternalNonContainerDatabase | externalnoncontainerdatabases | Gets information about a specific external non-container database |
| UpdateExternalNonContainerDatabase | externalnoncontainerdatabases | Updates the properties of an external non-container database, such as the display name |
| ChangeExternalNonContainerDatabaseCompartment | externalnoncontainerdatabases | Move the external non-container database and its dependent resources to the specified compartment |
| DisableExternalNonContainerDatabaseDatabaseManagement | externalnoncontainerdatabases | Disable Database Management Service for the external non-container database |
| DisableExternalNonContainerDatabaseOperationsInsights | externalnoncontainerdatabases | Disable Operations Insights for the external non-container database |
| DisableExternalNonContainerDatabaseStackMonitoring | externalnoncontainerdatabases | Disable Stack Monitoring for the external non-container database |
| EnableExternalNonContainerDatabaseDatabaseManagement | externalnoncontainerdatabases | Enable Database Management Service for the external non-container database |
| EnableExternalNonContainerDatabaseOperationsInsights | externalnoncontainerdatabases | Enable Operations Insights for the external non-container database |
| EnableExternalNonContainerDatabaseStackMonitoring | externalnoncontainerdatabases | Enable Stack Monitoring for the external non-container database |
| ListExternalPluggableDatabases | externalpluggabledatabases | Gets a list of the [ExternalPluggableDatabase](#/en/database/latest/datatypes/CreateExternalPluggableDatabaseDetails) resources in the specified compartment |
| CreateExternalPluggableDatabase | externalpluggabledatabases | Registers a new [ExternalPluggableDatabase](#/en/database/latest/datatypes/CreateExternalPluggableDatabaseDetails) resource |
| DeleteExternalPluggableDatabase | externalpluggabledatabases | Deletes the [external pluggable database](#/en/database/latest/datatypes/CreateExternalPluggableDatabaseDetails) |
| GetExternalPluggableDatabase | externalpluggabledatabases | Gets information about a specific [external pluggable database](#/en/database/latest/datatypes/CreateExternalPluggableDatabaseDetails) resource |
| UpdateExternalPluggableDatabase | externalpluggabledatabases | Updates the properties of an [external pluggable database](#/en/database/latest/datatypes/CreateExternalPluggableDatabaseDetails) resource, such as the display name |
| ChangeExternalPluggableDatabaseCompartment | externalpluggabledatabases | Move the [external pluggable database](#/en/database/latest/datatypes/CreateExternalPluggableDatabaseDetails) and its dependent resources to the specified compartment |
| DisableExternalPluggableDatabaseDatabaseManagement | externalpluggabledatabases | Disable Database Management Service for the external pluggable database |
| DisableExternalPluggableDatabaseOperationsInsights | externalpluggabledatabases | Disable Operations Insights for the external pluggable database |
| DisableExternalPluggableDatabaseStackMonitoring | externalpluggabledatabases | Disable Stack Monitoring for the external pluggable database |
| EnableExternalPluggableDatabaseDatabaseManagement | externalpluggabledatabases | Enable Database Management Service for the external pluggable database |
| EnableExternalPluggableDatabaseOperationsInsights | externalpluggabledatabases | Enable Operations Insights for the external pluggable database |
| EnableExternalPluggableDatabaseStackMonitoring | externalpluggabledatabases | Enable Stack Monitoring for the external pluggable database |
| ListGiVersions | giVersions | Gets a list of supported GI versions |
| ListGiVersionMinorVersions | giVersions | Gets a list of supported Oracle Grid Infrastructure minor versions for the given major version and shape family |
| ListKeyStores | keyStores | Gets a list of key stores in the specified compartment |
| CreateKeyStore | keyStores | Creates a Key Store |
| DeleteKeyStore | keyStores | Deletes a key store |
| GetKeyStore | keyStores | Gets information about the specified key store |
| UpdateKeyStore | keyStores | Edit the key store |
| ChangeKeyStoreCompartment | keyStores | Move the key store resource to the specified compartment |
| ListMaintenanceRunHistory | maintenanceRunHistory | Gets a list of the maintenance run histories in the specified compartment |
| GetMaintenanceRunHistory | maintenanceRunHistory | Gets information about the specified maintenance run history |
| ListMaintenanceRuns | maintenanceRuns | Gets a list of the maintenance runs in the specified compartment |
| CreateMaintenanceRun | maintenanceRuns | Creates a maintenance run with one of the following: 1 |
| GetMaintenanceRun | maintenanceRuns | Gets information about the specified maintenance run |
| UpdateMaintenanceRun | maintenanceRuns | Updates the properties of a maintenance run, such as the state of a maintenance run |
| ListOneoffPatches | oneoffPatches | Lists one-off patches in the specified compartment |
| CreateOneoffPatch | oneoffPatches | Creates one-off patch for specified database version to download |
| DeleteOneoffPatch | oneoffPatches | Deletes a one-off patch |
| GetOneoffPatch | oneoffPatches | Gets information about the specified one-off patch |
| UpdateOneoffPatch | oneoffPatches | Updates the properties of the specified one-off patch |
| ChangeOneoffPatchCompartment | oneoffPatches | Move the one-off patch to the specified compartment |
| DownloadOneoffPatch | oneoffPatches | Download one-off patch |
| ListPluggableDatabases | pluggableDatabases | Gets a list of the pluggable databases in a database or compartment |
| CreatePluggableDatabase | pluggableDatabases | Creates and starts a pluggable database in the specified container database |
| DeletePluggableDatabase | pluggableDatabases | Deletes the specified pluggable database |
| GetPluggableDatabase | pluggableDatabases | Gets information about the specified pluggable database |
| UpdatePluggableDatabase | pluggableDatabases | Updates the specified pluggable database |
| ConvertToRegularPluggableDatabase | pluggableDatabases | Converts a Refreshable clone to Regular pluggable database (PDB) |
| RefreshPluggableDatabase | pluggableDatabases | Refreshes a pluggable database (PDB) Refreshable clone |
| StartPluggableDatabase | pluggableDatabases | Starts a stopped pluggable database |
| StopPluggableDatabase | pluggableDatabases | Stops a pluggable database |
| GetResourcePrincipalToken | resourcePrincipalToken | Gets a resource principal intermediate token that contains mapping information between the instance prinicpal and resource |
| ListParamsForActionType | scheduledActionParams | List all the action params and their possible values for a given action type  |
| ListScheduledActions | scheduledActions | Lists the Scheduled Action resources in the specified compartment |
| CreateScheduledAction | scheduledActions | Creates a Scheduled Action resource |
| DeleteScheduledAction | scheduledActions | Deletes the scheduled action |
| GetScheduledAction | scheduledActions | Gets information about the specified Scheduled Action |
| UpdateScheduledAction | scheduledActions | Updates the Scheduled Action resource |
| ListSchedulingPlans | schedulingPlans | Lists the Scheduling Plan resources in the specified compartment |
| CreateSchedulingPlan | schedulingPlans | Creates a Scheduling Plan resource |
| DeleteSchedulingPlan | schedulingPlans | Deletes the scheduling plan |
| GetSchedulingPlan | schedulingPlans | Gets information about the specified Scheduling Plan |
| ChangeSchedulingPlanCompartment | schedulingPlans | Moves an scheduling plan resource to another compartment |
| ReorderScheduledActions | schedulingPlans | Re-order the scheduled actions under this scheduling plan resource |
| ListSchedulingPolicies | schedulingPolicies | Lists the Scheduling Policy resources in the specified compartment |
| CreateSchedulingPolicy | schedulingPolicies | Creates a Scheduling Policy resource |
| DeleteSchedulingPolicy | schedulingPolicies | Deletes the scheduling policy |
| GetSchedulingPolicy | schedulingPolicies | Gets information about the specified Scheduling Policy |
| UpdateSchedulingPolicy | schedulingPolicies | Updates the Scheduling Policy resource |
| ChangeSchedulingPolicyCompartment | schedulingPolicies | Moves an scheduling policy resource to another compartment |
| ListRecommendedScheduledActions | schedulingPolicies | Returns a recommended Scheduled Actions configuration for a given resource, plan intent and scheduling policy |
| ListSchedulingWindows | schedulingPolicies | Lists the Scheduling Window resources in the specified compartment |
| CreateSchedulingWindow | schedulingPolicies | Creates a Scheduling Window resource |
| DeleteSchedulingWindow | schedulingPolicies | Deletes the scheduling window |
| GetSchedulingWindow | schedulingPolicies | Gets information about the specified Scheduling Window |
| UpdateSchedulingWindow | schedulingPolicies | Updates the Scheduling Window resource |
| ListSystemVersions | systemVersions | Gets a list of supported Exadata system versions for a given shape and GI version |
| ListVmClusters | vmClusters | Lists the VM clusters in the specified compartment |
| CreateVmCluster | vmClusters | Creates an Exadata Cloud@Customer VM cluster |
| DeleteVmCluster | vmClusters | Deletes the specified VM cluster |
| GetVmCluster | vmClusters | Gets information about the VM cluster |
| UpdateVmCluster | vmClusters | Updates the specified VM cluster |
| AddVirtualMachineToVmCluster | vmClusters | Add Virtual Machines to the VM cluster |
| ChangeVmClusterCompartment | vmClusters | Moves a VM cluster and its dependent resources to another compartment |
| RemoveVirtualMachineFromVmCluster | vmClusters | Remove Virtual Machines from the VM cluster |
| ListVmClusterPatchHistoryEntries | vmClusters | Gets the history of the patch actions performed on the specified VM cluster in an Exadata Cloud@Customer system |
| GetVmClusterPatchHistoryEntry | vmClusters | Gets the patch history details for the specified patch history entry |
| ListVmClusterPatches | vmClusters | Lists the patches applicable to the specified VM cluster in an Exadata Cloud@Customer system |
| GetVmClusterPatch | vmClusters | Gets information about a specified patch package |
| ListVmClusterUpdateHistoryEntries | vmClusters | Gets the history of the maintenance update actions performed on the specified VM cluster |
| GetVmClusterUpdateHistoryEntry | vmClusters | Gets the maintenance update history details for the specified update history entry |
| ListVmClusterUpdates | vmClusters | Lists the maintenance updates that can be applied to the specified VM cluster |
| GetVmClusterUpdate | vmClusters | Gets information about a specified maintenance update package for a VM cluster |


⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.

