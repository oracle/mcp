"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import hashlib
import json
import logging
import os
from typing import Any, Callable, Optional

import oci
from fastmcp import FastMCP
from oci import Response
from pydantic import Field
from pydantic.fields import FieldInfo

from . import __project__
from .client_factory import get_opensearch_cluster_client
from .models import (
    BACKUP_CLUSTER_MINIMAL_EXAMPLE,
    CREATE_CLUSTER_NON_SHAPE_DEFAULT_DETAILS,
    CREATE_CLUSTER_MINIMAL_EXAMPLE,
    CREATE_CLUSTER_REQUIRED_FIELDS,
    HOST_TYPE_ALLOWED_VALUES,
    HOST_TYPE_FLEX_ONLY_ALLOWED_VALUES,
    HOST_TYPE_FLEX,
    SECURITY_MODE_ENFORCING,
    BackupOpensearchClusterDetailsInput,
    CreateOpensearchClusterDetailsInput,
    ResizeOpensearchClusterHorizontalDetailsInput,
    ResizeOpensearchClusterVerticalDetailsInput,
    UpdateOpensearchClusterDetailsInput,
)
from .sdk_adapters import (
    build_backup_opensearch_cluster_details,
    build_create_opensearch_cluster_details,
    build_resize_opensearch_cluster_horizontal_details,
    build_resize_opensearch_cluster_vertical_details,
    build_update_opensearch_cluster_details,
)
from .scripts import (
    OPENSEARCH_API_GUIDE,
    TOOL_SURFACE_SUMMARY,
    WORK_REQUEST_GUIDE,
    get_script_content,
)

logger = logging.getLogger(__name__)

CERTIFICATE_MODE_OCI_CERTIFICATES_SERVICE = "OCI_CERTIFICATES_SERVICE"
CERTIFICATE_MODE_OPENSEARCH_SERVICE = "OPENSEARCH_SERVICE"
CERTIFICATE_MODE_ALLOWED_VALUES = (
    CERTIFICATE_MODE_OCI_CERTIFICATES_SERVICE,
    CERTIFICATE_MODE_OPENSEARCH_SERVICE,
)

mcp = FastMCP(
    name=__project__,
    instructions="""
        This server exposes OCI OpenSearch cluster control-plane operations for MVP usage.
        Most mutating operations are asynchronous and return an opc_work_request_id.
        After an async response, call get_work_request at most once for an immediate status snapshot,
        then ask the user whether they want another status check instead of polling continuously.
        For request bodies, use OCI SDK snake_case field names.
        Use list_opensearch_cluster_shapes before setting *_host_shape values for create or vertical resize.
    """,
)


def _serialize(data: Any) -> Any:
    if data is None:
        return None

    if isinstance(data, (bytes, bytearray)):
        data = data.decode("utf-8")

    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data

    try:
        return oci.util.to_dict(data)
    except Exception:
        if isinstance(data, list):
            return [_serialize(item) for item in data]
        if isinstance(data, dict):
            return {key: _serialize(value) for key, value in data.items()}
        return data


def _normalize_items(data: Any) -> list[Any]:
    if data is None:
        return []

    items = data.get("items", data) if isinstance(data, dict) else getattr(data, "items", data)
    serialized = _serialize(items)
    if serialized is None:
        return []
    return serialized if isinstance(serialized, list) else [serialized]


def _async_response(
    response: Response,
    opc_retry_token: Optional[str] = None,
    opc_retry_token_source: Optional[str] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": response.status}

    opc_request_id = None
    opc_work_request_id = None
    if response.headers is not None:
        opc_request_id = response.headers.get("opc-request-id")
        opc_work_request_id = response.headers.get("opc-work-request-id")

    if opc_request_id:
        payload["opc_request_id"] = opc_request_id
    if opc_retry_token:
        payload["opc_retry_token"] = opc_retry_token
    if opc_retry_token_source:
        payload["opc_retry_token_source"] = opc_retry_token_source
    if opc_work_request_id:
        payload["opc_work_request_id"] = opc_work_request_id
        payload["async_operation"] = True
        payload["status_check_policy"] = "single_get_work_request_then_ask_user"
        payload["recommended_next_action"] = (
            "Call get_work_request once for an immediate status snapshot if useful, then ask the user "
            "whether to check again later instead of polling continuously."
        )
    if response.data is not None:
        serialized_data = _serialize(response.data)
        payload["data"] = serialized_data

        if isinstance(serialized_data, dict):
            cluster_id = serialized_data.get("id")
            lifecycle_state = serialized_data.get("lifecycle_state")

            if cluster_id:
                payload["cluster_id"] = cluster_id
            if lifecycle_state:
                payload["lifecycle_state"] = lifecycle_state

    return payload


def _service_error_payload(exc: oci.exceptions.ServiceError) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": exc.status,
        "code": exc.code,
        "message": exc.message,
    }
    if exc.request_id:
        payload["opc_request_id"] = exc.request_id
    return payload


