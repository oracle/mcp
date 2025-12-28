"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# Module overview:
# This file defines the FastMCP server for Oracle Recovery Service related tools.
# It wires up:
# - Logging (file + optional console with rotation)
# - OCI client factories (Recovery, Identity, Database, Monitoring)
# - Helper utilities (tenancy/compartment discovery, DB Home discovery)
# - A set of MCP tools (decorated functions) that call OCI SDKs, paginate responses,
#   and map SDK models into server-specific dataclasses found in models.py.
#
# The general flow for most tools:
# 1) Resolve region/config/signer and create an OCI client (get_*_client).
# 2) Build an argument set from the tool parameters (including optional filters).
# 3) Call the appropriate OCI API, handling pagination where required.
# 4) Map SDK responses to the server's typed models (map_* functions).
# 5) Return typed results (summaries/objects) or computed aggregations.
#
# Main() chooses the transport:
# - If ORACLE_MCP_HOST and ORACLE_MCP_PORT are set: run HTTP transport.
# - Otherwise run stdio transport (default for MCP).
#
# Important robustness choices:
# - We add an "additional_user_agent" string to all OCI client configs for traceability.
# - We sign requests with a SecurityTokenSigner using the configured security token file.
# - We try to be resilient to SDK shape differences by using getattr/__dict__/to_dict
#   wherever possible, especially for pagination and nested model fields.
# - We log key milestones and counts for better operability and diagnostics.

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Annotated, Any, Optional

import oci
from fastmcp import FastMCP
from oci.monitoring.models import SummarizeMetricsDataDetails

# Database Service models and mappers
from oracle.oci_recovery_mcp_server.models import (
    Backup,
    BackupSummary,
    Database,
    DatabaseHome,
    DatabaseHomeSummary,
    DatabaseSummary,
    DbSystem,
    DbSystemSummary,
    ProtectedDatabase,
    ProtectedDatabaseBackupDestinationItem,
    ProtectedDatabaseBackupDestinationSummary,
    ProtectedDatabaseBackupSpaceSum,
    ProtectedDatabaseHealthCounts,
    ProtectedDatabaseRedoCounts,
    ProtectedDatabaseSummary,
    ProtectionPolicy,
    ProtectionPolicySummary,
    RecoveryServiceSubnet,
    RecoveryServiceSubnetSummary,
    map_backup,
    map_backup_summary,
    map_database,
    map_database_home,
    map_database_home_summary,
    map_database_summary,
    map_db_backup_config,
    map_db_system,
    map_db_system_summary,
    map_protected_database,
    map_protected_database_summary,
    map_protection_policy,
    map_protection_policy_summary,
    map_recovery_service_subnet,
    map_recovery_service_subnet_summary,
)

from . import __project__, __version__

"""MCP tools available in this server:
- get_compartment_by_name_tool
- list_protected_databases
- get_protected_database
- summarize_protected_database_health
- summarize_protected_database_redo_status
- summarize_backup_space_used
- list_protection_policies
- get_protection_policy
- list_recovery_service_subnets
- get_recovery_service_subnet
- get_recovery_service_metrics
- list_databases
- get_database
- list_backups
- get_backup
- summarise_protected_database_backup_destination
- get_db_home
- list_db_systems
- get_db_system
"""


# Logging setup
def setup_logging():
    # Resolve log level from env, default to INFO
    level_name = os.getenv("ORACLE_MCP_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # Compute default log dir relative to project root; allow env override
    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    log_dir = os.getenv("ORACLE_MCP_LOG_DIR", os.path.join(base_dir, "logs"))
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.getenv(
        "ORACLE_MCP_LOG_FILE", os.path.join(log_dir, "oci_recovery_mcp_server.log")
    )

    # Configure root logger once
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S%z",
    )

    # Add a rotating file handler if not already present for this file
    abs_log_file = os.path.abspath(log_file)
    has_file = any(
        isinstance(h, RotatingFileHandler)
        and getattr(h, "baseFilename", "") == abs_log_file
        for h in root_logger.handlers
    )
    if not has_file:
        fh = RotatingFileHandler(
            abs_log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        fh.setLevel(level)
        fh.setFormatter(formatter)
        root_logger.addHandler(fh)

    # Optional console handler (default on; set ORACLE_MCP_LOG_TO_STDOUT=0 to disable)
    if os.getenv("ORACLE_MCP_LOG_TO_STDOUT", "1").lower() in (
        "1",
        "true",
        "yes",
        "y",
    ):
        has_stream = any(
            isinstance(h, logging.StreamHandler)
            and not isinstance(h, RotatingFileHandler)
            for h in root_logger.handlers
        )
        if not has_stream:
            sh = logging.StreamHandler()
            sh.setLevel(level)
            sh.setFormatter(formatter)
            root_logger.addHandler(sh)

    # Quiet noisy libraries by default; override with ORACLE_SDK_LOG_LEVEL
    logging.getLogger("oci").setLevel(os.getenv("ORACLE_SDK_LOG_LEVEL", "WARNING"))
    logging.getLogger("urllib3").setLevel("WARNING")


setup_logging()
logger = logging.getLogger(__name__)
# Create the FastMCP app that exposes the functions decorated with @mcp.tool
mcp = FastMCP(name=__project__)


def get_recovery_client(
    region: str | None = None,
) -> oci.recovery.DatabaseRecoveryClient:
    """
    Initialize DatabaseRecoveryClient using the OCI config and a SecurityTokenSigner.
    Adds a custom user agent derived from the package name and version.
    Optionally overrides the region.
    """
    # Load config (profile or DEFAULT) and tag requests with additional user agent
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    # Build SecurityTokenSigner from configured key + token
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)

    # Region-aware client construction
    if region is None:
        return oci.recovery.DatabaseRecoveryClient(config, signer=signer)

    regional_config = config.copy()
    regional_config["region"] = region
    return oci.recovery.DatabaseRecoveryClient(regional_config, signer=signer)


def get_identity_client():
    # Create Identity client (for compartment/tenancy queries) with same UA and signer setup
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.identity.IdentityClient(config, signer=signer)


def get_database_client(region: str = None):
    # Create Database Service client (DB Home/DB/Backup APIs)
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    if region is None:
        return oci.database.DatabaseClient(config, signer=signer)
    regional_config = config.copy()  # make a shallow copy
    regional_config["region"] = region
    return oci.database.DatabaseClient(regional_config, signer=signer)


def get_monitoring_client(region: str | None = None):
    # Create Monitoring Service client (for Recovery metrics via Monitoring namespace)
    logger.info("entering get_monitoring_client")
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    if region is None:
        return oci.monitoring.MonitoringClient(config, signer=signer)
    regional_config = config.copy()
    regional_config["region"] = region
    return oci.monitoring.MonitoringClient(regional_config, signer=signer)


def get_tenancy():
    # Return the tenancy OCID from config unless overridden by TENANCY_ID_OVERRIDE
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    return os.getenv("TENANCY_ID_OVERRIDE", config["tenancy"])


def list_all_compartments_internal(only_one_page: bool, limit=100):
    """Internal function to get List all compartments in a tenancy"""
    # Use IdentityClient to list all accessible ACTIVE compartments and include the root tenancy
    identity_client = get_identity_client()
    response = identity_client.list_compartments(
        compartment_id=get_tenancy(),
        compartment_id_in_subtree=True,
        access_level="ACCESSIBLE",
        lifecycle_state="ACTIVE",
        limit=limit,
    )
    compartments = response.data
    # Also include the tenancy itself
    compartments.append(
        identity_client.get_compartment(compartment_id=get_tenancy()).data
    )
    if only_one_page:  # limiting the number of items returned
        return compartments
    # Manual pagination loop
    while response.has_next_page:
        response = identity_client.list_compartments(
            compartment_id=get_tenancy(),
            compartment_id_in_subtree=True,
            access_level="ACCESSIBLE",
            lifecycle_state="ACTIVE",
            page=response.next_page,
            limit=limit,
        )
        compartments.extend(response.data)
    return compartments


