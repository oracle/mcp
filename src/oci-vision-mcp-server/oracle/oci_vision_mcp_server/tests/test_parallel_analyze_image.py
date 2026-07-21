"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from types import SimpleNamespace

import oci

from oracle.oci_vision_mcp_server.tools.vision_api_tools import parallel_analyze_image as parallel_tool


def test_parallel_analyze_image_calls_analyze_for_each_item(monkeypatch) -> None:
    captured_request_ids = []

    monkeypatch.setattr(parallel_tool, "generate_request_id", lambda: "BATCH_REQ")
    monkeypatch.setattr(parallel_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(parallel_tool, "create_vision_client", lambda **_kwargs: object())

    def fake_call(*_args, **kwargs):
        captured_request_ids.append(kwargs["request_id"])
        return SimpleNamespace(
            data={
                "image_objects": [
                    {"name": "Person", "confidence": 0.91},
                ],
                "errors": [],
            },
            opc_request_id=f"OCI_{kwargs['request_id']}",
        )

    monkeypatch.setattr(parallel_tool, "call_analyze_image_features", fake_call)

    result = parallel_tool.run_parallel_analyze_image_tool(
        {
            "items": [
                {
                    "image": {"source_type": "base64", "data": "iVBORw0KGgpleGFtcGxl"},
                    "features": ["object_detection"],
                },
                {
                    "image": {"source_type": "base64", "data": "iVBORw0KGgpleGFtcGxlMg=="},
                    "features": ["object_detection"],
                },
            ],
            "max_parallel": 2,
        }
    )

    assert result.isError is False
    assert set(captured_request_ids) == {"BATCH_REQ-1", "BATCH_REQ-2"}
    summary = result.structuredContent["results"]["summary"]
    assert summary["total_count"] == 2
    assert summary["succeeded_count"] == 2
    assert summary["failed_count"] == 0
    assert summary["partial_failure"] is False
    items = result.structuredContent["results"]["items"]
    assert [item["index"] for item in items] == [0, 1]
    assert [item["status"] for item in items] == ["succeeded", "succeeded"]
    assert items[0]["results"]["object_detection"]["summary"]["object_count"] == 1


def test_parallel_non_raw_debug_metadata_hides_oci_request_ids(monkeypatch) -> None:
    monkeypatch.setattr(parallel_tool, "generate_request_id", lambda: "BATCH_REQ")
    monkeypatch.setattr(parallel_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(parallel_tool, "create_vision_client", lambda **_kwargs: object())
    monkeypatch.setattr(
        parallel_tool,
        "call_analyze_image_features",
        lambda *_args, **_kwargs: SimpleNamespace(
            data={"labels": [], "errors": []},
            opc_request_id="OCI_REQ",
        ),
    )

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
            ],
            "options": {"detail": "standard", "include_debug_metadata": True},
        }
    )

    assert result.isError is False
    assert "oci_request_id" not in result.structuredContent["debug_metadata"]
    assert "oci_request_ids" not in result.structuredContent["debug_metadata"]
    assert "oci_request_id" not in result.structuredContent["results"]["items"][0]


def test_parallel_analyze_image_reports_partial_failure(monkeypatch) -> None:
    monkeypatch.setattr(parallel_tool, "generate_request_id", lambda: "BATCH_REQ")
    monkeypatch.setattr(parallel_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(parallel_tool, "create_vision_client", lambda **_kwargs: object())

    def fake_call(*_args, **kwargs):
        if kwargs["request_id"].endswith("-2"):
            raise oci.exceptions.ServiceError(
                status=429,
                code="TooManyRequests",
                headers={},
                message="rate limited",
            )
        return SimpleNamespace(
            data={
                "labels": [
                    {"name": "Outdoor", "confidence": 0.88},
                ],
                "errors": [],
            },
            opc_request_id="OCI_OK",
        )

    monkeypatch.setattr(parallel_tool, "call_analyze_image_features", fake_call)

    result = parallel_tool.run_parallel_analyze_image_tool(
        {
            "items": [
                {
                    "image": {"source_type": "base64", "data": "iVBORw0KGgpleGFtcGxl"},
                    "features": ["image_classification"],
                },
                {
                    "image": {"source_type": "base64", "data": "iVBORw0KGgpleGFtcGxlMg=="},
                    "features": ["image_classification"],
                },
            ],
            "max_parallel": 2,
        }
    )

    assert result.isError is False
    summary = result.structuredContent["results"]["summary"]
    assert summary["succeeded_count"] == 1
    assert summary["failed_count"] == 1
    assert summary["partial_failure"] is True
    items = result.structuredContent["results"]["items"]
    assert [item["index"] for item in items] == [0, 1]
    assert items[0]["status"] == "succeeded"
    assert items[1]["status"] == "failed"
    assert items[1]["errors"][0]["code"] == "TooManyRequests"


def test_parallel_analyze_image_returns_error_when_every_item_fails(monkeypatch) -> None:
    monkeypatch.setattr(parallel_tool, "generate_request_id", lambda: "BATCH_REQ")
    monkeypatch.setattr(parallel_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(parallel_tool, "create_vision_client", lambda **_kwargs: object())

    def fake_call(*_args, **_kwargs):
        raise oci.exceptions.ServiceError(
            status=500,
            code="InternalError",
            headers={},
            message="temporary service failure",
        )

    monkeypatch.setattr(parallel_tool, "call_analyze_image_features", fake_call)

    result = parallel_tool.run_parallel_analyze_image_tool(
        {
            "items": [
                {
                    "image": {"source_type": "base64", "data": "iVBORw0KGgpleGFtcGxl"},
                    "features": ["image_classification"],
                }
            ]
        }
    )

    assert result.isError is True
    assert result.structuredContent["status"] == "failed"
    assert result.structuredContent["results"]["summary"]["failed_count"] == 1
    assert result.structuredContent["errors"][0]["code"] == "InternalError"
