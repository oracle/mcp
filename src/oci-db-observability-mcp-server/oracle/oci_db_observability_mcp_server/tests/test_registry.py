"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

from oracle.oci_db_observability_mcp_server.registry import (
    RegistryError,
    _read_json,
    _validate,
    _validate_strict_schema,
    client_class,
    load_registry,
)
from oracle.oci_db_observability_mcp_server.registry import to_jsonable
from oracle.oci_db_observability_mcp_server.sdk_schema import (
    _enum_from_description,
    _model_maps,
    _preserve_constraints,
    _split_pair,
    expected_kwargs,
    schema_for_operation,
    schema_for_type,
)


class _SimpleModel:
    swagger_types = {"name": "str", "counts": "list[int]", "labels": "dict(str, bool)"}
    attribute_map = {"name": "name", "counts": "counts", "labels": "labels"}

    @property
    def name(self):
        """**[Required]** A name."""


class _PolymorphicModel:
    swagger_types = {"target": "str"}
    attribute_map = {"target": "target"}

    @staticmethod
    def get_subtype(object_dictionary):
        type = object_dictionary["target"]
        if type == "INDIVIDUAL":
            return "_IndividualModel"
        if type == "GROUP":
            return "_GroupModel"
        return "_PolymorphicModel"


class _IndividualModel(_PolymorphicModel):
    swagger_types = {"target": "str", "identifier": "str"}
    attribute_map = {"target": "target", "identifier": "identifier"}

    @property
    def identifier(self):
        """**[Required]** An identifier."""


class _GroupModel(_PolymorphicModel):
    swagger_types = {"target": "str", "identifiers": "list[str]"}
    attribute_map = {"target": "target", "identifiers": "identifiers"}


def _schema_operation(self, account_id, **kwargs):
    """
    :param str account_id: (required) The account identifier.
    :param list[_SimpleModel] details: Optional model details.
    """
    expected_kwargs = ["details", "retry_strategy"]
    return account_id, kwargs, expected_kwargs


def test_packaged_registry_has_expected_shape() -> None:
    registry = load_registry()

    assert len(registry.skills) == 35
    assert len(registry.tools) == 236
    assert len({tool["name"] for tool in registry.tools}) == 236
    assert all(tool["inputSchema"]["type"] == "object" for tool in registry.tools)
    assert all(tool["inputSchema"].get("additionalProperties") in (False, {"type": "string"}) for tool in registry.tools)
    assert "retrieve_data" not in {tool["name"] for tool in registry.tools}
    assert not any(tool["mutable"] for tool in registry.tools)
    assert "query_opsi_data_object_data" not in {tool["name"] for tool in registry.tools}


def test_tool_filtering_is_skill_scoped() -> None:
    registry = load_registry()

    tools = registry.list_tools({"awr-historical-performance-analysis"})

    assert tools
    assert all("awr-historical-performance-analysis" in tool["skills"] for tool in tools)


def test_unknown_skill_and_tool_are_rejected() -> None:
    registry = load_registry()

    with pytest.raises(RegistryError, match="Unknown skill"):
        registry.get_skill("missing")
    with pytest.raises(RegistryError, match="Unknown tool"):
        registry.get_tool("missing")
    with pytest.raises(RegistryError, match="Unknown skill"):
        registry.list_tools({"missing"})


def test_duplicate_names_are_rejected() -> None:
    registry = load_registry()
    duplicate_skill = dict(registry.skills[0])
    duplicate_tool = dict(registry.tools[0])

    with pytest.raises(RegistryError, match="Duplicate skill"):
        _validate([registry.skills[0], duplicate_skill], [])
    with pytest.raises(RegistryError, match="Duplicate tool"):
        _validate(list(registry.skills), [duplicate_tool, duplicate_tool])


def test_metadata_files_are_valid_json() -> None:
    from importlib.resources import files

    metadata = files("oracle.oci_db_observability_mcp_server").joinpath("metadata")
    for name in ("manifest.json", "skills.json", "tools.json"):
        json.loads(metadata.joinpath(name).read_text(encoding="utf-8"))


