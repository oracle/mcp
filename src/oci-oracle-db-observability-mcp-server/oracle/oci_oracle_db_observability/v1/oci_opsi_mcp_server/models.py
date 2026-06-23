"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at

"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from oracle.oci_oracle_db_observability.v1.conversion import to_plain_data


class OpsiBaseModel(BaseModel):
    """Base model for OCI OPSI MCP schemas."""

    model_config = ConfigDict(
        alias_generator=None,
        arbitrary_types_allowed=True,
        extra="allow",
        populate_by_name=True,)

    @classmethod
    def from_oci(cls, value: Any):
        return cls.model_validate(to_plain_data(value))


class OpsiRequestModel(OpsiBaseModel):
    """Base model for OCI OPSI request schemas."""

    model_config = ConfigDict(
        alias_generator=None,
        arbitrary_types_allowed=True,
        extra="forbid",
        populate_by_name=True,)


CompartmentAccessLevel = Literal["ANY", "ACCESSIBLE"]
CompartmentLifecycleState = Literal["CREATING", "ACTIVE", "INACTIVE", "DELETING", "DELETED", "UNKNOWN_ENUM_VALUE"]


class Compartment(OpsiBaseModel):
    """OCI Identity compartment metadata."""

    id: str = Field(..., description="The OCID of the compartment.")
    compartment_id: str | None = Field(
        None,
        alias="compartmentId",
        description="The OCID of the parent compartment.",)
    name: str | None = Field(None, description="The compartment name.")
    description: str | None = Field(None, description="The compartment description.")
    lifecycle_state: CompartmentLifecycleState | None = Field(
        None,
        alias="lifecycleState",
        description="The current lifecycle state of the compartment.",)
    time_created: datetime | None = Field(
        None,
        alias="timeCreated",
        description="The date and time the compartment was created.",)
    inactive_status: int | None = Field(
        None,
        alias="inactiveStatus",
        ge=0,
        description="The status of the compartment if it is inactive.",)
    freeform_tags: dict[str, str] | None = Field(
        None,
        alias="freeformTags",
        description="Free-form tags returned for the compartment.",)
    defined_tags: dict[str, dict[str, Any]] | None = Field(
        None,
        alias="definedTags",
        description="Defined tags returned for the compartment.",)
    system_tags: dict[str, dict[str, Any]] | None = Field(
        None,
        alias="systemTags",
        description="System tags returned for the compartment.",)


class CompartmentCollection(OpsiBaseModel):
    """Collection of OCI Identity compartments."""

    items: list[Compartment] = Field(..., description="Compartments returned by the list request.")
    count: int = Field(..., ge=0, description="Number of compartments returned.")


class AddEmManagedExternalExadataInsightMembersDetails(OpsiBaseModel):
    """The information about the members of Exadata system to be added. If memberEntityDetails is not specified, the the Enterprise Manager entity (e.g. databases and hosts) associated with an Exadata system will be placed in the same compartment as the Exadata system."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Gets the entity_source of this AddExadataInsightMembersDetails.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')
    member_entity_details: list[CreateEmManagedExternalExadataMemberEntityDetails] | None = Field(None, alias='memberEntityDetails', description='The member_entity_details field of AddEmManagedExternalExadataInsightMembersDetails.')


class AddExadataInsightMembersDetails(OpsiRequestModel):
    """The information about the members of Exadata system to be added."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Source of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')


class AddMacsManagedCloudExadataInsightMembersDetails(OpsiBaseModel):
    """The information about the members of Exadata system to be added."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Gets the entity_source of this AddExadataInsightMembersDetails.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')
    member_entity_details: list[CreateMacsManagedCloudExadataVmclusterDetails] | None = Field(None, alias='memberEntityDetails', description='The member_entity_details field of AddMacsManagedCloudExadataInsightMembersDetails.')


class AddPeComanagedExadataInsightMembersDetails(OpsiBaseModel):
    """The information about the members of Exadata system to be added."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Gets the entity_source of this AddExadataInsightMembersDetails.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')
    member_entity_details: list[CreatePeComanagedExadataVmclusterDetails] | None = Field(None, alias='memberEntityDetails', description='The member_entity_details field of AddPeComanagedExadataInsightMembersDetails.')


class AddmDbCollection(OpsiBaseModel):
    """The result of ADDM databases."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    items: list[AddmDbSummary] = Field(..., alias='items', description='List of ADDM database summary data')


class AddmDbFindingAggregation(OpsiBaseModel):
    """Summarizes a specific ADDM finding."""

    id: str = Field(..., alias='id', description='The OCID of the Database insight.')
    finding_id: str = Field(..., alias='findingId', description='Unique finding id')
    category_name: str = Field(..., alias='categoryName', description='Category name')
    category_display_name: str = Field(..., alias='categoryDisplayName', description='Category display name')
    name: str = Field(..., alias='name', description='Finding name')
    message: str = Field(..., alias='message', description='Finding message')
    impact_overall_percent: float = Field(..., alias='impactOverallPercent', description='Overall impact in terms of percentage of total activity')
    impact_max_percent: float = Field(..., alias='impactMaxPercent', description='Maximum impact in terms of percentage of total activity')
    impact_avg_active_sessions: float | None = Field(None, alias='impactAvgActiveSessions', description='Impact in terms of average active sessions')
    frequency_count: int = Field(..., alias='frequencyCount', description='Number of occurrences for this finding', ge=0)
    recommendation_count: int = Field(..., alias='recommendationCount', description='Number of recommendations for this finding', ge=0)


class AddmDbFindingAggregationCollection(OpsiBaseModel):
    """Summarizes ADDM findings over specified time period."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    database_details_items: list[DatabaseDetails] = Field(..., alias='databaseDetailsItems', description='List of database details data')
    items: list[AddmDbFindingAggregation] = Field(..., alias='items', description='List of ADDM finding summaries')


class AddmDbFindingCategoryCollection(OpsiBaseModel):
    """List of finding categories."""

    database_details_items: list[DatabaseDetails] = Field(..., alias='databaseDetailsItems', description='List of database details data')
    items: list[AddmDbFindingCategorySummary] = Field(..., alias='items', description='List of finding categories')


class AddmDbFindingCategorySummary(OpsiBaseModel):
    """Finding category summary."""

    id: str = Field(..., alias='id', description='The OCID of the Database insight.')
    name: str = Field(..., alias='name', description='Name of finding category')
    display_name: str = Field(..., alias='displayName', description='Display name of finding category')


class AddmDbFindingsTimeSeriesCollection(OpsiBaseModel):
    """ADDM findings time series response."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    database_details_items: list[DatabaseDetails] = Field(..., alias='databaseDetailsItems', description='List of database details data')
    items: list[AddmDbFindingsTimeSeriesSummary] = Field(..., alias='items', description='List of ADDM finding time series data')


class AddmDbFindingsTimeSeriesSummary(OpsiBaseModel):
    """ADDM findings time series data."""

    id: str = Field(..., alias='id', description='The OCID of the Database insight.')
    task_id: int = Field(..., alias='taskId', description='Unique ADDM task id')
    task_name: str = Field(..., alias='taskName', description='ADDM task name')
    finding_id: str = Field(..., alias='findingId', description='Unique finding id')
    timestamp: datetime = Field(..., alias='timestamp', description='Timestamp when finding was generated')
    time_analysis_started: datetime | None = Field(None, alias='timeAnalysisStarted', description='Start Timestamp of snapshot')
    time_analysis_ended: datetime | None = Field(None, alias='timeAnalysisEnded', description='End Timestamp of snapshot')
    category_name: str = Field(..., alias='categoryName', description='Category name')
    category_display_name: str = Field(..., alias='categoryDisplayName', description='Category display name')
    name: str = Field(..., alias='name', description='Finding name')
    message: str = Field(..., alias='message', description='Finding message')
    analysis_db_time_in_secs: float | None = Field(None, alias='analysisDbTimeInSecs', description='DB time in seconds for the snapshot')
    analysis_avg_active_sessions: float | None = Field(None, alias='analysisAvgActiveSessions', description='DB avg active sessions for the snapshot')
    impact_db_time_in_secs: float | None = Field(None, alias='impactDbTimeInSecs', description='Impact in seconds')
    impact_percent: float = Field(..., alias='impactPercent', description='Impact in terms of percentage of total activity')
    impact_avg_active_sessions: float = Field(..., alias='impactAvgActiveSessions', description='Impact in terms of average active sessions')


class AddmDbParameterAggregation(OpsiBaseModel):
    """Summarizes change history for specific database parameter."""

    id: str = Field(..., alias='id', description='The OCID of the Database insight.')
    name: str = Field(..., alias='name', description='Name of  parameter')
    inst_num: int | None = Field(None, alias='instNum', description='Number of database instance')
    default_value: str | None = Field(None, alias='defaultValue', description='Parameter default value')
    begin_value: str | None = Field(None, alias='beginValue', description='Parameter value when time period began')
    end_value: str | None = Field(None, alias='endValue', description='Parameter value when time period ended')
    is_changed: bool = Field(..., alias='isChanged', description="Indicates whether the parameter's value changed during the selected time range (TRUE) or\ndid not change during the selected time range (FALSE)")
    is_default: bool | None = Field(None, alias='isDefault', description="Indicates whether the parameter's end value was set to the default value (TRUE) or was\nspecified in the parameter file (FALSE)")
    value_modified: str | None = Field(None, alias='valueModified', description='Indicates whether the parameter has been modified after instance starup\nMODIFIED - Parameter has been modified with ALTER SESSION\nSYSTEM_MOD - Parameter has been modified with ALTER SYSTEM\nFALSE - Parameter has not been modified after instance starup')
    is_high_impact: bool | None = Field(None, alias='isHighImpact', description='Indicates whether the parameter is a high impact parameter (TRUE) or not (FALSE)')


class AddmDbParameterAggregationCollection(OpsiBaseModel):
    """Summarizes AWR parameter change history over specified time period."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    database_details_items: list[DatabaseDetails] = Field(..., alias='databaseDetailsItems', description='List of database details data')
    items: list[AddmDbParameterAggregation] = Field(..., alias='items', description='List of AWR parameter change summaries')


class AddmDbParameterCategoryCollection(OpsiBaseModel):
    """List of database parameter categories."""

    database_details_items: list[DatabaseDetails] = Field(..., alias='databaseDetailsItems', description='List of database details data')
    items: list[AddmDbParameterCategorySummary] = Field(..., alias='items', description='List of database parameter categories')


class AddmDbParameterCategorySummary(OpsiBaseModel):
    """Database parameter category summary."""

    id: str = Field(..., alias='id', description='The OCID of the Database insight.')
    name: str = Field(..., alias='name', description='Name of database parameter category')
    display_name: str = Field(..., alias='displayName', description='Display name of database parameter  category')


class AddmDbParameterChangeAggregation(OpsiBaseModel):
    """Change record for AWR database parameter."""

    id: str = Field(..., alias='id', description='The OCID of the Database insight.')
    time_begin: datetime = Field(..., alias='timeBegin', description='Begin time of interval which includes change')
    time_end: datetime = Field(..., alias='timeEnd', description='End time of interval which includes change')
    inst_num: int = Field(..., alias='instNum', description='Instance number')
    previous_value: str | None = Field(None, alias='previousValue', description='Previous value')
    value: str | None = Field(None, alias='value', description='Current value')
    snapshot_id: int = Field(..., alias='snapshotId', description='AWR snapshot id which includes the parameter value change')


class AddmDbParameterChangeAggregationCollection(OpsiBaseModel):
    """Summarizes AWR parameter change history over specified time period for specified parameter."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    database_details_items: list[DatabaseDetails] = Field(..., alias='databaseDetailsItems', description='List of database details data')
    items: list[AddmDbParameterChangeAggregation] = Field(..., alias='items', description='List of AWR parameter changes')


class AddmDbRecommendationAggregation(OpsiBaseModel):
    """Summarizes a specific ADDM recommendation."""

    id: str = Field(..., alias='id', description='The OCID of the Database insight.')
    type: str | None = Field(None, alias='type', description='Type of recommendation')
    message: str = Field(..., alias='message', description='Recommendation message')
    requires_db_restart: str | None = Field(None, alias='requiresDbRestart', description='Indicates implementation of the recommended action requires a database restart in order for it\nto take effect. Possible values "Y", "N" and null.')
    implement_actions: list[str] | None = Field(None, alias='implementActions', description="Actions that can be performed to implement the recommendation (such as 'ALTER PARAMETER',\n'RUN SQL TUNING ADVISOR')")
    rationale: str | None = Field(None, alias='rationale', description='Recommendation message')
    max_benefit_percent: float | None = Field(None, alias='maxBenefitPercent', description='Maximum estimated benefit in terms of percentage of total activity')
    overall_benefit_percent: float | None = Field(None, alias='overallBenefitPercent', description='Overall estimated benefit in terms of percentage of total activity')
    max_benefit_avg_active_sessions: float | None = Field(None, alias='maxBenefitAvgActiveSessions', description='Maximum estimated benefit in terms of average active sessions')
    frequency_count: int | None = Field(None, alias='frequencyCount', description='Number of occurrences for this recommendation', ge=0)
    related_object: RelatedObjectTypeDetails | None = Field(None, alias='relatedObject', description='The related_object field of AddmDbRecommendationAggregation.')


class AddmDbRecommendationAggregationCollection(OpsiBaseModel):
    """Summarizes ADDM recommendations over specified time period."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    database_details_items: list[DatabaseDetails] = Field(..., alias='databaseDetailsItems', description='List of database details data')
    items: list[AddmDbRecommendationAggregation] = Field(..., alias='items', description='List of ADDM recommendation summaries')


class AddmDbRecommendationCategoryCollection(OpsiBaseModel):
    """List of recommendation categories."""

    database_details_items: list[DatabaseDetails] = Field(..., alias='databaseDetailsItems', description='List of database details data')
    items: list[AddmDbRecommendationCategorySummary] = Field(..., alias='items', description='List of recommendation categories')


class AddmDbRecommendationCategorySummary(OpsiBaseModel):
    """Recommendation category summary."""

    id: str = Field(..., alias='id', description='The OCID of the Database insight.')
    name: str = Field(..., alias='name', description='Name of recommendation category')
    display_name: str = Field(..., alias='displayName', description='Display name of recommendation  category')


class AddmDbRecommendationsTimeSeriesCollection(OpsiBaseModel):
    """ADDM recommendations time series."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    database_details_items: list[DatabaseDetails] = Field(..., alias='databaseDetailsItems', description='List of database details data')
    items: list[AddmDbRecommendationsTimeSeriesSummary] = Field(..., alias='items', description='List of ADDM recommendations time series data')


class AddmDbRecommendationsTimeSeriesSummary(OpsiBaseModel):
    """ADDM recommendation."""

    id: str = Field(..., alias='id', description='The OCID of the Database insight.')
    task_id: int = Field(..., alias='taskId', description='Unique ADDM task id')
    task_name: str = Field(..., alias='taskName', description='ADDM task name')
    timestamp: datetime = Field(..., alias='timestamp', description='Timestamp when recommendation was generated')
    time_analysis_started: datetime | None = Field(None, alias='timeAnalysisStarted', description='Start Timestamp of snapshot')
    time_analysis_ended: datetime | None = Field(None, alias='timeAnalysisEnded', description='End Timestamp of snapshot')
    type: str | None = Field(None, alias='type', description='Type of recommendation')
    analysis_db_time_in_secs: float | None = Field(None, alias='analysisDbTimeInSecs', description='DB time in seconds for the snapshot')
    analysis_avg_active_sessions: float | None = Field(None, alias='analysisAvgActiveSessions', description='DB avg active sessions for the snapshot')
    max_benefit_percent: float | None = Field(None, alias='maxBenefitPercent', description='Maximum estimated benefit in terms of percentage of total activity')
    max_benefit_db_time_in_secs: float | None = Field(None, alias='maxBenefitDbTimeInSecs', description='Maximum estimated benefit in terms of seconds')
    max_benefit_avg_active_sessions: float | None = Field(None, alias='maxBenefitAvgActiveSessions', description='Maximum estimated benefit in terms of average active sessions')
    related_object: RelatedObjectTypeDetails | None = Field(None, alias='relatedObject', description='The related_object field of AddmDbRecommendationsTimeSeriesSummary.')


class AddmDbSchemaObjectCollection(OpsiBaseModel):
    """Summarizes Schema Objects over specified time period."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    database_details_items: list[DatabaseDetails] = Field(..., alias='databaseDetailsItems', description='List of database details data')
    items: list[AddmDbSchemaObjectSummary] = Field(..., alias='items', description='List of Schema Objects')


class AddmDbSchemaObjectSummary(OpsiBaseModel):
    """Details for a given object id."""

    id: str = Field(..., alias='id', description='The OCID of the Database insight.')
    object_identifier: int = Field(..., alias='objectIdentifier', description='Object id (from RDBMS)')
    owner: str = Field(..., alias='owner', description='Owner of object')
    object_name: str = Field(..., alias='objectName', description='Name of object')
    sub_object_name: str | None = Field(None, alias='subObjectName', description='Subobject name; for example, partition name')
    object_type: str = Field(..., alias='objectType', description='Type of the object (such as TABLE, INDEX)')


class AddmDbSqlStatementCollection(OpsiBaseModel):
    """Summarizes SQL statements over specified time period."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    database_details_items: list[DatabaseDetails] = Field(..., alias='databaseDetailsItems', description='List of database details data')
    items: list[AddmDbSqlStatementSummary] = Field(..., alias='items', description='List of SQL statements')


class AddmDbSqlStatementSummary(OpsiBaseModel):
    """Details for a given SQL ID."""

    id: str = Field(..., alias='id', description='The OCID of the Database insight.')
    sql_identifier: str = Field(..., alias='sqlIdentifier', description='SQL identifier')
    sql_text: str = Field(..., alias='sqlText', description='First 3800 characters of the SQL text')
    is_sql_text_truncated: bool = Field(..., alias='isSqlTextTruncated', description='SQL identifier')
    sql_command: str = Field(..., alias='sqlCommand', description='SQL command name (such as SELECT, INSERT)')


class AddmDbSummary(OpsiBaseModel):
    """ADDM summary for a database."""

    database_details: DatabaseDetails = Field(..., alias='databaseDetails', description='The database_details field of AddmDbSummary.')
    number_of_findings: int | None = Field(None, alias='numberOfFindings', description='Number of ADDM findings')
    number_of_addm_tasks: int | None = Field(None, alias='numberOfAddmTasks', description='Number of ADDM tasks')
    time_first_snapshot_begin: datetime | None = Field(None, alias='timeFirstSnapshotBegin', description='The start timestamp that was passed into the request.')
    time_latest_snapshot_end: datetime | None = Field(None, alias='timeLatestSnapshotEnd', description='The end timestamp that was passed into the request.')
    snapshot_interval_start: str | None = Field(None, alias='snapshotIntervalStart', description='AWR snapshot id.')
    snapshot_interval_end: str | None = Field(None, alias='snapshotIntervalEnd', description='AWR snapshot id.')
    max_overall_impact: float | None = Field(None, alias='maxOverallImpact', description='Maximum overall impact in terms of percentage of total activity')
    most_frequent_category_name: str | None = Field(None, alias='mostFrequentCategoryName', description='Category name')
    most_frequent_category_display_name: str | None = Field(None, alias='mostFrequentCategoryDisplayName', description='Category display name')


class AddmReport(OpsiBaseModel):
    """ADDM Tasks."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    task_identifier: str = Field(..., alias='taskIdentifier', description='TASK_ID in the oracle database view DBA_ADDM_TASKS')
    database_identifier: str = Field(..., alias='databaseIdentifier', description='Internal id of the database.')
    snapshot_interval_start: str = Field(..., alias='snapshotIntervalStart', description='AWR snapshot id.')
    snapshot_interval_end: str = Field(..., alias='snapshotIntervalEnd', description='AWR snapshot id.')
    addm_report: str = Field(..., alias='addmReport', description='The complete ADDM report')


class AutonomousDatabaseConfigurationSummary(OpsiBaseModel):
    """Configuration Summary of autonomous database."""

    database_insight_id: str = Field(..., alias='databaseInsightId', description='Gets the database_insight_id of this DatabaseConfigurationSummary. The OCID of the database insight resource.')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseConfigurationSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseConfigurationSummary. The OCID of the compartment.')
    database_name: str = Field(..., alias='databaseName', description='Gets the database_name of this DatabaseConfigurationSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str = Field(..., alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseConfigurationSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str = Field(..., alias='databaseType', description='Gets the database_type of this DatabaseConfigurationSummary.\nOps Insights internal representation of the database type.')
    database_version: str = Field(..., alias='databaseVersion', description='Gets the database_version of this DatabaseConfigurationSummary.\nThe version of the database.')
    is_advanced_features_enabled: bool = Field(..., alias='isAdvancedFeaturesEnabled', description='Gets the is_advanced_features_enabled of this DatabaseConfigurationSummary.\nFlag is to identify if advanced features for autonomous database is enabled or not')
    cdb_name: str = Field(..., alias='cdbName', description='Gets the cdb_name of this DatabaseConfigurationSummary.\nName of the CDB.Only applies to PDB.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseConfigurationSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')


class AutonomousDatabaseInsight(OpsiBaseModel):
    """Database insight resource."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsight.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsight.\nDatabase insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseInsight.\nCompartment identifier of the database')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this DatabaseInsight.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsight.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsight.\nThe version of the database.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this DatabaseInsight.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsight.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsight.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsight.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    database_name: str = Field(..., alias='databaseName', description='Name of database')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Display name of database')
    database_resource_type: str = Field(..., alias='databaseResourceType', description='OCI database resource type')
    db_additional_details: Any | None = Field(None, alias='dbAdditionalDetails', description='Additional details of a database in JSON format. For autonomous databases, this is the AutonomousDatabase object serialized as a JSON string as defined in  For EM, pass in null or an empty string. Note that this string needs to be escaped when specified in the curl command.')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    is_advanced_features_enabled: bool | None = Field(None, alias='isAdvancedFeaturesEnabled', description='Flag is to identify if advanced features for autonomous database is enabled or not')
    connection_details: ConnectionDetails | None = Field(None, alias='connectionDetails', description='The connection_details field of AutonomousDatabaseInsight.')
    credential_details: CredentialDetails | None = Field(None, alias='credentialDetails', description='The credential_details field of AutonomousDatabaseInsight.')


class AutonomousDatabaseInsightSummary(OpsiBaseModel):
    """Summary of a database insight resource."""

    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsightSummary. The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='Gets the database_id of this DatabaseInsightSummary. The OCID of the database.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='Gets the compartment_id of this DatabaseInsightSummary. The OCID of the compartment.')
    database_name: str | None = Field(None, alias='databaseName', description='Gets the database_name of this DatabaseInsightSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseInsightSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsightSummary.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsightSummary.\nThe version of the database.')
    database_host_names: list[str] | None = Field(None, alias='databaseHostNames', description='Gets the database_host_names of this DatabaseInsightSummary.\nThe hostnames for the database.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this DatabaseInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsightSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this DatabaseInsightSummary.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this DatabaseInsightSummary.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsightSummary.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsightSummary.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsightSummary.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    database_resource_type: str | None = Field(None, alias='databaseResourceType', description='OCI database resource type')
    is_advanced_features_enabled: bool | None = Field(None, alias='isAdvancedFeaturesEnabled', description='Flag is to identify if advanced features for autonomous database is enabled or not')


class AwrDatabaseCollection(OpsiBaseModel):
    """The result of AWR query."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[AwrDatabaseSummary] | None = Field(None, alias='items', description='A list of AWR summary data.')


class AwrDatabaseCpuUsageCollection(OpsiBaseModel):
    """The AWR CPU usage data."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    num_cpu_cores: int | None = Field(None, alias='numCpuCores', description='The number of available CPU cores, which include subcores of multicore and single-core CPUs.')
    database_cpu_count: int | None = Field(None, alias='databaseCpuCount', description='The number of CPUs available for the database to use.', ge=0)
    host_cpu_count: float | None = Field(None, alias='hostCpuCount', description='The number of available CPUs or processors.', ge=0)
    items: list[AwrDatabaseCpuUsageSummary] | None = Field(None, alias='items', description='A list of AWR CPU usage summary data.')


class AwrDatabaseCpuUsageSummary(OpsiBaseModel):
    """A summary of the AWR CPU resource limits and metrics."""

    timestamp: datetime | None = Field(None, alias='timestamp', description='The timestamp for the CPU summary data.')
    avg_usage_in_secs: float | None = Field(None, alias='avgUsageInSecs', description='The average CPU usage per second.')


class AwrDatabaseMetricCollection(OpsiBaseModel):
    """The AWR metrics time series summary data."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[AwrDatabaseMetricSummary] | None = Field(None, alias='items', description='A list of AWR metric summary data.')


class AwrDatabaseMetricSummary(OpsiBaseModel):
    """The summary of the AWR metric data for a particular metric at a specific time."""

    name: str = Field(..., alias='name', description='The name of the metric.')
    timestamp: datetime | None = Field(None, alias='timestamp', description='The time of the sampling.')
    avg_value: float | None = Field(None, alias='avgValue', description='The average value of the sampling period.')
    min_value: float | None = Field(None, alias='minValue', description='The minimum value of the sampling period.')
    max_value: float | None = Field(None, alias='maxValue', description='The maximum value of the sampling period.')


class AwrDatabaseParameterChangeCollection(OpsiBaseModel):
    """The AWR database parameter change history."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[AwrDatabaseParameterChangeSummary] | None = Field(None, alias='items', description='A list of AWR database parameter change summary data.')


class AwrDatabaseParameterChangeSummary(OpsiBaseModel):
    """A summary of the changes made to a single AWR database parameter."""

    time_begin: datetime | None = Field(None, alias='timeBegin', description='The start time of the interval.')
    time_end: datetime | None = Field(None, alias='timeEnd', description='The end time of the interval.')
    instance_number: int | None = Field(None, alias='instanceNumber', description='The database instance number.')
    previous_value: str | None = Field(None, alias='previousValue', description='The previous value of the database parameter.')
    value: str | None = Field(None, alias='value', description='The current value of the database parameter.')
    snapshot_identifier: int = Field(..., alias='snapshotIdentifier', description='AWR snapshot identifier for the snapshot where the parameter value changed. This value is not an OCID.')
    value_modified: str | None = Field(None, alias='valueModified', description='Indicates whether the parameter has been modified after instance startup:\n- MODIFIED - Parameter has been modified with ALTER SESSION\n- SYSTEM_MOD - Parameter has been modified with ALTER SYSTEM (which causes all the currently logged in sessions values to be modified)\n- FALSE - Parameter has not been modified after instance startup')
    is_default: bool | None = Field(None, alias='isDefault', description='Indicates whether the parameter value in the end snapshot is the default.')


class AwrDatabaseParameterCollection(OpsiBaseModel):
    """The AWR database parameter data."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[AwrDatabaseParameterSummary] | None = Field(None, alias='items', description='A list of AWR database parameter summary data.')


class AwrDatabaseParameterSummary(OpsiBaseModel):
    """The summary of the AWR change history data for a single database parameter."""

    name: str = Field(..., alias='name', description='The name of the parameter.')
    instance_number: int | None = Field(None, alias='instanceNumber', description='The database instance number.')
    begin_value: str | None = Field(None, alias='beginValue', description='The parameter value when the period began.')
    end_value: str | None = Field(None, alias='endValue', description='The parameter value when the period ended.')
    is_changed: bool | None = Field(None, alias='isChanged', description='Indicates whether the parameter value changed within the period.')
    value_modified: str | None = Field(None, alias='valueModified', description='Indicates whether the parameter has been modified after instance startup:\n- MODIFIED - Parameter has been modified with ALTER SESSION\n- SYSTEM_MOD - Parameter has been modified with ALTER SYSTEM (which causes all the currently logged in sessions values to be modified)\n- FALSE - Parameter has not been modified after instance startup')
    is_default: bool | None = Field(None, alias='isDefault', description='Indicates whether the parameter value in the end snapshot is the default.')


class AwrDatabaseReport(OpsiBaseModel):
    """The result of the AWR report."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    content: str | None = Field(None, alias='content', description='The content of the report.')
    format: Literal['HTML', 'TEXT', 'XML', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='format', description='The format of the report.\n\nAllowed values for this property are: "HTML", "TEXT", "XML", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class AwrDatabaseSnapshotCollection(OpsiBaseModel):
    """The list of AWR snapshots for one database."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[AwrDatabaseSnapshotSummary] | None = Field(None, alias='items', description='A list of AWR snapshot summary data.')


class AwrDatabaseSnapshotRangeCollection(OpsiBaseModel):
    """The AWR snapshot range list."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[AwrDatabaseSnapshotRangeSummary] | None = Field(None, alias='items', description='A list of AWR snapshot range summary data.')


class AwrDatabaseSnapshotRangeSummary(OpsiBaseModel):
    """The summary data for a range of AWR snapshots."""

    awr_source_database_identifier: str = Field(..., alias='awrSourceDatabaseIdentifier', description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.')
    db_name: str = Field(..., alias='dbName', description='The name of the database.')
    instance_list: list[int] | None = Field(None, alias='instanceList', description='The database instance numbers.')
    time_db_startup: datetime | None = Field(None, alias='timeDbStartup', description='The timestamp of the database startup.')
    time_first_snapshot_begin: datetime | None = Field(None, alias='timeFirstSnapshotBegin', description='The start time of the earliest snapshot.')
    time_latest_snapshot_end: datetime | None = Field(None, alias='timeLatestSnapshotEnd', description='The end time of the latest snapshot.')
    first_snapshot_identifier: int | None = Field(None, alias='firstSnapshotIdentifier', description='Earliest AWR snapshot identifier in the range. This value is not an OCID; use snapshot identifiers returned by AWR snapshot listing results.')
    latest_snapshot_identifier: int | None = Field(None, alias='latestSnapshotIdentifier', description='Latest AWR snapshot identifier in the range. This value is not an OCID; use snapshot identifiers returned by AWR snapshot listing results.')
    snapshot_count: int | None = Field(None, alias='snapshotCount', description='The total number of snapshots.', ge=0)
    snapshot_interval_in_min: int | None = Field(None, alias='snapshotIntervalInMin', description='The interval time between snapshots (in minutes).')
    db_version: str | None = Field(None, alias='dbVersion', description='The version of the database.')
    snapshot_timezone: str | None = Field(None, alias='snapshotTimezone', description='The time zone of the snapshot. sample -  snapshotTimezone=+0 00:00:00')


class AwrDatabaseSnapshotSummary(OpsiBaseModel):
    """The AWR snapshot summary of one snapshot."""

    awr_source_database_identifier: str = Field(..., alias='awrSourceDatabaseIdentifier', description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.')
    instance_number: int | None = Field(None, alias='instanceNumber', description='The database instance number.')
    time_db_startup: datetime | None = Field(None, alias='timeDbStartup', description='The timestamp of the database startup.')
    time_begin: datetime | None = Field(None, alias='timeBegin', description='The start time of the snapshot.')
    time_end: datetime | None = Field(None, alias='timeEnd', description='The end time of the snapshot.')
    snapshot_identifier: int = Field(..., alias='snapshotIdentifier', description='AWR snapshot identifier within the selected AWR database. This value is not an OCID; use snapshot identifiers returned by AWR snapshot listing results.')
    error_count: int | None = Field(None, alias='errorCount', description='The total number of errors.', ge=0)


class AwrDatabaseSqlReport(OpsiBaseModel):
    """The result of the AWR SQL report."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    content: str | None = Field(None, alias='content', description='The content of the report.')
    format: Literal['HTML', 'TEXT', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='format', description='The format of the report.\n\nAllowed values for this property are: "HTML", "TEXT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class AwrDatabaseSummary(OpsiBaseModel):
    """The AWR summary for a database."""

    awr_source_database_identifier: str = Field(..., alias='awrSourceDatabaseIdentifier', description='Internal AWR source database identifier for the database in the AWR Hub. This value is not an OCID; use the identifier returned by AWR Hub database listing results.')
    db_name: str = Field(..., alias='dbName', description='The name of the database.')
    instance_list: list[int] | None = Field(None, alias='instanceList', description='The database instance numbers.')
    time_db_startup: datetime | None = Field(None, alias='timeDbStartup', description='The timestamp of the database startup.')
    time_first_snapshot_begin: datetime | None = Field(None, alias='timeFirstSnapshotBegin', description='The start time of the earliest snapshot.')
    time_latest_snapshot_end: datetime | None = Field(None, alias='timeLatestSnapshotEnd', description='The end time of the latest snapshot.')
    first_snapshot_identifier: int | None = Field(None, alias='firstSnapshotIdentifier', description='Earliest AWR snapshot identifier in the range. This value is not an OCID; use snapshot identifiers returned by AWR snapshot listing results.')
    latest_snapshot_identifier: int | None = Field(None, alias='latestSnapshotIdentifier', description='Latest AWR snapshot identifier in the range. This value is not an OCID; use snapshot identifiers returned by AWR snapshot listing results.')
    snapshot_count: int | None = Field(None, alias='snapshotCount', description='The total number of snapshots.', ge=0)
    snapshot_interval_in_min: int | None = Field(None, alias='snapshotIntervalInMin', description='The interval time between snapshots (in minutes).')
    db_version: str | None = Field(None, alias='dbVersion', description='The version of the database.')
    snapshot_timezone: str | None = Field(None, alias='snapshotTimezone', description='The time zone of the snapshot. sample -  snapshotTimezone=+0 00:00:00')


class AwrDatabaseSysstatCollection(OpsiBaseModel):
    """The AWR SYSSTAT time series summary data."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[AwrDatabaseSysstatSummary] | None = Field(None, alias='items', description='A list of AWR SYSSTAT summary data.')


class AwrDatabaseSysstatSummary(OpsiBaseModel):
    """The summary of the AWR SYSSTAT data."""

    name: str = Field(..., alias='name', description='The name of the SYSSTAT.')
    category: str | None = Field(None, alias='category', description='The name of the SYSSTAT category.')
    time_begin: datetime | None = Field(None, alias='timeBegin', description='The start time of the SYSSTAT.')
    time_end: datetime | None = Field(None, alias='timeEnd', description='The end time of the SYSSTAT.')
    avg_value: float | None = Field(None, alias='avgValue', description='The average value of the SYSSTAT. The units are stats name/val per the time period {timeBegin - timeEnd}.')
    current_value: float | None = Field(None, alias='currentValue', description='The last value of the SYSSTAT. The units are stats name/val per the time period {timeBegin - timeEnd}.')


class AwrDatabaseTopWaitEventCollection(OpsiBaseModel):
    """The AWR top wait event data."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[AwrDatabaseTopWaitEventSummary] | None = Field(None, alias='items', description='A list of AWR top event summary data.')


class AwrDatabaseTopWaitEventSummary(OpsiBaseModel):
    """A summary of the AWR top wait event data for one event."""

    name: str = Field(..., alias='name', description='The name of the event.')
    waits_per_sec: float | None = Field(None, alias='waitsPerSec', description='The wait count per second.')
    avg_wait_time_per_sec: float | None = Field(None, alias='avgWaitTimePerSec', description='The average wait time per second.')


class AwrDatabaseWaitEventBucketCollection(OpsiBaseModel):
    """The percentage distribution of waits in the AWR wait event buckets."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    total_waits: int | None = Field(None, alias='totalWaits', description='The total waits of the database.')
    items: list[AwrDatabaseWaitEventBucketSummary] | None = Field(None, alias='items', description='A list of AWR wait event buckets.')


class AwrDatabaseWaitEventBucketSummary(OpsiBaseModel):
    """A summary of the AWR wait event bucket and waits percentage."""

    category: str = Field(..., alias='category', description='The name of the wait event frequency category. Normally, it is the upper range of the waits within the AWR wait event bucket.')
    percentage: float = Field(..., alias='percentage', description='The percentage of waits in a wait event bucket over the total waits of the database.')


class AwrDatabaseWaitEventCollection(OpsiBaseModel):
    """The AWR wait event data."""

    name: str = Field(..., alias='name', description='Gets the name of this AwrQueryResult.\nThe name of the query result.')
    version: str | None = Field(None, alias='version', description='Gets the version of this AwrQueryResult.\nThe version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='Gets the db_query_time_in_secs of this AwrQueryResult.\nThe time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='Gets the awr_result_type of this AwrQueryResult.\nThe result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[AwrDatabaseWaitEventSummary] | None = Field(None, alias='items', description='A list of AWR wait events.')


class AwrDatabaseWaitEventSummary(OpsiBaseModel):
    """The summary of the AWR wait event time series data for one event."""

    name: str = Field(..., alias='name', description='The name of the event.')
    time_begin: datetime | None = Field(None, alias='timeBegin', description='The begin time of the wait event.')
    time_end: datetime | None = Field(None, alias='timeEnd', description='The end time of the wait event.')
    waits_per_sec: float | None = Field(None, alias='waitsPerSec', description='The wait count per second.')
    avg_wait_time_per_sec: float | None = Field(None, alias='avgWaitTimePerSec', description='The average wait time per second.')
    snapshot_identifier: int | None = Field(None, alias='snapshotIdentifier', description='AWR snapshot identifier within the selected AWR database. This value is not an OCID; use snapshot identifiers returned by AWR snapshot listing results.')


class AwrHub(OpsiBaseModel):
    """Awr Hub resource."""

    operations_insights_warehouse_id: str = Field(..., alias='operationsInsightsWarehouseId', description='OPSI Warehouse OCID')
    id: str = Field(..., alias='id', description='AWR Hub OCID')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    display_name: str = Field(..., alias='displayName', description='User-friedly name of AWR Hub that does not have to be unique.')
    object_storage_bucket_name: str = Field(..., alias='objectStorageBucketName', description='Object Storage Bucket Name')
    awr_mailbox_url: str | None = Field(None, alias='awrMailboxUrl', description='Mailbox URL required for AWR hub and AWR source setup.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='The time at which the resource was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time at which the resource was last updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Possible lifecycle states\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    hub_dst_timezone_version: str | None = Field(None, alias='hubDstTimezoneVersion', description='Dst Time Zone Version of the AWR Hub')


class AwrHubObjects(OpsiBaseModel):
    """Logical grouping used for Awr Hub Object operations."""

    awr_snapshots: Any | None = Field(None, alias='awrSnapshots', description='Awr Hub Object.')


class AwrHubSource(OpsiBaseModel):
    """Awr hub source object."""

    name: str = Field(..., alias='name', description='The name of the Awr Hub source database.')
    awr_hub_id: str = Field(..., alias='awrHubId', description='AWR Hub OCID')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    type: Literal['ADW_S', 'ATP_S', 'ADW_D', 'ATP_D', 'EXTERNAL_PDB', 'EXTERNAL_NONCDB', 'COMANAGED_VM_CDB', 'COMANAGED_VM_PDB', 'COMANAGED_VM_NONCDB', 'COMANAGED_BM_CDB', 'COMANAGED_BM_PDB', 'COMANAGED_BM_NONCDB', 'COMANAGED_EXACS_CDB', 'COMANAGED_EXACS_PDB', 'COMANAGED_EXACS_NONCDB', 'LH_S', 'APEX_S', 'AJD_S', 'AVD_S', 'LH_D', 'APEX_D', 'AJD_D', 'AVD_D', 'UNDEFINED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='type', description='source type of the database\n\nAllowed values for this property are: "ADW_S", "ATP_S", "ADW_D", "ATP_D", "EXTERNAL_PDB", "EXTERNAL_NONCDB", "COMANAGED_VM_CDB", "COMANAGED_VM_PDB", "COMANAGED_VM_NONCDB", "COMANAGED_BM_CDB", "COMANAGED_BM_PDB", "COMANAGED_BM_NONCDB", "COMANAGED_EXACS_CDB", "COMANAGED_EXACS_PDB", "COMANAGED_EXACS_NONCDB", "LH_S", "APEX_S", "AJD_S", "AVD_S", "LH_D", "APEX_D", "AJD_D", "AVD_D", "UNDEFINED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='The OCID of the Awr Hub source database.')
    awr_hub_opsi_source_id: str = Field(..., alias='awrHubOpsiSourceId', description='The shorted string of the Awr Hub source database identifier.')
    source_mail_box_url: str = Field(..., alias='sourceMailBoxUrl', description='Opsi Mailbox URL based on the Awr Hub and Awr Hub source.')
    associated_resource_id: str | None = Field(None, alias='associatedResourceId', description='The OCID of the database id.')
    associated_opsi_id: str | None = Field(None, alias='associatedOpsiId', description='The OCID of the database id.')
    time_created: datetime = Field(..., alias='timeCreated', description='The time at which the resource was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time at which the resource was last updated. An RFC3339 formatted datetime string')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    is_registered_with_awr_hub: bool | None = Field(None, alias='isRegisteredWithAwrHub', description='This is `true` if the source databse is registered with a Awr Hub, otherwise `false`')
    awr_source_database_id: str | None = Field(None, alias='awrSourceDatabaseId', description='DatabaseId of the Source database for which AWR Data will be uploaded to AWR Hub.')
    min_snapshot_identifier: float | None = Field(None, alias='minSnapshotIdentifier', description='The minimum snapshot identifier of the source database for which AWR data is uploaded to AWR Hub.')
    max_snapshot_identifier: float | None = Field(None, alias='maxSnapshotIdentifier', description='The maximum snapshot identifier of the source database for which AWR data is uploaded to AWR Hub.')
    time_first_snapshot_generated: datetime | None = Field(None, alias='timeFirstSnapshotGenerated', description='The time at which the earliest snapshot was generated in the source database for which data is uploaded to AWR Hub. An RFC3339 formatted datetime string')
    time_last_snapshot_generated: datetime | None = Field(None, alias='timeLastSnapshotGenerated', description='The time at which the latest snapshot was generated in the source database for which data is uploaded to AWR Hub. An RFC3339 formatted datetime string')
    hours_since_last_import: float | None = Field(None, alias='hoursSinceLastImport', description='Number of hours since last AWR snapshots import happened from the Source database.')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='the current state of the source database\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    status: Literal['ACCEPTING', 'NOT_ACCEPTING', 'NOT_REGISTERED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Indicates the status of a source database in Operations Insights\n\nAllowed values for this property are: "ACCEPTING", "NOT_ACCEPTING", "NOT_REGISTERED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class AwrHubSourceSummary(OpsiBaseModel):
    """Awr hub source object."""

    name: str = Field(..., alias='name', description='The name of the Awr Hub source database.')
    awr_hub_id: str = Field(..., alias='awrHubId', description='AWR Hub OCID')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    type: Literal['ADW_S', 'ATP_S', 'ADW_D', 'ATP_D', 'EXTERNAL_PDB', 'EXTERNAL_NONCDB', 'COMANAGED_VM_CDB', 'COMANAGED_VM_PDB', 'COMANAGED_VM_NONCDB', 'COMANAGED_BM_CDB', 'COMANAGED_BM_PDB', 'COMANAGED_BM_NONCDB', 'COMANAGED_EXACS_CDB', 'COMANAGED_EXACS_PDB', 'COMANAGED_EXACS_NONCDB', 'LH_S', 'APEX_S', 'AJD_S', 'AVD_S', 'LH_D', 'APEX_D', 'AJD_D', 'AVD_D', 'UNDEFINED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='type', description='source type of the database\n\nAllowed values for this property are: "ADW_S", "ATP_S", "ADW_D", "ATP_D", "EXTERNAL_PDB", "EXTERNAL_NONCDB", "COMANAGED_VM_CDB", "COMANAGED_VM_PDB", "COMANAGED_VM_NONCDB", "COMANAGED_BM_CDB", "COMANAGED_BM_PDB", "COMANAGED_BM_NONCDB", "COMANAGED_EXACS_CDB", "COMANAGED_EXACS_PDB", "COMANAGED_EXACS_NONCDB", "LH_S", "APEX_S", "AJD_S", "AVD_S", "LH_D", "APEX_D", "AJD_D", "AVD_D", "UNDEFINED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='The OCID of the Awr Hub source database.')
    awr_hub_opsi_source_id: str = Field(..., alias='awrHubOpsiSourceId', description='The shorted string of the Awr Hub source database identifier.')
    source_mail_box_url: str = Field(..., alias='sourceMailBoxUrl', description='Opsi Mailbox URL based on the Awr Hub and Awr Hub source.')
    associated_resource_id: str | None = Field(None, alias='associatedResourceId', description='The OCID of the database id.')
    associated_opsi_id: str | None = Field(None, alias='associatedOpsiId', description='The OCID of the database id.')
    time_created: datetime = Field(..., alias='timeCreated', description='The time at which the resource was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time at which the resource was last updated. An RFC3339 formatted datetime string')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    is_registered_with_awr_hub: bool | None = Field(None, alias='isRegisteredWithAwrHub', description='This is `true` if the source databse is registered with a Awr Hub, otherwise `false`')
    awr_source_database_id: str | None = Field(None, alias='awrSourceDatabaseId', description='DatabaseId of the Source database for which AWR Data will be uploaded to AWR Hub.')
    min_snapshot_identifier: float | None = Field(None, alias='minSnapshotIdentifier', description='The minimum snapshot identifier of the source database for which AWR data is uploaded to AWR Hub.')
    max_snapshot_identifier: float | None = Field(None, alias='maxSnapshotIdentifier', description='The maximum snapshot identifier of the source database for which AWR data is uploaded to AWR Hub.')
    time_first_snapshot_generated: datetime | None = Field(None, alias='timeFirstSnapshotGenerated', description='The time at which the earliest snapshot was generated in the source database for which data is uploaded to AWR Hub. An RFC3339 formatted datetime string')
    time_last_snapshot_generated: datetime | None = Field(None, alias='timeLastSnapshotGenerated', description='The time at which the latest snapshot was generated in the source database for which data is uploaded to AWR Hub. An RFC3339 formatted datetime string')
    hours_since_last_import: float | None = Field(None, alias='hoursSinceLastImport', description='Number of hours since last AWR snapshots import happened from the Source database.')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='the current state of the source database\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    status: Literal['ACCEPTING', 'NOT_ACCEPTING', 'NOT_REGISTERED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Indicates the status of a source database in Operations Insights\n\nAllowed values for this property are: "ACCEPTING", "NOT_ACCEPTING", "NOT_REGISTERED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class AwrHubSourceSummaryCollection(OpsiBaseModel):
    """Collection of Awr Hub sources."""

    items: list[AwrHubSourceSummary] = Field(..., alias='items', description='Array of Awr Hub source objects.')


class AwrHubSources(OpsiBaseModel):
    """Logical grouping used for Awr Hub Source operations."""

    awr_hub_sources: Any | None = Field(None, alias='awrHubSources', description='Awr Hub Source Object.')


class AwrHubSummary(OpsiBaseModel):
    """Summary Hub resource."""

    operations_insights_warehouse_id: str = Field(..., alias='operationsInsightsWarehouseId', description='OPSI Warehouse OCID')
    id: str = Field(..., alias='id', description='AWR Hub OCID')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    display_name: str = Field(..., alias='displayName', description='User-friedly name of AWR Hub that does not have to be unique.')
    object_storage_bucket_name: str = Field(..., alias='objectStorageBucketName', description='Object Storage Bucket Name')
    awr_mailbox_url: str | None = Field(None, alias='awrMailboxUrl', description='Mailbox URL required for AWR hub and AWR source setup.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='The time at which the resource was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time at which the resource was last updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Possible lifecycle states\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')


class AwrHubSummaryCollection(OpsiBaseModel):
    """Collection of Hub resources."""

    items: list[AwrHubSummary] = Field(..., alias='items', description='Array of Hub summary objects.')


class AwrHubs(OpsiBaseModel):
    """Logical grouping used for Awr Hub operations."""

    awr_hubs: Any | None = Field(None, alias='awrHubs', description='Awr Hub Object.')


class AwrQueryResult(OpsiBaseModel):
    """The AWR query result."""

    name: str = Field(..., alias='name', description='The name of the query result.')
    version: str | None = Field(None, alias='version', description='The version of the query result.')
    db_query_time_in_secs: float | None = Field(None, alias='dbQueryTimeInSecs', description='The time taken to query the database tier (in seconds).')
    awr_result_type: Literal['AWRDB_SET', 'AWRDB_SNAPSHOT_RANGE_SET', 'AWRDB_SNAPSHOT_SET', 'AWRDB_METRICS_SET', 'AWRDB_SYSSTAT_SET', 'AWRDB_TOP_EVENT_SET', 'AWRDB_EVENT_SET', 'AWRDB_EVENT_HISTOGRAM', 'AWRDB_DB_PARAMETER_SET', 'AWRDB_DB_PARAMETER_CHANGE', 'AWRDB_ASH_CPU_USAGE_SET', 'AWRDB_DB_REPORT', 'AWRDB_SQL_REPORT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='awrResultType', description='The result type of AWR query.\n\nAllowed values for this property are: "AWRDB_SET", "AWRDB_SNAPSHOT_RANGE_SET", "AWRDB_SNAPSHOT_SET", "AWRDB_METRICS_SET", "AWRDB_SYSSTAT_SET", "AWRDB_TOP_EVENT_SET", "AWRDB_EVENT_SET", "AWRDB_EVENT_HISTOGRAM", "AWRDB_DB_PARAMETER_SET", "AWRDB_DB_PARAMETER_CHANGE", "AWRDB_ASH_CPU_USAGE_SET", "AWRDB_DB_REPORT", "AWRDB_SQL_REPORT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class AwrReport(OpsiBaseModel):
    """The result of the AWR report."""

    content: str | None = Field(None, alias='content', description='The content of the report.')
    format: Literal['HTML', 'TEXT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='format', description='The format of the report.\n\nAllowed values for this property are: "HTML", "TEXT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class AwrSnapshotCollection(OpsiBaseModel):
    """The list of AWR snapshots for one database."""

    items: list[AwrSnapshotSummary] = Field(..., alias='items', description='A list of AWR snapshot summary data.')


class AwrSnapshotSummary(OpsiBaseModel):
    """The AWR snapshot summary of one snapshot."""

    awr_source_database_id: str = Field(..., alias='awrSourceDatabaseId', description='DatabaseId of the Source database for which AWR Data will be uploaded to AWR Hub.')
    instance_number: int | None = Field(None, alias='instanceNumber', description='The database instance number.')
    time_db_startup: datetime | None = Field(None, alias='timeDbStartup', description='The timestamp of the database startup.')
    time_snapshot_begin: datetime | None = Field(None, alias='timeSnapshotBegin', description='The start time of the snapshot.')
    time_snapshot_end: datetime | None = Field(None, alias='timeSnapshotEnd', description='The end time of the snapshot.')
    snapshot_identifier: int = Field(..., alias='snapshotIdentifier', description='The identifier of the snapshot.')
    error_count: int | None = Field(None, alias='errorCount', description='The total number of errors.', ge=0)


class AwrSourceSummary(OpsiBaseModel):
    """Summary of an AwrSource."""

    awr_hub_id: str = Field(..., alias='awrHubId', description='AWR Hub OCID')
    name: str = Field(..., alias='name', description='Database name of the Source database for which AWR Data will be uploaded to AWR Hub.')
    awr_source_database_id: str = Field(..., alias='awrSourceDatabaseId', description='DatabaseId of the Source database for which AWR Data will be uploaded to AWR Hub.')
    snapshots_uploaded: float = Field(..., alias='snapshotsUploaded', description='Number of AWR snapshots uploaded from the Source database.')
    min_snapshot_identifier: float = Field(..., alias='minSnapshotIdentifier', description='The minimum snapshot identifier of the source database for which AWR data is uploaded to AWR Hub.')
    max_snapshot_identifier: float = Field(..., alias='maxSnapshotIdentifier', description='The maximum snapshot identifier of the source database for which AWR data is uploaded to AWR Hub.')
    time_first_snapshot_generated: datetime = Field(..., alias='timeFirstSnapshotGenerated', description='The time at which the earliest snapshot was generated in the source database for which data is uploaded to AWR Hub. An RFC3339 formatted datetime string')
    time_last_snapshot_generated: datetime = Field(..., alias='timeLastSnapshotGenerated', description='The time at which the latest snapshot was generated in the source database for which data is uploaded to AWR Hub. An RFC3339 formatted datetime string')
    hours_since_last_import: float = Field(..., alias='hoursSinceLastImport', description='Number of hours since last AWR snapshots import happened from the Source database.')


class BasicConfigurationItemMetadata(OpsiBaseModel):
    """Basic configuration item metadata."""

    config_item_type: Literal['BASIC', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='configItemType', description='Gets the config_item_type of this ConfigurationItemMetadata.\nType of configuration item.\n\nAllowed values for this property are: "BASIC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description='User-friendly display name for the configuration item.')
    description: str | None = Field(None, alias='description', description='Description of configuration item.')
    data_type: str | None = Field(None, alias='dataType', description='Data type of configuration item.\nExamples: STRING, BOOLEAN, NUMBER')
    unit_details: ConfigurationItemUnitDetails | None = Field(None, alias='unitDetails', description='The unit_details field of BasicConfigurationItemMetadata.')
    value_input_details: ConfigurationItemAllowedValueDetails | None = Field(None, alias='valueInputDetails', description='The value_input_details field of BasicConfigurationItemMetadata.')


class BasicConfigurationItemSummary(OpsiBaseModel):
    """Basic configuration item summary. Value field contain the most preferred value for the specified scope (compartmentId), which could be from any of the ConfigurationItemValueSourceConfigurationType. Default value field contains the default value from Ops Insights."""

    config_item_type: Literal['BASIC', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='configItemType', description='Gets the config_item_type of this ConfigurationItemSummary.\nType of configuration item.\n\nAllowed values for this property are: "BASIC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    name: str | None = Field(None, alias='name', description='Name of configuration item.')
    value: Literal['COMPARTMENT', 'DEFAULT', 'TENANT'] | None = Field(None, alias='value', description='Value of configuration item.')
    value_source_config: Literal['DEFAULT', 'TENANT', 'COMPARTMENT', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='valueSourceConfig', description='Source configuration from where the value is taken for a configuration item.\n\nAllowed values for this property are: "DEFAULT", "TENANT", "COMPARTMENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    default_value: str | None = Field(None, alias='defaultValue', description='Value of configuration item.')
    applicable_contexts: list[str] | None = Field(None, alias='applicableContexts', description='List of contexts in Ops Insights where this configuration item is applicable.')
    metadata: ConfigurationItemMetadata | None = Field(None, alias='metadata', description='The metadata field of BasicConfigurationItemSummary.')


class ChangeAutonomousDatabaseInsightAdvancedFeaturesDetails(OpsiRequestModel):
    """Advanced feature details of autonomous database insight."""

    connection_details: ConnectionDetails = Field(..., alias='connectionDetails', description='The connection_details field of ChangeAutonomousDatabaseInsightAdvancedFeaturesDetails.')
    credential_details: CredentialDetails = Field(..., alias='credentialDetails', description='The credential_details field of ChangeAutonomousDatabaseInsightAdvancedFeaturesDetails.')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')


class ChangeAwrHubSourceCompartmentDetails(OpsiRequestModel):
    """Destination compartment for moving an AWR Hub source. Set compartmentId to the target compartment OCID."""

    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment into which the resource should be moved.')


class ChangeChargebackPlanCompartmentDetails(OpsiRequestModel):
    """Destination compartment for moving an Ops Insights chargeback plan. Set compartmentId to the target compartment OCID."""

    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment into which the resource should be moved.')


class ChangeDatabaseInsightCompartmentDetails(OpsiRequestModel):
    """Destination compartment for moving a database insight. Set compartmentId to the target compartment OCID."""

    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment into which the resource should be moved.')


class ChangeEnterpriseManagerBridgeCompartmentDetails(OpsiRequestModel):
    """Destination compartment for moving an Enterprise Manager bridge. Set compartmentId to the target compartment OCID."""

    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment into which the resource should be moved.')


class ChangeExadataInsightCompartmentDetails(OpsiRequestModel):
    """Destination compartment for moving an Exadata insight. Set compartmentId to the target compartment OCID."""

    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment into which the resource should be moved.')


class ChangeExternalMysqlDatabaseInsightConnectionDetails(OpsiBaseModel):
    """MySQL support within the OCI Ops Insights service has been deprecated as of January 29, 2026. Connection details of an External MySQL database insight."""

    database_connector_id: str = Field(..., alias='databaseConnectorId', description='The DBM owned database connector OCID mapping to the database credentials and connection details.')


class ChangeHostInsightCompartmentDetails(OpsiRequestModel):
    """Destination compartment for moving a host insight. Set compartmentId to the target compartment OCID."""

    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment into which the resource should be moved.')


class ChangeMacsManagedAutonomousDatabaseInsightConnectionDetails(OpsiRequestModel):
    """Connection details of a MACS-managed autonomous database insight."""

    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    connection_details: ConnectionDetails = Field(..., alias='connectionDetails', description='The connection_details field of ChangeMacsManagedAutonomousDatabaseInsightConnectionDetails.')
    connection_credential_details: CredentialDetails = Field(..., alias='connectionCredentialDetails', description='The connection_credential_details field of ChangeMacsManagedAutonomousDatabaseInsightConnectionDetails.')


class ChangeMacsManagedCloudDatabaseInsightConnectionDetails(OpsiRequestModel):
    """Connection details of a MACS-managed cloud database insight."""

    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    connection_details: ConnectionDetails = Field(..., alias='connectionDetails', description='The connection_details field of ChangeMacsManagedCloudDatabaseInsightConnectionDetails.')
    connection_credential_details: CredentialDetails = Field(..., alias='connectionCredentialDetails', description='The connection_credential_details field of ChangeMacsManagedCloudDatabaseInsightConnectionDetails.')


class ChangeNewsReportCompartmentDetails(OpsiRequestModel):
    """Destination compartment for moving a news report. Set compartmentId to the target compartment OCID."""

    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment into which the resource will be moved.')


class ChangeOperationsInsightsPrivateEndpointCompartmentDetails(OpsiRequestModel):
    """The details used to change the compartment of a Operation Insights private endpoint."""

    compartment_id: str | None = Field(None, alias='compartmentId', description='The new compartment OCID of the Private service accessed database.')


class ChangeOperationsInsightsWarehouseCompartmentDetails(OpsiRequestModel):
    """Destination compartment for moving an Operations Insights warehouse. Set compartmentId to the target compartment OCID."""

    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')


class ChangeOpsiConfigurationCompartmentDetails(OpsiRequestModel):
    """The information used to change the compartment of an OPSI configuration resource."""

    compartment_id: str = Field(..., alias='compartmentId', description='OCID of the compartment into which the resource should be moved.')


class ChangePeComanagedDatabaseInsightDetails(OpsiRequestModel):
    """Details of a Private Endpoint co-managed database insight."""

    service_name: str = Field(..., alias='serviceName', description='Database service name used for connection requests.')
    credential_details: CredentialDetails = Field(..., alias='credentialDetails', description='The credential_details field of ChangePeComanagedDatabaseInsightDetails.')
    connection_details: PeComanagedDatabaseConnectionDetails | None = Field(None, alias='connectionDetails', description='The connection_details field of ChangePeComanagedDatabaseInsightDetails.')
    opsi_private_endpoint_id: str = Field(..., alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')


class ChargebackPlan(OpsiBaseModel):
    """A chargeback plan that allows Ops Insights services to compute chargeback costs."""

    id: str = Field(..., alias='id', description='OCID of OPSI Chargeback plan resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    plan_name: str = Field(..., alias='planName', description='Name for the OPSI Chargeback plan.')
    plan_description: str | None = Field(None, alias='planDescription', description='Description of OPSI Chargeback Plan.')
    plan_type: str = Field(..., alias='planType', description='Chargeback Plan type of the chargeback entity. For an Exadata it can be WEIGHTED_ALLOCATION, EQUAL_ALLOCATION, UNUSED_ALLOCATION.')
    plan_category: Literal['OOB', 'CUSTOM', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='planCategory', description='Chargeback Plan category of the chargeback entity. It can be OOB, or CUSTOM.\n\nAllowed values for this property are: "OOB", "CUSTOM", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    is_customizable: bool | None = Field(None, alias='isCustomizable', description='Indicates whether the chargeback plan can be customized.')
    entity_source: Literal['CHARGEBACK_EXADATA', 'CHARGEBACK_COMPUTE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='entitySource', description='Source of the chargeback plan.\n\nAllowed values for this property are: "CHARGEBACK_EXADATA", "CHARGEBACK_COMPUTE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime = Field(..., alias='timeCreated', description='The date and time the chargeback plan was created, in the format defined by RFC3339.')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time chargeback plan was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Chargeback Plan lifecycle states\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    plan_custom_items: list[CreatePlanCustomItemDetails] | None = Field(None, alias='planCustomItems', description='List of chargeback plan customizations.')


class ChargebackPlanCollection(OpsiBaseModel):
    """A collection of Ops Insights chargeback plan objects."""

    items: list[ChargebackPlanSummary] = Field(..., alias='items', description='A list of ChargebackPlanSummary objects.')


class ChargebackPlanDetails(OpsiBaseModel):
    """Object containing chargeback plan details."""

    plan_id: str | None = Field(None, alias='planId', description='OCID of OPSI Chargeback plan resource.')
    plan_type: str | None = Field(None, alias='planType', description='Chargeback Plan type of the chargeback entity. For an Exadata it can be WEIGHTED_ALLOCATION, EQUAL_ALLOCATION, UNUSED_ALLOCATION.')
    time_enabled: datetime | None = Field(None, alias='timeEnabled', description='The date and time the chargeback plan was enabled on the resource, in the format defined by RFC3339.')


class ChargebackPlanReport(OpsiBaseModel):
    """A chargeback plan report that allows Ops Insights services to showcase chargeback costs."""

    report_id: str = Field(..., alias='reportId', description='OCID of the Chargeback plan report.')
    report_name: str = Field(..., alias='reportName', description='The chargeback plan report name.')
    resource_type: Literal['EXADATA_INSIGHT', 'DATABASE_INSIGHT', 'HOST_INSIGHT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceType', description='Defines the type of resource (example: EXADATA, HOST)\n\nAllowed values for this property are: "EXADATA_INSIGHT", "DATABASE_INSIGHT", "HOST_INSIGHT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    resource_id: str = Field(..., alias='resourceId', description='OCID of the Chargeback plan report.')
    time_created: datetime = Field(..., alias='timeCreated', description='The date and time the chargeback plan was created, in the format defined by RFC3339.')
    time_updated: datetime = Field(..., alias='timeUpdated', description='The time chargeback plan was updated. An RFC3339 formatted datetime string')
    report_properties: ReportPropertyDetails = Field(..., alias='reportProperties', description='The report_properties field of ChargebackPlanReport.')


class ChargebackPlanReportCollection(OpsiBaseModel):
    """A collection of chargeback plan reports objects."""

    items: list[ChargebackPlanReportSummary] = Field(..., alias='items', description='A list of ChargebackPlanReportSummary objects.')


class ChargebackPlanReportSummary(OpsiBaseModel):
    """Summary of a Ops Insights chargeback plan report."""

    report_id: str = Field(..., alias='reportId', description='OCID of the Chargeback plan report.')
    report_name: str = Field(..., alias='reportName', description='The chargeback plan report name.')
    resource_type: Literal['EXADATA_INSIGHT', 'DATABASE_INSIGHT', 'HOST_INSIGHT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceType', description='Defines the type of resource (example: EXADATA, HOST)\n\nAllowed values for this property are: "EXADATA_INSIGHT", "DATABASE_INSIGHT", "HOST_INSIGHT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    resource_id: str = Field(..., alias='resourceId', description='OCID of the Chargeback plan report.')
    time_created: datetime = Field(..., alias='timeCreated', description='The date and time the chargeback plan was created, in the format defined by RFC3339.')
    time_updated: datetime = Field(..., alias='timeUpdated', description='The time chargeback plan was updated. An RFC3339 formatted datetime string')
    report_properties: ReportPropertyDetails = Field(..., alias='reportProperties', description='The report_properties field of ChargebackPlanReportSummary.')


class ChargebackPlanSummary(OpsiBaseModel):
    """Summary of a Ops Insights chargeback plan."""

    id: str = Field(..., alias='id', description='OCID of OPSI Chargeback plan resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    plan_name: str = Field(..., alias='planName', description='Name for the OPSI Chargeback plan.')
    plan_description: str | None = Field(None, alias='planDescription', description='Description of OPSI Chargeback Plan.')
    plan_type: str = Field(..., alias='planType', description='Chargeback Plan type of the chargeback entity. For an Exadata it can be WEIGHTED_ALLOCATION, EQUAL_ALLOCATION, UNUSED_ALLOCATION.')
    plan_category: Literal['OOB', 'CUSTOM', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='planCategory', description='Chargeback Plan category of the chargeback entity. It can be OOB, or CUSTOM.\n\nAllowed values for this property are: "OOB", "CUSTOM", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    is_customizable: bool | None = Field(None, alias='isCustomizable', description='Indicates whether the chargeback plan can be customized.')
    entity_source: Literal['CHARGEBACK_EXADATA', 'CHARGEBACK_COMPUTE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Source of the chargeback plan.\n\nAllowed values for this property are: "CHARGEBACK_EXADATA", "CHARGEBACK_COMPUTE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime = Field(..., alias='timeCreated', description='The date and time the chargeback plan was created, in the format defined by RFC3339.')
    time_updated: datetime = Field(..., alias='timeUpdated', description='The time chargeback plan was updated. An RFC3339 formatted datetime string')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Chargeback Plan lifecycle states\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    plan_custom_items: list[CreatePlanCustomItemDetails] = Field(..., alias='planCustomItems', description='List of chargeback plan customizations.')


class CloudImportableComputeEntitySummary(OpsiBaseModel):
    """A compute host entity that can be imported into Operations Insights."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this ImportableComputeEntitySummary.\nSource of the importable agent entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compute_id: str = Field(..., alias='computeId', description='Gets the compute_id of this ImportableComputeEntitySummary. The OCID of the Compute Instance.')
    compute_display_name: str = Field(..., alias='computeDisplayName', description='Gets the compute_display_name of this ImportableComputeEntitySummary. The Display Name of the Compute Instance.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this ImportableComputeEntitySummary. The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='The host name. The host name is unique amongst the hosts managed by the same management agent.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class ConfigurationItemAllowedValueDetails(OpsiBaseModel):
    """Allowed value details of configuration item, to validate what value can be assigned to a configuration item."""

    allowed_value_type: Literal['LIMIT', 'PICK', 'FREE_TEXT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='allowedValueType', description='Allowed value type of configuration item.\n\nAllowed values for this property are: "LIMIT", "PICK", "FREE_TEXT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class ConfigurationItemFreeTextAllowedValueDetails(OpsiBaseModel):
    """Allowed value details of configuration item for FREE_TEXT type."""

    allowed_value_type: Literal['LIMIT', 'PICK', 'FREE_TEXT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='allowedValueType', description='Gets the allowed_value_type of this ConfigurationItemAllowedValueDetails.\nAllowed value type of configuration item.\n\nAllowed values for this property are: "LIMIT", "PICK", "FREE_TEXT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class ConfigurationItemLimitAllowedValueDetails(OpsiBaseModel):
    """Allowed value details of configuration item for LIMIT type. Value has to be between minValue and maxValue."""

    allowed_value_type: Literal['LIMIT', 'PICK', 'FREE_TEXT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='allowedValueType', description='Gets the allowed_value_type of this ConfigurationItemAllowedValueDetails.\nAllowed value type of configuration item.\n\nAllowed values for this property are: "LIMIT", "PICK", "FREE_TEXT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    min_value: str | None = Field(None, alias='minValue', description='Minimum value limit for the configuration item.')
    max_value: str | None = Field(None, alias='maxValue', description='Maximum value limit for the configuration item.')


class ConfigurationItemMetadata(OpsiBaseModel):
    """Configuration item metadata."""

    config_item_type: Literal['BASIC', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='configItemType', description='Type of configuration item.\n\nAllowed values for this property are: "BASIC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class ConfigurationItemPickAllowedValueDetails(OpsiBaseModel):
    """Allowed value details of configuration item for PICK type. Value has to be from one of the possibleValues."""

    allowed_value_type: Literal['LIMIT', 'PICK', 'FREE_TEXT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='allowedValueType', description='Gets the allowed_value_type of this ConfigurationItemAllowedValueDetails.\nAllowed value type of configuration item.\n\nAllowed values for this property are: "LIMIT", "PICK", "FREE_TEXT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    possible_values: list[str] | None = Field(None, alias='possibleValues', description='Allowed values to pick for the configuration item.')


class ConfigurationItemSummary(OpsiBaseModel):
    """Configuration item summary."""

    config_item_type: Literal['BASIC', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='configItemType', description='Type of configuration item.\n\nAllowed values for this property are: "BASIC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class ConfigurationItemUnitDetails(OpsiBaseModel):
    """Unit details of configuration item."""

    unit: str | None = Field(None, alias='unit', description='Unit of configuration item.')
    display_name: str | None = Field(None, alias='displayName', description='User-friendly display name for the configuration item unit.')


class ConfigurationItemsCollection(OpsiBaseModel):
    """Collection of configuration item summary objects."""

    opsi_config_type: Literal['UX_CONFIGURATION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='opsiConfigType', description='OPSI configuration type.\n\nAllowed values for this property are: "UX_CONFIGURATION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    config_items: list[ConfigurationItemSummary] | None = Field(None, alias='configItems', description='Array of configuration item summary objects.')


class ConnectionDetails(OpsiBaseModel):
    """Connection details to connect to the database. HostName, protocol, and port should be specified."""

    host_name: str = Field(..., alias='hostName', description='Name of the listener host that will be used to create the connect string to the database.')
    protocol: Literal['TCP', 'TCPS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='protocol', description='Protocol used for connection requests.\n\nAllowed values for this property are: "TCP", "TCPS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    port: int = Field(..., alias='port', description='Listener port number used for connection requests.')
    service_name: str = Field(..., alias='serviceName', description='Database service name used for connection requests.')


class CreateAutonomousDatabaseInsightDetails(OpsiBaseModel):
    """The information about database to be analyzed. When isAdvancedFeaturesEnabled is set to false, parameters connectionDetails, credentialDetails and opsiPrivateEndpoint are optional. Otherwise, connectionDetails and crendetialDetails are required to enable full OPSI service features. If the Autonomouse Database is configured with private, restricted or dedicated access, opsiPrivateEndpoint parameter is required."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateDatabaseInsightDetails.\nCompartment Identifier of database')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    database_resource_type: str = Field(..., alias='databaseResourceType', description='OCI database resource type')
    is_advanced_features_enabled: bool = Field(..., alias='isAdvancedFeaturesEnabled', description='Flag is to identify if advanced features for autonomous database is enabled or not')
    connection_details: ConnectionDetails | None = Field(None, alias='connectionDetails', description='The connection_details field of CreateAutonomousDatabaseInsightDetails.')
    credential_details: CredentialDetails | None = Field(None, alias='credentialDetails', description='The credential_details field of CreateAutonomousDatabaseInsightDetails.')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')


class CreateAwrHubDetails(OpsiRequestModel):
    """The information about Hub to be analyzed. Input compartmentId MUST be the root compartment."""

    operations_insights_warehouse_id: str = Field(..., alias='operationsInsightsWarehouseId', description='OPSI Warehouse OCID')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    display_name: str = Field(..., alias='displayName', description='User-friedly name of AWR Hub that does not have to be unique.')
    object_storage_bucket_name: str | None = Field(None, alias='objectStorageBucketName', description='Object Storage Bucket Name')


class CreateAwrHubSourceDetails(OpsiRequestModel):
    """payload to register Awr Hub source."""

    name: str = Field(..., alias='name', description='The name of the Awr Hub source database.')
    awr_hub_id: str = Field(..., alias='awrHubId', description='AWR Hub OCID')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    associated_resource_id: str | None = Field(None, alias='associatedResourceId', description='The OCID of the database id.')
    associated_opsi_id: str | None = Field(None, alias='associatedOpsiId', description='The OCID of the database id.')
    type: Literal['ADW_S', 'ATP_S', 'ADW_D', 'ATP_D', 'EXTERNAL_PDB', 'EXTERNAL_NONCDB', 'COMANAGED_VM_CDB', 'COMANAGED_VM_PDB', 'COMANAGED_VM_NONCDB', 'COMANAGED_BM_CDB', 'COMANAGED_BM_PDB', 'COMANAGED_BM_NONCDB', 'COMANAGED_EXACS_CDB', 'COMANAGED_EXACS_PDB', 'COMANAGED_EXACS_NONCDB', 'LH_S', 'APEX_S', 'AJD_S', 'AVD_S', 'LH_D', 'APEX_D', 'AJD_D', 'AVD_D', 'UNDEFINED'] = Field(..., alias='type', description='source type of the database\n\nAllowed values for this property are: "ADW_S", "ATP_S", "ADW_D", "ATP_D", "EXTERNAL_PDB", "EXTERNAL_NONCDB", "COMANAGED_VM_CDB", "COMANAGED_VM_PDB", "COMANAGED_VM_NONCDB", "COMANAGED_BM_CDB", "COMANAGED_BM_PDB", "COMANAGED_BM_NONCDB", "COMANAGED_EXACS_CDB", "COMANAGED_EXACS_PDB", "COMANAGED_EXACS_NONCDB", "LH_S", "APEX_S", "AJD_S", "AVD_S", "LH_D", "APEX_D", "AJD_D", "AVD_D", "UNDEFINED"')


class CreateBasicConfigurationItemDetails(OpsiBaseModel):
    """Basic configuration item details for OPSI configuration creation."""

    config_item_type: Literal['BASIC'] = Field(..., alias='configItemType', description='Gets the config_item_type of this CreateConfigurationItemDetails.\nType of configuration item.\n\nAllowed values for this property are: "BASIC"')
    name: str | None = Field(None, alias='name', description='Name of configuration item.')
    value: str | None = Field(None, alias='value', description='Value of configuration item.')


class CreateChargebackPlanDetails(OpsiRequestModel):
    """The details used to create a new Ops Insights chargeback plan."""

    entity_source: Literal['CHARGEBACK_EXADATA', 'CHARGEBACK_COMPUTE'] = Field(..., alias='entitySource', description='Source of the chargeback plan.\n\nAllowed values for this property are: "CHARGEBACK_EXADATA", "CHARGEBACK_COMPUTE"')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    plan_name: str = Field(..., alias='planName', description='Name for the OPSI Chargeback plan.')
    plan_description: str | None = Field(None, alias='planDescription', description='Description of OPSI Chargeback Plan.')
    plan_type: str = Field(..., alias='planType', description='Chargeback Plan type of the chargeback entity. For an Exadata it can be WEIGHTED_ALLOCATION, EQUAL_ALLOCATION, UNUSED_ALLOCATION.')
    plan_custom_items: list[CreatePlanCustomItemDetails] | None = Field(None, alias='planCustomItems', description='List of chargeback plan customizations.')


class CreateChargebackPlanExadataDetails(OpsiBaseModel):
    """The information about the exadata and chargeback plan."""

    entity_source: Literal['CHARGEBACK_EXADATA', 'CHARGEBACK_COMPUTE'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateChargebackPlanDetails.\nSource of the chargeback plan.\n\nAllowed values for this property are: "CHARGEBACK_EXADATA", "CHARGEBACK_COMPUTE"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateChargebackPlanDetails. The OCID of the compartment.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateChargebackPlanDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateChargebackPlanDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    plan_name: str = Field(..., alias='planName', description='Gets the plan_name of this CreateChargebackPlanDetails.\nName for the OPSI Chargeback plan.')
    plan_description: str | None = Field(None, alias='planDescription', description='Gets the plan_description of this CreateChargebackPlanDetails.\nDescription of OPSI Chargeback Plan.')
    plan_type: str = Field(..., alias='planType', description='Gets the plan_type of this CreateChargebackPlanDetails.\nChargeback Plan type of the chargeback entity. For an Exadata it can be WEIGHTED_ALLOCATION, EQUAL_ALLOCATION, UNUSED_ALLOCATION.')
    plan_custom_items: list[CreatePlanCustomItemDetails] | None = Field(None, alias='planCustomItems', description='Gets the plan_custom_items of this CreateChargebackPlanDetails.\nList of chargeback plan customizations.')


class CreateChargebackPlanReportDetails(OpsiRequestModel):
    """The details used to create a new Ops Insights chargeback plan report."""

    report_name: str = Field(..., alias='reportName', description='The chargeback plan report name.')
    report_properties: ReportPropertyDetails = Field(..., alias='reportProperties', description='The report_properties field of CreateChargebackPlanReportDetails.')


class CreateConfigurationItemDetails(OpsiBaseModel):
    """Configuration item details for OPSI configuration creation."""

    config_item_type: Literal['BASIC'] = Field(..., alias='configItemType', description='Type of configuration item.\n\nAllowed values for this property are: "BASIC"')


class CreateDatabaseInsightDetails(OpsiRequestModel):
    """The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Source of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    compartment_id: str = Field(..., alias='compartmentId', description='Compartment Identifier of database')


class CreateEmManagedExternalDatabaseInsightDetails(OpsiBaseModel):
    """The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateDatabaseInsightDetails.\nCompartment Identifier of database')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_bridge_id: str = Field(..., alias='enterpriseManagerBridgeId', description='OPSI Enterprise Manager Bridge OCID')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    exadata_insight_id: str | None = Field(None, alias='exadataInsightId', description='The OCID of the Exadata insight.')


class CreateEmManagedExternalExadataInsightDetails(OpsiBaseModel):
    """The information about the Exadata system to be analyzed. If memberEntityDetails is not specified, the the Enterprise Manager entity (e.g. databases and hosts) associated with an Exadata system will be placed in the same compartment as the Exadata system."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateExadataInsightDetails.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateExadataInsightDetails.\nCompartment Identifier of Exadata insight')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateExadataInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateExadataInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_bridge_id: str = Field(..., alias='enterpriseManagerBridgeId', description='OPSI Enterprise Manager Bridge OCID')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    member_entity_details: list[CreateEmManagedExternalExadataMemberEntityDetails] | None = Field(None, alias='memberEntityDetails', description='The member_entity_details field of CreateEmManagedExternalExadataInsightDetails.')
    is_auto_sync_enabled: bool | None = Field(None, alias='isAutoSyncEnabled', description='Set to true to enable automatic enablement and disablement of related targets from Enterprise Manager. New resources (e.g. Database Insights) will be placed in the same compartment as the related Exadata Insight.')


class CreateEmManagedExternalExadataMemberEntityDetails(OpsiBaseModel):
    """Compartment OCID of the Enterprise Manager member entity (e.g. databases and hosts) associated with an Exadata system."""

    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')


class CreateEmManagedExternalHostInsightDetails(OpsiBaseModel):
    """The information about the EM-managed external host to be analyzed."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateHostInsightDetails.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateHostInsightDetails.\nCompartment Identifier of host')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateHostInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateHostInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_bridge_id: str = Field(..., alias='enterpriseManagerBridgeId', description='OPSI Enterprise Manager Bridge OCID')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    exadata_insight_id: str | None = Field(None, alias='exadataInsightId', description='The OCID of the Exadata insight.')


class CreateEnterpriseManagerBridgeDetails(OpsiRequestModel):
    """The information about a Enterprise Manager bridge resource to be created."""

    compartment_id: str = Field(..., alias='compartmentId', description='Compartment identifier of the Enterprise Manager bridge')
    display_name: str = Field(..., alias='displayName', description='User-friedly name of Enterprise Manager Bridge that does not have to be unique.')
    description: str | None = Field(None, alias='description', description='Description of Enterprise Manager Bridge')
    object_storage_bucket_name: str = Field(..., alias='objectStorageBucketName', description='Object Storage Bucket Name')


class CreateExadataInsightDetails(OpsiRequestModel):
    """The information about the Exadata system to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Source of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')
    compartment_id: str = Field(..., alias='compartmentId', description='Compartment Identifier of Exadata insight')


class CreateExternalMysqlDatabaseInsightDetails(OpsiBaseModel):
    """MySQL support within the OCI Ops Insights service has been deprecated as of January 29, 2026. The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateDatabaseInsightDetails.\nCompartment Identifier of database')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    database_connector_id: str = Field(..., alias='databaseConnectorId', description='The DBM owned database connector OCID mapping to the database credentials and connection details.')


class CreateHostInsightDetails(OpsiRequestModel):
    """The information about the host to be analyzed."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Source of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')
    compartment_id: str = Field(..., alias='compartmentId', description='Compartment Identifier of host')


class CreateMacsManagedAutonomousDatabaseInsightDetails(OpsiBaseModel):
    """The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateDatabaseInsightDetails.\nCompartment Identifier of database')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    connection_details: ConnectionDetails = Field(..., alias='connectionDetails', description='The connection_details field of CreateMacsManagedAutonomousDatabaseInsightDetails.')
    connection_credential_details: CredentialDetails = Field(..., alias='connectionCredentialDetails', description='The connection_credential_details field of CreateMacsManagedAutonomousDatabaseInsightDetails.')
    database_resource_type: str = Field(..., alias='databaseResourceType', description='OCI database resource type')
    deployment_type: Literal['EXACC'] = Field(..., alias='deploymentType', description='Database Deployment Type\n\nAllowed values for this property are: "EXACC"')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')


class CreateMacsManagedCloudDatabaseInsightDetails(OpsiBaseModel):
    """The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateDatabaseInsightDetails.\nCompartment Identifier of database')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    connection_details: ConnectionDetails = Field(..., alias='connectionDetails', description='The connection_details field of CreateMacsManagedCloudDatabaseInsightDetails.')
    connection_credential_details: CredentialDetails = Field(..., alias='connectionCredentialDetails', description='The connection_credential_details field of CreateMacsManagedCloudDatabaseInsightDetails.')
    database_resource_type: str = Field(..., alias='databaseResourceType', description='OCI database resource type')
    deployment_type: Literal['VIRTUAL_MACHINE', 'BARE_METAL', 'EXACC', 'EXACS'] = Field(..., alias='deploymentType', description='Database Deployment Type (EXACS will be supported in the future)\n\nAllowed values for this property are: "VIRTUAL_MACHINE", "BARE_METAL", "EXACC", "EXACS"')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')


class CreateMacsManagedCloudExadataClusterDetails(OpsiBaseModel):
    """The information of the VM Cluster which contains databases."""

    vm_cluster_type: Literal['vmCluster', 'autonomousVmCluster'] | None = Field(None, alias='vmClusterType', description='Exadata VMCluster type\n\nAllowed values for this property are: "vmCluster", "autonomousVmCluster"')
    vmcluster_id: str = Field(..., alias='vmclusterId', description='The OCID of the VM Cluster.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')


class CreateMacsManagedCloudExadataInsightDetails(OpsiBaseModel):
    """The information about the Exadata system to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateExadataInsightDetails.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateExadataInsightDetails.\nCompartment Identifier of Exadata insight')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateExadataInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateExadataInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    exadata_infra_id: str = Field(..., alias='exadataInfraId', description='The OCID of the Exadata Infrastructure.')
    member_vm_cluster_details: list[CreateMacsManagedCloudExadataVmclusterDetails] | None = Field(None, alias='memberVmClusterDetails', description='The member_vm_cluster_details field of CreateMacsManagedCloudExadataInsightDetails.')


class CreateMacsManagedCloudExadataVmclusterDetails(OpsiBaseModel):
    """The information of the VM Cluster which contains databases."""

    vm_cluster_type: Literal['vmCluster', 'autonomousVmCluster'] | None = Field(None, alias='vmClusterType', description='Gets the vm_cluster_type of this CreateMacsManagedCloudExadataClusterDetails.\nExadata VMCluster type\n\nAllowed values for this property are: "vmCluster", "autonomousVmCluster"')
    vmcluster_id: str = Field(..., alias='vmclusterId', description='Gets the vmcluster_id of this CreateMacsManagedCloudExadataClusterDetails. The OCID of the VM Cluster.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateMacsManagedCloudExadataClusterDetails. The OCID of the compartment.')
    member_database_details: list[CreateMacsManagedCloudDatabaseInsightDetails] | None = Field(None, alias='memberDatabaseDetails', description='The databases that belong to the VM Cluster')
    member_autonomous_details: list[CreateMacsManagedAutonomousDatabaseInsightDetails] | None = Field(None, alias='memberAutonomousDetails', description='The autonomous databases that belong to the Autonmous VM Cluster')


class CreateMacsManagedCloudHostInsightDetails(OpsiBaseModel):
    """The information about the Compute Instance host to be analyzed."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateHostInsightDetails.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateHostInsightDetails.\nCompartment Identifier of host')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateHostInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateHostInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    compute_id: str = Field(..., alias='computeId', description='The OCID of the Compute Instance.')


class CreateMacsManagedExternalHostInsightDetails(OpsiBaseModel):
    """The information about the MACS-managed external host to be analyzed."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateHostInsightDetails.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateHostInsightDetails.\nCompartment Identifier of host')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateHostInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateHostInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')


class CreateMdsMySqlDatabaseInsightDetails(OpsiBaseModel):
    """MySQL support within the OCI Ops Insights service has been deprecated as of January 29, 2026. The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateDatabaseInsightDetails.\nCompartment Identifier of database')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')


class CreateNewsReportDetails(OpsiRequestModel):
    """The information about the news report to be created."""

    name: str = Field(..., alias='name', description='The news report name.')
    news_frequency: Literal['WEEKLY', 'DAILY', 'HOURLY'] = Field(..., alias='newsFrequency', description='News report frequency.\n\nAllowed values for this property are: "WEEKLY", "DAILY", "HOURLY"')
    description: str = Field(..., alias='description', description='The description of the news report.')
    ons_topic_id: str = Field(..., alias='onsTopicId', description='The OCID of the ONS topic.')
    compartment_id: str = Field(..., alias='compartmentId', description='Compartment Identifier where the news report will be created.')
    content_types: NewsContentTypes = Field(..., alias='contentTypes', description='The content_types field of CreateNewsReportDetails.')
    locale: Literal['EN'] = Field(..., alias='locale', description='Language of the news report.\n\nAllowed values for this property are: "EN"')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED'] | None = Field(None, alias='status', description='Defines if the news report will be enabled or disabled.\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED"')
    day_of_week: Literal['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'] | None = Field(None, alias='dayOfWeek', description='Day of the week in which the news report will be sent if the frequency is set to WEEKLY.\n\nAllowed values for this property are: "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"')
    are_child_compartments_included: bool | None = Field(None, alias='areChildCompartmentsIncluded', description='A flag to consider the resources within a given compartment and all sub-compartments.')


class CreateOperationsInsightsPrivateEndpointDetails(OpsiRequestModel):
    """The details used to create a new Operation Insights private endpoint."""

    display_name: str = Field(..., alias='displayName', description='The display name for the private endpoint. It is changeable.')
    compartment_id: str = Field(..., alias='compartmentId', description='The compartment OCID of the Private service accessed database.')
    vcn_id: str = Field(..., alias='vcnId', description='The VCN OCID of the Private service accessed database.')
    subnet_id: str = Field(..., alias='subnetId', description='The Subnet OCID of the Private service accessed database.')
    is_used_for_rac_dbs: bool = Field(..., alias='isUsedForRacDbs', description='This flag was previously used to create a private endpoint with scan proxy. Setting this to true will now create a private endpoint with a\nDNS proxy causing `isProxyEnabled` flag to be true; this is used exclusively for full feature support for dedicated Autonomous Databases.')
    description: str | None = Field(None, alias='description', description='The description of the private endpoint.')
    nsg_ids: list[str] | None = Field(None, alias='nsgIds', description='The OCID of the network security groups that the private endpoint belongs to.')


class CreateOperationsInsightsWarehouseDetails(OpsiRequestModel):
    """The information about a Operations Insights Warehouse resource to be created. Input compartmentId MUST be the root compartment."""

    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    display_name: str = Field(..., alias='displayName', description='User-friedly name of Ops Insights Warehouse that does not have to be unique.')
    cpu_allocated: float = Field(..., alias='cpuAllocated', description='Number of CPUs allocated to OPSI Warehouse ADW.')
    compute_model: str | None = Field(None, alias='computeModel', description='The compute model for the OPSI warehouse ADW (OCPU or ECPU)')
    storage_allocated_in_gbs: float | None = Field(None, alias='storageAllocatedInGBs', description='Storage allocated to OPSI Warehouse ADW.')


class CreateOperationsInsightsWarehouseUserDetails(OpsiRequestModel):
    """The information about a Operations Insights Warehouse User to be created. Input compartmentId MUST be the root compartment."""

    operations_insights_warehouse_id: str = Field(..., alias='operationsInsightsWarehouseId', description='OPSI Warehouse OCID')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    name: str = Field(..., alias='name', description='Username for schema which would have access to AWR Data,  Enterprise Manager Data and Ops Insights OPSI Hub.')
    connection_password: str = Field(..., alias='connectionPassword', description='User provided connection password for the AWR Data,  Enterprise Manager Data and Ops Insights OPSI Hub.')
    is_awr_data_access: bool = Field(..., alias='isAwrDataAccess', description='Indicate whether user has access to AWR data.')
    is_em_data_access: bool | None = Field(None, alias='isEmDataAccess', description='Indicate whether user has access to EM data.')
    is_opsi_data_access: bool | None = Field(None, alias='isOpsiDataAccess', description='Indicate whether user has access to OPSI data.')


class CreateOpsiConfigurationDetails(OpsiRequestModel):
    """Information about OPSI configuration to be created."""

    compartment_id: str | None = Field(None, alias='compartmentId', description='The OCID of the compartment.')
    opsi_config_type: Literal['UX_CONFIGURATION'] = Field(..., alias='opsiConfigType', description='OPSI configuration type.\n\nAllowed values for this property are: "UX_CONFIGURATION"')
    display_name: str | None = Field(None, alias='displayName', description='User-friendly display name for the OPSI configuration. The name does not have to be unique.')
    description: str | None = Field(None, alias='description', description='Description of OPSI configuration.')
    config_items: list[CreateConfigurationItemDetails] | None = Field(None, alias='configItems', description='Array of configuration items with custom values. All and only configuration items requiring custom values should be part of this array.')


class CreateOpsiUxConfigurationDetails(OpsiBaseModel):
    """Information about OPSI UX configuration to be created."""

    compartment_id: str | None = Field(None, alias='compartmentId', description='Gets the compartment_id of this CreateOpsiConfigurationDetails. The OCID of the compartment.')
    opsi_config_type: Literal['UX_CONFIGURATION'] = Field(..., alias='opsiConfigType', description='Gets the opsi_config_type of this CreateOpsiConfigurationDetails.\nOPSI configuration type.\n\nAllowed values for this property are: "UX_CONFIGURATION"')
    display_name: str | None = Field(None, alias='displayName', description='Gets the display_name of this CreateOpsiConfigurationDetails.\nUser-friendly display name for the OPSI configuration. The name does not have to be unique.')
    description: str | None = Field(None, alias='description', description='Gets the description of this CreateOpsiConfigurationDetails.\nDescription of OPSI configuration.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateOpsiConfigurationDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateOpsiConfigurationDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this CreateOpsiConfigurationDetails.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    config_items: list[CreateConfigurationItemDetails] | None = Field(None, alias='configItems', description='Gets the config_items of this CreateOpsiConfigurationDetails.\nArray of configuration items with custom values. All and only configuration items requiring custom values should be part of this array.')


class CreatePeComanagedDatabaseInsightDetails(OpsiBaseModel):
    """The information about database to be analyzed. Either an opsiPrivateEndpointId or dbmPrivateEndpointId must be specified. If the dbmPrivateEndpointId is specified, a new Operations Insights private endpoint will be created."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateDatabaseInsightDetails.\nCompartment Identifier of database')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    database_resource_type: str = Field(..., alias='databaseResourceType', description='OCI database resource type')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    dbm_private_endpoint_id: str | None = Field(None, alias='dbmPrivateEndpointId', description='The OCID of the Database Management private endpoint.')
    service_name: str = Field(..., alias='serviceName', description='Database service name used for connection requests.')
    credential_details: CredentialDetails = Field(..., alias='credentialDetails', description='The credential_details field of CreatePeComanagedDatabaseInsightDetails.')
    connection_details: PeComanagedDatabaseConnectionDetails | None = Field(None, alias='connectionDetails', description='The connection_details field of CreatePeComanagedDatabaseInsightDetails.')
    deployment_type: Literal['VIRTUAL_MACHINE', 'BARE_METAL', 'EXACS'] = Field(..., alias='deploymentType', description='Database Deployment Type\n\nAllowed values for this property are: "VIRTUAL_MACHINE", "BARE_METAL", "EXACS"')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')


class CreatePeComanagedExadataInsightDetails(OpsiBaseModel):
    """The information about the Exadata system to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Gets the entity_source of this CreateExadataInsightDetails.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this CreateExadataInsightDetails.\nCompartment Identifier of Exadata insight')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this CreateExadataInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this CreateExadataInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    exadata_infra_id: str = Field(..., alias='exadataInfraId', description='The OCID of the Exadata Infrastructure.')
    member_vm_cluster_details: list[CreatePeComanagedExadataVmclusterDetails] | None = Field(None, alias='memberVmClusterDetails', description='The member_vm_cluster_details field of CreatePeComanagedExadataInsightDetails.')


class CreatePeComanagedExadataVmclusterDetails(OpsiBaseModel):
    """The information of the VM Cluster which contains databases. Either an opsiPrivateEndpointId or dbmPrivateEndpointId must be specified. If the dbmPrivateEndpointId is specified, a new Operations Insights private endpoint will be created."""

    vmcluster_id: str = Field(..., alias='vmclusterId', description='The OCID of the VM Cluster.')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    dbm_private_endpoint_id: str | None = Field(None, alias='dbmPrivateEndpointId', description='The OCID of the Database Management private endpoint.')
    member_database_details: list[CreatePeComanagedDatabaseInsightDetails] | None = Field(None, alias='memberDatabaseDetails', description='The databases that belong to the VM Cluster')
    vm_cluster_type: Literal['vmCluster', 'autonomousVmCluster'] | None = Field(None, alias='vmClusterType', description='Exadata VMCluster type\n\nAllowed values for this property are: "vmCluster", "autonomousVmCluster"')
    member_autonomous_details: list[CreateAutonomousDatabaseInsightDetails] | None = Field(None, alias='memberAutonomousDetails', description='The autonomous databases that belong to the Autonomous VM Cluster')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')


class CreatePlanCustomItemDetails(OpsiBaseModel):
    """Custom configuration item details for a chargeback plan. Example items for Exadata Insights Chargeback are statistic(default value AVG), percentile, infrastructureCost, infrastructurePlanType, additionalServerCost and additionalServerPlanType."""

    name: str | None = Field(None, alias='name', description='Name of chargeback plan customization item. Example items for Exadata Insights Chargeback are statistic, percentile, infrastructureCost, additionalServerCost etc.')
    value: str | None = Field(None, alias='value', description='Value of chargeback plan customization item.')
    is_customizable: bool | None = Field(None, alias='isCustomizable', description='Indicates whether the chargeback plan customization item can be customized.')


class CredentialByIam(OpsiBaseModel):
    """IAM Credential Details to connect to the database."""

    credential_source_name: str | None = Field(None, alias='credentialSourceName', description='Gets the credential_source_name of this CredentialDetails.\nCredential source name that had been added in Management Agent wallet. This value is only required when Credential set by CREDENTIALS_BY_SOURCE and is optional properties for ther others.')
    credential_type: Literal['CREDENTIALS_BY_SOURCE', 'CREDENTIALS_BY_VAULT', 'CREDENTIALS_BY_IAM', 'CREDENTIALS_BY_NAMED_CREDS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='credentialType', description='Gets the credential_type of this CredentialDetails.\nCREDENTIALS_BY_SOURCE is supplied via the External Database Service. CREDENTIALS_BY_VAULT is supplied by secret service to connection PE_COMANAGED_DATABASE and ADB as well. CREDENTIALS_BY_IAM is used db-token to connect only for Autonomous Database.\n\nAllowed values for this property are: "CREDENTIALS_BY_SOURCE", "CREDENTIALS_BY_VAULT", "CREDENTIALS_BY_IAM", "CREDENTIALS_BY_NAMED_CREDS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class CredentialByNamedCredentials(OpsiBaseModel):
    """Credentials by named credentials stored in management agent to connect database."""

    credential_source_name: str | None = Field(None, alias='credentialSourceName', description='Gets the credential_source_name of this CredentialDetails.\nCredential source name that had been added in Management Agent wallet. This value is only required when Credential set by CREDENTIALS_BY_SOURCE and is optional properties for ther others.')
    credential_type: Literal['CREDENTIALS_BY_SOURCE', 'CREDENTIALS_BY_VAULT', 'CREDENTIALS_BY_IAM', 'CREDENTIALS_BY_NAMED_CREDS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='credentialType', description='Gets the credential_type of this CredentialDetails.\nCREDENTIALS_BY_SOURCE is supplied via the External Database Service. CREDENTIALS_BY_VAULT is supplied by secret service to connection PE_COMANAGED_DATABASE and ADB as well. CREDENTIALS_BY_IAM is used db-token to connect only for Autonomous Database.\n\nAllowed values for this property are: "CREDENTIALS_BY_SOURCE", "CREDENTIALS_BY_VAULT", "CREDENTIALS_BY_IAM", "CREDENTIALS_BY_NAMED_CREDS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    named_credential_id: str | None = Field(None, alias='namedCredentialId', description='The credential OCID stored in management agent.')


class CredentialByVault(OpsiBaseModel):
    """Vault Credential Details to connect to the database."""

    credential_source_name: str | None = Field(None, alias='credentialSourceName', description='Gets the credential_source_name of this CredentialDetails.\nCredential source name that had been added in Management Agent wallet. This value is only required when Credential set by CREDENTIALS_BY_SOURCE and is optional properties for ther others.')
    credential_type: Literal['CREDENTIALS_BY_SOURCE', 'CREDENTIALS_BY_VAULT', 'CREDENTIALS_BY_IAM', 'CREDENTIALS_BY_NAMED_CREDS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='credentialType', description='Gets the credential_type of this CredentialDetails.\nCREDENTIALS_BY_SOURCE is supplied via the External Database Service. CREDENTIALS_BY_VAULT is supplied by secret service to connection PE_COMANAGED_DATABASE and ADB as well. CREDENTIALS_BY_IAM is used db-token to connect only for Autonomous Database.\n\nAllowed values for this property are: "CREDENTIALS_BY_SOURCE", "CREDENTIALS_BY_VAULT", "CREDENTIALS_BY_IAM", "CREDENTIALS_BY_NAMED_CREDS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    user_name: str | None = Field(None, alias='userName', description='database user name.')
    password_secret_id: str | None = Field(None, alias='passwordSecretId', description='The secret OCID mapping to the database credentials.')
    wallet_secret_id: str | None = Field(None, alias='walletSecretId', description='The OCID of the Secret where the database keystore contents are stored. This is used for TCPS support in BM/VM/ExaCS cases.')
    role: Literal['NORMAL', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='role', description='database user role.\n\nAllowed values for this property are: "NORMAL", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class CredentialDetails(OpsiBaseModel):
    """User credential details to connect to the database."""

    credential_source_name: str | None = Field(None, alias='credentialSourceName', description='Credential source name that had been added in Management Agent wallet. This value is only required when Credential set by CREDENTIALS_BY_SOURCE and is optional properties for ther others.')
    credential_type: Literal['CREDENTIALS_BY_SOURCE', 'CREDENTIALS_BY_VAULT', 'CREDENTIALS_BY_IAM', 'CREDENTIALS_BY_NAMED_CREDS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='credentialType', description='CREDENTIALS_BY_SOURCE is supplied via the External Database Service. CREDENTIALS_BY_VAULT is supplied by secret service to connection PE_COMANAGED_DATABASE and ADB as well. CREDENTIALS_BY_IAM is used db-token to connect only for Autonomous Database.\n\nAllowed values for this property are: "CREDENTIALS_BY_SOURCE", "CREDENTIALS_BY_VAULT", "CREDENTIALS_BY_IAM", "CREDENTIALS_BY_NAMED_CREDS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class CredentialsBySource(OpsiBaseModel):
    """Credential Source to connect to the database."""

    credential_source_name: str | None = Field(None, alias='credentialSourceName', description='Gets the credential_source_name of this CredentialDetails.\nCredential source name that had been added in Management Agent wallet. This value is only required when Credential set by CREDENTIALS_BY_SOURCE and is optional properties for ther others.')
    credential_type: Literal['CREDENTIALS_BY_SOURCE', 'CREDENTIALS_BY_VAULT', 'CREDENTIALS_BY_IAM', 'CREDENTIALS_BY_NAMED_CREDS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='credentialType', description='Gets the credential_type of this CredentialDetails.\nCREDENTIALS_BY_SOURCE is supplied via the External Database Service. CREDENTIALS_BY_VAULT is supplied by secret service to connection PE_COMANAGED_DATABASE and ADB as well. CREDENTIALS_BY_IAM is used db-token to connect only for Autonomous Database.\n\nAllowed values for this property are: "CREDENTIALS_BY_SOURCE", "CREDENTIALS_BY_VAULT", "CREDENTIALS_BY_IAM", "CREDENTIALS_BY_NAMED_CREDS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class DBConnectionStatus(OpsiBaseModel):
    """Database connection status."""

    metric_name: Literal['DB_EXTERNAL_PROPERTIES', 'DB_EXTERNAL_INSTANCE', 'DB_OS_CONFIG_INSTANCE', 'DB_PARAMETERS', 'DB_CONNECTION_STATUS', 'HOST_RESOURCE_ALLOCATION', 'ASM_ENTITY', 'EXADATA_CELL_CONFIG'] = Field(..., alias='metricName', description='Gets the metric_name of this DatabaseConfigurationMetricGroup.\nName of the metric group.\n\nAllowed values for this property are: "DB_EXTERNAL_PROPERTIES", "DB_EXTERNAL_INSTANCE", "DB_OS_CONFIG_INSTANCE", "DB_PARAMETERS", "DB_CONNECTION_STATUS", "HOST_RESOURCE_ALLOCATION", "ASM_ENTITY", "EXADATA_CELL_CONFIG"')
    time_collected: datetime | None = Field(None, alias='timeCollected', description='Gets the time_collected of this DatabaseConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')


class DBExternalInstance(OpsiBaseModel):
    """Configuration parameters defined for external databases instance level."""

    metric_name: Literal['DB_EXTERNAL_PROPERTIES', 'DB_EXTERNAL_INSTANCE', 'DB_OS_CONFIG_INSTANCE', 'DB_PARAMETERS', 'DB_CONNECTION_STATUS', 'HOST_RESOURCE_ALLOCATION', 'ASM_ENTITY', 'EXADATA_CELL_CONFIG'] = Field(..., alias='metricName', description='Gets the metric_name of this DatabaseConfigurationMetricGroup.\nName of the metric group.\n\nAllowed values for this property are: "DB_EXTERNAL_PROPERTIES", "DB_EXTERNAL_INSTANCE", "DB_OS_CONFIG_INSTANCE", "DB_PARAMETERS", "DB_CONNECTION_STATUS", "HOST_RESOURCE_ALLOCATION", "ASM_ENTITY", "EXADATA_CELL_CONFIG"')
    time_collected: datetime | None = Field(None, alias='timeCollected', description='Gets the time_collected of this DatabaseConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    instance_name: str = Field(..., alias='instanceName', description='Name of the database instance.')
    host_name: str = Field(..., alias='hostName', description='Host name of the database instance.')
    cpu_count: int | None = Field(None, alias='cpuCount', description='Total number of CPUs allocated for the host.', ge=0)
    host_memory_capacity: float | None = Field(None, alias='hostMemoryCapacity', description='Total amount of usable Physical RAM Memory available in gigabytes.')
    version: str | None = Field(None, alias='version', description='Database version.')
    parallel: str | None = Field(None, alias='parallel', description='Indicates whether the instance is mounted in cluster database mode (YES) or not (NO).')
    instance_role: str | None = Field(None, alias='instanceRole', description='Role (permissions) of the database instance.')
    logins: str | None = Field(None, alias='logins', description='Indicates if logins are allowed or restricted.')
    database_status: str | None = Field(None, alias='databaseStatus', description='Status of the database.')
    status: str | None = Field(None, alias='status', description='Status of the instance.')
    edition: str | None = Field(None, alias='edition', description='The edition of the database.')
    startup_time: datetime | None = Field(None, alias='startupTime', description='Start up time of the database instance.')


class DBExternalProperties(OpsiBaseModel):
    """Configuration parameters defined for external databases."""

    metric_name: Literal['DB_EXTERNAL_PROPERTIES', 'DB_EXTERNAL_INSTANCE', 'DB_OS_CONFIG_INSTANCE', 'DB_PARAMETERS', 'DB_CONNECTION_STATUS', 'HOST_RESOURCE_ALLOCATION', 'ASM_ENTITY', 'EXADATA_CELL_CONFIG'] = Field(..., alias='metricName', description='Gets the metric_name of this DatabaseConfigurationMetricGroup.\nName of the metric group.\n\nAllowed values for this property are: "DB_EXTERNAL_PROPERTIES", "DB_EXTERNAL_INSTANCE", "DB_OS_CONFIG_INSTANCE", "DB_PARAMETERS", "DB_CONNECTION_STATUS", "HOST_RESOURCE_ALLOCATION", "ASM_ENTITY", "EXADATA_CELL_CONFIG"')
    time_collected: datetime | None = Field(None, alias='timeCollected', description='Gets the time_collected of this DatabaseConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    name: str | None = Field(None, alias='name', description='Name of the database.')
    log_mode: str | None = Field(None, alias='logMode', description='Archive log mode.')
    cdb: str | None = Field(None, alias='cdb', description="Indicates if it is a CDB or not. This would be 'yes' or 'no'.")
    open_mode: str | None = Field(None, alias='openMode', description='Open mode information.')
    database_role: str | None = Field(None, alias='databaseRole', description='Current role of the database.')
    guard_status: str | None = Field(None, alias='guardStatus', description='Data protection policy.')
    platform_name: str | None = Field(None, alias='platformName', description='Platform name of the database, OS with architecture.')
    control_file_type: str | None = Field(None, alias='controlFileType', description='Type of control file.')
    switchover_status: str | None = Field(None, alias='switchoverStatus', description='Indicates whether switchover is allowed.')
    created: datetime | None = Field(None, alias='created', description='Creation time.')


class DBOSConfigInstance(OpsiBaseModel):
    """Configuration parameters defined for external databases instance level."""

    metric_name: Literal['DB_EXTERNAL_PROPERTIES', 'DB_EXTERNAL_INSTANCE', 'DB_OS_CONFIG_INSTANCE', 'DB_PARAMETERS', 'DB_CONNECTION_STATUS', 'HOST_RESOURCE_ALLOCATION', 'ASM_ENTITY', 'EXADATA_CELL_CONFIG'] = Field(..., alias='metricName', description='Gets the metric_name of this DatabaseConfigurationMetricGroup.\nName of the metric group.\n\nAllowed values for this property are: "DB_EXTERNAL_PROPERTIES", "DB_EXTERNAL_INSTANCE", "DB_OS_CONFIG_INSTANCE", "DB_PARAMETERS", "DB_CONNECTION_STATUS", "HOST_RESOURCE_ALLOCATION", "ASM_ENTITY", "EXADATA_CELL_CONFIG"')
    time_collected: datetime | None = Field(None, alias='timeCollected', description='Gets the time_collected of this DatabaseConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    instance_name: str = Field(..., alias='instanceName', description='Name of the database instance.')
    host_name: str = Field(..., alias='hostName', description='Host name of the database instance.')
    num_cp_us: int | None = Field(None, alias='numCPUs', description='Total number of CPUs available.')
    num_cpu_cores: int | None = Field(None, alias='numCPUCores', description='Number of CPU cores available (includes subcores of multicore CPUs as well as single-core CPUs).')
    num_cpu_sockets: int | None = Field(None, alias='numCPUSockets', description='Number of CPU Sockets available.')
    physical_memory_bytes: float | None = Field(None, alias='physicalMemoryBytes', description='Total number of bytes of physical memory.')


class DBParameters(OpsiBaseModel):
    """Initialization parameters for a database."""

    metric_name: Literal['DB_EXTERNAL_PROPERTIES', 'DB_EXTERNAL_INSTANCE', 'DB_OS_CONFIG_INSTANCE', 'DB_PARAMETERS', 'DB_CONNECTION_STATUS', 'HOST_RESOURCE_ALLOCATION', 'ASM_ENTITY', 'EXADATA_CELL_CONFIG'] = Field(..., alias='metricName', description='Gets the metric_name of this DatabaseConfigurationMetricGroup.\nName of the metric group.\n\nAllowed values for this property are: "DB_EXTERNAL_PROPERTIES", "DB_EXTERNAL_INSTANCE", "DB_OS_CONFIG_INSTANCE", "DB_PARAMETERS", "DB_CONNECTION_STATUS", "HOST_RESOURCE_ALLOCATION", "ASM_ENTITY", "EXADATA_CELL_CONFIG"')
    time_collected: datetime | None = Field(None, alias='timeCollected', description='Gets the time_collected of this DatabaseConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    instance_number: int = Field(..., alias='instanceNumber', description='Database instance number.')
    parameter_name: str = Field(..., alias='parameterName', description='Database parameter name.')
    parameter_value: str = Field(..., alias='parameterValue', description='Database parameter value.')
    snapshot_id: int | None = Field(None, alias='snapshotId', description='AWR snapshot id for the parameter value')
    is_changed: str | None = Field(None, alias='isChanged', description="Indicates whether the parameter's value changed in given snapshot or not.")
    is_default: str | None = Field(None, alias='isDefault', description='Indicates whether this value is the default value or not.')


class DataObjectBindParameter(OpsiBaseModel):
    """Details for a bind parameter used in data object query."""

    name: str = Field(..., alias='name', description='Name of the bind parameter.')
    value: Any = Field(..., alias='value', description='Value for the bind parameter.')
    data_type: str = Field(..., alias='dataType', description='Data type of the bind parameter.')


class DataObjectColumnMetadata(OpsiBaseModel):
    """Metadata of a column in a data object resultset."""

    name: str = Field(..., alias='name', description='Name of the column.')
    category: Literal['DIMENSION', 'METRIC', 'TIME_DIMENSION', 'UNKNOWN', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='category', description='Category of the column.\n\nAllowed values for this property are: "DIMENSION", "METRIC", "TIME_DIMENSION", "UNKNOWN", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    data_type: Literal['NUMBER', 'OTHER', 'TIMESTAMP', 'VARCHAR2'] | None = Field(None, alias='dataType', description='Type of a data object column.')
    data_type_name: Literal['NUMBER', 'TIMESTAMP', 'VARCHAR2', 'OTHER', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='dataTypeName', description='Type name of a data object column.\n\nAllowed values for this property are: "NUMBER", "TIMESTAMP", "VARCHAR2", "OTHER", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description='Display name of the column.')
    description: str | None = Field(None, alias='description', description='Description of the column.')
    group_name: str | None = Field(None, alias='groupName', description='Group name of the column.')
    unit_details: DataObjectColumnUnit | None = Field(None, alias='unitDetails', description='The unit_details field of DataObjectColumnMetadata.')


class DataObjectColumnUnit(OpsiBaseModel):
    """Unit details of a data object column."""

    unit_category: Literal['DATA_SIZE', 'TIME', 'POWER', 'TEMPERATURE', 'CORE', 'RATE', 'FREQUENCY', 'OTHER_STANDARD', 'CUSTOM', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='unitCategory', description='Category of the column\'s unit.\n\nAllowed values for this property are: "DATA_SIZE", "TIME", "POWER", "TEMPERATURE", "CORE", "RATE", "FREQUENCY", "OTHER_STANDARD", "CUSTOM", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description="Display name of the column's unit.")


class DataObjectCoreColumnUnit(OpsiBaseModel):
    """Unit details of a data object column of CORE unit category."""

    unit_category: Literal['DATA_SIZE', 'TIME', 'POWER', 'TEMPERATURE', 'CORE', 'RATE', 'FREQUENCY', 'OTHER_STANDARD', 'CUSTOM', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='unitCategory', description='Gets the unit_category of this DataObjectColumnUnit.\nCategory of the column\'s unit.\n\nAllowed values for this property are: "DATA_SIZE", "TIME", "POWER", "TEMPERATURE", "CORE", "RATE", "FREQUENCY", "OTHER_STANDARD", "CUSTOM", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description="Gets the display_name of this DataObjectColumnUnit.\nDisplay name of the column's unit.")
    unit: Literal['CORE', 'MILLI_CORE', 'UNKNOWN_ENUM_VALUE', 'CUSTOM', 'DATA_SIZE', 'FREQUENCY', 'OTHER_STANDARD', 'POWER', 'RATE', 'TEMPERATURE', 'TIME'] | None = Field(None, alias='unit', description='Core unit.\n\nAllowed values for this property are: "CORE", "MILLI_CORE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class DataObjectCustomColumnUnit(OpsiBaseModel):
    """Unit details of a data object column of CUSTOM unit category."""

    unit_category: Literal['DATA_SIZE', 'TIME', 'POWER', 'TEMPERATURE', 'CORE', 'RATE', 'FREQUENCY', 'OTHER_STANDARD', 'CUSTOM', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='unitCategory', description='Gets the unit_category of this DataObjectColumnUnit.\nCategory of the column\'s unit.\n\nAllowed values for this property are: "DATA_SIZE", "TIME", "POWER", "TEMPERATURE", "CORE", "RATE", "FREQUENCY", "OTHER_STANDARD", "CUSTOM", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description="Gets the display_name of this DataObjectColumnUnit.\nDisplay name of the column's unit.")
    unit: Literal['CORE', 'CUSTOM', 'DATA_SIZE', 'FREQUENCY', 'OTHER_STANDARD', 'POWER', 'RATE', 'TEMPERATURE', 'TIME'] | None = Field(None, alias='unit', description='Custom column unit.')


class DataObjectDataSizeColumnUnit(OpsiBaseModel):
    """Unit details of a data object column of DATA_SIZE unit category."""

    unit_category: Literal['DATA_SIZE', 'TIME', 'POWER', 'TEMPERATURE', 'CORE', 'RATE', 'FREQUENCY', 'OTHER_STANDARD', 'CUSTOM', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='unitCategory', description='Gets the unit_category of this DataObjectColumnUnit.\nCategory of the column\'s unit.\n\nAllowed values for this property are: "DATA_SIZE", "TIME", "POWER", "TEMPERATURE", "CORE", "RATE", "FREQUENCY", "OTHER_STANDARD", "CUSTOM", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description="Gets the display_name of this DataObjectColumnUnit.\nDisplay name of the column's unit.")
    unit: Literal['CHARACTER', 'BLOCK', 'BIT', 'BYTE', 'KILO_BYTE', 'MEGA_BYTE', 'GIGA_BYTE', 'TERA_BYTE', 'PETA_BYTE', 'EXA_BYTE', 'ZETTA_BYTE', 'YOTTA_BYTE', 'UNKNOWN_ENUM_VALUE', 'CORE', 'CUSTOM', 'DATA_SIZE', 'FREQUENCY', 'OTHER_STANDARD', 'POWER', 'RATE', 'TEMPERATURE', 'TIME'] | None = Field(None, alias='unit', description='Data size unit.\n\nAllowed values for this property are: "CHARACTER", "BLOCK", "BIT", "BYTE", "KILO_BYTE", "MEGA_BYTE", "GIGA_BYTE", "TERA_BYTE", "PETA_BYTE", "EXA_BYTE", "ZETTA_BYTE", "YOTTA_BYTE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class DataObjectFrequencyColumnUnit(OpsiBaseModel):
    """Unit details of a data object column of FREQEUENCY unit category."""

    unit_category: Literal['DATA_SIZE', 'TIME', 'POWER', 'TEMPERATURE', 'CORE', 'RATE', 'FREQUENCY', 'OTHER_STANDARD', 'CUSTOM', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='unitCategory', description='Gets the unit_category of this DataObjectColumnUnit.\nCategory of the column\'s unit.\n\nAllowed values for this property are: "DATA_SIZE", "TIME", "POWER", "TEMPERATURE", "CORE", "RATE", "FREQUENCY", "OTHER_STANDARD", "CUSTOM", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description="Gets the display_name of this DataObjectColumnUnit.\nDisplay name of the column's unit.")
    unit: Literal['HERTZ', 'KILO_HERTZ', 'MEGA_HERTZ', 'GIGA_HERTZ', 'TERA_HERTZ', 'UNKNOWN_ENUM_VALUE', 'CORE', 'CUSTOM', 'DATA_SIZE', 'FREQUENCY', 'OTHER_STANDARD', 'POWER', 'RATE', 'TEMPERATURE', 'TIME'] | None = Field(None, alias='unit', description='Frequency unit.\n\nAllowed values for this property are: "HERTZ", "KILO_HERTZ", "MEGA_HERTZ", "GIGA_HERTZ", "TERA_HERTZ", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class DataObjectOtherStandardColumnUnit(OpsiBaseModel):
    """Unit details of a data object column of OTHER_STANDARD unit category."""

    unit_category: Literal['DATA_SIZE', 'TIME', 'POWER', 'TEMPERATURE', 'CORE', 'RATE', 'FREQUENCY', 'OTHER_STANDARD', 'CUSTOM', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='unitCategory', description='Gets the unit_category of this DataObjectColumnUnit.\nCategory of the column\'s unit.\n\nAllowed values for this property are: "DATA_SIZE", "TIME", "POWER", "TEMPERATURE", "CORE", "RATE", "FREQUENCY", "OTHER_STANDARD", "CUSTOM", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description="Gets the display_name of this DataObjectColumnUnit.\nDisplay name of the column's unit.")
    unit: Literal['PERCENTAGE', 'COUNT', 'IO', 'BOOLEAN', 'OPERATION', 'TRANSACTION', 'CONNECTION', 'ACCESS', 'REQUEST', 'MESSAGE', 'EXECUTION', 'LOGONS', 'THREAD', 'ERROR', 'UNKNOWN_ENUM_VALUE', 'CORE', 'CUSTOM', 'DATA_SIZE', 'FREQUENCY', 'OTHER_STANDARD', 'POWER', 'RATE', 'TEMPERATURE', 'TIME'] | None = Field(None, alias='unit', description='Other standard column unit.\n\nAllowed values for this property are: "PERCENTAGE", "COUNT", "IO", "BOOLEAN", "OPERATION", "TRANSACTION", "CONNECTION", "ACCESS", "REQUEST", "MESSAGE", "EXECUTION", "LOGONS", "THREAD", "ERROR", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class DataObjectPowerColumnUnit(OpsiBaseModel):
    """Unit details of a data object column of POWER unit category."""

    unit_category: Literal['DATA_SIZE', 'TIME', 'POWER', 'TEMPERATURE', 'CORE', 'RATE', 'FREQUENCY', 'OTHER_STANDARD', 'CUSTOM', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='unitCategory', description='Gets the unit_category of this DataObjectColumnUnit.\nCategory of the column\'s unit.\n\nAllowed values for this property are: "DATA_SIZE", "TIME", "POWER", "TEMPERATURE", "CORE", "RATE", "FREQUENCY", "OTHER_STANDARD", "CUSTOM", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description="Gets the display_name of this DataObjectColumnUnit.\nDisplay name of the column's unit.")
    unit: Literal['AMP', 'WATT', 'KILO_WATT', 'MEGA_WATT', 'GIGA_WATT', 'UNKNOWN_ENUM_VALUE', 'CORE', 'CUSTOM', 'DATA_SIZE', 'FREQUENCY', 'OTHER_STANDARD', 'POWER', 'RATE', 'TEMPERATURE', 'TIME'] | None = Field(None, alias='unit', description='Power unit.\n\nAllowed values for this property are: "AMP", "WATT", "KILO_WATT", "MEGA_WATT", "GIGA_WATT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class DataObjectQuery(OpsiBaseModel):
    """Information required to form and execute query on a data object."""

    query_type: Literal['TEMPLATIZED_QUERY', 'STANDARD_QUERY'] = Field(..., alias='queryType', description='Type of Query\n\nAllowed values for this property are: "TEMPLATIZED_QUERY", "STANDARD_QUERY"')
    bind_params: list[DataObjectBindParameter] | None = Field(None, alias='bindParams', description='List of bind parameters to be applied in the query.')
    query_execution_timeout_in_seconds: float | None = Field(None, alias='queryExecutionTimeoutInSeconds', description='Timeout (in seconds) to be set for the data object query execution.')


class DataObjectQueryTimeFilters(OpsiBaseModel):
    """Time filters to be applied in the data object query."""

    time_period: str | None = Field(None, alias='timePeriod', description='Specify time period in ISO 8601 format with respect to current time.\nDefault is last 30 days represented by P30D.\nIf timePeriod is specified, then timeStart and timeEnd will be ignored.\nExamples: P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months).')
    time_start: datetime | None = Field(None, alias='timeStart', description='Start time in UTC in RFC3339 formatted datetime string. Example: 2021-10-30T00:00:00.000Z.\ntimeStart and timeEnd are used together. If timePeriod is specified, this parameter is ignored.')
    time_end: datetime | None = Field(None, alias='timeEnd', description='End time in UTC in RFC3339 formatted datetime string. Example: 2021-10-30T00:00:00.000Z.\ntimeStart and timeEnd are used together. If timePeriod is specified, this parameter is ignored.\nIf timeEnd is not specified, current time is used as timeEnd.')


class DataObjectRateColumnUnit(OpsiBaseModel):
    """Unit details of a data object column of RATE unit category."""

    unit_category: Literal['DATA_SIZE', 'TIME', 'POWER', 'TEMPERATURE', 'CORE', 'RATE', 'FREQUENCY', 'OTHER_STANDARD', 'CUSTOM', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='unitCategory', description='Gets the unit_category of this DataObjectColumnUnit.\nCategory of the column\'s unit.\n\nAllowed values for this property are: "DATA_SIZE", "TIME", "POWER", "TEMPERATURE", "CORE", "RATE", "FREQUENCY", "OTHER_STANDARD", "CUSTOM", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description="Gets the display_name of this DataObjectColumnUnit.\nDisplay name of the column's unit.")
    numerator: DataObjectColumnUnit | None = Field(None, alias='numerator', description='The numerator field of DataObjectRateColumnUnit.')
    denominator: DataObjectColumnUnit | None = Field(None, alias='denominator', description='The denominator field of DataObjectRateColumnUnit.')


class DataObjectStandardQuery(OpsiBaseModel):
    """Information required to execute query on data objects. Query is given in standard SQL syntax providing flexibility to form complex queries such as queries with joins and nested queries."""

    query_type: Literal['TEMPLATIZED_QUERY', 'STANDARD_QUERY'] = Field(..., alias='queryType', description='Gets the query_type of this DataObjectQuery.\nType of Query\n\nAllowed values for this property are: "TEMPLATIZED_QUERY", "STANDARD_QUERY"')
    bind_params: list[DataObjectBindParameter] | None = Field(None, alias='bindParams', description='Gets the bind_params of this DataObjectQuery.\nList of bind parameters to be applied in the query.')
    query_execution_timeout_in_seconds: float | None = Field(None, alias='queryExecutionTimeoutInSeconds', description='Gets the query_execution_timeout_in_seconds of this DataObjectQuery.\nTimeout (in seconds) to be set for the data object query execution.')
    statement: str | None = Field(None, alias='statement', description='SQL query statement with standard Oracle supported SQL syntax.\n- When Warehouse (e.g: Awr hub) data objects are queried, use the actual names of underlying data objects (e.g: tables, views) in the query.\nThe same query that works through JDBC connection with the OperationsInsightsWarehouseUsers credentials will work here and vice-versa.\nSCHEMA.VIEW syntax can also be used here.\n- When OPSI data objects are queried, use name of the respective OPSI data object, just like how views are used in a query.\nIdentifier of the OPSI data object cannot be used in the query.')
    time_filters: DataObjectQueryTimeFilters | None = Field(None, alias='timeFilters', description='The time_filters field of DataObjectStandardQuery.')


class DataObjectTemperatureColumnUnit(OpsiBaseModel):
    """Unit details of a data object column of TEMPERATURE unit category."""

    unit_category: Literal['DATA_SIZE', 'TIME', 'POWER', 'TEMPERATURE', 'CORE', 'RATE', 'FREQUENCY', 'OTHER_STANDARD', 'CUSTOM', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='unitCategory', description='Gets the unit_category of this DataObjectColumnUnit.\nCategory of the column\'s unit.\n\nAllowed values for this property are: "DATA_SIZE", "TIME", "POWER", "TEMPERATURE", "CORE", "RATE", "FREQUENCY", "OTHER_STANDARD", "CUSTOM", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description="Gets the display_name of this DataObjectColumnUnit.\nDisplay name of the column's unit.")
    unit: Literal['CELSIUS', 'FAHRENHEIT', 'UNKNOWN_ENUM_VALUE', 'CORE', 'CUSTOM', 'DATA_SIZE', 'FREQUENCY', 'OTHER_STANDARD', 'POWER', 'RATE', 'TEMPERATURE', 'TIME'] | None = Field(None, alias='unit', description='Temparature unit.\n\nAllowed values for this property are: "CELSIUS", "FAHRENHEIT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class DataObjectTemplatizedQuery(OpsiBaseModel):
    """Information required in a structured template to form and execute query on a data object."""

    query_type: Literal['TEMPLATIZED_QUERY', 'STANDARD_QUERY'] = Field(..., alias='queryType', description='Gets the query_type of this DataObjectQuery.\nType of Query\n\nAllowed values for this property are: "TEMPLATIZED_QUERY", "STANDARD_QUERY"')
    bind_params: list[DataObjectBindParameter] | None = Field(None, alias='bindParams', description='Gets the bind_params of this DataObjectQuery.\nList of bind parameters to be applied in the query.')
    query_execution_timeout_in_seconds: float | None = Field(None, alias='queryExecutionTimeoutInSeconds', description='Gets the query_execution_timeout_in_seconds of this DataObjectQuery.\nTimeout (in seconds) to be set for the data object query execution.')
    select_list: list[str] | None = Field(None, alias='selectList', description='List of items to be added into the SELECT clause of the query; items will be added with comma separation.')
    from_clause: str | None = Field(None, alias='fromClause', description='Unique data object name that will be added into the FROM clause of the query, just like a view name in FROM clause.\n- Use actual name of the data objects (e.g: tables, views) in case of Warehouse (e.g: Awr hub) data objects query. SCHEMA.VIEW name syntax can also be used here.\ne.g: SYS.DBA_HIST_SNAPSHOT or DBA_HIST_SNAPSHOT\n- Use name of the data object (e.g: SQL_STATS_DO) in case of OPSI data objects. Identifier of the OPSI data object cannot be used here.')
    where_conditions_list: list[str] | None = Field(None, alias='whereConditionsList', description='List of items to be added into the WHERE clause of the query; items will be added with AND separation.\nItem can contain a single condition or multiple conditions.\nSingle condition e.g:  "optimizer_mode=\'mode1\'"\nMultiple conditions e.g: (module=\'module1\' OR module=\'module2\')')
    group_by_list: list[str] | None = Field(None, alias='groupByList', description='List of items to be added into the GROUP BY clause of the query; items will be added with comma separation.')
    having_conditions_list: list[str] | None = Field(None, alias='havingConditionsList', description='List of items to be added into the HAVING clause of the query; items will be added with AND separation.')
    order_by_list: list[str] | None = Field(None, alias='orderByList', description='List of items to be added into the ORDER BY clause of the query; items will be added with comma separation.')
    time_filters: DataObjectQueryTimeFilters | None = Field(None, alias='timeFilters', description='The time_filters field of DataObjectTemplatizedQuery.')


class DataObjectTimeColumnUnit(OpsiBaseModel):
    """Unit details of a data object column of TIME unit category."""

    unit_category: Literal['DATA_SIZE', 'TIME', 'POWER', 'TEMPERATURE', 'CORE', 'RATE', 'FREQUENCY', 'OTHER_STANDARD', 'CUSTOM', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='unitCategory', description='Gets the unit_category of this DataObjectColumnUnit.\nCategory of the column\'s unit.\n\nAllowed values for this property are: "DATA_SIZE", "TIME", "POWER", "TEMPERATURE", "CORE", "RATE", "FREQUENCY", "OTHER_STANDARD", "CUSTOM", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description="Gets the display_name of this DataObjectColumnUnit.\nDisplay name of the column's unit.")
    unit: Literal['NANO_SECOND', 'MICRO_SECOND', 'MILLI_SECOND', 'CENTI_SECOND', 'SECOND', 'HOUR', 'DAY', 'WEEK', 'MONTH', 'YEAR', 'MINUTE', 'UNKNOWN_ENUM_VALUE', 'CORE', 'CUSTOM', 'DATA_SIZE', 'FREQUENCY', 'OTHER_STANDARD', 'POWER', 'RATE', 'TEMPERATURE', 'TIME'] | None = Field(None, alias='unit', description='Time unit.\n\nAllowed values for this property are: "NANO_SECOND", "MICRO_SECOND", "MILLI_SECOND", "CENTI_SECOND", "SECOND", "HOUR", "DAY", "WEEK", "MONTH", "YEAR", "MINUTE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class DatabaseConfigurationCollection(OpsiBaseModel):
    """Collection of database insight configuration summary objects."""

    items: list[DatabaseConfigurationSummary] = Field(..., alias='items', description='Array of database insight configurations summary objects.')


class DatabaseConfigurationMetricGroup(OpsiBaseModel):
    """Supported configuration metric groups for database capacity planning service."""

    metric_name: Literal['DB_EXTERNAL_PROPERTIES', 'DB_EXTERNAL_INSTANCE', 'DB_OS_CONFIG_INSTANCE', 'DB_PARAMETERS', 'DB_CONNECTION_STATUS', 'HOST_RESOURCE_ALLOCATION', 'ASM_ENTITY', 'EXADATA_CELL_CONFIG'] = Field(..., alias='metricName', description='Name of the metric group.\n\nAllowed values for this property are: "DB_EXTERNAL_PROPERTIES", "DB_EXTERNAL_INSTANCE", "DB_OS_CONFIG_INSTANCE", "DB_PARAMETERS", "DB_CONNECTION_STATUS", "HOST_RESOURCE_ALLOCATION", "ASM_ENTITY", "EXADATA_CELL_CONFIG"')
    time_collected: datetime | None = Field(None, alias='timeCollected', description='Collection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')


class DatabaseConfigurationSummary(OpsiBaseModel):
    """Summary of a database configuration for a resource."""

    database_insight_id: str = Field(..., alias='databaseInsightId', description='The OCID of the database insight resource.')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Source of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    database_name: str = Field(..., alias='databaseName', description='The database name. The database name is unique within the tenancy.')
    database_display_name: str = Field(..., alias='databaseDisplayName', description='The user-friendly name for the database. The name does not have to be unique.')
    database_type: str = Field(..., alias='databaseType', description='Ops Insights internal representation of the database type.')
    database_version: str = Field(..., alias='databaseVersion', description='The version of the database.')
    is_advanced_features_enabled: bool = Field(..., alias='isAdvancedFeaturesEnabled', description='Flag is to identify if advanced features for autonomous database is enabled or not')
    cdb_name: str = Field(..., alias='cdbName', description='Name of the CDB.Only applies to PDB.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    processor_count: int | None = Field(None, alias='processorCount', description='Processor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)


class DatabaseDetails(OpsiBaseModel):
    """Partial information about the database which includes id, name, type."""

    id: str = Field(..., alias='id', description='The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    database_name: str = Field(..., alias='databaseName', description='The database name. The database name is unique within the tenancy.')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='The user-friendly name for the database. The name does not have to be unique.')
    database_type: str = Field(..., alias='databaseType', description='Ops Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='The version of the database.')
    instances: list[HostInstanceMap] | None = Field(None, alias='instances', description='Array of hostname and instance name.')
    cdb_name: str | None = Field(None, alias='cdbName', description='Name of the CDB.Only applies to PDB.')


class DatabaseInsight(OpsiBaseModel):
    """Database insight resource."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Source of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Database insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Compartment identifier of the database')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Indicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    database_type: str | None = Field(None, alias='databaseType', description='Ops Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='The version of the database.')
    processor_count: int | None = Field(None, alias='processorCount', description='Processor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='The time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='The current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='A message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')


class DatabaseInsightSummary(OpsiBaseModel):
    """Summary of a database insight resource."""

    id: str = Field(..., alias='id', description='The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='The OCID of the compartment.')
    database_name: str | None = Field(None, alias='databaseName', description='The database name. The database name is unique within the tenancy.')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='The user-friendly name for the database. The name does not have to be unique.')
    database_type: str | None = Field(None, alias='databaseType', description='Ops Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='The version of the database.')
    database_host_names: list[str] | None = Field(None, alias='databaseHostNames', description='The hostnames for the database.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Source of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    processor_count: int | None = Field(None, alias='processorCount', description='Processor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Indicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='The time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='The current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='A message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')


class DatabaseInsights(OpsiBaseModel):
    """Logical grouping used for Operations Insights database-targeted operations."""

    database_insights: Any | None = Field(None, alias='databaseInsights', description='Database Insights Object.')


class DatabaseInsightsCollection(OpsiBaseModel):
    """Collection of database insight summary objects."""

    items: list[DatabaseInsightSummary] = Field(..., alias='items', description='Array of database insight summary objects.')


class DatabaseInsightsDataObject(OpsiBaseModel):
    """Database insights data object."""

    identifier: str = Field(..., alias='identifier', description='Gets the identifier of this OpsiDataObject.\nUnique identifier of OPSI data object.')
    data_object_type: Literal['DATABASE_INSIGHTS_DATA_OBJECT', 'HOST_INSIGHTS_DATA_OBJECT', 'EXADATA_INSIGHTS_DATA_OBJECT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='dataObjectType', description='Gets the data_object_type of this OpsiDataObject.\nType of OPSI data object.\n\nAllowed values for this property are: "DATABASE_INSIGHTS_DATA_OBJECT", "HOST_INSIGHTS_DATA_OBJECT", "EXADATA_INSIGHTS_DATA_OBJECT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str = Field(..., alias='displayName', description='Gets the display_name of this OpsiDataObject.\nUser-friendly name of OPSI data object.')
    description: str | None = Field(None, alias='description', description='Gets the description of this OpsiDataObject.\nDescription of OPSI data object.')
    name: str | None = Field(None, alias='name', description='Gets the name of this OpsiDataObject.\nName of the data object, which can be used in data object queries just like how view names are used in a query.')
    group_names: list[str] | None = Field(None, alias='groupNames', description='Gets the group_names of this OpsiDataObject.\nNames of all the groups to which the data object belongs to.')
    supported_query_time_period: str | None = Field(None, alias='supportedQueryTimePeriod', description='Gets the supported_query_time_period of this OpsiDataObject.\nTime period supported by the data object for quering data.\nTime period is in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D.\nExamples: P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months).')
    columns_metadata: list[DataObjectColumnMetadata] = Field(..., alias='columnsMetadata', description='Gets the columns_metadata of this OpsiDataObject.\nMetadata of columns in a data object.')
    supported_query_params: list[OpsiDataObjectSupportedQueryParam] | None = Field(None, alias='supportedQueryParams', description='Gets the supported_query_params of this OpsiDataObject.\nSupported query parameters by this OPSI data object that can be configured while a data object query involving this data object is executed.')


class DatabaseInsightsDataObjectSummary(OpsiBaseModel):
    """Summary of a database insights data object."""

    identifier: str = Field(..., alias='identifier', description='Gets the identifier of this OpsiDataObjectSummary.\nUnique identifier of OPSI data object.')
    data_object_type: Literal['DATABASE_INSIGHTS_DATA_OBJECT', 'HOST_INSIGHTS_DATA_OBJECT', 'EXADATA_INSIGHTS_DATA_OBJECT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='dataObjectType', description='Gets the data_object_type of this OpsiDataObjectSummary.\nType of OPSI data object.\n\nAllowed values for this property are: "DATABASE_INSIGHTS_DATA_OBJECT", "HOST_INSIGHTS_DATA_OBJECT", "EXADATA_INSIGHTS_DATA_OBJECT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str = Field(..., alias='displayName', description='Gets the display_name of this OpsiDataObjectSummary.\nUser-friendly name of OPSI data object.')
    description: str | None = Field(None, alias='description', description='Gets the description of this OpsiDataObjectSummary.\nDescription of OPSI data object.')
    name: str | None = Field(None, alias='name', description='Gets the name of this OpsiDataObjectSummary.\nName of the data object, which can be used in data object queries just like how view names are used in a query.')
    group_names: list[str] | None = Field(None, alias='groupNames', description='Gets the group_names of this OpsiDataObjectSummary.\nNames of all the groups to which the data object belongs to.')


class DatabaseParameterTypeDetails(OpsiBaseModel):
    """Database parameter details."""

    type: Literal['SCHEMA_OBJECT', 'SQL', 'DATABASE_PARAMETER', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='type', description='Gets the type of this RelatedObjectTypeDetails.\nType of related object\n\nAllowed values for this property are: "SCHEMA_OBJECT", "SQL", "DATABASE_PARAMETER", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    name: str = Field(..., alias='name', description='Name of database parameter')


class DiskGroupDetails(OpsiBaseModel):
    """Information about a diskgroup which includes diskgroup name and ASM name."""

    diskgroup_name: str = Field(..., alias='diskgroupName', description='The diskgroup name.')
    asm_name: str = Field(..., alias='asmName', description='The ASM name.')


class DiskStatistics(OpsiBaseModel):
    """Aggregated data per disk."""

    disk_name: str = Field(..., alias='diskName', description='Name of the disk.')
    disk_unallocated_in_gbs: float = Field(..., alias='diskUnallocatedInGBs', description='Value for unallocated space in a disk.')
    disk_usage_in_gbs: float = Field(..., alias='diskUsageInGBs', description='Disk usage.')
    disk_size_in_gbs: float = Field(..., alias='diskSizeInGBs', description='Size of the disk.')


class DownloadOperationsInsightsWarehouseWalletDetails(OpsiRequestModel):
    """Download Wallet details."""

    operations_insights_warehouse_wallet_password: str = Field(..., alias='operationsInsightsWarehouseWalletPassword', description='User provided ADW wallet password for the Ops Insights Warehouse.')


class EmManagedExternalDatabaseConfigurationSummary(OpsiBaseModel):
    """Configuration summary of a EM Managed External database."""

    database_insight_id: str = Field(..., alias='databaseInsightId', description='Gets the database_insight_id of this DatabaseConfigurationSummary. The OCID of the database insight resource.')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseConfigurationSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseConfigurationSummary. The OCID of the compartment.')
    database_name: str = Field(..., alias='databaseName', description='Gets the database_name of this DatabaseConfigurationSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str = Field(..., alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseConfigurationSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str = Field(..., alias='databaseType', description='Gets the database_type of this DatabaseConfigurationSummary.\nOps Insights internal representation of the database type.')
    database_version: str = Field(..., alias='databaseVersion', description='Gets the database_version of this DatabaseConfigurationSummary.\nThe version of the database.')
    is_advanced_features_enabled: bool = Field(..., alias='isAdvancedFeaturesEnabled', description='Gets the is_advanced_features_enabled of this DatabaseConfigurationSummary.\nFlag is to identify if advanced features for autonomous database is enabled or not')
    cdb_name: str = Field(..., alias='cdbName', description='Gets the cdb_name of this DatabaseConfigurationSummary.\nName of the CDB.Only applies to PDB.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseConfigurationSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_bridge_id: str = Field(..., alias='enterpriseManagerBridgeId', description='OPSI Enterprise Manager Bridge OCID')
    instances: list[HostInstanceMap] = Field(..., alias='instances', description='Array of hostname and instance name.')
    exadata_details: ExadataDetails = Field(..., alias='exadataDetails', description='The exadata_details field of EmManagedExternalDatabaseConfigurationSummary.')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    enterprise_manager_console_url: str = Field(..., alias='enterpriseManagerConsoleUrl', description='Enterprise Manager Console Url')
    enterprise_manager_oms_ver: str = Field(..., alias='enterpriseManagerOmsVer', description='Enterprise Manager OMS Version')
    enterprise_manager_entity_type: str = Field(..., alias='enterpriseManagerEntityType', description='Enterprise Manager Entity Type')


class EmManagedExternalDatabaseInsight(OpsiBaseModel):
    """Database insight resource."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsight.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsight.\nDatabase insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseInsight.\nCompartment identifier of the database')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this DatabaseInsight.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsight.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsight.\nThe version of the database.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this DatabaseInsight.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsight.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsight.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsight.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_entity_name: str = Field(..., alias='enterpriseManagerEntityName', description='Enterprise Manager Entity Name')
    enterprise_manager_entity_type: str = Field(..., alias='enterpriseManagerEntityType', description='Enterprise Manager Entity Type')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    enterprise_manager_entity_display_name: str | None = Field(None, alias='enterpriseManagerEntityDisplayName', description='Enterprise Manager Entity Display Name')
    enterprise_manager_bridge_id: str = Field(..., alias='enterpriseManagerBridgeId', description='OPSI Enterprise Manager Bridge OCID')
    exadata_insight_id: str | None = Field(None, alias='exadataInsightId', description='The OCID of the Exadata insight.')


class EmManagedExternalDatabaseInsightSummary(OpsiBaseModel):
    """Summary of a database insight resource."""

    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsightSummary. The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='Gets the database_id of this DatabaseInsightSummary. The OCID of the database.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='Gets the compartment_id of this DatabaseInsightSummary. The OCID of the compartment.')
    database_name: str | None = Field(None, alias='databaseName', description='Gets the database_name of this DatabaseInsightSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseInsightSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsightSummary.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsightSummary.\nThe version of the database.')
    database_host_names: list[str] | None = Field(None, alias='databaseHostNames', description='Gets the database_host_names of this DatabaseInsightSummary.\nThe hostnames for the database.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this DatabaseInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsightSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this DatabaseInsightSummary.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this DatabaseInsightSummary.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsightSummary.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsightSummary.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsightSummary.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_entity_name: str = Field(..., alias='enterpriseManagerEntityName', description='Enterprise Manager Entity Name')
    enterprise_manager_entity_type: str = Field(..., alias='enterpriseManagerEntityType', description='Enterprise Manager Entity Type')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    enterprise_manager_entity_display_name: str | None = Field(None, alias='enterpriseManagerEntityDisplayName', description='Enterprise Manager Entity Display Name')
    enterprise_manager_bridge_id: str = Field(..., alias='enterpriseManagerBridgeId', description='OPSI Enterprise Manager Bridge OCID')
    exadata_insight_id: str | None = Field(None, alias='exadataInsightId', description='The OCID of the Exadata insight.')


class EmManagedExternalExadataInsight(OpsiBaseModel):
    """EM-managed Exadata insight resource."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this ExadataInsight.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this ExadataInsight.\nExadata insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this ExadataInsight.\nCompartment identifier of the Exadata insight resource')
    exadata_name: str = Field(..., alias='exadataName', description='Gets the exadata_name of this ExadataInsight.\nThe Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str | None = Field(None, alias='exadataDisplayName', description='Gets the exadata_display_name of this ExadataInsight.\nThe user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataType', description='Gets the exadata_type of this ExadataInsight.\nOperations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataRackType', description='Gets the exadata_rack_type of this ExadataInsight.\nExadata rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    is_virtualized_exadata: bool | None = Field(None, alias='isVirtualizedExadata', description='Gets the is_virtualized_exadata of this ExadataInsight.\ntrue if virtualization is used in the Exadata system')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this ExadataInsight.\nIndicates the status of an Exadata insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    chargeback_plan_details: ChargebackPlanDetails | None = Field(None, alias='chargebackPlanDetails', description='Gets the chargeback_plan_details of this ExadataInsight.')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this ExadataInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this ExadataInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this ExadataInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this ExadataInsight.\nThe time the the Exadata insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this ExadataInsight.\nThe time the Exadata insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this ExadataInsight.\nThe current state of the Exadata insight.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this ExadataInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    status_details: str | None = Field(None, alias='statusDetails', description='Gets the status_details of this ExadataInsight.\nA message describing the status of the Exadata Resource. For example, it can be used to provide actionable information about the policies needed to access the Exadata Resource.')
    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_entity_name: str = Field(..., alias='enterpriseManagerEntityName', description='Enterprise Manager Entity Name')
    enterprise_manager_entity_type: str = Field(..., alias='enterpriseManagerEntityType', description='Enterprise Manager Entity Type')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    enterprise_manager_entity_display_name: str | None = Field(None, alias='enterpriseManagerEntityDisplayName', description='Enterprise Manager Entity Display Name')
    enterprise_manager_bridge_id: str = Field(..., alias='enterpriseManagerBridgeId', description='OPSI Enterprise Manager Bridge OCID')
    is_auto_sync_enabled: bool | None = Field(None, alias='isAutoSyncEnabled', description='Set to true to enable automatic enablement and disablement of related targets from Enterprise Manager. New resources (e.g. Database Insights) will be placed in the same compartment as the related Exadata Insight.')


class EmManagedExternalExadataInsightSummary(OpsiBaseModel):
    """Summary of an Exadata insight resource."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this ExadataInsightSummary.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this ExadataInsightSummary. The OCID of the Exadata insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this ExadataInsightSummary. The OCID of the compartment.')
    exadata_name: str = Field(..., alias='exadataName', description='Gets the exadata_name of this ExadataInsightSummary.\nThe Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str | None = Field(None, alias='exadataDisplayName', description='Gets the exadata_display_name of this ExadataInsightSummary.\nThe user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataType', description='Gets the exadata_type of this ExadataInsightSummary.\nOperations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataRackType', description='Gets the exadata_rack_type of this ExadataInsightSummary.\nOperations Insights internal representation of the the Exadata system rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this ExadataInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this ExadataInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this ExadataInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this ExadataInsightSummary.\nIndicates the status of an Exadata insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    chargeback_plan_details: ChargebackPlanDetails | None = Field(None, alias='chargebackPlanDetails', description='Gets the chargeback_plan_details of this ExadataInsightSummary.')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this ExadataInsightSummary.\nThe time the the Exadata insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this ExadataInsightSummary.\nThe time the Exadata insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this ExadataInsightSummary.\nThe current state of the Exadata insight.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this ExadataInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    status_details: str | None = Field(None, alias='statusDetails', description='Gets the status_details of this ExadataInsightSummary.\nA message describing the status of the Exadata Resource. For example, it can be used to provide actionable information about the policies needed to access the Exadata Resource.')
    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_entity_name: str = Field(..., alias='enterpriseManagerEntityName', description='Enterprise Manager Entity Name')
    enterprise_manager_entity_type: str = Field(..., alias='enterpriseManagerEntityType', description='Enterprise Manager Entity Type')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    enterprise_manager_entity_display_name: str | None = Field(None, alias='enterpriseManagerEntityDisplayName', description='Enterprise Manager Entity Display Name')
    enterprise_manager_bridge_id: str = Field(..., alias='enterpriseManagerBridgeId', description='OPSI Enterprise Manager Bridge OCID')


class EmManagedExternalHostConfigurationSummary(OpsiBaseModel):
    """Configuration summary of a EM Managed External host."""

    host_insight_id: str = Field(..., alias='hostInsightId', description='Gets the host_insight_id of this HostConfigurationSummary. The OCID of the host insight resource.')
    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostConfigurationSummary.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostConfigurationSummary. The OCID of the compartment.')
    host_name: str = Field(..., alias='hostName', description='Gets the host_name of this HostConfigurationSummary.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='platformType', description='Gets the platform_type of this HostConfigurationSummary.\nPlatform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    platform_version: str = Field(..., alias='platformVersion', description='Gets the platform_version of this HostConfigurationSummary.\nPlatform version.')
    platform_vendor: str = Field(..., alias='platformVendor', description='Gets the platform_vendor of this HostConfigurationSummary.\nPlatform vendor.')
    total_cpus: int = Field(..., alias='totalCpus', description='Gets the total_cpus of this HostConfigurationSummary.\nTotal CPU on this host.')
    total_memory_in_gbs: float = Field(..., alias='totalMemoryInGBs', description='Gets the total_memory_in_gbs of this HostConfigurationSummary.\nTotal amount of usable physical memory in gibabytes')
    cpu_architecture: str = Field(..., alias='cpuArchitecture', description='Gets the cpu_architecture of this HostConfigurationSummary.\nCPU architechure')
    cpu_cache_in_mbs: float = Field(..., alias='cpuCacheInMBs', description='Gets the cpu_cache_in_mbs of this HostConfigurationSummary.\nSize of cache memory in megabytes.')
    cpu_vendor: str = Field(..., alias='cpuVendor', description='Gets the cpu_vendor of this HostConfigurationSummary.\nName of the CPU vendor.')
    cpu_frequency_in_mhz: float = Field(..., alias='cpuFrequencyInMhz', description='Gets the cpu_frequency_in_mhz of this HostConfigurationSummary.\nClock frequency of the processor in megahertz.')
    cpu_implementation: str = Field(..., alias='cpuImplementation', description='Gets the cpu_implementation of this HostConfigurationSummary.\nModel name of processor.')
    cores_per_socket: int = Field(..., alias='coresPerSocket', description='Gets the cores_per_socket of this HostConfigurationSummary.\nNumber of cores per socket.')
    total_sockets: int = Field(..., alias='totalSockets', description='Gets the total_sockets of this HostConfigurationSummary.\nNumber of total sockets.')
    threads_per_socket: int = Field(..., alias='threadsPerSocket', description='Gets the threads_per_socket of this HostConfigurationSummary.\nNumber of threads per socket.')
    is_hyper_threading_enabled: bool = Field(..., alias='isHyperThreadingEnabled', description='Gets the is_hyper_threading_enabled of this HostConfigurationSummary.\nIndicates if hyper-threading is enabled or not')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this HostConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this HostConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_bridge_id: str = Field(..., alias='enterpriseManagerBridgeId', description='OPSI Enterprise Manager Bridge OCID')
    exadata_details: ExadataDetails = Field(..., alias='exadataDetails', description='The exadata_details field of EmManagedExternalHostConfigurationSummary.')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    enterprise_manager_console_url: str = Field(..., alias='enterpriseManagerConsoleUrl', description='Enterprise Manager Console Url')
    enterprise_manager_oms_ver: str = Field(..., alias='enterpriseManagerOmsVer', description='Enterprise Manager OMS Version')
    enterprise_manager_entity_type: str = Field(..., alias='enterpriseManagerEntityType', description='Enterprise Manager Entity Type')


class EmManagedExternalHostInsight(OpsiBaseModel):
    """EM-managed external host insight resource."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostInsight.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this HostInsight. The OCID of the host insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostInsight. The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='Gets the host_name of this HostInsight.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='Gets the host_display_name of this HostInsight.\nThe user-friendly name for the host. The name does not have to be unique.')
    host_type: str | None = Field(None, alias='hostType', description='Gets the host_type of this HostInsight.\nOps Insights internal representation of the host type. Possible value is EXTERNAL-HOST.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this HostInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this HostInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this HostInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this HostInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this HostInsight.\nIndicates the status of a host insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this HostInsight.\nThe time the the host insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this HostInsight.\nThe time the host insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this HostInsight.\nThe current state of the host.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this HostInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_entity_name: str = Field(..., alias='enterpriseManagerEntityName', description='Enterprise Manager Entity Name')
    enterprise_manager_entity_type: str = Field(..., alias='enterpriseManagerEntityType', description='Enterprise Manager Entity Type')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    enterprise_manager_entity_display_name: str | None = Field(None, alias='enterpriseManagerEntityDisplayName', description='Enterprise Manager Entity Display Name')
    enterprise_manager_bridge_id: str = Field(..., alias='enterpriseManagerBridgeId', description='OPSI Enterprise Manager Bridge OCID')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    platform_name: str | None = Field(None, alias='platformName', description='Platform name.')
    platform_version: str | None = Field(None, alias='platformVersion', description='Platform version.')
    exadata_insight_id: str | None = Field(None, alias='exadataInsightId', description='The OCID of the Exadata insight.')


class EmManagedExternalHostInsightSummary(OpsiBaseModel):
    """Summary of an EM-managed external host insight resource."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostInsightSummary.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this HostInsightSummary. The OCID of the host insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostInsightSummary. The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='Gets the host_name of this HostInsightSummary.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='Gets the host_display_name of this HostInsightSummary.\nThe user-friendly name for the host. The name does not have to be unique.')
    host_type: str | None = Field(None, alias='hostType', description='Gets the host_type of this HostInsightSummary.\nOps Insights internal representation of the host type. Possible value is EXTERNAL-HOST.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this HostInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this HostInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this HostInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this HostInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='Gets the opsi_private_endpoint_id of this HostInsightSummary. The OCID of the OPSI private endpoint.')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this HostInsightSummary.\nIndicates the status of a host insight in Ops Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this HostInsightSummary.\nThe time the the host insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this HostInsightSummary.\nThe time the host insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this HostInsightSummary.\nThe current state of the host.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this HostInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_entity_name: str = Field(..., alias='enterpriseManagerEntityName', description='Enterprise Manager Entity Name')
    enterprise_manager_entity_type: str = Field(..., alias='enterpriseManagerEntityType', description='Enterprise Manager Entity Type')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    enterprise_manager_entity_display_name: str | None = Field(None, alias='enterpriseManagerEntityDisplayName', description='Enterprise Manager Entity Display Name')
    enterprise_manager_bridge_id: str = Field(..., alias='enterpriseManagerBridgeId', description='OPSI Enterprise Manager Bridge OCID')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_insight_id: str | None = Field(None, alias='exadataInsightId', description='The OCID of the Exadata insight.')


class EnableAutonomousDatabaseInsightAdvancedFeaturesDetails(OpsiRequestModel):
    """The advanced feature details for autonomous database to be enabled."""

    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    connection_details: ConnectionDetails = Field(..., alias='connectionDetails', description='The connection_details field of EnableAutonomousDatabaseInsightAdvancedFeaturesDetails.')
    credential_details: CredentialDetails = Field(..., alias='credentialDetails', description='The credential_details field of EnableAutonomousDatabaseInsightAdvancedFeaturesDetails.')


class EnableAutonomousDatabaseInsightDetails(OpsiBaseModel):
    """The information about database to be analyzed. When isAdvancedFeaturesEnabled is set to false, parameters connectionDetails, credentialDetails and opsiPrivateEndpoint are optional. Otherwise, connectionDetails and crendetialDetails are required to enable full OPSI service features. If the Autonomouse Database is configured with private, restricted or dedicated access, opsiPrivateEndpoint parameter is required."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    database_resource_type: str | None = Field(None, alias='databaseResourceType', description='OCI database resource type')
    is_advanced_features_enabled: bool = Field(..., alias='isAdvancedFeaturesEnabled', description='Flag is to identify if advanced features for autonomous database is enabled or not')
    connection_details: ConnectionDetails | None = Field(None, alias='connectionDetails', description='The connection_details field of EnableAutonomousDatabaseInsightDetails.')
    credential_details: CredentialDetails | None = Field(None, alias='credentialDetails', description='The credential_details field of EnableAutonomousDatabaseInsightDetails.')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')


class EnableDatabaseInsightDetails(OpsiRequestModel):
    """The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Source of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')


class EnableEmManagedExternalDatabaseInsightDetails(OpsiBaseModel):
    """The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')


class EnableEmManagedExternalExadataInsightDetails(OpsiBaseModel):
    """The information about the Exadata system to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableExadataInsightDetails.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')


class EnableEmManagedExternalHostInsightDetails(OpsiBaseModel):
    """The information about the EM-managed external host to be analyzed."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableHostInsightDetails.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')


class EnableExadataInsightDetails(OpsiRequestModel):
    """The information about the Exadata system to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Source of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')


class EnableExternalMysqlDatabaseInsightDetails(OpsiBaseModel):
    """MySQL support within the OCI Ops Insights service has been deprecated as of January 29, 2026. The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    database_connector_id: str = Field(..., alias='databaseConnectorId', description='The DBM owned database connector OCID mapping to the database credentials and connection details.')


class EnableHostInsightDetails(OpsiRequestModel):
    """The information about the host to be analyzed."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Source of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')


class EnableMacsManagedAutonomousDatabaseInsightDetails(OpsiBaseModel):
    """The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    compartment_id: str = Field(..., alias='compartmentId', description='The compartment OCID of the Autonomous Database.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    connection_details: ConnectionDetails = Field(..., alias='connectionDetails', description='The connection_details field of EnableMacsManagedAutonomousDatabaseInsightDetails.')
    connection_credential_details: CredentialDetails = Field(..., alias='connectionCredentialDetails', description='The connection_credential_details field of EnableMacsManagedAutonomousDatabaseInsightDetails.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')


class EnableMacsManagedCloudDatabaseInsightDetails(OpsiBaseModel):
    """The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    compartment_id: str = Field(..., alias='compartmentId', description='The compartment OCID of the External Database.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    connection_details: ConnectionDetails = Field(..., alias='connectionDetails', description='The connection_details field of EnableMacsManagedCloudDatabaseInsightDetails.')
    connection_credential_details: CredentialDetails = Field(..., alias='connectionCredentialDetails', description='The connection_credential_details field of EnableMacsManagedCloudDatabaseInsightDetails.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')


class EnableMacsManagedCloudExadataInsightDetails(OpsiBaseModel):
    """The information about the Exadata system to be analyzed. (ExaCC)."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableExadataInsightDetails.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')


class EnableMacsManagedCloudHostInsightDetails(OpsiBaseModel):
    """The information about the MACS-managed external host to be analyzed."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableHostInsightDetails.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')


class EnableMacsManagedExternalHostInsightDetails(OpsiBaseModel):
    """The information about the MACS-managed external host to be analyzed."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableHostInsightDetails.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')


class EnableMdsMySqlDatabaseInsightDetails(OpsiBaseModel):
    """MySQL support within the OCI Ops Insights service has been deprecated as of January 29, 2026. The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')


class EnablePeComanagedDatabaseInsightDetails(OpsiBaseModel):
    """The information about database to be analyzed."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    compartment_id: str = Field(..., alias='compartmentId', description='The compartment OCID of the Private service accessed database.')
    opsi_private_endpoint_id: str = Field(..., alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    service_name: str = Field(..., alias='serviceName', description='Database service name used for connection requests.')
    credential_details: CredentialDetails = Field(..., alias='credentialDetails', description='The credential_details field of EnablePeComanagedDatabaseInsightDetails.')
    connection_details: PeComanagedDatabaseConnectionDetails | None = Field(None, alias='connectionDetails', description='The connection_details field of EnablePeComanagedDatabaseInsightDetails.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')


class EnablePeComanagedExadataInsightDetails(OpsiBaseModel):
    """The information about the Exadata system to be analyzed. (ExaCS)."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Gets the entity_source of this EnableExadataInsightDetails.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')


class EnablePlanExadataInsightDetails(OpsiRequestModel):
    """The information about the chargeback plan to be enabled."""

    plan_id: str = Field(..., alias='planId', description='OCID of OPSI Chargeback plan resource.')


class EnterpriseManagerBridge(OpsiBaseModel):
    """Enterprise Manager bridge resource."""

    id: str = Field(..., alias='id', description='Enterprise Manager bridge identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Compartment identifier of the Enterprise Manager bridge')
    display_name: str = Field(..., alias='displayName', description='User-friedly name of Enterprise Manager Bridge that does not have to be unique.')
    description: str | None = Field(None, alias='description', description='Description of Enterprise Manager Bridge')
    object_storage_namespace_name: str = Field(..., alias='objectStorageNamespaceName', description='Object Storage Namespace Name')
    object_storage_bucket_name: str = Field(..., alias='objectStorageBucketName', description='Object Storage Bucket Name')
    object_storage_bucket_status_details: str | None = Field(None, alias='objectStorageBucketStatusDetails', description='A message describing status of the object storage bucket of this resource. For example, it can be used to provide actionable information about the permission and content validity of the bucket.')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='The time the the Enterprise Manager bridge was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time the Enterprise Manager bridge was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='The current state of the Enterprise Manager bridge.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')


class EnterpriseManagerBridgeCollection(OpsiBaseModel):
    """Collection of Enterprose Manager bridge summary objects."""

    items: list[EnterpriseManagerBridgeSummary] = Field(..., alias='items', description='Array of Enterprose Manager bridge summary objects.')


class EnterpriseManagerBridgeSummary(OpsiBaseModel):
    """Summary of a Enterprise Manager bridge resource."""

    id: str = Field(..., alias='id', description='Enterprise Manager bridge identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Compartment identifier of the Enterprise Manager bridge')
    display_name: str = Field(..., alias='displayName', description='User-friedly name of Enterprise Manager Bridge that does not have to be unique.')
    object_storage_namespace_name: str = Field(..., alias='objectStorageNamespaceName', description='Object Storage Namespace Name')
    object_storage_bucket_name: str = Field(..., alias='objectStorageBucketName', description='Object Storage Bucket Name')
    object_storage_bucket_status_details: str | None = Field(None, alias='objectStorageBucketStatusDetails', description='A message describing status of the object storage bucket of this resource. For example, it can be used to provide actionable information about the permission and content validity of the bucket.')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='The time the the Enterprise Manager bridge was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time the Enterprise Manager bridge was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='The current state of the Enterprise Manager bridge.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')


class EnterpriseManagerBridges(OpsiBaseModel):
    """Logical grouping used for Ops Insights Enterprise Manager Bridge operations."""

    enterprise_manager_bridges: Any | None = Field(None, alias='enterpriseManagerBridges', description='Enterprise Manager Bridge Object.')


class ExadataAsmEntity(OpsiBaseModel):
    """ASM entitie for an exadata."""

    metric_name: Literal['DB_EXTERNAL_PROPERTIES', 'DB_EXTERNAL_INSTANCE', 'DB_OS_CONFIG_INSTANCE', 'DB_PARAMETERS', 'DB_CONNECTION_STATUS', 'HOST_RESOURCE_ALLOCATION', 'ASM_ENTITY', 'EXADATA_CELL_CONFIG'] = Field(..., alias='metricName', description='Gets the metric_name of this DatabaseConfigurationMetricGroup.\nName of the metric group.\n\nAllowed values for this property are: "DB_EXTERNAL_PROPERTIES", "DB_EXTERNAL_INSTANCE", "DB_OS_CONFIG_INSTANCE", "DB_PARAMETERS", "DB_CONNECTION_STATUS", "HOST_RESOURCE_ALLOCATION", "ASM_ENTITY", "EXADATA_CELL_CONFIG"')
    time_collected: datetime | None = Field(None, alias='timeCollected', description='Gets the time_collected of this DatabaseConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    instance_name: str | None = Field(None, alias='instanceName', description='Instance name of ASM')
    cluster_name: str | None = Field(None, alias='clusterName', description='Cluster name of ASM')
    software_version: str | None = Field(None, alias='softwareVersion', description='Software version')


class ExadataCellConfig(OpsiBaseModel):
    """Storage server configuration."""

    metric_name: Literal['DB_EXTERNAL_PROPERTIES', 'DB_EXTERNAL_INSTANCE', 'DB_OS_CONFIG_INSTANCE', 'DB_PARAMETERS', 'DB_CONNECTION_STATUS', 'HOST_RESOURCE_ALLOCATION', 'ASM_ENTITY', 'EXADATA_CELL_CONFIG'] = Field(..., alias='metricName', description='Gets the metric_name of this DatabaseConfigurationMetricGroup.\nName of the metric group.\n\nAllowed values for this property are: "DB_EXTERNAL_PROPERTIES", "DB_EXTERNAL_INSTANCE", "DB_OS_CONFIG_INSTANCE", "DB_PARAMETERS", "DB_CONNECTION_STATUS", "HOST_RESOURCE_ALLOCATION", "ASM_ENTITY", "EXADATA_CELL_CONFIG"')
    time_collected: datetime | None = Field(None, alias='timeCollected', description='Gets the time_collected of this DatabaseConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    cell_name: str | None = Field(None, alias='cellName', description='Cell name')
    cell_hash: str | None = Field(None, alias='cellHash', description='Cell hash')
    cell_properties: str | None = Field(None, alias='cellProperties', description='Cell properties')
    cell_configs: str | None = Field(None, alias='cellConfigs', description='Cell configs')
    disk_counts: str | None = Field(None, alias='diskCounts', description='Cell disk counts')


class ExadataConfigurationCollection(OpsiBaseModel):
    """Collection of exadata insight configuration summary objects."""

    items: list[ExadataConfigurationSummary] = Field(..., alias='items', description='Array of exadata insight configurations summary objects.')


class ExadataConfigurationSummary(OpsiBaseModel):
    """Summary of a exadata configuration for a resource."""

    exadata_insight_id: str = Field(..., alias='exadataInsightId', description='The OCID of the Exadata insight.')
    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Source of the exadata entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    exadata_name: str = Field(..., alias='exadataName', description='The Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str = Field(..., alias='exadataDisplayName', description='The user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataType', description='Operations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataRackType', description='Exadata rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    vmcluster_details: list[VmClusterSummary] | None = Field(None, alias='vmclusterDetails', description='Array of objects containing VM cluster information.')
    exadata_shape: str = Field(..., alias='exadataShape', description='The shape of the Exadata Infrastructure.')
    chargeback_plan_details: ChargebackPlanDetails = Field(..., alias='chargebackPlanDetails', description='The chargeback_plan_details field of ExadataConfigurationSummary.')


class ExadataDatabaseMachineConfigurationSummary(OpsiBaseModel):
    """Configuration summary of a database machine."""

    exadata_insight_id: str = Field(..., alias='exadataInsightId', description='Gets the exadata_insight_id of this ExadataConfigurationSummary. The OCID of the Exadata insight.')
    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this ExadataConfigurationSummary.\nSource of the exadata entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this ExadataConfigurationSummary. The OCID of the compartment.')
    exadata_name: str = Field(..., alias='exadataName', description='Gets the exadata_name of this ExadataConfigurationSummary.\nThe Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str = Field(..., alias='exadataDisplayName', description='Gets the exadata_display_name of this ExadataConfigurationSummary.\nThe user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataType', description='Gets the exadata_type of this ExadataConfigurationSummary.\nOperations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataRackType', description='Gets the exadata_rack_type of this ExadataConfigurationSummary.\nExadata rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this ExadataConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this ExadataConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    vmcluster_details: list[VmClusterSummary] | None = Field(None, alias='vmclusterDetails', description='Gets the vmcluster_details of this ExadataConfigurationSummary.\nArray of objects containing VM cluster information.')
    exadata_shape: str = Field(..., alias='exadataShape', description='Gets the exadata_shape of this ExadataConfigurationSummary.\nThe shape of the Exadata Infrastructure.')
    chargeback_plan_details: ChargebackPlanDetails = Field(..., alias='chargebackPlanDetails', description='Gets the chargeback_plan_details of this ExadataConfigurationSummary.')
    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_bridge_id: str = Field(..., alias='enterpriseManagerBridgeId', description='OPSI Enterprise Manager Bridge OCID')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    enterprise_manager_console_url: str = Field(..., alias='enterpriseManagerConsoleUrl', description='Enterprise Manager Console Url')
    enterprise_manager_oms_ver: str = Field(..., alias='enterpriseManagerOmsVer', description='Enterprise Manager OMS Version')
    enterprise_manager_entity_type: str = Field(..., alias='enterpriseManagerEntityType', description='Enterprise Manager Entity Type')
    parent_id: str | None = Field(None, alias='parentId', description='The OCID of the database.')
    region: str | None = Field(None, alias='region', description='The region the resource resides in.')


class ExadataDatabaseStatisticsSummary(OpsiBaseModel):
    """Database details and statistics."""

    exadata_resource_type: Literal['DATABASE', 'HOST', 'STORAGE_SERVER', 'DISKGROUP', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceType', description='Gets the exadata_resource_type of this ExadataInsightResourceStatisticsAggregation.\nDefines the resource type for an exadata  (example: DATABASE, STORAGE_SERVER, HOST, DISKGROUP)\n\nAllowed values for this property are: "DATABASE", "HOST", "STORAGE_SERVER", "DISKGROUP", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    resource_details: DatabaseDetails = Field(..., alias='resourceDetails', description='The resource_details field of ExadataDatabaseStatisticsSummary.')
    current_statistics: ExadataInsightResourceStatistics = Field(..., alias='currentStatistics', description='The current_statistics field of ExadataDatabaseStatisticsSummary.')


class ExadataDetails(OpsiBaseModel):
    """Partial information about the exadata which includes id, name and vmclusterNames."""

    id: str = Field(..., alias='id', description='The OCID of exadata insight resource.')
    name: str = Field(..., alias='name', description='Name of exadata insight resource.')
    vmcluster_names: list[str] | None = Field(None, alias='vmclusterNames', description='Array of vm cluster names. Applicable for ExaCC and ExaCS.')


class ExadataDiskgroupStatisticsSummary(OpsiBaseModel):
    """Diskgroup details and statistics."""

    exadata_resource_type: Literal['DATABASE', 'HOST', 'STORAGE_SERVER', 'DISKGROUP', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceType', description='Gets the exadata_resource_type of this ExadataInsightResourceStatisticsAggregation.\nDefines the resource type for an exadata  (example: DATABASE, STORAGE_SERVER, HOST, DISKGROUP)\n\nAllowed values for this property are: "DATABASE", "HOST", "STORAGE_SERVER", "DISKGROUP", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    resource_details: DiskGroupDetails = Field(..., alias='resourceDetails', description='The resource_details field of ExadataDiskgroupStatisticsSummary.')
    current_statistics: ExadataInsightResourceStatistics = Field(..., alias='currentStatistics', description='The current_statistics field of ExadataDiskgroupStatisticsSummary.')


class ExadataExaccConfigurationSummary(OpsiBaseModel):
    """Configuration summary of a macs managed Exacc exadata machine."""

    exadata_insight_id: str = Field(..., alias='exadataInsightId', description='Gets the exadata_insight_id of this ExadataConfigurationSummary. The OCID of the Exadata insight.')
    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this ExadataConfigurationSummary.\nSource of the exadata entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this ExadataConfigurationSummary. The OCID of the compartment.')
    exadata_name: str = Field(..., alias='exadataName', description='Gets the exadata_name of this ExadataConfigurationSummary.\nThe Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str = Field(..., alias='exadataDisplayName', description='Gets the exadata_display_name of this ExadataConfigurationSummary.\nThe user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataType', description='Gets the exadata_type of this ExadataConfigurationSummary.\nOperations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataRackType', description='Gets the exadata_rack_type of this ExadataConfigurationSummary.\nExadata rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this ExadataConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this ExadataConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    vmcluster_details: list[VmClusterSummary] | None = Field(None, alias='vmclusterDetails', description='Gets the vmcluster_details of this ExadataConfigurationSummary.\nArray of objects containing VM cluster information.')
    exadata_shape: str = Field(..., alias='exadataShape', description='Gets the exadata_shape of this ExadataConfigurationSummary.\nThe shape of the Exadata Infrastructure.')
    chargeback_plan_details: ChargebackPlanDetails = Field(..., alias='chargebackPlanDetails', description='Gets the chargeback_plan_details of this ExadataConfigurationSummary.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    parent_id: str = Field(..., alias='parentId', description='The OCID of the database.')


class ExadataExacsConfigurationSummary(OpsiBaseModel):
    """Configuration summary of a Exacs exadata machine."""

    exadata_insight_id: str = Field(..., alias='exadataInsightId', description='Gets the exadata_insight_id of this ExadataConfigurationSummary. The OCID of the Exadata insight.')
    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this ExadataConfigurationSummary.\nSource of the exadata entity.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this ExadataConfigurationSummary. The OCID of the compartment.')
    exadata_name: str = Field(..., alias='exadataName', description='Gets the exadata_name of this ExadataConfigurationSummary.\nThe Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str = Field(..., alias='exadataDisplayName', description='Gets the exadata_display_name of this ExadataConfigurationSummary.\nThe user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataType', description='Gets the exadata_type of this ExadataConfigurationSummary.\nOperations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataRackType', description='Gets the exadata_rack_type of this ExadataConfigurationSummary.\nExadata rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this ExadataConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this ExadataConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    vmcluster_details: list[VmClusterSummary] | None = Field(None, alias='vmclusterDetails', description='Gets the vmcluster_details of this ExadataConfigurationSummary.\nArray of objects containing VM cluster information.')
    exadata_shape: str = Field(..., alias='exadataShape', description='Gets the exadata_shape of this ExadataConfigurationSummary.\nThe shape of the Exadata Infrastructure.')
    chargeback_plan_details: ChargebackPlanDetails = Field(..., alias='chargebackPlanDetails', description='Gets the chargeback_plan_details of this ExadataConfigurationSummary.')
    opsi_private_endpoint_id: str = Field(..., alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    parent_id: str = Field(..., alias='parentId', description='The OCID of the database.')


class ExadataHostStatisticsSummary(OpsiBaseModel):
    """Host details and statistics."""

    exadata_resource_type: Literal['DATABASE', 'HOST', 'STORAGE_SERVER', 'DISKGROUP', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceType', description='Gets the exadata_resource_type of this ExadataInsightResourceStatisticsAggregation.\nDefines the resource type for an exadata  (example: DATABASE, STORAGE_SERVER, HOST, DISKGROUP)\n\nAllowed values for this property are: "DATABASE", "HOST", "STORAGE_SERVER", "DISKGROUP", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    resource_details: HostDetails = Field(..., alias='resourceDetails', description='The resource_details field of ExadataHostStatisticsSummary.')
    current_statistics: ExadataInsightResourceStatistics = Field(..., alias='currentStatistics', description='The current_statistics field of ExadataHostStatisticsSummary.')


class ExadataInsight(OpsiBaseModel):
    """Exadata insight resource."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Source of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Exadata insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Compartment identifier of the Exadata insight resource')
    exadata_name: str = Field(..., alias='exadataName', description='The Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str | None = Field(None, alias='exadataDisplayName', description='The user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataType', description='Operations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataRackType', description='Exadata rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    is_virtualized_exadata: bool | None = Field(None, alias='isVirtualizedExadata', description='true if virtualization is used in the Exadata system')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Indicates the status of an Exadata insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    chargeback_plan_details: ChargebackPlanDetails | None = Field(None, alias='chargebackPlanDetails', description='The chargeback_plan_details field of ExadataInsight.')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='The time the the Exadata insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time the Exadata insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='The current state of the Exadata insight.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    status_details: str | None = Field(None, alias='statusDetails', description='A message describing the status of the Exadata Resource. For example, it can be used to provide actionable information about the policies needed to access the Exadata Resource.')


class ExadataInsightResourceCapacityTrendAggregation(OpsiBaseModel):
    """Resource Capacity samples."""

    end_timestamp: datetime = Field(..., alias='endTimestamp', description='The timestamp in which the current sampling period ends in RFC 3339 format.')
    capacity: float = Field(..., alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    total_host_capacity: float | None = Field(None, alias='totalHostCapacity', description='The maximum host CPUs (cores x threads/core) on the underlying infrastructure. This only applies to CPU and does not not apply for Autonomous Databases.')


class ExadataInsightResourceCapacityTrendSummary(OpsiBaseModel):
    """List of resource id, name, capacity time series data."""

    id: str = Field(..., alias='id', description='The OCID of the database insight resource.')
    name: str = Field(..., alias='name', description='The name of the resource.')
    capacity_data: list[ExadataInsightResourceCapacityTrendAggregation] = Field(..., alias='capacityData', description='Time series data for capacity')


class ExadataInsightResourceForecastTrendSummary(OpsiBaseModel):
    """List of resource id, name, capacity insight value, pattern, historical usage and projected data."""

    id: str = Field(..., alias='id', description='The OCID of the database insight resource.')
    name: str = Field(..., alias='name', description='The name of the resource.')
    days_to_reach_capacity: int = Field(..., alias='daysToReachCapacity', description='Days to reach capacity for a storage server')
    selected_forecast_algorithm: str | None = Field(None, alias='selectedForecastAlgorithm', description='Auto-ML algorithm leveraged for the forecast. Only applicable for Auto-ML forecast.')
    pattern: Literal['LINEAR', 'MONTHLY_SEASONS', 'MONTHLY_AND_YEARLY_SEASONS', 'WEEKLY_SEASONS', 'WEEKLY_AND_MONTHLY_SEASONS', 'WEEKLY_MONTHLY_AND_YEARLY_SEASONS', 'WEEKLY_AND_YEARLY_SEASONS', 'YEARLY_SEASONS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='pattern', description='Time series patterns used in the forecasting.\n\nAllowed values for this property are: "LINEAR", "MONTHLY_SEASONS", "MONTHLY_AND_YEARLY_SEASONS", "WEEKLY_SEASONS", "WEEKLY_AND_MONTHLY_SEASONS", "WEEKLY_MONTHLY_AND_YEARLY_SEASONS", "WEEKLY_AND_YEARLY_SEASONS", "YEARLY_SEASONS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    historical_data: list[HistoricalDataItem] = Field(..., alias='historicalData', description='Time series data used for the forecast analysis.')
    projected_data: list[ProjectedDataItem] = Field(..., alias='projectedData', description='Time series data result of the forecasting analysis.')


class ExadataInsightResourceInsightUtilizationItem(OpsiBaseModel):
    """Object containing current utilization, projected utilization, id and daysToReach high and low utilization value."""

    exadata_insight_id: str = Field(..., alias='exadataInsightId', description='The OCID of the Exadata insight.')
    exadata_display_name: str | None = Field(None, alias='exadataDisplayName', description='The user-friendly name for the Exadata system. The name does not have to be unique.')
    current_utilization: float = Field(..., alias='currentUtilization', description='Current utilization')
    projected_utilization: float = Field(..., alias='projectedUtilization', description='Projected utilization')
    days_to_reach_high_utilization: int = Field(..., alias='daysToReachHighUtilization', description='Days to reach projected high utilization')
    days_to_reach_low_utilization: int = Field(..., alias='daysToReachLowUtilization', description='Days to reach projected low utilization')


class ExadataInsightResourceStatistics(OpsiBaseModel):
    """Contains resource statistics with usage unit."""

    usage: float = Field(..., alias='usage', description='Total amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    total_host_capacity: float | None = Field(None, alias='totalHostCapacity', description='The maximum host CPUs (cores x threads/core) on the underlying infrastructure. This only applies to CPU and does not not apply for Autonomous Databases.')
    utilization_percent: float = Field(..., alias='utilizationPercent', description='Resource utilization in percentage')
    usage_change_percent: float = Field(..., alias='usageChangePercent', description='Change in resource utilization in percentage')
    instance_metrics: list[InstanceMetrics] | None = Field(None, alias='instanceMetrics', description='Array of instance metrics')


class ExadataInsightResourceStatisticsAggregation(OpsiBaseModel):
    """Contains resource details and current statistics."""

    exadata_resource_type: Literal['DATABASE', 'HOST', 'STORAGE_SERVER', 'DISKGROUP', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceType', description='Defines the resource type for an exadata  (example: DATABASE, STORAGE_SERVER, HOST, DISKGROUP)\n\nAllowed values for this property are: "DATABASE", "HOST", "STORAGE_SERVER", "DISKGROUP", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class ExadataInsightSummary(OpsiBaseModel):
    """Summary of an Exadata insight resource."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Source of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='The OCID of the Exadata insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    exadata_name: str = Field(..., alias='exadataName', description='The Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str | None = Field(None, alias='exadataDisplayName', description='The user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataType', description='Operations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataRackType', description='Operations Insights internal representation of the the Exadata system rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Indicates the status of an Exadata insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    chargeback_plan_details: ChargebackPlanDetails | None = Field(None, alias='chargebackPlanDetails', description='The chargeback_plan_details field of ExadataInsightSummary.')
    time_created: datetime = Field(..., alias='timeCreated', description='The time the the Exadata insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time the Exadata insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='The current state of the Exadata insight.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    status_details: str | None = Field(None, alias='statusDetails', description='A message describing the status of the Exadata Resource. For example, it can be used to provide actionable information about the policies needed to access the Exadata Resource.')


class ExadataInsightSummaryCollection(OpsiBaseModel):
    """Collection of Exadata insight summary objects."""

    items: list[ExadataInsightSummary] = Field(..., alias='items', description='Array of Exadata insight summary objects.')


class ExadataInsights(OpsiBaseModel):
    """Logical grouping used for Operations Insights Exadata related operations."""

    exadata_insights: Any | None = Field(None, alias='exadataInsights', description='Exadata Insights Object.')


class ExadataInsightsDataObject(OpsiBaseModel):
    """Exadata insights data object."""

    identifier: str = Field(..., alias='identifier', description='Gets the identifier of this OpsiDataObject.\nUnique identifier of OPSI data object.')
    data_object_type: Literal['DATABASE_INSIGHTS_DATA_OBJECT', 'HOST_INSIGHTS_DATA_OBJECT', 'EXADATA_INSIGHTS_DATA_OBJECT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='dataObjectType', description='Gets the data_object_type of this OpsiDataObject.\nType of OPSI data object.\n\nAllowed values for this property are: "DATABASE_INSIGHTS_DATA_OBJECT", "HOST_INSIGHTS_DATA_OBJECT", "EXADATA_INSIGHTS_DATA_OBJECT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str = Field(..., alias='displayName', description='Gets the display_name of this OpsiDataObject.\nUser-friendly name of OPSI data object.')
    description: str | None = Field(None, alias='description', description='Gets the description of this OpsiDataObject.\nDescription of OPSI data object.')
    name: str | None = Field(None, alias='name', description='Gets the name of this OpsiDataObject.\nName of the data object, which can be used in data object queries just like how view names are used in a query.')
    group_names: list[str] | None = Field(None, alias='groupNames', description='Gets the group_names of this OpsiDataObject.\nNames of all the groups to which the data object belongs to.')
    supported_query_time_period: str | None = Field(None, alias='supportedQueryTimePeriod', description='Gets the supported_query_time_period of this OpsiDataObject.\nTime period supported by the data object for quering data.\nTime period is in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D.\nExamples: P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months).')
    columns_metadata: list[DataObjectColumnMetadata] = Field(..., alias='columnsMetadata', description='Gets the columns_metadata of this OpsiDataObject.\nMetadata of columns in a data object.')
    supported_query_params: list[OpsiDataObjectSupportedQueryParam] | None = Field(None, alias='supportedQueryParams', description='Gets the supported_query_params of this OpsiDataObject.\nSupported query parameters by this OPSI data object that can be configured while a data object query involving this data object is executed.')


class ExadataInsightsDataObjectSummary(OpsiBaseModel):
    """Summary of an exadata insights data object."""

    identifier: str = Field(..., alias='identifier', description='Gets the identifier of this OpsiDataObjectSummary.\nUnique identifier of OPSI data object.')
    data_object_type: Literal['DATABASE_INSIGHTS_DATA_OBJECT', 'HOST_INSIGHTS_DATA_OBJECT', 'EXADATA_INSIGHTS_DATA_OBJECT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='dataObjectType', description='Gets the data_object_type of this OpsiDataObjectSummary.\nType of OPSI data object.\n\nAllowed values for this property are: "DATABASE_INSIGHTS_DATA_OBJECT", "HOST_INSIGHTS_DATA_OBJECT", "EXADATA_INSIGHTS_DATA_OBJECT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str = Field(..., alias='displayName', description='Gets the display_name of this OpsiDataObjectSummary.\nUser-friendly name of OPSI data object.')
    description: str | None = Field(None, alias='description', description='Gets the description of this OpsiDataObjectSummary.\nDescription of OPSI data object.')
    name: str | None = Field(None, alias='name', description='Gets the name of this OpsiDataObjectSummary.\nName of the data object, which can be used in data object queries just like how view names are used in a query.')
    group_names: list[str] | None = Field(None, alias='groupNames', description='Gets the group_names of this OpsiDataObjectSummary.\nNames of all the groups to which the data object belongs to.')


class ExadataMemberCollection(OpsiBaseModel):
    """Partial definition of the exadata insight resource."""

    exadata_insight_id: str = Field(..., alias='exadataInsightId', description='The OCID of the Exadata insight.')
    exadata_name: str = Field(..., alias='exadataName', description='The Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str = Field(..., alias='exadataDisplayName', description='The user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataType', description='Operations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataRackType', description='Exadata rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[ExadataMemberSummary] = Field(..., alias='items', description='Collection of Exadata members')


class ExadataMemberSummary(OpsiBaseModel):
    """Lists name, display name and type of exadata member."""

    name: str = Field(..., alias='name', description='Name of exadata member target')
    display_name: str = Field(..., alias='displayName', description='Display Name of exadata member target')
    entity_type: Literal['DATABASE', 'ILOM_SERVER', 'PDU', 'STORAGE_SERVER', 'CLUSTER_ASM', 'INFINIBAND_SWITCH', 'ETHERNET_SWITCH', 'HOST', 'VM_CLUSTER', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entityType', description='Entity type of exadata member target\n\nAllowed values for this property are: "DATABASE", "ILOM_SERVER", "PDU", "STORAGE_SERVER", "CLUSTER_ASM", "INFINIBAND_SWITCH", "ETHERNET_SWITCH", "HOST", "VM_CLUSTER", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class ExadataStorageServerStatisticsSummary(OpsiBaseModel):
    """Storage server details and statistics."""

    exadata_resource_type: Literal['DATABASE', 'HOST', 'STORAGE_SERVER', 'DISKGROUP', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceType', description='Gets the exadata_resource_type of this ExadataInsightResourceStatisticsAggregation.\nDefines the resource type for an exadata  (example: DATABASE, STORAGE_SERVER, HOST, DISKGROUP)\n\nAllowed values for this property are: "DATABASE", "HOST", "STORAGE_SERVER", "DISKGROUP", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    resource_details: StorageServerDetails = Field(..., alias='resourceDetails', description='The resource_details field of ExadataStorageServerStatisticsSummary.')
    current_statistics: ExadataInsightResourceStatistics = Field(..., alias='currentStatistics', description='The current_statistics field of ExadataStorageServerStatisticsSummary.')


class ExternalMysqlDatabaseConfigurationSummary(OpsiBaseModel):
    """Configuration Summary of a External MySQL database."""

    database_insight_id: str = Field(..., alias='databaseInsightId', description='Gets the database_insight_id of this DatabaseConfigurationSummary. The OCID of the database insight resource.')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseConfigurationSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseConfigurationSummary. The OCID of the compartment.')
    database_name: str = Field(..., alias='databaseName', description='Gets the database_name of this DatabaseConfigurationSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str = Field(..., alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseConfigurationSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str = Field(..., alias='databaseType', description='Gets the database_type of this DatabaseConfigurationSummary.\nOps Insights internal representation of the database type.')
    database_version: str = Field(..., alias='databaseVersion', description='Gets the database_version of this DatabaseConfigurationSummary.\nThe version of the database.')
    is_advanced_features_enabled: bool = Field(..., alias='isAdvancedFeaturesEnabled', description='Gets the is_advanced_features_enabled of this DatabaseConfigurationSummary.\nFlag is to identify if advanced features for autonomous database is enabled or not')
    cdb_name: str = Field(..., alias='cdbName', description='Gets the cdb_name of this DatabaseConfigurationSummary.\nName of the CDB.Only applies to PDB.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseConfigurationSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    agent_id: str = Field(..., alias='agentId', description='The OCID of the Management Agent.')
    database_connector_id: str = Field(..., alias='databaseConnectorId', description='The DBM owned database connector OCID mapping to the database credentials and connection details.')


class ExternalMysqlDatabaseInsight(OpsiBaseModel):
    """MySQL support within the OCI Ops Insights service has been deprecated as of January 29, 2026. Database insight resource."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsight.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsight.\nDatabase insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseInsight.\nCompartment identifier of the database')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this DatabaseInsight.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsight.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsight.\nThe version of the database.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this DatabaseInsight.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsight.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsight.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsight.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    database_name: str = Field(..., alias='databaseName', description='Name of database')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Display name of database')


class ExternalMysqlDatabaseInsightSummary(OpsiBaseModel):
    """MySQL support within the OCI Ops Insights service has been deprecated as of January 29, 2026. Summary of a database insight resource."""

    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsightSummary. The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='Gets the database_id of this DatabaseInsightSummary. The OCID of the database.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='Gets the compartment_id of this DatabaseInsightSummary. The OCID of the compartment.')
    database_name: str | None = Field(None, alias='databaseName', description='Gets the database_name of this DatabaseInsightSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseInsightSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsightSummary.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsightSummary.\nThe version of the database.')
    database_host_names: list[str] | None = Field(None, alias='databaseHostNames', description='Gets the database_host_names of this DatabaseInsightSummary.\nThe hostnames for the database.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this DatabaseInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsightSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this DatabaseInsightSummary.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this DatabaseInsightSummary.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsightSummary.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsightSummary.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsightSummary.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    agent_id: str = Field(..., alias='agentId', description='The OCID of the Management Agent.')
    database_resource_type: str | None = Field(None, alias='databaseResourceType', description='OCI database resource type')
    database_connector_id: str | None = Field(None, alias='databaseConnectorId', description='The DBM owned database connector OCID mapping to the database credentials and connection details.')


class HistoricalDataItem(OpsiBaseModel):
    """The historical timestamp and the corresponding resource value."""

    end_timestamp: datetime = Field(..., alias='endTimestamp', description='The timestamp in which the current sampling period ends in RFC 3339 format.')
    usage: float = Field(..., alias='usage', description='Total amount used of the resource metric type (CPU, STORAGE).')


class HostAllocation(OpsiBaseModel):
    """Resource Allocation metric for the host."""

    metric_name: Literal['DB_EXTERNAL_PROPERTIES', 'DB_EXTERNAL_INSTANCE', 'DB_OS_CONFIG_INSTANCE', 'DB_PARAMETERS', 'DB_CONNECTION_STATUS', 'HOST_RESOURCE_ALLOCATION', 'ASM_ENTITY', 'EXADATA_CELL_CONFIG'] = Field(..., alias='metricName', description='Gets the metric_name of this DatabaseConfigurationMetricGroup.\nName of the metric group.\n\nAllowed values for this property are: "DB_EXTERNAL_PROPERTIES", "DB_EXTERNAL_INSTANCE", "DB_OS_CONFIG_INSTANCE", "DB_PARAMETERS", "DB_CONNECTION_STATUS", "HOST_RESOURCE_ALLOCATION", "ASM_ENTITY", "EXADATA_CELL_CONFIG"')
    time_collected: datetime | None = Field(None, alias='timeCollected', description='Gets the time_collected of this DatabaseConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    resource_name: str | None = Field(None, alias='resourceName', description='Name of the host resource')
    resource_value: int | None = Field(None, alias='resourceValue', description='Value of the host resource')


class HostConfigurationCollection(OpsiBaseModel):
    """Collection of host insight configuration summary objects."""

    items: list[HostConfigurationSummary] = Field(..., alias='items', description='Array of host insight configurations summary objects.')


class HostConfigurationMetricGroup(OpsiBaseModel):
    """Base Metric Group for Host configuration metrics."""

    metric_name: Literal['HOST_PRODUCT', 'HOST_RESOURCE_ALLOCATION', 'HOST_MEMORY_CONFIGURATION', 'HOST_HARDWARE_CONFIGURATION', 'HOST_CPU_HARDWARE_CONFIGURATION', 'HOST_NETWORK_CONFIGURATION', 'HOST_ENTITES', 'HOST_FILESYSTEM_CONFIGURATION', 'HOST_GPU_CONFIGURATION', 'HOST_CONTAINERS'] = Field(..., alias='metricName', description='Name of the metric group\n\nAllowed values for this property are: "HOST_PRODUCT", "HOST_RESOURCE_ALLOCATION", "HOST_MEMORY_CONFIGURATION", "HOST_HARDWARE_CONFIGURATION", "HOST_CPU_HARDWARE_CONFIGURATION", "HOST_NETWORK_CONFIGURATION", "HOST_ENTITES", "HOST_FILESYSTEM_CONFIGURATION", "HOST_GPU_CONFIGURATION", "HOST_CONTAINERS"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Collection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')


class HostConfigurationSummary(OpsiBaseModel):
    """Summary of a host configuration for a resource."""

    host_insight_id: str = Field(..., alias='hostInsightId', description='The OCID of the host insight resource.')
    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Source of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='The host name. The host name is unique amongst the hosts managed by the same management agent.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    platform_version: str | None = Field(None, alias='platformVersion', description='Platform version.')
    platform_vendor: str | None = Field(None, alias='platformVendor', description='Platform vendor.')
    total_cpus: int = Field(..., alias='totalCpus', description='Total CPU on this host.')
    total_memory_in_gbs: float = Field(..., alias='totalMemoryInGBs', description='Total amount of usable physical memory in gibabytes')
    cpu_architecture: str | None = Field(None, alias='cpuArchitecture', description='CPU architechure')
    cpu_cache_in_mbs: float = Field(..., alias='cpuCacheInMBs', description='Size of cache memory in megabytes.')
    cpu_vendor: str | None = Field(None, alias='cpuVendor', description='Name of the CPU vendor.')
    cpu_frequency_in_mhz: float = Field(..., alias='cpuFrequencyInMhz', description='Clock frequency of the processor in megahertz.')
    cpu_implementation: str | None = Field(None, alias='cpuImplementation', description='Model name of processor.')
    cores_per_socket: int = Field(..., alias='coresPerSocket', description='Number of cores per socket.')
    total_sockets: int = Field(..., alias='totalSockets', description='Number of total sockets.')
    threads_per_socket: int = Field(..., alias='threadsPerSocket', description='Number of threads per socket.')
    is_hyper_threading_enabled: bool = Field(..., alias='isHyperThreadingEnabled', description='Indicates if hyper-threading is enabled or not')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')


class HostContainers(OpsiBaseModel):
    """Host Containers details."""

    metric_name: Literal['HOST_PRODUCT', 'HOST_RESOURCE_ALLOCATION', 'HOST_MEMORY_CONFIGURATION', 'HOST_HARDWARE_CONFIGURATION', 'HOST_CPU_HARDWARE_CONFIGURATION', 'HOST_NETWORK_CONFIGURATION', 'HOST_ENTITES', 'HOST_FILESYSTEM_CONFIGURATION', 'HOST_GPU_CONFIGURATION', 'HOST_CONTAINERS'] = Field(..., alias='metricName', description='Gets the metric_name of this HostConfigurationMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_PRODUCT", "HOST_RESOURCE_ALLOCATION", "HOST_MEMORY_CONFIGURATION", "HOST_HARDWARE_CONFIGURATION", "HOST_CPU_HARDWARE_CONFIGURATION", "HOST_NETWORK_CONFIGURATION", "HOST_ENTITES", "HOST_FILESYSTEM_CONFIGURATION", "HOST_GPU_CONFIGURATION", "HOST_CONTAINERS"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    container_id: str | None = Field(None, alias='containerId', description='Container Id (full)')
    container_name: str | None = Field(None, alias='containerName', description='Container Name')
    container_image: str | None = Field(None, alias='containerImage', description='Container Image')
    container_image_tag: str | None = Field(None, alias='containerImageTag', description='Container Image Tag (version)')
    container_image_digest: str | None = Field(None, alias='containerImageDigest', description='Container Image Digest')
    container_ports: str | None = Field(None, alias='containerPorts', description='Container open ports')


class HostCpuHardwareConfiguration(OpsiBaseModel):
    """CPU Hardware Configuration metric for the host."""

    metric_name: Literal['HOST_PRODUCT', 'HOST_RESOURCE_ALLOCATION', 'HOST_MEMORY_CONFIGURATION', 'HOST_HARDWARE_CONFIGURATION', 'HOST_CPU_HARDWARE_CONFIGURATION', 'HOST_NETWORK_CONFIGURATION', 'HOST_ENTITES', 'HOST_FILESYSTEM_CONFIGURATION', 'HOST_GPU_CONFIGURATION', 'HOST_CONTAINERS'] = Field(..., alias='metricName', description='Gets the metric_name of this HostConfigurationMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_PRODUCT", "HOST_RESOURCE_ALLOCATION", "HOST_MEMORY_CONFIGURATION", "HOST_HARDWARE_CONFIGURATION", "HOST_CPU_HARDWARE_CONFIGURATION", "HOST_NETWORK_CONFIGURATION", "HOST_ENTITES", "HOST_FILESYSTEM_CONFIGURATION", "HOST_GPU_CONFIGURATION", "HOST_CONTAINERS"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    total_sockets: int | None = Field(None, alias='totalSockets', description='Total number of CPU Sockets')
    vendor_name: str | None = Field(None, alias='vendorName', description='Name of the CPU vendor')
    frequency_in_mhz: float | None = Field(None, alias='frequencyInMhz', description='Clock frequency of the processor in megahertz')
    cache_in_mb: float | None = Field(None, alias='cacheInMB', description='Size of cache memory in megabytes')
    cpu_implementation: str | None = Field(None, alias='cpuImplementation', description='Model name of processor')
    model: str | None = Field(None, alias='model', description='CPU model')
    cpu_family: str | None = Field(None, alias='cpuFamily', description='Type of processor in the system')
    cores_per_socket: int | None = Field(None, alias='coresPerSocket', description='Number of cores per socket')
    threads_per_socket: int | None = Field(None, alias='threadsPerSocket', description='Number of threads per socket')
    hyper_threading_enabled: str | None = Field(None, alias='hyperThreadingEnabled', description='Indicates if hyper-threading is enabled or not')


class HostCpuRecommendations(OpsiBaseModel):
    """Contains CPU recommendation."""

    metric_recommendation_name: Literal['HOST_CPU_RECOMMENDATIONS', 'HOST_MEMORY_RECOMMENDATIONS', 'HOST_NETWORK_RECOMMENDATIONS', 'HOST_STORAGE_RECOMMENDATIONS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='metricRecommendationName', description='Gets the metric_recommendation_name of this HostInsightHostRecommendations.\nName of recommendations depending of resource metric received.\n\nAllowed values for this property are: "HOST_CPU_RECOMMENDATIONS", "HOST_MEMORY_RECOMMENDATIONS", "HOST_NETWORK_RECOMMENDATIONS", "HOST_STORAGE_RECOMMENDATIONS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    burstable: Literal['BASELINE_1_8', 'BASELINE_1_2', 'NO_RECOMMENDATION', 'DISABLE_BURSTABLE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='burstable', description='Show if OPSI recommends to convert an instance to a burstable instance and show recommended cpu baseline if positive recommendation.\n\nAllowed values for this property are: "BASELINE_1_8", "BASELINE_1_2", "NO_RECOMMENDATION", "DISABLE_BURSTABLE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    shape: str | None = Field(None, alias='shape', description='Show if OPSI recommends to change the shape of an instance and show recommended shape based on CPU utilization.')
    unused_instance: Literal['IN_USE', 'NOT_IN_USE', 'IS_NOT_DETERMINED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='unusedInstance', description='Identify unused instances based on cpu, memory and network metrics.\n\nAllowed values for this property are: "IN_USE", "NOT_IN_USE", "IS_NOT_DETERMINED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    is_abandoned_instance: bool | None = Field(None, alias='isAbandonedInstance', description='Identify if an instance is abandoned.')


class HostCpuStatistics(OpsiBaseModel):
    """Contains CPU statistics."""

    usage: float = Field(..., alias='usage', description='Gets the usage of this HostResourceStatistics.\nTotal amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='Gets the capacity of this HostResourceStatistics.\nThe maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    utilization_percent: float = Field(..., alias='utilizationPercent', description='Gets the utilization_percent of this HostResourceStatistics.\nResource utilization in percentage.')
    usage_change_percent: float = Field(..., alias='usageChangePercent', description='Gets the usage_change_percent of this HostResourceStatistics.\nChange in resource utilization in percentage')
    resource_name: Literal['HOST_CPU_STATISTICS', 'HOST_MEMORY_STATISTICS', 'HOST_STORAGE_STATISTICS', 'HOST_NETWORK_STATISTICS', 'HOST_IO_STATISTICS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceName', description='Gets the resource_name of this HostResourceStatistics.\nName of resource for host\n\nAllowed values for this property are: "HOST_CPU_STATISTICS", "HOST_MEMORY_STATISTICS", "HOST_STORAGE_STATISTICS", "HOST_NETWORK_STATISTICS", "HOST_IO_STATISTICS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    cpu_baseline: float | None = Field(None, alias='cpuBaseline', description='The baseline utilization is a fraction of each CPU core expressed in percentages, either 12.5% or 50%. The baseline provides the minimum CPUs that can be used constantly.')
    load: SummaryStatistics | None = Field(None, alias='load', description='The load field of HostCpuStatistics.')


class HostCpuUsage(OpsiBaseModel):
    """CPU Usage metric for the host."""

    metric_name: Literal['HOST_CPU_USAGE', 'HOST_MEMORY_USAGE', 'HOST_NETWORK_ACTIVITY_SUMMARY', 'HOST_TOP_PROCESSES', 'HOST_FILESYSTEM_USAGE', 'HOST_GPU_USAGE', 'HOST_GPU_PROCESSES', 'HOST_IO_USAGE'] = Field(..., alias='metricName', description='Gets the metric_name of this HostPerformanceMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_CPU_USAGE", "HOST_MEMORY_USAGE", "HOST_NETWORK_ACTIVITY_SUMMARY", "HOST_TOP_PROCESSES", "HOST_FILESYSTEM_USAGE", "HOST_GPU_USAGE", "HOST_GPU_PROCESSES", "HOST_IO_USAGE"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostPerformanceMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    cpu_user_mode_in_percent: float | None = Field(None, alias='cpuUserModeInPercent', description='Percentage of CPU time spent in user mode')
    cpu_system_mode_in_percent: float | None = Field(None, alias='cpuSystemModeInPercent', description='Percentage of CPU time spent in system mode')
    cpu_usage_in_sec: float | None = Field(None, alias='cpuUsageInSec', description='Amount of CPU Time spent in seconds')
    cpu_utilization_in_percent: float | None = Field(None, alias='cpuUtilizationInPercent', description='Amount of CPU Time spent in percentage')
    cpu_stolen_in_percent: float | None = Field(None, alias='cpuStolenInPercent', description='Amount of CPU time stolen in percentage')
    cpu_idle_in_percent: float | None = Field(None, alias='cpuIdleInPercent', description='Amount of CPU idle time in percentage')
    cpu_load1min: float | None = Field(None, alias='cpuLoad1min', description='Load average in the last 1 minute')
    cpu_load5min: float | None = Field(None, alias='cpuLoad5min', description='Load average in the last 5 minutes')
    cpu_load15min: float | None = Field(None, alias='cpuLoad15min', description='Load average in the last 15 minutes')


class HostDetails(OpsiBaseModel):
    """Partial information about a host which includes id, name, type."""

    id: str = Field(..., alias='id', description='The OCID of the host.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='The host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='The user-friendly name for the host. The name does not have to be unique.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    agent_identifier: str = Field(..., alias='agentIdentifier', description='The identifier of the agent.')


class HostEntities(OpsiBaseModel):
    """Database entities running on the host."""

    metric_name: Literal['HOST_PRODUCT', 'HOST_RESOURCE_ALLOCATION', 'HOST_MEMORY_CONFIGURATION', 'HOST_HARDWARE_CONFIGURATION', 'HOST_CPU_HARDWARE_CONFIGURATION', 'HOST_NETWORK_CONFIGURATION', 'HOST_ENTITES', 'HOST_FILESYSTEM_CONFIGURATION', 'HOST_GPU_CONFIGURATION', 'HOST_CONTAINERS'] = Field(..., alias='metricName', description='Gets the metric_name of this HostConfigurationMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_PRODUCT", "HOST_RESOURCE_ALLOCATION", "HOST_MEMORY_CONFIGURATION", "HOST_HARDWARE_CONFIGURATION", "HOST_CPU_HARDWARE_CONFIGURATION", "HOST_NETWORK_CONFIGURATION", "HOST_ENTITES", "HOST_FILESYSTEM_CONFIGURATION", "HOST_GPU_CONFIGURATION", "HOST_CONTAINERS"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    entity_name: str = Field(..., alias='entityName', description='Name of the database entity')
    entity_type: str = Field(..., alias='entityType', description='Type of the database entity')


class HostFilesystemConfiguration(OpsiBaseModel):
    """Filesystem Configuration metric for the host."""

    metric_name: Literal['HOST_PRODUCT', 'HOST_RESOURCE_ALLOCATION', 'HOST_MEMORY_CONFIGURATION', 'HOST_HARDWARE_CONFIGURATION', 'HOST_CPU_HARDWARE_CONFIGURATION', 'HOST_NETWORK_CONFIGURATION', 'HOST_ENTITES', 'HOST_FILESYSTEM_CONFIGURATION', 'HOST_GPU_CONFIGURATION', 'HOST_CONTAINERS'] = Field(..., alias='metricName', description='Gets the metric_name of this HostConfigurationMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_PRODUCT", "HOST_RESOURCE_ALLOCATION", "HOST_MEMORY_CONFIGURATION", "HOST_HARDWARE_CONFIGURATION", "HOST_CPU_HARDWARE_CONFIGURATION", "HOST_NETWORK_CONFIGURATION", "HOST_ENTITES", "HOST_FILESYSTEM_CONFIGURATION", "HOST_GPU_CONFIGURATION", "HOST_CONTAINERS"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    file_system_name: str = Field(..., alias='fileSystemName', description='Name of filesystem')
    mount_point: str = Field(..., alias='mountPoint', description='Mount points are specialized NTFS filesystem objects')
    file_system_size_in_gb: float = Field(..., alias='fileSystemSizeInGB', description='Size of filesystem')


class HostFilesystemUsage(OpsiBaseModel):
    """Filesystem Usage metric for the host."""

    metric_name: Literal['HOST_CPU_USAGE', 'HOST_MEMORY_USAGE', 'HOST_NETWORK_ACTIVITY_SUMMARY', 'HOST_TOP_PROCESSES', 'HOST_FILESYSTEM_USAGE', 'HOST_GPU_USAGE', 'HOST_GPU_PROCESSES', 'HOST_IO_USAGE'] = Field(..., alias='metricName', description='Gets the metric_name of this HostPerformanceMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_CPU_USAGE", "HOST_MEMORY_USAGE", "HOST_NETWORK_ACTIVITY_SUMMARY", "HOST_TOP_PROCESSES", "HOST_FILESYSTEM_USAGE", "HOST_GPU_USAGE", "HOST_GPU_PROCESSES", "HOST_IO_USAGE"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostPerformanceMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    mount_point: str | None = Field(None, alias='mountPoint', description='Mount points are specialized NTFS filesystem objects')
    file_system_usage_in_gb: float | None = Field(None, alias='fileSystemUsageInGB', description='The file_system_usage_in_gb field of HostFilesystemUsage.')
    file_system_avail_in_percent: float | None = Field(None, alias='fileSystemAvailInPercent', description='The file_system_avail_in_percent field of HostFilesystemUsage.')
    file_system_avail_in_gbs: float | None = Field(None, alias='fileSystemAvailInGBs', description='The file_system_avail_in_gbs field of HostFilesystemUsage.')


class HostGpuConfiguration(OpsiBaseModel):
    """GPU configuration metrics."""

    metric_name: Literal['HOST_PRODUCT', 'HOST_RESOURCE_ALLOCATION', 'HOST_MEMORY_CONFIGURATION', 'HOST_HARDWARE_CONFIGURATION', 'HOST_CPU_HARDWARE_CONFIGURATION', 'HOST_NETWORK_CONFIGURATION', 'HOST_ENTITES', 'HOST_FILESYSTEM_CONFIGURATION', 'HOST_GPU_CONFIGURATION', 'HOST_CONTAINERS'] = Field(..., alias='metricName', description='Gets the metric_name of this HostConfigurationMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_PRODUCT", "HOST_RESOURCE_ALLOCATION", "HOST_MEMORY_CONFIGURATION", "HOST_HARDWARE_CONFIGURATION", "HOST_CPU_HARDWARE_CONFIGURATION", "HOST_NETWORK_CONFIGURATION", "HOST_ENTITES", "HOST_FILESYSTEM_CONFIGURATION", "HOST_GPU_CONFIGURATION", "HOST_CONTAINERS"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    gpu_id: int = Field(..., alias='gpuId', description='GPU Identifier')
    product_name: str = Field(..., alias='productName', description='GPU Product Name')
    vendor: str = Field(..., alias='vendor', description='GPU Vendor')
    bus_id: str = Field(..., alias='busId', description='Bus Identifier')
    bus_width: int = Field(..., alias='busWidth', description='Bus Width')
    gpu_capabilities: str | None = Field(None, alias='gpuCapabilities', description='GPU Capabilities')
    total_power: float = Field(..., alias='totalPower', description='Power Capacity')
    total_memory: float = Field(..., alias='totalMemory', description='Total Memory Allocated to GPU')
    total_video_clock_speed: float = Field(..., alias='totalVideoClockSpeed', description='Max Video Clock Speed')
    total_sm_clock_speed: float = Field(..., alias='totalSmClockSpeed', description='Max SM (Streaming Multiprocessor) Clock Speed')
    total_graphics_clock_speed: float = Field(..., alias='totalGraphicsClockSpeed', description='Max Graphics Clock Speed')
    total_memory_clock_speed: float = Field(..., alias='totalMemoryClockSpeed', description='Max Memory Clock Speed')
    cuda_version: str = Field(..., alias='cudaVersion', description='CUDA library version')
    driver_version: str = Field(..., alias='driverVersion', description='GPU Driver version')


class HostGpuProcesses(OpsiBaseModel):
    """GPU processes metrics, processes using GPUs."""

    metric_name: Literal['HOST_CPU_USAGE', 'HOST_MEMORY_USAGE', 'HOST_NETWORK_ACTIVITY_SUMMARY', 'HOST_TOP_PROCESSES', 'HOST_FILESYSTEM_USAGE', 'HOST_GPU_USAGE', 'HOST_GPU_PROCESSES', 'HOST_IO_USAGE'] = Field(..., alias='metricName', description='Gets the metric_name of this HostPerformanceMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_CPU_USAGE", "HOST_MEMORY_USAGE", "HOST_NETWORK_ACTIVITY_SUMMARY", "HOST_TOP_PROCESSES", "HOST_FILESYSTEM_USAGE", "HOST_GPU_USAGE", "HOST_GPU_PROCESSES", "HOST_IO_USAGE"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostPerformanceMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    gpu_id: int | None = Field(None, alias='gpuId', description='GPU Identifier')
    pid: int | None = Field(None, alias='pid', description='Process Identifier')
    process_name: str | None = Field(None, alias='processName', description='Process Name (process using GPU)')
    elapsed_time: float | None = Field(None, alias='elapsedTime', description='Process elapsed time')
    gpu_memory_usage: float | None = Field(None, alias='gpuMemoryUsage', description='Memory Used by Process in MBs')


class HostGpuUsage(OpsiBaseModel):
    """GPU performance metrics."""

    metric_name: Literal['HOST_CPU_USAGE', 'HOST_MEMORY_USAGE', 'HOST_NETWORK_ACTIVITY_SUMMARY', 'HOST_TOP_PROCESSES', 'HOST_FILESYSTEM_USAGE', 'HOST_GPU_USAGE', 'HOST_GPU_PROCESSES', 'HOST_IO_USAGE'] = Field(..., alias='metricName', description='Gets the metric_name of this HostPerformanceMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_CPU_USAGE", "HOST_MEMORY_USAGE", "HOST_NETWORK_ACTIVITY_SUMMARY", "HOST_TOP_PROCESSES", "HOST_FILESYSTEM_USAGE", "HOST_GPU_USAGE", "HOST_GPU_PROCESSES", "HOST_IO_USAGE"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostPerformanceMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    gpu_id: int | None = Field(None, alias='gpuId', description='GPU Identifier')
    utilization: float | None = Field(None, alias='utilization', description='GPU Utilization Percent')
    memory_utilization: float | None = Field(None, alias='memoryUtilization', description='GPU Memory Utilization Percent')
    power_draw: float | None = Field(None, alias='powerDraw', description='GPU Power Draw in Watts')
    temperature: float | None = Field(None, alias='temperature', description='GPU Temperature in Celsius')
    fan_utilization: float | None = Field(None, alias='fanUtilization', description='GPU Fan Utilization')
    clock_speed_graphics: float | None = Field(None, alias='clockSpeedGraphics', description='GPU Graphics (Shader) Clock Speed')
    clock_speed_sm: float | None = Field(None, alias='clockSpeedSm', description='GPU SM (Streaming Multiprocessor) Clock Speed')
    clock_speed_video: float | None = Field(None, alias='clockSpeedVideo', description='GPU Video Clock Speed')
    clock_speed_memory: float | None = Field(None, alias='clockSpeedMemory', description='GPU Memory Clock Speed')
    performance_state: float | None = Field(None, alias='performanceState', description='GPU Performance State')
    ecc_single_bit_errors: int | None = Field(None, alias='eccSingleBitErrors', description='GPU ECC Single Bit Errors')
    ecc_double_bit_errors: int | None = Field(None, alias='eccDoubleBitErrors', description='GPU ECC Double Bit Errors')
    clock_event_idle: int | None = Field(None, alias='clockEventIdle', description='Nothing running on CPU, clocks are idle')
    clock_event_hw_thermal_slow_down: int | None = Field(None, alias='clockEventHwThermalSlowDown', description='HW Thermal Slowdown (reducing the core clocks by a factor of 2 or more) is engaged. Temp too high')
    clock_event_sw_power_cap: int | None = Field(None, alias='clockEventSwPowerCap', description='SW Power Scaling algorithm is reducing the clocks below requested clocks because the GPU is consuming too much power')
    clock_event_app_clock_setting: int | None = Field(None, alias='clockEventAppClockSetting', description='GPU clocks are limited by applications clocks setting')
    clock_event_hw_power_break: int | None = Field(None, alias='clockEventHwPowerBreak', description='HW Power Brake Slowdown (reducing the core clocks by a factor of 2 or more) is engaged')
    clock_event_sw_thermal_slowdown: int | None = Field(None, alias='clockEventSwThermalSlowdown', description='SW Thermal capping algorithm is reducing clocks below requested clocks because GPU temperature is higher than Max Operating Temp')
    clock_event_sync_boost: int | None = Field(None, alias='clockEventSyncBoost', description='HW Power Brake Slowdown (reducing the core clocks by a factor of 2 or more) is engaged')


class HostHardwareConfiguration(OpsiBaseModel):
    """Hardware Configuration metric for the host."""

    metric_name: Literal['HOST_PRODUCT', 'HOST_RESOURCE_ALLOCATION', 'HOST_MEMORY_CONFIGURATION', 'HOST_HARDWARE_CONFIGURATION', 'HOST_CPU_HARDWARE_CONFIGURATION', 'HOST_NETWORK_CONFIGURATION', 'HOST_ENTITES', 'HOST_FILESYSTEM_CONFIGURATION', 'HOST_GPU_CONFIGURATION', 'HOST_CONTAINERS'] = Field(..., alias='metricName', description='Gets the metric_name of this HostConfigurationMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_PRODUCT", "HOST_RESOURCE_ALLOCATION", "HOST_MEMORY_CONFIGURATION", "HOST_HARDWARE_CONFIGURATION", "HOST_CPU_HARDWARE_CONFIGURATION", "HOST_NETWORK_CONFIGURATION", "HOST_ENTITES", "HOST_FILESYSTEM_CONFIGURATION", "HOST_GPU_CONFIGURATION", "HOST_CONTAINERS"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    cpu_architecture: str = Field(..., alias='cpuArchitecture', description='Processor architecture used by the platform')


class HostImportableAgentEntitySummary(OpsiBaseModel):
    """An agent host entity that can be imported into Operations Insights."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this ImportableAgentEntitySummary.\nSource of the importable agent entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='Gets the management_agent_id of this ImportableAgentEntitySummary. The OCID of the Management Agent.')
    management_agent_display_name: str = Field(..., alias='managementAgentDisplayName', description='Gets the management_agent_display_name of this ImportableAgentEntitySummary. The Display Name of the Management Agent.')
    host_name: str | None = Field(None, alias='hostName', description='The host name. The host name is unique amongst the hosts managed by the same management agent.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class HostInsight(OpsiBaseModel):
    """Host insight resource."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Source of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='The OCID of the host insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='The host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='The user-friendly name for the host. The name does not have to be unique.')
    host_type: str | None = Field(None, alias='hostType', description='Ops Insights internal representation of the host type. Possible value is EXTERNAL-HOST.')
    processor_count: int | None = Field(None, alias='processorCount', description='Processor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Indicates the status of a host insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime = Field(..., alias='timeCreated', description='The time the the host insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time the host insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='The current state of the host.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')


class HostInsightHostRecommendations(OpsiBaseModel):
    """Contains recommendations depending of resource metric received."""

    metric_recommendation_name: Literal['HOST_CPU_RECOMMENDATIONS', 'HOST_MEMORY_RECOMMENDATIONS', 'HOST_NETWORK_RECOMMENDATIONS', 'HOST_STORAGE_RECOMMENDATIONS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='metricRecommendationName', description='Name of recommendations depending of resource metric received.\n\nAllowed values for this property are: "HOST_CPU_RECOMMENDATIONS", "HOST_MEMORY_RECOMMENDATIONS", "HOST_NETWORK_RECOMMENDATIONS", "HOST_STORAGE_RECOMMENDATIONS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class HostInsightResourceStatisticsAggregation(OpsiBaseModel):
    """Contains host details and resource statistics."""

    host_details: HostDetails = Field(..., alias='hostDetails', description='The host_details field of HostInsightResourceStatisticsAggregation.')
    current_statistics: HostResourceStatistics = Field(..., alias='currentStatistics', description='The current_statistics field of HostInsightResourceStatisticsAggregation.')


class HostInsightSummary(OpsiBaseModel):
    """Summary of a host insight resource."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Source of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='The OCID of the host insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='The host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='The user-friendly name for the host. The name does not have to be unique.')
    host_type: str | None = Field(None, alias='hostType', description='Ops Insights internal representation of the host type. Possible value is EXTERNAL-HOST.')
    processor_count: int | None = Field(None, alias='processorCount', description='Processor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Indicates the status of a host insight in Ops Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='The time the the host insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time the host insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='The current state of the host.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')


class HostInsightSummaryCollection(OpsiBaseModel):
    """Collection of host insight summary objects."""

    items: list[HostInsightSummary] = Field(..., alias='items', description='Array of host insight summary objects.')


class HostInsights(OpsiBaseModel):
    """Logical grouping used for Operations Insights host related operations."""

    host_insights: Any | None = Field(None, alias='hostInsights', description='Host Insights Object.')


class HostInsightsDataObject(OpsiBaseModel):
    """Host insights data object."""

    identifier: str = Field(..., alias='identifier', description='Gets the identifier of this OpsiDataObject.\nUnique identifier of OPSI data object.')
    data_object_type: Literal['DATABASE_INSIGHTS_DATA_OBJECT', 'HOST_INSIGHTS_DATA_OBJECT', 'EXADATA_INSIGHTS_DATA_OBJECT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='dataObjectType', description='Gets the data_object_type of this OpsiDataObject.\nType of OPSI data object.\n\nAllowed values for this property are: "DATABASE_INSIGHTS_DATA_OBJECT", "HOST_INSIGHTS_DATA_OBJECT", "EXADATA_INSIGHTS_DATA_OBJECT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str = Field(..., alias='displayName', description='Gets the display_name of this OpsiDataObject.\nUser-friendly name of OPSI data object.')
    description: str | None = Field(None, alias='description', description='Gets the description of this OpsiDataObject.\nDescription of OPSI data object.')
    name: str | None = Field(None, alias='name', description='Gets the name of this OpsiDataObject.\nName of the data object, which can be used in data object queries just like how view names are used in a query.')
    group_names: list[str] | None = Field(None, alias='groupNames', description='Gets the group_names of this OpsiDataObject.\nNames of all the groups to which the data object belongs to.')
    supported_query_time_period: str | None = Field(None, alias='supportedQueryTimePeriod', description='Gets the supported_query_time_period of this OpsiDataObject.\nTime period supported by the data object for quering data.\nTime period is in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D.\nExamples: P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months).')
    columns_metadata: list[DataObjectColumnMetadata] = Field(..., alias='columnsMetadata', description='Gets the columns_metadata of this OpsiDataObject.\nMetadata of columns in a data object.')
    supported_query_params: list[OpsiDataObjectSupportedQueryParam] | None = Field(None, alias='supportedQueryParams', description='Gets the supported_query_params of this OpsiDataObject.\nSupported query parameters by this OPSI data object that can be configured while a data object query involving this data object is executed.')


class HostInsightsDataObjectSummary(OpsiBaseModel):
    """Summary of a host insights data object."""

    identifier: str = Field(..., alias='identifier', description='Gets the identifier of this OpsiDataObjectSummary.\nUnique identifier of OPSI data object.')
    data_object_type: Literal['DATABASE_INSIGHTS_DATA_OBJECT', 'HOST_INSIGHTS_DATA_OBJECT', 'EXADATA_INSIGHTS_DATA_OBJECT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='dataObjectType', description='Gets the data_object_type of this OpsiDataObjectSummary.\nType of OPSI data object.\n\nAllowed values for this property are: "DATABASE_INSIGHTS_DATA_OBJECT", "HOST_INSIGHTS_DATA_OBJECT", "EXADATA_INSIGHTS_DATA_OBJECT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str = Field(..., alias='displayName', description='Gets the display_name of this OpsiDataObjectSummary.\nUser-friendly name of OPSI data object.')
    description: str | None = Field(None, alias='description', description='Gets the description of this OpsiDataObjectSummary.\nDescription of OPSI data object.')
    name: str | None = Field(None, alias='name', description='Gets the name of this OpsiDataObjectSummary.\nName of the data object, which can be used in data object queries just like how view names are used in a query.')
    group_names: list[str] | None = Field(None, alias='groupNames', description='Gets the group_names of this OpsiDataObjectSummary.\nNames of all the groups to which the data object belongs to.')


class HostInstanceMap(OpsiBaseModel):
    """Object containing hostname and instance name mapping."""

    host_name: str = Field(..., alias='hostName', description='The hostname of the database insight resource.')
    instance_name: str = Field(..., alias='instanceName', description='The instance name of the database insight resource.')


class HostIoStatistics(OpsiBaseModel):
    """Contains io statistics."""

    usage: float = Field(..., alias='usage', description='Gets the usage of this HostResourceStatistics.\nTotal amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='Gets the capacity of this HostResourceStatistics.\nThe maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    utilization_percent: float = Field(..., alias='utilizationPercent', description='Gets the utilization_percent of this HostResourceStatistics.\nResource utilization in percentage.')
    usage_change_percent: float = Field(..., alias='usageChangePercent', description='Gets the usage_change_percent of this HostResourceStatistics.\nChange in resource utilization in percentage')
    resource_name: Literal['HOST_CPU_STATISTICS', 'HOST_MEMORY_STATISTICS', 'HOST_STORAGE_STATISTICS', 'HOST_NETWORK_STATISTICS', 'HOST_IO_STATISTICS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceName', description='Gets the resource_name of this HostResourceStatistics.\nName of resource for host\n\nAllowed values for this property are: "HOST_CPU_STATISTICS", "HOST_MEMORY_STATISTICS", "HOST_STORAGE_STATISTICS", "HOST_NETWORK_STATISTICS", "HOST_IO_STATISTICS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    disk_read_in_mbs: float | None = Field(None, alias='diskReadInMBs', description='The disk_read_in_mbs field of HostIoStatistics.')
    disk_write_in_mbs: float | None = Field(None, alias='diskWriteInMBs', description='The disk_write_in_mbs field of HostIoStatistics.')
    disk_iops: float | None = Field(None, alias='diskIops', description='The disk_iops field of HostIoStatistics.')


class HostIoUsage(OpsiBaseModel):
    """Host IO Performance Metrics."""

    metric_name: Literal['HOST_CPU_USAGE', 'HOST_MEMORY_USAGE', 'HOST_NETWORK_ACTIVITY_SUMMARY', 'HOST_TOP_PROCESSES', 'HOST_FILESYSTEM_USAGE', 'HOST_GPU_USAGE', 'HOST_GPU_PROCESSES', 'HOST_IO_USAGE'] = Field(..., alias='metricName', description='Gets the metric_name of this HostPerformanceMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_CPU_USAGE", "HOST_MEMORY_USAGE", "HOST_NETWORK_ACTIVITY_SUMMARY", "HOST_TOP_PROCESSES", "HOST_FILESYSTEM_USAGE", "HOST_GPU_USAGE", "HOST_GPU_PROCESSES", "HOST_IO_USAGE"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostPerformanceMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    mount_point: str | None = Field(None, alias='mountPoint', description='Mount point')
    disk_bytes_read: float | None = Field(None, alias='diskBytesRead', description='Bytes Read')
    disk_bytes_written: float | None = Field(None, alias='diskBytesWritten', description='Bytes Written')
    disk_iops_read: float | None = Field(None, alias='diskIopsRead', description='Read transactions per second')
    disk_iops_written: float | None = Field(None, alias='diskIopsWritten', description='Write transactions per second')
    disk_iops: float | None = Field(None, alias='diskIops', description='IO Transactions per second')


class HostMemoryConfiguration(OpsiBaseModel):
    """Memory Configuration metric for the host."""

    metric_name: Literal['HOST_PRODUCT', 'HOST_RESOURCE_ALLOCATION', 'HOST_MEMORY_CONFIGURATION', 'HOST_HARDWARE_CONFIGURATION', 'HOST_CPU_HARDWARE_CONFIGURATION', 'HOST_NETWORK_CONFIGURATION', 'HOST_ENTITES', 'HOST_FILESYSTEM_CONFIGURATION', 'HOST_GPU_CONFIGURATION', 'HOST_CONTAINERS'] = Field(..., alias='metricName', description='Gets the metric_name of this HostConfigurationMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_PRODUCT", "HOST_RESOURCE_ALLOCATION", "HOST_MEMORY_CONFIGURATION", "HOST_HARDWARE_CONFIGURATION", "HOST_CPU_HARDWARE_CONFIGURATION", "HOST_NETWORK_CONFIGURATION", "HOST_ENTITES", "HOST_FILESYSTEM_CONFIGURATION", "HOST_GPU_CONFIGURATION", "HOST_CONTAINERS"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    page_size_in_kb: float | None = Field(None, alias='pageSizeInKB', description='Page size in kilobytes')
    page_tables_in_kb: float | None = Field(None, alias='pageTablesInKB', description='Amount of memory used for page tables in kilobytes')
    swap_total_in_kb: float | None = Field(None, alias='swapTotalInKB', description='Amount of total swap space in kilobytes')
    huge_page_size_in_kb: float | None = Field(None, alias='hugePageSizeInKB', description='Size of huge pages in kilobytes')
    huge_pages_total: int | None = Field(None, alias='hugePagesTotal', description='Total number of huge pages')


class HostMemoryRecommendations(OpsiBaseModel):
    """Contains memory recommendation."""

    metric_recommendation_name: Literal['HOST_CPU_RECOMMENDATIONS', 'HOST_MEMORY_RECOMMENDATIONS', 'HOST_NETWORK_RECOMMENDATIONS', 'HOST_STORAGE_RECOMMENDATIONS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='metricRecommendationName', description='Gets the metric_recommendation_name of this HostInsightHostRecommendations.\nName of recommendations depending of resource metric received.\n\nAllowed values for this property are: "HOST_CPU_RECOMMENDATIONS", "HOST_MEMORY_RECOMMENDATIONS", "HOST_NETWORK_RECOMMENDATIONS", "HOST_STORAGE_RECOMMENDATIONS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    unused_instance: Literal['IN_USE', 'NOT_IN_USE', 'IS_NOT_DETERMINED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='unusedInstance', description='Identify unused instances based on cpu, memory and network metrics.\n\nAllowed values for this property are: "IN_USE", "NOT_IN_USE", "IS_NOT_DETERMINED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    is_abandoned_instance: bool | None = Field(None, alias='isAbandonedInstance', description='Identify if an instance is abandoned.')
    memory_optimization: str | None = Field(None, alias='memoryOptimization', description='Show if OPSI recommends to change memory capacity based on Memory utilization and current shape.')


class HostMemoryStatistics(OpsiBaseModel):
    """Contains memory statistics."""

    usage: float = Field(..., alias='usage', description='Gets the usage of this HostResourceStatistics.\nTotal amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='Gets the capacity of this HostResourceStatistics.\nThe maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    utilization_percent: float = Field(..., alias='utilizationPercent', description='Gets the utilization_percent of this HostResourceStatistics.\nResource utilization in percentage.')
    usage_change_percent: float = Field(..., alias='usageChangePercent', description='Gets the usage_change_percent of this HostResourceStatistics.\nChange in resource utilization in percentage')
    resource_name: Literal['HOST_CPU_STATISTICS', 'HOST_MEMORY_STATISTICS', 'HOST_STORAGE_STATISTICS', 'HOST_NETWORK_STATISTICS', 'HOST_IO_STATISTICS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceName', description='Gets the resource_name of this HostResourceStatistics.\nName of resource for host\n\nAllowed values for this property are: "HOST_CPU_STATISTICS", "HOST_MEMORY_STATISTICS", "HOST_STORAGE_STATISTICS", "HOST_NETWORK_STATISTICS", "HOST_IO_STATISTICS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    free_memory: float | None = Field(None, alias='freeMemory', description='The free_memory field of HostMemoryStatistics.')
    available_memory: float | None = Field(None, alias='availableMemory', description='The available_memory field of HostMemoryStatistics.')
    huge_pages_total: int | None = Field(None, alias='hugePagesTotal', description='Total number of huge pages.')
    huge_page_size_in_mb: float | None = Field(None, alias='hugePageSizeInMB', description='Size of huge pages in megabytes.')
    huge_pages_free: int | None = Field(None, alias='hugePagesFree', description='Total number of available huge pages.')
    huge_pages_reserved: int | None = Field(None, alias='hugePagesReserved', description='Total number of huge pages which are used or reserved.')
    load: SummaryStatistics | None = Field(None, alias='load', description='The load field of HostMemoryStatistics.')


class HostMemoryUsage(OpsiBaseModel):
    """Memory usage metric for the host."""

    metric_name: Literal['HOST_CPU_USAGE', 'HOST_MEMORY_USAGE', 'HOST_NETWORK_ACTIVITY_SUMMARY', 'HOST_TOP_PROCESSES', 'HOST_FILESYSTEM_USAGE', 'HOST_GPU_USAGE', 'HOST_GPU_PROCESSES', 'HOST_IO_USAGE'] = Field(..., alias='metricName', description='Gets the metric_name of this HostPerformanceMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_CPU_USAGE", "HOST_MEMORY_USAGE", "HOST_NETWORK_ACTIVITY_SUMMARY", "HOST_TOP_PROCESSES", "HOST_FILESYSTEM_USAGE", "HOST_GPU_USAGE", "HOST_GPU_PROCESSES", "HOST_IO_USAGE"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostPerformanceMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    memory_used_in_gb: float | None = Field(None, alias='memoryUsedInGB', description='Amount of physical memory used in gigabytes')
    memory_utilization_in_percent: float | None = Field(None, alias='memoryUtilizationInPercent', description='Amount of physical memory used in percentage')
    memory_load_in_gb: float | None = Field(None, alias='memoryLoadInGB', description='Load on memory in gigabytes')
    real_memory_in_kb: float | None = Field(None, alias='realMemoryInKB', description='Amount of usable physical memory in kilobytes')
    free_memory_in_kb: float | None = Field(None, alias='freeMemoryInKB', description='Amount of available physical memory in kilobytes')
    logical_memory_used_in_gb: float | None = Field(None, alias='logicalMemoryUsedInGB', description='Memory used excluding buffers and cache in gigabytes')
    logical_memory_utilization_in_percent: float | None = Field(None, alias='logicalMemoryUtilizationInPercent', description='Amount of logical memory used in percentage')
    free_logical_memory_in_kb: float | None = Field(None, alias='freeLogicalMemoryInKB', description='Amount of avaiable virtual memory in kilobytes')
    major_page_faults: int | None = Field(None, alias='majorPageFaults', description='Number of major page faults')
    swap_free_in_kb: float | None = Field(None, alias='swapFreeInKB', description='Amount of available swap space in kilobytes')
    anon_huge_pages_in_kb: float | None = Field(None, alias='anonHugePagesInKB', description='Amount of memory used for anon huge pages in kilobytes')
    huge_pages_free: int | None = Field(None, alias='hugePagesFree', description='Number of available huge pages')
    huge_pages_reserved: int | None = Field(None, alias='hugePagesReserved', description='Number of reserved huge pages')
    huge_pages_surplus: int | None = Field(None, alias='hugePagesSurplus', description='Number of surplus huge pages')


class HostNetworkActivitySummary(OpsiBaseModel):
    """Network Activity Summary metric for the host."""

    metric_name: Literal['HOST_CPU_USAGE', 'HOST_MEMORY_USAGE', 'HOST_NETWORK_ACTIVITY_SUMMARY', 'HOST_TOP_PROCESSES', 'HOST_FILESYSTEM_USAGE', 'HOST_GPU_USAGE', 'HOST_GPU_PROCESSES', 'HOST_IO_USAGE'] = Field(..., alias='metricName', description='Gets the metric_name of this HostPerformanceMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_CPU_USAGE", "HOST_MEMORY_USAGE", "HOST_NETWORK_ACTIVITY_SUMMARY", "HOST_TOP_PROCESSES", "HOST_FILESYSTEM_USAGE", "HOST_GPU_USAGE", "HOST_GPU_PROCESSES", "HOST_IO_USAGE"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostPerformanceMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    interface_name: str | None = Field(None, alias='interfaceName', description='Name of the network interface')
    all_network_read_in_mbps: float | None = Field(None, alias='allNetworkReadInMbps', description='All network interfaces read rate in Mbps')
    all_network_write_in_mbps: float | None = Field(None, alias='allNetworkWriteInMbps', description='All network interfaces write rate in Mbps')
    all_network_io_in_mbps: float | None = Field(None, alias='allNetworkIoInMbps', description='All network interfaces IO rate in Mbps')


class HostNetworkConfiguration(OpsiBaseModel):
    """Network Configuration metric for the host."""

    metric_name: Literal['HOST_PRODUCT', 'HOST_RESOURCE_ALLOCATION', 'HOST_MEMORY_CONFIGURATION', 'HOST_HARDWARE_CONFIGURATION', 'HOST_CPU_HARDWARE_CONFIGURATION', 'HOST_NETWORK_CONFIGURATION', 'HOST_ENTITES', 'HOST_FILESYSTEM_CONFIGURATION', 'HOST_GPU_CONFIGURATION', 'HOST_CONTAINERS'] = Field(..., alias='metricName', description='Gets the metric_name of this HostConfigurationMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_PRODUCT", "HOST_RESOURCE_ALLOCATION", "HOST_MEMORY_CONFIGURATION", "HOST_HARDWARE_CONFIGURATION", "HOST_CPU_HARDWARE_CONFIGURATION", "HOST_NETWORK_CONFIGURATION", "HOST_ENTITES", "HOST_FILESYSTEM_CONFIGURATION", "HOST_GPU_CONFIGURATION", "HOST_CONTAINERS"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    interface_name: str = Field(..., alias='interfaceName', description='Name of the network interface')
    ip_address: str = Field(..., alias='ipAddress', description='IP address (IPv4 or IPv6) of the network interface')
    mac_address: str | None = Field(None, alias='macAddress', description='MAC address of the network interface. MAC address is a 12-digit hexadecimal number separated by colons or dashes or dots. Following formats are accepted: MM:MM:MM:SS:SS:SS, MM-MM-MM-SS-SS-SS, MM.MM.MM.SS.SS.SS, MMM:MMM:SSS:SSS, MMM-MMM-SSS-SSS, MMM.MMM.SSS.SSS, MMMM:MMSS:SSSS, MMMM-MMSS-SSSS, MMMM.MMSS.SSSS')


class HostNetworkRecommendations(OpsiBaseModel):
    """Contains network recommendation."""

    metric_recommendation_name: Literal['HOST_CPU_RECOMMENDATIONS', 'HOST_MEMORY_RECOMMENDATIONS', 'HOST_NETWORK_RECOMMENDATIONS', 'HOST_STORAGE_RECOMMENDATIONS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='metricRecommendationName', description='Gets the metric_recommendation_name of this HostInsightHostRecommendations.\nName of recommendations depending of resource metric received.\n\nAllowed values for this property are: "HOST_CPU_RECOMMENDATIONS", "HOST_MEMORY_RECOMMENDATIONS", "HOST_NETWORK_RECOMMENDATIONS", "HOST_STORAGE_RECOMMENDATIONS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    unused_instance: Literal['IN_USE', 'NOT_IN_USE', 'IS_NOT_DETERMINED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='unusedInstance', description='Identify unused instances based on cpu, memory and network metrics.\n\nAllowed values for this property are: "IN_USE", "NOT_IN_USE", "IS_NOT_DETERMINED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    is_abandoned_instance: bool | None = Field(None, alias='isAbandonedInstance', description='Identify if an instance is abandoned.')


class HostNetworkStatistics(OpsiBaseModel):
    """Contains network statistics."""

    usage: float = Field(..., alias='usage', description='Gets the usage of this HostResourceStatistics.\nTotal amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='Gets the capacity of this HostResourceStatistics.\nThe maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    utilization_percent: float = Field(..., alias='utilizationPercent', description='Gets the utilization_percent of this HostResourceStatistics.\nResource utilization in percentage.')
    usage_change_percent: float = Field(..., alias='usageChangePercent', description='Gets the usage_change_percent of this HostResourceStatistics.\nChange in resource utilization in percentage')
    resource_name: Literal['HOST_CPU_STATISTICS', 'HOST_MEMORY_STATISTICS', 'HOST_STORAGE_STATISTICS', 'HOST_NETWORK_STATISTICS', 'HOST_IO_STATISTICS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceName', description='Gets the resource_name of this HostResourceStatistics.\nName of resource for host\n\nAllowed values for this property are: "HOST_CPU_STATISTICS", "HOST_MEMORY_STATISTICS", "HOST_STORAGE_STATISTICS", "HOST_NETWORK_STATISTICS", "HOST_IO_STATISTICS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    network_read_in_mbs: float | None = Field(None, alias='networkReadInMBs', description='The network_read_in_mbs field of HostNetworkStatistics.')
    network_write_in_mbs: float | None = Field(None, alias='networkWriteInMBs', description='The network_write_in_mbs field of HostNetworkStatistics.')


class HostPerformanceMetricGroup(OpsiBaseModel):
    """Base Metric Group for Host performance metrics."""

    metric_name: Literal['HOST_CPU_USAGE', 'HOST_MEMORY_USAGE', 'HOST_NETWORK_ACTIVITY_SUMMARY', 'HOST_TOP_PROCESSES', 'HOST_FILESYSTEM_USAGE', 'HOST_GPU_USAGE', 'HOST_GPU_PROCESSES', 'HOST_IO_USAGE'] = Field(..., alias='metricName', description='Name of the metric group\n\nAllowed values for this property are: "HOST_CPU_USAGE", "HOST_MEMORY_USAGE", "HOST_NETWORK_ACTIVITY_SUMMARY", "HOST_TOP_PROCESSES", "HOST_FILESYSTEM_USAGE", "HOST_GPU_USAGE", "HOST_GPU_PROCESSES", "HOST_IO_USAGE"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Collection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')


class HostProduct(OpsiBaseModel):
    """Product metric for the host."""

    metric_name: Literal['HOST_PRODUCT', 'HOST_RESOURCE_ALLOCATION', 'HOST_MEMORY_CONFIGURATION', 'HOST_HARDWARE_CONFIGURATION', 'HOST_CPU_HARDWARE_CONFIGURATION', 'HOST_NETWORK_CONFIGURATION', 'HOST_ENTITES', 'HOST_FILESYSTEM_CONFIGURATION', 'HOST_GPU_CONFIGURATION', 'HOST_CONTAINERS'] = Field(..., alias='metricName', description='Gets the metric_name of this HostConfigurationMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_PRODUCT", "HOST_RESOURCE_ALLOCATION", "HOST_MEMORY_CONFIGURATION", "HOST_HARDWARE_CONFIGURATION", "HOST_CPU_HARDWARE_CONFIGURATION", "HOST_NETWORK_CONFIGURATION", "HOST_ENTITES", "HOST_FILESYSTEM_CONFIGURATION", "HOST_GPU_CONFIGURATION", "HOST_CONTAINERS"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    vendor: str | None = Field(None, alias='vendor', description='Vendor of the product')
    name: str | None = Field(None, alias='name', description='Name of the product')
    version: str | None = Field(None, alias='version', description='Version of the product')


class HostResourceAllocation(OpsiBaseModel):
    """Resource Allocation metric for the host."""

    metric_name: Literal['HOST_PRODUCT', 'HOST_RESOURCE_ALLOCATION', 'HOST_MEMORY_CONFIGURATION', 'HOST_HARDWARE_CONFIGURATION', 'HOST_CPU_HARDWARE_CONFIGURATION', 'HOST_NETWORK_CONFIGURATION', 'HOST_ENTITES', 'HOST_FILESYSTEM_CONFIGURATION', 'HOST_GPU_CONFIGURATION', 'HOST_CONTAINERS'] = Field(..., alias='metricName', description='Gets the metric_name of this HostConfigurationMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_PRODUCT", "HOST_RESOURCE_ALLOCATION", "HOST_MEMORY_CONFIGURATION", "HOST_HARDWARE_CONFIGURATION", "HOST_CPU_HARDWARE_CONFIGURATION", "HOST_NETWORK_CONFIGURATION", "HOST_ENTITES", "HOST_FILESYSTEM_CONFIGURATION", "HOST_GPU_CONFIGURATION", "HOST_CONTAINERS"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostConfigurationMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    total_cpus: int | None = Field(None, alias='totalCpus', description='Total number of CPUs available')
    total_memory_in_gb: float | None = Field(None, alias='totalMemoryInGB', description='Total amount of usable physical memory in gibabytes')


class HostResourceCapacityTrendAggregation(OpsiBaseModel):
    """Host Resource Capacity samples."""

    end_timestamp: datetime = Field(..., alias='endTimestamp', description='The timestamp in which the current sampling period ends in RFC 3339 format.')
    capacity: float = Field(..., alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')


class HostResourceStatistics(OpsiBaseModel):
    """Contains host resource base statistics."""

    usage: float = Field(..., alias='usage', description='Total amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    utilization_percent: float = Field(..., alias='utilizationPercent', description='Resource utilization in percentage.')
    usage_change_percent: float = Field(..., alias='usageChangePercent', description='Change in resource utilization in percentage')
    resource_name: Literal['HOST_CPU_STATISTICS', 'HOST_MEMORY_STATISTICS', 'HOST_STORAGE_STATISTICS', 'HOST_NETWORK_STATISTICS', 'HOST_IO_STATISTICS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceName', description='Name of resource for host\n\nAllowed values for this property are: "HOST_CPU_STATISTICS", "HOST_MEMORY_STATISTICS", "HOST_STORAGE_STATISTICS", "HOST_NETWORK_STATISTICS", "HOST_IO_STATISTICS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class HostStorageRecommendations(OpsiBaseModel):
    """Contains storage recommendation."""

    metric_recommendation_name: Literal['HOST_CPU_RECOMMENDATIONS', 'HOST_MEMORY_RECOMMENDATIONS', 'HOST_NETWORK_RECOMMENDATIONS', 'HOST_STORAGE_RECOMMENDATIONS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='metricRecommendationName', description='Gets the metric_recommendation_name of this HostInsightHostRecommendations.\nName of recommendations depending of resource metric received.\n\nAllowed values for this property are: "HOST_CPU_RECOMMENDATIONS", "HOST_MEMORY_RECOMMENDATIONS", "HOST_NETWORK_RECOMMENDATIONS", "HOST_STORAGE_RECOMMENDATIONS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    unused_instance: Literal['IN_USE', 'NOT_IN_USE', 'IS_NOT_DETERMINED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='unusedInstance', description='Identify unused instances based on cpu, memory and network metrics.\n\nAllowed values for this property are: "IN_USE", "NOT_IN_USE", "IS_NOT_DETERMINED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    is_abandoned_instance: bool | None = Field(None, alias='isAbandonedInstance', description='Identify if an instance is abandoned.')


class HostStorageStatistics(OpsiBaseModel):
    """Contains storage statistics."""

    usage: float = Field(..., alias='usage', description='Gets the usage of this HostResourceStatistics.\nTotal amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='Gets the capacity of this HostResourceStatistics.\nThe maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    utilization_percent: float = Field(..., alias='utilizationPercent', description='Gets the utilization_percent of this HostResourceStatistics.\nResource utilization in percentage.')
    usage_change_percent: float = Field(..., alias='usageChangePercent', description='Gets the usage_change_percent of this HostResourceStatistics.\nChange in resource utilization in percentage')
    resource_name: Literal['HOST_CPU_STATISTICS', 'HOST_MEMORY_STATISTICS', 'HOST_STORAGE_STATISTICS', 'HOST_NETWORK_STATISTICS', 'HOST_IO_STATISTICS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceName', description='Gets the resource_name of this HostResourceStatistics.\nName of resource for host\n\nAllowed values for this property are: "HOST_CPU_STATISTICS", "HOST_MEMORY_STATISTICS", "HOST_STORAGE_STATISTICS", "HOST_NETWORK_STATISTICS", "HOST_IO_STATISTICS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    filesystem_available_in_percent: float | None = Field(None, alias='filesystemAvailableInPercent', description='The filesystem_available_in_percent field of HostStorageStatistics.')


class HostTopProcesses(OpsiBaseModel):
    """Top Processes metric for the host."""

    metric_name: Literal['HOST_CPU_USAGE', 'HOST_MEMORY_USAGE', 'HOST_NETWORK_ACTIVITY_SUMMARY', 'HOST_TOP_PROCESSES', 'HOST_FILESYSTEM_USAGE', 'HOST_GPU_USAGE', 'HOST_GPU_PROCESSES', 'HOST_IO_USAGE'] = Field(..., alias='metricName', description='Gets the metric_name of this HostPerformanceMetricGroup.\nName of the metric group\n\nAllowed values for this property are: "HOST_CPU_USAGE", "HOST_MEMORY_USAGE", "HOST_NETWORK_ACTIVITY_SUMMARY", "HOST_TOP_PROCESSES", "HOST_FILESYSTEM_USAGE", "HOST_GPU_USAGE", "HOST_GPU_PROCESSES", "HOST_IO_USAGE"')
    time_collected: datetime = Field(..., alias='timeCollected', description='Gets the time_collected of this HostPerformanceMetricGroup.\nCollection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    pid: float | None = Field(None, alias='pid', description='process id')
    user_name: str | None = Field(None, alias='userName', description='User that started the process')
    memory_utilization_percent: float | None = Field(None, alias='memoryUtilizationPercent', description='Memory utilization percentage')
    cpu_utilization_percent: float | None = Field(None, alias='cpuUtilizationPercent', description='CPU utilization percentage')
    cpu_usage_in_seconds: float | None = Field(None, alias='cpuUsageInSeconds', description='CPU usage in seconds')
    command: str | None = Field(None, alias='command', description='Command line executed for the process')
    virtual_memory_in_mbs: float | None = Field(None, alias='virtualMemoryInMBs', description='Virtual memory in megabytes')
    physical_memory_in_mbs: float | None = Field(None, alias='physicalMemoryInMBs', description='Physical memory in megabytes')
    start_time: datetime | None = Field(None, alias='startTime', description='Process Start Time\nExample: `"2020-03-31T00:00:00.000Z"`')
    total_processes: float | None = Field(None, alias='totalProcesses', description='Number of processes running at the time of collection')
    container_id: str | None = Field(None, alias='containerId', description='Container id if this process corresponds to a running container in the host')
    disk_bytes_read: float | None = Field(None, alias='diskBytesRead', description='Bytes Read')
    disk_bytes_written: float | None = Field(None, alias='diskBytesWritten', description='Bytes Written')
    disk_iops_read: float | None = Field(None, alias='diskIopsRead', description='Read transactions per second')
    disk_iops_written: float | None = Field(None, alias='diskIopsWritten', description='Write transactions per second')
    disk_iops: float | None = Field(None, alias='diskIops', description='IO Transactions per second')


class HostedEntityCollection(OpsiBaseModel):
    """Returns a list of hosted entities for the specific host."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    items: list[HostedEntitySummary] = Field(..., alias='items', description='List of hosted entities details.')


class HostedEntitySummary(OpsiBaseModel):
    """Information about a hosted entity which includes identifier, name, and type."""

    entity_identifier: str = Field(..., alias='entityIdentifier', description='The identifier of the entity.')
    entity_name: str = Field(..., alias='entityName', description='The entity name.')
    entity_type: str = Field(..., alias='entityType', description='The entity type.')


class ImportableAgentEntitySummary(OpsiBaseModel):
    """An agent entity that can be imported into Operations Insights."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Source of the importable agent entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    management_agent_display_name: str = Field(..., alias='managementAgentDisplayName', description='The Display Name of the Management Agent.')


class ImportableAgentEntitySummaryCollection(OpsiBaseModel):
    """Collection of importable agent entity objects."""

    items: list[ImportableAgentEntitySummary] = Field(..., alias='items', description='Array of importable agent entity objects.')


class ImportableComputeEntitySummary(OpsiBaseModel):
    """A compute entity that can be imported into Operations Insights."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Source of the importable agent entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compute_id: str = Field(..., alias='computeId', description='The OCID of the Compute Instance.')
    compute_display_name: str = Field(..., alias='computeDisplayName', description='The Display Name of the Compute Instance.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')


class ImportableComputeEntitySummaryCollection(OpsiBaseModel):
    """Collection of importable compute entity objects."""

    items: list[ImportableComputeEntitySummary] = Field(..., alias='items', description='Array of importable compute entity objects.')


class ImportableEnterpriseManagerEntity(OpsiBaseModel):
    """An Enterprise Manager entity that can be imported into Operations Insights."""

    enterprise_manager_identifier: str = Field(..., alias='enterpriseManagerIdentifier', description='Enterprise Manager Unique Identifier')
    enterprise_manager_entity_name: str = Field(..., alias='enterpriseManagerEntityName', description='Enterprise Manager Entity Name')
    enterprise_manager_entity_type: str = Field(..., alias='enterpriseManagerEntityType', description='Enterprise Manager Entity Type')
    enterprise_manager_entity_identifier: str = Field(..., alias='enterpriseManagerEntityIdentifier', description='Enterprise Manager Entity Unique Identifier')
    opsi_entity_type: str | None = Field(None, alias='opsiEntityType', description='Ops Insights internal representation of the resource type.')


class ImportableEnterpriseManagerEntityCollection(OpsiBaseModel):
    """Collection of importable Enterprise Manager entity objects."""

    items: list[ImportableEnterpriseManagerEntity] = Field(..., alias='items', description='Array of importable Enterprise Manager entity objects.')


class IndividualOpsiDataObjectDetailsInQuery(OpsiBaseModel):
    """Details applicable for an individual OPSI data object used in a data object query."""

    data_object_details_target: Literal['INDIVIDUAL_OPSIDATAOBJECT', 'OPSIDATAOBJECTTYPE_OPSIDATAOBJECTS'] = Field(..., alias='dataObjectDetailsTarget', description='Gets the data_object_details_target of this OpsiDataObjectDetailsInQuery.\nData objects to which this OpsiDataObjectDetailsInQuery is applicable.\n\nAllowed values for this property are: "INDIVIDUAL_OPSIDATAOBJECT", "OPSIDATAOBJECTTYPE_OPSIDATAOBJECTS"')
    query_params: list[OpsiDataObjectQueryParam] | None = Field(None, alias='queryParams', description='Gets the _query_params of this OpsiDataObjectDetailsInQuery.\nAn array of query parameters to be applied, for the OPSI data objects targetted by dataObjectDetailsTarget, before executing the query.\nRefer to supportedQueryParams of OpsiDataObject for the supported query parameters.')
    data_object_identifier: str = Field(..., alias='dataObjectIdentifier', description='Unique OPSI data object identifier.')


class IngestAddmReportsDetails(OpsiRequestModel):
    """Collection of Addm reports."""

    items: list[AddmReport] = Field(..., alias='items', description='List of Addm reports')


class IngestAddmReportsResponseDetails(OpsiBaseModel):
    """The response object returned from IngestAddmReports operation."""

    message: str = Field(..., alias='message', description='Success message returned as a result of the upload.')


class IngestDatabaseConfigurationDetails(OpsiRequestModel):
    """Database Configuration Metrics details."""

    items: list[DatabaseConfigurationMetricGroup] = Field(..., alias='items', description='Array of one or more database configuration metrics objects.')


class IngestDatabaseConfigurationResponseDetails(OpsiBaseModel):
    """The response object returned from IngestDatabaseConfiguration operation."""

    message: str = Field(..., alias='message', description='Success message returned as a result of the upload.')


class IngestHostConfigurationDetails(OpsiRequestModel):
    """Contains the data to ingest for one or more host configuration metrics."""

    items: list[HostConfigurationMetricGroup] = Field(..., alias='items', description='Collection of one or more host configuration metric data points')


class IngestHostConfigurationResponseDetails(OpsiBaseModel):
    """The response object returned from IngestHostConfiguration operation."""

    message: str = Field(..., alias='message', description='Success message returned as a result of the upload.')


class IngestHostMetricsDetails(OpsiRequestModel):
    """Contains the data to ingest for one or more host performance metrics."""

    items: list[HostPerformanceMetricGroup] = Field(..., alias='items', description='Collection of one or more host performance metric data points')


class IngestHostMetricsResponseDetails(OpsiBaseModel):
    """The response object returned from IngestHostMetrics operation."""

    message: str = Field(..., alias='message', description='Success message returned as a result of the upload.')


class IngestMySqlSqlStatsDetails(OpsiRequestModel):
    """Collection of MySql SQL Stats Metric Entries."""

    items: list[MySqlSqlStats] | None = Field(None, alias='items', description='List of MySql SQL Stats Metric Entries.')


class IngestMySqlSqlStatsResponseDetails(OpsiBaseModel):
    """The response object returned from IngestMySqlSqlStats operation."""

    message: str = Field(..., alias='message', description='Success message returned as a result of the upload.')


class IngestMySqlSqlTextDetails(OpsiRequestModel):
    """Collection of SQL Text Entries."""

    items: list[MySqlSqlText] | None = Field(None, alias='items', description='List of SQL Text Entries.')


class IngestMySqlSqlTextResponseDetails(OpsiBaseModel):
    """The response object returned from IngestMySqlSqlTextDetails operation."""

    message: str = Field(..., alias='message', description='Success message returned as a result of the upload.')


class IngestSqlBucketDetails(OpsiRequestModel):
    """Collection of SQL Bucket Metric Entries."""

    items: list[SqlBucket] | None = Field(None, alias='items', description='List of SQL Bucket Metric Entries.')


class IngestSqlBucketResponseDetails(OpsiBaseModel):
    """The response object returned from IngestSqlBucketDetails operation."""

    message: str = Field(..., alias='message', description='Success message returned as a result of the upload.')


class IngestSqlPlanLinesDetails(OpsiRequestModel):
    """Collection of SQL Plan Line Entries."""

    items: list[SqlPlanLine] | None = Field(None, alias='items', description='List of SQL Plan Line Entries.')


class IngestSqlPlanLinesResponseDetails(OpsiBaseModel):
    """The response object returned from IngestSqlPlanLines operation."""

    message: str = Field(..., alias='message', description='Success message returned as a result of the upload.')


class IngestSqlStatsDetails(OpsiRequestModel):
    """Collection of SQL Stats Metric Entries."""

    items: list[SqlStats] | None = Field(None, alias='items', description='List of SQL Stats Metric Entries.')


class IngestSqlStatsResponseDetails(OpsiBaseModel):
    """The response object returned from IngestSqlStats operation."""

    message: str = Field(..., alias='message', description='Success message returned as a result of the upload.')


class IngestSqlTextDetails(OpsiRequestModel):
    """Collection of SQL Text Entries."""

    items: list[SqlText] | None = Field(None, alias='items', description='List of SQL Text Entries.')


class IngestSqlTextResponseDetails(OpsiBaseModel):
    """The response object returned from IngestSqlTextDetails operation."""

    message: str = Field(..., alias='message', description='Success message returned as a result of the upload.')


class InstanceMetrics(OpsiBaseModel):
    """Object containing instance metrics."""

    host_name: str | None = Field(None, alias='hostName', description='The hostname of the database insight resource.')
    instance_name: str | None = Field(None, alias='instanceName', description='The instance name of the database insight resource.')
    usage: float | None = Field(None, alias='usage', description='Total amount used of the resource metric type (CPU, STORAGE).')
    capacity: float | None = Field(None, alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    total_host_capacity: float | None = Field(None, alias='totalHostCapacity', description='The maximum host CPUs (cores x threads/core) on the underlying infrastructure. This only applies to CPU and does not not apply for Autonomous Databases.')
    utilization_percent: float | None = Field(None, alias='utilizationPercent', description='Resource utilization in percentage')
    usage_change_percent: float | None = Field(None, alias='usageChangePercent', description='Change in resource utilization in percentage')


class IoUsageTrend(OpsiBaseModel):
    """Usage data for IO interface per usage unit."""

    end_timestamp: datetime = Field(..., alias='endTimestamp', description='The timestamp in which the current sampling period ends in RFC 3339 format.')
    disk_bytes_read_in_mbs: float = Field(..., alias='diskBytesReadInMBs', description='MBs Read.')
    disk_bytes_written_in_mbs: float = Field(..., alias='diskBytesWrittenInMBs', description='MBs Written.')
    disk_iops_read: float = Field(..., alias='diskIopsRead', description='Read IO operations per second.')
    disk_iops_written: float = Field(..., alias='diskIopsWritten', description='Write IO operations per second.')
    disk_iops: float = Field(..., alias='diskIops', description='IO operations per second.')


class IoUsageTrendAggregation(OpsiBaseModel):
    """Usage data per io interface."""

    mount_point: str = Field(..., alias='mountPoint', description='Mount point is specialized NTFS filesystem object.')
    usage_data: list[IoUsageTrend] = Field(..., alias='usageData', description='List of usage data samples for a IO interface.')


class ListObjects(OpsiBaseModel):
    """List of the objects."""

    prefixes: list[str] | None = Field(None, alias='prefixes', description='Array comprising of all the prefixes.')
    next_start_with: str | None = Field(None, alias='nextStartWith', description='Object names returned by a list query must be greater or equal to this parameter.')
    objects: list[ObjectSummary] = Field(..., alias='objects', description='List of the object summary data.')


class MacsManagedAutonomousDatabaseConfigurationSummary(OpsiBaseModel):
    """Configuration Summary of a Macs Managed Cloud Autonomous database."""

    database_insight_id: str = Field(..., alias='databaseInsightId', description='Gets the database_insight_id of this DatabaseConfigurationSummary. The OCID of the database insight resource.')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseConfigurationSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseConfigurationSummary. The OCID of the compartment.')
    database_name: str = Field(..., alias='databaseName', description='Gets the database_name of this DatabaseConfigurationSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str = Field(..., alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseConfigurationSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str = Field(..., alias='databaseType', description='Gets the database_type of this DatabaseConfigurationSummary.\nOps Insights internal representation of the database type.')
    database_version: str = Field(..., alias='databaseVersion', description='Gets the database_version of this DatabaseConfigurationSummary.\nThe version of the database.')
    is_advanced_features_enabled: bool = Field(..., alias='isAdvancedFeaturesEnabled', description='Gets the is_advanced_features_enabled of this DatabaseConfigurationSummary.\nFlag is to identify if advanced features for autonomous database is enabled or not')
    cdb_name: str = Field(..., alias='cdbName', description='Gets the cdb_name of this DatabaseConfigurationSummary.\nName of the CDB.Only applies to PDB.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseConfigurationSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    parent_id: str = Field(..., alias='parentId', description='The OCID of the database.')
    exadata_details: ExadataDetails = Field(..., alias='exadataDetails', description='The exadata_details field of MacsManagedAutonomousDatabaseConfigurationSummary.')


class MacsManagedAutonomousDatabaseInsight(OpsiBaseModel):
    """Database insight resource."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsight.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsight.\nDatabase insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseInsight.\nCompartment identifier of the database')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this DatabaseInsight.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsight.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsight.\nThe version of the database.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this DatabaseInsight.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsight.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsight.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsight.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    management_agent_id: str | None = Field(None, alias='managementAgentId', description='The OCID of the Management Agent.')
    connection_details: ConnectionDetails | None = Field(None, alias='connectionDetails', description='The connection_details field of MacsManagedAutonomousDatabaseInsight.')
    connection_credential_details: CredentialDetails | None = Field(None, alias='connectionCredentialDetails', description='The connection_credential_details field of MacsManagedAutonomousDatabaseInsight.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    database_name: str = Field(..., alias='databaseName', description='Name of database')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Display name of database')
    database_resource_type: str = Field(..., alias='databaseResourceType', description='OCI database resource type')
    db_additional_details: Any | None = Field(None, alias='dbAdditionalDetails', description='Additional details of a database in JSON format. For autonomous databases, this is the AutonomousDatabase object serialized as a JSON string as defined in  For EM, pass in null or an empty string. Note that this string needs to be escaped when specified in the curl command.')
    parent_id: str | None = Field(None, alias='parentId', description='The OCID of the VM Cluster or DB System ID, depending on which configuration the resource belongs to.')
    root_id: str | None = Field(None, alias='rootId', description='The OCID of the Exadata Infrastructure.')


class MacsManagedAutonomousDatabaseInsightSummary(OpsiBaseModel):
    """Summary of a database insight resource."""

    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsightSummary. The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='Gets the database_id of this DatabaseInsightSummary. The OCID of the database.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='Gets the compartment_id of this DatabaseInsightSummary. The OCID of the compartment.')
    database_name: str | None = Field(None, alias='databaseName', description='Gets the database_name of this DatabaseInsightSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseInsightSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsightSummary.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsightSummary.\nThe version of the database.')
    database_host_names: list[str] | None = Field(None, alias='databaseHostNames', description='Gets the database_host_names of this DatabaseInsightSummary.\nThe hostnames for the database.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this DatabaseInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsightSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this DatabaseInsightSummary.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this DatabaseInsightSummary.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsightSummary.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsightSummary.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsightSummary.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    database_resource_type: str | None = Field(None, alias='databaseResourceType', description='OCI database resource type')
    management_agent_id: str | None = Field(None, alias='managementAgentId', description='The OCID of the Management Agent.')
    parent_id: str | None = Field(None, alias='parentId', description='The OCID of the VM Cluster or DB System ID, depending on which configuration the resource belongs to.')
    root_id: str | None = Field(None, alias='rootId', description='The OCID of the root resource for a composite target. e.g. for ExaCS members the rootId will be the OCID of the Exadata Infrastructure resource.')


class MacsManagedCloudDatabaseConfigurationSummary(OpsiBaseModel):
    """Configuration Summary of a Macs Managed Cloud database."""

    database_insight_id: str = Field(..., alias='databaseInsightId', description='Gets the database_insight_id of this DatabaseConfigurationSummary. The OCID of the database insight resource.')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseConfigurationSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseConfigurationSummary. The OCID of the compartment.')
    database_name: str = Field(..., alias='databaseName', description='Gets the database_name of this DatabaseConfigurationSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str = Field(..., alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseConfigurationSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str = Field(..., alias='databaseType', description='Gets the database_type of this DatabaseConfigurationSummary.\nOps Insights internal representation of the database type.')
    database_version: str = Field(..., alias='databaseVersion', description='Gets the database_version of this DatabaseConfigurationSummary.\nThe version of the database.')
    is_advanced_features_enabled: bool = Field(..., alias='isAdvancedFeaturesEnabled', description='Gets the is_advanced_features_enabled of this DatabaseConfigurationSummary.\nFlag is to identify if advanced features for autonomous database is enabled or not')
    cdb_name: str = Field(..., alias='cdbName', description='Gets the cdb_name of this DatabaseConfigurationSummary.\nName of the CDB.Only applies to PDB.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseConfigurationSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    parent_id: str = Field(..., alias='parentId', description='The OCID of the database.')
    exadata_details: ExadataDetails = Field(..., alias='exadataDetails', description='The exadata_details field of MacsManagedCloudDatabaseConfigurationSummary.')


class MacsManagedCloudDatabaseHostInsight(OpsiBaseModel):
    """Cloud MACS-managed database host insight resource."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostInsight.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this HostInsight. The OCID of the host insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostInsight. The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='Gets the host_name of this HostInsight.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='Gets the host_display_name of this HostInsight.\nThe user-friendly name for the host. The name does not have to be unique.')
    host_type: str | None = Field(None, alias='hostType', description='Gets the host_type of this HostInsight.\nOps Insights internal representation of the host type. Possible value is EXTERNAL-HOST.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this HostInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this HostInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this HostInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this HostInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this HostInsight.\nIndicates the status of a host insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this HostInsight.\nThe time the the host insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this HostInsight.\nThe time the host insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this HostInsight.\nThe current state of the host.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this HostInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    platform_name: str | None = Field(None, alias='platformName', description='Platform name.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    platform_version: str | None = Field(None, alias='platformVersion', description='Platform version.')
    parent_id: str | None = Field(None, alias='parentId', description='The OCID of the VM Cluster or DB System ID, depending on which configuration the resource belongs to.')
    root_id: str | None = Field(None, alias='rootId', description='The OCID of the Exadata Infrastructure.')


class MacsManagedCloudDatabaseHostInsightSummary(OpsiBaseModel):
    """Summary of a Cloud MACS-managed database host insight resource."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostInsightSummary.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this HostInsightSummary. The OCID of the host insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostInsightSummary. The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='Gets the host_name of this HostInsightSummary.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='Gets the host_display_name of this HostInsightSummary.\nThe user-friendly name for the host. The name does not have to be unique.')
    host_type: str | None = Field(None, alias='hostType', description='Gets the host_type of this HostInsightSummary.\nOps Insights internal representation of the host type. Possible value is EXTERNAL-HOST.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this HostInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this HostInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this HostInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this HostInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='Gets the opsi_private_endpoint_id of this HostInsightSummary. The OCID of the OPSI private endpoint.')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this HostInsightSummary.\nIndicates the status of a host insight in Ops Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this HostInsightSummary.\nThe time the the host insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this HostInsightSummary.\nThe time the host insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this HostInsightSummary.\nThe current state of the host.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this HostInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    parent_id: str | None = Field(None, alias='parentId', description='The OCID of the VM Cluster or DB System ID, depending on which configuration the resource belongs to.')
    root_id: str | None = Field(None, alias='rootId', description='The OCID of the Exadata Infrastructure.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class MacsManagedCloudDatabaseInsight(OpsiBaseModel):
    """Database insight resource."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsight.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsight.\nDatabase insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseInsight.\nCompartment identifier of the database')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this DatabaseInsight.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsight.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsight.\nThe version of the database.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this DatabaseInsight.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsight.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsight.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsight.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    management_agent_id: str | None = Field(None, alias='managementAgentId', description='The OCID of the Management Agent.')
    connection_details: ConnectionDetails | None = Field(None, alias='connectionDetails', description='The connection_details field of MacsManagedCloudDatabaseInsight.')
    connection_credential_details: CredentialDetails | None = Field(None, alias='connectionCredentialDetails', description='The connection_credential_details field of MacsManagedCloudDatabaseInsight.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    database_name: str = Field(..., alias='databaseName', description='Name of database')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Display name of database')
    database_resource_type: str = Field(..., alias='databaseResourceType', description='OCI database resource type')
    db_additional_details: Any | None = Field(None, alias='dbAdditionalDetails', description='Additional details of a database in JSON format. For autonomous databases, this is the AutonomousDatabase object serialized as a JSON string as defined in  For EM, pass in null or an empty string. Note that this string needs to be escaped when specified in the curl command.')
    parent_id: str | None = Field(None, alias='parentId', description='The OCID of the VM Cluster or DB System ID, depending on which configuration the resource belongs to.')
    root_id: str | None = Field(None, alias='rootId', description='The OCID of the Exadata Infrastructure.')


class MacsManagedCloudDatabaseInsightSummary(OpsiBaseModel):
    """Summary of a database insight resource."""

    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsightSummary. The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='Gets the database_id of this DatabaseInsightSummary. The OCID of the database.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='Gets the compartment_id of this DatabaseInsightSummary. The OCID of the compartment.')
    database_name: str | None = Field(None, alias='databaseName', description='Gets the database_name of this DatabaseInsightSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseInsightSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsightSummary.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsightSummary.\nThe version of the database.')
    database_host_names: list[str] | None = Field(None, alias='databaseHostNames', description='Gets the database_host_names of this DatabaseInsightSummary.\nThe hostnames for the database.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this DatabaseInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsightSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this DatabaseInsightSummary.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this DatabaseInsightSummary.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsightSummary.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsightSummary.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsightSummary.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    database_resource_type: str | None = Field(None, alias='databaseResourceType', description='OCI database resource type')
    management_agent_id: str | None = Field(None, alias='managementAgentId', description='The OCID of the Management Agent.')
    parent_id: str | None = Field(None, alias='parentId', description='The OCID of the VM Cluster or DB System ID, depending on which configuration the resource belongs to.')
    root_id: str | None = Field(None, alias='rootId', description='The OCID of the root resource for a composite target. e.g. for ExaCS members the rootId will be the OCID of the Exadata Infrastructure resource.')


class MacsManagedCloudDbHostConfigurationSummary(OpsiBaseModel):
    """Configuration Summary of Cloud MACS-managed database host insight resource."""

    host_insight_id: str = Field(..., alias='hostInsightId', description='Gets the host_insight_id of this HostConfigurationSummary. The OCID of the host insight resource.')
    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostConfigurationSummary.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostConfigurationSummary. The OCID of the compartment.')
    host_name: str = Field(..., alias='hostName', description='Gets the host_name of this HostConfigurationSummary.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='platformType', description='Gets the platform_type of this HostConfigurationSummary.\nPlatform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    platform_version: str = Field(..., alias='platformVersion', description='Gets the platform_version of this HostConfigurationSummary.\nPlatform version.')
    platform_vendor: str = Field(..., alias='platformVendor', description='Gets the platform_vendor of this HostConfigurationSummary.\nPlatform vendor.')
    total_cpus: int = Field(..., alias='totalCpus', description='Gets the total_cpus of this HostConfigurationSummary.\nTotal CPU on this host.')
    total_memory_in_gbs: float = Field(..., alias='totalMemoryInGBs', description='Gets the total_memory_in_gbs of this HostConfigurationSummary.\nTotal amount of usable physical memory in gibabytes')
    cpu_architecture: str = Field(..., alias='cpuArchitecture', description='Gets the cpu_architecture of this HostConfigurationSummary.\nCPU architechure')
    cpu_cache_in_mbs: float = Field(..., alias='cpuCacheInMBs', description='Gets the cpu_cache_in_mbs of this HostConfigurationSummary.\nSize of cache memory in megabytes.')
    cpu_vendor: str = Field(..., alias='cpuVendor', description='Gets the cpu_vendor of this HostConfigurationSummary.\nName of the CPU vendor.')
    cpu_frequency_in_mhz: float = Field(..., alias='cpuFrequencyInMhz', description='Gets the cpu_frequency_in_mhz of this HostConfigurationSummary.\nClock frequency of the processor in megahertz.')
    cpu_implementation: str = Field(..., alias='cpuImplementation', description='Gets the cpu_implementation of this HostConfigurationSummary.\nModel name of processor.')
    cores_per_socket: int = Field(..., alias='coresPerSocket', description='Gets the cores_per_socket of this HostConfigurationSummary.\nNumber of cores per socket.')
    total_sockets: int = Field(..., alias='totalSockets', description='Gets the total_sockets of this HostConfigurationSummary.\nNumber of total sockets.')
    threads_per_socket: int = Field(..., alias='threadsPerSocket', description='Gets the threads_per_socket of this HostConfigurationSummary.\nNumber of threads per socket.')
    is_hyper_threading_enabled: bool = Field(..., alias='isHyperThreadingEnabled', description='Gets the is_hyper_threading_enabled of this HostConfigurationSummary.\nIndicates if hyper-threading is enabled or not')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this HostConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this HostConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    parent_id: str = Field(..., alias='parentId', description='The OCID of the database.')
    exadata_details: ExadataDetails = Field(..., alias='exadataDetails', description='The exadata_details field of MacsManagedCloudDbHostConfigurationSummary.')


class MacsManagedCloudExadataInsight(OpsiBaseModel):
    """Cloud MACS-managed Exadata insight resource (ExaCC) (ExaCS will be supported in the future)."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this ExadataInsight.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this ExadataInsight.\nExadata insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this ExadataInsight.\nCompartment identifier of the Exadata insight resource')
    exadata_name: str = Field(..., alias='exadataName', description='Gets the exadata_name of this ExadataInsight.\nThe Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str | None = Field(None, alias='exadataDisplayName', description='Gets the exadata_display_name of this ExadataInsight.\nThe user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataType', description='Gets the exadata_type of this ExadataInsight.\nOperations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataRackType', description='Gets the exadata_rack_type of this ExadataInsight.\nExadata rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    is_virtualized_exadata: bool | None = Field(None, alias='isVirtualizedExadata', description='Gets the is_virtualized_exadata of this ExadataInsight.\ntrue if virtualization is used in the Exadata system')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this ExadataInsight.\nIndicates the status of an Exadata insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    chargeback_plan_details: ChargebackPlanDetails | None = Field(None, alias='chargebackPlanDetails', description='Gets the chargeback_plan_details of this ExadataInsight.')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this ExadataInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this ExadataInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this ExadataInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this ExadataInsight.\nThe time the the Exadata insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this ExadataInsight.\nThe time the Exadata insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this ExadataInsight.\nThe current state of the Exadata insight.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this ExadataInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    status_details: str | None = Field(None, alias='statusDetails', description='Gets the status_details of this ExadataInsight.\nA message describing the status of the Exadata Resource. For example, it can be used to provide actionable information about the policies needed to access the Exadata Resource.')
    exadata_infra_id: str = Field(..., alias='exadataInfraId', description='The OCID of the Exadata Infrastructure.')
    exadata_infra_resource_type: Literal['cloudExadataInfrastructure', 'exadataInfrastructure', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataInfraResourceType', description='OCI exadata infrastructure resource type\n\nAllowed values for this property are: "cloudExadataInfrastructure", "exadataInfrastructure", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_shape: str = Field(..., alias='exadataShape', description='The shape of the Exadata Infrastructure.')


class MacsManagedCloudExadataInsightSummary(OpsiBaseModel):
    """Summary of a Cloud MACS-managed Exadata insight resource (ExaCC)."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this ExadataInsightSummary.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this ExadataInsightSummary. The OCID of the Exadata insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this ExadataInsightSummary. The OCID of the compartment.')
    exadata_name: str = Field(..., alias='exadataName', description='Gets the exadata_name of this ExadataInsightSummary.\nThe Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str | None = Field(None, alias='exadataDisplayName', description='Gets the exadata_display_name of this ExadataInsightSummary.\nThe user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataType', description='Gets the exadata_type of this ExadataInsightSummary.\nOperations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataRackType', description='Gets the exadata_rack_type of this ExadataInsightSummary.\nOperations Insights internal representation of the the Exadata system rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this ExadataInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this ExadataInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this ExadataInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this ExadataInsightSummary.\nIndicates the status of an Exadata insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    chargeback_plan_details: ChargebackPlanDetails | None = Field(None, alias='chargebackPlanDetails', description='Gets the chargeback_plan_details of this ExadataInsightSummary.')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this ExadataInsightSummary.\nThe time the the Exadata insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this ExadataInsightSummary.\nThe time the Exadata insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this ExadataInsightSummary.\nThe current state of the Exadata insight.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this ExadataInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    status_details: str | None = Field(None, alias='statusDetails', description='Gets the status_details of this ExadataInsightSummary.\nA message describing the status of the Exadata Resource. For example, it can be used to provide actionable information about the policies needed to access the Exadata Resource.')
    exadata_infra_id: str = Field(..., alias='exadataInfraId', description='The OCID of the Exadata Infrastructure.')
    exadata_infra_resource_type: Literal['cloudExadataInfrastructure', 'exadataInfrastructure', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataInfraResourceType', description='OCI exadata infrastructure resource type\n\nAllowed values for this property are: "cloudExadataInfrastructure", "exadataInfrastructure", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_shape: str = Field(..., alias='exadataShape', description='The shape of the Exadata Infrastructure.')


class MacsManagedCloudHostConfigurationSummary(OpsiBaseModel):
    """Configuration Summary of a Macs Managed Cloud host."""

    host_insight_id: str = Field(..., alias='hostInsightId', description='Gets the host_insight_id of this HostConfigurationSummary. The OCID of the host insight resource.')
    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostConfigurationSummary.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostConfigurationSummary. The OCID of the compartment.')
    host_name: str = Field(..., alias='hostName', description='Gets the host_name of this HostConfigurationSummary.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='platformType', description='Gets the platform_type of this HostConfigurationSummary.\nPlatform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    platform_version: str = Field(..., alias='platformVersion', description='Gets the platform_version of this HostConfigurationSummary.\nPlatform version.')
    platform_vendor: str = Field(..., alias='platformVendor', description='Gets the platform_vendor of this HostConfigurationSummary.\nPlatform vendor.')
    total_cpus: int = Field(..., alias='totalCpus', description='Gets the total_cpus of this HostConfigurationSummary.\nTotal CPU on this host.')
    total_memory_in_gbs: float = Field(..., alias='totalMemoryInGBs', description='Gets the total_memory_in_gbs of this HostConfigurationSummary.\nTotal amount of usable physical memory in gibabytes')
    cpu_architecture: str = Field(..., alias='cpuArchitecture', description='Gets the cpu_architecture of this HostConfigurationSummary.\nCPU architechure')
    cpu_cache_in_mbs: float = Field(..., alias='cpuCacheInMBs', description='Gets the cpu_cache_in_mbs of this HostConfigurationSummary.\nSize of cache memory in megabytes.')
    cpu_vendor: str = Field(..., alias='cpuVendor', description='Gets the cpu_vendor of this HostConfigurationSummary.\nName of the CPU vendor.')
    cpu_frequency_in_mhz: float = Field(..., alias='cpuFrequencyInMhz', description='Gets the cpu_frequency_in_mhz of this HostConfigurationSummary.\nClock frequency of the processor in megahertz.')
    cpu_implementation: str = Field(..., alias='cpuImplementation', description='Gets the cpu_implementation of this HostConfigurationSummary.\nModel name of processor.')
    cores_per_socket: int = Field(..., alias='coresPerSocket', description='Gets the cores_per_socket of this HostConfigurationSummary.\nNumber of cores per socket.')
    total_sockets: int = Field(..., alias='totalSockets', description='Gets the total_sockets of this HostConfigurationSummary.\nNumber of total sockets.')
    threads_per_socket: int = Field(..., alias='threadsPerSocket', description='Gets the threads_per_socket of this HostConfigurationSummary.\nNumber of threads per socket.')
    is_hyper_threading_enabled: bool = Field(..., alias='isHyperThreadingEnabled', description='Gets the is_hyper_threading_enabled of this HostConfigurationSummary.\nIndicates if hyper-threading is enabled or not')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this HostConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this HostConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    compute_id: str = Field(..., alias='computeId', description='The OCID of the Compute Instance.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    connector_id: str | None = Field(None, alias='connectorId', description='The OCID of External Database Connector.')


class MacsManagedCloudHostInsight(OpsiBaseModel):
    """MACS-managed OCI Compute host insight resource."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostInsight.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this HostInsight. The OCID of the host insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostInsight. The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='Gets the host_name of this HostInsight.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='Gets the host_display_name of this HostInsight.\nThe user-friendly name for the host. The name does not have to be unique.')
    host_type: str | None = Field(None, alias='hostType', description='Gets the host_type of this HostInsight.\nOps Insights internal representation of the host type. Possible value is EXTERNAL-HOST.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this HostInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this HostInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this HostInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this HostInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this HostInsight.\nIndicates the status of a host insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this HostInsight.\nThe time the the host insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this HostInsight.\nThe time the host insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this HostInsight.\nThe current state of the host.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this HostInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    compute_id: str = Field(..., alias='computeId', description='The OCID of the Compute Instance.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    platform_name: str | None = Field(None, alias='platformName', description='Platform name.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    platform_version: str | None = Field(None, alias='platformVersion', description='Platform version.')


class MacsManagedCloudHostInsightSummary(OpsiBaseModel):
    """Summary of a MACS-managed cloud host insight resource."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostInsightSummary.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this HostInsightSummary. The OCID of the host insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostInsightSummary. The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='Gets the host_name of this HostInsightSummary.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='Gets the host_display_name of this HostInsightSummary.\nThe user-friendly name for the host. The name does not have to be unique.')
    host_type: str | None = Field(None, alias='hostType', description='Gets the host_type of this HostInsightSummary.\nOps Insights internal representation of the host type. Possible value is EXTERNAL-HOST.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this HostInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this HostInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this HostInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this HostInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='Gets the opsi_private_endpoint_id of this HostInsightSummary. The OCID of the OPSI private endpoint.')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this HostInsightSummary.\nIndicates the status of a host insight in Ops Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this HostInsightSummary.\nThe time the the host insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this HostInsightSummary.\nThe time the host insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this HostInsightSummary.\nThe current state of the host.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this HostInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    compute_id: str = Field(..., alias='computeId', description='The OCID of the Compute Instance.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class MacsManagedExternalDatabaseConfigurationSummary(OpsiBaseModel):
    """Configuration Summary of a Macs Managed External database."""

    database_insight_id: str = Field(..., alias='databaseInsightId', description='Gets the database_insight_id of this DatabaseConfigurationSummary. The OCID of the database insight resource.')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseConfigurationSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseConfigurationSummary. The OCID of the compartment.')
    database_name: str = Field(..., alias='databaseName', description='Gets the database_name of this DatabaseConfigurationSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str = Field(..., alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseConfigurationSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str = Field(..., alias='databaseType', description='Gets the database_type of this DatabaseConfigurationSummary.\nOps Insights internal representation of the database type.')
    database_version: str = Field(..., alias='databaseVersion', description='Gets the database_version of this DatabaseConfigurationSummary.\nThe version of the database.')
    is_advanced_features_enabled: bool = Field(..., alias='isAdvancedFeaturesEnabled', description='Gets the is_advanced_features_enabled of this DatabaseConfigurationSummary.\nFlag is to identify if advanced features for autonomous database is enabled or not')
    cdb_name: str = Field(..., alias='cdbName', description='Gets the cdb_name of this DatabaseConfigurationSummary.\nName of the CDB.Only applies to PDB.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseConfigurationSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    connector_id: str = Field(..., alias='connectorId', description='The OCID of External Database Connector.')
    instances: list[HostInstanceMap] = Field(..., alias='instances', description='Array of hostname and instance name.')


class MacsManagedExternalDatabaseInsight(OpsiBaseModel):
    """Database insight resource."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsight.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsight.\nDatabase insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseInsight.\nCompartment identifier of the database')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this DatabaseInsight.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsight.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsight.\nThe version of the database.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this DatabaseInsight.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsight.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsight.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsight.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    management_agent_id: str | None = Field(None, alias='managementAgentId', description='The OCID of the Management Agent.')
    connector_id: str | None = Field(None, alias='connectorId', description='The OCID of External Database Connector.')
    connection_details: ConnectionDetails | None = Field(None, alias='connectionDetails', description='The connection_details field of MacsManagedExternalDatabaseInsight.')
    connection_credential_details: CredentialDetails | None = Field(None, alias='connectionCredentialDetails', description='The connection_credential_details field of MacsManagedExternalDatabaseInsight.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    database_name: str = Field(..., alias='databaseName', description='Name of database')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Display name of database')
    database_resource_type: str = Field(..., alias='databaseResourceType', description='OCI database resource type')
    db_additional_details: Any | None = Field(None, alias='dbAdditionalDetails', description='Additional details of a database in JSON format. For autonomous databases, this is the AutonomousDatabase object serialized as a JSON string as defined in  For EM, pass in null or an empty string. Note that this string needs to be escaped when specified in the curl command.')


class MacsManagedExternalDatabaseInsightSummary(OpsiBaseModel):
    """Summary of a database insight resource."""

    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsightSummary. The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='Gets the database_id of this DatabaseInsightSummary. The OCID of the database.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='Gets the compartment_id of this DatabaseInsightSummary. The OCID of the compartment.')
    database_name: str | None = Field(None, alias='databaseName', description='Gets the database_name of this DatabaseInsightSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseInsightSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsightSummary.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsightSummary.\nThe version of the database.')
    database_host_names: list[str] | None = Field(None, alias='databaseHostNames', description='Gets the database_host_names of this DatabaseInsightSummary.\nThe hostnames for the database.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this DatabaseInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsightSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this DatabaseInsightSummary.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this DatabaseInsightSummary.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsightSummary.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsightSummary.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsightSummary.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    database_resource_type: str | None = Field(None, alias='databaseResourceType', description='OCI database resource type')
    management_agent_id: str | None = Field(None, alias='managementAgentId', description='The OCID of the Management Agent.')
    connector_id: str | None = Field(None, alias='connectorId', description='The OCID of External Database Connector.')


class MacsManagedExternalHostConfigurationSummary(OpsiBaseModel):
    """Configuration Summary of a Macs Managed External host."""

    host_insight_id: str = Field(..., alias='hostInsightId', description='Gets the host_insight_id of this HostConfigurationSummary. The OCID of the host insight resource.')
    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostConfigurationSummary.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostConfigurationSummary. The OCID of the compartment.')
    host_name: str = Field(..., alias='hostName', description='Gets the host_name of this HostConfigurationSummary.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='platformType', description='Gets the platform_type of this HostConfigurationSummary.\nPlatform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    platform_version: str = Field(..., alias='platformVersion', description='Gets the platform_version of this HostConfigurationSummary.\nPlatform version.')
    platform_vendor: str = Field(..., alias='platformVendor', description='Gets the platform_vendor of this HostConfigurationSummary.\nPlatform vendor.')
    total_cpus: int = Field(..., alias='totalCpus', description='Gets the total_cpus of this HostConfigurationSummary.\nTotal CPU on this host.')
    total_memory_in_gbs: float = Field(..., alias='totalMemoryInGBs', description='Gets the total_memory_in_gbs of this HostConfigurationSummary.\nTotal amount of usable physical memory in gibabytes')
    cpu_architecture: str = Field(..., alias='cpuArchitecture', description='Gets the cpu_architecture of this HostConfigurationSummary.\nCPU architechure')
    cpu_cache_in_mbs: float = Field(..., alias='cpuCacheInMBs', description='Gets the cpu_cache_in_mbs of this HostConfigurationSummary.\nSize of cache memory in megabytes.')
    cpu_vendor: str = Field(..., alias='cpuVendor', description='Gets the cpu_vendor of this HostConfigurationSummary.\nName of the CPU vendor.')
    cpu_frequency_in_mhz: float = Field(..., alias='cpuFrequencyInMhz', description='Gets the cpu_frequency_in_mhz of this HostConfigurationSummary.\nClock frequency of the processor in megahertz.')
    cpu_implementation: str = Field(..., alias='cpuImplementation', description='Gets the cpu_implementation of this HostConfigurationSummary.\nModel name of processor.')
    cores_per_socket: int = Field(..., alias='coresPerSocket', description='Gets the cores_per_socket of this HostConfigurationSummary.\nNumber of cores per socket.')
    total_sockets: int = Field(..., alias='totalSockets', description='Gets the total_sockets of this HostConfigurationSummary.\nNumber of total sockets.')
    threads_per_socket: int = Field(..., alias='threadsPerSocket', description='Gets the threads_per_socket of this HostConfigurationSummary.\nNumber of threads per socket.')
    is_hyper_threading_enabled: bool = Field(..., alias='isHyperThreadingEnabled', description='Gets the is_hyper_threading_enabled of this HostConfigurationSummary.\nIndicates if hyper-threading is enabled or not')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this HostConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this HostConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    connector_id: str | None = Field(None, alias='connectorId', description='The OCID of External Database Connector.')


class MacsManagedExternalHostInsight(OpsiBaseModel):
    """MACS-managed external host insight resource."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostInsight.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this HostInsight. The OCID of the host insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostInsight. The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='Gets the host_name of this HostInsight.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='Gets the host_display_name of this HostInsight.\nThe user-friendly name for the host. The name does not have to be unique.')
    host_type: str | None = Field(None, alias='hostType', description='Gets the host_type of this HostInsight.\nOps Insights internal representation of the host type. Possible value is EXTERNAL-HOST.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this HostInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this HostInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this HostInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this HostInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this HostInsight.\nIndicates the status of a host insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this HostInsight.\nThe time the the host insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this HostInsight.\nThe time the host insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this HostInsight.\nThe current state of the host.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this HostInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    platform_name: str | None = Field(None, alias='platformName', description='Platform name.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    platform_version: str | None = Field(None, alias='platformVersion', description='Platform version.')


class MacsManagedExternalHostInsightSummary(OpsiBaseModel):
    """Summary of a MACS-managed external host insight resource."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostInsightSummary.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this HostInsightSummary. The OCID of the host insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostInsightSummary. The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='Gets the host_name of this HostInsightSummary.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='Gets the host_display_name of this HostInsightSummary.\nThe user-friendly name for the host. The name does not have to be unique.')
    host_type: str | None = Field(None, alias='hostType', description='Gets the host_type of this HostInsightSummary.\nOps Insights internal representation of the host type. Possible value is EXTERNAL-HOST.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this HostInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this HostInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this HostInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this HostInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='Gets the opsi_private_endpoint_id of this HostInsightSummary. The OCID of the OPSI private endpoint.')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this HostInsightSummary.\nIndicates the status of a host insight in Ops Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this HostInsightSummary.\nThe time the the host insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this HostInsightSummary.\nThe time the host insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this HostInsightSummary.\nThe current state of the host.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this HostInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class MdsMySqlDatabaseInsight(OpsiBaseModel):
    """MySQL support within the OCI Ops Insights service has been deprecated as of January 29, 2026. Database insight resource."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsight.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsight.\nDatabase insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseInsight.\nCompartment identifier of the database')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this DatabaseInsight.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsight.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsight.\nThe version of the database.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this DatabaseInsight.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsight.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsight.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsight.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    database_name: str = Field(..., alias='databaseName', description='Name of database')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Display name of database')
    database_resource_type: str = Field(..., alias='databaseResourceType', description='OCI database resource type')
    is_highly_available: bool | None = Field(None, alias='isHighlyAvailable', description='Specifies if MYSQL DB System is highly available.')
    is_heat_wave_cluster_attached: bool | None = Field(None, alias='isHeatWaveClusterAttached', description='Specifies if MYSQL DB System has heatwave cluster attached.')
    db_additional_details: Any | None = Field(None, alias='dbAdditionalDetails', description='Additional details of a db system in JSON format. For MySQL DB System, this is the DbSystem object serialized as a JSON string as defined in.')


class MdsMySqlDatabaseInsightSummary(OpsiBaseModel):
    """MySQL support within the OCI Ops Insights service has been deprecated as of January 29, 2026. Summary of a database insight resource."""

    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsightSummary. The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='Gets the database_id of this DatabaseInsightSummary. The OCID of the database.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='Gets the compartment_id of this DatabaseInsightSummary. The OCID of the compartment.')
    database_name: str | None = Field(None, alias='databaseName', description='Gets the database_name of this DatabaseInsightSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseInsightSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsightSummary.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsightSummary.\nThe version of the database.')
    database_host_names: list[str] | None = Field(None, alias='databaseHostNames', description='Gets the database_host_names of this DatabaseInsightSummary.\nThe hostnames for the database.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this DatabaseInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsightSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this DatabaseInsightSummary.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this DatabaseInsightSummary.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsightSummary.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsightSummary.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsightSummary.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    database_resource_type: str | None = Field(None, alias='databaseResourceType', description='OCI database resource type')


class MdsMysqlDatabaseConfigurationSummary(OpsiBaseModel):
    """Configuration Summary of a MDS MYSQL database."""

    database_insight_id: str = Field(..., alias='databaseInsightId', description='Gets the database_insight_id of this DatabaseConfigurationSummary. The OCID of the database insight resource.')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseConfigurationSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseConfigurationSummary. The OCID of the compartment.')
    database_name: str = Field(..., alias='databaseName', description='Gets the database_name of this DatabaseConfigurationSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str = Field(..., alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseConfigurationSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str = Field(..., alias='databaseType', description='Gets the database_type of this DatabaseConfigurationSummary.\nOps Insights internal representation of the database type.')
    database_version: str = Field(..., alias='databaseVersion', description='Gets the database_version of this DatabaseConfigurationSummary.\nThe version of the database.')
    is_advanced_features_enabled: bool = Field(..., alias='isAdvancedFeaturesEnabled', description='Gets the is_advanced_features_enabled of this DatabaseConfigurationSummary.\nFlag is to identify if advanced features for autonomous database is enabled or not')
    cdb_name: str = Field(..., alias='cdbName', description='Gets the cdb_name of this DatabaseConfigurationSummary.\nName of the CDB.Only applies to PDB.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseConfigurationSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    is_heat_wave_cluster_attached: bool = Field(..., alias='isHeatWaveClusterAttached', description='Specifies if MYSQL DB System has heatwave cluster attached.')
    is_highly_available: bool = Field(..., alias='isHighlyAvailable', description='Specifies if MYSQL DB System is highly available.')
    shape_name: str = Field(..., alias='shapeName', description='The shape of the primary instances of MYSQL DB system. The shape determines resources allocated to a DB System - CPU cores\nand memory for VM shapes; CPU cores, memory and storage for non-VM shapes.')


class MySqlSqlStats(OpsiBaseModel):
    """MySql Sql Stats type object."""

    digest: str = Field(..., alias='digest', description='Unique SQL ID Digest for a MySql Statement.\nExample: `"c20fcea11911be36651b7ca7bd3712d4ed9ac1134cee9c6620039e1fb13b5eff"`')
    time_collected: datetime = Field(..., alias='timeCollected', description='Collection timestamp.\nExample: `"2020-03-31T00:00:00.000Z"`')
    command_type: str | None = Field(None, alias='commandType', description='Type of statement such as select, update or delete.')
    total_rows: int | None = Field(None, alias='totalRows', description='Total number of SQL statements used in collection ranking calculation.')
    perf_schema_used_percent: int | None = Field(None, alias='perfSchemaUsedPercent', description='Percent of SQL statements in the perf schema table relative to max or overflow count set in @@GLOBAL.performance_schema_digests_size.')
    schema_name: str | None = Field(None, alias='schemaName', description='Name of Database Schema.\nExample: `"performance_schema"`')
    exec_count: int | None = Field(None, alias='execCount', description='The total number of times the statement has executed.', ge=0)
    total_latency_in_ps: int | None = Field(None, alias='totalLatencyInPs', description='The total wait time (in picoseconds) of timed occurrences of the statement.')
    lock_latency_in_ps: int | None = Field(None, alias='lockLatencyInPs', description='The total time waiting (in picoseconds) for locks by timed occurrences of the statement.')
    err_count: int | None = Field(None, alias='errCount', description='The total number of errors produced by occurrences of the statement.', ge=0)
    warn_count: int | None = Field(None, alias='warnCount', description='The total number of warnings produced by occurrences of the statement.', ge=0)
    rows_affected: int | None = Field(None, alias='rowsAffected', description='The total number of rows affected by occurrences of the statement.')
    rows_sent: int | None = Field(None, alias='rowsSent', description='The total number of rows returned by occurrences of the statement.')
    rows_examined: int | None = Field(None, alias='rowsExamined', description='The total number of rows read from storage engines by occurrences of the statement.')
    tmp_disk_tables: int | None = Field(None, alias='tmpDiskTables', description='The total number of internal on-disk temporary tables created by occurrences of the statement.')
    tmp_tables: int | None = Field(None, alias='tmpTables', description='The total number of internal in-memory temporary tables created by occurrences of the statement Count')
    select_full_join: int | None = Field(None, alias='selectFullJoin', description='The total number of joins that perform table scans because they do not use indexes by occurrences of the statement. If this value is not 0')
    select_full_range_join: int | None = Field(None, alias='selectFullRangeJoin', description='The total number of joins that used a range search on a reference table by occurrences of the statement')
    select_range: int | None = Field(None, alias='selectRange', description='The total number of joins that used ranges on the first table by occurrences of the statement. This is normally not a critical issue even if the value is quite large. Count')
    select_range_check: int | None = Field(None, alias='selectRangeCheck', description='The total number of joins without keys that check for key usage after each row by occurrences of the statement. If this is not 0')
    select_scan: int | None = Field(None, alias='selectScan', description='The total number of joins that did a full scan of the first table by occurrences of the statement Count')
    sort_merge_passes: int | None = Field(None, alias='sortMergePasses', description='The total number of sort merge passes by occurrences of the statement.')
    sort_range: int | None = Field(None, alias='sortRange', description='The total number of sorts that were done using ranges by occurrences of the statement.')
    rows_sorted: int | None = Field(None, alias='rowsSorted', description='The total number of rows sorted by occurrences of the statement.')
    sort_scan: int | None = Field(None, alias='sortScan', description='The total number of sorts that were done by scanning the table by occurrences of the statement.')
    no_index_used_count: int | None = Field(None, alias='noIndexUsedCount', description='The number of occurences of the statement which performed a table scan without using an index Count', ge=0)
    no_good_index_used_count: int | None = Field(None, alias='noGoodIndexUsedCount', description='The number of occurences of the statement where the server found no good index to use Count', ge=0)
    cpu_latency_in_ps: int | None = Field(None, alias='cpuLatencyInPs', description='The total time spent on CPU (in picoseconds) for the current thread.')
    max_controlled_memory_in_bytes: int | None = Field(None, alias='maxControlledMemoryInBytes', description='The maximum amount of controlled memory (in bytes) used by the statement.')
    max_total_memory_in_bytes: int | None = Field(None, alias='maxTotalMemoryInBytes', description='The maximum amount of memory (in bytes) used by the statement.')
    exec_count_secondary: int | None = Field(None, alias='execCountSecondary', description='The total number of times a query was processed on the secondary engine (HEATWAVE) for occurrences of this statement Count.')
    time_first_seen: datetime | None = Field(None, alias='timeFirstSeen', description='The time at which statement was first seen.\nExample: `"2023-01-16 08:04:31.533577"`')
    time_last_seen: datetime | None = Field(None, alias='timeLastSeen', description='The time at which statement was most recently seen for all occurrences of the statement.\nExample: `"2023-01-30 02:17:08.067961"`')


class MySqlSqlText(OpsiBaseModel):
    """MySql SQL Text type object."""

    schema_name: str | None = Field(None, alias='schemaName', description='Name of Database Schema.\nExample: `"performance_schema"`')
    digest: str = Field(..., alias='digest', description='digest\nExample: `"323k3k99ua09a90adf"`')
    time_collected: datetime = Field(..., alias='timeCollected', description='Collection timestamp.\nExample: `"2020-05-06T00:00:00.000Z"`')
    command_type: str | None = Field(None, alias='commandType', description='SQL event name\nExample: `"SELECT"`')
    digest_text: str = Field(..., alias='digestText', description='The normalized statement string.\nExample: `"SELECT username,profile,default_tablespace,temporary_tablespace FROM dba_users"`')


class NetworkUsageTrend(OpsiBaseModel):
    """Usage data samples."""

    end_timestamp: datetime = Field(..., alias='endTimestamp', description='The timestamp in which the current sampling period ends in RFC 3339 format.')
    all_network_read_in_mbps: float = Field(..., alias='allNetworkReadInMbps', description='Network read in Mbps.')
    all_network_write_in_mbps: float = Field(..., alias='allNetworkWriteInMbps', description='Network write in Mbps.')
    all_network_io_in_mbps: float = Field(..., alias='allNetworkIoInMbps', description='Network input/output in Mbps.')


class NetworkUsageTrendAggregation(OpsiBaseModel):
    """Usage data per network interface."""

    interface_name: str = Field(..., alias='interfaceName', description='Name of interface.')
    ip_address: str = Field(..., alias='ipAddress', description='Address that is connected to a computer network that uses the Internet Protocol for communication.')
    mac_address: str = Field(..., alias='macAddress', description='Unique identifier assigned to a network interface.')
    usage_data: list[NetworkUsageTrend] = Field(..., alias='usageData', description='List of usage data samples for a network interface.')


class NewsContentTypes(OpsiBaseModel):
    """Content types that the news report can handle."""

    capacity_planning_resources: list[Any] | None = Field(None, alias='capacityPlanningResources', description='Supported resources for capacity planning content type.')
    sql_insights_fleet_analysis_resources: list[Any] | None = Field(None, alias='sqlInsightsFleetAnalysisResources', description='Supported resources for SQL insights - fleet analysis content type.')
    sql_insights_plan_changes_resources: list[Any] | None = Field(None, alias='sqlInsightsPlanChangesResources', description='Supported resources for SQL insights - plan changes content type.')
    sql_insights_top_databases_resources: list[Any] | None = Field(None, alias='sqlInsightsTopDatabasesResources', description='Supported resources for SQL insights - top databases content type.')
    sql_insights_top_sql_by_insights_resources: list[Any] | None = Field(None, alias='sqlInsightsTopSqlByInsightsResources', description='Supported resources for SQL insights - top SQL by insights content type.')
    sql_insights_top_sql_resources: list[Any] | None = Field(None, alias='sqlInsightsTopSqlResources', description='Supported resources for SQL insights - top SQL content type.')
    sql_insights_performance_degradation_resources: list[Any] | None = Field(None, alias='sqlInsightsPerformanceDegradationResources', description='Supported resources for SQL insights - performance degradation content type.')
    actionable_insights_resources: list[Any] | None = Field(None, alias='actionableInsightsResources', description='Supported resources for actionable insights content type.')


class NewsReport(OpsiBaseModel):
    """News report resource."""

    news_frequency: Literal['WEEKLY', 'DAILY', 'HOURLY', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='newsFrequency', description='News report frequency.\n\nAllowed values for this property are: "WEEKLY", "DAILY", "HOURLY", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    content_types: NewsContentTypes = Field(..., alias='contentTypes', description='The content_types field of NewsReport.')
    locale: Literal['EN', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='locale', description='Language of the news report.\n\nAllowed values for this property are: "EN", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='The OCID of the news report resource.')
    description: str | None = Field(None, alias='description', description='The description of the news report.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    name: str | None = Field(None, alias='name', description='The news report name.')
    ons_topic_id: str = Field(..., alias='onsTopicId', description='The OCID of the ONS topic.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Indicates the status of a news report in Ops Insights.\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='The time the the news report was first enabled. An RFC3339 formatted datetime string.')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time the news report was updated. An RFC3339 formatted datetime string.')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='The current state of the news report.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    day_of_week: Literal['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='dayOfWeek', description='Day of the week in which the news report will be sent if the frequency is set to WEEKLY.\n\nAllowed values for this property are: "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    are_child_compartments_included: bool | None = Field(None, alias='areChildCompartmentsIncluded', description='A flag to consider the resources within a given compartment and all sub-compartments.')
    tag_filters: list[str] | None = Field(None, alias='tagFilters', description="List of tag filters; each filter composed by a namespace, key, and value.\nExample for defined tags - '<TagNamespace>.<TagKey>=<TagValue>'.\nExample for freeform tags - '<TagKey>=<TagValue>'.")
    match_rule: Literal['MATCH_ANY', 'MATCH_ALL', 'MATCH_NONE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='matchRule', description='Match rule used for tag filters.\n\nAllowed values for this property are: "MATCH_ANY", "MATCH_ALL", "MATCH_NONE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class NewsReportCollection(OpsiBaseModel):
    """Collection of news reports summary objects."""

    items: list[NewsReportSummary] = Field(..., alias='items', description='Array of news reports summary objects.')


class NewsReportSummary(OpsiBaseModel):
    """Summary of a news report resource."""

    news_frequency: Literal['WEEKLY', 'DAILY', 'HOURLY', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='newsFrequency', description='News report frequency.\n\nAllowed values for this property are: "WEEKLY", "DAILY", "HOURLY", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    content_types: NewsContentTypes = Field(..., alias='contentTypes', description='The content_types field of NewsReportSummary.')
    locale: Literal['EN', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='locale', description='Language of the news report.\n\nAllowed values for this property are: "EN", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='The OCID of the news report resource.')
    description: str | None = Field(None, alias='description', description='The description of the news report.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    name: str | None = Field(None, alias='name', description='The news report name.')
    ons_topic_id: str | None = Field(None, alias='onsTopicId', description='The OCID of the ONS topic.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Indicates the status of a news report in Ops Insights.\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='The time the the news report was first enabled. An RFC3339 formatted datetime string.')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time the news report was updated. An RFC3339 formatted datetime string.')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='The current state of the news report.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    day_of_week: Literal['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='dayOfWeek', description='Day of the week in which the news report will be sent if the frequency is set to WEEKLY.\n\nAllowed values for this property are: "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    are_child_compartments_included: bool | None = Field(None, alias='areChildCompartmentsIncluded', description='A flag to consider the resources within a given compartment and all sub-compartments.')
    tag_filters: list[str] | None = Field(None, alias='tagFilters', description="List of tag filters; each filter composed by a namespace, key, and value.\nExample for defined tags - '<TagNamespace>.<TagKey>=<TagValue>'.\nExample for freeform tags - '<TagKey>=<TagValue>'.")
    match_rule: Literal['MATCH_ANY', 'MATCH_ALL', 'MATCH_NONE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='matchRule', description='Match rule used for tag filters.\n\nAllowed values for this property are: "MATCH_ANY", "MATCH_ALL", "MATCH_NONE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class NewsReports(OpsiBaseModel):
    """Logical grouping used for Operations Insights news reports related operations."""

    news_reports: Any | None = Field(None, alias='newsReports', description='News report object.')


class ObjectSummary(OpsiBaseModel):
    """Summary resource object."""

    name: str | None = Field(None, alias='name', description='The name of the Awr Hub object.')
    size: int | None = Field(None, alias='size', description='Size of the Awr Hub object in bytes.')
    md5: str | None = Field(None, alias='md5', description='Base64-encoded MD5 hash of the Awr Hub object data.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='The time at which the resource was first created. An RFC3339 formatted datetime string')
    etag: str | None = Field(None, alias='etag', description='For optimistic concurrency control. See `if-match`.')
    storage_tier: Literal['STANDARD', 'INFREQUENTACCESS', 'ARCHIVE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='storageTier', description='The object\'s storage tier.\n\nAllowed values for this property are: "STANDARD", "INFREQUENTACCESS", "ARCHIVE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    archival_state: Literal['ARCHIVED', 'RESTORING', 'RESTORED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='archivalState', description='Archival state of an object for those in the archival tier.\n\nAllowed values for this property are: "ARCHIVED", "RESTORING", "RESTORED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_modified: datetime | None = Field(None, alias='timeModified', description='The date and time the Awr Hub object was modified')


class OperationsInsightsPrivateEndpoint(OpsiBaseModel):
    """A private endpoint that allows Operation Insights services to connect to databases in a customer's virtual cloud network (VCN)."""

    id: str = Field(..., alias='id', description='The OCID of the Private service accessed database.')
    display_name: str = Field(..., alias='displayName', description='The display name of the private endpoint.')
    compartment_id: str = Field(..., alias='compartmentId', description='The compartment OCID of the Private service accessed database.')
    vcn_id: str = Field(..., alias='vcnId', description='The OCID of the VCN.')
    subnet_id: str = Field(..., alias='subnetId', description='The OCID of the subnet.')
    private_ip: str | None = Field(None, alias='privateIp', description='The private IP addresses assigned to the private endpoint. All IP addresses will be concatenated if it is RAC DBs.')
    description: str | None = Field(None, alias='description', description='The description of the private endpoint.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='The date and time the private endpoint was created, in the format defined by RFC3339.')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='The current state of the private endpoint.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    private_endpoint_status_details: str | None = Field(None, alias='privateEndpointStatusDetails', description='A message describing the status of the private endpoint connection of this resource. For example, it can be used to provide actionable information about the validity of the private endpoint connection.')
    is_used_for_rac_dbs: bool | None = Field(None, alias='isUsedForRacDbs', description='The flag is to identify if private endpoint is used for rac database or not. This flag is deprecated and no longer is used.')
    nsg_ids: list[str] | None = Field(None, alias='nsgIds', description='The OCIDs of the network security groups that the private endpoint belongs to.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')


class OperationsInsightsPrivateEndpointCollection(OpsiBaseModel):
    """A collection of Operation Insights private endpoint objects."""

    items: list[OperationsInsightsPrivateEndpointSummary] = Field(..., alias='items', description='A list of OperationsInsightsPrivateEndpointSummary objects.')


class OperationsInsightsPrivateEndpointSummary(OpsiBaseModel):
    """Summary of a Operation Insights private endpoint."""

    id: str = Field(..., alias='id', description='The OCID of the Private service accessed database.')
    display_name: str = Field(..., alias='displayName', description='The display name of the private endpoint.')
    compartment_id: str = Field(..., alias='compartmentId', description='The compartment OCID of the Private service accessed database.')
    vcn_id: str = Field(..., alias='vcnId', description='The OCID of the VCN.')
    subnet_id: str = Field(..., alias='subnetId', description='The OCID of the subnet.')
    is_used_for_rac_dbs: bool | None = Field(None, alias='isUsedForRacDbs', description='The flag to identify if private endpoint is used for rac database or not. This flag is deprecated and no longer is used.')
    description: str | None = Field(None, alias='description', description='The description of the private endpoint.')
    time_created: datetime = Field(..., alias='timeCreated', description='The date and time the private endpoint was created, in the format defined by RFC3339.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Private endpoint lifecycle states\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    private_endpoint_status_details: str | None = Field(None, alias='privateEndpointStatusDetails', description='A message describing the status of the private endpoint connection of this resource. For example, it can be used to provide actionable information about the validity of the private endpoint connection.')


class OperationsInsightsWarehouse(OpsiBaseModel):
    """OPSI warehouse resource."""

    id: str = Field(..., alias='id', description='OPSI Warehouse OCID')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    display_name: str = Field(..., alias='displayName', description='User-friedly name of Ops Insights Warehouse that does not have to be unique.')
    cpu_allocated: float = Field(..., alias='cpuAllocated', description='Number of CPUs allocated to OPSI Warehouse ADW.')
    compute_model: Literal['OCPU', 'ECPU', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='computeModel', description='The compute model for the OPSI warehouse ADW (OCPU or ECPU)\n\nAllowed values for this property are: "OCPU", "ECPU", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    cpu_used: float | None = Field(None, alias='cpuUsed', description='Number of OCPUs used by OPSI Warehouse ADW. Can be fractional.')
    storage_allocated_in_gbs: float | None = Field(None, alias='storageAllocatedInGBs', description='Storage allocated to OPSI Warehouse ADW.')
    storage_used_in_gbs: float | None = Field(None, alias='storageUsedInGBs', description='Storage by OPSI Warehouse ADW in GB.')
    dynamic_group_id: str | None = Field(None, alias='dynamicGroupId', description='OCID of the dynamic group created for the warehouse')
    operations_insights_tenancy_id: str | None = Field(None, alias='operationsInsightsTenancyId', description='Tenancy Identifier of Ops Insights service')
    time_last_wallet_rotated: datetime | None = Field(None, alias='timeLastWalletRotated', description='The time at which the ADW wallet was last rotated for the Ops Insights Warehouse. An RFC3339 formatted datetime string')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='The time at which the resource was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time at which the resource was last updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Possible lifecycle states\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')


class OperationsInsightsWarehouseSummary(OpsiBaseModel):
    """Summary of a Operations Insights Warehouse resource."""

    id: str = Field(..., alias='id', description='OPSI Warehouse OCID')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    display_name: str = Field(..., alias='displayName', description='User-friedly name of Ops Insights Warehouse that does not have to be unique.')
    cpu_allocated: float = Field(..., alias='cpuAllocated', description='Number of CPUs allocated to OPSI Warehouse ADW.')
    compute_model: str | None = Field(None, alias='computeModel', description='The compute model for the OPSI warehouse ADW (OCPU or ECPU)')
    cpu_used: float | None = Field(None, alias='cpuUsed', description='Number of OCPUs used by OPSI Warehouse ADW. Can be fractional.')
    storage_allocated_in_gbs: float | None = Field(None, alias='storageAllocatedInGBs', description='Storage allocated to OPSI Warehouse ADW.')
    storage_used_in_gbs: float | None = Field(None, alias='storageUsedInGBs', description='Storage by OPSI Warehouse ADW in GB.')
    dynamic_group_id: str | None = Field(None, alias='dynamicGroupId', description='OCID of the dynamic group created for the warehouse')
    operations_insights_tenancy_id: str | None = Field(None, alias='operationsInsightsTenancyId', description='Tenancy Identifier of Ops Insights service')
    time_last_wallet_rotated: datetime | None = Field(None, alias='timeLastWalletRotated', description='The time at which the ADW wallet was last rotated for the Ops Insights Warehouse. An RFC3339 formatted datetime string')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='The time at which the resource was first created. An RFC3339 formatted datetime string')
    time_updated: datetime = Field(..., alias='timeUpdated', description='The time at which the resource was last updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Possible lifecycle states\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')


class OperationsInsightsWarehouseSummaryCollection(OpsiBaseModel):
    """Collection of Operations Insights Warehouse summary objects."""

    items: list[OperationsInsightsWarehouseSummary] = Field(..., alias='items', description='Array of Operations Insights Warehouse summary objects.')


class OperationsInsightsWarehouseUser(OpsiBaseModel):
    """OPSI warehouse User."""

    operations_insights_warehouse_id: str = Field(..., alias='operationsInsightsWarehouseId', description='OPSI Warehouse OCID')
    id: str = Field(..., alias='id', description='Hub User OCID')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    name: str = Field(..., alias='name', description='Username for schema which would have access to AWR Data,  Enterprise Manager Data and Ops Insights OPSI Hub.')
    connection_password: str | None = Field(None, alias='connectionPassword', description='User provided connection password for the AWR Data,  Enterprise Manager Data and Ops Insights OPSI Hub.')
    is_awr_data_access: bool = Field(..., alias='isAwrDataAccess', description='Indicate whether user has access to AWR data.')
    is_em_data_access: bool | None = Field(None, alias='isEmDataAccess', description='Indicate whether user has access to EM data.')
    is_opsi_data_access: bool | None = Field(None, alias='isOpsiDataAccess', description='Indicate whether user has access to OPSI data.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='The time at which the resource was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time at which the resource was last updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Possible lifecycle states\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')


class OperationsInsightsWarehouseUserSummary(OpsiBaseModel):
    """Summary of a Operations Insights Warehouse User."""

    operations_insights_warehouse_id: str = Field(..., alias='operationsInsightsWarehouseId', description='OPSI Warehouse OCID')
    id: str = Field(..., alias='id', description='Hub User OCID')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    name: str = Field(..., alias='name', description='Username for schema which would have access to AWR Data,  Enterprise Manager Data and Ops Insights OPSI Hub.')
    connection_password: str | None = Field(None, alias='connectionPassword', description='User provided connection password for the AWR Data,  Enterprise Manager Data and Ops Insights OPSI Hub.')
    is_awr_data_access: bool = Field(..., alias='isAwrDataAccess', description='Indicate whether user has access to AWR data.')
    is_em_data_access: bool | None = Field(None, alias='isEmDataAccess', description='Indicate whether user has access to EM data.')
    is_opsi_data_access: bool | None = Field(None, alias='isOpsiDataAccess', description='Indicate whether user has access to OPSI data.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='The time at which the resource was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time at which the resource was last updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Possible lifecycle states\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')


class OperationsInsightsWarehouseUserSummaryCollection(OpsiBaseModel):
    """Collection of Operations Insights Warehouse User summary objects."""

    items: list[OperationsInsightsWarehouseUserSummary] = Field(..., alias='items', description='Array of Operations Insights Warehouse user summary objects.')


class OperationsInsightsWarehouseUsers(OpsiBaseModel):
    """Logical grouping used for Operations Insights Warehouse User operations."""

    operations_insights_warehouse_users: Any | None = Field(None, alias='operationsInsightsWarehouseUsers', description='Operations Insights Warehouse User Object.')


class OperationsInsightsWarehouses(OpsiBaseModel):
    """Logical grouping used for Ops Insights Warehouse operations."""

    operations_insights_warehouses: Any | None = Field(None, alias='operationsInsightsWarehouses', description='Ops Insights Warehouse Object.')


class OpsiConfiguration(OpsiBaseModel):
    """OPSI configuration."""

    id: str | None = Field(None, alias='id', description='OCID of OPSI configuration resource.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='The OCID of the compartment.')
    opsi_config_type: Literal['UX_CONFIGURATION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='opsiConfigType', description='OPSI configuration type.\n\nAllowed values for this property are: "UX_CONFIGURATION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description='User-friendly display name for the OPSI configuration. The name does not have to be unique.')
    description: str | None = Field(None, alias='description', description='Description of OPSI configuration.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime | None = Field(None, alias='timeCreated', description='The time at which the resource was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time at which the resource was last updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='OPSI configuration resource lifecycle state.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    config_items: list[OpsiConfigurationConfigurationItemSummary] | None = Field(None, alias='configItems', description='Array of configuration item summary objects.')


class OpsiConfigurationBasicConfigurationItemSummary(OpsiBaseModel):
    """Basic configuration item summary. Value and defaultValue fields will contain the custom value stored in the resource and default value from Ops Insights respectively."""

    config_item_type: Literal['BASIC', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='configItemType', description='Gets the config_item_type of this OpsiConfigurationConfigurationItemSummary.\nType of configuration item.\n\nAllowed values for this property are: "BASIC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    name: str | None = Field(None, alias='name', description='Name of configuration item.')
    value: str | None = Field(None, alias='value', description='Value of configuration item.')
    default_value: str | None = Field(None, alias='defaultValue', description='Value of configuration item.')
    applicable_contexts: list[str] | None = Field(None, alias='applicableContexts', description='List of contexts in Operations Insights where this configuration item is applicable.')
    metadata: ConfigurationItemMetadata | None = Field(None, alias='metadata', description='The metadata field of OpsiConfigurationBasicConfigurationItemSummary.')


class OpsiConfigurationConfigurationItemSummary(OpsiBaseModel):
    """Configuration item summary."""

    config_item_type: Literal['BASIC', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='configItemType', description='Type of configuration item.\n\nAllowed values for this property are: "BASIC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class OpsiConfigurationSummary(OpsiBaseModel):
    """OPSI configuration summary."""

    id: str | None = Field(None, alias='id', description='OCID of OPSI configuration resource.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='The OCID of the compartment.')
    opsi_config_type: Literal['UX_CONFIGURATION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='opsiConfigType', description='OPSI configuration type.\n\nAllowed values for this property are: "UX_CONFIGURATION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description='User-friendly display name for the OPSI configuration. The name does not have to be unique.')
    description: str | None = Field(None, alias='description', description='Description of OPSI configuration.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Simple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Defined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='System tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime | None = Field(None, alias='timeCreated', description='The time at which the resource was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='The time at which the resource was last updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='OPSI configuration resource lifecycle state.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='A message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')


class OpsiConfigurations(OpsiBaseModel):
    """An OPSI configuration resource is a container for storing custom values for customizable configuration items exposed by Operations Insights."""

    opsi_configurations: Any | None = Field(None, alias='opsiConfigurations', description='OPSI Configuration Object.')


class OpsiConfigurationsCollection(OpsiBaseModel):
    """Collection of OPSI configuration summary objects."""

    items: list[OpsiConfigurationSummary] = Field(..., alias='items', description='Array of OPSI configuration summary objects.')


class OpsiDataObject(OpsiBaseModel):
    """OPSI data object."""

    identifier: str = Field(..., alias='identifier', description='Unique identifier of OPSI data object.')
    data_object_type: Literal['DATABASE_INSIGHTS_DATA_OBJECT', 'HOST_INSIGHTS_DATA_OBJECT', 'EXADATA_INSIGHTS_DATA_OBJECT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='dataObjectType', description='Type of OPSI data object.\n\nAllowed values for this property are: "DATABASE_INSIGHTS_DATA_OBJECT", "HOST_INSIGHTS_DATA_OBJECT", "EXADATA_INSIGHTS_DATA_OBJECT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str = Field(..., alias='displayName', description='User-friendly name of OPSI data object.')
    description: str | None = Field(None, alias='description', description='Description of OPSI data object.')
    name: str | None = Field(None, alias='name', description='Name of the data object, which can be used in data object queries just like how view names are used in a query.')
    group_names: list[str] | None = Field(None, alias='groupNames', description='Names of all the groups to which the data object belongs to.')
    supported_query_time_period: str | None = Field(None, alias='supportedQueryTimePeriod', description='Time period supported by the data object for quering data.\nTime period is in ISO 8601 format with respect to current time. Default is last 30 days represented by P30D.\nExamples: P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months).')
    columns_metadata: list[DataObjectColumnMetadata] = Field(..., alias='columnsMetadata', description='Metadata of columns in a data object.')
    supported_query_params: list[OpsiDataObjectSupportedQueryParam] | None = Field(None, alias='supportedQueryParams', description='Supported query parameters by this OPSI data object that can be configured while a data object query involving this data object is executed.')


class OpsiDataObjectDetailsInQuery(OpsiBaseModel):
    """Details for OPSI data object used in a data object query."""

    data_object_details_target: Literal['INDIVIDUAL_OPSIDATAOBJECT', 'OPSIDATAOBJECTTYPE_OPSIDATAOBJECTS'] = Field(..., alias='dataObjectDetailsTarget', description='Data objects to which this OpsiDataObjectDetailsInQuery is applicable.\n\nAllowed values for this property are: "INDIVIDUAL_OPSIDATAOBJECT", "OPSIDATAOBJECTTYPE_OPSIDATAOBJECTS"')
    query_params: list[OpsiDataObjectQueryParam] | None = Field(None, alias='queryParams', description='An array of query parameters to be applied, for the OPSI data objects targetted by dataObjectDetailsTarget, before executing the query.\nRefer to supportedQueryParams of OpsiDataObject for the supported query parameters.')


class OpsiDataObjectQueryParam(OpsiBaseModel):
    """Details for a query parameter to be applied on an OPSI data object, when a data object query is executed."""

    name: str = Field(..., alias='name', description='Name of the query parameter.')
    value: Any = Field(..., alias='value', description='Value for the query parameter.')


class OpsiDataObjectSummary(OpsiBaseModel):
    """Summary of an OPSI data object."""

    identifier: str = Field(..., alias='identifier', description='Unique identifier of OPSI data object.')
    data_object_type: Literal['DATABASE_INSIGHTS_DATA_OBJECT', 'HOST_INSIGHTS_DATA_OBJECT', 'EXADATA_INSIGHTS_DATA_OBJECT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='dataObjectType', description='Type of OPSI data object.\n\nAllowed values for this property are: "DATABASE_INSIGHTS_DATA_OBJECT", "HOST_INSIGHTS_DATA_OBJECT", "EXADATA_INSIGHTS_DATA_OBJECT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str = Field(..., alias='displayName', description='User-friendly name of OPSI data object.')
    description: str | None = Field(None, alias='description', description='Description of OPSI data object.')
    name: str | None = Field(None, alias='name', description='Name of the data object, which can be used in data object queries just like how view names are used in a query.')
    group_names: list[str] | None = Field(None, alias='groupNames', description='Names of all the groups to which the data object belongs to.')


class OpsiDataObjectSupportedQueryParam(OpsiBaseModel):
    """Details of query parameter supported by an OPSI data object."""

    name: str = Field(..., alias='name', description='Name of the query parameter.')
    description: str | None = Field(None, alias='description', description='Description of the query parameter.')
    data_type: str | None = Field(None, alias='dataType', description='Data type of the for the query parameter.')


class OpsiDataObjectTypeOpsiDataObjectDetailsInQuery(OpsiBaseModel):
    """Details applicable for all OPSI data objects of a specific OpsiDataObjectType used in a data object query."""

    data_object_details_target: Literal['INDIVIDUAL_OPSIDATAOBJECT', 'OPSIDATAOBJECTTYPE_OPSIDATAOBJECTS'] = Field(..., alias='dataObjectDetailsTarget', description='Gets the data_object_details_target of this OpsiDataObjectDetailsInQuery.\nData objects to which this OpsiDataObjectDetailsInQuery is applicable.\n\nAllowed values for this property are: "INDIVIDUAL_OPSIDATAOBJECT", "OPSIDATAOBJECTTYPE_OPSIDATAOBJECTS"')
    query_params: list[OpsiDataObjectQueryParam] | None = Field(None, alias='queryParams', description='Gets the _query_params of this OpsiDataObjectDetailsInQuery.\nAn array of query parameters to be applied, for the OPSI data objects targetted by dataObjectDetailsTarget, before executing the query.\nRefer to supportedQueryParams of OpsiDataObject for the supported query parameters.')
    data_object_type: Literal['DATABASE_INSIGHTS_DATA_OBJECT', 'HOST_INSIGHTS_DATA_OBJECT', 'EXADATA_INSIGHTS_DATA_OBJECT'] = Field(..., alias='dataObjectType', description='Type of OPSI data object.\n\nAllowed values for this property are: "DATABASE_INSIGHTS_DATA_OBJECT", "HOST_INSIGHTS_DATA_OBJECT", "EXADATA_INSIGHTS_DATA_OBJECT"')


class OpsiDataObjects(OpsiBaseModel):
    """Logical grouping used for OPSI data object targeted operations."""

    opsi_data_objects: Any | None = Field(None, alias='opsiDataObjects', description='OPSI Data Object.')


class OpsiDataObjectsCollection(OpsiBaseModel):
    """Collection of OPSI data object summary objects."""

    items: list[OpsiDataObjectSummary] = Field(..., alias='items', description='Array of OPSI data object summary objects.')


class OpsiDataStores(OpsiBaseModel):
    """Logical grouping used for Ops Insights Data Store operations."""

    opsi_data_stores: Any | None = Field(None, alias='opsiDataStores', description='OPSI Data Store Object.')


class OpsiUxConfiguration(OpsiBaseModel):
    """OPSI UX configuration."""

    id: str | None = Field(None, alias='id', description='Gets the id of this OpsiConfiguration. OCID of OPSI configuration resource.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='Gets the compartment_id of this OpsiConfiguration. The OCID of the compartment.')
    opsi_config_type: Literal['UX_CONFIGURATION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='opsiConfigType', description='Gets the opsi_config_type of this OpsiConfiguration.\nOPSI configuration type.\n\nAllowed values for this property are: "UX_CONFIGURATION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description='Gets the display_name of this OpsiConfiguration.\nUser-friendly display name for the OPSI configuration. The name does not have to be unique.')
    description: str | None = Field(None, alias='description', description='Gets the description of this OpsiConfiguration.\nDescription of OPSI configuration.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this OpsiConfiguration.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this OpsiConfiguration.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this OpsiConfiguration.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this OpsiConfiguration.\nThe time at which the resource was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this OpsiConfiguration.\nThe time at which the resource was last updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this OpsiConfiguration.\nOPSI configuration resource lifecycle state.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this OpsiConfiguration.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    config_items: list[OpsiConfigurationConfigurationItemSummary] | None = Field(None, alias='configItems', description='Gets the config_items of this OpsiConfiguration.\nArray of configuration item summary objects.')


class OpsiUxConfigurationSummary(OpsiBaseModel):
    """OPSI UX configuration summary."""

    id: str | None = Field(None, alias='id', description='Gets the id of this OpsiConfigurationSummary. OCID of OPSI configuration resource.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='Gets the compartment_id of this OpsiConfigurationSummary. The OCID of the compartment.')
    opsi_config_type: Literal['UX_CONFIGURATION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='opsiConfigType', description='Gets the opsi_config_type of this OpsiConfigurationSummary.\nOPSI configuration type.\n\nAllowed values for this property are: "UX_CONFIGURATION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    display_name: str | None = Field(None, alias='displayName', description='Gets the display_name of this OpsiConfigurationSummary.\nUser-friendly display name for the OPSI configuration. The name does not have to be unique.')
    description: str | None = Field(None, alias='description', description='Gets the description of this OpsiConfigurationSummary.\nDescription of OPSI configuration.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this OpsiConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this OpsiConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this OpsiConfigurationSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this OpsiConfigurationSummary.\nThe time at which the resource was first created. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this OpsiConfigurationSummary.\nThe time at which the resource was last updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this OpsiConfigurationSummary.\nOPSI configuration resource lifecycle state.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this OpsiConfigurationSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')


class OpsiWarehouseDataObjects(OpsiBaseModel):
    """Logical grouping used for Operations Insights Warehouse data objects operations."""

    opsi_warehouse_data_objects: Any | None = Field(None, alias='opsiWarehouseDataObjects', description='Operations Insights Warehouse Data Object.')


class PeComanagedDatabaseConnectionDetails(OpsiBaseModel):
    """Connection details of the private endpoints."""

    hosts: list[PeComanagedDatabaseHostDetails] = Field(..., alias='hosts', description='List of hosts and port for private endpoint accessed database resource.')
    protocol: Literal['TCP', 'TCPS', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='protocol', description='Protocol used for connection requests for private endpoint accssed database resource.\n\nAllowed values for this property are: "TCP", "TCPS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    service_name: str | None = Field(None, alias='serviceName', description='Database service name used for connection requests.')


class PeComanagedDatabaseHostDetails(OpsiBaseModel):
    """Input Host Details used for connection requests for private endpoint accessed db resource."""

    host_ip: str | None = Field(None, alias='hostIp', description='Host IP used for connection requests for Cloud DB resource.')
    port: int | None = Field(None, alias='port', description='Listener port number used for connection requests for rivate endpoint accessed db resource.')


class PeComanagedDatabaseInsight(OpsiBaseModel):
    """Database insight resource."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsight.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsight.\nDatabase insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseInsight.\nCompartment identifier of the database')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this DatabaseInsight.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsight.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsight.\nThe version of the database.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this DatabaseInsight.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsight.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsight.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsight.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    connection_details: PeComanagedDatabaseConnectionDetails | None = Field(None, alias='connectionDetails', description='The connection_details field of PeComanagedDatabaseInsight.')
    credential_details: CredentialDetails | None = Field(None, alias='credentialDetails', description='The credential_details field of PeComanagedDatabaseInsight.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    database_name: str = Field(..., alias='databaseName', description='Name of database')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Display name of database')
    database_resource_type: str = Field(..., alias='databaseResourceType', description='OCI database resource type')
    parent_id: str | None = Field(None, alias='parentId', description='The OCID of the VM Cluster or DB System ID, depending on which configuration the resource belongs to.')
    root_id: str | None = Field(None, alias='rootId', description='The OCID of the Exadata Infrastructure.')


class PeComanagedDatabaseInsightSummary(OpsiBaseModel):
    """Summary of a database insight resource."""

    id: str = Field(..., alias='id', description='Gets the id of this DatabaseInsightSummary. The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='Gets the database_id of this DatabaseInsightSummary. The OCID of the database.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='Gets the compartment_id of this DatabaseInsightSummary. The OCID of the compartment.')
    database_name: str | None = Field(None, alias='databaseName', description='Gets the database_name of this DatabaseInsightSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str | None = Field(None, alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseInsightSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str | None = Field(None, alias='databaseType', description='Gets the database_type of this DatabaseInsightSummary.\nOps Insights internal representation of the database type.')
    database_version: str | None = Field(None, alias='databaseVersion', description='Gets the database_version of this DatabaseInsightSummary.\nThe version of the database.')
    database_host_names: list[str] | None = Field(None, alias='databaseHostNames', description='Gets the database_host_names of this DatabaseInsightSummary.\nThe hostnames for the database.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this DatabaseInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this DatabaseInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this DatabaseInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseInsightSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this DatabaseInsightSummary.\nIndicates the status of a database insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this DatabaseInsightSummary.\nThe time the the database insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this DatabaseInsightSummary.\nThe time the database insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this DatabaseInsightSummary.\nThe current state of the database.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this DatabaseInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    database_connection_status_details: str | None = Field(None, alias='databaseConnectionStatusDetails', description='Gets the database_connection_status_details of this DatabaseInsightSummary.\nA message describing the status of the database connection of this resource. For example, it can be used to provide actionable information about the permission and content validity of the database connection.')
    database_resource_type: str | None = Field(None, alias='databaseResourceType', description='OCI database resource type')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    parent_id: str | None = Field(None, alias='parentId', description='The OCID of the VM Cluster or DB System ID, depending on which configuration the resource belongs to.')
    root_id: str | None = Field(None, alias='rootId', description='The OCID of the root resource for a composite target. e.g. for ExaCS members the rootId will be the OCID of the Exadata Infrastructure resource.')


class PeComanagedExadataInsight(OpsiBaseModel):
    """Private endpoint managed Exadata insight resource (ExaCS)."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this ExadataInsight.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this ExadataInsight.\nExadata insight identifier')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this ExadataInsight.\nCompartment identifier of the Exadata insight resource')
    exadata_name: str = Field(..., alias='exadataName', description='Gets the exadata_name of this ExadataInsight.\nThe Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str | None = Field(None, alias='exadataDisplayName', description='Gets the exadata_display_name of this ExadataInsight.\nThe user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataType', description='Gets the exadata_type of this ExadataInsight.\nOperations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataRackType', description='Gets the exadata_rack_type of this ExadataInsight.\nExadata rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    is_virtualized_exadata: bool | None = Field(None, alias='isVirtualizedExadata', description='Gets the is_virtualized_exadata of this ExadataInsight.\ntrue if virtualization is used in the Exadata system')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this ExadataInsight.\nIndicates the status of an Exadata insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    chargeback_plan_details: ChargebackPlanDetails | None = Field(None, alias='chargebackPlanDetails', description='Gets the chargeback_plan_details of this ExadataInsight.')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this ExadataInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this ExadataInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this ExadataInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this ExadataInsight.\nThe time the the Exadata insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this ExadataInsight.\nThe time the Exadata insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this ExadataInsight.\nThe current state of the Exadata insight.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this ExadataInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    status_details: str | None = Field(None, alias='statusDetails', description='Gets the status_details of this ExadataInsight.\nA message describing the status of the Exadata Resource. For example, it can be used to provide actionable information about the policies needed to access the Exadata Resource.')
    exadata_infra_id: str = Field(..., alias='exadataInfraId', description='The OCID of the Exadata Infrastructure.')
    exadata_infra_resource_type: Literal['cloudExadataInfrastructure', 'exadataInfrastructure', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataInfraResourceType', description='OCI exadata infrastructure resource type\n\nAllowed values for this property are: "cloudExadataInfrastructure", "exadataInfrastructure", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_shape: str = Field(..., alias='exadataShape', description='The shape of the Exadata Infrastructure.')


class PeComanagedExadataInsightSummary(OpsiBaseModel):
    """Summary of a Private endpoint managed Exadata insight resource (ExaCS)."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this ExadataInsightSummary.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this ExadataInsightSummary. The OCID of the Exadata insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this ExadataInsightSummary. The OCID of the compartment.')
    exadata_name: str = Field(..., alias='exadataName', description='Gets the exadata_name of this ExadataInsightSummary.\nThe Exadata system name. If the Exadata systems managed by Enterprise Manager, the name is unique amongst the Exadata systems managed by the same Enterprise Manager.')
    exadata_display_name: str | None = Field(None, alias='exadataDisplayName', description='Gets the exadata_display_name of this ExadataInsightSummary.\nThe user-friendly name for the Exadata system. The name does not have to be unique.')
    exadata_type: Literal['DBMACHINE', 'EXACS', 'EXACC', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataType', description='Gets the exadata_type of this ExadataInsightSummary.\nOperations Insights internal representation of the the Exadata system type.\n\nAllowed values for this property are: "DBMACHINE", "EXACS", "EXACC", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_rack_type: Literal['FULL', 'HALF', 'QUARTER', 'EIGHTH', 'FLEX', 'BASE', 'ELASTIC', 'ELASTIC_BASE', 'ELASTIC_LARGE', 'ELASTIC_EXTRA_LARGE', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='exadataRackType', description='Gets the exadata_rack_type of this ExadataInsightSummary.\nOperations Insights internal representation of the the Exadata system rack type.\n\nAllowed values for this property are: "FULL", "HALF", "QUARTER", "EIGHTH", "FLEX", "BASE", "ELASTIC", "ELASTIC_BASE", "ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this ExadataInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this ExadataInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this ExadataInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this ExadataInsightSummary.\nIndicates the status of an Exadata insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    chargeback_plan_details: ChargebackPlanDetails | None = Field(None, alias='chargebackPlanDetails', description='Gets the chargeback_plan_details of this ExadataInsightSummary.')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this ExadataInsightSummary.\nThe time the the Exadata insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this ExadataInsightSummary.\nThe time the Exadata insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this ExadataInsightSummary.\nThe current state of the Exadata insight.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this ExadataInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    status_details: str | None = Field(None, alias='statusDetails', description='Gets the status_details of this ExadataInsightSummary.\nA message describing the status of the Exadata Resource. For example, it can be used to provide actionable information about the policies needed to access the Exadata Resource.')
    exadata_infra_id: str = Field(..., alias='exadataInfraId', description='The OCID of the Exadata Infrastructure.')
    exadata_infra_resource_type: Literal['cloudExadataInfrastructure', 'exadataInfrastructure', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataInfraResourceType', description='OCI exadata infrastructure resource type\n\nAllowed values for this property are: "cloudExadataInfrastructure", "exadataInfrastructure", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_shape: str = Field(..., alias='exadataShape', description='The shape of the Exadata Infrastructure.')


class PeComanagedHostConfigurationSummary(OpsiBaseModel):
    """Configuration Summary of a PeComanaged host."""

    host_insight_id: str = Field(..., alias='hostInsightId', description='Gets the host_insight_id of this HostConfigurationSummary. The OCID of the host insight resource.')
    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostConfigurationSummary.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostConfigurationSummary. The OCID of the compartment.')
    host_name: str = Field(..., alias='hostName', description='Gets the host_name of this HostConfigurationSummary.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='platformType', description='Gets the platform_type of this HostConfigurationSummary.\nPlatform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    platform_version: str = Field(..., alias='platformVersion', description='Gets the platform_version of this HostConfigurationSummary.\nPlatform version.')
    platform_vendor: str = Field(..., alias='platformVendor', description='Gets the platform_vendor of this HostConfigurationSummary.\nPlatform vendor.')
    total_cpus: int = Field(..., alias='totalCpus', description='Gets the total_cpus of this HostConfigurationSummary.\nTotal CPU on this host.')
    total_memory_in_gbs: float = Field(..., alias='totalMemoryInGBs', description='Gets the total_memory_in_gbs of this HostConfigurationSummary.\nTotal amount of usable physical memory in gibabytes')
    cpu_architecture: str = Field(..., alias='cpuArchitecture', description='Gets the cpu_architecture of this HostConfigurationSummary.\nCPU architechure')
    cpu_cache_in_mbs: float = Field(..., alias='cpuCacheInMBs', description='Gets the cpu_cache_in_mbs of this HostConfigurationSummary.\nSize of cache memory in megabytes.')
    cpu_vendor: str = Field(..., alias='cpuVendor', description='Gets the cpu_vendor of this HostConfigurationSummary.\nName of the CPU vendor.')
    cpu_frequency_in_mhz: float = Field(..., alias='cpuFrequencyInMhz', description='Gets the cpu_frequency_in_mhz of this HostConfigurationSummary.\nClock frequency of the processor in megahertz.')
    cpu_implementation: str = Field(..., alias='cpuImplementation', description='Gets the cpu_implementation of this HostConfigurationSummary.\nModel name of processor.')
    cores_per_socket: int = Field(..., alias='coresPerSocket', description='Gets the cores_per_socket of this HostConfigurationSummary.\nNumber of cores per socket.')
    total_sockets: int = Field(..., alias='totalSockets', description='Gets the total_sockets of this HostConfigurationSummary.\nNumber of total sockets.')
    threads_per_socket: int = Field(..., alias='threadsPerSocket', description='Gets the threads_per_socket of this HostConfigurationSummary.\nNumber of threads per socket.')
    is_hyper_threading_enabled: bool = Field(..., alias='isHyperThreadingEnabled', description='Gets the is_hyper_threading_enabled of this HostConfigurationSummary.\nIndicates if hyper-threading is enabled or not')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this HostConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this HostConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    opsi_private_endpoint_id: str = Field(..., alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    parent_id: str = Field(..., alias='parentId', description='The OCID of the database.')
    exadata_details: ExadataDetails = Field(..., alias='exadataDetails', description='The exadata_details field of PeComanagedHostConfigurationSummary.')


class PeComanagedHostInsight(OpsiBaseModel):
    """Private Endpoint host insight resource."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostInsight.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this HostInsight. The OCID of the host insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostInsight. The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='Gets the host_name of this HostInsight.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='Gets the host_display_name of this HostInsight.\nThe user-friendly name for the host. The name does not have to be unique.')
    host_type: str | None = Field(None, alias='hostType', description='Gets the host_type of this HostInsight.\nOps Insights internal representation of the host type. Possible value is EXTERNAL-HOST.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this HostInsight.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this HostInsight.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this HostInsight.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this HostInsight.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Gets the status of this HostInsight.\nIndicates the status of a host insight in Operations Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime = Field(..., alias='timeCreated', description='Gets the time_created of this HostInsight.\nThe time the the host insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this HostInsight.\nThe time the host insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Gets the lifecycle_state of this HostInsight.\nThe current state of the host.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this HostInsight.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    opsi_private_endpoint_id: str = Field(..., alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    parent_id: str | None = Field(None, alias='parentId', description='The OCID of the VM Cluster or DB System ID, depending on which configuration the resource belongs to.')
    root_id: str | None = Field(None, alias='rootId', description='The OCID of the Exadata Infrastructure.')


class PeComanagedHostInsightSummary(OpsiBaseModel):
    """Summary of a Private Endpoint host insight resource."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this HostInsightSummary.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='Gets the id of this HostInsightSummary. The OCID of the host insight resource.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this HostInsightSummary. The OCID of the compartment.')
    host_name: str | None = Field(None, alias='hostName', description='Gets the host_name of this HostInsightSummary.\nThe host name. The host name is unique amongst the hosts managed by the same management agent.')
    host_display_name: str | None = Field(None, alias='hostDisplayName', description='Gets the host_display_name of this HostInsightSummary.\nThe user-friendly name for the host. The name does not have to be unique.')
    host_type: str | None = Field(None, alias='hostType', description='Gets the host_type of this HostInsightSummary.\nOps Insights internal representation of the host type. Possible value is EXTERNAL-HOST.')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this HostInsightSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this HostInsightSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this HostInsightSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this HostInsightSummary.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    opsi_private_endpoint_id: str | None = Field(None, alias='opsiPrivateEndpointId', description='Gets the opsi_private_endpoint_id of this HostInsightSummary. The OCID of the OPSI private endpoint.')
    status: Literal['DISABLED', 'ENABLED', 'TERMINATED', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='status', description='Gets the status of this HostInsightSummary.\nIndicates the status of a host insight in Ops Insights\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_created: datetime | None = Field(None, alias='timeCreated', description='Gets the time_created of this HostInsightSummary.\nThe time the the host insight was first enabled. An RFC3339 formatted datetime string')
    time_updated: datetime | None = Field(None, alias='timeUpdated', description='Gets the time_updated of this HostInsightSummary.\nThe time the host insight was updated. An RFC3339 formatted datetime string')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'NEEDS_ATTENTION', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='lifecycleState', description='Gets the lifecycle_state of this HostInsightSummary.\nThe current state of the host.\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", "NEEDS_ATTENTION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    lifecycle_details: str | None = Field(None, alias='lifecycleDetails', description='Gets the lifecycle_details of this HostInsightSummary.\nA message describing the current state in more detail. For example, can be used to provide actionable information for a resource in Failed state.')
    platform_type: Literal['LINUX', 'SOLARIS', 'SUNOS', 'ZLINUX', 'WINDOWS', 'AIX', 'HP_UX', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='platformType', description='Platform type.\nSupported platformType(s) for MACS-managed external host insight: [LINUX, SOLARIS, WINDOWS].\nSupported platformType(s) for MACS-managed cloud host insight: [LINUX].\nSupported platformType(s) for EM-managed external host insight: [LINUX, SOLARIS, SUNOS, ZLINUX, WINDOWS, AIX, HP-UX].\n\nAllowed values for this property are: "LINUX", "SOLARIS", "SUNOS", "ZLINUX", "WINDOWS", "AIX", "HP_UX", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    parent_id: str | None = Field(None, alias='parentId', description='The OCID of the VM Cluster or DB System ID, depending on which configuration the resource belongs to.')
    root_id: str | None = Field(None, alias='rootId', description='The OCID of the Exadata Infrastructure.')


class PeComanagedManagedExternalDatabaseConfigurationSummary(OpsiBaseModel):
    """Configuration Summary of a Private Endpoint Co-managed External database."""

    database_insight_id: str = Field(..., alias='databaseInsightId', description='Gets the database_insight_id of this DatabaseConfigurationSummary. The OCID of the database insight resource.')
    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='entitySource', description='Gets the entity_source of this DatabaseConfigurationSummary.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    compartment_id: str = Field(..., alias='compartmentId', description='Gets the compartment_id of this DatabaseConfigurationSummary. The OCID of the compartment.')
    database_name: str = Field(..., alias='databaseName', description='Gets the database_name of this DatabaseConfigurationSummary.\nThe database name. The database name is unique within the tenancy.')
    database_display_name: str = Field(..., alias='databaseDisplayName', description='Gets the database_display_name of this DatabaseConfigurationSummary.\nThe user-friendly name for the database. The name does not have to be unique.')
    database_type: str = Field(..., alias='databaseType', description='Gets the database_type of this DatabaseConfigurationSummary.\nOps Insights internal representation of the database type.')
    database_version: str = Field(..., alias='databaseVersion', description='Gets the database_version of this DatabaseConfigurationSummary.\nThe version of the database.')
    is_advanced_features_enabled: bool = Field(..., alias='isAdvancedFeaturesEnabled', description='Gets the is_advanced_features_enabled of this DatabaseConfigurationSummary.\nFlag is to identify if advanced features for autonomous database is enabled or not')
    cdb_name: str = Field(..., alias='cdbName', description='Gets the cdb_name of this DatabaseConfigurationSummary.\nName of the CDB.Only applies to PDB.')
    defined_tags: dict[str, dict[str, Any]] = Field(..., alias='definedTags', description='Gets the defined_tags of this DatabaseConfigurationSummary.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    freeform_tags: dict[str, str] = Field(..., alias='freeformTags', description='Gets the freeform_tags of this DatabaseConfigurationSummary.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    processor_count: int | None = Field(None, alias='processorCount', description='Gets the processor_count of this DatabaseConfigurationSummary.\nProcessor count. This is the OCPU count for Autonomous Database and CPU core count for other database types.', ge=0)
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    parent_id: str = Field(..., alias='parentId', description='The OCID of the database.')
    opsi_private_endpoint_id: str = Field(..., alias='opsiPrivateEndpointId', description='The OCID of the OPSI private endpoint.')
    instances: list[HostInstanceMap] = Field(..., alias='instances', description='Array of hostname and instance name.')
    exadata_details: ExadataDetails = Field(..., alias='exadataDetails', description='The exadata_details field of PeComanagedManagedExternalDatabaseConfigurationSummary.')


class ProjectedDataItem(OpsiBaseModel):
    """The timestamp of the projected event and their corresponding resource value. `highValue` and `lowValue` are the uncertainty bounds of the corresponding value."""

    end_timestamp: datetime = Field(..., alias='endTimestamp', description='The timestamp in which the current sampling period ends in RFC 3339 format.')
    usage: float = Field(..., alias='usage', description='Total amount used of the resource metric type (CPU, STORAGE).')
    high_value: float = Field(..., alias='highValue', description='Upper uncertainty bound of the current usage value.')
    low_value: float = Field(..., alias='lowValue', description='Lower uncertainty bound of the current usage value.')


class QueryDataObjectJsonResultSetRowsCollection(OpsiBaseModel):
    """Collection of result set rows from the data object query."""

    format: Literal['JSON', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='format', description='Gets the format of this QueryDataObjectResultSetRowsCollection.\nFormat type of data object query result set.\n\nAllowed values for this property are: "JSON", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[Any] = Field(..., alias='items', description='Array of result set rows.')
    items_metadata: list[QueryDataObjectResultSetColumnMetadata] = Field(..., alias='itemsMetadata', description='Array of QueryDataObjectResultSetColumnMetadata objects that describe the result set columns.')
    query_execution_time_in_seconds: float | None = Field(None, alias='queryExecutionTimeInSeconds', description='Time taken for executing the data object query (in seconds).\nConsider optimizing the query or reducing the target data range, if query execution time is longer.')


class QueryDataObjectResultSetColumnMetadata(OpsiBaseModel):
    """Metadata of a column in a data object query result set."""

    name: str = Field(..., alias='name', description='Name of the column in a data object query result set.')
    data_type: Literal['NUMBER', 'OTHER', 'TIMESTAMP', 'VARCHAR2'] | None = Field(None, alias='dataType', description='Type of the column in a data object query result.')
    data_type_name: Literal['NUMBER', 'TIMESTAMP', 'VARCHAR2', 'OTHER', 'UNKNOWN_ENUM_VALUE'] | None = Field(None, alias='dataTypeName', description='Type name of the column in a data object query result set.\n\nAllowed values for this property are: "NUMBER", "TIMESTAMP", "VARCHAR2", "OTHER", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class QueryDataObjectResultSetRowsCollection(OpsiBaseModel):
    """Collection of result set rows from the data object query."""

    format: Literal['JSON', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='format', description='Format type of data object query result set.\n\nAllowed values for this property are: "JSON", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class QueryOpsiDataObjectDataDetails(OpsiRequestModel):
    """Information required to form and execute query on an OPSI data object."""

    data_object_identifier: str | None = Field(None, alias='dataObjectIdentifier', description='Unique OPSI data object identifier.')
    data_objects: list[OpsiDataObjectDetailsInQuery] | None = Field(None, alias='dataObjects', description='Details of OPSI data objects used in the query.')
    query: DataObjectQuery = Field(..., alias='query', description='The query field of QueryOpsiDataObjectDataDetails.')
    resource_filters: ResourceFilters | None = Field(None, alias='resourceFilters', description='The resource_filters field of QueryOpsiDataObjectDataDetails.')


class QueryWarehouseDataObjectDataDetails(OpsiRequestModel):
    """Information required to form and execute Operations Insights Warehouse data objects query."""

    query: DataObjectQuery = Field(..., alias='query', description='The query field of QueryWarehouseDataObjectDataDetails.')


class RelatedObjectTypeDetails(OpsiBaseModel):
    """Related object details."""

    type: Literal['SCHEMA_OBJECT', 'SQL', 'DATABASE_PARAMETER', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='type', description='Type of related object\n\nAllowed values for this property are: "SCHEMA_OBJECT", "SQL", "DATABASE_PARAMETER", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class ReportGroupingDetails(OpsiBaseModel):
    """Report groupings."""

    key: str = Field(..., alias='key', description='Selected grouping key.')
    value: str = Field(..., alias='value', description='Selected grouping value.')


class ReportPropertyDetails(OpsiBaseModel):
    """Chargeback plan report properties."""

    analysis_time_interval: str = Field(..., alias='analysisTimeInterval', description='Specify time period in ISO 8601 format with respect to current time.\nIf timeInterval is specified, then timeIntervalStart and timeIntervalEnd will be ignored.\nExamples  P90D (last 90 days), P4W (last 4 weeks), P2M (last 2 months), P1Y (last 12 months),. Maximum value allowed is 25 months prior to current time (P25M).')
    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    group_by: Any = Field(..., alias='groupBy', description='Report filters used in grouping')


class ResourceCapacityTrendAggregation(OpsiBaseModel):
    """Resource Capacity samples."""

    end_timestamp: datetime = Field(..., alias='endTimestamp', description='The timestamp in which the current sampling period ends in RFC 3339 format.')
    capacity: float = Field(..., alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    base_capacity: float = Field(..., alias='baseCapacity', description='The base allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    total_host_capacity: float | None = Field(None, alias='totalHostCapacity', description='The maximum host CPUs (cores x threads/core) on the underlying infrastructure. This only applies to CPU and does not not apply for Autonomous Databases.')


class ResourceFilters(OpsiBaseModel):
    """Information to filter the actual target resources in an operation. e.g: While querying a DATABASE_INSIGHTS_DATA_OBJECT using /opsiDataObjects/actions/queryData API, if resourceFilters is set with valid value for definedTagEquals field, only data of the database insights resources for which the specified freeform tags exist will be considered for the actual query scope."""

    defined_tag_equals: list[str] | None = Field(None, alias='definedTagEquals', description='A list of tag filters to apply.  Only resources with a defined tag matching the value will be considered.\nEach item in the list has the format "{namespace}.{tagName}.{value}".  All inputs are case-insensitive.\nMultiple values for the same key (i.e. same namespace and tag name) are interpreted as "OR".\nValues for different keys (i.e. different namespaces, different tag names, or both) are interpreted as "AND".')
    freeform_tag_equals: list[str] | None = Field(None, alias='freeformTagEquals', description='A list of tag filters to apply.  Only resources with a freeform tag matching the value will be considered.\nThe key for each tag is "{tagName}.{value}".  All inputs are case-insensitive.\nMultiple values for the same tag name are interpreted as "OR".  Values for different tag names are interpreted as "AND".')
    defined_tag_exists: list[str] | None = Field(None, alias='definedTagExists', description='A list of tag existence filters to apply.  Only resources for which the specified defined tags exist will be considered.\nEach item in the list has the format "{namespace}.{tagName}.true" (for checking existence of a defined tag)\nor "{namespace}.true".  All inputs are case-insensitive.\nCurrently, only existence ("true" at the end) is supported. Absence ("false" at the end) is not supported.\nMultiple values for the same key (i.e. same namespace and tag name) are interpreted as "OR".\nValues for different keys (i.e. different namespaces, different tag names, or both) are interpreted as "AND".')
    freeform_tag_exists: list[str] | None = Field(None, alias='freeformTagExists', description='A list of tag existence filters to apply.  Only resources for which the specified freeform tags exist will be considered.\nThe key for each tag is "{tagName}.true".  All inputs are case-insensitive.\nCurrently, only existence ("true" at the end) is supported. Absence ("false" at the end) is not supported.\nMultiple values for different tag names are interpreted as "AND".')
    compartment_id_in_subtree: bool | None = Field(None, alias='compartmentIdInSubtree', description='A flag to consider all resources within a given compartment and all sub-compartments.')
    resource_status: list[str] | None = Field(None, alias='resourceStatus', description='Filter resources by status, multiple options could be chosen to show authorized resources even if those are disabled or deleted.\n\nAllowed values for items in this list are: "DISABLED", "ENABLED", "TERMINATED"')


class ResourceInsightCurrentUtilization(OpsiBaseModel):
    """Current utilization(High/low) for cpu or storage."""

    low: list[str] | None = Field(None, alias='low', description='List of db ids with low usage')
    high: list[str] | None = Field(None, alias='high', description='List of db ids with high usage')


class ResourceInsightProjectedUtilization(OpsiBaseModel):
    """Projected utilization(High/low) for cpu or storage."""

    low: list[ResourceInsightProjectedUtilizationItem] = Field(..., alias='low', description='List of db ids with low usage')
    high: list[ResourceInsightProjectedUtilizationItem] = Field(..., alias='high', description='List of db ids with high usage')


class ResourceInsightProjectedUtilizationItem(OpsiBaseModel):
    """Projected utilization object containing dbid and daysToReach value."""

    id: str = Field(..., alias='id', description='Db id')
    days_to_reach: int = Field(..., alias='daysToReach', description='Days to reach projected utilization')


class ResourceStatistics(OpsiBaseModel):
    """Contains resource statistics with usage unit."""

    usage: float = Field(..., alias='usage', description='Total amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    base_capacity: float | None = Field(None, alias='baseCapacity', description='The base allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    is_auto_scaling_enabled: bool | None = Field(None, alias='isAutoScalingEnabled', description='Indicates if auto scaling feature is enabled or disabled on a database. It will be false for all metrics other than CPU.')
    utilization_percent: float = Field(..., alias='utilizationPercent', description='Resource utilization in percentage')
    usage_change_percent: float = Field(..., alias='usageChangePercent', description='Change in resource utilization in percentage')
    instance_metrics: list[InstanceMetrics] | None = Field(None, alias='instanceMetrics', description='Array of instance metrics')
    total_host_capacity: float | None = Field(None, alias='totalHostCapacity', description='The maximum host CPUs (cores x threads/core) on the underlying infrastructure. This only applies to CPU and does not not apply for Autonomous Databases.')
    is_heat_wave_cluster_attached: bool | None = Field(None, alias='isHeatWaveClusterAttached', description='Specifies if MYSQL DB System has heatwave cluster attached.')
    is_highly_available: bool | None = Field(None, alias='isHighlyAvailable', description='Specifies if MYSQL DB System is highly available.')


class ResourceStatisticsAggregation(OpsiBaseModel):
    """Contains database details and resource statistics."""

    database_details: DatabaseDetails | None = Field(None, alias='databaseDetails', description='The database_details field of ResourceStatisticsAggregation.')
    current_statistics: ResourceStatistics | None = Field(None, alias='currentStatistics', description='The current_statistics field of ResourceStatisticsAggregation.')


class ResourceUsageSummary(OpsiBaseModel):
    """Contains resource usage summary."""

    exadata_insight_id: str = Field(..., alias='exadataInsightId', description='The OCID of the Exadata insight.')
    exadata_display_name: str | None = Field(None, alias='exadataDisplayName', description='The user-friendly name for the Exadata system. The name does not have to be unique.')
    usage: float = Field(..., alias='usage', description='Total amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    utilization_percent: float = Field(..., alias='utilizationPercent', description='Resource utilization in percentage')
    usage_change_percent: float = Field(..., alias='usageChangePercent', description='Change in resource utilization in percentage')
    total_host_capacity: float | None = Field(None, alias='totalHostCapacity', description='The maximum host CPUs (cores x threads/core) on the underlying infrastructure. This only applies to CPU and does not not apply for Autonomous Databases.')


class ResourceUsageTrendAggregation(OpsiBaseModel):
    """Aggregate usage samples."""

    end_timestamp: datetime = Field(..., alias='endTimestamp', description='The timestamp in which the current sampling period ends in RFC 3339 format.')
    usage: float = Field(..., alias='usage', description='Total amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    total_host_capacity: float | None = Field(None, alias='totalHostCapacity', description='The maximum host CPUs (cores x threads/core) on the underlying infrastructure. This only applies to CPU and does not not apply for Autonomous Databases.')


class SchemaObjectTypeDetails(OpsiBaseModel):
    """Schema object details."""

    type: Literal['SCHEMA_OBJECT', 'SQL', 'DATABASE_PARAMETER', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='type', description='Gets the type of this RelatedObjectTypeDetails.\nType of related object\n\nAllowed values for this property are: "SCHEMA_OBJECT", "SQL", "DATABASE_PARAMETER", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    object_id: int = Field(..., alias='objectId', description='Object id (from RDBMS)')
    owner: str = Field(..., alias='owner', description='Owner of object')
    object_name: str = Field(..., alias='objectName', description='Name of object')
    sub_object_name: str | None = Field(None, alias='subObjectName', description='Subobject name; for example, partition name')
    object_type: str = Field(..., alias='objectType', description='Type of the object (such as TABLE, INDEX)')


class SqlBucket(OpsiBaseModel):
    """Sql bucket type object."""

    version: float | None = Field(None, alias='version', description='Version\nExample: `1`')
    database_type: str | None = Field(None, alias='databaseType', description='Ops Insights internal representation of the database type.')
    time_collected: datetime = Field(..., alias='timeCollected', description='Collection timestamp\nExample: `"2020-03-31T00:00:00.000Z"`')
    sql_identifier: str = Field(..., alias='sqlIdentifier', description='Unique SQL_ID for a SQL Statement.')
    plan_hash: int = Field(..., alias='planHash', description='Plan hash value for the SQL Execution Plan')
    bucket_id: str = Field(..., alias='bucketId', description='SQL Bucket ID, examples <= 3 secs, 3-10 secs, 10-60 secs, 1-5 min, > 5 min\nExample: `"<= 3 secs"`')
    executions_count: int | None = Field(None, alias='executionsCount', description='Total number of executions\nExample: `60`', ge=0)
    cpu_time_in_sec: float | None = Field(None, alias='cpuTimeInSec', description='Total CPU time\nExample: `1046`')
    io_time_in_sec: float | None = Field(None, alias='ioTimeInSec', description='Total IO time\nExample: `5810`')
    other_wait_time_in_sec: float | None = Field(None, alias='otherWaitTimeInSec', description='Total other wait time\nExample: `24061`')
    total_time_in_sec: float | None = Field(None, alias='totalTimeInSec', description='Total time\nExample: `30917`')


class SqlInsightAggregation(OpsiBaseModel):
    """Represents a SQL Insight."""

    text: str = Field(..., alias='text', description='Insight text.\nFor example `Degrading SQLs`, `Variant SQLs`,\n`Inefficient SQLs`, `Improving SQLs`, `SQLs with Plan Changes`,\n`Degrading SQLs have increasing IO Time above 50%`,\n`Degrading SQLs are variant`,\n`2 of the 2 variant SQLs have plan changes`,\n`Inefficient SQLs have increasing CPU Time above 50%')
    values: list[int] = Field(..., alias='values', description='SQL counts for a given insight. For example insight text `2 of 10 SQLs have degrading response time` will have values as [2,10]"')
    category: str = Field(..., alias='category', description='Insight category. It would be one of the following\nDEGRADING,\nVARIANT,\nINEFFICIENT,\nCHANGING_PLANS,\nIMPROVING,\nDEGRADING_VARIANT,\nDEGRADING_INEFFICIENT,\nDEGRADING_CHANGING_PLANS,\nDEGRADING_INCREASING_IO,\nDEGRADING_INCREASING_CPU,\nDEGRADING_INCREASING_INEFFICIENT_WAIT,\nDEGRADING_CHANGING_PLANS_AND_INCREASING_IO,\nDEGRADING_CHANGING_PLANS_AND_INCREASING_CPU,\nDEGRADING_CHANGING_PLANS_AND_INCREASING_INEFFICIENT_WAIT,VARIANT_INEFFICIENT,\nVARIANT_CHANGING_PLANS,\nVARIANT_INCREASING_IO,\nVARIANT_INCREASING_CPU,\nVARIANT_INCREASING_INEFFICIENT_WAIT,\nVARIANT_CHANGING_PLANS_AND_INCREASING_IO,\nVARIANT_CHANGING_PLANS_AND_INCREASING_CPU,\nVARIANT_CHANGING_PLANS_AND_INCREASING_INEFFICIENT_WAIT,\nINEFFICIENT_CHANGING_PLANS,\nINEFFICIENT_INCREASING_INEFFICIENT_WAIT,\nINEFFICIENT_CHANGING_PLANS_AND_INCREASING_INEFFICIENT_WAIT')


class SqlInsightAggregationCollection(OpsiBaseModel):
    """SQL Insights response."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    inventory: SqlInventory = Field(..., alias='inventory', description='The inventory field of SqlInsightAggregationCollection.')
    items: list[SqlInsightAggregation] = Field(..., alias='items', description='List of insights.')
    thresholds: SqlInsightThresholds = Field(..., alias='thresholds', description='The thresholds field of SqlInsightAggregationCollection.')


class SqlInsightThresholds(OpsiBaseModel):
    """Inventory details."""

    degradation_in_pct: int = Field(..., alias='degradationInPct', description='Degradation Percent Threshold is used to derive degrading SQLs.')
    variability: float = Field(..., alias='variability', description='Variability Percent Threshold is used to derive variant SQLs.')
    inefficiency_in_pct: int = Field(..., alias='inefficiencyInPct', description='Inefficiency Percent Threshold is used to derive inefficient SQLs.')
    increase_in_io_in_pct: int = Field(..., alias='increaseInIOInPct', description='PctIncreaseInIO is used for deriving insights for SQLs which are degrading or\nvariant or inefficient. And these SQLs should also have increasing change in IO Time\nbeyond threshold. Insights are derived using linear regression.')
    increase_in_cpu_in_pct: int = Field(..., alias='increaseInCPUInPct', description='PctIncreaseInCPU is used for deriving insights for SQLs which are degrading or\nvariant or inefficient. And these SQLs should also have increasing change in CPU Time\nbeyond threshold. Insights are derived using linear regression.')
    increase_in_inefficient_wait_in_pct: int = Field(..., alias='increaseInInefficientWaitInPct', description='PctIncreaseInIO is used for deriving insights for SQLs which are degrading or\nvariant or inefficient. And these SQLs should also have increasing change in\nOther Wait Time beyond threshold. Insights are derived using linear regression.')
    improved_in_pct: int = Field(..., alias='improvedInPct', description='Improved Percent Threshold is used to derive improving SQLs.')


class SqlInventory(OpsiBaseModel):
    """Inventory details."""

    total_sqls: int = Field(..., alias='totalSqls', description='Total number of sqls. Example `2000`')
    total_databases: int = Field(..., alias='totalDatabases', description='Total number of Databases. Example `400`')
    sqls_analyzed: int = Field(..., alias='sqlsAnalyzed', description='Total number of sqls analyzed by the query. Example `120`')


class SqlPlanCollection(OpsiBaseModel):
    """SQL Plans for the particular SQL."""

    sql_identifier: str = Field(..., alias='sqlIdentifier', description='Unique SQL_ID for a SQL Statement.')
    id: str = Field(..., alias='id', description='The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    items: list[SqlPlanSummary] = Field(..., alias='items', description='array of SQL Plans.')


class SqlPlanInsightAggregation(OpsiBaseModel):
    """SQL execution plan Performance statistics."""

    plan_hash: int = Field(..., alias='planHash', description='Plan hash value for the SQL Execution Plan')
    io_time_in_sec: float = Field(..., alias='ioTimeInSec', description='IO Time in seconds')
    cpu_time_in_sec: float = Field(..., alias='cpuTimeInSec', description='CPU Time in seconds')
    inefficient_wait_time_in_sec: float = Field(..., alias='inefficientWaitTimeInSec', description='Inefficient Wait Time in seconds')
    executions_count: int = Field(..., alias='executionsCount', description='Total number of executions', ge=0)


class SqlPlanInsightAggregationCollection(OpsiBaseModel):
    """SQL plan insights response."""

    sql_identifier: str = Field(..., alias='sqlIdentifier', description='Unique SQL_ID for a SQL Statement.')
    id: str = Field(..., alias='id', description='The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    insights: list[SqlPlanInsights] = Field(..., alias='insights', description='List of SQL plan insights.')
    items: list[SqlPlanInsightAggregation] = Field(..., alias='items', description='List of SQL plan statistics.')


class SqlPlanInsights(OpsiBaseModel):
    """Represents collection of SQL Plan Insights."""

    text: str = Field(..., alias='text', description='SQL Plan Insight text.\nFor example `Number of Plans Used`, `Most Executed Plan`,\n`Best Performing Plan`, `Worst Performing Plan`,\n`Plan With Most IO`,\n`Plan with Most CPU`')
    value: int = Field(..., alias='value', description='SQL execution plan hash value for a given insight. For example `Most Executed Plan` insight will have value as "3975467901"')
    category: str = Field(..., alias='category', description='SQL Insight category. For example PLANS_USED, MOST_EXECUTED, BEST_PERFORMER, WORST_PERFORMER, MOST_CPU or MOST_IO.')


class SqlPlanLine(OpsiBaseModel):
    """SQL Plan Line type object."""

    version: float | None = Field(None, alias='version', description='Version\nExample: `1`')
    sql_identifier: str = Field(..., alias='sqlIdentifier', description='Unique SQL_ID for a SQL Statement.')
    plan_hash: int = Field(..., alias='planHash', description='Plan hash value for the SQL Execution Plan')
    force_matching_signature: str | None = Field(None, alias='forceMatchingSignature', description='Force matching signature\nExample: `"18067345456756876713"`')
    time_generated: datetime | None = Field(None, alias='timeGenerated', description='Generation time stamp\nExample: `"2020-05-05T02:10:00.000Z"`')
    time_collected: datetime = Field(..., alias='timeCollected', description='Collection time stamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    operation: str = Field(..., alias='operation', description='Operation\nExample: `"SELECT STATEMENT"`')
    remark: str | None = Field(None, alias='remark', description='Remark\nExample: `""`')
    options: str | None = Field(None, alias='options', description='Options\nExample: `"RANGE SCAN"`')
    object_node: str | None = Field(None, alias='objectNode', description='Object Node\nExample: `"Q4000"`')
    object_owner: str | None = Field(None, alias='objectOwner', description='Object Owner\nExample: `"TENANT_A#SCHEMA"`')
    object_name: str | None = Field(None, alias='objectName', description='Object Name\nExample: `"PLAN_LINES_PK"`')
    object_alias: str | None = Field(None, alias='objectAlias', description='Object Alias\nExample: `"PLAN_LINES@SEL$1"`')
    object_instance: int | None = Field(None, alias='objectInstance', description='Object Instance\nExample: `37472`')
    object_type: str | None = Field(None, alias='objectType', description='Object Type\nExample: `"INDEX (UNIQUE)"`')
    optimizer: str | None = Field(None, alias='optimizer', description='Optimizer\nExample: `"CLUSTER"`')
    search_columns: int | None = Field(None, alias='searchColumns', description='Search Columns\nExample: `3`')
    identifier: int = Field(..., alias='identifier', description='Identifier\nExample: `3`')
    parent_identifier: int | None = Field(None, alias='parentIdentifier', description='Parent Identifier\nExample: `2`')
    depth: int | None = Field(None, alias='depth', description='Depth\nExample: `3`')
    position: int | None = Field(None, alias='position', description='Position\nExample: `1`')
    cost: int | None = Field(None, alias='cost', description='Cost\nExample: `1`')
    cardinality: int | None = Field(None, alias='cardinality', description='Cardinality\nExample: `1`')
    bytes: int | None = Field(None, alias='bytes', description='Bytes\nExample: `150`')
    other: str | None = Field(None, alias='other', description='Other\nExample: ``')
    other_tag: str | None = Field(None, alias='otherTag', description='Other Tag\nExample: `"PARALLEL_COMBINED_WITH_PARENT"`')
    partition_start: str | None = Field(None, alias='partitionStart', description='Partition start\nExample: `1`')
    partition_stop: str | None = Field(None, alias='partitionStop', description='Partition stop\nExample: `2`')
    partition_identifier: int | None = Field(None, alias='partitionIdentifier', description='Partition identifier\nExample: `8`')
    distribution: str | None = Field(None, alias='distribution', description='Distribution\nExample: `"QC (RANDOM)"`')
    cpu_cost: int | None = Field(None, alias='cpuCost', description='CPU cost\nExample: `7321`')
    io_cost: int | None = Field(None, alias='ioCost', description='IO cost\nExample: `1`')
    temp_space: int | None = Field(None, alias='tempSpace', description='Time space\nExample: `15614000`')
    access_predicates: str | None = Field(None, alias='accessPredicates', description='Access predicates\nExample: `"\\"RESOURCE_ID\\"=:1 AND \\"QUERY_ID\\"=:2"`')
    filter_predicates: str | None = Field(None, alias='filterPredicates', description='Filter predicates\nExample: `"(INTERNAL_FUNCTION(\\"J\\".\\"DATABASE_ROLE\\") OR (\\"J\\".\\"DATABASE_ROLE\\" IS NULL AND SYS_CONTEXT(\'userenv\',\'database_role\')=\'PRIMARY\'))"`')
    projection: str | None = Field(None, alias='projection', description='Projection\nExample: `"COUNT(*)[22]"`')
    qblock_name: str | None = Field(None, alias='qblockName', description='Qblock Name\nExample: `"SEL$1"`')
    elapsed_time_in_sec: float | None = Field(None, alias='elapsedTimeInSec', description='Total elapsed time\nExample: `1.2`')
    other_xml: str | None = Field(None, alias='otherXML', description='Other SQL\nExample: `"<other_xml><info type=\\"db_version\\">18.0.0.0</info><info type=\\"parse_schema\\"><![CDATA[\\"SYS\\"]]></info><info type=\\"plan_hash_full\\">483892784</info><info type=\\"plan_hash\\">2709293936</info><info type=\\"plan_hash_2\\">483892784</info><outline_data><hint><![CDATA[IGNORE_OPTIM_EMBEDDED_HINTS]]></hint><hint><![CDATA[OPTIMIZER_FEATURES_ENABLE(\'18.1.0\')]]></hint><hint><![CDATA[DB_VERSION(\'18.1.0\')]]></hint><hint><![CDATA[OPT_PARAM(\'_b_tree_bitmap_plans\' \'false\')]]></hint><hint><![CDATA[OPT_PARAM(\'_optim_peek_user_binds\' \'false\')]]></hint><hint><![CDATA[OPT_PARAM(\'result_cache_mode\' \'FORCE\')]]></hint><hint><![CDATA[OPT_PARAM(\'_fix_control\' \'20648883:0 27745220:1 30001331:1 30142527:1 30539126:1\')]]></hint><hint><![CDATA[OUTLINE_LEAF(@\\"SEL$1\\")]]></hint><hint><![CDATA[INDEX(@\\"SEL$1\\" \\"USER$\\"@\\"SEL$1\\" \\"I_USER#\\")]]></hint></outline_data></other_xml>"`')


class SqlPlanSummary(OpsiBaseModel):
    """SQL Plan details."""

    plan_hash: int = Field(..., alias='planHash', description='Plan hash value for the SQL Execution Plan')
    plan_content: str = Field(..., alias='planContent', description='Plan XML Content')


class SqlResponseTimeDistributionAggregation(OpsiBaseModel):
    """SQL Response time distribution entry."""

    bucket_id: str = Field(..., alias='bucketId', description='Response time bucket id')
    executions_count: int = Field(..., alias='executionsCount', description='Total number of SQL executions', ge=0)


class SqlResponseTimeDistributionAggregationCollection(OpsiBaseModel):
    """SQL response time distribution over the selected time window."""

    sql_identifier: str = Field(..., alias='sqlIdentifier', description='Unique SQL_ID for a SQL Statement.')
    id: str = Field(..., alias='id', description='The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    items: list[SqlResponseTimeDistributionAggregation] = Field(..., alias='items', description='Array of pre defined SQL response time bucket id and SQL executions count.')


class SqlSearchCollection(OpsiBaseModel):
    """Search SQL response."""

    sql_identifier: str | None = Field(None, alias='sqlIdentifier', description='Unique SQL_ID for a SQL Statement.')
    sql_text: str | None = Field(None, alias='sqlText', description='SQL Statement Text')
    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    items: list[SqlSearchSummary] = Field(..., alias='items', description='List of Databases executing the sql.')


class SqlSearchSummary(OpsiBaseModel):
    """Database summary object resulting from a sql search operation."""

    id: str = Field(..., alias='id', description='The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    compartment_id: str = Field(..., alias='compartmentId', description='The OCID of the compartment.')
    database_name: str = Field(..., alias='databaseName', description='The database name. The database name is unique within the tenancy.')
    database_display_name: str = Field(..., alias='databaseDisplayName', description='The user-friendly name for the database. The name does not have to be unique.')
    database_type: str = Field(..., alias='databaseType', description='Ops Insights internal representation of the database type.')
    database_version: str = Field(..., alias='databaseVersion', description='The version of the database.')


class SqlStatisticAggregation(OpsiBaseModel):
    """SQL Statistics."""

    sql_identifier: str = Field(..., alias='sqlIdentifier', description='Unique SQL_ID for a SQL Statement.')
    database_details: DatabaseDetails = Field(..., alias='databaseDetails', description='The database_details field of SqlStatisticAggregation.')
    category: list[str] = Field(..., alias='category', description='SQL belongs to one or more categories based on the insights.')
    statistics: SqlStatistics | None = Field(None, alias='statistics', description='The statistics field of SqlStatisticAggregation.')


class SqlStatisticAggregationCollection(OpsiBaseModel):
    """SQL statistics response."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    items: list[SqlStatisticAggregation] = Field(..., alias='items', description='Array of SQLs along with its statistics statisfying the query criteria.')


class SqlStatistics(OpsiBaseModel):
    """Performance statistics for the SQL."""

    database_time_in_sec: float = Field(..., alias='databaseTimeInSec', description='Database Time in seconds')
    executions_per_hour: float = Field(..., alias='executionsPerHour', description='Number of executions per hour')
    executions_count: int = Field(..., alias='executionsCount', description='Total number of executions', ge=0)
    cpu_time_in_sec: float = Field(..., alias='cpuTimeInSec', description='CPU Time in seconds')
    io_time_in_sec: float = Field(..., alias='ioTimeInSec', description='I/O Time in seconds')
    inefficient_wait_time_in_sec: float = Field(..., alias='inefficientWaitTimeInSec', description='Inefficient Wait Time in seconds')
    response_time_in_sec: float = Field(..., alias='responseTimeInSec', description='Response time is the average elaspsed time per execution. It is the ratio of Total Database Time to the number of executions')
    plan_count: int = Field(..., alias='planCount', description='Number of SQL execution plans used by the SQL', ge=0)
    variability: float = Field(..., alias='variability', description='Variability is the ratio of the standard deviation in response time to the mean of response time of the SQL')
    average_active_sessions: float = Field(..., alias='averageActiveSessions', description='Average Active Sessions represent the average active sessions at a point in time. It is the number of sessions that are either working or waiting.')
    database_time_pct: float = Field(..., alias='databaseTimePct', description='Percentage of Database Time')
    inefficiency_in_pct: float = Field(..., alias='inefficiencyInPct', description='Percentage of Inefficiency. It is calculated by Total Database Time divided by Total Wait Time')
    change_in_cpu_time_in_pct: float = Field(..., alias='changeInCpuTimeInPct', description='Percent change in CPU Time based on linear regression')
    change_in_io_time_in_pct: float = Field(..., alias='changeInIoTimeInPct', description='Percent change in IO Time based on linear regression')
    change_in_inefficient_wait_time_in_pct: float = Field(..., alias='changeInInefficientWaitTimeInPct', description='Percent change in Inefficient Wait Time based on linear regression')
    change_in_response_time_in_pct: float = Field(..., alias='changeInResponseTimeInPct', description='Percent change in Response Time based on linear regression')
    change_in_average_active_sessions_in_pct: float = Field(..., alias='changeInAverageActiveSessionsInPct', description='Percent change in Average Active Sessions based on linear regression')
    change_in_executions_per_hour_in_pct: float = Field(..., alias='changeInExecutionsPerHourInPct', description='Percent change in Executions per hour based on linear regression')
    change_in_inefficiency_in_pct: float = Field(..., alias='changeInInefficiencyInPct', description='Percent change in Inefficiency based on linear regression')


class SqlStatisticsTimeSeries(OpsiBaseModel):
    """SQL performance statistics per database."""

    name: str = Field(..., alias='name', description='SQL performance statistic name')
    values: list[float] = Field(..., alias='values', description='SQL performance statistic value')


class SqlStatisticsTimeSeriesAggregation(OpsiBaseModel):
    """Database details and SQL performance statistics for a given database."""

    database_details: DatabaseDetails = Field(..., alias='databaseDetails', description='The database_details field of SqlStatisticsTimeSeriesAggregation.')
    statistics: list[SqlStatisticsTimeSeries] = Field(..., alias='statistics', description='SQL performance statistics for a given database')


class SqlStatisticsTimeSeriesAggregationCollection(OpsiBaseModel):
    """SQL performance statistics over the selected time window."""

    sql_identifier: str = Field(..., alias='sqlIdentifier', description='Unique SQL_ID for a SQL Statement.')
    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    end_timestamps: list[datetime] | None = Field(None, alias='endTimestamps', description='Array comprising of all the sampling period end timestamps in RFC 3339 format.')
    items: list[SqlStatisticsTimeSeriesAggregation] = Field(..., alias='items', description='Array of SQL performance statistics across databases.')


class SqlStatisticsTimeSeriesByPlanAggregation(OpsiBaseModel):
    """SQL performance statistics for a given plan."""

    plan_hash: int = Field(..., alias='planHash', description='Plan hash value for the SQL Execution Plan')
    statistics: list[SqlStatisticsTimeSeries] = Field(..., alias='statistics', description='SQL performance statistics for a given plan')


class SqlStatisticsTimeSeriesByPlanAggregationCollection(OpsiBaseModel):
    """SQL performance statistics by plan over the selected time window."""

    sql_identifier: str = Field(..., alias='sqlIdentifier', description='Unique SQL_ID for a SQL Statement.')
    id: str = Field(..., alias='id', description='The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    end_timestamps: list[datetime] = Field(..., alias='endTimestamps', description='Array comprising of all the sampling period end timestamps in RFC 3339 format.')
    items: list[SqlStatisticsTimeSeriesByPlanAggregation] = Field(..., alias='items', description='array of SQL performance statistics by plans')


class SqlStats(OpsiBaseModel):
    """Sql Stats type object."""

    sql_identifier: str = Field(..., alias='sqlIdentifier', description='Unique SQL_ID for a SQL Statement.')
    plan_hash_value: int = Field(..., alias='planHashValue', description='Plan hash value for the SQL Execution Plan')
    time_collected: datetime = Field(..., alias='timeCollected', description='Collection timestamp\nExample: `"2020-03-31T00:00:00.000Z"`')
    instance_name: str = Field(..., alias='instanceName', description='Name of Database Instance\nExample: `"DB10902_1"`')
    last_active_time: str | None = Field(None, alias='lastActiveTime', description='last_active_time\nExample: `"0000000099CCE300"`')
    parse_calls: int | None = Field(None, alias='parseCalls', description='Total integer of parse calls\nExample: `60`')
    disk_reads: int | None = Field(None, alias='diskReads', description='Number of disk reads')
    direct_reads: int | None = Field(None, alias='directReads', description='Number of direct reads')
    direct_writes: int | None = Field(None, alias='directWrites', description='Number of Direct writes')
    buffer_gets: int | None = Field(None, alias='bufferGets', description='Number of Buffer Gets')
    rows_processed: int | None = Field(None, alias='rowsProcessed', description='Number of row processed')
    serializable_aborts: int | None = Field(None, alias='serializableAborts', description='Number of serializable aborts')
    fetches: int | None = Field(None, alias='fetches', description='Number of fetches')
    executions: int | None = Field(None, alias='executions', description='Number of executions')
    avoided_executions: int | None = Field(None, alias='avoidedExecutions', description='Number of executions attempted on this object, but prevented due to the SQL statement being in quarantine')
    end_of_fetch_count: int | None = Field(None, alias='endOfFetchCount', description='Number of times this cursor was fully executed since the cursor was brought into the library cache', ge=0)
    loads: int | None = Field(None, alias='loads', description='Number of times the object was either loaded or reloaded')
    version_count: int | None = Field(None, alias='versionCount', description='Number of cursors present in the cache with this SQL text and plan', ge=0)
    invalidations: int | None = Field(None, alias='invalidations', description='Number of times this child cursor has been invalidated')
    obsolete_count: int | None = Field(None, alias='obsoleteCount', description='Number of times that a parent cursor became obsolete', ge=0)
    px_servers_executions: int | None = Field(None, alias='pxServersExecutions', description='Total number of executions performed by parallel execution servers (0 when the statement has never been executed in parallel)')
    cpu_time_in_us: int | None = Field(None, alias='cpuTimeInUs', description='CPU time (in microseconds) used by this cursor for parsing, executing, and fetching')
    elapsed_time_in_us: int | None = Field(None, alias='elapsedTimeInUs', description='Elapsed time (in microseconds) used by this cursor for parsing, executing, and fetching.')
    avg_hard_parse_time_in_us: int | None = Field(None, alias='avgHardParseTimeInUs', description='Average hard parse time (in microseconds) used by this cursor')
    concurrency_wait_time_in_us: int | None = Field(None, alias='concurrencyWaitTimeInUs', description='Concurrency wait time (in microseconds)')
    application_wait_time_in_us: int | None = Field(None, alias='applicationWaitTimeInUs', description='Application wait time (in microseconds)')
    cluster_wait_time_in_us: int | None = Field(None, alias='clusterWaitTimeInUs', description='Cluster wait time (in microseconds). This value is specific to Oracle RAC')
    user_io_wait_time_in_us: int | None = Field(None, alias='userIoWaitTimeInUs', description='User I/O wait time (in microseconds)')
    plsql_exec_time_in_us: int | None = Field(None, alias='plsqlExecTimeInUs', description='PL/SQL execution time (in microseconds)')
    java_exec_time_in_us: int | None = Field(None, alias='javaExecTimeInUs', description='Java execution time (in microseconds)')
    sorts: int | None = Field(None, alias='sorts', description='Number of sorts that were done for the child cursor')
    sharable_mem: int | None = Field(None, alias='sharableMem', description='Total shared memory (in bytes) currently occupied by all cursors with this SQL text and plan')
    total_sharable_mem: int | None = Field(None, alias='totalSharableMem', description='Total shared memory (in bytes) occupied by all cursors with this SQL text and plan if they were to be fully loaded in the shared pool (that is, cursor size)')
    type_check_mem: int | None = Field(None, alias='typeCheckMem', description='Typecheck memory')
    io_cell_offload_eligible_bytes: int | None = Field(None, alias='ioCellOffloadEligibleBytes', description='Number of I/O bytes which can be filtered by the Exadata storage system')
    io_interconnect_bytes: int | None = Field(None, alias='ioInterconnectBytes', description='Number of I/O bytes exchanged between Oracle Database and the storage system. Typically used for Cache Fusion or parallel queries')
    physical_read_requests: int | None = Field(None, alias='physicalReadRequests', description='Number of physical read I/O requests issued by the monitored SQL. The requests may not be disk reads')
    physical_read_bytes: int | None = Field(None, alias='physicalReadBytes', description='Number of bytes read from disks by the monitored SQL')
    physical_write_requests: int | None = Field(None, alias='physicalWriteRequests', description='Number of physical write I/O requests issued by the monitored SQL')
    physical_write_bytes: int | None = Field(None, alias='physicalWriteBytes', description='Number of bytes written to disks by the monitored SQL')
    exact_matching_signature: str | None = Field(None, alias='exactMatchingSignature', description='exact_matching_signature\nExample: `"18067345456756876713"`')
    force_matching_signature: str | None = Field(None, alias='forceMatchingSignature', description='force_matching_signature\nExample: `"18067345456756876713"`')
    io_cell_uncompressed_bytes: int | None = Field(None, alias='ioCellUncompressedBytes', description='Number of uncompressed bytes (that is, size after decompression) that are offloaded to the Exadata cells')
    io_cell_offload_returned_bytes: int | None = Field(None, alias='ioCellOffloadReturnedBytes', description='Number of bytes that are returned by Exadata cell through the regular I/O path')
    child_number: int | None = Field(None, alias='childNumber', description='Number of this child cursor')
    command_type: int | None = Field(None, alias='commandType', description='Oracle command type definition')
    users_opening: int | None = Field(None, alias='usersOpening', description='Number of users that have any of the child cursors open')
    users_executing: int | None = Field(None, alias='usersExecuting', description='Number of users executing the statement')
    optimizer_cost: int | None = Field(None, alias='optimizerCost', description='Cost of this query given by the optimizer')
    full_plan_hash_value: str | None = Field(None, alias='fullPlanHashValue', description='Total Number of rows in SQLStats table')
    module: str | None = Field(None, alias='module', description='Module name')
    service: str | None = Field(None, alias='service', description='Service name')
    action: str | None = Field(None, alias='action', description='Contains the name of the action that was executing when the SQL statement was first parsed, which is set by calling DBMS_APPLICATION_INFO.SET_ACTION')
    sql_profile: str | None = Field(None, alias='sqlProfile', description='SQL profile used for this statement, if any')
    sql_patch: str | None = Field(None, alias='sqlPatch', description='SQL patch used for this statement, if any')
    sql_plan_baseline: str | None = Field(None, alias='sqlPlanBaseline', description='SQL plan baseline used for this statement, if any')
    delta_execution_count: int | None = Field(None, alias='deltaExecutionCount', description='Number of executions for the cursor since the last AWR snapshot', ge=0)
    delta_cpu_time: int | None = Field(None, alias='deltaCpuTime', description='CPU time (in microseconds) for the cursor since the last AWR snapshot')
    delta_io_bytes: int | None = Field(None, alias='deltaIoBytes', description='Number of I/O bytes exchanged between the Oracle database and the storage system for the cursor since the last AWR snapshot')
    delta_cpu_rank: int | None = Field(None, alias='deltaCpuRank', description='Rank based on CPU Consumption')
    delta_execs_rank: int | None = Field(None, alias='deltaExecsRank', description='Rank based on number of execution')
    sharable_mem_rank: int | None = Field(None, alias='sharableMemRank', description='Rank based on sharable memory')
    delta_io_rank: int | None = Field(None, alias='deltaIoRank', description='Rank based on I/O Consumption')
    harmonic_sum: int | None = Field(None, alias='harmonicSum', description='Harmonic sum based on ranking parameters')
    wt_harmonic_sum: int | None = Field(None, alias='wtHarmonicSum', description='Weight based harmonic sum of ranking parameters')
    total_sql_count: int | None = Field(None, alias='totalSqlCount', description='Total number of rows in SQLStats table', ge=0)


class SqlText(OpsiBaseModel):
    """SQL Text type object."""

    version: float | None = Field(None, alias='version', description='Version\nExample: `1`')
    sql_identifier: str = Field(..., alias='sqlIdentifier', description='Unique SQL_ID for a SQL Statement.')
    time_collected: datetime = Field(..., alias='timeCollected', description='Collection timestamp\nExample: `"2020-05-06T00:00:00.000Z"`')
    sql_command: str = Field(..., alias='sqlCommand', description='SQL command\nExample: `"SELECT"`')
    exact_matching_signature: str | None = Field(None, alias='exactMatchingSignature', description='Exact matching signature\nExample: `"18067345456756876713"`')
    force_matching_signature: str | None = Field(None, alias='forceMatchingSignature', description='Force matching signature\nExample: `"18067345456756876713"`')
    sql_full_text: str = Field(..., alias='sqlFullText', description='Full SQL Text\nExample: `"SELECT username,profile,default_tablespace,temporary_tablespace FROM dba_users"`\nDisclaimer: SQL text being uploaded explicitly via APIs is not masked. Any sensitive literals contained in the sqlFullText column should be masked prior to ingestion.')


class SqlTextCollection(OpsiBaseModel):
    """SQL Text for the particular SQL."""

    items: list[SqlTextSummary] = Field(..., alias='items', description='array of SQL Texts.')


class SqlTextSummary(OpsiBaseModel):
    """SQL Text details."""

    sql_identifier: str = Field(..., alias='sqlIdentifier', description='Unique SQL_ID for a SQL Statement.')
    id: str = Field(..., alias='id', description='The OCID of the database insight resource.')
    database_id: str = Field(..., alias='databaseId', description='The OCID of the database.')
    compartment_id: str | None = Field(None, alias='compartmentId', description='The OCID of the compartment.')
    sql_text: str = Field(..., alias='sqlText', description='SQL Text')


class SqlTypeDetails(OpsiBaseModel):
    """SQL details."""

    type: Literal['SCHEMA_OBJECT', 'SQL', 'DATABASE_PARAMETER', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='type', description='Gets the type of this RelatedObjectTypeDetails.\nType of related object\n\nAllowed values for this property are: "SCHEMA_OBJECT", "SQL", "DATABASE_PARAMETER", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    sql_id: str = Field(..., alias='sqlId', description='SQL identifier')
    sql_text: str = Field(..., alias='sqlText', description='First 3800 characters of the SQL text')
    is_sql_text_truncated: bool = Field(..., alias='isSqlTextTruncated', description='SQL identifier')
    sql_command: str = Field(..., alias='sqlCommand', description='SQL command name (such as SELECT, INSERT)')


class StorageServerDetails(OpsiBaseModel):
    """Partial information about a storage server which includes name and displayName."""

    storage_server_name: str = Field(..., alias='storageServerName', description='The storage server name.')
    storage_server_display_name: str = Field(..., alias='storageServerDisplayName', description='The user-friendly name for the storage server. The name does not have to be unique.')


class StorageUsageTrend(OpsiBaseModel):
    """Usage data samples."""

    end_timestamp: datetime = Field(..., alias='endTimestamp', description='The timestamp in which the current sampling period ends in RFC 3339 format.')
    file_system_usage_in_gbs: float = Field(..., alias='fileSystemUsageInGBs', description='Filesystem usage in GB.')
    file_system_avail_in_percent: float = Field(..., alias='fileSystemAvailInPercent', description='Filesystem available in percent.')


class StorageUsageTrendAggregation(OpsiBaseModel):
    """Usage data per filesystem."""

    file_system_name: str = Field(..., alias='fileSystemName', description='Name of filesystem.')
    mount_point: str = Field(..., alias='mountPoint', description='Mount points are specialized NTFS filesystem objects.')
    file_system_size_in_gbs: float = Field(..., alias='fileSystemSizeInGBs', description='Size of filesystem.')
    usage_data: list[StorageUsageTrend] = Field(..., alias='usageData', description='List of usage data samples for a filesystem.')


class SummarizeAwrSourcesSummariesCollection(OpsiBaseModel):
    """Collection of AwrSource summary objects."""

    items: list[AwrSourceSummary] = Field(..., alias='items', description='Array of AwrSource summary objects.')


class SummarizeDatabaseInsightResourceCapacityTrendAggregationCollection(OpsiBaseModel):
    """Collection of resource capacity trend."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    high_utilization_threshold: int = Field(..., alias='highUtilizationThreshold', description='Percent value in which a resource metric is considered highly utilized.')
    low_utilization_threshold: int = Field(..., alias='lowUtilizationThreshold', description='Percent value in which a resource metric is considered lowly utilized.')
    resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'MEMORY_PGA', 'MEMORY_SGA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "MEMORY_PGA", "MEMORY_SGA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    capacity_data: list[ResourceCapacityTrendAggregation] = Field(..., alias='capacityData', description='Capacity Data with time interval')


class SummarizeDatabaseInsightResourceForecastTrendAggregation(OpsiBaseModel):
    """Forecast results from the selected time period."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    high_utilization_threshold: int = Field(..., alias='highUtilizationThreshold', description='Percent value in which a resource metric is considered highly utilized.')
    low_utilization_threshold: int = Field(..., alias='lowUtilizationThreshold', description='Percent value in which a resource metric is considered lowly utilized.')
    resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'MEMORY_PGA', 'MEMORY_SGA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "MEMORY_PGA", "MEMORY_SGA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    selected_forecast_algorithm: str | None = Field(None, alias='selectedForecastAlgorithm', description='Auto-ML algorithm leveraged for the forecast. Only applicable for Auto-ML forecast.')
    pattern: Literal['LINEAR', 'MONTHLY_SEASONS', 'MONTHLY_AND_YEARLY_SEASONS', 'WEEKLY_SEASONS', 'WEEKLY_AND_MONTHLY_SEASONS', 'WEEKLY_MONTHLY_AND_YEARLY_SEASONS', 'WEEKLY_AND_YEARLY_SEASONS', 'YEARLY_SEASONS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='pattern', description='Time series patterns used in the forecasting.\n\nAllowed values for this property are: "LINEAR", "MONTHLY_SEASONS", "MONTHLY_AND_YEARLY_SEASONS", "WEEKLY_SEASONS", "WEEKLY_AND_MONTHLY_SEASONS", "WEEKLY_MONTHLY_AND_YEARLY_SEASONS", "WEEKLY_AND_YEARLY_SEASONS", "YEARLY_SEASONS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    tablespace_name: str = Field(..., alias='tablespaceName', description='The name of tablespace.')
    historical_data: list[HistoricalDataItem] = Field(..., alias='historicalData', description='Time series data used for the forecast analysis.')
    projected_data: list[ProjectedDataItem] = Field(..., alias='projectedData', description='Time series data result of the forecasting analysis.')


class SummarizeDatabaseInsightResourceStatisticsAggregationCollection(OpsiBaseModel):
    """Returns list of the Databases with resource statistics like usage, capacity, utilization and usage change percent."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    high_utilization_threshold: int = Field(..., alias='highUtilizationThreshold', description='Percent value in which a resource metric is considered highly utilized.')
    low_utilization_threshold: int = Field(..., alias='lowUtilizationThreshold', description='Percent value in which a resource metric is considered lowly utilized.')
    resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'MEMORY_PGA', 'MEMORY_SGA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "MEMORY_PGA", "MEMORY_SGA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[ResourceStatisticsAggregation] = Field(..., alias='items', description='Collection of Resource Statistics items')


class SummarizeDatabaseInsightResourceUsageAggregation(OpsiBaseModel):
    """Resource usage summation for the current time period."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'MEMORY_PGA', 'MEMORY_SGA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "MEMORY_PGA", "MEMORY_SGA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage: float = Field(..., alias='usage', description='Total amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    usage_change_percent: float = Field(..., alias='usageChangePercent', description='Percentage change in resource usage during the current period calculated using linear regression functions')
    total_host_capacity: float | None = Field(None, alias='totalHostCapacity', description='The maximum host CPUs (cores x threads/core) on the underlying infrastructure. This only applies to CPU and does not not apply for Autonomous Databases.')


class SummarizeDatabaseInsightResourceUsageTrendAggregationCollection(OpsiBaseModel):
    """Top level response object."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'MEMORY_PGA', 'MEMORY_SGA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "MEMORY_PGA", "MEMORY_SGA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    usage_data: list[ResourceUsageTrendAggregation] = Field(..., alias='usageData', description='Usage Data with time stamps')


class SummarizeDatabaseInsightResourceUtilizationInsightAggregation(OpsiBaseModel):
    """Insights response containing current/projected groups for storage or CPU."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    high_utilization_threshold: int = Field(..., alias='highUtilizationThreshold', description='Percent value in which a resource metric is considered highly utilized.')
    low_utilization_threshold: int = Field(..., alias='lowUtilizationThreshold', description='Percent value in which a resource metric is considered lowly utilized.')
    resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'MEMORY_PGA', 'MEMORY_SGA', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "MEMORY_PGA", "MEMORY_SGA", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    projected_utilization: ResourceInsightProjectedUtilization = Field(..., alias='projectedUtilization', description='The projected_utilization field of SummarizeDatabaseInsightResourceUtilizationInsightAggregation.')
    current_utilization: ResourceInsightCurrentUtilization = Field(..., alias='currentUtilization', description='The current_utilization field of SummarizeDatabaseInsightResourceUtilizationInsightAggregation.')


class SummarizeDatabaseInsightTablespaceUsageTrendAggregationCollection(OpsiBaseModel):
    """Top level response object."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    items: list[TablespaceUsageTrendAggregation] = Field(..., alias='items', description='Collection of Usage Data with time stamps for top five tablespace')


class SummarizeExadataInsightResourceCapacityTrendAggregation(OpsiBaseModel):
    """Collection of resource capacity trend."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    exadata_resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'IOPS', 'THROUGHPUT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceMetric', description='Defines the type of exadata resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "IOPS", "THROUGHPUT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_resource_type: Literal['DATABASE', 'HOST', 'STORAGE_SERVER', 'DISKGROUP', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceType', description='Defines the resource type for an exadata  (example: DATABASE, STORAGE_SERVER, HOST, DISKGROUP)\n\nAllowed values for this property are: "DATABASE", "HOST", "STORAGE_SERVER", "DISKGROUP", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    capacity_data: list[ExadataInsightResourceCapacityTrendAggregation] = Field(..., alias='capacityData', description='Capacity Data with time interval')


class SummarizeExadataInsightResourceCapacityTrendCollection(OpsiBaseModel):
    """capacity results with breakdown by databases, hosts, storage servers or diskgroup."""

    exadata_insight_id: str = Field(..., alias='exadataInsightId', description='The OCID of the Exadata insight.')
    exadata_resource_type: Literal['DATABASE', 'HOST', 'STORAGE_SERVER', 'DISKGROUP', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceType', description='Defines the resource type for an exadata  (example: DATABASE, STORAGE_SERVER, HOST, DISKGROUP)\n\nAllowed values for this property are: "DATABASE", "HOST", "STORAGE_SERVER", "DISKGROUP", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'IOPS', 'THROUGHPUT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceMetric', description='Defines the type of exadata resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "IOPS", "THROUGHPUT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[ExadataInsightResourceCapacityTrendSummary] = Field(..., alias='items', description='Capacity Data with time interval')


class SummarizeExadataInsightResourceForecastTrendAggregation(OpsiBaseModel):
    """Usage and Forecast results from the selected time period."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    exadata_resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'IOPS', 'THROUGHPUT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceMetric', description='Defines the type of exadata resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "IOPS", "THROUGHPUT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_resource_type: Literal['DATABASE', 'HOST', 'STORAGE_SERVER', 'DISKGROUP', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceType', description='Defines the resource type for an exadata  (example: DATABASE, STORAGE_SERVER, HOST, DISKGROUP)\n\nAllowed values for this property are: "DATABASE", "HOST", "STORAGE_SERVER", "DISKGROUP", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    selected_forecast_algorithm: str | None = Field(None, alias='selectedForecastAlgorithm', description='Auto-ML algorithm leveraged for the forecast. Only applicable for Auto-ML forecast.')
    pattern: Literal['LINEAR', 'MONTHLY_SEASONS', 'MONTHLY_AND_YEARLY_SEASONS', 'WEEKLY_SEASONS', 'WEEKLY_AND_MONTHLY_SEASONS', 'WEEKLY_MONTHLY_AND_YEARLY_SEASONS', 'WEEKLY_AND_YEARLY_SEASONS', 'YEARLY_SEASONS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='pattern', description='Time series patterns used in the forecasting.\n\nAllowed values for this property are: "LINEAR", "MONTHLY_SEASONS", "MONTHLY_AND_YEARLY_SEASONS", "WEEKLY_SEASONS", "WEEKLY_AND_MONTHLY_SEASONS", "WEEKLY_MONTHLY_AND_YEARLY_SEASONS", "WEEKLY_AND_YEARLY_SEASONS", "YEARLY_SEASONS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    days_to_reach_capacity: int = Field(..., alias='daysToReachCapacity', description='Days to reach capacity for a storage server')
    historical_data: list[HistoricalDataItem] = Field(..., alias='historicalData', description='Time series data used for the forecast analysis.')
    projected_data: list[ProjectedDataItem] = Field(..., alias='projectedData', description='Time series data result of the forecasting analysis.')


class SummarizeExadataInsightResourceForecastTrendCollection(OpsiBaseModel):
    """Usage and Forecast results with breakdown by databases, hosts or storage servers."""

    exadata_insight_id: str = Field(..., alias='exadataInsightId', description='The OCID of the Exadata insight.')
    exadata_resource_type: Literal['DATABASE', 'HOST', 'STORAGE_SERVER', 'DISKGROUP', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceType', description='Defines the resource type for an exadata  (example: DATABASE, STORAGE_SERVER, HOST, DISKGROUP)\n\nAllowed values for this property are: "DATABASE", "HOST", "STORAGE_SERVER", "DISKGROUP", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'IOPS', 'THROUGHPUT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceMetric', description='Defines the type of exadata resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "IOPS", "THROUGHPUT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[ExadataInsightResourceForecastTrendSummary] = Field(..., alias='items', description='Collection of id, name, daysToReach Capacity, historical usage and projected usage forecast.')


class SummarizeExadataInsightResourceStatisticsAggregationCollection(OpsiBaseModel):
    """Returns list of the resources with resource statistics like usage,capacity,utilization and usage change percent."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    items: list[ExadataInsightResourceStatisticsAggregation] = Field(..., alias='items', description='Collection of Resource Statistics items')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'IOPS', 'THROUGHPUT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceMetric', description='Defines the type of exadata resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "IOPS", "THROUGHPUT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_insight_id: str = Field(..., alias='exadataInsightId', description='The OCID of the Exadata insight.')
    exadata_display_name: str | None = Field(None, alias='exadataDisplayName', description='The user-friendly name for the Exadata system. The name does not have to be unique.')


class SummarizeExadataInsightResourceUsageAggregation(OpsiBaseModel):
    """Resource usage summation for the current time period."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    exadata_resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'IOPS', 'THROUGHPUT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceMetric', description='Defines the type of exadata resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "IOPS", "THROUGHPUT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_resource_type: Literal['DATABASE', 'HOST', 'STORAGE_SERVER', 'DISKGROUP', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceType', description='Defines the resource type for an exadata  (example: DATABASE, STORAGE_SERVER, HOST, DISKGROUP)\n\nAllowed values for this property are: "DATABASE", "HOST", "STORAGE_SERVER", "DISKGROUP", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage: float = Field(..., alias='usage', description='Total amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    usage_change_percent: float = Field(..., alias='usageChangePercent', description='Percentage change in resource usage during the current period calculated using linear regression functions')
    total_host_capacity: float | None = Field(None, alias='totalHostCapacity', description='The maximum host CPUs (cores x threads/core) on the underlying infrastructure. This only applies to CPU and does not not apply for Autonomous Databases.')


class SummarizeExadataInsightResourceUsageCollection(OpsiBaseModel):
    """Resource usage, allocation, utilization and usage ChangePercent for the current time period."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    exadata_resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'IOPS', 'THROUGHPUT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceMetric', description='Defines the type of exadata resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "IOPS", "THROUGHPUT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_resource_type: Literal['DATABASE', 'HOST', 'STORAGE_SERVER', 'DISKGROUP', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceType', description='Defines the resource type for an exadata  (example: DATABASE, STORAGE_SERVER, HOST, DISKGROUP)\n\nAllowed values for this property are: "DATABASE", "HOST", "STORAGE_SERVER", "DISKGROUP", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[ResourceUsageSummary] = Field(..., alias='items', description='Collection of Resource Usage Summary items')


class SummarizeExadataInsightResourceUtilizationInsightAggregation(OpsiBaseModel):
    """Insights response containing utilization values for exadata systems."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    high_utilization_threshold: int = Field(..., alias='highUtilizationThreshold', description='Percent value in which a resource metric is considered highly utilized.')
    low_utilization_threshold: int = Field(..., alias='lowUtilizationThreshold', description='Percent value in which a resource metric is considered lowly utilized.')
    exadata_resource_metric: Literal['CPU', 'STORAGE', 'IO', 'MEMORY', 'IOPS', 'THROUGHPUT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceMetric', description='Defines the type of exadata resource metric (example: CPU, STORAGE)\n\nAllowed values for this property are: "CPU", "STORAGE", "IO", "MEMORY", "IOPS", "THROUGHPUT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    exadata_resource_type: Literal['DATABASE', 'HOST', 'STORAGE_SERVER', 'DISKGROUP', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='exadataResourceType', description='Defines the resource type for an exadata  (example: DATABASE, STORAGE_SERVER, HOST, DISKGROUP)\n\nAllowed values for this property are: "DATABASE", "HOST", "STORAGE_SERVER", "DISKGROUP", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    utilization: list[ExadataInsightResourceInsightUtilizationItem] = Field(..., alias='utilization', description='Collection of Exadata system utilization')


class SummarizeHostInsightHostRecommendationAggregation(OpsiBaseModel):
    """Returns list of hosts with resource statistics like usage, capacity, utilization, usage change percent and load."""

    resource_metric: Literal['CPU', 'MEMORY', 'LOGICAL_MEMORY', 'STORAGE', 'NETWORK', 'GPU_UTILIZATION', 'GPU_MEMORY_USAGE', 'IO', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (CPU, Physical Memory, Logical Memory)\n\nAllowed values for this property are: "CPU", "MEMORY", "LOGICAL_MEMORY", "STORAGE", "NETWORK", "GPU_UTILIZATION", "GPU_MEMORY_USAGE", "IO", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    details: HostInsightHostRecommendations | None = Field(None, alias='details', description='The details field of SummarizeHostInsightHostRecommendationAggregation.')


class SummarizeHostInsightIoUsageTrendAggregationCollection(OpsiBaseModel):
    """Top level response object."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    items: list[IoUsageTrendAggregation] = Field(..., alias='items', description='Collection of Usage Data with time stamps for all IO interfaces.')


class SummarizeHostInsightNetworkUsageTrendAggregationCollection(OpsiBaseModel):
    """Top level response object."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    items: list[NetworkUsageTrendAggregation] = Field(..., alias='items', description='Collection of Usage Data with time stamps for all network interfaces.')


class SummarizeHostInsightResourceCapacityTrendAggregationCollection(OpsiBaseModel):
    """Top level response object."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    high_utilization_threshold: int = Field(..., alias='highUtilizationThreshold', description='Percent value in which a resource metric is considered highly utilized.')
    low_utilization_threshold: int = Field(..., alias='lowUtilizationThreshold', description='Percent value in which a resource metric is considered lowly utilized.')
    resource_metric: Literal['CPU', 'MEMORY', 'LOGICAL_MEMORY', 'STORAGE', 'NETWORK', 'GPU_UTILIZATION', 'GPU_MEMORY_USAGE', 'IO', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (CPU, Physical Memory, Logical Memory)\n\nAllowed values for this property are: "CPU", "MEMORY", "LOGICAL_MEMORY", "STORAGE", "NETWORK", "GPU_UTILIZATION", "GPU_MEMORY_USAGE", "IO", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    capacity_data: list[HostResourceCapacityTrendAggregation] = Field(..., alias='capacityData', description='Capacity Data with timestamp.')


class SummarizeHostInsightResourceForecastTrendAggregation(OpsiBaseModel):
    """Forecast results from the selected time period."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    high_utilization_threshold: int = Field(..., alias='highUtilizationThreshold', description='Percent value in which a resource metric is considered highly utilized.')
    low_utilization_threshold: int = Field(..., alias='lowUtilizationThreshold', description='Percent value in which a resource metric is considered lowly utilized.')
    resource_metric: Literal['CPU', 'MEMORY', 'LOGICAL_MEMORY', 'STORAGE', 'NETWORK', 'GPU_UTILIZATION', 'GPU_MEMORY_USAGE', 'IO', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (CPU, Physical Memory, Logical Memory)\n\nAllowed values for this property are: "CPU", "MEMORY", "LOGICAL_MEMORY", "STORAGE", "NETWORK", "GPU_UTILIZATION", "GPU_MEMORY_USAGE", "IO", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    selected_forecast_algorithm: str | None = Field(None, alias='selectedForecastAlgorithm', description='Auto-ML algorithm leveraged for the forecast. Only applicable for Auto-ML forecast.')
    pattern: Literal['LINEAR', 'MONTHLY_SEASONS', 'MONTHLY_AND_YEARLY_SEASONS', 'WEEKLY_SEASONS', 'WEEKLY_AND_MONTHLY_SEASONS', 'WEEKLY_MONTHLY_AND_YEARLY_SEASONS', 'WEEKLY_AND_YEARLY_SEASONS', 'YEARLY_SEASONS', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='pattern', description='Time series patterns used in the forecasting.\n\nAllowed values for this property are: "LINEAR", "MONTHLY_SEASONS", "MONTHLY_AND_YEARLY_SEASONS", "WEEKLY_SEASONS", "WEEKLY_AND_MONTHLY_SEASONS", "WEEKLY_MONTHLY_AND_YEARLY_SEASONS", "WEEKLY_AND_YEARLY_SEASONS", "YEARLY_SEASONS", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    historical_data: list[HistoricalDataItem] = Field(..., alias='historicalData', description='Time series data used for the forecast analysis.')
    projected_data: list[ProjectedDataItem] = Field(..., alias='projectedData', description='Time series data result of the forecasting analysis.')


class SummarizeHostInsightResourceStatisticsAggregationCollection(OpsiBaseModel):
    """Returns list of hosts with resource statistics like usage, capacity, utilization, usage change percent and load."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    high_utilization_threshold: int = Field(..., alias='highUtilizationThreshold', description='Percent value in which a resource metric is considered highly utilized.')
    low_utilization_threshold: int = Field(..., alias='lowUtilizationThreshold', description='Percent value in which a resource metric is considered lowly utilized.')
    resource_metric: Literal['CPU', 'MEMORY', 'LOGICAL_MEMORY', 'STORAGE', 'NETWORK', 'GPU_UTILIZATION', 'GPU_MEMORY_USAGE', 'IO', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (CPU, Physical Memory, Logical Memory)\n\nAllowed values for this property are: "CPU", "MEMORY", "LOGICAL_MEMORY", "STORAGE", "NETWORK", "GPU_UTILIZATION", "GPU_MEMORY_USAGE", "IO", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    items: list[HostInsightResourceStatisticsAggregation] = Field(..., alias='items', description='Collection of Resource Statistics items')


class SummarizeHostInsightResourceUsageAggregation(OpsiBaseModel):
    """Resource usage summation for the current time period."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    resource_metric: Literal['CPU', 'MEMORY', 'LOGICAL_MEMORY', 'STORAGE', 'NETWORK', 'GPU_UTILIZATION', 'GPU_MEMORY_USAGE', 'IO', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (CPU, Physical Memory, Logical Memory)\n\nAllowed values for this property are: "CPU", "MEMORY", "LOGICAL_MEMORY", "STORAGE", "NETWORK", "GPU_UTILIZATION", "GPU_MEMORY_USAGE", "IO", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage: float = Field(..., alias='usage', description='Total amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')
    usage_change_percent: float = Field(..., alias='usageChangePercent', description='Percentage change in resource usage during the current period calculated using linear regression functions')


class SummarizeHostInsightResourceUsageTrendAggregationCollection(OpsiBaseModel):
    """Top level response object."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    resource_metric: Literal['CPU', 'MEMORY', 'LOGICAL_MEMORY', 'STORAGE', 'NETWORK', 'GPU_UTILIZATION', 'GPU_MEMORY_USAGE', 'IO', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (CPU, Physical Memory, Logical Memory)\n\nAllowed values for this property are: "CPU", "MEMORY", "LOGICAL_MEMORY", "STORAGE", "NETWORK", "GPU_UTILIZATION", "GPU_MEMORY_USAGE", "IO", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    usage_data: list[ResourceUsageTrendAggregation] = Field(..., alias='usageData', description='Usage Data with timestamp.')


class SummarizeHostInsightResourceUtilizationInsightAggregation(OpsiBaseModel):
    """Insights response containing current/projected groups for CPU or memory."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    high_utilization_threshold: int = Field(..., alias='highUtilizationThreshold', description='Percent value in which a resource metric is considered highly utilized.')
    low_utilization_threshold: int = Field(..., alias='lowUtilizationThreshold', description='Percent value in which a resource metric is considered lowly utilized.')
    resource_metric: Literal['CPU', 'MEMORY', 'LOGICAL_MEMORY', 'STORAGE', 'NETWORK', 'GPU_UTILIZATION', 'GPU_MEMORY_USAGE', 'IO', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='resourceMetric', description='Defines the type of resource metric (CPU, Physical Memory, Logical Memory)\n\nAllowed values for this property are: "CPU", "MEMORY", "LOGICAL_MEMORY", "STORAGE", "NETWORK", "GPU_UTILIZATION", "GPU_MEMORY_USAGE", "IO", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    projected_utilization: ResourceInsightProjectedUtilization = Field(..., alias='projectedUtilization', description='The projected_utilization field of SummarizeHostInsightResourceUtilizationInsightAggregation.')
    current_utilization: ResourceInsightCurrentUtilization = Field(..., alias='currentUtilization', description='The current_utilization field of SummarizeHostInsightResourceUtilizationInsightAggregation.')


class SummarizeHostInsightStorageUsageTrendAggregationCollection(OpsiBaseModel):
    """Top level response object."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    items: list[StorageUsageTrendAggregation] = Field(..., alias='items', description='Collection of Usage Data with time stamps for all filesystems.')


class SummarizeHostInsightsDiskStatisticsCollection(OpsiBaseModel):
    """Top level response object."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    usage_unit: Literal['CORES', 'GB', 'MBPS', 'IOPS', 'PERCENT', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='usageUnit', description='Displays usage unit ( CORES, GB, PERCENT, MBPS)\n\nAllowed values for this property are: "CORES", "GB", "MBPS", "IOPS", "PERCENT", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    item_duration_in_ms: int = Field(..., alias='itemDurationInMs', description='Time duration in milliseconds between data points (one hour or one day).')
    items: list[DiskStatistics] = Field(..., alias='items', description='Collection of Data for all disks in a host.')


class SummarizeHostInsightsTopProcessesUsageCollection(OpsiBaseModel):
    """Top level response object."""

    timestamp: datetime = Field(..., alias='timestamp', description='The start timestamp that was passed into the request.')
    items: list[TopProcessesUsage] = Field(..., alias='items', description='List of usage data samples for a top process on a specific date.')


class SummarizeHostInsightsTopProcessesUsageTrendCollection(OpsiBaseModel):
    """Top level response object."""

    time_interval_start: datetime = Field(..., alias='timeIntervalStart', description='The start timestamp that was passed into the request.')
    time_interval_end: datetime = Field(..., alias='timeIntervalEnd', description='The end timestamp that was passed into the request.')
    items: list[TopProcessesUsageTrendAggregation] = Field(..., alias='items', description='Collection of Usage Data with time stamps for top processes')


class SummarizeOperationsInsightsWarehouseResourceUsageAggregation(OpsiBaseModel):
    """Details of resource usage by an Operations Insights Warehouse resource."""

    id: str = Field(..., alias='id', description='OPSI Warehouse OCID')
    cpu_used: float | None = Field(None, alias='cpuUsed', description='Number of OCPUs used by OPSI Warehouse ADW. Can be fractional.')
    storage_used_in_gbs: float | None = Field(None, alias='storageUsedInGBs', description='Storage by OPSI Warehouse ADW in GB.')
    lifecycle_state: Literal['CREATING', 'UPDATING', 'ACTIVE', 'DELETING', 'DELETED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='lifecycleState', description='Possible lifecycle states\n\nAllowed values for this property are: "CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class SummaryStatistics(OpsiBaseModel):
    """Contains common summary statistics."""

    minimum: float = Field(..., alias='minimum', description='The smallest number in the data set.')
    maximum: float = Field(..., alias='maximum', description='The largest number in the data set.')
    average: float = Field(..., alias='average', description='The average number in the data set.')
    median: float = Field(..., alias='median', description='The middle number in the data set.')
    lower_quartile: float = Field(..., alias='lowerQuartile', description="The middle number between the smallest number and the median of the data set. It's also known as the 25th quartile.")
    upper_quartile: float = Field(..., alias='upperQuartile', description="The middle number between the median and the largest number of the data set. It's also known as the 75th quartile.")


class SynchronizeAutonomousDatabaseToExadataDetails(OpsiRequestModel):
    """The details of onboarded autonomous database need to synchroized with infracture information."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Source of the database entity. Currently only AUTONOMOUS_DATABASE source is supported.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')


class TablespaceUsageTrend(OpsiBaseModel):
    """Usage data samples."""

    end_timestamp: datetime = Field(..., alias='endTimestamp', description='The timestamp in which the current sampling period ends in RFC 3339 format.')
    usage: float = Field(..., alias='usage', description='Total amount used of the resource metric type (CPU, STORAGE).')
    capacity: float = Field(..., alias='capacity', description='The maximum allocated amount of the resource metric type  (CPU, STORAGE) for a set of databases.')


class TablespaceUsageTrendAggregation(OpsiBaseModel):
    """Usage data per tablespace for a Pluggable database."""

    tablespace_name: str = Field(..., alias='tablespaceName', description='The name of tablespace.')
    tablespace_type: str = Field(..., alias='tablespaceType', description='Type of tablespace')
    usage_data: list[TablespaceUsageTrend] = Field(..., alias='usageData', description='List of usage data samples for a tablespace')


class TestMacsManagedAutonomousDatabaseInsightConnectionDetails(OpsiRequestModel):
    """Connection details of a MACS-managed Autonomous database."""

    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    connection_details: ConnectionDetails = Field(..., alias='connectionDetails', description='The connection_details field of TestMacsManagedAutonomousDatabaseInsightConnectionDetails.')
    connection_credential_details: CredentialDetails = Field(..., alias='connectionCredentialDetails', description='The connection_credential_details field of TestMacsManagedAutonomousDatabaseInsightConnectionDetails.')


class TestMacsManagedCloudDatabaseInsightConnectionDetails(OpsiRequestModel):
    """Connection details of a MACS-managed cloud database."""

    management_agent_id: str = Field(..., alias='managementAgentId', description='The OCID of the Management Agent.')
    connection_details: ConnectionDetails = Field(..., alias='connectionDetails', description='The connection_details field of TestMacsManagedCloudDatabaseInsightConnectionDetails.')
    connection_credential_details: CredentialDetails = Field(..., alias='connectionCredentialDetails', description='The connection_credential_details field of TestMacsManagedCloudDatabaseInsightConnectionDetails.')


class TopProcessesUsage(OpsiBaseModel):
    """Aggregated data for top processes on a specific date."""

    command: str = Field(..., alias='command', description='Command line and arguments used to launch process.')
    container_id: str | None = Field(None, alias='containerId', description='Container id if this process corresponds to a running container in the host.')
    process_hash: str = Field(..., alias='processHash', description='Unique identifier for a process.')
    cpu_usage: float = Field(..., alias='cpuUsage', description='Process CPU usage.')
    cpu_utilization: float = Field(..., alias='cpuUtilization', description='Process CPU utilization percentage.')
    memory_utilization: float = Field(..., alias='memoryUtilization', description='Process memory utilization percentage.')
    virtual_memory_in_mbs: float = Field(..., alias='virtualMemoryInMBs', description='Process virtual memory in Megabytes.')
    physical_memory_in_mbs: float = Field(..., alias='physicalMemoryInMBs', description='Procress physical memory in Megabytes.')
    max_process_count: int = Field(..., alias='maxProcessCount', description='Maximum number of processes running at time of collection.', ge=0)


class TopProcessesUsageTrend(OpsiBaseModel):
    """Aggregated data for top processes."""

    end_timestamp: datetime = Field(..., alias='endTimestamp', description='The timestamp in which the current sampling period ends in RFC 3339 format.')
    container_id: str | None = Field(None, alias='containerId', description='Container id if this process corresponds to a running container in the host.')
    cpu_usage: float = Field(..., alias='cpuUsage', description='Process CPU usage.')
    cpu_utilization: float = Field(..., alias='cpuUtilization', description='Process CPU utilization percentage')
    memory_utilization: float = Field(..., alias='memoryUtilization', description='Process memory utilization percentage')
    virtual_memory_in_mbs: float = Field(..., alias='virtualMemoryInMBs', description='Process virtual memory in Megabytes')
    physical_memory_in_mbs: float = Field(..., alias='physicalMemoryInMBs', description='Procress physical memory in Megabytes')
    max_process_count: int = Field(..., alias='maxProcessCount', description='Maximum number of processes running at time of collection', ge=0)


class TopProcessesUsageTrendAggregation(OpsiBaseModel):
    """Usage data per host top process."""

    command: str = Field(..., alias='command', description='Command line and arguments used to launch process')
    usage_data: list[TopProcessesUsageTrend] = Field(..., alias='usageData', description='List of usage data samples for a top process')


class UpdateAutonomousDatabaseInsightDetails(OpsiBaseModel):
    """Update fields for an autonomous database insight. Include only mutable fields that should change."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdateAwrHubDetails(OpsiRequestModel):
    """Update fields for an AWR Hub, such as display name and tags. Include only fields that should change."""

    display_name: str | None = Field(None, alias='displayName', description='User-friedly name of AWR Hub that does not have to be unique.')


class UpdateAwrHubSourceDetails(OpsiRequestModel):
    """Awr hub source update object information."""

    type: Literal['ADW_S', 'ATP_S', 'ADW_D', 'ATP_D', 'EXTERNAL_PDB', 'EXTERNAL_NONCDB', 'COMANAGED_VM_CDB', 'COMANAGED_VM_PDB', 'COMANAGED_VM_NONCDB', 'COMANAGED_BM_CDB', 'COMANAGED_BM_PDB', 'COMANAGED_BM_NONCDB', 'COMANAGED_EXACS_CDB', 'COMANAGED_EXACS_PDB', 'COMANAGED_EXACS_NONCDB', 'LH_S', 'APEX_S', 'AJD_S', 'AVD_S', 'LH_D', 'APEX_D', 'AJD_D', 'AVD_D', 'UNDEFINED'] | None = Field(None, alias='type', description='source type of the database\n\nAllowed values for this property are: "ADW_S", "ATP_S", "ADW_D", "ATP_D", "EXTERNAL_PDB", "EXTERNAL_NONCDB", "COMANAGED_VM_CDB", "COMANAGED_VM_PDB", "COMANAGED_VM_NONCDB", "COMANAGED_BM_CDB", "COMANAGED_BM_PDB", "COMANAGED_BM_NONCDB", "COMANAGED_EXACS_CDB", "COMANAGED_EXACS_PDB", "COMANAGED_EXACS_NONCDB", "LH_S", "APEX_S", "AJD_S", "AVD_S", "LH_D", "APEX_D", "AJD_D", "AVD_D", "UNDEFINED"')


class UpdateBasicConfigurationItemDetails(OpsiBaseModel):
    """Configuration item details for OPSI configuration update."""

    config_item_type: Literal['BASIC'] = Field(..., alias='configItemType', description='Gets the config_item_type of this UpdateConfigurationItemDetails.\nType of configuration item.\n\nAllowed values for this property are: "BASIC"')
    name: str | None = Field(None, alias='name', description='Name of configuration item.')
    value: str | None = Field(None, alias='value', description='Value of configuration item.')


class UpdateChargebackPlanDetails(OpsiRequestModel):
    """The details used to update a Ops Insights chargeback plan."""

    plan_description: str | None = Field(None, alias='planDescription', description='Description of OPSI Chargeback Plan.')
    plan_name: str | None = Field(None, alias='planName', description='Name for the OPSI Chargeback plan.')
    plan_custom_items: list[CreatePlanCustomItemDetails] | None = Field(None, alias='planCustomItems', description='List of chargeback plan customizations.')


class UpdateChargebackPlanReportDetails(OpsiRequestModel):
    """The details used to update a Ops Insights chargeback plan report."""

    report_name: str = Field(..., alias='reportName', description='The chargeback plan report name.')
    report_properties: ReportPropertyDetails = Field(..., alias='reportProperties', description='The report_properties field of UpdateChargebackPlanReportDetails.')


class UpdateConfigurationItemDetails(OpsiBaseModel):
    """Configuration item details for OPSI configuration update."""

    config_item_type: Literal['BASIC'] = Field(..., alias='configItemType', description='Type of configuration item.\n\nAllowed values for this property are: "BASIC"')


class UpdateDatabaseInsightDetails(OpsiRequestModel):
    """Base update payload for database insights. Include the entitySource discriminator and any mutable tags or subtype fields to change."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Source of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')


class UpdateEmManagedExternalDatabaseInsightDetails(OpsiBaseModel):
    """Update fields for an Enterprise Manager-managed external database insight."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdateEmManagedExternalExadataInsightDetails(OpsiBaseModel):
    """Update fields for an Enterprise Manager-managed external Exadata insight."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateExadataInsightDetails.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateExadataInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateExadataInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    is_auto_sync_enabled: bool | None = Field(None, alias='isAutoSyncEnabled', description='Set to true to enable automatic enablement and disablement of related targets from Enterprise Manager. New resources (e.g. Database Insights) will be placed in the same compartment as the related Exadata Insight.')


class UpdateEmManagedExternalHostInsightDetails(OpsiBaseModel):
    """Update fields for an Enterprise Manager-managed external host insight."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateHostInsightDetails.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateHostInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateHostInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdateEnterpriseManagerBridgeDetails(OpsiRequestModel):
    """Update fields for an Enterprise Manager bridge, such as display name, description, and tags."""

    display_name: str | None = Field(None, alias='displayName', description='User-friedly name of Enterprise Manager Bridge that does not have to be unique.')
    description: str | None = Field(None, alias='description', description='Description of Enterprise Manager Bridge')


class UpdateExadataInsightDetails(OpsiRequestModel):
    """Base update payload for Exadata insights. Include the entitySource discriminator and any mutable tags or subtype fields to change."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Source of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')


class UpdateExternalMysqlDatabaseInsightDetails(OpsiBaseModel):
    """Database insight resource."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdateHostInsightDetails(OpsiRequestModel):
    """Base update payload for host insights. Include the entitySource discriminator and any mutable tags or subtype fields to change."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Source of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')


class UpdateMacsManagedAutonomousDatabaseInsightDetails(OpsiBaseModel):
    """The freeformTags and definedTags to be updated."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdateMacsManagedCloudDatabaseHostInsightDetails(OpsiBaseModel):
    """Update fields for a MACS-managed cloud database host insight."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateHostInsightDetails.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateHostInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateHostInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdateMacsManagedCloudDatabaseInsightDetails(OpsiBaseModel):
    """The freeformTags and definedTags to be updated."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdateMacsManagedCloudExadataInsightDetails(OpsiBaseModel):
    """Update fields for a MACS-managed cloud Exadata insight."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateExadataInsightDetails.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateExadataInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateExadataInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdateMacsManagedCloudHostInsightDetails(OpsiBaseModel):
    """Update fields for a MACS-managed cloud host insight."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateHostInsightDetails.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateHostInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateHostInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdateMacsManagedExternalDatabaseInsightDetails(OpsiBaseModel):
    """The freeformTags and definedTags to be updated."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdateMacsManagedExternalHostInsightDetails(OpsiBaseModel):
    """Update fields for a MACS-managed external host insight."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateHostInsightDetails.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateHostInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateHostInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdateMdsMySqlDatabaseInsight(OpsiBaseModel):
    """Database insight resource."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdateNewsReportDetails(OpsiRequestModel):
    """The information about the news report to be updated."""

    status: Literal['DISABLED', 'ENABLED', 'TERMINATED'] | None = Field(None, alias='status', description='Defines if the news report will be enabled or disabled.\n\nAllowed values for this property are: "DISABLED", "ENABLED", "TERMINATED"')
    news_frequency: Literal['WEEKLY', 'DAILY', 'HOURLY'] | None = Field(None, alias='newsFrequency', description='News report frequency.\n\nAllowed values for this property are: "WEEKLY", "DAILY", "HOURLY"')
    locale: Literal['EN'] | None = Field(None, alias='locale', description='Language of the news report.\n\nAllowed values for this property are: "EN"')
    content_types: NewsContentTypes | None = Field(None, alias='contentTypes', description='The content_types field of UpdateNewsReportDetails.')
    ons_topic_id: str | None = Field(None, alias='onsTopicId', description='The OCID of the ONS topic.')
    name: str | None = Field(None, alias='name', description='The news report name.')
    description: str | None = Field(None, alias='description', description='The description of the news report.')
    day_of_week: Literal['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'] | None = Field(None, alias='dayOfWeek', description='Day of the week in which the news report will be sent if the frequency is set to WEEKLY.\n\nAllowed values for this property are: "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"')
    are_child_compartments_included: bool | None = Field(None, alias='areChildCompartmentsIncluded', description='A flag to consider the resources within a given compartment and all sub-compartments.')


class UpdateOperationsInsightsPrivateEndpointDetails(OpsiRequestModel):
    """The details used to update a Operation Insights private endpoint."""

    display_name: str | None = Field(None, alias='displayName', description='The display name of the private endpoint.')
    description: str | None = Field(None, alias='description', description='The description of the private endpoint.')
    nsg_ids: list[str] | None = Field(None, alias='nsgIds', description='The OCID of the network security groups that the Private service accessed the database.')


class UpdateOperationsInsightsWarehouseDetails(OpsiRequestModel):
    """Update fields for an Operations Insights warehouse, such as display name, allocated CPU, storage, and tags."""

    display_name: str | None = Field(None, alias='displayName', description='User-friedly name of Ops Insights Warehouse that does not have to be unique.')
    cpu_allocated: float | None = Field(None, alias='cpuAllocated', description='Number of CPUs allocated to OPSI Warehouse ADW.')
    compute_model: str | None = Field(None, alias='computeModel', description='The compute model for the OPSI warehouse ADW (OCPU or ECPU)')
    storage_allocated_in_gbs: float | None = Field(None, alias='storageAllocatedInGBs', description='Storage allocated to OPSI Warehouse ADW.')


class UpdateOperationsInsightsWarehouseUserDetails(OpsiRequestModel):
    """Update fields for an Operations Insights warehouse user, including access flags, password, and tags."""

    connection_password: str | None = Field(None, alias='connectionPassword', description='User provided connection password for the AWR Data,  Enterprise Manager Data and Ops Insights OPSI Hub.')
    is_awr_data_access: bool | None = Field(None, alias='isAwrDataAccess', description='Indicate whether user has access to AWR data.')
    is_em_data_access: bool | None = Field(None, alias='isEmDataAccess', description='Indicate whether user has access to EM data.')
    is_opsi_data_access: bool | None = Field(None, alias='isOpsiDataAccess', description='Indicate whether user has access to OPSI data.')


class UpdateOpsiConfigurationDetails(OpsiRequestModel):
    """Information to be updated in OPSI configuration resource."""

    opsi_config_type: Literal['UX_CONFIGURATION'] = Field(..., alias='opsiConfigType', description='OPSI configuration type.\n\nAllowed values for this property are: "UX_CONFIGURATION"')
    display_name: str | None = Field(None, alias='displayName', description='User-friendly display name for the OPSI configuration. The name does not have to be unique.')
    description: str | None = Field(None, alias='description', description='Description of OPSI configuration.')
    config_items: list[UpdateConfigurationItemDetails] | None = Field(None, alias='configItems', description='Array of configuration items with custom values. All and only configuration items requiring custom values should be part of this array.\nThis array overwrites the existing custom configuration items array for this resource.')


class UpdateOpsiUxConfigurationDetails(OpsiBaseModel):
    """Information to be updated in OPSI UX configuration."""

    opsi_config_type: Literal['UX_CONFIGURATION'] = Field(..., alias='opsiConfigType', description='Gets the opsi_config_type of this UpdateOpsiConfigurationDetails.\nOPSI configuration type.\n\nAllowed values for this property are: "UX_CONFIGURATION"')
    display_name: str | None = Field(None, alias='displayName', description='Gets the display_name of this UpdateOpsiConfigurationDetails.\nUser-friendly display name for the OPSI configuration. The name does not have to be unique.')
    description: str | None = Field(None, alias='description', description='Gets the description of this UpdateOpsiConfigurationDetails.\nDescription of OPSI configuration.')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateOpsiConfigurationDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateOpsiConfigurationDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')
    system_tags: dict[str, dict[str, Any]] | None = Field(None, alias='systemTags', description='Gets the system_tags of this UpdateOpsiConfigurationDetails.\nSystem tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"orcl-cloud": {"free-tier-retained": "true"}}`')
    config_items: list[UpdateConfigurationItemDetails] | None = Field(None, alias='configItems', description='Gets the config_items of this UpdateOpsiConfigurationDetails.\nArray of configuration items with custom values. All and only configuration items requiring custom values should be part of this array.\nThis array overwrites the existing custom configuration items array for this resource.')


class UpdatePeComanagedDatabaseInsightDetails(OpsiBaseModel):
    """The freeformTags and definedTags to be updated."""

    entity_source: Literal['AUTONOMOUS_DATABASE', 'EM_MANAGED_EXTERNAL_DATABASE', 'MACS_MANAGED_EXTERNAL_DATABASE', 'PE_COMANAGED_DATABASE', 'MDS_MYSQL_DATABASE_SYSTEM', 'EXTERNAL_MYSQL_DATABASE_SYSTEM', 'MACS_MANAGED_CLOUD_DATABASE', 'MACS_MANAGED_AUTONOMOUS_DATABASE'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateDatabaseInsightDetails.\nSource of the database entity.\n\nAllowed values for this property are: "AUTONOMOUS_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "MACS_MANAGED_EXTERNAL_DATABASE", "PE_COMANAGED_DATABASE", "MDS_MYSQL_DATABASE_SYSTEM", "EXTERNAL_MYSQL_DATABASE_SYSTEM", "MACS_MANAGED_CLOUD_DATABASE", "MACS_MANAGED_AUTONOMOUS_DATABASE"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateDatabaseInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateDatabaseInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdatePeComanagedExadataInsightDetails(OpsiBaseModel):
    """Update fields for a private-endpoint co-managed Exadata insight."""

    entity_source: Literal['EM_MANAGED_EXTERNAL_EXADATA', 'PE_COMANAGED_EXADATA', 'MACS_MANAGED_CLOUD_EXADATA'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateExadataInsightDetails.\nSource of the Exadata system.\n\nAllowed values for this property are: "EM_MANAGED_EXTERNAL_EXADATA", "PE_COMANAGED_EXADATA", "MACS_MANAGED_CLOUD_EXADATA"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateExadataInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateExadataInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UpdatePeComanagedHostInsightDetails(OpsiBaseModel):
    """Update fields for a private-endpoint co-managed host insight."""

    entity_source: Literal['MACS_MANAGED_EXTERNAL_HOST', 'EM_MANAGED_EXTERNAL_HOST', 'MACS_MANAGED_CLOUD_HOST', 'PE_COMANAGED_HOST', 'MACS_MANAGED_CLOUD_DB_HOST'] = Field(..., alias='entitySource', description='Gets the entity_source of this UpdateHostInsightDetails.\nSource of the host entity.\n\nAllowed values for this property are: "MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST", "MACS_MANAGED_CLOUD_HOST", "PE_COMANAGED_HOST", "MACS_MANAGED_CLOUD_DB_HOST"')
    freeform_tags: dict[str, str] | None = Field(None, alias='freeformTags', description='Gets the freeform_tags of this UpdateHostInsightDetails.\nSimple key-value pair that is applied without any predefined name, type or scope. Exists for cross-compatibility only.\nExample: `{"bar-key": "value"}`')
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, alias='definedTags', description='Gets the defined_tags of this UpdateHostInsightDetails.\nDefined tags for this resource. Each key is predefined and scoped to a namespace.\nExample: `{"foo-namespace": {"bar-key": "value"}}`')


class UxConfigurationItemsCollection(OpsiBaseModel):
    """Collection of ux configuration item summary objects."""

    opsi_config_type: Literal['UX_CONFIGURATION', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='opsiConfigType', description='Gets the opsi_config_type of this ConfigurationItemsCollection.\nOPSI configuration type.\n\nAllowed values for this property are: "UX_CONFIGURATION", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    config_items: list[ConfigurationItemSummary] | None = Field(None, alias='configItems', description='Gets the config_items of this ConfigurationItemsCollection.\nArray of configuration item summary objects.')


class VmClusterSummary(OpsiBaseModel):
    """Partial information about the VM Cluster which includes name, memory allocated etc."""

    vmcluster_name: str = Field(..., alias='vmclusterName', description='The name of the VM Cluster.')
    memory_allocated_in_gbs: int | None = Field(None, alias='memoryAllocatedInGBs', description='The memory allocated on a VM Cluster.')
    cpu_allocated: int | None = Field(None, alias='cpuAllocated', description='The CPU allocated on a VM Cluster.')
    db_nodes_count: int | None = Field(None, alias='dbNodesCount', description='The number of DB nodes on a VM Cluster.', ge=0)
    storage_allocated_in_gbs: int | None = Field(None, alias='storageAllocatedInGBs', description='The storage allocated on a VM Cluster.')
    vm_cluster_id: str | None = Field(None, alias='vmClusterId', description='The OCID of the VM Cluster.')


class WarehouseDataObjectCollection(OpsiBaseModel):
    """Collection of Warehouse data object summary objects."""

    items: list[WarehouseDataObjectSummary] = Field(..., alias='items', description='Array of Warehouse data object summary objects.')


class WarehouseDataObjectDetails(OpsiBaseModel):
    """Warehouse data object details."""

    data_object_type: Literal['VIEW', 'TABLE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='dataObjectType', description='Type of the data object.\n\nAllowed values for this property are: "VIEW", "TABLE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')


class WarehouseDataObjectSummary(OpsiBaseModel):
    """Summary of a Warehouse data object."""

    data_object_type: Literal['VIEW', 'TABLE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='dataObjectType', description='Type of the data object.\n\nAllowed values for this property are: "VIEW", "TABLE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    name: str | None = Field(None, alias='name', description='Name of the data object, which can be used in data object queries just like how view names are used in a query.')
    owner: str | None = Field(None, alias='owner', description='Owner of the data object, which can be used in data object queries in front of data object names just like SCHEMA.VIEW notation in queries.')
    details: WarehouseDataObjectDetails | None = Field(None, alias='details', description='The details field of WarehouseDataObjectSummary.')


class WarehouseTableDataObjectDetails(OpsiBaseModel):
    """Details of a TABLE type data object in a Warehouse."""

    data_object_type: Literal['VIEW', 'TABLE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='dataObjectType', description='Gets the data_object_type of this WarehouseDataObjectDetails.\nType of the data object.\n\nAllowed values for this property are: "VIEW", "TABLE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    columns_metadata: list[DataObjectColumnMetadata] | None = Field(None, alias='columnsMetadata', description='Metadata of columns in the data object.')


class WarehouseViewDataObjectDetails(OpsiBaseModel):
    """Details of a VIEW type data object in a Warehouse."""

    data_object_type: Literal['VIEW', 'TABLE', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='dataObjectType', description='Gets the data_object_type of this WarehouseDataObjectDetails.\nType of the data object.\n\nAllowed values for this property are: "VIEW", "TABLE", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    columns_metadata: list[DataObjectColumnMetadata] | None = Field(None, alias='columnsMetadata', description='Metadata of columns in the data object.')


class WorkRequest(OpsiBaseModel):
    """A description of workrequest status."""

    operation_type: Literal['ENABLE_DATABASE_INSIGHT', 'DISABLE_DATABASE_INSIGHT', 'UPDATE_DATABASE_INSIGHT', 'CREATE_DATABASE_INSIGHT', 'MOVE_DATABASE_INSIGHT', 'DELETE_DATABASE_INSIGHT', 'CREATE_ENTERPRISE_MANAGER_BRIDGE', 'UDPATE_ENTERPRISE_MANAGER_BRIDGE', 'MOVE_ENTERPRISE_MANAGER_BRIDGE', 'DELETE_ENTERPRISE_MANAGER_BRIDGE', 'ENABLE_HOST_INSIGHT', 'DISABLE_HOST_INSIGHT', 'UPDATE_HOST_INSIGHT', 'CREATE_HOST_INSIGHT', 'MOVE_HOST_INSIGHT', 'DELETE_HOST_INSIGHT', 'CREATE_EXADATA_INSIGHT', 'ENABLE_EXADATA_INSIGHT', 'DISABLE_EXADATA_INSIGHT', 'UPDATE_EXADATA_INSIGHT', 'MOVE_EXADATA_INSIGHT', 'DELETE_EXADATA_INSIGHT', 'ADD_EXADATA_INSIGHT_MEMBERS', 'EXADATA_AUTO_SYNC', 'UPDATE_OPSI_WAREHOUSE', 'CREATE_OPSI_WAREHOUSE', 'MOVE_OPSI_WAREHOUSE', 'DELETE_OPSI_WAREHOUSE', 'ROTATE_OPSI_WAREHOUSE_WALLET', 'UPDATE_OPSI_WAREHOUSE_USER', 'CREATE_OPSI_WAREHOUSE_USER', 'MOVE_OPSI_WAREHOUSE_USER', 'DELETE_OPSI_WAREHOUSE_USER', 'UPDATE_AWRHUB', 'CREATE_AWRHUB', 'MOVE_AWRHUB', 'DELETE_AWRHUB', 'UPDATE_PRIVATE_ENDPOINT', 'CREATE_PRIVATE_ENDPOINT', 'MOVE_PRIVATE_ENDPOINT', 'DELETE_PRIVATE_ENDPOINT', 'CHANGE_PE_COMANAGED_DATABASE_INSIGHT_DETAILS', 'UPDATE_OPSI_CONFIGURATION', 'CREATE_OPSI_CONFIGURATION', 'MOVE_OPSI_CONFIGURATION', 'DELETE_OPSI_CONFIGURATION', 'ENABLE_ADB_ADVANCED_FEATURES', 'DISABLE_ADB_ADVANCED_FEATURES', 'UPDATE_ADB_ADVANCED_FEATURES', 'CREATE_NEWS_REPORT', 'ENABLE_NEWS_REPORT', 'DISABLE_NEWS_REPORT', 'UPDATE_NEWS_REPORT', 'MOVE_NEWS_REPORT', 'DELETE_NEWS_REPORT', 'CREATE_AWRHUB_SOURCE', 'DELETE_AWRHUB_SOURCE', 'UPDATE_AWRHUB_SOURCE', 'MOVE_AWRHUB_SOURCE', 'ENABLE_AWRHUB_SOURCE', 'DISABLE_AWRHUB_SOURCE', 'CHANGE_MACS_MANAGED_CLOUD_DATABASE_INSIGHT_CONNECTION_DETAILS', 'TEST_MACS_MANAGED_CLOUD_DATABASE_INSIGHT_CONNECTION_DETAILS', 'CHANGE_EXTERNAL_MYSQL_DATABASE_INSIGHT_CONNECTION_DETAILS', 'CHANGE_MACS_MANAGED_ADB_CONNECTION_DETAILS', 'TEST_MACS_MANAGED_ADB_CONNECTION_DETAILS', 'SYNCHRONIZE_AUTONOMOUS_DATABASE_TO_EXADATA', 'CREATE_CHARGE_BACK', 'ENABLE_CHARGE_BACK', 'DISABLE_CHARGE_BACK', 'UPDATE_CHARGE_BACK', 'MOVE_CHARGE_BACK', 'DELETE_CHARGE_BACK', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='operationType', description='Type of the work request\n\nAllowed values for this property are: "ENABLE_DATABASE_INSIGHT", "DISABLE_DATABASE_INSIGHT", "UPDATE_DATABASE_INSIGHT", "CREATE_DATABASE_INSIGHT", "MOVE_DATABASE_INSIGHT", "DELETE_DATABASE_INSIGHT", "CREATE_ENTERPRISE_MANAGER_BRIDGE", "UDPATE_ENTERPRISE_MANAGER_BRIDGE", "MOVE_ENTERPRISE_MANAGER_BRIDGE", "DELETE_ENTERPRISE_MANAGER_BRIDGE", "ENABLE_HOST_INSIGHT", "DISABLE_HOST_INSIGHT", "UPDATE_HOST_INSIGHT", "CREATE_HOST_INSIGHT", "MOVE_HOST_INSIGHT", "DELETE_HOST_INSIGHT", "CREATE_EXADATA_INSIGHT", "ENABLE_EXADATA_INSIGHT", "DISABLE_EXADATA_INSIGHT", "UPDATE_EXADATA_INSIGHT", "MOVE_EXADATA_INSIGHT", "DELETE_EXADATA_INSIGHT", "ADD_EXADATA_INSIGHT_MEMBERS", "EXADATA_AUTO_SYNC", "UPDATE_OPSI_WAREHOUSE", "CREATE_OPSI_WAREHOUSE", "MOVE_OPSI_WAREHOUSE", "DELETE_OPSI_WAREHOUSE", "ROTATE_OPSI_WAREHOUSE_WALLET", "UPDATE_OPSI_WAREHOUSE_USER", "CREATE_OPSI_WAREHOUSE_USER", "MOVE_OPSI_WAREHOUSE_USER", "DELETE_OPSI_WAREHOUSE_USER", "UPDATE_AWRHUB", "CREATE_AWRHUB", "MOVE_AWRHUB", "DELETE_AWRHUB", "UPDATE_PRIVATE_ENDPOINT", "CREATE_PRIVATE_ENDPOINT", "MOVE_PRIVATE_ENDPOINT", "DELETE_PRIVATE_ENDPOINT", "CHANGE_PE_COMANAGED_DATABASE_INSIGHT_DETAILS", "UPDATE_OPSI_CONFIGURATION", "CREATE_OPSI_CONFIGURATION", "MOVE_OPSI_CONFIGURATION", "DELETE_OPSI_CONFIGURATION", "ENABLE_ADB_ADVANCED_FEATURES", "DISABLE_ADB_ADVANCED_FEATURES", "UPDATE_ADB_ADVANCED_FEATURES", "CREATE_NEWS_REPORT", "ENABLE_NEWS_REPORT", "DISABLE_NEWS_REPORT", "UPDATE_NEWS_REPORT", "MOVE_NEWS_REPORT", "DELETE_NEWS_REPORT", "CREATE_AWRHUB_SOURCE", "DELETE_AWRHUB_SOURCE", "UPDATE_AWRHUB_SOURCE", "MOVE_AWRHUB_SOURCE", "ENABLE_AWRHUB_SOURCE", "DISABLE_AWRHUB_SOURCE", "CHANGE_MACS_MANAGED_CLOUD_DATABASE_INSIGHT_CONNECTION_DETAILS", "TEST_MACS_MANAGED_CLOUD_DATABASE_INSIGHT_CONNECTION_DETAILS", "CHANGE_EXTERNAL_MYSQL_DATABASE_INSIGHT_CONNECTION_DETAILS", "CHANGE_MACS_MANAGED_ADB_CONNECTION_DETAILS", "TEST_MACS_MANAGED_ADB_CONNECTION_DETAILS", "SYNCHRONIZE_AUTONOMOUS_DATABASE_TO_EXADATA", "CREATE_CHARGE_BACK", "ENABLE_CHARGE_BACK", "DISABLE_CHARGE_BACK", "UPDATE_CHARGE_BACK", "MOVE_CHARGE_BACK", "DELETE_CHARGE_BACK", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    status: Literal['ACCEPTED', 'IN_PROGRESS', 'WAITING', 'FAILED', 'SUCCEEDED', 'CANCELING', 'CANCELED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='status', description='Status of current work request.\n\nAllowed values for this property are: "ACCEPTED", "IN_PROGRESS", "WAITING", "FAILED", "SUCCEEDED", "CANCELING", "CANCELED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    id: str = Field(..., alias='id', description='The id of the work request.')
    compartment_id: str = Field(..., alias='compartmentId', description='The ocid of the compartment that contains the work request. Work requests should be scoped to\nthe same compartment as the resource the work request affects. If the work request affects multiple resources,\nand those resources are not in the same compartment, it is up to the service team to pick the primary\nresource whose compartment should be used')
    resources: list[WorkRequestResource] = Field(..., alias='resources', description='The resources affected by this work request.')
    percent_complete: float = Field(..., alias='percentComplete', description='Percentage of the request completed.')
    time_accepted: datetime = Field(..., alias='timeAccepted', description='The date and time the request was created, as described in RFC 3339, section 14.29.')
    time_started: datetime | None = Field(None, alias='timeStarted', description='The date and time the request was started, as described in RFC 3339, section 14.29.')
    time_finished: datetime | None = Field(None, alias='timeFinished', description='The date and time the object was finished, as described in RFC 3339.')


class WorkRequestCollection(OpsiBaseModel):
    """Results of a workRequest search. Contains both WorkRequest items and other information, such as metadata."""

    items: list[WorkRequest] = Field(..., alias='items', description='List of workRequests.')


class WorkRequestError(OpsiBaseModel):
    """An error encountered while executing a work request."""

    code: str = Field(..., alias='code', description='A machine-usable code for the error that occured. Error codes are listed on.')
    message: str = Field(..., alias='message', description='A human readable description of the issue encountered.')
    timestamp: datetime = Field(..., alias='timestamp', description='The time the error occured. An RFC3339 formatted datetime string.')


class WorkRequestErrorCollection(OpsiBaseModel):
    """Results of a workRequestError search. Contains both WorkRequestError items and other information, such as metadata."""

    items: list[WorkRequestError] = Field(..., alias='items', description='List of workRequestError objects.')


class WorkRequestLogEntry(OpsiBaseModel):
    """A log message from the execution of a work request."""

    message: str = Field(..., alias='message', description='Human-readable log message.')
    timestamp: datetime = Field(..., alias='timestamp', description='The time the log message was written. An RFC3339 formatted datetime string')


class WorkRequestLogEntryCollection(OpsiBaseModel):
    """Results of a workRequestLog search. Contains both workRequestLog items and other information, such as metadata."""

    items: list[WorkRequestLogEntry] = Field(..., alias='items', description='List of workRequestLogEntries.')


class WorkRequestResource(OpsiBaseModel):
    """A resource created or operated on by a work request."""

    entity_type: str = Field(..., alias='entityType', description='The resource type the work request affects.')
    action_type: Literal['CREATED', 'UPDATED', 'DELETED', 'IN_PROGRESS', 'RELATED', 'FAILED', 'UNKNOWN_ENUM_VALUE'] = Field(..., alias='actionType', description='The way in which this resource is affected by the work tracked in the work request.\nA resource being created, updated, or deleted will remain in the IN_PROGRESS state until\nwork is complete for that resource at which point it will transition to CREATED, UPDATED,\nor DELETED, respectively.\n\nAllowed values for this property are: "CREATED", "UPDATED", "DELETED", "IN_PROGRESS", "RELATED", "FAILED", \'UNKNOWN_ENUM_VALUE\'.\nAny unrecognized values returned by a service will be mapped to \'UNKNOWN_ENUM_VALUE\'.')
    identifier: str = Field(..., alias='identifier', description='The identifier of the resource the work request affects.')
    entity_uri: str | None = Field(None, alias='entityUri', description='The URI path that the user can do a GET on to access the resource')
    metadata: dict[str, str] | None = Field(None, alias='metadata', description='Additional information that helps to explain the resource.')


class WorkRequests(OpsiBaseModel):
    """Logical grouping used for Ops Insights Work Request operations."""

    work_requests: Any | None = Field(None, alias='workRequests', description='OPSI Work Request Object.')


OPSI_MODEL_NAMES = ['AddEmManagedExternalExadataInsightMembersDetails', 'AddExadataInsightMembersDetails', 'AddMacsManagedCloudExadataInsightMembersDetails', 'AddPeComanagedExadataInsightMembersDetails', 'AddmDbCollection', 'AddmDbFindingAggregation', 'AddmDbFindingAggregationCollection', 'AddmDbFindingCategoryCollection', 'AddmDbFindingCategorySummary', 'AddmDbFindingsTimeSeriesCollection', 'AddmDbFindingsTimeSeriesSummary', 'AddmDbParameterAggregation', 'AddmDbParameterAggregationCollection', 'AddmDbParameterCategoryCollection', 'AddmDbParameterCategorySummary', 'AddmDbParameterChangeAggregation', 'AddmDbParameterChangeAggregationCollection', 'AddmDbRecommendationAggregation', 'AddmDbRecommendationAggregationCollection', 'AddmDbRecommendationCategoryCollection', 'AddmDbRecommendationCategorySummary', 'AddmDbRecommendationsTimeSeriesCollection', 'AddmDbRecommendationsTimeSeriesSummary', 'AddmDbSchemaObjectCollection', 'AddmDbSchemaObjectSummary', 'AddmDbSqlStatementCollection', 'AddmDbSqlStatementSummary', 'AddmDbSummary', 'AddmReport', 'AutonomousDatabaseConfigurationSummary', 'AutonomousDatabaseInsight', 'AutonomousDatabaseInsightSummary', 'AwrDatabaseCollection', 'AwrDatabaseCpuUsageCollection', 'AwrDatabaseCpuUsageSummary', 'AwrDatabaseMetricCollection', 'AwrDatabaseMetricSummary', 'AwrDatabaseParameterChangeCollection', 'AwrDatabaseParameterChangeSummary', 'AwrDatabaseParameterCollection', 'AwrDatabaseParameterSummary', 'AwrDatabaseReport', 'AwrDatabaseSnapshotCollection', 'AwrDatabaseSnapshotRangeCollection', 'AwrDatabaseSnapshotRangeSummary', 'AwrDatabaseSnapshotSummary', 'AwrDatabaseSqlReport', 'AwrDatabaseSummary', 'AwrDatabaseSysstatCollection', 'AwrDatabaseSysstatSummary', 'AwrDatabaseTopWaitEventCollection', 'AwrDatabaseTopWaitEventSummary', 'AwrDatabaseWaitEventBucketCollection', 'AwrDatabaseWaitEventBucketSummary', 'AwrDatabaseWaitEventCollection', 'AwrDatabaseWaitEventSummary', 'AwrHub', 'AwrHubObjects', 'AwrHubSource', 'AwrHubSourceSummary', 'AwrHubSourceSummaryCollection', 'AwrHubSources', 'AwrHubSummary', 'AwrHubSummaryCollection', 'AwrHubs', 'AwrQueryResult', 'AwrReport', 'AwrSnapshotCollection', 'AwrSnapshotSummary', 'AwrSourceSummary', 'BasicConfigurationItemMetadata', 'BasicConfigurationItemSummary', 'ChangeAutonomousDatabaseInsightAdvancedFeaturesDetails', 'ChangeAwrHubSourceCompartmentDetails', 'ChangeChargebackPlanCompartmentDetails', 'ChangeDatabaseInsightCompartmentDetails', 'ChangeEnterpriseManagerBridgeCompartmentDetails', 'ChangeExadataInsightCompartmentDetails', 'ChangeExternalMysqlDatabaseInsightConnectionDetails', 'ChangeHostInsightCompartmentDetails', 'ChangeMacsManagedAutonomousDatabaseInsightConnectionDetails', 'ChangeMacsManagedCloudDatabaseInsightConnectionDetails', 'ChangeNewsReportCompartmentDetails', 'ChangeOperationsInsightsPrivateEndpointCompartmentDetails', 'ChangeOperationsInsightsWarehouseCompartmentDetails', 'ChangeOpsiConfigurationCompartmentDetails', 'ChangePeComanagedDatabaseInsightDetails', 'ChargebackPlan', 'ChargebackPlanCollection', 'ChargebackPlanDetails', 'ChargebackPlanReport', 'ChargebackPlanReportCollection', 'ChargebackPlanReportSummary', 'ChargebackPlanSummary', 'CloudImportableComputeEntitySummary', 'ConfigurationItemAllowedValueDetails', 'ConfigurationItemFreeTextAllowedValueDetails', 'ConfigurationItemLimitAllowedValueDetails', 'ConfigurationItemMetadata', 'ConfigurationItemPickAllowedValueDetails', 'ConfigurationItemSummary', 'ConfigurationItemUnitDetails', 'ConfigurationItemsCollection', 'ConnectionDetails', 'CreateAutonomousDatabaseInsightDetails', 'CreateAwrHubDetails', 'CreateAwrHubSourceDetails', 'CreateBasicConfigurationItemDetails', 'CreateChargebackPlanDetails', 'CreateChargebackPlanExadataDetails', 'CreateChargebackPlanReportDetails', 'CreateConfigurationItemDetails', 'CreateDatabaseInsightDetails', 'CreateEmManagedExternalDatabaseInsightDetails', 'CreateEmManagedExternalExadataInsightDetails', 'CreateEmManagedExternalExadataMemberEntityDetails', 'CreateEmManagedExternalHostInsightDetails', 'CreateEnterpriseManagerBridgeDetails', 'CreateExadataInsightDetails', 'CreateExternalMysqlDatabaseInsightDetails', 'CreateHostInsightDetails', 'CreateMacsManagedAutonomousDatabaseInsightDetails', 'CreateMacsManagedCloudDatabaseInsightDetails', 'CreateMacsManagedCloudExadataClusterDetails', 'CreateMacsManagedCloudExadataInsightDetails', 'CreateMacsManagedCloudExadataVmclusterDetails', 'CreateMacsManagedCloudHostInsightDetails', 'CreateMacsManagedExternalHostInsightDetails', 'CreateMdsMySqlDatabaseInsightDetails', 'CreateNewsReportDetails', 'CreateOperationsInsightsPrivateEndpointDetails', 'CreateOperationsInsightsWarehouseDetails', 'CreateOperationsInsightsWarehouseUserDetails', 'CreateOpsiConfigurationDetails', 'CreateOpsiUxConfigurationDetails', 'CreatePeComanagedDatabaseInsightDetails', 'CreatePeComanagedExadataInsightDetails', 'CreatePeComanagedExadataVmclusterDetails', 'CreatePlanCustomItemDetails', 'CredentialByIam', 'CredentialByNamedCredentials', 'CredentialByVault', 'CredentialDetails', 'CredentialsBySource', 'DBConnectionStatus', 'DBExternalInstance', 'DBExternalProperties', 'DBOSConfigInstance', 'DBParameters', 'DataObjectBindParameter', 'DataObjectColumnMetadata', 'DataObjectColumnUnit', 'DataObjectCoreColumnUnit', 'DataObjectCustomColumnUnit', 'DataObjectDataSizeColumnUnit', 'DataObjectFrequencyColumnUnit', 'DataObjectOtherStandardColumnUnit', 'DataObjectPowerColumnUnit', 'DataObjectQuery', 'DataObjectQueryTimeFilters', 'DataObjectRateColumnUnit', 'DataObjectStandardQuery', 'DataObjectTemperatureColumnUnit', 'DataObjectTemplatizedQuery', 'DataObjectTimeColumnUnit', 'DatabaseConfigurationCollection', 'DatabaseConfigurationMetricGroup', 'DatabaseConfigurationSummary', 'DatabaseDetails', 'DatabaseInsight', 'DatabaseInsightSummary', 'DatabaseInsights', 'DatabaseInsightsCollection', 'DatabaseInsightsDataObject', 'DatabaseInsightsDataObjectSummary', 'DatabaseParameterTypeDetails', 'DiskGroupDetails', 'DiskStatistics', 'DownloadOperationsInsightsWarehouseWalletDetails', 'EmManagedExternalDatabaseConfigurationSummary', 'EmManagedExternalDatabaseInsight', 'EmManagedExternalDatabaseInsightSummary', 'EmManagedExternalExadataInsight', 'EmManagedExternalExadataInsightSummary', 'EmManagedExternalHostConfigurationSummary', 'EmManagedExternalHostInsight', 'EmManagedExternalHostInsightSummary', 'EnableAutonomousDatabaseInsightAdvancedFeaturesDetails', 'EnableAutonomousDatabaseInsightDetails', 'EnableDatabaseInsightDetails', 'EnableEmManagedExternalDatabaseInsightDetails', 'EnableEmManagedExternalExadataInsightDetails', 'EnableEmManagedExternalHostInsightDetails', 'EnableExadataInsightDetails', 'EnableExternalMysqlDatabaseInsightDetails', 'EnableHostInsightDetails', 'EnableMacsManagedAutonomousDatabaseInsightDetails', 'EnableMacsManagedCloudDatabaseInsightDetails', 'EnableMacsManagedCloudExadataInsightDetails', 'EnableMacsManagedCloudHostInsightDetails', 'EnableMacsManagedExternalHostInsightDetails', 'EnableMdsMySqlDatabaseInsightDetails', 'EnablePeComanagedDatabaseInsightDetails', 'EnablePeComanagedExadataInsightDetails', 'EnablePlanExadataInsightDetails', 'EnterpriseManagerBridge', 'EnterpriseManagerBridgeCollection', 'EnterpriseManagerBridgeSummary', 'EnterpriseManagerBridges', 'ExadataAsmEntity', 'ExadataCellConfig', 'ExadataConfigurationCollection', 'ExadataConfigurationSummary', 'ExadataDatabaseMachineConfigurationSummary', 'ExadataDatabaseStatisticsSummary', 'ExadataDetails', 'ExadataDiskgroupStatisticsSummary', 'ExadataExaccConfigurationSummary', 'ExadataExacsConfigurationSummary', 'ExadataHostStatisticsSummary', 'ExadataInsight', 'ExadataInsightResourceCapacityTrendAggregation', 'ExadataInsightResourceCapacityTrendSummary', 'ExadataInsightResourceForecastTrendSummary', 'ExadataInsightResourceInsightUtilizationItem', 'ExadataInsightResourceStatistics', 'ExadataInsightResourceStatisticsAggregation', 'ExadataInsightSummary', 'ExadataInsightSummaryCollection', 'ExadataInsights', 'ExadataInsightsDataObject', 'ExadataInsightsDataObjectSummary', 'ExadataMemberCollection', 'ExadataMemberSummary', 'ExadataStorageServerStatisticsSummary', 'ExternalMysqlDatabaseConfigurationSummary', 'ExternalMysqlDatabaseInsight', 'ExternalMysqlDatabaseInsightSummary', 'HistoricalDataItem', 'HostAllocation', 'HostConfigurationCollection', 'HostConfigurationMetricGroup', 'HostConfigurationSummary', 'HostContainers', 'HostCpuHardwareConfiguration', 'HostCpuRecommendations', 'HostCpuStatistics', 'HostCpuUsage', 'HostDetails', 'HostEntities', 'HostFilesystemConfiguration', 'HostFilesystemUsage', 'HostGpuConfiguration', 'HostGpuProcesses', 'HostGpuUsage', 'HostHardwareConfiguration', 'HostImportableAgentEntitySummary', 'HostInsight', 'HostInsightHostRecommendations', 'HostInsightResourceStatisticsAggregation', 'HostInsightSummary', 'HostInsightSummaryCollection', 'HostInsights', 'HostInsightsDataObject', 'HostInsightsDataObjectSummary', 'HostInstanceMap', 'HostIoStatistics', 'HostIoUsage', 'HostMemoryConfiguration', 'HostMemoryRecommendations', 'HostMemoryStatistics', 'HostMemoryUsage', 'HostNetworkActivitySummary', 'HostNetworkConfiguration', 'HostNetworkRecommendations', 'HostNetworkStatistics', 'HostPerformanceMetricGroup', 'HostProduct', 'HostResourceAllocation', 'HostResourceCapacityTrendAggregation', 'HostResourceStatistics', 'HostStorageRecommendations', 'HostStorageStatistics', 'HostTopProcesses', 'HostedEntityCollection', 'HostedEntitySummary', 'ImportableAgentEntitySummary', 'ImportableAgentEntitySummaryCollection', 'ImportableComputeEntitySummary', 'ImportableComputeEntitySummaryCollection', 'ImportableEnterpriseManagerEntity', 'ImportableEnterpriseManagerEntityCollection', 'IndividualOpsiDataObjectDetailsInQuery', 'IngestAddmReportsDetails', 'IngestAddmReportsResponseDetails', 'IngestDatabaseConfigurationDetails', 'IngestDatabaseConfigurationResponseDetails', 'IngestHostConfigurationDetails', 'IngestHostConfigurationResponseDetails', 'IngestHostMetricsDetails', 'IngestHostMetricsResponseDetails', 'IngestMySqlSqlStatsDetails', 'IngestMySqlSqlStatsResponseDetails', 'IngestMySqlSqlTextDetails', 'IngestMySqlSqlTextResponseDetails', 'IngestSqlBucketDetails', 'IngestSqlBucketResponseDetails', 'IngestSqlPlanLinesDetails', 'IngestSqlPlanLinesResponseDetails', 'IngestSqlStatsDetails', 'IngestSqlStatsResponseDetails', 'IngestSqlTextDetails', 'IngestSqlTextResponseDetails', 'InstanceMetrics', 'IoUsageTrend', 'IoUsageTrendAggregation', 'ListObjects', 'MacsManagedAutonomousDatabaseConfigurationSummary', 'MacsManagedAutonomousDatabaseInsight', 'MacsManagedAutonomousDatabaseInsightSummary', 'MacsManagedCloudDatabaseConfigurationSummary', 'MacsManagedCloudDatabaseHostInsight', 'MacsManagedCloudDatabaseHostInsightSummary', 'MacsManagedCloudDatabaseInsight', 'MacsManagedCloudDatabaseInsightSummary', 'MacsManagedCloudDbHostConfigurationSummary', 'MacsManagedCloudExadataInsight', 'MacsManagedCloudExadataInsightSummary', 'MacsManagedCloudHostConfigurationSummary', 'MacsManagedCloudHostInsight', 'MacsManagedCloudHostInsightSummary', 'MacsManagedExternalDatabaseConfigurationSummary', 'MacsManagedExternalDatabaseInsight', 'MacsManagedExternalDatabaseInsightSummary', 'MacsManagedExternalHostConfigurationSummary', 'MacsManagedExternalHostInsight', 'MacsManagedExternalHostInsightSummary', 'MdsMySqlDatabaseInsight', 'MdsMySqlDatabaseInsightSummary', 'MdsMysqlDatabaseConfigurationSummary', 'MySqlSqlStats', 'MySqlSqlText', 'NetworkUsageTrend', 'NetworkUsageTrendAggregation', 'NewsContentTypes', 'NewsReport', 'NewsReportCollection', 'NewsReportSummary', 'NewsReports', 'ObjectSummary', 'OperationsInsightsPrivateEndpoint', 'OperationsInsightsPrivateEndpointCollection', 'OperationsInsightsPrivateEndpointSummary', 'OperationsInsightsWarehouse', 'OperationsInsightsWarehouseSummary', 'OperationsInsightsWarehouseSummaryCollection', 'OperationsInsightsWarehouseUser', 'OperationsInsightsWarehouseUserSummary', 'OperationsInsightsWarehouseUserSummaryCollection', 'OperationsInsightsWarehouseUsers', 'OperationsInsightsWarehouses', 'OpsiConfiguration', 'OpsiConfigurationBasicConfigurationItemSummary', 'OpsiConfigurationConfigurationItemSummary', 'OpsiConfigurationSummary', 'OpsiConfigurations', 'OpsiConfigurationsCollection', 'OpsiDataObject', 'OpsiDataObjectDetailsInQuery', 'OpsiDataObjectQueryParam', 'OpsiDataObjectSummary', 'OpsiDataObjectSupportedQueryParam', 'OpsiDataObjectTypeOpsiDataObjectDetailsInQuery', 'OpsiDataObjects', 'OpsiDataObjectsCollection', 'OpsiDataStores', 'OpsiUxConfiguration', 'OpsiUxConfigurationSummary', 'OpsiWarehouseDataObjects', 'PeComanagedDatabaseConnectionDetails', 'PeComanagedDatabaseHostDetails', 'PeComanagedDatabaseInsight', 'PeComanagedDatabaseInsightSummary', 'PeComanagedExadataInsight', 'PeComanagedExadataInsightSummary', 'PeComanagedHostConfigurationSummary', 'PeComanagedHostInsight', 'PeComanagedHostInsightSummary', 'PeComanagedManagedExternalDatabaseConfigurationSummary', 'ProjectedDataItem', 'QueryDataObjectJsonResultSetRowsCollection', 'QueryDataObjectResultSetColumnMetadata', 'QueryDataObjectResultSetRowsCollection', 'QueryOpsiDataObjectDataDetails', 'QueryWarehouseDataObjectDataDetails', 'RelatedObjectTypeDetails', 'ReportGroupingDetails', 'ReportPropertyDetails', 'ResourceCapacityTrendAggregation', 'ResourceFilters', 'ResourceInsightCurrentUtilization', 'ResourceInsightProjectedUtilization', 'ResourceInsightProjectedUtilizationItem', 'ResourceStatistics', 'ResourceStatisticsAggregation', 'ResourceUsageSummary', 'ResourceUsageTrendAggregation', 'SchemaObjectTypeDetails', 'SqlBucket', 'SqlInsightAggregation', 'SqlInsightAggregationCollection', 'SqlInsightThresholds', 'SqlInventory', 'SqlPlanCollection', 'SqlPlanInsightAggregation', 'SqlPlanInsightAggregationCollection', 'SqlPlanInsights', 'SqlPlanLine', 'SqlPlanSummary', 'SqlResponseTimeDistributionAggregation', 'SqlResponseTimeDistributionAggregationCollection', 'SqlSearchCollection', 'SqlSearchSummary', 'SqlStatisticAggregation', 'SqlStatisticAggregationCollection', 'SqlStatistics', 'SqlStatisticsTimeSeries', 'SqlStatisticsTimeSeriesAggregation', 'SqlStatisticsTimeSeriesAggregationCollection', 'SqlStatisticsTimeSeriesByPlanAggregation', 'SqlStatisticsTimeSeriesByPlanAggregationCollection', 'SqlStats', 'SqlText', 'SqlTextCollection', 'SqlTextSummary', 'SqlTypeDetails', 'StorageServerDetails', 'StorageUsageTrend', 'StorageUsageTrendAggregation', 'SummarizeAwrSourcesSummariesCollection', 'SummarizeDatabaseInsightResourceCapacityTrendAggregationCollection', 'SummarizeDatabaseInsightResourceForecastTrendAggregation', 'SummarizeDatabaseInsightResourceStatisticsAggregationCollection', 'SummarizeDatabaseInsightResourceUsageAggregation', 'SummarizeDatabaseInsightResourceUsageTrendAggregationCollection', 'SummarizeDatabaseInsightResourceUtilizationInsightAggregation', 'SummarizeDatabaseInsightTablespaceUsageTrendAggregationCollection', 'SummarizeExadataInsightResourceCapacityTrendAggregation', 'SummarizeExadataInsightResourceCapacityTrendCollection', 'SummarizeExadataInsightResourceForecastTrendAggregation', 'SummarizeExadataInsightResourceForecastTrendCollection', 'SummarizeExadataInsightResourceStatisticsAggregationCollection', 'SummarizeExadataInsightResourceUsageAggregation', 'SummarizeExadataInsightResourceUsageCollection', 'SummarizeExadataInsightResourceUtilizationInsightAggregation', 'SummarizeHostInsightHostRecommendationAggregation', 'SummarizeHostInsightIoUsageTrendAggregationCollection', 'SummarizeHostInsightNetworkUsageTrendAggregationCollection', 'SummarizeHostInsightResourceCapacityTrendAggregationCollection', 'SummarizeHostInsightResourceForecastTrendAggregation', 'SummarizeHostInsightResourceStatisticsAggregationCollection', 'SummarizeHostInsightResourceUsageAggregation', 'SummarizeHostInsightResourceUsageTrendAggregationCollection', 'SummarizeHostInsightResourceUtilizationInsightAggregation', 'SummarizeHostInsightStorageUsageTrendAggregationCollection', 'SummarizeHostInsightsDiskStatisticsCollection', 'SummarizeHostInsightsTopProcessesUsageCollection', 'SummarizeHostInsightsTopProcessesUsageTrendCollection', 'SummarizeOperationsInsightsWarehouseResourceUsageAggregation', 'SummaryStatistics', 'SynchronizeAutonomousDatabaseToExadataDetails', 'TablespaceUsageTrend', 'TablespaceUsageTrendAggregation', 'TestMacsManagedAutonomousDatabaseInsightConnectionDetails', 'TestMacsManagedCloudDatabaseInsightConnectionDetails', 'TopProcessesUsage', 'TopProcessesUsageTrend', 'TopProcessesUsageTrendAggregation', 'UpdateAutonomousDatabaseInsightDetails', 'UpdateAwrHubDetails', 'UpdateAwrHubSourceDetails', 'UpdateBasicConfigurationItemDetails', 'UpdateChargebackPlanDetails', 'UpdateChargebackPlanReportDetails', 'UpdateConfigurationItemDetails', 'UpdateDatabaseInsightDetails', 'UpdateEmManagedExternalDatabaseInsightDetails', 'UpdateEmManagedExternalExadataInsightDetails', 'UpdateEmManagedExternalHostInsightDetails', 'UpdateEnterpriseManagerBridgeDetails', 'UpdateExadataInsightDetails', 'UpdateExternalMysqlDatabaseInsightDetails', 'UpdateHostInsightDetails', 'UpdateMacsManagedAutonomousDatabaseInsightDetails', 'UpdateMacsManagedCloudDatabaseHostInsightDetails', 'UpdateMacsManagedCloudDatabaseInsightDetails', 'UpdateMacsManagedCloudExadataInsightDetails', 'UpdateMacsManagedCloudHostInsightDetails', 'UpdateMacsManagedExternalDatabaseInsightDetails', 'UpdateMacsManagedExternalHostInsightDetails', 'UpdateMdsMySqlDatabaseInsight', 'UpdateNewsReportDetails', 'UpdateOperationsInsightsPrivateEndpointDetails', 'UpdateOperationsInsightsWarehouseDetails', 'UpdateOperationsInsightsWarehouseUserDetails', 'UpdateOpsiConfigurationDetails', 'UpdateOpsiUxConfigurationDetails', 'UpdatePeComanagedDatabaseInsightDetails', 'UpdatePeComanagedExadataInsightDetails', 'UpdatePeComanagedHostInsightDetails', 'UxConfigurationItemsCollection', 'VmClusterSummary', 'WarehouseDataObjectCollection', 'WarehouseDataObjectDetails', 'WarehouseDataObjectSummary', 'WarehouseTableDataObjectDetails', 'WarehouseViewDataObjectDetails', 'WorkRequest', 'WorkRequestCollection', 'WorkRequestError', 'WorkRequestErrorCollection', 'WorkRequestLogEntry', 'WorkRequestLogEntryCollection', 'WorkRequestResource', 'WorkRequests']

for _model_name in OPSI_MODEL_NAMES:
    globals()[_model_name].model_rebuild()

BOOTSTRAP_MODEL_NAMES = ["Compartment", "CompartmentCollection"]

__all__ = ["OpsiBaseModel", "OpsiRequestModel", *BOOTSTRAP_MODEL_NAMES, *OPSI_MODEL_NAMES]
