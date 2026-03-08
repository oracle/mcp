"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from datetime import datetime, timezone
from logging import Logger
from typing import Annotated, List, Optional, Tuple

import oci
from fastmcp import Context, FastMCP
from oci import Response
from oci.monitoring.models import ListMetricsDetails, SummarizeMetricsDataDetails
from oracle.oci_monitoring_mcp_server.alarm_models import (
    AlarmSummary,
    map_alarm_summary,
)
from oracle.oci_monitoring_mcp_server.metric_models import (
    CompartmentField,
    CompartmentIdInSubtreeField,
    ExampleNamespaces,
    Metric,
    MetricData,
    NamespaceField,
    map_metric,
    map_metric_data,
)
from oracle.oci_monitoring_mcp_server.scripts import MQL_QUERY_DOC, get_script_content
from pydantic import Field

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(
    name=__project__,
    instructions="Use this MCP server to run read-only commands and analyze "
    "Monitoring Logs, Metrics, and Alarms.",
)


def get_monitoring_client():
    logger.info("entering get_monitoring_client")
    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = os.path.expanduser(config["security_token_file"])
    token = None
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.monitoring.MonitoringClient(config, signer=signer)


@mcp.tool(name="list_alarms", description="Lists all alarms in a given compartment")
def list_alarms(
    compartment_id: Annotated[
        str,
        "The ID of the compartment containing the resources"
        "monitored by the metric that you are searching for.",
    ],
) -> list[AlarmSummary] | str:
    monitoring_client = get_monitoring_client()
    response: Response | None = monitoring_client.list_alarms(compartment_id=compartment_id)
    if response is None:
        logger.error("Received None response from list_metrics")
        return "There was no response returned from the Monitoring API"

    alarms: List[oci.monitoring.models.AlarmSummary] = response.data
    return [map_alarm_summary(alarm) for alarm in alarms]


@mcp.tool(
    name="list_metric_definitions",
    description="This tool returns the available metric definitions. "
    "Use this tool when you do not know the name of the metric "
    "or want to see all the available metric namespaces in a compartment. "
    "If there are no results found, remove the metric name or namespace fields. ",
)
async def list_metric_definitions(
    context: Context,
    compartment_id: str = CompartmentField,
    group_by: Optional[List[str]] = Field(
        None,
        description="Group metrics by these fields in the response. "
        "For example, to list all metric namespaces available in a compartment, "
        'groupBy the "namespace" field. '
        "Supported fields: namespace, name, resourceGroup. "
        "If groupBy is used, then dimensionFilters is ignored.",
        examples=[["namespace"]],
    ),
    metric_name: Optional[str] = Field(
        None,
        description="The metric name to use when searching for metric definitions.",
    ),
    namespace: Optional[str] = Field(
        None,
        description="The source service or application to use when searching for metric definitions. "
        "If you do not know the name of the namespace, leave it blank.",
        examples=[ExampleNamespaces],
    ),
    resource_group: Optional[str] = Field(
        None,
        description="Resource group that you want to match. "
        "A null value returns only metric data that has no resource groups. "
        "The specified resource group must exist in the definition of the posted metric. "
        "Only one resource group can be applied per metric. "
        "A valid resourceGroup value starts with an alphabetical character "
        "and includes only alphanumeric characters,"
        " periods (.), underscores (_), hyphens (-), and dollar signs ($).",
        examples=["frontend-fleet"],
    ),
    compartment_id_in_subtree: bool = CompartmentIdInSubtreeField,
) -> List[Metric] | str:
    try:
        # Create client
        monitoring_client = get_monitoring_client()

        list_metrics_details = ListMetricsDetails(
            name=metric_name,
            namespace=namespace,
            resource_group=resource_group,
            group_by=group_by,
        )
        response: Response | None = monitoring_client.list_metrics(
            compartment_id,
            list_metrics_details=list_metrics_details,
            compartment_id_in_subtree=compartment_id_in_subtree,
        )

        if response is None:
            logger.error("Received None response from list_metrics")
            await context.error("Received None response from list_metrics")
            return "There was no response returned from the Monitoring API"

        data: List[oci.monitoring.models.Metric] = response.data
        return [map_metric(metric) for metric in data]
    except Exception as e:
        logger.error(f"Error in get_available_metrics: {str(e)}")
        await context.error(f"Error getting metric data: {str(e)}")
        raise


def _prepare_time_parameters(start_time, end_time) -> Tuple[datetime, datetime]:
    """Process time parameters and calculate the period."""
    # Convert string times to datetime objects
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

    if end_time is None:
        end_time = datetime.now(timezone.utc)
    elif isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

    return start_time, end_time


