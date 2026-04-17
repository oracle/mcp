"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

HTTP and request-signing utilities for GoldenGate and OCI calls.
"""

import base64
import hashlib
import json
from datetime import datetime, timezone
from email.utils import format_datetime
from typing import Any

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from .consts import DEFAULT_TIMEOUT_SECONDS


def _classify_request_error(exc: requests.exceptions.RequestException) -> str:
    """Map requests/urllib3 exceptions to concise, user-friendly connection errors."""
    if isinstance(exc, requests.exceptions.ConnectTimeout):
        return "Connection timed out"
    if isinstance(exc, requests.exceptions.ReadTimeout):
        return "Request timed out while waiting for response"

    if isinstance(exc, requests.exceptions.ConnectionError):
        msg = str(exc).lower()
        if "name or service not known" in msg or "nodename nor servname provided" in msg or "getaddrinfo failed" in msg:
            return "DNS resolution failed"
        if "connection refused" in msg:
            return "Connection refused"
        return "Network connection error"

    if isinstance(exc, requests.exceptions.InvalidURL):
        return "Invalid deployment URL"

    return "HTTP request failed"


def sign_oci_request(cfg: dict, method: str, path_with_query: str, host: str, body: str | None = None) -> dict[str, str]:
    """Create OCI Signature headers for a request.

    Used for OCI Secrets retrieval in basic-auth mode.
    """
    if not cfg.get("tenancyOCID") or not cfg.get("userOCID") or not cfg.get("keyFingerprint") or not cfg.get("privateKeyPEM"):
        raise ValueError("OCI signer is not fully configured")

    date = format_datetime(datetime.now(timezone.utc), usegmt=True)
    headers_to_sign = ["(request-target)", "host", "date"]
    signing = f"(request-target): {method.lower()} {path_with_query}\nhost: {host}\ndate: {date}"
    headers: dict[str, str] = {"date": date}

    if body is not None:
        sha256 = base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode("utf-8")
        headers_to_sign.extend(["content-length", "content-type", "x-content-sha256"])
        signing += (
            f"\ncontent-length: {len(body.encode('utf-8'))}"
            "\ncontent-type: application/json"
            f"\nx-content-sha256: {sha256}"
        )
        headers["content-length"] = str(len(body.encode("utf-8")))
        headers["content-type"] = "application/json"
        headers["x-content-sha256"] = sha256

    key_id = f"{cfg['tenancyOCID']}/{cfg['userOCID']}/{cfg['keyFingerprint']}"
    private_key: Any = load_pem_private_key(
        cfg["privateKeyPEM"].encode("utf-8"),
        password=(cfg.get("passphrase") or "").encode("utf-8") if cfg.get("passphrase") else None,
    )
    if not isinstance(private_key, RSAPrivateKey):
        raise ValueError("OCI signer private key must be an RSA private key")
    signature = private_key.sign(signing.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
    signature_b64 = base64.b64encode(signature).decode("utf-8")

    signed_headers = " ".join(headers_to_sign)
    headers["authorization"] = (
        f'Signature version="1",headers="{signed_headers}",'
        f'keyId="{key_id}",algorithm="rsa-sha256",signature="{signature_b64}"'
    )
    headers["host"] = host
    return headers


class HttpClient:
    """Minimal HTTP client wrapper around requests for GoldenGate REST APIs."""
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.base_url = cfg["baseUrl"].rstrip("/")
        self.timeout = DEFAULT_TIMEOUT_SECONDS
        self.session = requests.Session()

    def _headers(self, method: str, url: str, body: dict | None = None, custom_headers: dict | None = None) -> tuple[dict, str | None]:
        """Build request headers and serialized body."""
        headers = {"Accept": "application/json"}
        body_str = json.dumps(body) if body is not None else None

        if custom_headers:
            headers.update(custom_headers)
        return headers, body_str

    def _request(self, method: str, path: str, body: dict | None = None, headers: dict | None = None, response_text: bool = False):
        """Execute an HTTP request and normalize response/error handling."""
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        req_headers, body_str = self._headers(method, url, body, headers)
        auth: tuple[str, str] | None = None
        if self.cfg.get("authMode") == "basic":
            auth = (str(self.cfg.get("username") or ""), str(self.cfg.get("password") or ""))
        try:
            resp = self.session.request(
                method=method,
                url=url,
                data=body_str,
                headers=req_headers,
                auth=auth,
                timeout=self.timeout,
            )
        except requests.exceptions.RequestException as exc:
            reason = _classify_request_error(exc)
            raise RuntimeError(f"{method.upper()} {path} failed: {reason}") from exc
        if not (200 <= resp.status_code < 300):
            raise RuntimeError(f"{method.upper()} {path} failed: {resp.status_code} {resp.text}")
        if response_text:
            return resp.text
        try:
            return resp.json()
        except Exception:
            return resp.text

    def get(self, path: str, headers: dict | None = None, response_text: bool = False):
        """Execute HTTP GET."""
        return self._request("GET", path, None, headers, response_text)

    def post(self, path: str, body: dict | None = None):
        """Execute HTTP POST."""
        return self._request("POST", path, body)

    def patch(self, path: str, body: dict | None = None):
        """Execute HTTP PATCH."""
        return self._request("PATCH", path, body)

    def delete(self, path: str):
        """Execute HTTP DELETE."""
        return self._request("DELETE", path)
