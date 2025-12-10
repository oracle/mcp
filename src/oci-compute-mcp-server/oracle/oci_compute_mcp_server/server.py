"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Literal, Optional

import oci
from fastmcp import FastMCP
from oracle.oci_compute_mcp_server.consts import (
    DEFAULT_MEMORY_IN_GBS,
    DEFAULT_OCPU_COUNT,
    E5_FLEX,
    ORACLE_LINUX_9_IMAGE,
)
from oracle.oci_compute_mcp_server.models import (
    Image,
    Instance,
    Response,
    VnicAttachment,
    map_image,
    map_instance,
    map_response,
    map_vnic_attachment,
)
from pydantic import Field

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_compute_client():
    logger.info("entering get_compute_client")
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
    return oci.core.ComputeClient(config, signer=signer)


@mcp.tool(description="List Instances in a given compartment")
def list_instances(
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of instances to return. If None, there is no limit.",
        ge=1,
    ),
    lifecycle_state: Optional[
        Literal[
            "MOVING",
            "PROVISIONING",
            "RUNNING",
            "STARTING",
            "STOPPING",
            "STOPPED",
            "CREATING_IMAGE",
            "TERMINATING",
            "TERMINATED",
        ]
    ] = Field(None, description="The lifecycle state of the instance to filter on"),
) -> list[Instance]:
    instances: list[Instance] = []

    try:
        client = get_compute_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(instances) < limit):
            kwargs = {
                "compartment_id": compartment_id,
                "page": next_page,
                "limit": limit,
            }

            if lifecycle_state:
                kwargs["lifecycle_state"] = lifecycle_state

            response = client.list_instances(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.core.models.Instance] = response.data
            for d in data:
                instance = map_instance(d)
                instances.append(instance)

        logger.info(f"Found {len(instances)} Instances")
        return instances

    except Exception as e:
        logger.error(f"Error in list_instances tool: {str(e)}")
        raise e


@mcp.tool(description="Get Instance with a given instance OCID")
def get_instance(
    instance_id: str = Field(..., description="The OCID of the instance")
) -> Instance:
    try:
        client = get_compute_client()

        response: oci.response.Response = client.get_instance(instance_id=instance_id)
        data: oci.core.models.Instance = response.data
        logger.info("Found Instance")
        return map_instance(data)

    except Exception as e:
        logger.error(f"Error in get_instance tool: {str(e)}")
        raise e


@mcp.tool(
    description="Create a new instance. "
    "Another word for instance could be compute, server, or virtual machine"
)
def launch_instance(
    compartment_id: str = Field(
        ...,
        description="This is the ocid of the compartment to create the instance in."
        'Must begin with "ocid". If the user specifies a compartment name, '
        "then you may use the list_compartments tool in order to map the "
        "compartment name to its ocid",
    ),
    display_name: str = Field(
        ...,
        description="The display name of the instance. "
        "If no value is provded, then you can pass in "
        '"instance-<year><month><day>-<hour><minute>" '
        "where those time values come from the current date time",
        min_length=1,
        max_length=255,
    ),
    availability_domain: str = Field(
        ...,
        description="This is the availability domain to create the instance in. "
        'It must be formatted like "<4-digit-tenancy-code>:<ad-string>". '
        'Example: "aNMj:US-ASHBURN-AD-1". '
        "The value changes per tenancy, per region, and per AD number. "
        "To get a list of availability domains, you may use the "
        "list_availability_domains tool to grab the name of the AD. "
        "This tool is the only way to get the tenancy-code for an AD. "
        "If no AD is specified by the user, you may select the first one available.",
    ),
    subnet_id: str = Field(
        ...,
        description="This is the ocid of the subnet to attach to the "
        "primary virtual network interface card (VNIC) of the compute instance. "
        "If no value is provided, you may use the list_subnets tool, "
        "selecting the first subnet in the list and passing its ocid.",
    ),
    image_id: Optional[str] = Field(
        ORACLE_LINUX_9_IMAGE,
        description="This is the ocid of the image for the instance. "
        "If it is left unspecified or if the user specifies an image name, "
        "then you may have to list the images in the root compartment "
        "in order to map the image name to image ocid or display a "
        "list of images for the user to choose from.",
    ),
    shape: Optional[str] = Field(
        E5_FLEX,
        description="This is the name of the shape for the instance",
    ),
    ocpus: Optional[int] = Field(
        DEFAULT_OCPU_COUNT,
        description="The total number of cores in the instances",
    ),
    memory_in_gbs: Optional[float] = Field(
        DEFAULT_MEMORY_IN_GBS,
        description="The total amount of memory in gigabytes to assigned to the instance",
    ),
) -> Instance:
    try:
        client = get_compute_client()

        launch_details = oci.core.models.LaunchInstanceDetails(
            compartment_id=compartment_id,
            display_name=display_name,
            availability_domain=availability_domain,
            shape=shape,
            source_details=oci.core.models.InstanceSourceViaImageDetails(
                image_id=image_id,
            ),
            create_vnic_details=oci.core.models.CreateVnicDetails(subnet_id=subnet_id),
            shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                ocpus=ocpus, memory_in_gbs=memory_in_gbs
            ),
        )

        response: oci.response.Response = client.launch_instance(launch_details)
        data: oci.core.models.Instance = response.data
        logger.info("Launched Instance")
        return map_instance(data)

    except Exception as e:
        logger.error(f"Error in launch_instance tool: {str(e)}")
        raise e


