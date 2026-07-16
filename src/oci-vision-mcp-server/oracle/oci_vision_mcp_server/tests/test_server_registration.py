"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import oci
import pytest

from oracle.oci_vision_mcp_server.config.consts import (
    MAX_IMAGE_JOB_OBJECTS,
    MAX_OBJECT_STORAGE_BULK_FETCH_OBJECTS,
    MAX_OBJECT_STORAGE_BULK_UPLOAD_IMAGES,
    MAX_OBJECT_STORAGE_LIST_END_INDEX,
    MAX_OBJECT_STORAGE_LIST_PAGE_SIZE,
    MAX_PARALLEL_ANALYZE_ITEMS,
    MAX_PARALLEL_ANALYZE_MAX_PARALLEL,
    MAX_TOOL_MAX_ITEMS,
)
from oracle.oci_vision_mcp_server.config.schemas import ResponseDetail, VisionToolInput
from oracle.oci_vision_mcp_server.server import mcp
from oracle.oci_vision_mcp_server.tools.support_tools import get_analysis_result as analysis_result_tool
from oracle.oci_vision_mcp_server.tools.object_storage_tools import fetch_object_storage_object as fetch_tool
from oracle.oci_vision_mcp_server.tools.object_storage_tools import list_object_storage_objects as list_objects_tool
from oracle.oci_vision_mcp_server.tools.object_storage_tools import upload_image_to_object_storage as upload_tool
from oracle.oci_vision_mcp_server.tools.vision_api_tools import runner as analyze_tool


def _fastmcp_schema(tool) -> dict:
    return tool.parameters


def _fastmcp_text(result) -> str:
    return result.structured_content["content"][0]["text"]


def _fastmcp_structured(result) -> dict:
    return result.structured_content["structuredContent"]


def _fastmcp_is_error(result) -> bool:
    return result.structured_content["isError"]


@pytest.mark.anyio
async def test_fastmcp_registers_support_tools() -> None:
    tools = await mcp.list_tools()
    tools_by_name = {tool.name: tool for tool in tools}

    assert set(tools_by_name) == {
        "analyze_image",
        "parallel_analyze_image",
        "classify_image",
        "detect_objects",
        "detect_faces",
        "detect_text",
        "create_image_job",
        "get_image_job",
        "cancel_image_job",
        "upload_image_to_object_storage",
        "list_object_storage_objects",
        "fetch_object_storage_object",
        "get_config_status",
        "get_analysis_result",
    }
    analyze_tool_schema = _fastmcp_schema(tools_by_name["analyze_image"])
    parallel_tool_schema = _fastmcp_schema(tools_by_name["parallel_analyze_image"])
    assert sorted(analyze_tool_schema["properties"]) == [
        "compartment_id",
        "features",
        "image",
        "include_full_text",
        "max_results",
        "min_confidence",
        "options",
        "should_return_landmarks",
    ]
    assert sorted(parallel_tool_schema["properties"]) == [
        "compartment_id",
        "items",
        "max_parallel",
        "options",
    ]


