"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace

import oracle.oci_logging_mcp_server.models as models
from oracle.oci_logging_mcp_server.models import (
    Archiving,
    Configuration,
    FieldInfo,
    Log,
    LogGroup,
    LogGroupSummary,
    LogSummary,
    OciService,
    SearchResponse,
    SearchResult,
    SearchResultSummary,
    Source,
    _oci_to_dict,
    map_archiving,
    map_configuration,
    map_field_info,
    map_log,
    map_log_group,
    map_log_group_summary,
    map_log_summary,
    map_search_response,
    map_search_result,
    map_search_result_summary,
    map_source,
)


class TestLoggingModels:
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
            # In some environments, oci.util.to_dict returns the original object
            assert getattr(res, "x", None) == 1

    def test_map_log_group_summary_none_and_values(self):
        assert map_log_group_summary(None) is None

        src = SimpleNamespace(
            id="lg1",
            compartment_id="comp1",
            display_name="Group 1",
            description="desc",
            defined_tags={"ns": {"k": "v"}},
            freeform_tags={"k": "v"},
            time_created="1970-01-01T00:00:00Z",
            time_last_modified="1970-01-01T00:00:01Z",
            lifecycle_state="ACTIVE",
        )
        dst = map_log_group_summary(src)
        assert isinstance(dst, LogGroupSummary)
        assert dst.id == src.id
        assert dst.compartment_id == src.compartment_id
        assert dst.lifecycle_state == src.lifecycle_state

    def test_map_log_group_none_and_values(self):
        assert map_log_group(None) is None

        src = SimpleNamespace(
            id="lg2",
            compartment_id="comp2",
            display_name="Group 2",
            description="d2",
            lifecycle_state="ACTIVE",
            defined_tags={"ns": {"k": "v"}},
            freeform_tags={"k": "v"},
            time_created="1970-01-01T00:00:00Z",
            time_last_modified="1970-01-01T00:00:01Z",
        )
        dst = map_log_group(src)
        assert isinstance(dst, LogGroup)
        assert dst.id == src.id
        assert dst.lifecycle_state == src.lifecycle_state

    def test_map_archiving_none_and_values(self):
        assert map_archiving(None) is None
        arch = SimpleNamespace(is_enabled=True)
        dst = map_archiving(arch)
        assert isinstance(dst, Archiving)
        assert dst.is_enabled == arch.is_enabled

    def test_map_source_generic_without_sdk_class(self):
        # Not an SDK instance -> should map to generic Source
        src = SimpleNamespace(source_type="OCISERVICE", service="svc", resource="res")
        mapped = map_source(src)
        assert isinstance(mapped, Source)
        assert not isinstance(mapped, OciService)
        assert mapped.source_type == src.source_type

    def test_map_source_specific_oci_service_class(self, monkeypatch):
        # Monkeypatch the SDK class reference inside models to hit the explicit OciService path

        class DummyOciService:
            def __init__(self):
                self.source_type = "OCISERVICE"
                self.service = "svc"
                self.resource = "res"
                self.category = "cat"
                self.parameters = {"p": "v"}

        # Ensure oci.logging.models.OciService exists and is our dummy class
        dummy_logging_models = SimpleNamespace(OciService=DummyOciService)
        dummy_logging = SimpleNamespace(models=dummy_logging_models)
        dummy_oci = SimpleNamespace(logging=dummy_logging)

        monkeypatch.setattr(models, "oci", dummy_oci, raising=True)

        mapped = models.map_source(DummyOciService())
        assert isinstance(mapped, OciService)
        assert mapped.source_type == "OCISERVICE"
        assert mapped.service == "svc"
        assert mapped.parameters == {"p": "v"}

    def test_map_configuration_with_nested(self):
        cfg = SimpleNamespace(
            compartment_id="compX",
            source=SimpleNamespace(source_type="OCISERVICE"),
            archiving=SimpleNamespace(is_enabled=False),
        )
        mapped = map_configuration(cfg)
        assert isinstance(mapped, Configuration)
        assert mapped.compartment_id == cfg.compartment_id
        assert isinstance(mapped.source, Source)
        assert isinstance(mapped.archiving, Archiving)
        assert mapped.archiving.is_enabled == cfg.archiving.is_enabled

    def test_map_log_summary_nested(self):
        log = SimpleNamespace(
            id="log1",
            log_group_id="lg1",
            display_name="L1",
            is_enabled=True,
            lifecycle_state="ACTIVE",
            log_type="SERVICE",
            configuration=SimpleNamespace(
                compartment_id="compY",
                source=SimpleNamespace(source_type="OCISERVICE"),
                archiving=SimpleNamespace(is_enabled=True),
            ),
            defined_tags={"ns": {"k": "v"}},
            freeform_tags={"k": "v"},
            time_created="1970-01-01T00:00:00Z",
            time_last_modified="1970-01-01T00:00:01Z",
            retention_duration=30,
            compartment_id="compY",
        )
        mapped = map_log_summary(log)
        assert isinstance(mapped, LogSummary)
        assert mapped.id == log.id
        assert mapped.configuration is not None
        assert mapped.configuration.archiving.is_enabled == log.configuration.archiving.is_enabled

    def test_map_log_nested(self):
        log = SimpleNamespace(
            id="logX",
            tenancy_id="ten",
            log_group_id="lg",
            display_name="DX",
            log_type="CUSTOM",
            is_enabled=False,
            defined_tags={"a": {"b": "c"}},
            freeform_tags={"k": "v"},
            configuration=SimpleNamespace(
                compartment_id="compZ",
                source=SimpleNamespace(source_type="OCISERVICE"),
                archiving=SimpleNamespace(is_enabled=False),
            ),
            lifecycle_state="INACTIVE",
            time_created="1970-01-01T00:00:00Z",
            time_last_modified="1970-01-01T01:00:00Z",
            retention_duration=60,
            compartment_id="compZ",
        )
        mapped = map_log(log)
        assert isinstance(mapped, Log)
        assert mapped.log_type == log.log_type
        assert mapped.configuration.source.source_type == log.configuration.source.source_type

    def test_map_search_response_full(self):
        # FieldInfo mapping
        fi = SimpleNamespace(field_name="x", field_type="STRING")
        # SearchResult mapping; ensure dict type for pydantic model validation
        sr = SimpleNamespace(data={"k": "v"})
        # Summary mapping
        summary = SimpleNamespace(result_count=1, field_count=1)

        src = SimpleNamespace(results=[sr], fields=[fi], summary=summary)
        mapped = map_search_response(src)
        assert isinstance(mapped, SearchResponse)
        assert isinstance(mapped.fields[0], FieldInfo)
        assert mapped.fields[0].field_name == fi.field_name
        assert isinstance(mapped.results[0], SearchResult)
        assert mapped.results[0].data == sr.data
        assert isinstance(mapped.summary, SearchResultSummary)
        assert mapped.summary.result_count == summary.result_count

    def test_map_helpers_individual(self):
        field_input = SimpleNamespace(field_name="f", field_type="NUMBER")
        fi = map_field_info(field_input)
        assert isinstance(fi, FieldInfo)
        assert fi.field_type == field_input.field_type

        search_result_input = SimpleNamespace(data={"a": 1})
        sr = map_search_result(search_result_input)
        assert isinstance(sr, SearchResult)
        assert sr.data == search_result_input.data

        summary_input = SimpleNamespace(result_count=3, field_count=2)
        srs = map_search_result_summary(summary_input)
        assert isinstance(srs, SearchResultSummary)
        assert srs.field_count == summary_input.field_count

    def test_oci_to_dict_uses_oci_util(self, monkeypatch):
        import sys
        import types

        def fake_to_dict(obj):
            return {"fake": True}

        # If oci.util is already present, patch its to_dict. Otherwise, inject a minimal module.
        if "oci.util" in sys.modules:
            monkeypatch.setattr(sys.modules["oci.util"], "to_dict", fake_to_dict, raising=False)
        else:
            util_mod = types.ModuleType("oci.util")
            util_mod.to_dict = fake_to_dict
            sys.modules["oci.util"] = util_mod

        res = models._oci_to_dict(SimpleNamespace(a=1))
        assert res == {"fake": True}

    def test_models_none_mapping_helpers(self):
        # Ensure None inputs return None across helpers
        assert map_field_info(None) is None
        assert map_search_result(None) is None
        assert map_search_result_summary(None) is None
        assert map_configuration(None) is None
        assert map_search_response(None) is None
