"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, Literal, Optional, List

import oci
from pydantic import BaseModel, Field


def _oci_to_dict(obj):
    """Best-effort conversion of OCI SDK model objects to plain dicts."""
    if obj is None:
        return None
    try:
        from oci.util import to_dict as oci_to_dict

        return oci_to_dict(obj)
    except Exception:
        pass
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return None


def _map_list(items, mapper):
    """
    Safely map a sequence of SDK items to a list of Pydantic models using a mapper function.
    Returns:
      - None if items is None
      - [] if items is an empty iterable
    """
    if items is None:
        return None
    try:
        return [mapper(it) for it in items]
    except Exception:
        out: list = []
        try:
            for it in items or []:
                out.append(mapper(it))
            return out
        except Exception:
            return None


class OCIBaseModel(BaseModel):
    """Base model that supports conversion from OCI SDK models."""

    model_config = {"arbitrary_types_allowed": True}


class ProtectedDatabaseHealthCounts(OCIBaseModel):
    """
    Aggregated counts of Protected Database health in a compartment/region scope.
    """
    compartment_id: Optional[str] = Field(
        None, alias="compartmentId", description="The OCID of the compartment summarized."
    )
    region: Optional[str] = Field(
        None, alias="region", description="The OCI region used for the query (if specified)."
    )
    protected: int = Field(
        0, alias="protected", description="Number of Protected Databases with health=PROTECTED."
    )
    warning: int = Field(
        0, alias="warning", description="Number of Protected Databases with health=WARNING."
    )
    alert: int = Field(
        0, alias="alert", description="Number of Protected Databases with health=ALERT."
    )
    total: int = Field(
        0, alias="total", description="Total counted (protected + warning + alert)."
    )


class ProtectedDatabaseRedoCounts(OCIBaseModel):
    """
    Aggregated counts of redo transport enablement for Protected Databases in a compartment/region scope.
    """
    compartment_id: Optional[str] = Field(
        None, alias="compartmentId", description="The OCID of the compartment summarized."
    )
    region: Optional[str] = Field(
        None, alias="region", description="The OCI region used for the query (if specified)."
    )
    enabled: int = Field(
        0, alias="enabled", description="Count of Protected Databases with is_redo_logs_enabled = True."
    )
    disabled: int = Field(
        0, alias="disabled", description="Count of Protected Databases with is_redo_logs_enabled = False."
    )
    total: int = Field(
        0, alias="total", description="Total counted (enabled + disabled)."
    )


class ProtectedDatabaseBackupSpaceSum(OCIBaseModel):
    """
    Sum of backup space used (GBs) across Protected Databases in a compartment/region scope.
    """
    compartment_id: Optional[str] = Field(
        None, alias="compartmentId", description="The OCID of the compartment summarized."
    )
    region: Optional[str] = Field(
        None, alias="region", description="The OCI region used for the query (if specified)."
    )
    total_databases_scanned: int = Field(
        0, alias="totalDatabasesScanned", description="Number of Protected Databases scanned."
    )
    sum_backup_space_used_in_gbs: float = Field(
        0.0,
        alias="sumBackupSpaceUsedInGBs",
        description="Sum of metrics.backup_space_used_in_gbs across all scanned Protected Databases.",
    )


# region ProtectedDatabase and nested types (oci.recovery.models)


class ProtectedDatabaseMetrics(OCIBaseModel):
    """
    Pydantic model mirroring metrics object nested under
    oci.recovery.models.ProtectedDatabase (if present).
    This captures commonly used fields and remains tolerant to service evolution.
    """

    backup_space_used_in_gbs: Optional[float] = Field(
        None,
        description="Total backup space used by this protected database in GBs.",
    )
    database_size_in_gbs: Optional[float] = Field(
        None, description="Logical database size in GBs, if reported."
    )
    recoverable_window_start_time: Optional[datetime] = Field(
        None, description="Start of recoverable window (RFC3339), if reported."
    )
    recoverable_window_end_time: Optional[datetime] = Field(
        None, description="End of recoverable window (RFC3339), if reported."
    )
    latest_backup_time: Optional[datetime] = Field(
        None, description="Time of the latest successful backup (RFC3339), if reported."
    )


