"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint, request
from monitoring_data import ALARMS, METRIC_DATA, METRICS

monitoring_bp = Blueprint("monitoring", __name__, url_prefix="/20180401")


@monitoring_bp.route("/alarms", methods=["GET"])
def list_alarms():
    compartment_id = request.args.get("compartmentId")
    items = ALARMS
    if compartment_id:
        items = [a for a in items if a.get("compartmentId") == compartment_id]

    return oci_res(items)


@monitoring_bp.route("/metrics", methods=["GET"])
def list_metrics():
    compartment_id = request.args.get("compartmentId")
    items = METRICS
    if compartment_id:
        items = [m for m in items if m.get("compartmentId") == compartment_id]

    return oci_res(items)


@monitoring_bp.route("/metrics/actions/summarizeMetricsData", methods=["POST"])
def summarize_metrics_data():
    # In a real scenario, we'd parse the body for query, start/end time, etc.
    # For mock, we just return static data.
    return oci_res(METRIC_DATA)
