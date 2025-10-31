"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Optional

import oci
from fastmcp import FastMCP
from oracle.oci_logging_mcp_server.models import (
    Log,
    LogGroup,
    LogGroupSummary,
    LogSummary,
    map_log,
    map_log_group,
    map_log_group_summary,
    map_log_summary,
)
from pydantic import Field

from . import __project__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_logging_client():
    logger.info("entering get_logging_client")
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )

    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    token = None
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.logging.LoggingManagementClient(config, signer=signer)


@mcp.tool(description="List Log Groups in a given compartment")
def list_log_groups(
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[LogGroupSummary]:
    log_groups: list[LogGroupSummary] = []

    try:
        client = get_logging_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(log_groups) < limit):
            kwargs = {
                "compartment_id": compartment_id,
                "page": next_page,
                "limit": limit,
            }

            response = client.list_log_groups(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.logging.models.LogGroupSummary] = response.data
            for d in data:
                log_groups.append(map_log_group_summary(d))

        logger.info(f"Found {len(log_groups)} Log Groups")
        return log_groups

    except Exception as e:
        logger.error(f"Error in list_log_groups tool: {str(e)}")
        raise e


@mcp.tool(description="Fetch the details of a log group")
def get_log_group(
    log_group_id: str = Field(
        ..., description="The OCID of the log group that the log belongs to."
    ),
) -> LogGroup:
    try:
        client = get_logging_client()

        response: oci.response.Response = client.get_log_group(
            log_group_id=log_group_id
        )
        data: oci.logging.models.Log = response.data
        logger.info("Found Log Group")
        return map_log_group(data)

    except Exception as e:
        logger.error(f"Error in get_log_group tool: {str(e)}")
        raise e


@mcp.tool(description="List Log Groups in a given log group")
def list_logs(
    log_group_id: str = Field(
        ..., description="The OCID of the log group to list logs from."
    ),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[LogSummary]:
    logs: list[LogSummary] = []

    try:
        client = get_logging_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(logs) < limit):
            kwargs = {
                "log_group_id": log_group_id,
                "page": next_page,
                "limit": limit,
            }

            response = client.list_logs(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.logging.models.LogSummary] = response.data
            for d in data:
                logs.append(map_log_summary(d))

        logger.info(f"Found {len(logs)} Logs")
        return logs

    except Exception as e:
        logger.error(f"Error in list_logs tool: {str(e)}")
        raise e


@mcp.tool(description="Fetch the details of a log")
def get_log(
    log_id: str = Field(..., description="The OCID of the log"),
    log_group_id: str = Field(
        ..., description="The OCID of the log group that the log belongs to."
    ),
) -> Log:
    try:
        client = get_logging_client()

        response: oci.response.Response = client.get_log(
            log_group_id=log_group_id, log_id=log_id
        )
        data: oci.logging.models.Log = response.data
        logger.info("Found Log")
        return map_log(data)

    except Exception as e:
        logger.error(f"Error in get_log tool: {str(e)}")
        raise e


def main():
    mcp.run()


if __name__ == "__main__":
    main()
