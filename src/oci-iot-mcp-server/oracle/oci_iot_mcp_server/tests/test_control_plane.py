from datetime import UTC, datetime
from types import SimpleNamespace

import oci
import pytest
from oci.iot.models import (
    DigitalTwinAdapterInboundEnvelope,
    DigitalTwinAdapterInboundRoute,
    DigitalTwinAdapterJsonPayload,
)

import oracle.oci_iot_mcp_server.control_plane as control_plane
from oracle.oci_iot_mcp_server import server
from oracle.oci_iot_mcp_server.control_plane import (
    build_invoke_raw_command_details,
    get_digital_twin_adapter_record,
    get_digital_twin_instance_content_record,
    get_digital_twin_instance_record,
    get_digital_twin_model_record,
    get_digital_twin_model_spec_record,
    get_digital_twin_relationship_record,
    get_iot_domain_group_record,
    get_iot_domain_record,
    get_work_request_record,
    invoke_raw_command,
    list_digital_twin_adapters_records,
    list_digital_twin_instances_records,
    list_digital_twin_models_records,
    list_digital_twin_relationships_records,
    list_iot_domain_groups_records,
    list_iot_domains_records,
    list_work_request_errors_records,
    list_work_request_logs_records,
    list_work_requests_records,
    map_digital_twin_adapter,
    map_digital_twin_instance,
    map_digital_twin_model,
    map_digital_twin_model_summary,
    map_digital_twin_relationship,
    map_iot_domain,
    map_iot_domain_group,
    map_work_request,
    map_work_request_error,
    map_work_request_log,
)


def _fake_adapter_envelope():
    return DigitalTwinAdapterInboundEnvelope(
        reference_endpoint="/telemetry",
        reference_payload=DigitalTwinAdapterJsonPayload(data_format="JSON"),
        envelope_mapping={"type": "messageType"},
    )


def _fake_adapter_route():
    return DigitalTwinAdapterInboundRoute(
        condition="true",
        payload_mapping={"temperature": "temp"},
    )


def test_map_iot_domain_includes_device_host_and_identity_domain_host():
    model = SimpleNamespace(
        id="ocid1.iotdomain.oc1..aaaa",
        display_name="factory-domain",
        device_host="abc123.device.iot.us-phoenix-1.oci.oraclecloud.com",
        db_allowed_identity_domain_host="id.example.com",
    )

    result = map_iot_domain(model)

    assert result["device_host"] == "abc123.device.iot.us-phoenix-1.oci.oraclecloud.com"
    assert result["db_allowed_identity_domain_host"] == "id.example.com"


def test_map_iot_domain_group_includes_data_host_and_db_token_scope():
    model = SimpleNamespace(
        id="ocid1.iotdomaingroup.oc1..aaaa",
        display_name="factory-group",
        data_host="xyz987.data.iot.us-phoenix-1.oci.oraclecloud.com",
        db_token_scope="ignored-by-ords-but-exposed",
    )

    result = map_iot_domain_group(model)

    assert result["data_host"].startswith("xyz987.data.iot.")
    assert result["db_token_scope"] == "ignored-by-ords-but-exposed"


def test_map_digital_twin_instance_includes_iot_domain_and_adapter_ids():
    model = SimpleNamespace(
        id="ocid1.digitaltwininstance.oc1..aaaa",
        display_name="pump-01",
        iot_domain_id="ocid1.iotdomain.oc1..aaaa",
        digital_twin_adapter_id="ocid1.digitaltwinadapter.oc1..aaaa",
        digital_twin_model_id="ocid1.digitaltwinmodel.oc1..aaaa",
        digital_twin_model_spec_uri="https://example.com/models/pump.json",
        connectivity_type="INDIRECT",
        gateways=["ocid1.digitaltwininstance.oc1..gateway"],
        auth_id="ocid1.iotauth.oc1..aaaa",
        external_key="pump-01-external",
        system_tags={"orcl-cloud": {"free-tier-retained": "true"}},
    )

    result = map_digital_twin_instance(model)

    assert result["iot_domain_id"] == "ocid1.iotdomain.oc1..aaaa"
    assert result["digital_twin_adapter_id"] == "ocid1.digitaltwinadapter.oc1..aaaa"
    assert result["digital_twin_model_id"] == "ocid1.digitaltwinmodel.oc1..aaaa"
    assert result["digital_twin_model_spec_uri"] == "https://example.com/models/pump.json"
    assert result["connectivity_type"] == "INDIRECT"
    assert result["gateways"] == ["ocid1.digitaltwininstance.oc1..gateway"]
    assert result["auth_id"] == "ocid1.iotauth.oc1..aaaa"
    assert result["external_key"] == "pump-01-external"
    assert result["system_tags"] == {"orcl-cloud": {"free-tier-retained": "true"}}


def test_map_digital_twin_adapter_includes_model_spec_and_routes():
    model = SimpleNamespace(
        id="ocid1.digitaltwinadapter.oc1..aaaa",
        display_name="pump-adapter",
        digital_twin_model_id="ocid1.digitaltwinmodel.oc1..aaaa",
        digital_twin_model_spec_uri="https://example.com/spec.json",
        inbound_envelope={"type": "JSON"},
        inbound_routes=[{"messageType": "telemetry"}],
    )

    result = map_digital_twin_adapter(model)

    assert result["digital_twin_model_id"] == "ocid1.digitaltwinmodel.oc1..aaaa"
    assert result["digital_twin_model_spec_uri"] == "https://example.com/spec.json"
    assert result["inbound_routes"] == [{"messageType": "telemetry"}]


