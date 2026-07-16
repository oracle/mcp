"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from types import SimpleNamespace

import oci
import pytest

from oracle.oci_vision_mcp_server.tools.object_storage_tools import fetch_object_storage_object as fetch_tool
from oracle.oci_vision_mcp_server.tools.object_storage_tools import upload_image_to_object_storage as upload_tool


PNG_BYTES = bytes([137, 80, 78, 71, 13, 10, 26, 10]) + b"example"
JPEG_BYTES = b"\xff\xd8\xffexample"


def test_bulk_fetch_downloads_multiple_objects(monkeypatch, tmp_path) -> None:
    events = []
    calls = []
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_DOWNLOAD_DIR", str(tmp_path / "obj_results"))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setattr(fetch_tool, "generate_request_id", lambda: "BULK_FETCH_REQ")
    monkeypatch.setattr(fetch_tool, "ensure_session_auth", lambda: events.append("auth"))
    monkeypatch.setattr(
        fetch_tool,
        "create_object_storage_client",
        lambda **_kwargs: events.append("client") or object(),
    )

    def fake_get(*_args, **kwargs):
        events.append("call")
        calls.append(kwargs["object_name"])
        return SimpleNamespace(
            data=f"bytes:{kwargs['object_name']}".encode(),
            headers={
                "opc-request-id": f"OCI_{len(calls)}",
                "content-type": "image/jpeg",
                "content-length": "12",
                "etag": f"ETAG_{len(calls)}",
            },
        )

    monkeypatch.setattr(fetch_tool, "call_get_object", fake_get)

    result = fetch_tool.run_fetch_object_tool(
        {
            "object_names": ["images/one.jpg", "nested/two.jpg"],
            "destination_dir": "downloads",
        }
    )

    assert result.isError is False
    assert events == ["auth", "client", "call", "call"]
    assert calls == ["images/one.jpg", "nested/two.jpg"]
    assert (tmp_path / "obj_results" / "downloads" / "images" / "one.jpg").is_file()
    assert (tmp_path / "obj_results" / "downloads" / "nested" / "two.jpg").is_file()
    assert result.structuredContent["total_count"] == 2
    assert result.structuredContent["succeeded_count"] == 2
    assert result.structuredContent["failed_count"] == 0
    assert result.structuredContent["partial_failure"] is False
    assert [item["object"]["object_name"] for item in result.structuredContent["items"]] == [
        "images/one.jpg",
        "nested/two.jpg",
    ]
    assert "oci_request_id" not in result.structuredContent["items"][0]


