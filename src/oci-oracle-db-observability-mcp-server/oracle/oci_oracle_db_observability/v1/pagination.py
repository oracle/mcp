"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import inspect
import re
from typing import Any


_EXPECTED_KWARGS_RE = re.compile(r"expected_kwargs\s*=\s*\[(.*?)\]", re.DOTALL)
_KWARG_RE = re.compile(r"['\"]([a-zA-Z0-9_]+)['\"]")


def _expected_kwargs_from_source(method: Callable[..., Any]) -> set[str] | None:
    try:
        source = inspect.getsource(method)
    except (OSError, TypeError):
        return None

    match = _EXPECTED_KWARGS_RE.search(source)
    if match is None:
        return None
    return set(_KWARG_RE.findall(match.group(1)))


def _method_accepts_page(method: Callable[..., Any]) -> bool:
    expected_kwargs = _expected_kwargs_from_source(method)
    if expected_kwargs is not None:
        return "page" in expected_kwargs

    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return False
    return "page" in signature.parameters


def _next_page_token(response: Any) -> str | None:
    token = getattr(response, "next_page", None)
    if token:
        return str(token)

    headers = getattr(response, "headers", None)
    if not headers:
        return None
    if hasattr(headers, "get"):
        token = headers.get("opc-next-page") or headers.get("Opc-Next-Page")
    else:
        token = dict(headers).get("opc-next-page")
    return str(token) if token else None


def _collection_items(data: Any) -> list[Any] | None:
    if isinstance(data, list):
        return list(data)
    if isinstance(data, tuple):
        return list(data)
    if isinstance(data, Mapping):
        return None

    items = getattr(data, "items", None)
    if items is None or callable(items):
        return None
    if isinstance(items, Sequence) and not isinstance(items, str | bytes | bytearray):
        return list(items)
    return list(items)


def _set_collection_items(data: Any, items: list[Any]) -> Any:
    if isinstance(data, list):
        return items
    if isinstance(data, tuple):
        return items
    setattr(data, "items", items)
    return data


def _set_response_data(response: Any, data: Any) -> None:
    try:
        setattr(response, "data", data)
    except AttributeError:
        pass


def _normalized_limit(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int) and value > 0:
        return value
    return None


def _remaining_limit(limit: int | None, collected_count: int) -> int | None:
    if limit is None:
        return None
    return max(limit - collected_count, 0)


def call_with_auto_pagination(method: Callable[..., Any], sdk_kwargs: dict[str, Any]) -> Any:
    """Call an OCI SDK method and aggregate paginated collection response data."""

    first_response = method(**sdk_kwargs)
    if not _method_accepts_page(method):
        return first_response

    first_data = getattr(first_response, "data", None)
    if first_data is None:
        return first_response

    first_items = _collection_items(first_data)
    if first_items is None:
        return first_response

    limit = _normalized_limit(sdk_kwargs.get("limit"))
    aggregated = first_items[:limit] if limit is not None else first_items
    first_data = _set_collection_items(first_data, aggregated)
    _set_response_data(first_response, first_data)

    next_token = _next_page_token(first_response)
    seen_tokens: set[str] = set()
    while next_token and next_token not in seen_tokens:
        remaining = _remaining_limit(limit, len(aggregated))
        if remaining == 0:
            break

        seen_tokens.add(next_token)
        page_kwargs = dict(sdk_kwargs)
        page_kwargs["page"] = next_token
        if remaining is not None:
            page_kwargs["limit"] = remaining

        page_response = method(**page_kwargs)
        page_data = getattr(page_response, "data", None)
        page_items = _collection_items(page_data)
        if page_items is None:
            break

        if remaining is not None:
            page_items = page_items[:remaining]
        aggregated.extend(page_items)
        first_data = _set_collection_items(first_data, aggregated)
        _set_response_data(first_response, first_data)
        next_token = _next_page_token(page_response)

    return first_response
