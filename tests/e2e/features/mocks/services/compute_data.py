"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

INSTANCES = [
    {
        "id": "ocid1.instance.oc1..mock-uuid-1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "displayName": "Mock-Server-1",
        "lifecycleState": "RUNNING",
        "availabilityDomain": "aNMj:US-ASHBURN-AD-1",
        "shape": "VM.Standard.E5.Flex",
        "timeCreated": "2026-01-13T10:00:00Z",
    },
    {
        "id": "ocid1.instance.oc1..mock-uuid-2",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "displayName": "Mock-Server-2",
        "lifecycleState": "RUNNING",
        "availabilityDomain": "aNMj:US-ASHBURN-AD-1",
        "shape": "VM.Standard.E5.Flex",
        "timeCreated": "2026-01-13T10:00:00Z",
    },
]

IMAGES = [
    {
        "id": "ocid1.image.oc1..oraclelinux9",
        "operatingSystem": "Oracle Linux",
        "operatingSystemVersion": "9",
        "displayName": "Oracle-Linux-9.4-2024.05.29-0",
    }
]

VNIC_ATTACHMENTS = [
    {
        "id": "ocid1.vnicattachment.oc1..mock-vnic-1",
        "instanceId": "ocid1.instance.oc1..mock-uuid-1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "lifecycleState": "ATTACHED",
        "vnicId": "ocid1.vnic.oc1..mock-vnic-core-1",
    }
]
