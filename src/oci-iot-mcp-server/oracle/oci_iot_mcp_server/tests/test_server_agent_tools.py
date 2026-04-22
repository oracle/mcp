import pytest

from oci.iot.models import (
    DigitalTwinAdapterInboundEnvelope,
    DigitalTwinAdapterInboundRoute,
    DigitalTwinAdapterJsonPayload,
)

from oracle.oci_iot_mcp_server import server


def _fake_agent_envelope():
    return DigitalTwinAdapterInboundEnvelope(
        reference_endpoint="/telemetry",
        reference_payload=DigitalTwinAdapterJsonPayload(data_format="JSON"),
        envelope_mapping={"type": "messageType"},
    )


def _fake_agent_route():
    return DigitalTwinAdapterInboundRoute(
        condition="true",
        payload_mapping={"temperature": "temp"},
    )


def _fake_agent_adapter():
    return {
        "id": "ocid1.digitaltwinadapter.oc1..aaaa",
        "inbound_envelope": _fake_agent_envelope(),
        "inbound_routes": [_fake_agent_route()],
    }


def test_server_get_twin_platform_context_returns_success_envelope(monkeypatch):
    if not hasattr(server, "get_twin_platform_context"):
        pytest.fail("server should expose get_twin_platform_context")

    monkeypatch.setattr(
        server,
        "get_twin_platform_context_impl",
        lambda **_: {
            "twin": {"id": "twin-1"},
            "domain_context": {"region": "us-ashburn-1"},
        },
        raising=False,
    )

    payload = server.get_twin_platform_context(digital_twin_instance_id="twin-1")

    assert payload["ok"] is True
    assert payload["data"]["twin"]["id"] == "twin-1"


def test_server_get_twin_platform_context_serializes_nested_adapter(monkeypatch):
    monkeypatch.setattr(
        server,
        "get_twin_platform_context_impl",
        lambda **_: {
            "twin": {"id": "twin-1"},
            "adapter": _fake_agent_adapter(),
        },
        raising=False,
    )

    payload = server.get_twin_platform_context(digital_twin_instance_id="twin-1")

    assert payload["ok"] is True
    assert payload["data"]["adapter"]["id"] == "ocid1.digitaltwinadapter.oc1..aaaa"


def test_server_get_latest_twin_state_returns_success_envelope(monkeypatch):
    if not hasattr(server, "get_latest_twin_state"):
        pytest.fail("server should expose get_latest_twin_state")

    monkeypatch.setattr(
        server,
        "get_latest_twin_state_impl",
        lambda **_: {
            "twin": {"id": "twin-1"},
            "observed_timestamps": {"snapshot": "2026-03-27T10:00:00Z"},
        },
        raising=False,
    )

    payload = server.get_latest_twin_state(digital_twin_instance_id="twin-1")

    assert payload["ok"] is True
    assert payload["data"]["observed_timestamps"]["snapshot"] == "2026-03-27T10:00:00Z"


def test_server_validate_twin_readiness_returns_success(monkeypatch):
    if not hasattr(server, "validate_twin_readiness"):
        pytest.fail("server should expose validate_twin_readiness")

    monkeypatch.setattr(
        server,
        "validate_twin_readiness_impl",
        lambda **_: {
            "overall_status": "ok",
            "twin": {"id": "twin-1"},
            "checks": [{"name": "snapshot_read", "status": "ok"}],
        },
        raising=False,
    )

    payload = server.validate_twin_readiness(digital_twin_instance_id="twin-1")

    assert payload["ok"] is True
    assert payload["data"]["overall_status"] == "ok"
