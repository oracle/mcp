"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import oci
from mcp.types import CallToolResult, TextContent

from ...authentication.auth import ensure_session_auth
from ...config.consts import (
    MAX_OBJECT_STORAGE_LIST_SCAN_PAGES,
    TOOL_LIST_OBJECT_STORAGE_OBJECTS,
)
from ...config.settings import ResolvedMcpConfig, get_resolved_config
from ...responses.errors import (
    list_exception_envelope,
    list_service_error_envelope,
    list_summary_text,
    log_tool_failure,
    result_persistence_warning,
    response_request_id,
)
from ...io.result_store import ResultStoreError, generate_request_id, store_tool_result
from ...config.schemas import (
    DEFAULT_OBJECT_STORAGE_LIST_FIELDS,
    ObjectStorageListEnvelope,
    ObjectStorageListField,
    ObjectStorageListInput,
    ObjectStorageListOptions,
    ObjectStorageObjectSummary,
    ResponseDetail,
    WarningDetail,
)
from ...runtime.mcp_app import mcp
from ...authentication.session_signer import SessionAuthenticationError
from ...oci_clients.object_storage import call_list_objects, create_object_storage_client
from .helpers import (
    attach_raw_payload,
    object_storage_structured_content,
    object_summary,
    resolve_object_storage_namespace_bucket,
)


@mcp.tool(name=TOOL_LIST_OBJECT_STORAGE_OBJECTS)
def list_object_storage_objects(
    namespace: str | None = None,
    bucket: str | None = None,
    prefix: str | None = None,
    delimiter: str | None = None,
    fields: list[ObjectStorageListField] | None = None,
    options: ObjectStorageListOptions | None = None,
) -> CallToolResult:
    """List Object Storage objects in a bucket, optionally under a prefix.

    Call this when the user asks what images/files exist in an OCI Object
    Storage bucket, wants to inspect a folder-like prefix, or needs
    object names before creating batch/async Vision jobs. namespace and bucket
    may come from environment defaults; prefix is optional and omitted means
    list from the bucket root. Use delimiter="/" for folder-like grouping. The
    options.start_index/options.end_index range is zero-based and end-exclusive:
    0-10 returns the first 10 objects and 10-20 returns the next 10. The tool
    accepts end_index up to 10,000 and a range width up to 1,000 objects. It
    fetches only enough OCI pages to satisfy the requested range plus one object
    for has_more; it does not download object content. Numeric ranges can shift
    when bucket objects are added or removed between separate calls.
    """
    raw_args: dict[str, object] = {
        "namespace": namespace,
        "bucket": bucket,
        "prefix": prefix,
        "delimiter": delimiter,
        "options": options or {},
    }
    if fields is not None:
        raw_args["fields"] = fields
    return run_list_objects_tool(raw_args)


