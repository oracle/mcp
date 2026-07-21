"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from types import SimpleNamespace

import oci

from oracle.oci_vision_mcp_server.io.result_store import safe_request_key
from oracle.oci_vision_mcp_server.tools.object_storage_tools import fetch_object_storage_object as fetch_tool


def test_fetch_object_storage_object_downloads_under_default_download_dir(monkeypatch, tmp_path) -> None:
    events = []
    captured = {}
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_DOWNLOAD_DIR", str(tmp_path / "obj_results"))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setattr(fetch_tool, "generate_request_id", lambda: "FETCH_REQ")
    monkeypatch.setattr(fetch_tool, "ensure_session_auth", lambda: events.append("auth"))
    monkeypatch.setattr(
        fetch_tool,
        "create_object_storage_client",
        lambda **_kwargs: events.append("client") or object(),
    )

    def fake_get(*_args, **kwargs):
        captured.update(kwargs)
        events.append("call")
        return SimpleNamespace(
            data=b"image-bytes",
            headers={
                "opc-request-id": "OCI_REQ",
                "content-type": "image/jpeg",
                "content-length": "11",
                "etag": "ETAG",
            },
        )

    monkeypatch.setattr(fetch_tool, "call_get_object", fake_get)

    result = fetch_tool.run_fetch_object_tool({"object_name": "images/sample.jpg"})

    expected_name = f"{safe_request_key('FETCH_REQ')[:12]}-sample.jpg"
    downloaded = tmp_path / "obj_results" / expected_name
    assert result.isError is False
    assert events == ["auth", "client", "call"]
    assert captured["namespace"] == "configured_ns"
    assert captured["bucket"] == "configured_bucket"
    assert captured["object_name"] == "images/sample.jpg"
    assert downloaded.read_bytes() == b"image-bytes"
    assert result.structuredContent["file_path"] == f"obj_results/{expected_name}"
    assert result.structuredContent["image_input"] == {
        "source_type": "file_path",
        "data": None,
        "path": f"obj_results/{expected_name}",
        "oci_object": None,
        "url": None,
    }
    assert "oci_request_id" not in result.structuredContent
    assert "raw_result_path" not in result.structuredContent


def test_fetch_object_storage_object_rejects_destination_escape(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setattr(fetch_tool, "generate_request_id", lambda: "FETCH_REQ")

    result = fetch_tool.run_fetch_object_tool(
        {
            "object_name": "images/sample.jpg",
            "destination_path": "../sample.jpg",
        }
    )

    assert result.isError is True
    assert "destination_path must stay under" in result.structuredContent["errors"][0]["message"]


def test_fetch_object_storage_object_allows_download_dir_outside_image_base(monkeypatch, tmp_path) -> None:
    image_base = tmp_path / "images"
    download_dir = tmp_path / "outside_downloads"
    image_base.mkdir()
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(image_base))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_DOWNLOAD_DIR", str(download_dir))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
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
                "content-type": "image/jpeg",
                "content-length": "11",
            },
        ),
    )

    result = fetch_tool.run_fetch_object_tool({"object_name": "images/sample.jpg"})

    assert result.isError is False
    assert result.structuredContent["file_path"].startswith(str(download_dir))
    assert result.structuredContent["image_input"] is None


def test_fetch_object_storage_object_maps_401_to_session_auth_error(monkeypatch) -> None:
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setattr(fetch_tool, "generate_request_id", lambda: "FETCH_REQ")
    monkeypatch.setattr(fetch_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(fetch_tool, "create_object_storage_client", lambda **_kwargs: object())

    def fake_get(*_args, **_kwargs):
        raise oci.exceptions.ServiceError(
            status=401,
            code="NotAuthenticated",
            headers={},
            message="session expired",
        )

    monkeypatch.setattr(fetch_tool, "call_get_object", fake_get)

    result = fetch_tool.run_fetch_object_tool({"object_name": "images/sample.jpg"})

    assert result.isError is True
    assert result.structuredContent["errors"][0]["code"] == "OCI_SESSION_AUTH_REQUIRED"
    assert result.structuredContent["errors"][0]["retryable"] is True