def test_compartment_bootstrap_tool_is_not_registry_backed() -> None:
    registry = load_registry()

    assert "list_compartments" not in {tool["name"] for tool in registry.tools}
    assert "list_compartments" not in registry.get_skill("oci-common")["tools"]


def test_registry_values_can_be_returned_as_json() -> None:
    schema = to_jsonable(load_registry().get_tool("summarize_database_insight_resource_usage")["inputSchema"])

    assert isinstance(schema, dict)
    assert json.loads(json.dumps(schema)) == schema


def test_packaged_schemas_match_the_locked_oci_sdk() -> None:
    registry = load_registry()

    for tool in registry.tools:
        if tool.get("kind", "oci_sdk") != "oci_sdk" or tool.get("adapter") or "database-and-infra-observability-metric-catalog" in tool["skills"]:
            continue
        method = getattr(client_class(tool["service"], tool["client"]), tool["operation"])
        models = __import__(f"{method.__module__.rsplit('.', 1)[0]}.models", fromlist=["models"])
        schema = to_jsonable(tool["inputSchema"])
        assert schema == schema_for_operation(method, models, schema)


def test_job_status_summary_requires_one_sdk_supported_scope() -> None:
    schema = dict(load_registry().get_tool("summarize_job_executions_statuses")["inputSchema"])
    validator = Draft202012Validator(schema)
    base = {
        "compartment_id": "compartment",
        "start_time": "2026-01-01T00:00:00Z",
        "end_time": "2026-01-01T01:00:00Z",
    }

    assert validator.is_valid({**base, "id": "job"})
    assert validator.is_valid({**base, "managed_database_id": "database"})
    assert validator.is_valid({**base, "managed_database_group_id": "group"})
    assert not validator.is_valid(base)
    assert not validator.is_valid({**base, "id": "job", "managed_database_id": "database"})
    assert not validator.is_valid({**base, "job_id": "job"})


def test_metric_catalog_skill_uses_the_pinned_monitoring_client_operations() -> None:
    registry = load_registry()
    tool_operations = {
        tool["name"]: tool.get("operation")
        for tool in registry.list_tools({"database-and-infra-observability-metric-catalog"})
    }

    assert tool_operations == {
        "search_database_and_infra_observability_metrics": None,
        "get_database_and_infra_observability_metrics": None,
        "list_database_and_infra_observability_metrics": None,
        "read_database_and_infra_observability_metrics": "summarize_metrics_data",
        "list_database_and_infra_observability_alarms": "list_alarms",
        "get_database_and_infra_observability_alarm": "get_alarm",
        "list_database_and_infra_observability_alarm_states": "list_alarms_status",
    }


@pytest.mark.parametrize("mutation, error", [(lambda schema: schema.pop("additionalProperties"), "unrestricted object"), (lambda schema: schema["properties"].update({"values": {"type": "array"}}), "untyped array")])
def test_registry_rejects_open_objects_and_untyped_arrays(mutation, error) -> None:
    registry = load_registry()
    tool = to_jsonable(registry.tools[0])
    tool["skills"] = ["skill"]
    mutation(tool["inputSchema"])

    with pytest.raises(RegistryError, match=error):
        _validate([{"name": "skill", "tools": [tool["name"]]}], [tool])


@pytest.mark.parametrize(
    ("schema", "error"),
    [
        ({"oneOf": []}, "invalid oneOf"),
        ({"oneOf": ["not-a-schema"]}, "invalid oneOf variant"),
        ({"type": "array"}, "untyped array"),
        ({"type": "object", "additionalProperties": False}, "invalid object properties"),
        ({"type": "object", "properties": {"value": "not-a-schema"}, "additionalProperties": False}, "invalid property schema"),
        ({"type": "object", "properties": {}, "additionalProperties": "invalid"}, "invalid additionalProperties"),
    ],
)
def test_registry_rejects_invalid_strict_schema_shapes(schema, error) -> None:
    with pytest.raises(RegistryError, match=error):
        _validate_strict_schema(schema)