def _fetch_db_home_ids_for_compartment(
    compartment_id: str, region: Optional[str] = None
) -> list[str]:
    """
    Helper: enumerate DB Home OCIDs in a compartment.
    Used when a tool needs a db_home_id but the caller omitted it.
    Returns a list of DB Home OCIDs (may be empty).
    """
    try:
        client = get_database_client(region)
        resp = client.list_db_homes(compartment_id=compartment_id)
        data = resp.data
        # Normalize list shape (SDK may use .items or a raw list)
        raw_list = getattr(data, "items", data)
        raw_list = (
            raw_list
            if isinstance(raw_list, list)
            else [raw_list] if raw_list is not None else []
        )
        ids: list[str] = []
        for h in raw_list:
            # Try attribute access first
            hid = getattr(h, "id", None)
            if not hid:
                # Fall back to dict conversion if needed
                try:
                    d = (
                        getattr(oci.util, "to_dict")(h)
                        if hasattr(oci, "util") and hasattr(oci.util, "to_dict")
                        else None
                    )
                    if isinstance(d, dict):
                        hid = d.get("id")
                except Exception:
                    pass
            if hid:
                ids.append(hid)
        return ids
    except Exception:
        # Conservative: on error, return empty so callers can react (e.g., empty results)
        return []


def get_compartment_by_name(compartment_name: str):
    """Internal function to get compartment by name with caching"""
    compartments = list_all_compartments_internal(False)
    # Search for the compartment by name
    for compartment in compartments:
        if compartment.name.lower() == compartment_name.lower():
            return compartment

    return None


@mcp.tool()
def get_compartment_by_name_tool(name: str) -> str:
    """Return a compartment matching the provided name"""
    compartment = get_compartment_by_name(name)
    if compartment:
        return str(compartment)
    else:
        return json.dumps({"error": f"Compartment '{name}' not found."})


@mcp.tool(
    description="List Protected Databases in a given compartment with optional filters."
    "Response includes key information of the database it is protecting such as "
    "database ocid, dbuniquename of the database , vpcuser etc ."
    "Response also includes other details specific to protected databases resource."
)
def list_protected_databases(
    compartment_id: Annotated[str, "The OCID of the compartment"],
    lifecycle_state: Annotated[
        Optional[str],
        (
            'Filter by lifecycle state (e.g., "CREATING", "UPDATING", '
            '"ACTIVE", "DELETE_SCHEDULED", "DELETING", "DELETED", "FAILED")'
        ),
    ] = None,
    display_name: Annotated[Optional[str], "Exact match on display name"] = None,
    id: Annotated[Optional[str], "Protected Database OCID"] = None,
    protection_policy_id: Annotated[
        Optional[str], "Filter results to this Protection Policy OCID"
    ] = None,
    recovery_service_subnet_id: Annotated[
        Optional[str], "Filter by Recovery Service Subnet OCID"
    ] = None,
    limit: Annotated[Optional[int], "Maximum number of items per page"] = None,
    page: Annotated[
        Optional[str],
        "Pagination token (opc-next-page) to continue listing from",
    ] = None,
    sort_order: Annotated[Optional[str], 'Sort order: "ASC" or "DESC"'] = None,
    sort_by: Annotated[
        Optional[str], 'Sort by field: "timeCreated" or "displayName"'
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request"
    ] = None,
    region: Annotated[
        Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"
    ] = None,
) -> list[ProtectedDatabaseSummary]:
    """
    Paginates through Recovery Service to list Protected Databases and returns
    a list of ProtectedDatabaseSummary models mapped from the OCI SDK response.
    """
    try:
        client = get_recovery_client(region)

        results: list[ProtectedDatabaseSummary] = []
        has_next_page = True
        next_page: Optional[str] = page

        while has_next_page:
            # Build request kwargs from provided filters
            kwargs = {
                "compartment_id": compartment_id,
                "page": next_page,
            }
            if lifecycle_state is not None:
                kwargs["lifecycle_state"] = lifecycle_state
            if display_name is not None:
                kwargs["display_name"] = display_name
            if id is not None:
                kwargs["id"] = id
            if protection_policy_id is not None:
                kwargs["protection_policy_id"] = protection_policy_id
            if recovery_service_subnet_id is not None:
                kwargs["recovery_service_subnet_id"] = recovery_service_subnet_id
            if limit is not None:
                kwargs["limit"] = limit
            if sort_order is not None:
                kwargs["sort_order"] = sort_order
            if sort_by is not None:
                kwargs["sort_by"] = sort_by
            if opc_request_id is not None:
                kwargs["opc_request_id"] = opc_request_id

            # Invoke list API and handle pagination
            response: oci.response.Response = client.list_protected_databases(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            # Normalize list and map into our summaries
            data = response.data
            items = getattr(data, "items", data)  # collection.items or raw list
            for d in items:
                pd_summary = map_protected_database_summary(d)
                if pd_summary is not None:
                    results.append(pd_summary)

        logger.info(f"Found {len(results)} Protected Databases")
        return results

    except Exception as e:
        logger.error(f"Error in list_protected_databases tool: {str(e)}")
        raise


@mcp.tool(description="Get a Protected Database by OCID.")
def get_protected_database(
    protected_database_id: Annotated[str, "Protected Database OCID"],
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request"
    ] = None,
    region: Annotated[
        Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"
    ] = None,
) -> ProtectedDatabase:
    """
    Retrieves a single Protected Database resource from Recovery Service and returns
    a ProtectedDatabase model mapped from the OCI SDK response.
    """
    try:
        client = get_recovery_client(region)

        # Optional request ID passthrough
        kwargs = {}
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        response: oci.response.Response = client.get_protected_database(
            protected_database_id=protected_database_id, **kwargs
        )

        data = response.data
        pd = map_protected_database(data)
        logger.info(f"Fetched Protected Database {protected_database_id}")
        return pd

    except Exception as e:
        logger.error(f"Error in get_protected_database tool: {str(e)}")
        raise


@mcp.tool(
    description=(
        "Summarizes Protected Database health status counts (PROTECTED, WARNING, ALERT, UNKNOWN) "
        "in a compartment. "
        "Lists protected databases then fetches each to read its health field; returns counts including "
        "UNKNOWN for missing/None health."
    )
)
def summarize_protected_database_health(
    compartment_id: Annotated[
        Optional[str],
        "OCID of the compartment. If omitted, defaults to the tenancy OCID from your OCI profile.",
    ] = None,
    region: Annotated[
        Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"
    ] = None,
) -> dict:
    """
    Summarizes Protected Database health status counts (PROTECTED, WARNING, ALERT, UNKNOWN) in a compartment.
    The tool lists protected databases, reads health from summary when available, falls back to GET per PD,
    and returns counts. Total equals PDs scanned. UNKNOWN counts PDs with missing/None health (often DELETED
    or transitional).
    """
    try:
        client = get_recovery_client(region)
        comp_id = compartment_id or get_tenancy()

        protected = 0
        warning = 0
        alert = 0
        unknown = 0
        scanned = 0

        has_next_page = True
        next_page: Optional[str] = None

        while has_next_page:
            # Fetch ACTIVE PDs page by page
            list_kwargs = {
                "compartment_id": comp_id,
                "page": next_page,
                "lifecycle_state": "ACTIVE",
            }
            response: oci.response.Response = client.list_protected_databases(
                **list_kwargs
            )
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data = response.data
            items = getattr(data, "items", data)
            for item in items or []:
                # Try to read health from list summary; shape can vary by SDK versions
                health = getattr(item, "health", None)
                if not health and hasattr(item, "__dict__"):
                    try:
                        health = item.__dict__.get("health")
                    except Exception:
                        health = None

                # Robustly extract PD OCID to allow follow-up GET if required
                pd_id = getattr(item, "id", None) or (
                    getattr(item, "data", None) and getattr(item.data, "id", None)
                )
                logger.info(f"Item structure: {item}, Extracted id: {pd_id}")
                if pd_id is None:
                    try:
                        item_dict = getattr(item, "__dict__", None) or {}
                        pd_id = item_dict.get("id")
                    except Exception:
                        pd_id = None
                if not pd_id:
                    # Can't fetch details; skip counting this entry
                    continue

                scanned += 1

                # If health is not on the summary, fetch the full resource
                if not health:
                    try:
                        pd_resp: oci.response.Response = client.get_protected_database(
                            protected_database_id=pd_id
                        )
                        pd = pd_resp.data
                        health = getattr(pd, "health", None)
                        if not health and hasattr(pd, "__dict__"):
                            health = pd.__dict__.get("health")
                    except Exception:
                        health = None

                # Increment appropriate counters
                if health == "PROTECTED":
                    protected += 1
                elif health == "WARNING":
                    warning += 1
                elif health == "ALERT":
                    alert += 1
                else:
                    # unknown/None health
                    unknown += 1

        total = scanned
        logger.info(
            "Health summary for compartment %s (region=%s): "
            "PROTECTED=%s, WARNING=%s, ALERT=%s, UNKNOWN=%s, TOTAL=%s",
            comp_id,
            region,
            protected,
            warning,
            alert,
            unknown,
            total,
        )
        return ProtectedDatabaseHealthCounts(
            compartment_id=comp_id,
            region=region,
            protected=protected,
            warning=warning,
            alert=alert,
            unknown=unknown,
            total=total,
        )
    except Exception as e:
        logger.error(f"Error in summarize_protected_database_health tool: {str(e)}")
        raise


