"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of identity tools available")
def step_impl_identity_tools_available(context):
    response_json = context.result
    assert response_json.text, "Response is empty."
    content = response_json.text.lower()
    # Tools from Identity server we expect the model to list
    assert any(
        tool in content
        for tool in [
            "list_compartments",
            "get_tenancy",
            "list_availability_domains",
            "get_current_user",
            "list_subscribed_regions",
        ]
    ), "Identity tools could not be queried."


@then("the response should contain a list of compartments")
def step_impl_list_compartments(context):
    context.result.require_call("list_compartments")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.compartment" in result.text, "Compartments not found."


@then("the response should contain the details of a tenancy")
def step_impl_get_tenancy(context):
    context.result.require_call("get_tenancy", "get_current_tenancy")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.tenancy" in result.text, "Tenancy details not found."


@then("the response should contain a list of availability domains")
def step_impl_list_ads(context):
    context.result.require_call("list_availability_domains")
    result = context.result
    assert result.text, "Response is empty."
    assert (
        "us-ashburn-ad" in result.text.lower()
        or "availabilitydomain" in result.text.lower()
        or "ad-" in result.text.lower()
    ), "Availability domains not found."


@then("the response should contain the details of a user")
def step_impl_get_user(context):
    context.result.require_call("get_current_user")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.user" in result.text, "User details not found."


@then("the response should contain a list of regions")
def step_impl_list_regions(context):
    context.result.require_call("list_subscribed_regions")
    result = context.result
    assert result.text, "Response is empty."
    content = result.text.lower()
    assert any(kw in content for kw in ["region", "us-mock-1", "home region", "phx", "iad"]), (
        "Subscribed regions not found."
    )
