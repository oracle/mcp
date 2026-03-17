"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain terraform configuration")
def step_impl_terraform_configuration(context):
    response_json = context.response.json()
    assert "content" in response_json["message"], "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
    assert any(
        keyword in content for keyword in ["terraform", "resource", "provider", ".tf", "infrastructure"]
    ), "Terraform configuration could not be generated."


@then("the response should mention GPU instances")
def step_impl_gpu_instances(context):
    response_json = context.response.json()
    content = response_json["message"]["content"].lower()
    assert any(keyword in content for keyword in ["gpu", "bm.gpu", "vm.gpu", "a10", "v100", "graphics"]), (
        "GPU instances were not mentioned in the response."
    )


@then("the response should mention OCI Gen AI services")
def step_impl_oci_gen_ai(context):
    response_json = context.response.json()
    content = response_json["message"]["content"].lower()
    assert any(
        keyword in content
        for keyword in [
            "gen ai",
            "generative ai",
            "ai service",
            "llama",
            "cohere",
            "model",
        ]
    ), "OCI Gen AI services were not mentioned in the response."
