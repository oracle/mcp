from __future__ import annotations

import os
import ssl
import urllib.error
import urllib.request
from typing import Optional, Dict, Tuple


def build_ssl_context() -> ssl.SSLContext:
    """
    Build an SSL context honoring:
      - MCP_SSL_VERIFY: "false"/"0"/"no"/"off" to disable verification (default: verify)
      - MCP_CA_BUNDLE: absolute path to a PEM CA bundle to trust
    """
    verify_env = os.environ.get("MCP_SSL_VERIFY", "true").strip().lower()
    verify = verify_env not in ("0", "false", "no", "off")
    ca_bundle = os.environ.get("MCP_CA_BUNDLE")

    if verify:
        try:
            return ssl.create_default_context(cafile=ca_bundle) if ca_bundle else ssl.create_default_context()
        except Exception:
            # Fallback to default context if cafile fails
            return ssl.create_default_context()

    # Verification disabled (use sparingly; for corporate proxies/self-signed chains)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    if ca_bundle:
        try:
            ctx.load_verify_locations(ca_bundle)
        except Exception:
            # Ignore if loading custom CA fails when verification is off
            pass
    return ctx


# Module-level SSL context reused by http_request
SSL_CONTEXT = build_ssl_context()


def http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[bytes] = None,
) -> Tuple[int, str, bytes]:
    """
    Lightweight HTTP request using urllib with the module SSL context.

    Returns (status_code, content_type, body_bytes).
    On network errors, returns status=0 and body=error message.
    """
    req = urllib.request.Request(url=url, method=method, data=data)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, context=SSL_CONTEXT) as resp:
            body = resp.read()
            status = getattr(resp, "status", 200)
            ctype = resp.headers.get("content-type", "")
            return status, ctype, body
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        ctype = e.headers.get("content-type", "") if hasattr(e, "headers") and e.headers else ""
        return e.code, ctype, body
    except Exception as e:
        return 0, "", str(e).encode("utf-8")
