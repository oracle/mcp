"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of logging tools available")
def step_impl_logging_tools_available(context):
    response_json = context.result
    assert response_json.text, "Response is empty."
    content = response_json.text.lower()
    assert any(
        tool in content
        for tool in [
            "list_log_groups",
            "get_log_group",
            "list_logs",
            "get_log",
        ]
    ), "Logging tools could not be queried."


@then("the response should contain a list of log groups")
def step_impl_list_log_groups(context):
    context.result.require_call("list_log_groups")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.loggroup" in result.text.lower(), "List of log groups not found."


@then("the response should contain the details of a log group")
def step_impl_get_log_group(context):
    context.result.require_call("get_log_group")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.loggroup" in result.text.lower(), "Log group details not found."


@then("the response should contain a list of logs")
def step_impl_list_logs(context):
    context.result.require_call("list_logs")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.log" in result.text.lower(), "List of logs not found."


@then("the response should contain the details of a log")
def step_impl_get_log(context):
    context.result.require_call("get_log")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.log" in result.text.lower(), "Log details not found."
