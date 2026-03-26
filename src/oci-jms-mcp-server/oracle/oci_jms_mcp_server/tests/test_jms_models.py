"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime, UTC

import oci

from oracle.oci_jms_mcp_server.models import (
    map_fleet_diagnosis,
    map_fleet_error,
    map_jms_notice,
    map_fleet,
    map_fleet_advanced_feature_configuration,
    map_fleet_agent_configuration,
    map_fleet_summary,
    map_installation_site_summary,
    map_jms_plugin,
    map_jms_plugin_summary,
    map_managed_instance_usage,
    map_resource_inventory,
)


def test_map_fleet_summary():
    now = datetime.now(UTC)
    fleet = oci.jms.models.FleetSummary(
        id="fleet1",
        display_name="Fleet 1",
        compartment_id="compartment1",
        time_created=now,
    )

    result = map_fleet_summary(fleet)

    assert result.id == "fleet1"
    assert result.display_name == "Fleet 1"
    assert result.time_created == now


def test_map_fleet():
    fleet = oci.jms.models.Fleet(id="fleet1", display_name="Fleet 1")
    result = map_fleet(fleet)
    assert result.id == "fleet1"


def test_map_jms_plugin_summary():
    now = datetime.now(UTC)
    plugin = oci.jms.models.JmsPluginSummary(
        id="plugin1",
        agent_type="OMA",
        time_last_seen=now,
    )

    result = map_jms_plugin_summary(plugin)

    assert result.id == "plugin1"
    assert result.agent_type == "OMA"
    assert result.time_last_seen == now


def test_map_jms_plugin():
    plugin = oci.jms.models.JmsPlugin(id="plugin1", hostname="host1")
    result = map_jms_plugin(plugin)
    assert result.hostname == "host1"


def test_map_installation_site_summary_with_nested_values():
    now = datetime.now(UTC)
    site = oci.jms.models.InstallationSiteSummary(
        installation_key="install1",
        managed_instance_id="mi1",
        jre=oci.jms.models.JavaRuntimeId(version="17", vendor="Oracle", distribution="JDK"),
        operating_system=oci.jms.models.OperatingSystem(
            family="LINUX",
            name="Linux",
            version="9",
            architecture="x86_64",
        ),
        time_last_seen=now,
    )

    result = map_installation_site_summary(site)

    assert result.installation_key == "install1"
    assert result.jre.version == "17"
    assert result.operating_system.family == "LINUX"
    assert result.time_last_seen == now


def test_map_fleet_agent_configuration_with_nested_os_configuration():
    config = oci.jms.models.FleetAgentConfiguration(
        jre_scan_frequency_in_minutes=60,
        java_usage_tracker_processing_frequency_in_minutes=15,
        linux_configuration=oci.jms.models.FleetAgentOsConfiguration(include_paths=["/usr/java"]),
    )

    result = map_fleet_agent_configuration(config)

    assert result.jre_scan_frequency_in_minutes == 60
    assert result.linux_configuration.include_paths == ["/usr/java"]


def test_map_fleet_advanced_feature_configuration():
    config = oci.jms.models.FleetAdvancedFeatureConfiguration(
        analytic_namespace="analytics_ns",
        analytic_bucket_name="bucket",
    )

    result = map_fleet_advanced_feature_configuration(config)

    assert result.analytic_namespace == "analytics_ns"
    assert result.analytic_bucket_name == "bucket"


def test_map_managed_instance_usage():
    now = datetime.now(UTC)
    usage = oci.jms.models.ManagedInstanceUsage(
        managed_instance_id="mi1",
        managed_instance_type="ORACLE_MANAGEMENT_AGENT",
        hostname="host1",
        time_first_seen=now,
    )

    result = map_managed_instance_usage(usage)

    assert result.managed_instance_id == "mi1"
    assert result.hostname == "host1"
    assert result.time_first_seen == now


def test_map_resource_inventory():
    inventory = oci.jms.models.ResourceInventory(
        active_fleet_count=1,
        managed_instance_count=2,
        jre_count=3,
        installation_count=4,
        application_count=5,
    )

    result = map_resource_inventory(inventory)

    assert result.active_fleet_count == 1
    assert result.application_count == 5


def test_map_fleet_diagnosis():
    diagnosis = oci.jms.models.FleetDiagnosisSummary(
        resource_diagnosis="Inventory scan issue",
        resource_id="resource1",
        resource_state="FAILED",
        resource_type="JMS_FLEET",
    )

    result = map_fleet_diagnosis(diagnosis)

    assert result.resource_diagnosis == "Inventory scan issue"
    assert result.resource_id == "resource1"
    assert result.resource_state == "UNKNOWN_ENUM_VALUE"


def test_map_fleet_error_with_nested_details():
    now = datetime.now(UTC)
    fleet_error = oci.jms.models.FleetErrorSummary(
        fleet_id="fleet1",
        fleet_name="Fleet 1",
        time_first_seen=now,
        errors=[
            oci.jms.models.FleetErrorDetails(
                reason="Agent connectivity failure",
                details="Critical reporting failure",
                time_last_seen=now,
            )
        ],
    )

    result = map_fleet_error(fleet_error)

    assert result.fleet_id == "fleet1"
    assert result.fleet_name == "Fleet 1"
    assert result.time_first_seen == now
    assert result.errors[0].reason == "UNKNOWN_ENUM_VALUE"
    assert result.errors[0].details == "Critical reporting failure"


def test_map_jms_notice():
    now = datetime.now(UTC)
    notice = oci.jms.models.AnnouncementSummary(
        key=1001,
        summary="Planned maintenance",
        time_released=now,
        url="https://example.com",
    )

    result = map_jms_notice(notice)

    assert result.key == 1001
    assert result.summary == "Planned maintenance"
    assert result.time_released == now
