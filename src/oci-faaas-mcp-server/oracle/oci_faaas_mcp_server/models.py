"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

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


class FusionEnvironmentFamily(BaseModel):
    """Pydantic model representing a Fusion Environment Family."""

    id: Optional[str] = Field(None, description="OCID of the Fusion Environment Family")
    display_name: Optional[str] = Field(None, description="Display name")
    lifecycle_state: Optional[str] = Field(
        None,
        description="Lifecycle state (e.g., CREATING, UPDATING, ACTIVE, DELETING, DELETED, FAILED)",
    )
    compartment_id: Optional[str] = Field(
        None, description="Compartment OCID containing this family"
    )
    time_created: Optional[datetime] = Field(
        None, description="Creation time (RFC3339)"
    )
    time_updated: Optional[datetime] = Field(
        None, description="Last update time (RFC3339)"
    )
    freeform_tags: Optional[Dict[str, str]] = Field(None, description="Freeform tags")
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags"
    )


class FusionEnvironment(BaseModel):
    """Pydantic model representing a Fusion Environment."""

    id: Optional[str] = Field(None, description="OCID of the Fusion Environment")
    display_name: Optional[str] = Field(None, description="Display name")
    compartment_id: Optional[str] = Field(
        None, description="Compartment OCID containing the environment"
    )
    fusion_environment_family_id: Optional[str] = Field(
        None, description="OCID of the parent Fusion Environment Family"
    )
    fusion_environment_type: Optional[str] = Field(
        None, description="Environment type (e.g., PRODUCTION, TEST)"
    )
    version: Optional[str] = Field(None, description="Fusion Apps version (e.g., 25C)")
    public_url: Optional[str] = Field(None, description="Primary public URL")
    idcs_domain_url: Optional[str] = Field(None, description="IDCS domain URL")
    domain_id: Optional[str] = Field(None, description="IDCS domain OCID")

    lifecycle_state: Optional[str] = Field(None, description="Lifecycle state")
    lifecycle_details: Optional[str] = Field(
        None, description="Additional lifecycle details"
    )
    is_suspended: Optional[bool] = Field(None, description="Suspended flag")
    system_name: Optional[str] = Field(None, description="System name/code")
    environment_role: Optional[str] = Field(None, description="Environment role")

    maintenance_policy: Optional[Dict[str, Any]] = Field(
        None, description="Maintenance policy details"
    )
    time_upcoming_maintenance: Optional[datetime] = Field(
        None, description="Upcoming maintenance window (RFC3339)"
    )
    applied_patch_bundles: Optional[List[str]] = Field(
        None, description="Applied patch bundles"
    )

    subscription_ids: Optional[List[str]] = Field(
        None, description="Associated subscription OCIDs"
    )
    additional_language_packs: Optional[List[str]] = Field(
        None, description="Enabled language packs"
    )

    kms_key_id: Optional[str] = Field(None, description="KMS key OCID")
    kms_key_info: Optional[Dict[str, Any]] = Field(None, description="KMS key info")

    dns_prefix: Optional[str] = Field(None, description="DNS prefix")
    lockbox_id: Optional[str] = Field(None, description="Lockbox OCID")
    is_break_glass_enabled: Optional[bool] = Field(
        None, description="Break glass access enabled"
    )

    refresh: Optional[Any] = Field(None, description="Refresh details")
    rules: Optional[List[Any]] = Field(None, description="Rules")
    time_created: Optional[datetime] = Field(
        None, description="Creation time (RFC3339)"
    )
    time_updated: Optional[datetime] = Field(
        None, description="Last update time (RFC3339)"
    )

    freeform_tags: Optional[Dict[str, Any]] = Field(None, description="Freeform tags")
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags"
    )


class FusionEnvironmentStatus(BaseModel):
    """Pydantic model representing the status of a Fusion Environment."""

    fusion_environment_id: Optional[str] = Field(
        None, description="OCID of the Fusion Environment"
    )
    status: Optional[str] = Field(None, description="Status value")
    time_updated: Optional[datetime] = Field(
        None, description="Last status update time (RFC3339)"
    )
    time_created: Optional[datetime] = Field(
        None, description="Creation time if present (RFC3339)"
    )
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional status details"
    )


