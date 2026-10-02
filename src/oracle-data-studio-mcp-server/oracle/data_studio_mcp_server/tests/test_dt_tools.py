# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""dt_tools response contracts, failures, and SDK dispatch."""

import json
import sys
from unittest.mock import MagicMock

import pytest

from oracle.data_studio_mcp_server.tools import dt_tools
from .test_unit import DT_DISPATCH_CASES
from .tool_assertions import (
    assert_composite_response, assert_confirmation_required, assert_sdk_failure, assert_tools_require_connection,
)


SERVICE = 'datatransforms'
TOOL_MODULE = dt_tools


def test_tools_without_connection_return_setup_error(tools):
    assert_tools_require_connection(tools)


_failure_cases = list({tool: (tool, kwargs, path, on_workbench)
                        for tool, kwargs, path, on_workbench in reversed(DT_DISPATCH_CASES)}.values())
_failure_cases += [case for case in DT_DISPATCH_CASES if case[2] == "update_variable"]


@pytest.mark.parametrize("tool,kwargs,path,on_workbench", _failure_cases)
def test_sdk_failure_is_reported_and_redacted(tools, clients, tool, kwargs, path, on_workbench):
    ctx, sdk, workbench = clients
    fallback = {"update_variable": "create_variable", "list_data_entities": "get_all_datastores"}.get(path)
    assert_sdk_failure(tools[tool].fn, ctx, workbench if on_workbench else sdk, kwargs, path, fallback=fallback)


COMPOSITES = [
    ('dt_explore', {}, [
        ('get_about', 'about'), ('list_connections', 'connections'), ('list_projects', 'projects'),
        ('list_schedules', 'schedules'),
    ]),
    ('dt_describe_project', {'project_name': 'P'}, [
        ('list_dataflows_in_project', 'dataflows'), ('list_workflows_in_project', 'workflows'),
        ('list_dataloads_in_project', 'dataloads'),
    ]),
    ('dt_describe_connection', {'connection_name': 'C'}, [
        ('get_connection_details', 'details'), ('test_connection_by_name', 'test_result'),
        ('get_live_schemas', 'schemas'),
    ]),
]


@pytest.mark.parametrize("tool,kwargs,steps", COMPOSITES)
@pytest.mark.parametrize("fail_step", ["none", "first", "all"])
def test_composites_preserve_successful_sections_on_partial_failure(
        tools, clients, tool, kwargs, steps, fail_step):
    ctx, sdk, _ = clients
    assert_composite_response(tools[tool].fn, ctx, sdk, kwargs, steps, fail_step,
                              redacted=("connections", "details"))


_destructive = [(tool, kwargs, path) for tool, kwargs, path, _ in DT_DISPATCH_CASES if "confirm" in kwargs]


@pytest.mark.parametrize("tool,kwargs,path", _destructive)
@pytest.mark.parametrize("confirm", [None, "wrong-resource"])
def test_destructive_actions_require_matching_confirmation(tools, clients, tool, kwargs, path, confirm):
    ctx, sdk, _ = clients
    assert_confirmation_required(tools[tool].fn, ctx, sdk, kwargs, path, confirm)


@pytest.mark.parametrize("options,properties", [
    ({"host": "example.invalid", "port": 1521, "service_name": "service"},
     [("host", "example.invalid"), ("port", "1521"), ("serviceName", "service")]),
    ({"jdbc_url": "jdbc:oracle:thin:@example.invalid"}, [("jdbcUrl", "jdbc:oracle:thin:@example.invalid")]),
    ({"wallet_path": "test-wallet"}, []),
])
def test_connection_builder_receives_supplied_options(tools, clients, monkeypatch, options, properties):
    ctx, _, wb = clients
    module = MagicMock()
    monkeypatch.setitem(sys.modules, "datatransforms.connection", module)
    wb.save_connection.return_value = "saved"
    result = json.loads(tools["dt_manage_connection"].fn(
        action="create", connection_name="C", connection_type="Oracle", user="user", password="secret",
        ctx=ctx, **options))
    module.Connection.assert_called_once_with("C")
    builder = module.Connection.return_value
    builder.of_type.assert_called_once_with("Oracle")
    builder.with_credentials.assert_called_once_with("user", "secret")
    assert [call.args for call in builder.property.call_args_list] == properties
    if "wallet_path" in options:
        builder.usingWallet.assert_called_once_with("test-wallet")
    wb.save_connection.assert_called_once_with(builder)
    assert result == {"action": "created", "connection": "C", "result": "saved"}


