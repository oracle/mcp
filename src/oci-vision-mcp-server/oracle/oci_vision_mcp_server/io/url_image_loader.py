"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Secure HTTPS URL image fetcher for Vision inline image inputs.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import ipaddress
import socket
import ssl
from dataclasses import dataclass
from typing import Any
from urllib.parse import SplitResult, urljoin, urlsplit, urlunsplit

from ..config.consts import (
    DEFAULT_ALLOWED_EXTENSIONS,
    DEFAULT_ENABLE_URL_INPUTS,
    DEFAULT_MAX_IMAGE_BYTES,
    DEFAULT_URL_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_URL_MAX_REDIRECTS,
    DEFAULT_URL_READ_TIMEOUT_SECONDS,
)
from .image_validation import ImageValidationError, MIME_BY_EXTENSION, sniff_image_mime


class UrlImageFetchError(ValueError):
    """Raised when URL image fetching is disabled or blocked."""

    code = "URL_FETCH_BLOCKED"
    retryable = False


@dataclass(frozen=True)
class FetchedUrlImage:
    data_base64: str
    size_bytes: int
    content_type: str
    sha256: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class UrlFetchConfig:
    enabled: bool = DEFAULT_ENABLE_URL_INPUTS
    max_bytes: int = DEFAULT_MAX_IMAGE_BYTES
    max_redirects: int = DEFAULT_URL_MAX_REDIRECTS
    connect_timeout_seconds: float = DEFAULT_URL_CONNECT_TIMEOUT_SECONDS
    read_timeout_seconds: float = DEFAULT_URL_READ_TIMEOUT_SECONDS
    allowed_extensions: set[str] | None = None

    @property
    def extensions(self) -> set[str]:
        return self.allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS


_REDIRECT_STATUSES = {301, 302, 303, 307, 308}
_FORBIDDEN_HOSTS = {"metadata", "instance_metadata"}
_ALLOWED_MIME_BY_EXTENSION = MIME_BY_EXTENSION


def fetch_https_image(url: str, config: UrlFetchConfig) -> FetchedUrlImage:
    if not config.enabled:
        raise UrlImageFetchError("URL image inputs are disabled. Set OCI_VISION_ENABLE_URL_INPUTS=true to enable them.")

    current = _parse_and_validate_url(url, allowed_extensions=config.extensions)
    for redirect_count in range(config.max_redirects + 1):
        response, response_body = _request_once(current, config=config)
        try:
            if response.status in _REDIRECT_STATUSES:
                if redirect_count >= config.max_redirects:
                    raise UrlImageFetchError("URL redirect limit exceeded.")
                location = response.getheader("Location")
                if not location:
                    raise UrlImageFetchError("URL redirect response did not include a Location header.")
                current = _parse_and_validate_url(
                    urljoin(urlunsplit(current), location),
                    allowed_extensions=config.extensions,
                )
                continue

            if response.status != 200:
                raise UrlImageFetchError("URL fetch failed with a non-success response.")

            content_encoding = _normalized_header(response.getheader("Content-Encoding"))
            if content_encoding and content_encoding != "identity":
                raise UrlImageFetchError("Compressed URL responses are not accepted for image inputs.")

            header_mime = _mime_type(response.getheader("Content-Type"))
            if header_mime is not None and header_mime not in set(_ALLOWED_MIME_BY_EXTENSION.values()):
                raise UrlImageFetchError("URL response Content-Type is not a supported image type.")

            _check_content_length(response.getheader("Content-Length"), max_bytes=config.max_bytes)
            data = _read_bounded(response_body, max_bytes=config.max_bytes)
            sniffed_mime = _sniff_image_mime(data)
            if header_mime is not None and header_mime != sniffed_mime:
                raise UrlImageFetchError("URL response Content-Type does not match image bytes.")

            digest = hashlib.sha256(data).hexdigest()
            redacted = redacted_url_metadata(current)
            return FetchedUrlImage(
                data_base64=base64.b64encode(data).decode("ascii"),
                size_bytes=len(data),
                content_type=sniffed_mime,
                sha256=digest,
                metadata={
                    "source_type": "url",
                    "url": redacted,
                    "host": redacted["host"],
                    "path": redacted["path"],
                    "size_bytes": len(data),
                    "content_type": sniffed_mime,
                    "sha256": digest,
                },
            )
        finally:
            response.close()

    raise UrlImageFetchError("URL redirect limit exceeded.")


def redacted_url_metadata(parsed: SplitResult | str) -> dict[str, str]:
    value = _parse_and_validate_url(parsed, allowed_extensions=DEFAULT_ALLOWED_EXTENSIONS) if isinstance(parsed, str) else parsed
    return {
        "scheme": value.scheme,
        "host": value.hostname or "",
        "path": value.path or "/",
    }


