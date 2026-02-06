"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of network load balancer tools available")
def step_impl_nlb_tools_available(context):
    response_json = context.response.json()
    assert (
        "content" in response_json["message"]
    ), "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
    expected_tools = [
        "list_network_load_balancers",
        "get_network_load_balancer",
        "list_network_load_balancer_listeners",
        "get_network_load_balancer_listener",
        "list_network_load_balancer_backend_sets",
        "get_network_load_balancer_backend_set",
        "list_network_load_balancer_backends",
        "get_network_load_balancer_backend",
    ]
    assert any(
        tool in content for tool in expected_tools
    ), "Network Load Balancer tools could not be queried."


@then("the response should contain a list of network load balancers")
def step_impl_list_nlbs(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert (
        "ocid1.nlb" in result["message"]["content"]
    ), "List of network load balancers not found."


@then("the response should contain the details of a network load balancer")
def step_impl_get_nlb(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    assert (
        "ocid1.nlb" in result["message"]["content"]
    ), "Network load balancer details not found."


@then("the response should contain a list of listeners")
def step_impl_list_listeners(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        x in content for x in ["listener-1", "port", "protocol"]
    ), "List of listeners not found."


@then("the response should contain the details of a listener")
def step_impl_get_listener(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        x in content for x in ["listener-1", "defaultbackendsetname", "port"]
    ), "Listener details not found."


@then("the response should contain a list of backend sets")
def step_impl_list_backend_sets(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        x in content for x in ["backendset-1", "policy", "backends"]
    ), "List of backend sets not found."


@then("the response should contain the details of a backend set")
def step_impl_get_backend_set(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        x in content for x in ["backendset-1", "healthchecker", "policy"]
    ), "Backend set details not found."


@then("the response should contain a list of backends")
def step_impl_list_backends(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        x in content for x in ["backend-1", "10.0.0.10", "port"]
    ), "List of backends not found."


@then("the response should contain the details of a backend")
def step_impl_get_backend(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        x in content for x in ["backend-1", "10.0.0.10", "weight"]
    ), "Backend details not found."
