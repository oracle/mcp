"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Object Storage reference and download helpers.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from uuid import uuid4

from ..config.schemas import OciObjectInput
from .result_store import safe_request_key


class ObjectStorageDownloadError(ValueError):
    """Raised when an Object Storage object cannot be safely downloaded."""


def resolve_download_path(
    *,
    download_dir: str,
    object_name: str,
    request_id: str,
    destination_path: str | None = None,
) -> Path:
    base_dir = Path(download_dir).expanduser().resolve(strict=False)
    if destination_path:
        candidate = Path(destination_path).expanduser()
        if not candidate.is_absolute():
            candidate = base_dir / candidate
    else:
        object_file_name = PurePosixPath(object_name).name or "object"
        candidate = base_dir / f"{safe_request_key(request_id)[:12]}-{object_file_name}"
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(base_dir)
    except ValueError as exc:
        raise ObjectStorageDownloadError("destination_path must stay under OCI_OBJECT_STORAGE_DOWNLOAD_DIR.") from exc
    return resolved


def resolve_bulk_download_dir(
    *,
    download_dir: str,
    request_id: str,
    destination_dir: str | None = None,
) -> Path:
    base_dir = Path(download_dir).expanduser().resolve(strict=False)
    if destination_dir:
        candidate = Path(destination_dir).expanduser()
        if not candidate.is_absolute():
            candidate = base_dir / candidate
    else:
        candidate = base_dir / safe_request_key(request_id)[:12]
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(base_dir)
    except ValueError as exc:
        raise ObjectStorageDownloadError("destination_dir must stay under OCI_OBJECT_STORAGE_DOWNLOAD_DIR.") from exc
    return resolved


def resolve_bulk_download_path(*, bulk_dir: Path, object_name: str) -> Path:
    relative = safe_object_relative_path(object_name)
    return _validated_destination(bulk_dir / relative, root=bulk_dir)


def safe_object_relative_path(object_name: str) -> Path:
    pure_path = PurePosixPath(object_name)
    parts = [part for part in pure_path.parts if part not in {"", "."}]
    if not object_name or pure_path.is_absolute() or not parts or ".." in parts:
        raise ObjectStorageDownloadError("object_name must be a safe relative Object Storage path.")
    return Path(*parts)


def write_object_response_to_file(
    *,
    response: Any,
    destination: Path,
    max_bytes: int,
    overwrite: bool,
    allowed_root: Path | None = None,
) -> int:
    if allowed_root is not None:
        destination = _validated_destination(destination, root=allowed_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if allowed_root is not None:
        destination = _validated_destination(destination, root=allowed_root)
    if destination.exists() and not overwrite:
        raise ObjectStorageDownloadError(
            "Destination file already exists. Use a different destination_path or set overwrite=true."
        )

    temp_path = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
    bytes_written = 0
    try:
        with temp_path.open("wb") as file_obj:
            for chunk in _response_chunks(getattr(response, "data", response)):
                if not chunk:
                    continue
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    raise ObjectStorageDownloadError("Object exceeds OCI_OBJECT_STORAGE_FETCH_MAX_BYTES.")
                file_obj.write(chunk)
        try:
            temp_path.chmod(0o600)
        except OSError:
            pass
        temp_path.replace(destination)
    except Exception:
        try:
            temp_path.unlink()
        except OSError:
            pass
        raise

    try:
        destination.chmod(0o600)
    except OSError:
        pass
    return bytes_written


def _response_chunks(data: Any) -> Iterable[bytes]:
    raw = getattr(data, "raw", None)
    if raw is not None and hasattr(raw, "stream"):
        yield from raw.stream(1024 * 1024, decode_content=False)
        return
    if hasattr(data, "stream"):
        yield from data.stream(1024 * 1024, decode_content=False)
        return
    if hasattr(data, "read"):
        while True:
            chunk = data.read(1024 * 1024)
            if not chunk:
                break
            yield _bytes_chunk(chunk)
        return
    content = getattr(data, "content", None)
    if content is not None:
        yield _bytes_chunk(content)
        return
    if isinstance(data, (bytes, bytearray, memoryview)):
        yield _bytes_chunk(data)
        return
    raise ObjectStorageDownloadError("Unsupported Object Storage response body.")


def _bytes_chunk(value: bytes | bytearray | memoryview | str) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, (bytearray, memoryview)):
        return bytes(value)
    return str(value).encode("utf-8")


def _validated_destination(destination: Path, *, root: Path) -> Path:
    """Resolve a destination and reject existing symlinks or root escapes."""
    resolved_root = root.expanduser().resolve(strict=False)
    unresolved = destination.expanduser()
    if not unresolved.is_absolute():
        unresolved = resolved_root / unresolved

    try:
        relative = unresolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ObjectStorageDownloadError(
            "Download destination must stay under the selected bulk download directory."
        ) from exc

    current = resolved_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ObjectStorageDownloadError("Download destination must not contain symbolic links.")

    resolved = unresolved.resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ObjectStorageDownloadError(
            "Download destination must stay under the selected bulk download directory."
        ) from exc
    return resolved


__all__ = [
    "ObjectStorageDownloadError",
    "OciObjectInput",
    "resolve_bulk_download_dir",
    "resolve_bulk_download_path",
    "resolve_download_path",
    "safe_object_relative_path",
    "write_object_response_to_file",
]
