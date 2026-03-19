"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import oci
from pydantic import BaseModel, Field


def _oci_to_dict(obj):
    """Best-effort conversion of OCI SDK objects into plain dictionaries."""
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


class CustomLog(BaseModel):
    """Structured log destination metadata returned by JMS for fleet logging settings."""
    namespace: Optional[str] = Field(None, description="OCI Logging namespace.")
    bucket_name: Optional[str] = Field(None, description="Bucket name associated with the log.")
    object_name: Optional[str] = Field(None, description="Object name associated with the log.")
    log_group_id: Optional[str] = Field(None, description="OCI Logging log group OCID.")
    log_id: Optional[str] = Field(None, description="OCI Logging log OCID.")


def map_custom_log(custom_log) -> CustomLog | None:
    """Convert an OCI JMS custom log object into the local `CustomLog` model."""
    if custom_log is None:
        return None
    return CustomLog(
        namespace=getattr(custom_log, "namespace", None),
        bucket_name=getattr(custom_log, "bucket_name", None),
        object_name=getattr(custom_log, "object_name", None),
        log_group_id=getattr(custom_log, "log_group_id", None),
        log_id=getattr(custom_log, "log_id", None),
    )


class FleetSummary(BaseModel):
    """Summary view of a JMS fleet as returned by list-style fleet APIs."""
    id: Optional[str] = Field(None, description="The OCID of the fleet.")
    display_name: Optional[str] = Field(None, description="The name of the fleet.")
    description: Optional[str] = Field(None, description="Description of the fleet.")
    compartment_id: Optional[str] = Field(None, description="The OCID of the compartment.")
    approximate_jre_count: Optional[int] = Field(None, description="Approximate number of Java runtimes.")
    approximate_installation_count: Optional[int] = Field(
        None, description="Approximate number of Java installations."
    )
    approximate_application_count: Optional[int] = Field(
        None, description="Approximate number of applications."
    )
    approximate_managed_instance_count: Optional[int] = Field(
        None, description="Approximate number of managed instances."
    )
    approximate_java_server_count: Optional[int] = Field(
        None, description="Approximate number of Java servers."
    )
    approximate_library_count: Optional[int] = Field(
        None, description="Approximate number of libraries."
    )
    approximate_library_vulnerability_count: Optional[int] = Field(
        None,
        description="Approximate number of library vulnerabilities.",
    )
    inventory_log: Optional[CustomLog] = Field(None, description="Inventory log configuration.")
    operation_log: Optional[CustomLog] = Field(None, description="Operation log configuration.")
    is_advanced_features_enabled: Optional[bool] = Field(
        None, description="Whether advanced features are enabled."
    )
    is_export_setting_enabled: Optional[bool] = Field(
        None, description="Whether export setting is enabled."
    )
    time_created: Optional[datetime] = Field(None, description="Fleet creation time.")
    lifecycle_state: Optional[
        Literal[
            "ACTIVE",
            "CREATING",
            "DELETED",
            "DELETING",
            "FAILED",
            "NEEDS_ATTENTION",
            "UPDATING",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="Lifecycle state of the fleet.")
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags for this fleet."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(None, description="Free-form tags for this fleet.")
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="System tags for this fleet."
    )


def map_fleet_summary(data: oci.jms.models.FleetSummary) -> FleetSummary | None:
    """Convert `oci.jms.models.FleetSummary` into the local `FleetSummary` model."""
    if data is None:
        return None
    return FleetSummary(
        id=getattr(data, "id", None),
        display_name=getattr(data, "display_name", None),
        description=getattr(data, "description", None),
        compartment_id=getattr(data, "compartment_id", None),
        approximate_jre_count=getattr(data, "approximate_jre_count", None),
        approximate_installation_count=getattr(data, "approximate_installation_count", None),
        approximate_application_count=getattr(data, "approximate_application_count", None),
        approximate_managed_instance_count=getattr(data, "approximate_managed_instance_count", None),
        approximate_java_server_count=getattr(data, "approximate_java_server_count", None),
        approximate_library_count=getattr(data, "approximate_library_count", None),
        approximate_library_vulnerability_count=getattr(
            data, "approximate_library_vulnerability_count", None
        ),
        inventory_log=map_custom_log(getattr(data, "inventory_log", None)),
        operation_log=map_custom_log(getattr(data, "operation_log", None)),
        is_advanced_features_enabled=getattr(data, "is_advanced_features_enabled", None),
        is_export_setting_enabled=getattr(data, "is_export_setting_enabled", None),
        time_created=getattr(data, "time_created", None),
        lifecycle_state=getattr(data, "lifecycle_state", None),
        defined_tags=getattr(data, "defined_tags", None),
        freeform_tags=getattr(data, "freeform_tags", None),
        system_tags=getattr(data, "system_tags", None),
    )


