"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from datetime import datetime
from logging import Logger
from typing import Any, Literal, Optional

import oci
from fastmcp import FastMCP
from pydantic import Field

from . import __project__, __version__
from .models import (
    AdminUserSummary,
    FusionEnvironment,
    FusionEnvironmentFamily,
    FusionEnvironmentStatus,
    RefreshActivitySummary,
    ScheduledActivity,
    ScheduledActivitySummary,
    SubscriptionDetail,
    map_admin_user_summary,
    map_fusion_environment,
    map_fusion_environment_family,
    map_fusion_environment_status,
    map_refresh_activity_summary,
    map_scheduled_activity,
    map_scheduled_activity_summary,
    map_subscription_detail,
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
    limit: Optional[int] = Field(
        None,
        description="The maximum number of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[FusionEnvironmentFamily]:
    client = get_faaas_client()

    families: list[FusionEnvironmentFamily] = []
    next_page: Optional[str] = None
    has_next_page = True

    while has_next_page and (limit is None or len(families) < limit):
        kwargs: dict[str, Any] = {"compartment_id": compartment_id}
        if next_page is not None:
            kwargs["page"] = next_page
        if limit is not None:
            kwargs["limit"] = limit
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
            if limit is not None and len(families) >= limit:
                break

        # Robust pagination handling with header fallback
        headers = getattr(response, "headers", None)
        next_page = getattr(response, "next_page", None)
        if next_page is None and headers:
            try:
                next_page = dict(headers).get("opc-next-page")
            except Exception:
                next_page = None
        has_next_page = next_page is not None and (
            limit is None or len(families) < limit
        )

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
    limit: Optional[int] = Field(
        None,
        description="The maximum number of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[FusionEnvironment]:
    client = get_faaas_client()

    environments: list[FusionEnvironment] = []
    next_page: Optional[str] = None
    has_next_page = True

    while has_next_page and (limit is None or len(environments) < limit):
        kwargs: dict[str, Any] = {"compartment_id": compartment_id}
        if next_page is not None:
            kwargs["page"] = next_page
        if limit is not None:
            kwargs["limit"] = limit
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
            if limit is not None and len(environments) >= limit:
                break

        # Robust pagination handling with header fallback
        headers = getattr(response, "headers", None)
        next_page = getattr(response, "next_page", None)
        if next_page is None and headers:
            try:
                next_page = dict(headers).get("opc-next-page")
            except Exception:
                next_page = None
        has_next_page = next_page is not None and (
            limit is None or len(environments) < limit
        )

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


@mcp.tool(description="List all FusionEnvironment admin users")
def list_admin_users(
    fusion_environment_id: str = Field(
        ..., description="unique FusionEnvironment identifier"
    )
) -> list[AdminUserSummary]:
    client = get_faaas_client()

    admins: list[AdminUserSummary] = []
    next_page: Optional[str] = None
    has_next_page = True

    while has_next_page:
        kwargs: dict[str, Any] = {"fusion_environment_id": fusion_environment_id}
        if next_page is not None:
            kwargs["page"] = next_page

        response: oci.response.Response = client.list_admin_users(**kwargs)

        data_obj = response.data or []
        items = getattr(data_obj, "items", None)
        iterable = (
            items
            if items is not None
            else (data_obj if isinstance(data_obj, list) else [data_obj])
        )
        for d in iterable:
            mapped = map_admin_user_summary(d)
            if mapped:
                admins.append(mapped)

        has_next_page = getattr(response, "has_next_page", False)
        next_page = getattr(response, "next_page", None)

    return admins


@mcp.tool(description="List all FusionEnvironment refresh activities")
def list_refresh_activities(
    fusion_environment_id: str = Field(
        ..., description="unique FusionEnvironment identifier"
    ),
    display_name: Optional[str] = Field(
        None, description="Filter to match entire display name."
    ),
    time_scheduled_start_greater_than_or_equal_to: Optional[datetime] = Field(
        None, description="Filter: scheduled start time >= this RFC3339 datetime"
    ),
    time_expected_finish_less_than_or_equal_to: Optional[datetime] = Field(
        None, description="Filter: expected finish time <= this RFC3339 datetime"
    ),
    lifecycle_state: Optional[
        Literal[
            "ACCEPTED",
            "IN_PROGRESS",
            "NEEDS_ATTENTION",
            "FAILED",
            "SUCCEEDED",
            "CANCELED",
        ]
    ] = Field(
        None,
        description=(
            "Filter by lifecycle state. Allowed: ACCEPTED, IN_PROGRESS, "
            "NEEDS_ATTENTION, FAILED, SUCCEEDED, CANCELED."
        ),
    ),
    limit: Optional[int] = Field(
        None, description="Maximum number of results per page.", ge=1
    ),
    page: Optional[str] = Field(
        None, description="Pagination token from a previous call."
    ),
    sort_order: Optional[Literal["ASC", "DESC"]] = Field(
        None, description="Sort order: ASC or DESC"
    ),
    sort_by: Optional[Literal["TIME_CREATED", "DISPLAY_NAME"]] = Field(
        None, description="Sort by field. Allowed: TIME_CREATED, DISPLAY_NAME"
    ),
    opc_request_id: Optional[str] = Field(
        None, description="Client request ID for tracing."
    ),
) -> list[RefreshActivitySummary]:
    client = get_faaas_client()

    activities: list[RefreshActivitySummary] = []
    next_page: Optional[str] = page
    has_next_page = True

    while has_next_page and (limit is None or len(activities) < limit):
        kwargs: dict[str, Any] = {
            "fusion_environment_id": fusion_environment_id,
            "page": next_page,
            "limit": limit,
        }
        if display_name:
            kwargs["display_name"] = display_name
        if time_scheduled_start_greater_than_or_equal_to:
            kwargs["time_scheduled_start_greater_than_or_equal_to"] = (
                time_scheduled_start_greater_than_or_equal_to
            )
        if time_expected_finish_less_than_or_equal_to:
            kwargs["time_expected_finish_less_than_or_equal_to"] = (
                time_expected_finish_less_than_or_equal_to
            )
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state
        if sort_order:
            kwargs["sort_order"] = sort_order
        if sort_by:
            kwargs["sort_by"] = sort_by
        if opc_request_id:
            kwargs["opc_request_id"] = opc_request_id

        response: oci.response.Response = client.list_refresh_activities(**kwargs)

        data_obj = response.data or []
        items = getattr(data_obj, "items", None)
        iterable = (
            items
            if items is not None
            else (data_obj if isinstance(data_obj, list) else [data_obj])
        )
        for d in iterable:
            mapped = map_refresh_activity_summary(d)
            if mapped:
                activities.append(mapped)
            if limit is not None and len(activities) >= limit:
                break

        has_next_page = getattr(response, "has_next_page", False)
        next_page = getattr(response, "next_page", None)

    return activities


@mcp.tool(description="List all scheduled activities for a FusionEnvironment")
def list_scheduled_activities(
    fusion_environment_id: str = Field(
        ..., description="unique FusionEnvironment identifier"
    ),
    display_name: Optional[str] = Field(
        None,
        description="A filter to return only resources that match the entire display name given.",
    ),
    time_scheduled_start_greater_than_or_equal_to: Optional[datetime] = Field(
        None,
        description="A filter that returns all resources that are scheduled after this date",
    ),
    time_expected_finish_less_than_or_equal_to: Optional[datetime] = Field(
        None,
        description="A filter that returns all resources that end before this date",
    ),
    run_cycle: Optional[Literal["QUARTERLY", "MONTHLY", "ONEOFF", "VERTEX"]] = Field(
        None, description="Filter by run cycle."
    ),
    lifecycle_state: Optional[
        Literal["ACCEPTED", "IN_PROGRESS", "FAILED", "SUCCEEDED", "CANCELED"]
    ] = Field(None, description="Filter by lifecycle state."),
    scheduled_activity_association_id: Optional[str] = Field(
        None, description="Filter by scheduledActivityAssociationId."
    ),
    scheduled_activity_phase: Optional[
        Literal["PRE_MAINTENANCE", "MAINTENANCE", "POST_MAINTENANCE"]
    ] = Field(None, description="Filter by scheduled activity phase."),
    limit: Optional[int] = Field(
        None, description="The maximum number of items to return.", ge=1
    ),
    page: Optional[str] = Field(
        None,
        description="The page token representing the page at which to start retrieving results.",
    ),
    sort_order: Optional[Literal["ASC", "DESC"]] = Field(
        None, description="The sort order to use, either 'ASC' or 'DESC'."
    ),
    sort_by: Optional[Literal["TIME_CREATED", "DISPLAY_NAME"]] = Field(
        None,
        description=("The field to sort by. Allowed: TIME_CREATED, DISPLAY_NAME"),
    ),
    opc_request_id: Optional[str] = Field(
        None, description="The client request ID for tracing."
    ),
    retry_strategy: Optional[Literal["none", "default"]] = Field(
        None,
        description=(
            "Retry strategy to use. Use 'none' to explicitly disable retries "
            "(sets NoneRetryStrategy)."
        ),
    ),
    allow_control_chars: Optional[bool] = Field(
        None,
        description="Whether to allow control characters in the response object.",
    ),
) -> list[ScheduledActivitySummary]:
    client = get_faaas_client()

    activities: list[ScheduledActivitySummary] = []
    next_page: Optional[str] = page
    has_next_page = True

    while has_next_page and (limit is None or len(activities) < limit):
        kwargs: dict[str, Any] = {
            "fusion_environment_id": fusion_environment_id,
            "page": next_page,
            "limit": limit,
        }
        if display_name:
            kwargs["display_name"] = display_name
        if time_scheduled_start_greater_than_or_equal_to:
            kwargs["time_scheduled_start_greater_than_or_equal_to"] = (
                time_scheduled_start_greater_than_or_equal_to
            )
        if time_expected_finish_less_than_or_equal_to:
            kwargs["time_expected_finish_less_than_or_equal_to"] = (
                time_expected_finish_less_than_or_equal_to
            )
        if run_cycle:
            kwargs["run_cycle"] = run_cycle
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state
        if scheduled_activity_association_id:
            kwargs["scheduled_activity_association_id"] = (
                scheduled_activity_association_id
            )
        if scheduled_activity_phase:
            kwargs["scheduled_activity_phase"] = scheduled_activity_phase
        if sort_order:
            kwargs["sort_order"] = sort_order
        if sort_by:
            kwargs["sort_by"] = sort_by
        if opc_request_id:
            kwargs["opc_request_id"] = opc_request_id
        if allow_control_chars is not None:
            kwargs["allow_control_chars"] = allow_control_chars
        if retry_strategy == "none":
            try:
                kwargs["retry_strategy"] = oci.retry.NoneRetryStrategy()
            except Exception:
                pass

        response: oci.response.Response = client.list_scheduled_activities(**kwargs)

        data_obj = response.data or []
        items = getattr(data_obj, "items", None)
        iterable = (
            items
            if items is not None
            else (data_obj if isinstance(data_obj, list) else [data_obj])
        )
        for d in iterable:
            mapped = map_scheduled_activity_summary(d)
            if mapped:
                activities.append(mapped)
            if limit is not None and len(activities) >= limit:
                break

        has_next_page = getattr(response, "has_next_page", False)
        next_page = getattr(response, "next_page", None)

    return activities


@mcp.tool(description="Gets a ScheduledActivity by identifier")
def get_scheduled_activity(
    fusion_environment_id: str = Field(
        ..., description="unique FusionEnvironment identifier"
    ),
    scheduled_activity_id: str = Field(
        ..., description="Unique ScheduledActivity identifier."
    ),
    opc_request_id: Optional[str] = Field(
        None, description="The client request ID for tracing."
    ),
    retry_strategy: Optional[Literal["none", "default"]] = Field(
        None,
        description=(
            "A retry strategy to apply to this operation. "
            "Use 'none' to explicitly disable retries (sets NoneRetryStrategy). "
            "This operation uses DEFAULT_RETRY_STRATEGY as default if no retry strategy is provided."
        ),
    ),
    allow_control_chars: Optional[bool] = Field(
        None,
        description=(
            "Whether to allow control characters in the response object. "
            "By default, control characters are not allowed."
        ),
    ),
) -> ScheduledActivity:
    client = get_faaas_client()

    kwargs = {}
    if opc_request_id:
        kwargs["opc_request_id"] = opc_request_id
    if allow_control_chars is not None:
        kwargs["allow_control_chars"] = allow_control_chars
    if retry_strategy == "none":
        try:
            kwargs["retry_strategy"] = oci.retry.NoneRetryStrategy()
        except Exception:
            # Retry module may not be available in some environments; ignore if unavailable.
            pass

    response: oci.response.Response = client.get_scheduled_activity(
        fusion_environment_id=fusion_environment_id,
        scheduled_activity_id=scheduled_activity_id,
        **kwargs,
    )
    return map_scheduled_activity(response.data)


@mcp.tool(description="Gets the subscription details of a Fusion Environment Family.")
def get_fusion_environment_family_subscription_detail(
    fusion_environment_family_id: str = Field(
        ..., description="The unique identifier (OCID) of the FusionEnvironmentFamily."
    ),
    opc_request_id: Optional[str] = Field(
        None, description="The client request ID for tracing."
    ),
    retry_strategy: Optional[Literal["none", "default"]] = Field(
        None,
        description=(
            "Retry strategy to use. Use 'none' to explicitly disable retries (sets NoneRetryStrategy). "
            "If omitted or 'default', the SDK default/client-level retry strategy is used."
        ),
    ),
    allow_control_chars: Optional[bool] = Field(
        None,
        description="Whether to allow control characters in the response object.",
    ),
) -> SubscriptionDetail:
    client = get_faaas_client()

    kwargs = {}
    if opc_request_id:
        kwargs["opc_request_id"] = opc_request_id
    if allow_control_chars is not None:
        kwargs["allow_control_chars"] = allow_control_chars
    if retry_strategy == "none":
        try:
            kwargs["retry_strategy"] = oci.retry.NoneRetryStrategy()
        except Exception:
            # If retry module not available, skip to maintain compatibility in test environments
            pass

    response: oci.response.Response = (
        client.get_fusion_environment_family_subscription_detail(
            fusion_environment_family_id=fusion_environment_family_id, **kwargs
        )
    )
    return map_subscription_detail(response.data)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