def test_bulk_fetch_reports_partial_failure(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_DOWNLOAD_DIR", str(tmp_path / "obj_results"))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setattr(fetch_tool, "generate_request_id", lambda: "BULK_FETCH_REQ")
    monkeypatch.setattr(fetch_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(fetch_tool, "create_object_storage_client", lambda **_kwargs: object())

    def fake_get(*_args, **kwargs):
        if kwargs["object_name"] == "missing.jpg":
            raise oci.exceptions.ServiceError(status=404, code="NotFound", headers={}, message="missing")
        return SimpleNamespace(
            data=b"image-bytes",
            headers={
                "opc-request-id": "OCI_OK",
                "content-type": "image/jpeg",
                "content-length": "11",
            },
        )

    monkeypatch.setattr(fetch_tool, "call_get_object", fake_get)

    result = fetch_tool.run_fetch_object_tool({"object_names": ["ok.jpg", "missing.jpg"]})

    assert result.isError is False
    assert result.structuredContent["total_count"] == 2
    assert result.structuredContent["succeeded_count"] == 1
    assert result.structuredContent["failed_count"] == 1
    assert result.structuredContent["partial_failure"] is True
    failed = [item for item in result.structuredContent["items"] if item["status"] == "failed"]
    assert failed[0]["errors"][0]["code"] == "NotFound"


def test_bulk_fetch_rejects_unsafe_object_path(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OCI_OBJECT_STORAGE_DOWNLOAD_DIR", str(tmp_path / "obj_results"))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setattr(fetch_tool, "generate_request_id", lambda: "BULK_FETCH_REQ")
    monkeypatch.setattr(fetch_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(fetch_tool, "create_object_storage_client", lambda **_kwargs: object())
    monkeypatch.setattr(fetch_tool, "call_get_object", lambda *_args, **_kwargs: pytest.fail("OCI should not be called"))

    result = fetch_tool.run_fetch_object_tool({"object_names": ["../bad.jpg"]})

    assert result.isError is True
    assert result.structuredContent["failed_count"] == 1
    assert "safe relative" in result.structuredContent["items"][0]["errors"][0]["message"]


def test_bulk_fetch_rejects_intermediate_symlink_escape(monkeypatch, tmp_path) -> None:
    download_root = tmp_path / "obj_results"
    bulk_dir = download_root / "downloads"
    outside = tmp_path / "outside"
    bulk_dir.mkdir(parents=True)
    outside.mkdir()
    (bulk_dir / "images").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("OCI_OBJECT_STORAGE_DOWNLOAD_DIR", str(download_root))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "configured_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "configured_bucket")
    monkeypatch.setattr(fetch_tool, "generate_request_id", lambda: "BULK_FETCH_REQ")
    monkeypatch.setattr(fetch_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(fetch_tool, "create_object_storage_client", lambda **_kwargs: object())
    monkeypatch.setattr(
        fetch_tool,
        "call_get_object",
        lambda *_args, **_kwargs: pytest.fail("OCI should not be called"),
    )

    result = fetch_tool.run_fetch_object_tool(
        {
            "object_names": ["images/escaped.jpg"],
            "destination_dir": "downloads",
        }
    )

    assert result.isError is True
    assert "symbolic links" in result.structuredContent["items"][0]["errors"][0]["message"]
    assert not (outside / "escaped.jpg").exists()


def test_bulk_upload_uploads_multiple_images_to_prefix(monkeypatch, tmp_path) -> None:
    events = []
    calls = []
    (tmp_path / "one.png").write_bytes(PNG_BYTES)
    (tmp_path / "two.jpg").write_bytes(JPEG_BYTES)
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setattr(upload_tool, "generate_request_id", lambda: "BULK_UPLOAD_REQ")
    monkeypatch.setattr(upload_tool, "ensure_session_auth", lambda: events.append("auth"))
    monkeypatch.setattr(
        upload_tool,
        "create_object_storage_client",
        lambda **_kwargs: events.append("client") or object(),
    )

    def fake_put(*_args, **kwargs):
        events.append("call")
        calls.append(kwargs["object_name"])
        return SimpleNamespace(headers={"opc-request-id": f"OCI_{len(calls)}", "etag": f"ETAG_{len(calls)}"})

    monkeypatch.setattr(upload_tool, "call_put_object", fake_put)

    result = upload_tool.run_upload_tool(
        {
            "images": [
                {"source_type": "file_path", "path": "one.png"},
                {"source_type": "file_path", "path": "two.jpg"},
            ],
            "destination": {"namespace": "ns", "bucket": "bucket"},
            "destination_prefix": "incoming",
        }
    )

    assert result.isError is False
    assert events == ["auth", "client", "call", "call"]
    assert calls == ["incoming/one.png", "incoming/two.jpg"]
    assert result.structuredContent["total_count"] == 2
    assert result.structuredContent["succeeded_count"] == 2
    assert result.structuredContent["failed_count"] == 0
    assert [item["object"]["object_name"] for item in result.structuredContent["items"]] == calls
    assert "oci_request_id" not in result.structuredContent["items"][0]


def test_bulk_upload_reports_partial_failure(monkeypatch, tmp_path) -> None:
    (tmp_path / "one.png").write_bytes(PNG_BYTES)
    (tmp_path / "two.png").write_bytes(PNG_BYTES)
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setattr(upload_tool, "generate_request_id", lambda: "BULK_UPLOAD_REQ")
    monkeypatch.setattr(upload_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(upload_tool, "create_object_storage_client", lambda **_kwargs: object())

    def fake_put(*_args, **kwargs):
        if kwargs["object_name"] == "incoming/two.png":
            raise oci.exceptions.ServiceError(status=412, code="PreconditionFailed", headers={}, message="exists")
        return SimpleNamespace(headers={"opc-request-id": "OCI_OK", "etag": "ETAG"})

    monkeypatch.setattr(upload_tool, "call_put_object", fake_put)

    result = upload_tool.run_upload_tool(
        {
            "images": [
                {"source_type": "file_path", "path": "one.png"},
                {"source_type": "file_path", "path": "two.png"},
            ],
            "destination": {"namespace": "ns", "bucket": "bucket"},
            "destination_prefix": "incoming",
        }
    )

    assert result.isError is False
    assert result.structuredContent["succeeded_count"] == 1
    assert result.structuredContent["failed_count"] == 1
    assert result.structuredContent["partial_failure"] is True
    failed = [item for item in result.structuredContent["items"] if item["status"] == "failed"]
    assert failed[0]["errors"][0]["code"] == "OBJECT_ALREADY_EXISTS"


def test_bulk_upload_rejects_duplicate_target_names_before_auth(monkeypatch, tmp_path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "same.png").write_bytes(PNG_BYTES)
    (tmp_path / "b" / "same.png").write_bytes(PNG_BYTES)
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setattr(upload_tool, "generate_request_id", lambda: "BULK_UPLOAD_REQ")
    monkeypatch.setattr(upload_tool, "ensure_session_auth", lambda: pytest.fail("auth should not run"))

    result = upload_tool.run_upload_tool(
        {
            "images": [
                {"source_type": "file_path", "path": "a/same.png"},
                {"source_type": "file_path", "path": "b/same.png"},
            ],
            "destination": {"namespace": "ns", "bucket": "bucket"},
            "destination_prefix": "incoming",
        }
    )

    assert result.isError is True
    assert "must be unique" in result.structuredContent["errors"][0]["message"]


def test_upload_rejects_content_type_that_does_not_match_bytes(monkeypatch, tmp_path) -> None:
    (tmp_path / "image.png").write_bytes(PNG_BYTES)
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setattr(upload_tool, "generate_request_id", lambda: "UPLOAD_REQ")
    monkeypatch.setattr(upload_tool, "ensure_session_auth", lambda: pytest.fail("auth should not run"))

    result = upload_tool.run_upload_tool(
        {
            "image": {"source_type": "file_path", "path": "image.png"},
            "destination": {"namespace": "ns", "bucket": "bucket"},
            "content_type": "image/jpeg",
        }
    )

    assert result.isError is True
    assert "does not match detected image type" in result.structuredContent["errors"][0]["message"]
