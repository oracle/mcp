"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from typing import Any

import oci

from ..config.consts import (
    FEATURE_FACE_DETECTION,
    FEATURE_IMAGE_CLASSIFICATION,
    FEATURE_OBJECT_DETECTION,
    FEATURE_TEXT_DETECTION,
    TOOL_CLASSIFY_IMAGE,
    TOOL_DETECT_TEXT,
)
from ..io.result_store import raw_payload_reference
from ..config.schemas import ErrorDetail, ResponseDetail, ToolResultEnvelope, WarningDetail


def normalize_response(
    response: Any,
    *,
    tool: str,
    feature_type: str,
    request_id: str,
    detail: ResponseDetail,
    max_items: int,
    include_debug_metadata: bool,
    min_confidence: float | None = None,
    include_full_text: bool = True,
    raw_result_path: str | None = None,
    max_inline_response_bytes: int = 20_000,
    warnings: list[WarningDetail] | None = None,
) -> ToolResultEnvelope:
    data = getattr(response, "data", response)
    response_dict = oci.util.to_dict(data) if data is not None else {}
    oci_request_id = getattr(response, "opc_request_id", None)
    return render_response_dict(
        response_dict,
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
        oci_request_id=oci_request_id,
        warnings=warnings,
    )


def normalize_image_analysis_response(
    response: Any,
    *,
    tool: str,
    feature_types: list[str],
    request_id: str,
    detail: ResponseDetail,
    max_items: int,
    include_debug_metadata: bool,
    min_confidence: float | None = None,
    include_full_text: bool = True,
    raw_result_path: str | None = None,
    max_inline_response_bytes: int = 20_000,
    warnings: list[WarningDetail] | None = None,
) -> ToolResultEnvelope:
    data = getattr(response, "data", response)
    response_dict = oci.util.to_dict(data) if data is not None else {}
    oci_request_id = getattr(response, "opc_request_id", None)
    warnings = list(warnings or [])
    if detail == ResponseDetail.RAW:
        results, truncated = raw_payload_reference(
            raw_result=response_dict,
            raw_path=raw_result_path,
            max_inline_response_bytes=max_inline_response_bytes,
        ), False
    else:
        results = {}
        truncated = False
        for feature_type in feature_types:
            feature_results, feature_truncated = _results_for_feature(
                response_dict,
                feature_type=feature_type,
                detail=_effective_detail(tool, detail, warnings),
                max_items=max_items,
                min_confidence=min_confidence,
                include_full_text=include_full_text,
                raw_result_path=raw_result_path,
                max_inline_response_bytes=max_inline_response_bytes,
            )
            results[feature_type.lower()] = feature_results
            truncated = truncated or feature_truncated
    return ToolResultEnvelope(
        status="failed" if _response_errors(response_dict) else "succeeded",
        tool=tool,
        feature_type=",".join(feature_types),
        request_id=request_id,
        mcp_request_id=request_id,
        detail=detail,
        results=results,
        truncated=truncated,
        debug_metadata=_debug_metadata(
            response_dict=response_dict,
            include_debug_metadata=include_debug_metadata,
            detail=detail,
            oci_request_id=oci_request_id,
        ),
        warnings=warnings,
        errors=_response_errors(response_dict),
    )


def normalize_operation_response(
    response: Any,
    *,
    tool: str,
    feature_type: str,
    request_id: str,
    detail: ResponseDetail,
    max_items: int,
    include_debug_metadata: bool,
    raw_result_path: str | None = None,
    max_inline_response_bytes: int = 20_000,
    results: dict[str, Any] | None = None,
    warnings: list[WarningDetail] | None = None,
) -> ToolResultEnvelope:
    data = getattr(response, "data", response)
    response_dict = oci.util.to_dict(data) if data is not None else {}
    oci_request_id = getattr(response, "opc_request_id", None)
    if detail == ResponseDetail.RAW:
        selected_results, truncated = raw_payload_reference(
            raw_result=response_dict,
            raw_path=raw_result_path,
            max_inline_response_bytes=max_inline_response_bytes,
        ), False
    else:
        selected_results, truncated = _compact_generic_results(
            results if results is not None else response_dict,
            max_items=max_items,
        )
    return ToolResultEnvelope(
        status="failed" if _response_errors(response_dict) else "succeeded",
        tool=tool,
        feature_type=feature_type,
        request_id=request_id,
        mcp_request_id=request_id,
        detail=detail,
        results=selected_results,
        truncated=truncated,
        debug_metadata=_debug_metadata(
            response_dict=response_dict,
            include_debug_metadata=include_debug_metadata,
            detail=detail,
            oci_request_id=oci_request_id,
        ),
        warnings=list(warnings or []),
        errors=_response_errors(response_dict),
    )


