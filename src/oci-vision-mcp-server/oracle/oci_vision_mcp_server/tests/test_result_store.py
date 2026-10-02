"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import json

import pytest

from oracle.oci_vision_mcp_server.io.result_store import (
    ResultStoreError,
    generate_request_id,
    load_analysis_result,
    raw_payload_reference,
    safe_request_key,
    store_analysis_result,
    store_tool_result,
)
from oracle.oci_vision_mcp_server.io import result_store
from oracle.oci_vision_mcp_server.config.schemas import ResponseDetail
from oracle.oci_vision_mcp_server.tools.support_tools import get_analysis_result as get_result_tool


def test_generate_request_id_uses_local_mcp_prefix() -> None:
    assert generate_request_id().startswith("mcp_")


def test_result_store_uses_hashed_filename_and_loads_by_request_id(tmp_path) -> None:
    request_id = "../REQ123"

    metadata = store_analysis_result(
        result_store_dir=str(tmp_path),
        request_id=request_id,
        tool="detect_objects",
        feature_type="OBJECT_DETECTION",
        region="us-ashburn-1",
        compartment_id="ocid1.compartment.oc1..example",
        detail_options={"detail": "summary"},
        raw_result={"image_objects": []},
        oci_request_id="OCI_REQ",
        model_versions={"object_detection": "1.0"},
    )

    key = safe_request_key(request_id)
    assert (tmp_path / f"{key}.raw.json").is_file()
    assert (tmp_path / f"{key}.meta.json").is_file()
    assert "../REQ123" not in metadata["raw_result_path"]

    raw_result, loaded_metadata = load_analysis_result(
        result_store_dir=str(tmp_path),
        request_id=request_id,
        ttl_seconds=60,
    )

    assert raw_result == {"image_objects": []}
    assert loaded_metadata["request_id"] == request_id
    assert loaded_metadata["mcp_request_id"] == request_id
    assert loaded_metadata["oci_request_id"] == "OCI_REQ"
    assert loaded_metadata["oci_request_ids"] == ["OCI_REQ"]
    tool_calls = json.loads((tmp_path / "tool_calls.json").read_text(encoding="utf-8"))
    assert tool_calls == [
        {
            "created_at": loaded_metadata["created_at"],
            "mcp_request_id": request_id,
            "request_id": request_id,
            "client_request_id": None,
            "oci_request_id": "OCI_REQ",
            "oci_request_ids": ["OCI_REQ"],
            "tool": "detect_objects",
            "provider": "oci_vision",
            "image_path": None,
            "image_object_name": None,
            "raw_result_path": loaded_metadata["raw_result_path"],
            "metadata_path": loaded_metadata["metadata_path"],
        }
    ]
    assert not list(tmp_path.glob(".*.tmp"))


def test_result_store_rejects_mismatched_metadata_request_id(tmp_path) -> None:
    request_id = "REQ123"
    store_analysis_result(
        result_store_dir=str(tmp_path),
        request_id=request_id,
        tool="detect_objects",
        feature_type="OBJECT_DETECTION",
        region="us-ashburn-1",
        compartment_id="ocid1.compartment.oc1..example",
        detail_options={"detail": "summary"},
        raw_result={"image_objects": []},
        oci_request_id="OCI_REQ",
        model_versions={"object_detection": "1.0"},
    )

    meta_path = tmp_path / f"{safe_request_key(request_id)}.meta.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    metadata["request_id"] = "OTHER_REQ"
    meta_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ResultStoreError, match="metadata is invalid"):
        load_analysis_result(
            result_store_dir=str(tmp_path),
            request_id=request_id,
            ttl_seconds=60,
        )


def test_result_store_rejects_missing_expired_and_invalid_results(tmp_path) -> None:
    with pytest.raises(ResultStoreError, match="No stored OCI Vision result"):
        load_analysis_result(result_store_dir=str(tmp_path), request_id="missing", ttl_seconds=60)

    request_id = "REQ_EXPIRED"
    store_analysis_result(
        result_store_dir=str(tmp_path),
        request_id=request_id,
        tool="detect_objects",
        feature_type="OBJECT_DETECTION",
        region="us-ashburn-1",
        compartment_id="ocid1.compartment.oc1..example",
        detail_options={"detail": "summary"},
        raw_result={"image_objects": []},
        oci_request_id=None,
        model_versions={},
    )
    meta_path = tmp_path / f"{safe_request_key(request_id)}.meta.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    metadata["created_at"] = "not-a-date"
    meta_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ResultStoreError, match="expired"):
        load_analysis_result(result_store_dir=str(tmp_path), request_id=request_id, ttl_seconds=60)

    raw_path = tmp_path / f"{safe_request_key(request_id)}.raw.json"
    metadata["created_at"] = "2099-01-01T00:00:00+00:00"
    meta_path.write_text(json.dumps(metadata), encoding="utf-8")
    raw_path.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(ResultStoreError, match="invalid"):
        load_analysis_result(result_store_dir=str(tmp_path), request_id=request_id, ttl_seconds=60)


