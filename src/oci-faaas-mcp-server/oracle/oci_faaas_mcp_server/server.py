"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Any, Literal, Optional

import oci
from fastmcp import FastMCP
from pydantic import Field

from . import __project__, __version__
from .models import (
    FusionEnvironment,
    FusionEnvironmentFamily,
    FusionEnvironmentStatus,
    map_fusion_environment,
    map_fusion_environment_family,
    map_fusion_environment_status,
)

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


@mcp.tool(
    description="Returns a list of Fusion Environment Families in the specified compartment."
)
def list_fusion_environment_families(
    compartment_id: str = Field(
        ..., description="The ID of the compartment in which to list resources."
    ),
    display_name: Optional[str] = Field(
        None, description="Filter to match entire display name."
    ),
    lifecycle_state: Optional[
        Literal["CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED"]
    ] = Field(
        None,
        description=(
            "Filter by lifecycle state. Allowed: CREATING, UPDATING, ACTIVE, "
            "DELETING, DELETED, FAILED"
        ),
    ),
) -> list[FusionEnvironmentFamily]:
    client = get_faaas_client()

    families: list[FusionEnvironmentFamily] = []
    next_page: Optional[str] = None
    has_next_page = True

    while has_next_page:
        kwargs: dict[str, Any] = {"compartment_id": compartment_id}
        if next_page is not None:
            kwargs["page"] = next_page
        if display_name is not None:
            kwargs["display_name"] = display_name
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state

        response: oci.response.Response = client.list_fusion_environment_families(
            **kwargs
        )

        # Normalize response data to an iterable without using helpers
        data_obj = response.data or []
        items = getattr(data_obj, "items", None)
        iterable = (
            items
            if items is not None
            else (data_obj if isinstance(data_obj, list) else [data_obj])
        )
        for d in iterable:
            families.append(map_fusion_environment_family(d))

        # Robust pagination handling with header fallback
        headers = getattr(response, "headers", None)
        next_page = getattr(response, "next_page", None)
        if next_page is None and headers:
            try:
                next_page = dict(headers).get("opc-next-page")
            except Exception:
                next_page = None
        has_next_page = next_page is not None

    logger.info(f"Found {len(families)} Fusion Environment Families")
    return families


@mcp.tool(
    description=(
        "Returns a list of Fusion Environments in the specified compartment "
        "(optionally filtered by family)."
    )
)
def list_fusion_environments(
    compartment_id: str = Field(
        ..., description="The ID of the compartment in which to list resources."
    ),
    fusion_environment_family_id: Optional[str] = Field(
        None, description="Optional Fusion Environment Family OCID"
    ),
    display_name: Optional[str] = Field(
        None, description="Filter to match entire display name."
    ),
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "UPDATING",
            "ACTIVE",
            "INACTIVE",
            "DELETING",
            "DELETED",
            "FAILED",
        ]
    ] = Field(
        None,
        description=(
            "Filter by lifecycle state. Allowed: CREATING, UPDATING, ACTIVE, "
            "INACTIVE, DELETING, DELETED, FAILED"
        ),
    ),
) -> list[FusionEnvironment]:
    client = get_faaas_client()

    environments: list[FusionEnvironment] = []
    next_page: Optional[str] = None
    has_next_page = True

    while has_next_page:
        kwargs: dict[str, Any] = {"compartment_id": compartment_id}
        if next_page is not None:
            kwargs["page"] = next_page
        if fusion_environment_family_id is not None:
            kwargs["fusion_environment_family_id"] = fusion_environment_family_id
        if display_name is not None:
            kwargs["display_name"] = display_name
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state

        response: oci.response.Response = client.list_fusion_environments(**kwargs)

        # Normalize response data to an iterable without using helpers
        data_obj = response.data or []
        items = getattr(data_obj, "items", None)
        iterable = (
            items
            if items is not None
            else (data_obj if isinstance(data_obj, list) else [data_obj])
        )
        for d in iterable:
            environments.append(map_fusion_environment(d))

        # Robust pagination handling with header fallback
        headers = getattr(response, "headers", None)
        next_page = getattr(response, "next_page", None)
        if next_page is None and headers:
            try:
                next_page = dict(headers).get("opc-next-page")
            except Exception:
                next_page = None
        has_next_page = next_page is not None

    logger.info(f"Found {len(environments)} Fusion Environments")
    return environments


@mcp.tool(description="Gets a Fusion Environment by OCID.")
def get_fusion_environment(
    fusion_environment_id: str = Field(
        ..., description="Unique FusionEnvironment identifier (OCID)"
    ),
) -> FusionEnvironment:
    client = get_faaas_client()
    response: oci.response.Response = client.get_fusion_environment(
        fusion_environment_id
    )
    return map_fusion_environment(response.data)


@mcp.tool(description="Gets the status of a Fusion Environment by OCID.")
def get_fusion_environment_status(
    fusion_environment_id: str = Field(
        ..., description="Unique FusionEnvironment identifier (OCID)"
    ),
) -> FusionEnvironmentStatus:
    client = get_faaas_client()
    response: oci.response.Response = client.get_fusion_environment_status(
        fusion_environment_id
    )
    return map_fusion_environment_status(response.data)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
