"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from logging import Logger

from fastmcp import FastMCP
from oracle.oci_monitoring_mcp_server.alarms.tools import MonitoringAlarmTools
from oracle.oci_monitoring_mcp_server.metrics.tools import MonitoringMetricsTools

from . import __project__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(
    name=__project__,
    instructions="Use this MCP server to run read-only commands and analyze "
    "Monitoring Logs, Metrics, and Alarms.",
)

try:
    monitoring_metrics_tools = MonitoringMetricsTools()
    monitoring_metrics_tools.register(mcp)
    logger.info("Monitoring metrics tools registered successfully")
    monitoring_alarms_tools = MonitoringAlarmTools()
    monitoring_alarms_tools.register(mcp)
    logger.info("Monitoring alarms tools registered successfully")
except Exception as e:
    logger.error(f"Error initializing OCI Monitoring tools: {str(e)}")
    raise


def main():
    mcp.run()


if __name__ == "__main__":
    main()
