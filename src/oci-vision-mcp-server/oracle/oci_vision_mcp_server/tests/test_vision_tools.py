"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from oracle.oci_vision_mcp_server.config.consts import (
    FEATURE_FACE_DETECTION,
    FEATURE_IMAGE_CLASSIFICATION,
    FEATURE_OBJECT_DETECTION,
    FEATURE_TEXT_DETECTION,
)
from oracle.oci_vision_mcp_server.config.schemas import ImageInput, ImageSourceType
from oracle.oci_vision_mcp_server.oci_mapper.vision_features import (
    face_detection_feature,
    image_classification_feature,
    object_detection_feature,
    text_detection_feature,
)
from oracle.oci_vision_mcp_server.tools.vision_api_tools import (
    detect_faces,
    detect_objects,
    detect_text,
)


def test_vision_feature_factories_set_feature_types_and_defaults() -> None:
    classification = image_classification_feature()
    objects = object_detection_feature(max_results=7)
    faces = face_detection_feature(should_return_landmarks=True)
    text = text_detection_feature()

    assert classification.feature_type == FEATURE_IMAGE_CLASSIFICATION
    assert classification.max_results == 5
    assert objects.feature_type == FEATURE_OBJECT_DETECTION
    assert objects.max_results == 7
    assert faces.feature_type == FEATURE_FACE_DETECTION
    assert faces.max_results == 50
    assert faces.should_return_landmarks is True
    assert text.feature_type == FEATURE_TEXT_DETECTION


def test_detect_tool_wrappers_delegate_to_runner(monkeypatch) -> None:
    calls = []

    def fake_run_vision_tool(**kwargs):
        calls.append(kwargs)
        return kwargs["tool"]

    monkeypatch.setattr(detect_objects, "run_vision_tool", fake_run_vision_tool)
    monkeypatch.setattr(detect_faces, "run_vision_tool", fake_run_vision_tool)
    monkeypatch.setattr(detect_text, "run_vision_tool", fake_run_vision_tool)

    image = ImageInput(source_type=ImageSourceType.BASE64, data="aW1hZ2U=")

    assert detect_objects.detect_objects(image=image, max_results=3) == "detect_objects"
    assert detect_faces.detect_faces(image=image, should_return_landmarks=True) == "detect_faces"
    assert detect_text.detect_text(image=image, include_full_text=False) == "detect_text"

    assert calls[0]["feature_type"] == FEATURE_OBJECT_DETECTION
    assert calls[1]["feature_type"] == FEATURE_FACE_DETECTION
    assert calls[2]["feature_type"] == FEATURE_TEXT_DETECTION
