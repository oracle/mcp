"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from types import SimpleNamespace

from oracle.oci_resource_search_mcp_server.models import (
    ResourceSummary,
    _oci_to_dict,
    map_resource_summary,
    map_search_context,
)


class TestSearchContext:
    def test_map_search_context_none(self):
        assert map_search_context(None) is None

    def test_map_search_context_with_highlights(self):
        sc = SimpleNamespace(highlights={"displayName": ["<h1>match</h1>"]})
        mapped = map_search_context(sc)
        assert mapped is not None
        assert mapped.highlights == {"displayName": ["<h1>match</h1>"]}


class TestResourceSummaryMapping:
    def test_map_resource_summary_full(self):
        ts = datetime(2024, 1, 2, 3, 4, 5)
        rs_input = SimpleNamespace(
            resource_type="instance",
            identifier="ocid1.instance.oc1..exampleuniqueID",
            compartment_id="ocid1.compartment.oc1..exampleuniqueID",
            time_created=ts,
            display_name="My Instance",
            availability_domain="AD-1",
            lifecycle_state="RUNNING",
            freeform_tags={"Owner": "Dev"},
            defined_tags={"Operations": {"CostCenter": "42"}},
            system_tags={"orcl-cloud": {"free-tier-retain": True}},
            search_context=SimpleNamespace(highlights={"displayName": ["<h1>My Instance</h1>"]}),
            identity_context={"keyA": "valueA"},
            additional_details={"attachedVnic": []},
        )

        mapped: ResourceSummary = map_resource_summary(rs_input)

        assert mapped.resource_type == "instance"
        assert mapped.identifier.startswith("ocid1.instance")
        assert mapped.compartment_id.startswith("ocid1.compartment")
        assert mapped.time_created == ts
        assert mapped.display_name == "My Instance"
        assert mapped.availability_domain == "AD-1"
        assert mapped.lifecycle_state == "RUNNING"
        assert mapped.freeform_tags == {"Owner": "Dev"}
        assert mapped.defined_tags == {"Operations": {"CostCenter": "42"}}
        assert mapped.system_tags == {"orcl-cloud": {"free-tier-retain": True}}
        assert mapped.search_context is not None
        assert mapped.search_context.highlights == {"displayName": ["<h1>My Instance</h1>"]}
        assert mapped.identity_context == {"keyA": "valueA"}
        assert mapped.additional_details == {"attachedVnic": []}

    def test_map_resource_summary_without_search_context(self):
        rs_input = SimpleNamespace(resource_type="volume", identifier="vol-1")
        mapped = map_resource_summary(rs_input)
        assert mapped.resource_type == "volume"
        assert mapped.identifier == "vol-1"
        assert mapped.search_context is None


class TestOciToDict:
    def test_oci_to_dict_none(self):
        assert _oci_to_dict(None) is None

    def test_oci_to_dict_pass_through_dict(self):
        data = {"a": 1, "b": 2}
        assert _oci_to_dict(data) == {"a": 1, "b": 2}

    def test_oci_to_dict_fallback_private_filtered(self, monkeypatch):
        class Dummy:
            def __init__(self):
                self.a = 1
                self._private = 2

        def raise_from_oci_to_dict(_):  # force fallback path
            raise RuntimeError("force fallback")

        # Ensure the function attempts oci.util.to_dict then falls back
        import oci.util as oci_util  # type: ignore

        monkeypatch.setattr(oci_util, "to_dict", raise_from_oci_to_dict, raising=True)

        out = _oci_to_dict(Dummy())
        assert out == {"a": 1}
