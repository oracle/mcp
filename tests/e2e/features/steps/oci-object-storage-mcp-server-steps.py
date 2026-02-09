"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a the tenancy namespace")
def step_impl_namespace(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert any(
        key in result["message"]["content"].lower()
        for key in ["namespace", "mock-namespace"]
    ), "Namespace not found in response."


@then("the response should contain a list of buckets available")
def step_impl_list_buckets(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        name in content for name in ["mcp-e2e-bucket", "mcp-e2e-logs"]
    ), "Buckets not listed."


@then("the response should contain the details of a bucket")
def step_impl_bucket_details(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert (
        "ocid1.bucket" in content or "approximate" in content
    ), "Bucket details not found."


@then("the response should contain a list of objects")
def step_impl_list_objects(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        obj in content for obj in ["file1.txt", "app.log", "file2.log"]
    ), "Objects not listed."


@then("the response should contain a list of object versions")
def step_impl_list_object_versions(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert (
        "version_" in content or "object versions" in content
    ), "Object versions not listed."


@then("the response should contain the details of an object")
def step_impl_object_details(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert "file1.txt" in content or "size" in content, "Object details not found."
