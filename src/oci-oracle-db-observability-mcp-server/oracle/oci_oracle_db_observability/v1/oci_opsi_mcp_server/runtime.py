"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from functools import lru_cache
from logging import Logger
from typing import Any

import oci
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from oracle.oci_oracle_db_observability.v1.auth import build_client
from oracle.oci_oracle_db_observability.v1.conversion import (
    polymorphic_request_to_sdk_model,
    pydantic_to_sdk_model,
)
from oracle.oci_oracle_db_observability.v1.pagination import call_with_auto_pagination
from oracle.oci_oracle_db_observability.v1.response_mapping import map_response_data

from . import __project__, __version__
from .metadata import REQUEST_MODEL_TYPES

logger = Logger(__name__, level="INFO")


@lru_cache(maxsize=1)
def get_opsi_client() -> oci.opsi.OperationsInsightsClient:
    """Create the OCI Operations Insights SDK client."""

    return build_client(
        oci.opsi.OperationsInsightsClient,
        project=__project__,
        version=__version__,
        logger=logger,
    )


@lru_cache(maxsize=1)
def get_identity_client() -> oci.identity.IdentityClient:
    """Create the OCI Identity SDK client."""

    return build_client(
        oci.identity.IdentityClient,
        project=__project__,
        version=__version__,
        logger=logger,
    )


def normalize_tool_value(value: Any) -> Any:
    """Resolve FastMCP/Pydantic Field defaults when a tool is called directly."""

    if isinstance(value, FieldInfo):
        default = value.get_default(call_default_factory=True)
        return None if default is PydanticUndefined else default
    return value


def _coerce_argument(method_name: str, key: str, value: Any) -> Any:
    value = normalize_tool_value(value)
    if value is None:
        return None
    request_model_name = REQUEST_MODEL_TYPES.get((method_name, key))
    if request_model_name is not None:
        sdk_type = getattr(oci.opsi.models, request_model_name)
        return polymorphic_request_to_sdk_model(value, sdk_type)
    if isinstance(value, BaseModel):
        sdk_type = getattr(oci.opsi.models, value.__class__.__name__, None)
        if sdk_type is not None:
            return pydantic_to_sdk_model(value, sdk_type)
        return value.model_dump(by_alias=True, exclude_none=True)
    if isinstance(value, list):
        return [_coerce_argument(method_name, key, item) for item in value]
    if isinstance(value, dict):
        return {
            item_key: _coerce_argument(method_name, item_key, item)
            for item_key, item in value.items()
            if item is not None
        }
    return value


def invoke_opsi(method_name: str, **kwargs: Any) -> Any:
    """Invoke an OPSI SDK method and map the SDK response for MCP."""

    client = get_opsi_client()
    method = getattr(client, method_name)
    sdk_kwargs = {}
    for key, value in kwargs.items():
        coerced_value = _coerce_argument(method_name, key, value)
        if coerced_value is not None:
            sdk_kwargs[key] = coerced_value
    try:
        response = call_with_auto_pagination(method, sdk_kwargs)
        return map_response_data(getattr(response, "data", None))
    except Exception as exc:
        logger.error("Error in OPSI tool %s: %s", method_name, exc)
        raise


def invoke_identity(method_name: str, **kwargs: Any) -> Any:
    """Invoke an OCI Identity SDK method and map the SDK response for MCP."""

    client = get_identity_client()
    method = getattr(client, method_name)
    sdk_kwargs = {}
    for key, value in kwargs.items():
        coerced_value = _coerce_argument(method_name, key, value)
        if coerced_value is not None:
            sdk_kwargs[key] = coerced_value
    try:
        response = call_with_auto_pagination(method, sdk_kwargs)
        return map_response_data(getattr(response, "data", None))
    except Exception as exc:
        logger.error("Error in Identity tool %s: %s", method_name, exc)
        raise
