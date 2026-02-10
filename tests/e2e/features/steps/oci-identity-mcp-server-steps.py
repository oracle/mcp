"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of identity tools available")
def step_impl_identity_tools_available(context):
    response_json = context.response.json()
    assert "content" in response_json["message"], "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
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
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.compartment" in result["message"]["content"], "Compartments not found."


@then("the response should contain the details of a tenancy")
def step_impl_get_tenancy(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.tenancy" in result["message"]["content"], "Tenancy details not found."


@then("the response should contain a list of availability domains")
def step_impl_list_ads(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert (
        "us-ashburn-ad" in result["message"]["content"].lower()
        or "availabilitydomain" in result["message"]["content"].lower()
        or "ad-" in result["message"]["content"].lower()
    ), "Availability domains not found."


@then("the response should contain the details of a user")
def step_impl_get_user(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.user" in result["message"]["content"], "User details not found."


@then("the response should contain a list of regions")
def step_impl_list_regions(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(kw in content for kw in ["region", "us-mock-1", "home region", "phx", "iad"]), (
        "Subscribed regions not found."
    )
