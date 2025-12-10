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
from oci.resource_search.models import FreeTextSearchDetails, StructuredSearchDetails
from oracle.oci_resource_search_mcp_server.models import (
    ResourceSummary,
    map_resource_summary,
)
from pydantic import Field

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


@mcp.tool(description="Returns all resources")
def list_all_resources(
    tenant_id: str = Field(
        ...,
        description="The tenancy ID, which can be used to specify a different tenancy "
        "(for cross-tenancy authorization) when searching for resources in a different tenancy",
    ),
    compartment_id: str = Field(
        ..., description="The OCID of the compartment to list from"
    ),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[ResourceSummary]:
    resources: list[ResourceSummary] = []

    try:
        client = get_search_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(resources) < limit):
            kwargs = {
                "tenant_id": tenant_id,
                "search_details": StructuredSearchDetails(
                    type="Structured",
                    query=f"query all resources where compartmentId = '{compartment_id}'",
                ),
                "page": next_page,
                "limit": limit,
            }

            response = client.search_resources(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.resource_search.models.ResourceSummary] = response.data.items
            for d in data:
                resources.append(map_resource_summary(d))

        logger.info(f"Found {len(resources)} Resources")
        return resources

    except Exception as e:
        logger.error(f"Error in list_all_resources tool: {str(e)}")
        raise e


@mcp.tool(description="Searches for resources by display name")
def search_resources(
    tenant_id: str = Field(
        ...,
        description="The tenancy ID, which can be used to specify a different tenancy "
        "(for cross-tenancy authorization) when searching for resources in a different tenancy",
    ),
    compartment_id: str = Field(
        ..., description="The OCID of the compartment to list from"
    ),
    display_name: str = Field(
        ..., description="The display name (full or substring) of the resource"
    ),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[ResourceSummary]:
    resources: list[ResourceSummary] = []

    try:
        client = get_search_client()

        oci.identity.models.Compartment

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(resources) < limit):
            kwargs = {
                "tenant_id": tenant_id,
                "search_details": StructuredSearchDetails(
                    type="Structured",
                    query=(
                        f"query all resources where compartmentId = '{compartment_id}' "
                        f"&& displayName =~ '{display_name}'"
                    ),
                ),
                "page": next_page,
                "limit": limit,
            }

            response = client.search_resources(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.resource_search.models.ResourceSummary] = response.data.items
            for d in data:
                resources.append(map_resource_summary(d))

        logger.info(f"Found {len(resources)} Resources")
        return resources

    except Exception as e:
        logger.error(f"Error in search_resources tool: {str(e)}")
        raise e


@mcp.tool(
    description="Searches for the presence of the search string in all resource fields"
)
def search_resources_free_form(
    tenant_id: str = Field(
        ...,
        description="The tenancy ID, which can be used to specify a different tenancy "
        "(for cross-tenancy authorization) when searching for resources in a different tenancy",
    ),
    text: str = Field(..., description="Free-form search string"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[ResourceSummary]:
    resources: list[ResourceSummary] = []

    try:
        client = get_search_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(resources) < limit):
            kwargs = {
                "tenant_id": tenant_id,
                "search_details": FreeTextSearchDetails(
                    type="FreeText",
                    text=text,
                ),
                "page": next_page,
                "limit": limit,
            }

            response = client.search_resources(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.resource_search.models.ResourceSummary] = response.data.items
            for d in data:
                resources.append(map_resource_summary(d))

        logger.info(f"Found {len(resources)} Resources")
        return resources

    except Exception as e:
        logger.error(f"Error in search_resources_free_form tool: {str(e)}")
        raise e


@mcp.tool(description="Search for resources by resource type")
def search_resources_by_type(
    tenant_id: str = Field(
        ...,
        description="The tenancy ID, which can be used to specify a different tenancy "
        "(for cross-tenancy authorization) when searching for resources in a different tenancy",
    ),
    compartment_id: str = Field(
        ..., description="The OCID of the compartment to list from"
    ),
    resource_type: str = Field(
        ...,
        description="The source type to search by"
        "You may call list_resource_types to see the list of possible values"
        "Note: The values MUST be in lowercase",
    ),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[ResourceSummary]:
    resources: list[ResourceSummary] = []

    try:
        client = get_search_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(resources) < limit):
            kwargs = {
                "tenant_id": tenant_id,
                "search_details": StructuredSearchDetails(
                    type="Structured",
                    query=(
                        f"query {resource_type.lower()} "
                        f"resources where compartmentId = '{compartment_id}'"
                    ),
                ),
                "page": next_page,
                "limit": limit,
            }

            response = client.search_resources(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.resource_search.models.ResourceSummary] = response.data.items
            for d in data:
                resources.append(map_resource_summary(d))

        logger.info(f"Found {len(resources)} Resources")
        return resources

    except Exception as e:
        logger.error(f"Error in search_resources_by_type tool: {str(e)}")
        raise e


@mcp.tool(description="Returns a list of all supported OCI resource types")
def list_resource_types(
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[str]:
    resource_types: list[str] = []

    try:
        client = get_search_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(resource_types) < limit):
            kwargs = {
                "page": next_page,
                "limit": limit,
            }

            response = client.list_resource_types(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.resource_search.models.ResourceType] = response.data
            for d in data:
                resource_types.append(d.name)

        logger.info(f"Found {len(resource_types)} resource types")
        return resource_types

    except Exception as e:
        logger.error(f"Error in list_resource_types tool: {str(e)}")
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
