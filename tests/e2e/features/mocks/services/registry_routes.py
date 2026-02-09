"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint, jsonify, request
from registry_data import CONTAINER_REPOSITORIES

# OCI Artifacts (Container Registry) API base path
registry_bp = Blueprint("registry", __name__, url_prefix="/20160918")


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


@registry_bp.route("/container/repositories", methods=["GET"])
def list_container_repositories():
    # Accept common filters (ignored in mock): compartmentId, namespace, displayName, page, limit
    items = _apply_limit(CONTAINER_REPOSITORIES)
    # Shape must match ContainerRepositoryCollection
    return oci_res({"items": items})


@registry_bp.route("/container/repositories/<repository_id>", methods=["GET"])
def get_container_repository(repository_id):
    repo = next((r for r in CONTAINER_REPOSITORIES if r["id"] == repository_id), None)
    return (
        oci_res(repo) if repo else (jsonify({"code": "NotAuthorizedOrNotFound"}), 404)
    )
