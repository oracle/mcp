"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Dict, Optional

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
