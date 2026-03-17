"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

import oci
from pydantic import BaseModel, Field

# Utilities


def _oci_to_dict(obj: Any) -> Optional[Dict[str, Any]]:
    """Best-effort conversion of OCI SDK model objects to plain dicts."""
    if obj is None:
        return None
    try:
        from oci.util import to_dict as oci_to_dict

        return oci_to_dict(obj)  # handles nested OCI models
    except Exception:
        pass
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return None


# Sub-objects of LoadBalancer (SDK: oci.load_balancer.models)


class ReservedIP(BaseModel):
    """Reserved IP details used by load balancer IP addresses."""

    id: Optional[str] = Field(
        None,
        description=(
            "OCID of the Reserved/Public IP created with VCN. When set, the load balancer "
            "is configured to listen on this IP."
        ),
    )


class IpAddress(BaseModel):
    """A load balancer IP address entry."""

    ip_address: Optional[str] = Field(
        None, description="An IP address. Example: 192.168.0.3"
    )
    is_public: Optional[bool] = Field(
        None,
        description=(
            "Whether the IP address is public (internet-routable) or private (VCN-local)."
        ),
    )
    reserved_ip: Optional[ReservedIP] = Field(
        None, description="Reserved IP metadata if this address is reserved."
    )


class ShapeDetails(BaseModel):
    """Flexible shape bandwidth configuration for the load balancer."""

    minimum_bandwidth_in_mbps: Optional[int] = Field(
        None,
        description=(
            "Guaranteed pre-provisioned bandwidth (ingress + egress), in Mbps."
        ),
    )
    maximum_bandwidth_in_mbps: Optional[int] = Field(
        None,
        description=(
            "Maximum bandwidth (ingress + egress) that can be achieved, in Mbps."
        ),
    )


class ConnectionConfiguration(BaseModel):
    """Connection settings between client and backend servers."""

    idle_timeout: Optional[int] = Field(
        None,
        description=(
            "Maximum idle time in seconds allowed between successive send/receive operations."
        ),
    )
    backend_tcp_proxy_protocol_version: Optional[int] = Field(
        None, description="Backend TCP Proxy Protocol version (1 or 2)."
    )
    backend_tcp_proxy_protocol_options: Optional[
        List[Literal["PP2_TYPE_AUTHORITY"]]
    ] = Field(None, description="PPv2 options that can be enabled on TCP listeners.")


class SSLConfiguration(BaseModel):
    """SSL/TLS negotiation settings for listeners and backend sets."""

    verify_depth: Optional[int] = Field(
        None, description="Maximum depth for peer certificate chain verification."
    )
    verify_peer_certificate: Optional[bool] = Field(
        None, description="Whether peer certificates should be verified."
    )
    has_session_resumption: Optional[bool] = Field(
        None,
        description=(
            "Whether to resume TLS sessions to improve performance (lower security)."
        ),
    )
    trusted_certificate_authority_ids: Optional[List[str]] = Field(
        None,
        description="OCI Certificates CA/Bundle OCIDs the load balancer should trust.",
    )
    certificate_ids: Optional[List[str]] = Field(
        None,
        description=(
            "OCI Certificates certificate OCIDs (currently a single ID supported)."
        ),
    )
    certificate_name: Optional[str] = Field(
        None,
        description="Friendly name of the certificate bundle bound to this config.",
    )
    server_order_preference: Optional[
        Literal["ENABLED", "DISABLED", "UNKNOWN_ENUM_VALUE"]
    ] = Field(  # noqa: E501
        None, description="Prefer server ciphers over client ciphers when enabled."
    )
    cipher_suite_name: Optional[str] = Field(
        None, description="The cipher suite name for HTTPS/SSL connections."
    )
    protocols: Optional[List[str]] = Field(
        None,
        description=(
            "Supported SSL protocols for HTTPS/SSL connections (e.g., TLSv1.2, TLSv1.3)."
        ),
    )


class Hostname(BaseModel):
    """A hostname resource associated with a load balancer for one or more listeners."""

    name: Optional[str] = Field(
        None, description="Unique, friendly hostname resource name."
    )
    hostname: Optional[str] = Field(
        None, description="Virtual hostname (e.g., app.example.com)."
    )


class SSLCipherSuite(BaseModel):
    """A named set of SSL ciphers used for HTTPS/SSL connections."""

    name: Optional[str] = Field(
        None, description="Friendly name of the SSL cipher suite."
    )
    ciphers: Optional[List[str]] = Field(
        None, description="List of SSL cipher names in the suite."
    )


class Certificate(BaseModel):
    """Certificate bundle configuration (public and CA certificates)."""

    certificate_name: Optional[str] = Field(
        None, description="Friendly name of the certificate bundle."
    )
    public_certificate: Optional[str] = Field(
        None, description="Public certificate in PEM format."
    )
    ca_certificate: Optional[str] = Field(
        None, description="CA or intermediate certificate in PEM format."
    )


