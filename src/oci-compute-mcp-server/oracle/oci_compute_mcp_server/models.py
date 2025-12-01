"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import oci
from pydantic import BaseModel, Field

# Nested OCI models represented as Pydantic classes


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


# region Instance


class PlacementConstraintDetails(BaseModel):
    """Placement constraint details (shape- or cluster-related policies)."""

    strategy: Optional[str] = Field(
        None,
        description="Placement strategy/policy identifier (e.g., anti-affinity, cluster).",  # noqa
    )
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional placement constraint details."
    )


class LaunchOptions(BaseModel):
    """Launch options for VM instances."""

    boot_volume_type: Optional[str] = Field(
        None, description="Boot volume attachment type."
    )
    firmware: Optional[str] = Field(
        None, description="Firmware type to use when launching instances."
    )
    network_type: Optional[str] = Field(
        None, description="Network attachment type for VNIC."
    )
    remote_data_volume_type: Optional[str] = Field(
        None, description="Data volume attachment type."
    )
    is_pv_encryption_in_transit_enabled: Optional[bool] = Field(
        None,
        description="Whether paravirtualized volume encryption in transit is enabled.",
    )
    is_consistent_volume_naming_enabled: Optional[bool] = Field(
        None, description="Whether consistent volume/device naming is enabled."
    )


class InstanceOptions(BaseModel):
    """Instance-level options."""

    are_legacy_imds_endpoints_disabled: Optional[bool] = Field(
        None, description="Disable legacy IMDS endpoints."
    )


class InstanceAvailabilityConfig(BaseModel):
    """Availability configuration for the instance."""

    is_live_migration_preferred: Optional[bool] = Field(
        None, description="Preference for live migration versus reboot."
    )
    recovery_action: Optional[str] = Field(
        None,
        description="Action when host fails (e.g., RESTORE_INSTANCE, STOP_INSTANCE).",
    )
    is_pmu_enabled: Optional[bool] = Field(
        None, description="Whether PMU is enabled (platform-dependent)."
    )


class PreemptibleInstanceConfigDetails(BaseModel):
    """Configuration for preemptible instances."""

    preemption_action: Optional[Dict[str, Any]] = Field(
        None, description="Action taken when preempted (e.g., terminate)."
    )


class InstanceShapeConfig(BaseModel):
    """Shape configuration describing CPU/Memory resources."""

    ocpus: Optional[float] = Field(None, description="Number of OCPUs allocated.")
    memory_in_gbs: Optional[float] = Field(None, description="Memory size in GB.")
    vcpus: Optional[int] = Field(None, description="Number of virtual CPUs.")
    baseline_ocpu_utilization: Optional[str] = Field(
        None,
        description="Baseline OCPU utilization (e.g., BASELINE_1_1, BASELINE_1_2).",
    )
    nvmes: Optional[int] = Field(None, description="Number of local NVMe drives.")
    local_disks: Optional[int] = Field(None, description="Number of local disks.")
    local_disks_total_size_in_gbs: Optional[float] = Field(
        None, description="Total local disk size in GB."
    )


class InstanceSourceDetails(BaseModel):
    """Source details used for instance creation."""

    source_type: Optional[str] = Field(
        None, description="Type of source (e.g., image, bootVolume)."
    )
    image_id: Optional[str] = Field(None, description="Image OCID.")
    boot_volume_size_in_gbs: Optional[int] = Field(
        None, description="Boot volume size in GB."
    )


class InstanceAgentConfig(BaseModel):
    """Oracle Cloud Agent configuration."""

    is_monitoring_disabled: Optional[bool] = Field(
        None, description="Disable monitoring plugins."
    )
    is_management_disabled: Optional[bool] = Field(
        None, description="Disable management plugins."
    )
    are_all_plugins_disabled: Optional[bool] = Field(
        None, description="Disable all plugins."
    )
    plugins_config: Optional[List[Dict[str, Any]]] = Field(
        None, description="Per-plugin configuration list."
    )


class PlatformConfig(BaseModel):
    """Platform configuration (CPU vendor, firmware, etc.)."""

    type: Optional[str] = Field(
        None,
        description="Platform config discriminator (e.g., AMD_VM, INTEL_VM, AARCH64_VM).",  # noqa
    )
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional platform-specific details."
    )


