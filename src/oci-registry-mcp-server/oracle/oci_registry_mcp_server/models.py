"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, Literal, Optional

import oci
from pydantic import BaseModel, Field


# Utility function
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


# region ContainerRepository


class ContainerRepositoryReadme(BaseModel):
    """Container repository readme."""

    content: Optional[str] = Field(
        None, description="Readme content. Avoid entering confidential information."
    )
    format: Optional[Literal["TEXT_MARKDOWN", "TEXT_PLAIN", "UNKNOWN_ENUM_VALUE"]] = (
        Field(
            None,
            description="Readme format. Supported formats are text/plain and text/markdown.",
        )
    )


def map_container_repository_readme(readme) -> ContainerRepositoryReadme | None:
    if not readme:
        return None
    return ContainerRepositoryReadme(
        content=getattr(readme, "content", None),
        format=getattr(readme, "format", None),
    )


# Based on oci.artifacts.models.ContainerRepository
class ContainerRepository(BaseModel):
    """
    Pydantic model mirroring the fields of oci.artifacts.models.ContainerRepository.
    Nested OCI model types are represented as Pydantic classes (above).
    """

    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment in which the container repository exists.",
    )
    created_by: Optional[str] = Field(
        None, description="The id of the user or principal that created the resource."
    )
    display_name: Optional[str] = Field(
        None, description="The container repository name."
    )
    id: Optional[str] = Field(None, description="The OCID of the container repository.")
    image_count: Optional[int] = Field(None, description="Total number of images.")
    is_immutable: Optional[bool] = Field(
        None,
        description="Whether the repository is immutable. "
        "Images cannot be overwritten in an immutable repository.",
    )
    is_public: Optional[bool] = Field(
        None,
        description="Whether the repository is public. A public repository allows unauthenticated access.",
    )
    layer_count: Optional[int] = Field(None, description="Total number of layers.")
    layers_size_in_bytes: Optional[int] = Field(
        None, description="Total storage in bytes consumed by layers."
    )
    lifecycle_state: Optional[
        Literal["AVAILABLE", "DELETING", "DELETED", "UNKNOWN_ENUM_VALUE"]
    ] = Field(None, description="The current state of the container repository.")
    readme: Optional[ContainerRepositoryReadme] = Field(
        None, description="The repository readme."
    )
    time_created: Optional[datetime] = Field(
        None,
        description="An RFC 3339 timestamp indicating when the repository was created.",
    )
    time_last_pushed: Optional[datetime] = Field(
        None,
        description="An RFC 3339 timestamp indicating when an image was last pushed to the repository.",
    )
    billable_size_in_gbs: Optional[int] = Field(
        None, description="Total storage size in GBs that will be charged."
    )
    namespace: Optional[str] = Field(
        None, description="The tenancy namespace used in the container repository path."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags for this resource."
    )
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="The system tags for this resource."
    )


def map_container_repository(
    repo: oci.artifacts.models.ContainerRepository,
) -> ContainerRepository:
    """
    Convert an oci.artifacts.models.ContainerRepository to
    oracle.oci_registry_mcp_server.models.ContainerRepository,
    including all nested types.
    """
    return ContainerRepository(
        compartment_id=getattr(repo, "compartment_id", None),
        created_by=getattr(repo, "created_by", None),
        display_name=getattr(repo, "display_name", None),
        id=getattr(repo, "id", None),
        image_count=getattr(repo, "image_count", None),
        is_immutable=getattr(repo, "is_immutable", None),
        is_public=getattr(repo, "is_public", None),
        layer_count=getattr(repo, "layer_count", None),
        layers_size_in_bytes=getattr(repo, "layers_size_in_bytes", None),
        lifecycle_state=getattr(repo, "lifecycle_state", None),
        readme=map_container_repository_readme(getattr(repo, "readme", None)),
        time_created=getattr(repo, "time_created", None),
        time_last_pushed=getattr(repo, "time_last_pushed", None),
        billable_size_in_gbs=getattr(repo, "billable_size_in_gbs", None),
        namespace=getattr(repo, "namespace", None),
        freeform_tags=getattr(repo, "freeform_tags", None),
        defined_tags=getattr(repo, "defined_tags", None),
        system_tags=getattr(repo, "system_tags", None),
    )