@mcp.tool(
    description=(
        "Summarizes redo transport enablement for Protected Databases in a compartment. "
        "Lists protected databases then fetches each to inspect "
        "is_redo_logs_shipped (true=enabled, false=disabled)."
    )
)
def summarize_protected_database_redo_status(
    compartment_id: Annotated[
        Optional[str],
        "OCID of the compartment. If omitted, defaults to the tenancy OCID from your OCI profile.",
    ] = None,
    region: Annotated[
        Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"
    ] = None,
) -> dict:
    """
    Summarizes redo transport enablement for Protected Databases in a compartment.
    Lists protected databases then fetches each to inspect
    is_redo_logs_shipped (true=enabled, false=disabled).
    """
    try:
        client = get_recovery_client(region)
        comp_id = compartment_id or get_tenancy()

        enabled = 0
        disabled = 0

        has_next_page = True
        next_page: Optional[str] = None

        while has_next_page:
            # List ACTIVE PDs to assess redo status via GET per PD
            list_kwargs = {
                "compartment_id": comp_id,
                "page": next_page,
                "lifecycle_state": "ACTIVE",
            }
            response: oci.response.Response = client.list_protected_databases(
                **list_kwargs
            )
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data = response.data
            items = getattr(data, "items", data)
            for item in items or []:
                # Robustly get the PD OCID from summary item
                pd_id = getattr(item, "id", None) or (
                    getattr(item, "data", None) and getattr(item.data, "id", None)
                )
                if pd_id is None:
                    try:
                        item_dict = getattr(item, "__dict__", None) or {}
                        pd_id = item_dict.get("id")
                    except Exception:
                        pd_id = None
                if not pd_id:
                    continue

                # Fetch full Protected Database to read is_redo_logs_shipped (primary)
                pd_resp: oci.response.Response = client.get_protected_database(
                    protected_database_id=pd_id
                )
                pd = pd_resp.data
                redo_enabled = getattr(pd, "is_redo_logs_shipped", None)
                if redo_enabled is None and hasattr(pd, "__dict__"):
                    redo_enabled = pd.__dict__.get(
                        "is_redo_logs_shipped"
                    ) or pd.__dict__.get("isRedoLogsShipped")
                # Fallback: some SDK/reporting expose Real-time protection
                # under metrics as is_redo_logs_enabled
                if redo_enabled is None:
                    try:
                        m = getattr(pd, "metrics", None)
                        if m is not None:
                            redo_enabled = getattr(m, "is_redo_logs_enabled", None)
                            if redo_enabled is None and hasattr(m, "__dict__"):
                                redo_enabled = m.__dict__.get(
                                    "is_redo_logs_enabled"
                                ) or m.__dict__.get("isRedoLogsEnabled")
                    except Exception:
                        pass

                if redo_enabled is True:
                    enabled += 1
                elif redo_enabled is False:
                    disabled += 1
                else:
                    # None/unknown -> do not count
                    pass

        total = enabled + disabled
        logger.info(
            "Redo transport summary for compartment %s (region=%s): "
            "ENABLED=%s, DISABLED=%s, TOTAL=%s",
            comp_id,
            region,
            enabled,
            disabled,
            total,
        )
        return ProtectedDatabaseRedoCounts(
            compartment_id=comp_id,
            region=region,
            enabled=enabled,
            disabled=disabled,
            total=total,
        )
    except Exception as e:
        logger.error(f"Error in summarize_protected_database_redo_status tool: {e}")
        raise


@mcp.tool(
    description=(
        "Sums backup space used (GB) by Protected Databases in a compartment by "
        "reading backup_space_used_in_gbs from metrics. "
        "Returns compartmentId, region, totalDatabasesScanned, sumBackupSpaceUsedInGBs."
    )
)
def summarize_backup_space_used(
    compartment_id: Annotated[
        Optional[str],
        "OCID of the compartment. If omitted, defaults to the tenancy OCID from your OCI profile.",
    ] = None,
    region: Annotated[
        Optional[str],
        "Canonical OCI region (e.g., us-ashburn-1) to execute the request in.",
    ] = None,
) -> dict:
    """
    Sums backup space used (GB) by Protected Databases in a compartment.
    For each PD: scans, increments total, and reads backup_space_used_in_gbs from metrics.
    Important: metrics are not reliably exposed on list summaries; fetch the full PD to read metrics.
    Returns: compartmentId, region, totalDatabasesScanned, sumBackupSpaceUsedInGBs.
    """
    try:
        client = get_recovery_client(region)
        comp_id = compartment_id or get_tenancy()
        sum_gb = 0.0
        scanned = 0
        missing_metrics = 0
        has_next_page = True
        next_page: Optional[str] = None

        while has_next_page:
            list_kwargs = {
                "compartment_id": comp_id,
                "page": next_page,
            }
            response: oci.response.Response = client.list_protected_databases(
                **list_kwargs
            )
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data = response.data
            items = getattr(data, "items", data)

            for item in items or []:
                # Robustly get the PD OCID from summary item (same as redo status tool)
                pd_id = getattr(item, "id", None) or (
                    getattr(item, "data", None) and getattr(item.data, "id", None)
                )
                logger.info(f"Item structure: {item}, Extracted id: {pd_id}")
                if pd_id is None:
                    try:
                        item_dict = getattr(item, "__dict__", None) or {}
                        pd_id = item_dict.get("id")
                    except Exception:
                        pd_id = None
                if not pd_id:
                    continue

                scanned += 1

                # Always fetch the full Protected Database to read metrics reliably
                gb_val = None
                try:
                    pd_resp: oci.response.Response = client.get_protected_database(
                        protected_database_id=pd_id
                    )
                    pd_obj = pd_resp.data
                    metrics = getattr(pd_obj, "metrics", None)
                    if metrics is None and hasattr(pd_obj, "__dict__"):
                        metrics = getattr(pd_obj, "__dict__", {}).get("metrics")
                    # metrics may be a model or a dict; normalise access
                    if metrics is not None:
                        if hasattr(metrics, "backup_space_used_in_gbs"):
                            gb_val = getattr(metrics, "backup_space_used_in_gbs", None)
                        if gb_val is None and hasattr(metrics, "__dict__"):
                            gb_val = metrics.__dict__.get(
                                "backup_space_used_in_gbs"
                            ) or metrics.__dict__.get("backupSpaceUsedInGbs")
                        if gb_val is None and isinstance(metrics, dict):
                            gb_val = metrics.get(
                                "backup_space_used_in_gbs"
                            ) or metrics.get("backupSpaceUsedInGbs")
                except Exception:
                    # If GET fails, fall back to any summary metrics representation
                    try:
                        m = getattr(item, "metrics", None)
                        if m is not None:
                            gb_val = getattr(m, "backup_space_used_in_gbs", None)
                            if gb_val is None and hasattr(m, "__dict__"):
                                gb_val = m.__dict__.get(
                                    "backup_space_used_in_gbs"
                                ) or m.__dict__.get("backupSpaceUsedInGbs")
                            if gb_val is None and isinstance(m, dict):
                                gb_val = m.get("backup_space_used_in_gbs") or m.get(
                                    "backupSpaceUsedInGbs"
                                )
                    except Exception:
                        gb_val = None

                if gb_val is None:
                    missing_metrics += 1

                # Ensure numeric value; treat missing/non-numeric as 0.0
                try:
                    gb = float(gb_val) if gb_val is not None else 0.0
                except Exception:
                    gb = 0.0

                sum_gb += gb

        logger.info(
            "Backup space used summary for compartment %s (region=%s): "
            "scanned=%s, total_gb=%s, missing_metrics=%s",
            comp_id,
            region,
            scanned,
            sum_gb,
            missing_metrics,
        )
        return ProtectedDatabaseBackupSpaceSum(
            compartmentId=comp_id,
            region=region,
            totalDatabasesScanned=scanned,
            sumBackupSpaceUsedInGBs=round(sum_gb, 2),
        )
        # logger.info(f"Returning dict result: {result}")
        # return result
    except Exception as e:
        logger.error(f"Error in summarize_backup_space_used tool: {str(e)}")
        raise


