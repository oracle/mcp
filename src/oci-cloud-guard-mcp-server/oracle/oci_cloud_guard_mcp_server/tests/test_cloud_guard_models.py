"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import oci
from oracle.oci_cloud_guard_mcp_server.models import (
    Problem,
    ResourceLock,
    UpdateProblemStatusDetails,
    _oci_to_dict,
    map_problem,
    map_resource_lock,
    map_resource_locks,
    map_update_problem_status_details,
)


class TestOciToDict:
    def test_none_returns_none(self):
        assert _oci_to_dict(None) is None

    def test_uses_oci_util_to_dict_when_available(self, monkeypatch):
        class SomeModel:
            def __init__(self):
                self.value = 42

        def fake_to_dict(obj):
            return {"converted": getattr(obj, "value", None)}

        # Patch oci.util.to_dict so the import inside _oci_to_dict picks it up
        monkeypatch.setattr(oci.util, "to_dict", fake_to_dict, raising=True)

        obj = SomeModel()
        result = _oci_to_dict(obj)
        assert result == {"converted": 42}

    def test_fallback_when_to_dict_raises_and_when_obj_is_dict(self, monkeypatch):
        def boom(_):
            raise Exception("boom")

        monkeypatch.setattr(oci.util, "to_dict", boom, raising=True)

        # When obj is already a dict, should be returned as-is
        data = {"a": 1, "b": 2}
        result = _oci_to_dict(data)
        assert result is data

    def test_fallback_to_dunder_dict_filters_private_attributes(self, monkeypatch):
        def boom(_):
            raise Exception("boom")

        monkeypatch.setattr(oci.util, "to_dict", boom, raising=True)

        class Holder:
            def __init__(self):
                self.a = 1
                self._b = 2  # should be filtered out

        obj = Holder()
        result = _oci_to_dict(obj)
        assert result == {"a": 1}
        assert "_b" not in result


class TestResourceLockMapping:
    def test_map_resource_lock_none(self):
        assert map_resource_lock(None) is None

    def test_map_resource_lock_maps_fields(self):
        now = datetime.now(timezone.utc)
        source = SimpleNamespace(
            type="FULL",
            related_resource_id="ocid1.test",
            message="locked for testing",
            time_created=now,
        )
        rl = map_resource_lock(source)
        assert isinstance(rl, ResourceLock)
        assert rl.type == "FULL"
        assert rl.related_resource_id == "ocid1.test"
        assert rl.message == "locked for testing"
        assert rl.time_created == now

    def test_map_resource_locks_none(self):
        assert map_resource_locks(None) is None

    def test_map_resource_locks_list(self):
        now = datetime.now(timezone.utc)
        items = [
            SimpleNamespace(
                type="DELETE",
                related_resource_id="ocid1.a",
                message="m1",
                time_created=now,
            ),
            SimpleNamespace(
                type="FULL",
                related_resource_id="ocid1.b",
                message="m2",
                time_created=now + timedelta(seconds=1),
            ),
        ]
        result = map_resource_locks(items)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(x, ResourceLock) for x in result)
        assert result[0].type == "DELETE"
        assert result[1].related_resource_id == "ocid1.b"


