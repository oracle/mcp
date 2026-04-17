from datetime import UTC, datetime
from types import SimpleNamespace

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
    )

    result = map_digital_twin_instance(model)

    assert result["iot_domain_id"] == "ocid1.iotdomain.oc1..aaaa"
    assert result["digital_twin_adapter_id"] == "ocid1.digitaltwinadapter.oc1..aaaa"


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
        lifecycle_state="ACTIVE",
        created_at=timestamp,
        last_updated=timestamp,
        freeform_tags={"env": "dev"},
        defined_tags={"ns": {"key": "value"}},
    )
    summary = SimpleNamespace(
        id="summary-ocid",
        display_name="pump-model-summary",
        description="A twin model summary",
        lifecycle_state="ACTIVE",
        time_created=timestamp,
        time_updated=timestamp,
    )
    relationship = SimpleNamespace(
        id="rel-ocid",
        display_name="parent-child",
        description="Relationship",
        lifecycle_state="ACTIVE",
        time_created=timestamp,
        time_updated=timestamp,
    )
    work_request = SimpleNamespace(
        id="wr-ocid",
        lifecycle_state="IN_PROGRESS",
        compartment_id="compartment-ocid",
        time_created=timestamp,
        time_updated=timestamp,
    )

    assert map_digital_twin_model(model)["defined_tags"] == {"ns": {"key": "value"}}
    assert map_digital_twin_model_summary(summary)["name"] == "pump-model-summary"
    assert map_digital_twin_relationship(relationship)["name"] == "parent-child"
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
        ("list_digital_twin_relationships_records", "list_digital_twin_relationships", {"iot_domain_id": "domain-1"}, "map_digital_twin_relationship"),
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