def _async_operation_response(
    operation_name: str,
    call: Callable[[], Response],
    opc_retry_token: Optional[str] = None,
    opc_retry_token_source: Optional[str] = None,
) -> dict[str, Any]:
    try:
        response = call()
    except oci.exceptions.ServiceError as exc:
        logger.warning("%s request failed: %s", operation_name, exc)
        payload = _service_error_payload(exc)
        if opc_retry_token:
            payload["opc_retry_token"] = opc_retry_token
        if opc_retry_token_source:
            payload["opc_retry_token_source"] = opc_retry_token_source
        return payload
    return _async_response(
        response,
        opc_retry_token=opc_retry_token,
        opc_retry_token_source=opc_retry_token_source,
    )


def _canonical_json(data: Any) -> str:
    return json.dumps(_serialize(data), sort_keys=True, separators=(",", ":"), default=str)


def _deterministic_retry_token(prefix: str, payload: dict[str, Any]) -> str:
    digest_length = 64 - len(prefix)
    if digest_length <= 0:
        raise ValueError("Retry token prefix must be shorter than 64 characters.")
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return prefix + digest[:digest_length]


def _effective_retry_token(
    caller_retry_token: Optional[str],
    generated_prefix: str,
    generated_payload: dict[str, Any],
) -> tuple[str, str]:
    if _is_explicit_value(caller_retry_token):
        if not isinstance(caller_retry_token, str) or not caller_retry_token.strip():
            raise ValueError("`opc_retry_token` must be a non-empty string.")
        if len(caller_retry_token) > 64:
            raise ValueError("`opc_retry_token` must be 64 characters or fewer.")
        return caller_retry_token, "caller"

    return _deterministic_retry_token(generated_prefix, generated_payload), "generated"


def _validate_create_opensearch_cluster_details(
    details: CreateOpensearchClusterDetailsInput,
) -> dict[str, Any]:
    payload = details.model_dump(exclude_none=True)
    missing_fields = [field for field in CREATE_CLUSTER_REQUIRED_FIELDS if field not in payload]

    if missing_fields:
        raise ValueError(
            "Missing required create_opensearch_cluster_details field(s): "
            + ", ".join(missing_fields)
            + ". "
            + f"Minimal payload: {CREATE_CLUSTER_MINIMAL_EXAMPLE}"
        )

    if "security_master_user_password" in payload:
        raise ValueError(
            "`security_master_user_password` is not accepted. Provide only `security_master_user_password_hash`. "
            "See OCI docs: https://docs.oracle.com/en-us/iaas/Content/search-opensearch/Tasks/manageociopensearch.htm#password_hash"
        )

    username = payload.get("security_master_user_name")
    if not isinstance(username, str) or not username.strip():
        raise ValueError("`security_master_user_name` is required and must be a non-empty string.")
    if username.lower() == "admin":
        raise ValueError("`security_master_user_name` cannot be `admin`; OCI reserves this username.")

    password_hash = payload.get("security_master_user_password_hash")
    if (
        not isinstance(password_hash, str)
        or not password_hash.strip()
        or not password_hash.startswith("pbkdf2_stretch_1000")
    ):
        raise ValueError(
            "`security_master_user_password_hash` is required and must be a non-empty OCI-compatible hash in "
            "`pbkdf2_stretch_1000` format. See OCI docs: "
            "https://docs.oracle.com/en-us/iaas/Content/search-opensearch/Tasks/manageociopensearch.htm#password_hash"
        )

    security_mode = payload.get("security_mode")
    if security_mode is not None and security_mode != SECURITY_MODE_ENFORCING:
        raise ValueError("`security_mode` must be `ENFORCING`. Other security modes are not supported.")

    payload["security_mode"] = SECURITY_MODE_ENFORCING

    for field_name in ("master_node_host_type", "data_node_host_type"):
        host_type = payload.get(field_name)
        if host_type is not None and host_type not in HOST_TYPE_ALLOWED_VALUES:
            raise ValueError(f"`{field_name}` must be one of: " + ", ".join(HOST_TYPE_ALLOWED_VALUES))

    for field_name in ("search_node_host_type", "ml_node_host_type"):
        host_type = payload.get(field_name)
        if host_type is not None and host_type not in HOST_TYPE_FLEX_ONLY_ALLOWED_VALUES:
            raise ValueError(
                f"`{field_name}` must be one of: " + ", ".join(HOST_TYPE_FLEX_ONLY_ALLOWED_VALUES)
            )

    return payload