@pytest.mark.anyio
async def test_fastmcp_schema_requires_image_source_type() -> None:
    tools = await mcp.list_tools()
    classify_tool = next(tool for tool in tools if tool.name == "classify_image")
    analyze_tool_schema = next(tool for tool in tools if tool.name == "analyze_image")
    create_job_tool = next(tool for tool in tools if tool.name == "create_image_job")
    parallel_tool = next(tool for tool in tools if tool.name == "parallel_analyze_image")
    upload_tool = next(tool for tool in tools if tool.name == "upload_image_to_object_storage")
    list_tool = next(tool for tool in tools if tool.name == "list_object_storage_objects")
    fetch_tool_schema = next(tool for tool in tools if tool.name == "fetch_object_storage_object")

    classify_schema = _fastmcp_schema(classify_tool)
    analyze_schema = _fastmcp_schema(analyze_tool_schema)
    create_job_schema = _fastmcp_schema(create_job_tool)
    parallel_schema = _fastmcp_schema(parallel_tool)
    upload_schema = _fastmcp_schema(upload_tool)
    list_schema = _fastmcp_schema(list_tool)
    fetch_schema = _fastmcp_schema(fetch_tool_schema)

    assert classify_schema["properties"]["image"]["properties"]["source_type"]["enum"] == [
        "base64",
        "file_path",
        "oci_object",
        "url",
    ]
    assert "source_type" in classify_schema["properties"]["image"]["required"]
    assert "url" in classify_schema["properties"]["image"]["properties"]
    assert analyze_schema["properties"]["image"]["properties"]["source_type"]["enum"] == [
        "base64",
        "file_path",
        "oci_object",
        "url",
    ]
    assert (
        analyze_schema["properties"]["options"]["anyOf"][0]["properties"]["max_items"][
            "maximum"
        ]
        == MAX_TOOL_MAX_ITEMS
    )
    assert "features" in analyze_schema["properties"]
    assert create_job_schema["properties"]["objects"]["items"]["properties"]["namespace"]
    assert create_job_schema["properties"]["objects"]["minItems"] == 1
    assert create_job_schema["properties"]["objects"]["maxItems"] == MAX_IMAGE_JOB_OBJECTS
    assert parallel_schema["properties"]["items"]["items"]["properties"]["image"]
    assert parallel_schema["properties"]["items"]["maxItems"] == MAX_PARALLEL_ANALYZE_ITEMS
    assert parallel_schema["properties"]["max_parallel"]["maximum"] == MAX_PARALLEL_ANALYZE_MAX_PARALLEL
    assert "features" in parallel_schema["properties"]["items"]["items"]["properties"]
    assert "file_path" in upload_schema["properties"]["image"]["anyOf"][0]["properties"]["source_type"]["enum"]
    assert "images" in upload_schema["properties"]
    upload_images_schema = next(
        item
        for item in upload_schema["properties"]["images"]["anyOf"]
        if item.get("type") == "array"
    )
    assert upload_images_schema["maxItems"] == MAX_OBJECT_STORAGE_BULK_UPLOAD_IMAGES
    assert "destination_prefix" in upload_schema["properties"]
    assert "source_type" in upload_schema["properties"]["image"]["anyOf"][0]["required"]
    assert "prefix" in list_schema["properties"]
    assert "bucket" in list_schema["properties"]
    list_options = list_schema["properties"]["options"]["anyOf"][0]["properties"]
    assert list_options["start_index"]["default"] == 0
    assert list_options["end_index"]["default"] == 10
    assert list_options["page_size"]["maximum"] == MAX_OBJECT_STORAGE_LIST_PAGE_SIZE
    assert list_options["end_index"]["maximum"] == MAX_OBJECT_STORAGE_LIST_END_INDEX
    assert "destination_path" in fetch_schema["properties"]
    assert "destination_dir" in fetch_schema["properties"]
    assert "object_names" in fetch_schema["properties"]
    fetch_object_names_schema = next(
        item
        for item in fetch_schema["properties"]["object_names"]["anyOf"]
        if item.get("type") == "array"
    )
    assert fetch_object_names_schema["maxItems"] == MAX_OBJECT_STORAGE_BULK_FETCH_OBJECTS


@pytest.mark.anyio
async def test_fastmcp_tool_descriptions_are_actionable_for_agents() -> None:
    tools = {tool.name: tool.description or "" for tool in await mcp.list_tools()}

    assert "one or more image features" in tools["analyze_image"]
    assert "direct results" in tools["parallel_analyze_image"]
    assert "parallel_analyze_image" in tools["create_image_job"]
    assert "Use detect_objects instead" in tools["classify_image"]
    assert "options.detail=boxes" in tools["detect_objects"]
    assert "does not perform face" in tools["detect_faces"].lower()
    assert "OCR" in tools["detect_text"]
    assert "Object Storage" in tools["create_image_job"]
    assert "image job OCID" in tools["get_image_job"]
    assert "confirm=true" in tools["cancel_image_job"]
    assert "source_type=file_path" in tools["upload_image_to_object_storage"]
    assert "batch/async Vision jobs" in tools["list_object_storage_objects"]
    assert "local copy" in tools["fetch_object_storage_object"]
    assert "env-var catalog" in tools["get_config_status"]
    assert "MCP request_id" in tools["get_analysis_result"]


