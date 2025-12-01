"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Annotated, List, Tuple

import oci
from fastmcp import Context
from oci import Response
from oci.monitoring.models import (
    ListMetricsDetails,
    SummarizeMetricsDataDetails,
)
from oracle.oci_monitoring_mcp_server import __project__, __version__
from oracle.oci_monitoring_mcp_server.metrics.models import (
    CompartmentField,
    CompartmentIdInSubtreeField,
    Metric,
    MetricData,
    NamespaceField,
    StatisticType,
    map_metric,
    map_metric_data,
)
from pydantic import Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitoringMetricsTools:
    def __init__(self):
        logger.info("Loaded metric initialization")

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

    def register(self, mcp):
        """Register all Metrics tools with the MCP server."""
        # Register get_compute_metrics tool
        # @TODO Do we even need this tool anymore
        # mcp.tool(name="get_compute_metrics")(self.get_compute_metrics)
        mcp.tool(
            name="get_metrics_data",
            description="This tool retrieves aggregated metric data points in the OCI monitoring service."
            "Use the query and optional properties to filter the returned results. "
            "If there are no aggregated data points returned, "
            "suggest using another query or expanding the time range.",
        )(self.get_metrics_data)

        mcp.tool(
            name="get_available_metrics",
            description="This tool returns the available metric definitions "
            "that match the criteria specified in the request.",
        )(self.get_available_metrics)

    def _prepare_time_parameters(
        self, start_time, end_time
    ) -> Tuple[datetime, datetime]:
        """Process time parameters and calculate the period."""
        # Convert string times to datetime objects
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

        if end_time is None:
            end_time = datetime.now(timezone.utc)
        elif isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

        return start_time, end_time

    def _build_metric_query(
        self, metric: str, resolution: str, resource_id: str, statistic: str
    ) -> str:
        """Build the query string for the metric query."""
        # @TODO -> Convert user question into defined namespace or custom
        # @TODO -> Convert metric, statistic, and interval into query for API call
        # Need to group by
        # custom dimensions?

        filter_clause = f'{{resourceId = "{resource_id}"}}' if resource_id else ""
        query = f"{metric}[{resolution}]{filter_clause}.{statistic}()"

        logger.info(f"The metric query: {query}")
        return query

    async def get_metrics_data(
        self,
        context: Context,
        compartment_id: str = CompartmentField,
        resource_id: str = Field(
            ...,
            description="The OCID of the resource",
            examples=[
                "ocid1.instance.oc1.phx.anyhqljt6vnpo4icbvfcrphq2vkdmivmlbhupdw46nth7scky6rbigwjc7ea"
            ],
        ),
        metric: str = Field(
            "InstanceMetadataRequests",
            description="The metric that the user wants to fetch.",
        ),
        start_time: str | None = Field(
            "2025-11-04T18:17:00.000Z",
            description="The beginning of the time range to use when searching for metric data points. "
            "Format is defined by RFC3339. "
            "The response is inclusive of metric data points for the startTime. "
            "If no value is provided, this value will be the timestamp 3 hours before the call was sent.",
            examples=["2023-02-01T01:02:29.600Z", "2023-03-10T22:44:26.789Z"],
        ),
        end_time: str | None = Field(
            None,
            description="The end of the time range to use when searching for metric data points. "
            "Format is defined by RFC3339. "
            "The response is exclusive metric data points for the endTime. "
            "If no value is provided, this value will be the timestamp representing when the call was sent.",
            examples=["2023-02-01T01:02:29.600Z", "2023-03-10T22:44:26.789Z"],
        ),
        namespace: str = NamespaceField,
        statistic: StatisticType = Field(
            "mean", description="The statistic to use for the metric"
        ),
        resolution: str = Field(
            "1m",
            description="The time between calculated aggregation windows. "
            "Use with the query interval to vary the frequency for returning aggregated data points. "
            "For example, use a query interval of 5 minutes with a resolution of "
            "1 minute to retrieve five-minute aggregations at a one-minute frequency. "
            "The resolution must be equal or less than the interval in the query. "
            "The default resolution is 1m (one minute).",
            examples=["1m", "5m", "1h", "1d"],
        ),
        resource_group: str | None = Field(
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
            # Process time parameters and calculate period
            start_time_obj, end_time_obj = self._prepare_time_parameters(
                start_time, end_time
            )
            start_time = start_time_obj.isoformat().replace("+00:00", "Z")
            end_time = end_time_obj.isoformat().replace("+00:00", "Z")

            # Preprocess the query from the given params
            query = self._build_metric_query(metric, resolution, resource_id, statistic)

            logger.info(
                f"Calling get metrics data with these parameters: {query} namespace {namespace}"
            )

            # Create client
            monitoring_client = self.get_monitoring_client()

            # Call Summarize metrics data api and process the results
            summarize_metrics_data_details = SummarizeMetricsDataDetails(
                namespace=namespace,
                query=query,
                start_time=start_time,
                end_time=end_time,
            )
            response: Response | None = monitoring_client.summarize_metrics_data(
                compartment_id,
                summarize_metrics_data_details=summarize_metrics_data_details,
                compartment_id_in_subtree=compartment_id_in_subtree,
            )

            if response is None:
                logger.error("Received None response from summarize_metrics_data")
                await context.error(
                    "Received None response from summarize_metrics_data"
                )
                return "There was no response returned from the Monitoring API"

            data: List[oci.monitoring.models.Metric] = response.data
            return [map_metric(metric) for metric in data]
        except Exception as e:
            logger.error(f"Error in get_metric_data: {str(e)}")
            await context.error(f"Error getting metric data: {str(e)}")
            raise

    async def get_available_metrics(
        self,
        context: Context,
        compartment_id: str = CompartmentField,
        group_by: List[str] | None = Field(
            None,
            description="Group metrics by these fields in the response. "
            "For example, to list all metric namespaces available in a compartment, "
            'groupBy the "namespace" field. '
            "Supported fields: namespace, name, resourceGroup. "
            "If groupBy is used, then dimensionFilters is ignored.",
            examples=[["namespace"]],
        ),
        metric_name: str | None = Field(
            None,
            description="The metric name to use when searching for metric definitions.",
        ),
        namespace: str | None = Field(
            None,
            description="The source service or application to use when searching for metric definitions.",
            examples=["oci_computeagent"],
        ),
        resource_group: str | None = Field(
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
    ) -> List[MetricData] | str:
        try:
            # Create client
            monitoring_client = self.get_monitoring_client()

            list_metrics_details = ListMetricsDetails(
                name=metric_name,
                namespace=namespace,
                resource_group=resource_group,
                group_by=None,  # Add this line to avoid the error
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

            data: List[oci.monitoring.models.MetricData] = response.data
            return [map_metric_data(metric) for metric in data]
        except Exception as e:
            logger.error(f"Error in get_available_metrics: {str(e)}")
            await context.error(f"Error getting metric data: {str(e)}")
            raise

    def get_compute_metrics(
        self,
        compartment_id: str,
        start_time: str,
        end_time: str,
        metric_name: Annotated[
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
            str | None,
            "Optional compute instance OCID to filter by "
            "(maps to resourceId dimension)",
        ] = None,
        compartment_id_in_subtree: Annotated[
            bool,
            "Whether to include metrics from all subcompartments of the specified compartment",
        ] = False,
    ) -> list[dict]:
        # @TODO Remove this - its too specific to a use case
        monitoring_client = self.get_monitoring_client()
        namespace = "oci_computeagent"
        filter_clause = f'{{resourceId="{instance_id}"}}' if instance_id else ""
        query = f"{metric_name}[{resolution}]{filter_clause}.{aggregation}()"

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