class Fleet(FleetSummary):
    """Detailed JMS fleet model for single-fleet reads."""
    pass


def map_fleet(data: oci.jms.models.Fleet) -> Fleet | None:
    """Convert `oci.jms.models.Fleet` into the local `Fleet` model."""
    if data is None:
        return None
    return Fleet.model_validate(map_fleet_summary(data).model_dump())


class JmsPluginSummary(BaseModel):
    """Summary view of a JMS plugin returned by list APIs."""
    id: Optional[str] = Field(None, description="The OCID of the JMS plugin.")
    agent_id: Optional[str] = Field(None, description="The agent OCID.")
    agent_type: Optional[Literal["OMA", "OCA", "OCMA", "UNKNOWN_ENUM_VALUE"]] = Field(
        None, description="Type of agent reporting the plugin."
    )
    lifecycle_state: Optional[
        Literal["ACTIVE", "INACTIVE", "NEEDS_ATTENTION", "DELETED", "UNKNOWN_ENUM_VALUE"]
    ] = Field(None, description="Lifecycle state of the plugin.")
    availability_status: Optional[
        Literal["ACTIVE", "SILENT", "NOT_AVAILABLE", "UNKNOWN_ENUM_VALUE"]
    ] = Field(None, description="Availability status of the plugin.")
    fleet_id: Optional[str] = Field(None, description="The associated fleet OCID.")
    compartment_id: Optional[str] = Field(None, description="The compartment OCID.")
    hostname: Optional[str] = Field(None, description="Hostname of the plugin host.")
    os_family: Optional[Literal["LINUX", "WINDOWS", "MACOS", "UNKNOWN", "UNKNOWN_ENUM_VALUE"]] = (
        Field(None, description="Operating system family.")
    )
    os_architecture: Optional[str] = Field(None, description="Operating system architecture.")
    os_distribution: Optional[str] = Field(None, description="Operating system distribution.")
    plugin_version: Optional[str] = Field(None, description="Plugin version.")
    time_registered: Optional[datetime] = Field(None, description="Registration time.")
    time_last_seen: Optional[datetime] = Field(None, description="Last seen time.")
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags for this plugin."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(None, description="Free-form tags for this plugin.")
    system_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="System tags for this plugin."
    )


def map_jms_plugin_summary(data: oci.jms.models.JmsPluginSummary) -> JmsPluginSummary | None:
    """Convert `oci.jms.models.JmsPluginSummary` into `JmsPluginSummary`."""
    if data is None:
        return None
    return JmsPluginSummary(
        id=getattr(data, "id", None),
        agent_id=getattr(data, "agent_id", None),
        agent_type=getattr(data, "agent_type", None),
        lifecycle_state=getattr(data, "lifecycle_state", None),
        availability_status=getattr(data, "availability_status", None),
        fleet_id=getattr(data, "fleet_id", None),
        compartment_id=getattr(data, "compartment_id", None),
        hostname=getattr(data, "hostname", None),
        os_family=getattr(data, "os_family", None),
        os_architecture=getattr(data, "os_architecture", None),
        os_distribution=getattr(data, "os_distribution", None),
        plugin_version=getattr(data, "plugin_version", None),
        time_registered=getattr(data, "time_registered", None),
        time_last_seen=getattr(data, "time_last_seen", None),
        defined_tags=getattr(data, "defined_tags", None),
        freeform_tags=getattr(data, "freeform_tags", None),
        system_tags=getattr(data, "system_tags", None),
    )


class JmsPlugin(JmsPluginSummary):
    """Detailed JMS plugin model for single-plugin reads."""
    pass


