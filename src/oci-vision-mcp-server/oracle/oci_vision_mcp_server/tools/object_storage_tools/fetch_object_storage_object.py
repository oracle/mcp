"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

MCP tool for fetching OCI Object Storage objects to local files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import oci
from mcp.types import CallToolResult, TextContent
from pydantic import Field

from ...authentication.auth import ensure_session_auth
from ...authentication.session_signer import SessionAuthenticationError
from ...config.consts import (
    DEFAULT_ALLOWED_EXTENSIONS,
    MAX_OBJECT_STORAGE_BULK_FETCH_OBJECTS,
    TOOL_FETCH_OBJECT_STORAGE_OBJECT,
)
from ...config.schemas import (
    ErrorDetail,
    ImageInput,
    ObjectStorageFetchEnvelope,
    ObjectStorageFetchInput,
    ObjectStorageFetchItem,
    ObjectStorageFetchOptions,
    OciObjectInput,
    ResponseDetail,
)
from ...config.settings import ResolvedMcpConfig, get_resolved_config
from ...io.object_storage import (
    ObjectStorageDownloadError,
    resolve_bulk_download_dir,
    resolve_bulk_download_path,
    resolve_download_path,
    write_object_response_to_file,
)
from ...io.result_store import ResultStoreError, generate_request_id, store_tool_result
from ...oci_clients.object_storage import call_get_object, create_object_storage_client
from ...responses.errors import (
    list_service_error_envelope,
    log_tool_failure,
    result_persistence_warning,
    response_header,
    response_request_id,
)
from ...runtime.mcp_app import mcp
from .helpers import (
    attach_raw_payload,
    object_storage_structured_content,
    resolve_object_storage_namespace_bucket,
    response_headers,
)


@mcp.tool(name=TOOL_FETCH_OBJECT_STORAGE_OBJECT)
def fetch_object_storage_object(
    object_name: str | None = None,
    object_names: (
        Annotated[
            list[str],
            Field(min_length=1, max_length=MAX_OBJECT_STORAGE_BULK_FETCH_OBJECTS),
        ]
        | None
    ) = None,
    namespace: str | None = None,
    bucket: str | None = None,
    destination_path: str | None = None,
    destination_dir: str | None = None,
    overwrite: bool = False,
    options: ObjectStorageFetchOptions | None = None,
) -> CallToolResult:
    """Download one or more Object Storage objects to local files.

    Use single mode with `object_name` when the user needs one local copy. Use
    bulk mode with `object_names` for up to 100 explicit objects after object
    discovery with list_object_storage_objects. Namespace and bucket may come
    from environment defaults. Bulk downloads preserve object folder-like paths
    under `destination_dir` or a request-specific folder under
    `OCI_OBJECT_STORAGE_DOWNLOAD_DIR`.
    """
    raw_args: dict[str, object] = {
        "namespace": namespace,
        "bucket": bucket,
        "object_name": object_name,
        "object_names": object_names,
        "destination_path": destination_path,
        "destination_dir": destination_dir,
        "overwrite": overwrite,
        "options": options or {},
    }
    return run_fetch_object_tool(raw_args)


def run_fetch_object_tool(raw_args: dict[str, object]) -> CallToolResult:
    args: ObjectStorageFetchInput | None = None
    resolved_config: ResolvedMcpConfig | None = None
    mcp_request_id: str | None = None
    try:
        args = ObjectStorageFetchInput.model_validate(raw_args)
        resolved_config = get_resolved_config(persist_generated_profile=True)
        mcp_request_id = generate_request_id()
        if args.object_names is not None:
            envelope = _run_bulk_fetch(args, resolved_config=resolved_config, mcp_request_id=mcp_request_id)
        else:
            envelope = _run_single_fetch(args, resolved_config=resolved_config, mcp_request_id=mcp_request_id)
    except (ValueError, ObjectStorageDownloadError, SessionAuthenticationError) as exc:
        envelope = _fetch_exception_envelope(exc, request_id=mcp_request_id)
    except oci.exceptions.ServiceError as exc:
        selected_region = None
        if args and args.options.region:
            selected_region = args.options.region
        elif resolved_config:
            selected_region = resolved_config.region
        envelope = _fetch_error_envelope(
            _fetch_service_error_detail(exc, resolved_config=resolved_config, region=selected_region),
            request_id=mcp_request_id,
        )
    except Exception as exc:
        log_tool_failure(TOOL_FETCH_OBJECT_STORAGE_OBJECT, exc)
        envelope = _fetch_exception_envelope(exc, request_id=mcp_request_id)

    return CallToolResult(
        content=[TextContent(type="text", text=_fetch_summary_text(envelope))],
        structuredContent=object_storage_structured_content(envelope),
        isError=envelope.status == "failed",
    )


