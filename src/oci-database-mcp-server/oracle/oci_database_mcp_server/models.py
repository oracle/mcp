from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import oci
from pydantic import BaseModel, Field


class OCIBaseModel(BaseModel):
    """Base model that supports conversion from OCI SDK models."""

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def from_oci(cls, sdk_obj):
        """Convert an OCI SDK model into this Pydantic model."""
        return cls(**oci.util.to_dict(sdk_obj))


class PluggableDatabase(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.PluggableDatabase."""

    compartment_id: Optional[str] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this PluggableDatabase. The `OCID`__ of the compartment. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    )
    connection_strings: Optional[Any] = Field(None, description="")
    container_database_id: Optional[str] = Field(
        None,
        description="**[Required]** Gets the container_database_id of this PluggableDatabase. The `OCID`__ of the CDB. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    )
    defined_tags: Optional[dict] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm",
    )
    freeform_tags: Optional[dict] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}` __ https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm',
    )
    id: Optional[str] = Field(
        None,
        description="**[Required]** Gets the id of this PluggableDatabase. The `OCID`__ of the pluggable database. __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    )
    is_restricted: Optional[bool] = Field(
        None,
        description="The restricted mode of the pluggable database. If a pluggable database is opened in restricted mode, the user needs both create a session and have restricted session privileges to connect to it.",
    )
    kms_key_id: Optional[str] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    kms_key_version_id: Optional[str] = Field(
        None,
        description="The OCID of the key container version that is used in database transparent data encryption (TDE) operations KMS Key can have multiple key versions. If none is specified, the current key version (latest) of the Key Id is used for the operation. Autonomous Database Serverless does not use key versions, hence is not applicable for Autonomous Database Serverless instances.",
    )
    lifecycle_details: Optional[str] = Field(
        None, description="Detailed message for the lifecycle state."
    )
    lifecycle_state: Optional[str] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this PluggableDatabase. The current state of the pluggable database. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "TERMINATING", "TERMINATED", "UPDATING", "FAILED", "RELOCATING", "RELOCATED", "REFRESHING", "RESTORE_IN_PROGRESS", "RESTORE_FAILED", "BACKUP_IN_PROGRESS", "DISABLED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    open_mode: Optional[str] = Field(
        None,
        description='**[Required]** Gets the open_mode of this PluggableDatabase. **Deprecated.** Use :func:`pluggable_database_node_level_details` for OpenMode details. The mode that pluggable database is in. Open mode can only be changed to READ_ONLY or MIGRATE directly from the backend (within the Oracle Database software). Allowed values for this property are: "READ_ONLY", "READ_WRITE", "MOUNTED", "MIGRATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    pdb_name: Optional[str] = Field(
        None,
        description="**[Required]** Gets the pdb_name of this PluggableDatabase. The name for the pluggable database (PDB). The name is unique in the context of a :class:`Database`. The name must begin with an alphabetic character and can contain a maximum of thirty alphanumeric characters. Special characters are not permitted. The pluggable database name should not be same as the container database name.",
    )
    pdb_node_level_details: Optional[list[dict]] = Field(
        None,
        description='Pluggable Database Node Level Details. Example: [{"nodeName" : "node1", "openMode" : "READ_WRITE"}, {"nodeName" : "node2", "openMode" : "READ_ONLY"}]',
    )
    pluggable_database_management_config: Optional[dict] = Field(None, description="")
    refreshable_clone_config: Optional[dict] = Field(None, description="")
    time_created: Optional[datetime] = Field(
        None,
        description="**[Required]** Gets the time_created of this PluggableDatabase. The date and time the pluggable database was created.",
    )


def map_pluggabledatabase(
    o: oci.database.models.PluggableDatabase,
) -> PluggableDatabase | None:
    """Map oci.database.models.PluggableDatabase → PluggableDatabase Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return PluggableDatabase(**data)
    except Exception:
        return PluggableDatabase(
            compartment_id=getattr(o, "compartment_id", None),
            connection_strings=getattr(o, "connection_strings", None),
            container_database_id=getattr(o, "container_database_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_restricted=getattr(o, "is_restricted", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            kms_key_version_id=getattr(o, "kms_key_version_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            open_mode=getattr(o, "open_mode", None),
            pdb_name=getattr(o, "pdb_name", None),
            pdb_node_level_details=getattr(o, "pdb_node_level_details", None),
            pluggable_database_management_config=getattr(
                o, "pluggable_database_management_config", None
            ),
            refreshable_clone_config=getattr(o, "refreshable_clone_config", None),
            time_created=getattr(o, "time_created", None),
        )


class CreatePluggableDatabaseDetails(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.CreatePluggableDatabaseDetails."""

    container_database_admin_password: Optional[str] = Field(
        None,
        description="The DB system administrator password of the Container Database.",
    )
    container_database_id: Optional[str] = Field(
        None,
        description="**[Required]** Gets the container_database_id of this CreatePluggableDatabaseDetails. The `OCID`__ of the CDB __ https://docs.cloud.oracle.com/Content/General/Concepts/identifiers.htm",
    )
    defined_tags: Optional[str] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm",
    )
    freeform_tags: Optional[str] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}` __ https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm',
    )
    pdb_admin_password: Optional[str] = Field(
        None,
        description="A strong password for PDB Admin. The password must be at least nine characters and contain at least two uppercase, two lowercase, two numbers, and two special characters. The special characters must be _, \\#, or -.",
    )
    pdb_creation_type_details: Optional[dict] = Field(None, description="")
    pdb_name: Optional[str] = Field(
        None,
        description="**[Required]** Gets the pdb_name of this CreatePluggableDatabaseDetails. The name for the pluggable database (PDB). The name is unique in the context of a :class:`Database`. The name must begin with an alphabetic character and can contain a maximum of thirty alphanumeric characters. Special characters are not permitted. The pluggable database name should not be same as the container database name.",
    )
    should_create_pdb_backup: Optional[bool] = Field(
        None,
        description="Indicates whether to take Pluggable Database Backup after the operation.",
    )
    should_pdb_admin_account_be_locked: Optional[bool] = Field(
        None,
        description="The locked mode of the pluggable database admin account. If false, the user needs to provide the PDB Admin Password to connect to it. If true, the pluggable database will be locked and user cannot login to it.",
    )
    tde_wallet_password: Optional[str] = Field(
        None, description="The existing TDE wallet password of the CDB."
    )


def map_createpluggabledatabasedetails(
    o: oci.database.models.CreatePluggableDatabaseDetails,
) -> CreatePluggableDatabaseDetails | None:
    """Map oci.database.models.CreatePluggableDatabaseDetails → CreatePluggableDatabaseDetails Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return CreatePluggableDatabaseDetails(**data)
    except Exception:
        return CreatePluggableDatabaseDetails(
            container_database_admin_password=getattr(
                o, "container_database_admin_password", None
            ),
            container_database_id=getattr(o, "container_database_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            pdb_admin_password=getattr(o, "pdb_admin_password", None),
            pdb_creation_type_details=getattr(o, "pdb_creation_type_details", None),
            pdb_name=getattr(o, "pdb_name", None),
            should_create_pdb_backup=getattr(o, "should_create_pdb_backup", None),
            should_pdb_admin_account_be_locked=getattr(
                o, "should_pdb_admin_account_be_locked", None
            ),
            tde_wallet_password=getattr(o, "tde_wallet_password", None),
        )


class UpdatePluggableDatabaseDetails(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.UpdatePluggableDatabaseDetails."""

    defined_tags: Optional[str] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. __ https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm",
    )
    freeform_tags: Optional[str] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}` __ https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm',
    )


def map_updatepluggabledatabasedetails(
    o: oci.database.models.UpdatePluggableDatabaseDetails,
) -> UpdatePluggableDatabaseDetails | None:
    """Map oci.database.models.UpdatePluggableDatabaseDetails → UpdatePluggableDatabaseDetails Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return UpdatePluggableDatabaseDetails(**data)
    except Exception:
        return UpdatePluggableDatabaseDetails(
            defined_tags=getattr(o, "defined_tags", None),
            freeform_tags=getattr(o, "freeform_tags", None),
        )


class ApplicationVipSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ApplicationVipSummary."""

    cloud_vm_cluster_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cloud_vm_cluster_id of this ApplicationVipSummary. The `OCID`__ of the cloud VM cluster associated with the application virtual IP (VIP) address.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    hostname_label: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the hostname_label of this ApplicationVipSummary. The hostname of the application virtual IP (VIP) address.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ApplicationVipSummary. The `OCID`__ of the application virtual IP (VIP) address.",
    )
    ip_address: Optional[Any] = Field(
        None,
        description="The application virtual IP (VIP) address.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state of the application virtual IP (VIP) address.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ApplicationVipSummary. The current lifecycle state of the application virtual IP (VIP) address. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the subnet associated with the application virtual IP (VIP) address.",
    )
    time_assigned: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_assigned of this ApplicationVipSummary. The date and time when the create operation for the application virtual IP (VIP) address completed.",
    )


def map_applicationvipsummary(
    o: oci.database.models.ApplicationVipSummary,
) -> ApplicationVipSummary | None:
    """Map oci.database.models.ApplicationVipSummary → ApplicationVipSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ApplicationVipSummary(**data)
    except Exception:
        return ApplicationVipSummary(
            cloud_vm_cluster_id=getattr(o, "cloud_vm_cluster_id", None),
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            hostname_label=getattr(o, "hostname_label", None),
            id=getattr(o, "id", None),
            ip_address=getattr(o, "ip_address", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            subnet_id=getattr(o, "subnet_id", None),
            time_assigned=getattr(o, "time_assigned", None),
        )


class AutonomousContainerDatabaseDataguardAssociation(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousContainerDatabaseDataguardAssociation."""

    apply_lag: Optional[Any] = Field(
        None,
        description="The lag time between updates to the primary Autonomous Container Database and application of the redo data on the standby Autonomous Container Database, as computed by the reporting database. Example: `9 seconds`",
    )
    apply_rate: Optional[Any] = Field(
        None,
        description="The rate at which redo logs are synchronized between the associated Autonomous Container Databases. Example: `180 Mb per second`",
    )
    autonomous_container_database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the autonomous_container_database_id of this AutonomousContainerDatabaseDataguardAssociation. The `OCID`__ of the Autonomous Container Database that has a relationship with the peer Autonomous Container Database. Used only by Autonomous Database on Dedicated Exadata Infrastructure.",
    )
    fast_start_fail_over_lag_limit_in_seconds: Optional[Any] = Field(
        None,
        description="The lag time for my preference based on data loss tolerance in seconds.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousContainerDatabaseDataguardAssociation. The OCID of the Autonomous Data Guard created for a given Autonomous Container Database.",
    )
    is_automatic_failover_enabled: Optional[Any] = Field(
        None,
        description="Indicates whether Automatic Failover is enabled for Autonomous Container Database Dataguard Association",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycleState, if available.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousContainerDatabaseDataguardAssociation. The current state of Autonomous Data Guard. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "ROLE_CHANGE_IN_PROGRESS", "TERMINATING", "TERMINATED", "FAILED", "UNAVAILABLE", "UPDATING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_autonomous_container_database_dataguard_association_id: Optional[Any] = Field(
        None,
        description="The OCID of the peer Autonomous Container Database-Autonomous Data Guard association.",
    )
    peer_autonomous_container_database_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the peer Autonomous Container Database.",
    )
    peer_lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the Autonomous Container Database. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "BACKUP_IN_PROGRESS", "RESTORING", "RESTORE_FAILED", "RESTARTING", "MAINTENANCE_IN_PROGRESS", "ROLE_CHANGE_IN_PROGRESS", "ENABLING_AUTONOMOUS_DATA_GUARD", "UNAVAILABLE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_role: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the peer_role of this AutonomousContainerDatabaseDataguardAssociation. The Data Guard role of the Autonomous Container Database or Autonomous Database, if Autonomous Data Guard is enabled. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", "BACKUP_COPY", "SNAPSHOT_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    protection_mode: Optional[Any] = Field(
        None,
        description="The protection mode of this Autonomous Data Guard association. For more information, see `Oracle Data Guard Protection Modes`__ in the Oracle Data Guard documentation. Allowed values for this property are: \"MAXIMUM_AVAILABILITY\", \"MAXIMUM_PERFORMANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    role: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the role of this AutonomousContainerDatabaseDataguardAssociation. The Data Guard role of the Autonomous Container Database or Autonomous Database, if Autonomous Data Guard is enabled. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", "BACKUP_COPY", "SNAPSHOT_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Autonomous DataGuard association was created.",
    )
    time_last_role_changed: Optional[Any] = Field(
        None,
        description="The date and time when the last role change action happened.",
    )
    time_last_synced: Optional[Any] = Field(
        None,
        description="The date and time of the last update to the apply lag, apply rate, and transport lag values.",
    )
    transport_lag: Optional[Any] = Field(
        None,
        description="The approximate number of seconds of redo data not yet available on the standby Autonomous Container Database, as computed by the reporting database. Example: `7 seconds`",
    )


def map_autonomouscontainerdatabasedataguardassociation(
    o: oci.database.models.AutonomousContainerDatabaseDataguardAssociation,
) -> AutonomousContainerDatabaseDataguardAssociation | None:
    """Map oci.database.models.AutonomousContainerDatabaseDataguardAssociation → AutonomousContainerDatabaseDataguardAssociation Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousContainerDatabaseDataguardAssociation(**data)
    except Exception:
        return AutonomousContainerDatabaseDataguardAssociation(
            apply_lag=getattr(o, "apply_lag", None),
            apply_rate=getattr(o, "apply_rate", None),
            autonomous_container_database_id=getattr(
                o, "autonomous_container_database_id", None
            ),
            fast_start_fail_over_lag_limit_in_seconds=getattr(
                o, "fast_start_fail_over_lag_limit_in_seconds", None
            ),
            id=getattr(o, "id", None),
            is_automatic_failover_enabled=getattr(
                o, "is_automatic_failover_enabled", None
            ),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            peer_autonomous_container_database_dataguard_association_id=getattr(
                o, "peer_autonomous_container_database_dataguard_association_id", None
            ),
            peer_autonomous_container_database_id=getattr(
                o, "peer_autonomous_container_database_id", None
            ),
            peer_lifecycle_state=getattr(o, "peer_lifecycle_state", None),
            peer_role=getattr(o, "peer_role", None),
            protection_mode=getattr(o, "protection_mode", None),
            role=getattr(o, "role", None),
            time_created=getattr(o, "time_created", None),
            time_last_role_changed=getattr(o, "time_last_role_changed", None),
            time_last_synced=getattr(o, "time_last_synced", None),
            transport_lag=getattr(o, "transport_lag", None),
        )


class AutonomousContainerDatabaseVersionSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousContainerDatabaseVersionSummary."""

    details: Optional[Any] = Field(
        None,
        description="A URL that points to a detailed description of the Autonomous Container Database version.",
    )
    supported_apps: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the supported_apps of this AutonomousContainerDatabaseVersionSummary. The list of applications supported for the given version.",
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this AutonomousContainerDatabaseVersionSummary. A valid Oracle Database version for provisioning an Autonomous Container Database.",
    )


def map_autonomouscontainerdatabaseversionsummary(
    o: oci.database.models.AutonomousContainerDatabaseVersionSummary,
) -> AutonomousContainerDatabaseVersionSummary | None:
    """Map oci.database.models.AutonomousContainerDatabaseVersionSummary → AutonomousContainerDatabaseVersionSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousContainerDatabaseVersionSummary(**data)
    except Exception:
        return AutonomousContainerDatabaseVersionSummary(
            details=getattr(o, "details", None),
            supported_apps=getattr(o, "supported_apps", None),
            version=getattr(o, "version", None),
        )


class AutonomousContainerDatabaseSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousContainerDatabaseSummary."""

    associated_backup_configuration_details: Optional[Any] = Field(
        None,
        description="A backup config object holds information about preferred backup destinations only. This object holds information about the associated backup destinations, such as secondary backup destinations created for local backups or remote replicated backups.",
    )
    autonomous_exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="**No longer used.** For Autonomous Database on dedicated Exadata infrastructure, the container database is created within a specified `cloudAutonomousVmCluster`.",
    )
    autonomous_vm_cluster_id: Optional[Any] = Field(
        None,
        description="The OCID of the Autonomous VM Cluster.",
    )
    availability_domain: Optional[Any] = Field(
        None,
        description="The availability domain of the Autonomous Container Database.",
    )
    available_cpus: Optional[float] = Field(
        None,
        description="Sum of CPUs available on the Autonomous VM Cluster + Sum of reclaimable CPUs available in the Autonomous Container Database.",
    )
    backup_config: Optional[Any] = Field(
        None,
        description="",
    )
    backup_destination_properties_list: Optional[Any] = Field(
        None,
        description="This list describes the backup destination properties associated with the Autonomous Container Database (ACD) 's preferred backup destination. The object at a given index is associated with the destination present at the same index in the backup destination details list of the ACD Backup Configuration.",
    )
    cloud_autonomous_vm_cluster_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the cloud Autonomous Exadata VM Cluster.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this AutonomousContainerDatabaseSummary. The OCID of the compartment.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Container Database. For Autonomous Database on Dedicated Exadata Infrastructure, the CPU type (ECPUs or OCPUs) is determined by the parent Autonomous Exadata VM Cluster's compute model. ECPU compute model is the recommended model and OCPU compute model is legacy. See `Compute Models in Autonomous Database on Dedicated Exadata Infrastructure`__ for more details. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    db_name: Optional[Any] = Field(
        None,
        description="The Database name for the Autonomous Container Database. The name must be unique within the Cloud Autonomous VM Cluster, starting with an alphabetic character, followed by 1 to 7 alphanumeric characters.",
    )
    db_split_threshold: Optional[Any] = Field(
        None,
        description="The CPU value beyond which an Autonomous Database will be opened across multiple nodes. The default value of this attribute is 16 for OCPUs and 64 for ECPUs.",
    )
    db_unique_name: Optional[Any] = Field(
        None,
        description="**Deprecated.** The `DB_UNIQUE_NAME` value is set by Oracle Cloud Infrastructure. Do not specify a value for this parameter. Specifying a value for this field will cause Terraform operations to fail.",
    )
    db_version: Optional[Any] = Field(
        None,
        description="Oracle Database version of the Autonomous Container Database.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this AutonomousContainerDatabaseSummary. The user-provided name for the Autonomous Container Database.",
    )
    distribution_affinity: Optional[Any] = Field(
        None,
        description="Determines whether an Autonomous Database must be opened across the maximum number of nodes or the least number of nodes. By default, Minimum nodes is selected. Allowed values for this property are: \"MINIMUM_DISTRIBUTION\", \"MAXIMUM_DISTRIBUTION\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    dst_file_version: Optional[Any] = Field(
        None,
        description="DST Time-Zone File version of the Autonomous Container Database.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousContainerDatabaseSummary. The OCID of the Autonomous Container Database.",
    )
    infrastructure_type: Optional[Any] = Field(
        None,
        description="The infrastructure type this resource belongs to. Allowed values for this property are: \"CLOUD\", \"CLOUD_AT_CUSTOMER\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    is_dst_file_update_enabled: Optional[Any] = Field(
        None,
        description="Indicates if an automatic DST Time Zone file update is enabled for the Autonomous Container Database. If enabled along with Release Update, patching will be done in a Non-Rolling manner.",
    )
    key_history_entry: Optional[Any] = Field(
        None,
        description="Key History Entry.",
    )
    key_store_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the key store of Oracle Vault.",
    )
    key_store_wallet_name: Optional[Any] = Field(
        None,
        description="The wallet name for Oracle Key Vault.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    kms_key_version_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container version that is used in database transparent data encryption (TDE) operations KMS Key can have multiple key versions. If none is specified, the current key version (latest) of the Key Id is used for the operation. Autonomous Database Serverless does not use key versions, hence is not applicable for Autonomous Database Serverless instances.",
    )
    largest_provisionable_autonomous_database_in_cpus: Optional[float] = Field(
        None,
        description="The largest Autonomous Database (CPU) that can be created in a new Autonomous Container Database.",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousContainerDatabaseSummary. The current state of the Autonomous Container Database. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "BACKUP_IN_PROGRESS", "RESTORING", "RESTORE_FAILED", "RESTARTING", "MAINTENANCE_IN_PROGRESS", "ROLE_CHANGE_IN_PROGRESS", "ENABLING_AUTONOMOUS_DATA_GUARD", "UNAVAILABLE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    list_one_off_patches: Optional[Any] = Field(
        None,
        description="List of One-Off patches that has been successfully applied to Autonomous Container Database",
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="",
    )
    memory_per_oracle_compute_unit_in_gbs: Optional[Any] = Field(
        None,
        description="The amount of memory (in GBs) enabled per ECPU or OCPU in the Autonomous VM Cluster.",
    )
    net_services_architecture: Optional[Any] = Field(
        None,
        description="Enabling SHARED server architecture enables a database server to allow many client processes to share very few server processes, thereby increasing the number of supported users. Allowed values for this property are: \"DEDICATED\", \"SHARED\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    patch_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last patch applied on the system.",
    )
    patch_model: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the patch_model of this AutonomousContainerDatabaseSummary. Database patch model preference. Allowed values for this property are: \"RELEASE_UPDATES\", \"RELEASE_UPDATE_REVISIONS\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    provisionable_cpus: Optional[Any] = Field(
        None,
        description="An array of CPU values that can be used to successfully provision a single Autonomous Database.",
    )
    provisioned_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs provisioned in an Autonomous Container Database.",
    )
    reclaimable_cpus: Optional[float] = Field(
        None,
        description="CPUs that continue to be included in the count of CPUs available to the Autonomous Container Database even after one of its Autonomous Database is terminated or scaled down. You can release them to the available CPUs at its parent Autonomous VM Cluster level by restarting the Autonomous Container Database.",
    )
    recovery_appliance_details: Optional[Any] = Field(
        None,
        description="",
    )
    reserved_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs reserved in an Autonomous Container Database.",
    )
    role: Optional[Any] = Field(
        None,
        description='The Data Guard role of the Autonomous Container Database or Autonomous Database, if Autonomous Data Guard is enabled. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", "BACKUP_COPY", "SNAPSHOT_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    service_level_agreement_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the service_level_agreement_type of this AutonomousContainerDatabaseSummary. The service level agreement type of the container database. The default is STANDARD. Allowed values for this property are: "STANDARD", "MISSION_CRITICAL", "AUTONOMOUS_DATAGUARD", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    standby_maintenance_buffer_in_days: Optional[Any] = Field(
        None,
        description="The scheduling detail for the quarterly maintenance window of the standby Autonomous Container Database. This value represents the number of days before scheduled maintenance of the primary database.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Autonomous Container Database was created.",
    )
    time_of_last_backup: Optional[Any] = Field(
        None,
        description="The timestamp of last successful backup. Here NULL value represents either there are no successful backups or backups are not configured for this Autonomous Container Database.",
    )
    time_snapshot_standby_revert: Optional[Any] = Field(
        None,
        description="The date and time the Autonomous Container Database will be reverted to Standby from Snapshot Standby.",
    )
    total_cpus: Optional[Any] = Field(
        None,
        description="The number of CPUs allocated to the Autonomous VM cluster.",
    )
    vault_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Oracle Cloud Infrastructure `vault`__. This parameter and `secretId` are required for Customer Managed Keys.",
    )
    version_preference: Optional[Any] = Field(
        None,
        description="The next maintenance version preference. Allowed values for this property are: \"NEXT_RELEASE_UPDATE\", \"LATEST_RELEASE_UPDATE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    vm_failover_reservation: Optional[Any] = Field(
        None,
        description="The percentage of CPUs reserved across nodes to support node failover. Allowed values are 0%, 25%, and 50%, with 50% being the default option.",
    )


def map_autonomouscontainerdatabasesummary(
    o: oci.database.models.AutonomousContainerDatabaseSummary,
) -> AutonomousContainerDatabaseSummary | None:
    """Map oci.database.models.AutonomousContainerDatabaseSummary → AutonomousContainerDatabaseSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousContainerDatabaseSummary(**data)
    except Exception:
        return AutonomousContainerDatabaseSummary(
            associated_backup_configuration_details=getattr(
                o, "associated_backup_configuration_details", None
            ),
            autonomous_exadata_infrastructure_id=getattr(
                o, "autonomous_exadata_infrastructure_id", None
            ),
            autonomous_vm_cluster_id=getattr(o, "autonomous_vm_cluster_id", None),
            availability_domain=getattr(o, "availability_domain", None),
            available_cpus=getattr(o, "available_cpus", None),
            backup_config=getattr(o, "backup_config", None),
            backup_destination_properties_list=getattr(
                o, "backup_destination_properties_list", None
            ),
            cloud_autonomous_vm_cluster_id=getattr(
                o, "cloud_autonomous_vm_cluster_id", None
            ),
            compartment_id=getattr(o, "compartment_id", None),
            compute_model=getattr(o, "compute_model", None),
            db_name=getattr(o, "db_name", None),
            db_split_threshold=getattr(o, "db_split_threshold", None),
            db_unique_name=getattr(o, "db_unique_name", None),
            db_version=getattr(o, "db_version", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            distribution_affinity=getattr(o, "distribution_affinity", None),
            dst_file_version=getattr(o, "dst_file_version", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            infrastructure_type=getattr(o, "infrastructure_type", None),
            is_dst_file_update_enabled=getattr(o, "is_dst_file_update_enabled", None),
            key_history_entry=getattr(o, "key_history_entry", None),
            key_store_id=getattr(o, "key_store_id", None),
            key_store_wallet_name=getattr(o, "key_store_wallet_name", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            kms_key_version_id=getattr(o, "kms_key_version_id", None),
            largest_provisionable_autonomous_database_in_cpus=getattr(
                o, "largest_provisionable_autonomous_database_in_cpus", None
            ),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            list_one_off_patches=getattr(o, "list_one_off_patches", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            memory_per_oracle_compute_unit_in_gbs=getattr(
                o, "memory_per_oracle_compute_unit_in_gbs", None
            ),
            net_services_architecture=getattr(o, "net_services_architecture", None),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            patch_id=getattr(o, "patch_id", None),
            patch_model=getattr(o, "patch_model", None),
            provisionable_cpus=getattr(o, "provisionable_cpus", None),
            provisioned_cpus=getattr(o, "provisioned_cpus", None),
            reclaimable_cpus=getattr(o, "reclaimable_cpus", None),
            recovery_appliance_details=getattr(o, "recovery_appliance_details", None),
            reserved_cpus=getattr(o, "reserved_cpus", None),
            role=getattr(o, "role", None),
            service_level_agreement_type=getattr(
                o, "service_level_agreement_type", None
            ),
            standby_maintenance_buffer_in_days=getattr(
                o, "standby_maintenance_buffer_in_days", None
            ),
            time_created=getattr(o, "time_created", None),
            time_of_last_backup=getattr(o, "time_of_last_backup", None),
            time_snapshot_standby_revert=getattr(
                o, "time_snapshot_standby_revert", None
            ),
            total_cpus=getattr(o, "total_cpus", None),
            vault_id=getattr(o, "vault_id", None),
            version_preference=getattr(o, "version_preference", None),
            vm_failover_reservation=getattr(o, "vm_failover_reservation", None),
        )


class AutonomousDatabaseBackupSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDatabaseBackupSummary."""

    autonomous_database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the autonomous_database_id of this AutonomousDatabaseBackupSummary. The `OCID`__ of the Autonomous Database.",
    )
    backup_destination_details: Optional[Any] = Field(
        None,
        description="",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this AutonomousDatabaseBackupSummary. The `OCID`__ of the compartment.",
    )
    database_size_in_tbs: Optional[float] = Field(
        None,
        description="The size of the database in terabytes at the time the backup was taken.",
    )
    db_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Database version for Autonomous Database.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this AutonomousDatabaseBackupSummary. The user-friendly name for the backup. The name does not have to be unique.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousDatabaseBackupSummary. The `OCID`__ of the Autonomous Database backup.",
    )
    is_automatic: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the is_automatic of this AutonomousDatabaseBackupSummary. Indicates whether the backup is user-initiated or automatic.",
    )
    is_restorable: Optional[Any] = Field(
        None,
        description="Indicates whether the backup can be used to restore the associated Autonomous Database.",
    )
    key_store_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the key store of Oracle Vault.",
    )
    key_store_wallet_name: Optional[Any] = Field(
        None,
        description="The wallet name for Oracle Key Vault.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    kms_key_version_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container version that is used in database transparent data encryption (TDE) operations KMS Key can have multiple key versions. If none is specified, the current key version (latest) of the Key Id is used for the operation. Autonomous Database Serverless does not use key versions, hence is not applicable for Autonomous Database Serverless instances.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousDatabaseBackupSummary. The current state of the backup. Allowed values for this property are: "CREATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "UPDATING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    retention_period_in_days: Optional[Any] = Field(
        None,
        description="Retention period, in days, for long-term backups",
    )
    size_in_tbs: Optional[float] = Field(
        None,
        description="The backup size in terrabytes (TB).",
    )
    time_available_till: Optional[Any] = Field(
        None,
        description="Timestamp until when the backup will be available",
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time the backup completed.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="The date and time the backup started.",
    )
    type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the type of this AutonomousDatabaseBackupSummary. The type of backup. Allowed values for this property are: "INCREMENTAL", "FULL", "LONGTERM", "VIRTUAL_FULL", "CUMULATIVE_INCREMENTAL", "ROLL_FORWARD_IMAGE_COPY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    vault_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Oracle Cloud Infrastructure `vault`__. This parameter and `secretId` are required for Customer Managed Keys.",
    )


def map_autonomousdatabasebackupsummary(
    o: oci.database.models.AutonomousDatabaseBackupSummary,
) -> AutonomousDatabaseBackupSummary | None:
    """Map oci.database.models.AutonomousDatabaseBackupSummary → AutonomousDatabaseBackupSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDatabaseBackupSummary(**data)
    except Exception:
        return AutonomousDatabaseBackupSummary(
            autonomous_database_id=getattr(o, "autonomous_database_id", None),
            backup_destination_details=getattr(o, "backup_destination_details", None),
            compartment_id=getattr(o, "compartment_id", None),
            database_size_in_tbs=getattr(o, "database_size_in_tbs", None),
            db_version=getattr(o, "db_version", None),
            display_name=getattr(o, "display_name", None),
            id=getattr(o, "id", None),
            is_automatic=getattr(o, "is_automatic", None),
            is_restorable=getattr(o, "is_restorable", None),
            key_store_id=getattr(o, "key_store_id", None),
            key_store_wallet_name=getattr(o, "key_store_wallet_name", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            kms_key_version_id=getattr(o, "kms_key_version_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            retention_period_in_days=getattr(o, "retention_period_in_days", None),
            size_in_tbs=getattr(o, "size_in_tbs", None),
            time_available_till=getattr(o, "time_available_till", None),
            time_ended=getattr(o, "time_ended", None),
            time_started=getattr(o, "time_started", None),
            type=getattr(o, "type", None),
            vault_id=getattr(o, "vault_id", None),
        )


class AutonomousDatabaseCharacterSets(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDatabaseCharacterSets."""

    name: Optional[Any] = Field(
        None,
        description="A valid Oracle character set.",
    )


def map_autonomousdatabasecharactersets(
    o: oci.database.models.AutonomousDatabaseCharacterSets,
) -> AutonomousDatabaseCharacterSets | None:
    """Map oci.database.models.AutonomousDatabaseCharacterSets → AutonomousDatabaseCharacterSets Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDatabaseCharacterSets(**data)
    except Exception:
        return AutonomousDatabaseCharacterSets(
            name=getattr(o, "name", None),
        )


class AutonomousDatabaseSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDatabaseSummary."""

    actual_used_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The current amount of storage in use for user and system data, in terabytes (TB).",
    )
    allocated_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The amount of storage currently allocated for the database tables and billed for, rounded up. When auto-scaling is not enabled, this value is equal to the `dataStorageSizeInTBs` value. You can compare this value to the `actualUsedDataStorageSizeInTBs` value to determine if a manual shrink operation is appropriate for your allocated storage. **Note:** Auto-scaling does not automatically decrease allocated storage when data is deleted from the database.",
    )
    apex_details: Optional[Any] = Field(
        None,
        description="Information about Oracle APEX Application Development.",
    )
    are_primary_whitelisted_ips_used: Optional[Any] = Field(
        None,
        description="This field will be null if the Autonomous Database is not Data Guard enabled or Access Control is disabled. It's value would be `TRUE` if Autonomous Database is Data Guard enabled and Access Control is enabled and if the Autonomous Database uses primary IP access control list (ACL) for standby. It's value would be `FALSE` if Autonomous Database is Data Guard enabled and Access Control is enabled and if the Autonomous Database uses different IP access control list (ACL) for standby compared to primary.",
    )
    auto_refresh_frequency_in_seconds: Optional[Any] = Field(
        None,
        description="The frequency a refreshable clone is refreshed after auto-refresh is enabled. The minimum is 1 hour. The maximum is 7 days. The date and time that auto-refresh is enabled is controlled by the `timeOfAutoRefreshStart` parameter.",
    )
    auto_refresh_point_lag_in_seconds: Optional[Any] = Field(
        None,
        description="The time, in seconds, the data of the refreshable clone lags the primary database at the point of refresh. The minimum is 0 minutes (0 mins means refresh to the latest available timestamp). The maximum is 7 days. The lag time increases after refreshing until the next data refresh happens.",
    )
    autonomous_container_database_id: Optional[Any] = Field(
        None,
        description="The Autonomous Container Database `OCID`__. Used only by Autonomous Database on Dedicated Exadata Infrastructure.",
    )
    autonomous_maintenance_schedule_type: Optional[Any] = Field(
        None,
        description="The maintenance schedule type of the Autonomous Database Serverless. An EARLY maintenance schedule follows a schedule applying patches prior to the REGULAR schedule. A REGULAR maintenance schedule follows the normal cycle Allowed values for this property are: \"EARLY\", \"REGULAR\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    availability_domain: Optional[Any] = Field(
        None,
        description="The availability domain where the Autonomous Database Serverless instance is located.",
    )
    available_upgrade_versions: Optional[Any] = Field(
        None,
        description="List of Oracle Database versions available for a database upgrade. If there are no version upgrades available, this list is empty.",
    )
    backup_config: Optional[Any] = Field(
        None,
        description="",
    )
    backup_retention_period_in_days: Optional[Any] = Field(
        None,
        description="Retention period, in days, for long-term backups",
    )
    byol_compute_count_limit: Optional[float] = Field(
        None,
        description="The maximum number of CPUs allowed with a Bring Your Own License (BYOL), including those used for auto-scaling, disaster recovery, tools, etc. Any CPU usage above this limit is considered as License Included and billed.",
    )
    character_set: Optional[Any] = Field(
        None,
        description="The character set for the autonomous database. The default is AL32UTF8. Allowed values are: AL32UTF8, AR8ADOS710, AR8ADOS720, AR8APTEC715, AR8ARABICMACS, AR8ASMO8X, AR8ISO8859P6, AR8MSWIN1256, AR8MUSSAD768, AR8NAFITHA711, AR8NAFITHA721, AR8SAKHR706, AR8SAKHR707, AZ8ISO8859P9E, BG8MSWIN, BG8PC437S, BLT8CP921, BLT8ISO8859P13, BLT8MSWIN1257, BLT8PC775, BN8BSCII, CDN8PC863, CEL8ISO8859P14, CL8ISO8859P5, CL8ISOIR111, CL8KOI8R, CL8KOI8U, CL8MACCYRILLICS, CL8MSWIN1251, EE8ISO8859P2, EE8MACCES, EE8MACCROATIANS, EE8MSWIN1250, EE8PC852, EL8DEC, EL8ISO8859P7, EL8MACGREEKS, EL8MSWIN1253, EL8PC437S, EL8PC851, EL8PC869, ET8MSWIN923, HU8ABMOD, HU8CWI2, IN8ISCII, IS8PC861, IW8ISO8859P8, IW8MACHEBREWS, IW8MSWIN1255, IW8PC1507, JA16EUC, JA16EUCTILDE, JA16SJIS, JA16SJISTILDE, JA16VMS, KO16KSC5601, KO16KSCCS, KO16MSWIN949, LA8ISO6937, LA8PASSPORT, LT8MSWIN921, LT8PC772, LT8PC774, LV8PC1117, LV8PC8LR, LV8RST104090, N8PC865, NE8ISO8859P10, NEE8ISO8859P4, RU8BESTA, RU8PC855, RU8PC866, SE8ISO8859P3, TH8MACTHAIS, TH8TISASCII, TR8DEC, TR8MACTURKISHS, TR8MSWIN1254, TR8PC857, US7ASCII, US8PC437, UTF8, VN8MSWIN1258, VN8VN3, WE8DEC, WE8DG, WE8ISO8859P1, WE8ISO8859P15, WE8ISO8859P9, WE8MACROMAN8S, WE8MSWIN1252, WE8NCR4970, WE8NEXTSTEP, WE8PC850, WE8PC858, WE8PC860, WE8ROMAN8, ZHS16CGB231280, ZHS16GBK, ZHT16BIG5, ZHT16CCDC, ZHT16DBT, ZHT16HKSCS, ZHT16MSWIN950, ZHT32EUC, ZHT32SOPS, ZHT32TRIS",
    )
    clone_table_space_list: Optional[Any] = Field(
        None,
        description="A list of the source Autonomous Database's table space number(s) used to create this partial clone from the backup.",
    )
    cluster_placement_group_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the cluster placement group of the Autonomous Serverless Database.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this AutonomousDatabaseSummary. The `OCID`__ of the compartment.",
    )
    compute_count: Optional[float] = Field(
        None,
        description="The compute amount (CPUs) available to the database. Minimum and maximum values depend on the compute model and whether the database is an Autonomous Database Serverless instance or an Autonomous Database on Dedicated Exadata Infrastructure. The 'ECPU' compute model requires a minimum value of one, for databases in the elastic resource pool and minimum value of two, otherwise. Required when using the `computeModel` parameter. When using `cpuCoreCount` parameter, it is an error to specify computeCount to a non-null value. Providing `computeModel` and `computeCount` is the preferred method for both OCPU and ECPU.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    connection_strings: Optional[Any] = Field(
        None,
        description="The connection string used to connect to the Autonomous Database. The username for the Service Console is ADMIN. Use the password you entered when creating the Autonomous Database for the password value.",
    )
    connection_urls: Optional[Any] = Field(
        None,
        description="",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="The number of CPU cores to be made available to the database. When the ECPU is selected, the value for cpuCoreCount is 0. For Autonomous Database on Dedicated Exadata infrastructure, the maximum number of cores is determined by the infrastructure shape. See `Characteristics of Infrastructure Shapes`__ for shape details. **Note:** This parameter cannot be used with the `ocpuCount` parameter.",
    )
    customer_contacts: Optional[Any] = Field(
        None,
        description="Customer Contacts.",
    )
    data_safe_status: Optional[Any] = Field(
        None,
        description='Status of the Data Safe registration for this Autonomous Database. Allowed values for this property are: "REGISTERING", "REGISTERED", "DEREGISTERING", "NOT_REGISTERED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    data_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The quantity of data in the database, in gigabytes. For Autonomous Transaction Processing databases using ECPUs on Serverless Infrastructure, this value is always populated. In all the other cases, this value will be null and `dataStorageSizeInTBs` will be populated instead.",
    )
    data_storage_size_in_tbs: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the data_storage_size_in_tbs of this AutonomousDatabaseSummary. The quantity of data in the database, in terabytes. The following points apply to Autonomous Databases on Serverless Infrastructure: - This is an integer field whose value remains null when the data size is in GBs and cannot be converted to TBs (by dividing the GB value by 1024) without rounding error. - To get the exact value of data storage size without rounding error, please see `dataStorageSizeInGBs` of Autonomous Database.",
    )
    database_edition: Optional[Any] = Field(
        None,
        description="The Oracle Database Edition that applies to the Autonomous databases. Allowed values for this property are: \"STANDARD_EDITION\", \"ENTERPRISE_EDITION\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    database_management_status: Optional[Any] = Field(
        None,
        description='Status of Database Management for this Autonomous Database. Allowed values for this property are: "ENABLING", "ENABLED", "DISABLING", "NOT_ENABLED", "FAILED_ENABLING", "FAILED_DISABLING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    dataguard_region_type: Optional[Any] = Field(
        None,
        description="**Deprecated.** The Autonomous Data Guard region type of the Autonomous Database. For Autonomous Database Serverless, Autonomous Data Guard associations have designated primary and standby regions, and these region types do not change when the database changes roles. The standby regions in Autonomous Data Guard associations can be the same region designated as the primary region, or they can be remote regions. Certain database administrative operations may be available only in the primary region of the Autonomous Data Guard association, and cannot be performed when the database using the primary role is operating in a remote Autonomous Data Guard standby region. Allowed values for this property are: \"PRIMARY_DG_REGION\", \"REMOTE_STANDBY_DG_REGION\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    db_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_name of this AutonomousDatabaseSummary. The database name.",
    )
    db_tools_details: Optional[Any] = Field(
        None,
        description="The list of database tools details. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, whitelistedIps, isMTLSConnectionRequired, openMode, permissionLevel, dbWorkload, privateEndpointLabel, nsgIds, dbVersion, isRefreshable, dbName, scheduledOperations, isLocalDataGuardEnabled, or isFreeTier.",
    )
    db_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Database version for Autonomous Database.",
    )
    db_workload: Optional[Any] = Field(
        None,
        description='The Autonomous Database workload type. The following values are valid: - OLTP - indicates an Autonomous Transaction Processing database - DW - indicates an Autonomous Data Warehouse database - AJD - indicates an Autonomous JSON Database - APEX - indicates an Autonomous Database with the Oracle APEX Application Development workload type. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, privateEndpointLabel, nsgIds, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier. Allowed values for this property are: "OLTP", "DW", "AJD", "APEX", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    disaster_recovery_region_type: Optional[Any] = Field(
        None,
        description="**Deprecated.** The disaster recovery (DR) region type of the Autonomous Database. For Autonomous Database Serverless instances, DR associations have designated primary and standby regions. These region types do not change when the database changes roles. The standby region in DR associations can be the same region as the primary region, or they can be in a remote regions. Some database administration operations may be available only in the primary region of the DR association, and cannot be performed when the database using the primary role is operating in a remote region. Allowed values for this property are: \"PRIMARY\", \"REMOTE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the Autonomous Database. The name does not have to be unique.",
    )
    encryption_key: Optional[Any] = Field(
        None,
        description="",
    )
    encryption_key_history_entry: Optional[Any] = Field(
        None,
        description="Key History Entry.",
    )
    failed_data_recovery_in_seconds: Optional[Any] = Field(
        None,
        description="Indicates the number of seconds of data loss for a Data Guard failover.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousDatabaseSummary. The `OCID`__ of the Autonomous Database.",
    )
    in_memory_area_in_gbs: Optional[Any] = Field(
        None,
        description="The area assigned to In-Memory tables in Autonomous Database.",
    )
    in_memory_percentage: Optional[Any] = Field(
        None,
        description="The percentage of the System Global Area(SGA) assigned to In-Memory tables in Autonomous Database. This property is applicable only to Autonomous Databases on the Exadata Cloud@Customer platform.",
    )
    infrastructure_type: Optional[Any] = Field(
        None,
        description="The infrastructure type this resource belongs to. Allowed values for this property are: \"CLOUD\", \"CLOUD_AT_CUSTOMER\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    is_access_control_enabled: Optional[Any] = Field(
        None,
        description="Indicates if the database-level access control is enabled. If disabled, database access is defined by the network security rules. If enabled, database access is restricted to the IP addresses defined by the rules specified with the `whitelistedIps` property. While specifying `whitelistedIps` rules is optional, if database-level access control is enabled and no rules are specified, the database will become inaccessible. The rules can be added later using the `UpdateAutonomousDatabase` API operation or edit option in console. When creating a database clone, the desired access control setting should be specified. By default, database-level access control will be disabled for the clone. This property is applicable only to Autonomous Databases on the Exadata Cloud@Customer platform. For Autonomous Database Serverless instances, `whitelistedIps` is used.",
    )
    is_auto_scaling_enabled: Optional[Any] = Field(
        None,
        description="Indicates if auto scaling is enabled for the Autonomous Database CPU core count. The default value is `TRUE`.",
    )
    is_auto_scaling_for_storage_enabled: Optional[Any] = Field(
        None,
        description="Indicates if auto scaling is enabled for the Autonomous Database storage. The default value is `FALSE`.",
    )
    is_backup_retention_locked: Optional[Any] = Field(
        None,
        description="Indicates if the Autonomous Database is backup retention locked.",
    )
    is_data_guard_enabled: Optional[Any] = Field(
        None,
        description="**Deprecated.** Indicates whether the Autonomous Database has local (in-region) Data Guard enabled. Not applicable to cross-region Autonomous Data Guard associations, or to Autonomous Databases using dedicated Exadata infrastructure or Exadata Cloud@Customer infrastructure.",
    )
    is_dedicated: Optional[Any] = Field(
        None,
        description="True if the database uses `dedicated Exadata infrastructure`__.",
    )
    is_dev_tier: Optional[Any] = Field(
        None,
        description="Autonomous Database for Developers are fixed-shape Autonomous Databases that developers can use to build and test new applications. On Serverless, these are low-cost and billed per instance, on Dedicated and Cloud@Customer there is no additional cost to create Developer databases. Developer databases come with limited resources and is not intended for large-scale testing and production deployments. When you need more compute or storage resources, you may upgrade to a full paid production database.",
    )
    is_free_tier: Optional[Any] = Field(
        None,
        description="Indicates if this is an Always Free resource. The default value is false. Note that Always Free Autonomous Databases have 1 CPU and 20GB of memory. For Always Free databases, memory and CPU cannot be scaled. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, openMode, permissionLevel, privateEndpointLabel, nsgIds, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, or isLocalDataGuardEnabled",
    )
    is_local_data_guard_enabled: Optional[Any] = Field(
        None,
        description="Indicates whether the Autonomous Database has local (in-region) Data Guard enabled. Not applicable to cross-region Autonomous Data Guard associations, or to Autonomous Databases using dedicated Exadata infrastructure or Exadata Cloud@Customer infrastructure.",
    )
    is_mtls_connection_required: Optional[Any] = Field(
        None,
        description="Specifies if the Autonomous Database requires mTLS connections. This may not be updated in parallel with any of the following: licenseModel, databaseEdition, cpuCoreCount, computeCount, dataStorageSizeInTBs, whitelistedIps, openMode, permissionLevel, db-workload, privateEndpointLabel, nsgIds, customerContacts, dbVersion, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier. Service Change: The default value of the isMTLSConnectionRequired attribute will change from true to false on July 1, 2023 in the following APIs: - CreateAutonomousDatabase - GetAutonomousDatabase - UpdateAutonomousDatabase Details: Prior to the July 1, 2023 change, the isMTLSConnectionRequired attribute default value was true. This applies to Autonomous Database Serverless. Does this impact me? If you use or maintain custom scripts or Terraform scripts referencing the CreateAutonomousDatabase, GetAutonomousDatabase, or UpdateAutonomousDatabase APIs, you want to check, and possibly modify, the scripts for the changed default value of the attribute. Should you choose not to leave your scripts unchanged, the API calls containing this attribute will continue to work, but the default value will switch from true to false. How do I make this change? Using either OCI SDKs or command line tools, update your custom scripts to explicitly set the isMTLSConnectionRequired attribute to true.",
    )
    is_preview: Optional[Any] = Field(
        None,
        description="Indicates if the Autonomous Database version is a preview version.",
    )
    is_reconnect_clone_enabled: Optional[Any] = Field(
        None,
        description="Indicates if the refreshable clone can be reconnected to its source database.",
    )
    is_refreshable_clone: Optional[Any] = Field(
        None,
        description="Indicates if the Autonomous Database is a refreshable clone. This cannot be updated in parallel with any of the following: cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, openMode, permissionLevel, dbWorkload, privateEndpointLabel, nsgIds, dbVersion, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier.",
    )
    is_remote_data_guard_enabled: Optional[Any] = Field(
        None,
        description="Indicates whether the Autonomous Database has Cross Region Data Guard enabled. Not applicable to Autonomous Databases using dedicated Exadata infrastructure or Exadata Cloud@Customer infrastructure.",
    )
    key_history_entry: Optional[Any] = Field(
        None,
        description="Key History Entry.",
    )
    key_store_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the key store of Oracle Vault.",
    )
    key_store_wallet_name: Optional[Any] = Field(
        None,
        description="The wallet name for Oracle Key Vault.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    kms_key_lifecycle_details: Optional[Any] = Field(
        None,
        description="KMS key lifecycle details.",
    )
    kms_key_version_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container version that is used in database transparent data encryption (TDE) operations KMS Key can have multiple key versions. If none is specified, the current key version (latest) of the Key Id is used for the operation. Autonomous Database Serverless does not use key versions, hence is not applicable for Autonomous Database Serverless instances.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to the Oracle Autonomous Database. Bring your own license (BYOL) allows you to apply your current on-premises Oracle software licenses to equivalent, highly automated Oracle services in the cloud. License Included allows you to subscribe to new Oracle Database software licenses and the Oracle Database service. Note that when provisioning an `Autonomous Database on dedicated Exadata infrastructure`__, this attribute must be null. It is already set at the Autonomous Exadata Infrastructure level. When provisioning an `Autonomous Database Serverless]`__ database, if a value is not specified, the system defaults the value to `BRING_YOUR_OWN_LICENSE`. Bring your own license (BYOL) also allows you to select the DB edition using the optional parameter. This cannot be updated in parallel with any of the following: cpuCoreCount, computeCount, dataStorageSizeInTBs, adminPassword, isMTLSConnectionRequired, dbWorkload, privateEndpointLabel, nsgIds, dbVersion, dbName, scheduledOperations, dbToolsDetails, or isFreeTier. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousDatabaseSummary. The current state of the Autonomous Database. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "STOPPING", "STOPPED", "STARTING", "TERMINATING", "TERMINATED", "UNAVAILABLE", "RESTORE_IN_PROGRESS", "RESTORE_FAILED", "BACKUP_IN_PROGRESS", "SCALE_IN_PROGRESS", "AVAILABLE_NEEDS_ATTENTION", "UPDATING", "MAINTENANCE_IN_PROGRESS", "RESTARTING", "RECREATING", "ROLE_CHANGE_IN_PROGRESS", "UPGRADING", "INACCESSIBLE", "STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    local_adg_auto_failover_max_data_loss_limit: Optional[Any] = Field(
        None,
        description="Parameter that allows users to select an acceptable maximum data loss limit in seconds, up to which Automatic Failover will be triggered when necessary for a Local Autonomous Data Guard",
    )
    local_disaster_recovery_type: Optional[Any] = Field(
        None,
        description="Indicates the local disaster recovery (DR) type of the Autonomous Database Serverless instance. Autonomous Data Guard (ADG) DR type provides business critical DR with a faster recovery time objective (RTO) during failover or switchover. Backup-based DR type provides lower cost DR with a slower RTO during failover or switchover.",
    )
    local_standby_db: Optional[Any] = Field(
        None,
        description="",
    )
    long_term_backup_schedule: Optional[Any] = Field(
        None,
        description="",
    )
    memory_per_oracle_compute_unit_in_gbs: Optional[Any] = Field(
        None,
        description="The amount of memory (in GBs) enabled per ECPU or OCPU.",
    )
    ncharacter_set: Optional[Any] = Field(
        None,
        description="The national character set for the autonomous database. The default is AL16UTF16. Allowed values are: AL16UTF16 or UTF8.",
    )
    net_services_architecture: Optional[Any] = Field(
        None,
        description="Enabling SHARED server architecture enables a database server to allow many client processes to share very few server processes, thereby increasing the number of supported users. Allowed values for this property are: \"DEDICATED\", \"SHARED\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    next_long_term_backup_time_stamp: Optional[Any] = Field(
        None,
        description="The date and time when the next long-term backup would be created.",
    )
    nsg_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ for the network security groups (NSGs) to which this resource belongs. Setting this to an empty list removes all resources from all NSGs. For more information about NSGs, see `Security Rules`__. **NsgIds restrictions:** - A network security group (NSG) is optional for Autonomous Databases with private access. The nsgIds list can be empty.",
    )
    ocpu_count: Optional[float] = Field(
        None,
        description="The number of OCPU cores to be made available to the database. The following points apply: - For Autonomous Databases on Dedicated Exadata Infrastructure, to provision less than 1 core, enter a fractional value in an increment of 0.1. For example, you can provision 0.3 or 0.4 cores, but not 0.35 cores. (Note that fractional OCPU values are not supported for Autonomous Database Serverless instances.) - To provision cores, enter an integer between 1 and the maximum number of cores available for the infrastructure shape. For example, you can provision 2 cores or 3 cores, but not 2.5 cores. This applies to Autonomous Databases on both serverless and dedicated Exadata infrastructure. - For Autonomous Database Serverless instances, this parameter is not used. For Autonomous Databases on Dedicated Exadata Infrastructure, the maximum number of cores is determined by the infrastructure shape. See `Characteristics of Infrastructure Shapes`__ for shape details. **Note:** This parameter cannot be used with the `cpuCoreCount` parameter.",
    )
    open_mode: Optional[Any] = Field(
        None,
        description="Indicates the Autonomous Database mode. The database can be opened in `READ_ONLY` or `READ_WRITE` mode. This cannot be updated in parallel with any of the following: cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, or isFreeTier. Allowed values for this property are: \"READ_ONLY\", \"READ_WRITE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    operations_insights_status: Optional[Any] = Field(
        None,
        description='Status of Operations Insights for this Autonomous Database. Allowed values for this property are: "ENABLING", "ENABLED", "DISABLING", "NOT_ENABLED", "FAILED_ENABLING", "FAILED_DISABLING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_db_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ of standby databases located in Autonomous Data Guard remote regions that are associated with the source database. Note that for Autonomous Database Serverless instances, standby databases located in the same region as the source primary database do not have OCIDs.",
    )
    permission_level: Optional[Any] = Field(
        None,
        description="The Autonomous Database permission level. Restricted mode allows access only by admin users. This cannot be updated in parallel with any of the following: cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, nsgIds, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, or isFreeTier. Allowed values for this property are: \"RESTRICTED\", \"UNRESTRICTED\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    private_endpoint: Optional[Any] = Field(
        None,
        description="The private endpoint for the resource.",
    )
    private_endpoint_ip: Optional[Any] = Field(
        None,
        description="The private endpoint Ip address for the resource.",
    )
    private_endpoint_label: Optional[Any] = Field(
        None,
        description="The resource's private endpoint label. - Setting the endpoint label to a non-empty string creates a private endpoint database. - Resetting the endpoint label to an empty string, after the creation of the private endpoint database, changes the private endpoint database to a public endpoint database. - Setting the endpoint label to a non-empty string value, updates to a new private endpoint database, when the database is disabled and re-enabled. This setting cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, dbWorkload, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, or isFreeTier.",
    )
    provisionable_cpus: Optional[Any] = Field(
        None,
        description="An array of CPU values that an Autonomous Database can be scaled to.",
    )
    public_connection_urls: Optional[Any] = Field(
        None,
        description="The Public URLs of Private Endpoint database for accessing Oracle Application Express (APEX) and SQL Developer Web with a browser from a Compute instance within your VCN or that has a direct connection to your VCN.",
    )
    public_endpoint: Optional[Any] = Field(
        None,
        description="The public endpoint for the private endpoint enabled resource.",
    )
    refreshable_mode: Optional[Any] = Field(
        None,
        description="The refresh mode of the clone. AUTOMATIC indicates that the clone is automatically being refreshed with data from the source Autonomous Database. Allowed values for this property are: \"AUTOMATIC\", \"MANUAL\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    refreshable_status: Optional[Any] = Field(
        None,
        description="The refresh status of the clone. REFRESHING indicates that the clone is currently being refreshed with data from the source Autonomous Database. Allowed values for this property are: \"REFRESHING\", \"NOT_REFRESHING\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    remote_disaster_recovery_configuration: Optional[Any] = Field(
        None,
        description="",
    )
    resource_pool_leader_id: Optional[Any] = Field(
        None,
        description="The unique identifier for leader autonomous database OCID `OCID`__.",
    )
    resource_pool_summary: Optional[Any] = Field(
        None,
        description="",
    )
    role: Optional[Any] = Field(
        None,
        description='The Data Guard role of the Autonomous Container Database or Autonomous Database, if Autonomous Data Guard is enabled. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", "BACKUP_COPY", "SNAPSHOT_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    scheduled_operations: Optional[Any] = Field(
        None,
        description="The list of scheduled operations. Consists of values such as dayOfWeek, scheduledStartTime, scheduledStopTime. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, whitelistedIps, isMTLSConnectionRequired, openMode, permissionLevel, dbWorkload, privateEndpointLabel, nsgIds, dbVersion, isRefreshable, dbName, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier.",
    )
    security_attributes: Optional[Any] = Field(
        None,
        description='Security Attributes for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. Example: `{"Oracle-ZPR": {"MaxEgressCount": {"value": "42", "mode": "audit"}}}`',
    )
    service_console_url: Optional[Any] = Field(
        None,
        description="The URL of the Service Console for the Autonomous Database.",
    )
    source_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the source Autonomous Database that was cloned to create the current Autonomous Database.",
    )
    standby_db: Optional[Any] = Field(
        None,
        description="**Deprecated** Autonomous Data Guard standby database details.",
    )
    standby_whitelisted_ips: Optional[Any] = Field(
        None,
        description='The client IP access control list (ACL). This feature is available for `Autonomous Database Serverless]`__ and on Exadata Cloud@Customer. Only clients connecting from an IP address included in the ACL may access the Autonomous Database instance. If `arePrimaryWhitelistedIpsUsed` is \'TRUE\' then Autonomous Database uses this primary\'s IP access control list (ACL) for the disaster recovery peer called `standbywhitelistedips`. For Autonomous Database Serverless, this is an array of CIDR (classless inter-domain routing) notations for a subnet or VCN OCID (virtual cloud network Oracle Cloud ID). Multiple IPs and VCN OCIDs should be separate strings separated by commas, but if it’s other configurations that need multiple pieces of information then its each piece is connected with semicolon (;) as a delimiter. Example: `["1.1.1.1","1.1.1.0/24","ocid1.vcn.oc1.sea.<unique_id>","ocid1.vcn.oc1.sea.<unique_id1>;1.1.1.1","ocid1.vcn.oc1.sea.<unique_id2>;1.1.0.0/16"]` For Exadata Cloud@Customer, this is an array of IP addresses or CIDR notations. Example: `["1.1.1.1","1.1.1.0/24","1.1.2.25"]` For an update operation, if you want to delete all the IPs in the ACL, use an array with a single empty string entry. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, isMTLSConnectionRequired, openMode, permissionLevel, dbWorkload, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier.',
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the subnet the resource is associated with. **Subnet Restrictions:** - For bare metal DB systems and for single node virtual machine DB systems, do not use a subnet that overlaps with 192.168.16.16/28. - For Exadata and virtual machine 2-node RAC systems, do not use a subnet that overlaps with 192.168.128.0/20. - For Autonomous Database, setting this will disable public secure access to the database. These subnets are used by the Oracle Clusterware private interconnect on the database instance. Specifying an overlapping subnet will cause the private interconnect to malfunction. This restriction applies to both the client subnet and the backup subnet.",
    )
    subscription_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the subscription with which resource needs to be associated with.",
    )
    supported_regions_to_clone_to: Optional[Any] = Field(
        None,
        description="The list of regions that support the creation of an Autonomous Database clone or an Autonomous Data Guard standby database.",
    )
    system_tags: Optional[Any] = Field(
        None,
        description="System tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Autonomous Database was created.",
    )
    time_data_guard_role_changed: Optional[Any] = Field(
        None,
        description='The date and time the Autonomous Data Guard role was switched for the Autonomous Database. For databases that have standbys in both the primary Data Guard region and a remote Data Guard standby region, this is the latest timestamp of either the database using the "primary" role in the primary Data Guard region, or database located in the remote Data Guard standby region.',
    )
    time_deletion_of_free_autonomous_database: Optional[Any] = Field(
        None,
        description="The date and time the Always Free database will be automatically deleted because of inactivity. If the database is in the STOPPED state and without activity until this time, it will be deleted.",
    )
    time_disaster_recovery_role_changed: Optional[Any] = Field(
        None,
        description="The date and time the Disaster Recovery role was switched for the standby Autonomous Database.",
    )
    time_local_data_guard_enabled: Optional[Any] = Field(
        None,
        description="The date and time that Autonomous Data Guard was enabled for an Autonomous Database where the standby was provisioned in the same region as the primary database.",
    )
    time_maintenance_begin: Optional[Any] = Field(
        None,
        description="The date and time when maintenance will begin.",
    )
    time_maintenance_end: Optional[Any] = Field(
        None,
        description="The date and time when maintenance will end.",
    )
    time_of_auto_refresh_start: Optional[Any] = Field(
        None,
        description="The the date and time that auto-refreshing will begin for an Autonomous Database refreshable clone. This value controls only the start time for the first refresh operation. Subsequent (ongoing) refresh operations have start times controlled by the value of the `autoRefreshFrequencyInSeconds` parameter.",
    )
    time_of_joining_resource_pool: Optional[Any] = Field(
        None,
        description="The time the member joined the resource pool.",
    )
    time_of_last_failover: Optional[Any] = Field(
        None,
        description="The timestamp of the last failover operation.",
    )
    time_of_last_refresh: Optional[Any] = Field(
        None,
        description="The date and time when last refresh happened.",
    )
    time_of_last_refresh_point: Optional[Any] = Field(
        None,
        description="The refresh point timestamp (UTC). The refresh point is the time to which the database was most recently refreshed. Data created after the refresh point is not included in the refresh.",
    )
    time_of_last_switchover: Optional[Any] = Field(
        None,
        description="The timestamp of the last switchover operation for the Autonomous Database.",
    )
    time_of_next_refresh: Optional[Any] = Field(
        None,
        description="The date and time of next refresh.",
    )
    time_reclamation_of_free_autonomous_database: Optional[Any] = Field(
        None,
        description="The date and time the Always Free database will be stopped because of inactivity. If this time is reached without any database activity, the database will automatically be put into the STOPPED state.",
    )
    time_undeleted: Optional[Any] = Field(
        None,
        description="The date and time the Autonomous Database was most recently undeleted.",
    )
    time_until_reconnect_clone_enabled: Optional[Any] = Field(
        None,
        description="The time and date as an RFC3339 formatted string, e.g., 2022-01-01T12:00:00.000Z, to set the limit for a refreshable clone to be reconnected to its source database.",
    )
    total_backup_storage_size_in_gbs: Optional[float] = Field(
        None,
        description="The backup storage to the database.",
    )
    used_data_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The storage space consumed by Autonomous Database in GBs.",
    )
    used_data_storage_size_in_tbs: Optional[Any] = Field(
        None,
        description="The amount of storage that has been used for Autonomous Databases in dedicated infrastructure, in terabytes.",
    )
    vault_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Oracle Cloud Infrastructure `vault`__. This parameter and `secretId` are required for Customer Managed Keys.",
    )
    whitelisted_ips: Optional[Any] = Field(
        None,
        description='The client IP access control list (ACL). This feature is available for `Autonomous Database Serverless]`__ and on Exadata Cloud@Customer. Only clients connecting from an IP address included in the ACL may access the Autonomous Database instance. If `arePrimaryWhitelistedIpsUsed` is \'TRUE\' then Autonomous Database uses this primary\'s IP access control list (ACL) for the disaster recovery peer called `standbywhitelistedips`. For Autonomous Database Serverless, this is an array of CIDR (classless inter-domain routing) notations for a subnet or VCN OCID (virtual cloud network Oracle Cloud ID). Multiple IPs and VCN OCIDs should be separate strings separated by commas, but if it’s other configurations that need multiple pieces of information then its each piece is connected with semicolon (;) as a delimiter. Example: `["1.1.1.1","1.1.1.0/24","ocid1.vcn.oc1.sea.<unique_id>","ocid1.vcn.oc1.sea.<unique_id1>;1.1.1.1","ocid1.vcn.oc1.sea.<unique_id2>;1.1.0.0/16"]` For Exadata Cloud@Customer, this is an array of IP addresses or CIDR notations. Example: `["1.1.1.1","1.1.1.0/24","1.1.2.25"]` For an update operation, if you want to delete all the IPs in the ACL, use an array with a single empty string entry. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, isMTLSConnectionRequired, openMode, permissionLevel, dbWorkload, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier.',
    )


def map_autonomousdatabasesummary(
    o: oci.database.models.AutonomousDatabaseSummary,
) -> AutonomousDatabaseSummary | None:
    """Map oci.database.models.AutonomousDatabaseSummary → AutonomousDatabaseSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDatabaseSummary(**data)
    except Exception:
        return AutonomousDatabaseSummary(
            actual_used_data_storage_size_in_tbs=getattr(
                o, "actual_used_data_storage_size_in_tbs", None
            ),
            allocated_storage_size_in_tbs=getattr(
                o, "allocated_storage_size_in_tbs", None
            ),
            apex_details=getattr(o, "apex_details", None),
            are_primary_whitelisted_ips_used=getattr(
                o, "are_primary_whitelisted_ips_used", None
            ),
            auto_refresh_frequency_in_seconds=getattr(
                o, "auto_refresh_frequency_in_seconds", None
            ),
            auto_refresh_point_lag_in_seconds=getattr(
                o, "auto_refresh_point_lag_in_seconds", None
            ),
            autonomous_container_database_id=getattr(
                o, "autonomous_container_database_id", None
            ),
            autonomous_maintenance_schedule_type=getattr(
                o, "autonomous_maintenance_schedule_type", None
            ),
            availability_domain=getattr(o, "availability_domain", None),
            available_upgrade_versions=getattr(o, "available_upgrade_versions", None),
            backup_config=getattr(o, "backup_config", None),
            backup_retention_period_in_days=getattr(
                o, "backup_retention_period_in_days", None
            ),
            byol_compute_count_limit=getattr(o, "byol_compute_count_limit", None),
            character_set=getattr(o, "character_set", None),
            clone_table_space_list=getattr(o, "clone_table_space_list", None),
            cluster_placement_group_id=getattr(o, "cluster_placement_group_id", None),
            compartment_id=getattr(o, "compartment_id", None),
            compute_count=getattr(o, "compute_count", None),
            compute_model=getattr(o, "compute_model", None),
            connection_strings=getattr(o, "connection_strings", None),
            connection_urls=getattr(o, "connection_urls", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            customer_contacts=getattr(o, "customer_contacts", None),
            data_safe_status=getattr(o, "data_safe_status", None),
            data_storage_size_in_gbs=getattr(o, "data_storage_size_in_gbs", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            database_edition=getattr(o, "database_edition", None),
            database_management_status=getattr(o, "database_management_status", None),
            dataguard_region_type=getattr(o, "dataguard_region_type", None),
            db_name=getattr(o, "db_name", None),
            db_tools_details=getattr(o, "db_tools_details", None),
            db_version=getattr(o, "db_version", None),
            db_workload=getattr(o, "db_workload", None),
            defined_tags=getattr(o, "defined_tags", None),
            disaster_recovery_region_type=getattr(
                o, "disaster_recovery_region_type", None
            ),
            display_name=getattr(o, "display_name", None),
            encryption_key=getattr(o, "encryption_key", None),
            encryption_key_history_entry=getattr(
                o, "encryption_key_history_entry", None
            ),
            failed_data_recovery_in_seconds=getattr(
                o, "failed_data_recovery_in_seconds", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            in_memory_area_in_gbs=getattr(o, "in_memory_area_in_gbs", None),
            in_memory_percentage=getattr(o, "in_memory_percentage", None),
            infrastructure_type=getattr(o, "infrastructure_type", None),
            is_access_control_enabled=getattr(o, "is_access_control_enabled", None),
            is_auto_scaling_enabled=getattr(o, "is_auto_scaling_enabled", None),
            is_auto_scaling_for_storage_enabled=getattr(
                o, "is_auto_scaling_for_storage_enabled", None
            ),
            is_backup_retention_locked=getattr(o, "is_backup_retention_locked", None),
            is_data_guard_enabled=getattr(o, "is_data_guard_enabled", None),
            is_dedicated=getattr(o, "is_dedicated", None),
            is_dev_tier=getattr(o, "is_dev_tier", None),
            is_free_tier=getattr(o, "is_free_tier", None),
            is_local_data_guard_enabled=getattr(o, "is_local_data_guard_enabled", None),
            is_mtls_connection_required=getattr(o, "is_mtls_connection_required", None),
            is_preview=getattr(o, "is_preview", None),
            is_reconnect_clone_enabled=getattr(o, "is_reconnect_clone_enabled", None),
            is_refreshable_clone=getattr(o, "is_refreshable_clone", None),
            is_remote_data_guard_enabled=getattr(
                o, "is_remote_data_guard_enabled", None
            ),
            key_history_entry=getattr(o, "key_history_entry", None),
            key_store_id=getattr(o, "key_store_id", None),
            key_store_wallet_name=getattr(o, "key_store_wallet_name", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            kms_key_lifecycle_details=getattr(o, "kms_key_lifecycle_details", None),
            kms_key_version_id=getattr(o, "kms_key_version_id", None),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            local_adg_auto_failover_max_data_loss_limit=getattr(
                o, "local_adg_auto_failover_max_data_loss_limit", None
            ),
            local_disaster_recovery_type=getattr(
                o, "local_disaster_recovery_type", None
            ),
            local_standby_db=getattr(o, "local_standby_db", None),
            long_term_backup_schedule=getattr(o, "long_term_backup_schedule", None),
            memory_per_oracle_compute_unit_in_gbs=getattr(
                o, "memory_per_oracle_compute_unit_in_gbs", None
            ),
            ncharacter_set=getattr(o, "ncharacter_set", None),
            net_services_architecture=getattr(o, "net_services_architecture", None),
            next_long_term_backup_time_stamp=getattr(
                o, "next_long_term_backup_time_stamp", None
            ),
            nsg_ids=getattr(o, "nsg_ids", None),
            ocpu_count=getattr(o, "ocpu_count", None),
            open_mode=getattr(o, "open_mode", None),
            operations_insights_status=getattr(o, "operations_insights_status", None),
            peer_db_ids=getattr(o, "peer_db_ids", None),
            permission_level=getattr(o, "permission_level", None),
            private_endpoint=getattr(o, "private_endpoint", None),
            private_endpoint_ip=getattr(o, "private_endpoint_ip", None),
            private_endpoint_label=getattr(o, "private_endpoint_label", None),
            provisionable_cpus=getattr(o, "provisionable_cpus", None),
            public_connection_urls=getattr(o, "public_connection_urls", None),
            public_endpoint=getattr(o, "public_endpoint", None),
            refreshable_mode=getattr(o, "refreshable_mode", None),
            refreshable_status=getattr(o, "refreshable_status", None),
            remote_disaster_recovery_configuration=getattr(
                o, "remote_disaster_recovery_configuration", None
            ),
            resource_pool_leader_id=getattr(o, "resource_pool_leader_id", None),
            resource_pool_summary=getattr(o, "resource_pool_summary", None),
            role=getattr(o, "role", None),
            scheduled_operations=getattr(o, "scheduled_operations", None),
            security_attributes=getattr(o, "security_attributes", None),
            service_console_url=getattr(o, "service_console_url", None),
            source_id=getattr(o, "source_id", None),
            standby_db=getattr(o, "standby_db", None),
            standby_whitelisted_ips=getattr(o, "standby_whitelisted_ips", None),
            subnet_id=getattr(o, "subnet_id", None),
            subscription_id=getattr(o, "subscription_id", None),
            supported_regions_to_clone_to=getattr(
                o, "supported_regions_to_clone_to", None
            ),
            system_tags=getattr(o, "system_tags", None),
            time_created=getattr(o, "time_created", None),
            time_data_guard_role_changed=getattr(
                o, "time_data_guard_role_changed", None
            ),
            time_deletion_of_free_autonomous_database=getattr(
                o, "time_deletion_of_free_autonomous_database", None
            ),
            time_disaster_recovery_role_changed=getattr(
                o, "time_disaster_recovery_role_changed", None
            ),
            time_local_data_guard_enabled=getattr(
                o, "time_local_data_guard_enabled", None
            ),
            time_maintenance_begin=getattr(o, "time_maintenance_begin", None),
            time_maintenance_end=getattr(o, "time_maintenance_end", None),
            time_of_auto_refresh_start=getattr(o, "time_of_auto_refresh_start", None),
            time_of_joining_resource_pool=getattr(
                o, "time_of_joining_resource_pool", None
            ),
            time_of_last_failover=getattr(o, "time_of_last_failover", None),
            time_of_last_refresh=getattr(o, "time_of_last_refresh", None),
            time_of_last_refresh_point=getattr(o, "time_of_last_refresh_point", None),
            time_of_last_switchover=getattr(o, "time_of_last_switchover", None),
            time_of_next_refresh=getattr(o, "time_of_next_refresh", None),
            time_reclamation_of_free_autonomous_database=getattr(
                o, "time_reclamation_of_free_autonomous_database", None
            ),
            time_undeleted=getattr(o, "time_undeleted", None),
            time_until_reconnect_clone_enabled=getattr(
                o, "time_until_reconnect_clone_enabled", None
            ),
            total_backup_storage_size_in_gbs=getattr(
                o, "total_backup_storage_size_in_gbs", None
            ),
            used_data_storage_size_in_gbs=getattr(
                o, "used_data_storage_size_in_gbs", None
            ),
            used_data_storage_size_in_tbs=getattr(
                o, "used_data_storage_size_in_tbs", None
            ),
            vault_id=getattr(o, "vault_id", None),
            whitelisted_ips=getattr(o, "whitelisted_ips", None),
        )


class AutonomousDatabaseDataguardAssociation(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDatabaseDataguardAssociation."""

    apply_lag: Optional[Any] = Field(
        None,
        description="The lag time between updates to the primary database and application of the redo data on the standby database, as computed by the reporting database. Example: `9 seconds`",
    )
    apply_rate: Optional[Any] = Field(
        None,
        description="The rate at which redo logs are synced between the associated databases. Example: `180 Mb per second`",
    )
    autonomous_database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the autonomous_database_id of this AutonomousDatabaseDataguardAssociation. The `OCID`__ of the Autonomous Database that has a relationship with the peer Autonomous Database.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousDatabaseDataguardAssociation. The OCID of the Autonomous Dataguard created for Autonomous Container Database where given Autonomous Database resides in.",
    )
    is_automatic_failover_enabled: Optional[Any] = Field(
        None,
        description="Indicates whether Automatic Failover is enabled for Autonomous Container Database Dataguard Association",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycleState, if available.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousDatabaseDataguardAssociation. The current state of Autonomous Data Guard. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "ROLE_CHANGE_IN_PROGRESS", "TERMINATING", "TERMINATED", "FAILED", "UNAVAILABLE", "UPDATING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_autonomous_database_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the peer Autonomous Database.",
    )
    peer_autonomous_database_life_cycle_state: Optional[Any] = Field(
        None,
        description='The current state of the Autonomous Database. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "STOPPING", "STOPPED", "STARTING", "TERMINATING", "TERMINATED", "UNAVAILABLE", "RESTORE_IN_PROGRESS", "RESTORE_FAILED", "BACKUP_IN_PROGRESS", "SCALE_IN_PROGRESS", "AVAILABLE_NEEDS_ATTENTION", "UPDATING", "MAINTENANCE_IN_PROGRESS", "RESTARTING", "RECREATING", "ROLE_CHANGE_IN_PROGRESS", "UPGRADING", "INACCESSIBLE", "STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_role: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the peer_role of this AutonomousDatabaseDataguardAssociation. The Data Guard role of the Autonomous Container Database or Autonomous Database, if Autonomous Data Guard is enabled. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", "BACKUP_COPY", "SNAPSHOT_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    protection_mode: Optional[Any] = Field(
        None,
        description="The protection mode of this Autonomous Data Guard association. For more information, see `Oracle Data Guard Protection Modes`__ in the Oracle Data Guard documentation. Allowed values for this property are: \"MAXIMUM_AVAILABILITY\", \"MAXIMUM_PERFORMANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    role: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the role of this AutonomousDatabaseDataguardAssociation. The Data Guard role of the Autonomous Container Database or Autonomous Database, if Autonomous Data Guard is enabled. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", "BACKUP_COPY", "SNAPSHOT_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Data Guard association was created.",
    )
    time_last_role_changed: Optional[Any] = Field(
        None,
        description="The date and time when the last role change action happened.",
    )
    time_last_synced: Optional[Any] = Field(
        None,
        description="The date and time of the last update to the apply lag, apply rate, and transport lag values.",
    )
    transport_lag: Optional[Any] = Field(
        None,
        description="The approximate number of seconds of redo data not yet available on the standby Autonomous Container Database, as computed by the reporting database. Example: `7 seconds`",
    )


def map_autonomousdatabasedataguardassociation(
    o: oci.database.models.AutonomousDatabaseDataguardAssociation,
) -> AutonomousDatabaseDataguardAssociation | None:
    """Map oci.database.models.AutonomousDatabaseDataguardAssociation → AutonomousDatabaseDataguardAssociation Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDatabaseDataguardAssociation(**data)
    except Exception:
        return AutonomousDatabaseDataguardAssociation(
            apply_lag=getattr(o, "apply_lag", None),
            apply_rate=getattr(o, "apply_rate", None),
            autonomous_database_id=getattr(o, "autonomous_database_id", None),
            id=getattr(o, "id", None),
            is_automatic_failover_enabled=getattr(
                o, "is_automatic_failover_enabled", None
            ),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            peer_autonomous_database_id=getattr(o, "peer_autonomous_database_id", None),
            peer_autonomous_database_life_cycle_state=getattr(
                o, "peer_autonomous_database_life_cycle_state", None
            ),
            peer_role=getattr(o, "peer_role", None),
            protection_mode=getattr(o, "protection_mode", None),
            role=getattr(o, "role", None),
            time_created=getattr(o, "time_created", None),
            time_last_role_changed=getattr(o, "time_last_role_changed", None),
            time_last_synced=getattr(o, "time_last_synced", None),
            transport_lag=getattr(o, "transport_lag", None),
        )


class AutonomousDatabasePeerCollection(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDatabasePeerCollection."""

    items: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the items of this AutonomousDatabasePeerCollection. This array holds details about Autonomous Database Peers for Oracle an Autonomous Database.",
    )


def map_autonomousdatabasepeercollection(
    o: oci.database.models.AutonomousDatabasePeerCollection,
) -> AutonomousDatabasePeerCollection | None:
    """Map oci.database.models.AutonomousDatabasePeerCollection → AutonomousDatabasePeerCollection Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDatabasePeerCollection(**data)
    except Exception:
        return AutonomousDatabasePeerCollection(
            items=getattr(o, "items", None),
        )


class RefreshableCloneCollection(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.RefreshableCloneCollection."""

    items: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the items of this RefreshableCloneCollection.",
    )


def map_refreshableclonecollection(
    o: oci.database.models.RefreshableCloneCollection,
) -> RefreshableCloneCollection | None:
    """Map oci.database.models.RefreshableCloneCollection → RefreshableCloneCollection Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return RefreshableCloneCollection(**data)
    except Exception:
        return RefreshableCloneCollection(
            items=getattr(o, "items", None),
        )


class AutonomousDatabaseSoftwareImageCollection(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDatabaseSoftwareImageCollection."""

    items: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the items of this AutonomousDatabaseSoftwareImageCollection. List of Autonomous Database Software Images.",
    )


def map_autonomousdatabasesoftwareimagecollection(
    o: oci.database.models.AutonomousDatabaseSoftwareImageCollection,
) -> AutonomousDatabaseSoftwareImageCollection | None:
    """Map oci.database.models.AutonomousDatabaseSoftwareImageCollection → AutonomousDatabaseSoftwareImageCollection Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDatabaseSoftwareImageCollection(**data)
    except Exception:
        return AutonomousDatabaseSoftwareImageCollection(
            items=getattr(o, "items", None),
        )


class AutonomousDbPreviewVersionSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDbPreviewVersionSummary."""

    db_workload: Optional[Any] = Field(
        None,
        description='The Autonomous Database workload type. The following values are valid: - OLTP - indicates an Autonomous Transaction Processing database - DW - indicates an Autonomous Data Warehouse database - AJD - indicates an Autonomous JSON Database - APEX - indicates an Autonomous Database with the Oracle APEX Application Development workload type. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, privateEndpointLabel, nsgIds, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier. Allowed values for this property are: "OLTP", "DW", "AJD", "APEX", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    details: Optional[Any] = Field(
        None,
        description="A URL that points to a detailed description of the preview version.",
    )
    time_preview_begin: Optional[Any] = Field(
        None,
        description="The date and time when the preview version availability begins.",
    )
    time_preview_end: Optional[Any] = Field(
        None,
        description="The date and time when the preview version availability ends.",
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this AutonomousDbPreviewVersionSummary. A valid Autonomous Database preview version.",
    )


def map_autonomousdbpreviewversionsummary(
    o: oci.database.models.AutonomousDbPreviewVersionSummary,
) -> AutonomousDbPreviewVersionSummary | None:
    """Map oci.database.models.AutonomousDbPreviewVersionSummary → AutonomousDbPreviewVersionSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDbPreviewVersionSummary(**data)
    except Exception:
        return AutonomousDbPreviewVersionSummary(
            db_workload=getattr(o, "db_workload", None),
            details=getattr(o, "details", None),
            time_preview_begin=getattr(o, "time_preview_begin", None),
            time_preview_end=getattr(o, "time_preview_end", None),
            version=getattr(o, "version", None),
        )


class AutonomousDbVersionSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDbVersionSummary."""

    db_workload: Optional[Any] = Field(
        None,
        description='The Autonomous Database workload type. The following values are valid: - OLTP - indicates an Autonomous Transaction Processing database - DW - indicates an Autonomous Data Warehouse database - AJD - indicates an Autonomous JSON Database - APEX - indicates an Autonomous Database with the Oracle APEX Application Development workload type. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, privateEndpointLabel, nsgIds, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier. Allowed values for this property are: "OLTP", "DW", "AJD", "APEX", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    details: Optional[Any] = Field(
        None,
        description="A URL that points to a detailed description of the Autonomous Database version.",
    )
    is_dedicated: Optional[Any] = Field(
        None,
        description="True if the database uses `dedicated Exadata infrastructure`__.",
    )
    is_default_for_free: Optional[Any] = Field(
        None,
        description="True if this version of the Oracle Database software's default is free.",
    )
    is_default_for_paid: Optional[Any] = Field(
        None,
        description="True if this version of the Oracle Database software's default is paid.",
    )
    is_free_tier_enabled: Optional[Any] = Field(
        None,
        description="True if this version of the Oracle Database software can be used for Always-Free Autonomous Databases.",
    )
    is_paid_enabled: Optional[Any] = Field(
        None,
        description="True if this version of the Oracle Database software has payments enabled.",
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this AutonomousDbVersionSummary. A valid Oracle Database version for Autonomous Database.",
    )


def map_autonomousdbversionsummary(
    o: oci.database.models.AutonomousDbVersionSummary,
) -> AutonomousDbVersionSummary | None:
    """Map oci.database.models.AutonomousDbVersionSummary → AutonomousDbVersionSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDbVersionSummary(**data)
    except Exception:
        return AutonomousDbVersionSummary(
            db_workload=getattr(o, "db_workload", None),
            details=getattr(o, "details", None),
            is_dedicated=getattr(o, "is_dedicated", None),
            is_default_for_free=getattr(o, "is_default_for_free", None),
            is_default_for_paid=getattr(o, "is_default_for_paid", None),
            is_free_tier_enabled=getattr(o, "is_free_tier_enabled", None),
            is_paid_enabled=getattr(o, "is_paid_enabled", None),
            version=getattr(o, "version", None),
        )


class AutonomousVirtualMachineSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousVirtualMachineSummary."""

    autonomous_vm_cluster_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Autonomous VM Cluster associated with the Autonomous Virtual Machine.",
    )
    client_ip_address: Optional[Any] = Field(
        None,
        description="Client IP Address.",
    )
    cloud_autonomous_vm_cluster_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Cloud Autonomous VM Cluster associated with the Autonomous Virtual Machine.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="The number of CPU cores enabled on the Autonomous Virtual Machine.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The allocated local node storage in GBs on the Autonomous Virtual Machine.",
    )
    db_server_display_name: Optional[Any] = Field(
        None,
        description="The display name of the dbServer associated with the Autonomous Virtual Machine.",
    )
    db_server_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Db server associated with the Autonomous Virtual Machine.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousVirtualMachineSummary. The `OCID`__ of the Autonomous Virtual Machine.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousVirtualMachineSummary. The current state of the Autonomous Virtual Machine. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The allocated memory in GBs on the Autonomous Virtual Machine.",
    )
    vm_name: Optional[Any] = Field(
        None,
        description="The name of the Autonomous Virtual Machine.",
    )


def map_autonomousvirtualmachinesummary(
    o: oci.database.models.AutonomousVirtualMachineSummary,
) -> AutonomousVirtualMachineSummary | None:
    """Map oci.database.models.AutonomousVirtualMachineSummary → AutonomousVirtualMachineSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousVirtualMachineSummary(**data)
    except Exception:
        return AutonomousVirtualMachineSummary(
            autonomous_vm_cluster_id=getattr(o, "autonomous_vm_cluster_id", None),
            client_ip_address=getattr(o, "client_ip_address", None),
            cloud_autonomous_vm_cluster_id=getattr(
                o, "cloud_autonomous_vm_cluster_id", None
            ),
            compartment_id=getattr(o, "compartment_id", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_server_display_name=getattr(o, "db_server_display_name", None),
            db_server_id=getattr(o, "db_server_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            vm_name=getattr(o, "vm_name", None),
        )


class AutonomousVmClusterSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousVmClusterSummary."""

    autonomous_data_storage_percentage: Optional[float] = Field(
        None,
        description="The percentage of the data storage used for the Autonomous Databases in an Autonomous VM Cluster.",
    )
    autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size allocated for Autonomous Databases, in TBs.",
    )
    available_autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size available for Autonomous Databases, in TBs.",
    )
    available_container_databases: Optional[Any] = Field(
        None,
        description="The number of Autonomous Container Databases that can be created with the currently available local storage.",
    )
    available_cpus: Optional[Any] = Field(
        None,
        description="The numnber of CPU cores available.",
    )
    available_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="**Deprecated.** Use `availableAutonomousDataStorageSizeInTBs` for Autonomous Databases' data storage availability in TBs.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this AutonomousVmClusterSummary. The `OCID`__ of the compartment.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous VM Cluster. ECPU compute model is the recommended model and OCPU compute model is legacy. See `Compute Models in Autonomous Database on Dedicated Exadata #Infrastructure`__ for more details. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    cpu_core_count_per_node: Optional[Any] = Field(
        None,
        description="The number of CPU cores enabled per VM cluster node.",
    )
    cpu_percentage: Optional[float] = Field(
        None,
        description="The percentage of total number of CPUs used in an Autonomous VM Cluster.",
    )
    cpus_enabled: Optional[Any] = Field(
        None,
        description="The number of enabled CPU cores.",
    )
    cpus_lowest_scaled_value: Optional[Any] = Field(
        None,
        description="The lowest value to which cpus can be scaled down.",
    )
    data_storage_size_in_gbs: Optional[float] = Field(
        None,
        description="The total data storage allocated in GBs.",
    )
    data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The total data storage allocated in TBs",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage allocated in GBs.",
    )
    db_servers: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ of the Db servers.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this AutonomousVmClusterSummary. The user-friendly name for the Autonomous VM cluster. The name does not need to be unique.",
    )
    exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the exadata_infrastructure_id of this AutonomousVmClusterSummary. The `OCID`__ of the Exadata infrastructure.",
    )
    exadata_storage_in_tbs_lowest_scaled_value: Optional[float] = Field(
        None,
        description="The lowest value to which exadataStorage(in TBs) can be scaled down.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousVmClusterSummary. The `OCID`__ of the Autonomous VM cluster.",
    )
    is_local_backup_enabled: Optional[Any] = Field(
        None,
        description="If true, database backup on local Exadata storage is configured for the Autonomous VM cluster. If false, database backup on local Exadata storage is not available in the Autonomous VM cluster.",
    )
    is_mtls_enabled: Optional[Any] = Field(
        None,
        description="Enable mutual TLS(mTLS) authentication for database while provisioning a VMCluster. Default is TLS.",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to the Autonomous VM cluster. The default is LICENSE_INCLUDED. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousVmClusterSummary. The current state of the Autonomous VM cluster. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="",
    )
    max_acds_lowest_scaled_value: Optional[Any] = Field(
        None,
        description="The lowest value to which maximum number of ACDs can be scaled down.",
    )
    memory_per_oracle_compute_unit_in_gbs: Optional[Any] = Field(
        None,
        description="The amount of memory (in GBs) to be enabled per OCPU or ECPU.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory allocated in GBs.",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    node_count: Optional[Any] = Field(
        None,
        description="The number of nodes in the Autonomous VM Cluster.",
    )
    non_provisionable_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of non-provisionable Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    ocpus_enabled: Optional[float] = Field(
        None,
        description="The number of enabled OCPU cores.",
    )
    provisionable_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="**Deprecated.** Use field totalContainerDatabases.",
    )
    provisioned_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of provisioned Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    provisioned_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs provisioned in an Autonomous VM Cluster.",
    )
    reclaimable_cpus: Optional[Any] = Field(
        None,
        description="CPUs that continue to be included in the count of CPUs available to the Autonomous Container Database even after one of its Autonomous Database is terminated or scaled down. You can release them to the available CPUs at its parent Autonomous VM Cluster level by restarting the Autonomous Container Database.",
    )
    reserved_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs reserved in an Autonomous VM Cluster.",
    )
    scan_listener_port_non_tls: Optional[Any] = Field(
        None,
        description="The SCAN Listener Non TLS port number. Default value is 1521.",
    )
    scan_listener_port_tls: Optional[Any] = Field(
        None,
        description="The SCAN Listener TLS port number. Default value is 2484.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the Autonomous VM cluster was created.",
    )
    time_database_ssl_certificate_expires: Optional[Any] = Field(
        None,
        description="The date and time of the Database SSL certificate expiration.",
    )
    time_ords_certificate_expires: Optional[Any] = Field(
        None,
        description="The date and time of the ORDS certificate expiration.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone to use for the Autonomous VM cluster. For details, see `DB System Time Zones`__.",
    )
    total_autonomous_data_storage_in_tbs: Optional[float] = Field(
        None,
        description="The total data disk group size for Autonomous Databases, in TBs.",
    )
    total_container_databases: Optional[Any] = Field(
        None,
        description="The total number of Autonomous Container Databases that can be created.",
    )
    vm_cluster_network_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the vm_cluster_network_id of this AutonomousVmClusterSummary. The `OCID`__ of the VM cluster network.",
    )


def map_autonomousvmclustersummary(
    o: oci.database.models.AutonomousVmClusterSummary,
) -> AutonomousVmClusterSummary | None:
    """Map oci.database.models.AutonomousVmClusterSummary → AutonomousVmClusterSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousVmClusterSummary(**data)
    except Exception:
        return AutonomousVmClusterSummary(
            autonomous_data_storage_percentage=getattr(
                o, "autonomous_data_storage_percentage", None
            ),
            autonomous_data_storage_size_in_tbs=getattr(
                o, "autonomous_data_storage_size_in_tbs", None
            ),
            available_autonomous_data_storage_size_in_tbs=getattr(
                o, "available_autonomous_data_storage_size_in_tbs", None
            ),
            available_container_databases=getattr(
                o, "available_container_databases", None
            ),
            available_cpus=getattr(o, "available_cpus", None),
            available_data_storage_size_in_tbs=getattr(
                o, "available_data_storage_size_in_tbs", None
            ),
            compartment_id=getattr(o, "compartment_id", None),
            compute_model=getattr(o, "compute_model", None),
            cpu_core_count_per_node=getattr(o, "cpu_core_count_per_node", None),
            cpu_percentage=getattr(o, "cpu_percentage", None),
            cpus_enabled=getattr(o, "cpus_enabled", None),
            cpus_lowest_scaled_value=getattr(o, "cpus_lowest_scaled_value", None),
            data_storage_size_in_gbs=getattr(o, "data_storage_size_in_gbs", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_servers=getattr(o, "db_servers", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            exadata_infrastructure_id=getattr(o, "exadata_infrastructure_id", None),
            exadata_storage_in_tbs_lowest_scaled_value=getattr(
                o, "exadata_storage_in_tbs_lowest_scaled_value", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_local_backup_enabled=getattr(o, "is_local_backup_enabled", None),
            is_mtls_enabled=getattr(o, "is_mtls_enabled", None),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            max_acds_lowest_scaled_value=getattr(
                o, "max_acds_lowest_scaled_value", None
            ),
            memory_per_oracle_compute_unit_in_gbs=getattr(
                o, "memory_per_oracle_compute_unit_in_gbs", None
            ),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            node_count=getattr(o, "node_count", None),
            non_provisionable_autonomous_container_databases=getattr(
                o, "non_provisionable_autonomous_container_databases", None
            ),
            ocpus_enabled=getattr(o, "ocpus_enabled", None),
            provisionable_autonomous_container_databases=getattr(
                o, "provisionable_autonomous_container_databases", None
            ),
            provisioned_autonomous_container_databases=getattr(
                o, "provisioned_autonomous_container_databases", None
            ),
            provisioned_cpus=getattr(o, "provisioned_cpus", None),
            reclaimable_cpus=getattr(o, "reclaimable_cpus", None),
            reserved_cpus=getattr(o, "reserved_cpus", None),
            scan_listener_port_non_tls=getattr(o, "scan_listener_port_non_tls", None),
            scan_listener_port_tls=getattr(o, "scan_listener_port_tls", None),
            time_created=getattr(o, "time_created", None),
            time_database_ssl_certificate_expires=getattr(
                o, "time_database_ssl_certificate_expires", None
            ),
            time_ords_certificate_expires=getattr(
                o, "time_ords_certificate_expires", None
            ),
            time_zone=getattr(o, "time_zone", None),
            total_autonomous_data_storage_in_tbs=getattr(
                o, "total_autonomous_data_storage_in_tbs", None
            ),
            total_container_databases=getattr(o, "total_container_databases", None),
            vm_cluster_network_id=getattr(o, "vm_cluster_network_id", None),
        )


class BackupDestinationSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.BackupDestinationSummary."""

    associated_databases: Optional[Any] = Field(
        None,
        description="List of databases associated with the backup destination.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    connection_string: Optional[Any] = Field(
        None,
        description="For a RECOVERY_APPLIANCE backup destination, the connection string for connecting to the Recovery Appliance.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-provided name of the backup destination.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the backup destination.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="A descriptive text associated with the lifecycleState. Typically contains additional displayable text",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current lifecycle state of the backup destination. Allowed values for this property are: "ACTIVE", "FAILED", "DELETED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    local_mount_point_path: Optional[Any] = Field(
        None,
        description="The local directory path on each VM cluster node where the NFS server location is mounted. The local directory path and the NFS server location must each be the same across all of the VM cluster nodes. Ensure that the NFS mount is maintained continuously on all of the VM cluster nodes.",
    )
    nfs_mount_type: Optional[Any] = Field(
        None,
        description="NFS Mount type for backup destination. Allowed values for this property are: \"SELF_MOUNT\", \"AUTOMATED_MOUNT\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    nfs_server: Optional[Any] = Field(
        None,
        description="Host names or IP addresses for NFS Auto mount.",
    )
    nfs_server_export: Optional[Any] = Field(
        None,
        description="Specifies the directory on which to mount the file system",
    )
    time_at_which_storage_details_are_updated: Optional[Any] = Field(
        None,
        description="The time when the total storage size and the utilized storage size of the backup destination are updated.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the backup destination was created.",
    )
    total_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The total storage size of the backup destination in GBs, rounded to the nearest integer.",
    )
    type: Optional[Any] = Field(
        None,
        description="Type of the backup destination. Allowed values for this property are: \"NFS\", \"RECOVERY_APPLIANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    utilized_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The total amount of space utilized on the backup destination (in GBs), rounded to the nearest integer.",
    )
    vpc_users: Optional[Any] = Field(
        None,
        description="For a RECOVERY_APPLIANCE backup destination, the Virtual Private Catalog (VPC) users that are used to access the Recovery Appliance.",
    )


def map_backupdestinationsummary(
    o: oci.database.models.BackupDestinationSummary,
) -> BackupDestinationSummary | None:
    """Map oci.database.models.BackupDestinationSummary → BackupDestinationSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return BackupDestinationSummary(**data)
    except Exception:
        return BackupDestinationSummary(
            associated_databases=getattr(o, "associated_databases", None),
            compartment_id=getattr(o, "compartment_id", None),
            connection_string=getattr(o, "connection_string", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            local_mount_point_path=getattr(o, "local_mount_point_path", None),
            nfs_mount_type=getattr(o, "nfs_mount_type", None),
            nfs_server=getattr(o, "nfs_server", None),
            nfs_server_export=getattr(o, "nfs_server_export", None),
            time_at_which_storage_details_are_updated=getattr(
                o, "time_at_which_storage_details_are_updated", None
            ),
            time_created=getattr(o, "time_created", None),
            total_storage_size_in_gbs=getattr(o, "total_storage_size_in_gbs", None),
            type=getattr(o, "type", None),
            utilized_storage_size_in_gbs=getattr(
                o, "utilized_storage_size_in_gbs", None
            ),
            vpc_users=getattr(o, "vpc_users", None),
        )


class BackupSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.BackupSummary."""

    availability_domain: Optional[Any] = Field(
        None,
        description="The name of the availability domain where the database backup is stored.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    database_edition: Optional[Any] = Field(
        None,
        description='The Oracle Database edition of the DB system from which the database backup was taken. Allowed values for this property are: "STANDARD_EDITION", "ENTERPRISE_EDITION", "ENTERPRISE_EDITION_HIGH_PERFORMANCE", "ENTERPRISE_EDITION_EXTREME_PERFORMANCE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    database_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the database.",
    )
    database_size_in_gbs: Optional[float] = Field(
        None,
        description="The size of the database in gigabytes at the time the backup was taken.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the backup. The name does not have to be unique.",
    )
    encryption_key_location_details: Optional[Any] = Field(
        None,
        description="",
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the backup.",
    )
    key_store_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the key store of Oracle Vault.",
    )
    key_store_wallet_name: Optional[Any] = Field(
        None,
        description="The wallet name for Oracle Key Vault.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    kms_key_version_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container version that is used in database transparent data encryption (TDE) operations KMS Key can have multiple key versions. If none is specified, the current key version (latest) of the Key Id is used for the operation. Autonomous Database Serverless does not use key versions, hence is not applicable for Autonomous Database Serverless instances.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the backup. Allowed values for this property are: "CREATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "RESTORING", "CANCELING", "CANCELED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    shape: Optional[Any] = Field(
        None,
        description="Shape of the backup's source database.",
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time the backup was completed.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="The date and time the backup started.",
    )
    type: Optional[Any] = Field(
        None,
        description='The type of backup. Allowed values for this property are: "INCREMENTAL", "FULL", "VIRTUAL_FULL", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    vault_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Oracle Cloud Infrastructure `vault`__. This parameter and `secretId` are required for Customer Managed Keys.",
    )
    version: Optional[Any] = Field(
        None,
        description="Version of the backup's source database",
    )


def map_backupsummary(o: oci.database.models.BackupSummary) -> BackupSummary | None:
    """Map oci.database.models.BackupSummary → BackupSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return BackupSummary(**data)
    except Exception:
        return BackupSummary(
            availability_domain=getattr(o, "availability_domain", None),
            compartment_id=getattr(o, "compartment_id", None),
            database_edition=getattr(o, "database_edition", None),
            database_id=getattr(o, "database_id", None),
            database_size_in_gbs=getattr(o, "database_size_in_gbs", None),
            display_name=getattr(o, "display_name", None),
            encryption_key_location_details=getattr(
                o, "encryption_key_location_details", None
            ),
            id=getattr(o, "id", None),
            key_store_id=getattr(o, "key_store_id", None),
            key_store_wallet_name=getattr(o, "key_store_wallet_name", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            kms_key_version_id=getattr(o, "kms_key_version_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            shape=getattr(o, "shape", None),
            time_ended=getattr(o, "time_ended", None),
            time_started=getattr(o, "time_started", None),
            type=getattr(o, "type", None),
            vault_id=getattr(o, "vault_id", None),
            version=getattr(o, "version", None),
        )


class CloudAutonomousVmClusterSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.CloudAutonomousVmClusterSummary."""

    autonomous_data_storage_percentage: Optional[float] = Field(
        None,
        description="The percentage of the data storage used for the Autonomous Databases in an Autonomous VM Cluster.",
    )
    autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size allocated for Autonomous Databases, in TBs.",
    )
    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this CloudAutonomousVmClusterSummary. The name of the availability domain that the cloud Autonomous VM cluster is located in.",
    )
    available_autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size available for Autonomous Databases, in TBs.",
    )
    available_container_databases: Optional[Any] = Field(
        None,
        description="The number of Autonomous Container Databases that can be created with the currently available local storage.",
    )
    available_cpus: Optional[float] = Field(
        None,
        description="CPU cores available for allocation to Autonomous Databases.",
    )
    cloud_exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cloud_exadata_infrastructure_id of this CloudAutonomousVmClusterSummary. The `OCID`__ of the cloud Exadata infrastructure.",
    )
    cluster_time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the Cloud Autonomous VM Cluster.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this CloudAutonomousVmClusterSummary. The `OCID`__ of the compartment.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Cloud Autonomous VM Cluster. ECPU compute model is the recommended model and OCPU compute model is legacy. See `Compute Models in Autonomous Database on Dedicated Exadata #Infrastructure`__ for more details. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="The number of CPU cores on the cloud Autonomous VM cluster.",
    )
    cpu_core_count_per_node: Optional[Any] = Field(
        None,
        description="The number of CPU cores enabled per VM cluster node.",
    )
    cpu_percentage: Optional[float] = Field(
        None,
        description="The percentage of total number of CPUs used in an Autonomous VM Cluster.",
    )
    data_storage_size_in_gbs: Optional[float] = Field(
        None,
        description="The total data storage allocated, in gigabytes (GB).",
    )
    data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The total data storage allocated, in terabytes (TB).",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage allocated in GBs.",
    )
    db_servers: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ of the Db servers.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    description: Optional[Any] = Field(
        None,
        description="User defined description of the cloud Autonomous VM cluster.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this CloudAutonomousVmClusterSummary. The user-friendly name for the cloud Autonomous VM cluster. The name does not need to be unique.",
    )
    domain: Optional[Any] = Field(
        None,
        description="The domain name for the cloud Autonomous VM cluster.",
    )
    exadata_storage_in_tbs_lowest_scaled_value: Optional[float] = Field(
        None,
        description="The lowest value to which exadataStorage (in TBs) can be scaled down.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    hostname: Optional[Any] = Field(
        None,
        description="The hostname for the cloud Autonomous VM cluster.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this CloudAutonomousVmClusterSummary. The `OCID`__ of the Cloud Autonomous VM cluster.",
    )
    is_mtls_enabled_vm_cluster: Optional[Any] = Field(
        None,
        description="Enable mutual TLS(mTLS) authentication for database at time of provisioning a VMCluster. This is applicable to database TLS Certificates only. Default is TLS",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    last_update_history_entry_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance update history. This value is updated when a maintenance update starts.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to the Oracle Autonomous Database. Bring your own license (BYOL) allows you to apply your current on-premises Oracle software licenses to equivalent, highly automated Oracle services in the cloud. License Included allows you to subscribe to new Oracle Database software licenses and the Oracle Database service. Note that when provisioning an `Autonomous Database on dedicated Exadata infrastructure`__, this attribute must be null. It is already set at the Autonomous Exadata Infrastructure level. When provisioning an `Autonomous Database Serverless]`__ database, if a value is not specified, the system defaults the value to `BRING_YOUR_OWN_LICENSE`. Bring your own license (BYOL) also allows you to select the DB edition using the optional parameter. This cannot be updated in parallel with any of the following: cpuCoreCount, computeCount, dataStorageSizeInTBs, adminPassword, isMTLSConnectionRequired, dbWorkload, privateEndpointLabel, nsgIds, dbVersion, dbName, scheduledOperations, dbToolsDetails, or isFreeTier. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this CloudAutonomousVmClusterSummary. The current state of the cloud Autonomous VM cluster. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="",
    )
    max_acds_lowest_scaled_value: Optional[Any] = Field(
        None,
        description="The lowest value to which maximum number of ACDs can be scaled down.",
    )
    memory_per_oracle_compute_unit_in_gbs: Optional[Any] = Field(
        None,
        description="The amount of memory (in GBs) enabled per OCPU or ECPU.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory allocated in GBs.",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    node_count: Optional[Any] = Field(
        None,
        description="The number of database servers in the cloud VM cluster.",
    )
    non_provisionable_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of non-provisionable Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    nsg_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ for the network security groups (NSGs) to which this resource belongs. Setting this to an empty list removes all resources from all NSGs. For more information about NSGs, see `Security Rules`__. **NsgIds restrictions:** - A network security group (NSG) is optional for Autonomous Databases with private access. The nsgIds list can be empty.",
    )
    ocpu_count: Optional[float] = Field(
        None,
        description="The number of CPU cores on the cloud Autonomous VM cluster. Only 1 decimal place is allowed for the fractional part.",
    )
    ocpus_lowest_scaled_value: Optional[Any] = Field(
        None,
        description="The lowest value to which ocpus can be scaled down.",
    )
    provisionable_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of provisionable Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    provisioned_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of provisioned Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    provisioned_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs provisioned in an Autonomous VM Cluster.",
    )
    reclaimable_cpus: Optional[float] = Field(
        None,
        description="CPUs that continue to be included in the count of CPUs available to the Autonomous Container Database even after one of its Autonomous Database is terminated or scaled down. You can release them to the available CPUs at its parent Autonomous VM Cluster level by restarting the Autonomous Container Database.",
    )
    reserved_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs reserved in an Autonomous VM Cluster.",
    )
    scan_listener_port_non_tls: Optional[Any] = Field(
        None,
        description="The SCAN Listener Non TLS port. Default is 1521.",
    )
    scan_listener_port_tls: Optional[Any] = Field(
        None,
        description="The SCAN Listenenr TLS port. Default is 2484.",
    )
    security_attributes: Optional[Any] = Field(
        None,
        description='Security Attributes for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. Example: `{"Oracle-ZPR": {"MaxEgressCount": {"value": "42", "mode": "audit"}}}`',
    )
    shape: Optional[Any] = Field(
        None,
        description="The model name of the Exadata hardware running the cloud Autonomous VM cluster.",
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the subnet_id of this CloudAutonomousVmClusterSummary. The `OCID`__ of the subnet the cloud Autonomous VM Cluster is associated with. **Subnet Restrictions:** - For Exadata and virtual machine 2-node RAC DB systems, do not use a subnet that overlaps with 192.168.128.0/20. These subnets are used by the Oracle Clusterware private interconnect on the database instance. Specifying an overlapping subnet will cause the private interconnect to malfunction. This restriction applies to both the client subnet and backup subnet.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the cloud Autonomous VM cluster was created.",
    )
    time_database_ssl_certificate_expires: Optional[Any] = Field(
        None,
        description="The date and time of Database SSL certificate expiration.",
    )
    time_ords_certificate_expires: Optional[Any] = Field(
        None,
        description="The date and time of ORDS certificate expiration.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The last date and time that the cloud Autonomous VM cluster was updated.",
    )
    total_autonomous_data_storage_in_tbs: Optional[float] = Field(
        None,
        description="The total data disk group size for Autonomous Databases, in TBs.",
    )
    total_container_databases: Optional[Any] = Field(
        None,
        description="The total number of Autonomous Container Databases that can be created with the allocated local storage.",
    )
    total_cpus: Optional[float] = Field(
        None,
        description="The total number of CPUs in an Autonomous VM Cluster.",
    )


def map_cloudautonomousvmclustersummary(
    o: oci.database.models.CloudAutonomousVmClusterSummary,
) -> CloudAutonomousVmClusterSummary | None:
    """Map oci.database.models.CloudAutonomousVmClusterSummary → CloudAutonomousVmClusterSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return CloudAutonomousVmClusterSummary(**data)
    except Exception:
        return CloudAutonomousVmClusterSummary(
            autonomous_data_storage_percentage=getattr(
                o, "autonomous_data_storage_percentage", None
            ),
            autonomous_data_storage_size_in_tbs=getattr(
                o, "autonomous_data_storage_size_in_tbs", None
            ),
            availability_domain=getattr(o, "availability_domain", None),
            available_autonomous_data_storage_size_in_tbs=getattr(
                o, "available_autonomous_data_storage_size_in_tbs", None
            ),
            available_container_databases=getattr(
                o, "available_container_databases", None
            ),
            available_cpus=getattr(o, "available_cpus", None),
            cloud_exadata_infrastructure_id=getattr(
                o, "cloud_exadata_infrastructure_id", None
            ),
            cluster_time_zone=getattr(o, "cluster_time_zone", None),
            compartment_id=getattr(o, "compartment_id", None),
            compute_model=getattr(o, "compute_model", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            cpu_core_count_per_node=getattr(o, "cpu_core_count_per_node", None),
            cpu_percentage=getattr(o, "cpu_percentage", None),
            data_storage_size_in_gbs=getattr(o, "data_storage_size_in_gbs", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_servers=getattr(o, "db_servers", None),
            defined_tags=getattr(o, "defined_tags", None),
            description=getattr(o, "description", None),
            display_name=getattr(o, "display_name", None),
            domain=getattr(o, "domain", None),
            exadata_storage_in_tbs_lowest_scaled_value=getattr(
                o, "exadata_storage_in_tbs_lowest_scaled_value", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            hostname=getattr(o, "hostname", None),
            id=getattr(o, "id", None),
            is_mtls_enabled_vm_cluster=getattr(o, "is_mtls_enabled_vm_cluster", None),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            last_update_history_entry_id=getattr(
                o, "last_update_history_entry_id", None
            ),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            max_acds_lowest_scaled_value=getattr(
                o, "max_acds_lowest_scaled_value", None
            ),
            memory_per_oracle_compute_unit_in_gbs=getattr(
                o, "memory_per_oracle_compute_unit_in_gbs", None
            ),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            node_count=getattr(o, "node_count", None),
            non_provisionable_autonomous_container_databases=getattr(
                o, "non_provisionable_autonomous_container_databases", None
            ),
            nsg_ids=getattr(o, "nsg_ids", None),
            ocpu_count=getattr(o, "ocpu_count", None),
            ocpus_lowest_scaled_value=getattr(o, "ocpus_lowest_scaled_value", None),
            provisionable_autonomous_container_databases=getattr(
                o, "provisionable_autonomous_container_databases", None
            ),
            provisioned_autonomous_container_databases=getattr(
                o, "provisioned_autonomous_container_databases", None
            ),
            provisioned_cpus=getattr(o, "provisioned_cpus", None),
            reclaimable_cpus=getattr(o, "reclaimable_cpus", None),
            reserved_cpus=getattr(o, "reserved_cpus", None),
            scan_listener_port_non_tls=getattr(o, "scan_listener_port_non_tls", None),
            scan_listener_port_tls=getattr(o, "scan_listener_port_tls", None),
            security_attributes=getattr(o, "security_attributes", None),
            shape=getattr(o, "shape", None),
            subnet_id=getattr(o, "subnet_id", None),
            time_created=getattr(o, "time_created", None),
            time_database_ssl_certificate_expires=getattr(
                o, "time_database_ssl_certificate_expires", None
            ),
            time_ords_certificate_expires=getattr(
                o, "time_ords_certificate_expires", None
            ),
            time_updated=getattr(o, "time_updated", None),
            total_autonomous_data_storage_in_tbs=getattr(
                o, "total_autonomous_data_storage_in_tbs", None
            ),
            total_container_databases=getattr(o, "total_container_databases", None),
            total_cpus=getattr(o, "total_cpus", None),
        )


class CloudExadataInfrastructureSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.CloudExadataInfrastructureSummary."""

    activated_storage_count: Optional[Any] = Field(
        None,
        description="The requested number of additional storage servers activated for the Exadata infrastructure.",
    )
    additional_storage_count: Optional[Any] = Field(
        None,
        description="The requested number of additional storage servers for the Exadata infrastructure.",
    )
    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this CloudExadataInfrastructureSummary. The name of the availability domain that the cloud Exadata infrastructure resource is located in.",
    )
    available_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The available storage can be allocated to the cloud Exadata infrastructure resource, in gigabytes (GB).",
    )
    cluster_placement_group_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the cluster placement group of the Exadata Infrastructure.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this CloudExadataInfrastructureSummary. The `OCID`__ of the compartment.",
    )
    compute_count: Optional[Any] = Field(
        None,
        description="The number of compute servers for the cloud Exadata infrastructure.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    cpu_count: Optional[Any] = Field(
        None,
        description="The total number of CPU cores allocated.",
    )
    customer_contacts: Optional[Any] = Field(
        None,
        description="The list of customer email addresses that receive information from Oracle about the specified OCI Database service resource. Oracle uses these email addresses to send notifications about planned and unplanned software maintenance updates, information about system hardware, and other information needed by administrators. Up to 10 email addresses can be added to the customer contacts for a cloud Exadata infrastructure instance.",
    )
    data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="Size, in terabytes, of the DATA disk group.",
    )
    database_server_type: Optional[Any] = Field(
        None,
        description="The database server type of the Exadata infrastructure.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage allocated in GBs.",
    )
    db_server_version: Optional[Any] = Field(
        None,
        description="The software version of the database servers (dom0) in the cloud Exadata infrastructure. Example: 20.1.15",
    )
    defined_file_system_configurations: Optional[Any] = Field(
        None,
        description="Details of the file system configuration of the Exadata infrastructure.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this CloudExadataInfrastructureSummary. The user-friendly name for the cloud Exadata infrastructure resource. The name does not need to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this CloudExadataInfrastructureSummary. The `OCID`__ of the cloud Exadata infrastructure resource.",
    )
    is_scheduling_policy_associated: Optional[Any] = Field(
        None,
        description="If true, the infrastructure is using granular maintenance scheduling preference.",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this CloudExadataInfrastructureSummary. The current lifecycle state of the cloud Exadata infrastructure resource. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="",
    )
    max_cpu_count: Optional[Any] = Field(
        None,
        description="The total number of CPU cores available.",
    )
    max_data_storage_in_tbs: Optional[float] = Field(
        None,
        description="The total available DATA disk group size.",
    )
    max_db_node_storage_in_gbs: Optional[Any] = Field(
        None,
        description="The total local node storage available in GBs.",
    )
    max_memory_in_gbs: Optional[Any] = Field(
        None,
        description="The total memory available in GBs.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory allocated in GBs.",
    )
    monthly_db_server_version: Optional[Any] = Field(
        None,
        description="The monthly software version of the database servers (dom0) in the cloud Exadata infrastructure. Example: 20.1.15",
    )
    monthly_storage_server_version: Optional[Any] = Field(
        None,
        description="The monthly software version of the storage servers (cells) in the cloud Exadata infrastructure. Example: 20.1.15",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    shape: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the shape of this CloudExadataInfrastructureSummary. The model name of the cloud Exadata infrastructure resource.",
    )
    storage_count: Optional[Any] = Field(
        None,
        description="The number of storage servers for the cloud Exadata infrastructure.",
    )
    storage_server_type: Optional[Any] = Field(
        None,
        description="The storage server type of the Exadata infrastructure.",
    )
    storage_server_version: Optional[Any] = Field(
        None,
        description="The software version of the storage servers (cells) in the cloud Exadata infrastructure. Example: 20.1.15",
    )
    subscription_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the subscription with which resource needs to be associated with.",
    )
    system_tags: Optional[Any] = Field(
        None,
        description="System tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the cloud Exadata infrastructure resource was created.",
    )
    total_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The total storage allocated to the cloud Exadata infrastructure resource, in gigabytes (GB).",
    )


def map_cloudexadatainfrastructuresummary(
    o: oci.database.models.CloudExadataInfrastructureSummary,
) -> CloudExadataInfrastructureSummary | None:
    """Map oci.database.models.CloudExadataInfrastructureSummary → CloudExadataInfrastructureSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return CloudExadataInfrastructureSummary(**data)
    except Exception:
        return CloudExadataInfrastructureSummary(
            activated_storage_count=getattr(o, "activated_storage_count", None),
            additional_storage_count=getattr(o, "additional_storage_count", None),
            availability_domain=getattr(o, "availability_domain", None),
            available_storage_size_in_gbs=getattr(
                o, "available_storage_size_in_gbs", None
            ),
            cluster_placement_group_id=getattr(o, "cluster_placement_group_id", None),
            compartment_id=getattr(o, "compartment_id", None),
            compute_count=getattr(o, "compute_count", None),
            compute_model=getattr(o, "compute_model", None),
            cpu_count=getattr(o, "cpu_count", None),
            customer_contacts=getattr(o, "customer_contacts", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            database_server_type=getattr(o, "database_server_type", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_server_version=getattr(o, "db_server_version", None),
            defined_file_system_configurations=getattr(
                o, "defined_file_system_configurations", None
            ),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_scheduling_policy_associated=getattr(
                o, "is_scheduling_policy_associated", None
            ),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            max_cpu_count=getattr(o, "max_cpu_count", None),
            max_data_storage_in_tbs=getattr(o, "max_data_storage_in_tbs", None),
            max_db_node_storage_in_gbs=getattr(o, "max_db_node_storage_in_gbs", None),
            max_memory_in_gbs=getattr(o, "max_memory_in_gbs", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            monthly_db_server_version=getattr(o, "monthly_db_server_version", None),
            monthly_storage_server_version=getattr(
                o, "monthly_storage_server_version", None
            ),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            shape=getattr(o, "shape", None),
            storage_count=getattr(o, "storage_count", None),
            storage_server_type=getattr(o, "storage_server_type", None),
            storage_server_version=getattr(o, "storage_server_version", None),
            subscription_id=getattr(o, "subscription_id", None),
            system_tags=getattr(o, "system_tags", None),
            time_created=getattr(o, "time_created", None),
            total_storage_size_in_gbs=getattr(o, "total_storage_size_in_gbs", None),
        )


class UpdateSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.UpdateSummary."""

    available_actions: Optional[Any] = Field(
        None,
        description='The possible actions performed by the update operation on the infrastructure components. Allowed values for items in this list are: "ROLLING_APPLY", "NON_ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    description: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the description of this UpdateSummary. Details of the maintenance update package.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this UpdateSummary. The `OCID`__ of the maintenance update.",
    )
    last_action: Optional[Any] = Field(
        None,
        description='The previous update action performed. Allowed values for this property are: "ROLLING_APPLY", "NON_ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Descriptive text providing additional details about the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the maintenance update. Dependent on value of `lastAction`. Allowed values for this property are: "AVAILABLE", "SUCCESS", "IN_PROGRESS", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_released: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_released of this UpdateSummary. The date and time the maintenance update was released.",
    )
    update_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the update_type of this UpdateSummary. The type of cloud VM cluster maintenance update. Allowed values for this property are: "GI_UPGRADE", "GI_PATCH", "OS_UPDATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this UpdateSummary. The version of the maintenance update package.",
    )


def map_updatesummary(o: oci.database.models.UpdateSummary) -> UpdateSummary | None:
    """Map oci.database.models.UpdateSummary → UpdateSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return UpdateSummary(**data)
    except Exception:
        return UpdateSummary(
            available_actions=getattr(o, "available_actions", None),
            description=getattr(o, "description", None),
            id=getattr(o, "id", None),
            last_action=getattr(o, "last_action", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_released=getattr(o, "time_released", None),
            update_type=getattr(o, "update_type", None),
            version=getattr(o, "version", None),
        )


class CloudVmClusterSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.CloudVmClusterSummary."""

    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this CloudVmClusterSummary. The name of the availability domain that the cloud Exadata infrastructure resource is located in.",
    )
    backup_network_nsg_ids: Optional[Any] = Field(
        None,
        description="A list of the `OCIDs`__ of the network security groups (NSGs) that the backup network of this DB system belongs to. Setting this to an empty array after the list is created removes the resource from all NSGs. For more information about NSGs, see `Security Rules`__. Applicable only to Exadata systems.",
    )
    backup_subnet_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the backup network subnet associated with the cloud VM cluster. **Subnet Restriction:** See the subnet restrictions information for **subnetId**.",
    )
    cloud_automation_update_details: Optional[Any] = Field(
        None,
        description="",
    )
    cloud_exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cloud_exadata_infrastructure_id of this CloudVmClusterSummary. The `OCID`__ of the cloud Exadata infrastructure.",
    )
    cluster_name: Optional[Any] = Field(
        None,
        description="The cluster name for cloud VM cluster. The cluster name must begin with an alphabetic character, and may contain hyphens (-). Underscores (_) are not permitted. The cluster name can be no longer than 11 characters and is not case sensitive.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this CloudVmClusterSummary. The `OCID`__ of the compartment.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cpu_core_count of this CloudVmClusterSummary. The number of CPU cores enabled on the cloud VM cluster.",
    )
    data_collection_options: Optional[Any] = Field(
        None,
        description="",
    )
    data_storage_percentage: Optional[Any] = Field(
        None,
        description="The percentage assigned to DATA storage (user data and database files). The remaining percentage is assigned to RECO storage (database redo logs, archive logs, and recovery manager backups). Accepted values are 35, 40, 60 and 80. The default is 80 percent assigned to DATA storage. See `Storage Configuration`__ in the Exadata documentation for details on the impact of the configuration settings on storage.",
    )
    data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size to be allocated in TBs.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage to be allocated in GBs.",
    )
    db_servers: Optional[Any] = Field(
        None,
        description="The list of DB servers.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    disk_redundancy: Optional[Any] = Field(
        None,
        description="The type of redundancy configured for the cloud Vm cluster. NORMAL is 2-way redundancy. HIGH is 3-way redundancy. Allowed values for this property are: \"HIGH\", \"NORMAL\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this CloudVmClusterSummary. The user-friendly name for the cloud VM cluster. The name does not need to be unique.",
    )
    domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the domain of this CloudVmClusterSummary. The domain name for the cloud VM cluster.",
    )
    file_system_configuration_details: Optional[Any] = Field(
        None,
        description="Details of the file system configuration of the VM cluster.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    gi_software_image_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of a grid infrastructure software image. This is a database software image of the type `GRID_IMAGE`.",
    )
    gi_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Grid Infrastructure (GI) software version.",
    )
    hostname: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the hostname of this CloudVmClusterSummary. The hostname for the cloud VM cluster.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this CloudVmClusterSummary. The `OCID`__ of the cloud VM cluster.",
    )
    is_local_backup_enabled: Optional[Any] = Field(
        None,
        description="If true, database backup on local Exadata storage is configured for the cloud VM cluster. If false, database backup on local Exadata storage is not available in the cloud VM cluster.",
    )
    is_sparse_diskgroup_enabled: Optional[Any] = Field(
        None,
        description="If true, sparse disk group is configured for the cloud VM cluster. If false, sparse disk group is not created.",
    )
    last_update_history_entry_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance update history entry. This value is updated when a maintenance update starts.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to the cloud VM cluster. The default is LICENSE_INCLUDED. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this CloudVmClusterSummary. The current state of the cloud VM cluster. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    listener_port: Optional[Any] = Field(
        None,
        description="The port number configured for the listener on the cloud VM cluster.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory to be allocated in GBs.",
    )
    node_count: Optional[Any] = Field(
        None,
        description="The number of nodes in the cloud VM cluster.",
    )
    nsg_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ for the network security groups (NSGs) to which this resource belongs. Setting this to an empty list removes all resources from all NSGs. For more information about NSGs, see `Security Rules`__. **NsgIds restrictions:** - A network security group (NSG) is optional for Autonomous Databases with private access. The nsgIds list can be empty.",
    )
    ocpu_count: Optional[float] = Field(
        None,
        description="The number of OCPU cores to enable on the cloud VM cluster. Only 1 decimal place is allowed for the fractional part.",
    )
    scan_dns_name: Optional[Any] = Field(
        None,
        description="The FQDN of the DNS record for the SCAN IP addresses that are associated with the cloud VM cluster.",
    )
    scan_dns_record_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the DNS record for the SCAN IP addresses that are associated with the cloud VM cluster.",
    )
    scan_ip_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Single Client Access Name (SCAN) IP addresses associated with the cloud VM cluster. SCAN IP addresses are typically used for load balancing and are not assigned to any interface. Oracle Clusterware directs the requests to the appropriate nodes in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    scan_listener_port_tcp: Optional[Any] = Field(
        None,
        description="The TCP Single Client Access Name (SCAN) port. The default port is 1521.",
    )
    scan_listener_port_tcp_ssl: Optional[Any] = Field(
        None,
        description="The TCPS Single Client Access Name (SCAN) port. The default port is 2484.",
    )
    security_attributes: Optional[Any] = Field(
        None,
        description='Security Attributes for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. Example: `{"Oracle-ZPR": {"MaxEgressCount": {"value": "42", "mode": "audit"}}}`',
    )
    shape: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the shape of this CloudVmClusterSummary. The model name of the Exadata hardware running the cloud VM cluster.",
    )
    ssh_public_keys: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the ssh_public_keys of this CloudVmClusterSummary. The public key portion of one or more key pairs used for SSH access to the cloud VM cluster.",
    )
    storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The storage allocation for the disk group, in gigabytes (GB).",
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the subnet_id of this CloudVmClusterSummary. The `OCID`__ of the subnet associated with the cloud VM cluster. **Subnet Restrictions:** - For Exadata and virtual machine 2-node RAC systems, do not use a subnet that overlaps with 192.168.128.0/20. These subnets are used by the Oracle Clusterware private interconnect on the database instance. Specifying an overlapping subnet will cause the private interconnect to malfunction. This restriction applies to both the client subnet and backup subnet.",
    )
    subscription_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the subscription with which resource needs to be associated with.",
    )
    system_tags: Optional[Any] = Field(
        None,
        description="System tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    system_version: Optional[Any] = Field(
        None,
        description="Operating system version of the image.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the cloud VM cluster was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the cloud VM cluster. For details, see `Exadata Infrastructure Time Zones`__.",
    )
    vip_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the virtual IP (VIP) addresses associated with the cloud VM cluster. The Cluster Ready Services (CRS) creates and maintains one VIP address for each node in the Exadata Cloud Service instance to enable failover. If one node fails, the VIP is reassigned to another active node in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    zone_id: Optional[Any] = Field(
        None,
        description="The OCID of the zone the cloud VM cluster is associated with.",
    )


def map_cloudvmclustersummary(
    o: oci.database.models.CloudVmClusterSummary,
) -> CloudVmClusterSummary | None:
    """Map oci.database.models.CloudVmClusterSummary → CloudVmClusterSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return CloudVmClusterSummary(**data)
    except Exception:
        return CloudVmClusterSummary(
            availability_domain=getattr(o, "availability_domain", None),
            backup_network_nsg_ids=getattr(o, "backup_network_nsg_ids", None),
            backup_subnet_id=getattr(o, "backup_subnet_id", None),
            cloud_automation_update_details=getattr(
                o, "cloud_automation_update_details", None
            ),
            cloud_exadata_infrastructure_id=getattr(
                o, "cloud_exadata_infrastructure_id", None
            ),
            cluster_name=getattr(o, "cluster_name", None),
            compartment_id=getattr(o, "compartment_id", None),
            compute_model=getattr(o, "compute_model", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            data_collection_options=getattr(o, "data_collection_options", None),
            data_storage_percentage=getattr(o, "data_storage_percentage", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_servers=getattr(o, "db_servers", None),
            defined_tags=getattr(o, "defined_tags", None),
            disk_redundancy=getattr(o, "disk_redundancy", None),
            display_name=getattr(o, "display_name", None),
            domain=getattr(o, "domain", None),
            file_system_configuration_details=getattr(
                o, "file_system_configuration_details", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            gi_software_image_id=getattr(o, "gi_software_image_id", None),
            gi_version=getattr(o, "gi_version", None),
            hostname=getattr(o, "hostname", None),
            id=getattr(o, "id", None),
            is_local_backup_enabled=getattr(o, "is_local_backup_enabled", None),
            is_sparse_diskgroup_enabled=getattr(o, "is_sparse_diskgroup_enabled", None),
            last_update_history_entry_id=getattr(
                o, "last_update_history_entry_id", None
            ),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            listener_port=getattr(o, "listener_port", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            node_count=getattr(o, "node_count", None),
            nsg_ids=getattr(o, "nsg_ids", None),
            ocpu_count=getattr(o, "ocpu_count", None),
            scan_dns_name=getattr(o, "scan_dns_name", None),
            scan_dns_record_id=getattr(o, "scan_dns_record_id", None),
            scan_ip_ids=getattr(o, "scan_ip_ids", None),
            scan_listener_port_tcp=getattr(o, "scan_listener_port_tcp", None),
            scan_listener_port_tcp_ssl=getattr(o, "scan_listener_port_tcp_ssl", None),
            security_attributes=getattr(o, "security_attributes", None),
            shape=getattr(o, "shape", None),
            ssh_public_keys=getattr(o, "ssh_public_keys", None),
            storage_size_in_gbs=getattr(o, "storage_size_in_gbs", None),
            subnet_id=getattr(o, "subnet_id", None),
            subscription_id=getattr(o, "subscription_id", None),
            system_tags=getattr(o, "system_tags", None),
            system_version=getattr(o, "system_version", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
            vip_ids=getattr(o, "vip_ids", None),
            zone_id=getattr(o, "zone_id", None),
        )


class ConsoleConnectionSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ConsoleConnectionSummary."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ConsoleConnectionSummary. The OCID of the compartment to contain the console connection.",
    )
    connection_string: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the connection_string of this ConsoleConnectionSummary. The SSH connection string for the console connection.",
    )
    db_node_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_node_id of this ConsoleConnectionSummary. The OCID of the database node.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    fingerprint: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the fingerprint of this ConsoleConnectionSummary. The SSH public key fingerprint for the console connection.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ConsoleConnectionSummary. The OCID of the console connection.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ConsoleConnectionSummary. The current state of the console connection. Allowed values for this property are: "ACTIVE", "CREATING", "DELETED", "DELETING", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    service_host_key_fingerprint: Optional[Any] = Field(
        None,
        description="The SSH public key's fingerprint for the console connection service host.",
    )


def map_consoleconnectionsummary(
    o: oci.database.models.ConsoleConnectionSummary,
) -> ConsoleConnectionSummary | None:
    """Map oci.database.models.ConsoleConnectionSummary → ConsoleConnectionSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ConsoleConnectionSummary(**data)
    except Exception:
        return ConsoleConnectionSummary(
            compartment_id=getattr(o, "compartment_id", None),
            connection_string=getattr(o, "connection_string", None),
            db_node_id=getattr(o, "db_node_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            fingerprint=getattr(o, "fingerprint", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            service_host_key_fingerprint=getattr(
                o, "service_host_key_fingerprint", None
            ),
        )


class ConsoleHistoryCollection(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ConsoleHistoryCollection."""

    items: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the items of this ConsoleHistoryCollection. List of Db Node console histories.",
    )


def map_consolehistorycollection(
    o: oci.database.models.ConsoleHistoryCollection,
) -> ConsoleHistoryCollection | None:
    """Map oci.database.models.ConsoleHistoryCollection → ConsoleHistoryCollection Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ConsoleHistoryCollection(**data)
    except Exception:
        return ConsoleHistoryCollection(
            items=getattr(o, "items", None),
        )


class AutonomousPatchSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousPatchSummary."""

    autonomous_patch_type: Optional[Any] = Field(
        None,
        description='Maintenance run type, either "QUARTERLY" or "TIMEZONE". Allowed values for this property are: "QUARTERLY", "TIMEZONE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    description: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the description of this AutonomousPatchSummary. The text describing this patch package.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousPatchSummary. The `OCID`__ of the patch.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="A descriptive text associated with the lifecycleState. Typically can contain additional displayable text.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the patch as a result of lastAction. Allowed values for this property are: "AVAILABLE", "SUCCESS", "IN_PROGRESS", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    patch_model: Optional[Any] = Field(
        None,
        description="Database patching model preference. See `My Oracle Support note 2285040.1`__ for information on the Release Update (RU) and Release Update Revision (RUR) patching models. Allowed values for this property are: \"RELEASE_UPDATES\", \"RELEASE_UPDATE_REVISIONS\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    quarter: Optional[Any] = Field(
        None,
        description="First month of the quarter in which the patch was released.",
    )
    time_released: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_released of this AutonomousPatchSummary. The date and time that the patch was released.",
    )
    type: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the type of this AutonomousPatchSummary. The type of patch. BUNDLE is one example.",
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this AutonomousPatchSummary. The version of this patch package.",
    )
    year: Optional[Any] = Field(
        None,
        description="Year in which the patch was released.",
    )


def map_autonomouspatchsummary(
    o: oci.database.models.AutonomousPatchSummary,
) -> AutonomousPatchSummary | None:
    """Map oci.database.models.AutonomousPatchSummary → AutonomousPatchSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousPatchSummary(**data)
    except Exception:
        return AutonomousPatchSummary(
            autonomous_patch_type=getattr(o, "autonomous_patch_type", None),
            description=getattr(o, "description", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            patch_model=getattr(o, "patch_model", None),
            quarter=getattr(o, "quarter", None),
            time_released=getattr(o, "time_released", None),
            type=getattr(o, "type", None),
            version=getattr(o, "version", None),
            year=getattr(o, "year", None),
        )


class DataGuardAssociationSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DataGuardAssociationSummary."""

    apply_lag: Optional[Any] = Field(
        None,
        description="The lag time between updates to the primary database and application of the redo data on the standby database, as computed by the reporting database. Example: `9 seconds`",
    )
    apply_rate: Optional[Any] = Field(
        None,
        description="The rate at which redo logs are synced between the associated databases. Example: `180 Mb per second`",
    )
    database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the database_id of this DataGuardAssociationSummary. The `OCID`__ of the reporting database.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DataGuardAssociationSummary. The `OCID`__ of the Data Guard association.",
    )
    is_active_data_guard_enabled: Optional[Any] = Field(
        None,
        description="True if active Data Guard is enabled.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycleState, if available.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DataGuardAssociationSummary. The current state of the Data Guard association. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "UPGRADING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_data_guard_association_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the peer database's Data Guard association.",
    )
    peer_database_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the associated peer database.",
    )
    peer_db_home_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Database Home containing the associated peer database.",
    )
    peer_db_system_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the peer_db_system_id of this DataGuardAssociationSummary. The `OCID`__ of the DB system containing the associated peer database.",
    )
    peer_role: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the peer_role of this DataGuardAssociationSummary. The role of the peer database in this Data Guard association. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    protection_mode: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the protection_mode of this DataGuardAssociationSummary. The protection mode of this Data Guard association. For more information, see `Oracle Data Guard Protection Modes`__ in the Oracle Data Guard documentation. Allowed values for this property are: "MAXIMUM_AVAILABILITY", "MAXIMUM_PERFORMANCE", "MAXIMUM_PROTECTION", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    role: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the role of this DataGuardAssociationSummary. The role of the reporting database in this Data Guard association. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Data Guard association was created.",
    )
    transport_type: Optional[Any] = Field(
        None,
        description='The redo transport type used by this Data Guard association. For more information, see `Redo Transport Services`__ in the Oracle Data Guard documentation. Allowed values for this property are: "SYNC", "ASYNC", "FASTSYNC", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )


def map_dataguardassociationsummary(
    o: oci.database.models.DataGuardAssociationSummary,
) -> DataGuardAssociationSummary | None:
    """Map oci.database.models.DataGuardAssociationSummary → DataGuardAssociationSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DataGuardAssociationSummary(**data)
    except Exception:
        return DataGuardAssociationSummary(
            apply_lag=getattr(o, "apply_lag", None),
            apply_rate=getattr(o, "apply_rate", None),
            database_id=getattr(o, "database_id", None),
            id=getattr(o, "id", None),
            is_active_data_guard_enabled=getattr(
                o, "is_active_data_guard_enabled", None
            ),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            peer_data_guard_association_id=getattr(
                o, "peer_data_guard_association_id", None
            ),
            peer_database_id=getattr(o, "peer_database_id", None),
            peer_db_home_id=getattr(o, "peer_db_home_id", None),
            peer_db_system_id=getattr(o, "peer_db_system_id", None),
            peer_role=getattr(o, "peer_role", None),
            protection_mode=getattr(o, "protection_mode", None),
            role=getattr(o, "role", None),
            time_created=getattr(o, "time_created", None),
            transport_type=getattr(o, "transport_type", None),
        )


class DatabaseSoftwareImageSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DatabaseSoftwareImageSummary."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this DatabaseSoftwareImageSummary. The `OCID`__ of the compartment.",
    )
    database_software_image_included_patches: Optional[Any] = Field(
        None,
        description="List of one-off patches for Database Homes.",
    )
    database_software_image_one_off_patches: Optional[Any] = Field(
        None,
        description="List of one-off patches for Database Homes.",
    )
    database_version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the database_version of this DatabaseSoftwareImageSummary. The database version with which the database software image is to be built.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this DatabaseSoftwareImageSummary. The user-friendly name for the database software image. The name does not have to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DatabaseSoftwareImageSummary. The `OCID`__ of the database software image.",
    )
    image_shape_family: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the image_shape_family of this DatabaseSoftwareImageSummary. To what shape the image is meant for. Allowed values for this property are: "VM_BM_SHAPE", "EXADATA_SHAPE", "EXACC_SHAPE", "EXADBXS_SHAPE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    image_type: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the image_type of this DatabaseSoftwareImageSummary. The type of software image. Can be grid or database. Allowed values for this property are: \"GRID_IMAGE\", \"DATABASE_IMAGE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    included_patches_summary: Optional[Any] = Field(
        None,
        description="The patches included in the image and the version of the image.",
    )
    is_upgrade_supported: Optional[Any] = Field(
        None,
        description="True if this Database software image is supported for Upgrade.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Detailed message for the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DatabaseSoftwareImageSummary. The current state of the database software image. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "DELETING", "DELETED", "FAILED", "TERMINATING", "TERMINATED", "UPDATING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    ls_inventory: Optional[Any] = Field(
        None,
        description="The output from the OPatch lsInventory command, which is passed as a string.",
    )
    patch_set: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the patch_set of this DatabaseSoftwareImageSummary. The PSU or PBP or Release Updates. To get a list of supported versions, use the :func:`list_db_versions` operation.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this DatabaseSoftwareImageSummary. The date and time the database software image was created.",
    )


def map_databasesoftwareimagesummary(
    o: oci.database.models.DatabaseSoftwareImageSummary,
) -> DatabaseSoftwareImageSummary | None:
    """Map oci.database.models.DatabaseSoftwareImageSummary → DatabaseSoftwareImageSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DatabaseSoftwareImageSummary(**data)
    except Exception:
        return DatabaseSoftwareImageSummary(
            compartment_id=getattr(o, "compartment_id", None),
            database_software_image_included_patches=getattr(
                o, "database_software_image_included_patches", None
            ),
            database_software_image_one_off_patches=getattr(
                o, "database_software_image_one_off_patches", None
            ),
            database_version=getattr(o, "database_version", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            image_shape_family=getattr(o, "image_shape_family", None),
            image_type=getattr(o, "image_type", None),
            included_patches_summary=getattr(o, "included_patches_summary", None),
            is_upgrade_supported=getattr(o, "is_upgrade_supported", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            ls_inventory=getattr(o, "ls_inventory", None),
            patch_set=getattr(o, "patch_set", None),
            time_created=getattr(o, "time_created", None),
        )


class DatabaseSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DatabaseSummary."""

    character_set: Optional[Any] = Field(
        None,
        description="The character set for the database.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this DatabaseSummary. The `OCID`__ of the compartment.",
    )
    connection_strings: Optional[Any] = Field(
        None,
        description="The Connection strings used to connect to the Oracle Database.",
    )
    data_guard_group: Optional[Any] = Field(
        None,
        description="",
    )
    database_management_config: Optional[Any] = Field(
        None,
        description="",
    )
    database_software_image_id: Optional[Any] = Field(
        None,
        description="The database software image `OCID`__",
    )
    db_backup_config: Optional[Any] = Field(
        None,
        description="",
    )
    db_home_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Database Home.",
    )
    db_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_name of this DatabaseSummary. The database name.",
    )
    db_system_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the DB system.",
    )
    db_unique_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_unique_name of this DatabaseSummary. A system-generated name for the database to ensure uniqueness within an Oracle Data Guard group (a primary database and its standby databases). The unique name cannot be changed.",
    )
    db_workload: Optional[Any] = Field(
        None,
        description="**Deprecated.** The dbWorkload field has been deprecated for Exadata Database Service on Dedicated Infrastructure, Exadata Database Service on Cloud@Customer, and Base Database Service. Support for this attribute will end in November 2023. You may choose to update your custom scripts to exclude the dbWorkload attribute. After November 2023 if you pass a value to the dbWorkload attribute, it will be ignored. The database workload type.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    encryption_key_location_details: Optional[Any] = Field(
        None,
        description="",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DatabaseSummary. The `OCID`__ of the database.",
    )
    is_cdb: Optional[Any] = Field(
        None,
        description="True if the database is a container database.",
    )
    key_store_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the key store of Oracle Vault.",
    )
    key_store_wallet_name: Optional[Any] = Field(
        None,
        description="The wallet name for Oracle Key Vault.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    kms_key_version_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container version that is used in database transparent data encryption (TDE) operations KMS Key can have multiple key versions. If none is specified, the current key version (latest) of the Key Id is used for the operation. Autonomous Database Serverless does not use key versions, hence is not applicable for Autonomous Database Serverless instances.",
    )
    last_backup_duration_in_seconds: Optional[Any] = Field(
        None,
        description="The duration when the latest database backup created.",
    )
    last_backup_timestamp: Optional[Any] = Field(
        None,
        description="The date and time when the latest database backup was created.",
    )
    last_failed_backup_timestamp: Optional[Any] = Field(
        None,
        description="The date and time when the latest database backup failed.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DatabaseSummary. The current state of the database. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "BACKUP_IN_PROGRESS", "UPGRADING", "CONVERTING", "TERMINATING", "TERMINATED", "RESTORE_FAILED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    ncharacter_set: Optional[Any] = Field(
        None,
        description="The national character set for the database.",
    )
    pdb_name: Optional[Any] = Field(
        None,
        description="The name of the pluggable database. The name must begin with an alphabetic character and can contain a maximum of thirty alphanumeric characters. Special characters are not permitted. Pluggable database should not be same as database name.",
    )
    sid_prefix: Optional[Any] = Field(
        None,
        description="Specifies a prefix for the `Oracle SID` of the database to be created.",
    )
    source_database_point_in_time_recovery_timestamp: Optional[Any] = Field(
        None,
        description="Point in time recovery timeStamp of the source database at which cloned database system is cloned from the source database system, as described in `RFC 3339`__",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the database was created.",
    )
    vault_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Oracle Cloud Infrastructure `vault`__. This parameter and `secretId` are required for Customer Managed Keys.",
    )
    vm_cluster_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the VM cluster.",
    )


def map_databasesummary(
    o: oci.database.models.DatabaseSummary,
) -> DatabaseSummary | None:
    """Map oci.database.models.DatabaseSummary → DatabaseSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DatabaseSummary(**data)
    except Exception:
        return DatabaseSummary(
            character_set=getattr(o, "character_set", None),
            compartment_id=getattr(o, "compartment_id", None),
            connection_strings=getattr(o, "connection_strings", None),
            data_guard_group=getattr(o, "data_guard_group", None),
            database_management_config=getattr(o, "database_management_config", None),
            database_software_image_id=getattr(o, "database_software_image_id", None),
            db_backup_config=getattr(o, "db_backup_config", None),
            db_home_id=getattr(o, "db_home_id", None),
            db_name=getattr(o, "db_name", None),
            db_system_id=getattr(o, "db_system_id", None),
            db_unique_name=getattr(o, "db_unique_name", None),
            db_workload=getattr(o, "db_workload", None),
            defined_tags=getattr(o, "defined_tags", None),
            encryption_key_location_details=getattr(
                o, "encryption_key_location_details", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_cdb=getattr(o, "is_cdb", None),
            key_store_id=getattr(o, "key_store_id", None),
            key_store_wallet_name=getattr(o, "key_store_wallet_name", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            kms_key_version_id=getattr(o, "kms_key_version_id", None),
            last_backup_duration_in_seconds=getattr(
                o, "last_backup_duration_in_seconds", None
            ),
            last_backup_timestamp=getattr(o, "last_backup_timestamp", None),
            last_failed_backup_timestamp=getattr(
                o, "last_failed_backup_timestamp", None
            ),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            ncharacter_set=getattr(o, "ncharacter_set", None),
            pdb_name=getattr(o, "pdb_name", None),
            sid_prefix=getattr(o, "sid_prefix", None),
            source_database_point_in_time_recovery_timestamp=getattr(
                o, "source_database_point_in_time_recovery_timestamp", None
            ),
            time_created=getattr(o, "time_created", None),
            vault_id=getattr(o, "vault_id", None),
            vm_cluster_id=getattr(o, "vm_cluster_id", None),
        )


class PatchHistoryEntrySummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.PatchHistoryEntrySummary."""

    action: Optional[Any] = Field(
        None,
        description="The action being performed or was completed. Allowed values for this property are: \"APPLY\", \"PRECHECK\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this PatchHistoryEntrySummary. The `OCID`__ of the patch history entry.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="A descriptive text associated with the lifecycleState. Typically contains additional displayable text.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this PatchHistoryEntrySummary. The current state of the action. Allowed values for this property are: "IN_PROGRESS", "SUCCEEDED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    patch_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the patch_id of this PatchHistoryEntrySummary. The `OCID`__ of the patch.",
    )
    patch_type: Optional[Any] = Field(
        None,
        description='The type of Patch operation. Allowed values for this property are: "OS", "DB", "GI", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time when the patch action completed",
    )
    time_started: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_started of this PatchHistoryEntrySummary. The date and time when the patch action started.",
    )


def map_patchhistoryentrysummary(
    o: oci.database.models.PatchHistoryEntrySummary,
) -> PatchHistoryEntrySummary | None:
    """Map oci.database.models.PatchHistoryEntrySummary → PatchHistoryEntrySummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return PatchHistoryEntrySummary(**data)
    except Exception:
        return PatchHistoryEntrySummary(
            action=getattr(o, "action", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            patch_id=getattr(o, "patch_id", None),
            patch_type=getattr(o, "patch_type", None),
            time_ended=getattr(o, "time_ended", None),
            time_started=getattr(o, "time_started", None),
        )


class PatchSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.PatchSummary."""

    available_actions: Optional[Any] = Field(
        None,
        description="Actions that can possibly be performed using this patch. Allowed values for items in this list are: \"APPLY\", \"PRECHECK\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    description: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the description of this PatchSummary. The text describing this patch package.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this PatchSummary. The `OCID`__ of the patch.",
    )
    last_action: Optional[Any] = Field(
        None,
        description="Action that is currently being performed or was completed last. Allowed values for this property are: \"APPLY\", \"PRECHECK\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="A descriptive text associated with the lifecycleState. Typically can contain additional displayable text.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the patch as a result of lastAction. Allowed values for this property are: "AVAILABLE", "SUCCESS", "IN_PROGRESS", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_released: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_released of this PatchSummary. The date and time that the patch was released.",
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this PatchSummary. The version of this patch package.",
    )


def map_patchsummary(o: oci.database.models.PatchSummary) -> PatchSummary | None:
    """Map oci.database.models.PatchSummary → PatchSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return PatchSummary(**data)
    except Exception:
        return PatchSummary(
            available_actions=getattr(o, "available_actions", None),
            description=getattr(o, "description", None),
            id=getattr(o, "id", None),
            last_action=getattr(o, "last_action", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_released=getattr(o, "time_released", None),
            version=getattr(o, "version", None),
        )


class DbHomeSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbHomeSummary."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this DbHomeSummary. The `OCID`__ of the compartment.",
    )
    database_software_image_id: Optional[Any] = Field(
        None,
        description="The database software image `OCID`__",
    )
    db_home_location: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_home_location of this DbHomeSummary. The location of the Oracle Database Home.",
    )
    db_system_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the DB system.",
    )
    db_version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_version of this DbHomeSummary. The Oracle Database version.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this DbHomeSummary. The user-provided name for the Database Home. The name does not need to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DbHomeSummary. The `OCID`__ of the Database Home.",
    )
    is_unified_auditing_enabled: Optional[Any] = Field(
        None,
        description="Indicates whether unified autiding is enabled or not.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    last_patch_history_entry_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last patch history. This value is updated as soon as a patch operation is started.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DbHomeSummary. The current state of the Database Home. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    one_off_patches: Optional[Any] = Field(
        None,
        description="List of one-off patches for Database Homes.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Database Home was created.",
    )
    vm_cluster_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the VM cluster.",
    )


def map_dbhomesummary(o: oci.database.models.DbHomeSummary) -> DbHomeSummary | None:
    """Map oci.database.models.DbHomeSummary → DbHomeSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbHomeSummary(**data)
    except Exception:
        return DbHomeSummary(
            compartment_id=getattr(o, "compartment_id", None),
            database_software_image_id=getattr(o, "database_software_image_id", None),
            db_home_location=getattr(o, "db_home_location", None),
            db_system_id=getattr(o, "db_system_id", None),
            db_version=getattr(o, "db_version", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_unified_auditing_enabled=getattr(o, "is_unified_auditing_enabled", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            last_patch_history_entry_id=getattr(o, "last_patch_history_entry_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            one_off_patches=getattr(o, "one_off_patches", None),
            time_created=getattr(o, "time_created", None),
            vm_cluster_id=getattr(o, "vm_cluster_id", None),
        )


class DbNodeSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbNodeSummary."""

    additional_details: Optional[Any] = Field(
        None,
        description="Additional information about the planned maintenance.",
    )
    backup_ip_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the backup IP address associated with the database node. Use this OCID with either the :func:`get_private_ip` or the :func:`get_public_ip_by_private_ip_id` API to get the IP address needed to make a database connection. **Note:** Applies only to Exadata Cloud Service.",
    )
    backup_vnic2_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the second backup VNIC. **Note:** Applies only to Exadata Cloud Service.",
    )
    backup_vnic_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the backup VNIC.",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="The number of CPU cores enabled on the Db node.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The allocated local node storage in GBs on the Db node.",
    )
    db_server_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Exacc Db server associated with the database node.",
    )
    db_system_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_system_id of this DbNodeSummary. The `OCID`__ of the DB system.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    fault_domain: Optional[Any] = Field(
        None,
        description="The name of the Fault Domain the instance is contained in.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    host_ip_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the host IP address associated with the database node. Use this OCID with either the :func:`get_private_ip` or the :func:`get_public_ip_by_private_ip_id` API to get the IP address needed to make a database connection. **Note:** Applies only to Exadata Cloud Service.",
    )
    hostname: Optional[Any] = Field(
        None,
        description="The host name for the database node.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DbNodeSummary. The `OCID`__ of the database node.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DbNodeSummary. The current state of the database node. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "STOPPING", "STOPPED", "STARTING", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_type: Optional[Any] = Field(
        None,
        description="The type of database node maintenance. Allowed values for this property are: \"VMDB_REBOOT_MIGRATION\", \"EXADBXS_REBOOT_MIGRATION\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The allocated memory in GBs on the Db node.",
    )
    software_storage_size_in_gb: Optional[Any] = Field(
        None,
        description="The size (in GB) of the block storage volume allocation for the DB system. This attribute applies only for virtual machine DB systems.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this DbNodeSummary. The date and time that the database node was created.",
    )
    time_maintenance_window_end: Optional[Any] = Field(
        None,
        description="End date and time of maintenance window.",
    )
    time_maintenance_window_start: Optional[Any] = Field(
        None,
        description="Start date and time of maintenance window.",
    )
    total_cpu_core_count: Optional[Any] = Field(
        None,
        description="The total number of CPU cores reserved on the Db node.",
    )
    vnic2_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the second VNIC. **Note:** Applies only to Exadata Cloud Service.",
    )
    vnic_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the vnic_id of this DbNodeSummary. The `OCID`__ of the VNIC.",
    )


def map_dbnodesummary(o: oci.database.models.DbNodeSummary) -> DbNodeSummary | None:
    """Map oci.database.models.DbNodeSummary → DbNodeSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbNodeSummary(**data)
    except Exception:
        return DbNodeSummary(
            additional_details=getattr(o, "additional_details", None),
            backup_ip_id=getattr(o, "backup_ip_id", None),
            backup_vnic2_id=getattr(o, "backup_vnic2_id", None),
            backup_vnic_id=getattr(o, "backup_vnic_id", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_server_id=getattr(o, "db_server_id", None),
            db_system_id=getattr(o, "db_system_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            fault_domain=getattr(o, "fault_domain", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            host_ip_id=getattr(o, "host_ip_id", None),
            hostname=getattr(o, "hostname", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_type=getattr(o, "maintenance_type", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            software_storage_size_in_gb=getattr(o, "software_storage_size_in_gb", None),
            time_created=getattr(o, "time_created", None),
            time_maintenance_window_end=getattr(o, "time_maintenance_window_end", None),
            time_maintenance_window_start=getattr(
                o, "time_maintenance_window_start", None
            ),
            total_cpu_core_count=getattr(o, "total_cpu_core_count", None),
            vnic2_id=getattr(o, "vnic2_id", None),
            vnic_id=getattr(o, "vnic_id", None),
        )


class DbServerSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbServerSummary."""

    autonomous_virtual_machine_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ of the Autonomous Virtual Machines associated with the Db server.",
    )
    autonomous_vm_cluster_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ of the Autonomous VM Clusters associated with the Db server.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="The number of CPU cores enabled on the Db server.",
    )
    db_node_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Db nodes associated with the Db server.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The allocated local node storage in GBs on the Db server.",
    )
    db_server_patching_details: Optional[Any] = Field(
        None,
        description="",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the Db server. The name does not need to be unique.",
    )
    exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Exadata infrastructure.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Db server.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the Db server. Allowed values for this property are: "CREATING", "AVAILABLE", "UNAVAILABLE", "DELETING", "DELETED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    max_cpu_count: Optional[Any] = Field(
        None,
        description="The total number of CPU cores available.",
    )
    max_db_node_storage_in_gbs: Optional[Any] = Field(
        None,
        description="The total local node storage available in GBs.",
    )
    max_memory_in_gbs: Optional[Any] = Field(
        None,
        description="The total memory available in GBs.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The allocated memory in GBs on the Db server.",
    )
    shape: Optional[Any] = Field(
        None,
        description="The shape of the Db server. The shape determines the amount of CPU, storage, and memory resources available.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the Db Server was created.",
    )
    vm_cluster_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the VM Clusters associated with the Db server.",
    )


def map_dbserversummary(
    o: oci.database.models.DbServerSummary,
) -> DbServerSummary | None:
    """Map oci.database.models.DbServerSummary → DbServerSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbServerSummary(**data)
    except Exception:
        return DbServerSummary(
            autonomous_virtual_machine_ids=getattr(
                o, "autonomous_virtual_machine_ids", None
            ),
            autonomous_vm_cluster_ids=getattr(o, "autonomous_vm_cluster_ids", None),
            compartment_id=getattr(o, "compartment_id", None),
            compute_model=getattr(o, "compute_model", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            db_node_ids=getattr(o, "db_node_ids", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_server_patching_details=getattr(o, "db_server_patching_details", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            exadata_infrastructure_id=getattr(o, "exadata_infrastructure_id", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            max_cpu_count=getattr(o, "max_cpu_count", None),
            max_db_node_storage_in_gbs=getattr(o, "max_db_node_storage_in_gbs", None),
            max_memory_in_gbs=getattr(o, "max_memory_in_gbs", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            shape=getattr(o, "shape", None),
            time_created=getattr(o, "time_created", None),
            vm_cluster_ids=getattr(o, "vm_cluster_ids", None),
        )


class DbSystemComputePerformanceSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbSystemComputePerformanceSummary."""

    compute_performance_list: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compute_performance_list of this DbSystemComputePerformanceSummary. List of Compute performance details for the specified DB system shape.",
    )
    shape: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the shape of this DbSystemComputePerformanceSummary. The shape of the DB system.",
    )


def map_dbsystemcomputeperformancesummary(
    o: oci.database.models.DbSystemComputePerformanceSummary,
) -> DbSystemComputePerformanceSummary | None:
    """Map oci.database.models.DbSystemComputePerformanceSummary → DbSystemComputePerformanceSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbSystemComputePerformanceSummary(**data)
    except Exception:
        return DbSystemComputePerformanceSummary(
            compute_performance_list=getattr(o, "compute_performance_list", None),
            shape=getattr(o, "shape", None),
        )


class DbSystemShapeSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbSystemShapeSummary."""

    are_server_types_supported: Optional[Any] = Field(
        None,
        description="If true, the shape supports configurable DB and Storage Server types.",
    )
    available_core_count: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the available_core_count of this DbSystemShapeSummary. The maximum number of CPU cores that can be enabled on the DB system for this shape.",
    )
    available_core_count_per_node: Optional[Any] = Field(
        None,
        description="The maximum number of CPU cores per database node that can be enabled for this shape. Only applicable to the flex Exadata shape, ExaCC Elastic shapes and VM Flex shapes.",
    )
    available_data_storage_in_t_bs: Optional[Any] = Field(
        None,
        description="The maximum DATA storage that can be enabled for this shape.",
    )
    available_data_storage_per_server_in_tbs: Optional[float] = Field(
        None,
        description="The maximum data storage available per storage server for this shape. Only applicable to ExaCC Elastic shapes.",
    )
    available_db_node_per_node_in_gbs: Optional[Any] = Field(
        None,
        description="The maximum Db Node storage available per database node for this shape. Only applicable to ExaCC Elastic shapes.",
    )
    available_db_node_storage_in_g_bs: Optional[Any] = Field(
        None,
        description="The maximum Db Node storage that can be enabled for this shape.",
    )
    available_memory_in_gbs: Optional[Any] = Field(
        None,
        description="The maximum memory that can be enabled for this shape.",
    )
    available_memory_per_node_in_gbs: Optional[Any] = Field(
        None,
        description="The maximum memory available per database node for this shape. Only applicable to ExaCC Elastic shapes.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    core_count_increment: Optional[Any] = Field(
        None,
        description="The discrete number by which the CPU core count for this shape can be increased or decreased.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The display name of the shape used for the DB system.",
    )
    max_storage_count: Optional[Any] = Field(
        None,
        description="The maximum number of Exadata storage servers available for the Exadata infrastructure.",
    )
    maximum_node_count: Optional[Any] = Field(
        None,
        description="The maximum number of compute servers available for this shape.",
    )
    min_core_count_per_node: Optional[Any] = Field(
        None,
        description="The minimum number of CPU cores that can be enabled per node for this shape.",
    )
    min_data_storage_in_t_bs: Optional[Any] = Field(
        None,
        description="The minimum data storage that need be allocated for this shape.",
    )
    min_db_node_storage_per_node_in_g_bs: Optional[Any] = Field(
        None,
        description="The minimum Db Node storage that need be allocated per node for this shape.",
    )
    min_memory_per_node_in_g_bs: Optional[Any] = Field(
        None,
        description="The minimum memory that need be allocated per node for this shape.",
    )
    min_storage_count: Optional[Any] = Field(
        None,
        description="The minimum number of Exadata storage servers available for the Exadata infrastructure.",
    )
    minimum_core_count: Optional[Any] = Field(
        None,
        description="The minimum number of CPU cores that can be enabled on the DB system for this shape.",
    )
    minimum_node_count: Optional[Any] = Field(
        None,
        description="The minimum number of compute servers available for this shape.",
    )
    name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the name of this DbSystemShapeSummary. The name of the shape used for the DB system.",
    )
    shape: Optional[Any] = Field(
        None,
        description="Deprecated. Use `name` instead of `shape`.",
    )
    shape_family: Optional[Any] = Field(
        None,
        description="The family of the shape used for the DB system.",
    )
    shape_type: Optional[Any] = Field(
        None,
        description='The shape type for the virtual machine DB system. Shape type is determined by CPU hardware. Valid values are `AMD` , `INTEL`, `INTEL_FLEX_X9` or `AMPERE_FLEX_A1`. Allowed values for this property are: "AMD", "INTEL", "INTEL_FLEX_X9", "AMPERE_FLEX_A1", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )


def map_dbsystemshapesummary(
    o: oci.database.models.DbSystemShapeSummary,
) -> DbSystemShapeSummary | None:
    """Map oci.database.models.DbSystemShapeSummary → DbSystemShapeSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbSystemShapeSummary(**data)
    except Exception:
        return DbSystemShapeSummary(
            are_server_types_supported=getattr(o, "are_server_types_supported", None),
            available_core_count=getattr(o, "available_core_count", None),
            available_core_count_per_node=getattr(
                o, "available_core_count_per_node", None
            ),
            available_data_storage_in_t_bs=getattr(
                o, "available_data_storage_in_t_bs", None
            ),
            available_data_storage_per_server_in_tbs=getattr(
                o, "available_data_storage_per_server_in_tbs", None
            ),
            available_db_node_per_node_in_gbs=getattr(
                o, "available_db_node_per_node_in_gbs", None
            ),
            available_db_node_storage_in_g_bs=getattr(
                o, "available_db_node_storage_in_g_bs", None
            ),
            available_memory_in_gbs=getattr(o, "available_memory_in_gbs", None),
            available_memory_per_node_in_gbs=getattr(
                o, "available_memory_per_node_in_gbs", None
            ),
            compute_model=getattr(o, "compute_model", None),
            core_count_increment=getattr(o, "core_count_increment", None),
            display_name=getattr(o, "display_name", None),
            max_storage_count=getattr(o, "max_storage_count", None),
            maximum_node_count=getattr(o, "maximum_node_count", None),
            min_core_count_per_node=getattr(o, "min_core_count_per_node", None),
            min_data_storage_in_t_bs=getattr(o, "min_data_storage_in_t_bs", None),
            min_db_node_storage_per_node_in_g_bs=getattr(
                o, "min_db_node_storage_per_node_in_g_bs", None
            ),
            min_memory_per_node_in_g_bs=getattr(o, "min_memory_per_node_in_g_bs", None),
            min_storage_count=getattr(o, "min_storage_count", None),
            minimum_core_count=getattr(o, "minimum_core_count", None),
            minimum_node_count=getattr(o, "minimum_node_count", None),
            name=getattr(o, "name", None),
            shape=getattr(o, "shape", None),
            shape_family=getattr(o, "shape_family", None),
            shape_type=getattr(o, "shape_type", None),
        )


class DbSystemStoragePerformanceSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbSystemStoragePerformanceSummary."""

    data_storage_performance_list: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the data_storage_performance_list of this DbSystemStoragePerformanceSummary. List of storage performance for the DATA disks",
    )
    reco_storage_performance_list: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the reco_storage_performance_list of this DbSystemStoragePerformanceSummary. List of storage performance for the RECO disks",
    )
    shape_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the shape_type of this DbSystemStoragePerformanceSummary. ShapeType of the DbSystems INTEL , AMD, INTEL_FLEX_X9 or AMPERE_FLEX_A1 Allowed values for this property are: "AMD", "INTEL", "INTEL_FLEX_X9", "AMPERE_FLEX_A1", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )


def map_dbsystemstorageperformancesummary(
    o: oci.database.models.DbSystemStoragePerformanceSummary,
) -> DbSystemStoragePerformanceSummary | None:
    """Map oci.database.models.DbSystemStoragePerformanceSummary → DbSystemStoragePerformanceSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbSystemStoragePerformanceSummary(**data)
    except Exception:
        return DbSystemStoragePerformanceSummary(
            data_storage_performance_list=getattr(
                o, "data_storage_performance_list", None
            ),
            reco_storage_performance_list=getattr(
                o, "reco_storage_performance_list", None
            ),
            shape_type=getattr(o, "shape_type", None),
        )


class DbSystemSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbSystemSummary."""

    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this DbSystemSummary. The name of the availability domain that the DB system is located in.",
    )
    backup_network_nsg_ids: Optional[Any] = Field(
        None,
        description="A list of the `OCIDs`__ of the network security groups (NSGs) that the backup network of this DB system belongs to. Setting this to an empty array after the list is created removes the resource from all NSGs. For more information about NSGs, see `Security Rules`__. Applicable only to Exadata systems.",
    )
    backup_subnet_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the backup network subnet the DB system is associated with. Applicable only to Exadata DB systems. **Subnet Restriction:** See the subnet restrictions information for **subnetId**.",
    )
    cluster_name: Optional[Any] = Field(
        None,
        description="The cluster name for Exadata and 2-node RAC virtual machine DB systems. The cluster name must begin with an alphabetic character, and may contain hyphens (-). Underscores (_) are not permitted. The cluster name can be no longer than 11 characters and is not case sensitive.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this DbSystemSummary. The `OCID`__ of the compartment.",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cpu_core_count of this DbSystemSummary. The number of CPU cores enabled on the DB system.",
    )
    data_collection_options: Optional[Any] = Field(
        None,
        description="",
    )
    data_storage_percentage: Optional[Any] = Field(
        None,
        description="The percentage assigned to DATA storage (user data and database files). The remaining percentage is assigned to RECO storage (database redo logs, archive logs, and recovery manager backups). Accepted values are 40 and 80. The default is 80 percent assigned to DATA storage. Not applicable for virtual machine DB systems.",
    )
    data_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The data storage size, in gigabytes, that is currently available to the DB system. Applies only for virtual machine DB systems.",
    )
    database_edition: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the database_edition of this DbSystemSummary. The Oracle Database edition that applies to all the databases on the DB system. Allowed values for this property are: "STANDARD_EDITION", "ENTERPRISE_EDITION", "ENTERPRISE_EDITION_HIGH_PERFORMANCE", "ENTERPRISE_EDITION_EXTREME_PERFORMANCE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    db_system_options: Optional[Any] = Field(
        None,
        description="",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    disk_redundancy: Optional[Any] = Field(
        None,
        description="The type of redundancy configured for the DB system. NORMAL is 2-way redundancy. HIGH is 3-way redundancy. Allowed values for this property are: \"HIGH\", \"NORMAL\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this DbSystemSummary. The user-friendly name for the DB system. The name does not have to be unique.",
    )
    domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the domain of this DbSystemSummary. The domain name for the DB system.",
    )
    fault_domains: Optional[Any] = Field(
        None,
        description="List of the Fault Domains in which this DB system is provisioned.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    gi_software_image_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of a grid infrastructure software image. This is a database software image of the type `GRID_IMAGE`.",
    )
    hostname: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the hostname of this DbSystemSummary. The hostname for the DB system.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DbSystemSummary. The `OCID`__ of the DB system.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    last_patch_history_entry_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last patch history. This value is updated as soon as a patch operation starts.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to all the databases on the DB system. The default is LICENSE_INCLUDED. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DbSystemSummary. The current state of the DB system. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MIGRATED", "MAINTENANCE_IN_PROGRESS", "NEEDS_ATTENTION", "UPGRADING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    listener_port: Optional[Any] = Field(
        None,
        description="The port number configured for the listener on the DB system.",
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="Memory allocated to the DB system, in gigabytes.",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    node_count: Optional[Any] = Field(
        None,
        description="The number of nodes in the DB system. For RAC DB systems, the value is greater than 1.",
    )
    nsg_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ for the network security groups (NSGs) to which this resource belongs. Setting this to an empty list removes all resources from all NSGs. For more information about NSGs, see `Security Rules`__. **NsgIds restrictions:** - A network security group (NSG) is optional for Autonomous Databases with private access. The nsgIds list can be empty.",
    )
    os_version: Optional[Any] = Field(
        None,
        description="The most recent OS Patch Version applied on the DB system.",
    )
    point_in_time_data_disk_clone_timestamp: Optional[Any] = Field(
        None,
        description="The point in time for a cloned database system when the data disks were cloned from the source database system, as described in `RFC 3339`__.",
    )
    reco_storage_size_in_gb: Optional[Any] = Field(
        None,
        description="The RECO/REDO storage size, in gigabytes, that is currently allocated to the DB system. Applies only for virtual machine DB systems.",
    )
    scan_dns_name: Optional[Any] = Field(
        None,
        description="The FQDN of the DNS record for the SCAN IP addresses that are associated with the DB system.",
    )
    scan_dns_record_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the DNS record for the SCAN IP addresses that are associated with the DB system.",
    )
    scan_ip_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Single Client Access Name (SCAN) IPv4 addresses associated with the DB system. SCAN IPv4 addresses are typically used for load balancing and are not assigned to any interface. Oracle Clusterware directs the requests to the appropriate nodes in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    scan_ipv6_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Single Client Access Name (SCAN) IPv6 addresses associated with the DB system. SCAN IPv6 addresses are typically used for load balancing and are not assigned to any interface. Oracle Clusterware directs the requests to the appropriate nodes in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    security_attributes: Optional[Any] = Field(
        None,
        description='Security Attributes for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. Example: `{"Oracle-ZPR": {"MaxEgressCount": {"value": "42", "mode": "audit"}}}`',
    )
    shape: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the shape of this DbSystemSummary. The shape of the DB system. The shape determines resources to allocate to the DB system. - For virtual machine shapes, the number of CPU cores and memory - For bare metal and Exadata shapes, the number of CPU cores, storage, and memory",
    )
    source_db_system_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the DB system.",
    )
    sparse_diskgroup: Optional[Any] = Field(
        None,
        description="True, if Sparse Diskgroup is configured for Exadata dbsystem, False, if Sparse diskgroup was not configured.",
    )
    ssh_public_keys: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the ssh_public_keys of this DbSystemSummary. The public key portion of one or more key pairs used for SSH access to the DB system.",
    )
    storage_volume_performance_mode: Optional[Any] = Field(
        None,
        description="The block storage volume performance level. Valid values are `BALANCED` and `HIGH_PERFORMANCE`. See `Block Volume Performance`__ for more information. Allowed values for this property are: \"BALANCED\", \"HIGH_PERFORMANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the subnet_id of this DbSystemSummary. The `OCID`__ of the subnet the DB system is associated with. **Subnet Restrictions:** - For bare metal DB systems and for single node virtual machine DB systems, do not use a subnet that overlaps with 192.168.16.16/28. - For Exadata and virtual machine 2-node RAC DB systems, do not use a subnet that overlaps with 192.168.128.0/20. These subnets are used by the Oracle Clusterware private interconnect on the database instance. Specifying an overlapping subnet will cause the private interconnect to malfunction. This restriction applies to both the client subnet and backup subnet.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the DB system was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the DB system. For details, see `DB System Time Zones`__.",
    )
    version: Optional[Any] = Field(
        None,
        description="The Oracle Database version of the DB system.",
    )
    vip_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the virtual IPv4 (VIP) addresses associated with the DB system. The Cluster Ready Services (CRS) creates and maintains one VIPv4 address for each node in the DB system to enable failover. If one node fails, the VIPv4 is reassigned to another active node in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    vipv6_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the virtual IPv6 (VIP) addresses associated with the DB system. The Cluster Ready Services (CRS) creates and maintains one VIP IpV6 address for each node in the DB system to enable failover. If one node fails, the VIP is reassigned to another active node in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    zone_id: Optional[Any] = Field(
        None,
        description="The OCID of the zone the DB system is associated with.",
    )


def map_dbsystemsummary(
    o: oci.database.models.DbSystemSummary,
) -> DbSystemSummary | None:
    """Map oci.database.models.DbSystemSummary → DbSystemSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbSystemSummary(**data)
    except Exception:
        return DbSystemSummary(
            availability_domain=getattr(o, "availability_domain", None),
            backup_network_nsg_ids=getattr(o, "backup_network_nsg_ids", None),
            backup_subnet_id=getattr(o, "backup_subnet_id", None),
            cluster_name=getattr(o, "cluster_name", None),
            compartment_id=getattr(o, "compartment_id", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            data_collection_options=getattr(o, "data_collection_options", None),
            data_storage_percentage=getattr(o, "data_storage_percentage", None),
            data_storage_size_in_gbs=getattr(o, "data_storage_size_in_gbs", None),
            database_edition=getattr(o, "database_edition", None),
            db_system_options=getattr(o, "db_system_options", None),
            defined_tags=getattr(o, "defined_tags", None),
            disk_redundancy=getattr(o, "disk_redundancy", None),
            display_name=getattr(o, "display_name", None),
            domain=getattr(o, "domain", None),
            fault_domains=getattr(o, "fault_domains", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            gi_software_image_id=getattr(o, "gi_software_image_id", None),
            hostname=getattr(o, "hostname", None),
            id=getattr(o, "id", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            last_patch_history_entry_id=getattr(o, "last_patch_history_entry_id", None),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            listener_port=getattr(o, "listener_port", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            node_count=getattr(o, "node_count", None),
            nsg_ids=getattr(o, "nsg_ids", None),
            os_version=getattr(o, "os_version", None),
            point_in_time_data_disk_clone_timestamp=getattr(
                o, "point_in_time_data_disk_clone_timestamp", None
            ),
            reco_storage_size_in_gb=getattr(o, "reco_storage_size_in_gb", None),
            scan_dns_name=getattr(o, "scan_dns_name", None),
            scan_dns_record_id=getattr(o, "scan_dns_record_id", None),
            scan_ip_ids=getattr(o, "scan_ip_ids", None),
            scan_ipv6_ids=getattr(o, "scan_ipv6_ids", None),
            security_attributes=getattr(o, "security_attributes", None),
            shape=getattr(o, "shape", None),
            source_db_system_id=getattr(o, "source_db_system_id", None),
            sparse_diskgroup=getattr(o, "sparse_diskgroup", None),
            ssh_public_keys=getattr(o, "ssh_public_keys", None),
            storage_volume_performance_mode=getattr(
                o, "storage_volume_performance_mode", None
            ),
            subnet_id=getattr(o, "subnet_id", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
            version=getattr(o, "version", None),
            vip_ids=getattr(o, "vip_ids", None),
            vipv6_ids=getattr(o, "vipv6_ids", None),
            zone_id=getattr(o, "zone_id", None),
        )


class DbVersionSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbVersionSummary."""

    is_latest_for_major_version: Optional[Any] = Field(
        None,
        description="True if this version of the Oracle Database software is the latest version for a release.",
    )
    is_preview_db_version: Optional[Any] = Field(
        None,
        description="True if this version of the Oracle Database software is the preview version.",
    )
    is_upgrade_supported: Optional[Any] = Field(
        None,
        description="True if this version of the Oracle Database software is supported for Upgrade.",
    )
    supports_pdb: Optional[Any] = Field(
        None,
        description="True if this version of the Oracle Database software supports pluggable databases.",
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this DbVersionSummary. A valid Oracle Database version.",
    )


def map_dbversionsummary(
    o: oci.database.models.DbVersionSummary,
) -> DbVersionSummary | None:
    """Map oci.database.models.DbVersionSummary → DbVersionSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbVersionSummary(**data)
    except Exception:
        return DbVersionSummary(
            is_latest_for_major_version=getattr(o, "is_latest_for_major_version", None),
            is_preview_db_version=getattr(o, "is_preview_db_version", None),
            is_upgrade_supported=getattr(o, "is_upgrade_supported", None),
            supports_pdb=getattr(o, "supports_pdb", None),
            version=getattr(o, "version", None),
        )


class ExadataInfrastructureSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExadataInfrastructureSummary."""

    activated_storage_count: Optional[Any] = Field(
        None,
        description="The requested number of additional storage servers activated for the Exadata infrastructure.",
    )
    additional_compute_count: Optional[Any] = Field(
        None,
        description="The requested number of additional compute servers for the Exadata infrastructure.",
    )
    additional_compute_system_model: Optional[Any] = Field(
        None,
        description='Oracle Exadata System Model specification. The system model determines the amount of compute or storage server resources available for use. For more information, please see [System and Shape Configuration Options] ( Allowed values for this property are: "X7", "X8", "X8M", "X9M", "X10M", "X11M", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    additional_storage_count: Optional[Any] = Field(
        None,
        description="The requested number of additional storage servers for the Exadata infrastructure.",
    )
    admin_network_cidr: Optional[Any] = Field(
        None,
        description="The CIDR block for the Exadata administration network.",
    )
    availability_domain: Optional[Any] = Field(
        None,
        description="The name of the availability domain that the Exadata infrastructure is located in.",
    )
    cloud_control_plane_server1: Optional[Any] = Field(
        None,
        description="The IP address for the first control plane server.",
    )
    cloud_control_plane_server2: Optional[Any] = Field(
        None,
        description="The IP address for the second control plane server.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExadataInfrastructureSummary. The `OCID`__ of the compartment.",
    )
    compute_count: Optional[Any] = Field(
        None,
        description="The number of compute servers for the Exadata infrastructure.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    contacts: Optional[Any] = Field(
        None,
        description="The list of contacts for the Exadata infrastructure.",
    )
    corporate_proxy: Optional[Any] = Field(
        None,
        description="The corporate network proxy for access to the control plane network.",
    )
    cpus_enabled: Optional[Any] = Field(
        None,
        description="The number of enabled CPU cores.",
    )
    csi_number: Optional[Any] = Field(
        None,
        description="The CSI Number of the Exadata infrastructure.",
    )
    data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="Size, in terabytes, of the DATA disk group.",
    )
    database_server_type: Optional[Any] = Field(
        None,
        description="The database server type of the Exadata infrastructure.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage allocated in GBs.",
    )
    db_server_version: Optional[Any] = Field(
        None,
        description="The software version of the database servers (dom0) in the Exadata infrastructure.",
    )
    defined_file_system_configurations: Optional[Any] = Field(
        None,
        description="Details of the file system configuration of the Exadata infrastructure.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExadataInfrastructureSummary. The user-friendly name for the Exadata Cloud@Customer infrastructure. The name does not need to be unique.",
    )
    dns_server: Optional[Any] = Field(
        None,
        description="The list of DNS server IP addresses. Maximum of 3 allowed.",
    )
    exascale_config: Optional[Any] = Field(
        None,
        description="",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    gateway: Optional[Any] = Field(
        None,
        description="The gateway for the control plane network.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExadataInfrastructureSummary. The `OCID`__ of the Exadata infrastructure.",
    )
    infini_band_network_cidr: Optional[Any] = Field(
        None,
        description="The CIDR block for the Exadata InfiniBand interconnect.",
    )
    is_cps_offline_report_enabled: Optional[Any] = Field(
        None,
        description="Indicates whether cps offline diagnostic report is enabled for this Exadata infrastructure. This will allow a customer to quickly check status themselves and fix problems on their end, saving time and frustration for both Oracle and the customer when they find the CPS in a disconnected state.You can enable offline diagnostic report during Exadata infrastructure provisioning. You can also disable or enable it at any time using the UpdateExadatainfrastructure API.",
    )
    is_multi_rack_deployment: Optional[Any] = Field(
        None,
        description="Indicates if deployment is Multi-Rack or not.",
    )
    is_scheduling_policy_associated: Optional[Any] = Field(
        None,
        description="If true, the infrastructure is using granular maintenance scheduling preference.",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExadataInfrastructureSummary. The current lifecycle state of the Exadata infrastructure. Allowed values for this property are: "CREATING", "REQUIRES_ACTIVATION", "ACTIVATING", "ACTIVE", "ACTIVATION_FAILED", "FAILED", "UPDATING", "DELETING", "DELETED", "DISCONNECTED", "MAINTENANCE_IN_PROGRESS", "WAITING_FOR_CONNECTIVITY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_slo_status: Optional[Any] = Field(
        None,
        description="A field to capture ‘Maintenance SLO Status’ for the Exadata infrastructure with values ‘OK’, ‘DEGRADED’. Default is ‘OK’ when the infrastructure is provisioned. Allowed values for this property are: \"OK\", \"DEGRADED\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="",
    )
    max_cpu_count: Optional[Any] = Field(
        None,
        description="The total number of CPU cores available.",
    )
    max_data_storage_in_t_bs: Optional[float] = Field(
        None,
        description="The total available DATA disk group size.",
    )
    max_db_node_storage_in_g_bs: Optional[Any] = Field(
        None,
        description="The total local node storage available in GBs.",
    )
    max_memory_in_gbs: Optional[Any] = Field(
        None,
        description="The total memory available in GBs.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory allocated in GBs.",
    )
    monthly_db_server_version: Optional[Any] = Field(
        None,
        description="The monthly software version of the database servers (dom0) in the Exadata infrastructure.",
    )
    multi_rack_configuration_file: Optional[Any] = Field(
        None,
        description="The base64 encoded Multi-Rack configuration json file.",
    )
    netmask: Optional[Any] = Field(
        None,
        description="The netmask for the control plane network.",
    )
    network_bonding_mode_details: Optional[Any] = Field(
        None,
        description="",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    ntp_server: Optional[Any] = Field(
        None,
        description="The list of NTP server IP addresses. Maximum of 3 allowed.",
    )
    rack_serial_number: Optional[Any] = Field(
        None,
        description="The serial number for the Exadata infrastructure.",
    )
    shape: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the shape of this ExadataInfrastructureSummary. The shape of the Exadata infrastructure. The shape determines the amount of CPU, storage, and memory resources allocated to the instance.",
    )
    storage_count: Optional[Any] = Field(
        None,
        description="The number of Exadata storage servers for the Exadata infrastructure.",
    )
    storage_server_type: Optional[Any] = Field(
        None,
        description="The storage server type of the Exadata infrastructure.",
    )
    storage_server_version: Optional[Any] = Field(
        None,
        description="The software version of the storage servers (cells) in the Exadata infrastructure.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Exadata infrastructure was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the Exadata infrastructure. For details, see `Exadata Infrastructure Time Zones`__.",
    )


def map_exadatainfrastructuresummary(
    o: oci.database.models.ExadataInfrastructureSummary,
) -> ExadataInfrastructureSummary | None:
    """Map oci.database.models.ExadataInfrastructureSummary → ExadataInfrastructureSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExadataInfrastructureSummary(**data)
    except Exception:
        return ExadataInfrastructureSummary(
            activated_storage_count=getattr(o, "activated_storage_count", None),
            additional_compute_count=getattr(o, "additional_compute_count", None),
            additional_compute_system_model=getattr(
                o, "additional_compute_system_model", None
            ),
            additional_storage_count=getattr(o, "additional_storage_count", None),
            admin_network_cidr=getattr(o, "admin_network_cidr", None),
            availability_domain=getattr(o, "availability_domain", None),
            cloud_control_plane_server1=getattr(o, "cloud_control_plane_server1", None),
            cloud_control_plane_server2=getattr(o, "cloud_control_plane_server2", None),
            compartment_id=getattr(o, "compartment_id", None),
            compute_count=getattr(o, "compute_count", None),
            compute_model=getattr(o, "compute_model", None),
            contacts=getattr(o, "contacts", None),
            corporate_proxy=getattr(o, "corporate_proxy", None),
            cpus_enabled=getattr(o, "cpus_enabled", None),
            csi_number=getattr(o, "csi_number", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            database_server_type=getattr(o, "database_server_type", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_server_version=getattr(o, "db_server_version", None),
            defined_file_system_configurations=getattr(
                o, "defined_file_system_configurations", None
            ),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            dns_server=getattr(o, "dns_server", None),
            exascale_config=getattr(o, "exascale_config", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            gateway=getattr(o, "gateway", None),
            id=getattr(o, "id", None),
            infini_band_network_cidr=getattr(o, "infini_band_network_cidr", None),
            is_cps_offline_report_enabled=getattr(
                o, "is_cps_offline_report_enabled", None
            ),
            is_multi_rack_deployment=getattr(o, "is_multi_rack_deployment", None),
            is_scheduling_policy_associated=getattr(
                o, "is_scheduling_policy_associated", None
            ),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_slo_status=getattr(o, "maintenance_slo_status", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            max_cpu_count=getattr(o, "max_cpu_count", None),
            max_data_storage_in_t_bs=getattr(o, "max_data_storage_in_t_bs", None),
            max_db_node_storage_in_g_bs=getattr(o, "max_db_node_storage_in_g_bs", None),
            max_memory_in_gbs=getattr(o, "max_memory_in_gbs", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            monthly_db_server_version=getattr(o, "monthly_db_server_version", None),
            multi_rack_configuration_file=getattr(
                o, "multi_rack_configuration_file", None
            ),
            netmask=getattr(o, "netmask", None),
            network_bonding_mode_details=getattr(
                o, "network_bonding_mode_details", None
            ),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            ntp_server=getattr(o, "ntp_server", None),
            rack_serial_number=getattr(o, "rack_serial_number", None),
            shape=getattr(o, "shape", None),
            storage_count=getattr(o, "storage_count", None),
            storage_server_type=getattr(o, "storage_server_type", None),
            storage_server_version=getattr(o, "storage_server_version", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
        )


class ExadbVmClusterUpdateSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExadbVmClusterUpdateSummary."""

    available_actions: Optional[Any] = Field(
        None,
        description='The possible actions performed by the update operation on the infrastructure components. Allowed values for items in this list are: "ROLLING_APPLY", "NON_ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    description: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the description of this ExadbVmClusterUpdateSummary. Details of the maintenance update package.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExadbVmClusterUpdateSummary. The `OCID`__ of the maintenance update.",
    )
    last_action: Optional[Any] = Field(
        None,
        description='The previous update action performed. Allowed values for this property are: "ROLLING_APPLY", "NON_ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Descriptive text providing additional details about the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the maintenance update. Dependent on value of `lastAction`. Allowed values for this property are: "AVAILABLE", "SUCCESS", "IN_PROGRESS", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_released: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_released of this ExadbVmClusterUpdateSummary. The date and time the maintenance update was released.",
    )
    update_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the update_type of this ExadbVmClusterUpdateSummary. The type of cloud VM cluster maintenance update. Allowed values for this property are: "GI_UPGRADE", "GI_PATCH", "OS_UPDATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this ExadbVmClusterUpdateSummary. The version of the maintenance update package.",
    )


def map_exadbvmclusterupdatesummary(
    o: oci.database.models.ExadbVmClusterUpdateSummary,
) -> ExadbVmClusterUpdateSummary | None:
    """Map oci.database.models.ExadbVmClusterUpdateSummary → ExadbVmClusterUpdateSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExadbVmClusterUpdateSummary(**data)
    except Exception:
        return ExadbVmClusterUpdateSummary(
            available_actions=getattr(o, "available_actions", None),
            description=getattr(o, "description", None),
            id=getattr(o, "id", None),
            last_action=getattr(o, "last_action", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_released=getattr(o, "time_released", None),
            update_type=getattr(o, "update_type", None),
            version=getattr(o, "version", None),
        )


class ExadbVmClusterSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExadbVmClusterSummary."""

    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this ExadbVmClusterSummary. The name of the availability domain in which the Exadata VM cluster on Exascale Infrastructure is located.",
    )
    backup_network_nsg_ids: Optional[Any] = Field(
        None,
        description="A list of the `OCIDs`__ of the network security groups (NSGs) that the backup network of this DB system belongs to. Setting this to an empty array after the list is created removes the resource from all NSGs. For more information about NSGs, see `Security Rules`__. Applicable only to Exadata systems.",
    )
    backup_subnet_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the backup_subnet_id of this ExadbVmClusterSummary. The `OCID`__ of the backup network subnet associated with the Exadata VM cluster on Exascale Infrastructure.",
    )
    cluster_name: Optional[Any] = Field(
        None,
        description="The cluster name for Exadata VM cluster on Exascale Infrastructure. The cluster name must begin with an alphabetic character, and may contain hyphens (-). Underscores (_) are not permitted. The cluster name can be no longer than 11 characters and is not case sensitive.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExadbVmClusterSummary. The `OCID`__ of the compartment.",
    )
    data_collection_options: Optional[Any] = Field(
        None,
        description="",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExadbVmClusterSummary. The user-friendly name for the Exadata VM cluster on Exascale Infrastructure. The name does not need to be unique.",
    )
    domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the domain of this ExadbVmClusterSummary. A domain name used for the Exadata VM cluster on Exascale Infrastructure. If the Oracle-provided internet and VCN resolver is enabled for the specified subnet, then the domain name for the subnet is used (do not provide one). Otherwise, provide a valid DNS domain name. Hyphens (-) are not permitted. Applies to Exadata Database Service on Exascale Infrastructure only.",
    )
    enabled_e_cpu_count: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the enabled_e_cpu_count of this ExadbVmClusterSummary. The number of ECPUs to enable for an Exadata VM cluster on Exascale Infrastructure.",
    )
    exascale_db_storage_vault_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the exascale_db_storage_vault_id of this ExadbVmClusterSummary. The `OCID`__ of the Exadata Database Storage Vault.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    gi_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Grid Infrastructure (GI) software version.",
    )
    grid_image_id: Optional[Any] = Field(
        None,
        description="Grid Setup will be done using this grid image id. The grid image id can be extracted from 1. Obtain the supported major versions using API /20160918/giVersions?compartmentId=<compartmentId>&shape=EXADB_XS&availabilityDomain=<AD name> 2. Replace {version} with one of the supported major versions and obtain the supported minor versions using API /20160918/giVersions/{version}/minorVersions?compartmentId=<compartmentId>&shapeFamily=EXADB_XS&availabilityDomain=<AD name>",
    )
    grid_image_type: Optional[Any] = Field(
        None,
        description="The type of Grid Image Allowed values for this property are: \"RELEASE_UPDATE\", \"CUSTOM_IMAGE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    hostname: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the hostname of this ExadbVmClusterSummary. The hostname for the Exadata VM cluster on Exascale Infrastructure. The hostname must begin with an alphabetic character, and can contain alphanumeric characters and hyphens (-). For Exadata systems, the maximum length of the hostname is 12 characters. The maximum length of the combined hostname and domain is 63 characters. **Note:** The hostname must be unique within the subnet. If it is not unique, then the Exadata VM cluster on Exascale Infrastructure will fail to provision.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExadbVmClusterSummary. The `OCID`__ of the Exadata VM cluster on Exascale Infrastructure.",
    )
    last_update_history_entry_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance update history entry. This value is updated when a maintenance update starts.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to the Exadata VM cluster on Exascale Infrastructure. The default is BRING_YOUR_OWN_LICENSE. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExadbVmClusterSummary. The current state of the Exadata VM cluster on Exascale Infrastructure. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    listener_port: Optional[Any] = Field(
        None,
        description="The port number configured for the listener on the Exadata VM cluster on Exascale Infrastructure.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory that you want to be allocated in GBs. Memory is calculated based on 11 GB per VM core reserved.",
    )
    node_count: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the node_count of this ExadbVmClusterSummary. The number of nodes in the Exadata VM cluster on Exascale Infrastructure.",
    )
    nsg_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ for the network security groups (NSGs) to which this resource belongs. Setting this to an empty list removes all resources from all NSGs. For more information about NSGs, see `Security Rules`__. **NsgIds restrictions:** - A network security group (NSG) is optional for Autonomous Databases with private access. The nsgIds list can be empty.",
    )
    private_zone_id: Optional[Any] = Field(
        None,
        description="The private zone ID in which you want DNS records to be created.",
    )
    scan_dns_name: Optional[Any] = Field(
        None,
        description="The FQDN of the DNS record for the SCAN IP addresses that are associated with the Exadata VM cluster on Exascale Infrastructure.",
    )
    scan_dns_record_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the DNS record for the SCAN IP addresses that are associated with the Exadata VM cluster on Exascale Infrastructure.",
    )
    scan_ip_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Single Client Access Name (SCAN) IP addresses associated with the Exadata VM cluster on Exascale Infrastructure. SCAN IP addresses are typically used for load balancing and are not assigned to any interface. Oracle Clusterware directs the requests to the appropriate nodes in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    scan_listener_port_tcp: Optional[Any] = Field(
        None,
        description="The TCP Single Client Access Name (SCAN) port. The default port is 1521.",
    )
    scan_listener_port_tcp_ssl: Optional[Any] = Field(
        None,
        description="The Secured Communication (TCPS) protocol Single Client Access Name (SCAN) port. The default port is 2484.",
    )
    security_attributes: Optional[Any] = Field(
        None,
        description='Security Attributes for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. Example: `{"Oracle-ZPR": {"MaxEgressCount": {"value": "42", "mode": "audit"}}}`',
    )
    shape: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the shape of this ExadbVmClusterSummary. The shape of the Exadata VM cluster on Exascale Infrastructure resource",
    )
    snapshot_file_system_storage: Optional[Any] = Field(
        None,
        description="",
    )
    ssh_public_keys: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the ssh_public_keys of this ExadbVmClusterSummary. The public key portion of one or more key pairs used for SSH access to the Exadata VM cluster on Exascale Infrastructure.",
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the subnet_id of this ExadbVmClusterSummary. The `OCID`__ of the subnet associated with the Exadata VM cluster on Exascale Infrastructure.",
    )
    system_tags: Optional[Any] = Field(
        None,
        description="System tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    system_version: Optional[Any] = Field(
        None,
        description="Operating system version of the image.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the Exadata VM cluster on Exascale Infrastructure was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone to use for the Exadata VM cluster on Exascale Infrastructure. For details, see `Time Zones`__.",
    )
    total_e_cpu_count: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the total_e_cpu_count of this ExadbVmClusterSummary. The number of Total ECPUs for an Exadata VM cluster on Exascale Infrastructure.",
    )
    total_file_system_storage: Optional[Any] = Field(
        None,
        description="",
    )
    vip_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the virtual IP (VIP) addresses associated with the Exadata VM cluster on Exascale Infrastructure. The Cluster Ready Services (CRS) creates and maintains one VIP address for each node in the Exadata Cloud Service instance to enable failover. If one node fails, then the VIP is reassigned to another active node in the cluster.",
    )
    vm_file_system_storage: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the vm_file_system_storage of this ExadbVmClusterSummary.",
    )
    zone_id: Optional[Any] = Field(
        None,
        description="The OCID of the zone with which the Exadata VM cluster on Exascale Infrastructure is associated.",
    )


def map_exadbvmclustersummary(
    o: oci.database.models.ExadbVmClusterSummary,
) -> ExadbVmClusterSummary | None:
    """Map oci.database.models.ExadbVmClusterSummary → ExadbVmClusterSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExadbVmClusterSummary(**data)
    except Exception:
        return ExadbVmClusterSummary(
            availability_domain=getattr(o, "availability_domain", None),
            backup_network_nsg_ids=getattr(o, "backup_network_nsg_ids", None),
            backup_subnet_id=getattr(o, "backup_subnet_id", None),
            cluster_name=getattr(o, "cluster_name", None),
            compartment_id=getattr(o, "compartment_id", None),
            data_collection_options=getattr(o, "data_collection_options", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            domain=getattr(o, "domain", None),
            enabled_e_cpu_count=getattr(o, "enabled_e_cpu_count", None),
            exascale_db_storage_vault_id=getattr(
                o, "exascale_db_storage_vault_id", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            gi_version=getattr(o, "gi_version", None),
            grid_image_id=getattr(o, "grid_image_id", None),
            grid_image_type=getattr(o, "grid_image_type", None),
            hostname=getattr(o, "hostname", None),
            id=getattr(o, "id", None),
            last_update_history_entry_id=getattr(
                o, "last_update_history_entry_id", None
            ),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            listener_port=getattr(o, "listener_port", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            node_count=getattr(o, "node_count", None),
            nsg_ids=getattr(o, "nsg_ids", None),
            private_zone_id=getattr(o, "private_zone_id", None),
            scan_dns_name=getattr(o, "scan_dns_name", None),
            scan_dns_record_id=getattr(o, "scan_dns_record_id", None),
            scan_ip_ids=getattr(o, "scan_ip_ids", None),
            scan_listener_port_tcp=getattr(o, "scan_listener_port_tcp", None),
            scan_listener_port_tcp_ssl=getattr(o, "scan_listener_port_tcp_ssl", None),
            security_attributes=getattr(o, "security_attributes", None),
            shape=getattr(o, "shape", None),
            snapshot_file_system_storage=getattr(
                o, "snapshot_file_system_storage", None
            ),
            ssh_public_keys=getattr(o, "ssh_public_keys", None),
            subnet_id=getattr(o, "subnet_id", None),
            system_tags=getattr(o, "system_tags", None),
            system_version=getattr(o, "system_version", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
            total_e_cpu_count=getattr(o, "total_e_cpu_count", None),
            total_file_system_storage=getattr(o, "total_file_system_storage", None),
            vip_ids=getattr(o, "vip_ids", None),
            vm_file_system_storage=getattr(o, "vm_file_system_storage", None),
            zone_id=getattr(o, "zone_id", None),
        )


class ExascaleDbStorageVaultSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExascaleDbStorageVaultSummary."""

    additional_flash_cache_in_percent: Optional[Any] = Field(
        None,
        description="The size of additional Flash Cache in percentage of High Capacity database storage.",
    )
    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this ExascaleDbStorageVaultSummary. The name of the availability domain in which the Exadata Database Storage Vault is located.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExascaleDbStorageVaultSummary. The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    description: Optional[Any] = Field(
        None,
        description="Exadata Database Storage Vault description.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExascaleDbStorageVaultSummary. The user-friendly name for the Exadata Database Storage Vault. The name does not need to be unique.",
    )
    exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Exadata infrastructure.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    high_capacity_database_storage: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the high_capacity_database_storage of this ExascaleDbStorageVaultSummary.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExascaleDbStorageVaultSummary. The `OCID`__ of the Exadata Database Storage Vault.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the lifecycle_state of this ExascaleDbStorageVaultSummary. The current state of the Exadata Database Storage Vault.",
    )
    system_tags: Optional[Any] = Field(
        None,
        description="System tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the Exadata Database Storage Vault was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone that you want to use for the Exadata Database Storage Vault. For details, see `Time Zones`__.",
    )
    vm_cluster_count: Optional[Any] = Field(
        None,
        description="The number of Exadata VM clusters used the Exadata Database Storage Vault.",
    )


def map_exascaledbstoragevaultsummary(
    o: oci.database.models.ExascaleDbStorageVaultSummary,
) -> ExascaleDbStorageVaultSummary | None:
    """Map oci.database.models.ExascaleDbStorageVaultSummary → ExascaleDbStorageVaultSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExascaleDbStorageVaultSummary(**data)
    except Exception:
        return ExascaleDbStorageVaultSummary(
            additional_flash_cache_in_percent=getattr(
                o, "additional_flash_cache_in_percent", None
            ),
            availability_domain=getattr(o, "availability_domain", None),
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            description=getattr(o, "description", None),
            display_name=getattr(o, "display_name", None),
            exadata_infrastructure_id=getattr(o, "exadata_infrastructure_id", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            high_capacity_database_storage=getattr(
                o, "high_capacity_database_storage", None
            ),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            system_tags=getattr(o, "system_tags", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
            vm_cluster_count=getattr(o, "vm_cluster_count", None),
        )


class ExecutionActionSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExecutionActionSummary."""

    action_members: Optional[Any] = Field(
        None,
        description="List of action members of this execution action.",
    )
    action_params: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the action_params of this ExecutionActionSummary. Map<ParamName, ParamValue> where a key value pair describes the specific action parameter. Example: `{"count": "3"}`',
    )
    action_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the action_type of this ExecutionActionSummary. The action type of the execution action being performed Allowed values for this property are: "DB_SERVER_FULL_SOFTWARE_UPDATE", "STORAGE_SERVER_FULL_SOFTWARE_UPDATE", "NETWORK_SWITCH_FULL_SOFTWARE_UPDATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExecutionActionSummary. The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    description: Optional[Any] = Field(
        None,
        description="Description of the execution action.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExecutionActionSummary. The user-friendly name for the execution action. The name does not need to be unique.",
    )
    estimated_time_in_mins: Optional[Any] = Field(
        None,
        description="The estimated time of the execution action in minutes.",
    )
    execution_action_order: Optional[Any] = Field(
        None,
        description="The priority order of the execution action.",
    )
    execution_window_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the execution_window_id of this ExecutionActionSummary. The `OCID`__ of the execution window resource the execution action belongs to.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExecutionActionSummary. The `OCID`__ of the execution action.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExecutionActionSummary. The current state of the execution action. Valid states are SCHEDULED, IN_PROGRESS, FAILED, CANCELED, UPDATING, DELETED, SUCCEEDED and PARTIAL_SUCCESS. Allowed values for this property are: "SCHEDULED", "IN_PROGRESS", "FAILED", "CANCELED", "UPDATING", "DELETED", "SUCCEEDED", "PARTIAL_SUCCESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    lifecycle_substate: Optional[Any] = Field(
        None,
        description='The current sub-state of the execution action. Valid states are DURATION_EXCEEDED, MAINTENANCE_IN_PROGRESS and WAITING. Allowed values for this property are: "DURATION_EXCEEDED", "MAINTENANCE_IN_PROGRESS", "WAITING", "RESCHEDULED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the execution action was created.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The last date and time that the execution action was updated.",
    )
    total_time_taken_in_mins: Optional[Any] = Field(
        None,
        description="The total time taken by corresponding resource activity in minutes.",
    )


def map_executionactionsummary(
    o: oci.database.models.ExecutionActionSummary,
) -> ExecutionActionSummary | None:
    """Map oci.database.models.ExecutionActionSummary → ExecutionActionSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExecutionActionSummary(**data)
    except Exception:
        return ExecutionActionSummary(
            action_members=getattr(o, "action_members", None),
            action_params=getattr(o, "action_params", None),
            action_type=getattr(o, "action_type", None),
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            description=getattr(o, "description", None),
            display_name=getattr(o, "display_name", None),
            estimated_time_in_mins=getattr(o, "estimated_time_in_mins", None),
            execution_action_order=getattr(o, "execution_action_order", None),
            execution_window_id=getattr(o, "execution_window_id", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            lifecycle_substate=getattr(o, "lifecycle_substate", None),
            time_created=getattr(o, "time_created", None),
            time_updated=getattr(o, "time_updated", None),
            total_time_taken_in_mins=getattr(o, "total_time_taken_in_mins", None),
        )


class ExecutionWindowSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExecutionWindowSummary."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExecutionWindowSummary. The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    description: Optional[Any] = Field(
        None,
        description="Description of the execution window.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExecutionWindowSummary. The user-friendly name for the execution window. The name does not need to be unique.",
    )
    estimated_time_in_mins: Optional[Any] = Field(
        None,
        description="The estimated time of the execution window in minutes.",
    )
    execution_resource_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the execution_resource_id of this ExecutionWindowSummary. The `OCID`__ of the execution resource the execution window belongs to.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExecutionWindowSummary. The `OCID`__ of the execution window.",
    )
    is_enforced_duration: Optional[Any] = Field(
        None,
        description="Indicates if duration the user plans to allocate for scheduling window is strictly enforced. The default value is `FALSE`.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExecutionWindowSummary. The current state of the Schedule Policy. Valid states are CREATED, SCHEDULED, IN_PROGRESS, FAILED, CANCELED, UPDATING, DELETED, SUCCEEDED and PARTIAL_SUCCESS. Allowed values for this property are: "CREATED", "SCHEDULED", "IN_PROGRESS", "FAILED", "CANCELED", "UPDATING", "DELETED", "SUCCEEDED", "PARTIAL_SUCCESS", "CREATING", "DELETING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    lifecycle_substate: Optional[Any] = Field(
        None,
        description='The current sub-state of the execution window. Valid states are DURATION_EXCEEDED, MAINTENANCE_IN_PROGRESS and WAITING. Allowed values for this property are: "DURATION_EXCEEDED", "MAINTENANCE_IN_PROGRESS", "WAITING", "RESCHEDULED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the execution window was created.",
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time that the execution window ended.",
    )
    time_scheduled: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_scheduled of this ExecutionWindowSummary. The scheduled start date and time of the execution window.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="The date and time that the execution window was started.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The last date and time that the execution window was updated.",
    )
    total_time_taken_in_mins: Optional[Any] = Field(
        None,
        description="The total time taken by corresponding resource activity in minutes.",
    )
    window_duration_in_mins: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the window_duration_in_mins of this ExecutionWindowSummary. Duration window allows user to set a duration they plan to allocate for Scheduling window. The duration is in minutes.",
    )
    window_type: Optional[Any] = Field(
        None,
        description="The execution window is of PLANNED or UNPLANNED type. Allowed values for this property are: \"PLANNED\", \"UNPLANNED\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )


def map_executionwindowsummary(
    o: oci.database.models.ExecutionWindowSummary,
) -> ExecutionWindowSummary | None:
    """Map oci.database.models.ExecutionWindowSummary → ExecutionWindowSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExecutionWindowSummary(**data)
    except Exception:
        return ExecutionWindowSummary(
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            description=getattr(o, "description", None),
            display_name=getattr(o, "display_name", None),
            estimated_time_in_mins=getattr(o, "estimated_time_in_mins", None),
            execution_resource_id=getattr(o, "execution_resource_id", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_enforced_duration=getattr(o, "is_enforced_duration", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            lifecycle_substate=getattr(o, "lifecycle_substate", None),
            time_created=getattr(o, "time_created", None),
            time_ended=getattr(o, "time_ended", None),
            time_scheduled=getattr(o, "time_scheduled", None),
            time_started=getattr(o, "time_started", None),
            time_updated=getattr(o, "time_updated", None),
            total_time_taken_in_mins=getattr(o, "total_time_taken_in_mins", None),
            window_duration_in_mins=getattr(o, "window_duration_in_mins", None),
            window_type=getattr(o, "window_type", None),
        )


class ExternalContainerDatabaseSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExternalContainerDatabaseSummary."""

    character_set: Optional[Any] = Field(
        None,
        description="The character set of the external database.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExternalContainerDatabaseSummary. The `OCID`__ of the compartment.",
    )
    database_configuration: Optional[Any] = Field(
        None,
        description="The Oracle Database configuration Allowed values for this property are: \"RAC\", \"SINGLE_INSTANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    database_edition: Optional[Any] = Field(
        None,
        description='The Oracle Database edition. Allowed values for this property are: "STANDARD_EDITION", "ENTERPRISE_EDITION", "ENTERPRISE_EDITION_HIGH_PERFORMANCE", "ENTERPRISE_EDITION_EXTREME_PERFORMANCE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    database_management_config: Optional[Any] = Field(
        None,
        description="",
    )
    database_version: Optional[Any] = Field(
        None,
        description="The Oracle Database version.",
    )
    db_id: Optional[Any] = Field(
        None,
        description="The Oracle Database ID, which identifies an Oracle Database located outside of Oracle Cloud.",
    )
    db_packs: Optional[Any] = Field(
        None,
        description="The database packs licensed for the external Oracle Database.",
    )
    db_unique_name: Optional[Any] = Field(
        None,
        description="The `DB_UNIQUE_NAME` of the external database.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExternalContainerDatabaseSummary. The user-friendly name for the external database. The name does not have to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExternalContainerDatabaseSummary. The `OCID`__ of the Oracle Cloud Infrastructure external database resource.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExternalContainerDatabaseSummary. The current state of the Oracle Cloud Infrastructure external database resource. Allowed values for this property are: "PROVISIONING", "NOT_CONNECTED", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    ncharacter_set: Optional[Any] = Field(
        None,
        description="The national character of the external database.",
    )
    stack_monitoring_config: Optional[Any] = Field(
        None,
        description="",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this ExternalContainerDatabaseSummary. The date and time the database was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the external database. It is a time zone offset (a character type in the format '[+|-]TZH:TZM') or a time zone region name, depending on how the time zone value was specified when the database was created / last altered.",
    )


def map_externalcontainerdatabasesummary(
    o: oci.database.models.ExternalContainerDatabaseSummary,
) -> ExternalContainerDatabaseSummary | None:
    """Map oci.database.models.ExternalContainerDatabaseSummary → ExternalContainerDatabaseSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExternalContainerDatabaseSummary(**data)
    except Exception:
        return ExternalContainerDatabaseSummary(
            character_set=getattr(o, "character_set", None),
            compartment_id=getattr(o, "compartment_id", None),
            database_configuration=getattr(o, "database_configuration", None),
            database_edition=getattr(o, "database_edition", None),
            database_management_config=getattr(o, "database_management_config", None),
            database_version=getattr(o, "database_version", None),
            db_id=getattr(o, "db_id", None),
            db_packs=getattr(o, "db_packs", None),
            db_unique_name=getattr(o, "db_unique_name", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            ncharacter_set=getattr(o, "ncharacter_set", None),
            stack_monitoring_config=getattr(o, "stack_monitoring_config", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
        )


class ExternalDatabaseConnectorSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExternalDatabaseConnectorSummary."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExternalDatabaseConnectorSummary. The `OCID`__ of the compartment.",
    )
    connection_status: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the connection_status of this ExternalDatabaseConnectorSummary. The status of connectivity to the external database.",
    )
    connector_type: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the connector_type of this ExternalDatabaseConnectorSummary. The type of connector used by the external database resource. Allowed values for this property are: \"MACS\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExternalDatabaseConnectorSummary. The user-friendly name for the :func:`create_external_database_connector_details`. The name does not have to be unique.",
    )
    external_database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the external_database_id of this ExternalDatabaseConnectorSummary. The `OCID`__ of the external database resource.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExternalDatabaseConnectorSummary. The `OCID`__ of the :func:`create_external_database_connector_details`.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the lifecycle_state of this ExternalDatabaseConnectorSummary. The current lifecycle state of the external database connector resource.",
    )
    time_connection_status_last_updated: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_connection_status_last_updated of this ExternalDatabaseConnectorSummary. The date and time the `connectionStatus` of this external connector was last updated.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this ExternalDatabaseConnectorSummary. The date and time the external connector was created.",
    )


def map_externaldatabaseconnectorsummary(
    o: oci.database.models.ExternalDatabaseConnectorSummary,
) -> ExternalDatabaseConnectorSummary | None:
    """Map oci.database.models.ExternalDatabaseConnectorSummary → ExternalDatabaseConnectorSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExternalDatabaseConnectorSummary(**data)
    except Exception:
        return ExternalDatabaseConnectorSummary(
            compartment_id=getattr(o, "compartment_id", None),
            connection_status=getattr(o, "connection_status", None),
            connector_type=getattr(o, "connector_type", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            external_database_id=getattr(o, "external_database_id", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_connection_status_last_updated=getattr(
                o, "time_connection_status_last_updated", None
            ),
            time_created=getattr(o, "time_created", None),
        )


class ExternalNonContainerDatabaseSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExternalNonContainerDatabaseSummary."""

    character_set: Optional[Any] = Field(
        None,
        description="The character set of the external database.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExternalNonContainerDatabaseSummary. The `OCID`__ of the compartment.",
    )
    database_configuration: Optional[Any] = Field(
        None,
        description="The Oracle Database configuration Allowed values for this property are: \"RAC\", \"SINGLE_INSTANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    database_edition: Optional[Any] = Field(
        None,
        description='The Oracle Database edition. Allowed values for this property are: "STANDARD_EDITION", "ENTERPRISE_EDITION", "ENTERPRISE_EDITION_HIGH_PERFORMANCE", "ENTERPRISE_EDITION_EXTREME_PERFORMANCE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    database_management_config: Optional[Any] = Field(
        None,
        description="",
    )
    database_version: Optional[Any] = Field(
        None,
        description="The Oracle Database version.",
    )
    db_id: Optional[Any] = Field(
        None,
        description="The Oracle Database ID, which identifies an Oracle Database located outside of Oracle Cloud.",
    )
    db_packs: Optional[Any] = Field(
        None,
        description="The database packs licensed for the external Oracle Database.",
    )
    db_unique_name: Optional[Any] = Field(
        None,
        description="The `DB_UNIQUE_NAME` of the external database.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExternalNonContainerDatabaseSummary. The user-friendly name for the external database. The name does not have to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExternalNonContainerDatabaseSummary. The `OCID`__ of the Oracle Cloud Infrastructure external database resource.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExternalNonContainerDatabaseSummary. The current state of the Oracle Cloud Infrastructure external database resource. Allowed values for this property are: "PROVISIONING", "NOT_CONNECTED", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    ncharacter_set: Optional[Any] = Field(
        None,
        description="The national character of the external database.",
    )
    operations_insights_config: Optional[Any] = Field(
        None,
        description="",
    )
    stack_monitoring_config: Optional[Any] = Field(
        None,
        description="",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this ExternalNonContainerDatabaseSummary. The date and time the database was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the external database. It is a time zone offset (a character type in the format '[+|-]TZH:TZM') or a time zone region name, depending on how the time zone value was specified when the database was created / last altered.",
    )


def map_externalnoncontainerdatabasesummary(
    o: oci.database.models.ExternalNonContainerDatabaseSummary,
) -> ExternalNonContainerDatabaseSummary | None:
    """Map oci.database.models.ExternalNonContainerDatabaseSummary → ExternalNonContainerDatabaseSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExternalNonContainerDatabaseSummary(**data)
    except Exception:
        return ExternalNonContainerDatabaseSummary(
            character_set=getattr(o, "character_set", None),
            compartment_id=getattr(o, "compartment_id", None),
            database_configuration=getattr(o, "database_configuration", None),
            database_edition=getattr(o, "database_edition", None),
            database_management_config=getattr(o, "database_management_config", None),
            database_version=getattr(o, "database_version", None),
            db_id=getattr(o, "db_id", None),
            db_packs=getattr(o, "db_packs", None),
            db_unique_name=getattr(o, "db_unique_name", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            ncharacter_set=getattr(o, "ncharacter_set", None),
            operations_insights_config=getattr(o, "operations_insights_config", None),
            stack_monitoring_config=getattr(o, "stack_monitoring_config", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
        )


class ExternalPluggableDatabaseSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExternalPluggableDatabaseSummary."""

    character_set: Optional[Any] = Field(
        None,
        description="The character set of the external database.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExternalPluggableDatabaseSummary. The `OCID`__ of the compartment.",
    )
    database_configuration: Optional[Any] = Field(
        None,
        description="The Oracle Database configuration Allowed values for this property are: \"RAC\", \"SINGLE_INSTANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    database_edition: Optional[Any] = Field(
        None,
        description='The Oracle Database edition. Allowed values for this property are: "STANDARD_EDITION", "ENTERPRISE_EDITION", "ENTERPRISE_EDITION_HIGH_PERFORMANCE", "ENTERPRISE_EDITION_EXTREME_PERFORMANCE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    database_management_config: Optional[Any] = Field(
        None,
        description="",
    )
    database_version: Optional[Any] = Field(
        None,
        description="The Oracle Database version.",
    )
    db_id: Optional[Any] = Field(
        None,
        description="The Oracle Database ID, which identifies an Oracle Database located outside of Oracle Cloud.",
    )
    db_packs: Optional[Any] = Field(
        None,
        description="The database packs licensed for the external Oracle Database.",
    )
    db_unique_name: Optional[Any] = Field(
        None,
        description="The `DB_UNIQUE_NAME` of the external database.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExternalPluggableDatabaseSummary. The user-friendly name for the external database. The name does not have to be unique.",
    )
    external_container_database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the external_container_database_id of this ExternalPluggableDatabaseSummary. The `OCID`__ of the :func:`create_external_container_database_details` that contains the specified :func:`create_external_pluggable_database_details` resource.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExternalPluggableDatabaseSummary. The `OCID`__ of the Oracle Cloud Infrastructure external database resource.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExternalPluggableDatabaseSummary. The current state of the Oracle Cloud Infrastructure external database resource. Allowed values for this property are: "PROVISIONING", "NOT_CONNECTED", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    ncharacter_set: Optional[Any] = Field(
        None,
        description="The national character of the external database.",
    )
    operations_insights_config: Optional[Any] = Field(
        None,
        description="",
    )
    source_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the the non-container database that was converted to a pluggable database to create this resource.",
    )
    stack_monitoring_config: Optional[Any] = Field(
        None,
        description="",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this ExternalPluggableDatabaseSummary. The date and time the database was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the external database. It is a time zone offset (a character type in the format '[+|-]TZH:TZM') or a time zone region name, depending on how the time zone value was specified when the database was created / last altered.",
    )


def map_externalpluggabledatabasesummary(
    o: oci.database.models.ExternalPluggableDatabaseSummary,
) -> ExternalPluggableDatabaseSummary | None:
    """Map oci.database.models.ExternalPluggableDatabaseSummary → ExternalPluggableDatabaseSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExternalPluggableDatabaseSummary(**data)
    except Exception:
        return ExternalPluggableDatabaseSummary(
            character_set=getattr(o, "character_set", None),
            compartment_id=getattr(o, "compartment_id", None),
            database_configuration=getattr(o, "database_configuration", None),
            database_edition=getattr(o, "database_edition", None),
            database_management_config=getattr(o, "database_management_config", None),
            database_version=getattr(o, "database_version", None),
            db_id=getattr(o, "db_id", None),
            db_packs=getattr(o, "db_packs", None),
            db_unique_name=getattr(o, "db_unique_name", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            external_container_database_id=getattr(
                o, "external_container_database_id", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            ncharacter_set=getattr(o, "ncharacter_set", None),
            operations_insights_config=getattr(o, "operations_insights_config", None),
            source_id=getattr(o, "source_id", None),
            stack_monitoring_config=getattr(o, "stack_monitoring_config", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
        )


class FlexComponentCollection(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.FlexComponentCollection."""

    items: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the items of this FlexComponentCollection.",
    )


def map_flexcomponentcollection(
    o: oci.database.models.FlexComponentCollection,
) -> FlexComponentCollection | None:
    """Map oci.database.models.FlexComponentCollection → FlexComponentCollection Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return FlexComponentCollection(**data)
    except Exception:
        return FlexComponentCollection(
            items=getattr(o, "items", None),
        )


class GiMinorVersionSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.GiMinorVersionSummary."""

    grid_image_id: Optional[Any] = Field(
        None,
        description="Grid Infrastructure Image Id",
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this GiMinorVersionSummary. A valid Oracle Grid Infrastructure (GI) software version.",
    )


def map_giminorversionsummary(
    o: oci.database.models.GiMinorVersionSummary,
) -> GiMinorVersionSummary | None:
    """Map oci.database.models.GiMinorVersionSummary → GiMinorVersionSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return GiMinorVersionSummary(**data)
    except Exception:
        return GiMinorVersionSummary(
            grid_image_id=getattr(o, "grid_image_id", None),
            version=getattr(o, "version", None),
        )


class GiVersionSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.GiVersionSummary."""

    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this GiVersionSummary. A valid Oracle Grid Infrastructure (GI) software version.",
    )


def map_giversionsummary(
    o: oci.database.models.GiVersionSummary,
) -> GiVersionSummary | None:
    """Map oci.database.models.GiVersionSummary → GiVersionSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return GiVersionSummary(**data)
    except Exception:
        return GiVersionSummary(
            version=getattr(o, "version", None),
        )


class KeyStoreSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.KeyStoreSummary."""

    associated_databases: Optional[Any] = Field(
        None,
        description="List of databases associated with the key store.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this KeyStoreSummary. The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this KeyStoreSummary. The user-friendly name for the key store. The name does not need to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this KeyStoreSummary. The `OCID`__ of the key store.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this KeyStoreSummary. The current state of the key store. Allowed values for this property are: "ACTIVE", "DELETED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the key store was created.",
    )
    type_details: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the type_details of this KeyStoreSummary.",
    )


def map_keystoresummary(
    o: oci.database.models.KeyStoreSummary,
) -> KeyStoreSummary | None:
    """Map oci.database.models.KeyStoreSummary → KeyStoreSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return KeyStoreSummary(**data)
    except Exception:
        return KeyStoreSummary(
            associated_databases=getattr(o, "associated_databases", None),
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_created=getattr(o, "time_created", None),
            type_details=getattr(o, "type_details", None),
        )


class MaintenanceRunHistorySummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.MaintenanceRunHistorySummary."""

    current_execution_window: Optional[Any] = Field(
        None,
        description="The OCID of the current execution window.",
    )
    db_servers_history_details: Optional[Any] = Field(
        None,
        description="List of database server history details.",
    )
    granular_maintenance_history: Optional[Any] = Field(
        None,
        description="The list of granular maintenance history details.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this MaintenanceRunHistorySummary. The OCID of the maintenance run history.",
    )
    maintenance_run_details: Optional[Any] = Field(
        None,
        description="",
    )


def map_maintenancerunhistorysummary(
    o: oci.database.models.MaintenanceRunHistorySummary,
) -> MaintenanceRunHistorySummary | None:
    """Map oci.database.models.MaintenanceRunHistorySummary → MaintenanceRunHistorySummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return MaintenanceRunHistorySummary(**data)
    except Exception:
        return MaintenanceRunHistorySummary(
            current_execution_window=getattr(o, "current_execution_window", None),
            db_servers_history_details=getattr(o, "db_servers_history_details", None),
            granular_maintenance_history=getattr(
                o, "granular_maintenance_history", None
            ),
            id=getattr(o, "id", None),
            maintenance_run_details=getattr(o, "maintenance_run_details", None),
        )


class MaintenanceRunSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.MaintenanceRunSummary."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this MaintenanceRunSummary. The OCID of the compartment.",
    )
    current_custom_action_timeout_in_mins: Optional[Any] = Field(
        None,
        description="Extend current custom action timeout between the current database servers during waiting state, from 0 (zero) to 30 minutes.",
    )
    current_patching_component: Optional[Any] = Field(
        None,
        description="The name of the current infrastruture component that is getting patched.",
    )
    custom_action_timeout_in_mins: Optional[Any] = Field(
        None,
        description="Determines the amount of time the system will wait before the start of each database server patching operation. Specify a number of minutes, from 15 to 120.",
    )
    database_software_image_id: Optional[Any] = Field(
        None,
        description="The Autonomous Database Software Image `OCID`__",
    )
    description: Optional[Any] = Field(
        None,
        description="Description of the maintenance run.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this MaintenanceRunSummary. The user-friendly name for the maintenance run.",
    )
    estimated_component_patching_start_time: Optional[Any] = Field(
        None,
        description="The estimated start time of the next infrastruture component patching operation.",
    )
    estimated_patching_time: Optional[Any] = Field(
        None,
        description="",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this MaintenanceRunSummary. The OCID of the maintenance run.",
    )
    is_custom_action_timeout_enabled: Optional[Any] = Field(
        None,
        description="If true, enables the configuration of a custom action timeout (waiting period) between database servers patching operations.",
    )
    is_dst_file_update_enabled: Optional[Any] = Field(
        None,
        description="Indicates if an automatic DST Time Zone file update is enabled for the Autonomous Container Database. If enabled along with Release Update, patching will be done in a Non-Rolling manner.",
    )
    is_maintenance_run_granular: Optional[Any] = Field(
        None,
        description="If `FALSE`, the maintenance run doesn't support granular maintenance.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this MaintenanceRunSummary. The current state of the maintenance run. For Autonomous Database Serverless instances, valid states are IN_PROGRESS, SUCCEEDED, and FAILED. Allowed values for this property are: "SCHEDULED", "IN_PROGRESS", "SUCCEEDED", "SKIPPED", "FAILED", "UPDATING", "DELETING", "DELETED", "CANCELED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_subtype: Optional[Any] = Field(
        None,
        description='Maintenance sub-type. Allowed values for this property are: "QUARTERLY", "HARDWARE", "CRITICAL", "INFRASTRUCTURE", "DATABASE", "ONEOFF", "SECURITY_MONTHLY", "TIMEZONE", "CUSTOM_DATABASE_SOFTWARE_IMAGE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_type: Optional[Any] = Field(
        None,
        description="Maintenance type. Allowed values for this property are: \"PLANNED\", \"UNPLANNED\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    patch_failure_count: Optional[Any] = Field(
        None,
        description="Contain the patch failure count.",
    )
    patch_id: Optional[Any] = Field(
        None,
        description="The unique identifier of the patch. The identifier string includes the patch type, the Oracle Database version, and the patch creation date (using the format YYMMDD). For example, the identifier `ru_patch_19.9.0.0_201030` is used for an RU patch for Oracle Database 19.9.0.0 that was released October 30, 2020.",
    )
    patching_end_time: Optional[Any] = Field(
        None,
        description="The time when the patching operation ended.",
    )
    patching_mode: Optional[Any] = Field(
        None,
        description='Cloud Exadata infrastructure node patching method, either "ROLLING" or "NONROLLING". Default value is ROLLING. *IMPORTANT*: Non-rolling infrastructure patching involves system down time. See `Oracle-Managed Infrastructure Maintenance Updates`__ for more information. Allowed values for this property are: "ROLLING", "NONROLLING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    patching_start_time: Optional[Any] = Field(
        None,
        description="The time when the patching operation started.",
    )
    patching_status: Optional[Any] = Field(
        None,
        description='The status of the patching operation. Allowed values for this property are: "PATCHING", "WAITING", "SCHEDULED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the maintenance run for the Autonomous Data Guard association's peer container database.",
    )
    target_db_server_version: Optional[Any] = Field(
        None,
        description="The target software version for the database server patching operation.",
    )
    target_resource_id: Optional[Any] = Field(
        None,
        description="The ID of the target resource on which the maintenance run occurs.",
    )
    target_resource_type: Optional[Any] = Field(
        None,
        description='The type of the target resource on which the maintenance run occurs. Allowed values for this property are: "AUTONOMOUS_EXADATA_INFRASTRUCTURE", "AUTONOMOUS_CONTAINER_DATABASE", "EXADATA_DB_SYSTEM", "CLOUD_EXADATA_INFRASTRUCTURE", "EXACC_INFRASTRUCTURE", "AUTONOMOUS_VM_CLUSTER", "AUTONOMOUS_DATABASE", "CLOUD_AUTONOMOUS_VM_CLUSTER", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    target_storage_server_version: Optional[Any] = Field(
        None,
        description="The target Cell version that is to be patched to.",
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time the maintenance run was completed.",
    )
    time_scheduled: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_scheduled of this MaintenanceRunSummary. The date and time the maintenance run is scheduled to occur.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="The date and time the maintenance run starts.",
    )
    total_time_taken_in_mins: Optional[Any] = Field(
        None,
        description="The total time taken by corresponding resource activity in minutes.",
    )


def map_maintenancerunsummary(
    o: oci.database.models.MaintenanceRunSummary,
) -> MaintenanceRunSummary | None:
    """Map oci.database.models.MaintenanceRunSummary → MaintenanceRunSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return MaintenanceRunSummary(**data)
    except Exception:
        return MaintenanceRunSummary(
            compartment_id=getattr(o, "compartment_id", None),
            current_custom_action_timeout_in_mins=getattr(
                o, "current_custom_action_timeout_in_mins", None
            ),
            current_patching_component=getattr(o, "current_patching_component", None),
            custom_action_timeout_in_mins=getattr(
                o, "custom_action_timeout_in_mins", None
            ),
            database_software_image_id=getattr(o, "database_software_image_id", None),
            description=getattr(o, "description", None),
            display_name=getattr(o, "display_name", None),
            estimated_component_patching_start_time=getattr(
                o, "estimated_component_patching_start_time", None
            ),
            estimated_patching_time=getattr(o, "estimated_patching_time", None),
            id=getattr(o, "id", None),
            is_custom_action_timeout_enabled=getattr(
                o, "is_custom_action_timeout_enabled", None
            ),
            is_dst_file_update_enabled=getattr(o, "is_dst_file_update_enabled", None),
            is_maintenance_run_granular=getattr(o, "is_maintenance_run_granular", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_subtype=getattr(o, "maintenance_subtype", None),
            maintenance_type=getattr(o, "maintenance_type", None),
            patch_failure_count=getattr(o, "patch_failure_count", None),
            patch_id=getattr(o, "patch_id", None),
            patching_end_time=getattr(o, "patching_end_time", None),
            patching_mode=getattr(o, "patching_mode", None),
            patching_start_time=getattr(o, "patching_start_time", None),
            patching_status=getattr(o, "patching_status", None),
            peer_maintenance_run_id=getattr(o, "peer_maintenance_run_id", None),
            target_db_server_version=getattr(o, "target_db_server_version", None),
            target_resource_id=getattr(o, "target_resource_id", None),
            target_resource_type=getattr(o, "target_resource_type", None),
            target_storage_server_version=getattr(
                o, "target_storage_server_version", None
            ),
            time_ended=getattr(o, "time_ended", None),
            time_scheduled=getattr(o, "time_scheduled", None),
            time_started=getattr(o, "time_started", None),
            total_time_taken_in_mins=getattr(o, "total_time_taken_in_mins", None),
        )


class OneoffPatchSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.OneoffPatchSummary."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this OneoffPatchSummary. The `OCID`__ of the compartment.",
    )
    db_version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_version of this OneoffPatchSummary. A valid Oracle Database version. For a list of supported versions, use the ListDbVersions operation. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, openMode, permissionLevel, dbWorkload, privateEndpointLabel, nsgIds, isRefreshable, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this OneoffPatchSummary. One-off patch name.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this OneoffPatchSummary. The `OCID`__ of the one-off patch.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Detailed message for the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this OneoffPatchSummary. The current state of the one-off patch. Allowed values for this property are: "CREATING", "AVAILABLE", "UPDATING", "INACTIVE", "FAILED", "EXPIRED", "DELETING", "DELETED", "TERMINATING", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    one_off_patches: Optional[Any] = Field(
        None,
        description="List of one-off patches for Database Homes.",
    )
    release_update: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the release_update of this OneoffPatchSummary. The PSU or PBP or Release Updates. To get a list of supported versions, use the :func:`list_db_versions` operation.",
    )
    sha256_sum: Optional[Any] = Field(
        None,
        description="SHA-256 checksum of the one-off patch.",
    )
    size_in_kbs: Optional[float] = Field(
        None,
        description="The size of one-off patch in kilobytes.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this OneoffPatchSummary. The date and time one-off patch was created.",
    )
    time_of_expiration: Optional[Any] = Field(
        None,
        description="The date and time until which the one-off patch will be available for download.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The date and time one-off patch was updated.",
    )


def map_oneoffpatchsummary(
    o: oci.database.models.OneoffPatchSummary,
) -> OneoffPatchSummary | None:
    """Map oci.database.models.OneoffPatchSummary → OneoffPatchSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return OneoffPatchSummary(**data)
    except Exception:
        return OneoffPatchSummary(
            compartment_id=getattr(o, "compartment_id", None),
            db_version=getattr(o, "db_version", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            one_off_patches=getattr(o, "one_off_patches", None),
            release_update=getattr(o, "release_update", None),
            sha256_sum=getattr(o, "sha256_sum", None),
            size_in_kbs=getattr(o, "size_in_kbs", None),
            time_created=getattr(o, "time_created", None),
            time_of_expiration=getattr(o, "time_of_expiration", None),
            time_updated=getattr(o, "time_updated", None),
        )


class PluggableDatabaseSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.PluggableDatabaseSummary."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this PluggableDatabaseSummary. The `OCID`__ of the compartment.",
    )
    connection_strings: Optional[Any] = Field(
        None,
        description="",
    )
    container_database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the container_database_id of this PluggableDatabaseSummary. The `OCID`__ of the CDB.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this PluggableDatabaseSummary. The `OCID`__ of the pluggable database.",
    )
    is_restricted: Optional[Any] = Field(
        None,
        description="The restricted mode of the pluggable database. If a pluggable database is opened in restricted mode, the user needs both create a session and have restricted session privileges to connect to it.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    kms_key_version_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container version that is used in database transparent data encryption (TDE) operations KMS Key can have multiple key versions. If none is specified, the current key version (latest) of the Key Id is used for the operation. Autonomous Database Serverless does not use key versions, hence is not applicable for Autonomous Database Serverless instances.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Detailed message for the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this PluggableDatabaseSummary. The current state of the pluggable database. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "TERMINATING", "TERMINATED", "UPDATING", "FAILED", "RELOCATING", "RELOCATED", "REFRESHING", "RESTORE_IN_PROGRESS", "RESTORE_FAILED", "BACKUP_IN_PROGRESS", "DISABLED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    open_mode: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the open_mode of this PluggableDatabaseSummary. **Deprecated.** Use :func:`pluggable_database_node_level_details` for OpenMode details. The mode that pluggable database is in. Open mode can only be changed to READ_ONLY or MIGRATE directly from the backend (within the Oracle Database software). Allowed values for this property are: "READ_ONLY", "READ_WRITE", "MOUNTED", "MIGRATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    pdb_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the pdb_name of this PluggableDatabaseSummary. The name for the pluggable database (PDB). The name is unique in the context of a :class:`Database`. The name must begin with an alphabetic character and can contain a maximum of thirty alphanumeric characters. Special characters are not permitted. The pluggable database name should not be same as the container database name.",
    )
    pdb_node_level_details: Optional[Any] = Field(
        None,
        description='Pluggable Database Node Level Details. Example: [{"nodeName" : "node1", "openMode" : "READ_WRITE"}, {"nodeName" : "node2", "openMode" : "READ_ONLY"}]',
    )
    pluggable_database_management_config: Optional[Any] = Field(
        None,
        description="",
    )
    refreshable_clone_config: Optional[Any] = Field(
        None,
        description="",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this PluggableDatabaseSummary. The date and time the pluggable database was created.",
    )


def map_pluggabledatabasesummary(
    o: oci.database.models.PluggableDatabaseSummary,
) -> PluggableDatabaseSummary | None:
    """Map oci.database.models.PluggableDatabaseSummary → PluggableDatabaseSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return PluggableDatabaseSummary(**data)
    except Exception:
        return PluggableDatabaseSummary(
            compartment_id=getattr(o, "compartment_id", None),
            connection_strings=getattr(o, "connection_strings", None),
            container_database_id=getattr(o, "container_database_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_restricted=getattr(o, "is_restricted", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            kms_key_version_id=getattr(o, "kms_key_version_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            open_mode=getattr(o, "open_mode", None),
            pdb_name=getattr(o, "pdb_name", None),
            pdb_node_level_details=getattr(o, "pdb_node_level_details", None),
            pluggable_database_management_config=getattr(
                o, "pluggable_database_management_config", None
            ),
            refreshable_clone_config=getattr(o, "refreshable_clone_config", None),
            time_created=getattr(o, "time_created", None),
        )


class ScheduledActionCollection(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ScheduledActionCollection."""

    items: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the items of this ScheduledActionCollection. List of Scheduled Action resources.",
    )


def map_scheduledactioncollection(
    o: oci.database.models.ScheduledActionCollection,
) -> ScheduledActionCollection | None:
    """Map oci.database.models.ScheduledActionCollection → ScheduledActionCollection Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ScheduledActionCollection(**data)
    except Exception:
        return ScheduledActionCollection(
            items=getattr(o, "items", None),
        )


class SchedulingPlanCollection(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.SchedulingPlanCollection."""

    items: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the items of this SchedulingPlanCollection. List of Scheduling Plan resources.",
    )


def map_schedulingplancollection(
    o: oci.database.models.SchedulingPlanCollection,
) -> SchedulingPlanCollection | None:
    """Map oci.database.models.SchedulingPlanCollection → SchedulingPlanCollection Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return SchedulingPlanCollection(**data)
    except Exception:
        return SchedulingPlanCollection(
            items=getattr(o, "items", None),
        )


class SchedulingPolicySummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.SchedulingPolicySummary."""

    cadence: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the cadence of this SchedulingPolicySummary. The cadence period. Allowed values for this property are: "HALFYEARLY", "QUARTERLY", "MONTHLY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    cadence_start_month: Optional[Any] = Field(
        None,
        description="Start of the month to be followed during the cadence period.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this SchedulingPolicySummary. The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this SchedulingPolicySummary. The user-friendly name for the Scheduling Policy. The name does not need to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this SchedulingPolicySummary. The `OCID`__ of the Scheduling Policy.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this SchedulingPolicySummary. The current state of the Scheduling Policy. Valid states are CREATING, NEEDS_ATTENTION, ACTIVE, UPDATING, FAILED, DELETING and DELETED. Allowed values for this property are: "CREATING", "NEEDS_ATTENTION", "AVAILABLE", "UPDATING", "FAILED", "DELETING", "DELETED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Scheduling Policy was created.",
    )
    time_next_window_starts: Optional[Any] = Field(
        None,
        description="The date and time of the next scheduling window associated with the schedulingPolicy is planned to start.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The last date and time that the Scheduling Policy was updated.",
    )


def map_schedulingpolicysummary(
    o: oci.database.models.SchedulingPolicySummary,
) -> SchedulingPolicySummary | None:
    """Map oci.database.models.SchedulingPolicySummary → SchedulingPolicySummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return SchedulingPolicySummary(**data)
    except Exception:
        return SchedulingPolicySummary(
            cadence=getattr(o, "cadence", None),
            cadence_start_month=getattr(o, "cadence_start_month", None),
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_created=getattr(o, "time_created", None),
            time_next_window_starts=getattr(o, "time_next_window_starts", None),
            time_updated=getattr(o, "time_updated", None),
        )


class SchedulingWindowSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.SchedulingWindowSummary."""

    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the Scheduling Window. The name does not need to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this SchedulingWindowSummary. The `OCID`__ of the Scheduling Window.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this SchedulingWindowSummary. The current state of the Scheduling Window. Valid states are CREATING, ACTIVE, UPDATING, FAILED, DELETING and DELETED. Allowed values for this property are: "CREATING", "AVAILABLE", "UPDATING", "FAILED", "DELETING", "DELETED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    scheduling_policy_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the scheduling_policy_id of this SchedulingWindowSummary. The `OCID`__ of the Scheduling Policy.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Scheduling Window was created.",
    )
    time_next_scheduling_window_starts: Optional[Any] = Field(
        None,
        description="The date and time of the next upcoming window associated within the schedulingWindow is planned to start.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The last date and time that the Scheduling Window was updated.",
    )
    window_preference: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the window_preference of this SchedulingWindowSummary.",
    )


def map_schedulingwindowsummary(
    o: oci.database.models.SchedulingWindowSummary,
) -> SchedulingWindowSummary | None:
    """Map oci.database.models.SchedulingWindowSummary → SchedulingWindowSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return SchedulingWindowSummary(**data)
    except Exception:
        return SchedulingWindowSummary(
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            scheduling_policy_id=getattr(o, "scheduling_policy_id", None),
            time_created=getattr(o, "time_created", None),
            time_next_scheduling_window_starts=getattr(
                o, "time_next_scheduling_window_starts", None
            ),
            time_updated=getattr(o, "time_updated", None),
            window_preference=getattr(o, "window_preference", None),
        )


class SystemVersionCollection(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.SystemVersionCollection."""

    items: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the items of this SystemVersionCollection. List of System versions.",
    )


def map_systemversioncollection(
    o: oci.database.models.SystemVersionCollection,
) -> SystemVersionCollection | None:
    """Map oci.database.models.SystemVersionCollection → SystemVersionCollection Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return SystemVersionCollection(**data)
    except Exception:
        return SystemVersionCollection(
            items=getattr(o, "items", None),
        )


class VmClusterNetworkSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.VmClusterNetworkSummary."""

    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the VM cluster network. The name does not need to be unique.",
    )
    dns: Optional[Any] = Field(
        None,
        description="The list of DNS server IP addresses. Maximum of 3 allowed.",
    )
    dr_scans: Optional[Any] = Field(
        None,
        description="The SCAN details for DR network",
    )
    exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Exadata infrastructure.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the VM cluster network.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the VM cluster network. CREATING - The resource is being created REQUIRES_VALIDATION - The resource is created and may not be usable until it is validated. VALIDATING - The resource is being validated and not available to use. VALIDATED - The resource is validated and is available for consumption by VM cluster. VALIDATION_FAILED - The resource validation has failed and might require user input to be corrected. UPDATING - The resource is being updated and not available to use. ALLOCATED - The resource is is currently being used by VM cluster. TERMINATING - The resource is being deleted and not available to use. TERMINATED - The resource is deleted and unavailable. FAILED - The resource is in a failed state due to validation or other errors. NEEDS_ATTENTION - The resource is in needs attention state as some of it\'s child nodes are not validated and unusable by VM cluster. Allowed values for this property are: "CREATING", "REQUIRES_VALIDATION", "VALIDATING", "VALIDATED", "VALIDATION_FAILED", "UPDATING", "ALLOCATED", "TERMINATING", "TERMINATED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    ntp: Optional[Any] = Field(
        None,
        description="The list of NTP server IP addresses. Maximum of 3 allowed.",
    )
    scans: Optional[Any] = Field(
        None,
        description="The SCAN details.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time when the VM cluster network was created.",
    )
    vm_cluster_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the associated VM Cluster.",
    )
    vm_networks: Optional[Any] = Field(
        None,
        description="Details of the client and backup networks.",
    )


def map_vmclusternetworksummary(
    o: oci.database.models.VmClusterNetworkSummary,
) -> VmClusterNetworkSummary | None:
    """Map oci.database.models.VmClusterNetworkSummary → VmClusterNetworkSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return VmClusterNetworkSummary(**data)
    except Exception:
        return VmClusterNetworkSummary(
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            dns=getattr(o, "dns", None),
            dr_scans=getattr(o, "dr_scans", None),
            exadata_infrastructure_id=getattr(o, "exadata_infrastructure_id", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            ntp=getattr(o, "ntp", None),
            scans=getattr(o, "scans", None),
            time_created=getattr(o, "time_created", None),
            vm_cluster_id=getattr(o, "vm_cluster_id", None),
            vm_networks=getattr(o, "vm_networks", None),
        )


class VmClusterUpdateSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.VmClusterUpdateSummary."""

    available_actions: Optional[Any] = Field(
        None,
        description='The possible actions that can be performed using this maintenance update. Allowed values for items in this list are: "ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    description: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the description of this VmClusterUpdateSummary. Details of the maintenance update package.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this VmClusterUpdateSummary. The `OCID`__ of the maintenance update.",
    )
    last_action: Optional[Any] = Field(
        None,
        description='The update action performed most recently using this maintenance update. Allowed values for this property are: "ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Descriptive text providing additional details about the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the maintenance update. Dependent on value of `lastAction`. Allowed values for this property are: "AVAILABLE", "SUCCESS", "IN_PROGRESS", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_released: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_released of this VmClusterUpdateSummary. The date and time the maintenance update was released.",
    )
    update_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the update_type of this VmClusterUpdateSummary. The type of VM cluster maintenance update. Allowed values for this property are: "GI_UPGRADE", "GI_PATCH", "OS_UPDATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this VmClusterUpdateSummary. The version of the maintenance update package.",
    )


def map_vmclusterupdatesummary(
    o: oci.database.models.VmClusterUpdateSummary,
) -> VmClusterUpdateSummary | None:
    """Map oci.database.models.VmClusterUpdateSummary → VmClusterUpdateSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return VmClusterUpdateSummary(**data)
    except Exception:
        return VmClusterUpdateSummary(
            available_actions=getattr(o, "available_actions", None),
            description=getattr(o, "description", None),
            id=getattr(o, "id", None),
            last_action=getattr(o, "last_action", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_released=getattr(o, "time_released", None),
            update_type=getattr(o, "update_type", None),
            version=getattr(o, "version", None),
        )


class VmClusterSummary(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.VmClusterSummary."""

    availability_domain: Optional[Any] = Field(
        None,
        description="The name of the availability domain that the VM cluster is located in.",
    )
    cloud_automation_update_details: Optional[Any] = Field(
        None,
        description="",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    cpus_enabled: Optional[Any] = Field(
        None,
        description="The number of enabled CPU cores.",
    )
    data_collection_options: Optional[Any] = Field(
        None,
        description="",
    )
    data_storage_size_in_gbs: Optional[float] = Field(
        None,
        description="Size of the DATA disk group in GBs.",
    )
    data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="Size, in terabytes, of the DATA disk group.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage allocated in GBs.",
    )
    db_servers: Optional[Any] = Field(
        None,
        description="The list of Db server.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the Exadata Cloud@Customer VM cluster. The name does not need to be unique.",
    )
    exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Exadata infrastructure.",
    )
    exascale_db_storage_vault_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Exadata Database Storage Vault.",
    )
    file_system_configuration_details: Optional[Any] = Field(
        None,
        description="Details of the file system configuration of the VM cluster.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    gi_software_image_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of a grid infrastructure software image. This is a database software image of the type `GRID_IMAGE`.",
    )
    gi_version: Optional[Any] = Field(
        None,
        description="The Oracle Grid Infrastructure software version for the VM cluster.",
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the VM cluster.",
    )
    is_local_backup_enabled: Optional[Any] = Field(
        None,
        description="If true, database backup on local Exadata storage is configured for the VM cluster. If false, database backup on local Exadata storage is not available in the VM cluster.",
    )
    is_sparse_diskgroup_enabled: Optional[Any] = Field(
        None,
        description="If true, sparse disk group is configured for the VM cluster. If false, sparse disk group is not created.",
    )
    last_patch_history_entry_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last patch history. This value is updated as soon as a patch operation starts.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to the VM cluster. The default is LICENSE_INCLUDED. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the VM cluster. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory allocated in GBs.",
    )
    ocpus_enabled: Optional[float] = Field(
        None,
        description="The number of enabled OCPU cores.",
    )
    shape: Optional[Any] = Field(
        None,
        description="The shape of the Exadata infrastructure. The shape determines the amount of CPU, storage, and memory resources allocated to the instance.",
    )
    ssh_public_keys: Optional[Any] = Field(
        None,
        description="The public key portion of one or more key pairs used for SSH access to the VM cluster.",
    )
    storage_management_type: Optional[Any] = Field(
        None,
        description="Specifies whether the type of storage management for the VM cluster is ASM or Exascale. Allowed values for this property are: \"ASM\", \"EXASCALE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    system_version: Optional[Any] = Field(
        None,
        description="Operating system version of the image.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the VM cluster was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the Exadata infrastructure. For details, see `Exadata Infrastructure Time Zones`__.",
    )
    vm_cluster_network_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the VM cluster network.",
    )


def map_vmclustersummary(
    o: oci.database.models.VmClusterSummary,
) -> VmClusterSummary | None:
    """Map oci.database.models.VmClusterSummary → VmClusterSummary Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return VmClusterSummary(**data)
    except Exception:
        return VmClusterSummary(
            availability_domain=getattr(o, "availability_domain", None),
            cloud_automation_update_details=getattr(
                o, "cloud_automation_update_details", None
            ),
            compartment_id=getattr(o, "compartment_id", None),
            compute_model=getattr(o, "compute_model", None),
            cpus_enabled=getattr(o, "cpus_enabled", None),
            data_collection_options=getattr(o, "data_collection_options", None),
            data_storage_size_in_gbs=getattr(o, "data_storage_size_in_gbs", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_servers=getattr(o, "db_servers", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            exadata_infrastructure_id=getattr(o, "exadata_infrastructure_id", None),
            exascale_db_storage_vault_id=getattr(
                o, "exascale_db_storage_vault_id", None
            ),
            file_system_configuration_details=getattr(
                o, "file_system_configuration_details", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            gi_software_image_id=getattr(o, "gi_software_image_id", None),
            gi_version=getattr(o, "gi_version", None),
            id=getattr(o, "id", None),
            is_local_backup_enabled=getattr(o, "is_local_backup_enabled", None),
            is_sparse_diskgroup_enabled=getattr(o, "is_sparse_diskgroup_enabled", None),
            last_patch_history_entry_id=getattr(o, "last_patch_history_entry_id", None),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            ocpus_enabled=getattr(o, "ocpus_enabled", None),
            shape=getattr(o, "shape", None),
            ssh_public_keys=getattr(o, "ssh_public_keys", None),
            storage_management_type=getattr(o, "storage_management_type", None),
            system_version=getattr(o, "system_version", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
            vm_cluster_network_id=getattr(o, "vm_cluster_network_id", None),
        )


class ResourcePoolShapeCollection(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ResourcePoolShapeCollection."""

    items: Optional[Any] = Field(
        None,
        description="List of Autonomous Database resource pools Shapes.",
    )


def map_resourcepoolshapecollection(
    o: oci.database.models.ResourcePoolShapeCollection,
) -> ResourcePoolShapeCollection | None:
    """Map oci.database.models.ResourcePoolShapeCollection → ResourcePoolShapeCollection Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ResourcePoolShapeCollection(**data)
    except Exception:
        return ResourcePoolShapeCollection(
            items=getattr(o, "items", None),
        )


class ApplicationVip(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ApplicationVip."""

    cloud_vm_cluster_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cloud_vm_cluster_id of this ApplicationVip. The `OCID`__ of the cloud VM cluster associated with the application virtual IP (VIP) address.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    hostname_label: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the hostname_label of this ApplicationVip. The hostname of the application virtual IP (VIP) address.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ApplicationVip. The `OCID`__ of the application virtual IP (VIP) address.",
    )
    ip_address: Optional[Any] = Field(
        None,
        description="The application virtual IP (VIP) address.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state of the application virtual IP (VIP) address.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ApplicationVip. The current lifecycle state of the application virtual IP (VIP) address. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the subnet associated with the application virtual IP (VIP) address.",
    )
    time_assigned: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_assigned of this ApplicationVip. The date and time when the create operation for the application virtual IP (VIP) address completed.",
    )


def map_applicationvip(o: oci.database.models.ApplicationVip) -> ApplicationVip | None:
    """Map oci.database.models.ApplicationVip → ApplicationVip Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ApplicationVip(**data)
    except Exception:
        return ApplicationVip(
            cloud_vm_cluster_id=getattr(o, "cloud_vm_cluster_id", None),
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            hostname_label=getattr(o, "hostname_label", None),
            id=getattr(o, "id", None),
            ip_address=getattr(o, "ip_address", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            subnet_id=getattr(o, "subnet_id", None),
            time_assigned=getattr(o, "time_assigned", None),
        )


class AutonomousContainerDatabase(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousContainerDatabase."""

    associated_backup_configuration_details: Optional[Any] = Field(
        None,
        description="A backup config object holds information about preferred backup destinations only. This object holds information about the associated backup destinations, such as secondary backup destinations created for local backups or remote replicated backups.",
    )
    autonomous_exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="**No longer used.** For Autonomous Database on dedicated Exadata infrastructure, the container database is created within a specified `cloudAutonomousVmCluster`.",
    )
    autonomous_vm_cluster_id: Optional[Any] = Field(
        None,
        description="The OCID of the Autonomous VM Cluster.",
    )
    availability_domain: Optional[Any] = Field(
        None,
        description="The availability domain of the Autonomous Container Database.",
    )
    available_cpus: Optional[float] = Field(
        None,
        description="Sum of CPUs available on the Autonomous VM Cluster + Sum of reclaimable CPUs available in the Autonomous Container Database.",
    )
    backup_config: Optional[Any] = Field(
        None,
        description="",
    )
    backup_destination_properties_list: Optional[Any] = Field(
        None,
        description="This list describes the backup destination properties associated with the Autonomous Container Database (ACD) 's preferred backup destination. The object at a given index is associated with the destination present at the same index in the backup destination details list of the ACD Backup Configuration.",
    )
    cloud_autonomous_vm_cluster_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the cloud Autonomous Exadata VM Cluster.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this AutonomousContainerDatabase. The OCID of the compartment.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Container Database. For Autonomous Database on Dedicated Exadata Infrastructure, the CPU type (ECPUs or OCPUs) is determined by the parent Autonomous Exadata VM Cluster's compute model. ECPU compute model is the recommended model and OCPU compute model is legacy. See `Compute Models in Autonomous Database on Dedicated Exadata Infrastructure`__ for more details. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    db_name: Optional[Any] = Field(
        None,
        description="The Database name for the Autonomous Container Database. The name must be unique within the Cloud Autonomous VM Cluster, starting with an alphabetic character, followed by 1 to 7 alphanumeric characters.",
    )
    db_split_threshold: Optional[Any] = Field(
        None,
        description="The CPU value beyond which an Autonomous Database will be opened across multiple nodes. The default value of this attribute is 16 for OCPUs and 64 for ECPUs.",
    )
    db_unique_name: Optional[Any] = Field(
        None,
        description="**Deprecated.** The `DB_UNIQUE_NAME` value is set by Oracle Cloud Infrastructure. Do not specify a value for this parameter. Specifying a value for this field will cause Terraform operations to fail.",
    )
    db_version: Optional[Any] = Field(
        None,
        description="Oracle Database version of the Autonomous Container Database.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this AutonomousContainerDatabase. The user-provided name for the Autonomous Container Database.",
    )
    distribution_affinity: Optional[Any] = Field(
        None,
        description="Determines whether an Autonomous Database must be opened across the maximum number of nodes or the least number of nodes. By default, Minimum nodes is selected. Allowed values for this property are: \"MINIMUM_DISTRIBUTION\", \"MAXIMUM_DISTRIBUTION\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    dst_file_version: Optional[Any] = Field(
        None,
        description="DST Time-Zone File version of the Autonomous Container Database.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousContainerDatabase. The OCID of the Autonomous Container Database.",
    )
    infrastructure_type: Optional[Any] = Field(
        None,
        description="The infrastructure type this resource belongs to. Allowed values for this property are: \"CLOUD\", \"CLOUD_AT_CUSTOMER\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    is_dst_file_update_enabled: Optional[Any] = Field(
        None,
        description="Indicates if an automatic DST Time Zone file update is enabled for the Autonomous Container Database. If enabled along with Release Update, patching will be done in a Non-Rolling manner.",
    )
    key_history_entry: Optional[Any] = Field(
        None,
        description="Key History Entry.",
    )
    key_store_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the key store of Oracle Vault.",
    )
    key_store_wallet_name: Optional[Any] = Field(
        None,
        description="The wallet name for Oracle Key Vault.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    kms_key_version_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container version that is used in database transparent data encryption (TDE) operations KMS Key can have multiple key versions. If none is specified, the current key version (latest) of the Key Id is used for the operation. Autonomous Database Serverless does not use key versions, hence is not applicable for Autonomous Database Serverless instances.",
    )
    largest_provisionable_autonomous_database_in_cpus: Optional[float] = Field(
        None,
        description="The largest Autonomous Database (CPU) that can be created in a new Autonomous Container Database.",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousContainerDatabase. The current state of the Autonomous Container Database. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "BACKUP_IN_PROGRESS", "RESTORING", "RESTORE_FAILED", "RESTARTING", "MAINTENANCE_IN_PROGRESS", "ROLE_CHANGE_IN_PROGRESS", "ENABLING_AUTONOMOUS_DATA_GUARD", "UNAVAILABLE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    list_one_off_patches: Optional[Any] = Field(
        None,
        description="List of One-Off patches that has been successfully applied to Autonomous Container Database",
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="",
    )
    memory_per_oracle_compute_unit_in_gbs: Optional[Any] = Field(
        None,
        description="The amount of memory (in GBs) enabled per ECPU or OCPU in the Autonomous VM Cluster.",
    )
    net_services_architecture: Optional[Any] = Field(
        None,
        description="Enabling SHARED server architecture enables a database server to allow many client processes to share very few server processes, thereby increasing the number of supported users. Allowed values for this property are: \"DEDICATED\", \"SHARED\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    patch_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last patch applied on the system.",
    )
    patch_model: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the patch_model of this AutonomousContainerDatabase. Database patch model preference. Allowed values for this property are: \"RELEASE_UPDATES\", \"RELEASE_UPDATE_REVISIONS\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    provisionable_cpus: Optional[Any] = Field(
        None,
        description="An array of CPU values that can be used to successfully provision a single Autonomous Database.",
    )
    provisioned_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs provisioned in an Autonomous Container Database.",
    )
    reclaimable_cpus: Optional[float] = Field(
        None,
        description="CPUs that continue to be included in the count of CPUs available to the Autonomous Container Database even after one of its Autonomous Database is terminated or scaled down. You can release them to the available CPUs at its parent Autonomous VM Cluster level by restarting the Autonomous Container Database.",
    )
    recovery_appliance_details: Optional[Any] = Field(
        None,
        description="",
    )
    reserved_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs reserved in an Autonomous Container Database.",
    )
    role: Optional[Any] = Field(
        None,
        description='The Data Guard role of the Autonomous Container Database or Autonomous Database, if Autonomous Data Guard is enabled. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", "BACKUP_COPY", "SNAPSHOT_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    service_level_agreement_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the service_level_agreement_type of this AutonomousContainerDatabase. The service level agreement type of the container database. The default is STANDARD. Allowed values for this property are: "STANDARD", "MISSION_CRITICAL", "AUTONOMOUS_DATAGUARD", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    standby_maintenance_buffer_in_days: Optional[Any] = Field(
        None,
        description="The scheduling detail for the quarterly maintenance window of the standby Autonomous Container Database. This value represents the number of days before scheduled maintenance of the primary database.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Autonomous Container Database was created.",
    )
    time_of_last_backup: Optional[Any] = Field(
        None,
        description="The timestamp of last successful backup. Here NULL value represents either there are no successful backups or backups are not configured for this Autonomous Container Database.",
    )
    time_snapshot_standby_revert: Optional[Any] = Field(
        None,
        description="The date and time the Autonomous Container Database will be reverted to Standby from Snapshot Standby.",
    )
    total_cpus: Optional[Any] = Field(
        None,
        description="The number of CPUs allocated to the Autonomous VM cluster.",
    )
    vault_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Oracle Cloud Infrastructure `vault`__. This parameter and `secretId` are required for Customer Managed Keys.",
    )
    version_preference: Optional[Any] = Field(
        None,
        description="The next maintenance version preference. Allowed values for this property are: \"NEXT_RELEASE_UPDATE\", \"LATEST_RELEASE_UPDATE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    vm_failover_reservation: Optional[Any] = Field(
        None,
        description="The percentage of CPUs reserved across nodes to support node failover. Allowed values are 0%, 25%, and 50%, with 50% being the default option.",
    )


def map_autonomouscontainerdatabase(
    o: oci.database.models.AutonomousContainerDatabase,
) -> AutonomousContainerDatabase | None:
    """Map oci.database.models.AutonomousContainerDatabase → AutonomousContainerDatabase Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousContainerDatabase(**data)
    except Exception:
        return AutonomousContainerDatabase(
            associated_backup_configuration_details=getattr(
                o, "associated_backup_configuration_details", None
            ),
            autonomous_exadata_infrastructure_id=getattr(
                o, "autonomous_exadata_infrastructure_id", None
            ),
            autonomous_vm_cluster_id=getattr(o, "autonomous_vm_cluster_id", None),
            availability_domain=getattr(o, "availability_domain", None),
            available_cpus=getattr(o, "available_cpus", None),
            backup_config=getattr(o, "backup_config", None),
            backup_destination_properties_list=getattr(
                o, "backup_destination_properties_list", None
            ),
            cloud_autonomous_vm_cluster_id=getattr(
                o, "cloud_autonomous_vm_cluster_id", None
            ),
            compartment_id=getattr(o, "compartment_id", None),
            compute_model=getattr(o, "compute_model", None),
            db_name=getattr(o, "db_name", None),
            db_split_threshold=getattr(o, "db_split_threshold", None),
            db_unique_name=getattr(o, "db_unique_name", None),
            db_version=getattr(o, "db_version", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            distribution_affinity=getattr(o, "distribution_affinity", None),
            dst_file_version=getattr(o, "dst_file_version", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            infrastructure_type=getattr(o, "infrastructure_type", None),
            is_dst_file_update_enabled=getattr(o, "is_dst_file_update_enabled", None),
            key_history_entry=getattr(o, "key_history_entry", None),
            key_store_id=getattr(o, "key_store_id", None),
            key_store_wallet_name=getattr(o, "key_store_wallet_name", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            kms_key_version_id=getattr(o, "kms_key_version_id", None),
            largest_provisionable_autonomous_database_in_cpus=getattr(
                o, "largest_provisionable_autonomous_database_in_cpus", None
            ),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            list_one_off_patches=getattr(o, "list_one_off_patches", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            memory_per_oracle_compute_unit_in_gbs=getattr(
                o, "memory_per_oracle_compute_unit_in_gbs", None
            ),
            net_services_architecture=getattr(o, "net_services_architecture", None),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            patch_id=getattr(o, "patch_id", None),
            patch_model=getattr(o, "patch_model", None),
            provisionable_cpus=getattr(o, "provisionable_cpus", None),
            provisioned_cpus=getattr(o, "provisioned_cpus", None),
            reclaimable_cpus=getattr(o, "reclaimable_cpus", None),
            recovery_appliance_details=getattr(o, "recovery_appliance_details", None),
            reserved_cpus=getattr(o, "reserved_cpus", None),
            role=getattr(o, "role", None),
            service_level_agreement_type=getattr(
                o, "service_level_agreement_type", None
            ),
            standby_maintenance_buffer_in_days=getattr(
                o, "standby_maintenance_buffer_in_days", None
            ),
            time_created=getattr(o, "time_created", None),
            time_of_last_backup=getattr(o, "time_of_last_backup", None),
            time_snapshot_standby_revert=getattr(
                o, "time_snapshot_standby_revert", None
            ),
            total_cpus=getattr(o, "total_cpus", None),
            vault_id=getattr(o, "vault_id", None),
            version_preference=getattr(o, "version_preference", None),
            vm_failover_reservation=getattr(o, "vm_failover_reservation", None),
        )


class AutonomousContainerDatabaseDataguardAssociation(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousContainerDatabaseDataguardAssociation."""

    apply_lag: Optional[Any] = Field(
        None,
        description="The lag time between updates to the primary Autonomous Container Database and application of the redo data on the standby Autonomous Container Database, as computed by the reporting database. Example: `9 seconds`",
    )
    apply_rate: Optional[Any] = Field(
        None,
        description="The rate at which redo logs are synchronized between the associated Autonomous Container Databases. Example: `180 Mb per second`",
    )
    autonomous_container_database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the autonomous_container_database_id of this AutonomousContainerDatabaseDataguardAssociation. The `OCID`__ of the Autonomous Container Database that has a relationship with the peer Autonomous Container Database. Used only by Autonomous Database on Dedicated Exadata Infrastructure.",
    )
    fast_start_fail_over_lag_limit_in_seconds: Optional[Any] = Field(
        None,
        description="The lag time for my preference based on data loss tolerance in seconds.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousContainerDatabaseDataguardAssociation. The OCID of the Autonomous Data Guard created for a given Autonomous Container Database.",
    )
    is_automatic_failover_enabled: Optional[Any] = Field(
        None,
        description="Indicates whether Automatic Failover is enabled for Autonomous Container Database Dataguard Association",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycleState, if available.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousContainerDatabaseDataguardAssociation. The current state of Autonomous Data Guard. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "ROLE_CHANGE_IN_PROGRESS", "TERMINATING", "TERMINATED", "FAILED", "UNAVAILABLE", "UPDATING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_autonomous_container_database_dataguard_association_id: Optional[Any] = Field(
        None,
        description="The OCID of the peer Autonomous Container Database-Autonomous Data Guard association.",
    )
    peer_autonomous_container_database_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the peer Autonomous Container Database.",
    )
    peer_lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the Autonomous Container Database. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "BACKUP_IN_PROGRESS", "RESTORING", "RESTORE_FAILED", "RESTARTING", "MAINTENANCE_IN_PROGRESS", "ROLE_CHANGE_IN_PROGRESS", "ENABLING_AUTONOMOUS_DATA_GUARD", "UNAVAILABLE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_role: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the peer_role of this AutonomousContainerDatabaseDataguardAssociation. The Data Guard role of the Autonomous Container Database or Autonomous Database, if Autonomous Data Guard is enabled. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", "BACKUP_COPY", "SNAPSHOT_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    protection_mode: Optional[Any] = Field(
        None,
        description="The protection mode of this Autonomous Data Guard association. For more information, see `Oracle Data Guard Protection Modes`__ in the Oracle Data Guard documentation. Allowed values for this property are: \"MAXIMUM_AVAILABILITY\", \"MAXIMUM_PERFORMANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    role: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the role of this AutonomousContainerDatabaseDataguardAssociation. The Data Guard role of the Autonomous Container Database or Autonomous Database, if Autonomous Data Guard is enabled. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", "BACKUP_COPY", "SNAPSHOT_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Autonomous DataGuard association was created.",
    )
    time_last_role_changed: Optional[Any] = Field(
        None,
        description="The date and time when the last role change action happened.",
    )
    time_last_synced: Optional[Any] = Field(
        None,
        description="The date and time of the last update to the apply lag, apply rate, and transport lag values.",
    )
    transport_lag: Optional[Any] = Field(
        None,
        description="The approximate number of seconds of redo data not yet available on the standby Autonomous Container Database, as computed by the reporting database. Example: `7 seconds`",
    )


def map_autonomouscontainerdatabasedataguardassociation(
    o: oci.database.models.AutonomousContainerDatabaseDataguardAssociation,
) -> AutonomousContainerDatabaseDataguardAssociation | None:
    """Map oci.database.models.AutonomousContainerDatabaseDataguardAssociation → AutonomousContainerDatabaseDataguardAssociation Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousContainerDatabaseDataguardAssociation(**data)
    except Exception:
        return AutonomousContainerDatabaseDataguardAssociation(
            apply_lag=getattr(o, "apply_lag", None),
            apply_rate=getattr(o, "apply_rate", None),
            autonomous_container_database_id=getattr(
                o, "autonomous_container_database_id", None
            ),
            fast_start_fail_over_lag_limit_in_seconds=getattr(
                o, "fast_start_fail_over_lag_limit_in_seconds", None
            ),
            id=getattr(o, "id", None),
            is_automatic_failover_enabled=getattr(
                o, "is_automatic_failover_enabled", None
            ),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            peer_autonomous_container_database_dataguard_association_id=getattr(
                o, "peer_autonomous_container_database_dataguard_association_id", None
            ),
            peer_autonomous_container_database_id=getattr(
                o, "peer_autonomous_container_database_id", None
            ),
            peer_lifecycle_state=getattr(o, "peer_lifecycle_state", None),
            peer_role=getattr(o, "peer_role", None),
            protection_mode=getattr(o, "protection_mode", None),
            role=getattr(o, "role", None),
            time_created=getattr(o, "time_created", None),
            time_last_role_changed=getattr(o, "time_last_role_changed", None),
            time_last_synced=getattr(o, "time_last_synced", None),
            transport_lag=getattr(o, "transport_lag", None),
        )


class AutonomousContainerDatabaseResourceUsage(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousContainerDatabaseResourceUsage."""

    autonomous_container_database_vm_usage: Optional[Any] = Field(
        None,
        description="List of autonomous container database resource usage per autonomous virtual machine.",
    )
    available_cpus: Optional[float] = Field(
        None,
        description="CPUs available for provisioning or scaling an Autonomous Database in the Autonomous Container Database.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this AutonomousContainerDatabaseResourceUsage. The user-friendly name for the Autonomous Container Database. The name does not need to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Autonomous Container Database.",
    )
    largest_provisionable_autonomous_database_in_cpus: Optional[float] = Field(
        None,
        description="Largest provisionable ADB in the Autonomous Container Database.",
    )
    provisionable_cpus: Optional[Any] = Field(
        None,
        description="Valid list of provisionable CPUs for Autonomous Database.",
    )
    provisioned_cpus: Optional[float] = Field(
        None,
        description="CPUs / cores assigned to ADBs in the Autonomous Container Database.",
    )
    reclaimable_cpus: Optional[float] = Field(
        None,
        description="Number of CPUs that are reclaimable or released to the AVMC on Autonomous Container Database restart.",
    )
    reserved_cpus: Optional[float] = Field(
        None,
        description="CPUs / cores reserved for scalability, resilliency and other overheads. This includes failover, autoscaling and idle instance overhead.",
    )
    used_cpus: Optional[float] = Field(
        None,
        description="CPUs / cores assigned to the Autonomous Container Database. Sum of provisioned, reserved and reclaimable CPUs/ cores.",
    )


def map_autonomouscontainerdatabaseresourceusage(
    o: oci.database.models.AutonomousContainerDatabaseResourceUsage,
) -> AutonomousContainerDatabaseResourceUsage | None:
    """Map oci.database.models.AutonomousContainerDatabaseResourceUsage → AutonomousContainerDatabaseResourceUsage Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousContainerDatabaseResourceUsage(**data)
    except Exception:
        return AutonomousContainerDatabaseResourceUsage(
            autonomous_container_database_vm_usage=getattr(
                o, "autonomous_container_database_vm_usage", None
            ),
            available_cpus=getattr(o, "available_cpus", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            largest_provisionable_autonomous_database_in_cpus=getattr(
                o, "largest_provisionable_autonomous_database_in_cpus", None
            ),
            provisionable_cpus=getattr(o, "provisionable_cpus", None),
            provisioned_cpus=getattr(o, "provisioned_cpus", None),
            reclaimable_cpus=getattr(o, "reclaimable_cpus", None),
            reserved_cpus=getattr(o, "reserved_cpus", None),
            used_cpus=getattr(o, "used_cpus", None),
        )


class AutonomousDatabase(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDatabase."""

    actual_used_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The current amount of storage in use for user and system data, in terabytes (TB).",
    )
    allocated_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The amount of storage currently allocated for the database tables and billed for, rounded up. When auto-scaling is not enabled, this value is equal to the `dataStorageSizeInTBs` value. You can compare this value to the `actualUsedDataStorageSizeInTBs` value to determine if a manual shrink operation is appropriate for your allocated storage. **Note:** Auto-scaling does not automatically decrease allocated storage when data is deleted from the database.",
    )
    apex_details: Optional[Any] = Field(
        None,
        description="Information about Oracle APEX Application Development.",
    )
    are_primary_whitelisted_ips_used: Optional[Any] = Field(
        None,
        description="This field will be null if the Autonomous Database is not Data Guard enabled or Access Control is disabled. It's value would be `TRUE` if Autonomous Database is Data Guard enabled and Access Control is enabled and if the Autonomous Database uses primary IP access control list (ACL) for standby. It's value would be `FALSE` if Autonomous Database is Data Guard enabled and Access Control is enabled and if the Autonomous Database uses different IP access control list (ACL) for standby compared to primary.",
    )
    auto_refresh_frequency_in_seconds: Optional[Any] = Field(
        None,
        description="The frequency a refreshable clone is refreshed after auto-refresh is enabled. The minimum is 1 hour. The maximum is 7 days. The date and time that auto-refresh is enabled is controlled by the `timeOfAutoRefreshStart` parameter.",
    )
    auto_refresh_point_lag_in_seconds: Optional[Any] = Field(
        None,
        description="The time, in seconds, the data of the refreshable clone lags the primary database at the point of refresh. The minimum is 0 minutes (0 mins means refresh to the latest available timestamp). The maximum is 7 days. The lag time increases after refreshing until the next data refresh happens.",
    )
    autonomous_container_database_id: Optional[Any] = Field(
        None,
        description="The Autonomous Container Database `OCID`__. Used only by Autonomous Database on Dedicated Exadata Infrastructure.",
    )
    autonomous_maintenance_schedule_type: Optional[Any] = Field(
        None,
        description="The maintenance schedule type of the Autonomous Database Serverless. An EARLY maintenance schedule follows a schedule applying patches prior to the REGULAR schedule. A REGULAR maintenance schedule follows the normal cycle Allowed values for this property are: \"EARLY\", \"REGULAR\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    availability_domain: Optional[Any] = Field(
        None,
        description="The availability domain where the Autonomous Database Serverless instance is located.",
    )
    available_upgrade_versions: Optional[Any] = Field(
        None,
        description="List of Oracle Database versions available for a database upgrade. If there are no version upgrades available, this list is empty.",
    )
    backup_config: Optional[Any] = Field(
        None,
        description="",
    )
    backup_retention_period_in_days: Optional[Any] = Field(
        None,
        description="Retention period, in days, for long-term backups",
    )
    byol_compute_count_limit: Optional[float] = Field(
        None,
        description="The maximum number of CPUs allowed with a Bring Your Own License (BYOL), including those used for auto-scaling, disaster recovery, tools, etc. Any CPU usage above this limit is considered as License Included and billed.",
    )
    character_set: Optional[Any] = Field(
        None,
        description="The character set for the autonomous database. The default is AL32UTF8. Allowed values are: AL32UTF8, AR8ADOS710, AR8ADOS720, AR8APTEC715, AR8ARABICMACS, AR8ASMO8X, AR8ISO8859P6, AR8MSWIN1256, AR8MUSSAD768, AR8NAFITHA711, AR8NAFITHA721, AR8SAKHR706, AR8SAKHR707, AZ8ISO8859P9E, BG8MSWIN, BG8PC437S, BLT8CP921, BLT8ISO8859P13, BLT8MSWIN1257, BLT8PC775, BN8BSCII, CDN8PC863, CEL8ISO8859P14, CL8ISO8859P5, CL8ISOIR111, CL8KOI8R, CL8KOI8U, CL8MACCYRILLICS, CL8MSWIN1251, EE8ISO8859P2, EE8MACCES, EE8MACCROATIANS, EE8MSWIN1250, EE8PC852, EL8DEC, EL8ISO8859P7, EL8MACGREEKS, EL8MSWIN1253, EL8PC437S, EL8PC851, EL8PC869, ET8MSWIN923, HU8ABMOD, HU8CWI2, IN8ISCII, IS8PC861, IW8ISO8859P8, IW8MACHEBREWS, IW8MSWIN1255, IW8PC1507, JA16EUC, JA16EUCTILDE, JA16SJIS, JA16SJISTILDE, JA16VMS, KO16KSC5601, KO16KSCCS, KO16MSWIN949, LA8ISO6937, LA8PASSPORT, LT8MSWIN921, LT8PC772, LT8PC774, LV8PC1117, LV8PC8LR, LV8RST104090, N8PC865, NE8ISO8859P10, NEE8ISO8859P4, RU8BESTA, RU8PC855, RU8PC866, SE8ISO8859P3, TH8MACTHAIS, TH8TISASCII, TR8DEC, TR8MACTURKISHS, TR8MSWIN1254, TR8PC857, US7ASCII, US8PC437, UTF8, VN8MSWIN1258, VN8VN3, WE8DEC, WE8DG, WE8ISO8859P1, WE8ISO8859P15, WE8ISO8859P9, WE8MACROMAN8S, WE8MSWIN1252, WE8NCR4970, WE8NEXTSTEP, WE8PC850, WE8PC858, WE8PC860, WE8ROMAN8, ZHS16CGB231280, ZHS16GBK, ZHT16BIG5, ZHT16CCDC, ZHT16DBT, ZHT16HKSCS, ZHT16MSWIN950, ZHT32EUC, ZHT32SOPS, ZHT32TRIS",
    )
    clone_table_space_list: Optional[Any] = Field(
        None,
        description="A list of the source Autonomous Database's table space number(s) used to create this partial clone from the backup.",
    )
    cluster_placement_group_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the cluster placement group of the Autonomous Serverless Database.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this AutonomousDatabase. The `OCID`__ of the compartment.",
    )
    compute_count: Optional[float] = Field(
        None,
        description="The compute amount (CPUs) available to the database. Minimum and maximum values depend on the compute model and whether the database is an Autonomous Database Serverless instance or an Autonomous Database on Dedicated Exadata Infrastructure. The 'ECPU' compute model requires a minimum value of one, for databases in the elastic resource pool and minimum value of two, otherwise. Required when using the `computeModel` parameter. When using `cpuCoreCount` parameter, it is an error to specify computeCount to a non-null value. Providing `computeModel` and `computeCount` is the preferred method for both OCPU and ECPU.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    connection_strings: Optional[Any] = Field(
        None,
        description="The connection string used to connect to the Autonomous Database. The username for the Service Console is ADMIN. Use the password you entered when creating the Autonomous Database for the password value.",
    )
    connection_urls: Optional[Any] = Field(
        None,
        description="",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="The number of CPU cores to be made available to the database. When the ECPU is selected, the value for cpuCoreCount is 0. For Autonomous Database on Dedicated Exadata infrastructure, the maximum number of cores is determined by the infrastructure shape. See `Characteristics of Infrastructure Shapes`__ for shape details. **Note:** This parameter cannot be used with the `ocpuCount` parameter.",
    )
    customer_contacts: Optional[Any] = Field(
        None,
        description="Customer Contacts.",
    )
    data_safe_status: Optional[Any] = Field(
        None,
        description='Status of the Data Safe registration for this Autonomous Database. Allowed values for this property are: "REGISTERING", "REGISTERED", "DEREGISTERING", "NOT_REGISTERED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    data_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The quantity of data in the database, in gigabytes. For Autonomous Transaction Processing databases using ECPUs on Serverless Infrastructure, this value is always populated. In all the other cases, this value will be null and `dataStorageSizeInTBs` will be populated instead.",
    )
    data_storage_size_in_tbs: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the data_storage_size_in_tbs of this AutonomousDatabase. The quantity of data in the database, in terabytes. The following points apply to Autonomous Databases on Serverless Infrastructure: - This is an integer field whose value remains null when the data size is in GBs and cannot be converted to TBs (by dividing the GB value by 1024) without rounding error. - To get the exact value of data storage size without rounding error, please see `dataStorageSizeInGBs` of Autonomous Database.",
    )
    database_edition: Optional[Any] = Field(
        None,
        description="The Oracle Database Edition that applies to the Autonomous databases. Allowed values for this property are: \"STANDARD_EDITION\", \"ENTERPRISE_EDITION\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    database_management_status: Optional[Any] = Field(
        None,
        description='Status of Database Management for this Autonomous Database. Allowed values for this property are: "ENABLING", "ENABLED", "DISABLING", "NOT_ENABLED", "FAILED_ENABLING", "FAILED_DISABLING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    dataguard_region_type: Optional[Any] = Field(
        None,
        description="**Deprecated.** The Autonomous Data Guard region type of the Autonomous Database. For Autonomous Database Serverless, Autonomous Data Guard associations have designated primary and standby regions, and these region types do not change when the database changes roles. The standby regions in Autonomous Data Guard associations can be the same region designated as the primary region, or they can be remote regions. Certain database administrative operations may be available only in the primary region of the Autonomous Data Guard association, and cannot be performed when the database using the primary role is operating in a remote Autonomous Data Guard standby region. Allowed values for this property are: \"PRIMARY_DG_REGION\", \"REMOTE_STANDBY_DG_REGION\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    db_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_name of this AutonomousDatabase. The database name.",
    )
    db_tools_details: Optional[Any] = Field(
        None,
        description="The list of database tools details. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, whitelistedIps, isMTLSConnectionRequired, openMode, permissionLevel, dbWorkload, privateEndpointLabel, nsgIds, dbVersion, isRefreshable, dbName, scheduledOperations, isLocalDataGuardEnabled, or isFreeTier.",
    )
    db_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Database version for Autonomous Database.",
    )
    db_workload: Optional[Any] = Field(
        None,
        description='The Autonomous Database workload type. The following values are valid: - OLTP - indicates an Autonomous Transaction Processing database - DW - indicates an Autonomous Data Warehouse database - AJD - indicates an Autonomous JSON Database - APEX - indicates an Autonomous Database with the Oracle APEX Application Development workload type. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, privateEndpointLabel, nsgIds, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier. Allowed values for this property are: "OLTP", "DW", "AJD", "APEX", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    disaster_recovery_region_type: Optional[Any] = Field(
        None,
        description="**Deprecated.** The disaster recovery (DR) region type of the Autonomous Database. For Autonomous Database Serverless instances, DR associations have designated primary and standby regions. These region types do not change when the database changes roles. The standby region in DR associations can be the same region as the primary region, or they can be in a remote regions. Some database administration operations may be available only in the primary region of the DR association, and cannot be performed when the database using the primary role is operating in a remote region. Allowed values for this property are: \"PRIMARY\", \"REMOTE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the Autonomous Database. The name does not have to be unique.",
    )
    encryption_key: Optional[Any] = Field(
        None,
        description="",
    )
    encryption_key_history_entry: Optional[Any] = Field(
        None,
        description="Key History Entry.",
    )
    failed_data_recovery_in_seconds: Optional[Any] = Field(
        None,
        description="Indicates the number of seconds of data loss for a Data Guard failover.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousDatabase. The `OCID`__ of the Autonomous Database.",
    )
    in_memory_area_in_gbs: Optional[Any] = Field(
        None,
        description="The area assigned to In-Memory tables in Autonomous Database.",
    )
    in_memory_percentage: Optional[Any] = Field(
        None,
        description="The percentage of the System Global Area(SGA) assigned to In-Memory tables in Autonomous Database. This property is applicable only to Autonomous Databases on the Exadata Cloud@Customer platform.",
    )
    infrastructure_type: Optional[Any] = Field(
        None,
        description="The infrastructure type this resource belongs to. Allowed values for this property are: \"CLOUD\", \"CLOUD_AT_CUSTOMER\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    is_access_control_enabled: Optional[Any] = Field(
        None,
        description="Indicates if the database-level access control is enabled. If disabled, database access is defined by the network security rules. If enabled, database access is restricted to the IP addresses defined by the rules specified with the `whitelistedIps` property. While specifying `whitelistedIps` rules is optional, if database-level access control is enabled and no rules are specified, the database will become inaccessible. The rules can be added later using the `UpdateAutonomousDatabase` API operation or edit option in console. When creating a database clone, the desired access control setting should be specified. By default, database-level access control will be disabled for the clone. This property is applicable only to Autonomous Databases on the Exadata Cloud@Customer platform. For Autonomous Database Serverless instances, `whitelistedIps` is used.",
    )
    is_auto_scaling_enabled: Optional[Any] = Field(
        None,
        description="Indicates if auto scaling is enabled for the Autonomous Database CPU core count. The default value is `TRUE`.",
    )
    is_auto_scaling_for_storage_enabled: Optional[Any] = Field(
        None,
        description="Indicates if auto scaling is enabled for the Autonomous Database storage. The default value is `FALSE`.",
    )
    is_backup_retention_locked: Optional[Any] = Field(
        None,
        description="Indicates if the Autonomous Database is backup retention locked.",
    )
    is_data_guard_enabled: Optional[Any] = Field(
        None,
        description="**Deprecated.** Indicates whether the Autonomous Database has local (in-region) Data Guard enabled. Not applicable to cross-region Autonomous Data Guard associations, or to Autonomous Databases using dedicated Exadata infrastructure or Exadata Cloud@Customer infrastructure.",
    )
    is_dedicated: Optional[Any] = Field(
        None,
        description="True if the database uses `dedicated Exadata infrastructure`__.",
    )
    is_dev_tier: Optional[Any] = Field(
        None,
        description="Autonomous Database for Developers are fixed-shape Autonomous Databases that developers can use to build and test new applications. On Serverless, these are low-cost and billed per instance, on Dedicated and Cloud@Customer there is no additional cost to create Developer databases. Developer databases come with limited resources and is not intended for large-scale testing and production deployments. When you need more compute or storage resources, you may upgrade to a full paid production database.",
    )
    is_free_tier: Optional[Any] = Field(
        None,
        description="Indicates if this is an Always Free resource. The default value is false. Note that Always Free Autonomous Databases have 1 CPU and 20GB of memory. For Always Free databases, memory and CPU cannot be scaled. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, openMode, permissionLevel, privateEndpointLabel, nsgIds, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, or isLocalDataGuardEnabled",
    )
    is_local_data_guard_enabled: Optional[Any] = Field(
        None,
        description="Indicates whether the Autonomous Database has local (in-region) Data Guard enabled. Not applicable to cross-region Autonomous Data Guard associations, or to Autonomous Databases using dedicated Exadata infrastructure or Exadata Cloud@Customer infrastructure.",
    )
    is_mtls_connection_required: Optional[Any] = Field(
        None,
        description="Specifies if the Autonomous Database requires mTLS connections. This may not be updated in parallel with any of the following: licenseModel, databaseEdition, cpuCoreCount, computeCount, dataStorageSizeInTBs, whitelistedIps, openMode, permissionLevel, db-workload, privateEndpointLabel, nsgIds, customerContacts, dbVersion, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier. Service Change: The default value of the isMTLSConnectionRequired attribute will change from true to false on July 1, 2023 in the following APIs: - CreateAutonomousDatabase - GetAutonomousDatabase - UpdateAutonomousDatabase Details: Prior to the July 1, 2023 change, the isMTLSConnectionRequired attribute default value was true. This applies to Autonomous Database Serverless. Does this impact me? If you use or maintain custom scripts or Terraform scripts referencing the CreateAutonomousDatabase, GetAutonomousDatabase, or UpdateAutonomousDatabase APIs, you want to check, and possibly modify, the scripts for the changed default value of the attribute. Should you choose not to leave your scripts unchanged, the API calls containing this attribute will continue to work, but the default value will switch from true to false. How do I make this change? Using either OCI SDKs or command line tools, update your custom scripts to explicitly set the isMTLSConnectionRequired attribute to true.",
    )
    is_preview: Optional[Any] = Field(
        None,
        description="Indicates if the Autonomous Database version is a preview version.",
    )
    is_reconnect_clone_enabled: Optional[Any] = Field(
        None,
        description="Indicates if the refreshable clone can be reconnected to its source database.",
    )
    is_refreshable_clone: Optional[Any] = Field(
        None,
        description="Indicates if the Autonomous Database is a refreshable clone. This cannot be updated in parallel with any of the following: cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, openMode, permissionLevel, dbWorkload, privateEndpointLabel, nsgIds, dbVersion, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier.",
    )
    is_remote_data_guard_enabled: Optional[Any] = Field(
        None,
        description="Indicates whether the Autonomous Database has Cross Region Data Guard enabled. Not applicable to Autonomous Databases using dedicated Exadata infrastructure or Exadata Cloud@Customer infrastructure.",
    )
    key_history_entry: Optional[Any] = Field(
        None,
        description="Key History Entry.",
    )
    key_store_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the key store of Oracle Vault.",
    )
    key_store_wallet_name: Optional[Any] = Field(
        None,
        description="The wallet name for Oracle Key Vault.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    kms_key_lifecycle_details: Optional[Any] = Field(
        None,
        description="KMS key lifecycle details.",
    )
    kms_key_version_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container version that is used in database transparent data encryption (TDE) operations KMS Key can have multiple key versions. If none is specified, the current key version (latest) of the Key Id is used for the operation. Autonomous Database Serverless does not use key versions, hence is not applicable for Autonomous Database Serverless instances.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to the Oracle Autonomous Database. Bring your own license (BYOL) allows you to apply your current on-premises Oracle software licenses to equivalent, highly automated Oracle services in the cloud. License Included allows you to subscribe to new Oracle Database software licenses and the Oracle Database service. Note that when provisioning an `Autonomous Database on dedicated Exadata infrastructure`__, this attribute must be null. It is already set at the Autonomous Exadata Infrastructure level. When provisioning an `Autonomous Database Serverless]`__ database, if a value is not specified, the system defaults the value to `BRING_YOUR_OWN_LICENSE`. Bring your own license (BYOL) also allows you to select the DB edition using the optional parameter. This cannot be updated in parallel with any of the following: cpuCoreCount, computeCount, dataStorageSizeInTBs, adminPassword, isMTLSConnectionRequired, dbWorkload, privateEndpointLabel, nsgIds, dbVersion, dbName, scheduledOperations, dbToolsDetails, or isFreeTier. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousDatabase. The current state of the Autonomous Database. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "STOPPING", "STOPPED", "STARTING", "TERMINATING", "TERMINATED", "UNAVAILABLE", "RESTORE_IN_PROGRESS", "RESTORE_FAILED", "BACKUP_IN_PROGRESS", "SCALE_IN_PROGRESS", "AVAILABLE_NEEDS_ATTENTION", "UPDATING", "MAINTENANCE_IN_PROGRESS", "RESTARTING", "RECREATING", "ROLE_CHANGE_IN_PROGRESS", "UPGRADING", "INACCESSIBLE", "STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    local_adg_auto_failover_max_data_loss_limit: Optional[Any] = Field(
        None,
        description="Parameter that allows users to select an acceptable maximum data loss limit in seconds, up to which Automatic Failover will be triggered when necessary for a Local Autonomous Data Guard",
    )
    local_disaster_recovery_type: Optional[Any] = Field(
        None,
        description="Indicates the local disaster recovery (DR) type of the Autonomous Database Serverless instance. Autonomous Data Guard (ADG) DR type provides business critical DR with a faster recovery time objective (RTO) during failover or switchover. Backup-based DR type provides lower cost DR with a slower RTO during failover or switchover.",
    )
    local_standby_db: Optional[Any] = Field(
        None,
        description="",
    )
    long_term_backup_schedule: Optional[Any] = Field(
        None,
        description="",
    )
    memory_per_oracle_compute_unit_in_gbs: Optional[Any] = Field(
        None,
        description="The amount of memory (in GBs) enabled per ECPU or OCPU.",
    )
    ncharacter_set: Optional[Any] = Field(
        None,
        description="The national character set for the autonomous database. The default is AL16UTF16. Allowed values are: AL16UTF16 or UTF8.",
    )
    net_services_architecture: Optional[Any] = Field(
        None,
        description="Enabling SHARED server architecture enables a database server to allow many client processes to share very few server processes, thereby increasing the number of supported users. Allowed values for this property are: \"DEDICATED\", \"SHARED\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    next_long_term_backup_time_stamp: Optional[Any] = Field(
        None,
        description="The date and time when the next long-term backup would be created.",
    )
    nsg_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ for the network security groups (NSGs) to which this resource belongs. Setting this to an empty list removes all resources from all NSGs. For more information about NSGs, see `Security Rules`__. **NsgIds restrictions:** - A network security group (NSG) is optional for Autonomous Databases with private access. The nsgIds list can be empty.",
    )
    ocpu_count: Optional[float] = Field(
        None,
        description="The number of OCPU cores to be made available to the database. The following points apply: - For Autonomous Databases on Dedicated Exadata Infrastructure, to provision less than 1 core, enter a fractional value in an increment of 0.1. For example, you can provision 0.3 or 0.4 cores, but not 0.35 cores. (Note that fractional OCPU values are not supported for Autonomous Database Serverless instances.) - To provision cores, enter an integer between 1 and the maximum number of cores available for the infrastructure shape. For example, you can provision 2 cores or 3 cores, but not 2.5 cores. This applies to Autonomous Databases on both serverless and dedicated Exadata infrastructure. - For Autonomous Database Serverless instances, this parameter is not used. For Autonomous Databases on Dedicated Exadata Infrastructure, the maximum number of cores is determined by the infrastructure shape. See `Characteristics of Infrastructure Shapes`__ for shape details. **Note:** This parameter cannot be used with the `cpuCoreCount` parameter.",
    )
    open_mode: Optional[Any] = Field(
        None,
        description="Indicates the Autonomous Database mode. The database can be opened in `READ_ONLY` or `READ_WRITE` mode. This cannot be updated in parallel with any of the following: cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, or isFreeTier. Allowed values for this property are: \"READ_ONLY\", \"READ_WRITE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    operations_insights_status: Optional[Any] = Field(
        None,
        description='Status of Operations Insights for this Autonomous Database. Allowed values for this property are: "ENABLING", "ENABLED", "DISABLING", "NOT_ENABLED", "FAILED_ENABLING", "FAILED_DISABLING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_db_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ of standby databases located in Autonomous Data Guard remote regions that are associated with the source database. Note that for Autonomous Database Serverless instances, standby databases located in the same region as the source primary database do not have OCIDs.",
    )
    permission_level: Optional[Any] = Field(
        None,
        description="The Autonomous Database permission level. Restricted mode allows access only by admin users. This cannot be updated in parallel with any of the following: cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, nsgIds, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, or isFreeTier. Allowed values for this property are: \"RESTRICTED\", \"UNRESTRICTED\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    private_endpoint: Optional[Any] = Field(
        None,
        description="The private endpoint for the resource.",
    )
    private_endpoint_ip: Optional[Any] = Field(
        None,
        description="The private endpoint Ip address for the resource.",
    )
    private_endpoint_label: Optional[Any] = Field(
        None,
        description="The resource's private endpoint label. - Setting the endpoint label to a non-empty string creates a private endpoint database. - Resetting the endpoint label to an empty string, after the creation of the private endpoint database, changes the private endpoint database to a public endpoint database. - Setting the endpoint label to a non-empty string value, updates to a new private endpoint database, when the database is disabled and re-enabled. This setting cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, dbWorkload, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, or isFreeTier.",
    )
    provisionable_cpus: Optional[Any] = Field(
        None,
        description="An array of CPU values that an Autonomous Database can be scaled to.",
    )
    public_connection_urls: Optional[Any] = Field(
        None,
        description="The Public URLs of Private Endpoint database for accessing Oracle Application Express (APEX) and SQL Developer Web with a browser from a Compute instance within your VCN or that has a direct connection to your VCN.",
    )
    public_endpoint: Optional[Any] = Field(
        None,
        description="The public endpoint for the private endpoint enabled resource.",
    )
    refreshable_mode: Optional[Any] = Field(
        None,
        description="The refresh mode of the clone. AUTOMATIC indicates that the clone is automatically being refreshed with data from the source Autonomous Database. Allowed values for this property are: \"AUTOMATIC\", \"MANUAL\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    refreshable_status: Optional[Any] = Field(
        None,
        description="The refresh status of the clone. REFRESHING indicates that the clone is currently being refreshed with data from the source Autonomous Database. Allowed values for this property are: \"REFRESHING\", \"NOT_REFRESHING\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    remote_disaster_recovery_configuration: Optional[Any] = Field(
        None,
        description="",
    )
    resource_pool_leader_id: Optional[Any] = Field(
        None,
        description="The unique identifier for leader autonomous database OCID `OCID`__.",
    )
    resource_pool_summary: Optional[Any] = Field(
        None,
        description="",
    )
    role: Optional[Any] = Field(
        None,
        description='The Data Guard role of the Autonomous Container Database or Autonomous Database, if Autonomous Data Guard is enabled. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", "BACKUP_COPY", "SNAPSHOT_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    scheduled_operations: Optional[Any] = Field(
        None,
        description="The list of scheduled operations. Consists of values such as dayOfWeek, scheduledStartTime, scheduledStopTime. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, whitelistedIps, isMTLSConnectionRequired, openMode, permissionLevel, dbWorkload, privateEndpointLabel, nsgIds, dbVersion, isRefreshable, dbName, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier.",
    )
    security_attributes: Optional[Any] = Field(
        None,
        description='Security Attributes for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. Example: `{"Oracle-ZPR": {"MaxEgressCount": {"value": "42", "mode": "audit"}}}`',
    )
    service_console_url: Optional[Any] = Field(
        None,
        description="The URL of the Service Console for the Autonomous Database.",
    )
    source_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the source Autonomous Database that was cloned to create the current Autonomous Database.",
    )
    standby_db: Optional[Any] = Field(
        None,
        description="**Deprecated** Autonomous Data Guard standby database details.",
    )
    standby_whitelisted_ips: Optional[Any] = Field(
        None,
        description='The client IP access control list (ACL). This feature is available for `Autonomous Database Serverless]`__ and on Exadata Cloud@Customer. Only clients connecting from an IP address included in the ACL may access the Autonomous Database instance. If `arePrimaryWhitelistedIpsUsed` is \'TRUE\' then Autonomous Database uses this primary\'s IP access control list (ACL) for the disaster recovery peer called `standbywhitelistedips`. For Autonomous Database Serverless, this is an array of CIDR (classless inter-domain routing) notations for a subnet or VCN OCID (virtual cloud network Oracle Cloud ID). Multiple IPs and VCN OCIDs should be separate strings separated by commas, but if it’s other configurations that need multiple pieces of information then its each piece is connected with semicolon (;) as a delimiter. Example: `["1.1.1.1","1.1.1.0/24","ocid1.vcn.oc1.sea.<unique_id>","ocid1.vcn.oc1.sea.<unique_id1>;1.1.1.1","ocid1.vcn.oc1.sea.<unique_id2>;1.1.0.0/16"]` For Exadata Cloud@Customer, this is an array of IP addresses or CIDR notations. Example: `["1.1.1.1","1.1.1.0/24","1.1.2.25"]` For an update operation, if you want to delete all the IPs in the ACL, use an array with a single empty string entry. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, isMTLSConnectionRequired, openMode, permissionLevel, dbWorkload, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier.',
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the subnet the resource is associated with. **Subnet Restrictions:** - For bare metal DB systems and for single node virtual machine DB systems, do not use a subnet that overlaps with 192.168.16.16/28. - For Exadata and virtual machine 2-node RAC systems, do not use a subnet that overlaps with 192.168.128.0/20. - For Autonomous Database, setting this will disable public secure access to the database. These subnets are used by the Oracle Clusterware private interconnect on the database instance. Specifying an overlapping subnet will cause the private interconnect to malfunction. This restriction applies to both the client subnet and the backup subnet.",
    )
    subscription_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the subscription with which resource needs to be associated with.",
    )
    supported_regions_to_clone_to: Optional[Any] = Field(
        None,
        description="The list of regions that support the creation of an Autonomous Database clone or an Autonomous Data Guard standby database.",
    )
    system_tags: Optional[Any] = Field(
        None,
        description="System tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Autonomous Database was created.",
    )
    time_data_guard_role_changed: Optional[Any] = Field(
        None,
        description='The date and time the Autonomous Data Guard role was switched for the Autonomous Database. For databases that have standbys in both the primary Data Guard region and a remote Data Guard standby region, this is the latest timestamp of either the database using the "primary" role in the primary Data Guard region, or database located in the remote Data Guard standby region.',
    )
    time_deletion_of_free_autonomous_database: Optional[Any] = Field(
        None,
        description="The date and time the Always Free database will be automatically deleted because of inactivity. If the database is in the STOPPED state and without activity until this time, it will be deleted.",
    )
    time_disaster_recovery_role_changed: Optional[Any] = Field(
        None,
        description="The date and time the Disaster Recovery role was switched for the standby Autonomous Database.",
    )
    time_local_data_guard_enabled: Optional[Any] = Field(
        None,
        description="The date and time that Autonomous Data Guard was enabled for an Autonomous Database where the standby was provisioned in the same region as the primary database.",
    )
    time_maintenance_begin: Optional[Any] = Field(
        None,
        description="The date and time when maintenance will begin.",
    )
    time_maintenance_end: Optional[Any] = Field(
        None,
        description="The date and time when maintenance will end.",
    )
    time_of_auto_refresh_start: Optional[Any] = Field(
        None,
        description="The the date and time that auto-refreshing will begin for an Autonomous Database refreshable clone. This value controls only the start time for the first refresh operation. Subsequent (ongoing) refresh operations have start times controlled by the value of the `autoRefreshFrequencyInSeconds` parameter.",
    )
    time_of_joining_resource_pool: Optional[Any] = Field(
        None,
        description="The time the member joined the resource pool.",
    )
    time_of_last_failover: Optional[Any] = Field(
        None,
        description="The timestamp of the last failover operation.",
    )
    time_of_last_refresh: Optional[Any] = Field(
        None,
        description="The date and time when last refresh happened.",
    )
    time_of_last_refresh_point: Optional[Any] = Field(
        None,
        description="The refresh point timestamp (UTC). The refresh point is the time to which the database was most recently refreshed. Data created after the refresh point is not included in the refresh.",
    )
    time_of_last_switchover: Optional[Any] = Field(
        None,
        description="The timestamp of the last switchover operation for the Autonomous Database.",
    )
    time_of_next_refresh: Optional[Any] = Field(
        None,
        description="The date and time of next refresh.",
    )
    time_reclamation_of_free_autonomous_database: Optional[Any] = Field(
        None,
        description="The date and time the Always Free database will be stopped because of inactivity. If this time is reached without any database activity, the database will automatically be put into the STOPPED state.",
    )
    time_undeleted: Optional[Any] = Field(
        None,
        description="The date and time the Autonomous Database was most recently undeleted.",
    )
    time_until_reconnect_clone_enabled: Optional[Any] = Field(
        None,
        description="The time and date as an RFC3339 formatted string, e.g., 2022-01-01T12:00:00.000Z, to set the limit for a refreshable clone to be reconnected to its source database.",
    )
    total_backup_storage_size_in_gbs: Optional[float] = Field(
        None,
        description="The backup storage to the database.",
    )
    used_data_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The storage space consumed by Autonomous Database in GBs.",
    )
    used_data_storage_size_in_tbs: Optional[Any] = Field(
        None,
        description="The amount of storage that has been used for Autonomous Databases in dedicated infrastructure, in terabytes.",
    )
    vault_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Oracle Cloud Infrastructure `vault`__. This parameter and `secretId` are required for Customer Managed Keys.",
    )
    whitelisted_ips: Optional[Any] = Field(
        None,
        description='The client IP access control list (ACL). This feature is available for `Autonomous Database Serverless]`__ and on Exadata Cloud@Customer. Only clients connecting from an IP address included in the ACL may access the Autonomous Database instance. If `arePrimaryWhitelistedIpsUsed` is \'TRUE\' then Autonomous Database uses this primary\'s IP access control list (ACL) for the disaster recovery peer called `standbywhitelistedips`. For Autonomous Database Serverless, this is an array of CIDR (classless inter-domain routing) notations for a subnet or VCN OCID (virtual cloud network Oracle Cloud ID). Multiple IPs and VCN OCIDs should be separate strings separated by commas, but if it’s other configurations that need multiple pieces of information then its each piece is connected with semicolon (;) as a delimiter. Example: `["1.1.1.1","1.1.1.0/24","ocid1.vcn.oc1.sea.<unique_id>","ocid1.vcn.oc1.sea.<unique_id1>;1.1.1.1","ocid1.vcn.oc1.sea.<unique_id2>;1.1.0.0/16"]` For Exadata Cloud@Customer, this is an array of IP addresses or CIDR notations. Example: `["1.1.1.1","1.1.1.0/24","1.1.2.25"]` For an update operation, if you want to delete all the IPs in the ACL, use an array with a single empty string entry. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, isMTLSConnectionRequired, openMode, permissionLevel, dbWorkload, dbVersion, isRefreshable, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier.',
    )


def map_autonomousdatabase(
    o: oci.database.models.AutonomousDatabase,
) -> AutonomousDatabase | None:
    """Map oci.database.models.AutonomousDatabase → AutonomousDatabase Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDatabase(**data)
    except Exception:
        return AutonomousDatabase(
            actual_used_data_storage_size_in_tbs=getattr(
                o, "actual_used_data_storage_size_in_tbs", None
            ),
            allocated_storage_size_in_tbs=getattr(
                o, "allocated_storage_size_in_tbs", None
            ),
            apex_details=getattr(o, "apex_details", None),
            are_primary_whitelisted_ips_used=getattr(
                o, "are_primary_whitelisted_ips_used", None
            ),
            auto_refresh_frequency_in_seconds=getattr(
                o, "auto_refresh_frequency_in_seconds", None
            ),
            auto_refresh_point_lag_in_seconds=getattr(
                o, "auto_refresh_point_lag_in_seconds", None
            ),
            autonomous_container_database_id=getattr(
                o, "autonomous_container_database_id", None
            ),
            autonomous_maintenance_schedule_type=getattr(
                o, "autonomous_maintenance_schedule_type", None
            ),
            availability_domain=getattr(o, "availability_domain", None),
            available_upgrade_versions=getattr(o, "available_upgrade_versions", None),
            backup_config=getattr(o, "backup_config", None),
            backup_retention_period_in_days=getattr(
                o, "backup_retention_period_in_days", None
            ),
            byol_compute_count_limit=getattr(o, "byol_compute_count_limit", None),
            character_set=getattr(o, "character_set", None),
            clone_table_space_list=getattr(o, "clone_table_space_list", None),
            cluster_placement_group_id=getattr(o, "cluster_placement_group_id", None),
            compartment_id=getattr(o, "compartment_id", None),
            compute_count=getattr(o, "compute_count", None),
            compute_model=getattr(o, "compute_model", None),
            connection_strings=getattr(o, "connection_strings", None),
            connection_urls=getattr(o, "connection_urls", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            customer_contacts=getattr(o, "customer_contacts", None),
            data_safe_status=getattr(o, "data_safe_status", None),
            data_storage_size_in_gbs=getattr(o, "data_storage_size_in_gbs", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            database_edition=getattr(o, "database_edition", None),
            database_management_status=getattr(o, "database_management_status", None),
            dataguard_region_type=getattr(o, "dataguard_region_type", None),
            db_name=getattr(o, "db_name", None),
            db_tools_details=getattr(o, "db_tools_details", None),
            db_version=getattr(o, "db_version", None),
            db_workload=getattr(o, "db_workload", None),
            defined_tags=getattr(o, "defined_tags", None),
            disaster_recovery_region_type=getattr(
                o, "disaster_recovery_region_type", None
            ),
            display_name=getattr(o, "display_name", None),
            encryption_key=getattr(o, "encryption_key", None),
            encryption_key_history_entry=getattr(
                o, "encryption_key_history_entry", None
            ),
            failed_data_recovery_in_seconds=getattr(
                o, "failed_data_recovery_in_seconds", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            in_memory_area_in_gbs=getattr(o, "in_memory_area_in_gbs", None),
            in_memory_percentage=getattr(o, "in_memory_percentage", None),
            infrastructure_type=getattr(o, "infrastructure_type", None),
            is_access_control_enabled=getattr(o, "is_access_control_enabled", None),
            is_auto_scaling_enabled=getattr(o, "is_auto_scaling_enabled", None),
            is_auto_scaling_for_storage_enabled=getattr(
                o, "is_auto_scaling_for_storage_enabled", None
            ),
            is_backup_retention_locked=getattr(o, "is_backup_retention_locked", None),
            is_data_guard_enabled=getattr(o, "is_data_guard_enabled", None),
            is_dedicated=getattr(o, "is_dedicated", None),
            is_dev_tier=getattr(o, "is_dev_tier", None),
            is_free_tier=getattr(o, "is_free_tier", None),
            is_local_data_guard_enabled=getattr(o, "is_local_data_guard_enabled", None),
            is_mtls_connection_required=getattr(o, "is_mtls_connection_required", None),
            is_preview=getattr(o, "is_preview", None),
            is_reconnect_clone_enabled=getattr(o, "is_reconnect_clone_enabled", None),
            is_refreshable_clone=getattr(o, "is_refreshable_clone", None),
            is_remote_data_guard_enabled=getattr(
                o, "is_remote_data_guard_enabled", None
            ),
            key_history_entry=getattr(o, "key_history_entry", None),
            key_store_id=getattr(o, "key_store_id", None),
            key_store_wallet_name=getattr(o, "key_store_wallet_name", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            kms_key_lifecycle_details=getattr(o, "kms_key_lifecycle_details", None),
            kms_key_version_id=getattr(o, "kms_key_version_id", None),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            local_adg_auto_failover_max_data_loss_limit=getattr(
                o, "local_adg_auto_failover_max_data_loss_limit", None
            ),
            local_disaster_recovery_type=getattr(
                o, "local_disaster_recovery_type", None
            ),
            local_standby_db=getattr(o, "local_standby_db", None),
            long_term_backup_schedule=getattr(o, "long_term_backup_schedule", None),
            memory_per_oracle_compute_unit_in_gbs=getattr(
                o, "memory_per_oracle_compute_unit_in_gbs", None
            ),
            ncharacter_set=getattr(o, "ncharacter_set", None),
            net_services_architecture=getattr(o, "net_services_architecture", None),
            next_long_term_backup_time_stamp=getattr(
                o, "next_long_term_backup_time_stamp", None
            ),
            nsg_ids=getattr(o, "nsg_ids", None),
            ocpu_count=getattr(o, "ocpu_count", None),
            open_mode=getattr(o, "open_mode", None),
            operations_insights_status=getattr(o, "operations_insights_status", None),
            peer_db_ids=getattr(o, "peer_db_ids", None),
            permission_level=getattr(o, "permission_level", None),
            private_endpoint=getattr(o, "private_endpoint", None),
            private_endpoint_ip=getattr(o, "private_endpoint_ip", None),
            private_endpoint_label=getattr(o, "private_endpoint_label", None),
            provisionable_cpus=getattr(o, "provisionable_cpus", None),
            public_connection_urls=getattr(o, "public_connection_urls", None),
            public_endpoint=getattr(o, "public_endpoint", None),
            refreshable_mode=getattr(o, "refreshable_mode", None),
            refreshable_status=getattr(o, "refreshable_status", None),
            remote_disaster_recovery_configuration=getattr(
                o, "remote_disaster_recovery_configuration", None
            ),
            resource_pool_leader_id=getattr(o, "resource_pool_leader_id", None),
            resource_pool_summary=getattr(o, "resource_pool_summary", None),
            role=getattr(o, "role", None),
            scheduled_operations=getattr(o, "scheduled_operations", None),
            security_attributes=getattr(o, "security_attributes", None),
            service_console_url=getattr(o, "service_console_url", None),
            source_id=getattr(o, "source_id", None),
            standby_db=getattr(o, "standby_db", None),
            standby_whitelisted_ips=getattr(o, "standby_whitelisted_ips", None),
            subnet_id=getattr(o, "subnet_id", None),
            subscription_id=getattr(o, "subscription_id", None),
            supported_regions_to_clone_to=getattr(
                o, "supported_regions_to_clone_to", None
            ),
            system_tags=getattr(o, "system_tags", None),
            time_created=getattr(o, "time_created", None),
            time_data_guard_role_changed=getattr(
                o, "time_data_guard_role_changed", None
            ),
            time_deletion_of_free_autonomous_database=getattr(
                o, "time_deletion_of_free_autonomous_database", None
            ),
            time_disaster_recovery_role_changed=getattr(
                o, "time_disaster_recovery_role_changed", None
            ),
            time_local_data_guard_enabled=getattr(
                o, "time_local_data_guard_enabled", None
            ),
            time_maintenance_begin=getattr(o, "time_maintenance_begin", None),
            time_maintenance_end=getattr(o, "time_maintenance_end", None),
            time_of_auto_refresh_start=getattr(o, "time_of_auto_refresh_start", None),
            time_of_joining_resource_pool=getattr(
                o, "time_of_joining_resource_pool", None
            ),
            time_of_last_failover=getattr(o, "time_of_last_failover", None),
            time_of_last_refresh=getattr(o, "time_of_last_refresh", None),
            time_of_last_refresh_point=getattr(o, "time_of_last_refresh_point", None),
            time_of_last_switchover=getattr(o, "time_of_last_switchover", None),
            time_of_next_refresh=getattr(o, "time_of_next_refresh", None),
            time_reclamation_of_free_autonomous_database=getattr(
                o, "time_reclamation_of_free_autonomous_database", None
            ),
            time_undeleted=getattr(o, "time_undeleted", None),
            time_until_reconnect_clone_enabled=getattr(
                o, "time_until_reconnect_clone_enabled", None
            ),
            total_backup_storage_size_in_gbs=getattr(
                o, "total_backup_storage_size_in_gbs", None
            ),
            used_data_storage_size_in_gbs=getattr(
                o, "used_data_storage_size_in_gbs", None
            ),
            used_data_storage_size_in_tbs=getattr(
                o, "used_data_storage_size_in_tbs", None
            ),
            vault_id=getattr(o, "vault_id", None),
            whitelisted_ips=getattr(o, "whitelisted_ips", None),
        )


class AutonomousDatabaseBackup(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDatabaseBackup."""

    autonomous_database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the autonomous_database_id of this AutonomousDatabaseBackup. The `OCID`__ of the Autonomous Database.",
    )
    backup_destination_details: Optional[Any] = Field(
        None,
        description="",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this AutonomousDatabaseBackup. The `OCID`__ of the compartment.",
    )
    database_size_in_tbs: Optional[float] = Field(
        None,
        description="The size of the database in terabytes at the time the backup was taken.",
    )
    db_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Database version for Autonomous Database.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this AutonomousDatabaseBackup. The user-friendly name for the backup. The name does not have to be unique.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousDatabaseBackup. The `OCID`__ of the Autonomous Database backup.",
    )
    is_automatic: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the is_automatic of this AutonomousDatabaseBackup. Indicates whether the backup is user-initiated or automatic.",
    )
    is_restorable: Optional[Any] = Field(
        None,
        description="Indicates whether the backup can be used to restore the associated Autonomous Database.",
    )
    key_store_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the key store of Oracle Vault.",
    )
    key_store_wallet_name: Optional[Any] = Field(
        None,
        description="The wallet name for Oracle Key Vault.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    kms_key_version_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container version that is used in database transparent data encryption (TDE) operations KMS Key can have multiple key versions. If none is specified, the current key version (latest) of the Key Id is used for the operation. Autonomous Database Serverless does not use key versions, hence is not applicable for Autonomous Database Serverless instances.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousDatabaseBackup. The current state of the backup. Allowed values for this property are: "CREATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "UPDATING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    retention_period_in_days: Optional[Any] = Field(
        None,
        description="Retention period, in days, for long-term backups",
    )
    size_in_tbs: Optional[float] = Field(
        None,
        description="The backup size in terrabytes (TB).",
    )
    time_available_till: Optional[Any] = Field(
        None,
        description="Timestamp until when the backup will be available",
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time the backup completed.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="The date and time the backup started.",
    )
    type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the type of this AutonomousDatabaseBackup. The type of backup. Allowed values for this property are: "INCREMENTAL", "FULL", "LONGTERM", "VIRTUAL_FULL", "CUMULATIVE_INCREMENTAL", "ROLL_FORWARD_IMAGE_COPY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    vault_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Oracle Cloud Infrastructure `vault`__. This parameter and `secretId` are required for Customer Managed Keys.",
    )


def map_autonomousdatabasebackup(
    o: oci.database.models.AutonomousDatabaseBackup,
) -> AutonomousDatabaseBackup | None:
    """Map oci.database.models.AutonomousDatabaseBackup → AutonomousDatabaseBackup Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDatabaseBackup(**data)
    except Exception:
        return AutonomousDatabaseBackup(
            autonomous_database_id=getattr(o, "autonomous_database_id", None),
            backup_destination_details=getattr(o, "backup_destination_details", None),
            compartment_id=getattr(o, "compartment_id", None),
            database_size_in_tbs=getattr(o, "database_size_in_tbs", None),
            db_version=getattr(o, "db_version", None),
            display_name=getattr(o, "display_name", None),
            id=getattr(o, "id", None),
            is_automatic=getattr(o, "is_automatic", None),
            is_restorable=getattr(o, "is_restorable", None),
            key_store_id=getattr(o, "key_store_id", None),
            key_store_wallet_name=getattr(o, "key_store_wallet_name", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            kms_key_version_id=getattr(o, "kms_key_version_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            retention_period_in_days=getattr(o, "retention_period_in_days", None),
            size_in_tbs=getattr(o, "size_in_tbs", None),
            time_available_till=getattr(o, "time_available_till", None),
            time_ended=getattr(o, "time_ended", None),
            time_started=getattr(o, "time_started", None),
            type=getattr(o, "type", None),
            vault_id=getattr(o, "vault_id", None),
        )


class AutonomousDatabaseDataguardAssociation(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDatabaseDataguardAssociation."""

    apply_lag: Optional[Any] = Field(
        None,
        description="The lag time between updates to the primary database and application of the redo data on the standby database, as computed by the reporting database. Example: `9 seconds`",
    )
    apply_rate: Optional[Any] = Field(
        None,
        description="The rate at which redo logs are synced between the associated databases. Example: `180 Mb per second`",
    )
    autonomous_database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the autonomous_database_id of this AutonomousDatabaseDataguardAssociation. The `OCID`__ of the Autonomous Database that has a relationship with the peer Autonomous Database.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousDatabaseDataguardAssociation. The OCID of the Autonomous Dataguard created for Autonomous Container Database where given Autonomous Database resides in.",
    )
    is_automatic_failover_enabled: Optional[Any] = Field(
        None,
        description="Indicates whether Automatic Failover is enabled for Autonomous Container Database Dataguard Association",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycleState, if available.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousDatabaseDataguardAssociation. The current state of Autonomous Data Guard. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "ROLE_CHANGE_IN_PROGRESS", "TERMINATING", "TERMINATED", "FAILED", "UNAVAILABLE", "UPDATING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_autonomous_database_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the peer Autonomous Database.",
    )
    peer_autonomous_database_life_cycle_state: Optional[Any] = Field(
        None,
        description='The current state of the Autonomous Database. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "STOPPING", "STOPPED", "STARTING", "TERMINATING", "TERMINATED", "UNAVAILABLE", "RESTORE_IN_PROGRESS", "RESTORE_FAILED", "BACKUP_IN_PROGRESS", "SCALE_IN_PROGRESS", "AVAILABLE_NEEDS_ATTENTION", "UPDATING", "MAINTENANCE_IN_PROGRESS", "RESTARTING", "RECREATING", "ROLE_CHANGE_IN_PROGRESS", "UPGRADING", "INACCESSIBLE", "STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_role: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the peer_role of this AutonomousDatabaseDataguardAssociation. The Data Guard role of the Autonomous Container Database or Autonomous Database, if Autonomous Data Guard is enabled. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", "BACKUP_COPY", "SNAPSHOT_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    protection_mode: Optional[Any] = Field(
        None,
        description="The protection mode of this Autonomous Data Guard association. For more information, see `Oracle Data Guard Protection Modes`__ in the Oracle Data Guard documentation. Allowed values for this property are: \"MAXIMUM_AVAILABILITY\", \"MAXIMUM_PERFORMANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    role: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the role of this AutonomousDatabaseDataguardAssociation. The Data Guard role of the Autonomous Container Database or Autonomous Database, if Autonomous Data Guard is enabled. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", "BACKUP_COPY", "SNAPSHOT_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Data Guard association was created.",
    )
    time_last_role_changed: Optional[Any] = Field(
        None,
        description="The date and time when the last role change action happened.",
    )
    time_last_synced: Optional[Any] = Field(
        None,
        description="The date and time of the last update to the apply lag, apply rate, and transport lag values.",
    )
    transport_lag: Optional[Any] = Field(
        None,
        description="The approximate number of seconds of redo data not yet available on the standby Autonomous Container Database, as computed by the reporting database. Example: `7 seconds`",
    )


def map_autonomousdatabasedataguardassociation(
    o: oci.database.models.AutonomousDatabaseDataguardAssociation,
) -> AutonomousDatabaseDataguardAssociation | None:
    """Map oci.database.models.AutonomousDatabaseDataguardAssociation → AutonomousDatabaseDataguardAssociation Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDatabaseDataguardAssociation(**data)
    except Exception:
        return AutonomousDatabaseDataguardAssociation(
            apply_lag=getattr(o, "apply_lag", None),
            apply_rate=getattr(o, "apply_rate", None),
            autonomous_database_id=getattr(o, "autonomous_database_id", None),
            id=getattr(o, "id", None),
            is_automatic_failover_enabled=getattr(
                o, "is_automatic_failover_enabled", None
            ),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            peer_autonomous_database_id=getattr(o, "peer_autonomous_database_id", None),
            peer_autonomous_database_life_cycle_state=getattr(
                o, "peer_autonomous_database_life_cycle_state", None
            ),
            peer_role=getattr(o, "peer_role", None),
            protection_mode=getattr(o, "protection_mode", None),
            role=getattr(o, "role", None),
            time_created=getattr(o, "time_created", None),
            time_last_role_changed=getattr(o, "time_last_role_changed", None),
            time_last_synced=getattr(o, "time_last_synced", None),
            transport_lag=getattr(o, "transport_lag", None),
        )


class AutonomousDatabaseWallet(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDatabaseWallet."""

    lifecycle_state: Optional[Any] = Field(
        None,
        description="The current lifecycle state of the Autonomous Database wallet. Allowed values for this property are: \"ACTIVE\", \"UPDATING\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    time_rotated: Optional[Any] = Field(
        None,
        description="The date and time the wallet was last rotated.",
    )


def map_autonomousdatabasewallet(
    o: oci.database.models.AutonomousDatabaseWallet,
) -> AutonomousDatabaseWallet | None:
    """Map oci.database.models.AutonomousDatabaseWallet → AutonomousDatabaseWallet Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDatabaseWallet(**data)
    except Exception:
        return AutonomousDatabaseWallet(
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_rotated=getattr(o, "time_rotated", None),
        )


class AutonomousDatabaseSoftwareImage(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousDatabaseSoftwareImage."""

    autonomous_dsi_one_off_patches: Optional[Any] = Field(
        None,
        description="One-off patches included in the Autonomous Database Software Image",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this AutonomousDatabaseSoftwareImage. The `OCID`__ of the compartment.",
    )
    database_version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the database_version of this AutonomousDatabaseSoftwareImage. The database version with which the Autonomous Database Software Image is to be built.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this AutonomousDatabaseSoftwareImage. The user-friendly name for the Autonomous Database Software Image. The name does not have to be unique.",
    )
    dst_file_version: Optional[Any] = Field(
        None,
        description="DST Time-Zone File version of the Autonomous Container Database.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousDatabaseSoftwareImage. The `OCID`__ of the Autonomous Database Software Image.",
    )
    image_shape_family: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the image_shape_family of this AutonomousDatabaseSoftwareImage. To what shape the image is meant for. Allowed values for this property are: \"EXACC_SHAPE\", \"EXADATA_SHAPE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Detailed message for the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousDatabaseSoftwareImage. The current state of the Autonomous Database Software Image. Allowed values for this property are: "AVAILABLE", "FAILED", "PROVISIONING", "EXPIRED", "TERMINATED", "TERMINATING", "UPDATING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    release_update: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the release_update of this AutonomousDatabaseSoftwareImage. The Release Updates.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this AutonomousDatabaseSoftwareImage. The date and time the Autonomous Database Software Image was created.",
    )


def map_autonomousdatabasesoftwareimage(
    o: oci.database.models.AutonomousDatabaseSoftwareImage,
) -> AutonomousDatabaseSoftwareImage | None:
    """Map oci.database.models.AutonomousDatabaseSoftwareImage → AutonomousDatabaseSoftwareImage Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousDatabaseSoftwareImage(**data)
    except Exception:
        return AutonomousDatabaseSoftwareImage(
            autonomous_dsi_one_off_patches=getattr(
                o, "autonomous_dsi_one_off_patches", None
            ),
            compartment_id=getattr(o, "compartment_id", None),
            database_version=getattr(o, "database_version", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            dst_file_version=getattr(o, "dst_file_version", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            image_shape_family=getattr(o, "image_shape_family", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            release_update=getattr(o, "release_update", None),
            time_created=getattr(o, "time_created", None),
        )


class AutonomousExadataInfrastructure(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousExadataInfrastructure."""

    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this AutonomousExadataInfrastructure. The name of the availability domain that the Autonomous Exadata Infrastructure is located in.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this AutonomousExadataInfrastructure. The OCID of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this AutonomousExadataInfrastructure. The user-friendly name for the Autonomous Exadata Infrastructure.",
    )
    domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the domain of this AutonomousExadataInfrastructure. The domain name for the Autonomous Exadata Infrastructure.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    hostname: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the hostname of this AutonomousExadataInfrastructure. The host name for the Autonomous Exadata Infrastructure node.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousExadataInfrastructure. The OCID of the Autonomous Exadata Infrastructure.",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to all databases in the Autonomous Exadata Infrastructure. The default is BRING_YOUR_OWN_LICENSE. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state of the Autonomous Exadata Infrastructure.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousExadataInfrastructure. The current lifecycle state of the Autonomous Exadata Infrastructure. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the maintenance_window of this AutonomousExadataInfrastructure.",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    nsg_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ for the network security groups (NSGs) to which this resource belongs. Setting this to an empty list removes all resources from all NSGs. For more information about NSGs, see `Security Rules`__. **NsgIds restrictions:** - A network security group (NSG) is optional for Autonomous Databases with private access. The nsgIds list can be empty.",
    )
    scan_dns_name: Optional[Any] = Field(
        None,
        description="The FQDN of the DNS record for the SCAN IP addresses that are associated with the Autonomous Exadata Infrastructure.",
    )
    shape: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the shape of this AutonomousExadataInfrastructure. The shape of the Autonomous Exadata Infrastructure. The shape determines resources to allocate to the Autonomous Exadata Infrastructure (CPU cores, memory and storage).",
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the subnet_id of this AutonomousExadataInfrastructure. The OCID of the subnet the Autonomous Exadata Infrastructure is associated with. **Subnet Restrictions:** - For Autonomous Databases with Autonomous Exadata Infrastructure, do not use a subnet that overlaps with 192.168.128.0/20 These subnets are used by the Oracle Clusterware private interconnect on the database instance. Specifying an overlapping subnet will cause the private interconnect to malfunction. This restriction applies to both the client subnet and backup subnet.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Autonomous Exadata Infrastructure was created.",
    )
    zone_id: Optional[Any] = Field(
        None,
        description="The OCID of the zone the Autonomous Exadata Infrastructure is associated with.",
    )


def map_autonomousexadatainfrastructure(
    o: oci.database.models.AutonomousExadataInfrastructure,
) -> AutonomousExadataInfrastructure | None:
    """Map oci.database.models.AutonomousExadataInfrastructure → AutonomousExadataInfrastructure Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousExadataInfrastructure(**data)
    except Exception:
        return AutonomousExadataInfrastructure(
            availability_domain=getattr(o, "availability_domain", None),
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            domain=getattr(o, "domain", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            hostname=getattr(o, "hostname", None),
            id=getattr(o, "id", None),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            nsg_ids=getattr(o, "nsg_ids", None),
            scan_dns_name=getattr(o, "scan_dns_name", None),
            shape=getattr(o, "shape", None),
            subnet_id=getattr(o, "subnet_id", None),
            time_created=getattr(o, "time_created", None),
            zone_id=getattr(o, "zone_id", None),
        )


class AutonomousPatch(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousPatch."""

    autonomous_patch_type: Optional[Any] = Field(
        None,
        description='Maintenance run type, either "QUARTERLY" or "TIMEZONE". Allowed values for this property are: "QUARTERLY", "TIMEZONE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    description: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the description of this AutonomousPatch. The text describing this patch package.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousPatch. The `OCID`__ of the patch.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="A descriptive text associated with the lifecycleState. Typically can contain additional displayable text.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the patch as a result of lastAction. Allowed values for this property are: "AVAILABLE", "SUCCESS", "IN_PROGRESS", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    patch_model: Optional[Any] = Field(
        None,
        description="Database patching model preference. See `My Oracle Support note 2285040.1`__ for information on the Release Update (RU) and Release Update Revision (RUR) patching models. Allowed values for this property are: \"RELEASE_UPDATES\", \"RELEASE_UPDATE_REVISIONS\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    quarter: Optional[Any] = Field(
        None,
        description="First month of the quarter in which the patch was released.",
    )
    time_released: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_released of this AutonomousPatch. The date and time that the patch was released.",
    )
    type: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the type of this AutonomousPatch. The type of patch. BUNDLE is one example.",
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this AutonomousPatch. The version of this patch package.",
    )
    year: Optional[Any] = Field(
        None,
        description="Year in which the patch was released.",
    )


def map_autonomouspatch(
    o: oci.database.models.AutonomousPatch,
) -> AutonomousPatch | None:
    """Map oci.database.models.AutonomousPatch → AutonomousPatch Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousPatch(**data)
    except Exception:
        return AutonomousPatch(
            autonomous_patch_type=getattr(o, "autonomous_patch_type", None),
            description=getattr(o, "description", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            patch_model=getattr(o, "patch_model", None),
            quarter=getattr(o, "quarter", None),
            time_released=getattr(o, "time_released", None),
            type=getattr(o, "type", None),
            version=getattr(o, "version", None),
            year=getattr(o, "year", None),
        )


class AutonomousVirtualMachine(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousVirtualMachine."""

    autonomous_vm_cluster_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Autonomous VM Cluster associated with the Autonomous Virtual Machine.",
    )
    client_ip_address: Optional[Any] = Field(
        None,
        description="Client IP Address.",
    )
    cloud_autonomous_vm_cluster_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Cloud Autonomous VM Cluster associated with the Autonomous Virtual Machine.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="The number of CPU cores enabled on the Autonomous Virtual Machine.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The allocated local node storage in GBs on the Autonomous Virtual Machine.",
    )
    db_server_display_name: Optional[Any] = Field(
        None,
        description="The display name of the dbServer associated with the Autonomous Virtual Machine.",
    )
    db_server_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Db server associated with the Autonomous Virtual Machine.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousVirtualMachine. The `OCID`__ of the Autonomous Virtual Machine.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousVirtualMachine. The current state of the Autonomous Virtual Machine. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The allocated memory in GBs on the Autonomous Virtual Machine.",
    )
    vm_name: Optional[Any] = Field(
        None,
        description="The name of the Autonomous Virtual Machine.",
    )


def map_autonomousvirtualmachine(
    o: oci.database.models.AutonomousVirtualMachine,
) -> AutonomousVirtualMachine | None:
    """Map oci.database.models.AutonomousVirtualMachine → AutonomousVirtualMachine Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousVirtualMachine(**data)
    except Exception:
        return AutonomousVirtualMachine(
            autonomous_vm_cluster_id=getattr(o, "autonomous_vm_cluster_id", None),
            client_ip_address=getattr(o, "client_ip_address", None),
            cloud_autonomous_vm_cluster_id=getattr(
                o, "cloud_autonomous_vm_cluster_id", None
            ),
            compartment_id=getattr(o, "compartment_id", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_server_display_name=getattr(o, "db_server_display_name", None),
            db_server_id=getattr(o, "db_server_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            vm_name=getattr(o, "vm_name", None),
        )


class AutonomousVmCluster(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousVmCluster."""

    autonomous_data_storage_percentage: Optional[float] = Field(
        None,
        description="The percentage of the data storage used for the Autonomous Databases in an Autonomous VM Cluster.",
    )
    autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size allocated for Autonomous Databases, in TBs.",
    )
    available_autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size available for Autonomous Databases, in TBs.",
    )
    available_container_databases: Optional[Any] = Field(
        None,
        description="The number of Autonomous Container Databases that can be created with the currently available local storage.",
    )
    available_cpus: Optional[Any] = Field(
        None,
        description="The numnber of CPU cores available.",
    )
    available_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="**Deprecated.** Use `availableAutonomousDataStorageSizeInTBs` for Autonomous Databases' data storage availability in TBs.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this AutonomousVmCluster. The `OCID`__ of the compartment.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous VM Cluster. ECPU compute model is the recommended model and OCPU compute model is legacy. See `Compute Models in Autonomous Database on Dedicated Exadata #Infrastructure`__ for more details. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    cpu_core_count_per_node: Optional[Any] = Field(
        None,
        description="The number of CPU cores enabled per VM cluster node.",
    )
    cpu_percentage: Optional[float] = Field(
        None,
        description="The percentage of total number of CPUs used in an Autonomous VM Cluster.",
    )
    cpus_enabled: Optional[Any] = Field(
        None,
        description="The number of enabled CPU cores.",
    )
    cpus_lowest_scaled_value: Optional[Any] = Field(
        None,
        description="The lowest value to which cpus can be scaled down.",
    )
    data_storage_size_in_gbs: Optional[float] = Field(
        None,
        description="The total data storage allocated in GBs.",
    )
    data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The total data storage allocated in TBs",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage allocated in GBs.",
    )
    db_servers: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ of the Db servers.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this AutonomousVmCluster. The user-friendly name for the Autonomous VM cluster. The name does not need to be unique.",
    )
    exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the exadata_infrastructure_id of this AutonomousVmCluster. The `OCID`__ of the Exadata infrastructure.",
    )
    exadata_storage_in_tbs_lowest_scaled_value: Optional[float] = Field(
        None,
        description="The lowest value to which exadataStorage(in TBs) can be scaled down.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this AutonomousVmCluster. The `OCID`__ of the Autonomous VM cluster.",
    )
    is_local_backup_enabled: Optional[Any] = Field(
        None,
        description="If true, database backup on local Exadata storage is configured for the Autonomous VM cluster. If false, database backup on local Exadata storage is not available in the Autonomous VM cluster.",
    )
    is_mtls_enabled: Optional[Any] = Field(
        None,
        description="Enable mutual TLS(mTLS) authentication for database while provisioning a VMCluster. Default is TLS.",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to the Autonomous VM cluster. The default is LICENSE_INCLUDED. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this AutonomousVmCluster. The current state of the Autonomous VM cluster. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="",
    )
    max_acds_lowest_scaled_value: Optional[Any] = Field(
        None,
        description="The lowest value to which maximum number of ACDs can be scaled down.",
    )
    memory_per_oracle_compute_unit_in_gbs: Optional[Any] = Field(
        None,
        description="The amount of memory (in GBs) to be enabled per OCPU or ECPU.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory allocated in GBs.",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    node_count: Optional[Any] = Field(
        None,
        description="The number of nodes in the Autonomous VM Cluster.",
    )
    non_provisionable_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of non-provisionable Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    ocpus_enabled: Optional[float] = Field(
        None,
        description="The number of enabled OCPU cores.",
    )
    provisionable_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="**Deprecated.** Use field totalContainerDatabases.",
    )
    provisioned_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of provisioned Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    provisioned_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs provisioned in an Autonomous VM Cluster.",
    )
    reclaimable_cpus: Optional[Any] = Field(
        None,
        description="CPUs that continue to be included in the count of CPUs available to the Autonomous Container Database even after one of its Autonomous Database is terminated or scaled down. You can release them to the available CPUs at its parent Autonomous VM Cluster level by restarting the Autonomous Container Database.",
    )
    reserved_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs reserved in an Autonomous VM Cluster.",
    )
    scan_listener_port_non_tls: Optional[Any] = Field(
        None,
        description="The SCAN Listener Non TLS port number. Default value is 1521.",
    )
    scan_listener_port_tls: Optional[Any] = Field(
        None,
        description="The SCAN Listener TLS port number. Default value is 2484.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the Autonomous VM cluster was created.",
    )
    time_database_ssl_certificate_expires: Optional[Any] = Field(
        None,
        description="The date and time of the Database SSL certificate expiration.",
    )
    time_ords_certificate_expires: Optional[Any] = Field(
        None,
        description="The date and time of the ORDS certificate expiration.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone to use for the Autonomous VM cluster. For details, see `DB System Time Zones`__.",
    )
    total_autonomous_data_storage_in_tbs: Optional[float] = Field(
        None,
        description="The total data disk group size for Autonomous Databases, in TBs.",
    )
    total_container_databases: Optional[Any] = Field(
        None,
        description="The total number of Autonomous Container Databases that can be created.",
    )
    vm_cluster_network_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the vm_cluster_network_id of this AutonomousVmCluster. The `OCID`__ of the VM cluster network.",
    )


def map_autonomousvmcluster(
    o: oci.database.models.AutonomousVmCluster,
) -> AutonomousVmCluster | None:
    """Map oci.database.models.AutonomousVmCluster → AutonomousVmCluster Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousVmCluster(**data)
    except Exception:
        return AutonomousVmCluster(
            autonomous_data_storage_percentage=getattr(
                o, "autonomous_data_storage_percentage", None
            ),
            autonomous_data_storage_size_in_tbs=getattr(
                o, "autonomous_data_storage_size_in_tbs", None
            ),
            available_autonomous_data_storage_size_in_tbs=getattr(
                o, "available_autonomous_data_storage_size_in_tbs", None
            ),
            available_container_databases=getattr(
                o, "available_container_databases", None
            ),
            available_cpus=getattr(o, "available_cpus", None),
            available_data_storage_size_in_tbs=getattr(
                o, "available_data_storage_size_in_tbs", None
            ),
            compartment_id=getattr(o, "compartment_id", None),
            compute_model=getattr(o, "compute_model", None),
            cpu_core_count_per_node=getattr(o, "cpu_core_count_per_node", None),
            cpu_percentage=getattr(o, "cpu_percentage", None),
            cpus_enabled=getattr(o, "cpus_enabled", None),
            cpus_lowest_scaled_value=getattr(o, "cpus_lowest_scaled_value", None),
            data_storage_size_in_gbs=getattr(o, "data_storage_size_in_gbs", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_servers=getattr(o, "db_servers", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            exadata_infrastructure_id=getattr(o, "exadata_infrastructure_id", None),
            exadata_storage_in_tbs_lowest_scaled_value=getattr(
                o, "exadata_storage_in_tbs_lowest_scaled_value", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_local_backup_enabled=getattr(o, "is_local_backup_enabled", None),
            is_mtls_enabled=getattr(o, "is_mtls_enabled", None),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            max_acds_lowest_scaled_value=getattr(
                o, "max_acds_lowest_scaled_value", None
            ),
            memory_per_oracle_compute_unit_in_gbs=getattr(
                o, "memory_per_oracle_compute_unit_in_gbs", None
            ),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            node_count=getattr(o, "node_count", None),
            non_provisionable_autonomous_container_databases=getattr(
                o, "non_provisionable_autonomous_container_databases", None
            ),
            ocpus_enabled=getattr(o, "ocpus_enabled", None),
            provisionable_autonomous_container_databases=getattr(
                o, "provisionable_autonomous_container_databases", None
            ),
            provisioned_autonomous_container_databases=getattr(
                o, "provisioned_autonomous_container_databases", None
            ),
            provisioned_cpus=getattr(o, "provisioned_cpus", None),
            reclaimable_cpus=getattr(o, "reclaimable_cpus", None),
            reserved_cpus=getattr(o, "reserved_cpus", None),
            scan_listener_port_non_tls=getattr(o, "scan_listener_port_non_tls", None),
            scan_listener_port_tls=getattr(o, "scan_listener_port_tls", None),
            time_created=getattr(o, "time_created", None),
            time_database_ssl_certificate_expires=getattr(
                o, "time_database_ssl_certificate_expires", None
            ),
            time_ords_certificate_expires=getattr(
                o, "time_ords_certificate_expires", None
            ),
            time_zone=getattr(o, "time_zone", None),
            total_autonomous_data_storage_in_tbs=getattr(
                o, "total_autonomous_data_storage_in_tbs", None
            ),
            total_container_databases=getattr(o, "total_container_databases", None),
            vm_cluster_network_id=getattr(o, "vm_cluster_network_id", None),
        )


class AutonomousVmClusterResourceUsage(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.AutonomousVmClusterResourceUsage."""

    autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size allocated for Autonomous Databases, in TBs.",
    )
    autonomous_vm_resource_usage: Optional[Any] = Field(
        None,
        description="List of autonomous vm cluster resource usages.",
    )
    available_autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size available for Autonomous Databases, in TBs.",
    )
    available_cpus: Optional[float] = Field(
        None,
        description="The number of CPU cores available.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage allocated in GBs.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this AutonomousVmClusterResourceUsage. The user-friendly name for the Autonomous VM cluster. The name does not need to be unique.",
    )
    exadata_storage_in_tbs: Optional[float] = Field(
        None,
        description="Total exadata storage allocated for the Autonomous VM Cluster. DATA + RECOVERY + SPARSE + any overhead in TBs.",
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Autonomous VM cluster.",
    )
    is_local_backup_enabled: Optional[Any] = Field(
        None,
        description="If true, database backup on local Exadata storage is configured for the Autonomous VM cluster. If false, database backup on local Exadata storage is not available in the Autonomous VM cluster.",
    )
    memory_per_oracle_compute_unit_in_gbs: Optional[Any] = Field(
        None,
        description="The amount of memory (in GBs) to be enabled per each CPU core.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory allocated in GBs.",
    )
    non_provisionable_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of non-provisionable Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    provisionable_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of provisionable Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    provisioned_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of provisioned Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    provisioned_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs provisioned in an Autonomous VM Cluster.",
    )
    reclaimable_cpus: Optional[float] = Field(
        None,
        description="CPU cores that continue to be included in the count of OCPUs available to the Autonomous Container Database even after one of its Autonomous Database is terminated or scaled down. You can release them to the available OCPUs at its parent AVMC level by restarting the Autonomous Container Database.",
    )
    reserved_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs reserved in an Autonomous VM Cluster.",
    )
    total_container_databases: Optional[Any] = Field(
        None,
        description="The total number of Autonomous Container Databases that can be created.",
    )
    total_cpus: Optional[float] = Field(
        None,
        description="The number of CPU cores enabled on the Autonomous VM cluster.",
    )
    used_autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size used for Autonomous Databases, in TBs.",
    )
    used_cpus: Optional[float] = Field(
        None,
        description="The number of CPU cores alloted to the Autonomous Container Databases in an Autonomous VM cluster.",
    )


def map_autonomousvmclusterresourceusage(
    o: oci.database.models.AutonomousVmClusterResourceUsage,
) -> AutonomousVmClusterResourceUsage | None:
    """Map oci.database.models.AutonomousVmClusterResourceUsage → AutonomousVmClusterResourceUsage Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return AutonomousVmClusterResourceUsage(**data)
    except Exception:
        return AutonomousVmClusterResourceUsage(
            autonomous_data_storage_size_in_tbs=getattr(
                o, "autonomous_data_storage_size_in_tbs", None
            ),
            autonomous_vm_resource_usage=getattr(
                o, "autonomous_vm_resource_usage", None
            ),
            available_autonomous_data_storage_size_in_tbs=getattr(
                o, "available_autonomous_data_storage_size_in_tbs", None
            ),
            available_cpus=getattr(o, "available_cpus", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            display_name=getattr(o, "display_name", None),
            exadata_storage_in_tbs=getattr(o, "exadata_storage_in_tbs", None),
            id=getattr(o, "id", None),
            is_local_backup_enabled=getattr(o, "is_local_backup_enabled", None),
            memory_per_oracle_compute_unit_in_gbs=getattr(
                o, "memory_per_oracle_compute_unit_in_gbs", None
            ),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            non_provisionable_autonomous_container_databases=getattr(
                o, "non_provisionable_autonomous_container_databases", None
            ),
            provisionable_autonomous_container_databases=getattr(
                o, "provisionable_autonomous_container_databases", None
            ),
            provisioned_autonomous_container_databases=getattr(
                o, "provisioned_autonomous_container_databases", None
            ),
            provisioned_cpus=getattr(o, "provisioned_cpus", None),
            reclaimable_cpus=getattr(o, "reclaimable_cpus", None),
            reserved_cpus=getattr(o, "reserved_cpus", None),
            total_container_databases=getattr(o, "total_container_databases", None),
            total_cpus=getattr(o, "total_cpus", None),
            used_autonomous_data_storage_size_in_tbs=getattr(
                o, "used_autonomous_data_storage_size_in_tbs", None
            ),
            used_cpus=getattr(o, "used_cpus", None),
        )


class Backup(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.Backup."""

    availability_domain: Optional[Any] = Field(
        None,
        description="The name of the availability domain where the database backup is stored.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    database_edition: Optional[Any] = Field(
        None,
        description='The Oracle Database edition of the DB system from which the database backup was taken. Allowed values for this property are: "STANDARD_EDITION", "ENTERPRISE_EDITION", "ENTERPRISE_EDITION_HIGH_PERFORMANCE", "ENTERPRISE_EDITION_EXTREME_PERFORMANCE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    database_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the database.",
    )
    database_size_in_gbs: Optional[float] = Field(
        None,
        description="The size of the database in gigabytes at the time the backup was taken.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the backup. The name does not have to be unique.",
    )
    encryption_key_location_details: Optional[Any] = Field(
        None,
        description="",
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the backup.",
    )
    key_store_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the key store of Oracle Vault.",
    )
    key_store_wallet_name: Optional[Any] = Field(
        None,
        description="The wallet name for Oracle Key Vault.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    kms_key_version_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container version that is used in database transparent data encryption (TDE) operations KMS Key can have multiple key versions. If none is specified, the current key version (latest) of the Key Id is used for the operation. Autonomous Database Serverless does not use key versions, hence is not applicable for Autonomous Database Serverless instances.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the backup. Allowed values for this property are: "CREATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "RESTORING", "CANCELING", "CANCELED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    shape: Optional[Any] = Field(
        None,
        description="Shape of the backup's source database.",
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time the backup was completed.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="The date and time the backup started.",
    )
    type: Optional[Any] = Field(
        None,
        description='The type of backup. Allowed values for this property are: "INCREMENTAL", "FULL", "VIRTUAL_FULL", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    vault_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Oracle Cloud Infrastructure `vault`__. This parameter and `secretId` are required for Customer Managed Keys.",
    )
    version: Optional[Any] = Field(
        None,
        description="Version of the backup's source database",
    )


def map_backup(o: oci.database.models.Backup) -> Backup | None:
    """Map oci.database.models.Backup → Backup Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return Backup(**data)
    except Exception:
        return Backup(
            availability_domain=getattr(o, "availability_domain", None),
            compartment_id=getattr(o, "compartment_id", None),
            database_edition=getattr(o, "database_edition", None),
            database_id=getattr(o, "database_id", None),
            database_size_in_gbs=getattr(o, "database_size_in_gbs", None),
            display_name=getattr(o, "display_name", None),
            encryption_key_location_details=getattr(
                o, "encryption_key_location_details", None
            ),
            id=getattr(o, "id", None),
            key_store_id=getattr(o, "key_store_id", None),
            key_store_wallet_name=getattr(o, "key_store_wallet_name", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            kms_key_version_id=getattr(o, "kms_key_version_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            shape=getattr(o, "shape", None),
            time_ended=getattr(o, "time_ended", None),
            time_started=getattr(o, "time_started", None),
            type=getattr(o, "type", None),
            vault_id=getattr(o, "vault_id", None),
            version=getattr(o, "version", None),
        )


class BackupDestination(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.BackupDestination."""

    associated_databases: Optional[Any] = Field(
        None,
        description="List of databases associated with the backup destination.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    connection_string: Optional[Any] = Field(
        None,
        description="For a RECOVERY_APPLIANCE backup destination, the connection string for connecting to the Recovery Appliance.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-provided name of the backup destination.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the backup destination.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="A descriptive text associated with the lifecycleState. Typically contains additional displayable text",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current lifecycle state of the backup destination. Allowed values for this property are: "ACTIVE", "FAILED", "DELETED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    local_mount_point_path: Optional[Any] = Field(
        None,
        description="The local directory path on each VM cluster node where the NFS server location is mounted. The local directory path and the NFS server location must each be the same across all of the VM cluster nodes. Ensure that the NFS mount is maintained continuously on all of the VM cluster nodes.",
    )
    nfs_mount_type: Optional[Any] = Field(
        None,
        description="NFS Mount type for backup destination. Allowed values for this property are: \"SELF_MOUNT\", \"AUTOMATED_MOUNT\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    nfs_server: Optional[Any] = Field(
        None,
        description="Host names or IP addresses for NFS Auto mount.",
    )
    nfs_server_export: Optional[Any] = Field(
        None,
        description="Specifies the directory on which to mount the file system",
    )
    time_at_which_storage_details_are_updated: Optional[Any] = Field(
        None,
        description="The time when the total storage size and the utilized storage size of the backup destination are updated.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the backup destination was created.",
    )
    total_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The total storage size of the backup destination in GBs, rounded to the nearest integer.",
    )
    type: Optional[Any] = Field(
        None,
        description="Type of the backup destination. Allowed values for this property are: \"NFS\", \"RECOVERY_APPLIANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    utilized_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The total amount of space utilized on the backup destination (in GBs), rounded to the nearest integer.",
    )
    vpc_users: Optional[Any] = Field(
        None,
        description="For a RECOVERY_APPLIANCE backup destination, the Virtual Private Catalog (VPC) users that are used to access the Recovery Appliance.",
    )


def map_backupdestination(
    o: oci.database.models.BackupDestination,
) -> BackupDestination | None:
    """Map oci.database.models.BackupDestination → BackupDestination Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return BackupDestination(**data)
    except Exception:
        return BackupDestination(
            associated_databases=getattr(o, "associated_databases", None),
            compartment_id=getattr(o, "compartment_id", None),
            connection_string=getattr(o, "connection_string", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            local_mount_point_path=getattr(o, "local_mount_point_path", None),
            nfs_mount_type=getattr(o, "nfs_mount_type", None),
            nfs_server=getattr(o, "nfs_server", None),
            nfs_server_export=getattr(o, "nfs_server_export", None),
            time_at_which_storage_details_are_updated=getattr(
                o, "time_at_which_storage_details_are_updated", None
            ),
            time_created=getattr(o, "time_created", None),
            total_storage_size_in_gbs=getattr(o, "total_storage_size_in_gbs", None),
            type=getattr(o, "type", None),
            utilized_storage_size_in_gbs=getattr(
                o, "utilized_storage_size_in_gbs", None
            ),
            vpc_users=getattr(o, "vpc_users", None),
        )


class CloudAutonomousVmCluster(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.CloudAutonomousVmCluster."""

    autonomous_data_storage_percentage: Optional[float] = Field(
        None,
        description="The percentage of the data storage used for the Autonomous Databases in an Autonomous VM Cluster.",
    )
    autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size allocated for Autonomous Databases, in TBs.",
    )
    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this CloudAutonomousVmCluster. The name of the availability domain that the cloud Autonomous VM cluster is located in.",
    )
    available_autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size available for Autonomous Databases, in TBs.",
    )
    available_container_databases: Optional[Any] = Field(
        None,
        description="The number of Autonomous Container Databases that can be created with the currently available local storage.",
    )
    available_cpus: Optional[float] = Field(
        None,
        description="CPU cores available for allocation to Autonomous Databases.",
    )
    cloud_exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cloud_exadata_infrastructure_id of this CloudAutonomousVmCluster. The `OCID`__ of the cloud Exadata infrastructure.",
    )
    cluster_time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the Cloud Autonomous VM Cluster.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this CloudAutonomousVmCluster. The `OCID`__ of the compartment.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Cloud Autonomous VM Cluster. ECPU compute model is the recommended model and OCPU compute model is legacy. See `Compute Models in Autonomous Database on Dedicated Exadata #Infrastructure`__ for more details. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="The number of CPU cores on the cloud Autonomous VM cluster.",
    )
    cpu_core_count_per_node: Optional[Any] = Field(
        None,
        description="The number of CPU cores enabled per VM cluster node.",
    )
    cpu_percentage: Optional[float] = Field(
        None,
        description="The percentage of total number of CPUs used in an Autonomous VM Cluster.",
    )
    data_storage_size_in_gbs: Optional[float] = Field(
        None,
        description="The total data storage allocated, in gigabytes (GB).",
    )
    data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The total data storage allocated, in terabytes (TB).",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage allocated in GBs.",
    )
    db_servers: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ of the Db servers.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    description: Optional[Any] = Field(
        None,
        description="User defined description of the cloud Autonomous VM cluster.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this CloudAutonomousVmCluster. The user-friendly name for the cloud Autonomous VM cluster. The name does not need to be unique.",
    )
    domain: Optional[Any] = Field(
        None,
        description="The domain name for the cloud Autonomous VM cluster.",
    )
    exadata_storage_in_tbs_lowest_scaled_value: Optional[float] = Field(
        None,
        description="The lowest value to which exadataStorage (in TBs) can be scaled down.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    hostname: Optional[Any] = Field(
        None,
        description="The hostname for the cloud Autonomous VM cluster.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this CloudAutonomousVmCluster. The `OCID`__ of the Cloud Autonomous VM cluster.",
    )
    is_mtls_enabled_vm_cluster: Optional[Any] = Field(
        None,
        description="Enable mutual TLS(mTLS) authentication for database at time of provisioning a VMCluster. This is applicable to database TLS Certificates only. Default is TLS",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    last_update_history_entry_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance update history. This value is updated when a maintenance update starts.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to the Oracle Autonomous Database. Bring your own license (BYOL) allows you to apply your current on-premises Oracle software licenses to equivalent, highly automated Oracle services in the cloud. License Included allows you to subscribe to new Oracle Database software licenses and the Oracle Database service. Note that when provisioning an `Autonomous Database on dedicated Exadata infrastructure`__, this attribute must be null. It is already set at the Autonomous Exadata Infrastructure level. When provisioning an `Autonomous Database Serverless]`__ database, if a value is not specified, the system defaults the value to `BRING_YOUR_OWN_LICENSE`. Bring your own license (BYOL) also allows you to select the DB edition using the optional parameter. This cannot be updated in parallel with any of the following: cpuCoreCount, computeCount, dataStorageSizeInTBs, adminPassword, isMTLSConnectionRequired, dbWorkload, privateEndpointLabel, nsgIds, dbVersion, dbName, scheduledOperations, dbToolsDetails, or isFreeTier. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this CloudAutonomousVmCluster. The current state of the cloud Autonomous VM cluster. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="",
    )
    max_acds_lowest_scaled_value: Optional[Any] = Field(
        None,
        description="The lowest value to which maximum number of ACDs can be scaled down.",
    )
    memory_per_oracle_compute_unit_in_gbs: Optional[Any] = Field(
        None,
        description="The amount of memory (in GBs) enabled per OCPU or ECPU.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory allocated in GBs.",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    node_count: Optional[Any] = Field(
        None,
        description="The number of database servers in the cloud VM cluster.",
    )
    non_provisionable_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of non-provisionable Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    nsg_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ for the network security groups (NSGs) to which this resource belongs. Setting this to an empty list removes all resources from all NSGs. For more information about NSGs, see `Security Rules`__. **NsgIds restrictions:** - A network security group (NSG) is optional for Autonomous Databases with private access. The nsgIds list can be empty.",
    )
    ocpu_count: Optional[float] = Field(
        None,
        description="The number of CPU cores on the cloud Autonomous VM cluster. Only 1 decimal place is allowed for the fractional part.",
    )
    ocpus_lowest_scaled_value: Optional[Any] = Field(
        None,
        description="The lowest value to which ocpus can be scaled down.",
    )
    provisionable_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of provisionable Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    provisioned_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of provisioned Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    provisioned_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs provisioned in an Autonomous VM Cluster.",
    )
    reclaimable_cpus: Optional[float] = Field(
        None,
        description="CPUs that continue to be included in the count of CPUs available to the Autonomous Container Database even after one of its Autonomous Database is terminated or scaled down. You can release them to the available CPUs at its parent Autonomous VM Cluster level by restarting the Autonomous Container Database.",
    )
    reserved_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs reserved in an Autonomous VM Cluster.",
    )
    scan_listener_port_non_tls: Optional[Any] = Field(
        None,
        description="The SCAN Listener Non TLS port. Default is 1521.",
    )
    scan_listener_port_tls: Optional[Any] = Field(
        None,
        description="The SCAN Listenenr TLS port. Default is 2484.",
    )
    security_attributes: Optional[Any] = Field(
        None,
        description='Security Attributes for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. Example: `{"Oracle-ZPR": {"MaxEgressCount": {"value": "42", "mode": "audit"}}}`',
    )
    shape: Optional[Any] = Field(
        None,
        description="The model name of the Exadata hardware running the cloud Autonomous VM cluster.",
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the subnet_id of this CloudAutonomousVmCluster. The `OCID`__ of the subnet the cloud Autonomous VM Cluster is associated with. **Subnet Restrictions:** - For Exadata and virtual machine 2-node RAC DB systems, do not use a subnet that overlaps with 192.168.128.0/20. These subnets are used by the Oracle Clusterware private interconnect on the database instance. Specifying an overlapping subnet will cause the private interconnect to malfunction. This restriction applies to both the client subnet and backup subnet.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the cloud Autonomous VM cluster was created.",
    )
    time_database_ssl_certificate_expires: Optional[Any] = Field(
        None,
        description="The date and time of Database SSL certificate expiration.",
    )
    time_ords_certificate_expires: Optional[Any] = Field(
        None,
        description="The date and time of ORDS certificate expiration.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The last date and time that the cloud Autonomous VM cluster was updated.",
    )
    total_autonomous_data_storage_in_tbs: Optional[float] = Field(
        None,
        description="The total data disk group size for Autonomous Databases, in TBs.",
    )
    total_container_databases: Optional[Any] = Field(
        None,
        description="The total number of Autonomous Container Databases that can be created with the allocated local storage.",
    )
    total_cpus: Optional[float] = Field(
        None,
        description="The total number of CPUs in an Autonomous VM Cluster.",
    )


def map_cloudautonomousvmcluster(
    o: oci.database.models.CloudAutonomousVmCluster,
) -> CloudAutonomousVmCluster | None:
    """Map oci.database.models.CloudAutonomousVmCluster → CloudAutonomousVmCluster Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return CloudAutonomousVmCluster(**data)
    except Exception:
        return CloudAutonomousVmCluster(
            autonomous_data_storage_percentage=getattr(
                o, "autonomous_data_storage_percentage", None
            ),
            autonomous_data_storage_size_in_tbs=getattr(
                o, "autonomous_data_storage_size_in_tbs", None
            ),
            availability_domain=getattr(o, "availability_domain", None),
            available_autonomous_data_storage_size_in_tbs=getattr(
                o, "available_autonomous_data_storage_size_in_tbs", None
            ),
            available_container_databases=getattr(
                o, "available_container_databases", None
            ),
            available_cpus=getattr(o, "available_cpus", None),
            cloud_exadata_infrastructure_id=getattr(
                o, "cloud_exadata_infrastructure_id", None
            ),
            cluster_time_zone=getattr(o, "cluster_time_zone", None),
            compartment_id=getattr(o, "compartment_id", None),
            compute_model=getattr(o, "compute_model", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            cpu_core_count_per_node=getattr(o, "cpu_core_count_per_node", None),
            cpu_percentage=getattr(o, "cpu_percentage", None),
            data_storage_size_in_gbs=getattr(o, "data_storage_size_in_gbs", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_servers=getattr(o, "db_servers", None),
            defined_tags=getattr(o, "defined_tags", None),
            description=getattr(o, "description", None),
            display_name=getattr(o, "display_name", None),
            domain=getattr(o, "domain", None),
            exadata_storage_in_tbs_lowest_scaled_value=getattr(
                o, "exadata_storage_in_tbs_lowest_scaled_value", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            hostname=getattr(o, "hostname", None),
            id=getattr(o, "id", None),
            is_mtls_enabled_vm_cluster=getattr(o, "is_mtls_enabled_vm_cluster", None),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            last_update_history_entry_id=getattr(
                o, "last_update_history_entry_id", None
            ),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            max_acds_lowest_scaled_value=getattr(
                o, "max_acds_lowest_scaled_value", None
            ),
            memory_per_oracle_compute_unit_in_gbs=getattr(
                o, "memory_per_oracle_compute_unit_in_gbs", None
            ),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            node_count=getattr(o, "node_count", None),
            non_provisionable_autonomous_container_databases=getattr(
                o, "non_provisionable_autonomous_container_databases", None
            ),
            nsg_ids=getattr(o, "nsg_ids", None),
            ocpu_count=getattr(o, "ocpu_count", None),
            ocpus_lowest_scaled_value=getattr(o, "ocpus_lowest_scaled_value", None),
            provisionable_autonomous_container_databases=getattr(
                o, "provisionable_autonomous_container_databases", None
            ),
            provisioned_autonomous_container_databases=getattr(
                o, "provisioned_autonomous_container_databases", None
            ),
            provisioned_cpus=getattr(o, "provisioned_cpus", None),
            reclaimable_cpus=getattr(o, "reclaimable_cpus", None),
            reserved_cpus=getattr(o, "reserved_cpus", None),
            scan_listener_port_non_tls=getattr(o, "scan_listener_port_non_tls", None),
            scan_listener_port_tls=getattr(o, "scan_listener_port_tls", None),
            security_attributes=getattr(o, "security_attributes", None),
            shape=getattr(o, "shape", None),
            subnet_id=getattr(o, "subnet_id", None),
            time_created=getattr(o, "time_created", None),
            time_database_ssl_certificate_expires=getattr(
                o, "time_database_ssl_certificate_expires", None
            ),
            time_ords_certificate_expires=getattr(
                o, "time_ords_certificate_expires", None
            ),
            time_updated=getattr(o, "time_updated", None),
            total_autonomous_data_storage_in_tbs=getattr(
                o, "total_autonomous_data_storage_in_tbs", None
            ),
            total_container_databases=getattr(o, "total_container_databases", None),
            total_cpus=getattr(o, "total_cpus", None),
        )


class CloudAutonomousVmClusterResourceUsage(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.CloudAutonomousVmClusterResourceUsage."""

    autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size allocated for Autonomous Databases, in TBs.",
    )
    autonomous_vm_resource_usage: Optional[Any] = Field(
        None,
        description="List of Autonomous VM resource usages.",
    )
    available_autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size available for Autonomous Databases, in TBs.",
    )
    available_cpus: Optional[float] = Field(
        None,
        description="The number of CPU cores available.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage allocated in GBs.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this CloudAutonomousVmClusterResourceUsage. The user-friendly name for the Autonomous VM cluster. The name does not need to be unique.",
    )
    exadata_storage_in_tbs: Optional[float] = Field(
        None,
        description="Total exadata storage allocated for the Autonomous VM Cluster. DATA + RECOVERY + SPARSE + any overhead in TBs.",
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Cloud Autonomous VM cluster.",
    )
    memory_per_oracle_compute_unit_in_gbs: Optional[Any] = Field(
        None,
        description="The amount of memory (in GBs) to be enabled per each CPU core.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory allocated in GBs.",
    )
    non_provisionable_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of non-provisionable Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    provisionable_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of provisionable Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    provisioned_autonomous_container_databases: Optional[Any] = Field(
        None,
        description="The number of provisioned Autonomous Container Databases in an Autonomous VM Cluster.",
    )
    provisioned_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs provisioned in an Autonomous VM Cluster.",
    )
    reclaimable_cpus: Optional[float] = Field(
        None,
        description="CPU cores that continue to be included in the count of OCPUs available to the Autonomous Container Database even after one of its Autonomous Database is terminated or scaled down. You can release them to the available OCPUs at its parent AVMC level by restarting the Autonomous Container Database.",
    )
    reserved_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs reserved in an Autonomous VM Cluster.",
    )
    total_container_databases: Optional[Any] = Field(
        None,
        description="The total number of Autonomous Container Databases that can be created.",
    )
    total_cpus: Optional[float] = Field(
        None,
        description="The number of CPU cores enabled on the Cloud Autonomous VM cluster.",
    )
    used_autonomous_data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size used for Autonomous Databases, in TBs.",
    )
    used_cpus: Optional[float] = Field(
        None,
        description="The number of CPU cores alloted to the Autonomous Container Databases in an Cloud Autonomous VM cluster.",
    )


def map_cloudautonomousvmclusterresourceusage(
    o: oci.database.models.CloudAutonomousVmClusterResourceUsage,
) -> CloudAutonomousVmClusterResourceUsage | None:
    """Map oci.database.models.CloudAutonomousVmClusterResourceUsage → CloudAutonomousVmClusterResourceUsage Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return CloudAutonomousVmClusterResourceUsage(**data)
    except Exception:
        return CloudAutonomousVmClusterResourceUsage(
            autonomous_data_storage_size_in_tbs=getattr(
                o, "autonomous_data_storage_size_in_tbs", None
            ),
            autonomous_vm_resource_usage=getattr(
                o, "autonomous_vm_resource_usage", None
            ),
            available_autonomous_data_storage_size_in_tbs=getattr(
                o, "available_autonomous_data_storage_size_in_tbs", None
            ),
            available_cpus=getattr(o, "available_cpus", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            display_name=getattr(o, "display_name", None),
            exadata_storage_in_tbs=getattr(o, "exadata_storage_in_tbs", None),
            id=getattr(o, "id", None),
            memory_per_oracle_compute_unit_in_gbs=getattr(
                o, "memory_per_oracle_compute_unit_in_gbs", None
            ),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            non_provisionable_autonomous_container_databases=getattr(
                o, "non_provisionable_autonomous_container_databases", None
            ),
            provisionable_autonomous_container_databases=getattr(
                o, "provisionable_autonomous_container_databases", None
            ),
            provisioned_autonomous_container_databases=getattr(
                o, "provisioned_autonomous_container_databases", None
            ),
            provisioned_cpus=getattr(o, "provisioned_cpus", None),
            reclaimable_cpus=getattr(o, "reclaimable_cpus", None),
            reserved_cpus=getattr(o, "reserved_cpus", None),
            total_container_databases=getattr(o, "total_container_databases", None),
            total_cpus=getattr(o, "total_cpus", None),
            used_autonomous_data_storage_size_in_tbs=getattr(
                o, "used_autonomous_data_storage_size_in_tbs", None
            ),
            used_cpus=getattr(o, "used_cpus", None),
        )


class CloudExadataInfrastructure(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.CloudExadataInfrastructure."""

    activated_storage_count: Optional[Any] = Field(
        None,
        description="The requested number of additional storage servers activated for the Exadata infrastructure.",
    )
    additional_storage_count: Optional[Any] = Field(
        None,
        description="The requested number of additional storage servers for the Exadata infrastructure.",
    )
    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this CloudExadataInfrastructure. The name of the availability domain that the cloud Exadata infrastructure resource is located in.",
    )
    available_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The available storage can be allocated to the cloud Exadata infrastructure resource, in gigabytes (GB).",
    )
    cluster_placement_group_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the cluster placement group of the Exadata Infrastructure.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this CloudExadataInfrastructure. The `OCID`__ of the compartment.",
    )
    compute_count: Optional[Any] = Field(
        None,
        description="The number of compute servers for the cloud Exadata infrastructure.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    cpu_count: Optional[Any] = Field(
        None,
        description="The total number of CPU cores allocated.",
    )
    customer_contacts: Optional[Any] = Field(
        None,
        description="The list of customer email addresses that receive information from Oracle about the specified OCI Database service resource. Oracle uses these email addresses to send notifications about planned and unplanned software maintenance updates, information about system hardware, and other information needed by administrators. Up to 10 email addresses can be added to the customer contacts for a cloud Exadata infrastructure instance.",
    )
    data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="Size, in terabytes, of the DATA disk group.",
    )
    database_server_type: Optional[Any] = Field(
        None,
        description="The database server type of the Exadata infrastructure.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage allocated in GBs.",
    )
    db_server_version: Optional[Any] = Field(
        None,
        description="The software version of the database servers (dom0) in the cloud Exadata infrastructure. Example: 20.1.15",
    )
    defined_file_system_configurations: Optional[Any] = Field(
        None,
        description="Details of the file system configuration of the Exadata infrastructure.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this CloudExadataInfrastructure. The user-friendly name for the cloud Exadata infrastructure resource. The name does not need to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this CloudExadataInfrastructure. The `OCID`__ of the cloud Exadata infrastructure resource.",
    )
    is_scheduling_policy_associated: Optional[Any] = Field(
        None,
        description="If true, the infrastructure is using granular maintenance scheduling preference.",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this CloudExadataInfrastructure. The current lifecycle state of the cloud Exadata infrastructure resource. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="",
    )
    max_cpu_count: Optional[Any] = Field(
        None,
        description="The total number of CPU cores available.",
    )
    max_data_storage_in_tbs: Optional[float] = Field(
        None,
        description="The total available DATA disk group size.",
    )
    max_db_node_storage_in_gbs: Optional[Any] = Field(
        None,
        description="The total local node storage available in GBs.",
    )
    max_memory_in_gbs: Optional[Any] = Field(
        None,
        description="The total memory available in GBs.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory allocated in GBs.",
    )
    monthly_db_server_version: Optional[Any] = Field(
        None,
        description="The monthly software version of the database servers (dom0) in the cloud Exadata infrastructure. Example: 20.1.15",
    )
    monthly_storage_server_version: Optional[Any] = Field(
        None,
        description="The monthly software version of the storage servers (cells) in the cloud Exadata infrastructure. Example: 20.1.15",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    shape: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the shape of this CloudExadataInfrastructure. The model name of the cloud Exadata infrastructure resource.",
    )
    storage_count: Optional[Any] = Field(
        None,
        description="The number of storage servers for the cloud Exadata infrastructure.",
    )
    storage_server_type: Optional[Any] = Field(
        None,
        description="The storage server type of the Exadata infrastructure.",
    )
    storage_server_version: Optional[Any] = Field(
        None,
        description="The software version of the storage servers (cells) in the cloud Exadata infrastructure. Example: 20.1.15",
    )
    subscription_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the subscription with which resource needs to be associated with.",
    )
    system_tags: Optional[Any] = Field(
        None,
        description="System tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the cloud Exadata infrastructure resource was created.",
    )
    total_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The total storage allocated to the cloud Exadata infrastructure resource, in gigabytes (GB).",
    )


def map_cloudexadatainfrastructure(
    o: oci.database.models.CloudExadataInfrastructure,
) -> CloudExadataInfrastructure | None:
    """Map oci.database.models.CloudExadataInfrastructure → CloudExadataInfrastructure Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return CloudExadataInfrastructure(**data)
    except Exception:
        return CloudExadataInfrastructure(
            activated_storage_count=getattr(o, "activated_storage_count", None),
            additional_storage_count=getattr(o, "additional_storage_count", None),
            availability_domain=getattr(o, "availability_domain", None),
            available_storage_size_in_gbs=getattr(
                o, "available_storage_size_in_gbs", None
            ),
            cluster_placement_group_id=getattr(o, "cluster_placement_group_id", None),
            compartment_id=getattr(o, "compartment_id", None),
            compute_count=getattr(o, "compute_count", None),
            compute_model=getattr(o, "compute_model", None),
            cpu_count=getattr(o, "cpu_count", None),
            customer_contacts=getattr(o, "customer_contacts", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            database_server_type=getattr(o, "database_server_type", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_server_version=getattr(o, "db_server_version", None),
            defined_file_system_configurations=getattr(
                o, "defined_file_system_configurations", None
            ),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_scheduling_policy_associated=getattr(
                o, "is_scheduling_policy_associated", None
            ),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            max_cpu_count=getattr(o, "max_cpu_count", None),
            max_data_storage_in_tbs=getattr(o, "max_data_storage_in_tbs", None),
            max_db_node_storage_in_gbs=getattr(o, "max_db_node_storage_in_gbs", None),
            max_memory_in_gbs=getattr(o, "max_memory_in_gbs", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            monthly_db_server_version=getattr(o, "monthly_db_server_version", None),
            monthly_storage_server_version=getattr(
                o, "monthly_storage_server_version", None
            ),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            shape=getattr(o, "shape", None),
            storage_count=getattr(o, "storage_count", None),
            storage_server_type=getattr(o, "storage_server_type", None),
            storage_server_version=getattr(o, "storage_server_version", None),
            subscription_id=getattr(o, "subscription_id", None),
            system_tags=getattr(o, "system_tags", None),
            time_created=getattr(o, "time_created", None),
            total_storage_size_in_gbs=getattr(o, "total_storage_size_in_gbs", None),
        )


class CloudExadataInfrastructureUnallocatedResources(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.CloudExadataInfrastructureUnallocatedResources."""

    cloud_autonomous_vm_clusters: Optional[Any] = Field(
        None,
        description="The list of Cloud Autonomous VM Clusters on the Infrastructure and their associated unallocated resources details.",
    )
    cloud_exadata_infrastructure_display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cloud_exadata_infrastructure_display_name of this CloudExadataInfrastructureUnallocatedResources. The user-friendly name for the Cloud Exadata infrastructure. The name does not need to be unique.",
    )
    cloud_exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cloud_exadata_infrastructure_id of this CloudExadataInfrastructureUnallocatedResources. The `OCID`__ of the Cloud Exadata infrastructure.",
    )
    exadata_storage_in_tbs: Optional[float] = Field(
        None,
        description="Total unallocated exadata storage in the infrastructure in TBs.",
    )
    local_storage_in_gbs: Optional[Any] = Field(
        None,
        description="The minimum amount of unallocated storage available across all nodes in the infrastructure.",
    )
    memory_in_gbs: Optional[Any] = Field(
        None,
        description="The minimum amount of unallocated memory available across all nodes in the infrastructure.",
    )
    ocpus: Optional[Any] = Field(
        None,
        description="The minimum amount of unallocated ocpus available across all nodes in the infrastructure.",
    )


def map_cloudexadatainfrastructureunallocatedresources(
    o: oci.database.models.CloudExadataInfrastructureUnallocatedResources,
) -> CloudExadataInfrastructureUnallocatedResources | None:
    """Map oci.database.models.CloudExadataInfrastructureUnallocatedResources → CloudExadataInfrastructureUnallocatedResources Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return CloudExadataInfrastructureUnallocatedResources(**data)
    except Exception:
        return CloudExadataInfrastructureUnallocatedResources(
            cloud_autonomous_vm_clusters=getattr(
                o, "cloud_autonomous_vm_clusters", None
            ),
            cloud_exadata_infrastructure_display_name=getattr(
                o, "cloud_exadata_infrastructure_display_name", None
            ),
            cloud_exadata_infrastructure_id=getattr(
                o, "cloud_exadata_infrastructure_id", None
            ),
            exadata_storage_in_tbs=getattr(o, "exadata_storage_in_tbs", None),
            local_storage_in_gbs=getattr(o, "local_storage_in_gbs", None),
            memory_in_gbs=getattr(o, "memory_in_gbs", None),
            ocpus=getattr(o, "ocpus", None),
        )


class CloudVmCluster(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.CloudVmCluster."""

    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this CloudVmCluster. The name of the availability domain that the cloud Exadata infrastructure resource is located in.",
    )
    backup_network_nsg_ids: Optional[Any] = Field(
        None,
        description="A list of the `OCIDs`__ of the network security groups (NSGs) that the backup network of this DB system belongs to. Setting this to an empty array after the list is created removes the resource from all NSGs. For more information about NSGs, see `Security Rules`__. Applicable only to Exadata systems.",
    )
    backup_subnet_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the backup network subnet associated with the cloud VM cluster. **Subnet Restriction:** See the subnet restrictions information for **subnetId**.",
    )
    cloud_automation_update_details: Optional[Any] = Field(
        None,
        description="",
    )
    cloud_exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cloud_exadata_infrastructure_id of this CloudVmCluster. The `OCID`__ of the cloud Exadata infrastructure.",
    )
    cluster_name: Optional[Any] = Field(
        None,
        description="The cluster name for cloud VM cluster. The cluster name must begin with an alphabetic character, and may contain hyphens (-). Underscores (_) are not permitted. The cluster name can be no longer than 11 characters and is not case sensitive.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this CloudVmCluster. The `OCID`__ of the compartment.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cpu_core_count of this CloudVmCluster. The number of CPU cores enabled on the cloud VM cluster.",
    )
    data_collection_options: Optional[Any] = Field(
        None,
        description="",
    )
    data_storage_percentage: Optional[Any] = Field(
        None,
        description="The percentage assigned to DATA storage (user data and database files). The remaining percentage is assigned to RECO storage (database redo logs, archive logs, and recovery manager backups). Accepted values are 35, 40, 60 and 80. The default is 80 percent assigned to DATA storage. See `Storage Configuration`__ in the Exadata documentation for details on the impact of the configuration settings on storage.",
    )
    data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="The data disk group size to be allocated in TBs.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage to be allocated in GBs.",
    )
    db_servers: Optional[Any] = Field(
        None,
        description="The list of DB servers.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    disk_redundancy: Optional[Any] = Field(
        None,
        description="The type of redundancy configured for the cloud Vm cluster. NORMAL is 2-way redundancy. HIGH is 3-way redundancy. Allowed values for this property are: \"HIGH\", \"NORMAL\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this CloudVmCluster. The user-friendly name for the cloud VM cluster. The name does not need to be unique.",
    )
    domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the domain of this CloudVmCluster. The domain name for the cloud VM cluster.",
    )
    file_system_configuration_details: Optional[Any] = Field(
        None,
        description="Details of the file system configuration of the VM cluster.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    gi_software_image_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of a grid infrastructure software image. This is a database software image of the type `GRID_IMAGE`.",
    )
    gi_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Grid Infrastructure (GI) software version.",
    )
    hostname: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the hostname of this CloudVmCluster. The hostname for the cloud VM cluster.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this CloudVmCluster. The `OCID`__ of the cloud VM cluster.",
    )
    iorm_config_cache: Optional[Any] = Field(
        None,
        description="",
    )
    is_local_backup_enabled: Optional[Any] = Field(
        None,
        description="If true, database backup on local Exadata storage is configured for the cloud VM cluster. If false, database backup on local Exadata storage is not available in the cloud VM cluster.",
    )
    is_sparse_diskgroup_enabled: Optional[Any] = Field(
        None,
        description="If true, sparse disk group is configured for the cloud VM cluster. If false, sparse disk group is not created.",
    )
    last_update_history_entry_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance update history entry. This value is updated when a maintenance update starts.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to the cloud VM cluster. The default is LICENSE_INCLUDED. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this CloudVmCluster. The current state of the cloud VM cluster. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    listener_port: Optional[Any] = Field(
        None,
        description="The port number configured for the listener on the cloud VM cluster.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory to be allocated in GBs.",
    )
    node_count: Optional[Any] = Field(
        None,
        description="The number of nodes in the cloud VM cluster.",
    )
    nsg_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ for the network security groups (NSGs) to which this resource belongs. Setting this to an empty list removes all resources from all NSGs. For more information about NSGs, see `Security Rules`__. **NsgIds restrictions:** - A network security group (NSG) is optional for Autonomous Databases with private access. The nsgIds list can be empty.",
    )
    ocpu_count: Optional[float] = Field(
        None,
        description="The number of OCPU cores to enable on the cloud VM cluster. Only 1 decimal place is allowed for the fractional part.",
    )
    scan_dns_name: Optional[Any] = Field(
        None,
        description="The FQDN of the DNS record for the SCAN IP addresses that are associated with the cloud VM cluster.",
    )
    scan_dns_record_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the DNS record for the SCAN IP addresses that are associated with the cloud VM cluster.",
    )
    scan_ip_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Single Client Access Name (SCAN) IP addresses associated with the cloud VM cluster. SCAN IP addresses are typically used for load balancing and are not assigned to any interface. Oracle Clusterware directs the requests to the appropriate nodes in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    scan_listener_port_tcp: Optional[Any] = Field(
        None,
        description="The TCP Single Client Access Name (SCAN) port. The default port is 1521.",
    )
    scan_listener_port_tcp_ssl: Optional[Any] = Field(
        None,
        description="The TCPS Single Client Access Name (SCAN) port. The default port is 2484.",
    )
    security_attributes: Optional[Any] = Field(
        None,
        description='Security Attributes for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. Example: `{"Oracle-ZPR": {"MaxEgressCount": {"value": "42", "mode": "audit"}}}`',
    )
    shape: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the shape of this CloudVmCluster. The model name of the Exadata hardware running the cloud VM cluster.",
    )
    ssh_public_keys: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the ssh_public_keys of this CloudVmCluster. The public key portion of one or more key pairs used for SSH access to the cloud VM cluster.",
    )
    storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The storage allocation for the disk group, in gigabytes (GB).",
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the subnet_id of this CloudVmCluster. The `OCID`__ of the subnet associated with the cloud VM cluster. **Subnet Restrictions:** - For Exadata and virtual machine 2-node RAC systems, do not use a subnet that overlaps with 192.168.128.0/20. These subnets are used by the Oracle Clusterware private interconnect on the database instance. Specifying an overlapping subnet will cause the private interconnect to malfunction. This restriction applies to both the client subnet and backup subnet.",
    )
    subscription_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the subscription with which resource needs to be associated with.",
    )
    system_tags: Optional[Any] = Field(
        None,
        description="System tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    system_version: Optional[Any] = Field(
        None,
        description="Operating system version of the image.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the cloud VM cluster was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the cloud VM cluster. For details, see `Exadata Infrastructure Time Zones`__.",
    )
    vip_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the virtual IP (VIP) addresses associated with the cloud VM cluster. The Cluster Ready Services (CRS) creates and maintains one VIP address for each node in the Exadata Cloud Service instance to enable failover. If one node fails, the VIP is reassigned to another active node in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    zone_id: Optional[Any] = Field(
        None,
        description="The OCID of the zone the cloud VM cluster is associated with.",
    )


def map_cloudvmcluster(o: oci.database.models.CloudVmCluster) -> CloudVmCluster | None:
    """Map oci.database.models.CloudVmCluster → CloudVmCluster Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return CloudVmCluster(**data)
    except Exception:
        return CloudVmCluster(
            availability_domain=getattr(o, "availability_domain", None),
            backup_network_nsg_ids=getattr(o, "backup_network_nsg_ids", None),
            backup_subnet_id=getattr(o, "backup_subnet_id", None),
            cloud_automation_update_details=getattr(
                o, "cloud_automation_update_details", None
            ),
            cloud_exadata_infrastructure_id=getattr(
                o, "cloud_exadata_infrastructure_id", None
            ),
            cluster_name=getattr(o, "cluster_name", None),
            compartment_id=getattr(o, "compartment_id", None),
            compute_model=getattr(o, "compute_model", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            data_collection_options=getattr(o, "data_collection_options", None),
            data_storage_percentage=getattr(o, "data_storage_percentage", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_servers=getattr(o, "db_servers", None),
            defined_tags=getattr(o, "defined_tags", None),
            disk_redundancy=getattr(o, "disk_redundancy", None),
            display_name=getattr(o, "display_name", None),
            domain=getattr(o, "domain", None),
            file_system_configuration_details=getattr(
                o, "file_system_configuration_details", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            gi_software_image_id=getattr(o, "gi_software_image_id", None),
            gi_version=getattr(o, "gi_version", None),
            hostname=getattr(o, "hostname", None),
            id=getattr(o, "id", None),
            iorm_config_cache=getattr(o, "iorm_config_cache", None),
            is_local_backup_enabled=getattr(o, "is_local_backup_enabled", None),
            is_sparse_diskgroup_enabled=getattr(o, "is_sparse_diskgroup_enabled", None),
            last_update_history_entry_id=getattr(
                o, "last_update_history_entry_id", None
            ),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            listener_port=getattr(o, "listener_port", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            node_count=getattr(o, "node_count", None),
            nsg_ids=getattr(o, "nsg_ids", None),
            ocpu_count=getattr(o, "ocpu_count", None),
            scan_dns_name=getattr(o, "scan_dns_name", None),
            scan_dns_record_id=getattr(o, "scan_dns_record_id", None),
            scan_ip_ids=getattr(o, "scan_ip_ids", None),
            scan_listener_port_tcp=getattr(o, "scan_listener_port_tcp", None),
            scan_listener_port_tcp_ssl=getattr(o, "scan_listener_port_tcp_ssl", None),
            security_attributes=getattr(o, "security_attributes", None),
            shape=getattr(o, "shape", None),
            ssh_public_keys=getattr(o, "ssh_public_keys", None),
            storage_size_in_gbs=getattr(o, "storage_size_in_gbs", None),
            subnet_id=getattr(o, "subnet_id", None),
            subscription_id=getattr(o, "subscription_id", None),
            system_tags=getattr(o, "system_tags", None),
            system_version=getattr(o, "system_version", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
            vip_ids=getattr(o, "vip_ids", None),
            zone_id=getattr(o, "zone_id", None),
        )


class ExadataIormConfig(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExadataIormConfig."""

    db_plans: Optional[Any] = Field(
        None,
        description="An array of IORM settings for all the database in the Exadata DB system.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current `lifecycleState`.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of IORM configuration for the Exadata DB system. Allowed values for this property are: "BOOTSTRAPPING", "ENABLED", "DISABLED", "UPDATING", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    objective: Optional[Any] = Field(
        None,
        description='The current value for the IORM objective. The default is `AUTO`. Allowed values for this property are: "LOW_LATENCY", "HIGH_THROUGHPUT", "BALANCED", "AUTO", "BASIC", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )


def map_exadataiormconfig(
    o: oci.database.models.ExadataIormConfig,
) -> ExadataIormConfig | None:
    """Map oci.database.models.ExadataIormConfig → ExadataIormConfig Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExadataIormConfig(**data)
    except Exception:
        return ExadataIormConfig(
            db_plans=getattr(o, "db_plans", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            objective=getattr(o, "objective", None),
        )


class Update(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.Update."""

    available_actions: Optional[Any] = Field(
        None,
        description='The possible actions performed by the update operation on the infrastructure components. Allowed values for items in this list are: "ROLLING_APPLY", "NON_ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    description: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the description of this Update. Details of the maintenance update package.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this Update. The `OCID`__ of the maintenance update.",
    )
    last_action: Optional[Any] = Field(
        None,
        description='The previous update action performed. Allowed values for this property are: "ROLLING_APPLY", "NON_ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Descriptive text providing additional details about the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the maintenance update. Dependent on value of `lastAction`. Allowed values for this property are: "AVAILABLE", "SUCCESS", "IN_PROGRESS", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_released: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_released of this Update. The date and time the maintenance update was released.",
    )
    update_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the update_type of this Update. The type of cloud VM cluster maintenance update. Allowed values for this property are: "GI_UPGRADE", "GI_PATCH", "OS_UPDATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this Update. The version of the maintenance update package.",
    )


def map_update(o: oci.database.models.Update) -> Update | None:
    """Map oci.database.models.Update → Update Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return Update(**data)
    except Exception:
        return Update(
            available_actions=getattr(o, "available_actions", None),
            description=getattr(o, "description", None),
            id=getattr(o, "id", None),
            last_action=getattr(o, "last_action", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_released=getattr(o, "time_released", None),
            update_type=getattr(o, "update_type", None),
            version=getattr(o, "version", None),
        )


class UpdateHistoryEntry(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.UpdateHistoryEntry."""

    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this UpdateHistoryEntry. The `OCID`__ of the maintenance update history entry.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Descriptive text providing additional details about the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this UpdateHistoryEntry. The current lifecycle state of the maintenance update operation. Allowed values for this property are: "IN_PROGRESS", "SUCCEEDED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_completed: Optional[Any] = Field(
        None,
        description="The date and time when the maintenance update action completed.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_started of this UpdateHistoryEntry. The date and time when the maintenance update action started.",
    )
    update_action: Optional[Any] = Field(
        None,
        description='The update action. Allowed values for this property are: "ROLLING_APPLY", "NON_ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    update_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the update_id of this UpdateHistoryEntry. The `OCID`__ of the maintenance update.",
    )
    update_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the update_type of this UpdateHistoryEntry. The type of cloud VM cluster maintenance update. Allowed values for this property are: "GI_UPGRADE", "GI_PATCH", "OS_UPDATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )


def map_updatehistoryentry(
    o: oci.database.models.UpdateHistoryEntry,
) -> UpdateHistoryEntry | None:
    """Map oci.database.models.UpdateHistoryEntry → UpdateHistoryEntry Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return UpdateHistoryEntry(**data)
    except Exception:
        return UpdateHistoryEntry(
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_completed=getattr(o, "time_completed", None),
            time_started=getattr(o, "time_started", None),
            update_action=getattr(o, "update_action", None),
            update_id=getattr(o, "update_id", None),
            update_type=getattr(o, "update_type", None),
        )


class ConsoleConnection(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ConsoleConnection."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ConsoleConnection. The OCID of the compartment to contain the console connection.",
    )
    connection_string: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the connection_string of this ConsoleConnection. The SSH connection string for the console connection.",
    )
    db_node_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_node_id of this ConsoleConnection. The OCID of the database node.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    fingerprint: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the fingerprint of this ConsoleConnection. The SSH public key fingerprint for the console connection.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ConsoleConnection. The OCID of the console connection.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ConsoleConnection. The current state of the console connection. Allowed values for this property are: "ACTIVE", "CREATING", "DELETED", "DELETING", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    service_host_key_fingerprint: Optional[Any] = Field(
        None,
        description="The SSH public key's fingerprint for the console connection service host.",
    )


def map_consoleconnection(
    o: oci.database.models.ConsoleConnection,
) -> ConsoleConnection | None:
    """Map oci.database.models.ConsoleConnection → ConsoleConnection Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ConsoleConnection(**data)
    except Exception:
        return ConsoleConnection(
            compartment_id=getattr(o, "compartment_id", None),
            connection_string=getattr(o, "connection_string", None),
            db_node_id=getattr(o, "db_node_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            fingerprint=getattr(o, "fingerprint", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            service_host_key_fingerprint=getattr(
                o, "service_host_key_fingerprint", None
            ),
        )


class ConsoleHistory(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ConsoleHistory."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ConsoleHistory. The OCID of the compartment containing the console history.",
    )
    db_node_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_node_id of this ConsoleHistory. The OCID of the database node.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the console history. The name does not need to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ConsoleHistory. The OCID of the console history.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ConsoleHistory. The current state of the console history. Allowed values for this property are: "REQUESTED", "GETTING_HISTORY", "SUCCEEDED", "FAILED", "DELETED", "DELETING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this ConsoleHistory. The date and time the console history was created.",
    )


def map_consolehistory(o: oci.database.models.ConsoleHistory) -> ConsoleHistory | None:
    """Map oci.database.models.ConsoleHistory → ConsoleHistory Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ConsoleHistory(**data)
    except Exception:
        return ConsoleHistory(
            compartment_id=getattr(o, "compartment_id", None),
            db_node_id=getattr(o, "db_node_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_created=getattr(o, "time_created", None),
        )


class DataGuardAssociation(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DataGuardAssociation."""

    apply_lag: Optional[Any] = Field(
        None,
        description="The lag time between updates to the primary database and application of the redo data on the standby database, as computed by the reporting database. Example: `9 seconds`",
    )
    apply_rate: Optional[Any] = Field(
        None,
        description="The rate at which redo logs are synced between the associated databases. Example: `180 Mb per second`",
    )
    database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the database_id of this DataGuardAssociation. The `OCID`__ of the reporting database.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DataGuardAssociation. The `OCID`__ of the Data Guard association.",
    )
    is_active_data_guard_enabled: Optional[Any] = Field(
        None,
        description="True if active Data Guard is enabled.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycleState, if available.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DataGuardAssociation. The current state of the Data Guard association. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "UPGRADING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_data_guard_association_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the peer database's Data Guard association.",
    )
    peer_database_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the associated peer database.",
    )
    peer_db_home_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Database Home containing the associated peer database.",
    )
    peer_db_system_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the peer_db_system_id of this DataGuardAssociation. The `OCID`__ of the DB system containing the associated peer database.",
    )
    peer_role: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the peer_role of this DataGuardAssociation. The role of the peer database in this Data Guard association. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    protection_mode: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the protection_mode of this DataGuardAssociation. The protection mode of this Data Guard association. For more information, see `Oracle Data Guard Protection Modes`__ in the Oracle Data Guard documentation. Allowed values for this property are: "MAXIMUM_AVAILABILITY", "MAXIMUM_PERFORMANCE", "MAXIMUM_PROTECTION", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    role: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the role of this DataGuardAssociation. The role of the reporting database in this Data Guard association. Allowed values for this property are: "PRIMARY", "STANDBY", "DISABLED_STANDBY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Data Guard association was created.",
    )
    transport_type: Optional[Any] = Field(
        None,
        description='The redo transport type used by this Data Guard association. For more information, see `Redo Transport Services`__ in the Oracle Data Guard documentation. Allowed values for this property are: "SYNC", "ASYNC", "FASTSYNC", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )


def map_dataguardassociation(
    o: oci.database.models.DataGuardAssociation,
) -> DataGuardAssociation | None:
    """Map oci.database.models.DataGuardAssociation → DataGuardAssociation Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DataGuardAssociation(**data)
    except Exception:
        return DataGuardAssociation(
            apply_lag=getattr(o, "apply_lag", None),
            apply_rate=getattr(o, "apply_rate", None),
            database_id=getattr(o, "database_id", None),
            id=getattr(o, "id", None),
            is_active_data_guard_enabled=getattr(
                o, "is_active_data_guard_enabled", None
            ),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            peer_data_guard_association_id=getattr(
                o, "peer_data_guard_association_id", None
            ),
            peer_database_id=getattr(o, "peer_database_id", None),
            peer_db_home_id=getattr(o, "peer_db_home_id", None),
            peer_db_system_id=getattr(o, "peer_db_system_id", None),
            peer_role=getattr(o, "peer_role", None),
            protection_mode=getattr(o, "protection_mode", None),
            role=getattr(o, "role", None),
            time_created=getattr(o, "time_created", None),
            transport_type=getattr(o, "transport_type", None),
        )


class Database(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.Database."""

    character_set: Optional[Any] = Field(
        None,
        description="The character set for the database.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this Database. The `OCID`__ of the compartment.",
    )
    connection_strings: Optional[Any] = Field(
        None,
        description="The Connection strings used to connect to the Oracle Database.",
    )
    data_guard_group: Optional[Any] = Field(
        None,
        description="",
    )
    database_management_config: Optional[Any] = Field(
        None,
        description="",
    )
    database_software_image_id: Optional[Any] = Field(
        None,
        description="The database software image `OCID`__",
    )
    db_backup_config: Optional[Any] = Field(
        None,
        description="",
    )
    db_home_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Database Home.",
    )
    db_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_name of this Database. The database name.",
    )
    db_system_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the DB system.",
    )
    db_unique_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_unique_name of this Database. A system-generated name for the database to ensure uniqueness within an Oracle Data Guard group (a primary database and its standby databases). The unique name cannot be changed.",
    )
    db_workload: Optional[Any] = Field(
        None,
        description="**Deprecated.** The dbWorkload field has been deprecated for Exadata Database Service on Dedicated Infrastructure, Exadata Database Service on Cloud@Customer, and Base Database Service. Support for this attribute will end in November 2023. You may choose to update your custom scripts to exclude the dbWorkload attribute. After November 2023 if you pass a value to the dbWorkload attribute, it will be ignored. The database workload type.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    encryption_key_location_details: Optional[Any] = Field(
        None,
        description="",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this Database. The `OCID`__ of the database.",
    )
    is_cdb: Optional[Any] = Field(
        None,
        description="True if the database is a container database.",
    )
    key_store_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the key store of Oracle Vault.",
    )
    key_store_wallet_name: Optional[Any] = Field(
        None,
        description="The wallet name for Oracle Key Vault.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    kms_key_version_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container version that is used in database transparent data encryption (TDE) operations KMS Key can have multiple key versions. If none is specified, the current key version (latest) of the Key Id is used for the operation. Autonomous Database Serverless does not use key versions, hence is not applicable for Autonomous Database Serverless instances.",
    )
    last_backup_duration_in_seconds: Optional[Any] = Field(
        None,
        description="The duration when the latest database backup created.",
    )
    last_backup_timestamp: Optional[Any] = Field(
        None,
        description="The date and time when the latest database backup was created.",
    )
    last_failed_backup_timestamp: Optional[Any] = Field(
        None,
        description="The date and time when the latest database backup failed.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this Database. The current state of the database. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "BACKUP_IN_PROGRESS", "UPGRADING", "CONVERTING", "TERMINATING", "TERMINATED", "RESTORE_FAILED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    ncharacter_set: Optional[Any] = Field(
        None,
        description="The national character set for the database.",
    )
    pdb_name: Optional[Any] = Field(
        None,
        description="The name of the pluggable database. The name must begin with an alphabetic character and can contain a maximum of thirty alphanumeric characters. Special characters are not permitted. Pluggable database should not be same as database name.",
    )
    sid_prefix: Optional[Any] = Field(
        None,
        description="Specifies a prefix for the `Oracle SID` of the database to be created.",
    )
    source_database_point_in_time_recovery_timestamp: Optional[Any] = Field(
        None,
        description="Point in time recovery timeStamp of the source database at which cloned database system is cloned from the source database system, as described in `RFC 3339`__",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the database was created.",
    )
    vault_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Oracle Cloud Infrastructure `vault`__. This parameter and `secretId` are required for Customer Managed Keys.",
    )
    vm_cluster_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the VM cluster.",
    )


def map_database(o: oci.database.models.Database) -> Database | None:
    """Map oci.database.models.Database → Database Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return Database(**data)
    except Exception:
        return Database(
            character_set=getattr(o, "character_set", None),
            compartment_id=getattr(o, "compartment_id", None),
            connection_strings=getattr(o, "connection_strings", None),
            data_guard_group=getattr(o, "data_guard_group", None),
            database_management_config=getattr(o, "database_management_config", None),
            database_software_image_id=getattr(o, "database_software_image_id", None),
            db_backup_config=getattr(o, "db_backup_config", None),
            db_home_id=getattr(o, "db_home_id", None),
            db_name=getattr(o, "db_name", None),
            db_system_id=getattr(o, "db_system_id", None),
            db_unique_name=getattr(o, "db_unique_name", None),
            db_workload=getattr(o, "db_workload", None),
            defined_tags=getattr(o, "defined_tags", None),
            encryption_key_location_details=getattr(
                o, "encryption_key_location_details", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_cdb=getattr(o, "is_cdb", None),
            key_store_id=getattr(o, "key_store_id", None),
            key_store_wallet_name=getattr(o, "key_store_wallet_name", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            kms_key_version_id=getattr(o, "kms_key_version_id", None),
            last_backup_duration_in_seconds=getattr(
                o, "last_backup_duration_in_seconds", None
            ),
            last_backup_timestamp=getattr(o, "last_backup_timestamp", None),
            last_failed_backup_timestamp=getattr(
                o, "last_failed_backup_timestamp", None
            ),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            ncharacter_set=getattr(o, "ncharacter_set", None),
            pdb_name=getattr(o, "pdb_name", None),
            sid_prefix=getattr(o, "sid_prefix", None),
            source_database_point_in_time_recovery_timestamp=getattr(
                o, "source_database_point_in_time_recovery_timestamp", None
            ),
            time_created=getattr(o, "time_created", None),
            vault_id=getattr(o, "vault_id", None),
            vm_cluster_id=getattr(o, "vm_cluster_id", None),
        )


class DatabaseSoftwareImage(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DatabaseSoftwareImage."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this DatabaseSoftwareImage. The `OCID`__ of the compartment.",
    )
    database_software_image_included_patches: Optional[Any] = Field(
        None,
        description="List of one-off patches for Database Homes.",
    )
    database_software_image_one_off_patches: Optional[Any] = Field(
        None,
        description="List of one-off patches for Database Homes.",
    )
    database_version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the database_version of this DatabaseSoftwareImage. The database version with which the database software image is to be built.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this DatabaseSoftwareImage. The user-friendly name for the database software image. The name does not have to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DatabaseSoftwareImage. The `OCID`__ of the database software image.",
    )
    image_shape_family: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the image_shape_family of this DatabaseSoftwareImage. To what shape the image is meant for. Allowed values for this property are: "VM_BM_SHAPE", "EXADATA_SHAPE", "EXACC_SHAPE", "EXADBXS_SHAPE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    image_type: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the image_type of this DatabaseSoftwareImage. The type of software image. Can be grid or database. Allowed values for this property are: \"GRID_IMAGE\", \"DATABASE_IMAGE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    included_patches_summary: Optional[Any] = Field(
        None,
        description="The patches included in the image and the version of the image.",
    )
    is_upgrade_supported: Optional[Any] = Field(
        None,
        description="True if this Database software image is supported for Upgrade.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Detailed message for the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DatabaseSoftwareImage. The current state of the database software image. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "DELETING", "DELETED", "FAILED", "TERMINATING", "TERMINATED", "UPDATING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    ls_inventory: Optional[Any] = Field(
        None,
        description="The output from the OPatch lsInventory command, which is passed as a string.",
    )
    patch_set: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the patch_set of this DatabaseSoftwareImage. The PSU or PBP or Release Updates. To get a list of supported versions, use the :func:`list_db_versions` operation.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this DatabaseSoftwareImage. The date and time the database software image was created.",
    )


def map_databasesoftwareimage(
    o: oci.database.models.DatabaseSoftwareImage,
) -> DatabaseSoftwareImage | None:
    """Map oci.database.models.DatabaseSoftwareImage → DatabaseSoftwareImage Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DatabaseSoftwareImage(**data)
    except Exception:
        return DatabaseSoftwareImage(
            compartment_id=getattr(o, "compartment_id", None),
            database_software_image_included_patches=getattr(
                o, "database_software_image_included_patches", None
            ),
            database_software_image_one_off_patches=getattr(
                o, "database_software_image_one_off_patches", None
            ),
            database_version=getattr(o, "database_version", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            image_shape_family=getattr(o, "image_shape_family", None),
            image_type=getattr(o, "image_type", None),
            included_patches_summary=getattr(o, "included_patches_summary", None),
            is_upgrade_supported=getattr(o, "is_upgrade_supported", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            ls_inventory=getattr(o, "ls_inventory", None),
            patch_set=getattr(o, "patch_set", None),
            time_created=getattr(o, "time_created", None),
        )


class DatabaseUpgradeHistoryEntry(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DatabaseUpgradeHistoryEntry."""

    action: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the action of this DatabaseUpgradeHistoryEntry. The database upgrade action. Allowed values for this property are: "PRECHECK", "UPGRADE", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DatabaseUpgradeHistoryEntry. The `OCID`__ of the database upgrade history.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DatabaseUpgradeHistoryEntry. Status of database upgrade history SUCCEEDED|IN_PROGRESS|FAILED. Allowed values for this property are: "SUCCEEDED", "FAILED", "IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    options: Optional[Any] = Field(
        None,
        description='Additional upgrade options supported by DBUA(Database Upgrade Assistant). Example: "-upgradeTimezone false -keepEvents"',
    )
    source: Optional[Any] = Field(
        None,
        description='The source of the Oracle Database software to be used for the upgrade. - Use `DB_HOME` to specify an existing Database Home to upgrade the database. The database is moved to the target Database Home and makes use of the Oracle Database software version of the target Database Home. - Use `DB_VERSION` to specify a generally-available Oracle Database software version to upgrade the database. - Use `DB_SOFTWARE_IMAGE` to specify a `database software image`__ to upgrade the database. Allowed values for this property are: "DB_HOME", "DB_VERSION", "DB_SOFTWARE_IMAGE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    source_db_home_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Database Home.",
    )
    target_database_software_image_id: Optional[Any] = Field(
        None,
        description="the database software image used for upgrading database.",
    )
    target_db_home_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Database Home.",
    )
    target_db_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Database version. For a list of supported versions, use the ListDbVersions operation. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, openMode, permissionLevel, dbWorkload, privateEndpointLabel, nsgIds, isRefreshable, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier.",
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time when the database upgrade ended.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_started of this DatabaseUpgradeHistoryEntry. The date and time when the database upgrade started.",
    )


def map_databaseupgradehistoryentry(
    o: oci.database.models.DatabaseUpgradeHistoryEntry,
) -> DatabaseUpgradeHistoryEntry | None:
    """Map oci.database.models.DatabaseUpgradeHistoryEntry → DatabaseUpgradeHistoryEntry Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DatabaseUpgradeHistoryEntry(**data)
    except Exception:
        return DatabaseUpgradeHistoryEntry(
            action=getattr(o, "action", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            options=getattr(o, "options", None),
            source=getattr(o, "source", None),
            source_db_home_id=getattr(o, "source_db_home_id", None),
            target_database_software_image_id=getattr(
                o, "target_database_software_image_id", None
            ),
            target_db_home_id=getattr(o, "target_db_home_id", None),
            target_db_version=getattr(o, "target_db_version", None),
            time_ended=getattr(o, "time_ended", None),
            time_started=getattr(o, "time_started", None),
        )


class DbHome(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbHome."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this DbHome. The `OCID`__ of the compartment.",
    )
    database_software_image_id: Optional[Any] = Field(
        None,
        description="The database software image `OCID`__",
    )
    db_home_location: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_home_location of this DbHome. The location of the Oracle Database Home.",
    )
    db_system_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the DB system.",
    )
    db_version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_version of this DbHome. The Oracle Database version.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this DbHome. The user-provided name for the Database Home. The name does not need to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DbHome. The `OCID`__ of the Database Home.",
    )
    is_unified_auditing_enabled: Optional[Any] = Field(
        None,
        description="Indicates whether unified autiding is enabled or not.",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    last_patch_history_entry_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last patch history. This value is updated as soon as a patch operation is started.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DbHome. The current state of the Database Home. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    one_off_patches: Optional[Any] = Field(
        None,
        description="List of one-off patches for Database Homes.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Database Home was created.",
    )
    vm_cluster_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the VM cluster.",
    )


def map_dbhome(o: oci.database.models.DbHome) -> DbHome | None:
    """Map oci.database.models.DbHome → DbHome Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbHome(**data)
    except Exception:
        return DbHome(
            compartment_id=getattr(o, "compartment_id", None),
            database_software_image_id=getattr(o, "database_software_image_id", None),
            db_home_location=getattr(o, "db_home_location", None),
            db_system_id=getattr(o, "db_system_id", None),
            db_version=getattr(o, "db_version", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_unified_auditing_enabled=getattr(o, "is_unified_auditing_enabled", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            last_patch_history_entry_id=getattr(o, "last_patch_history_entry_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            one_off_patches=getattr(o, "one_off_patches", None),
            time_created=getattr(o, "time_created", None),
            vm_cluster_id=getattr(o, "vm_cluster_id", None),
        )


class Patch(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.Patch."""

    available_actions: Optional[Any] = Field(
        None,
        description="Actions that can possibly be performed using this patch. Allowed values for items in this list are: \"APPLY\", \"PRECHECK\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    description: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the description of this Patch. The text describing this patch package.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this Patch. The `OCID`__ of the patch.",
    )
    last_action: Optional[Any] = Field(
        None,
        description="Action that is currently being performed or was completed last. Allowed values for this property are: \"APPLY\", \"PRECHECK\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="A descriptive text associated with the lifecycleState. Typically can contain additional displayable text.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the patch as a result of lastAction. Allowed values for this property are: "AVAILABLE", "SUCCESS", "IN_PROGRESS", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_released: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_released of this Patch. The date and time that the patch was released.",
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this Patch. The version of this patch package.",
    )


def map_patch(o: oci.database.models.Patch) -> Patch | None:
    """Map oci.database.models.Patch → Patch Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return Patch(**data)
    except Exception:
        return Patch(
            available_actions=getattr(o, "available_actions", None),
            description=getattr(o, "description", None),
            id=getattr(o, "id", None),
            last_action=getattr(o, "last_action", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_released=getattr(o, "time_released", None),
            version=getattr(o, "version", None),
        )


class PatchHistoryEntry(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.PatchHistoryEntry."""

    action: Optional[Any] = Field(
        None,
        description="The action being performed or was completed. Allowed values for this property are: \"APPLY\", \"PRECHECK\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this PatchHistoryEntry. The `OCID`__ of the patch history entry.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="A descriptive text associated with the lifecycleState. Typically contains additional displayable text.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this PatchHistoryEntry. The current state of the action. Allowed values for this property are: "IN_PROGRESS", "SUCCEEDED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    patch_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the patch_id of this PatchHistoryEntry. The `OCID`__ of the patch.",
    )
    patch_type: Optional[Any] = Field(
        None,
        description='The type of Patch operation. Allowed values for this property are: "OS", "DB", "GI", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time when the patch action completed",
    )
    time_started: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_started of this PatchHistoryEntry. The date and time when the patch action started.",
    )


def map_patchhistoryentry(
    o: oci.database.models.PatchHistoryEntry,
) -> PatchHistoryEntry | None:
    """Map oci.database.models.PatchHistoryEntry → PatchHistoryEntry Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return PatchHistoryEntry(**data)
    except Exception:
        return PatchHistoryEntry(
            action=getattr(o, "action", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            patch_id=getattr(o, "patch_id", None),
            patch_type=getattr(o, "patch_type", None),
            time_ended=getattr(o, "time_ended", None),
            time_started=getattr(o, "time_started", None),
        )


class DbNode(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbNode."""

    additional_details: Optional[Any] = Field(
        None,
        description="Additional information about the planned maintenance.",
    )
    backup_ip_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the backup IP address associated with the database node. Use this OCID with either the :func:`get_private_ip` or the :func:`get_public_ip_by_private_ip_id` API to get the IP address needed to make a database connection. **Note:** Applies only to Exadata Cloud Service.",
    )
    backup_vnic2_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the second backup VNIC. **Note:** Applies only to Exadata Cloud Service.",
    )
    backup_vnic_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the backup VNIC.",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="The number of CPU cores enabled on the Db node.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The allocated local node storage in GBs on the Db node.",
    )
    db_server_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Exacc Db server associated with the database node.",
    )
    db_system_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_system_id of this DbNode. The `OCID`__ of the DB system.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    fault_domain: Optional[Any] = Field(
        None,
        description="The name of the Fault Domain the instance is contained in.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    host_ip_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the host IP address associated with the database node. Use this OCID with either the :func:`get_private_ip` or the :func:`get_public_ip_by_private_ip_id` API to get the IP address needed to make a database connection. **Note:** Applies only to Exadata Cloud Service.",
    )
    hostname: Optional[Any] = Field(
        None,
        description="The host name for the database node.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DbNode. The `OCID`__ of the database node.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DbNode. The current state of the database node. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "STOPPING", "STOPPED", "STARTING", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_type: Optional[Any] = Field(
        None,
        description="The type of database node maintenance. Allowed values for this property are: \"VMDB_REBOOT_MIGRATION\", \"EXADBXS_REBOOT_MIGRATION\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The allocated memory in GBs on the Db node.",
    )
    software_storage_size_in_gb: Optional[Any] = Field(
        None,
        description="The size (in GB) of the block storage volume allocation for the DB system. This attribute applies only for virtual machine DB systems.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this DbNode. The date and time that the database node was created.",
    )
    time_maintenance_window_end: Optional[Any] = Field(
        None,
        description="End date and time of maintenance window.",
    )
    time_maintenance_window_start: Optional[Any] = Field(
        None,
        description="Start date and time of maintenance window.",
    )
    total_cpu_core_count: Optional[Any] = Field(
        None,
        description="The total number of CPU cores reserved on the Db node.",
    )
    vnic2_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the second VNIC. **Note:** Applies only to Exadata Cloud Service.",
    )
    vnic_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the vnic_id of this DbNode. The `OCID`__ of the VNIC.",
    )


def map_dbnode(o: oci.database.models.DbNode) -> DbNode | None:
    """Map oci.database.models.DbNode → DbNode Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbNode(**data)
    except Exception:
        return DbNode(
            additional_details=getattr(o, "additional_details", None),
            backup_ip_id=getattr(o, "backup_ip_id", None),
            backup_vnic2_id=getattr(o, "backup_vnic2_id", None),
            backup_vnic_id=getattr(o, "backup_vnic_id", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_server_id=getattr(o, "db_server_id", None),
            db_system_id=getattr(o, "db_system_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            fault_domain=getattr(o, "fault_domain", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            host_ip_id=getattr(o, "host_ip_id", None),
            hostname=getattr(o, "hostname", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_type=getattr(o, "maintenance_type", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            software_storage_size_in_gb=getattr(o, "software_storage_size_in_gb", None),
            time_created=getattr(o, "time_created", None),
            time_maintenance_window_end=getattr(o, "time_maintenance_window_end", None),
            time_maintenance_window_start=getattr(
                o, "time_maintenance_window_start", None
            ),
            total_cpu_core_count=getattr(o, "total_cpu_core_count", None),
            vnic2_id=getattr(o, "vnic2_id", None),
            vnic_id=getattr(o, "vnic_id", None),
        )


class DbServer(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbServer."""

    autonomous_virtual_machine_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ of the Autonomous Virtual Machines associated with the Db server.",
    )
    autonomous_vm_cluster_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ of the Autonomous VM Clusters associated with the Db server.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="The number of CPU cores enabled on the Db server.",
    )
    db_node_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Db nodes associated with the Db server.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The allocated local node storage in GBs on the Db server.",
    )
    db_server_patching_details: Optional[Any] = Field(
        None,
        description="",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the Db server. The name does not need to be unique.",
    )
    exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Exadata infrastructure.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Db server.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the Db server. Allowed values for this property are: "CREATING", "AVAILABLE", "UNAVAILABLE", "DELETING", "DELETED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    max_cpu_count: Optional[Any] = Field(
        None,
        description="The total number of CPU cores available.",
    )
    max_db_node_storage_in_gbs: Optional[Any] = Field(
        None,
        description="The total local node storage available in GBs.",
    )
    max_memory_in_gbs: Optional[Any] = Field(
        None,
        description="The total memory available in GBs.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The allocated memory in GBs on the Db server.",
    )
    shape: Optional[Any] = Field(
        None,
        description="The shape of the Db server. The shape determines the amount of CPU, storage, and memory resources available.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the Db Server was created.",
    )
    vm_cluster_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the VM Clusters associated with the Db server.",
    )


def map_dbserver(o: oci.database.models.DbServer) -> DbServer | None:
    """Map oci.database.models.DbServer → DbServer Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbServer(**data)
    except Exception:
        return DbServer(
            autonomous_virtual_machine_ids=getattr(
                o, "autonomous_virtual_machine_ids", None
            ),
            autonomous_vm_cluster_ids=getattr(o, "autonomous_vm_cluster_ids", None),
            compartment_id=getattr(o, "compartment_id", None),
            compute_model=getattr(o, "compute_model", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            db_node_ids=getattr(o, "db_node_ids", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_server_patching_details=getattr(o, "db_server_patching_details", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            exadata_infrastructure_id=getattr(o, "exadata_infrastructure_id", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            max_cpu_count=getattr(o, "max_cpu_count", None),
            max_db_node_storage_in_gbs=getattr(o, "max_db_node_storage_in_gbs", None),
            max_memory_in_gbs=getattr(o, "max_memory_in_gbs", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            shape=getattr(o, "shape", None),
            time_created=getattr(o, "time_created", None),
            vm_cluster_ids=getattr(o, "vm_cluster_ids", None),
        )


class DbSystem(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbSystem."""

    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this DbSystem. The name of the availability domain that the DB system is located in.",
    )
    backup_network_nsg_ids: Optional[Any] = Field(
        None,
        description="A list of the `OCIDs`__ of the network security groups (NSGs) that the backup network of this DB system belongs to. Setting this to an empty array after the list is created removes the resource from all NSGs. For more information about NSGs, see `Security Rules`__. Applicable only to Exadata systems.",
    )
    backup_subnet_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the backup network subnet the DB system is associated with. Applicable only to Exadata DB systems. **Subnet Restriction:** See the subnet restrictions information for **subnetId**.",
    )
    cluster_name: Optional[Any] = Field(
        None,
        description="The cluster name for Exadata and 2-node RAC virtual machine DB systems. The cluster name must begin with an alphabetic character, and may contain hyphens (-). Underscores (_) are not permitted. The cluster name can be no longer than 11 characters and is not case sensitive.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this DbSystem. The `OCID`__ of the compartment.",
    )
    cpu_core_count: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cpu_core_count of this DbSystem. The number of CPU cores enabled on the DB system.",
    )
    data_collection_options: Optional[Any] = Field(
        None,
        description="",
    )
    data_storage_percentage: Optional[Any] = Field(
        None,
        description="The percentage assigned to DATA storage (user data and database files). The remaining percentage is assigned to RECO storage (database redo logs, archive logs, and recovery manager backups). Accepted values are 40 and 80. The default is 80 percent assigned to DATA storage. Not applicable for virtual machine DB systems.",
    )
    data_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The data storage size, in gigabytes, that is currently available to the DB system. Applies only for virtual machine DB systems.",
    )
    database_edition: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the database_edition of this DbSystem. The Oracle Database edition that applies to all the databases on the DB system. Allowed values for this property are: "STANDARD_EDITION", "ENTERPRISE_EDITION", "ENTERPRISE_EDITION_HIGH_PERFORMANCE", "ENTERPRISE_EDITION_EXTREME_PERFORMANCE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    db_system_options: Optional[Any] = Field(
        None,
        description="",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    disk_redundancy: Optional[Any] = Field(
        None,
        description="The type of redundancy configured for the DB system. NORMAL is 2-way redundancy. HIGH is 3-way redundancy. Allowed values for this property are: \"HIGH\", \"NORMAL\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this DbSystem. The user-friendly name for the DB system. The name does not have to be unique.",
    )
    domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the domain of this DbSystem. The domain name for the DB system.",
    )
    fault_domains: Optional[Any] = Field(
        None,
        description="List of the Fault Domains in which this DB system is provisioned.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    gi_software_image_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of a grid infrastructure software image. This is a database software image of the type `GRID_IMAGE`.",
    )
    hostname: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the hostname of this DbSystem. The hostname for the DB system.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DbSystem. The `OCID`__ of the DB system.",
    )
    iorm_config_cache: Optional[Any] = Field(
        None,
        description="",
    )
    kms_key_id: Optional[Any] = Field(
        None,
        description="The OCID of the key container that is used as the master encryption key in database transparent data encryption (TDE) operations.",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    last_patch_history_entry_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last patch history. This value is updated as soon as a patch operation starts.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to all the databases on the DB system. The default is LICENSE_INCLUDED. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DbSystem. The current state of the DB system. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MIGRATED", "MAINTENANCE_IN_PROGRESS", "NEEDS_ATTENTION", "UPGRADING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    listener_port: Optional[Any] = Field(
        None,
        description="The port number configured for the listener on the DB system.",
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="Memory allocated to the DB system, in gigabytes.",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    node_count: Optional[Any] = Field(
        None,
        description="The number of nodes in the DB system. For RAC DB systems, the value is greater than 1.",
    )
    nsg_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ for the network security groups (NSGs) to which this resource belongs. Setting this to an empty list removes all resources from all NSGs. For more information about NSGs, see `Security Rules`__. **NsgIds restrictions:** - A network security group (NSG) is optional for Autonomous Databases with private access. The nsgIds list can be empty.",
    )
    os_version: Optional[Any] = Field(
        None,
        description="The most recent OS Patch Version applied on the DB system.",
    )
    point_in_time_data_disk_clone_timestamp: Optional[Any] = Field(
        None,
        description="The point in time for a cloned database system when the data disks were cloned from the source database system, as described in `RFC 3339`__.",
    )
    reco_storage_size_in_gb: Optional[Any] = Field(
        None,
        description="The RECO/REDO storage size, in gigabytes, that is currently allocated to the DB system. Applies only for virtual machine DB systems.",
    )
    scan_dns_name: Optional[Any] = Field(
        None,
        description="The FQDN of the DNS record for the SCAN IP addresses that are associated with the DB system.",
    )
    scan_dns_record_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the DNS record for the SCAN IP addresses that are associated with the DB system.",
    )
    scan_ip_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Single Client Access Name (SCAN) IPv4 addresses associated with the DB system. SCAN IPv4 addresses are typically used for load balancing and are not assigned to any interface. Oracle Clusterware directs the requests to the appropriate nodes in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    scan_ipv6_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Single Client Access Name (SCAN) IPv6 addresses associated with the DB system. SCAN IPv6 addresses are typically used for load balancing and are not assigned to any interface. Oracle Clusterware directs the requests to the appropriate nodes in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    security_attributes: Optional[Any] = Field(
        None,
        description='Security Attributes for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. Example: `{"Oracle-ZPR": {"MaxEgressCount": {"value": "42", "mode": "audit"}}}`',
    )
    shape: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the shape of this DbSystem. The shape of the DB system. The shape determines resources to allocate to the DB system. - For virtual machine shapes, the number of CPU cores and memory - For bare metal and Exadata shapes, the number of CPU cores, storage, and memory",
    )
    source_db_system_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the DB system.",
    )
    sparse_diskgroup: Optional[Any] = Field(
        None,
        description="True, if Sparse Diskgroup is configured for Exadata dbsystem, False, if Sparse diskgroup was not configured.",
    )
    ssh_public_keys: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the ssh_public_keys of this DbSystem. The public key portion of one or more key pairs used for SSH access to the DB system.",
    )
    storage_volume_performance_mode: Optional[Any] = Field(
        None,
        description="The block storage volume performance level. Valid values are `BALANCED` and `HIGH_PERFORMANCE`. See `Block Volume Performance`__ for more information. Allowed values for this property are: \"BALANCED\", \"HIGH_PERFORMANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the subnet_id of this DbSystem. The `OCID`__ of the subnet the DB system is associated with. **Subnet Restrictions:** - For bare metal DB systems and for single node virtual machine DB systems, do not use a subnet that overlaps with 192.168.16.16/28. - For Exadata and virtual machine 2-node RAC DB systems, do not use a subnet that overlaps with 192.168.128.0/20. These subnets are used by the Oracle Clusterware private interconnect on the database instance. Specifying an overlapping subnet will cause the private interconnect to malfunction. This restriction applies to both the client subnet and backup subnet.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the DB system was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the DB system. For details, see `DB System Time Zones`__.",
    )
    version: Optional[Any] = Field(
        None,
        description="The Oracle Database version of the DB system.",
    )
    vip_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the virtual IPv4 (VIP) addresses associated with the DB system. The Cluster Ready Services (CRS) creates and maintains one VIPv4 address for each node in the DB system to enable failover. If one node fails, the VIPv4 is reassigned to another active node in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    vipv6_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the virtual IPv6 (VIP) addresses associated with the DB system. The Cluster Ready Services (CRS) creates and maintains one VIP IpV6 address for each node in the DB system to enable failover. If one node fails, the VIP is reassigned to another active node in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    zone_id: Optional[Any] = Field(
        None,
        description="The OCID of the zone the DB system is associated with.",
    )


def map_dbsystem(o: oci.database.models.DbSystem) -> DbSystem | None:
    """Map oci.database.models.DbSystem → DbSystem Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbSystem(**data)
    except Exception:
        return DbSystem(
            availability_domain=getattr(o, "availability_domain", None),
            backup_network_nsg_ids=getattr(o, "backup_network_nsg_ids", None),
            backup_subnet_id=getattr(o, "backup_subnet_id", None),
            cluster_name=getattr(o, "cluster_name", None),
            compartment_id=getattr(o, "compartment_id", None),
            cpu_core_count=getattr(o, "cpu_core_count", None),
            data_collection_options=getattr(o, "data_collection_options", None),
            data_storage_percentage=getattr(o, "data_storage_percentage", None),
            data_storage_size_in_gbs=getattr(o, "data_storage_size_in_gbs", None),
            database_edition=getattr(o, "database_edition", None),
            db_system_options=getattr(o, "db_system_options", None),
            defined_tags=getattr(o, "defined_tags", None),
            disk_redundancy=getattr(o, "disk_redundancy", None),
            display_name=getattr(o, "display_name", None),
            domain=getattr(o, "domain", None),
            fault_domains=getattr(o, "fault_domains", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            gi_software_image_id=getattr(o, "gi_software_image_id", None),
            hostname=getattr(o, "hostname", None),
            id=getattr(o, "id", None),
            iorm_config_cache=getattr(o, "iorm_config_cache", None),
            kms_key_id=getattr(o, "kms_key_id", None),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            last_patch_history_entry_id=getattr(o, "last_patch_history_entry_id", None),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            listener_port=getattr(o, "listener_port", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            node_count=getattr(o, "node_count", None),
            nsg_ids=getattr(o, "nsg_ids", None),
            os_version=getattr(o, "os_version", None),
            point_in_time_data_disk_clone_timestamp=getattr(
                o, "point_in_time_data_disk_clone_timestamp", None
            ),
            reco_storage_size_in_gb=getattr(o, "reco_storage_size_in_gb", None),
            scan_dns_name=getattr(o, "scan_dns_name", None),
            scan_dns_record_id=getattr(o, "scan_dns_record_id", None),
            scan_ip_ids=getattr(o, "scan_ip_ids", None),
            scan_ipv6_ids=getattr(o, "scan_ipv6_ids", None),
            security_attributes=getattr(o, "security_attributes", None),
            shape=getattr(o, "shape", None),
            source_db_system_id=getattr(o, "source_db_system_id", None),
            sparse_diskgroup=getattr(o, "sparse_diskgroup", None),
            ssh_public_keys=getattr(o, "ssh_public_keys", None),
            storage_volume_performance_mode=getattr(
                o, "storage_volume_performance_mode", None
            ),
            subnet_id=getattr(o, "subnet_id", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
            version=getattr(o, "version", None),
            vip_ids=getattr(o, "vip_ids", None),
            vipv6_ids=getattr(o, "vipv6_ids", None),
            zone_id=getattr(o, "zone_id", None),
        )


class DbSystemUpgradeHistoryEntry(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.DbSystemUpgradeHistoryEntry."""

    action: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the action of this DbSystemUpgradeHistoryEntry. The operating system upgrade action. Allowed values for this property are: "PRECHECK", "ROLLBACK", "UPDATE_SNAPSHOT_RETENTION_DAYS", "UPGRADE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this DbSystemUpgradeHistoryEntry. The `OCID`__ of the upgrade history entry.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="A descriptive text associated with the lifecycleState. Typically contains additional displayable text.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this DbSystemUpgradeHistoryEntry. The current state of the action. Allowed values for this property are: "IN_PROGRESS", "SUCCEEDED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    new_gi_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Grid Infrastructure (GI) software version.",
    )
    new_os_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Software (OS) version eg. Oracle Linux Server release 8",
    )
    old_gi_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Grid Infrastructure (GI) software version.",
    )
    old_os_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Software (OS) version eg. Oracle Linux Server release 8",
    )
    snapshot_retention_period_in_days: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the snapshot_retention_period_in_days of this DbSystemUpgradeHistoryEntry. The retention period, in days, for the snapshot that allows you to perform a rollback of the upgrade operation. After this number of days passes, you cannot roll back the upgrade.",
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time when the upgrade action completed",
    )
    time_started: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_started of this DbSystemUpgradeHistoryEntry. The date and time when the upgrade action started.",
    )


def map_dbsystemupgradehistoryentry(
    o: oci.database.models.DbSystemUpgradeHistoryEntry,
) -> DbSystemUpgradeHistoryEntry | None:
    """Map oci.database.models.DbSystemUpgradeHistoryEntry → DbSystemUpgradeHistoryEntry Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return DbSystemUpgradeHistoryEntry(**data)
    except Exception:
        return DbSystemUpgradeHistoryEntry(
            action=getattr(o, "action", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            new_gi_version=getattr(o, "new_gi_version", None),
            new_os_version=getattr(o, "new_os_version", None),
            old_gi_version=getattr(o, "old_gi_version", None),
            old_os_version=getattr(o, "old_os_version", None),
            snapshot_retention_period_in_days=getattr(
                o, "snapshot_retention_period_in_days", None
            ),
            time_ended=getattr(o, "time_ended", None),
            time_started=getattr(o, "time_started", None),
        )


class ExadataInfrastructure(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExadataInfrastructure."""

    activated_storage_count: Optional[Any] = Field(
        None,
        description="The requested number of additional storage servers activated for the Exadata infrastructure.",
    )
    additional_compute_count: Optional[Any] = Field(
        None,
        description="The requested number of additional compute servers for the Exadata infrastructure.",
    )
    additional_compute_system_model: Optional[Any] = Field(
        None,
        description='Oracle Exadata System Model specification. The system model determines the amount of compute or storage server resources available for use. For more information, please see [System and Shape Configuration Options] ( Allowed values for this property are: "X7", "X8", "X8M", "X9M", "X10M", "X11M", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    additional_storage_count: Optional[Any] = Field(
        None,
        description="The requested number of additional storage servers for the Exadata infrastructure.",
    )
    admin_network_cidr: Optional[Any] = Field(
        None,
        description="The CIDR block for the Exadata administration network.",
    )
    availability_domain: Optional[Any] = Field(
        None,
        description="The name of the availability domain that the Exadata infrastructure is located in.",
    )
    cloud_control_plane_server1: Optional[Any] = Field(
        None,
        description="The IP address for the first control plane server.",
    )
    cloud_control_plane_server2: Optional[Any] = Field(
        None,
        description="The IP address for the second control plane server.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExadataInfrastructure. The `OCID`__ of the compartment.",
    )
    compute_count: Optional[Any] = Field(
        None,
        description="The number of compute servers for the Exadata infrastructure.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    contacts: Optional[Any] = Field(
        None,
        description="The list of contacts for the Exadata infrastructure.",
    )
    corporate_proxy: Optional[Any] = Field(
        None,
        description="The corporate network proxy for access to the control plane network.",
    )
    cpus_enabled: Optional[Any] = Field(
        None,
        description="The number of enabled CPU cores.",
    )
    csi_number: Optional[Any] = Field(
        None,
        description="The CSI Number of the Exadata infrastructure.",
    )
    data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="Size, in terabytes, of the DATA disk group.",
    )
    database_server_type: Optional[Any] = Field(
        None,
        description="The database server type of the Exadata infrastructure.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage allocated in GBs.",
    )
    db_server_version: Optional[Any] = Field(
        None,
        description="The software version of the database servers (dom0) in the Exadata infrastructure.",
    )
    defined_file_system_configurations: Optional[Any] = Field(
        None,
        description="Details of the file system configuration of the Exadata infrastructure.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExadataInfrastructure. The user-friendly name for the Exadata Cloud@Customer infrastructure. The name does not need to be unique.",
    )
    dns_server: Optional[Any] = Field(
        None,
        description="The list of DNS server IP addresses. Maximum of 3 allowed.",
    )
    exascale_config: Optional[Any] = Field(
        None,
        description="",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    gateway: Optional[Any] = Field(
        None,
        description="The gateway for the control plane network.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExadataInfrastructure. The `OCID`__ of the Exadata infrastructure.",
    )
    infini_band_network_cidr: Optional[Any] = Field(
        None,
        description="The CIDR block for the Exadata InfiniBand interconnect.",
    )
    is_cps_offline_report_enabled: Optional[Any] = Field(
        None,
        description="Indicates whether cps offline diagnostic report is enabled for this Exadata infrastructure. This will allow a customer to quickly check status themselves and fix problems on their end, saving time and frustration for both Oracle and the customer when they find the CPS in a disconnected state.You can enable offline diagnostic report during Exadata infrastructure provisioning. You can also disable or enable it at any time using the UpdateExadatainfrastructure API.",
    )
    is_multi_rack_deployment: Optional[Any] = Field(
        None,
        description="Indicates if deployment is Multi-Rack or not.",
    )
    is_scheduling_policy_associated: Optional[Any] = Field(
        None,
        description="If true, the infrastructure is using granular maintenance scheduling preference.",
    )
    last_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance run.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExadataInfrastructure. The current lifecycle state of the Exadata infrastructure. Allowed values for this property are: "CREATING", "REQUIRES_ACTIVATION", "ACTIVATING", "ACTIVE", "ACTIVATION_FAILED", "FAILED", "UPDATING", "DELETING", "DELETED", "DISCONNECTED", "MAINTENANCE_IN_PROGRESS", "WAITING_FOR_CONNECTIVITY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_slo_status: Optional[Any] = Field(
        None,
        description="A field to capture ‘Maintenance SLO Status’ for the Exadata infrastructure with values ‘OK’, ‘DEGRADED’. Default is ‘OK’ when the infrastructure is provisioned. Allowed values for this property are: \"OK\", \"DEGRADED\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    maintenance_window: Optional[Any] = Field(
        None,
        description="",
    )
    max_cpu_count: Optional[Any] = Field(
        None,
        description="The total number of CPU cores available.",
    )
    max_data_storage_in_t_bs: Optional[float] = Field(
        None,
        description="The total available DATA disk group size.",
    )
    max_db_node_storage_in_g_bs: Optional[Any] = Field(
        None,
        description="The total local node storage available in GBs.",
    )
    max_memory_in_gbs: Optional[Any] = Field(
        None,
        description="The total memory available in GBs.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory allocated in GBs.",
    )
    monthly_db_server_version: Optional[Any] = Field(
        None,
        description="The monthly software version of the database servers (dom0) in the Exadata infrastructure.",
    )
    multi_rack_configuration_file: Optional[Any] = Field(
        None,
        description="The base64 encoded Multi-Rack configuration json file.",
    )
    netmask: Optional[Any] = Field(
        None,
        description="The netmask for the control plane network.",
    )
    network_bonding_mode_details: Optional[Any] = Field(
        None,
        description="",
    )
    next_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the next maintenance run.",
    )
    ntp_server: Optional[Any] = Field(
        None,
        description="The list of NTP server IP addresses. Maximum of 3 allowed.",
    )
    rack_serial_number: Optional[Any] = Field(
        None,
        description="The serial number for the Exadata infrastructure.",
    )
    shape: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the shape of this ExadataInfrastructure. The shape of the Exadata infrastructure. The shape determines the amount of CPU, storage, and memory resources allocated to the instance.",
    )
    storage_count: Optional[Any] = Field(
        None,
        description="The number of Exadata storage servers for the Exadata infrastructure.",
    )
    storage_server_type: Optional[Any] = Field(
        None,
        description="The storage server type of the Exadata infrastructure.",
    )
    storage_server_version: Optional[Any] = Field(
        None,
        description="The software version of the storage servers (cells) in the Exadata infrastructure.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Exadata infrastructure was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the Exadata infrastructure. For details, see `Exadata Infrastructure Time Zones`__.",
    )


def map_exadatainfrastructure(
    o: oci.database.models.ExadataInfrastructure,
) -> ExadataInfrastructure | None:
    """Map oci.database.models.ExadataInfrastructure → ExadataInfrastructure Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExadataInfrastructure(**data)
    except Exception:
        return ExadataInfrastructure(
            activated_storage_count=getattr(o, "activated_storage_count", None),
            additional_compute_count=getattr(o, "additional_compute_count", None),
            additional_compute_system_model=getattr(
                o, "additional_compute_system_model", None
            ),
            additional_storage_count=getattr(o, "additional_storage_count", None),
            admin_network_cidr=getattr(o, "admin_network_cidr", None),
            availability_domain=getattr(o, "availability_domain", None),
            cloud_control_plane_server1=getattr(o, "cloud_control_plane_server1", None),
            cloud_control_plane_server2=getattr(o, "cloud_control_plane_server2", None),
            compartment_id=getattr(o, "compartment_id", None),
            compute_count=getattr(o, "compute_count", None),
            compute_model=getattr(o, "compute_model", None),
            contacts=getattr(o, "contacts", None),
            corporate_proxy=getattr(o, "corporate_proxy", None),
            cpus_enabled=getattr(o, "cpus_enabled", None),
            csi_number=getattr(o, "csi_number", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            database_server_type=getattr(o, "database_server_type", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_server_version=getattr(o, "db_server_version", None),
            defined_file_system_configurations=getattr(
                o, "defined_file_system_configurations", None
            ),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            dns_server=getattr(o, "dns_server", None),
            exascale_config=getattr(o, "exascale_config", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            gateway=getattr(o, "gateway", None),
            id=getattr(o, "id", None),
            infini_band_network_cidr=getattr(o, "infini_band_network_cidr", None),
            is_cps_offline_report_enabled=getattr(
                o, "is_cps_offline_report_enabled", None
            ),
            is_multi_rack_deployment=getattr(o, "is_multi_rack_deployment", None),
            is_scheduling_policy_associated=getattr(
                o, "is_scheduling_policy_associated", None
            ),
            last_maintenance_run_id=getattr(o, "last_maintenance_run_id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_slo_status=getattr(o, "maintenance_slo_status", None),
            maintenance_window=getattr(o, "maintenance_window", None),
            max_cpu_count=getattr(o, "max_cpu_count", None),
            max_data_storage_in_t_bs=getattr(o, "max_data_storage_in_t_bs", None),
            max_db_node_storage_in_g_bs=getattr(o, "max_db_node_storage_in_g_bs", None),
            max_memory_in_gbs=getattr(o, "max_memory_in_gbs", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            monthly_db_server_version=getattr(o, "monthly_db_server_version", None),
            multi_rack_configuration_file=getattr(
                o, "multi_rack_configuration_file", None
            ),
            netmask=getattr(o, "netmask", None),
            network_bonding_mode_details=getattr(
                o, "network_bonding_mode_details", None
            ),
            next_maintenance_run_id=getattr(o, "next_maintenance_run_id", None),
            ntp_server=getattr(o, "ntp_server", None),
            rack_serial_number=getattr(o, "rack_serial_number", None),
            shape=getattr(o, "shape", None),
            storage_count=getattr(o, "storage_count", None),
            storage_server_type=getattr(o, "storage_server_type", None),
            storage_server_version=getattr(o, "storage_server_version", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
        )


class OCPUs(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.OCPUs."""

    by_workload_type: Optional[Any] = Field(
        None,
        description="",
    )
    consumed_cpu: Optional[float] = Field(
        None,
        description="The total number of consumed OCPUs in the Autonomous Exadata Infrastructure instance.",
    )
    total_cpu: Optional[float] = Field(
        None,
        description="The total number of OCPUs in the Autonomous Exadata Infrastructure instance.",
    )


def map_ocpus(o: oci.database.models.OCPUs) -> OCPUs | None:
    """Map oci.database.models.OCPUs → OCPUs Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return OCPUs(**data)
    except Exception:
        return OCPUs(
            by_workload_type=getattr(o, "by_workload_type", None),
            consumed_cpu=getattr(o, "consumed_cpu", None),
            total_cpu=getattr(o, "total_cpu", None),
        )


class ExadataInfrastructureUnAllocatedResources(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExadataInfrastructureUnAllocatedResources."""

    autonomous_vm_clusters: Optional[Any] = Field(
        None,
        description="The list of Autonomous VM Clusters on the Infra and their associated unallocated resources details",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExadataInfrastructureUnAllocatedResources. The user-friendly name for the Exadata Cloud@Customer infrastructure. The name does not need to be unique.",
    )
    exadata_storage_in_tbs: Optional[float] = Field(
        None,
        description="Total unallocated exadata storage in the infrastructure in TBs.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExadataInfrastructureUnAllocatedResources. The `OCID`__ of the Exadata infrastructure.",
    )
    local_storage_in_gbs: Optional[Any] = Field(
        None,
        description="The minimum amount of un allocated storage that is available across all nodes in the infrastructure.",
    )
    memory_in_gbs: Optional[Any] = Field(
        None,
        description="The minimum amount of un allocated memory that is available across all nodes in the infrastructure.",
    )
    ocpus: Optional[Any] = Field(
        None,
        description="The minimum amount of un allocated ocpus that is available across all nodes in the infrastructure.",
    )


def map_exadatainfrastructureunallocatedresources(
    o: oci.database.models.ExadataInfrastructureUnAllocatedResources,
) -> ExadataInfrastructureUnAllocatedResources | None:
    """Map oci.database.models.ExadataInfrastructureUnAllocatedResources → ExadataInfrastructureUnAllocatedResources Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExadataInfrastructureUnAllocatedResources(**data)
    except Exception:
        return ExadataInfrastructureUnAllocatedResources(
            autonomous_vm_clusters=getattr(o, "autonomous_vm_clusters", None),
            display_name=getattr(o, "display_name", None),
            exadata_storage_in_tbs=getattr(o, "exadata_storage_in_tbs", None),
            id=getattr(o, "id", None),
            local_storage_in_gbs=getattr(o, "local_storage_in_gbs", None),
            memory_in_gbs=getattr(o, "memory_in_gbs", None),
            ocpus=getattr(o, "ocpus", None),
        )


class ExadbVmCluster(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExadbVmCluster."""

    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this ExadbVmCluster. The name of the availability domain in which the Exadata VM cluster on Exascale Infrastructure is located.",
    )
    backup_network_nsg_ids: Optional[Any] = Field(
        None,
        description="A list of the `OCIDs`__ of the network security groups (NSGs) that the backup network of this DB system belongs to. Setting this to an empty array after the list is created removes the resource from all NSGs. For more information about NSGs, see `Security Rules`__. Applicable only to Exadata systems.",
    )
    backup_subnet_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the backup_subnet_id of this ExadbVmCluster. The `OCID`__ of the backup network subnet associated with the Exadata VM cluster on Exascale Infrastructure.",
    )
    cluster_name: Optional[Any] = Field(
        None,
        description="The cluster name for Exadata VM cluster on Exascale Infrastructure. The cluster name must begin with an alphabetic character, and may contain hyphens (-). Underscores (_) are not permitted. The cluster name can be no longer than 11 characters and is not case sensitive.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExadbVmCluster. The `OCID`__ of the compartment.",
    )
    data_collection_options: Optional[Any] = Field(
        None,
        description="",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExadbVmCluster. The user-friendly name for the Exadata VM cluster on Exascale Infrastructure. The name does not need to be unique.",
    )
    domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the domain of this ExadbVmCluster. A domain name used for the Exadata VM cluster on Exascale Infrastructure. If the Oracle-provided internet and VCN resolver is enabled for the specified subnet, then the domain name for the subnet is used (do not provide one). Otherwise, provide a valid DNS domain name. Hyphens (-) are not permitted. Applies to Exadata Database Service on Exascale Infrastructure only.",
    )
    enabled_e_cpu_count: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the enabled_e_cpu_count of this ExadbVmCluster. The number of ECPUs to enable for an Exadata VM cluster on Exascale Infrastructure.",
    )
    exascale_db_storage_vault_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the exascale_db_storage_vault_id of this ExadbVmCluster. The `OCID`__ of the Exadata Database Storage Vault.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    gi_version: Optional[Any] = Field(
        None,
        description="A valid Oracle Grid Infrastructure (GI) software version.",
    )
    grid_image_id: Optional[Any] = Field(
        None,
        description="Grid Setup will be done using this grid image id. The grid image id can be extracted from 1. Obtain the supported major versions using API /20160918/giVersions?compartmentId=<compartmentId>&shape=EXADB_XS&availabilityDomain=<AD name> 2. Replace {version} with one of the supported major versions and obtain the supported minor versions using API /20160918/giVersions/{version}/minorVersions?compartmentId=<compartmentId>&shapeFamily=EXADB_XS&availabilityDomain=<AD name>",
    )
    grid_image_type: Optional[Any] = Field(
        None,
        description="The type of Grid Image Allowed values for this property are: \"RELEASE_UPDATE\", \"CUSTOM_IMAGE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    hostname: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the hostname of this ExadbVmCluster. The hostname for the Exadata VM cluster on Exascale Infrastructure. The hostname must begin with an alphabetic character, and can contain alphanumeric characters and hyphens (-). For Exadata systems, the maximum length of the hostname is 12 characters. The maximum length of the combined hostname and domain is 63 characters. **Note:** The hostname must be unique within the subnet. If it is not unique, then the Exadata VM cluster on Exascale Infrastructure will fail to provision.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExadbVmCluster. The `OCID`__ of the Exadata VM cluster on Exascale Infrastructure.",
    )
    iorm_config_cache: Optional[Any] = Field(
        None,
        description="",
    )
    last_update_history_entry_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last maintenance update history entry. This value is updated when a maintenance update starts.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to the Exadata VM cluster on Exascale Infrastructure. The default is BRING_YOUR_OWN_LICENSE. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExadbVmCluster. The current state of the Exadata VM cluster on Exascale Infrastructure. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    listener_port: Optional[Any] = Field(
        None,
        description="The port number configured for the listener on the Exadata VM cluster on Exascale Infrastructure.",
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory that you want to be allocated in GBs. Memory is calculated based on 11 GB per VM core reserved.",
    )
    node_count: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the node_count of this ExadbVmCluster. The number of nodes in the Exadata VM cluster on Exascale Infrastructure.",
    )
    nsg_ids: Optional[Any] = Field(
        None,
        description="The list of `OCIDs`__ for the network security groups (NSGs) to which this resource belongs. Setting this to an empty list removes all resources from all NSGs. For more information about NSGs, see `Security Rules`__. **NsgIds restrictions:** - A network security group (NSG) is optional for Autonomous Databases with private access. The nsgIds list can be empty.",
    )
    private_zone_id: Optional[Any] = Field(
        None,
        description="The private zone ID in which you want DNS records to be created.",
    )
    scan_dns_name: Optional[Any] = Field(
        None,
        description="The FQDN of the DNS record for the SCAN IP addresses that are associated with the Exadata VM cluster on Exascale Infrastructure.",
    )
    scan_dns_record_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the DNS record for the SCAN IP addresses that are associated with the Exadata VM cluster on Exascale Infrastructure.",
    )
    scan_ip_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Single Client Access Name (SCAN) IP addresses associated with the Exadata VM cluster on Exascale Infrastructure. SCAN IP addresses are typically used for load balancing and are not assigned to any interface. Oracle Clusterware directs the requests to the appropriate nodes in the cluster. **Note:** For a single-node DB system, this list is empty.",
    )
    scan_listener_port_tcp: Optional[Any] = Field(
        None,
        description="The TCP Single Client Access Name (SCAN) port. The default port is 1521.",
    )
    scan_listener_port_tcp_ssl: Optional[Any] = Field(
        None,
        description="The Secured Communication (TCPS) protocol Single Client Access Name (SCAN) port. The default port is 2484.",
    )
    security_attributes: Optional[Any] = Field(
        None,
        description='Security Attributes for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__. Example: `{"Oracle-ZPR": {"MaxEgressCount": {"value": "42", "mode": "audit"}}}`',
    )
    shape: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the shape of this ExadbVmCluster. The shape of the Exadata VM cluster on Exascale Infrastructure resource",
    )
    snapshot_file_system_storage: Optional[Any] = Field(
        None,
        description="",
    )
    ssh_public_keys: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the ssh_public_keys of this ExadbVmCluster. The public key portion of one or more key pairs used for SSH access to the Exadata VM cluster on Exascale Infrastructure.",
    )
    subnet_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the subnet_id of this ExadbVmCluster. The `OCID`__ of the subnet associated with the Exadata VM cluster on Exascale Infrastructure.",
    )
    system_tags: Optional[Any] = Field(
        None,
        description="System tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    system_version: Optional[Any] = Field(
        None,
        description="Operating system version of the image.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the Exadata VM cluster on Exascale Infrastructure was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone to use for the Exadata VM cluster on Exascale Infrastructure. For details, see `Time Zones`__.",
    )
    total_e_cpu_count: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the total_e_cpu_count of this ExadbVmCluster. The number of Total ECPUs for an Exadata VM cluster on Exascale Infrastructure.",
    )
    total_file_system_storage: Optional[Any] = Field(
        None,
        description="",
    )
    vip_ids: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the virtual IP (VIP) addresses associated with the Exadata VM cluster on Exascale Infrastructure. The Cluster Ready Services (CRS) creates and maintains one VIP address for each node in the Exadata Cloud Service instance to enable failover. If one node fails, then the VIP is reassigned to another active node in the cluster.",
    )
    vm_file_system_storage: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the vm_file_system_storage of this ExadbVmCluster.",
    )
    zone_id: Optional[Any] = Field(
        None,
        description="The OCID of the zone with which the Exadata VM cluster on Exascale Infrastructure is associated.",
    )


def map_exadbvmcluster(o: oci.database.models.ExadbVmCluster) -> ExadbVmCluster | None:
    """Map oci.database.models.ExadbVmCluster → ExadbVmCluster Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExadbVmCluster(**data)
    except Exception:
        return ExadbVmCluster(
            availability_domain=getattr(o, "availability_domain", None),
            backup_network_nsg_ids=getattr(o, "backup_network_nsg_ids", None),
            backup_subnet_id=getattr(o, "backup_subnet_id", None),
            cluster_name=getattr(o, "cluster_name", None),
            compartment_id=getattr(o, "compartment_id", None),
            data_collection_options=getattr(o, "data_collection_options", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            domain=getattr(o, "domain", None),
            enabled_e_cpu_count=getattr(o, "enabled_e_cpu_count", None),
            exascale_db_storage_vault_id=getattr(
                o, "exascale_db_storage_vault_id", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            gi_version=getattr(o, "gi_version", None),
            grid_image_id=getattr(o, "grid_image_id", None),
            grid_image_type=getattr(o, "grid_image_type", None),
            hostname=getattr(o, "hostname", None),
            id=getattr(o, "id", None),
            iorm_config_cache=getattr(o, "iorm_config_cache", None),
            last_update_history_entry_id=getattr(
                o, "last_update_history_entry_id", None
            ),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            listener_port=getattr(o, "listener_port", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            node_count=getattr(o, "node_count", None),
            nsg_ids=getattr(o, "nsg_ids", None),
            private_zone_id=getattr(o, "private_zone_id", None),
            scan_dns_name=getattr(o, "scan_dns_name", None),
            scan_dns_record_id=getattr(o, "scan_dns_record_id", None),
            scan_ip_ids=getattr(o, "scan_ip_ids", None),
            scan_listener_port_tcp=getattr(o, "scan_listener_port_tcp", None),
            scan_listener_port_tcp_ssl=getattr(o, "scan_listener_port_tcp_ssl", None),
            security_attributes=getattr(o, "security_attributes", None),
            shape=getattr(o, "shape", None),
            snapshot_file_system_storage=getattr(
                o, "snapshot_file_system_storage", None
            ),
            ssh_public_keys=getattr(o, "ssh_public_keys", None),
            subnet_id=getattr(o, "subnet_id", None),
            system_tags=getattr(o, "system_tags", None),
            system_version=getattr(o, "system_version", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
            total_e_cpu_count=getattr(o, "total_e_cpu_count", None),
            total_file_system_storage=getattr(o, "total_file_system_storage", None),
            vip_ids=getattr(o, "vip_ids", None),
            vm_file_system_storage=getattr(o, "vm_file_system_storage", None),
            zone_id=getattr(o, "zone_id", None),
        )


class ExadbVmClusterUpdate(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExadbVmClusterUpdate."""

    available_actions: Optional[Any] = Field(
        None,
        description='The possible actions performed by the update operation on the infrastructure components. Allowed values for items in this list are: "ROLLING_APPLY", "NON_ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    description: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the description of this ExadbVmClusterUpdate. Details of the maintenance update package.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExadbVmClusterUpdate. The `OCID`__ of the maintenance update.",
    )
    last_action: Optional[Any] = Field(
        None,
        description='The previous update action performed. Allowed values for this property are: "ROLLING_APPLY", "NON_ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Descriptive text providing additional details about the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the maintenance update. Dependent on value of `lastAction`. Allowed values for this property are: "AVAILABLE", "SUCCESS", "IN_PROGRESS", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_released: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_released of this ExadbVmClusterUpdate. The date and time the maintenance update was released.",
    )
    update_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the update_type of this ExadbVmClusterUpdate. The type of cloud VM cluster maintenance update. Allowed values for this property are: "GI_UPGRADE", "GI_PATCH", "OS_UPDATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this ExadbVmClusterUpdate. The version of the maintenance update package.",
    )


def map_exadbvmclusterupdate(
    o: oci.database.models.ExadbVmClusterUpdate,
) -> ExadbVmClusterUpdate | None:
    """Map oci.database.models.ExadbVmClusterUpdate → ExadbVmClusterUpdate Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExadbVmClusterUpdate(**data)
    except Exception:
        return ExadbVmClusterUpdate(
            available_actions=getattr(o, "available_actions", None),
            description=getattr(o, "description", None),
            id=getattr(o, "id", None),
            last_action=getattr(o, "last_action", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_released=getattr(o, "time_released", None),
            update_type=getattr(o, "update_type", None),
            version=getattr(o, "version", None),
        )


class ExadbVmClusterUpdateHistoryEntry(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExadbVmClusterUpdateHistoryEntry."""

    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExadbVmClusterUpdateHistoryEntry. The `OCID`__ of the maintenance update history entry.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Descriptive text providing additional details about the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExadbVmClusterUpdateHistoryEntry. The current lifecycle state of the maintenance update operation. Allowed values for this property are: "IN_PROGRESS", "SUCCEEDED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_completed: Optional[Any] = Field(
        None,
        description="The date and time when the maintenance update action completed.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_started of this ExadbVmClusterUpdateHistoryEntry. The date and time when the maintenance update action started.",
    )
    update_action: Optional[Any] = Field(
        None,
        description='The update action. Allowed values for this property are: "ROLLING_APPLY", "NON_ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    update_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the update_id of this ExadbVmClusterUpdateHistoryEntry. The `OCID`__ of the maintenance update.",
    )
    update_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the update_type of this ExadbVmClusterUpdateHistoryEntry. The type of cloud VM cluster maintenance update. Allowed values for this property are: "GI_UPGRADE", "GI_PATCH", "OS_UPDATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    version: Optional[Any] = Field(
        None,
        description="The version of the maintenance update package.",
    )


def map_exadbvmclusterupdatehistoryentry(
    o: oci.database.models.ExadbVmClusterUpdateHistoryEntry,
) -> ExadbVmClusterUpdateHistoryEntry | None:
    """Map oci.database.models.ExadbVmClusterUpdateHistoryEntry → ExadbVmClusterUpdateHistoryEntry Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExadbVmClusterUpdateHistoryEntry(**data)
    except Exception:
        return ExadbVmClusterUpdateHistoryEntry(
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_completed=getattr(o, "time_completed", None),
            time_started=getattr(o, "time_started", None),
            update_action=getattr(o, "update_action", None),
            update_id=getattr(o, "update_id", None),
            update_type=getattr(o, "update_type", None),
            version=getattr(o, "version", None),
        )


class ExascaleDbStorageVault(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExascaleDbStorageVault."""

    additional_flash_cache_in_percent: Optional[Any] = Field(
        None,
        description="The size of additional Flash Cache in percentage of High Capacity database storage.",
    )
    availability_domain: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the availability_domain of this ExascaleDbStorageVault. The name of the availability domain in which the Exadata Database Storage Vault is located.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExascaleDbStorageVault. The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    description: Optional[Any] = Field(
        None,
        description="Exadata Database Storage Vault description.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExascaleDbStorageVault. The user-friendly name for the Exadata Database Storage Vault. The name does not need to be unique.",
    )
    exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Exadata infrastructure.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    high_capacity_database_storage: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the high_capacity_database_storage of this ExascaleDbStorageVault.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExascaleDbStorageVault. The `OCID`__ of the Exadata Database Storage Vault.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExascaleDbStorageVault. The current state of the Exadata Database Storage Vault. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    system_tags: Optional[Any] = Field(
        None,
        description="System tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the Exadata Database Storage Vault was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone that you want to use for the Exadata Database Storage Vault. For details, see `Time Zones`__.",
    )
    vm_cluster_count: Optional[Any] = Field(
        None,
        description="The number of Exadata VM clusters used the Exadata Database Storage Vault.",
    )
    vm_cluster_ids: Optional[Any] = Field(
        None,
        description="The List of Exadata VM cluster on Exascale Infrastructure `OCIDs`__ **Note:** If Exadata Database Storage Vault is not used for any Exadata VM cluster on Exascale Infrastructure, this list is empty.",
    )


def map_exascaledbstoragevault(
    o: oci.database.models.ExascaleDbStorageVault,
) -> ExascaleDbStorageVault | None:
    """Map oci.database.models.ExascaleDbStorageVault → ExascaleDbStorageVault Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExascaleDbStorageVault(**data)
    except Exception:
        return ExascaleDbStorageVault(
            additional_flash_cache_in_percent=getattr(
                o, "additional_flash_cache_in_percent", None
            ),
            availability_domain=getattr(o, "availability_domain", None),
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            description=getattr(o, "description", None),
            display_name=getattr(o, "display_name", None),
            exadata_infrastructure_id=getattr(o, "exadata_infrastructure_id", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            high_capacity_database_storage=getattr(
                o, "high_capacity_database_storage", None
            ),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            system_tags=getattr(o, "system_tags", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
            vm_cluster_count=getattr(o, "vm_cluster_count", None),
            vm_cluster_ids=getattr(o, "vm_cluster_ids", None),
        )


class ExecutionAction(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExecutionAction."""

    action_members: Optional[Any] = Field(
        None,
        description="List of action members of this execution action.",
    )
    action_params: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the action_params of this ExecutionAction. Map<ParamName, ParamValue> where a key value pair describes the specific action parameter. Example: `{"count": "3"}`',
    )
    action_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the action_type of this ExecutionAction. The action type of the execution action being performed Allowed values for this property are: "DB_SERVER_FULL_SOFTWARE_UPDATE", "STORAGE_SERVER_FULL_SOFTWARE_UPDATE", "NETWORK_SWITCH_FULL_SOFTWARE_UPDATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExecutionAction. The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    description: Optional[Any] = Field(
        None,
        description="Description of the execution action.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExecutionAction. The user-friendly name for the execution action. The name does not need to be unique.",
    )
    estimated_time_in_mins: Optional[Any] = Field(
        None,
        description="The estimated time of the execution action in minutes.",
    )
    execution_action_order: Optional[Any] = Field(
        None,
        description="The priority order of the execution action.",
    )
    execution_window_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the execution_window_id of this ExecutionAction. The `OCID`__ of the execution window resource the execution action belongs to.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExecutionAction. The `OCID`__ of the execution action.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExecutionAction. The current state of the execution action. Valid states are SCHEDULED, IN_PROGRESS, FAILED, CANCELED, UPDATING, DELETED, SUCCEEDED and PARTIAL_SUCCESS. Allowed values for this property are: "SCHEDULED", "IN_PROGRESS", "FAILED", "CANCELED", "UPDATING", "DELETED", "SUCCEEDED", "PARTIAL_SUCCESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    lifecycle_substate: Optional[Any] = Field(
        None,
        description='The current sub-state of the execution action. Valid states are DURATION_EXCEEDED, MAINTENANCE_IN_PROGRESS and WAITING. Allowed values for this property are: "DURATION_EXCEEDED", "MAINTENANCE_IN_PROGRESS", "WAITING", "RESCHEDULED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the execution action was created.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The last date and time that the execution action was updated.",
    )
    total_time_taken_in_mins: Optional[Any] = Field(
        None,
        description="The total time taken by corresponding resource activity in minutes.",
    )


def map_executionaction(
    o: oci.database.models.ExecutionAction,
) -> ExecutionAction | None:
    """Map oci.database.models.ExecutionAction → ExecutionAction Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExecutionAction(**data)
    except Exception:
        return ExecutionAction(
            action_members=getattr(o, "action_members", None),
            action_params=getattr(o, "action_params", None),
            action_type=getattr(o, "action_type", None),
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            description=getattr(o, "description", None),
            display_name=getattr(o, "display_name", None),
            estimated_time_in_mins=getattr(o, "estimated_time_in_mins", None),
            execution_action_order=getattr(o, "execution_action_order", None),
            execution_window_id=getattr(o, "execution_window_id", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            lifecycle_substate=getattr(o, "lifecycle_substate", None),
            time_created=getattr(o, "time_created", None),
            time_updated=getattr(o, "time_updated", None),
            total_time_taken_in_mins=getattr(o, "total_time_taken_in_mins", None),
        )


class ExecutionWindow(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExecutionWindow."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExecutionWindow. The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    description: Optional[Any] = Field(
        None,
        description="Description of the execution window.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExecutionWindow. The user-friendly name for the execution window. The name does not need to be unique.",
    )
    estimated_time_in_mins: Optional[Any] = Field(
        None,
        description="The estimated time of the execution window in minutes.",
    )
    execution_resource_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the execution_resource_id of this ExecutionWindow. The `OCID`__ of the execution resource the execution window belongs to.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExecutionWindow. The `OCID`__ of the execution window.",
    )
    is_enforced_duration: Optional[Any] = Field(
        None,
        description="Indicates if duration the user plans to allocate for scheduling window is strictly enforced. The default value is `FALSE`.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExecutionWindow. The current state of the Schedule Policy. Valid states are CREATED, SCHEDULED, IN_PROGRESS, FAILED, CANCELED, UPDATING, DELETED, SUCCEEDED and PARTIAL_SUCCESS. Allowed values for this property are: "CREATED", "SCHEDULED", "IN_PROGRESS", "FAILED", "CANCELED", "UPDATING", "DELETED", "SUCCEEDED", "PARTIAL_SUCCESS", "CREATING", "DELETING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    lifecycle_substate: Optional[Any] = Field(
        None,
        description='The current sub-state of the execution window. Valid states are DURATION_EXCEEDED, MAINTENANCE_IN_PROGRESS and WAITING. Allowed values for this property are: "DURATION_EXCEEDED", "MAINTENANCE_IN_PROGRESS", "WAITING", "RESCHEDULED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the execution window was created.",
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time that the execution window ended.",
    )
    time_scheduled: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_scheduled of this ExecutionWindow. The scheduled start date and time of the execution window.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="The date and time that the execution window was started.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The last date and time that the execution window was updated.",
    )
    total_time_taken_in_mins: Optional[Any] = Field(
        None,
        description="The total time taken by corresponding resource activity in minutes.",
    )
    window_duration_in_mins: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the window_duration_in_mins of this ExecutionWindow. Duration window allows user to set a duration they plan to allocate for Scheduling window. The duration is in minutes.",
    )
    window_type: Optional[Any] = Field(
        None,
        description="The execution window is of PLANNED or UNPLANNED type. Allowed values for this property are: \"PLANNED\", \"UNPLANNED\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )


def map_executionwindow(
    o: oci.database.models.ExecutionWindow,
) -> ExecutionWindow | None:
    """Map oci.database.models.ExecutionWindow → ExecutionWindow Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExecutionWindow(**data)
    except Exception:
        return ExecutionWindow(
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            description=getattr(o, "description", None),
            display_name=getattr(o, "display_name", None),
            estimated_time_in_mins=getattr(o, "estimated_time_in_mins", None),
            execution_resource_id=getattr(o, "execution_resource_id", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_enforced_duration=getattr(o, "is_enforced_duration", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            lifecycle_substate=getattr(o, "lifecycle_substate", None),
            time_created=getattr(o, "time_created", None),
            time_ended=getattr(o, "time_ended", None),
            time_scheduled=getattr(o, "time_scheduled", None),
            time_started=getattr(o, "time_started", None),
            time_updated=getattr(o, "time_updated", None),
            total_time_taken_in_mins=getattr(o, "total_time_taken_in_mins", None),
            window_duration_in_mins=getattr(o, "window_duration_in_mins", None),
            window_type=getattr(o, "window_type", None),
        )


class ExternalBackupJob(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExternalBackupJob."""

    backup_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the backup_id of this ExternalBackupJob. The `OCID`__ of the associated backup resource.",
    )
    bucket_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the bucket_name of this ExternalBackupJob. The name of the Swift compartment bucket where the backup should be stored.",
    )
    provisioning: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the provisioning of this ExternalBackupJob. An indicator for the provisioning state of the resource. If `TRUE`, the resource is still being provisioned.",
    )
    swift_password: Optional[Any] = Field(
        None,
        description="The auth token to use for access to the Swift compartment bucket that will store the standalone backup. For information about auth tokens, see `Working with Auth Tokens`__.",
    )
    swift_path: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the swift_path of this ExternalBackupJob. The Swift path to use as a destination for the standalone backup.",
    )
    tag: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the tag of this ExternalBackupJob. The tag for RMAN to apply to the backup.",
    )
    user_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the user_name of this ExternalBackupJob. The Swift user name to use for transferring the standalone backup to the designated Swift compartment bucket.",
    )


def map_externalbackupjob(
    o: oci.database.models.ExternalBackupJob,
) -> ExternalBackupJob | None:
    """Map oci.database.models.ExternalBackupJob → ExternalBackupJob Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExternalBackupJob(**data)
    except Exception:
        return ExternalBackupJob(
            backup_id=getattr(o, "backup_id", None),
            bucket_name=getattr(o, "bucket_name", None),
            provisioning=getattr(o, "provisioning", None),
            swift_password=getattr(o, "swift_password", None),
            swift_path=getattr(o, "swift_path", None),
            tag=getattr(o, "tag", None),
            user_name=getattr(o, "user_name", None),
        )


class ExternalContainerDatabase(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExternalContainerDatabase."""

    character_set: Optional[Any] = Field(
        None,
        description="The character set of the external database.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExternalContainerDatabase. The `OCID`__ of the compartment.",
    )
    database_configuration: Optional[Any] = Field(
        None,
        description="The Oracle Database configuration Allowed values for this property are: \"RAC\", \"SINGLE_INSTANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    database_edition: Optional[Any] = Field(
        None,
        description='The Oracle Database edition. Allowed values for this property are: "STANDARD_EDITION", "ENTERPRISE_EDITION", "ENTERPRISE_EDITION_HIGH_PERFORMANCE", "ENTERPRISE_EDITION_EXTREME_PERFORMANCE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    database_management_config: Optional[Any] = Field(
        None,
        description="",
    )
    database_version: Optional[Any] = Field(
        None,
        description="The Oracle Database version.",
    )
    db_id: Optional[Any] = Field(
        None,
        description="The Oracle Database ID, which identifies an Oracle Database located outside of Oracle Cloud.",
    )
    db_packs: Optional[Any] = Field(
        None,
        description="The database packs licensed for the external Oracle Database.",
    )
    db_unique_name: Optional[Any] = Field(
        None,
        description="The `DB_UNIQUE_NAME` of the external database.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExternalContainerDatabase. The user-friendly name for the external database. The name does not have to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExternalContainerDatabase. The `OCID`__ of the Oracle Cloud Infrastructure external database resource.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExternalContainerDatabase. The current state of the Oracle Cloud Infrastructure external database resource. Allowed values for this property are: "PROVISIONING", "NOT_CONNECTED", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    ncharacter_set: Optional[Any] = Field(
        None,
        description="The national character of the external database.",
    )
    stack_monitoring_config: Optional[Any] = Field(
        None,
        description="",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this ExternalContainerDatabase. The date and time the database was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the external database. It is a time zone offset (a character type in the format '[+|-]TZH:TZM') or a time zone region name, depending on how the time zone value was specified when the database was created / last altered.",
    )


def map_externalcontainerdatabase(
    o: oci.database.models.ExternalContainerDatabase,
) -> ExternalContainerDatabase | None:
    """Map oci.database.models.ExternalContainerDatabase → ExternalContainerDatabase Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExternalContainerDatabase(**data)
    except Exception:
        return ExternalContainerDatabase(
            character_set=getattr(o, "character_set", None),
            compartment_id=getattr(o, "compartment_id", None),
            database_configuration=getattr(o, "database_configuration", None),
            database_edition=getattr(o, "database_edition", None),
            database_management_config=getattr(o, "database_management_config", None),
            database_version=getattr(o, "database_version", None),
            db_id=getattr(o, "db_id", None),
            db_packs=getattr(o, "db_packs", None),
            db_unique_name=getattr(o, "db_unique_name", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            ncharacter_set=getattr(o, "ncharacter_set", None),
            stack_monitoring_config=getattr(o, "stack_monitoring_config", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
        )


class ExternalDatabaseConnector(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExternalDatabaseConnector."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExternalDatabaseConnector. The `OCID`__ of the compartment.",
    )
    connection_status: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the connection_status of this ExternalDatabaseConnector. The status of connectivity to the external database.",
    )
    connector_type: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the connector_type of this ExternalDatabaseConnector. The type of connector used by the external database resource. Allowed values for this property are: \"MACS\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExternalDatabaseConnector. The user-friendly name for the :func:`create_external_database_connector_details`. The name does not have to be unique.",
    )
    external_database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the external_database_id of this ExternalDatabaseConnector. The `OCID`__ of the external database resource.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExternalDatabaseConnector. The `OCID`__ of the :func:`create_external_database_connector_details`.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExternalDatabaseConnector. The current lifecycle state of the external database connector resource. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_connection_status_last_updated: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_connection_status_last_updated of this ExternalDatabaseConnector. The date and time the connectionStatus of this external connector was last updated.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this ExternalDatabaseConnector. The date and time the external connector was created.",
    )


def map_externaldatabaseconnector(
    o: oci.database.models.ExternalDatabaseConnector,
) -> ExternalDatabaseConnector | None:
    """Map oci.database.models.ExternalDatabaseConnector → ExternalDatabaseConnector Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExternalDatabaseConnector(**data)
    except Exception:
        return ExternalDatabaseConnector(
            compartment_id=getattr(o, "compartment_id", None),
            connection_status=getattr(o, "connection_status", None),
            connector_type=getattr(o, "connector_type", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            external_database_id=getattr(o, "external_database_id", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_connection_status_last_updated=getattr(
                o, "time_connection_status_last_updated", None
            ),
            time_created=getattr(o, "time_created", None),
        )


class ExternalNonContainerDatabase(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExternalNonContainerDatabase."""

    character_set: Optional[Any] = Field(
        None,
        description="The character set of the external database.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExternalNonContainerDatabase. The `OCID`__ of the compartment.",
    )
    database_configuration: Optional[Any] = Field(
        None,
        description="The Oracle Database configuration Allowed values for this property are: \"RAC\", \"SINGLE_INSTANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    database_edition: Optional[Any] = Field(
        None,
        description='The Oracle Database edition. Allowed values for this property are: "STANDARD_EDITION", "ENTERPRISE_EDITION", "ENTERPRISE_EDITION_HIGH_PERFORMANCE", "ENTERPRISE_EDITION_EXTREME_PERFORMANCE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    database_management_config: Optional[Any] = Field(
        None,
        description="",
    )
    database_version: Optional[Any] = Field(
        None,
        description="The Oracle Database version.",
    )
    db_id: Optional[Any] = Field(
        None,
        description="The Oracle Database ID, which identifies an Oracle Database located outside of Oracle Cloud.",
    )
    db_packs: Optional[Any] = Field(
        None,
        description="The database packs licensed for the external Oracle Database.",
    )
    db_unique_name: Optional[Any] = Field(
        None,
        description="The `DB_UNIQUE_NAME` of the external database.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExternalNonContainerDatabase. The user-friendly name for the external database. The name does not have to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExternalNonContainerDatabase. The `OCID`__ of the Oracle Cloud Infrastructure external database resource.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExternalNonContainerDatabase. The current state of the Oracle Cloud Infrastructure external database resource. Allowed values for this property are: "PROVISIONING", "NOT_CONNECTED", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    ncharacter_set: Optional[Any] = Field(
        None,
        description="The national character of the external database.",
    )
    operations_insights_config: Optional[Any] = Field(
        None,
        description="",
    )
    stack_monitoring_config: Optional[Any] = Field(
        None,
        description="",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this ExternalNonContainerDatabase. The date and time the database was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the external database. It is a time zone offset (a character type in the format '[+|-]TZH:TZM') or a time zone region name, depending on how the time zone value was specified when the database was created / last altered.",
    )


def map_externalnoncontainerdatabase(
    o: oci.database.models.ExternalNonContainerDatabase,
) -> ExternalNonContainerDatabase | None:
    """Map oci.database.models.ExternalNonContainerDatabase → ExternalNonContainerDatabase Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExternalNonContainerDatabase(**data)
    except Exception:
        return ExternalNonContainerDatabase(
            character_set=getattr(o, "character_set", None),
            compartment_id=getattr(o, "compartment_id", None),
            database_configuration=getattr(o, "database_configuration", None),
            database_edition=getattr(o, "database_edition", None),
            database_management_config=getattr(o, "database_management_config", None),
            database_version=getattr(o, "database_version", None),
            db_id=getattr(o, "db_id", None),
            db_packs=getattr(o, "db_packs", None),
            db_unique_name=getattr(o, "db_unique_name", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            ncharacter_set=getattr(o, "ncharacter_set", None),
            operations_insights_config=getattr(o, "operations_insights_config", None),
            stack_monitoring_config=getattr(o, "stack_monitoring_config", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
        )


class ExternalPluggableDatabase(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ExternalPluggableDatabase."""

    character_set: Optional[Any] = Field(
        None,
        description="The character set of the external database.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ExternalPluggableDatabase. The `OCID`__ of the compartment.",
    )
    database_configuration: Optional[Any] = Field(
        None,
        description="The Oracle Database configuration Allowed values for this property are: \"RAC\", \"SINGLE_INSTANCE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    database_edition: Optional[Any] = Field(
        None,
        description='The Oracle Database edition. Allowed values for this property are: "STANDARD_EDITION", "ENTERPRISE_EDITION", "ENTERPRISE_EDITION_HIGH_PERFORMANCE", "ENTERPRISE_EDITION_EXTREME_PERFORMANCE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    database_management_config: Optional[Any] = Field(
        None,
        description="",
    )
    database_version: Optional[Any] = Field(
        None,
        description="The Oracle Database version.",
    )
    db_id: Optional[Any] = Field(
        None,
        description="The Oracle Database ID, which identifies an Oracle Database located outside of Oracle Cloud.",
    )
    db_packs: Optional[Any] = Field(
        None,
        description="The database packs licensed for the external Oracle Database.",
    )
    db_unique_name: Optional[Any] = Field(
        None,
        description="The `DB_UNIQUE_NAME` of the external database.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ExternalPluggableDatabase. The user-friendly name for the external database. The name does not have to be unique.",
    )
    external_container_database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the external_container_database_id of this ExternalPluggableDatabase. The `OCID`__ of the :func:`create_external_container_database_details` that contains the specified :func:`create_external_pluggable_database_details` resource.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ExternalPluggableDatabase. The `OCID`__ of the Oracle Cloud Infrastructure external database resource.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ExternalPluggableDatabase. The current state of the Oracle Cloud Infrastructure external database resource. Allowed values for this property are: "PROVISIONING", "NOT_CONNECTED", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    ncharacter_set: Optional[Any] = Field(
        None,
        description="The national character of the external database.",
    )
    operations_insights_config: Optional[Any] = Field(
        None,
        description="",
    )
    source_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the the non-container database that was converted to a pluggable database to create this resource.",
    )
    stack_monitoring_config: Optional[Any] = Field(
        None,
        description="",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this ExternalPluggableDatabase. The date and time the database was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the external database. It is a time zone offset (a character type in the format '[+|-]TZH:TZM') or a time zone region name, depending on how the time zone value was specified when the database was created / last altered.",
    )


def map_externalpluggabledatabase(
    o: oci.database.models.ExternalPluggableDatabase,
) -> ExternalPluggableDatabase | None:
    """Map oci.database.models.ExternalPluggableDatabase → ExternalPluggableDatabase Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ExternalPluggableDatabase(**data)
    except Exception:
        return ExternalPluggableDatabase(
            character_set=getattr(o, "character_set", None),
            compartment_id=getattr(o, "compartment_id", None),
            database_configuration=getattr(o, "database_configuration", None),
            database_edition=getattr(o, "database_edition", None),
            database_management_config=getattr(o, "database_management_config", None),
            database_version=getattr(o, "database_version", None),
            db_id=getattr(o, "db_id", None),
            db_packs=getattr(o, "db_packs", None),
            db_unique_name=getattr(o, "db_unique_name", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            external_container_database_id=getattr(
                o, "external_container_database_id", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            ncharacter_set=getattr(o, "ncharacter_set", None),
            operations_insights_config=getattr(o, "operations_insights_config", None),
            source_id=getattr(o, "source_id", None),
            stack_monitoring_config=getattr(o, "stack_monitoring_config", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
        )


class InfrastructureTargetVersion(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.InfrastructureTargetVersion."""

    target_db_version_history_entry: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the target_db_version_history_entry of this InfrastructureTargetVersion. The history entry of the target system software version for the database server patching operation.",
    )
    target_resource_id: Optional[Any] = Field(
        None,
        description="The OCID of the target Exadata Infrastructure resource that will receive the maintenance update.",
    )
    target_resource_type: Optional[Any] = Field(
        None,
        description='The resource type of the target Exadata infrastructure resource that will receive the system software update. Allowed values for this property are: "EXADATA_DB_SYSTEM", "CLOUD_EXADATA_INFRASTRUCTURE", "EXACC_INFRASTRUCTURE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    target_storage_version_history_entry: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the target_storage_version_history_entry of this InfrastructureTargetVersion. The history entry of the target storage cell system software version for the storage cell patching operation.",
    )


def map_infrastructuretargetversion(
    o: oci.database.models.InfrastructureTargetVersion,
) -> InfrastructureTargetVersion | None:
    """Map oci.database.models.InfrastructureTargetVersion → InfrastructureTargetVersion Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return InfrastructureTargetVersion(**data)
    except Exception:
        return InfrastructureTargetVersion(
            target_db_version_history_entry=getattr(
                o, "target_db_version_history_entry", None
            ),
            target_resource_id=getattr(o, "target_resource_id", None),
            target_resource_type=getattr(o, "target_resource_type", None),
            target_storage_version_history_entry=getattr(
                o, "target_storage_version_history_entry", None
            ),
        )


class KeyStore(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.KeyStore."""

    associated_databases: Optional[Any] = Field(
        None,
        description="List of databases associated with the key store.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this KeyStore. The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this KeyStore. The user-friendly name for the key store. The name does not need to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this KeyStore. The `OCID`__ of the key store.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this KeyStore. The current state of the key store. Allowed values for this property are: "ACTIVE", "DELETED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the key store was created.",
    )
    type_details: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the type_details of this KeyStore.",
    )


def map_keystore(o: oci.database.models.KeyStore) -> KeyStore | None:
    """Map oci.database.models.KeyStore → KeyStore Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return KeyStore(**data)
    except Exception:
        return KeyStore(
            associated_databases=getattr(o, "associated_databases", None),
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_created=getattr(o, "time_created", None),
            type_details=getattr(o, "type_details", None),
        )


class MaintenanceRun(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.MaintenanceRun."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this MaintenanceRun. The OCID of the compartment.",
    )
    current_custom_action_timeout_in_mins: Optional[Any] = Field(
        None,
        description="Extend current custom action timeout between the current database servers during waiting state, from 0 (zero) to 30 minutes.",
    )
    current_patching_component: Optional[Any] = Field(
        None,
        description="The name of the current infrastruture component that is getting patched.",
    )
    custom_action_timeout_in_mins: Optional[Any] = Field(
        None,
        description="Determines the amount of time the system will wait before the start of each database server patching operation. Specify a number of minutes, from 15 to 120.",
    )
    database_software_image_id: Optional[Any] = Field(
        None,
        description="The Autonomous Database Software Image `OCID`__",
    )
    description: Optional[Any] = Field(
        None,
        description="Description of the maintenance run.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this MaintenanceRun. The user-friendly name for the maintenance run.",
    )
    estimated_component_patching_start_time: Optional[Any] = Field(
        None,
        description="The estimated start time of the next infrastruture component patching operation.",
    )
    estimated_patching_time: Optional[Any] = Field(
        None,
        description="",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this MaintenanceRun. The OCID of the maintenance run.",
    )
    is_custom_action_timeout_enabled: Optional[Any] = Field(
        None,
        description="If true, enables the configuration of a custom action timeout (waiting period) between database servers patching operations.",
    )
    is_dst_file_update_enabled: Optional[Any] = Field(
        None,
        description="Indicates if an automatic DST Time Zone file update is enabled for the Autonomous Container Database. If enabled along with Release Update, patching will be done in a Non-Rolling manner.",
    )
    is_maintenance_run_granular: Optional[Any] = Field(
        None,
        description="If `FALSE`, the maintenance run doesn't support granular maintenance.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this MaintenanceRun. The current state of the maintenance run. For Autonomous Database Serverless instances, valid states are IN_PROGRESS, SUCCEEDED, and FAILED. Allowed values for this property are: "SCHEDULED", "IN_PROGRESS", "SUCCEEDED", "SKIPPED", "FAILED", "UPDATING", "DELETING", "DELETED", "CANCELED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_subtype: Optional[Any] = Field(
        None,
        description='Maintenance sub-type. Allowed values for this property are: "QUARTERLY", "HARDWARE", "CRITICAL", "INFRASTRUCTURE", "DATABASE", "ONEOFF", "SECURITY_MONTHLY", "TIMEZONE", "CUSTOM_DATABASE_SOFTWARE_IMAGE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    maintenance_type: Optional[Any] = Field(
        None,
        description="Maintenance type. Allowed values for this property are: \"PLANNED\", \"UNPLANNED\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    patch_failure_count: Optional[Any] = Field(
        None,
        description="Contain the patch failure count.",
    )
    patch_id: Optional[Any] = Field(
        None,
        description="The unique identifier of the patch. The identifier string includes the patch type, the Oracle Database version, and the patch creation date (using the format YYMMDD). For example, the identifier `ru_patch_19.9.0.0_201030` is used for an RU patch for Oracle Database 19.9.0.0 that was released October 30, 2020.",
    )
    patching_end_time: Optional[Any] = Field(
        None,
        description="The time when the patching operation ended.",
    )
    patching_mode: Optional[Any] = Field(
        None,
        description='Cloud Exadata infrastructure node patching method, either "ROLLING" or "NONROLLING". Default value is ROLLING. *IMPORTANT*: Non-rolling infrastructure patching involves system down time. See `Oracle-Managed Infrastructure Maintenance Updates`__ for more information. Allowed values for this property are: "ROLLING", "NONROLLING", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    patching_start_time: Optional[Any] = Field(
        None,
        description="The time when the patching operation started.",
    )
    patching_status: Optional[Any] = Field(
        None,
        description='The status of the patching operation. Allowed values for this property are: "PATCHING", "WAITING", "SCHEDULED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    peer_maintenance_run_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the maintenance run for the Autonomous Data Guard association's peer container database.",
    )
    target_db_server_version: Optional[Any] = Field(
        None,
        description="The target software version for the database server patching operation.",
    )
    target_resource_id: Optional[Any] = Field(
        None,
        description="The ID of the target resource on which the maintenance run occurs.",
    )
    target_resource_type: Optional[Any] = Field(
        None,
        description='The type of the target resource on which the maintenance run occurs. Allowed values for this property are: "AUTONOMOUS_EXADATA_INFRASTRUCTURE", "AUTONOMOUS_CONTAINER_DATABASE", "EXADATA_DB_SYSTEM", "CLOUD_EXADATA_INFRASTRUCTURE", "EXACC_INFRASTRUCTURE", "AUTONOMOUS_VM_CLUSTER", "AUTONOMOUS_DATABASE", "CLOUD_AUTONOMOUS_VM_CLUSTER", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    target_storage_server_version: Optional[Any] = Field(
        None,
        description="The target Cell version that is to be patched to.",
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time the maintenance run was completed.",
    )
    time_scheduled: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_scheduled of this MaintenanceRun. The date and time the maintenance run is scheduled to occur.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="The date and time the maintenance run starts.",
    )
    total_time_taken_in_mins: Optional[Any] = Field(
        None,
        description="The total time taken by corresponding resource activity in minutes.",
    )


def map_maintenancerun(o: oci.database.models.MaintenanceRun) -> MaintenanceRun | None:
    """Map oci.database.models.MaintenanceRun → MaintenanceRun Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return MaintenanceRun(**data)
    except Exception:
        return MaintenanceRun(
            compartment_id=getattr(o, "compartment_id", None),
            current_custom_action_timeout_in_mins=getattr(
                o, "current_custom_action_timeout_in_mins", None
            ),
            current_patching_component=getattr(o, "current_patching_component", None),
            custom_action_timeout_in_mins=getattr(
                o, "custom_action_timeout_in_mins", None
            ),
            database_software_image_id=getattr(o, "database_software_image_id", None),
            description=getattr(o, "description", None),
            display_name=getattr(o, "display_name", None),
            estimated_component_patching_start_time=getattr(
                o, "estimated_component_patching_start_time", None
            ),
            estimated_patching_time=getattr(o, "estimated_patching_time", None),
            id=getattr(o, "id", None),
            is_custom_action_timeout_enabled=getattr(
                o, "is_custom_action_timeout_enabled", None
            ),
            is_dst_file_update_enabled=getattr(o, "is_dst_file_update_enabled", None),
            is_maintenance_run_granular=getattr(o, "is_maintenance_run_granular", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            maintenance_subtype=getattr(o, "maintenance_subtype", None),
            maintenance_type=getattr(o, "maintenance_type", None),
            patch_failure_count=getattr(o, "patch_failure_count", None),
            patch_id=getattr(o, "patch_id", None),
            patching_end_time=getattr(o, "patching_end_time", None),
            patching_mode=getattr(o, "patching_mode", None),
            patching_start_time=getattr(o, "patching_start_time", None),
            patching_status=getattr(o, "patching_status", None),
            peer_maintenance_run_id=getattr(o, "peer_maintenance_run_id", None),
            target_db_server_version=getattr(o, "target_db_server_version", None),
            target_resource_id=getattr(o, "target_resource_id", None),
            target_resource_type=getattr(o, "target_resource_type", None),
            target_storage_server_version=getattr(
                o, "target_storage_server_version", None
            ),
            time_ended=getattr(o, "time_ended", None),
            time_scheduled=getattr(o, "time_scheduled", None),
            time_started=getattr(o, "time_started", None),
            total_time_taken_in_mins=getattr(o, "total_time_taken_in_mins", None),
        )


class MaintenanceRunHistory(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.MaintenanceRunHistory."""

    current_execution_window: Optional[Any] = Field(
        None,
        description="The OCID of the current execution window.",
    )
    db_servers_history_details: Optional[Any] = Field(
        None,
        description="List of database server history details.",
    )
    granular_maintenance_history: Optional[Any] = Field(
        None,
        description="The list of granular maintenance history details.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this MaintenanceRunHistory. The OCID of the maintenance run history.",
    )
    maintenance_run_details: Optional[Any] = Field(
        None,
        description="",
    )


def map_maintenancerunhistory(
    o: oci.database.models.MaintenanceRunHistory,
) -> MaintenanceRunHistory | None:
    """Map oci.database.models.MaintenanceRunHistory → MaintenanceRunHistory Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return MaintenanceRunHistory(**data)
    except Exception:
        return MaintenanceRunHistory(
            current_execution_window=getattr(o, "current_execution_window", None),
            db_servers_history_details=getattr(o, "db_servers_history_details", None),
            granular_maintenance_history=getattr(
                o, "granular_maintenance_history", None
            ),
            id=getattr(o, "id", None),
            maintenance_run_details=getattr(o, "maintenance_run_details", None),
        )


class OneoffPatch(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.OneoffPatch."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this OneoffPatch. The `OCID`__ of the compartment.",
    )
    db_version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the db_version of this OneoffPatch. A valid Oracle Database version. For a list of supported versions, use the ListDbVersions operation. This cannot be updated in parallel with any of the following: licenseModel, dbEdition, cpuCoreCount, computeCount, computeModel, adminPassword, whitelistedIps, isMTLSConnectionRequired, openMode, permissionLevel, dbWorkload, privateEndpointLabel, nsgIds, isRefreshable, dbName, scheduledOperations, dbToolsDetails, isLocalDataGuardEnabled, or isFreeTier.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this OneoffPatch. One-off patch name.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this OneoffPatch. The `OCID`__ of the one-off patch.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Detailed message for the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this OneoffPatch. The current state of the one-off patch. Allowed values for this property are: "CREATING", "AVAILABLE", "UPDATING", "INACTIVE", "FAILED", "EXPIRED", "DELETING", "DELETED", "TERMINATING", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    one_off_patches: Optional[Any] = Field(
        None,
        description="List of one-off patches for Database Homes.",
    )
    release_update: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the release_update of this OneoffPatch. The PSU or PBP or Release Updates. To get a list of supported versions, use the :func:`list_db_versions` operation.",
    )
    sha256_sum: Optional[Any] = Field(
        None,
        description="SHA-256 checksum of the one-off patch.",
    )
    size_in_kbs: Optional[float] = Field(
        None,
        description="The size of one-off patch in kilobytes.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this OneoffPatch. The date and time one-off patch was created.",
    )
    time_of_expiration: Optional[Any] = Field(
        None,
        description="The date and time until which the one-off patch will be available for download.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The date and time one-off patch was updated.",
    )


def map_oneoffpatch(o: oci.database.models.OneoffPatch) -> OneoffPatch | None:
    """Map oci.database.models.OneoffPatch → OneoffPatch Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return OneoffPatch(**data)
    except Exception:
        return OneoffPatch(
            compartment_id=getattr(o, "compartment_id", None),
            db_version=getattr(o, "db_version", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            one_off_patches=getattr(o, "one_off_patches", None),
            release_update=getattr(o, "release_update", None),
            sha256_sum=getattr(o, "sha256_sum", None),
            size_in_kbs=getattr(o, "size_in_kbs", None),
            time_created=getattr(o, "time_created", None),
            time_of_expiration=getattr(o, "time_of_expiration", None),
            time_updated=getattr(o, "time_updated", None),
        )


class PdbConversionHistoryEntry(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.PdbConversionHistoryEntry."""

    action: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the action of this PdbConversionHistoryEntry. The operations used to convert a non-container database to a pluggable database. - Use `PRECHECK` to run a pre-check operation on non-container database prior to converting it into a pluggable database. - Use `CONVERT` to convert a non-container database into a pluggable database. - Use `SYNC` if the non-container database was manually converted into a pluggable database using the dbcli command-line utility. Databases may need to be converted manually if the CONVERT action fails when converting a non-container database using the API. - Use `SYNC_ROLLBACK` if the conversion of a non-container database into a pluggable database was manually rolled back using the dbcli command line utility. Conversions may need to be manually rolled back if the CONVERT action fails when converting a non-container database using the API. Allowed values for this property are: "PRECHECK", "CONVERT", "SYNC", "SYNC_ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    additional_cdb_params: Optional[Any] = Field(
        None,
        description="Additional container database parameter.",
    )
    cdb_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the cdb_name of this PdbConversionHistoryEntry. The database name. The name must begin with an alphabetic character and can contain a maximum of 8 alphanumeric characters. Special characters are not permitted. The database name must be unique in the tenancy.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this PdbConversionHistoryEntry. The `OCID`__ of the database conversion history.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state for the conversion operation.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this PdbConversionHistoryEntry. Status of an operation performed during the conversion of a non-container database to a pluggable database. Allowed values for this property are: "SUCCEEDED", "FAILED", "IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    source_database_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the source_database_id of this PdbConversionHistoryEntry. The `OCID`__ of the database.",
    )
    target: Optional[Any] = Field(
        None,
        description="The target container database of the pluggable database created by the database conversion operation. Currently, the database conversion operation only supports creating the pluggable database in a new container database. - Use `NEW_DATABASE` to specify that the pluggable database be created within a new container database in the same database home. Allowed values for this property are: \"NEW_DATABASE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    target_database_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the database.",
    )
    time_ended: Optional[Any] = Field(
        None,
        description="The date and time when the database conversion operation ended.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_started of this PdbConversionHistoryEntry. The date and time when the database conversion operation started.",
    )


def map_pdbconversionhistoryentry(
    o: oci.database.models.PdbConversionHistoryEntry,
) -> PdbConversionHistoryEntry | None:
    """Map oci.database.models.PdbConversionHistoryEntry → PdbConversionHistoryEntry Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return PdbConversionHistoryEntry(**data)
    except Exception:
        return PdbConversionHistoryEntry(
            action=getattr(o, "action", None),
            additional_cdb_params=getattr(o, "additional_cdb_params", None),
            cdb_name=getattr(o, "cdb_name", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            source_database_id=getattr(o, "source_database_id", None),
            target=getattr(o, "target", None),
            target_database_id=getattr(o, "target_database_id", None),
            time_ended=getattr(o, "time_ended", None),
            time_started=getattr(o, "time_started", None),
        )


class ScheduledAction(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.ScheduledAction."""

    action_members: Optional[Any] = Field(
        None,
        description="The list of action members in a scheduled action.",
    )
    action_order: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the action_order of this ScheduledAction. The order of the scheduled action.",
    )
    action_params: Optional[Any] = Field(
        None,
        description='Map<ParamName, ParamValue> where a key value pair describes the specific action parameter. Example: `{"count": "3"}`',
    )
    action_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the action_type of this ScheduledAction. The type of the scheduled action being performed Allowed values for this property are: "DB_SERVER_FULL_SOFTWARE_UPDATE", "STORAGE_SERVER_FULL_SOFTWARE_UPDATE", "NETWORK_SWITCH_FULL_SOFTWARE_UPDATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this ScheduledAction. The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this ScheduledAction. The display name of the Scheduled Action.",
    )
    estimated_time_in_mins: Optional[Any] = Field(
        None,
        description="The estimated patching time for the scheduled action.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this ScheduledAction. The `OCID`__ of the Scheduled Action.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this ScheduledAction. The current state of the Scheduled Action. Valid states are CREATING, NEEDS_ATTENTION, AVAILABLE, UPDATING, FAILED, DELETING and DELETED. Allowed values for this property are: "CREATING", "NEEDS_ATTENTION", "AVAILABLE", "UPDATING", "FAILED", "DELETING", "DELETED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    scheduling_plan_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the scheduling_plan_id of this ScheduledAction. The `OCID`__ of the Scheduling Plan.",
    )
    scheduling_window_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Scheduling Window.",
    )
    system_tags: Optional[Any] = Field(
        None,
        description="System tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this ScheduledAction. The date and time the Scheduled Action Resource was created.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The date and time the Scheduled Action Resource was updated.",
    )


def map_scheduledaction(
    o: oci.database.models.ScheduledAction,
) -> ScheduledAction | None:
    """Map oci.database.models.ScheduledAction → ScheduledAction Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return ScheduledAction(**data)
    except Exception:
        return ScheduledAction(
            action_members=getattr(o, "action_members", None),
            action_order=getattr(o, "action_order", None),
            action_params=getattr(o, "action_params", None),
            action_type=getattr(o, "action_type", None),
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            estimated_time_in_mins=getattr(o, "estimated_time_in_mins", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            scheduling_plan_id=getattr(o, "scheduling_plan_id", None),
            scheduling_window_id=getattr(o, "scheduling_window_id", None),
            system_tags=getattr(o, "system_tags", None),
            time_created=getattr(o, "time_created", None),
            time_updated=getattr(o, "time_updated", None),
        )


class SchedulingPlan(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.SchedulingPlan."""

    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this SchedulingPlan. The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The display name of the Scheduling Plan.",
    )
    estimated_time_in_mins: Optional[Any] = Field(
        None,
        description="The estimated time for the Scheduling Plan.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this SchedulingPlan. The `OCID`__ of the Scheduling Plan.",
    )
    is_using_recommended_scheduled_actions: Optional[Any] = Field(
        None,
        description="If true, recommended scheduled actions will be generated for the scheduling plan.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this SchedulingPlan. The current state of the Scheduling Plan. Valid states are CREATING, NEEDS_ATTENTION, AVAILABLE, UPDATING, FAILED, DELETING and DELETED. Allowed values for this property are: "CREATING", "NEEDS_ATTENTION", "AVAILABLE", "UPDATING", "FAILED", "DELETING", "DELETED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    plan_intent: Optional[Any] = Field(
        None,
        description="The current intent the Scheduling Plan. Valid states is EXADATA_INFRASTRUCTURE_FULL_SOFTWARE_UPDATE. Allowed values for this property are: \"EXADATA_INFRASTRUCTURE_FULL_SOFTWARE_UPDATE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    resource_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the resource_id of this SchedulingPlan. The `OCID`__ of the resource.",
    )
    scheduling_policy_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the scheduling_policy_id of this SchedulingPlan. The `OCID`__ of the Scheduling Policy.",
    )
    service_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the service_type of this SchedulingPlan. The service type of the Scheduling Plan. Allowed values for this property are: "EXACC", "EXACS", "FPPPCS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    system_tags: Optional[Any] = Field(
        None,
        description="System tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_created of this SchedulingPlan. The date and time the Scheduling Plan Resource was created.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The date and time the Scheduling Plan Resource was updated.",
    )


def map_schedulingplan(o: oci.database.models.SchedulingPlan) -> SchedulingPlan | None:
    """Map oci.database.models.SchedulingPlan → SchedulingPlan Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return SchedulingPlan(**data)
    except Exception:
        return SchedulingPlan(
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            estimated_time_in_mins=getattr(o, "estimated_time_in_mins", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            is_using_recommended_scheduled_actions=getattr(
                o, "is_using_recommended_scheduled_actions", None
            ),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            plan_intent=getattr(o, "plan_intent", None),
            resource_id=getattr(o, "resource_id", None),
            scheduling_policy_id=getattr(o, "scheduling_policy_id", None),
            service_type=getattr(o, "service_type", None),
            system_tags=getattr(o, "system_tags", None),
            time_created=getattr(o, "time_created", None),
            time_updated=getattr(o, "time_updated", None),
        )


class SchedulingPolicy(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.SchedulingPolicy."""

    cadence: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the cadence of this SchedulingPolicy. The cadence period. Allowed values for this property are: "HALFYEARLY", "QUARTERLY", "MONTHLY", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    cadence_start_month: Optional[Any] = Field(
        None,
        description="Start of the month to be followed during the cadence period.",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the compartment_id of this SchedulingPolicy. The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the display_name of this SchedulingPolicy. The user-friendly name for the Scheduling Policy. The name does not need to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this SchedulingPolicy. The `OCID`__ of the Scheduling Policy.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this SchedulingPolicy. The current state of the Scheduling Policy. Valid states are CREATING, NEEDS_ATTENTION, ACTIVE, UPDATING, FAILED, DELETING and DELETED. Allowed values for this property are: "CREATING", "NEEDS_ATTENTION", "AVAILABLE", "UPDATING", "FAILED", "DELETING", "DELETED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Scheduling Policy was created.",
    )
    time_next_window_starts: Optional[Any] = Field(
        None,
        description="The date and time of the next scheduling window associated with the schedulingPolicy is planned to start.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The last date and time that the Scheduling Policy was updated.",
    )


def map_schedulingpolicy(
    o: oci.database.models.SchedulingPolicy,
) -> SchedulingPolicy | None:
    """Map oci.database.models.SchedulingPolicy → SchedulingPolicy Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return SchedulingPolicy(**data)
    except Exception:
        return SchedulingPolicy(
            cadence=getattr(o, "cadence", None),
            cadence_start_month=getattr(o, "cadence_start_month", None),
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_created=getattr(o, "time_created", None),
            time_next_window_starts=getattr(o, "time_next_window_starts", None),
            time_updated=getattr(o, "time_updated", None),
        )


class SchedulingWindow(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.SchedulingWindow."""

    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the Scheduling Window. The name does not need to be unique.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this SchedulingWindow. The `OCID`__ of the Scheduling Window.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this SchedulingWindow. The current state of the Scheduling Window. Valid states are CREATING, ACTIVE, UPDATING, FAILED, DELETING and DELETED. Allowed values for this property are: "CREATING", "AVAILABLE", "UPDATING", "FAILED", "DELETING", "DELETED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    scheduling_policy_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the scheduling_policy_id of this SchedulingWindow. The `OCID`__ of the Scheduling Policy.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time the Scheduling Window was created.",
    )
    time_next_scheduling_window_starts: Optional[Any] = Field(
        None,
        description="The date and time of the next upcoming window associated within the schedulingWindow is planned to start.",
    )
    time_updated: Optional[Any] = Field(
        None,
        description="The last date and time that the Scheduling Window was updated.",
    )
    window_preference: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the window_preference of this SchedulingWindow.",
    )


def map_schedulingwindow(
    o: oci.database.models.SchedulingWindow,
) -> SchedulingWindow | None:
    """Map oci.database.models.SchedulingWindow → SchedulingWindow Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return SchedulingWindow(**data)
    except Exception:
        return SchedulingWindow(
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            scheduling_policy_id=getattr(o, "scheduling_policy_id", None),
            time_created=getattr(o, "time_created", None),
            time_next_scheduling_window_starts=getattr(
                o, "time_next_scheduling_window_starts", None
            ),
            time_updated=getattr(o, "time_updated", None),
            window_preference=getattr(o, "window_preference", None),
        )


class VmCluster(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.VmCluster."""

    availability_domain: Optional[Any] = Field(
        None,
        description="The name of the availability domain that the VM cluster is located in.",
    )
    cloud_automation_update_details: Optional[Any] = Field(
        None,
        description="",
    )
    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    compute_model: Optional[Any] = Field(
        None,
        description="The compute model of the Autonomous Database. This is required if using the `computeCount` parameter. If using `cpuCoreCount` then it is an error to specify `computeModel` to a non-null value. ECPU compute model is the recommended model and OCPU compute model is legacy. Allowed values for this property are: \"ECPU\", \"OCPU\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    cpus_enabled: Optional[Any] = Field(
        None,
        description="The number of enabled CPU cores.",
    )
    data_collection_options: Optional[Any] = Field(
        None,
        description="",
    )
    data_storage_size_in_gbs: Optional[float] = Field(
        None,
        description="Size of the DATA disk group in GBs.",
    )
    data_storage_size_in_tbs: Optional[float] = Field(
        None,
        description="Size, in terabytes, of the DATA disk group.",
    )
    db_node_storage_size_in_gbs: Optional[Any] = Field(
        None,
        description="The local node storage allocated in GBs.",
    )
    db_servers: Optional[Any] = Field(
        None,
        description="The list of Db server.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the Exadata Cloud@Customer VM cluster. The name does not need to be unique.",
    )
    exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Exadata infrastructure.",
    )
    exascale_db_storage_vault_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Exadata Database Storage Vault.",
    )
    file_system_configuration_details: Optional[Any] = Field(
        None,
        description="Details of the file system configuration of the VM cluster.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    gi_software_image_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of a grid infrastructure software image. This is a database software image of the type `GRID_IMAGE`.",
    )
    gi_version: Optional[Any] = Field(
        None,
        description="The Oracle Grid Infrastructure software version for the VM cluster.",
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the VM cluster.",
    )
    is_local_backup_enabled: Optional[Any] = Field(
        None,
        description="If true, database backup on local Exadata storage is configured for the VM cluster. If false, database backup on local Exadata storage is not available in the VM cluster.",
    )
    is_sparse_diskgroup_enabled: Optional[Any] = Field(
        None,
        description="If true, sparse disk group is configured for the VM cluster. If false, sparse disk group is not created.",
    )
    last_patch_history_entry_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the last patch history. This value is updated as soon as a patch operation starts.",
    )
    license_model: Optional[Any] = Field(
        None,
        description="The Oracle license model that applies to the VM cluster. The default is LICENSE_INCLUDED. Allowed values for this property are: \"LICENSE_INCLUDED\", \"BRING_YOUR_OWN_LICENSE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the VM cluster. Allowed values for this property are: "PROVISIONING", "AVAILABLE", "UPDATING", "TERMINATING", "TERMINATED", "FAILED", "MAINTENANCE_IN_PROGRESS", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    memory_size_in_gbs: Optional[Any] = Field(
        None,
        description="The memory allocated in GBs.",
    )
    ocpus_enabled: Optional[float] = Field(
        None,
        description="The number of enabled OCPU cores.",
    )
    shape: Optional[Any] = Field(
        None,
        description="The shape of the Exadata infrastructure. The shape determines the amount of CPU, storage, and memory resources allocated to the instance.",
    )
    ssh_public_keys: Optional[Any] = Field(
        None,
        description="The public key portion of one or more key pairs used for SSH access to the VM cluster.",
    )
    storage_management_type: Optional[Any] = Field(
        None,
        description="Specifies whether the type of storage management for the VM cluster is ASM or Exascale. Allowed values for this property are: \"ASM\", \"EXASCALE\", 'UNKNOWN_ENUM_VALUE'. Any unrecognized values returned by a service will be mapped to 'UNKNOWN_ENUM_VALUE'.",
    )
    system_version: Optional[Any] = Field(
        None,
        description="Operating system version of the image.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time that the VM cluster was created.",
    )
    time_zone: Optional[Any] = Field(
        None,
        description="The time zone of the Exadata infrastructure. For details, see `Exadata Infrastructure Time Zones`__.",
    )
    vm_cluster_network_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the VM cluster network.",
    )


def map_vmcluster(o: oci.database.models.VmCluster) -> VmCluster | None:
    """Map oci.database.models.VmCluster → VmCluster Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return VmCluster(**data)
    except Exception:
        return VmCluster(
            availability_domain=getattr(o, "availability_domain", None),
            cloud_automation_update_details=getattr(
                o, "cloud_automation_update_details", None
            ),
            compartment_id=getattr(o, "compartment_id", None),
            compute_model=getattr(o, "compute_model", None),
            cpus_enabled=getattr(o, "cpus_enabled", None),
            data_collection_options=getattr(o, "data_collection_options", None),
            data_storage_size_in_gbs=getattr(o, "data_storage_size_in_gbs", None),
            data_storage_size_in_tbs=getattr(o, "data_storage_size_in_tbs", None),
            db_node_storage_size_in_gbs=getattr(o, "db_node_storage_size_in_gbs", None),
            db_servers=getattr(o, "db_servers", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            exadata_infrastructure_id=getattr(o, "exadata_infrastructure_id", None),
            exascale_db_storage_vault_id=getattr(
                o, "exascale_db_storage_vault_id", None
            ),
            file_system_configuration_details=getattr(
                o, "file_system_configuration_details", None
            ),
            freeform_tags=getattr(o, "freeform_tags", None),
            gi_software_image_id=getattr(o, "gi_software_image_id", None),
            gi_version=getattr(o, "gi_version", None),
            id=getattr(o, "id", None),
            is_local_backup_enabled=getattr(o, "is_local_backup_enabled", None),
            is_sparse_diskgroup_enabled=getattr(o, "is_sparse_diskgroup_enabled", None),
            last_patch_history_entry_id=getattr(o, "last_patch_history_entry_id", None),
            license_model=getattr(o, "license_model", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            memory_size_in_gbs=getattr(o, "memory_size_in_gbs", None),
            ocpus_enabled=getattr(o, "ocpus_enabled", None),
            shape=getattr(o, "shape", None),
            ssh_public_keys=getattr(o, "ssh_public_keys", None),
            storage_management_type=getattr(o, "storage_management_type", None),
            system_version=getattr(o, "system_version", None),
            time_created=getattr(o, "time_created", None),
            time_zone=getattr(o, "time_zone", None),
            vm_cluster_network_id=getattr(o, "vm_cluster_network_id", None),
        )


class VmClusterNetwork(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.VmClusterNetwork."""

    compartment_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the compartment.",
    )
    defined_tags: Optional[Any] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace. For more information, see `Resource Tags`__.",
    )
    display_name: Optional[Any] = Field(
        None,
        description="The user-friendly name for the VM cluster network. The name does not need to be unique.",
    )
    dns: Optional[Any] = Field(
        None,
        description="The list of DNS server IP addresses. Maximum of 3 allowed.",
    )
    dr_scans: Optional[Any] = Field(
        None,
        description="The SCAN details for DR network",
    )
    exadata_infrastructure_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the Exadata infrastructure.",
    )
    freeform_tags: Optional[Any] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, type, or namespace. For more information, see `Resource Tags`__. Example: `{"Department": "Finance"}`',
    )
    id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the VM cluster network.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Additional information about the current lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the VM cluster network. CREATING - The resource is being created REQUIRES_VALIDATION - The resource is created and may not be usable until it is validated. VALIDATING - The resource is being validated and not available to use. VALIDATED - The resource is validated and is available for consumption by VM cluster. VALIDATION_FAILED - The resource validation has failed and might require user input to be corrected. UPDATING - The resource is being updated and not available to use. ALLOCATED - The resource is is currently being used by VM cluster. TERMINATING - The resource is being deleted and not available to use. TERMINATED - The resource is deleted and unavailable. FAILED - The resource is in a failed state due to validation or other errors. NEEDS_ATTENTION - The resource is in needs attention state as some of it\'s child nodes are not validated and unusable by VM cluster. Allowed values for this property are: "CREATING", "REQUIRES_VALIDATION", "VALIDATING", "VALIDATED", "VALIDATION_FAILED", "UPDATING", "ALLOCATED", "TERMINATING", "TERMINATED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    ntp: Optional[Any] = Field(
        None,
        description="The list of NTP server IP addresses. Maximum of 3 allowed.",
    )
    scans: Optional[Any] = Field(
        None,
        description="The SCAN details.",
    )
    time_created: Optional[Any] = Field(
        None,
        description="The date and time when the VM cluster network was created.",
    )
    vm_cluster_id: Optional[Any] = Field(
        None,
        description="The `OCID`__ of the associated VM Cluster.",
    )
    vm_networks: Optional[Any] = Field(
        None,
        description="Details of the client and backup networks.",
    )


def map_vmclusternetwork(
    o: oci.database.models.VmClusterNetwork,
) -> VmClusterNetwork | None:
    """Map oci.database.models.VmClusterNetwork → VmClusterNetwork Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return VmClusterNetwork(**data)
    except Exception:
        return VmClusterNetwork(
            compartment_id=getattr(o, "compartment_id", None),
            defined_tags=getattr(o, "defined_tags", None),
            display_name=getattr(o, "display_name", None),
            dns=getattr(o, "dns", None),
            dr_scans=getattr(o, "dr_scans", None),
            exadata_infrastructure_id=getattr(o, "exadata_infrastructure_id", None),
            freeform_tags=getattr(o, "freeform_tags", None),
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            ntp=getattr(o, "ntp", None),
            scans=getattr(o, "scans", None),
            time_created=getattr(o, "time_created", None),
            vm_cluster_id=getattr(o, "vm_cluster_id", None),
            vm_networks=getattr(o, "vm_networks", None),
        )


class VmClusterUpdate(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.VmClusterUpdate."""

    available_actions: Optional[Any] = Field(
        None,
        description='The possible actions that can be performed using this maintenance update. Allowed values for items in this list are: "ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    description: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the description of this VmClusterUpdate. Details of the maintenance update package.",
    )
    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this VmClusterUpdate. The `OCID`__ of the maintenance update.",
    )
    last_action: Optional[Any] = Field(
        None,
        description='The update action performed most recently using this maintenance update. Allowed values for this property are: "ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Descriptive text providing additional details about the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='The current state of the maintenance update. Dependent on value of `lastAction`. Allowed values for this property are: "AVAILABLE", "SUCCESS", "IN_PROGRESS", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_released: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_released of this VmClusterUpdate. The date and time the maintenance update was released.",
    )
    update_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the update_type of this VmClusterUpdate. The type of VM cluster maintenance update. Allowed values for this property are: "GI_UPGRADE", "GI_PATCH", "OS_UPDATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    version: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the version of this VmClusterUpdate. The version of the maintenance update package.",
    )


def map_vmclusterupdate(
    o: oci.database.models.VmClusterUpdate,
) -> VmClusterUpdate | None:
    """Map oci.database.models.VmClusterUpdate → VmClusterUpdate Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return VmClusterUpdate(**data)
    except Exception:
        return VmClusterUpdate(
            available_actions=getattr(o, "available_actions", None),
            description=getattr(o, "description", None),
            id=getattr(o, "id", None),
            last_action=getattr(o, "last_action", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_released=getattr(o, "time_released", None),
            update_type=getattr(o, "update_type", None),
            version=getattr(o, "version", None),
        )


class VmClusterUpdateHistoryEntry(OCIBaseModel):
    """Pydantic model mirroring oci.database.models.VmClusterUpdateHistoryEntry."""

    id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the id of this VmClusterUpdateHistoryEntry. The `OCID`__ of the maintenance update history entry.",
    )
    lifecycle_details: Optional[Any] = Field(
        None,
        description="Descriptive text providing additional details about the lifecycle state.",
    )
    lifecycle_state: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the lifecycle_state of this VmClusterUpdateHistoryEntry. The current lifecycle state of the maintenance update operation. Allowed values for this property are: "IN_PROGRESS", "SUCCEEDED", "FAILED", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    time_completed: Optional[Any] = Field(
        None,
        description="The date and time when the maintenance update action completed.",
    )
    time_started: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the time_started of this VmClusterUpdateHistoryEntry. The date and time when the maintenance update action started.",
    )
    update_action: Optional[Any] = Field(
        None,
        description='The update action performed using this maintenance update. Allowed values for this property are: "ROLLING_APPLY", "PRECHECK", "ROLLBACK", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )
    update_id: Optional[Any] = Field(
        None,
        description="**[Required]** Gets the update_id of this VmClusterUpdateHistoryEntry. The `OCID`__ of the maintenance update.",
    )
    update_type: Optional[Any] = Field(
        None,
        description='**[Required]** Gets the update_type of this VmClusterUpdateHistoryEntry. The type of VM cluster maintenance update. Allowed values for this property are: "GI_UPGRADE", "GI_PATCH", "OS_UPDATE", \'UNKNOWN_ENUM_VALUE\'. Any unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.',
    )


def map_vmclusterupdatehistoryentry(
    o: oci.database.models.VmClusterUpdateHistoryEntry,
) -> VmClusterUpdateHistoryEntry | None:
    """Map oci.database.models.VmClusterUpdateHistoryEntry → VmClusterUpdateHistoryEntry Pydantic model."""
    if not o:
        return None
    try:
        data = oci.util.to_dict(o)
        return VmClusterUpdateHistoryEntry(**data)
    except Exception:
        return VmClusterUpdateHistoryEntry(
            id=getattr(o, "id", None),
            lifecycle_details=getattr(o, "lifecycle_details", None),
            lifecycle_state=getattr(o, "lifecycle_state", None),
            time_completed=getattr(o, "time_completed", None),
            time_started=getattr(o, "time_started", None),
            update_action=getattr(o, "update_action", None),
            update_id=getattr(o, "update_id", None),
            update_type=getattr(o, "update_type", None),
        )