def _get(data: Any, key: str) -> Any:
    """Safe getter to support both dicts and SDK objects."""
    if isinstance(data, dict):
        return data.get(key)
    return getattr(data, key, None)


def map_fusion_environment_family(data: Any) -> FusionEnvironmentFamily:
    """Map SDK model or dict to FusionEnvironmentFamily."""
    return FusionEnvironmentFamily(
        id=_get(data, "id"),
        display_name=_get(data, "display_name"),
        lifecycle_state=_get(data, "lifecycle_state"),
        compartment_id=_get(data, "compartment_id"),
        time_created=_get(data, "time_created"),
        time_updated=_get(data, "time_updated"),
        freeform_tags=_get(data, "freeform_tags"),
        defined_tags=_get(data, "defined_tags"),
    )


def map_fusion_environment(data: Any) -> FusionEnvironment:
    """Map SDK model or dict to FusionEnvironment."""
    return FusionEnvironment(
        id=_get(data, "id"),
        display_name=_get(data, "display_name"),
        compartment_id=_get(data, "compartment_id"),
        fusion_environment_family_id=_get(data, "fusion_environment_family_id"),
        fusion_environment_type=_get(data, "fusion_environment_type"),
        version=_get(data, "version"),
        public_url=_get(data, "public_url"),
        idcs_domain_url=_get(data, "idcs_domain_url"),
        domain_id=_get(data, "domain_id"),
        lifecycle_state=_get(data, "lifecycle_state"),
        lifecycle_details=_get(data, "lifecycle_details"),
        is_suspended=_get(data, "is_suspended"),
        system_name=_get(data, "system_name"),
        environment_role=_get(data, "environment_role"),
        maintenance_policy=_oci_to_dict(_get(data, "maintenance_policy")),
        time_upcoming_maintenance=_get(data, "time_upcoming_maintenance"),
        applied_patch_bundles=_get(data, "applied_patch_bundles"),
        subscription_ids=_get(data, "subscription_ids"),
        additional_language_packs=_get(data, "additional_language_packs"),
        kms_key_id=_get(data, "kms_key_id"),
        kms_key_info=_get(data, "kms_key_info"),
        dns_prefix=_get(data, "dns_prefix"),
        lockbox_id=_get(data, "lockbox_id"),
        is_break_glass_enabled=_get(data, "is_break_glass_enabled"),
        refresh=_get(data, "refresh"),
        rules=_get(data, "rules"),
        time_created=_get(data, "time_created"),
        time_updated=_get(data, "time_updated"),
        freeform_tags=_get(data, "freeform_tags"),
        defined_tags=_get(data, "defined_tags"),
    )


def map_fusion_environment_status(data: Any) -> FusionEnvironmentStatus:
    """Map SDK model or dict to FusionEnvironmentStatus."""
    # Some SDK responses may not have fusion_environment_id as key; try id as fallback
    fe_id = _get(data, "fusion_environment_id") or _get(data, "id")
    # Anything else goes to details as a dict (best-effort)
    coerced = _oci_to_dict(data) or {}
    details = {
        k: v
        for k, v in coerced.items()
        if k
        not in {"fusion_environment_id", "id", "status", "time_updated", "time_created"}
    }  # noqa: E501
    return FusionEnvironmentStatus(
        fusion_environment_id=fe_id,
        status=_get(data, "status"),
        time_updated=_get(data, "time_updated"),
        time_created=_get(data, "time_created"),
        details=details or None,
    )


class AdminUserSummary(BaseModel):
    """
    IDM admin credentials without password.

    Attributes:
      - username: Admin username
      - email_address: Admin user's email address
      - first_name: Admin user's first name
      - last_name: Admin user's last name
    """

    username: Optional[str] = Field(None, description="Admin username")
    email_address: Optional[str] = Field(None, description="Admin user's email address")
    first_name: Optional[str] = Field(None, description="Admin user's first name")
    last_name: Optional[str] = Field(None, description="Admin user's last name")


