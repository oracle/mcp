"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# Using camelCase for keys to match OCI API responses

VCNS = [
    {
        "id": "ocid1.vcn.oc1..mock-vcn",
        "displayName": "mock-vcn",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "cidrBlock": "10.0.0.0/16",
        "lifecycleState": "AVAILABLE",
        "dnsLabel": "mockvcn",
        "vcnDomainName": "mockvcn.oraclevcn.com",
    }
]

SUBNETS = [
    {
        "id": "ocid1.subnet.oc1..mock-subnet",
        "displayName": "Default Subnet",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "vcnId": "ocid1.vcn.oc1..mock-vcn",
        "cidrBlock": "10.0.1.0/24",
        "lifecycleState": "AVAILABLE",
        "availabilityDomain": "aNMj:US-ASHBURN-AD-1",
        "virtualRouterIp": "10.0.1.1",
        "virtualRouterMac": "00:00:00:00:00:01",
    }
]

SECURITY_LISTS = [
    {
        "id": "ocid1.securitylist.oc1..mock-sl",
        "displayName": "Default Security List",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "vcnId": "ocid1.vcn.oc1..mock-vcn",
        "lifecycleState": "AVAILABLE",
    }
]

NETWORK_SECURITY_GROUPS = [
    {
        "id": "ocid1.networksecuritygroup.oc1..mock-nsg",
        "displayName": "mock-nsg",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "vcnId": "ocid1.vcn.oc1..mock-vcn",
        "lifecycleState": "AVAILABLE",
    }
]

VNICS = [
    {
        "id": "ocid1.vnic.oc1..mock-vnic",
        "displayName": "mock-vnic",
        "compartmentId": "ocid1.tenancy.oc1..mock",
        "subnetId": "ocid1.subnet.oc1..mock-subnet",
        "lifecycleState": "AVAILABLE",
    }
]
