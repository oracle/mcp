# JMS Tool Details

This file documents the 9 tools exposed by `oracle.oci-jms-mcp-server`.

Use this as a quick reference for:

- tool input parameters
- expected output shape
- demo MCP/agent queries

The source of truth is:

- `src/oci-jms-mcp-server/oracle/oci_jms_mcp_server/server.py`
- `src/oci-jms-mcp-server/oracle/oci_jms_mcp_server/models.py`

## General Notes

- Do not send extra keys such as `task_progress` to the tool call payload.
- Enum-like inputs are accepted in flexible form by the wrapper, but the safest values are the OCI SDK values shown below.
- `sort_order` values should be `ASC` or `DESC`.
- Timestamp inputs must be RFC3339 strings.
- For `get_fleet`, prefer using a fleet OCID returned by `list_fleets`.

---

## 1. `list_fleets`

Lists JMS fleets in a compartment.

### Inputs

```json
{
  "compartment_id": "string",
  "id": "string",
  "lifecycle_state": "ACTIVE|CREATING|DELETED|DELETING|FAILED|NEEDS_ATTENTION|UPDATING",
  "display_name": "string",
  "display_name_contains": "string",
  "limit": 50,
  "sort_order": "ASC|DESC",
  "sort_by": "displayName|timeCreated"
}
```

### Output

Returns a list of `FleetSummary` objects:

```json
[
  {
    "id": "ocid1.jmsfleet...",
    "display_name": "Test Fleet",
    "description": "Fleet description",
    "compartment_id": "ocid1.compartment...",
    "approximate_jre_count": 0,
    "approximate_installation_count": 0,
    "approximate_application_count": 0,
    "approximate_managed_instance_count": 0,
    "approximate_java_server_count": 0,
    "approximate_library_count": 0,
    "approximate_library_vulnerability_count": 0,
    "inventory_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup...",
      "log_id": "ocid1.log..."
    },
    "operation_log": {
      "namespace": null,
      "bucket_name": null,
      "object_name": null,
      "log_group_id": "ocid1.loggroup...",
      "log_id": "ocid1.log..."
    },
    "is_advanced_features_enabled": true,
    "is_export_setting_enabled": false,
    "time_created": "2026-02-10T09:27:25.338000Z",
    "lifecycle_state": "FAILED",
    "defined_tags": {},
    "freeform_tags": {},
    "system_tags": {}
  }
]
```

### Demo Query

```text
Call the `list_fleets` tool with:
{
  "compartment_id": "ocid1.compartment.oc1..example",
  "sort_order": "ASC",
  "sort_by": "displayName",
  "limit": 50
}
```

### Demo Query For Failed Fleets

```text
Call the `list_fleets` tool with:
{
  "compartment_id": "ocid1.compartment.oc1..example",
  "lifecycle_state": "FAILED",
  "sort_order": "DESC",
  "sort_by": "timeCreated",
  "limit": 20
}
```

---

## 2. `get_fleet`

Gets one JMS fleet by OCID.

### Inputs

```json
{
  "fleet_id": "ocid1.jmsfleet..."
}
```

### Output

Returns a `Fleet` object. It has the same shape as `FleetSummary` in this server.

### Demo Query

```text
Call the `get_fleet` tool with:
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.example"
}
```

---

## 3. `list_jms_plugins`

Lists JMS plugins for a compartment or fleet.

### Inputs

```json
{
  "compartment_id": "string",
  "compartment_id_in_subtree": false,
  "id": "string",
  "fleet_id": "string",
  "agent_id": "string",
  "lifecycle_state": "ACTIVE|INACTIVE|NEEDS_ATTENTION|DELETED",
  "availability_status": "ACTIVE|SILENT|NOT_AVAILABLE",
  "agent_type": "OMA|OCA",
  "time_registered_less_than_or_equal_to": "2026-03-01T00:00:00Z",
  "time_last_seen_less_than_or_equal_to": "2026-03-01T00:00:00Z",
  "hostname_contains": "host",
  "limit": 50,
  "sort_order": "ASC|DESC",
  "sort_by": "id|timeLastSeen|timeRegistered|hostname|agentId|agentType|lifecycleState|availabilityStatus|fleetId|compartmentId|osFamily|osArchitecture|osDistribution|pluginVersion"
}
```

### Output

Returns a list of `JmsPluginSummary` objects:

```json
[
  {
    "id": "ocid1.jmsplugin...",
    "agent_id": "ocid1.managementagent...",
    "agent_type": "OMA",
    "lifecycle_state": "ACTIVE",
    "availability_status": "ACTIVE",
    "fleet_id": "ocid1.jmsfleet...",
    "compartment_id": "ocid1.compartment...",
    "hostname": "host1",
    "os_family": "LINUX",
    "os_architecture": "x86_64",
    "os_distribution": "Oracle Linux",
    "plugin_version": "string",
    "time_registered": "2026-03-01T00:00:00Z",
    "time_last_seen": "2026-03-10T00:00:00Z",
    "defined_tags": {},
    "freeform_tags": {},
    "system_tags": {}
  }
]
```

### Demo Query

```text
Call the `list_jms_plugins` tool with:
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.example",
  "sort_order": "DESC",
  "sort_by": "timeLastSeen",
  "limit": 25
}
```

---

## 4. `get_jms_plugin`

Gets one JMS plugin by OCID.

### Inputs

```json
{
  "jms_plugin_id": "ocid1.jmsplugin..."
}
```

### Output

Returns a `JmsPlugin` object. In this server it has the same shape as `JmsPluginSummary`.

### Demo Query

```text
Call the `get_jms_plugin` tool with:
{
  "jms_plugin_id": "ocid1.jmsplugin.oc1.iad.example"
}
```

---

## 5. `list_installation_sites`

Lists Java installation sites for a fleet.

### Inputs

```json
{
  "fleet_id": "ocid1.jmsfleet...",
  "jre_vendor": "string",
  "jre_distribution": "string",
  "jre_version": "string",
  "installation_path": "string",
  "application_id": "string",
  "managed_instance_id": "string",
  "os_family": ["LINUX", "WINDOWS", "MACOS", "UNKNOWN"],
  "jre_security_status": "EARLY_ACCESS|UNKNOWN|UP_TO_DATE|UPDATE_REQUIRED|UPGRADE_REQUIRED",
  "path_contains": "string",
  "time_start": "2026-03-01T00:00:00Z",
  "time_end": "2026-03-10T00:00:00Z",
  "limit": 50,
  "sort_order": "ASC|DESC",
  "sort_by": "managedInstanceId|jreDistribution|jreVendor|jreVersion|path|approximateApplicationCount|osName|securityStatus"
}
```

### Output

Returns a list of `InstallationSiteSummary` objects:

```json
[
  {
    "installation_key": "string",
    "managed_instance_id": "ocid1.instance...",
    "jre": {
      "version": "17",
      "vendor": "Oracle",
      "distribution": "JDK",
      "jre_key": "string"
    },
    "security_status": "UP_TO_DATE",
    "path": "/usr/java",
    "operating_system": {
      "family": "LINUX",
      "name": "Oracle Linux",
      "distribution": "Oracle Linux",
      "version": "9",
      "architecture": "x86_64",
      "managed_instance_count": null,
      "container_count": null
    },
    "approximate_application_count": 0,
    "time_last_seen": "2026-03-10T00:00:00Z",
    "blocklist": [],
    "lifecycle_state": "ACTIVE"
  }
]
```

### Demo Query

```text
Call the `list_installation_sites` tool with:
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.example",
  "os_family": ["LINUX"],
  "sort_order": "ASC",
  "sort_by": "managedInstanceId",
  "limit": 20
}
```

---

## 6. `get_fleet_agent_configuration`

Gets fleet-level agent configuration.

### Inputs

```json
{
  "fleet_id": "ocid1.jmsfleet..."
}
```

### Output

Returns a `FleetAgentConfiguration` object:

```json
{
  "jre_scan_frequency_in_minutes": 60,
  "java_usage_tracker_processing_frequency_in_minutes": 15,
  "work_request_validity_period_in_days": 7,
  "agent_polling_interval_in_minutes": 5,
  "is_collecting_managed_instance_metrics_enabled": true,
  "is_collecting_usernames_enabled": false,
  "is_capturing_ip_address_and_fqdn_enabled": false,
  "is_libraries_scan_enabled": false,
  "linux_configuration": {
    "include_paths": ["/usr/java"],
    "exclude_paths": ["/tmp"]
  },
  "windows_configuration": null,
  "mac_os_configuration": null,
  "time_last_modified": "2026-03-01T00:00:00Z"
}
```

### Demo Query

```text
Call the `get_fleet_agent_configuration` tool with:
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.example"
}
```

---

## 7. `get_fleet_advanced_feature_configuration`

Gets advanced feature configuration for a fleet.

### Inputs

```json
{
  "fleet_id": "ocid1.jmsfleet..."
}
```

### Output

Returns a `FleetAdvancedFeatureConfiguration` object:

```json
{
  "analytic_namespace": "string",
  "analytic_bucket_name": "string",
  "lcm": {},
  "crypto_event_analysis": {},
  "advanced_usage_tracking": {},
  "jfr_recording": {},
  "performance_tuning_analysis": {},
  "java_migration_analysis": {},
  "time_last_modified": "2026-03-01T00:00:00Z"
}
```

### Demo Query

```text
Call the `get_fleet_advanced_feature_configuration` tool with:
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.example"
}
```

---

## 8. `summarize_resource_inventory`

Summarizes high-level JMS inventory counts for a compartment.

### Inputs

```json
{
  "compartment_id": "ocid1.compartment...",
  "compartment_id_in_subtree": false,
  "time_start": "2026-03-01T00:00:00Z",
  "time_end": "2026-03-10T00:00:00Z"
}
```

### Output

Returns a `ResourceInventory` object:

```json
{
  "active_fleet_count": 1,
  "managed_instance_count": 2,
  "jre_count": 3,
  "installation_count": 4,
  "application_count": 5
}
```

### Demo Query

```text
Call the `summarize_resource_inventory` tool with:
{
  "compartment_id": "ocid1.compartment.oc1..example",
  "compartment_id_in_subtree": false
}
```

---

## 9. `summarize_managed_instance_usage`

Summarizes managed instance usage records for a fleet.

### Inputs

```json
{
  "fleet_id": "ocid1.jmsfleet...",
  "managed_instance_id": "string",
  "managed_instance_type": "ORACLE_MANAGEMENT_AGENT|ORACLE_CLOUD_AGENT",
  "jre_vendor": "string",
  "jre_distribution": "string",
  "jre_version": "string",
  "installation_path": "string",
  "application_id": "string",
  "fields": ["approximateJreCount", "approximateInstallationCount", "approximateApplicationCount"],
  "time_start": "2026-03-01T00:00:00Z",
  "time_end": "2026-03-10T00:00:00Z",
  "limit": 50,
  "sort_order": "ASC|DESC",
  "sort_by": "timeFirstSeen|timeLastSeen|approximateJreCount|approximateInstallationCount|approximateApplicationCount|osName",
  "os_family": ["LINUX", "WINDOWS", "MACOS", "UNKNOWN"],
  "hostname_contains": "string",
  "library_key": "string"
}
```

### Output

Returns a list of `ManagedInstanceUsage` objects:

```json
[
  {
    "managed_instance_id": "ocid1.instance...",
    "managed_instance_type": "ORACLE_MANAGEMENT_AGENT",
    "hostname": "host1",
    "host_id": "string",
    "ip_addresses": ["10.0.0.10"],
    "hostnames": ["host1"],
    "fqdns": ["host1.example.internal"],
    "operating_system": {
      "family": "LINUX",
      "name": "Oracle Linux",
      "distribution": "Oracle Linux",
      "version": "9",
      "architecture": "x86_64",
      "managed_instance_count": null,
      "container_count": null
    },
    "agent": {},
    "cluster_details": {},
    "approximate_application_count": 0,
    "approximate_installation_count": 0,
    "approximate_jre_count": 0,
    "drs_file_status": "PRESENT",
    "application_invoked_by": "oracle",
    "time_start": "2026-03-01T00:00:00Z",
    "time_end": "2026-03-10T00:00:00Z",
    "time_first_seen": "2026-03-01T00:00:00Z",
    "time_last_seen": "2026-03-10T00:00:00Z"
  }
]
```

### Demo Query

```text
Call the `summarize_managed_instance_usage` tool with:
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.example",
  "fields": ["approximateJreCount"],
  "sort_order": "DESC",
  "sort_by": "timeLastSeen",
  "limit": 25
}
```

---

## Suggested Agent Workflow

### Find a fleet, then inspect it

```text
1. Call `list_fleets` with:
{
  "compartment_id": "ocid1.compartment.oc1..example",
  "sort_order": "ASC",
  "sort_by": "displayName",
  "limit": 50
}
2. Take one returned fleet id.
3. Call `get_fleet` with that fleet id.
```

### Find plugins for a fleet

```text
1. Call `list_jms_plugins` with:
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.example",
  "sort_order": "DESC",
  "sort_by": "timeLastSeen",
  "limit": 25
}
```

### Find installation sites for a fleet

```text
1. Call `list_installation_sites` with:
{
  "fleet_id": "ocid1.jmsfleet.oc1.iad.example",
  "os_family": ["LINUX"],
  "sort_order": "ASC",
  "sort_by": "managedInstanceId",
  "limit": 20
}
```