def map_admin_user_summary(u: Any) -> Optional[AdminUserSummary]:
    """Convert an OCI SDK AdminUserSummary model (or dict) into Pydantic AdminUserSummary."""
    if not u:
        return None
    data = _oci_to_dict(u) or {}
    return AdminUserSummary(
        username=getattr(u, "username", None) or data.get("username"),
        email_address=getattr(u, "email_address", None) or data.get("email_address"),
        first_name=getattr(u, "first_name", None) or data.get("first_name"),
        last_name=getattr(u, "last_name", None) or data.get("last_name"),
    )


class AdminUserCollection(BaseModel):
    """
    A page of AdminUserSummary objects.
    """

    items: Optional[List[AdminUserSummary]] = Field(
        None, description="A page of AdminUserSummary objects."
    )


def map_admin_user_collection(coll: Any) -> Optional[AdminUserCollection]:
    """Convert an OCI SDK AdminUserCollection model (or dict) into Pydantic AdminUserCollection."""
    if not coll:
        return None
    items = getattr(coll, "items", None)
    if items is None and isinstance(coll, dict):
        items = coll.get("items")

    result: List[AdminUserSummary] = []
    if items:
        for it in items:
            mapped = map_admin_user_summary(it)
            if mapped:
                result.append(mapped)
    return AdminUserCollection(items=result)


class RefreshActivitySummary(BaseModel):
    """
    Summary of the refresh activity.

    Attributes:
      - display_name: A friendly name for the refresh activity. Can be changed later.
      - id: The unique identifier (OCID) of the refresh activity. Can’t be changed after creation.
      - is_data_masking_opted: Represents if the customer opted for Data Masking or not
        during refreshActivity.
      - lifecycle_details: A message describing the current state in more detail.
      - lifecycle_state: The current state of the refresh activity.
        Valid values are Scheduled, In progress, Failed, Completed.
      - refresh_issue_details_list: Details of refresh investigation information,
        each item represents a different issue.
      - service_availability: Service availability / impact during refresh activity execution, up or down.
      - source_fusion_environment_id: The OCID of the Fusion environment that is the
        source environment for the refresh.
      - time_accepted: The time the refresh activity record was created. RFC3339 datetime.
      - time_expected_finish: The time the refresh activity is scheduled to end. RFC3339 datetime.
      - time_finished: The time the refresh activity actually completed / cancelled / failed.
        RFC3339 datetime.
      - time_of_restoration_point: The date and time of the most recent source
        environment backup used for the environment refresh.
      - time_scheduled_start: The time the refresh activity is scheduled to start. RFC3339 datetime.
      - time_updated: The time the refresh activity record was updated. RFC3339 datetime.
    """

    display_name: Optional[str] = Field(
        None,
        description="A friendly name for the refresh activity. Can be changed later.",
    )
    id: Optional[str] = Field(
        None,
        description=(
            "The unique identifier (OCID) of the refresh activity. "
            "Can’t be changed after creation."
        ),
    )
    is_data_masking_opted: Optional[bool] = Field(
        None,
        description="Represents if the customer opted for Data Masking or not during refreshActivity.",
    )
    lifecycle_details: Optional[str] = Field(
        None,
        description="A message describing the current state in more detail.",
    )
    lifecycle_state: Optional[str] = Field(
        None,
        description=(
            "The current state of the refresh activity. "
            "Valid values are Scheduled, In progress, Failed, Completed."
        ),
    )
    refresh_issue_details_list: Optional[List[Dict[str, Any]]] = Field(
        None,
        description=(
            "Details of refresh investigation information, each item "
            "represents a different issue."
        ),
    )
    service_availability: Optional[str] = Field(
        None,
        description=(
            "Service availability / impact during refresh activity execution, "
            "up or down."
        ),
    )
    source_fusion_environment_id: Optional[str] = Field(
        None,
        description="The OCID of the Fusion environment that is the source environment for the refresh.",
    )
    time_accepted: Optional[datetime] = Field(
        None,
        description="The time the refresh activity record was created. RFC3339 datetime.",
    )
    time_expected_finish: Optional[datetime] = Field(
        None,
        description="The time the refresh activity is scheduled to end. RFC3339 datetime.",
    )
    time_finished: Optional[datetime] = Field(
        None,
        description=(
            "The time the refresh activity actually completed / cancelled / failed. "
            "RFC3339 datetime."
        ),
    )
    time_of_restoration_point: Optional[datetime] = Field(
        None,
        description=(
            "The date and time of the most recent source environment backup used "
            "for the environment refresh."
        ),
    )
    time_scheduled_start: Optional[datetime] = Field(
        None,
        description="The time the refresh activity is scheduled to start. RFC3339 datetime.",
    )
    time_updated: Optional[datetime] = Field(
        None,
        description="The time the refresh activity record was updated. RFC3339 datetime.",
    )