def _run_single_fetch(
    args: ObjectStorageFetchInput,
    *,
    resolved_config: ResolvedMcpConfig,
    mcp_request_id: str,
) -> ObjectStorageFetchEnvelope:
    client_request_id = args.options.request_id
    oci_client_request_id = client_request_id or mcp_request_id
    namespace, bucket = resolve_object_storage_namespace_bucket(
        namespace=args.namespace,
        bucket=args.bucket,
        resolved_config=resolved_config,
        namespace_argument="namespace",
        bucket_argument="bucket",
    )
    object_name = args.object_name or ""
    destination = resolve_download_path(
        download_dir=resolved_config.object_storage_download_dir,
        object_name=object_name,
        request_id=mcp_request_id,
        destination_path=args.destination_path,
    )

    ensure_session_auth()
    client = create_object_storage_client(
        profile=resolved_config.profile,
        region=args.options.region or resolved_config.region,
    )
    response = call_get_object(
        client,
        namespace=namespace,
        bucket=bucket,
        object_name=object_name,
        request_id=oci_client_request_id,
    )
    item = _write_fetch_response(
        response=response,
        destination=destination,
        allowed_root=Path(resolved_config.object_storage_download_dir),
        object_ref=OciObjectInput(namespace=namespace, bucket=bucket, object_name=object_name),
        resolved_config=resolved_config,
        overwrite=args.overwrite,
    )
    raw_result = {
        "object": item.object.model_dump(mode="json") if item.object else None,
        "file_path": item.file_path,
        "size_bytes": item.size_bytes,
        "content_type": item.content_type,
        "etag": item.etag,
        "headers": response_headers(response),
    }
    stored_metadata: dict[str, object] = {}
    persistence_warnings = []
    try:
        stored_metadata = store_tool_result(
            result_store_dir=resolved_config.result_store_dir,
            mcp_request_id=mcp_request_id,
            client_request_id=client_request_id,
            tool=TOOL_FETCH_OBJECT_STORAGE_OBJECT,
            provider="oci_object_storage",
            raw_result=raw_result,
            oci_request_id=item.oci_request_id,
            oci_request_ids=[item.oci_request_id] if item.oci_request_id else [],
            region=args.options.region or resolved_config.region,
            object_storage_info={
                "namespace": namespace,
                "bucket": bucket,
                "object_name": object_name,
                "download_path": item.file_path,
            },
            operation_status="succeeded",
            ttl_seconds=resolved_config.result_ttl_seconds,
        )
    except ResultStoreError as exc:
        persistence_warnings.append(
            result_persistence_warning(TOOL_FETCH_OBJECT_STORAGE_OBJECT, exc)
        )
    envelope = ObjectStorageFetchEnvelope(
        status="succeeded",
        tool=TOOL_FETCH_OBJECT_STORAGE_OBJECT,
        request_id=mcp_request_id,
        mcp_request_id=mcp_request_id,
        detail=args.options.detail,
        oci_request_id=item.oci_request_id,
        oci_request_ids=[item.oci_request_id] if item.oci_request_id else [],
        object=item.object,
        file_path=item.file_path,
        image_input=item.image_input,
        size_bytes=item.size_bytes,
        content_type=item.content_type,
        etag=item.etag,
        warnings=persistence_warnings,
    )
    if args.options.detail == ResponseDetail.RAW:
        attach_raw_payload(
            envelope,
            raw_result=raw_result,
            stored_metadata=stored_metadata,
            max_inline_response_bytes=resolved_config.max_inline_response_bytes,
        )
    return envelope