class TestProblemMapping:
    def test_map_problem_maps_all_known_fields_and_locks(self):
        now = datetime.now(timezone.utc)
        problem_data = SimpleNamespace(
            id="ocid1.problem.oc1..xyz",
            compartment_id="ocid1.compartment.oc1..abc",
            detector_rule_id="ocid1.rule.oc1..rule",
            region="us-ashburn-1",
            regions=["us-ashburn-1", "us-phoenix-1"],
            risk_level="HIGH",
            risk_score=85.5,
            peak_risk_score_date="2024-12-01T00:00:00Z",
            peak_risk_score=90.1,
            auto_resolve_date="2025-01-01T00:00:00Z",
            peak_risk_score_lookup_period_in_days=30,
            resource_id="ocid1.instance.oc1..res",
            resource_name="my-instance",
            resource_type="instance",
            labels=["tag1", "tag2"],
            time_last_detected=now,
            time_first_detected=now - timedelta(days=1),
            lifecycle_state="ACTIVE",
            lifecycle_detail="OPEN",
            detector_id="IAAS_ACTIVITY_DETECTOR",
            target_id="ocid1.target.oc1..tgt",
            additional_details={"k": "v"},
            description="desc",
            recommendation="reco",
            comment="user comment",
            impacted_resource_id="ocid1.impacted.oc1..res",
            impacted_resource_name="impacted-name",
            impacted_resource_type="compute",
            locks=[
                SimpleNamespace(
                    type="FULL",
                    related_resource_id="ocid1.lock.oc1..a",
                    message="m",
                    time_created=now,
                )
            ],
        )

        mapped = map_problem(problem_data)
        assert isinstance(mapped, Problem)
        assert mapped.id == problem_data.id
        assert mapped.compartment_id == problem_data.compartment_id
        assert mapped.detector_rule_id == problem_data.detector_rule_id
        assert mapped.region == problem_data.region
        assert mapped.regions == problem_data.regions
        assert mapped.risk_level == problem_data.risk_level
        assert mapped.risk_score == problem_data.risk_score
        assert mapped.peak_risk_score_date == problem_data.peak_risk_score_date
        assert mapped.peak_risk_score == problem_data.peak_risk_score
        assert mapped.auto_resolve_date == problem_data.auto_resolve_date
        assert (
            mapped.peak_risk_score_lookup_period_in_days == problem_data.peak_risk_score_lookup_period_in_days
        )
        assert mapped.resource_id == problem_data.resource_id
        assert mapped.resource_name == problem_data.resource_name
        assert mapped.resource_type == problem_data.resource_type
        assert mapped.labels == problem_data.labels
        assert mapped.time_last_detected == problem_data.time_last_detected
        assert mapped.time_first_detected == problem_data.time_first_detected
        assert mapped.lifecycle_state == problem_data.lifecycle_state
        assert mapped.lifecycle_detail == problem_data.lifecycle_detail
        assert mapped.detector_id == problem_data.detector_id
        assert mapped.target_id == problem_data.target_id
        assert mapped.additional_details == problem_data.additional_details
        assert mapped.description == problem_data.description
        assert mapped.recommendation == problem_data.recommendation
        assert mapped.comment == problem_data.comment
        assert mapped.impacted_resource_id == problem_data.impacted_resource_id
        assert mapped.impacted_resource_name == problem_data.impacted_resource_name
        assert mapped.impacted_resource_type == problem_data.impacted_resource_type
        assert mapped.locks is not None
        assert len(mapped.locks) == len(problem_data.locks)
        assert isinstance(mapped.locks[0], ResourceLock)
        assert mapped.locks[0].type == problem_data.locks[0].type

    def test_problem_model_instantiation_direct(self):
        lock = ResourceLock(type="DELETE", related_resource_id="x")
        p = Problem(id="p1", compartment_id="c1", locks=[lock])
        assert p.id == "p1"
        assert p.compartment_id == "c1"
        assert p.locks and p.locks[0].type == "DELETE"


class TestUpdateProblemStatusDetailsMapping:
    def test_map_update_problem_status_details_none(self):
        assert map_update_problem_status_details(None) is None

    def test_map_update_problem_status_details_maps_fields(self):
        src = SimpleNamespace(status="OPEN", comment="ok")
        mapped = map_update_problem_status_details(src)
        assert isinstance(mapped, UpdateProblemStatusDetails)
        assert mapped.status == "OPEN"
        assert mapped.comment == "ok"

    def test_update_problem_status_details_model_instantiation(self):
        m = UpdateProblemStatusDetails(status="RESOLVED", comment="done")
        assert m.status == "RESOLVED"
        assert m.comment == "done"