def _parse_and_validate_url(url: str | SplitResult, *, allowed_extensions: set[str]) -> SplitResult:
    try:
        parsed = url if isinstance(url, SplitResult) else urlsplit(str(url).strip())
        _ = parsed.port
    except ValueError as exc:
        raise UrlImageFetchError("URL is malformed or contains an invalid port.") from exc

    if parsed.scheme != "https":
        raise UrlImageFetchError("Only https:// image URLs are allowed.")
    if not parsed.hostname:
        raise UrlImageFetchError("URL host is required.")
    if parsed.username or parsed.password:
        raise UrlImageFetchError("URL credentials are not allowed.")
    if parsed.fragment:
        raise UrlImageFetchError("URL fragments are not allowed.")
    if parsed.hostname.lower() in _FORBIDDEN_HOSTS:
        raise UrlImageFetchError("URL host is not allowed.")

    suffix = _path_suffix(parsed.path)
    if suffix and suffix not in allowed_extensions:
        raise UrlImageFetchError("URL path has an unsupported image extension.")
    _resolve_allowed_addresses(parsed.hostname, parsed.port or 443)
    return parsed


def _request_once(parsed: SplitResult, *, config: UrlFetchConfig) -> tuple[http.client.HTTPResponse, Any]:
    host = parsed.hostname or ""
    port = parsed.port or 443
    address = _resolve_allowed_addresses(host, port)[0]
    context = ssl.create_default_context()
    raw_sock = socket.create_connection((address, port), timeout=config.connect_timeout_seconds)
    raw_sock.settimeout(config.read_timeout_seconds)
    tls_sock = context.wrap_socket(raw_sock, server_hostname=host)
    try:
        target = parsed.path or "/"
        if parsed.query:
            target = f"{target}?{parsed.query}"
        request = (
            f"GET {target} HTTP/1.1\r\n"
            f"Host: {_host_header(host, port)}\r\n"
            "Accept: image/*\r\n"
            "User-Agent: oci-vision-mcp-url-fetcher\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        tls_sock.sendall(request.encode("ascii"))
        response = http.client.HTTPResponse(tls_sock)
        response.begin()
        return response, response
    except Exception:
        tls_sock.close()
        raise


def _resolve_allowed_addresses(host: str, port: int) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UrlImageFetchError("URL host could not be resolved.") from exc

    addresses = []
    for info in infos:
        address = str(info[4][0])
        _validate_public_ip(address)
        if address not in addresses:
            addresses.append(address)
    if not addresses:
        raise UrlImageFetchError("URL host did not resolve to an allowed address.")
    return addresses


def _validate_public_ip(address: str) -> None:
    ip = ipaddress.ip_address(address)
    blocked = (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )
    if blocked or str(ip) == "255.255.255.255":
        raise UrlImageFetchError("URL host resolved to a blocked network address.")


def _check_content_length(value: str | None, *, max_bytes: int) -> None:
    if not value:
        return
    try:
        parsed = int(value)
    except ValueError:
        return
    if parsed <= 0:
        raise UrlImageFetchError("URL image data is empty.")
    if parsed > max_bytes:
        raise UrlImageFetchError("URL image exceeds MCP_MAX_IMAGE_BYTES.")


def _read_bounded(response: Any, *, max_bytes: int) -> bytes:
    buffer = bytearray()
    while True:
        chunk = response.read(1024 * 64)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise UrlImageFetchError("URL image exceeds MCP_MAX_IMAGE_BYTES.")
    if not buffer:
        raise UrlImageFetchError("URL image data is empty.")
    return bytes(buffer)


def _sniff_image_mime(data: bytes) -> str:
    try:
        return sniff_image_mime(data)
    except ImageValidationError as exc:
        message = str(exc).replace("Image bytes", "URL response bytes").replace(
            "as image inputs", "as URL image inputs"
        )
        raise UrlImageFetchError(message) from exc


def _mime_type(value: str | None) -> str | None:
    if not value:
        return None
    return value.split(";", 1)[0].strip().lower() or None


def _normalized_header(value: str | None) -> str | None:
    return value.strip().lower() if value else None


def _path_suffix(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    if "." not in name:
        return ""
    return f".{name.rsplit('.', 1)[-1].lower()}"


def _host_header(host: str, port: int) -> str:
    display_host = f"[{host}]" if ":" in host and not host.startswith("[") else host
    if port == 443:
        return display_host
    return f"{display_host}:{port}"