def render_response_dict(
    response_dict: dict[str, Any],
    *,
    tool: str,
    feature_type: str,
    request_id: str,
    detail: ResponseDetail,
    max_items: int,
    include_debug_metadata: bool,
    min_confidence: float | None = None,
    include_full_text: bool = True,
    raw_result_path: str | None = None,
    max_inline_response_bytes: int = 20_000,
    oci_request_id: str | None = None,
    warnings: list[WarningDetail] | None = None,
) -> ToolResultEnvelope:
    warnings = list(warnings or [])
    errors = _response_errors(response_dict)
    effective_detail = _effective_detail(tool, detail, warnings)
    results, truncated = _results_for_feature(
        response_dict,
        feature_type=feature_type,
        detail=effective_detail,
        max_items=max_items,
        min_confidence=min_confidence,
        include_full_text=include_full_text,
        raw_result_path=raw_result_path,
        max_inline_response_bytes=max_inline_response_bytes,
    )
    return ToolResultEnvelope(
        status="failed" if errors else "succeeded",
        tool=tool,
        feature_type=feature_type,
        request_id=request_id,
        mcp_request_id=request_id,
        detail=effective_detail,
        results=results,
        truncated=truncated,
        debug_metadata=_debug_metadata(
            response_dict=response_dict,
            include_debug_metadata=include_debug_metadata,
            detail=effective_detail,
            oci_request_id=oci_request_id,
        ),
        warnings=warnings,
        errors=errors,
    )


def normalize_exception(
    *,
    tool: str,
    feature_type: str,
    exc: Exception,
    request_id: str | None = None,
) -> ToolResultEnvelope:
    return ToolResultEnvelope(
        status="failed",
        tool=tool,
        feature_type=feature_type,
        request_id=request_id,
        mcp_request_id=request_id,
        errors=[
            ErrorDetail(
                code=str(getattr(exc, "code", type(exc).__name__)),
                message=str(exc),
                retryable=bool(getattr(exc, "retryable", False)),
            )
        ],
    )


def summary_text(envelope: ToolResultEnvelope) -> str:
    if envelope.status == "failed":
        first = envelope.errors[0].message if envelope.errors else "Unknown error"
        return f"{envelope.tool} failed: {first}"

    results = envelope.results
    if "summary" in results:
        summary = results["summary"]
        if "classes" in summary:
            return f"Detected {summary.get('object_count', 0)} objects."
        if "labels" in summary:
            labels = summary["labels"]
            if labels:
                top = labels[0].get("name") or "unknown"
                confidence = labels[0].get("confidence")
                return f"Detected {len(labels)} labels. Top label: {top}, confidence {confidence}."
            return "Detected 0 labels."
        if "face_count" in summary:
            return f"Detected {summary.get('face_count', 0)} faces."
        if "line_count" in summary:
            return f"Detected text with {summary.get('line_count', 0)} lines."
        if "message" in summary:
            return str(summary["message"])
    if "objects" in results:
        return f"Detected {len(results['objects'])} objects."
    if "labels" in results:
        return f"Detected {len(results['labels'])} labels."
    if "faces" in results:
        return f"Detected {len(results['faces'])} faces."
    if "text" in results:
        lines = results["text"].get("lines") if isinstance(results["text"], dict) else None
        return f"Detected text with {len(lines or [])} lines."
    if "raw_result_available" in results:
        return f"{envelope.tool} raw result is available."
    return f"{envelope.tool} succeeded."


