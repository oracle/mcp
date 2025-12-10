"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Annotated

import oci
from fastmcp import FastMCP
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

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_networking_client():
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    token = None
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.core.VirtualNetworkClient(config, signer=signer)


@mcp.tool
def list_vcns(compartment_id: str) -> list[Vcn]:
    vcns: list[Vcn] = []

    try:
        client = get_networking_client()

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
def get_vcn(vcn_id: str) -> Vcn:
    try:
        client = get_networking_client()

        response: oci.response.Response = client.get_vcn(vcn_id)
        data: oci.core.models.Vcn = response.data
        logger.info("Found Vcn")
        return map_vcn(data)

    except Exception as e:
        logger.error(f"Error in get_vcn tool: {str(e)}")
        raise


@mcp.tool
def delete_vcn(vcn_id: str) -> Response:
    try:
        client = get_networking_client()

        response: oci.response.Response = client.delete_vcn(vcn_id)
        logger.info("Deleted Vcn")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in delete_vcn tool: {str(e)}")
        raise


@mcp.tool
def create_vcn(compartment_id: str, cidr_block: str, display_name: str) -> Vcn:
    try:
        client = get_networking_client()

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
def list_subnets(compartment_id: str, vcn_id: str = None) -> list[Subnet]:
    subnets: list[Subnet] = []

    try:
        client = get_networking_client()

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
def get_subnet(subnet_id: str) -> Subnet:
    try:
        client = get_networking_client()

        response: oci.response.Response = client.get_subnet(subnet_id)
        data: oci.core.models.Subnet = response.data
        logger.info("Found Subnet")
        return map_subnet(data)

    except Exception as e:
        logger.error(f"Error in get_subnet tool: {str(e)}")
        raise


@mcp.tool
def create_subnet(
    vcn_id: str, compartment_id: str, cidr_block: str, display_name: str
) -> Subnet:
    try:
        client = get_networking_client()

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
def list_security_lists(
    compartment_id: Annotated[str, "Compartment ocid"],
    vcn_id: Annotated[str, "VCN ocid"] = None,
) -> list[SecurityList]:
    security_lists: list[SecurityList] = []

    try:
        client = get_networking_client()

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
def get_security_list(security_list_id: Annotated[str, "security list id"]):
    try:
        client = get_networking_client()

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
def list_network_security_groups(
    compartment_id: Annotated[str, "compartment ocid"],
    vlan_id: Annotated[str, "vlan ocid"] = None,
    vcn_id: Annotated[str, "vcn ocid"] = None,
) -> list[NetworkSecurityGroup]:
    nsgs: list[NetworkSecurityGroup] = []

    try:
        client = get_networking_client()

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
def get_network_security_group(
    network_security_group_id: Annotated[str, "nsg id"],
):
    try:
        client = get_networking_client()

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
def get_vnic(vnic_id: str = Field(..., description="The OCID of the vnic")) -> Vnic:
    try:
        client = get_networking_client()

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
