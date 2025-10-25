"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger

import oci
from fastmcp import FastMCP

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_ocir_client():
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )

    config["additional_user_agent"] = f"{__project__}/{__version__}"

    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    token = None
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.artifacts.ArtifactsClient(config, signer=signer)


@mcp.tool
def create_container_repository(
    compartment_id: str, repository_name: str, is_public: bool = False
):
    ocir_client = get_ocir_client()
    create_repository_details = oci.artifacts.models.CreateContainerRepositoryDetails(
        compartment_id=compartment_id, display_name=repository_name, is_public=is_public
    )
    try:
        repository = ocir_client.create_container_repository(
            create_repository_details
        ).data
        return {
            "repository_name": repository.display_name,
            "id": repository.id,
            "is_public": repository.is_public,
        }
    except oci.exceptions.ServiceError as e:
        logger.error(f"Failed to create container repository: {e}")
        return {"error": str(e)}


@mcp.tool
def list_container_repositories(compartment_id: str):
    ocir_client = get_ocir_client()
    try:
        repositories = ocir_client.list_container_repositories(
            compartment_id=compartment_id
        ).data.items
        return [
            {
                "repository_name": repo.display_name,
                "id": repo.id,
                "is_public": repo.is_public,
            }
            for repo in repositories
        ]
    except oci.exceptions.ServiceError as e:
        logger.error(f"Failed to list container repositories: {e}")
        return {"error": str(e)}


@mcp.tool
def get_container_repo_details(repository_id: str):
    ocir_client = get_ocir_client()
    try:
        repository = ocir_client.get_container_repository(
            repository_id=repository_id
        ).data
        return {
            "repository_name": repository.display_name,
            "id": repository.id,
            "is_public": repository.is_public,
            "compartment_id": repository.compartment_id,
            "time_created": repository.time_created.isoformat(),
        }
    except oci.exceptions.ServiceError as e:
        logger.error(f"Failed to get container repository details: {e}")
        return {"error": str(e)}


@mcp.tool
def delete_container_repository(repository_id: str):
    ocir_client = get_ocir_client()
    try:
        ocir_client.delete_container_repository(repository_id=repository_id)
        return {"success": True}
    except oci.exceptions.ServiceError as e:
        logger.error(f"Failed to delete container repository: {e}")
        return {"error": str(e), "success": False}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
