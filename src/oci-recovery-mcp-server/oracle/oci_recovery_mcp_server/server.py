"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# Module overview:
# This file defines the FastMCP app and the MCP tools it exposes. Everything a tool
# needs in order to reach OCI lives in a sibling module, so this file stays about
# the tools themselves:
#
# - logging_setup: root logging configuration and the structured event log
#                  (redaction, payload summarisation, _log_event).
# - telemetry:     request/actor/installation ids, the opc-request-id stamped on
#                  outbound SDK calls, and the @_tool_logger decorator.
# - auth:          credential resolution for both transports (local OCI profile
#                  over stdio, OCI IAM/IDCS per caller over HTTP) and the tenancy.
# - clients:       OCI SDK client factories built on top of auth + telemetry.
# - cache:         the bounded, thread-safe TTL cache and its tenant/caller
#                  partition keys.
# - regions:       the tenancy's subscribed regions, cached per tenant.
# - compartments:  compartment discovery, subtree expansion and name/OCID
#                  resolution.
# - models:        the server's typed results and the map_* SDK adapters.
#
# The general flow for most tools:
# 1) Resolve region/config/signer and create an OCI client (clients.get_*_client).
# 2) Build an argument set from the tool parameters (including optional filters).
# 3) Call the appropriate OCI API, handling pagination where required.
# 4) Map SDK responses to the server's typed models (map_* functions).
# 5) Return typed results (summaries/objects) or computed aggregations.
#
# Main() chooses the transport:
# - If ORACLE_MCP_HOST and ORACLE_MCP_PORT are set: Streamable HTTP, with OCI IAM
#   (IDCS) sign-in per caller.
# - Otherwise stdio (default for MCP), on the operator's own OCI profile credentials.
#
# Important robustness choices:
# - We add an "additional_user_agent" string to all OCI client configs for traceability.
# - All credential resolution is delegated to the shared oracle-mcp-common library:
#   build_auth_context() for profile-backed session/apikey credentials, and
#   build_idcs_http_auth()/IDCSHttpAuth.context_for() for HTTP.
# - We try to be resilient to SDK shape differences by using getattr/__dict__/to_dict
#   wherever possible, especially for pagination and nested model fields.
# - We log key milestones and counts for better operability and diagnostics.

import logging
import os
import re
import time
import uuid
from pathlib import Path
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
    ProtectedDatabaseHealthSummary,
    ProtectedDatabaseRedoCounts,
    ProtectedDatabaseRedoSummary,
    ProtectedDatabaseSummary,
    ProtectionPolicy,
    RecoveryServiceSubnet,
    WorkRequest,
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
    map_recovery_service_subnet,
    map_recovery_service_subnet_details,
    map_work_request,
)

from . import (
    __project__,
    __version__,
    auth,
    cache,
    clients,
    compartments,
    logging_setup,
    regions,
    telemetry,
)
from .logging_setup import logger

"""MCP tools available in this server:
- fetch_regions_subscribed
- list_protected_databases
- get_protected_database
- summarize_protected_database_health
- summarize_protected_database_redo_status
- summarize_backup_space_used
- check_recovery_service_limits
- list_protection_policies
- get_protection_policy
- list_recovery_service_subnets
- get_recovery_service_subnet
- get_recovery_service_metrics
- list_databases
- get_database
- list_backups
- get_backup
- list_restore
- summarize_protected_database_backup_destination
- list_db_homes
- get_db_home
- list_db_systems
- get_db_system
- oci_recovery_service_dashboard_prompt
- onboard_database_to_recovery_service
- diagnose_recovery_service_issue
"""

_PROMPTS_DIR = Path(__file__).parent / "data" / "prompts"

OCI_RECOVERY_SERVICE_DASHBOARD_PROMPT = (
    _PROMPTS_DIR / "oci_recovery_service_dashboard.txt"
).read_text(encoding="utf-8")
ONBOARD_DATABASE_TO_RECOVERY_SERVICE_PROMPT = (
    _PROMPTS_DIR / "onboard_database_to_recovery_service.txt"
).read_text(encoding="utf-8")
DIAGNOSE_RECOVERY_SERVICE_ISSUE_PROMPT = (
    _PROMPTS_DIR / "diagnose_recovery_service_issue.txt"
).read_text(encoding="utf-8")


# Every tool here reads; none creates, updates or deletes an OCI resource. These
# hints tell an MCP host that much without a human reading the README, so a host
# can skip a confirmation prompt it would otherwise raise on an unknown tool.
_READ_ONLY_TOOL = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    # Results come from OCI, not from a closed set the server owns.
    "openWorldHint": True,
}

# The guidance tools return static text and never reach the network.
_LOCAL_GUIDANCE_TOOL = {**_READ_ONLY_TOOL, "openWorldHint": False}

# Create the FastMCP app that exposes the functions decorated with @mcp.tool.
# main() attaches the OCI IAM OAuth provider when it selects the HTTP transport.
mcp = FastMCP(name=__project__)


_TOOL_DEADLINE_SECONDS = float(os.getenv("ORACLE_MCP_TOOL_DEADLINE_SECONDS", "120"))


