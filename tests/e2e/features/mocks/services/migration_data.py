"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# All mock data keys use camelCase to align with OCI SDK JSON expectations.

MIGRATIONS = [
    {
        "id": "ocid1.migration.oc1..mock-mig-1",
        "displayName": "Mock Migration 1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "lifecycleState": "ACTIVE",
        "lifecycleDetails": "Running",
        "timeCreated": "2026-01-10T10:00:00Z",
        "timeUpdated": "2026-01-11T11:00:00Z",
        "replicationScheduleId": "ocid1.replicationschedule.oc1..mock-rs-1",
        "isCompleted": False,
        "freeformTags": {"env": "dev"},
    },
    {
        "id": "ocid1.migration.oc1..mock-mig-2",
        "displayName": "Mock Migration 2",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "lifecycleState": "NEEDS_ATTENTION",
        "lifecycleDetails": "Configuration required",
        "timeCreated": "2026-01-12T12:00:00Z",
        "timeUpdated": "2026-01-13T13:00:00Z",
        "replicationScheduleId": None,
        "isCompleted": False,
    },
]
