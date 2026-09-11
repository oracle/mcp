"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Single allowlisted OCI Python SDK dispatcher.
"""
from __future__ import annotations

import inspect
import json
from copy import copy
from datetime import datetime
from functools import lru_cache
from typing import Any, Mapping, get_args, get_origin

import oci
from jsonschema import Draft202012Validator
from fastmcp.server.dependencies import get_access_token
from oracle_mcp_common import IDCSHttpAuth, build_auth_context

from . import __project__, __version__
from .metric_catalog import MetricCatalogError, load_metric_catalog
from .registry import client_class, compartment_requirements
from .sdk_schema import parameter_docs

_USER_AGENT = f"{__project__.split('oracle.', 1)[1].removesuffix('-server')}/{__version__}"
_http_auth: IDCSHttpAuth | None = None


def configure_http_auth(policy: IDCSHttpAuth) -> None:
    """Configure caller-scoped OCI authentication for HTTP transport."""
    global _http_auth
    _http_auth = policy


def _get_http_config_and_signer(access_token: Any) -> tuple[dict[str, Any], Any]:
    """Build caller-specific OCI SDK authentication for one HTTP request."""
    if _http_auth is None:
        raise RuntimeError("HTTP authentication policy has not been initialized.")
    context = _http_auth.context_for(access_token.token if access_token else None)
    return ({**context.config, "additional_user_agent": _USER_AGENT}, context.signer)


def _get_config_and_signer(access_token: Any | None = None) -> tuple[dict[str, Any], Any]:
    """Resolve HTTP caller credentials or configured stdio OCI credentials."""
    if access_token is not None:
        return _get_http_config_and_signer(access_token)
    context = build_auth_context()
    return ({**context.config, "additional_user_agent": _USER_AGENT}, context.signer)


@lru_cache(maxsize=None)
def _stdio_client(service: str, client_name: str) -> Any:
    config, signer = _get_config_and_signer()
    return client_class(service, client_name)(config, signer=signer)


def _client(service: str, client_name: str) -> Any:
    access_token = get_access_token()
    if access_token is None:
        return _stdio_client(service, client_name)
    config, signer = _get_config_and_signer(access_token)
    return client_class(service, client_name)(config, signer=signer)


def identity_bootstrap_client() -> Any:
    """Create the Identity client for explicit compartment lookups."""
    config, signer = _get_config_and_signer(get_access_token())
    client = client_class("identity", "IdentityClient")(config, signer=signer)
    return client


def _serialize_data(data: Any) -> Any:
    """Convert a response payload to a JSON-safe value."""
    try:
        return json.loads(json.dumps(oci.util.to_dict(data), default=str))
    except Exception:
        return str(data)


def serialize_response(response: Any) -> dict[str, Any]:
    """Convert an OCI SDK response to JSON-safe data and pagination metadata."""
    data = getattr(response, "data", response)
    headers = getattr(response, "headers", {}) or {}
    return {"data": _serialize_data(data), "nextPage": headers.get("opc-next-page")}


def _models_module(client: type[Any]) -> Any:
    module = client.__module__.rsplit(".", 1)[0]
    try:
        return __import__(f"{module}.models", fromlist=["models"])
    except ImportError:
        return None


def _type_name(annotation: Any) -> str | None:
    if isinstance(annotation, str):
        return annotation
    if annotation is inspect.Signature.empty:
        return None
    if isinstance(annotation, type):
        return annotation.__name__
    origin = get_origin(annotation)
    args = [arg for arg in get_args(annotation) if arg is not type(None)]
    return _type_name(args[0]) if origin and len(args) == 1 else None


def _coerce(value: Any, type_name: str | None, models: Any) -> Any:
    if value is None or not type_name or not isinstance(value, dict) or models is None:
        return value
    model = getattr(models, type_name.rsplit(".", 1)[-1], None)
    if not inspect.isclass(model):
        return value
    model = getattr(models, value.get("model_type", ""), model)
    payload = {key: item for key, item in value.items() if key != "model_type"}
    swagger = getattr(model, "swagger_types", {})
    payload = {key: _coerce(item, swagger.get(key), models) for key, item in payload.items()}
    from_dict = getattr(oci.util, "from_dict", None)
    if not callable(from_dict):
        return model(**payload)
    try:
        return from_dict(model, payload)
    except (TypeError, ValueError):
        return model(**payload)


def _coerce_arguments(client: Any, operation: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
    method = getattr(client, operation)
    models = _models_module(client.__class__)
    signature = inspect.signature(method)
    docs = parameter_docs(method)
    coerced: dict[str, Any] = {}
    for key, value in arguments.items():
        parameter = signature.parameters.get(key)
        type_name = _type_name(parameter.annotation) if parameter and parameter.kind is not inspect.Parameter.VAR_KEYWORD else None
        if type_name is None and key in docs:
            type_name = docs[key][0]
        coerced[key] = _coerce(value, type_name, models)
    return coerced


def _require_compartment_scope(tool: Mapping[str, Any], arguments: Mapping[str, Any]) -> None:
    """Give actionable guidance when a required catalog scope is missing."""
    for requirement in compartment_requirements(tool):
        argument = requirement["argument"]
        if requirement["required"] and not arguments.get(argument):
            raise ValueError(
                f"{tool['name']} requires {argument}. Ask the user for a compartment OCID, or for a "
                "configured compartment discovery root to resolve a supplied compartment name. Do not invent an OCID."
            )


def _validate_compartment_scope(tool: Mapping[str, Any], arguments: Mapping[str, Any]) -> None:
    """Reject invalid or inaccessible catalog compartment scopes before dispatch."""
    requirements = compartment_requirements(tool)
    values = {str(arguments[requirement["argument"]]) for requirement in requirements if arguments.get(requirement["argument"])}
    if not values:
        return
    client = identity_bootstrap_client()
    for compartment_id in values:
        try:
            client.get_compartment(compartment_id=compartment_id)
        except oci.exceptions.ServiceError as exc:
            if exc.code == "NotAuthorizedOrNotFound" or exc.status in {403, 404}:
                raise ValueError(
                    f"The supplied compartment OCID {compartment_id} is invalid or inaccessible to the configured "
                    "OCI identity. Ask the user for a valid compartment OCID, or use a configured compartment "
                    "discovery root to resolve a compartment name."
                ) from exc
            raise RuntimeError(f"Unable to validate compartment OCID {compartment_id}: {exc}") from exc


def _metric_mql(arguments: Mapping[str, Any]) -> str:
    def quote(value: str) -> str:
        return f'"{value.replace("\\", "\\\\").replace(chr(34), "\\\"")}"'

    filters = ", ".join(
        f"{name} = {quote(value)}"
        for name, value in sorted(arguments.get("dimension_filters", {}).items())
    )
    selector = f'{arguments["metric_name"]}[{arguments["interval"]}]'
    grouping = f'.groupBy({arguments["group_by"]})' if arguments.get("group_by") else ""
    return f"{selector}{{{filters}}}{grouping}.{arguments['aggregation']}()" if filters else f"{selector}{grouping}.{arguments['aggregation']}()"


def _parse_metric_time(value: str, field: str) -> datetime:
    """Parse the required RFC 3339 metric window boundary."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an RFC 3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a UTC offset")
    return parsed