def _run_bulk_fetch(
    args: ObjectStorageFetchInput,
    *,
    resolved_config: ResolvedMcpConfig,
    mcp_request_id: str,
) -> ObjectStorageFetchEnvelope:
    client_request_id = args.options.request_id
    oci_client_request_id = client_request_id or mcp_request_id
    namespace, bucket = resolve_object_storage_namespace_bucket(
        namespace=args.namespace,
        bucket=args.bucket,
        resolved_config=resolved_config,
        namespace_argument="namespace",
        bucket_argument="bucket",
    )
    bulk_dir = resolve_bulk_download_dir(
        download_dir=resolved_config.object_storage_download_dir,
        request_id=mcp_request_id,
        destination_dir=args.destination_dir,
    )

    ensure_session_auth()
    client = create_object_storage_client(
        profile=resolved_config.profile,
        region=args.options.region or resolved_config.region,
    )
    items: list[ObjectStorageFetchItem] = []
    raw_items: list[dict[str, object]] = []
    oci_request_ids: list[str] = []
    for object_name in args.object_names or []:
        object_ref = _object_ref(namespace=namespace, bucket=bucket, object_name=object_name)
        try:
            destination = resolve_bulk_download_path(bulk_dir=bulk_dir, object_name=object_name)
            response = call_get_object(
                client,
                namespace=namespace,
                bucket=bucket,
                object_name=object_name,
                request_id=oci_client_request_id,
            )
            item = _write_fetch_response(
                response=response,
                destination=destination,
                allowed_root=bulk_dir,
                object_ref=object_ref,
                resolved_config=resolved_config,
                overwrite=args.overwrite,
            )
            if item.oci_request_id:
                oci_request_ids.append(item.oci_request_id)
            raw_items.append({**item.model_dump(mode="json"), "headers": response_headers(response)})
        except oci.exceptions.ServiceError as exc:
            item = ObjectStorageFetchItem(
                status="failed",
                object=object_ref,
                errors=[_fetch_service_error_detail(exc, resolved_config=resolved_config, region=args.options.region or resolved_config.region)],
            )
            raw_items.append(item.model_dump(mode="json"))
        except (ObjectStorageDownloadError, ValueError) as exc:
            item = ObjectStorageFetchItem(status="failed", object=object_ref, errors=[_error_detail(exc)])
            raw_items.append(item.model_dump(mode="json"))
        except Exception as exc:
            log_tool_failure(TOOL_FETCH_OBJECT_STORAGE_OBJECT, exc)
            item = ObjectStorageFetchItem(status="failed", object=object_ref, errors=[_error_detail(exc)])
            raw_items.append(item.model_dump(mode="json"))
        items.append(item)

    succeeded_count = sum(1 for item in items if item.status == "succeeded")
    failed_count = len(items) - succeeded_count
    raw_result = {
        "namespace": namespace,
        "bucket": bucket,
        "download_dir": str(bulk_dir),
        "items": raw_items,
        "total_count": len(items),
        "succeeded_count": succeeded_count,
        "failed_count": failed_count,
        "oci_request_ids": oci_request_ids,
    }
    if succeeded_count and failed_count:
        operation_status = "partial_failure"
    elif succeeded_count:
        operation_status = "succeeded"
    else:
        operation_status = "failed"
    stored_metadata: dict[str, object] = {}
    persistence_warnings = []
    try:
        stored_metadata = store_tool_result(
            result_store_dir=resolved_config.result_store_dir,
            mcp_request_id=mcp_request_id,
            client_request_id=client_request_id,
            tool=TOOL_FETCH_OBJECT_STORAGE_OBJECT,
            provider="oci_object_storage",
            raw_result=raw_result,
            oci_request_id=oci_request_ids[0] if oci_request_ids else None,
            oci_request_ids=oci_request_ids,
            region=args.options.region or resolved_config.region,
            object_storage_info={
                "namespace": namespace,
                "bucket": bucket,
                "object_count": len(args.object_names or []),
                "download_dir": str(bulk_dir),
            },
            operation_status=operation_status,
            ttl_seconds=resolved_config.result_ttl_seconds,
        )
    except ResultStoreError as exc:
        persistence_warnings.append(
            result_persistence_warning(TOOL_FETCH_OBJECT_STORAGE_OBJECT, exc)
        )
    envelope = ObjectStorageFetchEnvelope(
        status="succeeded" if succeeded_count else "failed",
        tool=TOOL_FETCH_OBJECT_STORAGE_OBJECT,
        request_id=mcp_request_id,
        mcp_request_id=mcp_request_id,
        detail=args.options.detail,
        oci_request_id=oci_request_ids[0] if oci_request_ids else None,
        oci_request_ids=oci_request_ids,
        items=items,
        total_count=len(items),
        succeeded_count=succeeded_count,
        failed_count=failed_count,
        partial_failure=succeeded_count > 0 and failed_count > 0,
        warnings=persistence_warnings,
        errors=_bulk_errors(items) if not succeeded_count else [],
    )
    if args.options.detail == ResponseDetail.RAW:
        attach_raw_payload(
            envelope,
            raw_result=raw_result,
            stored_metadata=stored_metadata,
            max_inline_response_bytes=resolved_config.max_inline_response_bytes,
        )
    return envelope


