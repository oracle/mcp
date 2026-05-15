"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Pydantic response models for OCI Full Stack Disaster Recovery MCP tools.

These models wrap the OCI SDK's raw to_dict() output into typed, clean
structures that are easier for LLMs to reason about. Noisy SDK fields
(empty tag dicts, verbose headers) are omitted.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .consts import FSDR_OPERATION_NAMES

DrProtectionGroupLifecycleState = Literal[
    "CREATING",
    "UPDATING",
    "ACTIVE",
    "INACTIVE",
    "DELETING",
    "DELETED",
    "FAILED",
    "NEEDS_ATTENTION",
    "UNKNOWN_ENUM_VALUE",
]

DrProtectionGroupRole = Literal[
    "PRIMARY",
    "STANDBY",
    "UNCONFIGURED",
    "UNKNOWN_ENUM_VALUE",
]

DrPlanLifecycleState = DrProtectionGroupLifecycleState

DrPlanType = Literal[
    "SWITCHOVER",
    "FAILOVER",
    "START_DRILL",
    "STOP_DRILL",
    "UNKNOWN_ENUM_VALUE",
]

DrPlanExecutionLifecycleState = Literal[
    "ACCEPTED",
    "IN_PROGRESS",
    "WAITING",
    "PAUSING",
    "PAUSED",
    "RESUMING",
    "CANCELING",
    "CANCELED",
    "SUCCEEDED",
    "FAILED",
    "DELETING",
    "DELETED",
    "UNKNOWN_ENUM_VALUE",
]

DrPlanExecutionType = Literal[
    "SWITCHOVER",
    "SWITCHOVER_PRECHECK",
    "FAILOVER",
    "FAILOVER_PRECHECK",
    "START_DRILL",
    "START_DRILL_PRECHECK",
    "STOP_DRILL",
    "STOP_DRILL_PRECHECK",
    "UNKNOWN_ENUM_VALUE",
]

WorkRequestStatus = Literal[
    "ACCEPTED",
    "IN_PROGRESS",
    "WAITING",
    "CANCELING",
    "CANCELED",
    "SUCCEEDED",
    "FAILED",
    "NEEDS_ATTENTION",
    "UNKNOWN_ENUM_VALUE",
]

WorkRequestOperationType = Literal[
    "CREATE_AUTOMATIC_DR_CONFIGURATION",
    "UPDATE_AUTOMATIC_DR_CONFIGURATION",
    "DELETE_AUTOMATIC_DR_CONFIGURATION",
    "CREATE_DR_PROTECTION_GROUP",
    "UPDATE_DR_PROTECTION_GROUP",
    "DELETE_DR_PROTECTION_GROUP",
    "MOVE_DR_PROTECTION_GROUP",
    "UPDATE_ROLE_DR_PROTECTION_GROUP",
    "ASSOCIATE_DR_PROTECTION_GROUP",
    "DISASSOCIATE_DR_PROTECTION_GROUP",
    "CREATE_DR_PLAN",
    "UPDATE_DR_PLAN",
    "DELETE_DR_PLAN",
    "REFRESH_DR_PLAN",
    "VERIFY_DR_PLAN",
    "CREATE_DR_PLAN_EXECUTION",
    "UPDATE_DR_PLAN_EXECUTION",
    "DELETE_DR_PLAN_EXECUTION",
    "CANCEL_DR_PLAN_EXECUTION",
    "PAUSE_DR_PLAN_EXECUTION",
    "RESUME_DR_PLAN_EXECUTION",
    "RETRY_DR_PLAN_EXECUTION",
    "IGNORE_DR_PLAN_EXECUTION",
    "UNKNOWN_ENUM_VALUE",
]

FsdrOperation = Literal[*FSDR_OPERATION_NAMES]


class DrProtectionGroupSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="The OCID of the DR Protection Group.")
    display_name: str = Field(
        ..., description="A user-friendly name for the DR Protection Group."
    )
    compartment_id: str = Field(
        ..., description="The OCID of the compartment containing the DR Protection Group."
    )
    role: Optional[DrProtectionGroupRole] = Field(
        None, description="The DR Protection Group role in the paired topology."
    )
    lifecycle_state: Optional[DrProtectionGroupLifecycleState] = Field(
        None, description="The current lifecycle state of the DR Protection Group."
    )
    peer_id: Optional[str] = Field(
        None, description="The OCID of the associated peer DR Protection Group."
    )
    peer_region: Optional[str] = Field(
        None, description="The OCI region identifier of the associated peer."
    )
    time_created: Optional[str] = Field(
        None, description="The date and time the DR Protection Group was created."
    )
    time_updated: Optional[str] = Field(
        None, description="The date and time the DR Protection Group was last updated."
    )

    @classmethod
    def from_sdk_dict(cls, d: Dict[str, Any]) -> "DrProtectionGroupSummary":
        return cls.model_validate(d)


class DrPlanSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="The OCID of the DR Plan.")
    display_name: str = Field(..., description="A user-friendly name for the DR Plan.")
    type: DrPlanType = Field(
        ..., description="The type of DR workflow represented by the plan."
    )
    lifecycle_state: Optional[DrPlanLifecycleState] = Field(
        None, description="The current lifecycle state of the DR Plan."
    )
    dr_protection_group_id: Optional[str] = Field(
        None, description="The OCID of the DR Protection Group that owns the plan."
    )
    peer_dr_protection_group_id: Optional[str] = Field(
        None, description="The OCID of the peer DR Protection Group for this plan."
    )
    time_created: Optional[str] = Field(
        None, description="The date and time the DR Plan was created."
    )
    time_updated: Optional[str] = Field(
        None, description="The date and time the DR Plan was last updated."
    )

    @classmethod
    def from_sdk_dict(cls, d: Dict[str, Any]) -> "DrPlanSummary":
        return cls.model_validate(d)


class DrPlanExecutionSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="The OCID of the DR Plan Execution.")
    display_name: str = Field(
        ..., description="A user-friendly name for the DR Plan Execution."
    )
    plan_execution_type: Optional[DrPlanExecutionType] = Field(
        None, description="The type of DR Plan Execution."
    )
    lifecycle_state: Optional[DrPlanExecutionLifecycleState] = Field(
        None, description="The current lifecycle state of the DR Plan Execution."
    )
    dr_protection_group_id: Optional[str] = Field(
        None,
        description="The OCID of the DR Protection Group associated with the execution.",
    )
    plan_id: Optional[str] = Field(
        None, description="The OCID of the DR Plan being executed."
    )
    time_created: Optional[str] = Field(
        None, description="The date and time the DR Plan Execution was created."
    )
    time_started: Optional[str] = Field(
        None, description="The date and time the DR Plan Execution started."
    )
    time_ended: Optional[str] = Field(
        None, description="The date and time the DR Plan Execution ended."
    )
    execution_duration_in_sec: Optional[int] = Field(
        None,
        description="The execution duration, in seconds, once the execution has ended.",
        ge=0,
    )

    @classmethod
    def from_sdk_dict(cls, d: Dict[str, Any]) -> "DrPlanExecutionSummary":
        return cls.model_validate(d)


class WorkRequestSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="The OCID of the work request.")
    operation_type: Optional[WorkRequestOperationType] = Field(
        None, description="The OCI FSDR operation tracked by the work request."
    )
    status: Optional[WorkRequestStatus] = Field(
        None, description="The current status of the work request."
    )
    percent_complete: Optional[float] = Field(
        None, description="The percentage of work completed.", ge=0, le=100
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment associated with the work request."
    )
    time_accepted: Optional[str] = Field(
        None, description="The date and time the work request was accepted."
    )
    time_started: Optional[str] = Field(
        None, description="The date and time the work request started."
    )
    time_finished: Optional[str] = Field(
        None, description="The date and time the work request finished."
    )

    @classmethod
    def from_sdk_dict(cls, d: Dict[str, Any]) -> "WorkRequestSummary":
        return cls.model_validate(d)


class OciResponseResult(BaseModel):
    """Normalized OCI SDK response."""

    model_config = ConfigDict(extra="ignore")

    data: Optional[Any] = Field(
        None, description="Response data converted from the OCI SDK model."
    )
    status: int = Field(..., description="HTTP status code returned by the OCI SDK.")
    headers: Dict[str, Any] = Field(
        default_factory=dict, description="Response headers returned by the OCI SDK."
    )


class WriteResult(BaseModel):
    """Normalized response for write operations that trigger a work request."""

    model_config = ConfigDict(extra="ignore")

    data: Optional[Any] = Field(
        None, description="Response data converted from the OCI SDK model."
    )
    status: int = Field(..., description="HTTP status code returned by the OCI SDK.")
    headers: Dict[str, Any] = Field(
        default_factory=dict, description="Response headers returned by the OCI SDK."
    )
    work_request_id: Optional[str] = Field(
        None, description="The opc-work-request-id header value, when present."
    )


class ListResult(BaseModel):
    """Paginated list response."""

    items: list[Dict[str, Any]] = Field(
        ..., description="Items returned by the list operation."
    )
    opc_next_page: Optional[str] = Field(
        None, description="Token for the next page of results, when present."
    )
    total_items: int = Field(
        ..., description="The number of items included in this response.", ge=0
    )

    @classmethod
    def from_items(
        cls,
        items: list[Dict[str, Any]],
        next_page: Optional[str],
    ) -> "ListResult":
        return cls(items=items, opc_next_page=next_page, total_items=len(items))
