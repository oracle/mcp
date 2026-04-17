"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import oci
from pydantic import BaseModel, Field

# type aliases to keep line lengths within flake8 limits
HealthStatus = Literal["PROTECTED", "WARNING", "ALERT", "UNKNOWN_ENUM_VALUE"]


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


def _first_not_none(*values):
    """
    Return the first value that is not None.
    Important for preserving falsy-but-valid values like False, 0, or empty containers.
    """
    for v in values:
        if v is not None:
            return v
    return None


class OCIBaseModel(BaseModel):
    """Base model that supports conversion from OCI SDK models."""

    model_config = {"arbitrary_types_allowed": True}


class ProtectedDatabaseHealthCounts(OCIBaseModel):
    """
    Aggregated counts of Protected Database health in a compartment/region scope.
    """

    compartment_id: Optional[str] = Field(
        None,
        alias="compartmentId",
        description="The OCID of the compartment summarized.",
    )
    region: Optional[str] = Field(
        None,
        alias="region",
        description="The OCI region used for the query (if specified).",
    )
    protected: int = Field(
        0,
        alias="protected",
        description="Number of Protected Databases with health=PROTECTED.",
    )
    warning: int = Field(
        0,
        alias="warning",
        description="Number of Protected Databases with health=WARNING.",
    )
    alert: int = Field(
        0, alias="alert", description="Number of Protected Databases with health=ALERT."
    )
    unknown: int = Field(
        0,
        alias="unknown",
        description=(
            "Number of Protected Databases with unknown or missing health "
            "(e.g., DELETED or transitional)."
        ),
    )
    total: int = Field(
        0, alias="total", description="Total Protected Databases scanned."
    )


class ProtectedDatabaseRedoCounts(OCIBaseModel):
    """
    Aggregated counts of redo transport enablement for Protected Databases in a compartment/region scope.
    """

    compartment_id: Optional[str] = Field(
        None,
        alias="compartmentId",
        description="The OCID of the compartment summarized.",
    )
    region: Optional[str] = Field(
        None,
        alias="region",
        description="The OCI region used for the query (if specified).",
    )
    enabled: int = Field(
        0,
        alias="enabled",
        description="Count of Protected Databases with is_redo_logs_enabled = True.",
    )
    disabled: int = Field(
        0,
        alias="disabled",
        description="Count of Protected Databases with is_redo_logs_enabled = False.",
    )
    total: int = Field(
        0, alias="total", description="Total counted (enabled + disabled)."
    )


