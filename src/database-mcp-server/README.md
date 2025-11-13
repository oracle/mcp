# OCI Database MCP Server

## Overview

This server provides tools to interact with the OCI Database service.

## Running the server

```sh
uv run oracle.database-mcp-server
```

## Tools

| Tool Name | Description                                                                  |
| --- |------------------------------------------------------------------------------|
| list_application_vips | Get application virtual IP (VIP) addresses on a cloud VM cluster             |
| list_autonomous_container_database_dataguard_associations | List Autonomous Data Guard associations for an Autonomous Container Database |
| list_autonomous_container_database_versions | List supported Autonomous Container Database versions                        |
| list_autonomous_container_databases | List Autonomous Container Databases in a compartment                         |
| list_autonomous_database_backups | List Autonomous Database backups by database ID or compartment               |
| list_autonomous_database_character_sets | List supported character sets for Autonomous Databases                       |
| list_autonomous_database_clones | List clones for a specific Autonomous Database                               |
| list_autonomous_database_dataguard_associations | List Autonomous Data Guard associations for an Autonomous Database           |
| list_autonomous_database_peers | List peers for a specific Autonomous Database                                |
| list_autonomous_database_refreshable_clones | List refreshable clones for a specific Autonomous Database                   |
| list_autonomous_database_software_images | List Autonomous Database Software Images in a compartment                    |
| list_autonomous_databases | List Autonomous Databases in a compartment                                   |
| list_autonomous_db_preview_versions | List supported preview versions for Autonomous Databases                     |
| list_autonomous_db_versions | List supported versions for Autonomous Databases                             |
| list_autonomous_virtual_machines | List Autonomous Virtual Machines in a specified cluster and compartment      |
| list_autonomous_vm_clusters | List Exadata Cloud@Customer Autonomous VM clusters in a compartment          |
| list_backup_destination | List backup destinations in a compartment                                    |
| list_backups | List database backups by database ID or compartment                          |
| list_cloud_autonomous_vm_clusters | List Autonomous Exadata VM clusters in the Oracle cloud                      |
| list_cloud_exadata_infrastructures | List cloud Exadata infrastructure resources in a compartment                 |
| list_cloud_vm_cluster_updates | List maintenance updates for a specific cloud VM cluster                     |
| list_cloud_vm_clusters | List cloud VM clusters in a compartment                                      |
| list_console_connections | List console connections for a database node                                 |
| list_console_histories | List console histories for a database node                                   |
| list_container_database_patches | List patches applicable to a container database                              |
| list_data_guard_associations | List Data Guard associations for a database                                  |
| list_database_software_images | List database software images in a compartment                               |
| list_databases | List databases in a specified Database Home                                  |
| list_db_home_patch_history_entries | List patch history for a Database Home                                       |
| list_db_home_patches | List patches applicable to a Database Home                                   |
| list_db_homes | List Database Homes in a DB system and compartment                           |
| list_db_nodes | List database nodes in a DB system and compartment                           |
| list_db_servers | List Exadata DB servers for an Exadata infrastructure                        |
| list_db_system_compute_performances | Get a list of expected compute performance for a VM DB system                |
| list_db_system_patches | List patches applicable to a DB system                                       |
| list_db_system_shapes | Get a list of shapes available for launching a new DB system                 |
| list_db_system_storage_performances | Get a list of expected storage performance for a VM DB system                |
| list_db_systems | List DB systems in a compartment                                             |
| list_db_versions | Get a list of supported Oracle Database versions                             |
| list_exadata_infrastructures | List Exadata Cloud@Customer infrastructure resources in a compartment        |
| list_exadb_vm_cluster_updates | List maintenance updates for an Exadata VM cluster on Exascale               |
| list_exadb_vm_clusters | List Exadata VM clusters on Exascale Infrastructure in a compartment         |
| list_exascale_db_storage_vaults | List Exadata Database Storage Vaults in a compartment                        |
| list_execution_actions | List execution action resources in a compartment                             |
| list_execution_windows | List execution window resources in a compartment                             |
| list_external_container_databases | List external container databases in a compartment                           |
| list_external_database_connectors | List external database connectors in a compartment                           |
| list_external_non_container_databases | List external non-container databases in a compartment                       |
| list_external_pluggable_databases | List external pluggable databases in a compartment                           |
| list_flex_components | Get a list of flex components available for launching a new DB system        |
| list_gi_version_minor_versions | Get a list of supported Grid Infrastructure minor versions                   |
| list_gi_versions | Get a list of supported Grid Infrastructure (GI) versions                    |
| list_key_stores | Get a list of key stores in the specified compartment                        |
| list_maintenance_run_history | Get a list of maintenance run histories in a compartment                     |
| list_maintenance_runs | Get a list of maintenance runs in a compartment                              |
| list_oneoff_patches | List one-off patches in a compartment                                        |
| list_pluggable_databases | Get a list of pluggable databases in a database or compartment               |
| list_scheduled_actions | List Scheduled Action resources in a compartment                             |
| list_scheduling_plans | List Scheduling Plan resources in a compartment                              |
| list_scheduling_policies | List Scheduling Policy resources in a compartment                            |
| list_scheduling_windows | List Scheduling Window resources in a compartment                            |
| list_system_versions | Get a list of supported Exadata system versions                              |
| list_vm_cluster_networks | Get a list of VM cluster networks in a compartment                           |
| list_vm_cluster_patches | List patches applicable to a VM cluster                                      |
| list_vm_cluster_updates | List maintenance updates for a VM cluster                                    |
| list_vm_clusters | List VM clusters in a compartment                                            |
| resource_pool_shapes | List available resource pool shapes                                          |
| create_pluggable_database | Create and start a pluggable database                                        |
| create_pluggable_database_from_local_clone | Create a pluggable database from a local clone                               |
| create_pluggable_database_from_remote_clone | Create a pluggable database by cloning from a remote source CDB              |
| create_pluggable_database_from_relocate | Relocate (move) a pluggable database from a source CDB into the target CDB   |
| delete_pluggable_database | Delete a specific pluggable database                                         |
| get_pluggable_database | Get information about a specific pluggable database                          |
| update_pluggable_database | Update a specific pluggable database                                         |
| get_compartment_by_name_tool | Return a compartment matching the provided name                              |
| list_subscribed_regions_tool | Return a list of all regions the customer (tenancy) is subscribed to         |
| get_application_vip | Gets information about a specified application virtual IP (VIP) address. |
| get_autonomous_container_database | Gets information about the specified Autonomous Container Database. |
| get_autonomous_container_database_dataguard_association | Gets an Autonomous Container Database enabled with Autonomous Data Guard associated with the specified Autonomous Container Database. |
| get_autonomous_container_database_resource_usage | Get resource usage details for the specified Autonomous Container Database. |
| get_autonomous_database | Gets the details of the specified Autonomous Database. |
| get_autonomous_database_backup | Gets information about the specified Autonomous Database backup. |
| get_autonomous_database_dataguard_association | Gets an Autonomous Data Guard-enabled database associated with the specified Autonomous Database. |
| get_autonomous_database_regional_wallet | Gets the Autonomous Database regional wallet details. |
| get_autonomous_database_software_image | Gets information about the specified Autonomous Database Software Image. |
| get_autonomous_database_wallet | Gets the wallet details for the specified Autonomous Database. |
| get_autonomous_exadata_infrastructure | **Deprecated.** Use the :func:`get_cloud_exadata_infrastructure` operation to get details of an Exadata Infrastructure resource and the :func:`get_cloud_autonomous_vm_cluster` operation to get details of an Autonomous Exadata VM cluster. |
| get_autonomous_patch | Gets information about a specific autonomous patch. |
| get_autonomous_virtual_machine | Gets the details of specific Autonomous Virtual Machine. |
| get_autonomous_vm_cluster | Gets information about the specified Autonomous VM cluster for an Exadata Cloud@Customer system. To get information about an Autonomous VM Cluster in the Oracle cloud, see :func:`get_cloud_autonomous_vm_cluster`. |
| get_autonomous_vm_cluster_resource_usage | Get the resource usage details for the specified Autonomous Exadata VM cluster. |
| get_backup | Gets information about the specified backup. |
| get_backup_destination | Gets information about the specified backup destination in an Exadata Cloud@Customer system. |
| get_cloud_autonomous_vm_cluster | Gets information about the specified Autonomous Exadata VM cluster in the Oracle cloud. For Exadata Cloud@Custustomer systems, see :func:`get_autonomous_vm_cluster`. |
| get_cloud_autonomous_vm_cluster_resource_usage | Get the resource usage details for the specified Cloud Autonomous Exadata VM cluster. |
| get_cloud_exadata_infrastructure | Gets information about the specified cloud Exadata infrastructure resource. Applies to Exadata Cloud Service instances and Autonomous Database on dedicated Exadata infrastructure only. |
| get_cloud_exadata_infrastructure_unallocated_resources | Gets unallocated resources information for the specified Cloud Exadata infrastructure. |
| get_cloud_vm_cluster | Gets information about the specified cloud VM cluster. Applies to Exadata Cloud Service instances and Autonomous Database on dedicated Exadata infrastructure only. |
| get_cloud_vm_cluster_iorm_config | Gets the IORM configuration for the specified cloud VM cluster in an Exadata Cloud Service instance. |
| get_cloud_vm_cluster_update | Gets information about a specified maintenance update package for a cloud VM cluster. Applies to Exadata Cloud Service instances only. |
| get_cloud_vm_cluster_update_history_entry | Gets the maintenance update history details for the specified update history entry. Applies to Exadata Cloud Service instances only. |
| get_console_connection | Gets the specified database node console connection's information. |
| get_console_history | Gets information about the specified database node console history. |
| get_console_history_content | Retrieves the specified database node console history contents upto a megabyte. |
| get_data_guard_association | Gets the specified Data Guard association's configuration information. |
| get_database | Gets information about the specified database. |
| get_database_software_image | Gets information about the specified database software image. |
| get_database_upgrade_history_entry | gets the upgrade history for a specified database. |
| get_db_home | Gets information about the specified Database Home. |
| get_db_home_patch | Gets information about a specified patch package. |
| get_db_home_patch_history_entry | Gets the patch history details for the specified patchHistoryEntryId |
| get_db_node | Gets information about the specified database node. |
| get_db_server | Gets information about the Exadata Db server. |
| get_db_system | Gets information about the specified DB system. |
| get_db_system_patch | Gets information the specified patch. |
| get_db_system_patch_history_entry | Gets the details of the specified patch operation on the specified DB system. |
| get_db_system_upgrade_history_entry | Gets the details of the specified operating system upgrade operation for the specified DB system. |
| get_exadata_infrastructure | Gets information about the specified Exadata infrastructure. Applies to Exadata Cloud@Customer instances only. |
| get_exadata_infrastructure_ocpus | Gets details of the available and consumed OCPUs for the specified Autonomous Exadata Infrastructure resource. |
| get_exadata_infrastructure_un_allocated_resources | Gets un allocated resources information for the specified Exadata infrastructure. Applies to Exadata Cloud@Customer instances only. |
| get_exadata_iorm_config | Gets the IORM configuration settings for the specified cloud Exadata DB system. |
| get_exadb_vm_cluster | Gets information about the specified Exadata VM cluster on Exascale Infrastructure. Applies to Exadata Database Service on Exascale Infrastructure only. |
| get_exadb_vm_cluster_update | Gets information about a specified maintenance update package for a Exadata VM cluster on Exascale Infrastructure. |
| get_exadb_vm_cluster_update_history_entry | Gets the maintenance update history details for the specified update history entry. |
| get_exascale_db_storage_vault | Gets information about the specified Exadata Database Storage Vaults in the specified compartment. |
| get_execution_action | Gets information about the specified execution action. |
| get_execution_window | Gets information about the specified execution window. |
| get_external_backup_job | Gets information about the specified external backup job. |
| get_external_container_database | Gets information about the specified external container database. |
| get_external_database_connector | Gets information about the specified external database connector. |
| get_external_non_container_database | Gets information about a specific external non-container database. |
| get_external_pluggable_database | Gets information about a specific |
| get_infrastructure_target_versions | Gets details of the Exadata Infrastructure target system software versions that can be applied to the specified infrastructure resource for maintenance updates. |
| get_key_store | Gets information about the specified key store. |
| get_maintenance_run | Gets information about the specified maintenance run. |
| get_maintenance_run_history | Gets information about the specified maintenance run history. |
| get_oneoff_patch | Gets information about the specified one-off patch. |
| get_pdb_conversion_history_entry | Gets the details of operations performed to convert the specified database from non-container (non-CDB) to pluggable (PDB). |
| get_pluggable_database | Gets information about the specified pluggable database. |
| get_scheduled_action | Gets information about the specified Scheduled Action. |
| get_scheduling_plan | Gets information about the specified Scheduling Plan. |
| get_scheduling_policy | Gets information about the specified Scheduling Policy. |
| get_scheduling_window | Gets information about the specified Scheduling Window. |
| get_vm_cluster | Gets information about the VM cluster. Applies to Exadata Cloud@Customer instances only. |
| get_vm_cluster_network | Gets information about the specified VM cluster network. Applies to Exadata Cloud@Customer instances only. |
| get_vm_cluster_patch | Gets information about a specified patch package. |
| get_vm_cluster_patch_history_entry | Gets the patch history details for the specified patch history entry. |
| get_vm_cluster_update | Gets information about a specified maintenance update package for a VM cluster. Applies to Exadata Cloud@Customer instances only. |
| get_vm_cluster_update_history_entry | Gets the maintenance update history details for the specified update history entry. Applies to Exadata Cloud@Customer instances only. |



⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.

