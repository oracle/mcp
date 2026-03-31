"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from datetime import datetime
from logging import Logger
from typing import Literal, Optional

import oci
from fastmcp import FastMCP
from oracle.oci_jms_mcp_server.models import (
    Fleet,
    FleetAdvancedFeatureConfiguration,
    FleetAgentConfiguration,
    FleetDiagnosisRecord,
    FleetErrorRecord,
    FleetHealthDiagnostics,
    FleetHealthSummary,
    FleetSummary,
    InstallationSiteSummary,
    JavaRuntimeComplianceBucket,
    JavaRuntimeComplianceReport,
    JavaRuntimeCountBreakdown,
    JmsNotice,
    JmsPlugin,
    JmsPluginSummary,
    ManagedInstanceUsage,
    OutdatedJavaInstallation,
    ResourceInventory,
    map_fleet,
    map_fleet_advanced_feature_configuration,
    map_fleet_agent_configuration,
    map_fleet_diagnosis,
    map_fleet_error,
    map_fleet_summary,
    map_installation_site_summary,
    map_jms_notice,
    map_jms_plugin,
    map_jms_plugin_summary,
    map_managed_instance_usage,
    map_resource_inventory,
)
from pydantic import Field

from . import __project__, __version__
from .util import get_jms_service_endpoint

# Setup
logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)

_UNSUPPORTED_ENV_ALIASES = {
    "OCI_CONFIG": "OCI_CONFIG_FILE",
    "OCI_PROFILE": "OCI_CONFIG_PROFILE",
}
_MAX_OUTDATED_INSTALLATIONS = 25

# Input Normalization Helpers
def _normalize_enum(value: Optional[str]) -> Optional[str]:
    """Normalize flexible enum input into OCI SDK-style uppercase values."""
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized.upper().replace("-", "_").replace(" ", "_")


def _normalize_enum_list(values: Optional[list[str]]) -> Optional[list[str]]:
    """Normalize lists of enum-like values."""
    if values is None:
        return None
    normalized = [_normalize_enum(value) for value in values]
    normalized = [value for value in normalized if value is not None]
    return normalized or None


def _normalized_key(value: str) -> str:
    """Canonicalize user input for case-insensitive matching of mixed-case SDK values."""
    return "".join(ch for ch in value.strip().lower() if ch.isalnum())


def _normalize_choice(value: Optional[str], allowed_values: list[str]) -> Optional[str]:
    """Map flexible user input to one of the SDK's exact allowed string values."""
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None

    by_key = {_normalized_key(item): item for item in allowed_values}
    return by_key.get(_normalized_key(normalized), value)


def _normalize_choice_list(
    values: Optional[list[str]], allowed_values: list[str]
) -> Optional[list[str]]:
    """Map a list of flexible user inputs to exact SDK values where possible."""
    if values is None:
        return None
    normalized = [_normalize_choice(value, allowed_values) for value in values]
    normalized = [value for value in normalized if value is not None]
    return normalized or None


def _omit_none(**kwargs):
    """Drop only None values so optional OCI SDK kwargs are not sent spuriously."""
    return {key: value for key, value in kwargs.items() if value is not None}


def _parse_rfc3339(value: Optional[str]) -> Optional[datetime]:
    """Convert an optional RFC3339 timestamp string into a datetime."""
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return datetime.fromisoformat(normalized.replace("Z", "+00:00"))


def _collect_paginated_items(method, **kwargs):
    """Collect all items from a paginated OCI list operation."""
    items = []
    has_next_page = True
    next_page: Optional[str] = None
    limit = kwargs.get("limit")

    while has_next_page and (limit is None or len(items) < limit):
        response = method(**_omit_none(**kwargs, page=next_page))
        response_items = list(getattr(response.data, "items", []))
        if limit is not None:
            remaining = limit - len(items)
            response_items = response_items[:remaining]
        items.extend(response_items)
        has_next_page = getattr(response, "has_next_page", False)
        next_page = response.next_page if hasattr(response, "next_page") else None

    return items


def _collect_text_fragments(*values) -> list[str]:
    """Recursively gather non-empty strings from nested tool data."""
    fragments: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            normalized = value.strip()
            if normalized and normalized != "UNKNOWN_ENUM_VALUE":
                fragments.append(normalized)
            continue
        if isinstance(value, list):
            fragments.extend(_collect_text_fragments(*value))
            continue
        if isinstance(value, dict):
            fragments.extend(_collect_text_fragments(*value.values()))
            continue
        if hasattr(value, "model_dump"):
            fragments.extend(_collect_text_fragments(value.model_dump()))
    return fragments


