"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import oci

from ..config.consts import (
    FEATURE_FACE_DETECTION,
    FEATURE_IMAGE_CLASSIFICATION,
    FEATURE_OBJECT_DETECTION,
    FEATURE_TEXT_DETECTION,
)
from ..config.schemas import ImageAnalysisFeature, OciObjectInput


def image_classification_feature(*, max_results: int | None = None):
    return oci.ai_vision.models.ImageClassificationFeature(
        feature_type=FEATURE_IMAGE_CLASSIFICATION,
        max_results=max_results or 5,
    )


def object_detection_feature(*, max_results: int | None = None):
    return oci.ai_vision.models.ImageObjectDetectionFeature(
        feature_type=FEATURE_OBJECT_DETECTION,
        max_results=max_results or 50,
    )


def face_detection_feature(
    *,
    max_results: int | None = None,
    should_return_landmarks: bool = False,
):
    return oci.ai_vision.models.FaceDetectionFeature(
        feature_type=FEATURE_FACE_DETECTION,
        max_results=max_results or 50,
        should_return_landmarks=should_return_landmarks,
    )


def text_detection_feature():
    return oci.ai_vision.models.ImageTextDetectionFeature(
        feature_type=FEATURE_TEXT_DETECTION,
    )


def image_feature_from_name(
    feature: ImageAnalysisFeature | str,
    *,
    max_results: int | None = None,
    should_return_landmarks: bool = False,
):
    value = feature.value if hasattr(feature, "value") else str(feature)
    if value == ImageAnalysisFeature.IMAGE_CLASSIFICATION.value:
        return image_classification_feature(max_results=max_results)
    if value == ImageAnalysisFeature.OBJECT_DETECTION.value:
        return object_detection_feature(max_results=max_results)
    if value == ImageAnalysisFeature.FACE_DETECTION.value:
        return face_detection_feature(
            max_results=max_results,
            should_return_landmarks=should_return_landmarks,
        )
    if value == ImageAnalysisFeature.TEXT_DETECTION.value:
        return text_detection_feature()
    raise ValueError(f"Unsupported image analysis feature: {feature}")


def object_list_input_location(objects: list[OciObjectInput]):
    return oci.ai_vision.models.ObjectListInlineInputLocation(
        source_type="OBJECT_LIST_INLINE_INPUT_LOCATION",
        object_locations=[
            oci.ai_vision.models.ObjectLocation(
                namespace_name=item.namespace,
                bucket_name=item.bucket,
                object_name=item.object_name,
            )
            for item in objects
        ],
    )


def output_location(*, namespace: str, bucket: str, prefix: str):
    return oci.ai_vision.models.OutputLocation(
        namespace_name=namespace,
        bucket_name=bucket,
        prefix=prefix.strip("/"),
    )


__all__ = [
    "FEATURE_FACE_DETECTION",
    "FEATURE_IMAGE_CLASSIFICATION",
    "FEATURE_OBJECT_DETECTION",
    "FEATURE_TEXT_DETECTION",
    "face_detection_feature",
    "image_feature_from_name",
    "image_classification_feature",
    "object_detection_feature",
    "object_list_input_location",
    "output_location",
    "text_detection_feature",
]
