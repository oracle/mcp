"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import os
from logging import Logger
from typing import Literal, Optional

import oci
from fastmcp import FastMCP
from oracle.oci_load_balancer_mcp_server.models import (
    Backend,
    BackendHealth,
    BackendSet,
    BackendSetHealth,
    Certificate,
    Hostname,
    Listener,
    LoadBalancer,
    LoadBalancerHealth,
    LoadBalancerHealthSummary,
    Response,
    RoutingPolicy,
    RuleSet,
    SSLCipherSuite,
    WorkRequest,
    map_backend,
    map_backend_health,
    map_backend_set,
    map_backend_set_health,
    map_certificate,
    map_hostname,
    map_listener,
    map_load_balancer,
    map_load_balancer_health,
    map_load_balancer_health_summary,
    map_response,
    map_routing_policy,
    map_rule_set,
    map_ssl_cipher_suite,
    map_work_request,
)
from pydantic import Field

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(
    name=__project__,
    instructions=(
        "OCI Load Balancer MCP tools. Use these tools directly and concisely. "
        "When a prompt mentions a load balancer by name, first call list_load_balancers with "
        "compartment_id=<active compartment> and display_name=<specified name> to obtain its OCID. "
        "Use that id for subsequent calls. Prefer minimal tool calls and return short confirmations using "
        "words like created/updated/deleted/retrieved and the nouns listener, backend set, backend, "
        "certificate, cipher suite, hostname, rule set, routing policy, health, work request."
    ),
)


def get_load_balancer_client():
    logger.info("entering get_load_balancer_client")
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    # Use the same token-based signer approach used in other servers for consistency
    token_file = (
        os.path.expanduser(config["security_token_file"])
        if "security_token_file" in config
        else None
    )
    token = None
    if token_file:
        with open(token_file, "r") as f:
            token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key) if token else None
    return oci.load_balancer.LoadBalancerClient(config, signer=signer)


@mcp.tool(
    name="list_load_balancers",
    description=(
        "Lists OCI load balancers in a compartment. Requires a compartment OCID. "
        "If you have a display name, you may first use this tool to list load balancers and "
        "search for the desired OCID based on display_name."
        " You MUST pass compartment_id=... (do NOT use name or 'root')."
        "Example: call list_load_balancers with compartment_id=ocid1.tenancy.oc1..abcd"
    ),
)
def list_load_balancers(
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of load balancers to return. If None, there is no limit.",
        ge=1,
    ),
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "FAILED",
            "ACTIVE",
            "DELETING",
            "DELETED",
        ]
    ] = Field(
        None,
        description="The lifecycle state of the load balancer to filter on",
    ),
    display_name: Optional[str] = Field(
        None, description="Exact display name to filter on"
    ),
    sort_by: Optional[Literal["TIMECREATED", "DISPLAYNAME"]] = Field(
        None, description="Field to sort by"
    ),
    sort_order: Optional[Literal["ASC", "DESC"]] = Field(
        None, description="Sort order to use"
    ),
) -> list[LoadBalancer]:
    lbs: list[LoadBalancer] = []

    try:
        client = get_load_balancer_client()

        next_page: Optional[str] = None
        first_page = True
        while first_page or (next_page and (limit is None or len(lbs) < limit)):
            first_page = False
            # Respect remaining client-side limit to avoid overfetching
            page_limit = None if limit is None else max(1, limit - len(lbs))
            # Build kwargs only for values that are not None to satisfy OCI SDK validation
            kwargs = {"compartment_id": compartment_id}
            if page_limit is not None:
                kwargs["limit"] = page_limit
            if next_page is not None:
                kwargs["page"] = next_page
            if display_name is not None:
                kwargs["display_name"] = display_name
            if lifecycle_state is not None:
                kwargs["lifecycle_state"] = lifecycle_state
            if sort_by is not None:
                kwargs["sort_by"] = sort_by
            if sort_order is not None:
                kwargs["sort_order"] = sort_order

            response = client.list_load_balancers(**kwargs)
            items = getattr(response.data, "items", response.data) or []
            remaining = None if limit is None else max(0, limit - len(lbs))
            to_process = items if remaining is None else items[:remaining]
            for d in to_process:
                lbs.append(map_load_balancer(d))
            next_page = getattr(response, "next_page", None)

        logger.info(f"Found {len(lbs)} Load Balancers")
        return lbs

    except Exception as e:
        logger.error(f"Error in list_load_balancers tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_load_balancer",
    description=(
        "Get details for a specific load balancer. Requires load_balancer_id (OCID). "
        "If you only have a display name, first perform a list_load_balancers call and search "
        "for the matching display_name to figure out the OCID."
        " Example: call get_load_balancer with load_balancer_id=ocid1.loadbalancer.oc1..abcd"
    ),
)
def get_load_balancer(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer")
) -> LoadBalancer:
    try:
        client = get_load_balancer_client()

        response: oci.response.Response = client.get_load_balancer(load_balancer_id)
        data: oci.load_balancer.models.LoadBalancer = response.data
        logger.info("Found Load Balancer")
        return map_load_balancer(data)

    except Exception as e:
        logger.error(f"Error in get_load_balancer tool: {str(e)}")
        raise e


@mcp.tool(
    name="create_load_balancer",
    description=(
        "Create a new load balancer. Requires compartment_id (OCID), display_name, shape_name, "
        "and subnet_ids (list of OCIDs). Do NOT use compartment name. "
        "Example: call create_load_balancer with compartment_id=ocid1.tenancy.oc1..abcd, "
        "display_name=lb-name, shape_name=Flexible, subnet_ids=[ocid1.subnet.oc1..subnet-abcd]"
        " When a compartment_id is not provided, use the currently active compartment."
    ),
)
def create_load_balancer(
    compartment_id: str = Field(
        ..., description="The OCID of the compartment to create the load balancer in."
    ),
    display_name: str = Field(
        ...,
        description="A user-friendly display name for the load balancer.",
        min_length=1,
        max_length=1024,
    ),
    shape_name: str = Field(
        ...,
        description="The shape name for the load balancer (e.g., Flexible, 100Mbps).",
    ),
    subnet_ids: list[str] = Field(
        ..., description="An array of subnet OCIDs for the load balancer."
    ),
    is_private: Optional[bool] = Field(
        None, description="Whether the load balancer should be private"
    ),
    ip_mode: Optional[Literal["IPV4", "IPV6"]] = Field(
        None, description="Whether the load balancer should have IPv4 or IPv6 address"
    ),
    is_delete_protection_enabled: Optional[bool] = Field(
        None, description="Enable delete protection for this load balancer"
    ),
    is_request_id_enabled: Optional[bool] = Field(
        None, description="Enable Request Id header feature for HTTP listeners"
    ),
    request_id_header: Optional[str] = Field(
        None, description="Custom header name for Request Id feature when enabled"
    ),
    network_security_group_ids: Optional[list[str]] = Field(
        None, description="Array of NSG OCIDs to associate with the load balancer"
    ),
    minimum_bandwidth_in_mbps: Optional[int] = Field(
        None, description="Minimum bandwidth in Mbps (Flexible shape only)"
    ),
    maximum_bandwidth_in_mbps: Optional[int] = Field(
        None, description="Maximum bandwidth in Mbps (Flexible shape only)"
    ),
) -> Response:
    try:
        client = get_load_balancer_client()

        shape_details = None
        if (
            minimum_bandwidth_in_mbps is not None
            and maximum_bandwidth_in_mbps is not None
        ):
            shape_details = oci.load_balancer.models.ShapeDetails(
                minimum_bandwidth_in_mbps=minimum_bandwidth_in_mbps,
                maximum_bandwidth_in_mbps=maximum_bandwidth_in_mbps,
            )

        details = oci.load_balancer.models.CreateLoadBalancerDetails(
            compartment_id=compartment_id,
            display_name=display_name,
            shape_name=shape_name,
            subnet_ids=subnet_ids,
            is_private=is_private,
            ip_mode=ip_mode,
            is_delete_protection_enabled=is_delete_protection_enabled,
            is_request_id_enabled=is_request_id_enabled,
            request_id_header=request_id_header,
            network_security_group_ids=network_security_group_ids,
            shape_details=shape_details,
        )

        response: oci.response.Response = client.create_load_balancer(details)
        logger.info("Create Load Balancer request accepted")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in create_load_balancer tool: {str(e)}")
        raise e


