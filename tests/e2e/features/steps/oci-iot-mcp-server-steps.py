"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import importlib

from behave import given, then, when
from oci.iot.models import (
    DigitalTwinAdapterInboundEnvelope,
    DigitalTwinAdapterInboundRoute,
    DigitalTwinAdapterJsonPayload,
)

from oracle.oci_iot_mcp_server.tool_models import success_result


def _fake_platform_context_envelope():
    return DigitalTwinAdapterInboundEnvelope(
        reference_endpoint="/telemetry",
        reference_payload=DigitalTwinAdapterJsonPayload(data_format="JSON"),
        envelope_mapping={"type": "messageType"},
    )


def _fake_platform_context_route():
    return DigitalTwinAdapterInboundRoute(
        condition="true",
        payload_mapping={"temperature": "temp"},
    )


def _platform_context_payload():
    return {
        "twin": {
            "id": "ocid1.digitaltwininstance.oc1..mock-twin",
            "name": "pump-17",
            "digital_twin_adapter_id": "ocid1.digitaltwinadapter.oc1..mock-adapter",
        },
        "domain": {"id": "ocid1.iotdomain.oc1..mock-domain", "name": "factory-a"},
        "domain_group": {
            "id": "ocid1.iotdomaingroup.oc1..mock-group",
            "name": "factory-group",
        },
        "domain_context": {
            "domain_short_id": "factory-a",
            "domain_group_short_id": "group-a",
            "region": "us-ashburn-1",
            "device_host": "factory-a.iot.us-ashburn-1.oci.oraclecloud.com",
            "data_host": "group-a.data.iot.us-ashburn-1.oci.oraclecloud.com",
        },
        "adapter": {
            "id": "ocid1.digitaltwinadapter.oc1..mock-adapter",
            "name": "pump-adapter",
            "inbound_envelope": _fake_platform_context_envelope(),
            "inbound_routes": [_fake_platform_context_route()],
        },
        "model": {"id": "ocid1.digitaltwinmodel.oc1..mock-model", "name": "pump-model"},
    }


def _latest_state_payload():
    return {
        "twin": {"id": "ocid1.digitaltwininstance.oc1..mock-twin", "name": "pump-17"},
        "latest_snapshot": {"id": "snap-1", "time_created": "2026-03-27T10:00:00Z"},
        "latest_historized": {"id": "hist-1", "time_created": "2026-03-27T09:58:00Z"},
        "latest_raw_command": {"id": "cmd-1", "time_created": "2026-03-27T09:57:00Z"},
        "latest_rejected_data": None,
        "observed_timestamps": {
            "snapshot": "2026-03-27T10:00:00Z",
            "historized": "2026-03-27T09:58:00Z",
            "raw_command": "2026-03-27T09:57:00Z",
            "rejected_data": None,
        },
    }


def _readiness_payload():
    return {
        "overall_status": "ok",
        "twin": {"id": "ocid1.digitaltwininstance.oc1..mock-twin", "name": "pump-17"},
        "checks": [
            {
                "name": "selector_resolution",
                "status": "ok",
                "details": {"twin_id": "ocid1.digitaltwininstance.oc1..mock-twin"},
            },
            {
                "name": "domain_context",
                "status": "ok",
                "details": {"domain_short_id": "factory-a", "region": "us-ashburn-1"},
            },
            {
                "name": "ords_credentials",
                "status": "ok",
                "details": {
                    "present": [
                        "OCI_IOT_ORDS_CLIENT_ID",
                        "OCI_IOT_ORDS_CLIENT_SECRET",
                        "OCI_IOT_ORDS_USERNAME",
                        "OCI_IOT_ORDS_PASSWORD",
                    ],
                    "missing": [],
                },
            },
            {
                "name": "token_mint",
                "status": "ok",
                "details": {"expires_at": "2026-03-27T13:00:00Z"},
            },
            {"name": "snapshot_read", "status": "ok", "details": {"count": 1}},
        ],
    }


@given("the OCI IoT MCP server package is installed")
def step_iot_package_installed(context):
    context.iot_server = importlib.import_module("oracle.oci_iot_mcp_server.server")
    assert context.iot_server is not None


@given("the OCI IoT e2e environment is configured")
def step_iot_environment_configured(context):
    context.configured_twin_args = {
        "digital_twin_instance_id": "ocid1.digitaltwininstance.oc1..mock-twin",
        "digital_twin_instance_name": "pump-17",
        "iot_domain_id": "ocid1.iotdomain.oc1..mock-domain",
        "compartment_id": "ocid1.tenancy.oc1..mock",
    }

    context.iot_server.invoke_raw_command_and_wait = lambda **_: success_result(
        {"request_id": "req-1", "status": "SUCCEEDED"}
    )
    context.iot_server.list_recent_raw_commands_for_twin = lambda **_: success_result(
        [{"id": "cmd-1", "time_created": "2026-03-27T09:57:00Z"}]
    )
    context.iot_server.get_twin_platform_context_impl = lambda **_: _platform_context_payload()
    context.iot_server.get_latest_twin_state_impl = lambda **_: _latest_state_payload()
    context.iot_server.validate_twin_readiness_impl = lambda **_: _readiness_payload()


@when('I invoke "{tool_name}" for the configured digital twin')
def step_invoke_iot_tool(context, tool_name):
    tool = getattr(context.iot_server, tool_name)
    tool_args = dict(context.configured_twin_args)
    if tool_name == "invoke_raw_command_and_wait":
        tool_args.update(
            {
                "request_endpoint": "/commands/reboot",
                "request_data_format": "JSON",
                "request_data": "{\"force\":true}",
            }
        )
    context.tool_response = tool(**tool_args)


@then('the response should have "{field_name}" equal to true')
def step_response_field_is_true(context, field_name):
    assert context.tool_response[field_name] is True


@then('the response data should include "{field_name}"')
def step_response_data_includes_field(context, field_name):
    assert field_name in context.tool_response["data"]


@then("the response data should be a list")
def step_response_data_is_list(context):
    assert isinstance(context.tool_response["data"], list)


@then('the IoT platform context response should include "{field_name}"')
def step_platform_context_includes_field(context, field_name):
    assert field_name in context.tool_response["data"]


@then('the latest twin state response should include "{field_name}"')
def step_latest_state_includes_field(context, field_name):
    assert field_name in context.tool_response["data"]


@then("the readiness response should include at least one check")
def step_readiness_has_checks(context):
    checks = context.tool_response["data"].get("checks", [])
    assert isinstance(checks, list)
    assert len(checks) >= 1
