"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import oci
from pydantic import BaseModel, Field


# Helper function
def _oci_to_dict(obj):
    """Best-effort conversion of OCI SDK model objects to plain dicts."""
    if obj is None:
        return None
    try:
        from oci.util import to_dict as oci_to_dict

        return oci_to_dict(obj)
    except Exception:
        pass
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return None


# Nested models


class ReservedIP(BaseModel):
    """Reserved IP details."""

    id: Optional[str] = Field(
        None, description="The OCID of the reserved public IP address."
    )


class IpAddress(BaseModel):
    """IP address details."""

    ip_address: Optional[str] = Field(None, description="The IP address.")
    is_public: Optional[bool] = Field(
        None, description="Whether the IP address is public."
    )
    ip_version: Optional[Literal["IPV4", "IPV6"]] = Field(
        None, description="IP version."
    )
    reserved_ip: Optional[ReservedIP] = Field(
        None, description="Reserved IP information."
    )


class Backend(BaseModel):
    """Backend server details."""

    name: Optional[str] = Field(None, description="The name of the backend.")
    ip_address: Optional[str] = Field(
        None, description="The IP address of the backend server."
    )
    target_id: Optional[str] = Field(
        None,
        description="The IP OCID/Instance OCID associated with the backend server.",
    )
    port: Optional[int] = Field(
        None, description="The communication port for the backend server."
    )
    weight: Optional[int] = Field(
        None,
        description="The network load balancing policy weight assigned to the server.",
    )
    is_drain: Optional[bool] = Field(
        None, description="Whether the network load balancer should drain this server."
    )
    is_backup: Optional[bool] = Field(
        None,
        description="Whether the network load balancer should treat this server as a backup unit.",
    )
    is_offline: Optional[bool] = Field(
        None,
        description="Whether the network load balancer should treat this server as offline.",
    )


class DnsHealthCheckerDetails(BaseModel):
    """DNS health checker details."""

    transport_protocol: Optional[Literal["UDP", "TCP"]] = Field(
        None, description="DNS transport protocol."
    )
    domain_name: Optional[str] = Field(
        None,
        description="The absolute fully-qualified domain name to perform periodic DNS queries.",
    )
    query_class: Optional[Literal["IN", "CH"]] = Field(
        None, description="The class of the DNS health check query."
    )
    query_type: Optional[Literal["A", "TXT", "AAAA"]] = Field(
        None, description="The type of the DNS health check query."
    )
    rcodes: Optional[List[str]] = Field(
        None, description="Acceptable RCODE values for DNS query response."
    )


class HealthChecker(BaseModel):
    """Health checker configuration."""

    protocol: Optional[Literal["HTTP", "HTTPS", "TCP", "UDP", "DNS"]] = Field(
        None, description="The protocol the health check must use."
    )
    port: Optional[int] = Field(
        None,
        description="The backend server port against which to run the health check.",
    )
    retries: Optional[int] = Field(
        None,
        description="The number of retries to attempt before a backend server is considered unhealthy.",
    )
    timeout_in_millis: Optional[int] = Field(
        None,
        description="The maximum time, in milliseconds, to wait for a reply to a health check.",
    )
    interval_in_millis: Optional[int] = Field(
        None, description="The interval between health checks, in milliseconds."
    )
    url_path: Optional[str] = Field(
        None, description="The path against which to run the health check."
    )
    response_body_regex: Optional[str] = Field(
        None,
        description="A regular expression for parsing the response body from the backend server.",
    )
    return_code: Optional[int] = Field(
        None, description="The status code a healthy backend server should return."
    )
    request_data: Optional[str] = Field(
        None,
        description="Base64 encoded pattern to be sent as UDP or TCP health check probe.",
    )
    response_data: Optional[str] = Field(
        None,
        description="Base64 encoded pattern to be validated as UDP or TCP health check probe response.",
    )
    dns: Optional[DnsHealthCheckerDetails] = Field(
        None, description="DNS health checker details."
    )


class Listener(BaseModel):
    """Listener configuration."""

    name: Optional[str] = Field(None, description="A friendly name for the listener.")
    default_backend_set_name: Optional[str] = Field(
        None, description="The name of the associated backend set."
    )
    port: Optional[int] = Field(
        None, description="The communication port for the listener."
    )
    protocol: Optional[Literal["ANY", "TCP", "UDP", "TCP_AND_UDP", "L3IP"]] = Field(
        None,
        description="The protocol on which the listener accepts connection requests.",
    )
    ip_version: Optional[Literal["IPV4", "IPV6"]] = Field(
        None, description="IP version associated with the listener."
    )
    is_ppv2_enabled: Optional[bool] = Field(
        None, description="Property to enable/disable PPv2 feature for this listener."
    )
    tcp_idle_timeout: Optional[int] = Field(
        None, description="The duration for TCP idle timeout in seconds."
    )
    udp_idle_timeout: Optional[int] = Field(
        None, description="The duration for UDP idle timeout in seconds."
    )
    l3_ip_idle_timeout: Optional[int] = Field(
        None, description="The duration for L3IP idle timeout in seconds."
    )


