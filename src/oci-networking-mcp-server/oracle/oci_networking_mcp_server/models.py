"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import oci
from pydantic import BaseModel, Field


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


# region Vcn


class Vcn(BaseModel):
    """
    Pydantic model mirroring the fields of oci.core.models.Vcn.
    This model intentionally includes only the VCN's direct
    fields (no related resources).
    """

    byoipv6_cidr_blocks: Optional[List[str]] = Field(
        None,
        description="The list of BYOIPv6 prefixes required to create a VCN that uses BYOIPv6 ranges.",  # noqa
    )
    ipv6_private_cidr_blocks: Optional[List[str]] = Field(
        None,
        description="For an IPv6-enabled VCN, the list of Private IPv6 prefixes for the VCN's IP address space.",  # noqa
    )
    cidr_block: Optional[str] = Field(
        None,
        description="Deprecated. The first CIDR IP address from cidrBlocks (e.g., 172.16.0.0/16).",  # noqa
    )
    cidr_blocks: Optional[List[str]] = Field(
        None, description="The list of IPv4 CIDR blocks the VCN will use."
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the VCN."
    )
    default_dhcp_options_id: Optional[str] = Field(
        None, description="The OCID for the VCN's default set of DHCP options."
    )
    default_route_table_id: Optional[str] = Field(
        None, description="The OCID for the VCN's default route table."
    )
    default_security_list_id: Optional[str] = Field(
        None, description="The OCID for the VCN's default security list."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource, each key scoped to a namespace.",
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name. Does not have to be unique."
    )
    dns_label: Optional[str] = Field(
        None,
        description="DNS label for the VCN, used to form FQDNs with subnet DNS label and VNIC hostname.",  # noqa
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource as simple key/value pairs."
    )
    security_attributes: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Security attributes for Zero Trust Packet Routing (ZPR), labeled by namespace.",  # noqa
    )
    id: Optional[str] = Field(None, description="The OCID of the VCN.")
    ipv6_cidr_blocks: Optional[List[str]] = Field(
        None,
        description="For an IPv6-enabled VCN, the list of IPv6 prefixes for the VCN's IP space (sizes are /56).",  # noqa
    )
    lifecycle_state: Optional[
        Literal[
            "PROVISIONING",
            "AVAILABLE",
            "TERMINATING",
            "TERMINATED",
            "UPDATING",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The VCN's current state.")
    time_created: Optional[datetime] = Field(
        None, description="The date and time the VCN was created (RFC3339)."
    )
    vcn_domain_name: Optional[str] = Field(
        None,
        description="The VCN's domain name, which consists of the VCN's DNS label and the oraclevcn.com domain.",  # noqa
    )
    is_zpr_only: Optional[bool] = Field(
        None, description="Indicates whether ZPR Only Mode is enforced."
    )


def map_vcn(vcn: oci.core.models.Vcn) -> Vcn | None:
    """
    Convert an oci.core.models.Vcn to oracle.oci_networking_mcp_server.models.Vcn.
    """
    if vcn is None:
        return None

    # lifecycle_state may include unknown enum values; pass through as-is
    return Vcn(
        byoipv6_cidr_blocks=getattr(vcn, "byoipv6_cidr_blocks", None),
        ipv6_private_cidr_blocks=getattr(vcn, "ipv6_private_cidr_blocks", None),
        cidr_block=getattr(vcn, "cidr_block", None),
        cidr_blocks=getattr(vcn, "cidr_blocks", None),
        compartment_id=getattr(vcn, "compartment_id", None),
        default_dhcp_options_id=getattr(vcn, "default_dhcp_options_id", None),
        default_route_table_id=getattr(vcn, "default_route_table_id", None),
        default_security_list_id=getattr(vcn, "default_security_list_id", None),
        defined_tags=getattr(vcn, "defined_tags", None),
        display_name=getattr(vcn, "display_name", None),
        dns_label=getattr(vcn, "dns_label", None),
        freeform_tags=getattr(vcn, "freeform_tags", None),
        security_attributes=getattr(vcn, "security_attributes", None),
        id=getattr(vcn, "id", None),
        ipv6_cidr_blocks=getattr(vcn, "ipv6_cidr_blocks", None),
        lifecycle_state=getattr(vcn, "lifecycle_state", None),
        time_created=getattr(vcn, "time_created", None),
        vcn_domain_name=getattr(vcn, "vcn_domain_name", None),
        is_zpr_only=getattr(vcn, "is_zpr_only", None),
    )


# endregion

# region Subnet


class Subnet(BaseModel):
    """
    Pydantic model mirroring the fields of oci.core.models.Subnet.
    """

    availability_domain: Optional[str] = Field(
        None,
        description="The subnet's availability domain. Null if this is a regional subnet.",  # noqa
    )
    cidr_block: Optional[str] = Field(
        None, description="The IPv4 CIDR block of the subnet."
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the subnet."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",  # noqa
    )
    dhcp_options_id: Optional[str] = Field(
        None, description="The OCID of the set of DHCP options that the subnet uses."
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name. Does not have to be unique."
    )
    dns_label: Optional[str] = Field(
        None,
        description="DNS label for the subnet, used with the VNIC's hostname and the VCN's DNS label to form the FQDN.",  # noqa
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource as simple key/value pairs."
    )
    id: Optional[str] = Field(None, description="The OCID of the subnet.")
    ipv6_cidr_block: Optional[str] = Field(
        None,
        description="For an IPv6-enabled subnet, the IPv6 prefix/CIDR for the subnet's IP address space.",  # noqa
    )
    ipv6_cidr_blocks: Optional[List[str]] = Field(
        None,
        description="All IPv6 prefixes (Oracle allocated GUA/ULA/private or BYOIPv6 prefixes) for the subnet.",  # noqa
    )
    ipv6_virtual_router_ip: Optional[str] = Field(
        None,
        description="For an IPv6-enabled subnet, the IPv6 address of the virtual router.",  # noqa
    )
    lifecycle_state: Optional[
        Literal[
            "PROVISIONING",
            "AVAILABLE",
            "TERMINATING",
            "TERMINATED",
            "UPDATING",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The subnet's current state.")
    prohibit_internet_ingress: Optional[bool] = Field(
        None,
        description="Whether to disallow ingress internet traffic to VNICs within this subnet.",  # noqa
    )
    prohibit_public_ip_on_vnic: Optional[bool] = Field(
        None,
        description="Whether VNICs within this subnet can have public IP addresses.",
    )
    route_table_id: Optional[str] = Field(
        None, description="The OCID of the route table that the subnet uses."
    )
    security_list_ids: Optional[List[str]] = Field(
        None,
        description="The OCIDs of the security list or lists that the subnet uses.",
    )
    subnet_domain_name: Optional[str] = Field(
        None,
        description="The subnet's domain name, composed from the subnet and VCN DNS labels.",  # noqa
    )
    time_created: Optional[datetime] = Field(
        None, description="The date and time the subnet was created (RFC3339)."
    )
    vcn_id: Optional[str] = Field(
        None, description="The OCID of the VCN the subnet is in."
    )
    virtual_router_ip: Optional[str] = Field(
        None, description="The IPv4 address of the virtual router."
    )
    virtual_router_mac: Optional[str] = Field(
        None, description="The MAC address of the virtual router."
    )


def map_subnet(subnet: oci.core.models.Subnet) -> Subnet | None:
    """
    Convert an oci.core.models.Subnet to oracle.oci_networking_mcp_server.models.Subnet.
    """
    if subnet is None:
        return None

    return Subnet(
        availability_domain=getattr(subnet, "availability_domain", None),
        cidr_block=getattr(subnet, "cidr_block", None),
        compartment_id=getattr(subnet, "compartment_id", None),
        defined_tags=getattr(subnet, "defined_tags", None),
        dhcp_options_id=getattr(subnet, "dhcp_options_id", None),
        display_name=getattr(subnet, "display_name", None),
        dns_label=getattr(subnet, "dns_label", None),
        freeform_tags=getattr(subnet, "freeform_tags", None),
        id=getattr(subnet, "id", None),
        ipv6_cidr_block=getattr(subnet, "ipv6_cidr_block", None),
        ipv6_cidr_blocks=getattr(subnet, "ipv6_cidr_blocks", None),
        ipv6_virtual_router_ip=getattr(subnet, "ipv6_virtual_router_ip", None),
        lifecycle_state=getattr(subnet, "lifecycle_state", None),
        prohibit_internet_ingress=getattr(subnet, "prohibit_internet_ingress", None),
        prohibit_public_ip_on_vnic=getattr(subnet, "prohibit_public_ip_on_vnic", None),
        route_table_id=getattr(subnet, "route_table_id", None),
        security_list_ids=getattr(subnet, "security_list_ids", None),
        subnet_domain_name=getattr(subnet, "subnet_domain_name", None),
        time_created=getattr(subnet, "time_created", None),
        vcn_id=getattr(subnet, "vcn_id", None),
        virtual_router_ip=getattr(subnet, "virtual_router_ip", None),
        virtual_router_mac=getattr(subnet, "virtual_router_mac", None),
    )


# endregion

# region SecurityList


class PortRange(BaseModel):
    """
    Pydantic model mirroring oci.core.models.PortRange.
    """

    min: Optional[int] = Field(None, description="The minimum port number, inclusive.")
    max: Optional[int] = Field(None, description="The maximum port number, inclusive.")


class IcmpOptions(BaseModel):
    """
    Pydantic model mirroring oci.core.models.IcmpOptions.
    """

    type: Optional[int] = Field(None, description="The ICMP type.")
    code: Optional[int] = Field(None, description="The ICMP code.")


class TcpOptions(BaseModel):
    """
    Pydantic model mirroring oci.core.models.TcpOptions.
    Supports both singular and list-based port range fields.
    """

    destination_port_range: Optional[PortRange] = Field(
        None, description="Single destination port range."
    )
    source_port_range: Optional[PortRange] = Field(
        None, description="Single source port range."
    )
    destination_port_ranges: Optional[List[PortRange]] = Field(
        None, description="List of destination port ranges."
    )
    source_port_ranges: Optional[List[PortRange]] = Field(
        None, description="List of source port ranges."
    )


class UdpOptions(BaseModel):
    """
    Pydantic model mirroring oci.core.models.UdpOptions.
    Supports both singular and list-based port range fields.
    """

    destination_port_range: Optional[PortRange] = Field(
        None, description="Single destination port range."
    )
    source_port_range: Optional[PortRange] = Field(
        None, description="Single source port range."
    )
    destination_port_ranges: Optional[List[PortRange]] = Field(
        None, description="List of destination port ranges."
    )
    source_port_ranges: Optional[List[PortRange]] = Field(
        None, description="List of source port ranges."
    )


class EgressSecurityRule(BaseModel):
    """
    Pydantic model mirroring oci.core.models.EgressSecurityRule.
    """

    description: Optional[str] = Field(
        None, description="An optional description of the rule."
    )
    destination: Optional[str] = Field(
        None, description="The destination CIDR block or service CIDR."
    )
    destination_type: Optional[
        Literal[
            "CIDR_BLOCK",
            "SERVICE_CIDR_BLOCK",
            "NETWORK_SECURITY_GROUP",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The type of destination target.")
    icmp_options: Optional[IcmpOptions] = Field(
        None,
        description="ICMP options. Required if protocol is ICMP and using ICMP type/code.",  # noqa
    )
    is_stateless: Optional[bool] = Field(
        None, description="A stateless rule does not keep track of traffic state."
    )
    protocol: Optional[str] = Field(
        None,
        description="The transport protocol. Specify either all or the protocol number.",  # noqa
    )
    tcp_options: Optional[TcpOptions] = Field(
        None,
        description="TCP options. Required if protocol is TCP and destination/source port range must be specified.",  # noqa
    )
    udp_options: Optional[UdpOptions] = Field(
        None,
        description="UDP options. Required if protocol is UDP and destination/source port range must be specified.",  # noqa
    )


class IngressSecurityRule(BaseModel):
    """
    Pydantic model mirroring oci.core.models.IngressSecurityRule.
    """

    description: Optional[str] = Field(
        None, description="An optional description of the rule."
    )
    icmp_options: Optional[IcmpOptions] = Field(
        None,
        description="ICMP options. Required if protocol is ICMP and using ICMP type/code.",  # noqa
    )
    is_stateless: Optional[bool] = Field(
        None, description="A stateless rule does not keep track of traffic state."
    )
    protocol: Optional[str] = Field(
        None,
        description="The transport protocol. Specify either all or the protocol number.",  # noqa
    )
    source: Optional[str] = Field(
        None, description="The source CIDR block or service CIDR."
    )
    source_type: Optional[
        Literal[
            "CIDR_BLOCK",
            "SERVICE_CIDR_BLOCK",
            "NETWORK_SECURITY_GROUP",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The type of source target.")
    tcp_options: Optional[TcpOptions] = Field(
        None,
        description="TCP options. Required if protocol is TCP and destination/source port range must be specified.",  # noqa
    )
    udp_options: Optional[UdpOptions] = Field(
        None,
        description="UDP options. Required if protocol is UDP and destination/source port range must be specified.",  # noqa
    )


class SecurityList(BaseModel):
    """
    Pydantic model mirroring the fields of oci.core.models.SecurityList.
    """

    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the security list."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",  # noqa
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name. Does not have to be unique."
    )
    egress_security_rules: Optional[List[EgressSecurityRule]] = Field(
        None, description="Rules for allowing egress IP packets."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource as simple key/value pairs."
    )
    id: Optional[str] = Field(None, description="The OCID of the security list.")
    ingress_security_rules: Optional[List[IngressSecurityRule]] = Field(
        None, description="Rules for allowing ingress IP packets."
    )
    lifecycle_state: Optional[
        Literal[
            "PROVISIONING",
            "AVAILABLE",
            "TERMINATING",
            "TERMINATED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The security list's current state.")
    time_created: Optional[datetime] = Field(
        None, description="The date and time the security list was created (RFC3339)."
    )
    vcn_id: Optional[str] = Field(
        None, description="The OCID of the VCN the security list belongs to."
    )


def map_port_range(pr) -> PortRange | None:
    if not pr:
        return None
    data = _oci_to_dict(pr) or {}
    return PortRange(
        min=getattr(pr, "min", None) or data.get("min"),
        max=getattr(pr, "max", None) or data.get("max"),
    )


def _map_port_ranges(items) -> list[PortRange] | None:
    if not items:
        return None
    result: list[PortRange] = []
    for it in items:
        result.append(map_port_range(it))
    return result


def map_icmp_options(icmp) -> IcmpOptions | None:
    if not icmp:
        return None
    data = _oci_to_dict(icmp) or {}
    return IcmpOptions(
        type=getattr(icmp, "type", None) or data.get("type"),
        code=getattr(icmp, "code", None) or data.get("code"),
    )


def map_tcp_options(tcp) -> TcpOptions | None:
    if not tcp:
        return None
    data = _oci_to_dict(tcp) or {}
    dest_range = getattr(tcp, "destination_port_range", None) or data.get(
        "destination_port_range"
    )
    src_range = getattr(tcp, "source_port_range", None) or data.get("source_port_range")
    dest_ranges = getattr(tcp, "destination_port_ranges", None) or data.get(
        "destination_port_ranges"
    )
    src_ranges = getattr(tcp, "source_port_ranges", None) or data.get(
        "source_port_ranges"
    )
    return TcpOptions(
        destination_port_range=map_port_range(dest_range),
        source_port_range=map_port_range(src_range),
        destination_port_ranges=_map_port_ranges(dest_ranges),
        source_port_ranges=_map_port_ranges(src_ranges),
    )


def map_udp_options(udp) -> UdpOptions | None:
    if not udp:
        return None
    data = _oci_to_dict(udp) or {}
    dest_range = getattr(udp, "destination_port_range", None) or data.get(
        "destination_port_range"
    )
    src_range = getattr(udp, "source_port_range", None) or data.get("source_port_range")
    dest_ranges = getattr(udp, "destination_port_ranges", None) or data.get(
        "destination_port_ranges"
    )
    src_ranges = getattr(udp, "source_port_ranges", None) or data.get(
        "source_port_ranges"
    )
    return UdpOptions(
        destination_port_range=map_port_range(dest_range),
        source_port_range=map_port_range(src_range),
        destination_port_ranges=_map_port_ranges(dest_ranges),
        source_port_ranges=_map_port_ranges(src_ranges),
    )


def map_egress_security_rule(rule) -> EgressSecurityRule | None:
    if not rule:
        return None
    data = _oci_to_dict(rule) or {}
    return EgressSecurityRule(
        description=getattr(rule, "description", None) or data.get("description"),
        destination=getattr(rule, "destination", None) or data.get("destination"),
        destination_type=getattr(rule, "destination_type", None)
        or data.get("destination_type"),
        icmp_options=map_icmp_options(
            getattr(rule, "icmp_options", None) or data.get("icmp_options")
        ),
        is_stateless=getattr(rule, "is_stateless", None) or data.get("is_stateless"),
        protocol=getattr(rule, "protocol", None) or data.get("protocol"),
        tcp_options=map_tcp_options(
            getattr(rule, "tcp_options", None) or data.get("tcp_options")
        ),
        udp_options=map_udp_options(
            getattr(rule, "udp_options", None) or data.get("udp_options")
        ),
    )


def map_ingress_security_rule(rule) -> IngressSecurityRule | None:
    if not rule:
        return None
    data = _oci_to_dict(rule) or {}
    return IngressSecurityRule(
        description=getattr(rule, "description", None) or data.get("description"),
        icmp_options=map_icmp_options(
            getattr(rule, "icmp_options", None) or data.get("icmp_options")
        ),
        is_stateless=getattr(rule, "is_stateless", None) or data.get("is_stateless"),
        protocol=getattr(rule, "protocol", None) or data.get("protocol"),
        source=getattr(rule, "source", None) or data.get("source"),
        source_type=getattr(rule, "source_type", None) or data.get("source_type"),
        tcp_options=map_tcp_options(
            getattr(rule, "tcp_options", None) or data.get("tcp_options")
        ),
        udp_options=map_udp_options(
            getattr(rule, "udp_options", None) or data.get("udp_options")
        ),
    )


def map_security_list(
    sl: oci.core.models.SecurityList,
) -> SecurityList | None:
    """
    Convert an oci.core.models.SecurityList to
    oracle.oci_networking_mcp_server.models.SecurityList,
    including all nested rule and option types.
    """
    if sl is None:
        return None

    egress_rules = getattr(sl, "egress_security_rules", None)
    ingress_rules = getattr(sl, "ingress_security_rules", None)

    return SecurityList(
        compartment_id=getattr(sl, "compartment_id", None),
        defined_tags=getattr(sl, "defined_tags", None),
        display_name=getattr(sl, "display_name", None),
        egress_security_rules=(
            [map_egress_security_rule(r) for r in (egress_rules or [])]
            if egress_rules is not None
            else None
        ),
        freeform_tags=getattr(sl, "freeform_tags", None),
        id=getattr(sl, "id", None),
        ingress_security_rules=(
            [map_ingress_security_rule(r) for r in (ingress_rules or [])]
            if ingress_rules is not None
            else None
        ),
        lifecycle_state=getattr(sl, "lifecycle_state", None),
        time_created=getattr(sl, "time_created", None),
        vcn_id=getattr(sl, "vcn_id", None),
    )


# endregion

# region NetworkSecurityGroup


class NetworkSecurityGroup(BaseModel):
    """
    Pydantic model mirroring the fields of oci.core.models.NetworkSecurityGroup.
    """

    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment containing the network security group.",  # noqa
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",  # noqa
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name. Does not have to be unique."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource as simple key/value pairs."
    )
    id: Optional[str] = Field(
        None, description="The OCID of the network security group."
    )
    lifecycle_state: Optional[
        Literal[
            "PROVISIONING",
            "AVAILABLE",
            "TERMINATING",
            "TERMINATED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The network security group's current state.")
    time_created: Optional[datetime] = Field(
        None,
        description="The date and time the network security group was created (RFC3339).",  # noqa
    )
    vcn_id: Optional[str] = Field(
        None, description="The OCID of the VCN the network security group belongs to."
    )


def map_network_security_group(
    nsg: oci.core.models.NetworkSecurityGroup,
) -> NetworkSecurityGroup | None:
    """
    Convert an oci.core.models.NetworkSecurityGroup to
    oracle.oci_networking_mcp_server.models.NetworkSecurityGroup.
    """
    if nsg is None:
        return None

    return NetworkSecurityGroup(
        compartment_id=getattr(nsg, "compartment_id", None),
        defined_tags=getattr(nsg, "defined_tags", None),
        display_name=getattr(nsg, "display_name", None),
        freeform_tags=getattr(nsg, "freeform_tags", None),
        id=getattr(nsg, "id", None),
        lifecycle_state=getattr(nsg, "lifecycle_state", None),
        time_created=getattr(nsg, "time_created", None),
        vcn_id=getattr(nsg, "vcn_id", None),
    )


# endregion

# region Response (oci.response.Response)


class Request(BaseModel):
    """
    Pydantic model mirroring the fields of oci.request.Request.
    """

    method: Optional[str] = Field(None, description="The HTTP method.")
    url: Optional[str] = Field(None, description="URL that will serve the request.")
    query_params: Optional[Dict[str, Any]] = Field(
        None, description="Query parameters in the URL."
    )
    header_params: Optional[Dict[str, Any]] = Field(
        None, description="Request header parameters."
    )
    body: Optional[Any] = Field(None, description="Request body.")
    response_type: Optional[str] = Field(
        None, description="Expected response data type."
    )
    enforce_content_headers: Optional[bool] = Field(
        None,
        description=(
            "Whether content headers should be added for PUT and POST requests when not present."  # noqa
        ),
    )


class Response(BaseModel):
    """
    Pydantic model mirroring the fields of oci.response.Response.
    Includes derived fields next_page, request_id, and has_next_page.
    """

    status: Optional[int] = Field(None, description="The HTTP status code.")
    headers: Optional[Dict[str, Any]] = Field(
        None, description="The HTTP headers (case-insensitive keys)."
    )
    data: Optional[Any] = Field(
        None, description="The response data. Type depends on the request."
    )
    request: Optional[Request] = Field(
        None, description="The corresponding request for this response."
    )
    next_page: Optional[str] = Field(
        None, description="The value of the opc-next-page response header."
    )
    request_id: Optional[str] = Field(
        None, description="The ID of the request that generated this response."
    )
    has_next_page: Optional[bool] = Field(
        None, description="Whether there is a next page of results."
    )


def map_request(req) -> Request | None:
    """
    Convert an oci.request.Request to oracle.oci_networking_mcp_server.models.Request.
    """
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


def _map_headers(headers) -> Dict[str, Any] | None:
    if headers is None:
        return None
    try:
        # requests.structures.CaseInsensitiveDict is convertible to dict
        return dict(headers)
    except Exception:
        try:
            return {k: v for k, v in headers.items()}
        except Exception:
            return _oci_to_dict(headers) or None


def _map_response_data(data: Any) -> Any:
    """
    Best-effort mapping of Response.data to Pydantic-friendly structures.
    Recognizes common networking models; otherwise falls back to to_dict.
    """
    # Handle sequences
    if isinstance(data, (list, tuple)):
        return [_map_response_data(x) for x in data]

    # Already a plain type
    if data is None or isinstance(data, (str, int, float, bool)):
        return data
    if isinstance(data, dict):
        return data

    # Known OCI networking models
    try:
        if isinstance(data, oci.core.models.Vcn):
            return map_vcn(data)
        if isinstance(data, oci.core.models.Subnet):
            return map_subnet(data)
        if isinstance(data, oci.core.models.SecurityList):
            return map_security_list(data)
        if isinstance(data, oci.core.models.NetworkSecurityGroup):
            return map_network_security_group(data)
        if isinstance(data, oci.core.models.Vnic):
            return map_vnic(data)
    except Exception:
        # Ignore import/type detection issues and fall through to generic handling
        pass

    # Fallback: attempt to convert OCI SDK models or other objects to dict
    coerced = _oci_to_dict(data)
    return coerced if coerced is not None else data


def map_response(resp: oci.response.Response) -> Response | None:
    """
    Convert oci.response.Response to oracle.oci_networking_mcp_server.models.Response,
    including nested Request and best-effort mapping of data.
    """
    if resp is None:
        return None

    headers = _map_headers(getattr(resp, "headers", None))
    next_page = getattr(resp, "next_page", None)
    request_id = getattr(resp, "request_id", None)

    # Derive from headers if not already present
    if next_page is None and headers is not None:
        next_page = headers.get("opc-next-page")
    if request_id is None and headers is not None:
        request_id = headers.get("opc-request-id")

    return Response(
        status=getattr(resp, "status", None),
        headers=headers,
        data=_map_response_data(getattr(resp, "data", None)),
        request=map_request(getattr(resp, "request", None)),
        next_page=next_page,
        request_id=request_id,
        has_next_page=(next_page is not None),
    )


# endregion

# region Vnic


class Vnic(BaseModel):
    """
    Pydantic model mirroring the fields of oci.core.models.Vnic.
    """

    availability_domain: Optional[str] = Field(
        None, description="The VNIC's availability domain. Example: `Uocm:PHX-AD-1`"
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the VNIC."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description=(
            "Defined tags for this resource. Each key is predefined and scoped to a "
            'namespace. Example: `{"Operations": {"CostCenter": "42"}}`',
        ),
    )
    display_name: Optional[str] = Field(
        None,
        description="A user-friendly name. Does not have to be unique, and it's changeable. "
        "Avoid entering confidential information.",
    )
    security_attributes: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Security attributes for Zero Trust Packet Routing (ZPR), labeled by namespace. "
        'Example: `{"Oracle-DataSecurity-ZPR": {"MaxEgressCount": {"value":"42","mode":"audit"}}}`',
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "Free-form tags for this resource. Each tag is a simple key-value pair with no "
            'predefined name, type, or namespace. Example: `{"Department": "Finance"}`',
        ),
    )
    hostname_label: Optional[str] = Field(
        None,
        description=(
            "The hostname for the VNIC's primary private IP. Used for DNS. The value is the "
            "hostname portion of the primary private IP's fully qualified domain name (FQDN) "
            "(for example, `bminstance1` in FQDN `bminstance1.subnet123.vcn1.oraclevcn.com`). "
            "Must be unique across all VNICs in the subnet and comply with RFC 952 and RFC 1123. "
            "Example: `bminstance1`",
        ),
    )
    id: Optional[str] = Field(None, description="The OCID of the VNIC.")
    is_primary: Optional[bool] = Field(
        None,
        description="Whether the VNIC is the primary VNIC "
        "(the VNIC that is automatically created and attached during instance launch).",
    )
    lifecycle_state: Optional[
        Literal[
            "PROVISIONING",
            "AVAILABLE",
            "TERMINATING",
            "TERMINATED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The current state of the VNIC.")
    mac_address: Optional[str] = Field(
        None,
        description=(
            "The MAC address of the VNIC. If the VNIC belongs to a VLAN as part of the Oracle "
            "Cloud VMware Solution, the MAC address is learned. If the VNIC belongs to a subnet, "
            "the MAC address is a static, Oracle-provided value. Example: `00:00:00:00:00:01`",
        ),
    )
    nsg_ids: Optional[List[str]] = Field(
        None,
        description=(
            "A list of the OCIDs of the network security groups that the VNIC belongs to. "
            "If the VNIC belongs to a VLAN as part of the Oracle Cloud VMware Solution "
            "(instead of belonging to a subnet), the value of the `nsgIds` attribute is ignored. "
            "Instead, the VNIC belongs to the NSGs that are associated with the VLAN itself. "
            "See Vlan.",
        ),
    )
    vlan_id: Optional[str] = Field(
        None,
        description="If the VNIC belongs to a VLAN as part of the Oracle Cloud VMware Solution "
        "(instead of belonging to a subnet), the `vlanId` is the OCID of the VLAN the VNIC is in. "
        "See Vlan. If the VNIC is instead in a subnet, `subnetId` has a value.",
    )
    private_ip: Optional[str] = Field(
        None,
        description="The private IP address of the primary `privateIp` object on the VNIC. "
        "The address is within the CIDR of the VNIC's subnet. Example: `10.0.3.3`",
    )
    public_ip: Optional[str] = Field(
        None, description="The public IP address of the VNIC, if one is assigned."
    )
    skip_source_dest_check: Optional[bool] = Field(
        None,
        description=(
            "Whether the source/destination check is disabled on the VNIC. Defaults to `false`, "
            "which means the check is performed. For information about why you would skip the "
            "source/destination check, see Using a Private IP as a Route Target. "
            "If the VNIC belongs to a VLAN as part of the Oracle Cloud VMware Solution "
            "(instead of belonging to a subnet), the `skipSourceDestCheck` attribute is `true`. "
            "This is because the source/destination check is always disabled for VNICs in a VLAN. "
            "Example: `true`",
        ),
    )
    subnet_id: Optional[str] = Field(
        None, description="The OCID of the subnet the VNIC is in."
    )
    time_created: Optional[datetime] = Field(
        None,
        description=(
            "The date and time the VNIC was created, in the format defined by RFC3339. "
            "Example: `2016-08-25T21:10:29.600Z`",
        ),
    )
    ipv6_addresses: Optional[List[str]] = Field(
        None,
        description="List of IPv6 addresses assigned to the VNIC. Example: `2001:DB8::`",
    )
    route_table_id: Optional[str] = Field(
        None,
        description="The OCID of the route table the IP address or VNIC will use. "
        "For more information, see Per-resource Routing.",
    )


def map_vnic(vnic: oci.core.models.Vnic) -> Vnic | None:
    """
    Convert an oci.core.models.Vnic to oracle.oci_networking_mcp_server.models.Vnic.
    """
    if vnic is None:
        return None

    return Vnic(
        availability_domain=getattr(vnic, "availability_domain", None),
        compartment_id=getattr(vnic, "compartment_id", None),
        defined_tags=getattr(vnic, "defined_tags", None),
        display_name=getattr(vnic, "display_name", None),
        security_attributes=getattr(vnic, "security_attributes", None),
        freeform_tags=getattr(vnic, "freeform_tags", None),
        hostname_label=getattr(vnic, "hostname_label", None),
        id=getattr(vnic, "id", None),
        is_primary=getattr(vnic, "is_primary", None),
        lifecycle_state=getattr(vnic, "lifecycle_state", None),
        mac_address=getattr(vnic, "mac_address", None),
        nsg_ids=getattr(vnic, "nsg_ids", None),
        vlan_id=getattr(vnic, "vlan_id", None),
        private_ip=getattr(vnic, "private_ip", None),
        public_ip=getattr(vnic, "public_ip", None),
        skip_source_dest_check=getattr(vnic, "skip_source_dest_check", None),
        subnet_id=getattr(vnic, "subnet_id", None),
        time_created=getattr(vnic, "time_created", None),
        ipv6_addresses=getattr(vnic, "ipv6_addresses", None),
        route_table_id=getattr(vnic, "route_table_id", None),
    )


# endregion
