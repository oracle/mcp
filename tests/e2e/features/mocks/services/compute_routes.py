"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import uuid
from datetime import datetime, timezone

from _common import oci_res
from compute_data import IMAGES, INSTANCES, VNIC_ATTACHMENTS
from flask import Blueprint, jsonify, request

compute_bp = Blueprint("compute", __name__, url_prefix="/20160918")


@compute_bp.route("/instances", methods=["GET"])
def list_instances():
    # Filters usually passed via query params: compartmentId, lifecycleState
    return oci_res(INSTANCES)


@compute_bp.route("/instances", methods=["POST"])
def launch_instance():
    data = request.json
    new_id = f"ocid1.instance.oc1..{uuid.uuid4()}"
    new_inst = {
        "id": new_id,
        "compartmentId": data.get("compartmentId"),
        "displayName": data.get("displayName", "instance-adhoc"),
        "lifecycleState": "PROVISIONING",
        "availabilityDomain": data.get("availabilityDomain"),
        "shape": data.get("shape"),
        "timeCreated": datetime.now(timezone.utc).isoformat(),
    }
    INSTANCES.append(new_inst)
    return oci_res(new_inst)


@compute_bp.route("/instances/<instance_id>", methods=["GET"])
def get_instance(instance_id):
    inst = next((i for i in INSTANCES if i["id"] == instance_id), None)
    return oci_res(inst) if inst else (jsonify({"code": "NotAuthorizedOrNotFound"}), 404)


@compute_bp.route("/instances/<instance_id>", methods=["DELETE"])
def terminate_instance(instance_id):
    # In a mock, we just return 204 or the object with TERMINATING state
    return "", 204


@compute_bp.route("/instances/<instance_id>", methods=["POST"])
def instance_action(instance_id):
    action = request.args.get("action")
    print(f"DEBUG: Performing {action} on {instance_id}")
    return oci_res(
        {
            "id": instance_id,
            "lifecycleState": "STARTING" if action == "START" else "STOPPING",
        }
    )


@compute_bp.route("/images", methods=["GET"])
def list_images():
    return oci_res(IMAGES)


@compute_bp.route("/images/<image_id>", methods=["GET"])
def get_image(image_id):
    img = next((i for i in IMAGES if i["id"] == image_id), None)
    return oci_res(img) if img else (jsonify({"code": "NotAuthorizedOrNotFound"}), 404)


@compute_bp.route("/vnicAttachments", methods=["GET"])
def list_vnic_attachments():
    return oci_res(VNIC_ATTACHMENTS)


@compute_bp.route("/vnicAttachments/<vnic_attachment_id>", methods=["GET"])
def get_vnic_attachment(vnic_attachment_id):
    vnic = next((i for i in VNIC_ATTACHMENTS if i["id"] == vnic_attachment_id), None)
    return oci_res(vnic) if vnic else (jsonify({"code": "NotAuthorizedOrNotFound"}), 404)