def map_refresh_activity_summary(obj: Any) -> Optional[RefreshActivitySummary]:
    """
    Convert an OCI SDK RefreshActivitySummary (or dict) into Pydantic RefreshActivitySummary.
    """
    if not obj:
        return None
    data = _oci_to_dict(obj) or {}

    # Map issue details to plain dicts for flexibility (we don't define the nested model here)
    raw_issues = getattr(obj, "refresh_issue_details_list", None) or data.get(
        "refresh_issue_details_list"
    )
    issues: Optional[List[Dict[str, Any]]] = None
    if raw_issues is not None:
        issues = []
        for it in raw_issues:
            issues.append(_oci_to_dict(it) or it)

    return RefreshActivitySummary(
        id=getattr(obj, "id", None) or data.get("id"),
        display_name=getattr(obj, "display_name", None) or data.get("display_name"),
        source_fusion_environment_id=getattr(obj, "source_fusion_environment_id", None)
        or data.get("source_fusion_environment_id"),
        time_of_restoration_point=getattr(obj, "time_of_restoration_point", None)
        or data.get("time_of_restoration_point"),
        lifecycle_state=getattr(obj, "lifecycle_state", None)
        or data.get("lifecycle_state"),
        time_scheduled_start=getattr(obj, "time_scheduled_start", None)
        or data.get("time_scheduled_start"),
        time_expected_finish=getattr(obj, "time_expected_finish", None)
        or data.get("time_expected_finish"),
        time_finished=getattr(obj, "time_finished", None) or data.get("time_finished"),
        service_availability=getattr(obj, "service_availability", None)
        or data.get("service_availability"),
        time_accepted=getattr(obj, "time_accepted", None) or data.get("time_accepted"),
        time_updated=getattr(obj, "time_updated", None) or data.get("time_updated"),
        is_data_masking_opted=getattr(obj, "is_data_masking_opted", None)
        or data.get("is_data_masking_opted"),
        lifecycle_details=getattr(obj, "lifecycle_details", None)
        or data.get("lifecycle_details"),
        refresh_issue_details_list=issues,
    )


class RefreshActivityCollection(BaseModel):
    """
    Results of a refresh activity search.

    Attributes:
      - items: A page of refresh activity objects.
    """

    items: Optional[List[RefreshActivitySummary]] = Field(
        None, description="A page of refresh activity objects."
    )


def map_refresh_activity_collection(coll: Any) -> Optional[RefreshActivityCollection]:
    """Convert an OCI SDK RefreshActivityCollection model (or dict) into Pydantic
    RefreshActivityCollection."""
    if not coll:
        return None

    items = getattr(coll, "items", None)
    if items is None and isinstance(coll, dict):
        items = coll.get("items")

    result: List[RefreshActivitySummary] = []
    if items:
        for it in items:
            mapped = map_refresh_activity_summary(it)
            if mapped:
                result.append(mapped)
    return RefreshActivityCollection(items=result)


