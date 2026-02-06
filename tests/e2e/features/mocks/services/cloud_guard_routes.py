"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from cloud_guard_data import PROBLEMS
from flask import Blueprint, jsonify, request

# Cloud Guard API version base path
cloud_guard_bp = Blueprint("cloud_guard", __name__, url_prefix="/20200131")


@cloud_guard_bp.route("/problems", methods=["GET"])
def list_problems():
    # Accept typical Cloud Guard filters
    risk_level = request.args.get("riskLevel")
    lifecycle_state = request.args.get("lifecycleState")
    detector_rule_ids = request.args.getlist("detectorRuleIdList")
    limit = request.args.get("limit", type=int)

    items = PROBLEMS.copy()

    if risk_level:
        items = [p for p in items if p.get("riskLevel") == risk_level]
    if lifecycle_state:
        items = [p for p in items if p.get("lifecycleState") == lifecycle_state]
    if detector_rule_ids:
        items = [p for p in items if p.get("detectorRuleId") in set(detector_rule_ids)]
    if limit is not None:
        items = items[:limit]

    # Cloud Guard ListProblems returns a ProblemCollection with `items`
    return oci_res({"items": items})


@cloud_guard_bp.route("/problems/<problem_id>", methods=["GET"])
def get_problem(problem_id):
    prob = next((p for p in PROBLEMS if p.get("id") == problem_id), None)
    if not prob:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(prob)
