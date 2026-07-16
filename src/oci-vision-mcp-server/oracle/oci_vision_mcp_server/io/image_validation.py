"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Shared image-byte and local-file validation primitives.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ImageValidationError(ValueError):
    """Raised when bytes do not represent a supported image format."""


class ImageResolverError(ValueError):
    """Raised when an image input cannot be safely resolved."""


@dataclass(frozen=True)
class LocalImageFile:
    path: Path
    size_bytes: int
    content_type: str


MIME_BY_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
}


def sniff_image_mime(data: bytes) -> str:
    """Return the supported image MIME type identified by magic bytes."""
    _reject_archive_or_container(data)
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"BM"):
        return "image/bmp"
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return "image/tiff"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    raise ImageValidationError("Image bytes are not a supported image type.")


def _reject_archive_or_container(data: bytes) -> None:
    archive_prefixes = (
        b"PK\x03\x04",
        b"PK\x05\x06",
        b"PK\x07\x08",
        b"\x1f\x8b",
        b"Rar!\x1a\x07\x00",
        b"7z\xbc\xaf\x27\x1c",
    )
    if data.startswith(archive_prefixes) or data[257:262] == b"ustar":
        raise ImageValidationError("Archive or container files are not accepted as image inputs.")


__all__ = [
    "ImageResolverError",
    "ImageValidationError",
    "LocalImageFile",
    "MIME_BY_EXTENSION",
    "sniff_image_mime",
]