class Backend(BaseModel):
    """Backend server configuration within a backend set."""

    name: Optional[str] = Field(
        None,
        description=(
            "Read-only composite key of backend (IP:port) within the backend set."
        ),
    )
    ip_address: Optional[str] = Field(None, description="Backend server IP address.")
    port: Optional[int] = Field(
        None, description="Communication port for the backend server."
    )
    weight: Optional[int] = Field(
        None,
        description=(
            "Load balancing weight; higher values receive more new connections."
        ),
    )
    max_connections: Optional[int] = Field(
        None,
        description=(
            "Maximum simultaneous connections allowed to this backend (unlimited if unset)."
        ),
    )
    drain: Optional[bool] = Field(
        None, description="Whether the backend is in drain mode (no new connections)."
    )
    backup: Optional[bool] = Field(
        None,
        description=(
            "Treat server as backup; receives traffic only if primary backends are unhealthy."
        ),
    )
    offline: Optional[bool] = Field(
        None, description="Whether the backend is offline (no incoming traffic)."
    )


class HealthChecker(BaseModel):
    """Health check policy configuration for backends."""

    protocol: Optional[str] = Field(
        None, description="Protocol to use for health checks (HTTP or TCP)."
    )
    url_path: Optional[str] = Field(
        None, description="Path for HTTP health checks (e.g., /healthcheck)."
    )
    port: Optional[int] = Field(
        None,
        description=(
            "Backend port to use for the health check; falls back to Backend.port if unset."
        ),
    )
    return_code: Optional[int] = Field(
        None, description="Expected status code from a healthy backend."
    )
    retries: Optional[int] = Field(
        None,
        description=(
            "Number of retries before marking backend unhealthy or when recovering to healthy."
        ),
    )
    timeout_in_millis: Optional[int] = Field(
        None, description="Maximum wait time for a health check reply (ms)."
    )
    interval_in_millis: Optional[int] = Field(
        None, description="Interval between health checks (ms)."
    )
    response_body_regex: Optional[str] = Field(
        None, description="Regex to match against response body for health checks."
    )
    is_force_plain_text: Optional[bool] = Field(
        None,
        description=(
            "Force plaintext health check even if backend set uses SSL; otherwise follow SSL config."
        ),
    )


class SessionPersistenceConfigurationDetails(BaseModel):
    """Application cookie based session persistence configuration."""

    cookie_name: Optional[str] = Field(
        None,
        description="Cookie name to detect a session initiated by the backend server.",
    )
    disable_fallback: Optional[bool] = Field(
        None,
        description=(
            "Prevent directing persistent-session clients to another backend if original is unavailable."
        ),
    )


class LBCookieSessionPersistenceConfigurationDetails(BaseModel):
    """LB cookie based session persistence configuration (stickiness)."""

    cookie_name: Optional[str] = Field(
        None, description="Name of cookie inserted by the load balancer."
    )
    disable_fallback: Optional[bool] = Field(
        None,
        description="Prevent fallback to a different backend if original is unavailable.",
    )
    domain: Optional[str] = Field(None, description="Cookie domain attribute value.")
    path: Optional[str] = Field(None, description="Cookie path attribute value.")
    max_age_in_seconds: Optional[int] = Field(
        None, description="Cookie Max-Age attribute (seconds)."
    )
    is_secure: Optional[bool] = Field(
        None, description="Whether to set the Secure attribute on the cookie."
    )
    is_http_only: Optional[bool] = Field(
        None, description="Whether to set the HttpOnly attribute on the cookie."
    )


class BackendSet(BaseModel):
    """Configuration of a load balancer backend set."""

    name: Optional[str] = Field(None, description="Friendly, unique backend set name.")
    policy: Optional[str] = Field(
        None, description="Load balancer policy (e.g., LEAST_CONNECTIONS)."
    )
    backends: Optional[List[Backend]] = Field(
        None, description="Backends in this backend set."
    )
    backend_max_connections: Optional[int] = Field(
        None,
        description=(
            "Max simultaneous connections to any backend unless overridden at backend level."
        ),
    )
    health_checker: Optional[HealthChecker] = Field(
        None, description="Health check policy for this backend set."
    )
    ssl_configuration: Optional[SSLConfiguration] = Field(
        None, description="SSL configuration for this backend set."
    )
    session_persistence_configuration: Optional[
        SessionPersistenceConfigurationDetails
    ] = Field(None, description="Application cookie stickiness configuration.")
    lb_cookie_session_persistence_configuration: Optional[
        LBCookieSessionPersistenceConfigurationDetails
    ] = Field(None, description="LB cookie stickiness configuration.")