@mcp.tool(
    name="get_metrics_data",
    description="This tool retrieves aggregated metric data points in the OCI monitoring service."
    "Use the query and optional properties to filter the returned results. "
    "If there are no aggregated data points returned, "
    "suggest using another query or expanding the time range."
    "You MUST use the MQL Syntax Guide resource before using this tool to get the query.",
)
async def get_metrics_data(
    context: Context,
    compartment_id: str = CompartmentField,
    query: str = Field(
        description="The Monitoring Query Language (MQL) expression "
        "to use when searching for metric data points to aggregate. "
        "The query must specify a metric, statistic, and interval."
        "Supported values for interval depend on the specified time range. "
        "More interval values are supported for smaller time ranges. "
        "You can optionally specify dimensions and grouping functions. "
        "When specifying a dimension value, surround it with double quotes,"
        "and escape each double quote with a backslash (`) character.",
        examples=[
            "CpuUtilization[1m].sum()",
            "BytesReceived[1h].mean()",
        ],
    ),
    start_time: Optional[str] = Field(
        "2025-11-04T18:17:00.000Z",
        description="The beginning of the time range to use when searching for metric data points. "
        "Format is defined by RFC3339. "
        "The response is inclusive of metric data points for the startTime. "
        "If no value is provided, this value will be the timestamp 3 hours before the call was sent.",
        examples=["2023-02-01T01:02:29.600Z", "2023-03-10T22:44:26.789Z"],
    ),
    end_time: Optional[str] = Field(
        None,
        description="The end of the time range to use when searching for metric data points. "
        "Format is defined by RFC3339. "
        "The response is exclusive metric data points for the endTime. "
        "If no value is provided, this value will be the timestamp representing when the call was sent.",
        examples=["2023-02-01T01:02:29.600Z", "2023-03-10T22:44:26.789Z"],
    ),
    namespace: str = NamespaceField,
    resource_group: Optional[str] = Field(
        None,
        description="Resource group that you want to match. "
        "A null value returns only metric data that has no resource groups. "
        "The specified resource group must exist in the definition of the posted metric. "
        "Only one resource group can be applied per metric. "
        "A valid resourceGroup value starts with an alphabetical character "
        "and includes only alphanumeric characters,"
        " periods (.), underscores (_), hyphens (-), and dollar signs ($).",
        examples=["frontend-fleet"],
    ),
    resolution: Optional[str] = Field(
        "1m",
        description="The time between calculated aggregation windows."
        "Use with the query interval to vary the frequency for returning aggregated data points. "
        "For example, use a query interval of 5 minutes with a resolution of "
        "1 minute to retrieve five-minute aggregations at a one-minute frequency. "
        "The resolution must 'be equal or less than the interval in the query. "
        "The default resolution is 1m (one minute).",
        examples=["1m", "5m", "1h", "1d"],
    ),
    compartment_id_in_subtree: Optional[bool] = CompartmentIdInSubtreeField,
) -> List[MetricData] | str:
    try:
        # Process time parameters and calculate period
        start_time_obj, end_time_obj = _prepare_time_parameters(start_time, end_time)
        start_time = start_time_obj.isoformat().replace("+00:00", "Z")
        end_time = end_time_obj.isoformat().replace("+00:00", "Z")

        logger.info(f"Calling get metrics data with these parameters: {query}")

        # Create client
        monitoring_client = get_monitoring_client()

        # Call Summarize metrics data api and process the results
        summarize_metrics_data_details = SummarizeMetricsDataDetails(
            namespace=namespace,
            query=query,
            start_time=start_time,
            end_time=end_time,
            resource_group=resource_group,
            resolution=resolution,
        )
        response: Response | None = monitoring_client.summarize_metrics_data(
            compartment_id,
            summarize_metrics_data_details=summarize_metrics_data_details,
            compartment_id_in_subtree=compartment_id_in_subtree,
        )

        if response is None:
            logger.error("Received None response from summarize_metrics_data")
            await context.error("Received None response from summarize_metrics_data")
            return "There was no response returned from the Monitoring API"

        data: List[oci.monitoring.models.MetricData] = response.data
        return [map_metric_data(metric) for metric in data]
    except Exception as e:
        logger.error(f"Error in get_metrics_data: {str(e)}")
        await context.error(f"Error getting metrics data: {str(e)}")
        raise


@mcp.resource(
    name="MQL Syntax Guide",
    uri="resource://monitoring-query-syntax-guide",
    description="A guide for OCI Monitoring Query Language (MQL), "
    "including syntax, examples, and event types. "
    "Use this for constructing mql queries in the get_metrics_data tool.",
)
def monitoring_query_syntax_guide() -> str:
    return get_script_content(MQL_QUERY_DOC)


def main():
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