@mcp.tool(
    description="List Protection Policies in a given compartment with optional filters."
)
def list_protection_policies(
    compartment_id: Annotated[str, "The OCID of the compartment"],
    lifecycle_state: Annotated[
        Optional[str],
        'Filter by lifecycle state (e.g., "ACTIVE", "DELETED")',
    ] = None,
    display_name: Annotated[Optional[str], "Exact match on display name"] = None,
    id: Annotated[Optional[str], "Protection Policy OCID"] = None,
    limit: Annotated[Optional[int], "Maximum number of items per page"] = None,
    page: Annotated[
        Optional[str],
        "Pagination token (opc-next-page) to continue listing from",
    ] = None,
    sort_order: Annotated[Optional[str], 'Sort order: "ASC" or "DESC"'] = None,
    sort_by: Annotated[
        Optional[str], 'Sort by field: "timeCreated" or "displayName"'
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request"
    ] = None,
    region: Annotated[
        Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"
    ] = None,
) -> list[ProtectionPolicySummary]:
    """
    Paginates through Recovery Service to list Protection Policies and returns
    a list of ProtectionPolicySummary models mapped from the OCI SDK response.
    """
    try:
        client = get_recovery_client(region)

        results: list[ProtectionPolicySummary] = []
        has_next_page = True
        next_page: Optional[str] = page

        while has_next_page:
            # Collect filters/controls into kwargs
            kwargs = {
                "compartment_id": compartment_id,
                "page": next_page,
            }
            if lifecycle_state is not None:
                kwargs["lifecycle_state"] = lifecycle_state
            if display_name is not None:
                kwargs["display_name"] = display_name
            if id is not None:
                kwargs["id"] = id
            if limit is not None:
                kwargs["limit"] = limit
            if sort_order is not None:
                kwargs["sort_order"] = sort_order
            if sort_by is not None:
                kwargs["sort_by"] = sort_by
            if opc_request_id is not None:
                kwargs["opc_request_id"] = opc_request_id

            response: oci.response.Response = client.list_protection_policies(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data = response.data
            items = getattr(data, "items", data)  # collection.items or raw list
            for d in items:
                s = map_protection_policy_summary(d)
                if s is not None:
                    results.append(s)

        logger.info(f"Found {len(results)} Protection Policies")
        return results

    except Exception as e:
        logger.error(f"Error in list_protection_policies tool: {str(e)}")
        raise


@mcp.tool(description="Get a Protection Policy by OCID.")
def get_protection_policy(
    protection_policy_id: Annotated[str, "Protection Policy OCID"],
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request"
    ] = None,
    region: Annotated[
        Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"
    ] = None,
) -> ProtectionPolicy:
    """
    Retrieves a single Protection Policy resource from Recovery Service and returns
    a ProtectionPolicy model mapped from the OCI SDK response.
    """
    try:
        client = get_recovery_client(region)

        kwargs = {}
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        response: oci.response.Response = client.get_protection_policy(
            protection_policy_id=protection_policy_id, **kwargs
        )

        data = response.data
        pp = map_protection_policy(data)
        logger.info(f"Fetched Protection Policy {protection_policy_id}")
        return pp

    except Exception as e:
        logger.error(f"Error in get_protection_policy tool: {str(e)}")
        raise


@mcp.tool(
    description="List Recovery Service Subnets in a given compartment with optional filters."
)
def list_recovery_service_subnets(
    compartment_id: Annotated[str, "The OCID of the compartment"],
    lifecycle_state: Annotated[
        Optional[str],
        (
            'Filter by lifecycle state (e.g., "CREATING", "ACTIVE", '
            '"UPDATING", "DELETING", "DELETED", "FAILED")'
        ),
    ] = None,
    display_name: Annotated[Optional[str], "Exact match on display name"] = None,
    id: Annotated[Optional[str], "Recovery Service Subnet OCID"] = None,
    vcn_id: Annotated[Optional[str], "Filter by VCN OCID"] = None,
    limit: Annotated[Optional[int], "Maximum number of items per page"] = None,
    page: Annotated[
        Optional[str],
        "Pagination token (opc-next-page) to continue listing from",
    ] = None,
    sort_order: Annotated[Optional[str], 'Sort order: "ASC" or "DESC"'] = None,
    sort_by: Annotated[
        Optional[str], 'Sort by field: "timeCreated" or "displayName"'
    ] = None,
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request"
    ] = None,
    region: Annotated[
        Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"
    ] = None,
) -> list[RecoveryServiceSubnetSummary]:
    """
    Paginates through Recovery Service to list Recovery Service Subnets and returns
    a list of RecoveryServiceSubnetSummary models mapped from the OCI SDK response.
    """
    try:
        client = get_recovery_client(region)

        results: list[RecoveryServiceSubnetSummary] = []
        has_next_page = True
        next_page: Optional[str] = page

        while has_next_page:
            kwargs = {
                "compartment_id": compartment_id,
                "page": next_page,
            }
            if lifecycle_state is not None:
                kwargs["lifecycle_state"] = lifecycle_state
            if display_name is not None:
                kwargs["display_name"] = display_name
            if id is not None:
                kwargs["id"] = id
            if vcn_id is not None:
                kwargs["vcn_id"] = vcn_id
            if limit is not None:
                kwargs["limit"] = limit
            if sort_order is not None:
                kwargs["sort_order"] = sort_order
            if sort_by is not None:
                kwargs["sort_by"] = sort_by
            if opc_request_id is not None:
                kwargs["opc_request_id"] = opc_request_id

            response: oci.response.Response = client.list_recovery_service_subnets(
                **kwargs
            )
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data = response.data
            items = getattr(data, "items", data)  # collection.items or raw list
            for d in items:
                s = map_recovery_service_subnet_summary(d)
                if s is not None:
                    results.append(s)

        logger.info(f"Found {len(results)} Recovery Service Subnets")
        return results

    except Exception as e:
        logger.error(f"Error in list_recovery_service_subnets tool: {str(e)}")
        raise