@mcp.tool(
    name="update_load_balancer", description="Update a load balancer configuration"
)
def update_load_balancer(
    load_balancer_id: str = Field(
        ..., description="The OCID of the load balancer to update"
    ),
    display_name: Optional[str] = Field(
        None, description="New display name for the load balancer"
    ),
    is_delete_protection_enabled: Optional[bool] = Field(
        None, description="Whether delete protection should be enabled"
    ),
    is_request_id_enabled: Optional[bool] = Field(
        None, description="Enable Request Id header feature for HTTP listeners"
    ),
    request_id_header: Optional[str] = Field(
        None, description="Custom header name for Request Id feature when enabled"
    ),
    freeform_tags: Optional[dict[str, str]] = Field(
        None, description="Free-form tags to set on the resource"
    ),
    defined_tags: Optional[dict[str, dict[str, object]]] = Field(
        None, description="Defined tags to set on the resource"
    ),
    defined_tags_extended: Optional[dict[str, dict[str, dict[str, object]]]] = Field(
        None, description="Extended defined tags to set on the resource"
    ),
) -> Response:
    try:
        client = get_load_balancer_client()

        update_details = oci.load_balancer.models.UpdateLoadBalancerDetails(
            display_name=display_name,
            is_delete_protection_enabled=is_delete_protection_enabled,
            is_request_id_enabled=is_request_id_enabled,
            request_id_header=request_id_header,
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
            defined_tags_extended=defined_tags_extended,
        )

        response: oci.response.Response = client.update_load_balancer(
            update_details, load_balancer_id
        )
        logger.info("Update Load Balancer request accepted")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in update_load_balancer tool: {str(e)}")
        raise e


@mcp.tool(
    name="update_load_balancer_shape",
    description="Update the shape (bandwidth) of a load balancer",
)
def update_load_balancer_shape(
    load_balancer_id: str = Field(
        ..., description="The OCID of the load balancer to update"
    ),
    shape_name: Optional[str] = Field(
        None,
        description="The shape name for the load balancer (e.g., Flexible, 100Mbps)",
    ),
    minimum_bandwidth_in_mbps: Optional[int] = Field(
        None,
        description="Minimum bandwidth in Mbps (Flexible shape only)",
    ),
    maximum_bandwidth_in_mbps: Optional[int] = Field(
        None,
        description="Maximum bandwidth in Mbps (Flexible shape only)",
    ),
) -> Response:
    try:
        client = get_load_balancer_client()

        shape_details = None
        if (
            minimum_bandwidth_in_mbps is not None
            and maximum_bandwidth_in_mbps is not None
        ):
            shape_details = oci.load_balancer.models.ShapeDetails(
                minimum_bandwidth_in_mbps=minimum_bandwidth_in_mbps,
                maximum_bandwidth_in_mbps=maximum_bandwidth_in_mbps,
            )

        update_details = oci.load_balancer.models.UpdateLoadBalancerShapeDetails(
            shape_name=shape_name,
            shape_details=shape_details,
        )

        response: oci.response.Response = client.update_load_balancer_shape(
            load_balancer_id, update_details
        )
        logger.info("Update Load Balancer shape request accepted")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in update_load_balancer_shape tool: {str(e)}")
        raise e


@mcp.tool(
    name="delete_load_balancer",
    description=(
        "Delete the specified load balancer. Requires load_balancer_id (OCID). "
        "If you have only a display name, use list_load_balancers to obtain the OCID first."
        " Example: call delete_load_balancer with load_balancer_id=ocid1.loadbalancer.oc1..abcd"
    ),
)
def delete_load_balancer(
    load_balancer_id: str = Field(
        ..., description="The OCID of the load balancer to delete"
    )
) -> Response:
    try:
        client = get_load_balancer_client()

        response: oci.response.Response = client.delete_load_balancer(load_balancer_id)
        logger.info("Delete Load Balancer request accepted")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in delete_load_balancer tool: {str(e)}")
        raise e


@mcp.tool(
    name="update_load_balancer_network_security_groups",
    description="Update the network security groups associated with a load balancer",
)
def update_load_balancer_network_security_groups(
    load_balancer_id: str = Field(
        ..., description="The OCID of the load balancer to update"
    ),
    network_security_group_ids: Optional[list[str]] = Field(
        None, description="Array of NSG OCIDs to associate with the load balancer"
    ),
) -> Response:
    try:
        client = get_load_balancer_client()

        update_details = oci.load_balancer.models.UpdateNetworkSecurityGroupsDetails(
            network_security_group_ids=network_security_group_ids,
        )

        response: oci.response.Response = client.update_network_security_groups(
            update_details, load_balancer_id
        )
        logger.info("Update Load Balancer network security groups request accepted")
        return map_response(response)

    except Exception as e:
        logger.error(
            f"Error in update_load_balancer_network_security_groups tool: {str(e)}"
        )
        raise e


@mcp.tool(
    name="list_load_balancer_listeners",
    description=(
        "List all listeners for the given load balancer. Use full OCID for load_balancer_id "
        "(do NOT use display_name or nickname). Example: call list_load_balancer_listeners with "
        "load_balancer_id=ocid1.loadbalancer.oc1..abcd"
        " IMPORTANT: Must be called by: list_load_balancer_listeners."
    ),
)
def list_load_balancer_listeners(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    limit: Optional[int] = Field(
        None,
        description="The maximum number of listeners to return. If None, all listeners are returned.",
        ge=1,
    ),
) -> list[Listener]:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.get_load_balancer(load_balancer_id)
        lb: oci.load_balancer.models.LoadBalancer = response.data
        listeners_map = getattr(lb, "listeners", {}) or {}
        listeners: list[Listener] = []
        for _, l in listeners_map.items():
            listeners.append(map_listener(l))
            if limit is not None and len(listeners) >= limit:
                break
        logger.info(f"Found {len(listeners)} Listeners")
        return listeners
    except Exception as e:
        logger.error(f"Error in list_load_balancer_listeners tool: {str(e)}")
        raise e


@mcp.tool(
    name="create_load_balancer_listener",
    description="Adds a listener to a load balancer",
)
def create_load_balancer_listener(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(
        ...,
        description="A friendly name for the listener",
        min_length=1,
        max_length=255,
    ),
    default_backend_set_name: str = Field(
        ...,
        description="The name of the associated backend set",
        min_length=1,
        max_length=32,
    ),
    port: int = Field(
        ..., description="The communication port for the listener", ge=1, le=65535
    ),
    protocol: Literal["HTTP", "HTTP2", "TCP", "GRPC"] = Field(
        ...,
        description="The protocol on which the listener accepts connection requests",
    ),
    hostname_names: Optional[list[str]] = Field(
        None, description="An array of hostname resource names"
    ),
    path_route_set_name: Optional[str] = Field(
        None,
        description="Deprecated. Name of the PathRouteSet applied to this listener",
    ),
    routing_policy_name: Optional[str] = Field(
        None, description="Name of the RoutingPolicy applied to this listener"
    ),
    rule_set_names: Optional[list[str]] = Field(
        None, description="Names of RuleSets applied to this listener"
    ),
    # SSL configuration (common subset)
    ssl_protocols: Optional[list[str]] = Field(
        None, description="Supported SSL protocols (e.g., TLSv1.2, TLSv1.3)"
    ),
    ssl_cipher_suite_name: Optional[str] = Field(
        None, description="Cipher suite name to use for SSL/HTTPS"
    ),
    ssl_server_order_preference: Optional[Literal["ENABLED", "DISABLED"]] = Field(
        None, description="Preference for server ciphers over client ciphers"
    ),
    ssl_certificate_name: Optional[str] = Field(
        None, description="Certificate bundle name configured on the load balancer"
    ),
    ssl_has_session_resumption: Optional[bool] = Field(
        None, description="Whether TLS session resumption should be enabled"
    ),
    ssl_verify_peer_certificate: Optional[bool] = Field(
        None, description="Whether to verify peer certificates"
    ),
    ssl_verify_depth: Optional[int] = Field(
        None, description="Max depth for peer certificate chain verification"
    ),
    # Connection configuration
    idle_timeout: Optional[int] = Field(
        None,
        description="Maximum idle time in seconds between client/backend operations",
    ),
    backend_tcp_proxy_protocol_version: Optional[int] = Field(
        None, description="Backend TCP Proxy Protocol version (1 or 2)"
    ),
    backend_tcp_proxy_protocol_options: Optional[
        list[Literal["PP2_TYPE_AUTHORITY"]]
    ] = Field(None, description="PPv2 options that can be enabled on TCP listeners"),
) -> Response:
    try:
        client = get_load_balancer_client()

        ssl_cfg = None
        if any(
            x is not None
            for x in [
                ssl_protocols,
                ssl_cipher_suite_name,
                ssl_server_order_preference,
                ssl_certificate_name,
                ssl_has_session_resumption,
                ssl_verify_peer_certificate,
                ssl_verify_depth,
            ]
        ):
            ssl_cfg = oci.load_balancer.models.SSLConfigurationDetails(
                protocols=ssl_protocols,
                cipher_suite_name=ssl_cipher_suite_name,
                server_order_preference=ssl_server_order_preference,
                certificate_name=ssl_certificate_name,
                has_session_resumption=ssl_has_session_resumption,
                verify_peer_certificate=ssl_verify_peer_certificate,
                verify_depth=ssl_verify_depth,
            )

        conn_cfg = None
        if any(
            x is not None
            for x in [
                idle_timeout,
                backend_tcp_proxy_protocol_version,
                backend_tcp_proxy_protocol_options,
            ]
        ):
            conn_cfg = oci.load_balancer.models.ConnectionConfiguration(
                idle_timeout=idle_timeout,
                backend_tcp_proxy_protocol_version=backend_tcp_proxy_protocol_version,
                backend_tcp_proxy_protocol_options=backend_tcp_proxy_protocol_options,
            )

        details = oci.load_balancer.models.CreateListenerDetails(
            name=name,
            default_backend_set_name=default_backend_set_name,
            port=port,
            protocol=protocol,
            hostname_names=hostname_names,
            path_route_set_name=path_route_set_name,
            ssl_configuration=ssl_cfg,
            connection_configuration=conn_cfg,
            routing_policy_name=routing_policy_name,
            rule_set_names=rule_set_names,
        )

        response: oci.response.Response = client.create_listener(
            details, load_balancer_id
        )
        logger.info("Create Listener request accepted")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in create_load_balancer_listener tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_load_balancer_listener",
    description="Gets a listener by name from the given load balancer",
)
def get_load_balancer_listener(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    listener_name: str = Field(..., description="The name of the listener to fetch"),
) -> Listener:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.get_load_balancer(load_balancer_id)
        lb: oci.load_balancer.models.LoadBalancer = response.data
        listeners_map = getattr(lb, "listeners", {}) or {}
        raw = listeners_map.get(listener_name)
        if raw is None:
            raise ValueError(
                f"Listener '{listener_name}' not found on load balancer {load_balancer_id}"
            )
        return map_listener(raw)
    except Exception as e:
        logger.error(f"Error in get_load_balancer_listener tool: {str(e)}")
        raise e


