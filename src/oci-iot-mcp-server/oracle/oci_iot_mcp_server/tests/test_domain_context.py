import pytest

import oracle.oci_iot_mcp_server.domain_context as domain_context
from oracle.oci_iot_mcp_server.domain_context import derive_domain_context, resolve_domain_context_for_tool


def test_derive_domain_context_parses_short_ids_and_region():
    payload = derive_domain_context(
        iot_domain={
            "id": "domain-ocid",
            "name": "factory",
            "device_host": "abc123.device.iot.us-phoenix-1.oci.oraclecloud.com",
        },
        iot_domain_group={
            "id": "group-ocid",
            "name": "factory-group",
            "data_host": "xyz987.data.iot.us-phoenix-1.oci.oraclecloud.com",
            "db_token_scope": "dbscope",
        },
    )

    assert payload.domain_short_id == "abc123"
    assert payload.domain_group_short_id == "xyz987"
    assert payload.region == "us-phoenix-1"


def test_derive_domain_context_rejects_mismatched_regions():
    with pytest.raises(ValueError, match="share the same OCI region"):
        derive_domain_context(
            iot_domain={
                "id": "domain-ocid",
                "name": "factory",
                "device_host": "abc123.device.iot.us-phoenix-1.oci.oraclecloud.com",
            },
            iot_domain_group={
                "id": "group-ocid",
                "name": "factory-group",
                "data_host": "xyz987.data.iot.us-ashburn-1.oci.oraclecloud.com",
            },
        )


def test_domain_context_helpers_extract_short_id_and_region():
    assert domain_context._first_label("abc123.device.iot.us-phoenix-1.oci.oraclecloud.com") == "abc123"
    assert domain_context._parse_region("abc123.device.iot.us-phoenix-1.oci.oraclecloud.com") == "us-phoenix-1"


def test_resolve_domain_context_for_tool_passes_through_twin_error(monkeypatch):
    monkeypatch.setattr(
        domain_context,
        "resolve_twin_for_tool",
        lambda **kwargs: {"ok": False, "error": {"code": "ambiguous_identifier"}},
    )

    result = resolve_domain_context_for_tool(digital_twin_instance_name="pump-01")

    assert result["ok"] is False
    assert result["error"]["code"] == "ambiguous_identifier"


def test_resolve_domain_context_for_tool_passes_through_domain_selector_error(monkeypatch):
    monkeypatch.setattr(
        domain_context,
        "resolve_domain_selector",
        lambda **kwargs: {"ok": False, "error": {"code": "resource_not_found"}},
    )

    result = resolve_domain_context_for_tool(iot_domain_display_name="factory-domain")

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_resolve_domain_context_for_tool_requires_domain_id(monkeypatch):
    monkeypatch.setattr(
        domain_context,
        "resolve_domain_selector",
        lambda **kwargs: {"ok": True, "data": {"id": None}},
    )

    result = resolve_domain_context_for_tool(domain_short_id="abc123", compartment_id="ocid1.compartment.oc1..aaaa")

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_input"


def test_resolve_domain_context_for_tool_returns_error_when_domain_has_no_group(monkeypatch):
    monkeypatch.setattr(
        domain_context,
        "resolve_domain_selector",
        lambda **kwargs: {"ok": True, "data": {"id": "domain-ocid"}},
    )
    monkeypatch.setattr(
        domain_context,
        "get_iot_domain_record",
        lambda domain_id: {"id": domain_id, "device_host": "abc123.device.iot.us-phoenix-1.oci.oraclecloud.com"},
    )

    result = resolve_domain_context_for_tool(iot_domain_id="domain-ocid")

    assert result["ok"] is False
    assert result["error"]["code"] == "control_plane_error"


def test_resolve_domain_context_for_tool_resolves_from_domain_selector(monkeypatch):
    monkeypatch.setattr(
        domain_context,
        "resolve_domain_selector",
        lambda **kwargs: {"ok": True, "data": {"id": "domain-ocid"}},
    )
    monkeypatch.setattr(
        domain_context,
        "get_iot_domain_record",
        lambda domain_id: {
            "id": domain_id,
            "name": "factory-domain",
            "iot_domain_group_id": "group-ocid",
            "device_host": "abc123.device.iot.us-phoenix-1.oci.oraclecloud.com",
            "db_allowed_identity_domain_host": "id.example.com",
        },
    )
    monkeypatch.setattr(
        domain_context,
        "get_iot_domain_group_record",
        lambda group_id: {
            "id": group_id,
            "name": "factory-group",
            "data_host": "xyz987.data.iot.us-phoenix-1.oci.oraclecloud.com",
            "db_token_scope": "scope",
        },
    )

    result = resolve_domain_context_for_tool(iot_domain_id="domain-ocid")

    assert result["iot_domain_id"] == "domain-ocid"
    assert result["iot_domain_group_id"] == "group-ocid"
    assert result["domain_short_id"] == "abc123"
    assert result["domain_group_short_id"] == "xyz987"


def test_resolve_domain_context_for_tool_resolves_from_twin_selector(monkeypatch):
    monkeypatch.setattr(
        domain_context,
        "resolve_twin_for_tool",
        lambda **kwargs: {"id": "twin-ocid", "iot_domain_id": "domain-ocid"},
    )
    monkeypatch.setattr(
        domain_context,
        "get_iot_domain_record",
        lambda domain_id: {
            "id": domain_id,
            "name": "factory-domain",
            "iot_domain_group_id": "group-ocid",
            "device_host": "abc123.device.iot.us-phoenix-1.oci.oraclecloud.com",
            "db_allowed_identity_domain_host": "id.example.com",
        },
    )
    monkeypatch.setattr(
        domain_context,
        "get_iot_domain_group_record",
        lambda group_id: {
            "id": group_id,
            "name": "factory-group",
            "data_host": "xyz987.data.iot.us-phoenix-1.oci.oraclecloud.com",
            "db_token_scope": "scope",
        },
    )

    result = resolve_domain_context_for_tool(digital_twin_instance_id="twin-ocid")

    assert result["iot_domain_id"] == "domain-ocid"
    assert result["iot_domain_group_id"] == "group-ocid"
