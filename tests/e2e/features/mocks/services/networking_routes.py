"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint, jsonify, request
from networking_data import (
    NETWORK_SECURITY_GROUPS,
    SECURITY_LISTS,
    SUBNETS,
    VCNS,
    VNICS,
)

networking_bp = Blueprint("networking", __name__, url_prefix="/20160918")


@networking_bp.route("/vcns", methods=["GET"])
def list_vcns():
    compartment_id = request.args.get("compartmentId")
    items = VCNS
    if compartment_id:
        items = [i for i in items if i.get("compartmentId") == compartment_id]
    return oci_res(items)


@networking_bp.route("/vcns/<vcn_id>", methods=["GET"])
def get_vcn(vcn_id):
    vcn = next((v for v in VCNS if v["id"] == vcn_id), None)
    return oci_res(vcn) if vcn else (jsonify({"code": "NotAuthorizedOrNotFound"}), 404)


@networking_bp.route("/subnets", methods=["GET"])
def list_subnets():
    compartment_id = request.args.get("compartmentId")
    vcn_id = request.args.get("vcnId")
    items = SUBNETS
    if compartment_id:
        items = [i for i in items if i.get("compartmentId") == compartment_id]
    if vcn_id:
        items = [i for i in items if i.get("vcnId") == vcn_id]
    return oci_res(items)


@networking_bp.route("/subnets/<subnet_id>", methods=["GET"])
def get_subnet(subnet_id):
    subnet = next((s for s in SUBNETS if s["id"] == subnet_id), None)
    return (
        oci_res(subnet)
        if subnet
        else (jsonify({"code": "NotAuthorizedOrNotFound"}), 404)
    )


@networking_bp.route("/securityLists", methods=["GET"])
def list_security_lists():
    compartment_id = request.args.get("compartmentId")
    vcn_id = request.args.get("vcnId")
    items = SECURITY_LISTS
    if compartment_id:
        items = [i for i in items if i.get("compartmentId") == compartment_id]
    if vcn_id:
        items = [i for i in items if i.get("vcnId") == vcn_id]
    return oci_res(items)


@networking_bp.route("/securityLists/<security_list_id>", methods=["GET"])
def get_security_list(security_list_id):
    sl = next((s for s in SECURITY_LISTS if s["id"] == security_list_id), None)
    return oci_res(sl) if sl else (jsonify({"code": "NotAuthorizedOrNotFound"}), 404)


@networking_bp.route("/networkSecurityGroups", methods=["GET"])
def list_network_security_groups():
    compartment_id = request.args.get("compartmentId")
    vcn_id = request.args.get("vcnId")
    items = NETWORK_SECURITY_GROUPS
    if compartment_id:
        items = [i for i in items if i.get("compartmentId") == compartment_id]
    if vcn_id:
        items = [i for i in items if i.get("vcnId") == vcn_id]
    return oci_res(items)


@networking_bp.route("/networkSecurityGroups/<nsg_id>", methods=["GET"])
def get_network_security_group(nsg_id):
    nsg = next((n for n in NETWORK_SECURITY_GROUPS if n["id"] == nsg_id), None)
    return oci_res(nsg) if nsg else (jsonify({"code": "NotAuthorizedOrNotFound"}), 404)


@networking_bp.route("/vnics/<vnic_id>", methods=["GET"])
def get_vnic(vnic_id):
    vnic = next((v for v in VNICS if v["id"] == vnic_id), None)
    return (
        oci_res(vnic) if vnic else (jsonify({"code": "NotAuthorizedOrNotFound"}), 404)
    )
