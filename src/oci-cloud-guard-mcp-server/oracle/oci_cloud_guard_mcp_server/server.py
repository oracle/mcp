"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Annotated, Any, Dict, List, Optional

import oci
from fastmcp import FastMCP
from oci.cloud_guard import CloudGuardClient

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_cloud_guard_client():
    logger.info("entering get_cloud guard client")
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )

    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    token = None
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return CloudGuardClient(config, signer=signer)


@mcp.tool(
    name="list_problems",
    description="Returns a list of all Problems identified by Cloud Guard which are currently in the database"
    " and meet the filtering criteria. The ListProblems operation returns only the problems in compartmentId "
    "passed. The list does not include any subcompartments of the compartmentId passed. The parameter"
    " accessLevel specifies whether to return only those compartments for which the requestor has INSPECT "
    "permissions on at least one resource directly or indirectly (ACCESSIBLE) (the resource can be in a "
    "subcompartment) or to return Not Authorized if Principal doesn't have access to even one of the child "
    "compartments. This is valid only when compartmentIdInSubtree is set to true. The parameter "
    "compartmentIdInSubtree applies when you perform ListProblems on the compartmentId passed and when it is "
    "set to true, the entire hierarchy of compartments can be returned. To get a full list of all"
    " compartments and subcompartments in the tenancy (root compartment), set the parameter "
    "compartmentIdInSubtree to true and accessLevel to ACCESSIBLE.",
)
def list_problems(
    compartment_id: Annotated[
        Optional[str], "The OCID of the compartment in which to list resources."
    ] = None,
    risk_level: Annotated[Optional[str], "Risk level of the problem"] = None,
    lifecycle_state: Annotated[
        Optional[str],
        "The field lifecycle state. Only one state can be provided. Default value for state is active.",
    ] = "ACTIVE",
    detector_rule_ids: Annotated[
        Optional[list[str]],
        "Comma seperated list of detector rule IDs to be passed in to match against Problems.",
    ] = None,
    time_range_days: Annotated[
        Optional[int], "Number of days to look back for problems"
    ] = 30,
    limit: Annotated[int, "The number of problems to return"] = 10,
) -> List[Dict[str, Any]]:
    time_filter = (
        datetime.now(timezone.utc) - timedelta(days=time_range_days)
    ).isoformat()

    kwargs = {
        "compartment_id": compartment_id,
        "time_last_detected_greater_than_or_equal_to": time_filter,
        "limit": limit,
    }

    if risk_level:
        kwargs["risk_level"] = risk_level
    if lifecycle_state:
        kwargs["lifecycle_state"] = lifecycle_state
    if detector_rule_ids:
        kwargs["detector_rule_id_list"] = detector_rule_ids

    response = get_cloud_guard_client().list_problems(**kwargs).data.items
    return [
        {
            "id": problem.id,
            "status": problem.lifecycle_detail,
            "detector_rule_id": problem.detector_rule_id,
            "risk_level": problem.risk_level,
            "risk_score": problem.risk_score,
            "resource_name": problem.resource_name,
            "resource_type": problem.resource_type,
            "lifecycle_state": problem.lifecycle_state,
            "time_first_detected": (
                problem.time_first_detected.isoformat()
                if problem.time_first_detected
                else None
            ),
            "time_last_detected": (
                problem.time_last_detected.isoformat()
                if problem.time_last_detected
                else None
            ),
            "region": problem.region,
            "labels": problem.labels,
            "compartment_id": problem.compartment_id,
        }
        for problem in response
    ]


@mcp.tool(
    name="get_problem_details",
    description="Get the details for a Problem identified by problemId.",
)
def get_problem_details(
    problem_id: Annotated[str, "The OCID of the problem"],
):
    response = get_cloud_guard_client().get_problem(problem_id=problem_id)
    problem = response.data

    return {
        "id": problem.id,
        "detector_rule_id": problem.detector_rule_id,
        "detector_id": problem.detector_id,
        "risk_level": problem.risk_level,
        "risk_score": problem.risk_score,
        "resource_id": problem.resource_id,
        "resource_name": problem.resource_name,
        "resource_type": problem.resource_type,
        "lifecycle_state": problem.lifecycle_state,
        "lifecycle_detail": problem.lifecycle_detail,
        "time_first_detected": (
            problem.time_first_detected.isoformat()
            if problem.time_first_detected
            else None
        ),
        "time_last_detected": (
            problem.time_last_detected.isoformat()
            if problem.time_last_detected
            else None
        ),
        "description": problem.description,
        "recommendation": problem.recommendation,
        "additional_details": problem.additional_details,
        "comment": problem.comment,
    }


@mcp.tool(
    name="update_problem_status",
    description="Changes the current status of the problem, identified by problemId, to the status "
    "specified in the UpdateProblemStatusDetails resource that you pass.",
)
def update_problem_status(
    problem_id: Annotated[str, "OCID of the problem"],
    status: Annotated[
        str,
        "Action taken by user. Allowed values are: OPEN, RESOLVED, DISMISSED, CLOSED",
    ],
    comment: Annotated[Optional[str], "A comment from the user"] = None,
):
    updated_problem_status = oci.cloud_guard.models.UpdateProblemStatusDetails(
        status=status, comment=comment
    )
    response = get_cloud_guard_client().update_problem_status(
        problem_id=problem_id,
        update_problem_status_details=updated_problem_status,
    )
    problem = response.data

    return {
        "id": problem.id,
        "detector_rule_id": problem.detector_rule_id,
        "detector_id": problem.detector_id,
        "risk_level": problem.risk_level,
        "risk_score": problem.risk_score,
        "resource_id": problem.resource_id,
        "resource_name": problem.resource_name,
        "resource_type": problem.resource_type,
        "lifecycle_state": problem.lifecycle_state,
        "lifecycle_detail": problem.lifecycle_detail,
        "time_first_detected": (
            problem.time_first_detected.isoformat()
            if problem.time_first_detected
            else None
        ),
        "time_last_detected": (
            problem.time_last_detected.isoformat()
            if problem.time_last_detected
            else None
        ),
        "description": problem.description,
        "recommendation": problem.recommendation,
        "additional_details": problem.additional_details,
        "comment": problem.comment,
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
