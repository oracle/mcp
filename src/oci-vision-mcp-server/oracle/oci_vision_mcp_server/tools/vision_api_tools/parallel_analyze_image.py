"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

MCP tool for concurrent OCI Vision analyzeImage requests.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated, Any

import oci
from mcp.types import CallToolResult
from pydantic import Field

from ...authentication.auth import ensure_session_auth
from ...authentication.session_signer import SessionAuthenticationError
from ...config.consts import (
    FEATURE_TEXT_DETECTION,
    MAX_PARALLEL_ANALYZE_ITEMS,
    MAX_PARALLEL_ANALYZE_MAX_PARALLEL,
    TOOL_PARALLEL_ANALYZE_IMAGE,
)
from ...config.schemas import (
    ErrorDetail,
    ParallelAnalyzeImageInput,
    ParallelAnalyzeImageItem,
    ResponseDetail,
    ToolOptions,
    ToolResultEnvelope,
    WarningDetail,
)
from ...config.settings import ResolvedMcpConfig, get_resolved_config
from ...io.image_loader import ImageResolverError
from ...io.result_store import ResultStoreError, generate_request_id, store_tool_result
from ...oci_clients.vision import call_analyze_image_features, create_vision_client
from ...oci_mapper.vision_results import (
    normalize_exception,
    normalize_image_analysis_response,
)
from ...responses.errors import (
    log_tool_failure,
    result_persistence_warning,
    response_request_id,
)
from ...runtime.mcp_app import mcp
from .runner import (
    call_tool_result,
    feature_types_from_names,
    image_features_from_names,
    image_info as default_image_info,
    image_resolver_from_config,
    model_versions_from_raw,
    resolve_compartment_id,
    vision_service_error,
    with_url_text_warning,
)


@mcp.tool(name=TOOL_PARALLEL_ANALYZE_IMAGE)
def parallel_analyze_image(
    items: Annotated[
        list[ParallelAnalyzeImageItem],
        Field(min_length=1, max_length=MAX_PARALLEL_ANALYZE_ITEMS),
    ],
    compartment_id: str | None = None,
    max_parallel: Annotated[
        int,
        Field(ge=1, le=MAX_PARALLEL_ANALYZE_MAX_PARALLEL),
    ] = 4,
    options: ToolOptions | None = None,
) -> CallToolResult:
    """Run multiple OCI analyzeImage calls concurrently and return direct results.

    Use this when the user has many images and wants the analysis returned by
    the MCP tool, not written by an OCI async image job to Object Storage. Each
    item has its own `image`, `features`, and analyze-image options. Results are
    collected into one ordered response so concurrent calls do not interleave.
    Use `create_image_job` instead when source images are in Object Storage and
    the user wants OCI Vision to save job output back to Object Storage.
    """
    return run_parallel_analyze_image_tool(
        {
            "items": items,
            "compartment_id": compartment_id,
            "max_parallel": max_parallel,
            "options": options or {},
        },
        tool=TOOL_PARALLEL_ANALYZE_IMAGE,
    )