def map_jms_plugin(data: oci.jms.models.JmsPlugin) -> JmsPlugin | None:
    """Convert `oci.jms.models.JmsPlugin` into the local `JmsPlugin` model."""
    if data is None:
        return None
    return JmsPlugin.model_validate(map_jms_plugin_summary(data).model_dump())


class JavaRuntimeId(BaseModel):
    """Minimal Java runtime identity used in installation-site responses."""
    version: Optional[str] = Field(None, description="Java runtime version.")
    vendor: Optional[str] = Field(None, description="Java runtime vendor.")
    distribution: Optional[str] = Field(None, description="Java runtime distribution.")
    jre_key: Optional[str] = Field(None, description="Unique runtime key.")


def map_java_runtime_id(data) -> JavaRuntimeId | None:
    """Convert an OCI JMS Java runtime identity object into `JavaRuntimeId`."""
    if data is None:
        return None
    return JavaRuntimeId(
        version=getattr(data, "version", None),
        vendor=getattr(data, "vendor", None),
        distribution=getattr(data, "distribution", None),
        jre_key=getattr(data, "jre_key", None),
    )


class OperatingSystem(BaseModel):
    """Operating system metadata attached to JMS resources and usage records."""
    family: Optional[Literal["LINUX", "WINDOWS", "MACOS", "UNKNOWN", "UNKNOWN_ENUM_VALUE"]] = (
        Field(None, description="Operating system family.")
    )
    name: Optional[str] = Field(None, description="Operating system name.")
    distribution: Optional[str] = Field(None, description="Operating system distribution.")
    version: Optional[str] = Field(None, description="Operating system version.")
    architecture: Optional[str] = Field(None, description="Operating system architecture.")
    managed_instance_count: Optional[int] = Field(
        None, description="Number of managed instances for this operating system."
    )
    container_count: Optional[int] = Field(
        None, description="Number of containers for this operating system."
    )


def map_operating_system(data) -> OperatingSystem | None:
    """Convert an OCI JMS operating system object into the local `OperatingSystem` model."""
    if data is None:
        return None
    return OperatingSystem(
        family=getattr(data, "family", None),
        name=getattr(data, "name", None),
        distribution=getattr(data, "distribution", None),
        version=getattr(data, "version", None),
        architecture=getattr(data, "architecture", None),
        managed_instance_count=getattr(data, "managed_instance_count", None),
        container_count=getattr(data, "container_count", None),
    )


