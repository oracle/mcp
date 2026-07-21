"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import inspect
from typing import Any, get_args, get_origin, get_type_hints

import pytest
from pydantic import ValidationError

from oracle.oci_oracle_db_observability.v1.oci_opsi_mcp_server import metadata, models, tools


REMOVED_TOOL_NAMES = {
    "add_exadata_insight_members",
    "download_operations_insights_warehouse_wallet",
    "head_awr_hub_object",
    "ingest_addm_reports",
    "ingest_database_configuration",
    "ingest_host_configuration",
    "ingest_host_metrics",
    "ingest_my_sql_sql_stats",
    "ingest_my_sql_sql_text",
    "ingest_sql_bucket",
    "ingest_sql_plan_lines",
    "ingest_sql_stats",
    "ingest_sql_text",
    "put_awr_hub_object",
    "rotate_operations_insights_warehouse_wallet",
    "synchronize_autonomous_database_to_exadata",
    "test_macs_managed_autonomous_database_insight_connection",
    "test_macs_managed_cloud_database_insight_connection",
}


def test_expected_tool_metadata_exposes_runtime_tool_sets() -> None:
    assert len(metadata.INCLUDED_METHOD_NAMES) == 158
    assert len(metadata.REQUEST_MODEL_TYPES) == 47
    assert len(tools.TOOL_NAMES) == 160
    assert tools.TOOL_NAMES == frozenset(metadata.INCLUDED_METHOD_NAMES) | tools.BOOTSTRAP_TOOL_NAMES
    assert tools.MUTABLE_TOOL_NAMES == frozenset(metadata.MUTABLE_METHOD_NAMES)
    assert set(metadata.MUTABLE_METHOD_NAMES).issubset(metadata.INCLUDED_METHOD_NAMES)
    assert REMOVED_TOOL_NAMES.isdisjoint(metadata.INCLUDED_METHOD_NAMES)
    assert REMOVED_TOOL_NAMES.isdisjoint(tools.TOOL_NAMES)
    assert REMOVED_TOOL_NAMES.isdisjoint(tools.TOOL_DESCRIPTIONS)
    assert all(not name.startswith("delete_") for name in metadata.INCLUDED_METHOD_NAMES)
    assert all(not name.startswith("summarize_sql_") for name in metadata.INCLUDED_METHOD_NAMES)


def test_tool_descriptions_do_not_duplicate_mutability_metadata() -> None:
    for description in tools.TOOL_DESCRIPTIONS.values():
        assert "WARNING:" not in description


def test_tool_annotations_match_mutability() -> None:
    assert set(tools.TOOL_ANNOTATIONS) == tools.TOOL_NAMES

    for name, annotations in tools.TOOL_ANNOTATIONS.items():
        is_mutable = name in tools.MUTABLE_TOOL_NAMES
        assert annotations.title == name.replace("_", " ").title()
        assert annotations.readOnlyHint is not is_mutable
        assert annotations.destructiveHint is is_mutable
        assert annotations.idempotentHint is not is_mutable
        assert annotations.openWorldHint is True


def test_schema_fields_include_descriptions_aliases_and_literals() -> None:
    field = models.CreateDatabaseInsightDetails.model_fields["entity_source"]

    assert field.is_required()
    assert field.alias == "entitySource"
    assert "Source of the database entity" in (field.description or "")
    assert "EM_MANAGED_EXTERNAL_DATABASE" in get_args(field.annotation)


def test_schema_fields_include_documented_constraints() -> None:
    parameter = inspect.signature(tools.list_database_insights).parameters["limit"]
    constraints = {item.__class__.__name__: item for item in parameter.default.metadata}

    assert parameter.default.description.startswith("For list pagination")
    assert constraints["Ge"].ge == 1
    assert constraints["Le"].le == 1000


def test_request_body_parameters_accept_dict_or_generated_model() -> None:
    annotation = get_type_hints(
        tools.create_database_insight,
        vars(tools),
        vars(tools),
    )["create_database_insight_details"]
    dict_arg, model_arg = get_args(annotation)

    assert get_origin(dict_arg) is dict
    assert get_args(dict_arg) == (str, Any)
    assert model_arg is models.CreateDatabaseInsightDetails


def test_tool_response_annotations_are_generic() -> None:
    for name in tools.TOOL_NAMES:
        annotation = get_type_hints(getattr(tools, name), vars(tools), vars(tools))["return"]
        assert annotation is Any


def test_tools_do_not_expose_skipped_sdk_transport_parameters() -> None:
    skipped = {
        "allow_control_chars",
        "buffer_limit",
        "defined_tag_equals",
        "defined_tag_exists",
        "enable_strict_url_encoding",
        "freeform_tag_equals",
        "freeform_tag_exists",
        "if_match",
        "opc_request_id",
        "opc_retry_token",
        "page",
    }

    for name in metadata.INCLUDED_METHOD_NAMES:
        assert skipped.isdisjoint(inspect.signature(getattr(tools, name)).parameters)


def test_request_models_do_not_expose_tag_mutation_fields() -> None:
    request_tag_fields = {"defined_tags", "freeform_tags", "system_tags", "tag_filters", "match_rule"}

    assert request_tag_fields.isdisjoint(models.CreateDatabaseInsightDetails.model_fields)
    assert request_tag_fields.isdisjoint(models.CreateNewsReportDetails.model_fields)
    assert "defined_tags" in models.DatabaseInsight.model_fields

    with pytest.raises(ValidationError):
        models.CreateDatabaseInsightDetails(
            entity_source="EM_MANAGED_EXTERNAL_DATABASE",
            compartment_id="ocid1.compartment.oc1..example",
            freeform_tags={"owner": "opsi"},
        )


def test_leading_underscore_sdk_fields_get_public_pydantic_names() -> None:
    fields = models.IndividualOpsiDataObjectDetailsInQuery.model_fields

    assert "query_params" in fields
    assert "_query_params" not in fields
    assert fields["query_params"].alias == "queryParams"
