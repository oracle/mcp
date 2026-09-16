"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

The aggregating tools: protection health, redo shipping, backup space used and
backup destinations. Each fans out over a compartment scope rather than reading a
single resource, which is why this is the only family that needs ``app._Deadline``
to bound how long that fan-out may run.
"""

import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Optional

import oci

# Database Service models and mappers
from oracle.oci_recovery_mcp_server.models import (
    ProtectedDatabaseBackupDestinationItem,
    ProtectedDatabaseBackupDestinationSummary,
    ProtectedDatabaseBackupSpaceSum,
    ProtectedDatabaseHealthCounts,
    ProtectedDatabaseHealthSummary,
    ProtectedDatabaseRedoCounts,
    ProtectedDatabaseRedoSummary,
)

from . import (
    auth,
    clients,
    compartments,
    telemetry,
)
from .logging_setup import logger
from . import app
from .app import mcp, _READ_ONLY_TOOL


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
        deadline = app._Deadline()
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
            partial=deadline.expired,
        )
        if deadline.expired:
            logger.warning(
                "Health summary stopped at its %ss deadline after %s of %s compartments; "
                "counts are partial.",
                app._TOOL_DEADLINE_SECONDS,
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
        deadline = app._Deadline()
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
            partial=deadline.expired,
        )
        if deadline.expired:
            logger.warning(
                "Redo transport summary stopped at its %ss deadline after %s of %s "
                "compartments; counts are partial.",
                app._TOOL_DEADLINE_SECONDS,
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
        # This tool reads one metric per protected database across every compartment in
        # scope, so it has the same unbounded fan-out the health and redo summaries are
        # already budgeted for. Without the budget a large tenancy turns one call into
        # hundreds of sequential round trips, long past the point an MCP client waits.
        deadline = app._Deadline()
        scanned_compartments: list[str] = []

        for each_comp in comp_ids:
            if deadline.reached():
                break
            scanned_compartments.append(each_comp)
            c_sum_gb = 0.0
            c_scanned = 0
            c_missing_metrics = 0

            has_next_page = True
            next_page = None

            while has_next_page and not deadline.reached():
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
                    if deadline.reached():
                        break
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
        if deadline.expired:
            logger.warning(
                "Backup space summary stopped at its %ss deadline after %s of %s "
                "compartments; the totals below cover only those.",
                app._TOOL_DEADLINE_SECONDS,
                len(scanned_compartments),
                len(comp_ids),
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
            # What was actually scanned, not what was in scope: on a truncated run those
            # differ, and a total covering half the compartments read as a whole-tenancy
            # figure would be worse than no answer.
            "compartmentIdsScanned": scanned_compartments,
            "compartmentIdsInScope": comp_ids,
            "missingMetricsCount": missing_metrics,
            "truncated": deadline.expired,
        }
        # logger.info(f"Returning dict result: {result}")
        # return result
    except Exception as e:
        logger.error(f"Error in summarize_backup_space_used tool: {str(e)}")
        raise


# ---------------------------------------------------------------------------
# Shape readers for the backup-destination summary.
#
# The OCI Database SDK returns these records as model objects on some paths and as
# plain dicts on others, in both snake_case and camelCase. These absorb that so the
# summary itself can read one shape. They were nested inside the tool, where they
# were re-created on every call and could not be tested without driving the whole
# 400-line fan-out; they close over nothing, so module level costs nothing.
# ---------------------------------------------------------------------------

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


def _as_instant(value: Any) -> Optional[datetime]:
    """
    Read one SDK timestamp as a comparable, timezone-aware datetime.

    The SDK hands back a datetime on some shapes and an ISO-8601 string on
    others, and the two do not order against each other as text: str() renders a
    datetime with a space separator and a string keeps its "T", and " " sorts
    below "T", so the datetime always loses regardless of when it actually
    happened. Comparing parsed instants removes the question. A naive value is
    read as UTC, which is what the OCI APIs emit.
    """
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


# Sorting helpers: prioritize DBRS over OBJECT_STORE and then by name
def _dest_rank(types: list[str]) -> int:
    """Rank a database's destination types so DBRS sorts ahead of the rest."""
    if not types:
        return 99
    order = {"DBRS": 0, "OBJECT_STORE": 1, "NFS": 2, "UNKNOWN": 3}
    return min(order.get(t, 3) for t in types)


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