class PathMatchType(BaseModel):
    """The type of matching to apply to incoming URIs for path routes."""

    match_type: Optional[
        Literal[
            "EXACT_MATCH",
            "FORCE_LONGEST_PREFIX_MATCH",
            "PREFIX_MATCH",
            "SUFFIX_MATCH",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="How to compare the path against the incoming URI.")


class PathRoute(BaseModel):
    """A path route rule mapping request path to a backend set."""

    path: Optional[str] = Field(
        None,
        description=(
            "Path string to match against the incoming URI path (case-insensitive, no wildcards or regex)."
        ),
    )
    path_match_type: Optional[PathMatchType] = Field(
        None, description="The type of path matching to apply."
    )
    backend_set_name: Optional[str] = Field(
        None,
        description=(
            "Target backend set name for requests that match the specified path."
        ),
    )


class PathRouteSet(BaseModel):
    """A named set of path route rules for a listener (deprecated in favor of routing policies)."""

    name: Optional[str] = Field(
        None, description="Unique name for this set of path route rules."
    )
    path_routes: Optional[List[PathRoute]] = Field(
        None, description="Path route rules."
    )


# Routing policy (listener-level advanced request routing)


class ForwardToBackendSet(BaseModel):
    """Routing action to forward requests to a backend set."""

    name: Literal["FORWARD_TO_BACKENDSET"] = Field(
        "FORWARD_TO_BACKENDSET", description="Routing action discriminator."
    )
    backend_set_name: Optional[str] = Field(
        None, description="Name of the backend set to forward traffic to."
    )


class Action(BaseModel):
    """Generic routing action. Unknown action payload is preserved in details."""

    name: Optional[str] = Field(
        None, description="Routing action discriminator (e.g., FORWARD_TO_BACKENDSET)."
    )
    details: Optional[Dict[str, Any]] = Field(
        None, description="Raw action fields when not mapped to a typed model."
    )


RoutingAction = Union[ForwardToBackendSet, Action]


class RoutingRule(BaseModel):
    """A routing rule evaluating condition expression and applying actions."""

    name: Optional[str] = Field(
        None, description="Unique name for the routing policy rule."
    )
    condition: Optional[str] = Field(
        None,
        description=(
            "Condition expression evaluated against the incoming HTTP request."
        ),
    )
    actions: Optional[List[RoutingAction]] = Field(
        None, description="Actions applied when the condition evaluates to true."
    )


class RoutingPolicy(BaseModel):
    """Named ordered list of routing rules applied to a listener."""

    name: Optional[str] = Field(
        None, description="Unique name for this list of routing rules."
    )
    condition_language_version: Optional[Literal["V1", "UNKNOWN_ENUM_VALUE"]] = Field(
        None, description="Version of the routing condition language."
    )
    rules: Optional[List[RoutingRule]] = Field(
        None, description="Ordered list of routing rules."
    )


# Listener and rule sets


class Listener(BaseModel):
    """Listener configuration."""

    name: Optional[str] = Field(None, description="Friendly, unique listener name.")
    default_backend_set_name: Optional[str] = Field(
        None, description="Name of the associated backend set."
    )
    port: Optional[int] = Field(
        None, description="Communication port for the listener."
    )
    protocol: Optional[str] = Field(
        None,
        description=(
            "Protocol on which the listener accepts connections (HTTP, HTTP2, TCP, GRPC)."
        ),
    )
    hostname_names: Optional[List[str]] = Field(
        None, description="Associated hostname resource names."
    )
    path_route_set_name: Optional[str] = Field(
        None,
        description="Deprecated. Name of the PathRouteSet applied to this listener.",
    )
    ssl_configuration: Optional[SSLConfiguration] = Field(
        None, description="SSL configuration of the listener."
    )
    connection_configuration: Optional[ConnectionConfiguration] = Field(
        None, description="Connection configuration between client and backends."
    )
    rule_set_names: Optional[List[str]] = Field(
        None, description="Names of RuleSets applied to this listener."
    )
    routing_policy_name: Optional[str] = Field(
        None, description="Name of the RoutingPolicy applied to this listener."
    )


class SimpleRule(BaseModel):
    """Generic listener Rule (for RuleSet). Preserves action and raw fields."""

    action: Optional[str] = Field(
        None, description="Rule action (e.g., ADD_HTTP_REQUEST_HEADER, REDIRECT, etc.)."
    )
    fields: Optional[Dict[str, Any]] = Field(
        None, description="Other rule fields serialized from the SDK model."
    )


class RuleSet(BaseModel):
    """A named set of listener rules (header manipulation, access control, etc.)."""

    name: Optional[str] = Field(None, description="Unique name for this set of rules.")
    items: Optional[List[SimpleRule]] = Field(
        None, description="Rules composed in this rule set."
    )


# Response (generic oci.response.Response mapping)


class Request(BaseModel):
    method: Optional[str] = Field(None, description="HTTP method")
    url: Optional[str] = Field(None, description="Request URL")
    query_params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    header_params: Optional[Dict[str, Any]] = Field(None, description="Request headers")
    body: Optional[Any] = Field(None, description="Request body")
    response_type: Optional[str] = Field(None, description="Expected response type")
    enforce_content_headers: Optional[bool] = Field(
        None, description="Whether content headers enforced for PUT/POST when absent"
    )


class Response(BaseModel):
    status: Optional[int] = Field(None, description="HTTP status code")
    headers: Optional[Dict[str, Any]] = Field(None, description="Response headers")
    data: Optional[Any] = Field(None, description="Response data (mapped)")
    request: Optional[Request] = Field(None, description="Original request")
    next_page: Optional[str] = Field(None, description="opc-next-page header value")
    request_id: Optional[str] = Field(None, description="opc-request-id header value")
    has_next_page: Optional[bool] = Field(
        None, description="Whether pagination continues"
    )


def _map_headers(headers) -> Optional[Dict[str, Any]]:
    if headers is None:
        return None
    try:
        return dict(headers)
    except Exception:
        try:
            return {k: v for k, v in headers.items()}
        except Exception:
            return _oci_to_dict(headers) or None


def _map_response_data(data: Any) -> Any:
    # handle sequence
    if isinstance(data, (list, tuple)):
        return [_map_response_data(x) for x in data]
    # passthrough simple
    if data is None or isinstance(data, (str, int, float, bool, dict)):
        return data
    # map known LB models
    try:
        if isinstance(data, oci.load_balancer.models.LoadBalancer):
            return map_load_balancer(data)  # type: ignore[name-defined]
        if isinstance(data, oci.load_balancer.models.BackendSet):
            return map_backend_set(data)  # type: ignore[name-defined]
        if isinstance(data, oci.load_balancer.models.Certificate):
            return map_certificate(data)  # type: ignore[name-defined]
        if isinstance(data, oci.load_balancer.models.SSLCipherSuite):
            return map_ssl_cipher_suite(data)  # type: ignore[name-defined]

        if isinstance(data, oci.load_balancer.models.Hostname):
            return map_hostname(data)  # type: ignore[name-defined]
        if isinstance(data, oci.load_balancer.models.RuleSet):
            return map_rule_set(data)  # type: ignore[name-defined]
        if isinstance(data, oci.load_balancer.models.RoutingPolicy):
            return map_routing_policy(data)  # type: ignore[name-defined]
        if isinstance(data, oci.load_balancer.models.LoadBalancerHealth):
            return map_load_balancer_health(data)  # type: ignore[name-defined]
        if isinstance(data, oci.load_balancer.models.BackendSetHealth):
            return map_backend_set_health(data)  # type: ignore[name-defined]
        if isinstance(data, oci.load_balancer.models.BackendHealth):
            return map_backend_health(data)  # type: ignore[name-defined]
        if isinstance(data, oci.load_balancer.models.WorkRequest):
            return map_work_request(data)  # type: ignore[name-defined]
    except Exception:
        pass
    # fallback to dict
    coerced = _oci_to_dict(data)
    return coerced if coerced is not None else data


def map_request(req) -> Optional[Request]:
    if not req:
        return None
    return Request(
        method=getattr(req, "method", None),
        url=getattr(req, "url", None),
        query_params=getattr(req, "query_params", None),
        header_params=getattr(req, "header_params", None),
        body=getattr(req, "body", None),
        response_type=getattr(req, "response_type", None),
        enforce_content_headers=getattr(req, "enforce_content_headers", None),
    )


def map_response(resp: oci.response.Response) -> Optional[Response]:
    if resp is None:
        return None
    headers = _map_headers(getattr(resp, "headers", None))
    next_page = getattr(resp, "next_page", None) or (headers or {}).get("opc-next-page")
    request_id = getattr(resp, "request_id", None) or (headers or {}).get(
        "opc-request-id"
    )
    return Response(
        status=getattr(resp, "status", None),
        headers=headers,
        data=_map_response_data(getattr(resp, "data", None)),
        request=map_request(getattr(resp, "request", None)),
        next_page=next_page,
        request_id=request_id,
        has_next_page=(next_page is not None),
    )


# Top-level LoadBalancer


class LoadBalancer(BaseModel):
    """
    Pydantic representation of oci.load_balancer.models.LoadBalancer and sub-objects.
    """

    id: Optional[str] = Field(None, description="OCID of the load balancer.")
    compartment_id: Optional[str] = Field(
        None, description="OCID of the compartment containing the load balancer."
    )
    display_name: Optional[str] = Field(
        None, description="User-friendly name; does not need to be unique."
    )
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "FAILED",
            "ACTIVE",
            "DELETING",
            "DELETED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="Current lifecycle state of the load balancer.")
    time_created: Optional[datetime] = Field(
        None, description="RFC3339 timestamp when the load balancer was created."
    )

    ip_addresses: Optional[List[IpAddress]] = Field(
        None, description="Array of IP addresses assigned to the load balancer."
    )

    shape_name: Optional[str] = Field(
        None,
        description=(
            "Shape template determining total pre-provisioned bandwidth (ingress + egress)."
        ),
    )
    shape_details: Optional[ShapeDetails] = Field(
        None, description="Flexible shape bandwidth configuration."
    )

    is_private: Optional[bool] = Field(
        None,
        description=(
            "Whether the load balancer is assigned a VCN-local (private) IP address."
        ),
    )
    is_delete_protection_enabled: Optional[bool] = Field(
        None, description="Whether delete protection is enabled."
    )
    is_request_id_enabled: Optional[bool] = Field(
        None,
        description=(
            "Whether to inject a unique request id header for HTTP listeners and echo on responses."
        ),
    )
    request_id_header: Optional[str] = Field(
        None,
        description=(
            "Header name used for the unique request id when Request Id feature is enabled."
        ),
    )

    subnet_ids: Optional[List[str]] = Field(None, description="Array of subnet OCIDs.")
    network_security_group_ids: Optional[List[str]] = Field(
        None, description="Array of NSG OCIDs associated with this load balancer."
    )

    listeners: Optional[Dict[str, Listener]] = Field(
        None, description="Listeners keyed by name."
    )
    hostnames: Optional[Dict[str, Hostname]] = Field(
        None, description="Hostnames keyed by name."
    )
    ssl_cipher_suites: Optional[Dict[str, SSLCipherSuite]] = Field(
        None, description="SSL cipher suites keyed by name."
    )
    certificates: Optional[Dict[str, Certificate]] = Field(
        None, description="Certificate bundles keyed by name."
    )
    backend_sets: Optional[Dict[str, BackendSet]] = Field(
        None, description="Backend sets keyed by name."
    )
    path_route_sets: Optional[Dict[str, PathRouteSet]] = Field(
        None, description="Path route sets keyed by name (deprecated)."
    )

    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags for this resource (scoped to namespaces)."
    )
    security_attributes: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description=(
            "Extended defined tags for ZPR for this resource (scoped to namespaces)."
        ),
    )
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description=(
            "System tags (scoped to namespaces), visible to users but only created by the system."
        ),
    )

    rule_sets: Optional[Dict[str, RuleSet]] = Field(
        None, description="Rule sets keyed by name."
    )
    routing_policies: Optional[Dict[str, RoutingPolicy]] = Field(
        None, description="Routing policies keyed by name."
    )

    ip_mode: Optional[Literal["IPV4", "IPV6", "UNKNOWN_ENUM_VALUE"]] = Field(
        None, description="Whether the load balancer has an IPv4 or IPv6 IP address."
    )


