"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import re
from urllib.parse import urlsplit


_DNS_LABEL = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
_REGION = r"[a-z]{2}(?:-[a-z0-9]+)+-[1-9][0-9]*"


def validate_short_id(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(_DNS_LABEL, value):
        raise ValueError(
            f"{field_name} must be a lowercase alphanumeric short ID with optional internal hyphens."
        )


def validate_region(region: str) -> None:
    if not isinstance(region, str) or not re.fullmatch(_REGION, region):
        raise ValueError("region must be an OCI region identifier such as us-phoenix-1.")


def validate_data_api_url(url: str) -> None:
    # Reject characters URL parsers may normalize differently before inspecting the authority.
    if any(ord(char) <= 32 or char == "\\" for char in url):
        raise ValueError("IoT Data API URL contains invalid characters.")
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    if (
        parsed.scheme != "https"
        or parsed.netloc != host
        or not host.endswith(".oci.oraclecloud.com")
        or not all(re.fullmatch(_DNS_LABEL, label) for label in host.split("."))
        or parsed.fragment
    ):
        raise ValueError(
            "IoT Data API URL must use HTTPS and an OCI host without credentials, ports, or fragments."
        )


def build_identity_token_url(host: str) -> str:
    # ORDS uses IDCS domain URLs, including the regional IAM identity-domain form.
    pattern = rf"{_DNS_LABEL}\.identity(?:\.{_REGION}\.oci)?\.oraclecloud\.com"
    if not isinstance(host, str) or not re.fullmatch(pattern, host):
        raise ValueError("ORDS identity domain host must be an Oracle IAM identity-domain hostname.")
    return f"https://{host}/oauth2/v1/token"
