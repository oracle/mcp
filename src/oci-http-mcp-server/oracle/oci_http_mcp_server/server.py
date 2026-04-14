"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
import os
from logging import Logger
from typing import Annotated, Any

import oci
import requests
from fastmcp import FastMCP

from . import __project__, __version__
from .utils import initAuditLogger

logger = Logger(__project__, level="INFO")

initAuditLogger(logger)

USER_AGENT_NAME = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
USER_AGENT = f"{USER_AGENT_NAME}/{__version__}"
DEFAULT_TIMEOUT_SECONDS = 30
FALSE_VALUES = {"0", "false", "no", "off"}

mcp = FastMCP(
    name=__project__,
    instructions="""
        This server provides tools to invoke OCI REST APIs directly over HTTP using requests.
        Use the resource resource://oci-http-request-guide for examples of signed OCI REST requests.
        Use invoke_oci_http_api to make a signed OCI request.
    """,
)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in FALSE_VALUES


def _get_config_and_signer() -> tuple[dict[str, Any], Any]:
    profile = os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    config = oci.config.from_file(profile_name=profile)
    config["additional_user_agent"] = USER_AGENT

    private_key = oci.signer.load_private_key_from_file(
        config["key_file"],
        config.get("pass_phrase"),
    )

    token_file = os.path.expanduser(config.get("security_token_file", "") or "")
    if token_file and os.path.exists(token_file):
        with open(token_file, "r", encoding="utf-8") as file:
            token = file.read().strip()
        signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
        logger.info("Using SecurityTokenSigner from security_token_file.")
        return config, signer

    signer = oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config["key_file"],
        pass_phrase=config.get("pass_phrase"),
    )
    logger.info("Using API key Signer.")
    return config, signer


def _find_header_key(headers: dict[str, str], header_name: str) -> str | None:
    for key in headers:
        if key.lower() == header_name.lower():
            return key
    return None


def _merge_user_agent(headers: dict[str, str] | None) -> dict[str, str]:
    merged_headers = dict(headers or {})
    header_key = _find_header_key(merged_headers, "User-Agent")
    if header_key is None:
        merged_headers["User-Agent"] = USER_AGENT
        return merged_headers

    if USER_AGENT not in merged_headers[header_key]:
        merged_headers[header_key] = f"{merged_headers[header_key]} {USER_AGENT}"
    return merged_headers


def _prepare_request_body(
    body: Any, headers: dict[str, str] | None
) -> tuple[dict[str, str], Any | None, Any | None]:
    request_headers = _merge_user_agent(headers)
    if body is None:
        return request_headers, None, None

    if isinstance(body, (dict, list)):
        if _find_header_key(request_headers, "Content-Type") is None:
            request_headers["Content-Type"] = "application/json"
        return request_headers, body, None

    if isinstance(body, bytes | str):
        return request_headers, None, body

    if _find_header_key(request_headers, "Content-Type") is None:
        request_headers["Content-Type"] = "application/json"
    return request_headers, None, json.dumps(body)


def _resolve_verify_ssl(verify_ssl: bool | None) -> bool:
    if verify_ssl is not None:
        return verify_ssl
    return _env_bool("OCI_HTTP_VERIFY_SSL", True)


def _build_request_url(
    *,
    path: str | None,
    service: str | None,
    region: str | None,
    endpoint: str | None,
    url: str | None,
    default_region: str | None,
) -> str:
    if url:
        return url
    if path and path.startswith(("https://", "http://")):
        return path
    if not path:
        raise ValueError("path is required when url is not provided.")

    if endpoint:
        base_url = endpoint
    else:
        if not service:
            raise ValueError("service is required when endpoint or url is not provided.")
        resolved_region = region or default_region
        if not resolved_region:
            raise ValueError("region is required when it is not present in the OCI config.")
        base_url = oci.regions.endpoint_for(service, region=resolved_region)

    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _decode_response_body(response: requests.Response) -> Any:
    if not response.content:
        return None

    content_type = response.headers.get("Content-Type", "")
    if "application/json" in content_type.lower():
        return response.json()

    try:
        return response.json()
    except ValueError:
        return response.text