class ScheduledActivitySummary(BaseModel):
    """
    Summary of the scheduled activity for a Fusion environment.

    Attributes:
      - actions: List of actions
      - defined_tags: Defined tags for this resource. Example: {"foo-namespace": {"bar-key": "value"}}
      - delay_in_hours: Cumulative delay hours
      - display_name: A friendly name for the scheduled activity. Can be changed later.
      - freeform_tags: Simple key-value pair applied without predefined name. Example: {"bar-key": "value"}
      - fusion_environment_id: The OCID of the Fusion environment for the scheduled activity.
      - id: Unique identifier that is immutable on creation.
      - lifecycle_details: Message describing the current state in more detail.
      - lifecycle_state: The current state of the scheduled activity.
        Valid values are Scheduled, In progress, Failed, Completed.
      - run_cycle: The run cadence of this scheduled activity.
        Valid values are Quarterly, Monthly, OneOff, and Vertex.
      - scheduled_activity_association_id: The unique identifier that associates a
        scheduled activity with others in one complete maintenance.
      - scheduled_activity_phase: A property describing the phase of the scheduled activity.
      - service_availability: Service availability / impact during scheduled activity execution, up down
      - time_accepted: The time the scheduled activity record was created. RFC3339 datetime.
      - time_expected_finish: Current time the scheduled activity is scheduled to end. RFC3339 datetime.
      - time_finished: The time the scheduled activity actually completed / cancelled / failed.
        RFC3339 datetime.
      - time_scheduled_start: Current time the scheduled activity is scheduled to start. RFC3339 datetime.
      - time_updated: The time the scheduled activity record was updated. RFC3339 datetime.
    """

    actions: Optional[List[Dict[str, Any]]] = Field(None, description="List of actions")
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",
    )
    delay_in_hours: Optional[int] = Field(None, description="Cumulative delay hours")
    display_name: Optional[str] = Field(
        None,
        description="A friendly name for the scheduled activity. Can be changed later.",
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description="Simple key-value pair that is applied without any predefined name, type or scope.",
    )
    fusion_environment_id: Optional[str] = Field(
        None,
        description="The OCID of the Fusion environment for the scheduled activity.",
    )
    id: Optional[str] = Field(
        None, description="Unique identifier that is immutable on creation."
    )
    lifecycle_details: Optional[str] = Field(
        None,
        description="A message describing the current state in more detail.",
    )
    lifecycle_state: Optional[str] = Field(
        None,
        description=(
            "The current state of the scheduled activity. "
            "Valid values are Scheduled, In progress, Failed, Completed."
        ),
    )
    run_cycle: Optional[str] = Field(
        None,
        description=(
            "The run cadence of this scheduled activity. "
            "Valid values are Quarterly, Monthly, OneOff, and Vertex."
        ),
    )
    scheduled_activity_association_id: Optional[str] = Field(
        None,
        description=(
            "The unique identifier that associates a scheduled activity "
            "with others in one complete maintenance."
        ),
    )
    scheduled_activity_phase: Optional[str] = Field(
        None, description="Phase of the scheduled activity."
    )
    service_availability: Optional[str] = Field(
        None,
        description="Service availability / impact during scheduled activity execution, up down",
    )
    time_accepted: Optional[datetime] = Field(
        None, description="The time the scheduled activity record was created."
    )
    time_expected_finish: Optional[datetime] = Field(
        None,
        description="Current time the scheduled activity is scheduled to end.",
    )
    time_finished: Optional[datetime] = Field(
        None,
        description="The time the scheduled activity actually completed / cancelled / failed.",
    )
    time_scheduled_start: Optional[datetime] = Field(
        None,
        description="Current time the scheduled activity is scheduled to start.",
    )
    time_updated: Optional[datetime] = Field(
        None, description="The time the scheduled activity record was updated."
    )


