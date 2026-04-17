import oracle.oci_iot_mcp_server.resolvers as resolvers
from oracle.oci_iot_mcp_server.resolvers import (
    resolve_domain_selector,
    resolve_twin_for_tool,
    resolve_twin_selector,
)


def test_resolve_domain_selector_returns_match_for_short_id(monkeypatch):
    monkeypatch.setattr(
        resolvers,
        "list_iot_domains_records",
        lambda compartment_id: [
            {
                "id": "domain-ocid",
                "name": "factory-domain",
                "device_host": "abc123.device.iot.us-phoenix-1.oci.oraclecloud.com",
            }
        ],
    )

    result = resolve_domain_selector(
        domain_short_id="abc123",
        compartment_id="ocid1.compartment.oc1..aaaa",
    )

    assert result["ok"] is True
    assert result["data"]["id"] == "domain-ocid"


def test_resolve_twin_selector_by_ocid_derives_domain_context(monkeypatch):
    monkeypatch.setattr(
        resolvers,
        "get_digital_twin_instance_record",
        lambda digital_twin_instance_id: {
            "id": digital_twin_instance_id,
            "iot_domain_id": "ocid1.iotdomain.oc1..aaaa",
        },
    )

    result = resolve_twin_selector(
        digital_twin_instance_id="ocid1.digitaltwininstance.oc1..aaaa"
    )

    assert result == {
        "ok": True,
        "data": {
            "id": "ocid1.digitaltwininstance.oc1..aaaa",
            "iot_domain_id": "ocid1.iotdomain.oc1..aaaa",
        },
    }


def test_resolve_twin_selector_requires_domain_scope_for_display_name():
    result = resolve_twin_selector(digital_twin_instance_name="pump-01")

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_input"