def run_parallel_analyze_image_tool(
    raw_args: dict[str, Any],
    *,
    tool: str = TOOL_PARALLEL_ANALYZE_IMAGE,
) -> CallToolResult:
    args: ParallelAnalyzeImageInput | None = None
    resolved_config: ResolvedMcpConfig | None = None
    mcp_request_id: str | None = None
    try:
        mcp_request_id = generate_request_id()
        args = ParallelAnalyzeImageInput.model_validate(raw_args)
        resolved_config = get_resolved_config(persist_generated_profile=True)
        detail, option_warnings = args.options.effective_detail(
            ResponseDetail(resolved_config.default_detail)
        )
        region = args.options.region or resolved_config.region
        ensure_session_auth()

        item_results = _run_items_concurrently(
            args=args,
            resolved_config=resolved_config,
            region=region,
            mcp_request_id=mcp_request_id,
        )
        raw_batch_result = _raw_batch_result(item_results)
        oci_request_ids = [
            str(item["oci_request_id"])
            for item in item_results
            if item.get("oci_request_id")
        ]
        metadata: dict[str, Any] = {}
        persistence_warnings: list[WarningDetail] = []
        try:
            metadata = store_tool_result(
                result_store_dir=resolved_config.result_store_dir,
                mcp_request_id=mcp_request_id,
                client_request_id=args.options.request_id,
                tool=tool,
                provider="oci_vision",
                raw_result=raw_batch_result,
                oci_request_id=oci_request_ids[0] if oci_request_ids else None,
                oci_request_ids=oci_request_ids,
                region=region,
                feature_type="parallel_analyze_image",
                compartment_id=args.compartment_id or resolved_config.default_compartment_id,
                detail_options={
                    "detail": detail.value,
                    "max_items": args.options.max_items,
                    "include_debug_metadata": args.options.include_debug_metadata,
                    "max_parallel": args.max_parallel,
                    "items": [
                        {
                            "index": item["index"],
                            "min_confidence": item.get("min_confidence"),
                            "include_full_text": bool(item.get("include_full_text", True)),
                        }
                        for item in item_results
                    ],
                },
                model_versions=_batch_model_versions(item_results),
                image_info=_batch_image_info(item_results),
                result_kind="vision_parallel",
                ttl_seconds=resolved_config.result_ttl_seconds,
            )
        except ResultStoreError as exc:
            persistence_warnings.append(result_persistence_warning(tool, exc))
        envelope = _normalize_batch_result(
            item_results=item_results,
            tool=tool,
            request_id=mcp_request_id,
            detail=detail,
            max_items=args.options.max_items,
            include_debug_metadata=args.options.include_debug_metadata,
            raw_result_path=str(metadata.get("raw_result_path") or ""),
            max_inline_response_bytes=resolved_config.max_inline_response_bytes,
            option_warnings=[*option_warnings, *persistence_warnings],
        )
    except (ImageResolverError, ValueError, SessionAuthenticationError, ResultStoreError) as exc:
        envelope = normalize_exception(
            tool=tool,
            feature_type="parallel_analyze_image",
            exc=exc,
            request_id=mcp_request_id,
        )
    except oci.exceptions.ServiceError as exc:
        envelope = vision_service_error(
            exc,
            tool=tool,
            feature_type="parallel_analyze_image",
            args=args,
            resolved_config=resolved_config,
            request_id=mcp_request_id,
        )
    except Exception as exc:
        log_tool_failure(tool, exc)
        envelope = normalize_exception(
            tool=tool,
            feature_type="parallel_analyze_image",
            exc=exc,
            request_id=mcp_request_id,
        )
    return call_tool_result(envelope)


def _run_items_concurrently(
    *,
    args: ParallelAnalyzeImageInput,
    resolved_config: ResolvedMcpConfig,
    region: str,
    mcp_request_id: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any] | None] = [None] * len(args.items)
    max_workers = min(args.max_parallel, len(args.items))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _analyze_one_item,
                index=index,
                item=item,
                args=args,
                resolved_config=resolved_config,
                region=region,
                mcp_request_id=mcp_request_id,
            ): index
            for index, item in enumerate(args.items)
        }
        for future in as_completed(futures):
            index = futures[future]
            results[index] = future.result()
    return [item for item in results if item is not None]