def test_raw_payload_reference_inlines_small_payloads_and_links_large_payloads() -> None:
    small = raw_payload_reference(raw_result={"ok": True}, raw_path="/tmp/raw.json", max_inline_response_bytes=100)
    large = raw_payload_reference(
        raw_result={"payload": "x" * 200},
        raw_path="/tmp/raw.json",
        max_inline_response_bytes=10,
    )

    assert small["raw_result_inline"] == {"ok": True}
    assert large["raw_result_inline"] is None
    assert large["raw_result_path"] == "/tmp/raw.json"
    unavailable = raw_payload_reference(
        raw_result={"payload": "x" * 200},
        raw_path=None,
        max_inline_response_bytes=10,
    )
    assert unavailable == {
        "raw_result_available": False,
        "raw_result_inline": None,
        "raw_result_path": None,
    }


def test_store_tool_result_ignores_corrupt_index_and_records_object_name(tmp_path) -> None:
    (tmp_path / "tool_calls.json").write_text("not-json", encoding="utf-8")

    metadata = store_tool_result(
        result_store_dir=str(tmp_path),
        mcp_request_id="REQ_OBJECT",
        tool="upload_image_to_object_storage",
        provider="oci_object_storage",
        raw_result={"object": {"object_name": "images/a.png"}},
        oci_request_id="OCI_REQ",
        oci_request_ids=["OCI_REQ"],
        region="us-ashburn-1",
        object_storage_info={"object_name": "images/a.png"},
    )

    tool_calls = json.loads((tmp_path / "tool_calls.json").read_text(encoding="utf-8"))
    assert metadata["provider"] == "oci_object_storage"
    assert tool_calls == [
        {
            "created_at": metadata["created_at"],
            "mcp_request_id": "REQ_OBJECT",
            "request_id": "REQ_OBJECT",
            "client_request_id": None,
            "oci_request_id": "OCI_REQ",
            "oci_request_ids": ["OCI_REQ"],
            "tool": "upload_image_to_object_storage",
            "provider": "oci_object_storage",
            "image_path": None,
            "image_object_name": "images/a.png",
            "raw_result_path": metadata["raw_result_path"],
            "metadata_path": metadata["metadata_path"],
        }
    ]


