"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
import json
from logging import Logger
from typing import Annotated, Optional

import oci
from fastmcp import FastMCP
from oci.monitoring.models import SummarizeMetricsDataDetails

from oracle.oci_recovery_mcp_server.models import (
    ProtectedDatabaseSummary,
    map_protected_database_summary,
    ProtectedDatabase,
    map_protected_database,
    ProtectionPolicySummary,
    map_protection_policy_summary,
    ProtectionPolicy,
    map_protection_policy,
    RecoveryServiceSubnetSummary,
    map_recovery_service_subnet_summary,
    RecoveryServiceSubnet,
    map_recovery_service_subnet,
    ProtectedDatabaseHealthCounts,
    ProtectedDatabaseRedoCounts,
    ProtectedDatabaseBackupSpaceSum,
)
from . import __project__, __version__

logger = Logger(__name__, level="INFO")
mcp = FastMCP(name=__project__)


def get_recovery_client(region: str | None = None) -> oci.recovery.DatabaseRecoveryClient:
    """
    Initialize DatabaseRecoveryClient using the OCI config and a SecurityTokenSigner.
    Adds a custom user agent derived from the package name and version.
    Optionally overrides the region.
    """
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
        return oci.recovery.DatabaseRecoveryClient(config, signer=signer)

    regional_config = config.copy()
    regional_config["region"] = region
    return oci.recovery.DatabaseRecoveryClient(regional_config, signer=signer)

def get_identity_client():
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

def get_monitoring_client():
    logger.info("entering get_monitoring_client")
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    token = None
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.monitoring.MonitoringClient(config, signer=signer)

def get_tenancy():
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    return os.getenv("TENANCY_ID_OVERRIDE", config["tenancy"])