def _build_fake_adapter():
    return SimpleNamespace(
        id="ocid1.digitaltwinadapter.oc1..bbbb",
        display_name="nested-adapter",
        digital_twin_model_id="ocid1.digitaltwinmodel.oc1..bbbb",
        digital_twin_model_spec_uri="https://example.com/spec-nested.json",
        inbound_envelope=_fake_adapter_envelope(),
        inbound_routes=[_fake_adapter_route()],
    )


def test_map_digital_twin_adapter_normalizes_nested_oci_objects():
    adapter = _build_fake_adapter()

    result = map_digital_twin_adapter(adapter)

    assert isinstance(result["inbound_envelope"], dict)
    assert isinstance(result["inbound_routes"], list)
    server.JSON_ADAPTER.dump_python(result, mode="json")


def test_server_get_iot_domain_delegates_to_control_plane(monkeypatch):
    monkeypatch.setattr(
        server,
        "get_iot_domain_record",
        lambda iot_domain_id: {
            "id": iot_domain_id,
            "device_host": "abc123.device.iot.us-phoenix-1.oci.oraclecloud.com",
        },
    )

    result = server.get_iot_domain("ocid1.iotdomain.oc1..aaaa")

    assert result["id"] == "ocid1.iotdomain.oc1..aaaa"
    assert result["device_host"].startswith("abc123.device.iot.")


def test_normalize_items_handles_collection_shapes():
    assert control_plane._normalize_items(SimpleNamespace(items=("a", "b"))) == ["a", "b"]
    assert control_plane._normalize_items(["a", "b"]) == ["a", "b"]
    assert control_plane._normalize_items(None) == []
    assert control_plane._normalize_items("item") == ["item"]


def test_map_model_variants_cover_remaining_resource_mappers():
    timestamp = datetime(2026, 3, 26, 12, 0, 0, tzinfo=UTC)

    model = SimpleNamespace(
        id="model-ocid",
        name="pump-model",
        description="A twin model",
        iot_domain_id="domain-ocid",
        spec_uri="dtmi:example:Pump;1",
        lifecycle_state="ACTIVE",
        created_at=timestamp,
        last_updated=timestamp,
        freeform_tags={"env": "dev"},
        defined_tags={"ns": {"key": "value"}},
        system_tags={"orcl-cloud": {"retained": "true"}},
    )
    summary = SimpleNamespace(
        id="summary-ocid",
        display_name="pump-model-summary",
        description="A twin model summary",
        iot_domain_id="domain-ocid",
        spec_uri="dtmi:example:PumpSummary;1",
        lifecycle_state="ACTIVE",
        time_created=timestamp,
        time_updated=timestamp,
        freeform_tags={"env": "test"},
        defined_tags={"ns": {"summary": "value"}},
        system_tags={"orcl-cloud": {"summary": "true"}},
    )
    relationship = SimpleNamespace(
        id="rel-ocid",
        display_name="parent-child",
        description="Relationship",
        iot_domain_id="domain-ocid",
        content_path="contains",
        source_digital_twin_instance_id="floor-1",
        target_digital_twin_instance_id="room-1",
        content={"confidence": 0.99},
        lifecycle_state="ACTIVE",
        time_created=timestamp,
        time_updated=timestamp,
        freeform_tags={"env": "rel"},
        defined_tags={"ns": {"relationship": "value"}},
        system_tags={"orcl-cloud": {"relationship": "true"}},
    )
    work_request = SimpleNamespace(
        id="wr-ocid",
        lifecycle_state="IN_PROGRESS",
        compartment_id="compartment-ocid",
        time_created=timestamp,
        time_updated=timestamp,
    )

    mapped_model = map_digital_twin_model(model)
    assert mapped_model["iot_domain_id"] == "domain-ocid"
    assert mapped_model["spec_uri"] == "dtmi:example:Pump;1"
    assert mapped_model["defined_tags"] == {"ns": {"key": "value"}}
    assert mapped_model["system_tags"] == {"orcl-cloud": {"retained": "true"}}

    mapped_summary = map_digital_twin_model_summary(summary)
    assert mapped_summary["name"] == "pump-model-summary"
    assert mapped_summary["iot_domain_id"] == "domain-ocid"
    assert mapped_summary["spec_uri"] == "dtmi:example:PumpSummary;1"
    assert mapped_summary["freeform_tags"] == {"env": "test"}
    assert mapped_summary["defined_tags"] == {"ns": {"summary": "value"}}
    assert mapped_summary["system_tags"] == {"orcl-cloud": {"summary": "true"}}

    mapped_relationship = map_digital_twin_relationship(relationship)
    assert mapped_relationship["name"] == "parent-child"
    assert mapped_relationship["iot_domain_id"] == "domain-ocid"
    assert mapped_relationship["content_path"] == "contains"
    assert mapped_relationship["source_digital_twin_instance_id"] == "floor-1"
    assert mapped_relationship["target_digital_twin_instance_id"] == "room-1"
    assert mapped_relationship["content"] == {"confidence": 0.99}
    assert mapped_relationship["freeform_tags"] == {"env": "rel"}
    assert mapped_relationship["defined_tags"] == {"ns": {"relationship": "value"}}
    assert mapped_relationship["system_tags"] == {"orcl-cloud": {"relationship": "true"}}
    assert map_work_request(work_request)["status"] == "IN_PROGRESS"
    assert map_work_request_error("boom") == {"code": None, "message": "boom", "timestamp": None}
    assert map_work_request_log("hello") == {"level": None, "message": "hello", "timestamp": None}


