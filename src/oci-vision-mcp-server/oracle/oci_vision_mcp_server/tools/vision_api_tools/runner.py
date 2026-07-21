"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from typing import Any, Callable

import oci
from mcp.types import CallToolResult, TextContent

from ...authentication.auth import ensure_session_auth
from ...config.consts import (
    FEATURE_FACE_DETECTION,
    FEATURE_IMAGE_CLASSIFICATION,
    FEATURE_OBJECT_DETECTION,
    FEATURE_TEXT_DETECTION,
    MAX_IMAGE_JOB_REQUEST_BYTES,
)
from ...config.settings import ResolvedMcpConfig, get_resolved_config
from ...responses.errors import (
    log_tool_failure,
    redact_diagnostic_fields,
    result_persistence_warning,
    response_header,
    response_request_id,
    vision_service_error_envelope,
)
from ...io.image_loader import ImageResolver, ImageResolverError
from ...io.result_store import (
    ResultStoreError,
    generate_request_id,
    store_analysis_result,
    store_tool_result,
)
from ...oci_mapper.vision_features import (
    image_feature_from_name,
    object_list_input_location,
    output_location,
)
from ...oci_mapper.vision_results import (
    normalize_exception,
    normalize_image_analysis_response,
    normalize_operation_response,
    normalize_response,
    summary_text,
)
from ...oci_clients.vision import (
    call_analyze_image,
    call_analyze_image_features,
    call_cancel_image_job,
    call_create_image_job,
    call_get_image_job,
    create_image_job_payload_size,
    create_vision_client,
)
from ...config.schemas import (
    AnalyzeImageInput,
    CancelImageJobInput,
    CreateImageJobInput,
    FaceToolInput,
    GetImageJobInput,
    ImageAnalysisFeature,
    ImageInput,
    ResponseDetail,
    TextToolInput,
    ToolResultEnvelope,
    VisionToolInput,
    VisionJobOutputInput,
    WarningDetail,
)
from ...authentication.session_signer import SessionAuthenticationError


IMAGE_FEATURE_TYPE_BY_NAME = {
    ImageAnalysisFeature.IMAGE_CLASSIFICATION: FEATURE_IMAGE_CLASSIFICATION,
    ImageAnalysisFeature.OBJECT_DETECTION: FEATURE_OBJECT_DETECTION,
    ImageAnalysisFeature.FACE_DETECTION: FEATURE_FACE_DETECTION,
    ImageAnalysisFeature.TEXT_DETECTION: FEATURE_TEXT_DETECTION,
}