@pytest.mark.anyio
async def test_fastmcp_returns_structured_tool_error_without_oci_call() -> None:
    result = await mcp.call_tool(
        "classify_image",
        {
            "image": {"source_type": "base64", "data": "not-base64!"},
            "compartment_id": "ocid1.compartment.oc1..example",
        },
    )

    structured = _fastmcp_structured(result)

    assert _fastmcp_is_error(result) is True
    assert _fastmcp_text(result) == "classify_image failed: Invalid base64 image data."
    assert structured["status"] == "failed"
    assert structured["tool"] == "classify_image"


@pytest.mark.anyio
async def test_fastmcp_requires_image_source_type() -> None:
    with pytest.raises(Exception) as exc_info:
        await mcp.call_tool(
            "classify_image",
            {
                "image": {"path": "data/38214.jpg"},
                "compartment_id": "ocid1.compartment.oc1..example",
            },
        )

    assert "image.source_type" in str(exc_info.value)


@pytest.mark.anyio
async def test_fastmcp_upload_requires_image_source_type() -> None:
    with pytest.raises(Exception) as exc_info:
        await mcp.call_tool(
            "upload_image_to_object_storage",
            {
                "image": {"path": "data/38214.jpg"},
                "destination": {
                    "namespace": "ns",
                    "bucket": "bucket",
                    "object_name": "images/38214.jpg",
                },
            },
        )

    assert "image.source_type" in str(exc_info.value)


@pytest.mark.anyio
async def test_get_config_status_returns_non_secret_config() -> None:
    result = await mcp.call_tool("get_config_status", {})

    structured = _fastmcp_structured(result)

    assert _fastmcp_is_error(result) is False
    assert structured["valid"] is True
    assert structured["missing_required_env_vars"] == []
    assert structured["errors"] == []
    assert structured["configuration_source"] == "process_environment"
    assert "profile" in structured["values"]
    assert "OCI_CONFIG_PROFILE" in structured["required_env_vars"]
    assert "environment variables" in structured["note"]


@pytest.mark.anyio
async def test_get_config_status_succeeds_with_missing_required_config(monkeypatch) -> None:
    monkeypatch.delenv("OCI_CONFIG_PROFILE", raising=False)
    monkeypatch.delenv("OCI_REGION", raising=False)
    monkeypatch.delenv("OCI_VISION_DEFAULT_COMPARTMENT_ID", raising=False)

    result = await mcp.call_tool("get_config_status", {})

    structured = _fastmcp_structured(result)

    assert _fastmcp_is_error(result) is False
    assert structured["valid"] is False
    assert structured["missing_required_env_vars"] == [
        "OCI_CONFIG_PROFILE",
        "OCI_REGION",
        "OCI_VISION_DEFAULT_COMPARTMENT_ID",
    ]
    assert len(structured["errors"]) == 3
    assert "profile=not configured" in _fastmcp_text(result)


def test_run_tool_checks_session_auth_before_oci_call(monkeypatch) -> None:
    events = []

    monkeypatch.setattr(analyze_tool, "ensure_session_auth", lambda: events.append("auth"))
    monkeypatch.setattr(
        analyze_tool,
        "create_vision_client",
        lambda **_kwargs: events.append("client") or object(),
    )
    monkeypatch.setattr(
        analyze_tool,
        "call_analyze_image",
        lambda *_args, **_kwargs: events.append("call") or SimpleNamespace(data={}),
    )

    result = analyze_tool.run_vision_tool(
        tool="classify_image",
        feature_type="IMAGE_CLASSIFICATION",
        input_model=VisionToolInput,
        raw_args={
            "image": {"source_type": "base64", "data": "iVBORw0KGgpleGFtcGxl"},
            "compartment_id": "ocid1.compartment.oc1..example",
        },
        feature_factory=lambda _args: object(),
    )

    assert result.isError is False
    assert events == ["auth", "client", "call"]


