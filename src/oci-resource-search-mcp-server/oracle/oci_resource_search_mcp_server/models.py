"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import oci
from pydantic import BaseModel, Field


def _oci_to_dict(obj):
    """Best-effort conversion of OCI SDK model objects to plain dicts."""
    if obj is None:
        return None
    try:
        from oci.util import to_dict as oci_to_dict

        return oci_to_dict(obj)
    except Exception:
        pass
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return None


# region SearchContext


class SearchContext(BaseModel):
    """
    Contains search context, such as highlighting, for found resources.
    """

    highlights: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Describes what in each field matched the search criteria by showing highlighted values, "
        "but only for free text searches or for structured queries that use a MATCHING clause. "
        "The list of strings represents fragments of values that matched the query conditions. "
        "Highlighted values are wrapped with <h1>..</h1> tags. "
        "All values are HTML-encoded (except <h1> tags).",
    )


def map_search_context(sc) -> SearchContext | None:
    if not sc:
        return None
    return SearchContext(highlights=getattr(sc, "highlights", None))


# endregion

# region ResourceSummary


class ResourceSummary(BaseModel):
    """
    A resource that exists in the cloud network that you're querying.
    """

    resource_type: Optional[str] = Field(None, description="The resource type name.")
    identifier: Optional[str] = Field(
        None,
        description="The unique identifier for this particular resource, usually an OCID.",
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment that contains this resource."
    )
    time_created: Optional[datetime] = Field(
        None, description="The time that this resource was created."
    )
    display_name: Optional[str] = Field(
        None, description="The display name (or name) of this resource, if one exists."
    )
    availability_domain: Optional[str] = Field(
        None,
        description="The availability domain where this resource exists, if applicable.",
    )
    lifecycle_state: Optional[str] = Field(
        None, description="The lifecycle state of this resource, if applicable."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description="Free-form tags for this resource. "
        "Each tag is a simple key-value pair with no predefined name, type, or namespace. "
        'For more information, see Resource Tags. Example: {"Department": "Finance"}',
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace."
        'For more information, see Resource Tags. Example: {"Operations": {"CostCenter": "42"}}',
    )
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="System tags associated with this resource, if any. "
        "System tags are set by Oracle Cloud Infrastructure services. "
        "Each key is predefined and scoped to namespaces. For more information, see Resource Tags. "
        "Example: {orcl-cloud: {free-tier-retain: true}}",
    )
    search_context: Optional[SearchContext] = Field(None, description="")
    identity_context: Optional[Dict[str, Any]] = Field(
        None,
        description='Additional identifiers to use together in a "Get" request for a '
        "specified resource, only required for resource types that explicitly "
        "cannot be retrieved by using a single identifier, such as the resource's OCID.",
    )
    additional_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional resource attribute fields of this resource that match queries "
        "with a return clause, if any. For example, if you ran a query to find the private IP addresses, "
        "public IP addresses, and isPrimary field of the VNIC attachment on instance resources, "
        "that field would be included in the ResourceSummary object as: "
        '{"additionalDetails": {"attachedVnic": [{"publicIP" : "172.110.110.110","privateIP" : "10.10.10.10","isPrimary" : true}, {"publicIP" : "172.110.110.111","privateIP" : "10.10.10.11","isPrimary" : false}]}}.'  # noqa
        "The structure of the additional details attribute fields depends on the matching resource.",
    )


def map_resource_summary(
    rs: oci.resource_search.models.ResourceSummary,
) -> ResourceSummary:
    """
    Convert an oci.resource_search.models.ResourceSummary to
    oracle.oci_resource_search_mcp_server.models.ResourceSummary,
    including all nested types.
    """
    return ResourceSummary(
        resource_type=getattr(rs, "resource_type", None),
        identifier=getattr(rs, "identifier", None),
        compartment_id=getattr(rs, "compartment_id", None),
        time_created=getattr(rs, "time_created", None),
        display_name=getattr(rs, "display_name", None),
        availability_domain=getattr(rs, "availability_domain", None),
        lifecycle_state=getattr(rs, "lifecycle_state", None),
        freeform_tags=getattr(rs, "freeform_tags", None),
        defined_tags=getattr(rs, "defined_tags", None),
        system_tags=getattr(rs, "system_tags", None),
        search_context=map_search_context(getattr(rs, "search_context", None)),
        identity_context=getattr(rs, "identity_context", None),
        additional_details=getattr(rs, "additional_details", None),
    )


# endregion
