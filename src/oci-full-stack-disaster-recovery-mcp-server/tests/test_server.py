"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Tests for MCP server helper behavior and tool schema metadata.
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest
from pydantic.fields import FieldInfo

from oracle.oci_fsdr_mcp_server import server
from oracle.oci_fsdr_mcp_server.consts import ALLOWED_FSDR_OPERATIONS


def test_tool_parameters_use_pydantic_field_metadata():
    signature = inspect.signature(server.list_dr_protection_groups)
    compartment_id = signature.parameters["compartment_id"].default
    limit = signature.parameters["limit"].default

    assert isinstance(compartment_id, FieldInfo)
    assert compartment_id.description
    assert isinstance(limit, FieldInfo)
    assert limit.description


def test_raw_call_rejects_unknown_operation_before_creating_client():
    with pytest.raises(ValueError, match="Unsupported operation"):
        server.fsdr_raw_call(operation="not_a_real_operation", parameters={})


def test_allowed_operation_literal_matches_allow_list():
    operation = inspect.signature(server.fsdr_raw_call).parameters["operation"].default
    assert isinstance(operation, FieldInfo)
    assert "create_dr_plan_execution" in ALLOWED_FSDR_OPERATIONS


def test_resolve_model_instantiates_polymorphic_oci_model():
    model = server._resolve_model(
        {
            "_type": "CreateObjectStorageLogLocationDetails",
            "bucket": "dr-logs",
            "namespace": "mytenancy",
        }
    )

    assert model.bucket == "dr-logs"
    assert model.namespace == "mytenancy"


def test_resolve_model_recurses_plain_dicts_and_lists():
    result = server._resolve_model(
        {
            "members": [
                {
                    "_type": "CreateObjectStorageLogLocationDetails",
                    "bucket": "dr-logs",
                    "namespace": "mytenancy",
                }
            ],
            "unchanged": {"value": 1},
        }
    )

    assert result["members"][0].bucket == "dr-logs"
    assert result["unchanged"] == {"value": 1}


def test_prompt_functions_load_expected_files(monkeypatch):
    loaded = []

    def fake_load_prompt(filename):
        loaded.append(filename)
        return f"prompt:{filename}"

    monkeypatch.setattr(server, "_load_prompt", fake_load_prompt)

    assert server.setup_drpg_pair() == "prompt:setup_drpg_pair.md"
    assert server.check_dr_status() == "prompt:check_dr_status.md"
    assert server.run_switchover() == "prompt:run_switchover.md"
    assert server.run_drill() == "prompt:run_drill.md"
    assert server.run_failover() == "prompt:run_failover.md"
    assert server.plan_refresh_workflow() == "prompt:plan_refresh_workflow.md"
    assert server.add_members() == "prompt:add_members.md"
    assert loaded == [
        "setup_drpg_pair.md",
        "check_dr_status.md",
        "run_switchover.md",
        "run_drill.md",
        "run_failover.md",
        "plan_refresh_workflow.md",
        "add_members.md",
    ]


class FakeResponse:
    def __init__(self, data=None, headers=None, status=200):
        self.data = data
        self.headers = headers or {}
        self.status = status


class FakeFsdrClient:
    def __init__(self):
        self.calls = []

    def list_dr_protection_groups(self, **kwargs):
        self.calls.append(("list_dr_protection_groups", kwargs))
        return FakeResponse(
            data=SimpleNamespace(items=[SimpleNamespace(id="drpg1")]),
            headers={"opc-next-page": "next-drpg"},
        )

    def list_dr_plans(self, **kwargs):
        self.calls.append(("list_dr_plans", kwargs))
        return FakeResponse(
            data=SimpleNamespace(items=[SimpleNamespace(id="plan1")]),
            headers={"opc-next-page": "next-plan"},
        )

    def list_dr_plan_executions(self, **kwargs):
        self.calls.append(("list_dr_plan_executions", kwargs))
        return FakeResponse(
            data=SimpleNamespace(items=[SimpleNamespace(id="execution1")]),
            headers={"opc-next-page": "next-execution"},
        )

    def get_dr_protection_group(self, dr_protection_group_id):
        self.calls.append(("get_dr_protection_group", dr_protection_group_id))
        return FakeResponse(data=SimpleNamespace(id=dr_protection_group_id))

    def get_dr_plan(self, dr_plan_id):
        self.calls.append(("get_dr_plan", dr_plan_id))
        return FakeResponse(data=SimpleNamespace(id=dr_plan_id))

    def get_dr_plan_execution(self, dr_plan_execution_id):
        self.calls.append(("get_dr_plan_execution", dr_plan_execution_id))
        return FakeResponse(data=SimpleNamespace(id=dr_plan_execution_id))

    def get_work_request(self, work_request_id):
        self.calls.append(("get_work_request", work_request_id))
        return FakeResponse(data=SimpleNamespace(id=work_request_id))

    def create_dr_protection_group(self, **kwargs):
        self.calls.append(("create_dr_protection_group", kwargs))
        return FakeResponse(
            data=SimpleNamespace(id="created-drpg"),
            headers={"opc-work-request-id": "work-request-1"},
            status=202,
        )