def test_run_analyze_image_tool_calls_one_combined_oci_request(monkeypatch) -> None:
    events = []
    captured = {}

    monkeypatch.setattr(analyze_tool, "generate_request_id", lambda: "ANALYZE_REQ")
    monkeypatch.setattr(analyze_tool, "ensure_session_auth", lambda: events.append("auth"))
    monkeypatch.setattr(
        analyze_tool,
        "create_vision_client",
        lambda **_kwargs: events.append("client") or object(),
    )

    def fake_analyze(*_args, **kwargs):
        events.append("call")
        captured.update(kwargs)
        return SimpleNamespace(data={}, headers={"opc-request-id": "OCI_REQ"})

    monkeypatch.setattr(analyze_tool, "call_analyze_image_features", fake_analyze)

    result = analyze_tool.run_analyze_image_tool(
        {
            "image": {"source_type": "base64", "data": "iVBORw0KGgpleGFtcGxl"},
            "compartment_id": "ocid1.compartment.oc1..example",
            "features": ["image_classification", "object_detection"],
        },
        tool="analyze_image",
    )

    assert result.isError is False
    assert events == ["auth", "client", "call"]
    assert len(captured["features"]) == 2
    assert captured["compartment_id"] == "ocid1.compartment.oc1..example"
    assert captured["request_id"] == "ANALYZE_REQ"


def test_create_image_job_uses_object_storage_output_defaults(monkeypatch) -> None:
    events = []
    captured = {}
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setattr(analyze_tool, "generate_request_id", lambda: "JOB_REQ")
    monkeypatch.setattr(analyze_tool, "ensure_session_auth", lambda: events.append("auth"))
    monkeypatch.setattr(
        analyze_tool,
        "create_vision_client",
        lambda **_kwargs: events.append("client") or object(),
    )

    def fake_create(*_args, **kwargs):
        events.append("call")
        captured.update(kwargs)
        return SimpleNamespace(
            data={"id": "ocid1.aivisionimagejob.oc1..example", "lifecycle_state": "ACCEPTED"},
            headers={"opc-request-id": "OCI_REQ", "opc-work-request-id": "WR_REQ"},
        )

    monkeypatch.setattr(analyze_tool, "call_create_image_job", fake_create)

    result = analyze_tool.run_create_image_job_tool(
        {
            "objects": [
                {
                    "namespace": "input_ns",
                    "bucket": "input_bucket",
                    "object_name": "images/sample.jpg",
                }
            ],
            "features": ["text_detection"],
        },
        tool="create_image_job",
    )

    assert result.isError is False
    assert events == ["auth", "client", "call"]
    assert captured["compartment_id"] == "ocid1.compartment.oc1..example"
    assert captured["output_location"].namespace_name == "configured_ns"
    assert captured["output_location"].bucket_name == "configured_bucket"
    assert captured["output_location"].prefix == "job_result"
    assert captured["request_id"] == "JOB_REQ"


def test_create_image_job_rejects_oversized_request_before_auth(monkeypatch) -> None:
    monkeypatch.setattr(
        analyze_tool,
        "ensure_session_auth",
        lambda: pytest.fail("auth should not run for an oversized request"),
    )

    result = analyze_tool.run_create_image_job_tool(
        {
            "objects": [
                {
                    "namespace": "input_ns",
                    "bucket": "input_bucket",
                    # This is just above the SDK-serialized 500 KB boundary but
                    # below the old compact-JSON estimate.
                    "object_name": f"images/{index}-{'x' * 417}.jpg",
                }
                for index in range(1000)
            ],
            "features": ["text_detection"],
            "output_location": {
                "namespace": "output_ns",
                "bucket": "output_bucket",
                "prefix": "results",
            },
        },
        tool="create_image_job",
    )

    assert result.isError is True
    assert "500 KB limit" in result.structuredContent["errors"][0]["message"]


def test_cancel_image_job_requires_explicit_confirmation(monkeypatch) -> None:
    monkeypatch.setattr(analyze_tool, "ensure_session_auth", lambda: pytest.fail("auth should not run"))

    result = analyze_tool.run_cancel_image_job_tool(
        {
            "job_id": "ocid1.aivisionimagejob.oc1..example",
            "confirm": False,
        },
        tool="cancel_image_job",
    )

    assert result.isError is True
    assert "confirm=true" in result.structuredContent["errors"][0]["message"]