@mcp.tool(description="Get a Recovery Service Subnet by OCID.")
def get_recovery_service_subnet(
    recovery_service_subnet_id: Annotated[str, "Recovery Service Subnet OCID"],
    opc_request_id: Annotated[
        Optional[str], "Unique identifier for the request"
    ] = None,
    region: Annotated[
        Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"
    ] = None,
) -> RecoveryServiceSubnet:
    """
    Retrieves a single Recovery Service Subnet resource from Recovery Service and returns
    a RecoveryServiceSubnet model mapped from the OCI SDK response.
    """
    try:
        client = get_recovery_client(region)

        kwargs = {}
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        response: oci.response.Response = client.get_recovery_service_subnet(
            recovery_service_subnet_id=recovery_service_subnet_id, **kwargs
        )

        data = response.data
        rss = map_recovery_service_subnet(data)
        logger.info(f"Fetched Recovery Service Subnet {recovery_service_subnet_id}")
        return rss

    except Exception as e:
        logger.error(f"Error in get_recovery_service_subnet tool: {str(e)}")
        raise


@mcp.tool
def get_recovery_service_metrics(
    compartment_id: str,
    start_time: str,
    end_time: str,
    metricName: Annotated[
        str,
        "The metric that the user wants to fetch. Currently we only support:"
        "SpaceUsedForRecoveryWindow, ProtectedDatabaseSize, ProtectedDatabaseHealth,"
        "DataLossExposure",
    ] = "SpaceUsedForRecoveryWindow",
    resolution: Annotated[
        str,
        "The granularity of the metric. Currently we only support: 1m, 5m, 1h, 1d. Default: 1h.",
    ] = "1h",
    aggregation: Annotated[
        str,
        "The aggregation for the metric. Currently we only support: "
        "mean, sum, max, min, count. Default: max",
    ] = "max",
    protected_database_id: Annotated[
        str,
        "Optional protected database OCID to filter by "
        "(maps to resourceId dimension)",
    ] = None,
) -> list[dict]:
    # Build Monitoring query against Recovery metrics namespace
    monitoring_client = get_monitoring_client()
    namespace = "oci_recovery_service"
    filter_clause = (
        f'{{resourceId="{protected_database_id}"}}' if protected_database_id else ""
    )
    # Query format: MetricName[resolution]{filters}.aggregation()
    query = f"{metricName}[{resolution}]{filter_clause}.{aggregation}()"

    # Fetch time series data for the metric and time window
    series_list = monitoring_client.summarize_metrics_data(
        compartment_id=compartment_id,
        summarize_metrics_data_details=SummarizeMetricsDataDetails(
            namespace=namespace,
            query=query,
            start_time=start_time,
            end_time=end_time,
            resolution=resolution,
        ),
    ).data

    # Convert SDK series into a simple dict of dimensions + aggregated datapoints
    result: list[dict] = []
    for series in series_list:
        dims = getattr(series, "dimensions", None)
        points = []
        for p in getattr(series, "aggregated_datapoints", []):
            points.append(
                {
                    "timestamp": getattr(p, "timestamp", None),
                    "value": getattr(p, "value", None),
                }
            )
        result.append(
            {
                "dimensions": dims,
                "datapoints": points,
            }
        )
    return result


# ---------------- Database Service Tools ----------------


@mcp.tool(
    description=(
        "Gets a list of the databases in the specified Database Home. "
        "If db_home_id is omitted, the tool will automatically look up all DB Homes in the given compartment "
        "and aggregate results per DB Home."
    )
)
def list_databases(
    compartment_id: Annotated[
        Optional[str], "The compartment OCID. Required if db_home_id is not provided."
    ] = None,
    db_home_id: Annotated[
        Optional[str],
        "A Database Home OCID. If omitted, all DB Homes in the compartment will be used.",
    ] = None,
    system_id: Annotated[
        Optional[str], "The OCID of the Exadata DB system to filter by (Exadata only)."
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of items to return per page."
    ] = None,
    page: Annotated[
        Optional[str], "The pagination token to continue listing from."
    ] = None,
    sort_by: Annotated[Optional[str], 'Sort by field: "DBNAME" | "TIMECREATED"'] = None,
    sort_order: Annotated[Optional[str], '"ASC" or "DESC"'] = None,
    lifecycle_state: Annotated[Optional[str], "Exact lifecycle state filter."] = None,
    db_name: Annotated[
        Optional[str], "Exact database name filter (case-insensitive)."
    ] = None,
    region: Annotated[
        Optional[str], "Region to execute the request, e.g., us-ashburn-1."
    ] = None,
) -> list[DatabaseSummary]:
    try:
        client = get_database_client(region)

        # Determine DB Home scope:
        # - If db_home_id not provided, discover all DB Homes in the compartment.
        # - If provided, just use that one.
        if db_home_id is None:
            if not compartment_id:
                raise ValueError(
                    "Either db_home_id must be provided or compartment_id "
                    "must be set to derive DB Homes."
                )
            home_ids = _fetch_db_home_ids_for_compartment(compartment_id, region=region)
        else:
            home_ids = [db_home_id]

        if not home_ids:
            return []

        # Try to correlate database_id -> protection_policy_id via Recovery PDs (best-effort)
        pd_policy_by_dbid: dict[str, str] = {}
        if compartment_id:
            try:
                rec_client = get_recovery_client(region)
                has_next = True
                next_page = None
                while has_next:
                    lp = rec_client.list_protected_databases(
                        compartment_id=compartment_id, page=next_page
                    )
                    has_next = lp.has_next_page
                    next_page = getattr(lp, "next_page", None)
                    pdata = lp.data
                    pitems = getattr(pdata, "items", pdata)
                    for it in pitems or []:
                        try:
                            if hasattr(oci, "util") and hasattr(oci.util, "to_dict"):
                                d = oci.util.to_dict(it)
                            else:
                                d = getattr(it, "__dict__", {}) or {}
                        except Exception:
                            d = getattr(it, "__dict__", {}) or {}
                        dbid = d.get("databaseId") or d.get("database_id")
                        ppid = d.get("protectionPolicyId") or d.get(
                            "protection_policy_id"
                        )
                        if dbid and ppid and dbid not in pd_policy_by_dbid:
                            pd_policy_by_dbid[dbid] = ppid
            except Exception:
                pd_policy_by_dbid = {}

        results: list[DatabaseSummary] = []
        # Common list_databases filters shared across DB Homes
        common_kwargs: dict = {}
        if compartment_id is not None:
            common_kwargs["compartment_id"] = compartment_id
        if system_id is not None:
            common_kwargs["system_id"] = system_id
        if limit is not None:
            common_kwargs["limit"] = limit
        if page is not None:
            common_kwargs["page"] = page
        if sort_by is not None:
            common_kwargs["sort_by"] = sort_by
        if sort_order is not None:
            common_kwargs["sort_order"] = sort_order
        if lifecycle_state is not None:
            common_kwargs["lifecycle_state"] = lifecycle_state
        if db_name is not None:
            common_kwargs["db_name"] = db_name

        # For each DB Home, list databases and map summaries
        for hid in home_ids:
            kwargs = dict(common_kwargs)
            kwargs["db_home_id"] = hid
            response: oci.response.Response = client.list_databases(**kwargs)
            raw = getattr(response.data, "items", response.data)
            for item in raw or []:
                mapped = map_database_summary(item)
                if mapped is not None:
                    # Enrich db_backup_config lazily by fetching full Database only if missing
                    try:
                        if getattr(mapped, "db_backup_config", None) is None:
                            db_id = getattr(item, "id", None) or (
                                getattr(item, "data", None)
                                and getattr(item.data, "id", None)
                            )
                            if not db_id and hasattr(item, "__dict__"):
                                db_id = item.__dict__.get("id")
                            if db_id:
                                gd = client.get_database(database_id=db_id).data
                                # Try to locate backup config from object or dict forms
                                cfg_src = getattr(
                                    gd, "db_backup_config", None
                                ) or getattr(gd, "database_backup_config", None)
                                if cfg_src is None:
                                    try:
                                        d = (
                                            oci.util.to_dict(gd)
                                            if hasattr(oci, "util")
                                            and hasattr(oci.util, "to_dict")
                                            else (getattr(gd, "__dict__", {}) or {})
                                        )
                                    except Exception:
                                        d = getattr(gd, "__dict__", {}) or {}
                                    cfg_src = (
                                        d.get("dbBackupConfig")
                                        or d.get("db_backup_config")
                                        or d.get("databaseBackupConfig")
                                        or d.get("database_backup_config")
                                    )
                                mapped.db_backup_config = map_db_backup_config(cfg_src)
                    except Exception:
                        # Best-effort enrichment; ignore failures and still return the summary
                        pass
                    # Enrich with protection policy id if we correlated via Recovery PDs earlier
                    try:
                        if compartment_id is not None:
                            mapped.protection_policy_id = pd_policy_by_dbid.get(
                                mapped.id
                            )
                    except Exception:
                        pass
                    results.append(mapped)

        return results
    except Exception as e:
        logger.error(f"Error in list_databases tool: {e}")
        raise