def map_scheduled_activity_summary(obj: Any) -> Optional[ScheduledActivitySummary]:
    """Convert an OCI SDK ScheduledActivitySummary (or dict) into Pydantic ScheduledActivitySummary."""
    if not obj:
        return None
    data = _oci_to_dict(obj) or {}

    raw_actions = getattr(obj, "actions", None) or data.get("actions")
    actions: Optional[List[Dict[str, Any]]] = None
    if raw_actions is not None:
        actions = []
        for it in raw_actions:
            actions.append(_oci_to_dict(it) or it)

    return ScheduledActivitySummary(
        id=getattr(obj, "id", None) or data.get("id"),
        display_name=getattr(obj, "display_name", None) or data.get("display_name"),
        run_cycle=getattr(obj, "run_cycle", None) or data.get("run_cycle"),
        fusion_environment_id=getattr(obj, "fusion_environment_id", None)
        or data.get("fusion_environment_id"),
        lifecycle_state=getattr(obj, "lifecycle_state", None)
        or data.get("lifecycle_state"),
        actions=actions,
        time_scheduled_start=getattr(obj, "time_scheduled_start", None)
        or data.get("time_scheduled_start"),
        time_expected_finish=getattr(obj, "time_expected_finish", None)
        or data.get("time_expected_finish"),
        time_finished=getattr(obj, "time_finished", None) or data.get("time_finished"),
        delay_in_hours=getattr(obj, "delay_in_hours", None)
        or data.get("delay_in_hours"),
        service_availability=getattr(obj, "service_availability", None)
        or data.get("service_availability"),
        time_accepted=getattr(obj, "time_accepted", None) or data.get("time_accepted"),
        time_updated=getattr(obj, "time_updated", None) or data.get("time_updated"),
        lifecycle_details=getattr(obj, "lifecycle_details", None)
        or data.get("lifecycle_details"),
        scheduled_activity_phase=getattr(obj, "scheduled_activity_phase", None)
        or data.get("scheduled_activity_phase"),
        scheduled_activity_association_id=getattr(
            obj, "scheduled_activity_association_id", None
        )
        or data.get("scheduled_activity_association_id"),
        freeform_tags=getattr(obj, "freeform_tags", None) or data.get("freeform_tags"),
        defined_tags=getattr(obj, "defined_tags", None) or data.get("defined_tags"),
    )


class ScheduledActivityCollection(BaseModel):
    """
    Results of a scheduled activity search.

    Attributes:
      - items: A page of scheduled activity objects.
    """

    items: Optional[List[ScheduledActivitySummary]] = Field(
        None, description="A page of scheduled activity objects."
    )


def map_scheduled_activity_collection(
    coll: Any,
) -> Optional[ScheduledActivityCollection]:
    """Convert an OCI SDK ScheduledActivityCollection model (or dict) into Pydantic
    ScheduledActivityCollection."""
    if not coll:
        return None

    items = getattr(coll, "items", None)
    if items is None and isinstance(coll, dict):
        items = coll.get("items")

    result: List[ScheduledActivitySummary] = []
    if items:
        for it in items:
            mapped = map_scheduled_activity_summary(it)
            if mapped:
                result.append(mapped)
    return ScheduledActivityCollection(items=result)