def _build_create_opensearch_cluster_payload(
    details: CreateOpensearchClusterDetailsInput,
) -> dict[str, Any]:
    payload = dict(CREATE_CLUSTER_NON_SHAPE_DEFAULT_DETAILS)
    payload.update(_validate_create_opensearch_cluster_details(details))
    _validate_certificate_config(payload.get("certificate_config"))
    for shape_field, host_type_field in (
        ("master_node_host_shape", "master_node_host_type"),
        ("data_node_host_shape", "data_node_host_type"),
        ("search_node_host_shape", "search_node_host_type"),
        ("ml_node_host_shape", "ml_node_host_type"),
    ):
        if payload.get(shape_field) and not payload.get(host_type_field):
            payload[host_type_field] = HOST_TYPE_FLEX
    return payload


def _validate_certificate_config(certificate_config: Any) -> None:
    if certificate_config is None:
        return
    if not isinstance(certificate_config, dict):
        return

    for mode_field, certificate_id_field in (
        ("cluster_certificate_mode", "open_search_api_certificate_id"),
        ("dashboard_certificate_mode", "open_search_dashboard_certificate_id"),
    ):
        mode = certificate_config.get(mode_field)
        certificate_id = certificate_config.get(certificate_id_field)
        if mode is None:
            continue
        if mode not in CERTIFICATE_MODE_ALLOWED_VALUES:
            raise ValueError(
                f"`certificate_config.{mode_field}` value `{mode}` is invalid; must be one of: "
                + ", ".join(CERTIFICATE_MODE_ALLOWED_VALUES)
                + ". Use `OCI_CERTIFICATES_SERVICE` for BYOC certificates stored in OCI Certificates service; "
            )
        if mode == CERTIFICATE_MODE_OCI_CERTIFICATES_SERVICE and not certificate_id:
            raise ValueError(
                f"`certificate_config.{certificate_id_field}` is required when "
                f"`certificate_config.{mode_field}` is `OCI_CERTIFICATES_SERVICE`."
            )
        if mode == CERTIFICATE_MODE_OPENSEARCH_SERVICE and certificate_id:
            raise ValueError(
                f"`certificate_config.{certificate_id_field}` must be omitted when "
                f"`certificate_config.{mode_field}` is `OPENSEARCH_SERVICE`."
            )


def _validate_update_opensearch_cluster_details(payload: dict[str, Any]) -> None:
    security_fields = (
        "security_mode",
        "security_master_user_name",
        "security_master_user_password_hash",
        "security_saml_config",
    )
    has_security_update = any(field in payload for field in security_fields)
    if not has_security_update:
        return

    if "security_mode" not in payload:
        raise ValueError(
            "Security updates require `update_details.security_mode`. "
            "To update the master-user password hash, provide `security_mode`, "
            "`security_master_user_name`, and `security_master_user_password_hash`."
        )

    username = payload.get("security_master_user_name")
    password_hash = payload.get("security_master_user_password_hash")
    has_username = username is not None
    has_password_hash = password_hash is not None
    if has_username != has_password_hash:
        raise ValueError(
            "Security master-user updates require both `security_master_user_name` and "
            "`security_master_user_password_hash`."
        )

    if has_username:
        if not isinstance(username, str) or not username.strip():
            raise ValueError("`security_master_user_name` must be a non-empty string for security updates.")
        if username.lower() == "admin":
            raise ValueError("`security_master_user_name` cannot be `admin`; OCI reserves this username.")
        if payload.get("security_mode") == "DISABLED":
            raise ValueError(
                "Do not provide security master-user credentials when `security_mode` is `DISABLED`."
            )
        if (
            not isinstance(password_hash, str)
            or not password_hash.strip()
            or not password_hash.startswith("pbkdf2_stretch_1000")
        ):
            raise ValueError(
                "`security_master_user_password_hash` must be a non-empty OCI-compatible hash in "
                "`pbkdf2_stretch_1000` format."
            )