class ProtectedDatabaseBackupSpaceSum(OCIBaseModel):
    """
    Simplified summary of backup space used across Protected Databases.
    """

    compartment_id: Optional[str] = Field(None, alias="compartmentId")
    region: Optional[str] = Field(None, alias="region")
    total_databases_scanned: int = Field(0, alias="totalDatabasesScanned")
    sum_backup_space_used_in_gbs: float = Field(0.0, alias="sumBackupSpaceUsedInGBs")


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
        None,
        description="The OCID of the compartment containing this Protected Database.",
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name for the Protected Database."
    )

    # Policy and networking attachments
    protection_policy_id: Optional[str] = Field(
        None, description="The OCID of the attached Protection Policy."
    )
    policy_locked_date_time: Optional[str] = Field(
        None,
        description=(
            "When the protection policy retention lock is scheduled to take effect "
            "(RFC3339 string)."
        ),
    )
    recovery_service_subnets: Optional[List["RecoveryServiceSubnetDetails"]] = Field(
        None,
        description="List of Recovery Service Subnet resources associated with this protected database.",
    )

    # DB identification (may not always be present for all database types)
    database_id: Optional[str] = Field(
        None, description="The OCID of the backing database, where applicable."
    )
    db_unique_name: Optional[str] = Field(
        None, description="The DB_UNIQUE_NAME of the protected database, if available."
    )
    vpc_user_name: Optional[str] = Field(
        None,
        description="The VPC user name associated with the protected database, if available.",
    )
    database_size: Optional[
        Literal["XS", "S", "M", "L", "XL", "XXL", "AUTO", "UNKNOWN_ENUM_VALUE"]
    ] = Field(
        None,
        description="Configured database size category for the protected database.",
    )
    database_size_in_gbs: Optional[int] = Field(
        None,
        description="The size of the database in gigabytes, if reported by the service.",
    )
    change_rate: Optional[float] = Field(
        None,
        description="Percentage of data change between successive incremental backups.",
    )
    compression_ratio: Optional[float] = Field(
        None, description="Compression ratio (compressed size to expanded size)."
    )

    # Status and health
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "ACTIVE",
            "UPDATING",
            "DELETE_SCHEDULED",
            "DELETING",
            "DELETED",
            "FAILED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(
        None, description="The current lifecycle state of the Protected Database."
    )
    lifecycle_details: Optional[str] = Field(
        None, description="Additional details about the current lifecycle state."
    )
    health_details: Optional[str] = Field(
        None,
        description="A message describing the current health of the protected database.",
    )
    is_read_only_resource: Optional[bool] = Field(
        None,
        description=(
            "Indicates whether the protected database is created by Recovery Service "
            "(TRUE) or manually (FALSE)."
        ),
    )
    health: Optional[HealthStatus] = Field(
        None,
        description="Service-evaluated health status: PROTECTED, WARNING, or ALERT.",
    )

    # Redo transport (for zero data loss RPO)
    is_redo_logs_shipped: Optional[bool] = Field(
        None,
        description=(
            "Whether real-time redo shipping to Recovery Service is enabled "
            "(SDK: is_redo_logs_shipped)."
        ),
    )

    # Metrics
    metrics: Optional["Metrics"] = Field(
        None, description="Metrics associated with this Protected Database."
    )
    subscription_id: Optional[str] = Field(
        None,
        description="The OCID of the cloud service subscription linked to the protected database.",
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

    # Preserve empty list for recovery_service_subnets if present (avoid treating [] as falsy)
    rss_in = getattr(pd, "recovery_service_subnets", None)
    if rss_in is None:
        rss_in = data.get("recovery_service_subnets")
    if rss_in is None:
        rss_in = data.get("recoveryServiceSubnets")

    return ProtectedDatabase(
        id=getattr(pd, "id", None) or data.get("id"),
        compartment_id=getattr(pd, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        display_name=getattr(pd, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        protection_policy_id=getattr(pd, "protection_policy_id", None)
        or data.get("protection_policy_id")
        or data.get("protectionPolicyId"),
        policy_locked_date_time=getattr(pd, "policy_locked_date_time", None)
        or data.get("policy_locked_date_time")
        or data.get("policyLockedDateTime"),
        recovery_service_subnets=_map_list(
            rss_in,
            map_recovery_service_subnet_details,
        ),
        database_id=getattr(pd, "database_id", None)
        or data.get("database_id")
        or data.get("databaseId"),
        db_unique_name=getattr(pd, "db_unique_name", None)
        or data.get("db_unique_name"),
        vpc_user_name=getattr(pd, "vpc_user_name", None) or data.get("vpc_user_name"),
        database_size=getattr(pd, "database_size", None)
        or data.get("database_size")
        or data.get("databaseSize"),
        database_size_in_gbs=(
            getattr(pd, "database_size_in_gbs", None)
            or data.get("database_size_in_gbs")
            or data.get("databaseSizeInGBs")
            or data.get("databaseSizeInGbs")
        ),
        change_rate=(
            getattr(pd, "change_rate", None)
            or data.get("change_rate")
            or data.get("changeRate")
        ),
        compression_ratio=(
            getattr(pd, "compression_ratio", None)
            or data.get("compression_ratio")
            or data.get("compressionRatio")
        ),
        lifecycle_state=getattr(pd, "lifecycle_state", None)
        or data.get("lifecycle_state"),
        lifecycle_details=getattr(pd, "lifecycle_details", None)
        or data.get("lifecycle_details")
        or data.get("lifecycleDetails"),
        health_details=getattr(pd, "health_details", None)
        or data.get("health_details")
        or data.get("healthDetails"),
        is_read_only_resource=getattr(pd, "is_read_only_resource", None)
        or data.get("is_read_only_resource")
        or data.get("isReadOnlyResource"),
        health=getattr(pd, "health", None) or data.get("health"),
        is_redo_logs_shipped=(
            getattr(pd, "is_redo_logs_shipped", None)
            or data.get("is_redo_logs_shipped")
            or data.get("isRedoLogsShipped")
        ),
        metrics=map_metrics(getattr(pd, "metrics", None) or data.get("metrics")),
        subscription_id=getattr(pd, "subscription_id", None)
        or data.get("subscription_id")
        or data.get("subscriptionId"),
        time_created=getattr(pd, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
        time_updated=getattr(pd, "time_updated", None)
        or data.get("time_updated")
        or data.get("timeUpdated"),
        freeform_tags=getattr(pd, "freeform_tags", None)
        or data.get("freeform_tags")
        or data.get("freeformTags"),
        defined_tags=getattr(pd, "defined_tags", None)
        or data.get("defined_tags")
        or data.get("definedTags"),
        system_tags=getattr(pd, "system_tags", None)
        or data.get("system_tags")
        or data.get("systemTags"),
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
        Literal[
            "CREATING",
            "ACTIVE",
            "UPDATING",
            "DELETE_SCHEDULED",
            "DELETING",
            "DELETED",
            "FAILED",
        ]
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
    subnets: Optional[List[str]] = Field(
        None,
        description="List of subnet OCIDs associated with this RSS (matches OCI CLI 'subnets').",
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

    def _normalize_subnets(val):
        if val is None:
            return None
        out = []
        try:
            for it in val or []:
                if isinstance(it, str):
                    out.append(it)
                elif isinstance(it, dict):
                    ocid = (
                        it.get("id")
                        or it.get("ocid")
                        or it.get("subnetId")
                        or it.get("subnet_id")
                    )
                    if ocid:
                        out.append(ocid)
        except Exception:
            return None
        return out if out else None

    # Normalize primary identifiers for VCN/subnet and ensure 'subnets' includes subnet_id when list is absent
    vcn_id_val = getattr(rss, "vcn_id", None) or data.get("vcn_id") or data.get("vcnId")
    subnet_id_val = (
        getattr(rss, "subnet_id", None) or data.get("subnet_id") or data.get("subnetId")
    )
    subnets_val = _normalize_subnets(data.get("subnets")) or (
        [subnet_id_val] if subnet_id_val else None
    )

    return RecoveryServiceSubnet(
        id=getattr(rss, "id", None) or data.get("id"),
        compartment_id=getattr(rss, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        display_name=getattr(rss, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        vcn_id=vcn_id_val,
        subnet_id=subnet_id_val,
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
        subnets=subnets_val,
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
        None,
        description="The OCID of the compartment containing the Protected Database.",
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name for the Protected Database."
    )
    protection_policy_id: Optional[str] = Field(
        None, description="The OCID of the attached Protection Policy."
    )
    policy_locked_date_time: Optional[str] = Field(
        None,
        description="Timestamp when the protection policy was locked (RFC3339 string).",
    )
    recovery_service_subnets: Optional[List["RecoveryServiceSubnetDetails"]] = Field(
        None,
        description=(
            "List of Recovery Service Subnet details associated with this "
            "protected database."
        ),
    )
    database_id: Optional[str] = Field(
        None, description="The OCID of the backing database, where applicable."
    )
    db_unique_name: Optional[str] = Field(
        None, description="The DB_UNIQUE_NAME of the protected database, if available."
    )
    vpc_user_name: Optional[str] = Field(
        None,
        description="The VPC user name associated with the protected database, if available.",
    )
    database_size: Optional[
        Literal["XS", "S", "M", "L", "XL", "XXL", "AUTO", "UNKNOWN_ENUM_VALUE"]
    ] = Field(
        None,
        description="Configured database size category for the protected database.",
    )
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "ACTIVE",
            "UPDATING",
            "DELETE_SCHEDULED",
            "DELETING",
            "DELETED",
            "FAILED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The current lifecycle state.")
    health: Optional[HealthStatus] = Field(None, description="Health status.")
    lifecycle_details: Optional[str] = Field(
        None,
        description="Detailed description about the current lifecycle state of the protected database.",
    )
    health_details: Optional[str] = Field(
        None,
        description="A message describing the current health of the protected database.",
    )
    is_read_only_resource: Optional[bool] = Field(
        None,
        description="Indicates whether the protected database is created by the service (TRUE) "
        "or manually (FALSE).",
    )
    metrics: Optional["MetricsSummary"] = Field(
        None, description="Metrics summary associated with this protected database."
    )
    subscription_id: Optional[str] = Field(
        None,
        description="The OCID of the cloud service subscription linked to the protected database.",
    )
    time_created: Optional[datetime] = Field(
        None, description="The time the Protected Database was created (RFC3339)."
    )
    time_updated: Optional[datetime] = Field(
        None, description="The time the Protected Database was last updated (RFC3339)."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(None, description="Free-form tags.")
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
    # Preserve empty list vs None for recovery_service_subnets
    rss_in = getattr(pds, "recovery_service_subnets", None)
    if rss_in is None:
        rss_in = data.get("recovery_service_subnets")
    if rss_in is None:
        rss_in = data.get("recoveryServiceSubnets")
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
        database_id=getattr(pds, "database_id", None)
        or data.get("database_id")
        or data.get("databaseId"),
        db_unique_name=(
            getattr(pds, "db_unique_name", None)
            or data.get("db_unique_name")
            or data.get("dbUniqueName")
        ),
        vpc_user_name=getattr(pds, "vpc_user_name", None)
        or data.get("vpc_user_name")
        or data.get("vpcUserName"),
        database_size=getattr(pds, "database_size", None)
        or data.get("database_size")
        or data.get("databaseSize"),
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
        metrics=map_metrics_summary(
            getattr(pds, "metrics", None) or data.get("metrics")
        ),
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
    # If service returns just an OCID string for the subnet, map it directly
    if isinstance(det, str):
        return RecoveryServiceSubnetDetails(id=det)
    nsgs = getattr(det, "nsg_ids", None) or data.get("nsg_ids") or data.get("nsgIds")
    if nsgs is not None:
        try:
            nsgs = list(nsgs)
        except Exception:
            nsgs = None
    id_val = (
        getattr(det, "id", None)
        or data.get("id")
        or data.get("recovery_service_subnet_id")
        or data.get("recoveryServiceSubnetId")
        or data.get("rss_id")
        or data.get("rssId")
    )
    return RecoveryServiceSubnetDetails(
        id=id_val,
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
    backup_space_estimate_in_gbs: Optional[float] = Field(
        None, description="Estimated backup space in GBs."
    )
    current_retention_period_in_seconds: Optional[float] = Field(
        None, description="Current recoverable window length in seconds."
    )
    is_redo_logs_enabled: Optional[bool] = Field(
        None, description="Whether redo transport is enabled."
    )
    minimum_recovery_needed_in_days: Optional[float] = Field(
        None, description="Minimum days of recovery needed."
    )
    retention_period_in_days: Optional[float] = Field(
        None, description="Configured retention period in days."
    )
    unprotected_window_in_seconds: Optional[float] = Field(
        None, description="Unprotected window in seconds."
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
        or data.get("databaseSizeInGbs")
        or data.get("dbSizeInGbs"),
        recoverable_window_start_time=getattr(m, "recoverable_window_start_time", None)
        or data.get("recoverable_window_start_time")
        or data.get("recoverableWindowStartTime"),
        recoverable_window_end_time=getattr(m, "recoverable_window_end_time", None)
        or data.get("recoverable_window_end_time")
        or data.get("recoverableWindowEndTime"),
        latest_backup_time=getattr(m, "latest_backup_time", None)
        or data.get("latest_backup_time")
        or data.get("latestBackupTime"),
        backup_space_estimate_in_gbs=getattr(m, "backup_space_estimate_in_gbs", None)
        or data.get("backup_space_estimate_in_gbs")
        or data.get("backupSpaceEstimateInGbs"),
        current_retention_period_in_seconds=getattr(
            m, "current_retention_period_in_seconds", None
        )
        or data.get("current_retention_period_in_seconds")
        or data.get("currentRetentionPeriodInSeconds"),
        is_redo_logs_enabled=getattr(m, "is_redo_logs_enabled", None)
        or data.get("is_redo_logs_enabled")
        or data.get("isRedoLogsEnabled"),
        minimum_recovery_needed_in_days=getattr(
            m, "minimum_recovery_needed_in_days", None
        )
        or data.get("minimum_recovery_needed_in_days")
        or data.get("minimumRecoveryNeededInDays"),
        retention_period_in_days=getattr(m, "retention_period_in_days", None)
        or data.get("retention_period_in_days")
        or data.get("retentionPeriodInDays"),
        unprotected_window_in_seconds=getattr(m, "unprotected_window_in_seconds", None)
        or data.get("unprotected_window_in_seconds")
        or data.get("unprotectedWindowInSeconds"),
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
        recoverable_window_start_time=getattr(ms, "recoverable_window_start_time", None)
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

    id: Optional[str] = Field(None, description="The OCID of the protection policy.")
    display_name: Optional[str] = Field(
        None, description="A user-friendly name for the protection policy."
    )
    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment containing the protection policy.",
    )
    backup_retention_period_in_days: Optional[int] = Field(
        None,
        description="Exact number of days to retain backups created by Recovery Service.",
    )
    is_predefined_policy: Optional[bool] = Field(
        None, description="Whether this is an Oracle-defined predefined policy."
    )
    policy_locked_date_time: Optional[str] = Field(
        None, description="When the protection policy was locked (RFC3339 string)."
    )
    must_enforce_cloud_locality: Optional[bool] = Field(
        None,
        description="Whether backup storage must stay in the same cloud locality as the database.",
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
        is_predefined_policy=_first_not_none(
            getattr(pp, "is_predefined_policy", None),
            data.get("is_predefined_policy"),
            data.get("isPredefinedPolicy"),
        ),
        policy_locked_date_time=getattr(pp, "policy_locked_date_time", None)
        or data.get("policy_locked_date_time")
        or data.get("policyLockedDateTime"),
        must_enforce_cloud_locality=_first_not_none(
            getattr(pp, "must_enforce_cloud_locality", None),
            data.get("must_enforce_cloud_locality"),
            data.get("mustEnforceCloudLocality"),
        ),
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

    id: Optional[str] = Field(None, description="The OCID of the protection policy.")
    display_name: Optional[str] = Field(
        None, description="A user-friendly name for the protection policy."
    )
    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment containing the protection policy.",
    )
    backup_retention_period_in_days: Optional[int] = Field(
        None,
        description="Exact number of days to retain backups created by Recovery Service.",
    )
    is_predefined_policy: Optional[bool] = Field(
        None, description="Whether this is an Oracle-defined predefined policy."
    )
    policy_locked_date_time: Optional[str] = Field(
        None, description="When the protection policy was locked (RFC3339 string)."
    )
    must_enforce_cloud_locality: Optional[bool] = Field(
        None,
        description="Whether backup storage must stay in the same cloud locality as the database.",
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
        must_enforce_cloud_locality=getattr(pps, "must_enforce_cloud_locality", None)
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

# region Database Service (oci.database.models)


class BackupDestinationDetails(OCIBaseModel):
    """
    Pydantic model for backup destination details within DbBackupConfig.
    Covers common fields across destination types; unmodeled keys are preserved in 'extras'.
    """

    type: Optional[str] = Field(
        None, description="Destination type, e.g., DBRS, OBJECT_STORE, NFS."
    )
    destination_type: Optional[str] = Field(
        None, description="Original destination type value if provided."
    )
    id: Optional[str] = Field(
        None, description="Destination OCID/identifier when applicable."
    )
    backup_destination_id: Optional[str] = Field(
        None, description="Backup destination OCID if provided by SDK."
    )
    bucket_name: Optional[str] = Field(
        None, description="Object Storage bucket name (OBJECT_STORE only)."
    )
    namespace: Optional[str] = Field(
        None, description="Object Storage namespace (OBJECT_STORE only)."
    )
    region: Optional[str] = Field(
        None, description="Region for Object Storage destination."
    )
    local_mount_point: Optional[str] = Field(
        None, description="Local mount point path (NFS)."
    )
    nfs_server: Optional[str] = Field(None, description="NFS server address (NFS).")
    path: Optional[str] = Field(None, description="Destination path if provided.")
    vault_id: Optional[str] = Field(
        None, description="Vault OCID for encryption (if applicable)."
    )
    encryption_key_id: Optional[str] = Field(
        None, description="KMS key OCID (if applicable)."
    )
    compartment_id: Optional[str] = Field(
        None, description="Compartment OCID of the destination (if applicable)."
    )
    tenancy_id: Optional[str] = Field(None, description="Tenancy OCID (if applicable).")
    extras: Optional[Dict[str, Any]] = Field(
        None, description="Any provider-specific fields not modeled above."
    )


def map_backup_destination_details(det) -> BackupDestinationDetails | None:
    if not det:
        return None
    data = _oci_to_dict(det) or {}

    def pick(*names: str):
        for n in names:
            v = getattr(det, n, None)
            if v is not None:
                return v
            if data.get(n) is not None:
                return data.get(n)
        return None

    type_val = pick("type", "destination_type", "destinationType")
    id_val = pick("id", "backup_destination_id", "backupDestinationId", "destinationId")
    bucket = pick("bucket_name", "bucketName")
    namespace = pick("namespace")
    region = pick("region")
    local_mount = pick("local_mount_point", "localMountPoint", "mountPoint")
    nfs_server = pick("nfs_server", "nfsServer", "nfsServerIp", "nfs_server_ip")
    path = pick("path")
    vault_id = pick("vault_id", "vaultId")
    key_id = pick("encryption_key_id", "encryptionKeyId", "kmsKeyId")
    compartment_id = pick("compartment_id", "compartmentId")
    tenancy_id = pick("tenancy_id", "tenancyId")

    consumed = {
        "type",
        "destination_type",
        "destinationType",
        "id",
        "backup_destination_id",
        "backupDestinationId",
        "destinationId",
        "bucket_name",
        "bucketName",
        "namespace",
        "region",
        "local_mount_point",
        "localMountPoint",
        "mountPoint",
        "nfs_server",
        "nfsServer",
        "nfsServerIp",
        "nfs_server_ip",
        "path",
        "vault_id",
        "vaultId",
        "encryption_key_id",
        "encryptionKeyId",
        "kmsKeyId",
        "compartment_id",
        "compartmentId",
        "tenancy_id",
        "tenancyId",
    }
    extras = None
    try:
        extras = {k: v for k, v in data.items() if k not in consumed}
    except Exception:
        extras = None

    return BackupDestinationDetails(
        type=type_val,
        destination_type=(
            pick("destination_type", "destinationType")
            if type_val is not None
            else pick("destination_type", "destinationType")
        ),
        id=id_val,
        backup_destination_id=pick("backup_destination_id", "backupDestinationId"),
        bucket_name=bucket,
        namespace=namespace,
        region=region,
        local_mount_point=local_mount,
        nfs_server=nfs_server,
        path=path,
        vault_id=vault_id,
        encryption_key_id=key_id,
        compartment_id=compartment_id,
        tenancy_id=tenancy_id,
        extras=extras,
    )


class DbBackupConfig(OCIBaseModel):
    """
    Pydantic model mirroring oci.database.models.DbBackupConfig.
    Nested under Database/DatabaseSummary as db_backup_config.
    """

    is_auto_backup_enabled: Optional[bool] = Field(
        None, description="Whether auto backup is enabled."
    )
    auto_backup_window: Optional[str] = Field(
        None, description="Preferred start time window for auto backups."
    )
    recovery_window_in_days: Optional[int] = Field(
        None, description="Recovery window in days (Recovery Service)."
    )
    vpcu_user: Optional[str] = Field(
        None, description="Virtual Private Catalog user (VPC user) if configured."
    )
    backup_deletion_policy: Optional[str] = Field(
        None, description="Deletion policy for backups."
    )
    backup_destination_details: Optional[List[BackupDestinationDetails]] = Field(
        None, description="Backup destination details."
    )
    extras: Optional[Dict[str, Any]] = Field(
        None, description="Any provider-specific fields not modeled above."
    )


def map_db_backup_config(cfg) -> DbBackupConfig | None:
    if not cfg:
        return None
    data = _oci_to_dict(cfg) or {}

    def pick(*names: str):
        for n in names:
            v = getattr(cfg, n, None)
            if v is not None:
                return v
            if data.get(n) is not None:
                return data.get(n)
        return None

    is_auto = pick(
        "is_auto_backup_enabled",
        "isAutoBackupEnabled",
        "auto_backup_enabled",
        "autoBackupEnabled",
    )
    window = pick(
        "auto_backup_window",
        "autoBackupWindow",
        "preferred_backup_window",
        "preferredBackupWindow",
    )
    recovery_days = pick(
        "recovery_window_in_days", "recoveryWindowInDays", "recovery_window"
    )
    vpcu = pick(
        "vpcu_user",
        "vpc_user",
        "vpcUser",
        "vpcUserName",
        "vpc_user_name",
        "vpcUsername",
    )
    deletion_policy = pick("backup_deletion_policy", "backupDeletionPolicy")
    dests = (
        pick("backup_destination_details", "backupDestinationDetails")
        or data.get("backupDestinationDetails")
        or data.get("backup_destination_details")
    )
    mapped_dests = _map_list(dests, map_backup_destination_details)

    consumed = {
        "is_auto_backup_enabled",
        "isAutoBackupEnabled",
        "auto_backup_enabled",
        "autoBackupEnabled",
        "auto_backup_window",
        "autoBackupWindow",
        "preferred_backup_window",
        "preferredBackupWindow",
        "recovery_window_in_days",
        "recoveryWindowInDays",
        "recovery_window",
        "vpcu_user",
        "vpc_user",
        "vpcUser",
        "vpcUserName",
        "vpc_user_name",
        "vpcUsername",
        "backup_deletion_policy",
        "backupDeletionPolicy",
        "backup_destination_details",
        "backupDestinationDetails",
    }
    extras = None
    try:
        extras = {k: v for k, v in data.items() if k not in consumed}
    except Exception:
        extras = None

    return DbBackupConfig(
        is_auto_backup_enabled=is_auto,
        auto_backup_window=window,
        recovery_window_in_days=recovery_days,
        vpcu_user=vpcu,
        backup_deletion_policy=deletion_policy,
        backup_destination_details=mapped_dests,
        extras=extras,
    )


class Database(OCIBaseModel):
    """
    Pydantic model mirroring oci.database.models.Database.
    """

    id: Optional[str] = Field(None, description="The OCID of the Database.")
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the Database."
    )
    lifecycle_state: Optional[str] = Field(
        None, description="The current lifecycle state of the Database."
    )
    db_name: Optional[str] = Field(None, description="The database name.")
    db_unique_name: Optional[str] = Field(
        None, description="The DB_UNIQUE_NAME of the database."
    )
    db_home_id: Optional[str] = Field(None, description="The OCID of the DB Home.")
    db_system_id: Optional[str] = Field(
        None, description="The OCID of the DB System (if applicable)."
    )
    db_backup_config: Optional["DbBackupConfig"] = Field(
        None, description="Database backup configuration."
    )
    protection_policy_id: Optional[str] = Field(
        None,
        description="Recovery Service Protection Policy OCID linked via Protected Database, if any.",
    )
    time_created: Optional[datetime] = Field(
        None, description="Creation time (RFC3339)."
    )


def map_database(db) -> Database | None:
    if db is None:
        return None
    data = _oci_to_dict(db) or {}
    return Database(
        id=getattr(db, "id", None) or data.get("id"),
        compartment_id=getattr(db, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        lifecycle_state=getattr(db, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        db_name=getattr(db, "db_name", None)
        or data.get("db_name")
        or data.get("dbName"),
        db_unique_name=getattr(db, "db_unique_name", None)
        or data.get("db_unique_name")
        or data.get("dbUniqueName"),
        db_home_id=getattr(db, "db_home_id", None)
        or data.get("db_home_id")
        or data.get("dbHomeId"),
        db_system_id=getattr(db, "db_system_id", None)
        or data.get("db_system_id")
        or data.get("dbSystemId"),
        db_backup_config=map_db_backup_config(
            getattr(db, "db_backup_config", None)
            or data.get("db_backup_config")
            or data.get("dbBackupConfig")
            or data.get("databaseBackupConfig")
        ),
        time_created=getattr(db, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
    )


class DatabaseSummary(OCIBaseModel):
    """
    Pydantic model mirroring oci.database.models.DatabaseSummary.
    """

    id: Optional[str] = Field(None, description="The OCID of the Database.")
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the Database."
    )
    lifecycle_state: Optional[str] = Field(
        None, description="The current lifecycle state of the Database."
    )
    db_name: Optional[str] = Field(None, description="The database name.")
    db_unique_name: Optional[str] = Field(
        None, description="The DB_UNIQUE_NAME of the database."
    )
    db_home_id: Optional[str] = Field(None, description="The OCID of the DB Home.")
    db_system_id: Optional[str] = Field(
        None, description="The OCID of the DB System (if applicable)."
    )
    db_backup_config: Optional["DbBackupConfig"] = Field(
        None, description="Database backup configuration."
    )
    protection_policy_id: Optional[str] = Field(
        None,
        description="Recovery Service Protection Policy OCID linked via Protected Database, if any.",
    )
    time_created: Optional[datetime] = Field(
        None, description="Creation time (RFC3339)."
    )


def map_database_summary(db) -> DatabaseSummary | None:
    if db is None:
        return None
    data = _oci_to_dict(db) or {}
    return DatabaseSummary(
        id=getattr(db, "id", None) or data.get("id"),
        compartment_id=getattr(db, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        lifecycle_state=getattr(db, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        db_name=getattr(db, "db_name", None)
        or data.get("db_name")
        or data.get("dbName"),
        db_unique_name=getattr(db, "db_unique_name", None)
        or data.get("db_unique_name")
        or data.get("dbUniqueName"),
        db_home_id=getattr(db, "db_home_id", None)
        or data.get("db_home_id")
        or data.get("dbHomeId"),
        db_system_id=getattr(db, "db_system_id", None)
        or data.get("db_system_id")
        or data.get("dbSystemId"),
        db_backup_config=map_db_backup_config(
            getattr(db, "db_backup_config", None)
            or data.get("db_backup_config")
            or data.get("dbBackupConfig")
            or data.get("databaseBackupConfig")
        ),
        time_created=getattr(db, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
    )


class BackupSummary(OCIBaseModel):
    """
    Pydantic model mirroring oci.database.models.BackupSummary.
    """

    id: Optional[str] = Field(None, description="The OCID of the backup.")
    display_name: Optional[str] = Field(None, description="Display name.")
    compartment_id: Optional[str] = Field(None, description="Compartment OCID.")
    database_id: Optional[str] = Field(None, description="Database OCID.")
    lifecycle_state: Optional[str] = Field(None, description="Lifecycle state.")
    type: Optional[str] = Field(None, description="Backup type.")
    time_started: Optional[datetime] = Field(None, description="Start time (RFC3339).")
    time_ended: Optional[datetime] = Field(None, description="End time (RFC3339).")
    retention_period_in_days: Optional[float] = Field(
        None,
        alias="retention-period-in-days",
        description="Retention period (days) inferred from Recovery protection policy, when available.",
    )
    retention_period_in_years: Optional[float] = Field(
        None,
        alias="retention-period-in-years",
        description="Retention period (years), derived from days when available.",
    )
    database_size_in_gbs: Optional[float] = Field(
        None,
        alias="database-size-in-gbs",
        description=(
            "Database size in GBs (from Recovery metrics) for the database "
            "that this backup belongs to."
        ),
    )
    backup_destination_type: Optional[str] = Field(
        None,
        alias="backup-destination-type",
        description=(
            "Primary backup destination type for the database "
            "(e.g., DBRS, OBJECT_STORE, NFS, UNKNOWN)."
        ),
    )


def map_backup_summary(b) -> BackupSummary | None:
    if b is None:
        return None
    data = _oci_to_dict(b) or {}
    return BackupSummary(
        id=getattr(b, "id", None) or data.get("id"),
        display_name=getattr(b, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        compartment_id=getattr(b, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        database_id=getattr(b, "database_id", None)
        or data.get("database_id")
        or data.get("databaseId"),
        lifecycle_state=getattr(b, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        type=getattr(b, "type", None) or data.get("type"),
        time_started=getattr(b, "time_started", None)
        or data.get("time_started")
        or data.get("timeStarted"),
        time_ended=getattr(b, "time_ended", None)
        or data.get("time_ended")
        or data.get("timeEnded"),
        database_size_in_gbs=getattr(b, "database_size_in_gbs", None)
        or data.get("database_size_in_gbs")
        or data.get("databaseSizeInGBs")
        or data.get("databaseSizeInGbs"),
        backup_destination_type=getattr(b, "backup_destination_type", None)
        or data.get("backup_destination_type")
        or data.get("backupDestinationType"),
        retention_period_in_days=getattr(b, "retention_period_in_days", None)
        or data.get("retention_period_in_days")
        or data.get("retentionPeriodInDays"),
        retention_period_in_years=getattr(b, "retention_period_in_years", None)
        or data.get("retention_period_in_years")
        or data.get("retentionPeriodInYears"),
    )


class Backup(OCIBaseModel):
    """
    Pydantic model mirroring oci.database.models.Backup.
    """

    id: Optional[str] = Field(None, description="The OCID of the backup.")
    display_name: Optional[str] = Field(None, description="Display name.")
    compartment_id: Optional[str] = Field(None, description="Compartment OCID.")
    database_id: Optional[str] = Field(None, description="Database OCID.")
    lifecycle_state: Optional[str] = Field(None, description="Lifecycle state.")
    type: Optional[str] = Field(None, description="Backup type.")
    time_started: Optional[datetime] = Field(None, description="Start time (RFC3339).")
    time_ended: Optional[datetime] = Field(None, description="End time (RFC3339).")
    database_version: Optional[str] = Field(
        None, description="Database version at backup time."
    )
    # Enriched fields populated by server get/list backup tools
    retention_period_in_days: Optional[float] = Field(
        None,
        alias="retention-period-in-days",
        description="Retention period (days) inferred from Recovery protection policy, when available.",
    )
    retention_period_in_years: Optional[float] = Field(
        None,
        alias="retention-period-in-years",
        description="Retention period (years), derived from days when available.",
    )
    database_size_in_gbs: Optional[float] = Field(
        None,
        alias="database-size-in-gbs",
        description=(
            "Database size in GBs (from Recovery metrics) for the database "
            "that this backup belongs to."
        ),
    )
    backup_destination_type: Optional[str] = Field(
        None,
        alias="backup-destination-type",
        description=(
            "Primary backup destination type for the database "
            "(e.g., DBRS, OBJECT_STORE, NFS, UNKNOWN)."
        ),
    )


def map_backup(b) -> Backup | None:
    if b is None:
        return None
    data = _oci_to_dict(b) or {}
    return Backup(
        id=getattr(b, "id", None) or data.get("id"),
        display_name=getattr(b, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        compartment_id=getattr(b, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        database_id=getattr(b, "database_id", None)
        or data.get("database_id")
        or data.get("databaseId"),
        lifecycle_state=getattr(b, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        type=getattr(b, "type", None) or data.get("type"),
        time_started=getattr(b, "time_started", None)
        or data.get("time_started")
        or data.get("timeStarted"),
        time_ended=getattr(b, "time_ended", None)
        or data.get("time_ended")
        or data.get("timeEnded"),
        database_size_in_gbs=getattr(b, "database_size_in_gbs", None)
        or data.get("database_size_in_gbs")
        or data.get("databaseSizeInGBs")
        or data.get("databaseSizeInGbs"),
        backup_destination_type=getattr(b, "backup_destination_type", None)
        or data.get("backup_destination_type")
        or data.get("backupDestinationType"),
        retention_period_in_days=getattr(b, "retention_period_in_days", None)
        or data.get("retention_period_in_days")
        or data.get("retentionPeriodInDays"),
        retention_period_in_years=getattr(b, "retention_period_in_years", None)
        or data.get("retention_period_in_years")
        or data.get("retentionPeriodInYears"),
        database_version=getattr(b, "database_version", None)
        or data.get("database_version")
        or data.get("databaseVersion"),
    )


class DatabaseHomeSummary(OCIBaseModel):
    """
    Pydantic model mirroring oci.database.models.DbHomeSummary.
    """

    id: Optional[str] = Field(None, description="The OCID of the DB Home.")
    display_name: Optional[str] = Field(None, description="Display name.")
    compartment_id: Optional[str] = Field(None, description="Compartment OCID.")
    db_system_id: Optional[str] = Field(None, description="DB System OCID.")
    lifecycle_state: Optional[str] = Field(None, description="Lifecycle state.")
    db_version: Optional[str] = Field(None, description="DB version.")
    time_created: Optional[datetime] = Field(
        None, description="Creation time (RFC3339)."
    )


def map_database_home_summary(h) -> DatabaseHomeSummary | None:
    if h is None:
        return None
    data = _oci_to_dict(h) or {}
    return DatabaseHomeSummary(
        id=getattr(h, "id", None) or data.get("id"),
        display_name=getattr(h, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        compartment_id=getattr(h, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        db_system_id=getattr(h, "db_system_id", None)
        or data.get("db_system_id")
        or data.get("dbSystemId"),
        lifecycle_state=getattr(h, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        db_version=getattr(h, "db_version", None)
        or data.get("db_version")
        or data.get("dbVersion"),
        time_created=getattr(h, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
    )


class DatabaseHome(OCIBaseModel):
    """
    Pydantic model mirroring oci.database.models.DbHome.
    """

    id: Optional[str] = Field(None, description="The OCID of the DB Home.")
    display_name: Optional[str] = Field(None, description="Display name.")
    compartment_id: Optional[str] = Field(None, description="Compartment OCID.")
    db_system_id: Optional[str] = Field(None, description="DB System OCID.")
    lifecycle_state: Optional[str] = Field(None, description="Lifecycle state.")
    db_version: Optional[str] = Field(None, description="DB version.")
    time_created: Optional[datetime] = Field(
        None, description="Creation time (RFC3339)."
    )


def map_database_home(h) -> DatabaseHome | None:
    if h is None:
        return None
    data = _oci_to_dict(h) or {}
    return DatabaseHome(
        id=getattr(h, "id", None) or data.get("id"),
        display_name=getattr(h, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        compartment_id=getattr(h, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        db_system_id=getattr(h, "db_system_id", None)
        or data.get("db_system_id")
        or data.get("dbSystemId"),
        lifecycle_state=getattr(h, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        db_version=getattr(h, "db_version", None)
        or data.get("db_version")
        or data.get("dbVersion"),
        time_created=getattr(h, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
    )


class DbSystemSummary(OCIBaseModel):
    """
    Pydantic model mirroring oci.database.models.DbSystemSummary.
    """

    id: Optional[str] = Field(None, description="DB System OCID.")
    display_name: Optional[str] = Field(None, description="Display name.")
    compartment_id: Optional[str] = Field(None, description="Compartment OCID.")
    lifecycle_state: Optional[str] = Field(None, description="Lifecycle state.")
    shape: Optional[str] = Field(None, description="Shape.")
    cpu_core_count: Optional[int] = Field(None, description="CPU core count.")
    node_count: Optional[int] = Field(None, description="Node count.")
    time_created: Optional[datetime] = Field(
        None, description="Creation time (RFC3339)."
    )


def map_db_system_summary(s) -> DbSystemSummary | None:
    if s is None:
        return None
    data = _oci_to_dict(s) or {}
    return DbSystemSummary(
        id=getattr(s, "id", None) or data.get("id"),
        display_name=getattr(s, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        compartment_id=getattr(s, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        lifecycle_state=getattr(s, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        shape=getattr(s, "shape", None) or data.get("shape"),
        cpu_core_count=getattr(s, "cpu_core_count", None)
        or data.get("cpu_core_count")
        or data.get("cpuCoreCount"),
        node_count=getattr(s, "node_count", None)
        or data.get("node_count")
        or data.get("nodeCount"),
        time_created=getattr(s, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
    )


class DbSystem(OCIBaseModel):
    """
    Pydantic model mirroring oci.database.models.DbSystem.
    """

    id: Optional[str] = Field(None, description="DB System OCID.")
    display_name: Optional[str] = Field(None, description="Display name.")
    compartment_id: Optional[str] = Field(None, description="Compartment OCID.")
    lifecycle_state: Optional[str] = Field(None, description="Lifecycle state.")
    shape: Optional[str] = Field(None, description="Shape.")
    cpu_core_count: Optional[int] = Field(None, description="CPU core count.")
    node_count: Optional[int] = Field(None, description="Node count.")
    license_model: Optional[str] = Field(None, description="License model.")
    availability_domain: Optional[str] = Field(None, description="Availability domain.")
    time_created: Optional[datetime] = Field(
        None, description="Creation time (RFC3339)."
    )


def map_db_system(s) -> DbSystem | None:
    if s is None:
        return None
    data = _oci_to_dict(s) or {}
    return DbSystem(
        id=getattr(s, "id", None) or data.get("id"),
        display_name=getattr(s, "display_name", None)
        or data.get("display_name")
        or data.get("displayName"),
        compartment_id=getattr(s, "compartment_id", None)
        or data.get("compartment_id")
        or data.get("compartmentId"),
        lifecycle_state=getattr(s, "lifecycle_state", None)
        or data.get("lifecycle_state")
        or data.get("lifecycleState"),
        shape=getattr(s, "shape", None) or data.get("shape"),
        cpu_core_count=getattr(s, "cpu_core_count", None)
        or data.get("cpu_core_count")
        or data.get("cpuCoreCount"),
        node_count=getattr(s, "node_count", None)
        or data.get("node_count")
        or data.get("nodeCount"),
        license_model=getattr(s, "license_model", None)
        or data.get("license_model")
        or data.get("licenseModel"),
        availability_domain=getattr(s, "availability_domain", None)
        or data.get("availability_domain")
        or data.get("availabilityDomain"),
        time_created=getattr(s, "time_created", None)
        or data.get("time_created")
        or data.get("timeCreated"),
    )


# Database Protection Summary (constructed by server, no direct SDK mapping)


class ProtectedDatabaseBackupDestinationItem(OCIBaseModel):
    database_id: str = Field(..., description="Database OCID.")
    db_name: Optional[str] = Field(None, description="Database name.")
    status: Optional[str] = Field(
        None, description="CONFIGURED | HAS_BACKUPS | UNCONFIGURED"
    )
    destination_types: List[str] = Field(
        default_factory=list,
        description="Backup destination type(s) (e.g., DBRS, OSS, NFS).",
    )
    destination_ids: List[str] = Field(
        default_factory=list, description="Backup destination OCIDs."
    )
    last_backup_time: Optional[datetime] = Field(
        None, description="Most recent backup time, if computed."
    )


class ProtectedDatabaseBackupDestinationSummary(OCIBaseModel):
    compartment_id: Optional[str] = Field(None, description="Compartment OCID.")
    region: Optional[str] = Field(None, description="Region.")
    total_databases: int = Field(0, description="Total databases scanned.")
    unconfigured_count: int = Field(
        0, description="Count of databases without configured automatic backups."
    )
    counts_by_destination_type: Dict[str, int] = Field(
        default_factory=dict, description="Counts by destination type."
    )
    db_names_by_destination_type: Dict[str, List[str]] = Field(
        default_factory=dict, description="DB names grouped by destination type."
    )
    unconfigured_db_names: List[str] = Field(
        default_factory=list, description="DBs not configured for auto backup."
    )
    has_backups_db_names: List[str] = Field(
        default_factory=list, description="DBs with backups but not configured."
    )
    items: List[ProtectedDatabaseBackupDestinationItem] = Field(
        default_factory=list, description="Per-database details."
    )


# endregion