@mcp.tool(
    name="update_load_balancer_listener",
    description="Updates a listener for a given load balancer",
)
def update_load_balancer_listener(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    listener_name: str = Field(..., description="The name of the listener to update"),
    default_backend_set_name: Optional[str] = Field(
        None,
        description="The name of the associated backend set",
        min_length=1,
        max_length=32,
    ),
    port: Optional[int] = Field(
        None, description="The communication port for the listener", ge=1, le=65535
    ),
    protocol: Optional[Literal["HTTP", "HTTP2", "TCP", "GRPC"]] = Field(
        None,
        description="The protocol on which the listener accepts connection requests",
    ),
    hostname_names: Optional[list[str]] = Field(
        None, description="An array of hostname resource names"
    ),
    path_route_set_name: Optional[str] = Field(
        None,
        description="Deprecated. Name of the PathRouteSet applied to this listener",
    ),
    routing_policy_name: Optional[str] = Field(
        None, description="Name of the RoutingPolicy applied to this listener"
    ),
    rule_set_names: Optional[list[str]] = Field(
        None, description="Names of RuleSets applied to this listener"
    ),
    # SSL configuration (common subset)
    ssl_protocols: Optional[list[str]] = Field(
        None, description="Supported SSL protocols (e.g., TLSv1.2, TLSv1.3)"
    ),
    ssl_cipher_suite_name: Optional[str] = Field(
        None, description="Cipher suite name to use for SSL/HTTPS"
    ),
    ssl_server_order_preference: Optional[Literal["ENABLED", "DISABLED"]] = Field(
        None, description="Preference for server ciphers over client ciphers"
    ),
    ssl_certificate_name: Optional[str] = Field(
        None, description="Certificate bundle name configured on the load balancer"
    ),
    ssl_has_session_resumption: Optional[bool] = Field(
        None, description="Whether TLS session resumption should be enabled"
    ),
    ssl_verify_peer_certificate: Optional[bool] = Field(
        None, description="Whether to verify peer certificates"
    ),
    ssl_verify_depth: Optional[int] = Field(
        None, description="Max depth for peer certificate chain verification"
    ),
    # Connection configuration
    idle_timeout: Optional[int] = Field(
        None,
        description="Maximum idle time in seconds between client/backend operations",
    ),
    backend_tcp_proxy_protocol_version: Optional[int] = Field(
        None, description="Backend TCP Proxy Protocol version (1 or 2)"
    ),
    backend_tcp_proxy_protocol_options: Optional[
        list[Literal["PP2_TYPE_AUTHORITY"]]
    ] = Field(None, description="PPv2 options that can be enabled on TCP listeners"),
) -> Response:
    try:
        client = get_load_balancer_client()

        ssl_cfg = None
        if any(
            x is not None
            for x in [
                ssl_protocols,
                ssl_cipher_suite_name,
                ssl_server_order_preference,
                ssl_certificate_name,
                ssl_has_session_resumption,
                ssl_verify_peer_certificate,
                ssl_verify_depth,
            ]
        ):
            ssl_cfg = oci.load_balancer.models.SSLConfigurationDetails(
                protocols=ssl_protocols,
                cipher_suite_name=ssl_cipher_suite_name,
                server_order_preference=ssl_server_order_preference,
                certificate_name=ssl_certificate_name,
                has_session_resumption=ssl_has_session_resumption,
                verify_peer_certificate=ssl_verify_peer_certificate,
                verify_depth=ssl_verify_depth,
            )

        conn_cfg = None
        if any(
            x is not None
            for x in [
                idle_timeout,
                backend_tcp_proxy_protocol_version,
                backend_tcp_proxy_protocol_options,
            ]
        ):
            conn_cfg = oci.load_balancer.models.ConnectionConfiguration(
                idle_timeout=idle_timeout,
                backend_tcp_proxy_protocol_version=backend_tcp_proxy_protocol_version,
                backend_tcp_proxy_protocol_options=backend_tcp_proxy_protocol_options,
            )

        details = oci.load_balancer.models.UpdateListenerDetails(
            default_backend_set_name=default_backend_set_name,
            port=port,
            protocol=protocol,
            hostname_names=hostname_names,
            path_route_set_name=path_route_set_name,
            ssl_configuration=ssl_cfg,
            connection_configuration=conn_cfg,
            routing_policy_name=routing_policy_name,
            rule_set_names=rule_set_names,
        )

        response: oci.response.Response = client.update_listener(
            details, load_balancer_id, listener_name
        )
        logger.info("Update Listener request accepted")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in update_load_balancer_listener tool: {str(e)}")
        raise e


@mcp.tool(
    name="delete_load_balancer_listener",
    description="Deletes a listener from a load balancer",
)
def delete_load_balancer_listener(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    listener_name: str = Field(..., description="The name of the listener to delete"),
) -> Response:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.delete_listener(
            load_balancer_id, listener_name
        )
        logger.info("Delete Listener request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in delete_load_balancer_listener tool: {str(e)}")
        raise e


@mcp.tool(
    name="list_load_balancer_backend_sets",
    description="Lists the backend sets from the given load balancer",
)
def list_load_balancer_backend_sets(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    limit: Optional[int] = Field(
        None,
        description="The maximum number of backend sets to return. If None, all are returned.",
        ge=1,
    ),
) -> list[BackendSet]:
    try:
        client = get_load_balancer_client()
        backend_sets: list[BackendSet] = []
        response: oci.response.Response = client.list_backend_sets(load_balancer_id)
        items = getattr(response.data, "items", response.data) or []
        for d in items:
            backend_sets.append(map_backend_set(d))
            if limit is not None and len(backend_sets) >= limit:
                break
        logger.info(f"Found {len(backend_sets)} Backend Sets")
        return backend_sets
    except Exception as e:
        logger.error(f"Error in list_load_balancer_backend_sets tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_load_balancer_backend_set",
    description="Gets the backend set with the given name from the given load balancer",
)
def get_load_balancer_backend_set(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    backend_set_name: str = Field(
        ..., description="The name of the backend set to fetch"
    ),
) -> BackendSet:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.get_backend_set(
            load_balancer_id, backend_set_name
        )
        data: oci.load_balancer.models.BackendSet = response.data
        logger.info("Found Backend Set")
        return map_backend_set(data)
    except Exception as e:
        logger.error(f"Error in get_load_balancer_backend_set tool: {str(e)}")
        raise e


