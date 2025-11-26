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

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_faaas_client():
    """Initialize and return an OCI Fusion Applications client using security token auth."""
    logger.info("entering get_faaas_client")

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

    return oci.fusion_apps.FusionApplicationsClient(config, signer=signer)


def _to_dict(obj):
    """Best-effort conversion of OCI SDK model objects to plain dicts."""
    try:
        return oci.util.to_dict(obj)
    except Exception:
        try:
            return obj.__dict__
        except Exception:
            return obj


def _append_items_from_response_data(accum: list[dict], data_obj):
    """
    Normalize list responses across SDK collections/lists:
      - If response.data has 'items', iterate it
      - If it's already a list, iterate directly
      - Else treat it as a single object
    """
    try:
        items = getattr(data_obj, "items", None)
        if items is not None:
            for it in items:
                accum.append(_to_dict(it))
            return

        if isinstance(data_obj, list):
            for it in data_obj:
                accum.append(_to_dict(it))
            return

        # Fallback: single object
        accum.append(_to_dict(data_obj))
    except Exception as e:
        logger.error(f"Error converting response data to dicts: {e}")
        raise


@mcp.tool(
    description="Returns a list of Fusion Environment Families in the specified compartment."
)
def list_fusion_environment_families(
    compartment_id: Annotated[
        str, "The ID of the compartment in which to list resources."
    ],
    display_name: Annotated[str, "Filter to match entire display name."] = None,
    lifecycle_state: Annotated[
        str,
        "Filter by lifecycle state. Allowed: CREATING, UPDATING, ACTIVE, DELETING, DELETED, FAILED",
    ] = None,
) -> list[dict]:
    client = get_faaas_client()

    families: list[dict] = []
    next_page: str | None = None
    has_next_page = True

    while has_next_page:
        response: oci.response.Response = client.list_fusion_environment_families(
            compartment_id=compartment_id,
            display_name=display_name,
            lifecycle_state=lifecycle_state,
            page=next_page,
        )
        _append_items_from_response_data(families, response.data)
        has_next_page = getattr(response, "has_next_page", False)
        next_page = getattr(response, "next_page", None)

    logger.info(f"Found {len(families)} Fusion Environment Families")
    return families


@mcp.tool(
    description=(
        "Returns a list of Fusion Environments in the specified compartment "
        "(optionally filtered by family)."
    )
)
def list_fusion_environments(
    compartment_id: Annotated[
        str, "The ID of the compartment in which to list resources."
    ],
    fusion_environment_family_id: Annotated[
        str, "Optional Fusion Environment Family OCID"
    ] = None,
    display_name: Annotated[str, "Filter to match entire display name."] = None,
    lifecycle_state: Annotated[
        str,
        "Filter by lifecycle state. Allowed: CREATING, UPDATING, ACTIVE, INACTIVE, DELETING, DELETED, FAILED",
    ] = None,
) -> list[dict]:
    client = get_faaas_client()

    environments: list[dict] = []
    next_page: str | None = None
    has_next_page = True

    while has_next_page:
        response: oci.response.Response = client.list_fusion_environments(
            compartment_id=compartment_id,
            fusion_environment_family_id=fusion_environment_family_id,
            display_name=display_name,
            lifecycle_state=lifecycle_state,
            page=next_page,
        )
        _append_items_from_response_data(environments, response.data)
        has_next_page = getattr(response, "has_next_page", False)
        next_page = getattr(response, "next_page", None)

    logger.info(f"Found {len(environments)} Fusion Environments")
    return environments


@mcp.tool(description="Gets a Fusion Environment by OCID.")
def get_fusion_environment(
    fusion_environment_id: Annotated[str, "Unique FusionEnvironment identifier (OCID)"],
) -> dict:
    client = get_faaas_client()
    response: oci.response.Response = client.get_fusion_environment(
        fusion_environment_id
    )
    return _to_dict(response.data)


@mcp.tool(description="Gets the status of a Fusion Environment by OCID.")
def get_fusion_environment_status(
    fusion_environment_id: Annotated[str, "Unique FusionEnvironment identifier (OCID)"],
) -> dict:
    client = get_faaas_client()
    response: oci.response.Response = client.get_fusion_environment_status(
        fusion_environment_id
    )
    return _to_dict(response.data)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
