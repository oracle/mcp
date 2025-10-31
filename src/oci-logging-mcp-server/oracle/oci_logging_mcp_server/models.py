"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

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


# region LogGroupSummary


class LogGroupSummary(BaseModel):
    """
    Pydantic model mirroring the fields of oci.logging.models.LogGroupSummary.
    Note: This OCI model does not contain nested types; all fields are primitives or mappings.
    """

    id: Optional[str] = Field(None, description="The OCID of the log group resource.")
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment that the resource belongs to."
    )
    display_name: Optional[str] = Field(
        None,
        description=(
            "The user-friendly display name. This must be unique within the enclosing resource, "
            "and it's changeable. Avoid entering confidential information."
        ),
    )
    description: Optional[str] = Field(
        None, description="Description for this resource."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description=(
            "Defined tags for this resource. Each key is predefined and scoped to a namespace."
        ),
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, "
            "type, or namespace."
        ),
    )
    time_created: Optional[datetime] = Field(
        None, description="Time the resource was created (RFC3339)."
    )
    time_last_modified: Optional[datetime] = Field(
        None, description="Time the resource was last modified (RFC3339)."
    )
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "ACTIVE",
            "UPDATING",
            "INACTIVE",
            "DELETING",
            "FAILED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The log group object state.")


def map_log_group_summary(
    log_group: oci.logging.models.LogGroupSummary,
) -> LogGroupSummary | None:
    """
    Convert an oci.logging.models.LogGroupSummary to
    oracle.oci_logging_mcp_server.models.LogGroupSummary.
    """
    if log_group is None:
        return None

    # Best-effort dict extraction (not strictly required here, but consistent with other servers)
    _ = _oci_to_dict(log_group)  # noqa: F841

    return LogGroupSummary(
        id=getattr(log_group, "id", None),
        compartment_id=getattr(log_group, "compartment_id", None),
        display_name=getattr(log_group, "display_name", None),
        description=getattr(log_group, "description", None),
        defined_tags=getattr(log_group, "defined_tags", None),
        freeform_tags=getattr(log_group, "freeform_tags", None),
        time_created=getattr(log_group, "time_created", None),
        time_last_modified=getattr(log_group, "time_last_modified", None),
        lifecycle_state=getattr(log_group, "lifecycle_state", None),
    )


# endregion

# region LogGroup


class LogGroup(BaseModel):
    """
    Pydantic model mirroring the fields of oci.logging.models.LogGroup.
    Note: This OCI model does not contain nested types; all fields are primitives or mappings.
    """

    id: Optional[str] = Field(None, description="The OCID of the resource.")
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment that the resource belongs to."
    )
    display_name: Optional[str] = Field(
        None,
        description=(
            "The user-friendly display name. This must be unique within the enclosing resource, "
            "and it's changeable. Avoid entering confidential information."
        ),
    )
    description: Optional[str] = Field(
        None, description="Description for this resource."
    )
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "ACTIVE",
            "UPDATING",
            "INACTIVE",
            "DELETING",
            "FAILED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The log group object state.")
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description=(
            "Defined tags for this resource. Each key is predefined and scoped to a namespace."
        ),
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "Free-form tags for this resource. Each tag is a simple key-value pair with no predefined name, "
            "type, or namespace."
        ),
    )
    time_created: Optional[datetime] = Field(
        None, description="Time the resource was created (RFC3339)."
    )
    time_last_modified: Optional[datetime] = Field(
        None, description="Time the resource was last modified (RFC3339)."
    )


def map_log_group(
    log_group: oci.logging.models.LogGroup,
) -> LogGroup | None:
    """
    Convert an oci.logging.models.LogGroup to
    oracle.oci_logging_mcp_server.models.LogGroup.
    """
    if log_group is None:
        return None

    return LogGroup(
        id=getattr(log_group, "id", None),
        compartment_id=getattr(log_group, "compartment_id", None),
        display_name=getattr(log_group, "display_name", None),
        description=getattr(log_group, "description", None),
        lifecycle_state=getattr(log_group, "lifecycle_state", None),
        defined_tags=getattr(log_group, "defined_tags", None),
        freeform_tags=getattr(log_group, "freeform_tags", None),
        time_created=getattr(log_group, "time_created", None),
        time_last_modified=getattr(log_group, "time_last_modified", None),
    )


# endregion

# region LogSummary


class Archiving(BaseModel):
    """Log archiving configuration."""

    is_enabled: Optional[bool] = Field(
        None,
        description="True if archiving is enabled. Deprecated; prefer Service Connector Hub.",
    )


class Source(BaseModel):
    """
    Base model for log source.
    Mirrors oci.logging.models.Source discriminator.
    """

    source_type: Optional[Literal["OCISERVICE", "UNKNOWN_ENUM_VALUE"]] = Field(
        None, description="The log source type."
    )


