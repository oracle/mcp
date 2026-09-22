"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import base64
import os
from functools import partial
from pathlib import Path

import anyio
import pytest
from mcp.types import CallToolResult

from oracle.oci_vision_mcp_server.config.settings import get_resolved_config
from oracle.oci_vision_mcp_server.server import mcp


pytestmark = pytest.mark.live


def _live_tests_enabled() -> bool:
    return os.getenv("OCI_VISION_RUN_LIVE_TESTS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _require_live_environment(*names: str) -> None:
    if not _live_tests_enabled():
        pytest.skip("set OCI_VISION_RUN_LIVE_TESTS=true to run live OCI tests")
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        pytest.skip(f"missing live OCI test configuration: {', '.join(missing)}")


async def _call_tool(name: str, arguments: dict[str, object]) -> CallToolResult:
    result = await mcp.call_tool(name, arguments)
    assert result.isError is False, result.content
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "succeeded"
    return result


def test_live_oci_vision_analysis() -> None:
    _require_live_environment(
        "OCI_CONFIG_PROFILE",
        "OCI_REGION",
        "OCI_VISION_DEFAULT_COMPARTMENT_ID",
        "OCI_VISION_LIVE_TEST_IMAGE",
    )
    image_path = Path(os.environ["OCI_VISION_LIVE_TEST_IMAGE"]).expanduser().resolve()
    if not image_path.is_file():
        pytest.fail(f"OCI_VISION_LIVE_TEST_IMAGE is not a file: {image_path}")
    max_image_bytes = get_resolved_config().max_image_bytes
    if image_path.stat().st_size > max_image_bytes:
        pytest.fail(
            "OCI_VISION_LIVE_TEST_IMAGE exceeds MCP_MAX_IMAGE_BYTES: "
            f"{image_path.stat().st_size} > {max_image_bytes}"
        )

    encoded_image = base64.b64encode(image_path.read_bytes()).decode("ascii")
    anyio.run(
        partial(
            _call_tool,
            "classify_image",
            {
                "image": {"source_type": "base64", "data": encoded_image},
                "options": {"detail": "summary", "max_items": 1},
            },
        )
    )


def test_live_object_storage_ranged_list_is_read_only() -> None:
    _require_live_environment(
        "OCI_CONFIG_PROFILE",
        "OCI_REGION",
        "OCI_VISION_DEFAULT_COMPARTMENT_ID",
        "OCI_OBJECT_STORAGE_NAMESPACE",
        "OCI_OBJECT_STORAGE_BUCKET",
    )
    result = anyio.run(
        partial(
            _call_tool,
            "list_object_storage_objects",
            {
                "namespace": os.environ["OCI_OBJECT_STORAGE_NAMESPACE"],
                "bucket": os.environ["OCI_OBJECT_STORAGE_BUCKET"],
                "options": {
                    "detail": "summary",
                    "page_size": 10,
                    "start_index": 0,
                    "end_index": 10,
                },
            },
        )
    )
    assert result.structuredContent["start_index"] == 0
    assert result.structuredContent["end_index"] <= 10
