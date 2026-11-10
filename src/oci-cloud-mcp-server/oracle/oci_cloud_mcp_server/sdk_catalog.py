"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Exact, immutable membership boundary for the packaged OCI SDK inventory.
"""

from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from importlib.metadata import version
from importlib.resources import files
import inspect
import json
import re
from types import MappingProxyType
from typing import Mapping

import oci


class SdkResolutionError(ValueError):
    """An identity or installed catalog is outside the supported SDK surface."""


@dataclass(frozen=True)
class OperationEntry:
    name: str
    summary: str


@dataclass(frozen=True)
class ClientEntry:
    identity: str
    module: str
    name: str
    service: str
    aliases: tuple[str, ...]
    operations: Mapping[str, OperationEntry]


@dataclass(frozen=True)
class ModelEntry:
    identity: str
    module: str
    name: str
    service: str
    aliases: tuple[str, ...]
    bases: tuple[str, ...]
    swagger_types: Mapping[str, str]
    attribute_map: Mapping[str, str]
    opaque_fields: frozenset[str]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SdkResolutionError(f"Invalid SDK catalog: {message}")


def _object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _keys(value, expected: set[str]) -> None:
    _require(isinstance(value, dict) and set(value) == expected, "record fields")


def _string_map(value) -> Mapping[str, str]:
    _require(isinstance(value, dict) and all(
        isinstance(k, str) and isinstance(v, str) for k, v in value.items()
    ), "schema map")
    return MappingProxyType(value)


def _strings(value) -> tuple[str, ...]:
    _require(isinstance(value, list) and all(isinstance(v, str) for v in value), "string list")
    _require(value == sorted(set(value)), "duplicate or unsorted identities")
    return tuple(value)


def _type_leaves(name: str):
    compact = name.replace(" ", "")
    if compact.startswith("list[") and compact.endswith("]"):
        yield from _type_leaves(compact[5:-1])
    elif compact.startswith("dict(") and compact.endswith(")"):
        key, separator, value = compact[5:-1].partition(",")
        _require(separator == "," and key == "str", "dictionary schema type")
        yield from _type_leaves(value)
    else:
        yield compact


class SdkCatalog:
    """Validated descriptors; callers cannot register additional SDK identities."""

    def __init__(self, clients, models, client_aliases, model_aliases):
        self.clients = MappingProxyType(clients)
        self.models = MappingProxyType(models)
        self._client_aliases = MappingProxyType(client_aliases)
        self._model_aliases = MappingProxyType(model_aliases)

    @classmethod
    def from_bytes(cls, data: bytes, installed_version: str, reported_version: str):
        try:
            raw = json.loads(data, object_pairs_hook=_object)
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise SdkResolutionError("Invalid SDK catalog JSON") from exc
        _keys(raw, {"schema_version", "sdk_version", "sdk_artifacts", "exclusions", "clients", "models"})
        _require(type(raw["schema_version"]) is int and raw["schema_version"] == 1, "schema version")
        _require(isinstance(raw["sdk_version"], str) and raw["sdk_version"] == installed_version == reported_version,
                 "SDK version mismatch; install matching server/catalog/SDK artifacts")
        artifacts = _strings(raw["sdk_artifacts"])
        _require(bool(artifacts) and all(re.fullmatch(r"sha256:[a-f0-9]{64}", a) for a in artifacts), "SDK hashes")
        _string_map(raw["exclusions"])
        clients, models, client_aliases, model_aliases = {}, {}, {}, {}
        for kind, records, destination, aliases in (
            ("client", raw["clients"], clients, client_aliases),
            ("model", raw["models"], models, model_aliases),
        ):
            _require(isinstance(records, dict) and bool(records), f"{kind} inventory")
            for identity, record in records.items():
                expected = {"module", "name", "service", "aliases"}
                expected |= {"operations"} if kind == "client" else {
                    "bases", "swagger_types", "attribute_map", "opaque_fields"
                }
                _keys(record, expected)
                service, module, name = record["service"], record["module"], record["name"]
                _require(isinstance(service, str) and bool(re.fullmatch(r"oci\.[a-z][a-z0-9_]*", service)), "service")
                _require(isinstance(name, str) and name.isidentifier() and not name.startswith("_"), "class name")
                namespace = service if kind == "client" else f"{service}.models"
                _require(identity == f"{namespace}.{name}", "canonical identity")
                suffix = r"[a-z][a-z0-9_]*_client" if kind == "client" else r"[a-z][a-z0-9_]*"
                _require(isinstance(module, str) and bool(re.fullmatch(re.escape(namespace) + r"\." + suffix, module)),
                         "defining module")
                entry_aliases = _strings(record["aliases"])
                _require(set(entry_aliases) == {identity, f"{module}.{name}"}, "canonical aliases")
                for alias in entry_aliases:
                    _require(alias not in aliases, "alias collision")
                    aliases[alias] = identity
                if kind == "client":
                    _require(name.endswith("Client") and isinstance(record["operations"], dict)
                             and bool(record["operations"]), "service client")
                    operations = {}
                    for operation, metadata in record["operations"].items():
                        _require(operation.isidentifier() and not operation.startswith("_"), "public operation")
                        _keys(metadata, {"summary"})
                        _require(isinstance(metadata["summary"], str), "operation summary")
                        operations[operation] = OperationEntry(operation, metadata["summary"])
                    destination[identity] = ClientEntry(identity, module, name, service, entry_aliases,
                                                        MappingProxyType(operations))
                else:
                    schema, attributes = _string_map(record["swagger_types"]), _string_map(record["attribute_map"])
                    _require(set(schema) == set(attributes), "schema/attribute fields disagree")
                    opaque = frozenset(_strings(record["opaque_fields"]))
                    _require(opaque <= schema.keys(), "opaque fields")
                    destination[identity] = ModelEntry(identity, module, name, service, entry_aliases,
                                                       _strings(record["bases"]), schema, attributes, opaque)
        primitives = {"str", "int", "float", "bool", "object", "datetime", "date", "None", "bytes"}
        for model in models.values():
            for base in model.bases:
                _require(base in models and models[base].service == model.service and base != model.identity,
                         "model inheritance reference")
            opaque = set()
            for field, type_name in model.swagger_types.items():
                for leaf in _type_leaves(type_name):
                    if leaf not in primitives and f"{model.service}.models.{leaf}" not in models:
                        _require(field in model.opaque_fields, "unresolved model schema reference")
                        opaque.add(field)
            _require(opaque == model.opaque_fields, "stale opaque field")
        # Detect cycles even if no polymorphic request ever reaches these entries.
        visited, active = set(), set()
        def visit(identity):
            _require(identity not in active, "model inheritance cycle")
            if identity not in visited:
                active.add(identity)
                for base in models[identity].bases:
                    visit(base)
                active.remove(identity)
                visited.add(identity)
        for identity in models:
            visit(identity)
        return cls(clients, models, client_aliases, model_aliases)

    def client(self, alias: str) -> ClientEntry:
        if not isinstance(alias, str) or alias not in self._client_aliases:
            raise SdkResolutionError("client_fqn must reference a cataloged OCI SDK service client")
        return self.clients[self._client_aliases[alias]]

    def operation(self, client: ClientEntry, name: str) -> OperationEntry:
        if not isinstance(name, str) or name not in client.operations:
            raise SdkResolutionError(f"Operation {name!r} is not public or cataloged on {client.identity}")
        return client.operations[name]

    def model(self, name: str, service: str | None = None) -> ModelEntry:
        alias = f"{service}.models.{name}" if isinstance(name, str) and "." not in name and service else name
        if not isinstance(alias, str) or alias not in self._model_aliases:
            raise SdkResolutionError("Model hint must reference a cataloged OCI SDK model class")
        return self.models[self._model_aliases[alias]]

    def load_client(self, entry: ClientEntry) -> type:
        _require(self.clients.get(entry.identity) is entry, "unapproved descriptor")
        return self._load_client(entry.identity)

    @lru_cache(maxsize=512)
    def _load_client(self, identity: str) -> type:
        return self._load(self.clients[identity], self.clients)

    def load_model(self, entry: ModelEntry) -> type:
        _require(self.models.get(entry.identity) is entry, "unapproved descriptor")
        return self._load_model(entry.identity)

    @lru_cache(maxsize=32768)
    def _load_model(self, identity: str) -> type:
        return self._load(self.models[identity], self.models)

    @staticmethod
    def _load(entry, entries) -> type:
        _require(entries.get(entry.identity) is entry, "unapproved descriptor")
        try:
            obj = getattr(import_module(entry.module), entry.name)
        except (ImportError, AttributeError) as exc:
            raise SdkResolutionError("Cataloged SDK class could not be loaded") from exc
        _require(inspect.isclass(obj) and obj.__module__ == entry.module and obj.__name__ == entry.name,
                 "loaded class identity")
        return obj

    def model_for_class(self, model_class: type) -> ModelEntry:
        entry = self.model(f"{model_class.__module__}.{model_class.__name__}")
        _require(self.load_model(entry) is model_class, "model class identity")
        return entry

    def is_subtype(self, base: ModelEntry, candidate: ModelEntry) -> bool:
        if base.identity == candidate.identity:
            return True
        return any(self.is_subtype(base, self.models[parent]) for parent in candidate.bases)


@lru_cache(maxsize=1)
def load_catalog() -> SdkCatalog:
    try:
        data = files(__package__).joinpath("sdk_catalog.json").read_bytes()
        return SdkCatalog.from_bytes(data, version("oci"), oci.__version__)
    except (OSError, ValueError) as exc:
        raise SdkResolutionError(f"Cannot load trusted SDK catalog: {exc}") from exc
