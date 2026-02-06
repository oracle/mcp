"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# CamelCase mock data for Network Load Balancer service

NETWORK_LOAD_BALANCERS = [
    {
        "id": "ocid1.nlb.oc1..mock-nlb-1",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "displayName": "mock-nlb-1",
        "lifecycleState": "ACTIVE",
        "timeCreated": "2026-01-13T10:00:00Z",
        "nlbIpVersion": "IPV4",
        "ipAddresses": [
            {
                "ipAddress": "203.0.113.10",
                "isPublic": True,
                "ipVersion": "IPV4",
                "reservedIp": {"id": "ocid1.publicip.oc1..mockip1"},
            }
        ],
        "isPrivate": False,
        "isPreserveSourceDestination": False,
        "isSymmetricHashEnabled": False,
        "subnetId": "ocid1.subnet.oc1..mock-subnet-1",
        "networkSecurityGroupIds": ["ocid1.nsg.oc1..mocknsg1"],
        "listeners": {
            "listener-1": {
                "name": "listener-1",
                "defaultBackendSetName": "backendset-1",
                "port": 80,
                "protocol": "TCP",
                "ipVersion": "IPV4",
                "isPpv2Enabled": False,
                "tcpIdleTimeout": 60,
                "udpIdleTimeout": 30,
                "l3IpIdleTimeout": 60,
            }
        },
        "backendSets": {
            "backendset-1": {
                "name": "backendset-1",
                "policy": "FIVE_TUPLE",
                "isPreserveSource": False,
                "isFailOpen": False,
                "isInstantFailoverEnabled": False,
                "isInstantFailoverTcpResetEnabled": False,
                "areOperationallyActiveBackendsPreferred": False,
                "ipVersion": "IPV4",
                "healthChecker": {
                    "protocol": "TCP",
                    "port": 80,
                    "retries": 3,
                    "timeoutInMillis": 3000,
                    "intervalInMillis": 10000,
                },
                "backends": [
                    {
                        "name": "backend-1",
                        "ipAddress": "10.0.0.10",
                        "port": 80,
                        "weight": 1,
                        "isDrain": False,
                        "isBackup": False,
                        "isOffline": False,
                    },
                    {
                        "name": "backend-2",
                        "ipAddress": "10.0.0.11",
                        "port": 80,
                        "weight": 1,
                        "isDrain": False,
                        "isBackup": False,
                        "isOffline": False,
                    },
                ],
            }
        },
    }
]
