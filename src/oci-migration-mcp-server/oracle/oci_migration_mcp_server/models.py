"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

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


# region Migration


class Migration(BaseModel):
    """
    Pydantic model mirroring the fields of oci.cloud_migrations.models.Migration.
    This model has no nested custom types; all fields are primitives or dicts.
    """

    id: Optional[str] = Field(
        None, description="Unique identifier that is immutable on creation"
    )
    display_name: Optional[str] = Field(
        None, description="Migration Identifier that can be renamed"
    )
    compartment_id: Optional[str] = Field(None, description="Compartment Identifier")
    lifecycle_state: Optional[str] = Field(
        None,
        description="The current state of migration.",
        json_schema_extra={
            "enum": [
                "CREATING",
                "UPDATING",
                "NEEDS_ATTENTION",
                "ACTIVE",
                "DELETING",
                "DELETED",
                "FAILED",
            ]
        },
    )
    lifecycle_details: Optional[str] = Field(
        None,
        description="A message describing the current state in more detail. "
        "For example, it can be used to provide actionable information for a resource in Failed state.",
    )
    time_created: Optional[datetime] = Field(
        None,
        description="The time when the migration project was created. An RFC3339 formatted datetime string",
    )
    time_updated: Optional[datetime] = Field(
        None,
        description="The time when the migration project was updated. An RFC3339 formatted datetime string",
    )
    replication_schedule_id: Optional[str] = Field(
        None, description="Replication schedule identifier"
    )
    is_completed: Optional[bool] = Field(
        None, description="Indicates whether migration is marked as completed."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description="Simple key-value pair that is applied without any predefined name, type or scope. "
        "It exists only for cross-compatibility.",
    )
    defined_tags: Optional[Dict[str, Dict[str, object]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",
    )
    system_tags: Optional[Dict[str, Dict[str, object]]] = Field(
        None,
        description="Usage of system tag keys. These predefined keys are scoped to namespaces.",
    )


def map_migration(migration_data: oci.cloud_migrations.models.Migration) -> Migration:
    """
    Convert an oci.cloud_migrations.models.Migration to oracle.oci_migration_mcp_server.models.Migration.
    Since there are no nested types, this is a direct mapping.
    """
    return Migration(
        id=getattr(migration_data, "id", None),
        display_name=getattr(migration_data, "display_name", None),
        compartment_id=getattr(migration_data, "compartment_id", None),
        lifecycle_state=getattr(migration_data, "lifecycle_state", None),
        lifecycle_details=getattr(migration_data, "lifecycle_details", None),
        time_created=getattr(migration_data, "time_created", None),
        time_updated=getattr(migration_data, "time_updated", None),
        replication_schedule_id=getattr(
            migration_data, "replication_schedule_id", None
        ),
        is_completed=getattr(migration_data, "is_completed", None),
        freeform_tags=getattr(migration_data, "freeform_tags", None),
        defined_tags=getattr(migration_data, "defined_tags", None),
        system_tags=getattr(migration_data, "system_tags", None),
    )


# endregion

# region ResourceAssessmentStrategy


# ResourceAssessmentStrategy and its subtype fields
class ResourceAssessmentStrategy(BaseModel):
    resource_type: Optional[Literal["CPU", "MEMORY", "ALL", "UNKNOWN_ENUM_VALUE"]] = (
        Field(None, description="The type of resource.")
    )
    strategy_type: Optional[
        Literal["AS_IS", "AVERAGE", "PEAK", "PERCENTILE", "UNKNOWN_ENUM_VALUE"]
    ] = Field(None, description="The type of strategy used for migration.")
    # Subtype-specific, all optional to cover union of subtypes
    adjustment_multiplier: Optional[float] = Field(
        None, description="Multiplier applied to usage before recommendation."
    )
    metric_type: Optional[
        Literal["AUTO", "HISTORICAL", "RUNTIME", "UNKNOWN_ENUM_VALUE"]
    ] = Field(None, description="Metric source type for assessment.")
    metric_time_window: Optional[Literal["1d", "7d", "30d", "UNKNOWN_ENUM_VALUE"]] = (
        Field(None, description="Time window over which metrics are evaluated.")
    )
    percentile: Optional[Literal["P50", "P90", "P95", "P99", "UNKNOWN_ENUM_VALUE"]] = (
        Field(None, description="Percentile value (for percentile strategy).")
    )


def map_resource_assessment_strategy(obj) -> ResourceAssessmentStrategy | None:
    if not obj:
        return None
    return ResourceAssessmentStrategy(
        resource_type=getattr(obj, "resource_type", None),
        strategy_type=getattr(obj, "strategy_type", None),
        adjustment_multiplier=getattr(obj, "adjustment_multiplier", None),
        metric_type=getattr(obj, "metric_type", None),
        metric_time_window=getattr(obj, "metric_time_window", None),
        percentile=getattr(obj, "percentile", None),
    )


def map_resource_assessment_strategies(
    items,
) -> list[ResourceAssessmentStrategy] | None:
    if not items:
        return None
    result: list[ResourceAssessmentStrategy] = []
    for it in items:
        mapped = map_resource_assessment_strategy(it)
        if mapped is not None:
            result.append(mapped)
    return result or None


# endregion


# CostEstimation stack
# region ComputeCostEstimation
class ComputeCostEstimation(BaseModel):
    ocpu_per_hour: Optional[float] = None
    ocpu_per_hour_by_subscription: Optional[float] = None
    memory_gb_per_hour: Optional[float] = None
    memory_gb_per_hour_by_subscription: Optional[float] = None
    gpu_per_hour: Optional[float] = None
    gpu_per_hour_by_subscription: Optional[float] = None
    total_per_hour: Optional[float] = None
    total_per_hour_by_subscription: Optional[float] = None
    ocpu_count: Optional[float] = None
    memory_amount_gb: Optional[float] = None
    gpu_count: Optional[float] = None


# endregion


# region StorageCostEstimation
class StorageCostEstimation(BaseModel):
    volumes: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of volume cost estimations (as dicts)."
    )
    total_gb_per_month: Optional[float] = None
    total_gb_per_month_by_subscription: Optional[float] = None


