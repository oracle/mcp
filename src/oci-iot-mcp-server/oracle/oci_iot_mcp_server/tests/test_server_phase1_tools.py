from datetime import UTC, datetime, timedelta

import pytest

from oci.iot.models import (
    DigitalTwinAdapterInboundEnvelope,
    DigitalTwinAdapterInboundRoute,
    DigitalTwinAdapterJsonPayload,
)

from oracle.oci_iot_mcp_server import server
from oracle.oci_iot_mcp_server.data_plane import DataApiTokenError
from oracle.oci_iot_mcp_server.errors import error_result
from oracle.oci_iot_mcp_server.tool_models import DataApiTokenModel


def _fake_phase1_adapter_envelope():
    return DigitalTwinAdapterInboundEnvelope(
        reference_endpoint="/telemetry",
        reference_payload=DigitalTwinAdapterJsonPayload(data_format="JSON"),
        envelope_mapping={"type": "messageType"},
    )


def _fake_phase1_adapter_route():
    return DigitalTwinAdapterInboundRoute(
        condition="true",
        payload_mapping={"temperature": "temp"},
    )


def _fake_phase1_adapter_payload():
    return {
        "id": "ocid1.digitaltwinadapter.oc1..eeee",
        "digital_twin_model_id": "ocid1.digitaltwinmodel.oc1..bbbb",
        "inbound_envelope": _fake_phase1_adapter_envelope(),
        "inbound_routes": [_fake_phase1_adapter_route()],
    }


def test_get_digital_twin_adapter_full_wraps_full_adapter_record(monkeypatch):
    monkeypatch.setattr(
        server,
        "get_digital_twin_adapter_record",
        lambda digital_twin_adapter_id: {
            "id": digital_twin_adapter_id,
            "digital_twin_model_id": "ocid1.digitaltwinmodel.oc1..aaaa",
            "digital_twin_model_spec_uri": "https://example.com/spec.json",
            "inbound_routes": [{"messageType": "telemetry"}],
        },
    )

    result = server.get_digital_twin_adapter_full("ocid1.digitaltwinadapter.oc1..aaaa")

    assert result["ok"] is True
    assert result["data"]["digital_twin_model_id"] == "ocid1.digitaltwinmodel.oc1..aaaa"


def test_get_digital_twin_adapter_full_serializes_nested_adapter(monkeypatch):
    monkeypatch.setattr(
        server,
        "get_digital_twin_adapter_record",
        lambda *_: _fake_phase1_adapter_payload(),
    )

    result = server.get_digital_twin_adapter_full("ocid1.digitaltwinadapter.oc1..eeee")

    assert result["ok"] is True
    assert result["data"]["id"] == "ocid1.digitaltwinadapter.oc1..eeee"
    assert isinstance(result["data"]["inbound_envelope"], dict)
    server.JSON_ADAPTER.dump_python(result, mode="json")


def test_derive_domain_context_returns_success_envelope(monkeypatch):
    monkeypatch.setattr(
        server,
        "resolve_domain_context_for_tool",
        lambda **_: {
            "iot_domain_id": "domain-ocid",
            "domain_short_id": "abc123",
            "region": "us-phoenix-1",
        },
    )

    result = server.derive_domain_context(iot_domain_id="domain-ocid")

    assert result == {
        "ok": True,
        "data": {
            "iot_domain_id": "domain-ocid",
            "domain_short_id": "abc123",
            "region": "us-phoenix-1",
        },
    }


def test_get_data_api_token_passes_through_structured_configuration_error(monkeypatch):
    monkeypatch.setattr(
        server,
        "get_data_api_token_impl",
        lambda **_: {
            "ok": False,
            "error": {
                "code": "missing_token_credentials",
                "message": "Missing one or more OCI IoT ORDS credential environment variables.",
            },
        },
    )

    result = server.get_data_api_token(iot_domain_id="domain-ocid")

    assert result["ok"] is False
    assert result["error"]["code"] == "missing_token_credentials"


