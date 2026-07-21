"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import base64

import pytest

from oracle.oci_vision_mcp_server.io.image_loader import ImageResolver, ImageResolverError
from oracle.oci_vision_mcp_server.io.url_image_loader import FetchedUrlImage, UrlImageFetchError
from oracle.oci_vision_mcp_server.config.schemas import ImageInput


PNG_BYTES = b"\x89PNG\r\n\x1a\nexample"


def test_resolves_base64_to_inline_image_details() -> None:
    data = base64.b64encode(PNG_BYTES).decode("ascii")
    image = ImageInput.model_validate({"source_type": "base64", "data": data})

    details = ImageResolver(base_dir=None).resolve(image)

    assert details.source == "INLINE"
    assert details.data == data


def test_rejects_invalid_base64() -> None:
    image = ImageInput.model_validate({"source_type": "base64", "data": "not-base64!"})

    with pytest.raises(ImageResolverError):
        ImageResolver(base_dir=None).resolve(image)


def test_rejects_base64_that_is_not_an_image() -> None:
    data = base64.b64encode(b"plain text, not image bytes").decode("ascii")
    image = ImageInput.model_validate({"source_type": "base64", "data": data})

    with pytest.raises(ImageResolverError, match="supported image type"):
        ImageResolver(base_dir=None).resolve(image)


def test_resolves_file_path_under_sandbox(tmp_path) -> None:
    image_path = tmp_path / "image.png"
    image_path.write_bytes(PNG_BYTES)
    image = ImageInput.model_validate({"source_type": "file_path", "path": str(image_path)})

    details = ImageResolver(base_dir=str(tmp_path)).resolve(image)

    assert details.source == "INLINE"
    assert base64.b64decode(details.data) == PNG_BYTES


def test_resolves_local_file_for_upload(tmp_path) -> None:
    image_path = tmp_path / "image.png"
    image_path.write_bytes(PNG_BYTES)
    image = ImageInput.model_validate({"source_type": "file_path", "path": str(image_path)})

    local_file = ImageResolver(base_dir=str(tmp_path)).resolve_local_file(image)

    assert local_file.path == image_path
    assert local_file.size_bytes == len(PNG_BYTES)
    assert local_file.content_type == "image/png"


def test_rejects_non_file_source_for_upload() -> None:
    image = ImageInput.model_validate({"source_type": "base64", "data": "aGVsbG8="})

    with pytest.raises(ImageResolverError):
        ImageResolver(base_dir=None).resolve_local_file(image)


def test_resolves_file_path_under_current_working_directory(monkeypatch, tmp_path) -> None:
    image_path = tmp_path / "image.png"
    image_path.write_bytes(PNG_BYTES)
    image = ImageInput.model_validate({"source_type": "file_path", "path": "image.png"})

    monkeypatch.chdir(tmp_path)

    details = ImageResolver(base_dir=None).resolve(image)

    assert details.source == "INLINE"
    assert base64.b64decode(details.data) == PNG_BYTES


def test_resolves_relative_file_path_under_configured_base_dir(tmp_path) -> None:
    image_path = tmp_path / "image.png"
    image_path.write_bytes(PNG_BYTES)
    image = ImageInput.model_validate({"source_type": "file_path", "path": "image.png"})

    details = ImageResolver(base_dir=str(tmp_path)).resolve(image)

    assert details.source == "INLINE"
    assert base64.b64decode(details.data) == PNG_BYTES


def test_rejects_file_path_outside_sandbox(tmp_path) -> None:
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    outside = tmp_path / "outside.png"
    outside.write_bytes(PNG_BYTES)
    image = ImageInput.model_validate({"source_type": "file_path", "path": str(outside)})

    with pytest.raises(ImageResolverError):
        ImageResolver(base_dir=str(base_dir)).resolve(image)


def test_rejects_symlink_escape(tmp_path) -> None:
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    outside = tmp_path / "outside.png"
    outside.write_bytes(PNG_BYTES)
    link = base_dir / "linked.png"
    link.symlink_to(outside)
    image = ImageInput.model_validate({"source_type": "file_path", "path": str(link)})

    with pytest.raises(ImageResolverError):
        ImageResolver(base_dir=str(base_dir)).resolve(image)


def test_rejects_file_when_extension_does_not_match_image_bytes(tmp_path) -> None:
    image_path = tmp_path / "disguised.png"
    image_path.write_bytes(b"\xff\xd8\xffjpeg")
    image = ImageInput.model_validate({"source_type": "file_path", "path": str(image_path)})

    with pytest.raises(ImageResolverError, match="extension does not match"):
        ImageResolver(base_dir=str(tmp_path)).resolve(image)


def test_resolves_oci_object_to_object_storage_details() -> None:
    image = ImageInput.model_validate(
        {
            "source_type": "oci_object",
            "oci_object": {
                "namespace": "ns",
                "bucket": "bucket",
                "object_name": "images/photo.png",
            },
        }
    )

    details = ImageResolver(base_dir=None).resolve(image)

    assert details.source == "OBJECT_STORAGE"
    assert details.namespace_name == "ns"
    assert details.bucket_name == "bucket"
    assert details.object_name == "images/photo.png"


def test_url_input_is_disabled_by_default() -> None:
    image = ImageInput.model_validate({"source_type": "url", "url": "https://example.com/image.png"})

    with pytest.raises(UrlImageFetchError) as exc_info:
        ImageResolver(base_dir=None).resolve(image)

    assert exc_info.value.code == "URL_FETCH_BLOCKED"


def test_url_input_resolves_to_inline_when_enabled(monkeypatch) -> None:
    image = ImageInput.model_validate({"source_type": "url", "url": "https://example.com/image.png?token=secret"})

    def fake_fetch(url, config):
        assert url == "https://example.com/image.png?token=secret"
        assert config.enabled is True
        return FetchedUrlImage(
            data_base64=base64.b64encode(PNG_BYTES).decode("ascii"),
            size_bytes=len(PNG_BYTES),
            content_type="image/png",
            sha256="abc123",
            metadata={
                "source_type": "url",
                "url": {"scheme": "https", "host": "example.com", "path": "/image.png"},
                "host": "example.com",
                "path": "/image.png",
                "size_bytes": len(PNG_BYTES),
                "content_type": "image/png",
                "sha256": "abc123",
            },
        )

    monkeypatch.setattr("oracle.oci_vision_mcp_server.io.image_loader.fetch_https_image", fake_fetch)

    resolver = ImageResolver(base_dir=None, enable_url_inputs=True)
    details = resolver.resolve(image)

    assert details.source == "INLINE"
    assert base64.b64decode(details.data) == PNG_BYTES
    assert resolver.image_info(image)["url"] == {"scheme": "https", "host": "example.com", "path": "/image.png"}
