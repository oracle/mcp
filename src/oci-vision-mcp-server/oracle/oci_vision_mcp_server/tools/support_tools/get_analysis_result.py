"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from mcp.types import CallToolResult, TextContent

from ...config.consts import TOOL_GET_ANALYSIS_RESULT
from ...config.settings import get_resolved_config
from ...responses.errors import log_tool_failure, redact_diagnostic_fields
from ...io.result_store import ResultStoreError, load_analysis_result
from ...oci_mapper.vision_results import (
    normalize_exception,
    normalize_image_analysis_response,
    normalize_operation_response,
    render_response_dict,
    summary_text,
)
from ...config.schemas import ErrorDetail, ResponseDetail, ToolResultEnvelope
from ...runtime.mcp_app import mcp


@mcp.tool(name=TOOL_GET_ANALYSIS_RESULT)
def get_analysis_result(
    request_id: str,
    detail: ResponseDetail = ResponseDetail.SUMMARY,
    max_items: int = 10,
    include_debug_metadata: bool = False,
) -> CallToolResult:
    """Re-render a previously stored successful tool result by MCP request_id.

    Call this when the user gives a request_id from an earlier tool response or
    asks to show old results without calling OCI again. Use the MCP
    request_id returned by the tool, not options.request_id or an OCI request id.
    detail can change how stored Vision results are rendered: summary, standard,
    boxes, or raw. For stored Object Storage upload/list results, non-raw output
    hides OCI request ids; raw includes raw/metadata paths and OCI request
    ids. Results expire after OCI_VISION_RESULT_TTL_SECONDS.
    """
    try:
        resolved_config = get_resolved_config(persist_generated_profile=True)
        raw_result, metadata = load_analysis_result(
            result_store_dir=resolved_config.result_store_dir,
            request_id=request_id,
            ttl_seconds=resolved_config.result_ttl_seconds,
        )
        if metadata.get("result_kind") == "object_storage":
            structured = _stored_object_storage_result(
                raw_result=raw_result,
                metadata=metadata,
                request_id=request_id,
                detail=detail,
            )
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Loaded stored result for {structured.get('tool')} with request_id {request_id}.",
                    )
                ],
                structuredContent=structured,
                isError=structured.get("status") == "failed",
            )
        envelope = _render_stored_vision_result(
            raw_result=raw_result,
            metadata=metadata,
            request_id=request_id,
            detail=detail,
            max_items=max_items,
            include_debug_metadata=include_debug_metadata,
            max_inline_response_bytes=resolved_config.max_inline_response_bytes,
        )
    except ResultStoreError as exc:
        envelope = normalize_exception(
            tool=TOOL_GET_ANALYSIS_RESULT,
            feature_type="",
            exc=exc,
        )
    except Exception as exc:
        log_tool_failure(TOOL_GET_ANALYSIS_RESULT, exc)
        envelope = normalize_exception(tool=TOOL_GET_ANALYSIS_RESULT, feature_type="", exc=exc)

    return CallToolResult(
        content=[TextContent(type="text", text=summary_text(envelope))],
        structuredContent=envelope.model_dump(mode="json"),
        isError=envelope.status == "failed",
    )


def _stored_object_storage_result(
    *,
    raw_result: dict[str, Any],
    metadata: dict[str, Any],
    request_id: str,
    detail: ResponseDetail,
) -> dict[str, Any]:
    operation_status = str(metadata.get("operation_status") or "succeeded")
    status = "failed" if operation_status == "failed" else "succeeded"
    public_results = _stored_object_storage_public_results(raw_result)
    succeeded_count = raw_result.get("succeeded_count")
    failed_count = raw_result.get("failed_count")
    if isinstance(succeeded_count, int) and isinstance(failed_count, int):
        public_results.setdefault(
            "partial_failure",
            succeeded_count > 0 and failed_count > 0,
        )
    structured: dict[str, Any] = {
        "status": status,
        "tool": metadata.get("tool"),
        "provider": "oci_object_storage",
        "request_id": request_id,
        "mcp_request_id": request_id,
        "detail": detail.value,
        "created_at": metadata.get("created_at"),
        "results": public_results,
    }
    stored_warnings = raw_result.get("warnings")
    if isinstance(stored_warnings, list):
        structured["warnings"] = [
            warning for warning in stored_warnings if isinstance(warning, dict)
        ]
    if status == "failed":
        structured["errors"] = _stored_object_storage_errors(raw_result)
    if detail == ResponseDetail.RAW:
        structured.update(
            {
                "raw_result": raw_result,
                "raw_result_path": metadata.get("raw_result_path"),
                "metadata_path": metadata.get("metadata_path"),
                "oci_request_id": metadata.get("oci_request_id"),
                "oci_request_ids": metadata.get("oci_request_ids") or [],
            }
        )
    return structured


def _stored_object_storage_public_results(raw_result: dict[str, Any]) -> dict[str, Any]:
    public_results = redact_diagnostic_fields(raw_result)
    public_results.pop("warnings", None)
    return public_results