# Mapping functions from OCI SDK -> Pydantic models


def map_reserved_ip(obj) -> Optional[ReservedIP]:
    if not obj:
        return None
    return ReservedIP(id=getattr(obj, "id", None))


def map_ip_address(obj) -> Optional[IpAddress]:
    if not obj:
        return None
    return IpAddress(
        ip_address=getattr(obj, "ip_address", None),
        is_public=getattr(obj, "is_public", None),
        reserved_ip=map_reserved_ip(getattr(obj, "reserved_ip", None)),
    )


def map_shape_details(obj) -> Optional[ShapeDetails]:
    if not obj:
        return None
    return ShapeDetails(
        minimum_bandwidth_in_mbps=getattr(obj, "minimum_bandwidth_in_mbps", None),
        maximum_bandwidth_in_mbps=getattr(obj, "maximum_bandwidth_in_mbps", None),
    )


def map_connection_configuration(obj) -> Optional[ConnectionConfiguration]:
    if not obj:
        return None
    return ConnectionConfiguration(
        idle_timeout=getattr(obj, "idle_timeout", None),
        backend_tcp_proxy_protocol_version=getattr(
            obj, "backend_tcp_proxy_protocol_version", None
        ),
        backend_tcp_proxy_protocol_options=getattr(
            obj, "backend_tcp_proxy_protocol_options", None
        ),
    )