def _normalize_issue_category(value: str) -> str:
    """Produce a stable issue category label from diagnosis or error text."""
    normalized = " ".join(value.replace("_", " ").split())
    return normalized[:1].upper() + normalized[1:] if normalized else normalized


def _pick_issue_category(*values: Optional[str]) -> Optional[str]:
    """Pick the first non-empty, non-sentinel issue text."""
    for value in values:
        if value and value.strip() and value != "UNKNOWN_ENUM_VALUE":
            return value
    return None


def _derive_top_issue_categories(
    diagnoses: list[FleetDiagnosisRecord], fleet_errors: list[FleetErrorRecord]
) -> list[str]:
    """Extract a stable, deduplicated list of high-signal issue categories."""
    categories: list[str] = []
    seen: set[str] = set()

    for diagnosis in diagnoses:
        candidate = diagnosis.resource_diagnosis
        if candidate:
            normalized = _normalize_issue_category(candidate)
            key = normalized.casefold()
            if key not in seen:
                seen.add(key)
                categories.append(normalized)

    for fleet_error in fleet_errors:
        for error in fleet_error.errors or []:
            candidate = _pick_issue_category(error.reason, error.details)
            if candidate:
                normalized = _normalize_issue_category(candidate)
                key = normalized.casefold()
                if key not in seen:
                    seen.add(key)
                    categories.append(normalized)

    return categories[:5]


def _derive_overall_health_status(
    diagnoses: list[FleetDiagnosisRecord], fleet_errors: list[FleetErrorRecord]
) -> Literal["HEALTHY", "WARNING", "CRITICAL", "UNKNOWN"]:
    """Collapse fleet diagnoses and errors into a single coarse health status."""
    if not diagnoses and not fleet_errors:
        return "HEALTHY"

    fragments = _collect_text_fragments(diagnoses, fleet_errors)
    if not fragments:
        return "UNKNOWN"

    severe_markers = (
        "critical",
        "failed",
        "failure",
        "error",
        "severe",
        "not available",
        "unavailable",
    )
    warning_markers = (
        "needs attention",
        "warning",
        "inventory",
        "scan",
        "plugin",
        "agent",
    )

    lowered = [fragment.casefold() for fragment in fragments]
    # Prefer a stable coarse status over surfacing raw provider-specific states.
    if any(marker in fragment for fragment in lowered for marker in severe_markers):
        return "CRITICAL"
    if any(marker in fragment for fragment in lowered for marker in warning_markers):
        return "WARNING"
    return "WARNING"


def _derive_recommended_next_checks(
    diagnoses: list[FleetDiagnosisRecord], fleet_errors: list[FleetErrorRecord]
) -> list[str]:
    """Generate deterministic next-step hints from returned diagnoses and errors."""
    if not diagnoses and not fleet_errors:
        return []

    fragments = [fragment.casefold() for fragment in _collect_text_fragments(diagnoses, fleet_errors)]
    recommendations: list[str] = []

    def add_once(text: str):
        if text not in recommendations:
            recommendations.append(text)

    # These recommendations intentionally trade completeness for deterministic,
    # chat-friendly next steps derived from recurring diagnosis/error keywords.
    if any(
        marker in fragment
        for fragment in fragments
        for marker in ("inventory", "scan", "discovery", "collection")
    ):
        add_once("Review fleet agent configuration and inventory collection settings.")

    if any(
        marker in fragment
        for fragment in fragments
        for marker in ("agent", "plugin", "silent", "report", "heartbeat", "connect")
    ):
        add_once("Inspect detailed fleet health diagnostics and verify recent agent or plugin reporting.")

    if any(
        marker in fragment
        for fragment in fragments
        for marker in ("auth", "permission", "unauthorized", "forbidden", "region")
    ):
        add_once("Verify fleet visibility, OCI access, and region or compartment alignment.")

    add_once("Check JMS notices for any known service-side issues or advisories.")
    return recommendations


def _normalize_count(value: Optional[int]) -> int:
    """Treat missing approximate counts as zero for aggregation purposes."""
    return int(value or 0)


def _safe_get_java_release(client, release_version: Optional[str]):
    """Best-effort Java release lookup; ignore not-found style misses for enrichment."""
    if not release_version:
        return None
    try:
        response: oci.response.Response = client.get_java_release(release_version=release_version)
        return response.data
    except oci.exceptions.ServiceError as exc:
        if exc.status in (400, 404):
            return None
        raise


