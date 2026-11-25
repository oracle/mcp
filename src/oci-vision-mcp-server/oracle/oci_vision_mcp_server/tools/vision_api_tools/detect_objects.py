"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from mcp.types import CallToolResult

from ...config.consts import FEATURE_OBJECT_DETECTION, TOOL_DETECT_OBJECTS
from ...config.schemas import ImageInput, ToolOptions, VisionToolInput
from ...oci_mapper.vision_features import object_detection_feature
from ...runtime.mcp_app import mcp
from .runner import run_vision_tool


@mcp.tool(name=TOOL_DETECT_OBJECTS)
def detect_objects(
    image: ImageInput,
    compartment_id: str | None = None,
    max_results: int | None = None,
    min_confidence: float | None = None,
    options: ToolOptions | None = None,
) -> CallToolResult:
    """Find object instances in one image and optionally return bounding boxes.

    Call this when the user asks to detect, locate, count, or draw boxes around
    things in an image. Provide image.source_type and exactly one carrier:
    file_path with path, base64 with data, oci_object with
    namespace/bucket/object_name, or opt-in HTTPS url. Use options.detail=boxes
    when bounding boxes are needed, summary for grouped counts by class, standard for compact object
    names/confidences, and raw only for raw OCI output. max_results controls the
    OCI feature limit; min_confidence filters returned detections.
    """
    return run_vision_tool(
        tool=TOOL_DETECT_OBJECTS,
        feature_type=FEATURE_OBJECT_DETECTION,
        input_model=VisionToolInput,
        raw_args={
            "image": image,
            "compartment_id": compartment_id,
            "max_results": max_results,
            "min_confidence": min_confidence,
            "options": options or {},
        },
        feature_factory=lambda args: object_detection_feature(max_results=args.max_results),
    )
