from oracle.oci_iot_mcp_server.errors import ambiguity_error, not_found_error
from oracle.oci_iot_mcp_server.tool_models import success_result


def test_ambiguity_error_returns_stable_payload():
    payload = ambiguity_error(
        resource_type="digital_twin_instance",
        message="Multiple digital twin instances matched display name 'pump-01'.",
        input_payload={
            "digital_twin_instance_name": "pump-01",
            "iot_domain_id": "ocid1.iotdomain.oc1..aaaa",
        },
        candidates=[
            {
                "id": "ocid1.digitaltwininstance.oc1..aaaa",
                "display_name": "pump-01",
            }
        ],
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "ambiguous_identifier"
    assert payload["error"]["details"]["candidates"][0]["display_name"] == "pump-01"


def test_success_result_wraps_tool_data():
    assert success_result({"id": "abc"}) == {"ok": True, "data": {"id": "abc"}}


def test_not_found_error_uses_stable_resource_not_found_code():
    payload = not_found_error(
        resource_type="raw_command",
        message="No raw command matched the provided selector.",
        input_payload={"request_id": "rc-1"},
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "resource_not_found"
    assert payload["error"]["details"]["input"] == {"request_id": "rc-1"}
