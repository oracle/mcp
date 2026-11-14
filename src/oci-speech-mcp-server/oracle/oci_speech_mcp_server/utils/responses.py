"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import errno
import logging
import os
import uuid
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import oci

from ..models import OperationResult

logger = logging.getLogger(__name__)


def safe_error_details(error: Exception) -> dict[str, Any]:
    """Return failure metadata without paths, endpoints, or response bodies."""
    details: dict[str, Any] = {"type": type(error).__name__}
    if isinstance(error, oci.exceptions.ServiceError):
        details.update(
            status=error.status,
            code=error.code,
            request_id=error.request_id,
        )
    elif isinstance(error, oci.exceptions.RequestException):
        return details
    elif isinstance(error, OSError):
        details.update(
            errno=error.errno,
            errno_name=errno.errorcode.get(error.errno, "UNKNOWN"),
        )
    return details


def response_header(response: Any, name: str) -> str | None:
    headers = getattr(response, "headers", {}) or {}
    return headers.get(name) or headers.get(name.lower()) or headers.get(name.title())


def to_dict(data: Any) -> Any:
    if data is None:
        return None
    return oci.util.to_dict(data)


def operation_result(
    operation: str,
    response: Any,
    *,
    notes: list[str] | None = None,
) -> OperationResult:
    return OperationResult(
        operation=operation,
        data=to_dict(getattr(response, "data", None)),
        status=getattr(response, "status", None),
        opc_request_id=response_header(response, "opc-request-id"),
        etag=response_header(response, "etag"),
        next_page=response_header(response, "opc-next-page"),
        notes=notes or [],
    )


def raise_safe(operation: str, error: Exception) -> None:
    if isinstance(error, oci.exceptions.ServiceError):
        raise RuntimeError(
            f"{operation} failed with OCI status {error.status}, code {error.code}, "
            f"request {error.request_id or 'unknown'}."
        ) from None
    if isinstance(error, oci.exceptions.RequestException):
        raise RuntimeError(
            f"{operation} failed due to an OCI transport error. "
            "Check the server log and retry only after reconciling any possible "
            "remote side effect."
        ) from None
    if isinstance(error, TimeoutError):
        raise RuntimeError(f"{operation} failed: {error}") from None
    if isinstance(error, OSError):
        details = safe_error_details(error)
        raise RuntimeError(
            f"{operation} failed with local I/O error "
            f"{details['errno_name']} (errno {details['errno']})."
        ) from None
    if isinstance(error, ValueError):
        raise RuntimeError(f"{operation} failed: {error}") from None
    logger.error(
        "Unexpected %s in %s; exception text omitted to protect sensitive data",
        type(error).__name__,
        operation,
    )
    raise RuntimeError(f"{operation} failed unexpectedly. Check the server log.") from None


def call_oci(
    operation: str,
    call: Callable[[], Any],
    *,
    notes: list[str] | None = None,
) -> OperationResult:
    try:
        return operation_result(operation, call(), notes=notes)
    except Exception as error:
        raise_safe(operation, error)


def page_items(data: Any) -> list[Any]:
    items = getattr(data, "items", data)
    return list(items or [])


def list_oci(
    operation: str,
    call: Callable[..., Any],
    kwargs: dict[str, Any],
    *,
    max_items: int,
) -> OperationResult:
    try:
        items: list[Any] = []
        page: str | None = kwargs.pop("page", None)
        visited_pages: set[str] = set()
        last_response: Any = None
        notes: list[str] = []
        while len(items) < max_items:
            if page:
                if page in visited_pages:
                    raise ValueError("OCI pagination returned a repeated page token.")
                visited_pages.add(page)
            remaining = max_items - len(items)
            request = {**kwargs, "limit": min(100, remaining)}
            if page:
                request["page"] = page
            last_response = call(**request)
            returned = page_items(last_response.data)
            items.extend(returned[:remaining])
            next_page = response_header(last_response, "opc-next-page")
            if len(returned) > remaining:
                page = None
                notes.append(
                    "OCI returned more items than requested. The result was truncated "
                    "to max_items and cannot be resumed losslessly."
                )
                break
            page = next_page
            if not page:
                break
        if page:
            notes.append(
                "The result reached max_items; pass next_page with the same filters "
                "to continue."
            )
        return OperationResult(
            operation=operation,
            data=to_dict(items),
            status=getattr(last_response, "status", None),
            opc_request_id=response_header(last_response, "opc-request-id"),
            next_page=page,
            count=len(items),
            notes=notes,
        )
    except Exception as error:
        raise_safe(operation, error)


def write_stream(data: Any, path: Path, *, overwrite: bool = False) -> int:
    raw = getattr(data, "raw", data)
    stream = getattr(raw, "stream", None)
    if callable(stream):
        chunks: Iterable[bytes] = stream(1024 * 1024, decode_content=False)
    elif callable(getattr(data, "iter_content", None)):
        chunks = data.iter_content(chunk_size=1024 * 1024)
    elif isinstance(data, bytes):
        chunks = [data]
    else:
        raise ValueError("OCI returned an unsupported streaming response.")
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(temporary, flags, 0o600)
    try:
        written = 0
        with os.fdopen(descriptor, "wb") as output:
            descriptor = -1
            for chunk in chunks:
                if chunk:
                    output.write(chunk)
                    written += len(chunk)
        if overwrite:
            os.replace(temporary, path)
        else:
            os.link(temporary, path, follow_symlinks=False)
            temporary.unlink()
        return written
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)
        raise