class BackendSet(BaseModel):
    """Backend set configuration."""

    name: Optional[str] = Field(
        None, description="A user-friendly name for the backend set."
    )
    policy: Optional[Literal["TWO_TUPLE", "THREE_TUPLE", "FIVE_TUPLE"]] = Field(
        None, description="The network load balancer policy for the backend set."
    )
    is_preserve_source: Optional[bool] = Field(
        None,
        description="If enabled, the network load balancer preserves the source IP of the packet.",
    )
    is_fail_open: Optional[bool] = Field(
        None,
        description="If enabled, the network load balancer will continue "
        "to distribute traffic if all backends are unhealthy.",
    )
    is_instant_failover_enabled: Optional[bool] = Field(
        None,
        description="If enabled, existing connections will be forwarded to an "
        "alternative healthy backend as soon as current backend becomes unhealthy.",
    )
    is_instant_failover_tcp_reset_enabled: Optional[bool] = Field(
        None,
        description="If enabled along with instant failover, the network load balancer "
        "will send TCP RST to the clients for the existing connections.",
    )
    are_operationally_active_backends_preferred: Optional[bool] = Field(
        None, description="If enabled, NLB supports active-standby backends."
    )
    ip_version: Optional[Literal["IPV4", "IPV6"]] = Field(
        None, description="IP version associated with the backend set."
    )
    backends: Optional[List[Backend]] = Field(None, description="An array of backends.")
    health_checker: Optional[HealthChecker] = Field(
        None, description="The health check policy configuration."
    )


class NetworkLoadBalancer(BaseModel):
    """Network load balancer."""

    id: Optional[str] = Field(
        None, description="The OCID of the network load balancer."
    )
    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment containing the network load balancer.",
    )
    display_name: Optional[str] = Field(None, description="A user-friendly name.")
    lifecycle_state: Optional[
        Literal["CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED"]
    ] = Field(None, description="The current state of the network load balancer.")
    lifecycle_details: Optional[str] = Field(
        None, description="A message describing the current state in more detail."
    )
    nlb_ip_version: Optional[Literal["IPV4", "IPV4_AND_IPV6", "IPV6"]] = Field(
        None, description="IP version associated with the NLB."
    )
    time_created: Optional[datetime] = Field(
        None, description="The date and time the network load balancer was created."
    )
    time_updated: Optional[datetime] = Field(
        None, description="The time the network load balancer was updated."
    )
    ip_addresses: Optional[List[IpAddress]] = Field(
        None, description="An array of IP addresses."
    )
    is_private: Optional[bool] = Field(
        None,
        description="Whether the network load balancer has a "
        "virtual cloud network-local (private) IP address.",
    )
    is_preserve_source_destination: Optional[bool] = Field(
        None,
        description="When enabled, the skipSourceDestinationCheck parameter is "
        "automatically enabled on the load balancer VNIC.",
    )
    is_symmetric_hash_enabled: Optional[bool] = Field(
        None,
        description="This can only be enabled when NLB is working in transparent "
        "mode with source destination header preservation enabled.",
    )
    subnet_id: Optional[str] = Field(
        None, description="The subnet in which the network load balancer is spawned."
    )
    network_security_group_ids: Optional[List[str]] = Field(
        None,
        description="An array of network security groups OCIDs associated with the network load balancer.",
    )
    listeners: Optional[Dict[str, Listener]] = Field(
        None, description="Listeners associated with the network load balancer."
    )
    backend_sets: Optional[Dict[str, BackendSet]] = Field(
        None, description="Backend sets associated with the network load balancer."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource."
    )
    security_attributes: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="ZPR tags for this resource."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags for this resource."
    )
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Key-value pair representing system tags' keys and values scoped to a namespace.",
    )


# Mapping functions


def map_reserved_ip(obj) -> ReservedIP | None:
    if not obj:
        return None
    return ReservedIP(id=getattr(obj, "id", None))


def map_ip_address(obj) -> IpAddress | None:
    if not obj:
        return None
    return IpAddress(
        ip_address=getattr(obj, "ip_address", None),
        is_public=getattr(obj, "is_public", None),
        ip_version=getattr(obj, "ip_version", None),
        reserved_ip=map_reserved_ip(getattr(obj, "reserved_ip", None)),
    )


def map_backend(obj) -> Backend | None:
    if not obj:
        return None
    return Backend(
        name=getattr(obj, "name", None),
        ip_address=getattr(obj, "ip_address", None),
        target_id=getattr(obj, "target_id", None),
        port=getattr(obj, "port", None),
        weight=getattr(obj, "weight", None),
        is_drain=getattr(obj, "is_drain", None),
        is_backup=getattr(obj, "is_backup", None),
        is_offline=getattr(obj, "is_offline", None),
    )


