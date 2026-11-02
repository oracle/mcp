"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

MCP tool for multi-feature OCI Vision image analysis.
"""

from __future__ import annotations

from mcp.types import CallToolResult

from ...config.consts import TOOL_ANALYZE_IMAGE
from ...config.schemas import ImageAnalysisFeature, ImageInput, ToolOptions
from ...runtime.mcp_app import mcp
from .runner import run_analyze_image_tool


@mcp.tool(name=TOOL_ANALYZE_IMAGE)
def analyze_image(
    image: ImageInput,
    features: list[ImageAnalysisFeature] | None = None,
    compartment_id: str | None = None,
    max_results: int | None = None,
    min_confidence: float | None = None,
    should_return_landmarks: bool = False,
    include_full_text: bool = True,
    options: ToolOptions | None = None,
) -> CallToolResult:
    """Run OCI analyzeImage with one or more image features in one request.

    Use this when the user wants combined image understanding, such as labels
    plus objects plus OCR. `features` may include classification, object
    detection, face detection, and OCR. When omitted it runs all four modes.
    Provide `image.source_type` with exactly one carrier: `path`, `data`,
    `oci_object`, or opt-in HTTPS `url`. Use `options.detail` to choose
    `summary`, `standard`, `boxes`, or `raw`.
    """
    raw_args = {
        "image": image,
        "compartment_id": compartment_id,
        "max_results": max_results,
        "min_confidence": min_confidence,
        "should_return_landmarks": should_return_landmarks,
        "include_full_text": include_full_text,
        "options": options or {},
    }
    if features is not None:
        raw_args["features"] = features
    return run_analyze_image_tool(raw_args, tool=TOOL_ANALYZE_IMAGE)