def _build_runtime_count_breakdowns(values: list[tuple[Optional[str], int]]) -> list[JavaRuntimeCountBreakdown]:
    """Aggregate runtime counts by a single string key such as vendor or distribution."""
    counts: dict[str, int] = {}
    for raw_key, count in values:
        key = raw_key or "UNKNOWN"
        counts[key] = counts.get(key, 0) + count

    return [
        JavaRuntimeCountBreakdown(key=key, runtime_count=runtime_count)
        for key, runtime_count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _warn_on_unsupported_env_aliases():
    """Warn when env vars from the separate generic OCI API MCP project are used."""
    for alias, canonical in _UNSUPPORTED_ENV_ALIASES.items():
        if os.getenv(alias) and not os.getenv(canonical):
            logger.warning(
                f"{alias} is not used by oracle.oci-jms-mcp-server; use {canonical} instead."
            )


def _load_oci_config() -> dict:
    """Load OCI SDK config using the JMS server's supported env var names."""
    # Warn early because users often copy client config from the generic OCI API MCP server.
    _warn_on_unsupported_env_aliases()
    return oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )


def _build_security_token_signer(config: dict) -> oci.auth.signers.SecurityTokenSigner:
    """Create a security-token signer from the OCI config file referenced key and token."""
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = os.path.expanduser(config["security_token_file"])
    with open(token_file, "r") as f:
        token = f.read().strip()
    return oci.auth.signers.SecurityTokenSigner(token, private_key)


def get_jms_client():
    """Construct a fresh OCI Java Management Service client for the active profile."""
    logger.info("entering get_jms_client")
    config = _load_oci_config()
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    signer = _build_security_token_signer(config)
    service_endpoint = get_jms_service_endpoint(config)
    if service_endpoint:
        logger.info(f"Using JMS endpoint override from JMS_TEST_ENVIRONMENT: {service_endpoint}")
    client_kwargs = _omit_none(signer=signer, service_endpoint=service_endpoint)
    return oci.jms.JavaManagementServiceClient(config, **client_kwargs)

# mcp tool functions
@mcp.tool(description="List Java Management Service fleets in a compartment.")
def list_fleets(
    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment in which to list fleets. Required unless `id` is provided.",
    ),
    id: Optional[str] = Field(None, description="The OCID of a specific fleet to filter for."),
    lifecycle_state: Optional[str] = Field(
        None,
        description=(
            "Filter fleets by lifecycle state. Accepted values include ACTIVE, CREATING, "
            "DELETED, DELETING, FAILED, NEEDS_ATTENTION, and UPDATING."
        ),
    ),
    display_name: Optional[str] = Field(None, description="Filter fleets by exact display name."),
    display_name_contains: Optional[str] = Field(
        None,
        description="Filter fleets whose display name contains this value.",
    ),
    limit: Optional[int] = Field(None, description="Maximum number of fleets to return.", ge=1),
    sort_order: Optional[str] = Field(
        None, description="Sort order for the fleet results: ASC or DESC."
    ),
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort fleets by.",
    ),
) -> list[FleetSummary]:
    """List fleets visible in the requested compartment, handling pagination transparently."""
    fleets: list[FleetSummary] = []

    try:
        client = get_jms_client()

        response: oci.response.Response | None = None
        has_next_page = True
        next_page: Optional[str] = None

        while has_next_page and (limit is None or len(fleets) < limit):
            # Continue paging until OCI stops returning pages or the caller-supplied limit is met.
            response = client.list_fleets(**_omit_none(
                compartment_id=compartment_id,
                id=id,
                lifecycle_state=_normalize_enum(lifecycle_state),
                display_name=display_name,
                display_name_contains=display_name_contains,
                limit=limit,
                sort_order=_normalize_enum(sort_order),
                sort_by=_normalize_choice(sort_by, ["displayName", "timeCreated"]),
                page=next_page,
            ))
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            for item in response.data.items:
                fleets.append(map_fleet_summary(item))
                if limit is not None and len(fleets) >= limit:
                    break

        logger.info(f"Found {len(fleets)} fleets")
        return fleets
    except Exception as e:
        logger.error(f"Error in list_fleets tool: {str(e)}")
        raise


@mcp.tool(description="Get a JMS fleet by its OCID.")
def get_fleet(fleet_id: str = Field(..., description="The OCID of the fleet.")) -> Fleet:
    """Fetch a single fleet by OCID and convert the OCI SDK model into the local Pydantic model."""
    try:
        client = get_jms_client()
        response: oci.response.Response = client.get_fleet(fleet_id=fleet_id)
        logger.info("Found fleet")
        return map_fleet(response.data)
    except Exception as e:
        logger.error(f"Error in get_fleet tool: {str(e)}")
        raise


