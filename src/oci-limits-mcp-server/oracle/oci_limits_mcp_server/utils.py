from logging import Logger
from typing import Any, Dict, List, Optional

import oci

logger = Logger(__name__, level="INFO")


def list_services_with_pagination(
    client: oci.limits.LimitsClient,
    compartment_id: str,
    sort_by: str = "name",
    sort_order: str = "ASC",
    limit: Optional[int] = 100,
    page: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> List[oci.limits.models.ServiceSummary]:
    try:
        items: List[oci.limits.models.ServiceSummary] = []
        next_page = page
        has_next_page = True

        while has_next_page:
            response = client.list_services(
                compartment_id=compartment_id,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                page=next_page,
                subscription_id=subscription_id,
            )
            data = response.data or []
            items.extend(data)
            has_next_page = response.has_next_page
            next_page = response.next_page

            if page is not None:
                break

        return items
    except Exception as e:
        logger.error(f"Error in list_services: {e}")
        raise


def list_limit_definitions_with_pagination(
    client: oci.limits.LimitsClient,
    compartment_id: str,
    service_name: Optional[str] = None,
    name: Optional[str] = None,
    sort_by: str = "name",
    sort_order: str = "ASC",
    limit: Optional[int] = 100,
    page: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> List[oci.limits.models.LimitDefinitionSummary]:
    try:
        items: List[oci.limits.models.LimitDefinitionSummary] = []
        next_page = page
        has_next_page = True

        while has_next_page:
            response = client.list_limit_definitions(
                compartment_id=compartment_id,
                service_name=service_name,
                name=name,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                page=next_page,
                subscription_id=subscription_id,
            )
            data = response.data or []
            items.extend(data)
            has_next_page = response.has_next_page
            next_page = response.next_page

            if page is not None:
                break

        return items
    except Exception as e:
        logger.error(f"Error in list_limit_definitions: {e}")
        raise


def list_limit_values_with_pagination(
    client: oci.limits.LimitsClient,
    compartment_id: str,
    service_name: str,
    scope_type: str,
    availability_domain: Optional[str] = None,
    name: Optional[str] = None,
    sort_by: str = "name",
    sort_order: str = "ASC",
    limit: Optional[int] = 100,
    page: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> List[oci.limits.models.LimitValueSummary]:
    try:
        items: List[oci.limits.models.LimitValueSummary] = []
        next_page = page
        has_next_page = True

        while has_next_page:
            response = client.list_limit_values(
                compartment_id=compartment_id,
                service_name=service_name,
                scope_type=scope_type,
                availability_domain=availability_domain,
                name=name,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                page=next_page,
                subscription_id=subscription_id,
            )
            data = response.data or []
            items.extend(data)
            has_next_page = response.has_next_page
            next_page = response.next_page

            if page is not None:
                break

        return items
    except Exception as e:
        logger.error(f"Error in list_limit_values: {e}")
        raise
