"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at

"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from mcp.types import ToolAnnotations
from pydantic import Field

from oracle.oci_oracle_db_observability.v1.auth import get_oci_config

from. import __project__, __version__
from. import models
from.metadata import BOOTSTRAP_TOOL_NAMES, MUTABLE_TOOL_NAMES, TOOL_DESCRIPTIONS, TOOL_NAMES
from.models import *  # noqa: F403
from.mcp import mcp
from.runtime import invoke_dbm, invoke_identity, normalize_tool_value


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
    root_compartment_id: str | None = Field(None, description="The root compartment OCID. Defaults to the configured tenancy OCID."),
    include_subtree: bool = Field(True, description="Whether to include subcompartments."),
    access_level: models.CompartmentAccessLevel = Field("ACCESSIBLE", description="Compartment visibility filter: ANY or ACCESSIBLE."),
    name: str | None = Field(None, description="Optional exact compartment name filter."),
    lifecycle_state: models.CompartmentLifecycleState | None = Field(None, description="Optional compartment lifecycle state filter."),
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
    description=TOOL_DESCRIPTIONS["addm_tasks"],
    annotations=TOOL_ANNOTATIONS["addm_tasks"],)
def addm_tasks(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    time_start: datetime = Field(..., description='The beginning of the time range to search for ADDM tasks as defined by date-time RFC3339 format.'),
    time_end: datetime = Field(..., description='The end of the time range to search for ADDM tasks as defined by date-time RFC3339 format.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TASK_NAME', 'TASK_ID', 'DESCRIPTION', 'DB_USER', 'STATUS', 'TIME_CREATED', 'BEGIN_TIME', 'END_TIME'] | None = Field(None, description='The option to sort the list of ADDM tasks.\n\nAllowed values are: "TASK_NAME", "TASK_ID", "DESCRIPTION", "DB_USER", "STATUS", "TIME_CREATED", "BEGIN_TIME", "END_TIME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'addm_tasks',
        managed_database_id=managed_database_id,
        time_start=time_start,
        time_end=time_end,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_cloud_exadata_infrastructure_compartment"],
    annotations=TOOL_ANNOTATIONS["change_cloud_exadata_infrastructure_compartment"],)
def change_cloud_exadata_infrastructure_compartment(
    cloud_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),
    change_cloud_exadata_infrastructure_compartment_details: dict[str, Any] | ChangeCloudExadataInfrastructureCompartmentDetails = Field(..., description='The details required to move the Exadata infrastructure from one compartment to another.'),) -> Any:
    return invoke_dbm(
        'change_cloud_exadata_infrastructure_compartment',
        cloud_exadata_infrastructure_id=cloud_exadata_infrastructure_id,
        change_cloud_exadata_infrastructure_compartment_details=change_cloud_exadata_infrastructure_compartment_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_database_parameters"],
    annotations=TOOL_ANNOTATIONS["change_database_parameters"],)
def change_database_parameters(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    change_database_parameters_details: dict[str, Any] | ChangeDatabaseParametersDetails = Field(..., description='The details required to change database parameter values.'),) -> Any:
    return invoke_dbm(
        'change_database_parameters',
        managed_database_id=managed_database_id,
        change_database_parameters_details=change_database_parameters_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_db_management_private_endpoint_compartment"],
    annotations=TOOL_ANNOTATIONS["change_db_management_private_endpoint_compartment"],)
def change_db_management_private_endpoint_compartment(
    db_management_private_endpoint_id: str = Field(..., description='The OCID of the Database Management private endpoint.'),
    change_db_management_private_endpoint_compartment_details: dict[str, Any] | ChangeDbManagementPrivateEndpointCompartmentDetails = Field(..., description='The details used to move the Database Management private endpoint to another compartment.'),) -> Any:
    return invoke_dbm(
        'change_db_management_private_endpoint_compartment',
        db_management_private_endpoint_id=db_management_private_endpoint_id,
        change_db_management_private_endpoint_compartment_details=change_db_management_private_endpoint_compartment_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_external_db_system_compartment"],
    annotations=TOOL_ANNOTATIONS["change_external_db_system_compartment"],)
def change_external_db_system_compartment(
    external_db_system_id: str = Field(..., description='The OCID of the external DB system.'),
    change_external_db_system_compartment_details: dict[str, Any] | ChangeExternalDbSystemCompartmentDetails = Field(..., description='The OCID of the compartment to which the external DB system should be moved.'),) -> Any:
    return invoke_dbm(
        'change_external_db_system_compartment',
        external_db_system_id=external_db_system_id,
        change_external_db_system_compartment_details=change_external_db_system_compartment_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_external_exadata_infrastructure_compartment"],
    annotations=TOOL_ANNOTATIONS["change_external_exadata_infrastructure_compartment"],)
def change_external_exadata_infrastructure_compartment(
    external_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),
    change_external_exadata_infrastructure_compartment_details: dict[str, Any] | ChangeExternalExadataInfrastructureCompartmentDetails = Field(..., description='The details required to move the Exadata infrastructure from one compartment to another.'),) -> Any:
    return invoke_dbm(
        'change_external_exadata_infrastructure_compartment',
        external_exadata_infrastructure_id=external_exadata_infrastructure_id,
        change_external_exadata_infrastructure_compartment_details=change_external_exadata_infrastructure_compartment_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_job_compartment"],
    annotations=TOOL_ANNOTATIONS["change_job_compartment"],)
def change_job_compartment(
    job_id: str = Field(..., description='The identifier of the job.'),
    change_job_compartment_details: dict[str, Any] | ChangeJobCompartmentDetails = Field(..., description='The OCID of the compartment to move the job to.'),) -> Any:
    return invoke_dbm(
        'change_job_compartment',
        job_id=job_id,
        change_job_compartment_details=change_job_compartment_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_managed_database_group_compartment"],
    annotations=TOOL_ANNOTATIONS["change_managed_database_group_compartment"],)
def change_managed_database_group_compartment(
    managed_database_group_id: str = Field(..., description='The OCID of the Managed Database Group.'),
    change_managed_database_group_compartment_details: dict[str, Any] | ChangeManagedDatabaseGroupCompartmentDetails = Field(..., description='The OCID of the compartment to move the Managed Database Group to.'),) -> Any:
    return invoke_dbm(
        'change_managed_database_group_compartment',
        managed_database_group_id=managed_database_group_id,
        change_managed_database_group_compartment_details=change_managed_database_group_compartment_details,)




@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_named_credential_compartment"],
    annotations=TOOL_ANNOTATIONS["change_named_credential_compartment"],)
def change_named_credential_compartment(
    named_credential_id: str = Field(..., description='The OCID of the named credential.'),
    change_named_credential_compartment_details: dict[str, Any] | ChangeNamedCredentialCompartmentDetails = Field(..., description='The OCID of the compartment to which the named credential should be moved.'),) -> Any:
    return invoke_dbm(
        'change_named_credential_compartment',
        named_credential_id=named_credential_id,
        change_named_credential_compartment_details=change_named_credential_compartment_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_plan_retention"],
    annotations=TOOL_ANNOTATIONS["change_plan_retention"],)
def change_plan_retention(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    change_plan_retention_details: dict[str, Any] | ChangePlanRetentionDetails = Field(..., description='The details required to change the plan retention period.'),) -> Any:
    return invoke_dbm(
        'change_plan_retention',
        managed_database_id=managed_database_id,
        change_plan_retention_details=change_plan_retention_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_space_budget"],
    annotations=TOOL_ANNOTATIONS["change_space_budget"],)
def change_space_budget(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    change_space_budget_details: dict[str, Any] | ChangeSpaceBudgetDetails = Field(..., description='The details required to change the disk space limit for the SQL Management Base.'),) -> Any:
    return invoke_dbm(
        'change_space_budget',
        managed_database_id=managed_database_id,
        change_space_budget_details=change_space_budget_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["change_sql_plan_baselines_attributes"],
    annotations=TOOL_ANNOTATIONS["change_sql_plan_baselines_attributes"],)
def change_sql_plan_baselines_attributes(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    change_sql_plan_baselines_attributes_details: dict[str, Any] | ChangeSqlPlanBaselinesAttributesDetails = Field(..., description='The details required to change SQL plan baseline attributes.'),) -> Any:
    return invoke_dbm(
        'change_sql_plan_baselines_attributes',
        managed_database_id=managed_database_id,
        change_sql_plan_baselines_attributes_details=change_sql_plan_baselines_attributes_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["check_cloud_db_system_connector_connection_status"],
    annotations=TOOL_ANNOTATIONS["check_cloud_db_system_connector_connection_status"],)
def check_cloud_db_system_connector_connection_status(
    cloud_db_system_connector_id: str = Field(..., description='The OCID of the cloud connector.'),) -> Any:
    return invoke_dbm(
        'check_cloud_db_system_connector_connection_status',
        cloud_db_system_connector_id=cloud_db_system_connector_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["check_cloud_exadata_storage_connector"],
    annotations=TOOL_ANNOTATIONS["check_cloud_exadata_storage_connector"],)
def check_cloud_exadata_storage_connector(
    cloud_exadata_storage_connector_id: str = Field(..., description='The OCID of the connector to the Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'check_cloud_exadata_storage_connector',
        cloud_exadata_storage_connector_id=cloud_exadata_storage_connector_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["check_external_db_system_connector_connection_status"],
    annotations=TOOL_ANNOTATIONS["check_external_db_system_connector_connection_status"],)
def check_external_db_system_connector_connection_status(
    external_db_system_connector_id: str = Field(..., description='The OCID of the external connector.'),) -> Any:
    return invoke_dbm(
        'check_external_db_system_connector_connection_status',
        external_db_system_connector_id=external_db_system_connector_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["check_external_exadata_storage_connector"],
    annotations=TOOL_ANNOTATIONS["check_external_exadata_storage_connector"],)
def check_external_exadata_storage_connector(
    external_exadata_storage_connector_id: str = Field(..., description='The OCID of the connector to the Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'check_external_exadata_storage_connector',
        external_exadata_storage_connector_id=external_exadata_storage_connector_id,)




@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_cloud_db_system"],
    annotations=TOOL_ANNOTATIONS["create_cloud_db_system"],)
def create_cloud_db_system(
    create_cloud_db_system_details: dict[str, Any] | CreateCloudDbSystemDetails = Field(..., description='The details required to create an cloud DB system.'),) -> Any:
    return invoke_dbm(
        'create_cloud_db_system',
        create_cloud_db_system_details=create_cloud_db_system_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_cloud_db_system_connector"],
    annotations=TOOL_ANNOTATIONS["create_cloud_db_system_connector"],)
def create_cloud_db_system_connector(
    create_cloud_db_system_connector_details: dict[str, Any] | CreateCloudDbSystemConnectorDetails = Field(..., description='The details required to create an cloud connector.'),) -> Any:
    return invoke_dbm(
        'create_cloud_db_system_connector',
        create_cloud_db_system_connector_details=create_cloud_db_system_connector_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_cloud_db_system_discovery"],
    annotations=TOOL_ANNOTATIONS["create_cloud_db_system_discovery"],)
def create_cloud_db_system_discovery(
    create_cloud_db_system_discovery_details: dict[str, Any] | CreateCloudDbSystemDiscoveryDetails = Field(..., description='The details required to create an cloud DB system discovery.'),) -> Any:
    return invoke_dbm(
        'create_cloud_db_system_discovery',
        create_cloud_db_system_discovery_details=create_cloud_db_system_discovery_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_cloud_exadata_infrastructure"],
    annotations=TOOL_ANNOTATIONS["create_cloud_exadata_infrastructure"],)
def create_cloud_exadata_infrastructure(
    create_cloud_exadata_infrastructure_details: dict[str, Any] | CreateCloudExadataInfrastructureDetails = Field(..., description='The details required to create the managed Exadata infrastructure resources.'),) -> Any:
    return invoke_dbm(
        'create_cloud_exadata_infrastructure',
        create_cloud_exadata_infrastructure_details=create_cloud_exadata_infrastructure_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_cloud_exadata_storage_connector"],
    annotations=TOOL_ANNOTATIONS["create_cloud_exadata_storage_connector"],)
def create_cloud_exadata_storage_connector(
    create_cloud_exadata_storage_connector_details: dict[str, Any] | CreateCloudExadataStorageConnectorDetails = Field(..., description='The details required to add connections to the Exadata storage servers.'),) -> Any:
    return invoke_dbm(
        'create_cloud_exadata_storage_connector',
        create_cloud_exadata_storage_connector_details=create_cloud_exadata_storage_connector_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_db_management_private_endpoint"],
    annotations=TOOL_ANNOTATIONS["create_db_management_private_endpoint"],)
def create_db_management_private_endpoint(
    create_db_management_private_endpoint_details: dict[str, Any] | CreateDbManagementPrivateEndpointDetails = Field(..., description='Details used to create a new Database Management private endpoint.'),) -> Any:
    return invoke_dbm(
        'create_db_management_private_endpoint',
        create_db_management_private_endpoint_details=create_db_management_private_endpoint_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_external_db_system"],
    annotations=TOOL_ANNOTATIONS["create_external_db_system"],)
def create_external_db_system(
    create_external_db_system_details: dict[str, Any] | CreateExternalDbSystemDetails = Field(..., description='The details required to create an external DB system.'),) -> Any:
    return invoke_dbm(
        'create_external_db_system',
        create_external_db_system_details=create_external_db_system_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_external_db_system_connector"],
    annotations=TOOL_ANNOTATIONS["create_external_db_system_connector"],)
def create_external_db_system_connector(
    create_external_db_system_connector_details: dict[str, Any] | CreateExternalDbSystemConnectorDetails = Field(..., description='The details required to create an external connector.'),) -> Any:
    return invoke_dbm(
        'create_external_db_system_connector',
        create_external_db_system_connector_details=create_external_db_system_connector_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_external_db_system_discovery"],
    annotations=TOOL_ANNOTATIONS["create_external_db_system_discovery"],)
def create_external_db_system_discovery(
    create_external_db_system_discovery_details: dict[str, Any] | CreateExternalDbSystemDiscoveryDetails = Field(..., description='The details required to create an external DB system discovery.'),) -> Any:
    return invoke_dbm(
        'create_external_db_system_discovery',
        create_external_db_system_discovery_details=create_external_db_system_discovery_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_external_exadata_infrastructure"],
    annotations=TOOL_ANNOTATIONS["create_external_exadata_infrastructure"],)
def create_external_exadata_infrastructure(
    create_external_exadata_infrastructure_details: dict[str, Any] | CreateExternalExadataInfrastructureDetails = Field(..., description='The details required to create the managed Exadata infrastructure resources.'),) -> Any:
    return invoke_dbm(
        'create_external_exadata_infrastructure',
        create_external_exadata_infrastructure_details=create_external_exadata_infrastructure_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_external_exadata_storage_connector"],
    annotations=TOOL_ANNOTATIONS["create_external_exadata_storage_connector"],)
def create_external_exadata_storage_connector(
    create_external_exadata_storage_connector_details: dict[str, Any] | CreateExternalExadataStorageConnectorDetails = Field(..., description='The details required to add connections to the Exadata storage servers.'),) -> Any:
    return invoke_dbm(
        'create_external_exadata_storage_connector',
        create_external_exadata_storage_connector_details=create_external_exadata_storage_connector_details,)






@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_job"],
    annotations=TOOL_ANNOTATIONS["create_job"],)
def create_job(
    create_job_details: dict[str, Any] | CreateJobDetails = Field(..., description='The details required to create a job.'),) -> Any:
    return invoke_dbm(
        'create_job',
        create_job_details=create_job_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_managed_database_group"],
    annotations=TOOL_ANNOTATIONS["create_managed_database_group"],)
def create_managed_database_group(
    create_managed_database_group_details: dict[str, Any] | CreateManagedDatabaseGroupDetails = Field(..., description='The details required to create a Managed Database Group.'),) -> Any:
    return invoke_dbm(
        'create_managed_database_group',
        create_managed_database_group_details=create_managed_database_group_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_named_credential"],
    annotations=TOOL_ANNOTATIONS["create_named_credential"],)
def create_named_credential(
    create_named_credential_details: dict[str, Any] | CreateNamedCredentialDetails = Field(..., description='The details required to create a named credential.'),) -> Any:
    return invoke_dbm(
        'create_named_credential',
        create_named_credential_details=create_named_credential_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_sql_tuning_set"],
    annotations=TOOL_ANNOTATIONS["create_sql_tuning_set"],)
def create_sql_tuning_set(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    create_sql_tuning_set_details: dict[str, Any] | CreateSqlTuningSetDetails = Field(..., description='The details required to create a Sql tuning set.'),) -> Any:
    return invoke_dbm(
        'create_sql_tuning_set',
        managed_database_id=managed_database_id,
        create_sql_tuning_set_details=create_sql_tuning_set_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["create_tablespace"],
    annotations=TOOL_ANNOTATIONS["create_tablespace"],)
def create_tablespace(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    create_tablespace_details: dict[str, Any] | CreateTablespaceDetails = Field(..., description='The details required to create a tablespace.'),) -> Any:
    return invoke_dbm(
        'create_tablespace',
        managed_database_id=managed_database_id,
        create_tablespace_details=create_tablespace_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_automatic_initial_plan_capture"],
    annotations=TOOL_ANNOTATIONS["disable_automatic_initial_plan_capture"],)
def disable_automatic_initial_plan_capture(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    disable_automatic_initial_plan_capture_details: dict[str, Any] | DisableAutomaticInitialPlanCaptureDetails = Field(..., description='The details required to disable automatic initial plan capture.'),) -> Any:
    return invoke_dbm(
        'disable_automatic_initial_plan_capture',
        managed_database_id=managed_database_id,
        disable_automatic_initial_plan_capture_details=disable_automatic_initial_plan_capture_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_automatic_spm_evolve_advisor_task"],
    annotations=TOOL_ANNOTATIONS["disable_automatic_spm_evolve_advisor_task"],)
def disable_automatic_spm_evolve_advisor_task(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    disable_automatic_spm_evolve_advisor_task_details: dict[str, Any] | DisableAutomaticSpmEvolveAdvisorTaskDetails = Field(..., description='The details required to disable Automatic SPM Evolve Advisor task.'),) -> Any:
    return invoke_dbm(
        'disable_automatic_spm_evolve_advisor_task',
        managed_database_id=managed_database_id,
        disable_automatic_spm_evolve_advisor_task_details=disable_automatic_spm_evolve_advisor_task_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_autonomous_database_management_feature"],
    annotations=TOOL_ANNOTATIONS["disable_autonomous_database_management_feature"],)
def disable_autonomous_database_management_feature(
    autonomous_database_id: str = Field(..., description='The OCID of the Autonomous Database.'),
    disable_autonomous_database_management_feature_details: dict[str, Any] | DisableAutonomousDatabaseManagementFeatureDetails = Field(..., description='The details required to disable a Database Management feature for an Autonomous Database.'),) -> Any:
    return invoke_dbm(
        'disable_autonomous_database_management_feature',
        autonomous_database_id=autonomous_database_id,
        disable_autonomous_database_management_feature_details=disable_autonomous_database_management_feature_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_cloud_db_system_database_management"],
    annotations=TOOL_ANNOTATIONS["disable_cloud_db_system_database_management"],)
def disable_cloud_db_system_database_management(
    cloud_db_system_id: str = Field(..., description='The OCID of the cloud DB system.'),) -> Any:
    return invoke_dbm(
        'disable_cloud_db_system_database_management',
        cloud_db_system_id=cloud_db_system_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_cloud_db_system_stack_monitoring"],
    annotations=TOOL_ANNOTATIONS["disable_cloud_db_system_stack_monitoring"],)
def disable_cloud_db_system_stack_monitoring(
    cloud_db_system_id: str = Field(..., description='The OCID of the cloud DB system.'),) -> Any:
    return invoke_dbm(
        'disable_cloud_db_system_stack_monitoring',
        cloud_db_system_id=cloud_db_system_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_cloud_exadata_infrastructure_management"],
    annotations=TOOL_ANNOTATIONS["disable_cloud_exadata_infrastructure_management"],)
