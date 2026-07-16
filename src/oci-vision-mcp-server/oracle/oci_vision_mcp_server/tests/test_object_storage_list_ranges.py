"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from oracle.oci_vision_mcp_server.config.consts import (
    MAX_OBJECT_STORAGE_LIST_END_INDEX,
    MAX_OBJECT_STORAGE_LIST_RANGE_SIZE,
    MAX_OBJECT_STORAGE_LIST_SCAN_PAGES,
)
from oracle.oci_vision_mcp_server.config.schemas import ObjectStorageListInput
from oracle.oci_vision_mcp_server.tools.object_storage_tools import list_object_storage_objects as list_tool


def _mock_list_runtime(monkeypatch, *, object_count: int, prefixes: list[str] | None = None):
    calls: list[dict[str, object]] = []
    objects = [SimpleNamespace(name=f"object-{index:05d}.jpg", size=index) for index in range(object_count)]

    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "namespace")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "bucket")
    monkeypatch.setattr(list_tool, "generate_request_id", lambda: "LIST_REQ")
    monkeypatch.setattr(list_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(list_tool, "create_object_storage_client", lambda **_kwargs: object())

    def fake_list(*_args, **kwargs):
        calls.append(kwargs)
        start = kwargs["start"]
        offset = int(str(start).removeprefix("cursor-")) if start else 0
        limit = int(kwargs["limit"])
        page_end = min(offset + limit, len(objects))
        next_start = f"cursor-{page_end}" if page_end < len(objects) else None
        return SimpleNamespace(
            data=SimpleNamespace(
                objects=objects[offset:page_end],
                prefixes=list(prefixes or []),
                next_start_with=next_start,
            ),
            headers={"opc-request-id": f"OCI_REQ_{len(calls)}"},
        )

    monkeypatch.setattr(list_tool, "call_list_objects", fake_list)
    return calls


def test_list_range_returns_requested_half_open_window_and_has_more(monkeypatch) -> None:
    calls = _mock_list_runtime(monkeypatch, object_count=25, prefixes=["shared/", "shared/"])

    result = list_tool.run_list_objects_tool(
        {
            "delimiter": "/",
            "options": {"start_index": 10, "end_index": 20, "page_size": 8},
        }
    )

    assert result.isError is False
    assert [call["limit"] for call in calls] == [8, 8, 5]
    assert [item["name"] for item in result.structuredContent["objects"]] == [
        f"object-{index:05d}.jpg" for index in range(10, 20)
    ]
    assert result.structuredContent["object_count"] == 10
    assert result.structuredContent["start_index"] == 10
    assert result.structuredContent["end_index"] == 20
    assert result.structuredContent["has_more"] is True
    assert result.structuredContent["next_start_index"] == 20
    assert result.structuredContent["prefixes"] == ["shared/"]


def test_list_range_returns_short_final_window(monkeypatch) -> None:
    calls = _mock_list_runtime(monkeypatch, object_count=13)

    result = list_tool.run_list_objects_tool(
        {"options": {"start_index": 10, "end_index": 20, "page_size": 6}}
    )

    assert result.isError is False
    assert len(calls) == 3
    assert [item["name"] for item in result.structuredContent["objects"]] == [
        "object-00010.jpg",
        "object-00011.jpg",
        "object-00012.jpg",
    ]
    assert result.structuredContent["start_index"] == 10
    assert result.structuredContent["end_index"] == 13
    assert result.structuredContent["has_more"] is False
    assert result.structuredContent["next_start_index"] is None


def test_list_range_beyond_bucket_end_returns_empty_window(monkeypatch) -> None:
    _mock_list_runtime(monkeypatch, object_count=4)

    result = list_tool.run_list_objects_tool(
        {"options": {"start_index": 10, "end_index": 20}}
    )

    assert result.isError is False
    assert result.structuredContent["objects"] == []
    assert result.structuredContent["start_index"] == 10
    assert result.structuredContent["end_index"] == 10
    assert result.structuredContent["has_more"] is False
    assert result.structuredContent["next_start_index"] is None


def test_default_list_range_fetches_only_ten_objects_plus_has_more_probe(monkeypatch) -> None:
    calls = _mock_list_runtime(monkeypatch, object_count=100)

    result = list_tool.run_list_objects_tool({})

    assert result.isError is False
    assert len(calls) == 1
    assert calls[0]["limit"] == 11
    assert result.structuredContent["object_count"] == 10
    assert result.structuredContent["end_index"] == 10
    assert result.structuredContent["has_more"] is True
    assert result.structuredContent["next_start_index"] == 10


def test_exact_end_does_not_report_has_more(monkeypatch) -> None:
    calls = _mock_list_runtime(monkeypatch, object_count=10)

    result = list_tool.run_list_objects_tool({})

    assert result.isError is False
    assert len(calls) == 1
    assert result.structuredContent["end_index"] == 10
    assert result.structuredContent["has_more"] is False
    assert result.structuredContent["next_start_index"] is None


def test_prefix_only_listing_stops_at_bounded_prefix_window(monkeypatch) -> None:
    calls: list[dict[str, object]] = []
    prefixes = [f"folder-{index:03d}/" for index in range(30)]
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "namespace")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "bucket")
    monkeypatch.setattr(list_tool, "generate_request_id", lambda: "LIST_REQ")
    monkeypatch.setattr(list_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(list_tool, "create_object_storage_client", lambda **_kwargs: object())

    def fake_list(*_args, **kwargs):
        calls.append(kwargs)
        offset = int(str(kwargs["start"]).removeprefix("cursor-")) if kwargs["start"] else 0
        page_end = min(offset + int(kwargs["limit"]), len(prefixes))
        return SimpleNamespace(
            data=SimpleNamespace(
                objects=[],
                prefixes=prefixes[offset:page_end],
                next_start_with=(f"cursor-{page_end}" if page_end < len(prefixes) else None),
            ),
            headers={},
        )

    monkeypatch.setattr(list_tool, "call_list_objects", fake_list)

    result = list_tool.run_list_objects_tool({"delimiter": "/"})

    assert result.isError is False
    assert len(calls) == 3
    assert result.structuredContent["prefix_count"] == 10
    assert result.structuredContent["prefixes_truncated"] is True
    assert result.structuredContent["scan_complete"] is True
    assert result.structuredContent["warnings"][0]["code"] == "PREFIX_RESULTS_TRUNCATED"


def test_prefix_overflow_does_not_hide_later_objects(monkeypatch) -> None:
    calls = []
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "namespace")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "bucket")
    monkeypatch.setattr(list_tool, "generate_request_id", lambda: "LIST_REQ")
    monkeypatch.setattr(list_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(list_tool, "create_object_storage_client", lambda **_kwargs: object())

    def fake_list(*_args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return SimpleNamespace(
                data=SimpleNamespace(
                    objects=[],
                    prefixes=[f"folder-{index}/" for index in range(11)],
                    next_start_with="cursor-1",
                ),
                headers={},
            )
        return SimpleNamespace(
            data=SimpleNamespace(
                objects=[SimpleNamespace(name="z.jpg", size=1)],
                prefixes=[],
                next_start_with=None,
            ),
            headers={},
        )

    monkeypatch.setattr(list_tool, "call_list_objects", fake_list)

    result = list_tool.run_list_objects_tool({"delimiter": "/"})

    assert len(calls) == 2
    assert [item["name"] for item in result.structuredContent["objects"]] == ["z.jpg"]
    assert result.structuredContent["has_more"] is False
    assert result.structuredContent["scan_complete"] is True
    assert result.structuredContent["prefixes_truncated"] is True


def test_scan_budget_reports_unknown_has_more_instead_of_false_exhaustion(
    monkeypatch,
) -> None:
    calls = []
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "namespace")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "bucket")
    monkeypatch.setattr(list_tool, "generate_request_id", lambda: "LIST_REQ")
    monkeypatch.setattr(list_tool, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(list_tool, "create_object_storage_client", lambda **_kwargs: object())

    def fake_list(*_args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            data=SimpleNamespace(
                objects=[],
                prefixes=[f"folder-{len(calls)}/"],
                next_start_with=f"cursor-{len(calls)}",
            ),
            headers={},
        )

    monkeypatch.setattr(list_tool, "call_list_objects", fake_list)

    result = list_tool.run_list_objects_tool({"delimiter": "/"})

    assert len(calls) == MAX_OBJECT_STORAGE_LIST_SCAN_PAGES
    assert result.structuredContent["has_more"] is None
    assert result.structuredContent["next_start_index"] is None
    assert result.structuredContent["scan_complete"] is False
    assert {warning["code"] for warning in result.structuredContent["warnings"]} == {
        "LIST_SCAN_LIMIT_REACHED",
        "PREFIX_RESULTS_TRUNCATED",
    }


def test_list_range_accepts_maximum_supported_boundaries() -> None:
    validated = ObjectStorageListInput.model_validate(
        {
            "options": {
                "start_index": MAX_OBJECT_STORAGE_LIST_END_INDEX
                - MAX_OBJECT_STORAGE_LIST_RANGE_SIZE,
                "end_index": MAX_OBJECT_STORAGE_LIST_END_INDEX,
            }
        }
    )

    assert (
        validated.options.start_index
        == MAX_OBJECT_STORAGE_LIST_END_INDEX - MAX_OBJECT_STORAGE_LIST_RANGE_SIZE
    )
    assert validated.options.end_index == MAX_OBJECT_STORAGE_LIST_END_INDEX


@pytest.mark.parametrize(
    "options",
    [
        {"start_index": -1, "end_index": 10},
        {"start_index": 10, "end_index": 10},
        {"start_index": 20, "end_index": 10},
        {"start_index": 0, "end_index": MAX_OBJECT_STORAGE_LIST_RANGE_SIZE + 1},
        {
            "start_index": MAX_OBJECT_STORAGE_LIST_END_INDEX - 1,
            "end_index": MAX_OBJECT_STORAGE_LIST_END_INDEX + 1,
        },
    ],
)
def test_list_range_rejects_invalid_or_excessive_windows(options: dict[str, int]) -> None:
    with pytest.raises(ValidationError):
        ObjectStorageListInput.model_validate({"options": options})
