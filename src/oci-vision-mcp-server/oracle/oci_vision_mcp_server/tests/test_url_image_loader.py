"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import pytest

from oracle.oci_vision_mcp_server.io.url_image_loader import (
    UrlFetchConfig,
    UrlImageFetchError,
    _parse_and_validate_url,
    _host_header,
    _request_once,
    _sniff_image_mime,
    fetch_https_image,
)


PNG_BYTES = b"\x89PNG\r\n\x1a\nexample"


def _allow_dns(monkeypatch, address: str = "93.184.216.34") -> None:
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, "", (address, 443))],
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/image.png",
        "file:///tmp/image.png",
        "ftp://example.com/image.png",
        "data:image/png;base64,aaaa",
        "https://user:pass@example.com/image.png",
        "https://example.com/image.png#fragment",
        "https:///image.png",
        "https://example.com/file.zip",
    ],
)
def test_parse_rejects_unsafe_url_shapes(monkeypatch, url: str) -> None:
    _allow_dns(monkeypatch)

    with pytest.raises(UrlImageFetchError) as exc_info:
        _parse_and_validate_url(url, allowed_extensions={".png", ".jpg", ".jpeg"})

    assert exc_info.value.code == "URL_FETCH_BLOCKED"


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.0.1",
        "169.254.169.254",
        "::1",
        "fe80::1",
        "224.0.0.1",
        "0.0.0.0",
    ],
)
def test_parse_blocks_internal_dns_targets(monkeypatch, address: str) -> None:
    _allow_dns(monkeypatch, address)

    with pytest.raises(UrlImageFetchError) as exc_info:
        _parse_and_validate_url("https://example.com/image.png", allowed_extensions={".png"})

    assert exc_info.value.code == "URL_FETCH_BLOCKED"


def test_sniff_image_mime_accepts_supported_image_bytes() -> None:
    assert _sniff_image_mime(PNG_BYTES) == "image/png"
    assert _sniff_image_mime(b"\xff\xd8\xffdata") == "image/jpeg"
    assert _sniff_image_mime(b"GIF89adata") == "image/gif"
    assert _sniff_image_mime(b"BMdata") == "image/bmp"
    assert _sniff_image_mime(b"II*\x00data") == "image/tiff"
    assert _sniff_image_mime(b"RIFFxxxxWEBPdata") == "image/webp"


@pytest.mark.parametrize("data", [b"PK\x03\x04zip", b"\x1f\x8bgzip", b"not-an-image"])
def test_sniff_image_mime_rejects_non_images(data: bytes) -> None:
    with pytest.raises(UrlImageFetchError):
        _sniff_image_mime(data)


class FakeResponse:
    def __init__(self, *, status: int, headers: dict[str, str] | None = None, chunks: list[bytes] | None = None):
        self.status = status
        self._headers = headers or {}
        self._chunks = list(chunks or [])
        self.closed = False

    def getheader(self, name: str):
        for key, value in self._headers.items():
            if key.lower() == name.lower():
                return value
        return None

    def read(self, _size: int):
        if not self._chunks:
            return b""
        return self._chunks.pop(0)

    def close(self) -> None:
        self.closed = True


def test_fetch_https_image_follows_valid_redirect(monkeypatch) -> None:
    _allow_dns(monkeypatch)
    calls = []

    def fake_request(parsed, *, config):
        del config
        calls.append(parsed.hostname)
        if len(calls) == 1:
            response = FakeResponse(status=302, headers={"Location": "https://cdn.example.com/final.png"})
            return response, response
        response = FakeResponse(
            status=200,
            headers={"Content-Type": "image/png", "Content-Length": str(len(PNG_BYTES))},
            chunks=[PNG_BYTES],
        )
        return response, response

    monkeypatch.setattr("oracle.oci_vision_mcp_server.io.url_image_loader._request_once", fake_request)

    fetched = fetch_https_image(
        "https://example.com/image.png",
        UrlFetchConfig(enabled=True, max_bytes=1024, max_redirects=3),
    )

    assert calls == ["example.com", "cdn.example.com"]
    assert fetched.content_type == "image/png"
    assert fetched.metadata["url"]["host"] == "cdn.example.com"


def test_fetch_https_image_rejects_non_image_content_type(monkeypatch) -> None:
    _allow_dns(monkeypatch)
    monkeypatch.setattr(
        "oracle.oci_vision_mcp_server.io.url_image_loader._request_once",
        lambda *_args, **_kwargs: _response_pair(
            FakeResponse(status=200, headers={"Content-Type": "text/html"}, chunks=[PNG_BYTES])
        ),
    )

    with pytest.raises(UrlImageFetchError):
        fetch_https_image("https://example.com/image.png", UrlFetchConfig(enabled=True))


