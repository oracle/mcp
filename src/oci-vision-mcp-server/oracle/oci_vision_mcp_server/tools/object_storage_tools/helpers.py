"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from typing import Any

from ...config.settings import (
    ENV_OBJECT_STORAGE_BUCKET,
    ENV_OBJECT_STORAGE_NAMESPACE,
    ResolvedMcpConfig,
)
from ...config.schemas import (
    ObjectStorageDestinationInput,
    ObjectStorageFetchEnvelope,
    ObjectStorageListEnvelope,
    ObjectStorageObjectSummary,
    ObjectStorageUploadEnvelope,
    OciObjectInput,
    ResponseDetail,
)
from ...io.result_store import raw_payload_reference
from ...responses.errors import redact_diagnostic_fields


def object_storage_structured_content(
    envelope: ObjectStorageUploadEnvelope | ObjectStorageListEnvelope | ObjectStorageFetchEnvelope,
) -> dict[str, Any]:
    data = envelope.model_dump(mode="json")
    # Normal responses expose only the MCP request id; raw mode includes OCI ids.
    if envelope.detail != ResponseDetail.RAW:
        data = redact_diagnostic_fields(data)
    return data


def attach_raw_payload(
    envelope: ObjectStorageUploadEnvelope | ObjectStorageListEnvelope | ObjectStorageFetchEnvelope,
    *,
    raw_result: dict[str, Any],
    stored_metadata: dict[str, object],
    max_inline_response_bytes: int,
) -> None:
    """Attach a truthful inline/path reference for an Object Storage raw response."""
    stored_path = stored_metadata.get("raw_result_path")
    reference = raw_payload_reference(
        raw_result=raw_result,
        raw_path=stored_path if isinstance(stored_path, str) else None,
        max_inline_response_bytes=max_inline_response_bytes,
    )
    envelope.raw_result_available = bool(reference["raw_result_available"])
    envelope.raw_result_inline = reference["raw_result_inline"]
    envelope.raw_result_path = reference["raw_result_path"]


def response_headers(response: Any) -> dict[str, str]:
    headers = getattr(response, "headers", None)
    if not headers:
        return {}
    return {str(key): str(value) for key, value in headers.items() if value is not None}


def resolve_object_storage_namespace_bucket(
    *,
    namespace: str | None,
    bucket: str | None,
    resolved_config: ResolvedMcpConfig,
    namespace_argument: str,
    bucket_argument: str,
) -> tuple[str, str]:
    selected_namespace = namespace or resolved_config.object_storage_namespace
    selected_bucket = bucket or resolved_config.object_storage_bucket

    if not selected_namespace:
        raise ValueError(
            f"Object Storage namespace is required. Provide {namespace_argument} or set "
            f"{ENV_OBJECT_STORAGE_NAMESPACE} in your MCP client environment."
        )
    if not selected_bucket:
        raise ValueError(
            f"Object Storage bucket is required. Provide {bucket_argument} or set "
            f"{ENV_OBJECT_STORAGE_BUCKET} in your MCP client environment."
        )
    return selected_namespace, selected_bucket


def resolve_upload_destination(
    *,
    destination: ObjectStorageDestinationInput | None,
    resolved_config: ResolvedMcpConfig,
    file_name: str,
) -> OciObjectInput:
    namespace, bucket = resolve_object_storage_namespace_bucket(
        namespace=destination.namespace if destination else None,
        bucket=destination.bucket if destination else None,
        resolved_config=resolved_config,
        namespace_argument="destination.namespace",
        bucket_argument="destination.bucket",
    )
    object_name = (
        destination.object_name
        if destination and destination.object_name
        else file_name
    )
    return OciObjectInput(namespace=namespace, bucket=bucket, object_name=object_name)


def object_summary(item: Any) -> ObjectStorageObjectSummary:
    return ObjectStorageObjectSummary(
        name=str(getattr(item, "name", "")),
        size=getattr(item, "size", None),
        time_created=stringify_datetime(getattr(item, "time_created", None)),
        time_modified=stringify_datetime(getattr(item, "time_modified", None)),
        etag=getattr(item, "etag", None),
        md5=getattr(item, "md5", None),
        storage_tier=getattr(item, "storage_tier", None),
        archival_state=getattr(item, "archival_state", None),
    )


def stringify_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)
