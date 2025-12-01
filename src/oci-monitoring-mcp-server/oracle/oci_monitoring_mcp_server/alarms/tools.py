"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Annotated, List

import oci
from fastmcp import FastMCP
from oci import Response
from oracle.oci_monitoring_mcp_server import __project__, __version__
from oracle.oci_monitoring_mcp_server.alarms.models import (
    AlarmSummary,
    map_alarm_summary,
)

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


class MonitoringAlarmTools:
    def __init__(self):
        logger.info("Loaded alarm class")

    def register(self, mcp):
        """Register all alarm tools with the MCP server."""
        # Register list_alarms tool
        mcp.tool(
            name="list_alarms", description="Lists all alarms in a given compartment"
        )(self.list_alarms)

    def get_monitoring_client(self):
        logger.info("entering get_monitoring_client")
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
        return oci.monitoring.MonitoringClient(config, signer=signer)

    def list_alarms(
        self,
        compartment_id: Annotated[
            str,
            "The ID of the compartment containing the resources"
            "monitored by the metric that you are searching for.",
        ],
    ) -> list[AlarmSummary] | str:
        monitoring_client = self.get_monitoring_client()
        response: Response | None = monitoring_client.list_alarms(
            compartment_id=compartment_id
        )
        if response is None:
            logger.error("Received None response from list_metrics")
            return "There was no response returned from the Monitoring API"

        alarms: List[oci.monitoring.models.AlarmSummary] = response.data
        return [map_alarm_summary(alarm) for alarm in alarms]