@mcp.tool(
    name="create_load_balancer_backend_set",
    description="Adds a backend set to a load balancer",
)
def create_load_balancer_backend_set(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="A friendly, unique backend set name",
    ),
    policy: str = Field(..., description="Load balancer policy for this backend set"),
    # Health checker (required argument must come before any optional args)
    health_checker_protocol: str = Field(
        ..., description="Protocol used for health checks (HTTP or TCP)"
    ),
    # Optional collections and tuning
    # Health checker (optional fields)
    health_checker_url_path: Optional[str] = Field(
        None, description="Path for HTTP health checks"
    ),
    health_checker_port: Optional[int] = Field(
        None, description="Port to use for the health check", ge=0, le=65535
    ),
    health_checker_return_code: Optional[int] = Field(
        None, description="Expected return code from healthy backend"
    ),
    health_checker_retries: Optional[int] = Field(
        None, description="Number of retries before marking backend unhealthy"
    ),
    health_checker_timeout_in_millis: Optional[int] = Field(
        None,
        description="Timeout in milliseconds for health check replies",
        ge=1,
        le=600000,
    ),
    health_checker_interval_in_millis: Optional[int] = Field(
        None,
        description="Interval between health checks in milliseconds",
        ge=1000,
        le=1800000,
    ),
    health_checker_response_body_regex: Optional[str] = Field(
        None, description="Regex to match against HTTP response body"
    ),
    health_checker_is_force_plain_text: Optional[bool] = Field(
        None,
        description=(
            "Force plaintext health checks regardless of backend set SSL configuration"
        ),
    ),
    backends: Optional[list[Backend]] = Field(
        None, description="Backends to include in the backend set"
    ),
    backend_max_connections: Optional[int] = Field(
        None,
        description=(
            "Max simultaneous connections to any backend unless overridden at backend level"
        ),
        ge=256,
        le=65535,
    ),
    # SSL configuration
    ssl_protocols: Optional[list[str]] = Field(
        None, description="Supported SSL protocols (e.g., TLSv1.2, TLSv1.3)"
    ),
    ssl_cipher_suite_name: Optional[str] = Field(
        None, description="Cipher suite name for SSL configuration"
    ),
    ssl_server_order_preference: Optional[Literal["ENABLED", "DISABLED"]] = Field(
        None, description="Preference for server ciphers over client ciphers"
    ),
    ssl_certificate_name: Optional[str] = Field(
        None, description="Certificate bundle name configured on the load balancer"
    ),
    ssl_certificate_ids: Optional[list[str]] = Field(
        None, description="OCI Certificates service certificate OCIDs"
    ),
    ssl_trusted_certificate_authority_ids: Optional[list[str]] = Field(
        None, description="OCI Certificates CA/bundle OCIDs to trust"
    ),
    ssl_has_session_resumption: Optional[bool] = Field(
        None, description="Whether TLS session resumption should be enabled"
    ),
    ssl_verify_peer_certificate: Optional[bool] = Field(
        None, description="Whether to verify peer certificates"
    ),
    ssl_verify_depth: Optional[int] = Field(
        None, description="Max depth for peer certificate chain verification"
    ),
    # Session persistence (application cookie)
    session_persistence_cookie_name: Optional[str] = Field(
        None, description="Cookie name for application-cookie stickiness"
    ),
    session_persistence_disable_fallback: Optional[bool] = Field(
        None,
        description="Disable fallback to a different backend when original unavailable",
    ),
    # LB cookie persistence
    lb_cookie_cookie_name: Optional[str] = Field(
        None, description="Name of cookie inserted by the load balancer"
    ),
    lb_cookie_disable_fallback: Optional[bool] = Field(
        None, description="Disable fallback when original backend unavailable"
    ),
    lb_cookie_domain: Optional[str] = Field(None, description="Cookie domain"),
    lb_cookie_path: Optional[str] = Field(None, description="Cookie path"),
    lb_cookie_max_age_in_seconds: Optional[int] = Field(
        None, description="Cookie Max-Age in seconds"
    ),
    lb_cookie_is_secure: Optional[bool] = Field(
        None, description="Whether to set the Secure attribute on the cookie"
    ),
    lb_cookie_is_http_only: Optional[bool] = Field(
        None, description="Whether to set the HttpOnly attribute on the cookie"
    ),
) -> Response:
    try:
        client = get_load_balancer_client()

        # Health checker details (protocol is required; always build)
        health_checker = oci.load_balancer.models.HealthCheckerDetails(
            protocol=health_checker_protocol,
            url_path=health_checker_url_path,
            port=health_checker_port,
            return_code=health_checker_return_code,
            retries=health_checker_retries,
            timeout_in_millis=health_checker_timeout_in_millis,
            interval_in_millis=health_checker_interval_in_millis,
            response_body_regex=health_checker_response_body_regex,
            is_force_plain_text=health_checker_is_force_plain_text,
        )

        # SSL configuration
        ssl_cfg = None
        if any(
            x is not None
            for x in [
                ssl_protocols,
                ssl_cipher_suite_name,
                ssl_server_order_preference,
                ssl_certificate_name,
                ssl_certificate_ids,
                ssl_trusted_certificate_authority_ids,
                ssl_has_session_resumption,
                ssl_verify_peer_certificate,
                ssl_verify_depth,
            ]
        ):
            ssl_cfg = oci.load_balancer.models.SSLConfigurationDetails(
                protocols=ssl_protocols,
                cipher_suite_name=ssl_cipher_suite_name,
                server_order_preference=ssl_server_order_preference,
                certificate_name=ssl_certificate_name,
                certificate_ids=ssl_certificate_ids,
                trusted_certificate_authority_ids=ssl_trusted_certificate_authority_ids,
                has_session_resumption=ssl_has_session_resumption,
                verify_peer_certificate=ssl_verify_peer_certificate,
                verify_depth=ssl_verify_depth,
            )

        # Session persistence
        session_persistence = None
        if any(
            x is not None
            for x in [
                session_persistence_cookie_name,
                session_persistence_disable_fallback,
            ]
        ):
            session_persistence = (
                oci.load_balancer.models.SessionPersistenceConfigurationDetails(
                    cookie_name=session_persistence_cookie_name,
                    disable_fallback=session_persistence_disable_fallback,
                )
            )

        # LB cookie persistence
        lb_cookie_persistence = None
        if any(
            x is not None
            for x in [
                lb_cookie_cookie_name,
                lb_cookie_disable_fallback,
                lb_cookie_domain,
                lb_cookie_path,
                lb_cookie_max_age_in_seconds,
                lb_cookie_is_secure,
                lb_cookie_is_http_only,
            ]
        ):
            lb_cookie_persistence = (
                oci.load_balancer.models.LBCookieSessionPersistenceConfigurationDetails(
                    cookie_name=lb_cookie_cookie_name,
                    disable_fallback=lb_cookie_disable_fallback,
                    domain=lb_cookie_domain,
                    path=lb_cookie_path,
                    max_age_in_seconds=lb_cookie_max_age_in_seconds,
                    is_secure=lb_cookie_is_secure,
                    is_http_only=lb_cookie_is_http_only,
                )
            )

        # Backend details conversion
        backend_details = None
        if backends is not None:
            backend_details = [
                oci.load_balancer.models.BackendDetails(
                    ip_address=b.ip_address,
                    port=b.port,
                    weight=b.weight,
                    max_connections=b.max_connections,
                    backup=b.backup,
                    drain=b.drain,
                    offline=b.offline,
                )
                for b in backends
            ]

        details = oci.load_balancer.models.CreateBackendSetDetails(
            name=name,
            policy=policy,
            backends=backend_details,
            backend_max_connections=backend_max_connections,
            health_checker=health_checker,
            ssl_configuration=ssl_cfg,
            session_persistence_configuration=session_persistence,
            lb_cookie_session_persistence_configuration=lb_cookie_persistence,
        )

        response: oci.response.Response = client.create_backend_set(
            details, load_balancer_id
        )
        logger.info("Create Backend Set request accepted")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in create_load_balancer_backend_set tool: {str(e)}")
        raise e


