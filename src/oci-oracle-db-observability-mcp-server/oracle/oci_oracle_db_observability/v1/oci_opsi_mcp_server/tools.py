"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at

"""

from __future__ import annotations

from mcp.types import ToolAnnotations
from pydantic import Field
from datetime import datetime
from typing import Any

from oracle.oci_oracle_db_observability.v1.auth import get_oci_config

from. import __project__, __version__
from. import models
from.metadata import BOOTSTRAP_TOOL_NAMES, MUTABLE_TOOL_NAMES, TOOL_DESCRIPTIONS, TOOL_NAMES
from.models import *  # noqa: F403
from.mcp import mcp
from.runtime import invoke_identity, invoke_opsi, normalize_tool_value


def _tool_title(name: str) -> str:
    return name.replace("_", " ").title()


def _tool_annotations(name: str) -> ToolAnnotations:
    is_mutable = name in MUTABLE_TOOL_NAMES
    return ToolAnnotations(
        title=_tool_title(name),
        readOnlyHint=not is_mutable,
        destructiveHint=is_mutable,
        idempotentHint=not is_mutable,
        openWorldHint=True,)


TOOL_ANNOTATIONS = {name: _tool_annotations(name) for name in TOOL_NAMES}


def _require_tenancy_id() -> str:
    config = get_oci_config(__project__, __version__)
    tenancy_id = config.get("tenancy")
    if not tenancy_id:
        raise ValueError("Configured OCI authentication context is missing tenancy.")
    return tenancy_id


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_compartment"],
    annotations=TOOL_ANNOTATIONS["get_compartment"],)
def get_compartment(
    compartment_id: str = Field(..., description="The compartment OCID."),) -> Any:
    """Get a compartment by OCID."""

    compartment_id = normalize_tool_value(compartment_id)
    if not compartment_id:
        raise ValueError("compartment_id is required.")

    result = invoke_identity("get_compartment", compartment_id=compartment_id)
    if result is None:
        raise ValueError("identity.get_compartment returned an empty response payload.")
    return result


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_compartments"],
    annotations=TOOL_ANNOTATIONS["list_compartments"],)
def list_compartments(
    root_compartment_id: str | None = Field(
        None,
        description="The root compartment OCID. Defaults to the configured tenancy OCID.",),
    include_subtree: bool = Field(
        True,
        description="Whether to include subcompartments.",),
    access_level: models.CompartmentAccessLevel = Field(
        "ACCESSIBLE",
        description="Compartment visibility filter: ANY or ACCESSIBLE.",),
    name: str | None = Field(None, description="Optional exact compartment name filter."),
    lifecycle_state: models.CompartmentLifecycleState | None = Field(
        None,
        description="Optional compartment lifecycle state filter.",),
    limit: int = Field(50, description="Maximum number of compartments to return.", ge=1, le=1000),) -> Any:
    """List compartments from a root compartment."""

    root_compartment_id = normalize_tool_value(root_compartment_id)
    include_subtree = normalize_tool_value(include_subtree)
    access_level = normalize_tool_value(access_level)
    name = normalize_tool_value(name)
    lifecycle_state = normalize_tool_value(lifecycle_state)
    limit = normalize_tool_value(limit)

    resolved_root_compartment_id = root_compartment_id or _require_tenancy_id()

    result = invoke_identity(
        "list_compartments",
        compartment_id=resolved_root_compartment_id,
        compartment_id_in_subtree=include_subtree,
        access_level=access_level,
        name=name,
        lifecycle_state=lifecycle_state,
        limit=limit,)
    if result is None:
        raise ValueError("identity.list_compartments returned an empty response payload.")
    return {"items": result, "count": len(result)}


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_autonomous_database_insight_advanced_features"],
    annotations=TOOL_ANNOTATIONS["change_autonomous_database_insight_advanced_features"],)
def change_autonomous_database_insight_advanced_features(
    change_autonomous_database_insight_advanced_features_details: dict[str, Any] | ChangeAutonomousDatabaseInsightAdvancedFeaturesDetails = Field(..., description='Details for the advanced features of Autonomous Database in Operations Insights.'),
    database_insight_id: str = Field(..., description='Unique database insight identifier'),) -> Any:
    return invoke_opsi('change_autonomous_database_insight_advanced_features', change_autonomous_database_insight_advanced_features_details=change_autonomous_database_insight_advanced_features_details, database_insight_id=database_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_awr_hub_source_compartment"],
    annotations=TOOL_ANNOTATIONS["change_awr_hub_source_compartment"],)
def change_awr_hub_source_compartment(
    awr_hub_source_id: str = Field(..., description='Unique Awr Hub Source identifier'),
    change_awr_hub_source_compartment_details: dict[str, Any] | ChangeAwrHubSourceCompartmentDetails = Field(..., description='The destination compartment for the AWR Hub source.'),) -> Any:
    return invoke_opsi('change_awr_hub_source_compartment', awr_hub_source_id=awr_hub_source_id, change_awr_hub_source_compartment_details=change_awr_hub_source_compartment_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_chargeback_plan_compartment"],
    annotations=TOOL_ANNOTATIONS["change_chargeback_plan_compartment"],)
def change_chargeback_plan_compartment(
    chargebackplan_id: str = Field(..., description='The OCID of the Ops Insights chargeback plan.'),
    change_chargeback_plan_compartment_details: dict[str, Any] | ChangeChargebackPlanCompartmentDetails = Field(..., description='The destination compartment for the chargeback plan.'),) -> Any:
    return invoke_opsi('change_chargeback_plan_compartment', chargebackplan_id=chargebackplan_id, change_chargeback_plan_compartment_details=change_chargeback_plan_compartment_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_database_insight_compartment"],
    annotations=TOOL_ANNOTATIONS["change_database_insight_compartment"],)
def change_database_insight_compartment(
    database_insight_id: str = Field(..., description='Unique database insight identifier'),
    change_database_insight_compartment_details: dict[str, Any] | ChangeDatabaseInsightCompartmentDetails = Field(..., description='The destination compartment for the database insight.'),) -> Any:
    return invoke_opsi('change_database_insight_compartment', database_insight_id=database_insight_id, change_database_insight_compartment_details=change_database_insight_compartment_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_enterprise_manager_bridge_compartment"],
    annotations=TOOL_ANNOTATIONS["change_enterprise_manager_bridge_compartment"],)
def change_enterprise_manager_bridge_compartment(
    enterprise_manager_bridge_id: str = Field(..., description='Unique Enterprise Manager bridge identifier'),
    change_enterprise_manager_bridge_compartment_details: dict[str, Any] | ChangeEnterpriseManagerBridgeCompartmentDetails = Field(..., description='The destination compartment for the Enterprise Manager bridge.'),) -> Any:
    return invoke_opsi('change_enterprise_manager_bridge_compartment', enterprise_manager_bridge_id=enterprise_manager_bridge_id, change_enterprise_manager_bridge_compartment_details=change_enterprise_manager_bridge_compartment_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_exadata_insight_compartment"],
    annotations=TOOL_ANNOTATIONS["change_exadata_insight_compartment"],)
def change_exadata_insight_compartment(
    exadata_insight_id: str = Field(..., description='Unique Exadata insight identifier'),
    change_exadata_insight_compartment_details: dict[str, Any] | ChangeExadataInsightCompartmentDetails = Field(..., description='The destination compartment for the Exadata insight.'),) -> Any:
    return invoke_opsi('change_exadata_insight_compartment', exadata_insight_id=exadata_insight_id, change_exadata_insight_compartment_details=change_exadata_insight_compartment_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_host_insight_compartment"],
    annotations=TOOL_ANNOTATIONS["change_host_insight_compartment"],)
def change_host_insight_compartment(
    host_insight_id: str = Field(..., description='Unique host insight identifier'),
    change_host_insight_compartment_details: dict[str, Any] | ChangeHostInsightCompartmentDetails = Field(..., description='The destination compartment for the host insight.'),) -> Any:
    return invoke_opsi('change_host_insight_compartment', host_insight_id=host_insight_id, change_host_insight_compartment_details=change_host_insight_compartment_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_macs_managed_autonomous_database_insight_connection"],
    annotations=TOOL_ANNOTATIONS["change_macs_managed_autonomous_database_insight_connection"],)
def change_macs_managed_autonomous_database_insight_connection(
    database_insight_id: str = Field(..., description='Unique database insight identifier'),
    change_macs_managed_autonomous_database_insight_connection_details: dict[str, Any] | ChangeMacsManagedAutonomousDatabaseInsightConnectionDetails = Field(..., description='The replacement connection details for the MACS-managed Autonomous Database insight.'),) -> Any:
    return invoke_opsi('change_macs_managed_autonomous_database_insight_connection', database_insight_id=database_insight_id, change_macs_managed_autonomous_database_insight_connection_details=change_macs_managed_autonomous_database_insight_connection_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_macs_managed_cloud_database_insight_connection"],
    annotations=TOOL_ANNOTATIONS["change_macs_managed_cloud_database_insight_connection"],)
def change_macs_managed_cloud_database_insight_connection(
    database_insight_id: str = Field(..., description='Unique database insight identifier'),
    change_macs_managed_cloud_database_insight_connection_details: dict[str, Any] | ChangeMacsManagedCloudDatabaseInsightConnectionDetails = Field(..., description='The replacement connection details for the Cloud MACS-managed database insight.'),) -> Any:
    return invoke_opsi('change_macs_managed_cloud_database_insight_connection', database_insight_id=database_insight_id, change_macs_managed_cloud_database_insight_connection_details=change_macs_managed_cloud_database_insight_connection_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_news_report_compartment"],
    annotations=TOOL_ANNOTATIONS["change_news_report_compartment"],)
def change_news_report_compartment(
    news_report_id: str = Field(..., description='Unique news report identifier.'),
    change_news_report_compartment_details: dict[str, Any] | ChangeNewsReportCompartmentDetails = Field(..., description='The destination compartment for the news report.'),) -> Any:
    return invoke_opsi('change_news_report_compartment', news_report_id=news_report_id, change_news_report_compartment_details=change_news_report_compartment_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_operations_insights_private_endpoint_compartment"],
    annotations=TOOL_ANNOTATIONS["change_operations_insights_private_endpoint_compartment"],)
def change_operations_insights_private_endpoint_compartment(
    operations_insights_private_endpoint_id: str = Field(..., description='The OCID of the Operation Insights private endpoint.'),
    change_operations_insights_private_endpoint_compartment_details: dict[str, Any] | ChangeOperationsInsightsPrivateEndpointCompartmentDetails = Field(..., description='The details used to change the compartment of a private endpoint'),) -> Any:
    return invoke_opsi('change_operations_insights_private_endpoint_compartment', operations_insights_private_endpoint_id=operations_insights_private_endpoint_id, change_operations_insights_private_endpoint_compartment_details=change_operations_insights_private_endpoint_compartment_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_operations_insights_warehouse_compartment"],
    annotations=TOOL_ANNOTATIONS["change_operations_insights_warehouse_compartment"],)
def change_operations_insights_warehouse_compartment(
    operations_insights_warehouse_id: str = Field(..., description='Unique Ops Insights Warehouse identifier'),
    change_operations_insights_warehouse_compartment_details: dict[str, Any] | ChangeOperationsInsightsWarehouseCompartmentDetails = Field(..., description='The destination compartment for the Operations Insights Warehouse.'),) -> Any:
    return invoke_opsi('change_operations_insights_warehouse_compartment', operations_insights_warehouse_id=operations_insights_warehouse_id, change_operations_insights_warehouse_compartment_details=change_operations_insights_warehouse_compartment_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_opsi_configuration_compartment"],
    annotations=TOOL_ANNOTATIONS["change_opsi_configuration_compartment"],)
def change_opsi_configuration_compartment(
    opsi_configuration_id: str = Field(..., description='OCID of OPSI configuration resource.'),
    change_opsi_configuration_compartment_details: dict[str, Any] | ChangeOpsiConfigurationCompartmentDetails = Field(..., description='The destination compartment for the OPSI configuration resource.'),) -> Any:
    return invoke_opsi('change_opsi_configuration_compartment', opsi_configuration_id=opsi_configuration_id, change_opsi_configuration_compartment_details=change_opsi_configuration_compartment_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_pe_comanaged_database_insight"],
    annotations=TOOL_ANNOTATIONS["change_pe_comanaged_database_insight"],)
def change_pe_comanaged_database_insight(
    database_insight_id: str = Field(..., description='Unique database insight identifier'),
    change_pe_comanaged_database_insight_details: dict[str, Any] | ChangePeComanagedDatabaseInsightDetails = Field(..., description='The replacement connection or private endpoint details for the private-endpoint co-managed database insight.'),) -> Any:
    return invoke_opsi('change_pe_comanaged_database_insight', database_insight_id=database_insight_id, change_pe_comanaged_database_insight_details=change_pe_comanaged_database_insight_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_awr_hub"],
    annotations=TOOL_ANNOTATIONS["create_awr_hub"],)
def create_awr_hub(
    create_awr_hub_details: dict[str, Any] | CreateAwrHubDetails = Field(..., description='Details using which an AWR hub resource will be created in Operations Insights.'),) -> Any:
    return invoke_opsi('create_awr_hub', create_awr_hub_details=create_awr_hub_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_awr_hub_source"],
    annotations=TOOL_ANNOTATIONS["create_awr_hub_source"],)
def create_awr_hub_source(
    create_awr_hub_source_details: dict[str, Any] | CreateAwrHubSourceDetails = Field(..., description='Payload containing details to register the source database'),) -> Any:
    return invoke_opsi('create_awr_hub_source', create_awr_hub_source_details=create_awr_hub_source_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_chargeback_plan"],
    annotations=TOOL_ANNOTATIONS["create_chargeback_plan"],)
def create_chargeback_plan(
    create_chargeback_plan_details: dict[str, Any] | CreateChargebackPlanDetails = Field(..., description='Details to create a new chargeback plan resource.'),) -> Any:
    return invoke_opsi('create_chargeback_plan', create_chargeback_plan_details=create_chargeback_plan_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_chargeback_plan_report"],
    annotations=TOOL_ANNOTATIONS["create_chargeback_plan_report"],)
def create_chargeback_plan_report(
    create_chargeback_plan_report_details: dict[str, Any] | CreateChargebackPlanReportDetails = Field(..., description='Details for the chargeback plan report to be created in Ops Insights.'),
    id: str = Field(..., description='Unique Ops insight identifier'),
    resource_type: str = Field(..., description='Filter by resource type. Supported values are EXADATA_INSIGHT, HOST_INSIGHT, DATABASE_INSIGHT.'),) -> Any:
    return invoke_opsi('create_chargeback_plan_report', create_chargeback_plan_report_details=create_chargeback_plan_report_details, id=id, resource_type=resource_type)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_database_insight"],
    annotations=TOOL_ANNOTATIONS["create_database_insight"],)
def create_database_insight(
    create_database_insight_details: dict[str, Any] | CreateDatabaseInsightDetails = Field(..., description='Details for the database for which a Database Insight resource will be created in Operations Insights.'),) -> Any:
    return invoke_opsi('create_database_insight', create_database_insight_details=create_database_insight_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_enterprise_manager_bridge"],
    annotations=TOOL_ANNOTATIONS["create_enterprise_manager_bridge"],)
def create_enterprise_manager_bridge(
    create_enterprise_manager_bridge_details: dict[str, Any] | CreateEnterpriseManagerBridgeDetails = Field(..., description='Details for the Enterprise Manager bridge to be created in Operations Insights.'),) -> Any:
    return invoke_opsi('create_enterprise_manager_bridge', create_enterprise_manager_bridge_details=create_enterprise_manager_bridge_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_exadata_insight"],
    annotations=TOOL_ANNOTATIONS["create_exadata_insight"],)
def create_exadata_insight(
    create_exadata_insight_details: dict[str, Any] | CreateExadataInsightDetails = Field(..., description='Details for the Exadata system for which an Exadata insight resource will be created in Operations Insights.'),) -> Any:
    return invoke_opsi('create_exadata_insight', create_exadata_insight_details=create_exadata_insight_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_host_insight"],
    annotations=TOOL_ANNOTATIONS["create_host_insight"],)
def create_host_insight(
    create_host_insight_details: dict[str, Any] | CreateHostInsightDetails = Field(..., description='Details for the host for which a Host Insight resource will be created in Ops Insights.'),) -> Any:
    return invoke_opsi('create_host_insight', create_host_insight_details=create_host_insight_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_news_report"],
    annotations=TOOL_ANNOTATIONS["create_news_report"],)
def create_news_report(
    create_news_report_details: dict[str, Any] | CreateNewsReportDetails = Field(..., description='Details for the news report that will be created in Ops Insights.'),) -> Any:
    return invoke_opsi('create_news_report', create_news_report_details=create_news_report_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_operations_insights_private_endpoint"],
    annotations=TOOL_ANNOTATIONS["create_operations_insights_private_endpoint"],)
def create_operations_insights_private_endpoint(
    create_operations_insights_private_endpoint_details: dict[str, Any] | CreateOperationsInsightsPrivateEndpointDetails = Field(..., description='Details to create a new private endpoint.'),) -> Any:
    return invoke_opsi('create_operations_insights_private_endpoint', create_operations_insights_private_endpoint_details=create_operations_insights_private_endpoint_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_operations_insights_warehouse"],
    annotations=TOOL_ANNOTATIONS["create_operations_insights_warehouse"],)
def create_operations_insights_warehouse(
    create_operations_insights_warehouse_details: dict[str, Any] | CreateOperationsInsightsWarehouseDetails = Field(..., description='Details using which an Ops Insights Warehouse resource will be created in Ops Insights.'),) -> Any:
    return invoke_opsi('create_operations_insights_warehouse', create_operations_insights_warehouse_details=create_operations_insights_warehouse_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_operations_insights_warehouse_user"],
    annotations=TOOL_ANNOTATIONS["create_operations_insights_warehouse_user"],)
def create_operations_insights_warehouse_user(
    create_operations_insights_warehouse_user_details: dict[str, Any] | CreateOperationsInsightsWarehouseUserDetails = Field(..., description='Parameter using which an Operations Insights Warehouse user resource will be created.'),) -> Any:
    return invoke_opsi('create_operations_insights_warehouse_user', create_operations_insights_warehouse_user_details=create_operations_insights_warehouse_user_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_opsi_configuration"],
    annotations=TOOL_ANNOTATIONS["create_opsi_configuration"],)
def create_opsi_configuration(
    create_opsi_configuration_details: dict[str, Any] | CreateOpsiConfigurationDetails = Field(..., description='Information about OPSI configuration resource to be created.'),
    opsi_config_field: list[str] | None = Field(None, description='Optional fields to return as part of OpsiConfiguration object. Unless requested, these fields will not be returned by default. Allowed values are: "configItems"'),
    config_item_custom_status: list[str] | None = Field(None, description='Specifies whether only customized configuration items or only non-customized configuration items or both have to be returned. By default only customized configuration items are returned. Allowed values are: "customized", "nonCustomized"'),
    config_items_applicable_context: list[str] | None = Field(None, description='Returns the configuration items filtered by applicable contexts sent in this param. By default configuration items of all applicable contexts are returned.'),
    config_item_field: list[str] | None = Field(None, description='Specifies the fields to return in a config item summary. Allowed values are: "name", "value", "defaultValue", "metadata", "applicableContexts"'),) -> Any:
    return invoke_opsi('create_opsi_configuration', create_opsi_configuration_details=create_opsi_configuration_details, opsi_config_field=opsi_config_field, config_item_custom_status=config_item_custom_status, config_items_applicable_context=config_items_applicable_context, config_item_field=config_item_field)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_autonomous_database_insight_advanced_features"],
    annotations=TOOL_ANNOTATIONS["disable_autonomous_database_insight_advanced_features"],)
def disable_autonomous_database_insight_advanced_features(
    database_insight_id: str = Field(..., description='Unique database insight identifier'),) -> Any:
    return invoke_opsi('disable_autonomous_database_insight_advanced_features', database_insight_id=database_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_awr_hub_source"],
    annotations=TOOL_ANNOTATIONS["disable_awr_hub_source"],)
def disable_awr_hub_source(
    awr_hub_source_id: str = Field(..., description='Unique Awr Hub Source identifier'),) -> Any:
    return invoke_opsi('disable_awr_hub_source', awr_hub_source_id=awr_hub_source_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_database_insight"],
    annotations=TOOL_ANNOTATIONS["disable_database_insight"],)
def disable_database_insight(
    database_insight_id: str = Field(..., description='Unique database insight identifier'),) -> Any:
    return invoke_opsi('disable_database_insight', database_insight_id=database_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_exadata_insight"],
    annotations=TOOL_ANNOTATIONS["disable_exadata_insight"],)
def disable_exadata_insight(
    exadata_insight_id: str = Field(..., description='Unique Exadata insight identifier'),) -> Any:
    return invoke_opsi('disable_exadata_insight', exadata_insight_id=exadata_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_host_insight"],
    annotations=TOOL_ANNOTATIONS["disable_host_insight"],)
def disable_host_insight(
    host_insight_id: str = Field(..., description='Unique host insight identifier'),) -> Any:
    return invoke_opsi('disable_host_insight', host_insight_id=host_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_plan_exadata_insight"],
    annotations=TOOL_ANNOTATIONS["disable_plan_exadata_insight"],)
def disable_plan_exadata_insight(
    exadata_insight_id: str = Field(..., description='Unique Exadata insight identifier'),) -> Any:
    return invoke_opsi('disable_plan_exadata_insight', exadata_insight_id=exadata_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_autonomous_database_insight_advanced_features"],
    annotations=TOOL_ANNOTATIONS["enable_autonomous_database_insight_advanced_features"],)
def enable_autonomous_database_insight_advanced_features(
    enable_autonomous_database_insight_advanced_features_details: dict[str, Any] | EnableAutonomousDatabaseInsightAdvancedFeaturesDetails = Field(..., description='Connection Details for the Autonomous Database in Operations Insights.'),
    database_insight_id: str = Field(..., description='Unique database insight identifier'),) -> Any:
    return invoke_opsi('enable_autonomous_database_insight_advanced_features', enable_autonomous_database_insight_advanced_features_details=enable_autonomous_database_insight_advanced_features_details, database_insight_id=database_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_awr_hub_source"],
    annotations=TOOL_ANNOTATIONS["enable_awr_hub_source"],)
def enable_awr_hub_source(
    awr_hub_source_id: str = Field(..., description='Unique Awr Hub Source identifier'),) -> Any:
    return invoke_opsi('enable_awr_hub_source', awr_hub_source_id=awr_hub_source_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_database_insight"],
    annotations=TOOL_ANNOTATIONS["enable_database_insight"],)
def enable_database_insight(
    enable_database_insight_details: dict[str, Any] | EnableDatabaseInsightDetails = Field(..., description='Details for the database to be enabled in Operations Insights.'),
    database_insight_id: str = Field(..., description='Unique database insight identifier'),) -> Any:
    return invoke_opsi('enable_database_insight', enable_database_insight_details=enable_database_insight_details, database_insight_id=database_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_exadata_insight"],
    annotations=TOOL_ANNOTATIONS["enable_exadata_insight"],)
def enable_exadata_insight(
    enable_exadata_insight_details: dict[str, Any] | EnableExadataInsightDetails = Field(..., description='Details for the Exadata system to be enabled in Operations Insights.'),
    exadata_insight_id: str = Field(..., description='Unique Exadata insight identifier'),) -> Any:
    return invoke_opsi('enable_exadata_insight', enable_exadata_insight_details=enable_exadata_insight_details, exadata_insight_id=exadata_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_host_insight"],
    annotations=TOOL_ANNOTATIONS["enable_host_insight"],)
def enable_host_insight(
    enable_host_insight_details: dict[str, Any] | EnableHostInsightDetails = Field(..., description='Details for the host to be enabled in Ops Insights.'),
    host_insight_id: str = Field(..., description='Unique host insight identifier'),) -> Any:
    return invoke_opsi('enable_host_insight', enable_host_insight_details=enable_host_insight_details, host_insight_id=host_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_plan_exadata_insight"],
    annotations=TOOL_ANNOTATIONS["enable_plan_exadata_insight"],)
def enable_plan_exadata_insight(
    enable_plan_exadata_insight_details: dict[str, Any] | EnablePlanExadataInsightDetails = Field(..., description='Details for the Exadata system to be enabled in Operations Insights.'),
    exadata_insight_id: str = Field(..., description='Unique Exadata insight identifier'),) -> Any:
    return invoke_opsi('enable_plan_exadata_insight', enable_plan_exadata_insight_details=enable_plan_exadata_insight_details, exadata_insight_id=exadata_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_awr_database_report"],
    annotations=TOOL_ANNOTATIONS["get_awr_database_report"],)
def get_awr_database_report(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    begin_snapshot_identifier_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_snapshot_identifier_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot Identifier.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    report_type: str | None = Field(None, description='The query parameter to filter the AWR report types. Allowed values are: "AWR", "ASH"'),
    report_format: str | None = Field(None, description='The format of the AWR report. Allowed values are: "HTML", "TEXT"'),) -> Any:
    return invoke_opsi('get_awr_database_report', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, instance_number=instance_number, begin_snapshot_identifier_greater_than_or_equal_to=begin_snapshot_identifier_greater_than_or_equal_to, end_snapshot_identifier_less_than_or_equal_to=end_snapshot_identifier_less_than_or_equal_to, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, report_type=report_type, report_format=report_format)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_awr_database_sql_report"],
    annotations=TOOL_ANNOTATIONS["get_awr_database_sql_report"],)
def get_awr_database_sql_report(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    sql_id: str = Field(..., description='Oracle-generated SQL ID for a SQL statement in the AWR data.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    begin_snapshot_identifier_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_snapshot_identifier_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot Identifier.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    report_format: str | None = Field(None, description='The format of the AWR report. Allowed values are: "HTML", "TEXT"'),) -> Any:
    return invoke_opsi('get_awr_database_sql_report', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, sql_id=sql_id, instance_number=instance_number, begin_snapshot_identifier_greater_than_or_equal_to=begin_snapshot_identifier_greater_than_or_equal_to, end_snapshot_identifier_less_than_or_equal_to=end_snapshot_identifier_less_than_or_equal_to, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, report_format=report_format)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_awr_hub"],
    annotations=TOOL_ANNOTATIONS["get_awr_hub"],)
def get_awr_hub(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),) -> Any:
    return invoke_opsi('get_awr_hub', awr_hub_id=awr_hub_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_awr_hub_object"],
    annotations=TOOL_ANNOTATIONS["get_awr_hub_object"],)
def get_awr_hub_object(
    awr_hub_source_id: str = Field(..., description='Unique Awr Hub Source identifier'),
    object_name: str = Field(..., description='Unique Awr Hub Object identifier'),) -> Any:
    return invoke_opsi('get_awr_hub_object', awr_hub_source_id=awr_hub_source_id, object_name=object_name)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_awr_hub_source"],
    annotations=TOOL_ANNOTATIONS["get_awr_hub_source"],)
def get_awr_hub_source(
    awr_hub_source_id: str = Field(..., description='Unique Awr Hub Source identifier'),) -> Any:
    return invoke_opsi('get_awr_hub_source', awr_hub_source_id=awr_hub_source_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_awr_report"],
    annotations=TOOL_ANNOTATIONS["get_awr_report"],)
def get_awr_report(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    report_format: str | None = Field(None, description='The format of the AWR report. Default report format is HTML. Allowed values are: "HTML", "TEXT"'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    begin_snapshot_identifier_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_snapshot_identifier_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot Identifier.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),) -> Any:
    return invoke_opsi('get_awr_report', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, report_format=report_format, instance_number=instance_number, begin_snapshot_identifier_greater_than_or_equal_to=begin_snapshot_identifier_greater_than_or_equal_to, end_snapshot_identifier_less_than_or_equal_to=end_snapshot_identifier_less_than_or_equal_to, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_chargeback_plan"],
    annotations=TOOL_ANNOTATIONS["get_chargeback_plan"],)
def get_chargeback_plan(
    chargebackplan_id: str = Field(..., description='The OCID of the Ops Insights chargeback plan.'),) -> Any:
    return invoke_opsi('get_chargeback_plan', chargebackplan_id=chargebackplan_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_chargeback_plan_report"],
    annotations=TOOL_ANNOTATIONS["get_chargeback_plan_report"],)
def get_chargeback_plan_report(
    chargeback_plan_report_id: str = Field(..., description='The OCID of the Ops Insights chargeback plan report.'),
    id: str = Field(..., description='Unique Ops insight identifier'),
    resource_type: str = Field(..., description='Filter by resource type. Supported values are EXADATA_INSIGHT, HOST_INSIGHT, DATABASE_INSIGHT.'),) -> Any:
    return invoke_opsi('get_chargeback_plan_report', chargeback_plan_report_id=chargeback_plan_report_id, id=id, resource_type=resource_type)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_chargeback_plan_report_content"],
    annotations=TOOL_ANNOTATIONS["get_chargeback_plan_report_content"],)
def get_chargeback_plan_report_content(
    chargeback_plan_report_id: str = Field(..., description='The OCID of the Ops Insights chargeback plan report.'),
    id: str = Field(..., description='Unique Ops insight identifier'),
    resource_type: str = Field(..., description='Filter by resource type. Supported values are EXADATA_INSIGHT, HOST_INSIGHT, DATABASE_INSIGHT.'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    relative_time_interval: str | None = Field(None, description='Specify relative time period with respect to current time. If relativeTimeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P1M (previous month), P1Q (previous quarter) and P1Y (previous year).'),) -> Any:
    return invoke_opsi('get_chargeback_plan_report_content', chargeback_plan_report_id=chargeback_plan_report_id, id=id, resource_type=resource_type, time_interval_start=time_interval_start, time_interval_end=time_interval_end, relative_time_interval=relative_time_interval)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_database_insight"],
    annotations=TOOL_ANNOTATIONS["get_database_insight"],)
def get_database_insight(
    database_insight_id: str = Field(..., description='Unique database insight identifier'),) -> Any:
    return invoke_opsi('get_database_insight', database_insight_id=database_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_enterprise_manager_bridge"],
    annotations=TOOL_ANNOTATIONS["get_enterprise_manager_bridge"],)
def get_enterprise_manager_bridge(
    enterprise_manager_bridge_id: str = Field(..., description='Unique Enterprise Manager bridge identifier'),) -> Any:
    return invoke_opsi('get_enterprise_manager_bridge', enterprise_manager_bridge_id=enterprise_manager_bridge_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_exadata_insight"],
    annotations=TOOL_ANNOTATIONS["get_exadata_insight"],)
def get_exadata_insight(
    exadata_insight_id: str = Field(..., description='Unique Exadata insight identifier'),) -> Any:
    return invoke_opsi('get_exadata_insight', exadata_insight_id=exadata_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_host_insight"],
    annotations=TOOL_ANNOTATIONS["get_host_insight"],)
def get_host_insight(
    host_insight_id: str = Field(..., description='Unique host insight identifier'),) -> Any:
    return invoke_opsi('get_host_insight', host_insight_id=host_insight_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_news_report"],
    annotations=TOOL_ANNOTATIONS["get_news_report"],)
def get_news_report(
    news_report_id: str = Field(..., description='Unique news report identifier.'),) -> Any:
    return invoke_opsi('get_news_report', news_report_id=news_report_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_operations_insights_private_endpoint"],
    annotations=TOOL_ANNOTATIONS["get_operations_insights_private_endpoint"],)
def get_operations_insights_private_endpoint(
    operations_insights_private_endpoint_id: str = Field(..., description='The OCID of the Operation Insights private endpoint.'),) -> Any:
    return invoke_opsi('get_operations_insights_private_endpoint', operations_insights_private_endpoint_id=operations_insights_private_endpoint_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_operations_insights_warehouse"],
    annotations=TOOL_ANNOTATIONS["get_operations_insights_warehouse"],)
def get_operations_insights_warehouse(
    operations_insights_warehouse_id: str = Field(..., description='Unique Ops Insights Warehouse identifier'),) -> Any:
    return invoke_opsi('get_operations_insights_warehouse', operations_insights_warehouse_id=operations_insights_warehouse_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_operations_insights_warehouse_user"],
    annotations=TOOL_ANNOTATIONS["get_operations_insights_warehouse_user"],)
def get_operations_insights_warehouse_user(
    operations_insights_warehouse_user_id: str = Field(..., description='Unique Operations Insights Warehouse User identifier'),) -> Any:
    return invoke_opsi('get_operations_insights_warehouse_user', operations_insights_warehouse_user_id=operations_insights_warehouse_user_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_opsi_configuration"],
    annotations=TOOL_ANNOTATIONS["get_opsi_configuration"],)
def get_opsi_configuration(
    opsi_configuration_id: str = Field(..., description='OCID of OPSI configuration resource.'),
    opsi_config_field: list[str] | None = Field(None, description='Optional fields to return as part of OpsiConfiguration object. Unless requested, these fields will not be returned by default. Allowed values are: "configItems"'),
    config_item_custom_status: list[str] | None = Field(None, description='Specifies whether only customized configuration items or only non-customized configuration items or both have to be returned. By default only customized configuration items are returned. Allowed values are: "customized", "nonCustomized"'),
    config_items_applicable_context: list[str] | None = Field(None, description='Returns the configuration items filtered by applicable contexts sent in this param. By default configuration items of all applicable contexts are returned.'),
    config_item_field: list[str] | None = Field(None, description='Specifies the fields to return in a config item summary. Allowed values are: "name", "value", "defaultValue", "metadata", "applicableContexts"'),) -> Any:
    return invoke_opsi('get_opsi_configuration', opsi_configuration_id=opsi_configuration_id, opsi_config_field=opsi_config_field, config_item_custom_status=config_item_custom_status, config_items_applicable_context=config_items_applicable_context, config_item_field=config_item_field)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_opsi_data_object"],
    annotations=TOOL_ANNOTATIONS["get_opsi_data_object"],)
def get_opsi_data_object(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    opsi_data_object_identifier: str = Field(..., description='Unique OPSI data object identifier.'),) -> Any:
    return invoke_opsi('get_opsi_data_object', compartment_id=compartment_id, opsi_data_object_identifier=opsi_data_object_identifier)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_work_request"],
    annotations=TOOL_ANNOTATIONS["get_work_request"],)
def get_work_request(
    work_request_id: str = Field(..., description='The ID of the asynchronous request.'),) -> Any:
    return invoke_opsi('get_work_request', work_request_id=work_request_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_addm_db_finding_categories"],
    annotations=TOOL_ANNOTATIONS["list_addm_db_finding_categories"],)
def list_addm_db_finding_categories(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Field name for sorting the finding categories Allowed values are: "name"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_addm_db_finding_categories', compartment_id=compartment_id, database_id=database_id, id=id, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_addm_db_findings_time_series"],
    annotations=TOOL_ANNOTATIONS["list_addm_db_findings_time_series"],)
def list_addm_db_findings_time_series(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    category_name: str | None = Field(None, description='Optional value filter to match the finding category exactly.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Field name for sorting the ADDM finding time series summary data Allowed values are: "timestamp"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_addm_db_findings_time_series', compartment_id=compartment_id, database_id=database_id, id=id, instance_number=instance_number, time_interval_start=time_interval_start, time_interval_end=time_interval_end, category_name=category_name, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_addm_db_parameter_categories"],
    annotations=TOOL_ANNOTATIONS["list_addm_db_parameter_categories"],)
def list_addm_db_parameter_categories(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Field name for sorting the database parameter categories Allowed values are: "name"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_addm_db_parameter_categories', compartment_id=compartment_id, database_id=database_id, id=id, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_addm_db_recommendation_categories"],
    annotations=TOOL_ANNOTATIONS["list_addm_db_recommendation_categories"],)
def list_addm_db_recommendation_categories(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Field name for sorting the recommendation categories Allowed values are: "name"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_addm_db_recommendation_categories', compartment_id=compartment_id, database_id=database_id, id=id, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_addm_db_recommendations_time_series"],
    annotations=TOOL_ANNOTATIONS["list_addm_db_recommendations_time_series"],)
def list_addm_db_recommendations_time_series(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    category_name: str | None = Field(None, description='Optional value filter to match the finding category exactly.'),
    sql_identifier: str | None = Field(None, description='Optional filter to return only resources whose sql id matches the value given. Only considered when categoryName is SQL_TUNING.'),
    owner_or_name_contains: str | None = Field(None, description='Optional filter to return only resources whose owner or name contains the substring given. The match is not case sensitive. Only considered when categoryName is SCHEMA_OBJECT.'),
    name_contains: str | None = Field(None, description='Optional filter to return only resources whose name contains the substring given. The match is not case sensitive. Only considered when categoryName is DATABASE_CONFIGURATION.'),
    name: str | None = Field(None, description='Optional filter to return only resources whose name exactly matches the substring given. The match is case sensitive. Only considered when categoryName is DATABASE_CONFIGURATION.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Field name for sorting the ADDM recommendation time series summary data Allowed values are: "timestamp"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_addm_db_recommendations_time_series', compartment_id=compartment_id, database_id=database_id, id=id, instance_number=instance_number, time_interval_start=time_interval_start, time_interval_end=time_interval_end, category_name=category_name, sql_identifier=sql_identifier, owner_or_name_contains=owner_or_name_contains, name_contains=name_contains, name=name, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_addm_dbs"],
    annotations=TOOL_ANNOTATIONS["list_addm_dbs"],)
def list_addm_dbs(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Field name for sorting ADDM database data Allowed values are: "databaseName", "numberOfFindings"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_addm_dbs', compartment_id=compartment_id, database_id=database_id, id=id, time_interval_start=time_interval_start, time_interval_end=time_interval_end, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_awr_database_snapshots"],
    annotations=TOOL_ANNOTATIONS["list_awr_database_snapshots"],)
def list_awr_database_snapshots(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    begin_snapshot_identifier_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_snapshot_identifier_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot Identifier.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The option to sort the AWR snapshot summary data. Allowed values are: "TIME_BEGIN", "SNAPSHOT_ID"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('list_awr_database_snapshots', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, instance_number=instance_number, begin_snapshot_identifier_greater_than_or_equal_to=begin_snapshot_identifier_greater_than_or_equal_to, end_snapshot_identifier_less_than_or_equal_to=end_snapshot_identifier_less_than_or_equal_to, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_awr_databases"],
    annotations=TOOL_ANNOTATIONS["list_awr_databases"],)
def list_awr_databases(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    name: str | None = Field(None, description='The optional single value query parameter to filter the entity name.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The option to sort the AWR summary data. Allowed values are: "END_INTERVAL_TIME", "NAME"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('list_awr_databases', awr_hub_id=awr_hub_id, name=name, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_awr_hub_objects"],
    annotations=TOOL_ANNOTATIONS["list_awr_hub_objects"],)
def list_awr_hub_objects(
    awr_hub_source_id: str = Field(..., description='Unique Awr Hub Source identifier'),
    prefix: str | None = Field(None, description='The string to use for matching against the start of object names in a Awr Hub list objects query.'),
    start: str | None = Field(None, description='Object names returned by Awr Hub list objects query must be greater or equal to this parameter.'),
    end: str | None = Field(None, description='Object names returned by Awr Hub list objects query must be strictly less than this parameter.'),
    delimiter: str | None = Field(None, description="When this parameter is set, only objects whose names do not contain the delimiter character (after an optionally specified prefix) are returned in the Awr Hub list objects key of the response body. Scanned objects whose names contain the delimiter have the part of their name up to the first occurrence of the delimiter (including the optional prefix) returned as a set of prefixes. Note that only '/' is a supported delimiter character at this time."),
    start_after: str | None = Field(None, description='Awr Hub Object name after which remaining objects are listed'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    fields: str | None = Field(None, description='By default all the fields are returned. Use this parameter to fetch specific fields \'size\', \'etag\', \'md5\', \'timeCreated\', \'timeModified\', \'storageTier\' and \'archivalState\' fields. List the names of those fields in a comma-separated, case-insensitive list as the value of this parameter. For example: \'name,etag,timeCreated,md5,timeModified,storageTier,archivalState\'. Allowed values are: "name", "size", "etag", "timeCreated", "md5", "archivalState", "timeModified", "storageTier"'),) -> Any:
    return invoke_opsi('list_awr_hub_objects', awr_hub_source_id=awr_hub_source_id, prefix=prefix, start=start, end=end, delimiter=delimiter, start_after=start_after, limit=limit, fields=fields)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_awr_hub_sources"],
    annotations=TOOL_ANNOTATIONS["list_awr_hub_sources"],)
def list_awr_hub_sources(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    awr_hub_source_id: str | None = Field(None, description='Awr Hub source identifier'),
    source_type: list[str] | None = Field(None, description='Filter by one or more database type. Possible values are ADW-S, ATP-S, ADW-D, ATP-D, EXTERNAL-PDB, EXTERNAL-NONCDB. Allowed values are: "ADW_S", "ATP_S", "ADW_D", "ATP_D", "EXTERNAL_PDB", "EXTERNAL_NONCDB", "COMANAGED_VM_CDB", "COMANAGED_VM_PDB", "COMANAGED_VM_NONCDB", "COMANAGED_BM_CDB", "COMANAGED_BM_PDB", "COMANAGED_BM_NONCDB", "COMANAGED_EXACS_CDB", "COMANAGED_EXACS_PDB", "COMANAGED_EXACS_NONCDB", "LH_S", "APEX_S", "AJD_S", "AVD_S", "LH_D", "APEX_D", "AJD_D", "AVD_D", "UNDEFINED"'),
    name: str | None = Field(None, description='Awr Hub source database name'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "ACCEPTING", "NOT_ACCEPTING", "NOT_REGISTERED", "TERMINATED"'),
    lifecycle_state: list[str] | None = Field(None, description='Lifecycle states Allowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The field to sort by. Only one sort order may be provided. Default order for timeCreated is descending. Default order for displayName is ascending. If no value is specified timeCreated is default. Allowed values are: "timeCreated", "displayName"'),) -> Any:
    return invoke_opsi('list_awr_hub_sources', awr_hub_id=awr_hub_id, compartment_id=compartment_id, awr_hub_source_id=awr_hub_source_id, source_type=source_type, name=name, status=status, lifecycle_state=lifecycle_state, limit=limit, sort_order=sort_order, sort_by=sort_by)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_awr_hubs"],
    annotations=TOOL_ANNOTATIONS["list_awr_hubs"],)
def list_awr_hubs(
    operations_insights_warehouse_id: str = Field(..., description='Unique Operations Insights Warehouse identifier'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    display_name: str | None = Field(None, description='A filter to return only resources that match the entire display name.'),
    id: str | None = Field(None, description='Unique Awr Hub identifier'),
    lifecycle_state: list[str] | None = Field(None, description='Lifecycle states Allowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The field to sort by. Only one sort order may be provided. Default order for timeCreated is descending. Default order for displayName is ascending. If no value is specified timeCreated is default. Allowed values are: "timeCreated", "displayName"'),) -> Any:
    return invoke_opsi('list_awr_hubs', operations_insights_warehouse_id=operations_insights_warehouse_id, compartment_id=compartment_id, display_name=display_name, id=id, lifecycle_state=lifecycle_state, limit=limit, sort_order=sort_order, sort_by=sort_by)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_awr_snapshots"],
    annotations=TOOL_ANNOTATIONS["list_awr_snapshots"],)
def list_awr_snapshots(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The option to sort the AWR snapshot summary data. Default sort is by timeBegin. Allowed values are: "timeBegin", "snapshotId"'),) -> Any:
    return invoke_opsi('list_awr_snapshots', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, limit=limit, sort_order=sort_order, sort_by=sort_by)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_chargeback_plan_reports"],
    annotations=TOOL_ANNOTATIONS["list_chargeback_plan_reports"],)
def list_chargeback_plan_reports(
    id: str = Field(..., description='Unique Ops insight identifier'),
    resource_type: str = Field(..., description='Filter by resource type. Supported values are EXADATA_INSIGHT, HOST_INSIGHT, DATABASE_INSIGHT.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The field to sort chargeback plan reports. Allowed values are: "timeCreated", "id"'),) -> Any:
    return invoke_opsi('list_chargeback_plan_reports', id=id, resource_type=resource_type, limit=limit, sort_order=sort_order, sort_by=sort_by)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_chargeback_plans"],
    annotations=TOOL_ANNOTATIONS["list_chargeback_plans"],)
def list_chargeback_plans(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    chargebackplan_id: str | None = Field(None, description='The OCID of the Ops Insights chargeback plan.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The field to sort chargeback plans. Allowed values are: "timeCreated", "id", "lifecycleState"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_chargeback_plans', compartment_id=compartment_id, chargebackplan_id=chargebackplan_id, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_database_configurations"],
    annotations=TOOL_ANNOTATIONS["list_database_configurations"],)
def list_database_configurations(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    enterprise_manager_bridge_id: str | None = Field(None, description='Unique Enterprise Manager bridge identifier'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    database_type: list[str] | None = Field(None, description='Filter by one or more database type. Possible values are ADW-S, ATP-S, ADW-D, ATP-D, EXTERNAL-PDB, EXTERNAL-NONCDB. Allowed values are: "ADW-S", "ATP-S", "ADW-D", "ATP-D", "EXTERNAL-PDB", "EXTERNAL-NONCDB", "COMANAGED-VM-CDB", "COMANAGED-VM-PDB", "COMANAGED-VM-NONCDB", "COMANAGED-BM-CDB", "COMANAGED-BM-PDB", "COMANAGED-BM-NONCDB", "COMANAGED-EXACS-CDB", "COMANAGED-EXACS-PDB", "COMANAGED-EXACS-NONCDB", "COMANAGED-EXACC-CDB", "COMANAGED-EXACC-PDB", "COMANAGED-EXACC-NONCDB", "MDS-MYSQL", "EXTERNAL-MYSQL", "ATP-EXACC", "ADW-EXACC", "EXTERNAL-ADW", "EXTERNAL-ATP", "LH-D", "APEX-D", "AJD-D", "AVD-D", "LH-S", "APEX-S", "AJD-S", "AVD-S", "LH-EXACC", "APEX-EXACC", "AJD-EXACC", "AVD-EXACC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Database configuration list sort options. If `fields` parameter is selected, the `sortBy` parameter must be one of the fields specified. Allowed values are: "databaseName", "databaseDisplayName", "databaseType"'),
    host_name: list[str] | None = Field(None, description='Filter by one or more hostname.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),) -> Any:
    return invoke_opsi('list_database_configurations', compartment_id=compartment_id, enterprise_manager_bridge_id=enterprise_manager_bridge_id, id=id, database_id=database_id, exadata_insight_id=exadata_insight_id, cdb_name=cdb_name, database_type=database_type, limit=limit, sort_order=sort_order, sort_by=sort_by, host_name=host_name, compartment_id_in_subtree=compartment_id_in_subtree, vmcluster_name=vmcluster_name)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_database_insights"],
    annotations=TOOL_ANNOTATIONS["list_database_insights"],)
def list_database_insights(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    enterprise_manager_bridge_id: str | None = Field(None, description='Unique Enterprise Manager bridge identifier'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),
    lifecycle_state: list[str] | None = Field(None, description='Lifecycle states Allowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION"'),
    database_type: list[str] | None = Field(None, description='Filter by one or more database type. Possible values are ADW-S, ATP-S, ADW-D, ATP-D, EXTERNAL-PDB, EXTERNAL-NONCDB. Allowed values are: "ADW-S", "ATP-S", "ADW-D", "ATP-D", "EXTERNAL-PDB", "EXTERNAL-NONCDB", "COMANAGED-VM-CDB", "COMANAGED-VM-PDB", "COMANAGED-VM-NONCDB", "COMANAGED-BM-CDB", "COMANAGED-BM-PDB", "COMANAGED-BM-NONCDB", "COMANAGED-EXACS-CDB", "COMANAGED-EXACS-PDB", "COMANAGED-EXACS-NONCDB", "COMANAGED-EXACC-CDB", "COMANAGED-EXACC-PDB", "COMANAGED-EXACC-NONCDB", "MDS-MYSQL", "EXTERNAL-MYSQL", "ATP-EXACC", "ADW-EXACC", "EXTERNAL-ADW", "EXTERNAL-ATP", "LH-D", "APEX-D", "AJD-D", "AVD-D", "LH-S", "APEX-S", "AJD-S", "AVD-S", "LH-EXACC", "APEX-EXACC", "AJD-EXACC", "AVD-EXACC"'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    fields: list[str] | None = Field(None, description='Specifies the fields to return in a database summary response. By default all fields are returned if omitted. Allowed values are: "compartmentId", "databaseName", "databaseDisplayName", "databaseType", "databaseVersion", "databaseHostNames", "freeformTags", "definedTags"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Database insight list sort options. If `fields` parameter is selected, the `sortBy` parameter must be one of the fields specified. Allowed values are: "databaseName", "databaseDisplayName", "databaseType"'),
    exadata_insight_id: str | None = Field(None, description='OCID of exadata insight resource.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    opsi_private_endpoint_id: str | None = Field(None, description='Unique Operations Insights PrivateEndpoint identifier'),) -> Any:
    return invoke_opsi('list_database_insights', compartment_id=compartment_id, enterprise_manager_bridge_id=enterprise_manager_bridge_id, id=id, status=status, lifecycle_state=lifecycle_state, database_type=database_type, database_id=database_id, fields=fields, limit=limit, sort_order=sort_order, sort_by=sort_by, exadata_insight_id=exadata_insight_id, compartment_id_in_subtree=compartment_id_in_subtree, opsi_private_endpoint_id=opsi_private_endpoint_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_enterprise_manager_bridges"],
    annotations=TOOL_ANNOTATIONS["list_enterprise_manager_bridges"],)
def list_enterprise_manager_bridges(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    display_name: str | None = Field(None, description='A filter to return only resources that match the entire display name.'),
    id: str | None = Field(None, description='Unique Enterprise Manager bridge identifier'),
    lifecycle_state: list[str] | None = Field(None, description='Lifecycle states Allowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The field to sort by. Only one sort order may be provided. Default order for timeCreated is descending. Default order for displayName is ascending. If no value is specified timeCreated is default. Allowed values are: "timeCreated", "displayName"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_enterprise_manager_bridges', compartment_id=compartment_id, display_name=display_name, id=id, lifecycle_state=lifecycle_state, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_exadata_configurations"],
    annotations=TOOL_ANNOTATIONS["list_exadata_configurations"],)
def list_exadata_configurations(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    exadata_type: list[str] | None = Field(None, description='Filter by one or more Exadata types. Possible value are DBMACHINE, EXACS, and EXACC.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Exadata configuration list sort options. If `fields` parameter is selected, the `sortBy` parameter must be one of the fields specified. Allowed values are: "exadataName", "exadataDisplayName", "exadataType"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_exadata_configurations', compartment_id=compartment_id, exadata_insight_id=exadata_insight_id, exadata_type=exadata_type, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_exadata_insights"],
    annotations=TOOL_ANNOTATIONS["list_exadata_insights"],)
def list_exadata_insights(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    enterprise_manager_bridge_id: str | None = Field(None, description='Unique Enterprise Manager bridge identifier'),
    id: list[str] | None = Field(None, description='Optional list of Exadata insight resource OCIDs.'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),
    lifecycle_state: list[str] | None = Field(None, description='Lifecycle states Allowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION"'),
    exadata_type: list[str] | None = Field(None, description='Filter by one or more Exadata types. Possible value are DBMACHINE, EXACS, and EXACC.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Exadata insight list sort options. If `fields` parameter is selected, the `sortBy` parameter must be one of the fields specified. Default order for timeCreated is descending. Default order for exadataName is ascending. If no value is specified timeCreated is default. Allowed values are: "timeCreated", "exadataName"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_exadata_insights', compartment_id=compartment_id, enterprise_manager_bridge_id=enterprise_manager_bridge_id, id=id, status=status, lifecycle_state=lifecycle_state, exadata_type=exadata_type, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_host_configurations"],
    annotations=TOOL_ANNOTATIONS["list_host_configurations"],)
def list_host_configurations(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    enterprise_manager_bridge_id: str | None = Field(None, description='Unique Enterprise Manager bridge identifier'),
    id: list[str] | None = Field(None, description='Optional list of host insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    platform_type: list[str] | None = Field(None, description='Filter by one or more platform types. Supported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS]. Supported platformType(s) for MACS-managed cloud host insight: [LINUX]. Supported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX]. Allowed values are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Host configuration list sort options. Allowed values are: "hostName", "platformType"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    host_type: list[str] | None = Field(None, description='Filter by one or more host types. Possible values are CLOUD-HOST, EXTERNAL-HOST, COMANAGED-VM-HOST, COMANAGED-BM-HOST, COMANAGED-EXACS-HOST, COMANAGED-EXACC-HOST'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('list_host_configurations', compartment_id=compartment_id, enterprise_manager_bridge_id=enterprise_manager_bridge_id, id=id, exadata_insight_id=exadata_insight_id, platform_type=platform_type, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree, host_type=host_type, host_id=host_id, vmcluster_name=vmcluster_name, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_host_insights"],
    annotations=TOOL_ANNOTATIONS["list_host_insights"],)
def list_host_insights(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    id: list[str] | None = Field(None, description='Optional list of host insight resource OCIDs.'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),
    lifecycle_state: list[str] | None = Field(None, description='Lifecycle states Allowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION"'),
    host_type: list[str] | None = Field(None, description='Filter by one or more host types. Possible values are CLOUD-HOST, EXTERNAL-HOST, COMANAGED-VM-HOST, COMANAGED-BM-HOST, COMANAGED-EXACS-HOST, COMANAGED-EXACC-HOST'),
    platform_type: list[str] | None = Field(None, description='Filter by one or more platform types. Supported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS]. Supported platformType(s) for MACS-managed cloud host insight: [LINUX]. Supported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX]. Allowed values are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Host insight list sort options. If `fields` parameter is selected, the `sortBy` parameter must be one of the fields specified. Allowed values are: "hostName", "hostType"'),
    enterprise_manager_bridge_id: str | None = Field(None, description='Unique Enterprise Manager bridge identifier'),
    exadata_insight_id: str | None = Field(None, description='OCID of exadata insight resource.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_host_insights', compartment_id=compartment_id, id=id, status=status, lifecycle_state=lifecycle_state, host_type=host_type, platform_type=platform_type, limit=limit, sort_order=sort_order, sort_by=sort_by, enterprise_manager_bridge_id=enterprise_manager_bridge_id, exadata_insight_id=exadata_insight_id, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_hosted_entities"],
    annotations=TOOL_ANNOTATIONS["list_hosted_entities"],)
def list_hosted_entities(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str = Field(..., description='Required OCID of the host insight resource.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    platform_type: list[str] | None = Field(None, description='Filter by one or more platform types. Supported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS]. Supported platformType(s) for MACS-managed cloud host insight: [LINUX]. Supported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX]. Allowed values are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX"'),
    exadata_insight_id: str | None = Field(None, description='OCID of exadata insight resource.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Hosted entity list sort options. Allowed values are: "entityName", "entityType"'),
    host_type: list[str] | None = Field(None, description='Filter by one or more host types. Possible values are CLOUD-HOST, EXTERNAL-HOST, COMANAGED-VM-HOST, COMANAGED-BM-HOST, COMANAGED-EXACS-HOST, COMANAGED-EXACC-HOST'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('list_hosted_entities', compartment_id=compartment_id, id=id, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, platform_type=platform_type, exadata_insight_id=exadata_insight_id, limit=limit, sort_order=sort_order, sort_by=sort_by, host_type=host_type, host_id=host_id, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_importable_agent_entities"],
    annotations=TOOL_ANNOTATIONS["list_importable_agent_entities"],)
def list_importable_agent_entities(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Hosted entity list sort options. Allowed values are: "entityName", "entityType"'),) -> Any:
    return invoke_opsi('list_importable_agent_entities', compartment_id=compartment_id, limit=limit, sort_order=sort_order, sort_by=sort_by)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_importable_compute_entities"],
    annotations=TOOL_ANNOTATIONS["list_importable_compute_entities"],)
def list_importable_compute_entities(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Compute entity list sort options. Allowed values are: "computeId", "computeDisplayName", "platformType", "hostName"'),) -> Any:
    return invoke_opsi('list_importable_compute_entities', compartment_id=compartment_id, limit=limit, sort_order=sort_order, sort_by=sort_by)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_importable_enterprise_manager_entities"],
    annotations=TOOL_ANNOTATIONS["list_importable_enterprise_manager_entities"],)
def list_importable_enterprise_manager_entities(
    enterprise_manager_bridge_id: str = Field(..., description='Unique Enterprise Manager bridge identifier'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    enterprise_manager_entity_type: list[str] | None = Field(None, description='Filter by one or more Enterprise Manager entity types. Currently, the supported types are "oracle_pdb", "oracle_database", "host", "oracle_dbmachine", "oracle_exa_cloud_service", and "oracle_oci_exadata_cloud_service". If this parameter is not specified, targets of all supported entity types are returned by default.'),
    enterprise_manager_identifier: str | None = Field(None, description='Used in combination with enterpriseManagerParentEntityIdentifier to return the members of a particular Enterprise Manager parent entity. Both enterpriseManagerIdentifier and enterpriseManagerParentEntityIdentifier must be specified to identify a particular Enterprise Manager parent entity.'),
    enterprise_manager_parent_entity_identifier: str | None = Field(None, description='Used in combination with enterpriseManagerIdentifier to return the members of a particular Enterprise Manager parent entity. Both enterpriseManagerIdentifier and enterpriseManagerParentEntityIdentifier must be specified to identify a particular Enterprise Manager parent entity.'),) -> Any:
    return invoke_opsi('list_importable_enterprise_manager_entities', enterprise_manager_bridge_id=enterprise_manager_bridge_id, limit=limit, enterprise_manager_entity_type=enterprise_manager_entity_type, enterprise_manager_identifier=enterprise_manager_identifier, enterprise_manager_parent_entity_identifier=enterprise_manager_parent_entity_identifier)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_news_reports"],
    annotations=TOOL_ANNOTATIONS["list_news_reports"],)
def list_news_reports(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    news_report_id: str | None = Field(None, description='Unique Ops Insights news report identifier'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),
    lifecycle_state: list[str] | None = Field(None, description='Lifecycle states Allowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='News report list sort options. If `fields` parameter is selected, the `sortBy` parameter must be one of the fields specified. Allowed values are: "name", "newsFrequency"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_news_reports', compartment_id=compartment_id, news_report_id=news_report_id, status=status, lifecycle_state=lifecycle_state, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_operations_insights_private_endpoints"],
    annotations=TOOL_ANNOTATIONS["list_operations_insights_private_endpoints"],)
def list_operations_insights_private_endpoints(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    display_name: str | None = Field(None, description='A filter to return only resources that match the entire display name.'),
    opsi_private_endpoint_id: str | None = Field(None, description='Unique Operations Insights PrivateEndpoint identifier'),
    is_used_for_rac_dbs: bool | None = Field(None, description='The option to filter OPSI private endpoints that can used for RAC. Should be used along with vcnId query parameter.'),
    vcn_id: str | None = Field(None, description='The OCID of the VCN.'),
    lifecycle_state: list[str] | None = Field(None, description='Lifecycle states Allowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The field to sort private endpoints. Allowed values are: "timeCreated", "id", "displayName"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_operations_insights_private_endpoints', compartment_id=compartment_id, display_name=display_name, opsi_private_endpoint_id=opsi_private_endpoint_id, is_used_for_rac_dbs=is_used_for_rac_dbs, vcn_id=vcn_id, lifecycle_state=lifecycle_state, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_operations_insights_warehouse_users"],
    annotations=TOOL_ANNOTATIONS["list_operations_insights_warehouse_users"],)
def list_operations_insights_warehouse_users(
    operations_insights_warehouse_id: str = Field(..., description='Unique Operations Insights Warehouse identifier'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    display_name: str | None = Field(None, description='A filter to return only resources that match the entire display name.'),
    id: str | None = Field(None, description='Unique Operations Insights Warehouse User identifier'),
    lifecycle_state: list[str] | None = Field(None, description='Lifecycle states Allowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The field to sort by. Only one sort order may be provided. Default order for timeCreated is descending. Default order for displayName is ascending. If no value is specified timeCreated is default. Allowed values are: "timeCreated", "displayName"'),) -> Any:
    return invoke_opsi('list_operations_insights_warehouse_users', operations_insights_warehouse_id=operations_insights_warehouse_id, compartment_id=compartment_id, display_name=display_name, id=id, lifecycle_state=lifecycle_state, limit=limit, sort_order=sort_order, sort_by=sort_by)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_operations_insights_warehouses"],
    annotations=TOOL_ANNOTATIONS["list_operations_insights_warehouses"],)
def list_operations_insights_warehouses(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    display_name: str | None = Field(None, description='A filter to return only resources that match the entire display name.'),
    id: str | None = Field(None, description='Unique Ops Insights Warehouse identifier'),
    lifecycle_state: list[str] | None = Field(None, description='Lifecycle states Allowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The field to sort by. Only one sort order may be provided. Default order for timeCreated is descending. Default order for displayName is ascending. If no value is specified timeCreated is default. Allowed values are: "timeCreated", "displayName"'),) -> Any:
    return invoke_opsi('list_operations_insights_warehouses', compartment_id=compartment_id, display_name=display_name, id=id, lifecycle_state=lifecycle_state, limit=limit, sort_order=sort_order, sort_by=sort_by)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_opsi_configurations"],
    annotations=TOOL_ANNOTATIONS["list_opsi_configurations"],)
def list_opsi_configurations(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    display_name: str | None = Field(None, description='Filter to return based on resources that match the entire display name.'),
    lifecycle_state: list[str] | None = Field(None, description='Filter to return based on Lifecycle state of OPSI configuration. Allowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED"'),
    opsi_config_type: list[str] | None = Field(None, description='Filter to return based on configuration type of OPSI configuration. Allowed values are: "UX_CONFIGURATION"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='OPSI configurations list sort options. Allowed values are: "displayName"'),) -> Any:
    return invoke_opsi('list_opsi_configurations', compartment_id=compartment_id, display_name=display_name, lifecycle_state=lifecycle_state, opsi_config_type=opsi_config_type, limit=limit, sort_order=sort_order, sort_by=sort_by)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_opsi_data_objects"],
    annotations=TOOL_ANNOTATIONS["list_opsi_data_objects"],)
def list_opsi_data_objects(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    data_object_type: list[str] | None = Field(None, description='OPSI data object types. Allowed values are: "DATABASE_INSIGHTS_DATA_OBJECT", "HOST_INSIGHTS_DATA_OBJECT", "EXADATA_INSIGHTS_DATA_OBJECT"'),
    display_name: str | None = Field(None, description='A filter to return only resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='OPSI data object list sort options. Allowed values are: "displayName", "dataObjectType", "name"'),
    group_name: str | None = Field(None, description='A filter to return only data objects that belongs to the group of the given group name. By default, no filtering will be applied on group name.'),
    name: str | None = Field(None, description='A filter to return only data objects that match the entire data object name. By default, no filtering will be applied on data object name.'),) -> Any:
    return invoke_opsi('list_opsi_data_objects', compartment_id=compartment_id, data_object_type=data_object_type, display_name=display_name, limit=limit, sort_order=sort_order, sort_by=sort_by, group_name=group_name, name=name)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_sql_plans"],
    annotations=TOOL_ANNOTATIONS["list_sql_plans"],)
def list_sql_plans(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    sql_identifier: str = Field(..., description='Unique SQL_ID for a SQL Statement. Example: `6rgjh9bjmy2s7`'),
    plan_hash: list[int] = Field(..., description='Unique plan hash for a SQL Plan of a particular SQL Statement. Example: `9820154385`'),
    database_id: str | None = Field(None, description='Optional OCID of the associated DBaaS entity.'),
    id: str | None = Field(None, description='OCID of the database insight resource.'),) -> Any:
    return invoke_opsi('list_sql_plans', compartment_id=compartment_id, sql_identifier=sql_identifier, plan_hash=plan_hash, database_id=database_id, id=id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_sql_texts"],
    annotations=TOOL_ANNOTATIONS["list_sql_texts"],)
def list_sql_texts(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    sql_identifier: list[str] = Field(..., description='One or more unique SQL_IDs for a SQL Statement. Example: `6rgjh9bjmy2s7`'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the assosicated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database OCIDs of the database insight resource.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('list_sql_texts', compartment_id=compartment_id, sql_identifier=sql_identifier, database_id=database_id, id=id, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_warehouse_data_objects"],
    annotations=TOOL_ANNOTATIONS["list_warehouse_data_objects"],)
def list_warehouse_data_objects(
    warehouse_type: str = Field(..., description='Type of the Warehouse. Allowed values are: "awrHubs"'),
    warehouse_id: str = Field(..., description='The OCID of a Warehouse.'),
    data_object_type: list[str] | None = Field(None, description='A filter to return only data objects that match the data object type. By default, no filtering will be applied on data object type. Allowed values are: "VIEW", "TABLE"'),
    name: str | None = Field(None, description='A filter to return only data objects that match the entire data object name. By default, no filtering will be applied on data object name.'),
    owner: str | None = Field(None, description='A filter to return only data objects that match the entire data object owner name. By default, no filtering will be applied on data object owner name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Sort options for Warehouse data objects list. Allowed values are: "dataObjectType", "name", "owner"'),
    summary_field: list[str] | None = Field(None, description='Specifies the optional fields to return in a WarehouseDataObjectSummary. Unless requested, these fields are not returned by default. Allowed values are: "details"'),) -> Any:
    return invoke_opsi('list_warehouse_data_objects', warehouse_type=warehouse_type, warehouse_id=warehouse_id, data_object_type=data_object_type, name=name, owner=owner, limit=limit, sort_order=sort_order, sort_by=sort_by, summary_field=summary_field)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_work_request_errors"],
    annotations=TOOL_ANNOTATIONS["list_work_request_errors"],)
def list_work_request_errors(
    work_request_id: str = Field(..., description='The ID of the asynchronous request.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The field to sort by. Only one sort order may be provided. Default order for timeAccepted is descending. Allowed values are: "timeAccepted"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('list_work_request_errors', work_request_id=work_request_id, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_work_request_logs"],
    annotations=TOOL_ANNOTATIONS["list_work_request_logs"],)
def list_work_request_logs(
    work_request_id: str = Field(..., description='The ID of the asynchronous request.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The field to sort by. Only one sort order may be provided. Default order for timeAccepted is descending. Allowed values are: "timeAccepted"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('list_work_request_logs', work_request_id=work_request_id, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_work_requests"],
    annotations=TOOL_ANNOTATIONS["list_work_requests"],)
def list_work_requests(
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    id: str | None = Field(None, description='The ID of the asynchronous work request.'),
    status: str | None = Field(None, description='A filter to return only resources their lifecycleState matches the given OperationStatus. Allowed values are: "ACCEPTED", "IN_PROGRESS", "WAITING", "FAILED", "SUCCEEDED", "CANCELING", "CANCELED"'),
    resource_id: str | None = Field(None, description='The ID of the resource affected by the work request.'),
    related_resource_id: str | None = Field(None, description='The ID of the related resource for the resource affected by the work request, e.g. the related Exadata Insight OCID of the Database Insight work request'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The field to sort by. Only one sort order may be provided. Default order for timeAccepted is descending. Allowed values are: "timeAccepted"'),) -> Any:
    return invoke_opsi('list_work_requests', limit=limit, compartment_id=compartment_id, id=id, status=status, resource_id=resource_id, related_resource_id=related_resource_id, sort_order=sort_order, sort_by=sort_by)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["query_opsi_data_object_data"],
    annotations=TOOL_ANNOTATIONS["query_opsi_data_object_data"],)
def query_opsi_data_object_data(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    query_opsi_data_object_data_details: dict[str, Any] | QueryOpsiDataObjectDataDetails = Field(..., description='The information to be used for querying an OPSI data object.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),) -> Any:
    return invoke_opsi('query_opsi_data_object_data', compartment_id=compartment_id, query_opsi_data_object_data_details=query_opsi_data_object_data_details, limit=limit)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["query_warehouse_data_object_data"],
    annotations=TOOL_ANNOTATIONS["query_warehouse_data_object_data"],)
def query_warehouse_data_object_data(
    warehouse_type: str = Field(..., description='Type of the Warehouse. Allowed values are: "awrHubs"'),
    warehouse_id: str = Field(..., description='The OCID of a Warehouse.'),
    query_warehouse_data_object_data_details: dict[str, Any] | QueryWarehouseDataObjectDataDetails = Field(..., description='The information to be used for querying a Warehouse.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),) -> Any:
    return invoke_opsi('query_warehouse_data_object_data', warehouse_type=warehouse_type, warehouse_id=warehouse_id, query_warehouse_data_object_data_details=query_warehouse_data_object_data_details, limit=limit)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_addm_db_findings"],
    annotations=TOOL_ANNOTATIONS["summarize_addm_db_findings"],)
def summarize_addm_db_findings(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    category_name: str | None = Field(None, description='Optional value filter to match the finding category exactly.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Field name for sorting the ADDM finding summary data Allowed values are: "impactOverallPercent", "impactMaxPercent", "impactAvgActiveSessions", "frequencyCount"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('summarize_addm_db_findings', compartment_id=compartment_id, database_id=database_id, id=id, instance_number=instance_number, time_interval_start=time_interval_start, time_interval_end=time_interval_end, category_name=category_name, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_addm_db_parameter_changes"],
    annotations=TOOL_ANNOTATIONS["summarize_addm_db_parameter_changes"],)
def summarize_addm_db_parameter_changes(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    name: str = Field(..., description='Required filter to return only changes for the specified parameter. The match is case sensitive.'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    value_contains: str | None = Field(None, description='Optional filter to return only resources whose value contains the substring given. The match is not case sensitive.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Field name for sorting the database parameter change data Allowed values are: "isChanged", "beginSnapId"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('summarize_addm_db_parameter_changes', compartment_id=compartment_id, name=name, database_id=database_id, id=id, instance_number=instance_number, time_interval_start=time_interval_start, time_interval_end=time_interval_end, value_contains=value_contains, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_addm_db_parameters"],
    annotations=TOOL_ANNOTATIONS["summarize_addm_db_parameters"],)
def summarize_addm_db_parameters(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    category_name: str | None = Field(None, description='Optional value filter to match an ADDM database parameter category exactly. Use a category name returned by ADDM database parameter category results.'),
    name_or_value_contains: str | None = Field(None, description='Optional filter to return only resources whose name or value contains the substring given. The match is not case sensitive.'),
    is_changed: str | None = Field(None, description='Optional filter to return only parameters whose value changed in the specified time period. Valid values include: TRUE, FALSE Allowed values are: "TRUE", "FALSE"'),
    is_default: str | None = Field(None, description='Optional filter to return only parameters whose end value was set to the default value (TRUE) or was specified in the parameter file (FALSE). Valid values include: TRUE, FALSE Allowed values are: "TRUE", "FALSE"'),
    has_recommendations: str | None = Field(None, description='Optional filter to return only parameters which have recommendations in the specified time period. Valid values include: TRUE, FALSE Allowed values are: "TRUE", "FALSE"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Field name for sorting the database parameter data Allowed values are: "isChanged", "name"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('summarize_addm_db_parameters', compartment_id=compartment_id, database_id=database_id, id=id, instance_number=instance_number, time_interval_start=time_interval_start, time_interval_end=time_interval_end, category_name=category_name, name_or_value_contains=name_or_value_contains, is_changed=is_changed, is_default=is_default, has_recommendations=has_recommendations, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_addm_db_recommendations"],
    annotations=TOOL_ANNOTATIONS["summarize_addm_db_recommendations"],)
def summarize_addm_db_recommendations(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    category_name: str | None = Field(None, description='Optional value filter to match the finding category exactly.'),
    finding_identifier: str | None = Field(None, description='Unique finding ID'),
    sql_identifier: str | None = Field(None, description='Optional filter to return only resources whose sql id matches the value given. Only considered when categoryName is SQL_TUNING.'),
    owner_or_name_contains: str | None = Field(None, description='Optional filter to return only resources whose owner or name contains the substring given. The match is not case sensitive. Only considered when categoryName is SCHEMA_OBJECT.'),
    name_contains: str | None = Field(None, description='Optional filter to return only resources whose name contains the substring given. The match is not case sensitive. Only considered when categoryName is DATABASE_CONFIGURATION.'),
    name: str | None = Field(None, description='Optional filter to return only resources whose name exactly matches the substring given. The match is case sensitive. Only considered when categoryName is DATABASE_CONFIGURATION.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Field name for sorting the recommendation data Allowed values are: "maxBenefitPercent", "maxBenefitAvgActiveSessions", "frequencyCount"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('summarize_addm_db_recommendations', compartment_id=compartment_id, database_id=database_id, id=id, instance_number=instance_number, time_interval_start=time_interval_start, time_interval_end=time_interval_end, category_name=category_name, finding_identifier=finding_identifier, sql_identifier=sql_identifier, owner_or_name_contains=owner_or_name_contains, name_contains=name_contains, name=name, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_addm_db_schema_objects"],
    annotations=TOOL_ANNOTATIONS["summarize_addm_db_schema_objects"],)
def summarize_addm_db_schema_objects(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    object_identifier: list[int] = Field(..., description='One or more unique Object id (from RDBMS)'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('summarize_addm_db_schema_objects', compartment_id=compartment_id, object_identifier=object_identifier, database_id=database_id, id=id, time_interval_start=time_interval_start, time_interval_end=time_interval_end, limit=limit, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_addm_db_sql_statements"],
    annotations=TOOL_ANNOTATIONS["summarize_addm_db_sql_statements"],)
def summarize_addm_db_sql_statements(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    sql_identifier: list[str] = Field(..., description='One or more unique SQL_IDs for a SQL Statement. Example: `6rgjh9bjmy2s7`'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('summarize_addm_db_sql_statements', compartment_id=compartment_id, sql_identifier=sql_identifier, database_id=database_id, id=id, time_interval_start=time_interval_start, time_interval_end=time_interval_end, limit=limit, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_database_cpu_usages"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_database_cpu_usages"],)
def summarize_awr_database_cpu_usages(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    begin_snapshot_identifier_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_snapshot_identifier_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot Identifier.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    session_type: str | None = Field(None, description='The optional query parameter to filter ASH activities by FOREGROUND or BACKGROUND. Allowed values are: "FOREGROUND", "BACKGROUND", "ALL"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The option to sort the AWR CPU usage summary data. Allowed values are: "TIME_SAMPLED", "AVG_VALUE"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('summarize_awr_database_cpu_usages', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, instance_number=instance_number, begin_snapshot_identifier_greater_than_or_equal_to=begin_snapshot_identifier_greater_than_or_equal_to, end_snapshot_identifier_less_than_or_equal_to=end_snapshot_identifier_less_than_or_equal_to, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, session_type=session_type, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_database_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_database_metrics"],)
def summarize_awr_database_metrics(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    name: list[str] = Field(..., description='The required multiple value query parameter to filter the entity name.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    begin_snapshot_identifier_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_snapshot_identifier_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot Identifier.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The option to sort the AWR time series summary data. Allowed values are: "TIMESTAMP", "NAME"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('summarize_awr_database_metrics', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, name=name, instance_number=instance_number, begin_snapshot_identifier_greater_than_or_equal_to=begin_snapshot_identifier_greater_than_or_equal_to, end_snapshot_identifier_less_than_or_equal_to=end_snapshot_identifier_less_than_or_equal_to, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_database_parameter_changes"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_database_parameter_changes"],)
def summarize_awr_database_parameter_changes(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    name: str = Field(..., description='The required single value query parameter to filter the entity name.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    begin_snapshot_identifier_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_snapshot_identifier_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot Identifier.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The option to sort the AWR database parameter change history data. Allowed values are: "IS_CHANGED", "NAME"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('summarize_awr_database_parameter_changes', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, name=name, instance_number=instance_number, begin_snapshot_identifier_greater_than_or_equal_to=begin_snapshot_identifier_greater_than_or_equal_to, end_snapshot_identifier_less_than_or_equal_to=end_snapshot_identifier_less_than_or_equal_to, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_database_parameters"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_database_parameters"],)
def summarize_awr_database_parameters(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    begin_snapshot_identifier_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_snapshot_identifier_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot Identifier.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    name: list[str] | None = Field(None, description='The optional multiple value query parameter to filter the entity name.'),
    name_contains: str | None = Field(None, description='The optional contains query parameter to filter the entity name by any part of the name.'),
    value_changed: str | None = Field(None, description='The optional query parameter to filter database parameters whose values were changed. Allowed values are: "Y", "N"'),
    value_default: str | None = Field(None, description='The optional query parameter to filter the database parameters that had the default value in the last snapshot. Allowed values are: "TRUE", "FALSE"'),
    value_modified: str | None = Field(None, description='The optional query parameter to filter the database parameters that had a modified value in the last snapshot. Allowed values are: "MODIFIED", "SYSTEM_MOD", "FALSE"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The option to sort the AWR database parameter change history data. Allowed values are: "IS_CHANGED", "NAME"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('summarize_awr_database_parameters', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, instance_number=instance_number, begin_snapshot_identifier_greater_than_or_equal_to=begin_snapshot_identifier_greater_than_or_equal_to, end_snapshot_identifier_less_than_or_equal_to=end_snapshot_identifier_less_than_or_equal_to, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, name=name, name_contains=name_contains, value_changed=value_changed, value_default=value_default, value_modified=value_modified, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_database_snapshot_ranges"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_database_snapshot_ranges"],)
def summarize_awr_database_snapshot_ranges(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    name: str | None = Field(None, description='The optional single value query parameter to filter the entity name.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The option to sort the AWR summary data. Allowed values are: "END_INTERVAL_TIME", "NAME"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('summarize_awr_database_snapshot_ranges', awr_hub_id=awr_hub_id, name=name, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_database_sysstats"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_database_sysstats"],)
def summarize_awr_database_sysstats(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    name: list[str] = Field(..., description='The required multiple value query parameter to filter the entity name.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    begin_snapshot_identifier_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_snapshot_identifier_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot Identifier.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The option to sort the data within a time period. Allowed values are: "TIME_BEGIN", "NAME"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('summarize_awr_database_sysstats', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, name=name, instance_number=instance_number, begin_snapshot_identifier_greater_than_or_equal_to=begin_snapshot_identifier_greater_than_or_equal_to, end_snapshot_identifier_less_than_or_equal_to=end_snapshot_identifier_less_than_or_equal_to, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_database_top_wait_events"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_database_top_wait_events"],)
def summarize_awr_database_top_wait_events(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    begin_snapshot_identifier_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_snapshot_identifier_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot Identifier.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    session_type: str | None = Field(None, description='The optional query parameter to filter ASH activities by FOREGROUND or BACKGROUND. Allowed values are: "FOREGROUND", "BACKGROUND", "ALL"'),
    top_n: int | None = Field(None, description='The optional query parameter to filter the number of top categories to be returned.'),
    sort_by: str | None = Field(None, description='The option to sort the AWR top event summary data. Allowed values are: "WAITS_PERSEC", "AVG_WAIT_TIME_PERSEC"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('summarize_awr_database_top_wait_events', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, instance_number=instance_number, begin_snapshot_identifier_greater_than_or_equal_to=begin_snapshot_identifier_greater_than_or_equal_to, end_snapshot_identifier_less_than_or_equal_to=end_snapshot_identifier_less_than_or_equal_to, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, session_type=session_type, top_n=top_n, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_database_wait_event_buckets"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_database_wait_event_buckets"],)
def summarize_awr_database_wait_event_buckets(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    name: str = Field(..., description='The required single value query parameter to filter the entity name.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    begin_snapshot_identifier_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_snapshot_identifier_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot Identifier.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    num_bucket: int | None = Field(None, description='The number of buckets within the histogram.'),
    min_value: float | None = Field(None, description='The minimum value of the histogram.'),
    max_value: float | None = Field(None, description='The maximum value of the histogram.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The option to sort distribution data. Allowed values are: "CATEGORY", "PERCENTAGE"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('summarize_awr_database_wait_event_buckets', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, name=name, instance_number=instance_number, begin_snapshot_identifier_greater_than_or_equal_to=begin_snapshot_identifier_greater_than_or_equal_to, end_snapshot_identifier_less_than_or_equal_to=end_snapshot_identifier_less_than_or_equal_to, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, num_bucket=num_bucket, min_value=min_value, max_value=max_value, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_database_wait_events"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_database_wait_events"],)
def summarize_awr_database_wait_events(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    awr_source_database_identifier: str = Field(..., description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.'),
    instance_number: str | None = Field(None, description='The optional single value query parameter to filter by database instance number.'),
    begin_snapshot_identifier_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_snapshot_identifier_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot Identifier.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. The timestamp format to be followed is: YYYY-MM-DDTHH:MM:SSZ, example 2020-12-03T19:00:53Z'),
    name: list[str] | None = Field(None, description='The optional multiple value query parameter to filter the entity name.'),
    session_type: str | None = Field(None, description='The optional query parameter to filter ASH activities by FOREGROUND or BACKGROUND. Allowed values are: "FOREGROUND", "BACKGROUND", "ALL"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The option to sort the data within a time period. Allowed values are: "TIME_BEGIN", "NAME"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('summarize_awr_database_wait_events', awr_hub_id=awr_hub_id, awr_source_database_identifier=awr_source_database_identifier, instance_number=instance_number, begin_snapshot_identifier_greater_than_or_equal_to=begin_snapshot_identifier_greater_than_or_equal_to, end_snapshot_identifier_less_than_or_equal_to=end_snapshot_identifier_less_than_or_equal_to, time_greater_than_or_equal_to=time_greater_than_or_equal_to, time_less_than_or_equal_to=time_less_than_or_equal_to, name=name, session_type=session_type, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_sources_summaries"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_sources_summaries"],)
def summarize_awr_sources_summaries(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    name: str | None = Field(None, description='Name for an Awr source database'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: str | None = Field(None, description='The order in which Awr sources summary records are listed Allowed values are: "snapshotsUploaded", "name"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_opsi('summarize_awr_sources_summaries', awr_hub_id=awr_hub_id, compartment_id=compartment_id, name=name, limit=limit, sort_by=sort_by, sort_order=sort_order)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_configuration_items"],
    annotations=TOOL_ANNOTATIONS["summarize_configuration_items"],)
def summarize_configuration_items(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    opsi_config_type: str | None = Field(None, description='Filter to return configuration items based on configuration type of OPSI configuration. Allowed values are: "UX_CONFIGURATION"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    config_items_applicable_context: list[str] | None = Field(None, description='Returns the configuration items filtered by applicable contexts sent in this param. By default configuration items of all applicable contexts are returned.'),
    config_item_field: list[str] | None = Field(None, description='Specifies the fields to return in a config item summary. Allowed values are: "name", "value", "defaultValue", "valueSourceConfig", "metadata", "applicableContexts"'),
    name: str | None = Field(None, description='A filter to return only configuration items that match the entire name.'),) -> Any:
    return invoke_opsi('summarize_configuration_items', compartment_id=compartment_id, opsi_config_type=opsi_config_type, limit=limit, config_items_applicable_context=config_items_applicable_context, config_item_field=config_item_field, name=name)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_database_insight_resource_capacity_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_database_insight_resource_capacity_trend"],)
def summarize_database_insight_resource_capacity_trend(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY and IO.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    database_type: list[str] | None = Field(None, description='Filter by one or more database type. Possible values are ADW-S, ATP-S, ADW-D, ATP-D, EXTERNAL-PDB, EXTERNAL-NONCDB. Allowed values are: "ADW-S", "ATP-S", "ADW-D", "ATP-D", "EXTERNAL-PDB", "EXTERNAL-NONCDB", "COMANAGED-VM-CDB", "COMANAGED-VM-PDB", "COMANAGED-VM-NONCDB", "COMANAGED-BM-CDB", "COMANAGED-BM-PDB", "COMANAGED-BM-NONCDB", "COMANAGED-EXACS-CDB", "COMANAGED-EXACS-PDB", "COMANAGED-EXACS-NONCDB", "COMANAGED-EXACC-CDB", "COMANAGED-EXACC-PDB", "COMANAGED-EXACC-NONCDB", "MDS-MYSQL", "EXTERNAL-MYSQL", "ATP-EXACC", "ADW-EXACC", "EXTERNAL-ADW", "EXTERNAL-ATP", "LH-D", "APEX-D", "AJD-D", "AVD-D", "LH-S", "APEX-S", "AJD-S", "AVD-S", "LH-EXACC", "APEX-EXACC", "AJD-EXACC", "AVD-EXACC"'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    utilization_level: str | None = Field(None, description='Filter by utilization level by the following buckets: - HIGH_UTILIZATION: DBs with utilization greater or equal than 75. - LOW_UTILIZATION: DBs with utilization lower than 25. - MEDIUM_HIGH_UTILIZATION: DBs with utilization greater or equal than 50 but lower than 75. - MEDIUM_LOW_UTILIZATION: DBs with utilization greater or equal than 25 but lower than 50. Allowed values are: "HIGH_UTILIZATION", "LOW_UTILIZATION", "MEDIUM_HIGH_UTILIZATION", "MEDIUM_LOW_UTILIZATION"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Sorts using end timestamp, capacity or baseCapacity Allowed values are: "endTimestamp", "capacity", "baseCapacity"'),
    tablespace_name: str | None = Field(None, description='Tablespace name for a database'),
    host_name: list[str] | None = Field(None, description='Filter by one or more hostname.'),
    is_database_instance_level_metrics: bool | None = Field(None, description='Flag to indicate if database instance level metrics should be returned. The flag is ignored when a host name filter is not applied. When a hostname filter is applied this flag will determine whether to return metrics for the instances located on the specified host or for the whole database which contains an instance on this host.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    high_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered highly utilized.'),
    low_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered low utilized.'),) -> Any:
    return invoke_opsi('summarize_database_insight_resource_capacity_trend', compartment_id=compartment_id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, database_type=database_type, database_id=database_id, id=id, exadata_insight_id=exadata_insight_id, cdb_name=cdb_name, utilization_level=utilization_level, sort_order=sort_order, sort_by=sort_by, tablespace_name=tablespace_name, host_name=host_name, is_database_instance_level_metrics=is_database_instance_level_metrics, compartment_id_in_subtree=compartment_id_in_subtree, vmcluster_name=vmcluster_name, high_utilization_threshold=high_utilization_threshold, low_utilization_threshold=low_utilization_threshold)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_database_insight_resource_forecast_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_database_insight_resource_forecast_trend"],)
def summarize_database_insight_resource_forecast_trend(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY and IO.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    database_type: list[str] | None = Field(None, description='Filter by one or more database type. Possible values are ADW-S, ATP-S, ADW-D, ATP-D, EXTERNAL-PDB, EXTERNAL-NONCDB. Allowed values are: "ADW-S", "ATP-S", "ADW-D", "ATP-D", "EXTERNAL-PDB", "EXTERNAL-NONCDB", "COMANAGED-VM-CDB", "COMANAGED-VM-PDB", "COMANAGED-VM-NONCDB", "COMANAGED-BM-CDB", "COMANAGED-BM-PDB", "COMANAGED-BM-NONCDB", "COMANAGED-EXACS-CDB", "COMANAGED-EXACS-PDB", "COMANAGED-EXACS-NONCDB", "COMANAGED-EXACC-CDB", "COMANAGED-EXACC-PDB", "COMANAGED-EXACC-NONCDB", "MDS-MYSQL", "EXTERNAL-MYSQL", "ATP-EXACC", "ADW-EXACC", "EXTERNAL-ADW", "EXTERNAL-ATP", "LH-D", "APEX-D", "AJD-D", "AVD-D", "LH-S", "APEX-S", "AJD-S", "AVD-S", "LH-EXACC", "APEX-EXACC", "AJD-EXACC", "AVD-EXACC"'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    statistic: str | None = Field(None, description='Choose the type of statistic metric data to be used for forecasting. Allowed values are: "AVG", "MAX"'),
    forecast_days: int | None = Field(None, description='Number of days used for utilization forecast analysis.'),
    forecast_model: str | None = Field(None, description='Choose algorithm model for the forecasting. Possible values: - LINEAR: Uses linear regression algorithm for forecasting. - ML_AUTO: Automatically detects best algorithm to use for forecasting. - ML_NO_AUTO: Automatically detects seasonality of the data for forecasting using linear or seasonal algorithm. Allowed values are: "LINEAR", "ML_AUTO", "ML_NO_AUTO"'),
    utilization_level: str | None = Field(None, description='Filter by utilization level by the following buckets: - HIGH_UTILIZATION: DBs with utilization greater or equal than 75. - LOW_UTILIZATION: DBs with utilization lower than 25. - MEDIUM_HIGH_UTILIZATION: DBs with utilization greater or equal than 50 but lower than 75. - MEDIUM_LOW_UTILIZATION: DBs with utilization greater or equal than 25 but lower than 50. Allowed values are: "HIGH_UTILIZATION", "LOW_UTILIZATION", "MEDIUM_HIGH_UTILIZATION", "MEDIUM_LOW_UTILIZATION"'),
    confidence: int | None = Field(None, description="This parameter is used to change data's confidence level, this data is ingested by the forecast algorithm. Confidence is the probability of an interval to contain the expected population parameter. Manipulation of this value will lead to different results. If not set, default confidence value is 95%."),
    host_name: list[str] | None = Field(None, description='Filter by one or more hostname.'),
    tablespace_name: str | None = Field(None, description='Tablespace name for a database'),
    is_database_instance_level_metrics: bool | None = Field(None, description='Flag to indicate if database instance level metrics should be returned. The flag is ignored when a host name filter is not applied. When a hostname filter is applied this flag will determine whether to return metrics for the instances located on the specified host or for the whole database which contains an instance on this host.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    high_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered highly utilized.'),
    low_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered low utilized.'),) -> Any:
    return invoke_opsi('summarize_database_insight_resource_forecast_trend', compartment_id=compartment_id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, database_type=database_type, database_id=database_id, id=id, exadata_insight_id=exadata_insight_id, cdb_name=cdb_name, statistic=statistic, forecast_days=forecast_days, forecast_model=forecast_model, utilization_level=utilization_level, confidence=confidence, host_name=host_name, tablespace_name=tablespace_name, is_database_instance_level_metrics=is_database_instance_level_metrics, compartment_id_in_subtree=compartment_id_in_subtree, vmcluster_name=vmcluster_name, high_utilization_threshold=high_utilization_threshold, low_utilization_threshold=low_utilization_threshold)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_database_insight_resource_statistics"],
    annotations=TOOL_ANNOTATIONS["summarize_database_insight_resource_statistics"],)
def summarize_database_insight_resource_statistics(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY and IO.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    database_type: list[str] | None = Field(None, description='Filter by one or more database type. Possible values are ADW-S, ATP-S, ADW-D, ATP-D, EXTERNAL-PDB, EXTERNAL-NONCDB. Allowed values are: "ADW-S", "ATP-S", "ADW-D", "ATP-D", "EXTERNAL-PDB", "EXTERNAL-NONCDB", "COMANAGED-VM-CDB", "COMANAGED-VM-PDB", "COMANAGED-VM-NONCDB", "COMANAGED-BM-CDB", "COMANAGED-BM-PDB", "COMANAGED-BM-NONCDB", "COMANAGED-EXACS-CDB", "COMANAGED-EXACS-PDB", "COMANAGED-EXACS-NONCDB", "COMANAGED-EXACC-CDB", "COMANAGED-EXACC-PDB", "COMANAGED-EXACC-NONCDB", "MDS-MYSQL", "EXTERNAL-MYSQL", "ATP-EXACC", "ADW-EXACC", "EXTERNAL-ADW", "EXTERNAL-ATP", "LH-D", "APEX-D", "AJD-D", "AVD-D", "LH-S", "APEX-S", "AJD-S", "AVD-S", "LH-EXACC", "APEX-EXACC", "AJD-EXACC", "AVD-EXACC"'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    percentile: int | None = Field(None, description='Percentile values of daily usage to be used for computing the aggregate resource usage.'),
    insight_by: str | None = Field(None, description='Return data of a specific insight Possible values are High Utilization, Low Utilization, Any,High Utilization Forecast, Low Utilization Forecast'),
    forecast_days: int | None = Field(None, description='Number of days used for utilization forecast analysis.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The order in which resource statistics records are listed Allowed values are: "utilizationPercent", "usage", "usageChangePercent", "databaseName", "databaseType"'),
    host_name: list[str] | None = Field(None, description='Filter by one or more hostname.'),
    is_database_instance_level_metrics: bool | None = Field(None, description='Flag to indicate if database instance level metrics should be returned. The flag is ignored when a host name filter is not applied. When a hostname filter is applied this flag will determine whether to return metrics for the instances located on the specified host or for the whole database which contains an instance on this host.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    high_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered highly utilized.'),
    low_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered low utilized.'),) -> Any:
    return invoke_opsi('summarize_database_insight_resource_statistics', compartment_id=compartment_id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, database_type=database_type, database_id=database_id, id=id, exadata_insight_id=exadata_insight_id, cdb_name=cdb_name, percentile=percentile, insight_by=insight_by, forecast_days=forecast_days, limit=limit, sort_order=sort_order, sort_by=sort_by, host_name=host_name, is_database_instance_level_metrics=is_database_instance_level_metrics, compartment_id_in_subtree=compartment_id_in_subtree, vmcluster_name=vmcluster_name, high_utilization_threshold=high_utilization_threshold, low_utilization_threshold=low_utilization_threshold)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_database_insight_resource_usage"],
    annotations=TOOL_ANNOTATIONS["summarize_database_insight_resource_usage"],)
def summarize_database_insight_resource_usage(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY and IO.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    database_type: list[str] | None = Field(None, description='Filter by one or more database type. Possible values are ADW-S, ATP-S, ADW-D, ATP-D, EXTERNAL-PDB, EXTERNAL-NONCDB. Allowed values are: "ADW-S", "ATP-S", "ADW-D", "ATP-D", "EXTERNAL-PDB", "EXTERNAL-NONCDB", "COMANAGED-VM-CDB", "COMANAGED-VM-PDB", "COMANAGED-VM-NONCDB", "COMANAGED-BM-CDB", "COMANAGED-BM-PDB", "COMANAGED-BM-NONCDB", "COMANAGED-EXACS-CDB", "COMANAGED-EXACS-PDB", "COMANAGED-EXACS-NONCDB", "COMANAGED-EXACC-CDB", "COMANAGED-EXACC-PDB", "COMANAGED-EXACC-NONCDB", "MDS-MYSQL", "EXTERNAL-MYSQL", "ATP-EXACC", "ADW-EXACC", "EXTERNAL-ADW", "EXTERNAL-ATP", "LH-D", "APEX-D", "AJD-D", "AVD-D", "LH-S", "APEX-S", "AJD-S", "AVD-S", "LH-EXACC", "APEX-EXACC", "AJD-EXACC", "AVD-EXACC"'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    host_name: list[str] | None = Field(None, description='Filter by one or more hostname.'),
    is_database_instance_level_metrics: bool | None = Field(None, description='Flag to indicate if database instance level metrics should be returned. The flag is ignored when a host name filter is not applied. When a hostname filter is applied this flag will determine whether to return metrics for the instances located on the specified host or for the whole database which contains an instance on this host.'),
    percentile: int | None = Field(None, description='Percentile values of daily usage to be used for computing the aggregate resource usage.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),) -> Any:
    return invoke_opsi('summarize_database_insight_resource_usage', compartment_id=compartment_id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, database_type=database_type, database_id=database_id, id=id, exadata_insight_id=exadata_insight_id, host_name=host_name, is_database_instance_level_metrics=is_database_instance_level_metrics, percentile=percentile, compartment_id_in_subtree=compartment_id_in_subtree, vmcluster_name=vmcluster_name, cdb_name=cdb_name)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_database_insight_resource_usage_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_database_insight_resource_usage_trend"],)
def summarize_database_insight_resource_usage_trend(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY and IO.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    database_type: list[str] | None = Field(None, description='Filter by one or more database type. Possible values are ADW-S, ATP-S, ADW-D, ATP-D, EXTERNAL-PDB, EXTERNAL-NONCDB. Allowed values are: "ADW-S", "ATP-S", "ADW-D", "ATP-D", "EXTERNAL-PDB", "EXTERNAL-NONCDB", "COMANAGED-VM-CDB", "COMANAGED-VM-PDB", "COMANAGED-VM-NONCDB", "COMANAGED-BM-CDB", "COMANAGED-BM-PDB", "COMANAGED-BM-NONCDB", "COMANAGED-EXACS-CDB", "COMANAGED-EXACS-PDB", "COMANAGED-EXACS-NONCDB", "COMANAGED-EXACC-CDB", "COMANAGED-EXACC-PDB", "COMANAGED-EXACC-NONCDB", "MDS-MYSQL", "EXTERNAL-MYSQL", "ATP-EXACC", "ADW-EXACC", "EXTERNAL-ADW", "EXTERNAL-ATP", "LH-D", "APEX-D", "AJD-D", "AVD-D", "LH-S", "APEX-S", "AJD-S", "AVD-S", "LH-EXACC", "APEX-EXACC", "AJD-EXACC", "AVD-EXACC"'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Sorts using end timestamp, usage or capacity Allowed values are: "endTimestamp", "usage", "capacity"'),
    host_name: list[str] | None = Field(None, description='Filter by one or more hostname.'),
    is_database_instance_level_metrics: bool | None = Field(None, description='Flag to indicate if database instance level metrics should be returned. The flag is ignored when a host name filter is not applied. When a hostname filter is applied this flag will determine whether to return metrics for the instances located on the specified host or for the whole database which contains an instance on this host.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),) -> Any:
    return invoke_opsi('summarize_database_insight_resource_usage_trend', compartment_id=compartment_id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, database_type=database_type, database_id=database_id, id=id, exadata_insight_id=exadata_insight_id, sort_order=sort_order, sort_by=sort_by, host_name=host_name, is_database_instance_level_metrics=is_database_instance_level_metrics, compartment_id_in_subtree=compartment_id_in_subtree, vmcluster_name=vmcluster_name, cdb_name=cdb_name)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_database_insight_resource_utilization_insight"],
    annotations=TOOL_ANNOTATIONS["summarize_database_insight_resource_utilization_insight"],)
def summarize_database_insight_resource_utilization_insight(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY and IO.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    database_type: list[str] | None = Field(None, description='Filter by one or more database type. Possible values are ADW-S, ATP-S, ADW-D, ATP-D, EXTERNAL-PDB, EXTERNAL-NONCDB. Allowed values are: "ADW-S", "ATP-S", "ADW-D", "ATP-D", "EXTERNAL-PDB", "EXTERNAL-NONCDB", "COMANAGED-VM-CDB", "COMANAGED-VM-PDB", "COMANAGED-VM-NONCDB", "COMANAGED-BM-CDB", "COMANAGED-BM-PDB", "COMANAGED-BM-NONCDB", "COMANAGED-EXACS-CDB", "COMANAGED-EXACS-PDB", "COMANAGED-EXACS-NONCDB", "COMANAGED-EXACC-CDB", "COMANAGED-EXACC-PDB", "COMANAGED-EXACC-NONCDB", "MDS-MYSQL", "EXTERNAL-MYSQL", "ATP-EXACC", "ADW-EXACC", "EXTERNAL-ADW", "EXTERNAL-ATP", "LH-D", "APEX-D", "AJD-D", "AVD-D", "LH-S", "APEX-S", "AJD-S", "AVD-S", "LH-EXACC", "APEX-EXACC", "AJD-EXACC", "AVD-EXACC"'),
    database_id: list[str] | None = Field(None, description='Optional list of database OCIDs of the associated DBaaS entity.'),
    id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    forecast_days: int | None = Field(None, description='Number of days used for utilization forecast analysis.'),
    host_name: list[str] | None = Field(None, description='Filter by one or more hostname.'),
    is_database_instance_level_metrics: bool | None = Field(None, description='Flag to indicate if database instance level metrics should be returned. The flag is ignored when a host name filter is not applied. When a hostname filter is applied this flag will determine whether to return metrics for the instances located on the specified host or for the whole database which contains an instance on this host.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    high_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered highly utilized.'),
    low_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered low utilized.'),) -> Any:
    return invoke_opsi('summarize_database_insight_resource_utilization_insight', compartment_id=compartment_id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, database_type=database_type, database_id=database_id, id=id, exadata_insight_id=exadata_insight_id, forecast_days=forecast_days, host_name=host_name, is_database_instance_level_metrics=is_database_instance_level_metrics, compartment_id_in_subtree=compartment_id_in_subtree, vmcluster_name=vmcluster_name, cdb_name=cdb_name, high_utilization_threshold=high_utilization_threshold, low_utilization_threshold=low_utilization_threshold)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_database_insight_tablespace_usage_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_database_insight_tablespace_usage_trend"],)
def summarize_database_insight_tablespace_usage_trend(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    database_id: str | None = Field(None, description='Optional OCID of the associated DBaaS entity.'),
    id: str | None = Field(None, description='OCID of the database insight resource.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),) -> Any:
    return invoke_opsi('summarize_database_insight_tablespace_usage_trend', compartment_id=compartment_id, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, database_id=database_id, id=id, limit=limit)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_exadata_insight_resource_capacity_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_exadata_insight_resource_capacity_trend"],)
def summarize_exadata_insight_resource_capacity_trend(
    resource_type: str = Field(..., description='Filter by resource. Supported values are HOST, STORAGE_SERVER and DATABASE'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY, IO, IOPS, THROUGHPUT'),
    exadata_insight_id: str = Field(..., description='OCID of exadata insight resource.'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    database_insight_id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    host_insight_id: list[str] | None = Field(None, description='Optional list of host insight resource OCIDs.'),
    storage_server_name: list[str] | None = Field(None, description='Optional storage server name on an exadata system.'),
    exadata_type: list[str] | None = Field(None, description='Filter by one or more Exadata types. Possible value are DBMACHINE, EXACS, and EXACC.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    host_name: list[str] | None = Field(None, description='Filter by hostname.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The order in which resource capacity trend records are listed Allowed values are: "id", "name"'),) -> Any:
    return invoke_opsi('summarize_exadata_insight_resource_capacity_trend', resource_type=resource_type, resource_metric=resource_metric, exadata_insight_id=exadata_insight_id, compartment_id=compartment_id, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, database_insight_id=database_insight_id, host_insight_id=host_insight_id, storage_server_name=storage_server_name, exadata_type=exadata_type, cdb_name=cdb_name, host_name=host_name, limit=limit, sort_order=sort_order, sort_by=sort_by)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_exadata_insight_resource_capacity_trend_aggregated"],
    annotations=TOOL_ANNOTATIONS["summarize_exadata_insight_resource_capacity_trend_aggregated"],)
def summarize_exadata_insight_resource_capacity_trend_aggregated(
    resource_type: str = Field(..., description='Filter by resource. Supported values are HOST, STORAGE_SERVER and DATABASE'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY, IO, IOPS, THROUGHPUT'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    exadata_type: list[str] | None = Field(None, description='Filter by one or more Exadata types. Possible value are DBMACHINE, EXACS, and EXACC.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    host_name: list[str] | None = Field(None, description='Filter by hostname.'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Sorts using end timestamp or capacity. Allowed values are: "endTimestamp", "capacity"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('summarize_exadata_insight_resource_capacity_trend_aggregated', resource_type=resource_type, resource_metric=resource_metric, compartment_id=compartment_id, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, exadata_insight_id=exadata_insight_id, exadata_type=exadata_type, cdb_name=cdb_name, host_name=host_name, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_exadata_insight_resource_forecast_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_exadata_insight_resource_forecast_trend"],)
def summarize_exadata_insight_resource_forecast_trend(
    resource_type: str = Field(..., description='Filter by resource. Supported values are HOST, STORAGE_SERVER and DATABASE'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY, IO, IOPS, THROUGHPUT'),
    exadata_insight_id: str = Field(..., description='OCID of exadata insight resource.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    database_insight_id: list[str] | None = Field(None, description='Optional list of database insight resource OCIDs.'),
    host_insight_id: list[str] | None = Field(None, description='Optional list of host insight resource OCIDs.'),
    storage_server_name: list[str] | None = Field(None, description='Optional storage server name on an exadata system.'),
    exadata_type: list[str] | None = Field(None, description='Filter by one or more Exadata types. Possible value are DBMACHINE, EXACS, and EXACC.'),
    statistic: str | None = Field(None, description='Choose the type of statistic metric data to be used for forecasting. Allowed values are: "AVG", "MAX"'),
    forecast_start_day: int | None = Field(None, description='Number of days used for utilization forecast analysis.'),
    forecast_days: int | None = Field(None, description='Number of days used for utilization forecast analysis.'),
    forecast_model: str | None = Field(None, description='Choose algorithm model for the forecasting. Possible values: - LINEAR: Uses linear regression algorithm for forecasting. - ML_AUTO: Automatically detects best algorithm to use for forecasting. - ML_NO_AUTO: Automatically detects seasonality of the data for forecasting using linear or seasonal algorithm. Allowed values are: "LINEAR", "ML_AUTO", "ML_NO_AUTO"'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    host_name: list[str] | None = Field(None, description='Filter by hostname.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    confidence: int | None = Field(None, description="This parameter is used to change data's confidence level, this data is ingested by the forecast algorithm. Confidence is the probability of an interval to contain the expected population parameter. Manipulation of this value will lead to different results. If not set, default confidence value is 95%."),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The order in which resource Forecast trend records are listed Allowed values are: "id", "name", "daysToReachCapacity"'),) -> Any:
    return invoke_opsi('summarize_exadata_insight_resource_forecast_trend', resource_type=resource_type, resource_metric=resource_metric, exadata_insight_id=exadata_insight_id, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, database_insight_id=database_insight_id, host_insight_id=host_insight_id, storage_server_name=storage_server_name, exadata_type=exadata_type, statistic=statistic, forecast_start_day=forecast_start_day, forecast_days=forecast_days, forecast_model=forecast_model, cdb_name=cdb_name, host_name=host_name, limit=limit, confidence=confidence, sort_order=sort_order, sort_by=sort_by)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_exadata_insight_resource_forecast_trend_aggregated"],
    annotations=TOOL_ANNOTATIONS["summarize_exadata_insight_resource_forecast_trend_aggregated"],)
def summarize_exadata_insight_resource_forecast_trend_aggregated(
    resource_type: str = Field(..., description='Filter by resource. Supported values are HOST, STORAGE_SERVER and DATABASE'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY, IO, IOPS, THROUGHPUT'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    exadata_type: list[str] | None = Field(None, description='Filter by one or more Exadata types. Possible value are DBMACHINE, EXACS, and EXACC.'),
    statistic: str | None = Field(None, description='Choose the type of statistic metric data to be used for forecasting. Allowed values are: "AVG", "MAX"'),
    forecast_start_day: int | None = Field(None, description='Number of days used for utilization forecast analysis.'),
    forecast_days: int | None = Field(None, description='Number of days used for utilization forecast analysis.'),
    forecast_model: str | None = Field(None, description='Choose algorithm model for the forecasting. Possible values: - LINEAR: Uses linear regression algorithm for forecasting. - ML_AUTO: Automatically detects best algorithm to use for forecasting. - ML_NO_AUTO: Automatically detects seasonality of the data for forecasting using linear or seasonal algorithm. Allowed values are: "LINEAR", "ML_AUTO", "ML_NO_AUTO"'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    host_name: list[str] | None = Field(None, description='Filter by hostname.'),
    confidence: int | None = Field(None, description="This parameter is used to change data's confidence level, this data is ingested by the forecast algorithm. Confidence is the probability of an interval to contain the expected population parameter. Manipulation of this value will lead to different results. If not set, default confidence value is 95%."),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('summarize_exadata_insight_resource_forecast_trend_aggregated', resource_type=resource_type, resource_metric=resource_metric, compartment_id=compartment_id, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, exadata_insight_id=exadata_insight_id, exadata_type=exadata_type, statistic=statistic, forecast_start_day=forecast_start_day, forecast_days=forecast_days, forecast_model=forecast_model, cdb_name=cdb_name, host_name=host_name, confidence=confidence, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_exadata_insight_resource_statistics"],
    annotations=TOOL_ANNOTATIONS["summarize_exadata_insight_resource_statistics"],)
def summarize_exadata_insight_resource_statistics(
    exadata_insight_id: str = Field(..., description='OCID of exadata insight resource.'),
    resource_type: str = Field(..., description='Filter by resource. Supported values are HOST, STORAGE_SERVER and DATABASE'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY, IO, IOPS, THROUGHPUT'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    exadata_type: list[str] | None = Field(None, description='Filter by one or more Exadata types. Possible value are DBMACHINE, EXACS, and EXACC.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    host_name: list[str] | None = Field(None, description='Filter by hostname.'),
    percentile: int | None = Field(None, description='Percentile values of daily usage to be used for computing the aggregate resource usage.'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The order in which resource statistics records are listed Allowed values are: "utilizationPercent", "usage", "usageChangePercent"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),) -> Any:
    return invoke_opsi('summarize_exadata_insight_resource_statistics', exadata_insight_id=exadata_insight_id, resource_type=resource_type, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, exadata_type=exadata_type, cdb_name=cdb_name, host_name=host_name, percentile=percentile, sort_order=sort_order, sort_by=sort_by, limit=limit)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_exadata_insight_resource_usage"],
    annotations=TOOL_ANNOTATIONS["summarize_exadata_insight_resource_usage"],)
def summarize_exadata_insight_resource_usage(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_type: str = Field(..., description='Filter by resource. Supported values are HOST, STORAGE_SERVER and DATABASE'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY, IO, IOPS, THROUGHPUT'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    exadata_type: list[str] | None = Field(None, description='Filter by one or more Exadata types. Possible value are DBMACHINE, EXACS, and EXACC.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    host_name: list[str] | None = Field(None, description='Filter by hostname.'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The order in which resource usage summary records are listed Allowed values are: "utilizationPercent", "usage", "capacity", "usageChangePercent"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    percentile: int | None = Field(None, description='Percentile values of daily usage to be used for computing the aggregate resource usage.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('summarize_exadata_insight_resource_usage', compartment_id=compartment_id, resource_type=resource_type, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, exadata_insight_id=exadata_insight_id, exadata_type=exadata_type, cdb_name=cdb_name, host_name=host_name, sort_order=sort_order, sort_by=sort_by, limit=limit, percentile=percentile, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_exadata_insight_resource_usage_aggregated"],
    annotations=TOOL_ANNOTATIONS["summarize_exadata_insight_resource_usage_aggregated"],)
def summarize_exadata_insight_resource_usage_aggregated(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_type: str = Field(..., description='Filter by resource. Supported values are HOST, STORAGE_SERVER and DATABASE'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY, IO, IOPS, THROUGHPUT'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    exadata_type: list[str] | None = Field(None, description='Filter by one or more Exadata types. Possible value are DBMACHINE, EXACS, and EXACC.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    host_name: list[str] | None = Field(None, description='Filter by hostname.'),
    percentile: int | None = Field(None, description='Percentile values of daily usage to be used for computing the aggregate resource usage.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),) -> Any:
    return invoke_opsi('summarize_exadata_insight_resource_usage_aggregated', compartment_id=compartment_id, resource_type=resource_type, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, exadata_insight_id=exadata_insight_id, exadata_type=exadata_type, cdb_name=cdb_name, host_name=host_name, percentile=percentile, compartment_id_in_subtree=compartment_id_in_subtree)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_exadata_insight_resource_utilization_insight"],
    annotations=TOOL_ANNOTATIONS["summarize_exadata_insight_resource_utilization_insight"],)
def summarize_exadata_insight_resource_utilization_insight(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_type: str = Field(..., description='Filter by resource. Supported values are HOST, STORAGE_SERVER and DATABASE'),
    resource_metric: str = Field(..., description='Filter by resource metric. Supported values are CPU, STORAGE, MEMORY, IO, IOPS, THROUGHPUT'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    exadata_type: list[str] | None = Field(None, description='Filter by one or more Exadata types. Possible value are DBMACHINE, EXACS, and EXACC.'),
    forecast_start_day: int | None = Field(None, description='Number of days used for utilization forecast analysis.'),
    forecast_days: int | None = Field(None, description='Number of days used for utilization forecast analysis.'),
    cdb_name: list[str] | None = Field(None, description='Filter by one or more cdb name.'),
    host_name: list[str] | None = Field(None, description='Filter by hostname.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    high_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered highly utilized.'),
    low_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered low utilized.'),) -> Any:
    return invoke_opsi('summarize_exadata_insight_resource_utilization_insight', compartment_id=compartment_id, resource_type=resource_type, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, exadata_insight_id=exadata_insight_id, exadata_type=exadata_type, forecast_start_day=forecast_start_day, forecast_days=forecast_days, cdb_name=cdb_name, host_name=host_name, limit=limit, compartment_id_in_subtree=compartment_id_in_subtree, high_utilization_threshold=high_utilization_threshold, low_utilization_threshold=low_utilization_threshold)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_exadata_members"],
    annotations=TOOL_ANNOTATIONS["summarize_exadata_members"],)
def summarize_exadata_members(
    exadata_insight_id: str = Field(..., description='OCID of exadata insight resource.'),
    exadata_type: list[str] | None = Field(None, description='Filter by one or more Exadata types. Possible value are DBMACHINE, EXACS, and EXACC.'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The order in which exadata member records are listed Allowed values are: "name", "displayName", "entityType"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),) -> Any:
    return invoke_opsi('summarize_exadata_members', exadata_insight_id=exadata_insight_id, exadata_type=exadata_type, sort_order=sort_order, sort_by=sort_by, limit=limit)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_disk_statistics"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_disk_statistics"],)
def summarize_host_insight_disk_statistics(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str = Field(..., description='Required OCID of the host insight resource.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    statistic: str | None = Field(None, description='Choose the type of statistic metric data to be used for forecasting. Allowed values are: "AVG", "MAX"'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('summarize_host_insight_disk_statistics', compartment_id=compartment_id, id=id, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, host_id=host_id, statistic=statistic, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_host_recommendation"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_host_recommendation"],)
def summarize_host_insight_host_recommendation(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str = Field(..., description='Required OCID of the host insight resource.'),
    resource_metric: str = Field(..., description='Filter by host resource metric. Supported values are CPU, MEMORY, LOGICAL_MEMORY, STORAGE and NETWORK.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    statistic: str | None = Field(None, description='Choose the type of statistic metric data to be used for forecasting. Allowed values are: "AVG", "MAX"'),) -> Any:
    return invoke_opsi('summarize_host_insight_host_recommendation', compartment_id=compartment_id, id=id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, host_id=host_id, limit=limit, statistic=statistic)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_io_usage_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_io_usage_trend"],)
def summarize_host_insight_io_usage_trend(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str = Field(..., description='Required OCID of the host insight resource.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    statistic: str | None = Field(None, description='Choose the type of statistic metric data to be used for forecasting. Allowed values are: "AVG", "MAX"'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('summarize_host_insight_io_usage_trend', compartment_id=compartment_id, id=id, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, host_id=host_id, limit=limit, statistic=statistic, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_network_usage_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_network_usage_trend"],)
def summarize_host_insight_network_usage_trend(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str = Field(..., description='Required OCID of the host insight resource.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    statistic: str | None = Field(None, description='Choose the type of statistic metric data to be used for forecasting. Allowed values are: "AVG", "MAX"'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('summarize_host_insight_network_usage_trend', compartment_id=compartment_id, id=id, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, host_id=host_id, limit=limit, statistic=statistic, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_resource_capacity_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_resource_capacity_trend"],)
def summarize_host_insight_resource_capacity_trend(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_metric: str = Field(..., description='Filter by host resource metric. Supported values are CPU, MEMORY, LOGICAL_MEMORY, STORAGE and NETWORK.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    platform_type: list[str] | None = Field(None, description='Filter by one or more platform types. Supported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS]. Supported platformType(s) for MACS-managed cloud host insight: [LINUX]. Supported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX]. Allowed values are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX"'),
    id: list[str] | None = Field(None, description='Optional list of host insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    utilization_level: str | None = Field(None, description='Filter by utilization level by the following buckets: - HIGH_UTILIZATION: DBs with utilization greater or equal than 75. - LOW_UTILIZATION: DBs with utilization lower than 25. - MEDIUM_HIGH_UTILIZATION: DBs with utilization greater or equal than 50 but lower than 75. - MEDIUM_LOW_UTILIZATION: DBs with utilization greater or equal than 25 but lower than 50. Allowed values are: "HIGH_UTILIZATION", "LOW_UTILIZATION", "MEDIUM_HIGH_UTILIZATION", "MEDIUM_LOW_UTILIZATION"'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Sorts using end timestamp or capacity Allowed values are: "endTimestamp", "capacity"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    host_type: list[str] | None = Field(None, description='Filter by one or more host types. Possible values are CLOUD-HOST, EXTERNAL-HOST, COMANAGED-VM-HOST, COMANAGED-BM-HOST, COMANAGED-EXACS-HOST, COMANAGED-EXACC-HOST'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    high_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered highly utilized.'),
    low_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered low utilized.'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('summarize_host_insight_resource_capacity_trend', compartment_id=compartment_id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, platform_type=platform_type, id=id, exadata_insight_id=exadata_insight_id, utilization_level=utilization_level, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree, host_type=host_type, host_id=host_id, vmcluster_name=vmcluster_name, high_utilization_threshold=high_utilization_threshold, low_utilization_threshold=low_utilization_threshold, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_resource_forecast_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_resource_forecast_trend"],)
def summarize_host_insight_resource_forecast_trend(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_metric: str = Field(..., description='Filter by host resource metric. Supported values are CPU, MEMORY, LOGICAL_MEMORY, STORAGE and NETWORK.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    platform_type: list[str] | None = Field(None, description='Filter by one or more platform types. Supported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS]. Supported platformType(s) for MACS-managed cloud host insight: [LINUX]. Supported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX]. Allowed values are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX"'),
    id: list[str] | None = Field(None, description='Optional list of host insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    statistic: str | None = Field(None, description='Choose the type of statistic metric data to be used for forecasting. Allowed values are: "AVG", "MAX"'),
    forecast_days: int | None = Field(None, description='Number of days used for utilization forecast analysis.'),
    forecast_model: str | None = Field(None, description='Choose algorithm model for the forecasting. Possible values: - LINEAR: Uses linear regression algorithm for forecasting. - ML_AUTO: Automatically detects best algorithm to use for forecasting. - ML_NO_AUTO: Automatically detects seasonality of the data for forecasting using linear or seasonal algorithm. Allowed values are: "LINEAR", "ML_AUTO", "ML_NO_AUTO"'),
    utilization_level: str | None = Field(None, description='Filter by utilization level by the following buckets: - HIGH_UTILIZATION: DBs with utilization greater or equal than 75. - LOW_UTILIZATION: DBs with utilization lower than 25. - MEDIUM_HIGH_UTILIZATION: DBs with utilization greater or equal than 50 but lower than 75. - MEDIUM_LOW_UTILIZATION: DBs with utilization greater or equal than 25 but lower than 50. Allowed values are: "HIGH_UTILIZATION", "LOW_UTILIZATION", "MEDIUM_HIGH_UTILIZATION", "MEDIUM_LOW_UTILIZATION"'),
    confidence: int | None = Field(None, description="This parameter is used to change data's confidence level, this data is ingested by the forecast algorithm. Confidence is the probability of an interval to contain the expected population parameter. Manipulation of this value will lead to different results. If not set, default confidence value is 95%."),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    host_type: list[str] | None = Field(None, description='Filter by one or more host types. Possible values are CLOUD-HOST, EXTERNAL-HOST, COMANAGED-VM-HOST, COMANAGED-BM-HOST, COMANAGED-EXACS-HOST, COMANAGED-EXACC-HOST'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    high_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered highly utilized.'),
    low_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered low utilized.'),
    mount_point: str | None = Field(None, description='Mount points are specialized NTFS filesystem objects.'),
    interface_name: str | None = Field(None, description='Name of the network interface.'),
    gpu_id: int | None = Field(None, description='GPU identifier.'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('summarize_host_insight_resource_forecast_trend', compartment_id=compartment_id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, platform_type=platform_type, id=id, exadata_insight_id=exadata_insight_id, statistic=statistic, forecast_days=forecast_days, forecast_model=forecast_model, utilization_level=utilization_level, confidence=confidence, compartment_id_in_subtree=compartment_id_in_subtree, host_type=host_type, host_id=host_id, vmcluster_name=vmcluster_name, high_utilization_threshold=high_utilization_threshold, low_utilization_threshold=low_utilization_threshold, mount_point=mount_point, interface_name=interface_name, gpu_id=gpu_id, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_resource_statistics"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_resource_statistics"],)
def summarize_host_insight_resource_statistics(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_metric: str = Field(..., description='Filter by host resource metric. Supported values are CPU, MEMORY, LOGICAL_MEMORY, STORAGE and NETWORK.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    platform_type: list[str] | None = Field(None, description='Filter by one or more platform types. Supported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS]. Supported platformType(s) for MACS-managed cloud host insight: [LINUX]. Supported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX]. Allowed values are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX"'),
    id: list[str] | None = Field(None, description='Optional list of host insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    percentile: int | None = Field(None, description='Percentile values of daily usage to be used for computing the aggregate resource usage.'),
    insight_by: str | None = Field(None, description='Return data of a specific insight Possible values are High Utilization, Low Utilization, Any,High Utilization Forecast, Low Utilization Forecast'),
    forecast_days: int | None = Field(None, description='Number of days used for utilization forecast analysis.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='The order in which resource statistics records are listed. Allowed values are: "utilizationPercent", "usage", "usageChangePercent", "hostName", "platformType"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    host_type: list[str] | None = Field(None, description='Filter by one or more host types. Possible values are CLOUD-HOST, EXTERNAL-HOST, COMANAGED-VM-HOST, COMANAGED-BM-HOST, COMANAGED-EXACS-HOST, COMANAGED-EXACC-HOST'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    high_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered highly utilized.'),
    low_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered low utilized.'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('summarize_host_insight_resource_statistics', compartment_id=compartment_id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, platform_type=platform_type, id=id, exadata_insight_id=exadata_insight_id, percentile=percentile, insight_by=insight_by, forecast_days=forecast_days, limit=limit, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree, host_type=host_type, host_id=host_id, vmcluster_name=vmcluster_name, high_utilization_threshold=high_utilization_threshold, low_utilization_threshold=low_utilization_threshold, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_resource_usage"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_resource_usage"],)
def summarize_host_insight_resource_usage(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_metric: str = Field(..., description='Filter by host resource metric. Supported values are CPU, MEMORY, LOGICAL_MEMORY, STORAGE and NETWORK.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    platform_type: list[str] | None = Field(None, description='Filter by one or more platform types. Supported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS]. Supported platformType(s) for MACS-managed cloud host insight: [LINUX]. Supported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX]. Allowed values are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX"'),
    id: list[str] | None = Field(None, description='Optional list of host insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    percentile: int | None = Field(None, description='Percentile values of daily usage to be used for computing the aggregate resource usage.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    host_type: list[str] | None = Field(None, description='Filter by one or more host types. Possible values are CLOUD-HOST, EXTERNAL-HOST, COMANAGED-VM-HOST, COMANAGED-BM-HOST, COMANAGED-EXACS-HOST, COMANAGED-EXACC-HOST'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('summarize_host_insight_resource_usage', compartment_id=compartment_id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, platform_type=platform_type, id=id, exadata_insight_id=exadata_insight_id, percentile=percentile, compartment_id_in_subtree=compartment_id_in_subtree, host_type=host_type, host_id=host_id, vmcluster_name=vmcluster_name, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_resource_usage_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_resource_usage_trend"],)
def summarize_host_insight_resource_usage_trend(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_metric: str = Field(..., description='Filter by host resource metric. Supported values are CPU, MEMORY, LOGICAL_MEMORY, STORAGE and NETWORK.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    platform_type: list[str] | None = Field(None, description='Filter by one or more platform types. Supported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS]. Supported platformType(s) for MACS-managed cloud host insight: [LINUX]. Supported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX]. Allowed values are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX"'),
    id: list[str] | None = Field(None, description='Optional list of host insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    sort_order: str | None = Field(None, description='The sort order to use, either ascending (`ASC`) or descending (`DESC`). Allowed values are: "ASC", "DESC"'),
    sort_by: str | None = Field(None, description='Sorts using end timestamp, usage or capacity Allowed values are: "endTimestamp", "usage", "capacity"'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    host_type: list[str] | None = Field(None, description='Filter by one or more host types. Possible values are CLOUD-HOST, EXTERNAL-HOST, COMANAGED-VM-HOST, COMANAGED-BM-HOST, COMANAGED-EXACS-HOST, COMANAGED-EXACC-HOST'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('summarize_host_insight_resource_usage_trend', compartment_id=compartment_id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, platform_type=platform_type, id=id, exadata_insight_id=exadata_insight_id, sort_order=sort_order, sort_by=sort_by, compartment_id_in_subtree=compartment_id_in_subtree, host_type=host_type, host_id=host_id, vmcluster_name=vmcluster_name, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_resource_utilization_insight"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_resource_utilization_insight"],)
def summarize_host_insight_resource_utilization_insight(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_metric: str = Field(..., description='Filter by host resource metric. Supported values are CPU, MEMORY, LOGICAL_MEMORY, STORAGE and NETWORK.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    platform_type: list[str] | None = Field(None, description='Filter by one or more platform types. Supported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS]. Supported platformType(s) for MACS-managed cloud host insight: [LINUX]. Supported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX]. Allowed values are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX"'),
    id: list[str] | None = Field(None, description='Optional list of host insight resource OCIDs.'),
    exadata_insight_id: list[str] | None = Field(None, description='Optional list of exadata insight resource OCIDs.'),
    forecast_days: int | None = Field(None, description='Number of days used for utilization forecast analysis.'),
    compartment_id_in_subtree: bool | None = Field(None, description='A flag to search all resources within a given compartment and all sub-compartments.'),
    host_type: list[str] | None = Field(None, description='Filter by one or more host types. Possible values are CLOUD-HOST, EXTERNAL-HOST, COMANAGED-VM-HOST, COMANAGED-BM-HOST, COMANAGED-EXACS-HOST, COMANAGED-EXACC-HOST'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    vmcluster_name: list[str] | None = Field(None, description='Optional list of Exadata Insight VM cluster name.'),
    high_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered highly utilized.'),
    low_utilization_threshold: int | None = Field(None, description='Percent value in which a resource metric is considered low utilized.'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('summarize_host_insight_resource_utilization_insight', compartment_id=compartment_id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, platform_type=platform_type, id=id, exadata_insight_id=exadata_insight_id, forecast_days=forecast_days, compartment_id_in_subtree=compartment_id_in_subtree, host_type=host_type, host_id=host_id, vmcluster_name=vmcluster_name, high_utilization_threshold=high_utilization_threshold, low_utilization_threshold=low_utilization_threshold, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_storage_usage_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_storage_usage_trend"],)
def summarize_host_insight_storage_usage_trend(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str = Field(..., description='Required OCID of the host insight resource.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    statistic: str | None = Field(None, description='Choose the type of statistic metric data to be used for forecasting. Allowed values are: "AVG", "MAX"'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('summarize_host_insight_storage_usage_trend', compartment_id=compartment_id, id=id, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, host_id=host_id, limit=limit, statistic=statistic, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_top_processes_usage"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_top_processes_usage"],)
def summarize_host_insight_top_processes_usage(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str = Field(..., description='Required OCID of the host insight resource.'),
    resource_metric: str = Field(..., description='Host top processes resource metric sort options. Supported values are CPU, MEMORY, VIIRTUAL_MEMORY.'),
    timestamp: datetime = Field(..., description='Timestamp at which to gather the top processes. This will be top processes over the hour or over the day pending the time range passed into the query.'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    host_type: list[str] | None = Field(None, description='Filter by one or more host types. Possible values are CLOUD-HOST, EXTERNAL-HOST, COMANAGED-VM-HOST, COMANAGED-BM-HOST, COMANAGED-EXACS-HOST, COMANAGED-EXACC-HOST'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    statistic: str | None = Field(None, description='Choose the type of statistic metric data to be used for forecasting. Allowed values are: "AVG", "MAX"'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('summarize_host_insight_top_processes_usage', compartment_id=compartment_id, id=id, resource_metric=resource_metric, timestamp=timestamp, time_interval_start=time_interval_start, time_interval_end=time_interval_end, limit=limit, analysis_time_interval=analysis_time_interval, host_type=host_type, host_id=host_id, statistic=statistic, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_host_insight_top_processes_usage_trend"],
    annotations=TOOL_ANNOTATIONS["summarize_host_insight_top_processes_usage_trend"],)
def summarize_host_insight_top_processes_usage_trend(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str = Field(..., description='Required OCID of the host insight resource.'),
    resource_metric: str = Field(..., description='Host top processes resource metric sort options. Supported values are CPU, MEMORY, VIIRTUAL_MEMORY.'),
    analysis_time_interval: str | None = Field(None, description='Specify time period in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D. If timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored. Examples P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).'),
    time_interval_start: datetime | None = Field(None, description='Analysis start time in UTC in ISO 8601 format(inclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). The minimum allowed value is 2 years prior to the current day. timeIntervalStart and timeIntervalEnd parameters are used together. If analysisTimeInterval is specified, this parameter is ignored.'),
    time_interval_end: datetime | None = Field(None, description='Analysis end time in UTC in ISO 8601 format(exclusive). Example 2019-10-30T00:00:00Z (yyyy-MM-ddThh:mm:ssZ). timeIntervalStart and timeIntervalEnd are used together. If timeIntervalEnd is not specified, current time is used as timeIntervalEnd.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    host_type: list[str] | None = Field(None, description='Filter by one or more host types. Possible values are CLOUD-HOST, EXTERNAL-HOST, COMANAGED-VM-HOST, COMANAGED-BM-HOST, COMANAGED-EXACS-HOST, COMANAGED-EXACC-HOST'),
    host_id: str | None = Field(None, description='Optional OCID of the host (Compute Id).'),
    process_hash: str | None = Field(None, description='Unique identifier for a process.'),
    statistic: str | None = Field(None, description='Choose the type of statistic metric data to be used for forecasting. Allowed values are: "AVG", "MAX"'),
    status: list[str] | None = Field(None, description='Resource Status Allowed values are: "DISABLED", "ENABLED", "TERMINATED"'),) -> Any:
    return invoke_opsi('summarize_host_insight_top_processes_usage_trend', compartment_id=compartment_id, id=id, resource_metric=resource_metric, analysis_time_interval=analysis_time_interval, time_interval_start=time_interval_start, time_interval_end=time_interval_end, limit=limit, host_type=host_type, host_id=host_id, process_hash=process_hash, statistic=statistic, status=status)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_operations_insights_warehouse_resource_usage"],
    annotations=TOOL_ANNOTATIONS["summarize_operations_insights_warehouse_resource_usage"],)
def summarize_operations_insights_warehouse_resource_usage(
    operations_insights_warehouse_id: str = Field(..., description='Unique Ops Insights Warehouse identifier'),) -> Any:
    return invoke_opsi('summarize_operations_insights_warehouse_resource_usage', operations_insights_warehouse_id=operations_insights_warehouse_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_awr_hub"],
    annotations=TOOL_ANNOTATIONS["update_awr_hub"],)
def update_awr_hub(
    awr_hub_id: str = Field(..., description='Unique Awr Hub identifier'),
    update_awr_hub_details: dict[str, Any] | UpdateAwrHubDetails = Field(..., description='The AWR Hub configuration fields to update.'),) -> Any:
    return invoke_opsi('update_awr_hub', awr_hub_id=awr_hub_id, update_awr_hub_details=update_awr_hub_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_awr_hub_source"],
    annotations=TOOL_ANNOTATIONS["update_awr_hub_source"],)
def update_awr_hub_source(
    update_awr_hub_source_details: dict[str, Any] | UpdateAwrHubSourceDetails = Field(..., description='The AWR Hub source configuration fields to update.'),
    awr_hub_source_id: str = Field(..., description='Unique Awr Hub Source identifier'),) -> Any:
    return invoke_opsi('update_awr_hub_source', update_awr_hub_source_details=update_awr_hub_source_details, awr_hub_source_id=awr_hub_source_id)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_chargeback_plan"],
    annotations=TOOL_ANNOTATIONS["update_chargeback_plan"],)
def update_chargeback_plan(
    chargebackplan_id: str = Field(..., description='The OCID of the Ops Insights chargeback plan.'),
    update_chargeback_plan_details: dict[str, Any] | UpdateChargebackPlanDetails = Field(..., description='The details used to update a chargeback plan.'),) -> Any:
    return invoke_opsi('update_chargeback_plan', chargebackplan_id=chargebackplan_id, update_chargeback_plan_details=update_chargeback_plan_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_chargeback_plan_report"],
    annotations=TOOL_ANNOTATIONS["update_chargeback_plan_report"],)
def update_chargeback_plan_report(
    chargeback_plan_report_id: str = Field(..., description='The OCID of the Ops Insights chargeback plan report.'),
    id: str = Field(..., description='Unique Ops insight identifier'),
    resource_type: str = Field(..., description='Filter by resource type. Supported values are EXADATA_INSIGHT, HOST_INSIGHT, DATABASE_INSIGHT.'),
    update_chargeback_plan_report_details: dict[str, Any] | UpdateChargebackPlanReportDetails = Field(..., description='The details used to update a chargeback plan report.'),) -> Any:
    return invoke_opsi('update_chargeback_plan_report', chargeback_plan_report_id=chargeback_plan_report_id, id=id, resource_type=resource_type, update_chargeback_plan_report_details=update_chargeback_plan_report_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_database_insight"],
    annotations=TOOL_ANNOTATIONS["update_database_insight"],)
def update_database_insight(
    database_insight_id: str = Field(..., description='Unique database insight identifier'),
    update_database_insight_details: dict[str, Any] | UpdateDatabaseInsightDetails = Field(..., description='The database insight configuration fields to update.'),) -> Any:
    return invoke_opsi('update_database_insight', database_insight_id=database_insight_id, update_database_insight_details=update_database_insight_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_enterprise_manager_bridge"],
    annotations=TOOL_ANNOTATIONS["update_enterprise_manager_bridge"],)
def update_enterprise_manager_bridge(
    enterprise_manager_bridge_id: str = Field(..., description='Unique Enterprise Manager bridge identifier'),
    update_enterprise_manager_bridge_details: dict[str, Any] | UpdateEnterpriseManagerBridgeDetails = Field(..., description='The Enterprise Manager bridge configuration fields to update.'),) -> Any:
    return invoke_opsi('update_enterprise_manager_bridge', enterprise_manager_bridge_id=enterprise_manager_bridge_id, update_enterprise_manager_bridge_details=update_enterprise_manager_bridge_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_exadata_insight"],
    annotations=TOOL_ANNOTATIONS["update_exadata_insight"],)
def update_exadata_insight(
    exadata_insight_id: str = Field(..., description='Unique Exadata insight identifier'),
    update_exadata_insight_details: dict[str, Any] | UpdateExadataInsightDetails = Field(..., description='The Exadata insight configuration fields to update.'),) -> Any:
    return invoke_opsi('update_exadata_insight', exadata_insight_id=exadata_insight_id, update_exadata_insight_details=update_exadata_insight_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_host_insight"],
    annotations=TOOL_ANNOTATIONS["update_host_insight"],)
def update_host_insight(
    host_insight_id: str = Field(..., description='Unique host insight identifier'),
    update_host_insight_details: dict[str, Any] | UpdateHostInsightDetails = Field(..., description='The host insight configuration fields to update.'),) -> Any:
    return invoke_opsi('update_host_insight', host_insight_id=host_insight_id, update_host_insight_details=update_host_insight_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_news_report"],
    annotations=TOOL_ANNOTATIONS["update_news_report"],)
def update_news_report(
    news_report_id: str = Field(..., description='Unique news report identifier.'),
    update_news_report_details: dict[str, Any] | UpdateNewsReportDetails = Field(..., description='The news report configuration fields to update.'),) -> Any:
    return invoke_opsi('update_news_report', news_report_id=news_report_id, update_news_report_details=update_news_report_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_operations_insights_private_endpoint"],
    annotations=TOOL_ANNOTATIONS["update_operations_insights_private_endpoint"],)
def update_operations_insights_private_endpoint(
    operations_insights_private_endpoint_id: str = Field(..., description='The OCID of the Operation Insights private endpoint.'),
    update_operations_insights_private_endpoint_details: dict[str, Any] | UpdateOperationsInsightsPrivateEndpointDetails = Field(..., description='The details used to update a private endpoint.'),) -> Any:
    return invoke_opsi('update_operations_insights_private_endpoint', operations_insights_private_endpoint_id=operations_insights_private_endpoint_id, update_operations_insights_private_endpoint_details=update_operations_insights_private_endpoint_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_operations_insights_warehouse"],
    annotations=TOOL_ANNOTATIONS["update_operations_insights_warehouse"],)
def update_operations_insights_warehouse(
    operations_insights_warehouse_id: str = Field(..., description='Unique Ops Insights Warehouse identifier'),
    update_operations_insights_warehouse_details: dict[str, Any] | UpdateOperationsInsightsWarehouseDetails = Field(..., description='The Operations Insights Warehouse configuration fields to update.'),) -> Any:
    return invoke_opsi('update_operations_insights_warehouse', operations_insights_warehouse_id=operations_insights_warehouse_id, update_operations_insights_warehouse_details=update_operations_insights_warehouse_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_operations_insights_warehouse_user"],
    annotations=TOOL_ANNOTATIONS["update_operations_insights_warehouse_user"],)
def update_operations_insights_warehouse_user(
    operations_insights_warehouse_user_id: str = Field(..., description='Unique Operations Insights Warehouse User identifier'),
    update_operations_insights_warehouse_user_details: dict[str, Any] | UpdateOperationsInsightsWarehouseUserDetails = Field(..., description='The Operations Insights Warehouse User configuration fields to update.'),) -> Any:
    return invoke_opsi('update_operations_insights_warehouse_user', operations_insights_warehouse_user_id=operations_insights_warehouse_user_id, update_operations_insights_warehouse_user_details=update_operations_insights_warehouse_user_details)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_opsi_configuration"],
    annotations=TOOL_ANNOTATIONS["update_opsi_configuration"],)
def update_opsi_configuration(
    opsi_configuration_id: str = Field(..., description='OCID of OPSI configuration resource.'),
    update_opsi_configuration_details: dict[str, Any] | UpdateOpsiConfigurationDetails = Field(..., description='The OPSI configuration resource details to be updated.'),) -> Any:
    return invoke_opsi('update_opsi_configuration', opsi_configuration_id=opsi_configuration_id, update_opsi_configuration_details=update_opsi_configuration_details)