def test_map_one_and_map_many_wrappers_delegate_to_iot_client(monkeypatch):
    calls = []

    class FakeClient:
        def get_digital_twin_instance(self, **kwargs):
            calls.append(("get_digital_twin_instance", kwargs))
            return SimpleNamespace(data=SimpleNamespace(id="twin-1"))

        def list_iot_domains(self, **kwargs):
            calls.append(("list_iot_domains", kwargs))
            return SimpleNamespace(
                data=SimpleNamespace(
                    items=[
                        SimpleNamespace(id="domain-1"),
                        SimpleNamespace(id="domain-2"),
                    ]
                )
            )

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_instance", lambda model: {"id": model.id})
    monkeypatch.setattr(control_plane, "map_iot_domain", lambda model: {"id": model.id})

    detail = get_digital_twin_instance_record("twin-1")
    rows = list_iot_domains_records(compartment_id="compartment-ocid")

    assert detail == {"id": "twin-1"}
    assert rows == [{"id": "domain-1"}, {"id": "domain-2"}]
    assert calls == [
        ("get_digital_twin_instance", {"digital_twin_instance_id": "twin-1"}),
        ("list_iot_domains", {"compartment_id": "compartment-ocid"}),
    ]


def test_content_and_spec_wrappers_return_raw_response_data(monkeypatch):
    class FakeClient:
        def get_digital_twin_instance_content(self, **kwargs):
            assert kwargs == {"digital_twin_instance_id": "twin-1"}
            return SimpleNamespace(data={"content": "value"})

        def get_digital_twin_model_spec(self, **kwargs):
            assert kwargs == {"digital_twin_model_id": "model-1"}
            return SimpleNamespace(data={"spec": "value"})

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())

    assert get_digital_twin_instance_content_record("twin-1") == {"content": "value"}
    assert get_digital_twin_model_spec_record("model-1") == {"spec": "value"}


def test_content_and_spec_wrappers_return_json_safe_dict_response_data(monkeypatch):
    class FakeClient:
        def get_digital_twin_instance_content(self, **kwargs):
            assert kwargs == {"digital_twin_instance_id": "twin-1"}
            return SimpleNamespace(
                data={
                    "content": {"temperature": 73},
                    "metadata": {"status": "ok"},
                }
            )

        def get_digital_twin_model_spec(self, **kwargs):
            assert kwargs == {"digital_twin_model_id": "model-1"}
            return SimpleNamespace(
                data={
                    "contents": [
                        {
                            "@id": "dtmi:example:Pump;1",
                            "@type": "Interface",
                        }
                    ]
                }
            )

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())

    content = get_digital_twin_instance_content_record("twin-1")
    spec = get_digital_twin_model_spec_record("model-1")

    assert server.JSON_ADAPTER.dump_python(content, mode="json") == {
        "content": {"temperature": 73},
        "metadata": {"status": "ok"},
    }
    assert server.JSON_ADAPTER.dump_python(spec, mode="json") == {
        "contents": [{"@id": "dtmi:example:Pump;1", "@type": "Interface"}]
    }