def run_vision_tool(
    *,
    tool: str,
    feature_type: str,
    input_model: type[VisionToolInput] | type[FaceToolInput] | type[TextToolInput],
    raw_args: dict[str, Any],
    feature_factory: Callable[[Any], Any],
) -> CallToolResult:
    args: VisionToolInput | FaceToolInput | TextToolInput | None = None
    resolved_config: ResolvedMcpConfig | None = None
    mcp_request_id: str | None = None
    try:
        mcp_request_id = generate_request_id()
        args = input_model.model_validate(raw_args)
        resolved_config = get_resolved_config(persist_generated_profile=True)
        detail, option_warnings = args.options.effective_detail(
            ResponseDetail(resolved_config.default_detail)
        )
        client_request_id = args.options.request_id
        oci_client_request_id = client_request_id or mcp_request_id
        compartment_id = resolve_compartment_id(args.compartment_id, resolved_config)
        resolver = image_resolver_from_config(resolved_config)
        image_details = resolver.resolve(args.image)
        resolved_image_info = resolver.image_info(args.image)
        feature = feature_factory(args)
        ensure_session_auth()
        client = create_vision_client(
            profile=resolved_config.profile,
            region=args.options.region or resolved_config.region,
        )
        response = call_analyze_image(
            client,
            feature=feature,
            image_details=image_details,
            compartment_id=compartment_id,
            request_id=oci_client_request_id,
        )
        raw_result = oci.util.to_dict(getattr(response, "data", response))
        oci_request_id = getattr(response, "opc_request_id", None)
        metadata: dict[str, Any] = {}
        persistence_warnings: list[WarningDetail] = []
        try:
            metadata = store_analysis_result(
                result_store_dir=resolved_config.result_store_dir,
                request_id=mcp_request_id,
                client_request_id=client_request_id,
                tool=tool,
                feature_type=feature_type,
                region=args.options.region or resolved_config.region,
                compartment_id=compartment_id,
                detail_options={
                    "detail": detail.value,
                    "max_items": args.options.max_items,
                    "include_debug_metadata": args.options.include_debug_metadata,
                    "min_confidence": getattr(args, "min_confidence", None),
                    "include_full_text": getattr(args, "include_full_text", True),
                },
                raw_result=raw_result,
                oci_request_id=oci_request_id,
                model_versions=model_versions_from_raw(raw_result),
                image_info=resolved_image_info,
                ttl_seconds=resolved_config.result_ttl_seconds,
            )
        except ResultStoreError as exc:
            persistence_warnings.append(result_persistence_warning(tool, exc))
        envelope = normalize_response(
            response,
            tool=tool,
            feature_type=feature_type,
            request_id=mcp_request_id,
            detail=detail,
            max_items=args.options.max_items,
            include_debug_metadata=args.options.include_debug_metadata,
            min_confidence=getattr(args, "min_confidence", None),
            include_full_text=getattr(args, "include_full_text", True),
            raw_result_path=str(metadata.get("raw_result_path") or ""),
            max_inline_response_bytes=resolved_config.max_inline_response_bytes,
            warnings=with_url_text_warning(
                [*option_warnings, *persistence_warnings],
                image=args.image,
                includes_text=feature_type == FEATURE_TEXT_DETECTION,
            ),
        )
    except (ImageResolverError, ValueError, SessionAuthenticationError, ResultStoreError) as exc:
        envelope = normalize_exception(tool=tool, feature_type=feature_type, exc=exc, request_id=mcp_request_id)
    except oci.exceptions.ServiceError as exc:
        envelope = vision_service_error(
            exc,
            tool=tool,
            feature_type=feature_type,
            args=args,
            resolved_config=resolved_config,
            request_id=mcp_request_id,
        )
    except Exception as exc:  # OCI SDK exceptions should become tool errors.
        log_tool_failure(tool, exc)
        envelope = normalize_exception(tool=tool, feature_type=feature_type, exc=exc, request_id=mcp_request_id)

    return call_tool_result(envelope)


