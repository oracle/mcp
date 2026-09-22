"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from types import SimpleNamespace

from oracle.oci_vision_mcp_server.config.schemas import ResponseDetail
from oracle.oci_vision_mcp_server.oci_mapper.vision_results import normalize_response, summary_text


def test_normalizes_classification_response() -> None:
    response = SimpleNamespace(
        data={
            "labels": [
                {"name": "cat", "confidence": 0.99},
                {"name": "low", "confidence": 0.10},
            ],
            "ontology_classes": [{"name": "animal"}],
            "image_classification_model_version": "1.0",
            "errors": [],
        },
        opc_request_id="REQ123",
    )

    envelope = normalize_response(
        response,
        tool="classify_image",
        feature_type="IMAGE_CLASSIFICATION",
        request_id="REQ123",
        detail=ResponseDetail.SUMMARY,
        max_items=10,
        include_debug_metadata=True,
        min_confidence=0.5,
    )

    assert envelope.status == "succeeded"
    assert envelope.request_id == "REQ123"
    assert envelope.mcp_request_id == "REQ123"
    assert envelope.debug_metadata == {"model_versions": {"image_classification": "1.0"}}
    assert envelope.results["summary"]["labels"] == [{"name": "cat", "confidence": 0.99}]
    assert "base64" not in summary_text(envelope).lower()


def test_raw_detail_exposes_oci_request_id_in_debug_metadata() -> None:
    response = SimpleNamespace(
        data={
            "labels": [{"name": "cat", "confidence": 0.99}],
            "image_classification_model_version": "1.0",
            "errors": [],
        },
        opc_request_id="OCI_REQ",
    )

    envelope = normalize_response(
        response,
        tool="classify_image",
        feature_type="IMAGE_CLASSIFICATION",
        request_id="MCP_REQ",
        detail=ResponseDetail.RAW,
        max_items=10,
        include_debug_metadata=False,
        raw_result_path="/tmp/result.raw.json",
    )

    assert envelope.request_id == "MCP_REQ"
    assert envelope.mcp_request_id == "MCP_REQ"
    assert envelope.debug_metadata["oci_request_id"] == "OCI_REQ"
    assert envelope.debug_metadata["oci_request_ids"] == ["OCI_REQ"]


def test_excludes_full_text_when_requested() -> None:
    response = SimpleNamespace(
        data={
            "image_text": {
                "text": "sensitive full text",
                "lines": [{"text": "line one", "confidence": 0.9}],
            },
            "errors": [],
        }
    )

    envelope = normalize_response(
        response,
        tool="detect_text",
        feature_type="TEXT_DETECTION",
        request_id="REQ123",
        detail=ResponseDetail.STANDARD,
        max_items=10,
        include_debug_metadata=False,
        include_full_text=False,
    )

    assert "text" not in envelope.results["text"]
    assert envelope.results["text"]["lines"] == [{"text": "line one", "confidence": 0.9}]


def test_object_summary_aggregates_names_and_truncates() -> None:
    response = SimpleNamespace(
        data={
            "image_objects": [
                {"name": "Person", "confidence": 0.9},
                {"name": "Person", "confidence": 0.7},
                {"name": "Laptop", "confidence": 0.8},
            ],
            "errors": [],
        }
    )

    envelope = normalize_response(
        response,
        tool="detect_objects",
        feature_type="OBJECT_DETECTION",
        request_id="REQ123",
        detail=ResponseDetail.SUMMARY,
        max_items=1,
        include_debug_metadata=False,
    )

    assert envelope.results["summary"]["object_count"] == 3
    assert envelope.results["summary"]["classes"] == [
        {"name": "Person", "count": 2, "max_confidence": 0.9}
    ]
    assert envelope.truncated is True


def test_object_boxes_convert_polygon_to_box() -> None:
    response = SimpleNamespace(
        data={
            "image_objects": [
                {
                    "name": "Person",
                    "confidence": 0.9,
                    "bounding_polygon": {
                        "normalized_vertices": [
                            {"x": 0.4, "y": 0.2},
                            {"x": 0.8, "y": 0.9},
                            {"x": 0.3, "y": 0.6},
                        ]
                    },
                }
            ],
            "errors": [],
        }
    )

    envelope = normalize_response(
        response,
        tool="detect_objects",
        feature_type="OBJECT_DETECTION",
        request_id="REQ123",
        detail=ResponseDetail.BOXES,
        max_items=10,
        include_debug_metadata=False,
    )

    assert envelope.results["objects"] == [
        {"name": "Person", "confidence": 0.9, "box": [0.3, 0.2, 0.8, 0.9]}
    ]