def test_read_tools_call_expected_client_methods(monkeypatch):
    client = FakeFsdrClient()
    monkeypatch.setattr(server, "get_dr_client", lambda profile: client)
    monkeypatch.setattr(server, "to_dict", lambda value: {"id": value.id})

    drpgs = server.list_dr_protection_groups(
        compartment_id="compartment",
        lifecycle_state="ACTIVE",
        limit=5,
        page="page-1",
        profile="FSDR_REGION2",
    )
    plans = server.list_dr_plans_for_protection_group(
        dr_protection_group_id="drpg1",
        display_name="plan",
        plan_type="SWITCHOVER",
        limit=10,
        page="page-2",
        profile="FSDR_REGION2",
    )
    executions = server.list_dr_plan_executions_for_protection_group(
        dr_protection_group_id="drpg1",
        lifecycle_state="SUCCEEDED",
        limit=15,
        page="page-3",
        profile="FSDR_REGION2",
    )

    assert drpgs.items == [{"id": "drpg1"}]
    assert drpgs.opc_next_page == "next-drpg"
    assert plans.items == [{"id": "plan1"}]
    assert plans.opc_next_page == "next-plan"
    assert executions.items == [{"id": "execution1"}]
    assert executions.opc_next_page == "next-execution"
    assert client.calls[:3] == [
        (
            "list_dr_protection_groups",
            {
                "compartment_id": "compartment",
                "lifecycle_state": "ACTIVE",
                "limit": 5,
                "page": "page-1",
            },
        ),
        (
            "list_dr_plans",
            {
                "dr_protection_group_id": "drpg1",
                "display_name": "plan",
                "dr_plan_type": "SWITCHOVER",
                "limit": 10,
                "page": "page-2",
            },
        ),
        (
            "list_dr_plan_executions",
            {
                "dr_protection_group_id": "drpg1",
                "lifecycle_state": "SUCCEEDED",
                "limit": 15,
                "page": "page-3",
            },
        ),
    ]


def test_get_tools_normalize_oci_responses(monkeypatch):
    client = FakeFsdrClient()
    monkeypatch.setattr(server, "get_dr_client", lambda profile: client)
    monkeypatch.setattr(server, "to_dict", lambda value: {"id": value.id})

    assert server.get_dr_protection_group("drpg1").data == {"id": "drpg1"}
    assert server.get_dr_plan("plan1").data == {"id": "plan1"}
    assert server.get_dr_plan_execution("execution1").data == {"id": "execution1"}
    assert server.get_work_request("work1").data == {"id": "work1"}
    assert client.calls == [
        ("get_dr_protection_group", "drpg1"),
        ("get_dr_plan", "plan1"),
        ("get_dr_plan_execution", "execution1"),
        ("get_work_request", "work1"),
    ]


def test_response_to_result_handles_empty_data_and_headers():
    result = server._response_to_result(FakeResponse(data=None, headers=None, status=204))

    assert result.data is None
    assert result.status == 204
    assert result.headers == {}


def test_fsdr_raw_call_converts_details_and_returns_work_request(monkeypatch):
    client = FakeFsdrClient()
    monkeypatch.setattr(server, "get_dr_client", lambda profile: client)
    monkeypatch.setattr(server, "to_dict", lambda value: {"id": value.id})

    result = server.fsdr_raw_call(
        operation="create_dr_protection_group",
        parameters={
            "create_dr_protection_group_details": {
                "display_name": "Primary DRPG",
                "compartment_id": "compartment",
                "log_location": {
                    "_type": "CreateObjectStorageLogLocationDetails",
                    "bucket": "dr-logs",
                    "namespace": "mytenancy",
                },
            },
            "retry_token": "retry-1",
        },
        profile="FSDR_REGION2",
    )

    assert result.status == 202
    assert result.data == {"id": "created-drpg"}
    assert result.work_request_id == "work-request-1"
    _, kwargs = client.calls[-1]
    details = kwargs["create_dr_protection_group_details"]
    assert details.display_name == "Primary DRPG"
    assert details.compartment_id == "compartment"
    assert details.log_location.bucket == "dr-logs"
    assert kwargs["retry_token"] == "retry-1"


def test_main_runs_stdio_without_banner(monkeypatch):
    run_kwargs = {}

    def fake_run(**kwargs):
        run_kwargs.update(kwargs)

    monkeypatch.setattr(server.mcp, "run", fake_run)

    server.main()

    assert run_kwargs == {"show_banner": False}
