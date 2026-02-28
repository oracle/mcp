"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Literal, Optional

import oci
from fastmcp import FastMCP
from pydantic import Field

from . import __project__, __version__
from .models import (
    map_limit_definition_summary,
    map_limit_value_summary,
    map_resource_availability,
    map_service_summary,
)
from .utils import (
    list_limit_definitions_with_pagination,
    list_limit_values_with_pagination,
    list_services_with_pagination,
)

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_limits_client():
    """
    Build an OCI LimitsClient using Security Token auth (consistent with other servers in this repo).
    Honors OCI_CONFIG_PROFILE if set. Adds a product-specific user agent.
    """
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    # Security token signer (same pattern as compute/identity)
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)

    # Limits client
    return oci.limits.LimitsClient(config, signer=signer)


def get_identity_client():
    """
    Deprecated: This server no longer constructs an Identity client.
    For identity-related data (e.g., availability domains), use the oracle-identity-mcp-server tools.
    """
    raise NotImplementedError(
        "Use oracle-identity-mcp-server tools for Identity operations (e.g., list_availability_domains)."
    )


# ----------------------------
# Tools
# ----------------------------


@mcp.tool(
    description=(
        "Redirect shim: Use oracle-identity-mcp-server.list_availability_domains. "
        "This tool does not query Identity and will instruct the MCP host to call the Identity tool."
    )
)
def provide_availability_domains_for_limits(
    compartment_id: str = Field(..., description="OCID of the compartment (tenancy)")
) -> list[dict]:
    """
    This is a non-fetching shim to guide orchestration. It avoids duplicating Identity logic
    and returns a structured hint for the MCP host to call the correct tool.
    """
    return [
        {
            "message": (
                "Call oracle-identity-mcp-server.list_availability_domains with tenancy_id=the tenancy OCID. "
                "Then pass one of the returned AD names to get_resource_availability when scopeType is AD."
            ),
            "redirect": {
                "server": "oracle.oci-identity-mcp-server",
                "tool": "list_availability_domains",
                "args": {"tenancy_id": compartment_id},
            },
        }
    ]


@mcp.tool(
    description="Returns the list of supported services that have resource limits exposed"
)
def list_services(
    compartment_id: str = Field(
        ..., description="OCID of the root compartment (tenancy)"
    ),
    sort_by: Literal["name", "description"] = Field("name", description="Sort field"),
    sort_order: Literal["ASC", "DESC"] = Field("ASC", description="Sort order"),
    limit: Optional[int] = Field(
        None,
        description="Max items per page (1-1000). If None, service default page size is used.",
        ge=1,
        le=1000,
    ),
    page: Optional[str] = Field(
        None, description="Pagination token from a previous call"
    ),
    subscription_id: Optional[str] = Field(
        None, description="Subscription OCID filter"
    ),
) -> list[dict]:
    """
    Maps to GET /20190729/services
    """
    try:
        client = get_limits_client()
        services = list_services_with_pagination(
            client,
            compartment_id=compartment_id,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            page=page,
            subscription_id=subscription_id,
        )
        service_summary = [map_service_summary(svc) for svc in services]
        return service_summary
    except Exception as e:
        logger.error(f"Error in list_services: {e}")
        raise


@mcp.tool(description="Get the list of resource limit definitions for a service")
def list_limit_definitions(
    compartment_id: str = Field(
        ..., description="OCID of the root compartment (tenancy)"
    ),
    service_name: Optional[str] = Field(None, description="Target service name filter"),
    name: Optional[str] = Field(
        None, description="Specific resource limit name filter"
    ),
    sort_by: Literal["name", "description"] = Field("name", description="Sort field"),
    sort_order: Literal["ASC", "DESC"] = Field("ASC", description="Sort order"),
    limit: Optional[int] = Field(
        None,
        description="Max items per page (1-1000). If None, service default page size is used.",
        ge=1,
        le=1000,
    ),
    page: Optional[str] = Field(
        None, description="Pagination token from a previous call"
    ),
    subscription_id: Optional[str] = Field(
        None, description="Subscription OCID filter"
    ),
) -> list[dict]:
    """
    Maps to GET /20190729/limitDefinitions
    """
    try:
        client = get_limits_client()
        items = list_limit_definitions_with_pagination(
            client,
            compartment_id=compartment_id,
            service_name=service_name,
            name=name,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            page=page,
            subscription_id=subscription_id,
        )
        return [map_limit_definition_summary(d) for d in items]
    except Exception as e:
        logger.error(f"Error in list_limit_definitions: {e}")
        raise


