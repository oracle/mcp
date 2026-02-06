"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

CONTAINER_REPOSITORIES = [
    {
        "id": "ocid1.containerrepo.oc1..mock-repo-1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "displayName": "mytenant/app1",
        "imageCount": 3,
        "isImmutable": False,
        "isPublic": False,
        "layerCount": 10,
        "layersSizeInBytes": 12345678,
        "lifecycleState": "AVAILABLE",
        "namespace": "mytenant",
        "timeCreated": "2026-01-10T10:00:00Z",
        "timeLastPushed": "2026-01-13T11:00:00Z",
        "freeformTags": {"env": "test"},
    },
    {
        "id": "ocid1.containerrepo.oc1..mock-repo-2",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "displayName": "mytenant/app2",
        "imageCount": 5,
        "isImmutable": True,
        "isPublic": True,
        "layerCount": 20,
        "layersSizeInBytes": 22334455,
        "lifecycleState": "AVAILABLE",
        "namespace": "mytenant",
        "timeCreated": "2026-01-12T08:30:00Z",
        "timeLastPushed": "2026-01-15T09:45:00Z",
        "definedTags": {"Operations": {"CostCenter": "42"}},
    },
]