class LicensingConfig(BaseModel):
    """Licensing configuration associated with the instance."""

    license_type: Optional[str] = Field(None, description="License type or SKU.")
    is_vendor_oracle: Optional[bool] = Field(
        None, description="Whether Oracle is the license vendor."
    )
    is_bring_your_own_license: Optional[bool] = Field(
        None, description="Whether BYOL is used."
    )


# Based on oci.core.Instance
class Instance(BaseModel):
    """
    Pydantic model mirroring the fields of oci.core.Instance.
    Nested OCI model types are represented as Pydantic classes (above).
    """

    availability_domain: Optional[str] = Field(
        None, description="The availability domain the instance is running in."
    )
    capacity_reservation_id: Optional[str] = Field(
        None,
        description=(
            "The OCID of the compute capacity reservation this instance is launched under. "  # noqa
            "Empty or null means not currently in a capacity reservation."
        ),
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment that contains the instance."
    )
    placement_constraint_details: Optional[PlacementConstraintDetails] = Field(
        None, description="Placement constraint details."
    )
    cluster_placement_group_id: Optional[str] = Field(
        None, description="The OCID of the cluster placement group of the instance."
    )
    dedicated_vm_host_id: Optional[str] = Field(
        None,
        description="The OCID of the dedicated virtual machine host that the instance is placed on.",  # noqa
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",  # noqa
    )
    security_attributes: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Security attributes for Zero Trust Packet Routing (ZPR), labeled by namespace.",  # noqa
    )
    security_attributes_state: Optional[
        Literal["STABLE", "UPDATING", "UNKNOWN_ENUM_VALUE"]
    ] = Field(None, description="The lifecycle state of the securityAttributes.")
    display_name: Optional[str] = Field(
        None, description="A user-friendly name. Does not have to be unique."
    )
    extended_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata key/value pairs; may contain nested JSON objects.",  # noqa
    )
    fault_domain: Optional[str] = Field(
        None, description="The name of the fault domain the instance is running in."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource as simple key/value pairs."
    )
    id: Optional[str] = Field(None, description="The OCID of the instance.")
    image_id: Optional[str] = Field(
        None, description="Deprecated. Use sourceDetails instead."
    )
    ipxe_script: Optional[str] = Field(
        None,
        description="Custom iPXE script to run when the instance boots. Not used for paravirtualized boot volumes.",  # noqa
    )
    launch_mode: Optional[
        Literal["NATIVE", "EMULATED", "PARAVIRTUALIZED", "CUSTOM", "UNKNOWN_ENUM_VALUE"]
    ] = Field(None, description="Configuration mode for launching VM instances.")
    launch_options: Optional[LaunchOptions] = Field(None, description="Launch options.")
    instance_options: Optional[InstanceOptions] = Field(
        None, description="Instance options."
    )
    availability_config: Optional[InstanceAvailabilityConfig] = Field(
        None, description="Availability configuration."
    )
    preemptible_instance_config: Optional[PreemptibleInstanceConfigDetails] = Field(
        None, description="Preemptible instance configuration details."
    )
    lifecycle_state: Optional[
        Literal[
            "MOVING",
            "PROVISIONING",
            "RUNNING",
            "STARTING",
            "STOPPING",
            "STOPPED",
            "CREATING_IMAGE",
            "TERMINATING",
            "TERMINATED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The current lifecycle state of the instance.")
    metadata: Optional[Dict[str, str]] = Field(
        None, description="Custom metadata that you provide."
    )
    region: Optional[str] = Field(
        None,
        description="The region that contains the availability domain the instance is running in.",  # noqa
    )
    shape: Optional[str] = Field(
        None,
        description="The shape of the instance. Determines CPU and memory allocated.",
    )
    shape_config: Optional[InstanceShapeConfig] = Field(
        None, description="Instance shape configuration."
    )
    is_cross_numa_node: Optional[bool] = Field(
        None,
        description="Whether the instance’s OCPUs and memory are distributed across multiple NUMA nodes.",  # noqa
    )
    source_details: Optional[InstanceSourceDetails] = Field(
        None,
        description="Details for creating the instance's source (image/boot volume).",
    )
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="System tags for this resource, scoped to namespaces."
    )
    time_created: Optional[datetime] = Field(
        None, description="The date and time the instance was created (RFC3339)."
    )
    agent_config: Optional[InstanceAgentConfig] = Field(
        None, description="Instance agent configuration."
    )
    time_maintenance_reboot_due: Optional[datetime] = Field(
        None,
        description="The date and time the instance is expected to be stopped/started (RFC3339).",  # noqa
    )
    platform_config: Optional[PlatformConfig] = Field(
        None, description="Platform configuration."
    )
    instance_configuration_id: Optional[str] = Field(
        None,
        description="The OCID of the Instance Configuration used to source launch details for this instance.",  # noqa
    )
    licensing_configs: Optional[List[LicensingConfig]] = Field(
        None,
        description="List of licensing configurations associated with the instance.",
    )


