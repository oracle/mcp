"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
import re
from typing import Optional

_JMS_TEST_ENVIRONMENT = "JMS_TEST_ENVIRONMENT"
_JMS_TEST_ENV_NAME = re.compile(r"^([a-zA-Z0-9]+)([_-]+[\w-]*)?$")
_SUPPORTED_JMS_ENVIRONMENTS = {
    "PROD",
    "HERDS",
    "DEV",
    "DEV2",
    "DEV3",
    "TEST",
    "TEST2",
    "TEST3",
    "STAGE",
    "VANILLA",
}


def get_jms_environment(value: Optional[str]) -> Optional[str]:
    """Parse the JMS environment selector, allowing Java-style optional suffixes."""
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        return None

    match = _JMS_TEST_ENV_NAME.match(normalized)
    if not match:
        raise ValueError(
            f"Unable to parse {_JMS_TEST_ENVIRONMENT}={value!r}; expected a base environment name "
            "such as PROD, HERDS, DEV, DEV2, DEV3, TEST, TEST2, TEST3, STAGE, or VANILLA."
        )

    environment = match.group(1).upper()
    if environment not in _SUPPORTED_JMS_ENVIRONMENTS:
        supported = ", ".join(sorted(_SUPPORTED_JMS_ENVIRONMENTS))
        raise ValueError(
            f"Unsupported {_JMS_TEST_ENVIRONMENT} base environment {environment!r}; "
            f"supported values are: {supported}."
        )

    return environment


def get_jms_service_endpoint(config: dict, environment_value: Optional[str] = None) -> Optional[str]:
    """Derive a Java-style JMS service endpoint override for non-prod environments."""
    environment = get_jms_environment(
        os.getenv(_JMS_TEST_ENVIRONMENT) if environment_value is None else environment_value
    )
    if environment is None or environment == "PROD":
        return None

    region = config.get("region")
    if not region:
        raise ValueError(
            f"{_JMS_TEST_ENVIRONMENT} is set to {environment!r} but the OCI config does not "
            "contain a region."
        )

    if environment == "HERDS":
        return f"https://javamanagement-herds.{region}.oci.rbcloud.oc-test.com"

    return f"https://javamanagement-{environment.lower()}.{region}.oci.oc-test.com"
