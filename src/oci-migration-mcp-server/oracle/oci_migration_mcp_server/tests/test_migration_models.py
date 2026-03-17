"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from types import SimpleNamespace

import oracle.oci_migration_mcp_server.models as models
from oracle.oci_migration_mcp_server.models import (
    Migration,
    MigrationSummary,
    _oci_to_dict,
    map_migration,
    map_migration_summary,
)


class TestMigrationModels:
    def test_oci_to_dict_variants(self):
        # None
        assert _oci_to_dict(None) is None

        # dict passthrough
        d = {"a": 1}
        assert _oci_to_dict(d) == d

        # object with __dict__ - accept either dict (fallback) or original object (SDK util behavior)
        obj = SimpleNamespace(x=1, _y=2)
        res = _oci_to_dict(obj)
        if isinstance(res, dict):
            assert res == {"x": 1}
        else:
            # In some environments, oci.util.to_dict may return the original object
            assert getattr(res, "x", None) == 1

    def test_oci_to_dict_fallback_when_oci_to_dict_raises(self, monkeypatch):
        # Force the oci.util.to_dict path to raise, covering the exception path and fallback

        class Dummy:
            def __init__(self):
                self.a = 1
                self._b = 2

        def raising(_):
            raise RuntimeError("boom")

        # Patch the to_dict function inside the oci.util module used by models
        monkeypatch.setattr(models.oci.util, "to_dict", raising, raising=False)

        res = models._oci_to_dict(Dummy())
        assert res == {"a": 1}

    def test_map_migration_full(self):
        src = SimpleNamespace(
            id="mig1",
            display_name="Migration One",
            compartment_id="ocid1.compartment.oc1..xyz",
            lifecycle_state="ACTIVE",
            lifecycle_details="All good",
            time_created="1970-01-01T00:00:00Z",
            time_updated="1970-01-01T01:00:00Z",
            replication_schedule_id="ocid1.rep.oc1..abc",
            is_completed=False,
            freeform_tags={"k": "v"},
            defined_tags={"ns": {"k": "v"}},
            system_tags={"orcl": {"res": "tag"}},
        )
        mapped = map_migration(src)
        assert isinstance(mapped, Migration)
        assert mapped.id == src.id
        assert mapped.display_name == src.display_name
        assert mapped.compartment_id == src.compartment_id
        assert mapped.lifecycle_state == src.lifecycle_state
        assert mapped.lifecycle_details == src.lifecycle_details
        expected_created = datetime.fromisoformat(src.time_created.replace("Z", "+00:00"))
        expected_updated = datetime.fromisoformat(src.time_updated.replace("Z", "+00:00"))
        assert mapped.time_created == expected_created
        assert mapped.time_updated == expected_updated
        assert mapped.replication_schedule_id == src.replication_schedule_id
        assert mapped.is_completed == src.is_completed
        assert mapped.freeform_tags == src.freeform_tags
        assert mapped.defined_tags == src.defined_tags
        assert mapped.system_tags == src.system_tags

    def test_map_migration_missing_fields(self):
        src = SimpleNamespace()  # no attributes
        mapped = map_migration(src)
        assert isinstance(mapped, Migration)
        assert mapped.id is None
        assert mapped.display_name is None
        assert mapped.compartment_id is None
        assert mapped.lifecycle_state is None
        assert mapped.lifecycle_details is None
        assert mapped.time_created is None
        assert mapped.time_updated is None
        assert mapped.replication_schedule_id is None
        assert mapped.is_completed is None
        assert mapped.freeform_tags is None
        assert mapped.defined_tags is None
        assert mapped.system_tags is None

    def test_map_migration_summary_full(self):
        src = SimpleNamespace(
            id="sum1",
            display_name="Summary One",
            compartment_id="ocid1.compartment.oc1..abc",
            time_created="1970-01-01T00:00:00Z",
            time_updated="1970-01-01T02:00:00Z",
            lifecycle_state="ACTIVE",
            lifecycle_details="Fine",
            is_completed=True,
            replication_schedule_id="ocid1.rep.oc1..xyz",
            freeform_tags={"a": "b"},
            defined_tags={"ns": {"k": "v"}},
            system_tags={"sys": {"t": "v"}},
        )
        mapped = map_migration_summary(src)
        assert isinstance(mapped, MigrationSummary)
        assert mapped.id == src.id
        assert mapped.display_name == src.display_name
        assert mapped.compartment_id == src.compartment_id
        expected_created = datetime.fromisoformat(src.time_created.replace("Z", "+00:00"))
        expected_updated = datetime.fromisoformat(src.time_updated.replace("Z", "+00:00"))
        assert mapped.time_created == expected_created
        assert mapped.time_updated == expected_updated
        assert mapped.lifecycle_state == src.lifecycle_state
        assert mapped.lifecycle_details == src.lifecycle_details
        assert mapped.is_completed == src.is_completed
        assert mapped.replication_schedule_id == src.replication_schedule_id
        assert mapped.freeform_tags == src.freeform_tags
        assert mapped.defined_tags == src.defined_tags
        assert mapped.system_tags == src.system_tags

    def test_map_migration_summary_missing_fields(self):
        src = SimpleNamespace()
        mapped = map_migration_summary(src)
        assert isinstance(mapped, MigrationSummary)
        assert mapped.id is None
        assert mapped.display_name is None
        assert mapped.compartment_id is None
        assert mapped.time_created is None
        assert mapped.time_updated is None
        assert mapped.lifecycle_state is None
        assert mapped.lifecycle_details is None
        assert mapped.is_completed is None
        assert mapped.replication_schedule_id is None
        assert mapped.freeform_tags is None
        assert mapped.defined_tags is None
        assert mapped.system_tags is None
