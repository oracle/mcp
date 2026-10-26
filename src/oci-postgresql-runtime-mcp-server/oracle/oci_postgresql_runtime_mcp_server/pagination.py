"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import base64
import binascii
import hashlib
import json
from collections.abc import Callable
from typing import Any, Optional

from pydantic_core import to_json

_DEFAULT_METADATA_LIMIT = 100
_MAX_METADATA_LIMIT = 1000
_MAX_METADATA_BYTES = 1_048_576
_STATEMENT_TIMEOUT_MS = 300_000
_LOCK_TIMEOUT_MS = 5_000
_MAX_IDENTIFIER_BYTES = 1024


def _bounded_integer(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= _MAX_METADATA_LIMIT:
        raise ValueError(f"{name} must be between 1 and {_MAX_METADATA_LIMIT}")





def _scope_digest(tool: str, connection_name: str, **filters: Any) -> str:
    scope = {"tool": tool, "connection_name": connection_name, **filters}
    return hashlib.sha256(to_json(scope)).hexdigest()


def _encode_cursor(scope: str, after: tuple[str, ...]) -> str:
    payload = to_json({"v": 1, "scope": scope, "after": after})
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(cursor: Optional[str], scope: str, width: int) -> Optional[tuple[str, ...]]:
    if cursor is None:
        return None
    try:
        if not isinstance(cursor, str) or not cursor or len(cursor) > 4096:
            raise ValueError
        payload = json.loads(base64.b64decode(
            cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True,
        ))
        if not isinstance(payload, dict) or set(payload) != {"v", "scope", "after"}:
            raise ValueError
        if type(payload["v"]) is not int or payload["v"] != 1 or payload["scope"] != scope:
            raise ValueError
        after = payload["after"]
        if not isinstance(after, list) or len(after) != width or any(
            not isinstance(value, str) or not value or "\x00" in value
            or len(value.encode("utf-8")) > _MAX_IDENTIFIER_BYTES
            for value in after
        ):
            raise ValueError
        return tuple(after)
    except (ValueError, TypeError, UnicodeError, binascii.Error) as exc:
        raise ValueError("Invalid cursor or cursor does not match this connection and request") from exc


def _bounded_page(
    items: list[Any],
    *,
    field: str,
    metadata: dict[str, Any],
    scope: str,
    key: Callable[[Any], tuple[str, ...]],
    has_more: bool,
) -> dict[str, Any]:
    empty = {**metadata, field: [], "count": 0, "has_more": False,
             "next_cursor": None, "truncation_reason": None}
    if len(to_json(empty)) > _MAX_METADATA_BYTES:
        raise ValueError("Metadata response scope exceeds the size limit; use fewer explicit filters")
    emitted: list[Any] = []
    item_bytes = 0
    byte_limited = False
    for item in items:
        next_cursor = _encode_cursor(scope, key(item))
        # Reserve continuation metadata even for the final object. This keeps the
        # budget valid when a subsequent object's size makes the page incomplete.
        envelope = {
            **metadata, field: [], "count": len(emitted) + 1,
            "has_more": True, "next_cursor": next_cursor,
            "truncation_reason": "max_result_bytes",
        }
        candidate_bytes = item_bytes + len(to_json(item)) + bool(emitted)
        if len(to_json(envelope)) + candidate_bytes > _MAX_METADATA_BYTES:
            if not emitted:
                raise ValueError(
                    "Metadata for one object exceeds the response size limit; "
                    "use summary detail or a smaller filter scope"
                )
            byte_limited = True
            break
        emitted.append(item)
        item_bytes = candidate_bytes

    more = has_more or byte_limited
    return {
        **metadata, field: emitted, "count": len(emitted),
        "has_more": more,
        "next_cursor": _encode_cursor(scope, key(emitted[-1])) if more and emitted else None,
        "truncation_reason": "max_result_bytes" if byte_limited else "limit" if more else None,
    }