@mcp.tool(description="List JMS plugins in a compartment or fleet.")
def list_jms_plugins(
    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment in which to list plugins.",
    ),
    compartment_id_in_subtree: bool = Field(
        False,
        description="Whether to gather plugin information from the compartment subtree.",
    ),
    id: Optional[str] = Field(None, description="The OCID of a specific JMS plugin."),
    fleet_id: Optional[str] = Field(None, description="Filter by fleet OCID."),
    agent_id: Optional[str] = Field(None, description="Filter by agent OCID."),
    lifecycle_state: Optional[str] = Field(
        None,
        description=(
            "Filter plugins by lifecycle state. Accepted values include ACTIVE, INACTIVE, "
            "NEEDS_ATTENTION, and DELETED."
        ),
    ),
    availability_status: Optional[str] = Field(
        None,
        description="Filter plugins by availability status: ACTIVE, SILENT, or NOT_AVAILABLE.",
    ),
    agent_type: Optional[str] = Field(
        None,
        description="Filter plugins by agent type: OMA or OCA.",
    ),
    time_registered_less_than_or_equal_to: Optional[str] = Field(
        None,
        description="Only return plugins registered at or before this RFC3339 timestamp.",
    ),
    time_last_seen_less_than_or_equal_to: Optional[str] = Field(
        None,
        description="Only return plugins last seen at or before this RFC3339 timestamp.",
    ),
    hostname_contains: Optional[str] = Field(
        None,
        description="Filter the list with hostname contains this value.",
    ),
    limit: Optional[int] = Field(None, description="Maximum number of plugins to return.", ge=1),
    sort_order: Optional[str] = Field(
        None, description="Sort order for the plugin results: ASC or DESC."
    ),
    sort_by: Optional[str] = Field(None, description="Field to sort plugins by."),
) -> list[JmsPluginSummary]:
    """List JMS plugins with optional fleet, agent, lifecycle, and time-based filtering."""
    plugins: list[JmsPluginSummary] = []

    try:
        client = get_jms_client()

        response: oci.response.Response | None = None
        has_next_page = True
        next_page: Optional[str] = None

        while has_next_page and (limit is None or len(plugins) < limit):
            # Parse timestamp filters up front so the SDK receives native datetimes.
            response = client.list_jms_plugins(**_omit_none(
                compartment_id=compartment_id,
                compartment_id_in_subtree=compartment_id_in_subtree,
                id=id,
                fleet_id=fleet_id,
                agent_id=agent_id,
                lifecycle_state=_normalize_enum(lifecycle_state),
                availability_status=_normalize_enum(availability_status),
                agent_type=_normalize_enum(agent_type),
                time_registered_less_than_or_equal_to=_parse_rfc3339(
                    time_registered_less_than_or_equal_to
                ),
                time_last_seen_less_than_or_equal_to=_parse_rfc3339(
                    time_last_seen_less_than_or_equal_to
                ),
                hostname_contains=hostname_contains,
                limit=limit,
                sort_order=_normalize_enum(sort_order),
                sort_by=_normalize_choice(
                    sort_by,
                    [
                        "id",
                        "timeLastSeen",
                        "timeRegistered",
                        "hostname",
                        "agentId",
                        "agentType",
                        "lifecycleState",
                        "availabilityStatus",
                        "fleetId",
                        "compartmentId",
                        "osFamily",
                        "osArchitecture",
                        "osDistribution",
                        "pluginVersion",
                    ],
                ),
                page=next_page,
            ))
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            for item in response.data.items:
                plugins.append(map_jms_plugin_summary(item))
                if limit is not None and len(plugins) >= limit:
                    break

        logger.info(f"Found {len(plugins)} JMS plugins")
        return plugins
    except Exception as e:
        logger.error(f"Error in list_jms_plugins tool: {str(e)}")
        raise


@mcp.tool(description="Get a JMS plugin by its OCID.")
def get_jms_plugin(
    jms_plugin_id: str = Field(..., description="The OCID of the JMS plugin.")
) -> JmsPlugin:
    """Fetch a single JMS plugin by OCID."""
    try:
        client = get_jms_client()
        response: oci.response.Response = client.get_jms_plugin(jms_plugin_id=jms_plugin_id)
        logger.info("Found JMS plugin")
        return map_jms_plugin(response.data)
    except Exception as e:
        logger.error(f"Error in get_jms_plugin tool: {str(e)}")
        raise


