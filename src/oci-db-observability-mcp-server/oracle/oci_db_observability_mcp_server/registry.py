"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Immutable JSON registry for the unified Database Observability server.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from types import MappingProxyType
from typing import Any, Mapping

import oci
from jsonschema import Draft202012Validator, SchemaError


class RegistryError(ValueError):
    """Raised when packaged discovery metadata is invalid."""


_CLIENTS = {
    "opsi": {"OperationsInsightsClient": oci.opsi.OperationsInsightsClient},
    "monitoring": {"MonitoringClient": oci.monitoring.MonitoringClient},
    "dbm": {
        "DbManagementClient": oci.database_management.DbManagementClient,
        "DiagnosabilityClient": oci.database_management.DiagnosabilityClient,
        "SqlTuningClient": oci.database_management.SqlTuningClient,
    },
    "identity": {"IdentityClient": oci.identity.IdentityClient},
}
_COMPARTMENT_ARGUMENTS = ("compartment_id", "peer_database_compartment_id")

_METADATA_HANDLERS = frozenset(
    {
        "metric_catalog.search",
        "metric_catalog.get",
        "metric_catalog.list",
    }
)

_OCI_SDK_ADAPTERS = frozenset({"monitoring.metric_read"})


@dataclass(frozen=True)
class Registry:
    skills: tuple[Mapping[str, Any], ...]
    tools: tuple[Mapping[str, Any], ...]
    _skills: Mapping[str, Mapping[str, Any]]
    _tools: Mapping[str, Mapping[str, Any]]

    def get_skill(self, name: str) -> Mapping[str, Any]:
        try:
            return self._skills[name]
        except KeyError as exc:
            raise RegistryError(f"Unknown skill: {name}") from exc

    def get_tool(self, name: str) -> Mapping[str, Any]:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise RegistryError(f"Unknown tool: {name}") from exc

    def list_tools(
        self,
        skill_names: set[str],
    ) -> list[Mapping[str, Any]]:
        for skill_name in skill_names:
            self.get_skill(skill_name)
        return [tool for tool in self.tools if skill_names.intersection(tool["skills"])]


def client_class(service: str, client: str) -> type[Any]:
    try:
        return _CLIENTS[service][client]
    except KeyError as exc:
        raise RegistryError(f"Unsupported SDK client binding: {service}/{client}") from exc


def compartment_requirements(tool: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return top-level OCI compartment arguments accepted by a catalog operation."""
    schema = tool["inputSchema"]
    properties = schema["properties"]
    required = set(schema.get("required", ()))
    return [
        {"argument": name, "required": name in required}
        for name in _COMPARTMENT_ARGUMENTS
        if name in properties
    ]


def _read_json(name: str) -> dict[str, Any]:
    try:
        return json.loads(files("oracle.oci_db_observability_mcp_server").joinpath("metadata", name).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"Unable to load registry file {name}: {exc}") from exc


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def to_jsonable(value: Any) -> Any:
    """Copy immutable registry values into JSON-compatible response values."""
    if isinstance(value, Mapping):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    return value


def _validate_strict_schema(schema: Mapping[str, Any], path: str = "inputSchema") -> None:
    """Reject open objects and untyped arrays in packaged tool contracts."""
    if "oneOf" in schema:
        variants = schema["oneOf"]
        if not isinstance(variants, list) or not variants:
            raise RegistryError(f"Tool has invalid oneOf schema: {path}")
        for index, variant in enumerate(variants):
            if not isinstance(variant, Mapping):
                raise RegistryError(f"Tool has invalid oneOf variant: {path}[{index}]")
            _validate_strict_schema(variant, f"{path}.oneOf[{index}]")
        return
    schema_type = schema.get("type")
    if schema_type == "array":
        items = schema.get("items")
        if not isinstance(items, Mapping) or not items:
            raise RegistryError(f"Tool has untyped array items: {path}")
        _validate_strict_schema(items, f"{path}.items")
    if schema_type != "object":
        return
    additional = schema.get("additionalProperties")
    if additional is None or additional is True:
        raise RegistryError(f"Tool has unrestricted object schema: {path}")
    if additional is False:
        properties = schema.get("properties")
        if not isinstance(properties, Mapping):
            raise RegistryError(f"Tool has invalid object properties: {path}")
        for name, property_schema in properties.items():
            if not isinstance(property_schema, Mapping):
                raise RegistryError(f"Tool has invalid property schema: {path}.properties.{name}")
            _validate_strict_schema(property_schema, f"{path}.properties.{name}")
    elif isinstance(additional, Mapping):
        _validate_strict_schema(additional, f"{path}.additionalProperties")
    else:
        raise RegistryError(f"Tool has invalid additionalProperties: {path}")


def _validate(skills: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Registry:
    by_skill = {skill.get("name"): skill for skill in skills}
    if any(not isinstance(skill.get("name"), str) or not skill["name"] for skill in skills):
        raise RegistryError("Skill names must be non-empty")
    if len(by_skill) != len(skills):
        raise RegistryError("Duplicate skill name")
    by_tool = {tool.get("name"): tool for tool in tools}
    if any(not isinstance(tool.get("name"), str) or not tool["name"] for tool in tools):
        raise RegistryError("Tool names must be non-empty")
    if len(by_tool) != len(tools):
        raise RegistryError("Duplicate tool name")
    referenced = {name for skill in skills for name in skill.get("tools", [])}
    if referenced != set(by_tool):
        raise RegistryError("Tools must be referenced by at least one skill, and skill references must resolve")
    for tool in tools:
        schema = tool.get("inputSchema")
        if not isinstance(schema, dict) or schema.get("type") != "object":
            raise RegistryError(f"Tool has invalid input schema: {tool.get('name')}")
        _validate_strict_schema(schema)
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise RegistryError(f"Tool has invalid JSON schema: {tool.get('name')}") from exc
        if not set(tool.get("skills", [])) or not set(tool["skills"]).issubset(by_skill):
            raise RegistryError(f"Tool has invalid skill membership: {tool.get('name')}")
        if tool["name"] not in {name for skill in skills if skill["name"] in tool["skills"] for name in skill["tools"]}:
            raise RegistryError(f"Tool/skill membership mismatch: {tool['name']}")
        kind = tool.get("kind", "oci_sdk")
        if kind == "metadata":
            if tool.get("handler") not in _METADATA_HANDLERS:
                raise RegistryError(f"Tool has invalid metadata handler: {tool['name']}")
        elif kind == "oci_sdk":
            cls = client_class(tool.get("service"), tool.get("client"))
            method = getattr(cls, tool.get("operation", ""), None)
            if not callable(method) or tool["operation"].startswith("_"):
                raise RegistryError(f"Tool has invalid SDK operation binding: {tool['name']}")
            if tool.get("adapter") is not None and tool.get("adapter") not in _OCI_SDK_ADAPTERS:
                raise RegistryError(f"Tool has invalid SDK adapter: {tool['name']}")
        else:
            raise RegistryError(f"Tool has invalid execution kind: {tool['name']}")
    frozen_skills = tuple(_freeze(skill) for skill in skills)
    frozen_tools = tuple(_freeze(tool) for tool in tools)
    return Registry(frozen_skills, frozen_tools, MappingProxyType(dict(zip(by_skill, frozen_skills))), MappingProxyType(dict(zip(by_tool, frozen_tools))))


def load_registry() -> Registry:
    manifest = _read_json("manifest.json")
    skills = _read_json(manifest["skills"])["skills"]
    tools = _read_json(manifest["tools"])["tools"]
    return _validate(skills, tools)
