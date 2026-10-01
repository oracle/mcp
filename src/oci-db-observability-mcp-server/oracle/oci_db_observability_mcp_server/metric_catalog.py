"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Immutable Database and Infrastructure Observability metric catalog.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from types import MappingProxyType
from typing import Any, Mapping


class MetricCatalogError(ValueError):
    """Raised when metric catalog input or packaged data is invalid."""


_DEFAULT_LIMIT = 50
_STOP_WORDS = frozenset(
    {"a", "an", "and", "are", "by", "during", "for", "get", "in", "me", "of", "on", "show", "summary", "that", "the", "to", "with"}
)


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _stem(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return f"{word[:-3]}y"
    if word.endswith("ing") and len(word) > 5:
        word = word[:-3]
    elif word.endswith("ed") and len(word) > 4:
        word = word[:-2]
    elif word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word[:-1] if len(word) > 2 and word[-1] == word[-2] else word


def _words(value: Any) -> list[str]:
    text = str(value or "")
    normalized: list[str] = []
    for index, char in enumerate(text):
        if index and char.isupper() and text[index - 1].islower():
            normalized.append(" ")
        normalized.append(char.lower() if char.isalnum() else " ")
    return [word for word in (_stem(item) for item in "".join(normalized).split()) if len(word) > 1 and word not in _STOP_WORDS]


def _field_text(value: Any) -> str:
    return " ".join(_field_text(item) for item in value) if isinstance(value, tuple) else str(value or "")


def _matches(record: Mapping[str, Any], namespace: str | None, name: str | None) -> bool:
    return (namespace is None or record.get("namespace") == namespace) and (name is None or record.get("name") == name)


@dataclass(frozen=True)
class MetricCatalog:
    catalog_id: str
    version: str
    records: tuple[Mapping[str, Any], ...]

    def _response(self, items: list[Any], **extra: Any) -> dict[str, Any]:
        return {"catalogId": self.catalog_id, "version": self.version, "items": _jsonable(items), **extra}

    def search(self, keywords: str, namespace: str | None = None, name: str | None = None, limit: int = _DEFAULT_LIMIT) -> dict[str, Any]:
        if not keywords or not keywords.strip():
            raise MetricCatalogError("keywords must be non-empty")
        if not 1 <= limit <= 100:
            raise MetricCatalogError("limit must be between 1 and 100")
        query_tokens = _words(keywords)
        matches: list[tuple[int, list[str], Mapping[str, Any]]] = []
        for record in self.records:
            if not _matches(record, namespace, name):
                continue
            score, fields, matched = 0, [], set()
            for field in ("name", "description", "namespace", "dimensions"):
                tokens = set(_words(_field_text(record.get(field))))
                current = [token for token in query_tokens if token in tokens]
                if current:
                    fields.append(field)
                    matched.update(current)
                    score += len(current) * (4 if field == "name" else 2)
            if len(query_tokens) > 1 and len(matched) == len(query_tokens):
                score += 8
            if query_tokens and score and len(fields) > 1:
                score += 1
            if not query_tokens or score:
                matches.append((score, fields, record))
        matches.sort(key=lambda item: (-item[0], str(item[2].get("namespace", "")), str(item[2].get("name", ""))))
        return self._response([
            {"key": {"namespace": record["namespace"], "name": record["name"]}, "score": score, "matchedFields": fields, "record": record}
            for score, fields, record in matches[:limit]
        ])

    def get(self, keys: list[Mapping[str, str]]) -> dict[str, Any]:
        if not keys:
            raise MetricCatalogError("keys must contain at least one namespace/name pair")
        wanted = {(key.get("namespace"), key.get("name")) for key in keys}
        if any(not namespace or not name for namespace, name in wanted):
            raise MetricCatalogError("each key must contain non-empty namespace and name")
        return self._response([record for record in self.records if (record.get("namespace"), record.get("name")) in wanted])

    def list(self, namespace: str | None = None, name: str | None = None, limit: int = _DEFAULT_LIMIT, cursor: str | None = None) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            raise MetricCatalogError("limit must be between 1 and 100")
        try:
            offset = int(cursor) if cursor is not None else 0
        except ValueError as exc:
            raise MetricCatalogError("cursor must be a non-negative integer") from exc
        if offset < 0:
            raise MetricCatalogError("cursor must be a non-negative integer")
        records = sorted((record for record in self.records if _matches(record, namespace, name)), key=lambda record: (str(record.get("namespace", "")), str(record.get("name", ""))))
        items = records[offset : offset + limit]
        next_cursor = str(offset + len(items)) if offset + len(items) < len(records) else None
        return self._response(items, nextCursor=next_cursor)


@lru_cache(maxsize=1)
def load_metric_catalog() -> MetricCatalog:
    path = files(__package__).joinpath("metadata", "database-and-infra-observability-metrics.json")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MetricCatalogError(f"Unable to load metric catalog: {exc}") from exc
    records = payload.get("records")
    if not isinstance(payload.get("catalogId"), str) or not isinstance(payload.get("version"), str) or not isinstance(records, list):
        raise MetricCatalogError("Metric catalog has invalid metadata")
    frozen_records = tuple(_freeze(record) for record in records if isinstance(record, dict))
    if len(frozen_records) != len(records):
        raise MetricCatalogError("Metric catalog records must be objects")
    return MetricCatalog(payload["catalogId"], payload["version"], frozen_records)
