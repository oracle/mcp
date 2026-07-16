"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Annotated

import oci
from mcp.types import CallToolResult, TextContent
from pydantic import Field

from ...authentication.auth import ensure_session_auth
from ...authentication.session_signer import SessionAuthenticationError
from ...config.consts import (
    MAX_OBJECT_STORAGE_BULK_UPLOAD_IMAGES,
    TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE,
)
from ...config.settings import ResolvedMcpConfig, get_resolved_config
from ...responses.errors import (
    log_tool_failure,
    result_persistence_warning,
    response_header,
    response_request_id,
    upload_exception_envelope,
    upload_service_error_envelope,
    upload_summary_text,
)
from ...io.image_loader import ImageResolver, ImageResolverError, LocalImageFile
from ...io.result_store import ResultStoreError, generate_request_id, store_tool_result
from ...config.schemas import (
    ErrorDetail,
    ImageInput,
    ObjectStorageDestinationInput,
    ObjectStorageUploadEnvelope,
    ObjectStorageUploadInput,
    ObjectStorageUploadItem,
    ObjectStorageUploadOptions,
    OciObjectInput,
    ResponseDetail,
)
from ...runtime.mcp_app import mcp
from ...oci_clients.object_storage import call_put_object, create_object_storage_client
from ..vision_api_tools.runner import image_info
from .helpers import (
    attach_raw_payload,
    object_storage_structured_content,
    resolve_upload_destination,
    response_headers,
)


@mcp.tool(name=TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE)
def upload_image_to_object_storage(
    image: ImageInput | None = None,
    images: (
        Annotated[
            list[ImageInput],
            Field(min_length=1, max_length=MAX_OBJECT_STORAGE_BULK_UPLOAD_IMAGES),
        ]
        | None
    ) = None,
    destination: ObjectStorageDestinationInput | None = None,
    destination_prefix: str | None = None,
    overwrite: bool | None = None,
    content_type: str | None = None,
    metadata: dict[str, str] | None = None,
    options: ObjectStorageUploadOptions | None = None,
) -> CallToolResult:
    """Upload one or more file_path images to OCI Object Storage.

    Use single mode with `image` and optional destination.object_name. Use bulk
    mode with `images`, destination.namespace, destination.bucket, and optional
    destination_prefix; each uploaded object keeps the local file basename under
    that prefix. All images must use source_type=file_path and stay under
    MCP_IMAGE_BASE_DIR. Bulk mode accepts up to 100 images.
    """
    return run_upload_tool(
        {
            "image": image,
            "images": images,
            "destination": destination,
            "destination_prefix": destination_prefix,
            "overwrite": overwrite,
            "content_type": content_type,
            "metadata": metadata or {},
            "options": options or {},
        }
    )


def run_upload_tool(raw_args: dict[str, object]) -> CallToolResult:
    args: ObjectStorageUploadInput | None = None
    resolved_config: ResolvedMcpConfig | None = None
    mcp_request_id: str | None = None
    try:
        args = ObjectStorageUploadInput.model_validate(raw_args)
        resolved_config = get_resolved_config(persist_generated_profile=True)
        mcp_request_id = generate_request_id()
        if args.images is not None:
            envelope = _run_bulk_upload(args, resolved_config=resolved_config, mcp_request_id=mcp_request_id)
        else:
            envelope = _run_single_upload(args, resolved_config=resolved_config, mcp_request_id=mcp_request_id)
    except (ImageResolverError, ValueError, SessionAuthenticationError) as exc:
        envelope = upload_exception_envelope(exc, request_id=mcp_request_id)
    except oci.exceptions.ServiceError as exc:
        selected_region = None
        if args and args.options.region:
            selected_region = args.options.region
        elif resolved_config:
            selected_region = resolved_config.region
        envelope = upload_service_error_envelope(
            exc,
            profile=resolved_config.profile if resolved_config else None,
            region=selected_region,
            request_id=mcp_request_id,
        )
    except Exception as exc:
        log_tool_failure(TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE, exc)
        envelope = upload_exception_envelope(exc, request_id=mcp_request_id)

    return CallToolResult(
        content=[TextContent(type="text", text=upload_summary_text(envelope))],
        structuredContent=object_storage_structured_content(envelope),
        isError=envelope.status == "failed",
    )