@mcp.tool(
    name="update_load_balancer_backend_set",
    description="Updates a backend set on a load balancer",
)
def update_load_balancer_backend_set(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="The name of the backend set to update",
    ),
    policy: Optional[str] = Field(
        None, description="Load balancer policy for this backend set"
    ),
    backends: Optional[list[Backend]] = Field(
        None, description="Backends to include in the backend set"
    ),
    backend_max_connections: Optional[int] = Field(
        None,
        description=(
            "Max simultaneous connections to any backend unless overridden at backend level"
        ),
        ge=256,
        le=65535,
    ),
    # Health checker (same fields as create)
    health_checker_protocol: Optional[str] = Field(
        None, description="Protocol used for health checks (HTTP or TCP)"
    ),
    health_checker_url_path: Optional[str] = Field(
        None, description="Path for HTTP health checks"
    ),
    health_checker_port: Optional[int] = Field(
        None, description="Port to use for the health check", ge=0, le=65535
    ),
    health_checker_return_code: Optional[int] = Field(
        None, description="Expected return code from healthy backend"
    ),
    health_checker_retries: Optional[int] = Field(
        None, description="Number of retries before marking backend unhealthy"
    ),
    health_checker_timeout_in_millis: Optional[int] = Field(
        None,
        description="Timeout in milliseconds for health check replies",
        ge=1,
        le=600000,
    ),
    health_checker_interval_in_millis: Optional[int] = Field(
        None,
        description="Interval between health checks in milliseconds",
        ge=1000,
        le=1800000,
    ),
    health_checker_response_body_regex: Optional[str] = Field(
        None, description="Regex to match against HTTP response body"
    ),
    health_checker_is_force_plain_text: Optional[bool] = Field(
        None,
        description=(
            "Force plaintext health checks regardless of backend set SSL configuration"
        ),
    ),
    # SSL configuration
    ssl_protocols: Optional[list[str]] = Field(
        None, description="Supported SSL protocols (e.g., TLSv1.2, TLSv1.3)"
    ),
    ssl_cipher_suite_name: Optional[str] = Field(
        None, description="Cipher suite name for SSL configuration"
    ),
    ssl_server_order_preference: Optional[Literal["ENABLED", "DISABLED"]] = Field(
        None, description="Preference for server ciphers over client ciphers"
    ),
    ssl_certificate_name: Optional[str] = Field(
        None, description="Certificate bundle name configured on the load balancer"
    ),
    ssl_certificate_ids: Optional[list[str]] = Field(
        None, description="OCI Certificates service certificate OCIDs"
    ),
    ssl_trusted_certificate_authority_ids: Optional[list[str]] = Field(
        None, description="OCI Certificates CA/bundle OCIDs to trust"
    ),
    ssl_has_session_resumption: Optional[bool] = Field(
        None, description="Whether TLS session resumption should be enabled"
    ),
    ssl_verify_peer_certificate: Optional[bool] = Field(
        None, description="Whether to verify peer certificates"
    ),
    ssl_verify_depth: Optional[int] = Field(
        None, description="Max depth for peer certificate chain verification"
    ),
    # Session persistence (application cookie)
    session_persistence_cookie_name: Optional[str] = Field(
        None, description="Cookie name for application-cookie stickiness"
    ),
    session_persistence_disable_fallback: Optional[bool] = Field(
        None,
        description="Disable fallback to a different backend when original unavailable",
    ),
    # LB cookie persistence
    lb_cookie_cookie_name: Optional[str] = Field(
        None, description="Name of cookie inserted by the load balancer"
    ),
    lb_cookie_disable_fallback: Optional[bool] = Field(
        None, description="Disable fallback when original backend unavailable"
    ),
    lb_cookie_domain: Optional[str] = Field(None, description="Cookie domain"),
    lb_cookie_path: Optional[str] = Field(None, description="Cookie path"),
    lb_cookie_max_age_in_seconds: Optional[int] = Field(
        None, description="Cookie Max-Age in seconds"
    ),
    lb_cookie_is_secure: Optional[bool] = Field(
        None, description="Whether to set the Secure attribute on the cookie"
    ),
    lb_cookie_is_http_only: Optional[bool] = Field(
        None, description="Whether to set the HttpOnly attribute on the cookie"
    ),
) -> Response:
    try:
        client = get_load_balancer_client()

        # Always fetch current backend set so we can safely preserve unspecified fields
        current_bs = client.get_backend_set(load_balancer_id, name).data

        # Determine policy value (preserve existing if not provided)
        effective_policy = (
            policy if policy is not None else getattr(current_bs, "policy", None)
        )

        # Backend details conversion (preserve existing if not provided)
        if backends is not None:
            backend_details = [
                oci.load_balancer.models.BackendDetails(
                    ip_address=b.ip_address,
                    port=b.port,
                    weight=b.weight,
                    max_connections=b.max_connections,
                    backup=b.backup,
                    drain=b.drain,
                    offline=b.offline,
                )
                for b in backends
            ]
        else:
            existing_backends = (
                (getattr(current_bs, "backends", []) or []) if current_bs else []
            )
            backend_details = [
                oci.load_balancer.models.BackendDetails(
                    ip_address=b.ip_address,
                    port=b.port,
                    weight=b.weight,
                    max_connections=b.max_connections,
                    backup=b.backup,
                    drain=b.drain,
                    offline=b.offline,
                )
                for b in existing_backends
            ]

        # Health checker fields (preserve existing where not provided)
        if current_bs:
            existing_hc = getattr(current_bs, "health_checker", None)
        else:
            existing_hc = None
        health_checker = oci.load_balancer.models.HealthCheckerDetails(
            protocol=health_checker_protocol
            or (existing_hc.protocol if existing_hc else None),
            url_path=(
                health_checker_url_path
                if health_checker_url_path is not None
                else (existing_hc.url_path if existing_hc else None)
            ),
            port=(
                health_checker_port
                if health_checker_port is not None
                else (existing_hc.port if existing_hc else None)
            ),
            return_code=(
                health_checker_return_code
                if health_checker_return_code is not None
                else (existing_hc.return_code if existing_hc else None)
            ),
            retries=(
                health_checker_retries
                if health_checker_retries is not None
                else (existing_hc.retries if existing_hc else None)
            ),
            timeout_in_millis=(
                health_checker_timeout_in_millis
                if health_checker_timeout_in_millis is not None
                else (existing_hc.timeout_in_millis if existing_hc else None)
            ),
            interval_in_millis=(
                health_checker_interval_in_millis
                if health_checker_interval_in_millis is not None
                else (existing_hc.interval_in_millis if existing_hc else None)
            ),
            response_body_regex=(
                health_checker_response_body_regex
                if health_checker_response_body_regex is not None
                else (existing_hc.response_body_regex if existing_hc else None)
            ),
            is_force_plain_text=(
                health_checker_is_force_plain_text
                if health_checker_is_force_plain_text is not None
                else (existing_hc.is_force_plain_text if existing_hc else None)
            ),
        )

        # SSL configuration
        ssl_cfg = None
        if any(
            x is not None
            for x in [
                ssl_protocols,
                ssl_cipher_suite_name,
                ssl_server_order_preference,
                ssl_certificate_name,
                ssl_certificate_ids,
                ssl_trusted_certificate_authority_ids,
                ssl_has_session_resumption,
                ssl_verify_peer_certificate,
                ssl_verify_depth,
            ]
        ):
            ssl_cfg = oci.load_balancer.models.SSLConfigurationDetails(
                protocols=ssl_protocols,
                cipher_suite_name=ssl_cipher_suite_name,
                server_order_preference=ssl_server_order_preference,
                certificate_name=ssl_certificate_name,
                certificate_ids=ssl_certificate_ids,
                trusted_certificate_authority_ids=ssl_trusted_certificate_authority_ids,
                has_session_resumption=ssl_has_session_resumption,
                verify_peer_certificate=ssl_verify_peer_certificate,
                verify_depth=ssl_verify_depth,
            )

        # Session persistence
        session_persistence = None
        if any(
            x is not None
            for x in [
                session_persistence_cookie_name,
                session_persistence_disable_fallback,
            ]
        ):
            session_persistence = (
                oci.load_balancer.models.SessionPersistenceConfigurationDetails(
                    cookie_name=session_persistence_cookie_name,
                    disable_fallback=session_persistence_disable_fallback,
                )
            )

        # LB cookie persistence
        lb_cookie_persistence = None
        if any(
            x is not None
            for x in [
                lb_cookie_cookie_name,
                lb_cookie_disable_fallback,
                lb_cookie_domain,
                lb_cookie_path,
                lb_cookie_max_age_in_seconds,
                lb_cookie_is_secure,
                lb_cookie_is_http_only,
            ]
        ):
            lb_cookie_persistence = (
                oci.load_balancer.models.LBCookieSessionPersistenceConfigurationDetails(
                    cookie_name=lb_cookie_cookie_name,
                    disable_fallback=lb_cookie_disable_fallback,
                    domain=lb_cookie_domain,
                    path=lb_cookie_path,
                    max_age_in_seconds=lb_cookie_max_age_in_seconds,
                    is_secure=lb_cookie_is_secure,
                    is_http_only=lb_cookie_is_http_only,
                )
            )

        details = oci.load_balancer.models.UpdateBackendSetDetails(
            policy=effective_policy,
            backends=backend_details,
            backend_max_connections=backend_max_connections,
            health_checker=health_checker,
            ssl_configuration=ssl_cfg,
            session_persistence_configuration=session_persistence,
            lb_cookie_session_persistence_configuration=lb_cookie_persistence,
        )

        response: oci.response.Response = client.update_backend_set(
            details, load_balancer_id, name
        )
        logger.info("Update Backend Set request accepted")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in update_load_balancer_backend_set tool: {str(e)}")
        raise e


