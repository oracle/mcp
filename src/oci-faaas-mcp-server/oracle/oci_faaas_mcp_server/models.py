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