def _effective_detail(
    tool: str,
    detail: ResponseDetail,
    warnings: list[WarningDetail],
) -> ResponseDetail:
    if detail == ResponseDetail.BOXES and tool in {TOOL_CLASSIFY_IMAGE, TOOL_DETECT_TEXT}:
        warnings.append(
            WarningDetail(
                code="DETAIL_FALLBACK",
                message=f"detail=boxes is not supported for {tool}; returned detail=standard instead.",
            )
        )
        return ResponseDetail.STANDARD
    return detail


def _response_errors(response_dict: dict[str, Any]) -> list[ErrorDetail]:
    return [
        ErrorDetail(
            code=str(item.get("code") or "OCI_VISION_ERROR"),
            message=str(item.get("message") or item),
            retryable=False,
        )
        for item in response_dict.get("errors") or []
        if isinstance(item, dict)
    ]


def _model_versions(response_dict: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "image_classification": "image_classification_model_version",
        "object_detection": "object_detection_model_version",
        "text_detection": "text_detection_model_version",
        "face_detection": "face_detection_model_version",
    }
    return {key: response_dict[value] for key, value in mapping.items() if response_dict.get(value)}


def _results_for_feature(
    response_dict: dict[str, Any],
    *,
    feature_type: str,
    detail: ResponseDetail,
    max_items: int,
    min_confidence: float | None,
    include_full_text: bool,
    raw_result_path: str | None,
    max_inline_response_bytes: int,
) -> tuple[dict[str, Any], bool]:
    if detail == ResponseDetail.RAW:
        return raw_payload_reference(
            raw_result=response_dict,
            raw_path=raw_result_path,
            max_inline_response_bytes=max_inline_response_bytes,
        ), False

    if feature_type == FEATURE_IMAGE_CLASSIFICATION:
        return _classification_results(response_dict, detail=detail, max_items=max_items, min_confidence=min_confidence)
    if feature_type == FEATURE_OBJECT_DETECTION:
        return _object_results(response_dict, detail=detail, max_items=max_items, min_confidence=min_confidence)
    if feature_type == FEATURE_FACE_DETECTION:
        return _face_results(response_dict, detail=detail, max_items=max_items, min_confidence=min_confidence)
    if feature_type == FEATURE_TEXT_DETECTION:
        return _text_results(
            response_dict,
            detail=detail,
            max_items=max_items,
            min_confidence=min_confidence,
            include_full_text=include_full_text,
        )
    return {}, False


def _classification_results(
    response_dict: dict[str, Any],
    *,
    detail: ResponseDetail,
    max_items: int,
    min_confidence: float | None,
) -> tuple[dict[str, Any], bool]:
    labels = _filter_confidence(response_dict.get("labels") or [], min_confidence)
    selected, truncated = _take(labels, max_items)
    compact_labels = [_compact_name_confidence(item) for item in selected if isinstance(item, dict)]
    if detail == ResponseDetail.SUMMARY:
        return {"summary": {"labels": compact_labels}}, truncated
    ontology, ontology_truncated = _take(response_dict.get("ontology_classes") or [], max_items)
    return {
        "labels": compact_labels,
        "ontology_classes": ontology,
    }, truncated or ontology_truncated


def _object_results(
    response_dict: dict[str, Any],
    *,
    detail: ResponseDetail,
    max_items: int,
    min_confidence: float | None,
) -> tuple[dict[str, Any], bool]:
    objects = _filter_confidence(response_dict.get("image_objects") or [], min_confidence)
    if detail == ResponseDetail.SUMMARY:
        classes: dict[str, dict[str, Any]] = {}
        for item in objects:
            if not isinstance(item, dict):
                continue
            name = _name(item)
            if not name:
                continue
            confidence = item.get("confidence")
            current = classes.setdefault(name, {"name": name, "count": 0, "max_confidence": confidence})
            current["count"] += 1
            if confidence is not None:
                prior = current.get("max_confidence")
                current["max_confidence"] = confidence if prior is None else max(prior, confidence)
        selected, truncated = _take(list(classes.values()), max_items)
        return {"summary": {"object_count": len(objects), "classes": selected}}, truncated

    selected, truncated = _take(objects, max_items)
    key = "objects"
    if detail == ResponseDetail.BOXES:
        compact = [_compact_detection(item, include_box=True) for item in selected if isinstance(item, dict)]
        return {key: compact}, truncated

    compact = [_compact_detection(item, include_box=False) for item in selected if isinstance(item, dict)]
    return {key: compact}, truncated


