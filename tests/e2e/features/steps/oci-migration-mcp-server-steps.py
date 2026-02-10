"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of migration tools available")
def step_impl_migration_tools_available(context):
    response_json = context.response.json()
    assert "content" in response_json["message"], "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
    assert any(tool in content for tool in ["list_migrations", "get_migration"]), (
        "Migration tools could not be queried."
    )


@then("the response should contain a list of migrations")
def step_impl_list_migrations(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.migration" in result["message"]["content"].lower(), "List of migrations not found."


@then("the response should contain the details of a migration")
def step_impl_get_migration(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.migration" in result["message"]["content"].lower(), "Migration details not found."
