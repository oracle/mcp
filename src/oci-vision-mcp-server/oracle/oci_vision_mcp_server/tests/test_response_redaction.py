"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from oracle.oci_vision_mcp_server.config.schemas import (
    ObjectStorageDestinationInput,
    ObjectStorageFetchEnvelope,
    ObjectStorageFetchItem,
    ResponseDetail,
)
from oracle.oci_vision_mcp_server.tools.object_storage_tools.helpers import (
    attach_raw_payload,
    object_storage_structured_content,
    object_summary,
    resolve_object_storage_namespace_bucket,
    resolve_upload_destination,
    response_headers,
    stringify_datetime,
)


def test_normal_object_storage_response_redacts_nested_diagnostic_ids() -> None:
    envelope = ObjectStorageFetchEnvelope(
        status="succeeded",
        tool="fetch_object_storage_object",
        detail=ResponseDetail.SUMMARY,
        request_id="MCP_REQ",
        mcp_request_id="MCP_REQ",
        oci_request_id="OCI_TOP",
        oci_request_ids=["OCI_TOP"],
        raw_result_path="/private/raw.json",
        items=[
            ObjectStorageFetchItem(
                status="succeeded",
                file_path="image.jpg",
                oci_request_id="OCI_ITEM",
            )
        ],
    )

    structured = object_storage_structured_content(envelope)

    assert structured["request_id"] == "MCP_REQ"
    assert "oci_request_id" not in structured
    assert "oci_request_ids" not in structured
    assert "raw_result_path" not in structured
    assert "raw_result_available" not in structured
    assert "raw_result_inline" not in structured
    assert "oci_request_id" not in structured["items"][0]


def test_raw_object_storage_response_keeps_diagnostic_ids() -> None:
    envelope = ObjectStorageFetchEnvelope(
        status="succeeded",
        tool="fetch_object_storage_object",
        detail=ResponseDetail.RAW,
        request_id="MCP_REQ",
        mcp_request_id="MCP_REQ",
        oci_request_id="OCI_TOP",
        oci_request_ids=["OCI_TOP"],
        raw_result_path="/private/raw.json",
        items=[ObjectStorageFetchItem(status="succeeded", oci_request_id="OCI_ITEM")],
    )

    structured = object_storage_structured_content(envelope)

    assert structured["oci_request_id"] == "OCI_TOP"
    assert structured["oci_request_ids"] == ["OCI_TOP"]
    assert structured["items"][0]["oci_request_id"] == "OCI_ITEM"


def test_object_storage_helper_edges_and_defaults() -> None:
    assert response_headers(SimpleNamespace(headers=None)) == {}
    assert response_headers(SimpleNamespace(headers={"a": 1, "skip": None})) == {"a": "1"}

    config = SimpleNamespace(
        object_storage_namespace="default_namespace",
        object_storage_bucket="default_bucket",
    )
    assert resolve_object_storage_namespace_bucket(
        namespace=None,
        bucket=None,
        resolved_config=config,
        namespace_argument="namespace",
        bucket_argument="bucket",
    ) == ("default_namespace", "default_bucket")

    destination = ObjectStorageDestinationInput(namespace="ns", bucket="bucket")
    resolved_destination = resolve_upload_destination(
        destination=destination,
        resolved_config=config,
        file_name="image.png",
    )
    assert resolved_destination.namespace == "ns"
    assert resolved_destination.bucket == "bucket"
    assert resolved_destination.object_name == "image.png"

    explicit_destination = resolve_upload_destination(
        destination=ObjectStorageDestinationInput(
            namespace="ns",
            bucket="bucket",
            object_name="folder/custom.png",
        ),
        resolved_config=config,
        file_name="image.png",
    )
    assert explicit_destination.object_name == "folder/custom.png"

    created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    summary = object_summary(
        SimpleNamespace(
            name="object.jpg",
            size=10,
            time_created=created,
            time_modified="later",
            etag="etag",
            md5="md5",
            storage_tier="Standard",
            archival_state=None,
        )
    )
    assert summary.name == "object.jpg"
    assert summary.time_created == created.isoformat()
    assert summary.time_modified == "later"
    assert stringify_datetime(None) is None


def test_attach_raw_payload_records_unavailable_large_payload() -> None:
    envelope = ObjectStorageFetchEnvelope(
        status="succeeded",
        tool="fetch_object_storage_object",
        detail=ResponseDetail.RAW,
        request_id="MCP_REQ",
        mcp_request_id="MCP_REQ",
        items=[],
    )

    attach_raw_payload(
        envelope,
        raw_result={"payload": "x" * 100},
        stored_metadata={"raw_result_path": None},
        max_inline_response_bytes=10,
    )

    assert envelope.raw_result_available is False
    assert envelope.raw_result_inline is None
    assert envelope.raw_result_path is None
