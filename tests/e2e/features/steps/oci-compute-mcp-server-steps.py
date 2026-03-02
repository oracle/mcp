"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of compute tools available")
def step_impl_compute_tools_available(context):
    response_json = context.response.json()
    assert "content" in response_json["message"], "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
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
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.instance" in result["message"]["content"], "List of instances not found."


@then("the response should contain the details of an instance")
def step_impl_get_instance(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.instance" in result["message"]["content"], "Instance details not found."


@then("the response should contain a list of images")
def step_impl_list_images(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.image" in result["message"]["content"], "List of instances not found."


@then("the response should contain the details of an image")
def step_impl_get_image(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.image" in result["message"]["content"], "Image details not found."


@then("the response should contain a list of vnic attachments")
def step_impl_list_vnic_attachments(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.vnicattachment" in result["message"]["content"], "List of vnic attachments not found."


@then("the response should contain the details of a vnic attachment")
def step_impl_get_vnic_attachment(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.vnicattachment" in result["message"]["content"], "Vnic attachment details not found."


@then("the response should contain security analysis")
def step_impl_security_analysis(context):
    response_json = context.response.json()
    assert "content" in response_json["message"], "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
    assert any(
        keyword in content for keyword in ["security", "configuration", "analysis", "review", "assessment"]
    ), "Security analysis could not be performed."


@then("the response should mention security best practices")
def step_impl_security_best_practices(context):
    response_json = context.response.json()
    content = response_json["message"]["content"].lower()
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
    response_json = context.response.json()
    content = response_json["message"]["content"].lower()
    assert any(
        keyword in content for keyword in ["ashburn", "us-ashburn-1", "region", "regional", "location"]
    ), "Regional considerations were not mentioned in the response."
