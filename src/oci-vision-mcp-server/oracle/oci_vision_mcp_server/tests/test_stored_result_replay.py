"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import json
from pathlib import Path

from oracle.oci_vision_mcp_server.config.schemas import ResponseDetail
from oracle.oci_vision_mcp_server.io.result_store import safe_request_key, store_tool_result
from oracle.oci_vision_mcp_server.tools.support_tools import get_analysis_result as replay_tool


def _store(
    store_dir: Path,
    *,
    request_id: str,
    tool: str,
    raw_result: dict,
    provider: str = "oci_vision",
    feature_type: str | None = None,
    result_kind: str | None = None,
    detail_options: dict | None = None,
) -> dict:
    return store_tool_result(
        result_store_dir=str(store_dir),
        mcp_request_id=request_id,
        tool=tool,
        provider=provider,
        raw_result=raw_result,
        oci_request_id="OCI_REQ",
        oci_request_ids=["OCI_REQ"],
        region="us-ashburn-1",
        feature_type=feature_type,
        detail_options=detail_options,
        result_kind=result_kind,
    )


def test_replay_combined_analysis_uses_all_features_and_saved_options(
    monkeypatch,
    tmp_path,
) -> None:
    store_dir = tmp_path / "results"
    monkeypatch.setenv("OCI_VISION_RESULT_STORE_DIR", str(store_dir))
    _store(
        store_dir,
        request_id="combined",
        tool="analyze_image",
        feature_type="IMAGE_CLASSIFICATION,OBJECT_DETECTION",
        result_kind="vision_combined",
        detail_options={"min_confidence": 0.8, "include_full_text": True},
        raw_result={
            "labels": [
                {"name": "high", "confidence": 0.9},
                {"name": "low", "confidence": 0.5},
            ],
            "image_objects": [{"name": "Person", "confidence": 0.85}],
            "errors": [],
        },
    )

    result = replay_tool.get_analysis_result(
        request_id="combined",
        detail=ResponseDetail.STANDARD,
        max_items=10,
    )

    assert result.isError is False
    assert result.structuredContent["feature_type"] == (
        "IMAGE_CLASSIFICATION,OBJECT_DETECTION"
    )
    assert result.structuredContent["results"]["image_classification"]["labels"] == [
        {"name": "high", "confidence": 0.9}
    ]
    assert result.structuredContent["results"]["object_detection"]["objects"] == [
        {"name": "Person", "confidence": 0.85}
    ]


def test_replay_parallel_analysis_preserves_partial_failure_and_item_options(
    monkeypatch,
    tmp_path,
) -> None:
    store_dir = tmp_path / "results"
    monkeypatch.setenv("OCI_VISION_RESULT_STORE_DIR", str(store_dir))
    _store(
        store_dir,
        request_id="parallel",
        tool="parallel_analyze_image",
        feature_type="parallel_analyze_image",
        result_kind="vision_parallel",
        raw_result={
            "total_count": 2,
            "succeeded_count": 1,
            "failed_count": 1,
            "items": [
                {
                    "index": 0,
                    "status": "succeeded",
                    "feature_types": ["IMAGE_CLASSIFICATION"],
                    "image": {"source_type": "base64"},
                    "oci_client_request_id": "CLIENT_1",
                    "oci_request_id": "OCI_1",
                    "min_confidence": 0.8,
                    "include_full_text": True,
                    "result": {
                        "labels": [
                            {"name": "high", "confidence": 0.9},
                            {"name": "low", "confidence": 0.4},
                        ],
                        "errors": [],
                    },
                },
                {
                    "index": 1,
                    "status": "failed",
                    "feature_types": ["IMAGE_CLASSIFICATION"],
                    "image": {"source_type": "base64"},
                    "oci_client_request_id": "CLIENT_2",
                    "oci_request_id": None,
                    "result": {
                        "errors": [
                            {
                                "code": "TooManyRequests",
                                "message": "rate limited",
                                "retryable": True,
                            }
                        ]
                    },
                },
            ],
        },
    )

    result = replay_tool.get_analysis_result(
        request_id="parallel",
        detail=ResponseDetail.STANDARD,
        max_items=10,
    )

    assert result.isError is False
    summary = result.structuredContent["results"]["summary"]
    assert summary == {
        "message": "parallel_analyze_image completed 1/2 images with 1 failures.",
        "total_count": 2,
        "succeeded_count": 1,
        "failed_count": 1,
        "partial_failure": True,
    }
    items = result.structuredContent["results"]["items"]
    assert items[0]["results"]["image_classification"]["labels"] == [
        {"name": "high", "confidence": 0.9}
    ]
    assert items[1]["errors"][0]["code"] == "TooManyRequests"


