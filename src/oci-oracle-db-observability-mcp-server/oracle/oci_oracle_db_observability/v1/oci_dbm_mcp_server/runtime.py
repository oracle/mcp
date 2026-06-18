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
from .metadata import METHOD_CLIENTS, REQUEST_MODEL_TYPES

logger = Logger(__name__, level="INFO")


@lru_cache(maxsize=1)
def get_db_management_client() -> oci.database_management.DbManagementClient:
    """Create the OCI Database Management DbManagementClient SDK client."""

    return build_client(
        oci.database_management.DbManagementClient,
        project=__project__,
        version=__version__,
        logger=logger,
    )


@lru_cache(maxsize=1)
def get_diagnosability_client() -> oci.database_management.DiagnosabilityClient:
    """Create the OCI Database Management DiagnosabilityClient SDK client."""

    return build_client(
        oci.database_management.DiagnosabilityClient,
        project=__project__,
        version=__version__,
        logger=logger,
    )




@lru_cache(maxsize=1)
def get_sql_tuning_client() -> oci.database_management.SqlTuningClient:
    """Create the OCI Database Management SqlTuningClient SDK client."""

    return build_client(
        oci.database_management.SqlTuningClient,
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


CLIENT_GETTERS = {
    'DbManagementClient': get_db_management_client,
    'DiagnosabilityClient': get_diagnosability_client,
    'SqlTuningClient': get_sql_tuning_client,
}


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
        sdk_type = getattr(oci.database_management.models, request_model_name)
        return polymorphic_request_to_sdk_model(value, sdk_type)
    if isinstance(value, BaseModel):
        sdk_type = getattr(oci.database_management.models, value.__class__.__name__, None)
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


def _invoke(method_name: str, client: Any, service_name: str, **kwargs: Any) -> Any:
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
        logger.error("Error in %s tool %s: %s", service_name, method_name, exc)
        raise


def invoke_dbm(method_name: str, **kwargs: Any) -> Any:
    """Invoke a DBM SDK method on the correct Database Management client."""

    client_name = METHOD_CLIENTS[method_name]
    return _invoke(method_name, CLIENT_GETTERS[client_name](), client_name, **kwargs)


def invoke_identity(method_name: str, **kwargs: Any) -> Any:
    """Invoke an OCI Identity SDK method and map the SDK response for MCP."""

    return _invoke(method_name, get_identity_client(), "Identity", **kwargs)