@mcp.tool(description="List Java installation sites in a JMS fleet.")
def list_installation_sites(
    fleet_id: str = Field(..., description="The OCID of the fleet."),
    jre_vendor: Optional[str] = Field(None, description="Filter by JRE vendor."),
    jre_distribution: Optional[str] = Field(None, description="Filter by JRE distribution."),
    jre_version: Optional[str] = Field(None, description="Filter by JRE version."),
    installation_path: Optional[str] = Field(None, description="Filter by installation path."),
    application_id: Optional[str] = Field(None, description="Filter by application identifier."),
    managed_instance_id: Optional[str] = Field(
        None, description="Filter by managed instance identifier."
    ),
    os_family: Optional[list[str]] = Field(None, description="Filter by operating system family."),
    jre_security_status: Optional[str] = Field(
        None,
        description=(
            "Filter by JRE security status. Accepted values include EARLY_ACCESS, UNKNOWN, "
            "UP_TO_DATE, UPDATE_REQUIRED, and UPGRADE_REQUIRED."
        ),
    ),
    path_contains: Optional[str] = Field(
        None,
        description="Filter installation sites where the path contains this value.",
    ),
    time_start: Optional[str] = Field(
        None,
        description="Search start time in RFC3339 format.",
    ),
    time_end: Optional[str] = Field(
        None,
        description="Search end time in RFC3339 format.",
    ),
    limit: Optional[int] = Field(None, description="Maximum number of installation sites to return.", ge=1),
    sort_order: Optional[str] = Field(
        None, description="Sort order for installation sites: ASC or DESC."
    ),
    sort_by: Optional[str] = Field(None, description="Field to sort installation sites by."),
) -> list[InstallationSiteSummary]:
    """List Java installation sites in a fleet with optional runtime, host, and time filters."""
    installation_sites: list[InstallationSiteSummary] = []

    try:
        client = get_jms_client()

        response: oci.response.Response | None = None
        has_next_page = True
        next_page: Optional[str] = None

        while has_next_page and (limit is None or len(installation_sites) < limit):
            # Convert RFC3339 strings before handing them to the OCI SDK search parameters.
            response = client.list_installation_sites(**_omit_none(
                fleet_id=fleet_id,
                jre_vendor=jre_vendor,
                jre_distribution=jre_distribution,
                jre_version=jre_version,
                installation_path=installation_path,
                application_id=application_id,
                managed_instance_id=managed_instance_id,
                os_family=_normalize_enum_list(os_family),
                jre_security_status=_normalize_enum(jre_security_status),
                path_contains=path_contains,
                time_start=_parse_rfc3339(time_start),
                time_end=_parse_rfc3339(time_end),
                limit=limit,
                sort_order=_normalize_enum(sort_order),
                sort_by=_normalize_choice(
                    sort_by,
                    [
                        "managedInstanceId",
                        "jreDistribution",
                        "jreVendor",
                        "jreVersion",
                        "path",
                        "approximateApplicationCount",
                        "osName",
                        "securityStatus",
                    ],
                ),
                page=next_page,
            ))
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            for item in response.data.items:
                installation_sites.append(map_installation_site_summary(item))
                if limit is not None and len(installation_sites) >= limit:
                    break

        logger.info(f"Found {len(installation_sites)} installation sites")
        return installation_sites
    except Exception as e:
        logger.error(f"Error in list_installation_sites tool: {str(e)}")
        raise


@mcp.tool(description="Get fleet agent configuration for a JMS fleet.")
def get_fleet_agent_configuration(
    fleet_id: str = Field(..., description="The OCID of the fleet.")
) -> FleetAgentConfiguration:
    """Return the fleet-wide agent configuration for a JMS fleet."""
    try:
        client = get_jms_client()
        response: oci.response.Response = client.get_fleet_agent_configuration(fleet_id=fleet_id)
        logger.info("Found fleet agent configuration")
        return map_fleet_agent_configuration(response.data)
    except Exception as e:
        logger.error(f"Error in get_fleet_agent_configuration tool: {str(e)}")
        raise


@mcp.tool(description="Get advanced feature configuration for a JMS fleet.")
def get_fleet_advanced_feature_configuration(
    fleet_id: str = Field(..., description="The OCID of the fleet.")
) -> FleetAdvancedFeatureConfiguration:
    """Return the advanced feature configuration for a JMS fleet."""
    try:
        client = get_jms_client()
        response: oci.response.Response = client.get_fleet_advanced_feature_configuration(
            fleet_id=fleet_id
        )
        logger.info("Found fleet advanced feature configuration")
        return map_fleet_advanced_feature_configuration(response.data)
    except Exception as e:
        logger.error(f"Error in get_fleet_advanced_feature_configuration tool: {str(e)}")
        raise