def test_list_digital_twin_instances_records_forwards_sdk_filters(monkeypatch):
    captured = {}

    class FakeClient:
        def list_digital_twin_instances(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(data=[SimpleNamespace(id="twin-1")])

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_instance", lambda model: {"id": model.id})

    result = list_digital_twin_instances_records(
        iot_domain_id="domain-1",
        display_name="Pump 01",
        page="page-token",
        lifecycle_state="ACTIVE",
        sort_order="ASC",
        sort_by="displayName",
        opc_request_id="req-1",
        digital_twin_model_id="model-1",
        digital_twin_model_spec_uri="https://example.com/models/pump.json",
        connectivity_type="INDIRECT",
        id="twin-1",
        limit=50,
    )

    assert result == [{"id": "twin-1"}]
    assert captured == {
        "iot_domain_id": "domain-1",
        "display_name": "Pump 01",
        "page": "page-token",
        "lifecycle_state": "ACTIVE",
        "sort_order": "ASC",
        "sort_by": "displayName",
        "opc_request_id": "req-1",
        "digital_twin_model_id": "model-1",
        "digital_twin_model_spec_uri": "https://example.com/models/pump.json",
        "connectivity_type": "INDIRECT",
        "id": "twin-1",
        "limit": 50,
    }


def test_list_digital_twin_adapters_records_forwards_sdk_filters(monkeypatch):
    captured = {}

    class FakeClient:
        def list_digital_twin_adapters(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(data=[SimpleNamespace(id="adapter-1")])

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_adapter", lambda model: {"id": model.id})

    result = list_digital_twin_adapters_records(
        iot_domain_id="domain-1",
        id="adapter-1",
        digital_twin_model_spec_uri="dtmi:example:Pump;1",
        digital_twin_model_id="model-1",
        display_name="Pump Adapter",
        lifecycle_state="ACTIVE",
        page="page-token",
        limit=25,
        sort_order="ASC",
        sort_by="displayName",
        opc_request_id="req-1",
    )

    assert result == [{"id": "adapter-1"}]
    assert captured["kwargs"] == {
        "iot_domain_id": "domain-1",
        "id": "adapter-1",
        "digital_twin_model_spec_uri": "dtmi:example:Pump;1",
        "digital_twin_model_id": "model-1",
        "display_name": "Pump Adapter",
        "lifecycle_state": "ACTIVE",
        "page": "page-token",
        "limit": 25,
        "sort_order": "ASC",
        "sort_by": "displayName",
        "opc_request_id": "req-1",
    }


def test_list_digital_twin_models_records_forwards_sdk_filters(monkeypatch):
    captured = {}

    class FakeClient:
        def list_digital_twin_models(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(data=[SimpleNamespace(id="model-1")])

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_model_summary", lambda model: {"id": model.id})

    result = list_digital_twin_models_records(
        iot_domain_id="domain-1",
        id="model-1",
        display_name="Pump Model",
        spec_uri_starts_with="dtmi:example:Pump",
        lifecycle_state="ACTIVE",
        page="page-token",
        limit=25,
        sort_order="DESC",
        sort_by="timeCreated",
        opc_request_id="req-1",
    )

    assert result == [{"id": "model-1"}]
    assert captured["kwargs"] == {
        "iot_domain_id": "domain-1",
        "id": "model-1",
        "display_name": "Pump Model",
        "spec_uri_starts_with": "dtmi:example:Pump",
        "lifecycle_state": "ACTIVE",
        "page": "page-token",
        "limit": 25,
        "sort_order": "DESC",
        "sort_by": "timeCreated",
        "opc_request_id": "req-1",
    }


def test_list_digital_twin_adapter_and_model_page_records_return_pagination_metadata(monkeypatch):
    calls = []

    class FakeClient:
        def list_digital_twin_adapters(self, **kwargs):
            calls.append(("adapters", kwargs))
            return SimpleNamespace(
                data=SimpleNamespace(items=[SimpleNamespace(id="adapter-1")]),
                headers={"opc-next-page": "adapter-next", "opc-request-id": "adapter-req"},
                request_id=None,
            )

        def list_digital_twin_models(self, **kwargs):
            calls.append(("models", kwargs))
            return SimpleNamespace(
                data=SimpleNamespace(items=[SimpleNamespace(id="model-1")]),
                headers={"opc-next-page": "model-next"},
                request_id="model-req",
            )

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_adapter", lambda model: {"id": model.id})
    monkeypatch.setattr(control_plane, "map_digital_twin_model_summary", lambda model: {"id": model.id})

    adapter_page = control_plane.list_digital_twin_adapters_page_record(
        iot_domain_id="domain-1",
        page="adapter-page",
        limit=10,
    )
    model_page = control_plane.list_digital_twin_models_page_record(
        iot_domain_id="domain-1",
        page="model-page",
        limit=20,
    )

    assert calls == [
        ("adapters", {"iot_domain_id": "domain-1", "page": "adapter-page", "limit": 10}),
        ("models", {"iot_domain_id": "domain-1", "page": "model-page", "limit": 20}),
    ]
    assert adapter_page == {
        "items": [{"id": "adapter-1"}],
        "opc_next_page": "adapter-next",
        "opc_request_id": "adapter-req",
        "page": "adapter-page",
        "limit": 10,
        "has_more": True,
    }
    assert model_page == {
        "items": [{"id": "model-1"}],
        "opc_next_page": "model-next",
        "opc_request_id": "model-req",
        "page": "model-page",
        "limit": 20,
        "has_more": True,
    }


def test_domain_group_domain_and_work_request_lists_forward_sdk_filters(monkeypatch):
    calls = []

    class FakeClient:
        def list_iot_domain_groups(self, **kwargs):
            calls.append(("groups", kwargs))
            return SimpleNamespace(data=[SimpleNamespace(id="group-1")])

        def list_iot_domains(self, **kwargs):
            calls.append(("domains", kwargs))
            return SimpleNamespace(data=[SimpleNamespace(id="domain-1")])

        def list_work_requests(self, **kwargs):
            calls.append(("work-requests", kwargs))
            return SimpleNamespace(data=[SimpleNamespace(id="wr-1")])

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_iot_domain_group", lambda model: {"id": model.id})
    monkeypatch.setattr(control_plane, "map_iot_domain", lambda model: {"id": model.id})
    monkeypatch.setattr(control_plane, "map_work_request", lambda model: {"id": model.id})

    groups = list_iot_domain_groups_records(
        compartment_id="compartment-1",
        id="group-1",
        display_name="Group 1",
        lifecycle_state="ACTIVE",
        type="STANDARD",
        page="group-page",
        limit=25,
        sort_order="ASC",
        sort_by="displayName",
        opc_request_id="group-req",
    )
    domains = list_iot_domains_records(
        compartment_id="compartment-1",
        id="domain-1",
        iot_domain_group_id="group-1",
        display_name="Domain 1",
        lifecycle_state="ACTIVE",
        page="domain-page",
        limit=50,
        sort_order="DESC",
        sort_by="timeCreated",
        opc_request_id="domain-req",
    )
    work_requests = list_work_requests_records(
        compartment_id="compartment-1",
        id="wr-1",
        status="SUCCEEDED",
        resource_id="domain-1",
        page="wr-page",
        limit=10,
        sort_order="DESC",
        sort_by="timeAccepted",
        opc_request_id="wr-req",
    )

    assert groups == [{"id": "group-1"}]
    assert domains == [{"id": "domain-1"}]
    assert work_requests == [{"id": "wr-1"}]
    assert calls == [
        (
            "groups",
            {
                "compartment_id": "compartment-1",
                "id": "group-1",
                "display_name": "Group 1",
                "lifecycle_state": "ACTIVE",
                "type": "STANDARD",
                "page": "group-page",
                "limit": 25,
                "sort_order": "ASC",
                "sort_by": "displayName",
                "opc_request_id": "group-req",
            },
        ),
        (
            "domains",
            {
                "compartment_id": "compartment-1",
                "id": "domain-1",
                "iot_domain_group_id": "group-1",
                "display_name": "Domain 1",
                "lifecycle_state": "ACTIVE",
                "page": "domain-page",
                "limit": 50,
                "sort_order": "DESC",
                "sort_by": "timeCreated",
                "opc_request_id": "domain-req",
            },
        ),
        (
            "work-requests",
            {
                "compartment_id": "compartment-1",
                "id": "wr-1",
                "status": "SUCCEEDED",
                "resource_id": "domain-1",
                "page": "wr-page",
                "limit": 10,
                "sort_order": "DESC",
                "sort_by": "timeAccepted",
                "opc_request_id": "wr-req",
            },
        ),
    ]


def test_list_digital_twin_relationships_records_forwards_sdk_filters(monkeypatch):
    captured = {}

    class FakeClient:
        def list_digital_twin_relationships(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(data=[SimpleNamespace(id="rel-1")])

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_relationship", lambda model: {"id": model.id})

    result = list_digital_twin_relationships_records(
        iot_domain_id="domain-1",
        display_name="Floor contains Room",
        content_path="contains",
        source_digital_twin_instance_id="floor-1",
        target_digital_twin_instance_id="room-1",
        lifecycle_state="ACTIVE",
        page="page-token",
        sort_order="ASC",
        sort_by="displayName",
        opc_request_id="req-1",
        id="rel-1",
        limit=25,
    )

    assert result == [{"id": "rel-1"}]
    assert captured["kwargs"] == {
        "iot_domain_id": "domain-1",
        "display_name": "Floor contains Room",
        "content_path": "contains",
        "source_digital_twin_instance_id": "floor-1",
        "target_digital_twin_instance_id": "room-1",
        "lifecycle_state": "ACTIVE",
        "page": "page-token",
        "sort_order": "ASC",
        "sort_by": "displayName",
        "opc_request_id": "req-1",
        "id": "rel-1",
        "limit": 25,
    }


def test_list_digital_twin_relationships_page_record_returns_pagination_metadata(monkeypatch):
    captured = {}

    class FakeClient:
        def list_digital_twin_relationships(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(
                data=SimpleNamespace(items=[SimpleNamespace(id="rel-1")]),
                headers={"opc-next-page": "next-token", "opc-request-id": "req-1"},
                request_id=None,
            )

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_relationship", lambda model: {"id": model.id})

    result = control_plane.list_digital_twin_relationships_page_record(
        iot_domain_id="domain-1",
        page="page-token",
        limit=10,
    )

    assert captured["kwargs"] == {
        "iot_domain_id": "domain-1",
        "page": "page-token",
        "limit": 10,
    }
    assert result == {
        "items": [{"id": "rel-1"}],
        "opc_next_page": "next-token",
        "opc_request_id": "req-1",
        "page": "page-token",
        "limit": 10,
        "has_more": True,
    }


def test_list_digital_twin_instances_page_record_returns_pagination_metadata(monkeypatch):
    captured = {}

    class FakeClient:
        def list_digital_twin_instances(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(
                data=SimpleNamespace(items=[SimpleNamespace(id="twin-1")]),
                headers={"opc-next-page": "next-token", "opc-request-id": "req-1"},
                request_id=None,
            )

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_instance", lambda model: {"id": model.id})

    result = control_plane.list_digital_twin_instances_page_record(
        iot_domain_id="domain-1",
        connectivity_type="INDIRECT",
        page="page-token",
        limit=100,
    )

    assert captured["kwargs"] == {
        "iot_domain_id": "domain-1",
        "connectivity_type": "INDIRECT",
        "page": "page-token",
        "limit": 100,
    }
    assert result == {
        "items": [{"id": "twin-1"}],
        "opc_next_page": "next-token",
        "opc_request_id": "req-1",
        "page": "page-token",
        "limit": 100,
        "has_more": True,
    }


def test_list_all_digital_twin_relationships_records_respects_max_items(monkeypatch):
    calls = []
    pages = [
        SimpleNamespace(
            data=[SimpleNamespace(id="rel-1"), SimpleNamespace(id="rel-2")],
            headers={"opc-next-page": "page-2"},
            request_id="req-1",
        ),
        SimpleNamespace(
            data=[SimpleNamespace(id="rel-3")],
            headers={"opc-next-page": "page-3"},
            request_id="req-2",
        ),
    ]

    class FakeClient:
        def list_digital_twin_relationships(self, **kwargs):
            calls.append(kwargs)
            return pages[len(calls) - 1]

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_relationship", lambda model: {"id": model.id})

    result = control_plane.list_all_digital_twin_relationships_records(
        iot_domain_id="domain-1",
        max_items=3,
        page_size=2,
        lifecycle_state="ACTIVE",
    )

    assert calls == [
        {"iot_domain_id": "domain-1", "lifecycle_state": "ACTIVE", "limit": 2},
        {"iot_domain_id": "domain-1", "page": "page-2", "lifecycle_state": "ACTIVE", "limit": 1},
    ]
    assert result == {
        "items": [{"id": "rel-1"}, {"id": "rel-2"}, {"id": "rel-3"}],
        "count": 3,
        "max_items": 3,
        "page_size": 2,
        "pages_fetched": 2,
        "opc_next_page": "page-3",
        "opc_request_id": "req-2",
        "has_more": True,
        "truncated": True,
    }


def test_list_all_digital_twin_relationships_records_bounds_over_returning_page(monkeypatch):
    class FakeClient:
        def list_digital_twin_relationships(self, **_kwargs):
            return SimpleNamespace(
                data=[
                    SimpleNamespace(id="rel-1"),
                    SimpleNamespace(id="rel-2"),
                    SimpleNamespace(id="rel-3"),
                ],
                headers={"opc-next-page": "page-2"},
                request_id="req-1",
            )

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_relationship", lambda model: {"id": model.id})

    result = control_plane.list_all_digital_twin_relationships_records(
        iot_domain_id="domain-1",
        max_items=2,
        page_size=2,
    )

    assert result["items"] == [{"id": "rel-1"}, {"id": "rel-2"}]
    assert result["count"] == 2
    assert result["opc_next_page"] == "page-2"
    assert result["has_more"] is True
    assert result["truncated"] is True


def test_header_value_handles_missing_and_case_insensitive_headers():
    assert control_plane._header_value({}, "opc-next-page") is None
    assert control_plane._header_value({"Opc-Next-Page": "next-token"}, "opc-next-page") == "next-token"
    assert control_plane._header_value({"opc-request-id": "req-1"}, "opc-next-page") is None


def test_list_all_digital_twin_relationships_records_stops_when_no_next_page(monkeypatch):
    calls = []

    class FakeClient:
        def list_digital_twin_relationships(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                data=[SimpleNamespace(id="rel-1")],
                headers={},
                request_id="req-1",
            )

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_relationship", lambda model: {"id": model.id})

    result = control_plane.list_all_digital_twin_relationships_records(
        iot_domain_id="domain-1",
        max_items=5,
        page_size=2,
    )

    assert calls == [{"iot_domain_id": "domain-1", "limit": 2}]
    assert result == {
        "items": [{"id": "rel-1"}],
        "count": 1,
        "max_items": 5,
        "page_size": 2,
        "pages_fetched": 1,
        "opc_next_page": None,
        "opc_request_id": "req-1",
        "has_more": False,
        "truncated": False,
    }


def test_list_all_digital_twin_relationships_records_continues_after_empty_page_with_next_token(monkeypatch):
    calls = []
    pages = [
        SimpleNamespace(
            data=[],
            headers={"opc-next-page": "page-2"},
            request_id="req-1",
        ),
        SimpleNamespace(
            data=[SimpleNamespace(id="rel-2")],
            headers={},
            request_id="req-2",
        ),
    ]

    class FakeClient:
        def list_digital_twin_relationships(self, **kwargs):
            calls.append(kwargs)
            return pages[len(calls) - 1]

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_relationship", lambda model: {"id": model.id})

    result = control_plane.list_all_digital_twin_relationships_records(
        iot_domain_id="domain-1",
        max_items=5,
        page_size=2,
    )

    assert calls == [
        {"iot_domain_id": "domain-1", "limit": 2},
        {"iot_domain_id": "domain-1", "page": "page-2", "limit": 2},
    ]
    assert result == {
        "items": [{"id": "rel-2"}],
        "count": 1,
        "max_items": 5,
        "page_size": 2,
        "pages_fetched": 2,
        "opc_next_page": None,
        "opc_request_id": "req-2",
        "has_more": False,
        "truncated": False,
    }


def test_list_all_digital_twin_relationships_records_stops_at_page_limit(monkeypatch):
    calls = []

    class FakeClient:
        def list_digital_twin_relationships(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                data=[],
                headers={"opc-next-page": f"page-{len(calls) + 1}"},
                request_id=f"req-{len(calls)}",
            )

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())

    result = control_plane.list_all_digital_twin_relationships_records(
        iot_domain_id="domain-1",
        max_items=5,
        page_size=2,
    )

    assert len(calls) == 100
    assert calls[-1] == {"iot_domain_id": "domain-1", "page": "page-100", "limit": 2}
    assert result == {
        "items": [],
        "count": 0,
        "max_items": 5,
        "page_size": 2,
        "pages_fetched": 100,
        "opc_next_page": "page-101",
        "opc_request_id": "req-100",
        "has_more": True,
        "truncated": True,
        "pagination_warning": "Stopped relationship pagination after reaching the maximum of 100 SDK pages.",
    }


def test_list_all_digital_twin_relationships_records_stops_on_repeated_next_token(monkeypatch):
    calls = []
    pages = [
        SimpleNamespace(
            data=[SimpleNamespace(id="rel-1")],
            headers={"opc-next-page": "page-2"},
            request_id="req-1",
        ),
        SimpleNamespace(
            data=[SimpleNamespace(id="rel-2")],
            headers={"opc-next-page": "page-2"},
            request_id="req-2",
        ),
    ]

    class FakeClient:
        def list_digital_twin_relationships(self, **kwargs):
            calls.append(kwargs)
            if len(calls) > len(pages):
                raise AssertionError("repeated next token should stop pagination")
            return pages[len(calls) - 1]

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, "map_digital_twin_relationship", lambda model: {"id": model.id})

    result = control_plane.list_all_digital_twin_relationships_records(
        iot_domain_id="domain-1",
        max_items=6,
        page_size=2,
    )

    assert calls == [
        {"iot_domain_id": "domain-1", "limit": 2},
        {"iot_domain_id": "domain-1", "page": "page-2", "limit": 2},
    ]
    assert result == {
        "items": [{"id": "rel-1"}, {"id": "rel-2"}],
        "count": 2,
        "max_items": 6,
        "page_size": 2,
        "pages_fetched": 2,
        "opc_next_page": "page-2",
        "opc_request_id": "req-2",
        "has_more": True,
        "truncated": True,
        "pagination_warning": "Stopped relationship pagination because OCI returned a repeated opc-next-page token.",
    }


def test_list_all_digital_twin_relationships_records_validates_bounds():
    with pytest.raises(ValueError, match="max_items must be between 1 and 1000"):
        control_plane.list_all_digital_twin_relationships_records(
            iot_domain_id="domain-1",
            max_items=0,
        )

    with pytest.raises(ValueError, match="max_items must be between 1 and 1000"):
        control_plane.list_all_digital_twin_relationships_records(
            iot_domain_id="domain-1",
            max_items=1001,
        )

    with pytest.raises(ValueError, match="page_size must be between 1 and 1000"):
        control_plane.list_all_digital_twin_relationships_records(
            iot_domain_id="domain-1",
            page_size=0,
        )

    with pytest.raises(ValueError, match="page_size must be between 1 and 1000"):
        control_plane.list_all_digital_twin_relationships_records(
            iot_domain_id="domain-1",
            page_size=1001,
        )


@pytest.mark.parametrize(
    ("function_name", "kwargs"),
    [
        (
            "list_digital_twin_adapters_records",
            {
                "iot_domain_id": "domain-1",
                "id": "adapter-1",
                "digital_twin_model_spec_uri": "dtmi:example:Pump;1",
                "digital_twin_model_id": "model-1",
                "display_name": "Adapter 1",
                "lifecycle_state": "ACTIVE",
                "page": "page-1",
                "limit": 10,
                "sort_order": "ASC",
                "sort_by": "displayName",
                "opc_request_id": "req-1",
            },
        ),
        (
            "list_digital_twin_models_records",
            {
                "iot_domain_id": "domain-1",
                "id": "model-1",
                "display_name": "Model 1",
                "spec_uri_starts_with": "dtmi:example",
                "lifecycle_state": "ACTIVE",
                "page": "page-1",
                "limit": 10,
                "sort_order": "ASC",
                "sort_by": "displayName",
                "opc_request_id": "req-1",
            },
        ),
        (
            "list_digital_twin_instances_records",
            {
                "iot_domain_id": "domain-1",
                "display_name": "Twin 1",
                "page": "page-1",
                "lifecycle_state": "ACTIVE",
                "sort_order": "ASC",
                "sort_by": "displayName",
                "opc_request_id": "req-1",
                "digital_twin_model_id": "model-1",
                "digital_twin_model_spec_uri": "dtmi:example:Pump;1",
                "connectivity_type": "INDIRECT",
                "id": "twin-1",
                "limit": 10,
            },
        ),
        (
            "list_digital_twin_relationships_records",
            {
                "iot_domain_id": "domain-1",
                "display_name": "Contains",
                "content_path": "contains",
                "source_digital_twin_instance_id": "twin-1",
                "target_digital_twin_instance_id": "twin-2",
                "lifecycle_state": "ACTIVE",
                "page": "page-1",
                "sort_order": "ASC",
                "sort_by": "displayName",
                "opc_request_id": "req-1",
                "id": "rel-1",
                "limit": 10,
            },
        ),
        (
            "list_iot_domain_groups_records",
            {
                "compartment_id": "compartment-1",
                "id": "group-1",
                "display_name": "Group 1",
                "lifecycle_state": "ACTIVE",
                "type": "STANDARD",
                "page": "page-1",
                "limit": 10,
                "sort_order": "ASC",
                "sort_by": "displayName",
                "opc_request_id": "req-1",
            },
        ),
        (
            "list_iot_domains_records",
            {
                "compartment_id": "compartment-1",
                "id": "domain-1",
                "iot_domain_group_id": "group-1",
                "display_name": "Domain 1",
                "lifecycle_state": "ACTIVE",
                "page": "page-1",
                "limit": 10,
                "sort_order": "ASC",
                "sort_by": "displayName",
                "opc_request_id": "req-1",
            },
        ),
        (
            "list_work_requests_records",
            {
                "compartment_id": "compartment-1",
                "id": "work-1",
                "status": "ACCEPTED",
                "resource_id": "domain-1",
                "page": "page-1",
                "limit": 10,
                "sort_order": "ASC",
                "sort_by": "timeAccepted",
                "opc_request_id": "req-1",
            },
        ),
    ],
)
def test_list_wrappers_accept_current_oci_sdk_kwargs(monkeypatch, function_name, kwargs):
    calls = []

    class FakeBaseClient:
        def get_preferred_retry_strategy(self, **_kwargs):
            return oci.retry.NoneRetryStrategy()

        def call_api(self, **call_kwargs):
            calls.append(call_kwargs)
            return SimpleNamespace(data=SimpleNamespace(items=[]), headers={}, request_id="req-1")

    client = object.__new__(oci.iot.IotClient)
    client.base_client = FakeBaseClient()
    client.retry_strategy = None
    client.circuit_breaker_callback = None
    monkeypatch.setattr(control_plane, "get_iot_client", lambda: client)

    result = getattr(control_plane, function_name)(**kwargs)

    assert result == []
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("function_name", "method_name", "arg_name", "mapper_name", "arg_value"),
    [
        ("get_digital_twin_adapter_record", "get_digital_twin_adapter", "digital_twin_adapter_id", "map_digital_twin_adapter", "adapter-1"),
        ("get_digital_twin_model_record", "get_digital_twin_model", "digital_twin_model_id", "map_digital_twin_model", "model-1"),
        ("get_digital_twin_relationship_record", "get_digital_twin_relationship", "digital_twin_relationship_id", "map_digital_twin_relationship", "rel-1"),
        ("get_iot_domain_record", "get_iot_domain", "iot_domain_id", "map_iot_domain", "domain-1"),
        ("get_iot_domain_group_record", "get_iot_domain_group", "iot_domain_group_id", "map_iot_domain_group", "group-1"),
        ("get_work_request_record", "get_work_request", "work_request_id", "map_work_request", "wr-1"),
    ],
)
def test_get_record_wrappers_cover_remaining_single_resource_functions(
    monkeypatch,
    function_name,
    method_name,
    arg_name,
    mapper_name,
    arg_value,
):
    class FakeClient:
        pass

    def method(self, **kwargs):
        assert kwargs == {arg_name: arg_value}
        return SimpleNamespace(data=SimpleNamespace(id=arg_value))

    setattr(FakeClient, method_name, method)
    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, mapper_name, lambda model: {"id": model.id, "wrapped": True})

    result = getattr(control_plane, function_name)(arg_value)

    assert result == {"id": arg_value, "wrapped": True}


@pytest.mark.parametrize(
    ("function_name", "method_name", "kwargs", "mapper_name"),
    [
        ("list_digital_twin_adapters_records", "list_digital_twin_adapters", {"iot_domain_id": "domain-1"}, "map_digital_twin_adapter"),
        ("list_digital_twin_models_records", "list_digital_twin_models", {"iot_domain_id": "domain-1"}, "map_digital_twin_model_summary"),
        ("list_digital_twin_instances_records", "list_digital_twin_instances", {"iot_domain_id": "domain-1", "limit": 2}, "map_digital_twin_instance"),
        ("list_digital_twin_relationships_records", "list_digital_twin_relationships", {"iot_domain_id": "domain-1", "limit": 1000}, "map_digital_twin_relationship"),
        ("list_iot_domain_groups_records", "list_iot_domain_groups", {"compartment_id": "compartment-1"}, "map_iot_domain_group"),
        ("list_work_request_errors_records", "list_work_request_errors", {"work_request_id": "wr-1"}, "map_work_request_error"),
        ("list_work_request_logs_records", "list_work_request_logs", {"work_request_id": "wr-1"}, "map_work_request_log"),
        ("list_work_requests_records", "list_work_requests", {"compartment_id": "compartment-1"}, "map_work_request"),
    ],
)
def test_list_record_wrappers_cover_remaining_collection_functions(
    monkeypatch,
    function_name,
    method_name,
    kwargs,
    mapper_name,
):
    class FakeClient:
        pass

    def method(self, **method_kwargs):
        assert method_kwargs == kwargs
        return SimpleNamespace(data=(SimpleNamespace(id="row-1"), SimpleNamespace(id="row-2")))

    setattr(FakeClient, method_name, method)
    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())
    monkeypatch.setattr(control_plane, mapper_name, lambda model: {"id": model.id})

    result = getattr(control_plane, function_name)(**kwargs)

    assert result == [{"id": "row-1"}, {"id": "row-2"}]


def test_build_invoke_raw_command_details_supports_text_json_and_binary():
    text = build_invoke_raw_command_details(
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
    )
    payload = build_invoke_raw_command_details(
        request_endpoint="/v1/cmd",
        request_data_format="JSON",
        request_data={"mode": "auto"},
    )
    binary = build_invoke_raw_command_details(
        request_endpoint="/v1/cmd",
        request_data_format="BINARY",
        request_data="aGVsbG8=",
    )

    assert text.request_data == "PING"
    assert text.request_data_content_type == "text/plain"
    assert payload.request_data == {"mode": "auto"}
    assert payload.request_data_content_type == "application/json"
    assert binary.request_data == "aGVsbG8="
    assert binary.request_data_content_type == "application/octet-stream"


@pytest.mark.parametrize(
    ("request_data_format", "request_data", "message"),
    [
        ("TEXT", {"bad": "payload"}, "TEXT request_data must be a string."),
        ("JSON", "bad", "JSON request_data must be an object."),
        ("BINARY", 123, "BINARY request_data must be a base64-encoded string."),
        ("BINARY", "***", "Only base64 data is allowed"),
        ("YAML", "bad", "request_data_format must be one of TEXT, JSON, or BINARY."),
    ],
)
def test_build_invoke_raw_command_details_rejects_invalid_inputs(
    request_data_format,
    request_data,
    message,
):
    with pytest.raises(ValueError, match=message):
        build_invoke_raw_command_details(
            request_endpoint="/v1/cmd",
            request_data_format=request_data_format,
            request_data=request_data,
        )


def test_invoke_raw_command_returns_status_code_and_request_id(monkeypatch):
    observed = {}

    class FakeClient:
        def invoke_raw_command(self, **kwargs):
            observed.update(kwargs)
            return SimpleNamespace(status=202, headers={"opc-request-id": "opc-123"})

    monkeypatch.setattr(control_plane, "get_iot_client", lambda: FakeClient())

    result = invoke_raw_command(
        digital_twin_instance_id="twin-1",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
    )

    assert result == {"status_code": 202, "opc_request_id": "opc-123"}
    assert observed["digital_twin_instance_id"] == "twin-1"
    assert observed["invoke_raw_command_details"].request_data == "PING"