def _write_fetch_response(
    *,
    response: object,
    destination: Path,
    allowed_root: Path,
    object_ref: OciObjectInput,
    resolved_config: ResolvedMcpConfig,
    overwrite: bool,
) -> ObjectStorageFetchItem:
    _validate_content_length(response, max_bytes=resolved_config.object_storage_fetch_max_bytes)
    size_bytes = write_object_response_to_file(
        response=response,
        destination=destination,
        max_bytes=resolved_config.object_storage_fetch_max_bytes,
        overwrite=overwrite,
        allowed_root=allowed_root,
    )
    content_type = response_header(response, "content-type")
    tool_file_path = _tool_file_path(destination, resolved_config.image_base_dir)
    oci_request_id = response_request_id(response)
    return ObjectStorageFetchItem(
        status="succeeded",
        object=object_ref,
        file_path=tool_file_path or str(destination),
        image_input=_image_input_for_path(tool_file_path, destination, content_type),
        size_bytes=size_bytes,
        content_type=content_type,
        etag=response_header(response, "etag"),
        oci_request_id=oci_request_id,
    )


def _validate_content_length(response: object, *, max_bytes: int) -> None:
    content_length = response_header(response, "content-length")
    if not content_length:
        return
    try:
        parsed = int(content_length)
    except ValueError:
        return
    if parsed > max_bytes:
        raise ObjectStorageDownloadError("Object exceeds OCI_OBJECT_STORAGE_FETCH_MAX_BYTES.")


def _tool_file_path(path: Path, image_base_dir: str) -> str | None:
    base = Path(image_base_dir).expanduser().resolve(strict=False)
    try:
        return str(path.resolve(strict=False).relative_to(base))
    except ValueError:
        return None


def _image_input_for_path(file_path: str | None, absolute_path: Path, content_type: str | None) -> ImageInput | None:
    if file_path and _is_image_file(absolute_path, content_type):
        return ImageInput(source_type="file_path", path=file_path)
    return None


def _is_image_file(path: Path, content_type: str | None) -> bool:
    return path.suffix.lower() in DEFAULT_ALLOWED_EXTENSIONS or bool(
        content_type and content_type.startswith("image/")
    )


def _fetch_exception_envelope(exc: Exception, *, request_id: str | None) -> ObjectStorageFetchEnvelope:
    return _fetch_error_envelope(_error_detail(exc), request_id=request_id)


def _fetch_error_envelope(error: ErrorDetail, *, request_id: str | None) -> ObjectStorageFetchEnvelope:
    return ObjectStorageFetchEnvelope(
        status="failed",
        tool=TOOL_FETCH_OBJECT_STORAGE_OBJECT,
        request_id=request_id,
        mcp_request_id=request_id,
        errors=[error],
    )


def _fetch_service_error_detail(
    exc: oci.exceptions.ServiceError,
    *,
    resolved_config: ResolvedMcpConfig | None,
    region: str | None,
) -> ErrorDetail:
    envelope = list_service_error_envelope(
        exc,
        profile=resolved_config.profile if resolved_config else None,
        region=region,
        request_id=None,
    )
    if envelope.errors:
        return envelope.errors[0]
    return _error_detail(exc)


def _error_detail(exc: Exception) -> ErrorDetail:
    return ErrorDetail(
        code=str(getattr(exc, "code", type(exc).__name__)),
        message=str(exc),
        retryable=bool(getattr(exc, "retryable", False)),
    )


def _bulk_errors(items: list[ObjectStorageFetchItem]) -> list[ErrorDetail]:
    errors: list[ErrorDetail] = []
    for item in items:
        errors.extend(item.errors)
    return errors


def _object_ref(*, namespace: str, bucket: str, object_name: str) -> OciObjectInput | None:
    if not object_name:
        return None
    return OciObjectInput(namespace=namespace, bucket=bucket, object_name=object_name)


def _fetch_summary_text(envelope: ObjectStorageFetchEnvelope) -> str:
    if envelope.items:
        if envelope.status == "failed":
            return f"{envelope.tool} failed: fetched 0/{envelope.total_count} objects."
        if envelope.partial_failure:
            return f"Fetched {envelope.succeeded_count}/{envelope.total_count} objects with {envelope.failed_count} failures."
        return f"Fetched {envelope.succeeded_count} objects."
    if envelope.status == "failed":
        first = envelope.errors[0].message if envelope.errors else "Unknown error"
        return f"{envelope.tool} failed: {first}"
    if envelope.file_path:
        return f"Fetched object to {envelope.file_path}."
    return f"{envelope.tool} succeeded."
