"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of usage tools available")
def step_impl_usage_tools_available(context):
    response_json = context.result
    assert response_json.text, "Response is empty."
    content = response_json.text.lower()
    assert any(
        tool in content
        for tool in [
            "get_summarized_usage",
        ]
    ), "Usage tools could not be queried."


@then("the response should contain a list of usage summaries")
def step_impl_get_summarized_usage(context):
    context.result.require_call("get_summarized_usage")
    result = context.result
    assert result.text, "Response is empty."
    content = result.text
    # We check for values present in the mock data
    assert (
        "10.5" in content or "12.0" in content or "Object Storage" in content
    ), "Usage summaries not found."