def test_registry_accepts_typed_map_schema_and_reports_bad_bindings() -> None:
    _validate_strict_schema({"type": "object", "additionalProperties": {"type": "string"}})

    with pytest.raises(RegistryError, match="Unsupported SDK client binding"):
        client_class("missing", "client")
    with pytest.raises(RegistryError, match="Unable to load registry file"):
        _read_json("missing.json")


def test_sdk_schema_helpers_reject_unresolvable_contracts() -> None:
    def no_expected_kwargs(self, **kwargs):
        return kwargs

    def mismatched_docs(self, **kwargs):
        """:param str other: (optional) A different argument."""
        expected_kwargs = ["value"]
        return kwargs, expected_kwargs

    assert _split_pair("str, list[int]") == ("str", "list[int]")
    assert _enum_from_description("No SDK enum here") is None
    assert schema_for_type("Any", SimpleNamespace()) == {}
    _preserve_constraints({}, None)
    with pytest.raises(ValueError, match="expected_kwargs"):
        expected_kwargs(no_expected_kwargs)
    with pytest.raises(ValueError, match="does not expose schema maps"):
        _model_maps(object)
    with pytest.raises(ValueError, match="Unable to resolve OCI SDK type"):
        schema_for_type("MissingModel", SimpleNamespace())
    with pytest.raises(ValueError, match="documentation and expected_kwargs differ"):
        schema_for_operation(mismatched_docs, SimpleNamespace())


def test_sdk_schema_helpers_build_strict_model_and_polymorphic_contracts() -> None:
    models = SimpleNamespace(
        _SimpleModel=_SimpleModel,
        _PolymorphicModel=_PolymorphicModel,
        _IndividualModel=_IndividualModel,
        _GroupModel=_GroupModel,
    )

    assert schema_for_type("str", models, 'Allowed values are: "A" "B"') == {"type": "string", "enum": ["A", "B"]}
    assert schema_for_type("list[datetime]", models) == {
        "type": "array",
        "items": {"type": "string", "format": "date-time"},
    }
    assert schema_for_type("dict(str, list[bool])", models) == {
        "type": "object",
        "additionalProperties": {"type": "array", "items": {"type": "boolean"}},
    }
    assert schema_for_type("_SimpleModel", models) == {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "counts": {"type": "array", "items": {"type": "integer"}},
            "labels": {"type": "object", "additionalProperties": {"type": "boolean"}},
        },
        "additionalProperties": False,
        "required": ["name"],
    }
    assert schema_for_type("_PolymorphicModel", models) == {
        "oneOf": [
            {
                "type": "object",
                "properties": {"target": {"type": "string", "enum": ["INDIVIDUAL"]}, "identifier": {"type": "string"}},
                "additionalProperties": False,
                "required": ["identifier", "target"],
            },
            {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "enum": ["GROUP"]},
                    "identifiers": {"type": "array", "items": {"type": "string"}},
                },
                "additionalProperties": False,
                "required": ["target"],
            },
        ]
    }


def test_sdk_schema_operation_preserves_nested_constraints() -> None:
    models = SimpleNamespace(_SimpleModel=_SimpleModel)

    schema = schema_for_operation(
        _schema_operation,
        models,
        {
            "properties": {
                "account_id": {"description": "Customer-facing account identifier", "minLength": 1},
                "details": {
                    "items": {
                        "properties": {
                            "name": {"pattern": "^[a-z]+$"},
                            "counts": {"items": {"minimum": 0}},
                        }
                    }
                },
            },
            "required": ["account_id"],
        },
    )

    assert schema == {
        "type": "object",
        "properties": {
            "account_id": {
                "type": "string",
                "minLength": 1,
                "description": "Customer-facing account identifier",
            },
            "details": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "pattern": "^[a-z]+$"},
                        "counts": {"type": "array", "items": {"type": "integer", "minimum": 0}},
                        "labels": {"type": "object", "additionalProperties": {"type": "boolean"}},
                    },
                    "additionalProperties": False,
                    "required": ["name"],
                },
            },
        },
        "additionalProperties": False,
        "required": ["account_id"],
    }
