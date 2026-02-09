"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# Mock data for OCI Resource Search service (camelCase keys)

RESOURCE_TYPES = [
    {"name": "instance"},
    {"name": "vcn"},
    {"name": "subnet"},
    {"name": "volume"},
    {"name": "bucket"},
]

RESOURCES = [
    {
        "resourceType": "Instance",
        "identifier": "ocid1.instance.oc1..mock-uuid-1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "timeCreated": "2026-01-13T10:00:00Z",
        "displayName": "Mock-Server-1",
        "availabilityDomain": "aNMj:US-ASHBURN-AD-1",
        "lifecycleState": "RUNNING",
        "freeformTags": {"Department": "Finance"},
        "definedTags": {"Operations": {"CostCenter": "42"}},
        "systemTags": {"orcl-cloud": {"free-tier-retain": True}},
        "searchContext": {"highlights": {"displayName": ["<h1>Mock</h1>-Server-1"]}},
        "identityContext": None,
        "additionalDetails": None,
    },
    {
        "resourceType": "Subnet",
        "identifier": "ocid1.subnet.oc1..mock-subnet-1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "timeCreated": "2026-01-13T10:00:00Z",
        "displayName": "Mock-Subnet-1",
        "lifecycleState": "AVAILABLE",
        "freeformTags": {},
        "definedTags": {},
        "systemTags": {},
        "searchContext": None,
        "identityContext": None,
        "additionalDetails": None,
    },
]