def map_ssl_configuration(obj) -> Optional[SSLConfiguration]:
    if not obj:
        return None
    return SSLConfiguration(
        verify_depth=getattr(obj, "verify_depth", None),
        verify_peer_certificate=getattr(obj, "verify_peer_certificate", None),
        has_session_resumption=getattr(obj, "has_session_resumption", None),
        trusted_certificate_authority_ids=getattr(
            obj, "trusted_certificate_authority_ids", None
        ),
        certificate_ids=getattr(obj, "certificate_ids", None),
        certificate_name=getattr(obj, "certificate_name", None),
        server_order_preference=getattr(obj, "server_order_preference", None),
        cipher_suite_name=getattr(obj, "cipher_suite_name", None),
        protocols=getattr(obj, "protocols", None),
    )


def map_hostname(obj) -> Optional[Hostname]:
    if not obj:
        return None
    return Hostname(
        name=getattr(obj, "name", None), hostname=getattr(obj, "hostname", None)
    )


def map_ssl_cipher_suite(obj) -> Optional[SSLCipherSuite]:
    if not obj:
        return None
    return SSLCipherSuite(
        name=getattr(obj, "name", None), ciphers=getattr(obj, "ciphers", None)
    )


def map_certificate(obj) -> Optional[Certificate]:
    if not obj:
        return None
    return Certificate(
        certificate_name=getattr(obj, "certificate_name", None),
        public_certificate=getattr(obj, "public_certificate", None),
        ca_certificate=getattr(obj, "ca_certificate", None),
    )


