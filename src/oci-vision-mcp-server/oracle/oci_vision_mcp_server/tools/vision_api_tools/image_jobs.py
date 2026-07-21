"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

MCP tools for OCI Vision async image jobs.
"""

from __future__ import annotations

from typing import Annotated

from mcp.types import CallToolResult
from pydantic import Field

from ...config.consts import (
    MAX_IMAGE_JOB_OBJECTS,
    TOOL_CANCEL_IMAGE_JOB,
    TOOL_CREATE_IMAGE_JOB,
    TOOL_GET_IMAGE_JOB,
)
from ...config.schemas import (
    ImageAnalysisFeature,
    OciObjectInput,
    ToolOptions,
    VisionJobOutputInput,
)
from ...runtime.mcp_app import mcp
from .runner import (
    run_cancel_image_job_tool,
    run_create_image_job_tool,
    run_get_image_job_tool,
)


@mcp.tool(name=TOOL_CREATE_IMAGE_JOB)
def create_image_job(
    objects: Annotated[
        list[OciObjectInput],
        Field(min_length=1, max_length=MAX_IMAGE_JOB_OBJECTS),
    ],
    features: list[ImageAnalysisFeature] | None = None,
    output_location: VisionJobOutputInput | None = None,
    compartment_id: str | None = None,
    display_name: str | None = None,
    is_zip_output_enabled: bool = False,
    max_results: int | None = None,
    should_return_landmarks: bool = False,
    options: ToolOptions | None = None,
) -> CallToolResult:
    """Create an OCI Vision image job that writes results to Object Storage.

    Use this when images already live in OCI Object Storage and the user wants
    OCI Vision to save async/batch job output back to Object Storage. `objects`
    accepts 1 to 1,000 source objects. `features` may include classification,
    object detection, face detection, and OCR; omitted means all four. The
    complete request must also fit OCI Vision's 500 KB request-body limit.
    Results are written using `output_location`, or the configured output
    namespace/bucket with prefix `job_result` when no prefix is supplied. If the
    user wants the analyzed image results returned directly by MCP instead of
    saved to Object Storage, use `parallel_analyze_image`.
    """
    raw_args = {
        "objects": objects,
        "output_location": output_location,
        "compartment_id": compartment_id,
        "display_name": display_name,
        "is_zip_output_enabled": is_zip_output_enabled,
        "max_results": max_results,
        "should_return_landmarks": should_return_landmarks,
        "options": options or {},
    }
    if features is not None:
        raw_args["features"] = features
    return run_create_image_job_tool(raw_args, tool=TOOL_CREATE_IMAGE_JOB)


@mcp.tool(name=TOOL_GET_IMAGE_JOB)
def get_image_job(
    job_id: str,
    options: ToolOptions | None = None,
) -> CallToolResult:
    """Get the current state and metadata for one OCI Vision image job.

    Call this after `create_image_job` to check lifecycle state, output
    location, errors, and other job metadata. Use the image job OCID returned by
    the create call.
    """
    return run_get_image_job_tool(
        {
            "job_id": job_id,
            "options": options or {},
        },
        tool=TOOL_GET_IMAGE_JOB,
    )


@mcp.tool(name=TOOL_CANCEL_IMAGE_JOB)
def cancel_image_job(
    job_id: str,
    confirm: bool = False,
    options: ToolOptions | None = None,
) -> CallToolResult:
    """Cancel a running OCI Vision image job.

    Use this only when the user explicitly wants to stop a submitted image job.
    Set `confirm=true`; the tool rejects the call without that confirmation to
    avoid accidental cancellation.
    """
    return run_cancel_image_job_tool(
        {
            "job_id": job_id,
            "confirm": confirm,
            "options": options or {},
        },
        tool=TOOL_CANCEL_IMAGE_JOB,
    )