def test_resolve_twin_selector_returns_ambiguity_error_with_candidates(monkeypatch):
    monkeypatch.setattr(
        resolvers,
        "list_digital_twin_instances_records",
        lambda iot_domain_id: [
            {"id": "twin-1", "name": "pump-01", "iot_domain_id": iot_domain_id},
            {"id": "twin-2", "name": "pump-01", "iot_domain_id": iot_domain_id},
        ],
    )

    result = resolve_twin_selector(
        digital_twin_instance_name="pump-01",
        iot_domain_id="ocid1.iotdomain.oc1..aaaa",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "ambiguous_identifier"
    assert [candidate["id"] for candidate in result["error"]["details"]["candidates"]] == [
        "twin-1",
        "twin-2",
    ]


def test_resolve_domain_selector_requires_compartment_for_display_name():
    result = resolve_domain_selector(iot_domain_display_name="factory-domain")

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_input"


def test_first_label_returns_none_for_missing_host():
    assert resolvers._first_label(None) is None


def test_resolve_domain_selector_returns_supplied_ocid_without_lookup():
    assert resolve_domain_selector(iot_domain_id="domain-ocid") == {
        "ok": True,
        "data": {"id": "domain-ocid"},
    }


def test_resolve_domain_selector_returns_not_found_when_no_match(monkeypatch):
    monkeypatch.setattr(resolvers, "list_iot_domains_records", lambda compartment_id: [])

    result = resolve_domain_selector(
        iot_domain_display_name="factory-domain",
        compartment_id="ocid1.compartment.oc1..aaaa",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_resolve_domain_selector_returns_ambiguity_error_for_multiple_matches(monkeypatch):
    monkeypatch.setattr(
        resolvers,
        "list_iot_domains_records",
        lambda compartment_id: [
            {"id": "domain-1", "name": "factory-domain", "device_host": "abc.device.iot.us-phoenix-1.oci.oraclecloud.com"},
            {"id": "domain-2", "name": "factory-domain", "device_host": "xyz.device.iot.us-phoenix-1.oci.oraclecloud.com"},
        ],
    )

    result = resolve_domain_selector(
        iot_domain_display_name="factory-domain",
        compartment_id="ocid1.compartment.oc1..aaaa",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "ambiguous_identifier"
    assert [candidate["id"] for candidate in result["error"]["details"]["candidates"]] == [
        "domain-1",
        "domain-2",
    ]


def test_resolve_domain_selector_deduplicates_same_row_matched_by_name_and_short_id(monkeypatch):
    monkeypatch.setattr(
        resolvers,
        "list_iot_domains_records",
        lambda compartment_id: [
            {
                "id": "domain-ocid",
                "name": "factory-domain",
                "device_host": "abc123.device.iot.us-phoenix-1.oci.oraclecloud.com",
            }
        ],
    )

    result = resolve_domain_selector(
        iot_domain_display_name="factory-domain",
        domain_short_id="abc123",
        compartment_id="ocid1.compartment.oc1..aaaa",
    )

    assert result["ok"] is True
    assert result["data"]["id"] == "domain-ocid"


def test_resolve_twin_selector_returns_not_found_when_name_has_no_match(monkeypatch):
    monkeypatch.setattr(resolvers, "list_digital_twin_instances_records", lambda iot_domain_id: [])

    result = resolve_twin_selector(
        digital_twin_instance_name="pump-01",
        iot_domain_id="domain-ocid",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_resolve_twin_selector_returns_single_friendly_match(monkeypatch):
    monkeypatch.setattr(
        resolvers,
        "list_digital_twin_instances_records",
        lambda iot_domain_id: [{"id": "twin-1", "name": "pump-01", "iot_domain_id": iot_domain_id}],
    )

    result = resolve_twin_selector(
        digital_twin_instance_name="pump-01",
        iot_domain_id="domain-ocid",
    )

    assert result == {
        "ok": True,
        "data": {"id": "twin-1", "name": "pump-01", "iot_domain_id": "domain-ocid"},
    }


def test_resolve_twin_for_tool_returns_ocid_lookup_data(monkeypatch):
    monkeypatch.setattr(
        resolvers,
        "resolve_twin_selector",
        lambda **kwargs: {"ok": True, "data": {"id": kwargs["digital_twin_instance_id"], "iot_domain_id": "domain-ocid"}},
    )

    result = resolve_twin_for_tool(digital_twin_instance_id="twin-1")

    assert result == {"id": "twin-1", "iot_domain_id": "domain-ocid"}


def test_resolve_twin_for_tool_requires_selector():
    result = resolve_twin_for_tool()

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_input"


def test_resolve_twin_for_tool_passes_through_domain_resolution_error(monkeypatch):
    monkeypatch.setattr(
        resolvers,
        "resolve_domain_selector",
        lambda **kwargs: {"ok": False, "error": {"code": "ambiguous_identifier"}},
    )

    result = resolve_twin_for_tool(
        digital_twin_instance_name="pump-01",
        compartment_id="ocid1.compartment.oc1..aaaa",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "ambiguous_identifier"


def test_resolve_twin_for_tool_returns_friendly_match(monkeypatch):
    monkeypatch.setattr(
        resolvers,
        "resolve_domain_selector",
        lambda **kwargs: {"ok": True, "data": {"id": "domain-ocid"}},
    )
    monkeypatch.setattr(
        resolvers,
        "resolve_twin_selector",
        lambda **kwargs: {"ok": True, "data": {"id": "twin-1", "iot_domain_id": kwargs["iot_domain_id"]}},
    )

    result = resolve_twin_for_tool(
        digital_twin_instance_name="pump-01",
        iot_domain_display_name="factory-domain",
        compartment_id="ocid1.compartment.oc1..aaaa",
    )

    assert result == {"id": "twin-1", "iot_domain_id": "domain-ocid"}


def test_resolve_twin_for_tool_passes_through_twin_selector_error(monkeypatch):
    monkeypatch.setattr(
        resolvers,
        "resolve_domain_selector",
        lambda **kwargs: {"ok": True, "data": {"id": "domain-ocid"}},
    )
    monkeypatch.setattr(
        resolvers,
        "resolve_twin_selector",
        lambda **kwargs: {"ok": False, "error": {"code": "resource_not_found"}},
    )

    result = resolve_twin_for_tool(
        digital_twin_instance_name="pump-01",
        iot_domain_id="domain-ocid",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"