def test_upload_tool_checks_session_auth_before_object_storage_call(monkeypatch, tmp_path) -> None:
    events = []
    captured = {}
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\nexample")
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setattr(upload_tool, "generate_request_id", lambda: "UPLOAD_REQ")
    monkeypatch.setattr(upload_tool, "ensure_session_auth", lambda: events.append("auth"))
    monkeypatch.setattr(
        upload_tool,
        "create_object_storage_client",
        lambda **_kwargs: events.append("client") or object(),
    )

    def fake_put(*_args, **kwargs):
        events.append("call")
        captured.update(kwargs)
        return SimpleNamespace(headers={"opc-request-id": "OCI_REQ", "etag": "ETAG"})

    monkeypatch.setattr(upload_tool, "call_put_object", fake_put)

    result = upload_tool.run_upload_tool(
        {
            "image": {"source_type": "file_path", "path": "image.png"},
            "destination": {
                "namespace": "ns",
                "bucket": "bucket",
                "object_name": "images/image.png",
            },
        }
    )

    assert result.isError is False
    assert events == ["auth", "client", "call"]
    assert captured["namespace"] == "ns"
    assert captured["bucket"] == "bucket"
    assert captured["object_name"] == "images/image.png"
    assert captured["content_length"] == image_path.stat().st_size
    assert captured["content_type"] == "image/png"
    assert captured["request_id"] == "UPLOAD_REQ"
    assert captured["overwrite"] is False
    assert result.structuredContent["request_id"] == "UPLOAD_REQ"
    assert result.structuredContent["mcp_request_id"] == "UPLOAD_REQ"
    assert "oci_request_id" not in result.structuredContent
    assert "oci_request_ids" not in result.structuredContent
    assert "raw_result_path" not in result.structuredContent
    assert result.structuredContent["etag"] == "ETAG"
    assert result.structuredContent["image_input"] == {
        "source_type": "oci_object",
        "data": None,
        "path": None,
        "oci_object": {
            "namespace": "ns",
            "bucket": "bucket",
            "object_name": "images/image.png",
        },
        "url": None,
    }
    tool_calls = json.loads((tmp_path / "results" / "tool_calls.json").read_text(encoding="utf-8"))
    assert tool_calls[-1]["mcp_request_id"] == "UPLOAD_REQ"
    assert tool_calls[-1]["oci_request_id"] == "OCI_REQ"
    assert tool_calls[-1]["tool"] == "upload_image_to_object_storage"
    assert tool_calls[-1]["image_path"] == "image.png"


