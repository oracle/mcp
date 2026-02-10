"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of logging tools available")
def step_impl_logging_tools_available(context):
    response_json = context.response.json()
    assert "content" in response_json["message"], "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
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
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.loggroup" in result["message"]["content"].lower(), "List of log groups not found."


@then("the response should contain the details of a log group")
def step_impl_get_log_group(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.loggroup" in result["message"]["content"].lower(), "Log group details not found."


@then("the response should contain a list of logs")
def step_impl_list_logs(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.log" in result["message"]["content"].lower(), "List of logs not found."


@then("the response should contain the details of a log")
def step_impl_get_log(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.log" in result["message"]["content"].lower(), "Log details not found."