class ProtectedDatabase(OCIBaseModel):
    """
    Pydantic model mirroring the fields of oci.recovery.models.ProtectedDatabase.

    This model includes commonly used attributes and remains permissive to
    additional fields by relying on Pydantic's default behavior to ignore extras.
    """

    id: Optional[str] = Field(None, description="The OCID of the Protected Database.")
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing this Protected Database."
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name for the Protected Database."
    )

    # Policy and networking attachments
    protection_policy_id: Optional[str] = Field(
        None, description="The OCID of the attached Protection Policy."
    )
    recovery_service_subnet_id: Optional[str] = Field(
        None, description="The OCID of the Recovery Service Subnet associated with this database."
    )

    # DB identification (may not always be present for all database types)
    database_id: Optional[str] = Field(
        None, description="The OCID of the backing database, where applicable."
    )
    db_unique_name: Optional[str] = Field(
        None, description="The DB_UNIQUE_NAME of the protected database, if available."
    )
    vpc_user_name: Optional[str] = Field(
        None, description="The VPC user name associated with the protected database, if available."
    )
    database_size: Optional[
        Literal["XS", "S", "M", "L", "XL", "XXL", "AUTO", "UNKNOWN_ENUM_VALUE"]
    ] = Field(
        None, description="Configured database size category for the protected database."
    )
    db_name: Optional[str] = Field(
        None, description="The database name, if available."
    )

    # Status and health
    lifecycle_state: Optional[
        Literal["CREATING", "ACTIVE", "UPDATING", "DELETE_SCHEDULED", "DELETING", "DELETED", "FAILED"]
    ] = Field(None, description="The current lifecycle state of the Protected Database.")
    lifecycle_details: Optional[str] = Field(
        None, description="Additional details about the current lifecycle state."
    )
    health: Optional[
        Literal["PROTECTED", "WARNING", "ALERT"]
    ] = Field(
        None,
        description="Service-evaluated health status: PROTECTED, WARNING, or ALERT.",
    )

    # Redo transport (for zero data loss RPO)
    is_redo_logs_enabled: Optional[bool] = Field(
        None, description="Whether redo transport is enabled for this Protected Database."
    )

    # Metrics
    metrics: Optional[ProtectedDatabaseMetrics] = Field(
        None, description="Metrics associated with this Protected Database."
    )

    # Timestamps
    time_created: Optional[datetime] = Field(
        None, description="The time the Protected Database was created (RFC3339)."
    )
    time_updated: Optional[datetime] = Field(
        None, description="The time the Protected Database was last updated (RFC3339)."
    )

    # Tags
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags for this resource."
    )
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="System tags for this resource."
    )


def map_protected_database_metrics(
    m,
) -> ProtectedDatabaseMetrics | None:
    """
    Convert nested metrics object to ProtectedDatabaseMetrics.
    Accepts either an OCI SDK model instance or plain dict, returns Pydantic model.
    """
    if not m:
        return None
    data = _oci_to_dict(m) or {}
    return ProtectedDatabaseMetrics(
        backup_space_used_in_gbs=getattr(m, "backup_space_used_in_gbs", None)
        or data.get("backup_space_used_in_gbs")
        or data.get("backupSpaceUsedInGbs"),
        database_size_in_gbs=getattr(m, "database_size_in_gbs", None)
        or data.get("database_size_in_gbs")
        or data.get("databaseSizeInGbs"),
        recoverable_window_start_time=getattr(m, "recoverable_window_start_time", None)
        or data.get("recoverable_window_start_time")
        or data.get("recoverableWindowStartTime"),
        recoverable_window_end_time=getattr(m, "recoverable_window_end_time", None)
        or data.get("recoverable_window_end_time")
        or data.get("recoverableWindowEndTime"),
        latest_backup_time=getattr(m, "latest_backup_time", None)
        or data.get("latest_backup_time")
        or data.get("latestBackupTime"),
    )


def map_protected_database(
    pd: "oci.recovery.models.ProtectedDatabase",
) -> ProtectedDatabase | None:
    """
    Convert an oci.recovery.models.ProtectedDatabase to
    oracle.oci_recovery_mcp_server.models.ProtectedDatabase,
    including nested metrics.
    """
    if pd is None:
        return None

    # Use getattr first; fall back to dict to be resilient to SDK variations.
    data = _oci_to_dict(pd) or {}

    return ProtectedDatabase(
        id=getattr(pd, "id", None) or data.get("id"),
        compartment_id=getattr(pd, "compartment_id", None) or data.get("compartment_id"),
        display_name=getattr(pd, "display_name", None) or data.get("display_name"),
        protection_policy_id=getattr(pd, "protection_policy_id", None)
        or data.get("protection_policy_id")
        or data.get("protectionPolicyId"),
        recovery_service_subnet_id=getattr(pd, "recovery_service_subnet_id", None)
        or data.get("recovery_service_subnet_id")
        or data.get("recoveryServiceSubnetId"),
        database_id=getattr(pd, "database_id", None) or data.get("database_id"),
        db_unique_name=getattr(pd, "db_unique_name", None) or data.get("db_unique_name"),
        db_name=getattr(pd, "db_name", None) or data.get("db_name"),
        lifecycle_state=getattr(pd, "lifecycle_state", None) or data.get("lifecycle_state"),
        lifecycle_details=getattr(pd, "lifecycle_details", None) or data.get("lifecycle_details"),
        health=getattr(pd, "health", None) or data.get("health"),
        is_redo_logs_enabled=getattr(pd, "is_redo_logs_enabled", None)
        or data.get("is_redo_logs_enabled")
        or data.get("isRedoLogsEnabled"),
        metrics=map_protected_database_metrics(
            getattr(pd, "metrics", None) or data.get("metrics")
        ),
        time_created=getattr(pd, "time_created", None) or data.get("time_created"),
        time_updated=getattr(pd, "time_updated", None) or data.get("time_updated"),
        freeform_tags=getattr(pd, "freeform_tags", None) or data.get("freeform_tags"),
        defined_tags=getattr(pd, "defined_tags", None) or data.get("defined_tags"),
        system_tags=getattr(pd, "system_tags", None) or data.get("system_tags"),
    )


