"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from oracle.oci_vision_mcp_server.config.consts import (
    MAX_IMAGE_JOB_OBJECTS,
    MAX_OBJECT_STORAGE_BULK_FETCH_OBJECTS,
    MAX_OBJECT_STORAGE_BULK_UPLOAD_IMAGES,
    MAX_PARALLEL_ANALYZE_ITEMS,
    MAX_PARALLEL_ANALYZE_MAX_PARALLEL,
    MAX_TOOL_MAX_ITEMS,
)
from oracle.oci_vision_mcp_server.config.schemas import (
    AnalyzeImageInput,
    CreateImageJobInput,
    ImageInput,
    ObjectStorageFetchInput,
    ObjectStorageListInput,
    ObjectStorageUploadInput,
    ParallelAnalyzeImageInput,
    ResponseDetail,
    ToolOptions,
    VisionToolInput,
)


def test_image_input_accepts_base64_source() -> None:
    image = ImageInput.model_validate({"source_type": "base64", "data": "aGVsbG8="})

    assert image.source_type == "base64"
    assert image.data == "aGVsbG8="


def test_image_input_accepts_url_source() -> None:
    image = ImageInput.model_validate({"source_type": "url", "url": "https://example.com/image.png"})

    assert image.source_type == "url"
    assert image.url == "https://example.com/image.png"


def test_image_input_requires_source_type() -> None:
    with pytest.raises(ValidationError):
        ImageInput.model_validate({"path": "data/38214.jpg"})


def test_image_input_rejects_multiple_carriers() -> None:
    with pytest.raises(ValidationError):
        ImageInput.model_validate(
            {
                "source_type": "base64",
                "data": "aGVsbG8=",
                "path": "/tmp/image.png",
            }
        )


def test_image_input_rejects_url_without_url_carrier() -> None:
    with pytest.raises(ValidationError):
        ImageInput.model_validate({"source_type": "url", "data": "aGVsbG8="})


def test_vision_tool_input_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        VisionToolInput.model_validate(
            {
                "image": {"source_type": "base64", "data": "aGVsbG8="},
                "compartment_id": "ocid1.compartment.oc1..example",
                "remote_mode": True,
            }
        )


def test_return_raw_compatibility_maps_to_raw_detail() -> None:
    options = ToolOptions.model_validate({"return_raw_oci_response": True})

    detail, warnings = options.effective_detail(ResponseDetail.SUMMARY)

    assert detail == ResponseDetail.RAW
    assert warnings[0].code == "DEPRECATED_OPTION"


def test_tool_options_rejects_too_many_rendered_items() -> None:
    with pytest.raises(ValidationError):
        ToolOptions.model_validate({"max_items": MAX_TOOL_MAX_ITEMS + 1})


def test_object_storage_upload_input_accepts_local_file_source() -> None:
    upload = ObjectStorageUploadInput.model_validate(
        {
            "image": {"source_type": "file_path", "path": "data/38214.jpg"},
            "destination": {
                "namespace": "ns",
                "bucket": "bucket",
                "object_name": "images/38214.jpg",
            },
        }
    )

    assert upload.overwrite is None
    assert upload.image.source_type == "file_path"
    assert upload.destination.object_name == "images/38214.jpg"


def test_object_storage_upload_input_rejects_non_file_source() -> None:
    with pytest.raises(ValidationError):
        ObjectStorageUploadInput.model_validate(
            {
                "image": {"source_type": "base64", "data": "aGVsbG8="},
                "destination": {
                    "namespace": "ns",
                    "bucket": "bucket",
                    "object_name": "images/38214.jpg",
                },
            }
        )


def test_object_storage_upload_input_rejects_non_image_content_type() -> None:
    with pytest.raises(ValidationError):
        ObjectStorageUploadInput.model_validate(
            {
                "image": {"source_type": "file_path", "path": "data/38214.jpg"},
                "destination": {
                    "namespace": "ns",
                    "bucket": "bucket",
                    "object_name": "images/38214.jpg",
                },
                "content_type": "text/plain",
            }
        )


def test_object_storage_list_input_defaults_options() -> None:
    list_input = ObjectStorageListInput.model_validate(
        {
            "namespace": "ns",
            "bucket": "bucket",
            "prefix": "tmp/",
        }
    )

    assert list_input.namespace == "ns"
    assert list_input.bucket == "bucket"
    assert list_input.prefix == "tmp/"
    assert list_input.options.page_size == 1000
    assert list_input.options.start_index == 0
    assert list_input.options.end_index == 10


def test_object_storage_list_input_rejects_non_slash_delimiter() -> None:
    with pytest.raises(ValidationError):
        ObjectStorageListInput.model_validate(
            {
                "namespace": "ns",
                "bucket": "bucket",
                "delimiter": "-",
            }
        )


def test_analyze_image_input_defaults_to_all_image_features() -> None:
    analyze = AnalyzeImageInput.model_validate(
        {
            "image": {"source_type": "base64", "data": "aGVsbG8="},
        }
    )

    assert [feature.value for feature in analyze.features] == [
        "image_classification",
        "object_detection",
        "face_detection",
        "text_detection",
    ]


def test_parallel_analyze_image_input_accepts_item_level_features() -> None:
    analyze = ParallelAnalyzeImageInput.model_validate(
        {
            "items": [
                {
                    "image": {"source_type": "base64", "data": "aGVsbG8="},
                    "features": ["object_detection"],
                    "min_confidence": 0.7,
                },
                {
                    "image": {"source_type": "base64", "data": "aW1hZ2U="},
                    "features": ["text_detection"],
                    "include_full_text": False,
                },
            ],
            "max_parallel": 2,
        }
    )

    assert len(analyze.items) == 2
    assert analyze.max_parallel == 2
    assert [feature.value for feature in analyze.items[0].features] == ["object_detection"]
    assert analyze.items[0].min_confidence == 0.7
    assert analyze.items[1].include_full_text is False