def _face_results(
    response_dict: dict[str, Any],
    *,
    detail: ResponseDetail,
    max_items: int,
    min_confidence: float | None,
) -> tuple[dict[str, Any], bool]:
    faces = _filter_confidence(response_dict.get("detected_faces") or [], min_confidence)
    if detail == ResponseDetail.SUMMARY:
        confidences = [
            item.get("confidence")
            for item in faces
            if isinstance(item, dict) and item.get("confidence") is not None
        ]
        landmarks_available = any(bool(item.get("landmarks")) for item in faces if isinstance(item, dict))
        return {
            "summary": {
                "face_count": len(faces),
                "max_confidence": max(confidences) if confidences else None,
                "landmarks_available": landmarks_available,
            }
        }, False

    selected, truncated = _take(faces, max_items)
    if detail == ResponseDetail.BOXES:
        compact = [
            _compact_face(item, include_box=True, include_landmarks=True)
            for item in selected
            if isinstance(item, dict)
        ]
        return {"faces": compact}, truncated

    compact = [
        _compact_face(item, include_box=False, include_landmarks=False)
        for item in selected
        if isinstance(item, dict)
    ]
    return {"faces": compact}, truncated


def _text_results(
    response_dict: dict[str, Any],
    *,
    detail: ResponseDetail,
    max_items: int,
    min_confidence: float | None,
    include_full_text: bool,
) -> tuple[dict[str, Any], bool]:
    image_text = response_dict.get("image_text") or {}
    if not isinstance(image_text, dict):
        return {"summary": {"line_count": 0, "sample_lines": [], "full_text_available": False}}, False
    lines = _filter_text_confidence(image_text.get("lines") or [], min_confidence)
    selected_lines, lines_truncated = _take(lines, max_items)
    line_texts = [text for text in (_line_text(line) for line in selected_lines) if text]
    if detail == ResponseDetail.SUMMARY:
        return {
            "summary": {
                "line_count": len(lines),
                "sample_lines": line_texts,
                "full_text_available": bool(line_texts),
            }
        }, lines_truncated

    text_result = dict(image_text)
    remapped_lines, selected_words, words_truncated = _remap_filtered_words(
        selected_lines,
        image_text.get("words") or [],
        min_confidence=min_confidence,
        max_items=max_items,
    )
    text_result["lines"] = remapped_lines
    text_result["words"] = selected_words
    if include_full_text:
        text_result["text"] = "\n".join(
            text for text in (_line_text(line) for line in remapped_lines) if text
        )
    else:
        text_result.pop("text", None)
    return {"text": text_result}, lines_truncated or words_truncated


def _filter_text_confidence(items: list[Any], min_confidence: float | None) -> list[Any]:
    if min_confidence is None:
        return list(items)
    return [
        item
        for item in items
        if isinstance(item, dict) and _meets_confidence(item, min_confidence)
    ]


def _meets_confidence(item: dict[str, Any], min_confidence: float) -> bool:
    confidence = item.get("confidence")
    return (
        isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
        and confidence >= min_confidence
    )


def _remap_filtered_words(
    lines: list[Any],
    words: list[Any],
    *,
    min_confidence: float | None,
    max_items: int,
) -> tuple[list[Any], list[Any], bool]:
    """Keep words referenced by returned lines and repair their indexes."""
    has_word_indexes = any(
        isinstance(line, dict) and isinstance(line.get("word_indexes"), list)
        for line in lines
    )
    if not has_word_indexes:
        filtered = _filter_text_confidence(words, min_confidence)
        selected_words, truncated = _take(filtered, max_items)
        return [dict(line) if isinstance(line, dict) else line for line in lines], selected_words, truncated

    selected_words: list[Any] = []
    new_index_by_old: dict[int, int] = {}
    remapped_lines: list[Any] = []
    for line in lines:
        if not isinstance(line, dict):
            remapped_lines.append(line)
            continue
        remapped = dict(line)
        new_indexes: list[int] = []
        for old_index in line.get("word_indexes") or []:
            if not isinstance(old_index, int) or isinstance(old_index, bool):
                continue
            if old_index < 0 or old_index >= len(words):
                continue
            word = words[old_index]
            if not isinstance(word, dict):
                continue
            if min_confidence is not None and not _meets_confidence(word, min_confidence):
                continue
            if old_index not in new_index_by_old:
                new_index_by_old[old_index] = len(selected_words)
                selected_words.append(word)
            new_indexes.append(new_index_by_old[old_index])
        remapped["word_indexes"] = new_indexes
        remapped_lines.append(remapped)
    return remapped_lines, selected_words, False