def map_backend(obj) -> Optional[Backend]:
    if not obj:
        return None
    return Backend(
        name=getattr(obj, "name", None),
        ip_address=getattr(obj, "ip_address", None),
        port=getattr(obj, "port", None),
        weight=getattr(obj, "weight", None),
        max_connections=getattr(obj, "max_connections", None),
        drain=getattr(obj, "drain", None),
        backup=getattr(obj, "backup", None),
        offline=getattr(obj, "offline", None),
    )


def map_health_checker(obj) -> Optional[HealthChecker]:
    if not obj:
        return None
    return HealthChecker(
        protocol=getattr(obj, "protocol", None),
        url_path=getattr(obj, "url_path", None),
        port=getattr(obj, "port", None),
        return_code=getattr(obj, "return_code", None),
        retries=getattr(obj, "retries", None),
        timeout_in_millis=getattr(obj, "timeout_in_millis", None),
        interval_in_millis=getattr(obj, "interval_in_millis", None),
        response_body_regex=getattr(obj, "response_body_regex", None),
        is_force_plain_text=getattr(obj, "is_force_plain_text", None),
    )


def map_session_persistence_configuration_details(
    obj,
) -> Optional[SessionPersistenceConfigurationDetails]:
    if not obj:
        return None
    return SessionPersistenceConfigurationDetails(
        cookie_name=getattr(obj, "cookie_name", None),
        disable_fallback=getattr(obj, "disable_fallback", None),
    )


def map_lb_cookie_session_persistence_configuration_details(
    obj,
) -> Optional[LBCookieSessionPersistenceConfigurationDetails]:
    if not obj:
        return None
    return LBCookieSessionPersistenceConfigurationDetails(
        cookie_name=getattr(obj, "cookie_name", None),
        disable_fallback=getattr(obj, "disable_fallback", None),
        domain=getattr(obj, "domain", None),
        path=getattr(obj, "path", None),
        max_age_in_seconds=getattr(obj, "max_age_in_seconds", None),
        is_secure=getattr(obj, "is_secure", None),
        is_http_only=getattr(obj, "is_http_only", None),
    )


def map_backend_set(obj) -> Optional[BackendSet]:
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
        backends=backends,
        backend_max_connections=getattr(obj, "backend_max_connections", None),
        health_checker=map_health_checker(getattr(obj, "health_checker", None)),
        ssl_configuration=map_ssl_configuration(
            getattr(obj, "ssl_configuration", None)
        ),
        session_persistence_configuration=map_session_persistence_configuration_details(
            getattr(obj, "session_persistence_configuration", None)
        ),
        lb_cookie_session_persistence_configuration=map_lb_cookie_session_persistence_configuration_details(
            getattr(obj, "lb_cookie_session_persistence_configuration", None)
        ),
    )


def map_path_match_type(obj) -> Optional[PathMatchType]:
    if not obj:
        return None
    return PathMatchType(match_type=getattr(obj, "match_type", None))


def map_path_route(obj) -> Optional[PathRoute]:
    if not obj:
        return None
    return PathRoute(
        path=getattr(obj, "path", None),
        path_match_type=map_path_match_type(getattr(obj, "path_match_type", None)),
        backend_set_name=getattr(obj, "backend_set_name", None),
    )


def map_path_route_set(obj) -> Optional[PathRouteSet]:
    if not obj:
        return None
    routes = (
        [map_path_route(x) for x in getattr(obj, "path_routes", [])]
        if getattr(obj, "path_routes", None)
        else None
    )
    return PathRouteSet(name=getattr(obj, "name", None), path_routes=routes)


def map_action(obj) -> RoutingAction:
    if not obj:
        return Action(name=None, details=None)
    name = getattr(obj, "name", None) or getattr(obj, "action", None)
    if name == "FORWARD_TO_BACKENDSET":
        return ForwardToBackendSet(
            backend_set_name=getattr(obj, "backend_set_name", None)
        )
    # Fallback: preserve raw fields
    data = _oci_to_dict(obj) or {}
    data.pop("name", None)
    data.pop("action", None)
    return Action(name=name, details=data or None)


def map_routing_rule(obj) -> Optional[RoutingRule]:
    if not obj:
        return None
    actions = (
        [map_action(a) for a in getattr(obj, "actions", [])]
        if getattr(obj, "actions", None)
        else None
    )
    return RoutingRule(
        name=getattr(obj, "name", None),
        condition=getattr(obj, "condition", None),
        actions=actions,
    )


