"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from types import SimpleNamespace

from oracle.oci_vision_mcp_server.config.schemas import VisionToolInput
from oracle.oci_vision_mcp_server.io.result_store import ResultStoreWriteError
from oracle.oci_vision_mcp_server.tools.object_storage_tools import (
    fetch_object_storage_object as fetch_tool,
)
from oracle.oci_vision_mcp_server.tools.object_storage_tools import (
    list_object_storage_objects as list_tool,
)
from oracle.oci_vision_mcp_server.tools.object_storage_tools import (
    upload_image_to_object_storage as upload_tool,
)
from oracle.oci_vision_mcp_server.tools.vision_api_tools import parallel_analyze_image as parallel_tool
from oracle.oci_vision_mcp_server.tools.vision_api_tools import runner as vision_runner


PNG_BYTES = b"\x89PNG\r\n\x1a\nexample"


def _fail_store(**_kwargs):
    raise ResultStoreWriteError("disk full")


def _assert_persistence_warning(result) -> None:
    assert result.isError is False
    assert result.structuredContent["status"] == "succeeded"
    assert result.structuredContent["warnings"] == [
        {
            "code": "RESULT_PERSISTENCE_FAILED",
            "message": (
                "The operation completed, but its local raw result or index could not "
                "be stored. Do not retry the external operation solely because of this warning."
            ),
        }
    ]


def test_vision_success_survives_result_persistence_failure(monkeypatch) -> None:
    monkeypatch.setattr(vision_runner, "generate_request_id", lambda: "VISION_REQ")
    monkeypatch.setattr(vision_runner, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(vision_runner, "create_vision_client", lambda **_kwargs: object())
    monkeypatch.setattr(
        vision_runner,
        "call_analyze_image",
        lambda *_args, **_kwargs: SimpleNamespace(
            data={"labels": [{"name": "Document", "confidence": 0.99}], "errors": []},
            opc_request_id="OCI_REQ",
        ),
    )
    monkeypatch.setattr(vision_runner, "store_analysis_result", _fail_store)

    result = vision_runner.run_vision_tool(
        tool="classify_image",
        feature_type="IMAGE_CLASSIFICATION",
        input_model=VisionToolInput,
        raw_args={
            "image": {"source_type": "base64", "data": "iVBORw0KGgpleGFtcGxl"},
        },
        feature_factory=lambda _args: object(),
    )

    _assert_persistence_warning(result)
    assert result.structuredContent["results"]["summary"]["labels"][0]["name"] == "Document"


def test_parallel_success_survives_result_persistence_failure(monkeypatch) -> None:
    monkeypatch.setattr(parallel_tool, "generate_request_id", lambda: "BATCH_REQ")
    monkeypatch.setattr(parallel_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(parallel_tool, "create_vision_client", lambda **_kwargs: object())
    monkeypatch.setattr(
        parallel_tool,
        "call_analyze_image_features",
        lambda *_args, **_kwargs: SimpleNamespace(data={"labels": [], "errors": []}),
    )
    monkeypatch.setattr(parallel_tool, "store_tool_result", _fail_store)

    result = parallel_tool.run_parallel_analyze_image_tool(
        {
            "items": [
                {
                    "image": {
                        "source_type": "base64",
                        "data": "iVBORw0KGgpleGFtcGxl",
                    },
                    "features": ["image_classification"],
                }
            ]
        }
    )

    _assert_persistence_warning(result)
    assert result.structuredContent["results"]["summary"]["succeeded_count"] == 1


def test_upload_success_survives_result_persistence_failure(monkeypatch, tmp_path) -> None:
    (tmp_path / "image.png").write_bytes(PNG_BYTES)
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setattr(upload_tool, "generate_request_id", lambda: "UPLOAD_REQ")
    monkeypatch.setattr(upload_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(upload_tool, "create_object_storage_client", lambda **_kwargs: object())
    monkeypatch.setattr(
        upload_tool,
        "call_put_object",
        lambda *_args, **_kwargs: SimpleNamespace(headers={"opc-request-id": "OCI_REQ"}),
    )
    monkeypatch.setattr(upload_tool, "store_tool_result", _fail_store)

    result = upload_tool.run_upload_tool(
        {
            "image": {"source_type": "file_path", "path": "image.png"},
            "destination": {
                "namespace": "namespace",
                "bucket": "bucket",
                "object_name": "image.png",
            },
            "options": {"detail": "raw"},
        }
    )

    _assert_persistence_warning(result)
    assert result.structuredContent["object"]["object_name"] == "image.png"
    assert result.structuredContent["raw_result_available"] is True
    assert result.structuredContent["raw_result_inline"]["object"]["object_name"] == (
        "image.png"
    )
    assert result.structuredContent["raw_result_path"] is None


def test_list_success_survives_result_persistence_failure(monkeypatch) -> None:
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "namespace")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "bucket")
    monkeypatch.setattr(list_tool, "generate_request_id", lambda: "LIST_REQ")
    monkeypatch.setattr(list_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(list_tool, "create_object_storage_client", lambda **_kwargs: object())
    monkeypatch.setattr(
        list_tool,
        "call_list_objects",
        lambda *_args, **_kwargs: SimpleNamespace(
            data=SimpleNamespace(objects=[], prefixes=[], next_start_with=None),
            headers={"opc-request-id": "OCI_REQ"},
        ),
    )
    monkeypatch.setattr(list_tool, "store_tool_result", _fail_store)

    result = list_tool.run_list_objects_tool({})

    _assert_persistence_warning(result)
    assert result.structuredContent["objects"] == []


def test_fetch_success_survives_result_persistence_failure(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_DOWNLOAD_DIR", str(tmp_path / "downloads"))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "namespace")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "bucket")
    monkeypatch.setattr(fetch_tool, "generate_request_id", lambda: "FETCH_REQ")
    monkeypatch.setattr(fetch_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(fetch_tool, "create_object_storage_client", lambda **_kwargs: object())
    monkeypatch.setattr(
        fetch_tool,
        "call_get_object",
        lambda *_args, **_kwargs: SimpleNamespace(
            data=b"image-bytes",
            headers={
                "opc-request-id": "OCI_REQ",
                "content-length": "11",
                "content-type": "image/jpeg",
            },
        ),
    )
    monkeypatch.setattr(fetch_tool, "store_tool_result", _fail_store)

    result = fetch_tool.run_fetch_object_tool({"object_name": "image.jpg"})

    _assert_persistence_warning(result)
    assert result.structuredContent["file_path"].endswith("-image.jpg")