def _run_single_upload(
    args: ObjectStorageUploadInput,
    *,
    resolved_config: ResolvedMcpConfig,
    mcp_request_id: str,
) -> ObjectStorageUploadEnvelope:
    client_request_id = args.options.request_id
    oci_client_request_id = client_request_id or mcp_request_id
    resolver = ImageResolver(
        base_dir=resolved_config.image_base_dir,
        max_image_bytes=resolved_config.max_image_bytes,
    )
    image = args.image
    if image is None:
        raise ValueError("image is required for single upload.")
    local_file = resolver.resolve_local_file(image)
    selected_content_type = _selected_content_type(args.content_type, local_file.content_type)
    destination = resolve_upload_destination(
        destination=args.destination,
        resolved_config=resolved_config,
        file_name=local_file.path.name,
    )
    overwrite = args.overwrite if args.overwrite is not None else resolved_config.object_storage_overwrite

    ensure_session_auth()
    client = create_object_storage_client(
        profile=resolved_config.profile,
        region=args.options.region or resolved_config.region,
    )
    with local_file.path.open("rb") as file_body:
        response = call_put_object(
            client,
            namespace=destination.namespace,
            bucket=destination.bucket,
            object_name=destination.object_name,
            body=file_body,
            content_length=local_file.size_bytes,
            content_type=selected_content_type,
            metadata=args.metadata,
            request_id=oci_client_request_id,
            overwrite=overwrite,
        )
    oci_request_id = response_request_id(response)
    oci_request_ids = [oci_request_id] if oci_request_id else []
    raw_result = {
        "object": destination.model_dump(mode="json"),
        "size_bytes": local_file.size_bytes,
        "content_type": selected_content_type,
        "etag": response_header(response, "etag"),
        "headers": response_headers(response),
    }
    stored_metadata: dict[str, object] = {}
    persistence_warnings = []
    try:
        stored_metadata = store_tool_result(
            result_store_dir=resolved_config.result_store_dir,
            mcp_request_id=mcp_request_id,
            client_request_id=client_request_id,
            tool=TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE,
            provider="oci_object_storage",
            raw_result=raw_result,
            oci_request_id=oci_request_id,
            oci_request_ids=oci_request_ids,
            region=args.options.region or resolved_config.region,
            image_info=image_info(image),
            object_storage_info={
                "namespace": destination.namespace,
                "bucket": destination.bucket,
                "object_name": destination.object_name,
            },
            operation_status="succeeded",
            ttl_seconds=resolved_config.result_ttl_seconds,
        )
    except ResultStoreError as exc:
        persistence_warnings.append(
            result_persistence_warning(TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE, exc)
        )

    envelope = ObjectStorageUploadEnvelope(
        status="succeeded",
        tool=TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE,
        request_id=mcp_request_id,
        mcp_request_id=mcp_request_id,
        detail=args.options.detail,
        oci_request_id=oci_request_id,
        oci_request_ids=oci_request_ids,
        object=destination,
        image_input=ImageInput(source_type="oci_object", oci_object=destination),
        size_bytes=local_file.size_bytes,
        content_type=selected_content_type,
        etag=response_header(response, "etag"),
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


def _run_bulk_upload(
    args: ObjectStorageUploadInput,
    *,
    resolved_config: ResolvedMcpConfig,
    mcp_request_id: str,
) -> ObjectStorageUploadEnvelope:
    destination = args.destination
    if destination is None or not destination.namespace or not destination.bucket:
        raise ValueError("Bulk upload requires destination.namespace and destination.bucket.")
    resolver = ImageResolver(
        base_dir=resolved_config.image_base_dir,
        max_image_bytes=resolved_config.max_image_bytes,
    )
    prepared: list[tuple[ImageInput, LocalImageFile, OciObjectInput, str | None]] = []
    items: list[ObjectStorageUploadItem] = []
    for image in args.images or []:
        try:
            local_file = resolver.resolve_local_file(image)
            object_name = _bulk_object_name(args.destination_prefix, local_file.path.name)
            object_ref = OciObjectInput(
                namespace=destination.namespace,
                bucket=destination.bucket,
                object_name=object_name,
            )
            prepared.append(
                (
                    image,
                    local_file,
                    object_ref,
                    _selected_content_type(args.content_type, local_file.content_type),
                )
            )
        except (ImageResolverError, ValueError) as exc:
            items.append(_failed_upload_item(image=image, error=_error_detail(exc)))
    _reject_duplicate_upload_targets([item[2].object_name for item in prepared])

    if prepared:
        ensure_session_auth()
        client = create_object_storage_client(
            profile=resolved_config.profile,
            region=args.options.region or resolved_config.region,
        )
        client_request_id = args.options.request_id
        oci_client_request_id = client_request_id or mcp_request_id
        overwrite = args.overwrite if args.overwrite is not None else resolved_config.object_storage_overwrite
        for image, local_file, object_ref, selected_content_type in prepared:
            try:
                with local_file.path.open("rb") as file_body:
                    response = call_put_object(
                        client,
                        namespace=object_ref.namespace,
                        bucket=object_ref.bucket,
                        object_name=object_ref.object_name,
                        body=file_body,
                        content_length=local_file.size_bytes,
                        content_type=selected_content_type,
                        metadata=args.metadata,
                        request_id=oci_client_request_id,
                        overwrite=overwrite,
                    )
                items.append(
                    ObjectStorageUploadItem(
                        status="succeeded",
                        object=object_ref,
                        image_input=ImageInput(source_type="oci_object", oci_object=object_ref),
                        source_path=image.path,
                        size_bytes=local_file.size_bytes,
                        content_type=selected_content_type,
                        etag=response_header(response, "etag"),
                        oci_request_id=response_request_id(response),
                    )
                )
            except oci.exceptions.ServiceError as exc:
                items.append(
                    ObjectStorageUploadItem(
                        status="failed",
                        object=object_ref,
                        source_path=image.path,
                        errors=[_upload_service_error_detail(exc, resolved_config=resolved_config, region=args.options.region or resolved_config.region)],
                    )
                )
            except Exception as exc:
                log_tool_failure(TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE, exc)
                items.append(
                    ObjectStorageUploadItem(
                        status="failed",
                        object=object_ref,
                        source_path=image.path,
                        errors=[_error_detail(exc)],
                    )
                )

    succeeded_count = sum(1 for item in items if item.status == "succeeded")
    failed_count = len(items) - succeeded_count
    oci_request_ids = [item.oci_request_id for item in items if item.oci_request_id]
    raw_result = {
        "namespace": destination.namespace,
        "bucket": destination.bucket,
        "destination_prefix": args.destination_prefix,
        "items": [item.model_dump(mode="json") for item in items],
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
            client_request_id=args.options.request_id,
            tool=TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE,
            provider="oci_object_storage",
            raw_result=raw_result,
            oci_request_id=oci_request_ids[0] if oci_request_ids else None,
            oci_request_ids=oci_request_ids,
            region=args.options.region or resolved_config.region,
            object_storage_info={
                "namespace": destination.namespace,
                "bucket": destination.bucket,
                "destination_prefix": args.destination_prefix,
                "object_count": len(args.images or []),
            },
            operation_status=operation_status,
            ttl_seconds=resolved_config.result_ttl_seconds,
        )
    except ResultStoreError as exc:
        persistence_warnings.append(
            result_persistence_warning(TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE, exc)
        )
    envelope = ObjectStorageUploadEnvelope(
        status="succeeded" if succeeded_count else "failed",
        tool=TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE,
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


def _bulk_object_name(destination_prefix: str | None, file_name: str) -> str:
    if not destination_prefix:
        return file_name
    prefix = PurePosixPath(destination_prefix)
    parts = [part for part in prefix.parts if part not in {"", "."}]
    if prefix.is_absolute() or ".." in parts:
        raise ValueError("destination_prefix must be a safe relative Object Storage prefix.")
    return "/".join([*parts, file_name])


def _selected_content_type(requested: str | None, detected: str) -> str:
    if requested is not None and requested.lower() != detected:
        raise ValueError(
            f"content_type {requested!r} does not match detected image type {detected!r}."
        )
    return detected


def _reject_duplicate_upload_targets(object_names: list[str]) -> None:
    duplicates = sorted({name for name in object_names if object_names.count(name) > 1})
    if duplicates:
        raise ValueError(f"Bulk upload target object names must be unique: {', '.join(duplicates)}")


def _failed_upload_item(*, image: ImageInput, error: ErrorDetail) -> ObjectStorageUploadItem:
    return ObjectStorageUploadItem(
        status="failed",
        source_path=image.path,
        errors=[error],
    )


def _upload_service_error_detail(
    exc: oci.exceptions.ServiceError,
    *,
    resolved_config: ResolvedMcpConfig,
    region: str | None,
) -> ErrorDetail:
    envelope = upload_service_error_envelope(
        exc,
        profile=resolved_config.profile,
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


def _bulk_errors(items: list[ObjectStorageUploadItem]) -> list[ErrorDetail]:
    errors: list[ErrorDetail] = []
    for item in items:
        errors.extend(item.errors)
    return errors
