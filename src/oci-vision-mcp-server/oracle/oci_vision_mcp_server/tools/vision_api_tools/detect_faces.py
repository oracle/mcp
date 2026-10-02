"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from mcp.types import CallToolResult

from ...config.consts import FEATURE_FACE_DETECTION, TOOL_DETECT_FACES
from ...config.schemas import FaceToolInput, ImageInput, ToolOptions
from ...oci_mapper.vision_features import face_detection_feature
from ...runtime.mcp_app import mcp
from .runner import run_vision_tool


@mcp.tool(name=TOOL_DETECT_FACES)
def detect_faces(
    image: ImageInput,
    compartment_id: str | None = None,
    max_results: int | None = None,
    should_return_landmarks: bool = False,
    min_confidence: float | None = None,
    options: ToolOptions | None = None,
) -> CallToolResult:
    """Detect faces in one image without identifying or comparing people.

    Call this when the user asks whether faces are present, how many faces are
    visible, or where faces are located. This tool does not perform face
    recognition, identity matching, face comparison, or embedding extraction.
    Provide image.source_type and exactly one image carrier. HTTPS url carriers
    require OCI_VISION_ENABLE_URL_INPUTS=true. Use
    should_return_landmarks=true only when landmarks are explicitly useful. Use
    options.detail=boxes for face boxes and returned landmarks, summary for
    counts, standard for compact face confidences, and raw only for raw OCI
    output/request ids.
    """
    return run_vision_tool(
        tool=TOOL_DETECT_FACES,
        feature_type=FEATURE_FACE_DETECTION,
        input_model=FaceToolInput,
        raw_args={
            "image": image,
            "compartment_id": compartment_id,
            "max_results": max_results,
            "should_return_landmarks": should_return_landmarks,
            "min_confidence": min_confidence,
            "options": options or {},
        },
        feature_factory=lambda args: face_detection_feature(
            max_results=args.max_results or 50,
            should_return_landmarks=args.should_return_landmarks,
        ),
    )