# endregion


# region OsImageEstimation
class OsImageEstimation(BaseModel):
    total_per_hour: Optional[float] = None
    total_per_hour_by_subscription: Optional[float] = None


# endregion


# region CostEstimation
class CostEstimation(BaseModel):
    compute: Optional[ComputeCostEstimation] = None
    storage: Optional[StorageCostEstimation] = None
    os_image: Optional[OsImageEstimation] = None
    currency_code: Optional[str] = None
    total_estimation_per_month: Optional[float] = None
    total_estimation_per_month_by_subscription: Optional[float] = None
    subscription_id: Optional[str] = None


# endregion


def map_compute_cost_estimation(obj) -> ComputeCostEstimation | None:
    if not obj:
        return None
    return ComputeCostEstimation(
        ocpu_per_hour=getattr(obj, "ocpu_per_hour", None),
        ocpu_per_hour_by_subscription=getattr(
            obj, "ocpu_per_hour_by_subscription", None
        ),
        memory_gb_per_hour=getattr(obj, "memory_gb_per_hour", None),
        memory_gb_per_hour_by_subscription=getattr(
            obj, "memory_gb_per_hour_by_subscription", None
        ),
        gpu_per_hour=getattr(obj, "gpu_per_hour", None),
        gpu_per_hour_by_subscription=getattr(obj, "gpu_per_hour_by_subscription", None),
        total_per_hour=getattr(obj, "total_per_hour", None),
        total_per_hour_by_subscription=getattr(
            obj, "total_per_hour_by_subscription", None
        ),
        ocpu_count=getattr(obj, "ocpu_count", None),
        memory_amount_gb=getattr(obj, "memory_amount_gb", None),
        gpu_count=getattr(obj, "gpu_count", None),
    )


def map_storage_cost_estimation(obj) -> StorageCostEstimation | None:
    if not obj:
        return None
    vols = getattr(obj, "volumes", None)
    if vols is not None:
        try:
            vols = [_oci_to_dict(v) for v in vols]
        except Exception:
            vols = None
    return StorageCostEstimation(
        volumes=vols,
        total_gb_per_month=getattr(obj, "total_gb_per_month", None),
        total_gb_per_month_by_subscription=getattr(
            obj, "total_gb_per_month_by_subscription", None
        ),
    )


def map_os_image_estimation(obj) -> OsImageEstimation | None:
    if not obj:
        return None
    return OsImageEstimation(
        total_per_hour=getattr(obj, "total_per_hour", None),
        total_per_hour_by_subscription=getattr(
            obj, "total_per_hour_by_subscription", None
        ),
    )


