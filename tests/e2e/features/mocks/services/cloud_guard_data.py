"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# All mock data keys use camelCase to align with OCI SDK JSON expectations.

PROBLEMS = [
    {
        "id": "ocid1.cloudguardproblem.oc1..mock-problem-1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "detectorRuleId": "ocid1.cloudguarddetectorrule.oc1..mock-rule-1",
        "regions": ["us-mock-1"],
        "riskLevel": "HIGH",
        "riskScore": 73.2,
        "resourceId": "ocid1.instance.oc1..mock-uuid-1",
        "resourceName": "Mock-Server-1",
        "resourceType": "instance",
        "labels": ["public", "open-ssh"],
        "timeLastDetected": "2026-01-13T10:00:00Z",
        "timeFirstDetected": "2026-01-12T09:00:00Z",
        "lifecycleState": "ACTIVE",
        "lifecycleDetail": "OPEN",
        "detectorId": "IAAS_CONFIGURATION_DETECTOR",
        "targetId": "ocid1.cloudguardtarget.oc1..mock-target-1",
        "additionalDetails": {"port": "22", "protocol": "tcp"},
        "description": "Security group allows SSH from 0.0.0.0/0",
        "recommendation": "Restrict SSH access to known IP ranges",
    },
    {
        "id": "ocid1.cloudguardproblem.oc1..mock-problem-2",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "detectorRuleId": "ocid1.cloudguarddetectorrule.oc1..mock-rule-2",
        "regions": ["us-mock-1"],
        "riskLevel": "MEDIUM",
        "riskScore": 55.0,
        "resourceId": "ocid1.object.oc1..mock-object-1",
        "resourceName": "Mock-Bucket-1",
        "resourceType": "bucket",
        "labels": ["public-read"],
        "timeLastDetected": "2026-01-13T11:00:00Z",
        "timeFirstDetected": "2026-01-12T08:30:00Z",
        "lifecycleState": "ACTIVE",
        "lifecycleDetail": "OPEN",
        "detectorId": "IAAS_ACTIVITY_DETECTOR",
        "targetId": "ocid1.cloudguardtarget.oc1..mock-target-2",
        "description": "Bucket allows public reads",
        "recommendation": "Disable public access for buckets",
    },
]
