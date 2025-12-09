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
from oci.monitoring.models import SummarizeMetricsDataDetails

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_monitoring_client():
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


@mcp.tool
def get_compute_metrics(
    compartment_id: str,
    start_time: str,
    end_time: str,
    metricName: Annotated[
        str,
        "The metric that the user wants to fetch. Currently we only support:"
        "CpuUtilization, MemoryUtilization, DiskIopsRead, DiskIopsWritten,"
        "DiskBytesRead, DiskBytesWritten, NetworksBytesIn,"
        "NetworksBytesOut, LoadAverage, MemoryAllocationStalls",
    ],
    resolution: Annotated[
        str,
        "The granularity of the metric. Currently we only support: 1m, 5m, 1h, 1d. Default: 1m.",
    ] = "1m",
    aggregation: Annotated[
        str,
        "The aggregation for the metric. Currently we only support: "
        "mean, sum, max, min, count. Default: mean",
    ] = "mean",
    instance_id: Annotated[
        str,
        "Optional compute instance OCID to filter by " "(maps to resourceId dimension)",
    ] = None,
    compartment_id_in_subtree: Annotated[
        bool,
        "Whether to include metrics from all subcompartments of the specified compartment",
    ] = False,
) -> list[dict]:
    monitoring_client = get_monitoring_client()
    namespace = "oci_computeagent"
    filter_clause = f'{{resourceId="{instance_id}"}}' if instance_id else ""
    query = f"{metricName}[{resolution}]{filter_clause}.{aggregation}()"

    series_list = monitoring_client.summarize_metrics_data(
        compartment_id=compartment_id,
        summarize_metrics_data_details=SummarizeMetricsDataDetails(
            namespace=namespace,
            query=query,
            start_time=start_time,
            end_time=end_time,
            resolution=resolution,
        ),
        compartment_id_in_subtree=compartment_id_in_subtree,
    ).data

    result: list[dict] = []
    for series in series_list:
        dims = getattr(series, "dimensions", None)
        points = []
        for p in getattr(series, "aggregated_datapoints", []):
            points.append(
                {
                    "timestamp": getattr(p, "timestamp", None),
                    "value": getattr(p, "value", None),
                }
            )
        result.append(
            {
                "dimensions": dims,
                "datapoints": points,
            }
        )
    return result


@mcp.tool
def list_alarms(
    compartment_id: Annotated[
        str,
        "The ID of the compartment containing the resources"
        "monitored by the metric that you are searching for.",
    ],
) -> list[dict]:
    monitoring_client = get_monitoring_client()
    response = monitoring_client.list_alarms(compartment_id=compartment_id)
    alarms = response.data
    result = []
    for alarm in alarms:
        result.append(
            {
                "id": alarm.id,
                "display_name": alarm.display_name,
                "severity": alarm.severity,
                "lifecycle_state": alarm.lifecycle_state,
                "namespace": alarm.namespace,
                "query": alarm.query,
            }
        )
    return result


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
