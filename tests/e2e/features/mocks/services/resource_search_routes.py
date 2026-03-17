"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint, request
from resource_search_data import RESOURCE_TYPES, RESOURCES

# OCI Resource Search API version base path
resource_search_bp = Blueprint("resource_search", __name__, url_prefix="/20180409")


def _apply_limit(items):
    try:
        limit = request.args.get("limit")
        if limit is not None:
            lim = int(limit)
            if lim >= 0:
                return items[:lim]
    except Exception:
        pass
    return items


@resource_search_bp.route("/resources", methods=["POST"])
def search_resources():
    body = request.get_json(silent=True) or {}

    # OCI SDK typically sends camelCase searchDetails
    details = body.get("searchDetails") or body.get("search_details") or {}

    results = RESOURCES

    # Handle FreeText vs Structured queries
    if (details.get("type") or details.get("Type")) in ("FreeText", "FREETEXT"):
        text = details.get("text", "") or details.get("Text", "")
        if text:
            t = str(text).lower()
            results = [
                r
                for r in RESOURCES
                if t in str(r.get("displayName", "")).lower()
                or t in str(r.get("identifier", "")).lower()
                or t in str(r.get("resourceType", "")).lower()
            ]
    else:
        query = details.get("query", "") or details.get("Query", "")
        q = str(query)
        # Very simple/forgiving parsing to support the queries used by the tools
        # compartmentId filter
        if "compartmentId" in q:
            # extract between compartmentId = '...'
            try:
                part = q.split("compartmentId", 1)[1]
                comp_val = part.split("'", 2)[1]
                results = [r for r in results if r.get("compartmentId") == comp_val]
            except Exception:
                pass
        # displayName =~ '...'
        if "displayName" in q and "=~" in q:
            try:
                disp_val = q.split("displayName", 1)[1].split("'", 2)[1]
                dv = disp_val.lower()
                results = [
                    r for r in results if dv in str(r.get("displayName", "")).lower()
                ]
            except Exception:
                pass
        # query {resource_type} resources
        if q.strip().lower().startswith("query ") and " resources" in q.lower():
            try:
                after_query = q.strip()[len("query ") :]  # noqa
                resource_type = after_query.split(" ", 1)[0].strip().lower()
                results = [
                    r
                    for r in results
                    if str(r.get("resourceType", "")).lower() == resource_type
                ]
            except Exception:
                pass

    # Apply limit via query param if present
    results = _apply_limit(results)

    # Shape must match OCI ResourceSummaryCollection
    return oci_res({"items": results})


@resource_search_bp.route("/resourceTypes", methods=["GET"])
def list_resource_types():
    items = _apply_limit(RESOURCE_TYPES)
    # Shape: list of ResourceType objects
    return oci_res(items)