def _paginated_list(
    method: Callable[..., Response],
    *args: Any,
    limit: Optional[int] = None,
    **kwargs: Any,
) -> list[Any]:
    results: list[Any] = []
    next_page: Optional[str] = None

    while True:
        call_kwargs = dict(kwargs)
        if next_page is not None:
            call_kwargs["page"] = next_page

        if limit is not None:
            remaining = limit - len(results)
            if remaining <= 0:
                break
            call_kwargs["limit"] = remaining
        elif call_kwargs.get("limit") is None:
            call_kwargs.pop("limit", None)

        response = method(*args, **call_kwargs)
        results.extend(_normalize_items(response.data))

        if not response.has_next_page:
            break
        next_page = response.next_page

    return results


def _is_explicit_value(value: Any) -> bool:
    return value is not None and not isinstance(value, FieldInfo)


def _optional_kwargs(**kwargs: Any) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if _is_explicit_value(value)}


@mcp.resource(
    name="OCI OpenSearch API Guide",
    uri="resource://oci-opensearch-api-guide",
    description="MVP guidance for using OCI OpenSearch cluster tools and work-request tracking.",
)
def opensearch_api_guide() -> str:
    return get_script_content(OPENSEARCH_API_GUIDE)


@mcp.resource(
    name="OCI OpenSearch Work Request Guide",
    uri="resource://oci-opensearch-work-request-guide",
    description="Guidance for following async OpenSearch work requests and triaging failures.",
)
def work_request_guide() -> str:
    return get_script_content(WORK_REQUEST_GUIDE)


@mcp.resource(
    name="OCI OpenSearch Tool Surface Summary",
    uri="resource://oci-opensearch-tool-surface-summary",
    description="Short summary of the current OCI OpenSearch MCP tool surface and deferred families.",
)
def tool_surface_summary() -> str:
    return get_script_content(TOOL_SURFACE_SUMMARY)


@mcp.tool(description="List OpenSearch clusters in a compartment.")
def list_opensearch_clusters(
    compartment_id: str = Field(..., description="The OCID of the compartment."),
    lifecycle_state: Optional[str] = Field(None, description="Optional lifecycle state filter."),
    display_name: Optional[str] = Field(None, description="Optional exact display name filter."),
    cluster_id: Optional[str] = Field(None, description="Optional OpenSearch cluster OCID filter."),
    limit: Optional[int] = Field(None, description="Maximum number of items to return."),
    sort_order: Optional[str] = Field(None, description="Sort order: ASC or DESC."),
    sort_by: Optional[str] = Field(None, description="Sort by field: timeCreated or displayName."),
    opc_request_id: Optional[str] = Field(None, description="Optional request ID for tracing."),
) -> list[dict[str, Any]] | dict[str, Any]:
    client = get_opensearch_cluster_client()
    optional_kwargs = _optional_kwargs(
        lifecycle_state=lifecycle_state,
        display_name=display_name,
        id=cluster_id,
        sort_order=sort_order,
        sort_by=sort_by,
        opc_request_id=opc_request_id,
    )
    try:
        return _paginated_list(
            client.list_opensearch_clusters,
            compartment_id,
            limit=limit if _is_explicit_value(limit) else None,
            **optional_kwargs,
        )
    except oci.exceptions.ServiceError as exc:
        logger.warning("List OpenSearch clusters failed: %s", exc)
        return _service_error_payload(exc)


@mcp.tool(description="Get an OpenSearch cluster by OCID.")
def get_opensearch_cluster(
    opensearch_cluster_id: str = Field(..., description="The OCID of the OpenSearch cluster."),
    opc_request_id: Optional[str] = Field(None, description="Optional request ID for tracing."),
) -> dict[str, Any]:
    client = get_opensearch_cluster_client()
    optional_kwargs = _optional_kwargs(opc_request_id=opc_request_id)
    try:
        response = client.get_opensearch_cluster(opensearch_cluster_id, **optional_kwargs)
    except oci.exceptions.ServiceError as exc:
        logger.warning("Get OpenSearch cluster failed: %s", exc)
        return _service_error_payload(exc)
    return _serialize(response.data)