@mcp.tool(
    name="delete_load_balancer_backend_set",
    description="Deletes a backend set from a load balancer",
)
def delete_load_balancer_backend_set(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="The name of the backend set to delete",
    ),
) -> Response:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.delete_backend_set(
            load_balancer_id, name
        )
        logger.info("Delete Backend Set request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in delete_load_balancer_backend_set tool: {str(e)}")
        raise e


@mcp.tool(
    name="list_backends",
    description="Lists the backends from the given backend set and load balancer",
)
def list_backends(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    backend_set_name: str = Field(..., description="The name of the backend set"),
    limit: Optional[int] = Field(
        None,
        description="The maximum number of backends to return. If None, all are returned.",
        ge=1,
    ),
) -> list[Backend]:
    try:
        client = get_load_balancer_client()
        backends: list[Backend] = []
        response: oci.response.Response = client.list_backends(
            load_balancer_id, backend_set_name
        )
        items = getattr(response.data, "items", response.data) or []
        for d in items:
            backends.append(map_backend(d))
            if limit is not None and len(backends) >= limit:
                break
        logger.info(f"Found {len(backends)} Backends")
        return backends
    except Exception as e:
        logger.error(f"Error in list_backends tool: {str(e)}")
        raise e


@mcp.tool(
    name="create_backend",
    description="Adds a backend to a backend set",
)
def create_backend(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    backend_set_name: str = Field(..., description="The name of the backend set"),
    ip_address: str = Field(..., description="IP address of the backend server"),
    port: int = Field(..., description="Port of the backend server", ge=1, le=65535),
    weight: Optional[int] = Field(
        None, description="Load balancing weight for the backend", ge=1, le=100
    ),
    max_connections: Optional[int] = Field(
        None, description="Maximum simultaneous connections for the backend"
    ),
    backup: Optional[bool] = Field(
        None, description="Whether this backend is a backup"
    ),
    drain: Optional[bool] = Field(
        None, description="Whether the backend is in drain mode"
    ),
    offline: Optional[bool] = Field(None, description="Whether the backend is offline"),
) -> Response:
    try:
        client = get_load_balancer_client()
        details = oci.load_balancer.models.CreateBackendDetails(
            ip_address=ip_address,
            port=port,
            weight=weight,
            max_connections=max_connections,
            backup=backup,
            drain=drain,
            offline=offline,
        )
        response: oci.response.Response = client.create_backend(
            details, load_balancer_id, backend_set_name
        )
        logger.info("Create Backend request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in create_backend tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_backend",
    description="Gets a backend by name from the given backend set and load balancer",
)
def get_backend(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    backend_set_name: str = Field(..., description="The name of the backend set"),
    backend_name: str = Field(..., description="The name of the backend (IP:port)"),
) -> Backend:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.get_backend(
            load_balancer_id, backend_set_name, backend_name
        )
        data: oci.load_balancer.models.Backend = response.data
        logger.info("Found Backend")
        return map_backend(data)
    except Exception as e:
        logger.error(f"Error in get_backend tool: {str(e)}")
        raise e


@mcp.tool(
    name="update_backend",
    description="Updates a backend in a backend set",
)
def update_backend(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    backend_set_name: str = Field(..., description="The name of the backend set"),
    backend_name: str = Field(..., description="The name of the backend (IP:port)"),
    weight: Optional[int] = Field(
        None, description="Load balancing weight for the backend", ge=1, le=100
    ),
    max_connections: Optional[int] = Field(
        None, description="Maximum simultaneous connections for the backend"
    ),
    backup: Optional[bool] = Field(
        None, description="Whether this backend is a backup"
    ),
    drain: Optional[bool] = Field(
        None, description="Whether the backend is in drain mode"
    ),
    offline: Optional[bool] = Field(None, description="Whether the backend is offline"),
) -> Response:
    try:
        client = get_load_balancer_client()
        details = oci.load_balancer.models.UpdateBackendDetails(
            weight=weight,
            max_connections=max_connections,
            backup=backup,
            drain=drain,
            offline=offline,
        )
        response: oci.response.Response = client.update_backend(
            details, load_balancer_id, backend_set_name, backend_name
        )
        logger.info("Update Backend request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in update_backend tool: {str(e)}")
        raise e


@mcp.tool(
    name="delete_backend",
    description="Deletes a backend from a backend set",
)
def delete_backend(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    backend_set_name: str = Field(..., description="The name of the backend set"),
    backend_name: str = Field(..., description="The name of the backend (IP:port)"),
) -> Response:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.delete_backend(
            load_balancer_id, backend_set_name, backend_name
        )
        logger.info("Delete Backend request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in delete_backend tool: {str(e)}")
        raise e


@mcp.tool(
    name="list_load_balancer_certificates",
    description="Lists the certificates from the given load balancer",
)
def list_load_balancer_certificates(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    limit: Optional[int] = Field(
        None,
        description="The maximum number of certificates to return. If None, all are returned.",
        ge=1,
    ),
) -> list[Certificate]:
    try:
        client = get_load_balancer_client()
        certificates: list[Certificate] = []
        response: oci.response.Response = client.list_certificates(load_balancer_id)
        items = getattr(response.data, "items", response.data) or []
        for d in items:
            certificates.append(map_certificate(d))
            if limit is not None and len(certificates) >= limit:
                break
        logger.info(f"Found {len(certificates)} Certificates")
        return certificates
    except Exception as e:
        logger.error(f"Error in list_load_balancer_certificates tool: {str(e)}")
        raise e


@mcp.tool(
    name="create_load_balancer_certificate",
    description="Creates a new certificate for HTTPS termination on a load balancer",
)
def create_load_balancer_certificate(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    certificate_name: str = Field(
        ..., description="A friendly name for the certificate"
    ),
    public_certificate: str = Field(..., description="Public certificate PEM contents"),
    private_key: str = Field(..., description="Private key PEM contents"),
    ca_certificate: Optional[str] = Field(
        None,
        description="CA certificate PEM contents (optional if using certificate bundle)",
    ),
    passphrase: Optional[str] = Field(
        None, description="Passphrase for the private key if encrypted"
    ),
) -> Response:
    try:
        client = get_load_balancer_client()
        details = oci.load_balancer.models.CreateCertificateDetails(
            certificate_name=certificate_name,
            ca_certificate=ca_certificate,
            public_certificate=public_certificate,
            private_key=private_key,
            passphrase=passphrase,
        )
        response: oci.response.Response = client.create_certificate(
            details, load_balancer_id
        )
        logger.info("Create Certificate request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in create_load_balancer_certificate tool: {str(e)}")
        raise e


@mcp.tool(
    name="delete_load_balancer_certificate",
    description="Deletes a certificate from a load balancer",
)
def delete_load_balancer_certificate(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    certificate_name: str = Field(
        ..., description="The name of the certificate to delete"
    ),
) -> Response:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.delete_certificate(
            load_balancer_id, certificate_name
        )
        logger.info("Delete Certificate request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in delete_load_balancer_certificate tool: {str(e)}")
        raise e


# SSL Cipher Suite tools


