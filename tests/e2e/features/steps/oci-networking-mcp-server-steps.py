"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of networking tools available")
def step_impl_networking_tools_available(context):
    response_json = context.response.json()
    assert (
        "content" in response_json["message"]
    ), "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
    assert any(
        tool in content
        for tool in [
            "list_vcns",
            "get_vcn",
            "list_subnets",
            "get_subnet",
            "list_security_lists",
        ]
    ), "Networking tools could not be queried."


@then("the response should contain a list of vcns")
def step_impl_list_vcns(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.vcn" in result["message"]["content"], "List of VCNs not found."


@then("the response should contain the details of a vcn")
def step_impl_get_vcn(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.vcn" in result["message"]["content"], "VCN details not found."


@then("the response should contain a list of subnets")
def step_impl_list_subnets(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.subnet" in result["message"]["content"], "List of subnets not found."


@then("the response should contain the details of a subnet")
def step_impl_get_subnet(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.subnet" in result["message"]["content"], "Subnet details not found."


@then("the response should contain a list of security lists")
def step_impl_list_security_lists(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert (
        "ocid1.securitylist" in result["message"]["content"]
    ), "List of security lists not found."


@then("the response should contain the details of a security list")
def step_impl_get_security_list(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert (
        "ocid1.securitylist" in result["message"]["content"]
    ), "Security list details not found."


@then("the response should contain a list of network security groups")
def step_impl_list_nsgs(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert (
        "ocid1.networksecuritygroup" in result["message"]["content"]
    ), "List of network security groups not found."


@then("the response should contain the details of a network security group")
def step_impl_get_nsg(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert (
        "ocid1.networksecuritygroup" in result["message"]["content"]
    ), "Network security group details not found."


@then("the response should contain the details of a vnic")
def step_impl_get_vnic(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert "ocid1.vnic" in result["message"]["content"], "Vnic details not found."