def _render_stored_vision_result(
    *,
    raw_result: dict[str, Any],
    metadata: dict[str, Any],
    request_id: str,
    detail: ResponseDetail,
    max_items: int,
    include_debug_metadata: bool,
    max_inline_response_bytes: int,
) -> ToolResultEnvelope:
    tool = str(metadata.get("tool") or TOOL_GET_ANALYSIS_RESULT)
    feature_type = str(metadata.get("feature_type") or "")
    result_kind = str(metadata.get("result_kind") or "vision_single")
    raw_result_path = str(metadata.get("raw_result_path") or "")
    options = metadata.get("detail_options")
    if not isinstance(options, dict):
        options = {}
    saved_min_confidence = options.get("min_confidence")
    min_confidence = (
        float(saved_min_confidence)
        if isinstance(saved_min_confidence, (int, float))
        and not isinstance(saved_min_confidence, bool)
        else None
    )
    saved_include_full_text = options.get("include_full_text", True)
    include_full_text = (
        saved_include_full_text
        if isinstance(saved_include_full_text, bool)
        else True
    )

    if result_kind == "vision_parallel":
        # Imported lazily to avoid coupling tool registration at module import time.
        from ..vision_api_tools.parallel_analyze_image import render_stored_parallel_result

        return render_stored_parallel_result(
            raw_result=raw_result,
            tool=tool,
            request_id=request_id,
            detail=detail,
            max_items=max_items,
            include_debug_metadata=include_debug_metadata,
            raw_result_path=raw_result_path,
            max_inline_response_bytes=max_inline_response_bytes,
        )

    response = SimpleNamespace(
        data=raw_result,
        opc_request_id=metadata.get("oci_request_id"),
    )
    if result_kind == "vision_combined":
        saved_feature_types = metadata.get("feature_types")
        if not isinstance(saved_feature_types, list):
            saved_feature_types = feature_type.split(",")
        feature_types = [
            value
            for value in saved_feature_types
            if isinstance(value, str) and value
        ]
        return normalize_image_analysis_response(
            response,
            tool=tool,
            feature_types=feature_types,
            request_id=request_id,
            detail=detail,
            max_items=max_items,
            include_debug_metadata=include_debug_metadata,
            min_confidence=min_confidence,
            include_full_text=include_full_text,
            raw_result_path=raw_result_path,
            max_inline_response_bytes=max_inline_response_bytes,
        )
    if result_kind == "vision_image_job":
        return _render_stored_image_job(
            raw_result=raw_result,
            metadata=metadata,
            tool=tool,
            feature_type=feature_type or "image_job",
            request_id=request_id,
            detail=detail,
            max_items=max_items,
            include_debug_metadata=include_debug_metadata,
            raw_result_path=raw_result_path,
            max_inline_response_bytes=max_inline_response_bytes,
        )
    return render_response_dict(
        raw_result,
        tool=tool,
        feature_type=feature_type,
        request_id=request_id,
        detail=detail,
        max_items=max_items,
        include_debug_metadata=include_debug_metadata,
        min_confidence=min_confidence,
        include_full_text=include_full_text,
        raw_result_path=raw_result_path,
        max_inline_response_bytes=max_inline_response_bytes,
        oci_request_id=metadata.get("oci_request_id"),
    )


def _render_stored_image_job(
    *,
    raw_result: dict[str, Any],
    metadata: dict[str, Any],
    tool: str,
    feature_type: str,
    request_id: str,
    detail: ResponseDetail,
    max_items: int,
    include_debug_metadata: bool,
    raw_result_path: str,
    max_inline_response_bytes: int,
) -> ToolResultEnvelope:
    data = dict(raw_result)
    data.pop("_headers", None)
    message = (
        f"{tool} submitted an OCI Vision image job."
        if tool == "create_image_job"
        else f"{tool} completed."
    )
    summary = {
        "message": message,
        "id": data.get("id"),
        "lifecycle_state": data.get("lifecycle_state"),
        "status": data.get("status"),
    }
    envelope = normalize_operation_response(
        SimpleNamespace(
            data=raw_result if detail == ResponseDetail.RAW else data,
            opc_request_id=metadata.get("oci_request_id"),
        ),
        tool=tool,
        feature_type=feature_type,
        request_id=request_id,
        detail=detail,
        max_items=max_items,
        include_debug_metadata=include_debug_metadata,
        raw_result_path=raw_result_path,
        max_inline_response_bytes=max_inline_response_bytes,
        results={
            "summary": {key: value for key, value in summary.items() if value is not None},
            "data": redact_diagnostic_fields(data),
        },
    )
    if detail == ResponseDetail.RAW:
        oci_request_ids = metadata.get("oci_request_ids")
        if isinstance(oci_request_ids, list) and oci_request_ids:
            envelope.debug_metadata["oci_request_ids"] = oci_request_ids
    if metadata.get("operation_status") == "failed":
        envelope.status = "failed"
        if not envelope.errors:
            envelope.errors = [
                ErrorDetail(
                    code="STORED_OPERATION_FAILED",
                    message=f"The stored {tool} operation failed.",
                    retryable=False,
                )
            ]
    return envelope


def _stored_object_storage_errors(raw_result: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for item in raw_result.get("items") or []:
        if not isinstance(item, dict):
            continue
        for error in item.get("errors") or []:
            if isinstance(error, dict):
                errors.append(error)
    if errors:
        return errors
    for error in raw_result.get("errors") or []:
        if isinstance(error, dict):
            errors.append(error)
    return errors or [
        {
            "code": "STORED_OPERATION_FAILED",
            "message": "The stored Object Storage operation failed.",
            "retryable": False,
        }
    ]
