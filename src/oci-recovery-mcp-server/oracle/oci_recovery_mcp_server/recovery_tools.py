"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Recovery Service resources: protected databases, protection policies, recovery
service subnets, backups, restore work requests, metrics, service limits and the
tenancy's subscribed regions -- the list and get tool for each.
"""

import re
import uuid
from typing import Annotated, Any, Optional

import oci
from oci.monitoring.models import SummarizeMetricsDataDetails

# Database Service models and mappers
from oracle.oci_recovery_mcp_server.models import (
    Backup,
    BackupSummary,
    ProtectedDatabase,
    ProtectedDatabaseSummary,
    ProtectionPolicy,
    RecoveryServiceSubnet,
    WorkRequest,
    map_backup,
    map_backup_summary,
    map_protected_database,
    map_protected_database_summary,
    map_protection_policy,
    map_recovery_service_subnet,
    map_recovery_service_subnet_details,
    map_work_request,
)

from . import (
    auth,
    clients,
    compartments,
    regions,
    telemetry,
)
from .logging_setup import logger
from .app import mcp, _READ_ONLY_TOOL


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
        "Canonical OCI region (e.g., us-ashburn-1) to check limits in. Defaults to the "
        "server's configured region.",
    ] = None,
    opc_request_id: Annotated[Optional[str], "Unique identifier for the request"] = None,
) -> dict:
    """
    Returns resource availability from OCI Limits API for:
      - autonomous-recovery-service / protected-database-backup-storage-gb
      - autonomous-recovery-service / protected-database-count

    Scope/region behavior:
      - Compartment is always the tenancy OCID from server config; `compartment_id` is
        accepted only for backward compatibility. Service limits are set per tenancy.
      - `region` is honored when given, and falls back to the server's configured
        region. Limits differ per region, so answering for a region the caller did not
        ask about would be wrong rather than merely imprecise -- if neither source
        yields one, this raises instead of guessing.

    API shape corresponds to:
      GET /20190729/services/autonomous-recovery-service/limits/<limitName>/resourceAvailability
    """
    try:
        request_id = uuid.uuid4().hex
        resolved_compartment_id = auth.get_tenancy()
        # No hard-coded fallback: limits are per region, so silently answering for
        # us-ashburn-1 when the region could not be resolved reports another region's
        # numbers as this one's. A caller can act on a wrong number; they cannot act on
        # one they were never given.
        # A blank argument is "not provided", not "provided as empty", so it falls
        # through to the configured region rather than erroring.
        target_region = (region or "").strip() or (auth._effective_region() or "").strip()
        if not target_region:
            raise ValueError(
                "No OCI region could be determined for the limits lookup. Pass `region`, "
                "or set OCI_REGION (HTTP) or a region on the configured OCI profile (stdio)."
            )
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
        "Lists every region this tenancy is subscribed to, with each subscription's "
        "status, via IdentityClient.list_region_subscriptions(). Use it to discover "
        "which regions the other tools can be pointed at. Read live from IAM on every "
        "call, so the caller's own permissions decide the answer."
    )
)
@telemetry._tool_logger("fetch_regions_subscribed")
def fetch_regions_subscribed(
    tenancy_id: Annotated[
        Optional[str],
        "OCID of the tenancy, used only to label the result. Region subscriptions are "
        "tenancy-wide, so this does not narrow the lookup. Defaults to the server's tenancy.",
    ] = None,
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