def test_fetch_https_image_enforces_streamed_size_limit(monkeypatch) -> None:
    _allow_dns(monkeypatch)
    monkeypatch.setattr(
        "oracle.oci_vision_mcp_server.io.url_image_loader._request_once",
        lambda *_args, **_kwargs: _response_pair(
            FakeResponse(status=200, headers={"Content-Type": "image/png"}, chunks=[PNG_BYTES, b"x" * 10])
        ),
    )

    with pytest.raises(UrlImageFetchError):
        fetch_https_image("https://example.com/image.png", UrlFetchConfig(enabled=True, max_bytes=len(PNG_BYTES)))


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (FakeResponse(status=302), "Location"),
        (FakeResponse(status=500), "non-success"),
        (FakeResponse(status=200, headers={"Content-Encoding": "gzip"}, chunks=[PNG_BYTES]), "Compressed"),
        (FakeResponse(status=200, headers={"Content-Length": "0"}, chunks=[PNG_BYTES]), "empty"),
        (
            FakeResponse(
                status=200,
                headers={"Content-Type": "image/jpeg", "Content-Length": str(len(PNG_BYTES))},
                chunks=[PNG_BYTES],
            ),
            "does not match",
        ),
    ],
)
def test_fetch_https_image_rejects_bad_response_shapes(monkeypatch, response: FakeResponse, message: str) -> None:
    _allow_dns(monkeypatch)
    monkeypatch.setattr(
        "oracle.oci_vision_mcp_server.io.url_image_loader._request_once",
        lambda *_args, **_kwargs: _response_pair(response),
    )

    with pytest.raises(UrlImageFetchError, match=message):
        fetch_https_image("https://example.com/image.png", UrlFetchConfig(enabled=True, max_bytes=1024))


def test_fetch_https_image_rejects_disabled_and_redirect_limit(monkeypatch) -> None:
    _allow_dns(monkeypatch)

    with pytest.raises(UrlImageFetchError, match="disabled"):
        fetch_https_image("https://example.com/image.png", UrlFetchConfig(enabled=False))

    monkeypatch.setattr(
        "oracle.oci_vision_mcp_server.io.url_image_loader._request_once",
        lambda *_args, **_kwargs: _response_pair(
            FakeResponse(status=302, headers={"Location": "https://cdn.example.com/final.png"})
        ),
    )
    with pytest.raises(UrlImageFetchError, match="redirect limit"):
        fetch_https_image("https://example.com/image.png", UrlFetchConfig(enabled=True, max_redirects=0))


def test_host_header_brackets_ipv6_literal() -> None:
    assert _host_header("2001:4860:4860::8888", 443) == "[2001:4860:4860::8888]"
    assert _host_header("2001:4860:4860::8888", 8443) == "[2001:4860:4860::8888]:8443"
    assert _host_header("example.com", 443) == "example.com"


def test_request_once_builds_https_request_and_closes_on_failure(monkeypatch) -> None:
    _allow_dns(monkeypatch)
    sent: list[bytes] = []

    class FakeSocket:
        def __init__(self) -> None:
            self.closed = False

        def settimeout(self, _timeout):
            pass

        def sendall(self, data: bytes) -> None:
            sent.append(data)

        def close(self) -> None:
            self.closed = True

    raw_sock = FakeSocket()
    tls_sock = FakeSocket()
    monkeypatch.setattr("socket.create_connection", lambda *_args, **_kwargs: raw_sock)

    class FakeContext:
        def wrap_socket(self, sock, *, server_hostname):
            assert sock is raw_sock
            assert server_hostname == "example.com"
            return tls_sock

    monkeypatch.setattr("ssl.create_default_context", lambda: FakeContext())

    class ResponseOk:
        def __init__(self, sock):
            assert sock is tls_sock
            self.status = 200

        def begin(self):
            pass

    monkeypatch.setattr("http.client.HTTPResponse", ResponseOk)
    parsed = _parse_and_validate_url("https://example.com:8443/path/image.png?x=1", allowed_extensions={".png"})
    response, response_body = _request_once(parsed, config=UrlFetchConfig(enabled=True))

    assert response is response_body
    assert b"GET /path/image.png?x=1 HTTP/1.1" in sent[0]
    assert b"Host: example.com:8443" in sent[0]

    class ResponseFails:
        def __init__(self, _sock):
            pass

        def begin(self):
            raise RuntimeError("bad response")

    monkeypatch.setattr("http.client.HTTPResponse", ResponseFails)
    with pytest.raises(RuntimeError, match="bad response"):
        _request_once(parsed, config=UrlFetchConfig(enabled=True))
    assert tls_sock.closed is True


def _response_pair(response: FakeResponse):
    return response, response