def test_parallel_analyze_image_input_rejects_empty_items() -> None:
    with pytest.raises(ValidationError):
        ParallelAnalyzeImageInput.model_validate({"items": []})


def test_parallel_analyze_image_input_rejects_too_many_items() -> None:
    source = {"source_type": "base64", "data": "aGVsbG8="}

    with pytest.raises(ValidationError):
        ParallelAnalyzeImageInput.model_validate(
            {"items": [{"image": source}] * (MAX_PARALLEL_ANALYZE_ITEMS + 1)}
        )


def test_parallel_analyze_image_input_rejects_too_much_concurrency() -> None:
    source = {"source_type": "base64", "data": "aGVsbG8="}

    with pytest.raises(ValidationError):
        ParallelAnalyzeImageInput.model_validate(
            {
                "items": [{"image": source}],
                "max_parallel": MAX_PARALLEL_ANALYZE_MAX_PARALLEL + 1,
            }
        )


def test_create_image_job_input_requires_at_least_one_object() -> None:
    with pytest.raises(ValidationError):
        CreateImageJobInput.model_validate({"objects": []})


def test_create_image_job_input_rejects_more_than_max_objects() -> None:
    source = {"namespace": "ns", "bucket": "bucket", "object_name": "image.jpg"}

    with pytest.raises(ValidationError):
        CreateImageJobInput.model_validate({"objects": [source] * (MAX_IMAGE_JOB_OBJECTS + 1)})


def test_create_image_job_input_accepts_max_objects() -> None:
    source = {"namespace": "ns", "bucket": "bucket", "object_name": "image.jpg"}

    job = CreateImageJobInput.model_validate({"objects": [source] * MAX_IMAGE_JOB_OBJECTS})

    assert len(job.objects) == MAX_IMAGE_JOB_OBJECTS


def test_object_storage_fetch_input_accepts_destination_path() -> None:
    fetch = ObjectStorageFetchInput.model_validate(
        {
            "object_name": "images/sample.jpg",
            "destination_path": "downloads/sample.jpg",
            "overwrite": True,
        }
    )

    assert fetch.object_name == "images/sample.jpg"
    assert fetch.destination_path == "downloads/sample.jpg"
    assert fetch.overwrite is True


def test_object_storage_upload_input_accepts_bulk_file_sources() -> None:
    upload = ObjectStorageUploadInput.model_validate(
        {
            "images": [
                {"source_type": "file_path", "path": "data/one.jpg"},
                {"source_type": "file_path", "path": "data/two.jpg"},
            ],
            "destination": {
                "namespace": "ns",
                "bucket": "bucket",
            },
            "destination_prefix": "images",
        }
    )

    assert upload.image is None
    assert len(upload.images or []) == 2
    assert upload.destination.namespace == "ns"
    assert upload.destination_prefix == "images"


def test_object_storage_upload_input_rejects_too_many_bulk_images() -> None:
    with pytest.raises(ValidationError):
        ObjectStorageUploadInput.model_validate(
            {
                "images": [
                    {"source_type": "file_path", "path": f"data/{index}.jpg"}
                    for index in range(MAX_OBJECT_STORAGE_BULK_UPLOAD_IMAGES + 1)
                ],
                "destination": {"namespace": "ns", "bucket": "bucket"},
            }
        )


def test_object_storage_upload_input_rejects_single_and_bulk_sources_together() -> None:
    with pytest.raises(ValidationError):
        ObjectStorageUploadInput.model_validate(
            {
                "image": {"source_type": "file_path", "path": "data/one.jpg"},
                "images": [{"source_type": "file_path", "path": "data/two.jpg"}],
                "destination": {"namespace": "ns", "bucket": "bucket"},
            }
        )


def test_object_storage_upload_input_rejects_bulk_destination_object_name() -> None:
    with pytest.raises(ValidationError):
        ObjectStorageUploadInput.model_validate(
            {
                "images": [{"source_type": "file_path", "path": "data/one.jpg"}],
                "destination": {
                    "namespace": "ns",
                    "bucket": "bucket",
                    "object_name": "images/one.jpg",
                },
            }
        )


def test_object_storage_fetch_input_accepts_bulk_object_names() -> None:
    fetch = ObjectStorageFetchInput.model_validate(
        {
            "object_names": ["images/one.jpg", "images/two.jpg"],
            "destination_dir": "downloads",
        }
    )

    assert fetch.object_name is None
    assert fetch.object_names == ["images/one.jpg", "images/two.jpg"]
    assert fetch.destination_dir == "downloads"


def test_object_storage_fetch_input_rejects_too_many_bulk_objects() -> None:
    with pytest.raises(ValidationError):
        ObjectStorageFetchInput.model_validate(
            {
                "object_names": [
                    f"images/{index}.jpg"
                    for index in range(MAX_OBJECT_STORAGE_BULK_FETCH_OBJECTS + 1)
                ],
            }
        )


def test_object_storage_fetch_input_rejects_single_and_bulk_sources_together() -> None:
    with pytest.raises(ValidationError):
        ObjectStorageFetchInput.model_validate(
            {
                "object_name": "images/one.jpg",
                "object_names": ["images/two.jpg"],
            }
        )


def test_object_storage_fetch_input_rejects_bulk_destination_path() -> None:
    with pytest.raises(ValidationError):
        ObjectStorageFetchInput.model_validate(
            {
                "object_names": ["images/one.jpg"],
                "destination_path": "downloads/one.jpg",
            }
        )
