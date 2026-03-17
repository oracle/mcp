"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of monitoring tools available")
def step_impl_monitoring_tools_available(context):
    response_json = context.response.json()
    assert (
        "content" in response_json["message"]
    ), "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
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
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert (
        "ocid1.alarm" in content or "high cpu alarm" in content
    ), "List of alarms not found."


@then("the response should contain a list of metric definitions")
def step_impl_list_metric_definitions(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert (
        "cpuutilization" in content or "oci_computeagent" in content
    ), "List of metric definitions not found."


@then("the response should contain aggregated metric data")
def step_impl_get_metrics_data(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert (
        "cpuutilization" in content
        or "aggregateddatapoints" in content
        or "45.5" in content
    ), "Aggregated metric data not found."
