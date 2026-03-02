"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# Availability Domains
ADS = [
    {
        "name": "aNMj:US-ASHBURN-AD-1",
        "id": "ocid1.ad.oc1..1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
    },
    {
        "name": "aNMj:US-ASHBURN-AD-2",
        "id": "ocid1.ad.oc1..2",
        "compartmentId": "ocid1.tenancy.oc1..mock",
    },
]

# Tenancy
TENANCY = {
    "id": "ocid1.tenancy.oc1..mock",
    "name": "mock-tenancy",
    "description": "Mock tenancy for tests",
    "homeRegionKey": "MOCK",
}

# User (current user)
USER = {
    "id": "ocid1.user.oc1..mock",
    "compartmentId": TENANCY["id"],
    "name": "mock.user@oracle.com",
    "description": "Mock user",
    "email": "mock.user@oracle.com",
    "emailVerified": True,
}

# Compartments (children of tenancy and nested example)
COMPARTMENTS = [
    {
        "id": "ocid1.compartment.oc1..root",
        "compartmentId": TENANCY["id"],
        "name": "root",
        "description": "Root compartment",
        "lifecycleState": "ACTIVE",
    },
    {
        "id": "ocid1.compartment.oc1..dev",
        "compartmentId": TENANCY["id"],
        "name": "Dev",
        "description": "Development",
        "lifecycleState": "ACTIVE",
    },
    {
        "id": "ocid1.compartment.oc1..dev-sub",
        "compartmentId": "ocid1.compartment.oc1..dev",
        "name": "Dev-Sub",
        "description": "Nested under Dev",
        "lifecycleState": "ACTIVE",
    },
]

# Region subscriptions for the tenancy
REGION_SUBSCRIPTIONS = [
    {
        "regionKey": "MOCK",
        "regionName": "us-mock-1",
        "status": "READY",
        "isHomeRegion": True,
    },
]
