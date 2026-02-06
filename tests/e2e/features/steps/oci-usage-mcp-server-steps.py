"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of usage tools available")
def step_impl_usage_tools_available(context):
    response_json = context.response.json()
    assert (
        "content" in response_json["message"]
    ), "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
    assert any(
        tool in content
        for tool in [
            "get_summarized_usage",
        ]
    ), "Usage tools could not be queried."


@then("the response should contain a list of usage summaries")
def step_impl_get_summarized_usage(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"]
    # We check for values present in the mock data
    assert (
        "10.5" in content or "12.0" in content or "Object Storage" in content
    ), "Usage summaries not found."
