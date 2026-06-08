"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Tests for Pydantic response models.
"""

import pytest
from oracle.oci_fsdr_mcp_server.models import (
    DrPlanExecutionSummary,
    DrPlanSummary,
    DrProtectionGroupSummary,
    ListResult,
    OciResponseResult,
    WorkRequestSummary,
    WriteResult,
)


def test_drpg_summary_from_sdk_dict():
    d = {
        "id": "ocid1.drprotectiongroup.oc1..xxx",
        "display_name": "Primary DRPG",
        "compartment_id": "ocid1.compartment.oc1..yyy",
        "role": "PRIMARY",
        "lifecycle_state": "ACTIVE",
        "peer_id": "ocid1.drprotectiongroup.oc1..zzz",
        "peer_region": "us-phoenix-1",
        "time_created": "2024-01-01T00:00:00Z",
        "freeform_tags": {},
        "defined_tags": {},
    }
    m = DrProtectionGroupSummary.from_sdk_dict(d)
    assert m.id == d["id"]
    assert m.role == "PRIMARY"
    assert m.peer_region == "us-phoenix-1"


def test_drpg_summary_ignores_extra_fields():
    d = {
        "id": "ocid1.drprotectiongroup.oc1..xxx",
        "display_name": "Test",
        "compartment_id": "ocid1.compartment.oc1..yyy",
        "some_unknown_field": "should_be_ignored",
    }
    m = DrProtectionGroupSummary.from_sdk_dict(d)
    assert not hasattr(m, "some_unknown_field")


def test_dr_plan_summary():
    d = {
        "id": "ocid1.drplan.oc1..xxx",
        "display_name": "Switchover Plan",
        "type": "SWITCHOVER",
        "lifecycle_state": "ACTIVE",
        "dr_protection_group_id": "ocid1.drprotectiongroup.oc1..yyy",
    }
    m = DrPlanSummary.from_sdk_dict(d)
    assert m.type == "SWITCHOVER"
    assert m.lifecycle_state == "ACTIVE"


def test_dr_plan_execution_summary():
    d = {
        "id": "ocid1.drplanexecution.oc1..xxx",
        "display_name": "Drill Run 1",
        "plan_execution_type": "START_DRILL",
        "lifecycle_state": "SUCCEEDED",
        "dr_protection_group_id": "ocid1.drprotectiongroup.oc1..yyy",
        "plan_id": "ocid1.drplan.oc1..zzz",
        "execution_duration_in_sec": 3600,
    }
    m = DrPlanExecutionSummary.from_sdk_dict(d)
    assert m.plan_execution_type == "START_DRILL"
    assert m.execution_duration_in_sec == 3600


def test_work_request_summary():
    d = {
        "id": "ocid1.workrequest.oc1..xxx",
        "operation_type": "CREATE_DR_PROTECTION_GROUP",
        "status": "SUCCEEDED",
        "percent_complete": 100.0,
        "compartment_id": "ocid1.compartment.oc1..yyy",
    }
    m = WorkRequestSummary.from_sdk_dict(d)
    assert m.status == "SUCCEEDED"
    assert m.percent_complete == 100.0


def test_list_result():
    items = [{"id": "1", "display_name": "A"}, {"id": "2", "display_name": "B"}]
    r = ListResult.from_items(items, next_page="token123")
    assert r.total_items == 2
    assert r.opc_next_page == "token123"
    d = r.model_dump()
    assert d["total_items"] == 2


def test_list_result_no_next_page():
    r = ListResult.from_items([], next_page=None)
    assert r.total_items == 0
    assert r.opc_next_page is None


def test_write_result():
    r = WriteResult(status=200, work_request_id="ocid1.workrequest.oc1..xxx")
    assert r.status == 200
    assert r.work_request_id is not None


def test_oci_response_result():
    r = OciResponseResult(status=200, headers={"opc-request-id": "req"}, data={"id": "1"})
    assert r.headers["opc-request-id"] == "req"


def test_model_schema_has_field_descriptions_and_enums():
    schema = DrPlanSummary.model_json_schema()
    assert schema["properties"]["id"]["description"]
    assert "SWITCHOVER" in schema["properties"]["type"]["enum"]
