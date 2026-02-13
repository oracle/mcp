"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Optional

import oci
from fastmcp import FastMCP
from oracle.mcp_common import with_oci_client
from oracle.oci_networking_mcp_server.models import (
    NetworkSecurityGroup,
    Response,
    SecurityList,
    Subnet,
    Vcn,
    Vnic,
    map_network_security_group,
    map_response,
    map_security_list,
    map_subnet,
    map_vcn,
    map_vnic,
)
from pydantic import Field

from . import __project__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


@mcp.tool
@with_oci_client(oci.core.VirtualNetworkClient)
def list_vcns(
    compartment_id: str = Field(
        ..., description="The OCID of the compartment containing the VCNs"
    ),
    *,
    client: oci.core.VirtualNetworkClient,
) -> list[Vcn]:
    vcns: list[Vcn] = []

    try:
        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page:
            response = client.list_vcns(compartment_id=compartment_id, page=next_page)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.core.models.Vcn] = response.data
            for d in data:
                vcn = map_vcn(d)
                vcns.append(vcn)

        logger.info(f"Found {len(vcns)} Vcns")
        return vcns

    except Exception as e:
        logger.error(f"Error in list_vcns tool: {str(e)}")
        raise


@mcp.tool
@with_oci_client(oci.core.VirtualNetworkClient)
def get_vcn(
    vcn_id: str = Field(..., description="The OCID of the VCN to retrieve"),
    *,
    client: oci.core.VirtualNetworkClient,
) -> Vcn:
    try:
        response: oci.response.Response = client.get_vcn(vcn_id)
        data: oci.core.models.Vcn = response.data
        logger.info("Found Vcn")
        return map_vcn(data)

    except Exception as e:
        logger.error(f"Error in get_vcn tool: {str(e)}")
        raise


@mcp.tool
@with_oci_client(oci.core.VirtualNetworkClient)
def delete_vcn(
    vcn_id: str = Field(..., description="The OCID of the VCN to delete"),
    *,
    client: oci.core.VirtualNetworkClient,
) -> Response:
    try:
        response: oci.response.Response = client.delete_vcn(vcn_id)
        logger.info("Deleted Vcn")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in delete_vcn tool: {str(e)}")
        raise


@mcp.tool
@with_oci_client(oci.core.VirtualNetworkClient)
def create_vcn(
    compartment_id: str = Field(
        ..., description="The OCID of the compartment where the VCN will be created"
    ),
    cidr_block: str = Field(..., description="The IPv4 CIDR block for the VCN"),
    display_name: str = Field(..., description="A user-friendly display name"),
    *,
    client: oci.core.VirtualNetworkClient,
) -> Vcn:
    try:
        vcn_details = oci.core.models.CreateVcnDetails(
            compartment_id=compartment_id,
            cidr_block=cidr_block,
            display_name=display_name,
        )

        response: oci.response.Response = client.create_vcn(vcn_details)
        data: oci.core.models.Vcn = response.data
        logger.info("Created Vcn")
        return map_vcn(data)

    except Exception as e:
        logger.error(f"Error in create_vcn tool: {str(e)}")
        raise


@mcp.tool
@with_oci_client(oci.core.VirtualNetworkClient)
def list_subnets(
    compartment_id: str = Field(
        ..., description="The OCID of the compartment containing the subnets"
    ),
    vcn_id: Optional[str] = Field(
        None, description="Optional VCN OCID used to filter subnets"
    ),
    *,
    client: oci.core.VirtualNetworkClient,
) -> list[Subnet]:
    subnets: list[Subnet] = []

    try:
        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page:
            response = client.list_subnets(
                compartment_id=compartment_id, vcn_id=vcn_id, page=next_page
            )
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.core.models.Subnet] = response.data
            for d in data:
                subnet = map_subnet(d)
                subnets.append(subnet)

        logger.info(f"Found {len(subnets)} Subnets")
        return subnets

    except Exception as e:
        logger.error(f"Error in list_subnets tool: {str(e)}")
        raise


@mcp.tool
@with_oci_client(oci.core.VirtualNetworkClient)
def get_subnet(
    subnet_id: str = Field(..., description="The OCID of the subnet to retrieve"),
    *,
    client: oci.core.VirtualNetworkClient,
) -> Subnet:
    try:
        response: oci.response.Response = client.get_subnet(subnet_id)
        data: oci.core.models.Subnet = response.data
        logger.info("Found Subnet")
        return map_subnet(data)

    except Exception as e:
        logger.error(f"Error in get_subnet tool: {str(e)}")
        raise