class _Deadline:
    """A cooperative monotonic-time budget for a fan-out the caller cannot see.

    The summary tools issue one request per protected database across every
    compartment in scope, so a large tenancy turns a single tool call into
    hundreds of sequential round trips -- long past the point where an MCP client
    has given up waiting. Stopping at a deadline and saying so is more useful
    than a request that never returns. Set ORACLE_MCP_TOOL_DEADLINE_SECONDS to 0
    to scan without a limit. An OCI request already in flight is allowed to
    finish; callers check the budget between requests.
    """

    def __init__(self, seconds: Optional[float] = None):
        """
        Start the budget, defaulting to ORACLE_MCP_TOOL_DEADLINE_SECONDS.

        A budget of 0 (or None resolving to 0) means no deadline at all.
        """
        budget = _TOOL_DEADLINE_SECONDS if seconds is None else seconds
        self._expires_at = (time.monotonic() + budget) if budget and budget > 0 else None
        self.expired = False

    def reached(self) -> bool:
        """Report whether the budget is spent, latching ``expired`` once it is."""
        if self._expires_at is not None and time.monotonic() >= self._expires_at:
            self.expired = True
        return self.expired


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Lists protected databases in a compartment with optional filters. For each "
        "database it also includes Recovery Service Subnet details, removes noisy "
        "fields, and adds basic per‑database metrics. It also includes "
        "policyLockedDateTime so retention-lock status is clear (null means lock "
        "is disabled for the attached protection policy; a timestamp means lock "
        "is configured/effective). The result is a list of simple dictionaries, "
        "each with cleaned subnet information and a small metrics map."
    )
)
@telemetry._tool_logger("list_protected_databases")
def list_protected_databases(
    compartment_id: Annotated[str, "The compartment OCID or compartment display name"],
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns the combined results.",
    ] = False,
    lifecycle_state: Annotated[
        Optional[str],
        (
            'Filter by lifecycle state (e.g., "CREATING", "UPDATING", '
            '"ACTIVE", "DELETE_SCHEDULED", "DELETING", "DELETED", "FAILED")'
        ),
    ] = None,
    display_name: Annotated[Optional[str], "Exact match on display name"] = None,
    id: Annotated[Optional[str], "Protected Database OCID"] = None,
    protection_policy_id: Annotated[Optional[str], "Filter results to this Protection Policy OCID"] = None,
    recovery_service_subnet_id: Annotated[Optional[str], "Filter by Recovery Service Subnet OCID"] = None,
    limit: Annotated[Optional[int], "Maximum number of items per page"] = None,
    page: Annotated[
        Optional[str],
        "Pagination token (opc-next-page) to continue listing from",
    ] = None,
    sort_order: Annotated[Optional[str], 'Sort order: "ASC" or "DESC"'] = None,
    sort_by: Annotated[Optional[str], 'Sort by field: "timeCreated" or "displayName"'] = None,
    opc_request_id: Annotated[Optional[str], "Unique identifier for the request"] = None,
    region: Annotated[Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"] = None,
) -> list[ProtectedDatabaseSummary]:
    """
    Paginates through Recovery Service to list Protected Databases and returns
    a list of ProtectedDatabaseSummary models mapped from the OCI SDK response.
    """
    try:
        # Keep tool behavior intact; only add correlation-id based logging via wrapped client
        request_id = uuid.uuid4().hex
        client = clients.get_recovery_client(region, request_id=request_id)

        results: list[ProtectedDatabaseSummary] = []

        comp_ids = compartments._compartment_ids_for_tool(
            compartment_id,
            fetch_for_child_compartment=fetch_for_child_compartment,
            request_id=request_id,
        )

        for comp_id in comp_ids:
            has_next_page = True
            next_page: Optional[str] = page

            while has_next_page:
                # Build request kwargs from provided filters
                kwargs = {
                    "compartment_id": comp_id,
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
                    logger.debug(f"Item structure: {d}")
                    pd_summary = map_protected_database_summary(d)
                    if pd_summary is None:
                        continue

                    # Start with a dict view of the Pydantic summary (exclude Nones)
                    try:
                        pd_dict = pd_summary.model_dump(exclude_none=True)
                    except Exception:
                        try:
                            pd_dict = pd_summary.dict(exclude_none=True)
                        except Exception:
                            pd_dict = dict(getattr(pd_summary, "__dict__", {}))

                    # Keep retention-lock visibility explicit for clients:
                    # include camelCase key even when value is None.
                    pd_dict["policyLockedDateTime"] = getattr(pd_summary, "policy_locked_date_time", None)

                    # Enrich/clean Recovery Service Subnet details similarly to get_protected_database
                    try:
                        rss_list = getattr(pd_summary, "recovery_service_subnets", None)
                        if rss_list:
                            enriched = []
                            for det in rss_list:
                                if det is None:
                                    continue
                                rss_id = getattr(det, "id", None)
                                needs_enrich = bool(
                                    rss_id
                                    and (
                                        getattr(det, "vcn_id", None) is None
                                        or getattr(det, "subnet_id", None) is None
                                        or getattr(det, "display_name", None) is None
                                        or getattr(det, "compartment_id", None) is None
                                    )
                                )
                                if needs_enrich:
                                    try:
                                        rss_resp: oci.response.Response = client.get_recovery_service_subnet(
                                            recovery_service_subnet_id=rss_id
                                        )
                                        full_rss = rss_resp.data
                                        mapped_det = map_recovery_service_subnet_details(full_rss)
                                        enriched.append(mapped_det or det)
                                    except Exception:
                                        enriched.append(det)
                                else:
                                    enriched.append(det)
                            # Clean and serialize RSS list, dropping noisy fields to match get_protected_database
                            cleaned_rss = []
                            for ed in enriched:
                                if isinstance(ed, dict):
                                    rd = dict(ed)
                                else:
                                    try:
                                        rd = ed.model_dump(exclude_none=True)
                                    except Exception:
                                        try:
                                            rd = ed.dict(exclude_none=True)
                                        except Exception:
                                            rd = dict(getattr(ed, "__dict__", {}))
                                for _rm in (
                                    "lifecycle_details",
                                    "time_created",
                                    "time_updated",
                                    "freeform_tags",
                                    "defined_tags",
                                    "system_tags",
                                ):
                                    rd.pop(_rm, None)
                                cleaned_rss.append(rd)
                            pd_dict["recovery_service_subnets"] = cleaned_rss
                    except Exception:
                        # best-effort enrichment
                        pass

                    # Populate metrics from full GET to align with CLI list output (no derivations/fallbacks)
                    try:
                        pdid = pd_dict.get("id") or getattr(pd_summary, "id", None)
                        if pdid:
                            try:
                                g = client.get_protected_database(protected_database_id=pdid)
                                full_pd = map_protected_database(getattr(g, "data", None))
                                mobj = getattr(full_pd, "metrics", None)
                                md = None
                                if mobj is not None:
                                    try:
                                        md = mobj.model_dump(exclude_none=False)
                                    except Exception:
                                        try:
                                            md = mobj.dict(exclude_none=False)
                                        except Exception:
                                            md = None

                                def _pick(d: dict | None, key: str):
                                    """Read one key from a metrics dict that may be missing entirely."""
                                    if not isinstance(d, dict):
                                        return None
                                    return d.get(key)

                                metrics_out = {
                                    "backup-space-estimate-in-gbs": _pick(md, "backup_space_estimate_in_gbs"),
                                    "backup-space-used-in-gbs": _pick(md, "backup_space_used_in_gbs"),
                                    "current-retention-period-in-seconds": _pick(
                                        md, "current_retention_period_in_seconds"
                                    ),
                                    "db-size-in-gbs": _pick(md, "database_size_in_gbs"),
                                    "is-redo-logs-enabled": _pick(md, "is_redo_logs_enabled"),
                                    "minimum-recovery-needed-in-days": _pick(
                                        md, "minimum_recovery_needed_in_days"
                                    ),
                                    "retention-period-in-days": _pick(md, "retention_period_in_days"),
                                    "unprotected-window-in-seconds": _pick(
                                        md, "unprotected_window_in_seconds"
                                    ),
                                }

                                # Keep real-time protection status explicit in list output.
                                # Prefer top-level PD flag; fallback to metrics flag.
                                redo_shipped = getattr(full_pd, "is_redo_logs_shipped", None)
                                if redo_shipped is None:
                                    redo_shipped = _pick(md, "is_redo_logs_enabled")

                                # Emit both key variants for client compatibility.
                                pd_dict["is_redo_logs_shipped"] = redo_shipped
                                pd_dict["isRedoLogsShipped"] = redo_shipped

                                pd_dict["metrics"] = metrics_out
                            except Exception:
                                # If GET fails, do not set metrics (avoid misleading partials)
                                pass
                    except Exception:
                        pass

                    results.append(pd_dict)

        # De-dupe by OCID when scanning multiple compartments
        if fetch_for_child_compartment:
            uniq: dict[str, Any] = {}
            for r in results:
                try:
                    rid = r.get("id") if isinstance(r, dict) else getattr(r, "id", None)
                except Exception:
                    rid = None
                if rid and rid not in uniq:
                    uniq[rid] = r
            results = list(uniq.values())

        logger.info(f"Found {len(results)} Protected Databases")
        return results

    except Exception as e:
        logger.error(f"Error in list_protected_databases tool: {str(e)}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Gets a protected database by OCID and presents a clean, easy‑to‑read view. "
        "It includes Recovery Service Subnet details, hides noisy fields, and adds "
        "core metrics. It also includes policyLockedDateTime so retention-lock "
        "status is explicit (null means lock is disabled for the attached "
        "protection policy; a timestamp means lock is configured/effective). "
        "The result is one protected database as a plain dictionary with subnet "
        "info and a simple metrics section."
    )
)
@telemetry._tool_logger("get_protected_database")
def get_protected_database(
    protected_database_id: Annotated[str, "Protected Database OCID"],
    opc_request_id: Annotated[Optional[str], "Unique identifier for the request"] = None,
    region: Annotated[Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"] = None,
) -> ProtectedDatabase:
    """
    Retrieves a single Protected Database resource from Recovery Service and returns
    a ProtectedDatabase model mapped from the OCI SDK response.
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_recovery_client(region, request_id=request_id)

        # Optional request ID passthrough
        kwargs = {}
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        response: oci.response.Response = client.get_protected_database(
            protected_database_id=protected_database_id, **kwargs
        )

        data = response.data
        pd = map_protected_database(data)

        # Enrich Recovery Service Subnet details if only IDs are present in PD payload
        try:
            rss_list = getattr(pd, "recovery_service_subnets", None)
            if rss_list:
                enriched: list = []
                for det in rss_list:
                    # det is a RecoveryServiceSubnetDetails model
                    if det is None:
                        continue
                    rss_id = getattr(det, "id", None)
                    # If we have an id but missing core fields, fetch full RSS object
                    needs_enrich = bool(
                        rss_id
                        and (
                            getattr(det, "vcn_id", None) is None
                            or getattr(det, "subnet_id", None) is None
                            or getattr(det, "display_name", None) is None
                            or getattr(det, "compartment_id", None) is None
                        )
                    )
                    if needs_enrich:
                        try:
                            rss_resp: oci.response.Response = client.get_recovery_service_subnet(
                                recovery_service_subnet_id=rss_id
                            )
                            full_rss = rss_resp.data
                            mapped_det = map_recovery_service_subnet_details(full_rss)
                            enriched.append(mapped_det or det)
                        except Exception:
                            # On failure, preserve original partial details
                            enriched.append(det)
                    else:
                        enriched.append(det)
                if enriched:
                    pd.recovery_service_subnets = enriched
        except Exception:
            # Best-effort enrichment; ignore errors and return mapped PD
            pass

        logger.info(f"Fetched Protected Database {protected_database_id}")

        # Build sanitized response dict (exclude None to avoid noisy nulls)
        try:
            pd_dict = pd.model_dump(exclude_none=True)
        except Exception:
            try:
                pd_dict = pd.dict(exclude_none=True)  # pydantic v1 fallback
            except Exception:
                pd_dict = dict(getattr(pd, "__dict__", {}))

        # Keep retention-lock visibility explicit for clients:
        # include camelCase key even when value is None.
        pd_dict["policyLockedDateTime"] = getattr(pd, "policy_locked_date_time", None)

        # Remove top-level fields not desired in response
        for _k in ("change_rate", "compression_ratio"):
            pd_dict.pop(_k, None)

        # Clean nested Recovery Service Subnet details
        _rss = pd_dict.get("recovery_service_subnets")
        if isinstance(_rss, list):
            cleaned_rss = []
            for _det in _rss:
                if isinstance(_det, dict):
                    d = dict(_det)
                else:
                    try:
                        d = _det.model_dump(exclude_none=True)
                    except Exception:
                        try:
                            d = _det.dict(exclude_none=True)
                        except Exception:
                            d = dict(getattr(_det, "__dict__", {}))
                for _rm in (
                    "lifecycle_details",
                    "time_created",
                    "time_updated",
                    "freeform_tags",
                    "defined_tags",
                    "system_tags",
                ):
                    d.pop(_rm, None)
                cleaned_rss.append(d)
            pd_dict["recovery_service_subnets"] = cleaned_rss

        # Normalize metrics to OCI CLI style keys using only values present on
        # PD.metrics (no derivations/fallbacks)
        metrics_obj = getattr(pd, "metrics", None)
        metrics_dict = None
        if metrics_obj is not None:
            try:
                metrics_dict = metrics_obj.model_dump(exclude_none=False)
            except Exception:
                try:
                    metrics_dict = metrics_obj.dict(exclude_none=False)
                except Exception:
                    metrics_dict = None

        def _pick(d: dict | None, key: str):
            """Read one key from a metrics dict that may be missing entirely."""
            if not isinstance(d, dict):
                return None
            return d.get(key)

        metrics_out = {
            "backup-space-estimate-in-gbs": _pick(metrics_dict, "backup_space_estimate_in_gbs"),
            "backup-space-used-in-gbs": _pick(metrics_dict, "backup_space_used_in_gbs"),
            "current-retention-period-in-seconds": _pick(metrics_dict, "current_retention_period_in_seconds"),
            "db-size-in-gbs": _pick(metrics_dict, "database_size_in_gbs"),
            "is-redo-logs-enabled": _pick(metrics_dict, "is_redo_logs_enabled"),
            "minimum-recovery-needed-in-days": _pick(metrics_dict, "minimum_recovery_needed_in_days"),
            "retention-period-in-days": _pick(metrics_dict, "retention_period_in_days"),
            "unprotected-window-in-seconds": _pick(metrics_dict, "unprotected_window_in_seconds"),
        }
        pd_dict["metrics"] = metrics_out

        return pd_dict

    except Exception as e:
        logger.error(f"Error in get_protected_database tool: {str(e)}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Shows how many protected databases are healthy, warning, alert, or unknown "
        "in a compartment. If a quick list doesn’t include health, it checks each "
        "database to fill it in. The result is a small JSON with the counts, the "
        "compartmentId, and the region."
    )
)
@telemetry._tool_logger("summarize_protected_database_health")
def summarize_protected_database_health(
    compartment_id: Annotated[
        Optional[str],
        "Compartment OCID or compartment display name. If omitted, defaults to the tenancy OCID from your OCI profile.",
    ] = None,
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns aggregated counts plus per-compartment breakdown.",
    ] = False,
    region: Annotated[Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"] = None,
) -> ProtectedDatabaseHealthSummary:
    """
    Summarizes Protected Database health status counts (PROTECTED, WARNING, ALERT, UNKNOWN) in a compartment.
    The tool lists protected databases, reads health from summary when available, falls back to GET per PD,
    and returns counts. Total equals PDs scanned. UNKNOWN counts PDs with missing/None health (often DELETED
    or transitional).
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_recovery_client(region, request_id=request_id)
        comp_id = compartment_id or auth.get_tenancy()
        comp_ids = compartments._compartment_ids_for_tool(
            comp_id,
            fetch_for_child_compartment=fetch_for_child_compartment,
            request_id=request_id,
        )

        protected = 0
        warning = 0
        alert = 0
        unknown = 0
        scanned = 0

        per_compartment: list[dict] = []
        deadline = _Deadline()
        scanned_compartments: list[str] = []

        has_next_page = True
        next_page: Optional[str] = None

        for each_comp in comp_ids:
            if deadline.reached():
                break
            scanned_compartments.append(each_comp)
            c_protected = 0
            c_warning = 0
            c_alert = 0
            c_unknown = 0
            c_scanned = 0

            has_next_page = True
            next_page = None

            while has_next_page and not deadline.reached():
                # Fetch ACTIVE PDs page by page
                list_kwargs = {
                    "compartment_id": each_comp,
                    "page": next_page,
                    "lifecycle_state": "ACTIVE",
                }
                response: oci.response.Response = client.list_protected_databases(**list_kwargs)
                has_next_page = response.has_next_page
                next_page = response.next_page if hasattr(response, "next_page") else None

                data = response.data
                items = getattr(data, "items", data)
                for item in items or []:
                    if deadline.reached():
                        break
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
                    logger.debug(f"Item structure: {item}")
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
                    c_scanned += 1

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
                        c_protected += 1
                    elif health == "WARNING":
                        warning += 1
                        c_warning += 1
                    elif health == "ALERT":
                        alert += 1
                        c_alert += 1
                    else:
                        # unknown/None health
                        unknown += 1
                        c_unknown += 1

            per_compartment.append(
                {
                    "compartmentId": each_comp,
                    "region": region,
                    "protected": c_protected,
                    "warning": c_warning,
                    "alert": c_alert,
                    "unknown": c_unknown,
                    "total": c_scanned,
                    # Only the compartment in flight when the budget ran out can be
                    # short, because the outer loop breaks on the next iteration.
                    # Without this, a partial compartment is indistinguishable from
                    # one that genuinely holds that few databases.
                    "partial": deadline.expired,
                }
            )

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
        # NOTE: construct using the alias key (compartmentId) to avoid any
        # pydantic alias population edge-cases that can result in null output.
        aggregated = ProtectedDatabaseHealthCounts(
            compartmentId=comp_id,
            region=region,
            protected=protected,
            warning=warning,
            alert=alert,
            unknown=unknown,
            total=total,
        )
        if deadline.expired:
            logger.warning(
                "Health summary stopped at its %ss deadline after %s of %s compartments; "
                "counts are partial.",
                _TOOL_DEADLINE_SECONDS,
                len(scanned_compartments),
                len(comp_ids),
            )

        return ProtectedDatabaseHealthSummary(
            aggregated=aggregated,
            per_compartment=per_compartment,
            compartmentIdsScanned=scanned_compartments,
            truncated=deadline.expired,
        )
    except Exception as e:
        logger.error(f"Error in summarize_protected_database_health tool: {str(e)}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Use this tool for real-time protection status questions. It shows how many "
        "protected databases have redo transport (real-time protection) turned on or "
        "off in a compartment. It reads the main setting and uses a fallback when "
        "needed. The result is a simple JSON with enabled, disabled, unknown (the "
        "databases whose setting could not be read), total (all three, i.e. the "
        "databases in scope), the compartmentId, and the region."
    )
)
@telemetry._tool_logger("summarize_protected_database_redo_status")
def summarize_protected_database_redo_status(
    compartment_id: Annotated[
        Optional[str],
        "Compartment OCID or compartment display name. If omitted, defaults to the tenancy OCID from your OCI profile.",
    ] = None,
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns aggregated counts plus per-compartment breakdown.",
    ] = False,
    region: Annotated[Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"] = None,
) -> ProtectedDatabaseRedoSummary:
    """
    Summarizes redo transport enablement for Protected Databases in a compartment.
    Lists protected databases then fetches each to inspect
    is_redo_logs_shipped (true=enabled, false=disabled).
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_recovery_client(region, request_id=request_id)
        comp_id = compartment_id or auth.get_tenancy()
        comp_ids = compartments._compartment_ids_for_tool(
            comp_id,
            fetch_for_child_compartment=fetch_for_child_compartment,
            request_id=request_id,
        )

        enabled = 0
        disabled = 0
        unknown = 0
        per_compartment: list[dict] = []
        deadline = _Deadline()
        scanned_compartments: list[str] = []

        has_next_page = True
        next_page: Optional[str] = None

        for each_comp in comp_ids:
            if deadline.reached():
                break
            scanned_compartments.append(each_comp)
            c_enabled = 0
            c_disabled = 0
            c_unknown = 0

            has_next_page = True
            next_page = None

            while has_next_page and not deadline.reached():
                # List ACTIVE PDs to assess redo status via GET per PD
                list_kwargs = {
                    "compartment_id": each_comp,
                    "page": next_page,
                    "lifecycle_state": "ACTIVE",
                }
                response: oci.response.Response = client.list_protected_databases(**list_kwargs)
                has_next_page = response.has_next_page
                next_page = response.next_page if hasattr(response, "next_page") else None

                data = response.data
                items = getattr(data, "items", data)
                for item in items or []:
                    if deadline.reached():
                        break
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
                        unknown += 1
                        c_unknown += 1
                        continue

                    # Fetch full Protected Database to read is_redo_logs_shipped (primary)
                    redo_enabled = None
                    try:
                        pd_resp: oci.response.Response = client.get_protected_database(
                            protected_database_id=pd_id
                        )
                        pd = pd_resp.data
                        redo_enabled = getattr(pd, "is_redo_logs_shipped", None)
                        if redo_enabled is None and hasattr(pd, "__dict__"):
                            redo_enabled = pd.__dict__.get("is_redo_logs_shipped") or pd.__dict__.get(
                                "isRedoLogsShipped"
                            )
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
                    except Exception:
                        redo_enabled = None

                    if redo_enabled is True:
                        enabled += 1
                        c_enabled += 1
                    elif redo_enabled is False:
                        disabled += 1
                        c_disabled += 1
                    else:
                        # Unreadable is not the same as disabled. Counting it here
                        # keeps a permissions gap visible instead of reporting a
                        # reassuring total that quietly left databases out.
                        unknown += 1
                        c_unknown += 1

            per_compartment.append(
                {
                    "compartmentId": each_comp,
                    "region": region,
                    "enabled": c_enabled,
                    "disabled": c_disabled,
                    "unknown": c_unknown,
                    # total is "databases in scope", so the unreadable ones are in it
                    # -- the same meaning total carries in the health summary. Leaving
                    # them out made a scan with a permissions gap report a smaller
                    # fleet than the caller actually has.
                    "total": c_enabled + c_disabled + c_unknown,
                    # Only the compartment in flight when the budget ran out can be
                    # short, because the outer loop breaks on the next iteration.
                    "partial": deadline.expired,
                }
            )

        total = enabled + disabled + unknown
        logger.info(
            "Redo transport summary for compartment %s (region=%s): "
            "ENABLED=%s, DISABLED=%s, UNKNOWN=%s, TOTAL=%s",
            comp_id,
            region,
            enabled,
            disabled,
            unknown,
            total,
        )
        # NOTE: construct using the alias key (compartmentId) to avoid any
        # pydantic alias population edge-cases that can result in null output.
        aggregated = ProtectedDatabaseRedoCounts(
            compartmentId=comp_id,
            region=region,
            enabled=enabled,
            disabled=disabled,
            unknown=unknown,
            total=total,
        )
        if deadline.expired:
            logger.warning(
                "Redo transport summary stopped at its %ss deadline after %s of %s "
                "compartments; counts are partial.",
                _TOOL_DEADLINE_SECONDS,
                len(scanned_compartments),
                len(comp_ids),
            )

        return ProtectedDatabaseRedoSummary(
            aggregated=aggregated,
            per_compartment=per_compartment,
            compartmentIdsScanned=scanned_compartments,
            truncated=deadline.expired,
        )
    except Exception as e:
        logger.error(f"Error in summarize_protected_database_redo_status tool: {e}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Adds up the backup space (in GB) used by protected databases in a compartment, "
        "including only those with lifecycle state ACTIVE or DELETE_SCHEDULED (excluding "
        "DELETED). It reads each database’s metrics and also tells you how many databases "
        "were checked. The result is a small JSON with the compartmentId, region, "
        "totalDatabasesScanned, and the total space in GB."
    )
)
@telemetry._tool_logger("summarize_backup_space_used")
def summarize_backup_space_used(
    compartment_id: Annotated[
        Optional[str],
        "Compartment OCID or compartment display name. If omitted, defaults to the tenancy OCID from your OCI profile.",
    ] = None,
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns aggregated sum plus per-compartment breakdown.",
    ] = False,
    region: Annotated[
        Optional[str],
        "Canonical OCI region (e.g., us-ashburn-1) to execute the request in.",
    ] = None,
) -> dict:
    """
    Sums backup space used (GB) by Protected Databases in a compartment.
    Only includes PDs with lifecycle_state in {'ACTIVE', 'DELETE_SCHEDULED'} (excludes 'DELETED').
    For each included PD: scans, increments total, and reads backup_space_used_in_gbs from metrics.
    Important: metrics are not reliably exposed on list summaries; fetch the full PD to read metrics.
    Returns: compartmentId, region, totalDatabasesScanned, sumBackupSpaceUsedInGBs.
    """
    try:
        request_id = uuid.uuid4().hex
        comp_id = compartments._resolve_compartment_id(compartment_id, default_to_tenancy=True)
        client = clients.get_recovery_client(region, request_id=request_id)
        comp_ids = compartments._compartment_ids_for_tool(
            comp_id,
            fetch_for_child_compartment=fetch_for_child_compartment,
            request_id=request_id,
        )

        sum_gb = 0.0
        scanned = 0
        missing_metrics = 0
        per_compartment: list[dict] = []

        for each_comp in comp_ids:
            c_sum_gb = 0.0
            c_scanned = 0
            c_missing_metrics = 0

            has_next_page = True
            next_page = None

            while has_next_page:
                list_kwargs = {
                    "compartment_id": each_comp,
                    "page": next_page,
                }
                response: oci.response.Response = client.list_protected_databases(**list_kwargs)
                has_next_page = response.has_next_page
                next_page = response.next_page if hasattr(response, "next_page") else None

                data = response.data
                items = getattr(data, "items", data)

                for item in items or []:
                    # Filter by lifecycle state: include only ACTIVE or DELETE_SCHEDULED
                    # (exclude DELETED and others)
                    try:
                        lifecycle_state = getattr(item, "lifecycle_state", None)
                        if not lifecycle_state and hasattr(item, "__dict__"):
                            lifecycle_state = (getattr(item, "__dict__", {}) or {}).get(
                                "lifecycle_state"
                            ) or (getattr(item, "__dict__", {}) or {}).get("lifecycleState")
                    except Exception:
                        lifecycle_state = None
                    if lifecycle_state not in ("ACTIVE", "DELETE_SCHEDULED"):
                        # Skip PDs that are not ACTIVE or DELETE_SCHEDULED (e.g., DELETED, CREATING, etc.)
                        continue

                    # Robustly get the PD OCID from summary item (same as redo status tool)
                    pd_id = getattr(item, "id", None) or (
                        getattr(item, "data", None) and getattr(item.data, "id", None)
                    )
                    logger.debug(f"Item structure: {item}")
                    if pd_id is None:
                        try:
                            item_dict = getattr(item, "__dict__", None) or {}
                            pd_id = item_dict.get("id")
                        except Exception:
                            pd_id = None
                    if not pd_id:
                        continue

                    scanned += 1
                    c_scanned += 1

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
                                gb_val = metrics.get("backup_space_used_in_gbs") or metrics.get(
                                    "backupSpaceUsedInGbs"
                                )
                    except Exception:
                        # If GET fails, fall back to any summary metrics representation
                        try:
                            m = getattr(item, "metrics", None)
                            if m is not None:
                                gb_val = getattr(m, "backup_space_used_in_gbs", None)
                                if gb_val is None and hasattr(m, "__dict__"):
                                    gb_val = m.__dict__.get("backup_space_used_in_gbs") or m.__dict__.get(
                                        "backupSpaceUsedInGbs"
                                    )
                                if gb_val is None and isinstance(m, dict):
                                    gb_val = m.get("backup_space_used_in_gbs") or m.get(
                                        "backupSpaceUsedInGbs"
                                    )
                        except Exception:
                            gb_val = None

                    if gb_val is None:
                        missing_metrics += 1
                        c_missing_metrics += 1

                    # Ensure numeric value; treat missing/non-numeric as 0.0
                    try:
                        gb = float(gb_val) if gb_val is not None else 0.0
                    except Exception:
                        gb = 0.0

                    sum_gb += gb
                    c_sum_gb += gb

            per_compartment.append(
                {
                    "compartmentId": each_comp,
                    "region": region,
                    "totalDatabasesScanned": c_scanned,
                    "sumBackupSpaceUsedInGBs": round(c_sum_gb, 2),
                    "missingMetricsCount": c_missing_metrics,
                }
            )

        logger.info(
            "Backup space used summary for compartment %s (region=%s): "
            "scanned=%s, total_gb=%s, missing_metrics=%s",
            comp_id,
            region,
            scanned,
            sum_gb,
            missing_metrics,
        )
        aggregated = ProtectedDatabaseBackupSpaceSum(
            compartmentId=comp_id,
            region=region,
            totalDatabasesScanned=scanned,
            sumBackupSpaceUsedInGBs=round(sum_gb, 2),
        )
        try:
            agg_dict = aggregated.model_dump(exclude_none=False, by_alias=True)
        except Exception:
            try:
                agg_dict = aggregated.dict(exclude_none=False, by_alias=True)
            except Exception:
                agg_dict = {
                    "compartmentId": comp_id,
                    "region": region,
                    "totalDatabasesScanned": scanned,
                    "sumBackupSpaceUsedInGBs": round(sum_gb, 2),
                }

        return {
            "aggregated": agg_dict,
            "per_compartment": per_compartment,
            "compartmentIdsScanned": comp_ids,
            "missingMetricsCount": missing_metrics,
        }
        # logger.info(f"Returning dict result: {result}")
        # return result
    except Exception as e:
        logger.error(f"Error in summarize_backup_space_used tool: {str(e)}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Checks OCI service limits for Autonomous Recovery Service using tenancy context from config profile."
        "It fetches resource availability for protected database backup storage (GB) "
        "and protected database count, then returns both values in a simple JSON "
        "response with tenancy compartment and configured region context."
    )
)
@telemetry._tool_logger("check_recovery_service_limits")
def check_recovery_service_limits(
    compartment_id: Annotated[
        Optional[str],
        "(Ignored; accepted for backward compatibility). Limits are always checked against tenancy from config.",
    ] = None,
    region: Annotated[
        Optional[str],
        "(Ignored; accepted for backward compatibility). Region is always taken from OCI config.",
    ] = None,
    opc_request_id: Annotated[Optional[str], "Unique identifier for the request"] = None,
) -> dict:
    """
    Returns resource availability from OCI Limits API for:
      - autonomous-recovery-service / protected-database-backup-storage-gb
      - autonomous-recovery-service / protected-database-count

    Scope/region behavior:
      - Compartment is always the tenancy OCID from server config
      - Region is always the configured profile region
      - `compartment_id` and `region` inputs are accepted only for backward compatibility

    API shape corresponds to:
      GET /20190729/services/autonomous-recovery-service/limits/<limitName>/resourceAvailability
    """
    try:
        request_id = uuid.uuid4().hex
        resolved_compartment_id = auth.get_tenancy()
        target_region = (auth._effective_region("us-ashburn-1") or "us-ashburn-1").strip()
        client = clients.get_limits_client(target_region, request_id=request_id)

        service_name = "autonomous-recovery-service"
        limit_map = {
            "protectedDatabaseBackupStorageGb": "protected-database-backup-storage-gb",
            "protectedDatabaseCount": "protected-database-count",
        }

        def _as_dict(obj: Any) -> dict[str, Any]:
            """Best-effort conversion of a Limits SDK object to a plain dict."""
            if obj is None:
                return {}
            if isinstance(obj, dict):
                return dict(obj)
            try:
                return oci.util.to_dict(obj)
            except Exception:
                pass
            if hasattr(obj, "__dict__"):
                try:
                    return dict(obj.__dict__)
                except Exception:
                    pass
            return {}

        limits_out: dict[str, Any] = {}

        for out_key, limit_name in limit_map.items():
            kwargs: dict[str, Any] = {
                "service_name": service_name,
                "limit_name": limit_name,
                "compartment_id": resolved_compartment_id,
            }
            if opc_request_id is not None:
                kwargs["opc_request_id"] = opc_request_id

            resp: oci.response.Response = client.get_resource_availability(**kwargs)
            data_dict = _as_dict(getattr(resp, "data", None))

            # Keep response explicit and stable for dashboard/tooling usage
            limits_out[out_key] = {
                "serviceName": service_name,
                "limitName": limit_name,
                "scopeType": data_dict.get("scope_type"),
                "available": data_dict.get("available"),
                "used": data_dict.get("used"),
                "fractionalAvailability": data_dict.get("fractional_availability"),
                "fractionalUsage": data_dict.get("fractional_usage"),
                "effectiveQuotaValue": data_dict.get("effective_quota_value"),
                "policyName": data_dict.get("policy_name"),
            }

        return {
            "compartmentId": resolved_compartment_id,
            "region": target_region,
            "serviceName": service_name,
            "limits": limits_out,
        }
    except Exception as e:
        logger.error(f"Error in check_recovery_service_limits tool: {str(e)}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Lists the tenancy's subscribed regions and their status using "
        "IdentityClient.list_region_subscriptions(). "
        "NOTE: The 'service' parameter is accepted for backward compatibility but is "
        "not used, because IAM region subscriptions are tenancy-wide, not service-specific."
    )
)
@telemetry._tool_logger("fetch_regions_subscribed")
def fetch_regions_subscribed(
    tenancy_id: Annotated[Optional[str], "OCID of the compartment to scope the search."] = None,
) -> dict:
    """
    Lists the tenancy's subscribed regions and each region's subscription status.

    ``tenancy_id`` only labels the result; region subscriptions are tenancy-wide,
    so it does not narrow the lookup. When omitted, the server's own tenancy is
    used.
    """
    request_id = uuid.uuid4().hex
    if not tenancy_id:
        tenancy_id = auth.get_tenancy()
    subscribed = regions._iam_subscribed_regions_with_status(request_id=request_id)
    return {
        "tenancyId": tenancy_id,
        "regions": subscribed,
        "total": len(subscribed),
    }


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Lists protection policies in a compartment with handy filters and automatic "
        "paging. The result is a straightforward list of protection policies."
    )
)
@telemetry._tool_logger("list_protection_policies")
def list_protection_policies(
    compartment_id: Annotated[str, "The compartment OCID or compartment display name"],
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns the combined results.",
    ] = False,
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
    sort_by: Annotated[Optional[str], 'Sort by field: "timeCreated" or "displayName"'] = None,
    opc_request_id: Annotated[Optional[str], "Unique identifier for the request"] = None,
    region: Annotated[Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"] = None,
) -> list[ProtectionPolicy]:
    """
    Paginates through Recovery Service to list Protection Policies and returns
    a list of ProtectionPolicy models mapped from the OCI SDK response.
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_recovery_client(region, request_id=request_id)

        results: list[ProtectionPolicy] = []

        comp_ids = compartments._compartment_ids_for_tool(
            compartment_id,
            fetch_for_child_compartment=fetch_for_child_compartment,
            request_id=request_id,
        )

        for comp_id in comp_ids:
            has_next_page = True
            next_page: Optional[str] = page

            while has_next_page:
                # Collect filters/controls into kwargs
                kwargs = {
                    "compartment_id": comp_id,
                    "page": next_page,
                }
                if lifecycle_state is not None:
                    kwargs["lifecycle_state"] = lifecycle_state
                if display_name is not None:
                    kwargs["display_name"] = display_name
                if id is not None:
                    # This SDK call names the filter protection_policy_id and rejects "id"
                    # outright; list_protected_databases and list_recovery_service_subnets do
                    # take "id", which is why only this one is remapped.
                    kwargs["protection_policy_id"] = id
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
                    logger.debug(f"Item structure: {d}")
                    pp = map_protection_policy(d)
                    if pp is not None:
                        results.append(pp)

        # De-dupe by OCID when scanning multiple compartments
        if fetch_for_child_compartment:
            uniq: dict[str, Any] = {}
            for r in results:
                rid = getattr(r, "id", None) if r is not None else None
                if rid and rid not in uniq:
                    uniq[rid] = r
            results = list(uniq.values())

        logger.info(f"Found {len(results)} Protection Policies")
        return results

    except Exception as e:
        logger.error(f"Error in list_protection_policies tool: {str(e)}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=("Gets a protection policy by OCID and returns it as a simple object."))
@telemetry._tool_logger("get_protection_policy")
def get_protection_policy(
    protection_policy_id: Annotated[str, "Protection Policy OCID"],
    opc_request_id: Annotated[Optional[str], "Unique identifier for the request"] = None,
    region: Annotated[Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"] = None,
) -> ProtectionPolicy:
    """
    Retrieves a single Protection Policy resource from Recovery Service and returns
    a ProtectionPolicy model mapped from the OCI SDK response.
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_recovery_client(region, request_id=request_id)

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
    annotations=_READ_ONLY_TOOL,
    description=(
        "Lists recovery service subnets in a compartment with helpful filters. When "
        "needed, it fills in the list of associated subnets or uses the subnet_id as "
        "a fallback. The result is a simple list of subnets with the subnets list "
        "included when available."
    )
)
@telemetry._tool_logger("list_recovery_service_subnets")
def list_recovery_service_subnets(
    compartment_id: Annotated[str, "The compartment OCID or compartment display name"],
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns the combined results.",
    ] = False,
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
    sort_by: Annotated[Optional[str], 'Sort by field: "timeCreated" or "displayName"'] = None,
    opc_request_id: Annotated[Optional[str], "Unique identifier for the request"] = None,
    region: Annotated[Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"] = None,
) -> list[RecoveryServiceSubnet]:
    """
    Paginates through Recovery Service to list Recovery Service Subnets and returns
    a list of RecoveryServiceSubnet models mapped from the OCI SDK response.
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_recovery_client(region, request_id=request_id)

        results: list[RecoveryServiceSubnet] = []

        comp_ids = compartments._compartment_ids_for_tool(
            compartment_id,
            fetch_for_child_compartment=fetch_for_child_compartment,
            request_id=request_id,
        )

        for comp_id in comp_ids:
            has_next_page = True
            next_page: Optional[str] = page

            while has_next_page:
                kwargs = {
                    "compartment_id": comp_id,
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
                    logger.debug(f"Item structure: {d}")
                    rss = map_recovery_service_subnet(d)
                    if rss is None:
                        continue
                    # Enrich with subnets list if missing by fetching the full resource
                    try:
                        missing_subnets = getattr(rss, "subnets", None) is None
                        rss_id = getattr(rss, "id", None)
                        if missing_subnets and rss_id:
                            try:
                                g = client.get_recovery_service_subnet(recovery_service_subnet_id=rss_id)
                                full = map_recovery_service_subnet(getattr(g, "data", None))
                                if full and getattr(full, "subnets", None):
                                    rss.subnets = full.subnets
                            except Exception:
                                pass
                    except Exception:
                        pass
                    # Final fallback: if still missing, derive from subnet_id when available
                    try:
                        if getattr(rss, "subnets", None) is None:
                            sid = getattr(rss, "subnet_id", None)
                            if sid:
                                rss.subnets = [sid]
                    except Exception:
                        pass
                    results.append(rss)

        # De-dupe by OCID when scanning multiple compartments
        if fetch_for_child_compartment:
            uniq: dict[str, Any] = {}
            for r in results:
                rid = getattr(r, "id", None) if r is not None else None
                if rid and rid not in uniq:
                    uniq[rid] = r
            results = list(uniq.values())

        logger.info(f"Found {len(results)} Recovery Service Subnets")
        return results

    except Exception as e:
        logger.error(f"Error in list_recovery_service_subnets tool: {str(e)}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Gets a recovery service subnet by OCID and makes sure the subnets list is "
        "present, using subnet_id if necessary. The result is one recovery service "
        "subnet."
    )
)
@telemetry._tool_logger("get_recovery_service_subnet")
def get_recovery_service_subnet(
    recovery_service_subnet_id: Annotated[str, "Recovery Service Subnet OCID"],
    opc_request_id: Annotated[Optional[str], "Unique identifier for the request"] = None,
    region: Annotated[Optional[str], "OCI region to execute the request in (e.g., us-ashburn-1)"] = None,
) -> RecoveryServiceSubnet:
    """
    Retrieves a single Recovery Service Subnet resource from Recovery Service and returns
    a RecoveryServiceSubnet model mapped from the OCI SDK response.
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_recovery_client(region, request_id=request_id)

        kwargs = {}
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        response: oci.response.Response = client.get_recovery_service_subnet(
            recovery_service_subnet_id=recovery_service_subnet_id, **kwargs
        )

        data = response.data
        rss = map_recovery_service_subnet(data)
        # Ensure subnets is populated even if service omits the array
        try:
            if getattr(rss, "subnets", None) is None:
                sid = getattr(rss, "subnet_id", None)
                if sid:
                    rss.subnets = [sid]
        except Exception:
            pass
        logger.info(f"Fetched Recovery Service Subnet {recovery_service_subnet_id}")
        return rss

    except Exception as e:
        logger.error(f"Error in get_recovery_service_subnet tool: {str(e)}")
        raise


# Fields of the mapped WorkRequest that list_restore can sort by. The OCI-style
# camelCase spelling is what the API's own sort_by accepts, so both it and the
# model's attribute name are recognised.
_RESTORE_SORT_FIELDS = {
    "timeaccepted": "time_accepted",
    "time_accepted": "time_accepted",
    "timestarted": "time_started",
    "time_started": "time_started",
    "timefinished": "time_finished",
    "time_finished": "time_finished",
    "status": "status",
    "operationtype": "operation_type",
    "operation_type": "operation_type",
}
_SORT_ORDERS = ("ASC", "DESC")


def _sorted_work_requests(
    items: list[WorkRequest], sort_by: Optional[str], sort_order: Optional[str]
) -> list[WorkRequest]:
    """Order restore work requests locally.

    The Work Requests API has no sort parameters (see the call site), so sorting
    happens here. Entries missing the sort field sort last in either direction,
    rather than being dropped or raising on a None comparison.
    """
    if sort_by is None and sort_order is None:
        return items

    field = "time_accepted"
    if sort_by is not None:
        key = str(sort_by).strip().lower()
        if key not in _RESTORE_SORT_FIELDS:
            raise ValueError(
                "sort_by must be one of: timeAccepted, timeStarted, timeFinished, "
                f"status, operationType. Received: {sort_by!r}"
            )
        field = _RESTORE_SORT_FIELDS[key]

    order = (sort_order or "DESC").strip().upper()
    if order not in _SORT_ORDERS:
        raise ValueError(f"sort_order must be one of: {', '.join(_SORT_ORDERS)}. Received: {sort_order!r}")

    present = [item for item in items if getattr(item, field, None) is not None]
    missing = [item for item in items if getattr(item, field, None) is None]
    return sorted(
        present,
        key=lambda item: getattr(item, field),
        reverse=(order == "DESC"),
    ) + missing


# Monitoring query vocabulary. The tool builds an MQL expression by
# interpolation, so every part of it that comes from the caller is checked
# against these first: an unvalidated value would let a caller reshape the query
# (and break out of the quoted resourceId filter), and a typo would surface as an
# opaque service-side parse error instead of a usable message.
_METRIC_NAMES = (
    "SpaceUsedForRecoveryWindow",
    "ProtectedDatabaseSize",
    "ProtectedDatabaseHealth",
    "DataLossExposure",
)
_METRIC_RESOLUTIONS = ("1m", "5m", "1h", "1d")
_METRIC_AGGREGATIONS = ("mean", "sum", "max", "min", "count")
_OCID_RE = re.compile(r"^ocid1\.[a-z0-9]+\.[a-z0-9-]+\.[a-z0-9-]*\.[A-Za-z0-9._-]+$")


def _validated_choice(value: str, allowed: tuple[str, ...], field: str) -> str:
    """Return value if it is one of allowed, else raise a message naming them."""
    if value not in allowed:
        raise ValueError(f"{field} must be one of: {', '.join(allowed)}. Received: {value!r}")
    return value


def _validated_ocid(value: str, field: str) -> str:
    """Return value if it is shaped like an OCID, else raise."""
    if not _OCID_RE.match(value or ""):
        raise ValueError(f"{field} must be an OCID (ocid1.<type>.<realm>...). Received: {value!r}")
    return value


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Fetches Recovery Service metrics for a time range. You choose the metric, "
        "time step, and how to combine values, and you can limit it to one protected "
        "database. The result is a simple time series where each item has dimensions "
        "and a list of {timestamp, value} points."
    )
)
@telemetry._tool_logger("get_recovery_service_metrics")
def get_recovery_service_metrics(
    compartment_id: Annotated[str, "The compartment OCID or compartment display name to query metrics for."],
    start_time: Annotated[str, "Start time for the metric query. Provide a RFC3339/ISO-8601 timestamp."],
    end_time: Annotated[str, "End time for the metric query. Provide a RFC3339/ISO-8601 timestamp."],
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns the combined results.",
    ] = False,
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
        "The aggregation for the metric. Currently we only support: mean, sum, max, min, count. Default: max",
    ] = "max",
    protected_database_id: Annotated[
        Optional[str],
        "Optional protected database OCID to filter by (maps to resourceId dimension)",
    ] = None,
) -> list[dict]:
    """
    Queries Monitoring for a Recovery Service metric over a time range.

    Returns one time series per dimension combination, each a list of
    {timestamp, value} points at the requested resolution and aggregation, and
    optionally narrowed to a single protected database.
    """
    # Every interpolated part is validated before it reaches the query string.
    metric_name = _validated_choice(metricName, _METRIC_NAMES, "metricName")
    metric_resolution = _validated_choice(resolution, _METRIC_RESOLUTIONS, "resolution")
    metric_aggregation = _validated_choice(aggregation, _METRIC_AGGREGATIONS, "aggregation")

    filter_clause = ""
    if protected_database_id:
        resource_id = _validated_ocid(protected_database_id, "protected_database_id")
        filter_clause = f'{{resourceId="{resource_id}"}}'

    # Build Monitoring query against Recovery metrics namespace
    request_id = uuid.uuid4().hex
    monitoring_client = clients.get_monitoring_client(request_id=request_id)
    namespace = "oci_recovery_service"
    # Query format: MetricName[resolution]{filters}.aggregation()
    query = f"{metric_name}[{metric_resolution}]{filter_clause}.{metric_aggregation}()"

    comp_ids = compartments._compartment_ids_for_tool(
        compartment_id,
        fetch_for_child_compartment=fetch_for_child_compartment,
        request_id=request_id,
    )

    results: list[dict] = []

    for comp_id in comp_ids:
        # Fetch time series data for the metric and time window
        series_list = monitoring_client.summarize_metrics_data(
            compartment_id=comp_id,
            summarize_metrics_data_details=SummarizeMetricsDataDetails(
                namespace=namespace,
                query=query,
                start_time=start_time,
                end_time=end_time,
                resolution=metric_resolution,
            ),
        ).data

        # Convert SDK series into a simple dict of dimensions + aggregated datapoints
        for series in series_list:
            logger.debug(f"Item structure: {series}")
            dims = getattr(series, "dimensions", None)
            points = []
            for p in getattr(series, "aggregated_datapoints", []):
                points.append(
                    {
                        "timestamp": getattr(p, "timestamp", None),
                        "value": getattr(p, "value", None),
                    }
                )
            results.append(
                {
                    "compartmentId": comp_id,
                    "dimensions": dims,
                    "datapoints": points,
                }
            )

    return results


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Lists databases in a DB Home or, if none is given, across all DB Homes in a "
        "compartment. It can find DB Homes for you, fills in backup settings only when "
        "needed, and, where possible, links each database to its protection policy. "
        "The result is a list of database summaries with optional backup settings and "
        "protection policy ID."
    )
)
@telemetry._tool_logger("list_databases")
def list_databases(
    compartment_id: Annotated[
        Optional[str], "The compartment OCID or display name. Required if db_home_id is not provided."
    ] = None,
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns the combined results.",
    ] = False,
    db_home_id: Annotated[
        Optional[str],
        "A Database Home OCID. If omitted, all DB Homes in the compartment will be used.",
    ] = None,
    system_id: Annotated[
        Optional[str], "The OCID of the Exadata DB system to filter by (Exadata only)."
    ] = None,
    limit: Annotated[Optional[int], "The maximum number of items to return per page."] = None,
    page: Annotated[Optional[str], "The pagination token to continue listing from."] = None,
    sort_by: Annotated[Optional[str], 'Sort by field: "DBNAME" | "TIMECREATED"'] = None,
    sort_order: Annotated[Optional[str], '"ASC" or "DESC"'] = None,
    lifecycle_state: Annotated[Optional[str], "Exact lifecycle state filter."] = None,
    db_name: Annotated[Optional[str], "Exact database name filter (case-insensitive)."] = None,
    region: Annotated[Optional[str], "Region to execute the request, e.g., us-ashburn-1."] = None,
) -> list[DatabaseSummary]:
    """
    Lists databases in a DB Home, or across every DB Home in a compartment.

    Exactly one starting point is required: ``db_home_id``, or a
    ``compartment_id`` whose DB Homes are discovered first. Backup settings are
    filled in lazily -- the full Database is fetched only when the summary comes
    back without them -- and each database is correlated with its Recovery
    Service protection policy where one can be found.
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_database_client(region, request_id=request_id)
        if compartment_id:
            compartment_id = compartments._resolve_compartment_id(compartment_id)

        # Determine compartment scope
        comp_ids: list[Optional[str]] = []
        if db_home_id is None:
            if not compartment_id:
                raise ValueError(
                    "Either db_home_id must be provided or compartment_id must be set to derive DB Homes."
                )
            comp_ids = compartments._compartment_ids_for_tool(
                compartment_id,
                fetch_for_child_compartment=fetch_for_child_compartment,
                request_id=request_id,
            )
        else:
            # db_home_id is explicit: keep existing behavior and don't expand compartments
            # A compartment is not required by the OCI list_databases API when
            # the DB Home has already been supplied.
            comp_ids = [compartment_id]

        results: list[DatabaseSummary] = []

        # Try to correlate database_id -> protection_policy_id via Recovery PDs (best-effort)
        # If we're scanning child compartments, include PDs from each scanned compartment.
        pd_policy_by_dbid: dict[str, str] = {}
        if compartment_id:
            try:
                rec_client = clients.get_recovery_client(region, request_id=request_id)
                pd_comp_ids = (
                    compartments._compartment_ids_for_tool(
                        compartment_id,
                        fetch_for_child_compartment=fetch_for_child_compartment,
                        request_id=request_id,
                    )
                    if fetch_for_child_compartment
                    else [compartment_id]
                )
            except Exception as e:
                # No Recovery client or no compartment scope: every database is
                # returned without a policy link, which is the best that can be done.
                logging_setup._log_event(
                    "protection_policy_enrichment_unavailable",
                    request_id=request_id,
                    tool="list_databases",
                    payload={"error": str(e)},
                    level=logging.WARNING,
                )
                pd_comp_ids = []

            skipped: list[str] = []
            for pd_comp_id in pd_comp_ids:
                # Scoped per compartment on purpose. A caller who cannot list
                # protected databases in one compartment of a subtree gets a 404
                # there; failing the whole correlation would strip the policy link
                # off every database in every *readable* compartment too, which
                # reads as "no protection policy" rather than "could not check".
                try:
                    has_next = True
                    next_page = None
                    while has_next:
                        lp = rec_client.list_protected_databases(compartment_id=pd_comp_id, page=next_page)
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
                            ppid = d.get("protectionPolicyId") or d.get("protection_policy_id")
                            if dbid and ppid and dbid not in pd_policy_by_dbid:
                                pd_policy_by_dbid[dbid] = ppid
                except Exception as e:
                    skipped.append(pd_comp_id)
                    logging_setup._log_event(
                        "protection_policy_enrichment_skipped_compartment",
                        request_id=request_id,
                        tool="list_databases",
                        payload={"compartment_id": pd_comp_id, "error": str(e)},
                        level=logging.WARNING,
                    )

            if skipped:
                logger.warning(
                    "Protection policy correlation skipped %s of %s compartments the caller "
                    "cannot read; databases in those compartments have no protectionPolicyId.",
                    len(skipped),
                    len(pd_comp_ids),
                )

        # Common list_databases filters shared across DB Homes
        common_kwargs: dict = {}
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

        # Iterate compartments -> DB homes -> list databases
        for each_comp in comp_ids:
            # Determine DB Home scope for this compartment:
            # - If db_home_id not provided, discover all DB Homes in the compartment.
            # - If provided, just use that one.
            if db_home_id is None:
                home_ids = compartments._fetch_db_home_ids_for_compartment(each_comp, region=region)
            else:
                home_ids = [db_home_id]

            if not home_ids:
                continue

            # For each DB Home, list databases and map summaries
            for hid in home_ids:
                kwargs = dict(common_kwargs)
                kwargs["db_home_id"] = hid
                if db_home_id is None:
                    kwargs["compartment_id"] = each_comp

                response: oci.response.Response = client.list_databases(**kwargs)
                raw = getattr(response.data, "items", response.data)
                for item in raw or []:
                    logger.debug(f"Item structure: {item}")
                    mapped = map_database_summary(item)
                    if mapped is None:
                        continue

                    # Enrich db_backup_config lazily by fetching full Database only if missing
                    try:
                        if getattr(mapped, "db_backup_config", None) is None:
                            db_id = getattr(item, "id", None) or (
                                getattr(item, "data", None) and getattr(item.data, "id", None)
                            )
                            if not db_id and hasattr(item, "__dict__"):
                                db_id = item.__dict__.get("id")
                            if db_id:
                                gd = client.get_database(database_id=db_id).data
                                # Try to locate backup config from object or dict forms
                                cfg_src = getattr(gd, "db_backup_config", None) or getattr(
                                    gd, "database_backup_config", None
                                )
                                if cfg_src is None:
                                    try:
                                        d = (
                                            oci.util.to_dict(gd)
                                            if hasattr(oci, "util") and hasattr(oci.util, "to_dict")
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
                        mapped.protection_policy_id = pd_policy_by_dbid.get(mapped.id)
                    except Exception:
                        pass
                    results.append(mapped)

        # De-dupe by DB OCID when scanning multiple compartments / homes
        if fetch_for_child_compartment and db_home_id is None:
            uniq: dict[str, DatabaseSummary] = {}
            for r in results:
                rid = getattr(r, "id", None) if r is not None else None
                if rid and rid not in uniq:
                    uniq[rid] = r
            results = list(uniq.values())

        return results
    except Exception as e:
        logger.error(f"Error in list_databases tool: {e}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Gets a database by OCID and returns an easy object. Where possible, it also "
        "links the database to its protection policy. The result is one database."
    )
)
@telemetry._tool_logger("get_database")
def get_database(
    database_id: Annotated[str, "OCID of the Database to retrieve."],
    region: Annotated[Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."] = None,
) -> Database:
    """
    Retrieves a Database by OCID and maps it to the server model.

    The mapped result is enriched with ``protection_policy_id`` by correlating
    the database with Recovery Service protected databases in the same
    compartment; enrichment failures are swallowed so the core lookup still
    returns.
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_database_client(region, request_id=request_id)
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
                rec_client = clients.get_recovery_client(region, request_id=request_id)
                has_next = True
                next_page = None
                found_ppid = None
                # Scan PDs in compartment until we find a match by databaseId
                while has_next and not found_ppid:
                    lp = rec_client.list_protected_databases(compartment_id=comp_id, page=next_page)
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
                            found_ppid = d.get("protectionPolicyId") or d.get("protection_policy_id")
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
    annotations=_READ_ONLY_TOOL,
    description=(
        "Finds database restore requests and returns only active or historical restore jobs."
        "Use this when answering customer questions about database restore status, "
        "restore history, or whether a restore request exists."
    )
)
@telemetry._tool_logger("list_restore")
def list_restore(
    compartment_id: Annotated[str, "Compartment OCID or compartment display name to scope work requests."],
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns the combined results.",
    ] = False,
    resource_id: Annotated[
        Optional[str], "Optional resource OCID to scope work requests (e.g., Database OCID)."
    ] = None,
    status: Annotated[
        Optional[str],
        "Optional work request status filter (e.g., IN_PROGRESS, SUCCEEDED, FAILED). "
        "Applied to the returned restore work requests.",
    ] = None,
    limit: Annotated[Optional[int], "Maximum number of items per backend page."] = None,
    page: Annotated[Optional[str], "Pagination token (opc-next-page) when aggregate_pages=false."] = None,
    sort_order: Annotated[Optional[str], 'Sort order: "ASC" or "DESC". Default "DESC".'] = None,
    sort_by: Annotated[
        Optional[str],
        "Sort the returned restore work requests by one of: timeAccepted, timeStarted, "
        "timeFinished, status, operationType.",
    ] = None,
    opc_request_id: Annotated[Optional[str], "Unique identifier for the request"] = None,
    region: Annotated[Optional[str], "Canonical OCI region (e.g., us-phoenix-1)."] = None,
    aggregate_pages: Annotated[bool, "When true (default), retrieves all pages."] = True,
) -> list[WorkRequest]:
    """
    Lists restore work requests for a compartment, or for a single resource.

    Work requests are fetched per compartment in scope, filtered down to restore
    operations, then sorted and optionally narrowed by status. With
    ``aggregate_pages`` set (the default) every backend page is walked, so
    ``page`` and ``limit`` only apply when it is turned off.
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_work_request_client(region, request_id=request_id)

        def _is_restore_operation(operation: Optional[str]) -> bool:
            """
            Match a work request operation type against "Restore Database", ignoring
            separator and case differences between SDK versions.
            """
            if operation is None:
                return False
            raw = str(operation).strip()
            if raw == "Restore Database":
                return True
            normalized = raw.replace("_", " ").replace("-", " ").lower()
            normalized = " ".join(normalized.split())
            return normalized == "restore database"

        comp_ids = compartments._compartment_ids_for_tool(
            compartment_id,
            fetch_for_child_compartment=fetch_for_child_compartment,
            request_id=request_id,
        )

        results: list[WorkRequest] = []

        for each_comp in comp_ids or [compartment_id]:
            next_page = page
            while True:
                kwargs: dict[str, Any] = {
                    "compartment_id": each_comp,
                }
                if resource_id is not None:
                    kwargs["resource_id"] = resource_id
                # status/sort_by/sort_order are deliberately NOT forwarded:
                # oci.work_requests.WorkRequestClient.list_work_requests accepts only
                # resource_id, limit, page and opc_request_id, and raises ValueError on
                # anything else. They are applied to the results below instead, the same
                # way this tool already filters by operation type.
                if opc_request_id is not None:
                    kwargs["opc_request_id"] = opc_request_id
                if limit is not None:
                    kwargs["limit"] = limit
                elif aggregate_pages:
                    kwargs["limit"] = 1000
                if next_page is not None:
                    kwargs["page"] = next_page

                response = client.list_work_requests(**kwargs)
                items = getattr(response.data, "items", response.data) or []
                raw_items = items if isinstance(items, list) else [items]

                for item in raw_items:
                    mapped = map_work_request(item)
                    if mapped is None:
                        continue
                    if not _is_restore_operation(getattr(mapped, "operation_type", None)):
                        continue
                    if status is not None and str(
                        getattr(mapped, "status", "") or ""
                    ).strip().upper() != status.strip().upper():
                        continue
                    results.append(mapped)

                has_next = bool(getattr(response, "has_next_page", False))
                next_page = getattr(response, "next_page", None) if has_next else None
                if not (aggregate_pages and has_next and next_page):
                    break

        if fetch_for_child_compartment:
            uniq: dict[str, WorkRequest] = {}
            for r in results:
                rid = getattr(r, "id", None) if r is not None else None
                if rid and rid not in uniq:
                    uniq[rid] = r
            results = list(uniq.values())

        return _sorted_work_requests(results, sort_by, sort_order)
    except Exception as e:
        logger.error("Error in list_restore tool: %s", e)
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Lists database backups with flexible filters and optional auto-paging. If "
        "database_id is provided, lists all backups for that database. If compartment_id "
        "is provided, finds AVAILABLE databases with auto-backup enabled and lists their "
        "backups. It includes manual backups, automatic backups and LTR backups as well. "
        "It adds helpful fields like backup destination, database's unique name. The "
        "result is a list of easy-to-read backup summaries."
    )
)
@telemetry._tool_logger("list_backups")
def list_backups(
    compartment_id: Annotated[
        Optional[str], "Compartment OCID or compartment display name to scope the search."
    ] = None,
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns the combined results.",
    ] = False,
    database_id: Annotated[Optional[str], "OCID of the Database to filter backups for."] = None,
    lifecycle_state: Annotated[Optional[str], "Filter by lifecycle state."] = None,
    type: Annotated[Optional[str], "Backup type filter (e.g., INCREMENTAL, FULL)."] = None,
    limit: Annotated[
        Optional[int],
        "Maximum number of items per backend page (when aggregate_pages=false).",
    ] = None,
    page: Annotated[Optional[str], "Pagination token (opc-next-page) when aggregate_pages=false."] = None,
    region: Annotated[Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."] = None,
    aggregate_pages: Annotated[bool, "When true (default), retrieves all pages."] = True,
) -> list[BackupSummary]:
    """
    Lists Database backups, either for one database or across a compartment.

    With ``database_id``, backups for that database are listed directly. With
    ``compartment_id``, AVAILABLE databases that have auto-backup enabled are
    discovered first and their backups are combined. Manual, automatic and
    long-term retention backups are all included, and each result is augmented
    from the raw SDK object for fields the model mapper leaves unset.
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_database_client(region, request_id=request_id)

        def _to_dict(o):
            """Best-effort conversion of an SDK object to a plain dict."""
            try:
                if hasattr(oci, "util") and hasattr(oci.util, "to_dict"):
                    d = oci.util.to_dict(o)
                    if isinstance(d, dict):
                        return d
            except Exception:
                pass
            return getattr(o, "__dict__", {}) if hasattr(o, "__dict__") else {}

        def _is_auto_backup_enabled_from_dict(d: dict) -> bool:
            """
            Read the auto-backup flag out of a database dict.

            The backup config nests under several different key spellings depending on
            SDK version and casing, so each known variant is tried before falling back to
            looking for the flag at the top level.
            """
            cfg = None
            for k in (
                "dbBackupConfig",
                "db_backup_config",
                "backupConfig",
                "backup_config",
                "databaseBackupConfig",
                "database_backup_config",
            ):
                v = d.get(k)
                if isinstance(v, dict):
                    cfg = v
                    break
            src = cfg if isinstance(cfg, dict) else d
            for key in (
                "isAutoBackupEnabled",
                "is_auto_backup_enabled",
                "autoBackupEnabled",
                "auto_backup_enabled",
            ):
                if key in src and src[key] is not None:
                    return bool(src[key])
            return False

        def _list_all_backups_for_db(dbid: str) -> list[dict]:
            """Walk every backup page for one database and return mapped dicts."""
            out: list[dict] = []
            next_token = None
            while True:
                call_kwargs = {"database_id": dbid}
                if lifecycle_state:
                    call_kwargs["lifecycle_state"] = lifecycle_state
                if type:
                    call_kwargs["type"] = type
                if not aggregate_pages:
                    if limit is not None:
                        call_kwargs["limit"] = limit
                    if page is not None and next_token is None:
                        call_kwargs["page"] = page
                if next_token is not None:
                    call_kwargs["page"] = next_token
                if "limit" not in call_kwargs or call_kwargs.get("limit") is None:
                    call_kwargs["limit"] = 1000
                resp = client.list_backups(**call_kwargs)
                items = getattr(resp.data, "items", resp.data) or []
                raw_list = items if isinstance(items, list) else [items]
                for obj in raw_list:
                    logger.debug(f"Item structure: {obj}")
                    mapped = map_backup_summary(obj)
                    if mapped is None:
                        continue
                    try:
                        out_dict = mapped.model_dump(exclude_none=False, by_alias=True)
                    except Exception:
                        try:
                            out_dict = mapped.dict(exclude_none=False, by_alias=True)
                        except Exception:
                            out_dict = _to_dict(mapped)

                    # Augment with raw SDK values for missing fields
                    try:
                        rawd = _to_dict(obj)
                    except Exception:
                        rawd = getattr(obj, "__dict__", {}) or {}

                    def _pick(d: dict, *keys: str):
                        """Return the first non-null value among several key spellings."""
                        for k in keys:
                            if k in d and d[k] is not None:
                                return d[k]
                        return None

                    if out_dict.get("database-size-in-gbs") is None:
                        ds = _pick(
                            rawd,
                            "database_size_in_gbs",
                            "databaseSizeInGBs",
                            "databaseSizeInGbs",
                        )
                        if ds is not None:
                            out_dict["database-size-in-gbs"] = ds
                    if out_dict.get("backup-destination-type") is None:
                        bdt = _pick(rawd, "backup_destination_type", "backupDestinationType")
                        if bdt is not None:
                            out_dict["backup-destination-type"] = bdt
                    if out_dict.get("retention-period-in-days") is None:
                        rpd = _pick(rawd, "retention_period_in_days", "retentionPeriodInDays")
                        if rpd is not None:
                            out_dict["retention-period-in-days"] = rpd
                    if out_dict.get("retention-period-in-years") is None:
                        rpy = _pick(rawd, "retention_period_in_years", "retentionPeriodInYears")
                        if rpy is not None:
                            out_dict["retention-period-in-years"] = rpy

                    # Ensure CLI-style keys are present even when values are still null
                    for _k in (
                        "database-size-in-gbs",
                        "backup-destination-type",
                        "retention-period-in-days",
                        "retention-period-in-years",
                    ):
                        if _k not in out_dict:
                            out_dict[_k] = None

                    out.append(out_dict)
                has_next = bool(getattr(resp, "has_next_page", False))
                next_token = getattr(resp, "next_page", None) if has_next else None
                if not (aggregate_pages and has_next and next_token):
                    break
            return out

        # Branch 1: database_id provided
        if database_id:
            backups = _list_all_backups_for_db(database_id)
            # Fetch and set db_unique_name for this database
            try:
                gdb = client.get_database(database_id=database_id)
                gdd = _to_dict(getattr(gdb, "data", None))
                dun = gdd.get("dbUniqueName") or gdd.get("db_unique_name")
            except Exception:
                dun = None
            for bk in backups:
                if "db_unique_name" not in bk or bk["db_unique_name"] is None:
                    bk["db_unique_name"] = dun
            return backups

        # Branch 2: compartment_id and region provided
        if compartment_id:
            comp_ids = compartments._compartment_ids_for_tool(
                compartment_id,
                fetch_for_child_compartment=fetch_for_child_compartment,
                request_id=request_id,
            )

            # find DB Homes then list AVAILABLE databases (per compartment)
            eligible_db_ids: list[str] = []
            db_unique_cache: dict[str, Optional[str]] = {}
            for each_comp in comp_ids:
                home_ids = compartments._fetch_db_home_ids_for_compartment(each_comp, region=region)
                for hid in home_ids or []:
                    next_db_page = None
                    while True:
                        kwargs_db = {
                            "compartment_id": each_comp,
                            "db_home_id": hid,
                            "lifecycle_state": "AVAILABLE",
                            "limit": 1000,
                        }
                        if next_db_page:
                            kwargs_db["page"] = next_db_page
                        dresp = client.list_databases(**kwargs_db)
                        ditems = getattr(dresp.data, "items", dresp.data) or []
                        for d in ditems:
                            logger.debug(f"Item structure: {d}")
                            d_dict = _to_dict(d)
                            dbid = d_dict.get("id") or getattr(d, "id", None)
                            dun = (
                                d_dict.get("dbUniqueName")
                                or d_dict.get("db_unique_name")
                                or getattr(d, "db_unique_name", None)
                            )
                            is_auto = _is_auto_backup_enabled_from_dict(d_dict)
                            if is_auto is False and dbid:
                                # fallback to GET for authoritative value and db_unique_name
                                try:
                                    g = client.get_database(database_id=dbid)
                                    gdd = _to_dict(getattr(g, "data", None))
                                    is_auto = _is_auto_backup_enabled_from_dict(gdd)
                                    if dun is None:
                                        dun = gdd.get("dbUniqueName") or gdd.get("db_unique_name")
                                except Exception:
                                    is_auto = False
                            if dbid:
                                if dun is not None:
                                    db_unique_cache[dbid] = dun
                                if is_auto:
                                    eligible_db_ids.append(dbid)
                        has_next = bool(getattr(dresp, "has_next_page", False))
                        next_db_page = getattr(dresp, "next_page", None) if has_next else None
                        if not has_next:
                            break

            # Aggregate backups for eligible DBs
            all_results: list[dict] = []
            seen_backup_ids: set[str] = set()
            for dbid in eligible_db_ids:
                backups = _list_all_backups_for_db(dbid)
                # Set db_unique_name from cache
                for bk in backups:
                    if "db_unique_name" not in bk or bk["db_unique_name"] is None:
                        bk["db_unique_name"] = db_unique_cache.get(dbid)

                if fetch_for_child_compartment:
                    # de-dupe by backup OCID across DBs/compartments
                    for bk in backups:
                        bid = bk.get("id") if isinstance(bk, dict) else None
                        if bid and bid in seen_backup_ids:
                            continue
                        if bid:
                            seen_backup_ids.add(bid)
                        all_results.append(bk)
                else:
                    all_results.extend(backups)

            return all_results

        # Neither database_id nor compartment_id provided
        raise ValueError("Provide database_id or compartment_id.")

    except Exception as e:
        logger.error("Error in list_backups tool: %s", e)
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Gets a database backup by OCID and returns a clean dictionary. It includes "
        "common fields like database size, backup destination, and the database's "
        "unique name. The result is one backup with those helpful fields included."
    )
)
@telemetry._tool_logger("get_backup")
def get_backup(
    backup_id: Annotated[str, "OCID of the Backup to retrieve."],
    region: Annotated[Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."] = None,
) -> Backup:
    """
    Retrieves a Database Backup by OCID and maps it to the server model.
    Mirrors the simpler logic used in rcv_mcp_server/fast_server.py without additional enrichment.
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_database_client(region, request_id=request_id)
        resp = client.get_backup(backup_id=backup_id)
        mapped = map_backup(resp.data)
        try:
            out = mapped.model_dump(exclude_none=False, by_alias=True)
        except Exception:
            try:
                out = mapped.dict(exclude_none=False, by_alias=True)
            except Exception:
                out = getattr(mapped, "__dict__", {}) or {}
        # Try to augment from raw SDK object dict if mapping missed fields
        try:
            rawd = (
                oci.util.to_dict(resp.data)
                if hasattr(oci, "util") and hasattr(oci.util, "to_dict")
                else (getattr(resp.data, "__dict__", {}) or {})
            )
        except Exception:
            rawd = getattr(resp.data, "__dict__", {}) or {}

        def _pick(d: dict, *keys: str):
            """Return the first non-null value among several key spellings."""
            for k in keys:
                if k in d and d[k] is not None:
                    return d[k]
            return None

        if out.get("database-size-in-gbs") is None:
            ds = _pick(rawd, "database_size_in_gbs", "databaseSizeInGBs", "databaseSizeInGbs")
            if ds is not None:
                out["database-size-in-gbs"] = ds
        if out.get("backup-destination-type") is None:
            bdt = _pick(rawd, "backup_destination_type", "backupDestinationType")
            if bdt is not None:
                out["backup-destination-type"] = bdt
        if out.get("retention-period-in-days") is None:
            rpd = _pick(rawd, "retention_period_in_days", "retentionPeriodInDays")
            if rpd is not None:
                out["retention-period-in-days"] = rpd
        if out.get("retention-period-in-years") is None:
            rpy = _pick(rawd, "retention_period_in_years", "retentionPeriodInYears")
            if rpy is not None:
                out["retention-period-in-years"] = rpy

        # Infer destination from DB backup config if still missing (no Recovery Service calls)
        try:
            dbid = out.get("database_id") or rawd.get("databaseId")
            if (out.get("backup-destination-type") is None) and dbid:
                gdb = client.get_database(database_id=dbid)
                gdd = (
                    oci.util.to_dict(getattr(gdb, "data", None))
                    if hasattr(oci, "util") and hasattr(oci.util, "to_dict")
                    else (getattr(getattr(gdb, "data", None), "__dict__", {}) or {})
                )
                cfg = (
                    gdd.get("dbBackupConfig")
                    or gdd.get("db_backup_config")
                    or gdd.get("databaseBackupConfig")
                )
                details = None
                if isinstance(cfg, dict):
                    details = cfg.get("backupDestinationDetails") or cfg.get("backup_destination_details")
                if not details:
                    details = gdd.get("backupDestinationDetails") or gdd.get("backup_destination_details")
                det_list = details if isinstance(details, list) else ([details] if details else [])
                types = []
                for det in det_list:
                    dd = (
                        det
                        if isinstance(det, dict)
                        else (
                            oci.util.to_dict(det)
                            if hasattr(oci, "util") and hasattr(oci.util, "to_dict")
                            else det.__dict__
                            if hasattr(det, "__dict__")
                            else {}
                        )
                    )
                    t = (dd or {}).get("type") or (dd or {}).get("destinationType")
                    tnorm = str(t).upper() if t else None
                    if tnorm in (
                        "RECOVERY_SERVICE",
                        "RECOVERY-SERVICE",
                        "DBRS",
                        "RECOVERY_SERVICE_BACKUP_DESTINATION",
                    ):
                        types.append("DBRS")
                    elif tnorm in ("OBJECT_STORE", "OBJECTSTORE", "OBJECT_STORAGE"):
                        types.append("OBJECT_STORE")
                    elif tnorm in ("NFS",):
                        types.append("NFS")
                if "DBRS" in types:
                    out["backup-destination-type"] = "DBRS"
                elif "OBJECT_STORE" in types:
                    out["backup-destination-type"] = "OBJECT_STORE"
                elif "NFS" in types:
                    out["backup-destination-type"] = "NFS"
        except Exception:
            pass

        # Ensure db_unique_name on model and output
        try:
            dbid = out.get("database_id") or rawd.get("databaseId") or rawd.get("database_id")
            if dbid:
                try:
                    gdb = client.get_database(database_id=dbid)
                    gdd = (
                        oci.util.to_dict(getattr(gdb, "data", None))
                        if hasattr(oci, "util") and hasattr(oci.util, "to_dict")
                        else (getattr(getattr(gdb, "data", None), "__dict__", {}) or {})
                    )
                    dun = gdd.get("dbUniqueName") or gdd.get("db_unique_name")
                    try:
                        if getattr(mapped, "db_unique_name", None) is None:
                            mapped.db_unique_name = dun
                    except Exception:
                        pass
                    if dun is not None:
                        out["db_unique_name"] = dun
                except Exception:
                    pass
        except Exception:
            pass

        # Ensure CLI-style keys are present even when values are still null
        for _k in (
            "database-size-in-gbs",
            "backup-destination-type",
            "retention-period-in-days",
            "retention-period-in-years",
        ):
            if _k not in out:
                out[_k] = None
        return out
    except Exception as e:
        logger.error("Error in get_backup tool: %s", e)
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Summarizes how databases in a compartment or DB Home are backed up. It can "
        "find DB Homes, looks at each database’s backup settings, can include the time "
        "of the most recent backup, and groups results by destination type while calling "
        "out databases that aren’t configured. The result is one summary object with "
        "counts, name lists, and per‑database details."
    )
)
@telemetry._tool_logger("summarize_protected_database_backup_destination")
def summarize_protected_database_backup_destination(
    compartment_id: Annotated[
        Optional[str],
        "Compartment OCID or compartment display name. If omitted, defaults to the tenancy/DEFAULT profile.",
    ] = None,
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns aggregated summary plus per-compartment breakdown.",
    ] = False,
    region: Annotated[Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."] = None,
    db_home_id: Annotated[
        Optional[str],
        "Optional DB Home OCID to scope databases. If omitted, all DB Homes in the compartment are used.",
    ] = None,
    include_last_backup_time: Annotated[
        bool, "If true, compute last backup time per DB (extra API calls)."
    ] = True,
    db_name: Annotated[Optional[str], "Exact database name filter (case-insensitive)."] = None,
    limit_per_home: Annotated[Optional[int], "Max databases to fetch per DB Home."] = None,
    max_db_homes: Annotated[Optional[int], "Max number of DB Homes to scan."] = None,
    max_total_databases: Annotated[Optional[int], "Global cap on databases to scan."] = None,
) -> ProtectedDatabaseBackupDestinationSummary:
    """
    Summarizes how the databases in a compartment or DB Home are backed up.

    Discovers DB Homes when none is given, reads each database's backup
    configuration, optionally looks up the most recent backup time, and groups
    the databases by destination type (DBRS, Object Store, NFS) while calling out
    those with no backup destination configured. Returns one summary object
    carrying counts, name lists and per-database detail.
    """
    try:
        request_id = uuid.uuid4().hex
        db_client = clients.get_database_client(region, request_id=request_id)
        if not compartment_id:
            compartment_id = auth.get_tenancy()

        comp_ids = compartments._compartment_ids_for_tool(
            compartment_id,
            fetch_for_child_compartment=fetch_for_child_compartment,
            request_id=request_id,
        )

        # Discover DB Homes if not specified, then list databases with lifecycle_state=AVAILABLE
        # NOTE: db_home_id is a single home; we do NOT expand it across compartments.
        home_ids_by_comp: dict[str, list[str]] = {}
        for each_comp in comp_ids:
            home_ids_by_comp[each_comp] = (
                [db_home_id] if db_home_id else compartments._fetch_db_home_ids_for_compartment(each_comp, region=region)
            )

        # Explicitly bind the SDK method to avoid any accidental reference to the MCP tool
        list_dbs_method = getattr(db_client, "list_databases")
        db_summaries: list[Any] = []
        for each_comp, home_ids in home_ids_by_comp.items():
            if not home_ids:
                continue
            for hid in home_ids[:max_db_homes] if (max_db_homes is not None) else home_ids:
                call_kwargs = {
                    "compartment_id": each_comp,
                    "db_home_id": hid,
                    "lifecycle_state": "AVAILABLE",
                }
                if db_name is not None:
                    call_kwargs["db_name"] = db_name
                if limit_per_home is not None:
                    call_kwargs["limit"] = limit_per_home
                next_page = None
                while True:
                    local_kwargs = dict(call_kwargs)
                    if next_page:
                        local_kwargs["page"] = next_page
                    resp = list_dbs_method(**local_kwargs)
                    data = getattr(resp.data, "items", resp.data)
                    if isinstance(data, list):
                        db_summaries.extend(data)
                    elif data is not None:
                        db_summaries.append(data)
                    if max_total_databases is not None and len(db_summaries) >= max_total_databases:
                        db_summaries = db_summaries[:max_total_databases]
                        break
                    has_next = bool(getattr(resp, "has_next_page", False))
                    next_page = getattr(resp, "next_page", None) if has_next else None
                    if not has_next:
                        break

        # Simplified: do not correlate via Recovery Protected Databases

        # Helper routines to normalize SDK objects and read fields across variants
        def _to_dict(o: Any) -> dict:
            """Best-effort conversion of an SDK object to a plain dict."""
            try:
                if hasattr(oci, "util") and hasattr(oci.util, "to_dict"):
                    d = oci.util.to_dict(o)
                    if isinstance(d, dict):
                        return d
            except Exception:
                pass
            return getattr(o, "__dict__", {}) if hasattr(o, "__dict__") else {}

        def _get(o: Any, *names: str):
            """Read the first non-null of several field names, by attribute then by key."""
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
            """
            Return a database's backup destination entries as a list.

            The details live under the backup config, whose key spelling varies by SDK
            version, and may arrive as a single object rather than a list.
            """
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
            """Canonicalize a destination type to DBRS, OBJECT_STORE, NFS or UNKNOWN."""
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
                return "OBJECT_STORE"
            if u in ("NFS",):
                return "NFS"
            return u

        def _is_auto_backup_enabled(db_dict: dict) -> bool:
            """Read the auto-backup flag out of a database dict, trying each key variant."""
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
            """
            Collect every timestamp a backup object exposes, newest field first.

            End, start and creation times are all gathered because SDK shapes differ in
            which of them they populate; the caller picks the most recent.
            """
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
                db_name_val = _get(s, "db_name", "dbName")

                # Prefer backup config from summary item to avoid per-DB GET when possible
                d_obj = None
                d_dict = _to_dict(s)
                cfg_present = False
                try:
                    cfg_present = any(
                        isinstance(d_dict.get(k), dict)
                        for k in (
                            "dbBackupConfig",
                            "db_backup_config",
                            "databaseBackupConfig",
                            "database_backup_config",
                            "backupConfig",
                            "backup_config",
                        )
                    )
                except Exception:
                    cfg_present = False
                if not cfg_present:
                    dresp = get_db(database_id=sid)
                    d_obj = getattr(dresp, "data", None)
                    d_dict = _to_dict(d_obj)

                # Extract configured destination details (normalize to a list of dicts)
                dest_details = _extract_backup_destination_details(d_dict)
                dest_types: list[str] = []
                dest_ids: list[str] = []
                for det in dest_details:
                    dd = det if isinstance(det, dict) else _to_dict(det)
                    t_norm = _normalize_dest_type(dd.get("type") or dd.get("destinationType"))
                    did = dd.get("id") or dd.get("backupDestinationId") or dd.get("destinationId")
                    if t_norm:
                        dest_types.append(t_norm)
                    if did:
                        dest_ids.append(did)

                # Deduplicate and restrict to DBRS/OBJECT_STORE; prefer DBRS if both
                dest_types = list(dict.fromkeys([t for t in dest_types if t in ("DBRS", "OBJECT_STORE")]))
                if "DBRS" in dest_types and "OBJECT_STORE" in dest_types:
                    dest_types = ["DBRS"]
                dest_ids = list(dict.fromkeys([d for d in dest_ids if d]))

                auto_enabled = _is_auto_backup_enabled(d_dict)
                # Configured strictly when auto-backup is enabled
                configured = bool(auto_enabled)
                status = "CONFIGURED" if configured else "UNCONFIGURED"
                last_backup_time = None

                # Optionally compute last backup time (more API calls)
                if include_last_backup_time:
                    try:
                        b_resp = list_bk(database_id=sid)
                        b_data = getattr(b_resp.data, "items", b_resp.data)
                        backups = (
                            b_data if isinstance(b_data, list) else [b_data] if b_data is not None else []
                        )
                        best = None
                        for b in backups:
                            for t in _read_backup_times_from_obj(b):
                                if best is None or (str(t) > str(best)):
                                    best = t
                        if best is not None:
                            last_backup_time = best
                    except Exception:
                        pass
                else:
                    pass

                # Aggregate summary counters and name lists by status/destination
                name_for_lists = db_name_val or sid
                if status == "CONFIGURED":
                    # Select a single effective destination type: DBRS preferred over OBJECT_STORE
                    eff_type = (
                        "DBRS"
                        if "DBRS" in dest_types
                        else ("OBJECT_STORE" if "OBJECT_STORE" in dest_types else "UNKNOWN")
                    )
                    if eff_type in ("DBRS", "OBJECT_STORE"):
                        counts_by_type[eff_type] = counts_by_type.get(eff_type, 0) + 1
                        db_names_by_type.setdefault(eff_type, []).append(name_for_lists)
                else:
                    unconfigured += 1
                    unconfigured_names.append(name_for_lists)

                # Append per-DB detail record
                items.append(
                    ProtectedDatabaseBackupDestinationItem(
                        database_id=sid,
                        db_name=db_name_val,
                        status=status,
                        destination_types=dest_types,
                        destination_ids=dest_ids,
                        last_backup_time=last_backup_time,
                    )
                )
            except Exception:
                # Continue on per-DB errors to maximize overall coverage
                continue

        # Sorting helpers: prioritize DBRS over OBJECT_STORE and then by name
        def _dest_rank(types: list[str]) -> int:
            """Rank a database's destination types so DBRS sorts ahead of the rest."""
            if not types:
                return 99
            order = {"DBRS": 0, "OBJECT_STORE": 1, "NFS": 2, "UNKNOWN": 3}
            return min(order.get(t, 3) for t in types)

        items = sorted(
            items,
            key=lambda it: (
                _dest_rank(it.destination_types),
                (it.db_name or ""),
            ),
        )

        # Name list post-processing
        def _uniq_sorted(xs: list[str]) -> list[str]:
            """Sort names, dropping blanks and duplicates."""
            return sorted(dict.fromkeys([x for x in xs if x]))

        # Preserve duplicates for name lists that can correspond to different DB OCIDs
        def _sorted_keep(xs: list[str]) -> list[str]:
            """
            Sort names, dropping blanks but keeping duplicates.

            Two databases may share a name under different OCIDs, so collapsing
            duplicates here would undercount them.
            """
            return sorted([x for x in xs if x])

        db_names_by_type = {k: _sorted_keep(v) for k, v in db_names_by_type.items()}
        unconfigured_names = _uniq_sorted(unconfigured_names)
        has_backups_names = _uniq_sorted(has_backups_names)

        # De-dupe by DB OCID when scanning multiple compartments
        if fetch_for_child_compartment:
            uniq_items: dict[str, ProtectedDatabaseBackupDestinationItem] = {}
            for it in items:
                did = getattr(it, "database_id", None)
                if did and did not in uniq_items:
                    uniq_items[did] = it
            items = list(uniq_items.values())

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
        logger.error(f"Error in summarize_protected_database_backup_destination tool: {e}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Lists database homes in a compartment with optional lifecycle filters, "
        "defaulting to your tenancy when no compartment is given, and handles paging "
        "for you. The result is a list of database home summaries."
    )
)
@telemetry._tool_logger("list_db_homes")
def list_db_homes(
    compartment_id: Annotated[
        Optional[str], "Compartment OCID or compartment display name to scope the search."
    ] = None,
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns the combined results.",
    ] = False,
    db_system_id: Annotated[
        Optional[str], "The OCID of the Exadata DB system to filter the DB homes by."
    ] = None,
    limit: Annotated[Optional[int], "Maximum number of items per page."] = None,
    page: Annotated[Optional[str], "Pagination token (opc-next-page)."] = None,
    region: Annotated[Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."] = None,
) -> list[DatabaseHomeSummary]:
    """
    Lists DB Homes in a compartment, defaulting to the tenancy when none is given.

    Not exposed as an MCP tool; the database and backup tools call it to discover
    DB Homes before listing what lives in them. Paging is handled internally.
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_database_client(region, request_id=request_id)
        if not compartment_id and not db_system_id:
            compartment_id = auth.get_tenancy()

        comp_ids = (
            compartments._compartment_ids_for_tool(
                compartment_id,
                fetch_for_child_compartment=fetch_for_child_compartment,
                request_id=request_id,
            )
            if compartment_id
            else []
        )

        results: list[DatabaseHomeSummary] = []
        for each_comp in comp_ids or [compartment_id] if compartment_id else []:
            has_next = True
            next_page = page
            while has_next:
                kwargs: dict = {"page": next_page}
                if each_comp:
                    kwargs["compartment_id"] = each_comp
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

        if fetch_for_child_compartment:
            uniq: dict[str, DatabaseHomeSummary] = {}
            for r in results:
                rid = getattr(r, "id", None) if r is not None else None
                if rid and rid not in uniq:
                    uniq[rid] = r
            results = list(uniq.values())

        return results
    except Exception as e:
        logger.error(f"Error in list_db_homes tool: {e}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Gets a database home by OCID and returns it as a simple object. The result is one database home."
    )
)
@telemetry._tool_logger("get_db_home")
def get_db_home(
    db_home_id: Annotated[str, "OCID of the DB Home to retrieve."],
    region: Annotated[Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."] = None,
) -> DatabaseHome:
    """Retrieves a DB Home by OCID and maps it to the server model."""
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_database_client(region, request_id=request_id)
        resp = client.get_db_home(db_home_id=db_home_id)
        return map_database_home(resp.data)
    except Exception as e:
        logger.error(f"Error in get_db_home tool: {e}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Lists database systems in a compartment with optional lifecycle filters, "
        "defaulting to your tenancy when no compartment is given, and handles paging "
        "for you. The result is a list of database system summaries."
    )
)
@telemetry._tool_logger("list_db_systems")
def list_db_systems(
    compartment_id: Annotated[
        Optional[str], "Compartment OCID or compartment display name to scope the search."
    ] = None,
    fetch_for_child_compartment: Annotated[
        bool,
        "When true, scans the full subtree under compartment_id (including child compartments) and returns the combined results.",
    ] = False,
    lifecycle_state: Annotated[Optional[str], "Filter by lifecycle state."] = None,
    limit: Annotated[Optional[int], "Maximum number of items per page."] = None,
    page: Annotated[Optional[str], "Pagination token (opc-next-page)."] = None,
    region: Annotated[Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."] = None,
) -> list[DbSystemSummary]:
    """
    Lists DB Systems in a compartment, defaulting to the tenancy when none is given.

    Paging is handled internally, and the scan can be widened to the full
    compartment subtree.
    """
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_database_client(region, request_id=request_id)
        if not compartment_id:
            compartment_id = auth.get_tenancy()

        comp_ids = (
            compartments._compartment_ids_for_tool(
                compartment_id,
                fetch_for_child_compartment=fetch_for_child_compartment,
                request_id=request_id,
            )
            if compartment_id
            else []
        )

        results: list[DbSystemSummary] = []
        for each_comp in comp_ids or [compartment_id] if compartment_id else []:
            has_next = True
            next_page = page
            while has_next:
                kwargs: dict = {"page": next_page}
                if each_comp:
                    kwargs["compartment_id"] = each_comp
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

        if fetch_for_child_compartment:
            uniq: dict[str, DbSystemSummary] = {}
            for r in results:
                rid = getattr(r, "id", None) if r is not None else None
                if rid and rid not in uniq:
                    uniq[rid] = r
            results = list(uniq.values())

        return results
    except Exception as e:
        logger.error(f"Error in list_db_systems tool: {e}")
        raise


@mcp.tool(
    annotations=_READ_ONLY_TOOL,
    description=(
        "Gets a database system by OCID and returns it as a convenient object. The "
        "result is one database system."
    )
)
@telemetry._tool_logger("get_db_system")
def get_db_system(
    db_system_id: Annotated[str, "OCID of the DB System to retrieve."],
    region: Annotated[Optional[str], "Canonical OCI region (e.g., us-ashburn-1)."] = None,
) -> DbSystem:
    """Retrieves a DB System by OCID and maps it to the server model."""
    try:
        request_id = uuid.uuid4().hex
        client = clients.get_database_client(region, request_id=request_id)
        resp = client.get_db_system(db_system_id=db_system_id)
        return map_db_system(resp.data)
    except Exception as e:
        logger.error(f"Error in get_db_system tool: {e}")
        raise


@mcp.tool(
    annotations=_LOCAL_GUIDANCE_TOOL,
    description=(
        "Returns dashboard-generation guidance for OCI Recovery Service, including "
        "cloud-protected databases."
    )
)
@telemetry._tool_logger("oci_recovery_service_dashboard_prompt")
def oci_recovery_service_dashboard_prompt() -> str:
    """Return dashboard-generation guidance as a tool for clients without prompt support."""
    return OCI_RECOVERY_SERVICE_DASHBOARD_PROMPT


@mcp.tool(
    annotations=_LOCAL_GUIDANCE_TOOL,
    description=(
        "Always call this tool first when a user asks to onboard, protect, enable Recovery Service backups for, or register a database to Recovery Service. The tool first determines and verifies whether the target database is OCI DBaaS or purely on-premises, retrieves the latest Oracle requirements, and performs only the read-only prerequisite checks appropriate for that deployment type. For OCI DBaaS, it configures DBRS automatic backups using the current UpdateDatabase / DbBackupConfig contract, then independently verifies the protected database, assigned policy, health status, and initial backup. For on-premises databases, it proceeds with the Cloud Protect workflow only after the deployment type has been verified and the required approval has been obtained."
    )
)
@telemetry._tool_logger("onboard_database_to_recovery_service")
def onboard_database_to_recovery_service() -> str:
    """Return database onboarding guidance as a tool for clients without prompt support."""
    return ONBOARD_DATABASE_TO_RECOVERY_SERVICE_PROMPT


@mcp.tool(
    annotations=_LOCAL_GUIDANCE_TOOL,
    description=(
        "Use this tool first whenever the user's underlying goal is to investigate, explain, or assess the health of Oracle Database backup, protection, or recoverability in an environment using Recovery Service. This includes explicit failures as well as implicit concerns such as unexpected backup behavior, stale or missing backups, protection lag, missing recovery points, restore/PITR problems, policy or retention behavior, RMAN issues, or questions about whether a protected database is healthy and recoverable. Also use it when the user asks whether anything is wrong with the protection environment, even without reporting an error. The tool provides an evidence-driven, access-first diagnostic workflow that traces the actual execution path, acquires relevant evidence, tests competing root-cause hypotheses, independently assesses recoverability, and guides safe remediation and verification. Do not use it for general database questions unrelated to backup, recovery, protection, or recoverability."
    )
)
@telemetry._tool_logger("diagnose_recovery_service_issue")
def diagnose_recovery_service_issue() -> str:
    """Return Recovery Service diagnostic guidance as a tool for clients without prompt support."""
    return DIAGNOSE_RECOVERY_SERVICE_ISSUE_PROMPT


def main():
    """
    Console entrypoint: start FastMCP over stdio, or over HTTP when a listener is
    configured.

    ORACLE_MCP_HOST and ORACLE_MCP_PORT must be set together; with neither set the
    server speaks stdio using local profile credentials. With both set it serves
    streamable HTTP and authenticates every caller against an OCI IAM (IDCS)
    domain -- local profile credentials are never used to serve a network
    listener.
    """
    host = (os.getenv("ORACLE_MCP_HOST") or "").strip()
    port = (os.getenv("ORACLE_MCP_PORT") or "").strip()

    # Log startup and where logs are actually going (stderr if the file could
    # not be opened, so the line never points at a file that does not exist).
    logger.info("Starting %s v%s", __project__, __version__)
    logger.info("Logs will be written to: %s", logging_setup._LOG_DESTINATION)

    if bool(host) != bool(port):
        raise ValueError(
            "ORACLE_MCP_HOST and ORACLE_MCP_PORT must either both be set or both be unset."
        )

    if not host:
        logger.info("Running FastMCP over stdio transport (auth_type=%s)", auth._resolved_auth_type_label())
        mcp.run()
        return

    try:
        port_number = int(port)
    except ValueError as exc:
        raise ValueError("ORACLE_MCP_PORT must be an integer from 1 to 65535.") from exc
    if not 1 <= port_number <= 65535:
        raise ValueError("ORACLE_MCP_PORT must be an integer from 1 to 65535.")

    # HTTP transport authenticates every caller against an OCI IAM (IDCS) domain;
    # local profile credentials are never used to serve a network listener.
    logger.info("Running FastMCP over streamable HTTP with OCI IAM OAuth at http://%s:%s", host, port)
    auth._http_auth = auth._build_http_auth()
    mcp.auth = auth._http_auth.provider
    mcp.run(transport="http", host=host, port=port_number)


if __name__ == "__main__":
    main()
