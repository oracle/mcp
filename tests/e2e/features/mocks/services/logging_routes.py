"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint, jsonify, request
from logging_data import LOG_GROUPS, LOGS

# OCI Logging Management API version base path
logging_bp = Blueprint("logging", __name__, url_prefix="/20200531")


@logging_bp.route("/logGroups", methods=["GET"])
def list_log_groups():
    compartment_id = request.args.get("compartmentId")
    limit = request.args.get("limit", type=int)

    items = LOG_GROUPS
    if compartment_id:
        items = [i for i in items if i.get("compartmentId") == compartment_id]
    if limit is not None:
        items = items[:limit]

    return oci_res(items)


@logging_bp.route("/logGroups/<log_group_id>", methods=["GET"])
def get_log_group(log_group_id):
    lg = next((i for i in LOG_GROUPS if i.get("id") == log_group_id), None)
    if not lg:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(lg)


@logging_bp.route("/logGroups/<log_group_id>/logs", methods=["GET"])
def list_logs(log_group_id):
    limit = request.args.get("limit", type=int)

    items = LOGS
    if log_group_id:
        items = [i for i in items if i.get("logGroupId") == log_group_id]
    if limit is not None:
        items = items[:limit]

    return oci_res(items)


@logging_bp.route("/logGroups/<log_group_id>/logs/<log_id>", methods=["GET"])
def get_log(log_group_id, log_id):
    match = next((i for i in LOGS if i.get("id") == log_id), None)
    if not match:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    if log_group_id and match.get("logGroupId") != log_group_id:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(match)