# region RecoveryServiceSubnet and nested types (oci.recovery.models)


class RecoveryServiceSubnet(OCIBaseModel):
    """
    Pydantic model mirroring the fields of oci.recovery.models.RecoveryServiceSubnet.
    """

    id: Optional[str] = Field(
        None, description="The OCID of the Recovery Service Subnet (RSS)."
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the RSS."
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name for the RSS."
    )
    vcn_id: Optional[str] = Field(None, description="The OCID of the VCN.")
    subnet_id: Optional[str] = Field(None, description="The OCID of the subnet.")
    nsg_ids: Optional[List[str]] = Field(
        None, description="List of Network Security Group OCIDs attached to the RSS."
    )
    lifecycle_state: Optional[
        Literal["CREATING", "ACTIVE", "UPDATING", "DELETE_SCHEDULED", "DELETING", "DELETED", "FAILED"]
    ] = Field(None, description="The current lifecycle state of the RSS.")
    lifecycle_details: Optional[str] = Field(
        None, description="Additional details about the RSS lifecycle."
    )

    time_created: Optional[datetime] = Field(
        None, description="The time the RSS was created (RFC3339)."
    )
    time_updated: Optional[datetime] = Field(
        None, description="The time the RSS was last updated (RFC3339)."
    )

    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags for this resource."
    )
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="System tags for this resource."
    )