def run_analyze_image_tool(raw_args: dict[str, Any], *, tool: str) -> CallToolResult:
    args: AnalyzeImageInput | None = None
    resolved_config: ResolvedMcpConfig | None = None
    mcp_request_id: str | None = None
    try:
        mcp_request_id = generate_request_id()
        args = AnalyzeImageInput.model_validate(raw_args)
        resolved_config = get_resolved_config(persist_generated_profile=True)
        detail, option_warnings = args.options.effective_detail(ResponseDetail(resolved_config.default_detail))
        client_request_id = args.options.request_id
        oci_client_request_id = client_request_id or mcp_request_id
        compartment_id = resolve_compartment_id(args.compartment_id, resolved_config)
        resolver = image_resolver_from_config(resolved_config)
        image_details = resolver.resolve(args.image)
        resolved_image_info = resolver.image_info(args.image)
        features = image_features_from_names(
            args.features,
            max_results=args.max_results,
            should_return_landmarks=args.should_return_landmarks,
        )
        feature_types = feature_types_from_names(args.features)
        ensure_session_auth()
        client = create_vision_client(
            profile=resolved_config.profile,
            region=args.options.region or resolved_config.region,
        )
        response = call_analyze_image_features(
            client,
            features=features,
            image_details=image_details,
            compartment_id=compartment_id,
            request_id=oci_client_request_id,
        )
        raw_result = oci.util.to_dict(getattr(response, "data", response))
        oci_request_id = getattr(response, "opc_request_id", None)
        metadata = {}
        persistence_warnings = []
        try:
            metadata = store_tool_result(
                result_store_dir=resolved_config.result_store_dir,
                mcp_request_id=mcp_request_id,
                client_request_id=client_request_id,
                tool=tool,
                provider="oci_vision",
                raw_result=raw_result,
                oci_request_id=oci_request_id,
                oci_request_ids=[oci_request_id] if oci_request_id else [],
                region=args.options.region or resolved_config.region,
                feature_type=",".join(feature_types),
                compartment_id=compartment_id,
                detail_options={
                    "detail": detail.value,
                    "max_items": args.options.max_items,
                    "include_debug_metadata": args.options.include_debug_metadata,
                    "min_confidence": args.min_confidence,
                    "include_full_text": args.include_full_text,
                },
                model_versions=model_versions_from_raw(raw_result),
                image_info=resolved_image_info,
                result_kind="vision_combined",
                ttl_seconds=resolved_config.result_ttl_seconds,
            )
        except ResultStoreError as exc:
            persistence_warnings.append(result_persistence_warning(tool, exc))
        envelope = normalize_image_analysis_response(
            response,
            tool=tool,
            feature_types=feature_types,
            request_id=mcp_request_id,
            detail=detail,
            max_items=args.options.max_items,
            include_debug_metadata=args.options.include_debug_metadata,
            min_confidence=args.min_confidence,
            include_full_text=args.include_full_text,
            raw_result_path=str(metadata.get("raw_result_path") or ""),
            max_inline_response_bytes=resolved_config.max_inline_response_bytes,
            warnings=with_url_text_warning(
                [*option_warnings, *persistence_warnings],
                image=args.image,
                includes_text=FEATURE_TEXT_DETECTION in feature_types,
            ),
        )
    except (ImageResolverError, ValueError, SessionAuthenticationError, ResultStoreError) as exc:
        envelope = normalize_exception(tool=tool, feature_type="analyze_image", exc=exc, request_id=mcp_request_id)
    except oci.exceptions.ServiceError as exc:
        envelope = vision_service_error(exc, tool=tool, feature_type="analyze_image", args=args, resolved_config=resolved_config, request_id=mcp_request_id)
    except Exception as exc:
        log_tool_failure(tool, exc)
        envelope = normalize_exception(tool=tool, feature_type="analyze_image", exc=exc, request_id=mcp_request_id)
    return call_tool_result(envelope)


def run_create_image_job_tool(raw_args: dict[str, Any], *, tool: str) -> CallToolResult:
    args: CreateImageJobInput | None = None
    resolved_config: ResolvedMcpConfig | None = None
    mcp_request_id: str | None = None
    try:
        mcp_request_id = generate_request_id()
        args = CreateImageJobInput.model_validate(raw_args)
        resolved_config = get_resolved_config(persist_generated_profile=True)
        detail, option_warnings = args.options.effective_detail(ResponseDetail(resolved_config.default_detail))
        client_request_id = args.options.request_id
        compartment_id = resolve_compartment_id(args.compartment_id, resolved_config)
        input_location = object_list_input_location(args.objects)
        selected_output = _resolve_job_output_location(
            output=args.output_location,
            resolved_config=resolved_config,
            tool=tool,
            mcp_request_id=mcp_request_id,
        )
        features = image_features_from_names(
            args.features,
            max_results=args.max_results,
            should_return_landmarks=args.should_return_landmarks,
        )
        feature_types = feature_types_from_names(args.features)
        request_body_size = create_image_job_payload_size(
            input_location=input_location,
            features=features,
            output_location=selected_output,
            compartment_id=compartment_id,
            display_name=args.display_name,
            is_zip_output_enabled=args.is_zip_output_enabled,
        )
        if request_body_size > MAX_IMAGE_JOB_REQUEST_BYTES:
            raise ValueError(
                "create_image_job request body exceeds OCI Vision's 500 KB limit. "
                "Use fewer objects or shorter namespace, bucket, and object names."
            )
        ensure_session_auth()
        client = create_vision_client(
            profile=resolved_config.profile,
            region=args.options.region or resolved_config.region,
        )
        response = call_create_image_job(
            client,
            input_location=input_location,
            features=features,
            output_location=selected_output,
            compartment_id=compartment_id,
            display_name=args.display_name,
            is_zip_output_enabled=args.is_zip_output_enabled,
            request_id=client_request_id or mcp_request_id,
        )
        envelope = _store_and_normalize_operation(
            response=response,
            tool=tool,
            feature_type=",".join(feature_types),
            request_id=mcp_request_id,
            client_request_id=client_request_id,
            resolved_config=resolved_config,
            detail=detail,
            max_items=args.options.max_items,
            include_debug_metadata=args.options.include_debug_metadata,
            option_warnings=option_warnings,
            region=args.options.region or resolved_config.region,
            compartment_id=compartment_id,
            results=_operation_results(response, message=f"{tool} submitted an OCI Vision image job."),
            object_storage_info={
                "input_objects": [item.model_dump(mode="json") for item in args.objects],
                "output_location": _location_dict(selected_output),
            },
        )
    except (ValueError, SessionAuthenticationError, ResultStoreError) as exc:
        envelope = normalize_exception(tool=tool, feature_type="image_job", exc=exc, request_id=mcp_request_id)
    except oci.exceptions.ServiceError as exc:
        envelope = vision_service_error(exc, tool=tool, feature_type="image_job", args=args, resolved_config=resolved_config, request_id=mcp_request_id)
    except Exception as exc:
        log_tool_failure(tool, exc)
        envelope = normalize_exception(tool=tool, feature_type="image_job", exc=exc, request_id=mcp_request_id)
    return call_tool_result(envelope)


