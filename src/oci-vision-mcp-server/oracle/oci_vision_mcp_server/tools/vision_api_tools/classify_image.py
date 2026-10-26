"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from mcp.types import CallToolResult

from ...config.consts import FEATURE_IMAGE_CLASSIFICATION, TOOL_CLASSIFY_IMAGE
from ...config.schemas import ImageInput, ToolOptions, VisionToolInput
from ...oci_mapper.vision_features import image_classification_feature
from ...runtime.mcp_app import mcp
from .runner import run_vision_tool


@mcp.tool(name=TOOL_CLASSIFY_IMAGE)
def classify_image(
    image: ImageInput,
    compartment_id: str | None = None,
    max_results: int | None = None,
    min_confidence: float | None = None,
    options: ToolOptions | None = None,
) -> CallToolResult:
    """Classify one image into high-level visual labels.

    Call this when the user asks what an image is, asks for tags/categories, or
    wants a general scene/content classification. Provide image.source_type and
    exactly one carrier: file_path with path, base64 with data, oci_object
    with namespace/bucket/object_name, or opt-in HTTPS url. Use detect_objects instead
    when the user asks where objects are or wants bounding boxes. compartment_id is optional
    when OCI_VISION_DEFAULT_COMPARTMENT_ID is configured. Set options.detail to
    summary for compact labels, standard for labels plus ontology classes, or
    raw only when the raw OCI response/request ids are needed.
    """
    return run_vision_tool(
        tool=TOOL_CLASSIFY_IMAGE,
        feature_type=FEATURE_IMAGE_CLASSIFICATION,
        input_model=VisionToolInput,
        raw_args={
            "image": image,
            "compartment_id": compartment_id,
            "max_results": max_results,
            "min_confidence": min_confidence,
            "options": options or {},
        },
        feature_factory=lambda args: image_classification_feature(max_results=args.max_results),
    )
