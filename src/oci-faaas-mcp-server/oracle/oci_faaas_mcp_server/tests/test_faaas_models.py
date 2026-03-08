"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import sys
import types
from types import SimpleNamespace

# Provide a lightweight stub for 'oci' if not installed, so tests can import/utilize models helpers
try:
    import oci  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    oci = types.SimpleNamespace()
    sys.modules["oci"] = oci
    oci.util = types.SimpleNamespace(to_dict=lambda x: x)

from oracle.oci_faaas_mcp_server import models as mdl


class TestFaaasModels:
    def test__get_for_dict_and_object(self):
        d = {"k": "v"}
        obj = SimpleNamespace(k="v", other=1)
        assert mdl._get(d, "k") == "v"
        assert mdl._get(obj, "k") == "v"
        assert mdl._get(obj, "missing") is None

    def test__oci_to_dict_prefers_oci_util_to_dict(self, monkeypatch):
        # Force using oci.util.to_dict
        def to_dict_override(x):
            return {"used_oci_to_dict": True, "value": getattr(x, "v", None)}

        monkeypatch.setattr(oci.util, "to_dict", to_dict_override, raising=True)

        ns = SimpleNamespace(v=123)
        out = mdl._oci_to_dict(ns)
        assert out == {"used_oci_to_dict": True, "value": 123}

    def test__oci_to_dict_fallbacks(self, monkeypatch):
        # Make oci.util.to_dict raise to exercise fallbacks
        def boom(_):
            raise RuntimeError("boom")

        monkeypatch.setattr(oci.util, "to_dict", boom, raising=True)

        # dict passthrough
        d = {"a": 1}
        assert mdl._oci_to_dict(d) == d

        # __dict__ fallback
        ns = SimpleNamespace(a=2, _private=3)
        out = mdl._oci_to_dict(ns)
        assert out == {"a": 2}  # private filtered

        # non-dict and without __dict__ returns None
        assert mdl._oci_to_dict(5) is None

    def test_map_fusion_environment_family_from_dict_and_obj(self):
        d = {
            "id": "fam1",
            "display_name": "Family 1",
            "lifecycle_state": "ACTIVE",
            "compartment_id": "ocid1.compartment...",
        }
        fam_d = mdl.map_fusion_environment_family(d)
        assert fam_d.id == d["id"] and fam_d.display_name == d["display_name"]
        assert fam_d.lifecycle_state == d["lifecycle_state"]

        obj = SimpleNamespace(
            id="fam2",
            display_name="Family 2",
            lifecycle_state="CREATING",
            compartment_id="ocid1.compartment..x",
        )
        fam_o = mdl.map_fusion_environment_family(obj)
        assert fam_o.id == obj.id and fam_o.display_name == obj.display_name
        assert fam_o.lifecycle_state == obj.lifecycle_state

    def test_map_fusion_environment_includes_maintenance_policy_to_dict(self, monkeypatch):
        # Ensure maintenance_policy goes through _oci_to_dict via oci.util.to_dict
        def to_dict_override(x):
            # Simulate SDK model conversion
            if hasattr(x, "__dict__"):
                return {"foo": getattr(x, "foo", None)}
            return x

        monkeypatch.setattr(oci.util, "to_dict", to_dict_override, raising=True)

        data = SimpleNamespace(
            id="env1",
            display_name="Env 1",
            compartment_id="ocid1.compartment..x",
            fusion_environment_family_id="ocid1.fusionfamily..y",
            fusion_environment_type="PRODUCTION",
            version="25C",
            public_url="https://example.com",
            idcs_domain_url="https://idcs.example.com",
            domain_id="ocid1.domain..z",
            lifecycle_state="ACTIVE",
            lifecycle_details="ok",
            is_suspended=False,
            system_name="SYS",
            environment_role="PRIMARY",
            maintenance_policy=SimpleNamespace(foo=1),
            time_upcoming_maintenance=None,
            applied_patch_bundles=["p1"],
            subscription_ids=["sub1"],
            additional_language_packs=["en"],
            kms_key_id=None,
            kms_key_info=None,
            dns_prefix="pre",
            lockbox_id=None,
            is_break_glass_enabled=False,
            refresh=None,
            rules=None,
            time_created=None,
            time_updated=None,
            freeform_tags={"a": "b"},
            defined_tags={"ns": {"k": "v"}},
        )
        env = mdl.map_fusion_environment(data)
        assert env.id == data.id and env.display_name == data.display_name
        assert env.fusion_environment_type == data.fusion_environment_type
        assert env.maintenance_policy == {"foo": 1}
        assert env.applied_patch_bundles == data.applied_patch_bundles
        assert env.freeform_tags == data.freeform_tags
        assert env.defined_tags == data.defined_tags

    def test_map_fusion_environment_status_id_fallback_and_details(self, monkeypatch):
        # Case 1: id fallback and details filter with to_dict data present
        def to_dict_ok(x):
            return {
                "id": getattr(x, "id", None),
                "status": getattr(x, "status", None),
                "time_updated": getattr(x, "time_updated", None),
                "time_created": getattr(x, "time_created", None),
                "extra": "keepme",
            }

        monkeypatch.setattr(oci.util, "to_dict", to_dict_ok, raising=True)

        src = SimpleNamespace(
            id="env1",
            status="ACTIVE",
            time_updated="2025-01-01T00:00:00Z",
            time_created="2025-01-01T00:00:00Z",
        )
        st = mdl.map_fusion_environment_status(src)
        assert st.fusion_environment_id == src.id
        assert st.status == src.status
        assert st.details == {"extra": "keepme"}

        # Case 2: if _oci_to_dict returns None, details becomes None
        # Patch mdl._oci_to_dict directly to simulate None
        monkeypatch.setattr(mdl, "_oci_to_dict", lambda _: None, raising=True)
        src2 = SimpleNamespace(fusion_environment_id="env2", status="INACTIVE")
        st2 = mdl.map_fusion_environment_status(src2)
        assert st2.fusion_environment_id == src2.fusion_environment_id
        assert st2.details is None