# endregion

# region Response (oci.response.Response)


class Request(BaseModel):
    """
    Pydantic model mirroring the fields of oci.request.Request.
    """

    method: Optional[str] = Field(None, description="The HTTP method.")
    url: Optional[str] = Field(None, description="URL that will serve the request.")
    query_params: Optional[Dict[str, Any]] = Field(
        None, description="Query parameters in the URL."
    )
    header_params: Optional[Dict[str, Any]] = Field(
        None, description="Request header parameters."
    )
    body: Optional[Any] = Field(None, description="Request body.")
    response_type: Optional[str] = Field(
        None, description="Expected response data type."
    )
    enforce_content_headers: Optional[bool] = Field(
        None,
        description=(
            "Whether content headers should be added for PUT and POST requests when not present."  # noqa
        ),
    )


class Response(BaseModel):
    """
    Pydantic model mirroring the fields of oci.response.Response.
    Includes derived fields next_page, request_id, and has_next_page.
    """

    status: Optional[int] = Field(None, description="The HTTP status code.")
    headers: Optional[Dict[str, Any]] = Field(
        None, description="The HTTP headers (case-insensitive keys)."
    )
    data: Optional[Any] = Field(
        None, description="The response data. Type depends on the request."
    )
    request: Optional[Request] = Field(
        None, description="The corresponding request for this response."
    )
    next_page: Optional[str] = Field(
        None, description="The value of the opc-next-page response header."
    )
    request_id: Optional[str] = Field(
        None, description="The ID of the request that generated this response."
    )
    has_next_page: Optional[bool] = Field(
        None, description="Whether there is a next page of results."
    )


def map_request(req) -> Request | None:
    if not req:
        return None
    return Request(
        method=getattr(req, "method", None),
        url=getattr(req, "url", None),
        query_params=getattr(req, "query_params", None),
        header_params=getattr(req, "header_params", None),
        body=getattr(req, "body", None),
        response_type=getattr(req, "response_type", None),
        enforce_content_headers=getattr(req, "enforce_content_headers", None),
    )


def _map_headers(headers) -> Dict[str, Any] | None:
    if headers is None:
        return None
    try:
        # requests.structures.CaseInsensitiveDict is convertible to dict
        return dict(headers)
    except Exception:
        try:
            return {k: v for k, v in headers.items()}
        except Exception:
            return _oci_to_dict(headers) or None


def _map_response_data(data: Any) -> Any:
    """
    Best-effort mapping of Response.data to Pydantic-friendly structures.
    Recognizes common repository models; otherwise falls back to to_dict.
    """
    # Handle sequences
    if isinstance(data, (list, tuple)):
        return [_map_response_data(x) for x in data]

    # Already a plain type
    if data is None or isinstance(data, (str, int, float, bool)):
        return data
    if isinstance(data, dict):
        return data

    # Known OCI repository models
    try:
        if isinstance(data, oci.artifacts.models.ContainerRepository):
            return map_container_repository(data)
    except Exception:
        # Ignore import/type detection issues and fall through to generic handling
        pass

    # Fallback: attempt to convert OCI SDK models or other objects to dict
    coerced = _oci_to_dict(data)
    return coerced if coerced is not None else data


def map_response(resp: oci.response.Response) -> Response | None:
    if resp is None:
        return None

    headers = _map_headers(getattr(resp, "headers", None))
    next_page = getattr(resp, "next_page", None)
    request_id = getattr(resp, "request_id", None)

    # Derive from headers if not already present
    if next_page is None and headers is not None:
        next_page = headers.get("opc-next-page")
    if request_id is None and headers is not None:
        request_id = headers.get("opc-request-id")

    return Response(
        status=getattr(resp, "status", None),
        headers=headers,
        data=_map_response_data(getattr(resp, "data", None)),
        request=map_request(getattr(resp, "request", None)),
        next_page=next_page,
        request_id=request_id,
        has_next_page=(next_page is not None),
    )


# endregion
