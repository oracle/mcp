"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint
from networking_data import SUBNETS

networking_bp = Blueprint("networking", __name__, url_prefix="/20160918")


@networking_bp.route("/subnets", methods=["GET"])
def list_subnets():
    return oci_res(SUBNETS)
