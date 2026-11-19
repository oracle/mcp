"""
Copyright (c) 2025, 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of compute tools available")
def step_impl_compute_tools_available(context):
    response_json = context.result
    assert response_json.text, "Response is empty."
    content = response_json.text.lower()
    assert any(
        tool in content
        for tool in [
            "list_instances",
            "get_instance",
            "launch_instance",
            "list_images",
            "instance_action",
        ]
    ), "Compute tools could not be queried."


@then("the response should contain a list of running instances")
def step_impl_list_instances(context):
    context.result.require_call("list_instances")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.instance" in result.text, "List of instances not found."


@then("the response should contain the details of an instance")
def step_impl_get_instance(context):
    context.result.require_chain("list_instances", "get_instance", "instance_id")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.instance" in result.text, "Instance details not found."


@then("the response should contain a list of images")
def step_impl_list_images(context):
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.image" in result.text, "List of instances not found."


@then("the response should contain the details of an image")
def step_impl_get_image(context):
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.image" in result.text, "Image details not found."


@then("the response should contain a list of vnic attachments")
def step_impl_list_vnic_attachments(context):
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.vnicattachment" in result.text, "List of vnic attachments not found."


@then("the response should contain the details of a vnic attachment")
def step_impl_get_vnic_attachment(context):
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.vnicattachment" in result.text, "Vnic attachment details not found."


@then("the response should contain security analysis")
def step_impl_security_analysis(context):
    response_json = context.result
    assert response_json.text, "Response is empty."
    content = response_json.text.lower()
    assert any(
        keyword in content for keyword in ["security", "configuration", "analysis", "review", "assessment"]
    ), "Security analysis could not be performed."


@then("the response should mention security best practices")
def step_impl_security_best_practices(context):
    response_json = context.result
    content = response_json.text.lower()
    assert any(
        keyword in content
        for keyword in [
            "best practice",
            "recommendation",
            "improve",
            "strengthen",
            "security group",
            "firewall",
            "ssh",
            "encryption",
        ]
    ), "Security best practices were not mentioned in the response."


@then("the response should reference regional considerations")
def step_impl_regional_considerations(context):
    response_json = context.result
    content = response_json.text.lower()
    assert any(
        keyword in content for keyword in ["ashburn", "us-ashburn-1", "region", "regional", "location"]
    ), "Regional considerations were not mentioned in the response."