@mcp.tool(
    name="list_ssl_cipher_suites",
    description="Lists the SSL cipher suites from the given load balancer",
)
def list_ssl_cipher_suites(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    limit: Optional[int] = Field(
        None,
        description="Maximum number of cipher suites to return. If None, all are returned.",
        ge=1,
    ),
) -> list[SSLCipherSuite]:
    try:
        client = get_load_balancer_client()
        cipher_suites: list[SSLCipherSuite] = []
        response: oci.response.Response = client.list_ssl_cipher_suites(
            load_balancer_id
        )
        items = getattr(response.data, "items", response.data) or []
        for d in items:
            cipher_suites.append(map_ssl_cipher_suite(d))
            if limit is not None and len(cipher_suites) >= limit:
                break
        logger.info(f"Found {len(cipher_suites)} SSL Cipher Suites")
        return cipher_suites
    except Exception as e:
        logger.error(f"Error in list_ssl_cipher_suites tool: {str(e)}")
        raise e


@mcp.tool(
    name="create_ssl_cipher_suite",
    description="Creates a new SSL cipher suite for a load balancer",
)
def create_ssl_cipher_suite(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Friendly name for the SSL cipher suite"),
    ciphers: list[str] = Field(..., description="List of cipher names for the suite"),
) -> Response:
    try:
        client = get_load_balancer_client()
        details = oci.load_balancer.models.CreateSSLCipherSuiteDetails(
            name=name,
            ciphers=ciphers,
        )
        response: oci.response.Response = client.create_ssl_cipher_suite(
            details, load_balancer_id
        )
        logger.info("Create SSL Cipher Suite request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in create_ssl_cipher_suite tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_ssl_cipher_suite",
    description="Gets an SSL cipher suite by name from a load balancer",
)
def get_ssl_cipher_suite(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Name of the SSL cipher suite to retrieve"),
) -> SSLCipherSuite:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.get_ssl_cipher_suite(
            load_balancer_id, name
        )
        data: oci.load_balancer.models.SSLCipherSuite = response.data
        logger.info("Found SSL Cipher Suite")
        return map_ssl_cipher_suite(data)
    except Exception as e:
        logger.error(f"Error in get_ssl_cipher_suite tool: {str(e)}")
        raise e


@mcp.tool(
    name="update_ssl_cipher_suite",
    description="Updates an existing SSL cipher suite for a load balancer",
)
def update_ssl_cipher_suite(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Name of the SSL cipher suite to update"),
    ciphers: Optional[list[str]] = Field(
        None, description="Updated list of cipher names for the suite"
    ),
) -> Response:
    try:
        client = get_load_balancer_client()
        details = oci.load_balancer.models.UpdateSSLCipherSuiteDetails(
            ciphers=ciphers,
        )
        response: oci.response.Response = client.update_ssl_cipher_suite(
            details, load_balancer_id, name
        )
        logger.info("Update SSL Cipher Suite request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in update_ssl_cipher_suite tool: {str(e)}")
        raise e


@mcp.tool(
    name="delete_ssl_cipher_suite",
    description="Deletes an SSL cipher suite from a load balancer",
)
def delete_ssl_cipher_suite(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Name of the SSL cipher suite to delete"),
) -> Response:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.delete_ssl_cipher_suite(
            load_balancer_id, name
        )
        logger.info("Delete SSL Cipher Suite request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in delete_ssl_cipher_suite tool: {str(e)}")
        raise e


# -------------------------------------------------------------------------
# Advanced routing and rule tools
# -------------------------------------------------------------------------

# Hostname tools


@mcp.tool(
    name="list_hostnames",
    description="Lists the hostnames from the given load balancer",
)
def list_hostnames(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    limit: Optional[int] = Field(
        None,
        description="Maximum number of hostnames to return. If None, all are returned.",
        ge=1,
    ),
) -> list[Hostname]:
    try:
        client = get_load_balancer_client()
        hostnames: list[Hostname] = []
        response: oci.response.Response = client.list_hostnames(load_balancer_id)
        items = getattr(response.data, "items", response.data) or []
        for d in items:
            hostnames.append(map_hostname(d))
            if limit is not None and len(hostnames) >= limit:
                break
        logger.info(f"Found {len(hostnames)} Hostnames")
        return hostnames
    except Exception as e:
        logger.error(f"Error in list_hostnames tool: {str(e)}")
        raise e


@mcp.tool(
    name="create_hostname",
    description="Creates a new hostname resource for a load balancer",
)
def create_hostname(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Unique name for the hostname resource"),
    hostname: str = Field(..., description="Virtual hostname (e.g., app.example.com)"),
) -> Response:
    try:
        client = get_load_balancer_client()
        details = oci.load_balancer.models.CreateHostnameDetails(
            name=name,
            hostname=hostname,
        )
        response: oci.response.Response = client.create_hostname(
            details, load_balancer_id
        )
        logger.info("Create Hostname request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in create_hostname tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_hostname",
    description="Gets a hostname resource by name from a load balancer",
)
def get_hostname(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Name of the hostname resource"),
) -> Hostname:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.get_hostname(load_balancer_id, name)
        data = response.data
        logger.info("Found Hostname")
        return map_hostname(data)
    except Exception as e:
        logger.error(f"Error in get_hostname tool: {str(e)}")
        raise e


@mcp.tool(
    name="update_hostname",
    description="Updates an existing hostname resource",
)
def update_hostname(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Name of the hostname resource to update"),
    hostname: Optional[str] = Field(
        None, description="New virtual hostname (e.g., app.example.com)"
    ),
) -> Response:
    try:
        client = get_load_balancer_client()
        details = oci.load_balancer.models.UpdateHostnameDetails(
            hostname=hostname,
        )
        response: oci.response.Response = client.update_hostname(
            details, load_balancer_id, name
        )
        logger.info("Update Hostname request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in update_hostname tool: {str(e)}")
        raise e


@mcp.tool(
    name="delete_hostname",
    description="Deletes a hostname resource from a load balancer",
)
def delete_hostname(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Name of the hostname resource to delete"),
) -> Response:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.delete_hostname(load_balancer_id, name)
        logger.info("Delete Hostname request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in delete_hostname tool: {str(e)}")
        raise e


# Rule Set tools


@mcp.tool(
    name="list_rule_sets",
    description="Lists the rule sets from the given load balancer",
)
def list_rule_sets(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    limit: Optional[int] = Field(
        None,
        description="Maximum number of rule sets to return. If None, all are returned.",
        ge=1,
    ),
) -> list[RuleSet]:
    try:
        client = get_load_balancer_client()
        rule_sets: list[RuleSet] = []
        response: oci.response.Response = client.list_rule_sets(load_balancer_id)
        items = getattr(response.data, "items", response.data) or []
        for d in items:
            rule_sets.append(map_rule_set(d))
            if limit is not None and len(rule_sets) >= limit:
                break

        logger.info(f"Found {len(rule_sets)} Rule Sets")
        return rule_sets
    except Exception as e:
        logger.error(f"Error in list_rule_sets tool: {str(e)}")
        raise e


@mcp.tool(
    name="create_rule_set",
    description="Creates a new rule set for a load balancer",
)
def create_rule_set(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Unique name for the rule set"),
    items: Optional[list[dict]] = Field(
        None,
        description="List of rule definitions (raw dicts) to include in the rule set",
    ),
) -> Response:
    try:
        client = get_load_balancer_client()
        details = oci.load_balancer.models.CreateRuleSetDetails(
            name=name,
            items=items,
        )
        response: oci.response.Response = client.create_rule_set(
            load_balancer_id, details
        )
        logger.info("Create Rule Set request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in create_rule_set tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_rule_set",
    description="Gets a rule set by name from a load balancer",
)
def get_rule_set(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Name of the rule set"),
) -> RuleSet:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.get_rule_set(load_balancer_id, name)
        data = response.data
        logger.info("Found Rule Set")
        return map_rule_set(data)
    except Exception as e:
        logger.error(f"Error in get_rule_set tool: {str(e)}")
        raise e


@mcp.tool(
    name="update_rule_set",
    description="Updates an existing rule set",
)
def update_rule_set(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Name of the rule set to update"),
    items: Optional[list[dict]] = Field(
        None,
        description="Updated list of rule definitions (raw dicts)",
    ),
) -> Response:
    try:
        client = get_load_balancer_client()
        details = oci.load_balancer.models.UpdateRuleSetDetails(
            items=items,
        )
        response: oci.response.Response = client.update_rule_set(
            load_balancer_id, name, details
        )
        logger.info("Update Rule Set request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in update_rule_set tool: {str(e)}")
        raise e


