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
        text_input = {"exit_code": 0, "message": "m", "text": "t", "text_sha256": "h"}
        text = mdl.map_text_output(text_input)
        assert text.output_type == "TEXT"
        assert (
            text.exit_code == text_input["exit_code"]
            and text.text == text_input["text"]
            and text.text_sha256 == text_input["text_sha256"]
        )

        uri_input = {"exit_code": 1, "message": "u", "output_uri": "https://x"}
        uri = mdl.map_uri_output(uri_input)
        assert uri.output_type == "OBJECT_STORAGE_URI" and uri.output_uri.startswith("https://")

        tup_input = {
            "exit_code": 2,
            "message": "tu",
            "bucket_name": "b",
            "namespace_name": "n",
            "object_name": "o",
        }
        tup = mdl.map_tuple_output(tup_input)
        assert tup.output_type == "OBJECT_STORAGE_TUPLE"
        assert (
            tup.bucket_name == tup_input["bucket_name"]
            and tup.namespace_name == tup_input["namespace_name"]
            and tup.object_name == tup_input["object_name"]
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
        assert res.instance_agent_command_id == cmd.instance_agent_command_id
        assert res.instance_id == cmd.instance_id
        assert res.delivery_state == cmd.delivery_state
        assert res.lifecycle_state == cmd.lifecycle_state
        assert res.sequence_number == cmd.sequence_number
        assert res.display_name == cmd.display_name
        assert res.content is not None
        assert res.content.output_type == cmd.content.output_type
        assert res.content.text == cmd.content.text
        assert res.content.exit_code == cmd.content.exit_code

    def test_map_instance_agent_command_execution_summary_maps_fields(self, monkeypatch):
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
        assert res.instance_agent_command_id == summ.instance_agent_command_id
        assert res.instance_id == summ.instance_id
        assert res.delivery_state == summ.delivery_state
        assert res.lifecycle_state == summ.lifecycle_state
        assert res.sequence_number == summ.sequence_number
        assert res.display_name == summ.display_name
        assert res.content is not None
        assert res.content.output_type == summ.content.output_type
        assert res.content.text == summ.content.text

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
        assert res.instance_agent_command_id == s.instance_agent_command_id
        assert res.display_name == s.display_name
        assert res.compartment_id == s.compartment_id
        assert res.is_canceled == s.is_canceled

    def test__oci_to_dict_fallback_with_namespace(self, monkeypatch):
        def boom(_):
            raise RuntimeError("boom")

        # Force _oci_to_dict to take the except path and then __dict__ path
        monkeypatch.setattr(oci_util, "to_dict", boom, raising=True)

        ns = SimpleNamespace(exit_code=3, message="e", text="ns", text_sha256="sha")
        out = mdl.map_text_output(ns)
        assert out.exit_code == ns.exit_code
        assert out.text == ns.text
        assert out.text_sha256 == ns.text_sha256