@pytest.mark.parametrize("builder_failure", [ImportError("builder unavailable"), RuntimeError("builder failed")])
def test_pipeline_builder_failure_uses_rest_payload(tools, clients, monkeypatch, builder_failure):
    ctx, dt, _ = clients
    module = MagicMock()
    module.Project.side_effect = builder_failure
    monkeypatch.setitem(sys.modules, "datatransforms.dataflow", module)
    dt.create_dataflow_from_json_payload.return_value = (True, "df-123")
    result = json.loads(tools["dt_create_pipeline"].fn(
        project_name="P", source_connection="SOURCE", source_schema="SRC", source_table="ORDERS",
        target_connection="TARGET", target_schema="TGT", target_table="ORDERS_COPY", ctx=ctx))
    payload = json.loads(dt.create_dataflow_from_json_payload.call_args.args[0])
    assert payload == {
        "name": "DF_ORDERS_to_ORDERS_COPY", "projectName": "P",
        "sources": [{"connectionName": "SOURCE", "schemaName": "SRC", "dataEntityName": "ORDERS",
                     "operatorName": "SRC"}],
        "targets": [{"connectionName": "TARGET", "schemaName": "TGT", "dataEntityName": "ORDERS_COPY",
                     "operatorName": "TGT", "integrationType": "CONTROL_APPEND"}],
        "connections": [{"from": "SRC", "to": "TGT"}],
    }
    dt.create_dataflow_from_json_payload.assert_called_once()
    assert result == {"project_name": "P", "dataflow_name": "DF_ORDERS_to_ORDERS_COPY",
                      "project_id": "project-123", "action": "created", "success": True, "global_id": "df-123"}


@pytest.mark.parametrize("resource_type", ["dataflow", "workflow", "dataload"])
def test_pipeline_execution_dispatches_runtime_client(tools, clients, resource_type):
    ctx, _, wb = clients
    runtime = wb.get_runtime_client.return_value
    method = getattr(runtime, f"run_{resource_type}")
    method.return_value = {"session": "job-123"}
    result = json.loads(tools["dt_run_pipeline"].fn(
        project_name="P", resource_name="R", resource_type=resource_type, ctx=ctx))
    method.assert_called_once_with("P", "R")
    assert result == {"project": "P", "resource": "R", "type": resource_type,
                      "job_result": {"session": "job-123"}}


@pytest.mark.parametrize("tool,kwargs", [
    ("dt_manage_dataflow", {"project_name": "P", "dataflow_name": "D"}),
    ("dt_manage_workflow", {"action": "get", "project_name": "P", "workflow_name": "W"}),
    ("dt_manage_dataload", {"action": "list", "project_name": "P"}),
    ("dt_manage_project", {"action": "delete", "project_name": "P", "confirm": "P"}),
])
def test_missing_project_prevents_further_sdk_calls(tools, clients, tool, kwargs):
    ctx, dt, _ = clients
    dt.check_if_project_exists.return_value = None
    result = json.loads(tools[tool].fn(ctx=ctx, **kwargs))
    assert result == {"error": 'Project "P" not found.'}
    assert len(dt.mock_calls) == 1


@pytest.mark.parametrize("tool,kwargs", [
    ("dt_run_pipeline", {"project_name": "P", "resource_name": "R"}),
    ("dt_manage_connection", {"action": "create", "connection_name": "C"}),
    ("dt_manage_data_entities", {"action": "import_entities", "connection_name": "C", "schema_name": "S"}),
])
def test_operation_requiring_workbench_reports_missing_connection(tools, clients, monkeypatch, tool, kwargs):
    ctx, _, _ = clients
    ctx.request_context.lifespan_context["datatransforms"]["workbench"] = None
    monkeypatch.setitem(sys.modules, "datatransforms.connection", MagicMock())
    result = json.loads(tools[tool].fn(ctx=ctx, **kwargs))
    assert "workbench" in result["error"].lower()
