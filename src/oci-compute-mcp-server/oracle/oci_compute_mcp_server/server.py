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
from oracle.oci_compute_mcp_server.models import (
    Image,
    Instance,
    Response,
    map_image,
    map_instance,
    map_response,
)

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
    compartment_id: Annotated[str, "The OCID of the compartment"],
    limit: Annotated[
        int,
        "The maximum amount of instances to return. If None, there is no limit. "
        "If the value is not None, then it must be a positive number greater than 0.",
    ] = None,
    lifecycle_state: Annotated[
        str,
        "The lifecycle state of the instance to filter on. The values can be: "
        "'MOVING', 'PROVISIONING', 'RUNNING', 'STARTING', 'STOPPING', 'STOPPED', "
        "'CREATING_IMAGE', 'TERMINATING', 'TERMINATED'",
    ] = None,
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

            if lifecycle_state is not None:
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
def get_instance(instance_id: str) -> Instance:
    try:
        client = get_compute_client()

        response: oci.response.Response = client.get_instance(instance_id=instance_id)
        data: oci.core.models.Instance = response.data
        logger.info("Found Instance")
        return map_instance(data)

    except Exception as e:
        logger.error(f"Error in get_instance tool: {str(e)}")
        raise


ORACLE_LINUX_9_IMAGE = (
    "ocid1.image.oc1.iad.aaaaaaaa4l64brs5udx52nedrhlex4cpaorcd2jwvpoududksmw4lgmameqq"
)
E5_FLEX = "VM.Standard.E5.Flex"
DEFAULT_OCPU_COUNT = 1
DEFAULT_MEMORY_IN_GBS = 12


@mcp.tool(
    description="Create a new instance. "
    "Another word for instance could be compute, server, or virtual machine"
)
def launch_instance(
    compartment_id: Annotated[
        str,
        "This is the ocid of the compartment to create the instance in."
        'Must begin with "ocid". If the user specifies a compartment name, '
        "then you may use the list_compartments tool in order to map the "
        "compartment name to its ocid",
    ],
    display_name: Annotated[
        str,
        "The display name of the instance. "
        "Must be between 1 and 255 characters in length. "
        "If no value is provded, then you can pass in "
        '"instance-<year><month><day>-<hour><minute>" '
        "where those time values come from the current date time",
    ],
    availability_domain: Annotated[
        str,
        "This is the availability domain to create the instance in. "
        'It must be formatted like "<4-digit-tenancy-code>:<ad-string>". '
        'Example: "aNMj:US-ASHBURN-AD-1". '
        "The value changes per tenancy, per region, and per AD number. "
        "To get a list of availability domains, you may use the "
        "list_availability_domains tool to grab the name of the AD. "
        "This tool is the only way to get the tenancy-code for an AD. "
        "If no AD is specified by the user, you may select the first one available.",
    ],
    subnet_id: Annotated[
        str,
        "This is the ocid of the subnet to attach to the "
        "primary virtual network interface card (VNIC) of the compute instance. "
        "If no value is provided, you may use the list_subnets tool, "
        "selecting the first subnet in the list and passing its ocid.",
    ],
    image_id: Annotated[
        str,
        "This is the ocid of the image for the instance. "
        "If it is left unspecified or if the user specifies an image name, "
        "then you may have to list the images in the root compartment "
        "in order to map the image name to image ocid or display a "
        "list of images for the user to choose from.",
    ] = ORACLE_LINUX_9_IMAGE,
    shape: Annotated[str, "This is the name of the shape for the instance"] = E5_FLEX,
    ocpus: Annotated[
        int, "The total number of cores in the instances"
    ] = DEFAULT_OCPU_COUNT,
    memory_in_gbs: Annotated[
        float, "The total amount of memory in gigabytes to assigned to the instance"
    ] = DEFAULT_MEMORY_IN_GBS,
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
        raise


@mcp.tool
def terminate_instance(instance_id: str) -> Response:
    try:
        client = get_compute_client()

        response: oci.response.Response = client.terminate_instance(instance_id)
        logger.info("Deleted Instance")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in delete_vcn tool: {str(e)}")
        raise


@mcp.tool(
    description="Update instance. " "This may restart the instance so warn the user"
)
def update_instance(
    instance_id: Annotated[str, "The ocid of the instance to update"],
    ocpus: Annotated[int, "The total number of cores in the instances"] = None,
    memory_in_gbs: Annotated[
        float, "The total amount of memory in gigabytes to assigned to the instance"
    ] = None,
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
        raise


@mcp.tool(
    description="List images in a given compartment, optionally filtered by operating system"  # noqa
)
def list_images(compartment_id: str, operating_system: str = None) -> list[Image]:
    images: list[Image] = []

    try:
        client = get_compute_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page:
            response = client.list_images(compartment_id=compartment_id, page=next_page)
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
        raise


@mcp.tool(description="Get Image with a given image OCID")
def get_image(image_id: str) -> Image:
    try:
        client = get_compute_client()

        response: oci.response.Response = client.get_image(image_id=image_id)
        data: oci.core.models.Image = response.data
        logger.info("Found Image")
        return map_image(data)

    except Exception as e:
        logger.error(f"Error in get_image tool: {str(e)}")
        raise


@mcp.tool(description="Perform the desired action on a given instance")
def instance_action(
    instance_id: str,
    action: Annotated[
        str,
        "The action to be performed. The action can only be one of these values: START, STOP, RESET, SOFTSTOP, SOFTRESET, SENDDIAGNOSTICINTERRUPT, DIAGNOSTICREBOOT, REBOOTMIGRATE",  # noqa
    ],
) -> Instance:
    try:
        client = get_compute_client()

        response: oci.response.Response = client.instance_action(instance_id, action)
        data: oci.core.models.Instance = response.data
        logger.info("Performed instance action")
        return map_instance(data)

    except Exception as e:
        logger.error(f"Error in instance_action tool: {str(e)}")
        raise


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