@mcp.tool(description="Summarize JMS resource inventory in a compartment.")
def summarize_resource_inventory(
    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment in which to summarize inventory.",
    ),
    compartment_id_in_subtree: bool = Field(
        False,
        description="Whether to include the compartment subtree in the summary.",
    ),
    time_start: Optional[str] = Field(
        None,
        description="Summary start time in RFC3339 format.",
    ),
    time_end: Optional[str] = Field(
        None,
        description="Summary end time in RFC3339 format.",
    ),
) -> ResourceInventory:
    """Summarize high-level JMS resource counts for a compartment and optional time range."""
    try:
        client = get_jms_client()
        response: oci.response.Response = client.summarize_resource_inventory(**_omit_none(
            compartment_id=compartment_id,
            compartment_id_in_subtree=compartment_id_in_subtree,
            time_start=_parse_rfc3339(time_start),
            time_end=_parse_rfc3339(time_end),
        ))
        logger.info("Summarized resource inventory")
        return map_resource_inventory(response.data)
    except Exception as e:
        logger.error(f"Error in summarize_resource_inventory tool: {str(e)}")
        raise


@mcp.tool(description="Summarize managed instance usage within a JMS fleet.")
def summarize_managed_instance_usage(
    fleet_id: str = Field(..., description="The OCID of the fleet."),
    managed_instance_id: Optional[str] = Field(
        None,
        description="Filter by managed instance OCID.",
    ),
    managed_instance_type: Optional[str] = Field(
        None,
        description=(
            "Filter by managed instance type. Accepted values include "
            "ORACLE_MANAGEMENT_AGENT and ORACLE_CLOUD_AGENT."
        ),
    ),
    jre_vendor: Optional[str] = Field(None, description="Filter by JRE vendor."),
    jre_distribution: Optional[str] = Field(None, description="Filter by JRE distribution."),
    jre_version: Optional[str] = Field(None, description="Filter by JRE version."),
    installation_path: Optional[str] = Field(None, description="Filter by installation path."),
    application_id: Optional[str] = Field(None, description="Filter by application identifier."),
    fields: Optional[list[str]] = Field(
        None, description="Additional fields to include in each usage record."
    ),
    time_start: Optional[str] = Field(None, description="Summary start time in RFC3339 format."),
    time_end: Optional[str] = Field(None, description="Summary end time in RFC3339 format."),
    limit: Optional[int] = Field(None, description="Maximum number of usage records to return.", ge=1),
    sort_order: Optional[str] = Field(
        None, description="Sort order for the usage results: ASC or DESC."
    ),
    sort_by: Optional[str] = Field(None, description="Field to sort usage results by."),
    os_family: Optional[list[str]] = Field(None, description="Filter by operating system family."),
    hostname_contains: Optional[str] = Field(
        None,
        description="Filter the list with hostname contains this value.",
    ),
    library_key: Optional[str] = Field(None, description="Filter by library key."),
) -> list[ManagedInstanceUsage]:
    """Summarize managed instance usage records for a fleet with optional filters."""
    usage: list[ManagedInstanceUsage] = []

    try:
        client = get_jms_client()

        response: oci.response.Response | None = None
        has_next_page = True
        next_page: Optional[str] = None

        while has_next_page and (limit is None or len(usage) < limit):
            # The summarize API is paginated even though it returns aggregate-style records.
            response = client.summarize_managed_instance_usage(**_omit_none(
                fleet_id=fleet_id,
                managed_instance_id=managed_instance_id,
                managed_instance_type=_normalize_enum(managed_instance_type),
                jre_vendor=jre_vendor,
                jre_distribution=jre_distribution,
                jre_version=jre_version,
                installation_path=installation_path,
                application_id=application_id,
                fields=_normalize_choice_list(
                    fields,
                    [
                        "approximateJreCount",
                        "approximateInstallationCount",
                        "approximateApplicationCount",
                    ],
                ),
                time_start=_parse_rfc3339(time_start),
                time_end=_parse_rfc3339(time_end),
                limit=limit,
                sort_order=_normalize_enum(sort_order),
                sort_by=_normalize_choice(
                    sort_by,
                    [
                        "timeFirstSeen",
                        "timeLastSeen",
                        "approximateJreCount",
                        "approximateInstallationCount",
                        "approximateApplicationCount",
                        "osName",
                    ],
                ),
                os_family=_normalize_enum_list(os_family),
                hostname_contains=hostname_contains,
                library_key=library_key,
                page=next_page,
            ))
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            for item in response.data.items:
                usage.append(map_managed_instance_usage(item))
                if limit is not None and len(usage) >= limit:
                    break

        logger.info(f"Found {len(usage)} managed instance usage records")
        return usage
    except Exception as e:
        logger.error(f"Error in summarize_managed_instance_usage tool: {str(e)}")
        raise


