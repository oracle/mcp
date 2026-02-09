"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint, jsonify, request
from migration_data import MIGRATIONS

# OCI Cloud Migrations API version base path (approximate)
migration_bp = Blueprint("migration", __name__, url_prefix="/20220919")


@migration_bp.route("/migrations", methods=["GET"])
def list_migrations():
    compartment_id = request.args.get("compartmentId")
    lifecycle_state = request.args.get("lifecycleState")
    limit = request.args.get("limit", type=int)

    items = MIGRATIONS

    if compartment_id:
        items = [i for i in items if i.get("compartmentId") == compartment_id]
    if lifecycle_state:
        items = [i for i in items if i.get("lifecycleState") == lifecycle_state]
    if limit is not None:
        items = items[:limit]

    # list_migrations returns a collection with `items`
    return oci_res({"items": items})


@migration_bp.route("/migrations/<migration_id>", methods=["GET"])
def get_migration(migration_id):
    mig = next((i for i in MIGRATIONS if i.get("id") == migration_id), None)
    if not mig:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(mig)
