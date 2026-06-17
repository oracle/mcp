"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

FLEETS = [
    {
        "id": "ocid1.jmsfleet.oc1..mock-fleet-1",
        "displayName": "mock-jms-fleet",
        "description": "Mock JMS fleet for e2e coverage",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "approximateJreCount": 7,
        "approximateInstallationCount": 4,
        "approximateApplicationCount": 3,
        "approximateManagedInstanceCount": 2,
        "approximateJavaServerCount": 1,
        "inventoryLog": {
            "logGroupId": "ocid1.loggroup.oc1..mock-jms-inventory",
            "logId": "ocid1.log.oc1..mock-jms-inventory-log",
        },
        "operationLog": {
            "logGroupId": "ocid1.loggroup.oc1..mock-jms-operation",
            "logId": "ocid1.log.oc1..mock-jms-operation-log",
        },
        "isAdvancedFeaturesEnabled": True,
        "isExportSettingEnabled": True,
        "timeCreated": "2026-02-11T10:15:00Z",
        "lifecycleState": "ACTIVE",
        "freeformTags": {"env": "test"},
    }
]

JMS_PLUGINS = [
    {
        "id": "ocid1.jmsplugin.oc1..mock-plugin-1",
        "agentId": "ocid1.managementagent.oc1..mock-agent-1",
        "agentType": "OMA",
        "lifecycleState": "ACTIVE",
        "availabilityStatus": "ACTIVE",
        "fleetId": "ocid1.jmsfleet.oc1..mock-fleet-1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "hostname": "plugin-host-1",
        "osFamily": "LINUX",
        "osArchitecture": "X86_64",
        "osDistribution": "Oracle Linux",
        "pluginVersion": "1.2.3",
        "timeRegistered": "2026-02-11T10:30:00Z",
        "timeLastSeen": "2026-02-12T09:45:00Z",
    },
    {
        "id": "ocid1.jmsplugin.oc1..mock-plugin-2",
        "agentId": "ocid1.managementagent.oc1..mock-agent-2",
        "agentType": "OCA",
        "lifecycleState": "ACTIVE",
        "availabilityStatus": "SILENT",
        "fleetId": "ocid1.jmsfleet.oc1..mock-fleet-1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "hostname": "archive-host-2",
        "osFamily": "LINUX",
        "osArchitecture": "X86_64",
        "osDistribution": "Oracle Linux",
        "pluginVersion": "1.1.8",
        "timeRegistered": "2026-02-10T08:15:00Z",
        "timeLastSeen": "2026-02-10T08:45:00Z",
    }
]

INSTALLATION_SITES = {
    "ocid1.jmsfleet.oc1..mock-fleet-1": [
        {
            "installationKey": "installation-alpha",
            "managedInstanceId": "managed-instance-1",
            "jre": {
                "version": "17.0.12",
                "vendor": "Oracle",
                "distribution": "JDK",
                "jreKey": "jre-17-oracle",
            },
            "securityStatus": "UP_TO_DATE",
            "path": "/usr/lib/jvm/java-17-oracle",
            "operatingSystem": {
                "family": "LINUX",
                "name": "Oracle Linux",
                "distribution": "Oracle Linux",
                "version": "9",
                "architecture": "X86_64",
                "managedInstanceCount": 1,
            },
            "approximateApplicationCount": 2,
            "timeLastSeen": "2026-02-12T09:45:00Z",
            "lifecycleState": "ACTIVE",
        },
        {
            "installationKey": "installation-beta",
            "managedInstanceId": "managed-instance-2",
            "jre": {
                "version": "17.0.10",
                "vendor": "Oracle",
                "distribution": "JDK",
                "jreKey": "jre-17-10-oracle",
            },
            "securityStatus": "UPDATE_REQUIRED",
            "path": "/opt/java/jdk-17.0.10",
            "operatingSystem": {
                "family": "LINUX",
                "name": "Oracle Linux",
                "distribution": "Oracle Linux",
                "version": "8",
                "architecture": "X86_64",
                "managedInstanceCount": 1,
            },
            "approximateApplicationCount": 1,
            "timeLastSeen": "2026-02-13T08:45:00Z",
            "lifecycleState": "ACTIVE",
        }
    ]
}

FLEET_AGENT_CONFIGURATIONS = {
    "ocid1.jmsfleet.oc1..mock-fleet-1": {
        "jreScanFrequencyInMinutes": 30,
        "javaUsageTrackerProcessingFrequencyInMinutes": 15,
        "workRequestValidityPeriodInDays": 7,
        "agentPollingIntervalInMinutes": 5,
        "linuxConfiguration": {
            "includePaths": ["/u01/java", "/usr/lib/jvm"],
            "excludePaths": ["/tmp/java-cache"],
        },
        "windowsConfiguration": {
            "includePaths": ["C:\\Java"],
            "excludePaths": ["C:\\Temp\\Java"],
        },
        "macOsConfiguration": {
            "includePaths": ["/Library/Java/JavaVirtualMachines"],
            "excludePaths": ["/tmp/java-cache"],
        },
        "timeLastModified": "2026-02-12T10:00:00Z",
    }
}

