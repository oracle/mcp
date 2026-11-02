"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from mcp.types import CallToolResult

from ...config.consts import FEATURE_TEXT_DETECTION, TOOL_DETECT_TEXT
from ...config.schemas import ImageInput, TextToolInput, ToolOptions
from ...oci_mapper.vision_features import text_detection_feature
from ...runtime.mcp_app import mcp
from .runner import run_vision_tool


@mcp.tool(name=TOOL_DETECT_TEXT)
def detect_text(
    image: ImageInput,
    compartment_id: str | None = None,
    min_confidence: float | None = None,
    include_full_text: bool = True,
    options: ToolOptions | None = None,
) -> CallToolResult:
    """Run OCR on one image and return visible text.

    Call this when the user asks to read text, extract words, parse signage,
    inspect screenshots, or transcribe document-like image content. Provide
    image.source_type and exactly one carrier: file_path, base64, oci_object, or
    opt-in HTTPS url.
    min_confidence filters both OCR lines and their referenced words in
    normalized responses; use detail=raw to inspect the unfiltered OCI output.
    include_full_text=false keeps responses compact when only lines/samples are
    needed. options.detail=summary returns line counts and sample lines;
    standard returns OCR line details; boxes is not supported for this tool and
    falls back to standard with a warning; raw returns the raw OCI response.
    """
    return run_vision_tool(
        tool=TOOL_DETECT_TEXT,
        feature_type=FEATURE_TEXT_DETECTION,
        input_model=TextToolInput,
        raw_args={
            "image": image,
            "compartment_id": compartment_id,
            "min_confidence": min_confidence,
            "include_full_text": include_full_text,
            "options": options or {},
        },
        feature_factory=lambda _args: text_detection_feature(),
    )
