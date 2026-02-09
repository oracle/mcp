"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import uuid

from _common import oci_res
from compute_instance_agent_data import (
    INSTANCE_AGENT_COMMANDS,
    INSTANCE_AGENT_EXECUTIONS,
    now_rfc3339,
)
from flask import Blueprint, request

# OCI Compute Instance Agent API version base path (matches OCI SDK expectations via proxy shim)
compute_instance_agent_bp = Blueprint(
    "compute_instance_agent", __name__, url_prefix="/20180530"
)


@compute_instance_agent_bp.route("/instanceAgentCommands", methods=["POST"])
def create_instance_agent_command():
    data = request.json or {}
    cmd_id = f"ocid1.instanceagentcommand.oc1..{uuid.uuid4()}"

    # Persist created command
    record = {
        "id": cmd_id,
        "displayName": data.get("displayName", "agent-command-adhoc"),
        "compartmentId": data.get("compartmentId"),
        "executionTimeOutInSeconds": data.get("executionTimeOutInSeconds", 30),
        "timeCreated": now_rfc3339(),
    }
    INSTANCE_AGENT_COMMANDS.append(record)

    return oci_res(record)


@compute_instance_agent_bp.route(
    "/instanceAgentCommands/<instance_agent_command_id>/status",
    methods=["GET"],
)
def get_instance_agent_command_execution(instance_agent_command_id):
    # Synthesize a successful execution for the created command
    exec_obj = {
        "instanceAgentCommandId": instance_agent_command_id,
        "instanceId": request.args.get("instanceId", "ocid1.instance.oc1..mock-uuid-1"),
        "deliveryState": "VISIBLE",
        "lifecycleState": "SUCCEEDED",
        "timeCreated": now_rfc3339(),
        "timeUpdated": now_rfc3339(),
        "sequenceNumber": 1,
        "displayName": "adhoc",
        "content": {
            "outputType": "TEXT",
            "exitCode": 0,
            "message": "Execution successful",
            "text": "Hello from agent",
            "textSha256": "deadbeef",
        },
    }
    return oci_res(exec_obj)


@compute_instance_agent_bp.route("/instanceAgentCommandExecutions", methods=["GET"])
def list_instance_agent_command_executions():
    instance_id = request.args.get("instanceId")
    limit = request.args.get("limit", type=int)

    items = INSTANCE_AGENT_EXECUTIONS
    if instance_id:
        items = [i for i in items if i.get("instanceId") == instance_id]
    if limit is not None:
        items = items[:limit]

    return oci_res(items)