def map_cost_estimation(obj) -> CostEstimation | None:
    if not obj:
        return None
    return CostEstimation(
        compute=map_compute_cost_estimation(getattr(obj, "compute", None)),
        storage=map_storage_cost_estimation(getattr(obj, "storage", None)),
        os_image=map_os_image_estimation(getattr(obj, "os_image", None)),
        currency_code=getattr(obj, "currency_code", None),
        total_estimation_per_month=getattr(obj, "total_estimation_per_month", None),
        total_estimation_per_month_by_subscription=getattr(
            obj, "total_estimation_per_month_by_subscription", None
        ),
        subscription_id=getattr(obj, "subscription_id", None),
    )


# region MigrationPlanStats
class MigrationPlanStats(BaseModel):
    total_estimated_cost: Optional[CostEstimation] = None
    time_updated: Optional[datetime] = Field(
        None, description="The time when the migration plan was calculated. RFC3339."
    )
    vm_count: Optional[int] = Field(
        None, description="The total count of VMs in migration"
    )


# endregion


def map_migration_plan_stats(obj) -> MigrationPlanStats | None:
    if not obj:
        return None
    return MigrationPlanStats(
        total_estimated_cost=map_cost_estimation(
            getattr(obj, "total_estimated_cost", None)
        ),
        time_updated=getattr(obj, "time_updated", None),
        vm_count=getattr(obj, "vm_count", None),
    )


# region TargetEnvironment
# TargetEnvironment and VM subtype fields flattened
class TargetEnvironment(BaseModel):
    target_compartment_id: Optional[str] = Field(
        None, description="Target compartment identifier"
    )
    target_environment_type: Optional[
        Literal["VM_TARGET_ENV", "UNKNOWN_ENUM_VALUE"]
    ] = Field(None, description="The type of target environment.")
    # VM-specific optional fields
    availability_domain: Optional[str] = None
    fault_domain: Optional[str] = None
    vcn: Optional[str] = None
    subnet: Optional[str] = None
    dedicated_vm_host: Optional[str] = None
    ms_license: Optional[str] = None
    preferred_shape_type: Optional[str] = None


# endregion


def map_target_environment(obj) -> TargetEnvironment | None:
    if not obj:
        return None
    return TargetEnvironment(
        target_compartment_id=getattr(obj, "target_compartment_id", None),
        target_environment_type=getattr(obj, "target_environment_type", None),
        availability_domain=getattr(obj, "availability_domain", None),
        fault_domain=getattr(obj, "fault_domain", None),
        vcn=getattr(obj, "vcn", None),
        subnet=getattr(obj, "subnet", None),
        dedicated_vm_host=getattr(obj, "dedicated_vm_host", None),
        ms_license=getattr(obj, "ms_license", None),
        preferred_shape_type=getattr(obj, "preferred_shape_type", None),
    )


def map_target_environments(items) -> list[TargetEnvironment] | None:
    if not items:
        return None
    result: list[TargetEnvironment] = []
    for it in items:
        mapped = map_target_environment(it)
        if mapped is not None:
            result.append(mapped)
    return result or None


# region MigrationPlan