@mcp.tool(description="Summarize fleet health using JMS fleet diagnoses and fleet errors.")
def summarize_fleet_health(
    fleet_id: str = Field(..., description="The OCID of the fleet.")
) -> FleetHealthSummary:
    """Return a chat-friendly health summary for a JMS fleet."""
    try:
        client = get_jms_client()
        diagnoses = [
            map_fleet_diagnosis(item)
            for item in _collect_paginated_items(client.list_fleet_diagnoses, fleet_id=fleet_id)
        ]
        fleet_errors = [
            map_fleet_error(item)
            for item in _collect_paginated_items(client.list_fleet_errors, fleet_id=fleet_id)
        ]
        diagnoses = [item for item in diagnoses if item is not None]
        fleet_errors = [item for item in fleet_errors if item is not None]

        return FleetHealthSummary(
            fleet_id=fleet_id,
            diagnosis_count=len(diagnoses),
            fleet_errors=fleet_errors,
            top_issue_categories=_derive_top_issue_categories(diagnoses, fleet_errors),
            overall_health_status=_derive_overall_health_status(diagnoses, fleet_errors),
            recommended_next_checks=_derive_recommended_next_checks(diagnoses, fleet_errors),
        )
    except Exception as e:
        logger.error(f"Error in summarize_fleet_health tool: {str(e)}")
        raise


@mcp.tool(description="Get detailed fleet health diagnostics using JMS diagnoses and fleet errors.")
def get_fleet_health_diagnostics(
    fleet_id: str = Field(..., description="The OCID of the fleet.")
) -> FleetHealthDiagnostics:
    """Return detailed fleet diagnoses and fleet errors for drill-down troubleshooting."""
    try:
        client = get_jms_client()
        diagnoses = [
            map_fleet_diagnosis(item)
            for item in _collect_paginated_items(client.list_fleet_diagnoses, fleet_id=fleet_id)
        ]
        fleet_errors = [
            map_fleet_error(item)
            for item in _collect_paginated_items(client.list_fleet_errors, fleet_id=fleet_id)
        ]
        diagnoses = [item for item in diagnoses if item is not None]
        fleet_errors = [item for item in fleet_errors if item is not None]

        return FleetHealthDiagnostics(
            fleet_id=fleet_id,
            diagnoses=diagnoses,
            fleet_errors=fleet_errors,
            diagnosis_count=len(diagnoses),
            fleet_error_count=len(fleet_errors),
        )
    except Exception as e:
        logger.error(f"Error in get_fleet_health_diagnostics tool: {str(e)}")
        raise


@mcp.tool(description="List JMS announcements and notices.")
def list_jms_notices(
    summary_contains: Optional[str] = Field(
        None,
        description="Filter notices whose summary contains this value.",
    ),
    time_start: Optional[str] = Field(None, description="Search start time in RFC3339 format."),
    time_end: Optional[str] = Field(None, description="Search end time in RFC3339 format."),
    limit: Optional[int] = Field(None, description="Maximum number of notices to return.", ge=1),
    sort_order: Optional[str] = Field(None, description="Sort order for notices: ASC or DESC."),
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort notices by: timeReleased or summary.",
    ),
) -> list[JmsNotice]:
    """List JMS notices and announcements with optional text, time, and sort filters."""
    try:
        client = get_jms_client()
        notices = [
            map_jms_notice(item)
            for item in _collect_paginated_items(
                client.list_announcements,
                summary_contains=summary_contains,
                time_start=_parse_rfc3339(time_start),
                time_end=_parse_rfc3339(time_end),
                limit=limit,
                sort_order=_normalize_enum(sort_order),
                sort_by=_normalize_choice(sort_by, ["timeReleased", "summary"]),
            )
        ]
        return [item for item in notices if item is not None]
    except Exception as e:
        logger.error(f"Error in list_jms_notices tool: {str(e)}")
        raise