def _latest_backup_time(database_id: str, *, list_backups) -> tuple[Any, bool]:
    """
    The most recent backup timestamp for one database, and whether it has any at all.

    Returns the timestamp in the shape the SDK gave it, so the response keeps the
    service's own rendering; the parsed instant is used only to decide which is newest.
    A database can have backups whose timestamps are all unreadable, which is why
    "has backups" is reported separately rather than inferred from the timestamp.
    """
    resp = list_backups(database_id=database_id)
    data = getattr(resp.data, "items", resp.data)
    backups = data if isinstance(data, list) else [data] if data is not None else []

    newest = None
    newest_instant = None
    for backup in backups:
        for stamp in _read_backup_times_from_obj(backup):
            instant = _as_instant(stamp)
            if instant is None:
                continue
            if newest_instant is None or instant > newest_instant:
                newest, newest_instant = stamp, instant
    return newest, bool(backups)


def _backup_destinations_for(summary_row: Any, *, get_database) -> tuple[dict, list[str], list[str]]:
    """
    Read one database's backup configuration: its full record, destination types and ids.

    The list response sometimes carries the backup config already and sometimes does
    not, so the per-database GET is made only when it is missing -- on a large DB Home
    that is the difference between one call and one call per database.

    Types are narrowed to the two this summary reports and de-duplicated, with DBRS
    winning when a database has both: the question the tool answers is which service
    protects a database, and DBRS is the answer whenever it is present.
    """
    record = _to_dict(summary_row)
    config_keys = (
        "dbBackupConfig",
        "db_backup_config",
        "databaseBackupConfig",
        "database_backup_config",
        "backupConfig",
        "backup_config",
    )
    try:
        has_config = any(isinstance(record.get(k), dict) for k in config_keys)
    except Exception:
        has_config = False
    if not has_config:
        response = get_database(database_id=_get(summary_row, "id"))
        record = _to_dict(getattr(response, "data", None))

    types: list[str] = []
    ids: list[str] = []
    for detail in _extract_backup_destination_details(record):
        entry = detail if isinstance(detail, dict) else _to_dict(detail)
        kind = _normalize_dest_type(entry.get("type") or entry.get("destinationType"))
        identifier = (
            entry.get("id") or entry.get("backupDestinationId") or entry.get("destinationId")
        )
        if kind:
            types.append(kind)
        if identifier:
            ids.append(identifier)

    types = list(dict.fromkeys([t for t in types if t in ("DBRS", "OBJECT_STORE")]))
    if "DBRS" in types and "OBJECT_STORE" in types:
        types = ["DBRS"]
    return record, types, list(dict.fromkeys([i for i in ids if i]))


