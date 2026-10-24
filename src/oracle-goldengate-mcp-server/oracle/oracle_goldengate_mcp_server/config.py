"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Runtime configuration loader for the GoldenGate MCP server.

This module reads environment variables, resolves credentials, and builds
the configuration dictionary consumed by the HTTP client and tool handlers.
"""

import base64
import os
import re
from codecs import BOM_UTF8, BOM_UTF16_BE, BOM_UTF16_LE
from pathlib import Path
from urllib.parse import quote

from .consts import DEFAULT_TIMEOUT_SECONDS
from .http_client import sign_oci_request

_ENV_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _unquote(value: str | None) -> str | None:
    """Strip matching single/double quotes around an environment value."""
    if value is None:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def _load_env_file(path: str | os.PathLike[str]) -> dict[str, str]:
    """Load literal KEY=VALUE entries without evaluating shell metacharacters.

    Matching single or double quotes around values are removed. Characters inside
    values, including !, $, %, &, #, spaces, and backslashes, are preserved exactly.
    The returned values are not evaluated or written into the process environment.
    """
    env_path = Path(path)
    try:
        lines = env_path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise ValueError(f"Unable to read environment file '{env_path}': {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"Unable to decode environment file '{env_path}'. Use UTF-8") from exc

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[7:].lstrip()
        if "=" not in stripped:
            raise ValueError(f"Invalid environment entry at {env_path}:{line_number}; expected KEY=VALUE")

        name, raw_value = stripped.split("=", 1)
        name = name.strip()
        if not _ENV_NAME_PATTERN.fullmatch(name):
            raise ValueError(f"Invalid environment variable name at {env_path}:{line_number}: {name!r}")

        value = raw_value.strip()
        if value and value[0] in {"'", '"'}:
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f"Unmatched quote in environment value at {env_path}:{line_number}")
            value = value[1:-1]
        values[name] = value
    return values


def _read_password_from_file(path: str) -> str:
    """Read password from file with BOM-aware decoding, trimming surrounding whitespace."""
    try:
        with open(path, "rb") as f:
            data = f.read()

        if data.startswith(BOM_UTF16_LE):
            text = data.decode("utf-16-le")
        elif data.startswith(BOM_UTF16_BE):
            text = data.decode("utf-16-be")
        elif data.startswith(BOM_UTF8):
            text = data.decode("utf-8-sig")
        else:
            text = data.decode("utf-8")

        if text.startswith("\ufeff"):
            text = text[1:]

        return text.strip()
    except OSError as exc:
        raise ValueError(f"Unable to read OGG_PASSWORD_FILE '{path}': {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"Unable to decode OGG_PASSWORD_FILE '{path}'. Use UTF-8 (recommended) or UTF-16 with BOM"
        ) from exc


def _signed_get(cfg: dict, hostname: str, path: str) -> dict:
    """Perform a signed OCI GET request and return parsed JSON payload."""
    import http.client

    headers = sign_oci_request(cfg, "GET", path, hostname)
    conn = http.client.HTTPSConnection(hostname, timeout=DEFAULT_TIMEOUT_SECONDS)
    conn.request("GET", path, headers=headers)
    response = conn.getresponse()
    data = response.read().decode("utf-8")
    if response.status != 200:
        raise RuntimeError(f"HTTP {response.status}: {data}")
    import json

    return json.loads(data)


def read_config() -> dict:
    """Build and validate runtime configuration from environment variables.

    Returns:
        dict: Normalized configuration for authentication and HTTP transport.

    Raises:
        ValueError: If required variables are missing or invalid.
    """
    env_file = os.getenv("OGG_ENV_FILE")
    file_values = _load_env_file(env_file) if env_file else {}

    def env(name: str, *, unquote_process: bool = False) -> str | None:
        if name in os.environ:
            value = os.environ[name]
            return _unquote(value) if unquote_process else value
        # The file parser already removed its one layer of surrounding quotes.
        return file_values.get(name)

    base_url = env("OGG_BASE_URL")
    if not base_url:
        raise ValueError("Missing required env var OGG_BASE_URL")

    cfg = {
        "baseUrl": base_url,
        "authMode": "basic",
        "username": env("OGG_USERNAME", unquote_process=True),
        "tenancyOCID": env("OCI_TENANCY_OCID"),
        "userOCID": env("OCI_USER_OCID"),
        "keyFingerprint": env("OCI_KEY_FINGERPRINT"),
        "privateKeyPEM": None,
        "passphrase": env("OCI_PRIVATE_KEY_PASSPHRASE") or "",
        "ociRegion": env("OCI_REGION"),
        "passwordSecretOcid": env("OGG_PASSWORD_SECRET_OCID"),
        "passwordFile": env("OGG_PASSWORD_FILE"),
        "password": None,
    }

    private_key_file = env("OCI_PRIVATE_KEY_FILE")
    if private_key_file:
        with open(private_key_file, encoding="utf-8") as f:
            cfg["privateKeyPEM"] = f.read()

    if cfg.get("passwordSecretOcid"):
        password_secret_ocid = cfg.get("passwordSecretOcid")
        if password_secret_ocid is None:
            raise ValueError("Missing OGG_PASSWORD_SECRET_OCID")
        if not cfg.get("ociRegion"):
            raise ValueError("Missing OCI_REGION for OGG_PASSWORD_SECRET_OCID")
        if not cfg.get("tenancyOCID") or not cfg.get("userOCID") or not cfg.get("keyFingerprint") or not cfg.get("privateKeyPEM"):
            raise ValueError("OCI signer credentials required for OGG_PASSWORD_SECRET_OCID in basic mode")
        host_secrets = f"secrets.vaults.{cfg['ociRegion']}.oci.oraclecloud.com"
        query = f"/20190301/secretbundles/{quote(password_secret_ocid, safe='')}?stage=CURRENT"
        bundle = _signed_get(cfg, host_secrets, query)
        content_base64 = bundle["secretBundleContent"]["content"]
        cfg["password"] = base64.b64decode(content_base64).decode("utf-8")
    elif cfg.get("passwordFile"):
        password_file = cfg.get("passwordFile")
        if password_file is None:
            raise ValueError("Missing OGG_PASSWORD_FILE")
        cfg["password"] = _read_password_from_file(password_file)
    else:
        cfg["password"] = env("OGG_PASSWORD", unquote_process=True)

    if not cfg.get("username") or cfg.get("password") is None:
        raise ValueError(
            "Basic auth requires OGG_USERNAME and one of OGG_PASSWORD_SECRET_OCID, OGG_PASSWORD_FILE, or OGG_PASSWORD"
        )

    return cfg