def map_placement_constraint_details(pcd) -> PlacementConstraintDetails | None:
    if not pcd:
        return None
    data = _oci_to_dict(pcd) or {}
    strategy = data.pop("strategy", getattr(pcd, "strategy", None))
    # Remaining keys are treated as additional details
    details = data or getattr(pcd, "details", None)
    return PlacementConstraintDetails(strategy=strategy, details=details)


def map_launch_options(lo) -> LaunchOptions | None:
    if not lo:
        return None
    return LaunchOptions(
        boot_volume_type=getattr(lo, "boot_volume_type", None),
        firmware=getattr(lo, "firmware", None),
        network_type=getattr(lo, "network_type", None),
        remote_data_volume_type=getattr(lo, "remote_data_volume_type", None),
        is_pv_encryption_in_transit_enabled=getattr(
            lo, "is_pv_encryption_in_transit_enabled", None
        ),
        is_consistent_volume_naming_enabled=getattr(
            lo, "is_consistent_volume_naming_enabled", None
        ),
    )


def map_instance_options(io) -> InstanceOptions | None:
    if not io:
        return None
    return InstanceOptions(
        are_legacy_imds_endpoints_disabled=getattr(
            io, "are_legacy_imds_endpoints_disabled", None
        )
    )


def map_availability_config(ac) -> InstanceAvailabilityConfig | None:
    if not ac:
        return None
    return InstanceAvailabilityConfig(
        is_live_migration_preferred=getattr(ac, "is_live_migration_preferred", None),
        recovery_action=getattr(ac, "recovery_action", None),
        is_pmu_enabled=getattr(ac, "is_pmu_enabled", None),
    )


def map_preemptible_config(pc) -> PreemptibleInstanceConfigDetails | None:
    if not pc:
        return None
    # preemption_action may itself be an OCI model; coerce to dict
    return PreemptibleInstanceConfigDetails(
        preemption_action=_oci_to_dict(getattr(pc, "preemption_action", None))
    )


def map_shape_config(sc) -> InstanceShapeConfig | None:
    if not sc:
        return None
    return InstanceShapeConfig(
        ocpus=getattr(sc, "ocpus", None),
        memory_in_gbs=getattr(sc, "memory_in_gbs", None),
        vcpus=getattr(sc, "vcpus", None),
        baseline_ocpu_utilization=getattr(sc, "baseline_ocpu_utilization", None),
        nvmes=getattr(sc, "nvmes", None),
        local_disks=getattr(sc, "local_disks", None),
        local_disks_total_size_in_gbs=getattr(
            sc, "local_disks_total_size_in_gbs", None
        ),
    )


def map_source_details(sd) -> InstanceSourceDetails | None:
    if not sd:
        return None
    return InstanceSourceDetails(
        source_type=getattr(sd, "source_type", None),
        image_id=getattr(sd, "image_id", None),
        boot_volume_size_in_gbs=getattr(sd, "boot_volume_size_in_gbs", None),
    )


def map_agent_config(acfg) -> InstanceAgentConfig | None:
    if not acfg:
        return None
    plugins = getattr(acfg, "plugins_config", None)
    if plugins is not None:
        try:
            plugins = [_oci_to_dict(p) for p in plugins]
        except Exception:
            plugins = None
    return InstanceAgentConfig(
        is_monitoring_disabled=getattr(acfg, "is_monitoring_disabled", None),
        is_management_disabled=getattr(acfg, "is_management_disabled", None),
        are_all_plugins_disabled=getattr(acfg, "are_all_plugins_disabled", None),
        plugins_config=plugins,
    )


