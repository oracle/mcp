"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of instance agent command executions")
def step_impl_list_agent_command_executions(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert (
        "ocid1.instanceagentcommand" in content
        or "instance agent command" in content
        or "command executions" in content
    ), "List of instance agent command executions not found."


@then("the response should contain instance agent command execution details")
def step_impl_get_agent_command_execution_details(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert (
        "hello from agent" in content
        or "exit code" in content
        or "succeeded" in content
    ), "Instance agent command execution details not found."
