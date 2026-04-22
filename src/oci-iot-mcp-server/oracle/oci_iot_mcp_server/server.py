"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Annotated, Any, Optional
from urllib.parse import urlencode

import httpx
import oci
from fastmcp import FastMCP
from oci.exceptions import ConfigFileNotFound, InvalidConfig
from pydantic import TypeAdapter

from . import __project__, __version__
from .agent_workflows import (
    get_latest_twin_state_impl,
    get_twin_platform_context_impl,
    validate_twin_readiness_impl,
)
from .auth import PRINCIPAL_AUTH_TYPES, build_auth_context, get_default_region, resolved_auth_type, resolved_profile_name
from .client import get_iot_client
from .control_plane import (
    get_digital_twin_adapter_record,
    get_digital_twin_instance_content_record,
    get_digital_twin_instance_record,
    get_digital_twin_model_record,
    get_digital_twin_model_spec_record,
    get_digital_twin_relationship_record,
    get_iot_domain_group_record,
    get_iot_domain_record,
    get_work_request_record,
    list_digital_twin_adapters_records,
    list_digital_twin_instances_records,
    list_digital_twin_models_records,
    list_digital_twin_relationships_records,
    list_iot_domain_groups_records,
    list_iot_domains_records,
    list_work_request_errors_records,
    list_work_request_logs_records,
    list_work_requests_records,
)
from .data_plane import (
    DataApiTokenError,
    build_ords_base_url,
    get_cached_data_api_token,
    get_raw_command_record,
    list_raw_command_records,
    list_rejected_data_records,
    list_snapshot_records,
    require_token_credentials,
)
from .domain_context import resolve_domain_context_for_tool
from .errors import ambiguity_error, error_result, invalid_input_error, not_found_error
from .polling import wait_for_raw_command_terminal_state, wait_for_snapshot_update
from .resolvers import resolve_twin_for_tool
from .tool_models import success_result

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create FastMCP instance
mcp = FastMCP(name=__project__)
JSON_ADAPTER = TypeAdapter(Any)
IOT_DATA_API_TIMEOUT_SECONDS = 30.0


def tool(*, description: str):
    def decorator(func):
        mcp.tool(description=description)(func)
        return func

    return decorator


def _normalize_items(data):
    if hasattr(data, "items"):
        return list(data.items)
    if isinstance(data, (list, tuple)):
        return list(data)
    if data is None:
        return []
    return [data]


def _parse_json_input(value, field_name: str):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            logger.error(f"Invalid JSON for {field_name}: {exc}")
            raise ValueError(f"Invalid JSON for {field_name}: {exc}") from exc
    return value


def _response_to_dict(response):
    headers = dict(getattr(response, "headers", {}) or {})
    request_id = getattr(response, "request_id", None) or headers.get("opc-request-id")
    return {
        "status": getattr(response, "status", None),
        "request_id": request_id,
        "headers": headers,
        "data": getattr(response, "data", None),
    }


def _result_payload(value):
    return {"result": value}


@lru_cache(maxsize=None)
def _get_identity_client_for_profile(profile_name: str, auth_type: str | None = None):
    logger.info(f"Creating Identity client for profile: {profile_name}")
    auth_context = build_auth_context(profile_name=profile_name, auth_type=auth_type)
    identity_client = oci.identity.IdentityClient(auth_context.config, signer=auth_context.signer)
    if not auth_context.tenancy_id:
        raise ValueError(f"Authentication mode '{auth_context.auth_type}' did not provide a tenancy OCID")
    return identity_client, auth_context.tenancy_id


def get_identity_client(
    profile_name: Annotated[Optional[str], "Stored/Authenticated OCI Profile"] = None,
    auth_type: Annotated[Optional[str], "OCI authentication type override"] = None,
):
    resolved_profile = resolved_profile_name(profile_name)
    resolved_type = resolved_auth_type(auth_type)
    try:
        return _get_identity_client_for_profile(resolved_profile, resolved_type)
    except ConfigFileNotFound as exc:
        logger.error(f"OCI config file not found: {exc}")
        raise
    except InvalidConfig as exc:
        logger.error(f"Invalid OCI configuration: {exc}")
        raise
    except Exception as exc:
        logger.error(f"Error creating Identity client: {exc}")
        raise


def _get_oci_config(profile_name: Optional[str] = None):
    return oci.config.from_file(profile_name=resolved_profile_name(profile_name))


def _get_iot_data_api_access_token(access_token: Optional[str] = None):
    token = access_token or os.getenv("OCI_IOT_DATA_API_ACCESS_TOKEN")
    if not token:
        raise ValueError(
            "IoT Data API access token is required. Pass access_token or set OCI_IOT_DATA_API_ACCESS_TOKEN."
        )
    return token


def _normalize_query_params(query_params: Optional[dict[str, Any] | str]):
    params = _parse_json_input(query_params, "query_params")
    if params is None:
        return {}
    if not isinstance(params, dict):
        raise ValueError("query_params must be a dictionary or JSON object string")

    normalized = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            normalized[key] = str(value).lower()
        elif isinstance(value, (dict, list)):
            normalized[key] = json.dumps(value)
        else:
            normalized[key] = value
    return normalized


def _build_iot_data_api_url(
    iot_domain_group_short_id: str,
    iot_domain_short_id: str,
    resource_path: str,
    region: Optional[str] = None,
):
    if region is None:
        auth_type = resolved_auth_type()
        if auth_type in PRINCIPAL_AUTH_TYPES:
            region = get_default_region(auth_type=auth_type)
        else:
            config = _get_oci_config()
            region = config.get("region")

    base_url = (
        f"https://{iot_domain_group_short_id}.data.iot.{region}.oci.oraclecloud.com"
        f"/ords/{iot_domain_short_id}"
    )
    return f"{base_url}{resource_path}"