@mcp.tool(description="List resource limit values for the given service")
def list_limit_value(
    compartment_id: str = Field(
        ..., description="OCID of the root compartment (tenancy)"
    ),
    service_name: str = Field(..., description="Target service name"),
    name: str = Field(..., description="Specific resource limit name filter"),
    scope_type: Literal["GLOBAL", "REGION", "AD"] = Field(
        ..., description="Scope type"
    ),
    availability_domain: Optional[str] = Field(
        None, description="If scope_type is AD, filter by availability domain"
    ),
    sort_by: Literal["name"] = Field("name", description="Sort field"),
    sort_order: Literal["ASC", "DESC"] = Field("ASC", description="Sort order"),
    limit: Optional[int] = Field(
        None,
        description="Max items per page (1-1000). If None, service default page size is used.",
        ge=1,
        le=1000,
    ),
    page: Optional[str] = Field(
        None, description="Pagination token from a previous call"
    ),
    subscription_id: Optional[str] = Field(
        None, description="Subscription OCID filter"
    ),
) -> list[dict]:
    """
    Maps to GET /20190729/limitValues
    """
    try:
        client = get_limits_client()
        items = list_limit_values_with_pagination(
            client,
            compartment_id=compartment_id,
            service_name=service_name,
            scope_type=scope_type,
            availability_domain=availability_domain,
            name=name,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            page=page,
            subscription_id=subscription_id,
        )
        return [map_limit_value_summary(d) for d in items]
    except Exception as e:
        logger.error(f"Error in list_limit_value: {e}")
        raise


@mcp.tool(
    description=(
        "Get the availability and usage for a resource limit. For AD-scoped limits, "
        "you must provide availability_domain. Use oracle-identity-mcp-server.list_availability_domains "
        "to discover valid AD names, then pass one here."
    )
)
def get_resource_availability(
    service_name: str = Field(..., description="Service name of the target limit"),
    limit_name: str = Field(..., description="Limit name"),
    compartment_id: str = Field(..., description="OCID of the compartment to evaluate"),
    availability_domain: Optional[str] = Field(
        None,
        description=(
            "Required if the limit scopeType is AD; omit otherwise. Example: 'US-ASHBURN-AD-1'"
        ),
    ),
    subscription_id: Optional[str] = Field(
        None, description="Subscription OCID filter"
    ),
) -> list[dict]:
    """
    Maps to GET /20190729/services/{serviceName}/limits/{limitName}/resourceAvailability
    """
    try:
        client = get_limits_client()
        limits = list_limit_definitions_with_pagination(
            client,
            compartment_id=compartment_id,
            service_name=service_name,
            name=limit_name,
        )
        if len(limits) == 0:
            return [
                {
                    "message": f"Limit '{limit_name}' not found for service '{service_name}'"
                }
            ]

        limit_definition = limits[0]
        if not limit_definition.is_resource_availability_supported:
            return [
                {
                    "message": f"Resource availability not supported for limit '{limit_name}'. "
                    f"Consider calling list_limit_value to get the limit value."
                }
            ]

        if limit_definition.scope_type == "AD":
            if not availability_domain:
                # Return a structured redirect hint instead of raising, so MCP hosts can chain to Identity
                return [
                    {
                        "message": (
                            "availability_domain is required for AD-scoped limits. "
                            "Call oracle-identity-mcp-server.list_availability_domains first,then retry"
                        ),
                        "redirect": {
                            "server": "oracle.oci-identity-mcp-server",
                            "tool": "list_availability_domains",
                            "args": {"tenancy_id": compartment_id},
                        },
                    }
                ]
            response: oci.response.Response = client.get_resource_availability(
                service_name=service_name,
                limit_name=limit_name,
                compartment_id=compartment_id,
                availability_domain=availability_domain,
                subscription_id=subscription_id,
            )
            data: oci.limits.models.ResourceAvailability = response.data
            return [
                {
                    "availabilityDomain": availability_domain,
                    "resourceAvailability": map_resource_availability(data),
                }
            ]
        else:
            response: oci.response.Response = client.get_resource_availability(
                service_name=service_name,
                limit_name=limit_name,
                compartment_id=compartment_id,
                availability_domain=availability_domain,
                subscription_id=subscription_id,
            )
            data: oci.limits.models.ResourceAvailability = response.data
            return [map_resource_availability(data)]
    except Exception as e:
        logger.error(f"Error in get_resource_availability: {e}")
        raise


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