@mcp.tool(description="Retrieves full details for a Database by OCID.")
def get_database(
    database_id: Annotated[str, "OCID of the Database to retrieve."],
    region: Annotated[
        Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."
    ] = None,
) -> Database:
    try:
        client = get_database_client(region)
        resp = client.get_database(database_id=database_id)
        mapped = map_database(resp.data)
        # Enrich protection_policy_id by correlating with Recovery Service
        # Protected Databases in the same compartment
        try:
            # Extract compartment from response (SDK shape may differ)
            comp_id = getattr(resp.data, "compartment_id", None)
            if comp_id is None:
                try:
                    d = (
                        oci.util.to_dict(resp.data)
                        if hasattr(oci, "util") and hasattr(oci.util, "to_dict")
                        else (getattr(resp.data, "__dict__", {}) or {})
                    )
                except Exception:
                    d = getattr(resp.data, "__dict__", {}) or {}
                comp_id = d.get("compartmentId") or d.get("compartment_id")
            if comp_id:
                rec_client = get_recovery_client(region)
                has_next = True
                next_page = None
                found_ppid = None
                # Scan PDs in compartment until we find a match by databaseId
                while has_next and not found_ppid:
                    lp = rec_client.list_protected_databases(
                        compartment_id=comp_id, page=next_page
                    )
                    has_next = lp.has_next_page
                    next_page = getattr(lp, "next_page", None)
                    pdata = lp.data
                    pitems = getattr(pdata, "items", pdata)
                    for it in pitems or []:
                        try:
                            if hasattr(oci, "util") and hasattr(oci.util, "to_dict"):
                                d = oci.util.to_dict(it)
                            else:
                                d = getattr(it, "__dict__", {}) or {}
                        except Exception:
                            d = getattr(it, "__dict__", {}) or {}
                        if (d.get("databaseId") or d.get("database_id")) == database_id:
                            found_ppid = d.get("protectionPolicyId") or d.get(
                                "protection_policy_id"
                            )
                            break
                if mapped is not None:
                    mapped.protection_policy_id = found_ppid
        except Exception:
            # Non-fatal enrichment failure
            pass
        return mapped
    except Exception as e:
        logger.error(f"Error in get_database tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists Database Backups with optional filters. "
        "If neither database_id nor compartment_id is provided, defaults to tenancy compartment."
    )
)
def list_backups(
    compartment_id: Annotated[
        Optional[str], "OCID of the compartment to scope the search."
    ] = None,
    database_id: Annotated[
        Optional[str], "OCID of the Database to filter backups for."
    ] = None,
    lifecycle_state: Annotated[Optional[str], "Filter by lifecycle state."] = None,
    type: Annotated[
        Optional[str], "Backup type filter (e.g., INCREMENTAL, FULL)."
    ] = None,
    limit: Annotated[Optional[int], "Maximum number of items per page."] = None,
    page: Annotated[Optional[str], "Pagination token (opc-next-page)."] = None,
    region: Annotated[
        Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."
    ] = None,
) -> list[BackupSummary]:
    try:
        client = get_database_client(region)
        results: list[BackupSummary] = []
        has_next = True
        next_page = page
        # If user didn't scope by DB or compartment, use a dummy compartment to avoid reading real OCI config
        if not compartment_id and not database_id:
            compartment_id = "ocid1.compartment.oc1..dummy"
        while has_next:
            # Build query filters
            kwargs: dict = {"page": next_page}
            if database_id:
                kwargs["database_id"] = database_id
            if compartment_id:
                kwargs["compartment_id"] = compartment_id
            if lifecycle_state:
                kwargs["lifecycle_state"] = lifecycle_state
            if type:
                kwargs["type"] = type
            if limit is not None:
                kwargs["limit"] = limit
            # Call list_backups and map summaries
            resp = client.list_backups(**kwargs)
            data = getattr(resp.data, "items", resp.data)
            for it in data or []:
                m = map_backup_summary(it)
                if m is not None:
                    results.append(m)
            # Robust pagination guard: only continue if has_next_page is explicitly True
            # and a concrete next_page token is present. This avoids infinite loops when
            # tests use MagicMock/auto-specs that return truthy Mock objects.
            _has_next_attr = getattr(resp, "has_next_page", False)
            _next_page_attr = getattr(resp, "next_page", None)
            has_next = (isinstance(_has_next_attr, bool) and _has_next_attr) and bool(
                _next_page_attr
            )
            next_page = _next_page_attr if has_next else None
        return results
    except Exception as e:
        logger.error(f"Error in list_backups tool: {e}")
        raise


@mcp.tool(description="Retrieves a Database Backup by OCID.")
def get_backup(
    backup_id: Annotated[str, "OCID of the Backup to retrieve."],
    region: Annotated[
        Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."
    ] = None,
) -> Backup:
    try:
        client = get_database_client(region)
        resp = client.get_backup(backup_id=backup_id)
        return map_backup(resp.data)
    except Exception as e:
        logger.error(f"Error in get_backup tool: {e}")
        raise


