"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of JMS tools available")
def step_impl_jms_tools_available(context):
    response_json = context.response.json()
    assert "content" in response_json["message"], "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
    expected_tools = [
        "list_fleets",
        "get_fleet",
        "list_jms_plugins",
        "get_jms_plugin",
        "list_installation_sites",
        "get_fleet_agent_configuration",
        "get_fleet_advanced_feature_configuration",
        "summarize_resource_inventory",
        "summarize_managed_instance_usage",
    ]
    assert any(tool in content for tool in expected_tools), "JMS tools could not be queried."


@then("the response should contain a list of JMS fleets")
def step_impl_list_jms_fleets(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert (
        "ocid1.jmsfleet" in content or "mock-jms-fleet" in content
    ), "List of JMS fleets not found."


@then("the response should contain fleet configuration details")
def step_impl_fleet_configuration(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        value in content
        for value in [
            "mock-jms-fleet",
            "analyticbucketname",
            "jms_analytics_bucket",
            "/u01/java",
            "jrescanfrequencyinminutes",
        ]
    ), "Fleet configuration details not found."


@then("the response should contain JMS plugin details")
def step_impl_jms_plugin_details(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        value in content
        for value in [
            "ocid1.jmsplugin",
            "plugin-host-1",
            "oraclemanagementagent",
            "pluginversion",
        ]
    ), "JMS plugin details not found."


@then("the response should contain installation site and managed instance usage details")
def step_impl_installation_site_and_usage(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        value in content
        for value in [
            "installation-alpha",
            "/usr/lib/jvm/java-17-oracle",
            "managed-instance-1",
            "approximatejrecount",
            "usage-host-1",
        ]
    ), "Installation site or managed instance usage details not found."


@then("the response should contain JMS resource inventory details")
def step_impl_resource_inventory(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        value in content
        for value in [
            "activefleetcount",
            "managedinstancecount",
            "installationcount",
            "applicationcount",
            "42",
        ]
    ), "JMS resource inventory details not found."