def run_list_objects_tool(raw_args: dict[str, object]) -> CallToolResult:
    args: ObjectStorageListInput | None = None
    resolved_config: ResolvedMcpConfig | None = None
    mcp_request_id: str | None = None
    try:
        args = ObjectStorageListInput.model_validate(raw_args)
        resolved_config = get_resolved_config(persist_generated_profile=True)
        mcp_request_id = generate_request_id()
        client_request_id = args.options.request_id
        oci_client_request_id = client_request_id or mcp_request_id
        namespace, bucket = resolve_object_storage_namespace_bucket(
            namespace=args.namespace,
            bucket=args.bucket,
            resolved_config=resolved_config,
            namespace_argument="namespace",
            bucket_argument="bucket",
        )
        prefix = args.prefix
        fields = args.fields or DEFAULT_OBJECT_STORAGE_LIST_FIELDS

        ensure_session_auth()
        client = create_object_storage_client(
            profile=resolved_config.profile,
            region=args.options.region or resolved_config.region,
        )
        objects: list[ObjectStorageObjectSummary] = []
        prefixes: list[str] = []
        seen_prefixes: set[str] = set()
        listing_warnings: list[WarningDetail] = []
        oci_request_ids: list[str] = []
        start: str | None = None
        scanned_object_count = 0
        has_more = False
        fields_csv = ",".join(str(field.value) for field in fields)

        # OCI pagination is lexical and does not expose numeric offsets. Scan
        # only through the requested exclusive end plus one object so callers
        # get a reliable has_more flag without materializing the whole bucket.
        target_object_count = args.options.end_index + 1
        max_scan_pages = MAX_OBJECT_STORAGE_LIST_SCAN_PAGES
        scanned_page_count = 0
        prefix_limit = args.options.end_index - args.options.start_index
        prefixes_truncated = False
        scan_complete = False
        while scanned_object_count < target_object_count:
            scanned_page_count += 1
            remaining_object_count = target_object_count - scanned_object_count
            request_limit = min(args.options.page_size, remaining_object_count)
            response = call_list_objects(
                client,
                namespace=namespace,
                bucket=bucket,
                prefix=prefix,
                delimiter=args.delimiter,
                fields=fields_csv,
                start=start,
                limit=request_limit,
                request_id=oci_client_request_id,
            )
            oci_request_id = response_request_id(response)
            if oci_request_id:
                oci_request_ids.append(oci_request_id)
            data = getattr(response, "data", None)
            for item in getattr(data, "objects", None) or []:
                object_index = scanned_object_count
                scanned_object_count += 1
                if object_index < args.options.start_index:
                    continue
                if object_index < args.options.end_index:
                    objects.append(object_summary(item))
                    continue
                has_more = True
                break
            for item in getattr(data, "prefixes", None) or []:
                prefix_value = str(item)
                if prefix_value in seen_prefixes:
                    continue
                seen_prefixes.add(prefix_value)
                if len(prefixes) < prefix_limit:
                    prefixes.append(prefix_value)
                else:
                    prefixes_truncated = True
            if has_more:
                scan_complete = True
                break
            next_start = getattr(data, "next_start_with", None)
            if not next_start or next_start == start:
                scan_complete = True
                break
            if scanned_page_count >= max_scan_pages:
                listing_warnings.append(
                    WarningDetail(
                        code="LIST_SCAN_LIMIT_REACHED",
                        message=(
                            "The bounded OCI page scan ended before the requested object "
                            "range was complete. Narrow prefix or increase page_size."
                        ),
                    )
                )
                break
            start = str(next_start)

        if prefixes_truncated:
            listing_warnings.append(
                WarningDetail(
                    code="PREFIX_RESULTS_TRUNCATED",
                    message=(
                        "Folder-like prefixes exceeded the requested range width and were "
                        "truncated. Narrow prefix to retrieve a smaller folder set."
                    ),
                )
            )

        actual_end_index = args.options.start_index + len(objects)
        reported_has_more = has_more if scan_complete else None
        next_start_index = actual_end_index if has_more and scan_complete else None

        raw_result = {
            "namespace": namespace,
            "bucket": bucket,
            "prefix": prefix,
            "delimiter": args.delimiter,
            "objects": [item.model_dump(mode="json") for item in objects],
            "prefixes": prefixes,
            "object_count": len(objects),
            "prefix_count": len(prefixes),
            "start_index": args.options.start_index,
            "end_index": actual_end_index,
            "has_more": reported_has_more,
            "next_start_index": next_start_index,
            "scan_complete": scan_complete,
            "prefixes_truncated": prefixes_truncated,
            "oci_request_ids": oci_request_ids,
            "warnings": [warning.model_dump(mode="json") for warning in listing_warnings],
        }
        stored_metadata: dict[str, object] = {}
        persistence_warnings = []
        try:
            stored_metadata = store_tool_result(
                result_store_dir=resolved_config.result_store_dir,
                mcp_request_id=mcp_request_id,
                client_request_id=client_request_id,
                tool=TOOL_LIST_OBJECT_STORAGE_OBJECTS,
                provider="oci_object_storage",
                raw_result=raw_result,
                oci_request_id=oci_request_ids[0] if oci_request_ids else None,
                oci_request_ids=oci_request_ids,
                region=args.options.region or resolved_config.region,
                image_info=None,
                object_storage_info={
                    "namespace": namespace,
                    "bucket": bucket,
                    "prefix": prefix,
                },
                operation_status="succeeded",
                ttl_seconds=resolved_config.result_ttl_seconds,
            )
        except ResultStoreError as exc:
            persistence_warnings.append(
                result_persistence_warning(TOOL_LIST_OBJECT_STORAGE_OBJECTS, exc)
            )

        envelope = ObjectStorageListEnvelope(
            status="succeeded",
            tool=TOOL_LIST_OBJECT_STORAGE_OBJECTS,
            request_id=mcp_request_id,
            mcp_request_id=mcp_request_id,
            detail=args.options.detail,
            oci_request_id=oci_request_ids[0] if oci_request_ids else None,
            namespace=namespace,
            bucket=bucket,
            prefix=prefix,
            delimiter=args.delimiter,
            objects=objects,
            prefixes=prefixes,
            object_count=len(objects),
            prefix_count=len(prefixes),
            start_index=args.options.start_index,
            end_index=actual_end_index,
            has_more=reported_has_more,
            next_start_index=next_start_index,
            scan_complete=scan_complete,
            prefixes_truncated=prefixes_truncated,
            oci_request_ids=oci_request_ids,
            warnings=[*listing_warnings, *persistence_warnings],
        )
        if args.options.detail == ResponseDetail.RAW:
            attach_raw_payload(
                envelope,
                raw_result=raw_result,
                stored_metadata=stored_metadata,
                max_inline_response_bytes=resolved_config.max_inline_response_bytes,
            )
    except (ValueError, SessionAuthenticationError) as exc:
        envelope = list_exception_envelope(exc, request_id=mcp_request_id)
    except oci.exceptions.ServiceError as exc:
        selected_region = None
        if args and args.options.region:
            selected_region = args.options.region
        elif resolved_config:
            selected_region = resolved_config.region
        envelope = list_service_error_envelope(
            exc,
            profile=resolved_config.profile if resolved_config else None,
            region=selected_region,
            request_id=mcp_request_id,
        )
    except Exception as exc:
        log_tool_failure(TOOL_LIST_OBJECT_STORAGE_OBJECTS, exc)
        envelope = list_exception_envelope(exc, request_id=mcp_request_id)

    return CallToolResult(
        content=[TextContent(type="text", text=list_summary_text(envelope))],
        structuredContent=object_storage_structured_content(envelope),
        isError=envelope.status == "failed",
    )