class ScheduledActivity(BaseModel):
    """
    Details of scheduled activity.

    Attributes:
      - actions: List of actions
      - defined_tags: Defined tags for this resource. Example: {"foo-namespace": {"bar-key": "value"}}
      - delay_in_hours: Cumulative delay hours
      - display_name: scheduled activity display name, can be renamed.
      - freeform_tags: Simple key-value pair applied without predefined name. Example: {"bar-key": "value"}
      - fusion_environment_id: FAaaS Environment Identifier.
      - id: Unique identifier that is immutable on creation.
      - lifecycle_details: A message describing the current state in more detail.
      - lifecycle_state: The current state of the scheduledActivity.
      - run_cycle: run cadence.
      - scheduled_activity_association_id: The unique identifier that associates a
        scheduled activity with others in one complete maintenance.
      - scheduled_activity_phase: A property describing the phase of the scheduled activity.
      - service_availability: Service availability / impact during scheduled activity execution up down
      - time_created: The time the scheduled activity record was created. RFC3339 datetime.
      - time_expected_finish: Current time the scheduled activity is scheduled to end. RFC3339 datetime.
      - time_finished: The time the scheduled activity actually completed / cancelled / failed.
        RFC3339 datetime.
      - time_scheduled_start: Current time the scheduled activity is scheduled to start. RFC3339 datetime.
      - time_updated: The time the scheduled activity record was updated. RFC3339 datetime.
    """

    actions: Optional[List[Dict[str, Any]]] = Field(None, description="List of actions")
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",
    )
    delay_in_hours: Optional[int] = Field(None, description="Cumulative delay hours")
    display_name: Optional[str] = Field(
        None, description="scheduled activity display name, can be renamed."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "Simple key-value pair that is applied without any predefined "
            "name, type or scope."
        ),
    )
    fusion_environment_id: Optional[str] = Field(
        None, description="FAaaS Environment Identifier."
    )
    id: Optional[str] = Field(
        None, description="Unique identifier that is immutable on creation."
    )
    lifecycle_details: Optional[str] = Field(
        None,
        description=(
            "A message describing the current state in more detail. "
            "For example, can be used to provide actionable information "
            "for a resource in Failed state."
        ),
    )
    lifecycle_state: Optional[str] = Field(
        None, description="The current state of the scheduledActivity."
    )
    run_cycle: Optional[str] = Field(None, description="run cadence.")
    scheduled_activity_association_id: Optional[str] = Field(
        None,
        description=(
            "The unique identifier that associates a scheduled activity "
            "with others in one complete maintenance."
        ),
    )
    scheduled_activity_phase: Optional[str] = Field(
        None, description="A property describing the phase of the scheduled activity."
    )
    service_availability: Optional[str] = Field(
        None,
        description="Service availability / impact during scheduled activity execution up down",
    )
    time_created: Optional[datetime] = Field(
        None,
        description=(
            "The time the scheduled activity record was created. "
            "An RFC3339 formatted datetime string."
        ),
    )
    time_expected_finish: Optional[datetime] = Field(
        None,
        description=(
            "Current time the scheduled activity is scheduled to end. "
            "An RFC3339 formatted datetime string."
        ),
    )
    time_finished: Optional[datetime] = Field(
        None,
        description=(
            "The time the scheduled activity actually completed / cancelled / failed. "
            "An RFC3339 formatted datetime string."
        ),
    )
    time_scheduled_start: Optional[datetime] = Field(
        None,
        description=(
            "Current time the scheduled activity is scheduled to start. "
            "An RFC3339 formatted datetime string."
        ),
    )
    time_updated: Optional[datetime] = Field(
        None,
        description=(
            "The time the scheduled activity record was updated. "
            "An RFC3339 formatted datetime string."
        ),
    )


def map_scheduled_activity(obj: Any) -> Optional[ScheduledActivity]:
    """Convert an OCI SDK ScheduledActivity (or dict) into Pydantic ScheduledActivity."""
    if not obj:
        return None
    data = _oci_to_dict(obj) or {}

    raw_actions = getattr(obj, "actions", None) or data.get("actions")
    actions: Optional[List[Dict[str, Any]]] = None
    if raw_actions is not None:
        actions = []
        for it in raw_actions:
            actions.append(_oci_to_dict(it) or it)

    return ScheduledActivity(
        id=getattr(obj, "id", None) or data.get("id"),
        display_name=getattr(obj, "display_name", None) or data.get("display_name"),
        run_cycle=getattr(obj, "run_cycle", None) or data.get("run_cycle"),
        fusion_environment_id=getattr(obj, "fusion_environment_id", None)
        or data.get("fusion_environment_id"),
        lifecycle_state=getattr(obj, "lifecycle_state", None)
        or data.get("lifecycle_state"),
        actions=actions,
        time_created=getattr(obj, "time_created", None) or data.get("time_created"),
        time_scheduled_start=getattr(obj, "time_scheduled_start", None)
        or data.get("time_scheduled_start"),
        time_expected_finish=getattr(obj, "time_expected_finish", None)
        or data.get("time_expected_finish"),
        time_finished=getattr(obj, "time_finished", None) or data.get("time_finished"),
        delay_in_hours=getattr(obj, "delay_in_hours", None)
        or data.get("delay_in_hours"),
        service_availability=getattr(obj, "service_availability", None)
        or data.get("service_availability"),
        time_updated=getattr(obj, "time_updated", None) or data.get("time_updated"),
        lifecycle_details=getattr(obj, "lifecycle_details", None)
        or data.get("lifecycle_details"),
        scheduled_activity_phase=getattr(obj, "scheduled_activity_phase", None)
        or data.get("scheduled_activity_phase"),
        scheduled_activity_association_id=getattr(
            obj, "scheduled_activity_association_id", None
        )
        or data.get("scheduled_activity_association_id"),
        freeform_tags=getattr(obj, "freeform_tags", None) or data.get("freeform_tags"),
        defined_tags=getattr(obj, "defined_tags", None) or data.get("defined_tags"),
    )


