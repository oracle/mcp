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
    FleetSummary,
    InstallationSiteSummary,
    JmsPlugin,
    JmsPluginSummary,
    ManagedInstanceUsage,
    ResourceInventory,
    map_fleet,
    map_fleet_advanced_feature_configuration,
    map_fleet_agent_configuration,
    map_fleet_summary,
    map_installation_site_summary,
    map_jms_plugin,
    map_jms_plugin_summary,
    map_managed_instance_usage,
    map_resource_inventory,
)
from pydantic import Field

from . import __project__, __version__
from .util import get_jms_service_endpoint

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)

_UNSUPPORTED_ENV_ALIASES = {
    "OCI_CONFIG": "OCI_CONFIG_FILE",
    "OCI_PROFILE": "OCI_CONFIG_PROFILE",
}


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
    return [_normalize_enum(value) for value in values]


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
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


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