def _monitoring_duration(value: str) -> int:
    """Convert a schema-validated OCI Monitoring duration into minutes."""
    amount, unit = int(value[:-1]), value[-1]
    return amount * {"m": 1, "h": 60, "d": 60 * 24}[unit]


def _limit_metric_streams(data: Any, max_results: int) -> list[Any]:
    """Bound both metric streams and their aggregate datapoints before serialization."""
    if not isinstance(data, list):
        return data
    limited: list[Any] = []
    remaining_datapoints = max_results
    for stream in data[:max_results]:
        datapoints = stream.get("aggregated_datapoints") if isinstance(stream, Mapping) else getattr(stream, "aggregated_datapoints", None)
        if isinstance(datapoints, list):
            if remaining_datapoints <= 0:
                break
            stream = dict(stream) if isinstance(stream, Mapping) else copy(stream)
            bounded_datapoints = datapoints[:remaining_datapoints]
            if isinstance(stream, dict):
                stream["aggregated_datapoints"] = bounded_datapoints
            else:
                stream.aggregated_datapoints = bounded_datapoints
            remaining_datapoints -= len(bounded_datapoints)
        limited.append(stream)
    return limited


def _invoke_metric_read(tool: Mapping[str, Any], arguments: Mapping[str, Any]) -> dict[str, Any]:
    catalog = load_metric_catalog()
    metric = catalog.get([{"namespace": arguments["namespace"], "name": arguments["metric_name"]}])["items"]
    if not metric:
        raise ValueError(f"Metric {arguments['namespace']}/{arguments['metric_name']} is not available in catalog {catalog.catalog_id}.")
    supported_dimensions = set(metric[0].get("dimensions", []))
    dimension_filters = arguments.get("dimension_filters", {})
    if not isinstance(dimension_filters, Mapping) or not all(isinstance(name, str) and isinstance(value, str) for name, value in dimension_filters.items()):
        raise ValueError("dimension_filters must map dimension names to string values")
    requested_dimensions = set(dimension_filters)
    if arguments.get("group_by"):
        requested_dimensions.add(arguments["group_by"])
    unsupported = sorted(requested_dimensions - supported_dimensions)
    if unsupported:
        raise ValueError(f"Unsupported dimensions for {arguments['namespace']}/{arguments['metric_name']}: {', '.join(unsupported)}")
    start_time = _parse_metric_time(arguments["start_time"], "start_time")
    end_time = _parse_metric_time(arguments["end_time"], "end_time")
    if start_time >= end_time:
        raise ValueError("start_time must be earlier than end_time")
    if _monitoring_duration(arguments["resolution"]) > _monitoring_duration(arguments["interval"]):
        raise ValueError("resolution must not exceed interval")
    client = _client(str(tool["service"]), str(tool["client"]))
    details = oci.monitoring.models.SummarizeMetricsDataDetails(
        namespace=arguments["namespace"],
        query=_metric_mql(arguments),
        resolution=arguments["resolution"],
        start_time=start_time,
        end_time=end_time,
        resource_group=arguments.get("resource_group"),
    )
    try:
        response = client.summarize_metrics_data(
            compartment_id=arguments["compartment_id"],
            summarize_metrics_data_details=details,
            compartment_id_in_subtree=arguments.get("compartment_id_in_subtree"),
        )
    except Exception as exc:
        raise RuntimeError(f"OCI operation {tool['name']} failed: {exc}") from exc
    max_results = arguments.get("max_results")
    if max_results is None:
        result = serialize_response(response)
    else:
        result = {
            "data": _serialize_data(_limit_metric_streams(getattr(response, "data", response), max_results)),
            "nextPage": (getattr(response, "headers", {}) or {}).get("opc-next-page"),
        }
    result["mql"] = _metric_mql(arguments)
    return result


