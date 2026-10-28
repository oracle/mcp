"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Security helpers for redacting sensitive values from tool output and logs.
"""

from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEYS = {
    "authorization",
    "connectionPassword",
    "keyFingerprint",
    "ociKeyFingerprint",
    "passphrase",
    "password",
    "passwordFile",
    "passwordSecretOcid",
    "privateKeyPEM",
    "privateKeyPem",
    "secret",
    "token",
}
SENSITIVE_KEYS_LOWER = {key.lower() for key in SENSITIVE_KEYS}

# Consume an entire quoted value, including backslash escapes and SQL doubled
# quotes. An unterminated quote is redacted through the end of the line.
_VALUE = r'''"(?:\\.|""|[^"\\])*"|'(?:\\.|''|[^'\\])*'|["'][^\r\n]*|[^\s,;}\]]+'''
_KEY_VALUE_RE = re.compile(
    r"(?P<prefix>\b(?:" + "|".join(re.escape(key) for key in sorted(SENSITIVE_KEYS))
    + r"|private[_ -]?key)\b[\"']?\s*[:=]\s*)(?P<value>" + _VALUE + ")",
    flags=re.IGNORECASE,
)
_OGG_PASSWORD_RE = re.compile(r"(?P<prefix>\bPASSWORD\s+)(?![\s:=])(?P<value>" + _VALUE + ")", flags=re.IGNORECASE)
_AUTH_HEADER_RE = re.compile(r"(?P<prefix>\bAuthorization:\s*)(?P<value>[^\r\n]+)", flags=re.IGNORECASE)
_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----.*?(?:-----END (?:[A-Z]+ )?PRIVATE KEY-----|\Z)",
    flags=re.DOTALL,
)


def _redacted_value(match: re.Match[str]) -> str:
    value = match.group("value")
    quote = value[0] if value[0] in {"'", '"'} else ""
    return f"{match.group('prefix')}{quote}[REDACTED]{quote}"


def redact_text(text: Any) -> str:
    """Redact common credential patterns from free-form text."""
    value = str(text)
    value = _PRIVATE_KEY_RE.sub("[REDACTED]", value)
    value = _AUTH_HEADER_RE.sub(r"\g<prefix>[REDACTED]", value)
    value = _KEY_VALUE_RE.sub(_redacted_value, value)
    value = _OGG_PASSWORD_RE.sub(_redacted_value, value)
    return value


def sanitize_data(data: Any) -> Any:
    """Recursively redact sensitive values from dict/list/string payloads."""
    if isinstance(data, dict):
        sanitized: dict[Any, Any] = {}
        for key, value in data.items():
            if str(key) in SENSITIVE_KEYS or str(key).lower() in SENSITIVE_KEYS_LOWER:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_data(value)
        return sanitized
    if isinstance(data, list):
        return [sanitize_data(item) for item in data]
    if isinstance(data, str):
        return redact_text(data)
    return data
