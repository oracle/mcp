"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import base64
import json
import os
from logging import Logger
from typing import Literal, Optional

import oci
from fastmcp import FastMCP
from oracle.oci_identity_mcp_server.models import (
    AuthToken,
    AvailabilityDomain,
    Compartment,
    RegionSubscription,
    Tenancy,
    User,
    map_auth_token,
    map_availability_domain,
    map_compartment,
    map_region_subscription,
    map_tenancy,
    map_user,
)
from pydantic import Field

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_identity_client():
    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = os.path.expanduser(config["security_token_file"])
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.identity.IdentityClient(config, signer=signer)


@mcp.tool(description="List compartments in a given compartment or tenancy.")
def list_compartments(
    compartment_id: str = Field(
        ...,
        description="The OCID of the compartment (remember that the tenancy is simply the root compartment)",
    ),
    compartment_id_in_subtree: Optional[bool] = Field(
        False,
        description="Can only be set to true when performing ListCompartments on the tenancy "
        "(root compartment). When set to true, the hierarchy of compartments is "
        "traversed and all compartments and subcompartments in the tenancy are returned "
        "depending on the the setting of accessLevel",
    ),
    access_level: Optional[Literal["ANY", "ACCESSIBLE"]] = Field(
        "ANY",
        description="Setting this to ACCESSIBLE returns only those compartments for which the user has "
        "INSPECT permissions directly or indirectly (permissions can be on a resource in a subcompartment). "
        "For the compartments on which the user indirectly has INSPECT permissions, a restricted set of "
        "fields is returned. When set to ANY permissions are not checked.",
    ),
    include_root: Optional[bool] = Field(
        True,
        description="Whether to include the root compartment in the response. "
        "Always include the root compartment in the response unless the user asks for it to not be included.",
    ),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of compartments to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[Compartment]:
    compartments: list[Compartment] = []

    try:
        client = get_identity_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(compartments) < limit):
            kwargs = {
                "compartment_id": compartment_id,
                "page": next_page,
                "limit": limit,
                "compartment_id_in_subtree": compartment_id_in_subtree,
                "access_level": access_level,
            }

            response = client.list_compartments(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.identity.models.Compartment] = response.data
            for d in data:
                compartments.append(map_compartment(d))

        if include_root:
            config = oci.config.from_file(
                file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
                profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
            )
            tenancy_id = os.getenv("TENANCY_ID_OVERRIDE", config["tenancy"])
            tenancy_response: oci.response.Response = client.get_compartment(
                compartment_id=tenancy_id,
            )
            root_compartment: Compartment = tenancy_response.data
            compartments.append(map_compartment(root_compartment))
        logger.info(f"Found {len(compartments)} Compartments")
        return compartments

    except Exception as e:
        logger.error(f"Error in list_compartments tool: {str(e)}")
        raise e


@mcp.tool(description="Get tenancy with a given OCID")
def get_tenancy(tenancy_id: str = Field(..., description="The OCID of the tenancy")) -> Tenancy:
    try:
        client = get_identity_client()

        response: oci.response.Response = client.get_tenancy(tenancy_id)
        data: oci.identity.models.Tenancy = response.data
        logger.info("Found Tenancy")
        return map_tenancy(data)

    except Exception as e:
        logger.error(f"Error in get_tenancy tool: {str(e)}")
        raise e


@mcp.tool(description="Lists all of the availability domains in a given tenancy")
def list_availability_domains(
    compartment_id: str = Field(
        ...,
        description="The OCID of the compartment (remember that the tenancy is simply the root compartment)",
    ),
) -> list[AvailabilityDomain]:
    ads: list[AvailabilityDomain] = []

    try:
        client = get_identity_client()

        response = client.list_availability_domains(compartment_id)

        data: list[oci.identity.models.AvailabilityDomain] = response.data
        for d in data:
            ads.append(map_availability_domain(d))

        logger.info(f"Found {len(ads)} Availability Domains")
        return ads

    except Exception as e:
        logger.error(f"Error in list_availability_domains tool: {str(e)}")
        raise e


