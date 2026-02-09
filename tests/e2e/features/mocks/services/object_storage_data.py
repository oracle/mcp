"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# CamelCase keys to mimic OCI SDK JSON structures

NAMESPACE = "mock-namespace"

BUCKETS = [
    {
        "namespace": NAMESPACE,
        "name": "mcp-e2e-bucket",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "createdBy": "ocid1.user.oc1..mock",
        "timeCreated": "2026-01-01T00:00:00Z",
        "etag": "etag-001",
        "freeformTags": {"env": "test"},
        "definedTags": {},
    },
    {
        "namespace": NAMESPACE,
        "name": "mcp-e2e-logs",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "createdBy": "ocid1.user.oc1..mock",
        "timeCreated": "2026-01-02T00:00:00Z",
        "etag": "etag-002",
        "freeformTags": {},
        "definedTags": {"ops": {"team": "mcp"}},
    },
]

# Full bucket details keyed by bucket name
BUCKET_DETAILS = {
    "mcp-e2e-bucket": {
        "namespace": NAMESPACE,
        "name": "mcp-e2e-bucket",
        "id": "ocid1.bucket.oc1..mock-bucket-1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "timeCreated": "2026-01-01T00:00:00Z",
        "etag": "etag-001",
        "publicAccessType": "NoPublicAccess",
        "storageTier": "Standard",
        "objectEventsEnabled": False,
        "freeformTags": {"env": "test"},
        "definedTags": {},
        "kmsKeyId": None,
        "objectLifecyclePolicyEtag": None,
        "approximateCount": 2,
        "approximateSize": 2048,
        "replicationEnabled": False,
        "isReadOnly": False,
        "versioning": "Enabled",
        "autoTiering": "InfrequentAccess",
    },
    "mcp-e2e-logs": {
        "namespace": NAMESPACE,
        "name": "mcp-e2e-logs",
        "id": "ocid1.bucket.oc1..mock-bucket-2",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "timeCreated": "2026-01-02T00:00:00Z",
        "etag": "etag-002",
        "publicAccessType": "NoPublicAccess",
        "storageTier": "Standard",
        "objectEventsEnabled": False,
        "freeformTags": {},
        "definedTags": {"ops": {"team": "mcp"}},
        "kmsKeyId": None,
        "objectLifecyclePolicyEtag": None,
        "approximateCount": 1,
        "approximateSize": 1024,
        "replicationEnabled": False,
        "isReadOnly": False,
        "versioning": "Disabled",
        "autoTiering": "Disabled",
    },
}

# Objects per bucket
OBJECTS = {
    "mcp-e2e-bucket": {
        "objects": [
            {
                "name": "file1.txt",
                "size": 1234,
                "md5": "d41d8cd98f00b204e9800998ecf8427e",
                "timeCreated": "2026-01-03T12:00:00Z",
                "etag": "o-etag-001",
                "storageTier": "Standard",
                "archivalState": None,
                "timeModified": "2026-01-03T12:00:00Z",
            },
            {
                "name": "file2.log",
                "size": 814,
                "md5": "098f6bcd4621d373cade4e832627b4f6",
                "timeCreated": "2026-01-03T13:00:00Z",
                "etag": "o-etag-002",
                "storageTier": "Standard",
                "archivalState": None,
                "timeModified": "2026-01-03T13:00:00Z",
            },
        ],
        "prefixes": ["dir1/"],
        "nextStartWith": None,
    },
    "mcp-e2e-logs": {
        "objects": [
            {
                "name": "app.log",
                "size": 1024,
                "md5": "098f6bcd4621d373cade4e832627b4f6",
                "timeCreated": "2026-01-04T13:00:00Z",
                "etag": "o-etag-010",
                "storageTier": "Standard",
                "archivalState": None,
                "timeModified": "2026-01-04T13:00:00Z",
            }
        ],
        "prefixes": [],
        "nextStartWith": None,
    },
}

OBJECT_VERSIONS = {
    "mcp-e2e-bucket": {
        "items": [
            {
                "name": "file1.txt",
                "size": 1234,
                "md5": "d41d8cd98f00b204e9800998ecf8427e",
                "timeCreated": "2026-01-03T12:00:00Z",
                "timeModified": "2026-01-03T12:00:00Z",
                "etag": "v-etag-001",
                "storageTier": "Standard",
                "archivalState": None,
                "versionId": "version_1",
                "isDeleteMarker": False,
            },
            {
                "name": "file1.txt",
                "size": 1230,
                "md5": "e41d8cd98f00b204e9800998ecf8427e",
                "timeCreated": "2026-01-02T10:00:00Z",
                "timeModified": "2026-01-02T10:00:00Z",
                "etag": "v-etag-000",
                "storageTier": "Standard",
                "archivalState": None,
                "versionId": "version_0",
                "isDeleteMarker": False,
            },
        ],
        "prefixes": ["dir1/"],
    },
    "mcp-e2e-logs": {
        "items": [],
        "prefixes": [],
    },
}