class Subscription(BaseModel):
    """
    Subscription information for a root compartment or tenancy.

    Attributes:
      - id: OCID of the subscription details for a particular root compartment or tenancy.
      - classic_subscription_id: Subscription id.
      - service_name: The type of subscription, such as 'CLOUDCM'/'SAAS'/'CRM', etc.
      - lifecycle_state: Lifecycle state of the subscription.
      - lifecycle_details: Subscription resource intermediate states.
      - skus: Stock keeping unit list.
    """

    id: Optional[str] = Field(
        None,
        description="OCID of the subscription details for particular root compartment or tenancy.",
    )
    classic_subscription_id: Optional[str] = Field(None, description="Subscription id.")
    service_name: Optional[str] = Field(
        None,
        description="The type of subscription, such as 'CLOUDCM'/'SAAS'/'CRM', etc.",
    )
    lifecycle_state: Optional[str] = Field(
        None, description="Lifecycle state of the subscription."
    )
    lifecycle_details: Optional[str] = Field(
        None, description="Subscription resource intermediate states."
    )
    skus: Optional[List[Dict[str, Any]]] = Field(
        None, description="Stock keeping unit list."
    )


def map_subscription(obj: Any) -> Optional[Subscription]:
    """Convert an OCI SDK Subscription model (or dict) into Pydantic Subscription."""
    if not obj:
        return None
    data = _oci_to_dict(obj) or {}

    raw_skus = getattr(obj, "skus", None) or data.get("skus")
    skus: Optional[List[Dict[str, Any]]] = None
    if raw_skus is not None:
        skus = []
        for it in raw_skus:
            skus.append(_oci_to_dict(it) or it)

    return Subscription(
        id=getattr(obj, "id", None) or data.get("id"),
        classic_subscription_id=getattr(obj, "classic_subscription_id", None)
        or data.get("classic_subscription_id"),
        service_name=getattr(obj, "service_name", None) or data.get("service_name"),
        lifecycle_state=getattr(obj, "lifecycle_state", None)
        or data.get("lifecycle_state"),
        lifecycle_details=getattr(obj, "lifecycle_details", None)
        or data.get("lifecycle_details"),
        skus=skus,
    )


class SubscriptionDetail(BaseModel):
    """
    Detail for the FusionEnvironmentFamily subscription.

    Attributes:
      - subscriptions: List of subscriptions.
    """

    subscriptions: Optional[List[Subscription]] = Field(
        None, description="List of subscriptions."
    )


def map_subscription_detail(obj: Any) -> Optional[SubscriptionDetail]:
    """Convert an OCI SDK SubscriptionDetail model (or dict) into Pydantic SubscriptionDetail."""
    if not obj:
        return None

    raw_subs = getattr(obj, "subscriptions", None)
    if raw_subs is None and isinstance(obj, dict):
        raw_subs = obj.get("subscriptions")

    subs: List[Subscription] = []
    if raw_subs:
        for it in raw_subs:
            mapped = map_subscription(it)
            if mapped:
                subs.append(mapped)

    return SubscriptionDetail(subscriptions=subs)