@mcp.tool(
    name="delete_rule_set",
    description="Deletes a rule set from a load balancer",
)
def delete_rule_set(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Name of the rule set to delete"),
) -> Response:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.delete_rule_set(load_balancer_id, name)
        logger.info("Delete Rule Set request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in delete_rule_set tool: {str(e)}")
        raise e


# Routing Policy tools


@mcp.tool(
    name="list_routing_policies",
    description="Lists the routing policies from the given load balancer",
)
def list_routing_policies(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    limit: Optional[int] = Field(
        None,
        description="Maximum number of routing policies to return. If None, all are returned.",
        ge=1,
    ),
) -> list[RoutingPolicy]:
    try:
        client = get_load_balancer_client()
        policies: list[RoutingPolicy] = []
        next_page: Optional[str] = None
        first_page = True

        while first_page or (next_page and (limit is None or len(policies) < limit)):
            first_page = False
            page_limit = None if limit is None else max(1, limit - len(policies))
            response = client.list_routing_policies(
                load_balancer_id, limit=page_limit, page=next_page
            )
            items = getattr(response.data, "items", response.data) or []
            remaining = None if limit is None else max(0, limit - len(policies))
            to_process = items if remaining is None else items[:remaining]
            for d in to_process:
                policies.append(map_routing_policy(d))
            next_page = getattr(response, "next_page", None)

        logger.info(f"Found {len(policies)} Routing Policies")
        return policies
    except Exception as e:
        logger.error(f"Error in list_routing_policies tool: {str(e)}")
        raise e


@mcp.tool(
    name="create_routing_policy",
    description="Creates a new routing policy for a load balancer",
)
def create_routing_policy(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Unique name for the routing policy"),
    condition_language_version: Optional[Literal["V1", "UNKNOWN_ENUM_VALUE"]] = Field(
        None, description="Version of the routing condition language"
    ),
    rules: Optional[list[dict]] = Field(
        None, description="List of routing rule definitions (raw dicts)"
    ),
) -> Response:
    try:
        client = get_load_balancer_client()
        details = oci.load_balancer.models.CreateRoutingPolicyDetails(
            name=name,
            condition_language_version=condition_language_version,
            rules=rules,
        )
        response: oci.response.Response = client.create_routing_policy(
            details, load_balancer_id
        )
        logger.info("Create Routing Policy request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in create_routing_policy tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_routing_policy",
    description="Gets a routing policy by name from a load balancer",
)
def get_routing_policy(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Name of the routing policy"),
) -> RoutingPolicy:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.get_routing_policy(
            load_balancer_id, name
        )
        data = response.data
        logger.info("Found Routing Policy")
        return map_routing_policy(data)
    except Exception as e:
        logger.error(f"Error in get_routing_policy tool: {str(e)}")
        raise e


@mcp.tool(
    name="update_routing_policy",
    description="Updates an existing routing policy",
)
def update_routing_policy(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Name of the routing policy to update"),
    condition_language_version: Optional[Literal["V1", "UNKNOWN_ENUM_VALUE"]] = Field(
        None, description="Version of the routing condition language"
    ),
    rules: Optional[list[dict]] = Field(
        None, description="Updated list of routing rule definitions (raw dicts)"
    ),
) -> Response:
    try:
        client = get_load_balancer_client()
        details = oci.load_balancer.models.UpdateRoutingPolicyDetails(
            condition_language_version=condition_language_version,
            rules=rules,
        )
        response: oci.response.Response = client.update_routing_policy(
            details, load_balancer_id, name
        )
        logger.info("Update Routing Policy request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in update_routing_policy tool: {str(e)}")
        raise e


@mcp.tool(
    name="delete_routing_policy",
    description="Deletes a routing policy from a load balancer",
)
def delete_routing_policy(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    name: str = Field(..., description="Name of the routing policy to delete"),
) -> Response:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.delete_routing_policy(
            load_balancer_id, name
        )
        logger.info("Delete Routing Policy request accepted")
        return map_response(response)
    except Exception as e:
        logger.error(f"Error in delete_routing_policy tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_load_balancer_health",
    description="Get health status of a load balancer",
)
def get_load_balancer_health(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer")
) -> LoadBalancerHealth:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.get_load_balancer_health(
            load_balancer_id
        )
        data = response.data
        logger.info("Retrieved Load Balancer health")
        return map_load_balancer_health(data)
    except Exception as e:
        logger.error(f"Error in get_load_balancer_health tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_backend_set_health",
    description="Get health status of a backend set within a load balancer",
)
def get_backend_set_health(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    backend_set_name: str = Field(..., description="The name of the backend set"),
) -> BackendSetHealth:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.get_backend_set_health(
            load_balancer_id, backend_set_name
        )
        data = response.data
        logger.info("Retrieved Backend Set health")
        return map_backend_set_health(data)
    except Exception as e:
        logger.error(f"Error in get_backend_set_health tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_backend_health",
    description="Get health status of a specific backend within a backend set",
)
def get_backend_health(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    backend_set_name: str = Field(..., description="The name of the backend set"),
    backend_name: str = Field(..., description="The name of the backend (IP:port)"),
) -> BackendHealth:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.get_backend_health(
            load_balancer_id, backend_set_name, backend_name
        )
        data = response.data
        logger.info("Retrieved Backend health")
        return map_backend_health(data)
    except Exception as e:
        logger.error(f"Error in get_backend_health tool: {str(e)}")
        raise e


@mcp.tool(
    name="list_load_balancer_healths",
    description="List health summaries for all load balancers in a compartment",
)
def list_load_balancer_healths(
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    limit: Optional[int] = Field(
        None,
        description="Maximum number of health summaries to return. If None, no limit.",
        ge=1,
    ),
) -> list[LoadBalancerHealthSummary]:
    health_summaries: list[LoadBalancerHealthSummary] = []
    try:
        client = get_load_balancer_client()
        next_page: Optional[str] = None
        first_page = True
        while first_page or (
            next_page and (limit is None or len(health_summaries) < limit)
        ):
            first_page = False
            page_limit = (
                None if limit is None else max(1, limit - len(health_summaries))
            )
            response: oci.response.Response = client.list_load_balancer_healths(
                compartment_id, limit=page_limit, page=next_page
            )
            items = getattr(response.data, "items", response.data) or []
            remaining = None if limit is None else max(0, limit - len(health_summaries))
            to_process = items if remaining is None else items[:remaining]
            for d in to_process:
                health_summaries.append(map_load_balancer_health_summary(d))
            next_page = getattr(response, "next_page", None)
        logger.info(f"Found {len(health_summaries)} Load Balancer health summaries")
        return health_summaries
    except Exception as e:
        logger.error(f"Error in list_load_balancer_healths tool: {str(e)}")
        raise e


@mcp.tool(
    name="list_load_balancer_work_requests",
    description="List work requests for a given load balancer",
)
def list_load_balancer_work_requests(
    load_balancer_id: str = Field(..., description="The OCID of the load balancer"),
    limit: Optional[int] = Field(
        None,
        description="Maximum number of work requests to return. If None, no limit.",
        ge=1,
    ),
) -> list[WorkRequest]:
    work_requests: list[WorkRequest] = []
    try:
        client = get_load_balancer_client()
        next_page: Optional[str] = None
        first_page = True
        while first_page or (
            next_page and (limit is None or len(work_requests) < limit)
        ):
            first_page = False
            page_limit = None if limit is None else max(1, limit - len(work_requests))
            response: oci.response.Response = client.list_work_requests(
                load_balancer_id, limit=page_limit, page=next_page
            )
            items = getattr(response.data, "items", response.data) or []
            remaining = None if limit is None else max(0, limit - len(work_requests))
            to_process = items if remaining is None else items[:remaining]
            for d in to_process:
                work_requests.append(map_work_request(d))
            next_page = getattr(response, "next_page", None)
        logger.info(f"Found {len(work_requests)} Load Balancer work requests")
        return work_requests
    except Exception as e:
        logger.error(f"Error in list_load_balancer_work_requests tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_load_balancer_work_request",
    description="Get details of a specific load balancer work request",
)
def get_load_balancer_work_request(
    work_request_id: str = Field(..., description="The OCID of the work request")
) -> WorkRequest:
    try:
        client = get_load_balancer_client()
        response: oci.response.Response = client.get_work_request(work_request_id)
        data = response.data
        logger.info("Retrieved Load Balancer work request")
        return map_work_request(data)
    except Exception as e:
        logger.error(f"Error in get_load_balancer_work_request tool: {str(e)}")
        raise e


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