class OciService(Source):
    """
    OCI service logging configuration (subtype of Source).
    Mirrors oci.logging.models.OciService.
    """

    service: Optional[str] = Field(None, description="Service generating the log.")
    resource: Optional[str] = Field(
        None, description="Unique identifier of the resource emitting the log."
    )
    category: Optional[str] = Field(None, description="Log object category.")
    parameters: Optional[Dict[str, str]] = Field(
        None, description="Log category parameters."
    )


class Configuration(BaseModel):
    """
    Log object configuration.
    Mirrors oci.logging.models.Configuration.
    """

    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment that the resource belongs to."
    )
    source: Optional[Source] = Field(
        None, description="The source the log object comes from."
    )
    archiving: Optional[Archiving] = Field(
        None, description="Log archiving configuration."
    )


class LogSummary(BaseModel):
    """
    Pydantic model mirroring the fields of oci.logging.models.LogSummary.
    Includes nested types: Configuration -> (Source|OciService, Archiving).
    """

    id: Optional[str] = Field(None, description="The OCID of the resource.")
    log_group_id: Optional[str] = Field(None, description="Log group OCID.")
    display_name: Optional[str] = Field(
        None,
        description=(
            "The user-friendly display name. This must be unique within the enclosing resource, "
            "and it's changeable. Avoid entering confidential information."
        ),
    )
    is_enabled: Optional[bool] = Field(
        None, description="Whether or not this resource is currently enabled."
    )
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "ACTIVE",
            "UPDATING",
            "INACTIVE",
            "DELETING",
            "FAILED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The pipeline state.")
    log_type: Optional[Literal["CUSTOM", "SERVICE", "UNKNOWN_ENUM_VALUE"]] = Field(
        None,
        description="The logType that the log object is for, whether custom or service.",
    )
    configuration: Optional[Configuration] = Field(
        None, description="Log object configuration."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description="Free-form tags for this resource as simple key/value pairs without predefined names.",
    )
    time_created: Optional[datetime] = Field(
        None, description="Time the resource was created (RFC3339)."
    )
    time_last_modified: Optional[datetime] = Field(
        None, description="Time the resource was last modified (RFC3339)."
    )
    retention_duration: Optional[int] = Field(
        None,
        description="Log retention duration in 30-day increments (30, 60, 90, ... up to 180).",
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment that the resource belongs to."
    )


def map_archiving(arch) -> Archiving | None:
    if not arch:
        return None
    return Archiving(is_enabled=getattr(arch, "is_enabled", None))


def map_source(src) -> Source | None:
    if not src:
        return None
    # Prefer explicit subtype mapping when possible
    try:
        if isinstance(src, oci.logging.models.OciService):
            return OciService(
                source_type=getattr(src, "source_type", None),
                service=getattr(src, "service", None),
                resource=getattr(src, "resource", None),
                category=getattr(src, "category", None),
                parameters=getattr(src, "parameters", None),
            )
    except Exception:
        # If SDK classes are not importable in this environment, fall through to generic mapping
        pass
    return Source(source_type=getattr(src, "source_type", None))


def map_configuration(cfg) -> Configuration | None:
    if not cfg:
        return None
    return Configuration(
        compartment_id=getattr(cfg, "compartment_id", None),
        source=map_source(getattr(cfg, "source", None)),
        archiving=map_archiving(getattr(cfg, "archiving", None)),
    )


def map_log_summary(log: oci.logging.models.LogSummary) -> LogSummary | None:
    """
    Convert an oci.logging.models.LogSummary to
    oracle.oci_logging_mcp_server.models.LogSummary, including nested types.
    """
    if log is None:
        return None

    return LogSummary(
        id=getattr(log, "id", None),
        log_group_id=getattr(log, "log_group_id", None),
        display_name=getattr(log, "display_name", None),
        is_enabled=getattr(log, "is_enabled", None),
        lifecycle_state=getattr(log, "lifecycle_state", None),
        log_type=getattr(log, "log_type", None),
        configuration=map_configuration(getattr(log, "configuration", None)),
        defined_tags=getattr(log, "defined_tags", None),
        freeform_tags=getattr(log, "freeform_tags", None),
        time_created=getattr(log, "time_created", None),
        time_last_modified=getattr(log, "time_last_modified", None),
        retention_duration=getattr(log, "retention_duration", None),
        compartment_id=getattr(log, "compartment_id", None),
    )


# endregion

# region Log