def map_platform_config(pc) -> PlatformConfig | None:
    if not pc:
        return None
    data = _oci_to_dict(pc) or {}
    pc_type = getattr(pc, "type", None) or data.get("type")
    # Exclude the discriminator from details to avoid duplication
    if "type" in data:
        data.pop("type", None)
    details = data or getattr(pc, "details", None)
    return PlatformConfig(type=pc_type, details=details)


def map_licensing_configs(items) -> list[LicensingConfig] | None:
    if not items:
        return None
    result: list[LicensingConfig] = []
    for it in items:
        data = _oci_to_dict(it) or {}
        result.append(
            LicensingConfig(
                license_type=getattr(it, "license_type", None)
                or data.get("license_type"),
                is_vendor_oracle=getattr(it, "is_vendor_oracle", None)
                or data.get("is_vendor_oracle"),
                is_bring_your_own_license=getattr(it, "is_bring_your_own_license", None)
                or data.get("is_bring_your_own_license"),
            )
        )
    return result


def map_instance(
    instance_data: oci.core.models.Instance,
) -> Instance:
    """
    Convert an oci.core.models.Instance to oracle.oci_compute_mcp_server.Instance,
    including all nested types.
    """
    return Instance(
        availability_domain=getattr(instance_data, "availability_domain", None),
        capacity_reservation_id=getattr(instance_data, "capacity_reservation_id", None),
        compartment_id=getattr(instance_data, "compartment_id", None),
        placement_constraint_details=map_placement_constraint_details(
            getattr(instance_data, "placement_constraint_details", None)
        ),
        cluster_placement_group_id=getattr(
            instance_data, "cluster_placement_group_id", None
        ),
        dedicated_vm_host_id=getattr(instance_data, "dedicated_vm_host_id", None),
        defined_tags=getattr(instance_data, "defined_tags", None),
        security_attributes=getattr(instance_data, "security_attributes", None),
        security_attributes_state=getattr(
            instance_data, "security_attributes_state", None
        ),
        display_name=getattr(instance_data, "display_name", None),
        extended_metadata=getattr(instance_data, "extended_metadata", None),
        fault_domain=getattr(instance_data, "fault_domain", None),
        freeform_tags=getattr(instance_data, "freeform_tags", None),
        id=getattr(instance_data, "id", None),
        image_id=getattr(instance_data, "image_id", None),
        ipxe_script=getattr(instance_data, "ipxe_script", None),
        launch_mode=getattr(instance_data, "launch_mode", None),
        launch_options=map_launch_options(
            getattr(instance_data, "launch_options", None)
        ),
        instance_options=map_instance_options(
            getattr(instance_data, "instance_options", None)
        ),
        availability_config=map_availability_config(
            getattr(instance_data, "availability_config", None)
        ),
        preemptible_instance_config=map_preemptible_config(
            getattr(instance_data, "preemptible_instance_config", None)
        ),
        lifecycle_state=getattr(instance_data, "lifecycle_state", None),
        metadata=getattr(instance_data, "metadata", None),
        region=getattr(instance_data, "region", None),
        shape=getattr(instance_data, "shape", None),
        shape_config=map_shape_config(getattr(instance_data, "shape_config", None)),
        is_cross_numa_node=getattr(instance_data, "is_cross_numa_node", None),
        source_details=map_source_details(
            getattr(instance_data, "source_details", None)
        ),
        system_tags=getattr(instance_data, "system_tags", None),
        time_created=getattr(instance_data, "time_created", None),
        agent_config=map_agent_config(getattr(instance_data, "agent_config", None)),
        time_maintenance_reboot_due=getattr(
            instance_data, "time_maintenance_reboot_due", None
        ),
        platform_config=map_platform_config(
            getattr(instance_data, "platform_config", None)
        ),
        instance_configuration_id=getattr(
            instance_data, "instance_configuration_id", None
        ),
        licensing_configs=map_licensing_configs(
            getattr(instance_data, "licensing_configs", None)
        ),
    )


# endregion

# region Image


class InstanceAgentFeatures(BaseModel):
    """Oracle Cloud Agent features supported on the image."""

    is_monitoring_supported: Optional[bool] = Field(
        None, description="This attribute is not used."
    )
    is_management_supported: Optional[bool] = Field(
        None, description="This attribute is not used."
    )


