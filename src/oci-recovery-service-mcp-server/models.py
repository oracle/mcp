from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Compartment(BaseModel):
    """Represents a compartment entry from list_compartments()."""

    compartment_ocid: str = Field(
        ...,
        description="OCID of the compartment returned by OCI Identity.",
    )
    name: str = Field(
        ...,
        description="Human-readable name of the compartment.",
    )
    lifecycle_state: Optional[str] = Field(
        None,
        description="Lifecycle state of the compartment (e.g. ACTIVE, DELETING, DELETED).",
    )
    is_accessible: Optional[bool] = Field(
        None,
        description="Whether the current principal has ACCESSIBLE visibility into the compartment.",
    )

    @classmethod
    def from_oci(cls, c: Any) -> "Compartment":
        """Create a Compartment model from an OCI SDK Compartment object."""
        return cls(
            compartment_ocid=c.id,
            name=c.name,
            lifecycle_state=getattr(c, "lifecycle_state", None),
            is_accessible=getattr(c, "is_accessible", None),
        )


class ProtectedDatabase(BaseModel):
    """Flattened view of a protected database from Recovery Service."""

    # Identity / location
    protected_database_id: Optional[str] = Field(
        None,
        description="OCID of the protected database resource in Recovery Service.",
    )
    display_name: Optional[str] = Field(
        None,
        description="Human-readable display name of the protected database.",
    )
    db_unique_name: Optional[str] = Field(
        None,
        description="Oracle Database unique name for the protected database.",
    )
    database_id: Optional[str] = Field(
        None,
        description="OCID of the source/original database (ADB, DB System, or Exadata Cloud Service).",
    )
    compartment_id: Optional[str] = Field(
        None,
        description="OCID of the compartment that contains the protected database.",
    )

    # Health / lifecycle
    health: Optional[str] = Field(
        None,
        description="High-level health status of the database backups in Recovery Service.",
    )
    health_details: Optional[str] = Field(
        None,
        description="Detailed explanation of backup health or any detected issues.",
    )
    lifecycle_state: Optional[str] = Field(
        None,
        description="Lifecycle state of the protected database resource (e.g. ACTIVE, UPDATING, DELETING, DELETED, FAILED).",
    )
    time_created: Optional[datetime] = Field(
        None,
        description="Timestamp when the database was registered with Recovery Service.",
    )

    # Metrics (flattened)
    database_size_in_gbs: Optional[float] = Field(
        None,
        description="Approximate size of the source database, in GiB.",
    )
    backup_space_used_in_gbs: Optional[float] = Field(
        None,
        description="Total backup space currently consumed for this database in ARS, in GiB.",
    )
    backup_space_estimate_in_gbs: Optional[float] = Field(
        None,
        description="Estimated full backup space required to satisfy the configured recovery window, in GiB.",
    )
    retention_period_in_days: Optional[int] = Field(
        None,
        description="Configured backup retention period in days.",
    )
    current_retention_period_in_seconds: Optional[int] = Field(
        None,
        description="Current effective retention window length, in seconds.",
    )
    minimum_recovery_needed: Optional[float] = Field(
        None,
        description=(
            "Minimum recovery needed (derived from minimum_recovery_needed_in_days in metrics). "
            "Represents the minimum amount of redo that must be applied for recovery."
        ),
    )
    unprotected_window_in_seconds: Optional[int] = Field(
        None,
        description=(
            "Estimated time window of unprotected data (recovery gap) in seconds. "
            "This effectively corresponds to the Recovery Point Objective (RPO)."
        ),
    )
    is_redo_logs_enabled: Optional[bool] = Field(
        None,
        description="Indicates whether redo log shipping to Recovery Service is enabled.",
    )

    # Protection policy / vault
    protection_policy_id: Optional[str] = Field(
        None,
        description="OCID of the protection policy currently applied to this protected database.",
    )
    protection_policy_name: Optional[str] = Field(
        None,
        description="Display name of the protection policy applied to this database, if resolvable.",
    )
    policy_locked_date_time: Optional[datetime] = Field(
        None,
        description=(
            "Timestamp until which backups are immutable/locked by the protection policy. "
            "Represents the 'lock until' time for backup immutability."
        ),
    )
    recovery_service_vault_id: Optional[str] = Field(
        None,
        description="OCID of the Recovery Service vault that stores this database's backups.",
    )

    # Other flags
    is_redo_transmission_enabled: Optional[bool] = Field(
        None,
        description="Whether redo data is transmitted to Recovery Service in near real-time.",
    )
    description: Optional[str] = Field(
        None,
        description="Optional free-form description for the protected database resource.",
    )

    @classmethod
    def from_oci(cls, p: Any, policy_name: Optional[str] = None) -> "ProtectedDatabase":
        """
        Create a ProtectedDatabase model from an OCI SDK ProtectedDatabaseSummary
        (or similar) object plus an optional resolved protection policy name.
        """
        metrics = getattr(p, "metrics", None)

        return cls(
            protected_database_id=getattr(p, "id", None),
            display_name=getattr(p, "display_name", None),
            db_unique_name=getattr(p, "db_unique_name", None),
            database_id=getattr(p, "database_id", None),
            compartment_id=getattr(p, "compartment_id", None),
            health=getattr(p, "health", None),
            health_details=getattr(p, "health_details", None),
            lifecycle_state=getattr(p, "lifecycle_state", None),
            time_created=getattr(p, "time_created", None),
            database_size_in_gbs=getattr(metrics, "db_size_in_gbs", None),
            backup_space_used_in_gbs=getattr(metrics, "backup_space_used_in_gbs", None),
            minimum_recovery_needed=getattr(
                metrics, "minimum_recovery_needed_in_days", None
            ),
            unprotected_window_in_seconds=getattr(
                metrics, "unprotected_window_in_seconds", None
            ),
            retention_period_in_days=getattr(
                metrics, "retention_period_in_days", None
            ),
            current_retention_period_in_seconds=getattr(
                metrics, "current_retention_period_in_seconds", None
            ),
            backup_space_estimate_in_gbs=getattr(
                metrics, "backup_space_estimate_in_gbs", None
            ),
            protection_policy_id=getattr(p, "protection_policy_id", None),
            policy_locked_date_time=getattr(p, "policy_locked_date_time", None),
            protection_policy_name=policy_name,
            recovery_service_vault_id=getattr(p, "recovery_service_vault_id", None),
            is_redo_transmission_enabled=getattr(
                p, "is_redo_transmission_enabled", None
            ),
            description=getattr(p, "description", None),
            is_redo_logs_enabled=getattr(p, "is_redo_logs_enabled", None),
        )