def test_classification_boxes_falls_back_to_standard() -> None:
    response = SimpleNamespace(
        data={
            "labels": [{"name": "cat", "confidence": 0.99}],
            "ontology_classes": [{"name": "animal"}],
            "errors": [],
        }
    )

    envelope = normalize_response(
        response,
        tool="classify_image",
        feature_type="IMAGE_CLASSIFICATION",
        request_id="REQ123",
        detail=ResponseDetail.BOXES,
        max_items=10,
        include_debug_metadata=False,
    )

    assert envelope.detail == ResponseDetail.STANDARD
    assert envelope.results["labels"] == [{"name": "cat", "confidence": 0.99}]
    assert envelope.warnings[0].code == "DETAIL_FALLBACK"


def test_text_summary_omits_full_text() -> None:
    response = SimpleNamespace(
        data={
            "image_text": {
                "text": "large full OCR text",
                "lines": [{"text": "line one"}, {"text": "line two"}],
            },
            "errors": [],
        }
    )

    envelope = normalize_response(
        response,
        tool="detect_text",
        feature_type="TEXT_DETECTION",
        request_id="REQ123",
        detail=ResponseDetail.SUMMARY,
        max_items=1,
        include_debug_metadata=False,
    )

    assert envelope.results == {
        "summary": {
            "line_count": 2,
            "sample_lines": ["line one"],
            "full_text_available": True,
        }
    }
    assert "large full OCR text" not in str(envelope.results)
    assert envelope.truncated is True


def test_text_min_confidence_filters_lines_and_words_and_remaps_indexes() -> None:
    response = SimpleNamespace(
        data={
            "image_text": {
                "words": [
                    {"text": "Invoice", "confidence": 0.98},
                    {"text": "I234S", "confidence": 0.62},
                    {"text": "Total", "confidence": 0.93},
                ],
                "lines": [
                    {
                        "text": "Invoice I234S",
                        "confidence": 0.91,
                        "word_indexes": [0, 1],
                    },
                    {"text": "discarded", "confidence": 0.5, "word_indexes": [2]},
                    {"text": "Total", "confidence": 0.95, "word_indexes": [2]},
                ],
            },
            "errors": [],
        }
    )

    envelope = normalize_response(
        response,
        tool="detect_text",
        feature_type="TEXT_DETECTION",
        request_id="REQ123",
        detail=ResponseDetail.STANDARD,
        max_items=10,
        include_debug_metadata=False,
        min_confidence=0.8,
    )

    assert envelope.results["text"]["words"] == [
        {"text": "Invoice", "confidence": 0.98},
        {"text": "Total", "confidence": 0.93},
    ]
    assert envelope.results["text"]["lines"] == [
        {"text": "Invoice I234S", "confidence": 0.91, "word_indexes": [0]},
        {"text": "Total", "confidence": 0.95, "word_indexes": [1]},
    ]
    assert envelope.results["text"]["text"] == "Invoice I234S\nTotal"


def test_text_min_confidence_removes_missing_scores_but_raw_stays_unfiltered() -> None:
    response = SimpleNamespace(
        data={
            "image_text": {
                "words": [{"text": "uncertain"}],
                "lines": [{"text": "uncertain", "word_indexes": [0]}],
            },
            "errors": [],
        }
    )

    summary = normalize_response(
        response,
        tool="detect_text",
        feature_type="TEXT_DETECTION",
        request_id="REQ123",
        detail=ResponseDetail.SUMMARY,
        max_items=10,
        include_debug_metadata=False,
        min_confidence=0.8,
    )
    raw = normalize_response(
        response,
        tool="detect_text",
        feature_type="TEXT_DETECTION",
        request_id="REQ123",
        detail=ResponseDetail.RAW,
        max_items=10,
        include_debug_metadata=False,
        min_confidence=0.8,
    )

    assert summary.results["summary"]["line_count"] == 0
    assert raw.results["raw_result_inline"]["image_text"]["lines"][0]["text"] == "uncertain"


