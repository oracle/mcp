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

from oracle.oci_oracle_db_observability.v1.oci_dbm_mcp_server import metadata, models, tools


REMOVED_TOOL_NAMES = {
    "add_data_files",
    "add_managed_database_to_managed_database_group",
    "clone_sql_tuning_task",
    "configure_automatic_capture_filters",
    "configure_automatic_spm_evolve_advisor_task",
    "fetch_sql_tuning_set",
    "implement_optimizer_statistics_advisor_recommendations",
    "load_sql_plan_baselines_from_awr",
    "load_sql_plan_baselines_from_cursor_cache",
    "load_sql_tuning_set",
    "modify_autonomous_database_management_feature",
    "modify_database_management_feature",
    "modify_external_container_database_management_feature",
    "modify_pluggable_database_management_feature",
    "modify_snapshot_settings",
    "patch_cloud_db_system_discovery",
    "patch_external_db_system_discovery",
    "remove_data_file",
    "remove_managed_database_from_managed_database_group",
    "reset_database_parameters",
    "resize_data_file",
    "run_historic_addm",
    "save_sql_tuning_set_as",
    "start_sql_tuning_task",
    "test_named_credential",
    "test_preferred_credential",
    "validate_basic_filter",
    # DBM MySQL/HeatWave tools removed because DBM MySQL support is deprecated.
    "change_mysql_database_management_type",
    "check_external_my_sql_database_connector_connection_status",
    "create_external_my_sql_database",
    "create_external_my_sql_database_connector",
    "disable_external_my_sql_database_management",
    "enable_external_my_sql_database_management",
    "get_binary_log_information",
    "get_external_my_sql_database",
    "get_external_my_sql_database_connector",
    "get_general_replication_information",
    "get_heat_wave_fleet_metric",
    "get_managed_my_sql_database",
    "get_my_sql_fleet_metric",
    "get_my_sql_query_details",
    "list_external_my_sql_databases",
    "list_high_availability_members",
    "list_inbound_replications",
    "list_managed_my_sql_database_configuration_data",
    "list_managed_my_sql_database_sql_data",
    "list_managed_my_sql_databases",
    "list_my_sql_database_connectors",
    "list_my_sql_digest_errors",
    "list_outbound_replications",
    "summarize_managed_my_sql_database_availability_metrics",
    "update_external_mysql_database",
    "update_external_mysql_database_connector",
}


def test_expected_tool_metadata_exposes_runtime_tool_sets() -> None:
    assert len(metadata.INCLUDED_METHOD_NAMES) == 266
    assert len(metadata.REQUEST_MODEL_TYPES) == 90
    assert len(tools.TOOL_NAMES) == 268
    assert tools.TOOL_NAMES == metadata.TOOL_NAMES
    assert metadata.TOOL_NAMES == frozenset(metadata.INCLUDED_METHOD_NAMES) | tools.BOOTSTRAP_TOOL_NAMES
    assert REMOVED_TOOL_NAMES.isdisjoint(metadata.INCLUDED_METHOD_NAMES)
    assert REMOVED_TOOL_NAMES.isdisjoint(tools.TOOL_NAMES)
    assert REMOVED_TOOL_NAMES.isdisjoint(tools.TOOL_DESCRIPTIONS)
    assert REMOVED_TOOL_NAMES.isdisjoint(metadata.METHOD_CLIENTS)
    assert all(not name.startswith("delete_") for name in metadata.INCLUDED_METHOD_NAMES)
    assert all(not name.startswith("drop_") for name in metadata.INCLUDED_METHOD_NAMES)


def test_tool_descriptions_do_not_duplicate_mutability_metadata() -> None:
    assert len(metadata.MUTABLE_METHOD_NAMES) == 97

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
    field = models.ManagedDatabase.model_fields["database_type"]

    assert field.is_required()
    assert field.alias == "databaseType"
    assert "type of Oracle Database installation" in (field.description or "")
    assert "EXTERNAL_SIDB" in get_args(field.annotation)


def test_schema_fields_include_documented_constraints() -> None:
    parameter = inspect.signature(tools.list_managed_databases).parameters["limit"]
    constraints = {item.__class__.__name__: item for item in parameter.default.metadata}

    assert parameter.default.description.startswith("For list pagination.")
    assert constraints["Ge"].ge == 1
    assert constraints["Le"].le == 1000


def test_request_body_parameters_accept_dict_or_generated_model() -> None:
    annotation = get_type_hints(
        tools.create_job,
        vars(tools),
        vars(tools),
    )["create_job_details"]
    dict_arg, model_arg = get_args(annotation)

    assert get_origin(dict_arg) is dict
    assert get_args(dict_arg) == (str, Any)
    assert model_arg is models.CreateJobDetails


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
        "retry_strategy",
    }

    for name in metadata.INCLUDED_METHOD_NAMES:
        assert skipped.isdisjoint(inspect.signature(getattr(tools, name)).parameters)


def test_request_models_do_not_expose_tag_mutation_fields() -> None:
    request_tag_fields = {"defined_tags", "freeform_tags", "system_tags", "tag_filters", "match_rule"}

    assert request_tag_fields.isdisjoint(models.CreateManagedDatabaseGroupDetails.model_fields)
    assert request_tag_fields.isdisjoint(models.UpdateManagedDatabaseGroupDetails.model_fields)
    assert "defined_tags" in models.ManagedDatabaseGroup.model_fields

    with pytest.raises(ValidationError):
        models.CreateManagedDatabaseGroupDetails(
            name="GROUP1",
            compartment_id="ocid1.compartment.oc1..example",
            freeform_tags={"owner": "dbm"},
        )


def test_schema_named_sdk_field_uses_non_shadowing_public_name() -> None:
    fields = models.SqlInSqlTuningSet.model_fields

    assert "schema_name" in fields
    assert "schema" not in fields
    assert fields["schema_name"].alias == "schema"
