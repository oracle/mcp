"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Literal, Optional

import oci
from fastmcp import FastMCP
from oracle.oci_migration_mcp_server.models import (
    Migration,
    MigrationSummary,
    map_migration,
    map_migration_summary,
)
from pydantic import Field

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_migration_client():
    logger.info("entering get_migration_client")
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
    return oci.cloud_migrations.MigrationClient(config, signer=signer)


@mcp.tool(description="Get details for a specific Migration Project by OCID")
def get_migration(
    migration_id: str = Field(..., description="OCID of the migration project")
) -> Migration:
    try:
        client = get_migration_client()

        response: oci.response.Response = client.get_migration(migration_id)
        data: oci.cloud_migrations.models.Migration = response.data
        logger.info("Found Migration")
        return map_migration(data)

    except Exception as e:
        logger.error(f"Error in get_migration tool: {str(e)}")
        raise e


@mcp.tool(
    description="List Migration Projects for a compartment, optionally filtered by lifecycle state"
)
def list_migrations(
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of migrations to return. If None, there is no limit.",
        ge=1,
    ),
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "UPDATING",
            "NEEDS_ATTENTION",
            "ACTIVE",
            "DELETING",
            "DELETED",
            "FAILED",
        ]
    ] = Field(None, description="The lifecycle state of the migration to filter on"),
) -> list[MigrationSummary]:
    migrations: list[Migration] = []

    try:
        client = get_migration_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(migrations) < limit):
            kwargs = {
                "compartment_id": compartment_id,
                "page": next_page,
                "limit": limit,
            }

            if lifecycle_state is not None:
                kwargs["lifecycle_state"] = lifecycle_state

            response = client.list_migrations(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.cloud_migrations.models.MigrationSummary] = (
                response.data.items
            )
            for d in data:
                migrations.append(map_migration_summary(d))

        logger.info(f"Found {len(migrations)} Migrations")
        return migrations

    except Exception as e:
        logger.error(f"Error in list_migrations tool: {str(e)}")
        raise e


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