def run_get_image_job_tool(raw_args: dict[str, Any], *, tool: str) -> CallToolResult:
    return _run_image_job_lookup_tool(
        raw_args,
        tool=tool,
        input_model=GetImageJobInput,
        call_factory=call_get_image_job,
    )


def run_cancel_image_job_tool(raw_args: dict[str, Any], *, tool: str) -> CallToolResult:
    return _run_image_job_lookup_tool(
        raw_args,
        tool=tool,
        input_model=CancelImageJobInput,
        call_factory=call_cancel_image_job,
    )


def image_info(image: ImageInput) -> dict[str, Any]:
    info: dict[str, Any] = {
        "source_type": image.source_type.value,
        "path": image.path,
        "object_name": None,
        "namespace": None,
        "bucket": None,
    }
    if image.oci_object:
        info["namespace"] = image.oci_object.namespace
        info["bucket"] = image.oci_object.bucket
        info["object_name"] = image.oci_object.object_name
    if image.url:
        info["url"] = {"scheme": "https", "host": "", "path": ""}
    return info


def image_resolver_from_config(resolved_config: ResolvedMcpConfig) -> ImageResolver:
    return ImageResolver(
        base_dir=resolved_config.image_base_dir,
        max_image_bytes=resolved_config.max_image_bytes,
        enable_url_inputs=resolved_config.enable_url_inputs,
        url_max_redirects=resolved_config.url_max_redirects,
        url_connect_timeout_seconds=resolved_config.url_connect_timeout_seconds,
        url_read_timeout_seconds=resolved_config.url_read_timeout_seconds,
    )


def image_features_from_names(
    features: list[ImageAnalysisFeature],
    *,
    max_results: int | None = None,
    should_return_landmarks: bool = False,
) -> list[Any]:
    return [
        image_feature_from_name(
            feature,
            max_results=max_results,
            should_return_landmarks=should_return_landmarks,
        )
        for feature in features
    ]


def feature_types_from_names(features: list[ImageAnalysisFeature]) -> list[str]:
    return [IMAGE_FEATURE_TYPE_BY_NAME[feature] for feature in features]


def model_versions_from_raw(response_dict: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "image_classification": "image_classification_model_version",
        "object_detection": "object_detection_model_version",
        "text_detection": "text_detection_model_version",
        "face_detection": "face_detection_model_version",
    }
    return {key: response_dict[value] for key, value in mapping.items() if response_dict.get(value)}


def with_url_text_warning(
    warnings: list[WarningDetail],
    *,
    image: ImageInput,
    includes_text: bool,
) -> list[WarningDetail]:
    result = list(warnings)
    if includes_text and image.source_type.value == "url":
        result.append(
            WarningDetail(
                code="UNTRUSTED_URL_OCR_TEXT",
                message="OCR/text output from URL-sourced images is untrusted content.",
            )
        )
    return result


