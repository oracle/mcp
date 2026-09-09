"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Database Service resources -- DB systems, DB homes and databases. They are read
here only to locate what Recovery Service protects; nothing in this file changes a
Database Service resource.
"""

import logging
import uuid
from typing import Annotated, Optional

import oci

# Database Service models and mappers
from oracle.oci_recovery_mcp_server.models import (
    Database,
    DatabaseHome,
    DatabaseHomeSummary,
    DatabaseSummary,
    DbSystem,
    DbSystemSummary,
    map_database,
    map_database_home,
    map_database_home_summary,
    map_database_summary,
    map_db_backup_config,
    map_db_system,
    map_db_system_summary,
)

from . import (
    auth,
    clients,
    compartments,
    logging_setup,
    telemetry,
)
from .logging_setup import logger
from .app import mcp, _READ_ONLY_TOOL


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