def test_get_data_api_token_wraps_success_payload(monkeypatch):
    monkeypatch.setattr(
        server,
        "get_data_api_token_impl",
        lambda **_: {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_at": "2026-03-26T13:00:00Z",
            "expires_in": 3600,
            "iot_domain_id": "domain-ocid",
        },
    )

    result = server.get_data_api_token(iot_domain_id="domain-ocid")

    assert result["ok"] is True
    assert result["data"]["access_token"] == "token-123"
    assert result["data"]["expires_at"] == "2026-03-26T13:00:00Z"


def test_get_data_api_token_serializes_nested_pydantic_payload(monkeypatch):
    monkeypatch.setattr(
        server,
        "get_data_api_token_impl",
        lambda **_: {
            "token": DataApiTokenModel(
                access_token="token-123",
                token_type="Bearer",
                expires_in=3600,
                expires_at=datetime(2026, 3, 26, 13, 0, 0, tzinfo=UTC),
            ),
            "iot_domain_id": "domain-ocid",
        },
    )

    result = server.get_data_api_token(iot_domain_id="domain-ocid")

    assert result["ok"] is True
    assert result["data"]["token"]["expires_at"] == "2026-03-26T13:00:00Z"


def test_get_raw_command_by_request_id_wraps_detail_record(monkeypatch):
    monkeypatch.setattr(
        server,
        "get_raw_command_by_request_id_impl",
        lambda **_: {
            "id": "rc-1",
            "digital_twin_instance_id": "ocid1.digitaltwininstance.oc1..aaaa",
            "delivery_status": "COMPLETED",
        },
    )

    result = server.get_raw_command_by_request_id(
        request_id="rc-1",
        digital_twin_instance_id="ocid1.digitaltwininstance.oc1..aaaa",
    )

    assert result["ok"] is True
    assert result["data"]["id"] == "rc-1"


def test_list_recent_raw_commands_for_twin_sorts_by_time_created_desc(monkeypatch):
    monkeypatch.setattr(
        server,
        "list_recent_raw_commands_for_twin_impl",
        lambda **_: [
            {"id": "rc-older", "time_created": "2026-03-26T11:59:59Z"},
            {"id": "rc-newer", "time_created": "2026-03-26T12:00:01Z"},
        ],
    )

    result = server.list_recent_raw_commands_for_twin(
        digital_twin_instance_id="ocid1.digitaltwininstance.oc1..aaaa",
        limit=20,
    )

    assert result["ok"] is True
    assert result["data"][0]["id"] == "rc-newer"