FLEET_ADVANCED_FEATURE_CONFIGURATIONS = {
    "ocid1.jmsfleet.oc1..mock-fleet-1": {
        "analyticNamespace": "mock_jms_namespace",
        "analyticBucketName": "jms_analytics_bucket",
        "lcm": {"isEnabled": True},
        "cryptoEventAnalysis": {"isEnabled": True},
        "advancedUsageTracking": {"isEnabled": True},
        "jfrRecording": {"isEnabled": False},
        "performanceTuningAnalysis": {"isEnabled": False},
        "javaMigrationAnalysis": {"isEnabled": True},
        "timeLastModified": "2026-02-12T10:05:00Z",
    }
}

RESOURCE_INVENTORY = {
    "activeFleetCount": 1,
    "managedInstanceCount": 2,
    "jreCount": 7,
    "installationCount": 4,
    "applicationCount": 42,
}

MANAGED_INSTANCE_USAGE = {
    "ocid1.jmsfleet.oc1..mock-fleet-1": [
        {
            "managedInstanceId": "managed-instance-1",
            "managedInstanceType": "ORACLE_MANAGEMENT_AGENT",
            "hostname": "usage-host-1",
            "hostId": "host-1",
            "operatingSystem": {
                "family": "LINUX",
                "name": "Oracle Linux",
                "distribution": "Oracle Linux",
                "version": "9",
                "architecture": "X86_64",
                "managedInstanceCount": 1,
            },
            "agent": {"version": "1.1.0"},
            "approximateApplicationCount": 2,
            "approximateInstallationCount": 1,
            "approximateJreCount": 1,
            "drsFileStatus": "PRESENT",
            "applicationInvokedBy": "opc",
            "timeStart": "2026-02-12T08:00:00Z",
            "timeEnd": "2026-02-12T09:00:00Z",
            "timeFirstSeen": "2026-02-11T09:00:00Z",
            "timeLastSeen": "2026-02-12T09:45:00Z",
        }
    ]
}

FLEET_DIAGNOSES = {
    "ocid1.jmsfleet.oc1..mock-fleet-1": [
        {
            "resourceDiagnosis": "Inventory scan issue",
            "resourceId": "ocid1.jmsfleet.oc1..mock-fleet-1",
            "resourceState": "FAILED",
            "resourceType": "JMS_FLEET",
        },
        {
            "resourceDiagnosis": "Plugin heartbeat warning",
            "resourceId": "ocid1.jmsplugin.oc1..mock-plugin-1",
            "resourceState": "NEEDS_ATTENTION",
            "resourceType": "JMS_PLUGIN",
        },
    ]
}

FLEET_ERRORS = [
    {
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "fleetId": "ocid1.jmsfleet.oc1..mock-fleet-1",
        "fleetName": "mock-jms-fleet",
        "errors": [
            {
                "reason": "Agent connectivity failure",
                "details": "Critical agent reporting failure for plugin-host-1",
                "timeLastSeen": "2026-02-13T10:30:00Z",
            }
        ],
        "timeFirstSeen": "2026-02-13T09:00:00Z",
        "timeLastSeen": "2026-02-13T10:30:00Z",
    }
]

JMS_NOTICES = [
    {
        "key": 1001,
        "summary": "Planned JMS maintenance window",
        "timeReleased": "2026-02-14T11:00:00Z",
        "url": "https://example.oracle.test/jms/maintenance",
    },
    {
        "key": 1002,
        "summary": "JMS advisory for plugin telemetry delays",
        "timeReleased": "2026-02-12T06:00:00Z",
        "url": "https://example.oracle.test/jms/advisory",
    },
]

JRE_USAGE = {
    "ocid1.jmsfleet.oc1..mock-fleet-1": [
        {
            "id": "jre-usage-1",
            "fleetId": "ocid1.jmsfleet.oc1..mock-fleet-1",
            "version": "21.0.2",
            "vendor": "Oracle",
            "distribution": "JDK",
            "securityStatus": "UP_TO_DATE",
            "approximateInstallationCount": 4,
            "approximateManagedInstanceCount": 2,
            "approximateApplicationCount": 3,
        },
        {
            "id": "jre-usage-2",
            "fleetId": "ocid1.jmsfleet.oc1..mock-fleet-1",
            "version": "17.0.10",
            "vendor": "Oracle",
            "distribution": "JDK",
            "securityStatus": "UPDATE_REQUIRED",
            "approximateInstallationCount": 3,
            "approximateManagedInstanceCount": 1,
            "approximateApplicationCount": 1,
        },
    ]
}

JAVA_RELEASES = {
    "21.0.2": {
        "releaseVersion": "21.0.2",
        "releaseDate": "2026-01-16T00:00:00Z",
        "daysUnderSecurityBaseline": 0,
        "licenseType": "NFTC",
        "releaseType": "CPU",
        "releaseNotesUrl": "https://example.oracle.test/jms/releases/21.0.2",
        "securityStatus": "UP_TO_DATE",
    },
    "17.0.10": {
        "releaseVersion": "17.0.10",
        "releaseDate": "2025-10-15T00:00:00Z",
        "daysUnderSecurityBaseline": 30,
        "licenseType": "NFTC",
        "releaseType": "CPU",
        "releaseNotesUrl": "https://example.oracle.test/jms/releases/17.0.10",
        "securityStatus": "UPDATE_REQUIRED",
    },
}