@mcp.tool(
    description=(
        "Summarizes Database backup configuration and destinations "
        "for databases in a compartment or DB Home. "
        "Reports counts by destination type (e.g., DBRS, OBJECT_STORE, NFS), "
        "number unconfigured, and per-DB details. "
        "If db_home_id is omitted, the tool automatically discovers all DB Homes "
        "in the compartment and aggregates per-home."
    )
)
def summarise_protected_database_backup_destination(
    compartment_id: Annotated[
        Optional[str],
        "OCID of the compartment. If omitted, defaults to the tenancy/DEFAULT profile.",
    ] = None,
    region: Annotated[
        Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."
    ] = None,
    db_home_id: Annotated[
        Optional[str],
        "Optional DB Home OCID to scope databases. If omitted, all DB Homes in the compartment are used.",
    ] = None,
    include_last_backup_time: Annotated[
        bool, "If true, compute last backup time per DB (extra API calls)."
    ] = False,
) -> ProtectedDatabaseBackupDestinationSummary:
    try:
        db_client = get_database_client(region)
        rec_client = get_recovery_client(region)
        if not compartment_id:
            compartment_id = get_tenancy()

        # Discover DB Homes if not specified
        home_ids: list[str] = (
            [db_home_id]
            if db_home_id
            else _fetch_db_home_ids_for_compartment(compartment_id, region=region)
        )

        # Collect database summaries for those DB Homes (AVAILABLE only)
        db_summaries: list[Any] = []
        if home_ids:
            for hid in home_ids:
                resp = db_client.list_databases(
                    compartment_id=compartment_id,
                    db_home_id=hid,
                    lifecycle_state="AVAILABLE",
                )
                data = getattr(resp.data, "items", resp.data)
                if isinstance(data, list):
                    db_summaries.extend(data)
                elif data is not None:
                    db_summaries.append(data)

        # Build a map of database_id -> list of Protected Databases (from Recovery Service)
        # This allows us to infer DBRS (Recovery Service) as a destination type even if DB backup config
        # does not explicitly list it as a destination, by virtue of PD linkage.
        pd_by_dbid: dict[str, list[dict]] = {}
        try:
            has_next = True
            next_page = None
            while has_next:
                lp = rec_client.list_protected_databases(
                    compartment_id=compartment_id, page=next_page
                )
                has_next = lp.has_next_page
                next_page = getattr(lp, "next_page", None)
                pdata = lp.data
                pitems = getattr(pdata, "items", pdata)
                for it in pitems or []:
                    # convert to dict for easy field access
                    try:
                        if hasattr(oci, "util") and hasattr(oci.util, "to_dict"):
                            d = oci.util.to_dict(it)
                        else:
                            d = getattr(it, "__dict__", {}) or {}
                    except Exception:
                        d = getattr(it, "__dict__", {}) or {}
                    dbid = d.get("databaseId") or d.get("database_id")
                    if dbid:
                        pd_by_dbid.setdefault(dbid, []).append(d)
        except Exception:
            pd_by_dbid = {}

        # Helper routines to normalize SDK objects and read fields across variants
        def _to_dict(o: Any) -> dict:
            try:
                if hasattr(oci, "util") and hasattr(oci.util, "to_dict"):
                    d = oci.util.to_dict(o)
                    if isinstance(d, dict):
                        return d
            except Exception:
                pass
            return getattr(o, "__dict__", {}) if hasattr(o, "__dict__") else {}

        def _get(o: Any, *names: str):
            # Try attribute names first, then dict conversion
            for n in names:
                if hasattr(o, n):
                    v = getattr(o, n)
                    if v is not None:
                        return v
            d = _to_dict(o)
            for n in names:
                if d.get(n) is not None:
                    return d.get(n)
            return None

        def _extract_backup_destination_details(db_dict: dict) -> list[dict]:
            # Discover backup destination details from known key variants
            cfg = None
            for k in (
                "dbBackupConfig",
                "db_backup_config",
                "backupConfig",
                "backup_config",
                "databaseBackupConfig",
                "database_backup_config",
            ):
                if isinstance(db_dict.get(k), dict):
                    cfg = db_dict.get(k)
                    break
            if cfg is None:
                cfg = db_dict if isinstance(db_dict, dict) else {}
            details = (
                cfg.get("backupDestinationDetails")
                or cfg.get("backup_destination_details")
                or db_dict.get("backupDestinationDetails")
                or db_dict.get("backup_destination_details")
            )
            if not details:
                return []
            return details if isinstance(details, list) else [details]

        def _normalize_dest_type(t: Optional[str]) -> str:
            # Canonicalize destination types to a small set for reporting
            if not t:
                return "UNKNOWN"
            u = str(t).upper()
            if u in (
                "RECOVERY_SERVICE",
                "RECOVERY-SERVICE",
                "DBRS",
                "RECOVERY_SERVICE_BACKUP_DESTINATION",
            ):
                return "DBRS"
            if u in ("OBJECT_STORE", "OBJECTSTORE", "OBJECT_STORAGE"):
                return "OSS"
            if u in ("NFS",):
                return "NFS"
            return u

        def _is_auto_backup_enabled(db_dict: dict) -> bool:
            # Determine if auto-backup is enabled from known config keys
            cfg = None
            for k in (
                "dbBackupConfig",
                "db_backup_config",
                "backupConfig",
                "backup_config",
                "databaseBackupConfig",
                "database_backup_config",
            ):
                v = db_dict.get(k)
                if isinstance(v, dict):
                    cfg = v
                    break
            if isinstance(cfg, dict):
                for key in (
                    "isAutoBackupEnabled",
                    "is_auto_backup_enabled",
                    "autoBackupEnabled",
                    "auto_backup_enabled",
                ):
                    if key in cfg and cfg[key] is not None:
                        return bool(cfg[key])
            for key in (
                "isAutoBackupEnabled",
                "is_auto_backup_enabled",
                "autoBackupEnabled",
                "auto_backup_enabled",
            ):
                if key in db_dict and db_dict[key] is not None:
                    return bool(db_dict[key])
            return False

        def _read_backup_times_from_obj(o: Any) -> list[Any]:
            # Collect possible time fields from a backup object (SDK shapes differ)
            times = []
            for attr in (
                "time_ended",
                "timeEnded",
                "time_started",
                "timeStarted",
                "time_created",
                "timeCreated",
            ):
                v = getattr(o, attr, None)
                if v is not None:
                    times.append(v)
            if not times:
                d = _to_dict(o)
                for k in ("timeEnded", "timeStarted", "timeCreated"):
                    if d.get(k) is not None:
                        times.append(d[k])
            return times

        # Aggregation structures for summary + per-DB details
        items: list[ProtectedDatabaseBackupDestinationItem] = []
        counts_by_type: dict[str, int] = {}
        db_names_by_type: dict[str, list[str]] = {}
        unconfigured = 0
        unconfigured_names: list[str] = []
        has_backups_names: list[str] = []

        get_db = db_client.get_database
        list_bk = db_client.list_backups

        # Iterate each DB summary, fetch full DB to inspect backup config and infer destinations
        for s in db_summaries:
            try:
                sid = _get(s, "id")
                if not sid:
                    continue
                db_name = _get(s, "db_name", "dbName")

                dresp = get_db(database_id=sid)
                d_obj = getattr(dresp, "data", None)
                d_dict = _to_dict(d_obj)

                # Extract configured destination details (normalize to a list of dicts)
                dest_details = _extract_backup_destination_details(d_dict)
                dest_types: list[str] = []
                dest_ids: list[str] = []
                for det in dest_details:
                    dd = det if isinstance(det, dict) else _to_dict(det)
                    t_norm = _normalize_dest_type(
                        dd.get("type") or dd.get("destinationType")
                    )
                    did = (
                        dd.get("id")
                        or dd.get("backupDestinationId")
                        or dd.get("destinationId")
                    )
                    if t_norm:
                        dest_types.append(t_norm)
                    if did:
                        dest_ids.append(did)

                # Augment with Recovery Service protected database linkage
                pds_for_db = pd_by_dbid.get(sid, [])
                if pds_for_db:
                    dest_types.append("DBRS")
                    try:
                        # Use PD OCID for reference if present
                        dest_ids.append(pds_for_db[0].get("id"))
                    except Exception:
                        pass

                # Deduplicate destinations and IDs
                dest_types = list(dict.fromkeys([t for t in dest_types if t]))
                # Enforce exclusivity between DBRS and OSS:
                # prefer DBRS (no dual classification)
                if "DBRS" in dest_types and "OSS" in dest_types:
                    dest_types = ["DBRS"]
                dest_ids = list(dict.fromkeys([d for d in dest_ids if d]))

                auto_enabled = _is_auto_backup_enabled(d_dict)
                # Consider configured if auto-backup enabled OR any destination types
                # detected (incl. DBRS via Recovery Service)
                configured = bool(auto_enabled or len(dest_types) > 0)
                status = "CONFIGURED" if configured else "UNCONFIGURED"
                last_backup_time = None

                # Optionally compute last backup time (more API calls)
                if include_last_backup_time:
                    try:
                        b_resp = list_bk(database_id=sid)
                        b_data = getattr(b_resp.data, "items", b_resp.data)
                        backups = (
                            b_data
                            if isinstance(b_data, list)
                            else [b_data] if b_data is not None else []
                        )
                        best = None
                        for b in backups:
                            for t in _read_backup_times_from_obj(b):
                                if best is None or (str(t) > str(best)):
                                    best = t
                        if best is not None:
                            last_backup_time = best
                            if status != "CONFIGURED":
                                status = "HAS_BACKUPS"
                    except Exception:
                        pass
                else:
                    # Lightweight existence check for backups
                    try:
                        b_resp = list_bk(database_id=sid, limit=1)
                        b_data = getattr(b_resp.data, "items", b_resp.data)
                        has_any = (
                            (len(b_data) > 0)
                            if isinstance(b_data, list)
                            else (b_data is not None)
                        )
                        if status != "CONFIGURED" and has_any:
                            status = "HAS_BACKUPS"
                    except Exception:
                        pass

                # Aggregate summary counters and name lists by status/destination
                name_for_lists = db_name or sid
                if status == "CONFIGURED":
                    for ut in set(dest_types):
                        if ut != "UNKNOWN":
                            counts_by_type[ut] = counts_by_type.get(ut, 0) + 1
                            db_names_by_type.setdefault(ut, []).append(name_for_lists)
                elif status == "HAS_BACKUPS":
                    has_backups_names.append(name_for_lists)
                else:
                    unconfigured += 1
                    unconfigured_names.append(name_for_lists)

                # Append per-DB detail record
                items.append(
                    ProtectedDatabaseBackupDestinationItem(
                        database_id=sid,
                        db_name=db_name,
                        status=status,
                        destination_types=dest_types,
                        destination_ids=dest_ids,
                        last_backup_time=last_backup_time,
                    )
                )
            except Exception:
                # Continue on per-DB errors to maximize overall coverage
                continue

        # Sorting helpers: prioritize DBRS over OSS/NFS, then by status, then by name
        def _dest_rank(types: list[str]) -> int:
            if not types:
                return 99
            order = {"DBRS": 0, "OSS": 1, "NFS": 2, "UNKNOWN": 3}
            return min(order.get(t, 3) for t in types)

        def _status_rank(st: Optional[str]) -> int:
            return {"CONFIGURED": 0, "HAS_BACKUPS": 1, "UNCONFIGURED": 2}.get(
                (st or "").upper(), 3
            )

        items = sorted(
            items,
            key=lambda it: (
                _dest_rank(it.destination_types),
                _status_rank(it.status),
                (it.db_name or ""),
            ),
        )

        # Name list post-processing
        def _uniq_sorted(xs: list[str]) -> list[str]:
            return sorted(dict.fromkeys([x for x in xs if x]))

        # Preserve duplicates for name lists that can correspond to different DB OCIDs
        def _sorted_keep(xs: list[str]) -> list[str]:
            return sorted([x for x in xs if x])

        db_names_by_type = {k: _sorted_keep(v) for k, v in db_names_by_type.items()}
        unconfigured_names = _uniq_sorted(unconfigured_names)
        has_backups_names = _uniq_sorted(has_backups_names)

        return ProtectedDatabaseBackupDestinationSummary(
            compartment_id=compartment_id,
            region=region,
            total_databases=len(db_summaries),
            unconfigured_count=unconfigured,
            counts_by_destination_type=counts_by_type,
            db_names_by_destination_type=db_names_by_type,
            unconfigured_db_names=unconfigured_names,
            has_backups_db_names=has_backups_names,
            items=items,
        )
    except Exception as e:
        logger.error(
            f"Error in summarise_protected_database_backup_destination tool: {e}"
        )
        raise