def _analyze_one_item(
    *,
    index: int,
    item: ParallelAnalyzeImageItem,
    args: ParallelAnalyzeImageInput,
    resolved_config: ResolvedMcpConfig,
    region: str,
    mcp_request_id: str,
) -> dict[str, Any]:
    feature_types = feature_types_from_names(item.features)
    oci_client_request_id = _child_request_id(
        args.options.request_id or mcp_request_id,
        index=index,
        total_count=len(args.items),
    )
    image_info: dict[str, Any] = {}
    try:
        compartment_id = resolve_compartment_id(item.compartment_id or args.compartment_id, resolved_config)
        resolver = image_resolver_from_config(resolved_config)
        image_details = resolver.resolve(item.image)
        image_info = resolver.image_info(item.image)
        features = image_features_from_names(
            item.features,
            max_results=item.max_results,
            should_return_landmarks=item.should_return_landmarks,
        )
        client = create_vision_client(profile=resolved_config.profile, region=region)
        response = call_analyze_image_features(
            client,
            features=features,
            image_details=image_details,
            compartment_id=compartment_id,
            request_id=oci_client_request_id,
        )
        raw_result = oci.util.to_dict(getattr(response, "data", response))
        return {
            "index": index,
            "status": "succeeded",
            "image_info": image_info,
            "image": item.image,
            "feature_types": feature_types,
            "compartment_id": compartment_id,
            "oci_client_request_id": oci_client_request_id,
            "oci_request_id": response_request_id(response),
            "response": response,
            "raw_result": raw_result,
            "min_confidence": item.min_confidence,
            "include_full_text": item.include_full_text,
            "warnings": with_url_text_warning(
                [],
                image=item.image,
                includes_text=FEATURE_TEXT_DETECTION in feature_types,
            ),
            "errors": [],
        }
    except oci.exceptions.ServiceError as exc:
        envelope = vision_service_error(
            exc,
            tool=TOOL_PARALLEL_ANALYZE_IMAGE,
            feature_type=",".join(feature_types),
            args=args,
            resolved_config=resolved_config,
            request_id=mcp_request_id,
        )
        return _failed_item(
            index=index,
            item=item,
            resolved_image_info=image_info,
            feature_types=feature_types,
            oci_client_request_id=oci_client_request_id,
            errors=envelope.errors,
        )
    except (ImageResolverError, ValueError, SessionAuthenticationError) as exc:
        envelope = normalize_exception(
            tool=TOOL_PARALLEL_ANALYZE_IMAGE,
            feature_type=",".join(feature_types),
            exc=exc,
            request_id=mcp_request_id,
        )
        return _failed_item(
            index=index,
            item=item,
            resolved_image_info=image_info,
            feature_types=feature_types,
            oci_client_request_id=oci_client_request_id,
            errors=envelope.errors,
        )
    except Exception as exc:
        log_tool_failure(TOOL_PARALLEL_ANALYZE_IMAGE, exc)
        envelope = normalize_exception(
            tool=TOOL_PARALLEL_ANALYZE_IMAGE,
            feature_type=",".join(feature_types),
            exc=exc,
            request_id=mcp_request_id,
        )
        return _failed_item(
            index=index,
            item=item,
            resolved_image_info=image_info,
            feature_types=feature_types,
            oci_client_request_id=oci_client_request_id,
            errors=envelope.errors,
        )


def _failed_item(
    *,
    index: int,
    item: ParallelAnalyzeImageItem,
    resolved_image_info: dict[str, Any],
    feature_types: list[str],
    oci_client_request_id: str,
    errors: list[ErrorDetail],
) -> dict[str, Any]:
    return {
        "index": index,
        "status": "failed",
        "image_info": resolved_image_info or default_image_info(item.image),
        "image": item.image,
        "feature_types": feature_types,
        "compartment_id": item.compartment_id,
        "oci_client_request_id": oci_client_request_id,
        "oci_request_id": None,
        "response": None,
        "raw_result": {"errors": [error.model_dump(mode="json") for error in errors]},
        "min_confidence": item.min_confidence,
        "include_full_text": item.include_full_text,
        "warnings": [],
        "errors": errors,
    }


def _normalize_batch_result(
    *,
    item_results: list[dict[str, Any]],
    tool: str,
    request_id: str,
    detail: ResponseDetail,
    max_items: int,
    include_debug_metadata: bool,
    raw_result_path: str,
    max_inline_response_bytes: int,
    option_warnings: list[WarningDetail],
) -> ToolResultEnvelope:
    visible_items = [
        _visible_item(
            item,
            tool=tool,
            request_id=request_id,
            detail=detail,
            max_items=max_items,
            include_debug_metadata=include_debug_metadata,
            raw_result_path=raw_result_path,
            max_inline_response_bytes=max_inline_response_bytes,
        )
        for item in item_results
    ]
    succeeded_count = sum(1 for item in visible_items if item["status"] == "succeeded")
    failed_count = len(visible_items) - succeeded_count
    status = "succeeded" if succeeded_count else "failed"
    message = _batch_message(
        total_count=len(visible_items),
        succeeded_count=succeeded_count,
        failed_count=failed_count,
    )
    top_level_errors = []
    if status == "failed":
        for item in visible_items:
            top_level_errors.extend(_errors_from_visible_item(item))
    return ToolResultEnvelope(
        status=status,
        tool=tool,
        feature_type="parallel_analyze_image",
        request_id=request_id,
        mcp_request_id=request_id,
        detail=detail,
        results={
            "summary": {
                "message": message,
                "total_count": len(visible_items),
                "succeeded_count": succeeded_count,
                "failed_count": failed_count,
                "partial_failure": succeeded_count > 0 and failed_count > 0,
            },
            "items": visible_items,
        },
        truncated=any(bool(item.get("truncated")) for item in visible_items),
        debug_metadata=_batch_debug_metadata(
            item_results=item_results,
            include_debug_metadata=include_debug_metadata,
            detail=detail,
        ),
        warnings=_batch_warnings(option_warnings, item_results),
        errors=top_level_errors[:max_items],
    )


