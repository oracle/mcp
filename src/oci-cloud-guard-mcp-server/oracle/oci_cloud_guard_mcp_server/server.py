"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Literal, Optional

import oci
from fastmcp import FastMCP
from oci.cloud_guard import CloudGuardClient
from oracle.oci_cloud_guard_mcp_server.models import (
    Problem,
    map_problem,
)
from pydantic import Field

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_cloud_guard_client():
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
    description="Returns a list of all Problems identified by Cloud Guard.",
)
def list_problems(
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    risk_level: Optional[str] = Field(None, description="Risk level of the problem"),
    lifecycle_state: Optional[str] = Field(
        "ACTIVE",
        description="The field lifecycle state. "
        "Only one state can be provided. Default value for state is active.",
    ),
    detector_rule_ids: Optional[list[str]] = Field(
        None,
        description="Comma separated list of detector rule IDs to be passed in to match against Problems.",
    ),
    time_range_days: Optional[int] = Field(
        30, description="Number of days to look back for problems"
    ),
    limit: Optional[int] = Field(10, description="The number of problems to return"),
) -> list[Problem]:
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

    response = get_cloud_guard_client().list_problems(**kwargs)

    problems: list[Problem] = []
    data: list[oci.cloud_guard.models.Problem] = response.data.items
    for d in data:
        problem = map_problem(d)
        problems.append(problem)
    return problems


@mcp.tool(
    name="get_problem_details",
    description="Get the details for a Problem identified by problemId.",
)
def get_problem_details(
    problem_id: str = Field(..., description="The OCID of the problem")
) -> Problem:
    response = get_cloud_guard_client().get_problem(problem_id=problem_id)
    problem = response.data
    return map_problem(problem)


@mcp.tool(
    name="update_problem_status",
    description="Changes the current status of the problem, identified by problemId, to the status "
    "specified in the UpdateProblemStatusDetails resource that you pass.",
)
def update_problem_status(
    problem_id: str = Field(..., description="The OCID of the problem"),
    status: str = Field(
        Literal["OPEN", "RESOLVED", "DISMISSED", "DELETED", "UNKNOWN_ENUM_VALUE"],
        description="Action taken by user. Allowed values are: OPEN, RESOLVED, DISMISSED, CLOSED",
    ),
    comment: str = Field(None, description="A comment from the user"),
) -> Problem:
    updated_problem_status = oci.cloud_guard.models.UpdateProblemStatusDetails(
        status=status, comment=comment
    )
    response = get_cloud_guard_client().update_problem_status(
        problem_id=problem_id,
        update_problem_status_details=updated_problem_status,
    )
    problem = response.data
    return map_problem(problem)


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