def test_list_recent_raw_commands_for_twin_rejects_limit_above_100():
    result = server.list_recent_raw_commands_for_twin(
        digital_twin_instance_id="ocid1.digitaltwininstance.oc1..aaaa",
        limit=101,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_input"


def test_invoke_raw_command_and_wait_wraps_terminal_record(monkeypatch):
    monkeypatch.setattr(
        server,
        "invoke_raw_command_and_wait_impl",
        lambda **_: {
            "request_id": "rc-1",
            "timed_out": False,
            "raw_command": {"id": "rc-1", "delivery_status": "COMPLETED"},
        },
    )

    result = server.invoke_raw_command_and_wait(
        digital_twin_instance_id="ocid1.digitaltwininstance.oc1..aaaa",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
        timeout=30,
    )

    assert result["ok"] is True
    assert result["data"]["request_id"] == "rc-1"
    assert result["data"]["raw_command"]["delivery_status"] == "COMPLETED"


def test_invoke_raw_command_and_wait_passes_through_recoverable_error(monkeypatch):
    monkeypatch.setattr(
        server,
        "invoke_raw_command_and_wait_impl",
        lambda **_: {
            "ok": False,
            "error": {
                "code": "ambiguous_identifier",
                "message": "Multiple raw command records matched the invoke request.",
            },
        },
    )

    result = server.invoke_raw_command_and_wait(
        digital_twin_instance_id="ocid1.digitaltwininstance.oc1..aaaa",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
        timeout=30,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "ambiguous_identifier"


def test_delegate_logs_and_reraises_exceptions(monkeypatch):
    logged = []

    def boom():
        raise RuntimeError("broken")

    monkeypatch.setattr(server.logger, "error", lambda message: logged.append(message))

    with pytest.raises(RuntimeError, match="broken"):
        server._delegate("while delegating", boom)

    assert logged == ["while delegating: broken"]


def test_delegate_returns_success_result():
    assert server._delegate("unused", lambda value: value + 1, 1) == 2


def test_as_tool_result_handles_error_payload_success_payload_and_plain_data():
    wrapped_success = server._as_tool_result(
        {"ok": True, "data": {"expires_at": datetime(2026, 3, 26, 13, 0, 0, tzinfo=UTC)}}
    )
    wrapped_plain = server._as_tool_result({"id": "abc"})

    assert server._as_tool_result({"ok": False, "error": {"code": "bad"}}) == {
        "ok": False,
        "error": {"code": "bad"},
    }
    assert wrapped_success == {
        "ok": True,
        "data": {"expires_at": "2026-03-26T13:00:00Z"},
    }
    assert wrapped_plain == {"ok": True, "data": {"id": "abc"}}


def test_limit_parse_window_and_sort_helpers_cover_edge_cases():
    lower = "2026-03-26T12:00:00Z"
    upper = "2026-03-26T12:05:00Z"

    assert server._limit_error(field_name="limit", value=20) is None
    assert server._limit_error(field_name="limit", value=0)["error"]["code"] == "invalid_input"
    assert server._parse_rfc3339(None) is None
    assert server._in_time_window(None, None, None) is True
    assert server._in_time_window(None, lower, None) is False
    assert server._in_time_window("2026-03-26T12:01:00Z", lower, upper) is True
    assert server._in_time_window("2026-03-26T11:59:59Z", lower, upper) is False
    assert server._in_time_window("2026-03-26T12:05:01Z", lower, upper) is False
    assert [row["id"] for row in server._sort_desc(
        [
            {"id": "old", "time_created": "2026-03-26T12:00:00Z"},
            {"id": "missing"},
            {"id": "new", "time_created": "2026-03-26T12:01:00Z"},
        ],
        "time_created",
    )] == ["new", "old", "missing"]


def test_resolve_data_plane_access_passes_through_domain_error(monkeypatch):
    monkeypatch.setattr(
        server,
        "resolve_domain_context_for_tool",
        lambda **kwargs: {"ok": False, "error": {"code": "resource_not_found"}},
    )

    result = server._resolve_data_plane_access(iot_domain_id="domain-ocid")

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_resolve_data_plane_access_passes_through_missing_credentials(monkeypatch):
    monkeypatch.setattr(server, "resolve_domain_context_for_tool", lambda **kwargs: {"iot_domain_id": "domain-ocid"})
    monkeypatch.setattr(
        server,
        "require_token_credentials",
        lambda env: {"ok": False, "error": {"code": "missing_token_credentials"}},
    )

    result = server._resolve_data_plane_access(iot_domain_id="domain-ocid")

    assert result["ok"] is False
    assert result["error"]["code"] == "missing_token_credentials"


def test_resolve_data_plane_access_returns_error_when_token_minting_fails(monkeypatch):
    monkeypatch.setattr(server, "resolve_domain_context_for_tool", lambda **kwargs: {"iot_domain_id": "domain-ocid"})
    monkeypatch.setattr(server, "require_token_credentials", lambda env: {"ok": True, "data": {}})
    monkeypatch.setattr(server, "get_cached_data_api_token", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("bad token")))

    result = server._resolve_data_plane_access(iot_domain_id="domain-ocid")

    assert result["ok"] is False
    assert result["error"]["code"] == "data_plane_error"


def test_resolve_data_plane_access_returns_structured_token_mint_error(monkeypatch):
    monkeypatch.setattr(server, "resolve_domain_context_for_tool", lambda **kwargs: {"iot_domain_id": "domain-ocid"})
    monkeypatch.setattr(server, "require_token_credentials", lambda env: {"ok": True, "data": {}})
    monkeypatch.setattr(
        server,
        "get_cached_data_api_token",
        lambda **kwargs: (_ for _ in ()).throw(
            DataApiTokenError(
                code="missing_ords_configuration",
                message="IoT domain is not configured for ORDS token minting.",
                retry_hint="Configure ORDS data access for the IoT domain and retry.",
                details={"missing": ["db_allowed_identity_domain_host"]},
            )
        ),
    )

    result = server._resolve_data_plane_access(iot_domain_id="domain-ocid")

    assert result["ok"] is False
    assert result["error"]["code"] == "missing_ords_configuration"
    assert result["error"]["details"]["missing"] == ["db_allowed_identity_domain_host"]


def test_resolve_data_plane_access_returns_domain_context_and_token(monkeypatch):
    token = DataApiTokenModel(
        access_token="token-123",
        token_type="Bearer",
        expires_in=3600,
        expires_at=datetime(2026, 3, 26, 13, 0, 0, tzinfo=UTC),
    )
    monkeypatch.setattr(
        server,
        "resolve_domain_context_for_tool",
        lambda **kwargs: {"iot_domain_id": "domain-ocid", "domain_short_id": "abc123"},
    )
    monkeypatch.setattr(server, "require_token_credentials", lambda env: {"ok": True, "data": {}})
    monkeypatch.setattr(server, "get_cached_data_api_token", lambda **kwargs: token)

    result = server._resolve_data_plane_access(iot_domain_id="domain-ocid")

    assert result == (
        {"iot_domain_id": "domain-ocid", "domain_short_id": "abc123"},
        token,
    )


def test_resolve_twin_with_data_plane_access_covers_error_and_success_paths(monkeypatch):
    token = DataApiTokenModel(
        access_token="token-123",
        token_type="Bearer",
        expires_in=3600,
        expires_at=datetime(2026, 3, 26, 13, 0, 0, tzinfo=UTC),
    )

    monkeypatch.setattr(
        server,
        "resolve_twin_for_tool",
        lambda **kwargs: {"ok": False, "error": {"code": "resource_not_found"}},
    )
    assert server._resolve_twin_with_data_plane_access(digital_twin_instance_name="pump-01")["error"]["code"] == (
        "resource_not_found"
    )

    monkeypatch.setattr(
        server,
        "resolve_twin_for_tool",
        lambda **kwargs: {"id": "twin-1", "iot_domain_id": "domain-ocid"},
    )
    monkeypatch.setattr(
        server,
        "_resolve_data_plane_access",
        lambda **kwargs: {"ok": False, "error": {"code": "missing_token_credentials"}},
    )
    assert server._resolve_twin_with_data_plane_access(digital_twin_instance_name="pump-01")["error"]["code"] == (
        "missing_token_credentials"
    )

    monkeypatch.setattr(
        server,
        "_resolve_data_plane_access",
        lambda **kwargs: ({"iot_domain_id": "domain-ocid"}, token),
    )
    assert server._resolve_twin_with_data_plane_access(digital_twin_instance_name="pump-01") == (
        {"id": "twin-1", "iot_domain_id": "domain-ocid"},
        {"iot_domain_id": "domain-ocid"},
        token,
    )


def test_get_data_api_token_impl_passes_through_error(monkeypatch):
    monkeypatch.setattr(
        server,
        "_resolve_data_plane_access",
        lambda **kwargs: {"ok": False, "error": {"code": "resource_not_found"}},
    )

    result = server.get_data_api_token_impl(iot_domain_id="domain-ocid")

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_get_data_api_token_impl_merges_context_and_token(monkeypatch):
    token = DataApiTokenModel(
        access_token="token-123",
        token_type="Bearer",
        expires_in=3600,
        expires_at=datetime(2026, 3, 26, 13, 0, 0, tzinfo=UTC),
    )
    monkeypatch.setattr(
        server,
        "_resolve_data_plane_access",
        lambda **kwargs: ({"iot_domain_id": "domain-ocid", "region": "us-phoenix-1"}, token),
    )

    result = server.get_data_api_token_impl(iot_domain_id="domain-ocid")

    assert result["iot_domain_id"] == "domain-ocid"
    assert result["access_token"] == "token-123"


def test_get_raw_command_by_request_id_impl_returns_access_error(monkeypatch):
    monkeypatch.setattr(
        server,
        "_resolve_data_plane_access",
        lambda **kwargs: {"ok": False, "error": {"code": "resource_not_found"}},
    )

    result = server.get_raw_command_by_request_id_impl(request_id="rc-1", iot_domain_id="domain-ocid")

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_get_raw_command_by_request_id_impl_returns_data_plane_error(monkeypatch):
    token = DataApiTokenModel(
        access_token="token-123",
        token_type="Bearer",
        expires_in=3600,
        expires_at=datetime(2026, 3, 26, 13, 0, 0, tzinfo=UTC),
    )
    monkeypatch.setattr(
        server,
        "_resolve_data_plane_access",
        lambda **kwargs: ({"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(
        server,
        "get_raw_command_record",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("lookup failed")),
    )

    result = server.get_raw_command_by_request_id_impl(request_id="rc-1", iot_domain_id="domain-ocid")

    assert result["ok"] is False
    assert result["error"]["code"] == "data_plane_error"


def test_get_raw_command_by_request_id_impl_returns_not_found_for_twin_mismatch(monkeypatch):
    token = DataApiTokenModel(
        access_token="token-123",
        token_type="Bearer",
        expires_in=3600,
        expires_at=datetime(2026, 3, 26, 13, 0, 0, tzinfo=UTC),
    )
    monkeypatch.setattr(
        server,
        "_resolve_data_plane_access",
        lambda **kwargs: ({"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(
        server,
        "get_raw_command_record",
        lambda **kwargs: {
            "id": "rc-1",
            "digital_twin_instance_id": "twin-2",
            "time_created": "2026-03-26T12:00:00Z",
        },
    )
    monkeypatch.setattr(
        server,
        "resolve_twin_for_tool",
        lambda **kwargs: {"id": "twin-1", "iot_domain_id": "domain-ocid"},
    )

    result = server.get_raw_command_by_request_id_impl(
        request_id="rc-1",
        digital_twin_instance_name="pump-01",
        iot_domain_id="domain-ocid",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_get_raw_command_by_request_id_impl_rejects_invalid_time_window(monkeypatch):
    token = DataApiTokenModel(
        access_token="token-123",
        token_type="Bearer",
        expires_in=3600,
        expires_at=datetime(2026, 3, 26, 13, 0, 0, tzinfo=UTC),
    )
    monkeypatch.setattr(
        server,
        "_resolve_data_plane_access",
        lambda **kwargs: ({"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(
        server,
        "get_raw_command_record",
        lambda **kwargs: {
            "id": "rc-1",
            "digital_twin_instance_id": "twin-1",
            "time_created": "2026-03-26T12:00:00Z",
        },
    )

    result = server.get_raw_command_by_request_id_impl(
        request_id="rc-1",
        since="not-a-timestamp",
        iot_domain_id="domain-ocid",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_input"


def test_get_raw_command_by_request_id_impl_returns_not_found_outside_time_window(monkeypatch):
    token = DataApiTokenModel(
        access_token="token-123",
        token_type="Bearer",
        expires_in=3600,
        expires_at=datetime(2026, 3, 26, 13, 0, 0, tzinfo=UTC),
    )
    monkeypatch.setattr(
        server,
        "_resolve_data_plane_access",
        lambda **kwargs: ({"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(
        server,
        "get_raw_command_record",
        lambda **kwargs: {
            "id": "rc-1",
            "digital_twin_instance_id": "twin-1",
            "time_created": "2026-03-26T12:00:00Z",
        },
    )

    result = server.get_raw_command_by_request_id_impl(
        request_id="rc-1",
        since="2026-03-26T12:00:01Z",
        iot_domain_id="domain-ocid",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_get_raw_command_by_request_id_impl_returns_record_when_inputs_match(monkeypatch):
    token = DataApiTokenModel(
        access_token="token-123",
        token_type="Bearer",
        expires_in=3600,
        expires_at=datetime(2026, 3, 26, 13, 0, 0, tzinfo=UTC),
    )
    record = {
        "id": "rc-1",
        "digital_twin_instance_id": "twin-1",
        "time_created": "2026-03-26T12:00:00Z",
    }
    monkeypatch.setattr(
        server,
        "_resolve_data_plane_access",
        lambda **kwargs: ({"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(server, "get_raw_command_record", lambda **kwargs: record)
    monkeypatch.setattr(
        server,
        "resolve_twin_for_tool",
        lambda **kwargs: {"id": "twin-1", "iot_domain_id": "domain-ocid"},
    )

    result = server.get_raw_command_by_request_id_impl(
        request_id="rc-1",
        digital_twin_instance_name="pump-01",
        iot_domain_id="domain-ocid",
        since="2026-03-26T11:59:00Z",
        until="2026-03-26T12:01:00Z",
    )

    assert result == record


def test_list_recent_raw_commands_for_twin_impl_handles_errors_and_filters_rows(monkeypatch):
    token = DataApiTokenModel(
        access_token="token-123",
        token_type="Bearer",
        expires_in=3600,
        expires_at=datetime(2026, 3, 26, 13, 0, 0, tzinfo=UTC),
    )
    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: {"ok": False, "error": {"code": "resource_not_found"}},
    )
    assert server.list_recent_raw_commands_for_twin_impl(digital_twin_instance_name="pump-01")["error"]["code"] == (
        "resource_not_found"
    )

    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: ({"id": "twin-1"}, {"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(
        server,
        "list_raw_command_records",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("lookup failed")),
    )
    assert server.list_recent_raw_commands_for_twin_impl(digital_twin_instance_id="twin-1")["error"]["code"] == (
        "data_plane_error"
    )

    monkeypatch.setattr(
        server,
        "list_raw_command_records",
        lambda **kwargs: [
            {"id": "rc-1", "digital_twin_instance_id": "twin-1", "time_created": "bad"},
        ],
    )
    assert server.list_recent_raw_commands_for_twin_impl(
        digital_twin_instance_id="twin-1",
        since="2026-03-26T12:00:00Z",
    )["error"]["code"] == "invalid_input"

    monkeypatch.setattr(
        server,
        "list_raw_command_records",
        lambda **kwargs: [
            {"id": "rc-1", "digital_twin_instance_id": "twin-1", "time_created": "2026-03-26T12:00:00Z"},
            {"id": "rc-2", "digital_twin_instance_id": "twin-2", "time_created": "2026-03-26T12:00:00Z"},
            {"id": "rc-3", "digital_twin_instance_id": "twin-1", "time_created": "2026-03-26T11:00:00Z"},
        ],
    )
    assert server.list_recent_raw_commands_for_twin_impl(
        digital_twin_instance_id="twin-1",
        since="2026-03-26T11:59:00Z",
    ) == [{"id": "rc-1", "digital_twin_instance_id": "twin-1", "time_created": "2026-03-26T12:00:00Z"}]


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"digital_twin_instance_id": "other"}, False),
        ({"request_endpoint": "/wrong"}, False),
        ({"request_data_format": "JSON"}, False),
        ({"response_endpoint": "/wrong"}, False),
        ({"request_duration": "PT2S"}, False),
        ({"response_duration": "PT2S"}, False),
        ({"time_created": "2026-03-26T11:59:54Z"}, False),
        ({}, True),
    ],
)
def test_candidate_matches_invoke_covers_match_conditions(overrides, expected):
    base_row = {
        "id": "rc-1",
        "digital_twin_instance_id": "twin-1",
        "request_endpoint": "/v1/cmd",
        "request_data_format": "TEXT",
        "response_endpoint": "/v1/reply",
        "request_duration": "PT1S",
        "response_duration": "PT1S",
        "time_created": "2026-03-26T12:00:00Z",
    }
    row = {**base_row, **overrides}

    assert server._candidate_matches_invoke(
        row=row,
        twin_id="twin-1",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        response_endpoint="/v1/reply",
        request_duration="PT1S",
        response_duration="PT1S",
        invoke_started_at=datetime(2026, 3, 26, 12, 0, 0, tzinfo=UTC),
    ) is expected


@pytest.mark.parametrize(
    ("tool_name", "delegate_name", "args", "kwargs", "expected"),
    [
        ("get_digital_twin_adapter", "get_digital_twin_adapter_record", ("adapter-1",), {}, {"id": "adapter-1"}),
        ("get_digital_twin_instance", "get_digital_twin_instance_record", ("twin-1",), {}, {"id": "twin-1"}),
        ("get_digital_twin_instance_content", "get_digital_twin_instance_content_record", ("twin-1",), {}, {"content": "ok"}),
        ("get_digital_twin_model", "get_digital_twin_model_record", ("model-1",), {}, {"id": "model-1"}),
        ("get_digital_twin_model_spec", "get_digital_twin_model_spec_record", ("model-1",), {}, {"spec": "ok"}),
        ("get_digital_twin_relationship", "get_digital_twin_relationship_record", ("rel-1",), {}, {"id": "rel-1"}),
        ("get_iot_domain_group", "get_iot_domain_group_record", ("group-1",), {}, {"id": "group-1"}),
        ("get_work_request", "get_work_request_record", ("wr-1",), {}, {"id": "wr-1"}),
        ("list_digital_twin_adapters", "list_digital_twin_adapters_records", (), {"iot_domain_id": "domain-1"}, [{"id": "adapter-1"}]),
        ("list_digital_twin_models", "list_digital_twin_models_records", (), {"iot_domain_id": "domain-1"}, [{"id": "model-1"}]),
        ("list_digital_twin_instances", "list_digital_twin_instances_records", (), {"iot_domain_id": "domain-1", "limit": 2}, [{"id": "twin-1"}]),
        ("list_digital_twin_relationships", "list_digital_twin_relationships_records", (), {"iot_domain_id": "domain-1"}, [{"id": "rel-1"}]),
        ("list_iot_domain_groups", "list_iot_domain_groups_records", (), {"compartment_id": "compartment-1"}, [{"id": "group-1"}]),
        ("list_iot_domains", "list_iot_domains_records", (), {"compartment_id": "compartment-1"}, [{"id": "domain-1"}]),
        ("list_work_request_errors", "list_work_request_errors_records", (), {"work_request_id": "wr-1"}, [{"message": "boom"}]),
        ("list_work_request_logs", "list_work_request_logs_records", (), {"work_request_id": "wr-1"}, [{"message": "log"}]),
        ("list_work_requests", "list_work_requests_records", (), {"compartment_id": "compartment-1"}, [{"id": "wr-1"}]),
    ],
)
def test_legacy_control_plane_tools_delegate_to_record_helpers(
    monkeypatch,
    tool_name,
    delegate_name,
    args,
    kwargs,
    expected,
):
    monkeypatch.setattr(server, delegate_name, lambda *call_args, **call_kwargs: expected)

    result = getattr(server, tool_name)(*args, **kwargs)

    if tool_name.startswith("list_"):
        assert result == {"result": expected}
    else:
        assert result == expected