def disable_cloud_exadata_infrastructure_management(
    cloud_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),) -> Any:
    return invoke_dbm(
        'disable_cloud_exadata_infrastructure_management',
        cloud_exadata_infrastructure_id=cloud_exadata_infrastructure_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_database_management_feature"],
    annotations=TOOL_ANNOTATIONS["disable_database_management_feature"],)
def disable_database_management_feature(
    database_id: str = Field(..., description='The OCID of the Database.'),
    disable_database_management_feature_details: dict[str, Any] | DisableDatabaseManagementFeatureDetails = Field(..., description='The details required to disable a Database Management feature for an Oracle cloud database.'),) -> Any:
    return invoke_dbm(
        'disable_database_management_feature',
        database_id=database_id,
        disable_database_management_feature_details=disable_database_management_feature_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_external_container_database_management_feature"],
    annotations=TOOL_ANNOTATIONS["disable_external_container_database_management_feature"],)
def disable_external_container_database_management_feature(
    external_container_database_id: str = Field(..., description='The OCID of the external container database.'),
    disable_external_container_database_management_feature_details: dict[str, Any] | DisableExternalContainerDatabaseManagementFeatureDetails = Field(..., description='The details required to disable a Database Management feature for an external container database.'),) -> Any:
    return invoke_dbm(
        'disable_external_container_database_management_feature',
        external_container_database_id=external_container_database_id,
        disable_external_container_database_management_feature_details=disable_external_container_database_management_feature_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_external_db_system_database_management"],
    annotations=TOOL_ANNOTATIONS["disable_external_db_system_database_management"],)
def disable_external_db_system_database_management(
    external_db_system_id: str = Field(..., description='The OCID of the external DB system.'),) -> Any:
    return invoke_dbm(
        'disable_external_db_system_database_management',
        external_db_system_id=external_db_system_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_external_db_system_stack_monitoring"],
    annotations=TOOL_ANNOTATIONS["disable_external_db_system_stack_monitoring"],)
def disable_external_db_system_stack_monitoring(
    external_db_system_id: str = Field(..., description='The OCID of the external DB system.'),) -> Any:
    return invoke_dbm(
        'disable_external_db_system_stack_monitoring',
        external_db_system_id=external_db_system_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_external_exadata_infrastructure_management"],
    annotations=TOOL_ANNOTATIONS["disable_external_exadata_infrastructure_management"],)
def disable_external_exadata_infrastructure_management(
    external_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),) -> Any:
    return invoke_dbm(
        'disable_external_exadata_infrastructure_management',
        external_exadata_infrastructure_id=external_exadata_infrastructure_id,)




@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_external_non_container_database_management_feature"],
    annotations=TOOL_ANNOTATIONS["disable_external_non_container_database_management_feature"],)
def disable_external_non_container_database_management_feature(
    external_non_container_database_id: str = Field(..., description='The OCID of the external non-container database.'),
    disable_external_non_container_database_management_feature_details: dict[str, Any] | DisableExternalNonContainerDatabaseManagementFeatureDetails = Field(..., description='The details required to disable a Database Management feature for an external non-container database.'),) -> Any:
    return invoke_dbm(
        'disable_external_non_container_database_management_feature',
        external_non_container_database_id=external_non_container_database_id,
        disable_external_non_container_database_management_feature_details=disable_external_non_container_database_management_feature_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_external_pluggable_database_management_feature"],
    annotations=TOOL_ANNOTATIONS["disable_external_pluggable_database_management_feature"],)
def disable_external_pluggable_database_management_feature(
    external_pluggable_database_id: str = Field(..., description='The OCID of the external pluggable database.'),
    disable_external_pluggable_database_management_feature_details: dict[str, Any] | DisableExternalPluggableDatabaseManagementFeatureDetails = Field(..., description='The details required to disable a Database Management feature for an external pluggable database.'),) -> Any:
    return invoke_dbm(
        'disable_external_pluggable_database_management_feature',
        external_pluggable_database_id=external_pluggable_database_id,
        disable_external_pluggable_database_management_feature_details=disable_external_pluggable_database_management_feature_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_high_frequency_automatic_spm_evolve_advisor_task"],
    annotations=TOOL_ANNOTATIONS["disable_high_frequency_automatic_spm_evolve_advisor_task"],)
def disable_high_frequency_automatic_spm_evolve_advisor_task(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    disable_high_frequency_automatic_spm_evolve_advisor_task_details: dict[str, Any] | DisableHighFrequencyAutomaticSpmEvolveAdvisorTaskDetails = Field(..., description='The details required to disable high frequency Automatic SPM Evolve Advisor task.'),) -> Any:
    return invoke_dbm(
        'disable_high_frequency_automatic_spm_evolve_advisor_task',
        managed_database_id=managed_database_id,
        disable_high_frequency_automatic_spm_evolve_advisor_task_details=disable_high_frequency_automatic_spm_evolve_advisor_task_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_pluggable_database_management_feature"],
    annotations=TOOL_ANNOTATIONS["disable_pluggable_database_management_feature"],)
def disable_pluggable_database_management_feature(
    pluggable_database_id: str = Field(..., description='The OCID of the Oracle cloud pluggable database.'),
    disable_pluggable_database_management_feature_details: dict[str, Any] | DisablePluggableDatabaseManagementFeatureDetails = Field(..., description='The details required to disable a Database Management feature for an Oracle cloud pluggable database.'),) -> Any:
    return invoke_dbm(
        'disable_pluggable_database_management_feature',
        pluggable_database_id=pluggable_database_id,
        disable_pluggable_database_management_feature_details=disable_pluggable_database_management_feature_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["disable_sql_plan_baselines_usage"],
    annotations=TOOL_ANNOTATIONS["disable_sql_plan_baselines_usage"],)
def disable_sql_plan_baselines_usage(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    disable_sql_plan_baselines_usage_details: dict[str, Any] | DisableSqlPlanBaselinesUsageDetails = Field(..., description='The details required to disable SQL plan baseline usage.'),) -> Any:
    return invoke_dbm(
        'disable_sql_plan_baselines_usage',
        managed_database_id=managed_database_id,
        disable_sql_plan_baselines_usage_details=disable_sql_plan_baselines_usage_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["discover_cloud_exadata_infrastructure"],
    annotations=TOOL_ANNOTATIONS["discover_cloud_exadata_infrastructure"],)
def discover_cloud_exadata_infrastructure(
    discover_cloud_exadata_infrastructure_details: dict[str, Any] | DiscoverCloudExadataInfrastructureDetails = Field(..., description='The details required to discover and monitor the Exadata infrastructure.'),) -> Any:
    return invoke_dbm(
        'discover_cloud_exadata_infrastructure',
        discover_cloud_exadata_infrastructure_details=discover_cloud_exadata_infrastructure_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["discover_external_exadata_infrastructure"],
    annotations=TOOL_ANNOTATIONS["discover_external_exadata_infrastructure"],)
def discover_external_exadata_infrastructure(
    discover_external_exadata_infrastructure_details: dict[str, Any] | DiscoverExternalExadataInfrastructureDetails = Field(..., description='The details required to discover and monitor the Exadata infrastructure.'),) -> Any:
    return invoke_dbm(
        'discover_external_exadata_infrastructure',
        discover_external_exadata_infrastructure_details=discover_external_exadata_infrastructure_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_automatic_initial_plan_capture"],
    annotations=TOOL_ANNOTATIONS["enable_automatic_initial_plan_capture"],)
def enable_automatic_initial_plan_capture(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    enable_automatic_initial_plan_capture_details: dict[str, Any] | EnableAutomaticInitialPlanCaptureDetails = Field(..., description='The details required to enable automatic initial plan capture.'),) -> Any:
    return invoke_dbm(
        'enable_automatic_initial_plan_capture',
        managed_database_id=managed_database_id,
        enable_automatic_initial_plan_capture_details=enable_automatic_initial_plan_capture_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_automatic_spm_evolve_advisor_task"],
    annotations=TOOL_ANNOTATIONS["enable_automatic_spm_evolve_advisor_task"],)
def enable_automatic_spm_evolve_advisor_task(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    enable_automatic_spm_evolve_advisor_task_details: dict[str, Any] | EnableAutomaticSpmEvolveAdvisorTaskDetails = Field(..., description='The details required to enable Automatic SPM Evolve Advisor task.'),) -> Any:
    return invoke_dbm(
        'enable_automatic_spm_evolve_advisor_task',
        managed_database_id=managed_database_id,
        enable_automatic_spm_evolve_advisor_task_details=enable_automatic_spm_evolve_advisor_task_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_autonomous_database_management_feature"],
    annotations=TOOL_ANNOTATIONS["enable_autonomous_database_management_feature"],)
def enable_autonomous_database_management_feature(
    autonomous_database_id: str = Field(..., description='The OCID of the Autonomous Database.'),
    enable_autonomous_database_management_feature_details: dict[str, Any] | EnableAutonomousDatabaseManagementFeatureDetails = Field(..., description='The details required to enable a Database Management feature for an Autonomous Database.'),) -> Any:
    return invoke_dbm(
        'enable_autonomous_database_management_feature',
        autonomous_database_id=autonomous_database_id,
        enable_autonomous_database_management_feature_details=enable_autonomous_database_management_feature_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_cloud_db_system_database_management"],
    annotations=TOOL_ANNOTATIONS["enable_cloud_db_system_database_management"],)
def enable_cloud_db_system_database_management(
    cloud_db_system_id: str = Field(..., description='The OCID of the cloud DB system.'),
    enable_cloud_db_system_database_management_details: dict[str, Any] | EnableCloudDbSystemDatabaseManagementDetails = Field(..., description='The details required to enable Stack Monitoring for an cloud DB system.'),) -> Any:
    return invoke_dbm(
        'enable_cloud_db_system_database_management',
        cloud_db_system_id=cloud_db_system_id,
        enable_cloud_db_system_database_management_details=enable_cloud_db_system_database_management_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_cloud_db_system_stack_monitoring"],
    annotations=TOOL_ANNOTATIONS["enable_cloud_db_system_stack_monitoring"],)
def enable_cloud_db_system_stack_monitoring(
    cloud_db_system_id: str = Field(..., description='The OCID of the cloud DB system.'),
    enable_cloud_db_system_stack_monitoring_details: dict[str, Any] | EnableCloudDbSystemStackMonitoringDetails = Field(..., description='The details required to enable Stack Monitoring for an cloud DB system.'),) -> Any:
    return invoke_dbm(
        'enable_cloud_db_system_stack_monitoring',
        cloud_db_system_id=cloud_db_system_id,
        enable_cloud_db_system_stack_monitoring_details=enable_cloud_db_system_stack_monitoring_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_cloud_exadata_infrastructure_management"],
    annotations=TOOL_ANNOTATIONS["enable_cloud_exadata_infrastructure_management"],)
def enable_cloud_exadata_infrastructure_management(
    cloud_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),
    enable_cloud_exadata_infrastructure_management_details: dict[str, Any] | EnableCloudExadataInfrastructureManagementDetails = Field(..., description='The details required to enable management for the Exadata infrastructure.'),) -> Any:
    return invoke_dbm(
        'enable_cloud_exadata_infrastructure_management',
        cloud_exadata_infrastructure_id=cloud_exadata_infrastructure_id,
        enable_cloud_exadata_infrastructure_management_details=enable_cloud_exadata_infrastructure_management_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_database_management_feature"],
    annotations=TOOL_ANNOTATIONS["enable_database_management_feature"],)
def enable_database_management_feature(
    database_id: str = Field(..., description='The OCID of the Database.'),
    enable_database_management_feature_details: dict[str, Any] | EnableDatabaseManagementFeatureDetails = Field(..., description='The details required to enable a Database Management feature for an Oracle cloud database.'),) -> Any:
    return invoke_dbm(
        'enable_database_management_feature',
        database_id=database_id,
        enable_database_management_feature_details=enable_database_management_feature_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_external_container_database_management_feature"],
    annotations=TOOL_ANNOTATIONS["enable_external_container_database_management_feature"],)
def enable_external_container_database_management_feature(
    external_container_database_id: str = Field(..., description='The OCID of the external container database.'),
    enable_external_container_database_management_feature_details: dict[str, Any] | EnableExternalContainerDatabaseManagementFeatureDetails = Field(..., description='The details required to enable a Database Management feature for an external container database.'),) -> Any:
    return invoke_dbm(
        'enable_external_container_database_management_feature',
        external_container_database_id=external_container_database_id,
        enable_external_container_database_management_feature_details=enable_external_container_database_management_feature_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_external_db_system_database_management"],
    annotations=TOOL_ANNOTATIONS["enable_external_db_system_database_management"],)
def enable_external_db_system_database_management(
    external_db_system_id: str = Field(..., description='The OCID of the external DB system.'),
    enable_external_db_system_database_management_details: dict[str, Any] | EnableExternalDbSystemDatabaseManagementDetails = Field(..., description='The details required to enable Database Management for an external DB system.'),) -> Any:
    return invoke_dbm(
        'enable_external_db_system_database_management',
        external_db_system_id=external_db_system_id,
        enable_external_db_system_database_management_details=enable_external_db_system_database_management_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_external_db_system_stack_monitoring"],
    annotations=TOOL_ANNOTATIONS["enable_external_db_system_stack_monitoring"],)
def enable_external_db_system_stack_monitoring(
    external_db_system_id: str = Field(..., description='The OCID of the external DB system.'),
    enable_external_db_system_stack_monitoring_details: dict[str, Any] | EnableExternalDbSystemStackMonitoringDetails = Field(..., description='The details required to enable Stack Monitoring for an external DB system.'),) -> Any:
    return invoke_dbm(
        'enable_external_db_system_stack_monitoring',
        external_db_system_id=external_db_system_id,
        enable_external_db_system_stack_monitoring_details=enable_external_db_system_stack_monitoring_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_external_exadata_infrastructure_management"],
    annotations=TOOL_ANNOTATIONS["enable_external_exadata_infrastructure_management"],)
def enable_external_exadata_infrastructure_management(
    external_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),
    enable_external_exadata_infrastructure_management_details: dict[str, Any] | EnableExternalExadataInfrastructureManagementDetails = Field(..., description='The details required to enable management for the Exadata infrastructure.'),) -> Any:
    return invoke_dbm(
        'enable_external_exadata_infrastructure_management',
        external_exadata_infrastructure_id=external_exadata_infrastructure_id,
        enable_external_exadata_infrastructure_management_details=enable_external_exadata_infrastructure_management_details,)




@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_external_non_container_database_management_feature"],
    annotations=TOOL_ANNOTATIONS["enable_external_non_container_database_management_feature"],)
def enable_external_non_container_database_management_feature(
    external_non_container_database_id: str = Field(..., description='The OCID of the external non-container database.'),
    enable_external_non_container_database_management_feature_details: dict[str, Any] | EnableExternalNonContainerDatabaseManagementFeatureDetails = Field(..., description='The details required to enable a Database Management feature for an external non-container database.'),) -> Any:
    return invoke_dbm(
        'enable_external_non_container_database_management_feature',
        external_non_container_database_id=external_non_container_database_id,
        enable_external_non_container_database_management_feature_details=enable_external_non_container_database_management_feature_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_external_pluggable_database_management_feature"],
    annotations=TOOL_ANNOTATIONS["enable_external_pluggable_database_management_feature"],)
def enable_external_pluggable_database_management_feature(
    external_pluggable_database_id: str = Field(..., description='The OCID of the external pluggable database.'),
    enable_external_pluggable_database_management_feature_details: dict[str, Any] | EnableExternalPluggableDatabaseManagementFeatureDetails = Field(..., description='The details required to enable a Database Management feature for an external pluggable database.'),) -> Any:
    return invoke_dbm(
        'enable_external_pluggable_database_management_feature',
        external_pluggable_database_id=external_pluggable_database_id,
        enable_external_pluggable_database_management_feature_details=enable_external_pluggable_database_management_feature_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_high_frequency_automatic_spm_evolve_advisor_task"],
    annotations=TOOL_ANNOTATIONS["enable_high_frequency_automatic_spm_evolve_advisor_task"],)
def enable_high_frequency_automatic_spm_evolve_advisor_task(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    enable_high_frequency_automatic_spm_evolve_advisor_task_details: dict[str, Any] | EnableHighFrequencyAutomaticSpmEvolveAdvisorTaskDetails = Field(..., description='The details required to enable high frequency Automatic SPM Evolve Advisor task.'),) -> Any:
    return invoke_dbm(
        'enable_high_frequency_automatic_spm_evolve_advisor_task',
        managed_database_id=managed_database_id,
        enable_high_frequency_automatic_spm_evolve_advisor_task_details=enable_high_frequency_automatic_spm_evolve_advisor_task_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_pluggable_database_management_feature"],
    annotations=TOOL_ANNOTATIONS["enable_pluggable_database_management_feature"],)
def enable_pluggable_database_management_feature(
    pluggable_database_id: str = Field(..., description='The OCID of the Oracle cloud pluggable database.'),
    enable_pluggable_database_management_feature_details: dict[str, Any] | EnablePluggableDatabaseManagementFeatureDetails = Field(..., description='The details required to enable a Database Management feature for an Oracle cloud pluggable database.'),) -> Any:
    return invoke_dbm(
        'enable_pluggable_database_management_feature',
        pluggable_database_id=pluggable_database_id,
        enable_pluggable_database_management_feature_details=enable_pluggable_database_management_feature_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["enable_sql_plan_baselines_usage"],
    annotations=TOOL_ANNOTATIONS["enable_sql_plan_baselines_usage"],)
def enable_sql_plan_baselines_usage(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    enable_sql_plan_baselines_usage_details: dict[str, Any] | EnableSqlPlanBaselinesUsageDetails = Field(..., description='The details required to enable SQL plan baseline usage.'),) -> Any:
    return invoke_dbm(
        'enable_sql_plan_baselines_usage',
        managed_database_id=managed_database_id,
        enable_sql_plan_baselines_usage_details=enable_sql_plan_baselines_usage_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["generate_awr_snapshot"],
    annotations=TOOL_ANNOTATIONS["generate_awr_snapshot"],)
def generate_awr_snapshot(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'generate_awr_snapshot',
        managed_database_id=managed_database_id,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_awr_db_report"],
    annotations=TOOL_ANNOTATIONS["get_awr_db_report"],)
