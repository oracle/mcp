"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of registry tools available")
def step_impl_registry_tools_available(context):
    response_json = context.result
    assert response_json.text, "Response is empty."
    content = response_json.text.lower()
    assert any(
        tool in content
        for tool in [
            "list_container_repositories",
            "get_container_repository",
        ]
    ), "Registry tools could not be queried."


@then("the response should contain a list of container repositories")
def step_impl_list_container_repositories(context):
    context.result.require_call("list_container_repositories")
    result = context.result
    assert result.text, "Response is empty."
    assert (
        "ocid1.containerrepo" in result.text
    ), "List of container repositories not found."


@then("the response should contain the details of a container repository")
def step_impl_get_container_repository(context):
    context.result.require_call("get_container_repository")
    result = context.result
    assert result.text, "Response is empty."
    assert (
        "ocid1.containerrepo" in result.text
    ), "Container repository details not found."