class MigrationPlan(BaseModel):
    """
    Pydantic model mirroring the fields of oci.cloud_migrations.models.MigrationPlan.
    Nested OCI types (strategies, migration_plan_stats, target_environments) are represented
    as plain dicts/lists converted via _oci_to_dict for portability.
    """

    id: Optional[str] = Field(
        None, description="The unique Oracle ID (OCID) that is immutable on creation."
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the migration plan."
    )
    display_name: Optional[str] = Field(
        None,
        description=(
            "A user-friendly name. Does not have to be unique, and it's changeable. "
            "Avoid entering confidential information."
        ),
    )
    time_created: Optional[datetime] = Field(
        None,
        description="The time when the migration plan was created. RFC3339 datetime.",
    )
    time_updated: Optional[datetime] = Field(
        None,
        description="The time when the migration plan was updated. RFC3339 datetime.",
    )
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "UPDATING",
            "NEEDS_ATTENTION",
            "ACTIVE",
            "DELETING",
            "DELETED",
            "FAILED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The current state of the migration plan.")
    lifecycle_details: Optional[str] = Field(
        None,
        description=(
            "A message describing the current state in more detail. For example, it "
            "can be used to provide actionable information for a resource in Failed state."
        ),
    )
    migration_id: Optional[str] = Field(
        None, description="The OCID of the associated migration."
    )

    # Nested collections
    strategies: Optional[List[ResourceAssessmentStrategy]] = Field(
        None, description="List of strategies for the resources to be migrated."
    )
    migration_plan_stats: Optional[MigrationPlanStats] = Field(
        None, description="Statistics/details for the migration plan."
    )
    calculated_limits: Optional[Dict[str, int]] = Field(
        None,
        description=(
            "Limits of the resources that are needed for migration. "
            'Example: {"BlockVolume": 2, "VCN": 1}'
        ),
    )
    target_environments: Optional[List[TargetEnvironment]] = Field(
        None, description="List of target environments."
    )
    reference_to_rms_stack: Optional[str] = Field(
        None, description="OCID of the referenced ORM job."
    )
    source_migration_plan_id: Optional[str] = Field(
        None, description="Source migration plan ID to be cloned."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "Simple key-value pair that is applied without any predefined name, type or scope."
        ),
    )
    defined_tags: Optional[Dict[str, Dict[str, object]]] = Field(
        None,
        description=(
            "Defined tags for this resource. Each key is predefined and scoped to a namespace."
        ),
    )
    system_tags: Optional[Dict[str, Dict[str, object]]] = Field(
        None,
        description=(
            "Usage of system tag keys. These predefined keys are scoped to namespaces."
        ),
    )


def map_migration_plan(
    mp: "oci.cloud_migrations.models.MigrationPlan",
) -> MigrationPlan:
    """
    Convert an oci.cloud_migrations.models.MigrationPlan to
    oracle.oci_migration_mcp_server.models.MigrationPlan.
    Nested OCI SDK models are coerced to dicts for transport.
    """
    if mp is None:
        return None  # type: ignore[return-value]

    strategies = map_resource_assessment_strategies(getattr(mp, "strategies", None))

    target_envs = map_target_environments(getattr(mp, "target_environments", None))

    return MigrationPlan(
        id=getattr(mp, "id", None),
        compartment_id=getattr(mp, "compartment_id", None),
        display_name=getattr(mp, "display_name", None),
        time_created=getattr(mp, "time_created", None),
        time_updated=getattr(mp, "time_updated", None),
        lifecycle_state=getattr(mp, "lifecycle_state", None),
        lifecycle_details=getattr(mp, "lifecycle_details", None),
        migration_id=getattr(mp, "migration_id", None),
        strategies=strategies,
        migration_plan_stats=map_migration_plan_stats(
            getattr(mp, "migration_plan_stats", None)
        ),
        calculated_limits=getattr(mp, "calculated_limits", None),
        target_environments=target_envs,
        reference_to_rms_stack=getattr(mp, "reference_to_rms_stack", None),
        source_migration_plan_id=getattr(mp, "source_migration_plan_id", None),
        freeform_tags=getattr(mp, "freeform_tags", None),
        defined_tags=getattr(mp, "defined_tags", None),
        system_tags=getattr(mp, "system_tags", None),
    )


# endregion


# region MigrationSummary