def test_face_summary_standard_and_boxes_cover_landmarks_and_polygons() -> None:
    response = SimpleNamespace(
        data={
            "detected_faces": [
                {
                    "confidence": 0.9,
                    "landmarks": [{"type": "EYE", "x": 0.1, "y": 0.2}],
                    "boundingPolygon": [
                        {"x": 0.1, "y": 0.2},
                        {"x": 0.5, "y": 0.8},
                        "bad vertex",
                        {"x": "bad", "y": 0.9},
                    ],
                },
                {"confidence": 0.7, "bounding_polygon": []},
            ],
            "errors": [],
        }
    )

    summary = normalize_response(
        response,
        tool="detect_faces",
        feature_type="FACE_DETECTION",
        request_id="REQ123",
        detail=ResponseDetail.SUMMARY,
        max_items=10,
        include_debug_metadata=False,
    )
    boxes = normalize_response(
        response,
        tool="detect_faces",
        feature_type="FACE_DETECTION",
        request_id="REQ123",
        detail=ResponseDetail.BOXES,
        max_items=1,
        include_debug_metadata=False,
    )
    standard = normalize_response(
        response,
        tool="detect_faces",
        feature_type="FACE_DETECTION",
        request_id="REQ123",
        detail=ResponseDetail.STANDARD,
        max_items=10,
        include_debug_metadata=False,
    )

    assert summary.results["summary"] == {
        "face_count": 2,
        "max_confidence": 0.9,
        "landmarks_available": True,
    }
    assert boxes.results["faces"] == [
        {
            "confidence": 0.9,
            "box": [0.1, 0.2, 0.5, 0.8],
            "landmarks": [{"type": "EYE", "x": 0.1, "y": 0.2}],
        }
    ]
    assert boxes.truncated is True
    assert standard.results["faces"] == [{"confidence": 0.9}, {"confidence": 0.7}]


def test_text_standard_handles_malformed_payload_and_word_fallback() -> None:
    malformed = normalize_response(
        SimpleNamespace(data={"image_text": "not-a-dict", "errors": []}),
        tool="detect_text",
        feature_type="TEXT_DETECTION",
        request_id="REQ123",
        detail=ResponseDetail.STANDARD,
        max_items=10,
        include_debug_metadata=False,
    )
    no_word_indexes = normalize_response(
        SimpleNamespace(
            data={
                "image_text": {
                    "lines": [{"text": "plain line", "confidence": 0.9}],
                    "words": [
                        {"text": "keep", "confidence": 0.9},
                        {"text": "drop", "confidence": 0.1},
                    ],
                },
                "errors": [],
            }
        ),
        tool="detect_text",
        feature_type="TEXT_DETECTION",
        request_id="REQ124",
        detail=ResponseDetail.STANDARD,
        max_items=1,
        include_debug_metadata=False,
        min_confidence=0.5,
    )

    assert malformed.results == {
        "summary": {
            "line_count": 0,
            "sample_lines": [],
            "full_text_available": False,
        }
    }
    assert no_word_indexes.results["text"]["lines"] == [{"text": "plain line", "confidence": 0.9}]
    assert no_word_indexes.results["text"]["words"] == [{"text": "keep", "confidence": 0.9}]
    assert no_word_indexes.truncated is False


def test_summary_text_branches_for_empty_labels_and_direct_result_shapes() -> None:
    empty_labels = normalize_response(
        SimpleNamespace(data={"labels": [], "errors": []}),
        tool="classify_image",
        feature_type="IMAGE_CLASSIFICATION",
        request_id="REQ123",
        detail=ResponseDetail.SUMMARY,
        max_items=10,
        include_debug_metadata=False,
    )
    direct_objects = normalize_response(
        SimpleNamespace(data={"image_objects": [{"name": "Car"}], "errors": []}),
        tool="detect_objects",
        feature_type="OBJECT_DETECTION",
        request_id="REQ124",
        detail=ResponseDetail.STANDARD,
        max_items=10,
        include_debug_metadata=False,
    )
    direct_text = normalize_response(
        SimpleNamespace(data={"image_text": {"lines": ["one", "two"]}, "errors": []}),
        tool="detect_text",
        feature_type="TEXT_DETECTION",
        request_id="REQ125",
        detail=ResponseDetail.STANDARD,
        max_items=10,
        include_debug_metadata=False,
    )

    assert summary_text(empty_labels) == "Detected 0 labels."
    assert summary_text(direct_objects) == "Detected 1 objects."
    assert summary_text(direct_text) == "Detected text with 2 lines."