def _filter_confidence(items: list[Any], min_confidence: float | None) -> list[Any]:
    if min_confidence is None:
        return items
    filtered = []
    for item in items:
        if not isinstance(item, dict):
            filtered.append(item)
            continue
        confidence = item.get("confidence")
        if confidence is None or confidence >= min_confidence:
            filtered.append(item)
    return filtered


def _take(items: list[Any], max_items: int) -> tuple[list[Any], bool]:
    return items[:max_items], len(items) > max_items


def _name(item: dict[str, Any]) -> str | None:
    value = item.get("name") or item.get("label")
    return str(value) if value is not None else None


def _compact_name_confidence(item: dict[str, Any]) -> dict[str, Any]:
    result = {"name": _name(item), "confidence": item.get("confidence")}
    return {key: value for key, value in result.items() if value is not None}


def _compact_detection(item: dict[str, Any], *, include_box: bool) -> dict[str, Any]:
    result = _compact_name_confidence(item)
    if include_box:
        result["box"] = _box_from_detection(item)
    return result


def _compact_face(item: dict[str, Any], *, include_box: bool, include_landmarks: bool) -> dict[str, Any]:
    result = {"confidence": item.get("confidence")}
    if include_box:
        result["box"] = _box_from_detection(item)
    if include_landmarks and item.get("landmarks"):
        result["landmarks"] = item["landmarks"]
    return {key: value for key, value in result.items() if value is not None}


def _box_from_detection(item: dict[str, Any]) -> list[float] | None:
    points = _points_from_polygon(item)
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def _points_from_polygon(item: dict[str, Any]) -> list[tuple[float, float]]:
    polygon = (
        item.get("bounding_polygon")
        or item.get("boundingPolygon")
        or item.get("bounding_polygon_normalized_vertices")
    )
    if isinstance(polygon, dict):
        vertices = polygon.get("normalized_vertices") or polygon.get("normalizedVertices") or polygon.get("vertices")
    else:
        vertices = polygon
    points: list[tuple[float, float]] = []
    if not isinstance(vertices, list):
        return points
    for vertex in vertices:
        if not isinstance(vertex, dict):
            continue
        x = vertex.get("x")
        y = vertex.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            points.append((float(x), float(y)))
    return points


def _line_text(line: Any) -> str | None:
    if isinstance(line, dict):
        text = line.get("text")
        return str(text) if text is not None else None
    return str(line) if line is not None else None


def _compact_generic_results(
    payload: dict[str, Any],
    *,
    max_items: int,
) -> tuple[dict[str, Any], bool]:
    result: dict[str, Any] = {}
    truncated = False
    for key, value in payload.items():
        if isinstance(value, list):
            result[key], item_truncated = _take(value, max_items)
            truncated = truncated or item_truncated
        else:
            result[key] = value
    return result, truncated


def _debug_metadata(
    *,
    response_dict: dict[str, Any],
    include_debug_metadata: bool,
    detail: ResponseDetail,
    oci_request_id: str | None,
) -> dict[str, Any]:
    debug_metadata = {}
    if include_debug_metadata or detail == ResponseDetail.RAW:
        debug_metadata = {
            "model_versions": _model_versions(response_dict),
        }
        if detail == ResponseDetail.RAW:
            debug_metadata["oci_request_id"] = oci_request_id
            debug_metadata["oci_request_ids"] = [oci_request_id] if oci_request_id else []
    return {key: value for key, value in debug_metadata.items() if value not in (None, {}, [])}
