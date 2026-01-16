"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import UTC, datetime
from types import SimpleNamespace

import oci.util as oci_util
from oracle.oci_compute_instance_agent_mcp_server import models as mdl


class TestModels:
    def test_map_text_uri_tuple_outputs(self):
        text = mdl.map_text_output(
            {"exit_code": 0, "message": "m", "text": "t", "text_sha256": "h"}
        )
        assert text.output_type == "TEXT"
        assert text.exit_code == 0 and text.text == "t" and text.text_sha256 == "h"

        uri = mdl.map_uri_output(
            {"exit_code": 1, "message": "u", "output_uri": "https://x"}
        )
        assert uri.output_type == "OBJECT_STORAGE_URI" and uri.output_uri.startswith(
            "https://"
        )

        tup = mdl.map_tuple_output(
            {
                "exit_code": 2,
                "message": "tu",
                "bucket_name": "b",
                "namespace_name": "n",
                "object_name": "o",
            }
        )
        assert tup.output_type == "OBJECT_STORAGE_TUPLE"
        assert (
            tup.bucket_name == "b"
            and tup.namespace_name == "n"
            and tup.object_name == "o"
        )

    def test_map_output_content_none_and_unknown(self):
        assert mdl.map_output_content(None) is None
        unknown = SimpleNamespace(output_type="UNKNOWN")
        assert mdl.map_output_content(unknown) is None

    def test_map_instance_agent_command_execution_maps_fields(self, monkeypatch):
        # Force models._oci_to_dict to bypass oci.util.to_dict and use __dict__ fallback
        def boom(_):
            raise RuntimeError("boom")

        monkeypatch.setattr(oci_util, "to_dict", boom, raising=True)

        cmd = SimpleNamespace(
            instance_agent_command_id="id1",
            instance_id="inst",
            delivery_state="VISIBLE",
            lifecycle_state="SUCCEEDED",
            time_created=datetime.now(UTC),
            time_updated=datetime.now(UTC),
            sequence_number=42,
            display_name="name",
            content=SimpleNamespace(
                output_type="TEXT",
                exit_code=0,
                message="m",
                text="out",
                text_sha256="h",
            ),
        )
        res = mdl.map_instance_agent_command_execution(cmd)
        assert res.instance_agent_command_id == "id1"
        assert res.instance_id == "inst"
        assert res.delivery_state == "VISIBLE"
        assert res.lifecycle_state == "SUCCEEDED"
        assert res.sequence_number == 42
        assert res.display_name == "name"
        assert res.content is not None
        assert res.content.output_type == "TEXT"
        assert res.content.text == "out"
        assert res.content.exit_code == 0

    def test_map_instance_agent_command_execution_summary_maps_fields(
        self, monkeypatch
    ):
        # Force models._oci_to_dict to bypass oci.util.to_dict and use __dict__ fallback
        def boom(_):
            raise RuntimeError("boom")

        monkeypatch.setattr(oci_util, "to_dict", boom, raising=True)

        summ = SimpleNamespace(
            instance_agent_command_id="cid",
            instance_id="inst",
            delivery_state="PENDING",
            lifecycle_state="IN_PROGRESS",
            time_created=datetime.now(UTC),
            time_updated=datetime.now(UTC),
            sequence_number=7,
            display_name="dn",
            content=SimpleNamespace(
                output_type="TEXT",
                exit_code=0,
                text="ok",
                message="m",
                text_sha256="h",
            ),
        )
        res = mdl.map_instance_agent_command_execution_summary(summ)
        assert res.instance_agent_command_id == "cid"
        assert res.instance_id == "inst"
        assert res.delivery_state == "PENDING"
        assert res.lifecycle_state == "IN_PROGRESS"
        assert res.sequence_number == 7
        assert res.display_name == "dn"
        assert res.content is not None
        assert res.content.output_type == "TEXT"
        assert res.content.text == "ok"

    def test_map_instance_agent_command_summary_maps_fields(self):
        s = SimpleNamespace(
            instance_agent_command_id="sid",
            display_name="d",
            compartment_id="comp",
            time_created=datetime.now(UTC),
            time_updated=datetime.now(UTC),
            is_canceled=False,
        )
        res = mdl.map_instance_agent_command_summary(s)
        assert res.instance_agent_command_id == "sid"
        assert res.display_name == "d"
        assert res.compartment_id == "comp"
        assert res.is_canceled is False

    def test__oci_to_dict_fallback_with_namespace(self, monkeypatch):
        def boom(_):
            raise RuntimeError("boom")

        # Force _oci_to_dict to take the except path and then __dict__ path
        monkeypatch.setattr(oci_util, "to_dict", boom, raising=True)

        ns = SimpleNamespace(exit_code=3, message="e", text="ns", text_sha256="sha")
        out = mdl.map_text_output(ns)
        assert out.exit_code == 3
        assert out.text == "ns"
        assert out.text_sha256 == "sha"