def test_get_analysis_result_rerenders_stored_object_storage_results(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OCI_VISION_RESULT_STORE_DIR", str(tmp_path))
    store_tool_result(
        result_store_dir=str(tmp_path),
        mcp_request_id="REQ_OBJECT",
        tool="list_object_storage_objects",
        provider="oci_object_storage",
        raw_result={
            "object_count": 1,
            "headers": {"opc-request-id": "OCI_REQ"},
            "oci_request_id": "OCI_REQ",
        },
        oci_request_id="OCI_REQ",
        oci_request_ids=["OCI_REQ"],
        region="us-ashburn-1",
    )

    summary = get_result_tool.get_analysis_result("REQ_OBJECT")
    raw = get_result_tool.get_analysis_result("REQ_OBJECT", detail=ResponseDetail.RAW)

    assert summary.isError is False
    assert summary.structuredContent["results"] == {"object_count": 1}
    assert "oci_request_id" not in summary.structuredContent["results"]
    assert raw.structuredContent["oci_request_id"] == "OCI_REQ"
    assert raw.structuredContent["raw_result"]["object_count"] == 1


def test_get_analysis_result_returns_structured_errors(monkeypatch) -> None:
    missing = get_result_tool.get_analysis_result("missing")
    assert missing.isError is True
    assert missing.structuredContent["errors"][0]["code"] == "REQUEST_RESULT_NOT_FOUND"

    monkeypatch.setattr(
        get_result_tool,
        "load_analysis_result",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    failed = get_result_tool.get_analysis_result("REQ")

    assert failed.isError is True
    assert failed.structuredContent["errors"][0]["code"] == "RuntimeError"


def test_result_store_rebuilds_indexes_and_inferrs_metadata_defaults(tmp_path) -> None:
    valid = store_tool_result(
        result_store_dir=str(tmp_path),
        mcp_request_id="REQ_VALID",
        tool="parallel_analyze_image",
        provider="oci_vision",
        raw_result={
            "items": [
                {"feature_types": ["TEXT_DETECTION", "OBJECT_DETECTION"]},
                {"feature_types": ["TEXT_DETECTION"]},
            ],
            "succeeded_count": 1,
            "failed_count": 1,
        },
        oci_request_id=None,
        oci_request_ids=[],
        region="us-phoenix-1",
        feature_type="parallel_analyze_image",
    )
    store_tool_result(
        result_store_dir=str(tmp_path),
        mcp_request_id="REQ_JOB",
        tool="create_image_job",
        provider="oci_vision",
        raw_result={"errors": [{"message": "bad"}]},
        oci_request_id=None,
        oci_request_ids=[],
        region="us-phoenix-1",
        feature_type="image_job",
    )
    (tmp_path / "tool_calls.json").write_text('{"not": "a-list"}', encoding="utf-8")

    rebuilt = result_store._load_or_rebuild_index(tmp_path, tmp_path / "tool_calls.json")
    raw_result, loaded = load_analysis_result(
        result_store_dir=str(tmp_path),
        request_id="REQ_VALID",
        ttl_seconds=60,
    )
    compat = result_store._metadata_with_compatibility_defaults(
        {
            "tool": "detect_text",
            "provider": "oci_vision",
            "feature_type": "TEXT_DETECTION",
        },
        {"errors": [{"message": "bad"}]},
    )

    assert [entry["mcp_request_id"] for entry in rebuilt] == ["REQ_VALID", "REQ_JOB"]
    assert loaded["result_kind"] == "vision_parallel"
    assert loaded["operation_status"] == "partial_failure"
    assert loaded["feature_types"] == ["TEXT_DETECTION", "OBJECT_DETECTION"]
    assert raw_result["succeeded_count"] == 1
    assert valid["result_kind"] == "vision_parallel"
    assert compat["result_kind"] == "vision_single"
    assert compat["operation_status"] == "failed"
    assert compat["feature_types"] == ["TEXT_DETECTION"]


def test_result_store_rejects_symlinked_existing_result(tmp_path) -> None:
    raw_path = tmp_path / f"{safe_request_key('REQ')}.raw.json"
    meta_path = tmp_path / f"{safe_request_key('REQ')}.meta.json"
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    raw_path.symlink_to(target)
    meta_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ResultStoreError, match="symbolic links"):
        store_tool_result(
            result_store_dir=str(tmp_path),
            mcp_request_id="REQ",
            tool="detect_text",
            provider="oci_vision",
            raw_result={},
            oci_request_id=None,
            oci_request_ids=[],
            region="us-phoenix-1",
        )


def test_result_store_defensive_helpers_cover_error_branches(monkeypatch, tmp_path) -> None:
    path = tmp_path / "data.json"
    path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ResultStoreError, match="invalid"):
        result_store._read_json(path)

    with pytest.raises(ResultStoreError, match="written"):
        result_store._write_json(tmp_path / "bad.raw.json", {"bad": object()})
    with pytest.raises(ResultStoreError, match="index"):
        result_store._write_json_list(tmp_path / "bad-index.json", [object()])

    rollback_target = tmp_path / "rollback.json"
    result_store._restore_result_files({rollback_target: b"previous", tmp_path / "missing.json": None})
    assert rollback_target.read_bytes() == b"previous"
    assert not (tmp_path / "missing.json").exists()

    assert result_store._is_expired("2099-01-01T00:00:00", ttl_seconds=60) is False
    assert result_store._infer_result_kind(tool="detect_text", provider="oci_object_storage", feature_type=None) == "object_storage"
    assert result_store._infer_result_kind(tool="detect_text", provider="oci_vision", feature_type="A,B") == "vision_combined"
    assert result_store._infer_operation_status({"succeeded_count": 0, "failed_count": 1}) == "failed"
    assert result_store._infer_operation_status({"errors": [{"message": "bad"}]}) == "failed"

    expired_entry = {"created_at": "not-a-date", "mcp_request_id": "REQ_EXPIRED"}
    retained = result_store._prune_expired_entries(tmp_path, [expired_entry], ttl_seconds=60)
    assert retained == []

    original_open = result_store.Path.open

    def raising_open(self, *args, **kwargs):
        if self.name == ".tool_calls.lock":
            raise OSError("no lock")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(result_store.Path, "open", raising_open)
    with pytest.raises(ResultStoreError, match="locked"):
        with result_store._index_lock(tmp_path):
            pass


def test_result_store_rebuild_skips_invalid_metadata_shapes(tmp_path) -> None:
    valid_raw = tmp_path / f"{safe_request_key('REQ_OK')}.raw.json"
    valid_meta = tmp_path / f"{safe_request_key('REQ_OK')}.meta.json"
    valid_raw.write_text("{}", encoding="utf-8")
    valid_meta.write_text(
        json.dumps({"request_id": "REQ_OK", "created_at": "2099-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    (tmp_path / "bad-json.meta.json").write_text("{", encoding="utf-8")
    (tmp_path / "list.meta.json").write_text("[]", encoding="utf-8")
    (tmp_path / "no-request.meta.json").write_text("{}", encoding="utf-8")
    (tmp_path / f"{safe_request_key('REQ_MISSING_RAW')}.meta.json").write_text(
        json.dumps({"request_id": "REQ_MISSING_RAW"}),
        encoding="utf-8",
    )
    (tmp_path / "linked.meta.json").symlink_to(valid_meta)

    rebuilt = result_store._rebuild_tool_call_index(tmp_path)

    assert [entry["request_id"] for entry in rebuilt] == ["REQ_OK"]