@mcp.tool(
    description=(
        "List available OpenSearch cluster node shapes. "
        "Call this before setting `*_host_shape` values for create or vertical resize."
    )
)
def list_opensearch_cluster_shapes(
    compartment_id: str = Field(..., description="The OCID of the compartment in which to list shapes."),
) -> dict[str, Any]:
    client = get_opensearch_cluster_client()
    try:
        response = client.list_opensearch_cluster_shapes(compartment_id)
    except oci.exceptions.ServiceError as exc:
        logger.warning("List OpenSearch cluster shapes failed: %s", exc)
        return _service_error_payload(exc)
    serialized_data = _serialize(response.data)
    return serialized_data if isinstance(serialized_data, dict) else {"data": serialized_data}


@mcp.tool(
    description=(
        "Create an OpenSearch cluster. "
        "Pass `create_opensearch_cluster_details` as a JSON object using OCI SDK snake_case fields. "
        "Call `list_opensearch_cluster_shapes` before setting `*_host_shape` fields."
    )
)
def create_opensearch_cluster(
    create_opensearch_cluster_details: Optional[CreateOpensearchClusterDetailsInput] = Field(
        None,
        description=(
            "Preferred JSON request body matching CreateOpensearchClusterDetails using snake_case keys. "
            f"Minimal example: {CREATE_CLUSTER_MINIMAL_EXAMPLE}"
        ),
    ),
    opc_retry_token: Optional[str] = Field(None, description="Optional retry token."),
    opc_request_id: Optional[str] = Field(None, description="Optional request ID for tracing."),
) -> dict[str, Any]:
    if create_opensearch_cluster_details is None:
        raise ValueError(
            "Missing required request body: provide `create_opensearch_cluster_details`. "
            f"Minimal payload: {CREATE_CLUSTER_MINIMAL_EXAMPLE}"
        )

    create_payload = _build_create_opensearch_cluster_payload(create_opensearch_cluster_details)
    effective_retry_token, retry_token_source = _effective_retry_token(
        opc_retry_token,
        "mcp-create-",
        {"operation": "create_opensearch_cluster", "payload": create_payload},
    )
    optional_kwargs = _optional_kwargs(opc_retry_token=effective_retry_token, opc_request_id=opc_request_id)
    sdk_payload = build_create_opensearch_cluster_details(create_payload)
    client = get_opensearch_cluster_client()

    return _async_operation_response(
        "Create OpenSearch cluster",
        lambda: client.create_opensearch_cluster(sdk_payload, **optional_kwargs),
        opc_retry_token=effective_retry_token,
        opc_retry_token_source=retry_token_source,
    )


@mcp.tool(description="Update an OpenSearch cluster. Request body uses OCI SDK snake_case field names.")
def update_opensearch_cluster(
    opensearch_cluster_id: str = Field(..., description="The OCID of the OpenSearch cluster."),
    update_details: UpdateOpensearchClusterDetailsInput = Field(
        ...,
        description="Request body matching UpdateOpensearchClusterDetails using snake_case keys.",
    ),
    if_match: Optional[str] = Field(None, description="Optional ETag for optimistic concurrency."),
    opc_request_id: Optional[str] = Field(None, description="Optional request ID for tracing."),
) -> dict[str, Any]:
    serialized_update_details = update_details.model_dump(exclude_none=True)
    if not serialized_update_details:
        raise ValueError("Provide at least one update_details field.")
    _validate_update_opensearch_cluster_details(serialized_update_details)
    _validate_certificate_config(serialized_update_details.get("certificate_config"))

    client = get_opensearch_cluster_client()
    sdk_update_details = build_update_opensearch_cluster_details(serialized_update_details)
    optional_kwargs = _optional_kwargs(if_match=if_match, opc_request_id=opc_request_id)
    return _async_operation_response(
        "Update OpenSearch cluster",
        lambda: client.update_opensearch_cluster(
            opensearch_cluster_id, sdk_update_details, **optional_kwargs
        ),
    )


