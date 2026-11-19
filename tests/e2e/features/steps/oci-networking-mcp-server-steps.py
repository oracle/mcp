"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of networking tools available")
def step_impl_networking_tools_available(context):
    response_json = context.result
    assert response_json.text, "Response is empty."
    content = response_json.text.lower()
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
    context.result.require_call("list_vcns")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.vcn" in result.text, "List of VCNs not found."


@then("the response should contain the details of a vcn")
def step_impl_get_vcn(context):
    context.result.require_call("get_vcn")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.vcn" in result.text, "VCN details not found."


@then("the response should contain a list of subnets")
def step_impl_list_subnets(context):
    context.result.require_call("list_subnets")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.subnet" in result.text, "List of subnets not found."


@then("the response should contain the details of a subnet")
def step_impl_get_subnet(context):
    context.result.require_call("get_subnet")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.subnet" in result.text, "Subnet details not found."


@then("the response should contain a list of security lists")
def step_impl_list_security_lists(context):
    context.result.require_call("list_security_lists")
    result = context.result
    assert result.text, "Response is empty."
    assert (
        "ocid1.securitylist" in result.text
    ), "List of security lists not found."


@then("the response should contain the details of a security list")
def step_impl_get_security_list(context):
    context.result.require_call("get_security_list")
    result = context.result
    assert result.text, "Response is empty."
    assert (
        "ocid1.securitylist" in result.text
    ), "Security list details not found."


@then("the response should contain a list of network security groups")
def step_impl_list_nsgs(context):
    context.result.require_call("list_network_security_groups")
    result = context.result
    assert result.text, "Response is empty."
    assert (
        "ocid1.networksecuritygroup" in result.text
    ), "List of network security groups not found."


@then("the response should contain the details of a network security group")
def step_impl_get_nsg(context):
    context.result.require_call("get_network_security_group")
    result = context.result
    assert result.text, "Response is empty."
    assert (
        "ocid1.networksecuritygroup" in result.text
    ), "Network security group details not found."


@then("the response should contain the details of a vnic")
def step_impl_get_vnic(context):
    context.result.require_call("get_vnic")
    result = context.result
    assert result.text, "Response is empty."
    assert "ocid1.vnic" in result.text, "Vnic details not found."