def get_awr_db_report(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    awr_db_id: str = Field(..., description='Internal AWR database identifier within the managed database. This value is not an OCID; use the identifier returned by AWR database listing results.'),
    inst_nums: list[int] | None = Field(None, description='The optional multiple value query parameter to filter the database instance numbers.'),
    begin_sn_id_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_sn_id_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot ID.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    report_type: Literal['AWR', 'ASH'] | None = Field(None, description='The query parameter to filter the AWR report types.\n\nAllowed values are: "AWR", "ASH"'),
    container_id: int | None = Field(None, description='AWR database container identifier. This value is not an OCID; use container identifiers returned by AWR snapshot range results.'),
    report_format: Literal['HTML', 'TEXT'] | None = Field(None, description='The format of the AWR report.\n\nAllowed values are: "HTML", "TEXT"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_awr_db_report',
        managed_database_id=managed_database_id,
        awr_db_id=awr_db_id,
        inst_nums=inst_nums,
        begin_sn_id_greater_than_or_equal_to=begin_sn_id_greater_than_or_equal_to,
        end_sn_id_less_than_or_equal_to=end_sn_id_less_than_or_equal_to,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        report_type=report_type,
        container_id=container_id,
        report_format=report_format,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_awr_db_sql_report"],
    annotations=TOOL_ANNOTATIONS["get_awr_db_sql_report"],)
def get_awr_db_sql_report(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    awr_db_id: str = Field(..., description='Internal AWR database identifier within the managed database. This value is not an OCID; use the identifier returned by AWR database listing results.'),
    sql_id: str = Field(..., description='Oracle-generated SQL ID for a SQL statement in AWR or Performance Hub data.'),
    inst_num: str | None = Field(None, description='The optional single value query parameter to filter the database instance number.'),
    begin_sn_id_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_sn_id_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot ID.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    report_format: Literal['HTML', 'TEXT'] | None = Field(None, description='The format of the AWR report.\n\nAllowed values are: "HTML", "TEXT"'),
    container_id: int | None = Field(None, description='AWR database container identifier. This value is not an OCID; use container identifiers returned by AWR snapshot range results.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_awr_db_sql_report',
        managed_database_id=managed_database_id,
        awr_db_id=awr_db_id,
        sql_id=sql_id,
        inst_num=inst_num,
        begin_sn_id_greater_than_or_equal_to=begin_sn_id_greater_than_or_equal_to,
        end_sn_id_less_than_or_equal_to=end_sn_id_less_than_or_equal_to,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        report_format=report_format,
        container_id=container_id,
        opc_named_credential_id=opc_named_credential_id,)




@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_asm"],
    annotations=TOOL_ANNOTATIONS["get_cloud_asm"],)
def get_cloud_asm(
    cloud_asm_id: str = Field(..., description='The OCID of the cloud ASM.'),) -> Any:
    return invoke_dbm(
        'get_cloud_asm',
        cloud_asm_id=cloud_asm_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_asm_configuration"],
    annotations=TOOL_ANNOTATIONS["get_cloud_asm_configuration"],)
def get_cloud_asm_configuration(
    cloud_asm_id: str = Field(..., description='The OCID of the cloud ASM.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_cloud_asm_configuration',
        cloud_asm_id=cloud_asm_id,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_asm_instance"],
    annotations=TOOL_ANNOTATIONS["get_cloud_asm_instance"],)
def get_cloud_asm_instance(
    cloud_asm_instance_id: str = Field(..., description='The OCID of the cloud ASM instance.'),) -> Any:
    return invoke_dbm(
        'get_cloud_asm_instance',
        cloud_asm_instance_id=cloud_asm_instance_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_cluster"],
    annotations=TOOL_ANNOTATIONS["get_cloud_cluster"],)
def get_cloud_cluster(
    cloud_cluster_id: str = Field(..., description='The OCID of the cloud cluster.'),) -> Any:
    return invoke_dbm(
        'get_cloud_cluster',
        cloud_cluster_id=cloud_cluster_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_cluster_instance"],
    annotations=TOOL_ANNOTATIONS["get_cloud_cluster_instance"],)
def get_cloud_cluster_instance(
    cloud_cluster_instance_id: str = Field(..., description='The OCID of the cloud cluster instance.'),) -> Any:
    return invoke_dbm(
        'get_cloud_cluster_instance',
        cloud_cluster_instance_id=cloud_cluster_instance_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_db_home"],
    annotations=TOOL_ANNOTATIONS["get_cloud_db_home"],)
def get_cloud_db_home(
    cloud_db_home_id: str = Field(..., description='The OCID of the cloud database home.'),) -> Any:
    return invoke_dbm(
        'get_cloud_db_home',
        cloud_db_home_id=cloud_db_home_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_db_node"],
    annotations=TOOL_ANNOTATIONS["get_cloud_db_node"],)
def get_cloud_db_node(
    cloud_db_node_id: str = Field(..., description='The OCID of the cloud database node.'),) -> Any:
    return invoke_dbm(
        'get_cloud_db_node',
        cloud_db_node_id=cloud_db_node_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_db_system"],
    annotations=TOOL_ANNOTATIONS["get_cloud_db_system"],)
def get_cloud_db_system(
    cloud_db_system_id: str = Field(..., description='The OCID of the cloud DB system.'),) -> Any:
    return invoke_dbm(
        'get_cloud_db_system',
        cloud_db_system_id=cloud_db_system_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_db_system_connector"],
    annotations=TOOL_ANNOTATIONS["get_cloud_db_system_connector"],)
def get_cloud_db_system_connector(
    cloud_db_system_connector_id: str = Field(..., description='The OCID of the cloud connector.'),) -> Any:
    return invoke_dbm(
        'get_cloud_db_system_connector',
        cloud_db_system_connector_id=cloud_db_system_connector_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_db_system_discovery"],
    annotations=TOOL_ANNOTATIONS["get_cloud_db_system_discovery"],)
def get_cloud_db_system_discovery(
    cloud_db_system_discovery_id: str = Field(..., description='The OCID of the cloud DB system discovery.'),) -> Any:
    return invoke_dbm(
        'get_cloud_db_system_discovery',
        cloud_db_system_discovery_id=cloud_db_system_discovery_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_exadata_infrastructure"],
    annotations=TOOL_ANNOTATIONS["get_cloud_exadata_infrastructure"],)
def get_cloud_exadata_infrastructure(
    cloud_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),) -> Any:
    return invoke_dbm(
        'get_cloud_exadata_infrastructure',
        cloud_exadata_infrastructure_id=cloud_exadata_infrastructure_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_exadata_storage_connector"],
    annotations=TOOL_ANNOTATIONS["get_cloud_exadata_storage_connector"],)
def get_cloud_exadata_storage_connector(
    cloud_exadata_storage_connector_id: str = Field(..., description='The OCID of the connector to the Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'get_cloud_exadata_storage_connector',
        cloud_exadata_storage_connector_id=cloud_exadata_storage_connector_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_exadata_storage_grid"],
    annotations=TOOL_ANNOTATIONS["get_cloud_exadata_storage_grid"],)
def get_cloud_exadata_storage_grid(
    cloud_exadata_storage_grid_id: str = Field(..., description='The OCID of the Exadata storage grid.'),) -> Any:
    return invoke_dbm(
        'get_cloud_exadata_storage_grid',
        cloud_exadata_storage_grid_id=cloud_exadata_storage_grid_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_exadata_storage_server"],
    annotations=TOOL_ANNOTATIONS["get_cloud_exadata_storage_server"],)
def get_cloud_exadata_storage_server(
    cloud_exadata_storage_server_id: str = Field(..., description='The OCID of the Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'get_cloud_exadata_storage_server',
        cloud_exadata_storage_server_id=cloud_exadata_storage_server_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_iorm_plan"],
    annotations=TOOL_ANNOTATIONS["get_cloud_iorm_plan"],)
def get_cloud_iorm_plan(
    cloud_exadata_storage_server_id: str = Field(..., description='The OCID of the Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'get_cloud_iorm_plan',
        cloud_exadata_storage_server_id=cloud_exadata_storage_server_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_listener"],
    annotations=TOOL_ANNOTATIONS["get_cloud_listener"],)
def get_cloud_listener(
    cloud_listener_id: str = Field(..., description='The OCID of the cloud listener.'),) -> Any:
    return invoke_dbm(
        'get_cloud_listener',
        cloud_listener_id=cloud_listener_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cloud_open_alert_history"],
    annotations=TOOL_ANNOTATIONS["get_cloud_open_alert_history"],)
def get_cloud_open_alert_history(
    cloud_exadata_storage_server_id: str = Field(..., description='The OCID of the Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'get_cloud_open_alert_history',
        cloud_exadata_storage_server_id=cloud_exadata_storage_server_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_cluster_cache_metric"],
    annotations=TOOL_ANNOTATIONS["get_cluster_cache_metric"],)
def get_cluster_cache_metric(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    start_time: str = Field(..., description='The start time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    end_time: str = Field(..., description='The end time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),) -> Any:
    return invoke_dbm(
        'get_cluster_cache_metric',
        managed_database_id=managed_database_id,
        start_time=start_time,
        end_time=end_time,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_database_fleet_backup_metrics"],
    annotations=TOOL_ANNOTATIONS["get_database_fleet_backup_metrics"],)
def get_database_fleet_backup_metrics(
    database_hosted_in: Literal['CLOUD', 'EXTERNAL'] = Field(..., description='Indicates whether the database is a cloud database or an external database.\n\nAllowed values are: "CLOUD", "EXTERNAL"'),
    start_time: str = Field(..., description='The start time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    end_time: str = Field(..., description='The end time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    managed_database_group_id: str | None = Field(None, description='The OCID of the Managed Database Group.'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['DATABASENAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The\ndefault sort order for `DATABASENAME` is ascending and it is case-sensitive.\n\nAllowed values are: "DATABASENAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'get_database_fleet_backup_metrics',
        database_hosted_in=database_hosted_in,
        start_time=start_time,
        end_time=end_time,
        managed_database_group_id=managed_database_group_id,
        compartment_id=compartment_id,
        filter_by_metric_names=filter_by_metric_names,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_database_fleet_dataguard_metrics"],
    annotations=TOOL_ANNOTATIONS["get_database_fleet_dataguard_metrics"],)
def get_database_fleet_dataguard_metrics(
    managed_database_group_id: str | None = Field(None, description='The OCID of the Managed Database Group.'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['DATABASENAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The\ndefault sort order for `DATABASENAME` is ascending and it is case-sensitive.\n\nAllowed values are: "DATABASENAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'get_database_fleet_dataguard_metrics',
        managed_database_group_id=managed_database_group_id,
        compartment_id=compartment_id,
        filter_by_metric_names=filter_by_metric_names,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_database_fleet_ha_overview_metrics"],
    annotations=TOOL_ANNOTATIONS["get_database_fleet_ha_overview_metrics"],)
def get_database_fleet_ha_overview_metrics(
    managed_database_group_id: str | None = Field(None, description='The OCID of the Managed Database Group.'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['DATABASENAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The\ndefault sort order for `DATABASENAME` is ascending and it is case-sensitive.\n\nAllowed values are: "DATABASENAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'get_database_fleet_ha_overview_metrics',
        managed_database_group_id=managed_database_group_id,
        compartment_id=compartment_id,
        filter_by_metric_names=filter_by_metric_names,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_database_fleet_health_metrics"],
    annotations=TOOL_ANNOTATIONS["get_database_fleet_health_metrics"],)
def get_database_fleet_health_metrics(
    compare_baseline_time: str = Field(..., description='The baseline time for metrics comparison.'),
    compare_target_time: str = Field(..., description='The target time for metrics comparison.'),
    managed_database_group_id: str | None = Field(None, description='The OCID of the Managed Database Group.'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    compare_type: Literal['HOUR', 'DAY', 'WEEK'] | None = Field(None, description='The time window used for metrics comparison.\n\nAllowed values are: "HOUR", "DAY", "WEEK"'),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),
    filter_by_database_type: str | None = Field(None, description='The filter used to filter the databases in the fleet by a specific Oracle Database type.'),
    filter_by_database_sub_type: str | None = Field(None, description='The filter used to filter the databases in the fleet by a specific Oracle Database subtype.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    filter_by_database_deployment_type: str | None = Field(None, description='The filter used to filter the databases in the fleet by a specific Oracle Database deployment type.'),
    filter_by_database_version: str | None = Field(None, description='The filter used to filter the databases in the fleet by a specific Oracle Database version.'),) -> Any:
    return invoke_dbm(
        'get_database_fleet_health_metrics',
        compare_baseline_time=compare_baseline_time,
        compare_target_time=compare_target_time,
        managed_database_group_id=managed_database_group_id,
        compartment_id=compartment_id,
        compare_type=compare_type,
        filter_by_metric_names=filter_by_metric_names,
        filter_by_database_type=filter_by_database_type,
        filter_by_database_sub_type=filter_by_database_sub_type,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        filter_by_database_deployment_type=filter_by_database_deployment_type,
        filter_by_database_version=filter_by_database_version,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_database_ha_backup_details"],
    annotations=TOOL_ANNOTATIONS["get_database_ha_backup_details"],)
def get_database_ha_backup_details(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_database_ha_backup_details',
        managed_database_id=managed_database_id,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_database_home_metrics"],
    annotations=TOOL_ANNOTATIONS["get_database_home_metrics"],)
def get_database_home_metrics(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    start_time: str = Field(..., description='The start time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    end_time: str = Field(..., description='The end time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),) -> Any:
    return invoke_dbm(
        'get_database_home_metrics',
        managed_database_id=managed_database_id,
        start_time=start_time,
        end_time=end_time,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_dataguard_performance_metrics"],
    annotations=TOOL_ANNOTATIONS["get_dataguard_performance_metrics"],)
def get_dataguard_performance_metrics(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    start_time: str = Field(..., description='The start time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    end_time: str = Field(..., description='The end time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    peer_database_compartment_id: str | None = Field(None, description='The OCID of the compartment for which peer database metrics are required. This is not a mandatory parameter and in its absence, all the peer database metrics are returned.'),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),) -> Any:
    return invoke_dbm(
        'get_dataguard_performance_metrics',
        managed_database_id=managed_database_id,
        start_time=start_time,
        end_time=end_time,
        peer_database_compartment_id=peer_database_compartment_id,
        filter_by_metric_names=filter_by_metric_names,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_db_management_private_endpoint"],
    annotations=TOOL_ANNOTATIONS["get_db_management_private_endpoint"],)
def get_db_management_private_endpoint(
    db_management_private_endpoint_id: str = Field(..., description='The OCID of the Database Management private endpoint.'),) -> Any:
    return invoke_dbm(
        'get_db_management_private_endpoint',
        db_management_private_endpoint_id=db_management_private_endpoint_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_exadata_infrastructure_fleet_health_metrics"],
    annotations=TOOL_ANNOTATIONS["get_exadata_infrastructure_fleet_health_metrics"],)
def get_exadata_infrastructure_fleet_health_metrics(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    compare_baseline_time: str = Field(..., description='The baseline time for metrics comparison.'),
    compare_target_time: str = Field(..., description='The target time for metrics comparison.'),
    compare_type: Literal['HOUR', 'DAY', 'WEEK'] | None = Field(None, description='The time window used for metrics comparison.\n\nAllowed values are: "HOUR", "DAY", "WEEK"'),
    filter_by_exadata_infrastructure_deployment_type: Literal['ONPREMISE', 'EXADATA', 'EXADATA_CC'] | None = Field(None, description='The filter used to filter the Exadata infrastructures in the fleet by a specific deployment type.\n\nAllowed values are: "ONPREMISE", "EXADATA", "EXADATA_CC"'),
    filter_by_exadata_infrastructure_lifecycle_state: Literal['CREATING', 'ACTIVE', 'INACTIVE', 'UPDATING', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN'] | None = Field(None, description='The filter used to filter the Exadata infrastructure in the fleet by its lifecycle state.\nIf the parameter is not provided, Exdata infrastructures in any state are returned.\n\nAllowed values are: "CREATING", "ACTIVE", "INACTIVE", "UPDATING", "DELETING", "DELETED", "FAILED", "UNKNOWN"'),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'get_exadata_infrastructure_fleet_health_metrics',
        compartment_id=compartment_id,
        compare_baseline_time=compare_baseline_time,
        compare_target_time=compare_target_time,
        compare_type=compare_type,
        filter_by_exadata_infrastructure_deployment_type=filter_by_exadata_infrastructure_deployment_type,
        filter_by_exadata_infrastructure_lifecycle_state=filter_by_exadata_infrastructure_lifecycle_state,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_execution_plan_stats_comparision"],
    annotations=TOOL_ANNOTATIONS["get_execution_plan_stats_comparision"],)
def get_execution_plan_stats_comparision(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    sql_tuning_advisor_task_id: int = Field(..., description='The SQL tuning task identifier. This is not the OCID.'),
    sql_object_id: int = Field(..., description='The SQL object ID for the SQL tuning task. This is not the OCID.'),
    execution_id: int = Field(..., description='The execution ID for an execution of a SQL tuning task. This is not the OCID.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_execution_plan_stats_comparision',
        managed_database_id=managed_database_id,
        sql_tuning_advisor_task_id=sql_tuning_advisor_task_id,
        sql_object_id=sql_object_id,
        execution_id=execution_id,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_asm"],
    annotations=TOOL_ANNOTATIONS["get_external_asm"],)
def get_external_asm(
    external_asm_id: str = Field(..., description='The OCID of the external ASM.'),) -> Any:
    return invoke_dbm(
        'get_external_asm',
        external_asm_id=external_asm_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_asm_configuration"],
    annotations=TOOL_ANNOTATIONS["get_external_asm_configuration"],)
def get_external_asm_configuration(
    external_asm_id: str = Field(..., description='The OCID of the external ASM.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_external_asm_configuration',
        external_asm_id=external_asm_id,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_asm_instance"],
    annotations=TOOL_ANNOTATIONS["get_external_asm_instance"],)
def get_external_asm_instance(
    external_asm_instance_id: str = Field(..., description='The OCID of the external ASM instance.'),) -> Any:
    return invoke_dbm(
        'get_external_asm_instance',
        external_asm_instance_id=external_asm_instance_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_cluster"],
    annotations=TOOL_ANNOTATIONS["get_external_cluster"],)
def get_external_cluster(
    external_cluster_id: str = Field(..., description='The OCID of the external cluster.'),) -> Any:
    return invoke_dbm(
        'get_external_cluster',
        external_cluster_id=external_cluster_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_cluster_instance"],
    annotations=TOOL_ANNOTATIONS["get_external_cluster_instance"],)
def get_external_cluster_instance(
    external_cluster_instance_id: str = Field(..., description='The OCID of the external cluster instance.'),) -> Any:
    return invoke_dbm(
        'get_external_cluster_instance',
        external_cluster_instance_id=external_cluster_instance_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_db_home"],
    annotations=TOOL_ANNOTATIONS["get_external_db_home"],)
def get_external_db_home(
    external_db_home_id: str = Field(..., description='The OCID of the external database home.'),) -> Any:
    return invoke_dbm(
        'get_external_db_home',
        external_db_home_id=external_db_home_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_db_node"],
    annotations=TOOL_ANNOTATIONS["get_external_db_node"],)
def get_external_db_node(
    external_db_node_id: str = Field(..., description='The OCID of the external database node.'),) -> Any:
    return invoke_dbm(
        'get_external_db_node',
        external_db_node_id=external_db_node_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_db_system"],
    annotations=TOOL_ANNOTATIONS["get_external_db_system"],)
def get_external_db_system(
    external_db_system_id: str = Field(..., description='The OCID of the external DB system.'),) -> Any:
    return invoke_dbm(
        'get_external_db_system',
        external_db_system_id=external_db_system_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_db_system_connector"],
    annotations=TOOL_ANNOTATIONS["get_external_db_system_connector"],)
def get_external_db_system_connector(
    external_db_system_connector_id: str = Field(..., description='The OCID of the external connector.'),) -> Any:
    return invoke_dbm(
        'get_external_db_system_connector',
        external_db_system_connector_id=external_db_system_connector_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_db_system_discovery"],
    annotations=TOOL_ANNOTATIONS["get_external_db_system_discovery"],)
def get_external_db_system_discovery(
    external_db_system_discovery_id: str = Field(..., description='The OCID of the external DB system discovery.'),) -> Any:
    return invoke_dbm(
        'get_external_db_system_discovery',
        external_db_system_discovery_id=external_db_system_discovery_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_exadata_infrastructure"],
    annotations=TOOL_ANNOTATIONS["get_external_exadata_infrastructure"],)
def get_external_exadata_infrastructure(
    external_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),) -> Any:
    return invoke_dbm(
        'get_external_exadata_infrastructure',
        external_exadata_infrastructure_id=external_exadata_infrastructure_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_exadata_storage_connector"],
    annotations=TOOL_ANNOTATIONS["get_external_exadata_storage_connector"],)
def get_external_exadata_storage_connector(
    external_exadata_storage_connector_id: str = Field(..., description='The OCID of the connector to the Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'get_external_exadata_storage_connector',
        external_exadata_storage_connector_id=external_exadata_storage_connector_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_exadata_storage_grid"],
    annotations=TOOL_ANNOTATIONS["get_external_exadata_storage_grid"],)
def get_external_exadata_storage_grid(
    external_exadata_storage_grid_id: str = Field(..., description='The OCID of the Exadata storage grid.'),) -> Any:
    return invoke_dbm(
        'get_external_exadata_storage_grid',
        external_exadata_storage_grid_id=external_exadata_storage_grid_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_exadata_storage_server"],
    annotations=TOOL_ANNOTATIONS["get_external_exadata_storage_server"],)
def get_external_exadata_storage_server(
    external_exadata_storage_server_id: str = Field(..., description='The OCID of the Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'get_external_exadata_storage_server',
        external_exadata_storage_server_id=external_exadata_storage_server_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_external_listener"],
    annotations=TOOL_ANNOTATIONS["get_external_listener"],)
def get_external_listener(
    external_listener_id: str = Field(..., description='The OCID of the external listener.'),) -> Any:
    return invoke_dbm(
        'get_external_listener',
        external_listener_id=external_listener_id,)










@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_iorm_plan"],
    annotations=TOOL_ANNOTATIONS["get_iorm_plan"],)
def get_iorm_plan(
    external_exadata_storage_server_id: str = Field(..., description='The OCID of the Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'get_iorm_plan',
        external_exadata_storage_server_id=external_exadata_storage_server_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_job"],
    annotations=TOOL_ANNOTATIONS["get_job"],)
def get_job(
    job_id: str = Field(..., description='The identifier of the job.'),) -> Any:
    return invoke_dbm(
        'get_job',
        job_id=job_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_job_execution"],
    annotations=TOOL_ANNOTATIONS["get_job_execution"],)
def get_job_execution(
    job_execution_id: str = Field(..., description='The identifier of the job execution.'),) -> Any:
    return invoke_dbm(
        'get_job_execution',
        job_execution_id=job_execution_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_job_run"],
    annotations=TOOL_ANNOTATIONS["get_job_run"],)
def get_job_run(
    job_run_id: str = Field(..., description='The identifier of the job run.'),) -> Any:
    return invoke_dbm(
        'get_job_run',
        job_run_id=job_run_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_managed_database"],
    annotations=TOOL_ANNOTATIONS["get_managed_database"],)
def get_managed_database(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),) -> Any:
    return invoke_dbm(
        'get_managed_database',
        managed_database_id=managed_database_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_managed_database_group"],
    annotations=TOOL_ANNOTATIONS["get_managed_database_group"],)
def get_managed_database_group(
    managed_database_group_id: str = Field(..., description='The OCID of the Managed Database Group.'),) -> Any:
    return invoke_dbm(
        'get_managed_database_group',
        managed_database_group_id=managed_database_group_id,)








@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_named_credential"],
    annotations=TOOL_ANNOTATIONS["get_named_credential"],)
def get_named_credential(
    named_credential_id: str = Field(..., description='The OCID of the named credential.'),) -> Any:
    return invoke_dbm(
        'get_named_credential',
        named_credential_id=named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_open_alert_history"],
    annotations=TOOL_ANNOTATIONS["get_open_alert_history"],)
def get_open_alert_history(
    external_exadata_storage_server_id: str = Field(..., description='The OCID of the Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'get_open_alert_history',
        external_exadata_storage_server_id=external_exadata_storage_server_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_optimizer_statistics_advisor_execution"],
    annotations=TOOL_ANNOTATIONS["get_optimizer_statistics_advisor_execution"],)
def get_optimizer_statistics_advisor_execution(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    execution_name: str = Field(..., description='The name of the Optimizer Statistics Advisor execution.'),
    task_name: str = Field(..., description='The name of the optimizer statistics collection execution task.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_optimizer_statistics_advisor_execution',
        managed_database_id=managed_database_id,
        execution_name=execution_name,
        task_name=task_name,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_optimizer_statistics_advisor_execution_script"],
    annotations=TOOL_ANNOTATIONS["get_optimizer_statistics_advisor_execution_script"],)
def get_optimizer_statistics_advisor_execution_script(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    execution_name: str = Field(..., description='The name of the Optimizer Statistics Advisor execution.'),
    task_name: str = Field(..., description='The name of the optimizer statistics collection execution task.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_optimizer_statistics_advisor_execution_script',
        managed_database_id=managed_database_id,
        execution_name=execution_name,
        task_name=task_name,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_optimizer_statistics_collection_operation"],
    annotations=TOOL_ANNOTATIONS["get_optimizer_statistics_collection_operation"],)
def get_optimizer_statistics_collection_operation(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    optimizer_statistics_collection_operation_id: float = Field(..., description='The ID of the Optimizer Statistics Collection operation.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_optimizer_statistics_collection_operation',
        managed_database_id=managed_database_id,
        optimizer_statistics_collection_operation_id=optimizer_statistics_collection_operation_id,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_pdb_metrics"],
    annotations=TOOL_ANNOTATIONS["get_pdb_metrics"],)
def get_pdb_metrics(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    start_time: str = Field(..., description='The start time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    end_time: str = Field(..., description='The end time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    compare_type: Literal['HOUR', 'DAY', 'WEEK'] | None = Field(None, description='The time window used for metrics comparison.\n\nAllowed values are: "HOUR", "DAY", "WEEK"'),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),) -> Any:
    return invoke_dbm(
        'get_pdb_metrics',
        managed_database_id=managed_database_id,
        start_time=start_time,
        end_time=end_time,
        compartment_id=compartment_id,
        compare_type=compare_type,
        filter_by_metric_names=filter_by_metric_names,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_peer_database_metrics"],
    annotations=TOOL_ANNOTATIONS["get_peer_database_metrics"],)
def get_peer_database_metrics(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    start_time: str = Field(..., description='The start time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    end_time: str = Field(..., description='The end time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    peer_database_compartment_id: str | None = Field(None, description='The OCID of the compartment for which peer database metrics are required. This is not a mandatory parameter and in its absence, all the peer database metrics are returned.'),
    compare_type: Literal['HOUR', 'DAY', 'WEEK'] | None = Field(None, description='The time window used for metrics comparison.\n\nAllowed values are: "HOUR", "DAY", "WEEK"'),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),) -> Any:
    return invoke_dbm(
        'get_peer_database_metrics',
        managed_database_id=managed_database_id,
        start_time=start_time,
        end_time=end_time,
        peer_database_compartment_id=peer_database_compartment_id,
        compare_type=compare_type,
        filter_by_metric_names=filter_by_metric_names,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_preferred_credential"],
    annotations=TOOL_ANNOTATIONS["get_preferred_credential"],)
def get_preferred_credential(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    credential_name: str = Field(..., description='The name of the preferred credential.'),) -> Any:
    return invoke_dbm(
        'get_preferred_credential',
        managed_database_id=managed_database_id,
        credential_name=credential_name,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_sql_execution_plan"],
    annotations=TOOL_ANNOTATIONS["get_sql_execution_plan"],)
def get_sql_execution_plan(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    sql_tuning_advisor_task_id: int = Field(..., description='The SQL tuning task identifier. This is not the OCID.'),
    sql_object_id: int = Field(..., description='The SQL object ID for the SQL tuning task. This is not the OCID.'),
    attribute: Literal['ORIGINAL', 'ORIGINAL_WITH_ADJUSTED_COST', 'USING_SQL_PROFILE', 'USING_NEW_INDICES', 'USING_PARALLEL_EXECUTION'] = Field(..., description='The attribute of the SQL execution plan.\n\nAllowed values are: "ORIGINAL", "ORIGINAL_WITH_ADJUSTED_COST", "USING_SQL_PROFILE", "USING_NEW_INDICES", "USING_PARALLEL_EXECUTION"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_sql_execution_plan',
        managed_database_id=managed_database_id,
        sql_tuning_advisor_task_id=sql_tuning_advisor_task_id,
        sql_object_id=sql_object_id,
        attribute=attribute,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_sql_plan_baseline"],
    annotations=TOOL_ANNOTATIONS["get_sql_plan_baseline"],)
def get_sql_plan_baseline(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    plan_name: str = Field(..., description='The plan name of the SQL plan baseline.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_sql_plan_baseline',
        managed_database_id=managed_database_id,
        plan_name=plan_name,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_sql_plan_baseline_configuration"],
    annotations=TOOL_ANNOTATIONS["get_sql_plan_baseline_configuration"],)
def get_sql_plan_baseline_configuration(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_sql_plan_baseline_configuration',
        managed_database_id=managed_database_id,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_sql_tuning_advisor_task_summary_report"],
    annotations=TOOL_ANNOTATIONS["get_sql_tuning_advisor_task_summary_report"],)
def get_sql_tuning_advisor_task_summary_report(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    sql_tuning_advisor_task_id: int = Field(..., description='The SQL tuning task identifier. This is not the OCID.'),
    search_period: Literal['LAST_24HR', 'LAST_7DAY', 'LAST_31DAY', 'SINCE_LAST', 'ALL'] | None = Field(None, description='How far back the API will search for begin and end exec id. Unused if neither exec ids nor time filter query params are supplied. This is applicable only for Auto SQL Tuning tasks.\n\nAllowed values are: "LAST_24HR", "LAST_7DAY", "LAST_31DAY", "SINCE_LAST", "ALL"'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp. This is applicable only for Auto SQL Tuning tasks.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp. This is applicable only for Auto SQL Tuning tasks.'),
    begin_exec_id_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the execution ID related to a specific SQL Tuning Advisor task. This is applicable only for Auto SQL Tuning tasks.'),
    end_exec_id_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter on the execution ID related to a specific SQL Tuning Advisor task. This is applicable only for Auto SQL Tuning tasks.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_sql_tuning_advisor_task_summary_report',
        managed_database_id=managed_database_id,
        sql_tuning_advisor_task_id=sql_tuning_advisor_task_id,
        search_period=search_period,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        begin_exec_id_greater_than_or_equal_to=begin_exec_id_greater_than_or_equal_to,
        end_exec_id_less_than_or_equal_to=end_exec_id_less_than_or_equal_to,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_tablespace"],
    annotations=TOOL_ANNOTATIONS["get_tablespace"],)
def get_tablespace(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    tablespace_name: str = Field(..., description='The name of the tablespace.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_tablespace',
        managed_database_id=managed_database_id,
        tablespace_name=tablespace_name,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_top_sql_cpu_activity"],
    annotations=TOOL_ANNOTATIONS["get_top_sql_cpu_activity"],)
def get_top_sql_cpu_activity(
    external_exadata_storage_server_id: str = Field(..., description='The OCID of the Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'get_top_sql_cpu_activity',
        external_exadata_storage_server_id=external_exadata_storage_server_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_user"],
    annotations=TOOL_ANNOTATIONS["get_user"],)
def get_user(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    user_name: str = Field(..., description='The name of the user whose details are to be viewed.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'get_user',
        managed_database_id=managed_database_id,
        user_name=user_name,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["get_work_request"],
    annotations=TOOL_ANNOTATIONS["get_work_request"],)
def get_work_request(
    work_request_id: str = Field(..., description='The OCID of the asynchronous work request.'),) -> Any:
    return invoke_dbm(
        'get_work_request',
        work_request_id=work_request_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_alert_logs"],
    annotations=TOOL_ANNOTATIONS["list_alert_logs"],)
def list_alert_logs(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to timestamp to filter the logs.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to timestamp to filter the logs.'),
    level_filter: Literal['CRITICAL', 'SEVERE', 'IMPORTANT', 'NORMAL', 'ALL'] | None = Field(None, description='The optional parameter to filter the alert logs by log level.\n\nAllowed values are: "CRITICAL", "SEVERE", "IMPORTANT", "NORMAL", "ALL"'),
    type_filter: Literal['UNKNOWN', 'INCIDENT_ERROR', 'ERROR', 'WARNING', 'NOTIFICATION', 'TRACE', 'ALL'] | None = Field(None, description='The optional parameter to filter the attention or alert logs by type.\n\nAllowed values are: "UNKNOWN", "INCIDENT_ERROR", "ERROR", "WARNING", "NOTIFICATION", "TRACE", "ALL"'),
    log_search_text: str | None = Field(None, description='The optional query parameter to filter the attention or alert logs by search text.'),
    is_regular_expression: bool | None = Field(None, description='The flag to indicate whether the search text is regular expression or not.'),
    sort_by: Literal['LEVEL', 'TYPE', 'MESSAGE', 'TIMESTAMP'] | None = Field(None, description='The possible sortBy values of attention logs.\n\nAllowed values are: "LEVEL", "TYPE", "MESSAGE", "TIMESTAMP"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_alert_logs',
        managed_database_id=managed_database_id,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        level_filter=level_filter,
        type_filter=type_filter,
        log_search_text=log_search_text,
        is_regular_expression=is_regular_expression,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_asm_properties"],
    annotations=TOOL_ANNOTATIONS["list_asm_properties"],)
def list_asm_properties(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),) -> Any:
    return invoke_dbm(
        'list_asm_properties',
        managed_database_id=managed_database_id,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_associated_databases"],
    annotations=TOOL_ANNOTATIONS["list_associated_databases"],)
def list_associated_databases(
    db_management_private_endpoint_id: str = Field(..., description='The OCID of the Database Management private endpoint.'),
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    sort_by: Literal['timeRegistered'] | None = Field(None, description='The option to sort databases using a specific Database Management private endpoint.\n\nAllowed values are: "timeRegistered"'),) -> Any:
    return invoke_dbm(
        'list_associated_databases',
        db_management_private_endpoint_id=db_management_private_endpoint_id,
        compartment_id=compartment_id,
        limit=limit,
        sort_order=sort_order,
        sort_by=sort_by,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_attention_logs"],
    annotations=TOOL_ANNOTATIONS["list_attention_logs"],)
def list_attention_logs(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to timestamp to filter the logs.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to timestamp to filter the logs.'),
    urgency_filter: Literal['IMMEDIATE', 'SOON', 'DEFERRABLE', 'INFO', 'ALL'] | None = Field(None, description='The optional parameter to filter the attention logs by urgency.\n\nAllowed values are: "IMMEDIATE", "SOON", "DEFERRABLE", "INFO", "ALL"'),
    type_filter: Literal['UNKNOWN', 'INCIDENT_ERROR', 'ERROR', 'WARNING', 'NOTIFICATION', 'TRACE', 'ALL'] | None = Field(None, description='The optional parameter to filter the attention or alert logs by type.\n\nAllowed values are: "UNKNOWN", "INCIDENT_ERROR", "ERROR", "WARNING", "NOTIFICATION", "TRACE", "ALL"'),
    log_search_text: str | None = Field(None, description='The optional query parameter to filter the attention or alert logs by search text.'),
    is_regular_expression: bool | None = Field(None, description='The flag to indicate whether the search text is regular expression or not.'),
    sort_by: Literal['URGENCY', 'TYPE', 'MESSAGE', 'TIMESTAMP', 'SCOPE', 'TARGET_USER'] | None = Field(None, description='The possible sortBy values of attention logs.\n\nAllowed values are: "URGENCY", "TYPE", "MESSAGE", "TIMESTAMP", "SCOPE", "TARGET_USER"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_attention_logs',
        managed_database_id=managed_database_id,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        urgency_filter=urgency_filter,
        type_filter=type_filter,
        log_search_text=log_search_text,
        is_regular_expression=is_regular_expression,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_awr_db_snapshots"],
    annotations=TOOL_ANNOTATIONS["list_awr_db_snapshots"],)
def list_awr_db_snapshots(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    awr_db_id: str = Field(..., description='Internal AWR database identifier within the managed database. This value is not an OCID; use the identifier returned by AWR database listing results.'),
    inst_num: str | None = Field(None, description='The optional single value query parameter to filter the database instance number.'),
    begin_sn_id_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_sn_id_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot ID.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    container_id: int | None = Field(None, description='AWR database container identifier. This value is not an OCID; use container identifiers returned by AWR snapshot range results.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIME_BEGIN', 'SNAPSHOT_ID'] | None = Field(None, description='The option to sort the AWR snapshot summary data.\n\nAllowed values are: "TIME_BEGIN", "SNAPSHOT_ID"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_awr_db_snapshots',
        managed_database_id=managed_database_id,
        awr_db_id=awr_db_id,
        inst_num=inst_num,
        begin_sn_id_greater_than_or_equal_to=begin_sn_id_greater_than_or_equal_to,
        end_sn_id_less_than_or_equal_to=end_sn_id_less_than_or_equal_to,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        container_id=container_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_awr_dbs"],
    annotations=TOOL_ANNOTATIONS["list_awr_dbs"],)
def list_awr_dbs(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    name: str | None = Field(None, description='The optional single value query parameter to filter the entity name.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['END_INTERVAL_TIME', 'NAME'] | None = Field(None, description='The option to sort the AWR summary data.\n\nAllowed values are: "END_INTERVAL_TIME", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_awr_dbs',
        managed_database_id=managed_database_id,
        name=name,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_asm_disk_groups"],
    annotations=TOOL_ANNOTATIONS["list_cloud_asm_disk_groups"],)
def list_cloud_asm_disk_groups(
    cloud_asm_id: str = Field(..., description='The OCID of the cloud ASM.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The\ndefault sort order for `NAME` is ascending and it is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_cloud_asm_disk_groups',
        cloud_asm_id=cloud_asm_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_asm_instances"],
    annotations=TOOL_ANNOTATIONS["list_cloud_asm_instances"],)
def list_cloud_asm_instances(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    cloud_asm_id: str | None = Field(None, description='The OCID of the cloud ASM.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_asm_instances',
        compartment_id=compartment_id,
        cloud_asm_id=cloud_asm_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_asm_users"],
    annotations=TOOL_ANNOTATIONS["list_cloud_asm_users"],)
def list_cloud_asm_users(
    cloud_asm_id: str = Field(..., description='The OCID of the cloud ASM.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The\ndefault sort order for `NAME` is ascending and it is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_cloud_asm_users',
        cloud_asm_id=cloud_asm_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_asms"],
    annotations=TOOL_ANNOTATIONS["list_cloud_asms"],)
def list_cloud_asms(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    cloud_db_system_id: str | None = Field(None, description='The OCID of the cloud DB system.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_asms',
        compartment_id=compartment_id,
        cloud_db_system_id=cloud_db_system_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_cluster_instances"],
    annotations=TOOL_ANNOTATIONS["list_cloud_cluster_instances"],)
def list_cloud_cluster_instances(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    cloud_cluster_id: str | None = Field(None, description='The OCID of the cloud cluster.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_cluster_instances',
        compartment_id=compartment_id,
        cloud_cluster_id=cloud_cluster_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_clusters"],
    annotations=TOOL_ANNOTATIONS["list_cloud_clusters"],)
def list_cloud_clusters(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    cloud_db_system_id: str | None = Field(None, description='The OCID of the cloud DB system.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_clusters',
        compartment_id=compartment_id,
        cloud_db_system_id=cloud_db_system_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_databases"],
    annotations=TOOL_ANNOTATIONS["list_cloud_databases"],)
def list_cloud_databases(
    cloud_db_system_id: str = Field(..., description='The OCID of the cloud DB system.'),
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_databases',
        cloud_db_system_id=cloud_db_system_id,
        compartment_id=compartment_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_db_homes"],
    annotations=TOOL_ANNOTATIONS["list_cloud_db_homes"],)
def list_cloud_db_homes(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    cloud_db_system_id: str | None = Field(None, description='The OCID of the cloud DB system.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_db_homes',
        compartment_id=compartment_id,
        cloud_db_system_id=cloud_db_system_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_db_nodes"],
    annotations=TOOL_ANNOTATIONS["list_cloud_db_nodes"],)
def list_cloud_db_nodes(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    cloud_db_system_id: str | None = Field(None, description='The OCID of the cloud DB system.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_db_nodes',
        compartment_id=compartment_id,
        cloud_db_system_id=cloud_db_system_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_db_system_connectors"],
    annotations=TOOL_ANNOTATIONS["list_cloud_db_system_connectors"],)
def list_cloud_db_system_connectors(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    cloud_db_system_id: str | None = Field(None, description='The OCID of the cloud DB system.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_db_system_connectors',
        compartment_id=compartment_id,
        cloud_db_system_id=cloud_db_system_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_db_system_discoveries"],
    annotations=TOOL_ANNOTATIONS["list_cloud_db_system_discoveries"],)
def list_cloud_db_system_discoveries(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_db_system_discoveries',
        compartment_id=compartment_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_db_systems"],
    annotations=TOOL_ANNOTATIONS["list_cloud_db_systems"],)
def list_cloud_db_systems(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    dbaas_parent_infrastructure_id: str | None = Field(None, description='The OCID of the dbaas parent infrastructure of the cloud DB system.'),
    deployment_type: Literal['VM', 'EXADATA', 'EXADATA_CC', 'EXADATA_XS'] | None = Field(None, description='A filter to return cloud DB systems of the specified deployment type.\n\nAllowed values are: "VM", "EXADATA", "EXADATA_CC", "EXADATA_XS"'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    lifecycle_state: Literal['CREATING', 'ACTIVE', 'UPDATING', 'DELETING', 'DELETED', 'INACTIVE'] | None = Field(None, description='The lifecycle state of a resource.\n\nAllowed values are: "CREATING", "ACTIVE", "UPDATING", "DELETING", "DELETED", "INACTIVE"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_db_systems',
        compartment_id=compartment_id,
        dbaas_parent_infrastructure_id=dbaas_parent_infrastructure_id,
        deployment_type=deployment_type,
        display_name=display_name,
        lifecycle_state=lifecycle_state,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_exadata_infrastructures"],
    annotations=TOOL_ANNOTATIONS["list_cloud_exadata_infrastructures"],)
def list_cloud_exadata_infrastructures(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    display_name: str | None = Field(None, description='The optional single value query filter parameter on the entity display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_exadata_infrastructures',
        compartment_id=compartment_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_exadata_storage_connectors"],
    annotations=TOOL_ANNOTATIONS["list_cloud_exadata_storage_connectors"],)
def list_cloud_exadata_storage_connectors(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    cloud_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),
    display_name: str | None = Field(None, description='The optional single value query filter parameter on the entity display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_exadata_storage_connectors',
        compartment_id=compartment_id,
        cloud_exadata_infrastructure_id=cloud_exadata_infrastructure_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_exadata_storage_servers"],
    annotations=TOOL_ANNOTATIONS["list_cloud_exadata_storage_servers"],)
def list_cloud_exadata_storage_servers(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    cloud_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),
    display_name: str | None = Field(None, description='The optional single value query filter parameter on the entity display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_exadata_storage_servers',
        compartment_id=compartment_id,
        cloud_exadata_infrastructure_id=cloud_exadata_infrastructure_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_listener_services"],
    annotations=TOOL_ANNOTATIONS["list_cloud_listener_services"],)
def list_cloud_listener_services(
    cloud_listener_id: str = Field(..., description='The OCID of the cloud listener.'),
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The\ndefault sort order for `NAME` is ascending and it is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_cloud_listener_services',
        cloud_listener_id=cloud_listener_id,
        managed_database_id=managed_database_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cloud_listeners"],
    annotations=TOOL_ANNOTATIONS["list_cloud_listeners"],)
def list_cloud_listeners(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    cloud_db_system_id: str | None = Field(None, description='The OCID of the cloud DB system.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_cloud_listeners',
        compartment_id=compartment_id,
        cloud_db_system_id=cloud_db_system_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_consumer_group_privileges"],
    annotations=TOOL_ANNOTATIONS["list_consumer_group_privileges"],)
def list_consumer_group_privileges(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    user_name: str = Field(..., description='The name of the user whose details are to be viewed.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘NAME’ is ascending. The ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_consumer_group_privileges',
        managed_database_id=managed_database_id,
        user_name=user_name,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_cursor_cache_statements"],
    annotations=TOOL_ANNOTATIONS["list_cursor_cache_statements"],)
def list_cursor_cache_statements(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    sql_text: str | None = Field(None, description="A filter to return all the SQL plan baselines that match the SQL text. By default, the search\nis case insensitive. To run an exact or case-sensitive search, double-quote the search string.\nYou may also use the '%' symbol as a wildcard."),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['sqlId', 'schema'] | None = Field(None, description='The option to sort the SQL statement summary data.\n\nAllowed values are: "sqlId", "schema"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_cursor_cache_statements',
        managed_database_id=managed_database_id,
        sql_text=sql_text,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_data_access_containers"],
    annotations=TOOL_ANNOTATIONS["list_data_access_containers"],)
def list_data_access_containers(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    user_name: str = Field(..., description='The name of the user whose details are to be viewed.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘NAME’ is ascending. The ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_data_access_containers',
        managed_database_id=managed_database_id,
        user_name=user_name,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_database_parameters"],
    annotations=TOOL_ANNOTATIONS["list_database_parameters"],)
def list_database_parameters(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    source: Literal['CURRENT', 'SPFILE'] | None = Field(None, description='The source used to list database parameters. `CURRENT` is used to get the\ndatabase parameters that are currently in effect for the database\ninstance. `SPFILE` is used to list parameters from the server parameter\nfile. Default is `CURRENT`.\n\nAllowed values are: "CURRENT", "SPFILE"'),
    name: str | None = Field(None, description='A filter to return all parameters that have the text given in their names.'),
    is_allowed_values_included: bool | None = Field(None, description='When true, results include a list of valid values for parameters (if applicable).'),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The\ndefault sort order for `NAME` is ascending and it is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_database_parameters',
        managed_database_id=managed_database_id,
        source=source,
        name=name,
        is_allowed_values_included=is_allowed_values_included,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_db_management_private_endpoints"],
    annotations=TOOL_ANNOTATIONS["list_db_management_private_endpoints"],)
def list_db_management_private_endpoints(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    vcn_id: str | None = Field(None, description='The OCID of the VCN.'),
    is_cluster: bool | None = Field(None, description='The option to filter Database Management private endpoints that can used for Oracle Databases in a cluster. This should be used along with the vcnId query parameter.'),
    is_dns_resolution_enabled: bool | None = Field(None, description='The option to filter Database Management private endpoints which are endbled with DNS proxy server. This should be used along with the vcnId query parameter.\nOnly one of this parameter and IsClusterDbManagementPrivateEndpointQueryParam should be set to true at one time.'),
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED'] | None = Field(None, description='The lifecycle state of a resource.\n\nAllowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),) -> Any:
    return invoke_dbm(
        'list_db_management_private_endpoints',
        compartment_id=compartment_id,
        name=name,
        vcn_id=vcn_id,
        is_cluster=is_cluster,
        is_dns_resolution_enabled=is_dns_resolution_enabled,
        lifecycle_state=lifecycle_state,
        limit=limit,
        sort_order=sort_order,
        sort_by=sort_by,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_asm_disk_groups"],
    annotations=TOOL_ANNOTATIONS["list_external_asm_disk_groups"],)
def list_external_asm_disk_groups(
    external_asm_id: str = Field(..., description='The OCID of the external ASM.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The\ndefault sort order for `NAME` is ascending and it is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_external_asm_disk_groups',
        external_asm_id=external_asm_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_asm_instances"],
    annotations=TOOL_ANNOTATIONS["list_external_asm_instances"],)
def list_external_asm_instances(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    external_asm_id: str | None = Field(None, description='The OCID of the external ASM.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_asm_instances',
        compartment_id=compartment_id,
        external_asm_id=external_asm_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_asm_users"],
    annotations=TOOL_ANNOTATIONS["list_external_asm_users"],)
def list_external_asm_users(
    external_asm_id: str = Field(..., description='The OCID of the external ASM.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The\ndefault sort order for `NAME` is ascending and it is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_external_asm_users',
        external_asm_id=external_asm_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_asms"],
    annotations=TOOL_ANNOTATIONS["list_external_asms"],)
def list_external_asms(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    external_db_system_id: str | None = Field(None, description='The OCID of the external DB system.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_asms',
        compartment_id=compartment_id,
        external_db_system_id=external_db_system_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_cluster_instances"],
    annotations=TOOL_ANNOTATIONS["list_external_cluster_instances"],)
def list_external_cluster_instances(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    external_cluster_id: str | None = Field(None, description='The OCID of the external cluster.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_cluster_instances',
        compartment_id=compartment_id,
        external_cluster_id=external_cluster_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_clusters"],
    annotations=TOOL_ANNOTATIONS["list_external_clusters"],)
def list_external_clusters(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    external_db_system_id: str | None = Field(None, description='The OCID of the external DB system.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_clusters',
        compartment_id=compartment_id,
        external_db_system_id=external_db_system_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_databases"],
    annotations=TOOL_ANNOTATIONS["list_external_databases"],)
def list_external_databases(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    external_db_system_id: str | None = Field(None, description='The OCID of the external DB system.'),
    external_database_id: str | None = Field(None, description='The OCID of the external database.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_databases',
        compartment_id=compartment_id,
        external_db_system_id=external_db_system_id,
        external_database_id=external_database_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_db_homes"],
    annotations=TOOL_ANNOTATIONS["list_external_db_homes"],)
def list_external_db_homes(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    external_db_system_id: str | None = Field(None, description='The OCID of the external DB system.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_db_homes',
        compartment_id=compartment_id,
        external_db_system_id=external_db_system_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_db_nodes"],
    annotations=TOOL_ANNOTATIONS["list_external_db_nodes"],)
def list_external_db_nodes(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    external_db_system_id: str | None = Field(None, description='The OCID of the external DB system.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_db_nodes',
        compartment_id=compartment_id,
        external_db_system_id=external_db_system_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_db_system_connectors"],
    annotations=TOOL_ANNOTATIONS["list_external_db_system_connectors"],)
def list_external_db_system_connectors(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    external_db_system_id: str | None = Field(None, description='The OCID of the external DB system.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_db_system_connectors',
        compartment_id=compartment_id,
        external_db_system_id=external_db_system_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_db_system_discoveries"],
    annotations=TOOL_ANNOTATIONS["list_external_db_system_discoveries"],)
def list_external_db_system_discoveries(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_db_system_discoveries',
        compartment_id=compartment_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_db_systems"],
    annotations=TOOL_ANNOTATIONS["list_external_db_systems"],)
def list_external_db_systems(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_db_systems',
        compartment_id=compartment_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_exadata_infrastructures"],
    annotations=TOOL_ANNOTATIONS["list_external_exadata_infrastructures"],)
def list_external_exadata_infrastructures(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    display_name: str | None = Field(None, description='The optional single value query filter parameter on the entity display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_exadata_infrastructures',
        compartment_id=compartment_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_exadata_storage_connectors"],
    annotations=TOOL_ANNOTATIONS["list_external_exadata_storage_connectors"],)
def list_external_exadata_storage_connectors(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    external_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),
    display_name: str | None = Field(None, description='The optional single value query filter parameter on the entity display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_exadata_storage_connectors',
        compartment_id=compartment_id,
        external_exadata_infrastructure_id=external_exadata_infrastructure_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_exadata_storage_servers"],
    annotations=TOOL_ANNOTATIONS["list_external_exadata_storage_servers"],)
def list_external_exadata_storage_servers(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    external_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),
    display_name: str | None = Field(None, description='The optional single value query filter parameter on the entity display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_exadata_storage_servers',
        compartment_id=compartment_id,
        external_exadata_infrastructure_id=external_exadata_infrastructure_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_listener_services"],
    annotations=TOOL_ANNOTATIONS["list_external_listener_services"],)
def list_external_listener_services(
    external_listener_id: str = Field(..., description='The OCID of the external listener.'),
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The\ndefault sort order for `NAME` is ascending and it is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_external_listener_services',
        external_listener_id=external_listener_id,
        managed_database_id=managed_database_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_external_listeners"],
    annotations=TOOL_ANNOTATIONS["list_external_listeners"],)
def list_external_listeners(
    compartment_id: str | None = Field(None, description='The OCID of the compartment.'),
    external_db_system_id: str | None = Field(None, description='The OCID of the external DB system.'),
    display_name: str | None = Field(None, description='A filter to only return the resources that match the entire display name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'DISPLAYNAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor `TIMECREATED` is descending and the default sort order for `DISPLAYNAME` is ascending.\nThe `DISPLAYNAME` sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "DISPLAYNAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_external_listeners',
        compartment_id=compartment_id,
        external_db_system_id=external_db_system_id,
        display_name=display_name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)








@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_job_executions"],
    annotations=TOOL_ANNOTATIONS["list_job_executions"],)
def list_job_executions(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str | None = Field(None, description='The identifier of the resource.'),
    job_id: str | None = Field(None, description='The identifier of the job.'),
    managed_database_id: str | None = Field(None, description='The OCID of the Managed Database.'),
    managed_database_group_id: str | None = Field(None, description='The OCID of the Managed Database Group.'),
    status: str | None = Field(None, description='The status of the job execution.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    job_run_id: str | None = Field(None, description='The identifier of the job run.'),) -> Any:
    return invoke_dbm(
        'list_job_executions',
        compartment_id=compartment_id,
        id=id,
        job_id=job_id,
        managed_database_id=managed_database_id,
        managed_database_group_id=managed_database_group_id,
        status=status,
        name=name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        job_run_id=job_run_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_job_runs"],
    annotations=TOOL_ANNOTATIONS["list_job_runs"],)
def list_job_runs(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str | None = Field(None, description='The identifier of the resource.'),
    job_id: str | None = Field(None, description='The identifier of the job.'),
    managed_database_id: str | None = Field(None, description='The OCID of the Managed Database.'),
    managed_database_group_id: str | None = Field(None, description='The OCID of the Managed Database Group.'),
    run_status: str | None = Field(None, description='The status of the job run.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_job_runs',
        compartment_id=compartment_id,
        id=id,
        job_id=job_id,
        managed_database_id=managed_database_id,
        managed_database_group_id=managed_database_group_id,
        run_status=run_status,
        name=name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_jobs"],
    annotations=TOOL_ANNOTATIONS["list_jobs"],)
def list_jobs(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str | None = Field(None, description='The identifier of the resource.'),
    managed_database_group_id: str | None = Field(None, description='The OCID of the Managed Database Group.'),
    managed_database_id: str | None = Field(None, description='The OCID of the Managed Database.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    lifecycle_state: Literal['ACTIVE', 'INACTIVE'] | None = Field(None, description='The lifecycle state of the job.\n\nAllowed values are: "ACTIVE", "INACTIVE"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_jobs',
        compartment_id=compartment_id,
        id=id,
        managed_database_group_id=managed_database_group_id,
        managed_database_id=managed_database_id,
        name=name,
        lifecycle_state=lifecycle_state,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_managed_database_groups"],
    annotations=TOOL_ANNOTATIONS["list_managed_database_groups"],)
def list_managed_database_groups(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str | None = Field(None, description='The identifier of the resource.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED'] | None = Field(None, description='The lifecycle state of a resource.\n\nAllowed values are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_managed_database_groups',
        compartment_id=compartment_id,
        id=id,
        name=name,
        lifecycle_state=lifecycle_state,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_managed_databases"],
    annotations=TOOL_ANNOTATIONS["list_managed_databases"],)
def list_managed_databases(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    id: str | None = Field(None, description='The identifier of the resource.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    management_option: Literal['BASIC', 'ADVANCED'] | None = Field(None, description='A filter to return Managed Databases with the specified management option.\n\nAllowed values are: "BASIC", "ADVANCED"'),
    deployment_type: Literal['ONPREMISE', 'BM', 'VM', 'EXADATA', 'EXADATA_CC', 'AUTONOMOUS', 'EXADATA_XS'] | None = Field(None, description='A filter to return Managed Databases of the specified deployment type.\n\nAllowed values are: "ONPREMISE", "BM", "VM", "EXADATA", "EXADATA_CC", "AUTONOMOUS", "EXADATA_XS"'),
    external_exadata_infrastructure_id: str | None = Field(None, description='The OCID of the Exadata infrastructure.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_managed_databases',
        compartment_id=compartment_id,
        id=id,
        name=name,
        management_option=management_option,
        deployment_type=deployment_type,
        external_exadata_infrastructure_id=external_exadata_infrastructure_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)












@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_named_credentials"],
    annotations=TOOL_ANNOTATIONS["list_named_credentials"],)
def list_named_credentials(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    associated_resource: str | None = Field(None, description='The resource associated to the named credential.'),
    type: Literal['ORACLE_DB'] | None = Field(None, description='The type of database that is associated to the named credential.\n\nAllowed values are: "ORACLE_DB"'),
    scope: Literal['RESOURCE', 'GLOBAL'] | None = Field(None, description='The scope of named credential.\n\nAllowed values are: "RESOURCE", "GLOBAL"'),
    name: str | None = Field(None, description='The name of the named credential.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_named_credentials',
        compartment_id=compartment_id,
        associated_resource=associated_resource,
        type=type,
        scope=scope,
        name=name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_object_privileges"],
    annotations=TOOL_ANNOTATIONS["list_object_privileges"],)
def list_object_privileges(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    user_name: str = Field(..., description='The name of the user whose details are to be viewed.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘NAME’ is ascending. The ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_object_privileges',
        managed_database_id=managed_database_id,
        user_name=user_name,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_optimizer_statistics_advisor_executions"],
    annotations=TOOL_ANNOTATIONS["list_optimizer_statistics_advisor_executions"],)
def list_optimizer_statistics_advisor_executions(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    start_time_greater_than_or_equal_to: str | None = Field(None, description='The start time of the time range to retrieve the optimizer statistics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    end_time_less_than_or_equal_to: str | None = Field(None, description='The end time of the time range to retrieve the optimizer statistics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_optimizer_statistics_advisor_executions',
        managed_database_id=managed_database_id,
        start_time_greater_than_or_equal_to=start_time_greater_than_or_equal_to,
        end_time_less_than_or_equal_to=end_time_less_than_or_equal_to,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_optimizer_statistics_collection_aggregations"],
    annotations=TOOL_ANNOTATIONS["list_optimizer_statistics_collection_aggregations"],)
def list_optimizer_statistics_collection_aggregations(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    group_type: Literal['TASK_STATUS', 'TASK_OBJECTS_STATUS'] = Field(..., description='The optimizer statistics tasks grouped by type.\n\nAllowed values are: "TASK_STATUS", "TASK_OBJECTS_STATUS"'),
    start_time_greater_than_or_equal_to: str | None = Field(None, description='The start time of the time range to retrieve the optimizer statistics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    end_time_less_than_or_equal_to: str | None = Field(None, description='The end time of the time range to retrieve the optimizer statistics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    task_type: Literal['ALL', 'MANUAL', 'AUTO'] | None = Field(None, description='The filter types of the optimizer statistics tasks.\n\nAllowed values are: "ALL", "MANUAL", "AUTO"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_optimizer_statistics_collection_aggregations',
        managed_database_id=managed_database_id,
        group_type=group_type,
        start_time_greater_than_or_equal_to=start_time_greater_than_or_equal_to,
        end_time_less_than_or_equal_to=end_time_less_than_or_equal_to,
        task_type=task_type,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_optimizer_statistics_collection_operations"],
    annotations=TOOL_ANNOTATIONS["list_optimizer_statistics_collection_operations"],)
def list_optimizer_statistics_collection_operations(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    start_time_greater_than_or_equal_to: str | None = Field(None, description='The start time of the time range to retrieve the optimizer statistics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    end_time_less_than_or_equal_to: str | None = Field(None, description='The end time of the time range to retrieve the optimizer statistics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    task_type: Literal['ALL', 'MANUAL', 'AUTO'] | None = Field(None, description='The filter types of the optimizer statistics tasks.\n\nAllowed values are: "ALL", "MANUAL", "AUTO"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    filter_by: str | None = Field(None, description='The parameter used to filter the optimizer statistics operations.\nAny property of the OptimizerStatisticsCollectionOperationSummary can be used to define the filter condition.\nThe allowed conditional operators are AND or OR, and the allowed binary operators are are >, < and =. Any other operator is regarded invalid.\nExample: jobName=<replace with job name> AND status=<replace with status>'),
    sort_by: Literal['START_TIME', 'END_TIME', 'STATUS'] | None = Field(None, description='Sorts the list of optimizer statistics operations based on a specific attribute.\n\nAllowed values are: "START_TIME", "END_TIME", "STATUS"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_optimizer_statistics_collection_operations',
        managed_database_id=managed_database_id,
        start_time_greater_than_or_equal_to=start_time_greater_than_or_equal_to,
        end_time_less_than_or_equal_to=end_time_less_than_or_equal_to,
        task_type=task_type,
        limit=limit,
        filter_by=filter_by,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)




@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_preferred_credentials"],
    annotations=TOOL_ANNOTATIONS["list_preferred_credentials"],)
def list_preferred_credentials(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),) -> Any:
    return invoke_dbm(
        'list_preferred_credentials',
        managed_database_id=managed_database_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_proxied_for_users"],
    annotations=TOOL_ANNOTATIONS["list_proxied_for_users"],)
def list_proxied_for_users(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    user_name: str = Field(..., description='The name of the user whose details are to be viewed.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘NAME’ is ascending. The ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_proxied_for_users',
        managed_database_id=managed_database_id,
        user_name=user_name,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_proxy_users"],
    annotations=TOOL_ANNOTATIONS["list_proxy_users"],)
def list_proxy_users(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    user_name: str = Field(..., description='The name of the user whose details are to be viewed.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘NAME’ is ascending. The ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_proxy_users',
        managed_database_id=managed_database_id,
        user_name=user_name,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_roles"],
    annotations=TOOL_ANNOTATIONS["list_roles"],)
def list_roles(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    user_name: str = Field(..., description='The name of the user whose details are to be viewed.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘NAME’ is ascending. The ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_roles',
        managed_database_id=managed_database_id,
        user_name=user_name,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_sql_plan_baseline_jobs"],
    annotations=TOOL_ANNOTATIONS["list_sql_plan_baseline_jobs"],)
def list_sql_plan_baseline_jobs(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    name: str | None = Field(None, description='A filter to return the SQL plan baseline jobs that match the name.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_sql_plan_baseline_jobs',
        managed_database_id=managed_database_id,
        name=name,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_sql_plan_baselines"],
    annotations=TOOL_ANNOTATIONS["list_sql_plan_baselines"],)
def list_sql_plan_baselines(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    plan_name: str | None = Field(None, description='A filter to return only SQL plan baselines that match the plan name.'),
    sql_handle: str | None = Field(None, description='A filter to return all the SQL plan baselines for the specified SQL handle.'),
    sql_text: str | None = Field(None, description="A filter to return all the SQL plan baselines that match the SQL text. By default, the search\nis case insensitive. To run an exact or case-sensitive search, double-quote the search string.\nYou may also use the '%' symbol as a wildcard."),
    is_enabled: bool | None = Field(None, description='A filter to return only SQL plan baselines that are either enabled or not enabled.\nBy default, all SQL plan baselines are returned.'),
    is_accepted: bool | None = Field(None, description='A filter to return only SQL plan baselines that are either accepted or not accepted.\nBy default, all SQL plan baselines are returned.'),
    is_reproduced: bool | None = Field(None, description='A filter to return only SQL plan baselines that were either reproduced or\nnot reproduced by the optimizer. By default, all SQL plan baselines are returned.'),
    is_fixed: bool | None = Field(None, description='A filter to return only SQL plan baselines that are either fixed or not fixed.\nBy default, all SQL plan baselines are returned.'),
    is_adaptive: bool | None = Field(None, description='A filter to return only SQL plan baselines that are either adaptive or not adaptive.\nBy default, all SQL plan baselines are returned.'),
    origin: Literal['ADDM_SQLTUNE', 'AUTO_CAPTURE', 'AUTO_SQLTUNE', 'EVOLVE_AUTO_INDEX_LOAD', 'EVOLVE_CREATE_FROM_ADAPTIVE', 'EVOLVE_LOAD_FROM_STS', 'EVOLVE_LOAD_FROM_AWR', 'EVOLVE_LOAD_FROM_CURSOR_CACHE', 'MANUAL_LOAD', 'MANUAL_LOAD_FROM_AWR', 'MANUAL_LOAD_FROM_CURSOR_CACHE', 'MANUAL_LOAD_FROM_STS', 'MANUAL_SQLTUNE', 'STORED_OUTLINE', 'UNKNOWN'] | None = Field(None, description='A filter to return all the SQL plan baselines that match the origin.\n\nAllowed values are: "ADDM_SQLTUNE", "AUTO_CAPTURE", "AUTO_SQLTUNE", "EVOLVE_AUTO_INDEX_LOAD", "EVOLVE_CREATE_FROM_ADAPTIVE", "EVOLVE_LOAD_FROM_STS", "EVOLVE_LOAD_FROM_AWR", "EVOLVE_LOAD_FROM_CURSOR_CACHE", "MANUAL_LOAD", "MANUAL_LOAD_FROM_AWR", "MANUAL_LOAD_FROM_CURSOR_CACHE", "MANUAL_LOAD_FROM_STS", "MANUAL_SQLTUNE", "STORED_OUTLINE", "UNKNOWN"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['timeCreated', 'timeLastModified', 'timeLastExecuted'] | None = Field(None, description='The option to sort the SQL plan baseline summary data.\n\nAllowed values are: "timeCreated", "timeLastModified", "timeLastExecuted"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    is_auto_purged: bool | None = Field(None, description='A filter to return only SQL plan baselines that are either auto-purged or not auto-purged.\nBy default, all SQL plan baselines are returned.'),
    time_last_executed_greater_than: datetime | None = Field(None, description='A filter to return only SQL plan baselines whose last execution time is\nafter the specified value. By default, all SQL plan baselines are returned.'),
    time_last_executed_less_than: datetime | None = Field(None, description='A filter to return only SQL plan baselines whose last execution time is\nbefore the specified value. By default, all SQL plan baselines are returned.'),
    is_never_executed: bool | None = Field(None, description='A filter to return only SQL plan baselines that are not executed till now.\nBy default, all SQL plan baselines are returned.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_sql_plan_baselines',
        managed_database_id=managed_database_id,
        plan_name=plan_name,
        sql_handle=sql_handle,
        sql_text=sql_text,
        is_enabled=is_enabled,
        is_accepted=is_accepted,
        is_reproduced=is_reproduced,
        is_fixed=is_fixed,
        is_adaptive=is_adaptive,
        origin=origin,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        is_auto_purged=is_auto_purged,
        time_last_executed_greater_than=time_last_executed_greater_than,
        time_last_executed_less_than=time_last_executed_less_than,
        is_never_executed=is_never_executed,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_sql_tuning_advisor_task_findings"],
    annotations=TOOL_ANNOTATIONS["list_sql_tuning_advisor_task_findings"],)
def list_sql_tuning_advisor_task_findings(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    sql_tuning_advisor_task_id: int = Field(..., description='The SQL tuning task identifier. This is not the OCID.'),
    begin_exec_id: int | None = Field(None, description='The optional greater than or equal to filter on the execution ID related to a specific SQL Tuning Advisor task.'),
    end_exec_id: int | None = Field(None, description='The optional less than or equal to query parameter to filter on the execution ID related to a specific SQL Tuning Advisor task.'),
    search_period: Literal['LAST_24HR', 'LAST_7DAY', 'LAST_31DAY', 'SINCE_LAST', 'ALL'] | None = Field(None, description='The search period during which the API will search for begin and end exec id, if not supplied.\nUnused if beginExecId and endExecId optional query params are both supplied.\n\nAllowed values are: "LAST_24HR", "LAST_7DAY", "LAST_31DAY", "SINCE_LAST", "ALL"'),
    finding_filter: Literal['none', 'FINDINGS', 'NOFINDINGS', 'ERRORS', 'PROFILES', 'INDICES', 'STATS', 'RESTRUCTURE', 'ALTERNATIVE', 'AUTO_PROFILES', 'OTHER_PROFILES'] | None = Field(None, description='The filter used to display specific findings in the report.\n\nAllowed values are: "none", "FINDINGS", "NOFINDINGS", "ERRORS", "PROFILES", "INDICES", "STATS", "RESTRUCTURE", "ALTERNATIVE", "AUTO_PROFILES", "OTHER_PROFILES"'),
    stats_hash_filter: str | None = Field(None, description='The hash value of the object for the statistic finding search.'),
    index_hash_filter: str | None = Field(None, description='The hash value of the index table name.'),
    sort_by: Literal['DBTIME_BENEFIT', 'PARSING_SCHEMA', 'SQL_ID', 'STATS', 'PROFILES', 'SQL_BENEFIT', 'DATE', 'INDICES', 'RESTRUCTURE', 'ALTERNATIVE', 'MISC', 'ERROR', 'TIMEOUTS'] | None = Field(None, description='The possible sortBy values of an object\'s recommendations.\n\nAllowed values are: "DBTIME_BENEFIT", "PARSING_SCHEMA", "SQL_ID", "STATS", "PROFILES", "SQL_BENEFIT", "DATE", "INDICES", "RESTRUCTURE", "ALTERNATIVE", "MISC", "ERROR", "TIMEOUTS"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_sql_tuning_advisor_task_findings',
        managed_database_id=managed_database_id,
        sql_tuning_advisor_task_id=sql_tuning_advisor_task_id,
        begin_exec_id=begin_exec_id,
        end_exec_id=end_exec_id,
        search_period=search_period,
        finding_filter=finding_filter,
        stats_hash_filter=stats_hash_filter,
        index_hash_filter=index_hash_filter,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_sql_tuning_advisor_task_recommendations"],
    annotations=TOOL_ANNOTATIONS["list_sql_tuning_advisor_task_recommendations"],)
def list_sql_tuning_advisor_task_recommendations(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    sql_tuning_advisor_task_id: int = Field(..., description='The SQL tuning task identifier. This is not the OCID.'),
    sql_object_id: int = Field(..., description='The SQL object ID for the SQL tuning task. This is not the OCID.'),
    execution_id: int = Field(..., description='The execution ID for an execution of a SQL tuning task. This is not the OCID.'),
    sort_by: Literal['RECOMMENDATION_TYPE', 'BENEFIT'] | None = Field(None, description='The possible sortBy values of an object\'s recommendations.\n\nAllowed values are: "RECOMMENDATION_TYPE", "BENEFIT"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_sql_tuning_advisor_task_recommendations',
        managed_database_id=managed_database_id,
        sql_tuning_advisor_task_id=sql_tuning_advisor_task_id,
        sql_object_id=sql_object_id,
        execution_id=execution_id,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_sql_tuning_advisor_tasks"],
    annotations=TOOL_ANNOTATIONS["list_sql_tuning_advisor_tasks"],)
def list_sql_tuning_advisor_tasks(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    name: str | None = Field(None, description='The optional query parameter to filter the SQL Tuning Advisor task list by name.'),
    status: Literal['INITIAL', 'EXECUTING', 'INTERRUPTED', 'COMPLETED', 'ERROR'] | None = Field(None, description='The optional query parameter to filter the SQL Tuning Advisor task list by status.\n\nAllowed values are: "INITIAL", "EXECUTING", "INTERRUPTED", "COMPLETED", "ERROR"'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['NAME', 'START_TIME'] | None = Field(None, description='The option to sort the SQL Tuning Advisor task summary data.\n\nAllowed values are: "NAME", "START_TIME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_sql_tuning_advisor_tasks',
        managed_database_id=managed_database_id,
        name=name,
        status=status,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_sql_tuning_sets"],
    annotations=TOOL_ANNOTATIONS["list_sql_tuning_sets"],)
def list_sql_tuning_sets(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    owner: str | None = Field(None, description='The owner of the SQL tuning set.'),
    name_contains: str | None = Field(None, description='Allow searching the name of the SQL tuning set by partial matching. The search is case insensitive.'),
    sort_by: Literal['NAME'] | None = Field(None, description='The option to sort the SQL tuning set summary data.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_sql_tuning_sets',
        managed_database_id=managed_database_id,
        owner=owner,
        name_contains=name_contains,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_system_privileges"],
    annotations=TOOL_ANNOTATIONS["list_system_privileges"],)
def list_system_privileges(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    user_name: str = Field(..., description='The name of the user whose details are to be viewed.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    sort_by: Literal['NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘NAME’ is ascending. The ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_system_privileges',
        managed_database_id=managed_database_id,
        user_name=user_name,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_table_statistics"],
    annotations=TOOL_ANNOTATIONS["list_table_statistics"],)
def list_table_statistics(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_table_statistics',
        managed_database_id=managed_database_id,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_tablespaces"],
    annotations=TOOL_ANNOTATIONS["list_tablespaces"],)
def list_tablespaces(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_tablespaces',
        managed_database_id=managed_database_id,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_users"],
    annotations=TOOL_ANNOTATIONS["list_users"],)
def list_users(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'list_users',
        managed_database_id=managed_database_id,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_work_request_errors"],
    annotations=TOOL_ANNOTATIONS["list_work_request_errors"],)
def list_work_request_errors(
    work_request_id: str = Field(..., description='The OCID of the asynchronous work request.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['timeAccepted'] | None = Field(None, description='The field to sort by. Only one sort order may be provided and the default order for timeAccepted is descending.\n\nAllowed values are: "timeAccepted"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_work_request_errors',
        work_request_id=work_request_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_work_request_logs"],
    annotations=TOOL_ANNOTATIONS["list_work_request_logs"],)
def list_work_request_logs(
    work_request_id: str = Field(..., description='The OCID of the asynchronous work request.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['timeAccepted'] | None = Field(None, description='The field to sort by. Only one sort order may be provided and the default order for timeAccepted is descending.\n\nAllowed values are: "timeAccepted"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'list_work_request_logs',
        work_request_id=work_request_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["list_work_requests"],
    annotations=TOOL_ANNOTATIONS["list_work_requests"],)
def list_work_requests(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    resource_id: str | None = Field(None, description='The OCID of the resource affected by the work request.'),
    work_request_id: str | None = Field(None, description='The OCID of the asynchronous work request.'),
    status: Literal['ACCEPTED', 'IN_PROGRESS', 'FAILED', 'SUCCEEDED', 'CANCELING', 'CANCELED'] | None = Field(None, description='A filter that returns the resources whose status matches the given WorkRequestStatus.\n\nAllowed values are: "ACCEPTED", "IN_PROGRESS", "FAILED", "SUCCEEDED", "CANCELING", "CANCELED"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    sort_by: Literal['timeAccepted'] | None = Field(None, description='The field to sort by. Only one sort order may be provided and the default order for timeAccepted is descending.\n\nAllowed values are: "timeAccepted"'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),) -> Any:
    return invoke_dbm(
        'list_work_requests',
        compartment_id=compartment_id,
        resource_id=resource_id,
        work_request_id=work_request_id,
        status=status,
        sort_order=sort_order,
        sort_by=sort_by,
        limit=limit,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_alert_log_counts"],
    annotations=TOOL_ANNOTATIONS["summarize_alert_log_counts"],)
def summarize_alert_log_counts(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to timestamp to filter the logs.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to timestamp to filter the logs.'),
    level_filter: Literal['CRITICAL', 'SEVERE', 'IMPORTANT', 'NORMAL', 'ALL'] | None = Field(None, description='The optional parameter to filter the alert logs by log level.\n\nAllowed values are: "CRITICAL", "SEVERE", "IMPORTANT", "NORMAL", "ALL"'),
    group_by: Literal['LEVEL', 'TYPE'] | None = Field(None, description='The optional parameter used to group different alert logs.\n\nAllowed values are: "LEVEL", "TYPE"'),
    type_filter: Literal['UNKNOWN', 'INCIDENT_ERROR', 'ERROR', 'WARNING', 'NOTIFICATION', 'TRACE', 'ALL'] | None = Field(None, description='The optional parameter to filter the attention or alert logs by type.\n\nAllowed values are: "UNKNOWN", "INCIDENT_ERROR", "ERROR", "WARNING", "NOTIFICATION", "TRACE", "ALL"'),
    log_search_text: str | None = Field(None, description='The optional query parameter to filter the attention or alert logs by search text.'),
    is_regular_expression: bool | None = Field(None, description='The flag to indicate whether the search text is regular expression or not.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_alert_log_counts',
        managed_database_id=managed_database_id,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        level_filter=level_filter,
        group_by=group_by,
        type_filter=type_filter,
        log_search_text=log_search_text,
        is_regular_expression=is_regular_expression,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_attention_log_counts"],
    annotations=TOOL_ANNOTATIONS["summarize_attention_log_counts"],)
def summarize_attention_log_counts(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to timestamp to filter the logs.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to timestamp to filter the logs.'),
    urgency_filter: Literal['IMMEDIATE', 'SOON', 'DEFERRABLE', 'INFO', 'ALL'] | None = Field(None, description='The optional parameter to filter the attention logs by urgency.\n\nAllowed values are: "IMMEDIATE", "SOON", "DEFERRABLE", "INFO", "ALL"'),
    group_by: Literal['URGENCY', 'TYPE'] | None = Field(None, description='The optional parameter used to group different attention logs.\n\nAllowed values are: "URGENCY", "TYPE"'),
    type_filter: Literal['UNKNOWN', 'INCIDENT_ERROR', 'ERROR', 'WARNING', 'NOTIFICATION', 'TRACE', 'ALL'] | None = Field(None, description='The optional parameter to filter the attention or alert logs by type.\n\nAllowed values are: "UNKNOWN", "INCIDENT_ERROR", "ERROR", "WARNING", "NOTIFICATION", "TRACE", "ALL"'),
    log_search_text: str | None = Field(None, description='The optional query parameter to filter the attention or alert logs by search text.'),
    is_regular_expression: bool | None = Field(None, description='The flag to indicate whether the search text is regular expression or not.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_attention_log_counts',
        managed_database_id=managed_database_id,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        urgency_filter=urgency_filter,
        group_by=group_by,
        type_filter=type_filter,
        log_search_text=log_search_text,
        is_regular_expression=is_regular_expression,
        limit=limit,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_db_cpu_usages"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_db_cpu_usages"],)
def summarize_awr_db_cpu_usages(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    awr_db_id: str = Field(..., description='Internal AWR database identifier within the managed database. This value is not an OCID; use the identifier returned by AWR database listing results.'),
    inst_num: str | None = Field(None, description='The optional single value query parameter to filter the database instance number.'),
    begin_sn_id_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_sn_id_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot ID.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    session_type: Literal['FOREGROUND', 'BACKGROUND', 'ALL'] | None = Field(None, description='The optional query parameter to filter ASH activities by FOREGROUND or BACKGROUND.\n\nAllowed values are: "FOREGROUND", "BACKGROUND", "ALL"'),
    container_id: int | None = Field(None, description='AWR database container identifier. This value is not an OCID; use container identifiers returned by AWR snapshot range results.'),
    limit: int | None = Field(None, description='For large list pagination. Maximum number of results to return in one response page. Example: 1000.', ge=1, le=1000),
    sort_by: Literal['TIME_SAMPLED', 'AVG_VALUE'] | None = Field(None, description='The option to sort the AWR CPU usage summary data.\n\nAllowed values are: "TIME_SAMPLED", "AVG_VALUE"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_awr_db_cpu_usages',
        managed_database_id=managed_database_id,
        awr_db_id=awr_db_id,
        inst_num=inst_num,
        begin_sn_id_greater_than_or_equal_to=begin_sn_id_greater_than_or_equal_to,
        end_sn_id_less_than_or_equal_to=end_sn_id_less_than_or_equal_to,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        session_type=session_type,
        container_id=container_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_db_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_db_metrics"],)
def summarize_awr_db_metrics(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    awr_db_id: str = Field(..., description='Internal AWR database identifier within the managed database. This value is not an OCID; use the identifier returned by AWR database listing results.'),
    name: list[str] = Field(..., description='The required multiple value query parameter to filter the entity name.'),
    inst_num: str | None = Field(None, description='The optional single value query parameter to filter the database instance number.'),
    begin_sn_id_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_sn_id_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot ID.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    container_id: int | None = Field(None, description='AWR database container identifier. This value is not an OCID; use container identifiers returned by AWR snapshot range results.'),
    limit: int | None = Field(None, description='For large list pagination. Maximum number of results to return in one response page. Example: 1000.', ge=1, le=1000),
    sort_by: Literal['TIMESTAMP', 'NAME'] | None = Field(None, description='The option to sort the AWR time series summary data.\n\nAllowed values are: "TIMESTAMP", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_awr_db_metrics',
        managed_database_id=managed_database_id,
        awr_db_id=awr_db_id,
        name=name,
        inst_num=inst_num,
        begin_sn_id_greater_than_or_equal_to=begin_sn_id_greater_than_or_equal_to,
        end_sn_id_less_than_or_equal_to=end_sn_id_less_than_or_equal_to,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        container_id=container_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_db_parameter_changes"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_db_parameter_changes"],)
def summarize_awr_db_parameter_changes(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    awr_db_id: str = Field(..., description='Internal AWR database identifier within the managed database. This value is not an OCID; use the identifier returned by AWR database listing results.'),
    name: str = Field(..., description='The required single value query parameter to filter the entity name.'),
    inst_num: str | None = Field(None, description='The optional single value query parameter to filter the database instance number.'),
    begin_sn_id_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_sn_id_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot ID.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    container_id: int | None = Field(None, description='AWR database container identifier. This value is not an OCID; use container identifiers returned by AWR snapshot range results.'),
    limit: int | None = Field(None, description='For large list pagination. Maximum number of results to return in one response page. Example: 1000.', ge=1, le=1000),
    sort_by: Literal['IS_CHANGED', 'NAME'] | None = Field(None, description='The option to sort the AWR database parameter change history data.\n\nAllowed values are: "IS_CHANGED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_awr_db_parameter_changes',
        managed_database_id=managed_database_id,
        awr_db_id=awr_db_id,
        name=name,
        inst_num=inst_num,
        begin_sn_id_greater_than_or_equal_to=begin_sn_id_greater_than_or_equal_to,
        end_sn_id_less_than_or_equal_to=end_sn_id_less_than_or_equal_to,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        container_id=container_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_db_parameters"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_db_parameters"],)
def summarize_awr_db_parameters(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    awr_db_id: str = Field(..., description='Internal AWR database identifier within the managed database. This value is not an OCID; use the identifier returned by AWR database listing results.'),
    inst_num: str | None = Field(None, description='The optional single value query parameter to filter the database instance number.'),
    begin_sn_id_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_sn_id_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot ID.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    container_id: int | None = Field(None, description='AWR database container identifier. This value is not an OCID; use container identifiers returned by AWR snapshot range results.'),
    name: list[str] | None = Field(None, description='The optional multiple value query parameter to filter the entity name.'),
    name_contains: str | None = Field(None, description='The optional contains query parameter to filter the entity name by any part of the name.'),
    value_changed: Literal['Y', 'N'] | None = Field(None, description='The optional query parameter to filter database parameters whose values were changed.\n\nAllowed values are: "Y", "N"'),
    value_default: Literal['TRUE', 'FALSE'] | None = Field(None, description='The optional query parameter to filter the database parameters that had the default value in the last snapshot.\n\nAllowed values are: "TRUE", "FALSE"'),
    value_modified: Literal['MODIFIED', 'SYSTEM_MOD', 'FALSE'] | None = Field(None, description='The optional query parameter to filter the database parameters that had a modified value in the last snapshot.\n\nAllowed values are: "MODIFIED", "SYSTEM_MOD", "FALSE"'),
    limit: int | None = Field(None, description='For large list pagination. Maximum number of results to return in one response page. Example: 1000.', ge=1, le=1000),
    sort_by: Literal['IS_CHANGED', 'NAME'] | None = Field(None, description='The option to sort the AWR database parameter change history data.\n\nAllowed values are: "IS_CHANGED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_awr_db_parameters',
        managed_database_id=managed_database_id,
        awr_db_id=awr_db_id,
        inst_num=inst_num,
        begin_sn_id_greater_than_or_equal_to=begin_sn_id_greater_than_or_equal_to,
        end_sn_id_less_than_or_equal_to=end_sn_id_less_than_or_equal_to,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        container_id=container_id,
        name=name,
        name_contains=name_contains,
        value_changed=value_changed,
        value_default=value_default,
        value_modified=value_modified,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_db_snapshot_ranges"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_db_snapshot_ranges"],)
def summarize_awr_db_snapshot_ranges(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    name: str | None = Field(None, description='The optional single value query parameter to filter the entity name.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    sort_by: Literal['END_INTERVAL_TIME', 'NAME'] | None = Field(None, description='The option to sort the AWR summary data.\n\nAllowed values are: "END_INTERVAL_TIME", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_awr_db_snapshot_ranges',
        managed_database_id=managed_database_id,
        name=name,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_db_sysstats"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_db_sysstats"],)
def summarize_awr_db_sysstats(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    awr_db_id: str = Field(..., description='Internal AWR database identifier within the managed database. This value is not an OCID; use the identifier returned by AWR database listing results.'),
    name: list[str] = Field(..., description='The required multiple value query parameter to filter the entity name.'),
    inst_num: str | None = Field(None, description='The optional single value query parameter to filter the database instance number.'),
    begin_sn_id_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_sn_id_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot ID.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    container_id: int | None = Field(None, description='AWR database container identifier. This value is not an OCID; use container identifiers returned by AWR snapshot range results.'),
    limit: int | None = Field(None, description='For large list pagination. Maximum number of results to return in one response page. Example: 1000.', ge=1, le=1000),
    sort_by: Literal['TIME_BEGIN', 'NAME'] | None = Field(None, description='The option to sort the data within a time period.\n\nAllowed values are: "TIME_BEGIN", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_awr_db_sysstats',
        managed_database_id=managed_database_id,
        awr_db_id=awr_db_id,
        name=name,
        inst_num=inst_num,
        begin_sn_id_greater_than_or_equal_to=begin_sn_id_greater_than_or_equal_to,
        end_sn_id_less_than_or_equal_to=end_sn_id_less_than_or_equal_to,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        container_id=container_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_db_top_wait_events"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_db_top_wait_events"],)
def summarize_awr_db_top_wait_events(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    awr_db_id: str = Field(..., description='Internal AWR database identifier within the managed database. This value is not an OCID; use the identifier returned by AWR database listing results.'),
    inst_num: str | None = Field(None, description='The optional single value query parameter to filter the database instance number.'),
    begin_sn_id_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_sn_id_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot ID.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    session_type: Literal['FOREGROUND', 'BACKGROUND', 'ALL'] | None = Field(None, description='The optional query parameter to filter ASH activities by FOREGROUND or BACKGROUND.\n\nAllowed values are: "FOREGROUND", "BACKGROUND", "ALL"'),
    container_id: int | None = Field(None, description='AWR database container identifier. This value is not an OCID; use container identifiers returned by AWR snapshot range results.'),
    top_n: int | None = Field(None, description='The optional query parameter to filter the number of top categories to be returned.'),
    sort_by: Literal['WAITS_PERSEC', 'AVG_WAIT_TIME_PERSEC'] | None = Field(None, description='The option to sort the AWR top event summary data.\n\nAllowed values are: "WAITS_PERSEC", "AVG_WAIT_TIME_PERSEC"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_awr_db_top_wait_events',
        managed_database_id=managed_database_id,
        awr_db_id=awr_db_id,
        inst_num=inst_num,
        begin_sn_id_greater_than_or_equal_to=begin_sn_id_greater_than_or_equal_to,
        end_sn_id_less_than_or_equal_to=end_sn_id_less_than_or_equal_to,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        session_type=session_type,
        container_id=container_id,
        top_n=top_n,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_db_wait_event_buckets"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_db_wait_event_buckets"],)
def summarize_awr_db_wait_event_buckets(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    awr_db_id: str = Field(..., description='Internal AWR database identifier within the managed database. This value is not an OCID; use the identifier returned by AWR database listing results.'),
    name: str = Field(..., description='The required single value query parameter to filter the entity name.'),
    inst_num: str | None = Field(None, description='The optional single value query parameter to filter the database instance number.'),
    begin_sn_id_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_sn_id_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot ID.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    num_bucket: int | None = Field(None, description='The number of buckets within the histogram.'),
    min_value: float | None = Field(None, description='The minimum value of the histogram.'),
    max_value: float | None = Field(None, description='The maximum value of the histogram.'),
    container_id: int | None = Field(None, description='AWR database container identifier. This value is not an OCID; use container identifiers returned by AWR snapshot range results.'),
    limit: int | None = Field(None, description='For large list pagination. Maximum number of results to return in one response page. Example: 1000.', ge=1, le=1000),
    sort_by: Literal['CATEGORY', 'PERCENTAGE'] | None = Field(None, description='The option to sort distribution data.\n\nAllowed values are: "CATEGORY", "PERCENTAGE"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_awr_db_wait_event_buckets',
        managed_database_id=managed_database_id,
        awr_db_id=awr_db_id,
        name=name,
        inst_num=inst_num,
        begin_sn_id_greater_than_or_equal_to=begin_sn_id_greater_than_or_equal_to,
        end_sn_id_less_than_or_equal_to=end_sn_id_less_than_or_equal_to,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        num_bucket=num_bucket,
        min_value=min_value,
        max_value=max_value,
        container_id=container_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_awr_db_wait_events"],
    annotations=TOOL_ANNOTATIONS["summarize_awr_db_wait_events"],)
def summarize_awr_db_wait_events(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    awr_db_id: str = Field(..., description='Internal AWR database identifier within the managed database. This value is not an OCID; use the identifier returned by AWR database listing results.'),
    inst_num: str | None = Field(None, description='The optional single value query parameter to filter the database instance number.'),
    begin_sn_id_greater_than_or_equal_to: int | None = Field(None, description='The optional greater than or equal to filter on the snapshot ID.'),
    end_sn_id_less_than_or_equal_to: int | None = Field(None, description='The optional less than or equal to query parameter to filter the snapshot ID.'),
    time_greater_than_or_equal_to: datetime | None = Field(None, description='The optional greater than or equal to query parameter to filter the timestamp.'),
    time_less_than_or_equal_to: datetime | None = Field(None, description='The optional less than or equal to query parameter to filter the timestamp.'),
    name: list[str] | None = Field(None, description='The optional multiple value query parameter to filter the entity name.'),
    session_type: Literal['FOREGROUND', 'BACKGROUND', 'ALL'] | None = Field(None, description='The optional query parameter to filter ASH activities by FOREGROUND or BACKGROUND.\n\nAllowed values are: "FOREGROUND", "BACKGROUND", "ALL"'),
    container_id: int | None = Field(None, description='AWR database container identifier. This value is not an OCID; use container identifiers returned by AWR snapshot range results.'),
    limit: int | None = Field(None, description='For large list pagination. Maximum number of results to return in one response page. Example: 1000.', ge=1, le=1000),
    sort_by: Literal['TIME_BEGIN', 'NAME'] | None = Field(None, description='The option to sort the data within a time period.\n\nAllowed values are: "TIME_BEGIN", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Descending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_awr_db_wait_events',
        managed_database_id=managed_database_id,
        awr_db_id=awr_db_id,
        inst_num=inst_num,
        begin_sn_id_greater_than_or_equal_to=begin_sn_id_greater_than_or_equal_to,
        end_sn_id_less_than_or_equal_to=end_sn_id_less_than_or_equal_to,
        time_greater_than_or_equal_to=time_greater_than_or_equal_to,
        time_less_than_or_equal_to=time_less_than_or_equal_to,
        name=name,
        session_type=session_type,
        container_id=container_id,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_cloud_asm_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_cloud_asm_metrics"],)
def summarize_cloud_asm_metrics(
    cloud_asm_id: str = Field(..., description='The OCID of the cloud ASM.'),
    start_time: str = Field(..., description="The beginning of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    end_time: str = Field(..., description="The end of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),) -> Any:
    return invoke_dbm(
        'summarize_cloud_asm_metrics',
        cloud_asm_id=cloud_asm_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        filter_by_metric_names=filter_by_metric_names,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_cloud_cluster_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_cloud_cluster_metrics"],)
def summarize_cloud_cluster_metrics(
    cloud_cluster_id: str = Field(..., description='The OCID of the cloud cluster.'),
    start_time: str = Field(..., description="The beginning of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    end_time: str = Field(..., description="The end of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),) -> Any:
    return invoke_dbm(
        'summarize_cloud_cluster_metrics',
        cloud_cluster_id=cloud_cluster_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        filter_by_metric_names=filter_by_metric_names,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_cloud_db_node_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_cloud_db_node_metrics"],)
def summarize_cloud_db_node_metrics(
    cloud_db_node_id: str = Field(..., description='The OCID of the cloud database node.'),
    start_time: str = Field(..., description="The beginning of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    end_time: str = Field(..., description="The end of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),) -> Any:
    return invoke_dbm(
        'summarize_cloud_db_node_metrics',
        cloud_db_node_id=cloud_db_node_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        filter_by_metric_names=filter_by_metric_names,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_cloud_db_system_availability_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_cloud_db_system_availability_metrics"],)
def summarize_cloud_db_system_availability_metrics(
    cloud_db_system_id: str = Field(..., description='The OCID of the cloud DB system.'),
    start_time: str = Field(..., description="The beginning of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    end_time: str = Field(..., description="The end of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    filter_by_component_types: str | None = Field(None, description='The filter used to retrieve metrics for a specific set of component types by passing the desired component types separated by a comma. Note that, by default, the service returns metrics for all DB system component types.'),) -> Any:
    return invoke_dbm(
        'summarize_cloud_db_system_availability_metrics',
        cloud_db_system_id=cloud_db_system_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        filter_by_component_types=filter_by_component_types,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_cloud_listener_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_cloud_listener_metrics"],)
def summarize_cloud_listener_metrics(
    cloud_listener_id: str = Field(..., description='The OCID of the cloud listener.'),
    start_time: str = Field(..., description="The beginning of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    end_time: str = Field(..., description="The end of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),) -> Any:
    return invoke_dbm(
        'summarize_cloud_listener_metrics',
        cloud_listener_id=cloud_listener_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        filter_by_metric_names=filter_by_metric_names,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_external_asm_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_external_asm_metrics"],)
def summarize_external_asm_metrics(
    external_asm_id: str = Field(..., description='The OCID of the external ASM.'),
    start_time: str = Field(..., description="The beginning of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    end_time: str = Field(..., description="The end of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),) -> Any:
    return invoke_dbm(
        'summarize_external_asm_metrics',
        external_asm_id=external_asm_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        filter_by_metric_names=filter_by_metric_names,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_external_cluster_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_external_cluster_metrics"],)
def summarize_external_cluster_metrics(
    external_cluster_id: str = Field(..., description='The OCID of the external cluster.'),
    start_time: str = Field(..., description="The beginning of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    end_time: str = Field(..., description="The end of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),) -> Any:
    return invoke_dbm(
        'summarize_external_cluster_metrics',
        external_cluster_id=external_cluster_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        filter_by_metric_names=filter_by_metric_names,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_external_db_node_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_external_db_node_metrics"],)
def summarize_external_db_node_metrics(
    external_db_node_id: str = Field(..., description='The OCID of the external database node.'),
    start_time: str = Field(..., description="The beginning of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    end_time: str = Field(..., description="The end of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),) -> Any:
    return invoke_dbm(
        'summarize_external_db_node_metrics',
        external_db_node_id=external_db_node_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        filter_by_metric_names=filter_by_metric_names,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_external_db_system_availability_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_external_db_system_availability_metrics"],)
def summarize_external_db_system_availability_metrics(
    external_db_system_id: str = Field(..., description='The OCID of the external DB system.'),
    start_time: str = Field(..., description="The beginning of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    end_time: str = Field(..., description="The end of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    filter_by_component_types: str | None = Field(None, description='The filter used to retrieve metrics for a specific set of component types by passing the desired component types separated by a comma. Note that, by default, the service returns metrics for all DB system component types.'),) -> Any:
    return invoke_dbm(
        'summarize_external_db_system_availability_metrics',
        external_db_system_id=external_db_system_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        filter_by_component_types=filter_by_component_types,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_external_listener_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_external_listener_metrics"],)
def summarize_external_listener_metrics(
    external_listener_id: str = Field(..., description='The OCID of the external listener.'),
    start_time: str = Field(..., description="The beginning of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    end_time: str = Field(..., description="The end of the time range set to retrieve metric data for the DB system\nand its members. Expressed in UTC in ISO-8601 format, which is `yyyy-MM-dd'T'hh:mm:ss.sss'Z'`."),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),
    filter_by_metric_names: str | None = Field(None, description='The filter used to retrieve a specific set of metrics by passing the desired metric names with a comma separator. Note that, by default, the service returns all supported metrics.'),) -> Any:
    return invoke_dbm(
        'summarize_external_listener_metrics',
        external_listener_id=external_listener_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        filter_by_metric_names=filter_by_metric_names,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_job_executions_statuses"],
    annotations=TOOL_ANNOTATIONS["summarize_job_executions_statuses"],)
def summarize_job_executions_statuses(
    compartment_id: str = Field(..., description='The OCID of the compartment.'),
    start_time: str = Field(..., description='The start time of the time range to retrieve the status summary of job executions\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    end_time: str = Field(..., description='The end time of the time range to retrieve the status summary of job executions\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    id: str | None = Field(None, description='The identifier of the resource.'),
    managed_database_group_id: str | None = Field(None, description='The OCID of the Managed Database Group.'),
    managed_database_id: str | None = Field(None, description='The OCID of the Managed Database.'),
    name: str | None = Field(None, description='A filter to return only resources that match the entire name.'),
    sort_by: Literal['TIMECREATED', 'NAME'] | None = Field(None, description='The field to sort information by. Only one sortOrder can be used. The default sort order\nfor ‘TIMECREATED’ is descending and the default sort order for ‘NAME’ is ascending.\nThe ‘NAME’ sort order is case-sensitive.\n\nAllowed values are: "TIMECREATED", "NAME"'),
    sort_order: Literal['ASC', 'DESC'] | None = Field(None, description='The option to sort information in ascending (‘ASC’) or descending (‘DESC’) order. Ascending order is the default order.\n\nAllowed values are: "ASC", "DESC"'),) -> Any:
    return invoke_dbm(
        'summarize_job_executions_statuses',
        compartment_id=compartment_id,
        start_time=start_time,
        end_time=end_time,
        id=id,
        managed_database_group_id=managed_database_group_id,
        managed_database_id=managed_database_id,
        name=name,
        sort_by=sort_by,
        sort_order=sort_order,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_managed_database_availability_metrics"],
    annotations=TOOL_ANNOTATIONS["summarize_managed_database_availability_metrics"],)
def summarize_managed_database_availability_metrics(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    start_time: str = Field(..., description='The start time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    end_time: str = Field(..., description='The end time of the time range to retrieve the health metrics of a Managed Database\nin UTC in ISO-8601 format, which is "yyyy-MM-dd\'T\'hh:mm:ss.sss\'Z\'".'),
    limit: int | None = Field(None, description='For list pagination. Maximum number of results to return in one response page. Example: 50.', ge=1, le=1000),) -> Any:
    return invoke_dbm(
        'summarize_managed_database_availability_metrics',
        managed_database_id=managed_database_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,)




@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_sql_plan_baselines"],
    annotations=TOOL_ANNOTATIONS["summarize_sql_plan_baselines"],)
def summarize_sql_plan_baselines(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_sql_plan_baselines',
        managed_database_id=managed_database_id,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["summarize_sql_plan_baselines_by_last_execution"],
    annotations=TOOL_ANNOTATIONS["summarize_sql_plan_baselines_by_last_execution"],)
def summarize_sql_plan_baselines_by_last_execution(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    opc_named_credential_id: str | None = Field(None, description='The OCID of the Named Credential.'),) -> Any:
    return invoke_dbm(
        'summarize_sql_plan_baselines_by_last_execution',
        managed_database_id=managed_database_id,
        opc_named_credential_id=opc_named_credential_id,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_asm"],
    annotations=TOOL_ANNOTATIONS["update_cloud_asm"],)
def update_cloud_asm(
    cloud_asm_id: str = Field(..., description='The OCID of the cloud ASM.'),
    update_cloud_asm_details: dict[str, Any] | UpdateCloudAsmDetails = Field(..., description='The details required to update an cloud ASM.'),) -> Any:
    return invoke_dbm(
        'update_cloud_asm',
        cloud_asm_id=cloud_asm_id,
        update_cloud_asm_details=update_cloud_asm_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_asm_instance"],
    annotations=TOOL_ANNOTATIONS["update_cloud_asm_instance"],)
def update_cloud_asm_instance(
    cloud_asm_instance_id: str = Field(..., description='The OCID of the cloud ASM instance.'),
    update_cloud_asm_instance_details: dict[str, Any] | UpdateCloudAsmInstanceDetails = Field(..., description='The details required to update an cloud ASM instance.'),) -> Any:
    return invoke_dbm(
        'update_cloud_asm_instance',
        cloud_asm_instance_id=cloud_asm_instance_id,
        update_cloud_asm_instance_details=update_cloud_asm_instance_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_cluster"],
    annotations=TOOL_ANNOTATIONS["update_cloud_cluster"],)
def update_cloud_cluster(
    cloud_cluster_id: str = Field(..., description='The OCID of the cloud cluster.'),
    update_cloud_cluster_details: dict[str, Any] | UpdateCloudClusterDetails = Field(..., description='The details required to update an cloud cluster.'),) -> Any:
    return invoke_dbm(
        'update_cloud_cluster',
        cloud_cluster_id=cloud_cluster_id,
        update_cloud_cluster_details=update_cloud_cluster_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_cluster_instance"],
    annotations=TOOL_ANNOTATIONS["update_cloud_cluster_instance"],)
def update_cloud_cluster_instance(
    cloud_cluster_instance_id: str = Field(..., description='The OCID of the cloud cluster instance.'),
    update_cloud_cluster_instance_details: dict[str, Any] | UpdateCloudClusterInstanceDetails = Field(..., description='The details required to update an cloud cluster instance.'),) -> Any:
    return invoke_dbm(
        'update_cloud_cluster_instance',
        cloud_cluster_instance_id=cloud_cluster_instance_id,
        update_cloud_cluster_instance_details=update_cloud_cluster_instance_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_db_home"],
    annotations=TOOL_ANNOTATIONS["update_cloud_db_home"],)
def update_cloud_db_home(
    cloud_db_home_id: str = Field(..., description='The OCID of the cloud database home.'),
    update_cloud_db_home_details: dict[str, Any] | UpdateCloudDbHomeDetails = Field(..., description='The details required to update an cloud DB home.'),) -> Any:
    return invoke_dbm(
        'update_cloud_db_home',
        cloud_db_home_id=cloud_db_home_id,
        update_cloud_db_home_details=update_cloud_db_home_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_db_node"],
    annotations=TOOL_ANNOTATIONS["update_cloud_db_node"],)
def update_cloud_db_node(
    cloud_db_node_id: str = Field(..., description='The OCID of the cloud database node.'),
    update_cloud_db_node_details: dict[str, Any] | UpdateCloudDbNodeDetails = Field(..., description='The details required to update an cloud DB node.'),) -> Any:
    return invoke_dbm(
        'update_cloud_db_node',
        cloud_db_node_id=cloud_db_node_id,
        update_cloud_db_node_details=update_cloud_db_node_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_db_system"],
    annotations=TOOL_ANNOTATIONS["update_cloud_db_system"],)
def update_cloud_db_system(
    cloud_db_system_id: str = Field(..., description='The OCID of the cloud DB system.'),
    update_cloud_db_system_details: dict[str, Any] | UpdateCloudDbSystemDetails = Field(..., description='The details required to update an cloud DB system.'),) -> Any:
    return invoke_dbm(
        'update_cloud_db_system',
        cloud_db_system_id=cloud_db_system_id,
        update_cloud_db_system_details=update_cloud_db_system_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_db_system_connector"],
    annotations=TOOL_ANNOTATIONS["update_cloud_db_system_connector"],)
def update_cloud_db_system_connector(
    cloud_db_system_connector_id: str = Field(..., description='The OCID of the cloud connector.'),
    update_cloud_db_system_connector_details: dict[str, Any] | UpdateCloudDbSystemConnectorDetails = Field(..., description='The details required to update an cloud connector.'),) -> Any:
    return invoke_dbm(
        'update_cloud_db_system_connector',
        cloud_db_system_connector_id=cloud_db_system_connector_id,
        update_cloud_db_system_connector_details=update_cloud_db_system_connector_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_db_system_discovery"],
    annotations=TOOL_ANNOTATIONS["update_cloud_db_system_discovery"],)
def update_cloud_db_system_discovery(
    cloud_db_system_discovery_id: str = Field(..., description='The OCID of the cloud DB system discovery.'),
    update_cloud_db_system_discovery_details: dict[str, Any] | UpdateCloudDbSystemDiscoveryDetails = Field(..., description='The details required to update an cloud DB system discovery.'),) -> Any:
    return invoke_dbm(
        'update_cloud_db_system_discovery',
        cloud_db_system_discovery_id=cloud_db_system_discovery_id,
        update_cloud_db_system_discovery_details=update_cloud_db_system_discovery_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_exadata_infrastructure"],
    annotations=TOOL_ANNOTATIONS["update_cloud_exadata_infrastructure"],)
def update_cloud_exadata_infrastructure(
    cloud_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),
    update_cloud_exadata_infrastructure_details: dict[str, Any] | UpdateCloudExadataInfrastructureDetails = Field(..., description='The details required to update the managed Exadata infrastructure resources.'),) -> Any:
    return invoke_dbm(
        'update_cloud_exadata_infrastructure',
        cloud_exadata_infrastructure_id=cloud_exadata_infrastructure_id,
        update_cloud_exadata_infrastructure_details=update_cloud_exadata_infrastructure_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_exadata_storage_connector"],
    annotations=TOOL_ANNOTATIONS["update_cloud_exadata_storage_connector"],)
def update_cloud_exadata_storage_connector(
    cloud_exadata_storage_connector_id: str = Field(..., description='The OCID of the connector to the Exadata storage server.'),
    update_cloud_exadata_storage_connector_details: dict[str, Any] | UpdateCloudExadataStorageConnectorDetails = Field(..., description='The details required to update connections to the Exadata storage servers.'),) -> Any:
    return invoke_dbm(
        'update_cloud_exadata_storage_connector',
        cloud_exadata_storage_connector_id=cloud_exadata_storage_connector_id,
        update_cloud_exadata_storage_connector_details=update_cloud_exadata_storage_connector_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_exadata_storage_grid"],
    annotations=TOOL_ANNOTATIONS["update_cloud_exadata_storage_grid"],)
def update_cloud_exadata_storage_grid(
    cloud_exadata_storage_grid_id: str = Field(..., description='The OCID of the Exadata storage grid.'),
    update_cloud_exadata_storage_grid_details: dict[str, Any] | UpdateCloudExadataStorageGridDetails = Field(..., description='The details required to update an Exadata storage grid.'),) -> Any:
    return invoke_dbm(
        'update_cloud_exadata_storage_grid',
        cloud_exadata_storage_grid_id=cloud_exadata_storage_grid_id,
        update_cloud_exadata_storage_grid_details=update_cloud_exadata_storage_grid_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_exadata_storage_server"],
    annotations=TOOL_ANNOTATIONS["update_cloud_exadata_storage_server"],)
def update_cloud_exadata_storage_server(
    cloud_exadata_storage_server_id: str = Field(..., description='The OCID of the Exadata storage server.'),
    update_cloud_exadata_storage_server_details: dict[str, Any] | UpdateCloudExadataStorageServerDetails = Field(..., description='The details required to update an Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'update_cloud_exadata_storage_server',
        cloud_exadata_storage_server_id=cloud_exadata_storage_server_id,
        update_cloud_exadata_storage_server_details=update_cloud_exadata_storage_server_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_cloud_listener"],
    annotations=TOOL_ANNOTATIONS["update_cloud_listener"],)
def update_cloud_listener(
    cloud_listener_id: str = Field(..., description='The OCID of the cloud listener.'),
    update_cloud_listener_details: dict[str, Any] | UpdateCloudListenerDetails = Field(..., description='The details required to update an cloud listener.'),) -> Any:
    return invoke_dbm(
        'update_cloud_listener',
        cloud_listener_id=cloud_listener_id,
        update_cloud_listener_details=update_cloud_listener_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_db_management_private_endpoint"],
    annotations=TOOL_ANNOTATIONS["update_db_management_private_endpoint"],)
def update_db_management_private_endpoint(
    db_management_private_endpoint_id: str = Field(..., description='The OCID of the Database Management private endpoint.'),
    update_db_management_private_endpoint_details: dict[str, Any] | UpdateDbManagementPrivateEndpointDetails = Field(..., description='The details used to update a Database Management private endpoint.'),) -> Any:
    return invoke_dbm(
        'update_db_management_private_endpoint',
        db_management_private_endpoint_id=db_management_private_endpoint_id,
        update_db_management_private_endpoint_details=update_db_management_private_endpoint_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_asm"],
    annotations=TOOL_ANNOTATIONS["update_external_asm"],)
def update_external_asm(
    external_asm_id: str = Field(..., description='The OCID of the external ASM.'),
    update_external_asm_details: dict[str, Any] | UpdateExternalAsmDetails = Field(..., description='The details required to update an external ASM.'),) -> Any:
    return invoke_dbm(
        'update_external_asm',
        external_asm_id=external_asm_id,
        update_external_asm_details=update_external_asm_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_asm_instance"],
    annotations=TOOL_ANNOTATIONS["update_external_asm_instance"],)
def update_external_asm_instance(
    external_asm_instance_id: str = Field(..., description='The OCID of the external ASM instance.'),
    update_external_asm_instance_details: dict[str, Any] | UpdateExternalAsmInstanceDetails = Field(..., description='The details required to update an external ASM instance.'),) -> Any:
    return invoke_dbm(
        'update_external_asm_instance',
        external_asm_instance_id=external_asm_instance_id,
        update_external_asm_instance_details=update_external_asm_instance_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_cluster"],
    annotations=TOOL_ANNOTATIONS["update_external_cluster"],)
def update_external_cluster(
    external_cluster_id: str = Field(..., description='The OCID of the external cluster.'),
    update_external_cluster_details: dict[str, Any] | UpdateExternalClusterDetails = Field(..., description='The details required to update an external cluster.'),) -> Any:
    return invoke_dbm(
        'update_external_cluster',
        external_cluster_id=external_cluster_id,
        update_external_cluster_details=update_external_cluster_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_cluster_instance"],
    annotations=TOOL_ANNOTATIONS["update_external_cluster_instance"],)
def update_external_cluster_instance(
    external_cluster_instance_id: str = Field(..., description='The OCID of the external cluster instance.'),
    update_external_cluster_instance_details: dict[str, Any] | UpdateExternalClusterInstanceDetails = Field(..., description='The details required to update an external cluster instance.'),) -> Any:
    return invoke_dbm(
        'update_external_cluster_instance',
        external_cluster_instance_id=external_cluster_instance_id,
        update_external_cluster_instance_details=update_external_cluster_instance_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_db_home"],
    annotations=TOOL_ANNOTATIONS["update_external_db_home"],)
def update_external_db_home(
    external_db_home_id: str = Field(..., description='The OCID of the external database home.'),
    update_external_db_home_details: dict[str, Any] | UpdateExternalDbHomeDetails = Field(..., description='The details required to update an external DB home.'),) -> Any:
    return invoke_dbm(
        'update_external_db_home',
        external_db_home_id=external_db_home_id,
        update_external_db_home_details=update_external_db_home_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_db_node"],
    annotations=TOOL_ANNOTATIONS["update_external_db_node"],)
def update_external_db_node(
    external_db_node_id: str = Field(..., description='The OCID of the external database node.'),
    update_external_db_node_details: dict[str, Any] | UpdateExternalDbNodeDetails = Field(..., description='The details required to update an external DB node.'),) -> Any:
    return invoke_dbm(
        'update_external_db_node',
        external_db_node_id=external_db_node_id,
        update_external_db_node_details=update_external_db_node_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_db_system"],
    annotations=TOOL_ANNOTATIONS["update_external_db_system"],)
def update_external_db_system(
    external_db_system_id: str = Field(..., description='The OCID of the external DB system.'),
    update_external_db_system_details: dict[str, Any] | UpdateExternalDbSystemDetails = Field(..., description='The details required to update an external DB system.'),) -> Any:
    return invoke_dbm(
        'update_external_db_system',
        external_db_system_id=external_db_system_id,
        update_external_db_system_details=update_external_db_system_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_db_system_connector"],
    annotations=TOOL_ANNOTATIONS["update_external_db_system_connector"],)
def update_external_db_system_connector(
    external_db_system_connector_id: str = Field(..., description='The OCID of the external connector.'),
    update_external_db_system_connector_details: dict[str, Any] | UpdateExternalDbSystemConnectorDetails = Field(..., description='The details required to update an external connector.'),) -> Any:
    return invoke_dbm(
        'update_external_db_system_connector',
        external_db_system_connector_id=external_db_system_connector_id,
        update_external_db_system_connector_details=update_external_db_system_connector_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_db_system_discovery"],
    annotations=TOOL_ANNOTATIONS["update_external_db_system_discovery"],)
def update_external_db_system_discovery(
    external_db_system_discovery_id: str = Field(..., description='The OCID of the external DB system discovery.'),
    update_external_db_system_discovery_details: dict[str, Any] | UpdateExternalDbSystemDiscoveryDetails = Field(..., description='The details required to update an external DB system discovery.'),) -> Any:
    return invoke_dbm(
        'update_external_db_system_discovery',
        external_db_system_discovery_id=external_db_system_discovery_id,
        update_external_db_system_discovery_details=update_external_db_system_discovery_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_exadata_infrastructure"],
    annotations=TOOL_ANNOTATIONS["update_external_exadata_infrastructure"],)
def update_external_exadata_infrastructure(
    external_exadata_infrastructure_id: str = Field(..., description='The OCID of the Exadata infrastructure.'),
    update_external_exadata_infrastructure_details: dict[str, Any] | UpdateExternalExadataInfrastructureDetails = Field(..., description='The details required to update the managed Exadata infrastructure resources.'),) -> Any:
    return invoke_dbm(
        'update_external_exadata_infrastructure',
        external_exadata_infrastructure_id=external_exadata_infrastructure_id,
        update_external_exadata_infrastructure_details=update_external_exadata_infrastructure_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_exadata_storage_connector"],
    annotations=TOOL_ANNOTATIONS["update_external_exadata_storage_connector"],)
def update_external_exadata_storage_connector(
    external_exadata_storage_connector_id: str = Field(..., description='The OCID of the connector to the Exadata storage server.'),
    update_external_exadata_storage_connector_details: dict[str, Any] | UpdateExternalExadataStorageConnectorDetails = Field(..., description='The details required to update connections to the Exadata storage servers.'),) -> Any:
    return invoke_dbm(
        'update_external_exadata_storage_connector',
        external_exadata_storage_connector_id=external_exadata_storage_connector_id,
        update_external_exadata_storage_connector_details=update_external_exadata_storage_connector_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_exadata_storage_grid"],
    annotations=TOOL_ANNOTATIONS["update_external_exadata_storage_grid"],)
def update_external_exadata_storage_grid(
    external_exadata_storage_grid_id: str = Field(..., description='The OCID of the Exadata storage grid.'),
    update_external_exadata_storage_grid_details: dict[str, Any] | UpdateExternalExadataStorageGridDetails = Field(..., description='The details required to update an external Exadata storage grid.'),) -> Any:
    return invoke_dbm(
        'update_external_exadata_storage_grid',
        external_exadata_storage_grid_id=external_exadata_storage_grid_id,
        update_external_exadata_storage_grid_details=update_external_exadata_storage_grid_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_exadata_storage_server"],
    annotations=TOOL_ANNOTATIONS["update_external_exadata_storage_server"],)
def update_external_exadata_storage_server(
    external_exadata_storage_server_id: str = Field(..., description='The OCID of the Exadata storage server.'),
    update_external_exadata_storage_server_details: dict[str, Any] | UpdateExternalExadataStorageServerDetails = Field(..., description='The details required to update an external Exadata storage server.'),) -> Any:
    return invoke_dbm(
        'update_external_exadata_storage_server',
        external_exadata_storage_server_id=external_exadata_storage_server_id,
        update_external_exadata_storage_server_details=update_external_exadata_storage_server_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_external_listener"],
    annotations=TOOL_ANNOTATIONS["update_external_listener"],)
def update_external_listener(
    external_listener_id: str = Field(..., description='The OCID of the external listener.'),
    update_external_listener_details: dict[str, Any] | UpdateExternalListenerDetails = Field(..., description='The details required to update an external listener.'),) -> Any:
    return invoke_dbm(
        'update_external_listener',
        external_listener_id=external_listener_id,
        update_external_listener_details=update_external_listener_details,)






@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_job"],
    annotations=TOOL_ANNOTATIONS["update_job"],)
def update_job(
    job_id: str = Field(..., description='The identifier of the job.'),
    update_job_details: dict[str, Any] | UpdateJobDetails = Field(..., description='The details required to update a job.'),) -> Any:
    return invoke_dbm(
        'update_job',
        job_id=job_id,
        update_job_details=update_job_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_managed_database"],
    annotations=TOOL_ANNOTATIONS["update_managed_database"],)
def update_managed_database(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    update_managed_database_details: dict[str, Any] | UpdateManagedDatabaseDetails = Field(..., description='The details required to update a Managed Database.'),) -> Any:
    return invoke_dbm(
        'update_managed_database',
        managed_database_id=managed_database_id,
        update_managed_database_details=update_managed_database_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_managed_database_group"],
    annotations=TOOL_ANNOTATIONS["update_managed_database_group"],)
def update_managed_database_group(
    managed_database_group_id: str = Field(..., description='The OCID of the Managed Database Group.'),
    update_managed_database_group_details: dict[str, Any] | UpdateManagedDatabaseGroupDetails = Field(..., description='The details required to update a Managed Database Group.'),) -> Any:
    return invoke_dbm(
        'update_managed_database_group',
        managed_database_group_id=managed_database_group_id,
        update_managed_database_group_details=update_managed_database_group_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_named_credential"],
    annotations=TOOL_ANNOTATIONS["update_named_credential"],)
def update_named_credential(
    named_credential_id: str = Field(..., description='The OCID of the named credential.'),
    update_named_credential_details: dict[str, Any] | UpdateNamedCredentialDetails = Field(..., description='The details required to update a named credential.'),) -> Any:
    return invoke_dbm(
        'update_named_credential',
        named_credential_id=named_credential_id,
        update_named_credential_details=update_named_credential_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_preferred_credential"],
    annotations=TOOL_ANNOTATIONS["update_preferred_credential"],)
def update_preferred_credential(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    credential_name: str = Field(..., description='The name of the preferred credential.'),
    update_preferred_credential_details: dict[str, Any] | UpdatePreferredCredentialDetails = Field(..., description='The details required to update preferred credential.'),) -> Any:
    return invoke_dbm(
        'update_preferred_credential',
        managed_database_id=managed_database_id,
        credential_name=credential_name,
        update_preferred_credential_details=update_preferred_credential_details,)


@mcp.tool(
    description=TOOL_DESCRIPTIONS["update_tablespace"],
    annotations=TOOL_ANNOTATIONS["update_tablespace"],)
def update_tablespace(
    managed_database_id: str = Field(..., description='The OCID of the Managed Database.'),
    tablespace_name: str = Field(..., description='The name of the tablespace.'),
    update_tablespace_details: dict[str, Any] | UpdateTablespaceDetails = Field(..., description='The details required to update a tablespace.'),) -> Any:
    return invoke_dbm(
        'update_tablespace',
        managed_database_id=managed_database_id,
        tablespace_name=tablespace_name,
        update_tablespace_details=update_tablespace_details,)

