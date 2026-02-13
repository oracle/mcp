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
from oci.usage_api import UsageapiClient
from oci.usage_api.models import RequestSummarizedUsagesDetails
from oracle.mcp_common import with_oci_client

from . import __project__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


@mcp.tool
@with_oci_client(UsageapiClient)
def get_summarized_usage(
    tenant_id: Annotated[str, "Tenancy OCID"],
    start_time: Annotated[
        str,
        "The value to assign to the time_usage_started property of this RequestSummarizedUsagesDetails."
        "UTC date must have the right precision: hours, minutes, seconds, and second fractions must be 0",
    ],
    end_time: Annotated[
        str,
        "The value to assign to the time_usage_ended property of this RequestSummarizedUsagesDetails."
        "UTC date must have the right precision: hours, minutes, seconds, and second fractions must be 0",
    ],
    group_by: Annotated[
        list[str],
        "Aggregate the result by."
        "Allows values are “tagNamespace”, “tagKey”, “tagValue”, “service”,"
        "“skuName”, “skuPartNumber”, “unit”, “compartmentName”, “compartmentPath”, “compartmentId”"
        "“platform”, “region”, “logicalAd”, “resourceId”, “tenantId”, “tenantName”",
    ],
    compartment_depth: Annotated[float, "The compartment depth level."],
    granularity: Annotated[
        str,
        'Allowed values for this property are: "HOURLY", "DAILY", "MONTHLY". Default: "DAILY"',
    ] = "DAILY",
    query_type: Annotated[
        str,
        'Allowed values are: "USAGE", "COST", "CREDIT", "EXPIREDCREDIT", "ALLCREDIT", "OVERAGE"'
        'Default: "COST"',
    ] = "COST",
    is_aggregate_by_time: Annotated[
        bool,
        "Specifies whether aggregated by time. If isAggregateByTime is true,"
        "all usage or cost over the query time period will be added up.",
    ] = False,
    *,
    client: UsageapiClient,
) -> list[dict]:
    summarized_details = RequestSummarizedUsagesDetails(
        tenant_id=tenant_id,
        time_usage_started=start_time,
        time_usage_ended=end_time,
        granularity=granularity,
        is_aggregate_by_time=is_aggregate_by_time,
        query_type=query_type,
        group_by=group_by,
        compartment_depth=compartment_depth,
    )

    response = client.request_summarized_usages(
        request_summarized_usages_details=summarized_details
    )
    # Convert UsageSummary objects to dictionaries for proper serialization
    summarized_usages = [
        oci.util.to_dict(usage_summary) for usage_summary in response.data.items
    ]
    return summarized_usages


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
