"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import sys
from typing import Any

import oci

from ..authentication.session_signer import session_auth_error_from_service_error
from ..config.consts import TOOL_LIST_OBJECT_STORAGE_OBJECTS, TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE
from ..oci_mapper.vision_results import normalize_exception
from ..config.schemas import (
    ErrorDetail,
    ObjectStorageListEnvelope,
    ObjectStorageUploadEnvelope,
    WarningDetail,
)


class ObjectStorageUploadError(ValueError):
    code = "OBJECT_ALREADY_EXISTS"
    retryable = False


def log_tool_failure(tool: str, exc: Exception) -> None:
    print(f"[oci-vision-mcp] {tool} failed: {type(exc).__name__}: {exc}", file=sys.stderr)


def result_persistence_warning(tool: str, exc: Exception) -> WarningDetail:
    """Log a local storage failure without changing a completed OCI operation."""
    print(
        f"[oci-vision-mcp] {tool} result persistence failed: {type(exc).__name__}: {exc}",
        file=sys.stderr,
    )
    return WarningDetail(
        code="RESULT_PERSISTENCE_FAILED",
        message=(
            "The operation completed, but its local raw result or index could not be stored. "
            "Do not retry the external operation solely because of this warning."
        ),
    )


def redact_diagnostic_fields(value: Any) -> Any:
    """Recursively remove provider diagnostics from non-raw responses."""
    if isinstance(value, list):
        return [redact_diagnostic_fields(item) for item in value]
    if not isinstance(value, dict):
        return value
    diagnostic_keys = {
        "client_request_id",
        "oci_client_request_id",
        "oci_request_id",
        "oci_request_ids",
        "opc_request_id",
        "opc-request-id",
        "opc-work-request-id",
        "work_request_id",
        "raw_result_available",
        "raw_result_inline",
        "raw_result_path",
        "headers",
        "_headers",
    }
    return {
        key: redact_diagnostic_fields(item)
        for key, item in value.items()
        if key not in diagnostic_keys
    }


def vision_service_error_envelope(
    exc: oci.exceptions.ServiceError,
    *,
    tool: str,
    feature_type: str,
    profile: str | None,
    region: str | None,
    request_id: str | None = None,
):
    auth_exc = session_auth_error_from_service_error(exc, profile=profile, region=region)
    if auth_exc:
        return normalize_exception(tool=tool, feature_type=feature_type, exc=auth_exc, request_id=request_id)
    log_tool_failure(tool, exc)
    return normalize_exception(tool=tool, feature_type=feature_type, exc=exc, request_id=request_id)


def upload_service_error_envelope(
    exc: oci.exceptions.ServiceError,
    *,
    profile: str | None,
    region: str | None,
    request_id: str | None = None,
) -> ObjectStorageUploadEnvelope:
    auth_exc = session_auth_error_from_service_error(exc, profile=profile, region=region)
    if auth_exc:
        return upload_exception_envelope(auth_exc, request_id=request_id)
    if is_existing_object_error(exc):
        return upload_exception_envelope(
            ObjectStorageUploadError(
                "Object already exists and overwrite=false. Use a different object_name or set overwrite=true."
            ),
            request_id=request_id,
        )
    log_tool_failure(TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE, exc)
    return upload_exception_envelope(exc, request_id=request_id)


def list_service_error_envelope(
    exc: oci.exceptions.ServiceError,
    *,
    profile: str | None,
    region: str | None,
    request_id: str | None = None,
) -> ObjectStorageListEnvelope:
    auth_exc = session_auth_error_from_service_error(exc, profile=profile, region=region)
    if auth_exc:
        return list_exception_envelope(auth_exc, request_id=request_id)
    log_tool_failure(TOOL_LIST_OBJECT_STORAGE_OBJECTS, exc)
    return list_exception_envelope(exc, request_id=request_id)


def upload_exception_envelope(
    exc: Exception,
    *,
    request_id: str | None = None,
) -> ObjectStorageUploadEnvelope:
    return ObjectStorageUploadEnvelope(
        status="failed",
        tool=TOOL_UPLOAD_IMAGE_TO_OBJECT_STORAGE,
        request_id=request_id,
        mcp_request_id=request_id,
        errors=[
            ErrorDetail(
                code=str(getattr(exc, "code", type(exc).__name__)),
                message=str(exc),
                retryable=bool(getattr(exc, "retryable", False)),
            )
        ],
    )


def list_exception_envelope(
    exc: Exception,
    *,
    request_id: str | None = None,
) -> ObjectStorageListEnvelope:
    return ObjectStorageListEnvelope(
        status="failed",
        tool=TOOL_LIST_OBJECT_STORAGE_OBJECTS,
        request_id=request_id,
        mcp_request_id=request_id,
        errors=[
            ErrorDetail(
                code=str(getattr(exc, "code", type(exc).__name__)),
                message=str(exc),
                retryable=bool(getattr(exc, "retryable", False)),
            )
        ],
    )


def upload_summary_text(envelope: ObjectStorageUploadEnvelope) -> str:
    if envelope.items:
        if envelope.status == "failed":
            return f"{envelope.tool} failed: uploaded 0/{envelope.total_count} images."
        if envelope.partial_failure:
            return f"Uploaded {envelope.succeeded_count}/{envelope.total_count} images with {envelope.failed_count} failures."
        return f"Uploaded {envelope.succeeded_count} images."
    if envelope.status == "failed":
        first = envelope.errors[0].message if envelope.errors else "Unknown error"
        return f"{envelope.tool} failed: {first}"
    if envelope.object:
        return f"Uploaded image to {envelope.object.bucket}/{envelope.object.object_name}."
    return f"{envelope.tool} succeeded."


def list_summary_text(envelope: ObjectStorageListEnvelope) -> str:
    if envelope.status == "failed":
        first = envelope.errors[0].message if envelope.errors else "Unknown error"
        return f"{envelope.tool} failed: {first}"
    location = f"{envelope.bucket}/{envelope.prefix or ''}" if envelope.bucket else envelope.prefix or ""
    return f"Listed {envelope.object_count} objects and {envelope.prefix_count} prefixes from {location}."


def response_request_id(response: Any) -> str | None:
    for attr in ("opc_request_id", "request_id"):
        value = getattr(response, attr, None)
        if value:
            return str(value)
    return response_header(response, "opc-request-id")


def response_header(response: Any, name: str) -> str | None:
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    for key, value in headers.items():
        if key.lower() == name.lower() and value is not None:
            return str(value)
    return None


def is_existing_object_error(exc: oci.exceptions.ServiceError) -> bool:
    return getattr(exc, "status", None) == 412 or getattr(exc, "code", None) in {
        "PreconditionFailed",
        "NoEtagMatch",
    }