def list_all_compartments_internal(only_one_page: bool, limit=100):
    """Internal function to get List all compartments in a tenancy"""
    identity_client = get_identity_client()
    response = identity_client.list_compartments(
        compartment_id=get_tenancy(),
        compartment_id_in_subtree=True,
        access_level="ACCESSIBLE",
        lifecycle_state="ACTIVE",
        limit=limit,
    )
    compartments = response.data
    compartments.append(
        identity_client.get_compartment(compartment_id=get_tenancy()).data
    )
    if only_one_page:  # limiting the number of items returned
        return compartments
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
)
def list_protected_databases(
    compartment_id: Annotated[str, "The OCID of the compartment"],
    lifecycle_state: Annotated[
        Optional[str],
        'Filter by lifecycle state (e.g., "CREATING", "UPDATING", "ACTIVE", "DELETE_SCHEDULED", "DELETING", "DELETED", "FAILED")',
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
    sort_order: Annotated[
        Optional[str], 'Sort order: "ASC" or "DESC"'
    ] = None,
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

            response: oci.response.Response = client.list_protected_databases(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

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
    opc_request_id: Annotated[Optional[str], "Unique identifier for the request"] = None,
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


@mcp.tool(description="Summarizes Protected Database health status counts (PROTECTED, WARNING, ALERT) in a compartment. Lists protected databases then fetches each to read its health field; returns counts.")
def summarize_protected_database_health(
    compartment_id: Annotated[
        Optional[str],
        "OCID of the compartment. If omitted, defaults to the tenancy OCID from your OCI profile.",
    ] = None,
    region: Annotated[
        Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"
    ] = None,
) -> ProtectedDatabaseHealthCounts:
    """
    Summarizes Protected Database health status counts (PROTECTED, WARNING, ALERT) in a compartment.
    The tool lists protected databases then fetches each to read its health field; returns counts.
    """
    try:
        client = get_recovery_client(region)
        comp_id = compartment_id or get_tenancy()

        protected = 0
        warning = 0
        alert = 0

        has_next_page = True
        next_page: Optional[str] = None

        while has_next_page:
            list_kwargs = {
                "compartment_id": comp_id,
                "page": next_page,
            }
            response: oci.response.Response = client.list_protected_databases(**list_kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data = response.data
            items = getattr(data, "items", data)
            for item in items or []:
                pd_id = getattr(item, "id", None) or (getattr(item, "data", None) and getattr(item.data, "id", None))
                if pd_id is None:
                    try:
                        item_dict = getattr(item, "__dict__", None) or {}
                        pd_id = item_dict.get("id")
                    except Exception:
                        pd_id = None
                if not pd_id:
                    continue

                pd_resp: oci.response.Response = client.get_protected_database(protected_database_id=pd_id)
                pd = pd_resp.data
                health = getattr(pd, "health", None)
                if not health and hasattr(pd, "__dict__"):
                    health = pd.__dict__.get("health")

                if health == "PROTECTED":
                    protected += 1
                elif health == "WARNING":
                    warning += 1
                elif health == "ALERT":
                    alert += 1
                else:
                    # unknown/None health -> not counted in the three buckets
                    pass

        total = protected + warning + alert
        logger.info(
            f"Health summary for compartment {comp_id} (region={region}): "
            f"PROTECTED={protected}, WARNING={warning}, ALERT={alert}, TOTAL={total}"
        )
        return ProtectedDatabaseHealthCounts(
            compartment_id=comp_id,
            region=region,
            protected=protected,
            warning=warning,
            alert=alert,
            total=total,
        )
    except Exception as e:
        logger.error(f"Error in summarize_protected_database_health tool: {str(e)}")
        raise


@mcp.tool(description="Summarizes redo transport enablement for Protected Databases in a compartment. Lists protected databases then fetches each to inspect is_redo_logs_enabled (true=enabled, false=disabled).")
def summarize_protected_database_redo_status(
    compartment_id: Annotated[
        Optional[str],
        "OCID of the compartment. If omitted, defaults to the tenancy OCID from your OCI profile.",
    ] = None,
    region: Annotated[
        Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"
    ] = None,
) -> ProtectedDatabaseRedoCounts:
    """
    Summarizes redo transport enablement for Protected Databases in a compartment.
    Lists protected databases then fetches each to inspect is_redo_logs_enabled (true=enabled, false=disabled).
    """
    try:
        client = get_recovery_client(region)
        comp_id = compartment_id or get_tenancy()

        enabled = 0
        disabled = 0

        has_next_page = True
        next_page: Optional[str] = None

        while has_next_page:
            list_kwargs = {
                "compartment_id": comp_id,
                "page": next_page,
            }
            response: oci.response.Response = client.list_protected_databases(**list_kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data = response.data
            items = getattr(data, "items", data)
            for item in items or []:
                # Robustly get the PD OCID from summary item
                pd_id = getattr(item, "id", None) or (getattr(item, "data", None) and getattr(item.data, "id", None))
                if pd_id is None:
                    try:
                        item_dict = getattr(item, "__dict__", None) or {}
                        pd_id = item_dict.get("id")
                    except Exception:
                        pd_id = None
                if not pd_id:
                    continue

                # Fetch full Protected Database to read is_redo_logs_enabled
                pd_resp: oci.response.Response = client.get_protected_database(protected_database_id=pd_id)
                pd = pd_resp.data
                redo_enabled = getattr(pd, "is_redo_logs_enabled", None)
                if redo_enabled is None and hasattr(pd, "__dict__"):
                    redo_enabled = pd.__dict__.get("is_redo_logs_enabled") or pd.__dict__.get("isRedoLogsEnabled")

                if redo_enabled is True:
                    enabled += 1
                elif redo_enabled is False:
                    disabled += 1
                else:
                    # None/unknown -> do not count
                    pass

        total = enabled + disabled
        logger.info(
            f"Redo transport summary for compartment {comp_id} (region={region}): "
            f"ENABLED={enabled}, DISABLED={disabled}, TOTAL={total}"
        )
        return ProtectedDatabaseRedoCounts(
            compartment_id=comp_id,
            region=region,
            enabled=enabled,
            disabled=disabled,
            total=total,
        )
    except Exception as e:
        logger.error(f"Error in summarize_protected_database_redo_status tool: {str(e)}")
        raise


@mcp.tool(description="Sums backup space used (GB) by Protected Databases in a compartment. Lists protected databases in the compartment, fetches each, reads metrics.backup_space_used_in_gbs (or variants), and returns the total.")
def summarize_backup_space_used(
    compartment_id: Annotated[
        Optional[str],
        "OCID of the compartment. If omitted, defaults to the tenancy OCID from your OCI profile.",
    ] = None,
    region: Annotated[
        Optional[str],
        "Canonical OCI region (e.g., us-ashburn-1) to execute the request in.",
    ] = None,
) -> ProtectedDatabaseBackupSpaceSum:
    """
    Sums backup space used (GB) by Protected Databases in a compartment.
    Lists protected databases in the compartment, fetches each, reads metrics.backup_space_used_in_gbs
    (or variants), and returns the total as a ProtectedDatabaseBackupSpaceSum model.
    """
    try:
        client = get_recovery_client(region)
        comp_id = compartment_id or get_tenancy()

        total_scanned: int = 0
        sum_gb: float = 0.0

        has_next_page = True
        next_page: Optional[str] = None

        while has_next_page:
            list_kwargs = {
                "compartment_id": comp_id,
                "page": next_page,
            }
            response: oci.response.Response = client.list_protected_databases(**list_kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data = response.data
            items = getattr(data, "items", data)

            for item in items or []:
                # Extract PD OCID from the summary item robustly
                pd_id = getattr(item, "id", None) or (getattr(item, "data", None) and getattr(item.data, "id", None))
                if pd_id is None:
                    try:
                        item_dict = getattr(item, "__dict__", None) or {}
                        pd_id = item_dict.get("id")
                    except Exception:
                        pd_id = None
                if not pd_id:
                    continue

                total_scanned += 1

                # Fetch full PD to read metrics
                pd_resp: oci.response.Response = client.get_protected_database(protected_database_id=pd_id)
                pd = pd_resp.data

                # Try PD.metrics.backup_space_used_in_gbs (and variants)
                metrics = getattr(pd, "metrics", None)
                val = None
                if metrics is not None:
                    val = getattr(metrics, "backup_space_used_in_gbs", None)
                    if val is None and hasattr(metrics, "__dict__"):
                        val = metrics.__dict__.get("backup_space_used_in_gbs") or metrics.__dict__.get("backupSpaceUsedInGbs")

                # Fallback to summary metrics on list item if full PD had none
                if val is None:
                    try:
                        item_metrics = getattr(item, "metrics", None)
                        if item_metrics is not None:
                            val = getattr(item_metrics, "backup_space_used_in_gbs", None)
                            if val is None and hasattr(item_metrics, "__dict__"):
                                val = item_metrics.__dict__.get("backup_space_used_in_gbs") or item_metrics.__dict__.get("backupSpaceUsedInGbs")
                    except Exception:
                        pass

                # Accumulate if numeric
                try:
                    if val is not None:
                        sum_gb += float(val)
                except Exception:
                    # Ignore non-numeric values gracefully
                    pass

        logger.info(
            f"Backup space used summary for compartment {comp_id} (region={region}): "
            f"scanned={total_scanned}, sum_gb={sum_gb}"
        )
        return ProtectedDatabaseBackupSpaceSum(
            compartment_id=comp_id,
            region=region,
            total_databases_scanned=total_scanned,
            sum_backup_space_used_in_gbs=sum_gb,
        )
    except Exception as e:
        logger.error(f"Error in summarize_backup_space_used tool: {str(e)}")
        raise


@mcp.tool(description="List Protection Policies in a given compartment with optional filters.")
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
    sort_order: Annotated[
        Optional[str], 'Sort order: "ASC" or "DESC"'
    ] = None,
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
    opc_request_id: Annotated[Optional[str], "Unique identifier for the request"] = None,
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


@mcp.tool(description="List Recovery Service Subnets in a given compartment with optional filters.")
def list_recovery_service_subnets(
    compartment_id: Annotated[str, "The OCID of the compartment"],
    lifecycle_state: Annotated[
        Optional[str],
        'Filter by lifecycle state (e.g., "CREATING", "ACTIVE", "UPDATING", "DELETING", "DELETED", "FAILED")',
    ] = None,
    display_name: Annotated[Optional[str], "Exact match on display name"] = None,
    id: Annotated[Optional[str], "Recovery Service Subnet OCID"] = None,
    vcn_id: Annotated[Optional[str], "Filter by VCN OCID"] = None,
    limit: Annotated[Optional[int], "Maximum number of items per page"] = None,
    page: Annotated[
        Optional[str],
        "Pagination token (opc-next-page) to continue listing from",
    ] = None,
    sort_order: Annotated[
        Optional[str], 'Sort order: "ASC" or "DESC"'
    ] = None,
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

            response: oci.response.Response = client.list_recovery_service_subnets(**kwargs)
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
    opc_request_id: Annotated[Optional[str], "Unique identifier for the request"] = None,
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
        "The granularity of the metric. Currently we only support: 1m, 5m, 1h, 1d. Default: 1m.",
    ] = "1m",
    aggregation: Annotated[
        str,
        "The aggregation for the metric. Currently we only support: "
        "mean, sum, max, min, count. Default: mean",
    ] = "mean",
    protected_database_id: Annotated[
        str,
        "Optional protected database OCID to filter by " "(maps to resourceId dimension)",
    ] = None,
) -> list[dict]:
    monitoring_client = get_monitoring_client()
    namespace = "oci_recovery_service"
    filter_clause = f'{{resourceId="{protected_database_id}"}}' if protected_database_id else ""
    query = f"{metricName}[{resolution}]{filter_clause}.{aggregation}()"

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


def main():
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
