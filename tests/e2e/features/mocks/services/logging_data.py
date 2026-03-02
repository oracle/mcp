"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# All mock data keys use camelCase to align with OCI SDK JSON expectations.

LOG_GROUPS = [
    {
        "id": "ocid1.loggroup.oc1..mock-lg-1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "displayName": "Mock Log Group 1",
        "description": "Test log group",
        "lifecycleState": "ACTIVE",
        "timeCreated": "2026-01-15T10:00:00Z",
        "timeLastModified": "2026-01-15T11:00:00Z",
    }
]

LOGS = [
    {
        "id": "ocid1.log.oc1..mock-log-1",
        "displayName": "Mock-Service-Log",
        "logGroupId": "ocid1.loggroup.oc1..mock-lg-1",
        "logType": "SERVICE",
        "lifecycleState": "ACTIVE",
        "configuration": {
            "source": {
                "sourceType": "OCISERVICE",
                "service": "compute",
                "resource": "ocid1.instance.oc1..mock-uuid-1",
                "category": "all",
            }
        },
        "isEnabled": True,
        "retentionDuration": 30,
        "timeCreated": "2026-01-13T10:00:00Z",
    }
]