@mcp.tool(description="Summarize Java runtime compliance for a JMS fleet.")
def java_runtime_compliance(
    fleet_id: str = Field(..., description="The OCID of the fleet.")
) -> JavaRuntimeComplianceReport:
    """Return a fleet-level Java runtime compliance report enriched with release metadata."""
    try:
        client = get_jms_client()
        usage_rows = _collect_paginated_items(
            client.summarize_jre_usage,
            fleet_id=fleet_id,
            fields=[
                "approximateInstallationCount",
                "approximateApplicationCount",
                "approximateManagedInstanceCount",
            ],
        )

        release_cache: dict[str, object | None] = {}
        version_breakdown: list[JavaRuntimeComplianceBucket] = []
        total_runtimes = 0
        up_to_date_runtimes = 0
        runtimes_requiring_update = 0
        runtimes_requiring_upgrade = 0
        unknown_runtimes = 0
        vendor_values: list[tuple[Optional[str], int]] = []
        distribution_values: list[tuple[Optional[str], int]] = []
        outdated_installations: list[OutdatedJavaInstallation] = []

        for row in usage_rows:
            version = getattr(row, "version", None)
            vendor = getattr(row, "vendor", None)
            distribution = getattr(row, "distribution", None)
            security_status = getattr(row, "security_status", None)
            runtime_count = _normalize_count(getattr(row, "approximate_installation_count", None))
            total_runtimes += runtime_count

            if security_status == "UP_TO_DATE":
                up_to_date_runtimes += runtime_count
            elif security_status == "UPDATE_REQUIRED":
                runtimes_requiring_update += runtime_count
            elif security_status == "UPGRADE_REQUIRED":
                runtimes_requiring_upgrade += runtime_count
            else:
                unknown_runtimes += runtime_count

            vendor_values.append((vendor, runtime_count))
            distribution_values.append((distribution, runtime_count))

            if version not in release_cache:
                # Reuse release lookups across identical versions so the report
                # stays bounded even when multiple usage rows share a release.
                release_cache[version] = _safe_get_java_release(client, version)
            release = release_cache[version]

            version_breakdown.append(
                JavaRuntimeComplianceBucket(
                    version=version,
                    vendor=vendor,
                    distribution=distribution,
                    security_status=security_status,
                    runtime_count=runtime_count,
                    approximate_managed_instance_count=getattr(
                        row, "approximate_managed_instance_count", None
                    ),
                    approximate_application_count=getattr(
                        row, "approximate_application_count", None
                    ),
                    release_date=getattr(release, "release_date", None) if release else None,
                    days_under_security_baseline=getattr(
                        release, "days_under_security_baseline", None
                    )
                    if release
                    else None,
                    license_type=getattr(release, "license_type", None) if release else None,
                    release_type=getattr(release, "release_type", None) if release else None,
                    release_notes_url=getattr(release, "release_notes_url", None) if release else None,
                )
            )

            if (
                security_status in {"UPDATE_REQUIRED", "UPGRADE_REQUIRED"}
                and len(outdated_installations) < _MAX_OUTDATED_INSTALLATIONS
            ):
                # Drill down only for outdated buckets and cap the sample so the
                # tool remains readable while still surfacing concrete fixes.
                remaining = _MAX_OUTDATED_INSTALLATIONS - len(outdated_installations)
                sites = _collect_paginated_items(
                    client.list_installation_sites,
                    fleet_id=fleet_id,
                    jre_version=version,
                    jre_vendor=vendor,
                    jre_distribution=distribution,
                    jre_security_status=security_status,
                    limit=remaining,
                )
                for site in sites:
                    mapped_site = map_installation_site_summary(site)
                    if mapped_site is None:
                        continue
                    outdated_installations.append(
                        OutdatedJavaInstallation(
                            installation_key=mapped_site.installation_key,
                            managed_instance_id=mapped_site.managed_instance_id,
                            path=mapped_site.path,
                            version=mapped_site.jre.version if mapped_site.jre else None,
                            vendor=mapped_site.jre.vendor if mapped_site.jre else None,
                            distribution=mapped_site.jre.distribution if mapped_site.jre else None,
                            security_status=mapped_site.security_status,
                            time_last_seen=mapped_site.time_last_seen,
                        )
                    )

        version_breakdown.sort(
            key=lambda item: (
                -(item.runtime_count or 0),
                item.version or "",
                item.vendor or "",
                item.distribution or "",
            )
        )

        return JavaRuntimeComplianceReport(
            fleet_id=fleet_id,
            total_runtimes_in_fleet=total_runtimes,
            up_to_date_runtimes=up_to_date_runtimes,
            runtimes_requiring_update=runtimes_requiring_update,
            runtimes_requiring_upgrade=runtimes_requiring_upgrade,
            unknown_runtimes=unknown_runtimes,
            version_breakdown=version_breakdown,
            vendor_breakdown=_build_runtime_count_breakdowns(vendor_values),
            distribution_breakdown=_build_runtime_count_breakdowns(distribution_values),
            outdated_installations=outdated_installations,
        )
    except Exception as e:
        logger.error(f"Error in java_runtime_compliance tool: {str(e)}")
        raise


def main():
    """Run the JMS MCP server over stdio by default or HTTP when host and port are provided."""
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
