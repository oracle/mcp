"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from faaas_data import (
    FUSION_ENVIRONMENT_FAMILIES,
    FUSION_ENVIRONMENT_STATUSES,
    FUSION_ENVIRONMENTS,
)
from flask import Blueprint, jsonify, request

# Fusion Applications public base path follows service's versioning; using 20211201
faaas_bp = Blueprint("faaas", __name__, url_prefix="/20211201")


@faaas_bp.route("/fusionEnvironmentFamilies", methods=["GET"])
def list_fusion_environment_families():
    # Filters: compartmentId, displayName, lifecycleState, page
    compartment_id = request.args.get("compartmentId")
    display_name = request.args.get("displayName")
    lifecycle_state = request.args.get("lifecycleState")

    items = FUSION_ENVIRONMENT_FAMILIES

    if compartment_id:
        items = [i for i in items if i.get("compartmentId") == compartment_id]
    if display_name:
        items = [i for i in items if i.get("displayName") == display_name]
    if lifecycle_state:
        items = [i for i in items if i.get("lifecycleState") == lifecycle_state]

    # Emulate collection shape with `items` key
    return oci_res({"items": items})


@faaas_bp.route("/fusionEnvironments", methods=["GET"])
def list_fusion_environments():
    compartment_id = request.args.get("compartmentId")
    family_id = request.args.get("fusionEnvironmentFamilyId")
    display_name = request.args.get("displayName")
    lifecycle_state = request.args.get("lifecycleState")

    items = FUSION_ENVIRONMENTS

    if compartment_id:
        items = [i for i in items if i.get("compartmentId") == compartment_id]
    if family_id:
        items = [i for i in items if i.get("fusionEnvironmentFamilyId") == family_id]
    if display_name:
        items = [i for i in items if i.get("displayName") == display_name]
    if lifecycle_state:
        items = [i for i in items if i.get("lifecycleState") == lifecycle_state]

    return oci_res({"items": items})


@faaas_bp.route("/fusionEnvironments/<fusion_environment_id>", methods=["GET"])
def get_fusion_environment(fusion_environment_id):
    env = next((i for i in FUSION_ENVIRONMENTS if i.get("id") == fusion_environment_id), None)
    if not env:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(env)


@faaas_bp.route("/fusionEnvironments/<fusion_environment_id>/status", methods=["GET"])
def get_fusion_environment_status(fusion_environment_id):
    status = next(
        (i for i in FUSION_ENVIRONMENT_STATUSES if i.get("fusionEnvironmentId") == fusion_environment_id),
        None,
    )
    if not status:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(status)
