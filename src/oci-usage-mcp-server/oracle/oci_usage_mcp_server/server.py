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
from oci.usage_api.models import RequestSummarizedUsagesDetails

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_usage_client():
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
    return oci.usage_api.UsageapiClient(config, signer=signer)


@mcp.tool
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
) -> list[dict]:
    usage_client = get_usage_client()
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

    response = usage_client.request_summarized_usages(
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
