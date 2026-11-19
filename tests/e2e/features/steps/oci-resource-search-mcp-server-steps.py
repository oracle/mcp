"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of resource search tools available")
def step_impl_resource_search_tools_available(context):
    response_json = context.result
    assert response_json.text, "Response is empty."
    content = response_json.text.lower()
    expected_tools = [
        "list_all_resources",
        "search_resources",
        "search_resources_free_form",
        "search_resources_by_type",
        "list_resource_types",
    ]
    assert any(
        tool in content for tool in expected_tools
    ), "Resource Search tools could not be queried."


@then("the response should contain a list of resource types")
def step_impl_list_resource_types(context):
    result = context.result
    assert result.text, "Response is empty."
    content = result.text.lower()
    # Check for mock resource type names
    assert any(
        x in content for x in ["instance", "vcn", "subnet", "volume", "bucket"]
    ), "List of resource types not found."


@then("the response should contain a list of resources")
def step_impl_list_resources(context):
    result = context.result
    assert result.text, "Response is empty."
    content = result.text
    # We expect at least one OCID or display name from our mock
    assert (
        "ocid1.instance" in content or "mock-server-1" in content.lower()
    ), "List of resources not found."


@then("the response should contain resources matching the display name search")
def step_impl_search_by_display_name(context):
    result = context.result
    assert result.text, "Response is empty."
    content = result.text.lower()
    assert "mock-server-1" in content, "Display name search results not found."


@then("the response should contain resources matching the free-text search")
def step_impl_search_free_text(context):
    result = context.result
    assert result.text, "Response is empty."
    content = result.text.lower()
    # Free text search for "mock" should return at least one resource
    assert any(
        x in content for x in ["mock-server-1", "ocid1.instance", "subnet"]
    ), "Free-text search results not found."


@then("the response should contain resources of the specified type")
def step_impl_search_by_type(context):
    result = context.result
    assert result.text, "Response is empty."
    content = result.text.lower()
    # Searching for type subnet should include a subnet ocid or name
    assert (
        "ocid1.subnet" in content or "mock-subnet-1" in content
    ), "Typed resource search results not found."
