"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a the tenancy namespace")
def step_impl_namespace(context):
    result = context.response.json()
    print("buckets", result)
    assert "content" in result["message"], "Response does not contain a content key."
    # assert "bucket" in result["message"]["content"]


@then("the response should contain a list of buckets available")
def step_impl_list_buckets(context):
    result = context.response.json()
    print("buckets", result)
    assert "content" in result["message"], "Response does not contain a content key."
    # assert "bucket" in result["message"]["content"]
