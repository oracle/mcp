from datetime import UTC, datetime

import pytest

from oracle.oci_iot_mcp_server import server
from oracle.oci_iot_mcp_server.tool_models import DataApiTokenModel


def test_wait_for_twin_update_returns_first_matching_content_path(monkeypatch):
    monkeypatch.setattr(
        server,
        "wait_for_twin_update_impl",
        lambda **_: {
            "digital_twin_instance_id": "ocid1.digitaltwininstance.oc1..aaaa",
            "content_path": "temperature",
            "value": 72,
            "time_observed": "2026-03-26T12:00:05Z",
        },
    )

    result = server.wait_for_twin_update(
        digital_twin_instance_id="ocid1.digitaltwininstance.oc1..aaaa",
        content_path="temperature",
        since="2026-03-26T12:00:00Z",
        timeout=30,
    )

    assert result["ok"] is True
    assert result["data"]["content_path"] == "temperature"


def test_wait_for_twin_update_requires_since():
    result = server.wait_for_twin_update(
        digital_twin_instance_id="ocid1.digitaltwininstance.oc1..aaaa",
        since="",
        timeout=30,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_input"


def test_list_recent_rejected_data_for_twin_sorts_by_time_received_desc(monkeypatch):
    monkeypatch.setattr(
        server,
        "list_recent_rejected_data_for_twin_impl",
        lambda **_: [
            {"id": "r-older", "time_received": "2026-03-26T11:59:59Z"},
            {"id": "r-newer", "time_received": "2026-03-26T12:00:01Z"},
        ],
    )

    result = server.list_recent_rejected_data_for_twin(
        digital_twin_instance_id="ocid1.digitaltwininstance.oc1..aaaa",
        limit=20,
    )

    assert result["ok"] is True
    assert result["data"][0]["id"] == "r-newer"


def test_list_recent_rejected_data_for_twin_rejects_limit_above_100():
    result = server.list_recent_rejected_data_for_twin(
        digital_twin_instance_id="ocid1.digitaltwininstance.oc1..aaaa",
        limit=101,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_input"


class FrozenDateTime:
    @staticmethod
    def now(tz=None):
        return datetime(2026, 3, 26, 12, 0, 0, tzinfo=UTC)


def test_list_recent_raw_commands_for_twin_passes_through_impl_error(monkeypatch):
    monkeypatch.setattr(
        server,
        "list_recent_raw_commands_for_twin_impl",
        lambda **kwargs: {"ok": False, "error": {"code": "resource_not_found"}},
    )

    result = server.list_recent_raw_commands_for_twin(
        digital_twin_instance_id="ocid1.digitaltwininstance.oc1..aaaa",
        limit=20,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_list_recent_rejected_data_for_twin_passes_through_impl_error(monkeypatch):
    monkeypatch.setattr(
        server,
        "list_recent_rejected_data_for_twin_impl",
        lambda **kwargs: {"ok": False, "error": {"code": "resource_not_found"}},
    )

    result = server.list_recent_rejected_data_for_twin(
        digital_twin_instance_id="ocid1.digitaltwininstance.oc1..aaaa",
        limit=20,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_invoke_raw_command_and_wait_impl_returns_resolved_error(monkeypatch):
    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: {"ok": False, "error": {"code": "resource_not_found"}},
    )

    result = server.invoke_raw_command_and_wait_impl(
        digital_twin_instance_name="pump-01",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_invoke_raw_command_and_wait_impl_returns_invalid_input_for_value_error(monkeypatch):
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-26T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: ({"id": "twin-1"}, {"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "invoke_raw_command", lambda **kwargs: (_ for _ in ()).throw(ValueError("bad payload")))

    result = server.invoke_raw_command_and_wait_impl(
        digital_twin_instance_id="twin-1",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_input"


def test_invoke_raw_command_and_wait_impl_passes_through_invoke_error_payload(monkeypatch):
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-26T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: ({"id": "twin-1"}, {"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(
        server,
        "invoke_raw_command",
        lambda **kwargs: {
            "ok": False,
            "error": {
                "code": "invalid_input",
                "message": "bad payload",
                "details": {},
            },
        },
    )

    result = server.invoke_raw_command_and_wait_impl(
        digital_twin_instance_id="twin-1",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_input"


def test_invoke_raw_command_and_wait_impl_returns_control_plane_error(monkeypatch):
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-26T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: ({"id": "twin-1"}, {"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(
        server,
        "invoke_raw_command",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("control plane failed")),
    )

    result = server.invoke_raw_command_and_wait_impl(
        digital_twin_instance_id="twin-1",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "control_plane_error"


def test_invoke_raw_command_and_wait_impl_returns_data_plane_error_while_correlating(monkeypatch):
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-26T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: ({"id": "twin-1"}, {"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "invoke_raw_command", lambda **kwargs: {"status_code": 202, "opc_request_id": "opc-123"})
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(
        server,
        "list_raw_command_records",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("feed unavailable")),
    )
    ticks = iter([0.0, 1.0]).__next__
    monkeypatch.setattr(server.time, "monotonic", ticks)
    monkeypatch.setattr(server.time, "sleep", lambda seconds: None)

    result = server.invoke_raw_command_and_wait_impl(
        digital_twin_instance_id="twin-1",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
        timeout=5,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "data_plane_error"


def test_invoke_raw_command_and_wait_impl_returns_ambiguity_near_deadline(monkeypatch):
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-26T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: ({"id": "twin-1"}, {"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "invoke_raw_command", lambda **kwargs: {"status_code": 202, "opc_request_id": "opc-123"})
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(
        server,
        "list_raw_command_records",
        lambda **kwargs: [
            {
                "id": "rc-1",
                "digital_twin_instance_id": "twin-1",
                "request_endpoint": "/v1/cmd",
                "request_data_format": "TEXT",
                "time_created": "2026-03-26T12:00:00Z",
            },
            {
                "id": "rc-2",
                "digital_twin_instance_id": "twin-1",
                "request_endpoint": "/v1/cmd",
                "request_data_format": "TEXT",
                "time_created": "2026-03-26T12:00:01Z",
            },
        ],
    )
    monkeypatch.setattr(server, "_candidate_matches_invoke", lambda **kwargs: True)
    ticks = iter([0.0, 1.0, 4.0]).__next__
    monkeypatch.setattr(server.time, "monotonic", ticks)
    monkeypatch.setattr(server.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(server, "datetime", FrozenDateTime)

    result = server.invoke_raw_command_and_wait_impl(
        digital_twin_instance_id="twin-1",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
        timeout=5,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "ambiguous_identifier"


def test_invoke_raw_command_and_wait_impl_returns_ambiguity_after_loop(monkeypatch):
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-26T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: ({"id": "twin-1"}, {"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "invoke_raw_command", lambda **kwargs: {"status_code": 202, "opc_request_id": "opc-123"})
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(
        server,
        "list_raw_command_records",
        lambda **kwargs: [
            {
                "id": "rc-1",
                "digital_twin_instance_id": "twin-1",
                "request_endpoint": "/v1/cmd",
                "request_data_format": "TEXT",
                "time_created": "2026-03-26T12:00:00Z",
            },
            {
                "id": "rc-2",
                "digital_twin_instance_id": "twin-1",
                "request_endpoint": "/v1/cmd",
                "request_data_format": "TEXT",
                "time_created": "2026-03-26T12:00:01Z",
            },
        ],
    )
    monkeypatch.setattr(server, "_candidate_matches_invoke", lambda **kwargs: True)
    ticks = iter([0.0, 1.0, 1.0, 6.0]).__next__
    monkeypatch.setattr(server.time, "monotonic", ticks)
    monkeypatch.setattr(server.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(server, "datetime", FrozenDateTime)

    result = server.invoke_raw_command_and_wait_impl(
        digital_twin_instance_id="twin-1",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
        timeout=5,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "ambiguous_identifier"


def test_invoke_raw_command_and_wait_impl_returns_timeout_without_candidates(monkeypatch):
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-26T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: ({"id": "twin-1"}, {"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "invoke_raw_command", lambda **kwargs: {"status_code": 202, "opc_request_id": "opc-123"})
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(server, "list_raw_command_records", lambda **kwargs: [])
    monkeypatch.setattr(server, "_candidate_matches_invoke", lambda **kwargs: False)
    ticks = iter([0.0, 1.0, 6.0]).__next__
    monkeypatch.setattr(server.time, "monotonic", ticks)
    monkeypatch.setattr(server.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(server, "datetime", FrozenDateTime)

    result = server.invoke_raw_command_and_wait_impl(
        digital_twin_instance_id="twin-1",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
        timeout=5,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "timeout"


def test_invoke_raw_command_and_wait_impl_returns_terminal_record(monkeypatch):
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-26T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: ({"id": "twin-1"}, {"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "invoke_raw_command", lambda **kwargs: {"status_code": 202, "opc_request_id": "opc-123"})
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(
        server,
        "list_raw_command_records",
        lambda **kwargs: [
            {
                "id": "rc-1",
                "digital_twin_instance_id": "twin-1",
                "request_endpoint": "/v1/cmd",
                "request_data_format": "TEXT",
                "time_created": "2026-03-26T12:00:00Z",
            }
        ],
    )
    monkeypatch.setattr(server, "_candidate_matches_invoke", lambda **kwargs: True)
    monkeypatch.setattr(
        server,
        "wait_for_raw_command_terminal_state",
        lambda **kwargs: {
            "timed_out": False,
            "raw_command": {"id": kwargs["record_id"], "delivery_status": "COMPLETED"},
        },
    )
    ticks = iter([0.0, 1.0, 5.0]).__next__
    monkeypatch.setattr(server.time, "monotonic", ticks)
    monkeypatch.setattr(server.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(server, "datetime", FrozenDateTime)

    result = server.invoke_raw_command_and_wait_impl(
        digital_twin_instance_id="twin-1",
        request_endpoint="/v1/cmd",
        request_data_format="TEXT",
        request_data="PING",
        timeout=30,
    )

    assert result == {
        "status_code": 202,
        "opc_request_id": "opc-123",
        "request_id": "rc-1",
        "timed_out": False,
        "raw_command": {"id": "rc-1", "delivery_status": "COMPLETED"},
    }


def test_wait_for_twin_update_impl_handles_error_and_success_paths(monkeypatch):
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-26T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: {"ok": False, "error": {"code": "resource_not_found"}},
    )
    assert server.wait_for_twin_update_impl(digital_twin_instance_name="pump-01", since="2026-03-26T12:00:00Z")[
        "error"
    ]["code"] == "resource_not_found"

    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: ({"id": "twin-1"}, {"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(
        server,
        "list_snapshot_records",
        lambda **kwargs: [
            {"content_path": "humidity", "time_observed": "2026-03-26T12:00:00Z"},
            {"content_path": "temperature", "time_observed": "2026-03-26T12:00:01Z", "value": 72},
        ],
    )
    monkeypatch.setattr(
        server,
        "wait_for_snapshot_update",
        lambda **kwargs: kwargs["fetch_rows"]()[0],
    )
    assert server.wait_for_twin_update_impl(
        digital_twin_instance_id="twin-1",
        content_path="temperature",
        since="2026-03-26T12:00:00Z",
    ) == {"content_path": "temperature", "time_observed": "2026-03-26T12:00:01Z", "value": 72}

    monkeypatch.setattr(
        server,
        "wait_for_snapshot_update",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("bad timestamp")),
    )
    assert server.wait_for_twin_update_impl(
        digital_twin_instance_id="twin-1",
        since="bad",
    )["error"]["code"] == "invalid_input"

    monkeypatch.setattr(
        server,
        "wait_for_snapshot_update",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("feed unavailable")),
    )
    assert server.wait_for_twin_update_impl(
        digital_twin_instance_id="twin-1",
        since="2026-03-26T12:00:00Z",
    )["error"]["code"] == "data_plane_error"


def test_list_recent_rejected_data_for_twin_impl_handles_error_and_success_paths(monkeypatch):
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-26T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        server,
        "_resolve_twin_with_data_plane_access",
        lambda **kwargs: ({"id": "twin-1"}, {"data_host": "data.example.com", "domain_short_id": "abc123"}, token),
    )
    monkeypatch.setattr(server, "build_ords_base_url", lambda context: "https://example.com/base")
    monkeypatch.setattr(
        server,
        "list_rejected_data_records",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("feed unavailable")),
    )
    assert server.list_recent_rejected_data_for_twin_impl(digital_twin_instance_id="twin-1")["error"]["code"] == (
        "data_plane_error"
    )

    monkeypatch.setattr(
        server,
        "list_rejected_data_records",
        lambda **kwargs: [{"id": "rej-1", "digital_twin_instance_id": "twin-1", "time_received": "bad"}],
    )
    assert server.list_recent_rejected_data_for_twin_impl(
        digital_twin_instance_id="twin-1",
        since="2026-03-26T12:00:00Z",
    )["error"]["code"] == "invalid_input"

    monkeypatch.setattr(
        server,
        "list_rejected_data_records",
        lambda **kwargs: [
            {"id": "rej-1", "digital_twin_instance_id": "twin-1", "time_received": "2026-03-26T12:00:00Z"},
            {"id": "rej-2", "digital_twin_instance_id": "twin-2", "time_received": "2026-03-26T12:00:00Z"},
            {"id": "rej-3", "digital_twin_instance_id": "twin-1", "time_received": "2026-03-26T11:00:00Z"},
        ],
    )
    assert server.list_recent_rejected_data_for_twin_impl(
        digital_twin_instance_id="twin-1",
        since="2026-03-26T11:59:00Z",
    ) == [{"id": "rej-1", "digital_twin_instance_id": "twin-1", "time_received": "2026-03-26T12:00:00Z"}]


def test_server_health_check_and_main_cover_success_and_error_paths(monkeypatch):
    assert server.health_check()["service"] == "oci-iot-mcp-server"

    runs = []
    monkeypatch.setattr(server.mcp, "run", lambda: runs.append("ran"))
    server.main()
    assert runs == ["ran"]

    logged = []
    monkeypatch.setattr(server.mcp, "run", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(server.logger, "error", lambda message: logged.append(message))

    with pytest.raises(RuntimeError, match="boom"):
        server.main()

    assert logged == ["Error running MCP server: boom"]