class MigrationSummary(BaseModel):
    """
    Pydantic model mirroring the fields of oci.cloud_migrations.models.MigrationSummary.
    This model has no nested custom types; all fields are primitives or dicts.
    """

    id: Optional[str] = Field(
        None, description="Unique identifier that is immutable on creation."
    )
    display_name: Optional[str] = Field(
        None, description="Migration identifier that can be renamed"
    )
    compartment_id: Optional[str] = Field(None, description="Compartment identifier")
    time_created: Optional[datetime] = Field(
        None,
        description="The time when the migration project was created. An RFC3339 formatted datetime string.",
    )
    time_updated: Optional[datetime] = Field(
        None,
        description="The time when the migration project was updated. An RFC3339 formatted datetime string.",
    )
    lifecycle_state: Optional[str] = Field(
        None, description="The current state of migration."
    )
    lifecycle_details: Optional[str] = Field(
        None,
        description="A message describing the current state in more detail. "
        "For example, it can be used to provide actionable information for a resource in Failed state.",
    )
    is_completed: Optional[bool] = Field(
        None, description="Indicates whether migration is marked as complete."
    )
    replication_schedule_id: Optional[str] = Field(
        None, description="Replication schedule identifier"
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description="Simple key-value pair that is applied without any predefined name, type or scope. "
        "It exists only for cross-compatibility.",
    )
    defined_tags: Optional[Dict[str, Dict[str, object]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",
    )
    system_tags: Optional[Dict[str, Dict[str, object]]] = Field(
        None,
        description="Usage of system tag keys. These predefined keys are scoped to namespaces.",
    )


def map_migration_summary(
    summary_data: oci.cloud_migrations.models.MigrationSummary,
) -> MigrationSummary:
    """
    Convert an oci.cloud_migrations.models.MigrationSummary to
    oracle.oci_migration_mcp_server.models.MigrationSummary.
    Since there are no nested types, this is a direct mapping.
    """
    return MigrationSummary(
        id=getattr(summary_data, "id", None),
        display_name=getattr(summary_data, "display_name", None),
        compartment_id=getattr(summary_data, "compartment_id", None),
        time_created=getattr(summary_data, "time_created", None),
        time_updated=getattr(summary_data, "time_updated", None),
        lifecycle_state=getattr(summary_data, "lifecycle_state", None),
        lifecycle_details=getattr(summary_data, "lifecycle_details", None),
        is_completed=getattr(summary_data, "is_completed", None),
        replication_schedule_id=getattr(summary_data, "replication_schedule_id", None),
        freeform_tags=getattr(summary_data, "freeform_tags", None),
        defined_tags=getattr(summary_data, "defined_tags", None),
        system_tags=getattr(summary_data, "system_tags", None),
    )


# endregion


# region MigrationPlanSummary


class MigrationPlanSummary(BaseModel):
    """
    Pydantic model mirroring the fields of oci.cloud_migrations.models.MigrationPlanSummary.
    This summary model includes the common top-level fields of a migration plan.
    """

    id: Optional[str] = Field(
        None, description="The unique Oracle ID (OCID) that is immutable on creation."
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the migration plan."
    )
    display_name: Optional[str] = Field(
        None,
        description=(
            "A user-friendly name. Does not have to be unique, and it's changeable. "
            "Avoid entering confidential information."
        ),
    )
    time_created: Optional[datetime] = Field(
        None,
        description="The time when the migration plan was created. RFC3339 datetime.",
    )
    time_updated: Optional[datetime] = Field(
        None,
        description="The time when the migration plan was updated. RFC3339 datetime.",
    )
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "UPDATING",
            "NEEDS_ATTENTION",
            "ACTIVE",
            "DELETING",
            "DELETED",
            "FAILED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The current state of the migration plan.")
    lifecycle_details: Optional[str] = Field(
        None,
        description=(
            "A message describing the current state in more detail. For example, it "
            "can be used to provide actionable information for a resource in Failed state."
        ),
    )
    migration_id: Optional[str] = Field(
        None, description="The OCID of the associated migration."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "Simple key-value pair that is applied without any predefined name, type or scope."
        ),
    )
    defined_tags: Optional[Dict[str, Dict[str, object]]] = Field(
        None,
        description=(
            "Defined tags for this resource. Each key is predefined and scoped to a namespace."
        ),
    )
    system_tags: Optional[Dict[str, Dict[str, object]]] = Field(
        None,
        description=(
            "Usage of system tag keys. These predefined keys are scoped to namespaces."
        ),
    )


def map_migration_plan_summary(
    mps: "oci.cloud_migrations.models.MigrationPlanSummary",
) -> MigrationPlanSummary:
    """
    Convert an oci.cloud_migrations.models.MigrationPlanSummary to
    oracle.oci_migration_mcp_server.models.MigrationPlanSummary.
    """
    if mps is None:  # type: ignore[unreachable]
        return None  # type: ignore[return-value]

    return MigrationPlanSummary(
        id=getattr(mps, "id", None),
        compartment_id=getattr(mps, "compartment_id", None),
        display_name=getattr(mps, "display_name", None),
        time_created=getattr(mps, "time_created", None),
        time_updated=getattr(mps, "time_updated", None),
        lifecycle_state=getattr(mps, "lifecycle_state", None),
        lifecycle_details=getattr(mps, "lifecycle_details", None),
        migration_id=getattr(mps, "migration_id", None),
        freeform_tags=getattr(mps, "freeform_tags", None),
        defined_tags=getattr(mps, "defined_tags", None),
        system_tags=getattr(mps, "system_tags", None),
    )


# endregion
