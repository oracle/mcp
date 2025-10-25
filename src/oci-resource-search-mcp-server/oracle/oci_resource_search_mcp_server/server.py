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
from oci.resource_search.models import FreeTextSearchDetails, StructuredSearchDetails

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_search_client():
    logger.info("entering get_search_client")
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
    return oci.resource_search.ResourceSearchClient(config, signer=signer)


@mcp.tool
def list_all_resources(compartment_id: str) -> list[dict]:
    """Returns all resources"""
    search_client = get_search_client()
    structured_search = StructuredSearchDetails(
        type="Structured",
        query=f"query all resources where compartmentId = '{compartment_id}'",
    )
    response = search_client.search_resources(structured_search).data
    return [
        {
            "resource_id": resource.identifier,
            "compartment_id": compartment_id,
            "display_name": resource.display_name,
            "resource_type": resource.resource_type,
            "lifecycle_state": resource.lifecycle_state,
            "freeform_tags": resource.freeform_tags,
            "defined_tags": resource.defined_tags,
        }
        for resource in response.items
    ]


@mcp.tool
def search_resources(
    compartment_id: str,
    display_name: Annotated[str, "Full display name or display name substring"],
) -> list[dict]:
    """Searches for resources by display name"""
    search_client = get_search_client()
    structured_search = StructuredSearchDetails(
        type="Structured",
        query=(
            f"query all resources where compartmentId = '{compartment_id}' "
            f"&& displayName =~ '{display_name}'"
        ),
    )
    response = search_client.search_resources(structured_search).data
    return [
        {
            "resource_id": resource.identifier,
            "compartment_id": compartment_id,
            "display_name": resource.display_name,
            "resource_type": resource.resource_type,
            "lifecycle_state": resource.lifecycle_state,
            "freeform_tags": resource.freeform_tags,
            "defined_tags": resource.defined_tags,
        }
        for resource in response.items
    ]


@mcp.tool
def search_resources_free_form(
    compartment_id: str,
    text: Annotated[str, "Free-form search string"],
) -> list[dict]:
    """Searches for the presence of the search string in all resource fields"""
    search_client = get_search_client()
    freetext_search = FreeTextSearchDetails(
        type="FreeText",
        text=text,
    )
    response = search_client.search_resources(freetext_search).data
    return [
        {
            "resource_id": resource.identifier,
            "compartment_id": compartment_id,
            "display_name": resource.display_name,
            "resource_type": resource.resource_type,
            "lifecycle_state": resource.lifecycle_state,
            "freeform_tags": resource.freeform_tags,
            "defined_tags": resource.defined_tags,
        }
        for resource in response.items
    ]


def search_resources_by_type(compartment_id: str, resource_type: str):
    """Search for resources by resource type"""
    search_client = get_search_client()
    structured_search = StructuredSearchDetails(
        type="Structured",
        query=(
            f"query all {resource_type} "
            f"resources where compartmentId = '{compartment_id}'"
        ),
    )
    response = search_client.search_resources(structured_search).data
    return [
        {
            "resource_id": resource.identifier,
            "compartment_id": compartment_id,
            "display_name": resource.display_name,
            "resource_type": resource.resource_type,
            "lifecycle_state": resource.lifecycle_state,
            "freeform_tags": resource.freeform_tags,
            "defined_tags": resource.defined_tags,
        }
        for resource in response.items
    ]


@mcp.tool
def list_resource_types() -> list[str]:
    """Returns a list of all supported OCI resource types"""
    search_client = get_search_client()
    resource_types = search_client.list_resource_types()
    return [x.name for x in resource_types.data]


def main():
    mcp.run()


if __name__ == "__main__":
    main()
