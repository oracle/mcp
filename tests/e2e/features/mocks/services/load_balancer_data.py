"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# Canonical IDs
TENANCY_ID = "ocid1.tenancy.oc1..mock"
LB_ID = "ocid1.loadbalancer.oc1..mock-lb-1"
WORK_REQUEST_ID = "ocid1.loadbalancerworkrequest.oc1..wr1"

# Core load balancer object as returned by GetLoadBalancer
LOAD_BALANCER_OBJ = {
    "id": LB_ID,
    "compartmentId": TENANCY_ID,
    "displayName": "mock-lb",
    "lifecycleState": "ACTIVE",
    "timeCreated": "2026-01-01T00:00:00Z",
    "ipAddresses": [
        {"ipAddress": "192.168.0.3", "isPublic": False},
    ],
    "shapeName": "Flexible",
    "isPrivate": False,
    "isDeleteProtectionEnabled": False,
    "isRequestIdEnabled": False,
    "requestIdHeader": "X-Request-Id",
    "subnetIds": ["ocid1.subnet.oc1..mock-subnet-1"],
    "networkSecurityGroupIds": [],
    # Maps on the LB document
    "listeners": {
        "listener1": {
            "name": "listener1",
            "defaultBackendSetName": "backendset1",
            "port": 80,
            "protocol": "HTTP",
            "hostnameNames": [],
            "pathRouteSetName": None,
            "sslConfiguration": None,
            "connectionConfiguration": {"idleTimeout": 1200},
            "ruleSetNames": [],
            "routingPolicyName": None,
        }
    },
    "hostnames": {
        "host1": {
            "name": "host1",
            "hostname": "app.example.com",
        }
    },
    "sslCipherSuites": {
        "suite1": {
            "name": "suite1",
            "ciphers": ["TLS_AES_128_GCM_SHA256"],
        }
    },
    "certificates": {
        "cert1": {
            "certificateName": "cert1",
            "publicCertificate": "---PUBLIC---",
            "caCertificate": "---CA---",
        }
    },
    "backendSets": {
        "backendset1": {
            "name": "backendset1",
            "policy": "ROUND_ROBIN",
            "backends": [
                {
                    "name": "10.0.0.3:8080",
                    "ipAddress": "10.0.0.3",
                    "port": 8080,
                    "weight": 3,
                    "maxConnections": 300,
                    "backup": False,
                    "drain": False,
                    "offline": False,
                },
                {
                    "name": "10.0.0.4:8080",
                    "ipAddress": "10.0.0.4",
                    "port": 8080,
                    "weight": 1,
                    "maxConnections": 256,
                    "backup": False,
                    "drain": False,
                    "offline": False,
                },
            ],
            "backendMaxConnections": 300,
            "healthChecker": {
                "protocol": "HTTP",
                "isForcePlainText": False,
                "urlPath": "/health",
                "port": 8080,
                "returnCode": 200,
                "retries": 3,
                "timeoutInMillis": 3000,
                "intervalInMillis": 10000,
                "responseBodyRegex": "^OK$",
            },
            "sslConfiguration": None,
            "sessionPersistenceConfiguration": None,
            "lbCookieSessionPersistenceConfiguration": None,
        }
    },
    "pathRouteSets": {},
    "ruleSets": {
        "ruleset1": {
            "name": "ruleset1",
            "items": [
                {
                    "action": "ADD_HTTP_REQUEST_HEADER",
                    "header": "x-test",
                    "value": "demo",
                }
            ],
        }
    },
    "routingPolicies": {
        "policy1": {
            "name": "policy1",
            "conditionLanguageVersion": "V1",
            "rules": [
                {
                    "name": "r1",
                    "condition": "true",
                    "actions": [
                        {
                            "name": "FORWARD_TO_BACKENDSET",
                            "backendSetName": "backendset1",
                        }
                    ],
                }
            ],
        }
    },
}

# Collections for list endpoints
LOAD_BALANCERS = [
    {
        "id": LB_ID,
        "compartmentId": TENANCY_ID,
        "displayName": "mock-lb",
        "lifecycleState": "ACTIVE",
        "timeCreated": "2026-01-01T00:00:00Z",
        "shapeName": "Flexible",
        "isPrivate": False,
    }
]

BACKEND_SETS = [LOAD_BALANCER_OBJ["backendSets"]["backendset1"]]
BACKENDS = LOAD_BALANCER_OBJ["backendSets"]["backendset1"]["backends"]
CERTIFICATES = [
    {
        "certificateName": "cert1",
        "publicCertificate": "---PUBLIC---",
        "caCertificate": "---CA---",
    }
]
SSL_CIPHER_SUITES = [
    {
        "name": "suite1",
        "ciphers": ["TLS_AES_128_GCM_SHA256"],
    }
]
HOSTNAMES = [
    {
        "name": "host1",
        "hostname": "app.example.com",
    }
]
RULE_SETS = [LOAD_BALANCER_OBJ["ruleSets"]["ruleset1"]]
ROUTING_POLICIES = [
    {
        "name": "policy1",
        "conditionLanguageVersion": "V1",
        "rules": LOAD_BALANCER_OBJ["routingPolicies"]["policy1"]["rules"],
    }
]

# Health
LOAD_BALANCER_HEALTH = {
    "status": "OK",
    "warningStateBackendSetNames": [],
    "criticalStateBackendSetNames": [],
    "unknownStateBackendSetNames": [],
    "totalBackendSetCount": 1,
}

BACKEND_SET_HEALTH = {
    "status": "OK",
    "warningStateBackendNames": [],
    "criticalStateBackendNames": [],
    "unknownStateBackendNames": [],
    "totalBackendCount": 2,
}

BACKEND_HEALTH = {
    "status": "OK",
    "healthCheckResults": [
        {
            "subnetId": "ocid1.subnet.oc1..mock-subnet-1",
            "sourceIpAddress": "192.168.0.7",
            "timestamp": "2026-01-01T00:00:00Z",
            "healthCheckStatus": "OK",
        }
    ],
}

HEALTH_SUMMARIES = [
    {"loadBalancerId": LB_ID, "status": "OK"},
]

# Work Requests
WORK_REQUESTS = [
    {
        "id": WORK_REQUEST_ID,
        "loadBalancerId": LB_ID,
        "type": "CreateListener",
        "compartmentId": TENANCY_ID,
        "lifecycleState": "SUCCEEDED",
        "message": "OK",
        "timeAccepted": "2026-01-01T00:00:00Z",
        "timeFinished": "2026-01-01T00:00:10Z",
        "errorDetails": [],
    }
]