def map_dns_health_checker_details(obj) -> DnsHealthCheckerDetails | None:
    if not obj:
        return None
    return DnsHealthCheckerDetails(
        transport_protocol=getattr(obj, "transport_protocol", None),
        domain_name=getattr(obj, "domain_name", None),
        query_class=getattr(obj, "query_class", None),
        query_type=getattr(obj, "query_type", None),
        rcodes=getattr(obj, "rcodes", None),
    )


def map_health_checker(obj) -> HealthChecker | None:
    if not obj:
        return None
    return HealthChecker(
        protocol=getattr(obj, "protocol", None),
        port=getattr(obj, "port", None),
        retries=getattr(obj, "retries", None),
        timeout_in_millis=getattr(obj, "timeout_in_millis", None),
        interval_in_millis=getattr(obj, "interval_in_millis", None),
        url_path=getattr(obj, "url_path", None),
        response_body_regex=getattr(obj, "response_body_regex", None),
        return_code=getattr(obj, "return_code", None),
        request_data=getattr(obj, "request_data", None),
        response_data=getattr(obj, "response_data", None),
        dns=map_dns_health_checker_details(getattr(obj, "dns", None)),
    )


def map_listener(obj) -> Listener | None:
    if not obj:
        return None
    return Listener(
        name=getattr(obj, "name", None),
        default_backend_set_name=getattr(obj, "default_backend_set_name", None),
        port=getattr(obj, "port", None),
        protocol=getattr(obj, "protocol", None),
        ip_version=getattr(obj, "ip_version", None),
        is_ppv2_enabled=getattr(obj, "is_ppv2_enabled", None),
        tcp_idle_timeout=getattr(obj, "tcp_idle_timeout", None),
        udp_idle_timeout=getattr(obj, "udp_idle_timeout", None),
        l3_ip_idle_timeout=getattr(obj, "l3_ip_idle_timeout", None),
    )


def map_backend_set(obj) -> BackendSet | None:
    if not obj:
        return None
    backends = (
        [map_backend(b) for b in getattr(obj, "backends", [])]
        if getattr(obj, "backends", None)
        else None
    )
    return BackendSet(
        name=getattr(obj, "name", None),
        policy=getattr(obj, "policy", None),
        is_preserve_source=getattr(obj, "is_preserve_source", None),
        is_fail_open=getattr(obj, "is_fail_open", None),
        is_instant_failover_enabled=getattr(obj, "is_instant_failover_enabled", None),
        is_instant_failover_tcp_reset_enabled=getattr(
            obj, "is_instant_failover_tcp_reset_enabled", None
        ),
        are_operationally_active_backends_preferred=getattr(
            obj, "are_operationally_active_backends_preferred", None
        ),
        ip_version=getattr(obj, "ip_version", None),
        backends=backends,
        health_checker=map_health_checker(getattr(obj, "health_checker", None)),
    )


def map_network_load_balancer(
    obj: oci.network_load_balancer.models.NetworkLoadBalancer,
) -> NetworkLoadBalancer:
    """Map OCI NetworkLoadBalancer to custom Pydantic model."""
    ip_addresses = (
        [map_ip_address(ip) for ip in getattr(obj, "ip_addresses", [])]
        if getattr(obj, "ip_addresses", None)
        else None
    )
    listeners = (
        {k: map_listener(v) for k, v in getattr(obj, "listeners", {}).items()}
        if getattr(obj, "listeners", None)
        else None
    )
    backend_sets = (
        {k: map_backend_set(v) for k, v in getattr(obj, "backend_sets", {}).items()}
        if getattr(obj, "backend_sets", None)
        else None
    )
    return NetworkLoadBalancer(
        id=getattr(obj, "id", None),
        compartment_id=getattr(obj, "compartment_id", None),
        display_name=getattr(obj, "display_name", None),
        lifecycle_state=getattr(obj, "lifecycle_state", None),
        lifecycle_details=getattr(obj, "lifecycle_details", None),
        nlb_ip_version=getattr(obj, "nlb_ip_version", None),
        time_created=getattr(obj, "time_created", None),
        time_updated=getattr(obj, "time_updated", None),
        ip_addresses=ip_addresses,
        is_private=getattr(obj, "is_private", None),
        is_preserve_source_destination=getattr(
            obj, "is_preserve_source_destination", None
        ),
        is_symmetric_hash_enabled=getattr(obj, "is_symmetric_hash_enabled", None),
        subnet_id=getattr(obj, "subnet_id", None),
        network_security_group_ids=getattr(obj, "network_security_group_ids", None),
        listeners=listeners,
        backend_sets=backend_sets,
        freeform_tags=getattr(obj, "freeform_tags", None),
        security_attributes=getattr(obj, "security_attributes", None),
        defined_tags=getattr(obj, "defined_tags", None),
        system_tags=getattr(obj, "system_tags", None),
    )