def _visible_item(
    item: dict[str, Any],
    *,
    tool: str,
    request_id: str,
    detail: ResponseDetail,
    max_items: int,
    include_debug_metadata: bool,
    raw_result_path: str,
    max_inline_response_bytes: int,
) -> dict[str, Any]:
    base = {
        "index": item["index"],
        "status": item["status"],
        "feature_types": item["feature_types"],
        "image": item["image_info"],
    }
    if detail == ResponseDetail.RAW:
        base["oci_client_request_id"] = item["oci_client_request_id"]
        base["oci_request_id"] = item.get("oci_request_id")
    if item["status"] != "succeeded":
        return {
            **base,
            "errors": [error.model_dump(mode="json") for error in item["errors"]],
        }

    normalized = normalize_image_analysis_response(
        item["response"],
        tool=tool,
        feature_types=item["feature_types"],
        request_id=request_id,
        detail=detail,
        max_items=max_items,
        include_debug_metadata=include_debug_metadata,
        min_confidence=item.get("min_confidence"),
        include_full_text=bool(item.get("include_full_text", True)),
        raw_result_path=raw_result_path,
        max_inline_response_bytes=max_inline_response_bytes,
        warnings=item.get("warnings") or [],
    )
    return {
        **base,
        "results": normalized.results,
        "truncated": normalized.truncated,
        "warnings": [warning.model_dump(mode="json") for warning in normalized.warnings],
        "errors": [error.model_dump(mode="json") for error in normalized.errors],
    }


def _raw_batch_result(item_results: list[dict[str, Any]]) -> dict[str, Any]:
    succeeded_count = sum(1 for item in item_results if item["status"] == "succeeded")
    return {
        "total_count": len(item_results),
        "succeeded_count": succeeded_count,
        "failed_count": len(item_results) - succeeded_count,
        "items": [
            {
                "index": item["index"],
                "status": item["status"],
                "feature_types": item["feature_types"],
                "image": item["image_info"],
                "oci_client_request_id": item["oci_client_request_id"],
                "oci_request_id": item.get("oci_request_id"),
                "min_confidence": item.get("min_confidence"),
                "include_full_text": bool(item.get("include_full_text", True)),
                "warnings": [
                    warning.model_dump(mode="json")
                    if isinstance(warning, WarningDetail)
                    else warning
                    for warning in item.get("warnings") or []
                ],
                "result": item["raw_result"],
            }
            for item in item_results
        ],
    }


def render_stored_parallel_result(
    *,
    raw_result: dict[str, Any],
    tool: str,
    request_id: str,
    detail: ResponseDetail,
    max_items: int,
    include_debug_metadata: bool,
    raw_result_path: str,
    max_inline_response_bytes: int,
    option_warnings: list[WarningDetail] | None = None,
) -> ToolResultEnvelope:
    """Re-render a stored parallel result without issuing OCI requests."""

    item_results: list[dict[str, Any]] = []
    for fallback_index, stored_item in enumerate(raw_result.get("items") or []):
        if not isinstance(stored_item, dict):
            continue
        item_result = stored_item.get("result")
        if not isinstance(item_result, dict):
            item_result = {}
        status = "succeeded" if stored_item.get("status") == "succeeded" else "failed"
        item_results.append(
            {
                "index": stored_item.get("index", fallback_index),
                "status": status,
                "image_info": stored_item.get("image")
                if isinstance(stored_item.get("image"), dict)
                else {},
                "image": None,
                "feature_types": [
                    value
                    for value in stored_item.get("feature_types") or []
                    if isinstance(value, str)
                ],
                "compartment_id": None,
                "oci_client_request_id": stored_item.get("oci_client_request_id"),
                "oci_request_id": stored_item.get("oci_request_id"),
                "response": item_result,
                "raw_result": item_result,
                "min_confidence": stored_item.get("min_confidence"),
                "include_full_text": bool(stored_item.get("include_full_text", True)),
                "warnings": _stored_warnings(stored_item.get("warnings")),
                "errors": _stored_errors(item_result.get("errors")),
            }
        )
    return _normalize_batch_result(
        item_results=item_results,
        tool=tool,
        request_id=request_id,
        detail=detail,
        max_items=max_items,
        include_debug_metadata=include_debug_metadata,
        raw_result_path=raw_result_path,
        max_inline_response_bytes=max_inline_response_bytes,
        option_warnings=list(option_warnings or []),
    )


