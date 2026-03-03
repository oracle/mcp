"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of registry tools available")
def step_impl_registry_tools_available(context):
    response_json = context.response.json()
    assert (
        "content" in response_json["message"]
    ), "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
    assert any(
        tool in content
        for tool in [
            "list_container_repositories",
            "get_container_repository",
        ]
    ), "Registry tools could not be queried."


@then("the response should contain a list of container repositories")
def step_impl_list_container_repositories(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert (
        "ocid1.containerrepo" in result["message"]["content"]
    ), "List of container repositories not found."


@then("the response should contain the details of a container repository")
def step_impl_get_container_repository(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert (
        "ocid1.containerrepo" in result["message"]["content"]
    ), "Container repository details not found."
