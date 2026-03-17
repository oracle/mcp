"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# Alarms
ALARMS = [
    {
        "id": "ocid1.alarm.oc1..mock-alarm-1",
        "displayName": "High CPU Alarm",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "metricCompartmentId": "ocid1.tenancy.oc1..mock",
        "namespace": "oci_computeagent",
        "query": "CpuUtilization[1m].mean() > 80",
        "severity": "CRITICAL",
        "lifecycleState": "ACTIVE",
        "isEnabled": True,
        "timeCreated": "2026-01-15T10:00:00Z",
        "timeUpdated": "2026-01-15T11:00:00Z",
    }
]

# Metric Definitions
METRICS = [
    {
        "name": "CpuUtilization",
        "namespace": "oci_computeagent",
        "resourceGroup": "mock-resource-group",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "dimensions": {"resourceId": "ocid1.instance.oc1..mock-uuid-1"},
    }
]

# Metric Data (Summarized)
METRIC_DATA = [
    {
        "namespace": "oci_computeagent",
        "resourceGroup": "mock-resource-group",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "name": "CpuUtilization",
        "dimensions": {"resourceId": "ocid1.instance.oc1..mock-uuid-1"},
        "metadata": {"displayName": "CpuUtilization", "unit": "Percent"},
        "aggregatedDatapoints": [
            {"timestamp": "2026-01-15T12:00:00Z", "value": 45.5},
            {"timestamp": "2026-01-15T12:01:00Z", "value": 50.2},
        ],
    }
]
