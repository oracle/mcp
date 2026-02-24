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
from oracle.oci_registry_mcp_server.models import (
    ContainerRepository,
    Response,
    map_container_repository,
    map_response,
)
from pydantic import Field

from . import __project__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


@mcp.tool(description="List container repositories in the given compartment")
@with_oci_client(oci.artifacts.ArtifactsClient)
def list_container_repositories(
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of conatiner repositories to return. If None, there is no limit.",
        ge=1,
    ),
    *,
    client: oci.artifacts.ArtifactsClient,
) -> list[ContainerRepository]:
    container_repositories: list[ContainerRepository] = []

    try:
        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(container_repositories) < limit):
            kwargs = {
                "compartment_id": compartment_id,
                "page": next_page,
                "limit": limit,
            }

            response = client.list_container_repositories(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.artifacts.models.ContainerRepository] = response.data.items
            for d in data:
                container_repositories.append(map_container_repository(d))

        logger.info(f"Found {len(container_repositories)} Container Repositories")
        return container_repositories

    except Exception as e:
        logger.error(f"Error in list_container_repositories tool: {str(e)}")
        raise e


@mcp.tool
@with_oci_client(oci.artifacts.ArtifactsClient)
def get_container_repository(
    repository_id: str = Field(..., description="The OCID of the container repository"),
    *,
    client: oci.artifacts.ArtifactsClient,
) -> ContainerRepository:
    try:
        response: oci.response.Response = client.get_container_repository(repository_id)
        data: oci.artifacts.models.ContainerRepository = response.data
        logger.info("Found Container Repository")
        return map_container_repository(data)

    except Exception as e:
        logger.error(f"Error in get_container_repository tool: {str(e)}")
        raise e


@mcp.tool
@with_oci_client(oci.artifacts.ArtifactsClient)
def create_container_repository(
    compartment_id: str = Field(
        ...,
        description="This is the ocid of the compartment to create the instance in."
        'Must begin with "ocid". If the user specifies a compartment name, '
        "then you may use the list_compartments tool in order to map the "
        "compartment name to its ocid",
    ),
    repository_name: str = Field(
        ...,
        description="The name of the repository",
        min_length=1,
        max_length=255,
    ),
    is_public: bool = Field(
        False, description="Whether or not the repository is public"
    ),
    *,
    client: oci.artifacts.ArtifactsClient,
) -> ContainerRepository:
    try:
        create_repository_details = (
            oci.artifacts.models.CreateContainerRepositoryDetails(
                compartment_id=compartment_id,
                display_name=repository_name,
                is_public=is_public,
            )
        )

        response: oci.response.Response = client.create_container_repository(
            create_repository_details
        )
        data: oci.artifacts.models.ContainerRepository = response.data
        logger.info("Created Container Repository")
        return map_container_repository(data)

    except Exception as e:
        logger.error(f"Error in create_container_repository tool: {str(e)}")
        raise e


@mcp.tool
@with_oci_client(oci.artifacts.ArtifactsClient)
def delete_container_repository(
    repository_id: str = Field(..., description="The OCID of the container repository"),
    *,
    client: oci.artifacts.ArtifactsClient,
) -> Response:
    try:
        response: oci.response.Response = client.delete_container_repository(
            repository_id
        )
        logger.info("Deleted Container Repository")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in delete_container_repository tool: {str(e)}")
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
