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
from fastmcp.server.auth.providers.oci import OCIProvider
from fastmcp.server.dependencies import get_access_token
from fastmcp.utilities.auth import parse_scopes
from oci.usage_api.models import RequestSummarizedUsagesDetails

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def _get_http_config_and_signer():
    if not (os.getenv("ORACLE_MCP_HOST") and os.getenv("ORACLE_MCP_PORT")):
        return None, None
    token = get_access_token()
    if token is None:
        raise RuntimeError("HTTP requests require an authenticated IDCS access token.")
    domain = os.getenv("IDCS_DOMAIN")
    client_id = os.getenv("IDCS_CLIENT_ID")
    client_secret = os.getenv("IDCS_CLIENT_SECRET")
    if not all((domain, client_id, client_secret)):
        raise RuntimeError(
            "HTTP requests require IDCS authentication. Set IDCS_DOMAIN, IDCS_CLIENT_ID, and IDCS_CLIENT_SECRET."
        )
    region = os.getenv("OCI_REGION")
    if not region:
        raise RuntimeError("HTTP requests require OCI_REGION.")
    config = {"region": region}
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    return config, oci.auth.signers.TokenExchangeSigner(
        token.token,
        f"https://{domain}",
        client_id,
        client_secret,
        region=config.get("region"),
    )

def _get_oci_client_kwargs(signer=None):
    kwargs = {
        "circuit_breaker_strategy": oci.circuit_breaker.CircuitBreakerStrategy(
            failure_threshold=int(os.getenv("OCI_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "10")),
            recovery_timeout=int(os.getenv("OCI_CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30")),
        ),
        "circuit_breaker_callback": lambda exc: logger.warning(
            "Circuit breaker triggered: %s", exc
        ),
    }
    if signer is not None:
        kwargs["signer"] = signer
    return kwargs


def get_usage_client():
    logger.info("entering get_monitoring_client")
    config, signer = _get_http_config_and_signer()
    if signer is not None:
        return oci.usage_api.UsageapiClient(config, **_get_oci_client_kwargs(signer))
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
    return oci.usage_api.UsageapiClient(config, **_get_oci_client_kwargs(signer))


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

    response = usage_client.request_summarized_usages(request_summarized_usages_details=summarized_details)
    # Convert UsageSummary objects to dictionaries for proper serialization
    summarized_usages = [oci.util.to_dict(usage_summary) for usage_summary in response.data.items]
    return summarized_usages


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if not (host and port):
        mcp.run()
        return
    domain = os.getenv("IDCS_DOMAIN")
    client_id = os.getenv("IDCS_CLIENT_ID")
    client_secret = os.getenv("IDCS_CLIENT_SECRET")
    base_url = os.getenv("ORACLE_MCP_BASE_URL", "")
    audience = os.getenv("IDCS_AUDIENCE")
    if not all((domain, client_id, client_secret, audience, base_url)):
        raise RuntimeError(
            "HTTP transport requires IDCS authentication. "
            "Set IDCS_DOMAIN, IDCS_CLIENT_ID, IDCS_CLIENT_SECRET, IDCS_AUDIENCE, "
            "ORACLE_MCP_BASE_URL, ORACLE_MCP_HOST, and ORACLE_MCP_PORT."
        )
    mcp.auth = OCIProvider(
        config_url=f"https://{domain}/.well-known/openid-configuration",
        client_id=client_id,
        client_secret=client_secret,
        audience=audience,
        required_scopes=parse_scopes(os.getenv("IDCS_REQUIRED_SCOPES")) or f"openid profile email oci_mcp.{__project__.removeprefix('oracle.oci-').removesuffix('-mcp-server').replace('-', '_')}.invoke".split(),
        base_url=base_url,
    )
    mcp.run(transport="http", host=host, port=int(port))


if __name__ == "__main__":
    main()
