"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of monitoring tools available")
def step_impl_monitoring_tools_available(context):
    response_json = context.result
    assert response_json.text, "Response is empty."
    content = response_json.text.lower()
    assert any(
        tool in content
        for tool in [
            "list_alarms",
            "list_metric_definitions",
            "get_metrics_data",
        ]
    ), "Monitoring tools could not be queried."


@then("the response should contain a list of alarms")
def step_impl_list_alarms(context):
    context.result.require_call("list_alarms")
    result = context.result
    assert result.text, "Response is empty."
    content = result.text.lower()
    assert (
        "ocid1.alarm" in content or "high cpu alarm" in content
    ), "List of alarms not found."


@then("the response should contain a list of metric definitions")
def step_impl_list_metric_definitions(context):
    context.result.require_call("list_metric_definitions")
    result = context.result
    assert result.text, "Response is empty."
    content = result.text.lower()
    assert (
        "cpuutilization" in content or "oci_computeagent" in content
    ), "List of metric definitions not found."


@then("the response should contain aggregated metric data")
def step_impl_get_metrics_data(context):
    context.result.require_call("get_metrics_data")
    result = context.result
    assert result.text, "Response is empty."
    content = result.text.lower()
    assert (
        "cpuutilization" in content
        or "aggregateddatapoints" in content
        or "45.5" in content
    ), "Aggregated metric data not found."