def map_routing_policy(obj) -> Optional[RoutingPolicy]:
    if not obj:
        return None
    rules = (
        [map_routing_rule(r) for r in getattr(obj, "rules", [])]
        if getattr(obj, "rules", None)
        else None
    )
    return RoutingPolicy(
        name=getattr(obj, "name", None),
        condition_language_version=getattr(obj, "condition_language_version", None),
        rules=rules,
    )


def map_listener(obj) -> Optional[Listener]:
    if not obj:
        return None
    return Listener(
        name=getattr(obj, "name", None),
        default_backend_set_name=getattr(obj, "default_backend_set_name", None),
        port=getattr(obj, "port", None),
        protocol=getattr(obj, "protocol", None),
        hostname_names=getattr(obj, "hostname_names", None),
        path_route_set_name=getattr(obj, "path_route_set_name", None),
        ssl_configuration=map_ssl_configuration(
            getattr(obj, "ssl_configuration", None)
        ),
        connection_configuration=map_connection_configuration(
            getattr(obj, "connection_configuration", None)
        ),
        rule_set_names=getattr(obj, "rule_set_names", None),
        routing_policy_name=getattr(obj, "routing_policy_name", None),
    )


def map_simple_rule(obj) -> Optional[SimpleRule]:
    if not obj:
        return None
    action = getattr(obj, "action", None)
    raw = _oci_to_dict(obj) or {}
    if "action" in raw:
        raw.pop("action", None)
    return SimpleRule(action=action, fields=raw or None)


def map_rule_set(obj) -> Optional[RuleSet]:
    if not obj:
        return None
    items = (
        [map_simple_rule(x) for x in getattr(obj, "items", [])]
        if getattr(obj, "items", None)
        else None
    )
    return RuleSet(name=getattr(obj, "name", None), items=items)


def map_load_balancer(obj: oci.load_balancer.models.LoadBalancer) -> LoadBalancer:
    """Map OCI LoadBalancer SDK model (and nested types) to Pydantic model."""
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
    hostnames = (
        {k: map_hostname(v) for k, v in getattr(obj, "hostnames", {}).items()}
        if getattr(obj, "hostnames", None)
        else None
    )
    ssl_cipher_suites = (
        {
            k: map_ssl_cipher_suite(v)
            for k, v in getattr(obj, "ssl_cipher_suites", {}).items()
        }
        if getattr(obj, "ssl_cipher_suites", None)
        else None
    )
    certificates = (
        {k: map_certificate(v) for k, v in getattr(obj, "certificates", {}).items()}
        if getattr(obj, "certificates", None)
        else None
    )
    backend_sets = (
        {k: map_backend_set(v) for k, v in getattr(obj, "backend_sets", {}).items()}
        if getattr(obj, "backend_sets", None)
        else None
    )
    path_route_sets = (
        {
            k: map_path_route_set(v)
            for k, v in getattr(obj, "path_route_sets", {}).items()
        }
        if getattr(obj, "path_route_sets", None)
        else None
    )
    rule_sets = (
        {k: map_rule_set(v) for k, v in getattr(obj, "rule_sets", {}).items()}
        if getattr(obj, "rule_sets", None)
        else None
    )
    routing_policies = (
        {
            k: map_routing_policy(v)
            for k, v in getattr(obj, "routing_policies", {}).items()
        }
        if getattr(obj, "routing_policies", None)
        else None
    )

    return LoadBalancer(
        id=getattr(obj, "id", None),
        compartment_id=getattr(obj, "compartment_id", None),
        display_name=getattr(obj, "display_name", None),
        lifecycle_state=getattr(obj, "lifecycle_state", None),
        time_created=getattr(obj, "time_created", None),
        ip_addresses=ip_addresses,
        shape_name=getattr(obj, "shape_name", None),
        shape_details=map_shape_details(getattr(obj, "shape_details", None)),
        is_private=getattr(obj, "is_private", None),
        is_delete_protection_enabled=getattr(obj, "is_delete_protection_enabled", None),
        is_request_id_enabled=getattr(obj, "is_request_id_enabled", None),
        request_id_header=getattr(obj, "request_id_header", None),
        subnet_ids=getattr(obj, "subnet_ids", None),
        network_security_group_ids=getattr(obj, "network_security_group_ids", None),
        listeners=listeners,
        hostnames=hostnames,
        ssl_cipher_suites=ssl_cipher_suites,
        certificates=certificates,
        backend_sets=backend_sets,
        path_route_sets=path_route_sets,
        freeform_tags=getattr(obj, "freeform_tags", None),
        defined_tags=getattr(obj, "defined_tags", None),
        security_attributes=getattr(obj, "security_attributes", None),
        system_tags=getattr(obj, "system_tags", None),
        rule_sets=rule_sets,
        routing_policies=routing_policies,
        ip_mode=getattr(obj, "ip_mode", None),
    )


# Health and Work Request models + mapping


