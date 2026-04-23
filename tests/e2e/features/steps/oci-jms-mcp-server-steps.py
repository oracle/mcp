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
        "summarize_fleet_health",
        "get_fleet_health_diagnostics",
        "list_jms_notices",
        "java_runtime_compliance",
    ]
    missing_tools = [tool for tool in expected_tools if tool not in content]
    assert not missing_tools, f"JMS tools could not be queried: missing {missing_tools}"


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
            "hostname",
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
            "hostname",
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


@then("the response should contain JMS fleet health summary details")
def step_impl_fleet_health_summary(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        value in content
        for value in [
            "critical",
            "warning",
            "agent connectivity failure",
            "inventory scan issue",
            "recommended_next_checks",
        ]
    ), "JMS fleet health summary details not found."


@then("the response should contain JMS fleet health diagnostics details")
def step_impl_fleet_health_diagnostics(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        value in content
        for value in [
            "diagnosis_count",
            "fleet_error_count",
            "plugin heartbeat warning",
            "critical agent reporting failure",
            "jms_fleet",
        ]
    ), "JMS fleet health diagnostics details not found."


@then("the response should contain JMS notice details")
def step_impl_jms_notice_details(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        value in content
        for value in [
            "planned jms maintenance window",
            "maintenance",
            "1001",
            "time_released",
            "example.oracle.test/jms/maintenance",
        ]
    ), "JMS notice details not found."


@then("the response should contain JMS runtime compliance details")
def step_impl_jms_runtime_compliance(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        value in content
        for value in [
            "total_runtimes_in_fleet",
            "17.0.10",
            "update_required",
            "nftc",
            "/opt/java/jdk-17.0.10",
        ]
    ), "JMS runtime compliance details not found."
