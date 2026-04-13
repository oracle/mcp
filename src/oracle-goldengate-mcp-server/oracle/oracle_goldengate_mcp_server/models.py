"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

AuthMode = Literal["basic"]
Primitive = str | int | bool


class CamelModel(BaseModel):
    """Base model enabling both snake_case and camelCase payload compatibility."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid", protected_namespaces=())


class ConfigModel(CamelModel):
    base_url: str = Field(..., description="GoldenGate deployment base URL")
    auth_mode: AuthMode = Field("basic", description="Authentication mode (only 'basic' is supported)")
    username: str | None = Field(None, description="GoldenGate username")
    password: str | None = Field(None, description="GoldenGate password")
    tenancy_ocid: str | None = Field(None, description="OCI tenancy OCID")
    user_ocid: str | None = Field(None, description="OCI user OCID")
    key_fingerprint: str | None = Field(None, description="OCI key fingerprint")
    private_key_pem: str | None = Field(None, description="OCI private key PEM")
    passphrase: str | None = Field(None, description="Private key passphrase")
    oci_region: str | None = Field(None, description="OCI region")
    password_secret_ocid: str | None = Field(None, description="OCI secret OCID containing password")


class CreateExtractSource(CamelModel):
    container: str | None = Field(None, description="Optional source container or PDB")
    schema_name: str = Field(..., alias="schema", min_length=1, description="Source schema name")
    table: str = Field(..., min_length=1, description="Source table name")
    partition_obj_ids: list[int] | None = Field(None, alias="partitionObjIds", description="Optional partition object identifiers")
    target_table: str | None = Field(None, alias="targetTable", description="Optional target table name override")


class CreateExtractOptions(CamelModel):
    attr_charset: str | None = Field(None, alias="attrCharset", description="ATTRCHARSET option")
    charset: str | None = Field(None, description="CHARSET option")
    col_charset: str | None = Field(None, alias="colCharset", description="COLCHARSET option")
    col_map: str | None = Field(None, alias="colMap", description="COLMAP option")
    cols: list[str] | None = Field(None, description="COLS option list")
    cols_except: list[str] | None = Field(None, alias="colsExcept", description="COLSEXCEPT option list")
    ddf: str | None = Field(None, alias="def", description="DEFGEN definition file")
    target_def: str | None = Field(None, alias="targetDef", description="TARGETDEF option")
    event_actions: str | None = Field(None, alias="eventActions", description="EVENTACTIONS option")
    exit_param: str | None = Field(None, alias="exitParam", description="EXITPARAM option")
    fetch_cols: list[str] | None = Field(None, alias="fetchCols", description="FETCHCOLS option")
    fetch_cols_except: list[str] | None = Field(None, alias="fetchColsExcept", description="FETCHCOLSEXCEPT option")
    fetch_mod_cols: list[str] | None = Field(None, alias="fetchModCols", description="FETCHMODCOLS option")
    fetch_mod_cols_except: list[str] | None = Field(None, alias="fetchModColsExcept", description="FETCHMODCOLSEXCEPT option")
    fetch_before_filter: bool | None = Field(None, alias="fetchBeforeFilter", description="FETCHBEFOREFILTER option")
    filter: str | None = Field(None, description="FILTER option")
    get_before_cols: Literal["ALL"] | list[str] | None = Field(None, alias="getBeforeCols", description="GETBEFORECOLS option")
    key_cols: list[str] | None = Field(None, alias="keyCols", description="KEYCOLS option")
    sql_exec: str | None = Field(None, alias="sqlExec", description="SQLEXEC option")
    sql_predicate: str | None = Field(None, alias="sqlPredicate", description="SQLPREDICATE option")
    tokens: dict[str, str] | None = Field(None, description="TOKENS option key/value pairs")
    trim_spaces: bool | None = Field(None, alias="trimSpaces", description="TRIMSPACES option")
    trim_var_spaces: bool | None = Field(None, alias="trimVarSpaces", description="TRIMVARSPACES option")
    where: str | None = Field(None, description="WHERE clause")


class CreateReplicatSource(CamelModel):
    container: str | None = Field(None, description="Optional source container or PDB")
    schema_name: str = Field(..., alias="schema", min_length=1, description="Source schema name")
    table: str = Field(..., min_length=1, description="Source table name")
    partition_obj_ids: list[int] | None = Field(None, alias="partitionObjIds", description="Optional partition object identifiers")
    target_table: str = Field(..., alias="targetTable", min_length=1, description="Target table name")


class CreateReplicatOptions(CamelModel):
    mod_compare_cols: str | None = Field(None, alias="modCompareCols", description="MOD_COMPARE_COLS option")
    col_map: str | None = Field(None, alias="colMap", description="COLMAP option")
    compare_cols: str | None = Field(None, alias="compareCols", description="COMPARECOLS option")
    coordinated: bool | None = Field(None, description="COORDINATED option")
    ddf: str | None = Field(None, alias="def", description="DEFGEN definition file")
    target_def: str | None = Field(None, alias="targetDef", description="TARGETDEF option")
    exceptions_only: bool | None = Field(None, alias="exceptionsOnly", description="EXCEPTIONSONLY option")
    exit_param: str | None = Field(None, alias="exitParam", description="EXITPARAM option")
    event_actions: str | None = Field(None, alias="eventActions", description="EVENTACTIONS option")
    filter: str | None = Field(None, description="FILTER option")
    handle_collisions: bool | None = Field(None, alias="handleCollisions", description="HANDLECOLLISIONS option")
    insert_all_records: bool | None = Field(None, alias="insertAllRecords", description="INSERTALLRECORDS option")
    insert_append: bool | None = Field(None, alias="insertAppend", description="INSERTAPPEND option")
    key_cols: list[str] | None = Field(None, alias="keyCols", description="KEYCOLS option")
    map_all_columns: bool | None = Field(None, alias="mapAllColumns", description="MAPALLCOLUMNS option")
    map_exception: str | None = Field(None, alias="mapException", description="MAPEXCEPTION option")
    map_invisible_columns: bool | None = Field(None, alias="mapInvisibleColumns", description="MAPINVISIBLECOLUMNS option")
    rep_error: str | None = Field(None, alias="repError", description="REPERROR option")
    resolve_conflict: str | None = Field(None, alias="resolveConflict", description="RESOLVECONFLICT option")
    sql_exec: str | None = Field(None, alias="sqlExec", description="SQLEXEC option")
    thread: str | int | None = Field(None, description="THREAD option")
    thread_range: str | None = Field(None, alias="threadRange", description="THREADRANGE option")
    trim_spaces: bool | None = Field(None, alias="trimSpaces", description="TRIMSPACES option")
    trim_var_spaces: bool | None = Field(None, alias="trimVarSpaces", description="TRIMVARSPACES option")
    where: str | None = Field(None, description="WHERE clause")


class IntegratedParamsObject(CamelModel):
    entries: list[str] | None = Field(None, description="Raw INTEGRATEDPARAMS entries")
    key_values: dict[str, Primitive] | None = Field(None, alias="keyValues", description="INTEGRATEDPARAMS key/value pairs")


class StructuredTranlogOptions(CamelModel):
    clauses: list[str] | None = Field(None, description="TRANLOGOPTIONS clauses")
    integrated_params: str | list[str] | IntegratedParamsObject | None = Field(None, alias="integratedParams", description="INTEGRATEDPARAMS specification")
    additional: list[str] | None = Field(None, description="Additional TRANLOGOPTIONS tokens")


class ReportCountSpec(CamelModel):
    every: str | dict[str, Any] | None = Field(None, description="REPORTCOUNT frequency expression")
    records: int | None = Field(None, ge=1, description="REPORTCOUNT record interval")
    rate: bool | None = Field(None, description="Whether to include RATE in REPORTCOUNT")
    additional: list[str] | None = Field(None, description="Additional REPORTCOUNT tokens")


class BoundedRecoverySpec(CamelModel):
    interval: str | None = Field(None, description="BRINTERVAL value")
    dir: str | None = Field(None, description="BRDIR value")
    additional: list[str] | None = Field(None, description="Additional BR tokens")


class ExtractAdvancedParameters(CamelModel):
    disable_heartbeat_table: bool | None = Field(None, alias="disableHeartbeatTable", description="Emit DISABLE_HEARTBEAT_TABLE")
    tranlog_options: str | list[str] | StructuredTranlogOptions | None = Field(None, alias="tranlogOptions", description="TRANLOGOPTIONS specification")
    report_count: ReportCountSpec | None = Field(None, alias="reportCount", description="REPORTCOUNT specification")
    bounded_recovery: BoundedRecoverySpec | None = Field(None, alias="boundedRecovery", description="Bounded recovery specification")
    db_options: str | list[str] | dict[str, list[str]] | None = Field(None, alias="dbOptions", description="DBOPTIONS specification")
    ext_trail: str | None = Field(None, alias="extTrail", min_length=2, max_length=2, description="Optional EXTTRAIL override")
    source_catalog: str | None = Field(None, alias="sourceCatalog", description="SOURCECATALOG value")
    ddl: str | list[str] | None = Field(None, description="DDL directives")
    additional_parameters: list[str] | None = Field(None, alias="additionalParameters", description="Additional raw Extract parameter lines")


class ReplicatAdvancedParameters(CamelModel):
    credential: str | list[str] | None = Field(None, description="Credential line(s), e.g. USERIDALIAS")
    db_options: str | list[str] | dict[str, list[str]] | None = Field(None, alias="dbOptions", description="DBOPTIONS specification")
    batch_sql: str | list[str] | None = Field(None, alias="batchSql", description="BATCHSQL directives")
    apply_parallelism: int | None = Field(None, alias="applyParallelism", ge=1, description="APPLY_PARALLELISM value")
    mode_type: Literal["nonintegrated", "integrated", "parallel", "coordinated"] | None = Field(None, alias="modeType", description="Replicat mode type")
    mode_parallel: bool | None = Field(None, alias="modeParallel", description="Replicat mode parallel flag")
    ddl_error: str | None = Field(None, alias="ddlError", description="DDLERROR directive")
    rep_error: str | None = Field(None, alias="repError", description="REPERROR directive")
    ddl_options: str | None = Field(None, alias="ddlOptions", description="DDLOPTIONS directive")
    source_catalog: str | None = Field(None, alias="sourceCatalog", description="SOURCECATALOG directive")
    obey: str | None = Field(None, description="OBEY file path")
    map_parallelism: int | None = Field(None, alias="mapParallelism", ge=1, description="MAP_PARALLELISM value")
    min_apply_parallelism: int | None = Field(None, alias="minApplyParallelism", ge=1, description="MIN_APPLY_PARALLELISM value")
    max_apply_parallelism: int | None = Field(None, alias="maxApplyParallelism", ge=1, description="MAX_APPLY_PARALLELISM value")
    split_trans_recs: int | None = Field(None, alias="splitTransRecs", ge=1, description="SPLIT_TRANS_RECS value")
    look_ahead_transactions: int | None = Field(None, alias="lookAheadTransactions", ge=1, description="LOOK_AHEAD_TRANSACTIONS value")
    chunk_size: int | None = Field(None, alias="chunkSize", ge=1, description="CHUNK_SIZE value")
    checkpoint_table: str | None = Field(None, alias="checkpointTable", description="CHECKPOINTTABLE name")
    additional_parameters: list[str] | None = Field(None, alias="additionalParameters", description="Additional raw Replicat parameter lines")
