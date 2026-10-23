"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import Any

import oci

from ..config.consts import (
    DEFAULT_ALLOWED_EXTENSIONS,
    DEFAULT_ENABLE_URL_INPUTS,
    DEFAULT_MAX_IMAGE_BYTES,
    DEFAULT_URL_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_URL_MAX_REDIRECTS,
    DEFAULT_URL_READ_TIMEOUT_SECONDS,
)
from ..config.schemas import ImageInput, ImageSourceType
from .image_validation import (
    ImageResolverError,
    ImageValidationError,
    LocalImageFile,
    MIME_BY_EXTENSION,
    sniff_image_mime,
)
from .url_image_loader import UrlFetchConfig, fetch_https_image


class ImageResolver:
    def __init__(
        self,
        *,
        base_dir: str | None,
        max_image_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
        allowed_extensions: set[str] | None = None,
        enable_url_inputs: bool = DEFAULT_ENABLE_URL_INPUTS,
        url_max_redirects: int = DEFAULT_URL_MAX_REDIRECTS,
        url_connect_timeout_seconds: float = DEFAULT_URL_CONNECT_TIMEOUT_SECONDS,
        url_read_timeout_seconds: float = DEFAULT_URL_READ_TIMEOUT_SECONDS,
    ) -> None:
        self.base_dir = Path(base_dir).expanduser().resolve() if base_dir else Path.cwd().resolve()
        self.max_image_bytes = max_image_bytes
        self.allowed_extensions = allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS
        self.url_fetch_config = UrlFetchConfig(
            enabled=enable_url_inputs,
            max_bytes=max_image_bytes,
            max_redirects=url_max_redirects,
            connect_timeout_seconds=url_connect_timeout_seconds,
            read_timeout_seconds=url_read_timeout_seconds,
            allowed_extensions=self.allowed_extensions,
        )
        self._last_image_info: dict[str, Any] | None = None

    def resolve(self, image: ImageInput):
        self._last_image_info = None
        if image.source_type == ImageSourceType.BASE64:
            details = self._inline_from_base64(image.data or "")
            self._last_image_info = self._image_info(image)
            return details
        if image.source_type == ImageSourceType.FILE_PATH:
            details = self._inline_from_file(image.path or "")
            self._last_image_info = self._image_info(image)
            return details
        if image.source_type == ImageSourceType.OCI_OBJECT:
            details = self._object_storage(image)
            self._last_image_info = self._image_info(image)
            return details
        if image.source_type == ImageSourceType.URL:
            return self._inline_from_url(image.url or "")
        raise ImageResolverError(f"Unsupported image source type: {image.source_type}")

    def resolve_local_file(self, image: ImageInput) -> LocalImageFile:
        if image.source_type != ImageSourceType.FILE_PATH:
            raise ImageResolverError("source_type=file_path is required for file upload.")
        return self._local_image_file(image.path or "")

    def image_info(self, image: ImageInput) -> dict[str, Any]:
        return dict(self._last_image_info or self._image_info(image))

    def _inline_from_base64(self, data: str):
        try:
            decoded = base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ImageResolverError("Invalid base64 image data.") from exc

        self._validate_size(len(decoded))
        try:
            sniff_image_mime(decoded)
        except ImageValidationError as exc:
            raise ImageResolverError(str(exc)) from exc
        return oci.ai_vision.models.InlineImageDetails(source="INLINE", data=data)

    def _inline_from_file(self, raw_path: str):
        local_file = self._local_image_file(raw_path)
        data = local_file.path.read_bytes()
        self._validate_size(len(data))
        try:
            detected_mime = sniff_image_mime(data)
        except ImageValidationError as exc:
            raise ImageResolverError(str(exc)) from exc
        if detected_mime != local_file.content_type:
            raise ImageResolverError("Image file changed while it was being read.")
        encoded = base64.b64encode(data).decode("ascii")
        return oci.ai_vision.models.InlineImageDetails(source="INLINE", data=encoded)

    def _inline_from_url(self, url: str):
        fetched = fetch_https_image(url, self.url_fetch_config)
        self._last_image_info = fetched.metadata
        return oci.ai_vision.models.InlineImageDetails(source="INLINE", data=fetched.data_base64)

    def _local_image_file(self, raw_path: str) -> LocalImageFile:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = self.base_dir / path
        resolved = path.resolve()

        # Resolve before checking containment so symlink escapes are blocked.
        if not self._is_relative_to(resolved, self.base_dir):
            raise ImageResolverError("file_path must stay under MCP_IMAGE_BASE_DIR.")
        if not resolved.is_file():
            raise ImageResolverError("file_path does not point to a regular file.")
        if resolved.suffix.lower() not in self.allowed_extensions:
            raise ImageResolverError("Unsupported image file extension.")

        size = resolved.stat().st_size
        self._validate_size(size)
        try:
            with resolved.open("rb") as file_obj:
                detected_mime = sniff_image_mime(file_obj.read(512))
        except ImageValidationError as exc:
            raise ImageResolverError(str(exc)) from exc
        expected_mime = MIME_BY_EXTENSION.get(resolved.suffix.lower())
        if expected_mime != detected_mime:
            raise ImageResolverError("Image file extension does not match its bytes.")

        return LocalImageFile(path=resolved, size_bytes=size, content_type=detected_mime)

    @staticmethod
    def _object_storage(image: ImageInput):
        obj = image.oci_object
        if obj is None:
            raise ImageResolverError("oci_object is required.")
        return oci.ai_vision.models.ObjectStorageImageDetails(
            source="OBJECT_STORAGE",
            namespace_name=obj.namespace,
            bucket_name=obj.bucket,
            object_name=obj.object_name,
        )

    def _validate_size(self, size: int) -> None:
        if size <= 0:
            raise ImageResolverError("Image data is empty.")
        if size > self.max_image_bytes:
            raise ImageResolverError("Image exceeds MCP_MAX_IMAGE_BYTES.")

    @staticmethod
    def _image_info(image: ImageInput) -> dict[str, Any]:
        info: dict[str, Any] = {
            "source_type": image.source_type.value,
            "path": image.path,
            "object_name": None,
            "namespace": None,
            "bucket": None,
        }
        if image.oci_object:
            info["namespace"] = image.oci_object.namespace
            info["bucket"] = image.oci_object.bucket
            info["object_name"] = image.oci_object.object_name
        if image.url:
            info["url"] = {"scheme": "https", "host": "", "path": ""}
        return info

    @staticmethod
    def _is_relative_to(path: Path, base: Path) -> bool:
        try:
            path.relative_to(base)
            return True
        except ValueError:
            return False
