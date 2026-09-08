"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Compartment discovery, subtree expansion and name/OCID resolution.

Tools take a compartment as an OCID or a display name and may be asked to
include the whole subtree beneath it. Both need the tenancy's accessible
compartment listing, which is one Identity scan per caller and is therefore
cached; the tree walking on top of it is local.
"""

import json
import logging
import os
import time
import uuid
from typing import Annotated, Any, Optional

import oci

from . import auth, cache, clients, logging_setup


def list_all_compartments_internal(only_one_page: bool, limit=100):
    """Internal function to get List all compartments in a tenancy"""
    # Use IdentityClient to list all accessible ACTIVE compartments and include the root tenancy
    identity_client = clients.get_identity_client()
    response = identity_client.list_compartments(
        compartment_id=auth.get_tenancy(),
        compartment_id_in_subtree=True,
        access_level="ACCESSIBLE",
        lifecycle_state="ACTIVE",
        limit=limit,
    )
    compartments = response.data
    # Also include the tenancy itself
    compartments.append(identity_client.get_compartment(compartment_id=auth.get_tenancy()).data)
    if only_one_page:  # limiting the number of items returned
        return compartments
    # Manual pagination loop
    while response.has_next_page:
        response = identity_client.list_compartments(
            compartment_id=auth.get_tenancy(),
            compartment_id_in_subtree=True,
            access_level="ACCESSIBLE",
            lifecycle_state="ACTIVE",
            page=response.next_page,
            limit=limit,
        )
        compartments.extend(response.data)
    return compartments


_COMPARTMENT_CACHE: dict[str, Any] = {
    "ttl_seconds": int(os.getenv("ORACLE_MCP_COMPARTMENT_CACHE_TTL_SECONDS", "300")),
    # entries: dict["<tenant_key>|<caller_key>" -> {"items": list[Any], "fetched_at": float}]
    "entries": {},
}


def _list_all_compartments_cached(*, request_id: Optional[str] = None) -> list[Any]:
    """
    Return all accessible ACTIVE compartments in the tenancy (plus root tenancy)
    with a small in-process TTL cache to avoid repeated Identity scans.

    The cache is keyed by tenant AND caller: the listing is fetched with
    access_level="ACCESSIBLE", so it contains exactly the compartments the calling
    identity may see. Keying it by tenant alone would let one user's compartment
    tree be served to a differently-authorized user in the same tenancy.

    NOTE:
    - OCI CLI `oci iam compartment list --compartment-id <root>` returns ONLY direct children.
    - For our use-case (expand subtree), we list the full subtree using:
        list_compartments(compartment_id_in_subtree=True, access_level="ACCESSIBLE")
      and then build a parent->children index locally to BFS the descendants.
    """
    now = time.time()
    ttl = float(_COMPARTMENT_CACHE.get("ttl_seconds") or 300)
    entries = _COMPARTMENT_CACHE.setdefault("entries", {})
    cache_key = f"{cache._tenant_cache_key()}|{cache._caller_cache_key()}"
    cached = cache._cache_get(entries, cache_key, ttl=ttl, now=now)

    if cached and cached.get("items"):
        return cached["items"]  # type: ignore[return-value]

    rid = request_id or uuid.uuid4().hex

    # Refresh cache
    try:
        comps = list_all_compartments_internal(False)

        # Normalize shape and ensure we always have the root tenancy in the list.
        # list_all_compartments_internal already tries to append tenancy, but we make it robust.
        tenancy_id = auth.get_tenancy()
        seen_ids: set[str] = set()
        normalized: list[Any] = []

        for c in comps or []:
            try:
                cid = getattr(c, "id", None) or getattr(c, "ocid", None)
            except Exception:
                cid = None
            if not cid or cid in seen_ids:
                continue
            seen_ids.add(cid)
            normalized.append(c)

        if tenancy_id and tenancy_id not in seen_ids:
            try:
                identity_client = clients.get_identity_client(request_id=rid)
                t = identity_client.get_compartment(compartment_id=tenancy_id).data
                normalized.append(t)
            except Exception:
                pass

        comps = normalized
    except Exception as e:
        # If identity listing fails, fall back to empty (callers will handle)
        logging_setup._log_event(
            "compartment_cache_refresh_failed",
            request_id=rid,
            tool=None,
            phase="error",
            payload={"error": str(e)},
            level=logging.WARNING,
        )
        comps = []

    cache._cache_put(entries, cache_key, {"items": comps, "fetched_at": now}, ttl=ttl, now=now)
    return comps


def _build_children_index(compartments: list[Any]) -> dict[str, list[str]]:
    """
    Build a parent->children map from identity compartment objects.

    Identity compartment model uses:
      - id: compartment OCID
      - compartment_id: parent OCID (called "compartment-id" in OCI CLI JSON)
    """
    children: dict[str, list[str]] = {}
    for c in compartments or []:
        try:
            cid = getattr(c, "id", None) or getattr(c, "ocid", None)
            pid = (
                getattr(c, "compartment_id", None)
                or getattr(c, "compartmentId", None)
                or getattr(c, "parent_id", None)
                or getattr(c, "parentId", None)
            )
            if not cid or not pid:
                continue
            children.setdefault(pid, []).append(cid)
        except Exception:
            continue
    return children


def _expand_compartment_scope(
    root_compartment_id: str,
    *,
    include_child_compartments: bool,
    request_id: Optional[str] = None,
) -> list[str]:
    """
    Expand a root compartment into a list including all descendant compartments (BFS)
    when include_child_compartments=True.

    Robustness:
    - Primary approach: use cached full-subtree identity listing (compartment_id_in_subtree=True)
      and build a parent->children index locally.
    - Fallback: if that yields only the root (common in restricted IAM environments),
      do a direct-children crawl using IdentityClient.list_compartments(compartment_id=<pid>)
      recursively.

    Safety:
    - Cap max compartments scanned via ORACLE_MCP_MAX_COMPARTMENTS_IN_SCOPE (default 200).
    """
    if not include_child_compartments:
        return [root_compartment_id]

    cap = int(os.getenv("ORACLE_MCP_MAX_COMPARTMENTS_IN_SCOPE", "200"))
    rid = request_id or uuid.uuid4().hex

    # ---------------- Primary: cached full-subtree listing ----------------
    try:
        comps = _list_all_compartments_cached(request_id=rid)
        children_index = _build_children_index(comps)

        scope: list[str] = []
        seen: set[str] = set()
        queue: list[str] = [root_compartment_id]

        while queue:
            cid = queue.pop(0)
            if cid in seen:
                continue
            seen.add(cid)
            scope.append(cid)

            if cap and len(scope) >= cap:
                logging_setup._log_event(
                    "compartment_scope_capped",
                    request_id=rid,
                    tool=None,
                    phase="warn",
                    payload={"root": root_compartment_id, "cap": cap},
                    level=logging.WARNING,
                )
                return scope

            for child in children_index.get(cid, []) or []:
                if child not in seen:
                    queue.append(child)

        # If we found at least one child, we're done.
        if len(scope) > 1:
            return scope
    except Exception:
        # Fall through to direct-children crawl fallback
        pass

    # ---------------- Fallback: direct-children crawl ----------------
    try:
        identity_client = clients.get_identity_client(request_id=rid)

        scope: list[str] = []
        seen: set[str] = set()
        queue: list[str] = [root_compartment_id]

        while queue:
            pid = queue.pop(0)
            if pid in seen:
                continue
            seen.add(pid)
            scope.append(pid)

            if cap and len(scope) >= cap:
                logging_setup._log_event(
                    "compartment_scope_capped",
                    request_id=rid,
                    tool=None,
                    phase="warn",
                    payload={"root": root_compartment_id, "cap": cap},
                    level=logging.WARNING,
                )
                break

            next_page = None
            while True:
                resp = identity_client.list_compartments(
                    compartment_id=pid,
                    access_level="ACCESSIBLE",
                    lifecycle_state="ACTIVE",
                    limit=1000,
                    page=next_page,
                )
                for c in resp.data or []:
                    cid = getattr(c, "id", None) or getattr(c, "ocid", None)
                    if cid and cid not in seen:
                        queue.append(cid)

                has_next = bool(getattr(resp, "has_next_page", False))
                next_page = getattr(resp, "next_page", None) if has_next else None
                if not has_next:
                    break

        return scope
    except Exception:
        # Final fallback: only root
        return [root_compartment_id]


def _compartment_ids_for_tool(
    root_compartment_id: str,
    *,
    fetch_for_child_compartment: bool,
    request_id: Optional[str] = None,
) -> list[str]:
    """
    Helper used by tools to decide compartment scope.

    Behavior:
    - fetch_for_child_compartment=False  -> [root_compartment_id]
    - fetch_for_child_compartment=True   -> full subtree (including root)

    IMPORTANT:
    - We should avoid tool->tool style calls from inside server handlers.
    - Instead, we reuse the underlying internal helper `_expand_compartment_scope(...)`
      which implements robust subtree expansion with caching + fallback.
    """
    resolved_root = _resolve_compartment_id(root_compartment_id)

    if not fetch_for_child_compartment:
        return [resolved_root]

    rid = request_id or uuid.uuid4().hex

    try:
        ids = _expand_compartment_scope(
            resolved_root,
            include_child_compartments=True,
            request_id=rid,
        )
        if isinstance(ids, list) and ids:
            return [str(x) for x in ids if x]
    except Exception:
        pass

    # Final fallback: only root
    return [resolved_root]


def _fetch_db_home_ids_for_compartment(compartment_id: str, region: Optional[str] = None) -> list[str]:
    """
    Helper: enumerate DB Home OCIDs in a compartment.
    Used when a tool needs a db_home_id but the caller omitted it.
    Returns a list of DB Home OCIDs (may be empty).
    """
    try:
        client = clients.get_database_client(region)
        resp = client.list_db_homes(compartment_id=compartment_id)
        data = resp.data
        # Normalize list shape (SDK may use .items or a raw list)
        raw_list = getattr(data, "items", data)
        raw_list = raw_list if isinstance(raw_list, list) else [raw_list] if raw_list is not None else []
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


def _looks_like_ocid(value: Optional[str]) -> bool:
    """Report whether a value is shaped like an OCID rather than a display name."""
    return bool(value and isinstance(value, str) and value.strip().lower().startswith("ocid1."))


def _resolve_compartment_id(
    compartment_input: Optional[str],
    *,
    default_to_tenancy: bool = False,
) -> str:
    """
    Accept either a compartment OCID or a compartment display name and return an OCID.

    - If an OCID is provided, return it unchanged.
    - If a display name is provided, resolve it using get_compartment_by_name().
    - If omitted and default_to_tenancy is True, return the tenancy OCID.
    """
    if compartment_input is None:
        if default_to_tenancy:
            return auth.get_tenancy()
        raise ValueError("compartment_id is required.")

    candidate = compartment_input.strip()
    if not candidate:
        if default_to_tenancy:
            return auth.get_tenancy()
        raise ValueError("compartment_id cannot be empty.")

    if _looks_like_ocid(candidate):
        return candidate

    compartment = get_compartment_by_name(candidate)
    if compartment is None:
        raise ValueError(f"Compartment '{candidate}' not found.")

    resolved_id = getattr(compartment, "id", None)
    if not resolved_id:
        raise ValueError(f"Unable to resolve OCID for compartment '{candidate}'.")
    return resolved_id


def fetch_child_compartments(
    compartment_id: Annotated[str, "Root compartment OCID to expand (included in results)."],
    include_self: Annotated[
        bool, "When true (default), include the given compartment_id in the output."
    ] = True,
    limit: Annotated[
        Optional[int],
        "Optional cap on how many compartmentIds to return (defaults to ORACLE_MCP_MAX_COMPARTMENTS_IN_SCOPE or 200).",
    ] = None,
) -> dict:
    """
    Internal helper that expands a root compartment to its subtree.

    Returns a simple JSON-like dict:
      {
        "rootCompartmentId": "<ocid>",
        "total": N,
        "compartmentIds": ["<ocid1>", "<ocid2>", ...]
      }

    Implementation notes:
    - OCI CLI `oci iam compartment list --compartment-id <X>` returns ONLY direct children.
    - This tool returns the full subtree under <X>.
    - Some environments do not allow `compartment_id_in_subtree=True` even with ACCESSIBLE.
      If subtree listing yields no children for the root, we fall back to a direct-children crawl.
    """
    request_id = uuid.uuid4().hex
    compartment_id = _resolve_compartment_id(compartment_id)
    identity_client = clients.get_identity_client(request_id=request_id)

    # 1) Try fast path: use our cached full-subtree listing and BFS it.
    scope = _expand_compartment_scope(
        compartment_id,
        include_child_compartments=True,
        request_id=request_id,
    )

    # 2) If subtree expansion produced only the root, fall back to direct-children crawl.
    # This matches the CLI semantics and works even when subtree listing is restricted.
    if len(scope) <= 1:
        cap = limit
        if cap is None:
            cap = int(os.getenv("ORACLE_MCP_MAX_COMPARTMENTS_IN_SCOPE", "200"))

        queue: list[str] = [compartment_id]
        seen: set[str] = set()
        out: list[str] = []

        while queue:
            pid = queue.pop(0)
            if pid in seen:
                continue
            seen.add(pid)
            out.append(pid)

            if cap and len(out) >= cap:
                logging_setup._log_event(
                    "compartment_scope_capped",
                    request_id=request_id,
                    tool="fetch_child_compartments",
                    phase="warn",
                    payload={"root": compartment_id, "cap": cap},
                    level=logging.WARNING,
                )
                break

            next_page = None
            while True:
                resp = identity_client.list_compartments(
                    compartment_id=pid,
                    access_level="ACCESSIBLE",
                    lifecycle_state="ACTIVE",
                    limit=1000,
                    page=next_page,
                )
                children = resp.data or []
                for c in children:
                    cid = getattr(c, "id", None) or getattr(c, "ocid", None)
                    if cid and cid not in seen:
                        queue.append(cid)

                has_next = bool(getattr(resp, "has_next_page", False))
                next_page = getattr(resp, "next_page", None) if has_next else None
                if not has_next:
                    break

        scope = out

    # include_self behavior
    if not include_self:
        scope = [x for x in scope if x != compartment_id]

    # final cap enforcement (also applies to fast-path)
    cap2 = limit
    if cap2 is None:
        cap2 = int(os.getenv("ORACLE_MCP_MAX_COMPARTMENTS_IN_SCOPE", "200"))
    if cap2 and len(scope) > cap2:
        scope = scope[:cap2]

    return {
        "rootCompartmentId": compartment_id,
        "total": len(scope),
        "compartmentIds": scope,
    }


def get_compartment_by_name_tool(
    name: Annotated[
        str,
        "Compartment display name to search for (case-insensitive). Searches all "
        "accessible ACTIVE compartments in the tenancy, including the root tenancy.",
    ],
) -> str:
    """Internal helper to return a compartment matching the provided name."""
    compartment = get_compartment_by_name(name)
    if compartment:
        return str(compartment)
    else:
        return json.dumps({"error": f"Compartment '{name}' not found."})