@mcp.tool(description="Delete an OpenSearch cluster.")
def delete_opensearch_cluster(
    opensearch_cluster_id: str = Field(..., description="The OCID of the OpenSearch cluster."),
    if_match: Optional[str] = Field(None, description="Optional ETag for optimistic concurrency."),
    opc_request_id: Optional[str] = Field(None, description="Optional request ID for tracing."),
) -> dict[str, Any]:
    client = get_opensearch_cluster_client()
    optional_kwargs = _optional_kwargs(if_match=if_match, opc_request_id=opc_request_id)
    return _async_operation_response(
        "Delete OpenSearch cluster",
        lambda: client.delete_opensearch_cluster(opensearch_cluster_id, **optional_kwargs),
    )


@mcp.tool(
    description=(
        "Resize an OpenSearch cluster vertically. "
        "Call `list_opensearch_cluster_shapes` before setting `*_host_shape` fields."
    )
)
def resize_opensearch_cluster_vertical(
    opensearch_cluster_id: str = Field(..., description="The OCID of the OpenSearch cluster."),
    resize_details: ResizeOpensearchClusterVerticalDetailsInput = Field(
        ...,
        description="Request body matching ResizeOpensearchClusterVerticalDetails using snake_case keys.",
    ),
    if_match: Optional[str] = Field(None, description="Optional ETag for optimistic concurrency."),
    opc_retry_token: Optional[str] = Field(None, description="Optional retry token."),
    opc_request_id: Optional[str] = Field(None, description="Optional request ID for tracing."),
) -> dict[str, Any]:
    serialized_resize_details = resize_details.model_dump(exclude_none=True)
    if not serialized_resize_details:
        raise ValueError("Provide at least one resize_details field for vertical resize.")

    effective_retry_token, retry_token_source = _effective_retry_token(
        opc_retry_token,
        "mcp-rzv-",
        {
            "operation": "resize_opensearch_cluster_vertical",
            "opensearch_cluster_id": opensearch_cluster_id,
            "payload": serialized_resize_details,
        },
    )
    client = get_opensearch_cluster_client()
    sdk_resize_details = build_resize_opensearch_cluster_vertical_details(serialized_resize_details)
    optional_kwargs = _optional_kwargs(
        if_match=if_match,
        opc_retry_token=effective_retry_token,
        opc_request_id=opc_request_id,
    )
    return _async_operation_response(
        "Vertical resize OpenSearch cluster",
        lambda: client.resize_opensearch_cluster_vertical(
            opensearch_cluster_id, sdk_resize_details, **optional_kwargs
        ),
        opc_retry_token=effective_retry_token,
        opc_retry_token_source=retry_token_source,
    )


@mcp.tool(description="Resize an OpenSearch cluster horizontally.")
def resize_opensearch_cluster_horizontal(
    opensearch_cluster_id: str = Field(..., description="The OCID of the OpenSearch cluster."),
    resize_details: ResizeOpensearchClusterHorizontalDetailsInput = Field(
        ...,
        description="Request body matching ResizeOpensearchClusterHorizontalDetails using snake_case keys.",
    ),
    if_match: Optional[str] = Field(None, description="Optional ETag for optimistic concurrency."),
    opc_retry_token: Optional[str] = Field(None, description="Optional retry token."),
    opc_request_id: Optional[str] = Field(None, description="Optional request ID for tracing."),
) -> dict[str, Any]:
    serialized_resize_details = resize_details.model_dump(exclude_none=True)
    if not serialized_resize_details:
        raise ValueError("Provide at least one resize_details field for horizontal resize.")

    effective_retry_token, retry_token_source = _effective_retry_token(
        opc_retry_token,
        "mcp-rzh-",
        {
            "operation": "resize_opensearch_cluster_horizontal",
            "opensearch_cluster_id": opensearch_cluster_id,
            "payload": serialized_resize_details,
        },
    )
    client = get_opensearch_cluster_client()
    sdk_resize_details = build_resize_opensearch_cluster_horizontal_details(serialized_resize_details)
    optional_kwargs = _optional_kwargs(
        if_match=if_match,
        opc_retry_token=effective_retry_token,
        opc_request_id=opc_request_id,
    )
    return _async_operation_response(
        "Horizontal resize OpenSearch cluster",
        lambda: client.resize_opensearch_cluster_horizontal(
            opensearch_cluster_id, sdk_resize_details, **optional_kwargs
        ),
        opc_retry_token=effective_retry_token,
        opc_retry_token_source=retry_token_source,
    )