def _call_iot_data_api(
    *,
    resource_path: str,
    iot_domain_group_short_id: str,
    iot_domain_short_id: str,
    query_params: Optional[dict[str, Any] | str] = None,
    region: Optional[str] = None,
    access_token: Optional[str] = None,
    opc_request_id: Optional[str] = None,
):
    try:
        token = _get_iot_data_api_access_token(access_token)
    except ValueError:
        return error_result(
            code="missing_access_token",
            message="IoT Data API access token is required.",
            retry_hint="Pass access_token or set OCI_IOT_DATA_API_ACCESS_TOKEN, then retry.",
        )
    url = _build_iot_data_api_url(
        iot_domain_group_short_id=iot_domain_group_short_id,
        iot_domain_short_id=iot_domain_short_id,
        resource_path=resource_path,
        region=region,
    )

    normalized_query_params = _normalize_query_params(query_params)
    if normalized_query_params:
        url = f"{url}?{urlencode(normalized_query_params, doseq=True)}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if opc_request_id is not None:
        headers["opc-request-id"] = opc_request_id

    try:
        response = httpx.get(
            url,
            headers=headers,
            timeout=IOT_DATA_API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text
    except httpx.TimeoutException as exc:
        logger.error(f"IoT Data API request timed out for {url}: {exc}")
        return error_result(
            code="data_plane_timeout",
            message="IoT Data API request timed out.",
            retry_hint="Retry the request. If it persists, verify Data API connectivity and region settings.",
            details={"url": url},
        )
    except httpx.HTTPStatusError as exc:
        response = exc.response
        error_body = response.text
        logger.error(f"IoT Data API request failed for {url}: {response.status_code} {error_body}")
        return error_result(
            code="data_plane_http_error",
            message=f"IoT Data API request failed with status {response.status_code}.",
            retry_hint="Verify the token, domain short IDs, and request parameters, then retry.",
            details={
                "url": str(exc.request.url),
                "status_code": response.status_code,
                "response_body": error_body,
            },
        )
    except httpx.RequestError as exc:
        request_url = str(exc.request.url) if exc.request is not None else url
        logger.error(f"IoT Data API request failed for {request_url}: {exc}")
        return error_result(
            code="data_plane_request_error",
            message="IoT Data API request failed before receiving a response.",
            retry_hint="Verify Data API connectivity, DNS, and TLS settings, then retry.",
            details={"url": request_url, "reason": str(exc)},
        )


def _delegate(message: str, func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"{message}: {e}")
        raise


def _is_error(payload) -> bool:
    return isinstance(payload, dict) and payload.get("ok") is False


def _as_tool_result(payload):
    if isinstance(payload, dict) and payload.get("ok") is False:
        return payload
    if isinstance(payload, dict) and payload.get("ok") is True and "data" in payload:
        return JSON_ADAPTER.dump_python(payload, mode="json", fallback=oci.util.to_dict)
    return success_result(JSON_ADAPTER.dump_python(payload, mode="json", fallback=oci.util.to_dict))


def _limit_error(*, field_name: str, value: int):
    if 1 <= value <= 100:
        return None
    return error_result(
        code="invalid_input",
        message=f"{field_name} must be between 1 and 100.",
        retry_hint=f"Retry with {field_name} set between 1 and 100.",
        details={field_name: value},
    )


def _parse_rfc3339(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _in_time_window(value: str | None, since: str | None, until: str | None) -> bool:
    observed = _parse_rfc3339(value)
    if observed is None:
        return since is None and until is None
    if since and observed < _parse_rfc3339(since):
        return False
    if until and observed > _parse_rfc3339(until):
        return False
    return True


def _sort_desc(rows: list[dict], field_name: str) -> list[dict]:
    floor = datetime.min.replace(tzinfo=UTC)
    return sorted(
        rows,
        key=lambda row: _parse_rfc3339(row.get(field_name)) or floor,
        reverse=True,
    )


def _resolve_data_plane_access(**selectors):
    domain_context = resolve_domain_context_for_tool(**selectors)
    if _is_error(domain_context):
        return domain_context

    credentials = require_token_credentials(os.environ)
    if _is_error(credentials):
        return credentials

    try:
        token = get_cached_data_api_token(
            domain_context=domain_context,
            env=os.environ,
            now=lambda: datetime.now(UTC),
        )
    except DataApiTokenError as exc:
        return error_result(
            code=exc.code,
            message=str(exc),
            retry_hint=exc.retry_hint,
            details=exc.details,
        )
    except Exception as exc:
        return error_result(
            code="data_plane_error",
            message="Failed to mint an IoT Data API bearer token.",
            retry_hint="Verify the ORDS credentials and domain access, then retry.",
            details={"reason": str(exc)},
        )

    return domain_context, token


def _resolve_twin_with_data_plane_access(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
):
    twin = resolve_twin_for_tool(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    if _is_error(twin):
        return twin

    access = _resolve_data_plane_access(digital_twin_instance_id=twin["id"])
    if _is_error(access):
        return access

    domain_context, token = access
    return twin, domain_context, token


def get_data_api_token_impl(
    *,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
):
    access = _resolve_data_plane_access(
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    if _is_error(access):
        return access

    domain_context, token = access
    return {**domain_context, **token.model_dump()}


def get_raw_command_by_request_id_impl(
    *,
    request_id: str,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    since: str | None = None,
    until: str | None = None,
):
    access = _resolve_data_plane_access(
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
    )
    if _is_error(access):
        return access

    domain_context, token = access
    try:
        record = get_raw_command_record(
            base_url=build_ords_base_url(domain_context),
            token=token.access_token,
            request_id=request_id,
        )
    except Exception as exc:
        return error_result(
            code="data_plane_error",
            message="Failed to fetch the raw command detail record.",
            retry_hint="Verify the request_id and domain selector, then retry.",
            details={"request_id": request_id, "reason": str(exc)},
        )

    if digital_twin_instance_id or digital_twin_instance_name:
        twin = resolve_twin_for_tool(
            digital_twin_instance_id=digital_twin_instance_id,
            digital_twin_instance_name=digital_twin_instance_name,
            iot_domain_id=iot_domain_id,
            iot_domain_display_name=iot_domain_display_name,
            domain_short_id=domain_short_id,
            compartment_id=compartment_id,
        )
        if _is_error(twin):
            return twin
        if record.get("digital_twin_instance_id") != twin["id"]:
            return not_found_error(
                resource_type="raw_command",
                message="The raw command record did not match the provided twin selector.",
                input_payload={
                    "request_id": request_id,
                    "digital_twin_instance_id": digital_twin_instance_id,
                    "digital_twin_instance_name": digital_twin_instance_name,
                },
            )

    try:
        if not _in_time_window(record.get("time_created"), since, until):
            return not_found_error(
                resource_type="raw_command",
                message="The raw command record did not match the provided time window.",
                input_payload={
                    "request_id": request_id,
                    "since": since,
                    "until": until,
                },
            )
    except ValueError:
        return invalid_input_error(
            resource_type="raw_command",
            message="since and until must be RFC 3339 timestamps when provided.",
            input_payload={"since": since, "until": until},
            retry_hint="Retry with RFC 3339 timestamps for since and until.",
        )

    return record


def list_recent_raw_commands_for_twin_impl(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
    limit: int = 20,
    since: str | None = None,
    until: str | None = None,
):
    resolved = _resolve_twin_with_data_plane_access(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    if _is_error(resolved):
        return resolved

    twin, domain_context, token = resolved
    try:
        rows = list_raw_command_records(
            base_url=build_ords_base_url(domain_context),
            token=token.access_token,
            digital_twin_instance_id=twin["id"],
            target_count=500 if since or until else max(limit, 20),
        )
    except Exception as exc:
        return error_result(
            code="data_plane_error",
            message="Failed to list recent raw command records.",
            retry_hint="Verify the twin selector and domain access, then retry.",
            details={"reason": str(exc)},
        )

    try:
        return [
            row
            for row in rows
            if row.get("digital_twin_instance_id") == twin["id"]
            and _in_time_window(row.get("time_created"), since, until)
        ]
    except ValueError:
        return invalid_input_error(
            resource_type="raw_command",
            message="since and until must be RFC 3339 timestamps when provided.",
            input_payload={"since": since, "until": until},
            retry_hint="Retry with RFC 3339 timestamps for since and until.",
        )


def _candidate_matches_invoke(
    *,
    row: dict,
    twin_id: str,
    request_endpoint: str,
    request_data_format: str,
    response_endpoint: str | None,
    request_duration: str | None,
    response_duration: str | None,
    invoke_started_at: datetime,
) -> bool:
    if row.get("digital_twin_instance_id") != twin_id:
        return False
    if row.get("request_endpoint") != request_endpoint:
        return False
    if (row.get("request_data_format") or "").upper() != request_data_format.upper():
        return False
    if response_endpoint is not None and row.get("response_endpoint") != response_endpoint:
        return False
    if request_duration is not None and row.get("request_duration") != request_duration:
        return False
    if response_duration is not None and row.get("response_duration") != response_duration:
        return False
    created = _parse_rfc3339(row.get("time_created"))
    if created and created < invoke_started_at - timedelta(seconds=5):
        return False
    return True


def invoke_raw_command_and_wait_impl(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
    request_endpoint: str,
    request_data_format: str,
    request_data: object,
    response_endpoint: str | None = None,
    request_duration: str | None = None,
    response_duration: str | None = None,
    timeout: int = 30,
):
    resolved = _resolve_twin_with_data_plane_access(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    if _is_error(resolved):
        return resolved

    twin, domain_context, token = resolved
    invoke_started_at = datetime.now(UTC)
    try:
        invoke_metadata = invoke_raw_command(
            digital_twin_instance_id=twin["id"],
            request_endpoint=request_endpoint,
            request_data_format=request_data_format,
            request_data=request_data,
            response_endpoint=response_endpoint,
            request_duration=request_duration,
            response_duration=response_duration,
        )
        if _is_error(invoke_metadata):
            return invoke_metadata
    except ValueError as exc:
        return invalid_input_error(
            resource_type="raw_command",
            message=str(exc),
            input_payload={
                "request_data_format": request_data_format,
                "request_endpoint": request_endpoint,
            },
            retry_hint="Retry with valid raw command inputs for the selected format.",
        )
    except Exception as exc:
        return error_result(
            code="control_plane_error",
            message="Failed to invoke the raw command on the digital twin instance.",
            retry_hint="Verify the twin selector and command payload, then retry.",
            details={"reason": str(exc)},
        )

    base_url = build_ords_base_url(domain_context)
    deadline = time.monotonic() + timeout
    last_candidates = []
    candidate = None
    while time.monotonic() < deadline:
        try:
            rows = list_raw_command_records(
                base_url=base_url,
                token=token.access_token,
                digital_twin_instance_id=twin["id"],
                target_count=100,
            )
        except Exception as exc:
            return error_result(
                code="data_plane_error",
                message="Failed while correlating the raw command against the data-plane feed.",
                retry_hint="Retry the command or inspect recent raw commands for the twin.",
                details={"reason": str(exc)},
            )

        candidates = [
            row
            for row in rows
            if _candidate_matches_invoke(
                row=row,
                twin_id=twin["id"],
                request_endpoint=request_endpoint,
                request_data_format=request_data_format,
                response_endpoint=response_endpoint,
                request_duration=request_duration,
                response_duration=response_duration,
                invoke_started_at=invoke_started_at,
            )
        ]
        last_candidates = candidates
        if len(candidates) == 1:
            candidate = candidates[0]
            break
        if len(candidates) > 1 and time.monotonic() + 2 >= deadline:
            return ambiguity_error(
                resource_type="raw_command",
                message="Multiple raw command records matched the invoke request.",
                input_payload={
                    "digital_twin_instance_id": twin["id"],
                    "request_endpoint": request_endpoint,
                    "request_data_format": request_data_format,
                    "response_endpoint": response_endpoint,
                },
                candidates=[
                    {
                        "id": row.get("id"),
                        "time_created": row.get("time_created"),
                        "request_endpoint": row.get("request_endpoint"),
                    }
                    for row in candidates
                ],
            )
        time.sleep(2)

    if candidate is None:
        if last_candidates:
            return ambiguity_error(
                resource_type="raw_command",
                message="Multiple raw command records matched the invoke request.",
                input_payload={
                    "digital_twin_instance_id": twin["id"],
                    "request_endpoint": request_endpoint,
                    "request_data_format": request_data_format,
                    "response_endpoint": response_endpoint,
                },
                candidates=[
                    {
                        "id": row.get("id"),
                        "time_created": row.get("time_created"),
                        "request_endpoint": row.get("request_endpoint"),
                    }
                    for row in last_candidates
                ],
            )
        return error_result(
            code="timeout",
            message="Timed out waiting for a correlated raw command record.",
            retry_hint="Retry with a larger timeout or inspect recent raw commands for the twin.",
            details={"digital_twin_instance_id": twin["id"]},
        )

    remaining = max(0, int(deadline - time.monotonic()))
    terminal = wait_for_raw_command_terminal_state(
        fetch_detail=lambda record_id: get_raw_command_record(
            base_url=base_url,
            token=token.access_token,
            request_id=record_id,
        ),
        record_id=candidate["id"],
        timeout_seconds=remaining,
        sleep=time.sleep,
        monotonic=time.monotonic,
    )
    return {
        **invoke_metadata,
        "request_id": candidate["id"],
        "timed_out": terminal["timed_out"],
        "raw_command": terminal["raw_command"],
    }


def wait_for_twin_update_impl(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
    content_path: str | None = None,
    since: str,
    timeout: int = 30,
):
    resolved = _resolve_twin_with_data_plane_access(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    if _is_error(resolved):
        return resolved

    twin, domain_context, token = resolved
    base_url = build_ords_base_url(domain_context)

    def fetch_rows():
        rows = list_snapshot_records(
            base_url=base_url,
            token=token.access_token,
            digital_twin_instance_id=twin["id"],
            target_count=500,
        )
        if content_path:
            return [row for row in rows if row.get("content_path") == content_path]
        return rows

    try:
        return wait_for_snapshot_update(
            fetch_rows=fetch_rows,
            since=since,
            timeout_seconds=timeout,
            sleep=time.sleep,
            monotonic=time.monotonic,
        )
    except ValueError:
        return invalid_input_error(
            resource_type="snapshot_data",
            message="since must be an RFC 3339 timestamp.",
            input_payload={"since": since},
            retry_hint="Retry with since set to an RFC 3339 timestamp.",
        )
    except Exception as exc:
        return error_result(
            code="data_plane_error",
            message="Failed while waiting for a twin snapshot update.",
            retry_hint="Verify the twin selector and data-plane access, then retry.",
            details={"reason": str(exc)},
        )


def list_recent_rejected_data_for_twin_impl(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
    limit: int = 20,
    since: str | None = None,
    until: str | None = None,
):
    resolved = _resolve_twin_with_data_plane_access(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    if _is_error(resolved):
        return resolved

    twin, domain_context, token = resolved
    try:
        rows = list_rejected_data_records(
            base_url=build_ords_base_url(domain_context),
            token=token.access_token,
            digital_twin_instance_id=twin["id"],
            target_count=500 if since or until else max(limit, 20),
        )
    except Exception as exc:
        return error_result(
            code="data_plane_error",
            message="Failed to list recent rejected ingest records.",
            retry_hint="Verify the twin selector and data-plane access, then retry.",
            details={"reason": str(exc)},
        )

    try:
        return [
            row
            for row in rows
            if row.get("digital_twin_instance_id") == twin["id"]
            and _in_time_window(row.get("time_received"), since, until)
        ]
    except ValueError:
        return invalid_input_error(
            resource_type="rejected_data",
            message="since and until must be RFC 3339 timestamps when provided.",
            input_payload={"since": since, "until": until},
            retry_hint="Retry with RFC 3339 timestamps for since and until.",
        )


@tool(
    description="Retrieves a specific digital twin adapter by its identifier."
)
def get_digital_twin_adapter(
    digital_twin_adapter_id: Annotated[str, "The digital twin adapter identifier"]
):
    return _delegate(
        f"Error getting digital twin adapter {digital_twin_adapter_id}",
        get_digital_twin_adapter_record,
        digital_twin_adapter_id,
    )

@tool(
    description="Retrieves a specific digital twin instance by its identifier."
)
def get_digital_twin_instance(
    digital_twin_instance_id: Annotated[str, "The digital twin instance identifier"]
):
    return _delegate(
        f"Error getting digital twin instance {digital_twin_instance_id}",
        get_digital_twin_instance_record,
        digital_twin_instance_id,
    )

@tool(
    description="Retrieves the content of a specific digital twin instance by its identifier."
)
def get_digital_twin_instance_content(
    digital_twin_instance_id: Annotated[str, "The digital twin instance identifier"],
    should_include_metadata: Annotated[
        bool,
        "If true, includes digital twin instance metadata in the response payload",
    ] = False,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the request",
    ] = None,
):
    if not should_include_metadata and opc_request_id is None:
        return _delegate(
            f"Error getting digital twin instance content {digital_twin_instance_id}",
            get_digital_twin_instance_content_record,
            digital_twin_instance_id,
        )

    try:
        kwargs = {
            "digital_twin_instance_id": digital_twin_instance_id,
            "should_include_metadata": should_include_metadata,
        }
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        return get_iot_client().get_digital_twin_instance_content(**kwargs).data
    except Exception as e:
        logger.error(f"Error getting digital twin instance content {digital_twin_instance_id}: {e}")
        raise

@tool(
    description="Retrieves a specific digital twin model by its identifier."
)
def get_digital_twin_model(
    digital_twin_model_id: Annotated[str, "The digital twin model identifier"]
):
    return _delegate(
        f"Error getting digital twin model {digital_twin_model_id}",
        get_digital_twin_model_record,
        digital_twin_model_id,
    )

@tool(
    description="Retrieves the specification of a specific digital twin model by its identifier."
)
def get_digital_twin_model_spec(
    digital_twin_model_id: Annotated[str, "The digital twin model identifier"]
):
    return _delegate(
        f"Error getting digital twin model spec {digital_twin_model_id}",
        get_digital_twin_model_spec_record,
        digital_twin_model_id,
    )

@tool(
    description="Retrieves a specific digital twin relationship by its identifier."
)
def get_digital_twin_relationship(
    digital_twin_relationship_id: Annotated[str, "The digital twin relationship identifier"]
):
    return _delegate(
        f"Error getting digital twin relationship {digital_twin_relationship_id}",
        get_digital_twin_relationship_record,
        digital_twin_relationship_id,
    )

@tool(
    description="Retrieves a specific IoT domain by its identifier."
)
def get_iot_domain(
    iot_domain_id: Annotated[str, "The IoT domain identifier"]
):
    return _delegate(f"Error getting IoT domain {iot_domain_id}", get_iot_domain_record, iot_domain_id)

@tool(
    description="Retrieves a specific IoT domain group by its identifier."
)
def get_iot_domain_group(
    iot_domain_group_id: Annotated[str, "The IoT domain group identifier"]
):
    return _delegate(
        f"Error getting IoT domain group {iot_domain_group_id}",
        get_iot_domain_group_record,
        iot_domain_group_id,
    )

@tool(
    description="Retrieves a specific work request by its identifier."
)
def get_work_request(
    work_request_id: Annotated[str, "The work request identifier"]
):
    return _delegate(
        f"Error getting work request {work_request_id}",
        get_work_request_record,
        work_request_id,
    )

@tool(
    description="Lists digital twin adapters in a specified IoT domain."
)
def list_digital_twin_adapters(
    iot_domain_id: Annotated[str, "The IoT domain identifier"]
):
    return _result_payload(
        _delegate(
            f"Error listing digital twin adapters for domain {iot_domain_id}",
            list_digital_twin_adapters_records,
            iot_domain_id=iot_domain_id,
        )
    )

@tool(
    description="Lists digital twin models in a specified IoT domain."
)
def list_digital_twin_models(
    iot_domain_id: Annotated[str, "The IoT domain identifier"]
):
    return _result_payload(
        _delegate(
            f"Error listing digital twin models for domain {iot_domain_id}",
            list_digital_twin_models_records,
            iot_domain_id=iot_domain_id,
        )
    )

@tool(
    description="Lists digital twin instances in a specified IoT domain."
)
def list_digital_twin_instances(
    iot_domain_id: Annotated[str, "The IoT domain identifier"],
    limit: Annotated[int, "The limit of results"] = 1000
):
    return _result_payload(
        _delegate(
            f"Error listing digital twin instances for domain {iot_domain_id}",
            list_digital_twin_instances_records,
            iot_domain_id=iot_domain_id,
            limit=limit,
        )
    )

@tool(
    description="Lists digital twin relationships in a specified IoT domain."
)
def list_digital_twin_relationships(
    iot_domain_id: Annotated[str, "The IoT domain identifier"]
):
    return _result_payload(
        _delegate(
            f"Error listing digital twin relationships for domain {iot_domain_id}",
            list_digital_twin_relationships_records,
            iot_domain_id=iot_domain_id,
        )
    )

@tool(
    description="Lists IoT domain groups in a specified compartment."
)
def list_iot_domain_groups(
    compartment_id: Annotated[str, "Compartment containing IoT Domain Groups"]
):
    return _result_payload(
        _delegate(
            f"Error listing IoT domain groups for compartment {compartment_id}",
            list_iot_domain_groups_records,
            compartment_id=compartment_id,
        )
    )

@tool(
    description="Lists IoT domains in a specified compartment."
)
def list_iot_domains(
    compartment_id: Annotated[str, "Compartment containing IoT Domains"]
):
    return _result_payload(
        _delegate(
            f"Error listing IoT domains for compartment {compartment_id}",
            list_iot_domains_records,
            compartment_id=compartment_id,
        )
    )

@tool(
    description="Lists errors for a specific work request."
)
def list_work_request_errors(
    work_request_id: Annotated[str, "The work request identifier"]
):
    return _result_payload(
        _delegate(
            f"Error listing work request errors for {work_request_id}",
            list_work_request_errors_records,
            work_request_id=work_request_id,
        )
    )

@tool(
    description="Lists logs for a specific work request."
)
def list_work_request_logs(
    work_request_id: Annotated[str, "The work request identifier"]
):
    return _result_payload(
        _delegate(
            f"Error listing work request logs for {work_request_id}",
            list_work_request_logs_records,
            work_request_id=work_request_id,
        )
    )

@tool(
    description="Lists work requests in a specified compartment."
)
def list_work_requests(
    compartment_id: Annotated[str, "The compartment ID containing the work requests"]
):
    return _result_payload(
        _delegate(
            f"Error listing work requests for compartment {compartment_id}",
            list_work_requests_records,
            compartment_id=compartment_id,
        )
    )


@tool(
    description="Creates a new digital twin model in a specified IoT domain."
)
def create_digital_twin_model(
    iot_domain_id: Annotated[str, "The IoT domain identifier"],
    display_name: Annotated[str, "A user-friendly display name for the digital twin model"],
    spec: Annotated[
        dict[str, Any] | str,
        "The DTDL v3 digital twin model specification as a JSON object or JSON string",
    ],
    description: Annotated[Optional[str], "A short description of the digital twin model"] = None,
    opc_retry_token: Annotated[Optional[str], "A retry token for safely retrying the request"] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    try:
        create_digital_twin_model_details = oci.iot.models.CreateDigitalTwinModelDetails(
            iot_domain_id=iot_domain_id,
            display_name=display_name,
            description=description,
            spec=_parse_json_input(spec, "spec"),
        )

        kwargs = {"create_digital_twin_model_details": create_digital_twin_model_details}
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        digital_twin_model = get_iot_client().create_digital_twin_model(**kwargs)
        from .models import DigitalTwinModelModel

        return DigitalTwinModelModel.from_oci_model(digital_twin_model.data).model_dump()
    except Exception as e:
        logger.error(f"Error creating digital twin model in domain {iot_domain_id}: {e}")
        raise


@tool(
    description="Creates a new digital twin adapter in a specified IoT domain."
)
def create_digital_twin_adapter(
    iot_domain_id: Annotated[str, "The IoT domain identifier"],
    display_name: Annotated[Optional[str], "A user-friendly display name for the digital twin adapter"] = None,
    description: Annotated[Optional[str], "A short description of the digital twin adapter"] = None,
    digital_twin_model_id: Annotated[
        Optional[str],
        "The digital twin model OCID associated with the adapter",
    ] = None,
    digital_twin_model_spec_uri: Annotated[
        Optional[str],
        "The URI of the digital twin model specification",
    ] = None,
    inbound_envelope: Annotated[
        Optional[dict[str, Any] | str],
        "The adapter inbound envelope as a JSON object or JSON string",
    ] = None,
    inbound_routes: Annotated[
        Optional[list[dict[str, Any]] | str],
        "The adapter inbound routes as a JSON array or JSON string",
    ] = None,
    freeform_tags: Annotated[Optional[dict[str, str] | str], "Free-form tags as an object or JSON string"] = None,
    defined_tags: Annotated[
        Optional[dict[str, dict[str, Any]] | str],
        "Defined tags as an object or JSON string",
    ] = None,
    opc_retry_token: Annotated[Optional[str], "A retry token for safely retrying the request"] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    try:
        create_digital_twin_adapter_details = oci.iot.models.CreateDigitalTwinAdapterDetails(
            iot_domain_id=iot_domain_id,
            display_name=display_name,
            description=description,
            digital_twin_model_id=digital_twin_model_id,
            digital_twin_model_spec_uri=digital_twin_model_spec_uri,
            inbound_envelope=_parse_json_input(inbound_envelope, "inbound_envelope"),
            inbound_routes=_parse_json_input(inbound_routes, "inbound_routes"),
            freeform_tags=_parse_json_input(freeform_tags, "freeform_tags"),
            defined_tags=_parse_json_input(defined_tags, "defined_tags"),
        )

        kwargs = {"create_digital_twin_adapter_details": create_digital_twin_adapter_details}
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        digital_twin_adapter = get_iot_client().create_digital_twin_adapter(**kwargs)
        from .models import DigitalTwinAdapterModel

        return DigitalTwinAdapterModel.from_oci_model(digital_twin_adapter.data).model_dump()
    except Exception as e:
        logger.error(f"Error creating digital twin adapter in domain {iot_domain_id}: {e}")
        raise


@tool(
    description="Creates a new digital twin instance in a specified IoT domain."
)
def create_digital_twin_instance(
    iot_domain_id: Annotated[str, "The IoT domain identifier"],
    auth_id: Annotated[Optional[str], "The OCID of the authentication resource for the instance"] = None,
    external_key: Annotated[
        Optional[str],
        "A unique identifier for the physical entity represented by the twin",
    ] = None,
    display_name: Annotated[Optional[str], "A user-friendly display name for the digital twin instance"] = None,
    description: Annotated[Optional[str], "A short description of the digital twin instance"] = None,
    digital_twin_adapter_id: Annotated[
        Optional[str],
        "The digital twin adapter OCID associated with the instance",
    ] = None,
    digital_twin_model_id: Annotated[
        Optional[str],
        "The digital twin model OCID associated with the instance",
    ] = None,
    digital_twin_model_spec_uri: Annotated[
        Optional[str],
        "The URI of the digital twin model specification",
    ] = None,
    freeform_tags: Annotated[Optional[dict[str, str] | str], "Free-form tags as an object or JSON string"] = None,
    defined_tags: Annotated[
        Optional[dict[str, dict[str, Any]] | str],
        "Defined tags as an object or JSON string",
    ] = None,
    opc_retry_token: Annotated[Optional[str], "A retry token for safely retrying the request"] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    try:
        create_digital_twin_instance_details = oci.iot.models.CreateDigitalTwinInstanceDetails(
            iot_domain_id=iot_domain_id,
            auth_id=auth_id,
            external_key=external_key,
            display_name=display_name,
            description=description,
            digital_twin_adapter_id=digital_twin_adapter_id,
            digital_twin_model_id=digital_twin_model_id,
            digital_twin_model_spec_uri=digital_twin_model_spec_uri,
            freeform_tags=_parse_json_input(freeform_tags, "freeform_tags"),
            defined_tags=_parse_json_input(defined_tags, "defined_tags"),
        )

        kwargs = {"create_digital_twin_instance_details": create_digital_twin_instance_details}
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        digital_twin_instance = get_iot_client().create_digital_twin_instance(**kwargs)
        from .models import DigitalTwinInstanceModel

        return DigitalTwinInstanceModel.from_oci_model(digital_twin_instance.data).model_dump()
    except Exception as e:
        logger.error(f"Error creating digital twin instance in domain {iot_domain_id}: {e}")
        raise


@tool(
    description="Creates a new digital twin relationship in a specified IoT domain."
)
def create_digital_twin_relationship(
    iot_domain_id: Annotated[str, "The IoT domain identifier"],
    content_path: Annotated[str, "The relationship name from the source digital twin model"],
    source_digital_twin_instance_id: Annotated[str, "The source digital twin instance identifier"],
    target_digital_twin_instance_id: Annotated[str, "The target digital twin instance identifier"],
    display_name: Annotated[
        Optional[str],
        "A user-friendly display name for the digital twin relationship",
    ] = None,
    description: Annotated[Optional[str], "A short description of the digital twin relationship"] = None,
    content: Annotated[
        Optional[dict[str, Any] | str],
        "The relationship property values as an object or JSON string",
    ] = None,
    freeform_tags: Annotated[Optional[dict[str, str] | str], "Free-form tags as an object or JSON string"] = None,
    defined_tags: Annotated[
        Optional[dict[str, dict[str, Any]] | str],
        "Defined tags as an object or JSON string",
    ] = None,
    opc_retry_token: Annotated[Optional[str], "A retry token for safely retrying the request"] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    try:
        create_digital_twin_relationship_details = oci.iot.models.CreateDigitalTwinRelationshipDetails(
            iot_domain_id=iot_domain_id,
            content_path=content_path,
            source_digital_twin_instance_id=source_digital_twin_instance_id,
            target_digital_twin_instance_id=target_digital_twin_instance_id,
            display_name=display_name,
            description=description,
            content=_parse_json_input(content, "content"),
            freeform_tags=_parse_json_input(freeform_tags, "freeform_tags"),
            defined_tags=_parse_json_input(defined_tags, "defined_tags"),
        )

        kwargs = {
            "create_digital_twin_relationship_details": create_digital_twin_relationship_details,
        }
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        digital_twin_relationship = get_iot_client().create_digital_twin_relationship(**kwargs)
        from .models import DigitalTwinRelationshipModel

        return DigitalTwinRelationshipModel.from_oci_model(digital_twin_relationship.data).model_dump()
    except Exception as e:
        logger.error(f"Error creating digital twin relationship in domain {iot_domain_id}: {e}")
        raise


@tool(
    description="Deletes a specific digital twin adapter by its identifier."
)
def delete_digital_twin_adapter(
    digital_twin_adapter_id: Annotated[str, "The digital twin adapter identifier"],
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when deleting the digital twin adapter",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the delete digital twin adapter request",
    ] = None,
):
    try:
        kwargs = {"digital_twin_adapter_id": digital_twin_adapter_id}
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response = get_iot_client().delete_digital_twin_adapter(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error deleting digital twin adapter {digital_twin_adapter_id}: {e}")
        raise


@tool(
    description="Deletes a specific digital twin instance by its identifier."
)
def delete_digital_twin_instance(
    digital_twin_instance_id: Annotated[str, "The digital twin instance identifier"],
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when deleting the digital twin instance",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the delete digital twin instance request",
    ] = None,
):
    try:
        kwargs = {"digital_twin_instance_id": digital_twin_instance_id}
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response = get_iot_client().delete_digital_twin_instance(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error deleting digital twin instance {digital_twin_instance_id}: {e}")
        raise


@tool(
    description="Deletes a specific digital twin model by its identifier."
)
def delete_digital_twin_model(
    digital_twin_model_id: Annotated[str, "The digital twin model identifier"],
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when deleting the digital twin model",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the delete digital twin model request",
    ] = None,
):
    try:
        kwargs = {"digital_twin_model_id": digital_twin_model_id}
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response = get_iot_client().delete_digital_twin_model(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error deleting digital twin model {digital_twin_model_id}: {e}")
        raise


@tool(
    description="Deletes a specific digital twin relationship by its identifier."
)
def delete_digital_twin_relationship(
    digital_twin_relationship_id: Annotated[str, "The digital twin relationship identifier"],
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when deleting the digital twin relationship",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the delete digital twin relationship request",
    ] = None,
):
    try:
        kwargs = {"digital_twin_relationship_id": digital_twin_relationship_id}
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        response = get_iot_client().delete_digital_twin_relationship(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error deleting digital twin relationship {digital_twin_relationship_id}: {e}")
        raise


def _build_direct_invoke_raw_command_details(
    *,
    request_data_format: str,
    request_endpoint: str,
    response_endpoint: Optional[str] = None,
    request_duration: Optional[str] = None,
    response_duration: Optional[str] = None,
    request_data_content_type: Optional[str] = None,
    request_data: Optional[dict[str, Any] | str] = None,
):
    normalized_format = request_data_format.upper()
    common_kwargs = {
        "request_duration": request_duration,
        "response_duration": response_duration,
        "request_endpoint": request_endpoint,
        "response_endpoint": response_endpoint,
        "request_data_content_type": request_data_content_type,
    }

    if normalized_format == "JSON":
        return oci.iot.models.InvokeRawJsonCommandDetails(
            request_data=_parse_json_input(request_data, "request_data"),
            **common_kwargs,
        )
    if normalized_format == "TEXT":
        return oci.iot.models.InvokeRawTextCommandDetails(
            request_data=request_data,
            **common_kwargs,
        )
    if normalized_format == "BINARY":
        return oci.iot.models.InvokeRawBinaryCommandDetails(
            request_data=request_data,
            **common_kwargs,
        )
    raise ValueError("request_data_format must be one of: JSON, TEXT, BINARY")


@tool(
    description="Updates a specific digital twin adapter by its identifier."
)
def update_digital_twin_adapter(
    digital_twin_adapter_id: Annotated[str, "The digital twin adapter identifier"],
    display_name: Annotated[Optional[str], "A user-friendly display name for the digital twin adapter"] = None,
    description: Annotated[Optional[str], "A short description of the digital twin adapter"] = None,
    inbound_envelope: Annotated[
        Optional[dict[str, Any] | str],
        "The adapter inbound envelope as a JSON object or JSON string",
    ] = None,
    inbound_routes: Annotated[
        Optional[list[dict[str, Any]] | str],
        "The adapter inbound routes as a JSON array or JSON string",
    ] = None,
    freeform_tags: Annotated[Optional[dict[str, str] | str], "Free-form tags as an object or JSON string"] = None,
    defined_tags: Annotated[
        Optional[dict[str, dict[str, Any]] | str],
        "Defined tags as an object or JSON string",
    ] = None,
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when updating the digital twin adapter",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the update digital twin adapter request",
    ] = None,
):
    try:
        update_digital_twin_adapter_details = oci.iot.models.UpdateDigitalTwinAdapterDetails(
            display_name=display_name,
            description=description,
            inbound_envelope=_parse_json_input(inbound_envelope, "inbound_envelope"),
            inbound_routes=_parse_json_input(inbound_routes, "inbound_routes"),
            freeform_tags=_parse_json_input(freeform_tags, "freeform_tags"),
            defined_tags=_parse_json_input(defined_tags, "defined_tags"),
        )

        kwargs = {
            "digital_twin_adapter_id": digital_twin_adapter_id,
            "update_digital_twin_adapter_details": update_digital_twin_adapter_details,
        }
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        digital_twin_adapter = get_iot_client().update_digital_twin_adapter(**kwargs)
        from .models import DigitalTwinAdapterModel

        return DigitalTwinAdapterModel.from_oci_model(digital_twin_adapter.data).model_dump()
    except Exception as e:
        logger.error(f"Error updating digital twin adapter {digital_twin_adapter_id}: {e}")
        raise


@tool(
    description="Updates a specific digital twin instance by its identifier."
)
def update_digital_twin_instance(
    digital_twin_instance_id: Annotated[str, "The digital twin instance identifier"],
    auth_id: Annotated[Optional[str], "The OCID of the authentication resource for the instance"] = None,
    external_key: Annotated[
        Optional[str],
        "A unique identifier for the physical entity represented by the twin",
    ] = None,
    display_name: Annotated[
        Optional[str],
        "A user-friendly display name for the digital twin instance",
    ] = None,
    description: Annotated[Optional[str], "A short description of the digital twin instance"] = None,
    digital_twin_adapter_id: Annotated[
        Optional[str],
        "The digital twin adapter OCID associated with the instance",
    ] = None,
    digital_twin_model_id: Annotated[
        Optional[str],
        "The digital twin model OCID associated with the instance",
    ] = None,
    digital_twin_model_spec_uri: Annotated[
        Optional[str],
        "The URI of the digital twin model specification",
    ] = None,
    freeform_tags: Annotated[Optional[dict[str, str] | str], "Free-form tags as an object or JSON string"] = None,
    defined_tags: Annotated[
        Optional[dict[str, dict[str, Any]] | str],
        "Defined tags as an object or JSON string",
    ] = None,
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when updating the digital twin instance",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the update digital twin instance request",
    ] = None,
):
    try:
        update_digital_twin_instance_details = oci.iot.models.UpdateDigitalTwinInstanceDetails(
            auth_id=auth_id,
            external_key=external_key,
            display_name=display_name,
            description=description,
            digital_twin_adapter_id=digital_twin_adapter_id,
            digital_twin_model_id=digital_twin_model_id,
            digital_twin_model_spec_uri=digital_twin_model_spec_uri,
            freeform_tags=_parse_json_input(freeform_tags, "freeform_tags"),
            defined_tags=_parse_json_input(defined_tags, "defined_tags"),
        )

        kwargs = {
            "digital_twin_instance_id": digital_twin_instance_id,
            "update_digital_twin_instance_details": update_digital_twin_instance_details,
        }
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        digital_twin_instance = get_iot_client().update_digital_twin_instance(**kwargs)
        from .models import DigitalTwinInstanceModel

        return DigitalTwinInstanceModel.from_oci_model(digital_twin_instance.data).model_dump()
    except Exception as e:
        logger.error(f"Error updating digital twin instance {digital_twin_instance_id}: {e}")
        raise


@tool(
    description="Updates a specific digital twin model by its identifier."
)
def update_digital_twin_model(
    digital_twin_model_id: Annotated[str, "The digital twin model identifier"],
    display_name: Annotated[Optional[str], "A user-friendly display name for the digital twin model"] = None,
    description: Annotated[Optional[str], "A short description of the digital twin model"] = None,
    freeform_tags: Annotated[Optional[dict[str, str] | str], "Free-form tags as an object or JSON string"] = None,
    defined_tags: Annotated[
        Optional[dict[str, dict[str, Any]] | str],
        "Defined tags as an object or JSON string",
    ] = None,
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when updating the digital twin model",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the update digital twin model request",
    ] = None,
):
    try:
        update_digital_twin_model_details = oci.iot.models.UpdateDigitalTwinModelDetails(
            display_name=display_name,
            description=description,
            freeform_tags=_parse_json_input(freeform_tags, "freeform_tags"),
            defined_tags=_parse_json_input(defined_tags, "defined_tags"),
        )

        kwargs = {
            "digital_twin_model_id": digital_twin_model_id,
            "update_digital_twin_model_details": update_digital_twin_model_details,
        }
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        digital_twin_model = get_iot_client().update_digital_twin_model(**kwargs)
        from .models import DigitalTwinModelModel

        return DigitalTwinModelModel.from_oci_model(digital_twin_model.data).model_dump()
    except Exception as e:
        logger.error(f"Error updating digital twin model {digital_twin_model_id}: {e}")
        raise


@tool(
    description="Updates a specific digital twin relationship by its identifier."
)
def update_digital_twin_relationship(
    digital_twin_relationship_id: Annotated[str, "The digital twin relationship identifier"],
    display_name: Annotated[
        Optional[str],
        "A user-friendly display name for the digital twin relationship",
    ] = None,
    description: Annotated[Optional[str], "A short description of the digital twin relationship"] = None,
    content: Annotated[
        Optional[dict[str, Any] | str],
        "The relationship property values as an object or JSON string",
    ] = None,
    freeform_tags: Annotated[Optional[dict[str, str] | str], "Free-form tags as an object or JSON string"] = None,
    defined_tags: Annotated[
        Optional[dict[str, dict[str, Any]] | str],
        "Defined tags as an object or JSON string",
    ] = None,
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when updating the digital twin relationship",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the update digital twin relationship request",
    ] = None,
):
    try:
        update_digital_twin_relationship_details = oci.iot.models.UpdateDigitalTwinRelationshipDetails(
            display_name=display_name,
            description=description,
            content=_parse_json_input(content, "content"),
            freeform_tags=_parse_json_input(freeform_tags, "freeform_tags"),
            defined_tags=_parse_json_input(defined_tags, "defined_tags"),
        )

        kwargs = {
            "digital_twin_relationship_id": digital_twin_relationship_id,
            "update_digital_twin_relationship_details": update_digital_twin_relationship_details,
        }
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        digital_twin_relationship = get_iot_client().update_digital_twin_relationship(**kwargs)
        from .models import DigitalTwinRelationshipModel

        return DigitalTwinRelationshipModel.from_oci_model(digital_twin_relationship.data).model_dump()
    except Exception as e:
        logger.error(f"Error updating digital twin relationship {digital_twin_relationship_id}: {e}")
        raise


@tool(
    description="Creates a new IoT domain in a specified IoT domain group."
)
def create_iot_domain(
    iot_domain_group_id: Annotated[str, "The IoT domain group identifier"],
    compartment_id: Annotated[str, "The compartment identifier where the IoT domain will be created"],
    display_name: Annotated[Optional[str], "A user-friendly display name for the IoT domain"] = None,
    description: Annotated[Optional[str], "A short description of the IoT domain"] = None,
    freeform_tags: Annotated[Optional[dict[str, str] | str], "Free-form tags as an object or JSON string"] = None,
    defined_tags: Annotated[
        Optional[dict[str, dict[str, Any]] | str],
        "Defined tags as an object or JSON string",
    ] = None,
    opc_retry_token: Annotated[Optional[str], "A retry token for safely retrying the request"] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    try:
        create_iot_domain_details = oci.iot.models.CreateIotDomainDetails(
            iot_domain_group_id=iot_domain_group_id,
            compartment_id=compartment_id,
            display_name=display_name,
            description=description,
            freeform_tags=_parse_json_input(freeform_tags, "freeform_tags"),
            defined_tags=_parse_json_input(defined_tags, "defined_tags"),
        )

        kwargs = {"create_iot_domain_details": create_iot_domain_details}
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        iot_domain = get_iot_client().create_iot_domain(**kwargs)
        from .models import IoTDomainModel

        return IoTDomainModel.from_oci_model(iot_domain.data).model_dump()
    except Exception as e:
        logger.error(f"Error creating IoT domain in group {iot_domain_group_id}: {e}")
        raise


@tool(
    description="Creates a new IoT domain group in a specified compartment."
)
def create_iot_domain_group(
    compartment_id: Annotated[str, "The compartment identifier where the IoT domain group will be created"],
    type: Annotated[Optional[str], "The IoT domain group type, such as STANDARD or LIGHTWEIGHT"] = None,
    display_name: Annotated[Optional[str], "A user-friendly display name for the IoT domain group"] = None,
    description: Annotated[Optional[str], "A short description of the IoT domain group"] = None,
    freeform_tags: Annotated[Optional[dict[str, str] | str], "Free-form tags as an object or JSON string"] = None,
    defined_tags: Annotated[
        Optional[dict[str, dict[str, Any]] | str],
        "Defined tags as an object or JSON string",
    ] = None,
    opc_retry_token: Annotated[Optional[str], "A retry token for safely retrying the request"] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    try:
        create_iot_domain_group_details = oci.iot.models.CreateIotDomainGroupDetails(
            compartment_id=compartment_id,
            type=type,
            display_name=display_name,
            description=description,
            freeform_tags=_parse_json_input(freeform_tags, "freeform_tags"),
            defined_tags=_parse_json_input(defined_tags, "defined_tags"),
        )

        kwargs = {"create_iot_domain_group_details": create_iot_domain_group_details}
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        iot_domain_group = get_iot_client().create_iot_domain_group(**kwargs)
        from .models import IoTDomainGroupModel

        return IoTDomainGroupModel.from_oci_model(iot_domain_group.data).model_dump()
    except Exception as e:
        logger.error(f"Error creating IoT domain group in compartment {compartment_id}: {e}")
        raise


@tool(
    description="Moves a specific IoT domain to a different compartment."
)
def change_iot_domain_compartment(
    iot_domain_id: Annotated[str, "The IoT domain identifier"],
    compartment_id: Annotated[str, "The target compartment identifier for the IoT domain"],
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when moving the IoT domain",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the change IoT domain compartment request",
    ] = None,
    opc_retry_token: Annotated[Optional[str], "A retry token for safely retrying the request"] = None,
):
    try:
        change_iot_domain_compartment_details = oci.iot.models.ChangeIotDomainCompartmentDetails(
            compartment_id=compartment_id,
        )

        kwargs = {
            "iot_domain_id": iot_domain_id,
            "change_iot_domain_compartment_details": change_iot_domain_compartment_details,
        }
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token

        response = get_iot_client().change_iot_domain_compartment(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error changing IoT domain compartment for {iot_domain_id}: {e}")
        raise


@tool(
    description="Changes the data retention period configuration for a specific IoT domain."
)
def change_iot_domain_data_retention_period(
    iot_domain_id: Annotated[str, "The IoT domain identifier"],
    type: Annotated[
        str,
        "The retention data type, such as RAW_DATA, REJECTED_DATA, HISTORIZED_DATA, or RAW_COMMAND_DATA",
    ],
    data_retention_period_in_days: Annotated[int, "The number of days to retain the selected data type"],
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when updating retention settings",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the data retention period change request",
    ] = None,
    opc_retry_token: Annotated[Optional[str], "A retry token for safely retrying the request"] = None,
):
    try:
        change_iot_domain_data_retention_period_details = (
            oci.iot.models.ChangeIotDomainDataRetentionPeriodDetails(
                type=type,
                data_retention_period_in_days=data_retention_period_in_days,
            )
        )

        kwargs = {
            "iot_domain_id": iot_domain_id,
            "change_iot_domain_data_retention_period_details": (
                change_iot_domain_data_retention_period_details
            ),
        }
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token

        response = get_iot_client().change_iot_domain_data_retention_period(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error changing data retention period for IoT domain {iot_domain_id}: {e}")
        raise


@tool(
    description="Moves a specific IoT domain group to a different compartment."
)
def change_iot_domain_group_compartment(
    iot_domain_group_id: Annotated[str, "The IoT domain group identifier"],
    compartment_id: Annotated[str, "The target compartment identifier for the IoT domain group"],
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when moving the IoT domain group",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the change IoT domain group compartment request",
    ] = None,
    opc_retry_token: Annotated[Optional[str], "A retry token for safely retrying the request"] = None,
):
    try:
        change_iot_domain_group_compartment_details = (
            oci.iot.models.ChangeIotDomainGroupCompartmentDetails(
                compartment_id=compartment_id,
            )
        )

        kwargs = {
            "iot_domain_group_id": iot_domain_group_id,
            "change_iot_domain_group_compartment_details": change_iot_domain_group_compartment_details,
        }
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token

        response = get_iot_client().change_iot_domain_group_compartment(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error changing IoT domain group compartment for {iot_domain_group_id}: {e}")
        raise


@tool(
    description="Configures data access for a specific IoT domain."
)
def configure_iot_domain_data_access(
    iot_domain_id: Annotated[str, "The IoT domain identifier"],
    type: Annotated[str, "The data access configuration type: DIRECT, ORDS, or APEX"],
    db_allow_listed_identity_group_names: Annotated[
        Optional[list[str] | str],
        "Allowed identity group names for DIRECT access as a list or JSON string",
    ] = None,
    db_allowed_identity_domain_host: Annotated[
        Optional[str],
        "The allowed identity domain host for ORDS access",
    ] = None,
    db_workspace_admin_initial_password: Annotated[
        Optional[str],
        "The initial workspace admin password for APEX access",
    ] = None,
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when configuring IoT domain data access",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the configure IoT domain data access request",
    ] = None,
    opc_retry_token: Annotated[Optional[str], "A retry token for safely retrying the request"] = None,
):
    try:
        normalized_type = type.upper()
        if normalized_type == "DIRECT":
            configure_iot_domain_data_access_details = oci.iot.models.DirectDataAccessDetails(
                db_allow_listed_identity_group_names=_parse_json_input(
                    db_allow_listed_identity_group_names,
                    "db_allow_listed_identity_group_names",
                ),
            )
        elif normalized_type == "ORDS":
            configure_iot_domain_data_access_details = oci.iot.models.OrdsDataAccessDetails(
                db_allowed_identity_domain_host=db_allowed_identity_domain_host,
            )
        elif normalized_type == "APEX":
            configure_iot_domain_data_access_details = oci.iot.models.ApexDataAccessDetails(
                db_workspace_admin_initial_password=db_workspace_admin_initial_password,
            )
        else:
            raise ValueError("type must be one of: DIRECT, ORDS, APEX")

        kwargs = {
            "iot_domain_id": iot_domain_id,
            "configure_iot_domain_data_access_details": configure_iot_domain_data_access_details,
        }
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token

        response = get_iot_client().configure_iot_domain_data_access(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error configuring IoT domain data access for {iot_domain_id}: {e}")
        raise


@tool(
    description="Configures data access for a specific IoT domain group."
)
def configure_iot_domain_group_data_access(
    iot_domain_group_id: Annotated[str, "The IoT domain group identifier"],
    db_allow_listed_vcn_ids: Annotated[list[str] | str, "Allowed VCN identifiers as a list or JSON string"],
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when configuring IoT domain group data access",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the configure IoT domain group data access request",
    ] = None,
    opc_retry_token: Annotated[Optional[str], "A retry token for safely retrying the request"] = None,
):
    try:
        configure_iot_domain_group_data_access_details = (
            oci.iot.models.ConfigureIotDomainGroupDataAccessDetails(
                db_allow_listed_vcn_ids=_parse_json_input(
                    db_allow_listed_vcn_ids,
                    "db_allow_listed_vcn_ids",
                ),
            )
        )

        kwargs = {
            "iot_domain_group_id": iot_domain_group_id,
            "configure_iot_domain_group_data_access_details": configure_iot_domain_group_data_access_details,
        }
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token

        response = get_iot_client().configure_iot_domain_group_data_access(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error configuring IoT domain group data access for {iot_domain_group_id}: {e}")
        raise


@tool(
    description="Updates a specific IoT domain by its identifier."
)
def update_iot_domain(
    iot_domain_id: Annotated[str, "The IoT domain identifier"],
    display_name: Annotated[Optional[str], "A user-friendly display name for the IoT domain"] = None,
    description: Annotated[Optional[str], "A short description of the IoT domain"] = None,
    freeform_tags: Annotated[Optional[dict[str, str] | str], "Free-form tags as an object or JSON string"] = None,
    defined_tags: Annotated[
        Optional[dict[str, dict[str, Any]] | str],
        "Defined tags as an object or JSON string",
    ] = None,
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when updating the IoT domain",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the update IoT domain request",
    ] = None,
):
    try:
        update_iot_domain_details = oci.iot.models.UpdateIotDomainDetails(
            display_name=display_name,
            description=description,
            freeform_tags=_parse_json_input(freeform_tags, "freeform_tags"),
            defined_tags=_parse_json_input(defined_tags, "defined_tags"),
        )

        kwargs = {
            "iot_domain_id": iot_domain_id,
            "update_iot_domain_details": update_iot_domain_details,
        }
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        response = get_iot_client().update_iot_domain(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error updating IoT domain {iot_domain_id}: {e}")
        raise


@tool(
    description="Updates a specific IoT domain group by its identifier."
)
def update_iot_domain_group(
    iot_domain_group_id: Annotated[str, "The IoT domain group identifier"],
    display_name: Annotated[
        Optional[str],
        "A user-friendly display name for the IoT domain group",
    ] = None,
    description: Annotated[Optional[str], "A short description of the IoT domain group"] = None,
    freeform_tags: Annotated[Optional[dict[str, str] | str], "Free-form tags as an object or JSON string"] = None,
    defined_tags: Annotated[
        Optional[dict[str, dict[str, Any]] | str],
        "Defined tags as an object or JSON string",
    ] = None,
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when updating the IoT domain group",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the update IoT domain group request",
    ] = None,
):
    try:
        update_iot_domain_group_details = oci.iot.models.UpdateIotDomainGroupDetails(
            display_name=display_name,
            description=description,
            freeform_tags=_parse_json_input(freeform_tags, "freeform_tags"),
            defined_tags=_parse_json_input(defined_tags, "defined_tags"),
        )

        kwargs = {
            "iot_domain_group_id": iot_domain_group_id,
            "update_iot_domain_group_details": update_iot_domain_group_details,
        }
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        response = get_iot_client().update_iot_domain_group(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error updating IoT domain group {iot_domain_group_id}: {e}")
        raise


@tool(
    description="Deletes a specific IoT domain by its identifier."
)
def delete_iot_domain(
    iot_domain_id: Annotated[str, "The IoT domain identifier"],
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when deleting the IoT domain",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the delete IoT domain request",
    ] = None,
):
    try:
        kwargs = {"iot_domain_id": iot_domain_id}
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        response = get_iot_client().delete_iot_domain(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error deleting IoT domain {iot_domain_id}: {e}")
        raise


@tool(
    description="Deletes a specific IoT domain group by its identifier."
)
def delete_iot_domain_group(
    iot_domain_group_id: Annotated[str, "The IoT domain group identifier"],
    if_match: Annotated[
        Optional[str],
        "An etag value for optimistic concurrency control when deleting the IoT domain group",
    ] = None,
    opc_request_id: Annotated[
        Optional[str],
        "A unique Oracle-assigned identifier for the delete IoT domain group request",
    ] = None,
):
    try:
        kwargs = {"iot_domain_group_id": iot_domain_group_id}
        if if_match is not None:
            kwargs["if_match"] = if_match
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        response = get_iot_client().delete_iot_domain_group(**kwargs)
        return _response_to_dict(response)
    except Exception as e:
        logger.error(f"Error deleting IoT domain group {iot_domain_group_id}: {e}")
        raise


@tool(
    description="Invokes a raw command on a specific digital twin instance."
)
def invoke_raw_command(
    digital_twin_instance_id: Annotated[str, "The digital twin instance identifier"],
    request_endpoint: Annotated[str, "The device endpoint where the request should be forwarded"],
    request_data_format: Annotated[str, "The request payload format: JSON, TEXT, or BINARY"],
    request_data: Annotated[
        Optional[dict[str, Any] | str],
        "The request payload as an object, plain text, base64 string, or JSON string",
    ] = None,
    response_endpoint: Annotated[
        Optional[str],
        "The device endpoint from which a response is expected",
    ] = None,
    request_duration: Annotated[Optional[str], "The duration by which the request should be sent"] = None,
    response_duration: Annotated[
        Optional[str],
        "The duration by which the response should be received",
    ] = None,
    request_data_content_type: Annotated[
        Optional[str],
        "The MIME content type for the request payload",
    ] = None,
    opc_retry_token: Annotated[Optional[str], "A retry token for safely retrying the request"] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    try:
        invoke_raw_command_details = _build_direct_invoke_raw_command_details(
            request_data_format=request_data_format,
            request_endpoint=request_endpoint,
            response_endpoint=response_endpoint,
            request_duration=request_duration,
            response_duration=response_duration,
            request_data_content_type=request_data_content_type,
            request_data=request_data,
        )

        kwargs = {
            "digital_twin_instance_id": digital_twin_instance_id,
            "invoke_raw_command_details": invoke_raw_command_details,
        }
        if opc_retry_token is not None:
            kwargs["opc_retry_token"] = opc_retry_token
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id

        response = get_iot_client().invoke_raw_command(**kwargs)
        return _response_to_dict(response)
    except ValueError as exc:
        return invalid_input_error(
            resource_type="raw_command",
            message=str(exc),
            input_payload={
                "digital_twin_instance_id": digital_twin_instance_id,
                "request_endpoint": request_endpoint,
                "request_data_format": request_data_format,
            },
            retry_hint="Retry with valid raw command inputs for the selected format.",
        )
    except Exception as e:
        logger.error(f"Error invoking raw command for digital twin instance {digital_twin_instance_id}: {e}")
        raise


@tool(
    description="Lists all OCI compartments that the current user has access to."
)
def list_compartments(
    include_root: Annotated[bool, "Include the root tenancy compartment"] = True
):
    try:
        identity_client, tenancy_id = get_identity_client()
        from .models import CompartmentModel

        compartments = []

        if include_root:
            try:
                root_compartment = identity_client.get_compartment(compartment_id=tenancy_id).data
                compartments.append(root_compartment)
            except Exception as root_error:
                logger.warning(f"Unable to load root tenancy compartment {tenancy_id}: {root_error}")

        list_result = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            compartment_id=tenancy_id,
            compartment_id_in_subtree=True,
            access_level="ACCESSIBLE",
        )
        compartments.extend(_normalize_items(list_result.data))

        deduped = {}
        for compartment in compartments:
            compartment_id = getattr(compartment, "id", None)
            if compartment_id:
                deduped[compartment_id] = compartment

        return _result_payload(
            [CompartmentModel.from_oci_model(compartment).model_dump() for compartment in deduped.values()]
        )
    except Exception as e:
        logger.error(f"Error listing compartments: {e}")
        raise


@tool(
    description="Lists raw data records from the Oracle IoT Data API for a specific IoT domain."
)
def list_raw_data(
    iot_domain_group_short_id: Annotated[
        str,
        "The IoT domain group short identifier used by the Data API host",
    ],
    iot_domain_short_id: Annotated[str, "The IoT domain short identifier used by the Data API path"],
    query_params: Annotated[
        Optional[dict[str, Any] | str],
        "Optional Data API query parameters as an object or JSON string",
    ] = None,
    region: Annotated[
        Optional[str],
        "OCI region for the IoT Data API endpoint; defaults to the configured OCI profile region",
    ] = None,
    access_token: Annotated[
        Optional[str],
        "Bearer token for the IoT Data API; defaults to OCI_IOT_DATA_API_ACCESS_TOKEN if omitted",
    ] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    return _call_iot_data_api(
        resource_path="/rawData",
        iot_domain_group_short_id=iot_domain_group_short_id,
        iot_domain_short_id=iot_domain_short_id,
        query_params=query_params,
        region=region,
        access_token=access_token,
        opc_request_id=opc_request_id,
    )


@tool(
    description="Gets a raw data record by identifier from the Oracle IoT Data API for a specific IoT domain."
)
def get_raw_data(
    iot_domain_group_short_id: Annotated[
        str,
        "The IoT domain group short identifier used by the Data API host",
    ],
    iot_domain_short_id: Annotated[str, "The IoT domain short identifier used by the Data API path"],
    record_id: Annotated[str, "The raw data record identifier"],
    region: Annotated[
        Optional[str],
        "OCI region for the IoT Data API endpoint; defaults to the configured OCI profile region",
    ] = None,
    access_token: Annotated[
        Optional[str],
        "Bearer token for the IoT Data API; defaults to OCI_IOT_DATA_API_ACCESS_TOKEN if omitted",
    ] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    return _call_iot_data_api(
        resource_path=f"/rawData/{record_id}",
        iot_domain_group_short_id=iot_domain_group_short_id,
        iot_domain_short_id=iot_domain_short_id,
        region=region,
        access_token=access_token,
        opc_request_id=opc_request_id,
    )


@tool(
    description="Lists rejected data records from the Oracle IoT Data API for a specific IoT domain."
)
def list_rejected_data(
    iot_domain_group_short_id: Annotated[
        str,
        "The IoT domain group short identifier used by the Data API host",
    ],
    iot_domain_short_id: Annotated[str, "The IoT domain short identifier used by the Data API path"],
    query_params: Annotated[
        Optional[dict[str, Any] | str],
        "Optional Data API query parameters as an object or JSON string",
    ] = None,
    region: Annotated[
        Optional[str],
        "OCI region for the IoT Data API endpoint; defaults to the configured OCI profile region",
    ] = None,
    access_token: Annotated[
        Optional[str],
        "Bearer token for the IoT Data API; defaults to OCI_IOT_DATA_API_ACCESS_TOKEN if omitted",
    ] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    return _call_iot_data_api(
        resource_path="/rejectedData",
        iot_domain_group_short_id=iot_domain_group_short_id,
        iot_domain_short_id=iot_domain_short_id,
        query_params=query_params,
        region=region,
        access_token=access_token,
        opc_request_id=opc_request_id,
    )


@tool(
    description="Gets a rejected data record by identifier from the Oracle IoT Data API for a specific IoT domain."
)
def get_rejected_data(
    iot_domain_group_short_id: Annotated[
        str,
        "The IoT domain group short identifier used by the Data API host",
    ],
    iot_domain_short_id: Annotated[str, "The IoT domain short identifier used by the Data API path"],
    record_id: Annotated[str, "The rejected data record identifier"],
    region: Annotated[
        Optional[str],
        "OCI region for the IoT Data API endpoint; defaults to the configured OCI profile region",
    ] = None,
    access_token: Annotated[
        Optional[str],
        "Bearer token for the IoT Data API; defaults to OCI_IOT_DATA_API_ACCESS_TOKEN if omitted",
    ] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    return _call_iot_data_api(
        resource_path=f"/rejectedData/{record_id}",
        iot_domain_group_short_id=iot_domain_group_short_id,
        iot_domain_short_id=iot_domain_short_id,
        region=region,
        access_token=access_token,
        opc_request_id=opc_request_id,
    )


@tool(
    description="Lists snapshot data records from the Oracle IoT Data API for a specific IoT domain."
)
def list_snapshot_data(
    iot_domain_group_short_id: Annotated[
        str,
        "The IoT domain group short identifier used by the Data API host",
    ],
    iot_domain_short_id: Annotated[str, "The IoT domain short identifier used by the Data API path"],
    query_params: Annotated[
        Optional[dict[str, Any] | str],
        "Optional Data API query parameters as an object or JSON string",
    ] = None,
    region: Annotated[
        Optional[str],
        "OCI region for the IoT Data API endpoint; defaults to the configured OCI profile region",
    ] = None,
    access_token: Annotated[
        Optional[str],
        "Bearer token for the IoT Data API; defaults to OCI_IOT_DATA_API_ACCESS_TOKEN if omitted",
    ] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    return _call_iot_data_api(
        resource_path="/snapshotData",
        iot_domain_group_short_id=iot_domain_group_short_id,
        iot_domain_short_id=iot_domain_short_id,
        query_params=query_params,
        region=region,
        access_token=access_token,
        opc_request_id=opc_request_id,
    )


@tool(
    description="Lists historized data records from the Oracle IoT Data API for a specific IoT domain."
)
def list_historized_data(
    iot_domain_group_short_id: Annotated[
        str,
        "The IoT domain group short identifier used by the Data API host",
    ],
    iot_domain_short_id: Annotated[str, "The IoT domain short identifier used by the Data API path"],
    query_params: Annotated[
        Optional[dict[str, Any] | str],
        "Optional Data API query parameters as an object or JSON string",
    ] = None,
    region: Annotated[
        Optional[str],
        "OCI region for the IoT Data API endpoint; defaults to the configured OCI profile region",
    ] = None,
    access_token: Annotated[
        Optional[str],
        "Bearer token for the IoT Data API; defaults to OCI_IOT_DATA_API_ACCESS_TOKEN if omitted",
    ] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    return _call_iot_data_api(
        resource_path="/historizedData",
        iot_domain_group_short_id=iot_domain_group_short_id,
        iot_domain_short_id=iot_domain_short_id,
        query_params=query_params,
        region=region,
        access_token=access_token,
        opc_request_id=opc_request_id,
    )


@tool(
    description="Gets a historized data record by identifier from the Oracle IoT Data API for a specific IoT domain."
)
def get_historized_data(
    iot_domain_group_short_id: Annotated[
        str,
        "The IoT domain group short identifier used by the Data API host",
    ],
    iot_domain_short_id: Annotated[str, "The IoT domain short identifier used by the Data API path"],
    record_id: Annotated[str, "The historized data record identifier"],
    region: Annotated[
        Optional[str],
        "OCI region for the IoT Data API endpoint; defaults to the configured OCI profile region",
    ] = None,
    access_token: Annotated[
        Optional[str],
        "Bearer token for the IoT Data API; defaults to OCI_IOT_DATA_API_ACCESS_TOKEN if omitted",
    ] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    return _call_iot_data_api(
        resource_path=f"/historizedData/{record_id}",
        iot_domain_group_short_id=iot_domain_group_short_id,
        iot_domain_short_id=iot_domain_short_id,
        region=region,
        access_token=access_token,
        opc_request_id=opc_request_id,
    )


@tool(
    description="Lists raw command data records from the Oracle IoT Data API for a specific IoT domain."
)
def list_raw_command_data(
    iot_domain_group_short_id: Annotated[
        str,
        "The IoT domain group short identifier used by the Data API host",
    ],
    iot_domain_short_id: Annotated[str, "The IoT domain short identifier used by the Data API path"],
    query_params: Annotated[
        Optional[dict[str, Any] | str],
        "Optional Data API query parameters as an object or JSON string",
    ] = None,
    region: Annotated[
        Optional[str],
        "OCI region for the IoT Data API endpoint; defaults to the configured OCI profile region",
    ] = None,
    access_token: Annotated[
        Optional[str],
        "Bearer token for the IoT Data API; defaults to OCI_IOT_DATA_API_ACCESS_TOKEN if omitted",
    ] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    return _call_iot_data_api(
        resource_path="/rawCommandData",
        iot_domain_group_short_id=iot_domain_group_short_id,
        iot_domain_short_id=iot_domain_short_id,
        query_params=query_params,
        region=region,
        access_token=access_token,
        opc_request_id=opc_request_id,
    )


@tool(
    description="Gets a raw command data record by identifier from the Oracle IoT Data API for a specific IoT domain."
)
def get_raw_command_data(
    iot_domain_group_short_id: Annotated[
        str,
        "The IoT domain group short identifier used by the Data API host",
    ],
    iot_domain_short_id: Annotated[str, "The IoT domain short identifier used by the Data API path"],
    record_id: Annotated[str, "The raw command data record identifier"],
    region: Annotated[
        Optional[str],
        "OCI region for the IoT Data API endpoint; defaults to the configured OCI profile region",
    ] = None,
    access_token: Annotated[
        Optional[str],
        "Bearer token for the IoT Data API; defaults to OCI_IOT_DATA_API_ACCESS_TOKEN if omitted",
    ] = None,
    opc_request_id: Annotated[Optional[str], "A unique Oracle-assigned identifier for the request"] = None,
):
    return _call_iot_data_api(
        resource_path=f"/rawCommandData/{record_id}",
        iot_domain_group_short_id=iot_domain_group_short_id,
        iot_domain_short_id=iot_domain_short_id,
        region=region,
        access_token=access_token,
        opc_request_id=opc_request_id,
    )

@tool(
    description="Return the full mapped digital twin adapter payload for debugging and migration workflows."
)
def get_digital_twin_adapter_full(
    digital_twin_adapter_id: Annotated[str, "The digital twin adapter OCID"],
):
    return _as_tool_result(get_digital_twin_adapter_record(digital_twin_adapter_id))


@tool(description="Return the control-plane and domain-context resources that explain how a twin is wired into OCI IoT.")
def get_twin_platform_context(
    digital_twin_instance_id: Annotated[str | None, "The digital twin instance OCID"] = None,
    digital_twin_instance_name: Annotated[str | None, "The digital twin instance display name"] = None,
    iot_domain_id: Annotated[str | None, "The IoT domain OCID for friendly twin lookup"] = None,
    iot_domain_display_name: Annotated[str | None, "The IoT domain display name for friendly twin lookup"] = None,
    domain_short_id: Annotated[str | None, "The IoT domain short ID for friendly twin lookup"] = None,
    compartment_id: Annotated[str | None, "Compartment OCID for friendly domain lookup"] = None,
):
    return _as_tool_result(
        get_twin_platform_context_impl(
            digital_twin_instance_id=digital_twin_instance_id,
            digital_twin_instance_name=digital_twin_instance_name,
            iot_domain_id=iot_domain_id,
            iot_domain_display_name=iot_domain_display_name,
            domain_short_id=domain_short_id,
            compartment_id=compartment_id,
        )
    )


@tool(description="Derive normalized IoT domain context for ORDS and operator workflows.")
def derive_domain_context(
    iot_domain_id: Annotated[str | None, "The IoT domain OCID"] = None,
    iot_domain_display_name: Annotated[str | None, "The IoT domain display name"] = None,
    domain_short_id: Annotated[str | None, "The IoT domain short ID"] = None,
    compartment_id: Annotated[str | None, "Compartment OCID for friendly domain lookup"] = None,
):
    context = resolve_domain_context_for_tool(
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    return _as_tool_result(context)


@tool(description="Return the latest observed snapshot, historized, raw-command, and rejected-data records for a twin.")
def get_latest_twin_state(
    digital_twin_instance_id: Annotated[str | None, "The digital twin instance OCID"] = None,
    digital_twin_instance_name: Annotated[str | None, "The digital twin instance display name"] = None,
    iot_domain_id: Annotated[str | None, "The IoT domain OCID for friendly twin lookup"] = None,
    iot_domain_display_name: Annotated[str | None, "The IoT domain display name for friendly twin lookup"] = None,
    domain_short_id: Annotated[str | None, "The IoT domain short ID for friendly twin lookup"] = None,
    compartment_id: Annotated[str | None, "Compartment OCID for friendly domain lookup"] = None,
):
    return _as_tool_result(
        get_latest_twin_state_impl(
            digital_twin_instance_id=digital_twin_instance_id,
            digital_twin_instance_name=digital_twin_instance_name,
            iot_domain_id=iot_domain_id,
            iot_domain_display_name=iot_domain_display_name,
            domain_short_id=domain_short_id,
            compartment_id=compartment_id,
        )
    )


@tool(description="Passively validate whether a twin is reporting snapshot data.")
def validate_twin_readiness(
    digital_twin_instance_id: Annotated[str | None, "The digital twin instance OCID"] = None,
    digital_twin_instance_name: Annotated[str | None, "The digital twin instance display name"] = None,
    iot_domain_id: Annotated[str | None, "The IoT domain OCID for friendly twin lookup"] = None,
    iot_domain_display_name: Annotated[str | None, "The IoT domain display name for friendly twin lookup"] = None,
    domain_short_id: Annotated[str | None, "The IoT domain short ID for friendly twin lookup"] = None,
    compartment_id: Annotated[str | None, "Compartment OCID for friendly domain lookup"] = None,
):
    return _as_tool_result(
        validate_twin_readiness_impl(
            digital_twin_instance_id=digital_twin_instance_id,
            digital_twin_instance_name=digital_twin_instance_name,
            iot_domain_id=iot_domain_id,
            iot_domain_display_name=iot_domain_display_name,
            domain_short_id=domain_short_id,
            compartment_id=compartment_id,
        )
    )


@tool(description="Mint and return an IoT Data API bearer token plus the resolved domain context.")
def get_data_api_token(
    iot_domain_id: Annotated[str | None, "The IoT domain OCID"] = None,
    iot_domain_display_name: Annotated[str | None, "The IoT domain display name"] = None,
    domain_short_id: Annotated[str | None, "The IoT domain short ID"] = None,
    compartment_id: Annotated[str | None, "Compartment OCID for friendly domain lookup"] = None,
):
    token_payload = get_data_api_token_impl(
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    return _as_tool_result(token_payload)


@tool(description="Fetch the raw command detail record for an ORDS request ID.")
def get_raw_command_by_request_id(
    request_id: Annotated[str, "The IoT Data API raw command record ID"],
    iot_domain_id: Annotated[str | None, "The IoT domain OCID"] = None,
    iot_domain_display_name: Annotated[str | None, "The IoT domain display name"] = None,
    domain_short_id: Annotated[str | None, "The IoT domain short ID"] = None,
    compartment_id: Annotated[str | None, "Compartment OCID for friendly domain lookup"] = None,
    digital_twin_instance_id: Annotated[str | None, "Optional digital twin OCID for validation"] = None,
    digital_twin_instance_name: Annotated[str | None, "Optional digital twin display name for validation"] = None,
    since: Annotated[str | None, "Optional RFC 3339 lower bound for validation"] = None,
    until: Annotated[str | None, "Optional RFC 3339 upper bound for validation"] = None,
):
    return _as_tool_result(
        get_raw_command_by_request_id_impl(
            request_id=request_id,
            iot_domain_id=iot_domain_id,
            iot_domain_display_name=iot_domain_display_name,
            domain_short_id=domain_short_id,
            compartment_id=compartment_id,
            digital_twin_instance_id=digital_twin_instance_id,
            digital_twin_instance_name=digital_twin_instance_name,
            since=since,
            until=until,
        )
    )


@tool(description="List recent raw command records for a digital twin instance.")
def list_recent_raw_commands_for_twin(
    digital_twin_instance_id: Annotated[str | None, "The digital twin instance OCID"] = None,
    digital_twin_instance_name: Annotated[str | None, "The digital twin instance display name"] = None,
    iot_domain_id: Annotated[str | None, "The IoT domain OCID for friendly twin lookup"] = None,
    iot_domain_display_name: Annotated[str | None, "The IoT domain display name for friendly twin lookup"] = None,
    domain_short_id: Annotated[str | None, "The IoT domain short ID for friendly twin lookup"] = None,
    compartment_id: Annotated[str | None, "Compartment OCID for friendly domain lookup"] = None,
    limit: Annotated[int, "Maximum records to return"] = 20,
    since: Annotated[str | None, "Optional RFC 3339 lower bound"] = None,
    until: Annotated[str | None, "Optional RFC 3339 upper bound"] = None,
):
    limit_error = _limit_error(field_name="limit", value=limit)
    if limit_error:
        return limit_error
    rows = list_recent_raw_commands_for_twin_impl(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
        limit=limit,
        since=since,
        until=until,
    )
    if _is_error(rows):
        return rows
    ordered = _sort_desc(rows, "time_created")
    return _as_tool_result(ordered[:limit])


@tool(description="Invoke a raw command on a digital twin instance and wait for a terminal data-plane result.")
def invoke_raw_command_and_wait(
    digital_twin_instance_id: Annotated[str | None, "The digital twin instance OCID"] = None,
    digital_twin_instance_name: Annotated[str | None, "The digital twin instance display name"] = None,
    iot_domain_id: Annotated[str | None, "The IoT domain OCID for friendly twin lookup"] = None,
    iot_domain_display_name: Annotated[str | None, "The IoT domain display name for friendly twin lookup"] = None,
    domain_short_id: Annotated[str | None, "The IoT domain short ID for friendly twin lookup"] = None,
    compartment_id: Annotated[str | None, "Compartment OCID for friendly domain lookup"] = None,
    request_endpoint: Annotated[str, "Device endpoint for the outbound request"] = "",
    request_data_format: Annotated[str, "TEXT, JSON, or BINARY"] = "TEXT",
    request_data: Annotated[object, "Request payload"] = "",
    response_endpoint: Annotated[str | None, "Optional response endpoint"] = None,
    request_duration: Annotated[str | None, "Request duration string"] = None,
    response_duration: Annotated[str | None, "Response duration string"] = None,
    timeout: Annotated[int, "Maximum seconds to wait for a terminal result"] = 30,
):
    result = invoke_raw_command_and_wait_impl(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
        request_endpoint=request_endpoint,
        request_data_format=request_data_format,
        request_data=request_data,
        response_endpoint=response_endpoint,
        request_duration=request_duration,
        response_duration=response_duration,
        timeout=timeout,
    )
    return _as_tool_result(result)


@tool(description="Wait for a twin snapshot update after a given timestamp.")
def wait_for_twin_update(
    digital_twin_instance_id: Annotated[str | None, "The digital twin instance OCID"] = None,
    digital_twin_instance_name: Annotated[str | None, "The digital twin instance display name"] = None,
    iot_domain_id: Annotated[str | None, "The IoT domain OCID for friendly twin lookup"] = None,
    iot_domain_display_name: Annotated[str | None, "The IoT domain display name for friendly twin lookup"] = None,
    domain_short_id: Annotated[str | None, "The IoT domain short ID for friendly twin lookup"] = None,
    compartment_id: Annotated[str | None, "Compartment OCID for friendly domain lookup"] = None,
    content_path: Annotated[str | None, "Optional exact snapshot content path"] = None,
    since: Annotated[str, "RFC 3339 timestamp"] = "",
    timeout: Annotated[int, "Maximum seconds to wait"] = 30,
):
    if not since:
        return error_result(
            code="invalid_input",
            message="since is required and must be an RFC 3339 timestamp.",
            retry_hint="Retry with since set to an RFC 3339 timestamp.",
            details={"since": since},
        )
    return _as_tool_result(
        wait_for_twin_update_impl(
            digital_twin_instance_id=digital_twin_instance_id,
            digital_twin_instance_name=digital_twin_instance_name,
            iot_domain_id=iot_domain_id,
            iot_domain_display_name=iot_domain_display_name,
            domain_short_id=domain_short_id,
            compartment_id=compartment_id,
            content_path=content_path,
            since=since,
            timeout=timeout,
        )
    )


@tool(description="List recent rejected ingest records for a digital twin instance.")
def list_recent_rejected_data_for_twin(
    digital_twin_instance_id: Annotated[str | None, "The digital twin instance OCID"] = None,
    digital_twin_instance_name: Annotated[str | None, "The digital twin instance display name"] = None,
    iot_domain_id: Annotated[str | None, "The IoT domain OCID for friendly twin lookup"] = None,
    iot_domain_display_name: Annotated[str | None, "The IoT domain display name for friendly twin lookup"] = None,
    domain_short_id: Annotated[str | None, "The IoT domain short ID for friendly twin lookup"] = None,
    compartment_id: Annotated[str | None, "Compartment OCID for friendly domain lookup"] = None,
    limit: Annotated[int, "Maximum records to return"] = 20,
    since: Annotated[str | None, "Optional RFC 3339 lower bound"] = None,
    until: Annotated[str | None, "Optional RFC 3339 upper bound"] = None,
):
    limit_error = _limit_error(field_name="limit", value=limit)
    if limit_error:
        return limit_error
    rows = list_recent_rejected_data_for_twin_impl(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
        limit=limit,
        since=since,
        until=until,
    )
    if _is_error(rows):
        return rows
    ordered = _sort_desc(rows, "time_received")
    return _as_tool_result(ordered[:limit])

@tool(
    description="Health check endpoint for the OCI IoT MCP server."
)
def health_check():
    """Health check endpoint that verifies the server is running."""
    return {
        "status": "healthy",
        "service": "oci-iot-mcp-server",
        "version": __version__
    }

def main():
    """Main function to run the MCP server."""
    try:
        mcp.run()
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        raise

if __name__ == "__main__":
    main()
