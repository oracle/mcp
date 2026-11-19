"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of cloud guard tools available")
def step_impl_cloud_guard_tools_available(context):
    response_json = context.result
    assert response_json.text, "Response is empty."
    content = response_json.text.lower()
    # Tools from Cloud Guard server
    assert any(tool in content for tool in ["list_problems", "get_problem_details"]), (
        "Cloud Guard tools could not be queried."
    )


@then("the response should contain a list of cloud guard problems")
def step_impl_list_problems(context):
    context.result.require_call("list_problems")
    result = context.result
    assert result.text, "Response is empty."
    # Look for a known OCID prefix for Cloud Guard Problem
    assert "ocid1.cloudguardproblem" in result.text.lower(), (
        "List of Cloud Guard problems not found."
    )


@then("the response should contain the details of a cloud guard problem")
def step_impl_get_problem_details(context):
    context.result.require_call("get_problem_details")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.cloudguardproblem" in result.text.lower(), (
        "Cloud Guard problem details not found."
    )