def _scan_available_databases(
    db_client,
    home_ids_by_compartment: dict[str, list[str]],
    *,
    db_name: Optional[str] = None,
    limit_per_home: Optional[int] = None,
    max_db_homes: Optional[int] = None,
    max_total_databases: Optional[int] = None,
    deadline=None,
) -> list[Any]:
    """
    Every AVAILABLE database across the given compartments and DB Homes.

    Three loops deep -- compartment, DB Home, result page -- because that is the shape
    of the API: databases are reached only through a home, and homes only through a
    compartment. Pulling it out of the tool leaves one thing to reason about, which
    matters most for the cap: max_total_databases has to stop all three levels, and
    when this was inline the break reached only the page loop, so each further home
    resumed appending past it.
    """
    list_databases = getattr(db_client, "list_databases")
    found: list[Any] = []

    def _stop() -> bool:
        """True once the global cap or the time budget is spent, at any depth."""
        if max_total_databases is not None and len(found) >= max_total_databases:
            return True
        return bool(deadline is not None and deadline.reached())

    for compartment, home_ids in home_ids_by_compartment.items():
        if _stop():
            break
        for home_id in (home_ids[:max_db_homes] if max_db_homes is not None else home_ids):
            if _stop():
                break
            call_kwargs: dict[str, Any] = {
                "compartment_id": compartment,
                "db_home_id": home_id,
                "lifecycle_state": "AVAILABLE",
            }
            if db_name is not None:
                call_kwargs["db_name"] = db_name
            if limit_per_home is not None:
                call_kwargs["limit"] = limit_per_home

            next_page = None
            while True:
                page_kwargs = dict(call_kwargs)
                if next_page:
                    page_kwargs["page"] = next_page
                response = list_databases(**page_kwargs)
                data = getattr(response.data, "items", response.data)
                if isinstance(data, list):
                    found.extend(data)
                elif data is not None:
                    found.append(data)
                if _stop():
                    return found[:max_total_databases] if max_total_databases else found
                if not getattr(response, "has_next_page", False):
                    break
                next_page = getattr(response, "next_page", None)

    return found


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
        bool,
        "If true, look up each database's backups to report its last backup time "
        "(extra API calls). Also what populates has_backups_db_names, which is empty "
        "when this is false because no backup is then queried.",
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

        # Two OCI calls per database on top of the compartment/home/page walk, so this
        # is the heaviest fan-out of the four summaries and needs the same budget.
        deadline = app._Deadline()
        db_summaries = _scan_available_databases(
            db_client,
            home_ids_by_comp,
            db_name=db_name,
            limit_per_home=limit_per_home,
            max_db_homes=max_db_homes,
            max_total_databases=max_total_databases,
            deadline=deadline,
        )

        # Aggregation structures for summary + per-DB details
        items: list[ProtectedDatabaseBackupDestinationItem] = []
        counts_by_type: dict[str, int] = {}
        db_names_by_type: dict[str, list[str]] = {}
        unconfigured = 0
        unconfigured_names: list[str] = []
        has_backups_names: list[str] = []

        get_db = db_client.get_database
        list_bk = db_client.list_backups

        # Overlapping compartment scopes can return the same database more than once.
        # De-duplicating here rather than at the end is what keeps the response
        # self-consistent: the tail de-dupe only rewrote `items`, leaving
        # total_databases, unconfigured_count and counts_by_destination_type still
        # counting every occurrence, so the counts did not add up to the list beside
        # them. Skipping the repeat before any of them is touched fixes all of them at
        # once.
        seen_database_ids: set[str] = set()

        # Iterate each DB summary, fetch full DB to inspect backup config and infer destinations
        for s in db_summaries:
            if deadline.reached():
                break
            try:
                sid = _get(s, "id")
                if not sid:
                    continue
                if sid in seen_database_ids:
                    continue
                db_name_val = _get(s, "db_name", "dbName")

                d_dict, dest_types, dest_ids = _backup_destinations_for(s, get_database=get_db)
                # Marked seen only once its config is read. Marked before, a failed read
                # still counted toward total_databases while appearing in no other count
                # or list, and a later duplicate of it was skipped instead of retried.
                seen_database_ids.add(sid)

                auto_enabled = _is_auto_backup_enabled(d_dict)
                # Configured strictly when auto-backup is enabled
                configured = bool(auto_enabled)
                status = "CONFIGURED" if configured else "UNCONFIGURED"
                last_backup_time = None
                # The label this database appears under in every name list below.
                name_for_lists = db_name_val or sid

                # Costs an extra call per database, so it is opt-in.
                if include_last_backup_time:
                    try:
                        last_backup_time, had_backups = _latest_backup_time(
                            sid, list_backups=list_bk
                        )
                        if had_backups:
                            has_backups_names.append(name_for_lists)
                    except Exception:
                        pass

                # Aggregate summary counters and name lists by status/destination
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


        items = sorted(
            items,
            key=lambda it: (
                _dest_rank(it.destination_types),
                (it.db_name or ""),
            ),
        )

        db_names_by_type = {k: _sorted_keep(v) for k, v in db_names_by_type.items()}
        unconfigured_names = _uniq_sorted(unconfigured_names)
        has_backups_names = _uniq_sorted(has_backups_names)

        return ProtectedDatabaseBackupDestinationSummary(
            compartment_id=compartment_id,
            region=region,
            total_databases=len(seen_database_ids),
            unconfigured_count=unconfigured,
            counts_by_destination_type=counts_by_type,
            db_names_by_destination_type=db_names_by_type,
            unconfigured_db_names=unconfigured_names,
            has_backups_db_names=has_backups_names,
            items=items,
            truncated=deadline.expired,
        )
    except Exception as e:
        logger.error(f"Error in summarize_protected_database_backup_destination tool: {e}")
        raise
