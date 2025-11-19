# models.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Compartment(BaseModel):
    """Represents a compartment entry from list_compartments()."""
    compartment_ocid: str = Field(..., description="OCID of the compartment")
    name: str
    lifecycle_state: Optional[str] = None
    is_accessible: Optional[bool] = None


class ProtectedDatabase(BaseModel):
    """Flattened view of a protected database from Recovery Service."""
    protected_database_id: Optional[str] = Field(
        None, description="OCID of the protected database in Recovery Service"
    )
    display_name: Optional[str] = None
    db_unique_name: Optional[str] = None
    database_id: Optional[str] = Field(
        None, description="OCID of the source DB (ADB, DB System, or ExaCS)"
    )
    compartment_id: Optional[str] = None

    # Health / lifecycle
    health: Optional[str] = None
    health_details: Optional[str] = None
    lifecycle_state: Optional[str] = None
    time_created: Optional[datetime] = None

    # Metrics (flattened)
    database_size_in_gbs: Optional[float] = None
    backup_space_used_in_gbs: Optional[float] = None
    backup_space_estimate_in_gbs: Optional[float] = None
    retention_period_in_days: Optional[int] = None
    current_retention_period_in_seconds: Optional[int] = None
    minimum_recovery_needed: Optional[float] = Field(
        None,
        description="Minimum recovery needed (from minimum_recovery_needed_in_days in metrics)",
    )
    unprotected_window_in_seconds: Optional[int] = Field(
        None,
        description="Estimated time window of unprotected data in seconds (RPO)",
    )
    is_redo_logs_enabled: Optional[bool] = None

    # Protection policy / vault
    protection_policy_id: Optional[str] = None
    protection_policy_name: Optional[str] = None
    policy_locked_date_time: Optional[datetime] = None
    recovery_service_vault_id: Optional[str] = None

    # Other flags
    is_redo_transmission_enabled: Optional[bool] = None
    description: Optional[str] = None


class TenancyCostSummary(BaseModel):
    """Summary view of cost information from Usage API."""
    start: str
    end: str
    granularity: str
    total_computed_amount: float
    total_computed_usage: float
    items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Raw Usage API line items as dicts",
    )