def _stored_errors(value: Any) -> list[ErrorDetail]:
    errors: list[ErrorDetail] = []
    for item in value or []:
        if not isinstance(item, dict):
            continue
        try:
            errors.append(ErrorDetail.model_validate(item))
        except ValueError:
            errors.append(
                ErrorDetail(
                    code=str(item.get("code") or "STORED_ITEM_ERROR"),
                    message=str(item.get("message") or item),
                    retryable=bool(item.get("retryable", False)),
                )
            )
    return errors


def _stored_warnings(value: Any) -> list[WarningDetail]:
    warnings: list[WarningDetail] = []
    for item in value or []:
        if not isinstance(item, dict):
            continue
        try:
            warnings.append(WarningDetail.model_validate(item))
        except ValueError:
            continue
    return warnings


def _batch_model_versions(item_results: list[dict[str, Any]]) -> dict[str, Any]:
    versions: dict[str, Any] = {}
    for item in item_results:
        for key, value in model_versions_from_raw(item.get("raw_result") or {}).items():
            versions.setdefault(key, value)
    return versions


def _batch_image_info(item_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source_type": "batch",
        "items": [
            {
                "index": item["index"],
                **dict(item.get("image_info") or {}),
            }
            for item in item_results
        ],
    }


def _batch_debug_metadata(
    *,
    item_results: list[dict[str, Any]],
    include_debug_metadata: bool,
    detail: ResponseDetail,
) -> dict[str, Any]:
    if not include_debug_metadata and detail != ResponseDetail.RAW:
        return {}
    debug_metadata: dict[str, Any] = {
        "model_versions": _batch_model_versions(item_results),
    }
    if detail == ResponseDetail.RAW:
        oci_request_ids = [
            str(item["oci_request_id"])
            for item in item_results
            if item.get("oci_request_id")
        ]
        debug_metadata.update(
            {
                "oci_request_id": oci_request_ids[0] if oci_request_ids else None,
                "oci_request_ids": oci_request_ids,
            }
        )
    return {
        key: value
        for key, value in debug_metadata.items()
        if value not in (None, [], {})
    }


def _batch_warnings(
    option_warnings: list[WarningDetail],
    item_results: list[dict[str, Any]],
) -> list[WarningDetail]:
    warnings = list(option_warnings)
    if any(item.get("warnings") for item in item_results):
        warnings.append(
            WarningDetail(
                code="UNTRUSTED_URL_OCR_TEXT",
                message="OCR/text output from URL-sourced images is untrusted content.",
            )
        )
    return warnings


def _child_request_id(base_request_id: str, *, index: int, total_count: int) -> str:
    if total_count == 1:
        return base_request_id
    suffix = f"-{index + 1}"
    return f"{base_request_id[: 255 - len(suffix)]}{suffix}"


def _batch_message(*, total_count: int, succeeded_count: int, failed_count: int) -> str:
    if failed_count == 0:
        return f"parallel_analyze_image completed {succeeded_count}/{total_count} images."
    if succeeded_count == 0:
        return f"parallel_analyze_image failed for all {total_count} images."
    return (
        f"parallel_analyze_image completed {succeeded_count}/{total_count} images "
        f"with {failed_count} failures."
    )


def _errors_from_visible_item(item: dict[str, Any]) -> list[ErrorDetail]:
    errors = []
    for error in item.get("errors") or []:
        if isinstance(error, dict):
            errors.append(ErrorDetail.model_validate(error))
    return errors


__all__ = [
    "parallel_analyze_image",
    "render_stored_parallel_result",
    "run_parallel_analyze_image_tool",
]