class Log(BaseModel):
    """
    Pydantic model mirroring the fields of oci.logging.models.Log.
    Includes nested types: Configuration -> (Source|OciService, Archiving).
    """

    id: Optional[str] = Field(None, description="The OCID of the resource.")
    tenancy_id: Optional[str] = Field(None, description="The OCID of the tenancy.")
    log_group_id: Optional[str] = Field(None, description="Log group OCID.")
    display_name: Optional[str] = Field(
        None,
        description=(
            "The user-friendly display name. This must be unique within the enclosing resource, "
            "and it's changeable. Avoid entering confidential information."
        ),
    )
    log_type: Optional[Literal["CUSTOM", "SERVICE", "UNKNOWN_ENUM_VALUE"]] = Field(
        None,
        description="The logType that the log object is for, whether custom or service.",
    )
    is_enabled: Optional[bool] = Field(
        None, description="Whether or not this resource is currently enabled."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description="Free-form tags for this resource as simple key/value pairs without predefined names.",
    )
    configuration: Optional[Configuration] = Field(
        None, description="Log object configuration."
    )
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "ACTIVE",
            "UPDATING",
            "INACTIVE",
            "DELETING",
            "FAILED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The pipeline state.")
    time_created: Optional[datetime] = Field(
        None, description="Time the resource was created (RFC3339)."
    )
    time_last_modified: Optional[datetime] = Field(
        None, description="Time the resource was last modified (RFC3339)."
    )
    retention_duration: Optional[int] = Field(
        None,
        description="Log retention duration in 30-day increments (30, 60, 90, ... up to 180).",
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment that the resource belongs to."
    )


def map_log(log: oci.logging.models.Log) -> Log | None:
    """
    Convert an oci.logging.models.Log to
    oracle.oci_logging_mcp_server.models.Log, including nested types.
    """
    if log is None:
        return None

    return Log(
        id=getattr(log, "id", None),
        tenancy_id=getattr(log, "tenancy_id", None),
        log_group_id=getattr(log, "log_group_id", None),
        display_name=getattr(log, "display_name", None),
        log_type=getattr(log, "log_type", None),
        is_enabled=getattr(log, "is_enabled", None),
        defined_tags=getattr(log, "defined_tags", None),
        freeform_tags=getattr(log, "freeform_tags", None),
        configuration=map_configuration(getattr(log, "configuration", None)),
        lifecycle_state=getattr(log, "lifecycle_state", None),
        time_created=getattr(log, "time_created", None),
        time_last_modified=getattr(log, "time_last_modified", None),
        retention_duration=getattr(log, "retention_duration", None),
        compartment_id=getattr(log, "compartment_id", None),
    )


# endregion

# region SearchResponse


class FieldInfo(BaseModel):
    """Contains field schema information."""

    field_name: Optional[str] = Field(None, description="Field name")
    field_type: Optional[Literal["STRING", "NUMBER", "BOOLEAN", "ARRAY"]] = Field(
        None,
        description="Field type - STRING: A sequence of characters. "
        "NUMBER: Numeric type which can be an integer or floating point. "
        "BOOLEAN: Either true or false. "
        "ARRAY: An ordered collection of values.",
    )


class SearchResult(BaseModel):
    """A log search result entry."""

    data: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON blob containing the search entry with the projected fields.",
    )


class SearchResultSummary(BaseModel):
    """Summary of results."""

    result_count: Optional[int] = Field(
        None, description="Total number of search results."
    )
    field_count: Optional[int] = Field(
        None, description="Total number of field schema information."
    )


class SearchResponse(BaseModel):
    """Search response object."""

    results: Optional[List[SearchResult]] = Field(
        None, description="List of search results"
    )
    fields: Optional[List[FieldInfo]] = Field(
        None, description="List of log field schema information."
    )
    summary: Optional[SearchResultSummary] = Field(
        None, description="Summary of results."
    )


def map_field_info(fi) -> FieldInfo | None:
    if not fi:
        return None
    return FieldInfo(
        field_name=getattr(fi, "field_name", None),
        field_type=getattr(fi, "field_type", None),
    )


def map_search_result(sr) -> SearchResult | None:
    if not sr:
        return None
    return SearchResult(data=_oci_to_dict(getattr(sr, "data", None)))


def map_search_result_summary(srs) -> SearchResultSummary | None:
    if not srs:
        return None
    return SearchResultSummary(
        result_count=getattr(srs, "result_count", None),
        field_count=getattr(srs, "field_count", None),
    )


def map_search_response(
    sr: oci.loggingsearch.models.SearchResponse,
) -> SearchResponse | None:
    if not sr:
        return None
    return SearchResponse(
        results=[map_search_result(r) for r in getattr(sr, "results", None) or []],
        fields=[map_field_info(f) for f in getattr(sr, "fields", None) or []],
        summary=map_search_result_summary(getattr(sr, "summary", None)),
    )


# endregion
