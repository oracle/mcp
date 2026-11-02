"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import pytest

from oracle.oci_vision_mcp_server.prompts import vision_workflows
from oracle.oci_vision_mcp_server.server import mcp


def _prompt_text(messages: list[dict[str, str]]) -> str:
    return messages[0]["content"]


@pytest.mark.anyio
async def test_fastmcp_registers_workflow_prompts() -> None:
    prompts = await mcp.list_prompts()

    assert {prompt.name for prompt in prompts} == {
        "interpret_object_storage_url",
        "resolve_detection_confusion",
        "debug_compartment_region_error",
        "image_analysis_workflow",
    }


@pytest.mark.anyio
async def test_object_storage_url_prompt_uses_redacted_examples() -> None:
    text = _prompt_text(vision_workflows.interpret_object_storage_url())

    assert "objectstorage.<region>.oraclecloud.com" in text
    assert "/n/<namespace>" in text
    assert "/b/<bucket>" in text
    assert "%2F" in text
    assert "signed-token" in text


@pytest.mark.anyio
async def test_detection_confusion_prompt_guides_detail_modes() -> None:
    text = _prompt_text(vision_workflows.resolve_detection_confusion())

    assert 'options.detail="boxes"' in text
    assert 'options.detail="raw"' in text
    assert "bounding box coordinates" in text
    assert "Do not merge counts" in text


@pytest.mark.anyio
async def test_compartment_region_prompt_guides_mismatch_debugging() -> None:
    text = _prompt_text(vision_workflows.debug_compartment_region_error())

    assert "Object Storage URL region" in text
    assert "OCI_REGION" in text
    assert "OCI_VISION_DEFAULT_COMPARTMENT_ID" in text
    assert "OCI_CONFIG_PROFILE" in text


@pytest.mark.anyio
async def test_image_analysis_prompt_combines_sync_async_and_reporting() -> None:
    text = _prompt_text(vision_workflows.image_analysis_workflow())

    assert "Sync flow" in text
    assert "Async flow" in text
    assert "Report generation flow" in text
    assert "list_object_storage_objects" in text
    assert "create_image_job" in text
    assert "get_image_job" in text
    assert "below about 50" in text