class InstallationSiteSummary(BaseModel):
    """Summary of a Java installation site discovered within a JMS fleet."""
    installation_key: Optional[str] = Field(None, description="Unique installation identifier.")
    managed_instance_id: Optional[str] = Field(None, description="Managed instance OCID.")
    jre: Optional[JavaRuntimeId] = Field(None, description="Associated Java runtime identifier.")
    security_status: Optional[
        Literal[
            "EARLY_ACCESS",
            "UNKNOWN",
            "UP_TO_DATE",
            "UPDATE_REQUIRED",
            "UPGRADE_REQUIRED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="Security status of the Java runtime.")
    path: Optional[str] = Field(None, description="Installation path.")
    operating_system: Optional[OperatingSystem] = Field(
        None, description="Operating system for the installation site."
    )
    approximate_application_count: Optional[int] = Field(
        None, description="Approximate number of applications using this installation."
    )
    time_last_seen: Optional[datetime] = Field(None, description="Last seen time.")
    blocklist: Optional[List[Dict[str, Any]]] = Field(
        None, description="Blocklist entries associated with the installation."
    )
    lifecycle_state: Optional[
        Literal[
            "ACTIVE",
            "CREATING",
            "DELETED",
            "DELETING",
            "FAILED",
            "NEEDS_ATTENTION",
            "UPDATING",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="Lifecycle state of the installation site.")


def map_installation_site_summary(
    data: oci.jms.models.InstallationSiteSummary,
) -> InstallationSiteSummary | None:
    """Convert `oci.jms.models.InstallationSiteSummary` into `InstallationSiteSummary`."""
    if data is None:
        return None
    blocklist = getattr(data, "blocklist", None)
    return InstallationSiteSummary(
        installation_key=getattr(data, "installation_key", None),
        managed_instance_id=getattr(data, "managed_instance_id", None),
        jre=map_java_runtime_id(getattr(data, "jre", None)),
        security_status=getattr(data, "security_status", None),
        path=getattr(data, "path", None),
        operating_system=map_operating_system(getattr(data, "operating_system", None)),
        approximate_application_count=getattr(data, "approximate_application_count", None),
        time_last_seen=getattr(data, "time_last_seen", None),
        blocklist=[_oci_to_dict(item) for item in blocklist] if blocklist else None,
        lifecycle_state=getattr(data, "lifecycle_state", None),
    )


class FleetAgentOsConfiguration(BaseModel):
    """OS-specific include and exclude path configuration for JMS fleet agents."""
    include_paths: Optional[List[str]] = Field(None, description="Included filesystem paths.")
    exclude_paths: Optional[List[str]] = Field(None, description="Excluded filesystem paths.")


def map_fleet_agent_os_configuration(data) -> FleetAgentOsConfiguration | None:
    """Convert an OCI JMS fleet-agent OS configuration into the local model."""
    if data is None:
        return None
    return FleetAgentOsConfiguration(
        include_paths=getattr(data, "include_paths", None),
        exclude_paths=getattr(data, "exclude_paths", None),
    )


class FleetAgentConfiguration(BaseModel):
    """Fleet-wide JMS agent configuration returned for a fleet."""
    jre_scan_frequency_in_minutes: Optional[int] = Field(
        None, description="JRE scanning frequency in minutes."
    )
    java_usage_tracker_processing_frequency_in_minutes: Optional[int] = Field(
        None, description="Java usage tracker processing frequency in minutes."
    )
    work_request_validity_period_in_days: Optional[int] = Field(
        None, description="Validity period for work requests in days."
    )
    agent_polling_interval_in_minutes: Optional[int] = Field(
        None, description="Agent polling interval in minutes."
    )
    is_collecting_managed_instance_metrics_enabled: Optional[bool] = Field(
        None, description="Whether managed instance metrics collection is enabled."
    )
    is_collecting_usernames_enabled: Optional[bool] = Field(
        None, description="Whether username collection is enabled."
    )
    is_capturing_ip_address_and_fqdn_enabled: Optional[bool] = Field(
        None, description="Whether IP address and FQDN capture is enabled."
    )
    is_libraries_scan_enabled: Optional[bool] = Field(
        None, description="Whether library scanning is enabled."
    )
    linux_configuration: Optional[FleetAgentOsConfiguration] = Field(
        None, description="Linux-specific agent configuration."
    )
    windows_configuration: Optional[FleetAgentOsConfiguration] = Field(
        None, description="Windows-specific agent configuration."
    )
    mac_os_configuration: Optional[FleetAgentOsConfiguration] = Field(
        None, description="macOS-specific agent configuration."
    )
    time_last_modified: Optional[datetime] = Field(None, description="Last modified time.")


def map_fleet_agent_configuration(
    data: oci.jms.models.FleetAgentConfiguration,
) -> FleetAgentConfiguration | None:
    """Convert `oci.jms.models.FleetAgentConfiguration` into `FleetAgentConfiguration`."""
    if data is None:
        return None
    return FleetAgentConfiguration(
        jre_scan_frequency_in_minutes=getattr(data, "jre_scan_frequency_in_minutes", None),
        java_usage_tracker_processing_frequency_in_minutes=getattr(
            data, "java_usage_tracker_processing_frequency_in_minutes", None
        ),
        work_request_validity_period_in_days=getattr(
            data, "work_request_validity_period_in_days", None
        ),
        agent_polling_interval_in_minutes=getattr(data, "agent_polling_interval_in_minutes", None),
        is_collecting_managed_instance_metrics_enabled=getattr(
            data, "is_collecting_managed_instance_metrics_enabled", None
        ),
        is_collecting_usernames_enabled=getattr(data, "is_collecting_usernames_enabled", None),
        is_capturing_ip_address_and_fqdn_enabled=getattr(
            data, "is_capturing_ip_address_and_fqdn_enabled", None
        ),
        is_libraries_scan_enabled=getattr(data, "is_libraries_scan_enabled", None),
        linux_configuration=map_fleet_agent_os_configuration(
            getattr(data, "linux_configuration", None)
        ),
        windows_configuration=map_fleet_agent_os_configuration(
            getattr(data, "windows_configuration", None)
        ),
        mac_os_configuration=map_fleet_agent_os_configuration(
            getattr(data, "mac_os_configuration", None)
        ),
        time_last_modified=getattr(data, "time_last_modified", None),
    )


class FleetAdvancedFeatureConfiguration(BaseModel):
    """Advanced feature configuration attached to a JMS fleet."""
    analytic_namespace: Optional[str] = Field(None, description="Analytics namespace.")
    analytic_bucket_name: Optional[str] = Field(None, description="Analytics bucket name.")
    lcm: Optional[Dict[str, Any]] = Field(None, description="LCM configuration.")
    crypto_event_analysis: Optional[Dict[str, Any]] = Field(
        None, description="Crypto event analysis configuration."
    )
    advanced_usage_tracking: Optional[Dict[str, Any]] = Field(
        None, description="Advanced usage tracking configuration."
    )
    jfr_recording: Optional[Dict[str, Any]] = Field(None, description="JFR recording configuration.")
    performance_tuning_analysis: Optional[Dict[str, Any]] = Field(
        None, description="Performance tuning analysis configuration."
    )
    java_migration_analysis: Optional[Dict[str, Any]] = Field(
        None, description="Java migration analysis configuration."
    )
    time_last_modified: Optional[datetime] = Field(None, description="Last modified time.")


def map_fleet_advanced_feature_configuration(
    data: oci.jms.models.FleetAdvancedFeatureConfiguration,
) -> FleetAdvancedFeatureConfiguration | None:
    """Convert fleet advanced feature configuration into a serializable local model."""
    if data is None:
        return None
    return FleetAdvancedFeatureConfiguration(
        analytic_namespace=getattr(data, "analytic_namespace", None),
        analytic_bucket_name=getattr(data, "analytic_bucket_name", None),
        lcm=_oci_to_dict(getattr(data, "lcm", None)),
        crypto_event_analysis=_oci_to_dict(getattr(data, "crypto_event_analysis", None)),
        advanced_usage_tracking=_oci_to_dict(getattr(data, "advanced_usage_tracking", None)),
        jfr_recording=_oci_to_dict(getattr(data, "jfr_recording", None)),
        performance_tuning_analysis=_oci_to_dict(
            getattr(data, "performance_tuning_analysis", None)
        ),
        java_migration_analysis=_oci_to_dict(getattr(data, "java_migration_analysis", None)),
        time_last_modified=getattr(data, "time_last_modified", None),
    )


class ManagedInstanceUsage(BaseModel):
    """Managed instance usage summary returned by JMS usage aggregation APIs."""
    managed_instance_id: Optional[str] = Field(None, description="Managed instance OCID.")
    managed_instance_type: Optional[
        Literal[
            "ORACLE_MANAGEMENT_AGENT",
            "ORACLE_CLOUD_AGENT",
            "ORACLE_CONTAINER_MANAGEMENT_AGENT",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="Managed instance type.")
    hostname: Optional[str] = Field(None, description="Hostname of the managed instance.")
    host_id: Optional[str] = Field(None, description="Host OCID or host identifier.")
    ip_addresses: Optional[List[str]] = Field(None, description="IP addresses of the managed instance.")
    hostnames: Optional[List[str]] = Field(None, description="Hostnames associated with the instance.")
    fqdns: Optional[List[str]] = Field(None, description="FQDNs associated with the instance.")
    operating_system: Optional[OperatingSystem] = Field(
        None, description="Operating system information."
    )
    agent: Optional[Dict[str, Any]] = Field(None, description="Agent details.")
    cluster_details: Optional[Dict[str, Any]] = Field(None, description="Cluster details.")
    approximate_application_count: Optional[int] = Field(
        None, description="Approximate application count."
    )
    approximate_installation_count: Optional[int] = Field(
        None, description="Approximate installation count."
    )
    approximate_jre_count: Optional[int] = Field(None, description="Approximate JRE count.")
    drs_file_status: Optional[
        Literal["PRESENT", "ABSENT", "MISMATCH", "NOT_CONFIGURED", "UNKNOWN_ENUM_VALUE"]
    ] = Field(None, description="DRS file status.")
    application_invoked_by: Optional[str] = Field(
        None, description="Username or principal that invoked the application."
    )
    time_start: Optional[datetime] = Field(None, description="Usage summary start time.")
    time_end: Optional[datetime] = Field(None, description="Usage summary end time.")
    time_first_seen: Optional[datetime] = Field(None, description="First seen time.")
    time_last_seen: Optional[datetime] = Field(None, description="Last seen time.")


def map_managed_instance_usage(
    data: oci.jms.models.ManagedInstanceUsage,
) -> ManagedInstanceUsage | None:
    """Convert `oci.jms.models.ManagedInstanceUsage` into `ManagedInstanceUsage`."""
    if data is None:
        return None
    return ManagedInstanceUsage(
        managed_instance_id=getattr(data, "managed_instance_id", None),
        managed_instance_type=getattr(data, "managed_instance_type", None),
        hostname=getattr(data, "hostname", None),
        host_id=getattr(data, "host_id", None),
        ip_addresses=getattr(data, "ip_addresses", None),
        hostnames=getattr(data, "hostnames", None),
        fqdns=getattr(data, "fqdns", None),
        operating_system=map_operating_system(getattr(data, "operating_system", None)),
        agent=_oci_to_dict(getattr(data, "agent", None)),
        cluster_details=_oci_to_dict(getattr(data, "cluster_details", None)),
        approximate_application_count=getattr(data, "approximate_application_count", None),
        approximate_installation_count=getattr(data, "approximate_installation_count", None),
        approximate_jre_count=getattr(data, "approximate_jre_count", None),
        drs_file_status=getattr(data, "drs_file_status", None),
        application_invoked_by=getattr(data, "application_invoked_by", None),
        time_start=getattr(data, "time_start", None),
        time_end=getattr(data, "time_end", None),
        time_first_seen=getattr(data, "time_first_seen", None),
        time_last_seen=getattr(data, "time_last_seen", None),
    )


class ResourceInventory(BaseModel):
    """High-level inventory counts for JMS resources in a compartment."""
    active_fleet_count: Optional[int] = Field(None, description="Number of active fleets.")
    managed_instance_count: Optional[int] = Field(None, description="Number of managed instances.")
    jre_count: Optional[int] = Field(None, description="Number of Java runtimes.")
    installation_count: Optional[int] = Field(None, description="Number of Java installations.")
    application_count: Optional[int] = Field(None, description="Number of applications.")


def map_resource_inventory(data: oci.jms.models.ResourceInventory) -> ResourceInventory | None:
    """Convert `oci.jms.models.ResourceInventory` into `ResourceInventory`."""
    if data is None:
        return None
    return ResourceInventory(
        active_fleet_count=getattr(data, "active_fleet_count", None),
        managed_instance_count=getattr(data, "managed_instance_count", None),
        jre_count=getattr(data, "jre_count", None),
        installation_count=getattr(data, "installation_count", None),
        application_count=getattr(data, "application_count", None),
    )


class FleetDiagnosisRecord(BaseModel):
    """Fleet diagnosis record returned by JMS health APIs."""
    resource_diagnosis: Optional[str] = Field(None, description="Diagnosis message for the resource.")
    resource_id: Optional[str] = Field(None, description="Affected resource OCID or identifier.")
    resource_state: Optional[str] = Field(None, description="Lifecycle or health state of the resource.")
    resource_type: Optional[str] = Field(None, description="Type of the affected resource.")


def map_fleet_diagnosis(data: oci.jms.models.FleetDiagnosisSummary) -> FleetDiagnosisRecord | None:
    """Convert `oci.jms.models.FleetDiagnosisSummary` into `FleetDiagnosisRecord`."""
    if data is None:
        return None
    return FleetDiagnosisRecord(
        resource_diagnosis=getattr(data, "resource_diagnosis", None),
        resource_id=getattr(data, "resource_id", None),
        resource_state=getattr(data, "resource_state", None),
        resource_type=getattr(data, "resource_type", None),
    )


class FleetErrorDetail(BaseModel):
    """Detailed fleet error entry nested inside a fleet error summary."""
    details: Optional[str] = Field(None, description="Detailed description of the error.")
    reason: Optional[str] = Field(None, description="High-level reason for the error.")
    time_last_seen: Optional[datetime] = Field(None, description="Last time the error was seen.")


def map_fleet_error_detail(data: oci.jms.models.FleetErrorDetails) -> FleetErrorDetail | None:
    """Convert `oci.jms.models.FleetErrorDetails` into `FleetErrorDetail`."""
    if data is None:
        return None
    return FleetErrorDetail(
        details=getattr(data, "details", None),
        reason=getattr(data, "reason", None),
        time_last_seen=getattr(data, "time_last_seen", None),
    )


class FleetErrorRecord(BaseModel):
    """Fleet-scoped error summary returned by JMS health APIs."""
    compartment_id: Optional[str] = Field(None, description="Compartment OCID containing the fleet.")
    fleet_id: Optional[str] = Field(None, description="Fleet OCID.")
    fleet_name: Optional[str] = Field(None, description="Fleet display name.")
    errors: Optional[List[FleetErrorDetail]] = Field(
        None, description="Error detail entries associated with this fleet."
    )
    time_first_seen: Optional[datetime] = Field(None, description="First time the fleet error was seen.")
    time_last_seen: Optional[datetime] = Field(None, description="Last time the fleet error was seen.")


def map_fleet_error(data: oci.jms.models.FleetErrorSummary) -> FleetErrorRecord | None:
    """Convert `oci.jms.models.FleetErrorSummary` into `FleetErrorRecord`."""
    if data is None:
        return None
    errors = getattr(data, "errors", None)
    return FleetErrorRecord(
        compartment_id=getattr(data, "compartment_id", None),
        fleet_id=getattr(data, "fleet_id", None),
        fleet_name=getattr(data, "fleet_name", None),
        errors=[map_fleet_error_detail(item) for item in errors] if errors else None,
        time_first_seen=getattr(data, "time_first_seen", None),
        time_last_seen=getattr(data, "time_last_seen", None),
    )


class FleetHealthSummary(BaseModel):
    """Chat-friendly summary of the health posture of a JMS fleet."""
    fleet_id: str = Field(..., description="Fleet OCID.")
    diagnosis_count: int = Field(..., description="Number of diagnosis records for the fleet.")
    fleet_errors: List[FleetErrorRecord] = Field(
        default_factory=list, description="Fleet error records returned for the fleet."
    )
    top_issue_categories: List[str] = Field(
        default_factory=list, description="Deduplicated high-signal issue categories."
    )
    overall_health_status: Literal["HEALTHY", "WARNING", "CRITICAL", "UNKNOWN"] = Field(
        ..., description="Derived overall health status for the fleet."
    )
    recommended_next_checks: List[str] = Field(
        default_factory=list,
        description="MCP-generated follow-up checks derived from returned diagnoses and errors.",
    )


class FleetHealthDiagnostics(BaseModel):
    """Detailed fleet health diagnostics for drill-down troubleshooting."""
    fleet_id: str = Field(..., description="Fleet OCID.")
    diagnoses: List[FleetDiagnosisRecord] = Field(
        default_factory=list, description="Detailed diagnosis records for the fleet."
    )
    fleet_errors: List[FleetErrorRecord] = Field(
        default_factory=list, description="Detailed fleet error records for the fleet."
    )
    diagnosis_count: int = Field(..., description="Number of diagnosis records returned.")
    fleet_error_count: int = Field(..., description="Number of fleet error records returned.")


class JmsNotice(BaseModel):
    """Announcement or notice surfaced by the JMS service."""
    key: Optional[str] = Field(None, description="Announcement key.")
    summary: Optional[str] = Field(None, description="Announcement summary.")
    time_released: Optional[datetime] = Field(None, description="Announcement release time.")
    url: Optional[str] = Field(None, description="Announcement reference URL.")


def map_jms_notice(data: oci.jms.models.AnnouncementSummary) -> JmsNotice | None:
    """Convert `oci.jms.models.AnnouncementSummary` into `JmsNotice`."""
    if data is None:
        return None
    return JmsNotice(
        key=getattr(data, "key", None),
        summary=getattr(data, "summary", None),
        time_released=getattr(data, "time_released", None),
        url=getattr(data, "url", None),
    )
