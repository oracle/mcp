"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Annotated

import oci
from fastmcp import FastMCP

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


@mcp.tool
def list_log_groups(
    compartment_id: Annotated[str, "Compartment OCID to list resources in."],
) -> list[dict]:
    logging_client = get_logging_client()
    response = logging_client.list_log_groups(compartment_id=compartment_id)
    log_groups = response.data
    result = []
    for log_group in log_groups:
        result.append(
            {
                "id": log_group.id,
                "display_name": log_group.display_name,
                "lifecycle_state": log_group.lifecycle_state,
                "description": log_group.description,
            }
        )
    return result


@mcp.tool
def list_logs(
    log_group_id: Annotated[str, "OCID of a log group to work with."],
) -> list[dict]:
    logging_client = get_logging_client()
    response = logging_client.list_logs(log_group_id=log_group_id)
    logs = response.data
    result = []
    for log in logs:
        result.append(
            {
                "id": log.id,
                "log_group_id": log_group_id,
                "display_name": log.display_name,
                "lifecycle_state": log.lifecycle_state,
            }
        )
    return result


@mcp.tool
def get_log(
    log_id: Annotated[str, "OCID of a log to work with."],
    log_group_id: Annotated[str, "OCID of a log group to work with."],
) -> dict:
    logging_client = get_logging_client()
    response = logging_client.get_log(log_group_id=log_group_id, log_id=log_id)
    log = response.data
    return {
        "id": log.id,
        "display_name": log.display_name,
        "lifecycle_state": log.lifecycle_state,
        "log_type": log.log_type,
        "retention_duration": log.retention_duration,
        "is_enabled": log.is_enabled,
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