def _invoke_metadata_tool(tool: Mapping[str, Any], arguments: Mapping[str, Any]) -> dict[str, Any]:
    catalog = load_metric_catalog()
    try:
        handler = str(tool["handler"]).rsplit(".", 1)[-1]
        return getattr(catalog, handler)(**arguments)
    except (AttributeError, MetricCatalogError) as exc:
        raise RuntimeError(f"Metadata tool {tool['name']} failed: {exc}") from exc


def invoke_registered_tool(tool: Mapping[str, Any], arguments: dict[str, Any]) -> Any:
    if not isinstance(arguments, dict):
        raise ValueError("arguments must be a JSON object")
    _require_compartment_scope(tool, arguments)
    errors = sorted(Draft202012Validator(dict(tool["inputSchema"])).iter_errors(arguments), key=lambda error: list(error.path))
    if errors:
        raise ValueError(f"Invalid arguments: {errors[0].message}")
    _validate_compartment_scope(tool, arguments)
    if tool.get("kind") == "metadata":
        return _invoke_metadata_tool(tool, arguments)
    if tool.get("adapter") == "monitoring.metric_read":
        return _invoke_metric_read(tool, arguments)
    client = _client(str(tool["service"]), str(tool["client"]))
    try:
        response = getattr(client, tool["operation"])(**_coerce_arguments(client, str(tool["operation"]), arguments))
    except Exception as exc:
        raise RuntimeError(f"OCI operation {tool['name']} failed: {exc}") from exc
    return serialize_response(response)