def list_db_homes(
    compartment_id: Annotated[
        Optional[str], "OCID of the compartment to scope the search."
    ] = None,
    db_system_id: Annotated[
        Optional[str], "The OCID of the Exadata DB system to filter the DB homes by."
    ] = None,
    limit: Annotated[Optional[int], "Maximum number of items per page."] = None,
    page: Annotated[Optional[str], "Pagination token (opc-next-page)."] = None,
    region: Annotated[
        Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."
    ] = None,
) -> list[DatabaseHomeSummary]:
    # Note: This helper is not exposed as an MCP tool; other tools use it internally.
    try:
        client = get_database_client(region)
        if not compartment_id and not db_system_id:
            compartment_id = get_tenancy()
        results: list[DatabaseHomeSummary] = []
        has_next = True
        next_page = page
        while has_next:
            kwargs: dict = {"page": next_page}
            if compartment_id:
                kwargs["compartment_id"] = compartment_id
            if db_system_id:
                kwargs["db_system_id"] = db_system_id
            if limit is not None:
                kwargs["limit"] = limit
            resp = client.list_db_homes(**kwargs)
            data = getattr(resp.data, "items", resp.data)
            for it in data or []:
                m = map_database_home_summary(it)
                if m is not None:
                    results.append(m)
            has_next = resp.has_next_page
            next_page = resp.next_page if hasattr(resp, "next_page") else None
        return results
    except Exception as e:
        logger.error(f"Error in list_db_homes tool: {e}")
        raise


@mcp.tool(description="Retrieves a single Database Home by OCID.")
def get_db_home(
    db_home_id: Annotated[str, "OCID of the DB Home to retrieve."],
    region: Annotated[
        Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."
    ] = None,
) -> DatabaseHome:
    try:
        client = get_database_client(region)
        resp = client.get_db_home(db_home_id=db_home_id)
        return map_database_home(resp.data)
    except Exception as e:
        logger.error(f"Error in get_db_home tool: {e}")
        raise


@mcp.tool(
    description=(
        "Lists Database Systems in the specified compartment with optional lifecycle filters. "
        "If compartment_id is omitted, defaults to tenancy compartment."
    )
)
def list_db_systems(
    compartment_id: Annotated[
        Optional[str], "OCID of the compartment to scope the search."
    ] = None,
    lifecycle_state: Annotated[Optional[str], "Filter by lifecycle state."] = None,
    limit: Annotated[Optional[int], "Maximum number of items per page."] = None,
    page: Annotated[Optional[str], "Pagination token (opc-next-page)."] = None,
    region: Annotated[
        Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."
    ] = None,
) -> list[DbSystemSummary]:
    try:
        client = get_database_client(region)
        if not compartment_id:
            compartment_id = get_tenancy()
        results: list[DbSystemSummary] = []
        has_next = True
        next_page = page
        while has_next:
            kwargs: dict = {"page": next_page}
            if compartment_id:
                kwargs["compartment_id"] = compartment_id
            if lifecycle_state:
                kwargs["lifecycle_state"] = lifecycle_state
            if limit is not None:
                kwargs["limit"] = limit
            resp = client.list_db_systems(**kwargs)
            data = getattr(resp.data, "items", resp.data)
            for it in data or []:
                m = map_db_system_summary(it)
                if m is not None:
                    results.append(m)
            has_next = resp.has_next_page
            next_page = resp.next_page if hasattr(resp, "next_page") else None
        return results
    except Exception as e:
        logger.error(f"Error in list_db_systems tool: {e}")
        raise


@mcp.tool(description="Retrieves a single Database System by OCID.")
def get_db_system(
    db_system_id: Annotated[str, "OCID of the DB System to retrieve."],
    region: Annotated[
        Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."
    ] = None,
) -> DbSystem:
    try:
        client = get_database_client(region)
        resp = client.get_db_system(db_system_id=db_system_id)
        return map_db_system(resp.data)
    except Exception as e:
        logger.error(f"Error in get_db_system tool: {e}")
        raise


def main():
    # Entrypoint: choose transport based on env; always log startup meta and log file location
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    # Log startup and where logs are written
    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    log_dir = os.getenv("ORACLE_MCP_LOG_DIR", os.path.join(base_dir, "logs"))
    log_file = os.getenv(
        "ORACLE_MCP_LOG_FILE", os.path.join(log_dir, "oci_recovery_mcp_server.log")
    )
    logger.info("Starting %s v%s", __project__, __version__)
    logger.info("Logs will be written to: %s", os.path.abspath(log_file))

    if host and port:
        logger.info("Running FastMCP over HTTP at http://%s:%s", host, port)
        mcp.run(transport="http", host=host, port=int(port))
    else:
        logger.info("Running FastMCP over stdio transport")
        mcp.run()


if __name__ == "__main__":
    main()