@mcp.tool
def get_current_tenancy() -> Tenancy:
    try:
        client = get_identity_client()

        config = oci.config.from_file(
            file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
            profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
        )
        tenancy_id = os.getenv("TENANCY_ID_OVERRIDE", config["tenancy"])
        response: oci.response.Response = client.get_tenancy(tenancy_id)
        data: oci.identity.models.Tenancy = response.data
        logger.info("Found Tenancy")
        return map_tenancy(data)

    except Exception as e:
        logger.error(f"Error in get_tenancy tool: {str(e)}")
        raise e


@mcp.tool
def create_auth_token(
    user_id: str = Field(..., description="The OCID of the user"),
    description: Optional[str] = Field("", description="The description of the auth token"),
) -> AuthToken:
    try:
        client = get_identity_client()

        create_auth_token_details = oci.identity.models.CreateAuthTokenDetails(description=description)

        response: oci.response.Response = client.create_auth_token(
            user_id=user_id,
            create_auth_token_details=create_auth_token_details,
        )
        data: oci.identity.models.AuthToken = response.data
        logger.info("Created auth token")
        return map_auth_token(data)

    except Exception as e:
        logger.error(f"Error in create_auth_token tool: {str(e)}")
        raise e


@mcp.tool
def get_current_user() -> User:
    try:
        client = get_identity_client()
        config = oci.config.from_file(
            file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
            profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
        )

        # Prefer explicit user from config if present
        user_id = config.get("user")

        # Fallback: derive user OCID from the security token (session auth)
        if not user_id:
            token_file = config.get("security_token_file")
            if token_file and os.path.exists(token_file):
                with open(token_file, "r") as f:
                    token = f.read().strip()

                # Expect JWT-like token: header.payload.signature (base64url)
                if "." in token:
                    try:
                        payload_b64 = token.split(".", 2)[1]
                        padding = "=" * (-len(payload_b64) % 4)
                        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
                        payload = json.loads(payload_json)
                        # 'sub' typically contains the user OCID for session tokens;
                        # fallback to opc-user-id if present
                        user_id = payload.get("sub") or payload.get("opc-user-id")
                    except Exception:
                        user_id = None

            if not user_id:
                raise KeyError("Unable to determine current user OCID from config or security token")

        response: oci.response.Response = client.get_user(user_id)
        data: oci.identity.models.User = response.data
        logger.info("Found current user")
        return map_user(data)

    except Exception as e:
        logger.error(f"Error in get_current_user tool: {str(e)}")
        raise e


@mcp.tool(description="Get a specific compartment by its name within a parent compartment.")
def get_compartment_by_name(
    name: str = Field(description="The name of the compartment to find."),
    parent_compartment_id: str = Field(
        description="The OCID of the parent compartment to search within (or tenancy OCID).",
    ),
) -> Optional[Compartment]:
    """
    Searches for a compartment by name within a specific parent compartment.
    Note: This is not a recursive search; it only looks at direct children.
    """
    try:
        client = get_identity_client()

        has_next_page = True
        next_page: str = None

        while has_next_page:
            response = client.list_compartments(
                compartment_id=parent_compartment_id,
                page=next_page,
                access_level="ACCESSIBLE",
                lifecycle_state="ACTIVE",
            )

            for cmp in response.data:
                if cmp.name == name:
                    logger.info(f"Found compartment: {name}")
                    return map_compartment(cmp)

            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

        logger.warning(f"Compartment '{name}' not found in parent '{parent_compartment_id}'")
        return None

    except Exception as e:
        logger.error(f"Error in get_compartment_by_name tool: {str(e)}")
        raise e


@mcp.tool(description="List the regions a tenancy is subscribed to.")
def list_subscribed_regions(
    tenancy_id: str = Field(..., description="The OCID of the tenancy."),
) -> list[RegionSubscription]:
    regions: list[RegionSubscription] = []

    try:
        client = get_identity_client()
        response = client.list_region_subscriptions(tenancy_id=tenancy_id)

        data: list[oci.identity.models.RegionSubscription] = response.data
        for d in data:
            regions.append(map_region_subscription(d))

        logger.info(f"Found {len(regions)} subscribed regions")
        return regions

    except Exception as e:
        logger.error(f"Error in list_subscribed_regions tool: {str(e)}")
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
