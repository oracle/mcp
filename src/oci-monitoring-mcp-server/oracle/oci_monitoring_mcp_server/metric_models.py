"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

import oci
from pydantic import BaseModel, Field

StatisticType = Literal[
    "absent",
    "avg",
    "count",
    "first",
    "increment",
    "last",
    "max",
    "mean",
    "min",
    "percentile",
    "rate",
    "sum",
]
PredicateType = Literal[
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "not_equal_to",
    "between",
    "outside",
    "absent",
]
ExampleNamespaces = [
    "oci_apigateway",
    "oci_autonomous_database",
    "oci_bastion",
    "oci_blockstore",
    "oci_certificates",
    "oci_cloudevents",
    "oci_compute",
    "oci_compute_infrastructure_health",
    "oci_compute_instance_health",
    "oci_dns",
    "oci_dynamic_routing_gateway",
    "oci_fastconnect",
    "oci_filestorage",
    "oci_goldengate",
    "oci_healthchecks",
    "oci_instancepools",
    "oci_internet_gateway",
    "oci_lbaas",
    "oci_logging",
    "oci_logging_analytics",
    "oci_nat_gateway",
    "oci_network_firewall",
    "oci_nlb",
    "oci_nlb_extended",
    "oci_notification",
    "oci_objectstorage",
    "oci_secrets",
    "oci_vcn",
    "oci_vcnip",
    "oci_vmi_resource_utilization",
    "oci_vpn",
]
# Reusable Fields across tools

CompartmentField = Field(
    ...,
    description="The OCID of the compartment",
)

CompartmentIdInSubtreeField = Field(
    False,
    description="Whether to include metrics from all subcompartments of the specified compartment",
)

NamespaceField = Field(
    "oci_compute",
    description="The source service or application to use when searching for metric data points"
    "to aggregate. If you do not know the name of the namespace, "
    "use the list_metric_definitions tool with an empty namespace parameter.",
    examples=[ExampleNamespaces],
)


class Metric(BaseModel):
    """
    Pydantic model mirroring (a subset of) oci.monitoring.models.Metric.
    The fields below represent the commonly used attributes found on the OCI SDK Metric model.
    """

    namespace: Optional[str] = Field(
        None, description="The source service or application emitting the metric."
    )
    resource_group: Optional[str] = Field(
        None,
        description="Resource group specified for the metric. A metric can be part of a resource group.",
    )
    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment containing the resource emitting the metric.",
    )
    name: Optional[str] = Field(None, description="The metric name (for example, CpuUtilization).")
    dimensions: Optional[Dict[str, str]] = Field(
        None,
        description="Dimensions (key/value pairs) that qualify the metric (for example, resourceId).",
    )
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description="Metric metadata (for example, unit). "
        "Keys and values are defined by the emitting service.",
    )
    resolution: Optional[str] = Field(
        None,
        description="The publication resolution of the metric, such as '1m'.",
    )


def map_metric(metric_data: oci.monitoring.models.Metric) -> Metric:
    """
    Convert an oci.monitoring.models.Metric to oracle.oci_monitoring_mcp_server.models.Metric.
    """
    return Metric(
        namespace=getattr(metric_data, "namespace", None),
        resource_group=getattr(metric_data, "resource_group", None),
        compartment_id=getattr(metric_data, "compartment_id", None),
        name=getattr(metric_data, "name", None),
        dimensions=getattr(metric_data, "dimensions", None),
        metadata=getattr(metric_data, "metadata", None),
        resolution=getattr(metric_data, "resolution", None),
    )


class AggregatedDatapoint(BaseModel):
    """
    Pydantic model mirroring oci.monitoring.models.AggregatedDatapoint.
    """

    timestamp: Optional[datetime] = Field(
        None,
        description="The date and time associated with the aggregated value (RFC3339).",
    )
    value: Optional[float] = Field(None, description="The aggregated metric value for the time window.")


class MetricData(BaseModel):
    """
    Pydantic model mirroring (a subset of) oci.monitoring.models.MetricData.
    """

    namespace: Optional[str] = Field(
        None, description="The source service or application emitting the metric."
    )
    resource_group: Optional[str] = Field(None, description="Resource group specified for the metric.")
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the resource."
    )
    name: Optional[str] = Field(None, description="The metric name (for example, CpuUtilization).")
    dimensions: Optional[Dict[str, str]] = Field(
        None,
        description="Dimensions that qualify the metric (for example, resourceId).",
    )
    metadata: Optional[Dict[str, str]] = Field(None, description="Metric metadata such as unit.")
    resolution: Optional[str] = Field(
        None,
        description="The publication resolution of the metric (for example, '1m').",
    )
    aggregated_datapoints: Optional[List[AggregatedDatapoint]] = Field(
        None,
        description="Time series datapoints aggregated at the requested resolution.",
    )


def map_aggregated_datapoint(
    p: oci.monitoring.models.AggregatedDatapoint | None,
) -> AggregatedDatapoint | None:
    if not p:
        return None
    return AggregatedDatapoint(
        timestamp=getattr(p, "timestamp", None),
        value=getattr(p, "value", None),
    )


def map_aggregated_datapoints(items) -> list[AggregatedDatapoint] | None:
    if not items:
        return None
    result: list[AggregatedDatapoint] = []
    for it in items:
        mapped_datapoint = map_aggregated_datapoint(it)
        if mapped_datapoint is not None:
            result.append(mapped_datapoint)
    return result if result else None