@mcp.tool(description="Delete instance with given instance OCID")
def terminate_instance(
    instance_id: str = Field(..., description="The OCID of the instance")
) -> Response:
    try:
        client = get_compute_client()

        response: oci.response.Response = client.terminate_instance(instance_id)
        logger.info("Deleted Instance")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in delete_vcn tool: {str(e)}")
        raise e


@mcp.tool(
    description="Update instance. This may restart the instance, so warn the user"
)
def update_instance(
    instance_id: str = Field(..., description="The OCID of the instance"),
    ocpus: Optional[int] = Field(
        None,
        description="The total number of cores in the instances",
    ),
    memory_in_gbs: Optional[float] = Field(
        None,
        description="The total amount of memory in gigabytes to assigned to the instance",
    ),
) -> Instance:
    try:
        client = get_compute_client()

        update_instance_details = oci.core.models.UpdateInstanceDetails(
            shape_config=oci.core.models.UpdateInstanceShapeConfigDetails(
                ocpus=ocpus, memory_in_gbs=memory_in_gbs
            ),
        )

        response: oci.response.Response = client.update_instance(
            instance_id=instance_id, update_instance_details=update_instance_details
        )
        data: oci.core.models.Instance = response.data
        logger.info("Updated Instance")
        return map_instance(data)

    except Exception as e:
        logger.error(f"Error in update_instance tool: {str(e)}")
        raise e


@mcp.tool(
    description="List images in a given compartment, "
    "optionally filtered by operating system"
)
def list_images(
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    operating_system: Optional[str] = Field(
        None, description="The operating system to filter with"
    ),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[Image]:
    images: list[Image] = []

    try:
        client = get_compute_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(images) < limit):
            kwargs = {
                "compartment_id": compartment_id,
                "page": next_page,
                "limit": limit,
            }

            response = client.list_images(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.core.models.Image] = response.data
            if operating_system:
                data = [img for img in data if img.operating_system == operating_system]

            for d in data:
                image = map_image(d)
                images.append(image)

        logger.info(f"Found {len(images)} Images")
        return images

    except Exception as e:
        logger.error(f"Error in list_images tool: {str(e)}")
        raise e


@mcp.tool(description="Get Image with a given image OCID")
def get_image(image_id: str = Field(..., description="The OCID of the image")) -> Image:
    try:
        client = get_compute_client()

        response: oci.response.Response = client.get_image(image_id=image_id)
        data: oci.core.models.Image = response.data
        logger.info("Found Image")
        return map_image(data)

    except Exception as e:
        logger.error(f"Error in get_image tool: {str(e)}")
        raise e


@mcp.tool(description="Perform the desired action on a given instance")
def instance_action(
    instance_id: str = Field(..., description="The OCID of the instance"),
    action: Literal[
        "START",
        "STOP",
        "RESET",
        "SOFTSTOP",
        "SOFTRESET",
        "SENDDIAGNOSTICINTERRUPT",
        "DIAGNOSTICREBOOT",
        "REBOOTMIGRATE",
    ] = Field(..., description="The instance action to be performed"),
) -> Instance:
    try:
        client = get_compute_client()

        response: oci.response.Response = client.instance_action(instance_id, action)
        data: oci.core.models.Instance = response.data
        logger.info("Performed instance action")
        return map_instance(data)

    except Exception as e:
        logger.error(f"Error in instance_action tool: {str(e)}")
        raise e


@mcp.tool(
    description="List vnic attachments in a given compartment and/or on a given instance. "
)
def list_vnic_attachments(
    compartment_id: str = Field(
        ...,
        description="The OCID of the compartment. "
        "If an instance_id is passed in, but no compartment_id is passed in,"
        "then the compartment OCID of the instance may be used as a default.",
    ),
    instance_id: Optional[str] = Field(None, description="The OCID of the instance"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[VnicAttachment]:
    vnic_attachments: list[VnicAttachment] = []

    try:
        client = get_compute_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(vnic_attachments) < limit):
            kwargs = {
                "compartment_id": compartment_id,
                "page": next_page,
                "limit": limit,
            }

            if instance_id:
                kwargs["instance_id"] = instance_id

            response = client.list_vnic_attachments(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.core.models.VnicAttachment] = response.data

            for d in data:
                vnic_attachments.append(map_vnic_attachment(d))

        logger.info(f"Found {len(vnic_attachments)} Vnic Attachments")
        return vnic_attachments

    except Exception as e:
        logger.error(f"Error in list_vnic_attachments tool: {str(e)}")
        raise e


@mcp.tool(description="Get Vnic Attachment with a given OCID")
def get_vnic_attachment(
    vnic_attachment_id: str = Field(..., description="The OCID of the vnic attachment")
) -> VnicAttachment:
    try:
        client = get_compute_client()

        response: oci.response.Response = client.get_vnic_attachment(
            vnic_attachment_id=vnic_attachment_id
        )
        data: oci.core.models.VnicAttachment = response.data
        logger.info("Found Vnic Attachment")
        return map_vnic_attachment(data)

    except Exception as e:
        logger.error(f"Error in get_vnic_attachment tool: {str(e)}")
        raise e


def main() -> None:

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