def _run_image_job_lookup_tool(
    raw_args: dict[str, Any],
    *,
    tool: str,
    input_model: type[GetImageJobInput] | type[CancelImageJobInput],
    call_factory: Callable[..., Any],
) -> CallToolResult:
    args: GetImageJobInput | CancelImageJobInput | None = None
    resolved_config: ResolvedMcpConfig | None = None
    mcp_request_id: str | None = None
    try:
        mcp_request_id = generate_request_id()
        args = input_model.model_validate(raw_args)
        if isinstance(args, CancelImageJobInput) and not args.confirm:
            raise ValueError("confirm=true is required before canceling an image job.")
        resolved_config = get_resolved_config(persist_generated_profile=True)
        detail, option_warnings = args.options.effective_detail(ResponseDetail(resolved_config.default_detail))
        client_request_id = args.options.request_id
        ensure_session_auth()
        client = create_vision_client(
            profile=resolved_config.profile,
            region=args.options.region or resolved_config.region,
        )
        response = call_factory(client=client, job_id=args.job_id, request_id=client_request_id or mcp_request_id)
        envelope = _store_and_normalize_operation(
            response=response,
            tool=tool,
            feature_type="image_job",
            request_id=mcp_request_id,
            client_request_id=client_request_id,
            resolved_config=resolved_config,
            detail=detail,
            max_items=args.options.max_items,
            include_debug_metadata=args.options.include_debug_metadata,
            option_warnings=option_warnings,
            region=args.options.region or resolved_config.region,
            compartment_id=None,
            results=_operation_results(response, message=f"{tool} completed."),
        )
    except (ValueError, SessionAuthenticationError, ResultStoreError) as exc:
        envelope = normalize_exception(tool=tool, feature_type="image_job", exc=exc, request_id=mcp_request_id)
    except oci.exceptions.ServiceError as exc:
        envelope = vision_service_error(exc, tool=tool, feature_type="image_job", args=args, resolved_config=resolved_config, request_id=mcp_request_id)
    except Exception as exc:
        log_tool_failure(tool, exc)
        envelope = normalize_exception(tool=tool, feature_type="image_job", exc=exc, request_id=mcp_request_id)
    return call_tool_result(envelope)


def _store_and_normalize_operation(
    *,
    response: Any,
    tool: str,
    feature_type: str,
    request_id: str,
    client_request_id: str | None,
    resolved_config: ResolvedMcpConfig,
    detail: ResponseDetail,
    max_items: int,
    include_debug_metadata: bool,
    option_warnings: list[Any],
    region: str,
    compartment_id: str | None,
    results: dict[str, Any],
    object_storage_info: dict[str, Any] | None = None,
) -> ToolResultEnvelope:
    raw_result = oci.util.to_dict(getattr(response, "data", response))
    headers = _response_headers(response)
    if headers:
        raw_result = dict(raw_result)
        raw_result["_headers"] = headers
    oci_request_id = response_request_id(response)
    oci_request_ids = _response_request_ids(response)
    metadata: dict[str, Any] = {}
    persistence_warnings: list[WarningDetail] = []
    try:
        metadata = store_tool_result(
            result_store_dir=resolved_config.result_store_dir,
            mcp_request_id=request_id,
            client_request_id=client_request_id,
            tool=tool,
            provider="oci_vision",
            raw_result=raw_result,
            oci_request_id=oci_request_id,
            oci_request_ids=oci_request_ids,
            region=region,
            feature_type=feature_type,
            compartment_id=compartment_id,
            object_storage_info=object_storage_info,
            result_kind="vision_image_job",
            ttl_seconds=resolved_config.result_ttl_seconds,
        )
    except ResultStoreError as exc:
        persistence_warnings.append(result_persistence_warning(tool, exc))
    return normalize_operation_response(
        response,
        tool=tool,
        feature_type=feature_type,
        request_id=request_id,
        detail=detail,
        max_items=max_items,
        include_debug_metadata=include_debug_metadata,
        raw_result_path=str(metadata.get("raw_result_path") or ""),
        max_inline_response_bytes=resolved_config.max_inline_response_bytes,
        results=results,
        warnings=[*option_warnings, *persistence_warnings],
    )