def map_metric_data(metric_data: oci.monitoring.models.MetricData) -> MetricData:
    """
    Convert an oci.monitoring.models.MetricData to oracle.oci_monitoring_mcp_server.models.MetricData.
    """
    return MetricData(
        namespace=getattr(metric_data, "namespace", None),
        resource_group=getattr(metric_data, "resource_group", None),
        compartment_id=getattr(metric_data, "compartment_id", None),
        name=getattr(metric_data, "name", None),
        dimensions=getattr(metric_data, "dimensions", None),
        metadata=getattr(metric_data, "metadata", None),
        resolution=getattr(metric_data, "resolution", None),
        aggregated_datapoints=map_aggregated_datapoints(getattr(metric_data, "aggregated_datapoints", None)),
    )


class Datapoint(BaseModel):
    """
    Pydantic model mirroring oci.monitoring.models.Datapoint
    used when posting metric data (not aggregated/summarized).
    """

    timestamp: Optional[datetime] = Field(
        None, description="The time the metric value was recorded (RFC3339)."
    )
    value: Optional[float] = Field(None, description="Metric value at the given timestamp.")
    count: Optional[int] = Field(
        None,
        description="Optional number of samples represented by this value (if provided).",
    )


def map_datapoint(p: oci.monitoring.models.Datapoint) -> Datapoint | None:
    if not p:
        return None
    return Datapoint(
        timestamp=getattr(p, "timestamp", None),
        value=getattr(p, "value", None),
        count=getattr(p, "count", None),
    )


def map_datapoints(items) -> list[Datapoint] | None:
    if not items:
        return None
    result: list[Datapoint] = []
    for it in items:
        mapped_datapoint = map_datapoint(it)
        if mapped_datapoint is not None:
            result.append(mapped_datapoint)
    return result if result else None


class MetricDataDetails(BaseModel):
    """
    Pydantic model mirroring (a subset of) oci.monitoring.models.MetricDataDetails.
    Represents a single time series being posted to the Monitoring service.
    """

    namespace: Optional[str] = Field(
        None, description="The source service or application emitting the metric."
    )
    resource_group: Optional[str] = Field(None, description="Resource group specified for the metric.")
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the resource."
    )
    name: Optional[str] = Field(None, description="The metric name (for example, CpuUtilization).")
    dimensions: Optional[Dict[str, str]] = Field(
        None,
        description="Dimensions that qualify the metric (for example, resourceId).",
    )
    metadata: Optional[Dict[str, str]] = Field(None, description="Metric metadata such as unit.")
    datapoints: Optional[List[Datapoint]] = Field(None, description="Raw datapoints to post for this metric.")


def map_metric_data_details(
    mdd: oci.monitoring.models.MetricDataDetails,
) -> MetricDataDetails:
    """
    Convert an oci.monitoring.models.MetricDataDetails to
    oracle.oci_monitoring_mcp_server.models.MetricDataDetails.
    """
    return MetricDataDetails(
        namespace=getattr(mdd, "namespace", None),
        resource_group=getattr(mdd, "resource_group", None),
        compartment_id=getattr(mdd, "compartment_id", None),
        name=getattr(mdd, "name", None),
        dimensions=getattr(mdd, "dimensions", None),
        metadata=getattr(mdd, "metadata", None),
        datapoints=map_datapoints(getattr(mdd, "datapoints", None)),
    )


# region List Metrics


class ListMetricsDetails(BaseModel):
    """
    Pydantic model mirroring (a subset of) oci.monitoring.models.ListMetricsDetails.
    Used to filter and group results when listing available metrics.
    """

    namespace: Optional[str] = Field(
        None, description="The source service or application emitting the metric."
    )
    resource_group: Optional[str] = Field(None, description="Resource group specified for the metric.")
    name: Optional[str] = Field(None, description="Optional metric name to filter by (e.g., CpuUtilization).")
    dimension_filters: Optional[Dict[str, str]] = Field(
        None,
        description="Filter to only include metrics that match these dimension key/value pairs.",
    )
    group_by: Optional[List[str]] = Field(
        None,
        description="Optional list of fields to group by in the response (e.g., ['namespace', 'name']).",
    )


def map_list_metrics_details(
    lmd: oci.monitoring.models.ListMetricsDetails,
) -> ListMetricsDetails | None:
    """
    Convert an oci.monitoring.models.ListMetricsDetails to
    oracle.oci_monitoring_mcp_server.models.ListMetricsDetails.
    """
    if not lmd:
        return None
    return ListMetricsDetails(
        namespace=getattr(lmd, "namespace", None),
        resource_group=getattr(lmd, "resource_group", None),
        name=getattr(lmd, "name", None),
        # OCI SDK may expose snake_case or camelCase depending on version
        dimension_filters=getattr(lmd, "dimension_filters", None) or getattr(lmd, "dimensionFilters", None),
        group_by=getattr(lmd, "group_by", None) or getattr(lmd, "groupBy", None),
    )


class SummarizeMetricsDataDetails(BaseModel):
    """
    Pydantic model mirroring (a subset of) oci.monitoring.models.SummarizeMetricsDataDetails.
    Used to request aggregated time series from the Monitoring service.
    """

    namespace: Optional[str] = Field(
        None, description="The source service or application emitting the metric."
    )
    resource_group: Optional[str] = Field(None, description="Resource group specified for the metric.")
    query: Optional[str] = Field(
        None,
        description=(
            "The Monitoring Query Language (MQL) expression, e.g. "
            "'CpuUtilization[1m]{resourceId=\"ocid1.instance...\"}.mean()'"
        ),
    )
    start_time: Optional[datetime] = Field(
        None, description="The beginning of the time window for the metrics (RFC3339)."
    )
    end_time: Optional[datetime] = Field(
        None, description="The end of the time window for the metrics (RFC3339)."
    )
    resolution: Optional[str] = Field(
        None,
        description="The time window used to aggregate metrics, e.g., '1m', '5m', '1h'.",
    )
