"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint
from identity_data import ADS

identity_bp = Blueprint("identity", __name__, url_prefix="/20160918")


@identity_bp.route("/20160918/availabilityDomains", methods=["GET"])
def list_ads():
    return oci_res(ADS)
