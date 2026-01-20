"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# All mock data keys use camelCase to align with OCI SDK JSON expectations.

FUSION_ENVIRONMENT_FAMILIES = [
    {
        "id": "ocid1.fusionenvironmentfamily.oc1..mock-family-1",
        "displayName": "Mock Family 1",
        "lifecycleState": "ACTIVE",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "timeCreated": "2026-01-15T12:00:00Z",
    },
    {
        "id": "ocid1.fusionenvironmentfamily.oc1..mock-family-2",
        "displayName": "Mock Family 1",
        "lifecycleState": "ACTIVE",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "timeCreated": "2026-01-15T12:00:00Z",
    },
]

FUSION_ENVIRONMENTS = [
    {
        "id": "ocid1.fusionenvironment.oc1..mock-env-1",
        "displayName": "Mock Env 1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "fusionEnvironmentFamilyId": "ocid1.fusionenvironmentfamily.oc1..mock-family-1",
        "fusionEnvironmentType": "TEST",
        "version": "25C",
        "publicUrl": "https://mock-env1.example.com",
        "lifecycleState": "ACTIVE",
        "timeCreated": "2026-01-15T13:00:00Z",
    },
    {
        "id": "ocid1.fusionenvironment.oc1..mock-env-2",
        "displayName": "Mock Env 2",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "fusionEnvironmentFamilyId": "ocid1.fusionenvironmentfamily.oc1..mock-family-1",
        "fusionEnvironmentType": "PRODUCTION",
        "version": "25C",
        "publicUrl": "https://mock-env2.example.com",
        "lifecycleState": "ACTIVE",
        "timeCreated": "2026-01-15T14:00:00Z",
    },
]

FUSION_ENVIRONMENT_STATUSES = [
    {
        "fusionEnvironmentId": "ocid1.fusionenvironment.oc1..mock-env-1",
        "status": "AVAILABLE",
        "timeUpdated": "2026-01-15T15:00:00Z",
    },
    {
        "fusionEnvironmentId": "ocid1.fusionenvironment.oc1..mock-env-2",
        "status": "AVAILABLE",
        "timeUpdated": "2026-01-15T15:00:00Z",
    },
]
