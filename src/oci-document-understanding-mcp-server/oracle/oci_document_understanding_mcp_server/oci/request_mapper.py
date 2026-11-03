"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any

from oracle.oci_document_understanding_mcp_server.models import ClassificationRequest, DocumentSource, ExtractionRequest
from oracle.oci_document_understanding_mcp_server.oci.config import OciDocumentUnderstandingConfig


def extraction_configs(request: ExtractionRequest, config: OciDocumentUnderstandingConfig) -> list[dict[str, Any]]:
    """Builds sanitized OCI request metadata for extraction features."""
    return [
        {
            "operationName": "AnalyzeDocument",
            "parameters": {
                "compartmentId": config.default_compartment_id,
                "document": {
                    **_source_metadata(request.document_source),
                },
                "featureType": feature,
                "includeConfidence": request.options.include_confidence,
                "languageCode": request.options.language,
            },
        }
        for feature in request.features
    ]


def classification_config(request: ClassificationRequest, config: OciDocumentUnderstandingConfig) -> dict[str, Any]:
    """Builds sanitized OCI request metadata for classification."""
    return {
        "operationName": "AnalyzeDocument",
        "parameters": {
            "compartmentId": config.default_compartment_id,
            "document": {
                **_source_metadata(request.document_source),
            },
            "featureType": "DOCUMENT_CLASSIFICATION",
            "languageCode": request.options.language,
            "documentTypeHint": request.document_type_hint,
            "confidenceThreshold": request.options.confidence_threshold,
        },
    }


def _source_metadata(source: DocumentSource) -> dict[str, Any]:
    """Builds sanitized metadata for inline and Object Storage document sources."""
    if source.source_type == "INLINE_BASE64":
        return {
            "sourceType": "INLINE_BASE64",
            "content": "<redacted>",
            "contentLength": len(source.document or ""),
            "mimeType": source.mime_type,
            "pageRange": source.page_range,
        }

    return {
        "sourceType": "OBJECT_STORAGE",
        "namespaceName": source.namespace_name,
        "bucketName": source.bucket_name,
        "objectName": source.object_name,
        "pageRange": source.page_range,
    }
