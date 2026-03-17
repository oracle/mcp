"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime, UTC

import oci

from oracle.oci_jms_mcp_server.models import (
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