@mcp.resource("resource://oci-http-request-guide")
def get_oci_http_request_guide() -> str:
    """Returns usage guidance for invoking OCI REST APIs directly."""
    return """
Use invoke_oci_http_api to make signed OCI REST requests with your configured OCI principal.

Preferred inputs:
- Provide service plus path for standard OCI regional endpoints.
- Provide url if you already have the full endpoint.
- Use query keys and body fields exactly as the OCI REST API expects them.

Examples:
- List compute instances:
  {
    "method": "GET",
    "service": "iaas",
    "path": "/20160918/instances",
    "query": {"compartmentId": "ocid1.compartment.oc1..example"}
  }

- Get tenancy details:
  {
    "method": "GET",
    "service": "identity",
    "path": "/20160918/tenancies/ocid1.tenancy.oc1..example"
  }

- Create a VCN:
  {
    "method": "POST",
    "service": "iaas",
    "path": "/20160918/vcns",
    "body": {
      "cidrBlock": "10.0.0.0/16",
      "compartmentId": "ocid1.compartment.oc1..example",
      "displayName": "my-vcn"
    }
  }

Pagination is manual. If the response headers include opc-next-page, pass that value back as query.page.
"""


@mcp.tool
def invoke_oci_http_api(
    method: Annotated[str, "HTTP method such as GET, POST, PUT, PATCH, DELETE, or HEAD."],
    path: Annotated[
        str | None,
        "OCI REST path such as /20160918/instances, or a full URL if url is omitted.",
    ] = None,
    service: Annotated[
        str | None,
        "OCI service name such as iaas, identity, monitoring, or objectstorage.",
    ] = None,
    region: Annotated[str | None, "OCI region override such as us-phoenix-1."] = None,
    endpoint: Annotated[str | None, "Explicit service endpoint base URL."] = None,
    url: Annotated[str | None, "Fully-qualified OCI endpoint URL."] = None,
    query: Annotated[dict[str, Any] | None, "Query-string parameters for the request."] = None,
    body: Annotated[Any, "Optional request body. Dictionaries and lists are sent as JSON."] = None,
    headers: Annotated[dict[str, str] | None, "Optional request headers."] = None,
    timeout_seconds: Annotated[int, "Request timeout in seconds. Defaults to 30."] = DEFAULT_TIMEOUT_SECONDS,
    verify_ssl: Annotated[
        bool | None,
        "Override SSL verification. Defaults to OCI_HTTP_VERIFY_SSL or true.",
    ] = None,
) -> dict[str, Any]:
    """Makes a signed OCI REST API request directly through requests."""

    normalized_method = method.upper()
    config, signer = _get_config_and_signer()
    request_url = _build_request_url(
        path=path,
        service=service,
        region=region,
        endpoint=endpoint,
        url=url,
        default_region=config.get("region"),
    )
    request_headers, json_body, data_body = _prepare_request_body(body, headers)
    verify_value = _resolve_verify_ssl(verify_ssl)

    logger.info("invoke_oci_http_api called with method=%s url=%s", normalized_method, request_url)

    request_kwargs: dict[str, Any] = {
        "method": normalized_method,
        "url": request_url,
        "params": query,
        "headers": request_headers,
        "auth": signer,
        "timeout": timeout_seconds,
        "verify": verify_value,
    }
    if json_body is not None:
        request_kwargs["json"] = json_body
    if data_body is not None:
        request_kwargs["data"] = data_body

    try:
        response = requests.request(**request_kwargs)
    except requests.RequestException as exc:
        logger.error("OCI HTTP request failed: %s", exc)
        return {
            "method": normalized_method,
            "url": request_url,
            "status_code": None,
            "ok": False,
            "error": str(exc),
            "error_type": type(exc).__name__,
        }

    return {
        "method": normalized_method,
        "url": request_url,
        "status_code": response.status_code,
        "ok": response.ok,
        "reason": response.reason,
        "opc_request_id": response.headers.get("opc-request-id"),
        "headers": dict(response.headers),
        "data": _decode_response_body(response),
    }


def main():
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
