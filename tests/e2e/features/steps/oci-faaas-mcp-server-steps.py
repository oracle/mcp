"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of faaas tools available")
def step_impl_faaas_tools_available(context):
    response_json = context.response.json()
    assert "content" in response_json["message"], "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
    assert any(
        tool in content
        for tool in [
            "list_fusion_environment_families",
            "list_fusion_environments",
            "get_fusion_environment",
            "get_fusion_environment_status",
        ]
    ), "FaaS tools could not be queried."


@then("the response should contain a list of fusion environment families")
def step_impl_list_families(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    # Look for family OCID prefix to be present
    assert "ocid1.fusionenvironmentfamily" in content, "Fusion environment families not found."


@then("the response should contain a list of fusion environments")
def step_impl_list_environments(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert "ocid1.fusionenvironment" in content, "Fusion environments not found."


@then("the response should contain the details of a fusion environment")
def step_impl_get_environment(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert "ocid1.fusionenvironment" in content, "Fusion environment details not found."


@then("the response should contain the status of a fusion environment")
def step_impl_get_environment_status(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    # Expect to mention status and/or environment OCID
    assert any(kw in content for kw in ["status", "available", "ocid1.fusionenvironment"]), (
        "Fusion environment status not found."
    )
