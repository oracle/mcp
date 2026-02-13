"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from logging import Logger
from typing import Any, Literal, Optional

import oci
from fastmcp import FastMCP
from oracle.mcp_common import with_oci_client
from pydantic import Field

from . import __project__
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


@mcp.tool(
    description="Returns a list of Fusion Environment Families in the specified compartment."
)
@with_oci_client(oci.fusion_apps.FusionApplicationsClient)
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
    *,
    client: oci.fusion_apps.FusionApplicationsClient,
) -> list[FusionEnvironmentFamily]:

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
@with_oci_client(oci.fusion_apps.FusionApplicationsClient)
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
    *,
    client: oci.fusion_apps.FusionApplicationsClient,
) -> list[FusionEnvironment]:

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
@with_oci_client(oci.fusion_apps.FusionApplicationsClient)
def get_fusion_environment(
    fusion_environment_id: str = Field(
        ..., description="Unique FusionEnvironment identifier (OCID)"
    ),
    *,
    client: oci.fusion_apps.FusionApplicationsClient,
) -> FusionEnvironment:
    response: oci.response.Response = client.get_fusion_environment(
        fusion_environment_id
    )
    return map_fusion_environment(response.data)


@mcp.tool(description="Gets the status of a Fusion Environment by OCID.")
@with_oci_client(oci.fusion_apps.FusionApplicationsClient)
def get_fusion_environment_status(
    fusion_environment_id: str = Field(
        ..., description="Unique FusionEnvironment identifier (OCID)"
    ),
    *,
    client: oci.fusion_apps.FusionApplicationsClient,
) -> FusionEnvironmentStatus:
    response: oci.response.Response = client.get_fusion_environment_status(
        fusion_environment_id
    )
    return map_fusion_environment_status(response.data)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
