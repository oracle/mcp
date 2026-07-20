"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class FrozenModel(BaseModel):
    """Base model for immutable MCP request and response models."""

    model_config = ConfigDict(frozen=True)


class DocumentSource(FrozenModel):
    """Normalized document input source for inline base64 and Object Storage inputs."""

    source_type: Literal["INLINE_BASE64", "OBJECT_STORAGE", "inline_base64", "object_storage"] = Field(
        ..., description="Document source type: INLINE_BASE64 or OBJECT_STORAGE."
    )
    document: str | None = Field(None, description="Base64-encoded inline document content.")
    mime_type: str | None = Field(None, description="MIME type for inline document content.")
    namespace_name: str | None = Field(None, description="OCI Object Storage namespace.")
    bucket_name: str | None = Field(None, description="OCI Object Storage bucket name.")
    object_name: str | None = Field(None, description="OCI Object Storage object name.")
    page_range: list[str] | None = Field(None, description="Optional page ranges accepted by OCI Document Understanding.")


class ExtractionOptions(FrozenModel):
    """Options accepted by the document_extract tool."""

    language: str | None = Field(None, description="Optional document language code.")
    include_confidence: bool = Field(True, description="Whether confidence scores should be included in extraction metadata.")


class ExtractionRequest(FrozenModel):
    """Normalized internal request for document extraction."""

    document_source: DocumentSource = Field(..., description="Document input source.")
    features: list[str] = Field(..., description="Document extraction feature names.")
    options: ExtractionOptions = Field(..., description="Extraction options.")


class ClassificationOptions(FrozenModel):
    """Options accepted by the document_classify tool."""

    language: str | None = Field(None, description="Optional document language code.")
    confidence_threshold: float | None = Field(None, description="Minimum classification confidence threshold.")


class ClassificationRequest(FrozenModel):
    """Normalized internal request for document classification."""

    document_source: DocumentSource = Field(..., description="Document input source.")
    options: ClassificationOptions = Field(..., description="Classification options.")
    document_type_hint: str | None = Field(None, description="Optional OCI document type hint.")


class RawOciDocumentResult(FrozenModel):
    """Raw provider result before post-processing."""

    request_id: str = Field(..., description="OCI request identifier or generated stub request id.")
    operation: str = Field(..., description="Provider operation name.")
    received_at: datetime = Field(..., description="Timestamp when the provider result was received.")
    payload: dict[str, Any] = Field(..., description="Raw provider payload.")
