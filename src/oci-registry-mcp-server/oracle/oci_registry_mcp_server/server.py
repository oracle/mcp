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
from fastmcp.server.auth.providers.oci import OCIProvider
from fastmcp.server.dependencies import get_access_token
from fastmcp.utilities.auth import parse_scopes
from oracle.oci_registry_mcp_server.models import (
    ContainerRepository,
    Response,
    map_container_repository,
    map_response,
)
from pydantic import Field

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def _get_http_config_and_signer():
    if not (os.getenv("ORACLE_MCP_HOST") and os.getenv("ORACLE_MCP_PORT")):
        return None, None
    token = get_access_token()
    if token is None:
        raise RuntimeError("HTTP requests require an authenticated IDCS access token.")
    domain = os.getenv("IDCS_DOMAIN")
    client_id = os.getenv("IDCS_CLIENT_ID")
    client_secret = os.getenv("IDCS_CLIENT_SECRET")
    if not all((domain, client_id, client_secret)):
        raise RuntimeError(
            "HTTP requests require IDCS authentication. Set IDCS_DOMAIN, IDCS_CLIENT_ID, and IDCS_CLIENT_SECRET."
        )
    region = os.getenv("OCI_REGION")
    if not region:
        raise RuntimeError("HTTP requests require OCI_REGION.")
    config = {"region": region}
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    return config, oci.auth.signers.TokenExchangeSigner(
        token.token,
        f"https://{domain}",
        client_id,
        client_secret,
        region=config.get("region"),
    )

def _get_oci_client_kwargs(signer=None):
    kwargs = {
        "circuit_breaker_strategy": oci.circuit_breaker.CircuitBreakerStrategy(
            failure_threshold=int(os.getenv("OCI_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "10")),
            recovery_timeout=int(os.getenv("OCI_CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30")),
        ),
        "circuit_breaker_callback": lambda exc: logger.warning(
            "Circuit breaker triggered: %s", exc
        ),
    }
    if signer is not None:
        kwargs["signer"] = signer
    return kwargs


def get_ocir_client():
    config, signer = _get_http_config_and_signer()
    if signer is not None:
        return oci.artifacts.ArtifactsClient(config, **_get_oci_client_kwargs(signer))
    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )

    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = os.path.expanduser(config["security_token_file"])
    token = None
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.artifacts.ArtifactsClient(config, **_get_oci_client_kwargs(signer))


@mcp.tool(description="List container repositories in the given compartment")
def list_container_repositories(
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of conatiner repositories to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[ContainerRepository]:
    container_repositories: list[ContainerRepository] = []

    try:
        client = get_ocir_client()

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
def get_container_repository(
    repository_id: str = Field(..., description="The OCID of the container repository"),
) -> ContainerRepository:
    try:
        client = get_ocir_client()

        response: oci.response.Response = client.get_container_repository(repository_id)
        data: oci.artifacts.models.ContainerRepository = response.data
        logger.info("Found Container Repository")
        return map_container_repository(data)

    except Exception as e:
        logger.error(f"Error in get_container_repository tool: {str(e)}")
        raise e


@mcp.tool
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
    is_public: bool = Field(False, description="Whether or not the repository is public"),
) -> ContainerRepository:
    try:
        client = get_ocir_client()

        create_repository_details = oci.artifacts.models.CreateContainerRepositoryDetails(
            compartment_id=compartment_id,
            display_name=repository_name,
            is_public=is_public,
        )

        response: oci.response.Response = client.create_container_repository(create_repository_details)
        data: oci.artifacts.models.ContainerRepository = response.data
        logger.info("Created Container Repository")
        return map_container_repository(data)

    except Exception as e:
        logger.error(f"Error in create_container_repository tool: {str(e)}")
        raise e


@mcp.tool
def delete_container_repository(
    repository_id: str = Field(..., description="The OCID of the container repository"),
) -> Response:
    try:
        client = get_ocir_client()

        response: oci.response.Response = client.delete_container_repository(repository_id)
        logger.info("Deleted Container Repository")
        return map_response(response)

    except Exception as e:
        logger.error(f"Error in delete_container_repository tool: {str(e)}")
        raise e


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if not (host and port):
        mcp.run()
        return
    domain = os.getenv("IDCS_DOMAIN")
    client_id = os.getenv("IDCS_CLIENT_ID")
    client_secret = os.getenv("IDCS_CLIENT_SECRET")
    base_url = os.getenv("ORACLE_MCP_BASE_URL", "")
    audience = os.getenv("IDCS_AUDIENCE")
    if not all((domain, client_id, client_secret, audience, base_url)):
        raise RuntimeError(
            "HTTP transport requires IDCS authentication. "
            "Set IDCS_DOMAIN, IDCS_CLIENT_ID, IDCS_CLIENT_SECRET, IDCS_AUDIENCE, "
            "ORACLE_MCP_BASE_URL, ORACLE_MCP_HOST, and ORACLE_MCP_PORT."
        )
    mcp.auth = OCIProvider(
        config_url=f"https://{domain}/.well-known/openid-configuration",
        client_id=client_id,
        client_secret=client_secret,
        audience=audience,
        required_scopes=parse_scopes(os.getenv("IDCS_REQUIRED_SCOPES")) or f"openid profile email oci_mcp.{__project__.removeprefix('oracle.oci-').removesuffix('-mcp-server').replace('-', '_')}.invoke".split(),
        base_url=base_url,
    )
    mcp.run(transport="http", host=host, port=int(port))


if __name__ == "__main__":
    main()