class Image(BaseModel):
    """
    Pydantic model mirroring the fields of oci.core.models.Image.
    Uses existing LaunchOptions model and a lightweight InstanceAgentFeatures model.
    """

    base_image_id: Optional[str] = Field(
        None,
        description="The OCID of the image originally used to launch the instance.",
    )
    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment containing the instance you want to use as the basis for the image.",  # noqa
    )
    create_image_allowed: Optional[bool] = Field(
        None,
        description="Whether instances launched with this image can be used to create new images.",  # noqa
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",  # noqa
    )
    display_name: Optional[str] = Field(
        None,
        description="A user-friendly name for the image. It does not have to be unique, and it's changeable.",  # noqa
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description="Free-form tags for this resource as simple key/value pairs without predefined names.",  # noqa
    )
    id: Optional[str] = Field(None, description="The OCID of the image.")
    launch_mode: Optional[
        Literal["NATIVE", "EMULATED", "PARAVIRTUALIZED", "CUSTOM", "UNKNOWN_ENUM_VALUE"]
    ] = Field(
        None,
        description="Configuration mode for launching VM instances for this image.",
    )
    launch_options: Optional[LaunchOptions] = Field(
        None, description="Launch options associated with this image."
    )
    lifecycle_state: Optional[
        Literal[
            "PROVISIONING",
            "IMPORTING",
            "AVAILABLE",
            "EXPORTING",
            "DISABLED",
            "DELETED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The current lifecycle state of the image.")
    operating_system: Optional[str] = Field(
        None, description="The image's operating system (e.g., Oracle Linux)."
    )
    operating_system_version: Optional[str] = Field(
        None, description="The image's operating system version (e.g., 8)."
    )
    agent_features: Optional[InstanceAgentFeatures] = Field(
        None, description="Oracle Cloud Agent features supported on the image."
    )
    listing_type: Optional[Literal["COMMUNITY", "NONE", "UNKNOWN_ENUM_VALUE"]] = Field(
        None, description="The listing type of the image."
    )
    size_in_mbs: Optional[int] = Field(
        None,
        description="Boot volume size for an instance launched from this image (in MB).",  # noqa
    )
    billable_size_in_gbs: Optional[int] = Field(
        None,
        description="Size of the internal storage for this image that is subject to billing (in GB).",  # noqa
    )
    time_created: Optional[datetime] = Field(
        None, description="The date and time the image was created (RFC3339)."
    )


def map_instance_agent_features(af) -> InstanceAgentFeatures | None:
    if not af:
        return None
    return InstanceAgentFeatures(
        is_monitoring_supported=getattr(af, "is_monitoring_supported", None),
        is_management_supported=getattr(af, "is_management_supported", None),
    )


def map_image(image_data: oci.core.models.Image) -> Image:
    """
    Convert an oci.core.models.Image to oracle.oci_compute_mcp_server.models.Image,
    including nested types (LaunchOptions and InstanceAgentFeatures).
    """
    return Image(
        base_image_id=getattr(image_data, "base_image_id", None),
        compartment_id=getattr(image_data, "compartment_id", None),
        create_image_allowed=getattr(image_data, "create_image_allowed", None),
        defined_tags=getattr(image_data, "defined_tags", None),
        display_name=getattr(image_data, "display_name", None),
        freeform_tags=getattr(image_data, "freeform_tags", None),
        id=getattr(image_data, "id", None),
        launch_mode=getattr(image_data, "launch_mode", None),
        launch_options=map_launch_options(getattr(image_data, "launch_options", None)),
        lifecycle_state=getattr(image_data, "lifecycle_state", None),
        operating_system=getattr(image_data, "operating_system", None),
        operating_system_version=getattr(image_data, "operating_system_version", None),
        agent_features=map_instance_agent_features(
            getattr(image_data, "agent_features", None)
        ),
        listing_type=getattr(image_data, "listing_type", None),
        size_in_mbs=getattr(image_data, "size_in_mbs", None),
        billable_size_in_gbs=getattr(image_data, "billable_size_in_gbs", None),
        time_created=getattr(image_data, "time_created", None),
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
    """
    Convert an oci.request.Request to oracle.oci_networking_mcp_server.models.Request.
    """
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
    Recognizes common networking models; otherwise falls back to to_dict.
    """
    # Handle sequences
    if isinstance(data, (list, tuple)):
        return [_map_response_data(x) for x in data]

    # Already a plain type
    if data is None or isinstance(data, (str, int, float, bool)):
        return data
    if isinstance(data, dict):
        return data

    # Known OCI networking models
    try:
        if isinstance(data, oci.core.models.Instance):
            return map_instance(data)
    except Exception:
        # Ignore import/type detection issues and fall through to generic handling
        pass

    # Fallback: attempt to convert OCI SDK models or other objects to dict
    coerced = _oci_to_dict(data)
    return coerced if coerced is not None else data


def map_response(resp: oci.response.Response) -> Response | None:
    """
    Convert oci.response.Response to oracle.oci_networking_mcp_server.models.Response,
    including nested Request and best-effort mapping of data.
    """
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

# region VnicAttachment


class VnicAttachment(BaseModel):
    """
    Pydantic model mirroring the fields of oci.core.models.VnicAttachment.
    """

    availability_domain: Optional[str] = Field(
        None,
        description="The availability domain of the instance. Example: `Uocm:PHX-AD-1`",
    )
    compartment_id: Optional[str] = Field(
        None,
        description=(
            "The OCID of the compartment the VNIC attachment is in, which is the "
            "same compartment the instance is in."
        ),
    )
    display_name: Optional[str] = Field(
        None,
        description=(
            "A user-friendly name. Does not have to be unique, and it's changeable. "
            "Avoid entering confidential information."
        ),
    )
    id: Optional[str] = Field(None, description="The OCID of the VNIC attachment.")
    instance_id: Optional[str] = Field(None, description="The OCID of the instance.")
    lifecycle_state: Optional[
        Literal["ATTACHING", "ATTACHED", "DETACHING", "DETACHED", "UNKNOWN_ENUM_VALUE"]
    ] = Field(None, description="The current state of the VNIC attachment.")
    nic_index: Optional[int] = Field(
        None,
        description=(
            "Which physical network interface card (NIC) the VNIC uses. Certain bare "
            "metal instance shapes have two active physical NICs (0 and 1). If you add "
            "a secondary VNIC to one of these instances, you can specify which NIC "
            "the VNIC will use. For more information, see Virtual Network Interface "
            "Cards (VNICs)."
        ),
    )
    subnet_id: Optional[str] = Field(
        None, description="The OCID of the subnet to create the VNIC in."
    )
    vlan_id: Optional[str] = Field(
        None,
        description=(
            "The OCID of the VLAN to create the VNIC in. Creating the VNIC in a VLAN "
            "(instead of a subnet) is possible only if you are an Oracle Cloud VMware "
            "Solution customer. See Vlan. An error is returned if the instance already "
            "has a VNIC attached to it from this VLAN."
        ),
    )
    time_created: Optional[datetime] = Field(
        None,
        description=(
            "The date and time the VNIC attachment was created, in the format defined "
            "by RFC3339. Example: `2016-08-25T21:10:29.600Z`"
        ),
    )
    vlan_tag: Optional[int] = Field(
        None,
        description=(
            "The Oracle-assigned VLAN tag of the attached VNIC. Available after the "
            "attachment process is complete. However, if the VNIC belongs to a VLAN "
            "as part of the Oracle Cloud VMware Solution, the `vlanTag` value is "
            "instead the value of the `vlanTag` attribute for the VLAN. See Vlan. "
            "Example: `0`"
        ),
    )
    vnic_id: Optional[str] = Field(
        None,
        description=(
            "The OCID of the VNIC. Available after the attachment process is "
            "complete."
        ),
    )


def map_vnic_attachment(va: oci.core.models.VnicAttachment) -> VnicAttachment:
    """
    Convert an oci.core.models.VnicAttachment to oracle.oci_compute_mcp_server.models.VnicAttachment.
    """
    return VnicAttachment(
        availability_domain=getattr(va, "availability_domain", None),
        compartment_id=getattr(va, "compartment_id", None),
        display_name=getattr(va, "display_name", None),
        id=getattr(va, "id", None),
        instance_id=getattr(va, "instance_id", None),
        lifecycle_state=getattr(va, "lifecycle_state", None),
        nic_index=getattr(va, "nic_index", None),
        subnet_id=getattr(va, "subnet_id", None),
        vlan_id=getattr(va, "vlan_id", None),
        time_created=getattr(va, "time_created", None),
        vlan_tag=getattr(va, "vlan_tag", None),
        vnic_id=getattr(va, "vnic_id", None),
    )


# endregion