@mcp.tool(description="Create a backup for an OpenSearch cluster.")
def backup_opensearch_cluster(
    opensearch_cluster_id: str = Field(..., description="The OCID of the OpenSearch cluster."),
    backup_details: BackupOpensearchClusterDetailsInput = Field(
        ...,
        description=(
            "Request body matching BackupOpensearchClusterDetails using snake_case keys. "
            f"Minimal example: {BACKUP_CLUSTER_MINIMAL_EXAMPLE}"
        ),
    ),
    if_match: Optional[str] = Field(None, description="Optional ETag for optimistic concurrency."),
    opc_retry_token: Optional[str] = Field(None, description="Optional retry token."),
    opc_request_id: Optional[str] = Field(None, description="Optional request ID for tracing."),
) -> dict[str, Any]:
    serialized_backup_details = backup_details.model_dump(exclude_none=True)
    missing_fields = [
        field for field in ("compartment_id", "display_name") if field not in serialized_backup_details
    ]
    if missing_fields:
        raise ValueError(
            "Missing required backup_details field(s): "
            + ", ".join(missing_fields)
            + ". "
            + f"Minimal payload: {BACKUP_CLUSTER_MINIMAL_EXAMPLE}"
        )

    effective_retry_token, retry_token_source = _effective_retry_token(
        opc_retry_token,
        "mcp-backup-",
        {
            "operation": "backup_opensearch_cluster",
            "opensearch_cluster_id": opensearch_cluster_id,
            "payload": serialized_backup_details,
        },
    )
    client = get_opensearch_cluster_client()
    sdk_backup_details = build_backup_opensearch_cluster_details(serialized_backup_details)
    optional_kwargs = _optional_kwargs(
        if_match=if_match,
        opc_retry_token=effective_retry_token,
        opc_request_id=opc_request_id,
    )
    return _async_operation_response(
        "Backup OpenSearch cluster",
        lambda: client.backup_opensearch_cluster(
            opensearch_cluster_id, sdk_backup_details, **optional_kwargs
        ),
        opc_retry_token=effective_retry_token,
        opc_retry_token_source=retry_token_source,
    )


@mcp.tool(description="List OpenSearch work requests in a compartment.")
def list_work_requests(
    compartment_id: str = Field(..., description="The OCID of the compartment."),
    work_request_id: Optional[str] = Field(None, description="Optional work request OCID filter."),
    source_resource_id: Optional[str] = Field(None, description="Optional source resource OCID filter."),
    limit: Optional[int] = Field(None, description="Maximum number of items to return."),
    opc_request_id: Optional[str] = Field(None, description="Optional request ID for tracing."),
) -> dict[str, Any]:
    client = get_opensearch_cluster_client()
    optional_kwargs = _optional_kwargs(
        work_request_id=work_request_id,
        source_resource_id=source_resource_id,
        opc_request_id=opc_request_id,
    )
    try:
        items = _paginated_list(
            client.list_work_requests,
            compartment_id,
            limit=limit if _is_explicit_value(limit) else None,
            **optional_kwargs,
        )
    except oci.exceptions.ServiceError as exc:
        logger.warning("List OpenSearch work requests failed: %s", exc)
        return _service_error_payload(exc)

    return {"items": items, "count": len(items)}


@mcp.tool(description="Get an OpenSearch work request by OCID.")
def get_work_request(
    work_request_id: str = Field(..., description="The OCID of the work request."),
    opc_request_id: Optional[str] = Field(None, description="Optional request ID for tracing."),
) -> dict[str, Any]:
    client = get_opensearch_cluster_client()
    optional_kwargs = _optional_kwargs(opc_request_id=opc_request_id)
    try:
        response = client.get_work_request(work_request_id, **optional_kwargs)
    except oci.exceptions.ServiceError as exc:
        logger.warning("Get OpenSearch work request failed: %s", exc)
        return _service_error_payload(exc)
    return _serialize(response.data)


def main() -> None:
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host or port:
        raise RuntimeError(
            "oracle.oci-opensearch-mcp-server supports stdio transport only. "
            "Unset ORACLE_MCP_HOST and ORACLE_MCP_PORT, then run the server again."
        )

    mcp.run()


if __name__ == "__main__":
    main()