def map_recovery_service_subnet(
    rss: "oci.recovery.models.RecoveryServiceSubnet",
) -> RecoveryServiceSubnet | None:
    """
    Convert an oci.recovery.models.RecoveryServiceSubnet to
    oracle.oci_recovery_mcp_server.models.RecoveryServiceSubnet.
    """
    if rss is None:
        return None

    data = _oci_to_dict(rss) or {}

    # Attempt to normalize NSG IDs list from various sources
    nsgs = getattr(rss, "nsg_ids", None) or data.get("nsg_ids") or data.get("nsgIds")
    if nsgs is not None:
        try:
            nsgs = list(nsgs)
        except Exception:
            nsgs = None

    return RecoveryServiceSubnet(
        id=getattr(rss, "id", None) or data.get("id"),
        compartment_id=getattr(rss, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        display_name=getattr(rss, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        vcn_id=getattr(rss, "vcn_id", None) or data.get("vcn_id") or data.get("vcnId"),
        subnet_id=getattr(rss, "subnet_id", None)
        or data.get("subnet_id")
        or data.get("subnetId"),
        nsg_ids=nsgs,
        lifecycle_state=getattr(rss, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        lifecycle_details=getattr(rss, "lifecycle_details", None)
        or data.get("lifecycle_details")
        or data.get("lifecycleDetails"),
        time_created=getattr(rss, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
        time_updated=getattr(rss, "time_updated", None)
        or data.get("time_updated")
        or data.get("timeUpdated"),
        freeform_tags=getattr(rss, "freeform_tags", None)
        or data.get("freeform_tags")
        or data.get("freeformTags"),
        defined_tags=getattr(rss, "defined_tags", None)
        or data.get("defined_tags")
        or data.get("definedTags"),
        system_tags=getattr(rss, "system_tags", None)
        or data.get("system_tags")
        or data.get("systemTags"),
    )


# endregion

# region ProtectionPolicyCollection (oci.recovery.models)


class ProtectionPolicyCollection(OCIBaseModel):
    """
    Pydantic model mirroring oci.recovery.models.ProtectionPolicyCollection.
    """

    items: Optional[List["ProtectionPolicySummary"]] = Field(
        None, description="List of ProtectionPolicySummary items."
    )


def map_protection_policy_collection(
    coll: "oci.recovery.models.ProtectionPolicyCollection",
) -> ProtectionPolicyCollection | None:
    """
    Convert an oci.recovery.models.ProtectionPolicyCollection to
    oracle.oci_recovery_mcp_server.models.ProtectionPolicyCollection.
    """
    if coll is None:
        return None
    data = _oci_to_dict(coll) or {}
    items = getattr(coll, "items", None) or data.get("items")
    return ProtectionPolicyCollection(
        items=_map_list(items, map_protection_policy_summary)
    )


# endregion

# region ProtectedDatabase Summary and Collection


class ProtectedDatabaseSummary(OCIBaseModel):
    """
    Pydantic model mirroring the fields of oci.recovery.models.ProtectedDatabaseSummary.
    """

    id: Optional[str] = Field(None, description="The OCID of the Protected Database.")
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the Protected Database."
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name for the Protected Database."
    )
    protection_policy_id: Optional[str] = Field(
        None, description="The OCID of the attached Protection Policy."
    )
    recovery_service_subnet_id: Optional[str] = Field(
        None, description="The OCID of the Recovery Service Subnet associated with this database."
    )
    policy_locked_date_time: Optional[str] = Field(
        None, description="Timestamp when the protection policy was locked (RFC3339 string)."
    )
    recovery_service_subnets: Optional[List["RecoveryServiceSubnetDetails"]] = Field(
        None, description="List of Recovery Service Subnet details associated with this protected database."
    )
    database_id: Optional[str] = Field(
        None, description="The OCID of the backing database, where applicable."
    )
    db_unique_name: Optional[str] = Field(
        None, description="The DB_UNIQUE_NAME of the protected database, if available."
    )
    vpc_user_name: Optional[str] = Field(
        None, description="The VPC user name associated with the protected database, if available."
    )
    database_size: Optional[
        Literal["XS", "S", "M", "L", "XL", "XXL", "AUTO", "UNKNOWN_ENUM_VALUE"]
    ] = Field(
        None, description="Configured database size category."
    )
    db_name: Optional[str] = Field(None, description="The database name, if available.")
    lifecycle_state: Optional[
        Literal["CREATING", "ACTIVE", "UPDATING", "DELETE_SCHEDULED", "DELETING", "DELETED", "FAILED"]
    ] = Field(None, description="The current lifecycle state.")
    health: Optional[
        Literal["PROTECTED", "WARNING", "ALERT"]
    ] = Field(None, description="Health status.")
    lifecycle_details: Optional[str] = Field(
        None, description="Detailed description about the current lifecycle state of the protected database."
    )
    health_details: Optional[str] = Field(
        None, description="A message describing the current health of the protected database."
    )
    is_read_only_resource: Optional[bool] = Field(
        None, description="Indicates whether the protected database is created by the service (TRUE) or manually (FALSE)."
    )
    metrics: Optional["MetricsSummary"] = Field(
        None, description="Metrics summary associated with this protected database."
    )
    subscription_id: Optional[str] = Field(
        None, description="The OCID of the cloud service subscription linked to the protected database."
    )
    is_redo_logs_enabled: Optional[bool] = Field(
        None, description="Whether redo transport is enabled."
    )
    time_created: Optional[datetime] = Field(
        None, description="The time the Protected Database was created (RFC3339)."
    )
    time_updated: Optional[datetime] = Field(
        None, description="The time the Protected Database was last updated (RFC3339)."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags."
    )
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="System tags."
    )


def map_protected_database_summary(
    pds: "oci.recovery.models.ProtectedDatabaseSummary",
) -> ProtectedDatabaseSummary | None:
    if pds is None:
        return None
    data = _oci_to_dict(pds) or {}
    rss_in = getattr(pds, "recovery_service_subnets", None) or data.get("recovery_service_subnets") or data.get("recoveryServiceSubnets")
    return ProtectedDatabaseSummary(
        id=getattr(pds, "id", None) or data.get("id"),
        compartment_id=getattr(pds, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        display_name=getattr(pds, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        protection_policy_id=getattr(pds, "protection_policy_id", None)
        or data.get("protection_policy_id")
        or data.get("protectionPolicyId"),
        policy_locked_date_time=getattr(pds, "policy_locked_date_time", None)
        or data.get("policy_locked_date_time")
        or data.get("policyLockedDateTime"),
        recovery_service_subnets=_map_list(rss_in, map_recovery_service_subnet_details),
        recovery_service_subnet_id=getattr(pds, "recovery_service_subnet_id", None)
        or data.get("recovery_service_subnet_id")
        or data.get("recoveryServiceSubnetId"),
        database_id=getattr(pds, "database_id", None)
        or data.get("database_id")
        or data.get("databaseId"),
        db_unique_name=getattr(pds, "db_unique_name", None)
        or data.get("db_unique_name")
        or data.get("dbUniqueName"),
        vpc_user_name=getattr(pds, "vpc_user_name", None)
        or data.get("vpc_user_name")
        or data.get("vpcUserName"),
        database_size=getattr(pds, "database_size", None)
        or data.get("database_size")
        or data.get("databaseSize"),
        db_name=getattr(pds, "db_name", None) or data.get("db_name"),
        lifecycle_state=getattr(pds, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        lifecycle_details=getattr(pds, "lifecycle_details", None)
        or data.get("lifecycle_details")
        or data.get("lifecycleDetails"),
        health=getattr(pds, "health", None) or data.get("health"),
        health_details=getattr(pds, "health_details", None)
        or data.get("health_details")
        or data.get("healthDetails"),
        is_read_only_resource=getattr(pds, "is_read_only_resource", None)
        or data.get("is_read_only_resource")
        or data.get("isReadOnlyResource"),
        is_redo_logs_enabled=getattr(pds, "is_redo_logs_enabled", None)
        or data.get("is_redo_logs_enabled")
        or data.get("isRedoLogsEnabled"),
        metrics=map_metrics_summary(getattr(pds, "metrics", None) or data.get("metrics")),
        subscription_id=getattr(pds, "subscription_id", None)
        or data.get("subscription_id")
        or data.get("subscriptionId"),
        time_created=getattr(pds, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
        time_updated=getattr(pds, "time_updated", None)
        or data.get("time_updated")
        or data.get("timeUpdated"),
        freeform_tags=getattr(pds, "freeform_tags", None)
        or data.get("freeform_tags")
        or data.get("freeformTags"),
        defined_tags=getattr(pds, "defined_tags", None)
        or data.get("defined_tags")
        or data.get("definedTags"),
        system_tags=getattr(pds, "system_tags", None)
        or data.get("system_tags")
        or data.get("systemTags"),
    )


class ProtectedDatabaseCollection(OCIBaseModel):
    """
    Pydantic model mirroring oci.recovery.models.ProtectedDatabaseCollection.
    """

    items: Optional[List[ProtectedDatabaseSummary]] = Field(
        None, description="List of ProtectedDatabaseSummary items."
    )


def map_protected_database_collection(
    coll: "oci.recovery.models.ProtectedDatabaseCollection",
) -> ProtectedDatabaseCollection | None:
    if coll is None:
        return None
    data = _oci_to_dict(coll) or {}
    items = getattr(coll, "items", None) or data.get("items")
    return ProtectedDatabaseCollection(
        items=_map_list(items, map_protected_database_summary)
    )


# endregion


# region RecoveryServiceSubnet Details/Input/Summary/Collection


class RecoveryServiceSubnetDetails(OCIBaseModel):
    """
    Pydantic model mirroring oci.recovery.models.RecoveryServiceSubnetDetails.
    Represents a detailed view of RSS properties.
    """

    id: Optional[str] = Field(None, description="The OCID of the RSS.")
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the RSS."
    )
    display_name: Optional[str] = Field(None, description="A user-friendly name.")
    vcn_id: Optional[str] = Field(None, description="The OCID of the VCN.")
    subnet_id: Optional[str] = Field(None, description="The OCID of the subnet.")
    nsg_ids: Optional[List[str]] = Field(
        None, description="List of NSG OCIDs associated to the RSS."
    )
    lifecycle_state: Optional[
        Literal["CREATING", "ACTIVE", "UPDATING", "DELETING", "DELETED", "FAILED"]
    ] = Field(None, description="The current lifecycle state.")
    lifecycle_details: Optional[str] = Field(
        None, description="Additional lifecycle details."
    )
    time_created: Optional[datetime] = Field(
        None, description="Creation time (RFC3339)."
    )
    time_updated: Optional[datetime] = Field(
        None, description="Last update time (RFC3339)."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(None, description="Free-form tags.")
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags."
    )
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="System tags."
    )


def map_recovery_service_subnet_details(
    det: "oci.recovery.models.RecoveryServiceSubnetDetails",
) -> RecoveryServiceSubnetDetails | None:
    if det is None:
        return None
    data = _oci_to_dict(det) or {}
    nsgs = getattr(det, "nsg_ids", None) or data.get("nsg_ids") or data.get("nsgIds")
    if nsgs is not None:
        try:
            nsgs = list(nsgs)
        except Exception:
            nsgs = None
    return RecoveryServiceSubnetDetails(
        id=getattr(det, "id", None) or data.get("id"),
        compartment_id=getattr(det, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        display_name=getattr(det, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        vcn_id=getattr(det, "vcn_id", None) or data.get("vcn_id") or data.get("vcnId"),
        subnet_id=getattr(det, "subnet_id", None)
        or data.get("subnet_id")
        or data.get("subnetId"),
        nsg_ids=nsgs,
        lifecycle_state=getattr(det, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        lifecycle_details=getattr(det, "lifecycle_details", None)
        or data.get("lifecycle_details")
        or data.get("lifecycleDetails"),
        time_created=getattr(det, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
        time_updated=getattr(det, "time_updated", None)
        or data.get("time_updated")
        or data.get("timeUpdated"),
        freeform_tags=getattr(det, "freeform_tags", None)
        or data.get("freeform_tags")
        or data.get("freeformTags"),
        defined_tags=getattr(det, "defined_tags", None)
        or data.get("defined_tags")
        or data.get("definedTags"),
        system_tags=getattr(det, "system_tags", None)
        or data.get("system_tags")
        or data.get("systemTags"),
    )


class RecoveryServiceSubnetInput(OCIBaseModel):
    """
    Pydantic model mirroring oci.recovery.models.RecoveryServiceSubnetInput.
    Represents the payload to create/update a Recovery Service Subnet.
    """

    display_name: Optional[str] = Field(
        None, description="A user-friendly name for the RSS."
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment for the RSS."
    )
    vcn_id: Optional[str] = Field(None, description="The OCID of the VCN.")
    subnet_id: Optional[str] = Field(None, description="The OCID of the subnet.")
    nsg_ids: Optional[List[str]] = Field(
        None, description="List of NSG OCIDs to associate."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(None, description="Free-form tags.")
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags."
    )


def map_recovery_service_subnet_input(
    inp: "oci.recovery.models.RecoveryServiceSubnetInput",
) -> RecoveryServiceSubnetInput | None:
    if inp is None:
        return None
    data = _oci_to_dict(inp) or {}
    nsgs = getattr(inp, "nsg_ids", None) or data.get("nsg_ids") or data.get("nsgIds")
    if nsgs is not None:
        try:
            nsgs = list(nsgs)
        except Exception:
            nsgs = None
    return RecoveryServiceSubnetInput(
        display_name=getattr(inp, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        compartment_id=getattr(inp, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        vcn_id=getattr(inp, "vcn_id", None) or data.get("vcn_id") or data.get("vcnId"),
        subnet_id=getattr(inp, "subnet_id", None)
        or data.get("subnet_id")
        or data.get("subnetId"),
        nsg_ids=nsgs,
        freeform_tags=getattr(inp, "freeform_tags", None)
        or data.get("freeform_tags")
        or data.get("freeformTags"),
        defined_tags=getattr(inp, "defined_tags", None)
        or data.get("defined_tags")
        or data.get("definedTags"),
    )


class RecoveryServiceSubnetSummary(OCIBaseModel):
    """
    Pydantic model mirroring oci.recovery.models.RecoveryServiceSubnetSummary.
    """

    id: Optional[str] = Field(None, description="The OCID of the RSS.")
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the RSS."
    )
    display_name: Optional[str] = Field(None, description="A user-friendly name.")
    vcn_id: Optional[str] = Field(None, description="The OCID of the VCN.")
    subnet_id: Optional[str] = Field(None, description="The OCID of the subnet.")
    nsg_ids: Optional[List[str]] = Field(None, description="List of NSG OCIDs.")
    lifecycle_state: Optional[
        Literal["CREATING", "ACTIVE", "UPDATING", "DELETING", "DELETED", "FAILED"]
    ] = Field(None, description="The current lifecycle state.")
    time_created: Optional[datetime] = Field(
        None, description="Creation time (RFC3339)."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(None, description="Free-form tags.")
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags."
    )
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="System tags."
    )


def map_recovery_service_subnet_summary(
    rss: "oci.recovery.models.RecoveryServiceSubnetSummary",
) -> RecoveryServiceSubnetSummary | None:
    if rss is None:
        return None
    data = _oci_to_dict(rss) or {}
    nsgs = getattr(rss, "nsg_ids", None) or data.get("nsg_ids") or data.get("nsgIds")
    if nsgs is not None:
        try:
            nsgs = list(nsgs)
        except Exception:
            nsgs = None
    return RecoveryServiceSubnetSummary(
        id=getattr(rss, "id", None) or data.get("id"),
        compartment_id=getattr(rss, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        display_name=getattr(rss, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        vcn_id=getattr(rss, "vcn_id", None) or data.get("vcn_id") or data.get("vcnId"),
        subnet_id=getattr(rss, "subnet_id", None)
        or data.get("subnet_id")
        or data.get("subnetId"),
        nsg_ids=nsgs,
        lifecycle_state=getattr(rss, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        time_created=getattr(rss, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
        freeform_tags=getattr(rss, "freeform_tags", None)
        or data.get("freeform_tags")
        or data.get("freeformTags"),
        defined_tags=getattr(rss, "defined_tags", None)
        or data.get("defined_tags")
        or data.get("definedTags"),
        system_tags=getattr(rss, "system_tags", None)
        or data.get("system_tags")
        or data.get("systemTags"),
    )


class RecoveryServiceSubnetCollection(OCIBaseModel):
    """
    Pydantic model mirroring oci.recovery.models.RecoveryServiceSubnetCollection.
    """

    items: Optional[List[RecoveryServiceSubnetSummary]] = Field(
        None, description="List of RecoveryServiceSubnetSummary items."
    )


def map_recovery_service_subnet_collection(
    coll: "oci.recovery.models.RecoveryServiceSubnetCollection",
) -> RecoveryServiceSubnetCollection | None:
    if coll is None:
        return None
    data = _oci_to_dict(coll) or {}
    items = getattr(coll, "items", None) or data.get("items")
    return RecoveryServiceSubnetCollection(
        items=_map_list(items, map_recovery_service_subnet_summary)
    )


# endregion

# region Metrics and MetricsSummary (oci.recovery.models)


class Metrics(OCIBaseModel):
    """
    Pydantic model mirroring oci.recovery.models.Metrics.
    Captures common Recovery metrics fields and remains tolerant to service evolution.
    """

    backup_space_used_in_gbs: Optional[float] = Field(
        None, description="Total backup space used in GBs."
    )
    database_size_in_gbs: Optional[float] = Field(
        None, description="Logical database size in GBs, if reported."
    )
    recoverable_window_start_time: Optional[datetime] = Field(
        None, description="Start of recoverable window (RFC3339), if reported."
    )
    recoverable_window_end_time: Optional[datetime] = Field(
        None, description="End of recoverable window (RFC3339), if reported."
    )
    latest_backup_time: Optional[datetime] = Field(
        None, description="Time of the latest successful backup (RFC3339), if reported."
    )


def map_metrics(m) -> Metrics | None:
    """
    Convert an oci.recovery.models.Metrics (or dict-like) to Metrics.
    """
    if not m:
        return None
    data = _oci_to_dict(m) or {}
    return Metrics(
        backup_space_used_in_gbs=getattr(m, "backup_space_used_in_gbs", None)
        or data.get("backup_space_used_in_gbs")
        or data.get("backupSpaceUsedInGbs"),
        database_size_in_gbs=getattr(m, "database_size_in_gbs", None)
        or data.get("database_size_in_gbs")
        or data.get("databaseSizeInGbs"),
        recoverable_window_start_time=getattr(
            m, "recoverable_window_start_time", None
        )
        or data.get("recoverable_window_start_time")
        or data.get("recoverableWindowStartTime"),
        recoverable_window_end_time=getattr(m, "recoverable_window_end_time", None)
        or data.get("recoverable_window_end_time")
        or data.get("recoverableWindowEndTime"),
        latest_backup_time=getattr(m, "latest_backup_time", None)
        or data.get("latest_backup_time")
        or data.get("latestBackupTime"),
    )


class MetricsSummary(OCIBaseModel):
    """
    Pydantic model mirroring oci.recovery.models.MetricsSummary.
    Contains a summarized view of recovery metrics over a period or scope.
    """

    backup_space_used_in_gbs: Optional[float] = Field(
        None, description="Total backup space used in GBs for the scope of the summary."
    )
    database_size_in_gbs: Optional[float] = Field(
        None, description="Logical database size in GBs for the scope of the summary."
    )
    recoverable_window_start_time: Optional[datetime] = Field(
        None,
        description="Start of recoverable window (RFC3339) covered by the summary, if reported.",
    )
    recoverable_window_end_time: Optional[datetime] = Field(
        None,
        description="End of recoverable window (RFC3339) covered by the summary, if reported.",
    )
    latest_backup_time: Optional[datetime] = Field(
        None,
        description="Time of the latest successful backup (RFC3339) in the summary window, if reported.",
    )


def map_metrics_summary(ms) -> MetricsSummary | None:
    """
    Convert an oci.recovery.models.MetricsSummary (or dict-like) to MetricsSummary.
    """
    if not ms:
        return None
    data = _oci_to_dict(ms) or {}
    return MetricsSummary(
        backup_space_used_in_gbs=getattr(ms, "backup_space_used_in_gbs", None)
        or data.get("backup_space_used_in_gbs")
        or data.get("backupSpaceUsedInGbs"),
        database_size_in_gbs=getattr(ms, "database_size_in_gbs", None)
        or data.get("database_size_in_gbs")
        or data.get("databaseSizeInGbs"),
        recoverable_window_start_time=getattr(
            ms, "recoverable_window_start_time", None
        )
        or data.get("recoverable_window_start_time")
        or data.get("recoverableWindowStartTime"),
        recoverable_window_end_time=getattr(ms, "recoverable_window_end_time", None)
        or data.get("recoverable_window_end_time")
        or data.get("recoverableWindowEndTime"),
        latest_backup_time=getattr(ms, "latest_backup_time", None)
        or data.get("latest_backup_time")
        or data.get("latestBackupTime"),
    )


# endregion

# region ProtectionPolicy (full) (oci.recovery.models)


class ProtectionPolicy(OCIBaseModel):
    """
    Pydantic model mirroring the fields of oci.recovery.models.ProtectionPolicy.
    Named ProtectionPolicy here as requested.
    """

    id: Optional[str] = Field(
        None, description="The OCID of the protection policy."
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name for the protection policy."
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the protection policy."
    )
    backup_retention_period_in_days: Optional[int] = Field(
        None, description="Exact number of days to retain backups created by Recovery Service."
    )
    is_predefined_policy: Optional[bool] = Field(
        None, description="Whether this is an Oracle-defined predefined policy."
    )
    policy_locked_date_time: Optional[str] = Field(
        None, description="When the protection policy was locked (RFC3339 string)."
    )
    must_enforce_cloud_locality: Optional[bool] = Field(
        None, description="Whether backup storage must stay in the same cloud locality as the database."
    )
    time_created: Optional[datetime] = Field(
        None, description="The time the protection policy was created (RFC3339)."
    )
    time_updated: Optional[datetime] = Field(
        None, description="The time the protection policy was last updated (RFC3339)."
    )
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "UPDATING",
            "ACTIVE",
            "DELETE_SCHEDULED",
            "DELETING",
            "DELETED",
            "FAILED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The current lifecycle state of the protection policy.")
    lifecycle_details: Optional[str] = Field(
        None, description="Additional details about the current lifecycle state."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags for this resource."
    )
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="System tags for this resource."
    )


def map_protection_policy(
    pp: "oci.recovery.models.ProtectionPolicy",
) -> ProtectionPolicy | None:
    """
    Convert an oci.recovery.models.ProtectionPolicy (aka ProtectionPolicy here) to
    oracle.oci_recovery_mcp_server.models.ProtectionPolicy.
    """
    if pp is None:
        return None

    data = _oci_to_dict(pp) or {}

    return ProtectionPolicy(
        id=getattr(pp, "id", None) or data.get("id"),
        display_name=getattr(pp, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        compartment_id=getattr(pp, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        backup_retention_period_in_days=getattr(
            pp, "backup_retention_period_in_days", None
        )
        or data.get("backup_retention_period_in_days")
        or data.get("backupRetentionPeriodInDays"),
        is_predefined_policy=getattr(pp, "is_predefined_policy", None)
        or data.get("is_predefined_policy")
        or data.get("isPredefinedPolicy"),
        policy_locked_date_time=getattr(pp, "policy_locked_date_time", None)
        or data.get("policy_locked_date_time")
        or data.get("policyLockedDateTime"),
        must_enforce_cloud_locality=getattr(
            pp, "must_enforce_cloud_locality", None
        )
        or data.get("must_enforce_cloud_locality")
        or data.get("mustEnforceCloudLocality"),
        time_created=getattr(pp, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
        time_updated=getattr(pp, "time_updated", None)
        or data.get("time_updated")
        or data.get("timeUpdated"),
        lifecycle_state=getattr(pp, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        lifecycle_details=getattr(pp, "lifecycle_details", None)
        or data.get("lifecycle_details")
        or data.get("lifecycleDetails"),
        freeform_tags=getattr(pp, "freeform_tags", None)
        or data.get("freeform_tags")
        or data.get("freeformTags"),
        defined_tags=getattr(pp, "defined_tags", None)
        or data.get("defined_tags")
        or data.get("definedTags"),
        system_tags=getattr(pp, "system_tags", None)
        or data.get("system_tags")
        or data.get("systemTags"),
    )


# region ProtectionPolicySummary (oci.recovery.models)


class ProtectionPolicySummary(OCIBaseModel):
    """
    Pydantic model mirroring oci.recovery.models.ProtectionPolicySummary.
    """

    id: Optional[str] = Field(
        None, description="The OCID of the protection policy."
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name for the protection policy."
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the protection policy."
    )
    backup_retention_period_in_days: Optional[int] = Field(
        None, description="Exact number of days to retain backups created by Recovery Service."
    )
    is_predefined_policy: Optional[bool] = Field(
        None, description="Whether this is an Oracle-defined predefined policy."
    )
    policy_locked_date_time: Optional[str] = Field(
        None, description="When the protection policy was locked (RFC3339 string)."
    )
    must_enforce_cloud_locality: Optional[bool] = Field(
        None, description="Whether backup storage must stay in the same cloud locality as the database."
    )
    time_created: Optional[datetime] = Field(
        None, description="The time the protection policy was created (RFC3339)."
    )
    time_updated: Optional[datetime] = Field(
        None, description="The time the protection policy was last updated (RFC3339)."
    )
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "UPDATING",
            "ACTIVE",
            "DELETE_SCHEDULED",
            "DELETING",
            "DELETED",
            "FAILED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The current lifecycle state of the protection policy.")
    lifecycle_details: Optional[str] = Field(
        None, description="Additional details about the current lifecycle state."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags for this resource."
    )
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="System tags for this resource."
    )


def map_protection_policy_summary(
    pps: "oci.recovery.models.ProtectionPolicySummary",
) -> ProtectionPolicySummary | None:
    """
    Convert an oci.recovery.models.ProtectionPolicySummary to
    oracle.oci_recovery_mcp_server.models.ProtectionPolicySummary.
    """
    if pps is None:
        return None

    data = _oci_to_dict(pps) or {}

    return ProtectionPolicySummary(
        id=getattr(pps, "id", None) or data.get("id"),
        display_name=getattr(pps, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        compartment_id=getattr(pps, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        backup_retention_period_in_days=getattr(
            pps, "backup_retention_period_in_days", None
        )
        or data.get("backup_retention_period_in_days")
        or data.get("backupRetentionPeriodInDays"),
        is_predefined_policy=getattr(pps, "is_predefined_policy", None)
        or data.get("is_predefined_policy")
        or data.get("isPredefinedPolicy"),
        policy_locked_date_time=getattr(pps, "policy_locked_date_time", None)
        or data.get("policy_locked_date_time")
        or data.get("policyLockedDateTime"),
        must_enforce_cloud_locality=getattr(
            pps, "must_enforce_cloud_locality", None
        )
        or data.get("must_enforce_cloud_locality")
        or data.get("mustEnforceCloudLocality"),
        time_created=getattr(pps, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
        time_updated=getattr(pps, "time_updated", None)
        or data.get("time_updated")
        or data.get("timeUpdated"),
        lifecycle_state=getattr(pps, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        lifecycle_details=getattr(pps, "lifecycle_details", None)
        or data.get("lifecycle_details")
        or data.get("lifecycleDetails"),
        freeform_tags=getattr(pps, "freeform_tags", None)
        or data.get("freeform_tags")
        or data.get("freeformTags"),
        defined_tags=getattr(pps, "defined_tags", None)
        or data.get("defined_tags")
        or data.get("definedTags"),
        system_tags=getattr(pps, "system_tags", None)
        or data.get("system_tags")
        or data.get("systemTags"),
    )


# endregion