@mcp.tool
@with_oci_client(oci.core.VirtualNetworkClient)
def create_subnet(
    vcn_id: str = Field(..., description="The OCID of the VCN for the subnet"),
    compartment_id: str = Field(
        ..., description="The OCID of the compartment for the subnet"
    ),
    cidr_block: str = Field(..., description="The IPv4 CIDR block for the subnet"),
    display_name: str = Field(..., description="A user-friendly display name"),
    *,
    client: oci.core.VirtualNetworkClient,
) -> Subnet:
    try:
        subnet_details = oci.core.models.CreateSubnetDetails(
            compartment_id=compartment_id,
            vcn_id=vcn_id,
            cidr_block=cidr_block,
            display_name=display_name,
        )

        response: oci.response.Response = client.create_subnet(subnet_details)
        data: oci.core.models.Vcn = response.data
        logger.info("Created Subnet")
        return map_subnet(data)

    except Exception as e:
        logger.error(f"Error in create_subnet tool: {str(e)}")
        raise


@mcp.tool(
    name="list_security_lists",
    description="Lists the security lists in the specified VCN and compartment. "
    "If the VCN ID is not provided, then the list includes the security lists from all "
    "VCNs in the specified compartment.",
)
@with_oci_client(oci.core.VirtualNetworkClient)
def list_security_lists(
    compartment_id: str = Field(
        ..., description="The OCID of the compartment containing the security lists"
    ),
    vcn_id: Optional[str] = Field(
        None, description="Optional VCN OCID to limit the results"
    ),
    *,
    client: oci.core.VirtualNetworkClient,
) -> list[SecurityList]:
    security_lists: list[SecurityList] = []

    try:
        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page:
            response = client.list_security_lists(
                compartment_id=compartment_id, vcn_id=vcn_id, page=next_page
            )
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.core.models.SecurityList] = response.data
            for d in data:
                security_list = map_security_list(d)
                security_lists.append(security_list)

        logger.info(f"Found {len(security_lists)} Security Lists")
        return security_lists

    except Exception as e:
        logger.error(f"Error in list_security_lists tool: {str(e)}")
        raise


@mcp.tool(name="get_security_list", description="Gets the security list's information.")
@with_oci_client(oci.core.VirtualNetworkClient)
def get_security_list(
    security_list_id: str = Field(..., description="The OCID of the security list"),
    *,
    client: oci.core.VirtualNetworkClient,
):
    try:
        response: oci.response.Response = client.get_security_list(security_list_id)
        data: oci.core.models.Subnet = response.data
        logger.info("Found Security List")
        return map_security_list(data)

    except Exception as e:
        logger.error(f"Error in get_security_list tool: {str(e)}")
        raise


@mcp.tool(
    description="Lists either the network security groups in the specified compartment,"
    "or those associated with the specified VLAN. You must specify either a vlanId or"
    "a compartmentId, but not both. If you specify a vlanId, all other parameters are "
    "ignored.",
)
@with_oci_client(oci.core.VirtualNetworkClient)
def list_network_security_groups(
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the NSGs"
    ),
    vlan_id: Optional[str] = Field(
        None, description="Optional VLAN OCID to filter the results"
    ),
    vcn_id: Optional[str] = Field(
        None, description="Optional VCN OCID to filter the results"
    ),
    *,
    client: oci.core.VirtualNetworkClient,
) -> list[NetworkSecurityGroup]:
    nsgs: list[NetworkSecurityGroup] = []

    try:
        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page:
            response = client.list_network_security_groups(
                compartment_id=compartment_id,
                vlan_id=vlan_id,
                vcn_id=vcn_id,
                page=next_page,
            )
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.core.models.NetworkSecurityGroup] = response.data
            for d in data:
                nsg = map_network_security_group(d)
                nsgs.append(nsg)

        logger.info(f"Found {len(nsgs)} Network Security Groups")
        return nsgs

    except Exception as e:
        logger.error(f"Error in list_network_security_groups tool: {str(e)}")
        raise


@mcp.tool(
    description="Gets the specified network security group's information.",
)
@with_oci_client(oci.core.VirtualNetworkClient)
def get_network_security_group(
    network_security_group_id: str = Field(
        ..., description="The OCID of the network security group"
    ),
    *,
    client: oci.core.VirtualNetworkClient,
):
    try:
        response: oci.response.Response = client.get_network_security_group(
            network_security_group_id
        )
        data: oci.core.models.Subnet = response.data
        logger.info("Found Network Security Group")
        return map_network_security_group(data)

    except Exception as e:
        logger.error(f"Error in get_network_security_group tool: {str(e)}")
        raise


@mcp.tool(description="Get Vnic with a given OCID")
@with_oci_client(oci.core.VirtualNetworkClient)
def get_vnic(
    vnic_id: str = Field(..., description="The OCID of the VNIC"),
    *,
    client: oci.core.VirtualNetworkClient,
) -> Vnic:
    try:
        response: oci.response.Response = client.get_vnic(vnic_id=vnic_id)
        data: oci.core.models.Vnic = response.data
        logger.info("Found Vnic")
        return map_vnic(data)

    except Exception as e:
        logger.error(f"Error in get_vnic tool: {str(e)}")
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
