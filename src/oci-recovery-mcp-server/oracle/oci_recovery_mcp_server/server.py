"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# Module overview:
# This file chooses a transport and starts the server. The tools live in four
# families, and the OCI plumbing they share lives beside them:
#
# TOOL FAMILIES -- each registers its tools on import
# - recovery_tools:  list/get for protected databases, protection policies, recovery
#                    service subnets, backups, restore, metrics, limits and regions.
# - summarise_tools: the aggregating tools -- health, redo status, backup space used
#                    and backup destinations.
# - database_tools:  list/get for DB systems, DB homes and databases.
# - prompt_tools:    the three static guidance tools.
#
# SHARED
# - app:            the FastMCP instance, the tool annotation hints, and _Deadline.
# - logging_setup:  root logging configuration and the structured event log.
# - telemetry:      request/actor/installation ids, the opc-request-id stamped on
#                   outbound SDK calls, and the @_tool_logger decorator.
# - auth:           credential resolution for both transports (local OCI profile over
#                   stdio, OCI IAM/IDCS per caller over HTTP) and the tenancy.
# - clients:        OCI SDK client factories built on top of auth + telemetry.
# - cache:          the key that partitions cached entries by tenant and caller.
# - regions:        the tenancy's subscribed regions, read from IAM on every call.
# - compartments:   compartment discovery, subtree expansion, name/OCID resolution.
# - models:         the server's typed results and the map_* SDK adapters.
#
# Importing a tool family is what registers its tools -- the @mcp.tool decorators run
# at import time -- so those imports below are the wiring, not a convenience. Dropping
# one silently removes that family from the served tool surface.
#
# main() chooses the transport:
# - ORACLE_MCP_HOST and ORACLE_MCP_PORT both set: streamable HTTP, with OCI IAM (IDCS)
#   sign-in per caller.
# - Otherwise stdio (the default for MCP), on the operator's own OCI profile.

import os

from . import __project__, __version__, auth, logging_setup
from . import database_tools, prompt_tools, recovery_tools, summarise_tools  # noqa: F401
from .app import mcp
from .logging_setup import logger


def main():
    """
    Console entrypoint: start FastMCP over stdio, or over HTTP when a listener is
    configured.

    ORACLE_MCP_HOST and ORACLE_MCP_PORT must be set together; with neither set the
    server speaks stdio using local profile credentials. With both set it serves
    streamable HTTP and authenticates every caller against an OCI IAM (IDCS)
    domain -- local profile credentials are never used to serve a network
    listener.
    """
    host = (os.getenv("ORACLE_MCP_HOST") or "").strip()
    port = (os.getenv("ORACLE_MCP_PORT") or "").strip()

    # Log startup and where logs are actually going (stderr if the file could
    # not be opened, so the line never points at a file that does not exist).
    logger.info("Starting %s v%s", __project__, __version__)
    logger.info("Logs will be written to: %s", logging_setup._LOG_DESTINATION)

    if bool(host) != bool(port):
        raise ValueError(
            "ORACLE_MCP_HOST and ORACLE_MCP_PORT must either both be set or both be unset."
        )

    if not host:
        logger.info("Running FastMCP over stdio transport (auth_type=%s)", auth._resolved_auth_type_label())
        mcp.run()
        return

    try:
        port_number = int(port)
    except ValueError as exc:
        raise ValueError("ORACLE_MCP_PORT must be an integer from 1 to 65535.") from exc
    if not 1 <= port_number <= 65535:
        raise ValueError("ORACLE_MCP_PORT must be an integer from 1 to 65535.")

    # HTTP transport authenticates every caller against an OCI IAM (IDCS) domain;
    # local profile credentials are never used to serve a network listener.
    logger.info("Running FastMCP over streamable HTTP with OCI IAM OAuth at http://%s:%s", host, port)
    auth._http_auth = auth._build_http_auth()
    mcp.auth = auth._http_auth.provider
    mcp.run(transport="http", host=host, port=port_number)


if __name__ == "__main__":
    main()