def test_replay_image_job_uses_operation_renderer(monkeypatch, tmp_path) -> None:
    store_dir = tmp_path / "results"
    monkeypatch.setenv("OCI_VISION_RESULT_STORE_DIR", str(store_dir))
    _store(
        store_dir,
        request_id="job",
        tool="create_image_job",
        feature_type="TEXT_DETECTION",
        result_kind="vision_image_job",
        raw_result={
            "id": "ocid1.aivisionimagejob.oc1..example",
            "lifecycle_state": "ACCEPTED",
            "_headers": {"opc-work-request-id": "WORK_REQ"},
        },
    )

    result = replay_tool.get_analysis_result(
        request_id="job",
        detail=ResponseDetail.SUMMARY,
        max_items=10,
    )

    assert result.isError is False
    summary = result.structuredContent["results"]["summary"]
    assert summary["id"] == "ocid1.aivisionimagejob.oc1..example"
    assert summary["lifecycle_state"] == "ACCEPTED"
    assert "work_request_id" not in summary
    assert "_headers" not in result.structuredContent["results"]["data"]

    raw_result = replay_tool.get_analysis_result(
        request_id="job",
        detail=ResponseDetail.RAW,
        max_items=10,
    )
    assert raw_result.structuredContent["results"]["raw_result_inline"]["_headers"] == {
        "opc-work-request-id": "WORK_REQ"
    }
    assert raw_result.structuredContent["debug_metadata"]["oci_request_ids"] == [
        "OCI_REQ"
    ]


def test_replay_failed_non_create_image_job_adds_default_error(monkeypatch, tmp_path) -> None:
    store_dir = tmp_path / "results"
    monkeypatch.setenv("OCI_VISION_RESULT_STORE_DIR", str(store_dir))
    _store(
        store_dir,
        request_id="failed-job",
        tool="get_image_job",
        feature_type="",
        result_kind="vision_image_job",
        raw_result={
            "id": "ocid1.aivisionimagejob.oc1..example",
            "lifecycle_state": "FAILED",
        },
    )
    meta_path = store_dir / f"{safe_request_key('failed-job')}.meta.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    metadata["operation_status"] = "failed"
    metadata["oci_request_ids"] = "not-a-list"
    meta_path.write_text(json.dumps(metadata), encoding="utf-8")

    result = replay_tool.get_analysis_result(
        request_id="failed-job",
        detail=ResponseDetail.STANDARD,
        max_items=10,
    )

    assert result.isError is True
    assert result.structuredContent["feature_type"] == "image_job"
    assert result.structuredContent["results"]["summary"]["message"] == "get_image_job completed."
    assert result.structuredContent["errors"] == [
        {
            "code": "STORED_OPERATION_FAILED",
            "message": "The stored get_image_job operation failed.",
            "retryable": False,
        }
    ]


def test_replay_failed_object_storage_batch_preserves_failure(monkeypatch, tmp_path) -> None:
    store_dir = tmp_path / "results"
    monkeypatch.setenv("OCI_VISION_RESULT_STORE_DIR", str(store_dir))
    _store(
        store_dir,
        request_id="object-failure",
        tool="fetch_object_storage_object",
        provider="oci_object_storage",
        result_kind="object_storage",
        raw_result={
            "total_count": 1,
            "succeeded_count": 0,
            "failed_count": 1,
            "items": [
                {
                    "status": "failed",
                    "oci_request_id": "OCI_NESTED",
                    "headers": {"opc-request-id": "OCI_NESTED"},
                    "errors": [
                        {
                            "code": "NotFound",
                            "message": "object missing",
                            "retryable": False,
                        }
                    ],
                }
            ],
        },
    )

    result = replay_tool.get_analysis_result(
        request_id="object-failure",
        detail=ResponseDetail.STANDARD,
        max_items=10,
    )

    assert result.isError is True
    assert result.structuredContent["status"] == "failed"
    assert result.structuredContent["results"]["partial_failure"] is False
    assert result.structuredContent["errors"][0]["code"] == "NotFound"
    assert "oci_request_id" not in result.structuredContent["results"]["items"][0]
    assert "headers" not in result.structuredContent["results"]["items"][0]