class HealthCheckResult(BaseModel):
    subnet_id: Optional[str] = None
    source_ip_address: Optional[str] = None
    timestamp: Optional[datetime] = None
    health_check_status: Optional[
        Literal[
            "OK",
            "INVALID_STATUS_CODE",
            "TIMED_OUT",
            "REGEX_MISMATCH",
            "CONNECT_FAILED",
            "IO_ERROR",
            "OFFLINE",
            "UNKNOWN",
        ]
    ] = None


class BackendHealth(BaseModel):
    status: Optional[Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]] = None
    health_check_results: Optional[List[HealthCheckResult]] = None


class BackendSetHealth(BaseModel):
    status: Optional[Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]] = None
    warning_state_backend_names: Optional[List[str]] = None
    critical_state_backend_names: Optional[List[str]] = None
    unknown_state_backend_names: Optional[List[str]] = None
    total_backend_count: Optional[int] = None


class LoadBalancerHealth(BaseModel):
    status: Optional[Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]] = None
    warning_state_backend_set_names: Optional[List[str]] = None
    critical_state_backend_set_names: Optional[List[str]] = None
    unknown_state_backend_set_names: Optional[List[str]] = None
    total_backend_set_count: Optional[int] = None


class LoadBalancerHealthSummary(BaseModel):
    load_balancer_id: Optional[str] = None
    status: Optional[Literal["OK", "WARNING", "CRITICAL", "UNKNOWN"]] = None


class WorkRequestError(BaseModel):
    error_code: Optional[Literal["BAD_INPUT", "INTERNAL_ERROR"]] = None
    message: Optional[str] = None


class WorkRequest(BaseModel):
    id: Optional[str] = None
    load_balancer_id: Optional[str] = None
    type: Optional[str] = None
    compartment_id: Optional[str] = None
    lifecycle_state: Optional[
        Literal["ACCEPTED", "IN_PROGRESS", "FAILED", "SUCCEEDED"]
    ] = None
    message: Optional[str] = None
    time_accepted: Optional[datetime] = None
    time_finished: Optional[datetime] = None
    error_details: Optional[List[WorkRequestError]] = None


def map_health_check_result(obj) -> Optional[HealthCheckResult]:
    if not obj:
        return None
    return HealthCheckResult(
        subnet_id=getattr(obj, "subnet_id", None),
        source_ip_address=getattr(obj, "source_ip_address", None),
        timestamp=getattr(obj, "timestamp", None),
        health_check_status=getattr(obj, "health_check_status", None),
    )


def map_backend_health(obj) -> Optional[BackendHealth]:
    if not obj:
        return None
    results = (
        [map_health_check_result(r) for r in getattr(obj, "health_check_results", [])]
        if getattr(obj, "health_check_results", None)
        else None
    )
    return BackendHealth(
        status=getattr(obj, "status", None), health_check_results=results
    )


def map_backend_set_health(obj) -> Optional[BackendSetHealth]:
    if not obj:
        return None
    return BackendSetHealth(
        status=getattr(obj, "status", None),
        warning_state_backend_names=getattr(obj, "warning_state_backend_names", None),
        critical_state_backend_names=getattr(obj, "critical_state_backend_names", None),
        unknown_state_backend_names=getattr(obj, "unknown_state_backend_names", None),
        total_backend_count=getattr(obj, "total_backend_count", None),
    )


def map_load_balancer_health(obj) -> Optional[LoadBalancerHealth]:
    if not obj:
        return None
    return LoadBalancerHealth(
        status=getattr(obj, "status", None),
        warning_state_backend_set_names=getattr(
            obj, "warning_state_backend_set_names", None
        ),
        critical_state_backend_set_names=getattr(
            obj, "critical_state_backend_set_names", None
        ),
        unknown_state_backend_set_names=getattr(
            obj, "unknown_state_backend_set_names", None
        ),
        total_backend_set_count=getattr(obj, "total_backend_set_count", None),
    )


def map_load_balancer_health_summary(obj) -> Optional[LoadBalancerHealthSummary]:
    if not obj:
        return None
    return LoadBalancerHealthSummary(
        load_balancer_id=getattr(obj, "load_balancer_id", None),
        status=getattr(obj, "status", None),
    )


def map_work_request_error(obj) -> Optional[WorkRequestError]:
    if not obj:
        return None
    return WorkRequestError(
        error_code=getattr(obj, "error_code", None),
        message=getattr(obj, "message", None),
    )


def map_work_request(obj) -> Optional[WorkRequest]:
    if not obj:
        return None
    errors = (
        [map_work_request_error(e) for e in getattr(obj, "error_details", [])]
        if getattr(obj, "error_details", None)
        else None
    )
    return WorkRequest(
        id=getattr(obj, "id", None),
        load_balancer_id=getattr(obj, "load_balancer_id", None),
        type=getattr(obj, "type", None),
        compartment_id=getattr(obj, "compartment_id", None),
        lifecycle_state=getattr(obj, "lifecycle_state", None),
        message=getattr(obj, "message", None),
        time_accepted=getattr(obj, "time_accepted", None),
        time_finished=getattr(obj, "time_finished", None),
        error_details=errors,
    )