def test_upload_tool_raw_detail_exposes_oci_request_id(monkeypatch, tmp_path) -> None:
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\nexample")
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setattr(upload_tool, "generate_request_id", lambda: "UPLOAD_REQ")
    monkeypatch.setattr(upload_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(upload_tool, "create_object_storage_client", lambda **_kwargs: object())
    monkeypatch.setattr(
        upload_tool,
        "call_put_object",
        lambda *_args, **_kwargs: SimpleNamespace(headers={"opc-request-id": "OCI_REQ", "etag": "ETAG"}),
    )

    result = upload_tool.run_upload_tool(
        {
            "image": {"source_type": "file_path", "path": "image.png"},
            "destination": {
                "namespace": "ns",
                "bucket": "bucket",
                "object_name": "images/image.png",
            },
            "options": {"detail": "raw"},
        }
    )

    assert result.isError is False
    assert result.structuredContent["request_id"] == "UPLOAD_REQ"
    assert result.structuredContent["oci_request_id"] == "OCI_REQ"
    assert result.structuredContent["oci_request_ids"] == ["OCI_REQ"]
    assert result.structuredContent["raw_result_path"].endswith(".raw.json")


def test_upload_tool_uses_configured_object_storage_defaults(monkeypatch, tmp_path) -> None:
    captured = {}
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\nexample")
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_OVERWRITE", "1")
    monkeypatch.setattr(upload_tool, "generate_request_id", lambda: "UPLOAD_REQ")
    monkeypatch.setattr(upload_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(upload_tool, "create_object_storage_client", lambda **_kwargs: object())

    def fake_put(*_args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(headers={"opc-request-id": "OCI_REQ"})

    monkeypatch.setattr(upload_tool, "call_put_object", fake_put)

    result = upload_tool.run_upload_tool(
        {
            "image": {"source_type": "file_path", "path": "image.png"},
        }
    )

    assert result.isError is False
    assert captured["namespace"] == "configured_ns"
    assert captured["bucket"] == "configured_bucket"
    assert captured["object_name"] == "image.png"
    assert captured["overwrite"] is True
    assert result.structuredContent["object"] == {
        "namespace": "configured_ns",
        "bucket": "configured_bucket",
        "object_name": "image.png",
    }


def test_upload_tool_uses_local_file_name_when_object_name_is_omitted(monkeypatch, tmp_path) -> None:
    captured = {}
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\nexample")
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setattr(upload_tool, "generate_request_id", lambda: "UPLOAD_REQ")
    monkeypatch.setattr(upload_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(upload_tool, "create_object_storage_client", lambda **_kwargs: object())

    def fake_put(*_args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(headers={"opc-request-id": "OCI_REQ"})

    monkeypatch.setattr(upload_tool, "call_put_object", fake_put)

    result = upload_tool.run_upload_tool(
        {
            "image": {"source_type": "file_path", "path": "image.png"},
        }
    )

    assert result.isError is False
    assert captured["object_name"] == "image.png"
    assert captured["overwrite"] is False


def test_upload_tool_requires_namespace_and_bucket_without_defaults(monkeypatch, tmp_path) -> None:
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\nexample")
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.delenv("OCI_OBJECT_STORAGE_NAMESPACE", raising=False)
    monkeypatch.delenv("OCI_OBJECT_STORAGE_BUCKET", raising=False)

    result = upload_tool.run_upload_tool(
        {
            "image": {"source_type": "file_path", "path": "image.png"},
        }
    )

    assert result.isError is True
    assert result.structuredContent["errors"][0]["code"] == "ValueError"
    assert "OCI_OBJECT_STORAGE_NAMESPACE" in result.structuredContent["errors"][0]["message"]


def test_list_objects_tool_pages_until_exhausted_and_uses_config_defaults(monkeypatch) -> None:
    events = []
    captured = []
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setattr(list_objects_tool, "generate_request_id", lambda: "LIST_REQ")
    monkeypatch.setattr(list_objects_tool, "ensure_session_auth", lambda: events.append("auth"))
    monkeypatch.setattr(
        list_objects_tool,
        "create_object_storage_client",
        lambda **_kwargs: events.append("client") or object(),
    )

    def fake_list(*_args, **kwargs):
        captured.append(kwargs)
        events.append("call")
        if kwargs["start"] is None:
            return SimpleNamespace(
                data=SimpleNamespace(
                    objects=[
                        SimpleNamespace(
                            name="a.jpg",
                            size=11,
                            time_modified=datetime(2026, 6, 17, tzinfo=timezone.utc),
                            etag="ETAG_A",
                            storage_tier="Standard",
                            archival_state=None,
                        )
                    ],
                    prefixes=[],
                    next_start_with="a.jpg",
                ),
                headers={"opc-request-id": "OCI_REQ_1"},
            )
        return SimpleNamespace(
            data=SimpleNamespace(
                objects=[SimpleNamespace(name="b.jpg", size=22)],
                prefixes=["nested/"],
                next_start_with=None,
            ),
            headers={"opc-request-id": "OCI_REQ_2"},
        )

    monkeypatch.setattr(list_objects_tool, "call_list_objects", fake_list)

    result = list_objects_tool.run_list_objects_tool({})

    assert result.isError is False
    assert events == ["auth", "client", "call", "call"]
    assert captured[0]["namespace"] == "configured_ns"
    assert captured[0]["bucket"] == "configured_bucket"
    assert captured[0]["prefix"] is None
    assert captured[0]["start"] is None
    assert captured[0]["limit"] == 11
    assert captured[1]["start"] == "a.jpg"
    assert result.structuredContent["request_id"] == "LIST_REQ"
    assert result.structuredContent["mcp_request_id"] == "LIST_REQ"
    assert "oci_request_id" not in result.structuredContent
    assert "oci_request_ids" not in result.structuredContent
    assert "raw_result_path" not in result.structuredContent
    assert result.structuredContent["object_count"] == 2
    assert result.structuredContent["prefix_count"] == 1
    assert result.structuredContent["start_index"] == 0
    assert result.structuredContent["end_index"] == 2
    assert result.structuredContent["has_more"] is False
    assert result.structuredContent["next_start_index"] is None
    assert result.structuredContent["objects"][0] == {
        "name": "a.jpg",
        "size": 11,
        "time_created": None,
        "time_modified": "2026-06-17T00:00:00+00:00",
        "etag": "ETAG_A",
        "md5": None,
        "storage_tier": "Standard",
        "archival_state": None,
    }
    assert result.structuredContent["prefixes"] == ["nested/"]


def test_list_objects_tool_allows_explicit_location_to_override_config(monkeypatch) -> None:
    captured = {}
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setattr(list_objects_tool, "generate_request_id", lambda: "LIST_REQ")
    monkeypatch.setattr(list_objects_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(list_objects_tool, "create_object_storage_client", lambda **_kwargs: object())

    def fake_list(*_args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            data=SimpleNamespace(objects=[], prefixes=[], next_start_with=None),
            headers={"opc-request-id": "OCI_REQ"},
        )

    monkeypatch.setattr(list_objects_tool, "call_list_objects", fake_list)

    result = list_objects_tool.run_list_objects_tool(
        {
            "namespace": "explicit_ns",
            "bucket": "explicit_bucket",
            "prefix": "images/",
            "delimiter": "/",
            "fields": ["name", "size"],
            "options": {"page_size": 25, "detail": "raw"},
        }
    )

    assert result.isError is False
    assert captured["namespace"] == "explicit_ns"
    assert captured["bucket"] == "explicit_bucket"
    assert captured["prefix"] == "images/"
    assert captured["delimiter"] == "/"
    assert captured["fields"] == "name,size"
    assert captured["limit"] == 11
    assert result.structuredContent["prefix"] == "images/"
    assert result.structuredContent["oci_request_id"] == "OCI_REQ"
    assert result.structuredContent["oci_request_ids"] == ["OCI_REQ"]
    assert result.structuredContent["raw_result_path"].endswith(".raw.json")


def test_list_objects_tool_requires_namespace_and_bucket_without_defaults(monkeypatch) -> None:
    monkeypatch.delenv("OCI_OBJECT_STORAGE_NAMESPACE", raising=False)
    monkeypatch.delenv("OCI_OBJECT_STORAGE_BUCKET", raising=False)

    result = list_objects_tool.run_list_objects_tool({})

    assert result.isError is True
    assert result.structuredContent["errors"][0]["code"] == "ValueError"
    assert "OCI_OBJECT_STORAGE_NAMESPACE" in result.structuredContent["errors"][0]["message"]


def test_list_objects_tool_maps_401_to_session_auth_error(monkeypatch) -> None:
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setattr(list_objects_tool, "generate_request_id", lambda: "LIST_REQ")
    monkeypatch.setattr(list_objects_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(list_objects_tool, "create_object_storage_client", lambda **_kwargs: object())

    def fake_list(*_args, **_kwargs):
        raise oci.exceptions.ServiceError(
            status=401,
            code="NotAuthenticated",
            headers={},
            message="session expired",
        )

    monkeypatch.setattr(list_objects_tool, "call_list_objects", fake_list)

    result = list_objects_tool.run_list_objects_tool({})

    assert result.isError is True
    assert result.structuredContent["errors"][0]["code"] == "OCI_SESSION_AUTH_REQUIRED"
    assert result.structuredContent["errors"][0]["retryable"] is True


def test_upload_tool_maps_existing_object_to_structured_error(monkeypatch, tmp_path) -> None:
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\nexample")
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setattr(upload_tool, "generate_request_id", lambda: "UPLOAD_REQ")
    monkeypatch.setattr(upload_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(upload_tool, "create_object_storage_client", lambda **_kwargs: object())

    def fake_put(*_args, **_kwargs):
        raise oci.exceptions.ServiceError(
            status=412,
            code="PreconditionFailed",
            headers={},
            message="object exists",
        )

    monkeypatch.setattr(upload_tool, "call_put_object", fake_put)

    result = upload_tool.run_upload_tool(
        {
            "image": {"source_type": "file_path", "path": "image.png"},
            "destination": {
                "namespace": "ns",
                "bucket": "bucket",
                "object_name": "images/image.png",
            },
        }
    )

    assert result.isError is True
    assert result.structuredContent["errors"][0]["code"] == "OBJECT_ALREADY_EXISTS"
    assert "overwrite=false" in result.structuredContent["errors"][0]["message"]


def test_run_tool_generates_request_id_and_stores_result(monkeypatch) -> None:
    captured = {}

    monkeypatch.setattr(analyze_tool, "generate_request_id", lambda: "GENERATED_REQ")
    monkeypatch.setattr(analyze_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(analyze_tool, "create_vision_client", lambda **_kwargs: object())

    def fake_call(*_args, **kwargs):
        captured["request_id"] = kwargs["request_id"]
        return SimpleNamespace(
            data={"labels": [{"name": "cat", "confidence": 0.99}], "errors": []},
            opc_request_id="OCI_REQ",
        )

    monkeypatch.setattr(analyze_tool, "call_analyze_image", fake_call)

    result = analyze_tool.run_vision_tool(
        tool="classify_image",
        feature_type="IMAGE_CLASSIFICATION",
        input_model=VisionToolInput,
        raw_args={
            "image": {"source_type": "base64", "data": "iVBORw0KGgpleGFtcGxl"},
            "compartment_id": "ocid1.compartment.oc1..example",
        },
        feature_factory=lambda _args: object(),
    )

    assert captured["request_id"] == "GENERATED_REQ"
    assert result.structuredContent["request_id"] == "GENERATED_REQ"
    assert result.structuredContent["results"]["summary"]["labels"] == [
        {"name": "cat", "confidence": 0.99}
    ]


def test_get_analysis_result_reads_local_store_and_direct_calls_are_not_cached(monkeypatch) -> None:
    call_count = 0
    oci_request_ids = []
    mcp_request_ids = iter(["MCP_REQ_1", "MCP_REQ_2"])

    monkeypatch.setattr(analyze_tool, "generate_request_id", lambda: next(mcp_request_ids))
    monkeypatch.setattr(analyze_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(analyze_tool, "create_vision_client", lambda **_kwargs: object())

    def fake_call(*_args, **kwargs):
        nonlocal call_count
        call_count += 1
        oci_request_ids.append(kwargs["request_id"])
        return SimpleNamespace(
            data={
                "image_objects": [
                    {"name": "Person", "confidence": 0.9},
                    {"name": "Laptop", "confidence": 0.8},
                ],
                "errors": [],
            },
            opc_request_id=kwargs["request_id"],
        )

    monkeypatch.setattr(analyze_tool, "call_analyze_image", fake_call)

    raw_args = {
        "image": {"source_type": "base64", "data": "iVBORw0KGgpleGFtcGxl"},
        "compartment_id": "ocid1.compartment.oc1..example",
        "options": {"request_id": "REQ_OBJECTS"},
    }
    first = analyze_tool.run_vision_tool(
        tool="detect_objects",
        feature_type="OBJECT_DETECTION",
        input_model=VisionToolInput,
        raw_args=raw_args,
        feature_factory=lambda _args: object(),
    )
    second = analyze_tool.run_vision_tool(
        tool="detect_objects",
        feature_type="OBJECT_DETECTION",
        input_model=VisionToolInput,
        raw_args=raw_args,
        feature_factory=lambda _args: object(),
    )
    stored = analysis_result_tool.get_analysis_result(
        request_id=first.structuredContent["request_id"],
        detail=ResponseDetail.STANDARD,
        max_items=10,
    )
    stored_raw = analysis_result_tool.get_analysis_result(
        request_id=first.structuredContent["request_id"],
        detail=ResponseDetail.RAW,
        max_items=10,
    )

    assert first.isError is False
    assert second.isError is False
    assert call_count == 2
    assert oci_request_ids == ["REQ_OBJECTS", "REQ_OBJECTS"]
    assert first.structuredContent["request_id"] == "MCP_REQ_1"
    assert second.structuredContent["request_id"] == "MCP_REQ_2"
    assert stored.isError is False
    assert stored.structuredContent["request_id"] == "MCP_REQ_1"
    assert stored.structuredContent["results"]["objects"] == [
        {"name": "Person", "confidence": 0.9},
        {"name": "Laptop", "confidence": 0.8},
    ]
    assert stored_raw.isError is False
    assert stored_raw.structuredContent["debug_metadata"]["oci_request_id"] == "REQ_OBJECTS"