def test_replay_failed_object_storage_uses_top_level_and_default_errors(
    monkeypatch,
    tmp_path,
) -> None:
    store_dir = tmp_path / "results"
    monkeypatch.setenv("OCI_VISION_RESULT_STORE_DIR", str(store_dir))
    _store(
        store_dir,
        request_id="object-top-error",
        tool="upload_image_to_object_storage",
        provider="oci_object_storage",
        result_kind="object_storage",
        raw_result={
            "succeeded_count": 0,
            "failed_count": 1,
            "warnings": [{"code": "W"}, "ignore"],
            "items": [{"errors": ["ignore"]}],
            "errors": [
                {
                    "code": "TopLevel",
                    "message": "top-level failure",
                    "retryable": False,
                }
            ],
        },
    )
    top_meta_path = store_dir / f"{safe_request_key('object-top-error')}.meta.json"
    top_metadata = json.loads(top_meta_path.read_text(encoding="utf-8"))
    top_metadata["operation_status"] = "failed"
    top_meta_path.write_text(json.dumps(top_metadata), encoding="utf-8")

    top_result = replay_tool.get_analysis_result("object-top-error")

    assert top_result.isError is True
    assert top_result.structuredContent["warnings"] == [{"code": "W"}]
    assert top_result.structuredContent["errors"][0]["code"] == "TopLevel"

    _store(
        store_dir,
        request_id="object-default-error",
        tool="upload_image_to_object_storage",
        provider="oci_object_storage",
        result_kind="object_storage",
        raw_result={"succeeded_count": 0, "failed_count": 1},
    )
    default_meta_path = store_dir / f"{safe_request_key('object-default-error')}.meta.json"
    default_metadata = json.loads(default_meta_path.read_text(encoding="utf-8"))
    default_metadata["operation_status"] = "failed"
    default_meta_path.write_text(json.dumps(default_metadata), encoding="utf-8")

    default_result = replay_tool.get_analysis_result("object-default-error")

    assert default_result.isError is True
    assert default_result.structuredContent["errors"] == [
        {
            "code": "STORED_OPERATION_FAILED",
            "message": "The stored Object Storage operation failed.",
            "retryable": False,
        }
    ]


def test_replay_object_storage_list_preserves_numeric_range(monkeypatch, tmp_path) -> None:
    store_dir = tmp_path / "results"
    monkeypatch.setenv("OCI_VISION_RESULT_STORE_DIR", str(store_dir))
    _store(
        store_dir,
        request_id="object-list",
        tool="list_object_storage_objects",
        provider="oci_object_storage",
        result_kind="object_storage",
        raw_result={
            "namespace": "namespace",
            "bucket": "bucket",
            "objects": [{"name": "object-10.jpg"}],
            "prefixes": [],
            "object_count": 1,
            "prefix_count": 0,
            "start_index": 10,
            "end_index": 11,
            "has_more": True,
            "next_start_index": 11,
            "oci_request_ids": ["OCI_REQ"],
        },
    )

    result = replay_tool.get_analysis_result(
        request_id="object-list",
        detail=ResponseDetail.STANDARD,
        max_items=10,
    )

    assert result.isError is False
    assert result.structuredContent["results"]["start_index"] == 10
    assert result.structuredContent["results"]["end_index"] == 11
    assert result.structuredContent["results"]["has_more"] is True
    assert result.structuredContent["results"]["next_start_index"] == 11
    assert "oci_request_ids" not in result.structuredContent["results"]


def test_legacy_combined_metadata_is_inferred_without_rewrite(monkeypatch, tmp_path) -> None:
    store_dir = tmp_path / "results"
    monkeypatch.setenv("OCI_VISION_RESULT_STORE_DIR", str(store_dir))
    _store(
        store_dir,
        request_id="legacy",
        tool="analyze_image",
        feature_type="IMAGE_CLASSIFICATION,OBJECT_DETECTION",
        raw_result={"labels": [], "image_objects": [], "errors": []},
    )
    meta_path = store_dir / f"{safe_request_key('legacy')}.meta.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    for key in ("schema_version", "result_kind", "operation_status", "feature_types"):
        metadata.pop(key, None)
    metadata["detail_options"] = "not-a-dict"
    meta_path.write_text(json.dumps(metadata), encoding="utf-8")

    result = replay_tool.get_analysis_result(
        request_id="legacy",
        detail=ResponseDetail.STANDARD,
        max_items=10,
    )

    assert result.isError is False
    assert set(result.structuredContent["results"]) == {
        "image_classification",
        "object_detection",
    }
    persisted = json.loads(meta_path.read_text(encoding="utf-8"))
    assert "schema_version" not in persisted
