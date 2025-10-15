"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Annotated, Optional

import oci
from fastmcp import FastMCP

from . import __project__, __version__
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
    Build an OCI IdentityClient using Security Token auth (consistent with other servers in this repo).
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

    # Identity client
    return oci.identity.IdentityClient(config, signer=signer)


# ----------------------------
# Mappers to stable dict shapes
# ----------------------------
def map_service_summary(svc: "oci.limits.models.ServiceSummary") -> dict:
    return {
        "name": getattr(svc, "name", None),
        "description": getattr(svc, "description", None),
        "supported_subscriptions": getattr(svc, "supported_subscriptions", None),
    }


def map_limit_definition_summary(
    defn: "oci.limits.models.LimitDefinitionSummary",
) -> dict:
    return {
        "name": getattr(defn, "name", None),
        "serviceName": getattr(defn, "service_name", None),
        "description": getattr(defn, "description", None),
        "scopeType": getattr(defn, "scope_type", None),
        "areQuotasSupported": getattr(defn, "are_quotas_supported", None),
        "isResourceAvailabilitySupported": getattr(
            defn, "is_resource_availability_supported", None
        ),
        "isDeprecated": getattr(defn, "is_deprecated", None),
        "isEligibleForLimitIncrease": getattr(
            defn, "is_eligible_for_limit_increase", None
        ),
        "isDynamic": getattr(defn, "is_dynamic", None),
        "externalLocationSupportedSubscriptions": getattr(
            defn, "external_location_supported_subscriptions", None
        ),
        "supportedSubscriptions": getattr(defn, "supported_subscriptions", None),
        "supportedQuotaFamilies": getattr(defn, "supported_quota_families", None),
    }


def map_limit_value_summary(val: "oci.limits.models.LimitValueSummary") -> dict:
    return {
        "name": getattr(val, "name", None),
        "scopeType": getattr(val, "scope_type", None),
        "availabilityDomain": getattr(val, "availability_domain", None),
        "value": getattr(val, "value", None),
    }


def map_resource_availability(ra: "oci.limits.models.ResourceAvailability") -> dict:
    return {
        "used": getattr(ra, "used", None),
        "available": getattr(ra, "available", None),
        "fractionalUsage": getattr(ra, "fractional_usage", None),
        "fractionalAvailability": getattr(ra, "fractional_availability", None),
        "effectiveQuotaValue": getattr(ra, "effective_quota_value", None),
    }


def list_availability_domains(compartment_id: str) -> list[dict]:
    client = get_identity_client()
    response = client.list_availability_domains(compartment_id=compartment_id)
    data = response.data
    return [{"name": ad.name, "id": ad.id} for ad in data]


# ----------------------------
# Tools
# ----------------------------


@mcp.tool(
    description="List availability domains for a given compartment needed for limits"
)
def provide_availability_domains_for_limits(
    compartment_id: Annotated[str, "OCID of the compartment"],
) -> list[dict]:
    return list_availability_domains(compartment_id)


@mcp.tool(
    description="Returns the list of supported services that have resource limits exposed"
)
def list_services(
    compartment_id: Annotated[str, "OCID of the root compartment (tenancy)"],
    sort_by: Annotated[str, "Sort field: name or description"] = "name",
    sort_order: Annotated[str, "Sort order: ASC or DESC"] = "ASC",
    limit: Annotated[Optional[int], "Max items per page (1-1000)"] = 100,
    page: Annotated[Optional[str], "Pagination token from a previous call"] = None,
    subscription_id: Annotated[Optional[str], "Subscription OCID filter"] = None,
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
    compartment_id: Annotated[str, "OCID of the root compartment (tenancy)"],
    service_name: Annotated[Optional[str], "Target service name filter"] = None,
    name: Annotated[Optional[str], "Specific resource limit name filter"] = None,
    sort_by: Annotated[str, "Sort field: name or description"] = "name",
    sort_order: Annotated[str, "Sort order: ASC or DESC"] = "ASC",
    limit: Annotated[Optional[int], "Max items per page (1-1000)"] = 100,
    page: Annotated[Optional[str], "Pagination token from a previous call"] = None,
    subscription_id: Annotated[Optional[str], "Subscription OCID filter"] = None,
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


@mcp.tool(
    description="Get the full list of resource limit values for the given service"
)
def get_limit_value(
    compartment_id: Annotated[str, "OCID of the root compartment (tenancy)"],
    service_name: Annotated[str, "Target service name"],
    name: Annotated[str, "Specific resource limit name filter"],
    scope_type: Annotated[str, "Filter by scope type: GLOBAL, REGION, or AD"],
    availability_domain: Annotated[
        Optional[str], "If scope_type is AD, filter by availability domain"
    ] = None,
    sort_by: Annotated[str, "Sort field: name"] = "name",
    sort_order: Annotated[str, "Sort order: ASC or DESC"] = "ASC",
    limit: Annotated[Optional[int], "Max items per page (1-1000)"] = 100,
    page: Annotated[Optional[str], "Pagination token from a previous call"] = None,
    subscription_id: Annotated[Optional[str], "Subscription OCID filter"] = None,
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
        logger.error(f"Error in get_limit_value: {e}")
        raise


@mcp.tool(
    description="Get the availability and usage within a compartment for a given resource limit"
)
def get_resource_availability(
    service_name: Annotated[str, "Service name of the target limit"],
    limit_name: Annotated[str, "Limit name"],
    compartment_id: Annotated[str, "OCID of the compartment to evaluate"],
    availability_domain: Annotated[
        Optional[str],
        "Required if the limit scopeType is AD; omit otherwise. Example: 'US-ASHBURN-AD-1'",
    ] = None,
    subscription_id: Annotated[Optional[str], "Subscription OCID filter"] = None,
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
            return {
                "message": f"Limit '{limit_name}' not found for service '{service_name}'"
            }

        limit_definition = limits[0]
        if not limit_definition.is_resource_availability_supported:
            return {
                "message": f"Resource availability not supported for limit '{limit_name}'. Consider calling get_limit_value to get the limit value."
            }

        if limit_definition.scope_type == "AD":
            availability_domains = list_availability_domains(compartment_id)
            resource_availability = []
            for ad in availability_domains:
                response: oci.response.Response = client.get_resource_availability(
                    service_name=service_name,
                    limit_name=limit_name,
                    compartment_id=compartment_id,
                    availability_domain=ad["name"],
                    subscription_id=subscription_id,
                )
                data: oci.limits.models.ResourceAvailability = response.data
                resource_availability.append(
                    {
                        "availabilityDomain": ad["name"],
                        "resourceAvailability": map_resource_availability(data),
                    }
                )
            return resource_availability
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
