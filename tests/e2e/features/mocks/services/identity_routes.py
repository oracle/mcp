"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint, jsonify, request
from identity_data import ADS, COMPARTMENTS, REGION_SUBSCRIPTIONS, TENANCY, USER

identity_bp = Blueprint("identity", __name__, url_prefix="/20160918")


@identity_bp.route("/availabilityDomains", methods=["GET"])
def list_ads():
    # OCI expects compartmentId but we ignore filtering in mock
    return oci_res(ADS)


@identity_bp.route("/compartments/<compartment_id>", methods=["GET"])
def get_compartment(compartment_id):
    compartments = COMPARTMENTS + [TENANCY]
    compartment = next((i for i in compartments if i["id"] == compartment_id), None)
    return oci_res(compartment) if compartment else (jsonify({"code": "NotAuthorizedOrNotFound"}), 404)


@identity_bp.route("/compartments", methods=["GET"])
def list_compartments():
    parent_id = request.args.get("compartmentId")

    items = COMPARTMENTS
    if parent_id:
        items = [c for c in COMPARTMENTS if c.get("compartmentId") == parent_id]

    return oci_res(items)


@identity_bp.route("/tenancies/<tenancy_id>", methods=["GET"])
def get_tenancy(tenancy_id):
    if TENANCY.get("id") == tenancy_id:
        return oci_res(TENANCY)
    return jsonify({"code": "NotAuthorizedOrNotFound"}), 404


@identity_bp.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    if USER.get("id") == user_id:
        return oci_res(USER)
    return jsonify({"code": "NotAuthorizedOrNotFound"}), 404


@identity_bp.route("/tenancies/<tenancy_id>/regionSubscriptions", methods=["GET"])
def list_region_subscriptions(tenancy_id):
    # Filter by tenancyId if passed
    tenancy_id = request.args.get("tenancyId")
    if tenancy_id and TENANCY.get("id") != tenancy_id:
        return oci_res([])
    return oci_res(REGION_SUBSCRIPTIONS)
