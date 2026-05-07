# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''Shared helpers for upleveled MCP tools.'''

import json
import logging
import re

logger = logging.getLogger('oracle-data-studio-mcp')


# ────────────────────────────────────────────────────────────────────
#  Error sanitisation
# ────────────────────────────────────────────────────────────────────
# Oracle / cx_Oracle / ORDS exceptions routinely contain credentials,
# connect strings, OCIDs, file paths, and bearer tokens.  Returning
# them verbatim to the LLM (which then echoes them back to the user
# or downstream tools) is a quiet info-disclosure path.  Every tool
# that catches Exception should funnel the message through `safe_err`.

# Patterns we redact.  Each tuple is (regex, replacement). Order matters
# — earliest wins.  Patterns are case-insensitive where useful.
_REDACTORS = [
    # JDBC / SQL*Net DSN with embedded password:
    #   tcps://user/PASSWORD@host:port
    #   user/PASSWORD@//host:port/svc
    (re.compile(r'(?P<u>[\w.\-+]+)/[^/@\s\'"]+@'),
     r'\g<u>/***@'),
    # URL with userinfo: https://user:password@host
    (re.compile(r'(?P<scheme>\bhttps?://)[^/@\s:]+:[^/@\s]+@'),
     r'\g<scheme>***:***@'),
    # Authorization headers / Bearer tokens
    (re.compile(r'(?i)(authorization\s*[:=]\s*)(?:bearer|basic)\s+\S+'),
     r'\1***'),
    (re.compile(r'(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}\b'),
     r'Bearer ***'),
    # OCI OCIDs — keep prefix for context, redact the random tail
    (re.compile(r'\bocid1\.([a-z]+)\.[a-z0-9.\-]*[a-z0-9]+'),
     r'ocid1.\1.***'),
    # password=... / pwd=...  (query strings, env-style, JSON)
    (re.compile(r'(?i)(["\']?(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']?)'
                r'[^"\'\s,&}]+'),
     r'\1***'),
    # OS / wallet absolute paths — drop the prefix to keep the basename
    (re.compile(r'(?:/(?:Users|home|opt|var|tmp|u\d+)/[\w./\-]+/)'
                r'(?P<base>[\w.\-]+)'),
     r'<path>/\g<base>'),
    # Windows-style paths (C:\Users\...\file)
    (re.compile(r'(?i)\b[A-Z]:\\(?:Users|Documents and Settings)\\[\w\\.\-]+\\'
                r'(?P<base>[\w.\-]+)'),
     r'<path>\\\g<base>'),
]


def safe_err(exc, *, label: str = None) -> str:
    '''Sanitize an exception (or string) into an LLM-safe error message.

    Strips: embedded passwords (DSN/URL/JSON), Authorization headers,
    Bearer tokens, OCID tails, absolute filesystem paths.

    The full original message is logged at DEBUG so operators retain
    diagnostics without leaking them to the LLM client.

    Args:
        exc: Exception or any object str()-able.
        label: Optional prefix included in the returned message.
    '''
    raw = str(exc) if exc is not None else ''
    if label:
        logger.debug('%s failed: %s', label, raw)
    else:
        logger.debug('error: %s', raw)

    cleaned = raw
    for pattern, replacement in _REDACTORS:
        cleaned = pattern.sub(replacement, cleaned)

    # Cap length — Oracle stack traces can be huge; keep first 800 chars
    if len(cleaned) > 800:
        cleaned = cleaned[:800] + '… [truncated]'

    return f'{label}: {cleaned}' if label else cleaned


def safe_call(label, fn, *args, **kwargs):
    '''Call *fn* and return (result, None) or (None, error_string).

    Used by composite tools to gather partial results gracefully.
    Errors are funnelled through `safe_err` to strip credentials.
    '''
    try:
        return fn(*args, **kwargs), None
    except Exception as e:
        return None, safe_err(e, label=label)


def build_response(data, errors=None):
    '''Build a JSON response string with optional collected errors.'''
    if errors:
        data['_errors'] = errors
    return json.dumps(data, indent=2, default=str)


def err(msg):
    '''Return a JSON error string.

    The message is funnelled through `safe_err` to strip credentials,
    OCIDs, paths, and bearer tokens. Pass either a plain string or an
    Exception — both are sanitised.
    '''
    return json.dumps({'error': safe_err(msg)})


def fmt(result):
    '''Standard JSON formatting for SDK results.'''
    if result is None:
        return json.dumps({'status': 'success'})
    if isinstance(result, (dict, list)):
        return json.dumps(result, indent=2, default=str)
    return str(result)