# models.py

class RecoveryServiceSubnets(BaseModel):
    """Flattened view of registered subnets from Recovery Service."""

    # Identity / location
    id: Optional[str] = Field(
        None,
        description="OCID of the recovery service subnet resource.",
    )
    display_name: Optional[str] = Field(
        None,
        description="Display name of the recovery service subnet resource.",
    )
    compartment_id: Optional[str] = Field(
        None,
        description="OCID of the compartment that contains the recovery service subnet.",
    )

    # VCN information
    vcn_id: Optional[str] = Field(
        None,
        description="OCID of the VCN containing the recovery service subnet.",
    )
    vcn_name: Optional[str] = Field(
        None,
        description="Human-readable display name of the VCN (resolved via VirtualNetworkClient).",
    )

    # Subnet information
    subnet_id: Optional[str] = Field(
        None,
        description="OCID of the underlying OCI subnet associated with the recovery service subnet.",
    )
    subnet_name: Optional[str] = Field(
        None,
        description="Display name of the underlying OCI subnet (resolved via VirtualNetworkClient).",
    )

    # Lifecycle
    lifecycle_state: Optional[str] = Field(
        None,
        description="Lifecycle state of the recovery service subnet (e.g. ACTIVE, UPDATING, DELETING, DELETED, FAILED).",
    )
    time_created: Optional[datetime] = Field(
        None,
        description="Timestamp when the recovery service subnet was created.",
    )

    @classmethod
    def from_oci(
        cls,
        s: Any,
        subnet_name: Optional[str] = None,
        vcn_name: Optional[str] = None,
    ) -> "RecoveryServiceSubnets":
        """
        Create a RecoveryServiceSubnets model from an OCI SDK RecoveryServiceSubnetSummary
        (or similar) object plus optional resolved VCN and Subnet names.
        """
        return cls(
            id=getattr(s, "id", None),
            display_name=getattr(s, "display_name", None),
            compartment_id=getattr(s, "compartment_id", None),
            lifecycle_state=getattr(s, "lifecycle_state", None),
            time_created=getattr(s, "time_created", None),
            vcn_id=getattr(s, "vcn_id", None),
            subnet_id=getattr(s, "subnet_id", None),
            subnet_name=subnet_name,
            vcn_name=vcn_name,
        )

class TenancyCostSummary(BaseModel):
    """Summary view of cost information from Usage API."""

    start: str = Field(
        ...,
        description="Start of the usage window in ISO-8601 format (UTC, with trailing 'Z').",
    )
    end: str = Field(
        ...,
        description="End of the usage window in ISO-8601 format (UTC, with trailing 'Z').",
    )
    granularity: str = Field(
        ...,
        description="Aggregation granularity used for summarization (e.g. DAILY or MONTHLY).",
    )
    total_computed_amount: float = Field(
        ...,
        description="Total cost (e.g. in the tenancy's billing currency) over the window.",
    )
    total_computed_usage: float = Field(
        ...,
        description="Total usage quantity over the window (units depend on the service and metric).",
    )
    items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Raw Usage API summarized usage line items as dictionaries, "
            "one per resourceId/interval/grouping."
        ),
    )

    @classmethod
    def from_usage_api(
        cls,
        start: datetime,
        end: datetime,
        granularity: str,
        rows: List[Dict[str, Any]],
    ) -> "TenancyCostSummary":
        """
        Build a TenancyCostSummary from raw Usage API rows and time bounds.
        """
        total_cost = sum((r.get("computed_amount", 0) or 0) for r in rows)
        total_usage = sum((r.get("computed_quantity", 0) or 0) for r in rows)

        return cls(
            start=start.isoformat() + "Z",
            end=end.isoformat() + "Z",
            granularity=granularity,
            total_computed_amount=total_cost,
            total_computed_usage=total_usage,
            items=rows,
        )
