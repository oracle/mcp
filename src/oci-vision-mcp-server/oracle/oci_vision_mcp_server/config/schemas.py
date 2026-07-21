"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .consts import (
    MAX_IMAGE_JOB_OBJECTS,
    MAX_OBJECT_STORAGE_BULK_FETCH_OBJECTS,
    MAX_OBJECT_STORAGE_BULK_UPLOAD_IMAGES,
    MAX_OBJECT_STORAGE_LIST_END_INDEX,
    MAX_OBJECT_STORAGE_LIST_PAGE_SIZE,
    MAX_OBJECT_STORAGE_LIST_RANGE_SIZE,
    MAX_PARALLEL_ANALYZE_ITEMS,
    MAX_PARALLEL_ANALYZE_MAX_PARALLEL,
    MAX_TOOL_MAX_ITEMS,
)


class ImageSourceType(str, Enum):
    BASE64 = "base64"
    FILE_PATH = "file_path"
    OCI_OBJECT = "oci_object"
    URL = "url"


class ResponseDetail(str, Enum):
    SUMMARY = "summary"
    STANDARD = "standard"
    BOXES = "boxes"
    RAW = "raw"


class ImageAnalysisFeature(str, Enum):
    IMAGE_CLASSIFICATION = "image_classification"
    OBJECT_DETECTION = "object_detection"
    FACE_DETECTION = "face_detection"
    TEXT_DETECTION = "text_detection"


class ObjectStorageListField(str, Enum):
    NAME = "name"
    SIZE = "size"
    ETAG = "etag"
    TIME_CREATED = "timeCreated"
    MD5 = "md5"
    TIME_MODIFIED = "timeModified"
    STORAGE_TIER = "storageTier"
    ARCHIVAL_STATE = "archivalState"


DEFAULT_OBJECT_STORAGE_LIST_FIELDS = [
    ObjectStorageListField.NAME,
    ObjectStorageListField.SIZE,
    ObjectStorageListField.TIME_MODIFIED,
    ObjectStorageListField.ETAG,
    ObjectStorageListField.STORAGE_TIER,
    ObjectStorageListField.ARCHIVAL_STATE,
]


class OciObjectInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    namespace: str = Field(min_length=1, description="Object Storage namespace.")
    bucket: str = Field(min_length=1, description="Object Storage bucket name.")
    object_name: str = Field(min_length=1, description="Object Storage object name.")


class ObjectStorageDestinationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    namespace: str | None = Field(default=None, min_length=1, description="Object Storage namespace.")
    bucket: str | None = Field(default=None, min_length=1, description="Object Storage bucket name.")
    object_name: str | None = Field(default=None, min_length=1, description="Object Storage object name.")


class ImageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: ImageSourceType
    data: str | None = Field(default=None, description="Base64 image bytes.")
    path: str | None = Field(default=None, description="Filesystem image path.")
    oci_object: OciObjectInput | None = None
    url: str | None = Field(default=None, description="HTTPS image URL.")

    @model_validator(mode="after")
    def validate_source_payload(self) -> "ImageInput":
        carriers = [
            self.data is not None,
            self.path is not None,
            self.oci_object is not None,
            self.url is not None,
        ]
        if sum(carriers) != 1:
            raise ValueError("Exactly one image data carrier must be provided.")

        if self.source_type == ImageSourceType.BASE64 and self.data is None:
            raise ValueError("data is required when source_type=base64.")
        if self.source_type == ImageSourceType.FILE_PATH and self.path is None:
            raise ValueError("path is required when source_type=file_path.")
        if self.source_type == ImageSourceType.OCI_OBJECT and self.oci_object is None:
            raise ValueError("oci_object is required when source_type=oci_object.")
        if self.source_type == ImageSourceType.URL and self.url is None:
            raise ValueError("url is required when source_type=url.")
        return self


class ToolOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: str | None = None
    request_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description=(
            "Optional OCI client request id for tracing; stored result lookup uses "
            "the tool response request_id."
        ),
    )
    detail: ResponseDetail = ResponseDetail.SUMMARY
    max_items: int = Field(default=10, ge=1, le=MAX_TOOL_MAX_ITEMS)
    include_debug_metadata: bool = False
    return_raw_oci_response: bool = False

    def effective_detail(self, default_detail: ResponseDetail) -> tuple[ResponseDetail, list["WarningDetail"]]:
        if "detail" in self.model_fields_set:
            detail = self.detail
            warnings = []
        elif self.return_raw_oci_response:
            detail = ResponseDetail.RAW
            warnings = [
                WarningDetail(
                    code="DEPRECATED_OPTION",
                    message="return_raw_oci_response is deprecated; use detail=raw instead.",
                )
            ]
        else:
            detail = default_detail
            warnings = []

        if self.return_raw_oci_response and "detail" in self.model_fields_set:
            warnings.append(
                WarningDetail(
                    code="DEPRECATED_OPTION_IGNORED",
                    message="return_raw_oci_response is deprecated and ignored because detail was provided.",
                )
            )
        return detail, warnings


class VisionToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: ImageInput
    compartment_id: str | None = Field(default=None, min_length=1)
    max_results: int | None = Field(default=None, ge=1, le=100)
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    options: ToolOptions = Field(default_factory=ToolOptions)


class FaceToolInput(VisionToolInput):
    should_return_landmarks: bool = False


class TextToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: ImageInput
    compartment_id: str | None = Field(default=None, min_length=1)
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    include_full_text: bool = True
    options: ToolOptions = Field(default_factory=ToolOptions)


def _default_image_analysis_features() -> list[ImageAnalysisFeature]:
    return [
        ImageAnalysisFeature.IMAGE_CLASSIFICATION,
        ImageAnalysisFeature.OBJECT_DETECTION,
        ImageAnalysisFeature.FACE_DETECTION,
        ImageAnalysisFeature.TEXT_DETECTION,
    ]


class AnalyzeImageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: ImageInput
    features: list[ImageAnalysisFeature] = Field(
        default_factory=_default_image_analysis_features,
        min_length=1,
    )
    compartment_id: str | None = Field(default=None, min_length=1)
    max_results: int | None = Field(default=None, ge=1, le=100)
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    should_return_landmarks: bool = False
    include_full_text: bool = True
    options: ToolOptions = Field(default_factory=ToolOptions)


class ParallelAnalyzeImageItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: ImageInput
    features: list[ImageAnalysisFeature] = Field(
        default_factory=_default_image_analysis_features,
        min_length=1,
    )
    compartment_id: str | None = Field(default=None, min_length=1)
    max_results: int | None = Field(default=None, ge=1, le=100)
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    should_return_landmarks: bool = False
    include_full_text: bool = True


class ParallelAnalyzeImageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ParallelAnalyzeImageItem] = Field(
        min_length=1,
        max_length=MAX_PARALLEL_ANALYZE_ITEMS,
    )
    compartment_id: str | None = Field(default=None, min_length=1)
    max_parallel: int = Field(default=4, ge=1, le=MAX_PARALLEL_ANALYZE_MAX_PARALLEL)
    options: ToolOptions = Field(default_factory=ToolOptions)


class VisionJobOutputInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    namespace: str | None = Field(default=None, min_length=1)
    bucket: str | None = Field(default=None, min_length=1)
    prefix: str | None = Field(default=None, min_length=1)


class CreateImageJobInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objects: list[OciObjectInput] = Field(min_length=1, max_length=MAX_IMAGE_JOB_OBJECTS)
    features: list[ImageAnalysisFeature] = Field(
        default_factory=_default_image_analysis_features,
        min_length=1,
    )
    output_location: VisionJobOutputInput | None = None
    compartment_id: str | None = Field(default=None, min_length=1)
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_zip_output_enabled: bool = False
    max_results: int | None = Field(default=None, ge=1, le=100)
    should_return_landmarks: bool = False
    options: ToolOptions = Field(default_factory=ToolOptions)


class GetImageJobInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    options: ToolOptions = Field(default_factory=ToolOptions)


class CancelImageJobInput(GetImageJobInput):
    confirm: bool = False


class ObjectStorageUploadOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: str | None = None
    request_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description=(
            "Optional OCI client request id for tracing; stored result lookup uses "
            "the tool response request_id."
        ),
    )
    detail: ResponseDetail = ResponseDetail.SUMMARY


class ObjectStorageUploadInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: ImageInput | None = None
    images: list[ImageInput] | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_OBJECT_STORAGE_BULK_UPLOAD_IMAGES,
    )
    destination: ObjectStorageDestinationInput | None = None
    destination_prefix: str | None = Field(default=None, min_length=1)
    overwrite: bool | None = None
    content_type: str | None = Field(default=None, min_length=1, max_length=255)
    metadata: dict[str, str] = Field(default_factory=dict)
    options: ObjectStorageUploadOptions = Field(default_factory=ObjectStorageUploadOptions)

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if "\r" in value or "\n" in value:
            raise ValueError("content_type must not contain line breaks.")
        if not value.startswith("image/"):
            raise ValueError("content_type must start with image/.")
        return value

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        for key, item in value.items():
            if not key:
                raise ValueError("metadata keys must not be empty.")
            if "\r" in key or "\n" in key or "\r" in item or "\n" in item:
                raise ValueError("metadata keys and values must not contain line breaks.")
        return value

    @model_validator(mode="after")
    def validate_upload_source(self) -> "ObjectStorageUploadInput":
        if (self.image is None) == (self.images is None):
            raise ValueError("Provide exactly one of image or images.")
        selected_images = [self.image] if self.image is not None else list(self.images or [])
        for image in selected_images:
            if image.source_type != ImageSourceType.FILE_PATH:
                raise ValueError("upload_image_to_object_storage only accepts source_type=file_path.")
        if self.images is not None:
            if not self.destination or not self.destination.namespace or not self.destination.bucket:
                raise ValueError("Bulk upload requires destination.namespace and destination.bucket.")
            if self.destination.object_name:
                raise ValueError(
                    "Bulk upload uses destination_prefix and local filenames; "
                    "destination.object_name is not allowed."
                )
        return self


class ObjectStorageListOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: str | None = None
    request_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description=(
            "Optional OCI client request id for tracing; stored result lookup uses "
            "the tool response request_id."
        ),
    )
    detail: ResponseDetail = ResponseDetail.SUMMARY
    page_size: int = Field(
        default=1000,
        ge=1,
        le=MAX_OBJECT_STORAGE_LIST_PAGE_SIZE,
        description="OCI page size used while scanning toward the requested numeric range.",
    )
    start_index: int = Field(
        default=0,
        ge=0,
        description=(
            "Zero-based index of the first object to return. It must be lower than "
            f"end_index, and the range may contain at most "
            f"{MAX_OBJECT_STORAGE_LIST_RANGE_SIZE} objects."
        ),
    )
    end_index: int = Field(
        default=10,
        ge=1,
        le=MAX_OBJECT_STORAGE_LIST_END_INDEX,
        description=(
            f"Exclusive object index, at most {MAX_OBJECT_STORAGE_LIST_END_INDEX}; "
            "0-10 returns the first 10 objects. "
            f"The difference from start_index may not exceed {MAX_OBJECT_STORAGE_LIST_RANGE_SIZE}."
        ),
    )

    @model_validator(mode="after")
    def validate_index_range(self) -> "ObjectStorageListOptions":
        if self.start_index >= self.end_index:
            raise ValueError("start_index must be less than end_index.")
        if self.end_index - self.start_index > MAX_OBJECT_STORAGE_LIST_RANGE_SIZE:
            raise ValueError(
                f"The requested object range must not exceed "
                f"{MAX_OBJECT_STORAGE_LIST_RANGE_SIZE} items."
            )
        return self


class ObjectStorageListInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    namespace: str | None = Field(default=None, min_length=1)
    bucket: str | None = Field(default=None, min_length=1)
    prefix: str | None = None
    delimiter: str | None = None
    fields: list[ObjectStorageListField] | None = None
    options: ObjectStorageListOptions = Field(default_factory=ObjectStorageListOptions)

    @field_validator("delimiter")
    @classmethod
    def validate_delimiter(cls, value: str | None) -> str | None:
        if value is not None and value != "/":
            raise ValueError("delimiter must be / when provided.")
        return value


class ObjectStorageFetchOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: str | None = None
    request_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description=(
            "Optional OCI client request id for tracing; stored result lookup uses "
            "the tool response request_id."
        ),
    )
    detail: ResponseDetail = ResponseDetail.SUMMARY


class ObjectStorageFetchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    namespace: str | None = Field(default=None, min_length=1)
    bucket: str | None = Field(default=None, min_length=1)
    object_name: str | None = Field(default=None, min_length=1)
    object_names: list[str] | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_OBJECT_STORAGE_BULK_FETCH_OBJECTS,
    )
    destination_path: str | None = Field(default=None, min_length=1)
    destination_dir: str | None = Field(default=None, min_length=1)
    overwrite: bool = False
    options: ObjectStorageFetchOptions = Field(default_factory=ObjectStorageFetchOptions)

    @field_validator("object_names")
    @classmethod
    def validate_object_names(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        if any(not item for item in value):
            raise ValueError("object_names entries must not be empty.")
        return value

    @model_validator(mode="after")
    def validate_fetch_source(self) -> "ObjectStorageFetchInput":
        if (self.object_name is None) == (self.object_names is None):
            raise ValueError("Provide exactly one of object_name or object_names.")
        if self.object_names is not None and self.destination_path is not None:
            raise ValueError("Bulk fetch uses destination_dir; destination_path is only for single fetch.")
        if self.object_name is not None and self.destination_dir is not None:
            raise ValueError("destination_dir is only for bulk fetch.")
        return self


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    retryable: bool = False


class WarningDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class ToolResultEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["succeeded", "failed"]
    tool: str
    feature_type: str
    provider: Literal["oci_vision"] = "oci_vision"
    request_id: str | None = None
    mcp_request_id: str | None = None
    detail: ResponseDetail | None = None
    results: dict[str, Any] = Field(default_factory=dict)
    truncated: bool = False
    debug_metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[WarningDetail] = Field(default_factory=list)
    errors: list[ErrorDetail] = Field(default_factory=list)


class ObjectStorageUploadItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["succeeded", "failed"]
    object: OciObjectInput | None = None
    image_input: ImageInput | None = None
    source_path: str | None = None
    size_bytes: int | None = None
    content_type: str | None = None
    etag: str | None = None
    oci_request_id: str | None = None
    errors: list[ErrorDetail] = Field(default_factory=list)


class ObjectStorageUploadEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["succeeded", "failed"]
    tool: str
    provider: Literal["oci_object_storage"] = "oci_object_storage"
    request_id: str | None = None
    mcp_request_id: str | None = None
    detail: ResponseDetail = ResponseDetail.SUMMARY
    oci_request_id: str | None = None
    oci_request_ids: list[str] = Field(default_factory=list)
    object: OciObjectInput | None = None
    image_input: ImageInput | None = None
    size_bytes: int | None = None
    content_type: str | None = None
    etag: str | None = None
    items: list[ObjectStorageUploadItem] = Field(default_factory=list)
    total_count: int = 0
    succeeded_count: int = 0
    failed_count: int = 0
    partial_failure: bool = False
    raw_result_available: bool | None = None
    raw_result_inline: dict[str, Any] | None = None
    raw_result_path: str | None = None
    warnings: list[WarningDetail] = Field(default_factory=list)
    errors: list[ErrorDetail] = Field(default_factory=list)


class ObjectStorageObjectSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    size: int | None = None
    time_created: str | None = None
    time_modified: str | None = None
    etag: str | None = None
    md5: str | None = None
    storage_tier: str | None = None
    archival_state: str | None = None


class ObjectStorageListEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["succeeded", "failed"]
    tool: str
    provider: Literal["oci_object_storage"] = "oci_object_storage"
    request_id: str | None = None
    mcp_request_id: str | None = None
    detail: ResponseDetail = ResponseDetail.SUMMARY
    oci_request_id: str | None = None
    namespace: str | None = None
    bucket: str | None = None
    prefix: str | None = None
    delimiter: str | None = None
    objects: list[ObjectStorageObjectSummary] = Field(default_factory=list)
    prefixes: list[str] = Field(default_factory=list)
    object_count: int = 0
    prefix_count: int = 0
    start_index: int = 0
    end_index: int = 0
    has_more: bool | None = False
    next_start_index: int | None = None
    scan_complete: bool = True
    prefixes_truncated: bool = False
    oci_request_ids: list[str] = Field(default_factory=list)
    raw_result_available: bool | None = None
    raw_result_inline: dict[str, Any] | None = None
    raw_result_path: str | None = None
    warnings: list[WarningDetail] = Field(default_factory=list)
    errors: list[ErrorDetail] = Field(default_factory=list)


class ObjectStorageFetchItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["succeeded", "failed"]
    object: OciObjectInput | None = None
    file_path: str | None = None
    image_input: ImageInput | None = None
    size_bytes: int | None = None
    content_type: str | None = None
    etag: str | None = None
    oci_request_id: str | None = None
    errors: list[ErrorDetail] = Field(default_factory=list)


class ObjectStorageFetchEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["succeeded", "failed"]
    tool: str
    provider: Literal["oci_object_storage"] = "oci_object_storage"
    request_id: str | None = None
    mcp_request_id: str | None = None
    detail: ResponseDetail = ResponseDetail.SUMMARY
    oci_request_id: str | None = None
    oci_request_ids: list[str] = Field(default_factory=list)
    object: OciObjectInput | None = None
    file_path: str | None = None
    image_input: ImageInput | None = None
    size_bytes: int | None = None
    content_type: str | None = None
    etag: str | None = None
    items: list[ObjectStorageFetchItem] = Field(default_factory=list)
    total_count: int = 0
    succeeded_count: int = 0
    failed_count: int = 0
    partial_failure: bool = False
    raw_result_available: bool | None = None
    raw_result_inline: dict[str, Any] | None = None
    raw_result_path: str | None = None
    warnings: list[WarningDetail] = Field(default_factory=list)
    errors: list[ErrorDetail] = Field(default_factory=list)
