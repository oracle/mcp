"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of migration tools available")
def step_impl_migration_tools_available(context):
    response_json = context.result
    assert response_json.text, "Response is empty."
    content = response_json.text.lower()
    assert any(tool in content for tool in ["list_migrations", "get_migration"]), (
        "Migration tools could not be queried."
    )


@then("the response should contain a list of migrations")
def step_impl_list_migrations(context):
    context.result.require_call("list_migrations")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.migration" in result.text.lower(), "List of migrations not found."


@then("the response should contain the details of a migration")
def step_impl_get_migration(context):
    context.result.require_call("get_migration")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.migration" in result.text.lower(), "Migration details not found."