def _operation_results(response: Any, *, message: str) -> dict[str, Any]:
    raw = oci.util.to_dict(getattr(response, "data", response))
    summary = {
        "message": message,
        "id": raw.get("id") if isinstance(raw, dict) else None,
        "lifecycle_state": raw.get("lifecycle_state") if isinstance(raw, dict) else None,
        "status": raw.get("status") if isinstance(raw, dict) else None,
    }
    return {
        "summary": {key: value for key, value in summary.items() if value is not None},
        "data": redact_diagnostic_fields(raw) if isinstance(raw, dict) else {"items": raw},
    }


def _resolve_job_output_location(
    *,
    output: VisionJobOutputInput | None,
    resolved_config: ResolvedMcpConfig,
    tool: str,
    mcp_request_id: str,
):
    namespace = output.namespace if output and output.namespace else resolved_config.job_output_namespace
    bucket = output.bucket if output and output.bucket else resolved_config.job_output_bucket
    if not namespace:
        raise ValueError(
            "Job output namespace is required. Provide output_location.namespace, "
            "set OCI_VISION_JOB_OUTPUT_NAMESPACE, or set OCI_OBJECT_STORAGE_NAMESPACE."
        )
    if not bucket:
        raise ValueError(
            "Job output bucket is required. Provide output_location.bucket, "
            "set OCI_VISION_JOB_OUTPUT_BUCKET, or set OCI_OBJECT_STORAGE_BUCKET."
        )
    del tool, mcp_request_id
    prefix = output.prefix if output and output.prefix else "job_result"
    return output_location(namespace=namespace, bucket=bucket, prefix=prefix)


def _location_dict(location: Any) -> dict[str, Any]:
    return {
        "namespace": getattr(location, "namespace_name", None),
        "bucket": getattr(location, "bucket_name", None),
        "prefix": getattr(location, "prefix", None),
    }


def resolve_compartment_id(value: str | None, resolved_config: ResolvedMcpConfig) -> str:
    compartment_id = value or resolved_config.default_compartment_id
    if not compartment_id:
        raise ValueError(
            "compartment_id is required. Provide it in the tool call or set "
            "OCI_VISION_DEFAULT_COMPARTMENT_ID in your MCP client environment."
        )
    return compartment_id


def vision_service_error(
    exc: oci.exceptions.ServiceError,
    *,
    tool: str,
    feature_type: str,
    args: Any,
    resolved_config: ResolvedMcpConfig | None,
    request_id: str | None,
) -> ToolResultEnvelope:
    selected_region = None
    if args and args.options.region:
        selected_region = args.options.region
    elif resolved_config:
        selected_region = resolved_config.region
    return vision_service_error_envelope(
        exc,
        tool=tool,
        feature_type=feature_type,
        profile=resolved_config.profile if resolved_config else None,
        region=selected_region,
        request_id=request_id,
    )


def call_tool_result(envelope: ToolResultEnvelope) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=summary_text(envelope))],
        structuredContent=envelope.model_dump(mode="json"),
        isError=envelope.status == "failed",
    )


def _response_request_ids(response: Any) -> list[str]:
    request_ids = []
    for header_name in ("opc-request-id", "opc-work-request-id"):
        value = response_header(response, header_name)
        if value:
            request_ids.append(value)
    attr_value = response_request_id(response)
    if attr_value and attr_value not in request_ids:
        request_ids.insert(0, attr_value)
    return request_ids


def _response_headers(response: Any) -> dict[str, str]:
    headers = getattr(response, "headers", None)
    if not headers:
        return {}
    return {str(key): str(value) for key, value in headers.items() if value is not None}


__all__ = [
    "call_tool_result",
    "resolve_compartment_id",
    "feature_types_from_names",
    "image_features_from_names",
    "image_info",
    "image_resolver_from_config",
    "model_versions_from_raw",
    "run_analyze_image_tool",
    "run_cancel_image_job_tool",
    "run_create_image_job_tool",
    "run_get_image_job_tool",
    "run_vision_tool",
    "vision_service_error",
    "with_url_text_warning",
]
