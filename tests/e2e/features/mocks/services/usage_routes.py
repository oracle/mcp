"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint
from usage_data import SUMMARIZED_USAGES

usage_bp = Blueprint("usage", __name__, url_prefix="/20200107")


@usage_bp.route("/usage", methods=["POST"])
def get_summarized_usage():
    return oci_res({"items": SUMMARIZED_USAGES})
