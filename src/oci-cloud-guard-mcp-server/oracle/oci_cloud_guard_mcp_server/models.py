"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

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


class ResourceLock(BaseModel):
    """
    Pydantic model mirroring oci.cloud_guard.models.ResourceLock
    (subset needed for Problem.locks).
    """

    type: Optional[Literal["FULL", "DELETE", "UNKNOWN_ENUM_VALUE"]] = Field(
        None, description="Type of the lock."
    )
    related_resource_id: Optional[str] = Field(
        None,
        description=(
            "The ID of the resource that is locking this resource. Deleting the "
            "related resource will remove the lock."
        ),
    )
    message: Optional[str] = Field(
        None,
        description=(
            "A message added by the creator of the lock, typically indicating why "
            "the resource is locked."
        ),
    )
    time_created: Optional[datetime] = Field(
        None, description="When the lock was created (RFC3339)."
    )


class Problem(BaseModel):
    """
    Pydantic model mirroring oci.cloud_guard.models.Problem.
    """

    id: Optional[str] = Field(
        None, description="Unique identifier that can't be changed after creation."
    )
    compartment_id: Optional[str] = Field(
        None, description="Compartment OCID where the resource is created."
    )
    detector_rule_id: Optional[str] = Field(
        None,
        description="Unique identifier of the detector rule that triggered the problem.",
    )
    region: Optional[str] = Field(None, description="DEPRECATED.")
    regions: Optional[List[str]] = Field(
        None, description="Regions where the problem is found."
    )
    risk_level: Optional[
        Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINOR", "UNKNOWN_ENUM_VALUE"]
    ] = Field(None, description="The risk level for the problem.")
    risk_score: Optional[float] = Field(
        None, description="The risk score for the problem."
    )
    peak_risk_score_date: Optional[str] = Field(
        None,
        description=(
            "The date and time for the peak risk score observed for the problem (RFC3339)."
        ),
    )
    peak_risk_score: Optional[float] = Field(
        None, description="Peak risk score for the problem."
    )
    auto_resolve_date: Optional[str] = Field(
        None,
        description="The date and time when the problem will be auto resolved (RFC3339).",
    )
    peak_risk_score_lookup_period_in_days: Optional[int] = Field(
        None,
        description="Number of days for which peak score is calculated for the problem.",
    )
    resource_id: Optional[str] = Field(
        None, description="Unique identifier of the resource affected by the problem."
    )
    resource_name: Optional[str] = Field(
        None, description="Display name of the affected resource."
    )
    resource_type: Optional[str] = Field(
        None, description="Type of the affected resource."
    )
    labels: Optional[List[str]] = Field(
        None, description="User-defined labels on the problem."
    )
    time_last_detected: Optional[datetime] = Field(
        None, description="The date and time the problem was last detected (RFC3339)."
    )
    time_first_detected: Optional[datetime] = Field(
        None, description="The date and time the problem was first detected (RFC3339)."
    )
    lifecycle_state: Optional[Literal["ACTIVE", "INACTIVE", "UNKNOWN_ENUM_VALUE"]] = (
        Field(None, description="The current lifecycle state of the problem.")
    )
    lifecycle_detail: Optional[
        Literal["OPEN", "RESOLVED", "DISMISSED", "DELETED", "UNKNOWN_ENUM_VALUE"]
    ] = Field(
        None, description="Additional details on the substate of the lifecycle state."
    )
    detector_id: Optional[
        Literal[
            "IAAS_ACTIVITY_DETECTOR",
            "IAAS_CONFIGURATION_DETECTOR",
            "IAAS_THREAT_DETECTOR",
            "IAAS_LOG_INSIGHT_DETECTOR",
            "IAAS_INSTANCE_SECURITY_DETECTOR",
            "IAAS_CONTAINER_SECURITY_DETECTOR",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(
        None,
        description="Unique identifier of the detector that triggered the problem.",
    )
    target_id: Optional[str] = Field(
        None, description="Unique identifier of the target associated with the problem."
    )
    additional_details: Optional[Dict[str, str]] = Field(
        None, description="Additional details of the problem as key/value pairs."
    )
    description: Optional[str] = Field(None, description="Description of the problem.")
    recommendation: Optional[str] = Field(
        None, description="Recommendation for the problem."
    )
    comment: Optional[str] = Field(None, description="User comments on the problem.")
    impacted_resource_id: Optional[str] = Field(
        None, description="Unique identifier of the resource impacted by the problem."
    )
    impacted_resource_name: Optional[str] = Field(
        None, description="Display name of the impacted resource."
    )
    impacted_resource_type: Optional[str] = Field(
        None, description="Type of the impacted resource."
    )
    locks: Optional[List[ResourceLock]] = Field(
        None, description="Locks associated with this resource."
    )


def map_resource_lock(rl) -> ResourceLock | None:
    if not rl:
        return None
    return ResourceLock(
        type=getattr(rl, "type", None),
        related_resource_id=getattr(rl, "related_resource_id", None),
        message=getattr(rl, "message", None),
        time_created=getattr(rl, "time_created", None),
    )


def map_resource_locks(items) -> list[ResourceLock] | None:
    if not items:
        return None
    result: list[ResourceLock] = []
    for it in items:
        result.append(map_resource_lock(it))
    return result


def map_problem(problem_data: oci.cloud_guard.models.Problem) -> Problem:
    """
    Convert an oci.cloud_guard.models.Problem to oracle.oci_cloud_guard_mcp_server.models.Problem.
    """
    return Problem(
        id=getattr(problem_data, "id", None),
        compartment_id=getattr(problem_data, "compartment_id", None),
        detector_rule_id=getattr(problem_data, "detector_rule_id", None),
        region=getattr(problem_data, "region", None),
        regions=getattr(problem_data, "regions", None),
        risk_level=getattr(problem_data, "risk_level", None),
        risk_score=getattr(problem_data, "risk_score", None),
        peak_risk_score_date=getattr(problem_data, "peak_risk_score_date", None),
        peak_risk_score=getattr(problem_data, "peak_risk_score", None),
        auto_resolve_date=getattr(problem_data, "auto_resolve_date", None),
        peak_risk_score_lookup_period_in_days=getattr(
            problem_data, "peak_risk_score_lookup_period_in_days", None
        ),
        resource_id=getattr(problem_data, "resource_id", None),
        resource_name=getattr(problem_data, "resource_name", None),
        resource_type=getattr(problem_data, "resource_type", None),
        labels=getattr(problem_data, "labels", None),
        time_last_detected=getattr(problem_data, "time_last_detected", None),
        time_first_detected=getattr(problem_data, "time_first_detected", None),
        lifecycle_state=getattr(problem_data, "lifecycle_state", None),
        lifecycle_detail=getattr(problem_data, "lifecycle_detail", None),
        detector_id=getattr(problem_data, "detector_id", None),
        target_id=getattr(problem_data, "target_id", None),
        additional_details=getattr(problem_data, "additional_details", None),
        description=getattr(problem_data, "description", None),
        recommendation=getattr(problem_data, "recommendation", None),
        comment=getattr(problem_data, "comment", None),
        impacted_resource_id=getattr(problem_data, "impacted_resource_id", None),
        impacted_resource_name=getattr(problem_data, "impacted_resource_name", None),
        impacted_resource_type=getattr(problem_data, "impacted_resource_type", None),
        locks=map_resource_locks(getattr(problem_data, "locks", None)),
    )


class UpdateProblemStatusDetails(BaseModel):
    """
    Pydantic model mirroring oci.cloud_guard.models.UpdateProblemStatusDetails.
    """

    status: Optional[
        Literal["OPEN", "RESOLVED", "DISMISSED", "DELETED", "UNKNOWN_ENUM_VALUE"]
    ] = Field(None, description="Action taken by user.")
    comment: Optional[str] = Field(None, description="User comments.")


def map_update_problem_status_details(
    upd: oci.cloud_guard.models.UpdateProblemStatusDetails,
) -> UpdateProblemStatusDetails | None:
    """
    Convert an oci.cloud_guard.models.UpdateProblemStatusDetails to
    oracle.oci_cloud_guard_mcp_server.models.UpdateProblemStatusDetails.
    """
    if not upd:
        return None
    return UpdateProblemStatusDetails(
        status=getattr(upd, "status", None),
        comment=getattr(upd, "comment", None),
    )
